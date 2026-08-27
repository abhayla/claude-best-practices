"""Tests for the rule-compliance line-lint (fable-window item 5, Part B).

Fixture rule files + fixture telemetry logs -> expected KEEP / REWRITE / DEMOTE / DELETE.
Pins the graceful-degrade path (no telemetry on disk) and the time-window filtering.
"""
from datetime import datetime, timezone
from pathlib import Path

from scripts.lint_rule_compliance import (
    associate_log,
    count_recent,
    extract_directives,
    run,
)

NOW = datetime(2026, 7, 10, tzinfo=timezone.utc)


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _verdicts(report: dict) -> dict:
    """Map 'rule:line' -> verdict for easy assertions."""
    return {f"{d['rule']}:{d['line']}": d["verdict"] for d in report["directives"]}


def test_extract_directives_finds_shouted_imperatives():
    text = "# Scope: global\n\n- You MUST run tests.\n- normal prose line.\n- NEVER commit secrets.\n"
    ds = extract_directives(text, "x.md")
    texts = [d["text"] for d in ds]
    assert any("MUST run tests" in t for t in texts)
    assert any("NEVER commit secrets" in t for t in texts)
    assert not any("normal prose" in t for t in texts)


def test_associate_log_maps_concepts():
    assert associate_log("start every response with the *Enhanced:* banner") == ".enhance-misses.log"
    assert associate_log("do NOT over-ask; decide reversible work") == ".overask-violations.log"
    assert associate_log("run the independent verifier before done") == ".verifier-misses.log"
    assert associate_log("MUST keep product code outside the git tree") is None


def test_count_recent_respects_window(tmp_path):
    log = tmp_path / ".enhance-misses.log"
    log.write_text(
        "2026-07-09T10:00:00Z\tenhance-block-miss\n"   # in window
        "2026-06-01T10:00:00Z\tenhance-block-miss\n"   # out of window (>30d)
        "garbage line without timestamp\n",
        encoding="utf-8",
    )
    assert count_recent(log, window_days=30, now=NOW) == 1
    assert count_recent(log, window_days=90, now=NOW) == 2


def test_rewrite_when_enforced_but_systematically_missed(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel"
    tel.mkdir()
    _write(rules / "enhance.md", "# Scope: global\n\n- The *Enhanced:* banner MUST open every response.\n")
    (tel / ".enhance-misses.log").write_text(
        "\n".join(f"2026-07-0{d}T10:00:00Z\tenhance-block-miss" for d in range(1, 8)) + "\n",
        encoding="utf-8",
    )
    report = run(rules, tel, window_days=30, min_misses=5, now=NOW)
    assert _verdicts(report)["enhance.md:3"] == "REWRITE"


def test_keep_when_enforced_and_compliant(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel"
    tel.mkdir()
    _write(rules / "enhance.md", "# Scope: global\n\n- The *Enhanced:* banner MUST open every response.\n")
    (tel / ".enhance-misses.log").write_text("2026-07-09T10:00:00Z\tenhance-block-miss\n", encoding="utf-8")
    report = run(rules, tel, window_days=30, min_misses=20, now=NOW)
    assert _verdicts(report)["enhance.md:3"] == "KEEP"


def test_demote_unenforceable_prose(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel"
    tel.mkdir()
    _write(rules / "product.md", "# Scope: global\n\n- MUST keep product code OUTSIDE the git tree.\n")
    report = run(rules, tel, window_days=30, min_misses=20, now=NOW)
    assert _verdicts(report)["product.md:3"] == "DEMOTE"


def test_delete_duplicate_directive_across_files(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel"
    tel.mkdir()
    dup = "- MUST keep product code OUTSIDE the git tree.\n"
    _write(rules / "a.md", "# Scope: global\n\n" + dup)
    _write(rules / "b.md", "# Scope: global\n\n" + dup)
    report = run(rules, tel, window_days=30, min_misses=20, now=NOW)
    v = _verdicts(report)
    verdicts = sorted([v["a.md:3"], v["b.md:3"]])
    # first occurrence keeps its base verdict (DEMOTE), the later one is DELETE
    assert "DELETE" in verdicts, verdicts
    assert "DEMOTE" in verdicts, verdicts


def test_graceful_degrade_without_telemetry(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel-absent"  # never created -> logs absent
    _write(rules / "enhance.md", "# Scope: global\n\n- The *Enhanced:* banner MUST open every response.\n")
    report = run(rules, tel, window_days=30, min_misses=20, now=NOW)
    assert report["telemetry_available"] is False
    # no telemetry -> cannot claim non-compliance -> KEEP (safe default), never a false REWRITE
    assert _verdicts(report)["enhance.md:3"] == "KEEP"


def test_only_scope_global_rules_scanned(tmp_path):
    rules = tmp_path / "rules"
    tel = tmp_path / "tel"
    tel.mkdir()
    _write(rules / "global.md", "# Scope: global\n\n- MUST do X globally.\n")
    _write(rules / "scoped.md", "---\npaths: ['*.py']\n---\n\n- MUST do Y only for py.\n")
    report = run(rules, tel, window_days=30, min_misses=20, now=NOW)
    assert "global.md" in report["scanned_rules"]
    assert "scoped.md" not in report["scanned_rules"]
