---
name: drizzle-orm
description: >
  Drizzle ORM schema design, migrations, queries, and relations for TypeScript projects.
  Use when working with Drizzle ORM in any TypeScript backend (Next.js, Bun, Hono, Express).
allowed-tools: "Read Grep Glob"
argument-hint: "[schema|migrate|query|relations]"
version: "1.0.0"
type: reference
triggers: drizzle, drizzle-orm, drizzle-kit
---

# Drizzle ORM Reference

Drizzle ORM with drizzle-kit for TypeScript projects using PostgreSQL, MySQL, or SQLite.

## Schema Definition

### Table Definitions (PostgreSQL)

```typescript
// db/schema/users.ts
import { pgTable, uuid, varchar, timestamp, boolean, integer } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: varchar("email", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  isActive: boolean("is_active").notNull().default(true),
  loginCount: integer("login_count").notNull().default(0),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});
```

### Column Type Quick Reference

| TypeScript | PostgreSQL | Notes |
|------------|-----------|-------|
| `uuid()` | `UUID` | Use `.defaultRandom()` for auto-gen |
| `serial()` | `SERIAL` | Auto-incrementing integer |
| `varchar("col", { length: N })` | `VARCHAR(N)` | Always specify length |
| `text()` | `TEXT` | Unlimited length |
| `integer()` | `INTEGER` | 32-bit |
| `bigint("col", { mode: "number" })` | `BIGINT` | Use `mode: "bigint"` for BigInt type |
| `boolean()` | `BOOLEAN` | — |
| `timestamp("col", { withTimezone: true })` | `TIMESTAMPTZ` | Always use timezone |
| `jsonb()` | `JSONB` | Use for structured JSON data |
| `real()` | `REAL` | 32-bit float |
| `doublePrecision()` | `DOUBLE PRECISION` | 64-bit float |
| `decimal("col", { precision: 10, scale: 2 })` | `DECIMAL(10,2)` | Exact numeric |
| `pgEnum("name", [...])` | `ENUM` | Define outside table |

### Enums

```typescript
import { pgEnum } from "drizzle-orm/pg-core";

export const statusEnum = pgEnum("status", ["active", "inactive", "pending"]);

export const orders = pgTable("orders", {
  id: uuid("id").primaryKey().defaultRandom(),
  status: statusEnum("status").notNull().default("pending"),
});
```

### Indexes and Constraints

```typescript
import { pgTable, uuid, varchar, index, uniqueIndex } from "drizzle-orm/pg-core";

export const products = pgTable("products", {
  id: uuid("id").primaryKey().defaultRandom(),
  sku: varchar("sku", { length: 50 }).notNull(),
  categoryId: uuid("category_id").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
}, (table) => [
  uniqueIndex("products_sku_idx").on(table.sku),
  index("products_category_idx").on(table.categoryId),
]);
```

## Relations

```typescript
// db/schema/relations.ts
import { relations } from "drizzle-orm";
import { users } from "./users";
import { posts } from "./posts";
import { comments } from "./comments";

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one, many }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
  comments: many(comments),
}));

export const commentsRelations = relations(comments, ({ one }) => ({
  post: one(posts, {
    fields: [comments.postId],
    references: [posts.id],
  }),
  author: one(users, {
    fields: [comments.authorId],
    references: [users.id],
  }),
}));
```

**Key rule**: Relations are declared separately from table schemas. They do NOT create foreign keys — use `.references(() => otherTable.col)` on columns for actual FK constraints.

### Foreign Key Columns

```typescript
export const posts = pgTable("posts", {
  id: uuid("id").primaryKey().defaultRandom(),
  authorId: uuid("author_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  title: varchar("title", { length: 255 }).notNull(),
});
```

## Migrations with drizzle-kit

### Configuration

```typescript
// drizzle.config.ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./db/schema/*",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

### Migration Commands

```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply pending migrations
npx drizzle-kit migrate

# Push schema directly (dev only — no migration files)
npx drizzle-kit push

# Open Drizzle Studio (visual DB browser)
npx drizzle-kit studio

# Drop a migration (remove last generated file)
npx drizzle-kit drop

# Check for schema drift
npx drizzle-kit check
```

### Migration Workflow

1. Modify schema files in `db/schema/`
2. Run `npx drizzle-kit generate` — creates SQL migration in `drizzle/` folder
3. Review the generated `.sql` file for correctness
4. Run `npx drizzle-kit migrate` to apply
5. Commit both schema changes and migration files

## Database Client Setup

```typescript
// db/index.ts
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

export const db = drizzle(pool, { schema });
```

### With Bun (postgres.js driver)

```typescript
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client, { schema });
```

### With Neon Serverless

```typescript
import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import * as schema from "./schema";

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle(sql, { schema });
```

## Query Patterns

### Select Queries

```typescript
// Basic select
const allUsers = await db.select().from(users);

// With conditions
import { eq, and, or, gt, like, inArray, isNull, between } from "drizzle-orm";

const activeUsers = await db.select().from(users).where(eq(users.isActive, true));

const filtered = await db.select().from(users).where(
  and(
    eq(users.isActive, true),
    gt(users.loginCount, 5),
    like(users.email, "%@example.com"),
  )
);

// Select specific columns
const names = await db.select({ name: users.name, email: users.email }).from(users);

// With ordering and pagination
const page = await db.select().from(users)
  .orderBy(users.createdAt)
  .limit(20)
  .offset(40);
```

### Relational Queries (Query API)

```typescript
// Fetch with relations (requires relations defined + schema passed to drizzle())
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: {
      with: { comments: true },
      limit: 10,
      orderBy: (posts, { desc }) => [desc(posts.createdAt)],
    },
  },
  where: (users, { eq }) => eq(users.isActive, true),
});

// Find one
const user = await db.query.users.findFirst({
  where: (users, { eq }) => eq(users.id, userId),
  with: { posts: true },
});
```

### Joins

```typescript
// Inner join
const result = await db.select({
  userName: users.name,
  postTitle: posts.title,
}).from(users)
  .innerJoin(posts, eq(users.id, posts.authorId));

// Left join
const result = await db.select().from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));
```

### Insert

```typescript
// Single insert
const [newUser] = await db.insert(users).values({
  email: "user@example.com",
  name: "Test User",
}).returning();

// Bulk insert
await db.insert(users).values([
  { email: "a@example.com", name: "A" },
  { email: "b@example.com", name: "B" },
]);

// Upsert (insert or update on conflict)
await db.insert(users).values({
  email: "user@example.com",
  name: "Updated Name",
}).onConflictDoUpdate({
  target: users.email,
  set: { name: "Updated Name", updatedAt: new Date() },
});
```

### Update

```typescript
const [updated] = await db.update(users)
  .set({ isActive: false, updatedAt: new Date() })
  .where(eq(users.id, userId))
  .returning();
```

### Delete

```typescript
await db.delete(users).where(eq(users.id, userId));
```

### Transactions

```typescript
const result = await db.transaction(async (tx) => {
  const [user] = await tx.insert(users).values({ email, name }).returning();
  await tx.insert(posts).values({ authorId: user.id, title: "First Post" });
  return user;
});
```

## Drizzle-Zod Integration

```typescript
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { users } from "./schema/users";

// Auto-generate Zod schemas from Drizzle tables
export const insertUserSchema = createInsertSchema(users, {
  email: (schema) => schema.email(),
  name: (schema) => schema.min(1).max(255),
});

export const selectUserSchema = createSelectSchema(users);

// Use for validation
const validated = insertUserSchema.parse(requestBody);
```

## Schema Organization

```
db/
├── schema/
│   ├── index.ts          # Re-exports all tables and relations
│   ├── users.ts          # User table
│   ├── posts.ts          # Posts table
│   ├── comments.ts       # Comments table
│   └── relations.ts      # All relation definitions
├── index.ts              # Database client instance
└── seed.ts               # Seed script
drizzle/
├── 0000_initial.sql      # Generated migrations
├── 0001_add_posts.sql
└── meta/                 # drizzle-kit metadata
drizzle.config.ts          # drizzle-kit configuration
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `relation "X" does not exist` | Migration not applied | Run `npx drizzle-kit migrate` |
| Relations return empty | Schema not passed to `drizzle()` | Pass `{ schema }` in drizzle client setup |
| `findMany`/`findFirst` not available | Using `db.select()` instead of `db.query` | Use `db.query.tableName.findMany()` for relational queries |
| Type errors on insert | Missing required field | Check which columns lack `.default()` or `.notNull()` |
| Migration conflicts | Multiple developers generating | Coordinate or use `npx drizzle-kit check` |
| `push` vs `migrate` confusion | `push` skips migration files | Use `push` in dev only, `migrate` in prod |

## CRITICAL RULES

### MUST DO
- Always use `withTimezone: true` for timestamp columns
- Always define relations in a separate file from table schemas
- Always review generated migration SQL before applying
- Always commit migration files alongside schema changes
- Use `drizzle-zod` for input validation at API boundaries
- Pass `{ schema }` to `drizzle()` to enable relational query API
- Use `.references()` on columns for actual FK constraints (relations alone do NOT create FKs)

### MUST NOT DO
- NEVER use `npx drizzle-kit push` in production — use `migrate` with versioned SQL files
- NEVER modify generated migration SQL files after they have been applied
- NEVER put relation definitions inside `pgTable()` calls — they are separate
- NEVER use `db.select()` when you need nested relation data — use `db.query` API instead
