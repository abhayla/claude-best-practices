# STEP 5: API + UI Combined Testing

### 5.1 API Setup with UI Verification

```typescript
import { test, expect } from '@playwright/test';

test('admin views user list after creating users via API', async ({ page, request }) => {
  // ARRANGE: Create test data via API (fast, reliable)
  const users = ['alice', 'bob', 'charlie'];
  for (const name of users) {
    await request.post('/api/users', {
      data: { name, email: `${name}@test.com`, role: 'member' },
    });
  }

  // ACT: Navigate to admin panel via UI
  await page.goto('/admin/users');

  // ASSERT: Verify UI reflects API-created data
  for (const name of users) {
    await expect(page.getByRole('cell', { name })).toBeVisible();
  }
  await expect(page.getByRole('row')).toHaveCount(users.length + 1); // +1 for header
});
```

### 5.2 Authenticated API Requests

```typescript
import { test, expect } from '@playwright/test';

// Share authentication between API and browser
test('authenticated API and UI combined', async ({ page, request }) => {
  // Login via API to get auth token
  const loginResponse = await request.post('/api/auth/login', {
    data: { email: 'admin@example.com', password: 'admin123' },
  });
  const { token } = await loginResponse.json();

  // Use token for API setup
  const createResponse = await request.post('/api/projects', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'Test Project', description: 'E2E test' },
  });
  const project = await createResponse.json();

  // Set auth in browser context
  await page.goto('/login');
  await page.evaluate((t) => localStorage.setItem('auth_token', t), token);

  // Verify via UI
  await page.goto(`/projects/${project.id}`);
  await expect(page.getByRole('heading', { name: 'Test Project' })).toBeVisible();
});
```

### 5.3 API Cleanup in Teardown

```typescript
test.describe('Order management', () => {
  let orderId: string;

  test.afterEach(async ({ request }) => {
    // Clean up test data via API
    if (orderId) {
      await request.delete(`/api/orders/${orderId}`);
    }
  });

  test('create order and verify in UI', async ({ page, request }) => {
    const response = await request.post('/api/orders', {
      data: { product: 'Widget', quantity: 3 },
    });
    const order = await response.json();
    orderId = order.id;

    await page.goto(`/orders/${orderId}`);
    await expect(page.getByText('Widget')).toBeVisible();
    await expect(page.getByText('Quantity: 3')).toBeVisible();
  });
});
```

---

