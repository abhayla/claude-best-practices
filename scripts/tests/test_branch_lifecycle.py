"""Guards for the autonomous branch-lifecycle automation.

Covers the two hooks (auto-git.sh commit/push + auto-pr.sh PR/auto-merge/prune), their
settings.json wiring, and the branch-lifecycle control skill. These are safety-property
tests: they pin the guardrails that keep the automation from losing code or messing up
main (no force-push, secret-scan gate, delete-only-after-MERGED, CI-gated merge).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUTO_GIT = ROOT / ".claude" / "hooks" / "auto-git.sh"
AUTO_PR = ROOT / ".claude" / "hooks" / "auto-pr.sh"
SETTINGS = ROOT / ".claude" / "settings.json"
SKILL = ROOT / ".claude" / "skills" / "git-branch-lifecycle" / "SKILL.md"

bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ---- existence -------------------------------------------------------------

def test_hooks_and_skill_exist():
    for p in (AUTO_GIT, AUTO_PR, SKILL):
        assert p.is_file(), f"missing {p}"


# ---- syntax ----------------------------------------------------------------

@bash
@pytest.mark.parametrize("hook", [AUTO_GIT, AUTO_PR])
def test_hook_bash_syntax_valid(hook):
    r = subprocess.run(["bash", "-n", str(hook)], capture_output=True, text=True)
    assert r.returncode == 0, f"{hook.name} syntax error: {r.stderr}"


# ---- auto-pr.sh safety properties -----------------------------------------

def test_auto_pr_is_fail_open():
    body = _read(AUTO_PR)
    assert body.rstrip().endswith("exit 0"), "auto-pr.sh must fail-open (end with exit 0)"


def test_auto_pr_has_off_switches():
    body = _read(AUTO_PR)
    assert "AUTO_PR_DISABLE" in body, "missing AUTO_PR_DISABLE off-switch"
    assert "AUTO_MERGE" in body, "missing AUTO_MERGE (gate human-merge) off-switch"


def test_auto_pr_never_targets_main():
    body = _read(AUTO_PR)
    # guards that prevent opening a PR / merging from main itself
    assert 'branch" = "main"' in body and 'branch" = "master"' in body


def test_auto_pr_uses_ci_gated_auto_merge_squash():
    body = _read(AUTO_PR)
    assert "--auto" in body, "merge must be CI-gated via --auto"
    assert "--squash" in body, "feature->main must squash-merge (git-collaboration.md)"


def test_auto_pr_prunes_only_after_merged_confirmation():
    body = _read(AUTO_PR)
    # the only hard-delete must be preceded by a MERGED check in the same pipeline
    assert "branch -D" in body, "expected a prune path"
    assert "MERGED" in body, "branch -D must be gated on a gh MERGED confirmation"


# ---- auto-git.sh safety properties ----------------------------------------

def test_auto_git_secret_scan_gate_present():
    body = _read(AUTO_GIT)
    assert "--secret-scan" in body and "No secrets found" in body, \
        "auto-git must abort commit unless secret-scan is confirmed clean"


def test_auto_git_protects_main_and_merged_branches():
    body = _read(AUTO_GIT)
    assert 'branch" = "main"' in body, "must not commit onto main"
    assert "MERGED" in body, "must not stack new work onto an already-merged branch (G4)"


def test_auto_git_detects_merged_branch_without_gh():
    # Guardrail 1b must NOT rely on `gh pr view` alone — once a branch's PR squash-merges
    # and the remote is pruned, gh often can't resolve it. The network-independent signal
    # (commits ahead of origin/main by SHA + zero net content diff) must back it up, or the
    # post-merge-commit gap (this session's incident) silently regresses.
    body = _read(AUTO_GIT)
    assert "git diff --quiet origin/main..HEAD" in body, (
        "guardrail 1b must detect a squash-merged branch by content (zero net diff), "
        "not by `gh pr view` alone — see the pruned-remote gap"
    )
    assert "rev-list --count origin/main..HEAD" in body, (
        "the content-diff signal must be gated on commits-ahead>0 so a fresh branch "
        "(0 ahead, identical to main) never false-triggers a rotation"
    )


# ---- no dangerous git anywhere in the new automation ----------------------

@pytest.mark.parametrize("hook", [AUTO_GIT, AUTO_PR])
def test_no_force_push_or_no_verify(hook):
    # inspect only executable lines — a safety comment like "never --force" is allowed
    code = "\n".join(
        ln for ln in _read(hook).splitlines() if not ln.lstrip().startswith("#")
    )
    for bad in ("--force", "--no-verify", "push -f"):
        assert bad not in code, f"{hook.name} must never use {bad!r}"


# ---- settings.json wiring --------------------------------------------------

def test_settings_wires_hooks_to_correct_events():
    cfg = json.loads(_read(SETTINGS))
    hooks = cfg.get("hooks", {})

    def commands(event):
        return [
            h.get("command", "")
            for blk in hooks.get(event, [])
            for h in blk.get("hooks", [])
        ]

    assert any("auto-pr.sh" in c for c in commands("SessionEnd")), \
        "auto-pr.sh must be wired to SessionEnd (arm merge on close, not mid-turn)"
    assert any("auto-git.sh" in c for c in commands("SessionStart")), \
        "auto-git.sh must run at SessionStart"
    assert any("auto-git.sh" in c for c in commands("Stop")), \
        "auto-git.sh must run at Stop"
    # auto-pr must NOT be on Stop (that would arm merge after every turn, mid-work)
    assert not any("auto-pr.sh" in c for c in commands("Stop")), \
        "auto-pr.sh must NOT be on Stop — it would merge work mid-session"


# ---- skill frontmatter -----------------------------------------------------

def test_skill_frontmatter_well_formed():
    body = _read(SKILL)
    assert body.startswith("---"), "skill must open with YAML frontmatter"
    fm = body.split("---", 2)[1]
    assert "name: git-branch-lifecycle" in fm, "name must match directory"
    for field in ("description:", "type: workflow", "allowed-tools:", "version:"):
        assert field in fm, f"frontmatter missing {field}"
    # finish-mode must dispatch the independent reviewer
    assert "code-reviewer-agent" in body, "finish must run an independent agent review"
