---
name: fastapi-deploy
description: >
  Backend deployment orchestration for FastAPI projects. Runs migrations, seeds data,
  restarts server, and performs health checks.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[--skip-seed] [--skip-migrate] [--port 8000]"
version: "1.0.0"
type: workflow
---

# Deploy Backend (FastAPI)

Orchestrates backend deployment steps with health verification.

**Arguments:** $ARGUMENTS

---

## STEP 1: Pre-flight Checks

```bash
cd backend && python --version
python -c "import sys; print('venv:', hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix)"
ls -la .env 2>/dev/null || echo "WARNING: .env not found"
```

## STEP 2: Run Migrations (unless --skip-migrate)

```bash
cd backend && alembic current && alembic upgrade head
```

## STEP 3: Seed Data (unless --skip-seed)

Run any seed scripts in the project:
```bash
cd backend && ls scripts/seed_*.py 2>/dev/null
# Run each seed script found
```

## STEP 4: Start/Restart Server

```bash
cd backend && uvicorn app.main:app --reload --port ${PORT:-8000}
```

## STEP 5: Health Check

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT:-8000}/docs
curl -s http://localhost:${PORT:-8000}/openapi.json | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'Endpoints: {len(data.get(\"paths\", {}))}')
"
```

## Report

```
Deploy Complete:
  Migrations: applied
  Server: running on port {port}
  Health: {status}
  URL: http://localhost:{port}/docs
```
