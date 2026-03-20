# Index Analysis

### Index Usage Statistics

```bash
psql "$DATABASE_URL" <<'SQL'
-- Index usage: which indexes are being used
SELECT schemaname, relname AS table_name, indexrelname AS index_name,
       idx_scan AS times_used, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
SQL
```

### Unused Indexes

```bash
psql "$DATABASE_URL" <<'SQL'
-- Indexes with zero scans (candidates for removal)
SELECT schemaname, relname AS table_name, indexrelname AS index_name,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
SQL
```

### Missing Index Detection

```bash
psql "$DATABASE_URL" <<'SQL'
-- Tables with high sequential scan counts (may need indexes)
SELECT schemaname, relname AS table_name,
       seq_scan, seq_tup_read,
       idx_scan, n_live_tup,
       round(seq_tup_read::numeric / GREATEST(seq_scan, 1), 0) AS avg_rows_per_seq_scan
FROM pg_stat_user_tables
WHERE seq_scan > 100
  AND n_live_tup > 10000
ORDER BY seq_tup_read DESC;
SQL
```

---

