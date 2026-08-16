"""Behavior tests for the CORE mechanics of scripts/sync_dual_home.py against isolated
tmp-path "hub"/"core" fixture trees.

test_dual_home_sync.py (the existing CI gate) ALSO exercises this module's pure text-diff
helpers (in_sync, shared_in_sync, fence_problems, intermingle_problems, extra_file_problems)
directly, and runs check()/discover() ONLY against the real repo's live .claude/ +
core/.claude/ trees via a module-scoped fixture — it never proves discover(), classify(),
sync_one()'s COPY path, or the CLI (main()) work correctly against isolated fixtures, so a
bug in any of those (e.g. discover() missing a one-sided resource, sync_one() copying the
wrong direction) would ship silently. This file closes that gap, AND (TestStraySideMarkers)
carries its own direct, isolated coverage of stray_side_markers/intermingle_problems so this
file's suite alone (not just the sibling file) catches a forbidden-side regression.
"""

import json

import pytest
import yaml

from scripts import sync_dual_home as s


@pytest.fixture
def fixture_repo(tmp_path, monkeypatch):
    """An isolated hub/core tree + manifest, with sync_dual_home's module globals repointed
    at it — so discover()/check()/sync_one() run their real logic against a small, fully
    controlled fixture instead of this repo's live (large, slow-changing) trees."""
    hub = tmp_path / ".claude"
    core = tmp_path / "core" / ".claude"
    manifest_path = tmp_path / "dual-home-resources.yml"
    monkeypatch.setattr(s, "HUB", hub)
    monkeypatch.setattr(s, "CORE", core)
    monkeypatch.setattr(s, "MANIFEST", manifest_path)
    return {"hub": hub, "core": core, "manifest_path": manifest_path}


def _write_manifest(path, data):
    path.write_text(yaml.dump(data), encoding="utf-8")


# ── discover(): real filesystem scan of both trees ───────────────────────────

class TestDiscover:
    def test_happy_path_finds_resource_present_in_both_trees(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "rules").mkdir(parents=True)
        (core / "rules").mkdir(parents=True)
        (hub / "rules" / "workflow.md").write_text("same\n", encoding="utf-8")
        (core / "rules" / "workflow.md").write_text("same\n", encoding="utf-8")

        found = s.discover()
        assert len(found) == 1
        assert found[0]["kind"] == "rules"
        assert found[0]["name"] == "workflow.md"

    def test_one_sided_resource_is_excluded(self, fixture_repo):
        """A resource only in .claude/ (hub-only, not distributed) must NOT be reported as
        dual-home — it's not present in core/.claude/ at all."""
        hub = fixture_repo["hub"]
        (hub / "agents").mkdir(parents=True)
        (hub / "agents" / "hub-only-agent.md").write_text("x", encoding="utf-8")
        assert s.discover() == []

    def test_skill_directories_compare_skill_md_and_carry_dir_refs(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        for base in (hub, core):
            skill = base / "skills" / "my-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: my-skill\n---\n", encoding="utf-8")

        found = s.discover()
        assert len(found) == 1
        entry = found[0]
        assert entry["hub"].name == "SKILL.md"
        assert "hub_dir" in entry and "core_dir" in entry


# ── stray_side_markers() / intermingle_problems(): forbidden-fence detection ─

class TestStraySideMarkers:
    """Direct, isolated coverage of the intermingle-fence drift detector — deliberately
    NOT relying on test_dual_home_sync.py's coverage of the same functions, so this file's
    suite alone catches a forbidden-side regression (e.g. the HUB<->DOWNSTREAM ternary
    swapped in stray_side_markers)."""

    def test_correct_side_markers_pass_clean(self):
        hub_text = "shared\n# DUAL-SYNC:HUB-ONLY\nhub bit\n# DUAL-SYNC:END\n"
        core_text = "shared\n# DUAL-SYNC:DOWNSTREAM-ONLY\ncore bit\n# DUAL-SYNC:END\n"
        assert s.stray_side_markers(hub_text, "hub") == []
        assert s.stray_side_markers(core_text, "core") == []

    def test_hub_only_marker_in_downstream_copy_is_flagged(self):
        """A HUB-ONLY fenced line appearing in the downstream (core) copy must be flagged —
        core files must never carry hub-specific fenced content."""
        core_text = "shared\n# DUAL-SYNC:HUB-ONLY\nleaked hub bit\n# DUAL-SYNC:END\n"
        found = s.stray_side_markers(core_text, "core")
        assert found == ["# DUAL-SYNC:HUB-ONLY"]

    def test_downstream_only_marker_in_hub_copy_is_flagged(self):
        """A DOWNSTREAM-ONLY fenced line appearing in the hub copy must be flagged — hub
        files must never carry downstream-specific fenced content."""
        hub_text = "shared\n# DUAL-SYNC:DOWNSTREAM-ONLY\nleaked core bit\n# DUAL-SYNC:END\n"
        found = s.stray_side_markers(hub_text, "hub")
        assert found == ["# DUAL-SYNC:DOWNSTREAM-ONLY"]

    def test_intermingle_problems_reports_both_directions(self):
        res = {
            "hub": None,
            "core": None,
        }

        class _FakePath:
            def __init__(self, text):
                self._text = text

            def read_text(self, encoding="utf-8"):
                return self._text

        res["hub"] = _FakePath("clean\n")
        res["core"] = _FakePath("shared\n# DUAL-SYNC:HUB-ONLY\noops\n# DUAL-SYNC:END\n")
        assert s.intermingle_problems(res) == ["# DUAL-SYNC:HUB-ONLY"]

        res["hub"] = _FakePath("shared\n# DUAL-SYNC:DOWNSTREAM-ONLY\noops\n# DUAL-SYNC:END\n")
        res["core"] = _FakePath("clean\n")
        assert s.intermingle_problems(res) == ["# DUAL-SYNC:DOWNSTREAM-ONLY"]

        res["hub"] = _FakePath("clean\n")
        res["core"] = _FakePath("clean\n")
        assert s.intermingle_problems(res) == []


# ── classify(): manifest lookup ──────────────────────────────────────────────

class TestClassify:
    MANIFEST = {
        "synced": {"agents": ["a.md"]},
        "shared": {"skills": ["shared-skill"]},
        "divergent": {"hooks": {"h.sh": "reason"}},
    }

    def test_synced_lookup(self):
        assert s.classify("agents", "a.md", self.MANIFEST) == "synced"

    def test_shared_lookup(self):
        assert s.classify("skills", "shared-skill", self.MANIFEST) == "shared"

    def test_divergent_lookup(self):
        assert s.classify("hooks", "h.sh", self.MANIFEST) == "divergent"

    def test_unclassified_returns_none(self):
        assert s.classify("rules", "unknown.md", self.MANIFEST) is None


# ── check(): end-to-end drift report against the fixture tree ───────────────

class TestCheckEndToEnd:
    def test_happy_path_synced_resource_reports_ok(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "agents").mkdir(parents=True)
        (core / "agents").mkdir(parents=True)
        (hub / "agents" / "a.md").write_text("same content\n", encoding="utf-8")
        (core / "agents" / "a.md").write_text("same content\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {"synced": {"agents": ["a.md"]}})

        report = s.check()
        assert [f"{r['kind']}/{r['name']}" for r in report["ok"]] == ["agents/a.md"]
        assert report["drifted"] == []
        assert report["unclassified"] == []

    def test_drift_case_synced_resource_with_different_content_is_flagged(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "agents").mkdir(parents=True)
        (core / "agents").mkdir(parents=True)
        (hub / "agents" / "a.md").write_text("hub version\n", encoding="utf-8")
        (core / "agents" / "a.md").write_text("core version — DIFFERENT\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {"synced": {"agents": ["a.md"]}})

        report = s.check()
        assert [f"{r['kind']}/{r['name']}" for r in report["drifted"]] == ["agents/a.md"]

    def test_resource_present_but_not_in_manifest_is_unclassified(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "rules").mkdir(parents=True)
        (core / "rules").mkdir(parents=True)
        (hub / "rules" / "new.md").write_text("x\n", encoding="utf-8")
        (core / "rules" / "new.md").write_text("x\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {})

        report = s.check()
        assert [f"{r['kind']}/{r['name']}" for r in report["unclassified"]] == ["rules/new.md"]


# ── sync_one(): real copy between the two fixture trees ─────────────────────

class TestSyncOneCopies:
    def test_happy_path_copies_hub_to_core_for_synced_resource(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "rules").mkdir(parents=True)
        (core / "rules").mkdir(parents=True)
        (hub / "rules" / "workflow.md").write_text("NEW hub content\n", encoding="utf-8")
        (core / "rules" / "workflow.md").write_text("stale core content\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {"synced": {"rules": ["workflow.md"]}})

        rc = s.sync_one("workflow.md", "hub")
        assert rc == 0
        assert (core / "rules" / "workflow.md").read_text(encoding="utf-8") == "NEW hub content\n"

    def test_unknown_resource_returns_error(self, fixture_repo):
        assert s.sync_one("does-not-exist.md", "hub") == 1


# ── main(): CLI wrapper exit codes ───────────────────────────────────────────

class TestMainCli:
    def test_check_exits_nonzero_on_unclassified(self, fixture_repo, capsys):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "rules").mkdir(parents=True)
        (core / "rules").mkdir(parents=True)
        (hub / "rules" / "new.md").write_text("x\n", encoding="utf-8")
        (core / "rules" / "new.md").write_text("x\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {})

        rc = s.main([])
        assert rc == 1
        assert "UNCLASSIFIED" in capsys.readouterr().out

    def test_check_exits_zero_when_all_ok(self, fixture_repo):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "agents").mkdir(parents=True)
        (core / "agents").mkdir(parents=True)
        (hub / "agents" / "a.md").write_text("same\n", encoding="utf-8")
        (core / "agents" / "a.md").write_text("same\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {"synced": {"agents": ["a.md"]}})

        assert s.main([]) == 0

    def test_list_prints_every_resource_with_its_class(self, fixture_repo, capsys):
        hub, core = fixture_repo["hub"], fixture_repo["core"]
        (hub / "agents").mkdir(parents=True)
        (core / "agents").mkdir(parents=True)
        (hub / "agents" / "a.md").write_text("x\n", encoding="utf-8")
        (core / "agents" / "a.md").write_text("x\n", encoding="utf-8")
        _write_manifest(fixture_repo["manifest_path"], {"synced": {"agents": ["a.md"]}})

        assert s.main(["--list"]) == 0
        assert "[synced] agents/a.md" in capsys.readouterr().out

    def test_sync_without_from_returns_error(self, fixture_repo, capsys):
        assert s.main(["--sync", "a.md"]) == 2
        assert "requires --from" in capsys.readouterr().out


# ── Windows-vs-Unix path-separator case ──────────────────────────────────────

class TestWindowsStyleTreeRoots:
    def test_discover_and_check_work_when_roots_are_backslash_joined_strings(self, tmp_path, monkeypatch):
        """HUB/CORE are normally built via pathlib '/' joins from ROOT (Path(__file__)...); this
        proves discover()/check() behave identically when those roots instead come from a raw
        backslash-joined Windows path string (e.g. an env var or CLI arg on this platform)."""
        from pathlib import Path

        hub = Path(str(tmp_path) + "\\.claude")
        core = Path(str(tmp_path) + "\\core\\.claude")
        manifest_path = Path(str(tmp_path) + "\\dual-home-resources.yml")
        monkeypatch.setattr(s, "HUB", hub)
        monkeypatch.setattr(s, "CORE", core)
        monkeypatch.setattr(s, "MANIFEST", manifest_path)

        (hub / "hooks").mkdir(parents=True)
        (core / "hooks").mkdir(parents=True)
        (hub / "hooks" / "auto-git.sh").write_text("#!/bin/bash\necho hub\n", encoding="utf-8")
        (core / "hooks" / "auto-git.sh").write_text("#!/bin/bash\necho hub\n", encoding="utf-8")
        _write_manifest(manifest_path, {"synced": {"hooks": ["auto-git.sh"]}})

        report = s.check()
        assert [f"{r['kind']}/{r['name']}" for r in report["ok"]] == ["hooks/auto-git.sh"]
        assert report["drifted"] == []
