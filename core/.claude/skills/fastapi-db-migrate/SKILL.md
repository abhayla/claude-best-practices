---
name: fastapi-db-migrate
description: >
  Database migration helper for FastAPI + Alembic projects. Generates migrations and
  auto-updates model import locations. Use when adding or modifying SQLAlchemy models.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<model-name or 'run' or 'status' or 'check'>"
version: "1.0.1"
type: workflow
---

# Database Migration Helper (FastAPI + Alembic)

Automates Alembic migration creation and model import location updates.

**Request:** $ARGUMENTS

---

## Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **new-model** | Model name provided | Create model file + update import locations + generate migration |
| **migrate** | "run" or "migrate" | Run `alembic upgrade head` |
| **status** | "status" | Show current migration status |
| **check** | "check" | Verify all import locations are in sync |

---

## STEP 1: New Model Mode

### 1. Create the Model File

Create `backend/app/models/{model_name_snake}.py` following existing patterns:

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class ModelName(Base):
    __tablename__ = "table_name"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 2. Update Import Locations

Find all locations where models are imported and add the new one:

```bash
cd backend && grep -rn "from app.models" app/db/ app/models/__init__.py tests/conftest.py
```

Update each location to include the new model import.

### 3. Generate Migration

```bash
cd backend && alembic revision --autogenerate -m "add {model_name} table"
```

### 4. Run Migration

```bash
cd backend && alembic upgrade head
```

### 5. Verify

```bash
cd backend && PYTHONPATH=. python -c "from app.models import *; print('All imports OK')"
```

---

## STEP 2: Check Mode

Compare model imports across all required locations and report mismatches.

## STEP 3: Status Mode

```bash
cd backend && alembic current && alembic history --verbose | head -20
```

---

## CRITICAL RULES

- Never skip any import location — missing ones cause silent failures
- Always run sync check after adding a model
- Follow existing naming conventions (snake_case files, PascalCase classes)
