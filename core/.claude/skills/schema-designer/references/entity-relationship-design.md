# STEP 2: Entity-Relationship Design

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

### 2.2b Business Rule Constraints

If business rules were provided (from PRD or Stage 5 orchestration), map each to the appropriate enforcement level:

```markdown
### Constraints for: <Entity>

| Rule | Constraint Type | DB Enforcement | App Enforcement |
|------|----------------|----------------|-----------------|
| Status must be one of: draft, active, archived | Domain | `CHECK (status IN ('draft','active','archived'))` | Enum validation in API layer |
| Price must be positive | Domain | `CHECK (price > 0)` | Input validation |
| Max 5 active projects per user | Cardinality | Trigger (complex) or none | Service layer `count()` check |
| Email unique per organization | Scoped uniqueness | `UNIQUE(org_id, email)` | — (DB is authoritative) |
| Accounts soft-delete only | Deletion policy | No CASCADE DELETE on FK | `deleted_at` column, app filters |
```

**Decision heuristic:**
- **DB level** (CHECK, UNIQUE, FK, trigger) — Use when the constraint is simple, universal, and data-integrity-critical. DB constraints prevent invalid data even from direct SQL access.
- **App level** (service/API validation) — Use when the constraint involves cross-entity logic, external state, or is complex enough that a trigger would be hard to maintain.
- **Both** — Use for defense-in-depth on critical constraints (e.g., DB CHECK + API validation).

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

### 2.5 Temporal Modeling

If the domain requires auditable history, version tracking, or point-in-time queries, apply bi-temporal modeling. Evaluate each entity against this decision table:

| Signal | Temporal Need | Example |
|--------|--------------|---------|
| "Show me the state as of last Tuesday" | Valid-time (business time) | Insurance policy effective dates |
| "Who changed this and when?" | Transaction-time (system time) | Compliance audit trail |
| "What did we *think* the value was at time T?" | Bi-temporal (both) | Financial corrections, regulatory reporting |
| No history needed, current state only | Standard `created_at`/`updated_at` | User profiles, settings |

#### Standard Audit (default for all entities)

Every entity gets `created_at` and `updated_at` timestamps. This is sufficient when you only need "when was this row last touched."

#### History Table Pattern (when transaction-time is needed)

For entities requiring full change history:

```sql
-- Main table holds current state
CREATE TABLE policies (
  id UUID PRIMARY KEY,
  holder_id UUID NOT NULL REFERENCES users(id),
  coverage_amount BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- History table records every version
CREATE TABLE policies_history (
  history_id BIGSERIAL PRIMARY KEY,
  policy_id UUID NOT NULL REFERENCES policies(id),
  -- All columns from main table (snapshot)
  holder_id UUID NOT NULL,
  coverage_amount BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  -- Transaction-time columns
  valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  valid_to TIMESTAMPTZ,  -- NULL = current version
  changed_by UUID REFERENCES users(id),
  change_reason VARCHAR(255)
);

CREATE INDEX idx_policies_hist_lookup ON policies_history(policy_id, valid_from DESC);
```

Use triggers or application-level hooks to populate the history table on every UPDATE/DELETE.

#### Bi-Temporal Pattern (when both valid-time and transaction-time are needed)

For entities where business-effective dates differ from when the change was recorded:

```sql
CREATE TABLE contracts (
  id UUID PRIMARY KEY,
  -- Business columns
  customer_id UUID NOT NULL,
  monthly_rate BIGINT NOT NULL,

  -- Valid-time (business time): when this version is/was effective
  effective_from DATE NOT NULL,
  effective_to DATE,  -- NULL = currently effective

  -- Transaction-time (system time): when this row was recorded
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  superseded_at TIMESTAMPTZ,  -- NULL = latest known version

  -- Audit
  changed_by UUID REFERENCES users(id)
);

-- Query: "What rate was effective on March 1, as we knew it on March 10?"
-- WHERE effective_from <= '2026-03-01' AND (effective_to IS NULL OR effective_to > '2026-03-01')
--   AND recorded_at <= '2026-03-10' AND (superseded_at IS NULL OR superseded_at > '2026-03-10')
```

#### Temporal Modeling Decision

For each entity, document the decision:

```markdown
| Entity | Temporal Type | Reason |
|--------|--------------|--------|
| users | Standard (created/updated) | Current state sufficient |
| policies | History table (transaction-time) | Regulatory audit trail required |
| contracts | Bi-temporal | Rate corrections must track both effective date and when we learned it |
| settings | Standard (created/updated) | No history value |
```

---

