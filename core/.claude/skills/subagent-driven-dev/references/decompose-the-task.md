# STEP 2: Decompose the Task

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
