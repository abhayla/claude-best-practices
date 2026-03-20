# Testing Examples


### Framework-Specific Test Invocation

```typescript
// Express â€” use supertest
import request from 'supertest';
const res = await request(app).get('/api/health');
expect(res.status).toBe(200);
expect(res.body).toEqual({ status: 'ok' });

// Hono â€” use app.request (built-in)
const res = await app.request('/api/health');
expect(res.status).toBe(200);
expect(await res.json()).toEqual({ status: 'ok' });

// ElysiaJS â€” use app.handle with Request object
const res = await app.handle(new Request('http://localhost/api/health'));
expect(res.status).toBe(200);
expect(await res.json()).toEqual({ status: 'ok' });
```

### Validation Test (any framework)

```typescript
// POST with invalid body â€” expect 400 + structured error
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
