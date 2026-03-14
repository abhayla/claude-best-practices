---
paths:
  - "**/app/**/*.tsx"
  - "**/app/**/*.ts"
  - "**/components/**/*.tsx"
description: Next.js App Router and React Server Component patterns and conventions.
---

# Next.js App Router Rules

## Server vs Client Components
- Server Components by default — only add `'use client'` for hooks, event handlers, or browser APIs
- Mark the interactive leaf component as `'use client'` — never mark parent layouts
- Never import server-only code (DB clients, `process.env` secrets) in Client Components — causes build errors or leaks secrets
- Never fetch your own API routes from Server Components — call the data layer directly

## Route File Conventions
- Every route segment should have `loading.tsx` (skeleton with `aria-busy`) and `error.tsx` (`'use client'` with `reset()`)
- `error.tsx` must be a Client Component — error boundaries require `useEffect`/`useState`
- Use `not-found.tsx` per route segment — never return a generic 404 from the layout

## Data Fetching
- Fetch data in Server Components using `async/await` — never use `useEffect` for data that can be server-rendered
- Route Handlers (`route.ts`) return `NextResponse.json()` — never raw `Response` constructor
- Use `generateStaticParams` for static paths on dynamic routes — never hardcode paths in config
- Use `generateMetadata` for dynamic SEO — never hardcode page titles

## Middleware
- Place cross-cutting concerns (security headers, auth redirects) in `middleware.ts` — not per-route logic
- Matcher must exclude static assets: `matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']`
- Set security headers: CSP, HSTS (production only), X-Frame-Options DENY, X-Content-Type-Options nosniff

## Component Patterns
- Use `cn()` utility (`clsx` + `tailwind-merge`) for conditional class names — never manual string concatenation
- Use `next/font` for fonts — never import from CDN (causes layout shift)
- Use `next/image` with explicit `width`/`height` or `sizes` prop — never unset dimensions
- Use `next/dynamic` for heavy client-side components (charts, maps, editors) — import with `{ ssr: false }`

## Static Export
- When using `output: 'export'`: no API routes, no middleware, no server-only features
- Set `images: { unoptimized: true }` — Image Optimization requires a server
- Client-side data fetching with `useEffect` + `useState` replaces Server Component fetching

## Anti-Patterns
- `'use client'` on `layout.tsx` — opts out all children from server rendering
- `useEffect` for data fetching in Server Components — use `async/await` directly
- Importing `server-only` packages in `'use client'` files — causes build-time errors
- Missing `loading.tsx` — users see blank page while Server Components render on navigation
