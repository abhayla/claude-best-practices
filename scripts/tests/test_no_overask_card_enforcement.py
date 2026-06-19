"""Regression guard for the prompt-auto-enhance ENFORCEMENT system (2026-06-18 audit).

Pins the fixes for the loopholes that let the full enhance process silently not render:
- G6: the UserPromptSubmit reminder demands the FULL process UP FRONT (not the weaker
  "format A — MANDATORY" compact block that contradicted the rule).
- G7/G3: the Stop-hook card block fires INDEPENDENT of banner shape (a disguised/missing
  banner can't let the strongest omission escape).
- G4: the trivial "ran as-is" escape is verifiable (first line + short turn), so a long
  working turn can't exempt itself by mentioning the phrase in prose.
- G11: the card is detected by a token SET, not one literal.
- G9: cap-exhaustion logs a distinct escalation line.
Hub and core copies stay byte-identical; registry hashes stay in sync.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CORE = ROOT / "core" / ".claude" / "hooks"
HUB = ROOT / ".claude" / "hooks"
REGISTRY = ROOT / "registry" / "patterns.json"

GUARD = "no-overask-guard.sh"
REMINDER = "prompt-enhance-reminder.sh"


def _guard() -> str:
    return (CORE / GUARD).read_text(encoding="utf-8")


def _reminder() -> str:
    return (CORE / REMINDER).read_text(encoding="utf-8")


def test_both_hooks_present_and_hub_matches_core():
    for h in (GUARD, REMINDER):
        assert (CORE / h).exists() and (HUB / h).exists(), f"missing {h}"
        assert (HUB / h).read_text(encoding="utf-8") == (CORE / h).read_text(encoding="utf-8"), (
            f"hub {h} drifted from core"
        )


def test_card_block_is_decoupled_from_banner_shape():
    body = _guard()
    # the old block-present gate must be gone...
    assert "enh_block" not in body, "the enh_block gate must be gone (G7)"
    # ...and the card block fires on substantive + not-trivial + NO card, not on banner shape.
    assert '[ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] && [ -z "$card" ]' in body, (
        "card block must gate on (substantive AND not-trivial AND no-card), banner-independent (G7)"
    )


def test_card_detection_uses_a_token_set():
    body = _guard()
    assert "reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer" in body, (
        "the card must be detected by a token set, not one literal (G11)"
    )


def test_trivial_escape_is_verifiable():
    body = _guard()
    # trivial only when declared on the FIRST line AND the turn is short (<600).
    assert 'head -1 | grep -qE "ran (your )?input as-is' in body, "trivial must be first-line only (G4)"
    assert '[ "${#last_text}" -lt 600 ]' in body, "trivial must require a short turn (G4)"


def test_cap_exhaustion_is_logged():
    body = _guard()
    assert "card-block-EXHAUSTED" in body, "cap exhaustion must log a distinct escalation (G9)"


def test_substance_block_enforces_diagnose_to_fix_linkage():
    body = _guard()
    # the substance guard must detect the diagnose→fix tokens by a SET (not one literal)...
    assert (
        "diagnosis:|changes applied|missing_role" in body
    ), "substance must be detected by the diagnosis/fix token set"
    # ...and block on substantive + not-trivial + card-present + NO substance.
    assert (
        '[ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] && [ -n "$card" ] && [ -z "$substance" ]'
        in body
    ), "substance block must gate on (substantive AND not-trivial AND card-present AND no-substance)"
    assert "diagnosis-block-EXHAUSTED" in body, (
        "substance cap exhaustion must log a distinct escalation line"
    )


def test_substance_block_exempts_grade_a_zero_fix_turns():
    body = _guard()
    # a legitimate Grade-A / zero-fix turn has no diagnosis — it must be substance-accounted.
    assert "grade: a|grade a[^a-z]|0 fix|no fix|zero fix" in body, (
        "Grade-A / zero-fix turns must be exempt (tightened so 'grade and' can't false-match)"
    )


def test_reminder_resets_the_diagnosis_loop_guard():
    rem = _reminder()
    assert ".diagnosis-count" in rem, (
        "reminder must reset the .diagnosis-count loop-guard per user turn"
    )


def test_reminder_demands_full_process_up_front_not_format_A():
    rem = _reminder()
    assert "format A" not in rem, "reminder must NOT demand the weaker compact 'format A' (G6)"
    assert "FULL ENHANCE PROCESS UP FRONT" in rem, "reminder must demand the full process up front (G6)"
    assert "Reviewer-after" in rem, "reminder must name the reviewer card column (G6)"


def test_registry_hashes_in_sync():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def h(fp: Path) -> str:
        c = fp.read_text(encoding="utf-8")
        return hashlib.sha256(re.sub(r"  +", " ", "\n".join(l.strip() for l in c.splitlines())).encode()).hexdigest()

    for name, fp in [("no-overask-guard", CORE / GUARD), ("prompt-enhance-reminder", CORE / REMINDER)]:
        assert reg[name]["type"] == "hook"
        assert reg[name]["hash"] == h(fp), f"{name} registry hash drifted — resync it"
