---
name: framework-detection
description: Detect testing frameworks and application frameworks in target projects. Use when analyzing a codebase to identify which testing framework is configured (pytest, Jest, JUnit, xUnit, Google Test, Unreal Engine LLT, etc.) across Python, JavaScript, TypeScript, Java, C#, Go, C++, and Unreal Engine.
user-invocable: false
---

# Framework Detection Skill

**Version**: 1.1.0
**Category**: Analysis
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++, Rust, Ruby, C, Unreal Engine C++
**Purpose**: Detect testing frameworks and application frameworks in target projects

**New in v1.1.0**: Added Unreal Engine Low Level Tests (LLT) framework detection with UE-specific build system patterns (TestModuleRules, TestTargetRules, TestHarness.h)

## Overview

The Framework Detection Skill provides comprehensive language and framework identification capabilities for automated testing workflows. It uses multiple detection strategies with confidence scoring to accurately identify which testing framework(s) a project uses, enabling context-aware test generation and execution.

## Skill Interface

### Input

```yaml
project_path: Path to the project root directory
language_hint: Optional language type (python, javascript, typescript, etc.)
```

### Output

```yaml
primary_framework: Detected primary testing framework (e.g., "pytest", "jest", "junit", "ue-llt", "playwright")
secondary_frameworks: List of additional frameworks found (e.g., ["unittest", "pytest-mock"])
test_type: Type of tests the primary framework supports ("unit", "integration", "e2e")
application_framework: Detected application framework if any (e.g., "django", "react", "spring-boot", "unreal-engine")
confidence_score: Float 0.0-1.0 indicating detection confidence
detection_details:
  config_files: List of framework config files found
  dependencies: List of framework dependencies found
  import_patterns: List of framework imports found in code
  code_patterns: List of framework-specific code patterns found
  build_system: Build system detected (e.g., "cmake", "ue-ubt", "maven", "npm")
```

**Note**: For Unreal Engine LLT detection details, see `skills/framework-detection/ue-llt-framework.md`

### Confidence Scoring Algorithm

Framework detection uses a weighted scoring system:

1. **Configuration Files** (weight: 10)
   - Framework-specific config files (pytest.ini, jest.config.js, etc.)
   - High confidence indicator

2. **Dependencies** (weight: 8)
   - Package manager declarations (requirements.txt, package.json, pom.xml, etc.)
   - Strong indicator of intentional framework usage

3. **Import Patterns** (weight: 2-3)
   - Import statements in source files
   - Lower weight as files might import without using

4. **Code Patterns** (weight: 3-5)
   - Framework-specific syntax (decorators, function names, assertions)
   - Medium confidence indicator

5. **Build System Patterns** (weight: 10-15)
   - Language-specific build configs (CMakeLists.txt, Cargo.toml, .csproj, pom.xml, go.mod, Gemfile)
   - Very high confidence for compiled languages

**Total Confidence** = `framework_score / total_all_scores`

**Minimum Threshold**: 0.1 (10%) to report a framework as detected

**Evidence Requirements**: At least 2 types of evidence required to avoid false positives

## Detection Strategies

### 1. Config File Detection

Scan for framework-specific configuration files:

```
pytest.ini, pyproject.toml, setup.cfg          # Python/pytest
jest.config.js, jest.config.json               # JavaScript/Jest
vitest.config.ts, vite.config.ts               # TypeScript/Vitest
CMakeLists.txt                                 # C++
Cargo.toml                                     # Rust
go.mod                                         # Go
*.csproj                                       # C#
pom.xml, build.gradle                          # Java
Gemfile                                        # Ruby
playwright.config.ts, playwright.config.js     # E2E/Playwright
cypress.config.js, cypress.config.ts           # E2E/Cypress
cypress.json                                   # E2E/Cypress (legacy)
```

### 2. Dependency Analysis

Parse package manager files:

**Python**:
- requirements.txt (pip)
- pyproject.toml (poetry, pip)
- setup.py, setup.cfg

**JavaScript/TypeScript**:
- package.json (npm, yarn, pnpm)

**Java**:
- pom.xml (Maven)
- build.gradle, build.gradle.kts (Gradle)

**C#**:
- *.csproj (NuGet)
- packages.config

**Go**:
- go.mod, go.sum

**C++**:
- CMakeLists.txt (CMake)
- conanfile.txt, conanfile.py (Conan)

**Rust**:
- Cargo.toml, Cargo.lock

**Ruby**:
- Gemfile, Gemfile.lock

### 3. Import Pattern Analysis

Scan source files for framework imports (sample up to 50 files per extension):

```python
# Python
import pytest
import unittest
from unittest import TestCase

# JavaScript/TypeScript
import { describe, it, expect } from 'jest'
import { describe, test } from 'vitest'

# Java
import org.junit.jupiter.api.Test;
import org.junit.Test;

# C#
using Xunit;
using NUnit.Framework;

# Go
import "testing"
import "github.com/stretchr/testify/assert"

# C++
#include <gtest/gtest.h>
#include <catch2/catch_test_macros.hpp>

# Rust
#[test]
#[cfg(test)]

# Ruby
require 'rspec'
require 'minitest/autorun'
```

### 4. Code Pattern Detection

Identify framework-specific syntax using regex patterns:

```python
# Pytest
r'def test_\w+'                                 # Test function naming
r'import pytest'                                # pytest import
r'@pytest\.(fixture|mark)'                      # pytest decorators

# unittest
r'class \w+\(unittest\.TestCase\)'              # unittest class
r'def test\w+\(self\)'                          # unittest method
r'self\.assert\w+'                              # unittest assertions

# Jest/Vitest
r'describe\s*\('                                # describe block
r'it\s*\(|test\s*\('                            # test cases
r'expect\(.*\)\.to'                             # expect assertions

# JUnit
r'@Test|@ParameterizedTest'                     # JUnit annotations
r'import org\.junit'                            # JUnit imports

# xUnit
r'\[Fact\]|\[Theory\]'                          # xUnit attributes
r'Assert\.Equal|Assert\.True'                   # xUnit assertions

# Go
r'func\s+Test\w+\('                             # Go test functions
r'\*testing\.T\b'                               # testing.T parameter

# GTest
r'TEST\(|TEST_F\('                              # GTest macros
r'EXPECT_|ASSERT_'                              # GTest assertions

# Catch2
r'TEST_CASE\(|SECTION\('                        # Catch2 macros
r'REQUIRE\(|CHECK\('                            # Catch2 assertions

# Rust
r'#\[test\]|#\[cfg\(test\)\]'                   # Rust test attributes
r'assert_eq!|assert!'                           # Rust assertions

# RSpec
r'describe\s+|context\s+'                       # RSpec blocks
r'it\s+["\']|expect\(.*\)\.to\s+'               # RSpec expectations
```

### 5. Build System Pattern Detection

Language-specific build configuration analysis:

**CMake (C/C++)**:
```cmake
find_package(GTest REQUIRED)
target_link_libraries(mytest gtest)
find_package(Catch2 REQUIRED)
```

**Cargo.toml (Rust)**:
```toml
[dev-dependencies]
proptest = "1.0"
criterion = "0.5"

[[test]]
name = "integration_tests"
```

**go.mod (Go)**:
```go
require (
    github.com/stretchr/testify v1.8.0
    github.com/onsi/ginkgo/v2 v2.8.0
)
```

**.csproj (C#)**:
```xml
<PackageReference Include="xunit" Version="2.4.2" />
<PackageReference Include="NUnit" Version="3.13.3" />
```

**pom.xml / build.gradle (Java)**:
```xml
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
</dependency>
```

```gradle
testImplementation 'org.junit.jupiter:junit-jupiter:5.9.0'
```

**Gemfile (Ruby)**:
```ruby
gem 'rspec'
gem 'minitest'
```

### 6. Language-Specific Filtering

Filter detected frameworks by language compatibility:

- **Python**: pytest, unittest, django, flask, fastapi
- **JavaScript**: jest, mocha, vitest, react, vue, express
- **TypeScript**: jest, vitest, react, angular, vue
- **Java**: junit, spring, spring-boot
- **C#**: xunit, nunit, mstest
- **Go**: go built-in, testify, ginkgo
- **C++**: gtest, catch2, cppunit, boost.test, doctest, ue-llt (Unreal Engine)
- **Rust**: rust built-in, cargo-nextest, proptest, criterion
- **Ruby**: rspec, minitest
- **C**: unity, cmocka, cunit, check
- **E2E (cross-language)**: playwright, cypress, selenium -- see [E2E Frameworks](./e2e-frameworks.md)

## Language-Specific Skills

Each supported language has its own detailed skill document:

- [Python Frameworks](./python-frameworks.md) - pytest, unittest
- JavaScript Frameworks (Phase 3) - jest, vitest, mocha
- TypeScript Frameworks (Phase 3) - jest, vitest
- Java Frameworks (Phase 3) - junit 4/5, testng
- C# Frameworks (Phase 4) - xunit, nunit, mstest
- Go Frameworks (Phase 4) - built-in, testify, ginkgo
- [C++ Frameworks](./cpp-frameworks.md) - gtest, catch2
- [Unreal Engine LLT](./ue-llt-framework.md) - Unreal Engine Low Level Tests (Catch2 wrapper)
- Rust Frameworks (Phase 5) - cargo test, nextest
- Ruby Frameworks (Phase 5) - rspec, minitest
- C Frameworks (Phase 5) - unity, cmocka
- [E2E Frameworks](./e2e-frameworks.md) - playwright, cypress, selenium (cross-language)

## Usage in Agents

### Analyze Agent

When analyzing a project to identify test targets:

```markdown
1. Read this skill: skills/framework-detection/SKILL.md
2. Read language-specific skill based on detected language
3. Apply detection strategies in order:
   - Check config files (fast, high confidence)
   - Check dependencies (medium speed, high confidence)
   - Check build system patterns (medium speed, high confidence)
   - Check imports (slower, medium confidence)
   - Check code patterns (slower, medium confidence)
4. Calculate confidence scores
5. Filter by language compatibility
6. Return primary framework with ≥ 0.3 confidence OR fallback to language default
```

### Write Agent

When generating test code:

```markdown
1. Receive framework from Analyze Agent output
2. **CRITICAL**: Read skills/test-location-detection/SKILL.md to determine correct test file location
3. Load corresponding template: templates/{language}-{framework}-template.md
4. Use framework-specific conventions from detection skill
5. Determine test file path using Test Location Detection skill
6. Validate test path is NOT in .claude-tests/ or temporary directories
7. Generate test code following framework patterns at correct location
```

### Execute Agent

When running tests:

```markdown
1. Receive framework from Analyze Agent output
2. Use framework-specific test execution command
3. Parse output using framework-specific parser from result-parsing skill
```

### Special Case: Unreal Engine LLT Detection

For C++ projects, **ALWAYS check for UE LLT FIRST** before checking for standalone Catch2:

```markdown
1. **Priority Detection for UE LLT**:
   - Check for TestModuleRules in .Build.cs files (Weight: 15) - DEFINITIVE
   - Check for TestTargetRules in .Target.cs files (Weight: 15) - DEFINITIVE
   - Check for #include "TestHarness.h" (Weight: 8) - HIGH CONFIDENCE
   - If any found → UE LLT with high confidence

2. **Exclusion Check for Standalone Catch2**:
   - Check for CMakeLists.txt, Makefile, Bazel WORKSPACE
   - Check for #include <catch2/catch_test_macros.hpp>
   - If found → Standalone Catch2 (NOT UE LLT)

3. **Supporting Evidence** (only if high confidence already):
   - TEST_CASE with UE naming (ModuleName::FClassName::Method)
   - UE types (FString, TArray, UObject) in test code
   - Tests/ directory at plugin root
   - .uplugin or .uproject files

4. **Recommendation**:
   - If UE LLT detected (confidence ≥ 0.5), recommend `/llt-generate` command
   - Display: "Detected Unreal Engine LLT framework. Use `/llt-generate` for UE-specific test generation."
```

**Important**: See `skills/framework-detection/ue-llt-framework.md` for complete UE LLT detection patterns and confidence scoring algorithm.

## Error Handling

### No Framework Detected

If confidence scores are all < 0.1:

1. Return language-specific fallback:
   - Python → pytest (most common)
   - JavaScript → jest (most common)
   - TypeScript → jest (most common)
   - Java → junit (standard)
   - C# → xunit (modern preference)
   - Go → built-in (always available)
   - C++ → gtest (most popular)
   - Rust → cargo test (built-in)
   - Ruby → rspec (most common)
   - C → unity (lightweight)

2. Report confidence: 0.1 (fallback)

### Multiple Frameworks Detected

If multiple frameworks have high confidence (≥ 0.2):

1. Return highest scoring as primary
2. List others as secondary frameworks
3. Note potential conflicts in detection_details

### Conflicting Evidence

If config files suggest one framework but dependencies suggest another:

1. Prioritize config files (weight: 10) over other evidence
2. Report conflict in detection_details
3. Suggest user confirmation via approval gate

## Testing

Manual validation with sample projects:

- Python project with pytest (pytest.ini + pytest in requirements.txt)
- Python project with unittest only (no external dependencies)
- Python project with both pytest and unittest
- Project with no test framework installed
- Project with custom test harness

Expected outcomes:

- Single framework: Confidence ≥ 0.6
- Multiple frameworks: Primary ≥ 0.4, secondary ≥ 0.2
- No framework: Fallback with confidence = 0.1
- False positive rate: < 5%

## Future Enhancements

- Version detection for frameworks (currently returns "unknown")
- Test coverage tool detection (pytest-cov, nyc, coverage.py)
- Mocking library detection (unittest.mock, pytest-mock, sinon)
- Plugin/extension detection (pytest plugins, jest transformers)
- Performance test framework detection (pytest-benchmark, JMH)
- ~~E2E framework detection (Cypress, Playwright, Selenium)~~ -- Implemented in [E2E Frameworks](./e2e-frameworks.md)

## References

- Dante's FrameworkDetector: `dante/src/dante/analysis/framework_detector.py`
- Framework documentation links (pytest, jest, junit, etc.)
- Language package manager documentation

---

**Last Updated**: 2026-02-16
**Status**: Phase 1 - Python support implemented; Phase 2 - E2E framework detection integrated
