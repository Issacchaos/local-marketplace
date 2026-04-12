---
language: typescript
framework: playwright
test_type: e2e
description: Example E2E analysis output for a TypeScript project using Playwright
---

# Example E2E Analysis: TypeScript/Playwright

This example demonstrates the expected analysis output format for an E2E testing project using Playwright with TypeScript.

---

## Analysis Summary

**Project**: example-ecommerce
**Language**: `typescript`
**Framework**: `playwright` (Confidence: 0.95)
**Test Type**: `e2e`
**Base URL**: `http://localhost:3000`
**E2E Config**: `playwright.config.ts`
**Total Source Files**: 24
**Existing E2E Test Files**: 2
**E2E Knowledge Loaded**: true
**Browser Exploration**: disabled (app not accessible at http://localhost:3000)

---

## Test Targets

- **User Login Flow** [Priority: Critical]
  - Entry Point: /login
  - Steps: Navigate to login -> Enter email and password -> Click submit -> Verify redirect to /dashboard
  - Coverage: Not Covered
  - Reason: Core authentication flow, handles sensitive credentials, gateway to all authenticated features

- **Product Checkout Flow** [Priority: Critical]
  - Entry Point: /cart
  - Steps: View cart -> Enter shipping address -> Select payment method -> Confirm order -> Verify confirmation page
  - Coverage: Not Covered
  - Reason: Core business flow, handles payment data, highest business value

- **Product Search and Filter Flow** [Priority: High]
  - Entry Point: /products
  - Steps: Navigate to products -> Enter search term -> Apply category filter -> Verify filtered results
  - Coverage: Partial (basic search tested in search.spec.ts, filtering not covered)
  - Reason: Primary user interaction for product discovery

- **User Registration Flow** [Priority: High]
  - Entry Point: /register
  - Steps: Navigate to register -> Fill registration form -> Submit -> Verify welcome page
  - Coverage: Not Covered
  - Reason: User onboarding flow, form validation, email verification

- **Dashboard Navigation Flow** [Priority: Medium]
  - Entry Point: /dashboard
  - Steps: Login -> Navigate between dashboard sections (orders, profile, settings) -> Verify content loads
  - Coverage: Covered (dashboard.spec.ts)
  - Reason: Navigation verification, already has basic coverage

- **Error Page Flow** [Priority: Low]
  - Entry Point: /nonexistent
  - Steps: Navigate to invalid URL -> Verify 404 page displays -> Click "Go Home" -> Verify redirect
  - Coverage: Not Covered
  - Reason: Edge case flow, low business impact

---

## Priority Summary

- Critical: 2 flows
- High: 2 flows
- Medium: 1 flow
- Low: 1 flow

Total: 6 user flows identified

---

## E2E Configuration

Framework: playwright
Config File: playwright.config.ts
Base URL: http://localhost:3000
Test Directory: tests/e2e/
Browsers: chromium, firefox
Viewport: 1280x720
Timeouts: test=30s, assertion=5s
Web Server: npm run dev (port 3000)

---

## Selector Discovery

Existing Conventions:
- data-testid attributes used in 2 existing test files
- No page object model detected
- Existing tests use getByRole and getByTestId selectors

Browser Exploration: disabled (app not accessible at http://localhost:3000)
- Reason: app not accessible at http://localhost:3000
- Selectors inferred from static analysis

> **When active** (app running at base_url), this section would instead show:
> ```
> Browser Exploration: active (app accessible at http://localhost:3000)
> - Pages Explored: 4
> - Test IDs Found: 12
> - Interactive Elements: 28
> - Key Selectors: [data-testid="login-form"], [data-testid="cart-checkout-btn"], getByRole('navigation')
> ```

---

## Coverage Gaps

No Coverage (4 flows):
- Login Flow: No E2E tests found
- Checkout Flow: No E2E tests found
- Registration Flow: No E2E tests found
- Error Page Flow: No E2E tests found

Partial Coverage (1 flow):
- Product Search: Basic search tested in search.spec.ts, filtering and pagination not tested

Well Covered (1 flow):
- Dashboard Navigation: Covered in dashboard.spec.ts

---

## Known Patterns

Knowledge Base: Loaded

Known Issues: 2 entries
  - E2 (Timing): "Product list renders after async API call, requires waitFor"
  - E1 (Selector): "Multiple submit buttons on checkout page, use specific form context"

Project Patterns:
  - Auth: Session-based auth with JWT tokens; test account: test@example.com / password123
  - Navigation: React Router SPA with client-side routing
  - Components: data-testid follows {feature}-{component}-{action} convention
  - Data Setup: API seeding via /api/test/seed endpoint in beforeEach

---

## Recommendations

1. **Start with Login and Checkout flows**: Critical priority, highest business value, no existing coverage
2. **Establish Auth Fixture**: Create reusable storageState fixture using test account credentials (see project patterns)
3. **Follow Existing Selector Convention**: Use data-testid with {feature}-{component}-{action} naming (see project patterns)
4. **Address Known Timing Issue**: Use waitFor patterns for product list rendering (known issue E2)
5. **Start App for Browser Exploration**: Run the dev server (`npm run dev`) before analysis to enable automatic browser exploration for selector discovery on checkout page (known multiple submit buttons)
