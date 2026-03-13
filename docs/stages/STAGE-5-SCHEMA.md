# Stage 5: Schema Design, Migrations & Seed Data — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to design database schema, generate migrations, and create seed data — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 2 (Plan — data model details) + Stage 3 (Scaffold — project structure + DB service)
> **Last Updated:** 2026-03-13
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
        └───────────┬───────────┘
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
  │  Seed Data & Fixtures        │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Dev seed script           │
  │  • Test factory functions    │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  API Alignment & Gate        │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • DB types ↔ API types      │
  │  • Query plan check (pg-qry) │
  │  • ERD documentation         │
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
 ┌──────────────────────────────────────────────┐
 │                                              │
 │  ┌──────────────────┐ ┌──────────────────┐   │
 │  │ From ST2: plan.md│ │ From ST3:        │   │
 │  │  • Data model    │ │  • Project struct│   │
 │  │    details       │ │  • DB service    │   │
 │  │  • Task breakdown│ │    (Docker)      │   │
 │  └────────┬─────────┘ └────────┬─────────┘   │
 │           │                    │              │
 └───────────┼────────────────────┼──────────────┘
             │                    │
             └─────────┬──────────┘
                       │
                       ▼
        ┌───────────────────────────────┐
        │                               │
        │  ███ STAGE 5: SCHEMA ███      │
        │                               │
        │  schema-designer              │
        │  db-migrate                   │
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
 │            │ │           │ │  data)   │ │ funcs    │
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

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Entity-Relationship design | Stage 5 prompt (Step 2) | ✅ Covered | — |
| 2 | Normalization check (3NF) | Stage 5 prompt (Step 2.2) | ✅ Covered | **Database Normal Forms** |
| 3 | Migration file generation | `fastapi-db-migrate` (Alembic) + `db-migrate` (Prisma, Knex, Django, TypeORM, Drizzle) | ✅ Covered | — |
| 4 | Reversible migrations (up + down) | Stage 5 prompt (Step 3: "both up AND down") | ✅ Covered | — |
| 5 | Seed data scripts | Stage 5 prompt (Step 4) | ✅ Covered | — |
| 6 | Test fixtures / factories | Stage 5 prompt (Step 4.2) | ✅ Covered | — |
| 7 | ERD documentation | Stage 5 prompt (Step 2.4) | ✅ Covered | — |
| 8 | Index design & justification | Stage 5 prompt (Step 2.1) | ✅ Covered | — |
| 9 | Schema versioning / evolution strategy | `schema-designer` (Step 4: expand-contract pattern) | ✅ Covered | **Evolutionary Database Design (Fowler)** |
| 10 | Data migration (separate from schema) | `schema-designer` (Step 4.2: separate DDL/DML migrations) | ✅ Covered | — |
| 11 | Multi-tenant schema patterns | `schema-designer` (Step 6: multi-DB considerations) | ⚠️ Partial — mentioned but not deep | **Multi-tenancy Patterns** |
| 12 | Performance: query plan analysis | `schema-designer` (Step 3.3) + `pg-query` skill | ✅ Covered | **Query Optimization** |
| 13 | Schema security (row-level security, column encryption) | `schema-designer` (Step 2.4: PII identification + RLS) | ✅ Covered | **OWASP Data Protection** |
| 14 | Audit trail / temporal tables | `schema-designer` (Step 2.1: created_at/updated_at audit columns) | ⚠️ Partial — basic audit, no bi-temporal | **Temporal Data (Snodgrass)** |
| 15 | API schema alignment (DB ↔ API contract) | `schema-designer` (Step 5: type mapping + sync rules) | ✅ Covered | **Contract-First Design** |
| 16 | Database-agnostic design | `schema-designer` (Step 6: multi-DB feature matrix) | ✅ Covered | **Portability (ISO 25010)** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Database Normal Forms** | 1NF through 3NF, BCNF | ✅ 3NF check included |
| **Evolutionary Database Design (Fowler)** | Schema evolution strategy, backward-compatible migrations, expand-contract pattern | ✅ Expand-contract pattern in `schema-designer` Step 4, backward compatibility contract per migration |
| **OWASP Data Protection** | Column-level encryption for PII, row-level security, parameterized queries | ✅ PII register + RLS + encryption recommendations in `schema-designer` Step 2.4 |
| **Temporal Data Patterns** | Audit trail, history tables, bi-temporal modeling | ⚠️ Basic audit columns (created_at/updated_at) — no bi-temporal modeling |
| **Contract-First Design** | DB schema aligned with API contract (OpenAPI/GraphQL) | ✅ Type mapping + sync rules in `schema-designer` Step 5 |
| **Query Optimization** | Index coverage analysis, EXPLAIN ANALYZE on seed data queries | ✅ `schema-designer` Step 3.3 + delegation to `pg-query` for interactive analysis |

## Gap Proposals

### Gap 5.1: `schema-designer` skill (Priority: P1)

**Problem it solves:** No dedicated skill for holistic database schema design. Schema logic is inline in Stage 5 prompt, and `fastapi-db-migrate` only covers Alembic migration generation — not design, evolution strategy, security, or query analysis.

**What it needs:**
- Evolutionary design strategy (expand-contract migrations)
- Query plan analysis on seed data (EXPLAIN ANALYZE)
- PII column identification and encryption recommendations
- API contract alignment check (DB types ↔ API response types)
- Multi-database support (PostgreSQL, MySQL, SQLite, MongoDB)

**Existing coverage:** Stage 5 prompt covers ER design, normalization, indexes, seeds. `fastapi-db-migrate` covers Alembic migrations.

### Gap 5.2: Stack-neutral migration skill (Priority: P2)

**Problem it solves:** `fastapi-db-migrate` only covers FastAPI + Alembic. No skill exists for Prisma, Knex, Django, TypeORM, or Drizzle migrations.

**What it needs:**
- Generic `db-migrate` skill that detects ORM and delegates to stack-specific tooling
- Or: individual stack-prefixed skills (`prisma-migrate`, `django-migrate`)

**Existing coverage:** `fastapi-db-migrate` for Alembic only.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `docs/schema/erd.md` | Stage 6 (Pre-Tests), Stage 7 (Impl), Stage 11 (Docs) | Text ERD diagram |
| Migration files | Stage 7 (Impl — runs migrations), Stage 10 (Deploy — runs in prod) | ORM-specific migration files |
| Seed script | Stage 6 (Pre-Tests — test data), Stage 7 (Impl — dev data) | Python/TypeScript script |
| Test fixtures/factories | Stage 6 (Pre-Tests), Stage 8 (Post-Tests) | Factory functions |

## Research Targets

- **GitHub**: `database schema design patterns`, `evolutionary database design`, `migration best practices <framework>`
- **Reddit**: r/PostgreSQL — "schema evolution strategy", r/Database — "migration patterns production"
- **Twitter/X**: `database migration strategy`, `schema design AI coding`

## Stack Coverage

| Stack | Migration Tool Covered | Notes |
|-------|----------------------|-------|
| FastAPI + SQLAlchemy | ✅ `fastapi-db-migrate` | Alembic-specific |
| Django | ⚠️ Mentioned in prompt | No dedicated skill |
| Node + Prisma | ⚠️ Mentioned in prompt | No dedicated skill |
| Node + Knex | ⚠️ Mentioned in prompt | No dedicated skill |
| Android (Room) | ❌ | Not mentioned |
| Firebase (Firestore) | ❌ | NoSQL — different paradigm |

## Autonomy Verdict

**✅ Can run autonomously.** `schema-designer` skill now covers: ER modeling with normalization check, PII identification with protection strategies, evolutionary design (expand-contract pattern), query plan analysis (with `pg-query` delegation), API contract alignment, multi-DB support, and comprehensive review checklist. Combined with `fastapi-db-migrate` for Alembic and `pg-query` for PostgreSQL analysis, all major capabilities are ✅. Minor gaps remain in multi-tenancy depth and bi-temporal modeling.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `schema-designer` skill created with ER modeling, PII identification, expand-contract evolution, query plan analysis, API alignment, multi-DB support — 5 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `db-migrate` skill created — stack-neutral migrations supporting Prisma, Knex, Django, TypeORM, Drizzle, SQLAlchemy/Alembic |
