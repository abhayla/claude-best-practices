---
name: schema-designer
description: >
  Holistic database schema design: ER modeling, normalization, evolutionary
  strategy (expand-contract), PII identification, query plan analysis, API
  contract alignment, multi-DB support. Use before generating migrations.
triggers:
  - design schema
  - database design
  - data model
  - schema design
  - ER diagram
  - entity relationship
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<PRD file path, data model description, or existing schema to evolve>"
---

# Schema Designer — Holistic Database Schema Design

Design production-ready database schemas with normalization, evolution strategy, security, query analysis, and API alignment.

**Input:** $ARGUMENTS

---

## STEP 1: Gather Requirements

1. **Parse input** — Accept a PRD file, data model description, existing schema file, or entity list
2. **If PRD provided** — Extract entities from user stories, ACs, and data model sections
3. **If existing schema** — Read the current schema to understand what's already in place
4. **Identify data questions:**
   - What are the core entities and their relationships?
   - What are the expected data volumes (rows per table)?
   - What are the primary access patterns (read-heavy? write-heavy? mixed)?
   - Are there multi-tenancy requirements?
   - What PII/sensitive data exists?

Present entity list and wait for confirmation before proceeding.

---

## STEP 2: Entity-Relationship Design

### 2.1 Entity Modeling

For each entity, define:

```markdown
### Entity: <Name>

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID / BIGINT | PK | <justification for ID type> |
| <field> | <type> | NOT NULL / UNIQUE / FK | <domain meaning> |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | Audit trail |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | Audit trail |

**Relationships:**
- Has many: <Entity> (1:N via <fk_column>)
- Belongs to: <Entity> (N:1 via <fk_column>)
- Many-to-many: <Entity> (via <join_table>)

**Access patterns:**
- Read: <primary queries — e.g., "find by email", "list by org">
- Write: <primary mutations — e.g., "create on signup", "update on login">
- Volume: ~<N> rows expected (year 1)
```

### 2.2 Normalization Check

Verify each table satisfies at least 3NF:

| Normal Form | Check | Pass? |
|-------------|-------|-------|
| **1NF** | No repeating groups, all columns atomic | |
| **2NF** | No partial dependencies (all non-key columns depend on full PK) | |
| **3NF** | No transitive dependencies (non-key columns don't depend on other non-key columns) | |

Document any **intentional denormalization** with justification:
```
DENORMALIZATION: <table>.<column>
  Reason: Read performance — avoids N+1 join on hot path
  Trade-off: Must update in two places (see sync trigger / application logic)
```

### 2.3 Relationship Diagram

Present the ERD in text format:

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│   User   │──1:N──│  Organization│──1:N──│  Project  │
│          │       │              │       │          │
│ id (PK)  │       │ id (PK)      │       │ id (PK)  │
│ email    │       │ name         │       │ name     │
│ org_id   │◄──FK──│              │       │ org_id   │◄──FK
└──────────┘       └──────────────┘       └──────────┘
```

### 2.4 PII Identification

Flag all columns containing Personally Identifiable Information:

| Table | Column | PII Category | Protection |
|-------|--------|-------------|-----------|
| users | email | Direct identifier | Index on hash, not plaintext |
| users | name | Direct identifier | Application-level encryption optional |
| users | ip_address | Indirect identifier | Rotate/purge per retention policy |
| payments | card_last4 | Sensitive | Store only last 4 digits, full number in payment processor |

For each PII column, recommend:
- **Encryption at rest** — Column-level encryption for highly sensitive data
- **Row-Level Security (RLS)** — PostgreSQL policies restricting access by role
- **Data retention** — Purge or anonymize after retention period
- **Masking** — Log/debug output must mask PII values

---

## STEP 3: Index Design

### 3.1 Index Strategy

Design indexes based on access patterns identified in Step 2:

```markdown
### Indexes for: <table>

| Index Name | Columns | Type | Justification |
|-----------|---------|------|---------------|
| idx_users_email | email | UNIQUE BTREE | Login lookup — O(log n) |
| idx_users_org_id | org_id | BTREE | List users by org — avoids seq scan |
| idx_orders_created | created_at DESC | BTREE | Recent orders query — range scan |
| idx_products_search | name, category | GIN (tsvector) | Full-text search |
```

### 3.2 Index Anti-patterns to Check

- No index on foreign keys (causes slow JOINs and DELETE cascades)
- Indexes on low-cardinality columns (boolean, status with 3 values)
- Too many indexes on write-heavy tables (each INSERT updates all indexes)
- Missing composite index for multi-column WHERE clauses
- Unused indexes (check via `pg_stat_user_indexes` after data load)

### 3.3 Query Plan Verification

After seed data is loaded, verify critical queries with EXPLAIN ANALYZE.
Delegate to `/pg-query` for interactive analysis, or run directly:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM users WHERE email = 'test@example.com';

-- Expected: Index Scan using idx_users_email
-- Red flag: Seq Scan on large table
```

Document any query that shows a sequential scan on a table expected to exceed 10K rows.

---

## STEP 4: Evolution Strategy

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

## STEP 5: API Contract Alignment

Verify the database schema aligns with the API contract (OpenAPI, GraphQL, or PRD endpoints):

### 5.1 Type Mapping

| DB Column | DB Type | API Field | API Type | Match? |
|-----------|---------|-----------|----------|--------|
| users.id | UUID | user.id | string (uuid format) | ✅ |
| users.created_at | TIMESTAMPTZ | user.createdAt | string (ISO-8601) | ✅ |
| users.status | VARCHAR(20) | user.status | enum | ⚠️ DB allows any string, API restricts to enum |

### 5.2 Common Misalignment Patterns

Check for these discrepancies:
- **Enum drift** — API defines strict enum, DB allows any string → Add CHECK constraint
- **Nullable mismatch** — DB allows NULL, API marks required (or vice versa)
- **Missing API fields** — API exposes computed fields not in DB (fine) or DB columns not in API (check if intentional)
- **ID type mismatch** — DB uses integer PK, API expects UUID (or vice versa)
- **Timestamp format** — DB stores UTC, API returns without timezone info

### 5.3 Sync Rules

- Every API response field MUST trace to either a DB column or a computed value
- Every required API field MUST map to a NOT NULL DB column (or have a default)
- DB enum constraints MUST match API enum definitions exactly
- Changes to DB types MUST trigger API contract review

---

## STEP 6: Multi-Database Considerations

If the project requires support for multiple databases, document differences:

| Feature | PostgreSQL | MySQL | SQLite | MongoDB |
|---------|-----------|-------|--------|---------|
| UUID type | `UUID` native | `CHAR(36)` or `BINARY(16)` | `TEXT` | `ObjectId` |
| JSON queries | `jsonb` operators | `JSON_EXTRACT` | `json_extract` | Native |
| Full-text search | `tsvector + GIN` | `FULLTEXT` index | `FTS5` extension | `$text` |
| Array type | `ARRAY` native | JSON array | Not supported | Native |
| Row-level security | Native `POLICY` | Views + grants | Not supported | Field-level |
| Auto-increment | `GENERATED ALWAYS AS IDENTITY` | `AUTO_INCREMENT` | `AUTOINCREMENT` | `_id` auto |

For ORM-based projects, flag any ORM-specific syntax that doesn't translate across databases.

---

## STEP 7: Output Artifacts

Generate these files:

### 7.1 Schema Document
Save to `docs/schema/<feature>-schema.md`:
```markdown
# Schema Design: <Feature>
**Version:** 1.0
**Database:** PostgreSQL 16
**Last updated:** <date>

## Entities
<from Step 2>

## ERD
<from Step 2.3>

## PII Register
<from Step 2.4>

## Index Strategy
<from Step 3>

## Evolution Strategy
<from Step 4>

## API Alignment
<from Step 5>
```

### 7.2 Migration Files

Generate the initial migration using the project's ORM/migration tool:
- **FastAPI/SQLAlchemy** → Delegate to `/fastapi-db-migrate`
- **Prisma** → Generate `prisma/schema.prisma` + `npx prisma migrate dev`
- **Django** → Generate models.py + `python manage.py makemigrations`
- **Knex/TypeORM/Drizzle** → Generate migration files in the tool's format
- **Raw SQL** → Generate `.sql` files with UP/DOWN sections

### 7.3 Seed Script

Generate seed data that:
- Covers all entity types and relationships
- Includes edge cases (empty strings, max-length values, special characters)
- Creates enough volume for meaningful query plan analysis (~1000 rows for key tables)
- Uses deterministic data (no random — reproducible across environments)

---

## STEP 8: Review Checklist

Before presenting the schema, verify:

- [ ] Every entity has a primary key (UUID or BIGINT — justified)
- [ ] Every foreign key has an index
- [ ] All tables pass 3NF check (intentional denormalization documented)
- [ ] PII columns identified with protection strategy
- [ ] Access patterns documented with matching indexes
- [ ] Evolution strategy defined (expand-contract)
- [ ] Every migration has UP + DOWN scripts
- [ ] API contract alignment verified (no type mismatches)
- [ ] Seed data covers edge cases
- [ ] Naming conventions consistent (snake_case for SQL, camelCase for API)

---

## MUST DO

- Always identify and flag PII columns with protection recommendations
- Always design indexes based on documented access patterns, not intuition
- Always include both UP and DOWN migration scripts
- Always follow the expand-contract pattern for schema evolution
- Always verify API contract alignment (Step 5)
- Always generate seed data sufficient for query plan analysis
- Always check normalization to at least 3NF

## MUST NOT DO

- MUST NOT skip PII identification — every schema audit must flag sensitive data
- MUST NOT create indexes without documenting which access pattern they serve
- MUST NOT design schema without knowing the expected data volume
- MUST NOT generate migrations without DOWN scripts
- MUST NOT assume PostgreSQL — ask which database engine is in use
- MUST NOT begin implementation during this skill — this skill produces a schema design, not application code
- MUST NOT duplicate query analysis that `/pg-query` already handles — delegate to it for interactive EXPLAIN ANALYZE sessions
