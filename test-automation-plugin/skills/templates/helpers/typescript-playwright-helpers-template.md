# TypeScript Playwright E2E Helper Template

This template provides reusable test helper utilities for TypeScript Playwright E2E projects, including page objects, custom fixtures, network mock helpers, and common assertion helpers.

## Page Object Patterns

Page objects encapsulate page-specific selectors and actions, keeping test files focused on user flow logic rather than DOM details. Selectors within page objects follow the same priority: `getByTestId` > `getByRole` > `getByLabel` > `getByText` > `locator`.

### Base Page Object

```typescript
import type { Page, Locator } from '@playwright/test';

/**
 * Base page object with shared navigation and assertion helpers.
 * All page objects should extend this class.
 */
export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path);
  }

  async getTitle(): Promise<string> {
    return this.page.title();
  }
}
```

### Login Page Object

```typescript
import { expect, type Page, type Locator } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Page object for the login page.
 * Encapsulates login form selectors and authentication actions.
 */
export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly signInButton: Locator;
  readonly errorAlert: Locator;
  readonly forgotPasswordLink: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.signInButton = page.getByRole('button', { name: 'Sign In' });
    this.errorAlert = page.getByRole('alert');
    this.forgotPasswordLink = page.getByRole('link', { name: 'Forgot password?' });
  }

  async goto(): Promise<void> {
    await this.navigateTo('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.signInButton.click();
  }

  async expectError(message: string): Promise<void> {
    await expect(this.errorAlert).toBeVisible();
    await expect(this.errorAlert).toContainText(message);
  }

  async expectRedirectToDashboard(): Promise<void> {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }
}
```

### Dashboard Page Object

```typescript
import { expect, type Page, type Locator } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Page object for the dashboard page.
 * Encapsulates dashboard widgets and data interactions.
 */
export class DashboardPage extends BasePage {
  readonly heading: Locator;
  readonly statsWidget: Locator;
  readonly activityFeed: Locator;
  readonly refreshButton: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = page.getByRole('heading', { name: 'Dashboard' });
    this.statsWidget = page.getByTestId('stats-widget');
    this.activityFeed = page.getByTestId('activity-feed');
    this.refreshButton = page.getByRole('button', { name: 'Refresh' });
    this.loadingSpinner = page.getByTestId('loading-spinner');
  }

  async goto(): Promise<void> {
    await this.navigateTo('/dashboard');
    await expect(this.heading).toBeVisible();
  }

  async refresh(): Promise<void> {
    const responsePromise = this.page.waitForResponse('**/api/dashboard');
    await this.refreshButton.click();
    await responsePromise;
  }

  async expectLoaded(): Promise<void> {
    await expect(this.statsWidget).toBeVisible();
    await expect(this.activityFeed).toBeVisible();
  }

  async waitForDataLoad(): Promise<void> {
    await expect(this.loadingSpinner).toBeHidden();
  }
}
```

### Page Object Usage in Tests

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login-page';
import { DashboardPage } from './pages/dashboard-page';

test.describe('Login to Dashboard Flow', () => {
  test('user logs in and sees dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    // Navigate
    await loginPage.goto();

    // Interact
    await loginPage.login('testuser@example.com', 'password123');

    // Assert
    await loginPage.expectRedirectToDashboard();
    await dashboardPage.expectLoaded();
  });

  test('invalid login shows error', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login('wrong@example.com', 'wrongpassword');
    await loginPage.expectError('Invalid email or password');
  });
});
```

## Custom Fixture Patterns

### Authentication Setup Fixture

```typescript
import { test as base, expect, type Page, type BrowserContext } from '@playwright/test';

/**
 * Custom fixtures that extend Playwright's built-in fixtures.
 * Provides pre-authenticated page contexts and test data seeding.
 */

type CustomFixtures = {
  authenticatedPage: Page;
  adminPage: Page;
};

export const test = base.extend<CustomFixtures>({
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/admin.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect };
```

### Data Seeding Fixture

```typescript
import { test as base, type Page } from '@playwright/test';

interface TestData {
  userId: number;
  projectId: number;
}

type DataFixtures = {
  seededData: TestData;
  seededPage: Page;
};

export const test = base.extend<DataFixtures>({
  seededData: async ({ request }, use) => {
    // Seed test data via API before test
    const userResponse = await request.post('/api/test/seed-user', {
      data: { name: 'Test User', email: 'test@example.com' },
    });
    const user = await userResponse.json();

    const projectResponse = await request.post('/api/test/seed-project', {
      data: { name: 'Test Project', ownerId: user.id },
    });
    const project = await projectResponse.json();

    await use({ userId: user.id, projectId: project.id });

    // Cleanup after test
    await request.delete(`/api/test/cleanup-user/${user.id}`);
  },

  seededPage: async ({ page, seededData }, use) => {
    // Page is available with seeded data context
    await use(page);
  },
});
```

### Auth Setup File (Global Setup Pattern)

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const AUTH_FILE = 'playwright/.auth/user.json';
const ADMIN_AUTH_FILE = 'playwright/.auth/admin.json';

setup('authenticate as regular user', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('testuser@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: AUTH_FILE });
});

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('adminpass123');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/admin');
  await page.context().storageState({ path: ADMIN_AUTH_FILE });
});
```

## Network Mock Helpers

### API Mock Builder

```typescript
import type { Page, Route } from '@playwright/test';

/**
 * Helper for setting up API mocks with consistent patterns.
 * Wraps page.route() with a fluent builder interface.
 */
export class ApiMockBuilder {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Mock a GET endpoint with a JSON response.
   */
  async mockGet(urlPattern: string, data: unknown, status: number = 200): Promise<void> {
    await this.page.route(`**${urlPattern}`, async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status,
          contentType: 'application/json',
          body: JSON.stringify(data),
        });
      } else {
        await route.continue();
      }
    });
  }

  /**
   * Mock a POST endpoint with a JSON response.
   */
  async mockPost(urlPattern: string, responseData: unknown, status: number = 201): Promise<void> {
    await this.page.route(`**${urlPattern}`, async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status,
          contentType: 'application/json',
          body: JSON.stringify(responseData),
        });
      } else {
        await route.continue();
      }
    });
  }

  /**
   * Mock an endpoint to return an error.
   */
  async mockError(urlPattern: string, status: number = 500, message: string = 'Internal Server Error'): Promise<void> {
    await this.page.route(`**${urlPattern}`, async route => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ error: message }),
      });
    });
  }

  /**
   * Mock an endpoint to simulate a network failure.
   */
  async mockNetworkFailure(urlPattern: string): Promise<void> {
    await this.page.route(`**${urlPattern}`, route => route.abort('failed'));
  }

  /**
   * Mock an endpoint with a delayed response (using route.fulfill, NOT fixed delays).
   * The delay is handled server-side via route interception, not via waitForTimeout.
   */
  async mockDelayedResponse(urlPattern: string, data: unknown, delayMs: number): Promise<void> {
    await this.page.route(`**${urlPattern}`, async route => {
      await new Promise(resolve => setTimeout(resolve, delayMs));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data),
      });
    });
  }

  /**
   * Remove all mocks (restore real network behavior).
   */
  async clearAll(): Promise<void> {
    await this.page.unrouteAll({ behavior: 'wait' });
  }
}
```

### Response Interceptor Helper

```typescript
import type { Page, Response } from '@playwright/test';

/**
 * Helper for capturing and inspecting network responses during tests.
 */
export class ResponseInterceptor {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Wait for a specific API response and return its JSON body.
   */
  async captureResponse<T>(urlPattern: string, triggerAction: () => Promise<void>): Promise<T> {
    const responsePromise = this.page.waitForResponse(
      resp => resp.url().includes(urlPattern) && resp.status() === 200
    );
    await triggerAction();
    const response = await responsePromise;
    return response.json() as Promise<T>;
  }

  /**
   * Wait for a specific API request and return its POST body.
   */
  async captureRequest<T>(urlPattern: string, triggerAction: () => Promise<void>): Promise<T> {
    const requestPromise = this.page.waitForRequest(
      req => req.url().includes(urlPattern)
    );
    await triggerAction();
    const request = await requestPromise;
    return request.postDataJSON() as T;
  }
}
```

### Network Mock Usage in Tests

```typescript
import { test, expect } from '@playwright/test';
import { ApiMockBuilder } from './helpers/api-mock-builder';
import { ResponseInterceptor } from './helpers/response-interceptor';

test.describe('User List', () => {
  test('displays users from API', async ({ page }) => {
    const api = new ApiMockBuilder(page);
    await api.mockGet('/api/users', {
      users: [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
      ],
    });

    await page.goto('/users');
    await expect(page.getByRole('listitem')).toHaveCount(2);
  });

  test('shows error state on API failure', async ({ page }) => {
    const api = new ApiMockBuilder(page);
    await api.mockError('/api/users', 500, 'Service unavailable');

    await page.goto('/users');
    await expect(page.getByRole('alert')).toContainText('Failed to load');
  });

  test('sends correct data on form submit', async ({ page }) => {
    const interceptor = new ResponseInterceptor(page);

    await page.goto('/users/new');
    await page.getByLabel('Name').fill('New User');
    await page.getByLabel('Email').fill('new@example.com');

    const requestBody = await interceptor.captureRequest<{ name: string; email: string }>(
      '/api/users',
      () => page.getByRole('button', { name: 'Create' }).click(),
    );

    expect(requestBody.name).toBe('New User');
    expect(requestBody.email).toBe('new@example.com');
  });
});
```

## Common Assertion Helpers

### Page Assertion Helpers

```typescript
import { expect, type Page, type Locator } from '@playwright/test';

/**
 * Reusable assertion helpers for common E2E verification patterns.
 */

/**
 * Assert that a toast/notification message appears with expected text.
 */
export async function expectToast(page: Page, message: string): Promise<void> {
  const toast = page.getByRole('alert');
  await expect(toast).toBeVisible();
  await expect(toast).toContainText(message);
}

/**
 * Assert that the page navigated to the expected URL pattern.
 */
export async function expectNavigatedTo(page: Page, urlPattern: RegExp): Promise<void> {
  await expect(page).toHaveURL(urlPattern);
}

/**
 * Assert that a form field displays a validation error.
 */
export async function expectFieldError(page: Page, fieldLabel: string, errorMessage: string): Promise<void> {
  const field = page.getByLabel(fieldLabel);
  await expect(field).toBeVisible();
  // Look for error message near the field
  const fieldGroup = field.locator('..');
  await expect(fieldGroup.getByText(errorMessage)).toBeVisible();
}

/**
 * Assert a table has the expected number of data rows (excluding header).
 */
export async function expectTableRowCount(page: Page, tableTestId: string, expectedCount: number): Promise<void> {
  const table = page.getByTestId(tableTestId);
  await expect(table).toBeVisible();
  // Count rows in tbody (data rows, not header)
  await expect(table.locator('tbody tr')).toHaveCount(expectedCount);
}

/**
 * Assert that a loading indicator appears and then disappears.
 */
export async function expectLoadingComplete(page: Page, loadingTestId: string = 'loading-spinner'): Promise<void> {
  const spinner = page.getByTestId(loadingTestId);
  await expect(spinner).toBeHidden();
}

/**
 * Assert that a modal dialog is visible with the expected title.
 */
export async function expectModal(page: Page, title: string): Promise<void> {
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('heading')).toContainText(title);
}

/**
 * Assert that a modal dialog is closed.
 */
export async function expectModalClosed(page: Page): Promise<void> {
  await expect(page.getByRole('dialog')).toBeHidden();
}
```

### Assertion Helper Usage in Tests

```typescript
import { test } from '@playwright/test';
import {
  expectToast,
  expectNavigatedTo,
  expectFieldError,
  expectTableRowCount,
  expectLoadingComplete,
  expectModal,
  expectModalClosed,
} from './helpers/assertion-helpers';

test.describe('Settings Page', () => {
  test('user saves settings and sees confirmation', async ({ page }) => {
    await page.goto('/settings');
    await page.getByLabel('Notifications').check();
    await page.getByRole('button', { name: 'Save' }).click();

    await expectToast(page, 'Settings saved');
  });

  test('form shows validation errors', async ({ page }) => {
    await page.goto('/settings/profile');
    await page.getByLabel('Email').clear();
    await page.getByRole('button', { name: 'Save' }).click();

    await expectFieldError(page, 'Email', 'Email is required');
  });

  test('confirmation modal opens and closes', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Delete Account' }).click();

    await expectModal(page, 'Confirm Deletion');

    await page.getByRole('button', { name: 'Cancel' }).click();
    await expectModalClosed(page);
  });
});
```

## Test Data Builders

```typescript
/**
 * Build test data objects with sensible defaults and optional overrides.
 */

interface TestUser {
  id: number;
  name: string;
  email: string;
  role: string;
}

export function buildTestUser(overrides: Partial<TestUser> = {}): TestUser {
  return {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    ...overrides,
  };
}

interface TestProduct {
  id: number;
  name: string;
  price: number;
  category: string;
  inStock: boolean;
}

export function buildTestProduct(overrides: Partial<TestProduct> = {}): TestProduct {
  return {
    id: 1,
    name: 'Test Product',
    price: 29.99,
    category: 'electronics',
    inStock: true,
    ...overrides,
  };
}

/**
 * Build a list of test items with sequential IDs.
 */
export function buildTestList<T extends { id: number }>(
  builder: (overrides?: Partial<T>) => T,
  count: number = 3,
  overridesFn?: (index: number) => Partial<T>,
): T[] {
  return Array.from({ length: count }, (_, i) =>
    builder({ id: i + 1, ...(overridesFn?.(i) || {}) } as Partial<T>),
  );
}
```

## File Organization

```
tests/
  e2e/
    pages/                           # Page objects
      base-page.ts
      login-page.ts
      dashboard-page.ts
    fixtures/                        # Custom fixtures and test data
      auth-fixtures.ts
      data-fixtures.ts
      test-data.ts
    helpers/                         # Reusable helper utilities
      api-mock-builder.ts
      response-interceptor.ts
      assertion-helpers.ts
    auth/                            # Auth flow tests
      login.spec.ts
      registration.spec.ts
    dashboard/                       # Dashboard flow tests
      overview.spec.ts
      filters.spec.ts
    auth.setup.ts                    # Global auth setup
```
