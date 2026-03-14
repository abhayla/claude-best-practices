---
name: hono-backend
description: >
  Hono web framework patterns for TypeScript backends on Node.js, Bun, Deno, or Cloudflare Workers.
  Use when building APIs, middleware, or server-side logic with Hono.
allowed-tools: "Read Grep Glob"
argument-hint: "[route|middleware|auth|validation]"
version: "1.0.0"
type: reference
triggers: hono, hono-backend
---

# Hono Backend Reference

Hono web framework for TypeScript backends across runtimes (Node.js, Bun, Deno, Cloudflare Workers).

## Project Setup

### Node.js

```bash
npm create hono@latest my-app -- --template nodejs
```

```typescript
// src/index.ts
import { serve } from "@hono/node-server";
import { Hono } from "hono";

const app = new Hono();
app.get("/", (c) => c.json({ message: "Hello" }));

serve({ fetch: app.fetch, port: 3000 });
```

### Bun

```typescript
// src/index.ts
import { Hono } from "hono";

const app = new Hono();
app.get("/", (c) => c.json({ message: "Hello" }));

export default { port: 3000, fetch: app.fetch };
```

## Routing

### Basic Routes

```typescript
const app = new Hono();

app.get("/users", (c) => c.json(users));
app.get("/users/:id", (c) => {
  const id = c.req.param("id");
  return c.json({ id });
});
app.post("/users", async (c) => {
  const body = await c.req.json();
  return c.json(body, 201);
});
app.put("/users/:id", async (c) => { /* ... */ });
app.delete("/users/:id", (c) => c.body(null, 204));
```

### Route Groups

```typescript
// routes/users.ts
import { Hono } from "hono";

const users = new Hono();

users.get("/", (c) => c.json([]));
users.get("/:id", (c) => c.json({ id: c.req.param("id") }));
users.post("/", async (c) => { /* ... */ });

export default users;

// src/index.ts
import users from "./routes/users";
import posts from "./routes/posts";

const app = new Hono();
app.route("/api/users", users);
app.route("/api/posts", posts);
```

### Route with Query Parameters

```typescript
app.get("/search", (c) => {
  const q = c.req.query("q");           // single param
  const page = c.req.query("page");
  const tags = c.req.queries("tag");     // multiple: ?tag=a&tag=b
  return c.json({ q, page, tags });
});
```

## Middleware

### Built-in Middleware

```typescript
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { secureHeaders } from "hono/secure-headers";
import { compress } from "hono/compress";
import { etag } from "hono/etag";
import { timing } from "hono/timing";

const app = new Hono();

app.use("*", logger());
app.use("*", secureHeaders());
app.use("*", compress());
app.use("*", etag());
app.use("*", timing());
app.use("/api/*", cors({
  origin: ["http://localhost:5173"],
  credentials: true,
}));
```

### Custom Middleware

```typescript
import { createMiddleware } from "hono/factory";

const authMiddleware = createMiddleware<{
  Variables: { userId: string };
}>(async (c, next) => {
  const token = c.req.header("Authorization")?.replace("Bearer ", "");
  if (!token) return c.json({ error: "Unauthorized" }, 401);

  try {
    const decoded = await verifyToken(token);
    c.set("userId", decoded.sub);
    await next();
  } catch {
    return c.json({ error: "Invalid token" }, 401);
  }
});

// Apply to specific routes
app.use("/api/protected/*", authMiddleware);

// Access in handlers
app.get("/api/protected/me", (c) => {
  const userId = c.get("userId");
  return c.json({ userId });
});
```

## Validation with Zod

```typescript
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(255),
});

const idParamSchema = z.object({
  id: z.string().uuid(),
});

app.post(
  "/users",
  zValidator("json", createUserSchema),
  async (c) => {
    const data = c.req.valid("json");   // typed as { email: string, name: string }
    return c.json(data, 201);
  }
);

app.get(
  "/users/:id",
  zValidator("param", idParamSchema),
  (c) => {
    const { id } = c.req.valid("param");
    return c.json({ id });
  }
);

// Query validation
const searchSchema = z.object({
  q: z.string().optional(),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

app.get("/search", zValidator("query", searchSchema), (c) => {
  const { q, page, limit } = c.req.valid("query");
  return c.json({ q, page, limit });
});
```

## Error Handling

```typescript
import { HTTPException } from "hono/http-exception";

// Throw HTTP errors
app.get("/users/:id", async (c) => {
  const user = await findUser(c.req.param("id"));
  if (!user) throw new HTTPException(404, { message: "User not found" });
  return c.json(user);
});

// Global error handler
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return c.json({ error: err.message }, err.status);
  }
  console.error(err);
  return c.json({ error: "Internal server error" }, 500);
});

// Not found handler
app.notFound((c) => c.json({ error: "Not found" }, 404));
```

## Database Integration (Drizzle)

```typescript
// db/index.ts
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const db = drizzle(pool, { schema });

// Middleware to inject db into context
import { createMiddleware } from "hono/factory";

const dbMiddleware = createMiddleware<{
  Variables: { db: typeof db };
}>(async (c, next) => {
  c.set("db", db);
  await next();
});

app.use("*", dbMiddleware);

// Use in routes
app.get("/users", async (c) => {
  const db = c.get("db");
  const users = await db.query.users.findMany();
  return c.json(users);
});
```

## Testing

```typescript
import { describe, it, expect } from "vitest";
import app from "../src/index";

describe("API", () => {
  it("GET /users returns list", async () => {
    const res = await app.request("/users");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });

  it("POST /users validates input", async () => {
    const res = await app.request("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "invalid" }),
    });
    expect(res.status).toBe(400);
  });
});
```

Hono's `app.request()` method enables testing without starting a server.

## RPC Client (End-to-End Type Safety)

```typescript
// server.ts
import { Hono } from "hono";
import { hc } from "hono/client";

const app = new Hono()
  .get("/users", (c) => c.json([{ id: "1", name: "Alice" }]))
  .post("/users", async (c) => {
    const body = await c.req.json();
    return c.json(body, 201);
  });

export type AppType = typeof app;

// client.ts (frontend or another service)
import { hc } from "hono/client";
import type { AppType } from "../server";

const client = hc<AppType>("http://localhost:3000");

// Fully typed — IDE autocomplete works
const res = await client.users.$get();
const users = await res.json();  // typed as { id: string, name: string }[]
```

## File Structure

```
src/
├── index.ts           # App entry point, server startup
├── routes/
│   ├── users.ts       # User routes
│   ├── posts.ts       # Post routes
│   └── auth.ts        # Auth routes
├── middleware/
│   ├── auth.ts        # Auth middleware
│   └── rate-limit.ts  # Rate limiting
├── db/
│   ├── index.ts       # Database client
│   └── schema/        # Drizzle schema files
└── utils/
    └── errors.ts      # Error helpers
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `c.req.json()` returns empty | Missing `Content-Type: application/json` header | Set header or use `zValidator` |
| CORS errors in browser | CORS middleware not applied | Add `cors()` middleware before routes |
| `c.get("key")` returns undefined | Variable not set in middleware | Check middleware order and type registration |
| Types not inferred in client | Export `AppType` incorrectly | Use `typeof app` on the chained app instance |
| Hot reload not working (Node) | Not using `--watch` | Use `tsx watch src/index.ts` |

## CRITICAL RULES

### MUST DO
- Always use `zValidator` for request validation — never parse manually
- Always chain route definitions for RPC type inference (`const app = new Hono().get(...).post(...)`)
- Always use `createMiddleware` with typed Variables for type-safe context
- Always handle errors with `app.onError()` global handler
- Use `app.request()` for testing — no need to start a server

### MUST NOT DO
- NEVER use `c.req.json()` without validation — always use `zValidator` or try/catch
- NEVER import runtime-specific modules at top level if targeting multiple runtimes
- NEVER mutate `c.req` directly — use `c.set()` / `c.get()` for passing data through middleware
