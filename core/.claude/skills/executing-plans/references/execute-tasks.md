# STEP 3: Execute Tasks

### 3.1 Sequential Execution (Default)

For each task in dependency order:

#### A. Announce the Task

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Task {N}/{total}] {task_title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files: {file_list}
Depends on: {dependencies}
Verify: {verify_command}
```

#### B. Implement the Task

1. Read the task description and code snippets from the plan
2. Read existing files that will be modified to understand current state
3. Apply the changes described in the task:
   - For file modifications — use Edit to make targeted changes
   - For file creations — use Write to create new files
   - For deletions — use Bash to remove files
4. Follow existing code patterns and conventions found in the project

If the task description is ambiguous or incomplete:
- Check the plan for additional context in surrounding tasks
- Look at the code snippets provided in the plan
- If still unclear, ask the user for clarification before proceeding

#### C. Run Verification

Execute the verification command specified in the plan:

```bash
{verify_command}
```

Evaluate the result:

| Outcome | Action |
|---------|--------|
| **Pass** | Mark task complete, proceed to commit |
| **Fail** | Enter fix loop (Step 4) |
| **Command not found** | Check if a dependency needs installing, fix and retry |
| **Timeout** | Report timeout, ask user whether to retry or skip |

#### D. Commit Checkpoint

After a task passes verification, commit the changes:

```bash
git add {files_changed}
git commit -m "plan-exec: {task_title}

Task {N}/{total} from {plan_name}
Verify: {verify_command} — PASSED"
```

Use specific file paths in `git add` — do NOT use `git add -A` or `git add .`.

#### E. Update Progress

```
Progress: {completed} / {total} tasks
  [x] Task 1: Create user model — PASSED
  [x] Task 2: Add validation — PASSED
  [ ] Task 3: Write API endpoint — IN PROGRESS
  [ ] Task 4: Integration tests — PENDING
```

### 3.2 Parallel Execution (When Safe)

When multiple tasks in the same wave have no dependencies on each other AND modify different files, delegate them to subagents for parallel execution.

**Safety checks before parallelizing:**
1. Tasks modify **completely different files** — no overlapping file paths
2. Tasks have **no implicit dependencies** — e.g., one task creates a type that another imports
3. Tasks have **independent verification commands** — running one verify does not affect another

If all checks pass, delegate each task to a subagent:

```
Agent("Execute plan task {N}: {task_title}

Files to modify: {file_list}
Changes: {task_description}
Code: {code_snippet}

After making changes, run this verification command:
{verify_command}

If verification fails, fix the issue (max 3 attempts). Report back with:
- Status: PASSED or FAILED
- Files changed: [list]
- Verification output: [output]")
```

After all subagents in the wave complete:
1. Collect results from each subagent
2. If any task failed, pause and report before continuing
3. If all passed, commit all changes from the wave in a single commit:

```bash
git add {all_files_from_wave}
git commit -m "plan-exec: Wave {W} — {task_titles_comma_separated}

Tasks {N1}, {N2}, {N3} of {total} from {plan_name}
All verifications PASSED"
```

4. Update the progress tracker

**When NOT to parallelize:**
- Tasks touch the same files or directories
- Tasks involve database migrations or schema changes
- Tasks modify shared configuration files
- Any doubt about independence — default to sequential

---

