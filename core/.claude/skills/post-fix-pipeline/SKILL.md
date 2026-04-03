---
name: post-fix-pipeline
description: >
  Finalize verified changes by reading the upstream auto-verify gate, updating
  documentation, committing, and capturing learnings. Use after auto-verify
  succeeds to complete the post-fix workflow. Does NOT re-run tests — use
  /auto-verify for that. For the full fix→verify→commit chain, use /test-pipeline.
type: workflow
triggers:
  - finalize fix
  - commit after verify
  - post fix pipeline
  - commit verified changes
  - finalize and commit
  - post-fix commit
allowed-tools: "Bash Read Grep Glob Write Agent Skill"
argument-hint: "[fixes_applied] [commit_format] [--strict-gates] [--capture-proof | --no-capture-proof]"
version: "3.1.0"
---

# Post-Fix Pipeline

Finalize verified changes: documentation, commit, and learning capture.

**Critical:** This skill does NOT re-run tests. It reads upstream gate results from `test-results/auto-verify.json`. If the gate fails or is missing (with `--strict-gates`), it BLOCKS the commit. Always invoke `/auto-verify` before this skill.

**Input:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fixes_applied` | — | Summary of fixes that were applied |
| `commit_format` | `fix(scope): description` | Commit message format |
| `push` | false | Whether to push after commit |
| `--strict-gates` | false | Missing upstream JSON = BLOCK |
| `--capture-proof` | true (from config) | Include evidence summary in commit body |
| `--no-capture-proof` | — | Disable screenshot capture even if config says true |

---

## STEP 0: Gate Check — Read Upstream Results

1. If `test-results/auto-verify.json` exists, read it:
   - If `result` is `FAILED` → BLOCK. Exit immediately.
   - If `result` is `PASSED` or `FIXED` → proceed.

2. If `test-results/auto-verify.json` does NOT exist:
   - **With `--strict-gates`:** BLOCK. Report: "BLOCKED: auto-verify output missing."
   - **Without `--strict-gates`:** WARN + proceed.

3. If `test-evidence/*/visual-review.json` exists (most recent run_id), read it:
   - If any `overrides` exist (passed tests overridden to FAILED) → BLOCK.
   - Report which tests were visually overridden.

4. **Screenshot verdict gate (defense-in-depth):** Read `test-results/auto-verify.json`
   failures array. If ANY failure has `verdict_source: "screenshot"`, BLOCK commit.
   This is redundant with auto-verify's own verdict (screenshot FAILED already
   means auto-verify FAILED), but serves as an independent safety check — two
   gates must agree before code is committed.

```bash
if [ -f test-results/auto-verify.json ]; then
  UPSTREAM_RESULT=$(python3 -c "import json; print(json.load(open('test-results/auto-verify.json'))['result'])")
  if [ "$UPSTREAM_RESULT" = "FAILED" ]; then
    echo "BLOCKED: auto-verify reported FAILED"
    exit 1
  fi
  # Defense-in-depth: check for screenshot-verdict failures even if result is PASSED
  SCREENSHOT_FAILURES=$(python3 -c "
import json
d = json.load(open('test-results/auto-verify.json'))
failures = [f for f in d.get('failures', []) if f.get('verdict_source') == 'screenshot']
print(len(failures))
")
  if [ "$SCREENSHOT_FAILURES" -gt 0 ]; then
    echo "BLOCKED: $SCREENSHOT_FAILURES UI test(s) failed screenshot verification"
    exit 1
  fi
  echo "auto-verify result: $UPSTREAM_RESULT — proceeding"
else
  if [ "$STRICT_GATES" = "true" ]; then
    echo "BLOCKED: auto-verify output missing (--strict-gates enforced)"
    exit 1
  else
    echo "WARN: No auto-verify results found — proceeding without gate check"
  fi
fi

# Check visual review overrides
VISUAL_REVIEW=$(find test-evidence -name "visual-review.json" 2>/dev/null | sort | tail -1)
if [ -n "$VISUAL_REVIEW" ]; then
  OVERRIDES=$(python3 -c "import json; d=json.load(open('$VISUAL_REVIEW')); print(len(d.get('overrides', [])))")
  if [ "$OVERRIDES" -gt 0 ]; then
    echo "BLOCKED: visual review found $OVERRIDES override(s) — passed tests visually broken"
    exit 1
  fi
fi
```

---

## STEP 1: Documentation Updates

Delegate to docs-manager-agent if documentation needs updating:
- Update continuation/handoff documents
- Record test results and evidence location

## STEP 2: Git Commit

If all gates pass:

1. Delegate to git-manager-agent for secure commit
2. Use conventional commit format
3. Include summary of fixes in commit body
4. If `--capture-proof`, include evidence directory path in commit body

If gates fail:
- Report blocking issues
- Do NOT commit

## STEP 3: Learning Capture

Invoke `/learn-n-improve session` to record the fix for future reference.

## STEP 4: Structured JSON Output

Write machine-readable results to `test-results/post-fix-pipeline.json`:

```json
{
  "skill": "post-fix-pipeline",
  "result": "PASSED|FAILED",
  "timestamp": "<ISO-8601>",
  "details": {
    "documentation": "UPDATED|SKIPPED",
    "commit": "<hash>|BLOCKED",
    "learning_capture": "RECORDED|SKIPPED",
    "upstream_gate": "PASSED|SKIPPED",
    "visual_review_gate": "PASSED|BLOCKED|SKIPPED"
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
        'documentation': '<status>',
        'commit': '<hash_or_BLOCKED>',
        'learning_capture': '<status>',
        'upstream_gate': '<status>',
        'visual_review_gate': '<status>'
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
  Upstream gate: PASSED/BLOCKED
  Visual review gate: PASSED/BLOCKED/SKIPPED
  Documentation: UPDATED/SKIPPED
  Commit: [hash] — [message] / BLOCKED
```

---

## CRITICAL RULES

- MUST read upstream gate results before any commit — never commit without verification evidence
- MUST NOT re-run tests — this skill finalizes, it does not verify
- MUST NOT commit when `auto-verify.json` reports FAILED or has screenshot-verdict failures
- MUST NOT skip learning capture (Step 3) — every fix must be recorded via `/learn-n-improve`
- MUST write structured JSON output to `test-results/post-fix-pipeline.json` for downstream consumption
- MUST block commit if visual review has any overrides (passed tests visually broken)
