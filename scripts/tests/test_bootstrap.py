"""Tests for project bootstrapping from hub patterns."""

import json
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.bootstrap import (
    load_stack_config,
    validate_stack_selection,
    copy_layer,
    render_template,
    generate_sync_config,
)


class TestLoadStackConfig:
    def test_loads_valid_config(self, tmp_path):
        config_file = tmp_path / "stack-config.yml"
        config_file.write_text(yaml.dump({
            "name": "test-stack",
            "namespace": "test",
            "conflicts_with": [],
            "merges_with": [],
        }))
        config = load_stack_config(config_file)
        assert config["name"] == "test-stack"

    def test_missing_file_returns_none(self, tmp_path):
        config = load_stack_config(tmp_path / "nonexistent.yml")
        assert config is None


class TestValidateStackSelection:
    def test_no_conflicts_passes(self):
        configs = {
            "android": {"conflicts_with": []},
            "fastapi": {"conflicts_with": []},
        }
        errors = validate_stack_selection(["android", "fastapi"], configs)
        assert len(errors) == 0

    def test_conflict_detected(self):
        configs = {
            "android": {"conflicts_with": ["react"]},
            "react": {"conflicts_with": ["android"]},
        }
        errors = validate_stack_selection(["android", "react"], configs)
        assert len(errors) > 0

    def test_unknown_stack_rejected(self):
        configs = {"android": {"conflicts_with": []}}
        errors = validate_stack_selection(["android", "nonexistent"], configs)
        assert any("nonexistent" in e for e in errors)


class TestCopyLayer:
    def test_copies_files(self, tmp_path):
        src = tmp_path / "src" / ".claude" / "skills" / "test"
        src.mkdir(parents=True)
        (src / "SKILL.md").write_text("# test")
        dst = tmp_path / "dst"
        dst.mkdir()
        copy_layer(tmp_path / "src", dst)
        assert (dst / ".claude" / "skills" / "test" / "SKILL.md").exists()

    def test_skips_gitkeep(self, tmp_path):
        src = tmp_path / "src" / ".claude" / "skills"
        src.mkdir(parents=True)
        (src / ".gitkeep").write_text("")
        dst = tmp_path / "dst"
        dst.mkdir()
        copy_layer(tmp_path / "src", dst)
        assert not (dst / ".claude" / "skills" / ".gitkeep").exists()


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
