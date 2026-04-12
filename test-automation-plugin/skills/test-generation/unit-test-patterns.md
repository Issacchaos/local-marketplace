# Unit Test Patterns

**Test Type**: Unit Testing
**Purpose**: Patterns for writing effective unit tests across languages
**Focus**: Isolation, speed, and clarity
**Version**: 1.0.0

---

## Overview

Unit tests are the foundation of a robust test suite. They test individual units of code (functions, methods, classes) in isolation from external dependencies. This document provides universal patterns for writing high-quality unit tests.

---

## Core Principles

### 1. Test Isolation

**Definition**: Each test should be completely independent and not affect other tests.

**Rules**:
- No shared mutable state between tests
- Each test sets up its own data
- Tests can run in any order
- Tests can run in parallel
- No dependencies on external systems

**Example (Python)**:
```python
# ❌ Bad - Tests share state
class TestCounter:
    counter = 0  # Shared mutable state

    def test_increment(self):
        self.counter += 1
        assert self.counter == 1  # Fails if other tests run first!

    def test_decrement(self):
        self.counter -= 1
        assert self.counter == -1  # Depends on execution order!

# ✅ Good - Tests are isolated
class TestCounter:
    def test_increment(self):
        counter = Counter()  # Fresh instance
        counter.increment()
        assert counter.value == 1

    def test_decrement(self):
        counter = Counter()  # Fresh instance
        counter.decrement()
        assert counter.value == -1
```

### 2. Test One Thing

**Definition**: Each test should verify a single behavior or concept.

**Benefits**:
- Clear test failures point to specific problems
- Easy to understand what's being tested
- Simple to maintain
- Better test documentation

**Example (Python)**:
```python
# ❌ Bad - Tests multiple concepts
def test_user_operations():
    # Creating user
    user_id = create_user("Alice")
    assert user_id is not None

    # Getting user
    user = get_user(user_id)
    assert user.name == "Alice"

    # Updating user
    update_user(user_id, name="Bob")
    user = get_user(user_id)
    assert user.name == "Bob"

    # Deleting user
    delete_user(user_id)
    assert get_user(user_id) is None

# ✅ Good - Each test verifies one concept
def test_create_user_returns_valid_id():
    user_id = create_user("Alice")
    assert user_id is not None

def test_get_user_returns_user_with_correct_name():
    user_id = create_user("Alice")
    user = get_user(user_id)
    assert user.name == "Alice"

def test_update_user_changes_name():
    user_id = create_user("Alice")
    update_user(user_id, name="Bob")
    user = get_user(user_id)
    assert user.name == "Bob"

def test_delete_user_removes_user():
    user_id = create_user("Alice")
    delete_user(user_id)
    assert get_user(user_id) is None
```

### 3. Fast Execution

**Definition**: Unit tests should execute in milliseconds.

**Guidelines**:
- No network calls (use mocks)
- No database access (use in-memory or mocks)
- No file I/O (use temporary files or mocks)
- No sleep/waits
- Minimal setup/teardown

**Target**: <100ms per test, ideally <10ms

---

## The AAA Pattern

### Arrange-Act-Assert

**Structure**:
```
def test_<what>_<condition>_<expected>():
    """Description of what is being tested."""
    # Arrange - Set up test data and conditions
    [setup code]

    # Act - Execute the code under test
    [action code]

    # Assert - Verify the results
    [assertion code]
```

### Pattern Variants

#### Standard AAA

```python
def test_add_positive_numbers_returns_sum():
    """Test that adding positive numbers returns correct sum."""
    # Arrange
    calculator = Calculator()
    a = 5
    b = 3
    expected = 8

    # Act
    result = calculator.add(a, b)

    # Assert
    assert result == expected
```

#### Given-When-Then (BDD Style)

```python
def test_add_positive_numbers_returns_sum():
    """
    Test addition of positive numbers.

    Given: A calculator and two positive numbers (5 and 3)
    When: add() is called
    Then: Returns 8
    """
    # Given
    calculator = Calculator()
    a, b = 5, 3

    # When
    result = calculator.add(a, b)

    # Then
    assert result == 8
```

#### Combined Act-Assert (for exceptions)

```python
def test_divide_by_zero_raises_error():
    """Test that dividing by zero raises ValueError."""
    # Arrange
    calculator = Calculator()

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10, 0)
```

---

## Test Structure Templates

### Testing Functions

```python
def test_function_name_scenario_expected():
    """
    Test [function_name] [scenario].

    Verifies that [expected behavior].
    """
    # Arrange
    input_value = [test input]
    expected_output = [expected result]

    # Act
    actual_output = function_name(input_value)

    # Assert
    assert actual_output == expected_output
```

**Example**:
```python
def test_capitalize_lowercase_string_returns_capitalized():
    """
    Test capitalize with lowercase string.

    Verifies that a lowercase string is properly capitalized.
    """
    # Arrange
    input_str = "hello"
    expected = "Hello"

    # Act
    result = capitalize(input_str)

    # Assert
    assert result == expected
```

### Testing Methods

```python
def test_method_name_scenario_expected():
    """
    Test [ClassName.method_name] [scenario].

    Verifies that [expected behavior].
    """
    # Arrange
    instance = ClassName()
    input_value = [test input]
    expected_output = [expected result]

    # Act
    actual_output = instance.method_name(input_value)

    # Assert
    assert actual_output == expected_output
```

**Example**:
```python
def test_user_get_full_name_returns_combined_name():
    """
    Test User.get_full_name with first and last name.

    Verifies that full name is properly combined.
    """
    # Arrange
    user = User(first_name="Alice", last_name="Smith")
    expected = "Alice Smith"

    # Act
    result = user.get_full_name()

    # Assert
    assert result == expected
```

### Testing Classes

```python
def test_class_initialization_sets_correct_values():
    """
    Test [ClassName] initialization.

    Verifies that constructor sets all attributes correctly.
    """
    # Arrange
    param1 = [value1]
    param2 = [value2]

    # Act
    instance = ClassName(param1, param2)

    # Assert
    assert instance.attribute1 == param1
    assert instance.attribute2 == param2
```

**Example**:
```python
def test_user_initialization_sets_name_and_email():
    """
    Test User initialization.

    Verifies that constructor sets name and email correctly.
    """
    # Arrange
    name = "Alice"
    email = "alice@example.com"

    # Act
    user = User(name=name, email=email)

    # Assert
    assert user.name == name
    assert user.email == email
```

---

## Testing Different Scenarios

### Happy Path Tests

**Purpose**: Verify the function works correctly with valid inputs.

```python
def test_add_positive_numbers():
    """Happy path: add two positive numbers."""
    # Arrange
    calculator = Calculator()

    # Act
    result = calculator.add(5, 3)

    # Assert
    assert result == 8
```

### Edge Case Tests

**Purpose**: Test boundary conditions and special values.

**Common Edge Cases**:
- Empty inputs (empty string, empty array, None)
- Boundary values (0, -1, max int, min int)
- Single element collections
- Very large values
- Very small values

```python
def test_add_with_zero():
    """Edge case: adding zero."""
    calculator = Calculator()
    result = calculator.add(5, 0)
    assert result == 5

def test_add_negative_numbers():
    """Edge case: negative numbers."""
    calculator = Calculator()
    result = calculator.add(-5, -3)
    assert result == -8

def test_add_large_numbers():
    """Edge case: very large numbers."""
    calculator = Calculator()
    result = calculator.add(10**100, 10**100)
    assert result == 2 * (10**100)

def test_process_empty_list():
    """Edge case: empty list."""
    result = process_list([])
    assert result == []

def test_find_in_single_element_list():
    """Edge case: single element list."""
    result = find_item([42], 42)
    assert result == 0
```

### Error Case Tests

**Purpose**: Verify the function handles errors correctly.

**Common Error Cases**:
- Invalid types
- Out of range values
- Null/None inputs
- Missing required parameters
- Invalid state

```python
def test_divide_by_zero_raises_error():
    """Error case: division by zero."""
    calculator = Calculator()
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10, 0)

def test_add_invalid_type_raises_error():
    """Error case: invalid input type."""
    calculator = Calculator()
    with pytest.raises(TypeError):
        calculator.add("5", 3)

def test_get_user_nonexistent_id_returns_none():
    """Error case: nonexistent user ID."""
    result = get_user(99999)
    assert result is None

def test_negative_age_raises_error():
    """Error case: negative age."""
    with pytest.raises(ValueError, match="Age must be positive"):
        User(name="Alice", age=-1)
```

### Boundary Tests

**Purpose**: Test values at the boundaries of valid ranges.

```python
def test_age_at_minimum_boundary():
    """Boundary: minimum valid age."""
    user = User(name="Alice", age=0)
    assert user.age == 0

def test_age_at_maximum_boundary():
    """Boundary: maximum valid age."""
    user = User(name="Alice", age=150)
    assert user.age == 150

def test_age_below_minimum_raises_error():
    """Boundary: age below minimum."""
    with pytest.raises(ValueError):
        User(name="Alice", age=-1)

def test_age_above_maximum_raises_error():
    """Boundary: age above maximum."""
    with pytest.raises(ValueError):
        User(name="Alice", age=151)
```

---

## Assertion Patterns

### Equality Assertions

```python
# Exact equality
assert result == expected

# Identity
assert result is expected_object
assert result is None
assert result is True

# Membership
assert item in collection
assert key in dictionary

# Type checking
assert isinstance(result, ExpectedType)
```

### Comparison Assertions

```python
# Greater/less than
assert result > 0
assert result >= 10
assert result < 100
assert result <= 50

# Range checking
assert 0 <= result <= 100
```

### Collection Assertions

```python
# Length
assert len(result) == 3
assert len(result) > 0

# Contents
assert "item" in result
assert result == ["a", "b", "c"]
assert set(result) == {"a", "b", "c"}

# Subset/superset
assert set1.issubset(set2)
assert set1.issuperset(set2)
```

### String Assertions

```python
# Substring
assert "substring" in result
assert result.startswith("prefix")
assert result.endswith("suffix")

# Pattern matching (with regex)
import re
assert re.match(r"pattern.*", result)

# Case-insensitive
assert result.lower() == "expected".lower()
```

### Floating Point Assertions

```python
# Approximate equality (avoid == for floats)
import math
assert math.isclose(result, expected, rel_tol=1e-9)

# pytest approx
import pytest
assert result == pytest.approx(expected, rel=1e-9)
```

### Boolean Assertions

```python
# Truth testing
assert result
assert result is True
assert result is not False

# Falsiness
assert not result
assert result is False
assert result is None
```

---

## Test Organization

### Grouping Related Tests

```python
class TestCalculatorAddition:
    """Tests for Calculator addition operations."""

    def test_add_positive_numbers(self):
        """Test adding positive numbers."""
        pass

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        pass

    def test_add_with_zero(self):
        """Test adding zero."""
        pass

class TestCalculatorSubtraction:
    """Tests for Calculator subtraction operations."""

    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        pass

    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        pass
```

### Test Method Ordering

**Recommended Order**:
1. Happy path tests
2. Edge case tests
3. Error case tests
4. Boundary tests

```python
class TestUserService:
    """Tests for UserService."""

    # --- Happy Path ---

    def test_create_user_returns_user_id(self):
        pass

    def test_get_user_returns_user(self):
        pass

    # --- Edge Cases ---

    def test_create_user_with_empty_name(self):
        pass

    def test_get_user_nonexistent_id(self):
        pass

    # --- Error Cases ---

    def test_create_user_invalid_email_raises_error(self):
        pass

    def test_get_user_invalid_id_type_raises_error(self):
        pass
```

---

## Common Anti-Patterns

### ❌ Testing Multiple Things

```python
# Bad - too much in one test
def test_everything():
    assert add(1, 2) == 3
    assert subtract(5, 3) == 2
    assert multiply(2, 3) == 6
    assert divide(6, 2) == 3
```

### ❌ Unclear Test Names

```python
# Bad names
def test_1():
    pass

def test_user():
    pass

def test_stuff():
    pass

# Good names
def test_add_positive_numbers_returns_sum():
    pass

def test_user_creation_with_valid_email_succeeds():
    pass

def test_parse_json_with_invalid_syntax_raises_error():
    pass
```

### ❌ Testing Implementation Details

```python
# Bad - tests internal implementation
def test_uses_quicksort():
    sorter = Sorter()
    sorter.sort([3, 1, 2])
    assert sorter._algorithm == "quicksort"

# Good - tests behavior
def test_sort_returns_sorted_list():
    sorter = Sorter()
    result = sorter.sort([3, 1, 2])
    assert result == [1, 2, 3]
```

### ❌ Dependent Tests

```python
# Bad - tests depend on each other
class TestUserWorkflow:
    user_id = None

    def test_1_create_user(self):
        self.user_id = create_user("Alice")

    def test_2_get_user(self):
        # Depends on test_1_create_user!
        user = get_user(self.user_id)
        assert user.name == "Alice"
```

### ❌ Slow Tests

```python
# Bad - slow test (network call)
def test_fetch_user_from_api():
    response = requests.get("https://api.example.com/users/1")
    assert response.status_code == 200

# Good - fast test (mocked)
def test_fetch_user_from_api(mock_api):
    mock_api.get.return_value = Mock(status_code=200)
    response = fetch_user(1)
    assert response.status_code == 200
```

### ❌ No Assertions

```python
# Bad - no assertion
def test_create_user():
    create_user("Alice")
    # What are we testing?

# Good - clear assertion
def test_create_user_returns_id():
    user_id = create_user("Alice")
    assert user_id is not None
    assert isinstance(user_id, int)
```

---

## Test Data Management

### Inline Test Data

**When**: Simple, small test data

```python
def test_with_inline_data():
    # Arrange
    user = User(name="Alice", age=30)

    # Act
    result = user.get_summary()

    # Assert
    assert "Alice" in result
```

### Test Data Builders

**When**: Complex objects with many fields

```python
class UserBuilder:
    def __init__(self):
        self.name = "Default Name"
        self.email = "default@example.com"
        self.age = 30

    def with_name(self, name):
        self.name = name
        return self

    def with_email(self, email):
        self.email = email
        return self

    def build(self):
        return User(name=self.name, email=self.email, age=self.age)

# Usage
def test_user_with_custom_name():
    user = UserBuilder().with_name("Alice").build()
    assert user.name == "Alice"
```

### Fixtures (pytest)

**When**: Reusable test data across multiple tests

```python
@pytest.fixture
def sample_user():
    return User(name="Alice", age=30)

def test_user_name(sample_user):
    assert sample_user.name == "Alice"

def test_user_age(sample_user):
    assert sample_user.age == 30
```

---

## Checklist for Quality Unit Tests

Before considering a unit test complete, verify:

- [ ] **Isolated**: Test doesn't depend on other tests or external state
- [ ] **Fast**: Executes in milliseconds
- [ ] **Clear**: Test name clearly describes what's being tested
- [ ] **Focused**: Tests one specific behavior
- [ ] **AAA Pattern**: Clearly separated Arrange, Act, Assert sections
- [ ] **Assertions**: Has meaningful assertions that verify behavior
- [ ] **Edge Cases**: Covers boundary conditions and error cases
- [ ] **Mocked**: External dependencies are mocked
- [ ] **Maintainable**: Easy to understand and modify
- [ ] **Documentation**: Has clear docstring explaining what's tested

---

## Related Documents

- **Test Generation Skill**: `SKILL.md` - General test generation principles
- **Python Patterns**: `python-patterns.md` - Python-specific test patterns
- **Mocking Strategies**: `mocking-strategies.md` - When and how to mock dependencies

---

**Created**: 2025-12-05
**Last Updated**: 2025-12-05
**Maintained By**: Dante Automated Testing Plugin
