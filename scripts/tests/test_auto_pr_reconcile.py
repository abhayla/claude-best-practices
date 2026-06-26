"""Guard for the SessionStart PR-reconcile hook (auto-pr-reconcile.sh).

Closes the gap where a missed SessionEnd left CLEAN PRs open with no action: the
reconcile hook runs at the reliably-firing SessionStart and arms/prunes ALL eligible
open PRs, except the current (active) branch. These tests pin the safety properties.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "auto-pr-reconcile.sh"
LIB = ROOT / ".claude" / "hooks" / "session-git-landing.sh"  # shared landing SSOT it delegates to
SETTINGS = ROOT / ".claude" / "settings.json"


def _hook() -> str:
    return HOOK.read_text(encoding="utf-8")


def _lib() -> str:
    return LIB.read_text(encoding="utf-8")


def test_hook_exists():
    assert HOOK.exists(), "auto-pr-reconcile.sh must exist in .claude/hooks/"


def test_wired_into_session_start():
    cmds = [
        h["command"]
        for block in json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"].get("SessionStart", [])
        for h in block.get("hooks", [])
    ]
    assert any("auto-pr-reconcile.sh" in c for c in cmds), (
        "auto-pr-reconcile.sh must be wired into SessionStart (the reliably-firing event)"
    )


def test_excludes_current_branch():
    """The reconcile MUST NOT arm the current HEAD branch — that would merge active work.
    The reconcile logic lives in the shared SSOT that the hook delegates to."""
    assert "session-git-landing.sh" in _hook() and "reconcile" in _hook(), (
        "auto-pr-reconcile.sh must delegate to the shared landing lib's reconcile"
    )
    lib = _lib()
    assert 'cur="$(git rev-parse --abbrev-ref HEAD' in lib
    assert '"$br" = "$cur"' in lib, (
        "reconcile must skip the current branch so active work is never auto-merged"
    )


def test_honors_off_switches():
    body = _hook()
    assert 'AUTO_PR_DISABLE' in body, "must honor AUTO_PR_DISABLE=1"
    assert 'AUTO_MERGE' in body, "must honor AUTO_MERGE=0 (prune-only)"


def test_is_fail_safe():
    assert "exit 0" in _hook(), "hook must be fail-safe (always exit 0 so it never blocks session start)"
    # Only arms via native --auto, so GitHub still gates the real merge on required checks (in the lib).
    assert "--auto --squash" in _lib(), "must arm native CI-gated auto-merge, not force a merge"


def test_skips_draft_and_already_armed_prs():
    lib = _lib()  # the draft/already-armed filtering lives in the shared landing lib
    assert "isDraft==false" in lib, "must skip draft PRs"
    assert "autoMergeRequest==null" in lib, "must skip PRs that already have auto-merge armed"
