"""T-370 dod item 4: eval-coverage FRESHNESS check (check_eval_coverage.py).

Existence-is-not-freshness (review H7): a changed SKILL.md that already has an
evals/ report is still stale if the skill's own last commit is newer than every
eval file's last commit. Uses a tmp git repo fixture (real commits, real
`git log`) so the red-then-green proof is against the actual mechanism, not a
mock.
"""
import subprocess
import time
from pathlib import Path

import scripts.check_eval_coverage as cec

# git commit timestamps are second-resolution; separate commits whose order matters
# for the freshness comparison need a >= 1s gap so they don't tie.
_TICK = 1.1


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    return repo


def _write_and_commit(repo: Path, rel_path: str, content: str, message: str):
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    # -f: this machine's global gitignore excludes .claude/ (repo convention:
    # new .claude/ resources need `git add -f`, see CLAUDE.md).
    _git(["add", "-f", rel_path], repo)
    _git(["commit", "-q", "-m", message], repo)


def test_skill_md_committed_after_its_eval_is_flagged_stale(tmp_path):
    repo = _init_repo(tmp_path)
    skill_md = ".claude/skills/demo/SKILL.md"
    eval_md = ".claude/skills/demo/evals/2026-01-01-report.md"

    _write_and_commit(repo, skill_md, "---\nname: demo\n---\nv1\n", "add skill v1")
    time.sleep(_TICK)
    _write_and_commit(repo, eval_md, "# eval report\n", "add eval report")
    time.sleep(_TICK)
    # SKILL.md changes AGAIN after the eval was written — now stale.
    _write_and_commit(repo, skill_md, "---\nname: demo\n---\nv2\n", "change skill behavior")

    result = cec.stale_changed_skills([skill_md], repo)

    assert len(result) == 1
    assert result[0]["skill"] == "demo"
    assert result[0]["skill_md"] == skill_md


def test_skill_md_committed_before_its_eval_is_not_stale(tmp_path):
    repo = _init_repo(tmp_path)
    skill_md = ".claude/skills/demo/SKILL.md"
    eval_md = ".claude/skills/demo/evals/2026-01-01-report.md"

    _write_and_commit(repo, skill_md, "---\nname: demo\n---\nv1\n", "add skill v1")
    time.sleep(_TICK)
    _write_and_commit(repo, eval_md, "# eval report\n", "add eval report AFTER skill")

    result = cec.stale_changed_skills([skill_md], repo)

    assert result == []


def test_skill_with_no_evals_at_all_is_not_flagged_stale():
    """No evals -> that's the EXISTENCE gate's job (uncovered_changed_skills), not freshness."""
    repo_placeholder = Path(__file__).resolve().parent  # any real dir with no evals dir here
    skill_md = "does-not-exist/SKILL.md"
    result = cec.stale_changed_skills([skill_md], repo_placeholder)
    assert result == []


def test_cli_enforce_fails_on_stale_non_grandfathered_skill(tmp_path):
    repo = _init_repo(tmp_path)
    skill_md_rel = ".claude/skills/demo/SKILL.md"
    eval_md_rel = ".claude/skills/demo/evals/2026-01-01-report.md"

    _write_and_commit(repo, skill_md_rel, "---\nname: demo\n---\nv1\n", "add skill v1")
    _write_and_commit(repo, eval_md_rel, "# eval report\n", "add eval report")
    _write_and_commit(repo, "config/eval-coverage-grandfather.yml", "grandfathered:\n  - some-other-skill\n", "seed grandfather")
    _git(["branch", "base-branch"], repo)
    _git(["checkout", "-q", "-b", "feature-branch"], repo)
    time.sleep(_TICK)
    _write_and_commit(repo, skill_md_rel, "---\nname: demo\n---\nv2\n", "change skill behavior")

    # Run the REAL script from inside the tmp repo (root = Path(__file__).parent.parent,
    # so it must live under <repo>/scripts/ to resolve config/ against the tmp repo).
    import shutil
    (repo / "scripts").mkdir(exist_ok=True)
    shutil.copy(cec.__file__, repo / "scripts" / "check_eval_coverage.py")

    proc = subprocess.run(
        ["python", "scripts/check_eval_coverage.py", "--base", "base-branch", "--enforce"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "stale" in (proc.stdout + proc.stderr).lower()


def test_full_local_ci_existing_eval_coverage_tests_still_pass():
    """Non-regression check named in the T-370 contract: the pre-existing
    check_eval_coverage tests must stay green after adding the freshness check."""
    proc = subprocess.run(
        ["python", "-m", "pytest", "scripts/tests/test_check_eval_coverage.py", "-q"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
