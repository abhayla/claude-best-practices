"""Tests for rule organization across .claude/rules/ and core/.claude/rules/.

Validates:
- No duplicate rules across hub and core directories
- Hub rules (.claude/rules/) are lean — only global always-on guardrails
- Core meta-rules target downstream project paths (not core/.claude/)
- No glob overlaps that cause excessive context loading
- Dual scope declarations are standardized
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
HUB_RULES_DIR = ROOT / ".claude" / "rules"
CORE_RULES_DIR = ROOT / "core" / ".claude" / "rules"


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    import yaml
    return yaml.safe_load(parts[1]) or {}


def _get_globs(path: Path) -> list[str]:
    """Extract glob patterns from a rule's frontmatter."""
    fm = _parse_frontmatter(path)
    raw = fm.get("globs") or fm.get("paths") or []
    if isinstance(raw, str):
        return [g.strip() for g in raw.split(",") if g.strip()]
    if isinstance(raw, list):
        return [str(g).strip() for g in raw]
    return []


def _is_global(path: Path) -> bool:
    """Check if a rule declares global scope."""
    content = path.read_text(encoding="utf-8")
    first_lines = "\n".join(content.splitlines()[:10])
    has_scope_global = "# Scope: global" in first_lines
    globs = _get_globs(path)
    has_wildcard = any(g == "**/*" for g in globs)
    return has_scope_global or has_wildcard


def _hub_rule_files() -> list[Path]:
    if not HUB_RULES_DIR.exists():
        return []
    return sorted(HUB_RULES_DIR.glob("*.md"))


def _core_rule_files() -> list[Path]:
    if not CORE_RULES_DIR.exists():
        return []
    return sorted(CORE_RULES_DIR.glob("*.md"))


# ── Test: No duplicate rules across directories ──────────────────────────────


class TestNoDuplicateRules:
    """Hub (.claude/rules/) and core (core/.claude/rules/) must not share
    rules with the same filename unless explicitly declared as shared.
    Shared rules are universal behavioral rules that apply to all projects."""

    # These global behavioral rules intentionally exist in both directories:
    # - core/ copy: distributable template for downstream projects
    # - .claude/ copy: active version for this hub repo
    ALLOWED_SHARED = {
        "claude-behavior.md",
        "context-management.md",
        "workflow.md",
    }

    def test_no_unexpected_duplicate_filenames(self):
        """Non-shared rule files must not exist in both directories."""
        hub_names = {f.name for f in _hub_rule_files()}
        core_names = {f.name for f in _core_rule_files()}
        duplicates = (hub_names & core_names) - self.ALLOWED_SHARED
        assert duplicates == set(), (
            f"Duplicate rules found in both .claude/rules/ and core/.claude/rules/: "
            f"{sorted(duplicates)}. Each rule must exist in exactly one directory "
            f"(unless added to ALLOWED_SHARED for universal behavioral rules)."
        )


# ── Test: Hub rules are lean ─────────────────────────────────────────────────


class TestHubRulesAreLean:
    """Hub rules should contain only always-on global guardrails.
    Verbose procedural content belongs in skills (loaded on-demand)."""

    # These are the only rules that should remain in .claude/rules/
    ALLOWED_HUB_RULES = {
        "claude-behavior.md",
        "context-management.md",
        "workflow.md",
        "prompt-auto-enhance.md",
    }

    def test_hub_rules_are_approved_set(self):
        """Only approved lean rules should exist in .claude/rules/."""
        actual = {f.name for f in _hub_rule_files()}
        unexpected = actual - self.ALLOWED_HUB_RULES
        assert unexpected == set(), (
            f"Unexpected rules in .claude/rules/: {sorted(unexpected)}. "
            f"Only {sorted(self.ALLOWED_HUB_RULES)} should be hub rules. "
            f"Move verbose rules to skills for on-demand loading."
        )

    def test_hub_rules_are_all_global(self):
        """Every hub rule must be global scope — no path-scoped rules in hub."""
        for rule in _hub_rule_files():
            assert _is_global(rule), (
                f"{rule.name}: Hub rule must be global scope. "
                f"Path-scoped rules belong in core/.claude/rules/ (distributable) "
                f"or in skills (on-demand)."
            )

    def test_hub_rules_total_lines_under_budget(self):
        """Total hub rules should be under 250 lines to minimize context load."""
        total = 0
        for rule in _hub_rule_files():
            total += len(rule.read_text(encoding="utf-8").splitlines())
        assert total <= 250, (
            f"Hub rules total {total} lines (budget: 250). "
            f"Move verbose content to skills for on-demand loading."
        )


# ── Test: Core meta-rules target downstream paths ────────────────────────────


class TestCoreMetaRuleGlobs:
    """Core meta-rules (pattern-portability, pattern-structure, etc.) must
    target .claude/**/*.md — not core/.claude/**/*.md — so they work in
    downstream projects where core/ doesn't exist."""

    META_RULES = [
        "pattern-portability.md",
        "pattern-self-containment.md",
        "pattern-structure.md",
        "rule-curation.md",
    ]

    def test_meta_rules_target_downstream_paths(self):
        """Meta-rules must use .claude/**/*.md globs, not core/.claude/**/*.md."""
        for name in self.META_RULES:
            path = CORE_RULES_DIR / name
            if not path.exists():
                continue
            globs = _get_globs(path)
            for g in globs:
                assert not g.startswith("core/"), (
                    f"{name}: Glob '{g}' targets core/ which doesn't exist in "
                    f"downstream projects. Use '.claude/**/*.md' instead."
                )


# ── Test: No glob overlaps that cause context pollution ──────────────────────


class TestNoGlobOverlaps:
    """Rules with overlapping globs load simultaneously, wasting context."""

    def test_tdd_rule_no_source_globs(self):
        """tdd-rule should only target test files, not source files."""
        path = CORE_RULES_DIR / "tdd-rule.md"
        if not path.exists():
            pytest.skip("tdd-rule.md not found")
        globs = _get_globs(path)
        source_globs = [g for g in globs if any(
            g.startswith(prefix) for prefix in ("src/", "lib/", "app/")
        )]
        assert source_globs == [], (
            f"tdd-rule.md has source-directory globs {source_globs} that overlap "
            f"with non-test rules. TDD guidance for source files belongs in the "
            f"/tdd skill. Keep only test-file globs."
        )

    def test_android_kotlin_not_global(self):
        """android-kotlin.md should be scoped to android dirs, not all .kt files."""
        path = CORE_RULES_DIR / "android-kotlin.md"
        if not path.exists():
            pytest.skip("android-kotlin.md not found")
        globs = _get_globs(path)
        overly_broad = [g for g in globs if g.startswith("**/*.kt")]
        assert overly_broad == [], (
            f"android-kotlin.md has overly broad globs {overly_broad} that shadow "
            f"android.md for all Kotlin files. Narrow to android-specific paths."
        )


# ── Test: Standardized scope declarations ────────────────────────────────────


class TestScopeDeclarations:
    """Rules should not have redundant dual scope declarations."""

    def test_no_dual_scope(self):
        """Rules with # Scope: global should not also have globs: ['**/*']."""
        for rule_dir in [HUB_RULES_DIR, CORE_RULES_DIR]:
            if not rule_dir.exists():
                continue
            for rule in rule_dir.glob("*.md"):
                content = rule.read_text(encoding="utf-8")
                first_lines = "\n".join(content.splitlines()[:10])
                has_scope_comment = "# Scope: global" in first_lines
                globs = _get_globs(rule)
                has_wildcard_glob = any(g == "**/*" for g in globs)
                assert not (has_scope_comment and has_wildcard_glob), (
                    f"{rule.parent.parent.name}/{rule.name}: Has both "
                    f"'# Scope: global' AND globs: ['**/*']. Use only "
                    f"'# Scope: global' for global rules (remove globs)."
                )


# ── Test: Hub-only rules not in core ─────────────────────────────────────────


class TestHubOnlyRulesNotInCore:
    """Rules specific to hub operations must not be in core/.claude/rules/."""

    HUB_ONLY_RULES = {
        "workflow-change-verification.md",
        "workflow-docs-sync.md",
        "workflow-quality-gate.md",
    }

    def test_hub_only_rules_not_distributed(self):
        """Hub-specific workflow rules must not exist in core/.claude/rules/."""
        core_names = {f.name for f in _core_rule_files()}
        misplaced = self.HUB_ONLY_RULES & core_names
        assert misplaced == set(), (
            f"Hub-only rules found in core/.claude/rules/: {sorted(misplaced)}. "
            f"These manage hub infrastructure and should not be distributed."
        )
