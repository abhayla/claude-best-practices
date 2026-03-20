# 1.3 Build the Analysis Manifest

### 1.3 Build the Analysis Manifest

Construct a manifest of what to analyze:

```
ANALYSIS MANIFEST
=================

New files (full scan):
  src/services/UserService.py (245 lines)
  src/models/Role.py (89 lines)

Modified files (changed lines only):
  src/routes/users.py (+45, -12) — 45 added lines to check
  src/middleware/auth.py (+8, -3) — 8 added lines to check
  tests/test_users.py (+120, -5) — 120 added lines to check

Deleted files (reference check):
  src/utils/old_validator.py — check for dangling imports

Renamed files (import check):
  src/helpers/format.py -> src/utils/format.py — verify imports updated

Total lines to analyze: 507 (added/changed only)
```

---

