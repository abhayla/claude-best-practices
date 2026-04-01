# Architecture

## Overview
The Todo API follows a layered architecture:

```
src/todo_api/
  main.py       — FastAPI app and startup
  models.py     — SQLAlchemy/dataclass models
  router.py     — API route handlers
```

## Data Flow
1. Request enters via FastAPI router
2. Route handler validates input
3. Database operation via models
4. Response returned as JSON

## Database
- SQLite for development
- PostgreSQL for production
- Migrations managed via SQL files in migrations/

## Authentication
- JWT tokens with HS256 signing
- Tokens expire after 24 hours
- Refresh tokens not implemented (v1.1)
