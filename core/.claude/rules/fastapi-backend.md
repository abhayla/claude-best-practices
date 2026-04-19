---
globs: ["backend/**/*.py"]
description: FastAPI backend development rules and patterns.
---

# FastAPI Backend Rules

## Commands
- Always prefix with `PYTHONPATH=.` when running from `backend/`
- Clear stale cache: `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +`

## SQLAlchemy Async Patterns
- Use `selectinload()` for eager loading — `joinedload`/lazy raises `MissingGreenlet`
- `expire_on_commit=False` is required — removing it breaks post-commit attribute access
- Compare UUIDs consistently — `uuid.UUID` vs `String` mismatches cause 500 errors

## Adding Models

When adding a new SQLAlchemy model, ensure ALL import locations are updated:
1. Model definition file
2. Models `__init__.py` — re-export
3. Database init/create/drop functions — import in each
4. Test `conftest.py` — import so test DB creates the table
5. Generate Alembic migration

Missing any location causes silent test/migration failures.

## Services Pattern
- Services take `db: AsyncSession` as parameter (not creating own sessions)
- Services raise domain exceptions; routers map to `HTTPException`
- Never raise `HTTPException` inside a service

## FastAPI Anti-Patterns

**No blocking in async routes:**
- No `time.sleep()` — use `await asyncio.sleep()`
- No synchronous HTTP — use `httpx.AsyncClient`
- One blocking call stalls ALL concurrent requests

**No `__future__` annotations in routers:**
- `from __future__ import annotations` breaks `Annotated + Depends()` at runtime
- Safe in non-router files

## Rate Limiting
- Use `slowapi` with per-endpoint decorators
- Endpoints must have `request: Request` as first parameter
