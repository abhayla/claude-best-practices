---
name: batch
description: >
  Orchestrate parallel codebase-wide changes — renames, API migrations, pattern updates
  across many files. Performs exhaustive impact analysis, decomposes changes into independent
  batches, dispatches parallel subagents in isolated worktrees, verifies consistency across
  the full codebase, runs auto-simplify cleanup, and creates well-structured PRs with
  rollback safety. Inspired by Boris Cherny's approach to large-scale codemods.
triggers:
  - /batch
  - /codemod
  - /mass-rename
  - /migrate-api
  - batch change
  - codebase-wide rename
  - mass update
  - migrate api
  - codemod
  - rename across codebase
  - update all callers
  - replace deprecated
allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill"
argument-hint: "<description of codebase-wide change, e.g. 'rename UserService to AccountService' or 'migrate from axios v0.x to v1.x'>"
version: "1.0.1"
type: workflow
---

# Batch — Parallel Codebase-Wide Changes

Orchestrate large-scale changes across an entire codebase: renames, API migrations,
pattern updates, dependency upgrades, and structural refactors. Changes are analyzed,
decomposed into independent batches, executed in parallel via isolated subagents, and
verified for full-codebase consistency.

**Change Request:** $ARGUMENTS

---

## STEP 1: Codebase-Wide Impact Analysis

Before changing anything, build a complete picture of every file affected by the change.
Missing even one file turns a clean migration into a broken build.

### 1.1 Exhaustive Search

Run multiple search strategies to find ALL references. A single grep is never enough.

```bash
# Strategy 1: Exact string match
grep -rn "UserService" --include="*.ts" --include="*.tsx" --include="*.js" src/ tests/ scripts/

# Strategy 2: Case variations
grep -rn -i "userservice" --include="*.ts" --include="*.tsx" src/ tests/

# Strategy 3: Import paths (may differ from class name)
grep -rn "from.*user-service" --include="*.ts" src/
grep -rn "require.*user-service" --include="*.js" src/

# Strategy 4: String literals and comments
grep -rn "'UserService'\|\"UserService\"" src/ tests/ docs/

# Strategy 5: Configuration files
grep -rn "UserService" *.json *.yml *.yaml *.toml config/ .github/

# Strategy 6: Documentation
grep -rn "UserService" docs/ *.md README*

# Strategy 7: Generated files and build config
grep -rn "UserService" webpack.config.* tsconfig.* jest.config.* vite.config.*
```

### 1.3 Verify Completeness

After the initial search, validate that nothing was missed:

```bash
# Count total occurrences across the entire repo
grep -rn "UserService" . --include="*.ts" --include="*.tsx" --include="*.js" \
  --include="*.json" --include="*.yml" --include="*.yaml" --include="*.md" \
  --include="*.toml" | wc -l

# Cross-reference: search for the file path pattern too
grep -rn "user-service\|UserService\|user_service" . | grep -v node_modules | grep -v .git

# Check for dynamic references (string concatenation, template literals)
grep -rn "User.*Service\|user.*service" --include="*.ts" src/ | grep -v "UserService"
```

## STEP 2: Change Decomposition

Group affected files into independent batches that can be processed in parallel without
conflicts.


**Read:** `references/change-decomposition.md` for detailed step 2: change decomposition reference material.

## STEP 3: Parallel Execution

Dispatch one subagent per batch, each in its own worktree for full isolation.

1. Complete foundational changes (file renames, class renames) that all batches depend on and commit pre-work
2. Dispatch one `Agent()` per batch with `isolation="worktree"` — each gets: objective, change pattern, owned files, read-only files, verification commands
3. Monitor progress as results come in; retry failed batches with enriched failure context (max 3 retries)

**Read:** `references/parallel-execution.md` for pre-work examples, subagent dispatch templates, multi-batch dispatch, and retry patterns.

**Read:** `references/verification.md` for progress monitoring and batch status tracking.

---

## STEP 4: Consistency Verification

After all batches complete and their branches are merged, verify the entire codebase is consistent. Individual batch verification is necessary but not sufficient.

1. Run the type checker / compiler (tsc, mypy, go build, cargo check) — every type error indicates a missed reference
2. Run the linter (eslint, ruff, golangci-lint) — errors after renames indicate unused imports or undefined references
3. Run the full test suite (not just changed files) — the strongest signal of correctness
4. Re-run the impact analysis from Step 1 to verify zero old references remain
5. Compare symbol counts (old name count before vs new name count after should match)
6. Validate the import graph for broken chains

**Read:** `references/consistency-verification.md` for detailed verification commands by language/stack.

---

## STEP 5: Auto-Simplify

After a codebase-wide change, run a cleanup pass to remove dead code, unused imports, and redundant patterns.

1. Remove unused imports (eslint auto-fix, autoflake, goimports)
2. Delete dead code (old adapters, compatibility shims with zero callers)
3. Remove redundant type assertions from the old type
4. Run the project formatter to normalize all changes

**Read:** `references/auto-simplify.md` for cleanup commands by language/stack.

## STEP 6: PR Strategy

Choose the right PR structure based on the size and nature of the change: single PR for under 50 files, split by module for 50-200 files, or split by change type for API migrations. Every PR must include change pattern, scope, verification results, and rollback instructions.

**Read:** `references/pr-strategy.md` for PR templates, split strategies, and description format.

---

## STEP 7: Rollback Safety

Every batch change must be reversible. Create a pre-change tag, commit each batch independently, and document rollback procedures.

1. Tag current state before starting (`git tag batch/pre-<description>`)
2. One commit per batch for surgical rollback capability
3. For partial rollback: `git revert <batch-commit>` for the problematic batch
4. For full rollback: `git revert <tag>..HEAD` or reset to tag if not pushed
5. After any rollback, verify zero new-name references remain and full test suite passes

**Read:** `references/rollback-safety.md` for detailed rollback commands and verification.

---

## STEP 8: Common Change Patterns

> **Reference:** See [references/change-patterns.md](references/change-patterns.md) for full details on rename, API migration, dependency update, callback-to-async, import path, deprecated function, and parameter change patterns.

---

## STEP 9: Dry Run Mode & Progress Tracking

> **Reference:** See [references/dry-run.md](references/dry-run.md) for dry run preview diffs, risk assessment, and progress tracking dashboard details.

---

## MUST DO

- Always run exhaustive multi-strategy search (Step 1.1) — a single grep misses references
- Always categorize affected files (direct, transitive, tests, config, docs) before grouping batches
- Always present the batch plan for user approval before executing
- Always complete and commit pre-work before dispatching parallel agents
- Always use `isolation: "worktree"` for batch subagents — codebase-wide changes are too risky without isolation
- Always create a rollback tag before starting any batch work
- Always commit each batch independently — enables surgical rollback
- Always run the full test suite after merging all batches (Step 4.3) — batch-level tests are insufficient
- Always re-run impact analysis after completion (Step 4.4) — verify zero old references remain
- Always include a rollback section in PR descriptions
- Always track and report progress through every phase of execution
- Always flag ambiguous matches for human review rather than guessing

## MUST NOT DO

- MUST NOT execute a batch plan without user confirmation — show the plan first (Step 2.4)
- MUST NOT skip the impact analysis — changing files without a complete inventory causes silent breakage
- MUST NOT put files with shared imports into different parallel batches — they must be sequential or same-batch
- MUST NOT modify database migration files, lock files, or vendored dependencies in batch changes
- MUST NOT rename environment variables without coordinating with the operations team
- MUST NOT assume a single grep finds all references — use multiple search strategies (exact, case-insensitive, path patterns, string literals)
- MUST NOT skip the auto-simplify pass (Step 5) — dead imports and unused code accumulate after batch changes
- MUST NOT retry a failed batch more than 3 times — escalate to the user after 3 failures
- MUST NOT modify files outside the declared batch scope — each agent owns only its listed files
- MUST NOT create a single monolithic commit for batch changes — one commit per batch enables partial rollback
