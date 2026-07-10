"""Tests for scripts/validate_plugin_cleanroom.py's structural gate.

Pure-Python checks against fixture plugin dirs only — this file MUST NOT invoke
the `claude` CLI (see scripts/tests/conftest.py's `integration` marker for that
category; the CLI-calling gates (`claude plugin validate`, the headless
clean-room serve probe) are exercised manually, not in the pytest suite).
"""

from pathlib import Path

import pytest

from scripts.validate_plugin_cleanroom import check_structural_gate, resolve_plugin_dir

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "plugin-cleanroom" / "marketplace"
MARKETPLACE_PATH = FIXTURES_ROOT / ".claude-plugin" / "marketplace.json"


class TestResolvePluginDir:
    def test_resolves_registered_plugin(self):
        plugin_dir, issues = resolve_plugin_dir("good-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        assert issues == []
        assert plugin_dir == (FIXTURES_ROOT / "good-plugin").resolve()

    def test_unregistered_plugin_reports_issue(self):
        plugin_dir, issues = resolve_plugin_dir("does-not-exist", FIXTURES_ROOT, MARKETPLACE_PATH)
        assert plugin_dir is None
        assert any("not registered" in issue for issue in issues)

    def test_missing_marketplace_file_reports_issue(self, tmp_path):
        plugin_dir, issues = resolve_plugin_dir("good-plugin", FIXTURES_ROOT, tmp_path / "nope.json")
        assert plugin_dir is None
        assert any("unreadable" in issue for issue in issues)


class TestStructuralGate:
    def test_good_plugin_passes(self):
        plugin_dir, resolve_issues = resolve_plugin_dir("good-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        assert resolve_issues == []
        issues = check_structural_gate(plugin_dir, "good-plugin", MARKETPLACE_PATH)
        assert issues == []

    def test_hooks_declared_in_manifest_is_flagged(self):
        plugin_dir, _ = resolve_plugin_dir("hooks-declared-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "hooks-declared-plugin", MARKETPLACE_PATH)
        assert any("declares 'hooks'" in issue for issue in issues)

    def test_missing_skill_md_is_flagged(self):
        plugin_dir, _ = resolve_plugin_dir("missing-skill-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "missing-skill-plugin", MARKETPLACE_PATH)
        assert any("missing SKILL.md" in issue for issue in issues)

    def test_missing_commands_dir_is_flagged(self):
        plugin_dir, _ = resolve_plugin_dir("missing-commands-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "missing-commands-plugin", MARKETPLACE_PATH)
        assert any("missing directory" in issue for issue in issues)

    def test_missing_hook_file_is_flagged(self):
        plugin_dir, _ = resolve_plugin_dir("missing-hook-file-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "missing-hook-file-plugin", MARKETPLACE_PATH)
        assert any("references missing file" in issue for issue in issues)

    def test_missing_version_is_flagged(self):
        plugin_dir, _ = resolve_plugin_dir("no-version-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "no-version-plugin", MARKETPLACE_PATH)
        assert any("version" in issue for issue in issues)

    def test_missing_manifest_is_flagged(self, tmp_path):
        empty_plugin_dir = tmp_path / "empty-plugin"
        empty_plugin_dir.mkdir()
        issues = check_structural_gate(empty_plugin_dir, "empty-plugin", MARKETPLACE_PATH)
        assert any("missing manifest" in issue for issue in issues)

    def test_unparseable_manifest_is_flagged(self, tmp_path):
        plugin_dir = tmp_path / "bad-json-plugin"
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{not valid json", encoding="utf-8")
        issues = check_structural_gate(plugin_dir, "bad-json-plugin", MARKETPLACE_PATH)
        assert any("does not parse" in issue for issue in issues)

    def test_unregistered_plugin_name_is_flagged(self):
        # Structurally valid plugin dir, but checked under a name absent from the fixture marketplace.
        plugin_dir, _ = resolve_plugin_dir("good-plugin", FIXTURES_ROOT, MARKETPLACE_PATH)
        issues = check_structural_gate(plugin_dir, "not-in-marketplace", MARKETPLACE_PATH)
        assert any("not registered" in issue for issue in issues)


class TestRealPlugins:
    """The 5 shipped plugins under plugins/ must all clear the structural gate —
    a regression guard so a future plugin edit can't silently reintroduce the
    manifest hooks-double-declare bug or a dangling skill/hook reference."""

    REPO_ROOT = Path(__file__).parent.parent.parent
    REAL_PLUGINS_ROOT = REPO_ROOT / "plugins"
    REAL_MARKETPLACE_PATH = REAL_PLUGINS_ROOT / ".claude-plugin" / "marketplace.json"

    @pytest.mark.parametrize(
        "plugin_name",
        ["prompt-auto-enhance", "auto-google-analytics", "branch-lifecycle", "fable-operating-manual", "loop-engineering"],
    )
    def test_shipped_plugin_passes_structural_gate(self, plugin_name):
        plugin_dir, resolve_issues = resolve_plugin_dir(plugin_name, self.REAL_PLUGINS_ROOT, self.REAL_MARKETPLACE_PATH)
        assert resolve_issues == [], resolve_issues
        issues = check_structural_gate(plugin_dir, plugin_name, self.REAL_MARKETPLACE_PATH)
        assert issues == [], issues
