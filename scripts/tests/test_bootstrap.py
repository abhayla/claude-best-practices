"""Tests for project bootstrapping from hub patterns."""

import json
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.bootstrap import (
    validate_stack_selection,
    copy_claude_dir,
    render_template,
    generate_sync_config,
    get_available_stacks,
    STACK_PREFIXES,
)


class TestValidateStackSelection:
    def test_valid_stacks_pass(self):
        errors = validate_stack_selection(["fastapi-python", "android-compose"])
        assert len(errors) == 0

    def test_unknown_stack_rejected(self):
        errors = validate_stack_selection(["fastapi-python", "nonexistent"])
        assert any("nonexistent" in e for e in errors)

    def test_empty_list_passes(self):
        errors = validate_stack_selection([])
        assert len(errors) == 0


class TestGetAvailableStacks:
    def test_returns_all_stacks(self):
        stacks = get_available_stacks()
        assert "fastapi-python" in stacks
        assert "android-compose" in stacks
        assert "ai-gemini" in stacks

    def test_returns_sorted(self):
        stacks = get_available_stacks()
        assert stacks == sorted(stacks)


class TestCopyClaudeDir:
    def test_copies_core_files(self, tmp_path):
        """Core (non-prefixed) files are always copied."""
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "agents").mkdir(parents=True)
        (hub / "core" / ".claude" / "agents" / "debugger.md").write_text("# Debugger")
        (hub / "core" / ".claude" / "skills" / "fix-loop").mkdir(parents=True)
        (hub / "core" / ".claude" / "skills" / "fix-loop" / "SKILL.md").write_text("# Fix Loop")

        dst = tmp_path / "dst"
        dst.mkdir()
        copied = copy_claude_dir(hub, dst, ["fastapi-python"])

        assert (dst / ".claude" / "agents" / "debugger.md").exists()
        assert (dst / ".claude" / "skills" / "fix-loop" / "SKILL.md").exists()

    def test_copies_matching_stack_files(self, tmp_path):
        """Stack-prefixed files are copied when stack is selected."""
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "agents").mkdir(parents=True)
        (hub / "core" / ".claude" / "agents" / "fastapi-api-tester.md").write_text("# API Tester")
        (hub / "core" / ".claude" / "skills" / "fastapi-db-migrate").mkdir(parents=True)
        (hub / "core" / ".claude" / "skills" / "fastapi-db-migrate" / "SKILL.md").write_text("# DB Migrate")

        dst = tmp_path / "dst"
        dst.mkdir()
        copied = copy_claude_dir(hub, dst, ["fastapi-python"])

        assert (dst / ".claude" / "agents" / "fastapi-api-tester.md").exists()
        assert (dst / ".claude" / "skills" / "fastapi-db-migrate" / "SKILL.md").exists()

    def test_excludes_non_matching_stack_files(self, tmp_path):
        """Stack-prefixed files are excluded when stack is not selected."""
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "agents").mkdir(parents=True)
        (hub / "core" / ".claude" / "agents" / "fastapi-api-tester.md").write_text("# API Tester")
        (hub / "core" / ".claude" / "agents" / "android-compose.md").write_text("# Android")
        (hub / "core" / ".claude" / "agents" / "debugger.md").write_text("# Debugger")

        dst = tmp_path / "dst"
        dst.mkdir()
        copied = copy_claude_dir(hub, dst, ["android-compose"])

        # Core file always copied
        assert (dst / ".claude" / "agents" / "debugger.md").exists()
        # Android file copied (selected stack)
        assert (dst / ".claude" / "agents" / "android-compose.md").exists()
        # FastAPI file NOT copied (not selected)
        assert not (dst / ".claude" / "agents" / "fastapi-api-tester.md").exists()

    def test_skips_gitkeep(self, tmp_path):
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "skills").mkdir(parents=True)
        (hub / "core" / ".claude" / "skills" / ".gitkeep").write_text("")

        dst = tmp_path / "dst"
        dst.mkdir()
        copied = copy_claude_dir(hub, dst, [])

        assert not (dst / ".claude" / "skills" / ".gitkeep").exists()

    def test_handles_missing_claude_dir(self, tmp_path):
        hub = tmp_path / "hub"
        hub.mkdir()  # No core/.claude/ inside

        dst = tmp_path / "dst"
        dst.mkdir()
        copied = copy_claude_dir(hub, dst, ["fastapi-python"])

        assert len(copied) == 0


class TestRenderTemplate:
    def test_replaces_variables(self):
        template = "# {{PROJECT_NAME}}\n{{PROJECT_DESCRIPTION}}"
        result = render_template(template, {
            "PROJECT_NAME": "MyApp",
            "PROJECT_DESCRIPTION": "A test app",
        })
        assert "MyApp" in result
        assert "A test app" in result


class TestGenerateSyncConfig:
    def test_generates_valid_yaml(self):
        config = generate_sync_config(
            hub_repo="owner/hub",
            stacks=["android-compose", "fastapi-python"],
        )
        parsed = yaml.safe_load(config)
        assert parsed["hub_repo"] == "owner/hub"
        assert "android-compose" in parsed["selected_stacks"]
        assert "fastapi-python" in parsed["selected_stacks"]
