# Python Test Generation Patterns

**Language**: Python
**Framework Focus**: pytest, unittest
**Purpose**: Python-specific patterns for generating high-quality tests
**Version**: 1.0.0

---

## Overview

This document provides Python-specific patterns for test generation, focusing on pytest (primary) and unittest (secondary). It covers Python language features, testing idioms, and framework-specific patterns.

---

## Python Testing Fundamentals

### Testing Frameworks

#### pytest (Recommended)

**Characteristics**:
- Simple, Pythonic syntax using `assert`
- Powerful fixture system
- Excellent plugin ecosystem
- Parametrization support
- Detailed assertion introspection

**When to Use**:
- New projects (default choice)
- Projects needing advanced fixtures
- Projects using parametrized tests
- Modern Python applications

#### unittest (Standard Library)

**Characteristics**:
- Part of Python standard library
- JUnit-inspired (xUnit style)
- Class-based test structure
- setUp/tearDown methods

**When to Use**:
- Legacy projects already using unittest
- Projects avoiding external dependencies
- Teams familiar with xUnit frameworks

---

## File Organization

### Directory Structure

```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── calculator.py
│       ├── user_service.py
│       └── api/
│           ├── __init__.py
│           └── endpoints.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_calculator.py
│   │   └── test_user_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api_endpoints.py
│   └── e2e/
│       ├── __init__.py
│       └── test_user_workflows.py
├── pytest.ini                    # pytest configuration
└── requirements-dev.txt          # Test dependencies
```

### Naming Conventions

**Test Files**:
- Pattern: `test_*.py` or `*_test.py`
- Match source file: `calculator.py` → `test_calculator.py`
- Location: Mirror source structure in `tests/` directory

**Test Classes**:
- Pattern: `Test*` (PascalCase, no `()` inheritance unless using unittest)
- Example: `TestCalculator`, `TestUserService`
- Group related tests together

**Test Functions**:
- Pattern: `test_*` (snake_case)
- Format: `test_<function>_<scenario>_<expected>`
- Examples:
  - `test_add_positive_numbers_returns_sum`
  - `test_divide_by_zero_raises_value_error`
  - `test_login_invalid_password_returns_false`

---

## Test Structure Patterns

### pytest Pattern (Recommended)

```python
"""
Test module for calculator operations.

This module tests the Calculator class, covering:
- Basic arithmetic operations
- Edge cases (zero, negative numbers)
- Error handling (invalid inputs)
"""

import pytest
from myapp.calculator import Calculator

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def calculator():
    """Provide a Calculator instance for tests."""
    return Calculator()

# ============================================================================
# Test Class: TestCalculator
# ============================================================================

class TestCalculator:
    """Test suite for Calculator class."""

    # ------------------------------------------------------------------------
    # Happy Path Tests
    # ------------------------------------------------------------------------

    def test_add_positive_numbers_returns_sum(self, calculator):
        """
        Test adding two positive numbers.

        Given: Two positive integers (5 and 3)
        When: add() is called
        Then: Returns 8
        """
        # Arrange
        a = 5
        b = 3
        expected = 8

        # Act
        result = calculator.add(a, b)

        # Assert
        assert result == expected
        assert isinstance(result, int)

    # ------------------------------------------------------------------------
    # Edge Case Tests
    # ------------------------------------------------------------------------

    def test_add_zero_returns_other_number(self, calculator):
        """Test that adding zero returns the other number."""
        # Arrange
        a = 5
        b = 0

        # Act
        result = calculator.add(a, b)

        # Assert
        assert result == a

    # ------------------------------------------------------------------------
    # Error Handling Tests
    # ------------------------------------------------------------------------

    def test_divide_by_zero_raises_value_error(self, calculator):
        """Test that dividing by zero raises ValueError."""
        # Arrange
        a = 10
        b = 0

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(a, b)
```

### unittest Pattern (Alternative)

```python
"""Test module for calculator operations using unittest."""

import unittest
from myapp.calculator import Calculator

class TestCalculator(unittest.TestCase):
    """Test suite for Calculator class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.calculator = Calculator()

    def tearDown(self):
        """Clean up after each test method."""
        self.calculator = None

    def test_add_positive_numbers_returns_sum(self):
        """Test adding two positive numbers."""
        # Arrange
        a = 5
        b = 3
        expected = 8

        # Act
        result = self.calculator.add(a, b)

        # Assert
        self.assertEqual(result, expected)
        self.assertIsInstance(result, int)

    def test_divide_by_zero_raises_value_error(self):
        """Test that dividing by zero raises ValueError."""
        # Arrange
        a = 10
        b = 0

        # Act & Assert
        with self.assertRaises(ValueError):
            self.calculator.divide(a, b)

if __name__ == '__main__':
    unittest.main()
```

---

## Python-Specific Test Patterns

### Testing Python Data Structures

#### Lists/Arrays

```python
def test_list_operations():
    """Test list manipulation functions."""
    # Arrange
    items = [1, 2, 3]

    # Act
    result = process_list(items)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0] == 1
    assert 2 in result
    assert result == [1, 2, 3]  # Exact match

def test_empty_list_returns_empty():
    """Test handling of empty lists."""
    # Arrange
    items = []

    # Act
    result = process_list(items)

    # Assert
    assert result == []
    assert len(result) == 0
```

#### Dictionaries

```python
def test_dictionary_operations():
    """Test dictionary manipulation."""
    # Arrange
    data = {"name": "Alice", "age": 30}

    # Act
    result = process_dict(data)

    # Assert
    assert isinstance(result, dict)
    assert "name" in result
    assert result["name"] == "Alice"
    assert result.get("age") == 30
    assert len(result) == 2

def test_missing_key_returns_default():
    """Test accessing missing dictionary keys."""
    # Arrange
    data = {"name": "Alice"}

    # Act
    result = data.get("age", 0)

    # Assert
    assert result == 0
```

#### Sets

```python
def test_set_operations():
    """Test set operations."""
    # Arrange
    set1 = {1, 2, 3}
    set2 = {3, 4, 5}

    # Act
    union = set1 | set2
    intersection = set1 & set2
    difference = set1 - set2

    # Assert
    assert union == {1, 2, 3, 4, 5}
    assert intersection == {3}
    assert difference == {1, 2}
```

### Testing Type Hints

```python
from typing import List, Dict, Optional, Union

def test_type_hints_respected():
    """Test that functions respect type hints."""
    # Arrange
    data: List[int] = [1, 2, 3]

    # Act
    result: int = sum_list(data)

    # Assert
    assert isinstance(result, int)
    assert result == 6

def test_optional_parameter():
    """Test function with Optional parameter."""
    # Arrange
    value: Optional[str] = None

    # Act
    result = process_optional(value)

    # Assert
    assert result is None

def test_union_types():
    """Test function accepting multiple types."""
    # Test with int
    result1 = process_union(42)
    assert isinstance(result1, str)

    # Test with string
    result2 = process_union("hello")
    assert isinstance(result2, str)
```

### Testing Generators and Iterators

```python
def test_generator_yields_values():
    """Test that generator yields expected values."""
    # Arrange
    gen = number_generator(3)

    # Act
    values = list(gen)

    # Assert
    assert values == [0, 1, 2]

def test_generator_is_lazy():
    """Test that generator doesn't evaluate immediately."""
    # Arrange & Act
    gen = expensive_generator()

    # Assert - generator created but not executed
    assert hasattr(gen, '__iter__')
    assert hasattr(gen, '__next__')

def test_iterator_protocol():
    """Test custom iterator implementation."""
    # Arrange
    iterator = CustomIterator([1, 2, 3])

    # Act
    first = next(iterator)
    second = next(iterator)

    # Assert
    assert first == 1
    assert second == 2
```

### Testing Context Managers

```python
def test_context_manager_cleans_up():
    """Test that context manager properly cleans up resources."""
    # Arrange
    resource_created = False
    resource_cleaned = False

    # Act
    with ResourceManager() as resource:
        resource_created = resource.is_open()
    resource_cleaned = not resource.is_open()

    # Assert
    assert resource_created
    assert resource_cleaned

def test_context_manager_handles_exceptions():
    """Test context manager cleanup even when exception occurs."""
    # Arrange
    resource = None

    # Act & Assert
    with pytest.raises(ValueError):
        with ResourceManager() as resource:
            raise ValueError("Test error")

    # Verify cleanup happened despite exception
    assert not resource.is_open()
```

### Testing Decorators

```python
def test_decorator_preserves_function():
    """Test that decorator doesn't break the function."""
    # Arrange
    @my_decorator
    def sample_function(x):
        return x * 2

    # Act
    result = sample_function(5)

    # Assert
    assert result == 10

def test_decorator_adds_functionality():
    """Test that decorator adds expected behavior."""
    # Arrange
    call_count = []

    def counting_decorator(func):
        def wrapper(*args, **kwargs):
            call_count.append(1)
            return func(*args, **kwargs)
        return wrapper

    @counting_decorator
    def sample_function():
        return "result"

    # Act
    result = sample_function()

    # Assert
    assert result == "result"
    assert len(call_count) == 1
```

### Testing Properties

```python
class TestUserProperties:
    """Test User class properties."""

    def test_full_name_property_returns_combined_name(self):
        """Test that full_name property combines first and last name."""
        # Arrange
        user = User(first_name="Alice", last_name="Smith")

        # Act
        full_name = user.full_name

        # Assert
        assert full_name == "Alice Smith"

    def test_age_property_is_read_only(self):
        """Test that age property cannot be set directly."""
        # Arrange
        user = User(birth_year=1990)

        # Act & Assert
        with pytest.raises(AttributeError):
            user.age = 25

    def test_email_setter_validates_format(self):
        """Test that email setter validates email format."""
        # Arrange
        user = User()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            user.email = "invalid-email"
```

---

## Fixture Patterns

### Basic Fixtures

```python
@pytest.fixture
def sample_user():
    """Provide a sample User instance."""
    return User(name="Alice", email="alice@example.com")

@pytest.fixture
def sample_users():
    """Provide a list of sample users."""
    return [
        User(name="Alice", email="alice@example.com"),
        User(name="Bob", email="bob@example.com"),
        User(name="Charlie", email="charlie@example.com"),
    ]

# Usage
def test_user_name(sample_user):
    assert sample_user.name == "Alice"

def test_multiple_users(sample_users):
    assert len(sample_users) == 3
```

### Fixtures with Setup/Teardown

```python
@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    # Setup
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    yield file_path  # Provide to test

    # Teardown (optional, tmp_path auto-cleans)
    if file_path.exists():
        file_path.unlink()

@pytest.fixture
def database_connection():
    """Provide database connection with cleanup."""
    # Setup
    conn = create_connection(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")

    yield conn

    # Teardown
    conn.close()
```

### Parametrized Fixtures

```python
@pytest.fixture(params=[1, 2, 3])
def number(request):
    """Provide different numbers to tests."""
    return request.param

def test_with_multiple_numbers(number):
    """This test runs 3 times with different numbers."""
    assert number > 0

@pytest.fixture(params=["pytest", "unittest", "nose"])
def framework_name(request):
    """Provide different framework names."""
    return request.param
```

### Fixtures with Scope

```python
@pytest.fixture(scope="function")  # Default: runs for each test
def function_scope_fixture():
    return "function"

@pytest.fixture(scope="class")  # Runs once per test class
def class_scope_fixture():
    return ExpensiveResource()

@pytest.fixture(scope="module")  # Runs once per module
def module_scope_fixture():
    return Database.connect()

@pytest.fixture(scope="session")  # Runs once per test session
def session_scope_fixture():
    return GlobalConfiguration.load()
```

### Fixture Composition

```python
@pytest.fixture
def database():
    """Provide database connection."""
    return Database.connect(":memory:")

@pytest.fixture
def user_repo(database):
    """Provide UserRepository (depends on database fixture)."""
    return UserRepository(database)

@pytest.fixture
def user_service(user_repo):
    """Provide UserService (depends on user_repo fixture)."""
    return UserService(user_repo)

# Test gets all three fixtures automatically
def test_create_user(user_service, database):
    user_service.create_user("Alice")
    users = database.query("SELECT * FROM users")
    assert len(users) == 1
```

---

## Parametrized Tests

### Basic Parametrization

```python
@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_parametrized(a, b, expected):
    """Test add with multiple input combinations."""
    calculator = Calculator()
    result = calculator.add(a, b)
    assert result == expected
```

### Parametrization with IDs

```python
@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
], ids=["positive", "zeros", "mixed_signs"])
def test_add_with_ids(a, b, expected):
    """Test add with descriptive test IDs."""
    result = Calculator().add(a, b)
    assert result == expected
```

### Parametrization with pytest.param

```python
@pytest.mark.parametrize("input, expected", [
    pytest.param(5, 25, id="small_number"),
    pytest.param(0, 0, id="zero"),
    pytest.param(-5, 25, id="negative_number"),
    pytest.param(10**6, 10**12, id="large_number"),
    pytest.param("5", None, marks=pytest.mark.xfail(raises=TypeError), id="invalid_type"),
])
def test_square(input, expected):
    """Test square function with various inputs."""
    if expected is None:
        with pytest.raises(TypeError):
            square(input)
    else:
        result = square(input)
        assert result == expected
```

### Multiple Parameter Sets

```python
@pytest.mark.parametrize("x", [0, 1, 2])
@pytest.mark.parametrize("y", [0, 1, 2])
def test_grid(x, y):
    """Test all combinations: (0,0), (0,1), (0,2), (1,0), ..., (2,2)."""
    # This creates 9 tests (3 x 3)
    result = compute(x, y)
    assert result >= 0
```

---

## Async Testing Patterns

### Basic Async Tests

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    # Arrange
    service = AsyncService()

    # Act
    result = await service.fetch_data()

    # Assert
    assert result is not None

@pytest.mark.asyncio
async def test_async_with_timeout():
    """Test async function with timeout."""
    # Act & Assert
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(), timeout=1.0)
```

### Async Fixtures

```python
@pytest.fixture
async def async_client():
    """Provide async HTTP client."""
    client = AsyncHTTPClient()
    await client.connect()

    yield client

    await client.disconnect()

@pytest.mark.asyncio
async def test_with_async_fixture(async_client):
    """Test using async fixture."""
    response = await async_client.get("/api/users")
    assert response.status == 200
```

### Concurrent Async Tests

```python
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test multiple async requests concurrently."""
    # Arrange
    client = AsyncClient()
    urls = ["/api/user/1", "/api/user/2", "/api/user/3"]

    # Act
    responses = await asyncio.gather(*[client.get(url) for url in urls])

    # Assert
    assert len(responses) == 3
    assert all(r.status == 200 for r in responses)
```

---

## Mocking Patterns

See `mocking-strategies.md` for detailed mocking patterns.

**Quick Reference**:

```python
from unittest.mock import Mock, MagicMock, patch, call

# Mock object
mock_obj = Mock()
mock_obj.method.return_value = "result"

# Patch decorator
@patch('module.external_api')
def test_with_patch(mock_api):
    mock_api.get.return_value = {"data": "test"}
    result = fetch_data()
    assert result == {"data": "test"}

# Patch context manager
def test_with_context():
    with patch('module.external_api') as mock_api:
        mock_api.get.return_value = {"data": "test"}
        result = fetch_data()
        assert result == {"data": "test"}
```

---

## Exception Testing

### pytest Style

```python
def test_exception_raised():
    """Test that exception is raised."""
    with pytest.raises(ValueError):
        raise_error()

def test_exception_message():
    """Test exception message matches pattern."""
    with pytest.raises(ValueError, match="Invalid input: .+"):
        raise_error("test")

def test_exception_details():
    """Test exception details."""
    with pytest.raises(ValueError) as exc_info:
        raise_error()

    assert "Invalid" in str(exc_info.value)
    assert exc_info.type is ValueError
```

### unittest Style

```python
def test_exception_raised(self):
    """Test that exception is raised."""
    with self.assertRaises(ValueError):
        raise_error()

def test_exception_message(self):
    """Test exception message."""
    with self.assertRaisesRegex(ValueError, "Invalid input"):
        raise_error("test")
```

---

## Best Practices for Python Tests

### 1. Use Type Hints in Tests

```python
from typing import List

def test_returns_list_of_strings() -> None:
    """Test function returns list of strings."""
    result: List[str] = get_user_names()
    assert isinstance(result, list)
    assert all(isinstance(name, str) for name in result)
```

### 2. Test Magic Methods

```python
def test_string_representation():
    """Test __str__ and __repr__ methods."""
    user = User(name="Alice")
    assert str(user) == "User(name='Alice')"
    assert repr(user) == "User(name='Alice')"

def test_equality():
    """Test __eq__ method."""
    user1 = User(id=1, name="Alice")
    user2 = User(id=1, name="Alice")
    user3 = User(id=2, name="Bob")

    assert user1 == user2
    assert user1 != user3

def test_iteration():
    """Test __iter__ method."""
    container = Container([1, 2, 3])
    items = list(container)
    assert items == [1, 2, 3]
```

### 3. Test Class Methods and Static Methods

```python
def test_class_method():
    """Test @classmethod."""
    user = User.from_dict({"name": "Alice", "age": 30})
    assert isinstance(user, User)
    assert user.name == "Alice"

def test_static_method():
    """Test @staticmethod."""
    result = User.validate_email("alice@example.com")
    assert result is True
```

### 4. Use pytest's Built-in Fixtures

```python
def test_with_tmp_path(tmp_path):
    """Test using temporary directory (pytest fixture)."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    assert file_path.read_text() == "content"

def test_with_capsys(capsys):
    """Test stdout/stderr capture (pytest fixture)."""
    print("Hello")
    captured = capsys.readouterr()
    assert captured.out == "Hello\n"

def test_with_monkeypatch(monkeypatch):
    """Test with environment variable (pytest fixture)."""
    monkeypatch.setenv("API_KEY", "test_key")
    assert os.getenv("API_KEY") == "test_key"
```

---

## Code Coverage

### Running Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
pytest --cov=myapp --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage Assertions

```python
# In pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=myapp --cov-fail-under=80"
```

---

## Related Documents

- **Test Generation Skill**: `SKILL.md` - General test generation principles
- **Unit Test Patterns**: `unit-test-patterns.md` - AAA pattern, isolation
- **Mocking Strategies**: `mocking-strategies.md` - When and how to mock
- **pytest Template**: `../templates/python-pytest-template.md` - Test templates

---

**Created**: 2025-12-05
**Last Updated**: 2025-12-05
**Python Version**: 3.8+
**pytest Version**: 7.x, 8.x
**Maintained By**: Dante Automated Testing Plugin
