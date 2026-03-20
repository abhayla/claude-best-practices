# STEP 6: Reka UI Headless Components

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

