"""Tests for REQ-S004 — config-driven per-category auto-heal matrix.

Static checks only — verify the analyzer agent body declares the config read
procedure, fallback policy, and ALLOWED enum, and that the shipped
test-pipeline.yml auto_heal: block is valid and covers every category
mentioned in spec §3.6.

Runtime behavior testing (actual config loading by a dispatched agent) is
exercised via /agent-evaluator scenarios when authored, and via end-to-end
smoke runs.
"""

from pathlib import Path
import re

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = REPO_ROOT / "core" / ".claude"
AGENTS_DIR = CORE_CLAUDE / "agents"
CONFIG_DIR = CORE_CLAUDE / "config"
SPEC_FILE = REPO_ROOT / "docs" / "specs" / "test-pipeline-three-lane-spec.md"

ALLOWED_ACTIONS = {
    "AUTO_HEAL",
    "AUTO_HEAL_WITH_FLAG",
    "ISSUE_ONLY",
    "QUARANTINE",
    "RETRY_INFRA",
}


def _analyzer_body() -> str:
    return (AGENTS_DIR / "test-failure-analyzer-agent.md").read_text(encoding="utf-8")


def _pipeline_yml() -> dict:
    return yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))


# ── REQ-S004: config shape + enum validity ──────────────────────────────────


def test_auto_heal_block_exists_in_pipeline_yml():
    cfg = _pipeline_yml()
    assert "auto_heal" in cfg, "test-pipeline.yml MUST declare auto_heal: block (REQ-S004)"
    assert isinstance(cfg["auto_heal"], dict), "auto_heal: MUST be a mapping"
    assert len(cfg["auto_heal"]) >= 1, "auto_heal: MUST declare at least one category"


def test_auto_heal_values_are_in_allowed_enum():
    """Every value in auto_heal: MUST be one of the 5 allowed actions.

    Keeps config honest — typos or invented actions would silently downgrade
    to ISSUE_ONLY at runtime per the fallback policy, but we catch them here.
    """
    cfg = _pipeline_yml()
    for category, action in cfg["auto_heal"].items():
        assert action in ALLOWED_ACTIONS, (
            f"auto_heal[{category}] = {action!r} is not in ALLOWED enum "
            f"{sorted(ALLOWED_ACTIONS)}"
        )


def test_auto_heal_block_is_commented_with_spec_ref():
    """The shipped comment MUST cite REQ-S004 and mark the block load-bearing,
    not forward-compat — this prevents future editors from treating it as dead."""
    raw = (CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8")
    auto_heal_section = raw.split("auto_heal:", 1)[0].splitlines()[-10:]
    header_block = "\n".join(auto_heal_section)
    assert "REQ-S004" in header_block, (
        "auto_heal: header MUST cite REQ-S004 so future editors see it's load-bearing"
    )
    assert "read by test-failure-analyzer-agent" in header_block.lower() or (
        "read by" in header_block.lower()
    ), "auto_heal: header MUST state which consumer reads it"


# ── REQ-S004: spec §3.6 drift check ─────────────────────────────────────────


def test_every_spec_category_has_an_auto_heal_entry():
    """Each category named in spec §3.6 auto-fix matrix MUST have a
    corresponding auto_heal: entry. Detects silent drift when the spec
    adds a new category but the config forgets to wire it."""
    spec_text = SPEC_FILE.read_text(encoding="utf-8")
    section_start = spec_text.index("### 3.6 Auto-Fix Authority Matrix")
    section_end = spec_text.index("### 3.7", section_start)
    section = spec_text[section_start:section_end]

    category_pattern = re.compile(r"\|\s*`([A-Z_]+)`", re.MULTILINE)
    spec_categories = {m.group(1) for m in category_pattern.finditer(section)}

    assert spec_categories, "§3.6 parse produced zero categories — parser may be broken"

    cfg = _pipeline_yml()
    configured = set(cfg["auto_heal"].keys())

    missing_in_config = spec_categories - configured
    assert not missing_in_config, (
        f"Spec §3.6 names these categories but auto_heal: config is missing them: "
        f"{sorted(missing_in_config)}"
    )


# ── REQ-S004: analyzer body declares the read procedure ─────────────────────


def test_analyzer_nn_references_config_path():
    """NN#6 MUST reference the config path so the agent reads from YAML,
    not from LLM recall of spec §3.6."""
    body = _analyzer_body()
    assert "test-pipeline.yml" in body, (
        "NN#6 MUST reference test-pipeline.yml so the analyzer reads config, not LLM recall"
    )
    assert "REQ-S004" in body, (
        "Analyzer body MUST cite REQ-S004 so future readers find the provenance"
    )


def test_analyzer_declares_both_config_path_candidates():
    """Downstream projects override via `.claude/config/test-pipeline.yml`; the
    hub itself uses `core/.claude/config/test-pipeline.yml`. Both MUST be named."""
    body = _analyzer_body()
    assert ".claude/config/test-pipeline.yml" in body, (
        "Analyzer MUST reference downstream config path"
    )
    assert "core/.claude/config/test-pipeline.yml" in body, (
        "Analyzer MUST reference hub config path as fallback"
    )


def test_analyzer_declares_allowed_action_enum():
    """The 5 allowed values MUST be enumerated in the agent body so the LLM
    doesn't invent a sixth."""
    body = _analyzer_body()
    for action in ALLOWED_ACTIONS:
        assert action in body, (
            f"Analyzer body MUST enumerate allowed action {action!r} "
            f"(REQ-S004 ALLOWED enum)"
        )


def test_analyzer_declares_fallback_policy():
    """Missing/invalid config MUST NOT block the pipeline — the agent MUST
    fall back to ISSUE_ONLY and emit a WARN line."""
    body = _analyzer_body()
    assert "Fallback policy" in body or "fallback policy" in body.lower(), (
        "Analyzer MUST document its fallback policy"
    )
    assert "ISSUE_ONLY" in body, "Fallback policy MUST name ISSUE_ONLY as the safe default"
    assert "WARN" in body or "warn" in body.lower(), (
        "Fallback policy MUST require a WARN log line per error-handling.md 'no silent failures'"
    )


def test_analyzer_confidence_override_preserved():
    """NN#6's confidence < 0.85 → ISSUE_ONLY override MUST survive the
    config-driven refactor — it's independent of the config value."""
    body = _analyzer_body()
    assert "0.85" in body, (
        "Confidence threshold 0.85 MUST remain documented in NN#6"
    )
    assert re.search(r"confidence\s*(<|below|under).*0\.85", body, re.IGNORECASE), (
        "Analyzer MUST state the confidence-< 0.85 override explicitly"
    )


# ── REQ-S004: analyzer version bumped ────────────────────────────────────────


def test_analyzer_version_bumped_to_2_3_0():
    body = _analyzer_body()
    version_match = re.search(r'^version:\s*"([\d.]+)"', body, re.MULTILINE)
    assert version_match, "Analyzer frontmatter MUST declare version"
    assert version_match.group(1) == "2.3.0", (
        f"Analyzer version MUST be bumped to 2.3.0 for REQ-S004 "
        f"(was {version_match.group(1)!r})"
    )


# ── REQ-S004: JSON output example includes recommended_action ───────────────


def test_analyzer_output_example_shows_recommended_action():
    """The body's JSON output example MUST include recommended_action so
    the agent and downstream consumers agree on the field name."""
    body = _analyzer_body()
    # The example JSON block lives under ## Output Format
    output_section = body.split("## Output Format", 1)[1].split("##", 1)[0]
    assert '"recommended_action"' in output_section, (
        "Output Format example MUST include the recommended_action field "
        "(REQ-S004 agent output contract)"
    )
    # Both sample entries SHOULD demonstrate different action values so readers
    # see the mapping in action.
    sample_actions = re.findall(r'"recommended_action":\s*"([A-Z_]+)"', output_section)
    assert len(sample_actions) >= 2, (
        "Output Format example SHOULD show at least 2 failures with distinct "
        "recommended_action values to illustrate the matrix"
    )
    assert len(set(sample_actions)) >= 2, (
        "Example failures SHOULD use distinct recommended_action values to "
        "illustrate the matrix (got all identical)"
    )
    assert set(sample_actions) <= ALLOWED_ACTIONS, (
        f"Output Format example uses actions outside ALLOWED enum: "
        f"{sorted(set(sample_actions) - ALLOWED_ACTIONS)}"
    )
