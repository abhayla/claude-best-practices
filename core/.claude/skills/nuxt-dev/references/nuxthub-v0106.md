# STEP 5: NuxtHub (v0.10.6)

### Enable NuxtHub

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxthub/core'],
  hub: {
    database: true,
    kv: true,
    blob: true,
    cache: true,
  },
})
```

### Database (Drizzle ORM)

```typescript
// server/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
})
```

```typescript
// server/api/users.get.ts — db and schema are auto-imported
export default defineEventHandler(async () => {
  return await db.select().from(schema.users)
})

// server/api/users.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const [user] = await db.insert(schema.users).values(body).returning()
  return user
})
```

**Migration Commands:**

```bash
npx nuxt db generate    # Generate migration from schema changes
npx nuxt db migrate     # Apply pending migrations
npx nuxt db sql         # Open interactive SQL console
npx nuxt db drop        # Drop all tables
npx nuxt db squash      # Squash migrations into one
```

**Database Providers:**

| Provider | Driver | Use Case |
|----------|--------|----------|
| D1 (Cloudflare) | Default | Production on Cloudflare |
| Turso | `libsql` | Edge-distributed SQLite |
| PGlite | `pglite` | Embedded Postgres |
| postgres-js | `postgres` | Standard PostgreSQL |
| neon-http | `neon-http` | Serverless Postgres |
| mysql2 | `mysql2` | MySQL databases |

### KV Storage

```typescript
// server/api/settings.get.ts — kv is auto-imported
export default defineEventHandler(async () => {
  return await kv.get('app:settings')
})

// server/api/settings.put.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  await kv.set('app:settings', body, { ttl: 3600 }) // TTL in seconds
  return { ok: true }
})

// Other KV operations
await kv.has('key')           // Check existence
await kv.del('key')           // Delete
await kv.keys('app:')         // List keys by prefix
await kv.clear('app:')        // Clear by prefix
```

**KV Providers:** Upstash, Redis, Cloudflare KV, Deno KV, Vercel KV.

### Blob Storage

```typescript
// server/api/files.get.ts — blob is auto-imported
export default defineEventHandler(async () => {
  return await blob.list({ prefix: 'uploads/' })
})

// server/api/files.post.ts
export default defineEventHandler(async (event) => {
  return await blob.handleUpload(event, {
    multiple: true,
    ensure: { maxSize: '10MB', types: ['image/png', 'image/jpeg'] },
    put: { prefix: 'uploads/' },
  })
})

// server/api/files/[...path].get.ts — serve blob
export default defineEventHandler(async (event) => {
  const path = getRouterParam(event, 'path')
  return blob.serve(event, path!)
})

// Delete
await blob.del('uploads/photo.png')
// Or batch delete
await blob.del(['uploads/a.png', 'uploads/b.png'])
```

**Client-side upload composable:**

```vue
<script setup>
const upload = useUpload('/api/files', { method: 'POST' })

async function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) {
    const result = await upload(files)
  }
}
</script>
```

**Blob Providers:** R2 (Cloudflare), Vercel Blob, S3-compatible.

### Cache

```typescript
// server/api/stats.get.ts
export default cachedEventHandler(async () => {
  // Expensive computation cached automatically
  const stats = await computeStats()
  return stats
}, {
  maxAge: 60 * 60,    // Cache for 1 hour
  swr: true,          // Stale-while-revalidate
  name: 'stats',
})

// Programmatic cache invalidation
await defineCachedFunction(fn, { maxAge: 300, name: 'myCache' })
```

### Deployment Targets

| Platform | Config |
|----------|--------|
| Cloudflare | Default, auto-generates `wrangler.json` |
| Vercel | `NITRO_PRESET=vercel` |
| Netlify | `NITRO_PRESET=netlify` |
| Deno Deploy | `NITRO_PRESET=deno-deploy` |
| AWS Lambda | `NITRO_PRESET=aws-lambda` |

```bash
