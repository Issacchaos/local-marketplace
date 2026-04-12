---
name: test-generation
description: Guide automated generation of high-quality unit, integration, and E2E tests. Use when writing test code to apply language-specific patterns, mocking strategies, async test patterns, and best practices for Python, JavaScript, TypeScript, Java, C#, Go, and C++.
user-invocable: false
---

# Test Generation Skill

**Skill Type**: Test Generation
**Purpose**: Guide automated generation of high-quality unit, integration, and E2E tests
**Target Users**: Write Agent, test-generation workflows
**Version**: 1.0.0

---

## Overview

This skill provides knowledge and patterns for generating comprehensive test suites across multiple programming languages and testing frameworks. It focuses on creating maintainable, readable, and effective tests that validate functionality while catching regressions.

---

## Skill Interface

### Input

The test generation skill expects the following context:

```markdown
**Analysis Context**:
- Language: [e.g., Python, JavaScript, Java]
- Framework: [e.g., pytest, Jest, JUnit]
- Test Type: [unit, integration, e2e]
- Target Code: [function, class, module to test]
- Dependencies: [external services, databases, APIs]
- Complexity Score: [low, medium, high]

**Code to Test**:
[Source code that needs tests]

**Requirements**:
- Coverage Goals: [e.g., >80% line coverage, all public methods]
- Edge Cases: [specific scenarios to test]
- Mock Strategy: [what should be mocked vs real]
```

### Output

The skill guides generation of:

```markdown
**Generated Tests**:
- Test File Path: [where to create the test]
- Test Structure: [classes, functions, fixtures]
- Test Cases: [individual test methods with AAA pattern]
- Mocks & Fixtures: [setup code and dependencies]
- Assertions: [validation logic]
- Edge Cases: [boundary and error conditions]

**Test Metadata**:
- Test Count: [number of tests generated]
- Coverage Estimate: [expected coverage %]
- Requires Review: [true/false - needs human review]
- Complexity: [test maintenance complexity]
```

---

## Generation Principles

### 1. Test Independence

**Principle**: Each test should run independently and not rely on execution order.

**Guidelines**:
- No shared mutable state between tests
- Each test sets up its own data
- Tests can run in any order or in parallel
- Use fixtures for shared setup, not globals

**Example (Python)**:
```python
# ❌ Bad - Tests depend on order
class TestUserService:
    user_id = None

    def test_create_user(self):
        self.user_id = create_user("Alice")
        assert self.user_id is not None

    def test_get_user(self):
        # Depends on test_create_user running first!
        user = get_user(self.user_id)
        assert user.name == "Alice"

# ✅ Good - Tests are independent
class TestUserService:
    @pytest.fixture
    def user_id(self):
        return create_user("Alice")

    def test_create_user(self):
        user_id = create_user("Alice")
        assert user_id is not None

    def test_get_user(self, user_id):
        user = get_user(user_id)
        assert user.name == "Alice"
```

### 2. Clear Test Structure

**Principle**: Tests should follow a clear, readable pattern (AAA: Arrange-Act-Assert).

**Pattern**:
```
def test_what_when_then():
    """Describe what is being tested."""
    # Arrange - Set up test data and conditions
    [setup code]

    # Act - Execute the code under test
    [action code]

    # Assert - Verify the results
    [assertion code]
```

**Benefits**:
- Easy to understand what's being tested
- Clear separation of concerns
- Simple to debug failures
- Consistent across codebase

### 3. Descriptive Test Names

**Principle**: Test names should clearly describe what is being tested and expected outcome.

**Format**: `test_<function>_<condition>_<expected_result>`

**Examples**:
- `test_add_positive_numbers_returns_sum`
- `test_divide_by_zero_raises_value_error`
- `test_login_invalid_credentials_returns_false`
- `test_fetch_user_nonexistent_id_returns_none`

### 4. Test the Behavior, Not Implementation

**Principle**: Focus on testing what the code does (behavior), not how it does it (implementation).

**Guidelines**:
- Test public interfaces, not private methods
- Don't assert on internal state unless necessary
- Allow refactoring without breaking tests
- Focus on inputs and outputs

**Example (Python)**:
```python
# ❌ Bad - Tests implementation details
def test_calculator_uses_correct_algorithm(self):
    calc = Calculator()
    calc.add(2, 3)
    assert calc._intermediate_result == 2  # Testing internal state
    assert calc._operation_count == 1      # Testing implementation

# ✅ Good - Tests behavior
def test_add_returns_correct_sum(self):
    calc = Calculator()
    result = calc.add(2, 3)
    assert result == 5  # Testing the observable behavior
```

### 5. One Concept Per Test

**Principle**: Each test should verify one specific behavior or concept.

**Guidelines**:
- Single logical assertion (multiple physical assertions OK)
- If test name uses "and", consider splitting
- Easier to identify what broke
- Better test documentation

**Example (Python)**:
```python
# ❌ Bad - Testing multiple concepts
def test_user_service(self):
    # Testing creation
    user_id = create_user("Alice")
    assert user_id is not None

    # Testing retrieval
    user = get_user(user_id)
    assert user.name == "Alice"

    # Testing update
    update_user(user_id, name="Bob")
    user = get_user(user_id)
    assert user.name == "Bob"

    # Testing deletion
    delete_user(user_id)
    user = get_user(user_id)
    assert user is None

# ✅ Good - Each test verifies one concept
def test_create_user_returns_valid_id(self):
    user_id = create_user("Alice")
    assert user_id is not None

def test_get_user_returns_correct_user(self):
    user_id = create_user("Alice")
    user = get_user(user_id)
    assert user.name == "Alice"

def test_update_user_changes_name(self):
    user_id = create_user("Alice")
    update_user(user_id, name="Bob")
    user = get_user(user_id)
    assert user.name == "Bob"

def test_delete_user_removes_user(self):
    user_id = create_user("Alice")
    delete_user(user_id)
    user = get_user(user_id)
    assert user is None
```

### 6. Test Edge Cases and Boundaries

**Principle**: Don't just test the happy path; test boundary conditions and error cases.

**Categories**:
- **Null/Empty**: `None`, `null`, empty strings, empty arrays
- **Boundaries**: Min/max values, array bounds, string length limits
- **Invalid Input**: Wrong types, negative numbers where positive expected
- **Error Conditions**: Network failures, timeouts, exceptions
- **Special Values**: Zero, negative numbers, very large numbers

**Example (Python)**:
```python
class TestCalculator:
    # Happy path
    def test_add_positive_numbers(self):
        assert Calculator().add(2, 3) == 5

    # Edge cases
    def test_add_zero(self):
        assert Calculator().add(5, 0) == 5

    def test_add_negative_numbers(self):
        assert Calculator().add(-2, -3) == -5

    def test_add_large_numbers(self):
        result = Calculator().add(10**100, 10**100)
        assert result == 2 * (10**100)

    # Error cases
    def test_add_invalid_type_raises_error(self):
        with pytest.raises(TypeError):
            Calculator().add("2", 3)
```

### 7. Mock External Dependencies

**Principle**: Isolate the code under test by mocking external dependencies.

**Mock When**:
- External APIs or services
- Database calls
- File system operations
- Time-dependent code
- Random number generation
- Expensive computations

**Don't Mock**:
- Simple data structures
- Pure functions
- The code under test itself
- Standard library basics (unless truly necessary)

### 8. Use Fixtures for Shared Setup

**Principle**: Extract common setup code into reusable fixtures.

**Benefits**:
- DRY (Don't Repeat Yourself)
- Consistent test data
- Clear dependencies
- Easy to maintain

---

## Test Categories

### Unit Tests

**Purpose**: Test individual functions, methods, or classes in isolation.

**Characteristics**:
- Fast execution (milliseconds)
- No external dependencies (use mocks)
- Test one unit of code
- High test count (most tests are unit tests)

**When to Generate**:
- For every public function/method
- For complex private functions
- For utility functions
- For business logic

### Integration Tests

**Purpose**: Test how multiple components work together.

**Characteristics**:
- Slower than unit tests (seconds)
- May use real dependencies (database, file system)
- Test component interactions
- Medium test count

**When to Generate**:
- For API endpoints
- For database operations
- For service-to-service communication
- For workflow orchestration

### End-to-End (E2E) Tests

**Purpose**: Test complete user workflows from start to finish.

**Characteristics**:
- Slowest tests (seconds to minutes)
- Use real systems when possible
- Test critical user journeys
- Low test count (expensive to maintain)

**When to Generate**:
- For critical user flows
- For happy path scenarios
- For regression prevention
- For smoke tests

---

## Language-Specific Patterns

This skill includes detailed patterns for:

- **Python**: `python-patterns.md` - pytest, unittest, fixtures, mocking
- **JavaScript/TypeScript**: (Phase 2) - Jest, Vitest, mocking, async patterns
- **Java**: (Phase 2) - JUnit, Mockito, annotations
- **C#**: (Phase 3) - xUnit, NUnit, MSTest
- **Go**: (Phase 3) - testing package, testify, table-driven tests
- **Rust**: (Phase 4) - Built-in test framework, proptest
- **Ruby**: (Phase 4) - RSpec, Minitest
- **C++**: (Phase 4) - Google Test, Catch2
- **C**: (Phase 4) - Unity, CMocka
- **PHP**: (Future) - PHPUnit

---

## Test Type Patterns

This skill includes detailed patterns for:

- **Unit Tests**: `unit-test-patterns.md` - AAA pattern, isolation, fast tests
- **Mocking**: `mocking-strategies.md` - When, what, and how to mock
- **Integration Tests**: (Future) - Database, API, service integration
- **E2E Tests**: (Future) - User workflows, browser automation

---

## Generation Workflow

### Step 1: Analyze Target Code

**Actions**:
1. Identify code structure (functions, classes, modules)
2. Determine complexity (simple, medium, complex)
3. Identify dependencies (external services, databases)
4. Find edge cases (boundary conditions, error scenarios)

**Output**: Analysis report with test targets prioritized

### Step 2: Select Test Patterns

**Actions**:
1. Choose appropriate test type (unit, integration, e2e)
2. Select language-specific patterns
3. Determine fixture requirements
4. Plan mock strategy

**Output**: Test plan with patterns to use

### Step 3: Generate Test Code

**Actions**:
1. Load appropriate template
2. Fill in placeholders with actual values
3. Generate test cases for each scenario
4. Add fixtures and mocks as needed
5. Include edge cases and error handling

**Output**: Syntactically valid test code

### Step 4: Validate Generated Tests

**Actions**:
1. Check syntax validity
2. Verify test independence
3. Ensure proper naming conventions
4. Validate coverage of edge cases
5. Review mock usage

**Output**: Validated test code ready for execution

---

## Quality Criteria

Generated tests should meet these criteria:

### Correctness
- [ ] Tests validate the actual behavior
- [ ] Assertions are meaningful
- [ ] Edge cases are covered
- [ ] Error conditions are tested

### Maintainability
- [ ] Clear, descriptive test names
- [ ] Follows AAA pattern
- [ ] Proper use of fixtures
- [ ] Minimal duplication

### Independence
- [ ] Tests run in any order
- [ ] No shared mutable state
- [ ] Each test sets up own data
- [ ] Clean teardown

### Performance
- [ ] Unit tests run quickly (<100ms)
- [ ] Appropriate use of mocking
- [ ] No unnecessary setup
- [ ] Efficient assertions

### Readability
- [ ] Clear test structure
- [ ] Good variable names
- [ ] Appropriate comments
- [ ] Consistent style

---

## Example Usage

### Input to Skill

```markdown
**Context**:
- Language: Python
- Framework: pytest
- Test Type: unit
- Target: `calculator.py` - `add()` function

**Code**:
```python
def add(a: int, b: int) -> int:
    """Add two numbers and return the sum."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers")
    return a + b
```

**Requirements**:
- Test happy path
- Test edge cases (zero, negative)
- Test error handling (invalid types)
```

### Output from Skill

```python
import pytest
from calculator import add

class TestAdd:
    """Test suite for add() function."""

    def test_add_positive_numbers_returns_sum(self):
        """Test adding two positive integers."""
        # Arrange
        a = 5
        b = 3
        expected = 8

        # Act
        result = add(a, b)

        # Assert
        assert result == expected

    def test_add_negative_numbers_returns_sum(self):
        """Test adding two negative integers."""
        # Arrange
        a = -5
        b = -3
        expected = -8

        # Act
        result = add(a, b)

        # Assert
        assert result == expected

    def test_add_with_zero_returns_other_number(self):
        """Test adding zero returns the other number."""
        # Arrange
        a = 5
        b = 0
        expected = 5

        # Act
        result = add(a, b)

        # Assert
        assert result == expected

    def test_add_invalid_type_raises_type_error(self):
        """Test that invalid types raise TypeError."""
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="Both arguments must be integers"):
            add("5", 3)

    @pytest.mark.parametrize("a, b, expected", [
        (0, 0, 0),
        (1, 1, 2),
        (100, 200, 300),
        (-1, 1, 0),
        (10**6, 10**6, 2 * 10**6),
    ], ids=[
        "both_zero",
        "small_positive",
        "large_positive",
        "opposite_signs",
        "very_large_numbers"
    ])
    def test_add_various_inputs(self, a, b, expected):
        """Test add() with various input combinations."""
        result = add(a, b)
        assert result == expected
```

---

## Integration with Other Skills

### Framework Detection
- Use detected framework to select appropriate patterns
- Adapt test structure to framework conventions
- Use framework-specific features (fixtures, markers, etc.)

### Result Parsing
- Generate tests that produce parseable output
- Include test IDs for traceability
- Use descriptive names for clear failure messages

### Templates
- Reference language-specific templates
- Fill template placeholders with generated values
- Maintain template structure and style

---

## Anti-Patterns to Avoid

### ❌ Testing Framework Code
```python
# Don't test that the framework works
def test_pytest_fixture_works(self, database):
    assert database is not None
```

### ❌ Over-Mocking
```python
# Don't mock everything, including simple objects
def test_user_name(self):
    mock_user = Mock()
    mock_user.name = "Alice"
    assert mock_user.name == "Alice"  # Useless test
```

### ❌ Unclear Test Names
```python
# Names should be descriptive
def test_1(self):  # What does this test?
    pass

def test_user(self):  # Too vague
    pass
```

### ❌ Multiple Unrelated Assertions
```python
# Each test should verify one concept
def test_everything(self):
    assert add(1, 2) == 3
    assert subtract(5, 3) == 2
    assert multiply(2, 3) == 6
    assert divide(6, 2) == 3
```

### ❌ Testing Implementation Details
```python
# Test behavior, not implementation
def test_uses_correct_algorithm(self):
    calc = Calculator()
    assert calc._algorithm == "fast_add"  # Internal detail
```

### ❌ Testing Pure Delegation (No Logic in the Method Under Test)
When a method does nothing but forward a call to one dependency and return the result unchanged, the test exercises the mock, not the production code. Only test delegation when the method adds routing, transformation, error handling, or business logic on top of the forwarded call.
```kotlin
// source: fun setPendingItemsCount(n: Int) = repository.setPendingItemsCount(n)
// ❌ no logic here — this test covers the mock, not the class under test
fun test_setPendingItemsCount_delegates() = runTest {
    sut.setPendingItemsCount(42)
    coVerify { repository.setPendingItemsCount(42) }
}
```

### ❌ Testing Constructor Plumbing / Parameter Pass-Through
Verifying that a constructor argument ends up in a property or URL as-is tests the language runtime, not application behaviour. Skip unless the value is transformed (formatted, encoded, combined with other fields, validated, etc.).

### ❌ Testing Constants and Hard-Coded Strings
A test whose only assertion is `assertEquals("SomeString", sut.someConstant)` will never catch a real bug — it fails only if someone renames the constant, which is a refactor, not a regression. Remove it.

### ❌ Symmetric Method-Pair Duplicates With Identical Assertion Structure
When two methods (e.g. `startedSpeaking` / `stoppedSpeaking`, `enabled` / `disabled` variants) share the same internal logic, one test is sufficient. The second adds noise without covering a new code path. Only add the second test when the assertion is *different* — a different output value, a different event type, or a different side-effect.

### ❌ Repeating the Same Guard-Clause Test Across Sibling Branches
When multiple handlers (e.g. different notification types) share an identical early-return guard (`if (account == null) return`), test that guard **once** on a representative handler. Duplicating the identical arrange/act/assert across every sibling produces correlated failures and adds no safety.

---

## Skill Maintenance

**Version**: 1.0.0 (Phase 1 - Python/pytest focus)

**Future Enhancements**:
- Phase 2: JavaScript/TypeScript patterns (Jest, Vitest)
- Phase 3: Java patterns (JUnit, Mockito)
- Phase 4: Multi-language expansion (C#, Go, Rust, Ruby, C++, C)
- Property-based testing patterns
- Mutation testing guidance
- Performance testing patterns

**Related Skills**:
- Framework Detection: `skills/framework-detection/SKILL.md`
- Result Parsing: `skills/result-parsing/SKILL.md`
- Templates: `skills/templates/python-pytest-template.md`

---

**Created**: 2025-12-05
**Last Updated**: 2025-12-05
**Maintained By**: Dante Automated Testing Plugin
