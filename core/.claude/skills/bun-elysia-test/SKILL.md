---
name: bun-elysia-test
description: >
  Run and validate tests for Bun + Elysia applications covering endpoints,
  plugins, and WebSocket handlers. Detects project structure, executes tests
  via `bun test`, and writes structured JSON results. Use when testing Bun + Elysia
  endpoints or when test failures need automated diagnosis.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<test-scope> [--endpoint|--plugin|--websocket]"
version: "1.1.0"
---

# Bun + Elysia Test Workflow

Test Bun + Elysia applications end-to-end: endpoint routes, plugins, WebSocket
handlers, and mocked dependencies. Outputs structured results as JSON.

**Constraint**: Never install global packages. Never modify production source
files. All test artifacts go to `test-results/`.

---

## STEP 1: Detect Bun Project

Confirm the project uses Bun and Elysia before proceeding.

1. Search for `bunfig.toml` or `bun.lockb` at the project root:

```bash
ls bunfig.toml bun.lockb 2>/dev/null
```

2. Verify Elysia is listed in `package.json` dependencies:

```bash
grep -q '"elysia"' package.json && echo "elysia found"
```

3. If neither Bun marker nor Elysia dependency is found, abort with a clear
   message: "No Bun + Elysia project detected."

4. Check that `@elysiajs/eden` is available (needed for STEP 3). If missing,
   suggest:

```bash
bun add -d @elysiajs/eden
```

---

## STEP 2: Write Tests Using `bun:test` Patterns

Bun ships a built-in test runner. Use its native API for all test files.

### Basic structure

```ts
import { describe, it, expect, beforeAll, afterAll } from "bun:test";

describe("<your-module>", () => {
  beforeAll(() => {
    // setup: start server, seed DB, etc.
  });

  afterAll(() => {
    // teardown: stop server, clean up
  });

  it("should <expected-behavior>", () => {
    expect(actual).toBe(expected);
  });
});
```

### Assertion cheat-sheet

| Assertion | Use for |
|---|---|
| `expect(v).toBe(x)` | Primitive equality |
| `expect(v).toEqual(x)` | Deep object equality |
| `expect(v).toContain(x)` | Array/string inclusion |
| `expect(v).toThrow()` | Error throwing |
| `expect(v).toBeNull()` | Null check |
| `expect(v).toBeDefined()` | Existence check |

Place test files next to source as `<name>.test.ts` or under a `__tests__/`
directory. Bun discovers `*.test.ts` and `*.test.tsx` automatically.

---

## STEP 3: Test Elysia Endpoints with Eden Treaty

Use the `eden` treaty client for type-safe endpoint testing without raw HTTP.

```ts
import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { Elysia } from "elysia";
import { treaty } from "@elysiajs/eden";

const app = new Elysia()
  .get("/health", () => ({ status: "ok" }))
  .post("/<your-endpoint>", ({ body }) => ({ received: body }));

const api = treaty(app);

describe("<your-endpoint> routes", () => {
  it("GET /health returns ok", async () => {
    const { data, status } = await api.health.get();
    expect(status).toBe(200);
    expect(data).toEqual({ status: "ok" });
  });

  it("POST /<your-endpoint> accepts body", async () => {
    const { data, status } = await api["<your-endpoint>"].post({
      key: "value",
    });
    expect(status).toBe(200);
    expect(data?.received).toEqual({ key: "value" });
  });

  it("returns 422 on invalid input", async () => {
    const { status } = await api["<your-endpoint>"].post(null as any);
    expect(status).toBe(422);
  });
});
```

### Route parameter testing

```ts
// For routes like /items/:id
const { data } = await api.items({ id: "123" }).get();
expect(data?.id).toBe("123");
```

---

## STEP 4: Test Plugins (Lifecycle Hooks, Decorators)

Elysia plugins extend the app via lifecycle hooks and decorators. Test them
in isolation by mounting on a minimal Elysia instance.

```ts
import { describe, it, expect } from "bun:test";
import { Elysia } from "elysia";
import { treaty } from "@elysiajs/eden";
import { <yourPlugin> } from "<your-plugin-path>";

describe("<your-plugin> plugin", () => {
  const app = new Elysia()
    .use(<yourPlugin>())
    .get("/test-decorator", ({ <decoratedProperty> }) => ({
      value: <decoratedProperty>,
    }));

  const api = treaty(app);

  it("registers decorator on the context", async () => {
    const { data } = await api["test-decorator"].get();
    expect(data?.value).toBeDefined();
  });

  it("onBeforeHandle hook runs before route", async () => {
    // If the plugin adds an auth guard, test that unauthorized calls fail
    const { status } = await api["test-decorator"].get();
    expect(status).not.toBe(401);
  });
});
```

### Lifecycle hooks to verify

| Hook | What to test |
|---|---|
| `onBeforeHandle` | Request rejection / transformation before handler |
| `onAfterHandle` | Response transformation after handler |
| `onError` | Custom error formatting |
| `onRequest` | Logging, rate limiting side-effects |
| `derive` / `resolve` | Decorated context properties are present |

---

## STEP 5: Test WebSocket Handlers

Elysia supports WebSocket via `.ws()`. Test message exchange and lifecycle
events.

```ts
import { describe, it, expect } from "bun:test";
import { Elysia } from "elysia";

describe("<your-websocket> WebSocket", () => {
  let server: ReturnType<Elysia["listen"]>;
  let port: number;

  const app = new Elysia().ws("/<your-ws-path>", {
    message(ws, message) {
      ws.send({ echo: message });
    },
    open(ws) {
      ws.send({ event: "connected" });
    },
  });

  it("connects and receives open event", async () => {
    server = app.listen(0);
    port = server.port;

    const ws = new WebSocket(`ws://localhost:${port}/<your-ws-path>`);
    const messages: any[] = [];

    ws.onmessage = (ev) => messages.push(JSON.parse(ev.data));

    await new Promise<void>((resolve) => {
      ws.onopen = () => resolve();
    });

    // Wait for the open event message
    await Bun.sleep(50);
    expect(messages).toContainEqual({ event: "connected" });

    ws.close();
    server.stop();
  });

  it("echoes messages back", async () => {
    server = app.listen(0);
    port = server.port;

    const ws = new WebSocket(`ws://localhost:${port}/<your-ws-path>`);
    const messages: any[] = [];

    ws.onmessage = (ev) => messages.push(JSON.parse(ev.data));

    await new Promise<void>((resolve) => {
      ws.onopen = () => resolve();
    });

    ws.send(JSON.stringify("hello"));
    await Bun.sleep(50);

    expect(messages).toContainEqual({ echo: "hello" });

    ws.close();
    server.stop();
  });
});
```

Use `app.listen(0)` to bind an ephemeral port so tests never collide.

---

## STEP 6: Mock Dependencies with `bun:test` Spy and Mock

### Spy on functions

```ts
import { spyOn, expect, it } from "bun:test";
import * as db from "<your-db-module>";

it("calls the database layer", async () => {
  const spy = spyOn(db, "findById").mockResolvedValueOnce({ id: "1" });

  // ...invoke the route or function under test...

  expect(spy).toHaveBeenCalledWith("1");
  spy.mockRestore();
});
```

### Mock entire modules

```ts
import { mock } from "bun:test";

mock.module("<your-external-service>", () => ({
  fetchData: () => Promise.resolve({ mocked: true }),
}));

// Subsequent imports of <your-external-service> get the mock
```

### When to mock

| Scenario | Approach |
|---|---|
| External HTTP APIs | `mock.module` the client wrapper |
| Database calls | `spyOn` the repository/query functions |
| Environment config | Set `process.env` in `beforeAll`, restore in `afterAll` |
| Time-sensitive logic | Use `mock` for `Date.now` or timers |

---

## STEP 7: Run Tests and Collect Results

Execute the test suite with Bun's built-in runner.

### Run all tests

```bash
bun test
```

### Run scoped tests

```bash
# By file pattern
bun test <test-scope>

# By test name
bun test --test-name-pattern "<pattern>"
```

### Collect machine-readable output

```bash
bun test --reporter=json 2>&1 | tee test-results/raw-output.json
```

If `--reporter=json` is not available in the installed Bun version, parse the
default output and construct the JSON manually in STEP 8.

---

## STEP 8: Write Structured JSON Output

Write results to `test-results/bun-elysia-test.json` with this schema:

```json
{
  "tool": "bun-elysia-test",
  "timestamp": "<ISO-8601>",
  "scope": "<test-scope-argument>",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "duration_ms": 0
  },
  "suites": [
    {
      "name": "<describe-block-name>",
      "tests": [
        {
          "name": "<it-block-name>",
          "status": "passed | failed | skipped",
          "duration_ms": 0,
          "error": null
        }
      ]
    }
  ]
}
```

Create the `test-results/` directory if it does not exist:

```bash
mkdir -p test-results
```

---

## STEP 9: Auto-Fix and Learn (On Failure Only)

If tests failed in STEP 7, automatically invoke the fix-and-learn pipeline. Do NOT just report failures — fix them.

### 9a. Invoke Fix-Loop

```
Skill("fix-loop", args="<failure_output>\n\nretest_command: bun test {test_scope}")
```

This iterates: analyze → fix → retest until green (max 5 iterations).

### 9b. Capture Learnings (On Fix Success)

If `/fix-loop` reports `result: PASSED` or `result: FIXED`:

```
Skill("learn-n-improve", args="session")
```

### 9c. Escalation (On Fix Failure)

If `/fix-loop` exhausts 5 iterations without success:
- Report the failure to the user
- Suggest `/systematic-debugging` for deeper investigation
- Do NOT silently continue

### Skip Conditions

Do NOT auto-invoke fix-loop if:
- Bun project was not detected (STEP 1 failed)
- The failure is an environment error (Bun not installed, missing dependencies)

---

## CRITICAL RULES

### MUST DO

- Detect Bun (`bunfig.toml` or `bun.lockb`) before running any test command.
- Invoke `/fix-loop` on test failure — do not just report failures.
- Use `app.listen(0)` for ephemeral ports in WebSocket and integration tests.
- Restore every spy and mock after use (`spy.mockRestore()`, cleanup in `afterAll`).
- Write `test-results/bun-elysia-test.json` on every run, even if all tests pass.
- Use `@elysiajs/eden` treaty for endpoint testing instead of raw `fetch`.
- Keep test files co-located or in `__tests__/` — never place them in `src/`.

### MUST NOT DO

- Do not install packages globally (`bun add -g`).
- Do not modify production source files during testing.
- Do not hardcode ports — always use ephemeral port 0.
- Do not leave test servers running — call `server.stop()` in `afterAll` or
  after each test.
- Do not skip WebSocket cleanup — always call `ws.close()` before stopping
  the server.
- Do not use `node` or `npx` to run tests — use `bun test` exclusively.
