# E2E Framework Detection

**Version**: 1.0.0
**Category**: E2E Testing (Cross-Language)
**Frameworks**: Playwright, Cypress, Selenium
**Status**: Phase 2 - Detection and Parsing

## Overview

E2E framework detection skill for identifying Playwright, Cypress, and Selenium testing frameworks in projects. Unlike language-specific detection files (e.g., `python-frameworks.md`, `javascript-frameworks.md`), this file is organized by framework rather than language because E2E frameworks span multiple languages (Selenium spans Python, Java, JavaScript, C#, Ruby; Playwright and Cypress span JavaScript and TypeScript).

When any E2E framework is detected as the primary framework, the detection output includes `test_type: "e2e"`. This signals all downstream agents to activate E2E-specific behavior branches as defined in `skills/e2e/SKILL.md`.

### Relationship to Other Detection Files

- Language-specific detection files (`python-frameworks.md`, `javascript-frameworks.md`, etc.) detect **unit test** frameworks
- This file detects **E2E test** frameworks
- Both detection paths run in parallel during framework detection
- Priority resolution (see below) determines which is primary and which is secondary

### `--type e2e` Flag

When the user passes `--type e2e` to `/test-generate` or `/test-loop`:

1. Framework detection still runs normally (all detection paths)
2. If an E2E framework is detected with any confidence >= 0.1, it becomes the primary framework regardless of unit framework confidence
3. If no E2E framework is detected, detection falls back to the standard primary framework and warns the user that no E2E framework was found
4. The `--type e2e` flag does NOT change detection weights or scoring -- it only changes the priority resolution logic

## Supported Frameworks

### 1. Playwright

**Description**: Modern E2E testing framework with auto-waiting, multi-browser support, and built-in test runner
**Official Docs**: https://playwright.dev
**Language**: TypeScript, JavaScript
**Detection Priority**: High (dedicated config file + specific dependency)
**Full Reference**: `skills/e2e/frameworks/playwright.md`

### 2. Cypress

**Description**: JavaScript-based E2E testing framework with real-time reloading and automatic waiting
**Official Docs**: https://docs.cypress.io
**Language**: JavaScript, TypeScript
**Detection Priority**: High (dedicated config file + specific dependency)
**Full Reference**: `skills/e2e/frameworks/cypress.md`

### 3. Selenium

**Description**: Cross-language browser automation framework with WebDriver protocol
**Official Docs**: https://www.selenium.dev
**Language**: Python, Java, JavaScript, C#, Ruby, Kotlin
**Detection Priority**: Medium (no standard config file; relies more on dependencies and code patterns)
**Full Reference**: `skills/e2e/frameworks/selenium.md`

## Detection Patterns

### Playwright Detection

#### 1. Configuration Files (Weight: 10)

Config files are the strongest detection signal for Playwright.

```
playwright.config.ts          # TypeScript config (most common)
playwright.config.js          # JavaScript config
playwright.config.mts         # ES module TypeScript config
playwright.config.mjs         # ES module JavaScript config
```

**Detection Logic**:
```python
config_files = [
    "playwright.config.ts",
    "playwright.config.js",
    "playwright.config.mts",
    "playwright.config.mjs",
]

for config in config_files:
    if exists(config):
        score += 10
        evidence.append(f"{config} found")
        break  # One config file is sufficient
```

#### 2. Dependencies (Weight: 8)

Package dependency signals in `package.json`.

| Dependency | Location | Notes |
|---|---|---|
| `@playwright/test` | `devDependencies` in `package.json` | Primary dependency; the test runner and assertion library |
| `@playwright/test` | `dependencies` in `package.json` | Less common but valid |
| `playwright` | `devDependencies` in `package.json` | Core library without test runner; weaker signal (weight 6) |

**Detection Logic**:
```python
if exists("package.json"):
    pkg = parse_json("package.json")
    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    if "@playwright/test" in all_deps:
        score += 8
        evidence.append("@playwright/test in package.json")
    elif "playwright" in all_deps:
        score += 6
        evidence.append("playwright in package.json (core library, no test runner)")
```

#### 3. Import Patterns (Weight: 3)

Import patterns found in test source files. Scan `.ts` and `.js` files.

| Pattern | Regex | Notes |
|---|---|---|
| `import { test, expect } from '@playwright/test'` | `from\s+['"]@playwright/test['"]` | Primary test runner import |
| `import { Page, BrowserContext } from '@playwright/test'` | `import\s+\{.*(?:Page\|BrowserContext\|Browser).*\}\s+from\s+['"]@playwright/test['"]` | Type imports for fixtures |
| `import { defineConfig, devices } from '@playwright/test'` | `defineConfig.*from\s+['"]@playwright/test['"]` | Config file import |
| `require('@playwright/test')` | `require\s*\(\s*['"]@playwright/test['"]\s*\)` | CommonJS import |

**Detection Logic**:
```python
source_files = glob("**/*.ts") + glob("**/*.js")
source_files = source_files[:50]  # Sample up to 50 files

for file in source_files:
    content = read_file(file)
    if re.search(r"from\s+['\"]@playwright/test['\"]", content):
        score += 3
        evidence.append(f"Playwright import in {file}")
        break  # One import match is sufficient
```

#### 4. Code Patterns (Weight: 5)

Runtime code patterns characteristic of Playwright test files.

| Pattern | Description | Regex |
|---|---|---|
| `test('...', async ({ page }) =>` | Playwright test declaration with page fixture | `test\s*\(\s*['"\x60].*['"\x60]\s*,\s*async\s*\(\s*\{.*page` |
| `await page.goto(` | Page navigation | `await\s+page\.goto\s*\(` |
| `await expect(...).toBeVisible(` | Playwright auto-retrying assertion | `await\s+expect\s*\(.*\)\.toBeVisible\s*\(` |
| `await page.getByTestId(` | Test ID selector | `page\.getByTestId\s*\(` |
| `await page.getByRole(` | Role-based selector | `page\.getByRole\s*\(` |
| `await page.getByLabel(` | Label-based selector | `page\.getByLabel\s*\(` |
| `await page.getByText(` | Text-based selector | `page\.getByText\s*\(` |
| `await page.locator(` | CSS/XPath locator | `page\.locator\s*\(` |
| `page.waitForURL(` | URL wait | `page\.waitForURL\s*\(` |
| `page.route(` | Network interception | `page\.route\s*\(` |

**Detection Logic**:
```python
playwright_code_patterns = [
    r"test\s*\(\s*['\"\x60].*['\"\x60]\s*,\s*async\s*\(\s*\{.*page",
    r"await\s+page\.goto\s*\(",
    r"await\s+expect\s*\(.*\)\.toBeVisible\s*\(",
    r"page\.getByTestId\s*\(",
    r"page\.getByRole\s*\(",
    r"page\.getByLabel\s*\(",
]

for file in source_files:
    content = read_file(file)
    for pattern in playwright_code_patterns:
        if re.search(pattern, content):
            score += 5
            evidence.append(f"Playwright code pattern in {file}")
            break  # One match per file
```

#### 5. File Patterns

Directory and file naming conventions that indicate Playwright test structure.

| Pattern | Description |
|---|---|
| `*.spec.ts` in configured `testDir` | TypeScript test files (Playwright convention) |
| `*.spec.js` in configured `testDir` | JavaScript test files |
| `tests/e2e/*.spec.ts` | Common E2E test directory with Playwright naming |
| `e2e/*.spec.ts` | Alternative E2E directory |
| `playwright/.auth/` | Auth storage state directory |
| `test-results/` | Default Playwright test results directory |
| `playwright-report/` | Default Playwright HTML report directory |

#### 6. Detection Confidence Thresholds

| Condition | Confidence |
|---|---|
| Config file + `@playwright/test` in dependencies | >= 0.95 |
| Config file only | >= 0.80 |
| `@playwright/test` in dependencies only | >= 0.70 |
| Import patterns + code patterns (no config/deps) | >= 0.50 |
| Code patterns only | >= 0.35 |

---

### Cypress Detection

#### 1. Configuration Files (Weight: 10)

Config files are the strongest detection signal for Cypress.

```
cypress.config.js             # Current standard config (JavaScript, Cypress 10+)
cypress.config.ts             # Current standard config (TypeScript, Cypress 10+)
cypress.config.mjs            # ES module config (Cypress 10+)
cypress.config.cjs            # CommonJS config (Cypress 10+)
cypress.json                  # Legacy config (Cypress 9 and earlier, deprecated in v10)
```

**Detection Logic**:
```python
config_files = [
    "cypress.config.js",
    "cypress.config.ts",
    "cypress.config.mjs",
    "cypress.config.cjs",
    "cypress.json",
]

for config in config_files:
    if exists(config):
        score += 10
        evidence.append(f"{config} found")
        break  # One config file is sufficient
```

#### 2. Dependencies (Weight: 8)

Package dependency signals in `package.json`.

| Dependency | Location | Notes |
|---|---|---|
| `cypress` | `devDependencies` in `package.json` | Primary dependency |
| `cypress` | `dependencies` in `package.json` | Less common but valid |

**Detection Logic**:
```python
if exists("package.json"):
    pkg = parse_json("package.json")
    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    if "cypress" in all_deps:
        score += 8
        evidence.append("cypress in package.json")
```

#### 3. Import Patterns (Weight: 3)

Import and reference patterns found in test source files.

| Pattern | Regex | Notes |
|---|---|---|
| `/// <reference types="cypress" />` | `///\s*<reference\s+types\s*=\s*["']cypress["']\s*/>` | Triple-slash directive (strong signal) |
| `/// <reference types="Cypress" />` | `///\s*<reference\s+types\s*=\s*["']Cypress["']\s*/>` | Case variant |
| `import 'cypress'` | `import\s+['"]cypress['"]` | ES module import |
| `require('cypress')` | `require\s*\(\s*['"]cypress['"]\s*\)` | CommonJS require |
| `from 'cypress'` | `from\s+['"]cypress['"]` | Partial import match |

**Detection Logic**:
```python
source_files = glob("**/*.ts") + glob("**/*.js") + glob("cypress/**/*")
source_files = source_files[:50]

for file in source_files:
    content = read_file(file)
    if re.search(r'///\s*<reference\s+types\s*=\s*["\'](?:c|C)ypress["\']\s*/>', content):
        score += 3
        evidence.append(f"Cypress type reference in {file}")
        break
```

#### 4. Code Patterns (Weight: 5)

Runtime code patterns characteristic of Cypress test files.

| Pattern | Description | Regex |
|---|---|---|
| `cy.visit()` | Navigate to URL | `cy\.visit\s*\(` |
| `cy.get()` | Query DOM elements | `cy\.get\s*\(` |
| `cy.contains()` | Find element by text | `cy\.contains\s*\(` |
| `.should()` | Assertion chaining | `\.should\s*\(` |
| `cy.intercept()` | Network interception | `cy\.intercept\s*\(` |
| `cy.request()` | HTTP request | `cy\.request\s*\(` |
| `cy.wait()` | Wait for alias or time | `cy\.wait\s*\(` |
| `cy.fixture()` | Load fixture data | `cy\.fixture\s*\(` |
| `cy.session()` | Session caching (Cypress 12+) | `cy\.session\s*\(` |
| `cy.origin()` | Cross-origin testing (Cypress 12+) | `cy\.origin\s*\(` |

**Detection Logic**:
```python
cypress_code_patterns = [
    r"cy\.visit\s*\(",
    r"cy\.get\s*\(",
    r"cy\.contains\s*\(",
    r"cy\.intercept\s*\(",
    r"\.should\s*\(",
]

for file in source_files:
    content = read_file(file)
    for pattern in cypress_code_patterns:
        if re.search(pattern, content):
            score += 5
            evidence.append(f"Cypress code pattern in {file}")
            break  # One match per file
```

#### 5. File Patterns

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
| `cypress/support/e2e.ts` | E2E support file (Cypress 10+) |
| `cypress/fixtures/` | Test fixture data directory |

#### 6. Detection Confidence Thresholds

| Condition | Confidence |
|---|---|
| Config file + `cypress` in dependencies | >= 0.95 |
| Config file only | >= 0.80 |
| `cypress` in dependencies only | >= 0.70 |
| Code patterns + file patterns (no config/deps) | >= 0.50 |
| File patterns only | >= 0.30 |

---

### Selenium Detection

Selenium is unique among E2E frameworks in that it spans multiple programming languages. Detection markers are organized by language to enable accurate identification regardless of which language binding is in use.

Selenium does NOT have a standard dedicated config file (unlike Playwright and Cypress), so its overall detection weight is lower than config-file-based frameworks. Detection relies more heavily on dependencies and code patterns.

#### 1. Configuration Files (Weight: 5)

Selenium has no standard config file. The lower weight (5 instead of 10) reflects this.

| Config File | Language | Notes |
|---|---|---|
| `conftest.py` with Selenium imports | Python | pytest conftest with Selenium fixtures (requires content check) |

Note: Selenium projects typically configure via the host test runner's config files (pytest.ini, testng.xml, etc.) rather than a dedicated Selenium config file. A bare `conftest.py` without Selenium imports does NOT count as evidence.

**Detection Logic**:
```python
# Selenium has no dedicated config file
# Check conftest.py for Selenium imports (Python projects only)
if exists("conftest.py"):
    content = read_file("conftest.py")
    if re.search(r"from\s+selenium\s+import|import\s+selenium", content):
        score += 5
        evidence.append("conftest.py with Selenium imports")
```

#### 2. Dependencies (Weight: 8)

Dependencies are the primary detection signal for Selenium due to the absence of a standard config file.

##### Python

| Dependency | Location | Notes |
|---|---|---|
| `selenium` | `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py` | Primary Python package |
| `webdriver-manager` | Any Python dependency file | Common companion package (strengthens confidence) |

##### Java

| Dependency | Location | Notes |
|---|---|---|
| `selenium-java` | `pom.xml` (`<dependency>`) | Maven projects |
| `selenium-java` | `build.gradle` / `build.gradle.kts` | Gradle projects |
| `selenium-api` | `pom.xml` or `build.gradle` | API-only dependency |
| `selenium-chrome-driver` | `pom.xml` or `build.gradle` | Chrome-specific driver |
| `selenium-support` | `pom.xml` or `build.gradle` | Support classes (WebDriverWait, etc.) |

##### JavaScript / TypeScript

| Dependency | Location | Notes |
|---|---|---|
| `selenium-webdriver` | `package.json` | Primary JS/TS package |
| `@types/selenium-webdriver` | `package.json` (`devDependencies`) | TypeScript type definitions |
| `chromedriver` | `package.json` | Chrome driver companion (strengthens confidence) |
| `geckodriver` | `package.json` | Firefox driver companion (strengthens confidence) |

##### C# / .NET

| Dependency | Location | Notes |
|---|---|---|
| `Selenium.WebDriver` | `.csproj` (`<PackageReference>`) | Primary NuGet package |
| `Selenium.Support` | `.csproj` (`<PackageReference>`) | Support classes |
| `Selenium.WebDriver` | `packages.config` | Legacy NuGet format |

##### Ruby

| Dependency | Location | Notes |
|---|---|---|
| `selenium-webdriver` | `Gemfile` | Primary Ruby gem |
| `webdrivers` | `Gemfile` | Common companion gem |

**Detection Logic**:
```python
# Python
if exists("requirements.txt"):
    content = read_file("requirements.txt")
    if "selenium" in parse_dependencies(content):
        score += 8
        evidence.append("selenium in requirements.txt")

# Java (Maven)
if exists("pom.xml"):
    content = read_file("pom.xml")
    if "selenium-java" in content or "selenium-api" in content:
        score += 8
        evidence.append("selenium-java in pom.xml")

# JavaScript
if exists("package.json"):
    pkg = parse_json("package.json")
    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    if "selenium-webdriver" in all_deps:
        score += 8
        evidence.append("selenium-webdriver in package.json")

# C#
for csproj in glob("**/*.csproj"):
    content = read_file(csproj)
    if "Selenium.WebDriver" in content:
        score += 8
        evidence.append(f"Selenium.WebDriver in {csproj}")
        break

# Ruby
if exists("Gemfile"):
    content = read_file("Gemfile")
    if "selenium-webdriver" in content:
        score += 8
        evidence.append("selenium-webdriver in Gemfile")
```

#### 3. Import Patterns (Weight: 3)

Import patterns organized by language.

##### Python

| Pattern | Regex |
|---|---|
| `from selenium import webdriver` | `from\s+selenium\s+import\s+webdriver` |
| `from selenium.webdriver.common.by import By` | `from\s+selenium\.webdriver\.common\.by\s+import\s+By` |
| `from selenium.webdriver.support.ui import WebDriverWait` | `from\s+selenium\.webdriver\.support\.ui\s+import\s+WebDriverWait` |
| `from selenium.webdriver.support import expected_conditions` | `from\s+selenium\.webdriver\.support\s+import\s+expected_conditions` |
| `import selenium` | `import\s+selenium` |

##### Java

| Pattern | Regex |
|---|---|
| `import org.openqa.selenium.*` | `import\s+org\.openqa\.selenium\.\*` |
| `import org.openqa.selenium.WebDriver` | `import\s+org\.openqa\.selenium\.WebDriver` |
| `import org.openqa.selenium.By` | `import\s+org\.openqa\.selenium\.By` |
| `import org.openqa.selenium.support.ui.WebDriverWait` | `import\s+org\.openqa\.selenium\.support\.ui\.WebDriverWait` |

##### JavaScript / TypeScript

| Pattern | Regex |
|---|---|
| `require('selenium-webdriver')` | `require\s*\(\s*['"]selenium-webdriver['"]\s*\)` |
| `from 'selenium-webdriver'` | `from\s+['"]selenium-webdriver['"]` |
| `import { Builder, By, until } from 'selenium-webdriver'` | `import\s+\{.*Builder.*\}\s+from\s+['"]selenium-webdriver['"]` |

##### C# / .NET

| Pattern | Regex |
|---|---|
| `using OpenQA.Selenium` | `using\s+OpenQA\.Selenium` |
| `using OpenQA.Selenium.Chrome` | `using\s+OpenQA\.Selenium\.Chrome` |
| `using OpenQA.Selenium.Support.UI` | `using\s+OpenQA\.Selenium\.Support\.UI` |

**Detection Logic**:
```python
# Determine project language, then apply language-specific patterns
selenium_import_patterns = {
    "python": [r"from\s+selenium\s+import", r"import\s+selenium"],
    "java": [r"import\s+org\.openqa\.selenium"],
    "javascript": [r"require\s*\(\s*['\"]selenium-webdriver", r"from\s+['\"]selenium-webdriver"],
    "csharp": [r"using\s+OpenQA\.Selenium"],
}

lang = detect_language()  # from existing language detection
patterns = selenium_import_patterns.get(lang, [])

for file in source_files:
    content = read_file(file)
    for pattern in patterns:
        if re.search(pattern, content):
            score += 3
            evidence.append(f"Selenium import in {file}")
            break
```

#### 4. Code Patterns (Weight: 5)

Cross-language code patterns characteristic of Selenium.

| Pattern | Description | Regex | Languages |
|---|---|---|---|
| `driver.get(` | Navigate to URL | `driver\.get\s*\(` | All |
| `driver.findElement(` | Find single element | `driver\.findElement\s*\(` | Java, C# |
| `driver.find_element(` | Find single element | `driver\.find_element\s*\(` | Python |
| `WebDriverWait(` | Explicit wait | `WebDriverWait\s*\(` | Python, Java, C# |
| `By.cssSelector(` | CSS selector | `By\.cssSelector\s*\(` | Java, C# |
| `By.css_selector(` | CSS selector | `By\.css_selector\s*\(` | Python |
| `By.xpath(` | XPath selector | `By\.xpath\s*\(` | All |
| `By.id(` | ID selector | `By\.id\s*\(` | Java, C#, JS |
| `driver.quit()` | Close browser session | `driver\.quit\s*\(` | All |
| `expected_conditions` | Expected conditions (Python) | `expected_conditions` | Python |
| `ExpectedConditions` | Expected conditions (Java/C#) | `ExpectedConditions` | Java, C# |

**Detection Logic**:
```python
selenium_code_patterns = [
    r"driver\.get\s*\(",
    r"driver\.find_?[Ee]lement\s*\(",
    r"WebDriverWait\s*\(",
    r"By\.(cssSelector|css_selector|xpath|id|ID|name|NAME)\s*[\(]?",
    r"driver\.quit\s*\(",
]

for file in source_files:
    content = read_file(file)
    for pattern in selenium_code_patterns:
        if re.search(pattern, content):
            score += 5
            evidence.append(f"Selenium code pattern in {file}")
            break  # One match per file
```

#### 5. File Patterns

Selenium does not enforce a standard directory structure. Common conventions per language ecosystem:

| Pattern | Language | Description |
|---|---|---|
| `tests/**/test_*.py` with Selenium imports | Python | pytest convention |
| `src/test/java/**/*Test.java` with Selenium imports | Java | Maven/JUnit convention |
| `test/**/*.test.js` with Selenium imports | JavaScript | Common JS convention |
| `**/*Tests.cs` with Selenium imports | C# | NUnit/xUnit convention |
| `**/page_objects/` or `**/pages/` | Any | Page Object Model directory (strong E2E signal) |

#### 6. Multi-Language Detection Notes

When detecting Selenium, the framework detection pipeline should:

1. **Identify the language first** -- Use existing language detection to determine the project's primary language
2. **Apply language-specific markers** -- Use the dependency, import, and code patterns for the detected language
3. **Aggregate cross-file signals** -- Selenium imports may appear in test files, conftest/setup files, and page object files; aggregate signals across all relevant files
4. **Consider companion packages** -- Presence of `webdriver-manager` (Python), `chromedriver` (JS), or driver-specific Maven dependencies strengthens Selenium confidence

#### 7. Detection Confidence Thresholds

| Condition | Confidence |
|---|---|
| Selenium dependency + import patterns + code patterns | >= 0.95 |
| Selenium dependency + import patterns | >= 0.85 |
| Selenium dependency only | >= 0.70 |
| Import patterns + code patterns (no dependency file found) | >= 0.60 |
| Code patterns only | >= 0.40 |

---

## Priority Resolution

When both E2E and unit test frameworks are detected in the same project, the priority resolution algorithm determines which is primary and which is secondary.

### Standard Resolution (no `--type` flag)

```python
def resolve_priority(unit_frameworks, e2e_frameworks):
    """
    Resolve primary framework across unit and E2E detection.

    Both unit_frameworks and e2e_frameworks are lists of
    (framework_name, score, test_type) tuples.
    """
    all_frameworks = unit_frameworks + e2e_frameworks
    total_score = sum(f[1] for f in all_frameworks)

    if total_score == 0:
        return {
            "primary_framework": "pytest",  # Language-specific fallback
            "test_type": "unit",
            "confidence": 0.1,
            "secondary_frameworks": [],
        }

    # Sort by score descending
    ranked = sorted(all_frameworks, key=lambda f: f[1], reverse=True)
    primary = ranked[0]

    # Secondary: all frameworks with confidence >= 0.2
    secondary = []
    for f in ranked[1:]:
        conf = f[1] / total_score
        if conf >= 0.2:
            secondary.append(f[0])

    return {
        "primary_framework": primary[0],
        "test_type": primary[2],  # "unit" or "e2e"
        "confidence": primary[1] / total_score,
        "secondary_frameworks": secondary,
    }
```

**Key rules**:
- Highest confidence score wins primary, regardless of whether it is a unit or E2E framework
- If the primary is an E2E framework, `test_type` = `"e2e"`
- If the primary is a unit framework, `test_type` = `"unit"` (or `"integration"`)
- Lower-confidence frameworks go to `secondary_frameworks`

### Resolution with `--type e2e` Flag

```python
def resolve_priority_with_type(unit_frameworks, e2e_frameworks, type_flag):
    """
    When --type e2e is specified, E2E frameworks get priority.
    """
    if type_flag == "e2e":
        # Filter E2E frameworks with any confidence
        e2e_candidates = [f for f in e2e_frameworks if f[1] > 0]

        if e2e_candidates:
            # Highest-scoring E2E framework becomes primary
            primary = max(e2e_candidates, key=lambda f: f[1])
            total = sum(f[1] for f in unit_frameworks + e2e_frameworks)
            return {
                "primary_framework": primary[0],
                "test_type": "e2e",
                "confidence": primary[1] / total if total > 0 else 0.5,
                "secondary_frameworks": [f[0] for f in unit_frameworks if f[1] / total >= 0.2],
            }
        else:
            # No E2E framework detected; warn user and fall back
            result = resolve_priority(unit_frameworks, e2e_frameworks)
            result["warning"] = "No E2E framework detected. Falling back to standard detection."
            return result

    # No type flag or type != "e2e": use standard resolution
    return resolve_priority(unit_frameworks, e2e_frameworks)
```

### Coexistence Examples

#### Example 1: Playwright project with Jest

```
Project Structure:
  playwright.config.ts              # Playwright config
  package.json                      # Contains @playwright/test and jest
  jest.config.js                    # Jest config
  tests/e2e/login.spec.ts           # Playwright tests
  tests/unit/api.test.ts            # Jest unit tests

Scoring:
  Playwright:
    - playwright.config.ts: +10
    - @playwright/test in package.json: +8
    - Playwright imports in tests/e2e/: +3
    - Playwright code patterns: +5
    Total: 26

  Jest:
    - jest.config.js: +10
    - jest in package.json: +8
    - Jest imports in tests/unit/: +3
    - Jest code patterns: +5
    Total: 26

  Grand total: 52

Standard resolution:
  - Tie: Both at 26/52 = 0.50
  - When tied, config file presence breaks the tie (both have configs)
  - When still tied, the framework listed first in package.json wins
  - Result: PRIMARY=playwright, test_type=e2e, SECONDARY=[jest]

With --type e2e:
  - PRIMARY=playwright, test_type=e2e, SECONDARY=[jest]
```

#### Example 2: Selenium project with pytest

```
Project Structure:
  pytest.ini                        # pytest config
  requirements.txt                  # Contains pytest and selenium
  tests/test_api.py                 # pytest unit tests
  tests/e2e/test_login.py           # Selenium E2E tests

Scoring:
  pytest:
    - pytest.ini: +10
    - pytest in requirements.txt: +8
    - pytest imports: +2
    - pytest code patterns: +3
    Total: 23

  Selenium:
    - No config file: 0
    - selenium in requirements.txt: +8
    - Selenium imports: +3
    - Selenium code patterns: +5
    Total: 16

  Grand total: 39

Standard resolution:
  - pytest: 23/39 = 0.59
  - Selenium: 16/39 = 0.41
  - PRIMARY=pytest, test_type=unit, SECONDARY=[selenium]

With --type e2e:
  - PRIMARY=selenium, test_type=e2e, SECONDARY=[pytest]
```

#### Example 3: Cypress only (no unit framework)

```
Project Structure:
  cypress.config.ts                 # Cypress config
  package.json                      # Contains cypress
  cypress/e2e/login.cy.ts           # Cypress test

Scoring:
  Cypress:
    - cypress.config.ts: +10
    - cypress in package.json: +8
    - Cypress code patterns: +5
    Total: 23

  No unit framework detected.

Standard resolution:
  - PRIMARY=cypress, test_type=e2e, CONFIDENCE=1.0
```

## Output Format

When E2E detection is complete, the output extends the standard framework detection output:

```yaml
primary_framework: playwright
secondary_frameworks:
  - jest
test_type: e2e
application_framework: react
confidence_score: 0.85
detection_details:
  config_files:
    - playwright.config.ts
    - jest.config.js
  dependencies:
    - "@playwright/test"
    - "jest"
  import_patterns:
    - "from '@playwright/test'" in tests/e2e/login.spec.ts
    - "from 'jest'" in tests/unit/api.test.ts
  code_patterns:
    - "page.goto" in tests/e2e/login.spec.ts
    - "expect(...).toBe" in tests/unit/api.test.ts
```

The `test_type` field values are:

| Value | Meaning |
|---|---|
| `"unit"` | Primary framework is a unit testing framework (pytest, jest, junit, etc.) |
| `"integration"` | Primary framework is an integration testing framework (rare; used when test patterns suggest integration scope) |
| `"e2e"` | Primary framework is an E2E testing framework (playwright, cypress, selenium) |

## Usage in Agents

### Analyze Agent

```markdown
# Read E2E Framework Detection Skill
Read file: skills/framework-detection/e2e-frameworks.md

# Apply Detection Strategies (in parallel with language-specific detection)
1. Check for E2E config files (playwright.config.ts, cypress.config.js, etc.)
2. Parse package.json for E2E dependencies (@playwright/test, cypress, selenium-webdriver)
3. Parse language-specific dependency files for Selenium (requirements.txt, pom.xml, .csproj, Gemfile)
4. Scan source files for E2E import patterns
5. Scan source files for E2E code patterns
6. Check for E2E file patterns (cypress/e2e/, *.spec.ts in testDir)

# Calculate Scores
playwright_score = sum(playwright_evidence_weights)
cypress_score = sum(cypress_evidence_weights)
selenium_score = sum(selenium_evidence_weights)

# Combine with unit framework scores
all_scores = unit_scores + e2e_scores
primary = resolve_priority(unit_frameworks, e2e_frameworks)

# If primary is E2E framework:
#   -> Set test_type = "e2e"
#   -> Load skills/e2e/SKILL.md for agent behavior contracts
#   -> Load skills/e2e/frameworks/{framework}.md for framework specifics
```

## Testing Validation

Test with these sample project configurations:

1. **Playwright-only**: `playwright.config.ts` + `@playwright/test` in package.json -> Expect: playwright, test_type=e2e, confidence >= 0.9
2. **Cypress-only**: `cypress.config.ts` + `cypress` in package.json -> Expect: cypress, test_type=e2e, confidence >= 0.9
3. **Selenium-only (Python)**: `selenium` in requirements.txt + Selenium imports -> Expect: selenium, test_type=e2e, confidence >= 0.85
4. **Selenium-only (Java)**: `selenium-java` in pom.xml + Selenium imports -> Expect: selenium, test_type=e2e, confidence >= 0.85
5. **Playwright + Jest**: Both configs present + both in package.json -> Expect: one primary, one secondary; test_type depends on primary
6. **Selenium + pytest**: pytest.ini + selenium in requirements.txt -> Expect: pytest primary (higher score), selenium secondary
7. **Selenium + pytest with --type e2e**: Same as above but with flag -> Expect: selenium primary, test_type=e2e
8. **No E2E framework**: Pure jest project -> Expect: no E2E detected, test_type=unit
9. **Multiple E2E frameworks**: `playwright.config.ts` + `cypress.config.ts` -> Expect: higher-scoring E2E is primary, other is secondary

## References

- Parent skill: `skills/framework-detection/SKILL.md`
- Playwright framework reference: `skills/e2e/frameworks/playwright.md`
- Cypress framework reference: `skills/e2e/frameworks/cypress.md`
- Selenium framework reference: `skills/e2e/frameworks/selenium.md`
- E2E testing skill: `skills/e2e/SKILL.md`
- E2E specification: `.sdd/specs/2026-02-13-e2e-web-test-authoring.md` (REQ-F-1, REQ-F-2, REQ-F-3)

---

**Last Updated**: 2026-02-16
**Phase**: 2 - Detection and Parsing
**Status**: Complete
