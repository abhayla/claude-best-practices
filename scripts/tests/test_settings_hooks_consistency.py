"""Regression guard: every hook WIRED in a settings.json must have a backing file.

Root cause this pins (investigated 2026-06-22, the cric incident): a downstream
project (cric) ended up with .claude/settings.json referencing governance hooks
(ba-usecase-discovery-reminder.sh, verifier-edge-guard.sh) whose .sh files were
never delivered, so the hooks failed at runtime with "file not found". The cause
was structural: `provision_settings_json` deep-merges core/.claude/settings.json
(which WIRES those hooks) into the target, but hook FILES were copied by an
independent recommendation-set mechanism that never reconciled with the wiring.

The pre-existing test_ba_gate_wiring.py only pinned ONE hook. These tests pin the
general invariant for the templates the hub SHIPS, and prove the provisioning path
now delivers every hook it wires.
"""

import json
import shutil
from pathlib import Path

import pytest

from scripts.recommend import (
    provision_settings_json,
    referenced_hook_basenames,
)

ROOT = Path(__file__).parent.parent.parent
CORE_SETTINGS = ROOT / "core" / ".claude" / "settings.json"
HUB_SETTINGS = ROOT / ".claude" / "settings.json"


def _missing_hook_files(settings_path: Path) -> list[str]:
    """Hook basenames the settings wires that have no backing file beside it."""
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    hooks_dir = settings_path.parent / "hooks"
    return [
        name
        for name in sorted(referenced_hook_basenames(settings))
        if not (hooks_dir / name).exists()
    ]


def test_core_template_wires_no_missing_hooks():
    """The DISTRIBUTABLE template must never wire a hook it cannot deliver."""
    missing = _missing_hook_files(CORE_SETTINGS)
    assert not missing, (
        f"core/.claude/settings.json wires hooks with no file in core/.claude/hooks/: "
        f"{missing} — add the file or remove the wiring before it ships downstream"
    )


def test_hub_settings_wires_no_missing_hooks():
    """The hub's own settings.json must reference only hooks that exist."""
    missing = _missing_hook_files(HUB_SETTINGS)
    assert not missing, (
        f".claude/settings.json wires hooks with no file in .claude/hooks/: {missing}"
    )


def test_referenced_hook_basenames_extracts_bash_and_powershell():
    settings = {
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"command": 'bash "$(git rev-parse --show-toplevel)/.claude/hooks/a.sh"'}]}
            ],
            "PreToolUse": [
                {"hooks": [{"command": 'powershell -File "$CLAUDE_PROJECT_DIR/.claude/hooks/b.ps1"'}]}
            ],
        }
    }
    assert referenced_hook_basenames(settings) == {"a.sh", "b.ps1"}


def test_provision_delivers_every_wired_hook(tmp_path):
    """Reproduces the cric gap: a target whose settings wire governance hooks but
    lack the files must, after provisioning, have those files delivered."""
    target = tmp_path / "downstream"
    (target / ".claude" / "hooks").mkdir(parents=True)
    # Pre-existing target settings with project-local wiring only — no governance hooks yet.
    (target / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"Stop": [{"matcher": "", "hooks": []}]}}, indent=2),
        encoding="utf-8",
    )

    status = provision_settings_json(ROOT, target)
    assert status == "merged"

    merged = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
    wired = referenced_hook_basenames(merged)
    # Every wired hook that exists in core must now exist in the target.
    src_hooks = ROOT / "core" / ".claude" / "hooks"
    for name in wired:
        if (src_hooks / name).exists():
            assert (target / ".claude" / "hooks" / name).exists(), (
                f"provision wired {name} but did not deliver its file"
            )


def test_provision_leaves_target_only_hooks_untouched(tmp_path):
    """A hook the target already owns (not in core) must not be clobbered."""
    target = tmp_path / "downstream"
    (target / ".claude" / "hooks").mkdir(parents=True)
    local_hook = target / ".claude" / "hooks" / "project-local.ps1"
    local_hook.write_text("# project-owned", encoding="utf-8")
    (target / ".claude" / "settings.json").write_text(
        json.dumps(
            {"hooks": {"PreToolUse": [
                {"matcher": "Edit", "hooks": [
                    {"command": 'powershell -File "$CLAUDE_PROJECT_DIR/.claude/hooks/project-local.ps1"'}
                ]}
            ]}},
            indent=2,
        ),
        encoding="utf-8",
    )

    provision_settings_json(ROOT, target)
    assert local_hook.read_text(encoding="utf-8") == "# project-owned"
