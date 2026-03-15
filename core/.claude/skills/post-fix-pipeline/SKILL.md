---
name: post-fix-pipeline
description: >
  Post-fix verification pipeline: regression tests, full test suite with auto-fix,
  documentation updates, and git commit. Use after fix-loop succeeds to verify
  no regressions before committing.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[fixes_applied] [test_suite_commands] [commit_format]"
version: "1.1.0"
type: workflow
---

# Post-Fix Pipeline

Verify fixes don't cause regressions, update docs, and commit.

**Input:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fixes_applied` | — | Summary of fixes that were applied |
| `test_suite_commands` | — | Commands to run for full test suite verification |
| `commit_format` | `fix(scope): description` | Commit message format |
| `push` | false | Whether to push after commit |

---

## STEP 0: Gate Check — Read Upstream Results

Before running the pipeline, check if the upstream `auto-verify` stage passed:

1. If `test-results/auto-verify.json` exists, read it
2. Parse the `result` field
3. If `result` is `FAILED`:
   - Report: "BLOCKED: auto-verify reported FAILED — resolve upstream failures before running post-fix-pipeline."
   - Exit immediately — do not proceed to regression testing
4. If `result` is `PASSED`, `FIXED`, or the file does not exist → proceed to STEP 1

```bash
if [ -f test-results/auto-verify.json ]; then
  UPSTREAM_RESULT=$(python3 -c "import json; print(json.load(open('test-results/auto-verify.json'))['result'])")
  if [ "$UPSTREAM_RESULT" = "FAILED" ]; then
    echo "BLOCKED: auto-verify reported FAILED"
    exit 1
  fi
  echo "auto-verify result: $UPSTREAM_RESULT — proceeding"
else
  echo "No auto-verify results found — proceeding without gate check"
fi
```

---

## STEP 1: Regression Testing

Run targeted tests on the areas where fixes were applied:

1. Identify test files related to changed files
2. Run targeted tests first
3. Report any regressions introduced by the fix

## STEP 2: Full Test Suite Verification

If test suite commands are provided, run them:

1. Execute each test suite command
2. If failures found:
   - Attempt auto-fix (max 2 attempts via `/fix-loop`)
   - If still failing, report and block commit
3. Gate: PASSED / PASSED_AFTER_FIX / FAILED

## STEP 3: Documentation Updates

Delegate to docs-manager agent if documentation needs updating:
- Update continuation/handoff documents
- Record test results

## STEP 4: Git Commit

If all gates pass:

1. Delegate to git-manager agent for secure commit
2. Use conventional commit format
3. Include summary of fixes in commit body

If gates fail:
- Report blocking issues
- Do NOT commit

## STEP 5: Learning Capture

Invoke `/learn-n-improve session` to record the fix for future reference.

## STEP 5.5: Structured JSON Output

Write machine-readable results to `test-results/post-fix-pipeline.json`:

```json
{
  "skill": "post-fix-pipeline",
  "result": "PASSED|FAILED",
  "timestamp": "<ISO-8601>",
  "details": {
    "regression_tests": "PASSED|FAILED",
    "test_suite": "PASSED|PASSED_AFTER_FIX|FAILED",
    "documentation": "UPDATED|SKIPPED",
    "commit": "<hash>|BLOCKED",
    "learning_capture": "RECORDED|SKIPPED",
    "upstream_gate": "PASSED|SKIPPED"
  }
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by downstream stage gates.

```bash
mkdir -p test-results
python3 -c "
import json, datetime
result = {
    'skill': 'post-fix-pipeline',
    'result': '<PASSED_or_FAILED>',
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'details': {
        'regression_tests': '<status>',
        'test_suite': '<status>',
        'documentation': '<status>',
        'commit': '<hash_or_BLOCKED>',
        'learning_capture': '<status>',
        'upstream_gate': '<status>'
    }
}
with open('test-results/post-fix-pipeline.json', 'w') as f:
    json.dump(result, f, indent=2)
"
```

---

## Report

```
Post-Fix Pipeline:
  Regression tests: PASSED/FAILED
  Test suite: PASSED/PASSED_AFTER_FIX/FAILED
  Documentation: UPDATED/SKIPPED
  Commit: [hash] — [message] / BLOCKED
```
