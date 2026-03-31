"""Tests for pattern effectiveness telemetry aggregation."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.aggregate_telemetry import (
    compute_adoption_rate,
    compute_retention_days,
    compute_error_prevention_rate,
    aggregate_project_telemetry,
    scan_project_adoption,
    write_effectiveness_to_registry,
    load_telemetry_aggregates,
    save_telemetry_aggregates,
)


# --- Fixtures ---


@pytest.fixture
def sample_registry_with_patterns(tmp_path):
    """Registry with a few patterns, no effectiveness data yet."""
    registry = {
        "_meta": {"version": "3.0.0", "last_updated": "2026-03-30", "total_patterns": 3},
        "fix-loop": {
            "hash": "abc123",
            "type": "skill",
            "category": "core",
            "version": "1.2.0",
            "tier": "must-have",
            "tags": ["testing", "fix"],
        },
        "security-audit": {
            "hash": "def456",
            "type": "skill",
            "category": "core",
            "version": "1.0.0",
            "tier": "nice-to-have",
            "tags": ["security", "audit"],
        },
        "tdd": {
            "hash": "ghi789",
            "type": "skill",
            "category": "core",
            "version": "1.0.0",
            "tier": "must-have",
            "tags": ["testing", "tdd"],
        },
    }
    path = tmp_path / "registry" / "patterns.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(registry, indent=2))
    return path


@pytest.fixture
def sync_manifest_project_a():
    """Manifest from project A: provisioned fix-loop and security-audit."""
    return {
        "_meta": {
            "version": "1.0.0",
            "hub_repo": "abhayla/claude-best-practices",
            "created": "2026-03-01T00:00:00+00:00",
            "last_sync": "2026-03-15T00:00:00+00:00",
        },
        "files": {
            "skills/fix-loop/SKILL.md": {
                "hub_hash": "sha256:aaa",
                "provisioned_date": "2026-03-01",
            },
            "skills/security-audit/SKILL.md": {
                "hub_hash": "sha256:bbb",
                "provisioned_date": "2026-03-01",
            },
            "skills/tdd/SKILL.md": {
                "hub_hash": "sha256:ccc",
                "provisioned_date": "2026-03-01",
            },
        },
    }


@pytest.fixture
def project_a_claude_dir(tmp_path, sync_manifest_project_a):
    """Project A: kept fix-loop and tdd, deleted security-audit."""
    claude_dir = tmp_path / "project_a" / ".claude"
    claude_dir.mkdir(parents=True)

    # fix-loop still exists
    (claude_dir / "skills" / "fix-loop").mkdir(parents=True)
    (claude_dir / "skills" / "fix-loop" / "SKILL.md").write_text("# fix-loop skill")

    # tdd still exists
    (claude_dir / "skills" / "tdd").mkdir(parents=True)
    (claude_dir / "skills" / "tdd" / "SKILL.md").write_text("# tdd skill")

    # security-audit was deleted (directory does not exist)

    # Write manifest
    manifest_path = claude_dir / "sync-manifest.json"
    manifest_path.write_text(json.dumps(sync_manifest_project_a, indent=2))

    return tmp_path / "project_a"


@pytest.fixture
def project_b_claude_dir(tmp_path):
    """Project B: kept all three patterns."""
    claude_dir = tmp_path / "project_b" / ".claude"
    claude_dir.mkdir(parents=True)

    for skill in ["fix-loop", "security-audit", "tdd"]:
        (claude_dir / "skills" / skill).mkdir(parents=True)
        (claude_dir / "skills" / skill / "SKILL.md").write_text(f"# {skill} skill")

    manifest = {
        "_meta": {
            "version": "1.0.0",
            "hub_repo": "abhayla/claude-best-practices",
            "created": "2026-02-15T00:00:00+00:00",
            "last_sync": "2026-03-10T00:00:00+00:00",
        },
        "files": {
            "skills/fix-loop/SKILL.md": {
                "hub_hash": "sha256:aaa",
                "provisioned_date": "2026-02-15",
            },
            "skills/security-audit/SKILL.md": {
                "hub_hash": "sha256:bbb",
                "provisioned_date": "2026-02-15",
            },
            "skills/tdd/SKILL.md": {
                "hub_hash": "sha256:ccc",
                "provisioned_date": "2026-02-15",
            },
        },
    }
    (claude_dir / "sync-manifest.json").write_text(json.dumps(manifest, indent=2))

    return tmp_path / "project_b"


@pytest.fixture
def sample_learnings_with_links():
    """Learnings from a project with hub_pattern_link fields."""
    return {
        "learnings": [
            {
                "id": "L001",
                "date": "2026-03-10",
                "error": {"message": "SQL injection in raw query"},
                "fix": {"description": "Used parameterized query"},
                "lesson": "Always use ORM or parameterized queries",
                "tags": ["security", "sql"],
                "hub_pattern_link": "security-audit",
                "reuse_count": 0,
            },
            {
                "id": "L002",
                "date": "2026-03-12",
                "error": {"message": "Test failed intermittently"},
                "fix": {"description": "Added retry logic"},
                "lesson": "Flaky tests need isolation",
                "tags": ["testing"],
                "hub_pattern_link": "fix-loop",
                "reuse_count": 2,
            },
            {
                "id": "L003",
                "date": "2026-03-20",
                "error": {"message": "Another SQL issue"},
                "fix": {"description": "Fixed raw query"},
                "lesson": "Same class of SQL issue",
                "tags": ["security", "sql"],
                "hub_pattern_link": "security-audit",
                "reuse_count": 0,
            },
        ]
    }


# --- Tests: scan_project_adoption ---


class TestScanProjectAdoption:
    """Test passive adoption scanning from project .claude/ state."""

    def test_detects_kept_patterns(self, project_a_claude_dir):
        result = scan_project_adoption(project_a_claude_dir)
        assert result["fix-loop"]["status"] == "adopted"
        assert result["tdd"]["status"] == "adopted"

    def test_detects_deleted_patterns(self, project_a_claude_dir):
        result = scan_project_adoption(project_a_claude_dir)
        assert result["security-audit"]["status"] == "deleted"

    def test_computes_retention_days(self, project_a_claude_dir):
        result = scan_project_adoption(project_a_claude_dir)
        # fix-loop provisioned 2026-03-01, scan date is "now"
        assert result["fix-loop"]["retention_days"] >= 0

    def test_returns_empty_without_manifest(self, tmp_path):
        """Project with no manifest returns empty adoption data."""
        project = tmp_path / "no_manifest_project"
        project.mkdir()
        result = scan_project_adoption(project)
        assert result == {}

    def test_handles_missing_claude_dir(self, tmp_path):
        project = tmp_path / "empty_project"
        project.mkdir()
        result = scan_project_adoption(project)
        assert result == {}


# --- Tests: compute_adoption_rate ---


class TestComputeAdoptionRate:
    """Test adoption rate calculation across multiple projects."""

    def test_full_adoption(self):
        """Pattern adopted in all projects = 1.0."""
        project_signals = [
            {"fix-loop": {"status": "adopted"}, "tdd": {"status": "adopted"}},
            {"fix-loop": {"status": "adopted"}, "tdd": {"status": "adopted"}},
        ]
        assert compute_adoption_rate("fix-loop", project_signals) == 1.0

    def test_partial_adoption(self):
        """Pattern adopted in 1 of 2 projects = 0.5."""
        project_signals = [
            {"fix-loop": {"status": "adopted"}},
            {"fix-loop": {"status": "deleted"}},
        ]
        assert compute_adoption_rate("fix-loop", project_signals) == 0.5

    def test_zero_adoption(self):
        """Pattern deleted everywhere = 0.0."""
        project_signals = [
            {"fix-loop": {"status": "deleted"}},
            {"fix-loop": {"status": "deleted"}},
        ]
        assert compute_adoption_rate("fix-loop", project_signals) == 0.0

    def test_pattern_not_provisioned(self):
        """Pattern not in any project returns None (no data)."""
        project_signals = [
            {"tdd": {"status": "adopted"}},
        ]
        assert compute_adoption_rate("fix-loop", project_signals) is None

    def test_mixed_provisioning(self):
        """Pattern only provisioned to some projects — rate computed from those only."""
        project_signals = [
            {"fix-loop": {"status": "adopted"}},
            {"fix-loop": {"status": "deleted"}},
            {},  # not provisioned to this project
        ]
        assert compute_adoption_rate("fix-loop", project_signals) == 0.5


# --- Tests: compute_retention_days ---


class TestComputeRetentionDays:
    """Test median retention calculation."""

    def test_median_of_single(self):
        project_signals = [
            {"fix-loop": {"status": "adopted", "retention_days": 30}},
        ]
        assert compute_retention_days("fix-loop", project_signals) == 30

    def test_median_of_multiple(self):
        project_signals = [
            {"fix-loop": {"status": "adopted", "retention_days": 10}},
            {"fix-loop": {"status": "adopted", "retention_days": 50}},
            {"fix-loop": {"status": "adopted", "retention_days": 30}},
        ]
        assert compute_retention_days("fix-loop", project_signals) == 30

    def test_deleted_patterns_use_zero_retention(self):
        """Deleted patterns contribute 0 retention days."""
        project_signals = [
            {"fix-loop": {"status": "adopted", "retention_days": 30}},
            {"fix-loop": {"status": "deleted", "retention_days": 5}},
        ]
        # median of [30, 5] = 17.5
        result = compute_retention_days("fix-loop", project_signals)
        assert result == 17.5

    def test_no_data_returns_none(self):
        assert compute_retention_days("fix-loop", [{}]) is None


# --- Tests: compute_error_prevention_rate ---


class TestComputeErrorPreventionRate:
    """Test error prevention rate from linked learnings."""

    def test_computes_from_linked_learnings(self):
        """security-audit linked to 2 errors — prevention rate depends on recurrence."""
        all_learnings = [
            {
                "learnings": [
                    {"hub_pattern_link": "security-audit", "tags": ["security", "sql"],
                     "date": "2026-03-10"},
                    {"hub_pattern_link": "security-audit", "tags": ["security", "sql"],
                     "date": "2026-03-20"},
                ]
            }
        ]
        # 2 errors linked to same pattern = recurring, rate < 1.0
        rate = compute_error_prevention_rate("security-audit", all_learnings)
        assert rate is not None
        assert 0.0 <= rate <= 1.0

    def test_no_linked_learnings_returns_none(self):
        all_learnings = [{"learnings": [{"tags": ["testing"]}]}]
        rate = compute_error_prevention_rate("fix-loop", all_learnings)
        assert rate is None

    def test_single_error_class(self):
        """Single occurrence of an error class = 1.0 prevention (caught once, didn't recur)."""
        all_learnings = [
            {
                "learnings": [
                    {"hub_pattern_link": "fix-loop", "tags": ["testing"],
                     "date": "2026-03-10"},
                ]
            }
        ]
        rate = compute_error_prevention_rate("fix-loop", all_learnings)
        assert rate == 1.0


# --- Tests: aggregate_project_telemetry ---


class TestAggregateProjectTelemetry:
    """Test full aggregation across multiple project directories."""

    def test_aggregates_across_projects(self, project_a_claude_dir, project_b_claude_dir):
        project_dirs = [project_a_claude_dir, project_b_claude_dir]
        result = aggregate_project_telemetry(project_dirs)

        # fix-loop adopted in both
        assert result["fix-loop"]["adoption_rate"] == 1.0
        # security-audit adopted in 1 of 2
        assert result["security-audit"]["adoption_rate"] == 0.5
        # sample_size
        assert result["fix-loop"]["sample_size"] == 2

    def test_empty_projects_list(self):
        result = aggregate_project_telemetry([])
        assert result == {}

    def test_includes_last_updated(self, project_a_claude_dir):
        result = aggregate_project_telemetry([project_a_claude_dir])
        assert "last_updated" in result.get("fix-loop", {})


# --- Tests: write_effectiveness_to_registry ---


class TestWriteEffectivenessToRegistry:
    """Test writing effectiveness data back to registry/patterns.json."""

    def test_writes_effectiveness_block(self, sample_registry_with_patterns):
        effectiveness = {
            "fix-loop": {
                "adoption_rate": 0.9,
                "retention_days_p50": 45,
                "error_prevention_rate": 0.8,
                "sample_size": 5,
                "last_updated": "2026-03-31",
            },
        }
        write_effectiveness_to_registry(sample_registry_with_patterns, effectiveness)

        registry = json.loads(sample_registry_with_patterns.read_text())
        assert "effectiveness" in registry["fix-loop"]
        assert registry["fix-loop"]["effectiveness"]["adoption_rate"] == 0.9
        assert registry["fix-loop"]["effectiveness"]["sample_size"] == 5

    def test_preserves_existing_fields(self, sample_registry_with_patterns):
        effectiveness = {
            "fix-loop": {
                "adoption_rate": 0.9,
                "retention_days_p50": 45,
                "error_prevention_rate": None,
                "sample_size": 2,
                "last_updated": "2026-03-31",
            },
        }
        write_effectiveness_to_registry(sample_registry_with_patterns, effectiveness)

        registry = json.loads(sample_registry_with_patterns.read_text())
        # Existing fields preserved
        assert registry["fix-loop"]["tier"] == "must-have"
        assert registry["fix-loop"]["version"] == "1.2.0"

    def test_skips_patterns_not_in_registry(self, sample_registry_with_patterns):
        effectiveness = {
            "nonexistent-pattern": {
                "adoption_rate": 1.0,
                "retention_days_p50": 30,
                "error_prevention_rate": 0.5,
                "sample_size": 3,
                "last_updated": "2026-03-31",
            },
        }
        write_effectiveness_to_registry(sample_registry_with_patterns, effectiveness)

        registry = json.loads(sample_registry_with_patterns.read_text())
        assert "nonexistent-pattern" not in registry

    def test_omits_none_values(self, sample_registry_with_patterns):
        """None values (insufficient data) should not be written."""
        effectiveness = {
            "tdd": {
                "adoption_rate": 0.5,
                "retention_days_p50": None,
                "error_prevention_rate": None,
                "sample_size": 1,
                "last_updated": "2026-03-31",
            },
        }
        write_effectiveness_to_registry(sample_registry_with_patterns, effectiveness)

        registry = json.loads(sample_registry_with_patterns.read_text())
        eff = registry["tdd"]["effectiveness"]
        assert "retention_days_p50" not in eff
        assert "error_prevention_rate" not in eff
        assert eff["adoption_rate"] == 0.5


# --- Tests: telemetry aggregates persistence ---


class TestTelemetryAggregatesPersistence:
    """Test saving/loading telemetry aggregates to config/."""

    def test_save_and_load_roundtrip(self, tmp_path):
        aggregates = {
            "fix-loop": {"adoption_rate": 0.9, "sample_size": 3},
        }
        save_path = tmp_path / "config" / "telemetry-aggregates.json"
        save_path.parent.mkdir(parents=True)
        save_telemetry_aggregates(save_path, aggregates)

        loaded = load_telemetry_aggregates(save_path)
        assert loaded["fix-loop"]["adoption_rate"] == 0.9

    def test_load_missing_file_returns_empty(self, tmp_path):
        missing = tmp_path / "config" / "telemetry-aggregates.json"
        loaded = load_telemetry_aggregates(missing)
        assert loaded == {}


# --- Edge Case Tests ---


class TestEdgeCases:
    """Edge cases identified by adversarial review."""

    def test_future_provisioned_date_clamps_to_zero(self, tmp_path):
        """Future dates should not produce negative retention days."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills" / "fix-loop").mkdir(parents=True)
        (claude_dir / "skills" / "fix-loop" / "SKILL.md").write_text("# fix-loop")

        manifest = {
            "files": {
                "skills/fix-loop/SKILL.md": {
                    "provisioned_date": "2099-01-01",
                }
            }
        }
        (claude_dir / "sync-manifest.json").write_text(json.dumps(manifest))
        result = scan_project_adoption(tmp_path)
        assert result["fix-loop"]["retention_days"] >= 0

    def test_timezone_aware_provisioned_date(self, tmp_path):
        """Dates with timezone info should not be silently shifted to UTC."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills" / "fix-loop").mkdir(parents=True)
        (claude_dir / "skills" / "fix-loop" / "SKILL.md").write_text("# fix-loop")

        manifest = {
            "files": {
                "skills/fix-loop/SKILL.md": {
                    "provisioned_date": "2026-03-01T00:00:00+05:30",
                }
            }
        }
        (claude_dir / "sync-manifest.json").write_text(json.dumps(manifest))
        result = scan_project_adoption(tmp_path)
        assert result["fix-loop"]["retention_days"] >= 0

    def test_corrupt_manifest_json(self, tmp_path):
        """Malformed manifest JSON returns empty, no crash."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "sync-manifest.json").write_text("not valid json {{{")
        result = scan_project_adoption(tmp_path)
        assert result == {}

    def test_write_effectiveness_to_corrupt_registry(self, tmp_path):
        """Writing to a corrupt registry file does not crash."""
        path = tmp_path / "patterns.json"
        path.write_text("not json")
        write_effectiveness_to_registry(path, {"fix-loop": {"adoption_rate": 0.9}})
        # Should silently return, file unchanged
        assert path.read_text() == "not json"

    def test_write_effectiveness_to_missing_registry(self, tmp_path):
        """Writing to a nonexistent registry file does not crash."""
        path = tmp_path / "nonexistent" / "patterns.json"
        write_effectiveness_to_registry(path, {"fix-loop": {"adoption_rate": 0.9}})
        # Should silently return

    def test_empty_tags_error_prevention(self):
        """Learnings with empty tags and no message get grouped as 'unknown'."""
        all_learnings = [
            {
                "learnings": [
                    {"hub_pattern_link": "fix-loop", "tags": [], "date": "2026-03-10"},
                    {"hub_pattern_link": "fix-loop", "tags": [], "date": "2026-03-15"},
                ]
            }
        ]
        rate = compute_error_prevention_rate("fix-loop", all_learnings)
        # Both have empty tags → grouped as same error class → recurring
        assert rate == 0.0

    def test_hook_type_patterns_silently_skipped(self, tmp_path):
        """Patterns with hook/config type are skipped in adoption scanning."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        manifest = {
            "files": {
                "hooks/auto-learn-trigger": {
                    "provisioned_date": "2026-03-01",
                }
            }
        }
        (claude_dir / "sync-manifest.json").write_text(json.dumps(manifest))
        result = scan_project_adoption(tmp_path)
        assert result == {}  # Hooks are not tracked
