# STEP 4: Composables

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

