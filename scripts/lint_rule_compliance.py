#!/usr/bin/env python3
"""Rule-compliance line-lint (report-only) — fable-window item 5, Part B.

Scores which auto-loaded governance directive lines actually *pay their way*. For each
`# Scope: global` rule file it extracts the imperative directive lines (MUST / MUST NOT /
NEVER / ALWAYS), cross-references the available runtime telemetry (the gitignored
`.claude/.*-misses.log` / `.overask-violations.log` files), and classifies each directive:

    KEEP    — enforced by a wired hook AND its telemetry shows compliance (few misses)
    REWRITE — enforced but the telemetry shows SYSTEMATIC non-compliance (make it more
              machine-checkable, or the wording isn't landing)
    DEMOTE  — ZERO measurable signal: unenforceable prose with no telemetry and no hook —
              belongs in skill docs, not an always-loaded rule
    DELETE  — the SAME directive is restated in >=2 rule files (redundant duplicate)

This changes NOTHING by itself. It is evidence FOR the delete-the-harness audit (Part C) and
future rule curation. Telemetry is optional: when a log is absent (they are gitignored, so absent
in CI / a fresh worktree) the script degrades gracefully — every directive falls to the static
heuristic (enforced-concept-with-hook vs pure-prose) and reports "no telemetry available".

Usage:
    PYTHONPATH=. python scripts/lint_rule_compliance.py                 # markdown to stdout
    PYTHONPATH=. python scripts/lint_rule_compliance.py --json          # machine-readable
    PYTHONPATH=. python scripts/lint_rule_compliance.py --rules-dir X --telemetry-dir Y
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES_DIR = ROOT / ".claude" / "rules"
DEFAULT_TELEMETRY_DIR = ROOT / ".claude"

# A directive line = an imperative governance clause. Matched case-sensitively on the UPPERCASE
# keyword so ordinary prose ("you must read") does not trip it — hub rules use the SHOUTED form.
DIRECTIVE_RE = re.compile(r"\b(MUST NOT|MUST|NEVER|ALWAYS)\b")

# keyword (lowercased, searched in the directive text) -> the telemetry log that measures it.
# These are the three enforcement backstops that actually accrue signal today.
CONCEPT_LOGS: dict[str, str] = {
    "enhanced": ".enhance-misses.log",
    "enhance": ".enhance-misses.log",
    "banner": ".enhance-misses.log",
    "grade card": ".enhance-misses.log",
    "strengthen": ".enhance-misses.log",
    "reviewer": ".enhance-misses.log",
    "over-ask": ".overask-violations.log",
    "overask": ".overask-violations.log",
    "narrate": ".overask-violations.log",
    "decide": ".overask-violations.log",
    "don't ask": ".overask-violations.log",
    "offer": ".overask-violations.log",
    "verifier": ".verifier-misses.log",
    "independent verif": ".verifier-misses.log",
    "supervisor": ".verifier-misses.log",
    "code review": ".verifier-misses.log",
    "code-review": ".verifier-misses.log",
}

# Absolute-miss threshold in the window above which an ENFORCED directive is judged systematically
# non-complied (REWRITE) rather than complied (KEEP). Used when a true miss-RATE denominator is not
# derivable (the honest default: we lack per-directive turn totals). Overridable via --min-misses.
DEFAULT_MIN_MISSES = 20
DEFAULT_WINDOW_DAYS = 30

_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T[\d:]+Z?")


def extract_directives(text: str, rule_name: str) -> list[dict]:
    """Every imperative directive line in a rule file, with its 1-based line number."""
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            # headings/blockquotes are framing, not directives — but a list item with a
            # directive keyword IS one. (A `#`-heading is skipped; inline directives in prose are kept.)
            if not DIRECTIVE_RE.search(line):
                continue
        if DIRECTIVE_RE.search(line):
            # strip markdown list/emphasis noise for the comparable text
            clean = re.sub(r"^[-*\d.\s]+", "", line)
            clean = re.sub(r"[*`]", "", clean).strip()
            out.append({"rule": rule_name, "line": i, "text": clean})
    return out


def associate_log(directive_text: str) -> str | None:
    """The telemetry log that measures this directive's concept, or None (no measurable signal)."""
    low = directive_text.lower()
    for kw, log in CONCEPT_LOGS.items():
        if kw in low:
            return log
    return None


def count_recent(log_path: Path, window_days: int, now: datetime | None = None) -> int:
    """Count log lines whose leading YYYY-MM-DD timestamp is within `window_days` of `now`."""
    if not log_path.exists():
        return 0
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    n = 0
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _TS_RE.match(line.strip())
        if not m:
            continue
        try:
            ts = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ts >= cutoff:
            n += 1
    return n


def load_telemetry(telemetry_dir: Path, window_days: int, now: datetime | None = None) -> dict:
    """Recent hit-count per known log (0 when the log is absent — the graceful-degrade path)."""
    logs = set(CONCEPT_LOGS.values())
    return {log: count_recent(telemetry_dir / log, window_days, now) for log in logs}


def classify(directive: dict, telemetry: dict, dup_texts: set[str], min_misses: int) -> dict:
    """Assign KEEP / REWRITE / DEMOTE / DELETE with the evidence that drove it."""
    norm = re.sub(r"\s+", " ", directive["text"].lower()).strip()
    log = associate_log(directive["text"])
    misses = telemetry.get(log, 0) if log else 0

    if norm in dup_texts:
        verdict = "DELETE"
        why = "duplicate — this exact directive is restated in >=1 other rule file (redundant prose)"
    elif log is None:
        verdict = "DEMOTE"
        why = "zero measurable signal — no telemetry and no wired hook measures this; unenforceable prose belongs in skill docs"
    elif misses >= min_misses:
        verdict = "REWRITE"
        why = f"systematic non-compliance — {misses} miss(es) in the window on {log}; the prose isn't landing, make it machine-checkable"
    else:
        verdict = "KEEP"
        why = f"enforced + complied — {misses} miss(es) in the window on {log} (below the {min_misses} threshold)"

    return {**directive, "verdict": verdict, "associated_log": log,
            "recent_misses": misses, "why": why}


def find_duplicates(all_directives: list[dict]) -> set[str]:
    """Normalized directive texts that appear in >=2 DIFFERENT rule files."""
    by_text: dict[str, set[str]] = defaultdict(set)
    for d in all_directives:
        norm = re.sub(r"\s+", " ", d["text"].lower()).strip()
        by_text[norm].add(d["rule"])
    return {t for t, files in by_text.items() if len(files) >= 2 and t}


def is_scope_global(text: str) -> bool:
    return "# Scope: global" in "\n".join(text.splitlines()[:6])


def run(rules_dir: Path, telemetry_dir: Path, window_days: int, min_misses: int,
        now: datetime | None = None) -> dict:
    telemetry = load_telemetry(telemetry_dir, window_days, now)
    all_directives: list[dict] = []
    scanned: list[str] = []
    for rule_path in sorted(rules_dir.glob("*.md")):
        text = rule_path.read_text(encoding="utf-8", errors="replace")
        if not is_scope_global(text):
            continue
        scanned.append(rule_path.name)
        all_directives.extend(extract_directives(text, rule_path.name))

    dup_texts = find_duplicates(all_directives)
    # DELETE marks the SECOND+ occurrence; keep the first occurrence as its normal verdict so we
    # don't recommend deleting the concept entirely.
    seen: set[str] = set()
    results = []
    for d in all_directives:
        norm = re.sub(r"\s+", " ", d["text"].lower()).strip()
        is_dup_later = norm in dup_texts and norm in seen
        seen.add(norm)
        res = classify(d, telemetry, dup_texts if is_dup_later else set(), min_misses)
        results.append(res)

    any_log_present = any((telemetry_dir / log).exists() for log in set(CONCEPT_LOGS.values()))
    summary = defaultdict(int)
    for r in results:
        summary[r["verdict"]] += 1
    return {
        "scanned_rules": scanned,
        "telemetry_available": any_log_present,
        "telemetry_window_days": window_days,
        "min_misses_threshold": min_misses,
        "telemetry_counts": telemetry,
        "summary": dict(summary),
        "directives": results,
    }


def render_markdown(report: dict) -> str:
    lines = ["# Rule-compliance line-lint", ""]
    lines.append(f"- Rules scanned (`# Scope: global`): {len(report['scanned_rules'])} "
                 f"— {', '.join(report['scanned_rules'])}")
    lines.append(f"- Directives found: {len(report['directives'])}")
    lines.append(f"- Telemetry available: **{report['telemetry_available']}** "
                 f"(window {report['telemetry_window_days']}d, systematic-miss threshold "
                 f"{report['min_misses_threshold']})")
    if report["telemetry_available"]:
        counts = ", ".join(f"{k}={v}" for k, v in sorted(report["telemetry_counts"].items()))
        lines.append(f"- Recent telemetry counts: {counts}")
    else:
        lines.append("- Recent telemetry counts: _none on disk (gitignored logs absent) — "
                     "verdicts fall back to the static enforced-vs-prose heuristic_")
    s = report["summary"]
    lines.append(f"- Verdicts: KEEP={s.get('KEEP',0)}, REWRITE={s.get('REWRITE',0)}, "
                 f"DEMOTE={s.get('DEMOTE',0)}, DELETE={s.get('DELETE',0)}")
    lines.append("")
    lines.append("| Rule | Line | Verdict | Log | Misses | Directive | Why |")
    lines.append("|---|---|---|---|---|---|---|")
    order = {"REWRITE": 0, "DELETE": 1, "DEMOTE": 2, "KEEP": 3}
    for r in sorted(report["directives"], key=lambda x: (order.get(x["verdict"], 9), x["rule"], x["line"])):
        txt = r["text"] if len(r["text"]) <= 90 else r["text"][:87] + "..."
        txt = txt.replace("|", "\\|")
        why = r["why"].replace("|", "\\|")
        lines.append(f"| {r['rule']} | {r['line']} | **{r['verdict']}** | "
                     f"{r['associated_log'] or '—'} | {r['recent_misses']} | {txt} | {why} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Rule-compliance line-lint (report-only).")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument("--rules-dir", type=Path, default=DEFAULT_RULES_DIR)
    ap.add_argument("--telemetry-dir", type=Path, default=DEFAULT_TELEMETRY_DIR)
    ap.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    ap.add_argument("--min-misses", type=int, default=DEFAULT_MIN_MISSES)
    args = ap.parse_args()
    report = run(args.rules_dir, args.telemetry_dir, args.window_days, args.min_misses)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report), end="")


if __name__ == "__main__":
    main()
