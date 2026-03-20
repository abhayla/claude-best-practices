# STEP 6: Nuxt Content v3

### Enable Nuxt Content

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],
})
```

### Collection Types

| Type | Purpose | Has Route | Has Body |
|------|---------|-----------|----------|
| `page` | Routable content (blog posts, docs) | Yes | Yes |
| `data` | Structured data (authors, config) | No | No |

### Define Collections

```typescript
// content.config.ts
import { defineCollection, defineContentConfig, z } from '@nuxt/content'

export default defineContentConfig({
  collections: {
    blog: defineCollection({
      type: 'page',
      source: 'blog/**',
      schema: z.object({
        title: z.string(),
        description: z.string(),
        date: z.date(),
        tags: z.array(z.string()).optional(),
        image: z.string().optional(),
      }),
    }),
    authors: defineCollection({
      type: 'data',
      source: 'authors/**',
      schema: z.object({
        name: z.string(),
        avatar: z.string(),
        twitter: z.string().optional(),
      }),
    }),
  },
})
```

### Query Collections

```vue
<script setup>
// Query page collection
const { data: posts } = await useAsyncData('blog', () =>
  queryCollection('blog')
    .order('date', 'DESC')
    .limit(10)
    .all()
)

// Query single item
const route = useRoute()
const { data: post } = await useAsyncData(`blog-${route.params.slug}`, () =>
  queryCollection('blog')
    .path(route.path)
    .first()
)
</script>
```

### Render Content (MDC)

```vue
<template>
  <ContentRenderer v-if="post" :value="post" />
</template>
```

### Remote Sources

```typescript
// content.config.ts — fetch from GitHub
export default defineContentConfig({
  collections: {
    docs: defineCollection({
      type: 'page',
      source: {
        repository: 'https://github.com/org/repo',
        path: 'docs/**',
      },
    }),
  },
})
```

---

