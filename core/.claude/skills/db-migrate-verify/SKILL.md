---
name: db-migrate-verify
description: >
  Verify database migrations: run forward, validate schema, run backward, validate rollback.
  Tests with seeded data to catch data-loss migrations. Supports Alembic (Python),
  Flyway/Liquibase (JVM), Prisma, and Django. Use after writing or modifying migrations.
allowed-tools: "Bash Read Grep Glob"
triggers:
  - db migrate
  - migration verify
  - schema check
  - alembic verify
  - flyway verify
argument-hint: "[migration-id|all|latest] [--rollback] [--seed-data]"
---

# DB Migration Verify

Verify database migrations are safe, reversible, and data-preserving.

**Arguments:** $ARGUMENTS

---

## STEP 1: Detect Migration Framework

Identify the migration tool from project files:

| Indicator | Framework | Commands |
|-----------|-----------|----------|
| `alembic.ini` or `alembic/` | Alembic (SQLAlchemy) | `alembic upgrade`, `alembic downgrade` |
| `flyway.conf` or `db/migration/` | Flyway | `flyway migrate`, `flyway undo` |
| `prisma/schema.prisma` | Prisma | `prisma migrate deploy`, `prisma migrate reset` |
| `manage.py` + `migrations/` | Django | `python manage.py migrate`, `python manage.py migrate <app> <prev>` |
| `liquibase.properties` | Liquibase | `liquibase update`, `liquibase rollback` |

## STEP 2: Pre-Migration State

Capture the current schema state before running migrations:

```bash
# Alembic
alembic current
alembic history --verbose

# Django
python manage.py showmigrations

# Prisma
npx prisma migrate status

# General: dump current schema
pg_dump --schema-only -f pre_migration_schema.sql $DATABASE_URL
# or for SQLite:
sqlite3 $DB_PATH ".schema" > pre_migration_schema.sql
```

## STEP 3: Forward Migration

Run the migration(s) and verify success:

```bash
# Alembic
alembic upgrade head  # or specific revision
echo $?  # Must be 0

# Django
python manage.py migrate --verbosity 2

# Prisma
npx prisma migrate deploy
```

Verify:
1. Exit code is 0
2. No warnings or errors in output
3. Migration is recorded in migration history table

## STEP 4: Schema Validation

After forward migration, verify the schema matches expectations:

```bash
# Dump post-migration schema
pg_dump --schema-only -f post_migration_schema.sql $DATABASE_URL

# Compare schemas (should show only intended changes)
diff pre_migration_schema.sql post_migration_schema.sql
```

Check for:
- Expected tables/columns exist
- Column types are correct
- Indexes are created
- Foreign key constraints are intact
- No unintended table drops or column removals

## STEP 5: Seed Data Test (if --seed-data)

Test migration with realistic data to catch data-loss issues:

```bash
# 1. Reset to pre-migration state
alembic downgrade -1  # or equivalent

# 2. Seed test data
python -c "
from tests.factories import seed_test_data
seed_test_data(count=100)
"

# 3. Run migration forward with seeded data
alembic upgrade head

# 4. Verify data integrity
python -c "
from app.models import User, Order
assert User.query.count() == 100, 'Data lost during migration'
assert Order.query.filter(Order.user_id.isnot(None)).count() > 0, 'FK references broken'
print('Data integrity check: PASSED')
"
```

## STEP 6: Rollback Verification (if --rollback or always)

Test that the migration can be reversed:

```bash
# Alembic
alembic downgrade -1
echo $?  # Must be 0

# Django
python manage.py migrate <app_name> <previous_migration_number>

# Prisma (if using migrate reset)
npx prisma migrate reset --force
```

After rollback:
1. Verify schema matches pre-migration state
2. Verify no data was permanently lost (if seeded)
3. Verify application can still start and serve requests

```bash
# Compare rollback schema to original
pg_dump --schema-only -f rollback_schema.sql $DATABASE_URL
diff pre_migration_schema.sql rollback_schema.sql  # Should be empty
```

## STEP 7: Dangerous Operation Detection

Scan migration files for risky operations:

| Operation | Risk | Mitigation |
|-----------|------|------------|
| `DROP TABLE` | Data loss | Verify backup exists, add deprecation period |
| `DROP COLUMN` | Data loss | Verify column is unused (check queries) |
| `ALTER TYPE` | Downtime on large tables | Use concurrent operations or shadow columns |
| `NOT NULL` on existing column | Fails if NULLs exist | Add DEFAULT or backfill first |
| `RENAME TABLE/COLUMN` | Breaks application code | Verify all references updated |
| Raw SQL without transaction | Partial application risk | Wrap in transaction block |

```bash
# Scan migration files for dangerous operations
grep -rn -i "drop table\|drop column\|alter.*type\|not null" alembic/versions/ || echo "No dangerous operations found"
```

## STEP 7A: Real Database Testing (Testcontainers + Respawn)

In-memory database substitutes (H2, SQLite) are an anti-pattern for migration testing — they silently ignore constraints, partial indexes, and engine-specific SQL. Always test migrations against the real database engine.

### Testcontainers Setup

```python
# conftest.py — singleton container for test suite (starts once, reused)
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    """Real PostgreSQL container — starts once for entire test suite."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
def db_url(postgres):
    return postgres.get_connection_url()
```

```kotlin
// Kotlin/JVM — Testcontainers with Flyway
@Testcontainers
class MigrationTest {
    companion object {
        @Container
        val postgres = PostgreSQLContainer("postgres:16-alpine")
    }

    @Test
    fun `migrations apply cleanly`() {
        val flyway = Flyway.configure()
            .dataSource(postgres.jdbcUrl, postgres.username, postgres.password)
            .load()

        val result = flyway.migrate()
        assertThat(result.success).isTrue()
        assertThat(result.migrationsExecuted).isGreaterThan(0)
    }
}
```

### Respawn Pattern (Fast Data Reset)

Instead of recreating containers between tests (~15-30s each), use Respawn to truncate tables (~50ms):

```python
# Fast data reset between tests — truncate all tables, keep schema
@pytest.fixture(autouse=True)
async def reset_db(db_session):
    """Reset data between tests without recreating container."""
    yield
    # Truncate all user tables (preserve schema + migrations table)
    tables = await db_session.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
        "AND tablename NOT IN ('alembic_version', 'flyway_schema_history')"
    ))
    for (table,) in tables:
        await db_session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    await db_session.commit()
```

```csharp
// .NET — Respawn library (purpose-built for this pattern)
private static readonly Respawner _respawner = Respawner.CreateAsync(
    connectionString,
    new RespawnerOptions {
        TablesToIgnore = new[] { "__EFMigrationsHistory" }
    }
).Result;

[SetUp]
public async Task ResetDatabase() => await _respawner.ResetAsync(connectionString);
```

### Why Not In-Memory Databases

| Feature | PostgreSQL / MySQL | H2 / SQLite |
|---------|-------------------|-------------|
| Partial indexes | Supported | Silently ignored |
| Custom SQL functions | Works | Missing |
| JSON operators (`->`, `->>`) | Native | Partial or missing |
| Constraint semantics | Strict | Permissive |
| Transaction isolation levels | Full support | Limited |
| Concurrent access behavior | Realistic | Single-threaded |

A migration that "passes" on SQLite may fail on PostgreSQL in production. Always test against the real engine.

### Performance

| Approach | Startup | Per-Test Reset | Total (100 tests) |
|----------|---------|---------------|-------------------|
| New container per test | 15-30s | 0ms | ~25 minutes |
| Singleton + Respawn | 15-30s (once) | ~50ms | ~35 seconds |
| In-memory DB | 0ms | 0ms | ~10 seconds (but unreliable) |

## STEP 8: Report

```
Migration Verify: [PASSED / FAILED]
  Framework: Alembic (SQLAlchemy)
  Migration: abc123_add_orders_table
  Forward: PASSED (exit 0, schema validated)
  Rollback: PASSED (schema matches pre-migration)
  Data integrity: PASSED (100 records preserved)
  Dangerous ops: NONE detected

  Schema changes:
    + Table: orders (id, user_id, total, created_at)
    + Index: ix_orders_user_id
    + FK: orders.user_id → users.id
```

## RULES

- ALWAYS capture pre-migration schema before running any migration
- ALWAYS test rollback — irreversible migrations must be flagged explicitly
- NEVER run destructive migrations without verifying data backup
- Flag any migration that takes >10 seconds on test data — it will be worse in production
- If rollback fails, report as CRITICAL — the migration is not safe to deploy
