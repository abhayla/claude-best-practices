---
name: vue-dev
description: >
  Vue 3.5+ development workflow: Composition API patterns, TypeScript integration,
  Reka UI headless components, Vue Router, composables, VueUse, testing with Vitest,
  and project architecture. Use for building Vue 3 applications with modern patterns.
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

### Core Reactivity Primitives

| Primitive | Use Case | Example |
|-----------|----------|---------|
| `ref()` | Single reactive values, DOM refs | Counters, toggles, input bindings |
| `computed()` | Derived values that auto-update | Filtered lists, formatted strings |
| `reactive()` | Reactive objects (use sparingly) | Complex form state |
| `watch()` | Side effects on reactive changes | API calls on param change |
| `watchEffect()` | Auto-tracking side effects | Logging, analytics |
| `shallowRef()` | Large objects where deep reactivity is wasteful | Chart data, large arrays |
| `readonly()` | Prevent mutations from consumers | Exposed store state |

### ref vs reactive

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// ref — use for primitives and single values (PREFERRED)
const count = ref(0)
const name = ref('')

// computed — derived state, auto-tracks dependencies
const doubled = computed(() => count.value * 2)

// Writable computed
const fullName = computed({
  get: () => `${firstName.value} ${lastName.value}`,
  set: (val: string) => {
    const [first, ...rest] = val.split(' ')
    firstName.value = first
    lastName.value = rest.join(' ')
  },
})

// watch — explicit side effects
watch(count, (newVal, oldVal) => {
  console.log(`count changed: ${oldVal} -> ${newVal}`)
})

// watch multiple sources
watch([count, name], ([newCount, newName]) => {
  saveToApi(newCount, newName)
})

// Deep watch with immediate execution
watch(
  () => props.modelValue,
  (newVal) => { internalState.value = newVal },
  { deep: true, immediate: true },
)
</script>
```

### Vue 3.5+ Reactive Props Destructure

```vue
<script setup lang="ts">
// Vue 3.5+: reactive destructured props with defaults
const { count = 0, msg = 'hello' } = defineProps<{
  count?: number
  msg?: string
}>()

// These are reactive — use directly in templates and computed
const doubled = computed(() => count * 2)
</script>
```

### Template Refs (Vue 3.5+)

```vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue'

// Vue 3.5+ useTemplateRef — type-safe DOM access
const inputEl = useTemplateRef<HTMLInputElement>('input')

onMounted(() => {
  inputEl.value?.focus()
})
</script>

<template>
  <input ref="input" />
</template>
```

---

## STEP 3: Component Patterns

### Props with TypeScript

```vue
<script setup lang="ts">
// Interface-based props (preferred)
interface Props {
  title: string
  count?: number
  items: string[]
  status: 'active' | 'inactive' | 'pending'
  /** Callback when item is selected */
  onSelect?: (id: string) => void
}

const props = withDefaults(defineProps<Props>(), {
  count: 0,
  status: 'active',
})
</script>
```

### Emits with TypeScript

```vue
<script setup lang="ts">
const emit = defineEmits<{
  update: [value: string]
  delete: [id: number]
  'update:modelValue': [value: boolean]
}>()

// Usage
emit('update', 'new value')
emit('delete', 42)
</script>
```

### v-model on Components

```vue
<!-- Parent -->
<ToggleSwitch v-model="isEnabled" />
<SearchInput v-model:query="searchQuery" v-model:filters="activeFilters" />

<!-- ToggleSwitch.vue -->
<script setup lang="ts">
const modelValue = defineModel<boolean>({ required: true })
</script>

<template>
  <button @click="modelValue = !modelValue">
    {{ modelValue ? 'On' : 'Off' }}
  </button>
</template>

<!-- SearchInput.vue — multiple v-model bindings -->
<script setup lang="ts">
const query = defineModel<string>('query', { default: '' })
const filters = defineModel<string[]>('filters', { default: () => [] })
</script>
```

### Slots

```vue
<!-- Card.vue -->
<script setup lang="ts">
defineSlots<{
  default: (props: Record<string, never>) => any
  header: (props: { title: string }) => any
  footer: (props: Record<string, never>) => any
}>()
</script>

<template>
  <div class="card">
    <div class="card-header">
      <slot name="header" :title="'Card Title'" />
    </div>
    <div class="card-body">
      <slot />
    </div>
    <div class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>
```

### Provide / Inject

```ts
// types/injection-keys.ts
import type { InjectionKey, Ref } from 'vue'

export interface UserContext {
  name: Ref<string>
  logout: () => void
}

export const UserKey: InjectionKey<UserContext> = Symbol('user')
```

```vue
<!-- Provider.vue -->
<script setup lang="ts">
import { provide, ref } from 'vue'
import { UserKey } from '@/types/injection-keys'

const name = ref('Alice')
provide(UserKey, {
  name,
  logout: () => { name.value = '' },
})
</script>

<!-- Consumer.vue -->
<script setup lang="ts">
import { inject } from 'vue'
import { UserKey } from '@/types/injection-keys'

const user = inject(UserKey)
if (!user) throw new Error('UserKey not provided')
</script>
```

### Generic Components

```vue
<!-- GenericList.vue -->
<script setup lang="ts" generic="T extends { id: string | number }">
defineProps<{
  items: T[]
  selected?: T
}>()

defineEmits<{
  select: [item: T]
}>()

defineSlots<{
  default: (props: { item: T; index: number }) => any
}>()
</script>

<template>
  <ul>
    <li v-for="(item, index) in items" :key="item.id" @click="$emit('select', item)">
      <slot :item="item" :index="index" />
    </li>
  </ul>
</template>
```

---

## STEP 4: Composables

Write composables for reusable stateful logic. Follow the `use` prefix convention.

### Writing a Custom Composable

```ts
// composables/useCounter.ts
import { ref, computed } from 'vue'
import type { Ref } from 'vue'

interface UseCounterOptions {
  min?: number
  max?: number
}

interface UseCounterReturn {
  count: Ref<number>
  doubled: Readonly<Ref<number>>
  increment: () => void
  decrement: () => void
  reset: () => void
}

export function useCounter(initial = 0, options: UseCounterOptions = {}): UseCounterReturn {
  const { min = -Infinity, max = Infinity } = options
  const count = ref(initial)
  const doubled = computed(() => count.value * 2)

  function increment() {
    if (count.value < max) count.value++
  }

  function decrement() {
    if (count.value > min) count.value--
  }

  function reset() {
    count.value = initial
  }

  return { count, doubled, increment, decrement, reset }
}
```

### Async Composable Pattern

```ts
// composables/useFetchData.ts
import { ref, watchEffect, toValue } from 'vue'
import type { Ref, MaybeRefOrGetter } from 'vue'

export function useFetchData<T>(url: MaybeRefOrGetter<string>) {
  const data = ref<T | null>(null) as Ref<T | null>
  const error = ref<Error | null>(null)
  const isLoading = ref(false)

  async function fetchData() {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch(toValue(url))
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      data.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      isLoading.value = false
    }
  }

  watchEffect(() => {
    toValue(url) // track the dependency
    fetchData()
  })

  return { data, error, isLoading, refetch: fetchData }
}
```

### VueUse Integration

```ts
import { useLocalStorage, useDebounceFn, useIntersectionObserver } from '@vueuse/core'

// Persistent state
const theme = useLocalStorage<'light' | 'dark'>('app-theme', 'light')

// Debounced search
const debouncedSearch = useDebounceFn((query: string) => {
  fetchResults(query)
}, 300)

// Intersection observer for lazy loading
const target = ref<HTMLElement | null>(null)
const isVisible = ref(false)
useIntersectionObserver(target, ([{ isIntersecting }]) => {
  isVisible.value = isIntersecting
})
```

---

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

### Core Concepts

| Concept | Description |
|---------|-------------|
| `asChild` | Merges props/events onto child element instead of rendering a wrapper |
| Controlled state | Bind with `v-model` for full control over open/value/checked |
| Uncontrolled state | Use `default-*` props (e.g., `default-open`) and let Reka manage state |
| Composition | Components split into Root, Trigger, Content, Portal, Item parts |
| WAI-ARIA | Keyboard navigation and ARIA attributes built in |

### asChild Prop Merging

```vue
<template>
  <!-- Renders <button> wrapper by default -->
  <Dialog.Trigger>Open</Dialog.Trigger>

  <!-- asChild: merges onto YOUR element — no extra wrapper -->
  <Dialog.Trigger as-child>
    <MyCustomButton variant="primary">Open</MyCustomButton>
  </Dialog.Trigger>
</template>
```

### Dialog Example (Controlled)

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { DialogRoot, DialogTrigger, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'reka-ui'

const isOpen = ref(false)
</script>

<template>
  <DialogRoot v-model:open="isOpen">
    <DialogTrigger as-child>
      <button>Edit Profile</button>
    </DialogTrigger>

    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50" />
      <DialogContent class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg">
        <DialogTitle>Edit Profile</DialogTitle>
        <DialogDescription>Make changes to your profile.</DialogDescription>

        <!-- form fields here -->

        <DialogClose as-child>
          <button>Close</button>
        </DialogClose>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
```

### Select Example (Uncontrolled)

```vue
<script setup lang="ts">
import { SelectRoot, SelectTrigger, SelectValue, SelectPortal, SelectContent, SelectViewport, SelectItem, SelectItemText, SelectItemIndicator } from 'reka-ui'
</script>

<template>
  <SelectRoot default-value="apple">
    <SelectTrigger aria-label="Fruit">
      <SelectValue placeholder="Pick a fruit" />
    </SelectTrigger>

    <SelectPortal>
      <SelectContent>
        <SelectViewport>
          <SelectItem value="apple">
            <SelectItemIndicator />
            <SelectItemText>Apple</SelectItemText>
          </SelectItem>
          <SelectItem value="banana">
            <SelectItemIndicator />
            <SelectItemText>Banana</SelectItemText>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>
```

### Tabs Example (Composition Pattern)

```vue
<script setup lang="ts">
import { TabsRoot, TabsList, TabsTrigger, TabsContent } from 'reka-ui'
</script>

<template>
  <TabsRoot default-value="tab1">
    <TabsList aria-label="Settings">
      <TabsTrigger value="tab1">General</TabsTrigger>
      <TabsTrigger value="tab2">Security</TabsTrigger>
    </TabsList>

    <TabsContent value="tab1">General settings content</TabsContent>
    <TabsContent value="tab2">Security settings content</TabsContent>
  </TabsRoot>
</template>
```

### Reka UI Component Families

| Family | Parts | Use Case |
|--------|-------|----------|
| Dialog | Root, Trigger, Portal, Overlay, Content, Title, Description, Close | Modals, confirmations |
| Popover | Root, Trigger, Portal, Content, Arrow, Close | Tooltips, dropdowns |
| Select | Root, Trigger, Value, Portal, Content, Viewport, Item, ItemText | Dropdowns, pickers |
| Tabs | Root, List, Trigger, Content | Tabbed interfaces |
| Accordion | Root, Item, Header, Trigger, Content | Collapsible sections |
| Combobox | Root, Input, Trigger, Portal, Content, Item | Autocomplete, search |
| Toast | Provider, Root, Title, Description, Action, Close, Viewport | Notifications |
| Checkbox | Root, Indicator | Boolean inputs |
| RadioGroup | Root, Item, Indicator | Single selection |
| Slider | Root, Track, Range, Thumb | Range inputs |

---

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

### Vitest Configuration

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
})
```

### Component Testing

```ts
// tests/components/ItemCard.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ItemCard from '@/components/ItemCard.vue'

describe('ItemCard', () => {
  it('renders title and subtitle', () => {
    const wrapper = mount(ItemCard, {
      props: { title: 'Test Title', subtitle: 'Test Sub' },
    })

    expect(wrapper.text()).toContain('Test Title')
    expect(wrapper.text()).toContain('Test Sub')
  })

  it('emits select event when clicked', async () => {
    const wrapper = mount(ItemCard, {
      props: { title: 'Click Me', subtitle: 'Sub' },
    })

    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })

  it('renders slot content', () => {
    const wrapper = mount(ItemCard, {
      props: { title: 'Title', subtitle: 'Sub' },
      slots: { footer: '<span>Footer</span>' },
    })

    expect(wrapper.html()).toContain('Footer')
  })
})
```

### Composable Testing

```ts
// tests/composables/useCounter.test.ts
import { describe, it, expect } from 'vitest'
import { useCounter } from '@/composables/useCounter'

describe('useCounter', () => {
  it('initializes with given value', () => {
    const { count } = useCounter(10)
    expect(count.value).toBe(10)
  })

  it('increments and decrements', () => {
    const { count, increment, decrement } = useCounter(0)

    increment()
    expect(count.value).toBe(1)

    decrement()
    expect(count.value).toBe(0)
  })

  it('respects min and max bounds', () => {
    const { count, increment, decrement } = useCounter(5, { min: 0, max: 10 })

    for (let i = 0; i < 20; i++) increment()
    expect(count.value).toBe(10)

    for (let i = 0; i < 20; i++) decrement()
    expect(count.value).toBe(0)
  })
})
```

### Testing with Vue Router

```ts
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div>Home</div>' } }],
})

const wrapper = mount(MyComponent, {
  global: {
    plugins: [router],
  },
})

await router.isReady()
```

### Run Tests

```bash
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
