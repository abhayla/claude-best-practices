"""Tests for scripts/check_standing_goals.py — the standing-goal invariant sentinel."""

import json
from pathlib import Path

import pytest

from scripts.check_standing_goals import (
    _split_frontmatter,
    check_all_goals,
    format_report,
    load_goal_files,
    main,
    update_timestamps,
    validate_frontmatter,
)

REPO_ROOT = Path(__file__).parent.parent.parent


def _write_goal(goals_dir: Path, name: str, frontmatter: str, body: str = "Body text.\n") -> Path:
    path = goals_dir / f"{name}.md"
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return path


class TestValidGoalFile:
    def test_passing_goal_with_file_and_command_predicates(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        target = tmp_path / "exists.txt"
        target.write_text("x", encoding="utf-8")
        _write_goal(
            goals_dir, "sample",
            f'name: sample\n'
            f'description: "a sample invariant"\n'
            f'enrolled: "2026-07-10"\n'
            f'source: "test"\n'
            f'last_verified: "2026-07-10"\n'
            f'predicates:\n'
            f'  - kind: file\n'
            f'    path: "{target.relative_to(tmp_path).as_posix()}"\n'
            f'  - kind: command\n'
            f'    cmd: "exit 0"\n'
            f'on_failure: "check it"\n',
        )
        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        assert report["total"] == 1
        assert report["passing"] == 1
        assert report["failing"] == 0
        assert report["goals"][0]["name"] == "sample"


class TestFailingPredicates:
    def test_failing_file_predicate_reports_goal_and_hint(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        _write_goal(
            goals_dir, "missing-file",
            'name: missing-file\n'
            'description: "an invariant with a missing file"\n'
            'enrolled: "2026-07-10"\n'
            'source: "test"\n'
            'last_verified: "2026-07-10"\n'
            'predicates:\n'
            '  - kind: file\n'
            '    path: "does/not/exist.txt"\n'
            'on_failure: "re-create the file"\n',
        )
        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        assert report["failing"] == 1
        text = format_report(report)
        assert "missing-file" in text
        assert "re-create the file" in text
        assert "does/not/exist.txt" in text

    def test_failing_command_predicate_reports_reason(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        _write_goal(
            goals_dir, "bad-command",
            'name: bad-command\n'
            'description: "an invariant whose command fails"\n'
            'enrolled: "2026-07-10"\n'
            'source: "test"\n'
            'last_verified: "2026-07-10"\n'
            'predicates:\n'
            '  - kind: command\n'
            '    cmd: "exit 1"\n'
            'on_failure: "investigate"\n',
        )
        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        assert report["failing"] == 1
        goal = report["goals"][0]
        assert goal["passed"] is False
        assert "command failed" in goal["predicates"][0]["reason"]

    def test_command_timeout_is_a_failure(self, tmp_path, monkeypatch):
        import subprocess

        from scripts import check_standing_goals as mod

        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="sleep 999", timeout=60)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        _write_goal(
            goals_dir, "slow",
            'name: slow\n'
            'description: "an invariant whose command times out"\n'
            'enrolled: "2026-07-10"\n'
            'last_verified: "2026-07-10"\n'
            'predicates:\n'
            '  - kind: command\n'
            '    cmd: "sleep 999"\n',
        )
        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        assert report["failing"] == 1
        assert "timed out" in report["goals"][0]["predicates"][0]["reason"]


class TestMalformedGoal:
    def test_malformed_goal_is_flagged_never_skipped(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()

        (goals_dir / "no-frontmatter.md").write_text("just a body, no frontmatter\n", encoding="utf-8")
        _write_goal(goals_dir, "no-predicates", 'name: no-predicates\ndescription: "x"\n')
        _write_goal(
            goals_dir, "bad-kind",
            'name: bad-kind\ndescription: "x"\npredicates:\n  - kind: network\n    url: "http://x"\n',
        )
        _write_goal(goals_dir, "empty-predicates", 'name: empty-predicates\ndescription: "x"\npredicates: []\n')

        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)

        assert report["total"] == 4
        assert report["passing"] == 0
        assert report["failing"] == 4
        for goal in report["goals"]:
            assert goal["malformed"] is True
            assert goal["error"]

        text = format_report(report)
        for slug in ("no-frontmatter", "no-predicates", "bad-kind", "empty-predicates"):
            assert slug in text or "MALFORMED" in text


class TestReadmeSkipped:
    def test_readme_is_not_treated_as_a_goal(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        (goals_dir / "README.md").write_text("# goals\nNot a goal file.\n", encoding="utf-8")
        _write_goal(
            goals_dir, "real-goal",
            'name: real-goal\ndescription: "x"\npredicates:\n  - kind: command\n    cmd: "exit 0"\n',
        )
        files = load_goal_files(goals_dir)
        assert len(files) == 1
        assert files[0].name == "real-goal.md"


class TestJsonOutput:
    def test_json_shape(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        _write_goal(
            goals_dir, "sample",
            'name: sample\ndescription: "x"\npredicates:\n  - kind: command\n    cmd: "exit 0"\n',
        )
        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        serialized = json.dumps(report, default=str)
        parsed = json.loads(serialized)
        assert parsed["total"] == 1
        assert parsed["passing"] == 1
        assert "goals" in parsed


class TestUpdateTimestamps:
    def test_updates_only_passing_goals_preserves_rest_of_file(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        passing_path = _write_goal(
            goals_dir, "passing",
            'name: passing\n'
            'description: "x"\n'
            'enrolled: "2026-01-01"\n'
            'last_verified: "2020-01-01"\n'
            'predicates:\n'
            '  - kind: command\n'
            '    cmd: "exit 0"\n'
            'on_failure: "hint"\n',
            body="Body text describing the goal.\n",
        )
        failing_path = _write_goal(
            goals_dir, "failing",
            'name: failing\n'
            'description: "x"\n'
            'last_verified: "2020-01-01"\n'
            'predicates:\n'
            '  - kind: command\n'
            '    cmd: "exit 1"\n',
        )

        passing_before = passing_path.read_bytes()
        failing_before = failing_path.read_bytes()

        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        update_timestamps(report, today="2026-07-10")

        # BYTE-exact assertion: the passing file may differ from its original bytes
        # ONLY in the single last_verified line — any EOL rewrite fails this.
        passing_after = passing_path.read_bytes()
        expected = passing_before.replace(
            b'last_verified: "2020-01-01"', b'last_verified: "2026-07-10"', 1
        )
        assert passing_after == expected

        # Failing goal: NOT a single byte changed.
        assert failing_path.read_bytes() == failing_before

    def test_crlf_file_stays_crlf_and_only_one_line_changes(self, tmp_path):
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        path = goals_dir / "crlf-goal.md"
        content = (
            '---\r\n'
            'name: crlf-goal\r\n'
            'description: "a goal saved with CRLF line endings"\r\n'
            'last_verified: "2020-01-01"\r\n'
            'predicates:\r\n'
            '  - kind: command\r\n'
            '    cmd: "exit 0"\r\n'
            '---\r\n'
            'Body line.\r\n'
        )
        path.write_bytes(content.encode("utf-8"))
        before = path.read_bytes()

        report = check_all_goals(goals_dir=goals_dir, repo_root=tmp_path)
        update_timestamps(report, today="2026-07-10")

        after = path.read_bytes()
        expected = before.replace(
            b'last_verified: "2020-01-01"', b'last_verified: "2026-07-10"', 1
        )
        assert after == expected  # CRLF preserved everywhere; only the one line changed
        assert b'last_verified: "2026-07-10"\r\n' in after


class TestPlantedDeadInvariant:
    def test_planted_dead_invariant_is_caught(self, tmp_path, monkeypatch, capsys):
        """A goal that passes today must be CAUGHT once its underlying file disappears —
        the whole point of the sentinel (a goal verified once is an assumption with a
        timestamp; this proves re-verification actually detects the silent death)."""
        from scripts import check_standing_goals as mod

        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        target = tmp_path / "deployed-artifact.txt"
        target.write_text("present", encoding="utf-8")
        _write_goal(
            goals_dir, "planted-invariant",
            'name: planted-invariant\n'
            'description: "the deployed artifact keeps existing"\n'
            'last_verified: "2026-07-10"\n'
            'predicates:\n'
            '  - kind: file\n'
            '    path: "deployed-artifact.txt"\n'
            'on_failure: "redeploy the artifact"\n',
        )
        monkeypatch.setattr(mod, "GOALS_DIR", goals_dir)
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

        assert main([]) == 0  # passes while the file exists

        target.unlink()  # simulate silent death

        exit_code = main([])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "planted-invariant" in captured.out


class TestRealSeedGoals:
    """The 3 real seed goals in goals/ must be STRUCTURALLY valid (parse, well-formed
    frontmatter, non-empty predicates).

    Deliberately does NOT execute the live predicates: pass/fail verification belongs to
    the daily standing-goals.yml sentinel, never PR CI (cron-only by design — an
    anticipatory or environment-dependent goal must not block PRs). Enrolled predicates
    should stay hermetic (no network, no gh, no environment dependence) or be understood
    as cron-only signals — see goals/README.md.
    """

    @pytest.mark.parametrize("slug", [
        "trust-recorder-sweep",
        "fable-operating-manual-plugin",
        "plugins-marketplace-integrity",
    ])
    def test_seed_goal_is_structurally_valid(self, slug):
        path = REPO_ROOT / "goals" / f"{slug}.md"
        assert path.exists(), f"seed goal file missing: {path}"
        fm, _raw = _split_frontmatter(path.read_text(encoding="utf-8"))
        error = validate_frontmatter(fm)
        assert error is None, f"{slug}: {error}"
        assert fm["name"] == slug
        assert len(fm["predicates"]) >= 1
