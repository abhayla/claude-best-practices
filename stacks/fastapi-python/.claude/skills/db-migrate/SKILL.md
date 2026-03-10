---
name: db-migrate
description: >
  Database migration helper: generates Alembic migrations and auto-updates all 5 model
  import locations (3 postgres.py blocks, conftest.py, models/__init__.py). Use when
  adding new SQLAlchemy models, modifying existing models, or running migrations.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<model-name or 'run' or 'status'>"
disable-model-invocation: true
---

# Database Migration Helper

Automates Alembic migration creation and the error-prone 5-location model import update.

**Request:** $ARGUMENTS

---

## Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **new-model** | Model name provided (e.g., `Achievement`) | Create model file + update all 5 import locations + generate migration |
| **migrate** | `$ARGUMENTS` = "run" or "migrate" | Run `alembic upgrade head` |
| **status** | `$ARGUMENTS` = "status" | Show current migration status and model registry |
| **check** | `$ARGUMENTS` = "check" | Verify all 5 import locations are in sync |

---

## STEP 1: Determine Mode

Parse `$ARGUMENTS` to determine which mode to execute.

---

## STEP 2: For "new-model" Mode

### 2a. Create the Model File

Create `backend/app/models/{model_name_snake}.py` following existing patterns:

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base
import uuid

class ModelName(Base):
    __tablename__ = "table_name"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ... fields based on user requirements
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 2b. Update All 5 Import Locations

**This is the critical step that prevents import errors.**

1. **`backend/app/models/__init__.py`** — Add import and `__all__` entry:
   ```python
   from app.models.{snake_name} import {ModelName}
   ```

2. **`backend/app/db/postgres.py`** — Update ALL 3 import blocks:
   - `init_db()` function
   - `create_tables()` function
   - `drop_tables()` function

   Search for existing import patterns:
   ```bash
   cd backend && grep -n "from app.models" app/db/postgres.py
   ```
   Add the new import to each block.

3. **`backend/tests/conftest.py`** — Add import so SQLite test DB creates the table:
   ```bash
   cd backend && grep -n "from app.models" tests/conftest.py
   ```
   Add the new import alongside existing model imports.

### 2c. Verify All 5 Locations

Run the sync check:

```bash
cd backend && python -c "
from app.models import *
import app.db.postgres
import importlib
print('All model imports successful')
"
```

### 2d. Generate Alembic Migration

```bash
cd backend && alembic revision --autogenerate -m "add {model_name_snake} table"
```

### 2e. Run the Migration

```bash
cd backend && alembic upgrade head
```

### 2f. Verify

```bash
cd backend && PYTHONPATH=. python -c "
from app.db.postgres import engine
import asyncio
async def check():
    async with engine.begin() as conn:
        from sqlalchemy import text
        result = await conn.execute(text(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\"))
        tables = [r[0] for r in result.fetchall()]
        print(f'Tables ({len(tables)}): {sorted(tables)}')
asyncio.run(check())
"
```

**Output Required:**
```
Migration Complete:
- Model: {ModelName}
- File: backend/app/models/{snake_name}.py
- Migration: backend/alembic/versions/{hash}_{message}.py
- Import locations updated: 5/5
- Table created: {table_name}
```

---

## STEP 3: For "check" Mode — Sync Verification

Verify all 5 import locations reference the same set of models:

```bash
cd backend && echo "=== models/__init__.py ===" && grep "^from app.models" app/models/__init__.py | sort
echo "=== postgres.py (init_db) ===" && grep "from app.models" app/db/postgres.py | sort
echo "=== conftest.py ===" && grep "from app.models" tests/conftest.py | sort
```

Compare the lists and report any mismatches.

**Output Required:**
```
Sync Check:
- models/__init__.py: N models
- postgres.py init_db: N models
- postgres.py create_tables: N models
- postgres.py drop_tables: N models
- conftest.py: N models
- Status: IN_SYNC | OUT_OF_SYNC (list differences)
```

---

## STEP 4: For "run" / "migrate" Mode

```bash
cd backend && alembic upgrade head
```

Report success/failure with migration details.

---

## STEP 5: For "status" Mode

```bash
cd backend && alembic current && echo "---" && alembic history --verbose | head -30
```

---

## CRITICAL RULES

- NEVER skip any of the 5 import locations — missing one causes runtime errors
- ALWAYS run sync check after adding a model
- ALWAYS test with `PYTHONPATH=. pytest tests/conftest.py` to verify SQLite table creation
- Follow existing naming conventions (snake_case files, PascalCase classes)
