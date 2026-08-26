"""T-353 red-then-green: SKILL.md v0.9 fast-lane wording + G16 reconciliation + CI reference.

Reads the files directly (no subprocess) per the contract's DoD item 5. Must FAIL on
origin/main before T-353's edits — see the PR body for the recorded red run.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / ".claude" / "skills" / "get-work-done" / "SKILL.md"
DISPATCHER_PLAN = REPO_ROOT / "plans" / "get-work-done-dispatcher.md"
CI_REFERENCE = (
    REPO_ROOT
    / "core"
    / ".claude"
    / "skills"
    / "ci-cd-setup"
    / "references"
    / "docs-only-short-circuit.md"
)


def test_step3_has_fast_lane_subsection_and_script_names():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "### FAST LANE" in text
    assert "lane: fast" in text
    assert "fast-lane-gate.py" in text
    assert "fast-lane-check.py" in text
    assert "stage-stamp.py" in text
    assert re.search(r"<=\s*5 files|≤\s*5 files", text)
    assert re.search(r"300 changed lines", text)
    assert "code` is NOT eligible in v1" in text or "code` is NOT eligible" in text


def test_critical_rules_never_say_inline_deleted_without_fast_lane():
    text = SKILL_MD.read_text(encoding="utf-8")
    critical_rules = text.split("## CRITICAL RULES", 1)[1]
    for line in critical_rules.splitlines():
        if re.search(r"inline(-execution)? path is DELETED", line):
            assert "FAST LANE" in line, f"bullet says inline path is DELETED with no FAST LANE reconciliation: {line!r}"


def test_dispatcher_plan_g16_names_fast_lane():
    text = DISPATCHER_PLAN.read_text(encoding="utf-8")
    g16_line = next(line for line in text.splitlines() if "(G16)" in line or "G16):" in line)
    assert "FAST LANE" in g16_line


def test_ci_reference_doc_exists_with_required_content():
    assert CI_REFERENCE.exists(), f"missing {CI_REFERENCE}"
    text = CI_REFERENCE.read_text(encoding="utf-8")
    assert "docs_only" in text
    assert "needs: changes" in text
    never_paths_ignore = [
        line
        for line in text.splitlines()
        if "NEVER" in line and "paths-ignore" in line
    ]
    assert never_paths_ignore, "expected a NEVER sentence naming paths-ignore"
