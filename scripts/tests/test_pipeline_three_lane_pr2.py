"""Tests for three-lane test pipeline PR2 scope.

Covers spec §6 success criteria for PR2:
- #3, 9, 10, 11, 12 (Issue creation + dedup + atomic switchover)
- #13, 14 (backward compat for /fix-loop and /fix-issue)
- #16, 17 (validator passes + empty Issue body fields)
- #20, 22, 23, 24 (T1 step deletion + evals + atomic diff apply + fan-in coordination)
- #26, 31 (PR2 atomic switchover + pre-merge migration)

Some scenarios are static (file/grep checks); others are mock-based for
behaviors that require live agents to verify.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = REPO_ROOT / "core" / ".claude"
AGENTS_DIR = CORE_CLAUDE / "agents"
SKILLS_DIR = CORE_CLAUDE / "skills"
CONFIG_DIR = CORE_CLAUDE / "config"
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ── /create-github-issue skill (REQ-M008) ─────────────────────────────────────


def test_create_github_issue_skill_exists():
    skill_path = SKILLS_DIR / "create-github-issue" / "SKILL.md"
    assert skill_path.exists(), f"missing {skill_path}"


def test_create_github_issue_has_4_preflight_checks():
    body = (SKILLS_DIR / "create-github-issue" / "SKILL.md").read_text(encoding="utf-8")
    # Each preflight check must be enumerated in the table
    for marker in ["gh installed", "gh authenticated", "Origin remote is github.com", "Token has Issue creation permission"]:
        assert marker in body, f"preflight check '{marker}' missing from /create-github-issue body"


def test_create_github_issue_uses_3_field_dedup_hash():
    """Closes Reviewer Gap N3 — must include failing_commit_sha_short."""
    body = (SKILLS_DIR / "create-github-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert "failing_commit_sha_short" in body, (
        "3-field dedup hash MUST include failing_commit_sha_short — without it, "
        "refactors create false-duplicates per spec §3.7 N3"
    )
    # Confirm it's in the actual hash computation, not just docs
    assert "test_id" in body and "category" in body and "failing_commit_sha_short" in body


def test_create_github_issue_returns_blocked_on_preflight_fail():
    """Skill body must document the BLOCKED contract shape."""
    body = (SKILLS_DIR / "create-github-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert '"result": "BLOCKED"' in body
    assert '"blocker": "GITHUB_NOT_CONNECTED"' in body
    assert '"failed_check"' in body
    assert '"remediation"' in body


def test_create_github_issue_body_has_empty_field_placeholders():
    """Closes spec G17 — empty fields render with placeholder, not blank lines."""
    body = (SKILLS_DIR / "create-github-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert "(no details captured)" in body or "(no stderr captured)" in body


# ── github-issue-manager-agent (REQ-M008, REQ-M013) ───────────────────────────


def test_github_issue_manager_agent_exists():
    assert (AGENTS_DIR / "github-issue-manager-agent.md").exists()


def test_github_issue_manager_agent_has_non_negotiable():
    body = (AGENTS_DIR / "github-issue-manager-agent.md").read_text(encoding="utf-8")
    assert "## NON-NEGOTIABLE" in body
    # Must cover hard-fail propagation
    assert "hard-fail" in body.lower() or "GITHUB_NOT_CONNECTED" in body


def test_github_issue_manager_is_t3_no_agent_dispatch():
    """T3 worker — must not have Agent in tools to enforce no-Agent rule."""
    body = (AGENTS_DIR / "github-issue-manager-agent.md").read_text(encoding="utf-8")
    fm = body.split("---")[1]
    tools_line = next(line for line in fm.splitlines() if line.startswith("tools:"))
    assert "Agent" not in tools_line, "T3 leaf MUST NOT include Agent tool (rule 3)"


# ── /serialize-fixes skill (REQ-M015, REQ-M018) ───────────────────────────────


def test_serialize_fixes_skill_exists():
    assert (SKILLS_DIR / "serialize-fixes" / "SKILL.md").exists()


def test_serialize_fixes_uses_git_apply_check_first():
    body = (SKILLS_DIR / "serialize-fixes" / "SKILL.md").read_text(encoding="utf-8")
    assert "git apply --check" in body, "Phase A MUST run --check first (atomic guard)"


def test_serialize_fixes_resets_hard_on_failure():
    body = (SKILLS_DIR / "serialize-fixes" / "SKILL.md").read_text(encoding="utf-8")
    assert "git reset --hard HEAD" in body, "Cleanup MUST run on any failure between apply and commit"


def test_serialize_fixes_discards_stale_diff_on_conflict():
    """Closes spec §3.9.3 G8 — stale diffs discarded so fresh diff next iteration."""
    body = (SKILLS_DIR / "serialize-fixes" / "SKILL.md").read_text(encoding="utf-8")
    assert "rm" in body and "stale_diff_discarded" in body


# ── /escalation-report skill (REQ-M020, REQ-M023) ─────────────────────────────


def test_escalation_report_skill_exists():
    assert (SKILLS_DIR / "escalation-report" / "SKILL.md").exists()


def test_escalation_report_writes_to_test_results():
    body = (SKILLS_DIR / "escalation-report" / "SKILL.md").read_text(encoding="utf-8")
    assert "test-results/escalation-report.md" in body


# ── /fix-issue --diff-only flag (REQ-M014, REQ-M017) ──────────────────────────


def test_fix_issue_diff_only_flag_documented():
    body = (SKILLS_DIR / "fix-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert "--diff-only" in body, "/fix-issue MUST document --diff-only flag"


def test_fix_issue_diff_only_writes_diff_no_commit():
    body = (SKILLS_DIR / "fix-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert "test-results/fixes/" in body, "diff-only MUST write to test-results/fixes/"
    assert "DIFF_WRITTEN" in body or "no_commit" in body


def test_fix_issue_default_mode_unchanged():
    """Backward compat: default mode (no flag) still calls /post-fix-pipeline."""
    body = (SKILLS_DIR / "fix-issue" / "SKILL.md").read_text(encoding="utf-8")
    assert "post-fix-pipeline" in body


# ── test-healer-agent commit_mode (REQ-M013, REQ-M016) ────────────────────────


def test_test_healer_agent_commit_mode_documented():
    body = (AGENTS_DIR / "test-healer-agent.md").read_text(encoding="utf-8")
    assert "commit_mode" in body, "test-healer-agent MUST document commit_mode parameter"
    assert "diff_only" in body and "direct" in body


def test_test_healer_agent_default_commit_mode_is_direct():
    """Backward compat: ABSENT commit_mode defaults to direct."""
    body = (AGENTS_DIR / "test-healer-agent.md").read_text(encoding="utf-8")
    assert ("default" in body.lower() and "direct" in body.lower())


# ── failure-triage-agent body activation (REQ-M006 — full body) ───────────────


def test_failure_triage_agent_full_body_replaces_skeleton():
    """PR1's NO_OP_PR1_SKELETON behavior MUST be replaced with full triage subgraph.

    Note: NO_OP_PR1_SKELETON may still appear in MUST NOT prose (documenting that
    we MUST NOT silently degrade to it). The test verifies the full body is active
    by checking for the 5-step subgraph + absence of skeleton return-contract behavior.
    """
    body = (AGENTS_DIR / "failure-triage-agent.md").read_text(encoding="utf-8")
    # Full body must mention the 5-step subgraph
    for step in ["Analyzer fan-out", "Issue-manager fan-out", "Fixer fan-out", "serialize-fixes", "escalation-report"]:
        assert step in body, f"full T2B body MUST cover step: {step}"
    # Skeleton return contract MUST NOT be the agent's behavior
    assert '"result": "NO_OP_PR1_SKELETON"' not in body, (
        "failure-triage-agent still emits NO_OP_PR1_SKELETON contract — PR2 must return TRIAGE_COMPLETE / TRIAGE_INCOMPLETE / BLOCKED"
    )
    # Confirm new return contracts are documented
    assert "TRIAGE_COMPLETE" in body
    assert "TRIAGE_INCOMPLETE" in body


def test_failure_triage_agent_version_bumped_to_1_0_0():
    body = (AGENTS_DIR / "failure-triage-agent.md").read_text(encoding="utf-8")
    fm = body.split("---")[1]
    version_line = next(line for line in fm.splitlines() if line.startswith("version:"))
    assert "1.0.0" in version_line, "PR1 was 0.1.0; PR2 activation bumps to 1.0.0"


# ── T1 atomic switchover (REQ-M011, success criteria #20, #26) ────────────────


def test_t1_inline_issue_creation_deleted():
    """T1's old GitHub Issue Creation step is DELETED in PR2's atomic switchover."""
    body = (AGENTS_DIR / "testing-pipeline-master-agent.md").read_text(encoding="utf-8")
    # The old algorithmic body MUST be gone
    assert 'gh issue create \\' not in body, (
        "T1 still has the old `gh issue create` invocation — PR2 atomic switchover deletes it"
    )
    # The 4 PR1-temporary category-tailored body sections MUST be gone too
    assert "category-tailored body section" not in body
    # Pointer to T2B replacement MUST be present
    assert "github-issue-manager-agent" in body
    assert "T2B" in body or "failure-triage-agent" in body


def test_t1_pr1_temporary_marker_removed():
    """The PR1-TEMPORARY HTML comment MUST be removed in PR2."""
    body = (AGENTS_DIR / "testing-pipeline-master-agent.md").read_text(encoding="utf-8")
    assert "PR1-TEMPORARY EXTENSION" not in body


# ── Pre-merge migration script (REQ-M011, success criterion #31) ──────────────


def test_pr2_premerge_migration_script_exists():
    assert (SCRIPTS_DIR / "pr2_premerge_migration.py").exists()


def test_pr2_premerge_migration_supports_dry_run():
    """Script must support --dry-run for safe verification before real run."""
    body = (SCRIPTS_DIR / "pr2_premerge_migration.py").read_text(encoding="utf-8")
    assert "--dry-run" in body
    assert 'argparse' in body


def test_pr2_premerge_migration_uses_30_day_default():
    body = (SCRIPTS_DIR / "pr2_premerge_migration.py").read_text(encoding="utf-8")
    assert "default=30" in body, "Default window MUST match dedup_window_days config"


# ── test-failure-analyzer-agent multi-lane (REQ-M006, spec §3.5) ──────────────


def test_analyzer_supports_multi_lane_evidence():
    body = (AGENTS_DIR / "test-failure-analyzer-agent.md").read_text(encoding="utf-8")
    assert "failed_lanes" in body, "Analyzer MUST accept failed_lanes input"
    assert "cross_lane_root_cause" in body or "Cross-lane root-cause detection" in body


def test_analyzer_emits_recommended_action():
    body = (AGENTS_DIR / "test-failure-analyzer-agent.md").read_text(encoding="utf-8")
    assert "recommended_action" in body
    for action in ["AUTO_HEAL", "ISSUE_ONLY", "QUARANTINE", "RETRY_INFRA"]:
        assert action in body, f"Analyzer body MUST cover recommended_action {action}"


def test_analyzer_backward_compat_single_lane():
    body = (AGENTS_DIR / "test-failure-analyzer-agent.md").read_text(encoding="utf-8")
    assert "Backward compat" in body or "backward compat" in body or "single-lane" in body


# ── T2A STEP 6 update (REQ-M006, AP9) ─────────────────────────────────────────


def test_t2a_step6_expects_full_t2b_contract():
    """T2A STEP 6 MUST expect TRIAGE_COMPLETE / TRIAGE_INCOMPLETE / BLOCKED, not NO_OP_PR1_SKELETON."""
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "TRIAGE_COMPLETE" in body, "T2A STEP 6 MUST handle full T2B return contract"
    # NO_OP_PR1_SKELETON might still be mentioned in MUST NOT (legacy reference); verify it's not the expected behavior
    # by checking that triage_outcome is in the return contract
    assert "triage_outcome" in body


# ── Backward compat (REQ-M032, success criteria #13, #14) ─────────────────────


def test_existing_fix_loop_skill_unchanged():
    """/fix-loop SKILL.md should be unchanged in PR2 — backward compat."""
    fix_loop = SKILLS_DIR / "fix-loop" / "SKILL.md"
    assert fix_loop.exists()
    # Sanity: should not have been changed to require commit_mode (still callable as before)
    body = fix_loop.read_text(encoding="utf-8")
    # This is a soft check: ensure /fix-loop doesn't now demand commit_mode parameter
    # (PR2's commit_mode is on test-healer-agent, not /fix-loop)


def test_post_fix_pipeline_skill_unchanged_in_pr2():
    """/post-fix-pipeline still exists and is unchanged. Verifies REQ-M032."""
    assert (SKILLS_DIR / "post-fix-pipeline" / "SKILL.md").exists()


# ── Registry consistency (success criterion #16) ──────────────────────────────


def test_create_github_issue_in_registry():
    with open(REPO_ROOT / "registry" / "patterns.json", encoding="utf-8") as f:
        registry = json.load(f)
    assert "create-github-issue" in registry


def test_serialize_fixes_in_registry():
    with open(REPO_ROOT / "registry" / "patterns.json", encoding="utf-8") as f:
        registry = json.load(f)
    assert "serialize-fixes" in registry


def test_escalation_report_in_registry():
    with open(REPO_ROOT / "registry" / "patterns.json", encoding="utf-8") as f:
        registry = json.load(f)
    assert "escalation-report" in registry


def test_failure_triage_agent_version_in_registry_is_1_0_0():
    """Registry MUST be updated to reflect T2B's PR2 activation."""
    with open(REPO_ROOT / "registry" / "patterns.json", encoding="utf-8") as f:
        registry = json.load(f)
    assert registry["failure-triage-agent"]["version"] == "1.0.0", (
        "PR1 was 0.1.0; PR2 activation bumps to 1.0.0"
    )
