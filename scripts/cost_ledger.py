"""Self-enforcing cost ledger — daily token/USD accrual (fable-window item 6).

Nothing today measures the hub's own autonomous-loop token spend, so cadence (how often
sessions/hooks/loops run) is never treated as a cost decision. This closes that gap by
reading Claude Code's own per-session transcript JSONLs (the ONLY source of real per-message
usage — there is no billing API to poll), aggregating them into a daily USD/token rollup via
`config/model-costs.yml`, and alerting the owner when a day's spend crosses
`daily_alert_usd`. Same shadow-mode spirit as the trust-score ledger: record honestly, alert
cheaply, never assume — a corrupt/missing transcript is skipped and counted, never fatal.

Transcript layout (per-project, under `--projects-dir`, default `~/.claude/projects/`):
    <project-slug>/*.jsonl                       — top-level session transcripts
    <project-slug>/<session>/subagents/agent-*.jsonl — subagent transcripts
Each assistant message line carries `message.usage` (token counts) and `message.model`;
lines without `message.usage` (system/tool/user entries) are skipped, not errors.

COMPLETENESS CONTRACT (the ledger must never freeze a partial day): a day is appended to
the ledger ONLY from a scan that ran to completion. A deadline-aborted scan appends NOTHING
— its per-day totals are partial, and the idempotency-by-date guard would otherwise freeze
the partial number forever. Bootstrap on a fresh machine: the first full-history scan takes
longer than the hook's soft deadline (measured ~106s over ~2,000 files), so run
`--daily --deadline-seconds 0` once manually; after that first complete pass the daily tick
scans only files modified since the newest recorded day (transcripts are append-only, so a
file whose mtime predates day D cannot contain day-D entries) and finishes in seconds.

All dates are UTC: entry timestamps are UTC, so "today" (the still-accruing, never-appended
day) is the UTC date too — using the machine-local date would mis-classify the in-progress
UTC day as completed between local midnight and UTC midnight (e.g. 00:00-05:30 IST).

CLI:
    python scripts/cost_ledger.py --daily [--projects-dir PATH] [--deadline-seconds N]
    python scripts/cost_ledger.py --report [--days 7]
    python scripts/cost_ledger.py --cadence-report
    python scripts/cost_ledger.py --alert
"""

import argparse
import json
import os
import subprocess
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "model-costs.yml"
LEDGER_PATH = ROOT / "costs" / "ledger.jsonl"

TOKEN_KINDS = ("input", "output", "cache_write", "cache_read")
USAGE_FIELD_MAP = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_write": "cache_creation_input_tokens",
    "cache_read": "cache_read_input_tokens",
}

# Bounded work: a full-tree scan over hundreds of transcript files must never hang the
# SessionStart hook that calls `--daily` (same soft-deadline contract as record_merged_prs.py).
DAILY_DEADLINE_SECONDS = 60
GH_TIMEOUT_SECONDS = 15


def default_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def _utc_today() -> date:
    """The current UTC date. Entry dates come from UTC timestamps, so the "today is still
    accruing" boundary MUST be UTC as well — `date.today()` (machine-local) would treat the
    in-progress UTC day as a completed past day between local and UTC midnight (IST is
    UTC+5:30, so 00:00-05:30 local), freezing a partial day into the ledger."""
    return datetime.now(timezone.utc).date()


def load_config(config_path: Path | str | None = None) -> dict:
    path = Path(config_path) if config_path else CONFIG_PATH
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_iso_date(timestamp: str):
    ts = timestamp.replace("Z", "+00:00")
    return datetime.fromisoformat(ts).date()


def scan_transcripts(
    projects_dir,
    since_date=None,
    stats: dict | None = None,
    deadline: float | None = None,
    min_mtime: float | None = None,
):
    """Stream usage-bearing entries from every `*.jsonl` transcript under `projects_dir`.

    Yields `(date_str, project, model, attribution, usage, session_id)` for every assistant
    message entry that carries `message.usage`. `attribution` is `entry["attributionAgent"]`
    when present, else `"main"`. Malformed lines/files are skipped and counted into `stats`
    (`skipped_lines` / `skipped_files`) rather than raising — one bad file must never abort
    the whole scan. `deadline` (a `time.monotonic()` value) stops the scan gracefully and sets
    `stats["aborted"] = "deadline"` when exceeded, so a caller with a hard time budget (the
    SessionStart hook) still gets a partial, honest result — which callers with a
    completeness requirement (append_daily) must treat as NOT persistable.

    `min_mtime` (epoch seconds) skips whole files whose st_mtime is older — the incremental-
    scan lever: transcripts are append-only and entries are written in near-real-time, so a
    file last touched before day D cannot contain day-D entries.

    Double-counting: subagent transcripts under `<session>/subagents/` do NOT duplicate the
    parent session file's entries. Verified empirically 2026-07-10 against the real
    ~/.claude/projects/ tree: across 40 sessions with subagent dirs, 0 of 6,927 subagent
    usage entries shared a `message.id`/`uuid` with the parent session file — each usage
    entry appears in exactly one file, so summing across all files is correct without
    message-id dedup.

    Lines lacking the literal substring '"usage"' are skipped WITHOUT json parsing (a full
    parse of every line measured ~106s over the real tree; the prefilter is what makes the
    incremental daily tick fit its deadline). Consequence: a malformed line only counts
    toward `skipped_lines` if it contains '"usage"' — an unparseable line without it is
    indistinguishable from an uninteresting one at prefilter speed, and is skipped silently.
    """
    if stats is None:
        stats = {}
    stats.setdefault("skipped_lines", 0)
    stats.setdefault("skipped_files", 0)

    projects_dir = Path(projects_dir)
    if not projects_dir.is_dir():
        return

    since_dt = date.fromisoformat(since_date) if since_date else None

    # Most-recently-modified project dirs first: under the deadline, a bounded scan must not
    # starve on alphabetically-early projects every run (stable sort order + a repeatable
    # timeout means the same early dirs would win every time) — prioritizing active projects
    # keeps today's/this-week's spend showing up even when the full historical tree can't be
    # scanned in one pass.
    try:
        project_dirs = sorted(
            (p for p in projects_dir.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        project_dirs = sorted(p for p in projects_dir.iterdir() if p.is_dir())

    for project_dir in project_dirs:
        if deadline is not None and time.monotonic() >= deadline:
            stats["aborted"] = "deadline"
            return
        project = project_dir.name
        try:
            jsonl_files = sorted(project_dir.rglob("*.jsonl"))
        except OSError:
            stats["skipped_files"] += 1
            continue

        for jsonl_path in jsonl_files:
            if deadline is not None and time.monotonic() >= deadline:
                stats["aborted"] = "deadline"
                return
            try:
                if min_mtime is not None and jsonl_path.stat().st_mtime < min_mtime:
                    continue
                fh = open(jsonl_path, encoding="utf-8")
            except OSError:
                stats["skipped_files"] += 1
                continue
            with fh:
                for line_no, line in enumerate(fh):
                    # Deadline check INSIDE the per-line loop too (every ~5000 lines): a
                    # single multi-hundred-MB transcript could otherwise overshoot the soft
                    # deadline by the whole time it takes to read that one file.
                    if (
                        deadline is not None
                        and line_no % 5000 == 4999
                        and time.monotonic() >= deadline
                    ):
                        stats["aborted"] = "deadline"
                        return
                    if '"usage"' not in line:
                        continue  # prefilter — see docstring; skips json.loads on ~70% of lines
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        stats["skipped_lines"] += 1
                        continue
                    try:
                        message = entry.get("message") or {}
                        usage = message.get("usage")
                        if not usage:
                            continue
                        model = message.get("model") or "unknown"
                        timestamp = entry.get("timestamp")
                        if not timestamp:
                            stats["skipped_lines"] += 1
                            continue
                        entry_date = _parse_iso_date(timestamp)
                    except (AttributeError, TypeError, ValueError):
                        stats["skipped_lines"] += 1
                        continue

                    if since_dt and entry_date < since_dt:
                        continue

                    attribution = entry.get("attributionAgent") or "main"
                    session_id = entry.get("sessionId") or f"{project}:{jsonl_path.stem}"
                    yield entry_date.isoformat(), project, model, attribution, usage, session_id


def model_family_rates(model: str, config: dict) -> dict:
    """Match a transcript model string to its family's rates by case-insensitive substring;
    an unmatched model falls back to `families.default` (never silently priced at zero)."""
    families = config.get("families", {})
    model_lower = (model or "").lower()
    for family, rates in families.items():
        if family == "default":
            continue
        if family in model_lower:
            return rates
    return families.get("default", dict.fromkeys(TOKEN_KINDS, 0.0))


def usd_for_usage(model: str, usage: dict, config: dict) -> float:
    rates = model_family_rates(model, config)
    total = 0.0
    for kind, field in USAGE_FIELD_MAP.items():
        tokens = usage.get(field) or 0
        total += (tokens / 1_000_000) * rates.get(kind, 0.0)
    return total


def _empty_bucket() -> dict:
    bucket = dict.fromkeys(TOKEN_KINDS, 0)
    bucket["usd"] = 0.0
    return bucket


def _add_usage(bucket: dict, usage: dict, usd: float) -> None:
    for kind, field in USAGE_FIELD_MAP.items():
        bucket[kind] += usage.get(field) or 0
    bucket["usd"] += usd


def aggregate(entries, config: dict) -> dict:
    """Roll up `scan_transcripts()` entries into one dict per day: token totals by kind, by
    model family, by attribution (main vs. subagent-name), a distinct session count, and the
    estimated total USD (cache_read priced at the cache_read rate, etc., per `usd_for_usage`)."""
    days: dict[str, dict] = {}
    for date_str, _project, model, attribution, usage, session_id in entries:
        day = days.setdefault(
            date_str,
            {
                "date": date_str,
                "tokens": _empty_bucket(),
                "by_model": {},
                "by_attribution": {},
                "sessions": set(),
                "usd": 0.0,
            },
        )
        usd = usd_for_usage(model, usage, config)
        day["usd"] += usd
        day["sessions"].add(session_id)

        _add_usage(day["tokens"], usage, usd)
        _add_usage(day["by_model"].setdefault(model, _empty_bucket()), usage, usd)
        _add_usage(day["by_attribution"].setdefault(attribution, _empty_bucket()), usage, usd)

    result = {}
    for date_str, day in days.items():
        day["session_count"] = len(day.pop("sessions"))
        result[date_str] = day
    return result


def _ledger_dates(ledger_path: Path) -> set[str]:
    if not ledger_path.exists():
        return set()
    dates = set()
    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "date" in record:
                dates.add(record["date"])
    return dates


def _prune_old(ledger_path: Path, retention_days: int, today: date) -> None:
    if not ledger_path.exists() or retention_days <= 0:
        return
    cutoff = (today - timedelta(days=retention_days)).isoformat()
    kept = []
    changed = False
    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                kept.append(line if line.endswith("\n") else line + "\n")
                continue
            if record.get("date", "9999-99-99") < cutoff:
                changed = True
                continue
            kept.append(line if line.endswith("\n") else line + "\n")
    if changed:
        # Crash-safe rewrite: write a sibling temp file, then atomically swap it in — a crash
        # mid-write must never leave the ledger truncated (os.replace is atomic on the same
        # filesystem on both Windows and POSIX).
        tmp_path = ledger_path.with_suffix(ledger_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(kept)
        os.replace(tmp_path, ledger_path)


def append_daily(
    ledger_path: Path | None = None,
    projects_dir: Path | None = None,
    config: dict | None = None,
    today: date | None = None,
    deadline: float | None = None,
) -> dict:
    """Append one JSON line per COMPLETED day (strictly before `today`, in UTC) not already
    present in the ledger. Idempotent by date — re-running never duplicates a recorded day.

    COMPLETENESS CONTRACT: a day is persisted only from a scan that ran to completion. When
    the scan hit its deadline (`stats["aborted"]`), NOTHING is appended — the per-day totals
    are partial, and appending one would freeze the partial number forever behind the
    idempotency guard (a later complete scan could never correct it). The chosen fix is
    no-append (simplest honest behavior) rather than provisional-and-overwrite rows: unfrozen
    days are simply captured by the next COMPLETE scan, which the incremental min_mtime
    filter below makes cheap after the one-time full-history bootstrap (see module docstring).

    `--report` may still show live partial data — it renders from the ledger plus nothing
    it persists, so only THIS function carries the completeness requirement.
    """
    ledger_path = ledger_path or LEDGER_PATH
    config = config or load_config()
    projects_dir = Path(projects_dir) if projects_dir else default_projects_dir()
    today = today or _utc_today()

    existing = _ledger_dates(ledger_path)

    # Incremental scan: once the ledger has a complete history through its newest date, only
    # files modified on/after that day can contain entries for the days still missing
    # (append-only transcripts; entries are written in near-real-time). The 1-day margin
    # absorbs filesystem-mtime vs entry-timestamp clock skew. Fresh ledger -> full scan.
    min_mtime = None
    if existing:
        newest = max(existing)
        newest_start_utc = datetime.combine(
            date.fromisoformat(newest), datetime.min.time(), tzinfo=timezone.utc
        )
        min_mtime = newest_start_utc.timestamp() - 86400

    stats: dict = {}
    entries = list(scan_transcripts(projects_dir, stats=stats, deadline=deadline, min_mtime=min_mtime))

    appended: list[str] = []
    if not stats.get("aborted"):
        days = aggregate(entries, config)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger_path, "a", encoding="utf-8") as f:
            for date_str in sorted(days):
                if date.fromisoformat(date_str) >= today:
                    continue
                if date_str in existing:
                    continue
                f.write(json.dumps(days[date_str], sort_keys=True) + "\n")
                appended.append(date_str)

        _prune_old(ledger_path, config.get("ledger_retention_days", 365), today)

    return {"appended": appended, "skipped_lines": stats.get("skipped_lines", 0), "aborted": stats.get("aborted")}


def load_ledger(ledger_path: Path | None = None) -> list[dict]:
    ledger_path = ledger_path or LEDGER_PATH
    if not ledger_path.exists():
        return []
    records = []
    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


# --- Notifier thin client (fail-open) ---------------------------------------------------
# Pattern SSOT: core/.claude/templates/owner_notify.py. Not imported from here — that
# template is the DISTRIBUTABLE downstream copy; the hub keeps its own tiny inline client so
# this script has no dependency on `core/` (per CLAUDE.md's "Two `.claude/` Directories").


def _notify_owner(severity: str, title: str, body: str, dedupe_key: str) -> None:
    import os

    url = os.environ.get("NOTIFIER_URL")
    key = os.environ.get("NOTIFIER_KEY")
    if not url or not key:
        return
    try:
        import requests

        requests.post(
            f"{url.rstrip('/')}/notify",
            json={
                "project": "claude-best-practices-hub",
                "severity": severity,
                "title": title,
                "body": body,
                "dedupeKey": dedupe_key,
            },
            headers={"X-Api-Key": key},
            timeout=2,
        )
    except Exception:  # noqa: BLE001 — owner-alerting must never break the caller
        pass


def check_alert(ledger_path: Path | None = None, config: dict | None = None, today: date | None = None, notify=_notify_owner) -> dict:
    """If yesterday's recorded USD exceeds `daily_alert_usd`, POST a P2 owner alert.

    Fail-open: no ledger entry for yesterday, or Notifier unset/unreachable -> silent no-op.
    Returns a small dict describing what happened (for CLI reporting / tests), never raises.
    """
    ledger_path = ledger_path or LEDGER_PATH
    config = config or load_config()
    today = today or _utc_today()  # ledger dates are UTC — see _utc_today()
    yesterday = (today - timedelta(days=1)).isoformat()
    threshold = config.get("daily_alert_usd", 50)

    record = next((r for r in load_ledger(ledger_path) if r.get("date") == yesterday), None)
    if record is None:
        return {"alerted": False, "reason": "no-ledger-entry", "date": yesterday}

    usd = record.get("usd", 0.0)
    if usd <= threshold:
        return {"alerted": False, "reason": "under-threshold", "date": yesterday, "usd": usd}

    notify(
        "P2",
        f"Hub cost ledger: {yesterday} spend ${usd:.2f} exceeded ${threshold:.2f}",
        body=json.dumps({k: v for k, v in record.items() if k not in ("by_model", "by_attribution")}, indent=2),
        dedupe_key=f"cost-alert-{yesterday}",
    )
    return {"alerted": True, "date": yesterday, "usd": usd, "threshold": threshold}


# --- Reports -----------------------------------------------------------------------------


def format_report(records: list[dict], days: int) -> str:
    if not records:
        return "No ledger entries yet - run `--daily` first."
    records = sorted(records, key=lambda r: r["date"])[-days:]
    lines = [f"Cost ledger - last {len(records)} day(s):", ""]
    total_usd = 0.0
    model_totals: Counter = Counter()
    attribution_totals: Counter = Counter()
    for r in records:
        total_usd += r.get("usd", 0.0)
        for model, bucket in r.get("by_model", {}).items():
            model_totals[model] += bucket.get("usd", 0.0)
        for attribution, bucket in r.get("by_attribution", {}).items():
            attribution_totals[attribution] += bucket.get("usd", 0.0)
        tokens = r.get("tokens", {})
        lines.append(
            f"  {r['date']}  ${r.get('usd', 0.0):8.2f}  "
            f"in={tokens.get('input', 0):,} out={tokens.get('output', 0):,} "
            f"cache_w={tokens.get('cache_write', 0):,} cache_r={tokens.get('cache_read', 0):,}  "
            f"sessions={r.get('session_count', 0)}"
        )
    lines.append("")
    lines.append(f"Total: ${total_usd:.2f} over {len(records)} day(s)")

    if model_totals:
        lines.append("")
        lines.append("By model:")
        for model, usd in model_totals.most_common():
            lines.append(f"  {model:30s} ${usd:8.2f}")

    if attribution_totals:
        lines.append("")
        lines.append("Top attributionAgents:")
        for attribution, usd in attribution_totals.most_common(10):
            lines.append(f"  {attribution:30s} ${usd:8.2f}")

    if len(records) >= 2:
        half = len(records) // 2
        prev_avg = sum(r.get("usd", 0.0) for r in records[:half]) / max(half, 1)
        recent_avg = sum(r.get("usd", 0.0) for r in records[half:]) / max(len(records) - half, 1)
        trend = "flat"
        if prev_avg > 0:
            delta_pct = (recent_avg - prev_avg) / prev_avg * 100
            trend = f"{delta_pct:+.0f}% vs prior period"
        lines.append("")
        lines.append(f"Trend: recent avg/day ${recent_avg:.2f} vs prior avg/day ${prev_avg:.2f} ({trend})")

    return "\n".join(lines)


CRON_WORKFLOWS = {
    "expire-sources.yml": "Monday 8am UTC",
    "scan-projects.yml": "Monday 9am UTC",
    "recommend.yml": "Wednesday 9am UTC",
    "scan-internet.yml": "Monday 10am UTC",
    "aggregate-telemetry.yml": "Friday 9am UTC",
    "standing-goals.yml": "daily 5am UTC",
}


def _merged_pr_count_by_day(days: list[str]) -> dict[str, int] | None:
    """Best-effort merged-PR count per day via `gh`; returns None (with a caller-visible note)
    when `gh` is unavailable — never raises, never blocks the cadence report."""
    if not days:
        return {}
    try:
        out = subprocess.run(
            ["gh", "pr", "list", "--state", "merged", "--limit", "200", "--json", "mergedAt"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_SECONDS,
        )
        if out.returncode != 0:
            return None
        prs = json.loads(out.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None

    counts: Counter = Counter()
    for pr in prs:
        merged_at = pr.get("mergedAt")
        if not merged_at:
            continue
        day = merged_at.split("T", 1)[0]
        if day in days:
            counts[day] += 1
    return dict(counts)


def cadence_report(ledger_path: Path | None = None, config: dict | None = None) -> str:
    """Cadence-is-a-cost-decision report: recent USD/session trend, an honest inventory of
    the repo's GH-cron workflows (which cost $0 Claude tokens — they never call Claude; the
    real cost centers are SESSIONS), a daily_alert_usd flag, and a cost-vs-merged-PR-growth
    flag over the last two 7-day windows (skipped with a note when `gh` is unavailable)."""
    ledger_path = ledger_path or LEDGER_PATH
    config = config or load_config()
    threshold = config.get("daily_alert_usd", 50)
    records = sorted(load_ledger(ledger_path), key=lambda r: r["date"])

    lines = ["Cadence report - cadence is a cost decision", ""]

    lines.append("GH-cron workflows (cost $0 Claude tokens - they never call Claude; the real")
    lines.append("cost centers below are Claude sessions, not these crons):")
    for wf, schedule in CRON_WORKFLOWS.items():
        lines.append(f"  {wf:28s} {schedule}")
    lines.append("")

    if not records:
        lines.append("No ledger entries yet - run `--daily` first for a session/USD trend.")
        return "\n".join(lines)

    lines.append("Sessions/day and USD/day (most recent 14 days):")
    recent = records[-14:]
    for r in recent:
        lines.append(f"  {r['date']}  sessions={r.get('session_count', 0):3d}  ${r.get('usd', 0.0):8.2f}")

    over_threshold = [r for r in records if r.get("usd", 0.0) > threshold]
    lines.append("")
    if over_threshold:
        lines.append(f"FLAG: {len(over_threshold)} day(s) exceeded daily_alert_usd (${threshold:.2f}):")
        for r in over_threshold:
            lines.append(f"  {r['date']}  ${r.get('usd', 0.0):.2f}")
    else:
        lines.append(f"No day has exceeded daily_alert_usd (${threshold:.2f}).")

    if len(records) >= 14:
        window_a = records[-14:-7]
        window_b = records[-7:]
        usd_a = sum(r.get("usd", 0.0) for r in window_a)
        usd_b = sum(r.get("usd", 0.0) for r in window_b)
        growth_pct = ((usd_b - usd_a) / usd_a * 100) if usd_a > 0 else 0.0

        day_names = [r["date"] for r in window_a] + [r["date"] for r in window_b]
        pr_counts = _merged_pr_count_by_day(day_names)

        lines.append("")
        lines.append(f"7-day cost trend: prior window ${usd_a:.2f} -> recent window ${usd_b:.2f} ({growth_pct:+.0f}%)")
        if pr_counts is None:
            lines.append("  (merged-PR count skipped - `gh` unavailable or errored)")
        else:
            prs_a = sum(pr_counts.get(d, 0) for d in [r["date"] for r in window_a])
            prs_b = sum(pr_counts.get(d, 0) for d in [r["date"] for r in window_b])
            lines.append(f"  merged PRs: prior window {prs_a} -> recent window {prs_b}")
            if growth_pct > 50 and prs_b <= prs_a:
                lines.append("  FLAG: cost grew >50% without a corresponding rise in merged-PR count")

    return "\n".join(lines)


def _main() -> int:
    p = argparse.ArgumentParser(description="Self-enforcing cost ledger for hub token spend.")
    p.add_argument("--projects-dir", default=None, help="override the Claude Code transcripts dir")
    p.add_argument("--daily", action="store_true", help="append_daily() + alert-if-over-threshold, bounded")
    p.add_argument("--report", action="store_true", help="print a plain-text per-day USD/token report")
    p.add_argument("--days", type=int, default=7, help="report window in days (default 7)")
    p.add_argument("--cadence-report", action="store_true", help="print the cadence-is-a-cost-decision report")
    p.add_argument("--alert", action="store_true", help="check yesterday's spend and alert if over threshold")
    p.add_argument(
        "--deadline-seconds",
        type=int,
        default=DAILY_DEADLINE_SECONDS,
        help="soft scan deadline for --daily (0 = unbounded; use once to bootstrap a fresh ledger)",
    )
    args = p.parse_args()

    config = load_config()
    projects_dir = Path(args.projects_dir) if args.projects_dir else default_projects_dir()

    if args.report:
        print(format_report(load_ledger(), args.days))
        return 0

    if args.cadence_report:
        print(cadence_report())
        return 0

    if args.alert:
        result = check_alert(config=config)
        print(json.dumps(result))
        return 0

    if args.daily:
        deadline = time.monotonic() + args.deadline_seconds if args.deadline_seconds > 0 else None
        outcome = append_daily(projects_dir=projects_dir, config=config, deadline=deadline)
        alert = check_alert(config=config)
        print(
            f"appended {len(outcome['appended'])} day(s) "
            f"(skipped_lines={outcome['skipped_lines']}, aborted={outcome['aborted']}); "
            f"alert={'sent' if alert.get('alerted') else 'none'}"
        )
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
