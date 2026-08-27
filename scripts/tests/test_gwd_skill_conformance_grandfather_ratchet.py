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


# --- T-371 (T-370C finding): the ratchet had a HOLE - nothing fed the shrink-only ---------
# comparison the BASE-branch copy, so a PR that raised a ceiling or grew the prose-only MUST
# count was green. These tests run the comparison against a real git ref via `git show`, and
# prove red-then-green in a throwaway repo (real commits, real `git show`, no mocks).

import subprocess

BASELINE_GRANDFATHER = "max_bytes: 30000\nmax_ungated_musts: 0\nstale_paths:\n  - a\n"
BASELINE_SKILL = """---
name: demo
---

## CRITICAL RULES

- MUST do the gated thing. gate:PREFLIGHT-OK
- MUST do the ungated thing. gate:PROSE-ONLY
"""


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True, text=True)


def _write(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    # -f: this machine's global gitignore excludes .claude/ (repo convention, see CLAUDE.md).
    _git(["add", "-f", rel], repo)


def _fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    _write(repo, gc.GRANDFATHER_PATH_REL if hasattr(gc, "GRANDFATHER_PATH_REL") else gc.GRANDFATHER_REL,
           BASELINE_GRANDFATHER)
    _write(repo, gc.SKILL_REL, BASELINE_SKILL)
    _git(["commit", "-q", "-m", "baseline"], repo)
    _git(["checkout", "-q", "-b", "feature"], repo)
    return repo


def test_base_ref_comparison_is_clean_when_nothing_grew(tmp_path):
    repo = _fixture_repo(tmp_path)
    assert gc.base_refs_readable(repo, ref="main")
    assert gc.ratchet_violations_vs_ref(repo, ref="main") == []


def test_raising_a_ceiling_on_the_branch_is_RED_against_the_base_ref(tmp_path):
    repo = _fixture_repo(tmp_path)
    _write(repo, gc.GRANDFATHER_REL, "max_bytes: 66296\nmax_ungated_musts: 0\nstale_paths:\n  - a\n")
    _git(["commit", "-q", "-m", "raise the ceiling"], repo)

    violations = gc.ratchet_violations_vs_ref(repo, ref="main")
    assert any("max_bytes" in v for v in violations), violations

    # GREEN again once the ceiling is put back (and lowering further stays allowed).
    _write(repo, gc.GRANDFATHER_REL, "max_bytes: 25000\nmax_ungated_musts: 0\nstale_paths:\n  - a\n")
    _git(["commit", "-q", "-m", "lower it instead"], repo)
    assert gc.ratchet_violations_vs_ref(repo, ref="main") == []


def test_adding_a_grandfather_entry_on_the_branch_is_RED_against_the_base_ref(tmp_path):
    repo = _fixture_repo(tmp_path)
    _write(repo, gc.GRANDFATHER_REL, "max_bytes: 30000\nmax_ungated_musts: 0\nstale_paths:\n  - a\n  - b\n")
    _git(["commit", "-q", "-m", "grandfather a new drift"], repo)
    assert any("stale_paths" in v for v in gc.ratchet_violations_vs_ref(repo, ref="main"))


def test_growing_the_prose_only_must_count_is_RED_against_the_base_ref(tmp_path):
    repo = _fixture_repo(tmp_path)
    _write(repo, gc.SKILL_REL, BASELINE_SKILL + "- MUST do a third thing. gate:PROSE-ONLY\n")
    _git(["commit", "-q", "-m", "add an unmechanised MUST"], repo)

    violations = gc.ratchet_violations_vs_ref(repo, ref="main")
    assert any("PROSE-ONLY" in v for v in violations), violations

    # GREEN once that new MUST cites a real gate id instead of the placeholder.
    _write(repo, gc.SKILL_REL, BASELINE_SKILL + "- MUST do a third thing. gate:PREFLIGHT-OK\n")
    _git(["commit", "-q", "-m", "wire it to a real gate"], repo)
    assert gc.ratchet_violations_vs_ref(repo, ref="main") == []


def test_an_ungated_must_counts_as_prose_only(tmp_path):
    """v0.9 had 26 MUSTs with no gate token at all; those are implicitly PROSE-ONLY, so
    swapping an explicit token for none must not read as a shrink."""
    repo = _fixture_repo(tmp_path)
    _write(repo, gc.SKILL_REL, BASELINE_SKILL + "- MUST do a third thing with no gate token.\n")
    _git(["commit", "-q", "-m", "add an ungated MUST"], repo)
    assert any("PROSE-ONLY" in v for v in gc.ratchet_violations_vs_ref(repo, ref="main"))


def test_live_repo_is_compared_against_origin_main_not_skipped():
    """The hole T-370C found: a green run must mean 'compared and clean'. When origin/main
    is fetchable here, assert the real comparison runs and passes."""
    if not gc.base_refs_readable(ROOT):
        import pytest
        pytest.skip("origin/main not readable in this checkout - nothing to compare against")
    assert gc.ratchet_violations_vs_ref(ROOT) == []
