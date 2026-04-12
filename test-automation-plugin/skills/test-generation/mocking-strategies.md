# Mocking Strategies

**Purpose**: Guide for when, what, and how to mock dependencies in tests
**Focus**: Test isolation and maintainability
**Version**: 1.0.0

---

## Overview

Mocking is a technique for replacing real dependencies with controlled test doubles. This document provides strategies for effective mocking that keeps tests fast, isolated, and maintainable.

---

## When to Mock

### ✅ DO Mock

#### 1. External Services and APIs

**Why**: Network calls are slow, unreliable, and may have side effects.

```python
# Mock HTTP API calls
@patch('requests.get')
def test_fetch_user_data(mock_get):
    """Test fetching user data from API."""
    # Arrange
    mock_get.return_value.json.return_value = {"id": 1, "name": "Alice"}
    mock_get.return_value.status_code = 200

    # Act
    result = fetch_user(1)

    # Assert
    assert result["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

#### 2. Database Operations

**Why**: Database access is slow and requires setup/teardown.

```python
@patch('myapp.database.get_connection')
def test_get_user_from_database(mock_db):
    """Test retrieving user from database."""
    # Arrange
    mock_db.return_value.query.return_value = [{"id": 1, "name": "Alice"}]

    # Act
    user = get_user(1)

    # Assert
    assert user.name == "Alice"
    mock_db.return_value.query.assert_called_once()
```

#### 3. File System Operations

**Why**: File I/O is slow and can leave artifacts.

```python
@patch('builtins.open', mock_open(read_data='test content'))
def test_read_config_file():
    """Test reading configuration file."""
    # Act
    config = load_config('config.txt')

    # Assert
    assert 'test content' in config
```

#### 4. Time-Dependent Code

**Why**: Tests should be deterministic and not depend on current time.

```python
@patch('myapp.utils.datetime')
def test_is_business_hours(mock_datetime):
    """Test business hours check."""
    # Arrange
    mock_datetime.now.return_value = datetime(2025, 1, 15, 14, 0)  # 2 PM

    # Act
    result = is_business_hours()

    # Assert
    assert result is True
```

#### 5. Random Number Generation

**Why**: Tests should be deterministic and repeatable.

```python
@patch('random.randint')
def test_generate_random_id(mock_randint):
    """Test random ID generation."""
    # Arrange
    mock_randint.return_value = 42

    # Act
    user_id = generate_user_id()

    # Assert
    assert user_id == 42
```

#### 6. External Command Execution

**Why**: System commands are slow and may have side effects.

```python
@patch('subprocess.run')
def test_run_git_command(mock_run):
    """Test Git command execution."""
    # Arrange
    mock_run.return_value.stdout = "branch main"
    mock_run.return_value.returncode = 0

    # Act
    branch = get_current_branch()

    # Assert
    assert branch == "main"
```

#### 7. Expensive Computations

**Why**: Unit tests should run quickly.

```python
@patch('myapp.compute_complex_hash')
def test_verify_password(mock_hash):
    """Test password verification."""
    # Arrange
    mock_hash.return_value = "hashed_password"

    # Act
    result = verify_password("test_password", "hashed_password")

    # Assert
    assert result is True
```

### ❌ DON'T Mock

#### 1. Simple Data Structures

**Why**: Real objects are just as fast and more realistic.

```python
# ❌ Bad - unnecessary mocking
def test_user_name():
    mock_user = Mock()
    mock_user.name = "Alice"
    assert mock_user.name == "Alice"  # Tests nothing useful

# ✅ Good - use real object
def test_user_name():
    user = User(name="Alice")
    assert user.name == "Alice"
```

#### 2. The Code Under Test

**Why**: You're testing the mock, not your code.

```python
# ❌ Bad - mocking the code being tested
@patch('myapp.calculator.add')
def test_add(mock_add):
    mock_add.return_value = 5
    result = add(2, 3)
    assert result == 5  # Tests nothing!

# ✅ Good - test the real implementation
def test_add():
    result = add(2, 3)
    assert result == 5
```

#### 3. Pure Functions

**Why**: Pure functions have no side effects and are fast.

```python
# ❌ Bad - mocking pure function
@patch('myapp.math_utils.square')
def test_square(mock_square):
    mock_square.return_value = 25
    assert square(5) == 25

# ✅ Good - test the real function
def test_square():
    assert square(5) == 25
```

#### 4. Simple Value Objects

**Why**: Value objects are cheap to create.

```python
# ❌ Bad - mocking simple value object
def test_point_distance():
    mock_point1 = Mock()
    mock_point1.x = 0
    mock_point1.y = 0
    # ...

# ✅ Good - use real objects
def test_point_distance():
    point1 = Point(0, 0)
    point2 = Point(3, 4)
    distance = calculate_distance(point1, point2)
    assert distance == 5.0
```

---

## What to Mock

### Mock Interfaces, Not Implementations

```python
# ✅ Good - mock the interface
@patch('myapp.services.UserRepository')
def test_user_service(mock_repo):
    """Mock the repository interface."""
    mock_repo.get_user.return_value = User(id=1, name="Alice")
    service = UserService(mock_repo)
    user = service.get_user(1)
    assert user.name == "Alice"
```

### Mock at the Boundary

**Principle**: Mock at the edges of your system, not deep in the implementation.

```python
# ✅ Good - mock at the boundary (HTTP client)
@patch('requests.get')
def test_api_client(mock_get):
    """Mock the HTTP library."""
    mock_get.return_value.json.return_value = {"data": "test"}
    client = APIClient()
    result = client.fetch_data()
    assert result == {"data": "test"}

# ❌ Bad - mocking too deep in the stack
@patch('myapp.client.parse_json')
@patch('myapp.client.validate_response')
@patch('myapp.client.extract_data')
def test_api_client(mock_extract, mock_validate, mock_parse):
    """Too many internal mocks."""
    # This makes the test brittle and coupled to implementation
    pass
```

---

## How to Mock

### Python Mocking Techniques

#### 1. unittest.mock.Mock

**Purpose**: Create a mock object with configurable behavior.

```python
from unittest.mock import Mock

def test_with_mock():
    """Test using Mock object."""
    # Arrange
    mock_service = Mock()
    mock_service.get_data.return_value = {"data": "test"}

    # Act
    result = process_data(mock_service)

    # Assert
    assert "data" in result
    mock_service.get_data.assert_called_once()
```

#### 2. unittest.mock.patch

**Purpose**: Temporarily replace an object with a mock.

```python
from unittest.mock import patch

# Patch as decorator
@patch('myapp.external_api.get_user')
def test_fetch_user(mock_get_user):
    """Test with patched function."""
    mock_get_user.return_value = {"id": 1, "name": "Alice"}
    result = fetch_user(1)
    assert result["name"] == "Alice"

# Patch as context manager
def test_fetch_user_context():
    """Test with patch context manager."""
    with patch('myapp.external_api.get_user') as mock_get_user:
        mock_get_user.return_value = {"id": 1, "name": "Alice"}
        result = fetch_user(1)
        assert result["name"] == "Alice"
```

#### 3. patch.object

**Purpose**: Patch a specific attribute of an object.

```python
from unittest.mock import patch

def test_with_patch_object():
    """Test using patch.object."""
    calculator = Calculator()

    with patch.object(calculator, 'complex_operation', return_value=42):
        result = calculator.perform_calculation()
        assert result == 42
```

#### 4. MagicMock

**Purpose**: Mock with magic methods (\__str\__, \__len\__, etc.).

```python
from unittest.mock import MagicMock

def test_with_magic_mock():
    """Test using MagicMock."""
    # Arrange
    mock_container = MagicMock()
    mock_container.__len__.return_value = 5
    mock_container.__getitem__.return_value = "item"

    # Act
    length = len(mock_container)
    item = mock_container[0]

    # Assert
    assert length == 5
    assert item == "item"
```

#### 5. mock_open

**Purpose**: Mock file operations.

```python
from unittest.mock import mock_open, patch

def test_read_file():
    """Test reading file with mock_open."""
    mock_data = "line1\nline2\nline3"

    with patch('builtins.open', mock_open(read_data=mock_data)):
        content = read_config_file('config.txt')
        assert "line1" in content
```

---

## Mock Configuration Patterns

### Return Values

```python
# Simple return value
mock_obj.method.return_value = "result"

# Different return values for multiple calls
mock_obj.method.side_effect = ["first", "second", "third"]

# Return value based on arguments
def dynamic_return(*args, **kwargs):
    if args[0] == 1:
        return "one"
    return "other"

mock_obj.method.side_effect = dynamic_return
```

### Side Effects

```python
# Raise an exception
mock_obj.method.side_effect = ValueError("Error message")

# Call a real function
def real_implementation(x):
    return x * 2

mock_obj.method.side_effect = real_implementation

# Multiple side effects
mock_obj.method.side_effect = [
    "first call",
    ValueError("second call fails"),
    "third call"
]
```

### Attributes

```python
# Set mock attributes
mock_obj.attribute = "value"
mock_obj.count = 42

# Configure spec (restrict to real object's interface)
mock_obj = Mock(spec=RealClass)
mock_obj.real_method()  # OK
mock_obj.fake_method()  # Raises AttributeError
```

---

## Verification Patterns

### Call Assertions

```python
# Assert called at least once
mock_obj.method.assert_called()

# Assert called exactly once
mock_obj.method.assert_called_once()

# Assert called with specific arguments
mock_obj.method.assert_called_with(arg1, arg2, kwarg=value)

# Assert called once with specific arguments
mock_obj.method.assert_called_once_with(arg1, arg2)

# Assert any call with arguments
mock_obj.method.assert_any_call(arg1, arg2)

# Assert never called
mock_obj.method.assert_not_called()

# Check call count
assert mock_obj.method.call_count == 3

# Access call arguments
args, kwargs = mock_obj.method.call_args
first_call_args = mock_obj.method.call_args_list[0]
```

### Advanced Verification

```python
from unittest.mock import call

# Verify call order
mock_obj.method1()
mock_obj.method2()
mock_obj.assert_has_calls([call.method1(), call.method2()])

# Verify no unexpected calls
mock_obj.method1()
mock_obj.assert_has_calls([call.method1()], any_order=False)
```

---

## Mocking Strategies by Dependency Type

### 1. Mocking HTTP Requests

```python
import requests
from unittest.mock import Mock, patch

@patch('requests.get')
def test_api_call(mock_get):
    """Mock HTTP GET request."""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    # Act
    result = fetch_data_from_api()

    # Assert
    assert result["data"] == "test"
    mock_get.assert_called_once_with("https://api.example.com/data")

@patch('requests.post')
def test_api_post(mock_post):
    """Mock HTTP POST request."""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 1}
    mock_post.return_value = mock_response

    # Act
    result = create_resource({"name": "test"})

    # Assert
    assert result["id"] == 1
    mock_post.assert_called_with(
        "https://api.example.com/resources",
        json={"name": "test"}
    )
```

### 2. Mocking Database Operations

```python
@patch('myapp.database.get_connection')
def test_database_query(mock_get_conn):
    """Mock database connection and query."""
    # Arrange
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    # Act
    users = get_all_users()

    # Assert
    assert len(users) == 2
    assert users[0]["name"] == "Alice"
    mock_cursor.execute.assert_called_once()
```

### 3. Mocking Time and Dates

```python
from datetime import datetime
from unittest.mock import patch

@patch('myapp.utils.datetime')
def test_time_based_logic(mock_datetime):
    """Mock datetime.now()."""
    # Arrange
    mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30)

    # Act
    result = get_greeting()

    # Assert
    assert result == "Good morning"

@patch('time.sleep')
def test_retry_logic(mock_sleep):
    """Mock time.sleep to speed up tests."""
    # Act
    result = retry_operation(max_retries=3)

    # Assert
    assert mock_sleep.call_count == 2  # Failed twice, then succeeded
```

### 4. Mocking File Operations

```python
from unittest.mock import mock_open, patch

@patch('builtins.open', mock_open(read_data='{"key": "value"}'))
@patch('os.path.exists', return_value=True)
def test_load_config(mock_exists):
    """Mock file reading."""
    # Act
    config = load_config('config.json')

    # Assert
    assert config["key"] == "value"

@patch('builtins.open', mock_open())
def test_write_config():
    """Mock file writing."""
    # Act
    save_config('config.json', {"key": "value"})

    # Assert
    open.assert_called_once_with('config.json', 'w')
```

### 5. Mocking Environment Variables

```python
@patch.dict('os.environ', {'API_KEY': 'test_key'})
def test_api_key_from_env():
    """Mock environment variable."""
    # Act
    api_key = get_api_key()

    # Assert
    assert api_key == 'test_key'
```

---

## Partial Mocking (Spy Pattern)

**Purpose**: Keep real implementation but track calls.

```python
# pytest-mock (requires pytest-mock plugin)
def test_spy_pattern(mocker):
    """Use spy to track calls while keeping real implementation."""
    # Arrange
    calculator = Calculator()
    spy = mocker.spy(calculator, 'add')

    # Act
    result = calculator.add(2, 3)

    # Assert
    assert result == 5  # Real implementation runs
    spy.assert_called_once_with(2, 3)  # But we can verify the call

# unittest.mock
from unittest.mock import Mock

def test_partial_mock():
    """Partially mock an object."""
    calculator = Calculator()
    calculator.complex_operation = Mock(return_value=42)

    # complex_operation is mocked
    assert calculator.complex_operation() == 42

    # add is still real
    assert calculator.add(2, 3) == 5
```

---

## Dependency Injection for Testability

**Principle**: Make dependencies explicit for easier mocking.

### Before (Hard to Test)

```python
class UserService:
    def __init__(self):
        self.db = Database.connect()  # Hard-coded dependency
        self.api = ExternalAPI()

    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")
```

### After (Easy to Test)

```python
class UserService:
    def __init__(self, database, api):
        self.db = database  # Injected dependency
        self.api = api

    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")

# Test
def test_get_user():
    # Arrange
    mock_db = Mock()
    mock_api = Mock()
    mock_db.query.return_value = {"id": 1, "name": "Alice"}

    service = UserService(mock_db, mock_api)

    # Act
    user = service.get_user(1)

    # Assert
    assert user["name"] == "Alice"
```

---

## Best Practices

### 1. Mock at the Right Level

```python
# ✅ Good - mock external dependency
@patch('requests.get')
def test_fetch_data(mock_get):
    pass

# ❌ Bad - mock internal implementation
@patch('myapp.services.user_service._validate_user')
def test_create_user(mock_validate):
    pass
```

### 2. Use Specific Assertions

```python
# ✅ Good - specific assertion
mock_api.get_user.assert_called_once_with(user_id=1, include_profile=True)

# ❌ Bad - generic assertion
assert mock_api.get_user.called
```

### 3. Reset Mocks Between Tests

```python
@pytest.fixture
def mock_service():
    mock = Mock()
    yield mock
    mock.reset_mock()  # Clean up after each test
```

### 4. Document Mock Behavior

```python
def test_complex_mock_scenario():
    """
    Test user creation with multiple service calls.

    Mocks:
    - UserRepository: Returns existing user on conflict
    - EmailService: Simulates successful email send
    - CacheService: Simulates cache miss
    """
    # Test implementation
    pass
```

### 5. Use spec= for Safety

```python
# ✅ Good - spec prevents typos
mock_user = Mock(spec=User)
mock_user.get_name()  # OK
mock_user.get_nam()   # Raises AttributeError

# ❌ Bad - no spec, typos pass silently
mock_user = Mock()
mock_user.get_nam()  # Returns another mock, no error!
```

---

## Anti-Patterns to Avoid

### ❌ Over-Mocking

```python
# Bad - mocking too much
@patch('myapp.module1.function1')
@patch('myapp.module2.function2')
@patch('myapp.module3.function3')
@patch('myapp.module4.function4')
@patch('myapp.module5.function5')
def test_complex(m1, m2, m3, m4, m5):
    # This test is fragile and hard to understand
    pass
```

### ❌ Testing the Mock

```python
# Bad - testing the mock itself
def test_mock_behavior():
    mock_obj = Mock()
    mock_obj.method.return_value = 5
    assert mock_obj.method() == 5  # Tests mock, not real code!
```

### ❌ Incomplete Mock Setup

```python
# Bad - mock returns unexpected values
def test_with_incomplete_mock():
    mock_service = Mock()
    # Forgot to configure return_value
    result = process_data(mock_service)
    # result is another Mock object, not expected data!
```

### ❌ Mocking Everything

```python
# Bad - even simple objects are mocked
def test_user_name():
    mock_string = Mock()
    mock_string.upper.return_value = "ALICE"
    # Just use a real string!
```

---

## Decision Tree: Should I Mock This?

```
Is it an external dependency (API, database, file system)?
├─ YES → Mock it
└─ NO → Is it slow (>10ms)?
    ├─ YES → Mock it
    └─ NO → Is it non-deterministic (random, time)?
        ├─ YES → Mock it
        └─ NO → Is it a simple value object or pure function?
            ├─ YES → Don't mock it
            └─ NO → Is it the code under test?
                ├─ YES → Don't mock it
                └─ NO → Consider mocking based on complexity
```

---

## Related Documents

- **Test Generation Skill**: `SKILL.md` - General test generation principles
- **Python Patterns**: `python-patterns.md` - Python-specific mocking with unittest.mock
- **Unit Test Patterns**: `unit-test-patterns.md` - AAA pattern and test structure

---

**Created**: 2025-12-05
**Last Updated**: 2025-12-05
**Maintained By**: Dante Automated Testing Plugin
