# E2E Browser Exploration

**Version**: 2.0.0
**Parent Skill**: [E2E Testing Skill](./SKILL.md)
**Purpose**: Generic browser exploration contract defining capabilities, agent workflow, activation rules, and installation instructions

## Overview

Browser exploration allows agents to interact with the running application under test to discover page structure, element selectors, navigation routes, and UI state. This capability is used by the analyze-agent (to discover test targets and selectors), the write-agent (to verify selectors against the live DOM when generating page objects), and the fix-agent (to verify element existence when fixing selector errors).

Browser exploration is **enabled by default** when the application is accessible at `base_url`. It enhances E2E test generation by providing accurate selectors from the live DOM, significantly reducing fix-agent iterations. When the app is not running or exploration is explicitly disabled, agents fall back to static analysis.

## Exploration Activation

Browser exploration is **enabled by default** when the application is accessible. Agents activate exploration automatically without requiring user opt-in.

### Opt-Out Methods

1. **CLI flag**: `--no-explore` disables exploration entirely
2. **CI environment**: When `CI=true` environment variable is set, exploration defaults to disabled (override with `--explore` flag)
3. **App not running**: Exploration is auto-skipped when the application is not accessible at `base_url`

### Safety Considerations

Browser exploration is safe by design:
- **Read-only**: Exploration uses only snapshot and inspect operations — no form submissions, clicks, or data mutations
- **Accessibility tree**: Captures the accessibility tree structure, not screenshots or visual content
- **Resource-bounded**: Sessions are short-lived and use a single browser context
- **No network side effects**: Exploration does not trigger API calls or data modifications beyond initial page loads

### When Exploration Is Disabled

If browser exploration is disabled (via `--no-explore`, CI environment, or app not accessible):

1. Agents skip all exploration steps
2. Test generation relies on static analysis (existing tests, config files, source code, project patterns)
3. The analyze-agent notes `browser_exploration: disabled` and `browser_exploration_reason` in its output
4. No exploration tools are launched

## App Availability Check

Before activating browser exploration, agents run this check algorithm:

```
1. Extract base_url from parsed E2E config
2. Check --no-explore flag
   → If set: disabled, reason: "user opted out"
3. Check CI=true environment variable (without --explore override)
   → If CI=true and no --explore: disabled, reason: "CI environment"
4. Probe base_url (HTTP request, 5s timeout, any response with status < 500 = accessible)
   → Accessible: enabled, reason: "app accessible at {base_url}"
   → Not accessible: disabled, reason: "app not accessible at {base_url}"
```

Output fields:
- `browser_exploration`: `true` or `false`
- `browser_exploration_reason`: Human-readable reason string

## Capability Table

The following capabilities are universal across E2E frameworks. The specific tool commands differ per framework and are defined in `skills/e2e/frameworks/{framework}.md`.

| Capability | Description | Playwright | Cypress | Selenium |
|-----------|-------------|------------|---------|----------|
| **Open URL** | Launch browser at a specific URL | `playwright-cli open <url>` | `cypress open` | WebDriver `get(url)` |
| **Snapshot** | Capture element tree or accessibility tree of current page | `playwright-cli snapshot` | Component snapshot | `getPageSource()` |
| **Navigate** | Go to a specific route within the application | `playwright-cli navigate <path>` | `cy.visit(path)` | `get(url+path)` |
| **Inspect** | Get details about a specific element (attributes, text, state) | `playwright-cli inspect` | Selector playground | `findElement` + attribute queries |

### Capability Details

#### Open URL

Opens a browser window and navigates to the specified URL. This is the entry point for all exploration sessions.

- **Input**: URL to open (typically the application's `base_url`)
- **Output**: Browser window opened; ready for further exploration
- **Prerequisites**: Browser binaries installed; application running at the target URL

#### Snapshot

Captures a structured representation of the current page. The output format varies by framework (accessibility tree, DOM tree, component tree) but always provides element identification information useful for writing selectors.

- **Input**: None (captures current page state)
- **Output**: Structured element tree with roles, names, text content, and attributes
- **Use case**: Discover available elements, identify test IDs, understand page layout

#### Navigate

Navigates to a different route within the same application session, preserving cookies, auth state, and session data.

- **Input**: Path or route to navigate to (e.g., `/dashboard`, `/settings/profile`)
- **Output**: Page navigated; new page state available for snapshot
- **Use case**: Explore multiple pages within a single exploration session

#### Inspect

Provides detailed information about a specific element, including its attributes, computed styles, accessibility properties, and interactability state.

- **Input**: Selector or element identifier
- **Output**: Element details (tag, attributes, text, visibility, enabled state)
- **Use case**: Verify element properties when writing or fixing selectors

## Agent Workflow

When browser exploration is active and the application is running, agents follow this workflow:

```
1. Detect Framework
   -> Read framework from detection output (e.g., "playwright")

2. Look Up Tool Commands
   -> Read skills/e2e/frameworks/{framework}.md
   -> Find the exploration tool section
   -> Extract specific commands for Open URL, Snapshot, Navigate, Inspect

3. Verify Prerequisites
   -> Check that the exploration tool is installed (installation check from framework reference)
   -> Check that the application is accessible at base_url
   -> If either check fails, skip exploration and proceed with static analysis

4. Execute Exploration
   -> Open URL at base_url
   -> Snapshot the landing page (capture element tree)
   -> Navigate to key routes (from config or user patterns)
   -> Snapshot each key page
   -> Inspect specific elements of interest

5. Parse Output
   -> Extract element identifiers, roles, names, text content
   -> Identify available test IDs (data-testid, data-cy, data-test attributes)
   -> Map page structure (headings, forms, navigation, interactive elements)

6. Feed Into Analysis
   -> page_structures added to analyze-agent output
   -> Selector candidates available for write-agent
   -> Element verification available for fix-agent
```

### Analyze Agent Usage

The analyze-agent uses browser exploration during initial project analysis:

1. Open the application at `base_url`
2. Snapshot the landing page to discover page structure
3. Navigate to key routes identified from config or existing tests
4. Snapshot each page to build a map of available elements and selectors
5. Include discovered page structures in analysis output for the write-agent

### Write Agent Usage

The write-agent uses browser exploration when generating page objects and test cases:

1. For each page involved in the user flows, navigate to the page route
2. Snapshot the page to capture the element tree (roles, labels, test IDs, text content)
3. Use discovered selectors directly in page objects instead of inferring from static analysis
4. This produces accurate selectors on the first pass, reducing Execute → Validate → Fix iterations

### Fix Agent Usage

The fix-agent uses browser exploration when fixing E2E test failures:

**E1 (Selector errors)**: Primary usage — navigate to failure URL, snapshot page, discover correct selector from live DOM.

**E2 (Timing errors)**: Diagnostic snapshot — check if the waited-on element exists. If not found, reclassify as E1 and fix the selector instead of the wait.

**E3 (Navigation errors)**: Diagnostic snapshot — inspect actual page state after navigation to confirm whether it's an auth redirect, wrong URL, or app bug. Boosts fix confidence.

**E6 (UI Assertion errors)**: Diagnostic snapshot — verify the asserted element exists and check its actual content. If element not found, reclassify as E1. If found, use live content to inform assertion fix.

Workflow:
1. Open the application at the URL where the failure occurred
2. Snapshot the page to see current element state
3. For E1: find correct selector in live DOM
4. For E2/E3/E6: check if waited-on/asserted element exists — reclassify to E1 if not found
5. Apply the fix using verified information from the snapshot

## Installation Instructions

Each E2E framework has its own exploration tool with specific installation requirements. The commands below are summaries; the authoritative installation instructions are in each framework's reference file.

### Playwright

```bash
# Install Playwright CLI globally
npm install -g @playwright/cli@latest

# Install browser binaries
playwright-cli install --skills

# Verify installation
playwright-cli --version
```

**Tool**: `playwright-cli` (command-line interface for browser exploration)
**Browsers**: Chromium, Firefox, WebKit (installed via `playwright-cli install`)
**Full details**: `skills/e2e/frameworks/playwright.md`

### Cypress

```bash
# Cypress is typically installed as a project dependency
npm install --save-dev cypress

# Open Cypress interactive mode (includes selector playground)
npx cypress open
```

**Tool**: `cypress open` (interactive test runner with built-in selector playground)
**Browsers**: Uses system-installed Chrome, Firefox, Edge, or bundled Electron
**Full details**: `skills/e2e/frameworks/cypress.md`

### Selenium

```bash
# Installation varies by language:

# JavaScript
npm install --save-dev selenium-webdriver

# Python
pip install selenium

# Java (via Maven)
# Add selenium-java dependency to pom.xml
```

**Tool**: WebDriver API (programmatic browser control)
**Browsers**: Requires browser-specific drivers (ChromeDriver, GeckoDriver, etc.)
**Full details**: `skills/e2e/frameworks/selenium.md`

## Session Management

Browser exploration sessions should be managed carefully to avoid resource leaks and state contamination:

### Session Lifecycle

1. **Start**: Open a new exploration session when exploration begins
2. **Reuse**: Reuse the same session for navigating multiple pages within one analysis pass
3. **End**: Close the session when exploration is complete (after all pages are snapshotted)

### Auth Considerations

- If the application requires authentication, the exploration session must be authenticated
- The framework reference file defines how to set up authenticated exploration sessions (e.g., Playwright's `storageState`, Cypress's `cy.session()`)
- Agents should check `project-patterns.md` for project-specific auth setup instructions

### Parallel Safety

- Exploration sessions should not interfere with concurrent test execution
- Use a separate browser context or profile for exploration
- The framework reference file defines how to isolate exploration from test execution

---

**Last Updated**: 2026-02-25
**Status**: Phase 2 - Browser exploration default-on when app accessible
**Next**: Framework-specific exploration workflows in framework reference files
