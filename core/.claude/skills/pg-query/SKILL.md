---
name: pg-query
description: >
  PostgreSQL read-only query assistant: schema exploration, query execution with timeouts,
  EXPLAIN ANALYZE performance analysis, index and table statistics, connection diagnostics,
  and query optimization. Use for any PostgreSQL database investigation or troubleshooting.
triggers: "postgresql postgres pg database query schema explain sql"
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<sql-query or question about database schema/performance>"
version: "1.0.0"
type: reference
---

# PostgreSQL Read-Only Query Assistant

Execute read-only queries, explore schemas, analyze performance, and troubleshoot PostgreSQL databases.
Based on PostgreSQL best practices and the jawwadfirdousi/agent-skills repository.

**Request:** $ARGUMENTS

---

## CRITICAL SAFETY RULES

**ONLY the following operations are permitted:**

| Allowed | Examples |
|---------|---------|
| SELECT | `SELECT * FROM users LIMIT 10;` |
| SHOW | `SHOW search_path;` |
| EXPLAIN / EXPLAIN ANALYZE | `EXPLAIN ANALYZE SELECT ...;` |
| Meta-commands | `\dt`, `\d table`, `\di`, `\dv`, `\df`, `\dn`, `\du`, `\l` |
| pg_catalog / information_schema | `SELECT * FROM pg_stat_user_tables;` |

**NEVER execute these -- reject immediately and use SELECT-based alternatives instead:**

| Forbidden | Use Instead |
|-----------|-------------|
| INSERT | Read existing data with SELECT |
| UPDATE | SELECT the rows to inspect current values |
| DELETE | SELECT with WHERE to verify which rows match |
| DROP | `\d tablename` to inspect the object |
| ALTER | `\d tablename` to view current structure |
| TRUNCATE | `SELECT count(*) FROM table` to check row count |
| CREATE | `\dt` or `\dn` to list existing objects |
| GRANT / REVOKE | `\du` to inspect current roles |

**Before executing ANY query:**
1. Parse the SQL statement and verify it begins with SELECT, SHOW, EXPLAIN, or WITH (CTE leading to SELECT)
2. Verify no subqueries contain write operations
3. If the user requests a write operation, REFUSE and explain this is a read-only skill

---

## Connection Setup

### Environment Variable

The connection uses the `DATABASE_URL` environment variable:

```bash
# Format
DATABASE_URL="postgresql://user:password@host:port/dbname"

# Examples
DATABASE_URL="postgresql://readonly:secret@localhost:5432/myapp_dev"
DATABASE_URL="postgresql://readonly:secret@db.example.com:5432/myapp_staging?sslmode=require"
```

### Running Queries

```bash
# Single query
psql "$DATABASE_URL" -c "SELECT 1;"

# Query with formatted output
psql "$DATABASE_URL" -c "SELECT * FROM users LIMIT 5;" --expanded

# Query from stdin (for multi-line)
psql "$DATABASE_URL" <<'SQL'
SELECT u.id, u.email, count(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.email
ORDER BY order_count DESC
LIMIT 10;
SQL

# Tuples-only output (no headers/footers, useful for scripting)
psql "$DATABASE_URL" -t -A -c "SELECT count(*) FROM users;"

# CSV output
psql "$DATABASE_URL" -c "COPY (SELECT * FROM users LIMIT 100) TO STDOUT WITH CSV HEADER;"
```

### Verify Connection

```bash
psql "$DATABASE_URL" -c "SELECT current_database(), current_user, version();"
```

---

## Schema Exploration

### List Objects

```bash
# Tables
psql "$DATABASE_URL" -c "\dt"
psql "$DATABASE_URL" -c "\dt public.*"          # Specific schema

# Table structure (columns, types, constraints)
psql "$DATABASE_URL" -c "\d tablename"
psql "$DATABASE_URL" -c "\d+ tablename"         # Extended (storage, description)

# Indexes
psql "$DATABASE_URL" -c "\di"
psql "$DATABASE_URL" -c "\di+ tablename*"       # Indexes for specific table

# Views
psql "$DATABASE_URL" -c "\dv"

# Functions
psql "$DATABASE_URL" -c "\df"
psql "$DATABASE_URL" -c "\df+ function_name"    # Function source code

# Schemas
psql "$DATABASE_URL" -c "\dn"

# Roles
psql "$DATABASE_URL" -c "\du"

# Databases
psql "$DATABASE_URL" -c "\l"
```

### information_schema Queries

```bash
# All tables with row counts (estimated)
psql "$DATABASE_URL" <<'SQL'
SELECT schemaname, relname AS table_name,
       n_live_tup AS estimated_rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
SQL

# Columns for a specific table
psql "$DATABASE_URL" <<'SQL'
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
SQL

# Foreign key relationships
psql "$DATABASE_URL" <<'SQL'
SELECT
    tc.table_name, kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
SQL

# Table sizes
psql "$DATABASE_URL" <<'SQL'
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
       pg_size_pretty(pg_relation_size(relid)) AS data_size,
       pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
SQL
```

---

## Query Execution with Timeouts

Always set a statement timeout to prevent long-running queries from impacting the database:

```bash
# 5-second timeout (default recommendation)
psql "$DATABASE_URL" -c "SET statement_timeout = '5s'; SELECT * FROM large_table LIMIT 100;"

# 30-second timeout for complex analytics
psql "$DATABASE_URL" -c "SET statement_timeout = '30s'; SELECT ... ;"

# 60-second timeout for EXPLAIN ANALYZE on complex queries
psql "$DATABASE_URL" -c "SET statement_timeout = '60s'; EXPLAIN ANALYZE SELECT ... ;"
```

**Timeout guidelines:**

| Query Type | Recommended Timeout |
|------------|-------------------|
| Simple SELECT | 5s |
| JOINs / aggregations | 15s |
| EXPLAIN ANALYZE | 30-60s |
| Large table scans | 30s |
| Schema exploration (\dt, \d) | 5s |

---

## EXPLAIN ANALYZE for Performance Analysis

### Basic Usage

```bash
# EXPLAIN only (shows plan without executing)
psql "$DATABASE_URL" -c "EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';"

# EXPLAIN ANALYZE (executes the query, shows actual times)
psql "$DATABASE_URL" -c "SET statement_timeout = '30s'; EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';"

# Full detail with buffers and timing
psql "$DATABASE_URL" <<'SQL'
SET statement_timeout = '60s';
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM users WHERE email = 'test@example.com';
SQL

# JSON format (easier to parse programmatically)
psql "$DATABASE_URL" -c "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM users WHERE id = 1;"
```

### Reading Query Plans

| Node Type | Meaning | Performance |
|-----------|---------|-------------|
| **Seq Scan** | Full table scan | Slow on large tables -- consider adding an index |
| **Index Scan** | Uses index to find rows | Good for selective queries (few rows returned) |
| **Index Only Scan** | Answers from index alone | Best -- no table access needed |
| **Bitmap Index Scan** | Index scan batched into bitmap | Good for medium selectivity |
| **Nested Loop** | Row-by-row join | Best for small result sets or indexed inner table |
| **Hash Join** | Hash table join | Good for large unsorted datasets |
| **Merge Join** | Sorted merge join | Good when both sides are pre-sorted or indexed |
| **Sort** | Sorts result set | Check if an index could eliminate the sort |
| **Aggregate** | GROUP BY / count / sum | Normal for aggregation queries |

### Key Metrics to Check

- **actual time**: Time in ms for first row..last row. Compare with `estimated` cost.
- **rows**: Compare `Rows Planned` vs `Rows Actual`. Large differences indicate stale statistics -- run `ANALYZE tablename`.
- **Buffers shared hit vs read**: Hits are from cache, reads are from disk. High read count means data not cached.
- **loops**: Number of times the node executed. High loop count with Nested Loop may indicate a missing index.

### Red Flags in Query Plans

| Red Flag | What It Means | Action |
|----------|---------------|--------|
| Seq Scan on large table | Missing index or non-sargable WHERE | Add index on filtered column |
| Rows Planned: 1, Actual: 100000 | Stale statistics | Run `ANALYZE tablename` |
| Sort with high cost | Sorting without index | Add index matching ORDER BY |
| Nested Loop with high loops | Repeated scans of inner table | Add index on join column |
| Buffers: shared read >> shared hit | Data not in cache | Check shared_buffers setting |

---

## Common Query Patterns


**Read:** `references/common-query-patterns.md` for detailed common query patterns reference material.

## Index Analysis


**Read:** `references/index-analysis.md` for detailed index analysis reference material.

## Table Statistics

### Table Health Overview

```bash
psql "$DATABASE_URL" <<'SQL'
SELECT relname AS table_name,
       n_live_tup AS live_rows,
       n_dead_tup AS dead_rows,
       round(n_dead_tup::numeric / GREATEST(n_live_tup, 1) * 100, 1) AS dead_pct,
       last_vacuum,
       last_autovacuum,
       last_analyze,
       last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
SQL
```

### Table Bloat Detection

```bash
psql "$DATABASE_URL" <<'SQL'
-- Tables with high dead tuple ratio (need VACUUM)
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup::numeric / GREATEST(n_live_tup + n_dead_tup, 1) * 100, 1) AS bloat_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY bloat_pct DESC;
SQL
```

---

## Connection Management


**Read:** `references/connection-management.md` for detailed connection management reference material.

## Query Optimization Tips

### When to Add an Index

| Scenario | Index Type |
|----------|-----------|
| WHERE clause on a column | B-tree (default) |
| Exact match on low-cardinality | B-tree or Hash |
| LIKE 'prefix%' | B-tree |
| LIKE '%substring%' | pg_trgm GIN |
| Range queries (dates, numbers) | B-tree |
| JSON field queries | GIN |
| Full-text search | GIN with tsvector |
| Composite WHERE (a AND b) | Multi-column B-tree (most selective first) |

### Query Rewriting Patterns

| Slow Pattern | Faster Alternative |
|-------------|-------------------|
| `SELECT * FROM ...` | `SELECT col1, col2 FROM ...` (only needed columns) |
| `WHERE col LIKE '%value%'` | Use pg_trgm extension or full-text search |
| `WHERE func(col) = value` | Create expression index or rewrite to `WHERE col = inverse_func(value)` |
| `SELECT DISTINCT` on large set | Use `GROUP BY` or `EXISTS` subquery |
| `NOT IN (subquery)` | `NOT EXISTS (correlated subquery)` -- handles NULLs correctly |
| `ORDER BY random()` | `TABLESAMPLE BERNOULLI(1)` for sampling |
| `count(*)` on large table | `SELECT n_live_tup FROM pg_stat_user_tables WHERE relname = 'table'` for estimate |
| Correlated subquery in SELECT | Rewrite as JOIN |

---

## Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Slow queries | `EXPLAIN ANALYZE` the query | Add missing indexes; check for Seq Scans on large tables |
| Connection refused | `pg_isready -h host -p port` | Verify host/port; check `pg_hba.conf`; check firewall |
| Permission denied | `SELECT current_user, current_database();` | Verify user has SELECT grant; check schema permissions |
| Statement timeout | Query exceeds `statement_timeout` | Increase timeout; optimize query; add LIMIT |
| Too many connections | `SELECT count(*) FROM pg_stat_activity;` | Use connection pooling (PgBouncer); check for leaked connections |
| Stale statistics | Planned vs actual rows mismatch in EXPLAIN | Run `ANALYZE tablename` (requires write permission) |
| Table bloat (slow scans) | Check `n_dead_tup` in `pg_stat_user_tables` | Request VACUUM from DBA |
| Lock contention | Check `pg_locks` and `pg_stat_activity` | Identify blocking query; coordinate with DBA |
| Encoding / locale issues | `SHOW server_encoding;` | Ensure client encoding matches: `SET client_encoding = 'UTF8';` |

---

## Security Guardrails

1. **Environment targeting**: Connect ONLY to development or staging databases. NEVER run queries against production unless explicitly confirmed by the user. Ask which environment before connecting.
2. **Credentials**: NEVER log, print, or expose the `DATABASE_URL` or any credentials. Use the environment variable directly in `psql` commands.
3. **Read-only enforcement**: Even if the database user has write permissions, this skill MUST NOT execute write operations. The safety validation in this skill is the primary guardrail.
4. **Result set limits**: Always use `LIMIT` on SELECT queries against unknown tables. Start with `LIMIT 10` and increase only if needed.
5. **Sensitive data**: Be cautious with columns like `password`, `ssn`, `token`, `secret`, `credit_card`. Avoid selecting these columns -- use `SELECT id, email, created_at` instead of `SELECT *` on tables that may contain PII.

---

## Output Format

Present query results using the following conventions:

- **Small result sets** (< 20 rows): Show the full `psql` output as a formatted table
- **Large result sets**: Summarize key findings and show representative rows
- **EXPLAIN output**: Show the full plan and highlight the most expensive nodes
- **Schema exploration**: Present as a clean table with column names, types, and constraints
- **Statistics**: Summarize with commentary on what the numbers mean (e.g., "42% dead tuples indicates this table needs a VACUUM")
- **Errors**: Show the full error message and provide the matching troubleshooting entry

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/)
- [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/sql-explain.html)
- [pg_stat_user_tables](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ALL-TABLES-VIEW)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- [jawwadfirdousi/agent-skills](https://github.com/jawwadfirdousi/agent-skills) -- Inspiration for this skill
