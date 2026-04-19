---
globs: ["backend/app/models/**/*.py", "backend/app/db/**/*.py", "backend/alembic/**/*.py"]
description: Database and migration rules for FastAPI + SQLAlchemy + Alembic.
---

# Database Rules

## PostgreSQL + SQLAlchemy

- Model import rule: ensure all import locations are in sync (see fastapi-backend.md)
- Always generate Alembic migration after model changes
- Connection pool defaults: `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`
- `expire_on_commit=False` and `selectinload()` required for async

## Alembic Migrations

- Generate: `alembic revision --autogenerate -m "description"`
- Apply: `alembic upgrade head`
- Rollback one: `alembic downgrade -1`
- Check current: `alembic current`

## Patterns

- Use `@Upsert` (or INSERT ON CONFLICT) for insert-or-update operations
- Every type converter / custom type MUST have unit tests
- UUID comparisons must use consistent types
