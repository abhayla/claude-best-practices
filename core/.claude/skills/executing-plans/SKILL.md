---
name: executing-plans
description: >
  Execute a pre-written implementation plan step by step. Parses tasks from a plan
  file (output of /writing-plans), runs each task with verification, uses subagents
  for independent tasks, commits after each sub-task, and handles failures with
  fix loops. Use after /writing-plans has produced a plan.
triggers:
  - execute plan
  - run plan
  - follow plan
  - execute tasks
  - work through plan
allowed-tools: "Bash Read Write Edit Grep Glob Skill Agent"
argument-hint: "<plan-file-path or inline plan>"
version: "1.0.0"
type: workflow
---

# Executing Plans — Step-by-Step Plan Execution

Execute a pre-written implementation plan, task by task, with verification and progress tracking.

**Plan:** $ARGUMENTS

---

## STEP 1: Load and Validate the Plan

Accept the plan from one of:
- **File path** — Read the plan from a markdown file (e.g., `docs/plans/feature-plan.md`)
- **Inline text** — Parse plan content provided directly in the arguments

### 1.1 Parse Plan Structure

Extract from the plan:

| Element | Required | Source |
|---------|----------|--------|
| **Task list** | Yes | Checkboxes (`- [ ]`) or numbered items (`### Task N:`) |
| **Task titles** | Yes | Heading or first line of each task |
| **File paths** | Yes | `Files:` section within each task |
| **Verification commands** | Yes | `Verify:` or code blocks marked as bash within each task |
| **Dependencies** | Yes | `Depends on:` field or dependency graph section |
| **Code snippets** | No | `Code:` section within each task |
| **Time estimates** | No | `Time:` field within each task |

Supported plan formats:

```markdown
# Format A: Checkbox style (default /writing-plans output)
- [ ] **Task 1:** Create user model
  - Files: `src/models/user.py`
  - Verify: `pytest tests/test_user.py -v`
  - Time: ~3 min
  - Depends on: None

# Format B: Heading style
### Task 1: Create user model
**Files:**
- `src/models/user.py` (create)
**Verify:**
```bash
pytest tests/test_user.py -v
```
**Depends on:** None
```

### 1.2 Validate Plan Integrity

Before executing, verify:

1. **All tasks have verification commands** — Reject tasks without a verify step. Ask the user to add one before proceeding.
2. **File paths are valid** — For modifications, confirm the file exists. For creations, confirm the parent directory exists.
3. **Dependencies are acyclic** — Check that no circular dependencies exist between tasks.
4. **No tasks are already checked off** — Identify and skip tasks marked `- [x]` (already completed in a prior session).

If validation fails, report the issues and wait for user correction before proceeding.

### 1.3 Build Execution Order

From the dependency graph, compute:

1. **Execution waves** — Group tasks into waves where all tasks in a wave can run in parallel (no mutual dependencies, all predecessors completed).
2. **Critical path** — Identify the longest sequential chain to estimate minimum total time.
3. **Total task count** — Count remaining unchecked tasks.

Present the execution order for confirmation:

```
Execution Order:
  Wave 1: Task 1, Task 2 (parallel — no dependencies)
  Wave 2: Task 3 (depends on Task 1)
  Wave 3: Task 4, Task 5 (parallel — both depend on Task 3)
  Wave 4: Task 6 (depends on Task 4 and Task 5)

Critical path: Task 1 → Task 3 → Task 4 → Task 6
Estimated time: ~18 min
Tasks to execute: 6 of 6
```

Wait for user approval before executing.

---

## STEP 2: Pre-Execution Setup

Before starting task execution:

### 2.1 Git Checkpoint

```bash
git status
```

- If there are uncommitted changes, ask the user to commit or stash them first.
- Record the current commit hash as the rollback point:

```bash
git rev-parse HEAD
```

Save this as `$ROLLBACK_HASH` for use in failure recovery.

### 2.2 Initialize Progress Tracker

Create an in-memory progress tracker (do NOT write a separate tracking file):

```
Progress: 0 / {total_tasks} tasks
Status: STARTING
Current wave: 1
Elapsed: 0 min
```

### 2.3 Verify Build Environment

If the plan includes a project-level verification command (e.g., `npm install`, `pip install -r requirements.txt`, or a build command), run it first to ensure the environment is ready. If no setup command is specified, skip this step.

---

## STEP 3: Execute Tasks

Process tasks wave by wave. Within each wave, determine whether tasks can be parallelized.


**Read:** `references/execute-tasks.md` for detailed step 3: execute tasks reference material.

## STEP 4: Handle Failures

When a task's verification command fails, enter a structured fix loop.

### 4.1 Fix Loop (Max 3 Attempts)

For each attempt:

1. **Analyze the failure output** — Parse error messages, identify failing assertions, locate error line numbers
2. **Identify root cause** — Determine whether the issue is in:
   - The implementation just applied (most common)
   - A dependency from a previous task (check recent commits)
   - The verification command itself (wrong path, missing fixture)
   - The plan's instructions (incorrect or incomplete specification)
3. **Apply a targeted fix** — Make the minimum change to address the root cause
4. **Re-run verification** — Execute the same verify command

```
Fix attempt {attempt}/3 for Task {N}:
  Error: {error_summary}
  Root cause: {analysis}
  Fix: {description_of_fix}
  Result: {PASS|FAIL}
```

Each attempt MUST try a different approach. If the same fix is applied twice, it will fail twice.

### 4.2 Delegation to Fix Loop Skill

If the failure is complex (e.g., multiple cascading errors, unclear root cause), delegate to the `/fix-loop` skill:

```
Skill("fix-loop", args="failure_output: {error_output} retest_command: {verify_command} max_iterations: 3")
```

**Retry budget:** Each of the 3 fix attempts (Step 4.1) may delegate to `/fix-loop` with `max_iterations: 3`. This means the total maximum attempts per task is **9** (3 attempts × 3 fix-loop iterations each). The `/fix-loop` skill's default of 5 iterations is overridden to 3 when called from `/executing-plans` to keep the total bounded. If all 9 attempts fail, escalate per Step 4.3.

### 4.3 Escalation After 3 Failures

If a task fails all 3 fix attempts:

1. **Do NOT continue to the next task if it depends on this one** — dependent tasks will also fail
2. **Check if independent tasks remain** — if so, skip the failed task and continue with independent tasks
3. **Report the failure clearly:**

```
TASK FAILED: Task {N} — {task_title}
  Attempts: 3/3 exhausted
  Last error: {error_output}
  Files modified: {files} (changes preserved in working tree)

  Options:
  1. Fix manually and resume: /executing-plans --resume {plan_file} --from {N}
  2. Skip this task and continue with independent tasks
  3. Roll back this task: git revert HEAD
  4. Abort execution entirely
```

Wait for user input before proceeding.

### 4.4 Rollback a Failed Task

If the user chooses to roll back a failed task:

```bash
git diff HEAD -- {files_from_failed_task}
git checkout HEAD -- {files_from_failed_task}
```

This reverts only the files from the failed task without affecting successfully completed tasks.

---

## STEP 5: Resume Support

The skill supports resuming a partially completed plan.

### 5.1 Detect Prior Progress

When loading a plan, check for already-completed tasks:

1. **Checkbox markers** — Tasks marked `- [x]` in the plan file are already done
2. **Git history** — Search recent commits for `plan-exec:` messages matching task titles:

```bash
git log --oneline --grep="plan-exec:" -20
```

3. **File state** — Verify that files from "completed" tasks actually contain the expected changes

### 5.2 Resume from a Specific Task

If `--from {N}` is specified or detected from prior progress:

1. Skip tasks 1 through N-1 (already completed)
2. Verify the codebase is in a consistent state by running the verification commands of the last completed task
3. If the last completed task's verification fails, warn the user — the codebase may have changed since the plan was last executed
4. Begin execution from task N

### 5.3 Update Plan File on Disk

After each task completes successfully, update the plan file to mark the task as done:

- Change `- [ ]` to `- [x]` for the completed task
- This allows the `/continue` skill to detect progress if the session ends mid-plan

Only update the plan file if the plan was loaded from a file path (not inline text).

---

## STEP 6: Completion Summary

After all tasks are executed (or execution is halted), produce a structured summary.


**Read:** `references/completion-summary.md` for detailed step 6: completion summary reference material.

## STEP 7: Edge Cases and Special Handling

### 7.1 Plan Modifications Mid-Execution

If the user requests changes to the plan during execution:

1. Pause execution after the current task completes
2. Accept the modification (add task, remove task, reorder, change verification)
3. Recalculate the dependency graph and execution order
4. Present the updated execution order for approval
5. Resume execution

Do NOT apply modifications to tasks that are already completed — those changes would require reverting and re-executing.

### 7.2 Large Plans (More Than 15 Tasks)

For plans with more than 15 tasks:

1. Present execution in phases — group tasks into logical milestones (e.g., "Data Layer," "API Layer," "Tests")
2. Pause between phases for user review
3. Run a broader test suite at each phase boundary, not just task-level verification

### 7.3 Tasks That Require User Input

Some tasks may require manual steps (e.g., "Configure environment variables," "Set up external service credentials"). When detected:

1. Announce the manual task clearly
2. Provide exact instructions from the plan
3. Wait for the user to confirm completion
4. Run the verification command to validate
5. If verification fails, ask the user to retry the manual step

### 7.4 Conflicting File Changes

If two tasks in the same wave modify the same file (detected during parallelization safety checks):

1. Force sequential execution for those specific tasks
2. Apply the first task's changes, verify, then apply the second task's changes
3. After both pass, commit together

### 7.5 Verification Command Produces Warnings

If the verification command exits with code 0 but produces warnings:

1. Report the warnings to the user
2. Ask whether to treat warnings as failures or continue
3. If continuing, log the warnings in the commit message

---

## MUST DO

- Always load and validate the plan before executing any task (Step 1)
- Always wait for user approval of the execution order before starting
- Always run the verification command for every task — no exceptions
- Always commit after each successfully verified task (or wave of tasks)
- Always record the rollback hash before starting execution
- Always update the plan file checkboxes after each completed task (when loaded from file)
- Always try a different approach on each fix attempt — never repeat the same fix
- Always report progress after each task completes
- Always check git status before starting — refuse to start with uncommitted changes
- Always present the completion summary at the end, regardless of success or failure

## MUST NOT DO

- MUST NOT skip verification for any task — every task must be verified before marking complete
- MUST NOT continue to dependent tasks when a predecessor fails — skip them and report clearly
- MUST NOT use `git add -A` or `git add .` — always add specific files by path
- MUST NOT modify the plan's task descriptions during execution — execute what was planned
- MUST NOT exceed 3 fix attempts per task — escalate to the user after 3 failures
- MUST NOT parallelize tasks that share files — always run those sequentially
- MUST NOT run the entire plan without user approval of the execution order first
- MUST NOT create additional tracking files — use the plan file itself and git history for state
- MUST NOT silently skip failed tasks — always report failures and wait for user direction
- MUST NOT start execution if the plan has tasks without verification commands — require them first
