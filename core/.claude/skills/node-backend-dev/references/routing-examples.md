# Route Definitions Per Framework


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

// src/routes/v1/index.ts â€” mount all domain routers
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

// src/routes/v1/index.ts â€” mount all domain routes
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
