# STEP 8: Testing

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
