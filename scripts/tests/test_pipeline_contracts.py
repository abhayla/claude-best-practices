"""Test pipeline contracts: gate JSON schemas, delegation chains, reference integrity.

Validates the test verification pipeline introduced by the pipeline overhaul:
  - Gate JSON schemas match what upstream/downstream stages expect
  - Skill() and Agent() delegation targets exist
  - Skills with references/ pointers have matching files
  - config/test-pipeline.yml references real skills with consistent artifact paths
  - test-evidence-config.json template is valid
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
SKILLS_DIR = CORE_CLAUDE / "skills"
AGENTS_DIR = CORE_CLAUDE / "agents"
RULES_DIR = CORE_CLAUDE / "rules"
TEMPLATES_DIR = CORE_CLAUDE / "templates"

TEST_PIPELINE_CONFIG = CONFIG_DIR / "test-pipeline.yml"
EVIDENCE_CONFIG_TEMPLATE = TEMPLATES_DIR / "test-evidence-config.json"

# Pipeline skills under test
AUTO_VERIFY = SKILLS_DIR / "auto-verify" / "SKILL.md"
FIX_LOOP = SKILLS_DIR / "fix-loop" / "SKILL.md"
POST_FIX = SKILLS_DIR / "post-fix-pipeline" / "SKILL.md"
REGRESSION_TEST = SKILLS_DIR / "regression-test" / "SKILL.md"
CODE_QUALITY_GATE = SKILLS_DIR / "code-quality-gate" / "SKILL.md"
VERIFY_SCREENSHOTS = SKILLS_DIR / "verify-screenshots" / "SKILL.md"

# Pipeline agents under test
TEST_PIPELINE_AGENT = AGENTS_DIR / "test-pipeline-agent.md"
TESTER_AGENT = AGENTS_DIR / "tester-agent.md"
FAILURE_ANALYZER_AGENT = AGENTS_DIR / "test-failure-analyzer-agent.md"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def _extract_skill_refs(content: str) -> list[str]:
    """Extract Skill() call targets from content."""
    return re.findall(r'Skill\(\s*["\']/?([^"\']+)["\']', content)


def _extract_agent_refs(content: str) -> list[str]:
    """Extract Agent() call targets from content."""
    return re.findall(r'Agent\(\s*["\']([^"\']+)["\']', content)


def _extract_json_file_refs(content: str) -> list[str]:
    """Extract test-results/*.json file references."""
    return re.findall(r'test-results/([a-z-]+\.json)', content)


def _extract_reference_pointers(content: str) -> list[str]:
    """Extract references/*.md pointers from skill content."""
    return re.findall(r'Read:\s*`references/([^`]+)`', content)


# ══════════════════════════════════════════════════════════════════════════════
# 1. CONFIG VALIDITY
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineConfig:
    """Validate config/test-pipeline.yml structure and references."""

    @pytest.fixture(autouse=True)
    def load_config(self):
        self.config = yaml.safe_load(TEST_PIPELINE_CONFIG.read_text())

    def test_config_exists(self):
        assert TEST_PIPELINE_CONFIG.exists()

    def test_has_pipeline_key(self):
        assert "pipeline" in self.config
        assert "stages" in self.config["pipeline"]

    def test_has_three_stages(self):
        stages = self.config["pipeline"]["stages"]
        assert len(stages) == 3

    def test_stage_order_is_correct(self):
        names = [s["name"] for s in self.config["pipeline"]["stages"]]
        assert names == ["fix-loop", "auto-verify", "post-fix-pipeline"]

    def test_each_stage_has_required_fields(self):
        for stage in self.config["pipeline"]["stages"]:
            assert "name" in stage, f"Stage missing 'name': {stage}"
            assert "skill" in stage, f"Stage {stage['name']} missing 'skill'"
            assert "writes" in stage, f"Stage {stage['name']} missing 'writes'"

    def test_stage_skills_reference_real_skills(self):
        for stage in self.config["pipeline"]["stages"]:
            skill_name = stage["skill"].lstrip("/")
            skill_dir = SKILLS_DIR / skill_name
            assert skill_dir.exists(), (
                f"Stage '{stage['name']}' references skill '{skill_name}' "
                f"but {skill_dir} does not exist"
            )

    def test_artifact_chain_is_connected(self):
        """auto-verify reads what fix-loop writes, post-fix reads what auto-verify writes."""
        stages = self.config["pipeline"]["stages"]
        # fix-loop writes → auto-verify reads
        assert stages[1].get("reads") == stages[0]["writes"], (
            f"auto-verify reads '{stages[1].get('reads')}' but fix-loop writes '{stages[0]['writes']}'"
        )
        # auto-verify writes → post-fix reads
        assert stages[2].get("reads") == stages[1]["writes"], (
            f"post-fix reads '{stages[2].get('reads')}' but auto-verify writes '{stages[1]['writes']}'"
        )

    def test_global_retry_budget_is_positive(self):
        assert self.config.get("global_retry_budget", 0) > 0

    def test_capture_proof_section_exists(self):
        assert "capture_proof" in self.config
        cp = self.config["capture_proof"]
        assert "enabled" in cp
        assert "evidence_dir" in cp

    def test_cleanup_includes_both_dirs(self):
        cleanup = self.config.get("cleanup", [])
        assert "test-results/" in cleanup
        assert "test-evidence/" in cleanup


class TestEvidenceConfigTemplate:
    """Validate test-evidence-config.json template."""

    def test_template_exists(self):
        assert EVIDENCE_CONFIG_TEMPLATE.exists()

    def test_is_valid_json(self):
        data = json.loads(EVIDENCE_CONFIG_TEMPLATE.read_text())
        assert isinstance(data, dict)

    def test_has_capture_proof_toggle(self):
        data = json.loads(EVIDENCE_CONFIG_TEMPLATE.read_text())
        assert "capture_proof" in data
        assert isinstance(data["capture_proof"], bool)

    def test_has_platform_configs(self):
        data = json.loads(EVIDENCE_CONFIG_TEMPLATE.read_text())
        assert "platforms" in data
        platforms = data["platforms"]
        for expected in ["playwright", "maestro", "flutter", "react_native_owl"]:
            assert expected in platforms, f"Missing platform config: {expected}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. GATE JSON SCHEMA CONTRACTS
# ══════════════════════════════════════════════════════════════════════════════


class TestGateJsonContracts:
    """Verify that upstream writers and downstream readers agree on JSON field names."""

    def test_fix_loop_writes_result_field(self):
        """fix-loop's structured output must have 'result' — auto-verify reads it."""
        content = _read(FIX_LOOP)
        assert '"result": "PASSED|FAILED"' in content or '"result":' in content

    def test_auto_verify_reads_fix_loop_result(self):
        """auto-verify gate check parses fix-loop.json 'result' field."""
        content = _read(AUTO_VERIFY)
        assert "fix-loop.json" in content
        assert "result" in content

    def test_auto_verify_writes_result_field(self):
        """auto-verify's structured output must have 'result' — post-fix reads it."""
        content = _read(AUTO_VERIFY)
        assert '"result": "PASSED' in content or '"result":' in content

    def test_post_fix_reads_auto_verify_result(self):
        """post-fix gate check parses auto-verify.json 'result' field."""
        content = _read(POST_FIX)
        assert "auto-verify.json" in content
        assert "result" in content

    def test_auto_verify_writes_visual_review_field(self):
        """auto-verify must include visual_review in structured output."""
        content = _read(AUTO_VERIFY)
        assert '"visual_review"' in content or "'visual_review'" in content

    def test_post_fix_reads_visual_review_overrides(self):
        """post-fix checks visual-review.json for overrides."""
        content = _read(POST_FIX)
        assert "visual-review.json" in content
        assert "overrides" in content

    def test_auto_verify_visual_review_has_enabled_field(self):
        """visual_review must have 'enabled' field for when capture-proof is off."""
        content = _read(AUTO_VERIFY)
        assert '"enabled"' in content

    def test_pipeline_agent_reads_all_stage_outputs(self):
        """Orchestrator must reference all test-results/*.json files."""
        content = _read(TEST_PIPELINE_AGENT)
        assert "test-results/" in content
        assert "pipeline-verdict.json" in content

    def test_pipeline_verdict_schema_in_orchestrator(self):
        """Orchestrator defines pipeline-verdict.json with required fields."""
        content = _read(TEST_PIPELINE_AGENT)
        for field in ["run_id", "result", "stages_completed", "stage_results", "failures"]:
            assert field in content, f"pipeline-verdict.json missing field: {field}"


# ══════════════════════════════════════════════════════════════════════════════
# 3. SKILL DELEGATION CHAIN INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillDelegationChains:
    """Verify that Skill() and Agent() calls reference existing targets."""

    def test_auto_verify_delegates_to_regression_test(self):
        content = _read(AUTO_VERIFY)
        assert "/regression-test" in content
        assert (SKILLS_DIR / "regression-test" / "SKILL.md").exists()

    def test_auto_verify_delegates_to_code_quality_gate(self):
        content = _read(AUTO_VERIFY)
        assert "/code-quality-gate" in content
        assert (SKILLS_DIR / "code-quality-gate" / "SKILL.md").exists()

    def test_auto_verify_delegates_to_contract_test(self):
        content = _read(AUTO_VERIFY)
        assert "/contract-test" in content
        assert (SKILLS_DIR / "contract-test" / "SKILL.md").exists()

    def test_auto_verify_delegates_to_perf_test(self):
        content = _read(AUTO_VERIFY)
        assert "/perf-test" in content
        assert (SKILLS_DIR / "perf-test" / "SKILL.md").exists()

    def test_auto_verify_dispatches_tester_agent(self):
        content = _read(AUTO_VERIFY)
        assert "tester-agent" in content
        assert TESTER_AGENT.exists()

    def test_fix_loop_dispatches_failure_analyzer_agent(self):
        content = _read(FIX_LOOP)
        assert "test-failure-analyzer-agent" in content
        assert FAILURE_ANALYZER_AGENT.exists()

    def test_fix_loop_escalates_to_contract_test(self):
        content = _read(FIX_LOOP)
        assert "/contract-test" in content

    def test_fix_loop_escalates_to_verify_screenshots(self):
        content = _read(FIX_LOOP)
        assert "/verify-screenshots" in content

    def test_post_fix_delegates_to_learn_n_improve(self):
        content = _read(POST_FIX)
        assert "/learn-n-improve" in content
        assert (SKILLS_DIR / "learn-n-improve" / "SKILL.md").exists()

    def test_regression_test_notes_auto_verify_consumer(self):
        """regression-test must document that auto-verify consumes it."""
        content = _read(REGRESSION_TEST)
        assert "canonical change-to-test mapper" in content
        assert "/auto-verify" in content

    def test_failure_analyzer_notes_fix_loop_consumer(self):
        """test-failure-analyzer-agent must document that fix-loop dispatches it."""
        content = _read(FAILURE_ANALYZER_AGENT)
        assert "Pipeline role" in content or "pipeline role" in content.lower()
        assert "/fix-loop" in content


# ══════════════════════════════════════════════════════════════════════════════
# 4. REFERENCE FILE INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════


class TestReferenceFileIntegrity:
    """Verify that skills with references/ pointers have matching files."""

    def test_code_quality_gate_references_exist(self):
        content = _read(CODE_QUALITY_GATE)
        pointers = _extract_reference_pointers(content)
        assert len(pointers) > 0, "code-quality-gate should have reference pointers"
        refs_dir = SKILLS_DIR / "code-quality-gate" / "references"
        for ref in pointers:
            ref_path = refs_dir / ref
            assert ref_path.exists(), (
                f"code-quality-gate references '{ref}' but {ref_path} does not exist"
            )

    def test_code_quality_gate_references_are_non_empty(self):
        refs_dir = SKILLS_DIR / "code-quality-gate" / "references"
        for ref_file in refs_dir.glob("*.md"):
            content = ref_file.read_text(encoding="utf-8")
            lines = [l for l in content.strip().split("\n") if l.strip()]
            assert len(lines) >= 20, (
                f"Reference file {ref_file.name} has only {len(lines)} non-empty lines — "
                f"may be a stub or extraction failure"
            )

    def test_code_quality_gate_preserves_step_numbers(self):
        """After extraction, main SKILL.md must still have Steps 7, 8.5, 10, 11, 12."""
        content = _read(CODE_QUALITY_GATE)
        for step in ["STEP 7", "STEP 8.5", "STEP 10", "STEP 11", "STEP 12"]:
            assert step in content, f"code-quality-gate missing {step} after reference extraction"

    def test_code_quality_gate_json_output_preserved(self):
        """Structured output path must remain in main SKILL.md, not extracted."""
        content = _read(CODE_QUALITY_GATE)
        assert "code-quality-gate.json" in content

    def test_code_quality_gate_under_550_lines(self):
        content = _read(CODE_QUALITY_GATE)
        lines = len(content.strip().split("\n"))
        assert lines < 550, f"code-quality-gate is {lines} lines (target: <550)"

    @pytest.mark.parametrize("skill_dir", [
        d for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ], ids=lambda d: d.name)
    def test_all_skills_reference_pointers_resolve(self, skill_dir):
        """For every skill, any Read: `references/X` pointer must have a matching file."""
        content = _read(skill_dir / "SKILL.md")
        pointers = _extract_reference_pointers(content)
        if not pointers:
            pytest.skip(f"{skill_dir.name} has no reference pointers")
        refs_dir = skill_dir / "references"
        for ref in pointers:
            ref_path = refs_dir / ref
            assert ref_path.exists(), (
                f"Skill '{skill_dir.name}' references '{ref}' but {ref_path} does not exist"
            )


# ══════════════════════════════════════════════════════════════════════════════
# 5. CAPTURE PROOF INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestCaptureProofIntegration:
    """Verify screenshot-as-proof feature is wired across all relevant skills."""

    def test_auto_verify_has_capture_proof_param(self):
        fm = _parse_frontmatter(_read(AUTO_VERIFY))
        assert "--capture-proof" in fm.get("argument-hint", "")

    def test_fix_loop_has_capture_proof_param(self):
        fm = _parse_frontmatter(_read(FIX_LOOP))
        assert "--capture-proof" in fm.get("argument-hint", "")

    def test_post_fix_has_capture_proof_param(self):
        fm = _parse_frontmatter(_read(POST_FIX))
        assert "--capture-proof" in fm.get("argument-hint", "")

    def test_auto_verify_has_visual_proof_review_step(self):
        content = _read(AUTO_VERIFY)
        assert "STEP 2.5" in content or "Visual Proof Review" in content

    def test_verify_screenshots_has_proof_mode(self):
        content = _read(VERIFY_SCREENSHOTS)
        assert "--proof-mode" in content
        assert "STEP 0.5" in content

    @pytest.mark.parametrize("skill_name", [
        "playwright", "android-run-e2e", "flutter-e2e-test", "react-native-e2e"
    ])
    def test_platform_skills_have_capture_proof_section(self, skill_name):
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_path.exists(), f"Skill {skill_name} not found"
        content = _read(skill_path)
        assert "CAPTURE PROOF MODE" in content, (
            f"Skill '{skill_name}' missing CAPTURE PROOF MODE section"
        )
        assert "test-evidence" in content, (
            f"Skill '{skill_name}' doesn't reference test-evidence directory"
        )

    def test_tester_agent_has_evidence_capture(self):
        content = _read(TESTER_AGENT)
        assert "Evidence Capture" in content
        assert "manifest.json" in content

    def test_testing_rule_has_proof_archive_section(self):
        content = _read(RULES_DIR / "testing.md")
        assert "Screenshot Proof Archive" in content
        assert "manifest.json" in content
        assert "visual-review.json" in content

    def test_pipeline_agent_references_evidence_dir(self):
        content = _read(TEST_PIPELINE_AGENT)
        assert "test-evidence" in content
        assert "capture_proof" in content


# ══════════════════════════════════════════════════════════════════════════════
# 6. STRICT GATES INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestStrictGatesIntegration:
    """Verify --strict-gates is wired across pipeline skills."""

    def test_auto_verify_has_strict_gates_param(self):
        fm = _parse_frontmatter(_read(AUTO_VERIFY))
        assert "--strict-gates" in fm.get("argument-hint", "")

    def test_auto_verify_blocks_on_missing_upstream_with_strict(self):
        content = _read(AUTO_VERIFY)
        assert "BLOCKED: fix-loop output missing" in content

    def test_auto_verify_warns_without_strict(self):
        content = _read(AUTO_VERIFY)
        assert "WARN: No fix-loop results" in content

    def test_post_fix_blocks_on_missing_upstream_with_strict(self):
        content = _read(POST_FIX)
        assert "BLOCKED: auto-verify output missing" in content or "strict-gates" in content.lower()

    def test_pipeline_agent_always_passes_strict_gates(self):
        content = _read(TEST_PIPELINE_AGENT)
        assert "--strict-gates" in content
        assert "always passed by this orchestrator" in content.lower() or "fail-closed" in content.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 7. VERSION CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestVersionConsistency:
    """Verify skill versions in frontmatter match what's in the registry."""

    @pytest.fixture(autouse=True)
    def load_registry(self):
        with open(ROOT / "registry" / "patterns.json") as f:
            self.registry = json.load(f)

    def _registry_version(self, name: str) -> str | None:
        entry = self.registry.get(name)
        if entry and isinstance(entry, dict):
            return entry.get("version")
        return None

    @pytest.mark.parametrize("skill_name,path", [
        ("auto-verify", AUTO_VERIFY),
        ("fix-loop", FIX_LOOP),
        ("post-fix-pipeline", POST_FIX),
        ("verify-screenshots", VERIFY_SCREENSHOTS),
    ])
    def test_skill_version_matches_registry(self, skill_name, path):
        fm = _parse_frontmatter(_read(path))
        file_version = fm.get("version", "").strip('"')
        reg_version = self._registry_version(skill_name)
        assert reg_version is not None, f"{skill_name} not found in registry"
        assert file_version == reg_version, (
            f"{skill_name} version mismatch: file={file_version}, registry={reg_version}"
        )

    @pytest.mark.parametrize("agent_name,path", [
        ("tester-agent", TESTER_AGENT),
        ("test-failure-analyzer-agent", FAILURE_ANALYZER_AGENT),
        ("test-pipeline-agent", TEST_PIPELINE_AGENT),
    ])
    def test_agent_version_matches_registry(self, agent_name, path):
        fm = _parse_frontmatter(_read(path))
        file_version = fm.get("version", "").strip('"')
        reg_version = self._registry_version(agent_name)
        assert reg_version is not None, f"{agent_name} not found in registry"
        assert file_version == reg_version, (
            f"{agent_name} version mismatch: file={file_version}, registry={reg_version}"
        )
