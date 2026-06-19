"""Unit + wiring guards for the SubagentStop + PreCompact hooks (S6 + S4, 2026-06-20).

Pins SCRIPT logic + settings.json wiring. Does NOT assert the events fire in a
given CC version — that needs a live dispatch/compaction after a session restart
(newly-wired hooks are session-pinned).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
SETTINGS = ROOT / ".claude" / "settings.json"
VERIFIER_HOOK = HOOKS / "subagent-verifier-edge.sh"
COMPACT_HOOK = HOOKS / "compaction-handoff.sh"

BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


def _wired(event: str) -> str:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    blocks = data.get("hooks", {}).get(event, [])
    return "\n".join(hk.get("command", "") for blk in blocks for hk in blk.get("hooks", []))


def test_hooks_exist():
    assert VERIFIER_HOOK.exists()
    assert COMPACT_HOOK.exists()


def test_subagentstop_hook_wired():
    assert "subagent-verifier-edge.sh" in _wired("SubagentStop")


def test_precompact_hook_wired():
    assert "compaction-handoff.sh" in _wired("PreCompact")


@needs_bash
def test_verifier_hook_emits_supervisor_gate_json():
    out = subprocess.run(
        [BASH, str(VERIFIER_HOOK)], input='{"hook_event_name":"SubagentStop"}',
        capture_output=True, text=True, timeout=20,
    ).stdout
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "REPRODUCE" in ctx and "CLAIM" in ctx, "supervisor-gate reminder missing"


@needs_bash
def test_verifier_hook_valid_json_without_python():
    import os
    env = dict(os.environ, PATH=str(ROOT / "nonexistent-dir"))
    out = subprocess.run(
        [BASH, str(VERIFIER_HOOK)], input='{}', capture_output=True, text=True,
        timeout=20, env=env,
    ).stdout
    assert "additionalContext" in json.loads(out)["hookSpecificOutput"]


@needs_bash
def test_precompact_hook_writes_breadcrumb():
    res = subprocess.run(
        [BASH, str(COMPACT_HOOK)], input='{"trigger":"manual"}',
        capture_output=True, text=True, timeout=20,
    )
    assert res.returncode == 0, "PreCompact hook must be non-blocking"
    crumb = ROOT / ".claude" / ".compaction-handoff.md"
    assert crumb.exists(), "compaction breadcrumb not written"
    text = crumb.read_text(encoding="utf-8")
    assert "Compaction handoff breadcrumb" in text and "branch:" in text


def test_breadcrumb_is_gitignored():
    assert ".compaction-handoff.md" in (ROOT / ".gitignore").read_text(encoding="utf-8")
