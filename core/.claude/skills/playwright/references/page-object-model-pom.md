# STEP 4: Page Object Model (POM)

### 4.1 POM Structure

```
e2e/
  pages/
    login.page.ts
    dashboard.page.ts
    settings.page.ts
    components/
      navbar.component.ts
      modal.component.ts
  fixtures/
    test-fixtures.ts
  specs/
    auth.spec.ts
    dashboard.spec.ts
```

### 4.2 Page Object Implementation

```typescript
// e2e/pages/login.page.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly rememberMeCheckbox: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
    this.rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async loginAndExpectDashboard(email: string, password: string) {
    await this.login(email, password);
    await expect(this.page).toHaveURL('/dashboard');
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectFieldError(field: 'email' | 'password', message: string) {
    const input = field === 'email' ? this.emailInput : this.passwordInput;
    await expect(input).toHaveAttribute('aria-invalid', 'true');
    await expect(this.page.getByText(message)).toBeVisible();
  }
}

// e2e/pages/dashboard.page.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly statsCards: Locator;
  readonly recentActivity: Locator;
  readonly userMenu: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Dashboard', level: 1 });
    this.statsCards = page.getByTestId('stats-card');
    this.recentActivity = page.getByRole('list', { name: 'Recent activity' });
    this.userMenu = page.getByRole('button', { name: /user menu/i });
  }

  async expectLoaded() {
    await expect(this.heading).toBeVisible();
    await expect(this.statsCards.first()).toBeVisible();
  }

  async getStatValue(statName: string): Promise<string> {
    const card = this.statsCards.filter({ hasText: statName });
    const value = card.locator('.stat-value');
    return (await value.textContent()) ?? '';
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    await this.openUserMenu();
    await this.page.getByRole('menuitem', { name: 'Logout' }).click();
    await expect(this.page).toHaveURL('/login');
  }

  async expectActivityCount(count: number) {
    await expect(this.recentActivity.getByRole('listitem')).toHaveCount(count);
  }
}
```

### 4.3 Using Page Objects with Custom Fixtures

```typescript
// e2e/fixtures/test-fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

type TestFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<TestFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
});

export { expect } from '@playwright/test';

// e2e/specs/auth.spec.ts
import { test, expect } from '../fixtures/test-fixtures';

test.describe('Authentication', () => {
  test('successful login redirects to dashboard', async ({ loginPage, dashboardPage }) => {
    await loginPage.goto();
    await loginPage.loginAndExpectDashboard('user@example.com', 'password123');
    await dashboardPage.expectLoaded();
  });

  test('invalid credentials show error', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('user@example.com', 'wrongpassword');
    await loginPage.expectError('Invalid email or password');
  });

  test('empty form shows validation errors', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.submitButton.click();
    await loginPage.expectFieldError('email', 'Email is required');
  });
});
```

---

