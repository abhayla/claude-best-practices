# Workflow Autonomy Audit Spec

**Date:** 2026-03-31
**Status:** DRAFT
**Scope:** All 11 workflow groups in this hub

## Problem Statement

After recent changes to workflow groups (auto-assignment, SVG diagrams, doc regeneration), we need to verify that all workflows and their sub-workflows are fully autonomous — meaning they can run end-to-end from a slash command without human intervention, with clear error handling on failure.

## Audit Results

### Overall Status

- **8 orchestrated workflows** (with master agents + contracts): ALL fully autonomous
- **3 reference groups** (no master agents): By design, not executable pipelines
- **0 critical missing references** across all workflows
- **Total resources audited:** 207 skills, 49 agents, 28 rules, 8 workflow contracts

### Per-Workflow Summary

| # | Workflow | Master Agent | Contract | Skills | Agents | Rules | Autonomous | Grade |
|---|---------|-------------|----------|--------|--------|-------|-----------|-------|
| 1 | development-loop | Yes | 5 steps | 36 | 8 | 14 | Full (dual-mode) | A |
| 2 | testing-pipeline | Yes | 6 steps | 49 | 15 | 5 | Full (dual-mode) | A |
| 3 | debugging-loop | Yes | 4 steps | 17 | 3 | 1 | Full (dual-mode) | A |
| 4 | code-review | Yes | 3 steps | 16 | 5 | 0 | Full (dual-mode) | A |
| 5 | documentation | Yes | contract | 9 | 3 | 0 | Full (dual-mode) | A |
| 6 | session-continuity | Yes | contract | 7 | 2 | 1 | Full (dual-mode) | A |
| 7 | learning-self-improvement | Yes | 3 steps | 15 | 3 | 1 | Full (dual-mode) | A- |
| 8 | skill-authoring | Yes | 3 steps | 18 | 4 | 6 | Full (dual-mode) | A |
| 9 | ops-quality | No | No | 14 | 7 | 0 | No (reference) | C |
| 10 | hub-sync | No | No | 5 | 0 | 0 | No (reference) | C |
| 11 | stack-frameworks | No | No | 20 | 1 | 6 | No (reference) | B |

### Autonomy Definition

A workflow is "fully autonomous" when it satisfies ALL of:
1. Has a T1 master agent that reads its contract from `config/workflow-contracts.yaml`
2. Supports dual-mode operation (standalone + dispatched by project-manager-agent)
3. All `Skill()` and `Agent()` references resolve to existing files
4. State management via `.workflows/{id}/state.json`
5. Gate enforcement at critical steps (fail-closed semantics)
6. Context passing between steps (upstream artifacts, decisions, summaries)
7. Resume from checkpoint after interruption

## Gap Analysis

### Gaps Found

| ID | Gap | Severity | Workflow | Resolution |
|----|-----|----------|----------|-----------|
| G1 | `/self-improve` listed in workflow doc without noting it's hub-only (`.claude/skills/`) | LOW | learning-self-improvement | Add hub-only note to workflow doc |
| G2 | `/synthesize-hub` listed in workflow doc without noting it's hub-only | LOW | hub-sync | Add hub-only note to workflow doc |
| G3 | hub-sync has no orchestrator for automated sync cycle | MEDIUM | hub-sync | Design decision: create master agent or document as manual workflow |
| G4 | ops-quality has no orchestrator | LOW | ops-quality | Intentional — document as ad-hoc skill collection |
| G5 | stack-frameworks in `_needs-manual-review` | LOW | stack-frameworks | Assign to formal group or mark reference-only |
| G6 | code-review has interactive "Auto-fix?" prompt in standalone | INFO | code-review | Intentional safety check — not a gap |
| G7 | No automated test harness for workflow autonomy | HIGH | ALL | Implement 3-tier test plan below |

### Hub-Only Skills Clarification

Two skills exist in `.claude/skills/` (hub-only) but are referenced in workflow docs as if distributable:

| Skill | Location | Referenced By | Correct Placement |
|-------|----------|--------------|-------------------|
| `/self-improve` | `.claude/skills/self-improve/` | learning-self-improvement workflow doc | YES — hub operational skill |
| `/synthesize-hub` | `.claude/skills/synthesize-hub/` | hub-sync workflow doc | YES — hub operational skill |

These skills are NOT in `core/.claude/skills/` and will NOT be provisioned to downstream projects. This is correct by design per CLAUDE.md "Critical: Two `.claude/` Directories".

## Test Plan

### 3-Tier Test Architecture

#### Tier 1: Static Validation

**What:** Verify structural integrity without executing workflows.
**Where:** Extend `scripts/workflow_quality_gate_validate_patterns.py` or new test file.
**Can run:** Now, against this hub repo, in CI.

Tests:
- All `Skill()` / `Agent()` references in workflow docs resolve to existing files
- All workflow contracts have valid step DAGs (no cycles, no missing depends_on)
- All artifact paths referenced in contracts follow naming convention
- All master agents declare dual-mode operation (standalone + dispatched)
- Tool permissions in skills match actual tool usage (least-privilege)
- Hub-only skills (`.claude/skills/`) are not referenced as if distributable
- No dead cross-references between workflow groups

#### Tier 2: Contract Simulation

**What:** Validate orchestration logic with mock artifacts.
**Where:** New `scripts/tests/test_workflow_contracts.py`.
**Can run:** Now, against this hub repo.

Tests per workflow:
- Parse contract YAML, build dependency graph, verify topological sort
- Verify step ordering matches `depends_on` declarations
- Verify conditional steps (`skip_when`) are evaluated correctly
- Simulate gate evaluation with mock pass/fail artifact JSON
- Verify dispatched mode skips correct steps
- Verify state file schema (step statuses, timestamps, artifacts)
- Verify global retry budget enforcement (inject 16 failures, verify escalation)

#### Tier 3: Live Execution

**What:** End-to-end workflow execution against a real codebase.
**Where:** Integration tests using `scripts/tests/smoke-test/todo-api/`.
**Can run:** Manually or in dedicated CI job (resource-intensive).

Tests per workflow:
- Invoke slash command, verify completion without human intervention
- Verify artifact production at each pipeline step
- Inject failure at each gate, verify pipeline stops correctly
- Interrupt mid-pipeline, resume, verify checkpoint recovery
- Run in dispatched mode, verify contract return format

### Edge Cases

| Edge Case | Expected Behavior | Affected Workflows |
|-----------|-------------------|--------------------|
| Gate failure mid-pipeline | Stop, update state, return FAILED | ALL 8 orchestrated |
| Resume from checkpoint | Skip completed steps, continue from first failed | ALL 8 orchestrated |
| Dispatched mode | Skip commit/PR steps, return contract | ALL 8 orchestrated |
| Missing upstream artifact | Block with clear error | ALL 8 orchestrated |
| Global retry budget (15) exhausted | Escalate to user | ALL 8 orchestrated |
| Circular dependency in contract | Static validator catches before execution | Tier 1 |
| Concurrent step execution | e2e + auto_verify parallel | testing-pipeline |
| Conditional step skip | E2E skipped when no UI tests | testing-pipeline |
| Complexity-adaptive routing | Simple changes skip ideate+plan | development-loop |
| Fix-loop escalation to debugger | After 2x same error, dispatch debugger-agent | debugging-loop |
| Mandatory learning in dispatched mode | Learn step runs even when dispatched | debugging-loop |
| Interactive prompt in standalone | "Auto-fix?" pauses pipeline | code-review |

### Implementation Priority

1. **Tier 1** (static validation) — Implement first. Low cost, high value, runs in CI.
2. **Tier 2** (contract simulation) — Implement second. Catches logic bugs in orchestration.
3. **Tier 3** (live execution) — Implement last. Resource-intensive but provides highest confidence.

## Recommendations

1. **Fix G1 + G2:** Add hub-only notes to workflow docs (5 min each)
2. **Decide G3:** Should hub-sync be orchestrated? If yes, create master agent + contract. If no, document as manual.
3. **Fix G5:** Move stack-frameworks out of `_needs-manual-review`
4. **Implement Tier 1 tests** as part of `validate-pr.yml` CI
5. **Implement Tier 2 tests** as new pytest file
6. **Defer Tier 3** until Tier 1+2 are green

## Success Criteria

- All 8 orchestrated workflows pass Tier 1 + Tier 2 tests
- Zero missing references across all 11 workflow groups
- Workflow docs accurately distinguish hub-only vs distributable skills
- CI enforces structural integrity on every PR
