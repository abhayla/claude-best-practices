"""Guards for the stale-branch reaper + the branch-choice model-layer rule.

The reaper (SessionStart) is REPORT-ONLY: it lists branches idle >24h and resets the
per-session branch-choice marker. It must never merge/push/delete/checkout. The actual
landing is owner-approved via session-git-landing.sh `merge-one`. The branch-choice rule
drives the once-per-session interactive menu (a Stop hook can't prompt interactively).
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
REAPER = ROOT / ".claude" / "hooks" / "stale-branch-reaper.sh"
SKILL = ROOT / ".claude" / "skills" / "branch-choice" / "SKILL.md"
LIB = ROOT / ".claude" / "hooks" / "session-git-landing.sh"
CORE_LIB = ROOT / "core" / ".claude" / "hooks" / "session-git-landing.sh"
SETTINGS = ROOT / ".claude" / "settings.json"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _func_body(src: str, name: str) -> str:
    """Slice a shell function body (`name() {` … first `\\n}` at col 0) so assertions can be
    scoped to ONE function — otherwise a substring also present in land()/reconcile() would
    mask a regression in the function under test."""
    m = re.search(rf"^{re.escape(name)}\(\) \{{$", src, re.M)
    assert m, f"function {name}() not found in landing lib"
    rest = src[m.end():]
    end = rest.find("\n}\n")
    assert end != -1, f"could not find end of {name}()"
    return rest[:end]


# ---- reaper hook ----------------------------------------------------------

def test_reaper_exists():
    assert REAPER.exists(), "stale-branch-reaper.sh must exist in .claude/hooks/"


def test_reaper_wired_into_session_start():
    cmds = [
        h["command"]
        for block in json.loads(_read(SETTINGS))["hooks"].get("SessionStart", [])
        for h in block.get("hooks", [])
    ]
    assert any("stale-branch-reaper.sh" in c for c in cmds), (
        "stale-branch-reaper.sh must be wired into SessionStart"
    )


def test_reaper_is_report_only():
    body = _read(REAPER)
    # MUST NOT mutate git state — broad denylist of every mutation vector, not just a few.
    forbidden = [
        "gh pr merge", "gh pr create", "git push", "git checkout", "checkout -b",
        "git merge", "git rebase", "git reset", "branch -d", "branch -D", "branch -m",
        "update-ref", "git fetch", "git commit", "git stash",
    ]
    hits = [tok for tok in forbidden if tok in body]
    assert hits == [], f"reaper must be report-only (zero git side-effects); found: {hits}"


def test_reaper_resets_branch_choice_marker():
    body = _read(REAPER)
    assert ".branch-choice-active" in body and "rm -f" in body, (
        "reaper must clear the per-session branch-choice marker at SessionStart (ask-once-per-session)"
    )


def test_reaper_nudges_branch_choice_skill():
    body = _read(REAPER)
    assert "BRANCH-CHOICE:" in body and "branch-choice" in body, (
        "reaper must nudge the model to run the branch-choice skill before the first edit"
    )


def test_reaper_has_24h_threshold_and_tunable():
    body = _read(REAPER)
    assert "STALE_BRANCH_HOURS" in body, "threshold must be tunable via STALE_BRANCH_HOURS"
    assert ":-24" in body, "default staleness threshold must be 24h"


def test_reaper_fail_safe_and_off_switch():
    body = _read(REAPER)
    assert "exit 0" in body, "reaper must be fail-safe (always exit 0)"
    assert "STALE_REAPER_DISABLE" in body, "reaper must honor STALE_REAPER_DISABLE=1 off-switch"


# ---- branch-choice skill (verbose procedure lives in a skill, not a hub rule) ----

def test_skill_exists_with_frontmatter():
    assert SKILL.exists(), "branch-choice SKILL.md must exist in .claude/skills/branch-choice/"
    body = _read(SKILL)
    assert body.startswith("---") and "name: branch-choice" in body, (
        "branch-choice skill must have valid frontmatter with name: branch-choice"
    )


def test_skill_is_once_per_session():
    body = _read(SKILL)
    assert ".branch-choice-active" in body, "skill must gate on the per-session marker"
    assert "ONCE" in body or "once-per-session" in body or "once per session" in body


def test_skill_new_branch_from_main():
    body = _read(SKILL)
    assert "origin/main" in body, "new branches must be cut from fresh origin/main"
    assert "fetch" in body, "must fetch before cutting a new branch"


def test_skill_hides_keep_when_merged_and_skips_readonly():
    body = _read(SKILL)
    assert "already merged" in body, "must hide 'keep existing' when the branch is already merged"
    assert "read-only" in body or "question" in body, "must NOT prompt on read-only/question turns"


def test_skill_requires_approval_for_stale_merge():
    body = _read(SKILL)
    assert "approv" in body.lower(), "landing a stale branch must be owner-approved"
    assert "merge-one" in body, "stale landing must delegate to session-git-landing.sh merge-one"


# ---- merge-one in the shared landing lib ----------------------------------

def test_merge_one_path_exists():
    lib = _read(LIB)
    assert "merge-one)" in lib and "merge_one()" in lib, "landing lib must expose a merge-one path"


def test_merge_one_is_ci_gated_and_safe():
    # Scope to the merge_one() body — "--auto --squash"/"AUTO_MERGE" also appear in land()/reconcile(),
    # so a CI-bypass regression in merge_one (e.g. switching to `--admin`) must still be caught here.
    body = _func_body(_read(LIB), "merge_one")
    assert "--auto --squash" in body, "merge-one must arm native CI-gated auto-merge, not force a merge"
    assert "AUTO_MERGE" in body, "merge-one must honor the AUTO_MERGE=0 off-switch"
    for bypass in ("--admin", "--force", "-f ", "reset --hard"):
        assert bypass not in body, f"merge-one must not bypass CI gating (found {bypass!r})"


def test_merge_one_refuses_main():
    body = _func_body(_read(LIB), "merge_one")
    assert "refusing to merge" in body, "merge-one must refuse to merge main/master into itself"
    assert "main|master)" in body, "merge-one must guard against main/master targets"


def test_landing_lib_synced_to_core():
    assert CORE_LIB.exists(), "core copy of session-git-landing.sh must exist (synced dual-home)"
    assert _read(LIB) == _read(CORE_LIB), (
        "session-git-landing.sh is classified 'synced' — hub and core copies MUST be identical"
    )


# ---- execution test: the report-only guarantee, proven by running the hook ----

@pytest.mark.skipif(
    not (shutil.which("bash") and shutil.which("git")),
    reason="needs bash + git on PATH",
)
def test_reaper_execution_makes_zero_git_mutations(tmp_path):
    """Run the reaper in a throwaway repo with a stale branch and prove it changes nothing:
    HEAD, current branch, and ALL refs are byte-identical before/after. This catches mutation
    vectors a static denylist would miss, and confirms exit 0 + the BRANCH-CHOICE nudge + marker reset."""
    repo = tmp_path / "r"
    repo.mkdir()
    bash, git = shutil.which("bash"), shutil.which("git")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*args):
        return subprocess.run([git, *args], cwd=repo, capture_output=True, text=True, env=env)

    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.test")
    g("config", "user.name", "tester")
    (repo / "a.txt").write_text("x", encoding="utf-8")
    g("add", "-A")
    g("commit", "-qm", "init")
    g("branch", "stale/old")          # a stale branch the reaper should REPORT (not touch)
    (repo / ".claude").mkdir()
    (repo / ".claude" / ".branch-choice-active").write_text("", encoding="utf-8")  # should be reset

    before_head = g("rev-parse", "HEAD").stdout
    before_branch = g("rev-parse", "--abbrev-ref", "HEAD").stdout
    before_refs = g("for-each-ref", "--format=%(refname) %(objectname)").stdout

    res = subprocess.run(
        [bash, str(REAPER)], cwd=repo, capture_output=True, text=True,
        env=dict(env, STALE_BRANCH_HOURS="0"),
    )

    assert res.returncode == 0, f"reaper must exit 0; stderr={res.stderr}"
    assert "BRANCH-CHOICE:" in res.stdout, "reaper must print the branch-choice nudge"
    assert not (repo / ".claude" / ".branch-choice-active").exists(), "reaper must reset the marker"
    assert g("rev-parse", "HEAD").stdout == before_head, "reaper must not move HEAD"
    assert g("rev-parse", "--abbrev-ref", "HEAD").stdout == before_branch, "reaper must not switch branches"
    assert g("for-each-ref", "--format=%(refname) %(objectname)").stdout == before_refs, (
        "reaper must not create/delete/move any ref (report-only)"
    )
