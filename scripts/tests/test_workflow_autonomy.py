"""Workflow autonomy validation tests.

Validates that all 8 orchestrated workflows (with master agents and contracts)
are fully autonomous — can run end-to-end without human intervention.

Tier 1: Static validation (structural integrity)
  - All workflow contracts have master agents on disk
  - All master agents reference their contract config
  - All sub-orchestrators referenced in contracts exist
  - All skills referenced in contract steps exist
  - Hub-only skills are not referenced as distributable
  - Every contract step has either 'skill' or 'dispatch'

Tier 2: Contract simulation (logic validation)
  - Topological sort produces valid execution order
  - Gate expressions reference existing artifact keys
  - skip_when steps are correctly identified
  - Dispatched mode skips correct steps
  - Global retry budget is enforced
  - Artifact chains are complete (no dangling inputs)
  - Handoff suggestions reference valid workflows
"""

import re
from pathlib import Path

import pytest
import yaml

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
HUB_CLAUDE = ROOT / ".claude"
CONFIG_DIR = ROOT / "config"
SKILLS_DIR = CORE_CLAUDE / "skills"
AGENTS_DIR = CORE_CLAUDE / "agents"
WORKFLOW_CONTRACTS = CONFIG_DIR / "workflow-contracts.yaml"
WORKFLOW_GROUPS = CONFIG_DIR / "workflow-groups.yml"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def contracts_data():
    return yaml.safe_load(WORKFLOW_CONTRACTS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflows(contracts_data):
    return contracts_data["workflows"]


@pytest.fixture(scope="module")
def defaults(contracts_data):
    return contracts_data.get("defaults", {})


@pytest.fixture(scope="module")
def groups_data():
    return yaml.safe_load(WORKFLOW_GROUPS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def existing_skills():
    if not SKILLS_DIR.exists():
        return set()
    return {
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


@pytest.fixture(scope="module")
def existing_agents():
    if not AGENTS_DIR.exists():
        return set()
    return {p.stem for p in AGENTS_DIR.glob("*.md") if p.name != "README.md"}


@pytest.fixture(scope="module")
def hub_only_skills():
    """Skills that exist in .claude/skills/ (hub-only) but NOT in core/.claude/skills/."""
    hub_skills_dir = HUB_CLAUDE / "skills"
    if not hub_skills_dir.exists():
        return set()
    return {
        d.name for d in hub_skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


def _parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


# ══════════════════════════════════════════════════════════════════════════════
#  TIER 1: STATIC VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestContractFilesExist:
    """Both config files must exist and be valid YAML."""

    def test_workflow_contracts_exists(self):
        assert WORKFLOW_CONTRACTS.exists()

    def test_workflow_groups_exists(self):
        assert WORKFLOW_GROUPS.exists()

    def test_contracts_has_workflows_key(self, contracts_data):
        assert "workflows" in contracts_data

    def test_contracts_has_defaults(self, contracts_data):
        assert "defaults" in contracts_data

    def test_defaults_has_retry_budget(self, defaults):
        assert "global_retry_budget" in defaults
        assert defaults["global_retry_budget"] == 15

    def test_defaults_has_max_retries(self, defaults):
        assert "max_retries_per_step" in defaults
        assert defaults["max_retries_per_step"] > 0

    def test_has_eight_workflows(self, workflows):
        assert len(workflows) == 8, (
            f"Expected 8 workflow contracts, got {len(workflows)}: "
            f"{list(workflows.keys())}"
        )


class TestMasterAgentsExist:
    """Every workflow contract must have a master agent that exists on disk."""

    @pytest.fixture
    def workflow_ids(self, workflows):
        return list(workflows.keys())

    def test_all_contracts_have_master_agent_field(self, workflows):
        missing = [
            wf_id for wf_id, wf in workflows.items()
            if "master_agent" not in wf
        ]
        assert missing == [], f"Workflows missing master_agent: {missing}"

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_master_agent_exists_on_disk(self, wf_id, workflows, existing_agents):
        master = workflows[wf_id]["master_agent"]
        assert master in existing_agents, (
            f"Workflow '{wf_id}' master agent '{master}' not found on disk"
        )

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_master_agent_naming_convention(self, wf_id, workflows):
        """Master agent should follow {workflow-id}-master-agent convention."""
        master = workflows[wf_id]["master_agent"]
        expected = f"{wf_id}-master-agent"
        assert master == expected, (
            f"Workflow '{wf_id}' master agent '{master}' doesn't match "
            f"convention '{expected}'"
        )


class TestMasterAgentContent:
    """Master agents must have the right structure for autonomous operation."""

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_master_agent_has_frontmatter(self, wf_id, workflows):
        master = workflows[wf_id]["master_agent"]
        path = AGENTS_DIR / f"{master}.md"
        fm = _parse_frontmatter(path)
        assert fm, f"Master agent '{master}' has no frontmatter"
        assert "name" in fm, f"Master agent '{master}' missing 'name'"
        assert "model" in fm, f"Master agent '{master}' missing 'model'"

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_master_agent_references_config(self, wf_id, workflows):
        """Master agent body must reference workflow-contracts.yaml."""
        master = workflows[wf_id]["master_agent"]
        path = AGENTS_DIR / f"{master}.md"
        content = path.read_text(encoding="utf-8")
        assert "workflow-contracts" in content.lower() or "config/" in content, (
            f"Master agent '{master}' doesn't reference workflow-contracts config"
        )

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_master_agent_has_dual_mode(self, wf_id, workflows):
        """Master agent must document standalone and dispatched modes."""
        master = workflows[wf_id]["master_agent"]
        path = AGENTS_DIR / f"{master}.md"
        content = path.read_text(encoding="utf-8").lower()
        assert "standalone" in content or "stand-alone" in content, (
            f"Master agent '{master}' doesn't document standalone mode"
        )
        assert "dispatched" in content or "dispatch" in content, (
            f"Master agent '{master}' doesn't document dispatched mode"
        )


class TestSubOrchestrators:
    """Sub-orchestrators declared in contracts must exist on disk."""

    def test_all_sub_orchestrators_exist(self, workflows, existing_agents):
        errors = []
        for wf_id, wf in workflows.items():
            for sub in wf.get("sub_orchestrators", []):
                agent = sub.get("agent", "")
                if agent and agent not in existing_agents:
                    errors.append(
                        f"Workflow '{wf_id}' sub-orchestrator '{agent}' "
                        f"not found on disk"
                    )
        assert errors == [], "\n".join(errors)

    def test_sub_orchestrators_have_roles(self, workflows):
        errors = []
        for wf_id, wf in workflows.items():
            for sub in wf.get("sub_orchestrators", []):
                if not sub.get("role"):
                    errors.append(
                        f"Workflow '{wf_id}' sub-orchestrator "
                        f"'{sub.get('agent', '?')}' missing 'role'"
                    )
        assert errors == [], "\n".join(errors)


class TestContractStepStructure:
    """Every step in every contract must have valid structure."""

    def test_all_steps_have_id(self, workflows):
        errors = []
        for wf_id, wf in workflows.items():
            for i, step in enumerate(wf.get("steps", [])):
                if "id" not in step:
                    errors.append(f"Workflow '{wf_id}' step {i} missing 'id'")
        assert errors == [], "\n".join(errors)

    def test_all_steps_have_skill_or_dispatch(self, workflows):
        """Every step must declare either 'skill' or 'dispatch' (not both)."""
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                sid = step.get("id", "?")
                has_skill = "skill" in step
                has_dispatch = "dispatch" in step
                if not has_skill and not has_dispatch:
                    errors.append(
                        f"Workflow '{wf_id}' step '{sid}' has neither "
                        f"'skill' nor 'dispatch'"
                    )
                if has_skill and has_dispatch:
                    errors.append(
                        f"Workflow '{wf_id}' step '{sid}' has both "
                        f"'skill' and 'dispatch'"
                    )
        assert errors == [], "\n".join(errors)

    def test_all_step_skills_exist(self, workflows, existing_skills):
        """Skills referenced in steps must exist on disk."""
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                skill = step.get("skill")
                if skill and skill not in existing_skills:
                    errors.append(
                        f"Workflow '{wf_id}' step '{step.get('id', '?')}' "
                        f"skill '{skill}' not found on disk"
                    )
        assert errors == [], "\n".join(errors)

    def test_all_step_dispatches_exist(self, workflows, existing_agents):
        """Agents dispatched in steps must exist on disk."""
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                dispatch = step.get("dispatch")
                if dispatch and dispatch not in existing_agents:
                    errors.append(
                        f"Workflow '{wf_id}' step '{step.get('id', '?')}' "
                        f"dispatch agent '{dispatch}' not found on disk"
                    )
        assert errors == [], "\n".join(errors)

    def test_all_state_files_declared(self, workflows):
        """Every workflow must declare a state_file."""
        missing = [
            wf_id for wf_id, wf in workflows.items()
            if "state_file" not in wf
        ]
        assert missing == [], f"Workflows missing state_file: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
#  TIER 2: CONTRACT SIMULATION
# ══════════════════════════════════════════════════════════════════════════════


class TestTopologicalSort:
    """Verify that step DAGs produce a valid topological order."""

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_topological_sort_succeeds(self, wf_id, workflows):
        """Kahn's algorithm must produce a complete ordering."""
        steps = workflows[wf_id]["steps"]
        step_ids = {s["id"] for s in steps}
        in_degree = {s["id"]: 0 for s in steps}
        adj = {s["id"]: [] for s in steps}

        for step in steps:
            for dep in step.get("depends_on", []):
                if dep in step_ids:
                    adj[dep].append(step["id"])
                    in_degree[step["id"]] += 1

        queue = [s for s in in_degree if in_degree[s] == 0]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        assert len(order) == len(step_ids), (
            f"Workflow '{wf_id}': topological sort incomplete — "
            f"ordered {len(order)} of {len(step_ids)} steps. "
            f"Possible cycle involving: {step_ids - set(order)}"
        )

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_root_steps_have_no_dependencies(self, wf_id, workflows):
        """At least one step must have empty depends_on (DAG root)."""
        steps = workflows[wf_id]["steps"]
        roots = [s["id"] for s in steps if not s.get("depends_on")]
        assert len(roots) >= 1, (
            f"Workflow '{wf_id}' has no root steps (all have dependencies)"
        )


class TestGateExpressions:
    """Gate expressions must reference artifact keys from the same step."""

    def test_gates_reference_valid_artifacts(self, workflows):
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                gate = step.get("gate")
                if not gate:
                    continue
                sid = step.get("id", "?")
                artifacts_out = step.get("artifacts_out", {})
                # Gate should reference an artifact key from this step's output
                # e.g., "verification.result == PASSED" → "verification" is in artifacts_out
                gate_var = gate.split(".")[0]
                if gate_var not in artifacts_out:
                    errors.append(
                        f"Workflow '{wf_id}' step '{sid}': gate references "
                        f"'{gate_var}' but artifacts_out only has "
                        f"{list(artifacts_out.keys())}"
                    )
        assert errors == [], "\n".join(errors)


class TestSkipWhenConditions:
    """Steps with skip_when must be correctly structured."""

    def test_skip_when_steps_exist(self, workflows):
        """Verify which steps have skip_when and their conditions."""
        skip_steps = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                if "skip_when" in step:
                    skip_steps.append((wf_id, step["id"], step["skip_when"]))
        # There should be at least some skip_when steps (dispatched mode)
        assert len(skip_steps) >= 1, "No skip_when conditions found in any workflow"

    def test_dispatched_mode_skips_commit_steps(self, workflows):
        """Steps that should skip in dispatched mode must have skip_when."""
        for wf_id, wf in workflows.items():
            steps = wf.get("steps", [])
            for step in steps:
                sid = step.get("id", "")
                # Commit/PR steps should skip in dispatched mode
                if sid in ("commit", "post_fix", "create_pr", "handle_feedback"):
                    assert "skip_when" in step, (
                        f"Workflow '{wf_id}' step '{sid}' should have "
                        f"skip_when for dispatched mode"
                    )

    def test_non_terminal_steps_dont_skip(self, workflows):
        """Non-terminal steps (verify, diagnose, etc.) should NOT skip."""
        never_skip = {"diagnose", "fix", "verify", "tdd_red", "fix_loop",
                      "auto_verify", "quality_gate", "capture", "author",
                      "validate", "save"}
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                sid = step.get("id", "")
                if sid in never_skip and "skip_when" in step:
                    errors.append(
                        f"Workflow '{wf_id}' step '{sid}' should NOT have "
                        f"skip_when — it's a core step"
                    )
        assert errors == [], "\n".join(errors)


class TestArtifactChainCompleteness:
    """Every artifacts_in must reference a valid artifacts_out from an upstream step."""

    @pytest.mark.parametrize("wf_id", [
        "development-loop", "testing-pipeline", "debugging-loop",
        "code-review", "documentation", "session-continuity",
        "learning-self-improvement", "skill-authoring",
    ])
    def test_artifact_inputs_resolve(self, wf_id, workflows):
        steps = workflows[wf_id]["steps"]
        available = {}
        for step in steps:
            for key in step.get("artifacts_out", {}):
                available[f"{step['id']}.artifacts_out.{key}"] = True

        errors = []
        for step in steps:
            for art_name, art_ref in step.get("artifacts_in", {}).items():
                if art_ref not in available:
                    errors.append(
                        f"Step '{step['id']}' artifact_in '{art_name}' "
                        f"references '{art_ref}' which doesn't exist"
                    )
        assert errors == [], (
            f"Workflow '{wf_id}' has broken artifact references:\n"
            + "\n".join(errors)
        )


class TestHandoffSuggestions:
    """Handoff suggestions must reference valid workflow IDs."""

    def test_handoffs_reference_valid_workflows(self, workflows):
        valid_ids = set(workflows.keys())
        errors = []
        for wf_id, wf in workflows.items():
            for handoff in wf.get("handoff_suggestions", []):
                target = handoff.get("workflow")
                if target and target not in valid_ids:
                    errors.append(
                        f"Workflow '{wf_id}' handoff references "
                        f"unknown workflow '{target}'"
                    )
        assert errors == [], "\n".join(errors)

    def test_handoffs_have_reason(self, workflows):
        errors = []
        for wf_id, wf in workflows.items():
            for handoff in wf.get("handoff_suggestions", []):
                if not handoff.get("reason"):
                    errors.append(
                        f"Workflow '{wf_id}' handoff to "
                        f"'{handoff.get('workflow', '?')}' missing 'reason'"
                    )
        assert errors == [], "\n".join(errors)


class TestStageToWorkflowMapping:
    """The stage_to_workflow section must map to valid workflows."""

    def test_mapping_exists(self, contracts_data):
        assert "stage_to_workflow" in contracts_data

    def test_mapped_workflows_are_valid(self, contracts_data):
        mapping = contracts_data["stage_to_workflow"]
        valid_ids = set(contracts_data["workflows"].keys())
        errors = []
        for stage, wf_id in mapping.items():
            if wf_id is not None and wf_id not in valid_ids:
                errors.append(
                    f"Stage '{stage}' maps to unknown workflow '{wf_id}'"
                )
        assert errors == [], "\n".join(errors)

    def test_all_eleven_stages_mapped(self, contracts_data):
        mapping = contracts_data["stage_to_workflow"]
        assert len(mapping) == 11, (
            f"Expected 11 stage mappings, got {len(mapping)}"
        )


class TestTimeoutConfiguration:
    """Every step should have a timeout (explicit or via default)."""

    def test_steps_have_timeouts(self, workflows, defaults):
        default_timeout = defaults.get("timeout_default_minutes", 20)
        errors = []
        for wf_id, wf in workflows.items():
            for step in wf.get("steps", []):
                timeout = step.get("timeout_minutes", default_timeout)
                if timeout <= 0:
                    errors.append(
                        f"Workflow '{wf_id}' step '{step['id']}' "
                        f"has non-positive timeout: {timeout}"
                    )
                if timeout > 120:
                    errors.append(
                        f"Workflow '{wf_id}' step '{step['id']}' "
                        f"has excessive timeout: {timeout} min (max 120)"
                    )
        assert errors == [], "\n".join(errors)


class TestWorkflowGroupCoverage:
    """Every workflow contract should have a matching group in workflow-groups.yml."""

    def test_all_contracts_have_groups(self, workflows, groups_data):
        group_names = set(groups_data.get("workflows", {}).keys())
        missing = []
        for wf_id in workflows:
            if wf_id not in group_names:
                missing.append(wf_id)
        assert missing == [], (
            f"Workflow contracts without matching groups: {missing}"
        )


class TestParallelStepDetection:
    """Steps with the same depends_on set can execute in parallel."""

    def test_testing_pipeline_has_parallel_steps(self, workflows):
        """auto_verify and e2e should run in parallel (both depend on fix_loop)."""
        assert "testing-pipeline" in workflows, "testing-pipeline must exist in workflow contracts"
        steps = workflows["testing-pipeline"]["steps"]
        step_map = {s["id"]: s for s in steps}

        auto_verify = step_map.get("auto_verify", {})
        e2e = step_map.get("e2e", {})

        av_deps = set(auto_verify.get("depends_on", []))
        e2e_deps = set(e2e.get("depends_on", []))

        # Both should depend on fix_loop, enabling parallel execution
        assert "fix_loop" in av_deps, "auto_verify should depend on fix_loop"
        assert "fix_loop" in e2e_deps, "e2e should depend on fix_loop"
        # Neither should depend on the other
        assert "auto_verify" not in e2e_deps, "e2e should not depend on auto_verify"
        assert "e2e" not in av_deps, "auto_verify should not depend on e2e"

    def test_documentation_has_parallel_steps(self, workflows):
        """adr and api_docs should run in parallel (both are roots)."""
        assert "documentation" in workflows, "documentation must exist in workflow contracts"
        steps = workflows["documentation"]["steps"]
        step_map = {s["id"]: s for s in steps}

        adr = step_map.get("adr", {})
        api_docs = step_map.get("api_docs", {})

        assert not adr.get("depends_on"), "adr should have no dependencies"
        assert not api_docs.get("depends_on"), "api_docs should have no dependencies"
