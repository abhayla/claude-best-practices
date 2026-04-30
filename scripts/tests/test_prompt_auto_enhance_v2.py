"""TDD tests for Prompt Auto-Enhance v2.0 changes.

Validates the v2.0 contract:
- Grading rubric reference file exists with 6 dimensions x 5 levels
- SKILL.md has Step 0 grading, 11 failure categories, 3 guardrails
- Rule is slim (~40 lines), no duplicated content from skill
- Hook has grading trigger line
- Registry versions bumped to 2.0.0
- SSOT: no procedural duplication between rule and skill
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
HUB_CLAUDE = ROOT / ".claude"

SKILL_PATH = CORE_CLAUDE / "skills" / "prompt-auto-enhance" / "SKILL.md"
RUBRIC_PATH = CORE_CLAUDE / "skills" / "prompt-auto-enhance" / "references" / "grading-rubric.md"
RULE_PATH = CORE_CLAUDE / "rules" / "prompt-auto-enhance-rule.md"
HUB_RULE_PATH = HUB_CLAUDE / "rules" / "prompt-auto-enhance.md"
HOOK_PATH = CORE_CLAUDE / "hooks" / "prompt-enhance-reminder.sh"
HUB_HOOK_PATH = HUB_CLAUDE / "hooks" / "prompt-enhance-reminder.sh"
REGISTRY_PATH = ROOT / "registry" / "patterns.json"
HUB_SKILL_PATH = HUB_CLAUDE / "skills" / "prompt-auto-enhance" / "SKILL.md"
HUB_RUBRIC_PATH = HUB_CLAUDE / "skills" / "prompt-auto-enhance" / "references" / "grading-rubric.md"
RELIABILITY_PATH = CORE_CLAUDE / "skills" / "prompt-auto-enhance" / "references" / "prompt-reliability-scoring.md"
HUB_RELIABILITY_PATH = HUB_CLAUDE / "skills" / "prompt-auto-enhance" / "references" / "prompt-reliability-scoring.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_registry() -> dict:
    import json
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
#  1. GRADING RUBRIC REFERENCE FILE
# ══════════════════════════════════════════════════════════════════════════════


class TestGradingRubric:
    """The grading rubric reference must exist with all 6 dimensions."""

    def test_rubric_file_exists(self):
        assert RUBRIC_PATH.exists(), (
            f"Missing: {RUBRIC_PATH.relative_to(ROOT)} — "
            "grading-rubric.md must be created with all dimension anchors"
        )

    def test_rubric_has_all_six_dimensions(self):
        if not RUBRIC_PATH.exists():
            pytest.skip("rubric file not yet created")
        content = _read(RUBRIC_PATH)
        dimensions = [
            "Intent Clarity",
            "Context Sufficiency",
            "Constraint Precision",
            "Output Specification",
            "Role & Framing",
            "Example Grounding",
        ]
        missing = [d for d in dimensions if d not in content]
        assert missing == [], f"Rubric missing dimensions: {missing}"

    def test_rubric_has_scoring_anchors_for_all_levels(self):
        """v3.x rubric uses 1-10 scale with range anchors (1-2, 3-4, 5-6, 7-8, 9-10)."""
        if not RUBRIC_PATH.exists():
            pytest.skip("rubric file not yet created")
        content = _read(RUBRIC_PATH)
        ranges = ["1-2", "3-4", "5-6", "7-8", "9-10"]
        missing = [r for r in ranges if f"| {r}" not in content and f"|{r}" not in content]
        assert missing == [], f"Rubric missing scoring anchor for ranges: {missing}"

    def test_rubric_has_weights(self):
        if not RUBRIC_PATH.exists():
            pytest.skip("rubric file not yet created")
        content = _read(RUBRIC_PATH)
        weights = ["0.25", "0.20", "0.15", "0.10"]
        missing = [w for w in weights if w not in content]
        assert missing == [], f"Rubric missing weights: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
#  2. SKILL v2.0 STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillV2Structure:
    """SKILL.md must have Step 0 grading, 11 categories, and guardrails."""

    def test_skill_has_step_0_grading(self):
        content = _read(SKILL_PATH)
        assert "STEP 0" in content, "SKILL.md must have STEP 0 for Quick Grade"

    def test_skill_has_11_failure_categories(self):
        content = _read(SKILL_PATH)
        categories = [
            "VAGUE_INTENT",
            "MISSING_CONTEXT",
            "AMBIGUOUS_SCOPE",
            "CONFLICTING_CONSTRAINTS",
            "OVER_SCOPED",
            "UNDER_CONSTRAINED",
            "MISSING_OUTPUT_SPEC",
            "IMPLICIT_ASSUMPTIONS",
            "MISSING_STRUCTURE",
            "MISSING_ROLE",
            "MISSING_EXAMPLES",
        ]
        missing = [c for c in categories if c not in content]
        assert missing == [], f"SKILL.md missing categories: {missing}"

    def test_skill_has_six_grading_dimensions(self):
        content = _read(SKILL_PATH)
        dimensions = [
            "Intent Clarity",
            "Context Sufficiency",
            "Constraint Precision",
            "Output Specification",
            "Role & Framing",
            "Example Grounding",
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
        content = _read(SKILL_PATH)
        assert "floor" in content.lower() or "Floor" in content, (
            "SKILL.md must have floor rule for degenerate scores"
        )

    def test_skill_has_three_guardrails(self):
        content = _read(SKILL_PATH)
        guardrails = [
            "Max Changes Cap",
            "Intent Preservation",
            "Over-Constraint Detection",
        ]
        missing = [g for g in guardrails if g not in content]
        assert missing == [], f"SKILL.md missing guardrails: {missing}"

    def test_skill_has_weakening_language_category_b(self):
        """Category B: Claude 4.x aggressive enforcement anti-patterns."""
        content = _read(SKILL_PATH)
        assert "Category B" in content or "Claude 4.x" in content, (
            "SKILL.md must have Category B weakening language (Claude 4.x specific)"
        )

    def test_skill_has_weakening_language_category_c(self):
        """Category C: Output-side anti-patterns (sycophantic openers)."""
        content = _read(SKILL_PATH)
        assert "Category C" in content or "Output-Side" in content or "Sycophantic" in content.lower(), (
            "SKILL.md must have Category C weakening language (output-side)"
        )

    def test_skill_version_is_3_2_0(self):
        content = _read(SKILL_PATH)
        assert 'version: "3.2.0"' in content, (
            "SKILL.md version must be 3.2.0"
        )

    def test_skill_references_grading_rubric(self):
        content = _read(SKILL_PATH)
        assert "grading-rubric" in content, (
            "SKILL.md must reference grading-rubric.md"
        )

    def test_skill_has_grade_card_output(self):
        content = _read(SKILL_PATH)
        assert "Grade Card" in content or "grade card" in content.lower(), (
            "SKILL.md must have grade card output format"
        )

    def test_skill_has_clarification_gate_sequencing(self):
        content = _read(SKILL_PATH)
        assert "Clarification Gate" in content, (
            "SKILL.md must reference Clarification Gate sequencing"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  3. LEAN RULE (SSOT FIX)
# ══════════════════════════════════════════════════════════════════════════════


class TestLeanRule:
    """Rule must be slim (~40 lines) with no duplicated skill content."""

    def test_rule_line_count_under_100(self):
        content = _read(RULE_PATH)
        line_count = len(content.strip().splitlines())
        assert line_count <= 100, (
            f"Rule has {line_count} lines — must be <= 100 (target ~90 for v3.x). "
            "Move procedural content to the skill."
        )

    def test_rule_does_not_contain_failure_categories(self):
        """9 or 11 failure categories must NOT be listed in the rule."""
        content = _read(RULE_PATH)
        categories_in_rule = [
            cat for cat in [
                "VAGUE_INTENT", "MISSING_CONTEXT", "CONFLICTING_CONSTRAINTS",
                "OVER_SCOPED", "UNDER_CONSTRAINED", "MISSING_OUTPUT_SPEC",
                "AMBIGUOUS_SCOPE", "IMPLICIT_ASSUMPTIONS", "MISSING_STRUCTURE",
            ]
            if cat in content
        ]
        assert categories_in_rule == [], (
            f"Rule still contains failure categories: {categories_in_rule}. "
            "These belong in the skill, not the rule."
        )

    def test_rule_does_not_contain_strengthening_steps(self):
        """Diagnose/Map/Rewrite steps must NOT be in the rule."""
        content = _read(RULE_PATH)
        step_markers = ["1. **Diagnose**", "2. **Map**", "3. **Rewrite**", "4. **Show"]
        found = [s for s in step_markers if s in content]
        assert found == [], (
            f"Rule still contains strengthening step details: {found}. "
            "These belong in the skill."
        )

    def test_rule_has_clarification_gate(self):
        """Clarification Gate is UNIQUE to the rule — must remain."""
        content = _read(RULE_PATH)
        assert "Clarification Gate" in content, (
            "Rule must retain the Clarification Gate section (unique to rule)"
        )

    def test_rule_points_to_skill(self):
        """Rule must contain a pointer to /prompt-auto-enhance skill."""
        content = _read(RULE_PATH)
        assert "/prompt-auto-enhance" in content, (
            "Rule must point to /prompt-auto-enhance skill for the full workflow"
        )

    def test_rule_has_enhanced_indicator(self):
        content = _read(RULE_PATH)
        assert "*Enhanced:" in content, (
            "Rule must mandate the *Enhanced:* indicator"
        )

    def test_rule_hub_copy_matches_core(self):
        """Hub-only rule must match core rule."""
        if not HUB_RULE_PATH.exists():
            pytest.skip("hub rule copy not found")
        core_content = _read(RULE_PATH)
        hub_content = _read(HUB_RULE_PATH)
        assert core_content == hub_content, (
            "Hub rule (.claude/rules/prompt-auto-enhance.md) must match "
            "core rule (core/.claude/rules/prompt-auto-enhance-rule.md)"
        )

    def test_rule_version_is_3_0_0(self):
        content = _read(RULE_PATH)
        if "version:" in content:
            assert "3.0.0" in content, "Rule version must be 3.0.0"


# ══════════════════════════════════════════════════════════════════════════════
#  4. HOOK WITH GRADING TRIGGER
# ══════════════════════════════════════════════════════════════════════════════


class TestHookGradingTrigger:
    """Hook must include the grading pipeline trigger."""

    def test_hook_has_grading_trigger(self):
        content = _read(HOOK_PATH)
        assert "Grade" in content or "grade" in content.lower(), (
            "Hook must mention grading pipeline trigger"
        )

    def test_hook_has_enhanced_reminder(self):
        content = _read(HOOK_PATH)
        assert "*Enhanced:" in content or "Enhanced:" in content, (
            "Hook must remind about *Enhanced:* indicator"
        )

    def test_hook_has_tier1_reminder(self):
        content = _read(HOOK_PATH)
        assert "Tier 1" in content, (
            "Hook must remind about Tier 1 context gathering"
        )

    def test_hook_exits_zero(self):
        content = _read(HOOK_PATH)
        assert "exit 0" in content, "Hook must exit 0 (non-blocking)"

    def test_hook_hub_copy_matches_core(self):
        core_content = _read(HOOK_PATH)
        hub_content = _read(HUB_HOOK_PATH)
        assert core_content == hub_content, (
            "Hub hook must match core hook"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  4b. SKILL + REFERENCES HUB↔CORE PARITY (added 2026-04-30 — closes drift gap)
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillHubCoreParity:
    """Hub-private SKILL.md and references/ MUST match the distributable core copies.

    Without these tests, an author can update hub-private content (which the hub
    repo itself uses) and forget to promote the same content to core/ (which is
    what downstream projects receive via recommend.py / sync_to_projects.py /
    /update-practices). This pattern of drift was the root cause of the v3.x
    updates not reaching FIREKaro-Vue between 5a6ecff and 2026-04-30.
    """

    def test_skill_hub_copy_matches_core(self):
        if not HUB_SKILL_PATH.exists():
            pytest.skip("hub skill copy not found")
        core_content = _read(SKILL_PATH)
        hub_content = _read(HUB_SKILL_PATH)
        assert core_content == hub_content, (
            "Hub SKILL.md (.claude/skills/prompt-auto-enhance/SKILL.md) must match "
            "core SKILL.md (core/.claude/skills/prompt-auto-enhance/SKILL.md). "
            "If you updated one, sync the other."
        )

    def test_grading_rubric_hub_copy_matches_core(self):
        if not HUB_RUBRIC_PATH.exists():
            pytest.skip("hub rubric copy not found")
        core_content = _read(RUBRIC_PATH)
        hub_content = _read(HUB_RUBRIC_PATH)
        assert core_content == hub_content, (
            "Hub grading-rubric.md must match core grading-rubric.md"
        )

    def test_reliability_scoring_hub_copy_matches_core(self):
        if not HUB_RELIABILITY_PATH.exists():
            pytest.skip("hub reliability scoring copy not found")
        if not RELIABILITY_PATH.exists():
            pytest.skip("core reliability scoring copy not found")
        core_content = _read(RELIABILITY_PATH)
        hub_content = _read(HUB_RELIABILITY_PATH)
        assert core_content == hub_content, (
            "Hub prompt-reliability-scoring.md must match core copy"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  5. REGISTRY VERSION SYNC
# ══════════════════════════════════════════════════════════════════════════════


class TestRegistryVersionSync:
    """Registry versions must be bumped to 2.0.0 for both skill and rule."""

    def test_skill_registry_version_is_3_2_0(self):
        reg = _load_registry()
        entry = reg.get("prompt-auto-enhance", {})
        assert entry.get("version") == "3.2.0", (
            f"Registry 'prompt-auto-enhance' version is {entry.get('version')}, "
            "must be 3.2.0"
        )

    def test_rule_registry_version_is_3_0_0(self):
        reg = _load_registry()
        entry = reg.get("prompt-auto-enhance-rule", {})
        assert entry.get("version") == "3.0.0", (
            f"Registry 'prompt-auto-enhance-rule' version is {entry.get('version')}, "
            "must be 3.0.0"
        )

    def test_skill_frontmatter_version_matches_registry(self):
        reg = _load_registry()
        reg_version = reg.get("prompt-auto-enhance", {}).get("version", "")
        content = _read(SKILL_PATH)
        assert f'version: "{reg_version}"' in content, (
            f"SKILL.md frontmatter version must match registry version {reg_version}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  6. SSOT COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════


class TestSSOTCompliance:
    """No procedural duplication between rule and skill."""

    def test_no_xml_tag_reference_in_rule(self):
        content = _read(RULE_PATH)
        assert "<task>" not in content and "<context>" not in content, (
            "Rule must NOT contain XML tag reference — belongs in skill"
        )

    def test_no_before_after_template_in_rule(self):
        """Rule may MENTION before/after comparison as a step output, but MUST
        NOT contain the actual template (Before:/After: example block)."""
        content = _read(RULE_PATH)
        template_markers = [
            "Before:\n",
            "After:\n",
            "**Before:**",
            "**After:**",
            "## Before/After Template",
        ]
        found = [m for m in template_markers if m in content]
        assert found == [], (
            f"Rule contains before/after template content: {found}. "
            "Templates belong in the skill, not the rule."
        )

    def test_no_web_search_decision_tree_in_rule(self):
        content = _read(RULE_PATH)
        assert "Decision Tree" not in content, (
            "Rule must NOT contain web search decision tree — belongs in skill"
        )

    def test_rule_under_40_percent_of_skill(self):
        """Rule should be <15% of skill size (was ~25% = duplication)."""
        rule_lines = len(_read(RULE_PATH).strip().splitlines())
        skill_lines = len(_read(SKILL_PATH).strip().splitlines())
        ratio = rule_lines / skill_lines if skill_lines > 0 else 1.0
        assert ratio < 0.15, (
            f"Rule is {ratio:.0%} of skill size ({rule_lines}/{skill_lines} lines). "
            "Must be under 15% — indicates too much procedural content in rule."
        )
