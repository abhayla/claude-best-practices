---
name: prisma-orm
description: >
  Prisma ORM schema design, migrations, queries, and client usage for TypeScript projects.
  Use when working with Prisma in any TypeScript backend (Next.js, Express, Hono, Fastify).
allowed-tools: "Read Grep Glob"
argument-hint: "[schema|migrate|query|seed]"
version: "1.0.0"
type: reference
triggers: prisma, prisma-orm, prisma-client
---

# Prisma ORM Reference

Prisma ORM with Prisma Client and Prisma Migrate for TypeScript projects.

## Schema Definition

### Basic Schema (prisma/schema.prisma)

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum Role {
  USER
  ADMIN
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String
  role      Role     @default(USER)
  isActive  Boolean  @default(true) @map("is_active")
  loginCount Int     @default(0) @map("login_count")
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  posts     Post[]
  comments  Comment[]

  @@map("users")
}

model Post {
  id        String   @id @default(uuid())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  String   @map("author_id")
  createdAt DateTime @default(now()) @map("created_at")

  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  comments  Comment[]

  @@index([authorId])
  @@map("posts")
}

model Comment {
  id       String @id @default(uuid())
  text     String
  postId   String @map("post_id")
  authorId String @map("author_id")

  post     Post   @relation(fields: [postId], references: [id], onDelete: Cascade)
  author   User   @relation(fields: [authorId], references: [id], onDelete: Cascade)

  @@index([postId])
  @@index([authorId])
  @@map("comments")
}
```

### Field Type Quick Reference

| Prisma Type | PostgreSQL | Notes |
|-------------|-----------|-------|
| `String` | `TEXT` | Use `@db.VarChar(N)` for VARCHAR |
| `Int` | `INTEGER` | 32-bit |
| `BigInt` | `BIGINT` | Use for large numbers |
| `Float` | `DOUBLE PRECISION` | — |
| `Decimal` | `DECIMAL(65,30)` | Use `@db.Decimal(P,S)` for precision |
| `Boolean` | `BOOLEAN` | — |
| `DateTime` | `TIMESTAMP(3)` | Millisecond precision by default |
| `Json` | `JSONB` | — |
| `Bytes` | `BYTEA` | Binary data |
| `String @id @default(uuid())` | `UUID` | Use `@db.Uuid` for native UUID type |

### Common Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `@id` | Primary key | `id String @id` |
| `@default()` | Default value | `@default(now())`, `@default(uuid())`, `@default(autoincrement())` |
| `@unique` | Unique constraint | `email String @unique` |
| `@map("col")` | Map to DB column name | `createdAt @map("created_at")` |
| `@@map("table")` | Map to DB table name | `@@map("users")` |
| `@@index([fields])` | Database index | `@@index([authorId])` |
| `@@unique([fields])` | Composite unique | `@@unique([email, tenantId])` |
| `@relation()` | Define FK relation | See relations section |
| `@updatedAt` | Auto-update timestamp | `updatedAt DateTime @updatedAt` |

## Migrations

### Commands

```bash
# Generate migration from schema changes (creates SQL + applies)
npx prisma migrate dev --name descriptive_name

# Generate migration SQL only (don't apply)
npx prisma migrate dev --create-only --name descriptive_name

# Apply pending migrations (production)
npx prisma migrate deploy

# Reset database (drop + recreate + apply all migrations + seed)
npx prisma migrate reset

# Check migration status
npx prisma migrate status

# Generate Prisma Client (after schema changes)
npx prisma generate

# Push schema without migrations (prototyping only)
npx prisma db push

# Pull schema from existing database
npx prisma db pull

# Open Prisma Studio (visual DB browser)
npx prisma studio

# Seed database
npx prisma db seed
```

### Migration Workflow

1. Edit `prisma/schema.prisma`
2. Run `npx prisma migrate dev --name what_changed`
3. Review generated SQL in `prisma/migrations/`
4. Prisma auto-generates the client
5. Commit schema + migration files

## Client Setup

```typescript
// lib/prisma.ts
import { PrismaClient } from "@prisma/client";

// Prevent multiple instances in development (hot reload)
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === "development" ? ["query", "warn", "error"] : ["error"],
});

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```

## Query Patterns

### Find Queries

```typescript
// Find many with filtering, ordering, pagination
const users = await prisma.user.findMany({
  where: {
    isActive: true,
    email: { contains: "@example.com" },
    loginCount: { gte: 5 },
  },
  orderBy: { createdAt: "desc" },
  skip: 20,
  take: 10,
});

// Find unique (by unique field or ID)
const user = await prisma.user.findUnique({
  where: { email: "user@example.com" },
});

// Find first (non-unique conditions)
const admin = await prisma.user.findFirst({
  where: { role: "ADMIN" },
});

// Find with relations (eager loading)
const userWithPosts = await prisma.user.findUnique({
  where: { id: userId },
  include: {
    posts: {
      where: { published: true },
      orderBy: { createdAt: "desc" },
      take: 10,
      include: { comments: true },
    },
  },
});

// Select specific fields
const names = await prisma.user.findMany({
  select: { name: true, email: true },
});
```

### Where Conditions

```typescript
// AND (implicit)
where: { isActive: true, role: "ADMIN" }

// OR
where: { OR: [{ email: { contains: "a" } }, { name: { contains: "a" } }] }

// NOT
where: { NOT: { role: "ADMIN" } }

// String filters
where: { email: { contains: "example", startsWith: "user", endsWith: ".com", mode: "insensitive" } }

// Number filters
where: { loginCount: { gt: 5, lte: 100, in: [1, 2, 3] } }

// Relation filters
where: { posts: { some: { published: true } } }       // has at least one published post
where: { posts: { none: { published: false } } }      // no unpublished posts
where: { posts: { every: { published: true } } }      // all posts are published
```

### Create

```typescript
// Single create
const user = await prisma.user.create({
  data: {
    email: "user@example.com",
    name: "Test User",
  },
});

// Create with nested relation
const userWithPost = await prisma.user.create({
  data: {
    email: "user@example.com",
    name: "Test User",
    posts: {
      create: [
        { title: "First Post", content: "Hello world" },
      ],
    },
  },
  include: { posts: true },
});

// Bulk create
const count = await prisma.user.createMany({
  data: [
    { email: "a@example.com", name: "A" },
    { email: "b@example.com", name: "B" },
  ],
  skipDuplicates: true,
});
```

### Update

```typescript
// Update by unique field
const updated = await prisma.user.update({
  where: { id: userId },
  data: { isActive: false },
});

// Upsert (create or update)
const user = await prisma.user.upsert({
  where: { email: "user@example.com" },
  create: { email: "user@example.com", name: "New User" },
  update: { name: "Updated Name" },
});

// Increment/decrement
await prisma.user.update({
  where: { id: userId },
  data: { loginCount: { increment: 1 } },
});

// Bulk update
await prisma.user.updateMany({
  where: { isActive: false },
  data: { role: "USER" },
});
```

### Delete

```typescript
await prisma.user.delete({ where: { id: userId } });
await prisma.user.deleteMany({ where: { isActive: false } });
```

### Transactions

```typescript
// Interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const user = await tx.user.create({ data: { email, name } });
  await tx.post.create({ data: { authorId: user.id, title: "First Post" } });
  return user;
});

// Batch transaction (all or nothing)
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { email, name } }),
  prisma.post.create({ data: { authorId: id, title: "Post" } }),
]);
```

### Aggregations

```typescript
const stats = await prisma.user.aggregate({
  _count: true,
  _avg: { loginCount: true },
  _max: { loginCount: true },
  where: { isActive: true },
});

// Group by
const byRole = await prisma.user.groupBy({
  by: ["role"],
  _count: true,
  _avg: { loginCount: true },
});
```

### Raw SQL

```typescript
// Tagged template (parameterized — safe from injection)
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE email = ${email}
`;

// Execute raw (for DDL or non-returning queries)
await prisma.$executeRaw`
  UPDATE users SET login_count = login_count + 1 WHERE id = ${userId}
`;
```

## Seeding

```typescript
// prisma/seed.ts
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  await prisma.user.upsert({
    where: { email: "admin@example.com" },
    update: {},
    create: {
      email: "admin@example.com",
      name: "Admin",
      role: "ADMIN",
    },
  });
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
```

```json
// package.json
{
  "prisma": {
    "seed": "tsx prisma/seed.ts"
  }
}
```

## File Structure

```
prisma/
├── schema.prisma           # Schema definition
├── migrations/             # Generated migration SQL
│   ├── 20240101_init/
│   │   └── migration.sql
│   └── migration_lock.toml
└── seed.ts                 # Seed script
lib/
└── prisma.ts               # Singleton client
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `PrismaClientInitializationError` | Client not generated | Run `npx prisma generate` |
| Types not matching schema | Client out of date | Run `npx prisma generate` after schema changes |
| Multiple Prisma Client instances warning | Hot reload in dev | Use singleton pattern (see Client Setup) |
| `relation "X" does not exist` | Migration not applied | Run `npx prisma migrate dev` |
| `prisma db push` lost data | Push can be destructive | Use `migrate dev` instead for existing data |
| Slow queries | Missing indexes | Add `@@index` to schema, check with `EXPLAIN ANALYZE` |

## CRITICAL RULES

### MUST DO
- Always use `@map()` and `@@map()` for snake_case database naming when Prisma fields are camelCase
- Always use the singleton pattern for PrismaClient in development to prevent connection exhaustion
- Always use `prisma migrate dev` (not `db push`) when you need versioned, reproducible migrations
- Always include `include` or `select` explicitly — default queries do not load relations
- Use `$transaction` for operations that must be atomic
- Use `skipDuplicates: true` with `createMany` when appropriate
- Always use tagged template literals (`$queryRaw`) for raw SQL — never string concatenation

### MUST NOT DO
- NEVER use `db push` in production — it can drop columns/tables
- NEVER use `prisma migrate reset` in production — it drops the entire database
- NEVER construct raw SQL with string interpolation — use `$queryRaw` tagged templates
- NEVER omit `@updatedAt` on timestamp fields that should auto-update
- NEVER skip `npx prisma generate` after schema changes — TypeScript types will be stale
