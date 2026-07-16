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

def test_autopr_main_guard_precedes_network_calls():
    """Structural companion to the behavioural test below: the main/master guard must sit ABOVE the
    first network call in the CODE (comments stripped — the prose legitimately names `git fetch`)."""
    code = [
        ln for ln in _read(AUTOPR).splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    guard_at = next(
        (i for i, ln in enumerate(code) if "main|master" in ln or '"$_cur" = "main"' in ln), None
    )
    assert guard_at is not None, "auto-pr.sh must guard on main/master before doing network work"
    net_at = next(
        (i for i, ln in enumerate(code) if "git fetch" in ln or "gh pr " in ln), len(code)
    )
    assert guard_at < net_at, (
        f"main/master guard (line {guard_at}) must precede the first network call (line {net_at})"
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


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_autopr_fast_exits_on_main_with_other_local_branches(tmp_path):
    """REGRESSION (2026-07-16 'Hook cancelled'): the fast-exit used to require main to be the ONLY
    local branch, so any leftover branch sent SessionEnd into `git fetch --prune` + a `gh pr view`
    per stale branch — multi-second network I/O that the shutdown window kills. On main there is
    nothing to LAND (session-git-landing.sh skips main), so it must fast-exit regardless of how
    many other local branches exist; pruning is auto-pr-reconcile.sh's job at SessionStart."""
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude").mkdir()
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*a):
        return subprocess.run([git, *a], cwd=repo, capture_output=True, text=True, env=env)

    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.test"); g("config", "user.name", "t")
    (repo / "a.txt").write_text("x", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "i")
    g("branch", "leftover/one"); g("branch", "leftover/two")
    before = g("for-each-ref", "--format=%(refname) %(objectname)").stdout

    # Shim `git` + `gh` on PATH so any NETWORK call leaves a hard marker. Asserting absence needs
    # this: the hook swallows `git fetch` output (`>/dev/null 2>&1 || true`), so a clean exit alone
    # cannot distinguish "skipped the fetch" from "fetched and failed quietly" — and it is exactly
    # that multi-second network I/O the SessionEnd shutdown window cancels.
    marker = tmp_path / "network-was-called"
    shim = tmp_path / "shim"; shim.mkdir()
    (shim / "git").write_text(
        "#!/usr/bin/env bash\n"
        'for a in "$@"; do case "$a" in\n'
        f'  fetch|push|ls-remote) echo "git $*" >> "{marker.as_posix()}";;\n'
        "esac; done\n"
        f'exec "{git}" "$@"\n',
        encoding="utf-8",
    )
    (shim / "gh").write_text(
        "#!/usr/bin/env bash\n" f'echo "gh $*" >> "{marker.as_posix()}"\nexit 0\n', encoding="utf-8"
    )
    for f in ("git", "gh"):
        (shim / f).chmod(0o755)
    shim_env = dict(env, PATH=f"{shim}{os.pathsep}{os.environ['PATH']}")

    r = subprocess.run([bash, str(AUTOPR)], cwd=repo, capture_output=True, text=True, env=shim_env)
    assert r.returncode == 0, f"auto-pr.sh must be fail-safe (exit 0), got {r.returncode}: {r.stderr}"
    assert not marker.exists(), (
        "fast-exit must make NO network call on main — got:\n"
        + marker.read_text(encoding="utf-8")
    )
    after = g("for-each-ref", "--format=%(refname) %(objectname)").stdout
    assert before == after, "fast-exit must not prune/mutate refs on main"


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("git")), reason="needs bash+git")
def test_autopr_does_not_fast_exit_on_a_task_branch(tmp_path):
    """The other side of the guard — the one the main-path tests CANNOT catch. If the fast-exit
    matched too broadly, every task branch would silently stop landing (a worse bug than the
    'Hook cancelled' race it fixes) and every main-path assertion would still pass. On a task
    branch the hook MUST fall through to the landing path (session-git-landing.sh -> gh)."""
    bash, git = shutil.which("bash"), shutil.which("git")
    repo = tmp_path / "r"; repo.mkdir(); (repo / ".claude" / "hooks").mkdir(parents=True)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*a):
        return subprocess.run([git, *a], cwd=repo, capture_output=True, text=True, env=env)

    # A local bare remote: `land` pushes before it ever touches gh, so without an origin the test
    # would pass for the WRONG reason (bailing at push, never proving the guard let it through).
    bare = tmp_path / "origin.git"
    subprocess.run([git, "init", "-q", "--bare", str(bare)], capture_output=True, env=env)

    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.test"); g("config", "user.name", "t")
    g("remote", "add", "origin", str(bare))
    (repo / "a.txt").write_text("x", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "i")
    g("push", "-q", "-u", "origin", "main")
    g("checkout", "-q", "-b", "task/some-work")
    (repo / "b.txt").write_text("y", encoding="utf-8"); g("add", "-A"); g("commit", "-qm", "w")

    # The hook resolves the landing lib as $(git rev-parse --show-toplevel)/.claude/hooks/, so the
    # REAL session-git-landing.sh must sit at that path inside the fixture repo.
    shutil.copy(
        AUTOPR.parent / "session-git-landing.sh", repo / ".claude" / "hooks" / "session-git-landing.sh"
    )

    calls = tmp_path / "gh-calls"
    shim = tmp_path / "shim"; shim.mkdir()
    (shim / "gh").write_text(
        "#!/usr/bin/env bash\n" f'echo "gh $*" >> "{calls.as_posix()}"\nexit 0\n', encoding="utf-8"
    )
    (shim / "gh").chmod(0o755)
    shim_env = dict(env, PATH=f"{shim}{os.pathsep}{os.environ['PATH']}", AUTO_MERGE="0")

    r = subprocess.run([bash, str(AUTOPR)], cwd=repo, capture_output=True, text=True, env=shim_env)
    assert r.returncode == 0, f"auto-pr.sh must be fail-safe (exit 0), got {r.returncode}: {r.stderr}"
    log_body = (repo / ".claude" / ".auto-git.log").read_text(encoding="utf-8")
    assert "fast-exit" not in log_body, (
        "auto-pr.sh must NOT fast-exit on a task branch — the guard is too broad:\n" + log_body
    )
    assert calls.exists(), (
        "auto-pr.sh on a task branch must reach the landing path (gh) — it never called gh.\n"
        f"log:\n{log_body}"
    )
