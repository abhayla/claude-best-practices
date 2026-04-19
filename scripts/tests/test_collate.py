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


class TestSanitizePatternText:
    """sanitize_pattern_text must scrub accidentally-committed sensitive
    strings before a pattern crosses the repo boundary (hub contributions
    via /synthesize-hub or manual PRs from a downstream project).

    Covered classes: absolute filesystem paths (POSIX + Windows), email
    addresses, and known secret prefixes (AKIA..., sk_live_, sk-ant-,
    ghp_..., Bearer tokens inside code blocks)."""

    def test_scrubs_windows_absolute_path(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text(r"Config at C:\Users\alice\project\config.yml")
        assert r"C:\Users\alice" not in out
        assert "<abs-path>" in out or "<path>" in out

    def test_scrubs_posix_absolute_path(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text("See /home/bob/project/src/main.py for the entry point")
        assert "/home/bob/project" not in out

    def test_scrubs_email(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text("Contact alice@example.com for details.")
        assert "alice@example.com" not in out
        assert "<email>" in out

    def test_scrubs_anthropic_api_key(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text("Set ANTHROPIC_API_KEY=sk-ant-api03-abcdef1234567890")
        assert "sk-ant-api03-abcdef1234567890" not in out
        assert "<redacted-secret>" in out

    def test_scrubs_github_pat(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text("token: ghp_1234567890abcdefghij1234567890abcdefgh")
        assert "ghp_1234567890abcdefghij1234567890abcdefgh" not in out

    def test_scrubs_aws_access_key(self):
        from scripts.collate import sanitize_pattern_text
        out = sanitize_pattern_text("AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN7EXAMPLE" not in out

    def test_idempotent_on_clean_input(self):
        from scripts.collate import sanitize_pattern_text
        original = "Normal pattern content with code `foo.py` and rel paths src/utils/."
        assert sanitize_pattern_text(original) == original, (
            "Sanitization must not mutate text with no sensitive strings"
        )

    def test_preserves_inline_code_examples(self):
        """Relative paths inside backticks (like `src/auth/` or `backend/app/`)
        must NOT be scrubbed — those are legitimate pattern content."""
        from scripts.collate import sanitize_pattern_text
        original = "Place new services in `backend/app/services/` and test in `tests/`."
        out = sanitize_pattern_text(original)
        assert "backend/app/services" in out
        assert "tests/" in out


class TestSynthesisConfigPrivacy:
    """extract_patterns_from_dir must respect the project's synthesis-config.yml
    so `/synthesize-project`'s documented privacy guarantees are real, not
    aspirational."""

    def _make_skill(self, claude_dir, name, frontmatter_extra=""):
        skill_dir = claude_dir / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        fm = f"---\nname: {name}\nversion: '1.0.0'\ndescription: test skill\n{frontmatter_extra}---\n# {name}\n"
        (skill_dir / "SKILL.md").write_text(fm)

    def test_allow_hub_sharing_false_skips_project_entirely(self, tmp_path):
        claude = tmp_path / ".claude"
        self._make_skill(claude, "public-skill")
        self._make_skill(claude, "another-skill")
        (claude / "synthesis-config.yml").write_text(
            "allow_hub_sharing: false\nprivate_patterns: []\n"
        )
        patterns = extract_patterns_from_dir(claude)
        assert patterns == [], (
            f"With allow_hub_sharing=false, no patterns should leak. Got: {patterns}"
        )

    def test_private_true_frontmatter_filters_pattern(self, tmp_path):
        claude = tmp_path / ".claude"
        self._make_skill(claude, "public-skill")
        self._make_skill(claude, "secret-skill", frontmatter_extra="private: true\n")
        (claude / "synthesis-config.yml").write_text("allow_hub_sharing: true\n")
        patterns = extract_patterns_from_dir(claude)
        names = {p["name"] for p in patterns}
        assert "public-skill" in names
        assert "secret-skill" not in names, (
            "Patterns with private: true in frontmatter must not be returned"
        )

    def test_private_patterns_list_filters_named_patterns(self, tmp_path):
        claude = tmp_path / ".claude"
        self._make_skill(claude, "public-skill")
        self._make_skill(claude, "internal-ops")
        (claude / "synthesis-config.yml").write_text(
            "allow_hub_sharing: true\nprivate_patterns:\n  - skills/internal-ops\n"
        )
        patterns = extract_patterns_from_dir(claude)
        names = {p["name"] for p in patterns}
        assert "public-skill" in names
        assert "internal-ops" not in names, (
            "Patterns listed in private_patterns must not be returned"
        )

    def test_no_config_file_returns_all_patterns(self, tmp_path):
        """Backward compatibility: projects without synthesis-config.yml behave
        as they did before (no filtering)."""
        claude = tmp_path / ".claude"
        self._make_skill(claude, "one")
        self._make_skill(claude, "two")
        patterns = extract_patterns_from_dir(claude)
        names = {p["name"] for p in patterns}
        assert names == {"one", "two"}
