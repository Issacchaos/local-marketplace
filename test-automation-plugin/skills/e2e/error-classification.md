# E2E Error Classification Reference

**Version**: 1.0.0
**Parent Skill**: [E2E Testing Skill](./SKILL.md)
**Purpose**: Complete error classification reference with universal categories and parameterized pattern matching for E2E test failures

## Overview

This document defines the six universal E2E error categories (E1-E6), their generic symptoms, parameterized pattern templates, resolution strategy templates, and classification rules. All categories are framework-agnostic -- the specific error messages and regex patterns are provided by framework-specific reference files (`skills/e2e/frameworks/{framework}.md`) that fill in the `{FRAMEWORK_SPECIFIC_*}` placeholders defined here.

## Subcategory Mapping Table

E2E error categories extend the existing validate-agent subcategory taxonomy. Unit test subcategories (1a-1e) remain unchanged; E2E subcategories (1f-1k) are added when `test_type=e2e`.

| Subcategory | E2E Category | Name | Scope |
|-------------|-------------|------|-------|
| 1a | -- | Import/Syntax Error | Unit tests |
| 1b | -- | Fixture/Setup Error | Unit tests |
| 1c | -- | Assertion Logic Error | Unit tests |
| 1d | -- | Mock/Stub Error | Unit tests |
| 1e | -- | Async/Timing Error | Unit tests |
| 1f | E1 | Selector Issue | E2E tests |
| 1g | E2 | Timing Issue | E2E tests |
| 1h | E3 | Navigation Issue | E2E tests |
| 1i | E4 | Network/Mock Issue | E2E tests |
| 1j | E5 | Browser Issue | E2E tests |
| 1k | E6 | UI Assertion Issue | E2E tests |

When classifying E2E failures, the validate-agent checks E2E patterns (1f-1k) first. If no E2E pattern matches, the agent falls through to standard subcategories (1a-1e) for errors that are not browser-specific (e.g., a syntax error in an E2E test file is still 1a).

---

## E1: Selector Errors

**Subcategory**: 1f
**Description**: Element identified by selector cannot be found, matches multiple elements, is not interactable, or has become stale (removed from DOM).

### Generic Symptoms

- Element not found at the specified selector
- Multiple elements match the selector (ambiguous/strict mode violation)
- Element exists but is not interactable (hidden, disabled, obscured by overlay)
- Stale element reference (element was removed from the DOM between lookup and interaction)

### Pattern Templates

Framework reference files fill in these placeholders with framework-specific regex patterns:

```
not_found:        {FRAMEWORK_SPECIFIC_NOT_FOUND_PATTERN}
ambiguous:        {FRAMEWORK_SPECIFIC_AMBIGUOUS_PATTERN}
not_interactable: {FRAMEWORK_SPECIFIC_NOT_INTERACTABLE_PATTERN}
stale_reference:  {FRAMEWORK_SPECIFIC_STALE_REFERENCE_PATTERN}
```

### Resolution Strategy Template

1. **Verify element exists** -- Use browser exploration (active by default when app accessible) to confirm the element is present on the page at the expected state
2. **Check selector specificity** -- Evaluate the current selector against the selector priority strategy defined in the framework reference; upgrade to a more resilient selector if possible
3. **Check timing** -- The element may not have rendered yet; this may actually be a timing issue (E2) disguised as a selector error
4. **Check visibility** -- The element may be hidden behind an overlay, loading spinner, or modal; wait for the blocking element to disappear
5. **Fall back to more specific selector** -- Use the selector priority hierarchy from the framework reference to choose a more targeted selector

### Default Classification

- **Category 1 (Test Bug)**: Test targets wrong element, uses fragile selector, or does not account for dynamic rendering
- **Category 2 (App Bug)**: Element was intentionally removed or renamed in the application -- test correctly identifies a regression
- **Category 3 (Environment)**: Rare; possible if element rendering depends on external data that is unavailable

---

## E2: Timing Errors

**Subcategory**: 1g
**Description**: Operation timed out waiting for an element, condition, or navigation to complete. Includes race conditions where actions execute before the page is ready.

### Generic Symptoms

- Timeout exceeded waiting for element to appear or become actionable
- Test timeout exceeded (overall test duration limit)
- Race condition: action performed before page finished rendering or transitioning
- Navigation interrupted by concurrent page activity

### Pattern Templates

```
timeout:    {FRAMEWORK_SPECIFIC_TIMEOUT_PATTERN}
race:       {FRAMEWORK_SPECIFIC_RACE_CONDITION_PATTERN}
```

### Resolution Strategy Template

1. **Diagnostic snapshot** -- When browser exploration is active, snapshot the page and check if the waited-on element exists in the DOM. If the element is not found, this is likely a misclassified selector issue (E1); reclassify and fix the selector instead of the wait strategy.
2. **Add explicit wait** -- Use the assertion-based or event-based wait pattern from the framework reference; never use fixed delays
3. **Increase scope of wait** -- If waiting for element visibility, also wait for any preceding navigation or network activity to complete
4. **Check for async data loading** -- The element may depend on an API call; wait for the network response before asserting element state
5. **Review test isolation** -- Ensure test does not depend on state from a previous test that may not have completed
6. **Adjust timeout if appropriate** -- If the operation legitimately takes longer (e.g., file upload, heavy computation), increase the specific timeout rather than adding a sleep

### Default Classification

- **Category 1 (Test Bug)**: Test does not wait long enough or uses incorrect wait strategy
- **Category 2 (App Bug)**: Application is genuinely slow or has a performance regression
- **Category 3 (Environment)**: CI environment is slower than local; resource contention causes timeouts

---

## E3: Navigation Errors

**Subcategory**: 1h
**Description**: Page failed to load, URL does not match expected value, or navigation enters a redirect loop.

### Generic Symptoms

- Page load failure (connection refused, DNS resolution failed)
- URL mismatch (expected URL differs from actual URL after navigation)
- Redirect loop (too many redirects)
- Navigation interrupted or aborted

### Pattern Templates

```
load_failure: {FRAMEWORK_SPECIFIC_LOAD_FAILURE_PATTERN}
url_mismatch: {FRAMEWORK_SPECIFIC_URL_MISMATCH_PATTERN}
redirect:     {FRAMEWORK_SPECIFIC_REDIRECT_PATTERN}
```

### Resolution Strategy Template

1. **Verify application is running** -- Check that the base URL is accessible; if using a dev server, ensure it has started before tests run
2. **Check URL correctness** -- Verify the test navigates to the correct route; account for base URL prefix, trailing slashes, and query parameters
3. **Snapshot actual page** -- When browser exploration is active, snapshot the page at the actual URL to confirm what the user sees (login redirect, error page, correct page with wrong URL pattern)
4. **Add navigation wait** -- After triggering navigation, wait for the new URL or page load event before asserting
5. **Check authentication state** -- Redirects to login pages are common when auth state is not properly configured for the test
6. **Check for SPA routing** -- Single-page applications may not trigger full page loads; use framework-specific SPA navigation detection

### Default Classification

- **Category 1 (Test Bug)**: Test navigates to wrong URL, does not wait for navigation, or lacks proper auth setup
- **Category 2 (App Bug)**: Application routing is broken, redirect logic has a bug
- **Category 3 (Environment)**: Application server is not running, network is unavailable, port conflict

---

## E4: Network/Mock Errors

**Subcategory**: 1i
**Description**: API request returned unexpected response, required mock is missing, or CORS policy blocks the request.

### Generic Symptoms

- API response does not match expected data (status code, body, headers)
- Network request was not intercepted by a mock (request went to real server or failed)
- CORS error blocking cross-origin request
- Network request failed entirely (connection error during API call)

### Pattern Templates

```
unexpected_response: {FRAMEWORK_SPECIFIC_UNEXPECTED_RESPONSE_PATTERN}
missing_mock:        {FRAMEWORK_SPECIFIC_MISSING_MOCK_PATTERN}
cors:                {FRAMEWORK_SPECIFIC_CORS_PATTERN}
```

### Resolution Strategy Template

1. **Add or fix API mock** -- Use the framework-specific mocking/interception API to intercept the failing request and return expected data
2. **Verify mock route pattern** -- Ensure the mock URL pattern matches the actual request URL (check path, query parameters, wildcards)
3. **Check response format** -- Verify mock returns correct status code, content type, and response body structure
4. **Check CORS configuration** -- If testing against a real server, ensure CORS headers are configured for the test origin
5. **Verify network state** -- Ensure previous test cleanup did not leave stale mocks or route handlers active

### Default Classification

- **Category 1 (Test Bug)**: Test missing required mock, mock returns wrong data, or mock pattern does not match request
- **Category 2 (App Bug)**: Application makes unexpected API call, sends malformed request, or fails to handle error responses
- **Category 3 (Environment)**: External API is down, network partition, DNS failure

---

## E5: Browser Errors

**Subcategory**: 1j
**Description**: Browser crashed, WebSocket connection to browser lost, or browser exhausted available resources (memory, handles).

### Generic Symptoms

- Browser process crashed or was killed
- WebSocket connection to browser disconnected
- Browser ran out of memory or exceeded resource limits
- Browser context or page was unexpectedly closed

### Pattern Templates

```
crash:      {FRAMEWORK_SPECIFIC_CRASH_PATTERN}
disconnect: {FRAMEWORK_SPECIFIC_DISCONNECT_PATTERN}
resource:   {FRAMEWORK_SPECIFIC_RESOURCE_PATTERN}
```

### Resolution Strategy Template

1. **Check browser installation** -- Verify the framework-specific browser binaries are correctly installed
2. **Check resource usage** -- Monitor memory and CPU during test execution; reduce parallelism if needed
3. **Isolate the test** -- Run the failing test in isolation to determine if resource exhaustion is caused by cumulative test execution
4. **Check for browser-specific issues** -- Some frameworks support multiple browser engines; the error may be browser-specific
5. **Restart browser context** -- Ensure each test (or test suite) starts with a fresh browser context to prevent resource leaks

### Default Classification

- **Category 1 (Test Bug)**: Rare; test may create excessive browser contexts or fail to clean up resources
- **Category 2 (App Bug)**: Rare; application may have memory leaks that crash the browser
- **Category 3 (Environment)**: Most common classification. Browser not installed, CI resource limits, Docker memory constraints

---

## E6: UI Assertion Errors

**Subcategory**: 1k
**Description**: UI state does not match expected values. Element text, visibility, attribute, or count differs from what the test asserts.

### Generic Symptoms

- Expected text content does not match actual text
- Element expected to be visible but is hidden (or vice versa)
- Element attribute (class, href, value) does not match expected value
- Expected number of elements does not match actual count

### Pattern Templates

```
text_mismatch:       {FRAMEWORK_SPECIFIC_TEXT_MISMATCH_PATTERN}
visibility_mismatch: {FRAMEWORK_SPECIFIC_VISIBILITY_MISMATCH_PATTERN}
attribute_mismatch:  {FRAMEWORK_SPECIFIC_ATTRIBUTE_MISMATCH_PATTERN}
count_mismatch:      {FRAMEWORK_SPECIFIC_COUNT_MISMATCH_PATTERN}
```

### Resolution Strategy Template

1. **Verify expected values** -- Confirm the test asserts the correct expected value; dynamic content (dates, generated IDs) needs flexible matching
2. **Check for partial matches** -- If expecting exact text, consider using "contains" assertion instead for content that may include extra whitespace or formatting
3. **Check element state** -- The element may be present but in an unexpected state (loading, disabled, collapsed); add a wait for the expected state
4. **Check test data** -- If the assertion depends on seeded data, verify the data setup completed before the assertion
5. **Use browser exploration** (active by default) -- Snapshot the page to verify the asserted element exists; if the element is not found, this may be a misclassified selector issue (E1). If found, inspect the actual content to compare against expected values

### Default Classification

- **Category 1 (Test Bug)**: Test asserts wrong expected value, does not account for dynamic content, or assertion is too strict/lenient
- **Category 2 (App Bug)**: Application renders incorrect content, has a display bug, or regression in UI behavior
- **Category 3 (Environment)**: Rare; possible if UI depends on locale, timezone, or feature flags that differ between environments

---

## Classification Decision Flow

When the validate-agent encounters a failure in an E2E test, it follows this decision flow:

```
1. Load framework-specific error patterns from skills/e2e/frameworks/{framework}.md

2. Match failure output against E2E patterns (in order):
   a. E1 patterns (selector) -> subcategory 1f
   b. E2 patterns (timing) -> subcategory 1g
   c. E3 patterns (navigation) -> subcategory 1h
   d. E4 patterns (network/mock) -> subcategory 1i
   e. E5 patterns (browser) -> subcategory 1j
   f. E6 patterns (UI assertion) -> subcategory 1k

3. If no E2E pattern matches, fall through to standard subcategories:
   a. Check 1a-1e patterns (import, fixture, assertion, mock, async)
   b. If still no match, use generic failure analysis

4. Determine top-level category:
   a. Check .dante/e2e-knowledge/known-issues.md for matching symptom
      -> If found, use stored category and confidence
   b. Apply E5 -> Category 3 heuristic (browser errors are usually environment)
   c. Check iteration history (same test passed before?)
      -> If yes, likely Category 1 (test changed) or Category 2 (app changed)
   d. Check failure breadth (multiple unrelated tests fail same way?)
      -> If yes, likely Category 3 (environment)
   e. Default to Category 1 (test bug) as most actionable

5. Flag novel patterns for knowledge capture
```

## Pattern Template Usage

Framework reference files provide concrete regex patterns that fill in the templates above. Example for a hypothetical framework:

```markdown
# In skills/e2e/frameworks/{framework}.md:

## Error Patterns

### E1 (Selector)
not_found: /specific regex for this framework's "not found" message/
ambiguous: /specific regex for this framework's "ambiguous match" message/
not_interactable: /specific regex for this framework's "not interactable" message/
stale_reference: /specific regex for this framework's "stale reference" message/

### E2 (Timing)
timeout: /specific regex for this framework's timeout message/
race: /specific regex for this framework's race condition message/

... and so on for E3-E6
```

The validate-agent loads these patterns at runtime and applies them against the test output to classify failures.

---

**Last Updated**: 2026-02-16
**Status**: Phase 1 - Universal error taxonomy defined
**Next**: Framework-specific error patterns in framework reference files
