---
name: deploy
description: >
  Backend deployment orchestration: runs Alembic migrations, syncs YAML config to PostgreSQL,
  seeds reference data, restarts uvicorn, and performs health checks. Use when deploying
  backend changes to local or staging environment.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[--skip-seed] [--skip-migrate] [--port 8000]"
disable-model-invocation: true
---

# Deploy Backend

Orchestrates backend deployment steps in the correct order with health verification.

**Request:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip-seed` | flag | false | Skip seeding festivals/achievements/recipes |
| `skip-migrate` | flag | false | Skip Alembic migrations |
| `port` | int | 8000 | Uvicorn port |

---

## STEP 1: Pre-flight Checks

Verify prerequisites before deployment:

```bash
cd backend && python --version && echo "---"
# Check venv is active
python -c "import sys; print('venv:', hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix)"
# Check .env exists
ls -la .env 2>/dev/null || echo "WARNING: .env file not found"
# Check PostgreSQL connection
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('DATABASE_URL', 'NOT SET')
print(f'DATABASE_URL: {url[:30]}...' if len(url) > 30 else f'DATABASE_URL: {url}')
"
```

**Output:**
```
Pre-flight:
- Python: [version]
- Venv: active/inactive
- .env: found/missing
- DB URL: configured/missing
```

---

## STEP 2: Run Migrations (unless --skip-migrate)

```bash
cd backend && alembic current && echo "---" && alembic upgrade head
```

Report current revision and any new migrations applied.

---

## STEP 3: Sync Configuration

Sync YAML config files to PostgreSQL:

```bash
cd backend && PYTHONPATH=. python scripts/sync_config_postgres.py
```

---

## STEP 4: Seed Reference Data (unless --skip-seed)

Run seed scripts in order:

```bash
cd backend && PYTHONPATH=. python scripts/seed_festivals.py && \
PYTHONPATH=. python scripts/seed_achievements.py && \
PYTHONPATH=. python scripts/import_recipes_postgres.py
```

Report count of records seeded for each.

---

## STEP 5: Start/Restart Server

Check if uvicorn is already running and restart:

```bash
# Check for existing process
pgrep -f "uvicorn app.main:app" && echo "Server already running" || echo "No server running"
```

If running, inform user to restart manually. If not running:

```bash
cd backend && uvicorn app.main:app --reload --port ${PORT:-8000} &
echo "Server starting on port ${PORT:-8000}..."
sleep 3
```

---

## STEP 6: Health Check

Verify the server is responding:

```bash
# Wait for server readiness
sleep 2

# Check root endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT:-8000}/docs && echo " - Swagger UI OK"

# Check API health
curl -s http://localhost:${PORT:-8000}/api/v1/auth/health 2>/dev/null || echo "No health endpoint (expected)"

# Verify key endpoints are registered
curl -s http://localhost:${PORT:-8000}/openapi.json | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    paths = list(data.get('paths', {}).keys())
    print(f'Endpoints registered: {len(paths)}')
    print(f'Expected: ~41')
except:
    print('ERROR: Could not parse OpenAPI spec')
"
```

---

## Final Output

```
Deploy Complete:
- Migrations: applied (current: {revision})
- Config sync: done
- Seeds: festivals={n}, achievements={n}, recipes={n}
- Server: running on port {port}
- Health: Swagger UI {status}, {n} endpoints registered
- URL: http://localhost:{port}/docs
```

---

## ROLLBACK

If deployment fails at any step:

1. **Migration rollback:** `cd backend && alembic downgrade -1`
2. **Server issues:** Check logs in terminal output
3. **Seed errors:** Seeds are idempotent, safe to re-run
