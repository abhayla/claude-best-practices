"""Regression guard for the verifier-edge Stop hook (Phase 2 — fragile-governance hardening).

Pins the deterministic salience layer for the three "independent verifier before done"
gates (reviewer-edge, independent-test-verification, supervisor-verification):
- present + identical in BOTH core and hub
- wired into BOTH settings.json Stop arrays
- the runtime log is gitignored
- registered as a hook
- telemetry-first (logs a miss; never emits decision:block) and signal-gated on all three
  builder signals (code edit, Task subagent, test run) + a done-claim + absence of verifier evidence
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
HUB_CLAUDE = ROOT / ".claude"

CORE_HOOK = CORE_CLAUDE / "hooks" / "verifier-edge-guard.sh"
HUB_HOOK = HUB_CLAUDE / "hooks" / "verifier-edge-guard.sh"
CORE_SETTINGS = CORE_CLAUDE / "settings.json"
HUB_SETTINGS = HUB_CLAUDE / "settings.json"
GITIGNORE = ROOT / ".gitignore"
REGISTRY = ROOT / "registry" / "patterns.json"

HOOK_BASENAME = "verifier-edge-guard.sh"


def _stop_commands(settings_path: Path) -> str:
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    cmds = []
    for block in data.get("hooks", {}).get("Stop", []):
        for hook in block.get("hooks", []):
            cmds.append(hook.get("command", ""))
    return "\n".join(cmds)


def test_hook_present_in_core_and_hub():
    assert CORE_HOOK.exists(), f"missing {CORE_HOOK.relative_to(ROOT)}"
    assert HUB_HOOK.exists(), (
        f"missing {HUB_HOOK.relative_to(ROOT)} — hub-unwired regression (force-add the hub copy)"
    )


def test_hook_hub_copy_matches_core():
    assert HUB_HOOK.read_text(encoding="utf-8") == CORE_HOOK.read_text(encoding="utf-8"), (
        "hub verifier-edge hook drifted from core — re-copy it"
    )


def test_hook_wired_in_both_stop_arrays():
    assert HOOK_BASENAME in _stop_commands(CORE_SETTINGS), "core settings.json must wire it into Stop"
    assert HOOK_BASENAME in _stop_commands(HUB_SETTINGS), "hub settings.json must wire it into Stop"


def test_runtime_log_is_gitignored():
    assert ".claude/.verifier-misses.log" in GITIGNORE.read_text(encoding="utf-8"), (
        "the verifier-misses runtime log must be gitignored (it is per-session state)"
    )


def test_hook_is_telemetry_first_not_blocking():
    body = CORE_HOOK.read_text(encoding="utf-8")
    assert ".verifier-misses.log" in body, "hook must log misses to the telemetry file"
    assert "decision" not in body or '"decision":"block"' not in body.replace(" ", ""), (
        "Phase-2 v1 is telemetry-first — it MUST NOT emit decision:block (escalate later if frequent)"
    )


def test_hook_covers_all_three_builder_signals():
    body = CORE_HOOK.read_text(encoding="utf-8")
    # code edit
    assert "Edit|Write|MultiEdit|NotebookEdit" in body, "must detect code Edit/Write builder work"
    # subagent
    assert "Task :: " in body, "must detect a Task subagent dispatch as builder work"
    # test run
    assert "pytest" in body and "playwright test" in body, "must detect a test-runner Bash command"


def test_multiedit_path_is_projected():
    # MultiEdit carries targets under .input.edits[].file_path, not .input.file_path —
    # the projection MUST include edits[0].file_path or MultiEdit silently never fires
    # (false-negative found in independent review).
    body = CORE_HOOK.read_text(encoding="utf-8")
    assert ".input.edits[0].file_path" in body, "MultiEdit target path must be projected"


def test_last_user_slice_guards_null():
    # The last-real-user index must not subtract from null when there is no real user
    # message (jq error → dead 'keep whole transcript' branch). Guard via index(true) null-check.
    body = CORE_HOOK.read_text(encoding="utf-8")
    assert "if $ri == null then ." in body, "the zero-real-user branch must be guarded, not a raw subtraction"


def test_hook_checks_done_claim_and_verifier_evidence():
    body = CORE_HOOK.read_text(encoding="utf-8")
    assert "tests pass" in body or "all (tests )?pass" in body, "must gate on a done/pass claim"
    assert "code[- ]review" in body and "supervisor" in body, (
        "must treat code-review / supervisor / blind-verify mentions as verifier evidence (stay silent)"
    )


def test_hook_registered():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert "verifier-edge-guard" in reg, "hook must be in the registry"
    assert reg["verifier-edge-guard"]["type"] == "hook"
