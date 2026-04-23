"""Test that a default test-pipeline.yml ships in core/.claude/config/.

Runtime verification (2026-04-22) caught that `test-pipeline-agent` v3.0.0
references `config/test-pipeline.yml` for stage definitions, capture_proof
settings, and retry budget — but no such file was shipped by provisioning.
Downstream projects using `/test-pipeline` would hit a missing-config
error on first invocation.

The fix is to ship a default config alongside `e2e-pipeline.yml` under
`core/.claude/config/`, and reference it via the `.claude/config/`
convention the agent body documents.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_PIPELINE_CONFIG = REPO_ROOT / "core" / ".claude" / "config" / "test-pipeline.yml"


def test_default_test_pipeline_config_exists():
    """The hub must ship a default test-pipeline.yml so downstream projects
    can run /test-pipeline out of the box after provisioning."""
    assert TEST_PIPELINE_CONFIG.is_file(), (
        f"Missing default config: {TEST_PIPELINE_CONFIG}. "
        "Test-pipeline-agent v3 references this file; provisioning must "
        "install it alongside e2e-pipeline.yml for downstream projects."
    )


def test_default_test_pipeline_config_is_valid_yaml():
    data = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "config must be a YAML mapping"


def test_config_declares_pipeline_stages():
    """The agent reads stage definitions from this file; at minimum
    fix-loop → auto-verify → post-fix-pipeline must be declared."""
    data = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text(encoding="utf-8"))
    pipeline = data.get("pipeline", {})
    stages = pipeline.get("stages", [])
    assert stages, "config must declare pipeline.stages"

    stage_skills = {s.get("skill") for s in stages}
    required = {"fix-loop", "auto-verify", "post-fix-pipeline"}
    missing = required - stage_skills
    assert not missing, (
        f"Default stage list missing: {sorted(missing)}. "
        "test-pipeline-agent's fix-verify-commit sub-chain requires these "
        "three stages by default."
    )


def test_config_declares_retry_budget():
    data = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text(encoding="utf-8"))
    retry = data.get("retry", {})
    budget = retry.get("global_budget")
    assert isinstance(budget, int), (
        "config must declare retry.global_budget (integer) — agent reads "
        "this as the fallback budget in standalone mode"
    )
    assert 5 <= budget <= 30, (
        f"retry.global_budget={budget} — outside reasonable range [5, 30]. "
        "Default 15 per testing.md rule."
    )


def test_config_declares_capture_proof():
    """Used by /test-pipeline skill body (line 76)."""
    data = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text(encoding="utf-8"))
    capture_proof = data.get("capture_proof", {})
    assert "enabled" in capture_proof, (
        "config must declare capture_proof.enabled (boolean). Skill body "
        "reads this to decide whether to emit screenshot evidence."
    )


def test_config_declares_schema_version():
    """Consistent with e2e-pipeline.yml which declares state.schema_version."""
    data = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text(encoding="utf-8"))
    # Either top-level or nested under state — both acceptable
    has_version = (
        "schema_version" in data
        or data.get("state", {}).get("schema_version") is not None
    )
    assert has_version, (
        "config must declare a schema_version (top-level or state.schema_version) "
        "for safe cross-version resume behavior"
    )
