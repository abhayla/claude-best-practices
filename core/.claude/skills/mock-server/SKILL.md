---
name: mock-server
description: >
  Configure API mock and stub servers for development and testing.
  Covers MSW, WireMock, nock, VCR/cassette patterns, and json-server with
  selection guidance, test integration, and CI patterns.
  Use when setting up API mocks for local development or test isolation.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "<tool-or-question> [language/framework]"
version: "1.0.0"
triggers:
  - mock server
  - stub server
  - msw
  - wiremock
  - nock
  - mock api
  - api stub
---

# API Mock Server Reference

Guide to API mocking tools for development, testing, and CI.
Select the right tool, configure it, and integrate it into your test suite.

**Request:** $ARGUMENTS

---

## MSW (Mock Service Worker)

Browser and Node.js API mocking via network-level request interception.
MSW 2.x uses `http` and `HttpResponse` (not the legacy `rest` handlers).

### Handlers

```typescript
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/users", () => {
    return HttpResponse.json([{ id: 1, name: "Alice" }]);
  }),
  http.post("/api/users", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),
  http.get("/api/users/:id", ({ params }) => {
    return HttpResponse.json({ id: Number(params.id), name: "User" });
  }),
  // Error and network failure simulation
  http.get("/api/unstable", () => {
    return HttpResponse.json({ error: "Unavailable" }, { status: 503 });
  }),
  http.get("/api/timeout", () => HttpResponse.error()),
];
```

### Setup

```typescript
// Browser (service worker)
import { setupWorker } from "msw/browser";
export const worker = setupWorker(...handlers);
// Dev entry: await worker.start({ onUnhandledRequest: "warn" });

// Node.js (Vitest / Jest)
import { setupServer } from "msw/node";
export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Per-Test Overrides

```typescript
test("handles server error", async () => {
  server.use(
    http.get("/api/users", () => {
      return HttpResponse.json({ error: "fail" }, { status: 500 });
    })
  );
  // Cleaned up by afterEach -> resetHandlers()
});
```

### Playwright Integration

```typescript
// Playwright's native route mocking (or start MSW service worker via dev server)
await page.route("**/api/users", (route) =>
  route.fulfill({ json: [{ id: 1, name: "Alice" }] })
);
```

---

## WireMock

Docker-based HTTP mock server. Ideal for contract testing, multi-service
environments, and language-agnostic teams.

### Docker Quickstart

```bash
docker run -d --name wiremock -p 8080:8080 \
  -v ./stubs:/home/wiremock wiremock/wiremock:3.12.1
```

### JSON Stub Mappings

```json
{
  "request": {
    "method": "GET",
    "urlPathPattern": "/api/users"
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": [{ "id": 1, "name": "Alice" }]
  }
}
```

### Request Matching

```json
{
  "request": {
    "method": "POST",
    "urlPath": "/api/orders",
    "headers": { "Authorization": { "matches": "Bearer .+" } },
    "bodyPatterns": [{ "matchesJsonPath": "$.items[?(@.quantity > 0)]" }]
  },
  "response": { "status": 201, "jsonBody": { "orderId": "abc-123" } }
}
```

### Stateful Scenarios

```json
{
  "scenarioName": "order-lifecycle",
  "requiredScenarioState": "Started",
  "newScenarioState": "Order Created",
  "request": { "method": "POST", "urlPath": "/api/orders" },
  "response": { "status": 201, "jsonBody": { "id": "order-1" } }
}
```

### Record and Playback

```bash
docker run -d -p 8080:8080 wiremock/wiremock:3.12.1 \
  --proxy-all="https://api.example.com" --record-mappings
# Recorded stubs saved to mappings/ and __files/ in the container volume.
# Stop container, then replay stubs without the real backend.
```

---

## nock

Node.js HTTP interceptor. Intercepts outgoing `http`/`https` requests
at the native module level for unit and integration tests.

### Basic Usage

```javascript
const nock = require("nock");

const scope = nock("https://api.example.com")
  .get("/users")
  .reply(200, [{ id: 1, name: "Alice" }]);

const response = await fetch("https://api.example.com/users");
scope.done(); // Throws if the request was never made
```

### Request Matching

```javascript
// Headers
nock("https://api.example.com")
  .get("/secure")
  .matchHeader("Authorization", /^Bearer .+/)
  .reply(200, { data: "protected" });

// Request body
nock("https://api.example.com")
  .post("/users", { name: "Alice", email: "alice@example.com" })
  .reply(201, { id: 1 });

// Query parameters
nock("https://api.example.com")
  .get("/users").query({ page: 1, limit: 10 })
  .reply(200, { users: [], total: 0 });

// Fixture file response
nock("https://api.example.com")
  .get("/users")
  .replyWithFile(200, path.join(__dirname, "fixtures", "users.json"));
```

### Persistence and Cleanup

```javascript
nock("https://api.example.com").get("/health").reply(200).persist(); // multi-use
nock.cleanAll();                     // Remove all interceptors
nock.disableNetConnect();            // Fail on unmocked requests
nock.enableNetConnect("127.0.0.1");  // Allow localhost

// Recommended test setup:
beforeEach(() => { nock.disableNetConnect(); nock.enableNetConnect("127.0.0.1"); });
afterEach(() => { nock.cleanAll(); nock.enableNetConnect(); });
```

---

## VCR / Cassette Patterns

Record real HTTP interactions and replay them in tests. Eliminates manual
fixture maintenance while keeping tests deterministic.

### Python -- vcrpy

```python
import vcr

@vcr.use_cassette("tests/cassettes/user_list.yaml")
def test_list_users():
    response = requests.get("https://api.example.com/users")
    assert response.status_code == 200

@vcr.use_cassette(
    "tests/cassettes/create_user.yaml",
    record_mode="new_episodes",
    match_on=["method", "path", "body"],
    filter_headers=["Authorization"],
    filter_post_data_parameters=["password"],
)
def test_create_user():
    response = requests.post(
        "https://api.example.com/users",
        json={"name": "Alice", "password": "secret"},
    )
    assert response.status_code == 201
```

### Python -- responses

```python
import responses

@responses.activate
def test_external_api():
    responses.add(
        responses.GET,
        "https://api.example.com/users",
        json=[{"id": 1, "name": "Alice"}],
        status=200,
    )
    result = my_service.fetch_users()
    assert len(result) == 1
```

### Cassette Hygiene

- Commit cassettes to `tests/cassettes/`; re-record monthly or on API version bumps
- Filter sensitive data (`Authorization`, API keys, passwords) before recording
- Use `match_on` to control matching granularity (method, path, body, query)

---

## json-server

Instant REST API from a JSON file. Best for frontend prototyping.

```bash
npx json-server db.json --port 3001
```

```json
{
  "users": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "bob@example.com" }
  ],
  "posts": [
    { "id": 1, "title": "Hello World", "userId": 1 }
  ]
}
```

Auto-generated CRUD endpoints plus filtering (`?name=Alice`), sorting
(`?_sort=name&_order=asc`), pagination (`?_page=1&_limit=10`), and
relation expansion (`/posts?_expand=user`).

---

## When to Use What

| Criteria | MSW | WireMock | nock | VCR/cassettes | json-server |
|----------|-----|----------|------|---------------|-------------|
| **Language** | JS/TS | Any | Node.js | Python | Any (HTTP) |
| **Browser mocking** | Yes | No | No | No | No |
| **Node.js mocking** | Yes | Via HTTP | Yes | Yes | Via HTTP |
| **Protocol level** | Network intercept | HTTP server | Module intercept | Library intercept | HTTP server |
| **Setup effort** | Low | Medium | Low | Low | Very low |
| **Stateful scenarios** | Manual | Built-in | Manual | No | Limited |
| **Record and replay** | No | Yes | Recording mode | Yes (core) | No |
| **Contract testing** | No | Yes | No | No | No |
| **CI friendliness** | High (no ports) | High (Docker) | High (no ports) | High (no ports) | Medium |
| **Best for** | Frontend + API tests | Microservices | Node unit tests | Python integration | Prototyping |

### Decision Flowchart

1. **Browser-level mocking needed?** MSW with service worker
2. **Python project with external APIs?** vcrpy or responses
3. **Node.js unit tests intercepting HTTP?** nock
4. **Multi-service / polyglot / contract tests?** WireMock
5. **Quick REST prototype for frontend?** json-server
6. **Need to record real API responses?** VCR (Python) or WireMock record mode
7. **Playwright/Cypress E2E?** Framework-native route mocking or MSW browser

---

## Test Integration

### Setup / Teardown

**Per-test mocks** (preferred for isolation):

```typescript
// MSW
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```javascript
// nock
beforeEach(() => nock.disableNetConnect());
afterEach(() => { nock.cleanAll(); nock.enableNetConnect(); });
```

**Docker-based mocks:**

```bash
docker compose -f docker-compose.test.yml up -d wiremock
npm test
docker compose -f docker-compose.test.yml down
```

### Asserting Requests and Preventing Leaks

```javascript
// nock — scope.done() throws if interceptor was not consumed
const scope = nock("https://api.example.com").get("/users").reply(200, []);
await myFunction();
scope.done();

// MSW — capture with a spy pattern
let captured;
server.use(
  http.post("/api/users", async ({ request }) => {
    captured = await request.json();
    return HttpResponse.json({ id: 1 });
  })
);
await myFunction();
expect(captured).toEqual({ name: "Alice" });
```

Block unmocked requests: `nock.disableNetConnect()`, MSW `onUnhandledRequest: "error"`,
Python `@responses.activate` (raises `ConnectionError` on unmocked calls).

---

## CI Patterns

### Docker Compose

```yaml
# docker-compose.test.yml
services:
  wiremock:
    image: wiremock/wiremock:3.12.1
    ports: ["8080:8080"]
    volumes: ["./stubs:/home/wiremock"]
  app-tests:
    build: .
    depends_on:
      wiremock: { condition: service_healthy }
    environment:
      API_BASE_URL: http://wiremock:8080
```

### GitHub Actions

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      wiremock:
        image: wiremock/wiremock:3.12.1
        ports: ["8080:8080"]
        options: >-
          --health-cmd "curl -f http://localhost:8080/__admin/health"
          --health-interval 10s --health-timeout 5s --health-retries 3
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
        env:
          API_BASE_URL: http://localhost:8080
```

For shared mocks across multiple services, run a central WireMock with stubs
in a shared repository. Version stub mappings alongside API specs (OpenAPI)
and use the admin API (`/api/v2/mappings`) to load stubs dynamically.

---

## MUST DO

- **Isolate per test** -- reset handlers/interceptors in `afterEach` to prevent pollution
- **Block unmocked requests** -- use `disableNetConnect` (nock), `onUnhandledRequest: "error"` (MSW), or `@responses.activate` (Python)
- **Filter sensitive data** -- strip API keys, tokens, and passwords from cassettes before committing
- **Pin versions** -- use specific Docker image tags and package versions, not `latest`
- **Match realistically** -- mock responses must match the real API schema (status codes, headers, body shape)
- **Document limitations** -- note what mocks do NOT cover (rate limiting, auth flows, pagination edge cases)

## MUST NOT DO

- **MUST NOT leave persistent interceptors without cleanup** -- `.persist()` (nock) or long-lived handlers leak between tests; always call `cleanAll()` or `resetHandlers()`
- **MUST NOT mock in production code** -- mocks are test/dev dependencies only; use environment flags, never ship mock code
- **MUST NOT hardcode ports** -- use environment variables (`$MOCK_PORT`, `$API_BASE_URL`) for portability across local, CI, and Docker
- **MUST NOT skip schema validation** -- a mock returning a different shape than the real API creates false confidence
- **MUST NOT record cassettes with real credentials** -- always filter `Authorization`, `X-Api-Key`, `Set-Cookie` before committing
- **MUST NOT use `sleep()` to wait for mock servers** -- use health check endpoints or retry loops with timeouts instead
