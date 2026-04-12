# Cypress Framework Reference

**Status**: Detection markers defined. Full implementation planned.

**Version**: 0.1.0 (stub)
**Framework**: Cypress
**Language**: JavaScript / TypeScript
**Category**: E2E Testing
**Purpose**: Framework-specific reference for Cypress E2E test authoring within Dante

## Overview

This file is the Level 2 framework-specific reference for Cypress. It follows the two-level architecture defined in `skills/e2e/SKILL.md`: agents load the generic E2E contract (Level 1), then load this file (Level 2) for Cypress-specific selector APIs, wait patterns, error regex, fix strategies, and CLI workflows.

Currently, only the detection markers section is implemented. Detection markers are comprehensive enough to support the framework detection pipeline (`skills/framework-detection/e2e-frameworks.md`). All other sections contain placeholder headings with content planned for future implementation.

## Detection Markers

Detection markers enable the framework detection pipeline to identify Cypress projects with high confidence. Each marker type carries a detection weight used in weighted confidence scoring.

### Config Files (weight: 10)

Config files are the strongest detection signal for Cypress.

| Config File | Version | Notes |
|---|---|---|
| `cypress.config.js` | Cypress 10+ | Current standard config (JavaScript) |
| `cypress.config.ts` | Cypress 10+ | Current standard config (TypeScript) |
| `cypress.config.mjs` | Cypress 10+ | ES module config |
| `cypress.config.cjs` | Cypress 10+ | CommonJS config |
| `cypress.json` | Cypress 9 and earlier | Legacy config format (deprecated in v10) |

### Dependencies (weight: 8)

Package dependency signals in `package.json`.

| Dependency | Location | Notes |
|---|---|---|
| `cypress` | `devDependencies` in `package.json` | Primary dependency; most Cypress projects list this |
| `cypress` | `dependencies` in `package.json` | Less common but valid |

### Import Patterns (weight: 3)

Import and reference patterns found in test source files.

| Pattern | Context | Notes |
|---|---|---|
| `/// <reference types="cypress" />` | Triple-slash directive at top of `.ts`/`.js` files | TypeScript type reference; strong Cypress signal |
| `/// <reference types="Cypress" />` | Case variant | Some projects use capitalized form |
| `import 'cypress'` | ES module import | Less common but valid |
| `require('cypress')` | CommonJS require | Found in plugin/config files |
| `from 'cypress'` | Partial import match | Matches `import { ... } from 'cypress'` |

### Code Patterns (weight: 5)

Runtime code patterns characteristic of Cypress test files.

| Pattern | Description | Regex |
|---|---|---|
| `cy.visit()` | Navigate to a URL | `cy\.visit\s*\(` |
| `cy.get()` | Query DOM elements | `cy\.get\s*\(` |
| `cy.contains()` | Find element by text content | `cy\.contains\s*\(` |
| `.should()` | Assertion chaining | `\.should\s*\(` |
| `cy.intercept()` | Network request interception | `cy\.intercept\s*\(` |
| `cy.request()` | HTTP request (API testing) | `cy\.request\s*\(` |
| `cy.wait()` | Wait for alias or time | `cy\.wait\s*\(` |
| `cy.fixture()` | Load fixture data | `cy\.fixture\s*\(` |
| `cy.session()` | Session caching (Cypress 12+) | `cy\.session\s*\(` |
| `cy.origin()` | Cross-origin testing (Cypress 12+) | `cy\.origin\s*\(` |
| `describe(` | Test suite declaration (shared with Mocha) | Context-dependent; stronger when combined with `cy.*` |
| `it(` | Test case declaration (shared with Mocha) | Context-dependent; stronger when combined with `cy.*` |
| `before(` / `beforeEach(` | Test hooks (shared with Mocha) | Context-dependent |

### File Patterns

Directory and file naming conventions that indicate Cypress test structure.

| Pattern | Description |
|---|---|
| `cypress/e2e/*.cy.ts` | TypeScript E2E test files (Cypress 10+ convention) |
| `cypress/e2e/*.cy.js` | JavaScript E2E test files (Cypress 10+ convention) |
| `cypress/e2e/**/*.cy.ts` | Nested TypeScript E2E test files |
| `cypress/e2e/**/*.cy.js` | Nested JavaScript E2E test files |
| `cypress/integration/*.spec.ts` | Legacy test location (Cypress 9 and earlier) |
| `cypress/integration/*.spec.js` | Legacy test location (Cypress 9 and earlier) |
| `cypress/support/commands.ts` | Custom command definitions |
| `cypress/support/commands.js` | Custom command definitions (JS) |
| `cypress/support/e2e.ts` | E2E support file (Cypress 10+) |
| `cypress/support/e2e.js` | E2E support file (Cypress 10+, JS) |
| `cypress/support/index.ts` | Legacy support file (Cypress 9) |
| `cypress/support/index.js` | Legacy support file (Cypress 9, JS) |
| `cypress/fixtures/` | Test fixture data directory |
| `cypress/plugins/` | Plugin files (legacy, pre-Cypress 10) |

### Detection Confidence Thresholds

| Condition | Confidence |
|---|---|
| Config file present + `cypress` in dependencies | >= 0.95 |
| Config file present only | >= 0.80 |
| `cypress` in dependencies only | >= 0.70 |
| Code patterns + file patterns (no config/deps) | >= 0.50 |
| File patterns only | >= 0.30 |

## API Mapping

Not yet implemented. Full implementation planned for future release.

This section will map generic E2E concepts to Cypress-specific APIs:

- Selector priority strategy (e.g., `[data-cy]` > `cy.contains()` > `cy.get('css')`)
- Wait strategy hierarchy (Cypress auto-retry assertions, `cy.intercept()` + `cy.wait()`)
- Assertion patterns (`.should('be.visible')`, `.should('have.text', ...)`)
- Navigation patterns (`cy.visit()`, `cy.url()`)
- Network mocking patterns (`cy.intercept()`)

## Error Patterns

Not yet implemented. Full implementation planned for future release.

This section will provide framework-specific regex patterns that fill the pattern templates defined in `skills/e2e/error-classification.md` for each error category (E1-E6):

- E1 (Selector): Timed out retrying, element not found, multiple elements
- E2 (Timing): Cypress command timeout, assertion retry timeout
- E3 (Navigation): Page load timeout, cross-origin errors
- E4 (Network): `cy.intercept()` mismatch, unexpected request
- E5 (Browser): Browser crash, Electron/Chrome failure
- E6 (UI Assertion): `.should()` assertion failures

## Fix Strategies

Not yet implemented. Full implementation planned for future release.

This section will provide Cypress-specific fix strategies per error category (E1-E6), following the resolution strategy templates in `skills/e2e/error-classification.md`:

- E1 (Selector): Use `data-cy` attributes, fall back to `cy.contains()`, avoid brittle CSS selectors
- E2 (Timing): Leverage Cypress auto-retry, use `cy.intercept()` + `cy.wait('@alias')` for network-dependent waits
- E3 (Navigation): Use `cy.url().should('include', ...)` after navigation actions
- E4 (Network): Use `cy.intercept()` for API stubbing and response mocking
- E5 (Browser): Retry configuration, memory management
- E6 (UI Assertion): Update `.should()` expected values, verify selector targets correct element

## CLI Workflows

Not yet implemented. Full implementation planned for future release.

This section will define Cypress CLI tool workflows for:

- Test execution: `npx cypress run --spec {path} --reporter spec`
- Interactive mode: `npx cypress open` (browser exploration)
- Headed execution: `npx cypress run --headed`
- Browser selection: `npx cypress run --browser chrome`
- Record/dashboard: `npx cypress run --record --key {key}`
- Component testing: `npx cypress run --component`

## Config Parsing

Not yet implemented. Full implementation planned for future release.

This section will define how to extract configuration from Cypress config files:

- `baseUrl` -- application URL for `cy.visit('/')`
- `specPattern` -- test file glob pattern (replaces `testFiles` in Cypress 10+)
- `supportFile` -- path to support file
- `fixturesFolder` -- path to fixture data
- `viewportWidth` / `viewportHeight` -- default viewport dimensions
- `defaultCommandTimeout` -- default timeout for Cypress commands
- `retries` -- retry configuration (run mode and open mode)
- `env` -- environment variables
- `e2e.setupNodeEvents` -- Node event listeners (Cypress 10+)

## Best Practices

Not yet implemented. Full implementation planned for future release.

This section will document Cypress-specific best practices for E2E test authoring:

- Custom commands for reusable interactions
- `cy.session()` for authentication state caching
- `cy.intercept()` for deterministic network behavior
- Avoiding `cy.wait(ms)` fixed delays in favor of assertion-based waits
- Test isolation via `testIsolation: true` (Cypress 12+)
- Cross-origin handling via `cy.origin()` (Cypress 12+)
- Cypress best practices for selector resilience (`data-cy` attributes)
- Fixture management for test data

## References

- Generic E2E contract: `skills/e2e/SKILL.md`
- Error classification: `skills/e2e/error-classification.md`
- Knowledge management: `skills/e2e/knowledge-management.md`
- Browser exploration: `skills/e2e/browser-exploration.md`
- Framework detection: `skills/framework-detection/e2e-frameworks.md`
- Cypress documentation: https://docs.cypress.io

---

**Last Updated**: 2026-02-16
**Status**: Stub -- Detection markers defined. Full implementation planned.
**Next**: Full Cypress implementation (API mapping, error patterns, fix strategies, CLI workflows, config parsing, best practices)
