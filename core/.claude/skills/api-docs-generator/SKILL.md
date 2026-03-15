---
name: api-docs-generator
description: >
  Auto-generate OpenAPI/Swagger docs from code annotations. Supports FastAPI,
  Express/NestJS, Go, and manual spec writing. Validates spec against API tests,
  generates Redoc/Swagger UI, and produces API changelog.
triggers:
  - api docs
  - openapi
  - swagger
  - api documentation
  - generate api spec
  - api reference
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<project directory, framework name, or existing OpenAPI spec path>"
version: "1.0.0"
type: workflow
---

# API Docs Generator — OpenAPI from Code

Auto-generate, validate, and serve API documentation from code annotations.

**Input:** $ARGUMENTS

---

## STEP 1: Detect API Framework

Scan the project to automatically identify the API framework:

### 1.1 Automated Detection

Run these checks in order — use the first match:

```bash
# FastAPI (Python)
grep -rl "from fastapi" src/ app/ --include="*.py" 2>/dev/null && echo "FRAMEWORK=fastapi"

# NestJS (TypeScript)
grep -rl "@ApiTags\|@ApiProperty\|@nestjs/swagger" src/ --include="*.ts" 2>/dev/null && echo "FRAMEWORK=nestjs"

# Express (JavaScript/TypeScript)
grep -rl "express()\|app\.get(\|app\.post(" src/ --include="*.ts" --include="*.js" 2>/dev/null && echo "FRAMEWORK=express"

# Spring Boot (Java/Kotlin)
grep -rl "@RestController\|@GetMapping\|@PostMapping" src/ --include="*.kt" --include="*.java" 2>/dev/null && echo "FRAMEWORK=spring"

# Go (net/http, gin, chi, echo)
grep -rl "http\.HandleFunc\|gin\.Default\|chi\.NewRouter\|echo\.New" --include="*.go" 2>/dev/null && echo "FRAMEWORK=go"
```

If no framework detected, check if an `openapi.json` or `openapi.yaml` already exists in `docs/`. If so, use spec-first mode. Otherwise, report "No API framework detected — skipping API docs generation."

### 1.2 Detection Report

| Indicator | Framework | OpenAPI Support |
|-----------|-----------|----------------|
| `from fastapi import FastAPI` | FastAPI | Native — auto-generates at `/openapi.json` |
| `@ApiTags`, `@ApiProperty` | NestJS | Native via `@nestjs/swagger` |
| `app.get(`, `express()` | Express | Manual — needs swagger-jsdoc |
| `http.HandleFunc` or chi/gin/echo | Go | Manual — needs swaggo or similar |
| `@RestController`, `@GetMapping` | Spring Boot | Native via springdoc-openapi |
| No API framework | — | Write spec manually (spec-first) |

```markdown
## API Detection

| Check | Result |
|-------|--------|
| Framework | FastAPI |
| Existing spec | ✅ /openapi.json auto-generated |
| Annotations | Partial — response models missing on 3 endpoints |
| Current spec version | OpenAPI 3.1.0 |
```

---

## STEP 2: Generate or Extract OpenAPI Spec

### 2.1 FastAPI (Auto-Generated)

FastAPI generates OpenAPI natively. Ensure quality:

```python
# Verify all endpoints have proper annotations
from fastapi import FastAPI

app = FastAPI(
    title="<Project Name> API",
    version="1.0.0",
    description="<API description from PRD>",
)

# Every endpoint needs:
@app.post(
    "/users",
    response_model=UserResponse,          # ← Response schema
    status_code=201,                       # ← Correct status code
    summary="Create a new user",           # ← Short description
    description="Creates a user account...",# ← Detailed description
    tags=["Users"],                        # ← Grouping
    responses={                            # ← Error responses
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def create_user(user: UserCreate):
    ...
```

Extract the spec:
```bash
# Start the app and extract OpenAPI spec
curl -s http://localhost:8000/openapi.json | python -m json.tool > docs/openapi.json
```

### 2.2 Express + swagger-jsdoc

```javascript
// swagger.js
const swaggerJsdoc = require("swagger-jsdoc");

const options = {
  definition: {
    openapi: "3.1.0",
    info: {
      title: "<Project Name> API",
      version: "1.0.0",
      description: "<description>",
    },
    servers: [
      { url: "http://localhost:3000", description: "Development" },
    ],
  },
  apis: ["./src/routes/*.js"],
};

module.exports = swaggerJsdoc(options);
```

Add JSDoc annotations to routes:
```javascript
/**
 * @openapi
 * /users:
 *   post:
 *     summary: Create a new user
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UserCreate'
 *     responses:
 *       201:
 *         description: User created
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/UserResponse'
 *       409:
 *         description: Email already registered
 */
router.post("/users", createUser);
```

### 2.3 Go (swaggo)

```go
// @title           <Project Name> API
// @version         1.0.0
// @description     <description>
// @host            localhost:8000
// @BasePath        /api/v1

// @Summary      Create a new user
// @Tags         Users
// @Accept       json
// @Produce      json
// @Param        user body UserCreate true "User data"
// @Success      201 {object} UserResponse
// @Failure      409 {object} ErrorResponse
// @Router       /users [post]
func CreateUser(w http.ResponseWriter, r *http.Request) {
```

```bash
# Generate spec
swag init -g cmd/server/main.go -o docs/
```

### 2.4 Spec-First (Manual)

If no framework auto-generates, write the spec:

```yaml
# docs/openapi.yaml
openapi: "3.1.0"
info:
  title: "<Project Name> API"
  version: "1.0.0"
  description: "<from PRD>"

paths:
  /users:
    post:
      summary: Create a new user
      operationId: createUser
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreate"
      responses:
        "201":
          description: User created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UserResponse"
        "409":
          description: Email already registered

components:
  schemas:
    UserCreate:
      type: object
      required: [email, name]
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 1
          maxLength: 255
    UserResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
        name:
          type: string
        created_at:
          type: string
          format: date-time
```

---

## STEP 3: Validate Spec

### 3.1 Lint the OpenAPI Spec

```bash
# Install spectral (OpenAPI linter)
npm install -g @stoplight/spectral-cli

# Lint the spec
spectral lint docs/openapi.json --ruleset .spectral.yml
```

Default `.spectral.yml`:
```yaml
extends: ["spectral:oas"]
rules:
  operation-description: warn
  operation-operationId: error
  operation-tags: error
  oas3-api-servers: warn
```

### 3.2 Validate Against API Tests

Cross-reference the OpenAPI spec against existing API tests:

```markdown
## Spec vs Tests Alignment

| Endpoint | In Spec | In Tests | Match |
|----------|---------|----------|-------|
| POST /users | ✅ | ✅ (AT-001) | ✅ |
| GET /users/:id | ✅ | ✅ (AT-002) | ✅ |
| PUT /users/:id | ✅ | ❌ | ⚠️ Missing test |
| DELETE /users/:id | ❌ | ✅ (AT-005) | ⚠️ Missing from spec |
```

Flag:
- Endpoints in spec but not tested → **add test**
- Endpoints tested but not in spec → **add to spec**
- Response schemas in spec that differ from test assertions → **fix mismatch**

### 3.3 Schema Validation

Verify API schemas match database schemas (from `schema-designer`):

```markdown
| API Field | API Type | DB Column | DB Type | Match |
|-----------|----------|-----------|---------|-------|
| user.id | string (uuid) | users.id | UUID | ✅ |
| user.email | string (email) | users.email | VARCHAR(255) | ✅ |
| user.status | enum (active,inactive) | users.status | VARCHAR(20) | ⚠️ DB allows any string |
```

---

## STEP 4: Generate Human-Readable Docs

### 4.1 Redoc (Static HTML)

```bash
# Generate static HTML documentation
npx @redocly/cli build-docs docs/openapi.json -o docs/api-reference.html
```

### 4.2 Swagger UI (Interactive)

**FastAPI:** Built-in at `/docs` (Swagger UI) and `/redoc` (Redoc).

**Express:**
```javascript
const swaggerUi = require("swagger-ui-express");
const spec = require("./swagger");
app.use("/docs", swaggerUi.serve, swaggerUi.setup(spec));
```

### 4.3 Markdown API Reference

Generate a markdown API reference for the repo:

```markdown
# API Reference

## Authentication
All endpoints require `Authorization: Bearer <token>` header unless noted.

## Endpoints

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

## STEP 5: API Versioning Documentation

Document the API versioning strategy:

```markdown
## API Versioning

**Strategy:** URL path versioning (`/api/v1/`, `/api/v2/`)

### Version Lifecycle
| Version | Status | End of Life |
|---------|--------|-------------|
| v1 | Current | — |
| v2 | Planning | — |

### Breaking Change Policy
- Breaking changes require a new major version
- Non-breaking additions (new fields, new endpoints) are backward-compatible
- Deprecated endpoints are marked with `Sunset` header and 6-month notice
- Migration guides published for each major version bump

### Deprecation Headers
```
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Deprecation: true
Link: <https://docs.example.com/migration/v1-to-v2>; rel="sunset"
```
```

---

## STEP 6: CI Integration

Add API doc generation to CI:

```yaml
# .github/workflows/api-docs.yml
name: API Documentation
on:
  push:
    branches: [main]
    paths:
      - "src/routes/**"
      - "src/presentation/**"
      - "docs/openapi.*"

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate OpenAPI spec
        run: <framework-specific command>

      - name: Lint spec
        run: npx @stoplight/spectral-cli lint docs/openapi.json

      - name: Generate docs
        run: npx @redocly/cli build-docs docs/openapi.json -o docs/api-reference.html

      - name: Commit updated docs
        run: |
          git add docs/openapi.json docs/api-reference.html
          git diff --cached --quiet || git commit -m "docs: auto-update API documentation"
          git push
```

---

## STEP 7: Output Summary

```markdown
## API Documentation Summary

**Framework:** <detected>
**Spec format:** OpenAPI 3.1.0
**Endpoints documented:** <N>

### Generated Files
| File | Purpose |
|------|---------|
| `docs/openapi.json` | Machine-readable spec |
| `docs/api-reference.html` | Human-readable Redoc |
| `docs/API.md` | Markdown reference |

### Validation
| Check | Status |
|-------|--------|
| Spec lint | ✅ 0 errors, 2 warnings |
| Spec vs tests | ✅ All endpoints tested |
| Spec vs schema | ⚠️ 1 enum mismatch |

### Next Steps
- Fix enum mismatch (`user.status`)
- Add Swagger UI endpoint to dev server
- Set up CI auto-generation
```

---

## MUST DO

- Always detect the API framework before generating docs
- Always validate the spec with spectral (or equivalent linter)
- Always cross-reference spec against API tests
- Always generate both machine-readable (JSON/YAML) and human-readable docs
- Always include example requests with curl
- Always document authentication requirements
- Always document error responses (not just success)

## MUST NOT DO

- MUST NOT write specs manually when the framework auto-generates them
- MUST NOT skip spec validation — invalid specs break client code generators
- MUST NOT document internal/private endpoints in public-facing docs
- MUST NOT include secrets or real credentials in example requests
- MUST NOT generate docs without checking alignment with actual implementation

## See Also

- `/diataxis-docs` — After generating API docs, use this to place the API reference into the correct Diataxis category (`docs/reference/`)
- `/doc-structure-enforcer` — Enforces that generated API docs land in `docs/api/` when using pipeline stages
- `/changelog-contributing` — Generate a CHANGELOG.md alongside API docs to document endpoint changes over time
- `/doc-staleness` — Detect when API documentation has drifted from the actual implementation
- `/adr` — Record the decision to adopt a specific API documentation strategy
- `docs-manager` agent — Orchestrates documentation updates across the project, delegates API doc generation to this skill
