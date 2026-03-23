---
name: node-backend-dev
description: >
  Build Node.js backend services with project setup, routing, middleware, validation,
  database access (Prisma/Drizzle/pg), error handling, auth patterns, WebSocket real-time,
  and testing. Use when developing APIs or server-side logic with Express, Hono, or ElysiaJS.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "express, hono, elysia, node backend, api server, route handler, node.js server"
argument-hint: "<feature-description or 'setup' or 'middleware' or 'auth' or 'websocket'>"
version: "1.0.0"
type: workflow
---

# Node.js Backend Development

Build production-ready Node.js backend APIs with Express, Hono, or ElysiaJS. Includes routing,
middleware, validation, database access, error handling, auth, WebSocket, and testing patterns.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup

### Framework Decision Table

| Framework  | Best For                           | Runtime              | Validation               |
|------------|------------------------------------|----------------------|--------------------------|
| Express    | Mature ecosystem, middleware depth | Node.js              | Manual (Zod)             |
| Hono       | Edge/lightweight, multi-runtime   | Node/Bun/Deno/Edge   | @hono/zod-validator      |
| ElysiaJS   | Bun-native, type-safe DI          | Bun                  | TypeBox (built-in)       |
| Fastify    | Plugin ecosystem, schema-first    | Node.js              | JSON Schema (built-in)   |

### Initialize Project

```bash
# Node.js (Express or Hono)
mkdir my-api && cd my-api
npm init -y
npm install typescript tsx @types/node --save-dev
npx tsc --init --strict --module nodenext --moduleResolution nodenext --outDir dist

# Bun (ElysiaJS)
bun init
bun add elysia
```

### Project Structure

```
src/
  index.ts            # Entry point
  routes/
    v1/               # Versioned routes
      users.ts
      health.ts
  middleware/
    auth.ts
    error-handler.ts
    cors.ts
    rate-limit.ts
  services/           # Business logic layer
    user.service.ts
  db/
    index.ts          # DB client singleton
    schema/           # ORM schema definitions
    migrations/       # Migration files
  config/
    env.ts            # Environment validation at startup
  types/
    index.ts          # Shared type definitions
```


**Read:** `references/framework-setup.md` for entry point examples per framework and environment validation with Zod.

---

## STEP 2: Routing

**Read:** `references/routing-examples.md` for complete route definitions per framework (Express, Hono, ElysiaJS).

### Route Conventions

- One file per domain (users, orders, products) inside `routes/v1/`.
- API versioning: all routes under `/api/v1/`. When v2 is needed, create `routes/v2/` and mount separately.
- Health check at `GET /api/health` (outside versioned prefix).

---

## STEP 3: Middleware

**Read:** `references/middleware-examples.md` for auth, CORS, security headers, logging, and rate limiting examples per framework.

---

## STEP 4: Validation

**Read:** `references/validation-examples.md` for Zod schema definitions and validation patterns per framework (Express, Hono, ElysiaJS).

---

## STEP 5: Database Access

**Read:** `references/database-setup.md` for ORM setup (Prisma, Drizzle, raw pg), connection pooling, and service layer pattern.

---

## STEP 6: Error Handling

**Read:** `references/error-handling-examples.md` for AppError class, PostgreSQL error mapping, and global error handlers per framework.

---

## STEP 7: Auth Patterns

**Read:** `references/auth-patterns.md` for session-based (Better Auth), token-based (JWT), dev bypass, and optional auth middleware.

---

## STEP 8: Real-time (WebSocket)

> Extended examples with all three frameworks: `references/websocket.md`

### Core Patterns

- **ElysiaJS**: Use `.ws()` with built-in Bun WebSocket. Supports `subscribe`/`publish` for topic-based pub/sub.
- **Express/Hono on Node.js**: Use `ws` library with `WebSocketServer` attached to the HTTP server.
- **Hono**: Use `@hono/node-ws` with `createNodeWebSocket()` and `upgradeWebSocket()` helper.
- Auth on WS connect: validate token from query param or first message. Close with 4001/4003 codes on failure.

### Typed Message Protocol (Discriminated Union)

```typescript
type WsMessage =
  | { type: 'join'; payload: { roomId: string } }
  | { type: 'leave'; payload: { roomId: string } }
  | { type: 'message'; payload: { roomId: string; content: string } }
  | { type: 'typing'; payload: { roomId: string; isTyping: boolean } };
```

### Broadcaster Pattern

Hold a server reference so services can publish events without importing WebSocket internals.

```typescript
class Broadcaster {
  private wss: WebSocketServer | null = null;
  attach(wss: WebSocketServer) { this.wss = wss; }

  publish(topic: string, data: unknown) {
    if (!this.wss) return;
    const message = JSON.stringify({ topic, data });
    this.wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) client.send(message);
    });
  }
}
export const broadcaster = new Broadcaster();
```

---

## STEP 9: Testing

**Read:** `references/testing-examples.md` for framework-specific test invocation, validation tests, service mocking, and DB cleanup.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| CORS errors in browser | Missing or misconfigured CORS middleware | Mount CORS middleware before routes. Verify allowed origins include the frontend URL with protocol. |
| Connection pool exhaustion | Too many PrismaClient instances or unclosed connections | Use singleton pattern (Step 5). Set `max` pool size to 10-20. Close pools on SIGTERM. |
| Middleware not executing | Middleware mounted after the route it should protect | Mount middleware before routes. Express processes middleware in registration order. |
| Async error crashes process | Unhandled promise rejection in route handler | Express: wrap handlers with `try/catch` and call `next(err)`, or use `express-async-errors`. Hono/Elysia: errors in async handlers are caught automatically. |
| Port already in use (EADDRINUSE) | Previous process still bound to the port | Kill the old process: `lsof -ti :3000 \| xargs kill` (Unix) or `npx kill-port 3000`. |
| ECONNREFUSED to database | Database not running or wrong connection string | Verify DATABASE_URL, confirm the database is accepting connections, check firewall rules. |
| Request body undefined | Missing JSON body parser middleware | Express: add `app.use(express.json())` before routes. Hono/Elysia: built-in, no extra step needed. |
| TypeBox validation errors cryptic | Default ElysiaJS error format lacks field-level detail | Use `.onError()` hook to reformat validation errors into the standard `{ error: { code, message, details } }` shape. |
| Drizzle migrations out of sync | Schema changed without generating migration | Run `npx drizzle-kit generate` after schema changes, then `npx drizzle-kit migrate`. |
| JWT token rejected after deploy | Different JWT_SECRET between environments | Validate JWT_SECRET in env.ts at startup. Use the same secret across all instances in an environment. |

---

## CRITICAL RULES

### MUST DO

- Always parameterize SQL queries -- never use string interpolation for user data
- Implement graceful shutdown: close DB pools and HTTP server on SIGTERM/SIGINT
- Use a consistent JSON error response format (`{ error: { code, message, details? } }`) across all endpoints
- Provide a health check endpoint at `GET /api/health` that verifies DB connectivity
- Validate all user input at the route boundary -- services trust validated data
- Use connection pooling for PostgreSQL (max 10-20 connections per instance)
- Validate environment variables at startup with a schema -- fail fast on missing config
- Use `createMiddleware()` from `hono/factory` when extracting Hono middleware to separate files (preserves type safety)
- Register CORS middleware before routes -- especially before WebSocket upgrade handlers in Hono
- Use the singleton pattern for Prisma in development to prevent hot-reload connection leaks

### MUST NOT DO

- Expose stack traces in production error responses -- log them server-side, return a generic message to the client
- Use synchronous file I/O or heavy computation in request handlers -- offload to worker threads or a job queue
- Trust client-submitted user IDs for authorization -- always derive the user identity from the auth token
- Skip error handling middleware -- unhandled rejections crash the Node.js process
- Store secrets in code -- use environment variables validated at startup
- Mount auth middleware after routes -- middleware registration order determines execution order
- Create a new PrismaClient per request -- reuse a single instance via the singleton pattern
- Use `express.json()` after route definitions -- body parsing must happen before handlers execute
