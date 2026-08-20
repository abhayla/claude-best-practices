"""Guard for T-232: the fleet dispatcher's ROOT-CAUSE GATE must stay a rule, not decay
back into prose.

Why this test exists: on 2026-08-20 eight workers in a row (T-204 ... T-228) died at
their turn cap with correct work uncommitted, and each time the "fix" was a firmer
instruction in the worker mandate. Eight identical failures of one prose line is the
evidence that prose is not a mechanism. This test IS the mechanism for the rule that
says so: it fails if the recurrence rule, the prose-is-not-a-mechanism statement, the
sweep obligation or the self-improvement loop is removed or watered down.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_MD = REPO / ".claude/skills/get-work-done/SKILL.md"


def _skill() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_recurrence_rule_is_a_step_not_an_appendix():
    body = _skill()
    assert "## STEP 3.5" in body, (
        "the root-cause gate must be a numbered STEP on the dispatcher's own path, "
        "not an appendix a dispatcher never reaches"
    )
    gate = body.index("## STEP 3.5")
    assert gate < body.index("## STEP 4 —"), "STEP 3.5 must sit before STEP 4 in the flow"


def test_second_occurrence_demands_a_mechanism_fix():
    body = _skill()
    assert re.search(r"SECOND occurrence of the same failure SHAPE", body), (
        "SKILL.md must state the rule in terms of the SECOND occurrence of a failure SHAPE"
    )
    rule = body[body.index("SECOND occurrence of the same failure SHAPE"):][:700]
    assert "MECHANISM" in rule, "the second-occurrence rule must demand a MECHANISM fix"
    assert re.search(r"NOT acceptable on its own", rule), (
        "the second-occurrence rule must say an instance fix alone is NOT acceptable"
    )
    assert "status_log" in rule, (
        "the rule must require recording WHY a mechanism fix is impossible when it is"
    )
    assert "will take a lot of time" in body, (
        "keep the owner's own framing - re-fixing instances 'will take a lot of time'"
    )


def test_prose_is_not_a_mechanism_is_stated_with_its_definition():
    body = _skill()
    assert "PROSE IS NOT A MECHANISM" in body, (
        "SKILL.md must state plainly that prose is not a mechanism"
    )
    section = body[body.index("PROSE IS NOT A MECHANISM"):][:800]
    for kind in ("CODE", "GUARD", "HOOK", "SCHEMA", "TEST"):
        assert kind in section, (
            f"the definition of a mechanism must name {kind} - otherwise 'mechanism' "
            "is itself just a word"
        )
    assert "eight" in section.lower(), (
        "cite the eight consecutive failures of the COMMIT EARLY AND OFTEN mandate - "
        "the evidence is what makes the rule stick"
    )


def test_sweep_obligation_is_on_the_completion_path():
    body = _skill()
    assert "fixed 1 of N found" in body and "swept, no other instances" in body, (
        "SKILL.md must require the sweep RESULT be reported in one of the two "
        "explicit forms, so 'I looked' cannot pass as a sweep"
    )
    assert "ROOT-CAUSE CLOSE-OUT" in body, (
        "the sweep obligation must also bind the task-completion path (STEP 7), "
        "not only intake"
    )
    close_out = body[body.index("ROOT-CAUSE CLOSE-OUT"):][:600]
    assert "SWEEP" in close_out and "INCOMPLETE" in close_out, (
        "close-out must make a missing sweep result an INCOMPLETE task, not a nit"
    )


def test_self_improvement_loop_points_at_patterns_seen():
    body = _skill()
    assert "LESSON(CODIFIED" in body, (
        "class fixes must be recorded in the existing LESSON(CODIFIED -> where) form"
    )
    lesson = body[body.index("SELF-IMPROVEMENT."):][:600]
    assert "PATTERNS-SEEN.md" in lesson, (
        "point at the fleet's existing PATTERNS-SEEN.md store, never a new one"
    )
    assert "mechanism installed" in lesson, (
        "the lesson form must record the MECHANISM installed, not just the story"
    )


def test_critical_rules_carry_the_gate():
    body = _skill()
    rules = body[body.index("## CRITICAL RULES"):]
    assert "MUST apply the ROOT-CAUSE GATE" in rules, (
        "the gate must appear as a MUST in CRITICAL RULES so an audit can check it"
    )


def test_skill_stays_lean():
    lines = _skill().splitlines()
    assert len(lines) <= 780, (
        f"SKILL.md is auto-loaded every session; it grew to {len(lines)} lines. "
        "Tighten before adding more."
    )
