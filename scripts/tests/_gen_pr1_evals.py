"""One-shot eval scenario generator for PR1 agents.

Generates 16 eval scenarios across 3 agents per spec §4 EVALS:
- failure-triage-agent (5 scenarios — PR1 skeleton behavior)
- tester-agent (5 scenarios — lane parameter + verdict authority)
- test-scout-agent (6 scenarios — classify mode, accumulate, sidecar overflow)

This script is a one-shot: run once during PR1 implementation, scenarios are
then committed. Not part of the runtime test suite.

Run from repo root:
    python scripts/tests/_gen_pr1_evals.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = ROOT / "core" / ".claude" / "agents"


def make_failure_triage_scenarios():
    return [
        {
            "scenario_name": "no-op-skeleton-empty-failures",
            "description": "PR1 skeleton receives empty failure set; returns NO_OP_PR1_SKELETON immediately.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-2026-04-23T14-30-00Z_abc1234",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "failures": [],
                    "remaining_budget": 15,
                },
                "filesystem_setup": {},
                "env_setup": {},
            },
            "expected_contract": {
                "result": "NO_OP_PR1_SKELETON",
                "failures_received": 0,
                "next_action": "T2A bubble-up to T1 inline Issue creation",
            },
            "rubric_hints": {
                "trigger_reliability": "Agent recognizes dispatch context and immediately enters PR1 skeleton mode",
                "output_structure": "Return contract has exactly result/failures_received/next_action keys",
                "non_negotiable_adherence": "Honors NN#1 return-immediately, NN#2 no file mods, NN#4 no Agent() calls",
                "side_effect_correctness": "Zero file writes; zero gh CLI; zero git ops",
                "error_propagation": "Empty failures is not an error -- returns NO_OP_PR1_SKELETON not BLOCKED",
            },
        },
        {
            "scenario_name": "no-op-skeleton-with-failures",
            "description": "PR1 skeleton receives 5 failures; counts them in failures_received but returns NO_OP_PR1_SKELETON.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN_X",
                    "run_id": "RUN_X",
                    "failures": [
                        {"test_id": f"tests/test_{i}.py::t", "failed_lanes": ["functional"]}
                        for i in range(5)
                    ],
                    "remaining_budget": 15,
                },
                "filesystem_setup": {},
                "env_setup": {},
            },
            "expected_contract": {
                "result": "NO_OP_PR1_SKELETON",
                "failures_received": 5,
                "next_action": "T2A bubble-up to T1 inline Issue creation",
            },
            "rubric_hints": {
                "trigger_reliability": "Agent counts failures correctly without analyzing them",
                "output_structure": "failures_received reflects input count exactly",
                "non_negotiable_adherence": "Does NOT call analyzer, issue-manager, or healer (PR1 skeleton)",
                "side_effect_correctness": "No Issue creation; no commits; T1 handles Issue creation in PR1",
                "error_propagation": "Non-empty failures still produces NO_OP -- failures bubbled to T1",
            },
        },
        {
            "scenario_name": "no-op-skeleton-pr2-categories-deferred",
            "description": "Failures with PR2 categories (SCHEMA_MISMATCH/CONTRACT_BROKEN) -- skeleton MUST NOT branch on them in PR1.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN_Y",
                    "run_id": "RUN_Y",
                    "failures": [
                        {
                            "test_id": "tests/api/test_users.py::tu",
                            "failed_lanes": ["functional", "api"],
                            "category_hint": "SCHEMA_MISMATCH",
                        }
                    ],
                    "remaining_budget": 15,
                },
                "filesystem_setup": {},
                "env_setup": {},
            },
            "expected_contract": {
                "result": "NO_OP_PR1_SKELETON",
                "failures_received": 1,
                "next_action": "T2A bubble-up to T1 inline Issue creation",
            },
            "rubric_hints": {
                "trigger_reliability": "Agent does NOT branch on category_hint in PR1 -- skeleton is category-agnostic",
                "output_structure": "Same NO_OP contract regardless of input categories",
                "non_negotiable_adherence": "T1 handles SCHEMA_MISMATCH per its PR1 extension",
                "side_effect_correctness": "Does not invoke github-issue-manager-agent (does not exist in PR1)",
                "error_propagation": "Unknown category is not an error in PR1 -- pass through",
            },
        },
        {
            "scenario_name": "no-op-skeleton-honors-pipeline-id",
            "description": "Pipeline ID present -- skeleton acknowledges but still returns NO_OP.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN999",
                    "run_id": "RUN999",
                    "failures": [],
                    "remaining_budget": 12,
                },
                "filesystem_setup": {},
                "env_setup": {},
            },
            "expected_contract": {
                "result": "NO_OP_PR1_SKELETON",
                "failures_received": 0,
                "next_action": "T2A bubble-up to T1 inline Issue creation",
            },
            "rubric_hints": {
                "trigger_reliability": "Pipeline ID is read but does not change behavior in PR1 skeleton",
                "output_structure": "Contract is mode-independent (no pipeline_id echoed back)",
                "non_negotiable_adherence": "Skeleton mode is identical for dispatched and standalone (PR1)",
                "side_effect_correctness": "remaining_budget is not consumed in PR1 (no fixer dispatches)",
                "error_propagation": "All inputs valid -- no error to propagate",
            },
        },
        {
            "scenario_name": "no-op-skeleton-large-failure-batch",
            "description": "Large failure set (50) -- skeleton must not attempt batched fan-out in PR1.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-BIG",
                    "run_id": "BIG",
                    "failures": [
                        {"test_id": f"tests/test_{i}.py::t", "failed_lanes": ["functional"]}
                        for i in range(50)
                    ],
                    "remaining_budget": 15,
                },
                "filesystem_setup": {},
                "env_setup": {},
            },
            "expected_contract": {
                "result": "NO_OP_PR1_SKELETON",
                "failures_received": 50,
                "next_action": "T2A bubble-up to T1 inline Issue creation",
            },
            "rubric_hints": {
                "trigger_reliability": "Agent does NOT trip dispatch budget by trying to fan out 50 fixers in PR1",
                "output_structure": "failures_received: 50 documented honestly even though no triage happened",
                "non_negotiable_adherence": "PR2 batch fan-out logic stays inactive in PR1",
                "side_effect_correctness": "Zero state files written, zero subagent dispatches at scale",
                "error_propagation": "Large input is not an error -- handled identically to small input",
            },
        },
    ]


def make_tester_scenarios():
    return [
        {
            "scenario_name": "lane-functional-non-ui-exit-code-authority",
            "description": "Functional lane, non-UI test (pytest unit) -- exit code is authoritative.",
            "input": {
                "dispatch_context": {
                    "lane": "functional",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "queue": ["tests/unit/test_logic_bug.py::test_add_two_plus_three_equals_five"],
                    "capture_proof": True,
                },
                "filesystem_setup": {"tests/unit/test_logic_bug.py": "fixture-content-from-playwright-demo"},
                "env_setup": {},
            },
            "expected_contract": {
                "lane": "functional",
                "tests_processed": 1,
                "passed": 0,
                "failed": 1,
                "failures": [{"test_id": "*", "category_hint": "LOGIC_BUG"}],
            },
            "rubric_hints": {
                "trigger_reliability": "Agent runs pytest with --capture-proof and detects exit code = failure",
                "output_structure": "Lane contract includes lane/tests_processed/passed/failed/failures per spec",
                "non_negotiable_adherence": "NN#2: exit code is authoritative for non-UI functional; NN#4: writes test-results/functional.jsonl",
                "side_effect_correctness": "Writes test-results/functional.json + .jsonl; no screenshots for non-UI by default",
                "error_propagation": "Test failure surfaces in failures[] with category_hint, not BLOCKED",
            },
        },
        {
            "scenario_name": "lane-functional-ui-screenshot-authority",
            "description": "Functional lane, UI test (Playwright) -- screenshot is authoritative even if exit code is 0.",
            "input": {
                "dispatch_context": {
                    "lane": "functional",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "queue": ["tests/checkout.spec.ts::checkout flow"],
                    "capture_proof": True,
                },
                "filesystem_setup": {"tests/checkout.spec.ts": "fixture-from-playwright-demo"},
                "env_setup": {},
            },
            "expected_contract": {
                "lane": "functional",
                "tests_processed": 1,
                "passed": "*",
                "failed": "*",
                "failures": "*",
            },
            "rubric_hints": {
                "trigger_reliability": "Agent detects Playwright test, captures screenshot to test-evidence/{run_id}/screenshots/",
                "output_structure": "manifest.json updated with verdict_source: screenshot for UI tests",
                "non_negotiable_adherence": "NN#2 lane=functional UI: screenshot is authoritative; NN#3: never bypass screenshot capture",
                "side_effect_correctness": "Screenshots land in test-evidence/{run_id}/screenshots/{test}.{pass|fail}.png",
                "error_propagation": "Visual divergence surfaces with category_hint VISUAL_REGRESSION",
            },
        },
        {
            "scenario_name": "lane-api-with-contract-test",
            "description": "API lane with contract files -- combined verdict (pytest AND /contract-test).",
            "input": {
                "dispatch_context": {
                    "lane": "api",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "queue": ["tests/api/test_users.py::test_create_user_with_wrong_field_name_returns_422"],
                },
                "filesystem_setup": {
                    "openapi.yaml": "openapi: 3.0.0\ninfo: {title: api, version: 1.0.0}\npaths: {}",
                    "tests/api/test_users.py": "fixture-content",
                },
                "env_setup": {},
            },
            "expected_contract": {"lane": "api", "tests_processed": 1, "passed": "*", "failed": "*"},
            "rubric_hints": {
                "trigger_reliability": "Agent detects openapi.yaml and invokes Skill(contract-test) after pytest",
                "output_structure": "Lane contract includes both pytest verdict AND contract-test verdict",
                "non_negotiable_adherence": "NN#2 lane=api: combined exit code + contract-test; emits CONTRACT_BROKEN if drift",
                "side_effect_correctness": "Skill(contract-test) invoked once per lane invocation, after pytest",
                "error_propagation": "Contract drift surfaces as CONTRACT_BROKEN in failures[]",
            },
        },
        {
            "scenario_name": "lane-api-no-contract-tooling-NEEDS_CONTRACT_VALIDATION",
            "description": "API lane with NO contract files -- emits NEEDS_CONTRACT_VALIDATION (treated as FAILED).",
            "input": {
                "dispatch_context": {
                    "lane": "api",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "queue": ["tests/api/test_users.py::test_request_uses_httpx_client"],
                },
                "filesystem_setup": {"tests/api/test_users.py": "fixture-no-contracts"},
                "env_setup": {},
            },
            "expected_contract": {
                "lane": "api",
                "tests_processed": 1,
                "failed": 1,
                "failures": [{"test_id": "*", "category_hint": "NEEDS_CONTRACT_VALIDATION"}],
            },
            "rubric_hints": {
                "trigger_reliability": "Agent detects absence of openapi.yaml + pact/ + .pact/ → emits NEEDS_CONTRACT_VALIDATION",
                "output_structure": "category_hint = NEEDS_CONTRACT_VALIDATION (NEW PR1 category)",
                "non_negotiable_adherence": "NN#2: lane=api WITHOUT contract tooling MUST emit NEEDS_CONTRACT_VALIDATION",
                "side_effect_correctness": "Does NOT invoke /contract-test; does NOT silently skip",
                "error_propagation": "NEEDS_CONTRACT_VALIDATION surfaces in failures[] with INFRASTRUCTURE-level severity",
            },
        },
        {
            "scenario_name": "legacy-no-lane-parameter-backward-compat",
            "description": "Legacy invocation WITHOUT lane parameter -- defaults to single-lane mode for backward compat.",
            "input": {
                "dispatch_context": {"queue": ["tests/test_login.py::test_oauth"]},
                "filesystem_setup": {"tests/test_login.py": "fixture-content"},
                "env_setup": {},
            },
            "expected_contract": {"tests_processed": 1, "passed": "*", "failed": "*"},
            "rubric_hints": {
                "trigger_reliability": "Agent recognizes lane parameter is absent → falls back to legacy single-lane",
                "output_structure": "Return contract is in legacy shape (no lane field; no .jsonl)",
                "non_negotiable_adherence": "NN#1: lane parameter is mandatory ONLY for three-lane T2A dispatch",
                "side_effect_correctness": "Does not write to test-results/{lane}.jsonl (no lane); legacy report only",
                "error_propagation": "Backward compat is not an error -- normal verdict",
            },
        },
    ]


def make_scout_scenarios():
    return [
        {
            "scenario_name": "classify-mode-basic-functional-only",
            "description": "Single unit test, no path/import signals -- classified as functional-only.",
            "input": {
                "dispatch_context": {"mode": "classify", "pipeline_id": "test-pipeline-RUN001", "run_id": "RUN001"},
                "filesystem_setup": {"tests/test_simple.py": "def test_x(): assert 1 == 1"},
                "env_setup": {},
            },
            "expected_contract": {
                "mode": "classify",
                "tests_discovered": 1,
                "queue_counts": {"functional": 1, "api": 0, "ui": 0},
                "overlap_count": 0,
            },
            "rubric_hints": {
                "trigger_reliability": "Agent enters classify mode on `mode: classify`; does NOT execute tests",
                "output_structure": "Return contract per spec §3.1: mode/tests_discovered/queue_counts/overlap_count",
                "non_negotiable_adherence": "NN#9 classify does NOT execute; NN#7 schema_version 2.0.0 written",
                "side_effect_correctness": "Writes .workflows/testing-pipeline/sub/test-pipeline.json with queues + tracks_required_per_test",
                "error_propagation": "No errors expected for valid input",
            },
        },
        {
            "scenario_name": "classify-mode-api-track-from-path",
            "description": "Test in tests/api/ → classified as functional + api.",
            "input": {
                "dispatch_context": {"mode": "classify", "pipeline_id": "test-pipeline-RUN002", "run_id": "RUN002"},
                "filesystem_setup": {"tests/api/test_users.py": "import httpx\ndef test_x(): pass"},
                "env_setup": {},
            },
            "expected_contract": {
                "mode": "classify",
                "tests_discovered": 1,
                "queue_counts": {"functional": 1, "api": 1, "ui": 0},
                "overlap_count": 0,
            },
            "rubric_hints": {
                "trigger_reliability": "Path glob (**/tests/api/**) matches → API track required",
                "output_structure": "tracks_required_per_test entry includes both functional and api",
                "non_negotiable_adherence": "NN#6: ALL detection rules run; path match adds API track",
                "side_effect_correctness": "queues.api array contains test_id; queues.ui is empty",
                "error_propagation": "No errors",
            },
        },
        {
            "scenario_name": "classify-mode-ui-track-from-import",
            "description": "Test in tests/ but imports Playwright → classified as functional + ui.",
            "input": {
                "dispatch_context": {"mode": "classify", "pipeline_id": "test-pipeline-RUN003", "run_id": "RUN003"},
                "filesystem_setup": {
                    "tests/checkout.spec.ts": "import { test } from \"@playwright/test\";\ntest(\"checkout\", async ({ page }) => {});"
                },
                "env_setup": {},
            },
            "expected_contract": {
                "mode": "classify",
                "tests_discovered": 1,
                "queue_counts": {"functional": 1, "api": 0, "ui": 1},
                "overlap_count": 0,
            },
            "rubric_hints": {
                "trigger_reliability": "@playwright/test import detected → UI track required",
                "output_structure": "tracks_required_per_test entry includes functional and ui; NOT api",
                "non_negotiable_adherence": "NN#6: import scan runs even though path didn't match API",
                "side_effect_correctness": "queues.ui contains test_id; queues.api is empty",
                "error_propagation": "No errors",
            },
        },
        {
            "scenario_name": "classify-mode-accumulate-overlap",
            "description": "Test in tests/api/ AND imports Playwright → BOTH api and ui (accumulate -- closes Reviewer Gap 9).",
            "input": {
                "dispatch_context": {"mode": "classify", "pipeline_id": "test-pipeline-RUN004", "run_id": "RUN004"},
                "filesystem_setup": {
                    "tests/api/test_widget.spec.ts": "import { test } from \"@playwright/test\";\ntest(\"widget\", async ({ page }) => { await page.request.get(\"/api/widget\"); });"
                },
                "env_setup": {},
            },
            "expected_contract": {
                "mode": "classify",
                "tests_discovered": 1,
                "queue_counts": {"functional": 1, "api": 1, "ui": 1},
                "overlap_count": 1,
            },
            "rubric_hints": {
                "trigger_reliability": "BOTH path glob (api) AND import scan (ui) match -- accumulate not first-match-wins",
                "output_structure": "tracks_required_per_test entry includes all three: functional, api, ui",
                "non_negotiable_adherence": "NN#6 explicit accumulate semantics; overlap_count incremented",
                "side_effect_correctness": "Test appears in BOTH queues.api AND queues.ui (duplicated test_id by design)",
                "error_propagation": "No errors -- overlap is intentional",
            },
        },
        {
            "scenario_name": "classify-mode-sidecar-overflow",
            "description": "Project with 1500 functional tests → queue exceeds 1000, written to sidecar file.",
            "input": {
                "dispatch_context": {"mode": "classify", "pipeline_id": "test-pipeline-RUN005", "run_id": "RUN005"},
                "filesystem_setup": {f"tests/test_{i:04d}.py": "def test_x(): pass" for i in range(1500)},
                "env_setup": {},
            },
            "expected_contract": {
                "mode": "classify",
                "tests_discovered": 1500,
                "queue_counts": {"functional": 1500, "api": 0, "ui": 0},
                "sidecar_files_created": [".workflows/testing-pipeline/sub/queues/functional.json"],
            },
            "rubric_hints": {
                "trigger_reliability": "Agent detects queue > 1000 → triggers sidecar write",
                "output_structure": "Main state file's queues.functional becomes {sidecar: ..., count: 1500} not inline",
                "non_negotiable_adherence": "NN#8: sidecar overflow rule applied at >1000 entries",
                "side_effect_correctness": "Sidecar file at .workflows/testing-pipeline/sub/queues/functional.json contains 1500 test_ids",
                "error_propagation": "Large queue is not an error -- handled by sidecar pattern",
            },
        },
        {
            "scenario_name": "execute-mode-legacy-e2e-conductor",
            "description": "Backward compat: dispatched without mode: classify → defaults to legacy execute mode.",
            "input": {
                "dispatch_context": {"pipeline_id": "test-pipeline-RUN006", "run_id": "RUN006"},
                "filesystem_setup": {
                    "tests/checkout.spec.ts": "import { test } from \"@playwright/test\";\ntest(\"checkout\", async ({ page }) => {});"
                },
                "env_setup": {},
            },
            "expected_contract": {"tests_executed": "*", "screenshots_captured": "*"},
            "rubric_hints": {
                "trigger_reliability": "Agent recognizes absence of mode: classify → enters legacy execute mode",
                "output_structure": "Legacy contract shape (per existing test-scout body for e2e-conductor)",
                "non_negotiable_adherence": "NN#2: mode auto-detection works; NN#3-5: execute mode rules respected",
                "side_effect_correctness": "Tests executed via npx playwright; screenshots captured to test-evidence/",
                "error_propagation": "Backward compat is not an error condition",
            },
        },
    ]


def main():
    scenarios = {
        "failure-triage-agent": make_failure_triage_scenarios(),
        "tester-agent": make_tester_scenarios(),
        "test-scout-agent": make_scout_scenarios(),
    }
    total = 0
    for agent_name, agent_scenarios in scenarios.items():
        base_dir = AGENTS_DIR / agent_name / "evals" / "scenarios"
        base_dir.mkdir(parents=True, exist_ok=True)
        for sc in agent_scenarios:
            path = base_dir / f"{sc['scenario_name']}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sc, f, indent=2, ensure_ascii=False)
                f.write("\n")
            total += 1
    print(f"OK - wrote {total} eval scenarios across {len(scenarios)} agents")


if __name__ == "__main__":
    main()
