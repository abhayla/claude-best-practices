"""Tests for REQ-S007 + REQ-S008 scaffolding — config-only scaffolding.

These knobs exist to make future activation a config-change-only edit; they
MUST default to null (no behavior change) and MUST cite their spec trigger
so the next reviewer can tell why they're present.

This is intentionally thin: the keys exist, are null, and are documented.
Runtime enforcement is deferred until a real trigger fires — activating
without evidence would violate YAGNI (claude-behavior.md rule 21) and
pattern-curation's reactive-not-speculative policy.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = REPO_ROOT / "core" / ".claude" / "config" / "test-pipeline.yml"


def _cfg() -> dict:
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))


def _raw() -> str:
    return CONFIG_FILE.read_text(encoding="utf-8")


# ── REQ-S007: weighted dispatch counter scaffold ────────────────────────────


def test_dispatch_weights_key_exists():
    cfg = _cfg()
    assert "concurrency" in cfg
    assert "dispatch_weights" in cfg["concurrency"], (
        "concurrency.dispatch_weights MUST be declared as a null-default scaffold "
        "for REQ-S007"
    )


def test_dispatch_weights_defaults_to_null():
    """Null default is the contract — any non-null value would silently
    activate weighted accounting without a trigger. YAGNI guard."""
    cfg = _cfg()
    assert cfg["concurrency"]["dispatch_weights"] is None, (
        "dispatch_weights MUST default to null (YAGNI — only activate on trigger)"
    )


def test_dispatch_weights_cites_spec_ref():
    raw = _raw()
    dispatch_block = raw.split("dispatch_weights:", 1)[0].splitlines()[-12:]
    header = "\n".join(dispatch_block)
    assert "REQ-S007" in header, (
        "dispatch_weights block MUST cite REQ-S007 so future editors see the trigger"
    )
    assert "TRADE-OFF-1" in header, (
        "dispatch_weights header MUST name the trade-off (TRADE-OFF-1) for audit trail"
    )


# ── REQ-S008: per-phase wall-clock timeouts scaffold ────────────────────────


def test_max_lane_minutes_key_exists():
    cfg = _cfg()
    assert "budget" in cfg
    assert "max_lane_minutes" in cfg["budget"], (
        "budget.max_lane_minutes MUST be declared as null-default scaffold for REQ-S008"
    )


def test_max_lane_minutes_defaults_to_null():
    cfg = _cfg()
    assert cfg["budget"]["max_lane_minutes"] is None, (
        "max_lane_minutes MUST default to null (only pipeline-wide timeout applies today)"
    )


def test_max_triage_minutes_key_exists():
    cfg = _cfg()
    assert "max_triage_minutes" in cfg["budget"], (
        "budget.max_triage_minutes MUST be declared as null-default scaffold for REQ-S008"
    )


def test_max_triage_minutes_defaults_to_null():
    cfg = _cfg()
    assert cfg["budget"]["max_triage_minutes"] is None


def test_s008_cites_spec_ref_and_trade_off():
    raw = _raw()
    # Grab the 12 lines immediately before `max_lane_minutes:` — the doc block.
    header_lines = raw.split("max_lane_minutes:", 1)[0].splitlines()[-12:]
    header = "\n".join(header_lines)
    assert "REQ-S008" in header, (
        "S008 scaffold block MUST cite REQ-S008"
    )
    assert "TRADE-OFF-2" in header, (
        "S008 scaffold block MUST name TRADE-OFF-2 for audit trail"
    )


# ── Invariant: pipeline-wide timeout remains authoritative until trigger ────


def test_pipeline_wide_timeout_unchanged():
    """REQ-S008 scaffold MUST NOT alter the pre-existing pipeline-wide
    timeout default — activating S008 is a separate decision."""
    cfg = _cfg()
    assert cfg["budget"]["max_wall_clock_minutes"] == 90, (
        "Pre-existing max_wall_clock_minutes MUST remain 90 — S008 scaffold is additive only"
    )


def test_dispatch_budget_unchanged():
    """REQ-S007 scaffold MUST NOT alter the pre-existing dispatch cap."""
    cfg = _cfg()
    assert cfg["budget"]["max_total_dispatches"] == 100, (
        "Pre-existing max_total_dispatches MUST remain 100 — S007 scaffold is additive only"
    )
