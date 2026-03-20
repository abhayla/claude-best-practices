# STEP 7: Nuxt UI v4

### Enable Nuxt UI

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
})
```

### UApp Wrapper (Required)

```vue
<!-- app.vue — wrap entire app for Toast, Tooltip, and overlay support -->
<template>
  <UApp>
    <NuxtPage />
  </UApp>
</template>
```

### Component Examples

```vue
<template>
  <!-- Button with variants -->
  <UButton label="Save" color="primary" variant="solid" size="lg" />

  <!-- Form with validation -->
  <UForm :schema="schema" :state="state" @submit="onSubmit">
    <UFormField label="Email" name="email">
      <UInput v-model="state.email" type="email" />
    </UFormField>
    <UFormField label="Password" name="password">
      <UInput v-model="state.password" type="password" />
    </UFormField>
    <UButton type="submit" label="Login" />
  </UForm>

  <!-- Table -->
  <UTable :data="users" :columns="columns" />

  <!-- Modal overlay -->
  <UModal v-model:open="isOpen">
    <template #header>Confirm</template>
    <p>Are you sure?</p>
    <template #footer>
      <UButton label="Cancel" @click="isOpen = false" />
      <UButton label="Confirm" color="primary" @click="confirm" />
    </template>
  </UModal>
</template>
```

### Theming (Tailwind CSS v4 + Tailwind Variants)

```css
/* app/assets/css/main.css */
@import "tailwindcss";
@import "@nuxt/ui";

@theme {
  --color-primary-50: #f0fdf4;
  --color-primary-500: #22c55e;
  --color-primary-900: #14532d;
}
```

### Key Composables

| Composable | Purpose |
|------------|---------|
| `useToast()` | Show toast notifications |
| `useOverlay()` | Programmatic overlays (modal, slideover, drawer) |
| `useModal()` | Open/close modals programmatically |

```typescript
const toast = useToast()
toast.add({ title: 'Saved', description: 'Changes saved successfully', color: 'success' })

const overlay = useOverlay()
const result = await overlay.open(ConfirmDialog, { title: 'Delete?' })
```

---

