# Data Fetching & Caching Examples


```typescript
// src/app/api/health/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() })
}
```

```typescript
// src/app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { postSchema } from '@/lib/validators'

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const page = parseInt(searchParams.get('page') ?? '1', 10)
  const limit = parseInt(searchParams.get('limit') ?? '20', 10)

  const posts = await db.post.findMany({
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: 'desc' },
  })

  return NextResponse.json({ data: posts, page, limit })
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const parsed = postSchema.safeParse(body)

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 }
    )
  }

  const post = await db.post.create({ data: parsed.data })
  return NextResponse.json({ data: post }, { status: 201 })
}
```

### Dynamic Route Handler (Next.js 15 â€” params is a Promise)

```typescript
// src/app/api/posts/[slug]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params
  const post = await db.post.findUnique({ where: { slug } })

  if (!post) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  return NextResponse.json({ data: post })
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params
  const body = await request.json()
  const updated = await db.post.update({ where: { slug }, data: body })
  return NextResponse.json({ data: updated })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params
  await db.post.delete({ where: { slug } })
  return NextResponse.json({ success: true })
}
```

### Static Generation with generateStaticParams

```tsx
// src/app/blog/[slug]/page.tsx
import { db } from '@/lib/db'

export async function generateStaticParams() {
  const posts = await db.post.findMany({ select: { slug: true } })
  return posts.map((post) => ({ slug: post.slug }))
}
```

### Revalidation

```typescript
// On-demand revalidation by path
import { revalidatePath } from 'next/cache'
revalidatePath('/blog')

// On-demand revalidation by tag
import { revalidateTag } from 'next/cache'
revalidateTag('posts')

// Time-based revalidation in fetch
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600, tags: ['posts'] },
})
```

### Server Actions

```typescript
// src/app/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { db } from '@/lib/db'

export async function likePost(postId: string): Promise<number> {
  const post = await db.post.update({
    where: { id: postId },
    data: { likeCount: { increment: 1 } },
  })
  revalidatePath(`/blog/${post.slug}`)
  return post.likeCount
}

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  const body = formData.get('body') as string

  await db.post.create({ data: { title, body, slug: title.toLowerCase().replace(/\s+/g, '-') } })
  revalidatePath('/blog')
}
```

### Static Export Configuration

```javascript
// next.config.mjs â€” for static hosting (no Node.js server)
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // trailingSlash: true, // optional: /about/ instead of /about
}

export default nextConfig
```

