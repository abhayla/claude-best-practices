---
name: fastapi-deploy
description: >
  Orchestrate backend deployment for FastAPI projects by running migrations, seeding data,
  restarting the server, and performing health checks. Use when deploying or updating a FastAPI service.
triggers:
  - deploy fastapi
  - deploy backend
  - restart fastapi server
  - run deploy
  - backend health check
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[--skip-seed] [--skip-migrate] [--port 8000]"
version: "1.1.0"
type: workflow
---

# Deploy Backend (FastAPI)

Orchestrates backend deployment steps with health verification.

**Scope:** Local/dev deployment orchestration. For migration authoring, use `/fastapi-db-migrate`. For post-migration verification, use `/db-migrate-verify`. For production deployment strategies (canary, blue-green), use `/deploy-strategy`.

**Arguments:** $ARGUMENTS

---

## STEP 1: Pre-flight Checks

```bash
cd backend && python --version
python -c "import sys; print('venv:', hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix)"
ls -la .env 2>/dev/null || echo "WARNING: .env not found"
```

If `.env` is missing, STOP and ask the user — deployment without config will fail silently.

## STEP 2: Run Migrations

**Skip if** `--skip-migrate` is in `$ARGUMENTS`.

```bash
cd backend && alembic current && alembic upgrade head
```

If migration fails, STOP and report the error. Do not proceed to seeding or server start with a broken schema.

## STEP 3: Seed Data

**Skip if** `--skip-seed` is in `$ARGUMENTS`.

```bash
cd backend && ls scripts/seed_*.py 2>/dev/null
```

If seed scripts are found, run each one:
```bash
for script in scripts/seed_*.py; do
  echo "Running: $script"
  python "$script" || echo "WARNING: $script failed"
done
```

If no seed scripts exist, skip this step silently.

## STEP 4: Start/Restart Server

Check if a server process is already running and stop it first:
```bash
# Check for existing uvicorn process on the target port
PORT=${PORT:-8000}
lsof -ti:$PORT 2>/dev/null && echo "Port $PORT in use — stopping existing process" && kill $(lsof -ti:$PORT)
```

Start the server in the background (NOT with `--reload` — that is for development, not deployment):
```bash
cd backend && nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2 > uvicorn.log 2>&1 &
echo "Server PID: $!"
sleep 2  # Allow startup time
```

## STEP 5: Health Check

```bash
PORT=${PORT:-8000}
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/docs)
echo "Health check: $HTTP_CODE"
```

If health check returns non-200:
1. Check `uvicorn.log` for errors: `tail -20 backend/uvicorn.log`
2. Report the failure with log output
3. If `--skip-migrate` was NOT set, suggest rolling back: `cd backend && alembic downgrade -1`

## Report

```
Deploy Summary:
  Migrations: <applied|skipped|failed>
  Seed data:  <N scripts run|skipped|none found>
  Server:     <running on port PORT (PID: N)|failed>
  Health:     <HTTP_CODE — OK|FAILED>
  URL:        http://localhost:PORT/docs
  Log:        backend/uvicorn.log
```

---

## CRITICAL RULES

- MUST verify health (Step 5) before reporting success — Why: a running process doesn't mean a working server
- MUST NOT use `--reload` in deployment — Why: reload is dev-only, blocks the shell, and restarts on file changes
- MUST stop on migration failure — Why: seeding or starting with a broken schema causes data corruption
- MUST check for existing process before starting — Why: port conflicts produce cryptic bind errors
- MUST report rollback path on failure — Why: a failed deploy must be reversible
