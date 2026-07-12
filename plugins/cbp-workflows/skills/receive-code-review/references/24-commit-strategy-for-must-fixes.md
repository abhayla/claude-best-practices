# 2.4 Commit Strategy for Must-Fixes

### 2.4 Commit Strategy for Must-Fixes

Group related must-fix items into logical commits:

| Scenario | Commit Strategy |
|----------|----------------|
| Two must-fix comments on the same file, same concern | Single commit |
| Must-fix comments on different files, same theme (e.g., "add validation") | Single commit with descriptive message |
| Must-fix comments addressing unrelated issues | Separate commits |

**Commit message format:**
```
fix: address review — {concise description}

Addresses review comments #{id1}, #{id2} from @{reviewer}.
{Brief explanation of what changed and why.}
```

---

