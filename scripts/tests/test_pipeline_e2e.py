"""End-to-end verification for the testing-pipeline overhaul.

This module drives the synthetic playwright-demo fixture through the
pipeline's classification + aggregation logic. It combines three test classes:

1. FixtureStructuralTests — assert the fixture files exist, are valid, and
   cover every pipeline branch (pass, broken-locator, timing, visual-change,
   logic, flaky, infra). These are fast and deps-free.

2. AggregatorScenarioTests — construct simulated `test-results/*.json`
   matching what each scenario would produce after a real pipeline run,
   feed them through `scripts/pipeline_aggregator.py`, and assert the
   verdict + failure surface + contradictions are what the plan expects.

3. PlaywrightSmokeTests (marked `requires_node`) — if Node + Playwright are
   installed, run `npx playwright test --list` against the fixture to prove
   the specs parse and the config is discoverable. Skipped otherwise.

The "run Claude Code headlessly against the fixture and assert the final
pipeline-verdict.json" variant is NOT included — it requires a Claude API
key + full Claude Code install in CI and is outside the narrow scope the
user chose for Phase F (aggregation-only). That end-to-end test is best
performed manually via the README instructions.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.pipeline_aggregator import aggregate, EXIT_FAILED, EXIT_PASSED

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "scripts" / "tests" / "fixtures" / "playwright-demo"
SPEC_DIR = FIXTURE / "tests"
APP_DIR = FIXTURE / "app"


SCENARIOS = {
    "pass":           {"spec": "home.spec.ts"},
    "broken-locator": {"spec": "dashboard.spec.ts", "healer_category": "SELECTOR"},
    "timing":         {"spec": "checkout.spec.ts", "healer_category": "TIMING"},
    "visual-change":  {"spec": "visual.spec.ts"},
    "logic":          {"spec": "logic.spec.ts", "healer_category": "LOGIC_BUG"},
    "flaky":          {"spec": "flaky.spec.ts", "healer_category": "FLAKY_TEST"},
    "infra":          {"spec": "infra.spec.ts", "healer_category": "INFRASTRUCTURE"},
}


# ── 1. Fixture structural tests ────────────────────────────────────────────


class TestFixtureStructure:
    """Confirm the fixture's shape matches the scenario matrix."""

    def test_fixture_directory_exists(self):
        assert FIXTURE.is_dir(), f"fixture missing at {FIXTURE}"

    def test_package_json_declares_playwright_and_express(self):
        pkg = json.loads((FIXTURE / "package.json").read_text(encoding="utf-8"))
        assert "express" in pkg.get("dependencies", {}), (
            "express must be a runtime dependency (the tiny app server)"
        )
        dev = pkg.get("devDependencies", {})
        assert "@playwright/test" in dev, "@playwright/test is required"
        assert "@playwright/mcp" in dev, (
            "@playwright/mcp is a hard dep per test-healer-agent v2.0.0"
        )

    def test_playwright_config_has_required_fields(self):
        text = (FIXTURE / "playwright.config.ts").read_text(encoding="utf-8")
        for required in (
            "webServer",
            "outputDir",
            "screenshot: 'on'",
            "/health",
        ):
            assert required in text, (
                f"playwright.config.ts missing required entry: {required}"
            )

    def test_server_has_scenario_aware_endpoints(self):
        text = (APP_DIR / "server.js").read_text(encoding="utf-8")
        for endpoint in ("/health", "/api/users", "/api/orders", "/api/metric"):
            assert endpoint in text, f"server.js missing endpoint: {endpoint}"
        # Confirm the DEMO_SCENARIO branching is present for each targeted scenario
        for scenario in ("logic", "infra", "flaky"):
            assert scenario in text, (
                f"server.js has no branching for scenario={scenario}"
            )

    @pytest.mark.parametrize("scenario,info", list(SCENARIOS.items()))
    def test_scenario_has_spec_file(self, scenario: str, info: dict):
        path = SPEC_DIR / info["spec"]
        assert path.is_file(), f"missing spec file for scenario {scenario}: {path}"
        content = path.read_text(encoding="utf-8")
        # Every spec starts with the scenario name in a comment so future
        # readers can find the mapping without hunting through HTML.
        assert scenario in content.lower(), (
            f"spec {info['spec']} does not reference its scenario "
            f"identifier {scenario!r} in the file body"
        )

    def test_three_pages_exist(self):
        for page in ("index.html", "dashboard.html", "checkout.html"):
            assert (APP_DIR / page).is_file(), f"missing page: {page}"

    def test_readme_documents_all_scenarios(self):
        readme = (FIXTURE / "README.md").read_text(encoding="utf-8")
        for scenario in SCENARIOS:
            assert scenario in readme, (
                f"README does not document the {scenario!r} scenario"
            )


# ── 2. Aggregator integration tests (simulated scenario results) ───────────


def _fake_scenario_results(tmp_path: Path, scenario: str) -> Path:
    """Write fake test-results/*.json matching what a real pipeline run of
    the named scenario would produce. Returns the results directory."""
    results = tmp_path / "test-results"
    results.mkdir(parents=True, exist_ok=True)

    # Every scenario produces fix-loop and auto-verify results; e2e and
    # others are scenario-specific.
    base = {"schema_version": "1.0.0", "timestamp": "2026-04-22T00:00:00Z"}

    if scenario == "pass":
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )
        (results / "auto-verify.json").write_text(
            json.dumps({
                **base,
                "skill": "auto-verify",
                "result": "PASSED",
                "summary": {"ui_tests": 1, "ui_tests_screenshot_verified": 1},
                "visual_review": {
                    "enabled": True,
                    "confirmed_passes": 1,
                    "overrides": [],
                    "flags": [],
                },
                "failures": [],
            }),
            encoding="utf-8",
        )

    elif scenario == "broken-locator":
        # Healer auto-fixed via SELECTOR — fix-loop reports FIXED
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "FIXED"}),
            encoding="utf-8",
        )
        (results / "auto-verify.json").write_text(
            json.dumps({
                **base,
                "skill": "auto-verify",
                "result": "PASSED",
                "summary": {"ui_tests": 1, "ui_tests_screenshot_verified": 1},
                "visual_review": {"confirmed_passes": 1, "overrides": [], "flags": []},
                "failures": [],
            }),
            encoding="utf-8",
        )

    elif scenario == "timing":
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "FIXED"}),
            encoding="utf-8",
        )
        (results / "auto-verify.json").write_text(
            json.dumps({
                **base,
                "skill": "auto-verify",
                "result": "PASSED",
                "summary": {"ui_tests": 1, "ui_tests_screenshot_verified": 1},
                "visual_review": {"confirmed_passes": 1, "overrides": [], "flags": []},
                "failures": [],
            }),
            encoding="utf-8",
        )

    elif scenario == "visual-change":
        # Visual drift routes to expected_changes — pipeline verdict = PASSED
        # (the aggregator does not fail on EXPECTED_CHANGE; it's surfaced
        # via the NEEDS_REVIEW status in the T1 master's human-readable
        # report, not in the exit code).
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )
        (results / "auto-verify.json").write_text(
            json.dumps({
                **base,
                "skill": "auto-verify",
                "result": "PASSED",
                "summary": {"ui_tests": 1, "ui_tests_screenshot_verified": 1},
                "visual_review": {
                    "confirmed_passes": 0,
                    "overrides": [],
                    "flags": [{"test": "dashboard-heading", "reason": "EXPECTED_CHANGE"}],
                },
                "failures": [],
            }),
            encoding="utf-8",
        )

    elif scenario == "logic":
        # LOGIC_BUG routes to known_issues — pipeline MUST be FAILED and a
        # GitHub Issue signature MUST be surfaced.
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )
        (results / "auto-verify.json").write_text(
            json.dumps({
                **base,
                "skill": "auto-verify",
                "result": "FAILED",
                "summary": {"ui_tests": 1, "ui_tests_screenshot_verified": 1},
                "visual_review": {"confirmed_passes": 0, "overrides": [], "flags": []},
                "failures": [{
                    "test": "users_schema_email_required",
                    "category": "SCHEMA_VALIDATION",
                    "healer_category": "LOGIC_BUG",
                    "verdict_source": "exit_code",
                    "message": "row 0 email was empty",
                }],
                "known_issues": [{
                    "test": "users_schema_email_required",
                    "final_classification": "LOGIC_BUG",
                    "top_stack_frame": "logic.spec.ts:17",
                }],
            }),
            encoding="utf-8",
        )

    elif scenario == "flaky":
        # Flaky quarantine — test moves to known_issues without consuming
        # the retry budget. The e2e conductor reports FAILED because the
        # quarantined test is in known_issues.
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )
        (results / "e2e-pipeline.json").write_text(
            json.dumps({
                **base,
                "skill": "e2e-conductor-agent",
                "result": "FAILED",
                "summary": {
                    "total": 1, "passed": 0, "failed": 1,
                    "healed": 0, "known_issues": 1,
                    "ui_tests": 1, "ui_tests_screenshot_verified": 1,
                },
                "failures": [],
                "known_issues": [{
                    "test": "metric_flaky_endpoint",
                    "final_classification": "FLAKY_TEST",
                    "top_stack_frame": "flaky.spec.ts:15",
                    "reason": "historically_flaky",
                }],
            }),
            encoding="utf-8",
        )

    elif scenario == "infra":
        (results / "fix-loop.json").write_text(
            json.dumps({**base, "skill": "fix-loop", "result": "PASSED"}),
            encoding="utf-8",
        )
        (results / "e2e-pipeline.json").write_text(
            json.dumps({
                **base,
                "skill": "e2e-conductor-agent",
                "result": "FAILED",
                "summary": {
                    "total": 1, "passed": 0, "failed": 1,
                    "healed": 0, "known_issues": 1,
                    "ui_tests": 1, "ui_tests_screenshot_verified": 1,
                },
                "failures": [{
                    "test": "orders_availability",
                    "category": "INFRASTRUCTURE",
                    "healer_category": "INFRASTRUCTURE",
                    "verdict_source": "exit_code",
                    "message": "ECONNREFUSED after env reset retry",
                }],
                "known_issues": [{
                    "test": "orders_availability",
                    "final_classification": "INFRASTRUCTURE",
                    "top_stack_frame": "infra.spec.ts:13",
                }],
            }),
            encoding="utf-8",
        )

    return results


class TestAggregatorScenarios:
    """Feed simulated per-scenario results through the aggregator and assert
    the verdict and the material artifacts that downstream consumers rely on."""

    def test_pass_scenario_returns_passed(self, tmp_path: Path):
        results = _fake_scenario_results(tmp_path, "pass")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id="r-pass")
        assert exit_code == EXIT_PASSED
        assert verdict["result"] == "PASSED"
        assert verdict["stages_completed"] == 2

    def test_broken_locator_returns_passed_after_heal(self, tmp_path: Path):
        """fix-loop reported FIXED; auto-verify confirmed PASSED on the re-run."""
        results = _fake_scenario_results(tmp_path, "broken-locator")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_PASSED
        assert verdict["stage_results"]["fix-loop"] == "FIXED"

    def test_timing_scenario_same_as_broken_locator(self, tmp_path: Path):
        results = _fake_scenario_results(tmp_path, "timing")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_PASSED
        assert verdict["stage_results"]["fix-loop"] == "FIXED"

    def test_visual_change_surfaces_flag_not_failure(self, tmp_path: Path):
        """EXPECTED_CHANGE routes to the visual_review.flags[] array; the
        aggregator keeps the verdict PASSED because no override exists."""
        results = _fake_scenario_results(tmp_path, "visual-change")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_PASSED
        assert verdict["ui_verification_summary"]["flags"] == 1
        assert verdict["ui_verification_summary"]["screenshot_failed"] == 0

    def test_logic_scenario_fails_and_creates_issue_signature(self, tmp_path: Path):
        results = _fake_scenario_results(tmp_path, "logic")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_FAILED
        assert verdict["result"] == "FAILED"
        assert verdict["failures"][0]["healer_category"] == "LOGIC_BUG"
        signatures = verdict["known_issues_created_as_issues"]
        assert len(signatures) == 1
        assert signatures[0]["final_classification"] == "LOGIC_BUG"
        assert len(signatures[0]["signature"]) == 12

    def test_flaky_scenario_surfaces_quarantined_issue(self, tmp_path: Path):
        results = _fake_scenario_results(tmp_path, "flaky")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_FAILED
        issues = verdict["known_issues_created_as_issues"]
        assert any(i["final_classification"] == "FLAKY_TEST" for i in issues)

    def test_infra_scenario_fails_after_env_reset_retry(self, tmp_path: Path):
        results = _fake_scenario_results(tmp_path, "infra")
        exit_code, verdict = aggregate(results, strict_contradictions=False, run_id=None)
        assert exit_code == EXIT_FAILED
        assert any(
            f.get("healer_category") == "INFRASTRUCTURE" for f in verdict["failures"]
        )


# ── 3. Optional Playwright smoke (requires Node) ───────────────────────────


def _has_node_with_playwright() -> bool:
    """Returns True only if `npx playwright --version` succeeds in the
    fixture directory. Used to skip optional smoke tests in bare CI."""
    if shutil.which("npx") is None:
        return False
    try:
        result = subprocess.run(
            ["npx", "--no-install", "playwright", "--version"],
            cwd=FIXTURE,
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


requires_node = pytest.mark.skipif(
    not _has_node_with_playwright(),
    reason="Node + Playwright not available — run `npm install` in the fixture directory",
)


class TestPlaywrightSmoke:
    """Only runs when Node + Playwright are locally installed."""

    @requires_node
    def test_fixture_test_list_discovers_seven_specs(self):
        """`npx playwright test --list` must discover all 7 scenario specs."""
        result = subprocess.run(
            ["npx", "playwright", "test", "--list", "--reporter=list"],
            cwd=FIXTURE,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, (
            f"playwright --list failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Each scenario must be discoverable by name
        combined = (result.stdout + result.stderr).lower()
        for info in SCENARIOS.values():
            assert info["spec"].replace(".spec.ts", "") in combined, (
                f"spec not discovered: {info['spec']}"
            )
