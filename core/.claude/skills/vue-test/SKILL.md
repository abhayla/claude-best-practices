---
name: vue-test
description: >
  Run and author tests for Vue.js applications covering components, Pinia stores,
  composables, Vue Router mocks, and Nuxt server routes. Detects the test framework
  automatically and produces structured JSON results.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<test-scope> [--component|--store|--composable|--e2e]"
version: "1.0.0"
---

# Vue.js Test Runner

Run, author, and validate tests for Vue.js applications — components, Pinia stores, composables, router integration, and Nuxt server routes.

**Constraint:** Never modify production source files. Only create or edit files under the test directory. Use generic placeholders (`<your-component>`, `<your-store>`) — never assume specific filenames exist.

**Request:** $ARGUMENTS

---

## STEP 1: Detect Test Framework and Configuration

Identify the project's test runner and configuration.

```bash
# Check for Vitest (preferred)
cat vitest.config.ts 2>/dev/null || cat vitest.config.js 2>/dev/null || cat vite.config.ts 2>/dev/null

# Check for Jest fallback
cat jest.config.ts 2>/dev/null || cat jest.config.js 2>/dev/null
```

**Decision table:**

| Found | Framework | Config File |
|-------|-----------|-------------|
| `vitest.config.*` or `vitest` in `vite.config.*` | Vitest | `vitest.config.ts` |
| `jest.config.*` or `"jest"` in `package.json` | Jest | `jest.config.ts` |
| Neither | Vitest (default) | Create `vitest.config.ts` |

Verify test utilities are installed:

```bash
# Check package.json for required deps
grep -E "vitest|jest|@vue/test-utils|@pinia/testing" package.json
```

If `@vue/test-utils` is missing, inform the user:

```bash
# Install with project's package manager
npm install --save-dev @vue/test-utils   # or yarn add -D / pnpm add -D
```

Record the detected framework for use in subsequent steps.

---

## STEP 2: Test Components with Vue Test Utils

Use `mount` for full rendering (when child component behavior matters) or `shallowMount` for isolated unit tests (stubs child components).

### Full mount example

```typescript
import { mount } from '@vue/test-utils'
import YourComponent from '@/components/<your-component>.vue'

describe('<your-component>', () => {
  it('renders the expected content', () => {
    const wrapper = mount(YourComponent, {
      props: {
        title: 'Test Title',
        items: [{ id: 1, label: 'Item 1' }],
      },
    })

    expect(wrapper.text()).toContain('Test Title')
    expect(wrapper.findAll('[data-testid="item"]')).toHaveLength(1)
  })

  it('emits an event when the button is clicked', async () => {
    const wrapper = mount(YourComponent)

    await wrapper.find('[data-testid="submit-btn"]').trigger('click')

    expect(wrapper.emitted('submit')).toHaveLength(1)
    expect(wrapper.emitted('submit')![0]).toEqual([{ id: 1 }])
  })
})
```

### Shallow mount for isolation

```typescript
import { shallowMount } from '@vue/test-utils'
import ParentComponent from '@/components/<your-parent>.vue'

it('renders without mounting children', () => {
  const wrapper = shallowMount(ParentComponent)
  // Child components are stubbed — only ParentComponent logic is tested
  expect(wrapper.exists()).toBe(true)
})
```

### Providing global plugins and stubs

```typescript
const wrapper = mount(YourComponent, {
  global: {
    plugins: [router, pinia],
    stubs: {
      'RouterLink': true,
      'Teleport': true,
    },
    mocks: {
      $t: (key: string) => key, // i18n mock
    },
  },
})
```

---

## STEP 3: Test Pinia Stores

Use `@pinia/testing` to create a testing-specific Pinia instance with optional stubbed actions.

```bash
# Ensure @pinia/testing is installed
grep "@pinia/testing" package.json || echo "Missing: npm install --save-dev @pinia/testing"
```

### Unit testing a store directly

```typescript
import { setActivePinia, createPinia } from 'pinia'
import { useYourStore } from '@/stores/<your-store>'

describe('<your-store>', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default state', () => {
    const store = useYourStore()
    expect(store.items).toEqual([])
    expect(store.isLoading).toBe(false)
  })

  it('updates state via action', async () => {
    const store = useYourStore()
    await store.fetchItems()
    expect(store.items.length).toBeGreaterThan(0)
  })
})
```

### Testing a component with createTestingPinia

```typescript
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import YourComponent from '@/components/<your-component>.vue'

it('uses mocked store actions', async () => {
  const wrapper = mount(YourComponent, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            '<your-store>': { items: [{ id: 1, name: 'Mock Item' }] },
          },
          stubActions: false, // set true to auto-stub all actions
        }),
      ],
    },
  })

  expect(wrapper.text()).toContain('Mock Item')
})
```

To mock individual actions, pass `createSpy: vi.fn` (Vitest) or `createSpy: jest.fn` (Jest) to `createTestingPinia`, then override the specific action on the store instance with a mock function.

---

## STEP 4: Test Composables

Composables that use Vue's reactivity (`ref`, `computed`, `watch`) need a component instance context. Use the `renderHook` pattern or a minimal wrapper component.

### Using a wrapper component

```typescript
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { useYourComposable } from '@/composables/<your-composable>'

function withSetup<T>(composable: () => T) {
  let result: T
  const Wrapper = defineComponent({
    setup() {
      result = composable()
      return () => null // render nothing
    },
  })
  const wrapper = mount(Wrapper)
  return { result: result!, wrapper }
}

describe('<your-composable>', () => {
  it('returns reactive state', () => {
    const { result } = withSetup(() => useYourComposable())
    expect(result.count.value).toBe(0)

    result.increment()
    expect(result.count.value).toBe(1)
  })
})
```

For composables with lifecycle hooks (`onMounted`, `onUnmounted`), use the same `withSetup` helper. Call `await flushPromises()` after mounting to resolve async `onMounted` effects, and `wrapper.unmount()` to trigger cleanup hooks.

---

## STEP 5: Mock Vue Router

Stub `useRoute` and `useRouter` to test components with routing dependencies without a real router instance.

### Mocking useRoute and useRouter

```typescript
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import YourComponent from '@/components/<your-component>.vue'

const mockPush = vi.fn()
const mockRoute = {
  params: { id: '42' },
  query: { tab: 'details' },
  name: 'item-detail',
  path: '/items/42',
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: vi.fn(),
  }),
}))

describe('<your-component> with router', () => {
  it('reads route params', () => {
    const wrapper = mount(YourComponent)
    expect(wrapper.text()).toContain('42')
  })

  it('navigates on action', async () => {
    const wrapper = mount(YourComponent)
    await wrapper.find('[data-testid="nav-btn"]').trigger('click')
    expect(mockPush).toHaveBeenCalledWith({ name: 'item-list' })
  })
})
```

For integration tests requiring a real router, create one with `createRouter({ history: createMemoryHistory(), routes: [...] })`, call `router.push('/target')` and `await router.isReady()`, then pass the router as a global plugin to `mount`.

---

## STEP 6: Test Nuxt Server Routes (If Nuxt Detected)

Check for Nuxt by looking for `nuxt.config.ts` or `nuxt.config.js`.

```bash
ls nuxt.config.ts nuxt.config.js 2>/dev/null
```

If Nuxt is detected, test server routes using `$fetch` from `@nuxt/test-utils`:

```typescript
import { describe, it, expect } from 'vitest'
import { setup, $fetch } from '@nuxt/test-utils'

describe('server routes', () => {
  // Start a Nuxt test server
  setup({ server: true })

  it('GET /api/<your-endpoint> returns expected data', async () => {
    const data = await $fetch('/api/<your-endpoint>')
    expect(data).toHaveProperty('items')
    expect(Array.isArray(data.items)).toBe(true)
  })

  it('POST /api/<your-endpoint> creates a resource', async () => {
    const data = await $fetch('/api/<your-endpoint>', {
      method: 'POST',
      body: { name: 'Test Item' },
    })
    expect(data).toHaveProperty('id')
    expect(data.name).toBe('Test Item')
  })
})
```

Skip this step if Nuxt is not detected.

---

## STEP 7: Test Async Components (Suspense and Lazy Loading)

### Testing components wrapped in Suspense

```typescript
import { mount, flushPromises } from '@vue/test-utils'
import { Suspense } from 'vue'
import AsyncComponent from '@/components/<your-async-component>.vue'

it('renders async component after resolution', async () => {
  const wrapper = mount({
    template: `
      <Suspense>
        <AsyncComponent />
        <template #fallback>Loading...</template>
      </Suspense>
    `,
    components: { AsyncComponent },
  })

  expect(wrapper.text()).toContain('Loading...')

  await flushPromises()

  expect(wrapper.text()).not.toContain('Loading...')
  expect(wrapper.findComponent(AsyncComponent).exists()).toBe(true)
})
```

### Testing lazy-loaded (defineAsyncComponent) components

```typescript
import { mount, flushPromises } from '@vue/test-utils'
import { defineAsyncComponent } from 'vue'

const LazyComponent = defineAsyncComponent(
  () => import('@/components/<your-lazy-component>.vue')
)

it('loads and renders the lazy component', async () => {
  const wrapper = mount({
    template: '<Suspense><LazyComponent /></Suspense>',
    components: { LazyComponent },
  })

  await flushPromises()
  expect(wrapper.text()).toBeTruthy()
})
```

---

## STEP 8: Run Tests and Collect Results

Execute tests based on the detected framework from STEP 1.

```bash
# Vitest
npx vitest run --reporter=json --outputFile=test-results/vue-raw.json $TEST_SCOPE

# Jest fallback
npx jest --json --outputFile=test-results/vue-raw.json $TEST_SCOPE

# Run specific test categories
npx vitest run --reporter=json --outputFile=test-results/vue-raw.json "**/*.spec.ts"   # all specs
npx vitest run --reporter=json --outputFile=test-results/vue-raw.json "components/"     # component tests
npx vitest run --reporter=json --outputFile=test-results/vue-raw.json "stores/"         # store tests
```

Replace `$TEST_SCOPE` with the scope from $ARGUMENTS (file path, directory, or test name pattern).

If tests fail, capture the output and analyze failures before proceeding.

---

## STEP 9: Write Structured JSON Output

Parse the raw test output and write a structured result file.

```json
{
  "skill": "vue-test",
  "timestamp": "<ISO-8601>",
  "result": "PASSED",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "flaky": 0
  },
  "quality_gate": "PASSED",
  "framework": "vitest",
  "scope": "<test-scope from arguments>",
  "failures": [],
  "warnings": [],
  "duration_ms": 0
}
```

Write to `test-results/vue-test.json`.

**Result field values:**

| result | Condition |
|--------|-----------|
| `PASSED` | All tests passed |
| `FAILED` | One or more tests failed |
| `FLAKY` | Tests passed on retry but failed initially |

**Failure entry format:**

```json
{
  "test": "<test-name>",
  "category": "ASSERTION_FAILURE",
  "file": "<file-path>:<line>",
  "message": "<failure message>",
  "confidence": "HIGH"
}
```

---

## CRITICAL RULES

### MUST DO

- Detect the test framework before running any commands (STEP 1)
- Use `data-testid` attributes for element selection — never rely on CSS classes or DOM structure
- Call `await flushPromises()` after any async operation before asserting
- Use `wrapper.unmount()` or `afterEach(() => wrapper.unmount())` to prevent memory leaks
- Reset Pinia state in `beforeEach` with a fresh `createPinia()` or `createTestingPinia()`
- Write the structured JSON output to `test-results/vue-test.json` on every run
- Use `vi.fn()` (Vitest) or `jest.fn()` (Jest) consistently — match the detected framework

### MUST NOT DO

- MUST NOT import from `@vue/test-utils` and `enzyme` in the same project — they are incompatible
- MUST NOT test implementation details (internal component state, private methods) — test behavior via props, events, and rendered output
- MUST NOT use `setTimeout` or `sleep` to wait for async operations — use `flushPromises()` or `await nextTick()`
- MUST NOT mutate Pinia store state directly in tests — use actions or `$patch` to keep tests realistic
- MUST NOT hardcode file paths — use the project's configured path aliases (`@/`, `~/`, `#imports`)
- MUST NOT skip failing tests without logging a tracking issue — quarantine with `it.todo()` and a comment linking the issue
- MUST NOT modify production source files — only create or edit test files
