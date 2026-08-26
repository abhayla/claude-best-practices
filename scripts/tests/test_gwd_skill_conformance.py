"""T-370 dod item 1: SKILL.md<->live-fleet conformance ratchet.

Reads .claude/skills/get-work-done/SKILL.md and the live fleet checkout at
GWD_ROOT as fixtures for each other. Green today because every current drift
is named in config/gwd-skill-conformance-grandfather.yml (shrink-only, T-370
dod item 2); RED the moment a NEW drift appears. Skips entirely when
GWD_ROOT is unset — CI has no fleet checkout to conform against.
"""
import json
import os
from pathlib import Path

import pytest

import scripts.gwd_skill_conformance as gc

HUB = Path(__file__).resolve().parents[2]

GWD_ROOT = os.environ.get("GWD_ROOT")
pytestmark = pytest.mark.skipif(
    not GWD_ROOT,
    reason="GWD_ROOT env var unset -- no fleet checkout to conform against (expected in CI)",
)


@pytest.fixture(scope="module")
def gwd_root():
    return Path(GWD_ROOT)


@pytest.fixture(scope="module")
def skill_text():
    return gc.load_skill_text(HUB)


@pytest.fixture(scope="module")
def grandfather():
    return gc.load_grandfather(HUB)


def test_path_and_script_refs_exist(skill_text, gwd_root, grandfather):
    missing = set(gc.missing_path_refs(skill_text, gwd_root))
    allowed = set(grandfather.get("stale_paths", []))
    new_drift = missing - allowed
    assert not new_drift, (
        f"SKILL.md names paths/scripts that no longer exist and are not grandfathered: "
        f"{sorted(new_drift)}"
    )


def test_settings_keys_exist(skill_text, gwd_root):
    settings = json.loads((gwd_root / "settings.json").read_text(encoding="utf-8"))
    missing = gc.missing_settings_keys(skill_text, settings)
    assert not missing, f"SKILL.md names settings.<key> not present in settings.json: {missing}"


def test_preflight_exit_codes_bidirectional(skill_text, gwd_root, grandfather):
    preflight_text = (gwd_root / "preflight-guard.ps1").read_text(encoding="utf-8")
    undocumented, unknown = gc.exit_code_diff(skill_text, preflight_text)
    allowed_undocumented = set(grandfather.get("missing_preflight_exit_codes", []))
    new_undocumented = set(undocumented) - allowed_undocumented
    assert not new_undocumented, (
        f"preflight-guard.ps1 defines exit codes SKILL.md never mentions, not grandfathered: "
        f"{sorted(new_undocumented)}"
    )
    assert not unknown, (
        f"SKILL.md mentions exit codes preflight-guard.ps1's header table doesn't define: {unknown}"
    )


def test_at_most_one_claude_p_recipe(skill_text, grandfather):
    count = gc.count_claude_p_recipes(skill_text)
    allowed = grandfather.get("max_claude_p_recipes", 1)
    assert count <= allowed, (
        f"SKILL.md documents {count} `claude -p` launch recipes; ratchet allows <= {allowed} "
        f"(config/gwd-skill-conformance-grandfather.yml max_claude_p_recipes)"
    )


def test_skill_invocations_resolve(skill_text, grandfather):
    unresolved = gc.unresolved_skill_invocations(
        skill_text, HUB, grandfather.get("plugin_skill_allowlist", [])
    )
    assert not unresolved, (
        f"SKILL.md invokes /skill(s) not under .claude/skills/ and not in the documented "
        f"plugin allowlist (config/gwd-skill-conformance-grandfather.yml plugin_skill_allowlist): "
        f"{unresolved}"
    )


def test_byte_size_ratchet(skill_text, grandfather):
    size = gc.skill_byte_size(HUB)
    max_bytes = grandfather.get("max_bytes")
    assert max_bytes is not None, (
        "config/gwd-skill-conformance-grandfather.yml must seed max_bytes (shrink-only ratchet)"
    )
    assert size <= max_bytes, (
        f"SKILL.md is {size} bytes, over the shrink-only ratchet ceiling of {max_bytes} bytes "
        f"(config/gwd-skill-conformance-grandfather.yml max_bytes)"
    )
