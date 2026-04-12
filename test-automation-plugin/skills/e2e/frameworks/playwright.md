# Playwright Framework Reference

**Version**: 1.0.0
**Parent Skill**: [E2E Testing Skill](../SKILL.md)
**Framework**: Playwright (`@playwright/test`)
**Language**: TypeScript / JavaScript
**Status**: Full implementation
**Purpose**: Complete framework-specific reference for Playwright E2E testing. Provides selector APIs, wait patterns, error regex patterns, fix strategies, CLI workflows, and config parsing. Agents load this file after the generic E2E skill when `framework=playwright`.

---

## API Mapping

### Selector Priority

Selectors are ranked from most resilient to least resilient. The write-agent and fix-agent MUST prefer higher-priority selectors and only fall to lower-priority options when higher options are unavailable.

| Priority | Strategy | Playwright API | When to Use |
|----------|----------|---------------|-------------|
| 1 (highest) | Test ID attribute | `page.getByTestId('submit-btn')` | Element has `data-testid` attribute. Most stable -- survives refactors, text changes, and restructuring. |
| 2 | Accessibility role | `page.getByRole('button', { name: 'Submit' })` | Element has a semantic ARIA role and accessible name. Robust against DOM restructuring while coupling to user-visible semantics. |
| 3 | Form label | `page.getByLabel('Email address')` | Form inputs associated with `<label>` elements. Ties selector to the label text users see. |
| 4 | Visible text | `page.getByText('Welcome back')` | Unique visible text content on the page. Acceptable for headings, paragraphs, and static content. Fragile if text is dynamic or duplicated. |
| 5 | Placeholder text | `page.getByPlaceholder('Search...')` | Input elements with placeholder attributes. Less stable than labels but useful when labels are absent. |
| 6 (lowest) | CSS / XPath | `page.locator('css=div.card >> nth=0')` or `page.locator('xpath=//div[@class="card"]')` | Last resort. Tightly coupled to DOM structure and CSS classes. Breaks on refactors. Use only when no semantic selector is available. |

**Selector composition**: Playwright supports chaining locators to narrow scope:

```typescript
// Narrow to a specific section, then find within it
const card = page.locator('[data-testid="user-card"]');
await card.getByRole('button', { name: 'Edit' }).click();

// Filter locators
await page.getByRole('listitem').filter({ hasText: 'Product A' }).click();
```

**Strict mode**: Playwright locators operate in strict mode by default. If a locator resolves to more than one element, the action throws a strict mode violation error. Use `.first()`, `.nth(n)`, or `.filter()` to narrow down to a single element when multiple matches are expected.

### Assertion API

Playwright provides auto-retrying assertions via the `expect` API. These assertions automatically wait for the expected condition and retry until the condition is met or the timeout expires.

```typescript
// Element state assertions
await expect(page.getByTestId('status')).toBeVisible();
await expect(page.getByTestId('status')).toBeHidden();
await expect(page.getByTestId('submit')).toBeEnabled();
await expect(page.getByTestId('submit')).toBeDisabled();
await expect(page.getByTestId('checkbox')).toBeChecked();

// Text assertions
await expect(page.getByTestId('heading')).toHaveText('Dashboard');
await expect(page.getByTestId('heading')).toContainText('Dash');

// Attribute and CSS assertions
await expect(page.getByTestId('link')).toHaveAttribute('href', '/dashboard');
await expect(page.getByTestId('alert')).toHaveClass(/error/);
await expect(page.getByTestId('box')).toHaveCSS('color', 'rgb(255, 0, 0)');

// Value assertions (inputs)
await expect(page.getByLabel('Email')).toHaveValue('user@example.com');

// Count assertions
await expect(page.getByRole('listitem')).toHaveCount(5);

// Page-level assertions
await expect(page).toHaveURL(/dashboard/);
await expect(page).toHaveTitle('My App - Dashboard');
```

### Action API

Common Playwright actions used in E2E tests:

```typescript
// Navigation
await page.goto('/login');
await page.goBack();
await page.goForward();
await page.reload();

// Click actions
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('button', { name: 'Submit' }).dblclick();
await page.getByRole('link', { name: 'Home' }).click();

// Form input
await page.getByLabel('Email').fill('user@example.com');
await page.getByLabel('Email').clear();
await page.getByLabel('Email').type('user@example.com'); // types character by character
await page.getByRole('combobox').selectOption('option-value');
await page.getByLabel('I agree').check();
await page.getByLabel('I agree').uncheck();

// File upload
await page.getByLabel('Upload file').setInputFiles('path/to/file.pdf');

// Keyboard and mouse
await page.keyboard.press('Enter');
await page.keyboard.press('Tab');
await page.getByTestId('draggable').dragTo(page.getByTestId('droppable'));

// Focus
await page.getByLabel('Search').focus();
```

---

## Wait Strategy

Playwright has built-in auto-waiting: actions automatically wait for elements to be actionable (visible, stable, enabled, receiving events) before performing the action. This eliminates most explicit wait needs. However, certain scenarios require explicit wait patterns.

### Wait Hierarchy

Use waits in this order of preference. Higher-priority waits are more reliable and less flaky.

| Priority | Strategy | Playwright API | When to Use |
|----------|----------|---------------|-------------|
| 1 (preferred) | Auto-wait (built-in) | All action methods (`click`, `fill`, `check`, etc.) | Default behavior. Playwright waits for elements to be actionable before performing actions. No explicit wait code needed. |
| 2 | Assertion-based wait | `await expect(locator).toBeVisible()` | Wait for a specific UI state before proceeding. Use when you need to verify a condition is true before the next step (e.g., waiting for a loading spinner to disappear, or a result to appear). |
| 3 | URL-based wait | `await expect(page).toHaveURL(url)` or `await page.waitForURL(url)` | Wait for navigation to complete. Use after actions that trigger route changes (link clicks, form submissions, programmatic navigation). |
| 4 | Network-based wait | `await page.waitForResponse(url)` or `await page.waitForRequest(url)` | Wait for a specific API call to complete. Use when UI state depends on data from an API response and assertion-based waits are insufficient. |
| 5 | Load state wait | `await page.waitForLoadState('networkidle')` | Wait for the page to reach a specific load state. Use sparingly -- `networkidle` is unreliable on pages with persistent connections (WebSockets, polling). Prefer assertion-based waits. |

### PROHIBITED: Fixed Delays

**NEVER use `page.waitForTimeout()`**. Fixed delays are the primary cause of flaky E2E tests.

```typescript
// PROHIBITED -- NEVER do this
await page.waitForTimeout(2000);
await page.waitForTimeout(5000);
await new Promise(resolve => setTimeout(resolve, 1000));
```

**Why it is prohibited**: Fixed delays either wait too long (slowing tests) or not long enough (causing flaky failures). They mask the actual condition being waited for and make tests environment-dependent (a 2-second wait may pass locally but fail in CI where resources are constrained).

**What to use instead**:

```typescript
// BAD: Waiting for an element to appear
await page.waitForTimeout(2000);
await page.getByTestId('result').click();

// GOOD: Wait for the element's expected state
await expect(page.getByTestId('result')).toBeVisible();
await page.getByTestId('result').click();

// BAD: Waiting after navigation
await page.getByRole('link', { name: 'Dashboard' }).click();
await page.waitForTimeout(3000);

// GOOD: Wait for the URL to change
await page.getByRole('link', { name: 'Dashboard' }).click();
await expect(page).toHaveURL(/dashboard/);

// BAD: Waiting for API data to load
await page.waitForTimeout(5000);
await expect(page.getByTestId('user-list')).toBeVisible();

// GOOD: Wait for the API response, then assert
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load Users' }).click();
await responsePromise;
await expect(page.getByTestId('user-list')).toBeVisible();
```

### Common Wait Patterns

**Wait for element to disappear** (loading spinners, overlays):

```typescript
await expect(page.getByTestId('loading-spinner')).toBeHidden();
// or
await expect(page.getByTestId('loading-spinner')).not.toBeVisible();
```

**Wait for navigation after form submission**:

```typescript
await page.getByRole('button', { name: 'Submit' }).click();
await page.waitForURL('**/success');
```

**Wait for API response before asserting UI**:

```typescript
const responsePromise = page.waitForResponse(resp =>
  resp.url().includes('/api/data') && resp.status() === 200
);
await page.getByRole('button', { name: 'Refresh' }).click();
await responsePromise;
await expect(page.getByTestId('data-table')).toBeVisible();
```

**Wait for multiple conditions**:

```typescript
await Promise.all([
  page.waitForResponse('**/api/save'),
  page.getByRole('button', { name: 'Save' }).click(),
]);
await expect(page.getByText('Saved successfully')).toBeVisible();
```

---

## Error Regex Patterns

These patterns fill the templates defined in [error-classification.md](../error-classification.md). The validate-agent loads these patterns and matches them against Playwright test output to classify failures into E2E error categories (E1-E6).

### E1: Selector Errors (Subcategory 1f)

```
not_found:        /Error: locator\..* resolved to 0 elements|waiting for locator|No element matches locator/
ambiguous:        /strict mode violation.*resolved to \d+ elements|locator resolved to \d+ elements/
not_interactable: /element is not visible|element is outside of the viewport|element is not enabled|element is not stable|intercepts pointer events/
stale_reference:  /frame was detached|Frame was detached|Execution context was destroyed|element was detached from the DOM/
```

**Pattern notes**:
- `not_found`: Playwright reports "resolved to 0 elements" when a locator matches nothing, and "waiting for locator" when the auto-wait times out looking for the element.
- `ambiguous`: Strict mode violations report the count of matched elements. This fires when a locator matches 2+ elements and no `.first()`/`.nth()` narrowing is applied.
- `not_interactable`: Playwright checks visibility, viewport bounds, enabled state, stability (no animation), and pointer interception (overlays) before acting. Each check produces a distinct message.
- `stale_reference`: Frame detachment and execution context destruction occur when the page navigates away while a locator action is pending.

### E2: Timing Errors (Subcategory 1g)

```
timeout:  /Test timeout of \d+ms exceeded|Timeout \d+ms exceeded|locator\..*: Timeout \d+ms exceeded|Timed out \d+ms waiting for expect/
race:     /Navigation was interrupted|page\.goto: net::ERR_ABORTED|navigating to|frame was detached while waiting/
```

**Pattern notes**:
- `timeout`: Playwright produces several timeout messages: the overall test timeout, individual action timeouts, and assertion (expect) timeouts. All carry the timeout value in milliseconds.
- `race`: Navigation interruption occurs when a page.goto is aborted by another navigation or when a frame detaches during an ongoing operation. These are race conditions between test actions and page activity.

### E3: Navigation Errors (Subcategory 1h)

```
load_failure: /page\.goto:.*net::ERR_CONNECTION_REFUSED|NS_ERROR_CONNECTION_REFUSED|net::ERR_NAME_NOT_RESOLVED|page\.goto:.*ERR_CONNECTION_RESET|ERR_EMPTY_RESPONSE/
url_mismatch: /expect\(page\)\.toHaveURL.*Expected.*Received|expect\.toHaveURL|page\.url\(\).*expected.*to (equal|match|contain)/
redirect:     /ERR_TOO_MANY_REDIRECTS|net::ERR_TOO_MANY_REDIRECTS/
```

**Pattern notes**:
- `load_failure`: Connection refused means the server is not running or is unreachable. Name not resolved means DNS lookup failed (wrong hostname). Connection reset and empty response indicate server-side failures.
- `url_mismatch`: The `toHaveURL` assertion shows "Expected" and "Received" values when the URL does not match, making it easy to identify what the test expected vs what the page actually shows.
- `redirect`: Too many redirects typically indicates a redirect loop (e.g., login page redirects to a page that redirects back to login).

### E4: Network/Mock Errors (Subcategory 1i)

```
unexpected_response: /page\.route.*did not match|Expected.*response.*Received|expect\(response\)\.(toBeOK|toHaveStatus)|response\.status\(\).*expected/
missing_mock:        /net::ERR_FAILED|ERR_NAME_NOT_RESOLVED|net::ERR_INTERNET_DISCONNECTED|net::ERR_BLOCKED_BY_CLIENT/
cors:                /has been blocked by CORS policy|Cross-Origin Request Blocked|Access-Control-Allow-Origin/
```

**Pattern notes**:
- `unexpected_response`: Route handler did not match the request URL pattern, or a response assertion (status code, body) failed.
- `missing_mock`: When tests run against mocked endpoints and a request goes unmatched, it may fail with network errors (especially in isolated/offline test environments). `ERR_BLOCKED_BY_CLIENT` can occur when ad blockers or test isolation blocks the request.
- `cors`: CORS errors appear when tests make cross-origin requests to real servers without proper CORS headers.

### E5: Browser Errors (Subcategory 1j)

```
crash:      /browser has been closed|Browser closed|Browser has been disconnected|Target page, context or browser has been closed/
disconnect: /Target closed|WebSocket.*disconnected|Connection refused|browserType\.launch: Process closed/
resource:   /out of memory|Page crashed|page\.goto: Page crashed|Cannot allocate memory/
```

**Pattern notes**:
- `crash`: Browser process terminated unexpectedly. Common in CI with memory limits or when using too many parallel workers.
- `disconnect`: The WebSocket connection between Playwright and the browser was lost. Can occur due to browser crash, process kill, or network issues between test runner and browser.
- `resource`: Memory exhaustion or page crash due to resource limits. Reduce parallelism (`workers: 1`) or increase container memory.

### E6: UI Assertion Errors (Subcategory 1k)

```
state_mismatch:      /expect\(locator\)\.to(Be|Have).*Expected.*Received|expect\(locator\)\.not\.to(Be|Have)/
text_mismatch:       /expect\(locator\)\.toHaveText.*Expected.*Received|expect\(locator\)\.toContainText.*Expected.*Received/
visibility_mismatch: /expect\(locator\)\.toBeVisible.*Received.*hidden|expect\(locator\)\.toBeHidden.*Received.*visible/
attribute_mismatch:  /expect\(locator\)\.toHaveAttribute.*Expected.*Received|expect\(locator\)\.toHaveClass.*Expected.*Received|expect\(locator\)\.toHaveCSS.*Expected.*Received/
count_mismatch:      /expect\(locator\)\.toHaveCount.*Expected.*Received/
```

**Pattern notes**:
- `state_mismatch`: Catch-all for any `expect(locator).toBe*` or `expect(locator).toHave*` assertion failure. Matches both positive and negative (`.not`) assertions.
- `text_mismatch`: Specific to `toHaveText` and `toContainText` failures. The "Expected" and "Received" values in the output show exactly what text was expected vs what was found.
- `visibility_mismatch`: Element was expected to be visible but was hidden, or vice versa.
- `attribute_mismatch`: Attribute, class, or CSS property did not match expected value.
- `count_mismatch`: Number of elements matched by locator differs from expected count.

### Pattern Matching Order

The validate-agent matches error output against these patterns in category order (E1 through E6). Within each category, patterns are checked in the order listed above. The first match determines the classification.

If error output matches patterns from multiple categories (e.g., a timeout waiting for a selector), the more specific category wins:
- Timeout while waiting for a selector -> E1 (Selector), not E2 (Timing), because the root cause is the selector
- General test timeout with no specific selector context -> E2 (Timing)
- URL assertion failure -> E3 (Navigation), not E6 (UI Assertion), because it is navigation-specific

---

## playwright-cli Workflows

The `playwright-cli` tool provides browser exploration capabilities for the analyze-agent and fix-agent. It launches a browser session where agents can inspect page structure, discover selectors, and verify element state.

### Installation

```bash
npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --skills
```

The `install --skills` subcommand installs browser binaries (Chromium, Firefox, WebKit) required for exploration. This is separate from the test framework's browser installation (`npx playwright install`).

### Commands

#### Open Browser at URL

```bash
playwright-cli open <url>
```

Opens a Chromium browser at the specified URL. Use this to begin exploration of the application under test.

```bash
playwright-cli open http://localhost:3000
playwright-cli open http://localhost:3000/login
```

**Output**: Confirmation that the browser opened and the page title.

#### Capture Accessibility Tree Snapshot

```bash
playwright-cli snapshot
```

Captures the current page's accessibility tree, which represents the semantic structure of the page. This is the primary tool for discovering selectors because it shows roles, names, and test IDs.

**Output**: Structured accessibility tree showing each element's role, name, and attributes:

```
- document "My Application"
  - navigation "Main Menu"
    - link "Home" [data-testid="nav-home"]
    - link "Dashboard" [data-testid="nav-dashboard"]
    - link "Settings"
  - main
    - heading "Welcome" [level=1]
    - form "Login"
      - textbox "Email" [data-testid="email-input"]
      - textbox "Password" [data-testid="password-input"]
      - button "Sign In" [data-testid="submit-btn"]
```

**Usage for selector discovery**: From the snapshot above, the agent can determine:
- `page.getByTestId('submit-btn')` (Priority 1 -- test ID present)
- `page.getByRole('button', { name: 'Sign In' })` (Priority 2 -- role + name)
- `page.getByLabel('Email')` (Priority 3 -- form label)
- `page.getByText('Welcome')` (Priority 4 -- visible text)

#### Navigate Within Session

```bash
playwright-cli navigate <path>
```

Navigates the current browser session to a new path (relative to the current origin). Use this to explore multiple pages without opening new browser windows.

```bash
playwright-cli navigate /dashboard
playwright-cli navigate /settings/profile
playwright-cli navigate /login?redirect=/dashboard
```

**Output**: Confirmation of navigation and new page title.

#### Interactive Selector Finder

```bash
playwright-cli inspect
```

Activates an interactive mode where the agent can hover over elements to see their recommended selectors. Playwright's inspector suggests selectors following the priority strategy (test ID > role > label > text > CSS).

**Output**: For each inspected element, returns the recommended selector and alternatives:

```
Element: <button data-testid="submit-btn" class="btn-primary">Sign In</button>
Recommended: getByTestId('submit-btn')
Alternatives:
  - getByRole('button', { name: 'Sign In' })
  - locator('.btn-primary')
```

### Session Management

#### Named Sessions

Named sessions allow the agent to maintain separate browser states (e.g., authenticated vs unauthenticated) for exploration.

```bash
playwright-cli open http://localhost:3000 --session auth-session
playwright-cli open http://localhost:3000 --session unauth-session
playwright-cli snapshot --session auth-session
playwright-cli snapshot --session unauth-session
```

This is useful for comparing page structure between authenticated and unauthenticated views to identify auth-gated elements.

#### Tracing

Tracing captures a detailed execution trace that includes screenshots, DOM snapshots, and network activity. Useful for debugging test failures.

```bash
playwright-cli tracing-start
# ... perform actions ...
playwright-cli tracing-stop --output trace.zip
```

The trace file can be viewed with `npx playwright show-trace trace.zip` for a timeline view of all actions, network requests, and console logs.

### Browser Exploration Workflow

When the analyze-agent or fix-agent uses browser exploration, it follows this workflow:

```
1. Verify application is running (check baseURL accessibility)
2. Open browser: playwright-cli open {baseURL}
3. Capture initial snapshot: playwright-cli snapshot
4. Navigate to target pages: playwright-cli navigate {route}
5. Capture snapshot at each page: playwright-cli snapshot
6. For selector issues: playwright-cli inspect to verify element presence
7. Extract selectors from snapshots using priority strategy
8. Close session when exploration is complete
```

---

## Config Parsing

When the analyze-agent processes a Playwright project, it parses `playwright.config.ts` (or `playwright.config.js`) to extract configuration values that inform test generation and execution.

### Config File Locations

Search for config files in this order (first found wins):

1. `playwright.config.ts` (project root)
2. `playwright.config.js` (project root)
3. `playwright.config.mts` (project root)
4. `playwright.config.mjs` (project root)

### Fields to Extract

#### `baseURL`

The base URL for all `page.goto()` calls. Extracted from `use.baseURL`.

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    baseURL: 'http://localhost:3000',
  },
});
```

**Extraction pattern**: Look for `baseURL` within the `use` configuration block. This value is passed to the analyze-agent as `base_url` and used by the execute-agent to verify application availability.

#### `testDir`

The directory containing test files. Defaults to the project root if not specified.

```typescript
export default defineConfig({
  testDir: './tests/e2e',
});
```

**Extraction pattern**: Look for `testDir` at the top level of the config. The write-agent places generated test files in this directory. The execute-agent uses it to scope test execution.

#### `projects`

Array of project configurations defining browser and device variants. Each project can override `use` settings.

```typescript
export default defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
```

**Extraction pattern**: Look for the `projects` array. Each entry has a `name` and optional `use` overrides. The execute-agent can target specific projects with `--project=chromium`. The analyze-agent notes which browsers are configured for potential browser-specific test considerations.

#### `webServer`

Configuration for automatically starting the application server before tests.

```typescript
export default defineConfig({
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

**Extraction pattern**: Look for `webServer` at the top level. If present, the execute-agent does NOT need to verify application availability separately -- Playwright handles server startup. If absent, the execute-agent must verify `baseURL` is accessible before running tests.

Multiple web servers are also supported:

```typescript
export default defineConfig({
  webServer: [
    { command: 'npm run dev', url: 'http://localhost:3000' },
    { command: 'npm run api', url: 'http://localhost:4000' },
  ],
});
```

#### `use.storageState`

Path to a stored authentication state file used to skip login for authenticated tests.

```typescript
export default defineConfig({
  use: {
    storageState: 'playwright/.auth/user.json',
  },
});
```

**Extraction pattern**: Look for `storageState` within the `use` block. If present, the project has an auth setup mechanism. The analyze-agent notes this for test generation: authenticated test fixtures should reference this storage state rather than performing login in every test.

#### `timeout` and `expect.timeout`

Global timeouts for test execution and assertions.

```typescript
export default defineConfig({
  timeout: 30000,        // per-test timeout (default 30s)
  expect: {
    timeout: 5000,       // per-assertion timeout (default 5s)
  },
});
```

**Extraction pattern**: Note configured timeouts so fix strategies can reference them when diagnosing timeout errors.

#### `retries`

Number of times to retry failed tests.

```typescript
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
});
```

**Extraction pattern**: Note retry configuration. The result parser must account for retry output when counting passes/failures.

#### `reporter`

Configured reporters. Dante overrides with `--reporter=list` for execution but notes the project's configured reporters for context.

```typescript
export default defineConfig({
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'results.xml' }],
  ],
});
```

### Config Parsing Example

Given a typical `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    storageState: 'e2e/.auth/user.json',
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

The analyze-agent extracts:

```yaml
e2e_config:
  base_url: "http://localhost:3000"
  test_dir: "./e2e"
  projects: ["chromium", "firefox"]
  web_server: { command: "npm run dev", url: "http://localhost:3000" }
  storage_state: "e2e/.auth/user.json"
  timeout: 30000
  retries: 2  # CI value
  has_auth_setup: true
```

---

## Fix Strategies

Framework-specific fix strategies for each E2E error category. The fix-agent loads these strategies when resolving Playwright test failures classified by the validate-agent.

### E1: Selector Errors (Subcategory 1f)

**Root cause**: The test targets an element using a selector that no longer matches (or never matched) the current DOM.

**Fix strategy**:

1. **Verify element exists** -- Use `playwright-cli snapshot` to capture the current page accessibility tree and confirm whether the target element is present.

2. **Apply selector priority fallback** -- Walk down the selector priority list until a working selector is found:
   - Check for `data-testid` attribute on the element -> `page.getByTestId('...')`
   - Check for ARIA role and accessible name -> `page.getByRole('...', { name: '...' })`
   - Check for associated label (form elements) -> `page.getByLabel('...')`
   - Check for unique visible text -> `page.getByText('...')`
   - Last resort: construct a CSS selector -> `page.locator('...')`

3. **Fix strict mode violations** -- If the error is "resolved to N elements":
   ```typescript
   // BAD: Ambiguous -- matches multiple buttons
   await page.getByRole('button').click();

   // GOOD: Narrow with name
   await page.getByRole('button', { name: 'Submit' }).click();

   // GOOD: Narrow with scope
   await page.getByTestId('login-form').getByRole('button', { name: 'Submit' }).click();

   // GOOD: Use .first() or .nth() when order is meaningful
   await page.getByRole('listitem').first().click();
   ```

4. **Fix not-interactable errors** -- If the element exists but is not interactable:
   ```typescript
   // Wait for overlay/spinner to disappear before acting
   await expect(page.getByTestId('loading-overlay')).toBeHidden();
   await page.getByRole('button', { name: 'Submit' }).click();

   // Scroll element into viewport if needed
   await page.getByTestId('footer-link').scrollIntoViewIfNeeded();
   await page.getByTestId('footer-link').click();
   ```

5. **Fix stale references** -- If a frame/context was destroyed:
   ```typescript
   // Wait for navigation to complete before acting on new page
   await page.waitForURL('**/new-page');
   await page.getByTestId('element-on-new-page').click();
   ```

### E2: Timing Errors (Subcategory 1g)

**Root cause**: The test does not wait long enough for an element, condition, or navigation to complete.

**Fix strategy**:

1. **Replace fixed waits with assertion-based waits**:
   ```typescript
   // BAD
   await page.waitForTimeout(3000);
   await page.getByTestId('result').click();

   // GOOD
   await expect(page.getByTestId('result')).toBeVisible();
   await page.getByTestId('result').click();
   ```

2. **Add waits for preceding conditions** -- The element may depend on a network request or navigation:
   ```typescript
   // Wait for API call that populates the data
   await page.waitForResponse('**/api/data');
   await expect(page.getByTestId('data-table')).toBeVisible();
   ```

3. **Increase specific timeouts** -- If an operation legitimately takes longer (file upload, report generation), increase the specific assertion or action timeout rather than adding a sleep:
   ```typescript
   // Increase timeout for a slow operation
   await expect(page.getByTestId('report')).toBeVisible({ timeout: 60000 });
   ```

4. **Fix race conditions between navigation and actions**:
   ```typescript
   // BAD: Action may fire before navigation completes
   await page.getByRole('link', { name: 'Dashboard' }).click();
   await page.getByTestId('dashboard-widget').click();

   // GOOD: Wait for navigation, then act
   await page.getByRole('link', { name: 'Dashboard' }).click();
   await page.waitForURL('**/dashboard');
   await page.getByTestId('dashboard-widget').click();
   ```

### E3: Navigation Errors (Subcategory 1h)

**Root cause**: The page failed to load, the URL does not match expectations, or navigation enters a redirect loop.

**Fix strategy**:

1. **Verify application is running** -- For `ERR_CONNECTION_REFUSED`:
   - Check that the development server is started (see `webServer` config)
   - Verify the `baseURL` is correct and accessible
   - If using `webServer` config, ensure the `command` and `url` are correct

2. **Add `page.waitForURL()` after navigation actions**:
   ```typescript
   // BAD: No wait after navigation
   await page.getByRole('link', { name: 'Settings' }).click();
   await expect(page.getByText('Settings Page')).toBeVisible();

   // GOOD: Wait for URL before asserting content
   await page.getByRole('link', { name: 'Settings' }).click();
   await page.waitForURL('**/settings');
   await expect(page.getByText('Settings Page')).toBeVisible();
   ```

3. **Fix URL mismatch assertions** -- Review the expected URL pattern:
   ```typescript
   // BAD: Exact URL match is fragile
   await expect(page).toHaveURL('http://localhost:3000/dashboard');

   // GOOD: Use pattern matching for the path
   await expect(page).toHaveURL(/\/dashboard/);

   // GOOD: Match path with query params flexibility
   await expect(page).toHaveURL(/\/dashboard(\?.*)?$/);
   ```

4. **Fix redirect loops** -- Typically caused by missing auth state:
   ```typescript
   // If redirecting to login, the test needs auth setup
   // Use storageState to skip login
   test.use({ storageState: 'playwright/.auth/user.json' });

   test('access dashboard', async ({ page }) => {
     await page.goto('/dashboard');
     await expect(page).toHaveURL(/dashboard/); // no redirect to login
   });
   ```

### E4: Network/Mock Errors (Subcategory 1i)

**Root cause**: An API request was not intercepted by a mock, returned unexpected data, or was blocked.

**Fix strategy**:

1. **Add `page.route()` for API mocking**:
   ```typescript
   // Mock an API endpoint
   await page.route('**/api/users', async route => {
     await route.fulfill({
       status: 200,
       contentType: 'application/json',
       body: JSON.stringify([{ id: 1, name: 'Test User' }]),
     });
   });
   ```

2. **Fix route URL patterns** -- Ensure the pattern matches the actual request:
   ```typescript
   // BAD: Pattern too specific
   await page.route('http://localhost:3000/api/users', ...);

   // GOOD: Use glob pattern to match regardless of host
   await page.route('**/api/users', ...);

   // GOOD: Match with query parameters
   await page.route('**/api/users?page=*', ...);

   // GOOD: Use regex for complex patterns
   await page.route(/\/api\/users\/\d+/, ...);
   ```

3. **Fix response format** -- Ensure mock returns correct structure:
   ```typescript
   await page.route('**/api/data', async route => {
     await route.fulfill({
       status: 200,
       contentType: 'application/json',
       body: JSON.stringify({
         data: [...],  // match the shape the app expects
         total: 10,
         page: 1,
       }),
     });
   });
   ```

4. **Add error response mocks** for error handling tests:
   ```typescript
   await page.route('**/api/save', async route => {
     await route.fulfill({
       status: 500,
       contentType: 'application/json',
       body: JSON.stringify({ error: 'Internal Server Error' }),
     });
   });
   ```

5. **Clean up routes** -- Ensure stale mocks from other tests do not interfere:
   ```typescript
   // Routes are per-page context and isolated between tests by default
   // If using shared context, unroute explicitly:
   await page.unroute('**/api/users');
   ```

### E5: Browser Errors (Subcategory 1j)

**Root cause**: Browser crashed, disconnected, or exhausted resources. Almost always an environment issue (Category 3), not a test bug.

**Fix strategy**:

1. **Verify browser installation**:
   ```bash
   npx playwright install
   npx playwright install chromium  # install specific browser
   ```

2. **Reduce parallelism** -- Browser resource exhaustion often occurs with too many parallel workers:
   ```typescript
   // playwright.config.ts
   export default defineConfig({
     workers: process.env.CI ? 1 : undefined,
   });
   ```
   Or via command line: `npx playwright test --workers=1`

3. **Ensure test isolation** -- Each test should use a fresh browser context:
   ```typescript
   // Default Playwright fixtures already provide per-test isolation
   // page and context are fresh for each test
   test('test one', async ({ page }) => { ... });
   test('test two', async ({ page }) => { ... });
   ```

4. **Increase container resources** -- In CI environments, increase memory and CPU allocation for the test job.

5. **Check for browser-specific issues** -- If the error occurs only in one browser, try running with `--project=chromium` to isolate.

### E6: UI Assertion Errors (Subcategory 1k)

**Root cause**: The test asserts an incorrect expected value, or the application renders unexpected content.

**Fix strategy**:

1. **Verify expected values** -- Use `playwright-cli snapshot` to see the actual page state:
   ```typescript
   // If text changed from "Welcome" to "Welcome back"
   // BAD: Exact match
   await expect(page.getByTestId('greeting')).toHaveText('Welcome');

   // GOOD: Flexible match
   await expect(page.getByTestId('greeting')).toContainText('Welcome');
   ```

2. **Handle dynamic content** -- Dates, timestamps, generated IDs require flexible assertions:
   ```typescript
   // BAD: Exact match on dynamic date
   await expect(page.getByTestId('date')).toHaveText('February 16, 2026');

   // GOOD: Use regex for dynamic parts
   await expect(page.getByTestId('date')).toHaveText(/\w+ \d+, \d{4}/);
   ```

3. **Wait for correct state before asserting** -- The element may be in a transitional state:
   ```typescript
   // BAD: Assert immediately (element may show loading state)
   await expect(page.getByTestId('status')).toHaveText('Complete');

   // GOOD: Wait for loading to finish first
   await expect(page.getByTestId('loading')).toBeHidden();
   await expect(page.getByTestId('status')).toHaveText('Complete');
   ```

4. **Fix count mismatches** -- Verify data setup or filter conditions:
   ```typescript
   // If list has more/fewer items than expected, check data setup
   await expect(page.getByRole('listitem')).toHaveCount(5);
   // Verify: Is the seed data producing exactly 5 items?
   // Is there pagination cutting off results?
   ```

5. **Distinguish test bug from app bug** -- If the actual value shown in the error output is correct for the current app behavior and the test expectation is outdated, update the test. If the actual value is wrong, this is a Category 2 (Application Bug) -- report it rather than "fixing" the test.

---

## Execution

### Command Construction

The execute-agent constructs Playwright test commands using this reference.

**Run all tests**:

```bash
npx playwright test --reporter=list
```

**Run specific test files**:

```bash
npx playwright test tests/e2e/login.spec.ts tests/e2e/checkout.spec.ts --reporter=list
```

**Run specific test by name**:

```bash
npx playwright test -g "user can log in with valid credentials" --reporter=list
```

**Run tests in a specific project (browser)**:

```bash
npx playwright test --project=chromium --reporter=list
```

**Run in headed mode** (for debugging, not default):

```bash
npx playwright test --headed --reporter=list
```

**Run with specific workers**:

```bash
npx playwright test --workers=1 --reporter=list
```

### Browser Installation Check

Before executing tests, verify browsers are installed:

```bash
npx playwright install --dry-run
```

If browsers are missing, install them:

```bash
npx playwright install
```

For CI environments with specific browser needs:

```bash
npx playwright install --with-deps chromium
```

The `--with-deps` flag also installs system-level dependencies (shared libraries) required by the browser.

### Application Availability Check

If the `playwright.config.ts` does NOT have a `webServer` configuration, the execute-agent must verify the application is accessible before running tests:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

If the status code is not 2xx or 3xx, warn the user that the application server does not appear to be running.

If the config DOES have `webServer`, skip this check -- Playwright handles server startup.

### Timeout Configuration

Default timeout for E2E test execution: **5 minutes** (300,000 ms). This is the outer timeout for the entire test run command, not the per-test timeout (which is configured in `playwright.config.ts`).

---

## Best Practices

### SPA Client-Side Routing

Single-page applications (React Router, Next.js, Vue Router) perform navigation without full page loads. Playwright handles this transparently, but tests must account for it:

```typescript
// Client-side navigation: URL changes without page reload
await page.getByRole('link', { name: 'Dashboard' }).click();
// Use waitForURL -- works for both full page loads and SPA routing
await page.waitForURL('**/dashboard');
// Now assert on the new page content
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
```

**Do not use** `page.waitForNavigation()` for SPA routing -- it waits for a network navigation event that may not fire. Use `page.waitForURL()` or assertion-based waits instead.

### Authentication State Reuse via storageState

Performing login in every test is slow and fragile. Use `storageState` to capture authenticated state once and reuse it:

**Setup project pattern** (recommended):

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    // Setup project: performs login and saves state
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

**Tests that require unauthenticated state** should explicitly clear storage:

```typescript
test.use({ storageState: { cookies: [], origins: [] } });

test('login page shows form', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByLabel('Email')).toBeVisible();
});
```

### Parallel Isolation via browser.newContext()

Each Playwright test runs in an isolated `BrowserContext` by default (separate cookies, localStorage, session). This provides natural test isolation without extra setup:

```typescript
// Each test gets its own page and context -- no shared state
test('test A', async ({ page }) => {
  // This page has its own cookies, localStorage, etc.
});

test('test B', async ({ page }) => {
  // Completely isolated from test A
});
```

For tests that need multiple contexts (e.g., testing multi-user interactions):

```typescript
test('two users can chat', async ({ browser }) => {
  const userOneContext = await browser.newContext({ storageState: 'auth/user1.json' });
  const userTwoContext = await browser.newContext({ storageState: 'auth/user2.json' });
  const userOnePage = await userOneContext.newPage();
  const userTwoPage = await userTwoContext.newPage();

  // Interact as two separate users simultaneously
  await userOnePage.goto('/chat');
  await userTwoPage.goto('/chat');
  // ...
});
```

### React DevTools Interference

React DevTools browser extension can interfere with Playwright tests by injecting scripts and modifying the component tree. Symptoms include:
- Unexpected elements in snapshots (DevTools overlay components)
- Slower test execution due to DevTools instrumentation
- Additional network requests from DevTools

**Mitigation**: Playwright test browsers launch with a clean profile (no extensions) by default. This is only an issue when running in headed mode with `--headed` and a user profile that has DevTools installed. If interference is observed:

```typescript
// Force a clean context with no extensions
const context = await browser.newContext({
  // Launch args to disable extensions
  ignoreHTTPSErrors: true,
});
```

In most cases, no action is needed because Playwright's default browser launch does not load user extensions.

### Network Mocking Patterns

For E2E tests that need deterministic API responses:

```typescript
// Mock all API calls in a beforeEach
test.beforeEach(async ({ page }) => {
  // Mock user data endpoint
  await page.route('**/api/user', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 1, name: 'Test User', role: 'admin' }),
    });
  });
});

test('shows user name in header', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('user-name')).toHaveText('Test User');
});
```

**Selective mocking** -- let some requests pass through to the real server:

```typescript
await page.route('**/api/users', route => route.fulfill({ ... })); // mocked
// /api/settings goes to real server (no route registered)
```

**Abort requests** (test error handling):

```typescript
await page.route('**/api/data', route => route.abort('failed'));
```

### Test File Organization

Organize E2E tests by user flow or feature, not by source file:

```
tests/e2e/
  auth/
    login.spec.ts         # Login flow: valid creds, invalid creds, forgot password
    registration.spec.ts  # Registration flow: new user signup
  dashboard/
    overview.spec.ts      # Dashboard overview: widgets, data loading
    filters.spec.ts       # Dashboard filtering: date range, category
  checkout/
    cart.spec.ts           # Shopping cart: add, remove, update quantity
    payment.spec.ts        # Payment flow: credit card, validation
  navigation/
    main-nav.spec.ts       # Primary navigation: menu links, active state
    breadcrumbs.spec.ts    # Breadcrumb navigation
```

### Test Naming Convention

Test names describe user-visible behavior, not implementation details:

```typescript
// GOOD: Describes what the user experiences
test('user can log in with valid credentials', async ({ page }) => { ... });
test('shows error message for invalid password', async ({ page }) => { ... });
test('shopping cart updates total when item quantity changes', async ({ page }) => { ... });

// BAD: Describes implementation
test('LoginForm component handles submit', async ({ page }) => { ... });
test('API returns 401 for invalid token', async ({ page }) => { ... });
test('Redux store updates cart state', async ({ page }) => { ... });
```

---

## References

- **Parent skill**: [E2E Testing Skill](../SKILL.md) -- Generic E2E contract, error taxonomy, agent behavior
- **Error classification**: [error-classification.md](../error-classification.md) -- Universal E1-E6 category definitions and pattern templates
- **Knowledge management**: [knowledge-management.md](../knowledge-management.md) -- `.dante/e2e-knowledge/` specification
- **Browser exploration**: [browser-exploration.md](../browser-exploration.md) -- Generic exploration interface
- **Specification**: `.sdd/specs/2026-02-13-e2e-web-test-authoring.md` -- Requirements (REQ-F-6, REQ-F-29, REQ-F-30, REQ-F-31)
- **Plan**: `.sdd/plans/2026-02-13-e2e-web-test-authoring-plan.md` -- Technical decisions (TD-1, TD-7)
- **Playwright docs**: https://playwright.dev/docs/api/class-page

---

**Last Updated**: 2026-02-16
**Status**: Full implementation -- all sections complete
**Framework Version Tested Against**: Playwright 1.50+
