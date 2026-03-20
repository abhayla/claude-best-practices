# Server vs Client Component Examples

### Server Component Data Fetching (Repository Pattern)

```tsx
// src/lib/data/posts.ts â€” server-only data layer
import 'server-only'
import { db } from '@/lib/db'

export async function getPostBySlug(slug: string) {
  return db.post.findUnique({ where: { slug } })
}

export async function getRecentPosts(limit = 10) {
  return db.post.findMany({
    orderBy: { createdAt: 'desc' },
    take: limit,
  })
}
```

```tsx
// src/app/blog/[slug]/page.tsx â€” Server Component
import { getPostBySlug } from '@/lib/data/posts'
import { notFound } from 'next/navigation'

interface PageProps {
  params: Promise<{ slug: string }>
}

export default async function BlogPostPage({ params }: PageProps) {
  const { slug } = await params
  const post = await getPostBySlug(slug)

  if (!post) notFound()

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.contentHtml }} />
    </article>
  )
}
```

### Client Component (Interactive Leaf)

```tsx
// src/components/ui/LikeButton.tsx
'use client'

import { useState, useTransition } from 'react'
import { likePost } from '@/app/actions'

export function LikeButton({ postId, initialCount }: { postId: string; initialCount: number }) {
  const [count, setCount] = useState(initialCount)
  const [isPending, startTransition] = useTransition()

  function handleClick() {
    startTransition(async () => {
      const newCount = await likePost(postId)
      setCount(newCount)
    })
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {isPending ? 'Saving...' : `Like (${count})`}
    </button>
  )
}
```

### Component Boundary Rule

Mark the **interactive leaf**, not the parent. Push `'use client'` as far down the component tree as possible.

```tsx
// CORRECT: Server Component parent, Client Component child
// src/app/blog/[slug]/page.tsx (Server)
import { LikeButton } from '@/components/ui/LikeButton'
import { getPostBySlug } from '@/lib/data/posts'

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPostBySlug(slug)
  if (!post) notFound()

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.body}</p>
      {/* Only LikeButton ships JavaScript to the client */}
      <LikeButton postId={post.id} initialCount={post.likeCount} />
    </article>
  )
}
```

### useSearchParams Requires Suspense Boundary

```tsx
// src/components/SearchResults.tsx
'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'

function SearchResultsInner() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') ?? ''
  return <p>Results for: {query}</p>
}

export function SearchResults() {
  return (
    <Suspense fallback={<p>Loading search...</p>}>
      <SearchResultsInner />
    </Suspense>
  )
}
```
