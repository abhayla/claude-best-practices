# Todo API — Seed Requirement

Build a REST API for managing todo items with user authentication.

## Core Features

1. **User Registration & Login** — Users can register with email/password and receive a JWT token for authenticated requests.

2. **Todo CRUD** — Authenticated users can create, read, update, and delete their own todo items. Each todo has: title (required, max 200 chars), description (optional), due_date (optional), priority (low/medium/high), completed (boolean).

3. **Todo Filtering** — Users can filter their todos by: completed status, priority level, due date range. Support pagination (limit/offset).

## Non-Functional Requirements

- Response time < 200ms for all endpoints (p95)
- Input validation on all endpoints with clear error messages
- Rate limiting: 100 requests/minute per user
- Passwords hashed with bcrypt, never stored in plain text
- API documented with OpenAPI/Swagger

## Tech Stack

- Python 3.12+ with FastAPI
- PostgreSQL database
- SQLAlchemy ORM with Alembic migrations
- pytest for testing
