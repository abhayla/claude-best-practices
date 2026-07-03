# 4.2 When to Use `isolation: "worktree"`

### 4.2 When to Use `isolation: "worktree"`

| Scenario | Use `isolation: "worktree"` | Use Regular Agent |
|----------|----------------------------|-------------------|
| Agents modifying overlapping files | Yes — prevents conflicts | No — will collide |
| Agents modifying completely different files | Optional but safe | Yes — simpler |
| Agent needs to run build/test in isolation | Yes — own build cache | No — shared cache may interfere |
| Agent task is read-only research | No — unnecessary overhead | Yes — no writes to conflict |
| More than 3 parallel agents | Yes — isolation scales safely | Risky — file conflicts increase with parallelism |
| Agent needs to install different dependencies | Yes — own node_modules/venv | No — would break other agents |

