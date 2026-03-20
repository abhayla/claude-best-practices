# STEP 3: Component Patterns

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

