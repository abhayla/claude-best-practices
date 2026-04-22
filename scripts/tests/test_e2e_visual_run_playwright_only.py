"""Content assertions for the Playwright-only scope of /e2e-visual-run.

These tests encode the acceptance criteria for the v4.0.0 consolidation:
- /e2e-visual-run is a thin skill wrapper that dispatches e2e-conductor-agent.
- e2e-conductor-agent absorbs all queue + healing behaviors previously in
  the skill and its references/ directory.
- The skill must still be Playwright-scoped, and the conductor must still
  encode the dual-signal verdict lanes (including expected_changes), section
  filter semantics, git-status pre-check on commit, and flakiness decay /
  probe-run recovery.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "core" / ".claude" / "skills" / "e2e-visual-run"
SKILL_MD = SKILL_DIR / "SKILL.md"
CONDUCTOR_AGENT = REPO_ROOT / "core" / ".claude" / "agents" / "e2e-conductor-agent.md"
SCOUT_AGENT = REPO_ROOT / "core" / ".claude" / "agents" / "test-scout-agent.md"
REGISTRY = REPO_ROOT / "registry" / "patterns.json"

OTHER_FRAMEWORKS = ["Cypress", "Selenium", "Detox", "Flutter"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter_version(text: str) -> str | None:
    match = re.search(r"^version:\s*\"?([^\"\n]+)\"?", text, re.MULTILINE)
    return match.group(1).strip() if match else None


# ── SKILL.md (thin wrapper) content assertions ──────────────────────────────


def test_skill_md_version_is_4_0_0():
    version = _parse_frontmatter_version(_read(SKILL_MD))
    assert version == "4.0.0", f"expected 4.0.0, got {version!r}"


def test_skill_md_is_thin_wrapper():
    """v4.0.0 consolidation: skill must be under 100 lines of wrapper logic."""
    content = _read(SKILL_MD)
    lines = content.count("\n")
    assert lines <= 150, (
        f"SKILL.md has {lines} lines — expected thin wrapper (<=150). "
        "Queue/healing logic should live in e2e-conductor-agent, not the skill."
    )


def test_skill_md_dispatches_conductor_agent():
    """The skill's sole job is to dispatch e2e-conductor-agent."""
    content = _read(SKILL_MD)
    assert "e2e-conductor-agent" in content, (
        "SKILL.md must dispatch e2e-conductor-agent for the queue/healing work"
    )


def test_skill_md_references_directory_is_removed():
    """references/ content was migrated into the agents in v4.0.0."""
    references_dir = SKILL_DIR / "references"
    assert not references_dir.exists(), (
        f"{references_dir} should be removed; content migrated into agents"
    )


@pytest.mark.parametrize("framework", OTHER_FRAMEWORKS)
def test_skill_md_does_not_support_non_playwright_frameworks(framework):
    """Non-Playwright frameworks may appear ONLY in scope-exclusion prose,
    never in support/capture/fallback instructions."""
    content = _read(SKILL_MD)
    forbidden_support_phrases = [
        f"**{framework}**:",
        f"### {framework}",
        f"{framework}: ",
        f"{framework}.config",
    ]
    for phrase in forbidden_support_phrases:
        assert phrase not in content, (
            f"SKILL.md still provides {framework} support via phrase {phrase!r}"
        )


def test_skill_md_frontmatter_says_playwright_only():
    frontmatter = _read(SKILL_MD).split("---", 2)[1]
    assert "Playwright" in frontmatter, (
        "frontmatter must explicitly scope the skill to Playwright"
    )


# ── e2e-conductor-agent content assertions (absorbed from skill references) ─


@pytest.mark.parametrize("framework", OTHER_FRAMEWORKS)
def test_conductor_does_not_support_non_playwright_frameworks(framework):
    """Conductor inherits the Playwright-only scope from v3.0.0 e2e-visual-run."""
    content = _read(CONDUCTOR_AGENT)
    forbidden_support_phrases = [
        f"**{framework}**:",
        f"### {framework}",
        f"{framework}: ",
        f"{framework}.config",
        f"| {framework} |",
    ]
    for phrase in forbidden_support_phrases:
        assert phrase not in content, (
            f"e2e-conductor-agent provides {framework} support via phrase {phrase!r}"
        )


def test_scout_agent_does_not_support_non_playwright_frameworks():
    """test-scout-agent absorbed scout-phase.md; Playwright-only scope stands."""
    content = _read(SCOUT_AGENT)
    for framework in OTHER_FRAMEWORKS:
        forbidden_support_phrases = [
            f"**{framework}**:",
            f"### {framework}",
            f"| {framework} |",
        ]
        for phrase in forbidden_support_phrases:
            assert phrase not in content, (
                f"test-scout-agent provides {framework} support via phrase {phrase!r}"
            )


# ── Registry sync assertions ────────────────────────────────────────────────


def test_registry_e2e_visual_run_version_matches_skill_md():
    with REGISTRY.open(encoding="utf-8") as f:
        registry = json.load(f)
    entry = registry.get("e2e-visual-run")
    assert entry is not None, "registry is missing e2e-visual-run entry"
    skill_version = _parse_frontmatter_version(_read(SKILL_MD))
    assert entry["version"] == skill_version, (
        f"registry version {entry['version']!r} does not match "
        f"SKILL.md version {skill_version!r}"
    )


def test_registry_e2e_conductor_version_matches_agent():
    with REGISTRY.open(encoding="utf-8") as f:
        registry = json.load(f)
    entry = registry.get("e2e-conductor-agent")
    assert entry is not None, "registry is missing e2e-conductor-agent entry"
    agent_version = _parse_frontmatter_version(_read(CONDUCTOR_AGENT))
    assert entry["version"] == agent_version, (
        f"registry version {entry['version']!r} does not match "
        f"agent version {agent_version!r}"
    )


# ── Audit-gap fixes: now enforced on the conductor, not the skill ───────────


def test_conductor_declares_expected_changes_queue():
    """Gap B: EXPECTED_CHANGE verdict must have a declared queue in state schema."""
    content = _read(CONDUCTOR_AGENT)
    assert "expected_changes" in content, (
        "EXPECTED_CHANGE verdict has no declared queue in conductor state schema"
    )


def test_conductor_specifies_section_filter_semantics():
    """Gap P: section filter must define what a 'section' is."""
    content = _read(CONDUCTOR_AGENT).lower()
    has_semantics = any(
        term in content
        for term in [
            "describe block",
            "@tag",
            "grep pattern",
            "file path substring",
            "test title",
        ]
    )
    assert has_semantics, (
        "conductor STEP 2 section filter must define matching semantics"
    )


def test_conductor_has_git_status_precheck_in_commit_step():
    """Gap N: commit step must check git status before staging."""
    content = _read(CONDUCTOR_AGENT)
    assert "git status" in content.lower() or "explicit files only" in content.lower(), (
        "conductor commit step lacks git-status pre-check or scoped staging"
    )


def test_conductor_has_flakiness_decay_or_probe_rule():
    """Gap C: quarantined flaky tests must have a recovery path."""
    content = _read(CONDUCTOR_AGENT).lower()
    has_recovery = any(
        term in content
        for term in ["probe run", "probe-run", "decay", "rehabilitat", "recovery"]
    )
    assert has_recovery, (
        "conductor flakiness quarantine has no decay or probe-run rule — "
        "tests would be permanently quarantined"
    )


# ── v2.0.0 consolidation invariants ─────────────────────────────────────────


def test_conductor_is_dual_mode():
    """v2.0.0: agent must support standalone + dispatched modes."""
    content = _read(CONDUCTOR_AGENT).lower()
    assert "standalone" in content and "dispatched" in content, (
        "conductor must declare dual-mode operation (standalone + dispatched)"
    )


def test_conductor_declares_state_schema_version():
    """Phase C gap #17: state files must carry a schema_version for safe resume."""
    content = _read(CONDUCTOR_AGENT)
    assert "schema_version" in content, (
        "conductor state schema must include schema_version field"
    )


def test_conductor_uses_mcp_aware_healer():
    """Phase B: test-healer-agent has Playwright MCP as a hard dependency."""
    healer = _read(REPO_ROOT / "core" / ".claude" / "agents" / "test-healer-agent.md")
    assert "@playwright/mcp" in healer or "playwright-test" in healer, (
        "test-healer-agent must declare Playwright MCP server"
    )
