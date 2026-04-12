# Python pytest Test Template

**Purpose**: Template for generating pytest test files with proper structure, conventions, and patterns.

**Target Language**: Python
**Test Framework**: pytest
**Version Support**: pytest 7.x, 8.x

---

## Template Structure

### Basic Test File Template

```python
"""
Test module for {MODULE_NAME}.

This test file covers:
- {TEST_COVERAGE_AREA_1}
- {TEST_COVERAGE_AREA_2}
- {TEST_COVERAGE_AREA_3}
"""

import pytest
{ADDITIONAL_IMPORTS}

# ============================================================================
# Fixtures
# ============================================================================

{FIXTURES}

# ============================================================================
# Test Class: {CLASS_NAME}
# ============================================================================

class {TEST_CLASS_NAME}:
    """Test suite for {CLASS_OR_MODULE_DESCRIPTION}."""

    {TEST_METHODS}
```

---

## Template Placeholders

### Module-Level Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{MODULE_NAME}` | Name of the module being tested | `calculator`, `user_service`, `data_processor` |
| `{TEST_COVERAGE_AREA_N}` | Areas of functionality covered | `Addition operations`, `Error handling`, `Edge cases` |
| `{ADDITIONAL_IMPORTS}` | Required imports for tests | `from unittest.mock import Mock, patch`<br>`from myapp.calculator import Calculator` |
| `{FIXTURES}` | Fixture definitions | See Fixture Patterns section |
| `{TEST_CLASS_NAME}` | Name of test class | `TestCalculator`, `TestUserService` |
| `{CLASS_OR_MODULE_DESCRIPTION}` | Description of what's being tested | `Calculator arithmetic operations`, `User authentication` |
| `{TEST_METHODS}` | Individual test method definitions | See Test Method Patterns section |

### Test Method Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{TEST_METHOD_NAME}` | Name of test method | `test_add_positive_numbers`, `test_divide_by_zero_raises_error` |
| `{TEST_DESCRIPTION}` | Docstring describing test | `Test that adding two positive numbers returns correct sum.` |
| `{ARRANGE_CODE}` | Setup code (AAA pattern) | `calculator = Calculator()`<br>`a, b = 5, 3` |
| `{ACT_CODE}` | Action/execution code | `result = calculator.add(a, b)` |
| `{ASSERT_CODE}` | Assertion code | `assert result == 8`<br>`assert result > 0` |

---

## pytest Conventions

### Naming Conventions

**Test Files**:
- Pattern: `test_*.py` or `*_test.py`
- Examples: `test_calculator.py`, `calculator_test.py`
- Location: `tests/` directory at project root or alongside source

**Test Classes**:
- Pattern: `Test*` (PascalCase)
- Examples: `TestCalculator`, `TestUserAuthentication`
- Use classes to group related tests

**Test Methods**:
- Pattern: `test_*` (snake_case)
- Format: `test_<function>_<condition>_<expected_result>`
- Examples:
  - `test_add_positive_numbers_returns_sum`
  - `test_divide_by_zero_raises_value_error`
  - `test_login_invalid_credentials_returns_false`

**Fixtures**:
- Pattern: `snake_case` names
- Examples: `sample_user`, `mock_database`, `api_client`

### File Structure

```
tests/
├── __init__.py                    # Makes tests a package
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_calculator.py
│   └── test_user_service.py
├── integration/
│   ├── __init__.py
│   └── test_api_endpoints.py
└── e2e/
    ├── __init__.py
    └── test_user_workflows.py
```

### Assertion Style

**Preferred**: Simple `assert` statements (pytest rewrites them)

```python
# Good - pytest provides detailed output
assert result == expected
assert len(items) > 0
assert "error" in response

# Avoid - unittest-style assertions
self.assertEqual(result, expected)  # Don't use with pytest
```

---

## Test Method Template (AAA Pattern)

### Basic Template

```python
def test_{function}_{condition}_{expected}(self{FIXTURE_PARAMS}):
    """
    {TEST_DESCRIPTION}

    Test scenario:
    - Given: {PRECONDITIONS}
    - When: {ACTION}
    - Then: {EXPECTED_OUTCOME}
    """
    # Arrange
    {ARRANGE_CODE}

    # Act
    {ACT_CODE}

    # Assert
    {ASSERT_CODE}
```

### Example: Simple Function Test

```python
def test_add_positive_numbers_returns_correct_sum(self):
    """
    Test that adding two positive numbers returns correct sum.

    Test scenario:
    - Given: Two positive integers (5 and 3)
    - When: add() is called
    - Then: Returns 8
    """
    # Arrange
    calculator = Calculator()
    a = 5
    b = 3
    expected = 8

    # Act
    result = calculator.add(a, b)

    # Assert
    assert result == expected
    assert isinstance(result, int)
```

### Example: Exception Test

```python
def test_divide_by_zero_raises_value_error(self):
    """
    Test that dividing by zero raises ValueError.

    Test scenario:
    - Given: A calculator instance
    - When: divide() is called with divisor = 0
    - Then: Raises ValueError with appropriate message
    """
    # Arrange
    calculator = Calculator()

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10, 0)
```

---

## Fixture Patterns

### 1. Basic Fixture

```python
@pytest.fixture
def calculator():
    """Provide a Calculator instance for tests."""
    return Calculator()

# Usage in test
def test_add_with_fixture(self, calculator):
    result = calculator.add(2, 3)
    assert result == 5
```

### 2. Setup/Teardown Fixture

```python
@pytest.fixture
def database_connection():
    """Provide a database connection with cleanup."""
    # Setup
    conn = create_connection("test_db")
    conn.create_tables()

    yield conn  # Provide to test

    # Teardown
    conn.drop_tables()
    conn.close()

# Usage
def test_insert_user(self, database_connection):
    database_connection.insert_user({"name": "Alice"})
    users = database_connection.get_users()
    assert len(users) == 1
```

### 3. Parametrized Fixture

```python
@pytest.fixture(params=[
    "sqlite",
    "postgresql",
    "mysql"
])
def database_type(request):
    """Run tests with multiple database types."""
    return request.param

# Test runs 3 times, once per parameter
def test_connection(self, database_type):
    conn = create_connection(database_type)
    assert conn.is_connected()
```

### 4. Fixture with Scope

```python
@pytest.fixture(scope="module")
def expensive_resource():
    """
    Create expensive resource once per module.

    Scopes:
    - function (default): Per test
    - class: Per test class
    - module: Per module
    - session: Once per test session
    """
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()
```

### 5. Autouse Fixture

```python
@pytest.fixture(autouse=True)
def reset_state():
    """Automatically reset state before each test."""
    global_state.reset()
    yield
    # Optional cleanup
```

### 6. Fixture Dependencies

```python
@pytest.fixture
def user():
    """Create a test user."""
    return User(name="Alice", email="alice@example.com")

@pytest.fixture
def authenticated_user(user):
    """Provide an authenticated user (depends on user fixture)."""
    user.authenticate("password123")
    return user

# Test uses both fixtures implicitly
def test_profile_access(self, authenticated_user):
    profile = authenticated_user.get_profile()
    assert profile is not None
```

### Template Placeholder for Fixtures

```python
{FIXTURES}

# Example expansion:
@pytest.fixture
def {FIXTURE_NAME}({FIXTURE_DEPENDENCIES}):
    """
    {FIXTURE_DESCRIPTION}
    """
    # Setup
    {FIXTURE_SETUP_CODE}

    yield {FIXTURE_VALUE}

    # Teardown (optional)
    {FIXTURE_TEARDOWN_CODE}
```

---

## Mocking Patterns

### 1. Mock with unittest.mock

```python
from unittest.mock import Mock, MagicMock, patch

def test_api_call_with_mock(self):
    """Test function that makes external API call using mock."""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    with patch('myapp.api.requests.get', return_value=mock_response):
        # Act
        result = fetch_user_data(user_id=123)

        # Assert
        assert result == {"data": "test"}
```

### 2. Mock with pytest-mock (pytest plugin)

```python
def test_database_query_with_mocker(self, mocker):
    """Test using pytest-mock plugin (requires pytest-mock)."""
    # Arrange
    mock_db = mocker.patch('myapp.database.get_connection')
    mock_db.return_value.query.return_value = [{"id": 1, "name": "Alice"}]

    # Act
    users = get_all_users()

    # Assert
    assert len(users) == 1
    assert users[0]["name"] == "Alice"
    mock_db.return_value.query.assert_called_once()
```

### 3. Mock Object Attributes

```python
def test_user_service_with_mock_attributes(self):
    """Test with mock object that has specific attributes."""
    # Arrange
    mock_user = Mock()
    mock_user.id = 123
    mock_user.name = "Alice"
    mock_user.is_active = True

    # Act
    result = process_user(mock_user)

    # Assert
    assert result.user_id == 123
```

### 4. Mock Class Methods

```python
def test_class_method_mock(self):
    """Test by mocking a class method."""
    # Arrange
    with patch.object(Calculator, 'complex_calculation', return_value=42):
        calculator = Calculator()

        # Act
        result = calculator.perform_operation()

        # Assert
        assert result == 42
```

### 5. Mock Side Effects

```python
def test_retry_logic_with_side_effects(self):
    """Test retry logic using side effects."""
    # Arrange
    mock_api = Mock()
    mock_api.call.side_effect = [
        Exception("Network error"),  # First call fails
        Exception("Timeout"),         # Second call fails
        {"status": "success"}         # Third call succeeds
    ]

    # Act
    result = retry_api_call(mock_api, max_retries=3)

    # Assert
    assert result == {"status": "success"}
    assert mock_api.call.call_count == 3
```

### 6. Spy Pattern (partial mock)

```python
def test_spy_pattern_tracks_calls(self, mocker):
    """Test using spy to track calls while keeping real implementation."""
    # Arrange
    calculator = Calculator()
    spy = mocker.spy(calculator, 'add')

    # Act
    result = calculator.add(2, 3)

    # Assert
    assert result == 5  # Real implementation runs
    spy.assert_called_once_with(2, 3)  # But we can verify it was called
```

### Template Placeholder for Mocking

```python
{MOCK_SETUP}

# Example expansion:
def test_{function}_with_mock(self, {MOCKER_FIXTURE}):
    """
    Test {FUNCTION_NAME} with mocked {DEPENDENCY_NAME}.
    """
    # Arrange - Mock setup
    mock_{DEPENDENCY} = {MOCKER_FIXTURE}.patch('{MODULE_PATH}.{DEPENDENCY_CLASS}')
    mock_{DEPENDENCY}.{METHOD}.return_value = {MOCK_RETURN_VALUE}

    # Act
    result = {FUNCTION_CALL}

    # Assert
    assert result == {EXPECTED_RESULT}
    mock_{DEPENDENCY}.{METHOD}.assert_called_once_with({EXPECTED_ARGS})
```

---

## Parametrized Test Patterns

### 1. Basic Parametrization

```python
@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_parametrized(self, a, b, expected):
    """Test add() with multiple input combinations."""
    # Arrange
    calculator = Calculator()

    # Act
    result = calculator.add(a, b)

    # Assert
    assert result == expected
```

### 2. Parametrization with IDs

```python
@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
], ids=[
    "positive_numbers",
    "both_zero",
    "negative_and_positive"
])
def test_add_with_ids(self, a, b, expected):
    """Test add() with descriptive test IDs."""
    calculator = Calculator()
    result = calculator.add(a, b)
    assert result == expected
```

### 3. Parametrization with pytest.param

```python
@pytest.mark.parametrize("dividend, divisor, expected", [
    pytest.param(10, 2, 5, id="simple_division"),
    pytest.param(7, 2, 3.5, id="decimal_result"),
    pytest.param(0, 5, 0, id="zero_dividend"),
    pytest.param(10, 0, None, marks=pytest.mark.xfail(raises=ValueError), id="division_by_zero"),
])
def test_divide_parametrized(self, dividend, divisor, expected):
    """Test divide() with various scenarios including expected failures."""
    calculator = Calculator()
    if expected is None:
        with pytest.raises(ValueError):
            calculator.divide(dividend, divisor)
    else:
        result = calculator.divide(dividend, divisor)
        assert result == expected
```

### Template Placeholder for Parametrization

```python
{PARAMETRIZED_TEST}

# Example expansion:
@pytest.mark.parametrize("{PARAM_NAMES}", [
    {PARAM_VALUES_TUPLE_1},
    {PARAM_VALUES_TUPLE_2},
    {PARAM_VALUES_TUPLE_N},
], ids=[
    "{TEST_ID_1}",
    "{TEST_ID_2}",
    "{TEST_ID_N}",
])
def test_{function}_parametrized(self, {PARAM_NAMES}):
    """
    Test {FUNCTION_NAME} with multiple scenarios.
    """
    # Arrange
    {ARRANGE_CODE}

    # Act
    {ACT_CODE}

    # Assert
    {ASSERT_CODE}
```

---

## Async Test Patterns

### 1. Basic Async Test

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function(self):
    """Test an async function."""
    # Arrange
    service = AsyncService()

    # Act
    result = await service.fetch_data()

    # Assert
    assert result is not None
    assert "data" in result
```

### 2. Async Fixture

```python
@pytest.fixture
async def async_client():
    """Provide an async HTTP client."""
    client = AsyncHTTPClient()
    await client.connect()

    yield client

    await client.disconnect()

@pytest.mark.asyncio
async def test_with_async_fixture(self, async_client):
    """Test using async fixture."""
    response = await async_client.get("/api/users")
    assert response.status == 200
```

### 3. Async Parametrization

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("url, expected_status", [
    ("/api/users", 200),
    ("/api/posts", 200),
    ("/api/invalid", 404),
])
async def test_api_endpoints(self, url, expected_status, async_client):
    """Test multiple API endpoints asynchronously."""
    response = await async_client.get(url)
    assert response.status == expected_status
```

---

## Example Test Cases

### Example 1: Simple Function Test

```python
class TestCalculator:
    """Test suite for Calculator class."""

    def test_add_positive_numbers_returns_sum(self):
        """Test adding two positive numbers."""
        # Arrange
        calculator = Calculator()

        # Act
        result = calculator.add(5, 3)

        # Assert
        assert result == 8

    def test_add_negative_numbers_returns_sum(self):
        """Test adding two negative numbers."""
        # Arrange
        calculator = Calculator()

        # Act
        result = calculator.add(-5, -3)

        # Assert
        assert result == -8

    def test_add_zero_returns_other_number(self):
        """Test adding zero returns the other number."""
        # Arrange
        calculator = Calculator()

        # Act
        result = calculator.add(5, 0)

        # Assert
        assert result == 5
```

### Example 2: Exception Handling Test

```python
class TestCalculator:
    """Test suite for Calculator class."""

    def test_divide_by_zero_raises_value_error(self):
        """Test that dividing by zero raises ValueError."""
        # Arrange
        calculator = Calculator()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(10, 0)

    def test_invalid_input_type_raises_type_error(self):
        """Test that invalid input types raise TypeError."""
        # Arrange
        calculator = Calculator()

        # Act & Assert
        with pytest.raises(TypeError):
            calculator.add("5", 3)
```

### Example 3: Integration Test with Fixtures

```python
@pytest.fixture
def database():
    """Provide test database."""
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

@pytest.fixture
def user_service(database):
    """Provide UserService with test database."""
    return UserService(database)

class TestUserService:
    """Test suite for UserService integration."""

    def test_create_user_persists_to_database(self, user_service, database):
        """Test that creating a user persists to database."""
        # Arrange
        user_data = {"name": "Alice", "email": "alice@example.com"}

        # Act
        user_id = user_service.create_user(user_data)

        # Assert
        user = database.get_user(user_id)
        assert user is not None
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"

    def test_delete_user_removes_from_database(self, user_service, database):
        """Test that deleting a user removes from database."""
        # Arrange
        user_id = user_service.create_user({"name": "Bob"})

        # Act
        user_service.delete_user(user_id)

        # Assert
        user = database.get_user(user_id)
        assert user is None
```

### Example 4: Mocked External Dependency

```python
from unittest.mock import Mock, patch

class TestWeatherService:
    """Test suite for WeatherService with mocked API."""

    def test_get_temperature_calls_api(self):
        """Test that get_temperature calls external API."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"temp": 72, "unit": "F"}

        with patch('requests.get', return_value=mock_response) as mock_get:
            weather_service = WeatherService()

            # Act
            temp = weather_service.get_temperature("New York")

            # Assert
            assert temp == 72
            mock_get.assert_called_once_with(
                "https://api.weather.com/current",
                params={"city": "New York"}
            )

    def test_get_temperature_handles_api_failure(self):
        """Test that get_temperature handles API failure gracefully."""
        # Arrange
        with patch('requests.get', side_effect=Exception("Network error")):
            weather_service = WeatherService()

            # Act
            temp = weather_service.get_temperature("New York")

            # Assert
            assert temp is None  # Service returns None on error
```

---

## Best Practices

### 1. Test Independence
- Each test should run independently
- Don't rely on test execution order
- Use fixtures for shared setup

### 2. Clear Test Names
- Use descriptive names that explain what's being tested
- Format: `test_<what>_<condition>_<expected>`
- Example: `test_login_invalid_password_returns_false`

### 3. One Assertion Concept Per Test
- Focus each test on one behavior
- Multiple assertions OK if testing same concept
- Split unrelated assertions into separate tests

### 4. Arrange-Act-Assert Pattern
- **Arrange**: Set up test data and conditions
- **Act**: Execute the code being tested
- **Assert**: Verify the results
- Add blank lines between sections for clarity

### 5. Use Fixtures Effectively
- Share common setup across tests
- Use appropriate scope (function, class, module, session)
- Clean up resources in fixture teardown

### 6. Mock External Dependencies
- Mock network calls, databases, file system
- Focus tests on unit under test
- Verify interactions with mocks

### 7. Test Edge Cases
- Empty inputs
- Null/None values
- Boundary values (min, max)
- Invalid inputs
- Error conditions

### 8. Descriptive Assertions
```python
# Good - clear what failed
assert len(users) == 5, f"Expected 5 users, got {len(users)}"

# Better - pytest does this automatically
assert len(users) == 5
```

---

## Common pytest Markers

```python
# Skip test
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature(self):
    pass

# Expected failure
@pytest.mark.xfail(reason="Known bug #123")
def test_buggy_feature(self):
    assert False

# Slow test
@pytest.mark.slow
def test_performance_intensive(self):
    pass

# Custom marker (defined in pytest.ini)
@pytest.mark.integration
def test_database_integration(self):
    pass
```

---

## Template Usage Guide

### For Generating Tests

1. **Identify target**: Function, class, or module to test
2. **Select template pattern**: Simple, parametrized, mocked, etc.
3. **Fill placeholders**: Replace `{PLACEHOLDER}` with actual values
4. **Add fixtures**: Include necessary setup/teardown
5. **Consider edge cases**: Add tests for boundary conditions
6. **Add mocks**: Mock external dependencies
7. **Validate syntax**: Ensure generated code is valid Python

### Template Expansion Example

**Input**:
- Function: `add(a: int, b: int) -> int`
- Description: "Adds two numbers"

**Generated Test**:
```python
class TestCalculator:
    """Test suite for Calculator arithmetic operations."""

    def test_add_positive_numbers_returns_sum(self):
        """
        Test that adding two positive numbers returns correct sum.

        Test scenario:
        - Given: Two positive integers (5 and 3)
        - When: add() is called
        - Then: Returns 8
        """
        # Arrange
        calculator = Calculator()
        a = 5
        b = 3
        expected = 8

        # Act
        result = calculator.add(a, b)

        # Assert
        assert result == expected
        assert isinstance(result, int)
```

---

## Related Skills

- **Framework Detection**: `skills/framework-detection/python-frameworks.md`
- **Test Generation**: `skills/test-generation/python-patterns.md`
- **Result Parsing**: `skills/result-parsing/parsers/pytest-parser.md`

---

**Template Version**: 1.0.0
**Last Updated**: 2025-12-05
**Maintained By**: Dante Automated Testing Plugin
