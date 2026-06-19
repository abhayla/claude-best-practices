"""Contract tests for the per-run state archive and require_git_remote polish.

Bug 10 (state overwrites): every pipeline run used to overwrite the canonical
state file, destroying cross-run audit. The archive step copies the final
state to a timestamped `runs/{run_id}/` directory AFTER completion, without
moving the canonical file. Callers that read the canonical path see no
behavior change.

Testbed's Bug 8 (require_git_remote): issue_creation needs to fail fast when
`gh auth status` is OK but no git origin exists, not silently skip.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "core" / ".claude" / "config" / "e2e-pipeline.yml"


@pytest.fixture(scope="module")
def config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_archive_enabled_by_default(config):
    assert config["state"].get("archive_enabled") is True, (
        "Archive must be on by default — silent opt-in doesn't preserve audit "
        "trail for teams that never edit config"
    )


def test_archive_max_runs_has_retention(config):
    max_runs = config["state"].get("archive_max_runs")
    assert isinstance(max_runs, int)
    assert 1 <= max_runs <= 1000, "archive_max_runs must be sensible bound"


def test_canonical_paths_unchanged(config):
    assert config["state"]["standalone_file"] == ".pipeline/e2e-state.json"
    assert (
        config["state"]["dispatched_file"]
        == ".workflows/testing-pipeline/e2e-state.json"
    )


def test_require_git_remote_present(config):
    issue_creation = config["issue_creation"]
    assert "require_git_remote" in issue_creation, (
        "issue_creation must support require_git_remote to fail fast when no "
        "origin exists (Bug 8 from testbed session)"
    )


def test_require_git_remote_defaults_to_true(config):
    assert config["issue_creation"]["require_git_remote"] is True, (
        "require_git_remote defaults true so silent-skip is opt-in, not "
        "opt-out — teams without GitHub remotes should set enabled=false "
        "rather than turning off the guard"
    )
