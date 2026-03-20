---
name: subagent-driven-dev
description: >
  Orchestrate task execution across multiple subagents for parallel development.
  Provides a decision framework for when to delegate vs. work directly, patterns for
  task decomposition, subagent prompt design, result aggregation, failure handling,
  and file conflict avoidance. Use when a task has independent subtasks that benefit
  from parallel execution.
triggers:
  - subagent
  - delegate tasks
  - parallel agents
  - fan out work
  - distribute work
  - multi-agent
  - orchestrate agents
allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill"
argument-hint: "<task description or plan with parallelizable subtasks>"
version: "1.1.0"
type: workflow
---

# Subagent-Driven Development — Parallel Task Orchestration

Orchestrate work across multiple subagents for faster, parallelized development.

**Task:** $ARGUMENTS

---

## STEP 1: Decide Whether to Use Subagents

Not every task benefits from subagent delegation. Evaluate the task against this decision framework before proceeding.


**Read:** `references/decide-whether-to-use-subagents.md` for detailed step 1: decide whether to use subagents reference material.

## STEP 2: Decompose the Task

Break the work into subtasks suitable for subagent delegation.


**Read:** `references/decompose-the-task.md` for detailed step 2: decompose the task reference material.

# Commit pre-work before dispatching subagents
git add src/api/validators.py
git commit -m "feat: add validator base class for endpoint validation

Pre-work for parallel validation implementation across endpoints"
```

### 2.4 Define Subtask Boundaries

For each subtask, define explicit boundaries:

```
Subtask A: User Validation
  OWNS (may modify):
    - src/api/users.py
    - tests/test_users.py
  READS (must not modify):
    - src/api/validators.py
    - src/models/user.py
  CREATES (new files only):
    - src/api/validators/user_validator.py (if needed)
  MUST NOT TOUCH:
    - Any file not listed above
```

These boundaries are critical — they go into the subagent prompt to prevent file conflicts.

---

## STEP 3: Write Subagent Prompts

Effective subagent prompts are self-contained, explicit, and bounded. A subagent has no access to the main conversation's context — everything it needs must be in the prompt.

### 3.1 Prompt Template

Every subagent prompt MUST include these sections:

```
Agent("
## Objective
<One sentence: what this subagent must accomplish>

## Context
<Background the subagent needs to understand the task. Include:
 - Why this change is being made
 - What pattern or convention to follow
 - Reference files to read for examples>

## Scope — Files You Own
<Exhaustive list of files this subagent may modify or create>
- `path/to/file.ext` (modify — add validation logic)
- `path/to/test_file.ext` (modify — add validation tests)

## Scope — Files You May Read (Do NOT Modify)
<Files the subagent should read for context but MUST NOT edit>
- `path/to/base_class.ext` (read for interface definition)
- `path/to/example.ext` (read for pattern reference)

## Detailed Instructions
<Step-by-step instructions for the implementation>
1. Read `path/to/example.ext` to understand the validation pattern
2. In `path/to/file.ext`, add validation for fields X, Y, Z
3. Write tests in `path/to/test_file.ext` covering:
   - Valid input passes
   - Missing required field raises error
   - Invalid format raises error

## Verification
<Command(s) to run after implementation>
Run: `pytest tests/test_file.py -v`
Expected: All tests pass, no failures

## Completion Report
When done, report:
- Status: PASSED or FAILED
- Files modified: [list with brief description of changes]
- Files created: [list]
- Test results: [pass/fail counts]
- Issues encountered: [any problems or decisions made]
")
```

### 3.2 Prompt Quality Checklist

Before dispatching, verify each prompt against:

- [ ] **Self-contained** — A developer with no prior context could execute this prompt
- [ ] **File boundaries explicit** — Every file the subagent may touch is listed; files it must not touch are called out
- [ ] **Verification included** — A concrete command that proves the work is correct
- [ ] **Pattern reference provided** — Points to an existing file as an example of the desired pattern
- [ ] **No forward references** — Does not say "after the other agent finishes" or "once X is ready"
- [ ] **Output format specified** — The completion report format is defined so results can be aggregated

### 3.3 Context Passing Guidelines

| Include in Prompt | Keep in Main Context |
|-------------------|---------------------|
| Task-specific requirements | Overall project plan |
| File paths and boundaries | Progress tracking across all subtasks |
| Pattern examples (file paths to read) | Dependency graph |
| Verification commands | Aggregated results |
| Relevant error context (if retry) | Decision log and rationale |
| Coding conventions for the area | User preferences and session history |

**Key principle:** Pass the minimum context needed. Subagents that receive too much irrelevant context perform worse — they get distracted by information unrelated to their focused task.

### 3.4 Anti-Patterns in Subagent Prompts

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| "Do your best" | No success criteria | Define exact verification command |
| "Fix the code" | No scope | List specific files and the specific issue |
| "Follow the existing pattern" (without pointing to a file) | Subagent may guess wrong | Add: "Read `src/services/OrderService.ts` and follow that pattern" |
| "Coordinate with other agents" | Subagents cannot communicate | Remove — handle coordination in main context |
| Dumping entire file contents into the prompt | Wastes tokens, buries the task | Pass file paths — let the subagent read files itself |
| "Also clean up anything else you notice" | Unbounded scope leads to conflicts | Remove — keep scope locked to the defined files |

---

## STEP 4: Dispatch Strategy

Choose the right dispatch pattern based on task structure.


**Read:** `references/dispatch-strategy.md` for detailed step 4: dispatch strategy reference material.

## STEP 5: Monitor Progress and Aggregate Results

### 5.1 Track Subagent Status

Maintain an in-memory tracker in the main context:

```
Subagent Status:
  [DONE]    Agent A: User validation — PASSED (3 tests added)
  [RUNNING] Agent B: Order validation — dispatched 2 min ago
  [DONE]    Agent C: Product validation — FAILED (import error)
  [PENDING] Agent D: Integration tests — blocked on B and C
```

Update this tracker as each subagent reports back.

### 5.2 Process Subagent Results

When a subagent completes, extract from its report:

1. **Status** — PASSED or FAILED
2. **Files changed** — Verify these match the expected file boundaries
3. **Test results** — Pass/fail counts and any unexpected output
4. **Issues or decisions** — Anything the subagent flagged that needs main-context review

### 5.3 Validate No File Conflicts

After all subagents in a wave complete, verify that no two subagents modified the same file:

```bash
# Check git status for all modified files
git status --porcelain
```

If two subagents modified the same file (a boundary violation):

1. **Identify the conflict** — Determine which changes overlap
2. **Keep the more correct version** — Usually the subagent whose task was more directly related to the file
3. **Manually merge** — Apply the other subagent's changes on top, resolving conflicts
4. **Add a rule** — Update file boundaries to prevent this in future dispatches

### 5.4 Run Integration Verification

After aggregating all subagent results from a wave:

```bash
# Run the full test suite, not just individual subtask tests
pytest tests/ -v

# Or the project-specific full verification
npm test
./gradlew test
```

Individual subtask verification passing does NOT guarantee integration correctness. Always run the full suite after merging subagent work.

### 5.5 Commit Aggregated Work

After all subagents in a wave pass and integration tests pass:

```bash
git add src/api/users.py src/api/orders.py src/api/products.py
git add tests/test_users.py tests/test_orders.py tests/test_products.py
git commit -m "feat: add input validation to all API endpoints

Implemented via parallel subagents:
- User endpoint validation (3 tests)
- Order endpoint validation (4 tests)
- Product endpoint validation (3 tests)

All subtask and integration tests passing."
```

Use specific file paths — do NOT use `git add -A` or `git add .`.

---

## STEP 6: Handle Failures

Subagent failures require different handling than single-context failures because the failed work exists alongside potentially successful parallel work.

### 6.1 Single Subagent Failure

When one subagent fails but others succeed:

1. **Collect the failure details** — Error output, files modified, what was attempted
2. **Check for contamination** — Did the failure affect shared files or state?
3. **Commit successful work** — Stage and commit files from passing subagents only
4. **Retry the failed subtask** — Dispatch a new subagent with additional context:

```
Agent("
## Objective
RETRY: Add order validation (previous attempt failed)

## Previous Failure Context
The prior attempt failed with this error:
{error_output}

The prior agent modified these files:
{files_modified}

The approach that failed was:
{description_of_what_was_tried}

## Instructions
Try a DIFFERENT approach than the one described above.
{rest_of_prompt_with_updated_guidance}

## Verification
Run: `pytest tests/test_orders.py -v`
")
```


**Read:** `references/verification.md` for detailed verification reference material.

# Identify files changed by failed subagents
git diff --name-only

# Revert only the problematic files
git checkout HEAD -- src/api/orders.py tests/test_orders.py

# Keep the successful files staged
git add src/api/users.py tests/test_users.py
git commit -m "feat: add user endpoint validation

Order validation failed and was reverted — will retry separately."
```

---

## STEP 7: Context Management for Subagents

Efficient context management is the difference between subagents that succeed on the first attempt and subagents that waste cycles on misunderstandings.

### 7.1 What to Pass to Subagents

| Always Pass | Never Pass |
|------------|------------|
| Exact file paths to read and modify | Entire conversation history |
| The specific coding pattern to follow (as a file path reference) | Unrelated subtask details |
| Verification command and expected output | Progress tracking for other subtasks |
| Error context if this is a retry | User's personal preferences (unless relevant) |
| Relevant type definitions or interfaces | Full project architecture docs |

### 7.2 Reducing Subagent Context Cost

Subagents read files into their own context windows. To minimize waste:

1. **Point, don't paste** — Say "Read `src/services/OrderService.ts` lines 15-45 for the pattern" instead of pasting the code into the prompt
2. **Specify line ranges** — When a subagent only needs a specific function, give the line range
3. **Limit read scope** — List only the files essential for the subtask, not every file in the module
4. **Provide summaries for large contexts** — Instead of "read the entire test suite," say "Tests use pytest with fixtures defined in conftest.py. Each test file follows the pattern: setup fixture, call function, assert output."

### 7.3 Main Context Budget

The main orchestration context must reserve capacity for:

- Tracking all subagent statuses and results
- Making decisions about failures and retries
- Running integration verification after waves
- Communicating final results to the user

If the main context is already deep into a long conversation, consider using the orchestration patterns from `/executing-plans` instead — it has structured progress tracking that survives compaction better.

---

## STEP 8: File Conflict Avoidance & Advanced Patterns

File conflicts are the most common failure mode in subagent-driven development. The **Ownership Rule** is the core prevention mechanism: **every file must be owned by exactly one subagent or the main context at any given time.** No exceptions.

Before dispatching, create a file ownership map listing which agent owns which files, which are read-only for all, and which are handled by the main context as pre/post-work.

For detailed patterns including:
- Ownership map templates and shared file strategies (post-work, append-only, file splitting)
- Lock file and generated file rules
- Research fan-out, progressive delegation, subagent chains, and watchdog patterns

Read: `references/orchestration-patterns.md`

---

## STEP 9: Completion Summary

After all subtasks are complete (or execution is halted), produce a structured summary.


**Read:** `references/completion-summary.md` for detailed step 9: completion summary reference material.

## MUST DO

- Always evaluate the decision framework (Step 1) before dispatching subagents — default to sequential when in doubt
- Always complete and commit pre-work before dispatching subagents that depend on it
- Always include explicit file ownership boundaries in every subagent prompt
- Always include a verification command in every subagent prompt
- Always validate that no two subagents modified the same file after each wave completes
- Always run integration tests after aggregating subagent results — subtask tests alone are insufficient
- Always use specific file paths in `git add` — never use `git add -A` or `git add .`
- Always pass failure context when retrying a subagent — include what was tried and why it failed
- Always track subagent status in the main context (dispatched, running, passed, failed, blocked)
- Always commit successful subagent work before retrying failed subtasks — do not risk losing passing work

## MUST NOT DO

- MUST NOT parallelize subtasks that modify the same file — use the ownership rule (Step 8) to prevent this
- MUST NOT dispatch subagents without a clear verification command — unverifiable subtasks produce unvalidated code
- MUST NOT let subagents modify lock files, generated code, or CI config — handle these in main context only
- MUST NOT retry a failed subagent more than 3 times — escalate to main context or the user after 3 failures
- MUST NOT pass entire conversation history to subagents — pass only the context needed for the specific subtask
- MUST NOT dispatch subagents for tasks under 5 minutes of total work — the orchestration overhead is not justified
- MUST NOT skip integration verification after merging subagent work — individual subtask tests do not guarantee correctness
- MUST NOT dispatch subagents when the task is exploratory or ambiguous — explore and clarify first, then dispatch
- MUST NOT use subagents as a substitute for understanding the task — the main context must understand the full picture before delegating pieces
- MUST NOT allow subagents to communicate with each other — all coordination flows through the main context
