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

# T-371 (SKILL.md v0.10, 2026-08-27): the skill was split into PROCEDURE (SKILL.md, <= 30 KB)
# and its dated INCIDENT NARRATIVES (references/incident-log.md, verbatim). The guard below
# keeps its full force but now reads the whole skill PACKAGE for the EVIDENCE tokens (the
# stories moved, they were not dropped), while placement and CRITICAL-RULES assertions stay
# pinned to SKILL.md itself - which is where a rule decaying would actually show up.
def _skill_package() -> str:
    refs = sorted((SKILL_MD.parent / "references").glob("*.md"))
    parts = [SKILL_MD.read_text(encoding="utf-8")]
    parts += [r.read_text(encoding="utf-8") for r in refs]
    return (chr(10)).join(parts)


def _cadence_windows():
    """Every 1200-char window that opens at an OWNER STATUS CADENCE heading anywhere in the
    skill package. After the T-371 split the RULE sits in SKILL.md STEP 6 and its full
    2026-08-20 evidence sits verbatim in references/incident-log.md (I-22); the guard is that
    ONE window still carries the complete rule - not that both copies do."""
    body = _skill_package()
    return [body[m.start():][:1200] for m in re.finditer("OWNER STATUS CADENCE", body)]


def test_cadence_rule_lives_on_the_dispatch_monitor_path():
    body = _skill()
    assert "OWNER STATUS CADENCE" in body, (
        "SKILL.md must state the owner status cadence as a named rule"
    )
    assert "## STEP 6" in body and re.search(r"## STEP 7 [-—]", body)
    cadence = body.index("OWNER STATUS CADENCE")
    assert body.index("## STEP 6") < cadence < re.search(r"## STEP 7 [-—]", body).start(), (
        "the cadence rule must sit on the dispatch/monitor path (STEP 6), not an appendix"
    )


def test_every_tick_opens_with_ist_timestamp():
    windows = _cadence_windows()
    assert any(
        re.search(r"CURRENT TIME IN IST", w)
        and re.search(r"\[\d{1,2}:\d{2} IST\]", w)
        and "does not satisfy the cadence" in w
        for w in windows
    ), (
        "one OWNER STATUS CADENCE block must require every tick to open with the current IST "
        "time, give a concrete [HH:MM IST] example, and say a tick missing it does not satisfy "
        "the cadence"
    )

def test_content_floor_is_specified():
    windows = _cadence_windows()
    assert any(
        "CONTENT FLOOR" in w
        and re.search(r"what changed since the last\s+tick", w)
        and re.search(r"NOTHING changed", w)
        for w in windows
    ), (
        "one OWNER STATUS CADENCE block must name a per-tick CONTENT FLOOR covering what changed "
        "since the last tick, and require an explicit no-change tick rather than a skipped one"
    )

def test_ticker_must_be_persistent_not_a_timeout():
    windows = _cadence_windows()
    assert any(
        "PERSISTENT" in w
        and re.search(r"never a fixed timeout", w)
        and "20:30" in w
        and "fabricated" in w
        for w in windows
    ), (
        "one OWNER STATUS CADENCE block must require a PERSISTENT ticker, forbid a fixed timeout, "
        "cite the 2026-08-20 20:30 lapse, and forbid fabricated progress"
    )

def test_critical_rules_carry_the_cadence():
    body = _skill()
    rules = body[body.index("## CRITICAL RULES"):]
    assert "MUST apply the OWNER STATUS CADENCE" in rules, (
        "the cadence must appear as a MUST in CRITICAL RULES so an audit can check it"
    )
