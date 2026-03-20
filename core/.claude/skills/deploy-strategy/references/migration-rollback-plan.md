# Migration Rollback Plan

### Migration Rollback Plan

| Migration | Rollback Command | Data Loss? |
|-----------|-----------------|-----------|
| 001_add_column | `alembic downgrade -1` | No |
| 002_backfill_data | Manual: restore from backup | Yes — backfill is one-way |
| 003_add_constraint | `alembic downgrade -1` | No |
| 004_drop_old_column | ❌ IRREVERSIBLE | Yes — data lost |
```

**Rule:** Mark any migration that drops data as IRREVERSIBLE and require explicit approval.

---

