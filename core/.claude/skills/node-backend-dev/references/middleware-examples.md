# Middleware Examples Per Framework

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
// Express â€” use helmet
import helmet from 'helmet';
app.use(helmet());

// Hono â€” use secureHeaders
import { secureHeaders } from 'hono/secure-headers';
app.use('*', secureHeaders());

// ElysiaJS â€” manual or plugin
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

// ElysiaJS â€” trace or manual
app.onBeforeHandle(({ request }) => {
  console.log(`${request.method} ${new URL(request.url).pathname}`);
});
```

### Rate Limiting (Sliding Window)

```typescript
// In-memory sliding window â€” suitable for single-instance deployments
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
