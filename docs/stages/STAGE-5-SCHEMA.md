# Stage 5: Schema Design, Migrations & Seed Data — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to design database schema, generate migrations, and create seed data — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 2 (Plan — data model details) + Stage 3 (Scaffold — project structure + DB service)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
 ┌─────────────────────────────────────────────────────────────────┐
 │          STAGE 5: SCHEMA DESIGN & MIGRATIONS                    │
 └─────────────────────────────────────────────────────────────────┘

        ┌───────────────────────┐
        │  Read Plan from ST2   │
        │  + Scaffold from ST3  │
        │  + Prototype from ST4 │
        └───────────┬───────────┘
                    │
                    ▼
  ┌──────────────────────────────┐
  │  PRD Constraint Extraction   │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Business rules → DB/app  │
  │  • Cardinality limits       │
  │  • State machine transitions│
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Entity-Relationship Design  │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  schema-designer skill       │
  │  • Entity identification     │
  │  • Relationship mapping      │
  │  • PII column flagging       │
  │  • Audit columns (timestamps)│
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Normalization Check         │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • 1NF → 2NF → 3NF verify   │
  │  • Denormalize with reason   │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Index & Security Design     │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  • Index strategy + reasons  │
  │  • RLS policies              │
  │  • Column encryption plan    │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Migration Generation        │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  db-migrate / fastapi-db-    │
  │  migrate skill               │
  │  • UP + DOWN migrations      │
  │  • Expand-contract pattern   │
  │  • Separate DDL / DML        │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Migration Verification      │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  db-migrate-verify skill     │
  │  • Forward + rollback test   │
  │  • Data integrity check      │
  │  • Dangerous op detection    │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Seed Data & Fixtures        │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  schema-designer (Step 7)    │
  │  • Dev seed script           │
  │  • Test factory functions    │
  │  • Stack-specific factories  │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  API Alignment & Gate        │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • DB types ↔ API types      │
  │  • Query plan check (pg-qry) │
  │  • ERD documentation         │
  │  • Structured JSON report    │
  └──────────────┬───────────────┘
                 │
            PASS │ / FAIL → retry
                 ▼
       ┌──────────────────┐
       │  Schema Output    │
       │  ████████████████ │
       └──────────────────┘
```

### Diagram B — I/O Artifact Contract

```
                          INPUTS
 ┌───────────────────────────────────────────────────────────┐
 │                                                           │
 │  ┌──────────────────┐ ┌──────────────────┐ ┌───────────┐ │
 │  │ From ST2: plan.md│ │ From ST3:        │ │ From ST4: │ │
 │  │  • Data model    │ │  • Project struct│ │  • HTML   │ │
 │  │    details       │ │  • DB service    │ │  prototype│ │
 │  │  • Task breakdown│ │    (Docker)      │ │  • Forms, │ │
 │  │  • Business rules│ │                  │ │  lists,   │ │
 │  │                  │ │                  │ │  detail   │ │
 │  │                  │ │                  │ │  views    │ │
 │  └────────┬─────────┘ └────────┬─────────┘ └─────┬─────┘ │
 │           │                    │                  │       │
 └───────────┼────────────────────┼──────────────────┼───────┘
             │                    │                  │
             └─────────┬──────────┴──────────────────┘
                       │
                       ▼
        ┌───────────────────────────────┐
        │                               │
        │  ███ STAGE 5: SCHEMA ███      │
        │                               │
        │  schema-designer              │
        │  db-migrate                   │
        │  db-migrate-verify            │
        │  fastapi-db-migrate           │
        │  pg-query                     │
        │                               │
        └──────────────┬────────────────┘
                       │
         ┌─────────────┼──────────┬──────────────┐
         │             │          │              │
         ▼             ▼          ▼              ▼
 ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
 │ erd.md     │ │ Migration │ │ Seed     │ │ Test     │
 │ (text ERD  │ │ files     │ │ script   │ │ fixtures │
 │  diagram)  │ │ (UP+DOWN) │ │ (dev     │ │ /factory │
 │            │ │ (verified)│ │  data)   │ │ funcs    │
 └─────┬──────┘ └─────┬─────┘ └────┬─────┘ └────┬─────┘
       │              │            │             │
       ▼              ▼            ▼             ▼
 ┌──────────┐  ┌──────────┐ ┌──────────┐  ┌──────────┐
 │ ST6 Tests│  │ ST7 Impl │ │ ST7 Impl │  │ ST6 Tests│
 │ ST7 Impl │  │ ST10 Depl│ │          │  │ ST8 Post │
 │ ST11 Docs│  │          │ │          │  │          │
 └──────────┘  └──────────┘ └──────────┘  └──────────┘
                   OUTPUTS
```

## Orchestration Prompt

This section is the **runnable prompt** that the pipeline orchestrator dispatches to a Stage 5 agent. The agent follows these steps sequentially, invoking skills as specified.

### STEP 1: Read Upstream Artifacts

1. **Read Stage 2 plan** — Find and read the plan document (typically `docs/plans/<feature>-plan.md`). Extract:
   - Entity list and relationships from the data model section
   - Business rules and constraints (cardinality limits, state machines, validation rules)
   - Access pattern expectations (read-heavy, write-heavy, mixed)
   - Non-functional requirements (data retention, compliance, multi-tenancy)

2. **Read Stage 3 scaffold** — Identify the project structure and database service:
   - Which ORM/migration tool is configured? (Alembic, Prisma, Django, Knex, TypeORM, Drizzle, Room)
   - Which database engine? (PostgreSQL, MySQL, SQLite, MongoDB)
   - Docker Compose database service configuration

3. **Cross-reference Stage 4 prototype** (if available) — Scan `demos/` directory for HTML prototypes:
   - Extract form fields → these imply entity columns and validation rules
   - Extract list views → these imply query access patterns and sort/filter columns
   - Extract detail views → these imply entity relationships and eager-load needs
   - Flag any UI data that doesn't map to the Stage 2 data model (potential schema gap)

### STEP 2: Extract Business Rule Constraints

Before designing entities, extract business rules from the PRD and plan that translate into database constraints. For each rule, decide enforcement level:

| Business Rule (from PRD) | Constraint Type | Enforcement Level | Implementation |
|--------------------------|----------------|-------------------|----------------|
| "A user can have at most 5 active projects" | Cardinality limit | Application + DB trigger | CHECK constraint or trigger + app validation |
| "Orders transition: draft → submitted → approved → shipped" | State machine | Application + CHECK | `CHECK (status IN ('draft','submitted','approved','shipped'))` |
| "Email must be unique per organization" | Scoped uniqueness | Database | `UNIQUE(org_id, email)` |
| "Accounts cannot be deleted, only deactivated" | Soft delete | Application | `deleted_at TIMESTAMPTZ` column, no CASCADE DELETE |
| "Price must be positive" | Domain constraint | Database | `CHECK (price > 0)` |

Document each constraint in `docs/schema/constraints.md`:

```markdown
| ID | Business Rule | Source (PRD section) | DB Constraint | App Validation | Notes |
|----|--------------|---------------------|---------------|----------------|-------|
| C1 | Max 5 active projects per user | US-003 AC-2 | None (complex) | Service layer check | Could add trigger for defense-in-depth |
| C2 | Valid order status transitions | US-007 AC-1 | CHECK constraint | State machine in OrderService | DB prevents invalid states, app enforces transitions |
```

### STEP 3: Schema Design

Invoke `/schema-designer` with the PRD/plan file and the extracted constraints.

The skill will produce:
- Entity definitions with columns, types, and constraints
- Relationship diagram (ERD)
- PII register with protection strategies
- Temporal modeling decisions per entity
- Index strategy based on access patterns
- Evolution strategy (expand-contract)
- API contract alignment check
- Multi-tenancy design (if applicable)
- Seed data and test factory generation

Pass the business rule constraints from Step 2 as additional input so the schema designer can incorporate CHECK constraints, triggers, and domain validations into the schema.

### STEP 4: Generate Migrations

Based on the detected ORM/migration tool from Step 1:

- **FastAPI + Alembic** → Invoke `/fastapi-db-migrate` with the new model definitions
- **All other ORMs** → Invoke `/db-migrate` which auto-detects the tool and generates migrations

Both skills produce UP + DOWN migration files with separate DDL and DML.

### STEP 5: Verify Migrations

Invoke `/db-migrate-verify` to validate the generated migrations:

1. **Forward migration** — Run UP, verify schema matches design
2. **Rollback test** — Run DOWN, verify schema returns to pre-migration state
3. **Round-trip test** — UP → DOWN → UP, verify final state matches fresh UP
4. **Dangerous operation detection** — Scan for DROP TABLE, DROP COLUMN, ALTER TYPE
5. **Data integrity test** — Seed test data, run migration, verify data preserved

If verification fails, fix the migration and re-run verification. Maximum 3 retry attempts before escalating.

### STEP 6: Query Plan Verification

After migrations are applied and seed data is loaded:

1. Invoke `/pg-query` (for PostgreSQL) to run EXPLAIN ANALYZE on critical queries identified from access patterns
2. Verify no sequential scans on tables expected to exceed 10K rows
3. Verify indexes are being used as designed
4. Document any query plan concerns in the schema document

For non-PostgreSQL databases, run equivalent query analysis tools or skip with documented justification.

### STEP 7: Gate — Write Structured Report

Write verification results to `test-results/schema-designer.json`:

```json
{
  "skill": "schema-designer",
  "timestamp": "<ISO-8601>",
  "result": "PASSED",
  "summary": {
    "entities_designed": 8,
    "migrations_generated": 3,
    "migrations_verified": 3,
    "seed_rows_created": 1200,
    "constraints_from_prd": 5,
    "constraints_enforced_db": 3,
    "constraints_enforced_app": 2,
    "pii_columns_flagged": 4,
    "indexes_created": 12,
    "query_plans_verified": 6,
    "query_plans_ok": 6
  },
  "quality_gate": "PASSED",
  "migration_verify": "PASSED",
  "query_plan_check": "PASSED",
  "failures": [],
  "warnings": [],
  "duration_ms": 0
}
```

If `migration_verify` is `FAILED` or any query plan shows a sequential scan on a large table, set `result` to `FAILED` and populate `failures[]`.

### STEP 8: Produce Output Artifacts

Verify all required artifacts exist on disk:

| Artifact | Path | Verified |
|----------|------|----------|
| Schema design document | `docs/schema/<feature>-schema.md` | Must include ERD, PII register, index strategy |
| Business rule constraints | `docs/schema/constraints.md` | PRD rules mapped to DB/app enforcement |
| Migration files | ORM-specific directory | UP + DOWN, verified by `db-migrate-verify` |
| Seed script | `scripts/seed.py` or `scripts/seed.ts` or equivalent | Deterministic, ~1000 rows for key tables |
| Test fixtures/factories | `tests/factories/` or `tests/fixtures/` | Stack-appropriate factory functions |
| Verification report | `test-results/schema-designer.json` | Structured JSON for stage gate |

If any artifact is missing, generate it before reporting completion.

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Entity-Relationship design | `schema-designer` (Steps 1-2) | ✅ Covered | — |
| 2 | Normalization check (3NF) | `schema-designer` (Step 2.2) | ✅ Covered | **Database Normal Forms** |
| 3 | Migration file generation | `fastapi-db-migrate` (Alembic) + `db-migrate` (Prisma, Knex, Django, TypeORM, Drizzle, Room) | ✅ Covered | — |
| 4 | Reversible migrations (up + down) | `db-migrate` (Step 3: round-trip test) + `db-migrate-verify` | ✅ Covered | — |
| 5 | Seed data scripts | `schema-designer` (Step 7.3: stack-specific factories) | ✅ Covered | — |
| 6 | Test fixtures / factories | `schema-designer` (Step 7.4: factory_boy, fishery, Room test helpers) | ✅ Covered | — |
| 7 | ERD documentation | `schema-designer` (Step 2.3) | ✅ Covered | — |
| 8 | Index design & justification | `schema-designer` (Step 3.1) | ✅ Covered | — |
| 9 | Schema versioning / evolution strategy | `schema-designer` (Step 4: expand-contract pattern) | ✅ Covered | **Evolutionary Database Design (Fowler)** |
| 10 | Data migration (separate from schema) | `schema-designer` (Step 4.2: separate DDL/DML migrations) | ✅ Covered | — |
| 11 | Multi-tenant schema patterns | `schema-designer` (Step 6: strategy selection, shared-schema with RLS, schema-per-tenant, checklist) | ✅ Covered | **Multi-tenancy Patterns** |
| 12 | Performance: query plan analysis | `schema-designer` (Step 3.3) + `pg-query` skill | ✅ Covered | **Query Optimization** |
| 13 | Schema security (row-level security, column encryption) | `schema-designer` (Step 2.4: PII identification + RLS) | ✅ Covered | **OWASP Data Protection** |
| 14 | Audit trail / temporal tables | `schema-designer` (Step 2.5: temporal modeling decision table, history table pattern, bi-temporal pattern) | ✅ Covered | **Temporal Data (Snodgrass)** |
| 15 | API schema alignment (DB ↔ API contract) | `schema-designer` (Step 5: type mapping + sync rules) | ✅ Covered | **Contract-First Design** |
| 16 | Database-agnostic design | `schema-designer` (Step 6b: multi-DB feature matrix) | ✅ Covered | **Portability (ISO 25010)** |
| 17 | Migration verification (round-trip + safety) | `db-migrate-verify` (forward, rollback, data integrity, dangerous op detection) | ✅ Covered | **Change Management** |
| 18 | PRD business rule → DB constraint mapping | Orchestration prompt (Step 2: constraint extraction) | ✅ Covered | **Domain-Driven Design** |
| 19 | Stage 4 prototype cross-reference | Orchestration prompt (Step 1.3: form/list/detail → schema validation) | ✅ Covered | **UI-Data Consistency** |
| 20 | Android Room migrations | `db-migrate` (Room section) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Database Normal Forms** | 1NF through 3NF, BCNF | ✅ 3NF check included |
| **Evolutionary Database Design (Fowler)** | Schema evolution strategy, backward-compatible migrations, expand-contract pattern | ✅ Expand-contract pattern in `schema-designer` Step 4, backward compatibility contract per migration |
| **OWASP Data Protection** | Column-level encryption for PII, row-level security, parameterized queries | ✅ PII register + RLS + encryption recommendations in `schema-designer` Step 2.4 |
| **Temporal Data Patterns** | Audit trail, history tables, bi-temporal modeling | ✅ `schema-designer` Step 2.5: decision table for standard/history/bi-temporal, history table pattern with `valid_from`/`valid_to`, bi-temporal pattern with `effective_from`/`recorded_at` |
| **Contract-First Design** | DB schema aligned with API contract (OpenAPI/GraphQL) | ✅ Type mapping + sync rules in `schema-designer` Step 5 |
| **Query Optimization** | Index coverage analysis, EXPLAIN ANALYZE on seed data queries | ✅ `schema-designer` Step 3.3 + delegation to `pg-query` for interactive analysis |
| **Domain-Driven Design** | Business rules enforced at correct architectural layer | ✅ PRD constraint extraction with DB vs app enforcement decision |
| **Change Management** | Migrations tested for safety and reversibility before deployment | ✅ `db-migrate-verify` round-trip test + dangerous operation detection |

## Gap Proposals

### Gap 5.1: `schema-designer` skill (Priority: P1) — RESOLVED

**Problem it solves:** No dedicated skill for holistic database schema design. Schema logic is inline in Stage 5 prompt, and `fastapi-db-migrate` only covers Alembic migration generation — not design, evolution strategy, security, or query analysis.

**Resolution:** `schema-designer` skill created with ER modeling, PII identification, expand-contract evolution, query plan analysis, API alignment, multi-DB support, seed data factory generation.

### Gap 5.2: Stack-neutral migration skill (Priority: P2) — RESOLVED

**Problem it solves:** `fastapi-db-migrate` only covers FastAPI + Alembic. No skill exists for Prisma, Knex, Django, TypeORM, or Drizzle migrations.

**Resolution:** `db-migrate` skill created — stack-neutral migrations supporting Prisma, Knex, Django, TypeORM, Drizzle, SQLAlchemy/Alembic, Room, and raw SQL.

### Gap 5.3: No stage orchestration prompt (Priority: P0) — RESOLVED

**Problem it solves:** The stage doc was an audit-only document with no runnable orchestration prompt. Skills existed in isolation but nothing tied them into a sequential workflow with gate checks.

**Resolution:** Added "Orchestration Prompt" section with 8 steps: read upstream artifacts, extract business constraints, invoke schema-designer, generate migrations, verify migrations, query plan verification, structured JSON gate report, artifact verification.

### Gap 5.4: `db-migrate-verify` not wired into workflow (Priority: P2) — RESOLVED

**Problem it solves:** The `db-migrate-verify` skill existed but was never referenced in Stage 5's workflow or capability checklist.

**Resolution:** Added as explicit Step 5 in the orchestration prompt and capability #17 in the checklist.

### Gap 5.5: No Stage 4 prototype cross-reference (Priority: P3) — RESOLVED

**Problem it solves:** Stage 4 HTML prototypes contain form fields, list views, and detail views that imply data structures, but Stage 5 never cross-referenced them.

**Resolution:** Added Step 1.3 in orchestration prompt to scan prototypes and flag UI data not represented in the schema.

### Gap 5.6: No PRD business rule → DB constraint mapping (Priority: P3) — RESOLVED

**Problem it solves:** Business rules in the PRD (cardinality limits, state machines, domain constraints) were not systematically extracted and mapped to DB constraints vs application-level validation.

**Resolution:** Added Step 2 in orchestration prompt with constraint extraction table and `docs/schema/constraints.md` output artifact.

### Gap 5.7: No Android Room migration support (Priority: P2) — RESOLVED

**Problem it solves:** `db-migrate` covered 6 ORM tools but not Android Room, which uses a completely different migration pattern (`@Database(version = N)` + `Migration(N, N+1)` classes).

**Resolution:** Added Room migration section to `db-migrate` skill with entity definitions, migration classes, auto-migration support, and testing patterns.

### Gap 5.8: Seed data lacks stack-specific factory patterns (Priority: P2) — RESOLVED

**Problem it solves:** `schema-designer` Step 7.3 said "generate seed data" but didn't show stack-specific factory patterns for Python (factory_boy), JS/TS (fishery/faker), or Android (Room test helpers).

**Resolution:** Enhanced `schema-designer` with Step 7.4 covering factory_boy (Python), fishery (TypeScript), and Room in-memory database test helpers (Android).

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `docs/schema/<feature>-schema.md` | Stage 6 (Pre-Tests), Stage 7 (Impl), Stage 11 (Docs) | Text ERD + full schema design |
| `docs/schema/constraints.md` | Stage 6 (Pre-Tests — constraint validation tests), Stage 7 (Impl — enforcement logic) | Business rule → constraint mapping |
| Migration files (verified) | Stage 7 (Impl — runs migrations), Stage 10 (Deploy — runs in prod) | ORM-specific migration files |
| Seed script | Stage 6 (Pre-Tests — test data), Stage 7 (Impl — dev data) | Python/TypeScript/Kotlin script |
| Test fixtures/factories | Stage 6 (Pre-Tests), Stage 8 (Post-Tests) | Factory functions (factory_boy / fishery / Room helpers) |
| `test-results/schema-designer.json` | Stage gate (pipeline orchestrator) | Structured JSON verification report |

## Research Targets

- **GitHub**: `database schema design patterns`, `evolutionary database design`, `migration best practices <framework>`
- **Reddit**: r/PostgreSQL — "schema evolution strategy", r/Database — "migration patterns production"
- **Twitter/X**: `database migration strategy`, `schema design AI coding`

## Stack Coverage

| Stack | Migration Tool Covered | Notes |
|-------|----------------------|-------|
| FastAPI + SQLAlchemy | ✅ `fastapi-db-migrate` + `db-migrate` | Alembic-specific |
| Django | ✅ `db-migrate` | `manage.py makemigrations` |
| Node + Prisma | ✅ `db-migrate` | `prisma migrate dev` |
| Node + Knex | ✅ `db-migrate` | `knex migrate:make` |
| Node + TypeORM | ✅ `db-migrate` | `typeorm migration:generate` |
| Node + Drizzle | ✅ `db-migrate` | `drizzle-kit generate` |
| Android (Room) | ✅ `db-migrate` | `@Database(version)` + `Migration` classes |
| Firebase (Firestore) | ⚠️ `firebase-data-connect` | NoSQL — different paradigm, uses Data Connect with PostgreSQL |

## Autonomy Verdict

**✅ Can run autonomously.** The stage now has a complete orchestration prompt (8 steps) that chains skills in the correct order: read upstream artifacts (ST2 plan + ST3 scaffold + ST4 prototype) → extract PRD business constraints → invoke `schema-designer` (ER modeling, normalization, PII, temporal modeling, indexes, evolution strategy, API alignment, multi-tenancy, seed data with stack-specific factories) → invoke `db-migrate` or `fastapi-db-migrate` for migration generation → invoke `db-migrate-verify` for round-trip verification → invoke `pg-query` for query plan analysis → write structured JSON gate report → verify all output artifacts. All 20 capabilities ✅. All 8 gaps resolved.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `schema-designer` skill created with ER modeling, PII identification, expand-contract evolution, query plan analysis, API alignment, multi-DB support — 5 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `db-migrate` skill created — stack-neutral migrations supporting Prisma, Knex, Django, TypeORM, Drizzle, SQLAlchemy/Alembic |
| 2026-03-13 | Gaps fixed: `schema-designer` enhanced with bi-temporal modeling (Step 2.5: decision table, history table pattern, bi-temporal pattern) and multi-tenancy design (Step 6: strategy selection, shared-schema RLS, schema-per-tenant, checklist) — both ⚠️ items flipped to ✅ |
| 2026-03-14 | P0 gap resolved: Added orchestration prompt (8 steps) tying all skills into sequential workflow with gate checks |
| 2026-03-14 | P2 gap resolved: Wired `db-migrate-verify` into orchestration Step 5 + added capability #17 |
| 2026-03-14 | P3 gap resolved: Added Stage 4 prototype cross-reference in orchestration Step 1.3 + capability #19 |
| 2026-03-14 | P3 gap resolved: Added PRD business rule → DB constraint mapping in orchestration Step 2 + capability #18 |
| 2026-03-14 | P2 gap resolved: Added Android Room migration support to `db-migrate` skill + capability #20 |
| 2026-03-14 | P2 gap resolved: Enhanced `schema-designer` with stack-specific seed data factory patterns (factory_boy, fishery, Room test helpers) |
