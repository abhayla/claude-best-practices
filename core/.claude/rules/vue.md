---
paths:
  - "**/src/**/*.vue"
  - "**/src/**/*.ts"
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

## Anti-Patterns
- `window.dispatchEvent` for cross-component communication — use Pinia stores or `provide`/`inject` instead
- Oversized stores (>300 lines) — split into domain-scoped stores or extract logic to composables
- Direct state mutation of nested objects — create new references via spread operator or dedicated actions
