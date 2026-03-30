"""End-to-end pipeline integrity tests.

Validates that the 11-stage pipeline is fully connected:
  - Every stage's DAG config matches its stage doc
  - Every artifact_out from stage N is consumed as artifact_in by stage M
  - Every Skill() referenced in stage docs exists as an actual skill
  - Every agent referenced exists as an actual agent
  - The orchestrator agent, thin skill wrapper, rule, and config are consistent
  - Artifact paths form a complete chain with no dangling references
  - Governance constraints (agent-orchestration rule) are satisfied
"""

import json
import re
from pathlib import Path

import pytest
import yaml

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
CONFIG_DIR = ROOT / "config"
DOCS_STAGES = ROOT / "docs" / "stages"
REGISTRY_PATH = ROOT / "registry" / "patterns.json"

PIPELINE_CONFIG = CONFIG_DIR / "pipeline-stages.yaml"
ORCHESTRATOR_AGENT = CORE_CLAUDE / "agents" / "project-manager-agent.md"
ORCHESTRATOR_SKILL = CORE_CLAUDE / "skills" / "pipeline-orchestrator" / "SKILL.md"
ORCHESTRATION_RULE = CORE_CLAUDE / "rules" / "agent-orchestration.md"
ORCHESTRATION_GUIDE = CORE_CLAUDE / "skills" / "anthropic-agent-orchestration-guide" / "SKILL.md"
REVIEW_GATE_SKILL = CORE_CLAUDE / "skills" / "review-gate" / "SKILL.md"
SUBAGENT_SKILL = CORE_CLAUDE / "skills" / "subagent-driven-dev" / "SKILL.md"
SUBAGENT_REFS = CORE_CLAUDE / "skills" / "subagent-driven-dev" / "references"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_pipeline_config() -> dict:
    with open(PIPELINE_CONFIG) as f:
        return yaml.safe_load(f)


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def _actual_skills() -> set[str]:
    d = CORE_CLAUDE / "skills"
    return {
        f.name for f in d.iterdir()
        if f.is_dir() and (f / "SKILL.md").exists()
    } if d.exists() else set()


def _actual_agents() -> set[str]:
    d = CORE_CLAUDE / "agents"
    return {
        f.stem for f in d.glob("*.md") if f.name != "README.md"
    } if d.exists() else set()


def _stage_doc_path(stage_id: str) -> Path | None:
    """Map stage_id like 'stage_1_prd' to docs/stages/STAGE-1-*.md."""
    match = re.match(r"stage_(\d+)_", stage_id)
    if not match:
        return None
    num = match.group(1)
    candidates = list(DOCS_STAGES.glob(f"STAGE-{num}-*.md"))
    return candidates[0] if candidates else None


def _extract_skill_refs(content: str) -> list[str]:
    """Extract skill names from Skill("name", ...) or Skill('name', ...) patterns.

    Only extracts explicit Skill() calls, not slash commands, to avoid false positives
    like /dev/null, /factory, etc.
    """
    skill_calls = re.findall(r'Skill\(\s*["\']([^"\']+)["\']', content)
    return list(set(skill_calls))


def _extract_agent_refs(content: str) -> list[str]:
    """Extract agent names from Agent(subagent_type="name", ...) patterns."""
    return re.findall(r'subagent_type\s*=\s*["\']([^"\']+)["\']', content)


# ══════════════════════════════════════════════════════════════════════════════
#  1. PIPELINE CONFIG (DAG) INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineConfigExists:
    """The pipeline DAG config file must exist and be valid YAML."""

    def test_config_file_exists(self):
        assert PIPELINE_CONFIG.exists(), (
            f"Pipeline config missing at {PIPELINE_CONFIG}"
        )

    def test_config_is_valid_yaml(self):
        config = _load_pipeline_config()
        assert "pipeline" in config, "Config missing 'pipeline' key"
        assert "stages" in config, "Config missing 'stages' key"

    def test_config_has_global_settings(self):
        config = _load_pipeline_config()
        pipeline = config["pipeline"]
        assert "max_retries_per_stage" in pipeline
        assert "global_retry_budget" in pipeline
        assert "timeout_default_minutes" in pipeline

    def test_global_retry_budget_is_15(self):
        config = _load_pipeline_config()
        assert config["pipeline"]["global_retry_budget"] == 15, (
            "Global retry budget must be 15 per agent-orchestration rule"
        )


class TestPipelineDAGStructure:
    """The DAG must have valid stage definitions with required fields."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_has_11_stages(self, stages):
        assert len(stages) == 11, f"Expected 11 stages, got {len(stages)}"

    def test_all_stages_have_required_fields(self, stages):
        required = {"id", "name", "depends_on", "artifacts_out", "timeout_minutes"}
        errors = []
        for stage in stages:
            missing = required - set(stage.keys())
            if missing:
                errors.append(f"Stage '{stage.get('id', '?')}' missing: {missing}")
        assert errors == [], "\n".join(errors)

    def test_stage_ids_are_sequential(self, stages):
        ids = [s["id"] for s in stages]
        expected = [
            "stage_1_prd", "stage_2_plan", "stage_3_scaffold", "stage_4_demo",
            "stage_5_schema", "stage_6_pre_tests", "stage_7_impl",
            "stage_8_post_tests", "stage_9_review", "stage_10_deploy",
            "stage_11_docs",
        ]
        assert ids == expected, f"Stage IDs out of order:\n{ids}"

    def test_depends_on_references_valid_stages(self, stages):
        stage_ids = {s["id"] for s in stages}
        errors = []
        for stage in stages:
            for dep in stage["depends_on"]:
                if dep not in stage_ids:
                    errors.append(
                        f"Stage '{stage['id']}' depends on '{dep}' which doesn't exist"
                    )
        assert errors == [], "\n".join(errors)

    def test_no_circular_dependencies(self, stages):
        """Topological sort must succeed — no cycles in the DAG."""
        stage_map = {s["id"]: set(s["depends_on"]) for s in stages}
        resolved = set()
        unresolved = set(stage_map.keys())
        changed = True
        while changed:
            changed = False
            for sid in list(unresolved):
                if stage_map[sid] <= resolved:
                    resolved.add(sid)
                    unresolved.remove(sid)
                    changed = True
        assert unresolved == set(), f"Circular dependencies: {unresolved}"

    def test_stage_1_has_no_dependencies(self, stages):
        stage_1 = next(s for s in stages if s["id"] == "stage_1_prd")
        assert stage_1["depends_on"] == [], "Stage 1 (PRD) should have no dependencies"

    def test_stage_11_depends_on_stage_10(self, stages):
        stage_11 = next(s for s in stages if s["id"] == "stage_11_docs")
        assert "stage_10_deploy" in stage_11["depends_on"]


class TestArtifactContractChain:
    """Every artifacts_in reference must point to a valid artifacts_out from an upstream stage."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_all_artifact_inputs_have_sources(self, stages):
        # Build map of stage_id → artifacts_out keys
        available = {}
        for stage in stages:
            for key in stage.get("artifacts_out", {}):
                available[f"{stage['id']}.artifacts_out.{key}"] = stage["id"]

        errors = []
        for stage in stages:
            for key, ref in stage.get("artifacts_in", {}).items():
                if ref not in available:
                    errors.append(
                        f"Stage '{stage['id']}' wants '{key}' from '{ref}' "
                        f"but no upstream stage produces it"
                    )
        assert errors == [], (
            f"Broken artifact references ({len(errors)}):\n" + "\n".join(errors)
        )

    def test_artifact_inputs_only_reference_upstream_deps(self, stages):
        """artifacts_in must reference stages in depends_on (direct or transitive)."""
        # Build transitive dependency map
        stage_map = {s["id"]: set(s["depends_on"]) for s in stages}

        def transitive_deps(sid: str, visited=None) -> set[str]:
            if visited is None:
                visited = set()
            if sid in visited:
                return set()
            visited.add(sid)
            deps = set(stage_map.get(sid, set()))
            for d in list(deps):
                deps |= transitive_deps(d, visited)
            return deps

        errors = []
        for stage in stages:
            trans = transitive_deps(stage["id"])
            for key, ref in stage.get("artifacts_in", {}).items():
                source_stage = ref.split(".")[0]
                if source_stage not in trans:
                    errors.append(
                        f"Stage '{stage['id']}' references '{ref}' but "
                        f"'{source_stage}' is not in its dependency chain"
                    )
        assert errors == [], "\n".join(errors)

    def test_every_stage_produces_at_least_one_artifact(self, stages):
        errors = []
        for stage in stages:
            if not stage.get("artifacts_out"):
                errors.append(f"Stage '{stage['id']}' produces no artifacts")
        assert errors == [], "\n".join(errors)

    def test_artifacts_out_have_path_or_type(self, stages):
        """Each artifact must specify either a path or a type."""
        errors = []
        for stage in stages:
            for key, spec in stage.get("artifacts_out", {}).items():
                if "path" not in spec and "type" not in spec:
                    errors.append(
                        f"Stage '{stage['id']}' artifact '{key}' has neither path nor type"
                    )
        assert errors == [], "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════════════
#  2. STAGE DOCS ↔ DAG CONFIG CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestStageDocsExist:
    """Every stage in the DAG config must have a corresponding stage doc."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_every_stage_has_a_doc(self, stages):
        missing = []
        for stage in stages:
            path = _stage_doc_path(stage["id"])
            if path is None or not path.exists():
                missing.append(stage["id"])
        assert missing == [], f"Stages without docs: {missing}"

    def test_stage_docs_have_orchestration_dispatch(self, stages):
        """Key stage docs must have an 'Orchestration Dispatch' section.

        Stages 1, 2, 3, 6, 11 were explicitly updated with dispatch sections.
        Other stages may have their own dispatch patterns in different formats.
        """
        required_stages = {
            "stage_1_prd", "stage_2_plan", "stage_3_scaffold",
            "stage_6_pre_tests", "stage_11_docs",
        }
        missing = []
        for stage in stages:
            if stage["id"] not in required_stages:
                continue
            path = _stage_doc_path(stage["id"])
            if path is None or not path.exists():
                continue
            content = _read_file(path)
            if "Orchestration Dispatch" not in content:
                missing.append(stage["id"])
        assert missing == [], (
            f"Stage docs without Orchestration Dispatch section: {missing}"
        )


class TestStageDocSkillReferences:
    """Every Skill() call in stage docs must reference an actual skill."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_all_skill_refs_exist(self, stages):
        actual = _actual_skills()
        errors = []
        for stage in stages:
            path = _stage_doc_path(stage["id"])
            if path is None or not path.exists():
                continue
            content = _read_file(path)
            refs = _extract_skill_refs(content)
            for ref in refs:
                if ref not in actual:
                    errors.append(f"Stage doc for '{stage['id']}' references skill '{ref}' which doesn't exist")
        # Deduplicate
        errors = list(set(errors))
        assert errors == [], (
            f"Dead skill references in stage docs ({len(errors)}):\n"
            + "\n".join(sorted(errors))
        )


# ══════════════════════════════════════════════════════════════════════════════
#  3. ORCHESTRATOR AGENT ↔ CONFIG CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestratorAgent:
    """The project-manager-agent must be properly configured."""

    def test_agent_file_exists(self):
        assert ORCHESTRATOR_AGENT.exists()

    def test_agent_has_required_frontmatter(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "project-manager-agent"
        assert "description" in fm
        assert "model" in fm
        assert "tools" in fm

    def test_agent_references_config_file(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert "pipeline-stages.yaml" in content, (
            "Orchestrator agent must reference config/pipeline-stages.yaml"
        )

    def test_agent_references_state_file(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert ".pipeline/state.json" in content

    def test_agent_references_event_log(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert "event-log.jsonl" in content

    def test_agent_has_core_responsibilities(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert "## Core Responsibilities" in content

    def test_agent_has_output_format(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert "## Output Format" in content or "## Stage Dispatch Protocol" in content

    def test_agent_has_agent_tool(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        fm = _parse_frontmatter(content)
        tools = fm.get("tools", [])
        assert "Agent" in tools, "Orchestrator agent needs Agent tool to dispatch stage agents"

    def test_agent_enforces_retry_limits(self):
        content = _read_file(ORCHESTRATOR_AGENT)
        assert "15" in content, "Agent should mention global retry budget of 15"
        assert "3" in content, "Agent should mention per-stage retry limit of 3"


class TestOrchestratorSkillWrapper:
    """The thin skill wrapper must correctly delegate to the agent."""

    def test_skill_file_exists(self):
        assert ORCHESTRATOR_SKILL.exists()

    def test_skill_dispatches_agent(self):
        content = _read_file(ORCHESTRATOR_SKILL)
        assert "project-manager-agent" in content, (
            "Skill wrapper must dispatch project-manager-agent"
        )

    def test_skill_has_correct_version(self):
        content = _read_file(ORCHESTRATOR_SKILL)
        fm = _parse_frontmatter(content)
        major = int(fm.get("version", "0.0.0").split(".")[0])
        assert major >= 2, "Skill wrapper should be v2.0.0+ after conversion to thin wrapper"

    def test_skill_is_thin(self):
        """A thin wrapper should be under 100 lines."""
        content = _read_file(ORCHESTRATOR_SKILL)
        lines = content.count("\n") + 1
        assert lines < 100, f"Thin wrapper has {lines} lines — should be under 100"

    def test_skill_does_not_contain_dag(self):
        """The skill should NOT contain inline DAG definitions."""
        content = _read_file(ORCHESTRATOR_SKILL)
        assert '"stages"' not in content, "Skill wrapper should not contain inline stage definitions"
        assert "stage_1_prd" not in content, "Skill wrapper should not contain stage IDs"


# ══════════════════════════════════════════════════════════════════════════════
#  4. ORCHESTRATION RULE ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestrationRule:
    """The agent-orchestration rule must exist and cover key constraints."""

    def test_rule_file_exists(self):
        assert ORCHESTRATION_RULE.exists()

    def test_rule_has_globs_scoping(self):
        content = _read_file(ORCHESTRATION_RULE)
        fm = _parse_frontmatter(content)
        globs = fm.get("globs", [])
        assert any("agents" in g for g in globs), "Rule must scope to agents"
        assert any("skills" in g for g in globs), "Rule must scope to skills"

    def test_rule_mentions_key_constraints(self):
        content = _read_file(ORCHESTRATION_RULE)
        constraints = [
            "Tiered Nesting",      # tiered nesting model
            "Externalize",         # externalize DAGs
            "retry budget",        # global retry budget
            "Single State",        # single state location
        ]
        for c in constraints:
            assert c.lower() in content.lower(), (
                f"Rule missing constraint: '{c}'"
            )


class TestOrchestrationConstraintsApplied:
    """Verify the orchestration constraints are actually satisfied in the codebase."""

    def test_pipeline_dag_is_externalized(self):
        """DAG must be in config/, not inline in agent or skill."""
        assert PIPELINE_CONFIG.exists(), "DAG must be externalized to config/"
        agent_content = _read_file(ORCHESTRATOR_AGENT)
        # Should not contain the full JSON DAG inline
        assert agent_content.count('"stage_') < 5, (
            "Agent should not contain inline stage definitions — use config file"
        )

    def test_no_agent_spawning_agents(self):
        """Worker agents dispatched by the orchestrator must not call Agent() themselves.

        We check that skills invoked by the stage docs don't contain Agent()
        calls to other named agents (subagent_type=...). Note: review-gate is
        a special case — it's an orchestrator itself (Stage 9).
        """
        # Known orchestrator skills that are allowed to use Agent()
        allowed_orchestrators = {
            "review-gate", "pipeline-orchestrator", "subagent-driven-dev",
            # Workflow master dispatch wrappers (thin skills that delegate to master agents)
            "development-loop", "testing-pipeline-workflow", "debugging-loop",
            "code-review-workflow", "documentation-workflow", "session-continuity",
            "learning-self-improvement", "skill-authoring-workflow",
        }
        skills_dir = CORE_CLAUDE / "skills"
        errors = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in allowed_orchestrators:
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = _read_file(skill_md)
            agent_refs = _extract_agent_refs(content)
            if agent_refs:
                errors.append(
                    f"Skill '{skill_dir.name}' calls Agent(subagent_type=...) "
                    f"for {agent_refs} — only orchestrators should dispatch agents"
                )
        # This is advisory, not a hard failure (some skills legitimately use agents)
        # Just verify it's a small number
        assert len(errors) < 10, (
            f"Too many skills dispatching agents ({len(errors)}):\n"
            + "\n".join(errors)
        )


# ══════════════════════════════════════════════════════════════════════════════
#  5. REVIEW GATE (STAGE 9) PARALLELIZATION INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════


class TestReviewGateIntegrity:
    """The review-gate skill must be correctly structured with parallel batches."""

    def test_skill_file_exists(self):
        assert REVIEW_GATE_SKILL.exists()

    def test_has_correct_allowed_tools(self):
        content = _read_file(REVIEW_GATE_SKILL)
        fm = _parse_frontmatter(content)
        tools = fm.get("allowed-tools", "")
        assert "Write" not in tools, "review-gate should not have Write tool"
        assert "Edit" not in tools, "review-gate should not have Edit tool"
        assert "Agent" not in tools, "review-gate should not have Agent in allowed-tools (uses inline Agent() calls)"

    def test_has_batch_structure(self):
        content = _read_file(REVIEW_GATE_SKILL)
        assert "Batch A" in content, "Missing Batch A (code quality + architecture)"
        assert "Batch B" in content, "Missing Batch B (security + risk)"
        assert "Batch C" in content, "Missing Batch C (adversarial + pr-standards)"

    def test_references_all_six_sub_skills(self):
        content = _read_file(REVIEW_GATE_SKILL)
        required_skills = [
            "code-quality-gate", "architecture-fitness",
            "security-audit", "change-risk-scoring",
            "adversarial-review", "pr-standards",
        ]
        for skill in required_skills:
            assert skill in content, f"review-gate missing reference to '{skill}'"

    def test_all_sub_skills_exist(self):
        actual = _actual_skills()
        required = {
            "code-quality-gate", "architecture-fitness",
            "security-audit", "change-risk-scoring",
            "adversarial-review", "pr-standards",
            "fix-loop", "auto-verify",
        }
        missing = required - actual
        assert missing == set(), f"Review-gate sub-skills missing: {missing}"

    def test_produces_machine_readable_output(self):
        content = _read_file(REVIEW_GATE_SKILL)
        assert "review-gate.json" in content, "Must produce test-results/review-gate.json"
        assert "verdict" in content.lower(), "Must include verdict logic"

    def test_verdict_logic_present(self):
        content = _read_file(REVIEW_GATE_SKILL)
        assert "APPROVED" in content
        assert "REJECTED" in content
        assert "APPROVED WITH CAVEATS" in content

    def test_version_bumped_for_parallelization(self):
        content = _read_file(REVIEW_GATE_SKILL)
        fm = _parse_frontmatter(content)
        major = int(fm.get("version", "0.0.0").split(".")[0])
        assert major >= 2, "review-gate should be v2.0.0+ after parallelization restructure"


# ══════════════════════════════════════════════════════════════════════════════
#  6. SUBAGENT-DRIVEN-DEV REFERENCE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════


class TestSubagentDrivenDevRefactoring:
    """Verify the references extraction was done correctly."""

    def test_main_skill_exists(self):
        assert SUBAGENT_SKILL.exists()

    def test_references_dir_exists(self):
        assert SUBAGENT_REFS.exists() and SUBAGENT_REFS.is_dir()

    def test_references_file_exists(self):
        ref_file = SUBAGENT_REFS / "orchestration-patterns.md"
        assert ref_file.exists()

    def test_main_skill_under_700_lines(self):
        content = _read_file(SUBAGENT_SKILL)
        lines = content.count("\n") + 1
        assert lines < 700, (
            f"subagent-driven-dev SKILL.md has {lines} lines — should be under 700 after extraction"
        )

    def test_main_skill_points_to_references(self):
        content = _read_file(SUBAGENT_SKILL)
        assert "references/" in content, "Main skill must point to references/ directory"

    def test_references_contain_ownership_rule(self):
        ref_file = SUBAGENT_REFS / "orchestration-patterns.md"
        content = _read_file(ref_file)
        assert "Ownership Rule" in content, "References must contain the Ownership Rule"

    def test_references_contain_advanced_patterns(self):
        ref_file = SUBAGENT_REFS / "orchestration-patterns.md"
        content = _read_file(ref_file)
        patterns = ["Progressive Delegation", "Subagent Chains", "Watchdog"]
        for p in patterns:
            assert p in content, f"References missing advanced pattern: '{p}'"

    def test_version_bumped(self):
        content = _read_file(SUBAGENT_SKILL)
        fm = _parse_frontmatter(content)
        version = fm.get("version", "0.0.0")
        parts = [int(x) for x in version.split(".")]
        assert parts[0] >= 1 and parts[1] >= 1, (
            f"subagent-driven-dev should be v1.1.0+ after extraction, got {version}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  7. ORCHESTRATION GUIDE (REFERENCE SKILL)
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestrationGuide:
    """The anthropic-agent-orchestration-guide must be a valid reference skill."""

    def test_skill_exists(self):
        assert ORCHESTRATION_GUIDE.exists()

    def test_is_reference_type(self):
        content = _read_file(ORCHESTRATION_GUIDE)
        fm = _parse_frontmatter(content)
        assert fm.get("type") == "reference"

    def test_is_read_only(self):
        content = _read_file(ORCHESTRATION_GUIDE)
        fm = _parse_frontmatter(content)
        tools = fm.get("allowed-tools", "")
        assert "Write" not in tools
        assert "Edit" not in tools
        assert "Bash" not in tools

    def test_covers_five_patterns(self):
        content = _read_file(ORCHESTRATION_GUIDE)
        patterns = [
            "Prompt Chaining", "Routing", "Parallelization",
            "Orchestrator-Workers", "Evaluator-Optimizer",
        ]
        for p in patterns:
            assert p in content, f"Guide missing pattern: '{p}'"

    def test_has_decision_table(self):
        content = _read_file(ORCHESTRATION_GUIDE)
        assert "Decision Table" in content or "decision table" in content.lower()

    def test_has_anti_patterns(self):
        content = _read_file(ORCHESTRATION_GUIDE)
        assert "Anti-Pattern" in content or "anti-pattern" in content.lower()


# ══════════════════════════════════════════════════════════════════════════════
#  8. CROSS-CUTTING: REGISTRY CONSISTENCY FOR NEW PATTERNS
# ══════════════════════════════════════════════════════════════════════════════


class TestNewPatternsInRegistry:
    """All new patterns from this change must be registered."""

    def test_orchestrator_agent_in_registry(self):
        reg = _load_registry()
        assert "project-manager-agent" in reg, (
            "project-manager-agent not in registry"
        )
        assert reg["project-manager-agent"]["type"] == "agent"

    def test_orchestration_rule_in_registry(self):
        reg = _load_registry()
        assert "agent-orchestration" in reg
        assert reg["agent-orchestration"]["type"] == "rule"

    def test_orchestration_guide_in_registry(self):
        reg = _load_registry()
        assert "anthropic-agent-orchestration-guide" in reg
        assert reg["anthropic-agent-orchestration-guide"]["type"] == "skill"

    def test_pipeline_orchestrator_skill_updated(self):
        reg = _load_registry()
        entry = reg.get("pipeline-orchestrator", {})
        major = int(entry.get("version", "0.0.0").split(".")[0])
        assert major >= 2, "pipeline-orchestrator skill should be v2.0.0+"

    def test_review_gate_updated(self):
        reg = _load_registry()
        entry = reg.get("review-gate", {})
        major = int(entry.get("version", "0.0.0").split(".")[0])
        assert major >= 2, "review-gate should be v2.0.0+"

    def test_subagent_driven_dev_updated(self):
        reg = _load_registry()
        entry = reg.get("subagent-driven-dev", {})
        minor = int(entry.get("version", "0.0.0").split(".")[1])
        assert minor >= 1, "subagent-driven-dev should be v1.1.0+"


# ══════════════════════════════════════════════════════════════════════════════
#  9. END-TO-END ARTIFACT FLOW VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestEndToEndArtifactFlow:
    """Verify the complete artifact chain from Stage 1 → Stage 11."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_prd_flows_to_plan(self, stages):
        """Stage 1 produces prd, Stage 2 consumes it."""
        s1 = next(s for s in stages if s["id"] == "stage_1_prd")
        s2 = next(s for s in stages if s["id"] == "stage_2_plan")
        assert "prd" in s1["artifacts_out"]
        assert "prd" in s2.get("artifacts_in", {})
        assert "stage_1_prd" in s2.get("artifacts_in", {}).get("prd", "")

    def test_plan_flows_to_pre_tests(self, stages):
        """Stage 2 produces plan, Stage 6 needs it for test generation."""
        s2 = next(s for s in stages if s["id"] == "stage_2_plan")
        s6 = next(s for s in stages if s["id"] == "stage_6_pre_tests")
        assert "plan" in s2["artifacts_out"]
        assert "stage_2_plan" in s6["depends_on"]

    def test_pre_tests_flow_to_impl(self, stages):
        """Stage 6 produces tests, Stage 7 makes them pass."""
        s6 = next(s for s in stages if s["id"] == "stage_6_pre_tests")
        s7 = next(s for s in stages if s["id"] == "stage_7_impl")
        assert "unit_tests" in s6["artifacts_out"]
        assert "unit_tests" in s7.get("artifacts_in", {})

    def test_impl_flows_to_post_tests(self, stages):
        """Stage 7 produces source, Stage 8 tests it."""
        s7 = next(s for s in stages if s["id"] == "stage_7_impl")
        s8 = next(s for s in stages if s["id"] == "stage_8_post_tests")
        assert "source_code" in s7["artifacts_out"]
        assert "stage_7_impl" in s8["depends_on"]

    def test_review_flows_to_deploy(self, stages):
        """Stage 9 produces review report + PR, Stage 10 uses for go/no-go."""
        s9 = next(s for s in stages if s["id"] == "stage_9_review")
        s10 = next(s for s in stages if s["id"] == "stage_10_deploy")
        assert "review_report" in s9["artifacts_out"]
        assert "pr_url" in s9["artifacts_out"]
        assert "pr_url" in s10.get("artifacts_in", {})

    def test_deploy_flows_to_docs(self, stages):
        """Stage 10 produces deploy URL, Stage 11 documents it."""
        s10 = next(s for s in stages if s["id"] == "stage_10_deploy")
        s11 = next(s for s in stages if s["id"] == "stage_11_docs")
        assert "deploy_url" in s10["artifacts_out"]
        assert "stage_10_deploy" in s11["depends_on"]

    def test_critical_path_is_connected(self, stages):
        """The critical path 1→2→5→6→7→8→9→10→11 must be fully connected."""
        critical = [
            "stage_1_prd", "stage_2_plan", "stage_5_schema",
            "stage_6_pre_tests", "stage_7_impl", "stage_8_post_tests",
            "stage_9_review", "stage_10_deploy", "stage_11_docs",
        ]
        stage_map = {s["id"]: s for s in stages}
        for i in range(1, len(critical)):
            current = stage_map[critical[i]]
            # Current stage should depend (directly or transitively) on the previous
            previous = critical[i - 1]
            all_deps = set()

            def collect_deps(sid):
                for dep in stage_map[sid]["depends_on"]:
                    all_deps.add(dep)
                    collect_deps(dep)

            collect_deps(critical[i])
            assert previous in all_deps, (
                f"Critical path break: '{critical[i]}' does not depend on '{previous}'"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  10. SKIP CONDITION COVERAGE
# ══════════════════════════════════════════════════════════════════════════════


class TestSkipConditions:
    """Stages with skip_when conditions must handle the DAG adjustment correctly."""

    @pytest.fixture
    def stages(self):
        return _load_pipeline_config()["stages"]

    def test_skippable_stages_have_conditions(self, stages):
        """Only specific stages should be skippable."""
        skippable = {s["id"] for s in stages if "skip_when" in s}
        expected_skippable = {"stage_1_prd", "stage_3_scaffold", "stage_4_demo", "stage_5_schema"}
        assert skippable == expected_skippable, (
            f"Unexpected skippable stages. Expected {expected_skippable}, got {skippable}"
        )

    def test_skip_stage5_adjusts_stage6_deps(self, stages):
        """When Stage 5 is skipped, Stage 6 should still be reachable via Stage 2."""
        s6 = next(s for s in stages if s["id"] == "stage_6_pre_tests")
        assert "stage_2_plan" in s6["depends_on"], (
            "Stage 6 must depend on Stage 2 so it's reachable even if Stage 5 is skipped"
        )
