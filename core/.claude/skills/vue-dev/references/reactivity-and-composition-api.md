# STEP 2: Reactivity and Composition API

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

