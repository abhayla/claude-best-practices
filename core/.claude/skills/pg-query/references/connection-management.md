# Connection Management

### Active Connections

```bash
psql "$DATABASE_URL" <<'SQL'
-- Current connections by state
SELECT state, count(*), max(now() - state_change) AS max_duration
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY count DESC;
SQL
```

### Long-Running Queries

```bash
psql "$DATABASE_URL" <<'SQL'
-- Queries running longer than 30 seconds
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       state, left(query, 100) AS query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - pg_stat_activity.query_start > interval '30 seconds'
ORDER BY duration DESC;
SQL
```

### Connection Limits

```bash
psql "$DATABASE_URL" <<'SQL'
SELECT
    (SELECT count(*) FROM pg_stat_activity) AS current_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections,
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') AS active_queries;
SQL
```

### Blocked Queries

```bash
psql "$DATABASE_URL" <<'SQL'
-- Queries blocked by locks
SELECT blocked.pid AS blocked_pid,
       blocked.query AS blocked_query,
       blocking.pid AS blocking_pid,
       blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid
JOIN pg_locks kl ON kl.locktype = bl.locktype
    AND kl.database IS NOT DISTINCT FROM bl.database
    AND kl.relation IS NOT DISTINCT FROM bl.relation
    AND kl.page IS NOT DISTINCT FROM bl.page
    AND kl.tuple IS NOT DISTINCT FROM bl.tuple
    AND kl.transactionid IS NOT DISTINCT FROM bl.transactionid
    AND kl.classid IS NOT DISTINCT FROM bl.classid
    AND kl.objid IS NOT DISTINCT FROM bl.objid
    AND kl.objsubid IS NOT DISTINCT FROM bl.objsubid
    AND kl.pid != bl.pid
    AND kl.granted
JOIN pg_stat_activity blocking ON blocking.pid = kl.pid
WHERE NOT bl.granted;
SQL
```

---

