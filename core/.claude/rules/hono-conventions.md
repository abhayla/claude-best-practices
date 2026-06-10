---
description: Hono backend route conventions — instance setup, inline Zod validation, ownership checks, response envelopes, opt-in pagination, and rate limiting.
globs: ["**/server/**/*.ts", "**/routes/**/*.ts", "**/api/**/*.ts"]
---

# Hono Route Conventions

## Route File Structure

Every route file creates a `new Hono()` instance, applies global auth middleware, and `export default`s the app. No exceptions.

```ts
import { Hono } from 'hono'
import { authMiddleware } from '../middleware/auth'

const app = new Hono()
app.use('*', authMiddleware)

// ... route handlers ...

export default app
```

Register routes in the root entry by domain: `app.route('/api/items', itemRoutes)`.

## Inline Zod Validation

Schemas are defined INLINE per route file — never shared across files.

- Create schema: full object with all required fields
- Update schema: reuse the create schema with `.partial()`
- Enums: standalone `z.enum([...])` constants at module level

```ts
const statusEnum = z.enum(['ACTIVE', 'PAUSED', 'ARCHIVED'])
const createItemSchema = z.object({ name: z.string().min(1), quantity: z.number().int(), status: statusEnum })
const updateItemSchema = createItemSchema.partial()
```

## Ownership Verification

Before any UPDATE or DELETE, verify ownership with `findFirst` on both `id` AND `userId` — never `findUnique`, and never trust the client to own the resource.

```ts
const item = await prisma.item.findFirst({ where: { id, userId } })
if (!item) return apiError(c, 'Not found', 404)
```

`findUnique` only filters on `@id` / `@@unique` fields and cannot scope by `userId` — it leaks cross-tenant rows.

## State-Changing Actions Use POST

Side-effecting actions are POST, not PUT/PATCH:

```ts
app.post('/:id/activate', ...)
app.post('/:id/archive', ...)
app.post('/process', ...)
```

## Response Envelope

Every response is wrapped in a discriminated envelope via helpers (e.g. `server/lib/api-utils.ts`). NEVER return raw `c.json(...)` — enforce this with an ESLint `no-restricted-syntax` rule on the `c.json` callee.

- `apiSuccess(c, data, status = 200)` → `{ success: true, data }`
- `apiError(c, message, status = 400, code?, details?)` → `{ success: false, error: { message, code?, ... } }`
- `apiPaginated(c, items, meta, status = 200)` → `{ success: true, data, pagination: { page, pageSize, total, totalPages, hasMore } }`

Use a shared `ErrorCode` enum for machine-readable codes; never invent ad-hoc strings. A central `onError` handler converts uncaught exceptions to `apiError` envelopes — do not duplicate that in every route's try/catch. (The client side of this contract is the unwrap helpers in `vue.md`.)

## Pagination Is Opt-In

List endpoints are unpaginated by default. Paginate ONLY when `?page=` is present — this preserves existing callers that consume full lists.

```ts
const pg = parsePagination(c)              // reads ?page= / ?pageSize=, returns null if absent
if (pg) return apiPaginated(c, items, buildPaginationMeta(pg, total))
return apiSuccess(c, items)                // full list when no ?page=
```

Never switch the response shape on anything but `?page=` (not role, flag, or body). Page-size caps live in the pagination helper — raise them there, not per-route.

## Rate Limiting

Rate-limit auth and other sensitive routes via a middleware factory with one isolated store per call. Relax thresholds in dev/test by passing a higher `max` at the mount site — never via an unconditional bypass.

```ts
export const rateLimit = ({ windowMs, max, prefix }: RateLimitOptions) => { /* in-memory Map */ }

app.use('/api/auth/*', rateLimit({ windowMs: 60_000, max: isProd ? 20 : 2000, prefix: 'auth' }))
```

Each sensitive sub-flow gets its own `prefix` so one attacker's budget cannot drain another's. Responses at the limit return HTTP 429 via `apiError(c, msg, 429, ErrorCode.RATE_LIMITED)`.

> **Scaling caveat:** a Map-based store resets on restart and is per-process. Behind more than one backend node, replace it with Redis or a shared store before deploying.

## Anti-Patterns

- NEVER use `findUnique` for ownership checks — it cannot filter by `userId` and leaks cross-tenant rows
- NEVER return raw `c.json(...)` from a handler — it breaks the client unwrap contract; use the envelope helpers
- NEVER paginate a list endpoint unconditionally — it breaks every caller that expected the full collection
- NEVER use PUT/PATCH for state-changing actions like activate/archive/process — use POST
- NEVER share Zod schemas across route files — define them inline per resource
- NEVER raise prod rate limits to accommodate a misbehaving client — fix the client or allow-list it
