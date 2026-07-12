"""Coexistence stand-down for plugin hooks that can double-fire against a host project's
own provisioned copies (calculatekaro migration friction, 2026-07-12; mirrors the
enhance-process-guard precedent from PR #309).

Pins, for every overlapping branch-lifecycle hook + the prompt-auto-enhance reminder:
  1. the stand-down block exists in source;
  2. BEHAVIORAL: with a host project that wires its OWN copy of the hook, the plugin copy
     exits 0 immediately with no output (project copy wins);
  3. control: with NO local copy, the hook does NOT take the stand-down exit (it proceeds
     into its own logic — proven by it emitting output OR touching state, per hook).
"""

import json
import shutil
import subprocess

import pytest

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BL_HOOKS = ROOT / "plugins" / "branch-lifecycle" / "hooks"
PAE_HOOKS = ROOT / "plugins" / "prompt-auto-enhance" / "hooks"

PATCHED = [
    BL_HOOKS / "auto-git.sh",
    BL_HOOKS / "auto-pr.sh",
    BL_HOOKS / "auto-pr-reconcile.sh",
    BL_HOOKS / "branch-choice-gate.sh",
    BL_HOOKS / "session-concurrency-guard.sh",
    BL_HOOKS / "session-git-landing.sh",
    BL_HOOKS / "stale-branch-reaper.sh",
    PAE_HOOKS / "prompt-enhance-reminder.sh",
]

BASH = shutil.which("bash")
GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(not (BASH and GIT), reason="bash+git required")


@pytest.mark.parametrize("hook", PATCHED, ids=lambda p: p.name)
def test_standdown_block_present(hook):
    text = hook.read_text(encoding="utf-8")
    assert "Coexistence stand-down" in text, f"{hook.name} missing the stand-down block"
    assert text.index("Coexistence stand-down") < 400, (
        f"{hook.name}: stand-down must run FIRST (immediately after the shebang), "
        "before any side effect"
    )


def _host_project(tmp_path, with_own_copy: bool, hook_name: str) -> Path:
    proj = tmp_path / ("with_copy" if with_own_copy else "without_copy")
    (proj / ".claude" / "hooks").mkdir(parents=True)
    subprocess.run([GIT, "init", "-q"], cwd=proj, check=True)
    settings = {"hooks": {}}
    if with_own_copy:
        (proj / ".claude" / "hooks" / hook_name).write_text("#!/usr/bin/env bash\nexit 0\n")
        settings["hooks"] = {
            "SessionStart": [{"hooks": [{"type": "command",
                                          "command": f'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/{hook_name}"'}]}]
        }
    (proj / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return proj


@pytest.mark.parametrize("hook", PATCHED, ids=lambda p: p.name)
def test_plugin_copy_stands_down_when_project_wires_own(tmp_path, hook):
    proj = _host_project(tmp_path, True, hook.name)
    res = subprocess.run(
        [BASH, str(hook)], input='{"prompt":"x","transcript_path":""}',
        capture_output=True, text=True, cwd=str(proj), timeout=60,
    )
    assert res.returncode == 0, f"{hook.name} must exit 0 on stand-down"
    assert res.stdout.strip() == "", (
        f"{hook.name} must be SILENT when standing down, got: {res.stdout[:200]}"
    )


def test_control_reminder_proceeds_without_local_copy(tmp_path):
    """Control for the reminder hook: with no local copy it must NOT silently exit —
    it emits its reminder/governance output on a plain human prompt."""
    hook = PAE_HOOKS / "prompt-enhance-reminder.sh"
    proj = _host_project(tmp_path, False, hook.name)
    res = subprocess.run(
        [BASH, str(hook)],
        input=json.dumps({"prompt": "please refactor the auth module and add tests"}),
        capture_output=True, text=True, cwd=str(proj), timeout=60,
    )
    assert res.returncode == 0
    assert res.stdout.strip() != "", "reminder hook should produce output when no local copy exists"
