"""Tests for the advisory eval-coverage touch-trigger gate (check_eval_coverage.py)."""

import subprocess
import sys
from pathlib import Path

from scripts.check_eval_coverage import uncovered_changed_skills

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_flags_changed_skill_without_evals(tmp_path):
    skill_dir = tmp_path / "core" / ".claude" / "skills" / "no-evals-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: no-evals-skill\n---\n", encoding="utf-8")

    changed = ["core/.claude/skills/no-evals-skill/SKILL.md"]
    result = uncovered_changed_skills(changed, tmp_path)

    assert len(result) == 1
    assert result[0]["skill"] == "no-evals-skill"
    assert result[0]["skill_md"] == "core/.claude/skills/no-evals-skill/SKILL.md"


def test_flags_changed_skill_with_empty_evals_dir(tmp_path):
    skill_dir = tmp_path / "core" / ".claude" / "skills" / "empty-evals-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: empty-evals-skill\n---\n", encoding="utf-8")
    (skill_dir / "evals").mkdir()

    changed = ["core/.claude/skills/empty-evals-skill/SKILL.md"]
    result = uncovered_changed_skills(changed, tmp_path)

    assert len(result) == 1
    assert result[0]["skill"] == "empty-evals-skill"


def test_does_not_flag_covered_skill_real_repo():
    covered_skills = ["fix-loop", "auto-verify", "learn-n-improve", "loop-engineering"]
    changed = [f"core/.claude/skills/{name}/SKILL.md" for name in covered_skills]

    result = uncovered_changed_skills(changed, REPO_ROOT)

    flagged = {item["skill"] for item in result}
    for name in covered_skills:
        assert name not in flagged, f"{name} has evals but was flagged as uncovered"


def test_ignores_non_skill_md_paths(tmp_path):
    (tmp_path / "core" / ".claude" / "skills" / "some-skill").mkdir(parents=True)
    changed = [
        "core/.claude/skills/some-skill/references/notes.md",
        "scripts/dedup_check.py",
        "README.md",
    ]
    result = uncovered_changed_skills(changed, tmp_path)
    assert result == []


def test_does_not_flag_covered_skill_synthetic(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "covered-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: covered-skill\n---\n", encoding="utf-8")
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "2026-01-01-full-eval.md").write_text("# eval\n", encoding="utf-8")

    changed = [".claude/skills/covered-skill/SKILL.md"]
    result = uncovered_changed_skills(changed, tmp_path)
    assert result == []


def test_cli_exits_zero_with_no_base_diff():
    proc = subprocess.run(
        [sys.executable, "scripts/check_eval_coverage.py", "--base", "origin/does-not-exist-branch"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0


def test_cli_exits_zero_against_real_base():
    proc = subprocess.run(
        [sys.executable, "scripts/check_eval_coverage.py", "--base", "HEAD~1"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
