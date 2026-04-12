# Selenium Framework Reference

**Status**: Detection markers defined. Full implementation planned.

**Version**: 0.1.0 (stub)
**Framework**: Selenium WebDriver
**Language**: Multi-language (Python, Java, JavaScript, C#, Ruby, Kotlin)
**Category**: E2E Testing
**Purpose**: Framework-specific reference for Selenium E2E test authoring within Dante

## Overview

This file is the Level 2 framework-specific reference for Selenium WebDriver. It follows the two-level architecture defined in `skills/e2e/SKILL.md`: agents load the generic E2E contract (Level 1), then load this file (Level 2) for Selenium-specific selector APIs, wait patterns, error regex, fix strategies, and CLI workflows.

Selenium is unique among E2E frameworks in that it spans multiple programming languages. Detection markers are organized by language to enable accurate identification regardless of which language binding is in use.

Currently, only the detection markers section is implemented. Detection markers are comprehensive enough to support the framework detection pipeline (`skills/framework-detection/e2e-frameworks.md`). All other sections contain placeholder headings with content planned for future implementation.

## Detection Markers

Detection markers enable the framework detection pipeline to identify Selenium projects with high confidence. Because Selenium spans multiple languages, markers are organized by language. Each marker type carries a detection weight used in weighted confidence scoring.

### Config Files (weight: 5)

Selenium does not have a single standard config file like Playwright or Cypress. The lower weight reflects this. Detection relies more heavily on dependencies and code patterns.

| Config File | Language | Notes |
|---|---|---|
| `selenium.conf.js` | JavaScript | Custom config (not standard, but sometimes used) |
| `conftest.py` with Selenium imports | Python | pytest conftest with Selenium fixtures |
| `seleniumrc.json` | Any | Legacy Selenium RC config (rare) |

Note: Selenium projects often configure via test runner config files (pytest.ini, testng.xml, etc.) rather than a dedicated Selenium config file.

### Dependencies (weight: 8)

#### Python

| Dependency | Location | Notes |
|---|---|---|
| `selenium` | `requirements.txt` | Primary Python Selenium package |
| `selenium` | `Pipfile` (under `[packages]` or `[dev-packages]`) | Pipenv projects |
| `selenium` | `pyproject.toml` (under `[project.dependencies]` or `[tool.poetry.dependencies]`) | Modern Python packaging |
| `selenium` | `setup.py` / `setup.cfg` | Legacy Python packaging |
| `webdriver-manager` | Any Python dependency file | Common companion package |

#### Java

| Dependency | Location | Notes |
|---|---|---|
| `selenium-java` | `pom.xml` (`<dependency>` section) | Maven projects |
| `selenium-java` | `build.gradle` / `build.gradle.kts` | Gradle projects |
| `selenium-api` | `pom.xml` or `build.gradle` | Selenium API-only dependency |
| `selenium-chrome-driver` | `pom.xml` or `build.gradle` | Chrome-specific driver dependency |
| `selenium-firefox-driver` | `pom.xml` or `build.gradle` | Firefox-specific driver dependency |
| `selenium-support` | `pom.xml` or `build.gradle` | Selenium support classes (WebDriverWait, etc.) |

#### JavaScript / TypeScript

| Dependency | Location | Notes |
|---|---|---|
| `selenium-webdriver` | `package.json` (`dependencies` or `devDependencies`) | Primary JS/TS Selenium package |
| `@types/selenium-webdriver` | `package.json` (`devDependencies`) | TypeScript type definitions |
| `chromedriver` | `package.json` | Chrome driver companion package |
| `geckodriver` | `package.json` | Firefox driver companion package |

#### C# / .NET

| Dependency | Location | Notes |
|---|---|---|
| `Selenium.WebDriver` | `.csproj` (`<PackageReference>`) | Primary C# Selenium package (NuGet) |
| `Selenium.Support` | `.csproj` (`<PackageReference>`) | Support classes (WebDriverWait, SelectElement) |
| `Selenium.WebDriver.ChromeDriver` | `.csproj` | Chrome driver NuGet package |
| `Selenium.WebDriver.GeckoDriver` | `.csproj` | Firefox driver NuGet package |
| `Selenium.WebDriver` | `packages.config` | Legacy NuGet package reference format |

#### Ruby

| Dependency | Location | Notes |
|---|---|---|
| `selenium-webdriver` | `Gemfile` | Primary Ruby Selenium gem |
| `webdrivers` | `Gemfile` | Common companion gem for driver management |

### Import Patterns (weight: 3)

#### Python

| Pattern | Regex | Notes |
|---|---|---|
| `from selenium import webdriver` | `from\s+selenium\s+import\s+webdriver` | Primary import |
| `from selenium.webdriver.common.by import By` | `from\s+selenium\.webdriver\.common\.by\s+import\s+By` | Locator strategy import |
| `from selenium.webdriver.common.keys import Keys` | `from\s+selenium\.webdriver\.common\.keys\s+import\s+Keys` | Keyboard interaction import |
| `from selenium.webdriver.support.ui import WebDriverWait` | `from\s+selenium\.webdriver\.support\.ui\s+import\s+WebDriverWait` | Explicit wait import |
| `from selenium.webdriver.support import expected_conditions` | `from\s+selenium\.webdriver\.support\s+import\s+expected_conditions` | Expected conditions import |
| `import selenium` | `import\s+selenium` | Top-level module import |

#### Java

| Pattern | Regex | Notes |
|---|---|---|
| `import org.openqa.selenium.*` | `import\s+org\.openqa\.selenium\.\*` | Wildcard import |
| `import org.openqa.selenium.WebDriver` | `import\s+org\.openqa\.selenium\.WebDriver` | WebDriver interface import |
| `import org.openqa.selenium.By` | `import\s+org\.openqa\.selenium\.By` | Locator strategy import |
| `import org.openqa.selenium.WebElement` | `import\s+org\.openqa\.selenium\.WebElement` | WebElement import |
| `import org.openqa.selenium.chrome.ChromeDriver` | `import\s+org\.openqa\.selenium\.chrome\.ChromeDriver` | Chrome driver import |
| `import org.openqa.selenium.firefox.FirefoxDriver` | `import\s+org\.openqa\.selenium\.firefox\.FirefoxDriver` | Firefox driver import |
| `import org.openqa.selenium.support.ui.WebDriverWait` | `import\s+org\.openqa\.selenium\.support\.ui\.WebDriverWait` | Explicit wait import |
| `import org.openqa.selenium.support.ui.ExpectedConditions` | `import\s+org\.openqa\.selenium\.support\.ui\.ExpectedConditions` | Expected conditions import |

#### JavaScript / TypeScript

| Pattern | Regex | Notes |
|---|---|---|
| `require('selenium-webdriver')` | `require\s*\(\s*['"]selenium-webdriver['"]\s*\)` | CommonJS require |
| `from 'selenium-webdriver'` | `from\s+['"]selenium-webdriver['"]` | ES module import |
| `require('selenium-webdriver/chrome')` | `require\s*\(\s*['"]selenium-webdriver/chrome['"]\s*\)` | Chrome-specific import |
| `const { Builder, By, until } = require('selenium-webdriver')` | `Builder.*By.*require.*selenium-webdriver` | Destructured CommonJS import |
| `import { Builder, By, until } from 'selenium-webdriver'` | `import\s+\{.*Builder.*\}\s+from\s+['"]selenium-webdriver['"]` | Destructured ES import |

#### C# / .NET

| Pattern | Regex | Notes |
|---|---|---|
| `using OpenQA.Selenium` | `using\s+OpenQA\.Selenium` | Primary namespace import |
| `using OpenQA.Selenium.Chrome` | `using\s+OpenQA\.Selenium\.Chrome` | Chrome driver namespace |
| `using OpenQA.Selenium.Firefox` | `using\s+OpenQA\.Selenium\.Firefox` | Firefox driver namespace |
| `using OpenQA.Selenium.Support.UI` | `using\s+OpenQA\.Selenium\.Support\.UI` | Support classes (WebDriverWait) |
| `using OpenQA.Selenium.Interactions` | `using\s+OpenQA\.Selenium\.Interactions` | Actions class for complex interactions |

### Code Patterns (weight: 5)

Code patterns that are characteristic of Selenium across all language bindings. These patterns use generalized regex that match regardless of the specific language syntax.

| Pattern | Description | Regex | Languages |
|---|---|---|---|
| `driver.get()` | Navigate to URL | `driver\.get\s*\(` | Python, Java, JS, C#, Ruby |
| `driver.findElement()` | Find single element | `driver\.findElement\s*\(` | Java, C# |
| `driver.find_element()` | Find single element | `driver\.find_element\s*\(` | Python |
| `driver.findElements()` | Find multiple elements | `driver\.findElements\s*\(` | Java, C# |
| `driver.find_elements()` | Find multiple elements | `driver\.find_elements\s*\(` | Python |
| `WebDriverWait(` | Explicit wait constructor | `WebDriverWait\s*\(` | Python, Java, C# |
| `By.cssSelector()` | CSS selector locator | `By\.cssSelector\s*\(` | Java, C# |
| `By.css_selector()` | CSS selector locator | `By\.css_selector\s*\(` | Python |
| `By.css(` | CSS selector locator | `By\.css\s*\(` | JS |
| `By.xpath()` | XPath locator | `By\.xpath\s*\(` | Java, C#, JS |
| `By.xpath(` | XPath locator | `By\.xpath\s*\(` | Python |
| `By.id()` | ID locator | `By\.id\s*\(` | Java, C#, JS |
| `By.ID` | ID locator | `By\.ID` | Python |
| `By.name()` | Name attribute locator | `By\.name\s*\(` | Java, C#, JS |
| `By.NAME` | Name attribute locator | `By\.NAME` | Python |
| `By.className()` | Class name locator | `By\.className\s*\(` | Java |
| `By.CLASS_NAME` | Class name locator | `By\.CLASS_NAME` | Python |
| `driver.quit()` | Close browser and end session | `driver\.quit\s*\(` | All |
| `driver.close()` | Close current window | `driver\.close\s*\(` | All |
| `driver.getCurrentUrl()` | Get current URL | `driver\.getCurrentUrl\s*\(` | Java |
| `driver.current_url` | Get current URL | `driver\.current_url` | Python |
| `driver.getTitle()` | Get page title | `driver\.getTitle\s*\(` | Java |
| `driver.title` | Get page title | `driver\.title` | Python |
| `expected_conditions` | Expected conditions for waits | `expected_conditions` | Python |
| `ExpectedConditions` | Expected conditions for waits | `ExpectedConditions` | Java, C# |
| `until.elementLocated` | JS expected condition | `until\.elementLocated` | JS |

### File Patterns

Selenium does not enforce a standard directory structure, but common conventions exist per language ecosystem.

| Pattern | Language | Description |
|---|---|---|
| `tests/**/test_*.py` with Selenium imports | Python | pytest convention with Selenium |
| `tests/**/*_test.py` with Selenium imports | Python | Alternative pytest naming |
| `src/test/java/**/*Test.java` with Selenium imports | Java | Maven/JUnit convention |
| `src/test/java/**/*IT.java` with Selenium imports | Java | Integration test convention |
| `test/**/*.test.js` with Selenium imports | JavaScript | Common JS test convention |
| `test/**/*.spec.js` with Selenium imports | JavaScript | Alternative JS convention |
| `**/*Tests.cs` with Selenium imports | C# | NUnit/xUnit convention |
| `**/page_objects/` or `**/pages/` | Any | Page Object Model directory (strong E2E signal) |
| `**/pageobjects/` | Any | Alternative Page Object directory |

### Detection Confidence Thresholds

| Condition | Confidence |
|---|---|
| Selenium dependency + import patterns + code patterns | >= 0.95 |
| Selenium dependency + import patterns | >= 0.85 |
| Selenium dependency only | >= 0.70 |
| Import patterns + code patterns (no dependency file found) | >= 0.60 |
| Code patterns only | >= 0.40 |

### Multi-Language Detection Notes

When detecting Selenium, the framework detection pipeline should:

1. **Identify the language first** -- Check which language ecosystem the project uses (Python, Java, JS, C#) based on existing language detection
2. **Apply language-specific markers** -- Use the dependency, import, and code patterns for the detected language
3. **Aggregate cross-file signals** -- Selenium imports may appear in test files, conftest/setup files, and page object files; aggregate signals across all relevant files
4. **Consider companion packages** -- Presence of `webdriver-manager` (Python), `chromedriver` (JS), or driver-specific Maven dependencies strengthens Selenium confidence

## API Mapping

Not yet implemented. Full implementation planned for future release.

This section will map generic E2E concepts to Selenium-specific APIs per language:

- Selector priority strategy per language binding
- Wait strategy hierarchy (implicit waits, explicit waits via `WebDriverWait`, fluent waits)
- Assertion patterns (framework-dependent: pytest assertions, JUnit assertions, etc.)
- Navigation patterns (`driver.get()`, `driver.navigate()`)
- Network mocking patterns (Selenium 4 CDP integration, proxy-based approaches)

## Error Patterns

Not yet implemented. Full implementation planned for future release.

This section will provide framework-specific regex patterns that fill the pattern templates defined in `skills/e2e/error-classification.md` for each error category (E1-E6):

- E1 (Selector): `NoSuchElementException`, `StaleElementReferenceException`, `ElementNotInteractableException`
- E2 (Timing): `TimeoutException` from `WebDriverWait`, implicit wait timeout
- E3 (Navigation): `WebDriverException` on navigation, `InvalidArgumentException` for malformed URLs
- E4 (Network): Network-related `WebDriverException`, proxy errors
- E5 (Browser): `SessionNotCreatedException`, `WebDriverException` on browser crash, driver version mismatch
- E6 (UI Assertion): Test runner assertion failures on element state/text/attribute

## Fix Strategies

Not yet implemented. Full implementation planned for future release.

This section will provide Selenium-specific fix strategies per error category (E1-E6), following the resolution strategy templates in `skills/e2e/error-classification.md`:

- E1 (Selector): Use `By.id()` or `By.cssSelector('[data-testid=...]')` over fragile XPath, verify element presence with explicit wait before interaction
- E2 (Timing): Use `WebDriverWait` with `expected_conditions` / `ExpectedConditions`, avoid `time.sleep()` / `Thread.sleep()`
- E3 (Navigation): Verify URL after navigation with explicit wait, handle redirects
- E4 (Network): Use Selenium 4 CDP for network interception, or proxy-based mocking
- E5 (Browser): Verify driver-browser version compatibility, manage driver lifecycle
- E6 (UI Assertion): Retrieve element state before assertion, use explicit waits for dynamic content

## CLI Workflows

Not yet implemented. Full implementation planned for future release.

This section will define Selenium test execution workflows per language:

- Python: `pytest tests/ -v`, `python -m pytest tests/`
- Java (Maven): `mvn test -Dtest=TestClass`, `mvn verify`
- Java (Gradle): `gradle test --tests TestClass`
- JavaScript: `npx mocha test/`, `npx jest test/`
- C#: `dotnet test`, `dotnet test --filter TestClass`
- Browser exploration: Language-specific REPL/interactive modes for selector discovery

## Config Parsing

Not yet implemented. Full implementation planned for future release.

This section will define how to extract configuration from Selenium project files per language:

- Python: Base URL from environment variables, fixtures, or config files
- Java: Base URL from properties files, TestNG XML, or JUnit configuration
- JavaScript: Base URL from environment or config module
- C#: Base URL from appsettings.json or runsettings
- Common: WebDriver options, browser selection, timeouts, headless mode, window size

## Best Practices

Not yet implemented. Full implementation planned for future release.

This section will document Selenium-specific best practices for E2E test authoring:

- Page Object Model (POM) for selector and interaction encapsulation
- Explicit waits over implicit waits (avoid mixing both)
- Driver lifecycle management (setup/teardown per test vs per suite)
- WebDriver manager for automatic driver version management
- Headless mode for CI environments
- Screenshot capture on failure
- Selenium Grid for parallel/remote execution
- Selenium 4 relative locators (`near()`, `above()`, `below()`)
- Avoiding `Thread.sleep()` / `time.sleep()` fixed delays

## References

- Generic E2E contract: `skills/e2e/SKILL.md`
- Error classification: `skills/e2e/error-classification.md`
- Knowledge management: `skills/e2e/knowledge-management.md`
- Browser exploration: `skills/e2e/browser-exploration.md`
- Framework detection: `skills/framework-detection/e2e-frameworks.md`
- Selenium documentation: https://www.selenium.dev/documentation/

---

**Last Updated**: 2026-02-16
**Status**: Stub -- Detection markers defined. Full implementation planned.
**Next**: Full Selenium implementation (API mapping, error patterns, fix strategies, CLI workflows, config parsing, best practices)
