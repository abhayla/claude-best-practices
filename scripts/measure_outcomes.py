"""Honest outcome scorecard — six delivery metrics from data that ALREADY exists.

The hub's existing gauges answer "did the process run?" (a file exists, CI was green).
None of them answer "did the work turn out well?" — so a green pipeline could be shipping
rework indefinitely and no number would move. This module is the outcome half: six
metrics computed from git history, `gh` PR metadata, and the cost ledger, with NO new
collection infrastructure and no new daemon to keep alive.

Design rules this file is built to (owner-reviewed, T-144):

  1. REPORT, never judge. Every function returns measured numbers. There are no
     thresholds, no pass/fail, no exit-code opinions — this is the baseline pass, and a
     metric with no baseline cannot have an honest threshold yet.
  2. "No data" is a first-class ANSWER, never a fabricated rate. Each metric returns a
     `sample_size`; when the sample is empty the value is None and `note` says why. A
     metric that reports 1.0 from a sample of one (the file-exists adoption tautology
     this replaces) is worse than reporting nothing.
  3. Anti-gaming: guardrail catches count CONFIRMED TRUE POSITIVES only. A gate that
     blocks everything must not be able to inflate its own score — see
     guardrail_catch_rate().
  4. Hand-checkable. Every metric is a pure function over plain dicts, and `--explain`
     prints the per-PR classification behind each number, so a checker can recompute a
     week by hand from raw data and get the same answer.

CLI:
    python scripts/measure_outcomes.py [--days 30] [--json] [--explain]
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A follow-up whose headline says it is repairing something. Intentionally the same
# vocabulary as record_task_run._FIX_PATTERN so the trust-score ledger and this
# scorecard classify a correction round identically — two gauges disagreeing about what
# counts as a fix would make both untrustworthy.
FIX_PATTERN = re.compile(r"(?i)\b(fix|repair|revert|hotfix|regression|broke|broken|bug)\b")

# `body` is deliberately EXCLUDED from the bulk fetch: hub PR bodies run to thousands of
# words each, and pulling 100 of them blew past the timeout — which silently degraded the
# whole scorecard to "NO DATA". Adoption's optional body-attribution fallback re-requests
# bodies separately (fetch_pr_bodies) only when it is actually going to use them.
PR_FIELDS = "number,title,headRefName,mergedAt,mergeCommit,commits,files,statusCheckRollup"

GH_TIMEOUT_SECONDS = 120


# --------------------------------------------------------------------------------------
# Metric 1 — change failure rate (DORA)
# --------------------------------------------------------------------------------------

def _touched_paths(pr: dict) -> set[str]:
    return {f.get("path") for f in (pr.get("files") or []) if f.get("path")}


def _merged_dt(pr: dict):
    stamp = pr.get("mergedAt")
    if not stamp:
        return None
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def change_failure_rate(prs: list[dict], window_days: int = 30) -> dict:
    """Fraction of merged PRs that needed a follow-up FIX within `window_days`.

    A PR counts as failed when a LATER merged PR (a) has a fix-shaped title and (b)
    touches at least one file the earlier PR touched. Both conditions are required: a
    fix-shaped PR that shares no files is repairing something else, and a same-file PR
    that is not fix-shaped is ordinary iteration, not a failure.

    Self-matching is impossible (strictly later merge time only), so a PR can never mark
    itself failed. PRs merged too recently to have had a full window to fail in are
    EXCLUDED from the denominator rather than counted as successes — including them
    would bias the rate down every time the report is run.
    """
    dated = [p for p in prs if _merged_dt(p)]
    dated.sort(key=_merged_dt)

    if not dated:
        return {"value": None, "sample_size": 0, "failed": 0,
                "note": "no merged PRs with a mergedAt timestamp in range"}

    newest = max(_merged_dt(p) for p in dated)
    cutoff = newest - timedelta(days=window_days)

    eligible, failed, detail = [], 0, []
    for pr in dated:
        merged = _merged_dt(pr)
        if merged > cutoff:
            # Not enough elapsed time for a fair verdict — excluded, not assumed good.
            continue
        eligible.append(pr)
        paths = _touched_paths(pr)
        culprit = None
        for later in dated:
            later_merged = _merged_dt(later)
            if later_merged <= merged:
                continue
            if later_merged - merged > timedelta(days=window_days):
                break
            if not FIX_PATTERN.search(later.get("title") or ""):
                continue
            if paths and _touched_paths(later) & paths:
                culprit = later.get("number")
                break
        if culprit:
            failed += 1
        detail.append({"pr": pr.get("number"), "failed_by": culprit})

    if not eligible:
        return {"value": None, "sample_size": 0, "failed": 0,
                "note": f"no PRs old enough for a full {window_days}-day window"}

    return {
        "value": round(failed / len(eligible), 4),
        "sample_size": len(eligible),
        "failed": failed,
        "detail": detail,
    }


# --------------------------------------------------------------------------------------
# Metric 2 — rework rate
# --------------------------------------------------------------------------------------

def rework_rate(prs: list[dict], window_days: int = 30) -> dict:
    """Fraction of merged PRs whose touched FILES were modified again within the window.

    Distinct from change_failure_rate by intent: this counts churn of any kind (the
    AI-code "rework" signal), so it does NOT require the later PR to be fix-shaped. A
    high rework rate with a low change-failure rate means code is being revisited a lot
    without being outright broken — a design-churn signal, not a defect signal.

    Same fairness rule: PRs without a full elapsed window are excluded from the
    denominator, never silently counted as clean.
    """
    dated = [p for p in prs if _merged_dt(p)]
    dated.sort(key=_merged_dt)

    if not dated:
        return {"value": None, "sample_size": 0, "reworked": 0,
                "note": "no merged PRs with a mergedAt timestamp in range"}

    newest = max(_merged_dt(p) for p in dated)
    cutoff = newest - timedelta(days=window_days)

    eligible, reworked, detail = [], 0, []
    for pr in dated:
        merged = _merged_dt(pr)
        if merged > cutoff:
            continue
        paths = _touched_paths(pr)
        if not paths:
            # No file list available for this PR — unmeasurable, so it is left out of
            # the denominator rather than scored as clean.
            continue
        eligible.append(pr)
        toucher = None
        for later in dated:
            later_merged = _merged_dt(later)
            if later_merged <= merged:
                continue
            if later_merged - merged > timedelta(days=window_days):
                break
            if _touched_paths(later) & paths:
                toucher = later.get("number")
                break
        if toucher:
            reworked += 1
        detail.append({"pr": pr.get("number"), "reworked_by": toucher})

    if not eligible:
        return {"value": None, "sample_size": 0, "reworked": 0,
                "note": f"no PRs with file data old enough for a full {window_days}-day window"}

    return {
        "value": round(reworked / len(eligible), 4),
        "sample_size": len(eligible),
        "reworked": reworked,
        "detail": detail,
    }


# --------------------------------------------------------------------------------------
# Metric 3 — checker / CI first-pass rate
# --------------------------------------------------------------------------------------

def first_pass_rate(prs: list[dict]) -> dict:
    """Fraction of merged PRs that landed on the FIRST try — one clean commit, no
    fix-shaped correction round in their own history.

    This is the "did the checker have to send it back?" number. Every merged PR is green
    at merge time (that is what let it merge), so CI conclusion alone carries no
    information here; the correction rounds inside the PR do.
    """
    eligible, first_pass, detail = 0, 0, []
    for pr in prs:
        commits = pr.get("commits") or []
        if not commits:
            continue  # unmeasurable, excluded rather than assumed clean
        eligible += 1
        headlines = [c.get("messageHeadline", "") for c in commits]
        clean = len(commits) == 1 and not FIX_PATTERN.search(headlines[0])
        if clean:
            first_pass += 1
        detail.append({"pr": pr.get("number"), "commits": len(commits), "first_pass": clean})

    if not eligible:
        return {"value": None, "sample_size": 0, "first_pass": 0,
                "note": "no PRs with commit data"}

    return {
        "value": round(first_pass / eligible, 4),
        "sample_size": eligible,
        "first_pass": first_pass,
        "detail": detail,
    }


# --------------------------------------------------------------------------------------
# Metric 4 — guardrail catches (true positives only)
# --------------------------------------------------------------------------------------

def guardrail_catches(prs: list[dict]) -> dict:
    """Count CONFIRMED guardrail true positives: a PR whose CI went RED and was then
    fixed and merged green.

    ANTI-GAMING (the design-review rule this metric exists to honour): only a red that
    was subsequently REPAIRED counts. A gate that blocks everything cannot inflate this
    number, because a block with no ensuing fix is not counted as a catch — it is noise.
    Nor can a never-failing gate claim credit: zero reds means zero catches, reported
    honestly as 0 rather than as a perfect score.

    Reported as a COUNT plus the sample it came from, deliberately not as a rate: the
    denominator ("bugs that existed") is unknowable, and inventing one would be exactly
    the kind of fabricated rate this module refuses to produce.
    """
    catches, detail = 0, []
    for pr in prs:
        rollup = pr.get("statusCheckRollup") or []
        conclusions = [c.get("conclusion") or c.get("state") for c in rollup]
        had_red = any(c in ("FAILURE", "ERROR", "CANCELLED") for c in conclusions)
        ended_green = bool(conclusions) and conclusions[-1] == "SUCCESS"
        commits = pr.get("commits") or []
        had_fix_commit = any(
            FIX_PATTERN.search(c.get("messageHeadline", "")) for c in commits
        )
        # A catch requires evidence of BOTH the block and the repair.
        confirmed = had_red and (ended_green or had_fix_commit)
        if confirmed:
            catches += 1
        detail.append({"pr": pr.get("number"), "had_red": had_red, "confirmed_catch": confirmed})

    return {
        "value": catches,
        "sample_size": len(prs),
        "unit": "confirmed true positives",
        "detail": detail,
    }


# --------------------------------------------------------------------------------------
# Metric 5 — invocation-based adoption
# --------------------------------------------------------------------------------------

def invocation_adoption(log_path: Path | None, prs: list[dict] | None = None) -> dict:
    """Adoption measured by ACTUAL INVOCATIONS, never by a file existing on disk.

    Replaces the `adoption_rate: 1.0 @ sample_size: 1` tautology, which only ever proved
    that a provisioning script had copied a file. Reads the invocation log if one is
    present; when it is absent this returns "no data" HONESTLY (value None) rather than
    any number at all. A skill nobody ran has no adoption rate — it has no data, and the
    two must not be confused.

    Falls back to PR body `Skill:` attribution when no log exists, which is weaker
    evidence (self-asserted) and is labelled as such in `source`.
    """
    if log_path and log_path.exists():
        counts: Counter = Counter()
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                counts[json.loads(line).get("skill")] += 1
            except (json.JSONDecodeError, AttributeError):
                continue
        counts.pop(None, None)
        if counts:
            return {"value": dict(counts.most_common()), "sample_size": sum(counts.values()),
                    "source": "invocation log (measured)"}
        return {"value": None, "sample_size": 0, "source": "invocation log (empty)",
                "note": "log present but contains no parseable invocations"}

    skills: Counter = Counter()
    for pr in prs or []:
        m = re.search(r"(?im)^skill:\s*(\S+)", pr.get("body") or "")
        if m:
            skills[m.group(1)] += 1
    if skills:
        return {"value": dict(skills.most_common()), "sample_size": sum(skills.values()),
                "source": "PR body Skill: attribution (self-asserted, weaker than a log)"}

    return {"value": None, "sample_size": 0, "source": "none",
            "note": "no invocation log and no PR skill attribution — NO DATA (not a rate of 0)"}


# --------------------------------------------------------------------------------------
# Metric 6 — cost per completed task
# --------------------------------------------------------------------------------------

def cost_per_task(cost_records: list[dict], prs: list[dict], days: int = 30) -> dict:
    """USD spent divided by merged PRs completed, over the same window.

    Both sides must cover the SAME date range or the ratio is meaningless, so the PR
    count is filtered to the dates actually present in the cost records.
    """
    if not cost_records:
        return {"value": None, "sample_size": 0,
                "note": "cost ledger empty or absent (costs/ledger.jsonl is gitignored runtime state)"}

    dates = sorted(r["date"] for r in cost_records if r.get("date"))
    if not dates:
        return {"value": None, "sample_size": 0, "note": "cost records carry no dates"}

    window = set(dates[-days:])
    usd = sum(r.get("usd", 0.0) for r in cost_records if r.get("date") in window)

    completed = 0
    for pr in prs:
        merged = _merged_dt(pr)
        if merged and merged.date().isoformat() in window:
            completed += 1

    if completed == 0:
        return {"value": None, "sample_size": 0, "usd": round(usd, 2),
                "note": "no merged PRs in the cost window — cost per task undefined"}

    return {
        "value": round(usd / completed, 2),
        "sample_size": completed,
        "usd": round(usd, 2),
        "unit": "USD per merged PR",
    }


# --------------------------------------------------------------------------------------
# I/O adapters + CLI
# --------------------------------------------------------------------------------------

class FetchError(RuntimeError):
    """`gh` could not be read. Distinct from "read fine, found nothing" ON PURPOSE.

    Collapsing the two is the exact dishonesty this module exists to prevent: a timeout
    that silently renders as "NO DATA" reads like a measured absence of PRs, when it is
    really an absence of MEASUREMENT. (Observed for real during T-144: PR bodies are huge,
    100 of them blew the timeout, and the scorecard cheerfully reported all-zeroes.)
    """


# GitHub's GraphQL API budgets a query by the maximum number of nodes it COULD traverse.
# `commits` on a PR expands to commits x authors, so asking for 100 PRs at once is
# rejected outright ("requesting up to 1,000,000 possible nodes"). Fetching in batches
# keeps each query inside the budget; 25 is comfortably under the limit observed live.
PR_BATCH_SIZE = 25


def _run_gh_json(args: list[str], gh: str) -> list[dict]:
    try:
        out = subprocess.run(
            [gh, *args], cwd=ROOT, capture_output=True, text=True,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise FetchError(f"gh timed out after {GH_TIMEOUT_SECONDS}s") from exc
    except OSError as exc:
        raise FetchError(f"could not run {gh!r}: {exc}") from exc

    if out.returncode != 0:
        raise FetchError(f"gh exited {out.returncode}: {(out.stderr or '').strip()[:200]}")
    try:
        return json.loads(out.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise FetchError(f"gh returned unparseable JSON: {exc}") from exc


def fetch_merged_prs(limit: int = 100, gh: str = "gh") -> list[dict]:
    """Read merged PRs via `gh`, in node-budget-safe batches.

    Raises FetchError when the read itself failed — see that class for why an unreadable
    history must never be reported as an empty one.
    """
    # `gh pr list` has no offset, so batching is done by paging on PR number: fetch the
    # newest batch, then repeatedly ask for PRs older than the oldest one seen.
    collected: list[dict] = []
    search = None
    while len(collected) < limit:
        batch_size = min(PR_BATCH_SIZE, limit - len(collected))
        args = ["pr", "list", "--state", "merged", "--limit", str(batch_size),
                "--json", PR_FIELDS]
        if search:
            args += ["--search", search]
        batch = _run_gh_json(args, gh)
        if not batch:
            break
        collected.extend(batch)
        oldest = min(p["number"] for p in batch if p.get("number") is not None)
        if oldest <= 1:
            break
        search = f"sort:created-desc merged:<={_oldest_merged_date(batch)}"
        # Guard against a non-advancing page (identical batch returned again).
        if len(batch) < batch_size:
            break
    return _dedupe_by_number(collected)[:limit]


def _oldest_merged_date(batch: list[dict]) -> str:
    stamps = [p.get("mergedAt") for p in batch if p.get("mergedAt")]
    return min(stamps)[:10] if stamps else "1970-01-01"


def _dedupe_by_number(prs: list[dict]) -> list[dict]:
    """Batch boundaries can overlap on the date cursor — keep one record per PR."""
    seen: dict = {}
    for pr in prs:
        seen.setdefault(pr.get("number"), pr)
    return sorted(seen.values(), key=lambda p: -(p.get("number") or 0))


def fetch_pr_bodies(limit: int = 100, gh: str = "gh") -> list[dict]:
    """Fetch just number+body for the adoption fallback (bodies are large — see PR_FIELDS).

    Returns [] rather than raising: this powers a WEAKER, optional evidence path, and a
    failure here means the fallback is unavailable, not that the scorecard is broken.
    """
    try:
        out = subprocess.run(
            [gh, "pr", "list", "--state", "merged", "--limit", str(limit),
             "--json", "number,body"],
            cwd=ROOT, capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS,
        )
        if out.returncode != 0:
            return []
        return json.loads(out.stdout or "[]")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return []


def load_cost_records() -> list[dict]:
    """Load the gitignored cost ledger, tolerating its absence (CI, fresh worktree)."""
    try:
        from scripts.cost_ledger import load_ledger
        return load_ledger()
    except Exception:
        return []


def measure_all(prs: list[dict], cost_records: list[dict], days: int,
                invocation_log: Path | None) -> dict:
    """Compute all six metrics. Pure over its inputs so a checker can hand-verify."""
    return {
        "window_days": days,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "pr_count": len(prs),
        "metrics": {
            "change_failure_rate": change_failure_rate(prs, days),
            "rework_rate": rework_rate(prs, days),
            "first_pass_rate": first_pass_rate(prs),
            "guardrail_catches": guardrail_catches(prs),
            "invocation_adoption": invocation_adoption(invocation_log, prs),
            "cost_per_task": cost_per_task(cost_records, prs, days),
        },
    }


def _strip_detail(report: dict) -> dict:
    """Drop the per-PR classification lists for the summary view."""
    slim = json.loads(json.dumps(report))
    for metric in slim["metrics"].values():
        metric.pop("detail", None)
    return slim


def format_report(report: dict, explain: bool = False) -> str:
    lines = [
        f"Outcome scorecard — {report['window_days']}-day window "
        f"({report['pr_count']} merged PRs read, generated {report['generated']})",
        "REPORT ONLY — these are measurements, not pass/fail gates.",
        "",
    ]
    for name, m in report["metrics"].items():
        value = m.get("value")
        if value is None:
            shown = f"NO DATA — {m.get('note') or m.get('source', 'no sample')}"
        elif isinstance(value, dict):
            shown = ", ".join(f"{k}={v}" for k, v in list(value.items())[:5]) or "—"
        elif isinstance(value, int) and m.get("unit"):
            shown = f"{value} {m['unit']}"
        else:
            shown = f"{value}"
        lines.append(f"  {name:24} {shown}   (n={m.get('sample_size', 0)})")

    if explain:
        lines.append("")
        lines.append("--- per-PR classification (recompute these by hand to audit) ---")
        for name, m in report["metrics"].items():
            if not m.get("detail"):
                continue
            lines.append(f"  {name}:")
            for row in m["detail"]:
                lines.append(f"    {row}")
    return "\n".join(lines)


def _main() -> int:
    p = argparse.ArgumentParser(description="Honest outcome scorecard from existing data.")
    p.add_argument("--days", type=int, default=30, help="measurement window in days")
    p.add_argument("--limit", type=int, default=100, help="how many merged PRs to read")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--explain", action="store_true",
                   help="print per-PR classifications so a checker can recompute by hand")
    p.add_argument("--invocation-log", type=Path, default=None,
                   help="optional JSONL invocation log for adoption measurement")
    args = p.parse_args()

    try:
        prs = fetch_merged_prs(args.limit)
        # Bodies only when the adoption fallback will actually consult them.
        if not (args.invocation_log and args.invocation_log.exists()):
            bodies = {b["number"]: b.get("body", "") for b in fetch_pr_bodies(args.limit)}
            for pr in prs:
                pr["body"] = bodies.get(pr.get("number"), "")
    except FetchError as exc:
        # Loud and non-zero: "we could not measure" must never be mistaken for
        # "we measured, and there was nothing there".
        print(f"ERROR: could not read PR history — {exc}", file=sys.stderr)
        print("No scorecard produced. This is a FETCH failure, not a finding of zero.",
              file=sys.stderr)
        return 2

    report = measure_all(prs, load_cost_records(), args.days, args.invocation_log)

    if args.json:
        print(json.dumps(report if args.explain else _strip_detail(report), indent=2))
    else:
        print(format_report(report, explain=args.explain))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
