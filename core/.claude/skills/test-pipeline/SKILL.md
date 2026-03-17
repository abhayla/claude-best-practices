---
name: test-pipeline
description: >
  Run the full test verification pipeline: fix failures, verify changes,
  review visual proof, and commit. Thin wrapper that dispatches the
  test-pipeline-agent orchestrator. Use when you want the complete
  fix→verify→commit chain with enforced gates and artifact cleanup.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "[--capture-proof | --no-capture-proof] [--skip-fix] [failure_output]"
triggers:
  - test pipeline
  - run tests
  - verify and commit
  - full test
  - test verification
  - run full test
version: "1.0.0"
---

# Test Pipeline — Full Verification Chain

Run the complete test verification pipeline with enforced gates, artifact
cleanup, and optional screenshot-as-proof capture.

**Arguments:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--capture-proof` | true (from config) | Capture screenshots on every test (pass and fail) for visual review |
| `--no-capture-proof` | — | Disable screenshot capture even if config says true |
| `--skip-fix` | false | Skip the fix-loop stage (start at auto-verify) |
| `failure_output` | — | Test failure output to feed into fix-loop |

---

## STEP 1: Determine Mode

| Input | Mode | Pipeline Stages |
|-------|------|-----------------|
| `failure_output` provided | **Fix mode** | fix-loop → auto-verify → post-fix-pipeline |
| `--skip-fix` flag | **Verify mode** | auto-verify → post-fix-pipeline |
| No input | **Auto-detect** | Check for failing tests, then decide |

### Auto-detect logic

If no failure output and no `--skip-fix`:
1. Run the project's test command (from CLAUDE.md or detected config)
2. If tests fail → enter Fix mode with the failure output
3. If tests pass → enter Verify mode (skip fix-loop)

---

## STEP 2: Check Configuration

Read `test-evidence-config.json` if it exists in the project root:
- If `capture_proof: true` → enable capture-proof for the pipeline
- CLI `--capture-proof` flag overrides the config file

Read `config/test-pipeline.yml` for stage definitions (the agent reads this
internally, but verify it exists):

```bash
if [ ! -f config/test-pipeline.yml ]; then
  echo "WARN: config/test-pipeline.yml not found — using default pipeline stages"
fi
```

---

## STEP 3: Dispatch Orchestrator

Delegate the entire pipeline to `test-pipeline-agent`:

```
Agent("test-pipeline-agent", prompt="Run the full test verification pipeline.

Mode: $MODE
Capture proof: $CAPTURE_PROOF
Failure output: $FAILURE_OUTPUT

Execute the pipeline as defined in config/test-pipeline.yml:
1. Clean test-results/ and test-evidence/
2. Run each stage with --strict-gates
3. Enforce gate checks between stages (fail-closed)
4. Aggregate all results into pipeline-verdict.json
5. Report the final verdict with evidence location")
```

---

## STEP 4: Report Results

After the agent completes, present the pipeline verdict to the user:

```
Test Pipeline: PASSED | FAILED
  Stages: 3/3 completed
  Evidence: test-evidence/{run_id}/ (if capture-proof enabled)

  fix-loop:          PASSED | SKIPPED
  auto-verify:       PASSED | FAILED
  post-fix-pipeline: PASSED | BLOCKED
```

If FAILED, list the blocking failures and suggest next steps.

---

## CRITICAL RULES

- MUST NOT duplicate orchestration logic — delegate entirely to test-pipeline-agent
- MUST NOT run stages directly — the agent handles sequencing and gates
- MUST pass `--strict-gates` to the agent (enforced by the agent itself)
- MUST report the pipeline verdict, not individual stage results
- If the agent reports FAILED, do NOT attempt fixes at this level — the fix-loop
  stage already exhausted its retry budget
