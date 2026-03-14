---
name: nextjs-dev
description: >
  Next.js 14/15 App Router development: Server/Client Components, route handlers,
  middleware, SEO metadata, Radix UI/shadcn patterns, static export, SSR/SSG,
  and testing with Vitest + Playwright. Use for building Next.js applications.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "nextjs, next.js, next, app router, server components, RSC, route handler"
argument-hint: "<feature-description or 'setup' or 'api' or 'middleware' or 'seo'>"
version: "1.0.0"
type: workflow
---

# Next.js App Router Development

Build Next.js 14/15 applications with the App Router, React Server Components, TypeScript, and modern tooling.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup

Scaffold or verify the Next.js App Router project structure.

### Create New Project

```bash
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir --use-npm
cd my-app
npm run dev -- --turbopack
```

### Project Structure

```
src/
  app/
    layout.tsx            # Root layout (Server Component)
    page.tsx              # Home page
    loading.tsx           # Loading UI (Suspense fallback)
    error.tsx             # Error boundary ('use client')
    not-found.tsx         # 404 page
    (marketing)/          # Route group (no URL segment)
      about/page.tsx
    dashboard/
      layout.tsx          # Nested layout
      page.tsx
      [slug]/page.tsx     # Dynamic route
    api/
      health/route.ts     # Route handler
  components/
    ui/                   # Base UI components (Button, Card, Input)
    layout/               # Layout components (Header, Sidebar, Footer)
    [feature]/            # Feature-scoped components
  lib/
    cn.ts                 # clsx + tailwind-merge utility
    db.ts                 # Database client (server-only)
    validators.ts         # Zod schemas
  hooks/                  # Client-side custom hooks
  types/                  # Shared TypeScript types
public/                   # Static assets (favicon, images)
next.config.mjs           # Next.js configuration
tailwind.config.ts        # Tailwind CSS configuration
```

### Dependencies (package.json essentials)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "next": "^15.2.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-slot": "^1.1.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.6.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "tailwindcss": "^3.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/node": "^22.0.0",
    "vitest": "^3.0.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@playwright/test": "^1.49.0"
  }
}
```

### next.config.mjs

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for development checks
  reactStrictMode: true,

  // For static export (no Node.js server):
  // output: 'export',

  // Image optimization settings
  images: {
    // For static export, use unoptimized:
    // unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.example.com',
      },
    ],
  },
}

export default nextConfig
```

### Verify Setup

```bash
npm run build     # Full production build
npm run dev       # Dev server with Turbopack
npx tsc --noEmit  # Type check
```

Fix all type and build errors before proceeding.

---

## STEP 2: Routing & Layouts

App Router uses file-system conventions. Each folder represents a route segment. Special files define UI for that segment.

### File Conventions

| File | Purpose | Component Type |
|------|---------|----------------|
| `layout.tsx` | Shared UI that wraps children, preserved across navigations | Server |
| `page.tsx` | Unique UI for a route, makes the route publicly accessible | Server |
| `loading.tsx` | Suspense fallback shown while the page loads | Server |
| `error.tsx` | Error boundary for the route segment | Client (`'use client'`) |
| `not-found.tsx` | UI shown when `notFound()` is called or route does not exist | Server |
| `route.ts` | API endpoint (GET, POST, PUT, DELETE) | Server |

### Root Layout (required)

```tsx
// src/app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: {
    default: 'My App',
    template: '%s | My App',
  },
  description: 'Application description for SEO.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  )
}
```

### Nested Layout

```tsx
// src/app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      <nav className="w-64 border-r p-4">
        {/* Sidebar navigation */}
      </nav>
      <main className="flex-1 p-8">{children}</main>
    </div>
  )
}
```

### Loading UI

```tsx
// src/app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div aria-busy="true" className="animate-pulse space-y-4 p-8">
      <div className="h-8 w-1/3 rounded bg-gray-200" />
      <div className="h-64 rounded bg-gray-200" />
      <div className="h-8 w-2/3 rounded bg-gray-200" />
    </div>
  )
}
```

### Error Boundary

```tsx
// src/app/dashboard/error.tsx
'use client'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center gap-4 p-8" role="alert">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="text-gray-600">
        {error.digest
          ? `Error ID: ${error.digest}`
          : error.message}
      </p>
      <button
        onClick={reset}
        className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  )
}
```

### Custom 404

```tsx
// src/app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-gray-600">Page not found.</p>
      <Link href="/" className="text-blue-600 hover:underline">
        Return home
      </Link>
    </div>
  )
}
```

### Dynamic Routes

```tsx
// src/app/dashboard/[slug]/page.tsx
interface PageProps {
  params: Promise<{ slug: string }>
}

export default async function DashboardDetailPage({ params }: PageProps) {
  const { slug } = await params
  // Fetch data using slug
  return <h1>Dashboard: {slug}</h1>
}
```

### Route Groups

```
src/app/
  (marketing)/        # Group — no /marketing in URL
    about/page.tsx    # /about
    pricing/page.tsx  # /pricing
    layout.tsx        # Shared marketing layout
  (app)/              # Group — no /app in URL
    dashboard/page.tsx  # /dashboard
    settings/page.tsx   # /settings
    layout.tsx          # Shared app layout
```

### Parallel Routes

```
src/app/dashboard/
  @analytics/page.tsx   # Parallel slot
  @activity/page.tsx    # Parallel slot
  layout.tsx            # Receives both as props
  page.tsx
```

```tsx
// src/app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  activity,
}: {
  children: React.ReactNode
  analytics: React.ReactNode
  activity: React.ReactNode
}) {
  return (
    <div>
      {children}
      <div className="grid grid-cols-2 gap-4">
        {analytics}
        {activity}
      </div>
    </div>
  )
}
```

### Intercepting Routes

```
src/app/
  feed/
    page.tsx
    (..)photo/[id]/page.tsx   # Intercepts /photo/[id] when navigating from /feed
  photo/
    [id]/page.tsx             # Direct access renders full page
```

---

## STEP 3: Server vs Client Components

React Server Components (RSC) are the default in the App Router. Add `'use client'` only when the component requires browser interactivity.

### Decision Table

| Need | Component Type | Why |
|------|----------------|-----|
| Database/API access | Server | Direct access to data layer, no client bundle cost |
| Environment secrets | Server | Server-only code never reaches the browser |
| `useState` / `useEffect` | Client | React hooks require client runtime |
| Event handlers (`onClick`, `onChange`) | Client | DOM events require browser |
| Browser APIs (`localStorage`, `IntersectionObserver`) | Client | Not available on server |
| Static content rendering | Server | Zero JavaScript shipped for static content |
| Third-party client libraries | Client | Libraries that use hooks or DOM |

### Server Component Data Fetching (Repository Pattern)

```tsx
// src/lib/data/posts.ts — server-only data layer
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
// src/app/blog/[slug]/page.tsx — Server Component
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

---

## STEP 4: Data Fetching & Caching

### Route Handlers (API Endpoints)

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

### Dynamic Route Handler (Next.js 15 — params is a Promise)

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
// next.config.mjs — for static hosting (no Node.js server)
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // trailingSlash: true, // optional: /about/ instead of /about
}

export default nextConfig
```

---

## STEP 5: Middleware & Security

### Middleware File

```typescript
// src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  // Security headers
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), browsing-topics=()'
  )

  // HSTS — production only
  if (process.env.NODE_ENV === 'production') {
    response.headers.set(
      'Strict-Transport-Security',
      'max-age=63072000; includeSubDomains; preload'
    )
  }

  // Content Security Policy
  const cspDirectives = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "connect-src 'self' https:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ]
  response.headers.set('Content-Security-Policy', cspDirectives.join('; '))

  return response
}

export const config = {
  matcher: [
    // Match all paths except static files and Next.js internals
    '/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
}
```

### Auth Middleware Pattern

```typescript
// src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const protectedPaths = ['/dashboard', '/settings', '/api/protected']
const authPages = ['/login', '/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const sessionToken = request.cookies.get('session-token')?.value

  // Redirect unauthenticated users to login
  const isProtected = protectedPaths.some((path) => pathname.startsWith(path))
  if (isProtected && !sessionToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Redirect authenticated users away from auth pages
  const isAuthPage = authPages.some((path) => pathname.startsWith(path))
  if (isAuthPage && sessionToken) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Add security headers
  const response = NextResponse.next()
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')

  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
}
```

---

## STEP 6: SEO & Metadata

Next.js provides first-class SEO support via the Metadata API. For complete examples, read `references/seo-metadata.md`.

### Key Patterns

- **Static metadata**: Export `metadata` object from `layout.tsx` with `title.template`, `openGraph`, `twitter`, `robots`
- **Dynamic metadata**: Export `generateMetadata` function from `page.tsx` for dynamic routes — fetches data and returns `Metadata`
- **Sitemap**: `src/app/sitemap.ts` returns `MetadataRoute.Sitemap` array
- **Robots**: `src/app/robots.ts` returns `MetadataRoute.Robots` with `rules` and `sitemap` URL
- **JSON-LD**: Use `next/script` with `type="application/ld+json"` for structured data (Article, Organization, etc.)

### Quick Example (Dynamic Metadata)

```tsx
// src/app/blog/[slug]/page.tsx
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const post = await getPostBySlug(slug)
  if (!post) return { title: 'Not Found' }
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: { title: post.title, description: post.excerpt, type: 'article' },
  }
}
```

---

## STEP 7: UI Patterns

For complete component examples (CVA Button, Radix Dialog, fonts, images), read `references/ui-patterns.md`.

### Key Patterns

- **`cn()` utility**: Combine `clsx` + `tailwind-merge` for conditional class names without conflicts
- **`next/font`**: Self-host Google or local fonts — assign to CSS variable, use in Tailwind config
- **`next/image`**: Always set `width`/`height` or `fill` + `sizes` prop. Use `priority` for above-the-fold images
- **`next/dynamic`**: Lazy-load heavy client components (charts, editors) with `{ ssr: false }`
- **CVA (class-variance-authority)**: Define typed component variants with `cva()`, extract `VariantProps`
- **Radix UI**: Use headless primitives for dialogs, dropdowns, tooltips — style with Tailwind

### Quick Example (cn utility)

```typescript
// src/lib/cn.ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### Quick Example (Lazy Loading)

```tsx
import dynamic from 'next/dynamic'

const Chart = dynamic(() => import('@/components/Chart'), {
  loading: () => <div className="h-64 animate-pulse rounded bg-gray-200" />,
  ssr: false,
})
```

---

## STEP 8: Testing

### Vitest Configuration for Next.js

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}', 'tests/**/*.test.{ts,tsx}'],
  },
})
```

```typescript
// tests/setup.ts
import '@testing-library/jest-dom/vitest'
```

### Unit Test Example

```tsx
// src/components/ui/__tests__/Button.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button', () => {
  it('renders with default variant', () => {
    render(<Button>Click me</Button>)
    const button = screen.getByRole('button', { name: 'Click me' })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('bg-blue-600')
  })

  it('renders destructive variant', () => {
    render(<Button variant="destructive">Delete</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-red-600')
  })

  it('calls onClick handler', async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('renders as child element with asChild', () => {
    render(
      <Button asChild>
        <a href="/link">Link Button</a>
      </Button>
    )
    expect(screen.getByRole('link', { name: 'Link Button' })).toBeInTheDocument()
  })

  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

### Data Layer Test (Mocking DB)

```tsx
// src/lib/data/__tests__/posts.test.ts
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/db', () => ({
  db: {
    post: {
      findMany: vi.fn().mockResolvedValue([{ id: '1', title: 'Test', slug: 'test' }]),
      findUnique: vi.fn().mockResolvedValue({ id: '1', title: 'Test', slug: 'test' }),
    },
  },
}))

import { getPostBySlug, getRecentPosts } from '../posts'

describe('posts data layer', () => {
  it('fetches recent posts', async () => {
    const posts = await getRecentPosts(5)
    expect(posts).toHaveLength(1)
  })

  it('fetches a post by slug', async () => {
    const post = await getPostBySlug('test')
    expect(post?.slug).toBe('test')
  })
})
```

### Run Tests

```bash
npx vitest run              # Unit tests
npx vitest run --coverage   # With coverage
npx playwright test         # E2E tests
npx tsc --noEmit            # Type check
```

For Playwright configuration, use the `/playwright` skill. For Vitest patterns, use the `/vitest-dev` skill.

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| Hydration mismatch error | Server and client HTML differ (browser-only values like `Date.now()`, `window.innerWidth`) | Move browser-dependent logic into `useEffect` or wrap component with `'use client'` + `Suspense` |
| `useState` or `useEffect` error in Server Component | Missing `'use client'` directive at top of file | Add `'use client'` as the first line of the component file |
| Middleware not running | Matcher pattern does not match the request path | Check `config.matcher` regex; use the middleware debugging pattern `console.log(request.nextUrl.pathname)` |
| Static export fails with dynamic features | Using `cookies()`, `headers()`, or dynamic route handlers with `output: 'export'` | Remove dynamic features or switch to server deployment; use `generateStaticParams` for dynamic routes |
| `params` type error in Next.js 15 | `params` is now `Promise<{ slug: string }>` instead of `{ slug: string }` | Change type to `Promise<>` and add `await params` before accessing properties |
| Font loading FOUT (flash of unstyled text) | Font not preloaded or `display` not set | Use `next/font` with `display: 'swap'`; never load fonts from external CDNs |
| `next/image` not working with static export | Image optimization requires a Node.js server | Set `images: { unoptimized: true }` in `next.config.mjs` when using `output: 'export'` |
| Build error: server-only import in Client Component | Importing a module that uses `server-only` or Node.js APIs in a `'use client'` file | Move the import to a Server Component and pass data as props to the Client Component |
| `useSearchParams` build error | `useSearchParams()` not wrapped in `Suspense` boundary | Create a wrapper component with `Suspense` around the component using `useSearchParams` |
| Route handler returns wrong content type | Using `Response` instead of `NextResponse.json()` | Use `NextResponse.json()` for JSON responses; it sets `Content-Type` automatically |
| Parallel route `default.tsx` missing | Next.js cannot render a parallel slot when navigating to an unmatched route | Add `default.tsx` to each parallel route slot returning `null` or fallback UI |
| Server Action fails silently | Action not marked with `'use server'` or not imported correctly | Ensure the file has `'use server'` at top, and the function is exported and `async` |

---

## CRITICAL RULES

### MUST DO

- Server Components by default — only add `'use client'` for interactivity (hooks, event handlers, browser APIs)
- Use `loading.tsx` + `error.tsx` per route segment for progressive loading and error recovery
- Route Handlers return `NextResponse.json()` — it sets headers and serializes correctly
- Dynamic routes use `generateMetadata` — never hardcode page titles on dynamic pages
- Middleware for cross-cutting concerns (security headers, auth redirects, request logging)
- Use `next/font` for all fonts — it self-hosts and eliminates external network requests
- Await `params` in Next.js 15 — `params` is a `Promise`, not a plain object
- Wrap `useSearchParams()` in a `Suspense` boundary — required for correct static/dynamic rendering
- Use the `server-only` package to guard server code — `import 'server-only'` in data layer modules
- Run `npx tsc --noEmit` and `npm run build` before committing — zero type errors, zero build errors

### MUST NOT DO

- Import server-only code (DB clients, env secrets) in Client Components — causes build errors or leaks secrets to the browser
- Fetch your own API routes from Server Components — call the data layer directly instead of making HTTP requests to yourself
- Use `'use client'` on `layout.tsx` — it opts out all children from server rendering, eliminating RSC benefits for the entire subtree
- Use `useEffect` for data fetching in Server Components — use `async`/`await` directly in the component body
- Skip `loading.tsx` — users see a blank screen while Server Components render on the server
- Use `next/image` with `unoptimized` in production (only acceptable for `output: 'export'` static builds)
- Use `Response` instead of `NextResponse` in route handlers — `NextResponse` provides cookie/header helpers and consistent behavior
- Hardcode font URLs from CDNs (Google Fonts CDN, Adobe Fonts) — use `next/font` for self-hosting and performance
- Skip the `sizes` prop on `next/image` — without it, the browser downloads the largest image variant regardless of viewport
