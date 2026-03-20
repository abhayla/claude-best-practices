# STEP 1: Decide Whether to Use Subagents

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

