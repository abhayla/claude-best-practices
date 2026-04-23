"""Tests for REQ-C003 (single-PR fixer batching mode).

Static checks — verify the new skill exists with correct shape, T2A/T2B
declare the flag, and the documented behavior contract holds.
"""

from pathlib import Path
import yaml
import json

REPO_ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = REPO_ROOT / "core" / ".claude"
SKILLS_DIR = CORE_CLAUDE / "skills"
AGENTS_DIR = CORE_CLAUDE / "agents"
CONFIG_DIR = CORE_CLAUDE / "config"


def test_pipeline_fix_pr_skill_exists():
    skill = SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md"
    assert skill.exists(), f"REQ-C003: /pipeline-fix-pr skill must exist at {skill}"


def test_pipeline_fix_pr_uses_serialize_fixes_underneath():
    """Wrapper pattern: pipeline-fix-pr delegates atomic diff apply to /serialize-fixes."""
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "Skill(\"serialize-fixes\"" in body or "Skill(\"/serialize-fixes\"" in body or 'serialize-fixes"' in body, (
        "/pipeline-fix-pr MUST delegate diff application to /serialize-fixes (no reimplementation)"
    )


def test_pipeline_fix_pr_creates_predictable_branch_name():
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "pipeline-fixes/" in body, "Branch naming convention pipeline-fixes/{run_id} required (NN#4)"


def test_pipeline_fix_pr_never_auto_merges():
    """Per git-collaboration.md § 'Review Before Merge'."""
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "Never auto-merge" in body or "never auto-merge" in body.lower()
    assert "git-collaboration.md" in body, "MUST cite git-collaboration.md for the never-auto-merge rationale"


def test_pipeline_fix_pr_has_preflight_checks():
    """Same gh CLI preflight as /create-github-issue (gh installed/auth/origin/permission)."""
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "STEP 0" in body and "Preflight" in body
    assert "create-github-issue" in body, "Should reference /create-github-issue's preflight as the canonical pattern"


def test_pipeline_fix_pr_returns_to_original_branch():
    """NN#2 — caller invoked from a working branch; must return there."""
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "ORIGINAL_BRANCH" in body
    assert "git checkout \"$ORIGINAL_BRANCH\"" in body or "return to original branch" in body.lower()


def test_t2a_documents_fix_pr_mode_flag():
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "--fix-pr-mode" in body, "T2A MUST document --fix-pr-mode flag (REQ-C003)"
    assert "REQ-C003" in body


def test_t2a_routes_to_pipeline_fix_pr_when_flag_set():
    """T2A's STEP 4 documentation must mention the routing change when --fix-pr-mode."""
    body = (AGENTS_DIR / "test-pipeline-agent.md").read_text(encoding="utf-8")
    assert "/pipeline-fix-pr" in body, "T2A must document routing to /pipeline-fix-pr"


def test_t2b_documents_fix_pr_mode_branching():
    body = (AGENTS_DIR / "failure-triage-agent.md").read_text(encoding="utf-8")
    assert "/pipeline-fix-pr" in body, "T2B MUST document the conditional /pipeline-fix-pr invocation"
    assert "REQ-C003" in body


def test_test_pipeline_yml_lists_fix_pr_mode_flag():
    cfg = yaml.safe_load((CONFIG_DIR / "test-pipeline.yml").read_text(encoding="utf-8"))
    assert "fix_pr_mode" in cfg["cli_flags"], "fix_pr_mode flag must be declared in cli_flags block"
    assert "REQ-C003" in cfg["cli_flags"]["fix_pr_mode"]["spec_ref"]


def test_pipeline_fix_pr_in_registry():
    with open(REPO_ROOT / "registry" / "patterns.json", encoding="utf-8") as f:
        registry = json.load(f)
    assert "pipeline-fix-pr" in registry, "/pipeline-fix-pr must be registered"
    entry = registry["pipeline-fix-pr"]
    assert entry["type"] == "skill"
    assert entry["tier"] in ("must-have", "nice-to-have"), (
        f"tier must be valid (must-have or nice-to-have), got {entry['tier']}"
    )
    assert "serialize-fixes" in entry["dependencies"], "Should declare /serialize-fixes as dependency"


def test_pipeline_fix_pr_pr_label_pipeline_auto_fix():
    """Per CRITICAL RULES: must label PR with `pipeline-auto-fix` for filtering."""
    body = (SKILLS_DIR / "pipeline-fix-pr" / "SKILL.md").read_text(encoding="utf-8")
    assert "pipeline-auto-fix" in body, "PR must be labeled `pipeline-auto-fix` (per CRITICAL RULES)"
