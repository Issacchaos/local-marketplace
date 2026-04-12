# TypeScript Playwright E2E Test Template

**Purpose**: Template for generating Playwright end-to-end test files with TypeScript
**Target Language**: TypeScript
**Test Framework**: @playwright/test
**Test Type**: E2E (End-to-End)
**Version Support**: Playwright 1.50+, TypeScript 4.0+

## E2E Test Pattern: Navigate -> Interact -> Assert

E2E tests follow a distinct pattern from unit tests. Unit tests use Arrange-Act-Assert for isolated function behavior. E2E tests simulate real user journeys through the application: navigating to a page, interacting with elements as a user would, then asserting on the resulting UI state.

```
Navigate:  Go to the page under test (page.goto, link clicks, form submissions)
Interact:  Perform user actions (click, fill, select, check, keyboard input)
Assert:    Verify the resulting UI state (visibility, text, URL, element count)
```

This distinction matters because E2E tests target **user flows**, not functions or modules. A single E2E test may span multiple pages, trigger API calls, and wait for asynchronous UI updates.

## Template Structure

### Basic E2E Test File Template

```typescript
/**
 * E2E tests for {FLOW_NAME}.
 *
 * User flows covered:
 * - {USER_FLOW_1}
 * - {USER_FLOW_2}
 * - {USER_FLOW_3}
 */

import { test, expect } from '@playwright/test';
{ADDITIONAL_IMPORTS}

// ============================================================================
// Test Suite: {SUITE_NAME}
// ============================================================================

test.describe('{SUITE_NAME}', () => {
  {SETUP_CODE}

  {TEST_CASES}
});
```

## Template Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{FLOW_NAME}` | User flow or feature being tested | `Login`, `Checkout`, `Dashboard Navigation` |
| `{USER_FLOW_N}` | Specific user flow scenarios | `User logs in with valid credentials` |
| `{ADDITIONAL_IMPORTS}` | Extra imports (fixtures, helpers) | `import { AuthPage } from './pages/auth-page';` |
| `{SUITE_NAME}` | Test suite name (by flow, not file) | `Login Flow`, `Shopping Cart` |
| `{SETUP_CODE}` | Shared setup (route mocks, hooks) | `test.beforeEach(async ({ page }) => { ... });` |
| `{TEST_CASES}` | Individual E2E test cases | Generated test methods |

## File Naming and Location

### File Naming
- Pattern: `*.spec.ts`
- Name by user flow or feature: `login.spec.ts`, `checkout.spec.ts`, `dashboard-navigation.spec.ts`
- NOT by source file: avoid `loginForm.spec.ts` or `authService.spec.ts`

### File Location
- Primary: Use `testDir` from `playwright.config.ts` (e.g., `./tests/e2e/`, `./e2e/`)
- Fallback: `tests/e2e/` if no config found

### Test Organization

Organize by user flow and feature area, NOT by source file:

```
{testDir}/
  auth/
    login.spec.ts              # Login flow: valid, invalid, forgot password
    registration.spec.ts       # Registration flow: new user signup
  dashboard/
    overview.spec.ts           # Dashboard overview: widgets, data loading
    filters.spec.ts            # Dashboard filtering: date range, category
  checkout/
    cart.spec.ts               # Shopping cart: add, remove, update quantity
    payment.spec.ts            # Payment flow: card entry, validation, success
  navigation/
    main-nav.spec.ts           # Primary navigation: menu links, active state
    breadcrumbs.spec.ts        # Breadcrumb navigation
```

## Import Structure

```typescript
// Test framework imports
import { test, expect } from '@playwright/test';

// Type imports (for custom fixtures, page objects)
import type { Page, BrowserContext } from '@playwright/test';

// Page object imports
import { LoginPage } from './pages/login-page';

// Test data imports
import { testUsers } from './fixtures/test-data';
```

## Test Method Template (Navigate -> Interact -> Assert)

```typescript
test('{USER_VISIBLE_BEHAVIOR}', async ({ page }) => {
  // Navigate
  {NAVIGATE_CODE}

  // Interact
  {INTERACT_CODE}

  // Assert
  {ASSERT_CODE}
});
```

## Selector Priority

Selectors MUST follow this priority order. Use the highest-priority selector available for each element:

| Priority | Strategy | API | When to Use |
|----------|----------|-----|-------------|
| 1 (highest) | Test ID | `page.getByTestId('submit-btn')` | Element has `data-testid` attribute |
| 2 | Role + Name | `page.getByRole('button', { name: 'Submit' })` | Semantic ARIA role with accessible name |
| 3 | Label | `page.getByLabel('Email address')` | Form inputs with `<label>` |
| 4 | Text | `page.getByText('Welcome back')` | Unique visible text |
| 5 | Placeholder | `page.getByPlaceholder('Search...')` | Input placeholder (less stable than label) |
| 6 (lowest) | CSS/XPath | `page.locator('.card >> nth=0')` | Last resort only |

### Selector Composition

```typescript
// Narrow scope, then find within it
const card = page.getByTestId('user-card');
await card.getByRole('button', { name: 'Edit' }).click();

// Filter by text content
await page.getByRole('listitem').filter({ hasText: 'Product A' }).click();

// Disambiguate strict mode violations
await page.getByRole('button', { name: 'Submit' }).first().click();
```

## Fixture Patterns

### Built-in Fixtures

```typescript
// page: Isolated page instance per test (most common)
test('basic test', async ({ page }) => {
  await page.goto('/');
});

// context: Browser context (cookies, localStorage)
test('context test', async ({ context }) => {
  const page = await context.newPage();
  await page.goto('/');
});

// browser: Full browser instance (multi-context scenarios)
test('multi-user test', async ({ browser }) => {
  const userOne = await browser.newContext({ storageState: 'auth/user1.json' });
  const userTwo = await browser.newContext({ storageState: 'auth/user2.json' });
  const pageOne = await userOne.newPage();
  const pageTwo = await userTwo.newPage();
});
```

### Custom Auth Fixture

```typescript
// tests/fixtures.ts
import { test as base, expect } from '@playwright/test';

export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect };
```

```typescript
// tests/e2e/dashboard/overview.spec.ts
import { test, expect } from '../fixtures';

test('dashboard shows user data', async ({ authenticatedPage: page }) => {
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Assertion Patterns

### Element State Assertions

```typescript
await expect(page.getByTestId('status')).toBeVisible();
await expect(page.getByTestId('status')).toBeHidden();
await expect(page.getByTestId('submit')).toBeEnabled();
await expect(page.getByTestId('submit')).toBeDisabled();
await expect(page.getByLabel('I agree')).toBeChecked();
```

### Text Assertions

```typescript
await expect(page.getByTestId('heading')).toHaveText('Dashboard');
await expect(page.getByTestId('heading')).toContainText('Dash');
```

### Page-Level Assertions

```typescript
await expect(page).toHaveURL(/\/dashboard/);
await expect(page).toHaveTitle('My App - Dashboard');
```

### Count and Attribute Assertions

```typescript
await expect(page.getByRole('listitem')).toHaveCount(5);
await expect(page.getByTestId('link')).toHaveAttribute('href', '/dashboard');
await expect(page.getByLabel('Email')).toHaveValue('user@example.com');
```

## Mocking Patterns: page.route()

### Basic API Mock

```typescript
await page.route('**/api/users', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Test User' }]),
  });
});
```

### Error Response Mock

```typescript
await page.route('**/api/save', async route => {
  await route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ error: 'Internal Server Error' }),
  });
});
```

### Abort Requests (test error handling)

```typescript
await page.route('**/api/data', route => route.abort('failed'));
```

### Wait for Network Response

```typescript
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load Users' }).click();
await responsePromise;
await expect(page.getByTestId('user-list')).toBeVisible();
```

## Complete Examples

### Example 1: Unauthenticated Flow (Login)

```typescript
/**
 * E2E tests for the login flow.
 *
 * User flows covered:
 * - User logs in with valid credentials
 * - User sees error for invalid credentials
 * - User navigates to forgot password
 */

import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
  });

  test('user can log in with valid credentials', async ({ page }) => {
    // Interact
    await page.getByLabel('Email').fill('testuser@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Assert
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('shows error message for invalid credentials', async ({ page }) => {
    // Interact
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Assert
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText('Invalid email or password');
    await expect(page).toHaveURL(/\/login/);
  });

  test('user can navigate to forgot password', async ({ page }) => {
    // Interact
    await page.getByRole('link', { name: 'Forgot password?' }).click();

    // Assert
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByRole('heading', { name: 'Reset Password' })).toBeVisible();
  });
});
```

### Example 2: Authenticated Flow (Dashboard)

```typescript
/**
 * E2E tests for the dashboard overview.
 *
 * User flows covered:
 * - Authenticated user sees dashboard widgets
 * - Dashboard loads data from API
 * - User can refresh dashboard data
 */

import { test, expect } from '@playwright/test';

// Use stored auth state to skip login
test.use({ storageState: 'playwright/.auth/user.json' });

test.describe('Dashboard Overview', () => {
  test('authenticated user sees dashboard widgets', async ({ page }) => {
    // Navigate
    await page.goto('/dashboard');

    // Assert
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByTestId('stats-widget')).toBeVisible();
    await expect(page.getByTestId('activity-feed')).toBeVisible();
    await expect(page.getByTestId('quick-actions')).toBeVisible();
  });

  test('dashboard loads data from API', async ({ page }) => {
    // Navigate (with API response wait)
    const responsePromise = page.waitForResponse('**/api/dashboard');
    await page.goto('/dashboard');
    await responsePromise;

    // Assert
    await expect(page.getByTestId('stats-widget')).toBeVisible();
    await expect(page.getByTestId('total-users')).not.toHaveText('--');
  });

  test('user can refresh dashboard data', async ({ page }) => {
    // Navigate
    await page.goto('/dashboard');
    await expect(page.getByTestId('stats-widget')).toBeVisible();

    // Interact
    const responsePromise = page.waitForResponse('**/api/dashboard');
    await page.getByRole('button', { name: 'Refresh' }).click();
    await responsePromise;

    // Assert
    await expect(page.getByTestId('stats-widget')).toBeVisible();
  });
});
```

### Example 3: Form Submission

```typescript
/**
 * E2E tests for the user profile form.
 *
 * User flows covered:
 * - User updates profile information
 * - Form validates required fields
 * - User sees success confirmation after save
 */

import { test, expect } from '@playwright/test';

test.use({ storageState: 'playwright/.auth/user.json' });

test.describe('Profile Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings/profile');
    await expect(page.getByRole('heading', { name: 'Profile' })).toBeVisible();
  });

  test('user can update profile information', async ({ page }) => {
    // Interact
    await page.getByLabel('Display Name').clear();
    await page.getByLabel('Display Name').fill('Updated Name');
    await page.getByLabel('Bio').fill('This is my updated bio.');
    await page.getByRole('combobox', { name: 'Timezone' }).selectOption('America/New_York');

    const responsePromise = page.waitForResponse('**/api/profile');
    await page.getByRole('button', { name: 'Save Changes' }).click();
    await responsePromise;

    // Assert
    await expect(page.getByText('Profile updated successfully')).toBeVisible();
    await expect(page.getByLabel('Display Name')).toHaveValue('Updated Name');
  });

  test('form validates required fields', async ({ page }) => {
    // Interact -- clear required field and submit
    await page.getByLabel('Display Name').clear();
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Assert
    await expect(page.getByText('Display name is required')).toBeVisible();
  });

  test('user sees success confirmation after save', async ({ page }) => {
    // Interact
    await page.getByLabel('Display Name').fill('New Name');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Assert
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText('successfully');
    // Confirmation disappears after display
    await expect(page.getByRole('alert')).toBeHidden();
  });
});
```

### Example 4: Navigation

```typescript
/**
 * E2E tests for primary navigation.
 *
 * User flows covered:
 * - User navigates between main sections
 * - Active nav item reflects current page
 * - Mobile menu opens and closes
 */

import { test, expect } from '@playwright/test';

test.use({ storageState: 'playwright/.auth/user.json' });

test.describe('Primary Navigation', () => {
  test('user can navigate between main sections', async ({ page }) => {
    // Navigate
    await page.goto('/');

    // Interact -- navigate to Dashboard
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Interact -- navigate to Settings
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    // Interact -- navigate back to Home
    await page.getByRole('link', { name: 'Home' }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('active nav item reflects current page', async ({ page }) => {
    // Navigate
    await page.goto('/dashboard');

    // Assert
    await expect(page.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByRole('link', { name: 'Settings' })).not.toHaveAttribute('aria-current', 'page');
  });

  test('mobile menu opens and closes', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Navigate
    await page.goto('/');

    // Assert -- menu starts closed
    await expect(page.getByRole('navigation', { name: 'Main' })).toBeHidden();

    // Interact -- open menu
    await page.getByRole('button', { name: 'Open menu' }).click();
    await expect(page.getByRole('navigation', { name: 'Main' })).toBeVisible();

    // Interact -- close menu
    await page.getByRole('button', { name: 'Close menu' }).click();
    await expect(page.getByRole('navigation', { name: 'Main' })).toBeHidden();
  });
});
```

### Example 5: API Mocking

```typescript
/**
 * E2E tests for the user list with mocked API.
 *
 * User flows covered:
 * - User sees list of users from API
 * - User sees empty state when no users
 * - User sees error state when API fails
 */

import { test, expect } from '@playwright/test';

test.use({ storageState: 'playwright/.auth/user.json' });

test.describe('User List with Mocked API', () => {
  test('user sees list of users from API', async ({ page }) => {
    // Setup mock
    await page.route('**/api/users', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          users: [
            { id: 1, name: 'Alice Johnson', role: 'Admin' },
            { id: 2, name: 'Bob Smith', role: 'User' },
            { id: 3, name: 'Carol Williams', role: 'User' },
          ],
          total: 3,
        }),
      });
    });

    // Navigate
    await page.goto('/admin/users');

    // Assert
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByRole('row')).toHaveCount(4); // header + 3 data rows
    await expect(page.getByRole('cell', { name: 'Alice Johnson' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Bob Smith' })).toBeVisible();
  });

  test('user sees empty state when no users', async ({ page }) => {
    // Setup mock -- empty list
    await page.route('**/api/users', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ users: [], total: 0 }),
      });
    });

    // Navigate
    await page.goto('/admin/users');

    // Assert
    await expect(page.getByText('No users found')).toBeVisible();
    await expect(page.getByRole('table')).toBeHidden();
  });

  test('user sees error state when API fails', async ({ page }) => {
    // Setup mock -- server error
    await page.route('**/api/users', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    // Navigate
    await page.goto('/admin/users');

    // Assert
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText('Failed to load users');
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
  });
});
```

## Wait Strategy

All tests MUST use proper wait strategies. Fixed delays are **prohibited**.

### Preferred Wait Approaches (in priority order)

| Priority | Strategy | API | When to Use |
|----------|----------|-----|-------------|
| 1 | Auto-wait (built-in) | All actions (`click`, `fill`, etc.) | Default -- Playwright waits for actionability |
| 2 | Assertion-based wait | `await expect(locator).toBeVisible()` | Wait for specific UI state |
| 3 | URL-based wait | `await expect(page).toHaveURL(url)` | Wait for navigation |
| 4 | Network-based wait | `await page.waitForResponse(url)` | Wait for API call to complete |
| 5 | Load state wait | `await page.waitForLoadState('networkidle')` | Sparingly -- unreliable with WebSockets |

### PROHIBITED: Fixed Delays

```typescript
// NEVER do this
await page.waitForTimeout(2000);
await new Promise(resolve => setTimeout(resolve, 1000));
```

### Correct Wait Patterns

```typescript
// Wait for element before interacting
await expect(page.getByTestId('result')).toBeVisible();
await page.getByTestId('result').click();

// Wait for navigation after click
await page.getByRole('link', { name: 'Dashboard' }).click();
await expect(page).toHaveURL(/\/dashboard/);

// Wait for API response before asserting UI
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load' }).click();
await responsePromise;
await expect(page.getByTestId('user-list')).toBeVisible();

// Wait for loading spinner to disappear
await expect(page.getByTestId('loading-spinner')).toBeHidden();
```

## Test Naming Convention

Test names describe user-visible behavior, not implementation:

```typescript
// GOOD: User-visible behavior
test('user can log in with valid credentials', async ({ page }) => { ... });
test('shows error message for invalid password', async ({ page }) => { ... });
test('shopping cart updates total when item quantity changes', async ({ page }) => { ... });

// BAD: Implementation details
test('LoginForm component handles submit', async ({ page }) => { ... });
test('API returns 401 for invalid token', async ({ page }) => { ... });
test('Redux store updates cart state', async ({ page }) => { ... });
```

## Authentication Patterns

### Storage State for Authenticated Tests

```typescript
// playwright.config.ts -- setup project
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
    },
  ],
});
```

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('testuser@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: 'playwright/.auth/user.json' });
});
```

### Unauthenticated Tests

```typescript
// Explicitly clear storage state for tests that need unauthenticated context
test.use({ storageState: { cookies: [], origins: [] } });

test('login page shows form', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Password')).toBeVisible();
});
```

## Configuration Notes

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
});
```

## Best Practices

1. **Selector Resilience**: Always prefer `getByTestId` > `getByRole` > `getByLabel` > `getByText` > `locator`
2. **No Fixed Delays**: Use assertion-based, URL-based, or network-based waits instead of `waitForTimeout`
3. **Test Isolation**: Each test gets its own `page` and `context` -- no shared state between tests
4. **Test by Flow**: Organize tests by user flow (login, checkout, navigation), not by source file
5. **Descriptive Names**: Test names describe user-visible behavior, not implementation details
6. **Auth Reuse**: Use `storageState` to skip login in authenticated tests
7. **Mock APIs Selectively**: Use `page.route()` for deterministic API responses; let unmatched requests pass through
8. **Assert After Wait**: Always ensure the expected state is reached via assertion before continuing to the next step

## References

- Playwright Documentation: https://playwright.dev/docs/api/class-page
- Playwright Test Documentation: https://playwright.dev/docs/writing-tests
- Playwright Assertions: https://playwright.dev/docs/test-assertions
- Playwright Fixtures: https://playwright.dev/docs/test-fixtures
- Playwright Framework Reference: `skills/e2e/frameworks/playwright.md`
- E2E Testing Skill: `skills/e2e/SKILL.md`
- Helpers Template: `skills/templates/helpers/typescript-playwright-helpers-template.md`

---

**Last Updated**: 2026-02-16
**Phase**: 3 - Implementation
**Status**: Complete
