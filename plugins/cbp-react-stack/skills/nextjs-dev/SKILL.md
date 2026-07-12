---
name: nextjs-dev
description: >
  Build Next.js 14/15 App Router applications with Server/Client Components, route handlers,
  middleware, SEO metadata, Radix UI/shadcn patterns, static export, SSR/SSG,
  and testing with Vitest + Playwright. Use when developing or extending Next.js applications.
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


**Read:** `references/routing-layouts.md` for complete examples of root layout, nested layout, loading UI, error boundary, 404, dynamic routes, route groups, parallel routes, and intercepting routes.

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

### Component Boundary Rule

Mark the **interactive leaf**, not the parent. Push `'use client'` as far down the component tree as possible.

**Read:** `references/server-client-components.md` for data fetching patterns, client component examples, boundary rule code, and useSearchParams with Suspense.

---

## STEP 4: Data Fetching & Caching

**Read:** `references/data-fetching.md` for route handlers, dynamic route handlers (Next.js 15 Promise params), generateStaticParams, revalidation, server actions, and static export configuration.

---

## STEP 5: Middleware & Security

**Read:** `references/middleware-security.md` for complete security headers middleware and auth middleware pattern with matcher configuration.

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

**Read:** `references/testing-examples.md` for Vitest configuration, unit test examples, data layer mocking, and test commands.

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
