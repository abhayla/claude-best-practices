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
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
CORE = ROOT / "core" / ".claude" / "hooks"
HUB = ROOT / ".claude" / "hooks"
REGISTRY = ROOT / "registry" / "patterns.json"
PLUGIN_GUARD = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "enhance-process-guard.sh"

GUARD = "no-overask-guard.sh"
REMINDER = "prompt-enhance-reminder.sh"


def _guard() -> str:
    return (CORE / GUARD).read_text(encoding="utf-8")


def _reminder() -> str:
    # The reminder hook is hub-only as of 2026-06-22 (the distributable copy graduated to
    # the prompt-auto-enhance plugin; core/ no longer carries it). Read the hub copy.
    return (HUB / REMINDER).read_text(encoding="utf-8")


def test_guard_present_and_hub_matches_core():
    # no-overask-guard.sh stays dual-home synced (hub == core).
    assert (CORE / GUARD).exists() and (HUB / GUARD).exists(), f"missing {GUARD}"
    assert (HUB / GUARD).read_text(encoding="utf-8") == (CORE / GUARD).read_text(encoding="utf-8"), (
        f"hub {GUARD} drifted from core"
    )
    # prompt-enhance-reminder.sh is now hub-only (distributable copy lives in the plugin).
    assert (HUB / REMINDER).exists(), f"missing hub {REMINDER}"
    assert not (CORE / REMINDER).exists(), (
        f"{REMINDER} was retired from core/ (now plugin-distributed) — it must not reappear"
    )


def test_card_block_is_decoupled_from_banner_shape():
    body = _guard()
    # the old block-present gate must be gone...
    assert "enh_block" not in body, "the enh_block gate must be gone (G7)"
    # ...and the card block fires on substantive + not-trivial + (no-card OR no-overall-row),
    # not on banner shape (H2/issue #279 ported the hub's overall-row check).
    assert (
        '[ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] && { [ -z "$card" ] || [ -z "$overall" ]; }'
        in body
    ), (
        "card block must gate on (substantive AND not-trivial AND (no-card OR no-overall)), "
        "banner-independent (G7/H2)"
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


def _scratch_repo(tmp_path_factory) -> Path:
    """A throwaway git repo so the guard's state files (.claude/.reviewcard-count,
    .overask-violations.log, etc.) never touch the real hub checkout, and so the
    test's outcome cannot depend on ambient hub state (e.g. a real .enhance-mode)."""
    scratch = tmp_path_factory.mktemp("guard-scratch")
    subprocess.run(["git", "init", "-q"], cwd=str(scratch), check=True)
    return scratch


def _run_guard(hook_path: Path, transcript_lines: list, cwd: Path) -> str:
    """Invoke a guard hook against a synthetic transcript; return its raw stdout."""
    fd, tp = tempfile.mkstemp(suffix=".jsonl", dir=str(cwd))
    try:
        with open(fd, "w", encoding="utf-8") as f:
            for line in transcript_lines:
                f.write(json.dumps(line) + "\n")
        result = subprocess.run(
            [shutil.which("bash") or "bash", str(hook_path)],
            input=json.dumps({"transcript_path": tp}),
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )
        return result.stdout.strip()
    finally:
        Path(tp).unlink(missing_ok=True)


def _is_block(out: str) -> bool:
    if not out:
        return False
    try:
        return json.loads(out).get("decision") == "block"
    except (json.JSONDecodeError, AttributeError):
        return False


_CARD_TEXT = (
    "*Enhanced: checked stuff*\n\n"
    "Before-after grade card:\n"
    "| Dim | Before | Self-after | Reviewer-after |\n"
    "|---|---|---|---|\n"
    "| Role | 2 | 8 | 8 |\n"
    "Overall: F -> B\n"
    "Independent reviewer (ran this turn): blind re-grade, divergence 0.2\n\n"
    "Diagnosis: MISSING_ROLE\n"
    "Changes Applied: [1] ROLE (high) -> added persona\n"
    "Role: engineer — because X\n"
)

# The final block must, on its own, already clear each guard's ">=300 chars" substantive
# gate and contain NONE of the card tokens. Otherwise a last-block-only implementation
# (the exact bug #253 alleges) would exit on the length gate before ever checking for a
# card, at which point it "passes" the test for the wrong reason (2026-07-03 review
# finding: a short final block does not discriminate a fixed guard from a broken one).
_LONG_CARDLESS_FINAL_BLOCK = "Done, committed the change. " * 15  # 420 chars, no card tokens
assert len(_LONG_CARDLESS_FINAL_BLOCK) >= 300

# Reproduces issue #253: the card renders in an EARLY assistant text block, then the
# turn makes tool calls, then ends with a long final summary block that itself contains
# no card — all within ONE real user turn (no intervening real user message). A
# last-block-only guard would see only the final block: long enough to trigger its
# substantiveness check, and card-less, so it would incorrectly block.
_MID_TURN_CARD_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _CARD_TEXT}]}},
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "echo hi"}}]},
    },
    {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}]},
    },
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]

# Negative control: no card anywhere in the turn — the guard MUST still block a long,
# non-trivial turn with no reviewer card, or the guard is doing nothing at all.
_NO_CARD_ANYWHERE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Some early text with no card. " * 10}]}},
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "echo hi"}}]},
    },
    {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}]},
    },
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]


# Issue #290 (owner-approved ceremony downgrade): a turn whose FIRST line explicitly declares
# Grade-A/no-strengthening is exempt from the full-card enforcement — it only owes the banner +
# a one-line declaration. Deliberately >600 chars (and NOT matching the `trivial` detector's
# "ran as-is"/"no enhancement" first-line phrasing) so this exercises the NEW `gradea` path, not
# the pre-existing `trivial` escape (which is length-capped at <600 and phrased differently).
_GRADE_A_DECLARED_TEXT = (
    "*Enhanced: checked git state and recent commits — Grade A, no strengthening needed*\n\n"
    + ("This turn's prompt was already clear, well-scoped, and needed no rewriting. " * 8)
)
assert len(_GRADE_A_DECLARED_TEXT) >= 600

_GRADE_A_DECLARED_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "what's the current git branch and status"}},
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": _GRADE_A_DECLARED_TEXT}]},
    },
]


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_gradea_declared_turn_is_not_blocked(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _GRADE_A_DECLARED_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} wrongly blocked a turn that explicitly declared Grade-A/no-strengthening "
        f"in its first 3 lines with no full card (issue #290 sampled ceremony): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_gradea_declared_turn_is_not_blocked(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _GRADE_A_DECLARED_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked a turn that explicitly declared "
        f"Grade-A/no-strengthening in its first 3 lines with no full card (issue #290): {out}"
    )


# ── Anchored strong-banner exemption (fix/enhance-gradea-strong-banner) ──
# The UserPromptSubmit reminder tells a STRONG prompt to emit exactly
# "*Enhanced: prompt already strong (grade N) — ran as-is*", but the gradea regex did not
# recognise that wording ("already strong"/"grade 8" are not "grade a"; "ran as-is" != "ran
# input as-is"), so a turn that FOLLOWED the sanctioned strong format was blocked anyway. Fix:
# exempt ONLY the anchored literal `prompt already strong (grade <digit>` — tight enough that
# loose "strong" prose cannot dodge the full-card enforcement (the no-hole control below).
_STRONG_BANNER_TEXT = (
    "*Enhanced: prompt already strong (grade 8) — ran as-is*\n\n"
    + ("The prompt was clear and well scoped, so I proceeded directly with the work. " * 9)
)
assert len(_STRONG_BANNER_TEXT) >= 600  # clears the substantive gate + past the trivial<600 escape

_STRONG_BANNER_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "merge #309 and update the plugin"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _STRONG_BANNER_TEXT}]}},
]

# No-hole control: a turn that only CLAIMS strength in loose prose ("was already strong") but does
# NOT emit the anchored "prompt already strong (grade <digit>" banner — and has no card, no
# grade-a, no "no strengthening needed" — must STILL block. The exemption is the exact banner,
# not any mention of strength.
_LOOSE_STRONG_PROSE_TEXT = (
    "I judged the request and the prompt was already strong enough to run, so I did. "
    + ("Proceeding with the change and reporting the outcome below. " * 9)
)
assert len(_LOOSE_STRONG_PROSE_TEXT) >= 600
assert not re.search(
    r"prompt already strong \(grade [0-9]|grade a[^a-z]|no strengthening needed|ran (your )?input as-is",
    _LOOSE_STRONG_PROSE_TEXT.lower(),
), "the no-hole control must contain NONE of the exemption tokens, or it doesn't test the anchor"

_LOOSE_STRONG_PROSE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LOOSE_STRONG_PROSE_TEXT}]}},
]


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_exempts_sanctioned_strong_banner(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _STRONG_BANNER_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} wrongly blocked a turn opening with the sanctioned strong banner "
        f"'prompt already strong (grade N)' (reminder/guard wording mismatch): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_exempts_sanctioned_strong_banner(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _STRONG_BANNER_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked the sanctioned strong banner: {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_loose_strong_prose(tmp_path_factory):
    """No-hole: mentioning 'strong' in prose must NOT exempt — only the anchored banner does."""
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _LOOSE_STRONG_PROSE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"hub {GUARD} failed to block a turn that only claims strength in loose prose — the "
        f"anchored exemption must not open a hole: {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_still_blocks_loose_strong_prose(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _LOOSE_STRONG_PROSE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} failed to block loose 'strong' prose (no-hole control): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_when_neither_card_nor_gradea_declared(tmp_path_factory):
    """Companion negative for #290: a substantive turn with NEITHER a card NOR a Grade-A
    declaration must stay blocked — the downgrade is an ADDITIVE exemption, not a general
    loosening. Reuses the existing #253/#279 negative-control transcript."""
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"hub {GUARD} failed to block a substantive turn with no card and no Grade-A "
        f"declaration (weak-prompt path must stay enforced, issue #290): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_still_blocks_when_neither_card_nor_gradea_declared(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} failed to block a substantive turn with no card and no "
        f"Grade-A declaration (weak-prompt path must stay enforced, issue #290): {out}"
    )


# Regression lock for issue #279: a fully-rendered card whose reviewer COLUMN is worded
# differently (a markdown table row "| Dim | Before | After | Blind reviewer |") and that
# uses NONE of the fixed prose tokens ("reviewer-after", "independent reviewer", …) — this
# used to false-block because the old regex matched only that fixed prose. Includes an
# Overall row + Diagnosis/Changes-Applied substance so ONLY the card-wording gap is exercised.
_DIFF_WORDED_CARD_TEXT = (
    "*Enhanced: checked stuff*\n\n"
    "Score table:\n"
    "| Dim | Before | After | Blind reviewer |\n"
    "|---|---|---|---|\n"
    "| Role | 2 | 8 | 8 |\n"
    "Overall: F -> B\n\n"
    "Diagnosis: MISSING_ROLE\n"
    "Changes Applied: [1] ROLE (high) -> added persona\n"
    "Role: engineer — because X\n"
)

_DIFF_WORDED_CARD_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": _DIFF_WORDED_CARD_TEXT}]},
    },
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "echo hi"}}]},
    },
    {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}]},
    },
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]


# Negative control for the H1 tightening (issue #279 review): an UNRELATED markdown table
# that merely contains the word "reviewer" (e.g. "| File | Reviewer |") plus the common word
# "overall" somewhere — but NO before/after/self card header row and NONE of the enhance
# prose tokens — must NOT be credited as a card. The guard MUST still block, or the widened
# regex would have opened a genuine-miss escape hatch.
_REVIEWER_TABLE_NO_CARD_TEXT = (
    "Here is the assignment table for the sprint:\n"
    "| File | Reviewer |\n"
    "|---|---|\n"
    "| a.py | bob |\n"
    "| b.py | carol |\n"
    "Overall this covers the backlog. " * 8
)
assert len(_REVIEWER_TABLE_NO_CARD_TEXT) >= 300

_REVIEWER_TABLE_NO_CARD_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": _REVIEWER_TABLE_NO_CARD_TEXT}]},
    },
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "echo hi"}}]},
    },
    {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}]},
    },
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]


def test_discriminating_transcript_would_trip_a_last_block_only_bug():
    """Meta-check: prove the transcript above actually discriminates. If a guard only
    looked at the LAST assistant text block (the literal bug #253 describes), that
    block alone already clears the length gate and contains no card token — so a
    last-block-only implementation would find "substantive, no card" and block. This
    is what makes test_*_credits_a_card_rendered_before_tool_calls below meaningful:
    the real hooks passing it proves they look past the last block, not that the
    scenario was too small to trigger the guard at all (2026-07-03 review finding)."""
    assert len(_LONG_CARDLESS_FINAL_BLOCK) >= 300
    lowered = _LONG_CARDLESS_FINAL_BLOCK.lower()
    assert not re.search(r"reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer", lowered)


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_credits_a_card_rendered_before_tool_calls(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _MID_TURN_CARD_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} wrongly blocked a turn whose card rendered before tool calls (issue #253): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_credits_a_card_rendered_before_tool_calls(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _MID_TURN_CARD_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked a turn whose card rendered before tool calls (issue #253): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_when_no_card_anywhere(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"hub {GUARD} failed to block a substantive turn with no reviewer card anywhere: {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_still_blocks_when_no_card_anywhere(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} failed to block a substantive turn with no reviewer card anywhere: {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_credits_differently_worded_reviewer_column(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _DIFF_WORDED_CARD_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} wrongly blocked a card whose reviewer column is worded differently "
        f"(issue #279): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_credits_differently_worded_reviewer_column(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _DIFF_WORDED_CARD_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked a card whose reviewer column is worded "
        f"differently (issue #279): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_reviewer_table_without_a_real_card(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _REVIEWER_TABLE_NO_CARD_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"hub {GUARD} failed to block a turn whose only 'reviewer' content is an unrelated "
        f"table (no before/after/self card header) (issue #279 review): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_still_blocks_reviewer_table_without_a_real_card(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _REVIEWER_TABLE_NO_CARD_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} failed to block a turn whose only 'reviewer' content is an "
        f"unrelated table (no before/after/self card header) (issue #279 review): {out}"
    )


def test_card_regex_consistent_across_guards():
    """H6: the card-detection regex AND the overall-row regex must be byte-identical across
    the hub, core, and plugin guards so they cannot drift out of sync again (issue #279)."""
    hub_body = (HUB / GUARD).read_text(encoding="utf-8")
    core_body = (CORE / GUARD).read_text(encoding="utf-8")
    plugin_body = PLUGIN_GUARD.read_text(encoding="utf-8")
    card_snippet = r"^[[:space:]]*\|.*(before|after|self).*reviewer.*\|"
    overall_snippet = r"overall|[a-f] *(→|->) *[a-f]|weighted total"
    for name, body in [("hub", hub_body), ("core", core_body), ("plugin", plugin_body)]:
        assert card_snippet in body, f"{name} guard's card-detection regex drifted (H6)"
        assert overall_snippet in body, f"{name} guard's overall-row regex drifted (H6)"


# ── Skill-execution turn exemption (fix/enhance-guard-skill-turn-exempt) ──
# When a skill runs (reached via /command OR natural language), the harness injects the skill BODY
# as a plain (non-tool_result) user message that SPLITS the turn — it becomes the guard's
# $last_user and carries the stable marker "Base directory for this skill:". The enhance banner
# lands in the pre-split segment, so the post-split final text ($last_text) has no card → the guard
# would false-block. Skills are enhance-exempt, so a $last_user carrying that marker exempts the turn.
_SKILL_BODY = (
    "Base directory for this skill: /repo/.claude/skills/end-session\n\n"
    "# End Session — Round Up & Close\n\nClose out a work session cleanly..."
)

_SKILL_TURN_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "can we end this session?"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "*Enhanced: mapping to /end-session — Grade A, no strengthening needed*"},
        {"type": "tool_use", "id": "s1", "name": "Skill", "input": {"skill": "end-session"}},
    ]}},
    # the harness-injected skill body (splits the turn; becomes $last_user)
    {"type": "user", "message": {"role": "user", "content": _SKILL_BODY}},
    # the card-less final segment the guard actually evaluates
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_exempts_skill_execution_turn(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _SKILL_TURN_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} wrongly blocked a skill-execution turn whose card-less final segment follows "
        f"a harness-injected skill body — skills are enhance-exempt (turn-split false-block): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_exempts_skill_execution_turn(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _SKILL_TURN_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked a skill-execution turn (turn-split false-block): {out}"
    )


def test_guards_carry_skill_body_marker_exemption():
    """Static lock: all three guards exempt a turn whose $last_user carries the skill-body marker."""
    for name, fp in [("hub", HUB / GUARD), ("core", CORE / GUARD), ("plugin", PLUGIN_GUARD)]:
        assert "Base directory for this skill:" in fp.read_text(encoding="utf-8"), (
            f"{name} guard must exempt skill-execution turns via the skill-body marker"
        )


# ── Coexistence dedup (fix/dedup-enhance-stop-hooks): the plugin guard must STAND DOWN where
# the hub-operational superset Stop hook (no-overask-guard.sh) is present AND wired, so a single
# card-miss cannot double-fire (two blocks + two log lines — the enhance-block-miss double-count).
# Downstream projects without that hook keep full plugin enforcement (no regression — already
# pinned by test_plugin_guard_still_blocks_when_no_card_anywhere, which uses a bare scratch repo).


def _scratch_repo_with_superset(tmp_path_factory) -> Path:
    """A throwaway git repo that ALSO carries a wired no-overask-guard.sh — i.e. it looks like
    the hub (or any host running the superset enforcer). The plugin card-guard must recognise
    this and stand down."""
    scratch = tmp_path_factory.mktemp("guard-superset")
    subprocess.run(["git", "init", "-q"], cwd=str(scratch), check=True)
    hooks_dir = scratch / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / GUARD).write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (scratch / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"Stop": [{"matcher": "", "hooks": [
            {"type": "command", "command": 'bash "$(git rev-parse --show-toplevel)/.claude/hooks/no-overask-guard.sh"'}
        ]}]}}),
        encoding="utf-8",
    )
    return scratch


def test_plugin_guard_source_has_coexistence_standdown():
    body = PLUGIN_GUARD.read_text(encoding="utf-8")
    assert 'no-overask-guard.sh"' in body and "$root/.claude/settings.json" in body, (
        "plugin guard must stand down when the hub superset hook is present AND wired"
    )
    # the hub guard is the superset ENFORCER — it must NOT carry a stand-down (it can't defer to
    # itself), or the hub would lose all card enforcement.
    hub_body = (HUB / GUARD).read_text(encoding="utf-8")
    assert "Coexistence guard" not in hub_body, "the hub superset guard must NOT stand itself down"


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_stands_down_when_superset_hook_present(tmp_path_factory):
    """The dedup: a substantive card-less turn that the plugin guard WOULD block is left alone
    once the hub-operational no-overask-guard.sh is present + wired (it enforces the same card)."""
    scratch = _scratch_repo_with_superset(tmp_path_factory)
    out = _run_guard(PLUGIN_GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert not _is_block(out), (
        f"plugin {PLUGIN_GUARD.name} double-fired: it must stand down where the superset "
        f"no-overask-guard.sh is present + wired (dedup), leaving one enforcer, not two: {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_even_with_its_own_hook_present(tmp_path_factory):
    """No-regression companion: the SUPERSET (hub) guard is the sole remaining enforcer where it
    is wired, so it must still block the same card-less turn — the dedup removes the DUPLICATE,
    never the enforcement."""
    scratch = _scratch_repo_with_superset(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _NO_CARD_ANYWHERE_TRANSCRIPT, scratch)
    assert _is_block(out), (
        f"hub {GUARD} must remain the active enforcer where it is wired (dedup keeps exactly "
        f"one enforcer, not zero): {out}"
    )


def test_registry_hashes_in_sync():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def h(fp: Path) -> str:
        c = fp.read_text(encoding="utf-8")
        return hashlib.sha256(re.sub(r"  +", " ", "\n".join(l.strip() for l in c.splitlines())).encode()).hexdigest()

    # prompt-enhance-reminder is no longer a core/registry hook (graduated to the plugin);
    # only no-overask-guard remains dual-home with a registry hash to keep in sync.
    for name, fp in [("no-overask-guard", CORE / GUARD)]:
        assert reg[name]["type"] == "hook"
        assert reg[name]["hash"] == h(fp), f"{name} registry hash drifted — resync it"


# ── Marker attestation (2026-07-15 root-cause fix, session fedaf490) ──
# The harness DROPS assistant text blocks that share one API response with tool_use blocks
# (live repro: a correctly-rendered pre-execution enhance card never persisted to the
# transcript — only thinking/tool_use entries and the final text did). The ordering rule
# (prompt-auto-enhance.md) requires the card BEFORE execution tool calls, so on tool-using
# turns the transcript is NOT evidence of card absence, and the guard false-blocked 5x in one
# session. Fix: the model touches .claude/.enhance-card-rendered in the same turn as the
# render; the guard credits marker OR persisted card text; prompt-enhance-reminder.sh resets
# the marker on every real user prompt so it cannot carry over.
_DROPPED_CARD_TOOL_TURN = [
    {"type": "user", "message": {"role": "user", "content": "do the thing"}},
    # No early text entry AT ALL — the harness dropped it (text + tool_use in one response).
    {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "echo hi"}}]},
    },
    {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}]},
    },
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _LONG_CARDLESS_FINAL_BLOCK}]}},
]


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_credits_marker_when_card_text_was_dropped(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    (scratch / ".claude").mkdir(exist_ok=True)
    (scratch / ".claude" / ".enhance-card-rendered").write_text("attested", encoding="utf-8")
    out = _run_guard(HUB / GUARD, _DROPPED_CARD_TOOL_TURN, scratch)
    assert not _is_block(out), (
        f"hub {GUARD} must credit the .enhance-card-rendered marker on a tool-using turn whose "
        f"card text the harness dropped (mid-turn text does not persist beside tool_use): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_still_blocks_dropped_card_shape_without_marker(tmp_path_factory):
    # No-hole control: same tool-using cardless shape, NO marker → the block must stand,
    # or the marker fix would have silently disabled enforcement on all tool-using turns.
    scratch = _scratch_repo(tmp_path_factory)
    out = _run_guard(HUB / GUARD, _DROPPED_CARD_TOOL_TURN, scratch)
    assert _is_block(out), (
        f"hub {GUARD} must STILL block a cardless tool-using turn when no marker exists: {out}"
    )


def test_reminder_resets_card_marker():
    rem = _reminder()
    assert ".enhance-card-rendered" in rem, (
        "prompt-enhance-reminder.sh must reset the .enhance-card-rendered marker each real "
        "user prompt, or a single render would attest every later turn"
    )
