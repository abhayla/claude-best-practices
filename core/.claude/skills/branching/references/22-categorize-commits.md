# 2.2 Categorize Commits

### 2.2 Categorize Commits

Separate commits into two categories:

| Category | Pattern | Action |
|----------|---------|--------|
| **Keep** | `feat:`, `fix:`, `refactor:`, `perf:`, `docs:` | Preserve as individual commits |
| **Squash** | `address review`, `fix typo`, `fixup`, `wip`, `oops`, `nit` | Squash into the nearest preceding "keep" commit |

From the example above:

```
KEEP:   9d7e2a1 feat: add user registration endpoint
SQUASH: c8a3f1d address review: add test for boundary condition  -> into 9d7e2a1
KEEP:   b2d4e6f fix: handle edge case for empty email
KEEP:   1e5f8g9 feat: add input validation for user registration
SQUASH: a7c9d4e address review: rename variable per feedback     -> into 1e5f8g9
SQUASH: f3a1b2c fix typo in error message                        -> into 1e5f8g9
```

