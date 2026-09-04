"""Context-usage report - 7-day token/context measurement (token-waste program, T-446).

Why (measured 2026-09-04 over 7 days of transcripts on this PC): 5.79 billion input tokens;
44% of that is the fixed prelude re-sent on every single call; four IPODhan main sessions ran
from ~140k to ~900k context (one made 1,680 calls, 944M tokens); 21 subagents made 151-400
calls each and used 1.09B tokens; 9,200 Bash calls kept ~70-result outputs over 20k chars in
context for the rest of the session. The context-budget and lean-worker rules
(`.claude/rules/context-management.md`) exist as prose and were not being followed — this
script is the report-only measurement that makes the waste visible before any enforcement is
built. Report-only by design (like `measure_outcomes.py`): it prints numbers, never a
pass/fail verdict.

Transcript layout (same discovery approach as `cost_ledger.py`, not imported from it — this
script has no dependency on the cost-ledger's ledger/ USD machinery, just the walking idea):
    <project-slug>/*.jsonl                            - top-level (main) session transcripts
    <project-slug>/<session>/subagents/agent-*.jsonl  - subagent transcripts
A transcript is classified "sub" when its parent directory is named `subagents` OR its
basename starts with `agent-`; everything else is "main". Each assistant message line carries
`message.usage` (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`,
`output_tokens`) and `message.model`; a message's "context" for a call is the sum of the three
input-side fields (what was actually sent on that call, cache included). `tool_use` blocks
live in `message.content` (a list) with `type == "tool_use"` and a `name`. The first user
record's `message.content` (a string, or a list of text blocks) gives the first user message
for a transcript's preview column. A line that fails `json.loads`, or whose shape is not what
is expected, is skipped and counted into `skipped_lines` - never fatal, one bad line/file must
never abort the scan.

Only files with `st_mtime` within the last `--days` are scanned (default 7) - this is a
report over RECENT activity, not the whole historical tree.

Sections printed (plain text) or returned (`--json`):
    1. totals            - transcripts, calls, total input tokens, output tokens, skipped_lines
    2. prelude share      - sum(first_call_context * calls) as tokens and % of total input
    3. top transcripts    - by total input, `--top` (default 20) rows
    4. subagent histogram - by call-count bucket: <=20, 21-60, 61-150, 151-400, >400
    5. tool-call counts   - by tool name, across all transcripts
    6. per-model totals   - input/output/cache tokens summed by model

CLI:
    python scripts/context_report.py [--days 7] [--top 20] [--json] [--projects-dir PATH]
"""

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

HISTOGRAM_BUCKETS = [
    (0, 20, "<=20"),
    (21, 60, "21-60"),
    (61, 150, "61-150"),
    (151, 400, "151-400"),
    (401, float("inf"), ">400"),
]


def default_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def is_subagent_path(jsonl_path: Path) -> bool:
    """A transcript is a subagent transcript when it sits in a `subagents/` directory or its
    own basename starts with `agent-` (both shapes are seen on disk depending on CC version)."""
    return jsonl_path.parent.name == "subagents" or jsonl_path.stem.startswith("agent-")


def _call_context(usage: dict) -> int:
    return (
        (usage.get("input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
    )


def _first_user_preview(entry: dict) -> str | None:
    message = entry.get("message") or {}
    if message.get("role") != "user":
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = ""
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text") or ""
                break
    else:
        return None
    text = text.strip()
    return text[:70] if text else None


@dataclass
class TranscriptSummary:
    path: str
    project: str
    kind: str  # "main" or "sub"
    calls: int = 0
    total_input: int = 0
    output: int = 0
    first_call_context: int = 0
    last_call_context: int = 0
    dominant_model: str = "unknown"
    first_user_preview: str | None = None
    model_calls: Counter = field(default_factory=Counter)
    tool_counts: Counter = field(default_factory=Counter)
    model_tokens: dict = field(default_factory=dict)  # model -> token-kind totals


def _empty_model_bucket() -> dict:
    return {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}


def read_transcript(jsonl_path: Path, projects_dir: Path, stats: dict) -> TranscriptSummary | None:
    try:
        rel = jsonl_path.relative_to(projects_dir)
        project = rel.parts[0] if rel.parts else "unknown"
    except ValueError:
        project = "unknown"

    kind = "sub" if is_subagent_path(jsonl_path) else "main"
    summary = TranscriptSummary(path=str(jsonl_path), project=project, kind=kind)
    saw_first_user = False

    try:
        fh = open(jsonl_path, encoding="utf-8")
    except OSError:
        stats["skipped_files"] = stats.get("skipped_files", 0) + 1
        return None

    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                stats["skipped_lines"] = stats.get("skipped_lines", 0) + 1
                continue
            if not isinstance(entry, dict):
                stats["skipped_lines"] = stats.get("skipped_lines", 0) + 1
                continue

            if not saw_first_user:
                preview = _first_user_preview(entry)
                if preview is not None:
                    summary.first_user_preview = preview
                    saw_first_user = True

            message = entry.get("message")
            if not isinstance(message, dict):
                continue

            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    name = block.get("name") or "unknown"
                    summary.tool_counts[name] += 1

            usage = message.get("usage")
            if not usage:
                continue
            model = message.get("model") or "unknown"
            context = _call_context(usage)
            output_tokens = usage.get("output_tokens") or 0

            summary.calls += 1
            summary.total_input += context
            summary.output += output_tokens
            if summary.calls == 1:
                summary.first_call_context = context
            summary.last_call_context = context
            summary.model_calls[model] += 1

            bucket = summary.model_tokens.setdefault(model, _empty_model_bucket())
            bucket["input"] += usage.get("input_tokens") or 0
            bucket["output"] += output_tokens
            bucket["cache_read"] += usage.get("cache_read_input_tokens") or 0
            bucket["cache_creation"] += usage.get("cache_creation_input_tokens") or 0

    if summary.model_calls:
        summary.dominant_model = summary.model_calls.most_common(1)[0][0]
    return summary


def discover_transcripts(projects_dir: Path, since_ts: float, stats: dict):
    """Yield every `*.jsonl` under `projects_dir` whose `st_mtime` is >= `since_ts`."""
    if not projects_dir.is_dir():
        return
    try:
        project_dirs = sorted(p for p in projects_dir.iterdir() if p.is_dir())
    except OSError:
        stats["skipped_files"] = stats.get("skipped_files", 0) + 1
        return
    for project_dir in project_dirs:
        try:
            jsonl_files = sorted(project_dir.rglob("*.jsonl"))
        except OSError:
            stats["skipped_files"] = stats.get("skipped_files", 0) + 1
            continue
        for jsonl_path in jsonl_files:
            try:
                if jsonl_path.stat().st_mtime < since_ts:
                    continue
            except OSError:
                stats["skipped_files"] = stats.get("skipped_files", 0) + 1
                continue
            yield jsonl_path


def collect_summaries(projects_dir: Path, days: int, stats: dict, now: float | None = None) -> list[TranscriptSummary]:
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    since_ts = now - days * 86400
    summaries = []
    for jsonl_path in discover_transcripts(projects_dir, since_ts, stats):
        summary = read_transcript(jsonl_path, projects_dir, stats)
        if summary is not None:
            summaries.append(summary)
    return summaries


def histogram_bucket(calls: int) -> str:
    for low, high, label in HISTOGRAM_BUCKETS:
        if low <= calls <= high:
            return label
    return HISTOGRAM_BUCKETS[-1][2]


def build_report(summaries: list[TranscriptSummary], top: int, stats: dict) -> dict:
    total_input = sum(s.total_input for s in summaries)
    total_output = sum(s.output for s in summaries)
    total_calls = sum(s.calls for s in summaries)

    prelude_tokens = sum(s.first_call_context * s.calls for s in summaries)
    prelude_pct = (prelude_tokens / total_input * 100) if total_input else 0.0

    top_transcripts = sorted(summaries, key=lambda s: s.total_input, reverse=True)[:top]

    histogram: dict[str, dict] = {
        label: {"count": 0, "tokens": 0} for _, _, label in HISTOGRAM_BUCKETS
    }
    for s in summaries:
        if s.kind != "sub":
            continue
        label = histogram_bucket(s.calls)
        histogram[label]["count"] += 1
        histogram[label]["tokens"] += s.total_input

    tool_counts: Counter = Counter()
    for s in summaries:
        tool_counts.update(s.tool_counts)

    model_totals: dict = {}
    for s in summaries:
        for model, bucket in s.model_tokens.items():
            totals = model_totals.setdefault(model, _empty_model_bucket())
            for kind in totals:
                totals[kind] += bucket[kind]

    return {
        "totals": {
            "transcripts": len(summaries),
            "calls": total_calls,
            "total_input_tokens": total_input,
            "output_tokens": total_output,
            "skipped_lines": stats.get("skipped_lines", 0),
            "skipped_files": stats.get("skipped_files", 0),
        },
        "prelude_share": {
            "tokens": prelude_tokens,
            "pct_of_total_input": round(prelude_pct, 2),
        },
        "top_transcripts": [
            {
                "project": s.project,
                "kind": s.kind,
                "calls": s.calls,
                "first_call_context": s.first_call_context,
                "last_call_context": s.last_call_context,
                "total_input": s.total_input,
                "output": s.output,
                "dominant_model": s.dominant_model,
                "first_user_preview": s.first_user_preview,
            }
            for s in top_transcripts
        ],
        "subagent_histogram": histogram,
        "tool_call_counts": dict(tool_counts.most_common()),
        "per_model_totals": model_totals,
    }


def format_report(report: dict, days: int) -> str:
    lines = [f"Context-usage report - last {days} day(s)", ""]

    t = report["totals"]
    lines.append("1. Totals")
    lines.append(f"   transcripts={t['transcripts']} calls={t['calls']} "
                 f"total_input_tokens={t['total_input_tokens']:,} output_tokens={t['output_tokens']:,} "
                 f"skipped_lines={t['skipped_lines']} skipped_files={t['skipped_files']}")
    lines.append("")

    p = report["prelude_share"]
    lines.append("2. Fixed-prelude share")
    lines.append(f"   {p['tokens']:,} tokens ({p['pct_of_total_input']:.2f}% of total input)")
    lines.append("")

    lines.append("3. Top transcripts by total input")
    for row in report["top_transcripts"]:
        preview = row["first_user_preview"] or ""
        lines.append(
            f"   [{row['kind']:4s}] {row['project']:30s} calls={row['calls']:5d} "
            f"first_ctx={row['first_call_context']:,} last_ctx={row['last_call_context']:,} "
            f"total_input={row['total_input']:,} output={row['output']:,} "
            f"model={row['dominant_model']:20s} \"{preview}\""
        )
    lines.append("")

    lines.append("4. Subagent histogram (by call count)")
    for _, _, label in HISTOGRAM_BUCKETS:
        bucket = report["subagent_histogram"][label]
        lines.append(f"   {label:8s} count={bucket['count']:4d} tokens={bucket['tokens']:,}")
    lines.append("")

    lines.append("5. Tool-call counts")
    for name, count in report["tool_call_counts"].items():
        lines.append(f"   {name:30s} {count:,}")
    lines.append("")

    lines.append("6. Per-model totals")
    for model, bucket in report["per_model_totals"].items():
        lines.append(
            f"   {model:30s} input={bucket['input']:,} output={bucket['output']:,} "
            f"cache_read={bucket['cache_read']:,} cache_creation={bucket['cache_creation']:,}"
        )

    return "\n".join(lines)


def _main() -> int:
    p = argparse.ArgumentParser(description="Context/token usage report over recent transcripts.")
    p.add_argument("--days", type=int, default=7, help="lookback window in days (default 7)")
    p.add_argument("--top", type=int, default=20, help="number of top transcripts to show (default 20)")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    p.add_argument("--projects-dir", default=None, help="override the Claude Code transcripts dir")
    args = p.parse_args()

    projects_dir = Path(args.projects_dir) if args.projects_dir else default_projects_dir()
    stats: dict = {}
    summaries = collect_summaries(projects_dir, args.days, stats)
    report = build_report(summaries, args.top, stats)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_report(report, args.days))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
