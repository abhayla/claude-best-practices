---
name: nuxt-dev
description: >
  Nuxt 4.3+ full-stack development: project setup, server routes, SSR/SSG, Nuxt Modules,
  NuxtHub (database/KV/blob/cache), Nuxt Content v3, Nuxt UI v4, nuxt-better-auth,
  auto-imports, middleware, composables, and deployment. Use for building Nuxt applications.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "nuxt, nuxt4, nuxt module, nuxthub, nuxt content, nuxt ui, nuxt auth, server routes, SSR"
argument-hint: "<feature-description or 'setup' or 'api' or 'module' or 'deploy'>"
---

# Nuxt Development

Build full-stack Nuxt 4.3+ applications with auto-imports, server routes, SSR/SSG, and the Nuxt ecosystem.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup & Configuration

Scaffold or verify the Nuxt project structure.

### Create New Project

```bash
npx nuxi@latest init my-app
cd my-app
npm install
```

### Project Structure

```
app/
  pages/              # File-based routing
  components/         # Auto-imported components
  composables/        # Auto-imported composables
  layouts/            # Layout components
  middleware/         # Route middleware
  plugins/            # Nuxt plugins
  assets/             # Processed assets (CSS, images)
  utils/              # Auto-imported utility functions
public/               # Static assets (served at /)
server/
  api/                # API routes (/api/*)
  routes/             # Server routes (any path)
  middleware/         # Server middleware
  plugins/            # Nitro plugins
  utils/              # Server utilities (auto-imported)
  db/
    schema.ts         # Drizzle ORM schema (NuxtHub)
    migrations/       # Database migrations
content/              # Markdown/YAML content (Nuxt Content)
nuxt.config.ts        # Nuxt configuration
app.config.ts         # Runtime app configuration
```

### nuxt.config.ts Essentials

```typescript
export default defineNuxtConfig({
  future: { compatibilityVersion: 4 },
  compatibilityDate: '2025-01-01',

  modules: [
    // Add modules here
  ],

  devtools: { enabled: true },

  // Auto-imports are enabled by default for:
  // - Vue APIs (ref, computed, watch, etc.)
  // - Nuxt composables (useRoute, useFetch, etc.)
  // - Components in components/
  // - Composables in composables/
  // - Utils in utils/
})
```

### app.config.ts (Runtime Config)

```typescript
// Runtime configuration accessible client-side (no secrets)
export default defineAppConfig({
  ui: {
    primary: 'green',
    gray: 'slate',
  },
})
```

### Verify Setup

```bash
npm run dev
npx nuxi typecheck
```

---

## STEP 2: Server Functionality

Define API routes, validation, WebSocket, and SSE handlers using Nitro.

### API Routes (defineEventHandler)

```typescript
// server/api/users.get.ts — GET /api/users
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  // Return data directly — auto-serialized to JSON
  return { users: [] }
})

// server/api/users.post.ts — POST /api/users
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  // Validate and create user
  return { id: 1, ...body }
})

// server/api/users/[id].get.ts — GET /api/users/:id
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  return { id }
})
```

### Input Validation

```typescript
// server/api/users.post.ts
export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, (data) => {
    // Use Zod or manual validation
    if (!data?.email) throw createError({ statusCode: 400, message: 'Email required' })
    return data as { email: string; name: string }
  })
  return body
})
```

### Error Handling

```typescript
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const item = await findItem(id)
  if (!item) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Item not found',
    })
  }
  return item
})
```

### WebSocket Handler

```typescript
// server/routes/_ws.ts
export default defineWebSocketHandler({
  open(peer) {
    peer.send(JSON.stringify({ message: 'Connected' }))
    peer.subscribe('chat')
  },
  message(peer, message) {
    peer.publish('chat', message.text())
  },
  close(peer) {
    peer.unsubscribe('chat')
  },
})
```

### Server-Sent Events (SSE)

```typescript
// server/api/stream.get.ts
export default defineEventHandler(async (event) => {
  const stream = createEventStream(event)
  let count = 0
  const interval = setInterval(async () => {
    await stream.push({ data: JSON.stringify({ count: ++count }) })
  }, 1000)
  stream.onClosed(() => clearInterval(interval))
  return stream.send()
})
```

---

## STEP 3: Routing, Middleware & Plugins

### File-Based Routing

```
app/pages/
  index.vue           # /
  about.vue           # /about
  users/
    index.vue         # /users
    [id].vue          # /users/:id
  posts/
    [...slug].vue     # /posts/* (catch-all)
  (admin)/            # Route group (no /admin prefix)
    dashboard.vue     # /dashboard
    settings.vue      # /settings
```

### Typed Router

```typescript
// Navigating with auto-generated typed routes
const router = useRouter()
router.push({ name: 'users-id', params: { id: '42' } })

// In template
// <NuxtLink :to="{ name: 'users-id', params: { id: user.id } }">Profile</NuxtLink>
```

### Route Middleware

```typescript
// app/middleware/auth.ts — named middleware
export default defineNuxtRouteMiddleware((to, from) => {
  const { loggedIn } = useUserSession()
  if (!loggedIn.value) {
    return navigateTo('/login')
  }
})

// Usage in page: definePageMeta({ middleware: 'auth' })
// Global middleware: rename to auth.global.ts
```

### Plugins

```typescript
// app/plugins/api.ts — auto-registered
export default defineNuxtPlugin((nuxtApp) => {
  const api = $fetch.create({
    baseURL: '/api',
    onRequest({ options }) {
      const { session } = useUserSession()
      if (session.value?.token) {
        options.headers.set('Authorization', `Bearer ${session.value.token}`)
      }
    },
  })
  return { provide: { api } }
})
```

### Core Nuxt Components

| Component | Purpose |
|-----------|---------|
| `<NuxtPage />` | Renders matched route page (replaces `<Nuxt />` in v4) |
| `<NuxtLink to="/path">` | Client-side navigation link |
| `<NuxtLayout name="custom">` | Wraps page in layout |
| `<NuxtLoadingIndicator />` | Top loading bar during navigation |
| `<NuxtErrorBoundary>` | Catches and displays component errors |
| `<ClientOnly>` | Renders children only on client side |
| `<NuxtImg>` | Optimized image component (@nuxt/image) |

### Key Composables

| Composable | Purpose |
|------------|---------|
| `useFetch(url)` | SSR-friendly data fetching with caching |
| `useAsyncData(key, fn)` | SSR-friendly async data with dedup |
| `$fetch(url)` | Direct fetch (no SSR dedup, use in event handlers) |
| `useRoute()` | Current route info (params, query, path) |
| `useRouter()` | Programmatic navigation |
| `useState(key, init)` | SSR-safe shared reactive state |
| `useRuntimeConfig()` | Access runtime config (public/private) |
| `useHead({})` | Set page meta/title/scripts |
| `useSeoMeta({})` | Set SEO meta tags |
| `useAppConfig()` | Access app.config.ts values |
| `navigateTo(path)` | Redirect (works in middleware and setup) |

---

## STEP 4: Nuxt Modules

Create, use, and test Nuxt modules.

### Module Types

| Type | Location | Use Case |
|------|----------|----------|
| Published | npm package | Shared across projects |
| Local | `modules/` directory | Project-specific extensions |
| Inline | `nuxt.config.ts` modules array | Quick config tweaks |

### Creating a Module

```bash
npx nuxi init -t module my-module
```

### Module Structure

```
my-module/
  src/
    module.ts           # Entry point (defineNuxtModule)
    runtime/            # Injected into user's app
      composables/      # Auto-imported composables
      components/       # Auto-imported components
      server/           # Server routes/middleware
      plugins/          # Client/server plugins
  playground/           # Dev app for testing
  test/
    fixtures/           # Test app fixtures
    basic.test.ts       # E2E tests
```

### defineNuxtModule

```typescript
// src/module.ts
import { defineNuxtModule, createResolver, addImportsDir, addComponentsDir } from '@nuxt/kit'

export default defineNuxtModule({
  meta: {
    name: 'my-module',
    configKey: 'myModule',
  },
  defaults: {
    enabled: true,
  },
  setup(options, nuxt) {
    if (!options.enabled) return

    const resolver = createResolver(import.meta.url)

    // Auto-import composables from runtime/composables/
    addImportsDir(resolver.resolve('runtime/composables'))

    // Auto-import components from runtime/components/
    addComponentsDir({ path: resolver.resolve('runtime/components') })

    // Add server routes
    nuxt.options.nitro.scanDirs ||= []
    nuxt.options.nitro.scanDirs.push(resolver.resolve('runtime/server'))
  },
})
```

### Testing Modules

```typescript
// test/basic.test.ts
import { describe, it, expect } from 'vitest'
import { setup, $fetch } from '@nuxt/test-utils/e2e'

describe('my-module', async () => {
  await setup({
    rootDir: './test/fixtures/basic',
  })

  it('renders the index page', async () => {
    const html = await $fetch('/')
    expect(html).toContain('Hello from module')
  })
})
```

---

## STEP 5: NuxtHub (v0.10.6)

Full-stack platform features: database, KV, blob storage, cache, and deployment.

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
# Deploy to Cloudflare (default)
npx nuxthub deploy

# Or via platform CLI
npx wrangler deploy
```

---

## STEP 6: Nuxt Content v3

Build content-driven applications with Markdown, YAML, and MDC.

### Enable Nuxt Content

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],
})
```

### Collection Types

| Type | Purpose | Has Route | Has Body |
|------|---------|-----------|----------|
| `page` | Routable content (blog posts, docs) | Yes | Yes |
| `data` | Structured data (authors, config) | No | No |

### Define Collections

```typescript
// content.config.ts
import { defineCollection, defineContentConfig, z } from '@nuxt/content'

export default defineContentConfig({
  collections: {
    blog: defineCollection({
      type: 'page',
      source: 'blog/**',
      schema: z.object({
        title: z.string(),
        description: z.string(),
        date: z.date(),
        tags: z.array(z.string()).optional(),
        image: z.string().optional(),
      }),
    }),
    authors: defineCollection({
      type: 'data',
      source: 'authors/**',
      schema: z.object({
        name: z.string(),
        avatar: z.string(),
        twitter: z.string().optional(),
      }),
    }),
  },
})
```

### Query Collections

```vue
<script setup>
// Query page collection
const { data: posts } = await useAsyncData('blog', () =>
  queryCollection('blog')
    .order('date', 'DESC')
    .limit(10)
    .all()
)

// Query single item
const route = useRoute()
const { data: post } = await useAsyncData(`blog-${route.params.slug}`, () =>
  queryCollection('blog')
    .path(route.path)
    .first()
)
</script>
```

### Render Content (MDC)

```vue
<template>
  <ContentRenderer v-if="post" :value="post" />
</template>
```

### Remote Sources

```typescript
// content.config.ts — fetch from GitHub
export default defineContentConfig({
  collections: {
    docs: defineCollection({
      type: 'page',
      source: {
        repository: 'https://github.com/org/repo',
        path: 'docs/**',
      },
    }),
  },
})
```

---

## STEP 7: Nuxt UI v4

Build interfaces with 125+ components, Tailwind CSS v4, and Tailwind Variants theming.

### Enable Nuxt UI

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
})
```

### UApp Wrapper (Required)

```vue
<!-- app.vue — wrap entire app for Toast, Tooltip, and overlay support -->
<template>
  <UApp>
    <NuxtPage />
  </UApp>
</template>
```

### Component Examples

```vue
<template>
  <!-- Button with variants -->
  <UButton label="Save" color="primary" variant="solid" size="lg" />

  <!-- Form with validation -->
  <UForm :schema="schema" :state="state" @submit="onSubmit">
    <UFormField label="Email" name="email">
      <UInput v-model="state.email" type="email" />
    </UFormField>
    <UFormField label="Password" name="password">
      <UInput v-model="state.password" type="password" />
    </UFormField>
    <UButton type="submit" label="Login" />
  </UForm>

  <!-- Table -->
  <UTable :data="users" :columns="columns" />

  <!-- Modal overlay -->
  <UModal v-model:open="isOpen">
    <template #header>Confirm</template>
    <p>Are you sure?</p>
    <template #footer>
      <UButton label="Cancel" @click="isOpen = false" />
      <UButton label="Confirm" color="primary" @click="confirm" />
    </template>
  </UModal>
</template>
```

### Theming (Tailwind CSS v4 + Tailwind Variants)

```css
/* app/assets/css/main.css */
@import "tailwindcss";
@import "@nuxt/ui";

@theme {
  --color-primary-50: #f0fdf4;
  --color-primary-500: #22c55e;
  --color-primary-900: #14532d;
}
```

### Key Composables

| Composable | Purpose |
|------------|---------|
| `useToast()` | Show toast notifications |
| `useOverlay()` | Programmatic overlays (modal, slideover, drawer) |
| `useModal()` | Open/close modals programmatically |

```typescript
const toast = useToast()
toast.add({ title: 'Saved', description: 'Changes saved successfully', color: 'success' })

const overlay = useOverlay()
const result = await overlay.open(ConfirmDialog, { title: 'Delete?' })
```

---

## STEP 8: Authentication (nuxt-better-auth)

Session-based auth with Better Auth integration.

### Enable Auth

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['nuxt-better-auth'],
})
```

### Client-Side Auth

```vue
<script setup>
const { loggedIn, user, session, clear: logout } = useUserSession()
</script>

<template>
  <div v-if="loggedIn">
    <p>Welcome, {{ user.name }}</p>
    <UButton label="Logout" @click="logout()" />
  </div>
  <div v-else>
    <NuxtLink to="/login">Login</NuxtLink>
  </div>
</template>
```

### Server-Side Auth

```typescript
// server/api/profile.get.ts
export default defineEventHandler(async (event) => {
  // Throws 401 if not authenticated
  const session = await requireUserSession(event)
  return { user: session.user }
})
```

### Route Protection

```typescript
// nuxt.config.ts — protect via routeRules
export default defineNuxtConfig({
  routeRules: {
    '/dashboard/**': { appMiddleware: 'auth' },
  },
})
```

```typescript
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession()
  if (!loggedIn.value) {
    return navigateTo('/login')
  }
})
```

### Auth Plugins

```typescript
// server/plugins/auth.ts — add Better Auth plugins
import { admin, twoFactor } from 'better-auth/plugins'

export default defineNitroPlugin(() => {
  // Plugins configured via nuxt.config.ts betterAuth key
})
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `500` on API route | Missing `await` on async operation or unhandled error | Add `try/catch` or use `createError()` for expected errors |
| Component not found | Not in `components/` or missing module registration | Check auto-import dirs; run `npx nuxi typecheck` |
| Hydration mismatch | Server/client HTML differs (dynamic dates, browser APIs) | Wrap browser-only code in `<ClientOnly>` or `onMounted` |
| `useFetch` returns null on client nav | Missing or mismatched `key` parameter | Provide unique `key` to `useAsyncData`/`useFetch` |
| Module not loading | Module not added to `modules` array in config | Add to `nuxt.config.ts` modules; restart dev server |
| DB migration fails | Schema mismatch or pending migrations | Run `npx nuxt db generate` then `npx nuxt db migrate` |
| KV/Blob not available | Hub features not enabled in config | Set `hub: { kv: true, blob: true }` in `nuxt.config.ts` |
| Content not rendering | Collection not defined or wrong source path | Check `content.config.ts` collection source glob |
| Nuxt UI overlay not working | Missing `<UApp>` wrapper in `app.vue` | Wrap root template with `<UApp>` component |
| Auth session undefined | `useUserSession` called outside setup or missing module | Call in `<script setup>` and ensure module is registered |
| TypeScript errors after update | Stale generated types | Run `npx nuxi prepare` to regenerate `.nuxt/` types |
| Build fails on Cloudflare | Unsupported Node API in edge runtime | Use Nitro-compatible APIs; check `nitro.preset` setting |

---

## CRITICAL RULES

### MUST DO

- Use `defineEventHandler` for all server routes — never export raw functions
- Use `useFetch` or `useAsyncData` for data fetching in pages/components — they handle SSR dedup and caching
- Wrap app in `<UApp>` when using Nuxt UI — required for toasts, tooltips, and overlays
- Run `npx nuxi typecheck` before committing — catches auto-import and type issues
- Use `createError()` for expected server errors — provides proper HTTP status codes
- Define database schema in `server/db/schema.ts` — NuxtHub auto-imports `db` and `schema`
- Run `npx nuxt db generate` after schema changes — then `npx nuxt db migrate`
- Use `<NuxtPage />` in Nuxt 4 — `<Nuxt />` is removed
- Define content collections with Zod schemas in `content.config.ts`
- Use `navigateTo()` for redirects in middleware — return the result

### MUST NOT DO

- Use `$fetch` in components for initial data loading — use `useFetch` instead (`$fetch` causes duplicate requests during SSR)
- Access `window`, `document`, or browser APIs outside `onMounted` or `<ClientOnly>` — breaks SSR
- Put secrets in `app.config.ts` or `runtimeConfig.public` — use `runtimeConfig` (private, server-only) with env vars instead
- Mutate `useState` values directly from server routes — `useState` is client/SSR state only
- Skip the `key` parameter in `useAsyncData` when routes share a data source — causes stale data on navigation
- Use `hub:` storage prefixes in client code — `db`, `kv`, `blob` are server-only auto-imports
- Import from `#imports` explicitly — auto-imports handle this; explicit imports cause duplication
- Use deprecated NuxtHub features (hubAI, hubBrowser, hubVectorize) — removed in v0.10
- Register modules in both `modules` and `buildModules` — Nuxt 4 uses only `modules`
- Use `nuxt-better-auth` in production without evaluating its alpha status (v0.0.2-alpha) — implement fallback auth strategies
