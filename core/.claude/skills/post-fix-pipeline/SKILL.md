---
name: post-fix-pipeline
description: >
  Post-fix verification pipeline: regression tests, full test suite with auto-fix,
  documentation updates (docs-manager agent), git commit (git-manager agent), evidence
  finalization. Use after fix-loop succeeds to verify no regressions before committing.
  Typically invoked by fix-issue or implement skills.
disable-model-invocation: true
allowed-tools: "Bash Read Grep Write Edit Task"
---

# Post-Fix Pipeline

Post-fix verification and commit process. Runs regression tests, test suite verification with auto-fix, documentation updates via docs-manager Agent, and git commit via git-manager Agent. Uses gate logic to block commits when test suites fail. Fully project-agnostic.

**Arguments:** $ARGUMENTS

Read and follow this process using the parameters passed by the caller (via `$ARGUMENTS` or inline in the calling Skill).

## Caller Context

This Skill is invoked by: `/adb-test`, `/run-e2e`, `/implement`, `/fix-issue`. Each provides different `test_suite_commands` and `commit_format`. Adapt behavior accordingly.

**Important:** If `test_suite_commands` is empty `[]` AND code files were changed (check `git diff --name-only` for `.kt`, `.py`, `.java`, `.xml` files), default to:
```
test_suite_commands: [
  { name: "backend", command: "cd backend && PYTHONPATH=. pytest --tb=short -q", timeout: 300 },
  { name: "android-unit", command: "cd android && ./gradlew test --console=plain", timeout: 600 }
]
```
If `test_suite_commands` is empty AND no code files changed, log: `Warning: No test suite commands and no code changes. Skipping test suite gate.`

---

## Input Parameters

### Core Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `fixes_applied` | Yes | List of fixes: `[{file, line, description}]` from the fix-loop process |
| `files_changed` | Yes | All file paths that were modified |
| `session_summary` | Yes | Human-readable summary of what was fixed and why |

### Regression Testing

| Parameter | Default | Description |
|-----------|---------|-------------|
| `regression_commands` | `[]` | Commands to run for regression testing: `[{name, command, timeout}]` |
| `regression_auto_fix` | `true` | If true (default), enter fix-loop for regressions. If false, log only |
| `regression_max_fix_attempts` | `3` | Maximum fix-loop iterations for regression failures |

### Test Suite Verification

| Parameter | Default | Description |
|-----------|---------|-------------|
| `test_suite_commands` | `[]` | Test suite commands as commit gate: `[{name, command, timeout}]` |
| `test_suite_max_fix_attempts` | `2` | Maximum auto-fix attempts when suites fail |
| `tester_agent_name` | `"tester"` | Agent name for test failure analysis (launched via Task tool) |

### Documentation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `docs_instructions` | `""` | Instructions for the docs-manager Agent. Empty string = skip documentation step |
| `docs_files_to_update` | `[]` | Specific documentation files to update |
| `docs_agent_name` | `"docs-manager"` | Agent name for documentation updates (launched via Task tool) |

### Git Commit

| Parameter | Default | Description |
|-----------|---------|-------------|
| `commit_format` | `"fix({scope}): {summary}"` | Commit message template |
| `commit_scope` | `"fix"` | Scope for the commit message |
| `push` | `false` | Whether to push after committing |
| `git_agent_name` | `"git-manager"` | Agent name for git operations (launched via Task tool) |

---

## Algorithm

```
STEP 0: INITIALIZE EVIDENCE
  Create evidence directory: .claude/logs/post-fix-pipeline/
  Write pipeline-init evidence:
    .claude/logs/post-fix-pipeline/evidence-init-{timestamp}.json
    { "event": "pipeline_start", "fixCount": N, "filesChanged": [...], "timestamp": "ISO8601" }

STEP 1: GATE CHECK
  If fixes_applied is empty:
    Return immediately with status: NO_FIXES
    Skip all remaining steps

STEP 2: REGRESSION TESTING (if regression_commands is non-empty)
  For each command in regression_commands:
    Run the command with its timeout
    Record: { name, status: PASSED|FAILED, output }

  Gate decision:
    ALL regressions pass -> proceed to Step 3
    Any regression fails:
      Enter fix-loop for the regression (max {regression_max_fix_attempts} iterations)
      After fix-loop -> re-run ALL regression commands
      If still failing after max attempts -> HARD BLOCK — skip Steps 3-5
      If all fixed -> proceed to Step 3

  Write regression evidence:
    .claude/logs/post-fix-pipeline/evidence-regression-{timestamp}.json
    { "event": "regression_complete", "gate": "PASSED|PASSED_AFTER_FIX|FAILED|NOT_RUN",
      "perCommand": [...], "fixAttempts": N, "timestamp": "ISO8601" }

STEP 3: TEST SUITE VERIFICATION (if test_suite_commands is non-empty)
  For each command in test_suite_commands:
    Run the command with its timeout
    Record: { name, passed_count, failed_count, failed_tests, output }

  Gate decision:
    ALL suites pass -> gate = PASSED -> proceed to Step 4
    Any suite fails:
      Launch tester Agent (read-only, via Task tool) with:
        - Failed test names and output
        - Diff of recent changes (files_changed)
        - Instruction: "Analyze these test failures against the recent fixes.
          Determine if the fixes caused the failures."

      The tester Agent returns analysis only.
      YOU (main Claude session) apply fixes based on that analysis (max {test_suite_max_fix_attempts} attempts).
      Re-run the test suite after each fix attempt.

      If all failures fixed:
        gate = PASSED_AFTER_FIX -> proceed to Step 4
      If still failing after max attempts:
        gate = FAILED -> HARD BLOCK — skip Steps 4 and 5

  Write test-suite evidence:
    .claude/logs/post-fix-pipeline/evidence-testsuite-{timestamp}.json
    { "event": "test_suite_complete", "gate": "PASSED|PASSED_AFTER_FIX|FAILED",
      "perSuite": [...], "autoFixAttempts": N, "timestamp": "ISO8601" }

STEP 4: DOCUMENTATION (only if regression gate != FAILED AND test suite gate != FAILED)
  If docs_instructions is non-empty:
    Launch docs_agent_name Agent (via Task tool) with:
      - fixes_applied list
      - files_changed list
      - session_summary
      - docs_instructions
      - docs_files_to_update
      - Instruction: "Update documentation based on the fixes applied.
        Return the list of documentation files updated."
    Record files updated by docs Agent

STEP 5: GIT COMMIT (only if regression gate != FAILED AND test suite gate != FAILED)
  Launch git_agent_name Agent (via Task tool) with:
    - files_changed (fix files + any doc files from Step 4)
    - commit_format with scope and summary filled in
    - push flag
    - Instruction: "Stage only the relevant files (not .env, build artifacts,
      or gitignored files). Create a commit using the provided format.
      Include the fix list in the commit body.
      Do NOT push unless push=true."
  Record commit hash and message

STEP 6: FINALIZE EVIDENCE
  Write pipeline-complete evidence:
    .claude/logs/post-fix-pipeline/evidence-complete-{timestamp}.json
    { "event": "pipeline_complete", "status": "COMPLETED|BLOCKED_BY_REGRESSION|BLOCKED_BY_TEST_SUITE|NO_FIXES",
      "regressionGate": "...", "testSuiteGate": "...", "commitHash": "...", "commitMessage": "...",
      "filesChanged": [...], "timestamp": "ISO8601" }
```

---

## Gate Logic

| Condition | Regression? | Docs? | Commit? |
|-----------|-------------|-------|---------|
| No fixes applied | NO | NO | NO |
| Regressions PASSED | YES (all pass) | YES | YES |
| Regressions PASSED_AFTER_FIX | YES (fixed) | YES | YES |
| Regressions FAILED (after max attempts) | YES (blocked) | **NO** | **NO** |
| Test suite PASSED | N/A | YES | YES |
| Test suite PASSED_AFTER_FIX | N/A | YES | YES |
| Test suite FAILED | N/A | **NO** | **NO** |
| No test_suite_commands | N/A | YES | YES |
| No regression_commands | N/A | YES | YES |

---

## Output

Return a structured report:

```markdown
## Post-Fix Pipeline Results

### Overall Status
- **Status:** COMPLETED | BLOCKED_BY_REGRESSION | BLOCKED_BY_TEST_SUITE | NO_FIXES

### Regression Testing
- **Commands run:** N
- **Passed:** N
- **Regressions found:** N
- **Details:**
  - {name}: PASSED | FAILED — {brief output}
(Omit section if no regression_commands provided)

### Test Suite Verification
- **Gate status:** PASSED | PASSED_AFTER_FIX | FAILED | NOT_RUN
- **Per-suite results:**
  - {name}: {passed_count} passed, {failed_count} failed
- **Auto-fix attempts:** N (if applicable)
- **Failed tests:** {list} (if gate = FAILED)
(Omit section if no test_suite_commands provided)

### Documentation Updates
- **Files updated:**
  - {file_path_1}
  - {file_path_2}
(Omit section if docs_instructions was empty)

### Git Commit
- **Hash:** {commit_hash}
- **Message:** {commit_message}
- **Pushed:** true | false
(Show "BLOCKED — test suite gate failed" if gate = FAILED)
(Show "SKIPPED — no fixes applied" if status = NO_FIXES)
```

---

## POST-RUN LEARNING CAPTURE

After producing the output report (regardless of pipeline status), automatically invoke:

```
Skill("reflect", args="session")
```

This captures the pipeline outcomes into structured learning logs and updates memory topic files. Runs for all statuses including NO_FIXES and BLOCKED.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Regression command times out | Treat as FAILED, enter fix-loop flow |
| Regression fix-loop exhausted | Gate = FAILED, block docs + commit |
| Test suite command times out | Treat as FAILED, enter auto-fix flow |
| Tester Agent fails to respond | Gate = FAILED, block commit |
| Docs Agent fails | Log warning, proceed to commit (non-blocking) |
| Git Agent fails | Log error, report COMMIT_FAILED |
| No test_suite_commands | Skip verification, proceed directly to docs + commit |
| No docs_instructions | Skip documentation, proceed to commit |
