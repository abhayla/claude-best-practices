# Routing & Layout Examples


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
  (marketing)/        # Group â€” no /marketing in URL
    about/page.tsx    # /about
    pricing/page.tsx  # /pricing
    layout.tsx        # Shared marketing layout
  (app)/              # Group â€” no /app in URL
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

