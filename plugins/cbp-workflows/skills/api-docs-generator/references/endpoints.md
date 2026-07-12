# Endpoints

### Users

#### Create User
`POST /users`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string (email) | Yes | User's email |
| name | string | Yes | Display name |

**Responses:**
| Status | Description |
|--------|-------------|
| 201 | User created |
| 409 | Email already registered |
| 422 | Validation error |

**Example:**
```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "Test User"}'
```
```

---

