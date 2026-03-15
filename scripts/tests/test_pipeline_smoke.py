"""Pipeline smoke test — validates artifacts produced by a live pipeline run.

This test file validates the output of a REAL pipeline execution against a test
project. It does NOT run the pipeline itself — that requires a live Claude Code
session.

Usage:
  1. Bootstrap the test project:
     python scripts/bootstrap.py --stacks fastapi-python --target scripts/tests/smoke-test/todo-api/

  2. Open Claude Code in the test project directory and run:
     /pipeline-orchestrator SEED-REQUIREMENT.md

  3. After the pipeline completes, validate:
     PYTHONPATH=. python -m pytest scripts/tests/test_pipeline_smoke.py -v

Set the SMOKE_TEST_PROJECT env var to point to a different project:
  SMOKE_TEST_PROJECT=/path/to/project python -m pytest scripts/tests/test_pipeline_smoke.py -v
"""

import json
import os
import re
from pathlib import Path

import pytest

# ── Target Project Path ──────────────────────────────────────────────────────

SMOKE_PROJECT = Path(
    os.environ.get(
        "SMOKE_TEST_PROJECT",
        Path(__file__).parent / "smoke-test" / "todo-api",
    )
)


def _pipeline_has_run() -> bool:
    """Check if the pipeline has actually been executed in the test project."""
    return (SMOKE_PROJECT / ".pipeline" / "state.json").exists()


# Skip the entire module if the pipeline hasn't been run
pytestmark = pytest.mark.skipif(
    not _pipeline_has_run(),
    reason=(
        f"Pipeline has not been run in {SMOKE_PROJECT}. "
        "Run /pipeline-orchestrator SEED-REQUIREMENT.md first."
    ),
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _find_files(pattern: str, root: Path = SMOKE_PROJECT) -> list[Path]:
    return sorted(root.rglob(pattern))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_state() -> dict:
    return _load_json(SMOKE_PROJECT / ".pipeline" / "state.json")


def _stage_status(state: dict, stage_id: str) -> str:
    """Get the status of a stage from the pipeline state."""
    stages = state.get("stages", {})
    if isinstance(stages, dict):
        return stages.get(stage_id, {}).get("status", "unknown")
    # Handle list format
    for s in stages:
        if isinstance(s, dict) and s.get("id") == stage_id:
            return s.get("status", "unknown")
    return "unknown"


def _is_skipped(state: dict, stage_id: str) -> bool:
    return _stage_status(state, stage_id) == "skipped"


# ══════════════════════════════════════════════════════════════════════════════
#  0. PIPELINE STATE & EVENT LOG
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineState:
    """Validate the pipeline state file and event log."""

    def test_state_file_exists(self):
        path = SMOKE_PROJECT / ".pipeline" / "state.json"
        assert path.exists(), "Missing .pipeline/state.json"

    def test_state_has_pipeline_id(self):
        state = _load_state()
        assert "pipeline_id" in state, "state.json missing pipeline_id"

    def test_state_has_all_stages(self):
        state = _load_state()
        stages = state.get("stages", {})
        # Should have entries for at least the 11 known stages
        expected_prefixes = [f"stage_{i}" for i in range(1, 12)]
        stage_keys = (
            list(stages.keys())
            if isinstance(stages, dict)
            else [s.get("id", "") for s in stages if isinstance(s, dict)]
        )
        for prefix in expected_prefixes:
            found = any(k.startswith(prefix) for k in stage_keys)
            assert found, f"state.json missing stage entry starting with '{prefix}'"

    def test_all_stages_completed_or_skipped(self):
        state = _load_state()
        stages = state.get("stages", {})
        terminal = {"passed", "skipped", "completed"}
        errors = []
        if isinstance(stages, dict):
            items = stages.items()
        else:
            items = [(s.get("id", "?"), s) for s in stages if isinstance(s, dict)]
        for stage_id, info in items:
            status = info.get("status", "unknown") if isinstance(info, dict) else "unknown"
            if status not in terminal:
                errors.append(f"{stage_id}: status={status}")
        assert errors == [], (
            f"Stages not in terminal state:\n" + "\n".join(errors)
        )

    def test_event_log_exists(self):
        path = SMOKE_PROJECT / ".pipeline" / "event-log.jsonl"
        assert path.exists(), "Missing .pipeline/event-log.jsonl"

    def test_event_log_has_entries(self):
        path = SMOKE_PROJECT / ".pipeline" / "event-log.jsonl"
        lines = [l for l in _read(path).strip().splitlines() if l.strip()]
        assert len(lines) >= 2, (
            f"Event log has only {len(lines)} entries — expected at least pipeline_started + pipeline_completed"
        )

    def test_event_log_entries_are_valid_json(self):
        path = SMOKE_PROJECT / ".pipeline" / "event-log.jsonl"
        errors = []
        for i, line in enumerate(_read(path).strip().splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: {e}")
        assert errors == [], f"Invalid JSONL entries:\n" + "\n".join(errors)


# ══════════════════════════════════════════════════════════════════════════════
#  1. STAGE 1: PRD
# ══════════════════════════════════════════════════════════════════════════════


class TestStage1PRD:
    """Stage 1 must produce a valid PRD with requirement IDs."""

    def test_prd_file_exists(self):
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        assert len(prds) >= 1, "No PRD file found in docs/plans/"

    def test_prd_has_user_stories(self):
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(prds[0])
        assert re.search(r"US-\d+", content), "PRD missing user story IDs (US-xxx)"

    def test_prd_has_acceptance_criteria(self):
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(prds[0])
        assert re.search(r"AC-\d+", content), "PRD missing acceptance criteria IDs (AC-xxx)"

    def test_prd_has_nfrs(self):
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(prds[0])
        assert re.search(r"NFR-\d+", content), "PRD missing non-functional requirement IDs (NFR-xxx)"

    def test_prd_is_substantial(self):
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(prds[0])
        lines = content.strip().splitlines()
        assert len(lines) >= 50, f"PRD too short ({len(lines)} lines) — expected >= 50"


# ══════════════════════════════════════════════════════════════════════════════
#  2. STAGE 2: PLAN
# ══════════════════════════════════════════════════════════════════════════════


class TestStage2Plan:
    """Stage 2 must produce a plan with tasks and dependencies."""

    def test_plan_file_exists(self):
        plans = _find_files("*-plan.md", SMOKE_PROJECT / "docs" / "plans")
        assert len(plans) >= 1, "No plan file found in docs/plans/"

    def test_plan_has_tasks(self):
        plans = _find_files("*-plan.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(plans[0])
        assert re.search(r"Task\s+\d+", content, re.IGNORECASE), (
            "Plan missing task entries (Task N format)"
        )

    def test_plan_is_substantial(self):
        plans = _find_files("*-plan.md", SMOKE_PROJECT / "docs" / "plans")
        content = _read(plans[0])
        lines = content.strip().splitlines()
        assert len(lines) >= 30, f"Plan too short ({len(lines)} lines)"

    def test_adrs_exist(self):
        adrs = _find_files("ADR-*.md", SMOKE_PROJECT / "docs")
        # ADRs are optional — but if the plan made architectural decisions, they should exist
        # Just check docs/adr/ directory exists
        adr_dir = SMOKE_PROJECT / "docs" / "adr"
        if adr_dir.exists():
            assert len(adrs) >= 1, "docs/adr/ exists but no ADR files found"


# ══════════════════════════════════════════════════════════════════════════════
#  3. STAGE 3: SCAFFOLDING
# ══════════════════════════════════════════════════════════════════════════════


class TestStage3Scaffold:
    """Stage 3 must produce a buildable project skeleton."""

    def test_pyproject_toml_exists(self):
        assert (SMOKE_PROJECT / "pyproject.toml").exists()

    def test_src_directory_exists(self):
        assert (SMOKE_PROJECT / "src").exists() or (SMOKE_PROJECT / "app").exists(), (
            "No src/ or app/ directory found"
        )

    def test_has_python_files_in_src(self):
        py_files = _find_files("*.py", SMOKE_PROJECT / "src")
        if not py_files:
            py_files = _find_files("*.py", SMOKE_PROJECT / "app")
        # After scaffolding, there should be at least __init__.py or main.py
        assert len(py_files) >= 1, "No Python files in src/ or app/"

    def test_ci_config_exists(self):
        ci_paths = [
            SMOKE_PROJECT / ".github" / "workflows" / "ci.yml",
            SMOKE_PROJECT / ".github" / "workflows" / "ci.yaml",
            SMOKE_PROJECT / ".github" / "workflows" / "test.yml",
        ]
        found = any(p.exists() for p in ci_paths)
        assert found, "No CI config found in .github/workflows/"

    def test_gitignore_exists(self):
        assert (SMOKE_PROJECT / ".gitignore").exists()


# ══════════════════════════════════════════════════════════════════════════════
#  4. STAGE 4: HTML DEMO (may be skipped for API-only projects)
# ══════════════════════════════════════════════════════════════════════════════


class TestStage4Demo:
    """Stage 4 produces HTML demo screens (or is skipped for API-only projects)."""

    def test_demo_exists_or_skipped(self):
        state = _load_state()
        if _is_skipped(state, "stage_4_demo"):
            pytest.skip("Stage 4 was skipped (API-only project)")
        demos = _find_files("index.html", SMOKE_PROJECT / "demos")
        assert len(demos) >= 1, "No demo index.html found in demos/"

    def test_demo_has_css(self):
        state = _load_state()
        if _is_skipped(state, "stage_4_demo"):
            pytest.skip("Stage 4 was skipped")
        css_files = _find_files("*.css", SMOKE_PROJECT / "demos")
        assert len(css_files) >= 1, "No CSS files in demos/"


# ══════════════════════════════════════════════════════════════════════════════
#  5. STAGE 5: SCHEMA & MIGRATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestStage5Schema:
    """Stage 5 must produce ERD, migrations, and seed data."""

    def test_schema_not_skipped(self):
        """Our test project has a database — Stage 5 should NOT be skipped."""
        state = _load_state()
        assert not _is_skipped(state, "stage_5_schema"), (
            "Stage 5 was skipped but this project requires a database"
        )

    def test_erd_exists(self):
        erd_files = (
            _find_files("erd.md", SMOKE_PROJECT / "docs" / "schema")
            + _find_files("*-schema.md", SMOKE_PROJECT / "docs" / "schema")
            + _find_files("*schema*.md", SMOKE_PROJECT / "docs")
        )
        assert len(erd_files) >= 1, "No ERD/schema file found in docs/schema/"

    def test_migrations_exist(self):
        migration_dirs = [
            SMOKE_PROJECT / "migrations",
            SMOKE_PROJECT / "alembic",
            SMOKE_PROJECT / "db" / "migrations",
        ]
        found = any(d.exists() and any(d.iterdir()) for d in migration_dirs if d.exists())
        assert found, "No migration files found"

    def test_seed_script_exists(self):
        seeds = (
            _find_files("seed.*", SMOKE_PROJECT / "scripts")
            + _find_files("seed_*.py", SMOKE_PROJECT)
            + _find_files("seeds.py", SMOKE_PROJECT)
        )
        # Seeds are optional but recommended
        if not seeds:
            pytest.skip("No seed script found (optional)")


# ══════════════════════════════════════════════════════════════════════════════
#  6. STAGE 6: PRE-IMPLEMENTATION TESTS (TDD RED PHASE)
# ══════════════════════════════════════════════════════════════════════════════


class TestStage6PreTests:
    """Stage 6 must produce failing test stubs."""

    def test_unit_tests_exist(self):
        unit_tests = _find_files("test_*.py", SMOKE_PROJECT / "tests")
        assert len(unit_tests) >= 1, "No test files found in tests/"

    def test_test_directory_structure(self):
        tests_dir = SMOKE_PROJECT / "tests"
        assert tests_dir.exists(), "tests/ directory missing"
        # Should have at least some test files
        all_tests = _find_files("test_*.py", tests_dir)
        assert len(all_tests) >= 2, f"Only {len(all_tests)} test files — expected >= 2"

    def test_test_generator_json_exists(self):
        path = SMOKE_PROJECT / "test-results" / "test-generator.json"
        if not path.exists():
            # Check alternative location
            alt_paths = _find_files("test-generator.json", SMOKE_PROJECT)
            if not alt_paths:
                pytest.skip("test-results/test-generator.json not found (may use different output format)")

    def test_conftest_exists(self):
        conftest = SMOKE_PROJECT / "tests" / "conftest.py"
        assert conftest.exists(), "tests/conftest.py missing — shared fixtures needed"


# ══════════════════════════════════════════════════════════════════════════════
#  7. STAGE 7: IMPLEMENTATION (TDD GREEN PHASE)
# ══════════════════════════════════════════════════════════════════════════════


class TestStage7Implementation:
    """Stage 7 must produce source code that makes tests pass."""

    def test_source_files_exist(self):
        py_files = _find_files("*.py", SMOKE_PROJECT / "src")
        if not py_files:
            py_files = _find_files("*.py", SMOKE_PROJECT / "app")
        assert len(py_files) >= 3, (
            f"Only {len(py_files)} Python source files — expected >= 3 for a todo API"
        )

    def test_has_main_or_app_entry(self):
        candidates = [
            SMOKE_PROJECT / "src" / "main.py",
            SMOKE_PROJECT / "app" / "main.py",
            SMOKE_PROJECT / "main.py",
        ]
        # Also check for __init__.py with app factory
        candidates += _find_files("main.py", SMOKE_PROJECT)
        found = any(p.exists() for p in candidates) or len(candidates) > 3
        assert found, "No main.py entry point found"

    def test_has_models(self):
        model_files = (
            _find_files("*model*.py", SMOKE_PROJECT / "src")
            + _find_files("*model*.py", SMOKE_PROJECT / "app")
        )
        assert len(model_files) >= 1, "No model files found"

    def test_has_routes_or_endpoints(self):
        route_files = (
            _find_files("*route*.py", SMOKE_PROJECT / "src")
            + _find_files("*router*.py", SMOKE_PROJECT / "src")
            + _find_files("*endpoint*.py", SMOKE_PROJECT / "src")
            + _find_files("*route*.py", SMOKE_PROJECT / "app")
            + _find_files("*router*.py", SMOKE_PROJECT / "app")
            + _find_files("*api*.py", SMOKE_PROJECT / "src")
        )
        assert len(route_files) >= 1, "No route/endpoint files found"

    def test_progress_file_exists(self):
        progress = _find_files("*-progress.md", SMOKE_PROJECT / "docs" / "plans")
        if not progress:
            pytest.skip("Progress file not found (optional artifact)")


# ══════════════════════════════════════════════════════════════════════════════
#  8. STAGE 8: POST-IMPLEMENTATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestStage8PostTests:
    """Stage 8 must produce test reports and security analysis."""

    def test_threat_model_exists(self):
        threat_models = (
            _find_files("threat-model.md", SMOKE_PROJECT / "tests" / "security")
            + _find_files("threat-model.md", SMOKE_PROJECT / "docs")
            + _find_files("threat*.md", SMOKE_PROJECT)
        )
        if not threat_models:
            pytest.skip("Threat model not found (may be in alternative location)")

    def test_stage8_report_exists(self):
        report_paths = [
            SMOKE_PROJECT / "test-results" / "stage-8-post-tests.json",
            SMOKE_PROJECT / "test-results" / "stage-8.json",
        ]
        found = any(p.exists() for p in report_paths)
        if not found:
            # Check for any test result files from Stage 8
            results = _find_files("*.json", SMOKE_PROJECT / "test-results")
            if not results:
                pytest.skip("No Stage 8 test results found")


# ══════════════════════════════════════════════════════════════════════════════
#  9. STAGE 9: REVIEW GATE
# ══════════════════════════════════════════════════════════════════════════════


class TestStage9ReviewGate:
    """Stage 9 must produce a review-gate.json with a verdict."""

    def test_review_gate_json_exists(self):
        path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        assert path.exists(), "Missing test-results/review-gate.json"

    def test_review_gate_has_verdict(self):
        path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        if not path.exists():
            pytest.skip("review-gate.json missing")
        data = _load_json(path)
        assert "verdict" in data or "result" in data, (
            "review-gate.json missing verdict/result field"
        )

    def test_review_gate_verdict_is_valid(self):
        path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        if not path.exists():
            pytest.skip("review-gate.json missing")
        data = _load_json(path)
        verdict = data.get("verdict") or data.get("result", "")
        valid = {"APPROVED", "APPROVED WITH CAVEATS", "REJECTED"}
        assert verdict in valid, f"Invalid verdict: '{verdict}'"

    def test_review_gate_has_checks(self):
        path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        if not path.exists():
            pytest.skip("review-gate.json missing")
        data = _load_json(path)
        checks = data.get("checks", {})
        expected_checks = [
            "code_quality_gate", "architecture_fitness",
            "security_audit", "change_risk_scoring",
        ]
        for check in expected_checks:
            assert check in checks, f"review-gate.json missing check: '{check}'"

    def test_review_gate_not_rejected(self):
        """The pipeline should only reach Stage 10 if review passed."""
        path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        if not path.exists():
            pytest.skip("review-gate.json missing")
        data = _load_json(path)
        verdict = data.get("verdict") or data.get("result", "")
        assert verdict != "REJECTED", (
            f"Review gate REJECTED — pipeline should not have continued to Stage 10"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  10. STAGE 10: DEPLOY
# ══════════════════════════════════════════════════════════════════════════════


class TestStage10Deploy:
    """Stage 10 must produce deployment artifacts."""

    def test_ci_pipeline_exists(self):
        ci_files = _find_files("ci.yml", SMOKE_PROJECT / ".github" / "workflows")
        ci_files += _find_files("ci.yaml", SMOKE_PROJECT / ".github" / "workflows")
        assert len(ci_files) >= 1, "No CI pipeline found"

    def test_ci_pipeline_is_substantial(self):
        ci_files = (
            _find_files("ci.yml", SMOKE_PROJECT / ".github" / "workflows")
            + _find_files("ci.yaml", SMOKE_PROJECT / ".github" / "workflows")
        )
        if not ci_files:
            pytest.skip("No CI pipeline found")
        content = _read(ci_files[0])
        lines = content.strip().splitlines()
        assert len(lines) >= 20, f"CI pipeline too short ({len(lines)} lines)"

    def test_dockerfile_or_docker_compose(self):
        docker_files = [
            SMOKE_PROJECT / "Dockerfile",
            SMOKE_PROJECT / "docker-compose.yml",
            SMOKE_PROJECT / "docker-compose.yaml",
        ]
        found = any(p.exists() for p in docker_files)
        if not found:
            pytest.skip("No Docker files found (deployment may use different strategy)")


# ══════════════════════════════════════════════════════════════════════════════
#  11. STAGE 11: DOCUMENTATION & HANDOVER
# ══════════════════════════════════════════════════════════════════════════════


class TestStage11Docs:
    """Stage 11 must produce comprehensive documentation."""

    def test_readme_exists(self):
        assert (SMOKE_PROJECT / "README.md").exists(), "Missing README.md"

    def test_readme_is_substantial(self):
        content = _read(SMOKE_PROJECT / "README.md")
        lines = content.strip().splitlines()
        assert len(lines) >= 20, f"README too short ({len(lines)} lines)"

    def test_architecture_doc_exists(self):
        arch_files = (
            _find_files("ARCHITECTURE.md", SMOKE_PROJECT / "docs")
            + _find_files("ARCHITECTURE.md", SMOKE_PROJECT)
        )
        assert len(arch_files) >= 1, "No ARCHITECTURE.md found"

    def test_handover_doc_exists(self):
        handover_files = (
            _find_files("HANDOVER.md", SMOKE_PROJECT / "docs")
            + _find_files("HANDOVER.md", SMOKE_PROJECT)
        )
        assert len(handover_files) >= 1, "No HANDOVER.md found"

    def test_changelog_exists(self):
        changelog = (
            _find_files("CHANGELOG.md", SMOKE_PROJECT)
            + _find_files("CHANGELOG.md", SMOKE_PROJECT / "docs")
        )
        if not changelog:
            pytest.skip("CHANGELOG.md not found (optional)")

    def test_pipeline_summary_exists(self):
        summaries = _find_files("PIPELINE-SUMMARY.md", SMOKE_PROJECT / "docs" / "stages")
        assert len(summaries) >= 1, "Missing docs/stages/PIPELINE-SUMMARY.md"

    def test_pipeline_summary_references_all_stages(self):
        summaries = _find_files("PIPELINE-SUMMARY.md", SMOKE_PROJECT / "docs" / "stages")
        if not summaries:
            pytest.skip("PIPELINE-SUMMARY.md missing")
        content = _read(summaries[0])
        for i in range(1, 12):
            assert f"Stage {i}" in content or f"stage_{i}" in content or f"Stage{i}" in content, (
                f"Pipeline summary missing reference to Stage {i}"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  12. CROSS-STAGE CONTRACT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestCrossStageContracts:
    """Validate that artifacts from earlier stages are consumed by later stages."""

    def test_plan_references_prd_requirements(self):
        """Stage 2 plan should trace back to Stage 1 PRD requirement IDs."""
        prds = _find_files("*-prd.md", SMOKE_PROJECT / "docs" / "plans")
        plans = _find_files("*-plan.md", SMOKE_PROJECT / "docs" / "plans")
        if not prds or not plans:
            pytest.skip("PRD or plan missing")

        prd_content = _read(prds[0])
        plan_content = _read(plans[0])

        # Extract US-xxx IDs from PRD
        prd_ids = set(re.findall(r"US-\d+", prd_content))
        if not prd_ids:
            pytest.skip("No US-xxx IDs in PRD")

        # At least some should appear in the plan
        plan_ids = set(re.findall(r"US-\d+", plan_content))
        overlap = prd_ids & plan_ids
        assert len(overlap) > 0, (
            f"Plan does not reference any PRD user story IDs. "
            f"PRD has {prd_ids}, plan has {plan_ids}"
        )

    def test_tests_exist_for_api_endpoints(self):
        """Stage 6 tests should cover the API endpoints defined in Stage 2 plan."""
        test_files = _find_files("test_*.py", SMOKE_PROJECT / "tests")
        if not test_files:
            pytest.skip("No test files")

        all_test_content = "\n".join(_read(f) for f in test_files)

        # Should reference common API patterns
        api_patterns = ["todo", "user", "auth", "login", "register"]
        found = sum(1 for p in api_patterns if p.lower() in all_test_content.lower())
        assert found >= 2, (
            f"Tests only reference {found}/5 expected API concepts "
            f"({api_patterns})"
        )

    def test_source_implements_api_endpoints(self):
        """Stage 7 source should implement the API endpoints from the plan."""
        src_files = _find_files("*.py", SMOKE_PROJECT / "src")
        if not src_files:
            src_files = _find_files("*.py", SMOKE_PROJECT / "app")
        if not src_files:
            pytest.skip("No source files")

        all_src = "\n".join(_read(f) for f in src_files)

        # Should contain FastAPI route decorators
        assert re.search(r"@(app|router)\.(get|post|put|delete|patch)", all_src), (
            "Source code missing FastAPI route decorators"
        )

    def test_review_gate_ran_after_implementation(self):
        """Stage 9 review should have run after Stage 7 implementation exists."""
        review_path = SMOKE_PROJECT / "test-results" / "review-gate.json"
        src_files = _find_files("*.py", SMOKE_PROJECT / "src")
        if not src_files:
            src_files = _find_files("*.py", SMOKE_PROJECT / "app")

        if not review_path.exists():
            pytest.skip("review-gate.json missing")

        assert len(src_files) >= 1, (
            "Review gate ran but no source files exist — Stage 7 didn't produce code"
        )
