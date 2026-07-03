"""Tests for the honest per-task trust-score accrual recorder (#196).

Uses tmp git repos + tmp ledgers/markers throughout — NEVER touches the real
trust-score/ledgers/atlas.jsonl or trust-score/.recorded-branches.
"""

import subprocess

import pytest

from scripts.record_task_run import (
    already_recorded,
    derive_human_had_to_fix,
    mark_recorded,
    record_task_run,
)


def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_main(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _run(["git", "add", "README.md"], repo)
    _run(["git", "commit", "-m", "initial commit"], repo)
    return repo


class TestDeriveHumanHadToFix:
    def test_single_clean_commit_is_false(self, tmp_path):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/one"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "add feature"], repo)

        assert derive_human_had_to_fix(cwd=repo) is False

    def test_second_commit_is_true(self, tmp_path):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/two"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "add feature"], repo)
        (repo / "a.txt").write_text("a2\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "tweak"], repo)

        assert derive_human_had_to_fix(cwd=repo) is True

    def test_fix_subject_on_single_commit_is_true(self, tmp_path):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/three"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "fix: resync hashes"], repo)

        assert derive_human_had_to_fix(cwd=repo) is True

    def test_no_commits_ahead_is_none(self, tmp_path):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/empty"], repo)

        assert derive_human_had_to_fix(cwd=repo) is None

    def test_no_mergeable_base_is_none(self, tmp_path):
        repo = tmp_path / "orphan_repo"
        repo.mkdir()
        _run(["git", "init", "-b", "main"], repo)
        _run(["git", "config", "user.email", "test@example.com"], repo)
        _run(["git", "config", "user.name", "Test"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "only commit, no other branch to diff against"], repo)

        assert derive_human_had_to_fix(cwd=repo) is None


class TestIdempotency:
    def test_marker_roundtrip(self, tmp_path):
        marker = tmp_path / ".recorded-branches"
        assert already_recorded("br-1", marker) is False
        mark_recorded("br-1", marker)
        assert already_recorded("br-1", marker) is True
        assert already_recorded("br-2", marker) is False

    def test_record_task_run_twice_appends_once(self, tmp_path, monkeypatch):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/idempotent"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "add feature"], repo)

        marker = tmp_path / "marker.txt"
        ledger = tmp_path / "atlas.jsonl"

        monkeypatch.setattr("scripts.record_task_run.run_tests", lambda: (5, 5, True))
        monkeypatch.setattr("scripts.record_task_run.run_secret_scan", lambda: 1.0)

        first = record_task_run(cwd=repo, marker_path=marker, ledger_path=ledger)
        second = record_task_run(cwd=repo, marker_path=marker, ledger_path=ledger)

        assert first["status"] == "recorded"
        assert second["status"] == "already_recorded"

        from scripts.trust_score import load_ledger

        assert len(load_ledger(ledger)) == 1


class TestWritesToAtlasNotSim:
    def test_default_ledger_is_atlas_not_sim(self):
        from scripts.collect_signals import default_ledger_for

        ledger = default_ledger_for("atlas")
        assert ledger.name == "atlas.jsonl"
        assert "sim-ledger" not in str(ledger)
        assert ledger.parent.name == "ledgers"

    def test_record_task_run_writes_to_explicit_non_sim_path(self, tmp_path, monkeypatch):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/atlas-only"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "add feature"], repo)

        marker = tmp_path / "marker.txt"
        ledger = tmp_path / "atlas.jsonl"

        monkeypatch.setattr("scripts.record_task_run.run_tests", lambda: (3, 3, True))
        monkeypatch.setattr("scripts.record_task_run.run_secret_scan", lambda: 1.0)

        record_task_run(cwd=repo, marker_path=marker, ledger_path=ledger)

        assert ledger.exists()
        assert "sim-ledger" not in str(ledger)


class TestHonestyInvariants:
    def test_indeterminate_proxy_never_written_as_false(self, tmp_path, monkeypatch):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/indeterminate"], repo)
        # No commits ahead of base -> proxy is None, must stay None end-to-end.

        marker = tmp_path / "marker.txt"
        ledger = tmp_path / "atlas.jsonl"

        monkeypatch.setattr("scripts.record_task_run.run_tests", lambda: (0, 0, False))
        monkeypatch.setattr("scripts.record_task_run.run_secret_scan", lambda: 1.0)

        outcome = record_task_run(cwd=repo, marker_path=marker, ledger_path=ledger)

        assert outcome["human_had_to_fix"] is None

        from scripts.trust_score import load_ledger

        runs = load_ledger(ledger)
        assert runs[0]["human_had_to_fix"] is None

    def test_override_wins_over_proxy(self, tmp_path, monkeypatch):
        repo = _init_repo_with_main(tmp_path)
        _run(["git", "checkout", "-b", "feature/override"], repo)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _run(["git", "add", "a.txt"], repo)
        _run(["git", "commit", "-m", "add feature"], repo)  # proxy would say False

        marker = tmp_path / "marker.txt"
        ledger = tmp_path / "atlas.jsonl"

        monkeypatch.setattr("scripts.record_task_run.run_tests", lambda: (1, 1, True))
        monkeypatch.setattr("scripts.record_task_run.run_secret_scan", lambda: 1.0)

        outcome = record_task_run(
            cwd=repo, marker_path=marker, ledger_path=ledger, human_had_to_fix_override=True
        )
        assert outcome["human_had_to_fix"] is True
