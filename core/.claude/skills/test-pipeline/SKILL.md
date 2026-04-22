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
  - fix verify commit
  - verify and commit
  - full test pipeline
  - test verification pipeline
  - run test pipeline
version: "1.1.0"
---

# Test Pipeline — Full Verification Chain

Run the complete test verification pipeline with enforced gates, artifact
cleanup, and optional screenshot-as-proof capture.

**Critical:** This skill delegates entirely to test-pipeline-agent. Do not inline orchestration. For the broader TDD-through-quality-gates chain, use `/testing-pipeline-workflow` instead. For just verification without fix, use `/auto-verify`.

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

### Configuration Precedence (highest wins)

1. **CLI flags** — `--capture-proof` or `--no-capture-proof` (always wins)
2. **`test-evidence-config.json`** — Project-level config in project root
3. **`.claude/config/test-pipeline.yml`** — Pipeline-level config (capture_proof.enabled)
4. **Built-in default** — `true` (capture proof is on by default)

Read configs in order and apply the highest-precedence value found:

```bash
# Check for project-level config
if [ -f test-evidence-config.json ]; then
  CAPTURE_PROOF=$(python3 -c "import json; print(json.load(open('test-evidence-config.json')).get('capture_proof', True))")
elif [ -f .claude/config/test-pipeline.yml ]; then
  CAPTURE_PROOF=$(python3 -c "import yaml; print(yaml.safe_load(open('.claude/config/test-pipeline.yml')).get('capture_proof', {}).get('enabled', True))")
else
  CAPTURE_PROOF=true
fi
# CLI flags override everything
# --capture-proof → true, --no-capture-proof → false
```

Read `.claude/config/test-pipeline.yml` for stage definitions (the agent reads this
internally, but verify it exists):

```bash
if [ ! -f .claude/config/test-pipeline.yml ]; then
  echo "WARN: .claude/config/test-pipeline.yml not found — using default pipeline stages"
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

Execute the pipeline as defined in .claude/config/test-pipeline.yml:
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
