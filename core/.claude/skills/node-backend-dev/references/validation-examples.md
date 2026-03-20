# Validation Examples Per Framework

### Schema Definition (Zod â€” shared across Express and Hono)

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
