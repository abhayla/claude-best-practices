---
description: Prisma model and query conventions — cuid PKs, cascade ownership, findFirst ownership checks, upsert singletons, parallel reads, and the dev-mode client singleton.
globs: ["**/schema.prisma", "**/*.prisma", "**/prisma/**/*.ts"]
---

# Prisma Conventions

## Model Conventions

### Primary Keys and Timestamps

Every model MUST include:

```prisma
id        String   @id @default(cuid())
createdAt DateTime @default(now())
updatedAt DateTime @updatedAt
```

### User Ownership

Every owned model MUST include a user relation with cascade delete and an index on the FK:

```prisma
userId String
user   User @relation(fields: [userId], references: [id], onDelete: Cascade)

@@index([userId])
```

Always `@@index` any foreign key you filter or join on — `@@index([fkId])`. Rely on `onDelete: Cascade` for child cleanup; do not manually delete children before the parent.

### Enum Conventions

- PascalCase enum names: `ItemStatus`, `OrderType`
- UPPER_SNAKE_CASE values: `ACTIVE`, `IN_PROGRESS`, `ARCHIVED`

### Schema Organization

Group related models with section comment blocks:

```prisma
// ==== Catalog ====
model Item { ... }
model Category { ... }

// ==== Orders ====
model Order { ... }
```

## Query Conventions

### Ownership-Checked Lookups

Use `findFirst` with both `id` and `userId` for ownership verification:

```ts
const record = await prisma.item.findFirst({ where: { id, userId } })
```

MUST NOT use `findUnique` for ownership checks — `findUnique` only accepts `@id` / `@@unique` fields and cannot filter by a non-unique `userId` alongside the id.

### True Unique Lookups

Use `findUnique` ONLY for genuinely unique lookups:

```ts
const profile = await prisma.userProfile.findUnique({ where: { userId } })
```

### Singleton Records

Use `upsert` for singleton-per-user records (preferences, settings, cached metrics):

```ts
await prisma.userSettings.upsert({
  where: { userId },
  create: { userId, ...data },
  update: { ...data },
})
```

### Parallel Independent Reads

Use `Promise.all([...])` for independent queries in aggregation/overview endpoints:

```ts
const [items, orders, categories] = await Promise.all([
  prisma.item.findMany({ where: { userId } }),
  prisma.order.findMany({ where: { userId } }),
  prisma.category.findMany({ where: { userId } }),
])
```

### Include Patterns

- LIST endpoints: `include` with a `take` limit on nested relations
- DETAIL endpoints: full `include`, no limits

### Dev-Mode Client Singleton

Reuse a single client via `globalThis` in dev to avoid connection-pool exhaustion on hot reload:

```ts
const prisma = globalThis.prisma || new PrismaClient()
if (process.env.NODE_ENV !== 'production') globalThis.prisma = prisma
```

## Anti-Patterns

- NEVER use `findUnique` for ownership checks — use `findFirst` with `{ id, userId }`
- NEVER `new PrismaClient()` per module in dev without the `globalThis` guard — hot reload exhausts the connection pool
- NEVER manually delete child rows before the parent when the relation declares `onDelete: Cascade` — let the database do it
- NEVER leave a frequently-filtered foreign key un-indexed — add `@@index([fkId])`
- NEVER run independent reads serially in aggregation endpoints — batch them with `Promise.all`
