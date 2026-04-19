"""Tests for pattern collation from project repos."""

import json
from pathlib import Path

import pytest

from scripts.collate import (
    extract_patterns_from_dir,
    detect_pattern_type,
    build_pattern_entry,
)


class TestDetectPatternType:
    def test_skill_directory(self, tmp_path):
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n# Skill")
        assert detect_pattern_type(skill_dir / "SKILL.md") == "skill"

    def test_agent_file(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent = agents_dir / "debugger.md"
        agent.write_text("---\nname: debugger\n---\n# Agent")
        assert detect_pattern_type(agent) == "agent"

    def test_hook_file(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "auto-format.sh"
        hook.write_text("#!/bin/bash\necho hi")
        assert detect_pattern_type(hook) == "hook"

    def test_rule_file(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        rule = rules_dir / "workflow.md"
        rule.write_text("---\nglobs:\n  - '**/*.py'\n---\n# Rules")
        assert detect_pattern_type(rule) == "rule"


class TestExtractPatterns:
    def test_extracts_skills(self, tmp_path):
        skills = tmp_path / ".claude" / "skills" / "test-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("---\nname: test-skill\nversion: '1.0.0'\ndescription: test\n---\n# Test")
        patterns = extract_patterns_from_dir(tmp_path / ".claude")
        assert len(patterns) >= 1
        assert any(p["name"] == "test-skill" for p in patterns)

    def test_skips_gitkeep(self, tmp_path):
        claude = tmp_path / ".claude" / "skills"
        claude.mkdir(parents=True)
        (claude / ".gitkeep").write_text("")
        patterns = extract_patterns_from_dir(tmp_path / ".claude")
        assert len(patterns) == 0

    def test_handles_empty_dir(self, tmp_path):
        claude = tmp_path / ".claude"
        claude.mkdir()
        patterns = extract_patterns_from_dir(claude)
        assert len(patterns) == 0


class TestBuildPatternEntry:
    def test_builds_valid_entry(self, sample_skill_path):
        entry = build_pattern_entry(
            name="sample-skill",
            pattern_type="skill",
            file_path=sample_skill_path,
            source="project:test/repo",
            category="core",
        )
        assert entry["type"] == "skill"
        assert entry["source"] == "project:test/repo"
        assert "hash" in entry
        assert "version" in entry
