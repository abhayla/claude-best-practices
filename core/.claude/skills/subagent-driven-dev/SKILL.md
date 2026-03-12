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
---

# Subagent-Driven Development — Parallel Task Orchestration

Orchestrate work across multiple subagents for faster, parallelized development.

**Task:** $ARGUMENTS

---

## STEP 1: Decide Whether to Use Subagents

Not every task benefits from subagent delegation. Evaluate the task against this decision framework before proceeding.

### 1.1 Use Subagents When

| Signal | Example |
|--------|---------|
| **3+ independent subtasks** | "Add logging to services A, B, and C" — each service is independent |
| **Bulk file operations** | "Update all test files to use new fixture" — each file is independent |
| **Research + implementation** | "Research API options while I scaffold the integration" — no dependency |
| **Multi-module features** | "Add validation to API, CLI, and SDK" — separate codebases |
| **Large-scale refactoring** | "Rename `UserService` across 15 files" — each file is independent |
| **Parallel test creation** | "Write unit tests for 5 utility functions" — each test file is independent |

### 1.2 Do NOT Use Subagents When

| Signal | Why Not |
|--------|---------|
| **Single-file change** | Overhead of delegation exceeds the work itself |
| **Tightly coupled logic** | Changes in one area depend on decisions in another — sequential is safer |
| **Shared state mutation** | Multiple agents writing to the same config, schema, or state file causes conflicts |
| **Under 5 minutes of total work** | Subagent setup overhead is not worth it |
| **Exploratory/ambiguous tasks** | When you don't yet know what needs to be done, explore first in the main context |
| **Database migrations** | Schema changes are inherently sequential and order-dependent |
| **Single test failure fix** | One focused fix loop is faster than spinning up orchestration |

### 1.3 Decision Checklist

Before dispatching subagents, answer all five questions:

1. **Can I identify 3+ subtasks?** If fewer than 3, do it directly.
2. **Are the subtasks truly independent?** If any subtask needs the output of another, they are dependent — execute those sequentially.
3. **Do the subtasks touch different files?** If they share files, do NOT parallelize.
4. **Is each subtask well-defined enough to describe in a self-contained prompt?** If you cannot write a clear prompt without saying "and also check what the other agent did," the tasks are coupled.
5. **Will the combined results merge cleanly?** If subagent outputs need complex reconciliation, sequential execution with manual integration is safer.

If any answer is "no," fall back to sequential execution (use `/implement` or `/executing-plans` instead).

---

## STEP 2: Decompose the Task

Break the work into subtasks suitable for subagent delegation.

### 2.1 Identify Units of Work

Analyze the task and extract independent units:

1. **Read the task description** — Understand the full scope
2. **Map affected files** — List every file that will be created, modified, or deleted
3. **Cluster by independence** — Group files that can be changed without knowledge of changes to other files
4. **Identify shared boundaries** — Find files, types, or interfaces that multiple subtasks depend on but none should modify

```
Task: "Add input validation to all API endpoints"

File mapping:
  src/api/users.py      → User validation (independent)
  src/api/orders.py     → Order validation (independent)
  src/api/products.py   → Product validation (independent)
  src/api/validators.py → Shared validator base class (BOUNDARY — do not parallelize)
  tests/test_users.py   → User validation tests (pairs with users.py)
  tests/test_orders.py  → Order validation tests (pairs with orders.py)
  tests/test_products.py → Product validation tests (pairs with products.py)

Clusters:
  Subtask A: users.py + test_users.py
  Subtask B: orders.py + test_orders.py
  Subtask C: products.py + test_products.py
  Pre-work:  validators.py (do this FIRST in main context, before dispatching)
```

### 2.2 Classify Dependencies

For each pair of subtasks, determine their relationship:

| Relationship | Definition | Action |
|-------------|------------|--------|
| **Independent** | No shared files, no shared types, no ordering constraint | Parallelize freely |
| **Shared-read** | Both read the same file but neither modifies it | Safe to parallelize |
| **Sequential** | Subtask B needs the output of Subtask A | Execute A first, then B |
| **Conflicting** | Both modify the same file | MUST NOT parallelize — execute sequentially or merge into one subtask |

### 2.3 Establish Pre-Work

Before dispatching any subagents, complete work that multiple subtasks depend on:

1. **Create shared interfaces or base classes** that subtasks will implement
2. **Set up directory structures** that subtasks will populate
3. **Write configuration or schema changes** that subtasks depend on
4. **Commit the pre-work** so subagents start from a clean, consistent state

```bash
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

### 4.1 Full Parallel (Fan-Out)

Use when all subtasks are independent and touch different files.

```
Dispatch pattern: Fan-out
  Agent A: User validation     (users.py, test_users.py)
  Agent B: Order validation    (orders.py, test_orders.py)
  Agent C: Product validation  (products.py, test_products.py)
  ↓ all complete ↓
  Main: Aggregate results, run full test suite, commit
```

Dispatch all agents simultaneously:

```
Agent("Subtask A: User validation ... [full prompt]")
Agent("Subtask B: Order validation ... [full prompt]")
Agent("Subtask C: Product validation ... [full prompt]")
```

### 4.2 Sequential with Parallel Waves

Use when some subtasks depend on others but independent groups exist within waves.

```
Wave 1 (sequential pre-work):
  Main context: Create base validator class, commit

Wave 2 (parallel):
  Agent A: User validation
  Agent B: Order validation
  Agent C: Product validation

Wave 3 (sequential post-work):
  Main context: Integration test, update API docs, commit
```

### 4.3 Pipeline (Sequential Fan-Out)

Use when later subtasks depend on earlier ones but each wave has parallelism.

```
Wave 1: Agent A (data models) + Agent B (config setup)
  ↓ both complete ↓
Wave 2: Agent C (API endpoints, depends on A) + Agent D (CLI commands, depends on A)
  ↓ both complete ↓
Wave 3: Agent E (integration tests, depends on C and D)
```

### 4.4 Research Fan-Out + Sequential Implementation

Use when you need to gather information from multiple sources before implementing.

```
Research phase (parallel):
  Agent A: "Read src/api/ and summarize all endpoint patterns"
  Agent B: "Read tests/ and summarize test conventions"
  Agent C: "Read docs/API.md and extract validation requirements"
  ↓ all complete ↓

Synthesis (main context):
  Combine research findings, make design decisions

Implementation (parallel or sequential based on findings):
  Dispatch implementation subagents with full context from research
```

This pattern is especially useful when exploring unfamiliar codebases. The research subagents consume their own context windows, keeping the main conversation lean.

---

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

### 6.2 Multiple Subagent Failures

When 2+ subagents fail in the same wave:

1. **Check for a common cause** — Same import error, shared dependency issue, or environment problem
2. **Fix the root cause in main context** if it is shared (e.g., missing package, broken base class)
3. **Commit the fix** before retrying
4. **Re-dispatch all failed subtasks** with updated context

### 6.3 Cascading Failures

When a failed subtask blocks downstream waves:

```
Wave 1: Agent A (PASSED) + Agent B (FAILED)
Wave 2: Agent C (depends on A — can proceed) + Agent D (depends on B — BLOCKED)
```

Action:
1. Dispatch Agent C (its dependency is satisfied)
2. Retry Agent B in parallel with Agent C
3. Once Agent B passes, dispatch Agent D

Do NOT wait for all retries to complete before making progress on unblocked work.

### 6.4 Retry Limits

| Attempt | Strategy |
|---------|----------|
| **1st retry** | Add failure context to prompt, suggest different approach |
| **2nd retry** | Simplify the task scope — break the subtask into smaller pieces |
| **3rd retry** | Escalate — do the work directly in the main context or ask the user |

MUST NOT retry more than 3 times. After 3 failures, the subtask has a deeper issue that automated retry will not solve.

### 6.5 Rollback a Failed Wave

If a wave produces partial results that cannot be salvaged:

```bash
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

## STEP 8: File Conflict Avoidance

File conflicts are the most common failure mode in subagent-driven development. These patterns prevent them.

### 8.1 The Ownership Rule

**Every file in the project must be owned by exactly one subagent or the main context at any given time.** No exceptions.

Before dispatching, create an ownership map:

```
File Ownership Map:
  MAIN CONTEXT:
    - src/api/validators.py (pre-work)
    - src/api/__init__.py (post-work imports)
    - tests/conftest.py (shared fixtures — main only)

  AGENT A:
    - src/api/users.py
    - tests/test_users.py

  AGENT B:
    - src/api/orders.py
    - tests/test_orders.py

  AGENT C:
    - src/api/products.py
    - tests/test_products.py

  UNOWNED (read-only for all):
    - src/models/*.py
    - src/config.py
```

If a file cannot be assigned to exactly one owner, either:
- Assign it to the main context (handle it before or after subagent dispatch)
- Merge the subtasks that need it into a single subtask

### 8.2 Shared File Patterns

When multiple subtasks need to add entries to the same file (e.g., imports in `__init__.py`, routes in a router, entries in a config):

**Pattern A: Main Context Post-Work**

Subagents do their work. Main context adds the shared-file entries after all subagents complete.

```
Subagents: Implement individual validators
Main (post-work): Add imports to __init__.py, register routes in router.py
```

**Pattern B: Append-Only Convention**

If the shared file supports appending (e.g., a YAML config, a list), each subagent appends to a DIFFERENT section or creates a SEPARATE file that gets merged:

```
Agent A creates: src/validators/user_rules.yaml
Agent B creates: src/validators/order_rules.yaml
Main (post-work): Merges YAML files or adds include directives
```

**Pattern C: Split the Shared File**

Refactor the shared file into per-module files before dispatching:

```
Before: src/api/routes.py (monolithic)
After:  src/api/routes/users.py, src/api/routes/orders.py, src/api/routes/products.py
        src/api/routes/__init__.py (imports from sub-modules)
```

This refactoring is pre-work done in the main context.

### 8.3 Lock Files and Generated Files

MUST NOT let subagents modify:
- `package-lock.json`, `poetry.lock`, `Cargo.lock` — dependency lock files
- Generated code (protobuf outputs, OpenAPI client code)
- CI/CD configuration (`.github/workflows/`)
- Database migration files

These files should be handled in the main context before or after subagent dispatch.

---

## STEP 9: Advanced Patterns

### 9.1 Subagent for Research, Main for Implementation

When facing an unfamiliar codebase or complex requirement:

```
Phase 1 — Research (parallel subagents):
  Agent A: "Read all files in src/api/ and report: file names, exported functions,
            patterns used for request validation, error handling approach"
  Agent B: "Read all files in tests/ and report: test framework, fixture patterns,
            mock strategies, assertion styles"
  Agent C: "Read docs/ARCHITECTURE.md and report: module boundaries, data flow,
            key design decisions"

Phase 2 — Synthesis (main context):
  Combine reports. Make design decisions. Write implementation plan.

Phase 3 — Implementation (parallel or sequential):
  Dispatch with full knowledge from research phase.
```

This keeps the main context lean. Research subagents may read 20+ files each, but only their summary reports enter the main conversation.

### 9.2 Progressive Delegation

Start with a small parallel batch. If it succeeds, increase parallelism:

```
Wave 1: 2 subagents (test the pattern)
  → Both pass? Increase confidence.
Wave 2: 4 subagents (scale up)
  → Any failures? Diagnose and adjust prompts.
Wave 3: Remaining subtasks
```

This is useful for bulk operations where you are uncertain whether the subtask prompt is correct. Test it on a small batch before scaling.

### 9.3 Subagent Chains

When subtask B depends on subtask A but both are complex enough to warrant subagent delegation:

```
Agent A: Implement data models
  → Wait for completion, verify, commit
Agent B: "The data models in src/models/ were just updated (committed at {hash}).
          Read the models and implement API endpoints using them."
  → Wait for completion, verify, commit
```

Pass the commit hash so Agent B reads the exact state of the code rather than a potentially stale version.

### 9.4 Watchdog Pattern

For long-running subagent batches, periodically check intermediate state:

1. Dispatch subagents
2. After each completes, immediately check its file changes against the ownership map
3. If a boundary violation is detected early, the main context can intervene before other subagents finish and create harder-to-resolve conflicts

---

## STEP 10: Completion Summary

After all subtasks are complete (or execution is halted), produce a structured summary.

### 10.1 Full Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUBAGENT ORCHESTRATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task: {task_description}
Subtasks: {total}/{total} completed
Waves: {wave_count}
Subagents dispatched: {agent_count} ({retry_count} retries)

Results:
  [PASSED] Agent A: User validation — 3 files, 3 tests added
  [PASSED] Agent B: Order validation — 3 files, 4 tests added
  [PASSED] Agent C: Product validation — 3 files, 3 tests added

Integration verification: ALL TESTS PASSING
Commits: {commit_count}

Files modified:
  src/api/users.py, src/api/orders.py, src/api/products.py
  src/api/validators.py (pre-work)
  tests/test_users.py, tests/test_orders.py, tests/test_products.py
```

### 10.2 Partial Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUBAGENT ORCHESTRATION PAUSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task: {task_description}
Subtasks: {completed}/{total} completed, {failed} failed

Results:
  [PASSED]  Agent A: User validation — committed
  [FAILED]  Agent B: Order validation — 3 retries exhausted
  [PASSED]  Agent C: Product validation — committed
  [BLOCKED] Agent D: Integration tests — blocked on Agent B

Failed subtask details:
  Agent B: Order validation
    Last error: {error_summary}
    Files with uncommitted changes: {file_list}
    Attempts: 3/3

Options:
  1. Fix Order validation manually, then resume
  2. Skip Order validation and proceed with unblocked subtasks
  3. Roll back all changes from this orchestration
```

### 10.3 Post-Completion

After orchestration completes:

1. **Run the full project test suite** — Subagent-level tests passing does not guarantee integration correctness
2. **Review the diff** — `git diff {start_hash}..HEAD` to see all changes holistically
3. **Invoke `/learn-n-improve`** to capture orchestration lessons:
   - Which subtask prompts worked well
   - Which needed retries and why
   - File boundary violations encountered
   - Patterns to reuse in future orchestrations

```
Skill("learn-n-improve", args="session")
```

---

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

- MUST NOT parallelize subtasks that modify the same file — use the ownership rule (Step 8.1) to prevent this
- MUST NOT dispatch subagents without a clear verification command — unverifiable subtasks produce unvalidated code
- MUST NOT let subagents modify lock files, generated code, or CI config — handle these in main context only
- MUST NOT retry a failed subagent more than 3 times — escalate to main context or the user after 3 failures
- MUST NOT pass entire conversation history to subagents — pass only the context needed for the specific subtask
- MUST NOT dispatch subagents for tasks under 5 minutes of total work — the orchestration overhead is not justified
- MUST NOT skip integration verification after merging subagent work — individual subtask tests do not guarantee correctness
- MUST NOT dispatch subagents when the task is exploratory or ambiguous — explore and clarify first, then dispatch
- MUST NOT use subagents as a substitute for understanding the task — the main context must understand the full picture before delegating pieces
- MUST NOT allow subagents to communicate with each other — all coordination flows through the main context
