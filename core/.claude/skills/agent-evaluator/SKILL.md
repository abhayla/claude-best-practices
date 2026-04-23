---
name: agent-evaluator
description: >
  Evaluate Claude Code AGENTS (not skills) against scenario files using LLM-as-judge
  with a 5-criterion rubric. Use when validating a new or modified agent before merge,
  enforcing pre-merge eval gates (REQ-M033 of test-pipeline-three-lane spec), or
  auditing existing agents for dispatch behavior + return contract correctness.
  Discovers `core/.claude/agents/<agent>/evals/scenarios/*.json`, runs each scenario,
  scores against rubric (trigger reliability, output structure, NON-NEGOTIABLE adherence,
  side-effect correctness, error propagation), and reports per-scenario + aggregate
  pass/fail (avg ≥4 of 5 threshold per scenario). Distinct from `/skill-evaluator`
  which evaluates skills with a different rubric (trigger activation rates,
  description optimization, cross-skill conflicts).
triggers:
  - agent-evaluator
  - evaluate agent
  - test agent
  - audit agent
  - agent evaluation
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<agent-path>"
type: workflow
version: "1.0.0"
---

# Agent Evaluator — Evaluate Agent Quality

Structured evaluation of agent dispatch behavior, return contract correctness,
and NON-NEGOTIABLE adherence. Produces per-scenario scores plus aggregate
pass/fail. Built specifically for the three-lane test pipeline's PR1 evals
gate (REQ-M033) but reusable for any agent with `evals/scenarios/*.json`.

**Request:** $ARGUMENTS

> Spec reference: `docs/specs/test-pipeline-three-lane-spec.md` v1.6 §4 EVALS

---

## STEP 0: Pre-Flight Checks

Run before evaluation. Each check pass/fail with specific evidence.

### 0.1 Agent file exists

Resolve `<agent-path>` from `$ARGUMENTS`. Accept either a name (`failure-triage-agent`) or a relative path (`core/.claude/agents/failure-triage-agent.md`). Verify the file exists. If missing → BLOCK with message: `"Agent not found at <resolved-path>. Run from repo root and pass agent name or path."`

### 0.2 Scenarios directory exists

Locate `core/.claude/agents/<agent-name>/evals/scenarios/`. If missing or empty → BLOCK with message: `"No eval scenarios found at <path>. Per spec §4 EVALS, agents need ≥5 scenarios in evals/scenarios/*.json. Author scenarios first."`

### 0.3 Scenario count check

Count `*.json` files in scenarios directory. If count < 5 → WARN (allow proceed but flag in report): `"Only N scenarios found; spec §4 recommends ≥5 for statistical confidence."`

### 0.4 Agent has NON-NEGOTIABLE block

Grep `## NON-NEGOTIABLE` in the agent body. If absent → WARN: `"Agent body has no NON-NEGOTIABLE block. Rubric criterion #3 (NON-NEGOTIABLE adherence) cannot be scored without one. Add per fugazi pattern (see core/.claude/rules/pattern-structure.md)."`

---

## STEP 1: Load Scenarios

For each `*.json` file in `core/.claude/agents/<agent-name>/evals/scenarios/`:

1. Parse JSON; verify required fields present:
   - `scenario_name` (string)
   - `description` (string)
   - `input.dispatch_context` (object)
   - `expected_contract` (object)
   - `rubric_hints` (object with 5 keys: `trigger_reliability`, `output_structure`, `non_negotiable_adherence`, `side_effect_correctness`, `error_propagation`)

2. If a scenario is missing required fields → SKIP that scenario, log: `"Scenario {scenario_name} skipped — missing fields: {list}. See spec §4 EVALS for schema."`

3. Optional fields: `input.filesystem_setup`, `input.env_setup` (used to set up state before dispatch).

---

## STEP 2: Run Each Scenario

For each loaded scenario:

### 2.1 Set up environment

If `input.filesystem_setup` is present, create the specified files/directories. If `input.env_setup` is present, set the env vars for the dispatch context.

### 2.2 Dispatch the agent

Construct the dispatch prompt by serializing `input.dispatch_context` as the agent's input. Invoke via the standard `Agent()` mechanism (or simulate via dry-run if running in non-interactive validation mode).

### 2.3 Capture the return contract

Record the agent's actual return value verbatim. Strip any conversational prose; extract the structured JSON contract.

### 2.4 Compare against expected_contract

Field-by-field comparison:
- For exact-match fields: actual must equal expected
- For pattern fields (e.g., `"timestamp": "ISO8601"`): actual must match the pattern
- For wildcard fields (`"*"`): any value accepted
- For absence checks (`"<absent>"`): actual must NOT contain the field

Record: PASS / PARTIAL / FAIL per field; combine into a single `output_structure` score (1-5).

---

## STEP 3: LLM-as-Judge Scoring

For each scenario, score 5 criteria (1-5 scale):

| Criterion | Definition | Scoring Anchor |
|---|---|---|
| `trigger_reliability` | Did the agent fire when its conditions were met? | 5 = correct mode/lane detected from dispatch context; 1 = silently skipped or wrong mode |
| `output_structure` | Did the return contract match the documented JSON schema? | 5 = all expected fields present with correct types; 1 = unstructured prose returned |
| `non_negotiable_adherence` | Were the agent's NON-NEGOTIABLE rules respected? | 5 = all NN rules visibly honored in dispatched behavior; 1 = NN rule violated (e.g., wrote to file when NN says no writes) |
| `side_effect_correctness` | Did file writes, gh calls, git operations match expected? | 5 = side effects match expected_contract.side_effects exactly; 1 = unexpected files modified or expected files NOT modified |
| `error_propagation` | Were failures returned as structured contracts vs swallowed? | 5 = errors include `result: "BLOCKED"` + structured remediation; 1 = errors swallowed or returned as freeform string |

Use `rubric_hints[criterion]` from the scenario as additional context for scoring (it captures what the scenario author considered important per criterion).

### 3.1 Per-scenario aggregate

Compute `avg_score = mean(5 criteria)`. PASS threshold: `avg_score >= 4.0`.

---

## STEP 4: Aggregate Across Scenarios

Compute:
- `total_scenarios_run`: integer
- `scenarios_passed`: count where avg_score >= 4.0
- `scenarios_failed`: count where avg_score < 4.0
- `aggregate_avg_score`: mean of all per-scenario avg_scores
- `pass_rate`: scenarios_passed / total_scenarios_run

**Aggregate verdict:** PASS if `pass_rate >= 0.8` AND `aggregate_avg_score >= 4.0`. Otherwise FAIL.

---

## STEP 5: Generate Report

Write Markdown report to stdout AND to `evals/reports/{agent-name}-{ISO-8601-timestamp}.md`:

```markdown
# Agent Eval Report: {agent-name}

**Date:** {timestamp}
**Scenarios run:** {total_scenarios_run}
**Aggregate verdict:** PASS | FAIL
**Pass rate:** {pass_rate}% ({scenarios_passed}/{total_scenarios_run})
**Aggregate avg score:** {aggregate_avg_score}/5.0

## Per-Scenario Results

| Scenario | Avg Score | Verdict | Notes |
|---|---|---|---|
| no-op-skeleton | 4.6 | PASS | All NN rules respected |
| empty-failure-set | 4.2 | PASS | Output contract matched exactly |
| {...} | | | |

## Failed Scenarios (Detail)

### {scenario_name}
- avg_score: {score}
- Failed criteria: {list with scores < 4}
- Evidence: {dispatch + actual return + expected diff}
- Recommended fix: {actionable suggestion}

## Aggregate

{summary paragraph}
```

---

## STEP 6: Pre-Merge Gate

If invoked from CI (env var `CI=true` or `--ci` flag passed):

- Aggregate verdict PASS → exit 0
- Aggregate verdict FAIL → exit 1, print failed scenario summary to stderr

If invoked interactively, just print the report; do not exit non-zero (let the user decide).

---

## STEP 7: Record Eval Run

Append a one-line summary to `evals/eval-history.jsonl`:

```jsonl
{"timestamp": "...", "agent": "...", "scenarios_run": N, "aggregate_verdict": "PASS|FAIL", "aggregate_avg_score": X.X}
```

This enables historical eval-quality tracking per spec §4 EVALS.

---

## CRITICAL RULES

- MUST NOT score an agent that has no `evals/scenarios/*.json` directory — BLOCK with actionable error
- MUST NOT score scenarios that lack required fields — SKIP them and log
- MUST NOT confuse skill eval with agent eval — `/skill-evaluator` is a different tool with a different rubric; this skill is for agents only
- MUST NOT silently treat warnings as passes — every WARN appears in the report
- MUST NOT modify any agent file during evaluation — read-only operation (no `Write`/`Edit` in `allowed-tools`)
- MUST emit aggregate exit code per CI flag for pre-merge gating
