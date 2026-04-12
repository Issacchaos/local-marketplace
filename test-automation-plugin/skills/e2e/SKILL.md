---
name: e2e-testing
description: Generic E2E web test authoring contracts. Defines universal error taxonomy (E1-E6), agent behavior contracts for all 5 agents when test_type=e2e, knowledge management conventions, and browser exploration interface. Framework-agnostic -- does NOT define selector rankings, wait hierarchies, fix strategies, or error regex patterns. Those belong in framework-specific reference files under skills/e2e/frameworks/.
user-invocable: false
---

# E2E Testing Skill

**Version**: 1.0.0
**Category**: Testing
**Languages**: Cross-language (E2E frameworks span languages)
**Purpose**: Define universal contracts for E2E web test authoring that all agents reference when `test_type=e2e`

## Overview

The E2E Testing Skill provides the generic contract layer for end-to-end web test authoring within Dante. When framework detection identifies an E2E framework (Playwright, Cypress, Selenium, etc.) as primary and sets `test_type=e2e`, all five agents reference this skill for universal E2E concepts: error taxonomy, agent behavior expectations, knowledge management, and browser exploration.

This skill is **Level 1** of a two-level architecture:

- **Level 1 (this file)**: Generic E2E contract -- defines WHAT E2E testing requires (categories, contracts, conventions, interfaces)
- **Level 2 (`skills/e2e/frameworks/{framework}.md`)**: Framework-specific references -- defines HOW (selector APIs, wait patterns, error regex, fix strategies, CLI workflows)

Agents always load Level 1. They load Level 2 based on the detected framework. Adding a new E2E framework means creating one framework reference file -- no agent modifications required.

## Skill Interface

### Input

```yaml
project_path: Path to the project root directory
e2e_framework: Detected E2E framework name (e.g., "playwright", "cypress", "selenium")
test_type: "e2e"
base_url: Application base URL extracted from framework config (e.g., "http://localhost:3000")
e2e_config_path: Path to framework config file (e.g., "playwright.config.ts")
```

### Output

```yaml
e2e_test_targets: List of user flow test targets identified during analysis
  - flow_name: Name of the user flow (e.g., "Login flow", "Checkout flow")
    entry_point: Starting URL or route
    steps: High-level description of flow steps
    priority: Importance ranking (critical, high, medium, low)
selector_strategies: Loaded from framework reference file (not defined here)
known_patterns: Loaded from .dante/e2e-knowledge/ if present
e2e_knowledge_loaded: Boolean indicating whether project knowledge was found and loaded
```

## E2E Error Taxonomy

E2E test failures fall into 6 universal categories (E1-E6). These categories are framework-agnostic -- every E2E framework can produce errors in each category. The specific error messages and regex patterns differ per framework and are defined in `skills/e2e/frameworks/{framework}.md`.

Each E2E error category maps to a validate-agent subcategory (1f-1k), extending the existing unit test subcategories (1a-1e).

| Category | Name | Subcategory | Description |
|----------|------|-------------|-------------|
| E1 | Selector Errors | 1f | Element not found, ambiguous match, stale reference, not interactable |
| E2 | Timing Errors | 1g | Timeout waiting for element/condition, race condition between actions |
| E3 | Navigation Errors | 1h | Page load failure, URL mismatch, redirect loop |
| E4 | Network/Mock Errors | 1i | Unexpected API response, missing mock, CORS failure |
| E5 | Browser Errors | 1j | Browser crash, WebSocket disconnect, resource exhaustion |
| E6 | UI Assertion Errors | 1k | Expected vs actual UI state mismatch (text, visibility, attribute) |

### Subcategory Mapping

The validate-agent uses subcategories 1a-1e for unit test errors. When `test_type=e2e`, subcategories 1f-1k extend the taxonomy:

```
Category 1 (Test Bug) Subcategories:
  Unit Test Errors (existing):
    1a: Import/Syntax Error
    1b: Fixture/Setup Error
    1c: Assertion Logic Error
    1d: Mock/Stub Error
    1e: Async/Timing Error

  E2E Test Errors (new, when test_type=e2e):
    1f: Selector Issue (E1) -- element targeting problem in test code
    1g: Timing Issue (E2) -- insufficient or incorrect wait strategy in test
    1h: Navigation Issue (E3) -- incorrect URL or navigation expectation in test
    1i: Network/Mock Issue (E4) -- missing or misconfigured API mock in test
    1j: Browser Issue (E5) -- usually escalates to Category 3 (Environment)
    1k: UI Assertion Issue (E6) -- incorrect expected value in test assertion
```

### Classification Rules

Each E2E error is classified into one of three top-level categories, consistent with existing Dante error categorization:

- **Category 1 (Test Bug)**: The test code is wrong. Selector targets wrong element, wait is insufficient, mock is misconfigured, assertion expects wrong value. Subcategories 1f-1k apply.
- **Category 2 (Application Bug)**: The application behavior is unexpected. UI does not render expected content, navigation leads to wrong page, API returns unexpected data. The test correctly identifies a real defect.
- **Category 3 (Environment Issue)**: Infrastructure problem. Browser fails to launch, application server is down, network is unreachable, resource exhaustion. E5 (Browser Errors) usually maps here.

Classification heuristic:
1. If the error matches a known issue in `.dante/e2e-knowledge/known-issues.md`, use the stored classification
2. If the error is E5 (Browser), default to Category 3 unless evidence suggests otherwise
3. If the same test passed on a previous iteration, likely Category 1 (test code changed) or Category 2 (app changed)
4. If multiple unrelated tests fail with the same pattern, likely Category 3 (environment)
5. Otherwise, default to Category 1 (test bug) as the most actionable classification

See [error-classification.md](./error-classification.md) for the complete error taxonomy reference.

## Agent Behavior Contracts

When `test_type=e2e`, each agent adapts its behavior. The contracts below describe WHAT each agent does differently -- the specific APIs, patterns, and strategies come from the framework reference file.

### Analyze Agent

When `test_type=e2e`, the analyze-agent shifts from function-level analysis to user-flow analysis:

1. **Load E2E skill** -- Read this file (`skills/e2e/SKILL.md`) for generic contracts
2. **Load framework reference** -- Read `skills/e2e/frameworks/{framework}.md` for framework-specific details
3. **Parse E2E config** -- Extract base URL, test directory, browser configurations, web server config from the framework config file (parsing rules defined in framework reference)
4. **Check app availability** -- Probe `base_url` to determine if browser exploration should activate (see [browser-exploration.md](./browser-exploration.md) App Availability Check)
5. **Browser exploration (default when app accessible)** -- When active, snapshot key pages and discover selectors; when disabled, skip to step 6 (see [browser-exploration.md](./browser-exploration.md))
6. **Load project knowledge** -- Check for `.dante/e2e-knowledge/` directory; load `known-issues.md` and `project-patterns.md` if present (see [knowledge-management.md](./knowledge-management.md))
7. **Lightweight existing test scan** -- Identify fixture patterns and test organization; when exploration is active, skip selector extraction (selectors come from browser)
8. **Identify test targets** -- Target **user flows** (login, checkout, navigation, form submission), not individual functions or methods; browser exploration is the primary source when active

**Output additions**: `test_type: "e2e"`, `base_url`, `page_structures` (from snapshots if available), `e2e_knowledge_loaded: true/false`, `e2e_config` (parsed framework config), `browser_exploration: active/disabled`, `browser_exploration_reason`

### Write Agent

When `test_type=e2e`, the write-agent generates flow-based E2E tests:

1. **Load E2E template** -- Select template based on framework: `skills/templates/{language}-{framework}-template.md`
2. **Organize by flow** -- Tests are organized by user flow or feature, NOT by source file
3. **Apply selector strategy** -- Use the selector priority defined in the framework reference file; the generic contract does not prescribe selector ranking
4. **Apply wait strategy** -- Use the wait hierarchy defined in the framework reference file; the generic contract does not prescribe wait patterns
5. **Test naming** -- Test names describe user-visible behavior: `"user can log in with valid credentials"`, `"shopping cart updates when item is added"`
6. **Test structure** -- E2E tests follow Navigate -> Interact -> Assert pattern (distinct from unit test Arrange-Act-Assert)
7. **Browser exploration for selectors** -- Primary source when active: navigate to each page, snapshot, extract selectors from live DOM. Static inference (existing tests, source code, project patterns) is the fallback when exploration is disabled.

### Execute Agent

When `test_type=e2e`, the execute-agent manages browser-based test execution:

1. **Browser installation check** -- Verify framework-specific browser dependencies are installed (check method defined in framework reference)
2. **Application availability** -- If no `webServer` config in framework config, verify `base_url` is accessible before running tests
3. **Timeout adjustment** -- Default 5 minutes for E2E tests (vs 2 minutes for unit tests) to account for browser startup and navigation
4. **Command construction** -- Build the test execution command from the framework reference (command template, reporter flag, file arguments)
5. **Result parsing** -- Route output to the framework-specific parser: `skills/result-parsing/parsers/{framework}-parser.md`

### Validate Agent

When `test_type=e2e`, the validate-agent applies the E2E error taxonomy:

1. **Load error taxonomy** -- Read [error-classification.md](./error-classification.md) for category definitions and classification rules
2. **Load framework patterns** -- Read error regex patterns from `skills/e2e/frameworks/{framework}.md`
3. **Match against E2E categories first** -- Check E2E patterns (E1-E6) before falling through to standard unit test subcategories (1a-1e); E2E patterns are more specific
4. **Cross-reference knowledge base** -- Check `.dante/e2e-knowledge/known-issues.md` for matching symptoms; flag known vs novel issues
5. **Classify top-level category** -- Apply classification rules (Category 1 / 2 / 3) per the heuristic above
6. **Flag novel patterns** -- If a failure does not match any known issue, flag it as novel for potential knowledge capture by the fix-agent

### Fix Agent

When `test_type=e2e`, the fix-agent applies E2E-aware resolution strategies:

1. **Consult knowledge base** -- Read `.dante/e2e-knowledge/known-issues.md`; if current failure matches a known issue (by symptom + category), apply the stored resolution first (highest confidence match wins)
2. **Load fix strategies** -- Read framework-specific fix strategies from `skills/e2e/frameworks/{framework}.md` for the relevant error category
3. **Apply framework-specific fix** -- Use the selector, wait, navigation, or mocking patterns defined in the framework reference
4. **Browser exploration (default for E1, E2, E3, E6)** -- Use browser exploration by default when app is accessible to: discover correct selectors for E1, diagnose misclassified selector issues in E2/E3/E6 timeouts and assertions, and verify page state for navigation errors; fall back to heuristic-based fix when exploration is disabled
5. **Capture novel resolutions** -- After a successful fix of a novel issue, append an entry to `.dante/e2e-knowledge/known-issues.md` with symptom, root cause, resolution, framework, category, and confidence (see [knowledge-management.md](./knowledge-management.md))

## Framework Content Loading Path

When `test_type=e2e`, agents load content in this order:

```
Step 1: Framework Detection
  -> Detects E2E framework, sets test_type=e2e, framework={name}
  -> Source: skills/framework-detection/e2e-frameworks.md

Step 2: Generic E2E Skill (this file)
  -> Agent reads skills/e2e/SKILL.md
  -> Provides: error taxonomy, agent contracts, conventions, references

Step 3: Framework-Specific Reference
  -> Agent reads skills/e2e/frameworks/{framework}.md
  -> Provides: selector APIs, wait patterns, error regex, fix strategies, CLI workflows

Step 4: Test Template
  -> Write-agent reads skills/templates/{language}-{framework}-template.md
  -> Provides: test file structure, fixture patterns, assertion patterns, examples

Step 5: Result Parser
  -> Execute-agent reads skills/result-parsing/parsers/{framework}-parser.md
  -> Provides: output parsing rules (pass/fail counts, failure details, retry indicators)

Step 6: Project Knowledge
  -> Agent reads .dante/e2e-knowledge/ (known-issues.md, project-patterns.md)
  -> Provides: project-specific known issues, auth flows, navigation patterns
```

## Supporting Files

This skill references three supporting documents that define detailed conventions:

- **[error-classification.md](./error-classification.md)** -- Complete E1-E6 category definitions with generic symptoms, pattern templates, resolution strategy templates, subcategory mapping, and classification rules
- **[knowledge-management.md](./knowledge-management.md)** -- Full specification of the `.dante/e2e-knowledge/` directory structure, entry format, auto-population rules, and consumption rules
- **[browser-exploration.md](./browser-exploration.md)** -- Generic browser exploration contract with capability table, agent workflow, activation rules (default-on when app accessible), and installation instructions per framework

## Explicit Constraints

The generic E2E layer (this file and its supporting files) does NOT contain:

- **Selector rankings** -- The priority of `data-testid` vs `role` vs `text` vs CSS selectors is defined per framework in `skills/e2e/frameworks/{framework}.md`
- **Wait hierarchies** -- The specific wait APIs and their precedence are defined per framework in `skills/e2e/frameworks/{framework}.md`
- **Fix strategies** -- The concrete code patterns to apply for each error category are defined per framework in `skills/e2e/frameworks/{framework}.md`
- **Error regex patterns** -- The specific regex patterns to match framework output are defined per framework in `skills/e2e/frameworks/{framework}.md`

This separation ensures that adding a new E2E framework requires only a new framework reference file and detection markers -- zero agent modifications.

## Usage in Agents

### Loading This Skill

All agents check `test_type` from the framework detection output. When `test_type=e2e`:

```markdown
1. Read this skill: skills/e2e/SKILL.md
2. Read framework reference: skills/e2e/frameworks/{framework}.md
3. Follow agent-specific contract (see Agent Behavior Contracts above)
4. Apply E2E error taxonomy when classifying failures
5. Consult/update .dante/e2e-knowledge/ as specified
```

### When NOT to Load

- When `test_type` is `"unit"` or `"integration"` -- standard agent behavior applies
- When no E2E framework is detected -- this skill is not referenced
- E2E branches activate ONLY when `test_type=e2e`; existing unit test behavior is unaffected

## References

- E2E Specification: `.sdd/specs/2026-02-13-e2e-web-test-authoring.md`
- Framework Detection: `skills/framework-detection/SKILL.md`
- Result Parsing: `skills/result-parsing/SKILL.md`
- State Management: `skills/state-management/SKILL.md`
- Test Templates: `skills/templates/SKILL.md`

---

**Last Updated**: 2026-02-25
**Status**: Phase 2 - Browser exploration default-on, agent contracts updated
**Next**: Framework-specific reference files (Playwright, Cypress stubs, Selenium stubs)
