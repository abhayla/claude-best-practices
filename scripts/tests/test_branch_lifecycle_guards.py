"""Guards for the two branch-lifecycle enforcement hooks added after the core feature:

- branch-choice-gate.sh — PreToolUse(Edit|Write|MultiEdit): deterministic first-edit reminder to
  run the branch-choice menu, gated on the per-session marker. NON-BLOCKING (never denies an edit).
- session-concurrency-guard.sh — SessionStart, ADVISORY: warns when another session shares the
  working tree (git keeps one branch per checkout) and recommends a worktree. Never mutates git.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
GATE = ROOT / ".claude" / "hooks" / "branch-choice-gate.sh"
GUARD = ROOT / ".claude" / "hooks" / "session-concurrency-guard.sh"
AUTOPR = ROOT / ".claude" / "hooks" / "auto-pr.sh"
SETTINGS = ROOT / ".claude" / "settings.json"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _pretooluse_matchers() -> dict:
    blocks = json.loads(_read(SETTINGS))["hooks"].get("PreToolUse", [])
    return {b.get("matcher", ""): [h["command"] for h in b.get("hooks", [])] for b in blocks}


def _sessionstart_cmds() -> list[str]:
    return [
        h["command"]
        for b in json.loads(_read(SETTINGS))["hooks"].get("SessionStart", [])
        for h in b.get("hooks", [])
    ]


# ---- branch-choice gate (PreToolUse) --------------------------------------

def test_gate_exists():
    assert GATE.exists(), "branch-choice-gate.sh must exist"


def test_gate_wired_on_edit_write_matcher():
    matchers = _pretooluse_matchers()
    target = next((m for m in matchers if "Edit" in m and "Write" in m), None)
    assert target, "a PreToolUse matcher must cover Edit|Write (got: %s)" % list(matchers)
    assert any("branch-choice-gate.sh" in c for c in matchers[target]), (
        "branch-choice-gate.sh must be wired on the Edit|Write|MultiEdit matcher"
    )


def test_gate_is_marker_gated():
    assert ".branch-choice-active" in _read(GATE), "gate must gate on the per-session marker"


def test_gate_is_non_blocking():
    body = _read(GATE)
    # MUST NOT deny/block an edit — no exit 2, no permission-deny decision.
    assert "exit 2" not in body, "gate must be non-blocking (no exit 2)"
    assert '"deny"' not in body and "permissionDecision" not in body, "gate must not deny edits"
    assert "exit 0" in body, "gate must be fail-safe (exit 0)"
    assert "BRANCH_CHOICE_GATE_DISABLE" in body, "gate must honor its off-switch"


@pytest.mark.skipif(not shutil.which("bash"), reason="needs bash")
def test_gate_execution_silent_with_marker_injects_without(tmp_path):
    bash = shutil.which("bash")
    # Run inside a tmp git repo so ROOT resolves there.
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    subprocess.run([shutil.which("git"), "init", "-q"], cwd=repo)
    sid = "sessAAA"
    marker = repo / ".claude" / f".branch-choice-active.{sid}"

    # marker ABSENT -> injects, naming THIS session's scoped marker path
    r1 = subprocess.run([bash, str(GATE)], cwd=repo, input=json.dumps({"session_id": sid}),
                        capture_output=True, text=True)
    assert r1.returncode == 0
    assert "BRANCH-CHOICE GATE" in r1.stdout and "additionalContext" in r1.stdout
    assert f".branch-choice-active.{sid}" in r1.stdout, "reminder must name the session-scoped marker"

    # THIS session's marker PRESENT -> silent
    marker.write_text("", encoding="utf-8")
    r2 = subprocess.run([bash, str(GATE)], cwd=repo, input=json.dumps({"session_id": sid}),
                        capture_output=True, text=True)
    assert r2.returncode == 0 and r2.stdout.strip() == "", "gate must be silent once THIS session's marker exists"

    # Fix 1: a DIFFERENT session still gets its own menu despite the first session's marker
    # (per-SESSION, not per-working-tree — this is the concurrent-session collision that was broken).
    r3 = subprocess.run([bash, str(GATE)], cwd=repo, input=json.dumps({"session_id": "sessBBB"}),
                        capture_output=True, text=True)
    assert r3.returncode == 0 and "BRANCH-CHOICE GATE" in r3.stdout, (
        "a concurrent session must still get its own menu despite another session's marker"
    )


@pytest.mark.skipif(not shutil.which("bash"), reason="needs bash")
def test_gate_escalates_to_worktree_on_concurrent_live_session(tmp_path):
    # Fix 2: at edit-time, if a DIFFERENT live session holds the working-tree lock, the gate's
    # reminder must escalate to a worktree recommendation (catches the collision the SessionStart
    # guard misses for the session that started first).
    import time
    bash = shutil.which("bash")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    subprocess.run([shutil.which("git"), "init", "-q"], cwd=repo)
    (repo / ".claude" / ".session-active.lock").write_text(
        f"otherSession {int(time.time())}\n", encoding="utf-8")
    r = subprocess.run([bash, str(GATE)], cwd=repo, input=json.dumps({"session_id": "mine"}),
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "CONCURRENCY" in r.stdout and "worktree" in r.stdout, (
        "gate must escalate to a worktree recommendation when another live session shares the tree"
    )


# ---- session concurrency guard (SessionStart) -----------------------------

def test_guard_exists_and_wired():
    assert GUARD.exists(), "session-concurrency-guard.sh must exist"
    assert any("session-concurrency-guard.sh" in c for c in _sessionstart_cmds()), (
        "session-concurrency-guard.sh must be wired into SessionStart"
    )


def test_guard_is_advisory_only():
    body = _read(GUARD)
    for tok in ("gh pr merge", "git push", "git checkout", "git merge", "git rebase",
                "git reset", "branch -d", "branch -D"):
        assert tok not in body, f"concurrency guard must be advisory (no {tok})"
    assert "exit 0" in body and "CONCURRENCY_GUARD_DISABLE" in body


def test_guard_uses_session_id_and_lock():
    body = _read(GUARD)
    assert "session_id" in body, "guard must read the session_id from the hook payload"
    assert ".session-active.lock" in body, "guard must use a lock file to detect concurrency"
    assert "worktree" in body, "guard must recommend a git worktree for parallel isolation"


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_guard_execution_warns_on_second_session_only(tmp_path):
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    subprocess.run([git, "init", "-q"], cwd=repo)

    def run(sid):
        return subprocess.run(
            [bash, str(GUARD)], cwd=repo, input=json.dumps({"session_id": sid}),
            capture_output=True, text=True,
        )

    a = run("sessA")
    assert a.returncode == 0 and "CONCURRENCY" not in a.stdout, "first session must not warn"
    b = run("sessB")
    assert b.returncode == 0 and "CONCURRENCY" in b.stdout, "a second, different session must be warned"
    assert "worktree" in b.stdout
    same = run("sessB")
    assert "CONCURRENCY" not in same.stdout, "the SAME session re-running must not warn itself"


def test_guard_suppresses_warning_on_resume_and_clear():
    body = _read(GUARD)
    assert ".source" in body, "guard must read the SessionStart source field"
    assert '"resume"' in body and '"clear"' in body, (
        "guard must suppress the concurrency warning on resume/clear (same operator, not a 2nd session)"
    )


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_guard_warns_on_startup_but_not_resume(tmp_path):
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    subprocess.run([git, "init", "-q"], cwd=repo)

    def run(sid, src):
        return subprocess.run(
            [bash, str(GUARD)], cwd=repo, input=json.dumps({"session_id": sid, "source": src}),
            capture_output=True, text=True,
        )

    run("A", "startup")                              # first session claims the lock
    resumed = run("B", "resume")                     # resuming must NOT warn (the bug we fixed)
    assert "CONCURRENCY" not in resumed.stdout, "resume must not trigger a concurrency warning"
    startup2 = run("C", "startup")                   # a genuine new startup still warns
    assert "CONCURRENCY" in startup2.stdout, "a fresh startup over a live lock must still warn"


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_guard_makes_no_git_mutations(tmp_path):
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*a):
        return subprocess.run([git, *a], cwd=repo, capture_output=True, text=True, env=env)

    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.test"); g("config", "user.name", "t")
    (repo / "a.txt").write_text("x", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "i")
    before = g("for-each-ref", "--format=%(refname) %(objectname)").stdout + g("rev-parse", "HEAD").stdout
    subprocess.run([bash, str(GUARD)], cwd=repo, input='{"session_id":"x"}', capture_output=True, text=True, env=env)
    after = g("for-each-ref", "--format=%(refname) %(objectname)").stdout + g("rev-parse", "HEAD").stdout
    assert before == after, "concurrency guard must not change any git ref or HEAD"


# ---- auto-pr.sh fast-exit on clean main (the "Hook cancelled" mitigation) --

def test_autopr_has_main_only_fast_exit():
    body = _read(AUTOPR)
    assert "fast-exit" in body, "auto-pr.sh must fast-exit on main with no other local branches"
    assert "for-each-ref" in body and "refs/heads/" in body, (
        "fast-exit must be a pure-local branch check (no network) before the slow git fetch/gh calls"
    )


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_autopr_fast_exits_on_main_only_repo(tmp_path):
    """On a repo whose only branch is main, auto-pr.sh must exit 0 and mutate nothing — it should
    NOT do the slow network work that races SessionEnd shutdown and surfaces 'Hook cancelled'."""
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*a):
        return subprocess.run([git, *a], cwd=repo, capture_output=True, text=True, env=env)

    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.test"); g("config", "user.name", "t")
    (repo / "a.txt").write_text("x", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "i")
    before = g("for-each-ref", "--format=%(refname) %(objectname)").stdout

    r = subprocess.run([bash, str(AUTOPR)], cwd=repo, capture_output=True, text=True, env=env)
    assert r.returncode == 0, "auto-pr.sh must be fail-safe (exit 0)"
    after = g("for-each-ref", "--format=%(refname) %(objectname)").stdout
    assert before == after, "fast-exit must not create branches/refs on a clean main-only repo"
    assert g("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "main", "must stay on main"
