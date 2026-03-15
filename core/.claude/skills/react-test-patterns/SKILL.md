---
name: react-test-patterns
description: >
  Execute advanced React testing workflows including RTL custom renders,
  Server Component testing, hook testing, form interaction simulation,
  state management verification, and accessibility audits.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<test-scope> [--component|--hook|--rsc|--form|--state]"
version: "1.0.0"
---

# React Test Patterns

Advanced React testing workflow covering component rendering, hooks, Server Components,
forms, state management, and accessibility. Produces structured JSON results.

**Critical constraints**: Always use `screen` queries over container queries. Prefer
`userEvent` over `fireEvent`. Never test implementation details — test behavior.

---

## STEP 1: Detect Test Framework and React Version

Identify the project's testing stack before writing any tests.

1. Check `package.json` for dependencies:
   ```
   Glob: **/package.json
   ```
2. Look for these key signals:

   | Dependency | Indicates |
   |---|---|
   | `@testing-library/react` | React Testing Library (RTL) |
   | `jest` | Jest test runner |
   | `vitest` | Vitest test runner |
   | `@testing-library/user-event` | userEvent available |
   | `react` >= 18 | Concurrent features, `createRoot` |
   | `next` >= 13.4 | App Router / RSC support |
   | `@testing-library/jest-dom` | Extended DOM matchers |

3. Check for config files:
   ```
   Glob: **/jest.config.{js,ts,cjs,mjs}
   Glob: **/vitest.config.{js,ts,cjs,mjs}
   Glob: **/setupTests.{js,ts}
   ```

4. Record findings for use in subsequent steps. If RTL is not installed, warn and
   recommend adding `@testing-library/react` and `@testing-library/user-event`.

---

## STEP 2: React Testing Library Advanced Patterns

Build reusable test utilities before writing individual tests.

### Custom Render with Providers

Create a test utility that wraps components in all necessary providers:

```tsx
// test-utils/render.tsx
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "<your-theme-provider>";

interface ExtendedRenderOptions extends Omit<RenderOptions, "wrapper"> {
  queryClient?: QueryClient;
  theme?: "light" | "dark";
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: React.ReactElement,
  options: ExtendedRenderOptions = {}
) {
  const { queryClient = createTestQueryClient(), theme = "light", ...renderOptions } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>{children}</ThemeProvider>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

export * from "@testing-library/react";
export { renderWithProviders as render };
```

### Suspense Boundary Testing

Test components that suspend during data fetching:

```tsx
import { render, screen } from "<your-test-utils>";
import { Suspense } from "react";

test("shows fallback while loading, then content", async () => {
  render(
    <Suspense fallback={<div>Loading...</div>}>
      <YourAsyncComponent />
    </Suspense>
  );

  expect(screen.getByText("Loading...")).toBeInTheDocument();
  expect(await screen.findByText(/expected content/i)).toBeInTheDocument();
});
```

### Async Query Testing

For React Query dependent components, pre-populate or await query results:

```tsx
test("renders data from query", async () => {
  // MSW or manual mock provides the response
  const { queryClient } = renderWithProviders(<YourDataComponent />);

  expect(await screen.findByRole("heading", { name: /title/i })).toBeInTheDocument();

  // Verify cache state if needed
  const data = queryClient.getQueryData(["your-query-key"]);
  expect(data).toBeDefined();
});
```

---

## STEP 3: Server Component Testing (Next.js RSC)

Test async Server Components by treating them as async functions.

### Async Component Test

```tsx
import { render, screen } from "@testing-library/react";

// Mock server-only modules
vi.mock("server-only", () => ({}));

// Mock data-fetching functions
vi.mock("<your-data-module>", () => ({
  fetchItems: vi.fn().mockResolvedValue([
    { id: "1", title: "Item One" },
    { id: "2", title: "Item Two" },
  ]),
}));

test("server component renders with fetched data", async () => {
  // RSCs are async functions — await them to get JSX
  const Component = await YourServerComponent({ params: { id: "1" } });
  render(Component);

  expect(screen.getByText("Item One")).toBeInTheDocument();
});
```

### Server-Only Module Boundary

When a component imports from `server-only`, mock the module to prevent errors
in the test environment:

```tsx
// At the top of the test file or in a setup file
vi.mock("server-only", () => ({}));
vi.mock("next/headers", () => ({
  cookies: vi.fn(() => ({ get: vi.fn(), set: vi.fn() })),
  headers: vi.fn(() => new Map()),
}));
```

---

## STEP 4: Hook Testing with renderHook

Test custom hooks in isolation using `renderHook`.

### Basic Hook Test

```tsx
import { renderHook, act } from "@testing-library/react";

test("useCounter increments and decrements", () => {
  const { result } = renderHook(() => useCounter({ initial: 5 }));

  expect(result.current.count).toBe(5);

  act(() => result.current.increment());
  expect(result.current.count).toBe(6);

  act(() => result.current.decrement());
  expect(result.current.count).toBe(5);
});
```

### Hook with Context Dependencies

Wrap hooks that consume context in their provider:

```tsx
test("useAuth returns current user from context", () => {
  const mockUser = { id: "1", name: "Test User" };

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider value={{ user: mockUser }}>{children}</AuthProvider>
  );

  const { result } = renderHook(() => useAuth(), { wrapper });
  expect(result.current.user).toEqual(mockUser);
});
```

### Async Hook Test

```tsx
test("useFetch resolves data", async () => {
  const { result } = renderHook(() => useFetch("/api/items"), {
    wrapper: createTestProviders(),
  });

  expect(result.current.isLoading).toBe(true);

  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });

  expect(result.current.data).toHaveLength(3);
});
```

---

## STEP 5: Form Testing Patterns

Simulate real user interactions with forms.

### React Hook Form

```tsx
import userEvent from "@testing-library/user-event";

test("submits form with validated data", async () => {
  const onSubmit = vi.fn();
  const user = userEvent.setup();

  render(<YourForm onSubmit={onSubmit} />);

  await user.type(screen.getByLabelText(/email/i), "test@example.com");
  await user.type(screen.getByLabelText(/password/i), "SecurePass123!");
  await user.click(screen.getByRole("button", { name: /submit/i }));

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ email: "test@example.com" }),
      expect.anything()
    );
  });
});

test("displays validation errors for invalid input", async () => {
  const user = userEvent.setup();

  render(<YourForm onSubmit={vi.fn()} />);

  await user.click(screen.getByRole("button", { name: /submit/i }));

  expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
});
```

### Formik Form

```tsx
test("Formik form handles submission and validation", async () => {
  const user = userEvent.setup();
  const handleSubmit = vi.fn();

  render(<YourFormikForm onSubmit={handleSubmit} />);

  // Leave required field empty and submit
  await user.click(screen.getByRole("button", { name: /save/i }));
  expect(await screen.findByText(/required/i)).toBeInTheDocument();

  // Fill in the field and resubmit
  await user.type(screen.getByLabelText(/name/i), "Jane Doe");
  await user.click(screen.getByRole("button", { name: /save/i }));

  await waitFor(() => expect(handleSubmit).toHaveBeenCalledTimes(1));
});
```

---

## STEP 6: State Management Testing

### Zustand Store Testing

Test Zustand stores in isolation without React components:

```tsx
import { createStore } from "zustand";

// Re-create the store for each test to avoid shared state
function createTestStore(initialState = {}) {
  return createStore((set) => ({
    items: [],
    addItem: (item) => set((s) => ({ items: [...s.items, item] })),
    clearItems: () => set({ items: [] }),
    ...initialState,
  }));
}

test("addItem appends to items list", () => {
  const store = createTestStore();
  store.getState().addItem({ id: "1", name: "Test" });

  expect(store.getState().items).toHaveLength(1);
  expect(store.getState().items[0].name).toBe("Test");
});
```

### Redux Toolkit Slice Testing

```tsx
import { configureStore } from "@reduxjs/toolkit";
import yourReducer, { actionOne, actionTwo } from "<your-slice>";

function createTestStore(preloadedState = {}) {
  return configureStore({
    reducer: { yourFeature: yourReducer },
    preloadedState,
  });
}

test("dispatching actionOne updates state correctly", () => {
  const store = createTestStore();
  store.dispatch(actionOne({ value: 42 }));

  expect(store.getState().yourFeature.value).toBe(42);
});

test("async thunk populates data on success", async () => {
  const store = createTestStore();
  await store.dispatch(fetchYourData("param"));

  expect(store.getState().yourFeature.data).toBeDefined();
  expect(store.getState().yourFeature.status).toBe("succeeded");
});
```

---

## STEP 7: Accessibility Testing Integration

Run automated a11y checks alongside component tests using axe-core.

### Setup

Ensure `jest-axe` or `vitest-axe` is available:

```tsx
import { axe, toHaveNoViolations } from "jest-axe";
expect.extend(toHaveNoViolations);
```

### Component Accessibility Test

```tsx
test("<YourComponent> has no accessibility violations", async () => {
  const { container } = render(<YourComponent />);
  const results = await axe(container);

  expect(results).toHaveNoViolations();
});
```

### Focused Rule Testing

Narrow axe checks to specific rules when you want targeted assertions:

```tsx
test("form labels are correctly associated", async () => {
  const { container } = render(<YourForm />);
  const results = await axe(container, {
    runOnly: { type: "rule", values: ["label", "label-title-only"] },
  });

  expect(results).toHaveNoViolations();
});
```

---

## STEP 8: Run Tests and Collect Results

Execute the test suite for the specified scope.

1. Determine the test runner from Step 1.
2. Run tests with JSON reporter enabled:

   **Jest:**
   ```bash
   npx jest --testPathPattern="<test-scope>" --json --outputFile=test-results/react-test-patterns.json
   ```

   **Vitest:**
   ```bash
   npx vitest run --reporter=json --outputFile=test-results/react-test-patterns.json "<test-scope>"
   ```

3. If tests fail, read the failure output and identify:
   - Missing providers (wrap in the custom render from Step 2)
   - Async state not awaited (add `findBy` or `waitFor`)
   - Act warnings (wrap state updates in `act()`)

---

## STEP 9: Write Structured JSON Output

Produce a summary at `test-results/react-test-patterns.json` with this schema:

```json
{
  "timestamp": "<ISO 8601>",
  "testScope": "<test-scope argument>",
  "framework": "jest | vitest",
  "reactVersion": "<detected version>",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  },
  "categories": {
    "component": { "total": 0, "passed": 0 },
    "hook": { "total": 0, "passed": 0 },
    "rsc": { "total": 0, "passed": 0 },
    "form": { "total": 0, "passed": 0 },
    "state": { "total": 0, "passed": 0 },
    "a11y": { "total": 0, "passed": 0 }
  },
  "failures": [
    {
      "test": "<test name>",
      "category": "<category>",
      "error": "<shortened error message>",
      "suggestion": "<fix recommendation>"
    }
  ]
}
```

If the runner already produced a JSON file in Step 8, merge the raw output into
this schema rather than overwriting.

---

## CRITICAL RULES

### MUST DO

- Always use `userEvent.setup()` over `fireEvent` — it simulates real browser behavior
- Always query by accessible role, label, or text — use `screen.getByRole`, `screen.getByLabelText`, `screen.getByText`
- Always wrap state-updating calls in `act()` or use `findBy` / `waitFor` queries
- Always create a fresh store instance per test for state management tests
- Always mock `server-only` and `next/headers` when testing Server Components
- Always run `axe()` on the rendered container, not on a partial DOM fragment
- Always use the custom `renderWithProviders` when components need context

### MUST NOT DO

- MUST NOT test implementation details (internal state, private methods, component internals)
- MUST NOT use `container.querySelector` — use RTL queries instead
- MUST NOT use `getBy` for elements that appear asynchronously — use `findBy` or `waitFor`
- MUST NOT share store instances across tests — creates hidden coupling
- MUST NOT snapshot-test entire component trees — snapshots are brittle and low-signal
- MUST NOT hardcode file paths — use the `<test-scope>` argument and relative patterns
- MUST NOT skip accessibility tests — they catch real user-facing bugs
