# 1.4 Flag Ambiguous Matches

### 1.4 Flag Ambiguous Matches

Some matches need human judgment:

```
AMBIGUOUS — Requires manual review:
  src/utils/naming.ts:42    — "UserServiceFactory" — rename to AccountServiceFactory?
  src/types/global.d.ts:18  — "UserServiceConfig" — rename to AccountServiceConfig?
  docs/adr/003-auth.md:15   — historical reference — update or leave as-is?
  migrations/002_add_user_service_table.sql — migration file — NEVER rename
```

Present ambiguous matches to the user for a decision before proceeding.

---

