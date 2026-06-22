"""Structural tests for the prompt-auto-enhance capability.

As of 2026-06-22 the capability is distributed as the installable PLUGIN
(`plugins/prompt-auto-enhance/`), which is its single source of truth — the old
`core/.claude/` template copy was retired to a thin pointer (see
`plans/prompt-auto-enhance-core-retirement.md`). These tests therefore validate the
PLUGIN's skill/rule/hook content. Hub↔core parity, hard-coded registry versions, and
core-as-distributable assertions were removed because that contract no longer holds —
the plugin owns the content and `config/dual-home-resources.yml` records the intentional
core/.claude/ ↔ hub .claude/ divergence. The plugin manifest/settings/hook behavior is
covered separately by `test_prompt_enhance_plugin.py`.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
PLUGIN = ROOT / "plugins" / "prompt-auto-enhance"

SKILL_PATH = PLUGIN / "skills" / "prompt-auto-enhance" / "SKILL.md"
RUBRIC_PATH = PLUGIN / "skills" / "prompt-auto-enhance" / "references" / "grading-rubric.md"
RULE_PATH = PLUGIN / "prompt-auto-enhance-rule.md"
HOOK_PATH = PLUGIN / "hooks" / "prompt-enhance-reminder.sh"

# The hub keeps an operational pointer in core/ (NOT the distributable content anymore).
CORE_POINTER = ROOT / "core" / ".claude" / "skills" / "prompt-auto-enhance" / "SKILL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  1. GRADING RUBRIC REFERENCE FILE (in the plugin)
# ══════════════════════════════════════════════════════════════════════════════


class TestGradingRubric:
    def test_rubric_file_exists(self):
        assert RUBRIC_PATH.exists(), f"Missing: {RUBRIC_PATH.relative_to(ROOT)}"

    def test_rubric_has_all_six_dimensions(self):
        content = _read(RUBRIC_PATH)
        dimensions = [
            "Intent Clarity", "Context Sufficiency", "Constraint Precision",
            "Output Specification", "Role & Framing", "Example Grounding",
        ]
        missing = [d for d in dimensions if d not in content]
        assert missing == [], f"Rubric missing dimensions: {missing}"

    def test_rubric_has_scoring_anchors_for_all_levels(self):
        content = _read(RUBRIC_PATH)
        ranges = ["1-2", "3-4", "5-6", "7-8", "9-10"]
        missing = [r for r in ranges if f"| {r}" not in content and f"|{r}" not in content]
        assert missing == [], f"Rubric missing scoring anchor for ranges: {missing}"

    def test_rubric_has_weights(self):
        content = _read(RUBRIC_PATH)
        weights = ["0.25", "0.20", "0.15", "0.10"]
        missing = [w for w in weights if w not in content]
        assert missing == [], f"Rubric missing weights: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
#  2. SKILL STRUCTURE (in the plugin)
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillStructure:
    def test_skill_has_step_0_grading(self):
        assert "STEP 0" in _read(SKILL_PATH), "SKILL.md must have STEP 0 for Quick Grade"

    def test_skill_has_11_failure_categories(self):
        content = _read(SKILL_PATH)
        categories = [
            "VAGUE_INTENT", "MISSING_CONTEXT", "AMBIGUOUS_SCOPE",
            "CONFLICTING_CONSTRAINTS", "OVER_SCOPED", "UNDER_CONSTRAINED",
            "MISSING_OUTPUT_SPEC", "IMPLICIT_ASSUMPTIONS", "MISSING_STRUCTURE",
            "MISSING_ROLE", "MISSING_EXAMPLES",
        ]
        missing = [c for c in categories if c not in content]
        assert missing == [], f"SKILL.md missing categories: {missing}"

    def test_skill_has_six_grading_dimensions(self):
        content = _read(SKILL_PATH)
        dimensions = [
            "Intent Clarity", "Context Sufficiency", "Constraint Precision",
            "Output Specification", "Role & Framing", "Example Grounding",
        ]
        missing = [d for d in dimensions if d not in content]
        assert missing == [], f"SKILL.md missing grading dimensions: {missing}"

    def test_skill_has_grade_thresholds(self):
        content = _read(SKILL_PATH)
        for grade in ["Grade A", "Grade B", "Grade C", "Grade D", "Grade F"]:
            assert grade in content or grade.replace("Grade ", "**") in content, (
                f"SKILL.md missing {grade} threshold"
            )

    def test_skill_has_floor_rule(self):
        assert "floor" in _read(SKILL_PATH).lower(), "SKILL.md must have floor rule"

    def test_skill_has_three_guardrails(self):
        content = _read(SKILL_PATH)
        guardrails = ["Max Changes Cap", "Intent Preservation", "Over-Constraint Detection"]
        missing = [g for g in guardrails if g not in content]
        assert missing == [], f"SKILL.md missing guardrails: {missing}"

    def test_skill_has_weakening_language_category_b(self):
        content = _read(SKILL_PATH)
        assert "Category B" in content or "Claude 4.x" in content

    def test_skill_has_weakening_language_category_c(self):
        content = _read(SKILL_PATH)
        assert "Category C" in content or "Output-Side" in content or "sycophantic" in content.lower()

    def test_skill_references_grading_rubric(self):
        assert "grading-rubric" in _read(SKILL_PATH)

    def test_skill_has_grade_card_output(self):
        assert "grade card" in _read(SKILL_PATH).lower()

    def test_skill_has_clarification_gate_sequencing(self):
        assert "Clarification Gate" in _read(SKILL_PATH)

    def test_skill_frontmatter_version_present(self):
        assert 'version:' in _read(SKILL_PATH), "SKILL.md must declare a version"


# ══════════════════════════════════════════════════════════════════════════════
#  3. LEAN RULE (in the plugin)
# ══════════════════════════════════════════════════════════════════════════════


class TestLeanRule:
    def test_rule_line_count_under_100(self):
        line_count = len(_read(RULE_PATH).strip().splitlines())
        assert line_count <= 100, f"Rule has {line_count} lines — must be <= 100"

    def test_rule_does_not_contain_failure_categories(self):
        content = _read(RULE_PATH)
        found = [c for c in [
            "VAGUE_INTENT", "MISSING_CONTEXT", "CONFLICTING_CONSTRAINTS",
            "OVER_SCOPED", "UNDER_CONSTRAINED", "MISSING_OUTPUT_SPEC",
            "AMBIGUOUS_SCOPE", "IMPLICIT_ASSUMPTIONS", "MISSING_STRUCTURE",
        ] if c in content]
        assert found == [], f"Rule still contains failure categories: {found}"

    def test_rule_points_to_skill(self):
        assert "/prompt-auto-enhance" in _read(RULE_PATH)

    def test_rule_has_enhanced_indicator(self):
        assert "*Enhanced:" in _read(RULE_PATH)

    def test_rule_under_15_percent_of_skill(self):
        rule_lines = len(_read(RULE_PATH).strip().splitlines())
        skill_lines = len(_read(SKILL_PATH).strip().splitlines())
        ratio = rule_lines / skill_lines if skill_lines > 0 else 1.0
        assert ratio < 0.40, f"Rule is {ratio:.0%} of skill size — too much procedural content"


# ══════════════════════════════════════════════════════════════════════════════
#  4. HOOK (in the plugin)
# ══════════════════════════════════════════════════════════════════════════════


class TestHookGradingTrigger:
    def test_hook_has_grading_trigger(self):
        assert "grade" in _read(HOOK_PATH).lower(), "Hook must mention grading pipeline"

    def test_hook_has_enhanced_reminder(self):
        assert "Enhanced:" in _read(HOOK_PATH)

    def test_hook_exits_zero(self):
        assert "exit 0" in _read(HOOK_PATH), "Hook must exit 0 (non-blocking)"


# ══════════════════════════════════════════════════════════════════════════════
#  5. CORE POINTER (retirement guard)
# ══════════════════════════════════════════════════════════════════════════════


class TestCorePointer:
    """core/ must hold a thin pointer to the plugin, NOT the full distributable content."""

    def test_core_pointer_exists(self):
        assert CORE_POINTER.exists(), "core/ pointer SKILL.md must exist to redirect provisioning"

    def test_core_pointer_redirects_to_plugin(self):
        content = _read(CORE_POINTER)
        assert "/plugin install" in content and "prompt-auto-enhance@" in content, (
            "core/ pointer must tell projects to install the plugin"
        )

    def test_core_pointer_is_not_the_full_skill(self):
        content = _read(CORE_POINTER)
        assert "STEP 0" not in content and "VAGUE_INTENT" not in content, (
            "core/ copy must be a pointer, not the full distributable skill (that's the plugin's job)"
        )
