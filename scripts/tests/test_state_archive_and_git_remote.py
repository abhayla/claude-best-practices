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
CONDUCTOR_PATH = REPO_ROOT / "core" / ".claude" / "agents" / "e2e-conductor-agent.md"


@pytest.fixture(scope="module")
def config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def conductor_body() -> str:
    return CONDUCTOR_PATH.read_text(encoding="utf-8")


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


def test_conductor_documents_archive_step(conductor_body):
    assert "runs/{run_id}" in conductor_body, (
        "Conductor must document the per-run archive path format"
    )
    assert "Archive per-run state snapshot" in conductor_body
    assert "COPY" in conductor_body or "copy" in conductor_body, (
        "Archive must COPY (not move) so canonical path stays for existing "
        "callers — backward compatibility is the point"
    )


def test_archive_step_is_non_destructive(conductor_body):
    archive_section_start = conductor_body.find("Archive per-run state snapshot")
    assert archive_section_start > 0
    # The archive block runs before the test-results write step. Grab a 1000-char
    # window and assert the canonical file is preserved.
    archive_section = conductor_body[archive_section_start : archive_section_start + 1000]
    assert "STAYS where it is" in archive_section or "stays" in archive_section, (
        "Archive step must explicitly state the canonical file is NOT moved"
    )
    assert "rm " not in archive_section.split("\n\n")[0] + archive_section.split("\n\n")[1], (
        "Archive step must not include rm/delete of canonical file"
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
