"""Zero-manual trust-score accrual for MERGED PRs (fable-window item 2).

scripts/record_task_run.py only fires on the manual `/git-branch-lifecycle finish` path —
it re-runs the test suite locally and requires an explicit invocation. But the hub's common
landing path is autonomous auto-merge (auto-pr.sh / auto-pr-reconcile.sh): most PRs merge
without anyone ever running `finish`, so today those runs record NOTHING and N/30 stalls.

This is the zero-manual counterpart: it sweeps recently MERGED PRs via `gh` and trusts each
PR's own CI rollup as evidence — the required `validate` check already ran the full test
suite + all validators + the secret scan on that exact code, so there is no need to
re-execute anything locally. It derives the remaining signals from the PR's own metadata
(body markers, reviews, commits) and records ONE honest calibration run per PR, per the same
shadow-mode contract as record_task_run.py (never lands or merges anything).

Swept automatically by `.claude/hooks/auto-pr-reconcile.sh` at SessionStart (fail-safe: a
`gh`/network hiccup here must never block session start — every gh call carries a
subprocess timeout, each per-PR failure is skipped rather than fatal, and the whole sweep
runs under a hard deadline).

Known limitations:
  - The `Verified-by:` body marker is SELF-ASSERTED evidence — the same automation that did
    the work can plant it. What catches an inflated verification signal over time is shadow
    mode + the hard gates + the human_had_to_fix calibration loop (a liar's AUTO runs show up
    as false confidence); an APPROVED GitHub review is the stronger of the two evidence
    branches.
  - `production_health=1.0` is the established hub convention (a hub task has no production
    surface to break), inherited from record_task_run.py — and it is load-bearing: without
    that 0.10 a green verified PR could not reach the 85 AUTO threshold.

CLI:
    python scripts/record_merged_prs.py [--limit 15] [--dry-run] [--report] [--quiet]
"""

import argparse
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

from scripts.collect_signals import assemble_signals, collect_and_record, default_ledger_for
from scripts.record_task_run import _FIX_PATTERN
from scripts.trust_score import load_ledger

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "trust-score.yml"
MARKER_PATH = ROOT / "trust-score" / ".recorded-prs"

_VERIFIED_BY_RE = re.compile(r"(?im)^verified-by:")
_SKILL_RE = re.compile(r"(?im)^skill:\s*(\S+)")

PR_FIELDS = "number,headRefName,title,body,mergedAt,commits,reviews,statusCheckRollup"

# Hang guards for the SessionStart hook's "never block session start" contract: per-gh-call
# timeout + a whole-sweep deadline (bounded in Python, NOT via the `timeout` shell command —
# on Windows Git Bash that can resolve to Windows' timeout.exe, which cannot run commands).
GH_TIMEOUT_SECONDS = 20
SWEEP_DEADLINE_SECONDS = 90


def _gh(args: list[str], timeout: float = GH_TIMEOUT_SECONDS) -> str:
    """Run `gh` with the given args; raise on nonzero exit. Bounded by `timeout` —
    subprocess.TimeoutExpired propagates and is handled as a normal per-PR failure."""
    result = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def list_merged_prs(limit: int, gh=_gh) -> list[int]:
    """Return the numbers of the most recently merged PRs (newest first, per `gh`)."""
    out = gh(["pr", "list", "--state", "merged", "--limit", str(limit), "--json", "number"])
    return [item["number"] for item in json.loads(out)]


def fetch_pr(number: int, gh=_gh) -> dict:
    """Fetch the fields needed to score one merged PR."""
    out = gh(["pr", "view", str(number), "--json", PR_FIELDS])
    return json.loads(out)


def validate_check_passed(pr: dict) -> bool:
    """True iff the required `validate` check rolled up to success.

    Handles both statusCheckRollup shapes gh can return: a check-run
    ({"name": ..., "conclusion": ...}) or a legacy status context ({"context": ...,
    "state": ...}). A missing `validate` entry is honestly False, not skipped.
    """
    for entry in pr.get("statusCheckRollup") or []:
        name = entry.get("name") or entry.get("context")
        if name == "validate":
            outcome = entry.get("conclusion") or entry.get("state")
            return outcome == "SUCCESS"
    return False


def independent_verification(pr: dict) -> float:
    """1.0 iff the PR body carries a machine-readable `Verified-by:` line OR any review
    is APPROVED; else 0.0 (honest unknown, not a guess)."""
    body = pr.get("body") or ""
    if _VERIFIED_BY_RE.search(body):
        return 1.0
    for review in pr.get("reviews") or []:
        if review.get("state") == "APPROVED":
            return 1.0
    return 0.0


def derive_skill(pr: dict) -> str | None:
    """Per-skill ledger attribution: an explicit `Skill: <name>` body line wins; else the
    branch's leading prefix (e.g. `auto/work-...` -> `branch:auto`); else None."""
    body = pr.get("body") or ""
    m = _SKILL_RE.search(body)
    if m:
        return m.group(1)
    branch = pr.get("headRefName") or ""
    if "/" in branch:
        return f"branch:{branch.split('/', 1)[0]}"
    return None


def derive_human_had_to_fix(pr: dict) -> bool | None:
    """Same semantics as record_task_run.derive_human_had_to_fix, sourced from PR commits
    instead of local git history: >1 commit -> True; exactly 1 clean commit -> False (or
    True if its headline matches the correction-round pattern); 0 commits -> None."""
    commits = pr.get("commits") or []
    if len(commits) > 1:
        return True
    if len(commits) == 1:
        headline = commits[0].get("messageHeadline", "")
        return bool(_FIX_PATTERN.search(headline))
    return None


def already_recorded(number: int, marker_path: Path, ledger_path: Path) -> bool:
    """Belt-and-suspenders dedup: the marker file OR a matching `pr` field already present
    in the ledger. Both are gitignored, machine-local state (trust-score/ledgers/ is in
    .gitignore too) — the second layer guards against a lost/wiped marker on the SAME
    machine, not against another clone recording independently."""
    if marker_path.exists():
        recorded = {
            int(line.strip()) for line in marker_path.read_text(encoding="utf-8").splitlines() if line.strip()
        }
        if number in recorded:
            return True
    if ledger_path.exists():
        for run in load_ledger(ledger_path):
            if run.get("pr") == number:
                return True
    return False


def mark_recorded(number: int, marker_path: Path) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, "a", encoding="utf-8") as f:
        f.write(f"{number}\n")


def record_merged_prs(
    limit: int = 15,
    marker_path: Path | None = None,
    ledger_path: Path | None = None,
    gh=_gh,
    dry_run: bool = False,
) -> dict:
    """Sweep recently merged PRs and record ONE honest calibration run per not-yet-recorded PR.

    Trusts the PR's own CI rollup instead of re-running tests locally — the `validate`
    check already covers tests + validators + secret scan for that exact code. Never lands
    or merges anything (shadow-mode recording only, same contract as record_task_run.py).
    """
    marker_path = marker_path or MARKER_PATH
    ledger_path = ledger_path or default_ledger_for("atlas")

    numbers = list_merged_prs(limit, gh=gh)
    recorded: list[int] = []
    skipped = 0
    results: dict[int, dict] = {}
    summary: dict = {"recorded": recorded, "skipped": 0, "results": results}

    # Hard sweep deadline (SessionStart contract). On expiry we stop gracefully — any PR
    # left unrecorded is simply picked up by the next session's sweep.
    deadline = time.monotonic() + SWEEP_DEADLINE_SECONDS

    for number in numbers:
        if time.monotonic() >= deadline:
            summary["aborted"] = "deadline"
            break

        # NOTE (accepted race): this check-then-act (already_recorded -> record ->
        # mark_recorded) is not atomic — two SessionStart sweeps running concurrently on
        # the SAME clone could in principle both record a PR. Accepted: sessions rarely
        # start simultaneously, and session-concurrency-guard.sh already warns when
        # multiple sessions share a working tree.
        if already_recorded(number, marker_path, ledger_path):
            skipped += 1
            continue

        # One bad PR (gh timeout/error, garbage JSON) skips that PR — never crashes the sweep.
        try:
            pr = fetch_pr(number, gh=gh)
            ci_green = validate_check_passed(pr)

            signals = assemble_signals(
                tests_passed=1 if ci_green else 0,
                tests_total=1,
                coverage=0.0,
                independent_verification=independent_verification(pr),
                regression_clean=1.0 if ci_green else 0.0,
                production_health=1.0,
                secret_scan_clean=1.0 if ci_green else 0.0,
            )

            extra = {
                "pr": number,
                "branch": pr.get("headRefName"),
                "skill": derive_skill(pr),
                "recorded_at": date.today().isoformat(),
            }

            result = collect_and_record(
                signals,
                stage="reversible",
                record=not dry_run,
                human_had_to_fix=derive_human_had_to_fix(pr),
                ledger_path=ledger_path,
                config_path=CONFIG_PATH,
                extra=extra,
            )
        except Exception:
            skipped += 1
            continue

        results[number] = {"score": result["score"], "recommended": result["recommended"]}
        recorded.append(number)
        if not dry_run:
            mark_recorded(number, marker_path)

    summary["skipped"] = skipped
    return summary


def _main() -> int:
    p = argparse.ArgumentParser(description="Zero-manual trust-score accrual for merged PRs.")
    p.add_argument("--limit", type=int, default=15, help="how many recent merged PRs to sweep")
    p.add_argument("--dry-run", action="store_true", help="score but do not record or mark")
    p.add_argument("--report", action="store_true", help="print graduation + per-skill stats and exit")
    p.add_argument("--quiet", action="store_true", help="print a one-line summary only")
    args = p.parse_args()

    ledger_path = default_ledger_for("atlas")

    if args.report:
        from scripts.trust_score import graduation_status, load_config, stats_by

        config = load_config(CONFIG_PATH)
        runs = load_ledger(ledger_path)
        print(
            json.dumps(
                {
                    "graduation": graduation_status(runs, config),
                    "by_skill": stats_by(runs, "skill"),
                },
                indent=2,
            )
        )
        return 0

    outcome = record_merged_prs(limit=args.limit, dry_run=args.dry_run)

    if args.quiet:
        parts = ", ".join(
            f"#{n} {outcome['results'][n]['recommended']}:{outcome['results'][n]['score']}"
            for n in outcome["recorded"]
        )
        total = len(load_ledger(ledger_path))
        print(f"recorded {len(outcome['recorded'])} PRs ({parts}) — atlas N/30 = {total}/30")
        return 0

    print(json.dumps(outcome, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
