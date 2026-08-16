"""Behavior tests for scripts/sync_to_projects.py (hub -> downstream project repos).

Covers the pure diff/manifest logic directly against tmp-path fixtures, and the
subprocess-backed gh calls via monkeypatched subprocess.run (real function bodies run,
only the external `gh` process boundary is stubbed — this is the repo's existing
convention for testing subprocess-wrapping functions, e.g. test_collate.py).
"""

import json
import subprocess

import pytest
import yaml

from scripts.sync_to_projects import (
    build_pr_body,
    build_sync_diff,
    check_existing_pr,
    create_sync_pr,
    generate_provision_manifest,
    get_repo_sync_config,
    load_repos_config,
    pattern_matches_stacks,
    scan_remote_adoption,
)


# ── load_repos_config: real file I/O against tmp_path ───────────────────────

class TestLoadReposConfig:
    def test_happy_path_reads_repo_list(self, tmp_path):
        cfg = tmp_path / "repos.yml"
        cfg.write_text(
            yaml.dump({"repos": [{"repo": "abhayla/foo"}, {"repo": "abhayla/bar"}]}),
            encoding="utf-8",
        )
        repos = load_repos_config(cfg)
        assert [r["repo"] for r in repos] == ["abhayla/foo", "abhayla/bar"]

    def test_missing_file_returns_empty_list(self, tmp_path):
        assert load_repos_config(tmp_path / "does-not-exist.yml") == []

    def test_missing_repos_key_returns_empty_list(self, tmp_path):
        cfg = tmp_path / "repos.yml"
        cfg.write_text(yaml.dump({"other": []}), encoding="utf-8")
        assert load_repos_config(cfg) == []


# ── pattern_matches_stacks: pure filtering logic ─────────────────────────────

class TestPatternMatchesStacks:
    def test_core_pattern_always_matches(self):
        assert pattern_matches_stacks("fix-loop", [], "core") is True
        assert pattern_matches_stacks("fix-loop", ["fastapi-python"], "core") is True

    def test_stack_specific_pattern_matches_selected_stack(self):
        assert pattern_matches_stacks("fastapi-db-migrate", ["fastapi-python"], "core") is True

    def test_stack_specific_pattern_excluded_when_not_selected(self):
        assert pattern_matches_stacks("fastapi-db-migrate", ["android-compose"], "core") is False

    def test_stack_specific_pattern_excluded_with_no_stacks_selected(self):
        assert pattern_matches_stacks("android-compose-helper", [], "core") is False


# ── build_sync_diff: filters a registry-shaped dict by selected stacks ──────

class TestBuildSyncDiff:
    def test_filters_by_selected_stacks_and_skips_meta(self):
        hub_registry = {
            "_meta": {"version": "1.0.0"},
            "fix-loop": {"type": "skill", "version": "1.2.0", "category": "core"},
            "fastapi-db-migrate": {"type": "skill", "version": "1.0.0", "category": "core"},
            "android-compose-helper": {"type": "skill", "version": "1.0.0", "category": "core"},
        }
        remote_config = {"selected_stacks": ["fastapi-python"]}
        updates = build_sync_diff(hub_registry, remote_config)
        names = {u["name"] for u in updates}
        assert names == {"fix-loop", "fastapi-db-migrate"}
        assert "android-compose-helper" not in names
        assert "_meta" not in names

    def test_carries_contributed_by_attribution(self):
        hub_registry = {"fix-loop": {"type": "skill", "version": "1.0.0", "contributed_by": ["projA"]}}
        updates = build_sync_diff(hub_registry, {"selected_stacks": []})
        assert updates[0]["contributed_by"] == ["projA"]


# ── build_pr_body: text generation — real behavior, asserted against content ─

class TestBuildPrBody:
    def test_groups_by_type_and_counts(self):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.2.0"},
            {"name": "debugger", "type": "agent", "version": "1.0.0"},
        ]
        body = build_pr_body(updates, "abhayla/foo")
        assert "Syncing 2 patterns from the hub to `abhayla/foo`." in body
        assert "### Skills (1)" in body
        assert "### Agents (1)" in body
        assert "**fix-loop** v1.2.0" in body

    def test_attribution_section_only_when_contributed(self):
        no_attr = build_pr_body([{"name": "x", "type": "skill", "version": "1.0.0"}], "r")
        assert "Attribution" not in no_attr

        with_attr = build_pr_body(
            [{"name": "x", "type": "skill", "version": "1.0.0", "contributed_by": ["projA", "projB"]}], "r"
        )
        assert "### Attribution" in with_attr
        assert "contributed by: projA, projB" in with_attr


# ── generate_provision_manifest: pure, checked structurally (not exact time) ─

class TestGenerateProvisionManifest:
    def test_builds_files_dict_with_correct_relative_paths(self):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.2.0"},
            {"name": "debugger", "type": "agent", "version": "1.0.0"},
            {"name": "workflow", "type": "rule", "version": "1.0.0"},
        ]
        manifest = generate_provision_manifest(updates)
        files = manifest["files"]
        assert set(files.keys()) == {
            "skills/fix-loop/SKILL.md",
            "agents/debugger.md",
            "rules/workflow.md",
        }
        assert files["skills/fix-loop/SKILL.md"]["version"] == "1.2.0"
        assert manifest["_meta"]["hub_repo"] == "abhayla/claude-best-practices"

    def test_missing_version_defaults(self):
        manifest = generate_provision_manifest([{"name": "x", "type": "rule"}])
        assert manifest["files"]["rules/x.md"]["version"] == "0.0.0"


# ── scan_remote_adoption: the Windows-vs-Unix path-separator case lives here ─

class TestScanRemoteAdoption:
    def test_happy_path_adopted(self):
        manifest = {"files": {"skills/fix-loop/SKILL.md": {"provisioned_date": "2026-01-01"}}}
        remote_files = [".claude/skills/fix-loop/SKILL.md"]
        result = scan_remote_adoption(manifest, remote_files)
        assert result["fix-loop"]["status"] == "adopted"
        assert result["fix-loop"]["retention_days"] >= 0

    def test_drift_case_deleted_when_missing_from_remote(self):
        manifest = {"files": {"skills/fix-loop/SKILL.md": {"provisioned_date": "2026-01-01"}}}
        result = scan_remote_adoption(manifest, [])
        assert result["fix-loop"]["status"] == "deleted"

    def test_windows_backslash_remote_paths_still_match(self):
        """A Windows-style file listing (backslash separators) must normalize to match the
        forward-slash manifest keys — otherwise every pattern on a Windows-produced listing
        would be misreported as deleted."""
        manifest = {"files": {"agents/debugger.md": {"provisioned_date": "2026-01-01"}}}
        remote_files_windows = [".claude\\agents\\debugger.md"]
        result = scan_remote_adoption(manifest, remote_files_windows)
        assert result["debugger"]["status"] == "adopted"

    def test_agent_and_rule_suffix_stripped_from_pattern_name(self):
        manifest = {
            "files": {
                "agents/debugger.md": {"provisioned_date": "2026-01-01"},
                "rules/workflow.md": {"provisioned_date": "2026-01-01"},
            }
        }
        result = scan_remote_adoption(manifest, [".claude/agents/debugger.md", ".claude/rules/workflow.md"])
        assert "debugger" in result and "debugger.md" not in result
        assert "workflow" in result and "workflow.md" not in result

    def test_empty_manifest_files_returns_empty(self):
        assert scan_remote_adoption({"files": {}}, ["anything"]) == {}

    def test_malformed_provisioned_date_yields_zero_retention(self):
        manifest = {"files": {"rules/x.md": {"provisioned_date": "not-a-date"}}}
        result = scan_remote_adoption(manifest, [".claude/rules/x.md"])
        assert result["x"]["retention_days"] == 0


# ── gh-subprocess-backed functions: monkeypatch the process boundary only ───

class TestGetRepoSyncConfig:
    def test_happy_path_parses_yaml_from_gh(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            assert cmd[0] == "gh"
            return subprocess.CompletedProcess(cmd, 0, stdout=yaml.dump({"selected_stacks": ["fastapi-python"]}))
        monkeypatch.setattr(subprocess, "run", fake_run)
        cfg = get_repo_sync_config("abhayla/foo")
        assert cfg == {"selected_stacks": ["fastapi-python"]}

    def test_gh_failure_returns_none(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, stdout="")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert get_repo_sync_config("abhayla/foo") is None

    def test_gh_raises_returns_none(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 30)
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert get_repo_sync_config("abhayla/foo") is None


class TestCheckExistingPr:
    def test_happy_path_true_when_pr_exists(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps([{"number": 42}]))
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert check_existing_pr("abhayla/foo", "sync-branch") is True

    def test_no_open_pr_returns_false(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps([]))
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert check_existing_pr("abhayla/foo", "sync-branch") is False

    def test_gh_failure_returns_false(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, stdout="")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert check_existing_pr("abhayla/foo", "sync-branch") is False


class TestCreateSyncPr:
    def test_happy_path_returns_pr_url(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout="https://github.com/abhayla/foo/pull/9\n")
        monkeypatch.setattr(subprocess, "run", fake_run)
        url = create_sync_pr("abhayla/foo", "sync-branch", [{"name": "x", "type": "skill"}])
        assert url == "https://github.com/abhayla/foo/pull/9"

    def test_gh_failure_returns_none(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, stdout="")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert create_sync_pr("abhayla/foo", "sync-branch", []) is None
