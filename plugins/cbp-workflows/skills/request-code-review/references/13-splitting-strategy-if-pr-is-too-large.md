# 1.3 Splitting Strategy (if PR is too large)

### 1.3 Splitting Strategy (if PR is too large)

When the PR exceeds 500 lines, suggest concrete splits:

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **By layer** | Changes span multiple layers | Split into "backend API" + "frontend UI" + "database migration" PRs |
| **By feature** | Multiple features bundled | Split each feature into its own PR |
| **By risk** | Mix of risky and mechanical changes | Split into "refactor (safe)" + "behavior change (needs review)" PRs |
| **By dependency** | Some changes depend on others | Create a chain: PR1 (base) -> PR2 (depends on PR1) -> PR3 |
| **Extract refactor** | Refactoring mixed with new logic | PR1: pure refactor (no behavior change), PR2: new logic on clean code |

Recommend the split with specific file groupings:

```
Recommended split:
  PR 1: "Refactor UserService to extract validation"
    Files: src/services/UserService.ts, src/validators/UserValidator.ts
    Lines: ~120
    Risk: Low (pure refactor, no behavior change)

  PR 2: "Add email verification flow"
    Files: src/services/EmailService.ts, src/routes/auth.ts, tests/
    Lines: ~200
    Risk: Medium (new auth flow)
    Depends on: PR 1
```

---

