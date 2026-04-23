"""Tests for SHOULD-HAVE batch (REQ-S001, S002, S003, S005, S006) + COULD-HAVE
(REQ-C002, C004) of the three-lane test pipeline.

Static checks only — verify the documentation declares the new flags/options
correctly. Runtime behavior testing happens via /agent-evaluator scenarios
(not yet authored for these flags) and end-to-end smoke runs.
"""

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = REPO_ROOT / "core" / ".claude"
AGENTS_DIR = CORE_CLAUDE / "agents"
SKILLS_DIR = CORE_CLAUDE / "skills"
CONFIG_DIR = CORE_CLAUDE / "config"


# ── REQ-S001: --only-issues N,M flag ─────────────────────────────────────────


def test_t2a_documents_only_issues_flag():
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "--only-issues" in body, "T2A MUST document --only-issues flag (REQ-S001)"
    assert "filter-test-ids" in body or "filtered set" in body, (
        "T2A must explain how --only-issues propagates to scout"
    )


def test_test_pipeline_yml_lists_only_issues_in_cli_flags():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert "cli_flags" in cfg, "test-pipeline.yml must declare cli_flags block"
    assert "only_issues" in cfg["cli_flags"]
    assert "REQ-S001" in cfg["cli_flags"]["only_issues"]["spec_ref"]


# ── REQ-S002: --update-baselines flag ────────────────────────────────────────


def test_t2a_documents_update_baselines_flag():
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "--update-baselines" in body, "T2A MUST document --update-baselines flag (REQ-S002)"


def test_healer_nn_includes_update_baselines_gating():
    body = (AGENTS_DIR / "test-healer-agent.md").read_text(encoding="utf-8")
    assert "update_baselines" in body, "Healer NON-NEGOTIABLE MUST cover update_baselines gating"
    assert "BASELINE_DRIFT_INTENTIONAL" in body


def test_test_pipeline_yml_lists_update_baselines_in_cli_flags():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert "update_baselines" in cfg["cli_flags"]
    assert "REQ-S002" in cfg["cli_flags"]["update_baselines"]["spec_ref"]


# ── REQ-S003: test-track-overrides.yml template ─────────────────────────────


def test_test_track_overrides_example_exists():
    template = CONFIG_DIR / "test-track-overrides.yml.example"
    assert template.exists(), (
        f"REQ-S003: test-track-overrides.yml.example template must exist at {template}"
    )


def test_test_track_overrides_example_is_valid_yaml():
    template = CONFIG_DIR / "test-track-overrides.yml.example"
    data = yaml.safe_load(template.read_text(encoding="utf-8"))
    assert "overrides" in data
    assert isinstance(data["overrides"], list)
    assert len(data["overrides"]) >= 2, "Example should have ≥2 entries to demonstrate the format"
    for entry in data["overrides"]:
        assert "path" in entry
        assert "tracks" in entry
        assert isinstance(entry["tracks"], list)
        for track in entry["tracks"]:
            assert track in ("functional", "api", "ui"), f"Invalid track: {track}"


# ── REQ-S005: --autosquash flag for /serialize-fixes ─────────────────────────


def test_serialize_fixes_documents_autosquash():
    body = (SKILLS_DIR / "serialize-fixes" / "SKILL.md").read_text(encoding="utf-8")
    assert "--autosquash" in body, "/serialize-fixes MUST document --autosquash flag (REQ-S005)"
    assert "git rebase" in body and "--autosquash" in body
    assert "GIT_SEQUENCE_EDITOR" in body, (
        "Autosquash must run non-interactively via GIT_SEQUENCE_EDITOR"
    )


def test_serialize_fixes_safety_aborts_on_rebase_failure():
    body = (SKILLS_DIR / "serialize-fixes" / "SKILL.md").read_text(encoding="utf-8")
    assert "git rebase --abort" in body, "Autosquash must abort on rebase failure to preserve original commits"


def test_t2a_documents_autosquash_flag():
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "--autosquash" in body, "T2A MUST document --autosquash flag propagation (REQ-S005)"


# ── REQ-S006: UI lane checkpoint optimization ────────────────────────────────


def test_ui_lane_checkpoint_documented_in_t2a():
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "ui-tests-complete.flag" in body, "T2A MUST document the checkpoint flag (REQ-S006)"
    assert "use_checkpoint" in body or "REQ-S006" in body


def test_ui_lane_use_checkpoint_in_config():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert "use_checkpoint" in cfg["lanes"]["ui"], "lanes.ui.use_checkpoint must be declared"
    # Default should be false (opt-in optimization)
    assert cfg["lanes"]["ui"]["use_checkpoint"] is False


# ── REQ-C002: Slack notification on pipeline-fix-failed ─────────────────────


def test_escalation_report_documents_slack_notification():
    body = (SKILLS_DIR / "escalation-report" / "SKILL.md").read_text(encoding="utf-8")
    assert "SLACK_WEBHOOK_URL" in body, "/escalation-report MUST document Slack integration (REQ-C002)"
    assert "REQ-C002" in body


def test_escalation_report_slack_failure_is_non_fatal():
    body = (SKILLS_DIR / "escalation-report" / "SKILL.md").read_text(encoding="utf-8")
    # Slack failure must not abort the escalation report
    assert "best-effort" in body.lower() or "non-fatal" in body.lower() or "fail-soft" in body.lower()


# ── REQ-C004: CODEOWNERS auto-assign ─────────────────────────────────────────


def test_escalation_report_documents_codeowners_assign():
    body = (SKILLS_DIR / "escalation-report" / "SKILL.md").read_text(encoding="utf-8")
    assert "CODEOWNERS" in body, "/escalation-report MUST document CODEOWNERS auto-assign (REQ-C004)"
    assert "REQ-C004" in body
    assert "gh issue edit" in body and "add-assignee" in body


def test_escalation_report_codeowners_failure_is_non_fatal():
    body = (SKILLS_DIR / "escalation-report" / "SKILL.md").read_text(encoding="utf-8")
    # Auto-assign failure must not abort
    assert "best-effort" in body.lower() or "MUST NOT abort" in body
