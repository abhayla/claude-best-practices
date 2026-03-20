# Auth Patterns


### Session-Based (Better Auth)

```typescript
// Express â€” mount Better Auth handler
import { toNodeHandler } from 'better-auth/node';
import { auth } from './auth'; // Better Auth instance
app.all('/api/auth/*splat', toNodeHandler(auth));

// Hono â€” mount directly (uses Web Standard Request)
import { auth } from './auth';
app.on(['GET', 'POST'], '/api/auth/**', (c) => auth.handler(c.req.raw));

// ElysiaJS â€” mount directly
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
    } catch { /* token invalid â€” continue as anonymous */ }
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
