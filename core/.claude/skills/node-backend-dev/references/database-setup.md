# Database Setup & Service Layer


### ORM Decision Table

| ORM         | Best For                       | Migrations      | Query Style          |
|-------------|--------------------------------|-----------------|----------------------|
| Prisma      | Type-safe, declarative schema  | prisma migrate  | Client methods       |
| Drizzle     | SQL-like, lightweight          | drizzle-kit     | Fluent builder       |
| pg (raw)    | Simple APIs, full control      | Manual SQL files | Parameterized queries|

### Prisma Singleton

Prevents connection pool exhaustion from hot reloads in development.

```typescript
// src/db/index.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'warn', 'error'] : ['error'],
});

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

// Graceful shutdown
process.on('SIGTERM', async () => {
  await prisma.$disconnect();
});
```

### Drizzle Setup

```typescript
// src/db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const client = postgres(process.env.DATABASE_URL!, {
  max: 10,
  idle_timeout: 20,
  connect_timeout: 10,
});

export const db = drizzle(client, { schema });

// Graceful shutdown
export async function closeDb() {
  await client.end();
}

// Schema example â€” src/db/schema/users.ts
import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});
```

### Raw pg Pool

```typescript
// src/db/index.ts
import { Pool } from 'pg';

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 15,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
});

// Always use parameterized queries
const result = await pool.query('SELECT * FROM users WHERE id = $1', [id]);

// Graceful shutdown
process.on('SIGTERM', async () => {
  await pool.end();
});
```

### Service Layer Pattern

Services encapsulate business logic. They receive validated data and interact with the database.

```typescript
// src/services/user.service.ts
import { prisma } from '../db';
import { CreateUserInput } from '../types/user.schema';

export const UserService = {
  async findById(id: string) {
    return prisma.user.findUnique({ where: { id } });
  },

  async create(data: CreateUserInput) {
    return prisma.user.create({ data });
  },

  async list(page: number, limit: number) {
    const skip = (page - 1) * limit;
    const [users, total] = await Promise.all([
      prisma.user.findMany({ skip, take: limit, orderBy: { createdAt: 'desc' } }),
      prisma.user.count(),
    ]);
    return { users, total, page, limit };
  },
};
```
