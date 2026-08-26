"""T-370 dod item 2: config/gwd-skill-conformance-grandfather.yml is SHRINK-ONLY,
mirroring config/eval-coverage-grandfather.yml. Entries may be removed and ceilings
lowered as SKILL.md/the fleet drift is fixed; nothing may be added or raised.
"""
from pathlib import Path

import yaml

import scripts.gwd_skill_conformance as gc

ROOT = Path(__file__).resolve().parent.parent.parent
GRANDFATHER_PATH = ROOT / "config" / "gwd-skill-conformance-grandfather.yml"


def test_grandfather_file_exists_and_loads():
    assert GRANDFATHER_PATH.exists()
    data = yaml.safe_load(GRANDFATHER_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("max_bytes")


def test_adding_a_list_entry_is_a_violation():
    old = {"stale_paths": ["a"]}
    new = {"stale_paths": ["a", "b"]}
    violations = gc.grandfather_shrink_violations(old, new)
    assert any("stale_paths" in v for v in violations)


def test_removing_a_list_entry_is_allowed():
    old = {"stale_paths": ["a", "b"]}
    new = {"stale_paths": ["a"]}
    assert gc.grandfather_shrink_violations(old, new) == []


def test_raising_a_ceiling_is_a_violation():
    old = {"max_bytes": 66296}
    new = {"max_bytes": 70000}
    violations = gc.grandfather_shrink_violations(old, new)
    assert any("max_bytes" in v for v in violations)


def test_lowering_a_ceiling_is_allowed():
    old = {"max_bytes": 66296}
    new = {"max_bytes": 60000}
    assert gc.grandfather_shrink_violations(old, new) == []


def test_plugin_allowlist_dict_entries_compare_by_identity():
    old = {"plugin_skill_allowlist": [{"skill": "goal-creator", "path": "plugins/x/skills/goal-creator"}]}
    new_same = {"plugin_skill_allowlist": [{"skill": "goal-creator", "path": "plugins/x/skills/goal-creator", "note": "reworded"}]}
    assert gc.grandfather_shrink_violations(old, new_same) == []

    new_added = {
        "plugin_skill_allowlist": [
            {"skill": "goal-creator", "path": "plugins/x/skills/goal-creator"},
            {"skill": "another-skill", "path": "plugins/y/skills/another-skill"},
        ]
    }
    violations = gc.grandfather_shrink_violations(old, new_added)
    assert any("plugin_skill_allowlist" in v for v in violations)


def test_current_committed_grandfather_has_no_self_violations():
    """A file never violates itself — sanity check the comparison function is reflexive."""
    data = yaml.safe_load(GRANDFATHER_PATH.read_text(encoding="utf-8"))
    assert gc.grandfather_shrink_violations(data, data) == []
