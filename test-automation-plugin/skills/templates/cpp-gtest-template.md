# Google Test (gtest) Template

**Purpose**: Template for generating Google Test test files for C++ projects
**Target Language**: C++
**Test Framework**: Google Test (gtest/gmock)
**Version Support**: Google Test 1.12+, C++17+

## Overview

This template provides copy-paste ready test patterns for Google Test, the industry-standard C++ testing framework. Includes comprehensive examples for TEST, TEST_F fixtures, parameterized tests, death tests, Google Mock, RAII patterns, and smart pointer usage.

## Template Structure

### Basic Test File Template

```cpp
/**
 * Test module for {{MODULE_NAME}}.
 *
 * Test coverage:
 * - {{TEST_COVERAGE_AREA_1}}
 * - {{TEST_COVERAGE_AREA_2}}
 * - {{TEST_COVERAGE_AREA_3}}
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include <string>
#include <vector>
#include "{{SOURCE_HEADER}}"

// ============================================================================
// Test Suite: {{TEST_SUITE_NAME}}
// ============================================================================

{{TEST_CASES}}
```

## Template Placeholders

### Module-Level Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{MODULE_NAME}}` | Name of module being tested | `Calculator`, `UserService`, `Database` |
| `{{TEST_COVERAGE_AREA_N}}` | Areas of functionality covered | `Addition operations`, `Error handling`, `Resource cleanup` |
| `{{SOURCE_HEADER}}` | Header file being tested | `calculator.h`, `user_service.h` |
| `{{TEST_SUITE_NAME}}` | Name of test suite | `CalculatorTest`, `UserServiceTest` |
| `{{TEST_CASES}}` | Individual test case definitions | See Test Case Patterns |

### Test Case Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_NAME}}` | Name of individual test | `AddPositiveNumbers`, `DivideByZeroThrows` |
| `{{FIXTURE_NAME}}` | Name of fixture class | `DatabaseTest`, `CalculatorTest` |
| `{{SETUP_CODE}}` | Setup code (Arrange) | `Calculator calc;`<br>`int a = 5, b = 3;` |
| `{{CODE_UNDER_TEST}}` | Code being tested (Act) | `int result = calc.add(a, b);` |
| `{{ASSERTIONS}}` | Assertion code (Assert) | `EXPECT_EQ(result, 8);` |
| `{{CLASS_NAME}}` | Class being tested | `Calculator`, `Database` |

## Google Test Conventions

### Naming Conventions

**Test Files**:
- Pattern: `test_*.cpp` or `*_test.cpp`
- Examples: `test_calculator.cpp`, `calculator_test.cpp`
- Location: `tests/` directory

**Test Suites**:
- Pattern: `PascalCase` with `Test` suffix
- Examples: `CalculatorTest`, `DatabaseTest`
- Format: `TEST(TestSuiteName, TestName)`

**Test Names**:
- Pattern: `PascalCase` describing behavior
- Examples: `AddPositiveNumbers`, `DivideByZeroThrows`
- Format: `Test<What><Condition><Expected>`

**Fixture Classes**:
- Pattern: `PascalCase` ending in `Test`
- Examples: `DatabaseTest`, `UserServiceTest`
- Inherit: `testing::Test`

### File Structure

```
project/
├── include/
│   └── mylib/
│       ├── calculator.h
│       └── database.h
├── src/
│   ├── calculator.cpp
│   └── database.cpp
├── tests/
│   ├── CMakeLists.txt
│   ├── test_main.cpp
│   ├── test_calculator.cpp
│   └── test_database.cpp
└── CMakeLists.txt
```

## Basic TEST Macro Template

### Simple Function Test

```cpp
#include <gtest/gtest.h>
#include "{{HEADER_FILE}}"

// ============================================================================
// Test Suite: {{TEST_SUITE_NAME}}
// ============================================================================

TEST({{TEST_SUITE_NAME}}, {{TEST_NAME}}) {
    // Arrange
    {{SETUP_CODE}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

```cpp
#include <gtest/gtest.h>
#include "calculator.h"

// ============================================================================
// Test Suite: CalculatorTest
// ============================================================================

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

## TEST_F Fixture Template

### Fixture Class with Setup/Teardown

```cpp
#include <gtest/gtest.h>
#include <memory>
#include "{{HEADER_FILE}}"

// ============================================================================
// Fixture Class: {{FIXTURE_NAME}}
// ============================================================================

class {{FIXTURE_NAME}} : public testing::Test {
protected:
    // SetUp() runs before each test
    void SetUp() override {
        {{SETUP_CODE}}
    }

    // TearDown() runs after each test
    void TearDown() override {
        {{TEARDOWN_CODE}}
    }

    // Helper method available to all tests
    {{HELPER_METHODS}}

    // Fixture member variables
    {{MEMBER_VARIABLES}}
};

// Use TEST_F to access fixture members
TEST_F({{FIXTURE_NAME}}, {{TEST_NAME}}) {
    // Arrange
    {{ADDITIONAL_SETUP}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

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
class {{FIXTURE_NAME}} : public testing::Test {
protected:
    // SetUpTestSuite() runs once before all tests in this suite
    static void SetUpTestSuite() {
        {{CLASS_LEVEL_SETUP}}
    }

    // TearDownTestSuite() runs once after all tests in this suite
    static void TearDownTestSuite() {
        {{CLASS_LEVEL_TEARDOWN}}
    }

    // SetUp() runs before each test (optional)
    void SetUp() override {
        {{PER_TEST_SETUP}}
    }

    // Shared across all tests in this suite
    static {{SHARED_RESOURCE_TYPE}} {{SHARED_RESOURCE_NAME}};
};

// Define static member
{{SHARED_RESOURCE_TYPE}} {{FIXTURE_NAME}}::{{SHARED_RESOURCE_NAME}} = {{INITIAL_VALUE}};
```

**Example:**

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

## RAII Resource Management Template

### Automatic Cleanup with Smart Pointers

```cpp
TEST_F({{FIXTURE_NAME}}, {{TEST_NAME}}) {
    // Arrange - Use RAII with smart pointers
    auto {{RESOURCE_NAME}} = std::make_unique<{{RESOURCE_TYPE}}>({{CONSTRUCTOR_ARGS}});
    {{RESOURCE_NAME}}->{{SETUP_METHOD}}();

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}

    // {{RESOURCE_NAME}} automatically cleaned up when scope ends
}
```

**Example:**

```cpp
TEST(FileHandleTest, ReadFileAutomaticCleanup) {
    // Arrange - RAII ensures file is closed
    const std::string filename = "test.txt";
    {
        std::ofstream out(filename);
        out << "test content";
    } // File closed automatically

    // Act
    std::ifstream in(filename);
    std::string content((std::istreambuf_iterator<char>(in)),
                        std::istreambuf_iterator<char>());

    // Assert
    EXPECT_EQ(content, "test content");

    // Cleanup test file
    std::filesystem::remove(filename);
}
```

### Fixture with RAII

```cpp
class TemporaryFileTest : public testing::Test {
protected:
    void SetUp() override {
        // Create temporary file with RAII
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

## Smart Pointer Patterns

### unique_ptr for Exclusive Ownership

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

### shared_ptr for Shared Ownership

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

### Smart Pointers in Fixtures

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

## Parameterized Test Template (TEST_P)

### Basic Parameterized Test

```cpp
// Parameter struct
struct {{PARAM_STRUCT_NAME}} {
    {{PARAM_TYPE_1}} {{PARAM_NAME_1}};
    {{PARAM_TYPE_2}} {{PARAM_NAME_2}};
    {{PARAM_TYPE_3}} {{EXPECTED_NAME}};
};

// Parameterized test fixture
class {{FIXTURE_NAME}} : public testing::TestWithParam<{{PARAM_STRUCT_NAME}}> {
protected:
    {{FIXTURE_MEMBERS}}
};

// Parameterized test
TEST_P({{FIXTURE_NAME}}, {{TEST_NAME}}) {
    // Arrange
    auto params = GetParam();

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}

// Instantiate test suite with parameters
INSTANTIATE_TEST_SUITE_P(
    {{INSTANTIATION_NAME}},
    {{FIXTURE_NAME}},
    testing::Values(
        {{PARAM_STRUCT_NAME}}{{{VALUES_1}}},
        {{PARAM_STRUCT_NAME}}{{{VALUES_2}}},
        {{PARAM_STRUCT_NAME}}{{{VALUES_3}}}
    )
);
```

**Example:**

```cpp
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

### Parameterized with Custom Test Names

```cpp
// Custom test name generator
struct {{PARAM_PRINT_STRUCT}} {
    std::string operator()(const testing::TestParamInfo<{{PARAM_STRUCT_NAME}}>& info) const {
        std::ostringstream oss;
        oss << {{CUSTOM_NAME_FORMAT}};
        return oss.str();
    }
};

INSTANTIATE_TEST_SUITE_P(
    {{INSTANTIATION_NAME}},
    {{FIXTURE_NAME}},
    testing::Values({{PARAM_VALUES}}),
    {{PARAM_PRINT_STRUCT}}()
);
```

**Example:**

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

## Death Test Template

### Basic Death Tests

```cpp
TEST({{TEST_SUITE_NAME}}, {{TEST_NAME}}_Crashes) {
    // Act & Assert - Expect death (crash/abort)
    EXPECT_DEATH({{CRASHING_CODE}}, "{{EXPECTED_MESSAGE_REGEX}}");
}

TEST({{TEST_SUITE_NAME}}, {{TEST_NAME}}_Asserts) {
    // Act & Assert - Expect assertion failure
    ASSERT_DEATH({
        assert({{FALSE_CONDITION}} && "{{ERROR_MESSAGE}}");
    }, "{{ERROR_MESSAGE}}");
}
```

**Example:**

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
```

## Google Mock Template (EXPECT_CALL)

### Creating Mock Classes

```cpp
#include <gmock/gmock.h>

// Interface to mock
class {{INTERFACE_NAME}} {
public:
    virtual ~{{INTERFACE_NAME}}() = default;
    virtual {{RETURN_TYPE_1}} {{METHOD_NAME_1}}({{PARAMS_1}}) = 0;
    virtual {{RETURN_TYPE_2}} {{METHOD_NAME_2}}({{PARAMS_2}}) = 0;
};

// Mock implementation
class Mock{{INTERFACE_NAME}} : public {{INTERFACE_NAME}} {
public:
    MOCK_METHOD({{RETURN_TYPE_1}}, {{METHOD_NAME_1}}, ({{PARAMS_1}}), (override));
    MOCK_METHOD({{RETURN_TYPE_2}}, {{METHOD_NAME_2}}, ({{PARAMS_2}}), (override));
};
```

**Example:**

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

### Setting Expectations with EXPECT_CALL

```cpp
using ::testing::Return;
using ::testing::_;

TEST({{TEST_SUITE_NAME}}, {{TEST_NAME}}) {
    // Arrange
    Mock{{INTERFACE_NAME}} mock_{{DEPENDENCY}};
    {{SERVICE_TYPE}} service(&mock_{{DEPENDENCY}});

    {{EXPECTED_VALUE_TYPE}} expected_{{VALUE}} = {{EXPECTED_VALUE}};
    EXPECT_CALL(mock_{{DEPENDENCY}}, {{METHOD_NAME}}({{EXPECTED_ARGS}}))
        .WillOnce(Return(expected_{{VALUE}}));

    // Act
    {{RESULT_TYPE}} {{RESULT}} = service.{{SERVICE_METHOD}}({{ARGS}});

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

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

### Mock in Fixture

```cpp
class {{SERVICE_NAME}}Test : public testing::Test {
protected:
    void SetUp() override {
        mock_{{DEPENDENCY}} = std::make_unique<Mock{{INTERFACE_NAME}}>();
        service = std::make_unique<{{SERVICE_NAME}}>(mock_{{DEPENDENCY}}.get());
    }

    void TearDown() override {
        // Smart pointers automatically clean up
    }

    std::unique_ptr<Mock{{INTERFACE_NAME}}> mock_{{DEPENDENCY}};
    std::unique_ptr<{{SERVICE_NAME}}> service;
};

TEST_F({{SERVICE_NAME}}Test, {{TEST_NAME}}) {
    // Arrange
    EXPECT_CALL(*mock_{{DEPENDENCY}}, {{METHOD_NAME}}({{ARGS}}))
        .WillOnce(Return({{RETURN_VALUE}}));

    // Act
    {{RESULT_TYPE}} result = service->{{SERVICE_METHOD}}({{SERVICE_ARGS}});

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

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

## Common Google Test Assertions

```cpp
// ============================================================================
// Comparison Assertions
// ============================================================================

EXPECT_EQ(actual, expected);      // ==
EXPECT_NE(actual, unexpected);    // !=
EXPECT_LT(actual, upper_bound);   // <
EXPECT_LE(actual, upper_bound);   // <=
EXPECT_GT(actual, lower_bound);   // >
EXPECT_GE(actual, lower_bound);   // >=

// ============================================================================
// Boolean Assertions
// ============================================================================

EXPECT_TRUE(condition);
EXPECT_FALSE(condition);

// ============================================================================
// String Assertions
// ============================================================================

EXPECT_STREQ(c_str1, c_str2);     // C-string equality
EXPECT_STRNE(c_str1, "World");    // C-string inequality
EXPECT_STRCASEEQ("Hello", "hello");  // Case-insensitive

// std::string
EXPECT_EQ(str1, str2);
EXPECT_NE(str1, "World");

// ============================================================================
// Floating-Point Assertions
// ============================================================================

EXPECT_DOUBLE_EQ(pi, 3.14159);
EXPECT_FLOAT_EQ(3.14f, 3.14f);
EXPECT_NEAR(pi, 3.14, 0.01);  // Within 0.01

// ============================================================================
// Exception Assertions
// ============================================================================

EXPECT_THROW(throwException(), std::runtime_error);
EXPECT_ANY_THROW(throwException());
EXPECT_NO_THROW(safeFunction());

// ============================================================================
// Fatal vs Non-Fatal
// ============================================================================

EXPECT_EQ(1, 2);  // Non-fatal (test continues)
ASSERT_EQ(1, 2);  // Fatal (test stops)
```

## Complete Example Test File

```cpp
/**
 * Test module for Calculator.
 *
 * Test coverage:
 * - Basic arithmetic operations (add, subtract, multiply, divide)
 * - Edge cases (zero, negative numbers)
 * - Error handling (division by zero)
 * - RAII and smart pointer usage
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include "calculator.h"

using ::testing::Return;
using ::testing::_;

// ============================================================================
// Test Suite: CalculatorTest (Basic Tests)
// ============================================================================

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

// ============================================================================
// Fixture Tests with Smart Pointers
// ============================================================================

class CalculatorFixtureTest : public testing::Test {
protected:
    void SetUp() override {
        // Use smart pointer for automatic cleanup
        calc = std::make_unique<Calculator>();
    }

    void TearDown() override {
        // calc automatically deleted
    }

    std::unique_ptr<Calculator> calc;
};

TEST_F(CalculatorFixtureTest, MultiplyNumbers) {
    // Arrange
    int a = 4;
    int b = 5;

    // Act
    int result = calc->multiply(a, b);

    // Assert
    EXPECT_EQ(result, 20);
}

// ============================================================================
// Parameterized Tests
// ============================================================================

struct AddTestParams {
    int a;
    int b;
    int expected;
};

class CalculatorParamTest : public testing::TestWithParam<AddTestParams> {
protected:
    Calculator calc;
};

TEST_P(CalculatorParamTest, AddVariousInputs) {
    // Arrange
    auto params = GetParam();

    // Act
    int result = calc.add(params.a, params.b);

    // Assert
    EXPECT_EQ(result, params.expected);
}

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

## Test Main Template

```cpp
// test_main.cpp
#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

## CMake Integration

```cmake
# CMakeLists.txt for tests
cmake_minimum_required(VERSION 3.15)
project({{PROJECT_NAME}}Tests CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Google Test
find_package(GTest REQUIRED)
include(GoogleTest)

# Enable testing
enable_testing()

# Add test executable
add_executable({{TEST_EXECUTABLE}}
    test_{{MODULE}}.cpp
    test_main.cpp
)

# Link against Google Test and project library
target_link_libraries({{TEST_EXECUTABLE}}
    GTest::GTest
    GTest::Main
    GTest::gmock
    {{PROJECT_LIBRARY}}
)

# Discover tests for CTest
gtest_discover_tests({{TEST_EXECUTABLE}})

# Optionally enable code coverage
if(ENABLE_COVERAGE)
    target_compile_options({{TEST_EXECUTABLE}} PRIVATE --coverage)
    target_link_options({{TEST_EXECUTABLE}} PRIVATE --coverage)
endif()
```

## Usage Guide

### Step 1: Choose the Right Pattern

- **TEST Macro**: Simple function tests, no shared setup
- **TEST_F Fixture**: Tests requiring setup/teardown, shared state
- **TEST_P Parameterized**: Multiple test cases with different inputs
- **Death Tests**: Testing crashes, assertions, abort conditions
- **Google Mock**: Testing with mocked dependencies

### Step 2: Customize Placeholders

Replace all `{{PLACEHOLDER}}` values:

1. Test suite/fixture names (`{{TEST_SUITE_NAME}}`, `{{FIXTURE_NAME}}`)
2. Test names (`{{TEST_NAME}}`)
3. Setup/Act/Assert code blocks
4. Member variables and types
5. Assertion expectations

### Step 3: Add Smart Pointers and RAII

1. Use `std::make_unique<>` for exclusive ownership
2. Use `std::make_shared<>` for shared ownership
3. Let destructors handle cleanup automatically
4. Avoid raw `new`/`delete`

### Step 4: Run Tests

```bash
# Build tests
mkdir build && cd build
cmake ..
cmake --build .

# Run tests
ctest --output-on-failure

# Or run test executable directly
./test_calculator

# With Google Test filters
./test_calculator --gtest_filter=CalculatorTest.*

# With XML output
./test_calculator --gtest_output=xml:test_results.xml
```

## Best Practices

1. **Use AAA Pattern**: Always structure tests with Arrange-Act-Assert comments
2. **Smart Pointers**: Prefer `unique_ptr` and `shared_ptr` over raw pointers
3. **RAII**: Use constructors/destructors for resource management
4. **Descriptive Names**: Test names should explain what's being tested
5. **One Behavior Per Test**: Focus each test on one specific behavior
6. **EXPECT vs ASSERT**: Use EXPECT for non-fatal, ASSERT for fatal assertions
7. **Mock External Dependencies**: Use Google Mock for dependencies
8. **Test Edge Cases**: Zero, null, negative, boundary values
9. **Const Correctness**: Mark methods and parameters const when appropriate
10. **Use Fixtures**: Share common setup across related tests

## Related Skills

- **Framework Detection**: `skills/framework-detection/cpp-frameworks.md`
- **Test Generation**: `skills/test-generation/cpp-patterns.md`
- **Result Parsing**: `skills/result-parsing/parsers/gtest-parser.md`
- **Build Integration**: `skills/build-integration/cmake-build-system.md`

---

**Template Version**: 1.0.0
**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
