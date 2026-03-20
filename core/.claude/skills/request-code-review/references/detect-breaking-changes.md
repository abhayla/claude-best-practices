# STEP 3: Detect Breaking Changes

### 3.1 Breaking Change Checklist

Scan for these categories of breaking changes:

| Category | What to Check | How to Detect |
|----------|---------------|---------------|
| **Removed exports** | Functions, classes, constants removed from public API | `git diff` shows removed `export` statements |
| **Changed signatures** | Function parameters added, removed, or reordered | Compare function signatures in the diff |
| **Schema changes** | Database columns added/removed/renamed, type changes | Check migration files, ORM model changes |
| **Config format** | Changed config keys, removed options, new required fields | Diff config files, check config parsing code |
| **API response shape** | Changed JSON structure, removed fields, renamed keys | Check serializers, response builders, API routes |
| **Behavioral changes** | Same input produces different output | Check for changed conditionals, altered defaults |
| **Dependency changes** | Major version bumps, removed dependencies | Check package.json, requirements.txt, go.mod |
| **Environment variables** | New required env vars, renamed vars | Check for new `os.getenv()` / `process.env` references |

### 3.2 Breaking Change Report

```
BREAKING CHANGES DETECTED
==========================

1. [API] POST /api/v1/users response shape changed
   Before: { "user": { "id": 1, "name": "..." } }
   After:  { "data": { "id": 1, "name": "...", "role": "..." } }
   Impact: All API consumers must update response parsing
   Migration: Update client code to read from `data` instead of `user`

2. [Schema] Added NOT NULL column `role` to `users` table
   Impact: Existing rows will fail migration without a default value
   Migration: Set default value in migration, backfill existing rows

3. [Config] Renamed ENV var `DB_URL` to `DATABASE_URL`
   Impact: All deployment configs must be updated
   Migration: Update .env files, CI/CD secrets, and deployment configs

No breaking changes: [NONE DETECTED] (state this explicitly if clean)
```

---

