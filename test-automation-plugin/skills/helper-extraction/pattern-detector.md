# Pattern Detector for Helper Extraction

**Purpose**: Analyze generated test code to identify extractable helper patterns (mocks, test data builders, setup/teardown utilities) that should be extracted into shared helper modules.

**Version**: 1.0.0

**Requirements Addressed**: REQ-F-14, REQ-F-18, REQ-F-19, REQ-F-20, REQ-F-21

---

## Overview

The Pattern Detector analyzes test code during generation to identify repeated patterns that are candidates for extraction into shared helper modules. It applies thresholds to determine which patterns are worth extracting versus keeping inline.

**Detection Criteria** (from TD-3):
- Pattern appears in **2+ test files** OR
- Pattern exceeds **10 lines of code**

**Pattern Types**:
1. **Mock Creation** (REQ-F-18): Mock objects, patch decorators, mock API clients, databases
2. **Test Data Builders** (REQ-F-19): Repeated object construction, factory functions
3. **Setup/Teardown** (REQ-F-20): Resource management (DB connections, file cleanup)

**Rejection Criteria** (REQ-F-21):
- Simple one-off code that doesn't repeat
- Patterns fewer than 10 lines used in only one file
- Simple variable assignments or trivial operations

---

## API Signature

```python
def detect_helper_patterns(
    test_code: str,
    language: str,
    framework: str,
    project_context: dict = None
) -> List[PatternMetadata]:
    """
    Detect extractable helper patterns in test code.

    Args:
        test_code: The generated test code to analyze
        language: Programming language (python, javascript, typescript, etc.)
        framework: Test framework (pytest, jest, junit5, etc.)
        project_context: Optional context including previously detected patterns,
                        existing test files, pattern frequency data

    Returns:
        List of PatternMetadata objects representing detected patterns,
        sorted by priority (most important first)

    Raises:
        No exceptions - returns empty list if no patterns detected or on error
    """
```

---

## Detection Algorithm

### Step 1: Preprocess Test Code

**Goal**: Clean and prepare code for pattern analysis

**Actions**:
1. Remove comments (they don't contribute to pattern detection)
2. Normalize whitespace (consistent indentation for line counting)
3. Extract imports (to understand dependencies)
4. Identify test functions/methods (boundaries for pattern analysis)

**Example** (Python):
```python
# Input: Raw test code with comments
"""
Test module for API.

This tests the API client.
"""
import pytest
from unittest.mock import Mock

def test_api_call():
    # Create mock
    mock = Mock()
    mock.get.return_value = {"status": "ok"}
    ...

# Output: Cleaned code
import pytest
from unittest.mock import Mock

def test_api_call():
    mock = Mock()
    mock.get.return_value = {"status": "ok"}
    ...
```

### Step 2: Detect Mock Creation Patterns (REQ-F-18)

**Mock Pattern Signatures** by language:

#### Python
```python
# unittest.mock patterns
mock_obj = Mock()
mock_obj.method.return_value = value

mock_obj = MagicMock()
mock_obj.attribute = value

@patch('module.function')
def test_something(mock_func):
    mock_func.return_value = value

# pytest-mock patterns
mocker.patch('module.function', return_value=value)
```

**Detection Logic**:
- Search for `Mock()`, `MagicMock()`, `patch(`, `mocker.patch(`
- Extract the full mock setup block (until next blank line or statement)
- Count lines in the block
- Check if similar pattern appears elsewhere in project

#### JavaScript/TypeScript
```javascript
// Jest patterns
const mockFn = jest.fn();
mockFn.mockReturnValue(value);

jest.mock('./module');
const mockApi = require('./module');
mockApi.method.mockResolvedValue(data);

// Manual mocks
const mockRequest = {
    body: {},
    headers: {},
    method: 'GET'
};
```

**Detection Logic**:
- Search for `jest.fn()`, `jest.mock(`, `.mockReturnValue`, `.mockResolvedValue`
- Search for object literals with mock-like properties (body, headers, status, etc.)
- Extract full setup block

#### Java
```java
// Mockito patterns
UserRepository mockRepo = Mockito.mock(UserRepository.class);
when(mockRepo.findById(1)).thenReturn(user);

@Mock
private UserRepository userRepository;

// Manual setup
doReturn(user).when(mockRepo).findById(1);
```

**Detection Logic**:
- Search for `Mockito.mock(`, `@Mock`, `when(`, `doReturn(`
- Extract setup block including `when().thenReturn()` chains

#### C#
```csharp
// Moq patterns
var mockRepo = new Mock<IUserRepository>();
mockRepo.Setup(r => r.GetById(1)).Returns(user);

// Setup verification
mockRepo.Verify(r => r.GetById(1), Times.Once);
```

**Detection Logic**:
- Search for `new Mock<`, `.Setup(`, `.Returns(`
- Extract full setup block

#### Go
```go
// Manual mock structs
type MockRepository struct {
    GetUserFunc func(id int) (*User, error)
}

func (m *MockRepository) GetUser(id int) (*User, error) {
    if m.GetUserFunc != nil {
        return m.GetUserFunc(id)
    }
    return nil, nil
}

// Usage
mockRepo := &MockRepository{
    GetUserFunc: func(id int) (*User, error) {
        return &User{ID: id}, nil
    },
}
```

**Detection Logic**:
- Search for mock struct definitions
- Search for mock struct initialization with function assignments

#### C++
```cpp
// Google Mock patterns
class MockRepository : public IRepository {
public:
    MOCK_METHOD(User, getUser, (int id), (override));
};

MockRepository mockRepo;
EXPECT_CALL(mockRepo, getUser(1))
    .WillOnce(Return(user));
```

**Detection Logic**:
- Search for `MOCK_METHOD`, `EXPECT_CALL`, `WillOnce`, `Return(`
- Extract mock class definition and setup

#### Rust
```rust
// Manual mock traits
struct MockRepository {
    get_user_result: Option<User>,
}

impl Repository for MockRepository {
    fn get_user(&self, id: i32) -> Option<User> {
        self.get_user_result.clone()
    }
}
```

**Detection Logic**:
- Search for mock struct implementations
- Search for trait implementations on test structs

### Step 3: Detect Test Data Builder Patterns (REQ-F-19)

**Builder Pattern Signatures**:

#### Python
```python
# Repeated object construction
user = User(
    id=1,
    name="Alice",
    email="alice@example.com",
    age=30,
    role="admin"
)

# Dictionary builders
test_data = {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
}
```

**Detection Logic**:
- Search for constructor calls with 3+ parameters
- Search for dictionary/object literals with 3+ fields
- Extract the full construction block
- Check if similar construction appears elsewhere with different values

#### JavaScript/TypeScript
```javascript
// Object builders
const testUser = {
    id: 1,
    name: 'Alice',
    email: 'alice@example.com',
    age: 30,
    role: 'admin'
};

// Class instantiation
const user = new User({
    id: 1,
    name: 'Alice',
    email: 'alice@example.com'
});
```

**Detection Logic**:
- Search for object literals with 3+ properties
- Search for `new ClassName({...})` with 3+ properties

#### Java
```java
// Builder pattern
User user = new User.Builder()
    .id(1)
    .name("Alice")
    .email("alice@example.com")
    .age(30)
    .build();

// Constructor
User user = new User(1, "Alice", "alice@example.com", 30, "admin");
```

**Detection Logic**:
- Search for `.Builder()` patterns
- Search for constructors with 3+ parameters

#### C#
```csharp
// Object initializer
var user = new User
{
    Id = 1,
    Name = "Alice",
    Email = "alice@example.com",
    Age = 30,
    Role = "admin"
};
```

**Detection Logic**:
- Search for object initializers with 3+ properties

#### Go
```go
// Struct literal
user := User{
    ID:    1,
    Name:  "Alice",
    Email: "alice@example.com",
    Age:   30,
    Role:  "admin",
}
```

**Detection Logic**:
- Search for struct literals with 3+ fields

#### C++
```cpp
// Constructor
User user(1, "Alice", "alice@example.com", 30, "admin");

// Aggregate initialization
User user{1, "Alice", "alice@example.com", 30, "admin"};
```

**Detection Logic**:
- Search for constructors with 3+ parameters
- Search for brace initialization with 3+ values

#### Rust
```rust
// Struct literal
let user = User {
    id: 1,
    name: String::from("Alice"),
    email: String::from("alice@example.com"),
    age: 30,
    role: String::from("admin"),
};
```

**Detection Logic**:
- Search for struct literals with 3+ fields

### Step 4: Detect Setup/Teardown Patterns (REQ-F-20)

**Setup/Teardown Signatures**:

#### Python
```python
# pytest fixtures with cleanup
@pytest.fixture
def database():
    db = Database()
    db.connect()
    yield db
    db.disconnect()

# Setup/teardown in test methods
def setup_method(self):
    self.db = Database()
    self.db.connect()

def teardown_method(self):
    self.db.disconnect()
```

**Detection Logic**:
- Search for `@pytest.fixture` with `yield`
- Search for `setup_method`, `teardown_method`
- Search for resource creation followed by cleanup (connect/disconnect, open/close)

#### JavaScript
```javascript
// Jest setup/teardown
beforeEach(() => {
    db = new Database();
    db.connect();
});

afterEach(() => {
    db.disconnect();
});
```

**Detection Logic**:
- Search for `beforeEach`, `afterEach`, `beforeAll`, `afterAll`
- Extract full setup/teardown blocks

#### Java
```java
// JUnit setup/teardown
@BeforeEach
void setUp() {
    database = new Database();
    database.connect();
}

@AfterEach
void tearDown() {
    database.disconnect();
}
```

**Detection Logic**:
- Search for `@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`
- Extract full method body

#### C#
```csharp
// xUnit setup/teardown with IDisposable
public class UserServiceTests : IDisposable
{
    private Database _db;

    public UserServiceTests()
    {
        _db = new Database();
        _db.Connect();
    }

    public void Dispose()
    {
        _db?.Disconnect();
    }
}
```

**Detection Logic**:
- Search for constructor with resource creation
- Search for `Dispose()` method
- Match paired creation/cleanup

#### Go
```go
// Setup with defer
func TestSomething(t *testing.T) {
    db, err := NewDatabase()
    if err != nil {
        t.Fatalf("setup failed: %v", err)
    }
    defer db.Close()

    // Test code...
}
```

**Detection Logic**:
- Search for resource creation followed by `defer cleanup()`
- Extract setup block

#### C++
```cpp
// RAII with fixtures
class DatabaseTest : public ::testing::Test {
protected:
    void SetUp() override {
        database = std::make_unique<Database>();
        database->connect();
    }

    void TearDown() override {
        if (database) {
            database->disconnect();
        }
    }

    std::unique_ptr<Database> database;
};
```

**Detection Logic**:
- Search for `SetUp()` and `TearDown()` methods in test fixtures
- Extract full method bodies

#### Rust
```rust
// Setup with Drop trait
struct TestFixture {
    database: Database,
}

impl TestFixture {
    fn new() -> Self {
        let mut db = Database::new();
        db.connect();
        TestFixture { database: db }
    }
}

impl Drop for TestFixture {
    fn drop(&mut self) {
        self.database.disconnect();
    }
}
```

**Detection Logic**:
- Search for fixture structs with `Drop` implementation
- Extract setup and teardown logic

### Step 5: Apply Thresholds (REQ-F-14)

For each detected pattern:

1. **Count occurrences**: How many times does this pattern appear across project?
   - Use `project_context` to track patterns across multiple test file generations
   - Store pattern signatures (normalized code) to detect duplicates

2. **Count lines**: How many lines of code in the pattern?
   - Exclude blank lines and comments
   - Count only significant code lines

3. **Apply threshold rules**:
   ```python
   if pattern.occurrences >= 2 OR pattern.line_count >= 10:
       # Pattern qualifies for extraction
       patterns_to_extract.append(pattern)
   else:
       # Pattern stays inline (REQ-F-21)
       continue
   ```

4. **Calculate complexity score** (REQ-F-15):
   - Mock setups: Always high priority (score 7-10)
   - Builders with 3+ fields: Medium priority (score 5-7)
   - Setup/teardown with resource management: High priority (score 7-9)
   - Simple assignments: Low priority (score 1-3, likely rejected)

### Step 6: Create PatternMetadata Objects

For each qualifying pattern:

```python
pattern = PatternMetadata(
    type="mock_creation",  # or "test_builder", "setup_teardown"
    name=generate_helper_name(pattern),  # e.g., "create_mock_api_client"
    code_snippet=pattern_code,  # The actual code to extract
    line_count=count_lines(pattern_code),
    occurrences=occurrences_count,
    complexity_score=calculate_complexity(pattern),
    dependencies=extract_imports(pattern_code)  # Required imports
)
```

**Helper Name Generation**:
- Mock creation: `create_mock_{type}` (e.g., `create_mock_api_client`)
- Test builders: `build_{entity}` (e.g., `build_test_user`)
- Setup/teardown: `setup_{resource}`, `cleanup_{resource}`

### Step 7: Sort and Return Patterns

Sort patterns by priority:
1. Complexity score (high to low)
2. Occurrences (high to low)
3. Line count (high to low)

Return sorted list of `PatternMetadata` objects.

---

## Error Handling

**Graceful Degradation**: Never raise exceptions, always return empty list on error

**Error Scenarios**:

1. **Malformed test code** (syntax errors):
   ```python
   try:
       ast.parse(test_code)
   except SyntaxError:
       # Log warning, return empty list
       return []
   ```

2. **Unknown language/framework**:
   ```python
   if language not in SUPPORTED_LANGUAGES:
       # Log warning, return empty list
       return []
   ```

3. **Empty test code**:
   ```python
   if not test_code or not test_code.strip():
       return []
   ```

4. **No patterns detected** (not an error):
   ```python
   return []  # This is valid - some tests don't have extractable patterns
   ```

---

## Example Usage

### Python pytest Example

```python
test_code = """
import pytest
from unittest.mock import Mock

def test_api_get_user():
    # Arrange
    mock_api = Mock()
    mock_api.get.return_value = {"id": 1, "name": "Alice"}

    user = User(
        id=1,
        name="Alice",
        email="alice@example.com",
        age=30
    )

    # Act
    result = get_user_data(1, mock_api)

    # Assert
    assert result["name"] == "Alice"
"""

patterns = detect_helper_patterns(
    test_code=test_code,
    language="python",
    framework="pytest",
    project_context={
        "existing_patterns": [],
        "test_files_generated": 1
    }
)

# Output:
# [
#     PatternMetadata(
#         type="mock_creation",
#         name="create_mock_api_client",
#         code_snippet='mock_api = Mock()\nmock_api.get.return_value = {"id": 1, "name": "Alice"}',
#         line_count=2,
#         occurrences=1,  # First occurrence
#         complexity_score=7,
#         dependencies=["unittest.mock.Mock"]
#     ),
#     PatternMetadata(
#         type="test_builder",
#         name="build_user",
#         code_snippet='User(id=1, name="Alice", email="alice@example.com", age=30)',
#         line_count=5,
#         occurrences=1,
#         complexity_score=5,
#         dependencies=["User"]
#     )
# ]
```

### JavaScript Jest Example

```javascript
test_code = `
const { createUser } = require('./userService');

describe('User Service', () => {
    it('creates a user', () => {
        const mockDb = {
            insert: jest.fn().mockResolvedValue({ id: 1 })
        };

        const testUser = {
            name: 'Alice',
            email: 'alice@example.com',
            age: 30,
            role: 'admin'
        };

        const result = await createUser(testUser, mockDb);
        expect(result.id).toBe(1);
    });
});
`

patterns = detect_helper_patterns(
    test_code=test_code,
    language="javascript",
    framework="jest"
)

# Output:
# [
#     PatternMetadata(
#         type="mock_creation",
#         name="createMockDatabase",
#         code_snippet='const mockDb = {\n    insert: jest.fn().mockResolvedValue({ id: 1 })\n};',
#         line_count=3,
#         occurrences=1,
#         complexity_score=6,
#         dependencies=["jest"]
#     ),
#     PatternMetadata(
#         type="test_builder",
#         name="buildTestUser",
#         code_snippet='{\n    name: "Alice",\n    email: "alice@example.com",\n    age: 30,\n    role: "admin"\n}',
#         line_count=5,
#         occurrences=1,
#         complexity_score=5,
#         dependencies=[]
#     )
# ]
```

---

## Integration with Write-Agent

The pattern detector is called in **Step 5: Add Mocking and Fixtures**:

```python
# In write-agent Step 5
def add_mocking_and_fixtures(test_code, language, framework, project_context):
    """Add mocking and fixtures to test code, extracting helpers where appropriate."""

    # Detect extractable patterns
    patterns = detect_helper_patterns(test_code, language, framework, project_context)

    if patterns:
        # Patterns found - proceed with helper extraction
        # (Next step: Helper Generator)
        return {"patterns": patterns, "test_code": test_code}
    else:
        # No patterns found - use inline helpers (existing behavior)
        return {"patterns": [], "test_code": test_code}
```

---

## Performance Considerations

**Target**: <500ms per test file

**Optimizations**:
1. **Regex-based detection** for pattern matching (fast)
2. **Early termination** if no patterns found in first pass
3. **Caching** of project_context patterns to avoid re-analysis
4. **Lazy loading** of language-specific parsers (only load when needed)

**Avoid**:
- LLM calls (too slow, unnecessary for pattern detection)
- Full AST parsing for every language (use regex first, AST only if needed)
- Complex NLP or ML models (overkill for well-defined patterns)

---

## Testing Requirements

Unit tests must cover:

1. **All pattern types** for all 7 languages:
   - Mock creation detection
   - Test builder detection
   - Setup/teardown detection

2. **Threshold logic**:
   - Pattern with 2+ occurrences extracted
   - Pattern with 10+ lines extracted
   - Pattern with 1 occurrence and <10 lines rejected

3. **Error handling**:
   - Malformed code returns empty list
   - Unknown language returns empty list
   - Empty code returns empty list

4. **Edge cases**:
   - Code with only comments
   - Code with no patterns
   - Patterns that are too simple (one-liners)

5. **Helper name generation**:
   - Mock creation → `create_mock_*`
   - Test builders → `build_*`
   - Setup/teardown → `setup_*`, `cleanup_*`

Test file: `tests/unit/test_pattern_detector.py`
