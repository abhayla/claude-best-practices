"""Unit + wiring guards for the native governance hooks (S3 + S5, 2026-06-20).

These pin the SCRIPT logic (deterministic given a payload) and the settings.json
wiring. They do NOT assert the events actually fire in a given Claude Code
version — that needs a live dispatch/config-edit after a session restart, which
no unit test can do (newly-wired hooks are session-pinned, like agents).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
SETTINGS = ROOT / ".claude" / "settings.json"
SUBAGENT_HOOK = HOOKS / "subagent-governance-inject.sh"
CONFIG_HOOK = HOOKS / "config-change-crud-guard.sh"

BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


def _wired_commands(event: str) -> str:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    blocks = data.get("hooks", {}).get(event, [])
    return "\n".join(
        hk.get("command", "") for blk in blocks for hk in blk.get("hooks", [])
    )


def test_hook_scripts_exist():
    assert SUBAGENT_HOOK.exists(), "SubagentStart hook missing"
    assert CONFIG_HOOK.exists(), "ConfigChange hook missing"


def test_subagent_hook_wired():
    assert "subagent-governance-inject.sh" in _wired_commands("SubagentStart"), (
        "SubagentStart hook not wired into .claude/settings.json"
    )


def test_config_change_hook_wired():
    assert "config-change-crud-guard.sh" in _wired_commands("ConfigChange"), (
        "ConfigChange hook not wired into .claude/settings.json"
    )


@needs_bash
def test_subagent_hook_emits_mandates_as_valid_json():
    payload = '{"hook_event_name":"SubagentStart","agent_type":"general-purpose"}'
    out = subprocess.run(
        [BASH, str(SUBAGENT_HOOK)], input=payload, capture_output=True, text=True, timeout=20
    ).stdout
    obj = json.loads(out)  # must be valid JSON
    ctx = obj["hookSpecificOutput"]["additionalContext"]
    # Substance: all three load-bearing dispatch mandates must be injected.
    assert "PLAN FIRST" in ctx
    assert "ROOT CAUSE, NOT PATCH" in ctx
    assert "STRUCTURED CONTRACT" in ctx


@needs_bash
def test_subagent_hook_stays_valid_json_without_python():
    """Load-bearing degenerate path: if `python` is absent the mandates degrade to
    an empty string, but the JSON envelope MUST stay valid (never crash/garble)."""
    import os

    payload = '{"hook_event_name":"SubagentStart"}'
    # Strip python from PATH; keep a minimal dir so bash builtins still resolve.
    env = dict(os.environ, PATH=str(ROOT / "nonexistent-dir"))
    out = subprocess.run(
        [BASH, str(SUBAGENT_HOOK)], input=payload, capture_output=True, text=True,
        timeout=20, env=env,
    ).stdout
    obj = json.loads(out)  # must still parse
    assert "additionalContext" in obj["hookSpecificOutput"]


@needs_bash
def test_config_change_hook_appends_log_line():
    payload = '{"matcher":"project_settings","file_path":".claude/settings.json"}'
    res = subprocess.run(
        [BASH, str(CONFIG_HOOK)], input=payload, capture_output=True, text=True, timeout=20
    )
    assert res.returncode == 0, "hook must be non-blocking (exit 0)"
    # The hook logs into the repo's .claude/.config-changes.log (gitignored).
    log = ROOT / ".claude" / ".config-changes.log"
    assert log.exists(), "ConfigChange hook did not write its telemetry log"
    last = log.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert "config-change" in last and "project_settings" in last


def test_config_log_is_gitignored():
    assert ".config-changes.log" in (ROOT / ".gitignore").read_text(encoding="utf-8"), (
        "runtime telemetry log must be gitignored"
    )
