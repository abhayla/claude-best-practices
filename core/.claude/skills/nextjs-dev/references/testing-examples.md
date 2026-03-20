# Testing Examples


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
