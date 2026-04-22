"""Content assertions for the Playwright-only scope of /e2e-visual-run.

These tests encode the acceptance criteria for the v3.0.0 scope cut: the skill
and its references must mention only Playwright, drop Cypress/Selenium/Detox/
Flutter, and the registry entry must be in sync with the SKILL.md version.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "core" / ".claude" / "skills" / "e2e-visual-run"
SKILL_MD = SKILL_DIR / "SKILL.md"
SCOUT_REF = SKILL_DIR / "references" / "scout-phase.md"
REGISTRY = REPO_ROOT / "registry" / "patterns.json"

OTHER_FRAMEWORKS = ["Cypress", "Selenium", "Detox", "Flutter"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter_version(text: str) -> str | None:
    match = re.search(r"^version:\s*\"?([^\"\n]+)\"?", text, re.MULTILINE)
    return match.group(1).strip() if match else None


# ── SKILL.md content assertions ─────────────────────────────────────────────


def test_skill_md_version_is_3_0_0():
    version = _parse_frontmatter_version(_read(SKILL_MD))
    assert version == "3.0.0", f"expected 3.0.0, got {version!r}"


@pytest.mark.parametrize("framework", OTHER_FRAMEWORKS)
def test_skill_md_does_not_support_non_playwright_frameworks(framework):
    """Non-Playwright frameworks may appear ONLY in scope-exclusion prose,
    never in support/capture/fallback instructions."""
    content = _read(SKILL_MD)
    # A support phrase names the framework as a *target* of instruction:
    # section headers, "for Cypress do X" fallbacks, config examples.
    # Scope-exclusion lists like "Cypress, Selenium, Detox, and Flutter"
    # are allowed because they clarify what is NOT supported.
    forbidden_support_phrases = [
        f"**{framework}**:",               # bold framework + colon = instruction
        f"### {framework}",                # subsection header
        f"{framework}: ",                  # inline framework instruction
        f"{framework}.config",             # references a framework config file
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


# ── scout-phase.md content assertions ───────────────────────────────────────


@pytest.mark.parametrize("framework", OTHER_FRAMEWORKS)
def test_scout_phase_does_not_support_non_playwright_frameworks(framework):
    """Same rule as SKILL.md: no support instructions for non-Playwright."""
    content = _read(SCOUT_REF)
    forbidden_support_phrases = [
        f"**{framework}**:",
        f"### {framework}",
        f"{framework}: ",
        f"{framework}.config",
        f"| {framework} |",                # framework row in a support table
    ]
    for phrase in forbidden_support_phrases:
        assert phrase not in content, (
            f"scout-phase.md still provides {framework} support via "
            f"phrase {phrase!r}"
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


# ── Audit-gap fixes: state-machine schema ───────────────────────────────────


def test_skill_md_declares_expected_changes_queue():
    """Gap B: EXPECTED_CHANGE verdict must have a declared queue in state schema."""
    content = _read(SKILL_MD)
    assert "expected_changes" in content, (
        "EXPECTED_CHANGE verdict has no declared queue in state schema"
    )


def test_skill_md_specifies_section_filter_semantics():
    """Gap P: section filter must define what a 'section' is."""
    content = _read(SKILL_MD).lower()
    # Accept any concrete definition: describe block, tag, file path, or grep
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
        "STEP 2 section filter must define section matching semantics"
    )


def test_skill_md_has_git_status_precheck_in_step_6():
    """Gap N: Step 6 commit must check git status before staging."""
    content = _read(SKILL_MD)
    # Look for a git-status-aware commit block
    assert "git status" in content.lower() or "only test files" in content.lower(), (
        "Step 6 commit lacks git-status pre-check or scoped staging discipline"
    )


def test_skill_md_has_flakiness_decay_or_probe_rule():
    """Gap C: quarantined flaky tests must have a recovery path."""
    content = _read(SKILL_MD).lower()
    has_recovery = any(
        term in content
        for term in ["probe run", "decay", "rehabilitat", "recovery"]
    )
    assert has_recovery, (
        "STEP 5 flakiness quarantine has no decay or probe-run rule — "
        "tests are permanently quarantined"
    )
