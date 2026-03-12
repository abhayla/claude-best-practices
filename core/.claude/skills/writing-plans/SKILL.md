---
name: writing-plans
description: >
  Generate detailed implementation plans with bite-sized tasks, exact file paths,
  code snippets, and verification commands. Use after /brainstorm or when you have
  a clear feature to implement.
triggers:
  - write plan
  - implementation plan
  - task breakdown
  - plan feature
  - detailed plan
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<feature description, spec file path, or brainstorm output>"
---

# Writing Plans — Detailed Implementation Planning

Generate a step-by-step implementation plan with actionable, verifiable tasks.

**Feature:** $ARGUMENTS

---

## STEP 1: Understand Scope

Read the provided spec, description, or brainstorm output. If no spec or clear description exists, suggest running `/brainstorm` first to clarify requirements before planning.

1. **Parse input** — Accept a feature description (inline text), a spec file path, or output from a prior `/brainstorm` session
2. **Explore the codebase** — Identify affected files, modules, and dependencies by searching for related code, types, and tests
3. **Map boundaries** — Determine what is in scope vs. out of scope for this plan
4. **Surface risks** — Note integration points, potential breaking changes, and unknowns

Summarize the scope before proceeding. Wait for user confirmation that the scope is correct.

---

## STEP 2: Decompose into Tasks

Break the feature into bite-sized tasks. Each task should take **2-5 minutes** to complete.

**Atomic Plan Constraint:** If the total plan exceeds 5 tasks, group them into atomic plans of 2-3 tasks each. Each atomic plan should be independently executable in a fresh context to prevent context rot. Mark group boundaries clearly:

```markdown
## Atomic Plan 1: <group title>
- [ ] Task 1 ...
- [ ] Task 2 ...

## Atomic Plan 2: <group title>
- [ ] Task 3 ...
- [ ] Task 4 ...
```

For each task, include all five elements:

| Element | Description |
|---------|-------------|
| **Description** | Clear, one-sentence statement of what to do |
| **File paths** | Exact paths to create or modify (verified against codebase) |
| **Code snippet** | Snippet or pseudocode showing the change |
| **Verification** | Command to confirm the task is complete (test, build, curl, etc.) |
| **Estimated time** | 2-5 minutes per task |

Order tasks by dependency — no task should reference work from a later task.

**Task format:**

```markdown
### Task N: <short title>

**Description:** <what to do and why>

**Files:**
- `path/to/file.ext` (modify)
- `path/to/new-file.ext` (create)

**Code:**
```<language>
// snippet showing the change
```

**Verify:**
```bash
<command that proves this task is done>
```

**Time:** ~N min
**Depends on:** Task X, Task Y (or "None")
```

---

## STEP 3: Add Dependency Graph

After decomposing tasks:

1. **Map dependencies** — For each task, list which other tasks must be completed first
2. **Identify parallelizable tasks** — Mark tasks that have no mutual dependencies and can be executed concurrently
3. **Find the critical path** — Determine the longest chain of dependent tasks (this sets the minimum total time)

Present the dependency graph as a simple list:

```
Task 1 → Task 3 → Task 5 → Task 7  (critical path)
Task 2 → Task 4 ↗
Task 6 (independent, parallelizable)
```

---

## STEP 4: Review Plan Quality

Before presenting the plan, run through this self-review checklist:

- [ ] Every task has a verification command
- [ ] Every task takes 2-5 minutes (split tasks that are larger, merge tasks that are trivial)
- [ ] All file paths exist in the codebase (for modifications) or have valid parent directories (for new files)
- [ ] Edge cases are covered (error handling, empty states, validation)
- [ ] Task ordering respects dependencies — no forward references
- [ ] No duplicate work across tasks
- [ ] Total plan covers the full scope from Step 1

Fix any issues found before proceeding.

---

## STEP 5: Present for Approval

Present the plan in logical sections (e.g., data layer, business logic, API, tests, integration). Show one section at a time.

After each section:
1. Wait for user feedback
2. Accept modifications, additions, or removals
3. Incorporate changes before showing the next section

Do NOT dump the entire plan at once.

---

## STEP 6: Save Plan and Companion Files

Save the approved plan and create companion files for persistent working memory:

1. Ask the user for a save location
2. If no preference, default to `docs/plans/<feature-name>-plan.md`
3. Format as markdown with checkboxes for progress tracking:

```markdown
# Implementation Plan: <Feature Name>

**Created:** <date>
**Estimated total time:** <sum of task times>
**Critical path:** <task chain>

## Tasks

- [ ] **Task 1:** <title>
  - Files: `path/to/file.ext`
  - Verify: `<command>`
  - Time: ~N min
  - Depends on: None

- [ ] **Task 2:** <title>
  ...
```

4. Create companion files alongside the plan:

**`docs/plans/<feature-name>-findings.md`** — Research log for discoveries during implementation:
```markdown
# Findings: <Feature Name>

## Discoveries
<!-- Append findings here during research/implementation -->

## Constraints Found
<!-- Limitations, blockers, or unexpected dependencies -->

## Key Code References
<!-- Important files, functions, or patterns discovered -->
```

**`docs/plans/<feature-name>-progress.md`** — Running session log:
```markdown
# Progress: <Feature Name>

## Session Log
<!-- Append progress entries as work proceeds -->

## Decisions Made
<!-- Record decisions with reasoning during execution -->

## Blockers
<!-- Current blockers and their status -->
```

### The 2-Action Rule

During research and implementation phases, apply the **2-Action Rule**: after every 2 browse, search, or read operations, immediately save key findings to the `findings.md` companion file. This prevents information loss when the context window compacts or the session ends unexpectedly.

```
Search codebase → Read file → SAVE to findings.md
Browse docs → Read API → SAVE to findings.md
```

This is the filesystem-as-working-memory principle: **Context Window = RAM, Filesystem = Disk.** Anything important enough to remember MUST be written to disk, not held only in context.

---

## STEP 7: Suggest Next Steps

After saving the plan, recommend one or more follow-up actions:

- **Execute the plan** — Work through tasks sequentially, checking off each one
- **`/plan-to-issues`** — Convert the plan into tracked GitHub Issues with labels and dependencies
- **Manual execution** — Hand the plan to a developer for independent implementation

---

## MUST DO

- Always verify file paths against the actual codebase before including them in the plan
- Always include a verification command for every task — no exceptions
- Always wait for user approval between sections in Step 5
- Always order tasks so dependencies come first
- Always include the dependency graph (Step 3) even for simple plans
- Split any task that would take more than 5 minutes into smaller tasks

## MUST NOT DO

- MUST NOT skip scope confirmation (Step 1) — misunderstood scope produces useless plans
- MUST NOT include tasks without verification commands — unverifiable tasks get skipped or done wrong
- MUST NOT present the entire plan at once — show section by section for review
- MUST NOT begin implementation during this skill — this skill produces a plan, not code
- MUST NOT include vague tasks like "refactor as needed" or "clean up" — every task must be specific and measurable
- MUST NOT assume file paths exist — verify by searching the codebase first
