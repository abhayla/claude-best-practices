---
name: vue-dev
description: >
  Build Vue 3.5+ applications using Composition API patterns, TypeScript integration,
  Reka UI headless components, Vue Router, composables, VueUse, testing with Vitest,
  and project architecture. Use when developing Vue 3 applications with modern patterns.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "vue, vue3, composition api, composable, vue component, vue router, reka-ui"
argument-hint: "<feature-description or 'setup' or 'test' or 'composable' or 'component'>"
version: "1.0.0"
type: workflow
---

# Vue 3 Development

Build Vue 3.5+ applications with Composition API, TypeScript, Reka UI headless primitives, and modern tooling.

**Request:** $ARGUMENTS

---

## STEP 1: Setup

Scaffold or verify the Vue 3 project structure.

### Project Structure

```
src/
  assets/              # Static assets, global CSS
  components/
    ui/                # Base UI components (buttons, inputs, cards)
    layout/            # Layout components (header, sidebar, footer)
    [feature]/         # Feature-scoped components
  composables/         # Shared composables (useAuth, useApi, useForm)
  directives/          # Custom directives (v-focus, v-click-outside)
  lib/                 # Utilities, helpers, constants
  pages/               # Route-level views (if using file-based routing)
  router/
    index.ts           # Router instance and route definitions
    guards.ts          # Navigation guards
  stores/              # Pinia stores (if using Pinia)
  types/               # Shared TypeScript types and interfaces
  App.vue              # Root component
  main.ts              # Entry point
```

### Dependencies (package.json essentials)

```json
{
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "reka-ui": "^2.8.0",
    "@vueuse/core": "^12.0.0",
    "pinia": "^3.0.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-vue": "^5.2.0",
    "vitest": "^3.0.0",
    "@vue/test-utils": "^2.4.0",
    "vue-tsc": "^2.2.0"
  }
}
```

### Entry Point

```ts
// main.ts
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from './App.vue'
import { routes } from './router'

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

### Verify Setup

```bash
npm run type-check   # vue-tsc --noEmit
npm run dev          # vite dev server
```

Fix all type errors before proceeding.

---

## STEP 2: Reactivity and Composition API

Use the Composition API with `<script setup>` for all components. Vue 3.5+ patterns only.


**Read:** `references/reactivity-and-composition-api.md` for detailed step 2: reactivity and composition api reference material.

## STEP 3: Component Patterns


**Read:** `references/component-patterns.md` for detailed step 3: component patterns reference material.

## STEP 4: Composables

Write composables for reusable stateful logic. Follow the `use` prefix convention.


**Read:** `references/composables.md` for detailed step 4: composables reference material.

## STEP 5: Vue Router

### Route Definitions with TypeScript

```ts
// router/index.ts
import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/pages/Home.vue'),
  },
  {
    path: '/users',
    component: () => import('@/pages/Users.vue'),
    children: [
      {
        path: ':id',
        component: () => import('@/pages/UserDetail.vue'),
        props: true,
      },
    ],
  },
  {
    path: '/settings',
    component: () => import('@/pages/Settings.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    component: () => import('@/pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export { router, routes }
```

### Navigation Guards

```ts
// router/guards.ts
import type { Router } from 'vue-router'

export function setupGuards(router: Router) {
  router.beforeEach((to, from) => {
    const isAuthenticated = !!localStorage.getItem('token')

    if (to.meta.requiresAuth && !isAuthenticated) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  })
}
```

### Typed Route Params in Components

```vue
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Access typed params
const userId = computed(() => route.params.id as string)

// Programmatic navigation
function goToUser(id: string) {
  router.push({ path: `/users/${id}` })
}

// Navigate with query params
function search(query: string) {
  router.push({ path: '/search', query: { q: query } })
}
</script>
```

---

## STEP 6: Reka UI Headless Components

Reka UI (formerly Radix Vue) provides unstyled, WAI-ARIA compliant Vue 3 primitives. Current version: v2.8+.


**Read:** `references/reka-ui-headless-components.md` for detailed step 6: reka ui headless components reference material.

## STEP 7: Custom Directives

```ts
// directives/vFocus.ts
import type { Directive } from 'vue'

export const vFocus: Directive<HTMLElement> = {
  mounted(el) {
    el.focus()
  },
}
```

```ts
// directives/vClickOutside.ts
import type { Directive, DirectiveBinding } from 'vue'

export const vClickOutside: Directive<HTMLElement, () => void> = {
  mounted(el, binding: DirectiveBinding<() => void>) {
    const handler = (event: MouseEvent) => {
      if (!el.contains(event.target as Node)) {
        binding.value()
      }
    }
    ;(el as any).__clickOutsideHandler = handler
    document.addEventListener('click', handler)
  },
  unmounted(el) {
    document.removeEventListener('click', (el as any).__clickOutsideHandler)
  },
}
```

```vue
<script setup lang="ts">
import { vFocus } from '@/directives/vFocus'
import { vClickOutside } from '@/directives/vClickOutside'
</script>

<template>
  <input v-focus />
  <div v-click-outside="closeDropdown">Dropdown content</div>
</template>
```

---

## STEP 8: Testing

Use Vitest + @vue/test-utils for all tests.


**Read:** `references/testing.md` for detailed step 8: testing reference material.

# All tests
npx vitest run

# Watch mode
npx vitest

# Single file
npx vitest run tests/components/ItemCard.test.ts

# With coverage
npx vitest run --coverage

# Type checking
npx vue-tsc --noEmit
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `ref` value not reactive in template | Using `.value` in template (not needed) | Remove `.value` in `<template>`, keep it in `<script>` |
| `watch` not firing | Watching a getter incorrectly | Wrap in arrow function: `watch(() => obj.prop, ...)` |
| Component not updating after prop change | Destructured props lost reactivity (pre-3.5) | Use `toRefs(props)` or upgrade to Vue 3.5+ reactive destructure |
| `inject()` returns undefined | Missing `provide()` in ancestor | Add `provide()` in parent or use fallback: `inject(Key, defaultVal)` |
| Reka UI component not rendering | Missing Root wrapper or Portal | Ensure component is inside its Root and Content is in Portal |
| Reka UI keyboard nav broken | Overriding native event handlers | Use Reka's built-in events; do not `preventDefault` on arrow keys |
| Template ref is `null` in `setup` | Accessed before mount | Use `onMounted()` or `watchEffect()` to access template refs |
| Hydration mismatch (SSR) | Browser-only code in setup | Guard with `onMounted()` or `<ClientOnly>` wrapper |
| TypeScript error on `defineProps` | Missing `lang="ts"` on script tag | Use `<script setup lang="ts">` |
| Circular dependency in composables | Composables importing each other | Extract shared logic to a third composable |
| `v-model` not working on custom component | Missing `defineModel()` or emit | Use `defineModel()` (Vue 3.4+) or manual prop + emit pattern |
| Router guard infinite redirect | Guard always returns a redirect | Add condition to skip redirect when already on target route |

---

## CRITICAL RULES

### MUST DO

- Use `<script setup lang="ts">` for all components
- Use `ref()` over `reactive()` as the default reactive primitive
- Define props with TypeScript interfaces via `defineProps<T>()`
- Define emits with TypeScript via `defineEmits<T>()`
- Use `defineModel()` for v-model bindings (Vue 3.4+)
- Use `useTemplateRef()` for DOM access (Vue 3.5+)
- Type injection keys with `InjectionKey<T>` and use `Symbol()`
- Wrap Reka UI content in `Portal` for modals, popovers, and selects
- Provide `aria-label` or `aria-labelledby` on all interactive Reka UI triggers
- Test components with `@vue/test-utils` mount and test composables as plain functions
- Lazy-load route components with dynamic `import()`
- Run `vue-tsc --noEmit` before every commit -- zero type errors

### MUST NOT DO

- Use Options API -- use Composition API with `<script setup>` instead
- Use `this` in `<script setup>` -- there is no `this` in Composition API
- Mutate props directly -- emit events or use `defineModel()` instead
- Use `reactive()` for primitives -- use `ref()` instead (reactive only works with objects)
- Destructure props without `toRefs()` or Vue 3.5+ reactive destructure -- reactivity is lost
- Skip the `key` attribute on `v-for` list items -- always bind `:key` to a unique identifier
- Nest `v-if` and `v-for` on the same element -- use `<template v-for>` with `v-if` on child instead
- Override keyboard event handlers on Reka UI components -- let Reka handle keyboard navigation
- Use `asChild` without a single direct child element -- Reka requires exactly one child to merge onto
- Import all Reka UI components globally -- import per-component to enable tree-shaking
- Skip `Portal` for overlays -- without Portal, z-index and overflow issues break the UI
- Commit code with `vue-tsc` type errors
