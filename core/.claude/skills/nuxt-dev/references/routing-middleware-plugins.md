# STEP 3: Routing, Middleware & Plugins

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

