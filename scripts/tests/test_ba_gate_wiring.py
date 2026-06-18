"""Regression guard for the BA-gate (use-case-discovery) trigger.

Root cause this pins (investigated 2026-06-18): the BA discovery process was
silently skipped because the `ba-usecase-discovery-reminder.sh` hook lived only
in `core/.claude/` (the downstream template) and was NEVER wired into the hub's
own `.claude/settings.json` — so hub sessions got zero BA salience — AND its
keyword gate missed common build phrasings ("work on", "add", "I need").

These tests fail if either regression returns:
- the hook is not present/identical in BOTH core and hub
- either settings.json stops wiring it into UserPromptSubmit
- the hook reverts from an OFFER (*Sync-check:*) back to a silent mandate
- the broadened keyword gate loses the phrasings that caused the original miss
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
HUB_CLAUDE = ROOT / ".claude"

CORE_HOOK = CORE_CLAUDE / "hooks" / "ba-usecase-discovery-reminder.sh"
HUB_HOOK = HUB_CLAUDE / "hooks" / "ba-usecase-discovery-reminder.sh"
CORE_SETTINGS = CORE_CLAUDE / "settings.json"
HUB_SETTINGS = HUB_CLAUDE / "settings.json"

HOOK_BASENAME = "ba-usecase-discovery-reminder.sh"


def _user_prompt_submit_commands(settings_path: Path) -> str:
    """All UserPromptSubmit hook command strings joined, for substring checks."""
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    blocks = data.get("hooks", {}).get("UserPromptSubmit", [])
    cmds = []
    for block in blocks:
        for hook in block.get("hooks", []):
            cmds.append(hook.get("command", ""))
    return "\n".join(cmds)


def test_ba_hook_present_in_core_and_hub():
    assert CORE_HOOK.exists(), f"missing {CORE_HOOK.relative_to(ROOT)}"
    assert HUB_HOOK.exists(), (
        f"missing {HUB_HOOK.relative_to(ROOT)} — the hub-unwired regression: the BA "
        "hook must be copied into the hub, not left only in the core template"
    )


def test_ba_hook_hub_copy_matches_core():
    assert HUB_HOOK.read_text(encoding="utf-8") == CORE_HOOK.read_text(encoding="utf-8"), (
        "hub BA hook drifted from core — re-copy core/.claude/hooks/"
        f"{HOOK_BASENAME} into .claude/hooks/"
    )


def test_ba_hook_wired_in_core_settings():
    assert HOOK_BASENAME in _user_prompt_submit_commands(CORE_SETTINGS), (
        "core settings.json must wire the BA hook into UserPromptSubmit"
    )


def test_ba_hook_wired_in_hub_settings():
    assert HOOK_BASENAME in _user_prompt_submit_commands(HUB_SETTINGS), (
        "hub settings.json must wire the BA hook into UserPromptSubmit — this is the "
        "exact regression that caused the silent BA skip"
    )


def test_ba_hook_is_an_offer_not_a_silent_mandate():
    body = CORE_HOOK.read_text(encoding="utf-8")
    assert "*Sync-check:*" in body, "BA hook must surface a *Sync-check:* OFFER"
    assert "BA-GATE" in body, "BA hook must label its injection BA-GATE"


def test_ba_hook_keyword_gate_covers_missed_phrasings():
    body = CORE_HOOK.read_text(encoding="utf-8").lower()
    # The phrasings whose absence caused the original miss must all be matchable.
    for phrase in ["work on", "add", "extend", "i need", "help me"]:
        assert phrase in body, (
            f"BA hook keyword gate lost '{phrase}' — the broadened gate must keep the "
            "phrasings that previously slipped past it"
        )
    # Domain signals that should trigger even without an explicit build verb.
    for signal in ["tax", "loan", "pricing", "financ"]:
        assert signal in body, f"BA hook lost domain signal '{signal}'"
