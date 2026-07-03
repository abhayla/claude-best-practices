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


def _run_guard(hook_path: Path, transcript_lines: list) -> str:
    """Invoke a guard hook against a synthetic transcript; return its raw stdout."""
    fd, tp = tempfile.mkstemp(suffix=".jsonl")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            for line in transcript_lines:
                f.write(json.dumps(line) + "\n")
        result = subprocess.run(
            [shutil.which("bash") or "bash", str(hook_path)],
            input=json.dumps({"transcript_path": tp}),
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        return result.stdout.strip()
    finally:
        Path(tp).unlink(missing_ok=True)


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

# Reproduces issue #253: the card renders in an EARLY assistant text block, then the
# turn makes tool calls, then ends with a short final summary block — all within ONE
# real user turn (no intervening real user message).
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
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Done, committed the change."}]}},
]


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_hub_guard_credits_a_card_rendered_before_tool_calls():
    out = _run_guard(HUB / GUARD, _MID_TURN_CARD_TRANSCRIPT)
    assert '"decision":"block"' not in out, (
        f"hub {GUARD} wrongly blocked a turn whose card rendered before tool calls (issue #253): {out}"
    )


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("jq") is None, reason="requires bash+jq")
def test_plugin_guard_credits_a_card_rendered_before_tool_calls():
    out = _run_guard(PLUGIN_GUARD, _MID_TURN_CARD_TRANSCRIPT)
    assert '"decision":"block"' not in out, (
        f"plugin {PLUGIN_GUARD.name} wrongly blocked a turn whose card rendered before tool calls (issue #253): {out}"
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
