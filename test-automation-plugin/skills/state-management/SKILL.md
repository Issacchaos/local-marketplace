---
name: state-management
description: Provides guidelines and patterns for workflow state persistence and resumption. Use when saving or restoring test loop state for the /test-resume command and tracking workflow progress across sessions.
user-invocable: false
---

# State Management Skill

**Purpose**: Provides guidelines and patterns for workflow state persistence and resumption

**Category**: Infrastructure
**Used By**: Test Loop Orchestrator, Resume Command
**Version**: 1.1.0 (Updated 2025-12-11)

---

## Overview

This skill defines how the automated testing plugin persists workflow state to enable resumption across sessions. State management is critical for:
- Resuming interrupted workflows (system crash, user exit, timeout)
- Debugging workflow issues
- Providing user visibility into workflow progress
- Enabling iterative development with approval gates

### Cross-Language Support (v1.1.0 - 2025-12-11)

**CRITICAL CHANGE**: State files are now written to `{project_root}/.claude/` instead of `.claude/` relative to current working directory. This ensures:
- ✅ State files are always in the correct project directory
- ✅ State files are versioned with the project (not lost in plugin directory)
- ✅ Multiple projects can have independent workflow states
- ✅ Supports all 7 languages (Python, JavaScript, TypeScript, Java, C#, Go, C++)

**Required Input**: All state operations now require `project_root` parameter from orchestrator.

---

## State File Format

### Primary State File

**Location**: `{project_root}/.claude/.test-loop-state.md`

Where `{project_root}` is the detected project root directory (see `skills/project-detection/SKILL.md`).

**Format**: Markdown with YAML frontmatter

**Structure**:
```markdown
---
workflow_id: "test-loop-20251208-143022"
current_phase: "code_approval"
iteration: 2
status: "awaiting_approval"
test_type: "unit"
target_path: "src/"
created_at: "2025-12-08T14:30:22Z"
updated_at: "2025-12-08T14:35:18Z"
---

# Test Loop Workflow State

**Workflow ID**: test-loop-20251208-143022
**Status**: Awaiting user approval for generated tests
**Current Phase**: Code Approval (Phase 4 of 7)
**Iteration**: 2 of 3
**Started**: 2025-12-08 14:30:22
**Last Updated**: 2025-12-08 14:35:18

---

## Workflow Progress

- [x] Phase 1: Analysis - Completed
- [x] Phase 2: Plan Generation - Completed
- [x] Phase 3: Plan Approval - Approved (iteration 1)
- [x] Phase 4: Code Generation - Completed
- [ ] Phase 5: Code Approval - **CURRENT** (awaiting approval)
- [ ] Phase 6: Test Execution
- [ ] Phase 7: Validation

---

## Phase 1: Analysis Results

**Completed**: 2025-12-08 14:31:05
**Duration**: 43 seconds

### Summary
- Language: python
- Framework: pytest (confidence: 0.85)
- Test Targets: 15
- Priorities: 3 Critical, 5 High, 4 Medium, 3 Low

### Test Targets
- `src/user_service.py:50` - **create_user** [Critical]
- `src/calculator.py:45` - **divide** [High]
- ...

[Full analysis results...]

---

## Phase 2: Test Plan

**Generated**: 2025-12-08 14:31:50
**Approved**: 2025-12-08 14:32:15
**Iteration**: 1 (approved on first attempt)

### Test Plan
[Full test plan content...]

---

## Phase 3: Plan Approval

**Status**: Approved
**Approved At**: 2025-12-08 14:32:15
**User Feedback**: "Looks good, proceed with generation"
**Iteration**: 1

---

## Phase 4: Generated Tests

**Generated**: 2025-12-08 14:35:18
**Iteration**: 2
**Status**: Pending Approval

### Generated Files
1. `.claude-tests/test_user_service.py` (150 lines, 8 tests)
2. `.claude-tests/test_calculator.py` (75 lines, 4 tests)

### Test Code

#### File: .claude-tests/test_user_service.py
```python
import pytest
from src.user_service import UserService

class TestUserService:
    def test_create_user_valid_data(self):
        # Arrange
        service = UserService()
        data = {"name": "John", "email": "john@example.com"}

        # Act
        result = service.create_user(data)

        # Assert
        assert result["id"] is not None
        assert result["name"] == "John"
```

[Full generated test code...]

---

## Phase 5: Code Approval

**Status**: Awaiting Approval
**Awaiting Since**: 2025-12-08 14:35:18
**Iteration**: 2

**Question**: Do you approve the generated test code?
**Options**: Approve / Request Changes / Reject

---

## User Feedback History

### Iteration 1
**Phase**: Code Approval
**Action**: Request Changes
**Feedback**: "Add more edge cases for divide function"
**Timestamp**: 2025-12-08 14:33:45

### Iteration 2
**Phase**: Code Generation
**Action**: Regenerated
**Changes Made**: Added edge cases for divide by zero, negative numbers
**Timestamp**: 2025-12-08 14:35:18

---

## Next Steps

When workflow resumes:
1. Continue from Phase 5 (Code Approval)
2. Wait for user decision
3. If approved: Proceed to Phase 6 (Test Execution)
4. If changes requested: Return to Phase 4 (Code Generation), iteration 3
5. If rejected: Abort workflow

---

## Metadata

**Workflow Type**: Test Loop (Human-in-the-Loop)
**Total Iterations**: 2
**Max Iterations**: 3
**Time Elapsed**: 5 minutes 18 seconds
```

---

## Frontmatter Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `workflow_id` | string | Unique workflow identifier | `"test-loop-20251208-143022"` |
| `current_phase` | string | Current workflow phase | `"code_approval"` |
| `iteration` | integer | Current iteration number | `2` |
| `status` | string | Workflow status | `"awaiting_approval"` |
| `created_at` | ISO8601 | Workflow start timestamp | `"2025-12-08T14:30:22Z"` |
| `updated_at` | ISO8601 | Last update timestamp | `"2025-12-08T14:35:18Z"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `test_type` | string | Type of tests (unit/integration/e2e) | `"unit"` |
| `target_path` | string | Target directory/file | `"src/"` |
| `language` | string | Detected language | `"python"` |
| `framework` | string | Detected framework | `"pytest"` |
| `max_iterations` | integer | Maximum iterations per phase | `3` |
| `generated_test_files` | array | List of test file paths generated this session | `["tests/test_calculator.py", "tests/test_user.py"]` |
| `generated_tests` | object | Map of {file: [test_names]} generated this session | `{"test_calculator.py": ["test_add", "test_divide"]}` |
| `fix_iterations` | array | List of fix iteration records with modified files and fixes applied | `[{"iteration": 1, "modified_files": ["tests/test_calculator.py"], "fixes_applied": 2}]` |

### E2E State Fields (TASK-011)

These fields are populated ONLY when `test_type=e2e`. For `test_type=unit` or `test_type=integration`, these fields are absent from the state frontmatter. All existing state behavior is unchanged for non-E2E projects.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `test_type` | string | Type of tests: `"unit"`, `"integration"`, or `"e2e"`. Determines which agent behavior branches activate. When `"e2e"`, all agents load the E2E skill and framework reference. | `"e2e"` |
| `e2e_framework` | string | Detected E2E framework name. Resolved during framework detection (see `skills/framework-detection/e2e-frameworks.md`). Used to load the correct framework reference from `skills/e2e/frameworks/{e2e_framework}.md`. | `"playwright"` |
| `e2e_base_url` | string | Application base URL extracted from the E2E framework config file. Used by execute-agent to verify application availability and by write-agent for navigation targets. May be `null` if not configured in the framework config. | `"http://localhost:3000"` |
| `e2e_browser` | string or array | Target browser(s) for E2E test execution. Extracted from framework config. Can be a single browser string or an array of browser names. May be `null` if using framework defaults. | `["chromium", "firefox"]` or `"chromium"` |
| `e2e_knowledge_loaded` | boolean | Whether the E2E knowledge base (`.dante/e2e-knowledge/`) was found and loaded during pre-flight. `true` if the directory existed and contained content; `false` if the directory was newly created (first E2E detection) or is empty. | `true` |

**E2E Field Lifecycle**:

1. **Population**: E2E fields are set during the orchestrator's E2E pre-flight phase (Phase 1.5) after framework detection identifies `test_type=e2e`
2. **Consumption**: All 5 agents (analyze, write, execute, validate, fix) read E2E fields from state to activate E2E-specific behavior
3. **Persistence**: E2E fields persist in the YAML frontmatter across all workflow phases and are archived with the workflow state

**Example State Frontmatter with E2E Fields**:
```yaml
---
workflow_id: "test-loop-20260216-143022"
current_phase: "code_approval"
iteration: 1
status: "awaiting_approval"
test_type: "e2e"
target_path: "e2e/"
project_root: "/home/user/my-web-app"
created_at: "2026-02-16T14:30:22Z"
updated_at: "2026-02-16T14:35:18Z"
language: "typescript"
framework: "playwright"
e2e_framework: "playwright"
e2e_base_url: "http://localhost:3000"
e2e_browser:
  - "chromium"
  - "firefox"
e2e_knowledge_loaded: true
---
```

**Non-E2E Example** (fields absent -- unchanged behavior):
```yaml
---
workflow_id: "test-loop-20260216-150000"
current_phase: "code_approval"
iteration: 1
status: "awaiting_approval"
test_type: "unit"
target_path: "src/"
project_root: "/home/user/my-python-app"
language: "python"
framework: "pytest"
---
```

### Status Values

Valid values for `status` field:
- `"in_progress"` - Workflow actively running
- `"awaiting_approval"` - Waiting for user decision
- `"completed"` - Workflow finished successfully
- `"failed"` - Workflow encountered error
- `"cancelled"` - User cancelled workflow

### Phase Values

Valid values for `current_phase` field:
- `"analysis"` - Analyzing code
- `"plan_generation"` - Generating test plan
- `"plan_approval"` - Waiting for plan approval
- `"code_generation"` - Generating test code
- `"code_approval"` - Waiting for code approval
- `"test_execution"` - Executing tests
- `"validation"` - Validating results
- `"iteration_decision"` - Deciding whether to iterate

---

## Test Origin Tracking Fields (Phase 6.5a)

**Purpose**: Track which test files and tests were generated in the current session to distinguish new vs existing tests for auto-heal logic.

**Added in**: Phase 6.5a (REQ-F-1: Auto-Heal Newly Written Tests)

### Field: `generated_test_files`

**Type**: Array of strings

**Description**: List of absolute file paths for all test files generated during the current workflow session. Used to identify which test files are "new" (written this session) vs "existing" (pre-existing in codebase).

**Example**:
```yaml
generated_test_files:
  - "D:/projects/myapp/tests/test_calculator.py"
  - "D:/projects/myapp/tests/test_user_service.py"
  - "D:/projects/myapp/tests/integration/test_api.py"
```

**Population Logic**: Populated in Phase 3 (Code Generation) after Write Agent completes. Extract all file paths from Write Agent output.

**Usage**: Used in Phase 6 (Validation) to determine if failing test is from a new file (auto-fix without approval) or existing file (require user approval).

### Field: `generated_tests`

**Type**: Object (map of filename → array of test names)

**Description**: Map of test file names to arrays of test function/method names generated during the current session. Enables fine-grained tracking of which specific tests are new.

**Structure**:
```yaml
generated_tests:
  test_calculator.py:
    - "test_add_positive_numbers"
    - "test_add_negative_numbers"
    - "test_divide_by_zero"
    - "test_divide_with_floats"
  test_user_service.py:
    - "TestUserCreation::test_create_user_valid_data"
    - "TestUserCreation::test_create_user_missing_email"
    - "TestUserValidation::test_validate_email_format"
```

**Key Format**: Use filename only (not full path) for map keys. Example: `test_calculator.py`, not `D:/projects/myapp/tests/test_calculator.py`.

**Value Format**: Array of test names. Format depends on language/framework:
- **Python (pytest)**: Function names like `test_add_positive_numbers` or class::method like `TestCalculator::test_add`
- **JavaScript/TypeScript (Jest/Vitest)**: Test descriptions like `"adds two positive numbers"` or `"Calculator › addition"`
- **Java (JUnit)**: Method names like `testAddPositiveNumbers` or class::method like `CalculatorTest::testAdd`
- **C# (xUnit/NUnit)**: Method names like `AddPositiveNumbers_ReturnsSum` or class::method
- **Go**: Function names like `TestAddPositiveNumbers`
- **C++ (GTest/Catch2)**: Test case names like `CalculatorTest.AddPositiveNumbers` or `"Calculator addition"`

**Population Logic**: Populated in Phase 3 (Code Generation) after Write Agent completes. Parse generated test files to extract test names using language-specific patterns (see Test Name Extraction Patterns below).

**Usage**: Used in Phase 6 (Validation) to check if a specific failing test is in the `generated_tests` map. If present: auto-fix without approval. If absent: require user approval before fixing.

### Test Name Extraction Patterns

**IMPORTANT - Code Review Fixes Applied (2026-01-09)**:

This section has been updated to fix all 8 issues identified in TASK-001 code review:

**BLOCKER Issues Fixed**:
1. JavaScript/TypeScript hierarchy tracking - Implemented stack-based tracking for nested describe/it blocks
2. C++ Catch2 SECTION extraction - Added recursive SECTION parsing with nested hierarchy
3. Java package-qualified class names - Extract package declaration and construct fully-qualified names
4. Go subtests recursive handling - Parse nested t.Run() calls with recursive algorithm

**MAJOR Issues Fixed**:
5. Inconsistent test name format - Standardized on `::` delimiter for all languages (C++ GTest changed from `.` to `::`)
6. TypeScript generic type parameters - Handle `describe<TestContext>()` with `(?:<[^>]+>)?` regex pattern
7. Duplicate test name validation - Added deduplication using `list(dict.fromkeys())` at end of extraction
8. Python pytest patterns - Added support for `async def test_*`, `@pytest.mark.parametrize`, and fixture exclusion

**Backward Compatibility**: All existing test names remain valid. Changes only affect new test name extraction.

---

Test name extraction must work consistently across all 7 supported languages. Use these patterns to parse test names from generated code:

#### Python (pytest)

**Pattern 1: Function-based tests (including async and parametrized)**
```python
# Regex: r'^\s*(?:async\s+)?def\s+(test_\w+)\s*\('
# Example code:
def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

async def test_async_fetch():
    result = await fetch_data()
    assert result is not None

@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (0, 0, 0), (-1, 1, 0)])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```
**Extracted names**: `["test_add_positive_numbers", "test_divide_by_zero", "test_async_fetch", "test_add_parametrized"]`

**Note**: Now supports `async def test_*` and functions decorated with `@pytest.mark.parametrize`.

**Pattern 2: Class-based tests (including fixtures and async methods)**
```python
# Regex: r'^\s*class\s+(\w+)' (class name)
# Regex: r'^\s*(?:async\s+)?def\s+(test_\w+)\s*\(self' (method within class)
# Example code:
class TestCalculator:
    @pytest.fixture
    def calculator(self):
        return Calculator()

    def test_add(self, calculator):
        assert calculator.add(2, 3) == 5

    async def test_async_operation(self, calculator):
        result = await calculator.async_add(2, 3)
        assert result == 5

    def test_subtract(self):
        assert self.calc.subtract(5, 3) == 2
```
**Extracted names**: `["TestCalculator::test_add", "TestCalculator::test_async_operation", "TestCalculator::test_subtract"]`

**Note**:
- Use `ClassName::method_name` format for class-based tests
- Now supports `async def test_*` methods
- Excludes `@pytest.fixture` decorated methods (not actual tests)
- To detect fixtures: check for `@pytest.fixture` decorator before method

#### JavaScript/TypeScript (Jest/Vitest)

**Pattern 1: describe/it blocks with hierarchy tracking**
```javascript
// Regex patterns:
// - Describe blocks: r'describe(?:<[^>]+>)?\s*\(\s*[\'"`](.+?)[\'"`]'
// - Test blocks: r'(?:it|test)(?:<[^>]+>)?\s*\(\s*[\'"`](.+?)[\'"`]'
// Note: (?:<[^>]+>)? handles TypeScript generics like describe<TestContext>()

// Example code:
describe('Calculator', () => {
  it('adds two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  test('divides by zero throws error', () => {
    expect(() => divide(1, 0)).toThrow();
  });
});
```
**Extracted names**: `["Calculator › adds two positive numbers", "Calculator › divides by zero throws error"]`

**Note**: Use `describe text › test text` format to capture hierarchy. Must use stack-based tracking to handle nesting correctly.

**Pattern 2: Nested describe blocks with stack-based tracking**
```javascript
describe('Calculator', () => {
  describe('addition', () => {
    it('handles positive numbers', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('handles negative numbers', () => {
      expect(add(-2, -3)).toBe(-5);
    });
  });

  describe('division', () => {
    it('divides positive numbers', () => {
      expect(divide(6, 2)).toBe(3);
    });
  });
});
```
**Extracted names**:
- `"Calculator › addition › handles positive numbers"`
- `"Calculator › addition › handles negative numbers"`
- `"Calculator › division › divides positive numbers"`

**Implementation Note**: Must track brace depth to determine when describe blocks close. See implementation example for stack-based algorithm.

#### Java (JUnit 4/5)

**Pattern 1: JUnit 5 @Test annotations with package-qualified class names**
```java
// Regex for package: r'^\s*package\s+([\w.]+)\s*;'
// Regex for class: r'(?:public\s+)?class\s+(\w+)'
// Regex for @Test: r'@Test\s+(?:public\s+)?void\s+(\w+)\s*\('

// Example code:
package com.example.calculator;

class CalculatorTest {
    @Test
    void testAddPositiveNumbers() {
        assertEquals(5, calculator.add(2, 3));
    }

    @Test
    public void testDivideByZero() {
        assertThrows(ArithmeticException.class, () -> calculator.divide(1, 0));
    }
}
```
**Extracted names**: `["com.example.calculator.CalculatorTest::testAddPositiveNumbers", "com.example.calculator.CalculatorTest::testDivideByZero"]`

**Pattern 2: JUnit 4 @Test annotations with package**
```java
// Same patterns
package com.example;

public class CalculatorTest {
    @Test
    public void testAdd() {
        // ...
    }
}
```
**Extracted names**: `["com.example.CalculatorTest::testAdd"]`

**Note**: Use `package.ClassName::methodName` format for fully-qualified names. Extract package declaration from top of file. If no package found, use `ClassName::methodName`.

#### C# (xUnit/NUnit/MSTest)

**Pattern 1: xUnit [Fact] and [Theory]**
```csharp
// Regex: r'\[(?:Fact|Theory)\]\s+public\s+(?:void|Task(?:<\w+>)?)\s+(\w+)\s*\('
// Example code:
public class CalculatorTests
{
    [Fact]
    public void AddPositiveNumbers_ReturnsSum()
    {
        Assert.Equal(5, calculator.Add(2, 3));
    }

    [Theory]
    [InlineData(2, 3, 5)]
    public void Add_WithInlineData_ReturnsSum(int a, int b, int expected)
    {
        Assert.Equal(expected, calculator.Add(a, b));
    }
}
```
**Extracted names**: `["CalculatorTests::AddPositiveNumbers_ReturnsSum", "CalculatorTests::Add_WithInlineData_ReturnsSum"]`

**Pattern 2: NUnit [Test]**
```csharp
// Regex: r'\[Test\]\s+public\s+(?:void|Task)\s+(\w+)\s*\('
[Test]
public void TestAdd()
{
    // ...
}
```
**Extracted names**: `["CalculatorTests::TestAdd"]`

**Note**: Use `ClassName::MethodName` format. C# test methods typically use PascalCase.

#### Go (testing package)

**Pattern: Test functions with recursive subtest handling**
```go
// Regex for test functions: r'func\s+(Test\w+)\s*\([^)]*\*testing\.T\)'
// Regex for t.Run calls: r't\.Run\s*\(\s*"([^"]+)"\s*,'

// Example code:
package calculator

import "testing"

func TestAddPositiveNumbers(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}

func TestDivideByZero(t *testing.T) {
    _, err := Divide(1, 0)
    if err == nil {
        t.Error("Expected error for division by zero")
    }
}
```
**Extracted names**: `["TestAddPositiveNumbers", "TestDivideByZero"]`

**Note**: Go test functions always start with `Test` prefix.

**Pattern with nested subtests** (recursive tracking required):
```go
func TestCalculator(t *testing.T) {
    t.Run("Addition", func(t *testing.T) {
        t.Run("positive numbers", func(t *testing.T) {
            // test code
        })
        t.Run("negative numbers", func(t *testing.T) {
            // test code
        })
    })
    t.Run("Division", func(t *testing.T) {
        t.Run("by zero", func(t *testing.T) {
            // test code
        })
    })
}
```
**Extracted names**:
- `"TestCalculator/Addition/positive numbers"`
- `"TestCalculator/Addition/negative numbers"`
- `"TestCalculator/Division/by zero"`

**Note**: Use `/` separator for nested subtests. Must parse nested t.Run() calls recursively by tracking brace depth. See implementation example for recursive parsing algorithm.

#### C++ (GTest)

**Pattern 1: TEST macro**
```cpp
// Regex: r'TEST\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)'
// Example code:
TEST(CalculatorTest, AddPositiveNumbers) {
    EXPECT_EQ(5, calculator.add(2, 3));
}

TEST(CalculatorTest, DivideByZero) {
    EXPECT_THROW(calculator.divide(1, 0), std::invalid_argument);
}
```
**Extracted names**: `["CalculatorTest::AddPositiveNumbers", "CalculatorTest::DivideByZero"]`

**Note**: Use `TestSuiteName::TestName` format (changed from `.` to `::` for consistency). First arg to TEST is suite, second is test name.

**Pattern 2: TEST_F (fixture tests)**
```cpp
// Regex: r'TEST_F\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)'
TEST_F(CalculatorTestFixture, AddWithFixture) {
    EXPECT_EQ(5, calculator->add(2, 3));
}
```
**Extracted names**: `["CalculatorTestFixture::AddWithFixture"]`

**Note**: Now uses `::` delimiter for consistency with other languages.

#### C++ (Catch2)

**Pattern 1: TEST_CASE macro**
```cpp
// Regex: r'TEST_CASE\s*\(\s*"(.+?)"\s*(?:,\s*"\[(.+?)\]"\s*)?\)'
// Example code:
TEST_CASE("Calculator addition", "[calculator]") {
    REQUIRE(add(2, 3) == 5);
}

TEST_CASE("Calculator division by zero", "[calculator][edge-cases]") {
    REQUIRE_THROWS(divide(1, 0));
}
```
**Extracted names**: `["Calculator addition", "Calculator division by zero"]`

**Note**: Use quoted test case description as name.

**Pattern 2: SECTION within TEST_CASE (nested extraction required)**
```cpp
// Regex for SECTION: r'SECTION\s*\(\s*"(.+?)"\s*\)'

// Example code:
TEST_CASE("Calculator operations", "[calculator]") {
    SECTION("addition") {
        REQUIRE(add(2, 3) == 5);

        SECTION("with positive numbers") {
            REQUIRE(add(5, 10) == 15);
        }
    }
    SECTION("subtraction") {
        REQUIRE(subtract(5, 3) == 2);
    }
}
```
**Extracted names**:
- `"Calculator operations"`
- `"Calculator operations › addition"`
- `"Calculator operations › addition › with positive numbers"`
- `"Calculator operations › subtraction"`

**Note**: Use `›` separator for nested sections. Must extract SECTION blocks and nest them with TEST_CASE by tracking brace depth. See implementation example for section parsing algorithm.

### Implementation Example

```python
def extract_test_names(test_file_path: str, language: str, framework: str) -> list:
    """
    Extract test names from a test file based on language and framework.

    FIXED ISSUES:
    - Issue #1: JavaScript/TypeScript hierarchy tracking (stack-based tracking for nested describe/it)
    - Issue #2: C++ Catch2 SECTION extraction (parse nested SECTION blocks)
    - Issue #3: Java package-qualified class names (extract package and construct fully-qualified names)
    - Issue #4: Go subtests recursive handling (parse nested t.Run() calls)
    - Issue #5: Inconsistent test name format (use :: delimiter for all languages including C++ GTest)
    - Issue #6: TypeScript generic type parameters (handle describe<TestContext>() with generics)
    - Issue #7: Duplicate test name validation (deduplicate test names)
    - Issue #8: Python pytest patterns (support @pytest.mark.parametrize, async def test_*, and fixtures)

    Args:
        test_file_path: Absolute path to test file
        language: Programming language (python, javascript, typescript, java, csharp, go, cpp)
        framework: Test framework (pytest, jest, vitest, junit, xunit, nunit, mstest, testing, gtest, catch2)

    Returns:
        List of unique test names extracted from file (deduplicated)
    """
    import re

    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    test_names = []

    if language == 'python' and framework == 'pytest':
        # ISSUE #8 FIX: Support async def test_*, @pytest.mark.parametrize, and exclude fixtures
        # Extract function-based tests (including async)
        func_tests = re.findall(r'^\s*(?:async\s+)?def\s+(test_\w+)\s*\(', content, re.MULTILINE)
        test_names.extend(func_tests)

        # Extract class-based tests
        class_matches = re.finditer(r'^\s*class\s+(\w+).*?(?=^\s*class\s+|\Z)', content, re.MULTILINE | re.DOTALL)
        for class_match in class_matches:
            class_name = class_match.group(1)
            class_body = class_match.group(0)

            # Find all methods in class
            method_matches = re.finditer(r'^\s*(?:async\s+)?def\s+(test_\w+)\s*\(self', class_body, re.MULTILINE)
            for method_match in method_matches:
                method_name = method_match.group(1)

                # Check if method is a fixture (exclude it)
                # Look backwards from method to check for @pytest.fixture decorator
                method_start = method_match.start()
                preceding_text = class_body[:method_start]
                lines_before = preceding_text.split('\n')[-5:]  # Check last 5 lines
                is_fixture = any('@pytest.fixture' in line for line in lines_before)

                if not is_fixture:
                    test_names.append(f"{class_name}::{method_name}")

    elif language in ['javascript', 'typescript'] and framework in ['jest', 'vitest']:
        # ISSUE #1 FIX: JavaScript/TypeScript hierarchy tracking with stack-based algorithm
        # ISSUE #6 FIX: Handle TypeScript generics like describe<TestContext>()

        # Parse with stack-based tracking of describe blocks
        describe_stack = []  # Stack of describe block names
        lines = content.split('\n')
        brace_depth = 0
        describe_depths = []  # Track brace depth when each describe was opened

        for line in lines:
            # Track brace depth
            brace_depth += line.count('{') - line.count('}')

            # Check for describe block (with optional TypeScript generics)
            describe_match = re.search(r'describe(?:<[^>]+>)?\s*\(\s*[\'"`](.+?)[\'"`]', line)
            if describe_match:
                describe_name = describe_match.group(1)
                describe_stack.append(describe_name)
                describe_depths.append(brace_depth)
                continue

            # Check for test block (it/test) (with optional TypeScript generics)
            test_match = re.search(r'(?:it|test)(?:<[^>]+>)?\s*\(\s*[\'"`](.+?)[\'"`]', line)
            if test_match:
                test_name = test_match.group(1)
                # Build hierarchical name from describe stack
                if describe_stack:
                    full_name = ' › '.join(describe_stack + [test_name])
                else:
                    full_name = test_name
                test_names.append(full_name)
                continue

            # Pop describe blocks that have closed (brace depth decreased)
            while describe_depths and brace_depth <= describe_depths[-1]:
                describe_stack.pop()
                describe_depths.pop()

    elif language == 'java' and 'junit' in framework:
        # ISSUE #3 FIX: Extract package declaration and construct fully-qualified names

        # Extract package name (if present)
        package_match = re.search(r'^\s*package\s+([\w.]+)\s*;', content, re.MULTILINE)
        package_name = package_match.group(1) if package_match else None

        # Extract class name
        class_match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else 'UnknownClass'

        # Construct fully-qualified class name
        if package_name:
            qualified_class_name = f"{package_name}.{class_name}"
        else:
            qualified_class_name = class_name

        # Extract @Test methods
        test_methods = re.findall(r'@Test\s+(?:public\s+)?void\s+(\w+)\s*\(', content)
        test_names.extend([f"{qualified_class_name}::{method}" for method in test_methods])

    elif language == 'csharp' and framework in ['xunit', 'nunit', 'mstest']:
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else 'UnknownClass'

        # Extract [Fact], [Theory], [Test] methods
        test_methods = re.findall(r'\[(?:Fact|Theory|Test)\]\s+public\s+(?:void|Task(?:<\w+>)?)\s+(\w+)\s*\(', content)
        test_names.extend([f"{class_name}::{method}" for method in test_methods])

    elif language == 'go' and framework == 'testing':
        # ISSUE #4 FIX: Parse nested t.Run() calls recursively

        # Extract top-level Test functions
        test_funcs = re.findall(r'func\s+(Test\w+)\s*\([^)]*\*testing\.T\)', content)

        # For each test function, extract nested t.Run() calls
        for test_func in test_funcs:
            test_names.append(test_func)

            # Find the test function body
            func_pattern = rf'func\s+{re.escape(test_func)}\s*\([^)]*\*testing\.T\)\s*\{{(.*?)^\}}'
            func_match = re.search(func_pattern, content, re.MULTILINE | re.DOTALL)

            if func_match:
                func_body = func_match.group(1)

                # Extract nested t.Run() calls recursively
                # Note: extract_go_subtests() implementation below at lines 824-854
                subtests = extract_go_subtests(func_body, test_func)
                test_names.extend(subtests)

    elif language == 'cpp' and framework == 'gtest':
        # ISSUE #5 FIX: Use :: delimiter instead of . for consistency
        # Extract TEST and TEST_F
        tests = re.findall(r'TEST(?:_F)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', content)
        test_names.extend([f"{suite}::{test}" for suite, test in tests])

    elif language == 'cpp' and framework == 'catch2':
        # ISSUE #2 FIX: Extract SECTION blocks and nest them with TEST_CASE

        # Extract TEST_CASE blocks
        test_case_pattern = r'TEST_CASE\s*\(\s*"(.+?)"\s*(?:,\s*"\[.+?\]"\s*)?\)\s*\{'
        test_case_matches = list(re.finditer(test_case_pattern, content))

        for tc_match in test_case_matches:
            test_case_name = tc_match.group(1)
            test_names.append(test_case_name)

            # Find the TEST_CASE body (from opening { to matching closing })
            tc_start = tc_match.end() - 1  # Start at opening {
            # Note: extract_braced_block() implementation below at lines 890-918
            tc_body = extract_braced_block(content, tc_start)

            # Extract SECTION blocks within this TEST_CASE
            # Note: extract_catch2_sections() implementation below at lines 857-887
            sections = extract_catch2_sections(tc_body, test_case_name)
            test_names.extend(sections)

    # ISSUE #7 FIX: Deduplicate test names
    # Use dict to preserve order while removing duplicates (Python 3.7+)
    test_names = list(dict.fromkeys(test_names))

    return test_names


def extract_go_subtests(func_body: str, parent_name: str) -> list:
    """
    Recursively extract t.Run() subtest calls from Go test function body.

    Args:
        func_body: The body of the test function
        parent_name: The parent test name to prepend

    Returns:
        List of nested subtest names with / separator
    """
    subtests = []

    # Find all t.Run calls
    run_pattern = r't\.Run\s*\(\s*"([^"]+)"\s*,\s*func\s*\([^)]*\*testing\.T\)\s*\{'
    run_matches = list(re.finditer(run_pattern, func_body))

    for run_match in run_matches:
        subtest_name = run_match.group(1)
        full_name = f"{parent_name}/{subtest_name}"
        subtests.append(full_name)

        # Find the subtest body
        subtest_start = run_match.end() - 1  # Start at opening {
        subtest_body = extract_braced_block(func_body, subtest_start)

        # Recursively extract nested subtests
        nested = extract_go_subtests(subtest_body, full_name)
        subtests.extend(nested)

    return subtests


def extract_catch2_sections(test_case_body: str, parent_name: str) -> list:
    """
    Recursively extract SECTION blocks from Catch2 TEST_CASE body.

    Args:
        test_case_body: The body of the TEST_CASE
        parent_name: The parent TEST_CASE or SECTION name

    Returns:
        List of nested section names with › separator
    """
    sections = []

    # Find all SECTION blocks
    section_pattern = r'SECTION\s*\(\s*"(.+?)"\s*\)\s*\{'
    section_matches = list(re.finditer(section_pattern, test_case_body))

    for section_match in section_matches:
        section_name = section_match.group(1)
        full_name = f"{parent_name} › {section_name}"
        sections.append(full_name)

        # Find the section body
        section_start = section_match.end() - 1  # Start at opening {
        section_body = extract_braced_block(test_case_body, section_start)

        # Recursively extract nested sections
        nested = extract_catch2_sections(section_body, full_name)
        sections.extend(nested)

    return sections


def extract_braced_block(content: str, start_pos: int) -> str:
    """
    Extract content of a braced block starting at start_pos.
    Handles nested braces correctly.

    Args:
        content: Full content string
        start_pos: Position of opening brace

    Returns:
        Content between matching braces (excluding braces)
    """
    if start_pos >= len(content) or content[start_pos] != '{':
        return ""

    brace_count = 1
    pos = start_pos + 1

    while pos < len(content) and brace_count > 0:
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
        pos += 1

    if brace_count == 0:
        return content[start_pos + 1:pos - 1]
    else:
        return ""  # Unmatched braces
```

### Usage in Phase 3 (Code Generation)

After Write Agent completes:

```python
# Step 1: Extract generated test file paths from Write Agent output
generated_test_files = [
    os.path.abspath(file_path)
    for file_path in write_agent_output['test_files']
]

# Step 2: Extract test names from each generated file
generated_tests = {}
for file_path in generated_test_files:
    filename = os.path.basename(file_path)
    test_names = extract_test_names(file_path, language, framework)
    generated_tests[filename] = test_names

# Step 3: Update state
state['generated_test_files'] = generated_test_files
state['generated_tests'] = generated_tests

# Step 4: Save state
save_state(state, project_root)
```

### Usage in Phase 6 (Validation)

When determining whether to auto-fix a failing test:

```python
def should_auto_fix(test_name: str, test_file: str, state: dict, confidence: float) -> bool:
    """
    Determine if test should be auto-fixed without user approval.

    Auto-fix criteria:
    1. Test is newly generated (in generated_tests tracking)
    2. Confidence > 0.7 (high confidence fix)
    3. Max 3 iterations not exceeded

    Args:
        test_name: Name of failing test
        test_file: File containing the test
        state: Workflow state dict
        confidence: Fix confidence score (0.0-1.0)

    Returns:
        True if should auto-fix, False if should ask user approval
    """
    # Extract filename from path
    file_name = os.path.basename(test_file)

    # Check if test is newly generated
    generated_tests = state.get('generated_tests', {})
    is_new_test = (
        file_name in generated_tests and
        test_name in generated_tests[file_name]
    )

    # Auto-fix if new test with high confidence
    if is_new_test and confidence > 0.7:
        return True  # Auto-fix
    else:
        return False  # Ask user approval
```

---

## Fix Iteration Change Tracking (Phase 6.5a)

**Purpose**: Track which test files were modified during each fix iteration. This enables smart test selection (only re-run modified tests) to improve iteration performance by 50-70%.

**Added in**: Phase 6.5a (REQ-F-2: Smart Test Selection During Iterations)

### Field: `fix_iterations`

**Type**: Array of objects

**Description**: List of fix iteration records tracking which files were modified and how many fixes were applied in each iteration. Used by Execute Agent to run only modified tests in subsequent iterations instead of the entire test suite.

**Structure**:
```yaml
fix_iterations:
  - iteration: 1
    modified_files:
      - "D:/projects/myapp/tests/test_calculator.py"
      - "D:/projects/myapp/tests/test_user_service.py"
    modified_tests:
      - "test_divide_by_zero"
      - "test_add_negative_numbers"
      - "TestUserCreation::test_create_user_valid_data"
    fixes_applied: 3
    timestamp: "2026-01-09T14:25:30Z"
  - iteration: 2
    modified_files:
      - "D:/projects/myapp/tests/test_calculator.py"
    modified_tests:
      - "test_divide_by_zero"
    fixes_applied: 1
    timestamp: "2026-01-09T14:26:15Z"
```

**Iteration Object Schema**:
- `iteration` (integer, required): Iteration number (1-3)
- `modified_files` (array, required): Absolute paths of test files modified by Fix Agent in this iteration
- `modified_tests` (array, optional): Names of specific tests modified (for granular tracking)
- `fixes_applied` (integer, required): Number of fixes successfully applied in this iteration
- `timestamp` (ISO8601, optional): When the fixes were applied

**Population Logic**: Populated in Phase 6 (Validation/Fixing) after Fix Agent completes each fix iteration:

1. **Fix Agent tracks modified files**: Fix Agent records which test files it edits using the Edit tool
2. **Fix Agent returns modified file list**: After applying fixes, Fix Agent returns list of modified files
3. **Orchestrator appends iteration record**: Orchestrator adds new iteration record to `fix_iterations` array
4. **State persists across iterations**: Change tracking accumulates across all fix iterations

**Usage**: Used in Phase 5 (Execution) and Phase 6 (Validation) for smart test selection:

### Usage in Phase 5 (Execution - Smart Test Selection)

When re-executing tests after a fix iteration:

```python
def get_tests_to_execute(state: dict, iteration: int, test_directory: str) -> list:
    """
    Determine which tests to execute based on iteration and change tracking.

    Args:
        state: Workflow state dict with fix_iterations
        iteration: Current execution iteration (0 = initial run, 1+ = fix iterations)
        test_directory: Base test directory

    Returns:
        List of test file paths to execute (empty = run all tests)
    """
    if iteration == 0:
        # Initial run: Execute all tests in test directory
        return []  # Empty list means "run all tests"

    # Fix iteration: Execute only modified tests
    fix_iterations = state.get('fix_iterations', [])

    if not fix_iterations:
        # No change tracking available, run all tests (safe fallback)
        return []

    # Get the most recent fix iteration
    latest_iteration = fix_iterations[-1]
    modified_files = latest_iteration.get('modified_files', [])

    if not modified_files:
        # No files modified, run all tests (unusual but safe)
        return []

    # Return list of modified files to execute
    # Execute Agent will construct framework-specific command for these files only
    return modified_files
```

### Usage in Phase 6 (Fix Agent - Change Tracking)

Fix Agent tracks and returns modified files after applying fixes:

```python
def track_modified_files_in_fix_agent(fixes_applied: list, test_files: dict) -> dict:
    """
    Track which test files were modified during fix application.

    This logic runs inside Fix Agent after applying fixes.

    Args:
        fixes_applied: List of Fix objects that were successfully applied
        test_files: Dict of test file paths to content

    Returns:
        Dict with modified_files list and fixes_applied count
    """
    modified_files = []
    modified_tests = []

    for fix in fixes_applied:
        # Track file path (deduplicate if same file fixed multiple times)
        if fix.file_path not in modified_files:
            modified_files.append(fix.file_path)

        # Track test name
        if fix.test_name not in modified_tests:
            modified_tests.append(fix.test_name)

    return {
        "modified_files": modified_files,
        "modified_tests": modified_tests,
        "fixes_applied": len(fixes_applied)
    }
```

### Usage in Orchestrator (Save Change Tracking)

Orchestrator saves change tracking data after each fix iteration:

```python
def save_fix_iteration_tracking(state: dict, iteration: int, modified_files: list, modified_tests: list, fixes_applied: int):
    """
    Save fix iteration tracking to state after Fix Agent completes.

    This logic runs in Orchestrator Phase 6 after Fix Agent returns.

    Args:
        state: Workflow state dict
        iteration: Current fix iteration number (1-3)
        modified_files: List of absolute paths to modified test files
        modified_tests: List of test names that were modified
        fixes_applied: Number of fixes successfully applied
    """
    import datetime

    # Initialize fix_iterations array if not exists
    if 'fix_iterations' not in state:
        state['fix_iterations'] = []

    # Create iteration record
    iteration_record = {
        "iteration": iteration,
        "modified_files": modified_files,
        "modified_tests": modified_tests,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    # Append to fix_iterations array
    state['fix_iterations'].append(iteration_record)

    # Save state
    save_state(state, state['project_root'])
```

**Performance Impact**:

With smart test selection enabled:
- **Before**: 19 tests × 3 iterations = 57 test executions
- **After**: 19 tests (initial) + 3 + 2 + 1 (iterations) = 25 test executions
- **Improvement**: 56% reduction in test execution time

**Example State Frontmatter with Fix Iteration Tracking**:
```yaml
---
workflow_id: "test-loop-20260109-140000"
current_phase: "validation"
status: "in_progress"
language: "python"
framework: "pytest"
fix_iteration: 2
generated_test_files:
  - "D:/projects/myapp/tests/test_calculator.py"
  - "D:/projects/myapp/tests/test_user_service.py"
generated_tests:
  test_calculator.py:
    - "test_add_positive_numbers"
    - "test_divide_by_zero"
  test_user_service.py:
    - "TestUserCreation::test_create_user_valid_data"
fix_iterations:
  - iteration: 1
    modified_files:
      - "D:/projects/myapp/tests/test_calculator.py"
      - "D:/projects/myapp/tests/test_user_service.py"
    modified_tests:
      - "test_divide_by_zero"
      - "TestUserCreation::test_create_user_valid_data"
    fixes_applied: 2
    timestamp: "2026-01-09T14:25:30Z"
  - iteration: 2
    modified_files:
      - "D:/projects/myapp/tests/test_calculator.py"
    modified_tests:
      - "test_divide_by_zero"
    fixes_applied: 1
    timestamp: "2026-01-09T14:26:15Z"
---
```

---

## State Location Validation

**CRITICAL**: Before any state operations, validate the state location to prevent writing to incorrect directories.

### Validation Function

```python
def validate_state_location(project_root: str, plugin_repo_path: str = None) -> dict:
    """
    Validate that state location is safe to write to.

    Args:
        project_root: Absolute path to project root directory
        plugin_repo_path: Absolute path to plugin repository (to prevent writes there)

    Returns:
        dict with 'valid' (bool) and 'error' (str if invalid)
    """
    project_root_abs = os.path.abspath(project_root)
    state_dir = os.path.join(project_root_abs, '.claude')

    # Rule 1: project_root must be an absolute path
    if not os.path.isabs(project_root):
        return {
            'valid': False,
            'error': f"❌ project_root must be absolute path, got: {project_root}"
        }

    # Rule 2: project_root must exist
    if not os.path.exists(project_root_abs):
        return {
            'valid': False,
            'error': f"❌ Project root does not exist: {project_root_abs}"
        }

    # Rule 3: Must NOT be plugin repository
    if plugin_repo_path:
        plugin_repo_abs = os.path.abspath(plugin_repo_path)
        if project_root_abs.startswith(plugin_repo_abs) or project_root_abs == plugin_repo_abs:
            return {
                'valid': False,
                'error': f"❌ Cannot write state to plugin repository\n"
                         f"Project root: {project_root_abs}\n"
                         f"Plugin repo: {plugin_repo_abs}\n"
                         f"This indicates project root detection failed."
            }

    # Rule 4: project_root must be writable
    if not os.access(project_root_abs, os.W_OK):
        return {
            'valid': False,
            'error': f"❌ Project root is not writable: {project_root_abs}"
        }

    return {
        'valid': True,
        'state_directory': state_dir,
        'state_file_path': os.path.join(state_dir, '.test-loop-state.md'),
        'history_directory': os.path.join(state_dir, '.test-loop-history')
    }
```

### Validation Before State Operations

**ALWAYS validate before state operations**:

```python
# Example: Before saving state
validation_result = validate_state_location(
    project_root=project_root,
    plugin_repo_path=PLUGIN_REPO_PATH
)

if not validation_result['valid']:
    # Display error and abort
    print(validation_result['error'])
    exit(1)

# Use validated paths
state_file_path = validation_result['state_file_path']
# Proceed with state save...
```

---

## State Operations

### Save State (Atomic Write)

To save state atomically with project root:

**Required Input**: `project_root` (absolute path to project root)

**Steps**:
1. **Validate state location** (CRITICAL - DO NOT SKIP):
   ```python
   validation_result = validate_state_location(project_root, plugin_repo_path)
   if not validation_result['valid']:
       display_error(validation_result['error'])
       exit(1)
   ```

2. **Create .claude/ directory if needed**:
   ```bash
   mkdir -p "{project_root}/.claude"
   # Windows: mkdir "{project_root}\.claude" (ignores if exists)
   ```

3. **Prepare state content** (markdown with frontmatter)

4. **Write to temporary file**: `{project_root}/.claude/.test-loop-state.tmp`
   ```python
   tmp_path = os.path.join(project_root, '.claude', '.test-loop-state.tmp')
   # Use Write tool to create tmp_path
   ```

5. **Rename (atomic)**: Move `.test-loop-state.tmp` → `.test-loop-state.md`
   ```bash
   # Unix/Linux/Mac:
   mv "{project_root}/.claude/.test-loop-state.tmp" "{project_root}/.claude/.test-loop-state.md"

   # Windows:
   move "{project_root}\.claude\.test-loop-state.tmp" "{project_root}\.claude\.test-loop-state.md"
   ```

This ensures state is never corrupted by partial writes and is always in the correct project directory.

**Implementation Pattern**:
```python
def save_state(state_content: str, project_root: str, plugin_repo_path: str = None):
    # Step 1: Validate
    validation = validate_state_location(project_root, plugin_repo_path)
    if not validation['valid']:
        raise StateError(validation['error'])

    # Step 2: Create directory
    state_dir = validation['state_directory']
    os.makedirs(state_dir, exist_ok=True)

    # Step 3: Write to temp file
    tmp_file = os.path.join(state_dir, '.test-loop-state.tmp')
    # Use Write tool: write state_content to tmp_file

    # Step 4: Atomic rename
    final_file = validation['state_file_path']
    os.rename(tmp_file, final_file)  # Atomic on POSIX systems
```

### Load State

To load existing state:

**Required Input**: `project_root` (absolute path to project root)

**Steps**:
1. **Validate state location**:
   ```python
   validation_result = validate_state_location(project_root, plugin_repo_path)
   if not validation_result['valid']:
       display_error(validation_result['error'])
       exit(1)
   state_file_path = validation_result['state_file_path']
   ```

2. **Check if state file exists**:
   ```python
   if not os.path.exists(state_file_path):
       return {'error': 'No workflow to resume'}
   ```

3. **Read state file**: Use Read tool on `{project_root}/.claude/.test-loop-state.md`
   ```python
   # Use Read tool: state_file_path
   ```

4. **Parse frontmatter**: Extract YAML frontmatter fields

5. **Parse body**: Extract phase-specific content

6. **Validate**: Check required fields present and valid

7. **Return**: State object for resumption

**Error Handling**:
- If state file doesn't exist: Return error "No workflow to resume"
- If state file is corrupted: Try to recover, or report error
- If required fields missing: Report validation error

**Implementation Pattern**:
```python
def load_state(project_root: str, plugin_repo_path: str = None) -> dict:
    # Step 1: Validate
    validation = validate_state_location(project_root, plugin_repo_path)
    if not validation['valid']:
        return {'error': validation['error']}

    # Step 2: Check existence
    state_file_path = validation['state_file_path']
    if not os.path.exists(state_file_path):
        return {'error': 'No workflow to resume'}

    # Step 3: Read file
    # Use Read tool: state_file_path
    state_content = read_file(state_file_path)

    # Step 4-6: Parse and validate
    state = parse_state(state_content)
    if not validate_state_fields(state):
        return {'error': 'Invalid state fields'}

    return {'success': True, 'state': state}
```

### Archive State

When workflow completes (success or failure), archive the state:

**Required Input**: `project_root` (absolute path to project root)

**Steps**:
1. **Validate state location**:
   ```python
   validation_result = validate_state_location(project_root, plugin_repo_path)
   history_dir = validation_result['history_directory']
   ```

2. **Create archive directory**: `{project_root}/.claude/.test-loop-history/` if not exists
   ```bash
   mkdir -p "{project_root}/.claude/.test-loop-history"
   # Windows: mkdir "{project_root}\.claude\.test-loop-history"
   ```

3. **Copy current state**: Copy `.test-loop-state.md` to `.test-loop-history/test-loop-{workflow_id}.md`
   ```bash
   cp "{project_root}/.claude/.test-loop-state.md" "{project_root}/.claude/.test-loop-history/test-loop-{workflow_id}.md"
   # Windows: copy "{project_root}\.claude\.test-loop-state.md" "{project_root}\.claude\.test-loop-history\test-loop-{workflow_id}.md"
   ```

4. **Delete current state**: Remove `{project_root}/.claude/.test-loop-state.md`
   ```bash
   rm "{project_root}/.claude/.test-loop-state.md"
   # Windows: del "{project_root}\.claude\.test-loop-state.md"
   ```

**Archive Naming**: `test-loop-{workflow_id}.md`
Example: `test-loop-20251208-143022.md`

### Update State

To update state during workflow:

**Required Input**: `project_root` (absolute path to project root)

**Steps**:
1. **Load current state**: Load `{project_root}/.claude/.test-loop-state.md`
   ```python
   state = load_state(project_root, plugin_repo_path)
   if 'error' in state:
       handle_error(state['error'])
   ```

2. **Modify fields**: Update frontmatter and/or body content

3. **Increment updated_at**: Set to current timestamp

4. **Save atomically**: Use atomic write pattern
   ```python
   save_state(modified_state_content, project_root, plugin_repo_path)
   ```

**Update Triggers**:
- Phase transition: Update `current_phase`, `updated_at`
- Iteration change: Update `iteration`, `updated_at`
- Status change: Update `status`, `updated_at`
- User feedback: Append to feedback history, update `updated_at`
- Agent results: Append phase results, update `updated_at`

---

## State Content Sections

### Section 1: Workflow Overview

Required content:
- Workflow ID
- Current status
- Current phase and progress indicator
- Iteration count
- Timestamps (started, last updated)

### Section 2: Workflow Progress

Checklist showing all phases:
- [x] Completed phases
- [ ] Current phase (marked with **CURRENT**)
- [ ] Pending phases

### Section 3: Phase Results

For each completed phase, include:
- **Phase Name**: Analysis, Plan Generation, etc.
- **Completion Timestamp**: When phase finished
- **Duration**: How long phase took
- **Results**: Phase-specific output (analysis results, test plan, generated code, etc.)
- **Status**: Success, approved, changes requested, etc.

### Section 4: Current Phase Details

Detailed information about current phase:
- What's happening
- What's needed (if awaiting approval)
- Options available
- Context for resumption

### Section 5: User Feedback History

For workflows with approval gates, track:
- Iteration number
- Phase name
- User action (approved, request changes, reject)
- User feedback text
- Timestamp

### Section 6: Next Steps

Clear guidance on what happens when workflow resumes:
- Which phase will continue
- What action is needed
- What happens based on user decisions

---

## State Management Patterns

### Pattern 1: Phase Transition

When moving from one phase to another:

```markdown
## Phase Transition Pattern

1. Complete current phase (agent finishes)
2. Append phase results to state
3. Update frontmatter:
   - `current_phase` ← next phase name
   - `updated_at` ← current timestamp
4. Save state atomically
5. Display progress to user
6. Start next phase
```

### Pattern 2: Approval Gate

When waiting for user approval:

```markdown
## Approval Gate Pattern

1. Generate content for approval (plan, code, etc.)
2. Append content to state
3. Update frontmatter:
   - `status` ← "awaiting_approval"
   - `current_phase` ← approval phase name
   - `updated_at` ← current timestamp
4. Save state atomically
5. Display content to user
6. Use AskUserQuestion tool
7. When user responds:
   - Append feedback to state
   - If approved: Update status, continue
   - If changes requested: Increment iteration, regenerate
   - If rejected: Update status to "cancelled", archive state
8. Save state atomically
```

### Pattern 3: Iteration

When user requests changes:

```markdown
## Iteration Pattern

1. User provides feedback via AskUserQuestion
2. Append feedback to state
3. Update frontmatter:
   - `iteration` ← iteration + 1
   - `updated_at` ← current timestamp
4. Save state atomically
5. Check iteration limit:
   - If < max_iterations: Return to previous phase with feedback
   - If >= max_iterations: Inform user, ask to continue or abort
6. Regenerate with feedback incorporated
```

### Pattern 4: Workflow Completion

When workflow finishes:

```markdown
## Completion Pattern

1. Final phase completes (validation)
2. Update frontmatter:
   - `status` ← "completed" or "failed"
   - `updated_at` ← current timestamp
3. Save state atomically
4. Display final summary to user
5. Archive state to `.test-loop-history/`
6. Delete current state file
```

### Pattern 5: Workflow Resumption

When user runs `/test-resume`:

```markdown
## Resumption Pattern

1. Detect project root (use Project Root Detection skill)
2. Validate state location
3. Load state from `{project_root}/.claude/.test-loop-state.md`
4. Parse frontmatter and body
5. Validate state (check required fields)
6. Display current status to user:
   - Workflow ID
   - Current phase
   - What happened so far
   - What's next
7. Ask user to confirm resumption
8. If confirmed:
   - Continue from `current_phase`
   - If awaiting approval: Re-prompt for decision
   - If in progress: Resume phase execution
9. Continue workflow as normal
```

**Implementation**:
```python
# Step 1: Detect project root
project_result = find_project_root(
    target_path=os.getcwd(),  # Or user-provided path
    plugin_repo_path=PLUGIN_REPO_PATH
)
if project_result['error']:
    display_error(project_result['error'])
    exit(1)

project_root = project_result['project_root']

# Step 2-3: Validate and load state
state = load_state(project_root, PLUGIN_REPO_PATH)
if 'error' in state:
    display_error(state['error'])
    exit(1)

# Continue with resumption...
```

---

## Error Handling

### Corrupted State File

If state file exists but cannot be parsed:

```markdown
❌ Error: Corrupted workflow state

The workflow state file at {project_root}/.claude/.test-loop-state.md could not be loaded.

Possible causes:
- File was manually edited and has syntax errors
- Partial write occurred (process interrupted)
- File system corruption

Recommendations:
1. Check {project_root}/.claude/.test-loop-history/ for recent archived states
2. Manually inspect {project_root}/.claude/.test-loop-state.md
3. Start a new workflow with /test-loop
```

### Missing State File

If `/test-resume` is run with no state file:

```markdown
⚠️ No workflow to resume

No active workflow state found at {project_root}/.claude/.test-loop-state.md

Possible reasons:
- No workflow was started
- Previous workflow completed and was archived
- State file was manually deleted
- Wrong directory (not in a project with workflow state)

Recommendations:
1. Check {project_root}/.claude/.test-loop-history/ for archived workflows
2. Ensure you're in the correct project directory
3. Start a new workflow with /test-loop
```

### State Validation Errors

If state file has missing or invalid fields:

```markdown
❌ Error: Invalid workflow state

The workflow state is missing required fields:
- Missing: workflow_id
- Invalid: current_phase (value: "unknown_phase")

Recommendations:
1. Check {project_root}/.claude/.test-loop-history/ for recent valid states
2. Start a new workflow with /test-loop
```

---

## Best Practices

### 1. Always Save State After Critical Operations

Save state after:
- Phase completion
- User approval/rejection
- Iteration change
- Status change
- Error occurs

**Rationale**: Ensures workflow can be resumed from latest checkpoint.

### 2. Use Atomic Writes

Always use temp file + rename pattern for state saves.

**Rationale**: Prevents state corruption from partial writes.

### 3. Include Sufficient Context

State should contain enough information to:
- Resume workflow without asking user to repeat information
- Debug issues if workflow fails
- Provide user visibility into what happened

**Rationale**: Improves resumption success rate and user experience.

### 4. Validate State on Load

Always validate state when loading:
- Check required fields present
- Validate field types and values
- Check phase names are valid
- Verify workflow_id format

**Rationale**: Catches corruption early before attempting resumption.

### 5. Archive Completed Workflows

Always archive state when workflow completes or fails.

**Rationale**: Preserves history for debugging and user reference.

### 6. Keep State Human-Readable

Use clear section headers, formatting, and descriptions.

**Rationale**: Users can inspect state files directly for debugging.

### 7. Limit State File Size

Avoid storing very large content (e.g., entire source code, massive test outputs).

**Rationale**: Keep state files manageable and fast to load.

**Guidelines**:
- Store references (file paths) instead of full file contents when possible
- Truncate very long outputs (e.g., show first 100 lines of test output)
- Link to other files (`.last-analysis.md`, `.last-execution.md`) for full content

---

## State File Locations

**IMPORTANT**: All paths below are relative to `{project_root}`, not current working directory.

### Active State
- **Path**: `{project_root}/.claude/.test-loop-state.md`
- **Purpose**: Current active workflow state
- **Lifecycle**: Created when workflow starts, updated during workflow, deleted/archived when workflow completes

### Archived States
- **Path**: `{project_root}/.claude/.test-loop-history/test-loop-{workflow_id}.md`
- **Purpose**: Historical record of completed workflows
- **Lifecycle**: Created when workflow completes or fails

### Supporting State Files

These are NOT part of core state management but work alongside it:

- `{project_root}/.claude/.last-analysis.md` - Most recent analysis results
- `{project_root}/.claude/.last-test-plan.md` - Most recent test plan
- `{project_root}/.claude/.last-execution.md` - Most recent test execution results
- `{project_root}/.claude/.last-validation.md` - Most recent validation report

These files are updated by `/test-analyze`, `/test-generate`, and `/test-loop` commands and provide detailed content that state files reference.

---

## Implementation Checklist

When implementing state management:

- [ ] **Obtain project_root** from orchestrator (detected via Project Root Detection skill)
- [ ] **Validate state location** before any state operations
- [ ] Create `{project_root}/.claude/` directory if not exists
- [ ] Create `{project_root}/.claude/.test-loop-history/` directory if not exists
- [ ] Generate unique `workflow_id` (use timestamp: `test-loop-YYYYMMDD-HHMMSS`)
- [ ] Initialize state with frontmatter and basic sections
- [ ] Use atomic write pattern (temp file + rename)
- [ ] Update state after each phase
- [ ] Save state before approval gates
- [ ] Validate state on load
- [ ] Handle missing/corrupted state gracefully
- [ ] Archive state on completion
- [ ] Clean up current state after archiving
- [ ] **Always use project_root parameter** - never use relative paths from cwd

---

## Testing State Management

To test state management:

1. **Test Save**: Create state, save, verify file exists and is readable
2. **Test Load**: Save state, load it, verify all fields parsed correctly
3. **Test Update**: Save state, update fields, verify changes persisted
4. **Test Atomic Write**: Simulate interruption during write, verify no corruption
5. **Test Archive**: Complete workflow, verify state archived to history
6. **Test Resume**: Save state, restart session, load state, verify resumption works
7. **Test Error Handling**: Test with missing file, corrupted file, invalid fields

---

## Example State Files

### Example 1: Analysis Phase

```markdown
---
workflow_id: "test-loop-20251208-140000"
current_phase: "analysis"
iteration: 1
status: "in_progress"
test_type: "unit"
target_path: "src/"
created_at: "2025-12-08T14:00:00Z"
updated_at: "2025-12-08T14:00:15Z"
---

# Test Loop Workflow State

**Workflow ID**: test-loop-20251208-140000
**Status**: Analyzing code
**Current Phase**: Analysis (Phase 1 of 7)
**Started**: 2025-12-08 14:00:00
**Last Updated**: 2025-12-08 14:00:15

---

## Workflow Progress

- [ ] Phase 1: Analysis - **CURRENT** (in progress)
- [ ] Phase 2: Plan Generation
- [ ] Phase 3: Plan Approval
- [ ] Phase 4: Code Generation
- [ ] Phase 5: Code Approval
- [ ] Phase 6: Test Execution
- [ ] Phase 7: Validation

---

## Phase 1: Analysis

**Started**: 2025-12-08 14:00:00
**Status**: Running analyze-agent

Analyzing codebase at: src/
```

### Example 2: Awaiting Plan Approval

```markdown
---
workflow_id: "test-loop-20251208-140000"
current_phase: "plan_approval"
iteration: 1
status: "awaiting_approval"
test_type: "unit"
target_path: "src/"
language: "python"
framework: "pytest"
created_at: "2025-12-08T14:00:00Z"
updated_at: "2025-12-08T14:02:30Z"
---

# Test Loop Workflow State

**Workflow ID**: test-loop-20251208-140000
**Status**: Awaiting plan approval
**Current Phase**: Plan Approval (Phase 3 of 7)
**Iteration**: 1 of 3
**Started**: 2025-12-08 14:00:00
**Last Updated**: 2025-12-08 14:02:30

---

## Workflow Progress

- [x] Phase 1: Analysis - Completed
- [x] Phase 2: Plan Generation - Completed
- [ ] Phase 3: Plan Approval - **CURRENT** (awaiting approval)
- [ ] Phase 4: Code Generation
- [ ] Phase 5: Code Approval
- [ ] Phase 6: Test Execution
- [ ] Phase 7: Validation

---

## Phase 1: Analysis Results

[Analysis results...]

---

## Phase 2: Test Plan

[Test plan content...]

---

## Phase 3: Plan Approval

**Status**: Awaiting Approval
**Question**: Do you approve this test plan?
**Options**: Approve / Request Changes / Reject
```

### Example 3: Workflow Completed

```markdown
---
workflow_id: "test-loop-20251208-140000"
current_phase: "validation"
iteration: 1
status: "completed"
test_type: "unit"
target_path: "src/"
language: "python"
framework: "pytest"
created_at: "2025-12-08T14:00:00Z"
updated_at: "2025-12-08T14:15:45Z"
---

# Test Loop Workflow State

**Workflow ID**: test-loop-20251208-140000
**Status**: ✅ Completed Successfully
**Completed**: 2025-12-08 14:15:45
**Total Duration**: 15 minutes 45 seconds

---

## Workflow Progress

- [x] Phase 1: Analysis - Completed
- [x] Phase 2: Plan Generation - Completed
- [x] Phase 3: Plan Approval - Approved
- [x] Phase 4: Code Generation - Completed
- [x] Phase 5: Code Approval - Approved
- [x] Phase 6: Test Execution - Completed
- [x] Phase 7: Validation - Completed

---

[All phase results...]

---

## Final Summary

All tests passed! Generated 12 tests across 3 files.
```

---

## Integration with Commands

### /test-loop Command

The `/test-loop` command uses state management to:
1. Initialize state when workflow starts
2. Update state after each phase
3. Save state before approval gates
4. Enable resumption via `/test-resume`

### /test-resume Command

The `/test-resume` command uses state management to:
1. Load state from `.claude/.test-loop-state.md`
2. Validate state
3. Display current status
4. Continue workflow from `current_phase`

### /test-generate Command

The `/test-generate` command does NOT use workflow state (it's fully automated), but it does:
1. Save supporting files (`.last-analysis.md`, `.last-test-plan.md`, etc.)
2. These files may be referenced by `/test-loop` if user switches workflows

---

This skill provides complete guidance for implementing robust state management in the automated testing plugin.
