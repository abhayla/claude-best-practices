"""Tests for writing-skills upgrade and skill-evaluator creation.

Validates:
1. writing-skills SKILL.md edits (frontmatter, new sections, cross-references)
2. instruction-writing-patterns.md reference (8 patterns)
3. skill-evaluator SKILL.md (frontmatter, steps, modes)
4. skill-evaluator reference files (description-optimization, eval-driven-iteration)
5. Cross-references between writing-skills and skill-evaluator
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
HUB_SKILLS = ROOT / ".claude" / "skills"
WRITING_SKILLS = HUB_SKILLS / "writing-skills"
SKILL_EVALUATOR = HUB_SKILLS / "skill-evaluator"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter fields as a dict."""
    import yaml

    text = _read(path)
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match, f"No frontmatter in {path}"
    return yaml.safe_load(match.group(1))


# ── FILE 1: writing-skills SKILL.md ─────────────────────────────────────────


class TestWritingSkillsFrontmatter:
    """Frontmatter must include Agent in allowed-tools."""

    def test_allowed_tools_includes_agent(self):
        fm = _parse_frontmatter(WRITING_SKILLS / "SKILL.md")
        tools = fm.get("allowed-tools", "")
        assert "Agent" in tools, "writing-skills must have Agent in allowed-tools to invoke skill-evaluator"


class TestWritingSkillsNecessityCheck:
    """Step 1.1 skill necessity check must exist."""

    def test_necessity_check_section_exists(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Skill Necessity Check" in content

    def test_necessity_check_has_auto_task_generation(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Auto-generate" in content or "auto-generate" in content

    def test_necessity_check_has_without_skill_test(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "WITHOUT a skill" in content or "without a skill" in content or "without skill" in content.lower()


class TestWritingSkillsContextBudget:
    """Context budget guidance must exist after Step 2.2."""

    def test_context_budget_section_exists(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Context Budget" in content

    def test_token_target_mentioned(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "5,000" in content or "5000" in content

    def test_would_agent_get_wrong_test(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "agent get this wrong" in content.lower()

    def test_conditional_disclosure_guidance(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "conditional" in content.lower() or "when to load" in content.lower() or "if the API returns" in content


class TestWritingSkillsArtifactSynthesis:
    """Step 3.1b artifact synthesis must exist."""

    def test_artifact_synthesis_section_exists(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Synthesize from Project Artifacts" in content or "Project Artifacts" in content

    def test_warns_against_llm_only(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "LLM general knowledge" in content or "general knowledge" in content.lower()

    def test_lists_source_materials(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "runbook" in content.lower()
        assert "API specification" in content or "api specification" in content.lower() or "API spec" in content


class TestWritingSkillsInstructionPatternsPointer:
    """Step 2.5 must reference instruction-writing-patterns.md."""

    def test_pointer_exists(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "instruction-writing-patterns.md" in content


class TestWritingSkillsStep4TooNarrow:
    """Step 4.2 must warn about too-narrow skills."""

    def test_too_narrow_warning(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "too narrow" in content.lower() or "narrowly" in content.lower()


class TestWritingSkillsStep6Rewrite:
    """Step 6 must delegate to skill-evaluator autonomously."""

    def test_references_skill_evaluator(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "skill-evaluator" in content

    def test_auto_fix_routing_table(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Auto-Fix Routing" in content or "auto-fix" in content.lower()

    def test_iterate_until_pass(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Iterate Until PASS" in content or "iterate until PASS" in content.lower()

    def test_max_5_iterations(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "5 iteration" in content.lower() or "max 5" in content.lower()

    def test_single_human_approval_gate(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "approval" in content.lower()

    def test_informal_iteration_before_eval(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "informal" in content.lower() or "single pass" in content.lower() or "one real task" in content.lower()

    def test_agent_tool_invocation(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "Agent" in content and "skill-evaluator" in content


class TestWritingSkillsMustDo:
    """MUST DO / MUST NOT DO must include autonomy rules."""

    def test_must_invoke_via_agent(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "invoke" in content.lower() and "Agent tool" in content or "Agent" in content

    def test_must_not_ask_user_to_invoke(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "MUST NOT" in content and "skill-evaluator" in content


# ── FILE 2: instruction-writing-patterns.md ──────────────────────────────────


class TestInstructionWritingPatterns:
    """instruction-writing-patterns.md must have all 8 patterns."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.path = WRITING_SKILLS / "references" / "instruction-writing-patterns.md"
        self.content = _read(self.path)

    def test_file_exists(self):
        assert self.path.exists()

    def test_pattern_1_calibrating_control(self):
        assert "Calibrating Control" in self.content

    def test_pattern_2_gotchas(self):
        assert "Gotchas" in self.content

    def test_pattern_3_validation_loops(self):
        assert "Validation Loop" in self.content

    def test_pattern_4_plan_validate_execute(self):
        assert "Plan-Validate-Execute" in self.content or "Plan Validate Execute" in self.content

    def test_pattern_5_defaults_over_menus(self):
        assert "Defaults" in self.content and "Menu" in self.content

    def test_pattern_6_procedures_over_declarations(self):
        assert "Procedures" in self.content and "Declarations" in self.content

    def test_pattern_7_scripts(self):
        assert "Script" in self.content or "script" in self.content

    def test_pattern_7_agentic_design_table(self):
        assert "interactive prompt" in self.content.lower() or "No interactive" in self.content

    def test_pattern_8_checklists(self):
        assert "Checklist" in self.content

    def test_gotchas_placement_guidance(self):
        assert "BEFORE encountering" in self.content or "before encountering" in self.content.lower()

    def test_gotchas_iterative_improvement(self):
        assert "iterative" in self.content.lower() or "correction" in self.content.lower()


# ── FILE 3: skill-evaluator SKILL.md ────────────────────────────────────────


class TestSkillEvaluatorExists:
    """skill-evaluator directory and SKILL.md must exist."""

    def test_directory_exists(self):
        assert SKILL_EVALUATOR.is_dir()

    def test_skill_md_exists(self):
        assert (SKILL_EVALUATOR / "SKILL.md").exists()

    def test_references_dir_exists(self):
        assert (SKILL_EVALUATOR / "references").is_dir()


class TestSkillEvaluatorFrontmatter:
    """Frontmatter must have correct fields."""

    @pytest.fixture(autouse=True)
    def load_fm(self):
        self.fm = _parse_frontmatter(SKILL_EVALUATOR / "SKILL.md")

    def test_name_matches_directory(self):
        assert self.fm["name"] == "skill-evaluator"

    def test_description_starts_with_verb(self):
        desc = str(self.fm["description"]).strip()
        assert desc[0].isupper()

    def test_has_triggers(self):
        triggers = self.fm.get("triggers", [])
        assert len(triggers) >= 3

    def test_has_agent_in_tools(self):
        tools = self.fm.get("allowed-tools", "")
        assert "Agent" in tools

    def test_has_argument_hint(self):
        hint = self.fm.get("argument-hint", "")
        assert "trigger" in hint and "output" in hint and "full" in hint

    def test_type_is_workflow(self):
        assert self.fm.get("type") == "workflow"

    def test_version_is_semver(self):
        version = self.fm.get("version", "")
        assert re.match(r"^\d+\.\d+\.\d+$", version)


class TestSkillEvaluatorModes:
    """All 4 modes must be documented."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_trigger_mode(self):
        assert "trigger" in self.content.lower()

    def test_output_mode(self):
        assert "output" in self.content.lower()

    def test_full_mode(self):
        assert "full" in self.content.lower()

    def test_conflicts_mode(self):
        assert "conflicts" in self.content.lower()


class TestSkillEvaluatorTriggerEval:
    """Trigger evaluation must have 20 queries and cross-skill check."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_20_eval_queries(self):
        assert "10 should-trigger" in self.content and "10 should-not" in self.content

    def test_cross_skill_conflict_check(self):
        assert "cross-skill" in self.content.lower() or "Cross-skill" in self.content

    def test_trigger_regression_baseline(self):
        assert "regression" in self.content.lower()

    def test_fresh_validation_queries(self):
        assert "fresh" in self.content.lower() and "quer" in self.content.lower()

    def test_description_optimization_reference(self):
        assert "description-optimization.md" in self.content


class TestSkillEvaluatorOutputEval:
    """Output evaluation must cover scenarios, stress, assertions, benchmarks."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_skill_necessity_baseline(self):
        assert "necessity" in self.content.lower() or "baseline" in self.content.lower()

    def test_clean_context_requirement(self):
        assert "clean context" in self.content.lower() or "subagent" in self.content.lower()

    def test_stress_test(self):
        assert "stress test" in self.content.lower() or "adversarial" in self.content.lower()

    def test_assertions(self):
        assert "assertion" in self.content.lower()

    def test_benchmarks(self):
        assert "benchmark" in self.content.lower()

    def test_blind_comparison(self):
        assert "blind" in self.content.lower() and "comparison" in self.content.lower()

    def test_eval_driven_iteration_reference(self):
        assert "eval-driven-iteration.md" in self.content


class TestSkillEvaluatorDelegationMode:
    """Must support standalone and delegated invocation."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_standalone_vs_delegated(self):
        assert "standalone" in self.content.lower() or "delegated" in self.content.lower()

    def test_skip_human_review_when_delegated(self):
        content_lower = self.content.lower()
        assert "skip" in content_lower and "human review" in content_lower


class TestSkillEvaluatorReport:
    """Evaluation report must have locked format."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_locked_report_format(self):
        assert "SKILL EVALUATION REPORT" in self.content

    def test_report_has_trigger_section(self):
        assert "TRIGGER EVALUATION" in self.content

    def test_report_has_output_section(self):
        assert "OUTPUT EVALUATION" in self.content

    def test_report_has_verdict(self):
        assert "OVERALL VERDICT" in self.content

    def test_verdict_values(self):
        assert "PASS" in self.content and "FIX" in self.content and "FAIL" in self.content


class TestSkillEvaluatorMustDo:
    """MUST DO / MUST NOT DO sections required."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read(SKILL_EVALUATOR / "SKILL.md")

    def test_must_do_exists(self):
        assert "MUST DO" in self.content or "## MUST DO" in self.content

    def test_must_not_do_exists(self):
        assert "MUST NOT DO" in self.content or "## MUST NOT DO" in self.content

    def test_no_grade_without_evidence(self):
        assert "evidence" in self.content.lower()


# ── FILE 4: description-optimization.md ──────────────────────────────────────


class TestDescriptionOptimization:
    """description-optimization.md must cover all key topics."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.path = SKILL_EVALUATOR / "references" / "description-optimization.md"
        self.content = _read(self.path)

    def test_file_exists(self):
        assert self.path.exists()

    def test_triggering_explanation(self):
        assert "trigger" in self.content.lower()

    def test_imperative_phrasing(self):
        assert "imperative" in self.content.lower() or "Use this skill when" in self.content

    def test_1024_char_limit(self):
        assert "1024" in self.content

    def test_before_after_example(self):
        assert "Before" in self.content and "After" in self.content

    def test_eval_queries_20(self):
        assert "10 should-trigger" in self.content or "10+10" in self.content or "20" in self.content

    def test_train_validation_split(self):
        assert "train" in self.content.lower() and "validation" in self.content.lower()

    def test_optimization_loop(self):
        assert "optimization" in self.content.lower() or "loop" in self.content.lower()

    def test_fresh_validation(self):
        assert "fresh" in self.content.lower()

    def test_overfitting_warning(self):
        assert "overfit" in self.content.lower()


# ── FILE 5: eval-driven-iteration.md ────────────────────────────────────────


class TestEvalDrivenIteration:
    """eval-driven-iteration.md must cover all key topics."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.path = SKILL_EVALUATOR / "references" / "eval-driven-iteration.md"
        self.content = _read(self.path)

    def test_file_exists(self):
        assert self.path.exists()

    def test_test_case_design(self):
        assert "test case" in self.content.lower() or "Test Case" in self.content

    def test_evals_json(self):
        assert "evals.json" in self.content or "evals/" in self.content

    def test_workspace_structure(self):
        assert "workspace" in self.content.lower() or "iteration-" in self.content

    def test_clean_context(self):
        assert "clean context" in self.content.lower() or "subagent" in self.content.lower()

    def test_assertions_guidance(self):
        assert "assertion" in self.content.lower()

    def test_grading_with_evidence(self):
        assert "evidence" in self.content.lower()

    def test_blind_comparison(self):
        assert "blind" in self.content.lower()

    def test_execution_trace_review(self):
        assert "trace" in self.content.lower() and ("execution" in self.content.lower() or "diagnostic" in self.content.lower())

    def test_trace_diagnostic_patterns(self):
        assert "vague" in self.content.lower() or "multiple approaches" in self.content.lower()

    def test_adversarial_categories(self):
        assert "adversarial" in self.content.lower()

    def test_severity_scoring(self):
        assert "CRITICAL" in self.content and "MAJOR" in self.content and "MINOR" in self.content

    def test_iteration_loop(self):
        assert "iteration" in self.content.lower() or "loop" in self.content.lower()

    def test_stop_criteria(self):
        assert "stop" in self.content.lower() or "Stop" in self.content

    def test_generalize_not_patch(self):
        assert "generalize" in self.content.lower()

    def test_keep_lean(self):
        assert "lean" in self.content.lower() or "removing instruction" in self.content.lower()

    def test_human_review(self):
        assert "human review" in self.content.lower() or "Human Review" in self.content


# ── Cross-References ─────────────────────────────────────────────────────────


class TestCrossReferences:
    """Verify cross-references between files are consistent."""

    def test_writing_skills_references_skill_evaluator(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "skill-evaluator" in content

    def test_writing_skills_references_instruction_patterns(self):
        content = _read(WRITING_SKILLS / "SKILL.md")
        assert "instruction-writing-patterns.md" in content

    def test_skill_evaluator_references_description_optimization(self):
        content = _read(SKILL_EVALUATOR / "SKILL.md")
        assert "description-optimization.md" in content

    def test_skill_evaluator_references_eval_driven_iteration(self):
        content = _read(SKILL_EVALUATOR / "SKILL.md")
        assert "eval-driven-iteration.md" in content

    def test_no_broken_reference_paths_writing_skills(self):
        """All Read: references/*.md in writing-skills must point to existing files."""
        content = _read(WRITING_SKILLS / "SKILL.md")
        refs = re.findall(r'`references/([\w-]+\.md)`', content)
        # Filter out placeholders used in examples (e.g., X.md, api-errors.md in prose)
        placeholders = {"X.md", "api-errors.md"}
        for ref in refs:
            if ref in placeholders:
                continue
            path = WRITING_SKILLS / "references" / ref
            assert path.exists(), f"Broken reference: references/{ref} in writing-skills"

    def test_no_broken_reference_paths_skill_evaluator(self):
        """All Read: references/*.md in skill-evaluator must point to existing files."""
        content = _read(SKILL_EVALUATOR / "SKILL.md")
        refs = re.findall(r'`references/([\w-]+\.md)`', content)
        for ref in refs:
            path = SKILL_EVALUATOR / "references" / ref
            assert path.exists(), f"Broken reference: references/{ref} in skill-evaluator"
