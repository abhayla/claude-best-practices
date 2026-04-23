"""Tests for three-lane test pipeline PR1 scope.

Covers spec §6 success criteria:
- #1, #2, #4 (partial), #5 — track detection, JOIN, schema mismatch
- #18, #19, #27 — accumulate semantics, responsibility cap, e2e-conductor isolation
- #28, #29, #30 — T1 4-category extension, validator allowlist, /agent-evaluator discovery

PR2 success criteria are out of scope — those tests will be added when PR2's
new agents and skills exist.
"""

from pathlib import Path

import pytest
import yaml

from scripts.workflow_quality_gate_validate_patterns import (
    RESPONSIBILITY_ALLOWLIST_PATH,
    RESPONSIBILITY_CAP,
    count_responsibilities,
    load_responsibility_allowlist,
)


REPO_ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = REPO_ROOT / "core" / ".claude"
AGENTS_DIR = CORE_CLAUDE / "agents"
SKILLS_DIR = CORE_CLAUDE / "skills"
CONFIG_DIR = CORE_CLAUDE / "config"
PLAYWRIGHT_DEMO = REPO_ROOT / "scripts" / "tests" / "fixtures" / "playwright-demo"


# ── Spec §3.13 + REQ-M026: state schema bumped to 2.0.0 ─────────────────────


def test_test_pipeline_yml_has_schema_2_0_0():
    """test-pipeline.yml schema_version is bumped to 2.0.0."""
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert cfg["schema_version"] == "2.0.0"


def test_test_pipeline_yml_has_three_lane_blocks():
    """test-pipeline.yml has lanes/track_detection/concurrency/budget blocks."""
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    for required_block in ["lanes", "track_detection", "concurrency", "budget"]:
        assert required_block in cfg, f"Missing block: {required_block}"


def test_lanes_block_has_three_lanes():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    for lane in ["functional", "api", "ui"]:
        assert lane in cfg["lanes"], f"Missing lane: {lane}"
    assert cfg["lanes"]["ui"]["runs_after"] == "functional", "UI lane must wait for functional"


def test_budget_uses_observable_proxies_not_tokens():
    """Budget block uses dispatch count + wall-clock (NOT max_total_tokens — that's a
    nonexistent platform primitive per reviewer-pass-2 N1)."""
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    budget = cfg["budget"]
    assert "max_total_dispatches" in budget
    assert "max_wall_clock_minutes" in budget
    # Make sure the bug from v1.2 didn't sneak back in
    assert "max_total_tokens" not in budget, (
        "max_total_tokens is NOT a Claude Code subagent return field; "
        "use max_total_dispatches + max_wall_clock_minutes (per reviewer-pass-2 N1)"
    )


def test_dedup_hash_includes_commit_sha():
    """Dedup hash uses 3-field formula: (test_id, category, failing_commit_sha_short).
    Closes reviewer-pass-2 N3 (cross-run conflation)."""
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    dedup_fields = cfg["issue_creation"]["dedup_hash_fields"]
    assert dedup_fields == ["test_id", "category", "failing_commit_sha_short"]


# ── Spec §3.1 + REQ-M002: track detection accumulate semantics ───────────────


def test_track_detection_mode_is_accumulate():
    """Detection rules accumulate (closes reviewer Gap 9 / NOT first-match-wins)."""
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert cfg["track_detection"]["detection_mode"] == "accumulate"


def test_overlap_fixture_exists_for_accumulate_test():
    """The accumulate semantics fixture (test in tests/api/ that imports Playwright)
    must exist so accumulate behavior can be empirically tested."""
    overlap_file = PLAYWRIGHT_DEMO / "tests" / "api" / "test_widget.spec.ts"
    assert overlap_file.exists(), (
        f"Overlap fixture missing at {overlap_file}. Required for "
        "test_track_accumulate_semantics."
    )
    content = overlap_file.read_text(encoding="utf-8")
    assert "@playwright/test" in content, "Overlap fixture must import Playwright"


def test_api_path_fixture_exists():
    """The SCHEMA_MISMATCH fixture in tests/api/ must exist."""
    api_file = PLAYWRIGHT_DEMO / "tests" / "api" / "test_users.py"
    assert api_file.exists()
    content = api_file.read_text(encoding="utf-8")
    assert "import httpx" in content, "API fixture must import an HTTP client signal"


def test_logic_bug_unit_fixture_exists():
    """The LOGIC_BUG unit-test fixture must exist."""
    unit_file = PLAYWRIGHT_DEMO / "tests" / "unit" / "test_logic_bug.py"
    assert unit_file.exists()


# ── Spec §3.5 + REQ-M035: responsibility cap with allowlist ──────────────────


def test_responsibility_cap_is_4():
    """Per agent-orchestration.md rule 8."""
    assert RESPONSIBILITY_CAP == 4


def test_allowlist_loads_t2b_inaugural_entry():
    """Allowlist YAML must exist with the failure-triage-agent entry."""
    al = load_responsibility_allowlist()
    assert "failure-triage-agent" in al
    entry = al["failure-triage-agent"]
    assert entry["responsibility_count"] == 5
    assert entry["rule_8_cap"] == 4
    assert entry["deviation"] == 1
    assert entry["justification"]  # non-empty string


def test_t1_responsibility_count_within_cap():
    """T1 (testing-pipeline-master-agent) must be at the cap or below."""
    count = count_responsibilities(AGENTS_DIR / "testing-pipeline-master-agent.md")
    assert count <= RESPONSIBILITY_CAP, (
        f"T1 has {count} responsibilities; rule-8 cap is {RESPONSIBILITY_CAP}. "
        "Either split T1 or add an allowlist entry with justification."
    )


def test_t2a_responsibility_count_within_cap():
    """T2A (test-pipeline-agent) must be at the cap or below post-rewrite."""
    count = count_responsibilities(AGENTS_DIR / "test-pipeline-agent.md")
    assert count <= RESPONSIBILITY_CAP, (
        f"T2A has {count} responsibilities post-rewrite; should be exactly 4 per "
        "spec §3.5 split."
    )


def test_t2b_responsibility_count_matches_allowlist():
    """T2B (failure-triage-agent) skeleton has 5 responsibilities (5 placeholders);
    must match the allowlisted count."""
    count = count_responsibilities(AGENTS_DIR / "failure-triage-agent.md")
    al = load_responsibility_allowlist()
    entry = al["failure-triage-agent"]
    assert count == entry["responsibility_count"], (
        f"T2B has {count} responsibilities but allowlist documents "
        f"{entry['responsibility_count']}. Update either the agent or the allowlist."
    )


def test_responsibility_count_function_handles_missing_section():
    """count_responsibilities returns 0 when ## Core Responsibilities is absent."""
    # Use a rule file as a control — rules don't have Core Responsibilities sections
    rules_file = CORE_CLAUDE / "rules" / "claude-behavior.md"
    if rules_file.exists():
        assert count_responsibilities(rules_file) == 0


# ── Spec §3.7 + REQ-M034: T1 handles 4 new API categories ────────────────────


def test_t1_handles_four_new_api_categories():
    """T1's body MUST mention the 4 new API categories (PR1 extension)."""
    # SUPERSEDED in PR2: PR1 introduced 4 new API categories handled by T1's
    # inline step. PR2's atomic switchover DELETES T1's inline step entirely;
    # T2B (failure-triage-agent) + github-issue-manager-agent now handle all
    # categories via /create-github-issue. See test_pipeline_three_lane_pr2.py
    # for PR2 verification of the deletion + delegation.
    pytest.skip("Superseded by PR2 atomic switchover; T1 inline step deleted")


def test_t1_extension_marked_pr1_temporary():
    """SUPERSEDED in PR2: PR1 marker was a hint for the PR2 implementer.
    PR2 atomic switchover deleted T1's inline step entirely; the marker is
    no longer present (its purpose served). See test_pipeline_three_lane_pr2.py."""
    pytest.skip("Superseded by PR2 atomic switchover; PR1-TEMPORARY marker removed with the deleted step")


# ── Spec §3.2 + REQ-M027/M029: tool grants ───────────────────────────────────


def test_test_healer_agent_has_explicit_tools_field():
    """test-healer-agent must declare tools explicitly (closes reviewer-pass-1 G3)."""
    healer_path = AGENTS_DIR / "test-healer-agent.md"
    content = healer_path.read_text(encoding="utf-8")
    assert "tools:" in content.split("---")[1], (
        "test-healer-agent missing explicit tools: declaration; "
        "without it, the default subagent tool grant may exclude Skill → silent collapse"
    )


def test_test_healer_agent_tools_includes_skill():
    """test-healer-agent tools must include Skill (it invokes /fix-issue in PR2)."""
    healer_path = AGENTS_DIR / "test-healer-agent.md"
    content = healer_path.read_text(encoding="utf-8")
    # Search just the frontmatter
    fm_block = content.split("---")[1]
    tools_line = next(line for line in fm_block.splitlines() if line.startswith("tools:"))
    assert "Skill" in tools_line


def test_fastapi_api_tester_has_skill_tool():
    """fastapi-api-tester-agent tools must include Skill (it invokes /contract-test)."""
    fapi_path = AGENTS_DIR / "fastapi-api-tester-agent.md"
    content = fapi_path.read_text(encoding="utf-8")
    fm_block = content.split("---")[1]
    tools_line = next(line for line in fm_block.splitlines() if line.startswith("tools:"))
    assert "Skill" in tools_line


def test_tester_agent_has_non_negotiable_block():
    """tester-agent must have NON-NEGOTIABLE block per fugazi pattern (REQ-M028)."""
    tester_path = AGENTS_DIR / "tester-agent.md"
    content = tester_path.read_text(encoding="utf-8")
    assert "## NON-NEGOTIABLE" in content


def test_tester_agent_declares_lane_verdict_authority():
    """tester-agent NON-NEGOTIABLE must declare verdict authority by lane (REQ-M028)."""
    tester_path = AGENTS_DIR / "tester-agent.md"
    content = tester_path.read_text(encoding="utf-8")
    nn_section = content.split("## NON-NEGOTIABLE")[1].split("---")[0]
    assert "lane=functional" in nn_section
    assert "lane=api" in nn_section
    assert "NEEDS_CONTRACT_VALIDATION" in nn_section


# ── Spec §3.5 + REQ-M006: failure-triage-agent skeleton ──────────────────────


def test_failure_triage_agent_skeleton_exists():
    assert (AGENTS_DIR / "failure-triage-agent.md").exists()


def test_failure_triage_agent_returns_no_op_in_pr1():
    """Skeleton must declare it returns NO_OP_PR1_SKELETON contract."""
    body = (AGENTS_DIR / "failure-triage-agent.md").read_text(encoding="utf-8")
    assert "NO_OP_PR1_SKELETON" in body


# ── Spec §4 EVALS + REQ-M036: /agent-evaluator skill ─────────────────────────


def test_agent_evaluator_skill_exists():
    skill_path = SKILLS_DIR / "agent-evaluator" / "SKILL.md"
    assert skill_path.exists()


def test_agent_evaluator_separate_from_skill_evaluator():
    """/agent-evaluator must be a distinct skill (not an extension of /skill-evaluator)."""
    skill_evaluator_dir = SKILLS_DIR / "skill-evaluator"
    agent_evaluator_dir = SKILLS_DIR / "agent-evaluator"
    assert skill_evaluator_dir.exists() and (skill_evaluator_dir / "SKILL.md").exists()
    assert agent_evaluator_dir.exists() and (agent_evaluator_dir / "SKILL.md").exists()
    # They must have different names in frontmatter
    se_content = (skill_evaluator_dir / "SKILL.md").read_text(encoding="utf-8")
    ae_content = (agent_evaluator_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "name: skill-evaluator" in se_content
    assert "name: agent-evaluator" in ae_content


def test_agent_evaluator_describes_5_criterion_rubric():
    """The skill body must describe the 5 rubric criteria."""
    body = (SKILLS_DIR / "agent-evaluator" / "SKILL.md").read_text(encoding="utf-8")
    for criterion in [
        "trigger_reliability",
        "output_structure",
        "non_negotiable_adherence",
        "side_effect_correctness",
        "error_propagation",
    ]:
        assert criterion in body, f"Rubric criterion {criterion} missing from /agent-evaluator body"


# ── Spec §3.1 + REQ-M025: e2e-conductor isolation ────────────────────────────


def test_e2e_conductor_uses_separate_namespace():
    """e2e-conductor-agent reads/writes .workflows/e2e/ — distinct from
    .workflows/testing-pipeline/. This protects e2e-conductor from the
    testing-pipeline schema bump (closes reviewer-pass-2 N4)."""
    conductor_path = AGENTS_DIR / "e2e-conductor-agent.md"
    if not conductor_path.exists():
        pytest.skip("e2e-conductor-agent not in this branch")
    content = conductor_path.read_text(encoding="utf-8")
    # The conductor's state file path should be in its own namespace (NOT testing-pipeline/sub/)
    assert "workflows/testing-pipeline/sub" not in content, (
        "e2e-conductor must not read T2A's sub-state — it has its own namespace"
    )


# ── Spec §3.13 + REQ-M025: schema mismatch abort policy ──────────────────────


def test_test_pipeline_yml_declares_schema_compatibility():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    schema_compat = cfg["state"]["schema_compatibility"]
    assert schema_compat["minimum_required"] == "2.0.0"
    assert schema_compat["on_mismatch"] == "abort_with_STATE_SCHEMA_INCOMPATIBLE"


def test_t2a_documents_state_schema_check():
    """T2A's body must document the schema_version check."""
    t2a_body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "STATE_SCHEMA_INCOMPATIBLE" in t2a_body


# ── Spec §3.3 + REQ-M001: lane orchestration model ───────────────────────────


def test_t2a_documents_7_step_lifecycle():
    """T2A body documents the 7-step lifecycle (INIT → SCOUT → WAVE 1 → WAVE 2 → JOIN → TRIAGE DISPATCH → BUBBLE-UP)."""
    t2a_body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    for step_marker in ["STEP 1 — INIT", "STEP 2 — SCOUT", "STEP 3 — WAVE 1", "STEP 4 — WAVE 2", "STEP 5 — JOIN", "STEP 6 — TRIAGE DISPATCH", "STEP 7 — BUBBLE-UP"]:
        assert step_marker in t2a_body, f"T2A missing {step_marker}"
