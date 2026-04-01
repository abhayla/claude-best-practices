# Todo API

A RESTful API for managing todo items with user authentication, built with FastAPI.

## Features
- User registration and JWT authentication
- CRUD operations for todo items
- Per-user todo isolation
- SQLite database with migrations

## Getting Started

### Prerequisites
- Python 3.12+
- pip

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running
```bash
uvicorn src.todo_api.main:app --reload
```

### Testing
```bash
python -m pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get JWT |
| GET | /todos | List user's todos |
| POST | /todos | Create a todo |
| PATCH | /todos/{id} | Update a todo |
| DELETE | /todos/{id} | Delete a todo |

## Architecture
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.
