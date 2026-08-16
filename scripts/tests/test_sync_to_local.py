"""Behavior tests for scripts/sync_to_local.py (hub -> local project directory).

apply_update and find_updated_patterns do real filesystem I/O against tmp-path fixture
"hub" and "project" directories — no mocking of the copy/hash behavior itself, per the
existing repo convention (see test_bootstrap.py's TestCopyClaudeDir).
"""

from pathlib import Path

import pytest
import yaml

from scripts.sync_to_local import (
    apply_update,
    compare_versions,
    find_updated_patterns,
    load_sync_config,
)
from scripts.dedup_check import hash_pattern


# ── load_sync_config: real file I/O ──────────────────────────────────────────

class TestLoadSyncConfig:
    def test_happy_path_reads_config(self, tmp_path):
        claude = tmp_path / ".claude"
        claude.mkdir()
        (claude / "sync-config.yml").write_text(yaml.dump({"selected_stacks": ["fastapi-python"]}), encoding="utf-8")
        cfg = load_sync_config(tmp_path)
        assert cfg == {"selected_stacks": ["fastapi-python"]}

    def test_missing_config_returns_none(self, tmp_path):
        assert load_sync_config(tmp_path) is None


# ── compare_versions: pure semver comparison ─────────────────────────────────

class TestCompareVersions:
    def test_hub_newer_returns_1(self):
        assert compare_versions("1.2.0", "1.1.0") == 1

    def test_hub_older_returns_negative_1(self):
        assert compare_versions("1.0.0", "1.1.0") == -1

    def test_equal_returns_0(self):
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_leading_v_prefix_is_stripped(self):
        assert compare_versions("v2.0.0", "1.9.9") == 1


# ── find_updated_patterns: real files on disk, hash-compared ────────────────

class TestFindUpdatedPatterns:
    def test_happy_path_up_to_date_pattern_is_skipped(self, tmp_path):
        local_dir = tmp_path / "project"
        skill_dir = local_dir / ".claude" / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Fix Loop\nsame content\n", encoding="utf-8")
        current_hash = hash_pattern(str(skill_file))

        hub_registry = {"fix-loop": {"type": "skill", "hash": current_hash, "version": "1.0.0"}}
        updates = find_updated_patterns(hub_registry, local_dir)
        assert updates == []

    def test_drift_case_hash_mismatch_is_flagged_for_update(self, tmp_path):
        local_dir = tmp_path / "project"
        skill_dir = local_dir / ".claude" / "skills" / "fix-loop"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Fix Loop\nOLD content\n", encoding="utf-8")

        hub_registry = {"fix-loop": {"type": "skill", "hash": "deadbeef" * 8, "version": "1.1.0"}}
        updates = find_updated_patterns(hub_registry, local_dir)
        assert len(updates) == 1
        assert updates[0]["name"] == "fix-loop"
        assert updates[0]["local_exists"] is True
        assert updates[0]["local_hash"] != "deadbeef" * 8

    def test_missing_local_pattern_is_flagged_with_local_exists_false(self, tmp_path):
        local_dir = tmp_path / "project"
        local_dir.mkdir()
        hub_registry = {"new-agent": {"type": "agent", "hash": "abc123", "version": "1.0.0"}}
        updates = find_updated_patterns(hub_registry, local_dir)
        assert len(updates) == 1
        assert updates[0]["local_exists"] is False
        assert updates[0]["local_hash"] is None

    def test_windows_crlf_vs_hub_lf_line_endings_do_not_register_as_drift(self, tmp_path):
        """A Windows checkout writes CRLF while the hub source is LF-normalized in git — the
        content hash must normalize line endings so this is NOT treated as a real edit."""
        local_dir = tmp_path / "project"
        rule_dir = local_dir / ".claude" / "rules"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "workflow.md"
        rule_file.write_bytes(b"# Workflow\r\nsame content\r\n")  # CRLF, as Windows git checkout would produce

        # Hash computed from the LF-normalized hub-side equivalent content.
        lf_equivalent = tmp_path / "lf_equivalent.md"
        lf_equivalent.write_bytes(b"# Workflow\nsame content\n")
        hub_hash = hash_pattern(str(lf_equivalent))

        hub_registry = {"workflow": {"type": "rule", "hash": hub_hash, "version": "1.0.0"}}
        updates = find_updated_patterns(hub_registry, local_dir)
        assert updates == [], "CRLF vs LF must not be reported as drift"

    def test_meta_and_non_dict_entries_are_skipped(self, tmp_path):
        local_dir = tmp_path / "project"
        local_dir.mkdir()
        hub_registry = {"_meta": {"version": "1.0.0"}, "not_a_dict": "oops"}
        assert find_updated_patterns(hub_registry, local_dir) == []

    def test_unknown_pattern_type_is_skipped(self, tmp_path):
        local_dir = tmp_path / "project"
        local_dir.mkdir()
        hub_registry = {"mystery": {"type": "unknown-type", "hash": "x", "version": "1.0.0"}}
        assert find_updated_patterns(hub_registry, local_dir) == []


# ── apply_update: real copy operations against tmp-path hub/project roots ───

class TestApplyUpdate:
    def test_happy_path_copies_skill_directory(self, tmp_path):
        hub_root = tmp_path / "hub"
        src = hub_root / "core" / ".claude" / "skills" / "fix-loop"
        src.mkdir(parents=True)
        (src / "SKILL.md").write_text("# Fix Loop", encoding="utf-8")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        assert apply_update(hub_root, project_dir, "fix-loop", "skill", "core") is True
        assert (project_dir / ".claude" / "skills" / "fix-loop" / "SKILL.md").read_text(encoding="utf-8") == "# Fix Loop"

    def test_missing_source_skill_returns_false(self, tmp_path):
        hub_root = tmp_path / "hub"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        assert apply_update(hub_root, project_dir, "does-not-exist", "skill", "core") is False

    def test_copies_agent_rule_and_hook_files(self, tmp_path):
        hub_root = tmp_path / "hub"
        (hub_root / "core" / ".claude" / "agents").mkdir(parents=True)
        (hub_root / "core" / ".claude" / "agents" / "debugger.md").write_text("# Debugger", encoding="utf-8")
        (hub_root / "core" / ".claude" / "rules").mkdir(parents=True)
        (hub_root / "core" / ".claude" / "rules" / "workflow.md").write_text("# Workflow", encoding="utf-8")
        (hub_root / "core" / ".claude" / "hooks").mkdir(parents=True)
        (hub_root / "core" / ".claude" / "hooks" / "auto-format.sh").write_text("#!/bin/bash", encoding="utf-8")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        assert apply_update(hub_root, project_dir, "debugger", "agent", "core") is True
        assert apply_update(hub_root, project_dir, "workflow", "rule", "core") is True
        assert apply_update(hub_root, project_dir, "auto-format", "hook", "core") is True

        assert (project_dir / ".claude" / "agents" / "debugger.md").exists()
        assert (project_dir / ".claude" / "rules" / "workflow.md").exists()
        assert (project_dir / ".claude" / "hooks" / "auto-format.sh").exists()

    def test_unknown_pattern_type_returns_false(self, tmp_path):
        hub_root = tmp_path / "hub"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        assert apply_update(hub_root, project_dir, "x", "unknown-type", "core") is False

    def test_skill_copy_overwrites_existing_destination(self, tmp_path):
        """A re-apply must replace stale content, not merge/append (shutil.rmtree then copytree)."""
        hub_root = tmp_path / "hub"
        src = hub_root / "core" / ".claude" / "skills" / "fix-loop"
        src.mkdir(parents=True)
        (src / "SKILL.md").write_text("# Fix Loop v2", encoding="utf-8")

        project_dir = tmp_path / "project"
        dst = project_dir / ".claude" / "skills" / "fix-loop"
        dst.mkdir(parents=True)
        (dst / "SKILL.md").write_text("# stale v1", encoding="utf-8")
        (dst / "stale-extra-file.md").write_text("should be removed", encoding="utf-8")

        assert apply_update(hub_root, project_dir, "fix-loop", "skill", "core") is True
        assert (dst / "SKILL.md").read_text(encoding="utf-8") == "# Fix Loop v2"
        assert not (dst / "stale-extra-file.md").exists()

    def test_windows_style_root_paths_still_resolve(self, tmp_path):
        """hub_root/project_dir constructed from a raw backslash-joined Windows string (as a CLI
        arg would arrive) must resolve identically to the pathlib-joined equivalent."""
        hub_root = Path(str(tmp_path) + "\\hub")
        src = hub_root / "core" / ".claude" / "agents"
        src.mkdir(parents=True)
        (src / "debugger.md").write_text("# Debugger", encoding="utf-8")

        project_dir = Path(str(tmp_path) + "\\project")
        project_dir.mkdir()

        assert apply_update(hub_root, project_dir, "debugger", "agent", "core") is True
        assert (project_dir / ".claude" / "agents" / "debugger.md").exists()
