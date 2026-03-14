# Advanced Orchestration Patterns

Supplementary reference for `subagent-driven-dev`. Covers file conflict avoidance, advanced dispatch patterns, and subagent chains.

## File Conflict Avoidance

File conflicts are the most common failure mode in subagent-driven development. These patterns prevent them.

### The Ownership Rule

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

### Shared File Patterns

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

### Lock Files and Generated Files

MUST NOT let subagents modify:
- `package-lock.json`, `poetry.lock`, `Cargo.lock` — dependency lock files
- Generated code (protobuf outputs, OpenAPI client code)
- CI/CD configuration (`.github/workflows/`)
- Database migration files

These files should be handled in the main context before or after subagent dispatch.

## Advanced Dispatch Patterns

### Subagent for Research, Main for Implementation

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

### Progressive Delegation

Start with a small parallel batch. If it succeeds, increase parallelism:

```
Wave 1: 2 subagents (test the pattern)
  → Both pass? Increase confidence.
Wave 2: 4 subagents (scale up)
  → Any failures? Diagnose and adjust prompts.
Wave 3: Remaining subtasks
```

This is useful for bulk operations where you are uncertain whether the subtask prompt is correct. Test it on a small batch before scaling.

### Subagent Chains

When subtask B depends on subtask A but both are complex enough to warrant subagent delegation:

```
Agent A: Implement data models
  → Wait for completion, verify, commit
Agent B: "The data models in src/models/ were just updated (committed at {hash}).
          Read the models and implement API endpoints using them."
  → Wait for completion, verify, commit
```

Pass the commit hash so Agent B reads the exact state of the code rather than a potentially stale version.

### Watchdog Pattern

For long-running subagent batches, periodically check intermediate state:

1. Dispatch subagents
2. After each completes, immediately check its file changes against the ownership map
3. If a boundary violation is detected early, the main context can intervene before other subagents finish and create harder-to-resolve conflicts
