# STEP 4: Evolution Strategy

### 4.1 Expand-Contract Pattern

All schema changes MUST follow the expand-contract pattern for zero-downtime deployments:

```
Phase 1: EXPAND — Add new column/table (nullable, no constraints)
  → Deploy code that writes to BOTH old and new
Phase 2: MIGRATE — Backfill data from old to new
  → Verify data integrity
Phase 3: CONTRACT — Remove old column/table, add constraints
  → Deploy code that reads only from new
```

Document the evolution strategy for each entity:

```markdown
### Evolution: <Entity>

**Current version:** v1 (initial schema)
**Anticipated changes:**
- v2: Add <column> for <feature> — expand-contract, 2 migrations
- v3: Split <table> into <table_a> + <table_b> — 3-phase migration

**Breaking change policy:**
- Column renames: NEVER rename — add new column, deprecate old
- Type changes: Add new column with new type, migrate data, drop old
- Table renames: Create view with old name → new table, deprecate view
```

### 4.2 Migration Ordering Rules

1. **Schema migrations** (DDL) and **data migrations** (DML) MUST be separate files
2. Every migration MUST have both UP and DOWN scripts
3. Migrations MUST be idempotent (`IF NOT EXISTS`, `IF EXISTS`)
4. Migration filenames MUST include a timestamp and description:
   ```
   20260313_001_create_users_table.sql
   20260313_002_add_users_email_index.sql
   20260313_003_backfill_user_display_names.sql  (data migration)
   ```

### 4.3 Backward Compatibility Contract

For each migration, document:
```markdown
**Migration:** <filename>
**Backward compatible:** Yes / No
**Rollback safe:** Yes / No
**Requires code deploy first:** Yes / No
**Estimated duration on prod data:** ~<N> seconds/minutes
```

---

