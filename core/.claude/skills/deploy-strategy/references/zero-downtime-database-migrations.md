# STEP 4: Zero-Downtime Database Migrations

### 4.1 The Expand-Contract Pattern

Every schema change follows three phases:

```
Phase 1: EXPAND (pre-deploy migration)
  ┌─────────────────────────────────────┐
  │ Add new column/table (nullable)     │
  │ No constraints yet                  │
  │ Old code continues to work          │
  └─────────────────────────────────────┘
                    ↓
Phase 2: DEPLOY (new code)
  ┌─────────────────────────────────────┐
  │ Deploy code that writes to BOTH     │
  │ old and new columns                 │
  │ Reads from new column with fallback │
  └─────────────────────────────────────┘
                    ↓
Phase 3: CONTRACT (post-deploy migration)
  ┌─────────────────────────────────────┐
  │ Backfill data from old to new       │
  │ Add NOT NULL constraints            │
  │ Drop old column (separate deploy)   │
  └─────────────────────────────────────┘
```

### 4.2 Migration Deployment Ordering

```yaml
