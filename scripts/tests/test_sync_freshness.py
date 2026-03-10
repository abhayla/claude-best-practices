"""Tests for sync and freshness scripts."""

import json
from pathlib import Path
from datetime import datetime, timedelta

import pytest
import yaml

from scripts.sync_to_local import (
    load_sync_config,
    compare_versions,
    find_updated_patterns,
)
from scripts.sync_to_projects import (
    load_repos_config,
    build_sync_diff,
    check_existing_pr,
)
from scripts.check_freshness import (
    load_url_config,
    check_all_sources,
    format_report,
)


class TestSyncToLocal:
    def test_load_sync_config_missing(self, tmp_path):
        assert load_sync_config(tmp_path) is None

    def test_load_sync_config_exists(self, tmp_path):
        claude = tmp_path / ".claude"
        claude.mkdir()
        (claude / "sync-config.yml").write_text(yaml.dump({"hub_repo": "test/repo"}))
        config = load_sync_config(tmp_path)
        assert config["hub_repo"] == "test/repo"

    def test_compare_versions_newer(self):
        assert compare_versions("2.0.0", "1.0.0") == 1

    def test_compare_versions_same(self):
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_compare_versions_older(self):
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_find_updated_patterns_empty_registry(self, tmp_path):
        registry = {"_meta": {"version": "1.0.0"}}
        updates = find_updated_patterns(registry, tmp_path)
        assert len(updates) == 0

    def test_find_updated_patterns_new_pattern(self, tmp_path):
        registry = {
            "_meta": {"version": "1.0.0"},
            "test-skill": {"hash": "abc123", "type": "skill", "version": "1.0.0"},
        }
        updates = find_updated_patterns(registry, tmp_path)
        assert len(updates) == 1
        assert updates[0]["name"] == "test-skill"
        assert updates[0]["local_exists"] is False


class TestSyncToProjects:
    def test_load_repos_config_missing(self, tmp_path):
        repos = load_repos_config(tmp_path / "nonexistent.yml")
        assert repos == []

    def test_load_repos_config_valid(self, tmp_path):
        config = tmp_path / "repos.yml"
        config.write_text(yaml.dump({"repos": [{"repo": "owner/repo"}]}))
        repos = load_repos_config(config)
        assert len(repos) == 1
        assert repos[0]["repo"] == "owner/repo"

    def test_build_sync_diff_filters_stacks(self):
        registry = {
            "_meta": {},
            "core-skill": {"type": "skill", "category": "core", "version": "1.0.0"},
            "android-skill": {"type": "skill", "category": "stack:android-compose", "version": "1.0.0"},
            "react-skill": {"type": "skill", "category": "stack:react-nextjs", "version": "1.0.0"},
        }
        remote_config = {"selected_stacks": ["android-compose"]}
        diff = build_sync_diff(registry, remote_config)
        names = [d["name"] for d in diff]
        assert "core-skill" in names
        assert "android-skill" in names
        assert "react-skill" not in names


class TestCheckFreshness:
    def test_load_url_config_missing(self, tmp_path):
        urls = load_url_config(tmp_path / "nonexistent.yml")
        assert urls == []

    def test_check_all_sources_mixed(self):
        sources = [
            {"url": "a.com", "last_verified": datetime.now().isoformat()[:10], "expires_after": "90d"},
            {"url": "b.com", "last_verified": (datetime.now() - timedelta(days=100)).isoformat()[:10], "expires_after": "90d"},
        ]
        report = check_all_sources(sources)
        assert report["total"] == 2
        assert report["fresh"] == 1
        assert report["expired"] == 1

    def test_format_report_includes_expired(self):
        report = {
            "total": 2, "fresh": 1, "expired": 1,
            "expired_sources": [{"url": "b.com", "last_verified": "2025-01-01", "expires_after": "30d"}],
        }
        text = format_report(report)
        assert "b.com" in text
        assert "Expired" in text
