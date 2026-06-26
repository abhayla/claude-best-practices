"""Tests for the local post-merge reconcile in session-git-landing.sh.

ROOT-CAUSE coverage: `land --wait` used to merge the PR REMOTELY but leave the LOCAL clone on the
now-dead branch with a stale `main` and an un-pruned branch — so the work looked unmerged locally.
`_sync_local_after_merge` fixes that. These tests verify (1) the helper is wired into the MERGED
path, (2) it reconciles a simulated squash-merge, and (3) it never clobbers a dirty tree.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LANDING = ROOT / ".claude" / "hooks" / "session-git-landing.sh"
CORE_LANDING = ROOT / "core" / ".claude" / "hooks" / "session-git-landing.sh"

bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_helper_defined_and_wired_into_merged_path():
    body = _read(LANDING)
    assert "_sync_local_after_merge()" in body, "helper must be defined"
    # It must be called from the MERGED branch of the --wait state machine.
    merged_line = next(l for l in body.splitlines() if l.strip().startswith("MERGED)"))
    assert "_sync_local_after_merge" in merged_line, "MERGED case must call the reconcile helper"


def test_reconcile_is_dirty_safe_and_squash_safe():
    body = _read(LANDING)
    assert "git status --porcelain" in body, "must guard on a dirty tree before switching"
    assert "branch -D" in body, "squash merge => local branch isn't an ancestor; must use -D"
    assert "merge --ff-only origin/main" in body, "must fast-forward local main"


def test_dispatch_is_source_guarded():
    # Sourcing the file (for tests) must not trigger the usage/exit path.
    assert 'BASH_SOURCE[0]:-$0' in _read(LANDING), "dispatch must be guarded so the file is sourceable"


def test_core_copy_in_sync():
    assert _read(LANDING) == _read(CORE_LANDING), "hub and core copies must stay byte-identical (dual-home synced)"


@bash
def test_reconcile_after_simulated_squash_merge(tmp_path):
    """End-to-end: caller left ON a squash-merged branch → ends on main, branch pruned, content present."""
    script = f"""
    set -e
    cd "{tmp_path}"
    git init -q --bare origin.git
    git clone -q origin.git work && cd work
    git config user.email t@t.com && git config user.name t
    echo base > f.txt && git add -A && git commit -qm base && git push -q origin HEAD:main
    git checkout -q -b feature && echo work >> f.txt && git add -A && git commit -qm feat
    git checkout -q main 2>/dev/null || git checkout -q -b main
    echo work >> f.txt && git add -A && git commit -qm 'squashed (#999)' && git push -q origin HEAD:main
    git checkout -q feature
    source "{LANDING}"
    _sync_local_after_merge feature
    echo "BRANCH=$(git rev-parse --abbrev-ref HEAD)"
    echo "FEATURE_EXISTS=$(git branch --list feature | wc -l | tr -d ' ')"
    """
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "BRANCH=main" in r.stdout, r.stdout
    assert "FEATURE_EXISTS=0" in r.stdout, r.stdout


@bash
def test_reconcile_skips_dirty_tree(tmp_path):
    """A dirty working tree must be preserved — never clobbered by the switch to main."""
    script = f"""
    set -e
    cd "{tmp_path}"
    git init -q --bare origin.git
    git clone -q origin.git work && cd work
    git config user.email t@t.com && git config user.name t
    echo base > f.txt && git add -A && git commit -qm base && git push -q origin HEAD:main
    git checkout -q -b feature && echo dirty >> uncommitted.txt
    source "{LANDING}"
    _sync_local_after_merge feature
    echo "BRANCH=$(git rev-parse --abbrev-ref HEAD)"
    echo "DIRTY_EXISTS=$(test -f uncommitted.txt && echo 1 || echo 0)"
    """
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "BRANCH=feature" in r.stdout, r.stdout
    assert "DIRTY_EXISTS=1" in r.stdout, r.stdout
