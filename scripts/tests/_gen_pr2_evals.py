"""One-shot eval scenario generator for PR2 agents.

Generates eval scenarios per spec §4 EVALS schema for:
- github-issue-manager-agent (5 scenarios)
- failure-triage-agent (6 scenarios — REPLACES the PR1 skeleton scenarios)
- test-healer-agent (5 scenarios — commit_mode behavior)
- test-failure-analyzer-agent (5 scenarios — multi-lane awareness)

This script is a one-shot: run once during PR2 implementation, scenarios are
then committed. Not part of the runtime test suite.

Run from repo root:
    python scripts/tests/_gen_pr2_evals.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = ROOT / "core" / ".claude" / "agents"


def make_issue_manager_scenarios():
    return [
        {
            "scenario_name": "successful-create-new-issue",
            "description": "Clean preflight + new failure (no dedup hit) → new GitHub Issue created.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/api/test_users.py::test_create_user",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "failing_commit_sha_short": "abc1234",
                    "category": "SCHEMA_MISMATCH",
                    "confidence": 0.91,
                    "evidence_summary": "Pydantic UserCreate model expects 'full_name' but POST sends 'name'",
                    "recommended_action": "AUTO_HEAL",
                    "failure_profile": {
                        "functional": {"result": "FAILED", "error": "AssertionError: 422", "stack": "..."},
                        "api": {"result": "FAILED", "error": "schema mismatch", "stack": "..."},
                        "ui": {"result": "n/a"}
                    }
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true", "GH_REMOTE_OK": "github.com", "GH_PERMISSION": "WRITE"}
            },
            "expected_contract": {
                "test_id": "tests/api/test_users.py::test_create_user",
                "result": "CREATED",
                "issue_number": "*",
                "issue_url": "*"
            },
            "rubric_hints": {
                "trigger_reliability": "Agent runs preflight, finds it clean, then writes profile JSON and invokes /create-github-issue",
                "output_structure": "Return contract has exactly result/issue_number/issue_url + test_id (no extra noise)",
                "non_negotiable_adherence": "NN#1 propagation works for non-blocked path too; NN#2 single Issue per test (not per lane); NN#3 dedup result honored (deduped=false here)",
                "side_effect_correctness": "Wrote profile JSON to test-results/issue-profiles/; invoked Skill(/create-github-issue) exactly once; gh issue create runs",
                "error_propagation": "Success path returns structured CREATED contract, not freeform prose"
            }
        },
        {
            "scenario_name": "dedup-hit-comments-existing",
            "description": "Same sha256 signature as existing open Issue → comment on existing instead of creating new.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/api/test_users.py::test_create_user",
                    "run_id": "2026-04-24T09-15-00Z_abc1234",
                    "failing_commit_sha_short": "abc1234",
                    "category": "SCHEMA_MISMATCH",
                    "confidence": 0.91,
                    "evidence_summary": "Same root cause as previous run",
                    "recommended_action": "AUTO_HEAL",
                    "failure_profile": {"functional": {"result": "FAILED"}, "api": {"result": "FAILED"}, "ui": {"result": "n/a"}}
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true", "GH_EXISTING_ISSUE": "847"}
            },
            "expected_contract": {"test_id": "*", "result": "DEDUPED", "issue_number": 847, "issue_url": "*"},
            "rubric_hints": {
                "trigger_reliability": "Agent invokes /create-github-issue; skill detects sha256 match in open pipeline-failure Issues from past 30 days",
                "output_structure": "result=DEDUPED (NOT CREATED); issue_number is the EXISTING #847",
                "non_negotiable_adherence": "NN#3: agent propagates deduped result; T2B treats deduped Issue identically for fixer dispatch",
                "side_effect_correctness": "gh issue comment runs against #847; no new Issue created (gh issue list count unchanged)",
                "error_propagation": "Dedup hit is not an error condition — returns DEDUPED, not BLOCKED"
            }
        },
        {
            "scenario_name": "preflight-gh-not-installed-blocked",
            "description": "command -v gh fails → BLOCKED contract returned, no Issue created.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_x.py::test_y",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "failing_commit_sha_short": "abc1234",
                    "category": "LOGIC_BUG",
                    "confidence": 0.95,
                    "evidence_summary": "test failed",
                    "recommended_action": "ISSUE_ONLY",
                    "failure_profile": {"functional": {"result": "FAILED"}, "api": {"result": "n/a"}, "ui": {"result": "n/a"}}
                },
                "filesystem_setup": {},
                "env_setup": {"PATH_NO_GH": "true"}
            },
            "expected_contract": {
                "test_id": "*",
                "result": "BLOCKED",
                "blocker": "GITHUB_NOT_CONNECTED",
                "failed_check": "gh installed",
                "remediation": "*Install from https://cli.github.com/*"
            },
            "rubric_hints": {
                "trigger_reliability": "Agent runs preflight, detects missing gh CLI immediately, returns BLOCKED",
                "output_structure": "BLOCKED contract has all 4 fields: result, blocker, failed_check, remediation",
                "non_negotiable_adherence": "NN#1: hard-fail propagated to parent (T2B will abort entire triage)",
                "side_effect_correctness": "Did NOT invoke gh issue create; did NOT write any state",
                "error_propagation": "Structured BLOCKED contract, NOT freeform error prose"
            }
        },
        {
            "scenario_name": "preflight-gh-not-authenticated-blocked",
            "description": "gh auth status fails → BLOCKED contract returned.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_x.py::test_y",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "failing_commit_sha_short": "abc1234",
                    "category": "LOGIC_BUG",
                    "confidence": 0.95,
                    "evidence_summary": "test failed",
                    "recommended_action": "ISSUE_ONLY",
                    "failure_profile": {"functional": {"result": "FAILED"}, "api": {"result": "n/a"}, "ui": {"result": "n/a"}}
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_FAIL": "true"}
            },
            "expected_contract": {
                "test_id": "*",
                "result": "BLOCKED",
                "blocker": "GITHUB_NOT_CONNECTED",
                "failed_check": "*authenticated*",
                "remediation": "*gh auth login*"
            },
            "rubric_hints": {
                "trigger_reliability": "Preflight check 2 (gh auth status) fails → BLOCKED",
                "output_structure": "remediation field has actionable `gh auth login` command",
                "non_negotiable_adherence": "NN#1: never silently skip; surfaces auth issue to caller",
                "side_effect_correctness": "Did not attempt gh issue create after preflight failure",
                "error_propagation": "Auth failure surfaces with actionable remediation, not generic 'gh failed' message"
            }
        },
        {
            "scenario_name": "non-github-remote-blocked",
            "description": "origin remote is not github.com (e.g., GitLab) → BLOCKED contract.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_x.py::test_y",
                    "run_id": "2026-04-23T14-30-00Z_abc1234",
                    "failing_commit_sha_short": "abc1234",
                    "category": "LOGIC_BUG",
                    "confidence": 0.95,
                    "evidence_summary": "test failed",
                    "recommended_action": "ISSUE_ONLY",
                    "failure_profile": {"functional": {"result": "FAILED"}, "api": {"result": "n/a"}, "ui": {"result": "n/a"}}
                },
                "filesystem_setup": {},
                "env_setup": {"GH_REMOTE_GITLAB": "true"}
            },
            "expected_contract": {
                "test_id": "*",
                "result": "BLOCKED",
                "blocker": "GITHUB_NOT_CONNECTED",
                "failed_check": "*github.com*",
                "remediation": "*GitHub remote*"
            },
            "rubric_hints": {
                "trigger_reliability": "Preflight check 3 (origin contains github.com) fails → BLOCKED",
                "output_structure": "remediation specifies adding GitHub remote (not generic 'remote missing')",
                "non_negotiable_adherence": "NN#1: never assume gh push to a non-github remote will work",
                "side_effect_correctness": "Did not attempt to create Issue against non-GitHub provider",
                "error_propagation": "Cross-provider config issue surfaces clearly"
            }
        }
    ]


def make_failure_triage_pr2_scenarios():
    """REPLACES the PR1 skeleton scenarios — PR2 has full triage body."""
    return [
        {
            "scenario_name": "all-auto-heal-batch-succeeds-end-to-end",
            "description": "3 failed tests all classified AUTO_HEAL → analyzer → issue-manager → fixer → serialize → Issues closed.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN001", "run_id": "RUN001",
                    "failures": [
                        {"test_id": "tests/test_a.py::ta", "failed_lanes": ["functional"], "category_hint": "BROKEN_LOCATOR"},
                        {"test_id": "tests/test_b.py::tb", "failed_lanes": ["functional"], "category_hint": "TIMEOUT_TIMING"},
                        {"test_id": "tests/test_c.py::tc", "failed_lanes": ["functional"], "category_hint": "ASSERTION_ERROR"}
                    ],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true"}
            },
            "expected_contract": {
                "result": "TRIAGE_COMPLETE",
                "issues_created": 3,
                "fixes_applied": 3,
                "fixes_pending": 0,
                "remaining_budget": "*"
            },
            "rubric_hints": {
                "trigger_reliability": "T2B dispatches 3 analyzers → 3 issue-managers → 3 fixers in batches; all confirmation paths fire",
                "output_structure": "TRIAGE_COMPLETE result with counts; remaining_budget propagated for parent T2A",
                "non_negotiable_adherence": "NN#1 single triage owner; NN#2 batched fan-out; NN#3 dispatch budget enforcement; NN#4 hard-fail propagation",
                "side_effect_correctness": "3 Issues created (or deduped), 3 commits land, Issues closed with commit SHA",
                "error_propagation": "Success path returns TRIAGE_COMPLETE, not BLOCKED"
            }
        },
        {
            "scenario_name": "issue-only-skips-fixer-dispatch",
            "description": "Mixed batch: 2 AUTO_HEAL + 1 LOGIC_BUG (ISSUE_ONLY) → only 2 fixers dispatched; LOGIC_BUG Issue stays open with no fix attempt.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN002", "run_id": "RUN002",
                    "failures": [
                        {"test_id": "tests/test_a.py::ta", "failed_lanes": ["functional"], "category_hint": "BROKEN_LOCATOR"},
                        {"test_id": "tests/unit/test_logic.py::tl", "failed_lanes": ["functional"], "category_hint": "LOGIC_BUG"},
                        {"test_id": "tests/test_b.py::tb", "failed_lanes": ["functional"], "category_hint": "ASSERTION_ERROR"}
                    ],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true"}
            },
            "expected_contract": {
                "result": "TRIAGE_COMPLETE",
                "issues_created": 3,
                "fixes_applied": 2,
                "fixes_pending": 0,
                "issue_only_count": 1
            },
            "rubric_hints": {
                "trigger_reliability": "T2B reads recommended_action from analyzer; ISSUE_ONLY → no fixer dispatch",
                "output_structure": "fixes_applied=2 NOT 3; issue_only_count=1 reflects the LOGIC_BUG that stayed unfixed",
                "non_negotiable_adherence": "Auto-fix matrix per spec §3.6 honored: LOGIC_BUG never auto-heals",
                "side_effect_correctness": "LOGIC_BUG Issue created but no fixer commit lands; Issue stays open",
                "error_propagation": "Mixed batch is normal (not error); TRIAGE_COMPLETE result"
            }
        },
        {
            "scenario_name": "github-not-connected-aborts-entire-triage",
            "description": "First issue-manager preflight fails → T2B aborts entire triage immediately (partial_failure_policy: abort_on_first_blocked).",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN003", "run_id": "RUN003",
                    "failures": [
                        {"test_id": "tests/test_a.py::ta", "failed_lanes": ["functional"], "category_hint": "BROKEN_LOCATOR"},
                        {"test_id": "tests/test_b.py::tb", "failed_lanes": ["functional"], "category_hint": "ASSERTION_ERROR"}
                    ],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_FAIL": "true"}
            },
            "expected_contract": {
                "result": "BLOCKED",
                "blocker": "GITHUB_NOT_CONNECTED",
                "failed_at_test": "*",
                "remediation": "*gh auth login*"
            },
            "rubric_hints": {
                "trigger_reliability": "T2B receives BLOCKED from first issue-manager → aborts before processing remaining failures",
                "output_structure": "BLOCKED contract bubbled up to T2A → T1 (chained propagation per spec §3.7.1)",
                "non_negotiable_adherence": "NN#4 hard-fail propagation; partial_failure_policy: abort_on_first_blocked enforced",
                "side_effect_correctness": "No fixers dispatched; no diffs serialized; no escalation report (because abort is not exhaustion)",
                "error_propagation": "BLOCKED contract is the canonical pipeline-blocker shape"
            }
        },
        {
            "scenario_name": "dispatch-budget-exhaustion",
            "description": "Synthetic 30 failures cascade × 3 fix iterations would trip dispatch budget at >100 → BLOCKED.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-BIG", "run_id": "BIG",
                    "failures": [{"test_id": f"tests/test_{i}.py::t", "failed_lanes": ["functional"], "category_hint": "BROKEN_LOCATOR"} for i in range(40)],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true", "MAX_DISPATCHES_LOW": "100"}
            },
            "expected_contract": {
                "result": "BLOCKED",
                "blocker": "DISPATCH_BUDGET_EXCEEDED",
                "dispatch_count": "*",
                "remediation": "*max_total_dispatches*"
            },
            "rubric_hints": {
                "trigger_reliability": "T2B counter increments on every Agent() dispatch; trips at 100 cap",
                "output_structure": "Includes dispatch_count for diagnostic visibility",
                "non_negotiable_adherence": "NN#3 budget enforcement: aborts BEFORE next batch dispatch (not mid-batch)",
                "side_effect_correctness": "Some Issues may be created/fixed before abort; partial state is acknowledged",
                "error_propagation": "Distinct from GITHUB_NOT_CONNECTED — different blocker code"
            }
        },
        {
            "scenario_name": "cross-lane-shared-root-cause-single-issue",
            "description": "Same test fails in functional + API → analyzer returns single SCHEMA_MISMATCH category → ONE consolidated Issue created.",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-RUN004", "run_id": "RUN004",
                    "failures": [
                        {"test_id": "tests/api/test_users.py::tu", "failed_lanes": ["functional", "api"], "evidence": {"functional": "...", "api": "..."}}
                    ],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true"}
            },
            "expected_contract": {
                "result": "TRIAGE_COMPLETE",
                "issues_created": 1,
                "cross_lane_root_causes_detected": 1
            },
            "rubric_hints": {
                "trigger_reliability": "T2B dispatches analyzer with multi-lane data; analyzer collapses to single category",
                "output_structure": "issues_created=1 (NOT 2 even though 2 lanes failed) — consolidation works",
                "non_negotiable_adherence": "NN#2 batched fan-out preserved; NN#3 dispatch budget tracked correctly",
                "side_effect_correctness": "Single GitHub Issue with both lanes' findings in body (per /create-github-issue template)",
                "error_propagation": "Cross-lane consolidation is normal flow; TRIAGE_COMPLETE result"
            }
        },
        {
            "scenario_name": "batch-of-12-fans-out-as-3-batches-of-5",
            "description": "12 failures with max_concurrent_fixers=5 → fan-out chunks into 3 batches (5+5+2).",
            "input": {
                "dispatch_context": {
                    "pipeline_id": "test-pipeline-BATCH", "run_id": "BATCH",
                    "failures": [{"test_id": f"tests/test_{i}.py::t", "failed_lanes": ["functional"], "category_hint": "BROKEN_LOCATOR"} for i in range(12)],
                    "remaining_budget": 15
                },
                "filesystem_setup": {},
                "env_setup": {"GH_AUTH_OK": "true"}
            },
            "expected_contract": {
                "result": "TRIAGE_COMPLETE",
                "issues_created": 12,
                "fixes_applied": "*",
                "batch_count": 3
            },
            "rubric_hints": {
                "trigger_reliability": "T2B chunks failures into batches of size max_concurrent_fixers (5)",
                "output_structure": "batch_count=3 (12/5 ceil); confirms cap enforcement",
                "non_negotiable_adherence": "NN#2 batched fan-out works; per-batch dispatch budget check happens before each batch",
                "side_effect_correctness": "Exactly 3 parallel-dispatch waves observed (not 12 simultaneous)",
                "error_propagation": "Large batch is normal; TRIAGE_COMPLETE result"
            }
        }
    ]


def make_test_healer_pr2_scenarios():
    return [
        {
            "scenario_name": "commit-mode-direct-default-commits",
            "description": "Legacy callsite: no commit_mode in dispatch context → defaults to direct (commits via /post-fix-pipeline).",
            "input": {
                "dispatch_context": {
                    "fix_queue_item": {"test_id": "tests/test_a.py::ta", "classification": "BROKEN_LOCATOR"}
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "fix_applied": True,
                "commit_sha": "*",
                "commit_mode_resolved": "direct"
            },
            "rubric_hints": {
                "trigger_reliability": "Healer detects commit_mode is absent → falls back to direct (legacy /fix-loop / e2e-conductor pathway)",
                "output_structure": "Return contract includes commit_sha (because commit happened)",
                "non_negotiable_adherence": "Backward compat preserved per spec §3.14",
                "side_effect_correctness": "Healer invokes /fix-issue without --diff-only flag; /post-fix-pipeline commits",
                "error_propagation": "Backward compat is not an error condition"
            }
        },
        {
            "scenario_name": "commit-mode-diff-only-writes-diff-no-commit",
            "description": "T2B PR2 callsite: commit_mode=diff_only → write diff to test-results/fixes/{N}.diff, NO commit.",
            "input": {
                "dispatch_context": {
                    "issue_number": 1234,
                    "test_id": "tests/test_a.py::ta",
                    "category": "BROKEN_LOCATOR",
                    "evidence": "selector ARIA tree shows...",
                    "commit_mode": "diff_only"
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "fix_applied": True,
                "diff_path": "test-results/fixes/1234.diff",
                "commit_sha": None,
                "commit_mode_resolved": "diff_only"
            },
            "rubric_hints": {
                "trigger_reliability": "Healer detects commit_mode=diff_only and routes to write-diff pathway",
                "output_structure": "diff_path field present; commit_sha is None (no commit happened)",
                "non_negotiable_adherence": "Spec §3.9.2 commit_mode gating honored",
                "side_effect_correctness": "Diff file exists at test-results/fixes/1234.diff; git log shows no new commit",
                "error_propagation": "diff_only path is normal flow"
            }
        },
        {
            "scenario_name": "issue-number-propagated-to-fix-issue",
            "description": "When commit_mode=diff_only AND issue_number provided, healer invokes /fix-issue --diff-only with the issue_number.",
            "input": {
                "dispatch_context": {
                    "issue_number": 5678,
                    "test_id": "tests/api/test_users.py::tu",
                    "category": "SCHEMA_MISMATCH",
                    "commit_mode": "diff_only"
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "fix_applied": True,
                "diff_path": "test-results/fixes/5678.diff",
                "fix_issue_invoked_with": "*5678*"
            },
            "rubric_hints": {
                "trigger_reliability": "issue_number is read from dispatch context, not derived",
                "output_structure": "fix_issue_invoked_with contains the exact issue_number",
                "non_negotiable_adherence": "Spec §3.9 chain: T2B → healer (issue_number) → /fix-issue --diff-only (issue_number) → diff file",
                "side_effect_correctness": "Diff filename matches issue_number (test-results/fixes/5678.diff)",
                "error_propagation": "Issue number must be valid integer; healer rejects malformed values"
            }
        },
        {
            "scenario_name": "skill-tool-grant-not-silently-collapsed",
            "description": "Verify Skill tool is in tools field — without it, Skill('fix-issue') would silently collapse.",
            "input": {
                "dispatch_context": {"static_check": True},
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "tools_field_includes_skill": True,
                "tools_field_excludes_agent": True
            },
            "rubric_hints": {
                "trigger_reliability": "Static check on agent frontmatter — tools field includes Skill (PR1 fix)",
                "output_structure": "Boolean flags reflect frontmatter contents",
                "non_negotiable_adherence": "T3 tier rule: tools must NOT include Agent (per agent-orchestration.md rule 3)",
                "side_effect_correctness": "PR1 fix preserved into PR2 (test-healer-agent didn't lose Skill grant)",
                "error_propagation": "If Skill tool missing, Skill('fix-issue') silently does nothing — caught by this scenario"
            }
        },
        {
            "scenario_name": "backward-compat-no-commit-mode-defaults-direct",
            "description": "Existing /fix-loop and e2e-conductor-agent callsites continue to work without specifying commit_mode.",
            "input": {
                "dispatch_context": {
                    "fix_queue_item": {"test_id": "tests/e2e/test_login.spec.ts::login", "classification": "TIMING"}
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "fix_applied": True,
                "commit_sha": "*",
                "commit_mode_resolved": "direct"
            },
            "rubric_hints": {
                "trigger_reliability": "Healer detects e2e-conductor dispatch shape (no commit_mode key) → direct",
                "output_structure": "Same as commit-mode-direct-default-commits scenario; redundant verification",
                "non_negotiable_adherence": "Spec §3.14 backward compat: e2e-conductor-agent callsite unchanged",
                "side_effect_correctness": "Healer commits via /post-fix-pipeline as before",
                "error_propagation": "Default behavior preserved"
            }
        }
    ]


def make_analyzer_pr2_scenarios():
    return [
        {
            "scenario_name": "regex-pre-classification-short-circuits-llm",
            "description": "Locator error matches the 18-rule regex set → BROKEN_LOCATOR with confidence 0.93, no LLM call.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_x.py::tx",
                    "failed_lanes": ["functional"],
                    "evidence": {"functional": {"error": "Locator: getByRole('button', {name: 'Submit'}).click() not found"}}
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "test_id": "*",
                "category": "BROKEN_LOCATOR",
                "confidence": 0.93,
                "classification_source": "regex_rule_*"
            },
            "rubric_hints": {
                "trigger_reliability": "Regex pattern Locator: matches → short-circuits LLM",
                "output_structure": "classification_source explicitly states regex (not 'llm')",
                "non_negotiable_adherence": "Existing 18 regex rules from 2026-04-22 overhaul preserved",
                "side_effect_correctness": "No LLM token consumption (faster, deterministic)",
                "error_propagation": "Regex hit is normal flow"
            }
        },
        {
            "scenario_name": "multi-lane-functional-plus-api-schema-mismatch",
            "description": "Same test fails in functional + API with schema-related errors → consolidated SCHEMA_MISMATCH category.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/api/test_users.py::tu",
                    "failed_lanes": ["functional", "api"],
                    "evidence": {
                        "functional": {"error": "AssertionError: 422 != 201"},
                        "api": {"error": "Expected field 'full_name' missing in request"}
                    }
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "test_id": "*",
                "category": "SCHEMA_MISMATCH",
                "confidence": "*",
                "failed_lanes": ["functional", "api"],
                "cross_lane_root_cause": True
            },
            "rubric_hints": {
                "trigger_reliability": "Multi-lane evidence is BOTH passed to analyzer; analyzer recognizes schema-related errors as one root cause",
                "output_structure": "cross_lane_root_cause=True flag; failed_lanes reflects all 2",
                "non_negotiable_adherence": "Spec §3.5 cross-lane root-cause detection works",
                "side_effect_correctness": "Single category emitted (NOT one per lane)",
                "error_propagation": "Multi-lane consolidation is normal flow"
            }
        },
        {
            "scenario_name": "confidence-threshold-gating-issue-only",
            "description": "Confidence below 0.85 → recommended_action=ISSUE_ONLY (don't auto-heal under-confident classifications).",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_unclear.py::tu",
                    "failed_lanes": ["functional"],
                    "evidence": {"functional": {"error": "AssertionError: ambiguous"}}
                },
                "filesystem_setup": {},
                "env_setup": {"FORCE_LOW_CONFIDENCE": "0.4"}
            },
            "expected_contract": {
                "test_id": "*",
                "confidence": "<0.85",
                "recommended_action": "ISSUE_ONLY"
            },
            "rubric_hints": {
                "trigger_reliability": "Confidence threshold check fires when LLM is uncertain",
                "output_structure": "recommended_action explicitly ISSUE_ONLY (NOT AUTO_HEAL)",
                "non_negotiable_adherence": "Spec §3.6 confidence threshold (0.85) honored",
                "side_effect_correctness": "Healer downstream MUST NOT attempt auto-fix on this test",
                "error_propagation": "Low confidence is not an error; routes to safer ISSUE_ONLY"
            }
        },
        {
            "scenario_name": "needs-contract-validation-when-api-lane-no-tooling",
            "description": "API lane reported NEEDS_CONTRACT_VALIDATION (no contract files) → analyzer preserves and routes to ISSUE_ONLY.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/api/test_x.py::tx",
                    "failed_lanes": ["api"],
                    "evidence": {"api": {"category": "NEEDS_CONTRACT_VALIDATION", "details": "no openapi.yaml, no pact/"}}
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "test_id": "*",
                "category": "NEEDS_CONTRACT_VALIDATION",
                "recommended_action": "ISSUE_ONLY"
            },
            "rubric_hints": {
                "trigger_reliability": "Pre-classified category from lane worker is preserved (analyzer doesn't override)",
                "output_structure": "category passed through; recommended_action correctly mapped per spec §3.6 matrix",
                "non_negotiable_adherence": "NEEDS_CONTRACT_VALIDATION is a NEW PR1 category; analyzer recognizes it",
                "side_effect_correctness": "Issue created surfaces 'add contract tooling' recommendation",
                "error_propagation": "Tooling absence is not an error in analyzer; surfaces actionable Issue"
            }
        },
        {
            "scenario_name": "backward-compat-single-lane-data",
            "description": "Legacy callsite passes only one lane's data → analyzer produces same classification as before.",
            "input": {
                "dispatch_context": {
                    "test_id": "tests/test_y.py::ty",
                    "failed_lanes": ["functional"],
                    "evidence": {"functional": {"error": "TimeoutError"}}
                },
                "filesystem_setup": {},
                "env_setup": {}
            },
            "expected_contract": {
                "test_id": "*",
                "category": "TIMEOUT_TIMING",
                "failed_lanes": ["functional"]
            },
            "rubric_hints": {
                "trigger_reliability": "Single-lane data is treated as the only signal; no multi-lane consolidation attempted",
                "output_structure": "Same shape as PR1 single-signal contract (no cross_lane_root_cause field needed)",
                "non_negotiable_adherence": "Spec §3.14 backward compat: single-lane callsites unchanged",
                "side_effect_correctness": "TIMEOUT_TIMING is correctly classified per existing 18-rule regex",
                "error_propagation": "Backward compat is normal flow"
            }
        }
    ]


def main():
    scenarios = {
        "github-issue-manager-agent": make_issue_manager_scenarios(),
        "failure-triage-agent": make_failure_triage_pr2_scenarios(),
        "test-healer-agent": make_test_healer_pr2_scenarios(),
        "test-failure-analyzer-agent": make_analyzer_pr2_scenarios(),
    }
    total = 0
    for agent_name, agent_scenarios in scenarios.items():
        base_dir = AGENTS_DIR / agent_name / "evals" / "scenarios"
        base_dir.mkdir(parents=True, exist_ok=True)
        # For failure-triage-agent: REPLACE PR1 skeleton scenarios
        if agent_name == "failure-triage-agent":
            for old_file in base_dir.glob("*.json"):
                old_file.unlink()
        for sc in agent_scenarios:
            path = base_dir / f"{sc['scenario_name']}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sc, f, indent=2, ensure_ascii=False)
                f.write("\n")
            total += 1
    print(f"OK - wrote {total} eval scenarios across {len(scenarios)} agents")


if __name__ == "__main__":
    main()
