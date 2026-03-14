---
name: node-backend-dev
description: >
  Node.js backend development workflow: project setup, routing, middleware, validation,
  database access (Prisma/Drizzle/pg), error handling, auth patterns, WebSocket real-time,
  and testing. Covers Express, Hono, and ElysiaJS frameworks.
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

### Entry Point Per Framework

**Express:**

```typescript
import express from 'express';
import cors from 'cors';
import { errorHandler } from './middleware/error-handler';
import { v1Router } from './routes/v1';
import { env } from './config/env';

const app = express();

app.use(cors());
app.use(express.json());
app.use('/api/v1', v1Router);
app.use(errorHandler);

const server = app.listen(env.PORT, () => {
  console.log(`Server running on port ${env.PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});
```

**Hono:**

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serve } from '@hono/node-server';
import { v1Routes } from './routes/v1';
import { env } from './config/env';

const app = new Hono();

app.use('*', cors());
app.route('/api/v1', v1Routes);

app.onError((err, c) => {
  const status = err instanceof HTTPException ? err.status : 500;
  return c.json({ error: { code: 'INTERNAL_ERROR', message: err.message } }, status);
});

serve({ fetch: app.fetch, port: env.PORT }, (info) => {
  console.log(`Server running on port ${info.port}`);
});
```

**ElysiaJS:**

```typescript
import { Elysia } from 'elysia';
import { cors } from '@elysiajs/cors';
import { userRoutes } from './routes/v1/users';
import { env } from './config/env';

const app = new Elysia()
  .use(cors())
  .use(userRoutes)
  .listen(env.PORT);

console.log(`Server running on port ${app.server?.port}`);
```

### Environment Validation (Fail-Fast)

Validate all environment variables at startup using Zod. Refuse to start if config is invalid.

```typescript
// src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

export const env = envSchema.parse(process.env);
export type Env = z.infer<typeof envSchema>;
```

---

## STEP 2: Routing

### Route Definitions Per Framework

**Express:**

```typescript
// src/routes/v1/users.ts
import { Router } from 'express';
import { UserService } from '../../services/user.service';

const router = Router();

router.get('/:id', async (req, res, next) => {
  try {
    const user = await UserService.findById(req.params.id);
    if (!user) return res.status(404).json({ error: { code: 'NOT_FOUND', message: 'User not found' } });
    res.json({ data: user });
  } catch (err) { next(err); }
});

router.post('/', async (req, res, next) => {
  try {
    const user = await UserService.create(req.body);
    res.status(201).json({ data: user });
  } catch (err) { next(err); }
});

export { router as userRouter };

// src/routes/v1/index.ts — mount all domain routers
import { Router } from 'express';
import { userRouter } from './users';
import { healthRouter } from './health';

const v1Router = Router();
v1Router.use('/users', userRouter);
v1Router.use('/health', healthRouter);
export { v1Router };
```

**Hono:**

```typescript
// src/routes/v1/users.ts
import { Hono } from 'hono';
import { UserService } from '../../services/user.service';

const users = new Hono();

users.get('/:id', async (c) => {
  const user = await UserService.findById(c.req.param('id'));
  if (!user) return c.json({ error: { code: 'NOT_FOUND', message: 'User not found' } }, 404);
  return c.json({ data: user });
});

users.post('/', async (c) => {
  const body = await c.req.json();
  const user = await UserService.create(body);
  return c.json({ data: user }, 201);
});

export { users as userRoutes };

// src/routes/v1/index.ts — mount all domain routes
import { Hono } from 'hono';
import { userRoutes } from './users';
import { healthRoutes } from './health';

const v1Routes = new Hono();
v1Routes.route('/users', userRoutes);
v1Routes.route('/health', healthRoutes);
export { v1Routes };
```

**ElysiaJS:**

```typescript
// src/routes/v1/users.ts
import { Elysia, t } from 'elysia';
import { UserService } from '../../services/user.service';

export const userRoutes = new Elysia({ prefix: '/api/v1/users' })
  .get('/:id', async ({ params }) => {
    const user = await UserService.findById(params.id);
    if (!user) throw new Error('NOT_FOUND');
    return { data: user };
  }, {
    params: t.Object({ id: t.String() })
  })
  .post('/', async ({ body }) => {
    const user = await UserService.create(body);
    return { data: user };
  }, {
    body: t.Object({ name: t.String(), email: t.String({ format: 'email' }) })
  });
```

### Route Conventions

- One file per domain (users, orders, products) inside `routes/v1/`.
- API versioning: all routes under `/api/v1/`. When v2 is needed, create `routes/v2/` and mount separately.
- Health check at `GET /api/health` (outside versioned prefix).

---

## STEP 3: Middleware

### Auth Middleware

**Express:**

```typescript
import { Request, Response, NextFunction } from 'express';
import { verifyToken } from '../services/auth.service';

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    return res.status(401).json({ error: { code: 'UNAUTHORIZED', message: 'Missing token' } });
  }
  try {
    const user = await verifyToken(header.slice(7));
    (req as any).user = user;
    next();
  } catch {
    res.status(401).json({ error: { code: 'UNAUTHORIZED', message: 'Invalid token' } });
  }
}
```

**Hono:**

```typescript
import { createMiddleware } from 'hono/factory';
import { verifyToken } from '../services/auth.service';

export const authMiddleware = createMiddleware(async (c, next) => {
  const header = c.req.header('Authorization');
  if (!header?.startsWith('Bearer ')) {
    return c.json({ error: { code: 'UNAUTHORIZED', message: 'Missing token' } }, 401);
  }
  try {
    const user = await verifyToken(header.slice(7));
    c.set('user', user);
    await next();
  } catch {
    return c.json({ error: { code: 'UNAUTHORIZED', message: 'Invalid token' } }, 401);
  }
});
```

**ElysiaJS:**

```typescript
import { Elysia } from 'elysia';
import { verifyToken } from '../services/auth.service';

export const authPlugin = new Elysia({ name: 'auth' })
  .resolve({ as: 'scoped' }, async ({ headers }) => {
    const header = headers.authorization;
    if (!header?.startsWith('Bearer ')) throw new Error('UNAUTHORIZED');
    const user = await verifyToken(header.slice(7));
    return { user };
  });
```

### CORS Configuration

```typescript
// Express
import cors from 'cors';
app.use(cors({ origin: env.ALLOWED_ORIGINS.split(','), credentials: true }));

// Hono
import { cors } from 'hono/cors';
app.use('*', cors({ origin: env.ALLOWED_ORIGINS.split(','), credentials: true }));

// ElysiaJS
import { cors } from '@elysiajs/cors';
app.use(cors({ origin: env.ALLOWED_ORIGINS.split(','), credentials: true }));
```

### Security Headers

```typescript
// Express — use helmet
import helmet from 'helmet';
app.use(helmet());

// Hono — use secureHeaders
import { secureHeaders } from 'hono/secure-headers';
app.use('*', secureHeaders());

// ElysiaJS — manual or plugin
app.onBeforeHandle(({ set }) => {
  set.headers['X-Content-Type-Options'] = 'nosniff';
  set.headers['X-Frame-Options'] = 'DENY';
  set.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains';
});
```

### Request Logging

```typescript
// Express
import morgan from 'morgan';
app.use(morgan('combined'));

// Hono
import { logger } from 'hono/logger';
app.use('*', logger());

// ElysiaJS — trace or manual
app.onBeforeHandle(({ request }) => {
  console.log(`${request.method} ${new URL(request.url).pathname}`);
});
```

### Rate Limiting (Sliding Window)

```typescript
// In-memory sliding window — suitable for single-instance deployments
const windowMs = 60_000;
const maxRequests = 100;
const requestCounts = new Map<string, { count: number; resetAt: number }>();

function rateLimitCheck(clientIp: string): boolean {
  const now = Date.now();
  const entry = requestCounts.get(clientIp);
  if (!entry || now > entry.resetAt) {
    requestCounts.set(clientIp, { count: 1, resetAt: now + windowMs });
    return true;
  }
  if (entry.count >= maxRequests) return false;
  entry.count++;
  return true;
}

// For multi-instance: use Redis-based rate limiting (e.g., rate-limiter-flexible)
```

---

## STEP 4: Validation

### Schema Definition (Zod — shared across Express and Hono)

```typescript
// src/types/user.schema.ts
import { z } from 'zod';

export const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user'),
});

export const queryParamsSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export type CreateUserInput = z.infer<typeof createUserSchema>;
```

### Validation Per Framework

**Express + Zod (middleware approach):**

```typescript
import { z, ZodSchema } from 'zod';
import { Request, Response, NextFunction } from 'express';

export function validate(schema: ZodSchema, source: 'body' | 'query' | 'params' = 'body') {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req[source]);
    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          details: result.error.flatten().fieldErrors,
        },
      });
    }
    req[source] = result.data;
    next();
  };
}

// Usage
router.post('/users', validate(createUserSchema), createUserHandler);
```

**Hono + Zod (@hono/zod-validator):**

```typescript
import { zValidator } from '@hono/zod-validator';
import { createUserSchema, queryParamsSchema } from '../../types/user.schema';

users.post('/', zValidator('json', createUserSchema), async (c) => {
  const validated = c.req.valid('json');
  const user = await UserService.create(validated);
  return c.json({ data: user }, 201);
});

users.get('/', zValidator('query', queryParamsSchema), async (c) => {
  const { page, limit } = c.req.valid('query');
  const users = await UserService.list(page, limit);
  return c.json({ data: users });
});
```

**ElysiaJS + TypeBox (built-in):**

```typescript
import { Elysia, t } from 'elysia';

new Elysia({ prefix: '/api/v1/users' })
  .post('/', async ({ body }) => {
    const user = await UserService.create(body);
    return { data: user };
  }, {
    body: t.Object({
      name: t.String({ minLength: 1, maxLength: 100 }),
      email: t.String({ format: 'email' }),
      role: t.Optional(t.Union([t.Literal('admin'), t.Literal('user')])),
    }),
    response: {
      200: t.Object({ data: t.Object({ id: t.String(), name: t.String() }) }),
      400: t.Object({ error: t.Object({ code: t.String(), message: t.String() }) }),
    },
  });
```

### Validation Error Response Format

All frameworks MUST return validation errors in this consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "email": ["Invalid email format"],
      "name": ["String must contain at least 1 character(s)"]
    }
  }
}
```

---

## STEP 5: Database Access

### ORM Decision Table

| ORM         | Best For                       | Migrations      | Query Style          |
|-------------|--------------------------------|-----------------|----------------------|
| Prisma      | Type-safe, declarative schema  | prisma migrate  | Client methods       |
| Drizzle     | SQL-like, lightweight          | drizzle-kit     | Fluent builder       |
| pg (raw)    | Simple APIs, full control      | Manual SQL files | Parameterized queries|

### Prisma Singleton

Prevents connection pool exhaustion from hot reloads in development.

```typescript
// src/db/index.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'warn', 'error'] : ['error'],
});

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

// Graceful shutdown
process.on('SIGTERM', async () => {
  await prisma.$disconnect();
});
```

### Drizzle Setup

```typescript
// src/db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const client = postgres(process.env.DATABASE_URL!, {
  max: 10,
  idle_timeout: 20,
  connect_timeout: 10,
});

export const db = drizzle(client, { schema });

// Graceful shutdown
export async function closeDb() {
  await client.end();
}

// Schema example — src/db/schema/users.ts
import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});
```

### Raw pg Pool

```typescript
// src/db/index.ts
import { Pool } from 'pg';

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 15,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
});

// Always use parameterized queries
const result = await pool.query('SELECT * FROM users WHERE id = $1', [id]);

// Graceful shutdown
process.on('SIGTERM', async () => {
  await pool.end();
});
```

### Service Layer Pattern

Services encapsulate business logic. They receive validated data and interact with the database.

```typescript
// src/services/user.service.ts
import { prisma } from '../db';
import { CreateUserInput } from '../types/user.schema';

export const UserService = {
  async findById(id: string) {
    return prisma.user.findUnique({ where: { id } });
  },

  async create(data: CreateUserInput) {
    return prisma.user.create({ data });
  },

  async list(page: number, limit: number) {
    const skip = (page - 1) * limit;
    const [users, total] = await Promise.all([
      prisma.user.findMany({ skip, take: limit, orderBy: { createdAt: 'desc' } }),
      prisma.user.count(),
    ]);
    return { users, total, page, limit };
  },
};
```

---

## STEP 6: Error Handling

### Custom AppError Class

```typescript
// src/middleware/error-handler.ts
export class AppError extends Error {
  constructor(
    public code: string,
    public statusCode: number,
    message: string,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// Convenience factory functions
export const NotFound = (resource: string) =>
  new AppError('NOT_FOUND', 404, `${resource} not found`);
export const Unauthorized = (msg = 'Authentication required') =>
  new AppError('UNAUTHORIZED', 401, msg);
export const Forbidden = (msg = 'Insufficient permissions') =>
  new AppError('FORBIDDEN', 403, msg);
export const BadRequest = (msg: string, details?: Record<string, unknown>) =>
  new AppError('BAD_REQUEST', 400, msg, details);
export const Conflict = (msg: string) =>
  new AppError('CONFLICT', 409, msg);
```

### PostgreSQL Error Code Mapping

```typescript
function mapPgError(err: any): AppError {
  switch (err.code) {
    case '23505': // unique_violation
      return new AppError('CONFLICT', 409, 'Resource already exists', {
        constraint: err.constraint,
      });
    case '23503': // foreign_key_violation
      return new AppError('BAD_REQUEST', 400, 'Referenced resource not found');
    case '22P02': // invalid_text_representation
      return new AppError('BAD_REQUEST', 400, 'Invalid input syntax');
    case '23502': // not_null_violation
      return new AppError('BAD_REQUEST', 400, `Missing required field: ${err.column}`);
    default:
      return new AppError('INTERNAL_ERROR', 500, 'Database error');
  }
}
```

### Global Error Handler Per Framework

**Express:**

```typescript
import { Request, Response, NextFunction } from 'express';

export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, ...(err.details && { details: err.details }) },
    });
  }

  // Map PostgreSQL errors
  if ((err as any).code && typeof (err as any).code === 'string' && (err as any).code.length === 5) {
    const mapped = mapPgError(err);
    return res.status(mapped.statusCode).json({
      error: { code: mapped.code, message: mapped.message, ...(mapped.details && { details: mapped.details }) },
    });
  }

  // Never expose stack traces in production
  console.error('Unhandled error:', err);
  res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } });
}
```

**Hono:**

```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  if (err instanceof AppError) {
    return c.json({
      error: { code: err.code, message: err.message, ...(err.details && { details: err.details }) },
    }, err.statusCode as any);
  }
  if (err instanceof HTTPException) {
    return c.json({ error: { code: 'HTTP_ERROR', message: err.message } }, err.status);
  }
  console.error('Unhandled error:', err);
  return c.json({ error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } }, 500);
});
```

**ElysiaJS:**

```typescript
new Elysia()
  .error({ APP_ERROR: AppError })
  .onError(({ error, code, set }) => {
    if (error instanceof AppError) {
      set.status = error.statusCode;
      return {
        error: { code: error.code, message: error.message, ...(error.details && { details: error.details }) },
      };
    }
    console.error('Unhandled error:', error);
    set.status = 500;
    return { error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } };
  });
```

---

## STEP 7: Auth Patterns

### Session-Based (Better Auth)

```typescript
// Express — mount Better Auth handler
import { toNodeHandler } from 'better-auth/node';
import { auth } from './auth'; // Better Auth instance
app.all('/api/auth/*splat', toNodeHandler(auth));

// Hono — mount directly (uses Web Standard Request)
import { auth } from './auth';
app.on(['GET', 'POST'], '/api/auth/**', (c) => auth.handler(c.req.raw));

// ElysiaJS — mount directly
import { auth } from './auth';
app.all('/api/auth/*', async ({ request }) => auth.handler(request));
```

### Token-Based (JWT with jose)

```typescript
import { SignJWT, jwtVerify } from 'jose';

const secret = new TextEncoder().encode(env.JWT_SECRET);

export async function signToken(payload: { sub: string; role: string }): Promise<string> {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(secret);
}

export async function verifyToken(token: string) {
  const { payload } = await jwtVerify(token, secret);
  return payload;
}
```

### Dev Auth Bypass

Environment-guarded fake user for development. Exits the process if accidentally enabled in production.

```typescript
export function devAuthMiddleware() {
  if (process.env.NODE_ENV === 'production' && process.env.DEV_AUTH === 'true') {
    console.error('FATAL: DEV_AUTH enabled in production');
    process.exit(1);
  }

  return (req: any, _res: any, next: any) => {
    if (process.env.DEV_AUTH === 'true') {
      req.user = { id: 'dev-user-001', email: 'dev@localhost', role: 'admin' };
    }
    next();
  };
}
```

### Optional Auth Middleware

Sets user if a valid token is present, continues without user if not. Useful for endpoints
that behave differently for authenticated vs anonymous users.

```typescript
// Express
export async function optionalAuth(req: Request, _res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (header?.startsWith('Bearer ')) {
    try {
      (req as any).user = await verifyToken(header.slice(7));
    } catch { /* token invalid — continue as anonymous */ }
  }
  next();
}

// Hono
export const optionalAuth = createMiddleware(async (c, next) => {
  const header = c.req.header('Authorization');
  if (header?.startsWith('Bearer ')) {
    try { c.set('user', await verifyToken(header.slice(7))); } catch {}
  }
  await next();
});
```

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

### Framework-Specific Test Invocation

```typescript
// Express — use supertest
import request from 'supertest';
const res = await request(app).get('/api/health');
expect(res.status).toBe(200);
expect(res.body).toEqual({ status: 'ok' });

// Hono — use app.request (built-in)
const res = await app.request('/api/health');
expect(res.status).toBe(200);
expect(await res.json()).toEqual({ status: 'ok' });

// ElysiaJS — use app.handle with Request object
const res = await app.handle(new Request('http://localhost/api/health'));
expect(res.status).toBe(200);
expect(await res.json()).toEqual({ status: 'ok' });
```

### Validation Test (any framework)

```typescript
// POST with invalid body — expect 400 + structured error
const res = await request(app).post('/api/v1/users').send({ name: '' });
expect(res.status).toBe(400);
expect(res.body.error.code).toBe('VALIDATION_ERROR');
```

### Service Layer Unit Test (with Mocks)

```typescript
jest.mock('../src/db', () => ({
  prisma: { user: { findUnique: jest.fn(), create: jest.fn() } },
}));

describe('UserService', () => {
  afterEach(() => jest.clearAllMocks());

  it('returns null for non-existent user', async () => {
    (prisma.user.findUnique as jest.Mock).mockResolvedValue(null);
    expect(await UserService.findById('nonexistent')).toBeNull();
  });
});
```

### Test Database with Cleanup

```typescript
afterEach(async () => {
  await prisma.$transaction([prisma.order.deleteMany(), prisma.user.deleteMany()]);
});
afterAll(async () => { await prisma.$disconnect(); });
```

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
