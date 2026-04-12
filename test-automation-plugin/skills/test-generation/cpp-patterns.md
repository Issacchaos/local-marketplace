# C++ Test Generation Patterns

**Version**: 1.0.0
**Language**: C++
**Frameworks**: Google Test (gtest), Catch2
**Purpose**: C++-specific patterns for generating idiomatic, memory-safe tests
**Status**: Phase 4 - Systems Languages

## Overview

C++ test generation patterns covering Google Test (primary) and Catch2 (secondary). This skill focuses on C++-specific features including RAII, smart pointers, fixtures, parameterized tests, death tests, Google Mock, and memory safety patterns.

## C++ Testing Fundamentals

### Framework Selection

#### Google Test (Recommended for Most Projects)

**Characteristics**:
- Industry standard C++ testing framework
- Rich assertion macros (EXPECT_*, ASSERT_*)
- Powerful fixture system (TEST_F)
- Parameterized tests (TEST_P)
- Death tests for crash testing
- Integration with Google Mock
- xUnit-style structure

**When to Use**:
- New C++ projects (default choice)
- Projects needing comprehensive test features
- Projects using Google Mock for mocking
- Enterprise C++ applications
- Projects with CMake build system

#### Catch2 (Modern Alternative)

**Characteristics**:
- Header-only library (easy integration)
- BDD-style syntax (TEST_CASE, SECTION)
- Natural assertion syntax (REQUIRE, CHECK)
- Built-in benchmarking
- Less verbose than Google Test

**When to Use**:
- Projects preferring header-only libraries
- Teams preferring BDD-style tests
- Projects with simpler test requirements
- Open-source libraries

## File Organization

### Project Structure

```
project/
├── include/
│   └── mylib/
│       ├── calculator.h
│       ├── database.h
│       └── utils/
│           └── string_utils.h
├── src/
│   ├── calculator.cpp
│   ├── database.cpp
│   └── utils/
│       └── string_utils.cpp
├── tests/
│   ├── CMakeLists.txt
│   ├── test_main.cpp              # Test runner
│   ├── test_calculator.cpp
│   ├── test_database.cpp
│   └── utils/
│       └── test_string_utils.cpp
├── CMakeLists.txt
└── README.md
```

### Naming Conventions

**Test Files**:
- Pattern: `test_*.cpp` or `*_test.cpp`
- Match source file: `calculator.cpp` → `test_calculator.cpp`
- Location: `tests/` directory mirroring `src/` structure

**Test Cases**:
- Google Test: `TEST(TestSuiteName, TestName)` (PascalCase)
- Catch2: `TEST_CASE("descriptive name", "[tag]")`
- Example: `TEST(CalculatorTest, AddPositiveNumbers)`

**Fixture Classes**:
- Pattern: `<ClassName>Test` (PascalCase)
- Example: `DatabaseTest`, `CalculatorTest`
- Inherit from `testing::Test`

## Google Test Patterns (Primary)

### Basic Test Structure (TEST Macro)

```cpp
#include <gtest/gtest.h>
#include "calculator.h"

// ============================================================================
// Test Suite: CalculatorTest
// ============================================================================

// Simple test using TEST macro
TEST(CalculatorTest, AddPositiveNumbers) {
    // Arrange
    Calculator calc;
    int a = 5;
    int b = 3;
    int expected = 8;

    // Act
    int result = calc.add(a, b);

    // Assert
    EXPECT_EQ(result, expected);
    EXPECT_GT(result, 0);
}

TEST(CalculatorTest, SubtractNumbers) {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.subtract(10, 3);

    // Assert
    EXPECT_EQ(result, 7);
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST(CalculatorTest, AddWithZero) {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.add(5, 0);

    // Assert
    EXPECT_EQ(result, 5);
}

TEST(CalculatorTest, AddNegativeNumbers) {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.add(-5, -3);

    // Assert
    EXPECT_EQ(result, -8);
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST(CalculatorTest, DivideByZeroThrows) {
    // Arrange
    Calculator calc;

    // Act & Assert
    EXPECT_THROW(calc.divide(10, 0), std::invalid_argument);
}
```

### Fixture Class Patterns (TEST_F)

```cpp
#include <gtest/gtest.h>
#include <memory>
#include "database.h"

// ============================================================================
// Fixture Class: DatabaseTest
// ============================================================================

class DatabaseTest : public testing::Test {
protected:
    // SetUp() runs before each test
    void SetUp() override {
        // Use smart pointers for automatic cleanup
        db = std::make_unique<Database>();
        db->connect("test.db");
        db->execute("CREATE TABLE users (id INTEGER, name TEXT)");
    }

    // TearDown() runs after each test
    void TearDown() override {
        if (db) {
            db->disconnect();
            // unique_ptr automatically deletes db
        }
    }

    // Helper method available to all tests
    void insertTestUser(int id, const std::string& name) {
        db->execute("INSERT INTO users VALUES (?, ?)", id, name);
    }

    // Fixture member variables
    std::unique_ptr<Database> db;
};

// Use TEST_F to access fixture members
TEST_F(DatabaseTest, InsertUser) {
    // Arrange
    int user_id = 1;
    std::string name = "Alice";

    // Act
    insertTestUser(user_id, name);
    auto result = db->query("SELECT * FROM users WHERE id = ?", user_id);

    // Assert
    EXPECT_EQ(result.size(), 1);
    EXPECT_EQ(result[0].name, name);
}

TEST_F(DatabaseTest, DeleteUser) {
    // Arrange
    insertTestUser(1, "Alice");

    // Act
    db->execute("DELETE FROM users WHERE id = ?", 1);
    auto result = db->query("SELECT * FROM users WHERE id = ?", 1);

    // Assert
    EXPECT_TRUE(result.empty());
}

TEST_F(DatabaseTest, UpdateUser) {
    // Arrange
    insertTestUser(1, "Alice");

    // Act
    db->execute("UPDATE users SET name = ? WHERE id = ?", "Bob", 1);
    auto result = db->query("SELECT * FROM users WHERE id = ?", 1);

    // Assert
    EXPECT_EQ(result[0].name, "Bob");
}
```

### Class-Level Setup/Teardown

```cpp
class ExpensiveResourceTest : public testing::Test {
protected:
    // SetUpTestSuite() runs once before all tests in this suite
    static void SetUpTestSuite() {
        // Allocate shared resource once
        shared_resource = std::make_shared<ExpensiveResource>();
        shared_resource->initialize();
    }

    // TearDownTestSuite() runs once after all tests in this suite
    static void TearDownTestSuite() {
        shared_resource->cleanup();
        shared_resource.reset();
    }

    // SetUp() runs before each test (optional)
    void SetUp() override {
        // Per-test setup if needed
    }

    // Shared across all tests in this suite
    static std::shared_ptr<ExpensiveResource> shared_resource;
};

// Define static member
std::shared_ptr<ExpensiveResource> ExpensiveResourceTest::shared_resource = nullptr;

TEST_F(ExpensiveResourceTest, TestOperation1) {
    EXPECT_TRUE(shared_resource->isReady());
}

TEST_F(ExpensiveResourceTest, TestOperation2) {
    EXPECT_TRUE(shared_resource->isReady());
}
```

## RAII Resource Management Patterns

### Pattern 1: Automatic Cleanup with Destructors

```cpp
// Resource wrapper using RAII
class FileHandle {
public:
    explicit FileHandle(const std::string& filename)
        : file(std::fopen(filename.c_str(), "r")) {
        if (!file) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~FileHandle() {
        if (file) {
            std::fclose(file);
        }
    }

    // Prevent copying
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

    // Allow moving
    FileHandle(FileHandle&& other) noexcept : file(other.file) {
        other.file = nullptr;
    }

    FILE* get() const { return file; }

private:
    FILE* file;
};

TEST(FileHandleTest, ReadFileAutomaticCleanup) {
    // Arrange
    const std::string filename = "test.txt";
    std::ofstream(filename) << "test content";

    {
        // Act
        FileHandle handle(filename);
        char buffer[100];
        std::fgets(buffer, sizeof(buffer), handle.get());

        // Assert
        EXPECT_STREQ(buffer, "test content");
    } // FileHandle destructor automatically closes file

    // Cleanup test file
    std::remove(filename.c_str());
}
```

### Pattern 2: Fixture with RAII

```cpp
class TemporaryFileTest : public testing::Test {
protected:
    void SetUp() override {
        // Create temporary file
        temp_filename = "test_temp_" + std::to_string(time(nullptr)) + ".txt";
        temp_file = std::make_unique<std::ofstream>(temp_filename);
        *temp_file << "initial content";
        temp_file->close();
    }

    void TearDown() override {
        // RAII: unique_ptr automatically deletes temp_file
        // Manual cleanup of filesystem resource
        if (std::filesystem::exists(temp_filename)) {
            std::filesystem::remove(temp_filename);
        }
    }

    std::string temp_filename;
    std::unique_ptr<std::ofstream> temp_file;
};

TEST_F(TemporaryFileTest, WriteAndRead) {
    // Arrange
    std::ofstream out(temp_filename, std::ios::app);
    out << "\nadditional content";
    out.close();

    // Act
    std::ifstream in(temp_filename);
    std::string content((std::istreambuf_iterator<char>(in)),
                        std::istreambuf_iterator<char>());

    // Assert
    EXPECT_TRUE(content.find("initial content") != std::string::npos);
    EXPECT_TRUE(content.find("additional content") != std::string::npos);
}
```

### Pattern 3: Scoped Resource Management

```cpp
TEST(ResourceManagementTest, ScopedLock) {
    // Arrange
    std::mutex mtx;
    int shared_counter = 0;

    {
        // Act - std::lock_guard uses RAII
        std::lock_guard<std::mutex> lock(mtx);
        shared_counter++;
        // Assert
        EXPECT_EQ(shared_counter, 1);
    } // lock automatically released here

    // Verify mutex is unlocked
    EXPECT_TRUE(mtx.try_lock());
    mtx.unlock();
}
```

## Smart Pointer Usage Patterns

### Pattern 1: unique_ptr for Exclusive Ownership

```cpp
TEST(SmartPointerTest, UniquePtrExclusiveOwnership) {
    // Arrange - unique_ptr for single ownership
    auto user = std::make_unique<User>("Alice", 30);

    // Act
    auto age = user->getAge();

    // Assert
    EXPECT_EQ(age, 30);
    EXPECT_NE(user.get(), nullptr);

    // user automatically deleted when scope ends
}

TEST(SmartPointerTest, UniquePtrMoveSemantics) {
    // Arrange
    auto user1 = std::make_unique<User>("Alice", 30);

    // Act - transfer ownership
    auto user2 = std::move(user1);

    // Assert
    EXPECT_EQ(user1.get(), nullptr);  // user1 no longer owns the object
    EXPECT_NE(user2.get(), nullptr);
    EXPECT_EQ(user2->getName(), "Alice");
}

TEST(SmartPointerTest, UniquePtrFactoryPattern) {
    // Arrange & Act
    auto createUser = []() -> std::unique_ptr<User> {
        return std::make_unique<User>("Bob", 25);
    };

    auto user = createUser();

    // Assert
    EXPECT_EQ(user->getName(), "Bob");
}
```

### Pattern 2: shared_ptr for Shared Ownership

```cpp
TEST(SmartPointerTest, SharedPtrMultipleOwners) {
    // Arrange - shared_ptr allows multiple owners
    auto user1 = std::make_shared<User>("Alice", 30);
    auto user2 = user1;  // Both share ownership

    // Act
    EXPECT_EQ(user1.use_count(), 2);

    // Assert
    EXPECT_EQ(user1->getName(), "Alice");
    EXPECT_EQ(user2->getName(), "Alice");
    EXPECT_EQ(user1.get(), user2.get());  // Point to same object
}

TEST(SmartPointerTest, SharedPtrInContainer) {
    // Arrange
    std::vector<std::shared_ptr<User>> users;

    // Act
    users.push_back(std::make_shared<User>("Alice", 30));
    users.push_back(std::make_shared<User>("Bob", 25));
    auto first_user = users[0];  // Shared ownership

    // Assert
    EXPECT_EQ(users.size(), 2);
    EXPECT_EQ(first_user.use_count(), 2);  // One in vector, one in first_user
    EXPECT_EQ(first_user->getName(), "Alice");
}
```

### Pattern 3: weak_ptr for Non-Owning References

```cpp
class Node {
public:
    std::shared_ptr<Node> parent;
    std::vector<std::shared_ptr<Node>> children;
};

// Better: Use weak_ptr to avoid circular references
class BetterNode {
public:
    std::weak_ptr<BetterNode> parent;  // Non-owning reference
    std::vector<std::shared_ptr<BetterNode>> children;
};

TEST(SmartPointerTest, WeakPtrAvoidsCycles) {
    // Arrange
    auto root = std::make_shared<BetterNode>();
    auto child = std::make_shared<BetterNode>();

    // Act - Set up parent-child relationship
    root->children.push_back(child);
    child->parent = root;  // weak_ptr doesn't increase ref count

    // Assert
    EXPECT_EQ(root.use_count(), 1);  // Only root owns itself
    EXPECT_EQ(child.use_count(), 2); // root->children and child both own

    // Verify parent is accessible
    auto parent = child->parent.lock();
    EXPECT_NE(parent, nullptr);
    EXPECT_EQ(parent, root);
}
```

### Pattern 4: Smart Pointers in Fixtures

```cpp
class ServiceTest : public testing::Test {
protected:
    void SetUp() override {
        // Use make_unique for exclusive ownership
        repository = std::make_unique<UserRepository>();

        // Use make_shared when service needs shared ownership
        cache = std::make_shared<Cache>();

        // Service takes ownership of repository, shares cache
        service = std::make_unique<UserService>(
            std::move(repository),
            cache
        );
    }

    void TearDown() override {
        // Smart pointers automatically clean up
        // No manual delete needed
    }

    std::unique_ptr<UserRepository> repository;
    std::shared_ptr<Cache> cache;
    std::unique_ptr<UserService> service;
};

TEST_F(ServiceTest, GetUserFromCache) {
    // Arrange
    cache->put(1, User("Alice", 30));

    // Act
    auto user = service->getUser(1);

    // Assert
    EXPECT_TRUE(user.has_value());
    EXPECT_EQ(user->getName(), "Alice");
}
```

## Parameterized Test Patterns (TEST_P)

### Pattern 1: Basic Parameterized Tests

```cpp
#include <gtest/gtest.h>

// Parameter struct
struct AddTestParams {
    int a;
    int b;
    int expected;
};

// Parameterized test fixture
class CalculatorParamTest : public testing::TestWithParam<AddTestParams> {
protected:
    Calculator calc;
};

// Parameterized test
TEST_P(CalculatorParamTest, AddVariousInputs) {
    // Arrange
    auto params = GetParam();

    // Act
    int result = calc.add(params.a, params.b);

    // Assert
    EXPECT_EQ(result, params.expected);
}

// Instantiate test suite with parameters
INSTANTIATE_TEST_SUITE_P(
    AdditionTests,
    CalculatorParamTest,
    testing::Values(
        AddTestParams{2, 3, 5},
        AddTestParams{0, 0, 0},
        AddTestParams{-1, 1, 0},
        AddTestParams{-5, -3, -8},
        AddTestParams{100, 200, 300}
    )
);
```

### Pattern 2: Parameterized Tests with Custom Test Names

```cpp
// Custom test name generator
struct AddTestParamsPrint {
    std::string operator()(const testing::TestParamInfo<AddTestParams>& info) const {
        std::ostringstream oss;
        oss << "Add_" << info.param.a << "_and_" << info.param.b
            << "_equals_" << info.param.expected;
        return oss.str();
    }
};

INSTANTIATE_TEST_SUITE_P(
    AdditionTests,
    CalculatorParamTest,
    testing::Values(
        AddTestParams{2, 3, 5},
        AddTestParams{-1, 1, 0}
    ),
    AddTestParamsPrint()
);
// Generates test names like: AdditionTests/CalculatorParamTest.Add_2_and_3_equals_5/0
```

### Pattern 3: Combining Multiple Parameters

```cpp
class StringOperationTest : public testing::TestWithParam<std::tuple<std::string, std::string, std::string>> {
};

TEST_P(StringOperationTest, Concatenate) {
    // Arrange
    auto [str1, str2, expected] = GetParam();

    // Act
    std::string result = str1 + str2;

    // Assert
    EXPECT_EQ(result, expected);
}

INSTANTIATE_TEST_SUITE_P(
    ConcatenationTests,
    StringOperationTest,
    testing::Values(
        std::make_tuple("Hello", "World", "HelloWorld"),
        std::make_tuple("", "Test", "Test"),
        std::make_tuple("Test", "", "Test"),
        std::make_tuple("", "", "")
    )
);
```

### Pattern 4: Parameterized Tests with Complex Types

```cpp
struct DivisionParams {
    double dividend;
    double divisor;
    double expected;
    bool should_throw;
};

class DivisionTest : public testing::TestWithParam<DivisionParams> {
protected:
    Calculator calc;
};

TEST_P(DivisionTest, DivideVariousInputs) {
    // Arrange
    auto params = GetParam();

    if (params.should_throw) {
        // Act & Assert - Expect exception
        EXPECT_THROW(calc.divide(params.dividend, params.divisor),
                     std::invalid_argument);
    } else {
        // Act
        double result = calc.divide(params.dividend, params.divisor);

        // Assert
        EXPECT_NEAR(result, params.expected, 0.0001);
    }
}

INSTANTIATE_TEST_SUITE_P(
    DivisionTests,
    DivisionTest,
    testing::Values(
        DivisionParams{10.0, 2.0, 5.0, false},
        DivisionParams{10.0, -2.0, -5.0, false},
        DivisionParams{0.0, 5.0, 0.0, false},
        DivisionParams{10.0, 0.0, 0.0, true}  // Should throw
    )
);
```

## Death Test Patterns (Testing Crashes)

### Pattern 1: Basic Death Tests

```cpp
// Function that asserts on invalid input
void processPositiveNumber(int value) {
    assert(value > 0 && "Value must be positive");
    // Process value...
}

TEST(DeathTest, ProcessNegativeNumberAsserts) {
    // Act & Assert - Expect death (crash/abort)
    EXPECT_DEATH(processPositiveNumber(-1), "Value must be positive");
}

TEST(DeathTest, NullPointerCrashes) {
    // Arrange
    int* ptr = nullptr;

    // Act & Assert - Expect crash on null dereference
    EXPECT_DEATH(*ptr = 42, "");  // Empty regex matches any output
}
```

### Pattern 2: Death Tests with Regex Matching

```cpp
void checkAge(int age) {
    if (age < 0) {
        std::cerr << "Fatal error: Age cannot be negative: " << age << std::endl;
        std::abort();
    }
}

TEST(DeathTest, NegativeAgeCrashesWithMessage) {
    // Act & Assert - Match error message with regex
    EXPECT_DEATH(checkAge(-5), "Fatal error: Age cannot be negative: -5");
}

TEST(DeathTest, AssertionFailureMessage) {
    // Act & Assert - Match assertion message
    EXPECT_DEATH({
        assert(false && "This should not happen");
    }, "This should not happen");
}
```

### Pattern 3: ASSERT_DEATH vs EXPECT_DEATH

```cpp
TEST(DeathTest, UseAssertDeathForFatalTests) {
    // ASSERT_DEATH stops test execution if death doesn't occur
    ASSERT_DEATH(std::abort(), "");

    // Code here won't run if death test fails
}

TEST(DeathTest, UseExpectDeathForContinuing) {
    // EXPECT_DEATH continues even if death doesn't occur
    EXPECT_DEATH(someFunction(), "");

    // Additional tests can run even if death test fails
    EXPECT_EQ(1 + 1, 2);
}
```

### Pattern 4: Death Tests in Separate Processes

```cpp
// Death tests run in separate process by default (safer)
TEST(DeathTest, MultipleDeathTests) {
    // Each death test runs in isolated process
    EXPECT_DEATH(std::abort(), "");
    EXPECT_DEATH(std::terminate(), "");
    EXPECT_DEATH(throw std::runtime_error("test"), "");
}

// For thread-safe death tests
TEST(DeathTest, ThreadSafeDeathTest) {
    // Use threadsafe style for multithreaded code
    testing::FLAGS_gtest_death_test_style = "threadsafe";

    EXPECT_DEATH(crashInThread(), "");
}
```

## Google Mock Patterns (EXPECT_CALL)

### Pattern 1: Creating Mock Classes

```cpp
#include <gmock/gmock.h>

// Interface to mock
class UserRepository {
public:
    virtual ~UserRepository() = default;
    virtual User getUser(int id) = 0;
    virtual void saveUser(const User& user) = 0;
    virtual bool deleteUser(int id) = 0;
};

// Mock implementation
class MockUserRepository : public UserRepository {
public:
    MOCK_METHOD(User, getUser, (int id), (override));
    MOCK_METHOD(void, saveUser, (const User& user), (override));
    MOCK_METHOD(bool, deleteUser, (int id), (override));
};
```

### Pattern 2: Setting Expectations with EXPECT_CALL

```cpp
using ::testing::Return;
using ::testing::_;

TEST(UserServiceTest, GetUserCallsRepository) {
    // Arrange
    MockUserRepository mock_repo;
    UserService service(&mock_repo);

    User expected_user("Alice", 30);
    EXPECT_CALL(mock_repo, getUser(1))
        .WillOnce(Return(expected_user));

    // Act
    User user = service.getUser(1);

    // Assert
    EXPECT_EQ(user.getName(), "Alice");
}

TEST(UserServiceTest, SaveUserCallsRepository) {
    // Arrange
    MockUserRepository mock_repo;
    UserService service(&mock_repo);
    User user("Bob", 25);

    EXPECT_CALL(mock_repo, saveUser(_))  // _ matches any argument
        .Times(1);

    // Act
    service.saveUser(user);

    // Assert - EXPECT_CALL verifies saveUser was called once
}
```

### Pattern 3: Argument Matchers

```cpp
using ::testing::Eq;
using ::testing::Ge;
using ::testing::Le;
using ::testing::Lt;
using ::testing::Gt;
using ::testing::Ne;
using ::testing::IsNull;
using ::testing::NotNull;
using ::testing::_;

TEST(MockTest, ArgumentMatchers) {
    MockUserRepository mock_repo;

    // Exact match
    EXPECT_CALL(mock_repo, getUser(Eq(1)))
        .WillOnce(Return(User("Alice", 30)));

    // Any value
    EXPECT_CALL(mock_repo, getUser(_))
        .WillRepeatedly(Return(User("Default", 0)));

    // Comparison matchers
    EXPECT_CALL(mock_repo, getUser(Ge(1)))  // >= 1
        .WillOnce(Return(User("Alice", 30)));

    EXPECT_CALL(mock_repo, getUser(Lt(100)))  // < 100
        .WillOnce(Return(User("Bob", 25)));
}

TEST(MockTest, CustomMatchers) {
    MockUserRepository mock_repo;

    // Custom matcher for User object
    EXPECT_CALL(mock_repo, saveUser(
        ::testing::Field(&User::getName, "Alice")
    )).Times(1);

    User alice("Alice", 30);
    mock_repo.saveUser(alice);
}
```

### Pattern 4: Return Values and Actions

```cpp
using ::testing::Return;
using ::testing::ReturnRef;
using ::testing::Throw;
using ::testing::DoAll;
using ::testing::SetArgReferee;

TEST(MockTest, ReturnValues) {
    MockUserRepository mock_repo;

    // Return value
    EXPECT_CALL(mock_repo, getUser(1))
        .WillOnce(Return(User("Alice", 30)));

    // Return reference
    User alice("Alice", 30);
    EXPECT_CALL(mock_repo, getUser(1))
        .WillOnce(ReturnRef(alice));

    // Throw exception
    EXPECT_CALL(mock_repo, getUser(999))
        .WillOnce(Throw(std::runtime_error("User not found")));
}

TEST(MockTest, MultipleActions) {
    MockUserRepository mock_repo;

    // Perform multiple actions
    User user;
    EXPECT_CALL(mock_repo, getUser(1))
        .WillOnce(DoAll(
            SetArgReferee<0>(user),  // Set argument
            Return(User("Alice", 30)) // Return value
        ));
}
```

### Pattern 5: Call Frequency

```cpp
using ::testing::Times;
using ::testing::AtLeast;
using ::testing::AtMost;
using ::testing::Between;

TEST(MockTest, CallFrequency) {
    MockUserRepository mock_repo;

    // Expect exactly N calls
    EXPECT_CALL(mock_repo, getUser(_))
        .Times(3);

    // Expect at least N calls
    EXPECT_CALL(mock_repo, saveUser(_))
        .Times(AtLeast(1));

    // Expect at most N calls
    EXPECT_CALL(mock_repo, deleteUser(_))
        .Times(AtMost(5));

    // Expect between N and M calls
    EXPECT_CALL(mock_repo, getUser(_))
        .Times(Between(1, 3));
}
```

### Pattern 6: Sequence and Order

```cpp
using ::testing::InSequence;

TEST(MockTest, CallOrder) {
    MockUserRepository mock_repo;

    // Enforce call order
    {
        InSequence seq;

        EXPECT_CALL(mock_repo, getUser(1))
            .WillOnce(Return(User("Alice", 30)));

        EXPECT_CALL(mock_repo, saveUser(_))
            .Times(1);

        EXPECT_CALL(mock_repo, deleteUser(1))
            .WillOnce(Return(true));
    }

    // Must be called in this order
    mock_repo.getUser(1);
    mock_repo.saveUser(User("Alice", 31));
    mock_repo.deleteUser(1);
}
```

### Pattern 7: Mock in Fixture

```cpp
class UserServiceTest : public testing::Test {
protected:
    void SetUp() override {
        mock_repo = std::make_unique<MockUserRepository>();
        service = std::make_unique<UserService>(mock_repo.get());
    }

    void TearDown() override {
        // Smart pointers automatically clean up
    }

    std::unique_ptr<MockUserRepository> mock_repo;
    std::unique_ptr<UserService> service;
};

TEST_F(UserServiceTest, ProcessUserCallsGetAndSave) {
    // Arrange
    EXPECT_CALL(*mock_repo, getUser(1))
        .WillOnce(Return(User("Alice", 30)));

    EXPECT_CALL(*mock_repo, saveUser(_))
        .Times(1);

    // Act
    service->processUser(1);

    // Assert - Mock verifies calls automatically
}
```

## Memory Safety Patterns

### Pattern 1: Avoiding Raw Pointers

```cpp
// ❌ Bad - Raw pointer, manual memory management
TEST(MemorySafetyTest, RawPointerBad) {
    User* user = new User("Alice", 30);
    // ... test code ...
    delete user;  // Easy to forget!
}

// ✅ Good - Smart pointer, automatic cleanup
TEST(MemorySafetyTest, SmartPointerGood) {
    auto user = std::make_unique<User>("Alice", 30);
    // ... test code ...
    // user automatically deleted
}
```

### Pattern 2: Container Ownership

```cpp
TEST(MemorySafetyTest, ContainerOwnership) {
    // Arrange - Vector owns the objects
    std::vector<User> users;
    users.emplace_back("Alice", 30);
    users.emplace_back("Bob", 25);

    // Act
    auto& first = users[0];

    // Assert
    EXPECT_EQ(first.getName(), "Alice");

    // users automatically cleaned up
}

TEST(MemorySafetyTest, ContainerOfSmartPointers) {
    // Arrange - Vector of unique_ptr for polymorphism
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(5.0));
    shapes.push_back(std::make_unique<Square>(4.0));

    // Act
    double total_area = 0.0;
    for (const auto& shape : shapes) {
        total_area += shape->area();
    }

    // Assert
    EXPECT_NEAR(total_area, 94.53, 0.01);

    // All shapes automatically deleted
}
```

### Pattern 3: Exception Safety

```cpp
class ResourceTest : public testing::Test {
protected:
    void SetUp() override {
        // RAII ensures cleanup even if exception thrown
        resource = std::make_unique<Resource>();
    }

    void TearDown() override {
        // Cleanup happens automatically via RAII
    }

    std::unique_ptr<Resource> resource;
};

TEST_F(ResourceTest, ExceptionDoesNotLeak) {
    // Arrange
    resource->allocate(1024);

    // Act & Assert - Even if exception thrown, resource cleaned up
    EXPECT_THROW(resource->performRiskyOperation(), std::runtime_error);

    // TearDown still called, resource properly cleaned up
}
```

### Pattern 4: Testing for Memory Leaks

```cpp
// Note: Actual leak detection requires external tools like Valgrind or AddressSanitizer

TEST(MemorySafetyTest, NoLeakWithSmartPointers) {
    // Arrange
    std::vector<std::unique_ptr<LargeObject>> objects;

    // Act - Allocate many objects
    for (int i = 0; i < 1000; ++i) {
        objects.push_back(std::make_unique<LargeObject>(i));
    }

    // Assert
    EXPECT_EQ(objects.size(), 1000);

    // Cleanup - All objects automatically deleted when vector destroyed
    // Run with: valgrind --leak-check=full ./test_executable
}
```

### Pattern 5: Move Semantics for Efficiency

```cpp
TEST(MemorySafetyTest, MoveSemantics) {
    // Arrange - Create expensive object
    std::vector<int> large_data(1000000, 42);

    // Act - Move instead of copy (efficient)
    auto moved_data = std::move(large_data);

    // Assert
    EXPECT_EQ(moved_data.size(), 1000000);
    EXPECT_TRUE(large_data.empty());  // Original is now empty (moved from)
}

TEST(MemorySafetyTest, ReturnByMove) {
    // Arrange & Act
    auto createLargeObject = []() -> std::unique_ptr<LargeObject> {
        auto obj = std::make_unique<LargeObject>(1000);
        // Return by move (automatic for unique_ptr)
        return obj;
    };

    auto result = createLargeObject();

    // Assert
    EXPECT_NE(result, nullptr);
}
```

## Assertion Patterns

### Comparison Assertions

```cpp
TEST(AssertionTest, Comparisons) {
    // Equality
    EXPECT_EQ(actual, expected);      // ==
    EXPECT_NE(actual, unexpected);    // !=

    // Relational
    EXPECT_LT(actual, upper_bound);   // <
    EXPECT_LE(actual, upper_bound);   // <=
    EXPECT_GT(actual, lower_bound);   // >
    EXPECT_GE(actual, lower_bound);   // >=
}

TEST(AssertionTest, NonfatalVsFatal) {
    // EXPECT_* continues after failure (non-fatal)
    EXPECT_EQ(1, 2);
    EXPECT_EQ(3, 4);  // This runs even if above fails

    // ASSERT_* stops test execution (fatal)
    ASSERT_EQ(1, 2);
    EXPECT_EQ(3, 4);  // This does NOT run if above fails
}
```

### Boolean Assertions

```cpp
TEST(AssertionTest, Boolean) {
    bool condition = true;

    EXPECT_TRUE(condition);
    EXPECT_FALSE(!condition);

    // Pointer checks
    int* ptr = nullptr;
    EXPECT_EQ(ptr, nullptr);
    EXPECT_TRUE(ptr == nullptr);
}
```

### String Assertions

```cpp
TEST(AssertionTest, Strings) {
    const char* c_str1 = "Hello";
    const char* c_str2 = "Hello";
    std::string str1 = "Hello";
    std::string str2 = "Hello";

    // C-strings
    EXPECT_STREQ(c_str1, c_str2);     // String equality
    EXPECT_STRNE(c_str1, "World");    // String inequality
    EXPECT_STRCASEEQ("Hello", "hello");  // Case-insensitive

    // std::string
    EXPECT_EQ(str1, str2);
    EXPECT_NE(str1, "World");
}
```

### Floating-Point Assertions

```cpp
TEST(AssertionTest, FloatingPoint) {
    double pi = 3.14159;

    // Approximate equality (accounts for floating-point errors)
    EXPECT_DOUBLE_EQ(pi, 3.14159);
    EXPECT_FLOAT_EQ(3.14f, 3.14f);

    // Near with tolerance
    EXPECT_NEAR(pi, 3.14, 0.01);  // Within 0.01
}
```

### Exception Assertions

```cpp
TEST(AssertionTest, Exceptions) {
    // Expect specific exception
    EXPECT_THROW(throwException(), std::runtime_error);

    // Expect any exception
    EXPECT_ANY_THROW(throwException());

    // Expect no exception
    EXPECT_NO_THROW(safeFunction());
}
```

### Predicate Assertions

```cpp
bool isPrime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; ++i) {
        if (n % i == 0) return false;
    }
    return true;
}

TEST(AssertionTest, Predicates) {
    // Custom predicate
    EXPECT_PRED1(isPrime, 7);
    EXPECT_PRED1(isPrime, 11);

    // Lambda predicate
    EXPECT_TRUE([](int x) { return x > 0; }(5));
}
```

## Catch2 Patterns (Alternative Framework)

### Basic Test Structure

```cpp
#include <catch2/catch_test_macros.hpp>

TEST_CASE("Calculator addition", "[calculator]") {
    // Arrange
    Calculator calc;

    SECTION("Adding positive numbers") {
        // Act
        int result = calc.add(2, 3);

        // Assert
        REQUIRE(result == 5);
    }

    SECTION("Adding negative numbers") {
        // Act
        int result = calc.add(-2, -3);

        // Assert
        REQUIRE(result == -5);
    }

    SECTION("Adding with zero") {
        // Act
        int result = calc.add(5, 0);

        // Assert
        REQUIRE(result == 5);
    }
}
```

### REQUIRE vs CHECK

```cpp
TEST_CASE("Assertions in Catch2", "[assertions]") {
    // REQUIRE - fatal assertion (stops test on failure)
    REQUIRE(1 + 1 == 2);

    // CHECK - non-fatal assertion (continues on failure)
    CHECK(2 + 2 == 4);
    CHECK(3 + 3 == 6);  // Runs even if above fails

    // REQUIRE_THROWS - expect exception
    REQUIRE_THROWS_AS(throwException(), std::runtime_error);

    // REQUIRE_NOTHROW - expect no exception
    REQUIRE_NOTHROW(safeFunction());
}
```

### Sections for Shared Setup

```cpp
TEST_CASE("Database operations", "[database]") {
    // Common setup
    Database db("test.db");
    db.connect();

    SECTION("Insert user") {
        db.insert(User("Alice", 30));
        REQUIRE(db.count() == 1);
    }

    SECTION("Delete user") {
        db.insert(User("Bob", 25));
        db.remove(1);
        REQUIRE(db.count() == 0);
    }

    // Each SECTION gets fresh db (setup re-runs)
}
```

### Generators for Parameterized Tests

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>

TEST_CASE("Parameterized addition", "[calculator]") {
    Calculator calc;

    auto [a, b, expected] = GENERATE(table<int, int, int>({
        {2, 3, 5},
        {0, 0, 0},
        {-1, 1, 0},
        {-5, -3, -8}
    }));

    REQUIRE(calc.add(a, b) == expected);
}
```

## Best Practices and Common Pitfalls

### Best Practices

1. **Use Smart Pointers**: Always prefer `unique_ptr` or `shared_ptr` over raw pointers
2. **RAII Everywhere**: Use constructors/destructors for resource management
3. **Const Correctness**: Mark methods and parameters `const` when possible
4. **Move Semantics**: Use `std::move` for expensive objects
5. **Explicit Constructors**: Use `explicit` for single-argument constructors
6. **Delete Special Members**: Use `= delete` for non-copyable resources
7. **Override Keyword**: Always use `override` for virtual function overrides
8. **Nullptr**: Use `nullptr` instead of `NULL` or `0`
9. **Auto Keyword**: Use `auto` for complex types to avoid errors
10. **Range-Based Loops**: Use `for (const auto& item : container)` for iteration

### Common Pitfalls

#### Pitfall 1: Memory Leaks with Raw Pointers

```cpp
// ❌ Bad
TEST(BadTest, RawPointerLeak) {
    User* user = new User("Alice", 30);
    // Test code...
    // Forgot to delete!
}

// ✅ Good
TEST(GoodTest, SmartPointer) {
    auto user = std::make_unique<User>("Alice", 30);
    // Automatic cleanup
}
```

#### Pitfall 2: Dangling Pointers

```cpp
// ❌ Bad
TEST(BadTest, DanglingPointer) {
    User* user_ptr;
    {
        User user("Alice", 30);
        user_ptr = &user;
    } // user destroyed here
    // user_ptr is now dangling!
    EXPECT_EQ(user_ptr->getName(), "Alice");  // Undefined behavior!
}

// ✅ Good
TEST(GoodTest, ProperLifetime) {
    auto user = std::make_unique<User>("Alice", 30);
    User* user_ptr = user.get();
    EXPECT_EQ(user_ptr->getName(), "Alice");
    // user destroyed after test, user_ptr not used after
}
```

#### Pitfall 3: Shared State Between Tests

```cpp
// ❌ Bad
static int global_counter = 0;

TEST(BadTest, Test1) {
    global_counter++;
    EXPECT_EQ(global_counter, 1);  // Depends on execution order!
}

TEST(BadTest, Test2) {
    global_counter++;
    EXPECT_EQ(global_counter, 1);  // Fails if Test1 runs first!
}

// ✅ Good
TEST(GoodTest, Test1) {
    int counter = 0;
    counter++;
    EXPECT_EQ(counter, 1);
}

TEST(GoodTest, Test2) {
    int counter = 0;
    counter++;
    EXPECT_EQ(counter, 1);
}
```

#### Pitfall 4: Testing Implementation Details

```cpp
// ❌ Bad
TEST(BadTest, InternalImplementation) {
    Sorter sorter;
    sorter.sort({3, 1, 2});
    EXPECT_EQ(sorter.algorithm_used_, "quicksort");  // Tests internal detail
}

// ✅ Good
TEST(GoodTest, Behavior) {
    Sorter sorter;
    auto result = sorter.sort({3, 1, 2});
    EXPECT_EQ(result, std::vector<int>({1, 2, 3}));  // Tests behavior
}
```

#### Pitfall 5: Not Checking Return Values

```cpp
// ❌ Bad
TEST(BadTest, IgnoresReturnValue) {
    database.insert(user);  // Returns bool, not checked
}

// ✅ Good
TEST(GoodTest, ChecksReturnValue) {
    bool success = database.insert(user);
    EXPECT_TRUE(success);
}
```

## Integration with Build Systems

### CMake Integration

```cmake
# CMakeLists.txt for tests
cmake_minimum_required(VERSION 3.15)
project(MyProjectTests CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Google Test
find_package(GTest REQUIRED)
include(GoogleTest)

# Enable testing
enable_testing()

# Add test executable
add_executable(my_tests
    test_calculator.cpp
    test_database.cpp
    test_main.cpp
)

# Link against Google Test and project library
target_link_libraries(my_tests
    GTest::GTest
    GTest::Main
    my_project_lib
)

# Discover tests for CTest
gtest_discover_tests(my_tests)

# Optionally enable code coverage
if(ENABLE_COVERAGE)
    target_compile_options(my_tests PRIVATE --coverage)
    target_link_options(my_tests PRIVATE --coverage)
endif()
```

### Test Main File

```cpp
// test_main.cpp
#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

## References

- Google Test Documentation: https://google.github.io/googletest/
- Google Mock Documentation: https://google.github.io/googletest/gmock_for_dummies.html
- Catch2 Documentation: https://github.com/catchorg/Catch2
- C++ Core Guidelines: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- Smart Pointers: https://en.cppreference.com/w/cpp/memory
- RAII: https://en.cppreference.com/w/cpp/language/raii
- Google Test Templates: `skills/templates/cpp-gtest-template.md`
- Catch2 Templates: `skills/templates/cpp-catch2-template.md`

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
