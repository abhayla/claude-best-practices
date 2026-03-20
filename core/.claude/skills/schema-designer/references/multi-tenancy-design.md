# STEP 6: Multi-Tenancy Design

### 6.1 Strategy Selection

| Strategy | Isolation | Complexity | Cost | Best For |
|----------|-----------|-----------|------|----------|
| **Shared schema, tenant column** | Row-level | Low | Low | SaaS with many small tenants |
| **Schema-per-tenant** | Schema-level | Medium | Medium | Compliance-sensitive (healthcare, finance) |
| **Database-per-tenant** | Full | High | High | Enterprise customers requiring data sovereignty |

Decision factors:
- **Regulatory requirements** — HIPAA/SOC2 may require schema or database isolation
- **Tenant count** — 10 tenants? Database-per-tenant is fine. 10,000? Must use shared schema
- **Cross-tenant queries** — Analytics across all tenants needs shared schema
- **Noisy neighbor risk** — Large tenants impacting others? Consider schema-per-tenant

### 6.2 Shared Schema Pattern (most common)

Add a `tenant_id` column to every tenant-scoped table:

```sql
-- Every tenant-scoped table gets tenant_id
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Composite index: tenant_id FIRST for partition pruning
CREATE INDEX idx_projects_tenant ON projects(tenant_id, created_at DESC);

-- PostgreSQL RLS for automatic tenant isolation
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON projects
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

Rules for shared schema multi-tenancy:
- `tenant_id` MUST be the first column in every composite index
- Every query MUST include `tenant_id` in WHERE clause (enforce via RLS or ORM middleware)
- Unique constraints MUST be scoped to tenant: `UNIQUE(tenant_id, email)` not `UNIQUE(email)`
- Foreign keys within tenant-scoped tables MUST NOT cross tenant boundaries
- Seed data MUST create at least 2 tenants to verify isolation

### 6.3 Schema-per-Tenant Pattern

```sql
-- Create schema per tenant
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_globex;

-- Same table structure in each schema
CREATE TABLE tenant_acme.projects (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

-- Application sets search_path per request
SET search_path TO tenant_acme, public;
```

Rules for schema-per-tenant:
- Shared reference data (countries, currencies) lives in `public` schema
- Migrations MUST run against ALL tenant schemas (use a migration runner that iterates)
- Connection pooling must support schema switching (PgBouncer `search_path`)
- Backup/restore operates per-schema for tenant-level recovery

### 6.4 Multi-Tenancy Checklist

For whichever strategy is chosen, verify:

- [ ] Every tenant-scoped table has tenant isolation (column, schema, or database)
- [ ] No query can accidentally return cross-tenant data
- [ ] Unique constraints are tenant-scoped where needed
- [ ] Indexes have `tenant_id` as leading column (shared schema)
- [ ] Seed data includes multiple tenants
- [ ] Admin/superuser queries explicitly opt out of isolation (documented)
- [ ] Tenant deletion strategy defined (soft delete? cascade? data export?)

---

