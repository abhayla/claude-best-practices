---
name: db-migrate
description: >
  Stack-neutral database migration helper supporting Prisma, Knex, Django,
  TypeORM, Drizzle, SQLAlchemy/Alembic, and raw SQL. Detects the project's
  migration tool, generates migrations with UP + DOWN, and verifies safety.
  Use when creating, running, or troubleshooting database migrations.
triggers:
  - db migrate
  - database migration
  - create migration
  - run migration
  - rollback migration
  - migration status
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<migration description, or 'run' or 'rollback' or 'status'>"
version: "1.0.0"
type: workflow
---

# Database Migration Helper (Stack-Neutral)

Generate, run, and manage database migrations across any ORM or migration tool.

For schema design decisions, delegate to `/schema-designer`. For deployment ordering
of migrations in CI/CD pipelines, delegate to `/deploy-strategy`.

**Request:** $ARGUMENTS

---

## STEP 1: Detect ORM / Migration Tool

Scan the project to determine which migration tool is in use:

```bash
ls -la prisma/schema.prisma knexfile.js knexfile.ts manage.py \
  ormconfig.ts ormconfig.json tsconfig.json drizzle.config.ts \
  drizzle.config.json alembic.ini alembic/ migrations/ 2>/dev/null

# Also check for Android Room
grep -rl "androidx.room" build.gradle build.gradle.kts app/build.gradle app/build.gradle.kts 2>/dev/null
```

### Auto-Detection Table

| Indicator File | Tool | Ecosystem |
|---------------|------|-----------|
| `prisma/schema.prisma` | **Prisma** | Node.js / TypeScript |
| `knexfile.js` or `knexfile.ts` | **Knex** | Node.js |
| `manage.py` + `django` in requirements | **Django** | Python |
| `ormconfig.ts` or `data-source.ts` with `typeorm` | **TypeORM** | Node.js / TypeScript |
| `drizzle.config.ts` or `drizzle.config.json` | **Drizzle** | Node.js / TypeScript |
| `alembic.ini` or `alembic/` directory | **Alembic** (SQLAlchemy) | Python |
| `build.gradle*` with `androidx.room` dependency | **Room** | Android / Kotlin |
| `migrations/*.sql` with no ORM config | **Raw SQL** | Any |

If multiple tools are detected, ask the user which one to use.

If Alembic is detected in a FastAPI project, delegate to `/fastapi-db-migrate` for
FastAPI-specific model import management.

---

## STEP 2: Generate Migration

### Per-Tool Commands

#### Prisma

```bash
# Generate migration from schema changes
npx prisma migrate dev --name <migration_name>

# Generate migration without applying (preview)
npx prisma migrate dev --name <migration_name> --create-only
```

Prisma auto-generates DOWN logic internally. After generating, open the migration SQL
file at `prisma/migrations/<timestamp>_<name>/migration.sql` and verify the statements.

#### Knex

```bash
# Generate migration stub
npx knex migrate:make <migration_name>
```

Edit the generated file in `migrations/` to include both `exports.up` and `exports.down`:

```javascript
exports.up = function(knex) {
  return knex.schema.createTable('table_name', (table) => {
    table.uuid('id').primary().defaultTo(knex.fn.uuid());
    table.timestamps(true, true);
  });
};

exports.down = function(knex) {
  return knex.schema.dropTableIfExists('table_name');
};
```

#### Django

```bash
# Auto-generate migration from model changes
python manage.py makemigrations <app_name> --name <migration_name>

# Generate empty migration for custom SQL
python manage.py makemigrations <app_name> --empty --name <migration_name>
```

Django auto-generates reverse operations for most DDL. For custom `RunSQL`, always
provide the `reverse_sql` parameter:

```python
migrations.RunSQL(
    sql="ALTER TABLE myapp_table ADD COLUMN status VARCHAR(20) DEFAULT 'active';",
    reverse_sql="ALTER TABLE myapp_table DROP COLUMN status;",
)
```

#### TypeORM

```bash
# Auto-generate migration from entity changes
npx typeorm migration:generate -d src/data-source.ts src/migrations/<MigrationName>

# Generate empty migration
npx typeorm migration:create src/migrations/<MigrationName>
```

Verify the generated file includes both `up()` and `down()` methods with correct
reverse operations in `down()`.

#### Drizzle

```bash
# Generate migration from schema changes
npx drizzle-kit generate --name <migration_name>

# Push schema directly (dev only, no migration file)
npx drizzle-kit push
```

Review the generated SQL in `drizzle/` or the configured output directory. Write a
manual DOWN migration file alongside it if the project requires rollback support.

#### SQLAlchemy / Alembic

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "<migration_description>"

# Generate empty migration
alembic revision -m "<migration_description>"
```

Verify the generated `upgrade()` and `downgrade()` functions in `alembic/versions/`.

#### Android Room

Room uses `@Database(version = N)` annotations and `Migration(startVersion, endVersion)` classes.
There is no CLI command to auto-generate migrations — migrations are hand-written Kotlin/Java.

**Step 1: Update the `@Database` version:**

```kotlin
// app/src/main/java/com/example/data/AppDatabase.kt
@Database(
    entities = [UserEntity::class, ProjectEntity::class],
    version = 2,  // Increment from previous version
    exportSchema = true  // Required for migration testing
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun projectDao(): ProjectDao
}
```

**Step 2: Write the Migration class:**

```kotlin
// app/src/main/java/com/example/data/migrations/Migration1To2.kt
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // UP: Add new table
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id)")
    }
}
```

**Step 3: Register the migration in the database builder:**

```kotlin
Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
    .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
    .build()
```

**Step 4: Write a DOWN migration (for dev/test rollback only):**

Room does not natively support DOWN migrations. For development, create a helper:

```kotlin
// Only used in tests — never in production
fun rollbackMigration2To1(db: SupportSQLiteDatabase) {
    db.execSQL("DROP TABLE IF EXISTS projects")
}
```

**Auto-migrations (Room 2.4+):**

For simple additive changes (new column, new table), use Room's auto-migration:

```kotlin
@Database(
    version = 3,
    autoMigrations = [
        AutoMigration(from = 2, to = 3)  // Room generates the SQL
    ]
)
abstract class AppDatabase : RoomDatabase()
```

Auto-migration works for: adding columns (with default values), adding tables, adding indexes.
Auto-migration does NOT work for: renaming columns/tables, deleting columns, changing types.
For those, use `@RenameColumn`, `@DeleteColumn`, or `@RenameTable` annotations with an `AutoMigrationSpec`.

**Step 5: Test the migration:**

```kotlin
@RunWith(AndroidJUnit4::class)
class MigrationTest {
    @get:Rule
    val helper = MigrationTestHelper(
        InstrumentationRegistry.getInstrumentation(),
        AppDatabase::class.java,
    )

    @Test
    fun migrate1To2() {
        // Create database at version 1
        helper.createDatabase("test-db", 1).apply {
            execSQL("INSERT INTO users (id, email) VALUES ('u1', 'test@example.com')")
            close()
        }
        // Run migration to version 2
        val db = helper.runMigrationsAndValidate("test-db", 2, true, MIGRATION_1_2)
        // Verify data survived
        val cursor = db.query("SELECT * FROM users WHERE id = 'u1'")
        assertThat(cursor.count).isEqualTo(1)
        cursor.close()
    }
}
```

#### Raw SQL

Create two files per migration:

```
migrations/<timestamp>_<description>.up.sql
migrations/<timestamp>_<description>.down.sql
```

Use `IF NOT EXISTS` / `IF EXISTS` guards for idempotency:

```sql
-- UP
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DOWN
DROP TABLE IF EXISTS users;
```

---

## STEP 3: Verify UP + DOWN

After generating, verify both directions work:

### 3.1 Run UP

| Tool | Command |
|------|---------|
| Prisma | `npx prisma migrate dev` |
| Knex | `npx knex migrate:latest` |
| Django | `python manage.py migrate` |
| TypeORM | `npx typeorm migration:run -d src/data-source.ts` |
| Drizzle | `npx drizzle-kit push` |
| Alembic | `alembic upgrade head` |
| Room | `./gradlew :app:connectedDebugAndroidTest --tests *MigrationTest` |
| Raw SQL | `psql -f migrations/<file>.up.sql` (or equivalent) |

### 3.2 Run DOWN (rollback)

| Tool | Command |
|------|---------|
| Prisma | `npx prisma migrate reset` (resets all, use with caution) |
| Knex | `npx knex migrate:rollback` |
| Django | `python manage.py migrate <app_name> <previous_migration>` |
| TypeORM | `npx typeorm migration:revert -d src/data-source.ts` |
| Drizzle | Manual: apply the `.down.sql` file |
| Alembic | `alembic downgrade -1` |
| Room | Manual: call `rollbackMigrationNToM()` helper in test (Room has no native rollback) |
| Raw SQL | `psql -f migrations/<file>.down.sql` (or equivalent) |

### 3.3 Round-Trip Test

Run UP, then DOWN, then UP again. The final state MUST match a fresh UP:

```bash
# Example for Knex
npx knex migrate:latest && npx knex migrate:rollback && npx knex migrate:latest
```

If the round-trip fails, the DOWN migration is incomplete or incorrect.

---

## STEP 4: Check Migration Status

| Tool | Command |
|------|---------|
| Prisma | `npx prisma migrate status` |
| Knex | `npx knex migrate:status` |
| Django | `python manage.py showmigrations` |
| TypeORM | `npx typeorm migration:show -d src/data-source.ts` |
| Drizzle | `npx drizzle-kit check` |
| Alembic | `alembic current && alembic history --verbose` |
| Room | Check `@Database(version = N)` annotation + `room_master_table` in SQLite |
| Raw SQL | Check a `schema_migrations` table or equivalent tracking |

---

## STEP 5: Test Migration

1. **Run against a staging-size dataset** -- Migrations that complete in milliseconds on
   an empty dev database may lock tables for minutes on production data. Always test with
   realistic row counts.

2. **Measure execution time** -- For any migration touching tables with >10K rows,
   wrap in timing:
   ```bash
   time alembic upgrade head  # or equivalent
   ```

3. **Check for locks** -- DDL statements (ALTER TABLE, CREATE INDEX) acquire locks.
   Use `CREATE INDEX CONCURRENTLY` (PostgreSQL) or equivalent where available.

4. **Verify data integrity** -- After UP, run spot checks:
   ```sql
   SELECT COUNT(*) FROM <table>;
   SELECT * FROM <table> LIMIT 5;
   ```

---

## STEP 6: Document Migration

After successful verification, document the migration:

```markdown
**Migration:** <filename or identifier>
**Tool:** <Prisma / Knex / Django / TypeORM / Drizzle / Alembic / Raw SQL>
**Description:** <what this migration does>
**Backward compatible:** Yes / No
**Rollback safe:** Yes / No
**Estimated duration on prod data:** ~<N> seconds/minutes
**Requires code deploy first:** Yes / No
```

For deployment ordering (pre-deploy vs post-deploy migrations, expand-contract
sequencing), follow the guidance in `/deploy-strategy` Step 4.

---

## Safety Rules

1. **Always generate DOWN** -- Every migration MUST have a working reverse operation.
   Mark truly irreversible migrations (e.g., DROP COLUMN with data) explicitly.

2. **Separate DDL and DML** -- Schema changes (CREATE TABLE, ALTER TABLE) and data
   changes (UPDATE, INSERT backfills) MUST be in separate migration files. Data
   migrations on large tables can hold locks and should run independently.

3. **Test on staging-size data** -- Never assume a migration is safe based on an
   empty database. Test with a representative dataset before applying to production.

4. **Idempotent migrations** -- Use `IF NOT EXISTS`, `IF EXISTS`, and conditional
   checks so that re-running a migration does not fail.

5. **No column renames in one step** -- Add the new column, migrate data, update code,
   then drop the old column in a later migration. See `/deploy-strategy` for the
   expand-contract pattern.

6. **Lock-safe index creation** -- Use `CREATE INDEX CONCURRENTLY` on PostgreSQL or
   equivalent non-blocking index creation where supported.

---

## MUST DO

- Always detect the migration tool before generating commands -- never assume
- Always verify both UP and DOWN migrations execute without errors
- Always run the round-trip test (UP, DOWN, UP) for new migrations
- Always separate DDL and DML into distinct migration files
- Always document backward compatibility and rollback safety for each migration
- Always delegate schema design decisions to `/schema-designer`
- Always delegate deployment ordering to `/deploy-strategy` for CI/CD integration
- Always test migrations against a staging-size dataset before production

## MUST NOT DO

- MUST NOT generate migrations without a working DOWN operation -- use manual
  reverse SQL if the tool does not auto-generate it
- MUST NOT combine schema changes and data backfills in a single migration file
- MUST NOT rename or change column types in a single migration -- use the
  expand-contract pattern across multiple migrations instead
- MUST NOT run migrations directly on production without testing on staging first
- MUST NOT skip the round-trip verification (UP, DOWN, UP) for new migrations
- MUST NOT assume PostgreSQL -- detect the database engine from the project config
- MUST NOT duplicate Alembic-specific FastAPI workflows that `/fastapi-db-migrate`
  already handles -- delegate to it when Alembic + FastAPI is detected
