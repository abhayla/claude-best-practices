---
globs: ["**/src/**/*.vue", "**/src/**/*.ts"]
description: Vue 3 Composition API patterns and conventions.
---

# Vue 3 Rules

## Composition API
- Use `<script setup lang="ts">` exclusively — never Options API
- Props via `defineProps<{}>()` with TypeScript interfaces — never `defineProps({})` object syntax
- Emits via `defineEmits<{}>()` with typed signatures

## Pinia State Management
- Setup-style stores only: `defineStore('name', () => { ... })` — never mix with options-style `{ state, getters, actions }`
- Use `storeToRefs()` when destructuring reactive state from stores — plain destructuring loses reactivity
- Keep stores thin for UI state — use TanStack Vue Query or composables for server state when available

## Composables
- Composables are the public API surface for components — components never call `fetch()` or API clients directly
- Co-locate types with composables or import from `src/types/`
- Return reactive refs and computed properties — never return raw promises

## Router
- Lazy-load all route components: `() => import('./pages/Feature.vue')` — never eagerly import views
- Auth guards in `beforeEach` — check session/token before allowing navigation
- Use `meta: { requiresAuth: true }` for protected routes — never check auth inside page components

## Component Organization
- Feature-based folders under `components/` — never organize by component type (buttons/, cards/)
- `data-testid` attribute on all interactive elements — convention: `[screen]-[component]-[element]`
- Extract reusable UI primitives to `components/ui/`

## State Primitives & Server/Client Split

Use `ref()` for all state — NEVER `reactive()`. `reactive()` loses reactivity on destructure and cannot be reassigned wholesale; standardizing on `ref()` avoids both gotchas.

```ts
// CORRECT
const user = ref<User | null>(null)
// WRONG — never reactive()
const state = reactive({ user: null })
```

Split state by lifetime — never store server data in Pinia, never use Vue Query for client-only state:

| Concern | Tool |
|---|---|
| Client UI state (sidebar, theme, view mode) | Pinia |
| Auth session (current user, sign-out) | Pinia |
| Server-fetched data / mutations | TanStack Vue Query |

This keeps cache invalidation, stale-while-revalidate, and background refetch working in Vue Query without fighting Pinia's synchronous reactivity.

## URL ↔ Query-Param Sync

Sync component state with URL query params via a computed getter/setter so views are deep-linkable, bookmarkable, and survive refresh.

```ts
const route = useRoute(); const router = useRouter()
const activeTab = computed({
  get: () => (route.query.tab as string) || 'overview',
  set: (val) => router.push({ query: { ...route.query, tab: val === 'overview' ? undefined : val } }),
})
```

- When the value equals its default, set the param to `undefined` to drop it from the URL (`/items`, not `/items?tab=overview`)
- Always spread `...route.query` so other active params survive the update
- Bind directly to Vuetify tabs: `<v-tabs v-model="activeTab">`

## Two-Tier Form Validation

Pick the validation tier by form complexity:

- **Simple (< ~5 fields, no cross-field rules):** plain `ref()` + `v-model` with manual `:rules` + a computed validity check
- **Complex (5+ fields, conditional/cross-field rules):** `vee-validate` + Zod via `useForm({ validationSchema: toTypedSchema(schema) })` + `defineField()`

Dialog forms use a `v-model` computed; reset on open and populate on edit via watches. Use `v-if` (inside `v-expand-transition`), NOT `v-show`, for conditional sections — hidden `v-show` fields still participate in validation.

## API Response Unwrapping

Every consumer of an enveloped endpoint (see `hono-conventions.md`) MUST unwrap via shared helpers (`unwrapResponse` / `unwrapArrayResponse`). NEVER index `.data.data` — it hides the error branch and silently swallows failures.

- `unwrapResponse<T>(json)` validates the envelope, throws the server's error message on `success: false`, returns `data`
- Unwrap inside the Vue Query `queryFn` so the component only sees the unwrapped type; the thrown error populates `error.value` — do not `try/catch` it into `null`
- Stores that fetch directly MUST also unwrap — assigning the raw `{ success, data }` envelope to state breaks every downstream `.map()` / `.filter()`

## Anti-Patterns
- `window.dispatchEvent` for cross-component communication — use Pinia stores or `provide`/`inject` instead
- Oversized stores (>300 lines) — split into domain-scoped stores or extract logic to composables
- Direct state mutation of nested objects — create new references via spread operator or dedicated actions
