"""Guard for T-238: the OWNER STATUS CADENCE rule must stay a rule, not decay back into
the bare scoreboard-cadence prose that shipped before it.

Why this test exists: the owner had to ask twice in one evening why updates stopped
(2026-08-20), and the ticker built in response silently EXPIRED after an hour because it
was armed as a timeout instead of persistent - inside the same session that spent two days
fixing exactly that failure shape elsewhere. The 2026-08-16 scoreboard-cadence rule already
existed and was not enough: it named a 15-minute cadence but never required a timestamp, a
content floor, or a persistent (non-timeout) mechanism. This test fails on that older text
and only passes once all three additions are present.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_MD = REPO / ".claude/skills/get-work-done/SKILL.md"


def _skill() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_cadence_rule_lives_on_the_dispatch_monitor_path():
    body = _skill()
    assert "OWNER STATUS CADENCE" in body, (
        "SKILL.md must state the owner status cadence as a named rule"
    )
    assert "## STEP 6" in body and "## STEP 7 —" in body
    cadence = body.index("OWNER STATUS CADENCE")
    assert body.index("## STEP 6") < cadence < body.index("## STEP 7 —"), (
        "the cadence rule must sit on the dispatch/monitor path (STEP 6), not an appendix"
    )


def test_every_tick_opens_with_ist_timestamp():
    body = _skill()
    section = body[body.index("OWNER STATUS CADENCE"):][:1200]
    assert re.search(r"CURRENT TIME IN IST", section), (
        "the rule must require every tick to open with the current time in IST"
    )
    assert re.search(r"\[\d{1,2}:\d{2} IST\]", section), (
        "the rule must give a concrete IST-timestamp example, e.g. [21:46 IST]"
    )
    assert "does not satisfy the cadence" in section, (
        "a tick missing its timestamp must not count as satisfying the cadence"
    )


def test_content_floor_is_specified():
    body = _skill()
    section = body[body.index("OWNER STATUS CADENCE"):][:1200]
    assert "CONTENT FLOOR" in section, "a per-tick content floor must be named"
    assert re.search(r"what changed since the last\s+tick", section), (
        "the content floor must cover what changed since the last tick"
    )
    assert re.search(r"NOTHING changed", section), (
        "a no-change tick must be an explicit statement, not a skipped tick"
    )


def test_ticker_must_be_persistent_not_a_timeout():
    body = _skill()
    section = body[body.index("OWNER STATUS CADENCE"):][:1200]
    assert "PERSISTENT" in section, "the ticker must be required to be persistent"
    assert re.search(r"never a fixed timeout", section), (
        "the rule must forbid a fixed-timeout ticker - the exact mechanism that failed"
    )
    assert "20:30" in section, (
        "cite the 2026-08-20 20:30 lapse as the evidence the rule exists to prevent"
    )
    assert "fabricated" in section, (
        "the ticker must report real state, never fabricated progress"
    )


def test_critical_rules_carry_the_cadence():
    body = _skill()
    rules = body[body.index("## CRITICAL RULES"):]
    assert "MUST apply the OWNER STATUS CADENCE" in rules, (
        "the cadence must appear as a MUST in CRITICAL RULES so an audit can check it"
    )
