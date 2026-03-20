# Framework Entry Points & Environment Validation

## Entry Point Per Framework

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
