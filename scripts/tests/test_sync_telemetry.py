"""Tests for sync_to_projects.py telemetry integration.

Tests the adoption scanning extension to sync_to_projects.py that
produces telemetry signals during the existing weekly sync cycle.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.sync_to_projects import (
    generate_provision_manifest,
    scan_remote_adoption,
    build_sync_diff,
    pattern_matches_stacks,
)


# --- Fixtures ---


@pytest.fixture
def sample_hub_registry():
    """Minimal registry for sync diff tests."""
    return {
        "_meta": {"version": "3.0.0", "total_patterns": 3},
        "fix-loop": {
            "type": "skill",
            "category": "core",
            "version": "1.2.0",
        },
        "security-audit": {
            "type": "skill",
            "category": "core",
            "version": "1.0.0",
        },
        "fastapi-backend": {
            "type": "rule",
            "category": "core",
            "version": "1.0.0",
        },
    }


# --- Tests: generate_provision_manifest ---


class TestGenerateProvisionManifest:
    """Test manifest generation during pattern sync."""

    def test_creates_manifest_from_sync_diff(self, sample_hub_registry):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.2.0", "category": "core"},
            {"name": "security-audit", "type": "skill", "version": "1.0.0", "category": "core"},
        ]
        manifest = generate_provision_manifest(updates)

        assert "files" in manifest
        assert "skills/fix-loop/SKILL.md" in manifest["files"]
        assert "skills/security-audit/SKILL.md" in manifest["files"]

    def test_manifest_includes_provisioned_date(self, sample_hub_registry):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.2.0", "category": "core"},
        ]
        manifest = generate_provision_manifest(updates)
        entry = manifest["files"]["skills/fix-loop/SKILL.md"]
        assert "provisioned_date" in entry
        # Should be today's date
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert entry["provisioned_date"] == today

    def test_manifest_includes_version(self, sample_hub_registry):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.2.0", "category": "core"},
        ]
        manifest = generate_provision_manifest(updates)
        entry = manifest["files"]["skills/fix-loop/SKILL.md"]
        assert entry["version"] == "1.2.0"

    def test_manifest_handles_different_types(self):
        updates = [
            {"name": "fix-loop", "type": "skill", "version": "1.0.0", "category": "core"},
            {"name": "code-reviewer-agent", "type": "agent", "version": "1.0.0", "category": "core"},
            {"name": "workflow", "type": "rule", "version": "1.0.0", "category": "core"},
        ]
        manifest = generate_provision_manifest(updates)
        assert "skills/fix-loop/SKILL.md" in manifest["files"]
        assert "agents/code-reviewer-agent.md" in manifest["files"]
        assert "rules/workflow.md" in manifest["files"]

    def test_manifest_has_meta_section(self):
        updates = [{"name": "tdd", "type": "skill", "version": "1.0.0", "category": "core"}]
        manifest = generate_provision_manifest(updates)
        assert "_meta" in manifest
        assert manifest["_meta"]["version"] == "1.0.0"
        assert "hub_repo" in manifest["_meta"]

    def test_empty_updates_produces_empty_files(self):
        manifest = generate_provision_manifest([])
        assert manifest["files"] == {}


# --- Tests: scan_remote_adoption ---


class TestScanRemoteAdoption:
    """Test computing adoption signals from a remote project's file listing."""

    def test_all_adopted(self):
        """All provisioned patterns exist in remote file listing."""
        manifest = {
            "files": {
                "skills/fix-loop/SKILL.md": {"provisioned_date": "2026-03-01"},
                "skills/tdd/SKILL.md": {"provisioned_date": "2026-03-01"},
            }
        }
        remote_files = [
            ".claude/skills/fix-loop/SKILL.md",
            ".claude/skills/tdd/SKILL.md",
        ]
        result = scan_remote_adoption(manifest, remote_files)
        assert result["fix-loop"]["status"] == "adopted"
        assert result["tdd"]["status"] == "adopted"

    def test_some_deleted(self):
        """Some provisioned patterns no longer exist remotely."""
        manifest = {
            "files": {
                "skills/fix-loop/SKILL.md": {"provisioned_date": "2026-03-01"},
                "skills/security-audit/SKILL.md": {"provisioned_date": "2026-03-01"},
            }
        }
        remote_files = [
            ".claude/skills/fix-loop/SKILL.md",
            # security-audit is missing
        ]
        result = scan_remote_adoption(manifest, remote_files)
        assert result["fix-loop"]["status"] == "adopted"
        assert result["security-audit"]["status"] == "deleted"

    def test_computes_retention_days(self):
        manifest = {
            "files": {
                "skills/fix-loop/SKILL.md": {"provisioned_date": "2026-03-01"},
            }
        }
        remote_files = [".claude/skills/fix-loop/SKILL.md"]
        result = scan_remote_adoption(manifest, remote_files)
        assert result["fix-loop"]["retention_days"] >= 0

    def test_empty_manifest(self):
        result = scan_remote_adoption({"files": {}}, [])
        assert result == {}

    def test_handles_agents_and_rules(self):
        manifest = {
            "files": {
                "agents/code-reviewer-agent.md": {"provisioned_date": "2026-03-01"},
                "rules/workflow.md": {"provisioned_date": "2026-03-01"},
            }
        }
        remote_files = [
            ".claude/agents/code-reviewer-agent.md",
            # rules/workflow.md is missing
        ]
        result = scan_remote_adoption(manifest, remote_files)
        assert result["code-reviewer-agent"]["status"] == "adopted"
        assert result["workflow"]["status"] == "deleted"
