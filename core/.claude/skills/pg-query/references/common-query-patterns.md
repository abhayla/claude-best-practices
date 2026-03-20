# Common Query Patterns

### Aggregations

```sql
-- Count with grouping
SELECT status, count(*) FROM orders GROUP BY status ORDER BY count DESC;

-- Date-based aggregation
SELECT date_trunc('day', created_at) AS day, count(*)
FROM events
GROUP BY day ORDER BY day DESC LIMIT 30;

-- Multiple aggregates
SELECT
    count(*) AS total,
    count(*) FILTER (WHERE status = 'active') AS active,
    avg(amount) AS avg_amount,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time) AS p95
FROM requests
WHERE created_at > now() - interval '1 hour';
```

### Joins

```sql
-- INNER JOIN with aggregation
SELECT u.email, count(o.id) AS order_count, sum(o.total) AS total_spent
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.created_at > now() - interval '30 days'
GROUP BY u.email
ORDER BY total_spent DESC LIMIT 20;

-- LEFT JOIN to find orphans
SELECT u.id, u.email
FROM users u
LEFT JOIN profiles p ON p.user_id = u.id
WHERE p.id IS NULL;
```

### Window Functions

```sql
-- Running total
SELECT date, revenue,
       sum(revenue) OVER (ORDER BY date) AS running_total
FROM daily_revenue;

-- Rank within groups
SELECT department, employee, salary,
       rank() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;

-- Lag/Lead comparison
SELECT date, metric_value,
       metric_value - lag(metric_value) OVER (ORDER BY date) AS change
FROM daily_metrics;
```

### Common Table Expressions (CTEs)

```sql
-- Readable multi-step queries
WITH active_users AS (
    SELECT user_id, count(*) AS action_count
    FROM user_actions
    WHERE created_at > now() - interval '7 days'
    GROUP BY user_id
    HAVING count(*) > 10
),
user_details AS (
    SELECT u.id, u.email, u.created_at, au.action_count
    FROM users u
    JOIN active_users au ON au.user_id = u.id
)
SELECT * FROM user_details ORDER BY action_count DESC LIMIT 50;
```

---

