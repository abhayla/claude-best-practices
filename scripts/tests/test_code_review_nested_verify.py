"""Structural guards for the code-review-workflow --nested-verify pilot.

The pilot (2026-06-20) adopts GA recursive subagents as an OPT-IN per-finding
adversarial verification stage. These tests pin the contract that protects the
default path and the dual-mode agent wiring — NOT the empirical review quality,
which needs a live run.
"""
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "core/.claude/skills/code-review-workflow/SKILL.md"
CODE_REVIEWER = REPO / "core/.claude/agents/code-reviewer-agent.md"
SECURITY_AUDITOR = REPO / "core/.claude/agents/security-auditor-agent.md"
ORCHESTRATION = REPO / "core/.claude/rules/agent-orchestration.md"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path.name} missing frontmatter"
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm)


def test_skill_documents_nested_verify_flag():
    body = SKILL.read_text(encoding="utf-8")
    assert "--nested-verify" in body, "nested-verify flag not documented"
    assert "Nested-verify mode" in body, "nested-verify STEP 2b section missing"


def test_skill_keeps_default_path_flat():
    """The opt-in MUST NOT change behavior when the flag is absent."""
    body = SKILL.read_text(encoding="utf-8")
    assert "DEFAULT (no `--nested-verify`) STEP 2b path flat" in body, (
        "missing the critical rule that the default path stays flat/single-level"
    )
    assert "degrade to the flat path" in body or "degrade to flat" in body, (
        "missing the depth-5-cap degrade-to-flat guard rail"
    )


@pytest.mark.parametrize("agent_file", [CODE_REVIEWER, SECURITY_AUDITOR])
def test_dimension_agents_are_dual_mode(agent_file):
    fm = _frontmatter(agent_file)
    assert fm.get("dispatched_from") == "dual-mode", (
        f"{agent_file.name} must be dispatched_from: dual-mode to spawn depth-2 verifiers"
    )
    assert "Agent" in fm.get("tools", []), (
        f"{agent_file.name} must declare Agent in tools for the nested-verify path"
    )


@pytest.mark.parametrize("agent_file", [CODE_REVIEWER, SECURITY_AUDITOR])
def test_dimension_agents_document_flat_default(agent_file):
    """Dual-mode body MUST state the default stays flat (no silent nesting)."""
    body = agent_file.read_text(encoding="utf-8")
    assert "nested-verify" in body, f"{agent_file.name} missing nested-verify mode doc"
    assert "Flat worker (DEFAULT)" in body, (
        f"{agent_file.name} must document the flat default dispatch path"
    )


def test_default_step2b_block_has_no_nesting():
    """Substance lock: the DEFAULT STEP 2b dispatch (everything before the
    opt-in 'Nested-verify mode' section) MUST NOT carry the nesting token, so a
    future edit that leaks nesting into the default path fails CI."""
    body = SKILL.read_text(encoding="utf-8")
    assert "### Nested-verify mode" in body, "nested-verify section anchor missing"
    default_part, _, _ = body.partition("### Nested-verify mode")
    # The default deep-audit dispatch lives in this region...
    assert 'subagent_type="code-reviewer-agent"' in default_part, (
        "default STEP 2b dispatch block not found before the nested-verify section"
    )
    # ...and it MUST be flat — no nesting token, no per-finding verifier spawn.
    assert "mode: nested-verify" not in default_part, (
        "the nesting token leaked into the DEFAULT STEP 2b dispatch — default path "
        "must stay flat/single-level"
    )


def test_orchestration_records_first_nested_consumer():
    body = ORCHESTRATION.read_text(encoding="utf-8")
    assert "First concrete nested consumer" in body, (
        "agent-orchestration.md must record the first nested-dispatch consumer"
    )
    assert "code-review-workflow --nested-verify" in body
