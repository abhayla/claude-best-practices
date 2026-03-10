"""Tests for documentation generation."""

import json
from pathlib import Path

import pytest

from scripts.generate_docs import (
    count_patterns,
    generate_dashboard_md,
    generate_stack_catalog,
    generate_getting_started,
)


class TestCountPatterns:
    def test_counts_correctly(self, sample_registry):
        counts = count_patterns(sample_registry)
        assert counts["total"] == 2
        assert counts["core"] == 2
        assert counts["by_type"]["skill"] == 1
        assert counts["by_type"]["hook"] == 1


class TestGenerateDashboardMd:
    def test_has_required_sections(self, sample_registry):
        md = generate_dashboard_md(sample_registry, [], {})
        assert "# Claude Best Practices Hub" in md
        assert "At a Glance" in md
        assert "Pattern Inventory" in md

    def test_includes_pattern_count(self, sample_registry):
        md = generate_dashboard_md(sample_registry, [], {})
        assert "2" in md


class TestGenerateStackCatalog:
    def test_lists_stacks(self, tmp_path):
        """Stack catalog now uses .claude/ dir with prefix convention."""
        claude_dir = tmp_path / ".claude"
        (claude_dir / "agents").mkdir(parents=True)
        (claude_dir / "agents" / "android-compose.md").write_text("# Android")
        (claude_dir / "skills" / "android-run-tests").mkdir(parents=True)
        (claude_dir / "skills" / "android-run-tests" / "SKILL.md").write_text("# Tests")
        catalog = generate_stack_catalog(claude_dir)
        assert "Android" in catalog
        assert "android-" in catalog


class TestGenerateGettingStarted:
    def test_has_quick_start(self):
        doc = generate_getting_started("abhayla/claude-best-practices", ["android-compose"])
        assert "Quick Start" in doc
        assert "android-compose" in doc
