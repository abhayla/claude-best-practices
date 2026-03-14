---
name: vitest-dev
description: >
  Vitest testing reference: configuration, mocking (vi.mock/vi.fn/vi.spyOn), snapshot
  testing, coverage with v8/istanbul, workspace mode for monorepos, and framework
  integration (React Testing Library, Vue Test Utils). Use for writing and running Vitest tests.
allowed-tools: "Bash Read Grep Glob"
triggers: "vitest, vi.mock, vi.fn, test runner, unit test vite, testing library vitest"
argument-hint: "<pattern-to-look-up or 'config' or 'mock' or 'coverage' or 'workspace'>"
version: "1.0.0"
type: reference
---

# Vitest Testing Reference

Vitest patterns for configuration, mocking, async testing, framework integration, coverage, and
monorepo workspace mode. **Request:** $ARGUMENTS

---

## Configuration

### Standalone Config (`vitest.config.ts`)

```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'jsdom',              // 'jsdom' for DOM fidelity, 'happy-dom' for speed
    globals: true,                     // Import describe/it/expect globally
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'e2e/**'],
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
    },
    testTimeout: 10000,
  },
});
```

### Inline Config (inside `vite.config.ts`)

```typescript
/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: { environment: 'jsdom', globals: true, setupFiles: './src/test/setup.ts' },
});
```

### Setup File (`src/test/setup.ts`)

```typescript
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => { cleanup(); });
```

| Environment | Install | Best For |
|-------------|---------|----------|
| `jsdom` | `npm i -D jsdom` | DOM-heavy tests, accurate browser behavior |
| `happy-dom` | `npm i -D happy-dom` | Speed-critical suites, basic DOM needs |
| `node` | built-in | Pure logic, no DOM required |

---

## Test Patterns

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('formatCurrency', () => {
  it('formats whole numbers with two decimals', () => {
    expect(formatCurrency(100)).toBe('$100.00');
  });
});
```

### Lifecycle Hooks

```typescript
describe('Service', () => {
  let service: Service;
  beforeAll(async () => { await connectTestDb(); });       // Once before all
  beforeEach(() => { service = new Service(); });          // Before each test
  afterEach(() => { vi.restoreAllMocks(); });              // Cleanup mocks
  afterAll(async () => { await disconnectTestDb(); });     // Once after all

  it('inserts a record', async () => {
    const result = await service.insert({ name: 'test' });
    expect(result.id).toBeDefined();
  });
});
```

### Parameterized Tests (`it.each`)

```typescript
it.each([
  { input: 0, expected: 'zero' },
  { input: 1, expected: 'one' },
  { input: -1, expected: 'negative' },
])('converts $input to "$expected"', ({ input, expected }) => {
  expect(numberToWord(input)).toBe(expected);
});

// Table syntax
it.each`
  a     | b     | expected
  ${1}  | ${2}  | ${3}
  ${-1} | ${1}  | ${0}
`('adds $a + $b = $expected', ({ a, b, expected }) => {
  expect(add(a, b)).toBe(expected);
});
```

### Other Modifiers

```typescript
it.todo('handles network timeout gracefully');   // Planned — shows in reports
it.concurrent('fetches users', async () => { }); // Parallel within describe block
```

### Snapshot Testing

```typescript
it('matches saved snapshot', () => {
  expect(generateConfig({ debug: true })).toMatchSnapshot();
});

it('matches inline snapshot', () => {
  expect(formatError('NOT_FOUND')).toMatchInlineSnapshot(`
    { "code": "NOT_FOUND", "message": "Resource not found" }
  `);
});
```

---

## Mocking

### Auto-Mock Entire Module

```typescript
import { fetchUser } from '@/api/users';
vi.mock('@/api/users'); // All exports become vi.fn() stubs

it('calls fetchUser', async () => {
  vi.mocked(fetchUser).mockResolvedValue({ id: 1, name: 'Alice' });
  const user = await service.getUser(1);
  expect(fetchUser).toHaveBeenCalledWith(1);
});
```

### Manual Mock with Factory

```typescript
vi.mock('@/lib/analytics', () => ({
  track: vi.fn(),
  identify: vi.fn(),
}));
```

### `vi.fn()` -- Standalone Mock Function

```typescript
const onSubmit = vi.fn();
onSubmit.mockReturnValue('success');
onSubmit.mockReturnValueOnce('first-call-only');
onSubmit.mockResolvedValue({ id: 1 });           // Async
onSubmit.mockRejectedValue(new Error('fail'));    // Async rejection
onSubmit.mockImplementation((data) => ({ ...data, id: 'generated' }));

expect(onSubmit).toHaveBeenCalledTimes(1);
expect(onSubmit).toHaveBeenCalledWith({ name: 'Alice' });
```

### `vi.spyOn()` -- Spy on Existing Method

```typescript
import * as mathUtils from '@/utils/math';
const spy = vi.spyOn(mathUtils, 'calculateTax').mockReturnValue(25);
expect(spy).toHaveBeenCalledWith(100, expect.any(Number));

// Spy on built-in
vi.spyOn(Date, 'now').mockReturnValue(1700000000000);
```

### `vi.stubGlobal()` -- Mock Globals

```typescript
vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ data: 'test' }),
}));
```

### `vi.hoisted()` -- Variables Before Mock Hoisting

```typescript
// vi.mock is hoisted above imports; vi.hoisted runs even earlier
const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock('@/lib/http-client', () => ({
  httpClient: { get: mocks.get, post: mocks.post },
}));

it('uses hoisted mock', async () => {
  mocks.get.mockResolvedValue({ users: [] });
  await apiService.getUsers();
  expect(mocks.get).toHaveBeenCalledWith('/users');
});
```

### `__mocks__/` Directory

Place `__mocks__/module.ts` next to the real module. Vitest uses it automatically on `vi.mock()`.

### `vi.importActual()` -- Partial Module Mock

```typescript
vi.mock('@/utils/validation', async () => {
  const actual = await vi.importActual<typeof import('@/utils/validation')>('@/utils/validation');
  return { ...actual, validateEmail: vi.fn().mockReturnValue(true) };
});
```

---

## Async Testing

```typescript
it('fetches data', async () => {
  expect(await fetchData('/endpoint')).toEqual({ status: 'ok' });
});
it('rejects on failure', async () => {
  await expect(fetchData('/bad')).rejects.toThrow('Not Found');
});
```

### Fake Timers

```typescript
beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { vi.useRealTimers(); });

it('calls handler after delay', () => {
  const handler = vi.fn();
  const debounced = debounce(handler, 300);
  debounced();
  expect(handler).not.toHaveBeenCalled();
  vi.advanceTimersByTime(300);
  expect(handler).toHaveBeenCalledOnce();
});

// For async code (Promises + setTimeout), use the async variant
it('retries with backoff', async () => {
  const fetchMock = vi.fn()
    .mockRejectedValueOnce(new Error('fail'))
    .mockResolvedValueOnce({ ok: true });
  const promise = retryWithBackoff(fetchMock);
  await vi.advanceTimersByTimeAsync(1000);
  expect(await promise).toEqual({ ok: true });
});
```

### `vi.waitFor()` (Vitest 1.0+)

```typescript
it('eventually resolves', async () => {
  let value = 'pending';
  setTimeout(() => { value = 'done'; }, 100);
  await vi.waitFor(() => { expect(value).toBe('done'); });
});
```

---

## Framework Integration

### React (Testing Library)

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('LoginForm', () => {
  it('renders fields', () => {
    render(<LoginForm onSubmit={vi.fn()} />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('submits form data', async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();
    render(<LoginForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await user.type(screen.getByLabelText(/password/i), 'secret123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'alice@example.com',
      password: 'secret123',
    });
  });

  it('shows validation error', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });
});
```

### Vue (Vue Test Utils)

```typescript
import { mount, flushPromises } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import CounterView from '@/components/CounterView.vue';
import { useCounterStore } from '@/stores/counter';

describe('CounterView', () => {
  it('renders count from store', () => {
    const wrapper = mount(CounterView, {
      global: { plugins: [createTestingPinia({ initialState: { counter: { count: 5 } } })] },
    });
    expect(wrapper.text()).toContain('5');
  });

  it('increments on click', async () => {
    const wrapper = mount(CounterView, {
      global: { plugins: [createTestingPinia({ stubActions: false })] },
    });
    await wrapper.find('[data-testid="increment-btn"]').trigger('click');
    expect(useCounterStore().count).toBe(1);
  });

  it('calls action on mount', async () => {
    mount(CounterView, {
      global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
    });
    await flushPromises();
    expect(useCounterStore().fetchInitialCount).toHaveBeenCalledOnce();
  });
});
```

---

## Coverage

| Provider | Package | Strengths |
|----------|---------|-----------|
| V8 | `@vitest/coverage-v8` | Faster. Since 3.2, AST-based remapping matches Istanbul accuracy. |
| Istanbul | `@vitest/coverage-istanbul` | Mature, widest ecosystem support. |

```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.d.ts', 'src/**/*.test.*', 'src/**/*.stories.*', 'src/generated/**'],
      thresholds: { lines: 80, branches: 75, functions: 80, statements: 80 },
    },
  },
});
```

```bash
npm i -D @vitest/coverage-v8 && vitest run --coverage
```

---

## Workspace Mode (Monorepo)

### Projects Config (Vitest 3.2+, replaces deprecated `vitest.workspace.ts`)

```typescript
// vitest.config.ts (root)
export default defineConfig({
  test: {
    projects: [
      'packages/*',                          // Glob: each package has its own config
      { test: { name: 'unit', include: ['src/**/*.test.ts'], environment: 'node' } },
      { test: { name: 'browser', include: ['src/**/*.browser.test.ts'], environment: 'jsdom' } },
    ],
  },
});
```

```typescript
// packages/web/vitest.config.ts — per-package config
export default defineConfig({
  test: { name: 'web', environment: 'jsdom', include: ['src/**/*.test.{ts,tsx}'] },
});
```

Run specific project: `vitest --project web` or multiple: `vitest --project api --project shared`

---

## Commands

```bash
vitest                        # Watch mode (default)
vitest run                    # Single run (CI)
vitest run --coverage         # With coverage
vitest run src/utils/         # Run specific directory
vitest run -t "pattern"       # Run tests matching pattern
vitest --ui                   # Browser UI (install @vitest/ui)
vitest --project web          # Run specific workspace project
vitest list                   # List test files without running
```

---

## CRITICAL RULES

- Always call `vi.restoreAllMocks()` in `afterEach` -- leaked mocks cause cascading failures across tests
- Use `happy-dom` for speed when tests only need basic DOM; use `jsdom` when DOM fidelity matters (layout, events, accessibility queries)
- Never call `vi.mock()` without corresponding cleanup -- mocks persist across tests in the same file
- Use `vi.hoisted()` for variables referenced in mock factories -- `vi.mock` calls are hoisted above imports, so regular `const` declarations are not yet initialized when the factory runs
- Prefer `vi.spyOn()` over `vi.mock()` when only one method needs mocking -- less invasive, preserves the rest of the module
- Use `it.each` for parameterized tests -- never copy-paste tests that differ only in input data
- Use `vi.advanceTimersByTimeAsync()` instead of `vi.advanceTimersByTime()` when code under test uses async timers -- the sync version will not flush microtasks
- Pair `vi.useFakeTimers()` in `beforeEach` with `vi.useRealTimers()` in `afterEach` -- forgetting to restore real timers breaks subsequent async tests
- In Vitest 3.2+, use the `projects` config in `vitest.config.ts` instead of the deprecated `vitest.workspace.ts` file
