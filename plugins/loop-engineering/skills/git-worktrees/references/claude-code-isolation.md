# Claude Code's Built-in Worktree Isolation

## 4.1 The `isolation: "worktree"` Parameter

Claude Code's `Agent()` tool supports an `isolation` parameter that automatically creates
a git worktree for the subagent, runs the agent inside it, and manages lifecycle:

```
Agent("
## Objective
Implement user authentication middleware

## Files to Modify
- src/middleware/auth.ts
- tests/middleware/auth.test.ts
", isolation="worktree")
```

## 4.3 Dispatching Multiple Isolated Agents

```
# Dispatch three agents, each in their own worktree
Agent("
## Objective: Implement user validation
## Files: src/validators/user.ts, tests/validators/user.test.ts
## Verification: npm test -- --grep 'user validator'
", isolation="worktree")

Agent("
## Objective: Implement order validation
## Files: src/validators/order.ts, tests/validators/order.test.ts
## Verification: npm test -- --grep 'order validator'
", isolation="worktree")

Agent("
## Objective: Implement product validation
## Files: src/validators/product.ts, tests/validators/product.test.ts
## Verification: npm test -- --grep 'product validator'
", isolation="worktree")
```

Each agent gets its own worktree. Even if all three agents need to read `src/config.ts`,
there is no conflict because each has a separate copy on disk.

## 4.4 Retrieving Results from Isolated Agents

After isolated agents complete, their changes exist on separate branches. The orchestrator
must merge them:

```bash
# List branches created by isolated agents
git branch --list 'agent/*'

# Review changes from each agent
git log main..agent/task42-user-validation --oneline
git diff main...agent/task42-user-validation

# Merge or rebase (see Step 6 for strategies)
```
