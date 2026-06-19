"""Guards for the project-manager-agent nesting-doctrine correction (S1, 2026-06-20).

Pins two things: (1) the factually-stale pre-GA "Agent is stripped" claim is gone
and replaced with the corrected GA framing; (2) the opt-in stage-level depth-2
nesting mode is documented WITHOUT changing the inline-Skill() default.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PM = REPO / "core/.claude/agents/project-manager-agent.md"


def test_stale_agent_stripped_claim_is_corrected():
    body = PM.read_text(encoding="utf-8")
    # The corrected note must explicitly flag the old justification as stale...
    assert "factually stale" in body, "the stale pre-GA claim must be marked corrected"
    assert "v2.1.172" in body, "must cite the GA version that superseded the claim"
    # ...and must NOT assert the old falsehood as current fact (only inside the
    # quoted correction, never as a live constraint).
    assert "platform constraint" not in body, (
        "the stale 'Anthropic platform constraint' justification must be removed"
    )


def test_opt_in_stage_nesting_documented():
    body = PM.read_text(encoding="utf-8")
    assert "--isolate-stage-workers" in body, "opt-in stage-nesting flag missing"
    assert "depth-2" in body, "depth-2 nesting not described"
    assert "5-level cap" in body, "must design for the 5-level cap"


def test_default_stays_inline_skill():
    # Normalize whitespace so the contract phrase matches even when line-wrapped.
    body = " ".join(PM.read_text(encoding="utf-8").split())
    assert "the DEFAULT stays inline-`Skill()` (byte-for-byte unchanged)" in body, (
        "the inline-Skill() default must be stated as unchanged"
    )
    assert "opt-in" in body.lower(), "stage nesting must be opt-in, not default"


def test_no_retired_master_agent_dispatch_instruction():
    """Consistency guard: the body MUST NOT instruct dispatching the retired
    <workflow>-master-agents — they are deprecated and the agent now uses Skill()."""
    body = PM.read_text(encoding="utf-8")
    assert 'subagent_type="{workflow-id}-master-agent"' not in body, (
        "body still instructs dispatching a retired workflow-master-agent — "
        "workflow-mapped stages must invoke Skill('/<workflow>') instead"
    )
    assert "RETIRED" in body and "deprecated: true" in body, (
        "the workflow-mapped section must state the master-agents are retired"
    )


def test_t0_lifecycle_convention_preserved():
    """The T0 convention itself stays — only its justification was corrected."""
    body = PM.read_text(encoding="utf-8")
    assert "dispatched_from: T0" in body
    assert "lifecycle-ownership" in body, (
        "T0 convention must now rest on lifecycle ownership, not the stale platform claim"
    )
