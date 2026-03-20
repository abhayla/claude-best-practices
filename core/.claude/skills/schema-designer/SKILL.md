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
version: "1.0.0"
type: workflow
---

# Schema Designer — Holistic Database Schema Design

Design production-ready database schemas with normalization, evolution strategy, security, query analysis, and API alignment.

**Input:** $ARGUMENTS

---

## STEP 1: Gather Requirements

1. **Parse input** — Accept a PRD file, data model description, existing schema file, or entity list
2. **If PRD provided** — Extract entities from user stories, ACs, and data model sections
3. **If existing schema** — Read the current schema to understand what's already in place
4. **If business rule constraints provided** — Incorporate them into schema design (CHECK constraints, triggers, domain validations). For each constraint, decide if it belongs at the DB level (CHECK, UNIQUE, FK, trigger) or application level (service validation), and document the decision.
5. **Identify data questions:**
   - What are the core entities and their relationships?
   - What are the expected data volumes (rows per table)?
   - What are the primary access patterns (read-heavy? write-heavy? mixed)?
   - Are there multi-tenancy requirements?
   - What PII/sensitive data exists?
   - What business rules constrain the data? (cardinality limits, state machines, domain ranges)

Present entity list and wait for confirmation before proceeding.

---

## STEP 2: Entity-Relationship Design


**Read:** `references/entity-relationship-design.md` for detailed step 2: entity-relationship design reference material.

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


**Read:** `references/evolution-strategy.md` for detailed step 4: evolution strategy reference material.

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

## STEP 6: Multi-Tenancy Design

If Step 1 identified multi-tenancy requirements, choose an isolation strategy:


**Read:** `references/multi-tenancy-design.md` for detailed step 6: multi-tenancy design reference material.

## STEP 6b: Multi-Database Considerations

If the project requires support for multiple databases, document differences:

| Feature | PostgreSQL | MySQL | SQLite | MongoDB |
|---------|-----------|-------|--------|---------|
| UUID type | `UUID` native | `CHAR(36)` or `BINARY(16)` | `TEXT` | `ObjectId` |
| JSON queries | `jsonb` operators | `JSON_EXTRACT` | `json_extract` | Native |
| Full-text search | `tsvector + GIN` | `FULLTEXT` index | `FTS5` extension | `$text` |
| Array type | `ARRAY` native | JSON array | Not supported | Native |
| Row-level security | Native `POLICY` | Views + grants | Not supported | Field-level |
| Auto-increment | `GENERATED ALWAYS AS IDENTITY` | `AUTO_INCREMENT` | `AUTOINCREMENT` | `_id` auto |
| Temporal tables | No native (use triggers) | `SYSTEM VERSIONING` (MariaDB) | Not supported | Change streams |
| Schema-per-tenant | Native `CREATE SCHEMA` | Separate databases | Not supported | Separate databases |

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
- Respects FK insertion order (parent tables before child tables)
- Includes at least 2 tenants if multi-tenant schema

### 7.4 Test Data Factories

Generate stack-appropriate factory functions for test data creation. Factories MUST produce valid, related objects with sensible defaults and support per-field overrides.

#### Python (factory_boy + SQLAlchemy/Django)

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Project
from app.db.session import TestSession

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = TestSession
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    status = "active"
    created_at = factory.LazyFunction(datetime.utcnow)

class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session = TestSession

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Project {n}")
    owner = factory.SubFactory(UserFactory)
    org_id = factory.LazyAttribute(lambda o: o.owner.org_id)

# Usage in tests:
# user = UserFactory(status="inactive")
# project = ProjectFactory(owner=user)
```

For Django, use `factory.django.DjangoModelFactory` instead of `SQLAlchemyModelFactory`.

#### TypeScript (fishery + Prisma/TypeORM)

```typescript
// tests/factories.ts
import { Factory } from "fishery";
import { User, Project } from "@prisma/client";

const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  email: `user${sequence}@example.com`,
  name: `User ${sequence}`,
  status: "active",
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
}));

const projectFactory = Factory.define<Project>(({ sequence, associations }) => ({
  id: `project-${sequence}`,
  name: `Project ${sequence}`,
  ownerId: associations.owner?.id ?? userFactory.build().id,
  orgId: associations.owner?.orgId ?? "org-1",
  createdAt: new Date("2026-01-01"),
}));

// Usage in tests:
// const user = userFactory.build({ status: "inactive" });
// const project = projectFactory.build({ owner: user });
// For DB-inserted records: await userFactory.create({ ... }) with Prisma client
```

#### Kotlin / Android (Room in-memory test helpers)

```kotlin
// tests/factories/TestDataFactory.kt
object TestDataFactory {
    private var sequence = 0

    fun createUser(
        id: String = "user-${++sequence}",
        email: String = "user$sequence@example.com",
        name: String = "User $sequence",
        status: String = "active",
    ): UserEntity = UserEntity(
        id = id,
        email = email,
        name = name,
        status = status,
        createdAt = Instant.parse("2026-01-01T00:00:00Z"),
    )

    fun createProject(
        id: String = "project-${++sequence}",
        name: String = "Project $sequence",
        ownerId: String = createUser().id,
    ): ProjectEntity = ProjectEntity(
        id = id,
        name = name,
        ownerId = ownerId,
        createdAt = Instant.parse("2026-01-01T00:00:00Z"),
    )

    fun reset() { sequence = 0 }
}

// Usage in tests with in-memory Room database:
// val db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
//     .allowMainThreadQueries().build()
// val user = TestDataFactory.createUser(status = "inactive")
// db.userDao().insert(user)
```

#### Factory Rules

- **Deterministic** — No `random()`, no `Date.now()`. Use sequences and fixed dates.
- **Self-contained** — Each factory builds valid objects independently. Use `SubFactory` / `associations` for related objects.
- **Override-friendly** — Every field has a default but accepts overrides via constructor/builder args.
- **Reset between tests** — Sequence counters and shared state reset in `beforeEach` / `@Before`.
- **Match schema exactly** — Factory field names and types MUST mirror the DB schema 1:1. If the schema has `created_at TIMESTAMPTZ`, the factory MUST produce a timezone-aware timestamp.

---

## STEP 8: Review Checklist

Before presenting the schema, verify:

- [ ] Every entity has a primary key (UUID or BIGINT — justified)
- [ ] Every foreign key has an index
- [ ] All tables pass 3NF check (intentional denormalization documented)
- [ ] PII columns identified with protection strategy
- [ ] Temporal modeling decision documented per entity (standard / history table / bi-temporal)
- [ ] History tables have `valid_from`/`valid_to` columns with proper indexes
- [ ] Access patterns documented with matching indexes
- [ ] Evolution strategy defined (expand-contract)
- [ ] Every migration has UP + DOWN scripts
- [ ] API contract alignment verified (no type mismatches)
- [ ] Multi-tenancy strategy chosen and applied (if applicable)
- [ ] Tenant isolation verified — no cross-tenant data leakage possible
- [ ] Seed data covers edge cases (including multiple tenants if multi-tenant)
- [ ] Naming conventions consistent (snake_case for SQL, camelCase for API)
- [ ] Business rule constraints mapped to DB or app enforcement level
- [ ] CHECK constraints added for domain rules (enums, ranges, positive values)
- [ ] Test factory functions generated for each entity (stack-appropriate: factory_boy / fishery / Room helpers)
- [ ] Factory field names and types match schema exactly

---

## MUST DO

- Always identify and flag PII columns with protection recommendations
- Always design indexes based on documented access patterns, not intuition
- Always include both UP and DOWN migration scripts
- Always follow the expand-contract pattern for schema evolution
- Always verify API contract alignment (Step 5)
- Always generate seed data sufficient for query plan analysis
- Always check normalization to at least 3NF
- Always document the temporal modeling decision per entity (standard / history table / bi-temporal)
- Always choose and document a multi-tenancy strategy when tenancy requirements exist
- Always scope unique constraints to tenant when using shared-schema multi-tenancy
- Always map business rule constraints to DB or app enforcement level when constraints are provided
- Always generate stack-appropriate test data factories (factory_boy for Python, fishery for TypeScript, TestDataFactory for Android/Kotlin)

## MUST NOT DO

- MUST NOT skip PII identification — every schema audit must flag sensitive data
- MUST NOT create indexes without documenting which access pattern they serve
- MUST NOT design schema without knowing the expected data volume
- MUST NOT generate migrations without DOWN scripts
- MUST NOT assume PostgreSQL — ask which database engine is in use
- MUST NOT begin implementation during this skill — this skill produces a schema design, not application code
- MUST NOT duplicate query analysis that `/pg-query` already handles — delegate to it for interactive EXPLAIN ANALYZE sessions
- MUST NOT use global unique constraints (e.g., `UNIQUE(email)`) in multi-tenant shared schemas — always scope to tenant (`UNIQUE(tenant_id, email)`)
- MUST NOT default all entities to bi-temporal — use the decision table in Step 2.5 to pick the simplest temporal model that meets the requirement
- MUST NOT generate factories with `random()` or `Date.now()` — all test data must be deterministic and reproducible
- MUST NOT skip business rule constraint mapping when constraints are provided — every rule must be explicitly assigned to DB or app enforcement
