---
name: jest-dev
description: >
  Jest testing reference: configuration (jest.config, transforms, moduleNameMapper),
  mocking (jest.mock/jest.fn/jest.spyOn/manual mocks), async testing, snapshot testing,
  coverage thresholds, parameterized tests, and React Testing Library integration.
  Use for writing and running Jest tests.
allowed-tools: "Read Grep Glob"
triggers: "jest, jest.mock, jest.fn, jest.spyOn, test runner, unit test jest, testing library jest, snapshot test"
argument-hint: "<pattern-to-look-up or 'config' or 'mock' or 'coverage' or 'snapshot' or 'async'>"
version: "1.0.0"
type: reference
---

# Jest Testing Reference

Jest patterns for configuration, mocking, async testing, snapshots, coverage, parameterized tests,
and framework integration. **Request:** $ARGUMENTS

---

## Configuration

### `jest.config.js`

```javascript
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',                    // 'node' for backend, 'jsdom' for DOM
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.{js,ts,tsx}', '**/*.{test,spec}.{js,ts,tsx}'],
  transform: {
    '^.+\\.tsx?$': 'ts-jest',                  // TypeScript via ts-jest
    '^.+\\.jsx?$': 'babel-jest',               // JavaScript via babel-jest (default)
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',            // Path aliases
    '\\.(css|less|scss)$': 'identity-obj-proxy', // CSS modules
    '\\.(png|jpg|svg)$': '<rootDir>/__mocks__/fileMock.js', // Static assets
  },
  setupFilesAfterSetup: ['<rootDir>/src/setupTests.ts'],
  clearMocks: true,                            // Auto-clear mock state between tests
  testTimeout: 10000,
};
```

For TypeScript config, use `import type { Config } from 'jest'` and `export default config` with the same options. Use `preset: 'ts-jest'` as shorthand for ts-jest transform + extensions.

### Setup File (`src/setupTests.ts`)

```typescript
import '@testing-library/jest-dom';

// Common global mock: window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: jest.fn(), removeListener: jest.fn(),
    addEventListener: jest.fn(), removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
```

| Environment | When to Use |
|-------------|-------------|
| `node` | Backend logic, APIs, no DOM needed |
| `jsdom` | React/DOM-heavy components |
| `@jest-environment docblock` | Per-file override: `/** @jest-environment node */` at top of file |

---

## Mocking

### `jest.mock()` -- Auto-Mock Entire Module

```typescript
import { fetchUser } from '../api/users';
jest.mock('../api/users'); // All exports become jest.fn() stubs

const mockedFetchUser = jest.mocked(fetchUser); // Typed mock (Jest 29+)

test('calls fetchUser', async () => {
  mockedFetchUser.mockResolvedValue({ id: 1, name: 'Alice' });
  const user = await service.getUser(1);
  expect(mockedFetchUser).toHaveBeenCalledWith(1);
});
```

### `jest.mock()` with Factory

```typescript
jest.mock('../lib/analytics', () => ({
  track: jest.fn(),
  identify: jest.fn(),
  __esModule: true,                            // Required for ES module mocks
}));
```

### Partial Mock with `jest.requireActual()`

```typescript
jest.mock('../utils/validation', () => ({
  ...jest.requireActual('../utils/validation'),
  validateEmail: jest.fn().mockReturnValue(true),
}));
```

### `jest.fn()` -- Standalone Mock Function

```typescript
const onSubmit = jest.fn();
onSubmit.mockReturnValue('success');
onSubmit.mockReturnValueOnce('first-call-only');
onSubmit.mockResolvedValue({ id: 1 });           // Wraps in Promise.resolve
onSubmit.mockRejectedValue(new Error('fail'));    // Wraps in Promise.reject
onSubmit.mockImplementation((data) => ({ ...data, id: 'generated' }));

expect(onSubmit).toHaveBeenCalledTimes(1);
expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ name: 'Alice' }));
```

### `jest.spyOn()` -- Spy on Existing Method

```typescript
import * as mathUtils from '../utils/math';

const spy = jest.spyOn(mathUtils, 'calculateTax').mockReturnValue(25);
expect(spy).toHaveBeenCalledWith(100, expect.any(Number));
spy.mockRestore();                             // Restore original implementation

// Spy on built-in
jest.spyOn(Date, 'now').mockReturnValue(1700000000000);
```

### Manual Mocks (`__mocks__/` directory)

Place `__mocks__/module-name.ts` adjacent to the real module. Jest uses it automatically when `jest.mock('./module-name')` is called. For `node_modules` mocks, place `__mocks__/` at the project root.

```typescript
// src/utils/__mocks__/http-client.ts
export const get = jest.fn().mockResolvedValue({ data: [] });
export const post = jest.fn().mockResolvedValue({ status: 201 });
```

### Mock Clearing vs Resetting vs Restoring

| Method | Clears Calls | Resets Implementation | Restores Original |
|--------|-------------|----------------------|-------------------|
| `mockClear()` | Yes | No | No |
| `mockReset()` | Yes | Yes (returns `undefined`) | No |
| `mockRestore()` | Yes | Yes | Yes (spyOn only) |

Set `clearMocks: true` or `restoreAllMocks: true` in config to auto-apply between tests.

---

## Async Testing

### async/await and resolves/rejects

```typescript
test('fetches data', async () => {
  const data = await fetchData('/endpoint');
  expect(data).toEqual({ status: 'ok' });
});

test('resolves with user', async () => {
  await expect(fetchUser(1)).resolves.toEqual({ id: 1, name: 'Alice' });
});

test('rejects on failure', async () => {
  await expect(fetchUser(-1)).rejects.toThrow('Not Found');
});
```

### `done` Callback (callback-based code)

```typescript
test('calls callback on success', (done) => {
  fetchWithCallback('/data', (err, result) => {
    try {
      expect(err).toBeNull();
      done();
    } catch (error) {
      done(error);                               // Fail test with error details
    }
  });
});
```

### Fake Timers

```typescript
beforeEach(() => { jest.useFakeTimers(); });
afterEach(() => { jest.useRealTimers(); });

test('debounce calls handler after delay', () => {
  const handler = jest.fn();
  const debounced = debounce(handler, 300);
  debounced();
  expect(handler).not.toHaveBeenCalled();
  jest.advanceTimersByTime(300);
  expect(handler).toHaveBeenCalledTimes(1);
});

// jest.runAllTimers() — runs all pending timers at once
// jest.runOnlyPendingTimers() — runs only currently pending (not newly scheduled)
// jest.useFakeTimers({ now: new Date('2025-01-15') }) — also mocks Date
```

---

## Snapshot Testing

### File and Inline Snapshots

```typescript
test('renders config correctly', () => {
  expect(generateConfig({ debug: true })).toMatchSnapshot();
  // Snapshot saved in __snapshots__/<testFile>.snap
});

test('formats error message', () => {
  expect(formatError('NOT_FOUND')).toMatchInlineSnapshot(`
    {
      "code": "NOT_FOUND",
      "message": "Resource not found"
    }
  `);
});
```

### Property Matchers (for dynamic values)

```typescript
test('snapshot with dynamic fields', () => {
  expect(createUser({ name: 'Alice' })).toMatchSnapshot({
    id: expect.any(String),
    createdAt: expect.any(Date),
  });
});
```

### Custom Serializers

```javascript
// jest.config.js
module.exports = { snapshotSerializers: ['enzyme-to-json/serializer'] };

// Or per-test
expect.addSnapshotSerializer({
  test: (val) => val && val.hasOwnProperty('className'),
  print: (val) => `ClassName<${val.className}>`,
});
```

### Updating Snapshots

```bash
npx jest --updateSnapshot                      # Update all outdated snapshots
npx jest -u --testPathPattern="component"      # Update specific files only
```

---

## Framework Integration

### React Testing Library

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('submits form data', async () => {
  const user = userEvent.setup();
  const handleSubmit = jest.fn();
  render(<LoginForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
  await user.click(screen.getByRole('button', { name: /sign in/i }));

  expect(handleSubmit).toHaveBeenCalledWith(
    expect.objectContaining({ email: 'alice@example.com' }),
  );
});
```

### Testing Hooks with `renderHook`

```typescript
import { renderHook, act } from '@testing-library/react';

test('increments counter', () => {
  const { result } = renderHook(() => useCounter(0));
  expect(result.current.count).toBe(0);
  act(() => { result.current.increment(); });
  expect(result.current.count).toBe(1);
});

test('hook with context provider wrapper', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <ThemeProvider theme="dark">{children}</ThemeProvider>
  );
  const { result } = renderHook(() => useTheme(), { wrapper });
  expect(result.current.theme).toBe('dark');
});
```

For multi-provider setups, create a `renderWithProviders` helper that wraps `render` with a `wrapper` option combining all context providers.

---

## Coverage

```javascript
// jest.config.js
module.exports = {
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.*',
    '!src/generated/**',
  ],
  coverageThreshold: {
    global: { branches: 75, functions: 80, lines: 80, statements: 80 },
    './src/critical/': { branches: 90, lines: 95 },  // Stricter per-directory
  },
  coverageReporters: ['text', 'text-summary', 'lcov', 'html'],
};
```

```bash
npx jest --coverage                            # Full suite with coverage
npx jest --coverage --changedSince=main        # Only changed files
```

---

## Parameterized Tests

### Array and Template Literal Syntax

```typescript
test.each([
  { input: 0, expected: 'zero' },
  { input: 1, expected: 'one' },
  { input: -1, expected: 'negative' },
])('converts $input to "$expected"', ({ input, expected }) => {
  expect(numberToWord(input)).toBe(expected);
});

test.each`
  a     | b     | expected
  ${1}  | ${2}  | ${3}
  ${-1} | ${1}  | ${0}
`('adds $a + $b = $expected', ({ a, b, expected }) => {
  expect(add(a, b)).toBe(expected);
});
```

### `describe.each` for Grouped Suites

```typescript
describe.each([
  { env: 'development', debug: true },
  { env: 'production', debug: false },
])('config for $env', ({ env, debug }) => {
  test('sets debug flag', () => {
    expect(loadConfig(env).debug).toBe(debug);
  });
});
```

---

## Module Resolution

### Path Aliases

```javascript
// jest.config.js — must mirror tsconfig paths
module.exports = {
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
  },
};
```

### ESM Packages (`transformIgnorePatterns`)

```javascript
// Jest runs CommonJS by default. ESM-only packages must be un-ignored for transform.
module.exports = {
  transformIgnorePatterns: [
    'node_modules/(?!(axios|uuid|nanoid|@esm-package)/)',
  ],
};
```

### CSS/Asset Imports

Create `__mocks__/fileMock.js` (`module.exports = 'test-file-stub'`) and `__mocks__/styleMock.js` (`module.exports = {}`) at the project root, then map them in `moduleNameMapper`:
- `'\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js'`
- `'\\.(css|less|scss)$': '<rootDir>/__mocks__/styleMock.js'`

---

## Commands

```bash
npx jest                                       # Run all tests
npx jest --watch                               # Watch mode (re-run on changes)
npx jest --watchAll                            # Watch all files (no git filter)
npx jest --verbose                             # Detailed per-test output
npx jest path/to/file.test.ts                  # Run single file
npx jest -t "pattern"                          # Run tests matching name pattern
npx jest --changedSince=main                   # Tests changed since branch point
npx jest --forceExit                           # Force exit (leaked handles)
npx jest --detectOpenHandles                   # Debug leaked async handles
npx jest --bail                                # Stop on first failure
npx jest --maxWorkers=4                        # Limit parallelism
npx jest --no-cache                            # Ignore transform cache
npx jest --passWithNoTests                     # Exit 0 when no tests found (CI)
npx jest --projects ./packages/*               # Multi-project mode (monorepo)
```

---

## CRITICAL RULES

- Always set `restoreAllMocks: true` in config or call `jest.restoreAllMocks()` in `afterEach` -- leaked mocks cause cascading failures across tests
- Use `jest.mocked()` (Jest 29+) for typed mocks instead of manual `as jest.MockedFunction<typeof fn>` casting
- Never call `jest.mock()` inside a test body -- mock calls are hoisted to the top of the file; placing them inside tests creates confusing execution order
- Use `jest.requireActual()` for partial mocks -- without it, the entire module is replaced and unmocked exports return `undefined`
- Add `__esModule: true` to factory mocks of ES modules -- without it, default exports are not resolved correctly
- Pair `jest.useFakeTimers()` in `beforeEach` with `jest.useRealTimers()` in `afterEach` -- forgetting to restore real timers breaks subsequent async tests
- Use `--forceExit` only for debugging, not as a permanent fix -- find and close the leaked handle with `--detectOpenHandles` instead
- Set `transformIgnorePatterns` to un-ignore ESM-only packages -- Jest runs CommonJS and cannot process untransformed `import`/`export` syntax
- Use `test.each` for parameterized tests -- never copy-paste tests that differ only in input data
- Prefer `jest.spyOn()` over `jest.mock()` when only one method needs mocking -- less invasive, easier to restore
- Set `clearMocks: true` in config to auto-clear mock call history between tests -- manual `mockClear()` in every `afterEach` is error-prone
