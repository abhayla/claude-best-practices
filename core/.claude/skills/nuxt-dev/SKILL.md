---
name: nuxt-dev
description: >
  Nuxt 4.3+ full-stack development: project setup, server routes, SSR/SSG, Nuxt Modules,
  NuxtHub (database/KV/blob/cache), Nuxt Content v3, Nuxt UI v4, nuxt-better-auth,
  auto-imports, middleware, composables, and deployment. Use for building Nuxt applications.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "nuxt, nuxt4, nuxt module, nuxthub, nuxt content, nuxt ui, nuxt auth, server routes, SSR"
argument-hint: "<feature-description or 'setup' or 'api' or 'module' or 'deploy'>"
version: "1.0.0"
type: workflow
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


**Read:** `references/server-functionality.md` for detailed step 2: server functionality reference material.

## STEP 3: Routing, Middleware & Plugins


**Read:** `references/routing-middleware-plugins.md` for detailed step 3: routing, middleware & plugins reference material.

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


**Read:** `references/nuxthub-v0106.md` for detailed step 5: nuxthub (v0.10.6) reference material.

# Deploy to Cloudflare (default)
npx nuxthub deploy

# Or via platform CLI
npx wrangler deploy
```

---

## STEP 6: Nuxt Content v3

Build content-driven applications with Markdown, YAML, and MDC.


**Read:** `references/nuxt-content-v3.md` for detailed step 6: nuxt content v3 reference material.

## STEP 7: Nuxt UI v4

Build interfaces with 125+ components, Tailwind CSS v4, and Tailwind Variants theming.


**Read:** `references/nuxt-ui-v4.md` for detailed step 7: nuxt ui v4 reference material.

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
