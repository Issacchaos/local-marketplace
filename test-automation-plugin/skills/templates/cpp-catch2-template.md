# Catch2 Test Template

**Purpose**: Template for generating Catch2 test files for C++ projects
**Target Language**: C++
**Test Framework**: Catch2 (v3.x)
**Version Support**: Catch2 3.0+, C++17+

## Overview

This template provides copy-paste ready test patterns for Catch2, a modern, header-only C++ testing framework. Features BDD-style TEST_CASE and SECTION patterns, natural assertion syntax, RAII patterns, smart pointers, and comprehensive examples.

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

#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <memory>
#include <string>
#include <vector>
#include "{{SOURCE_HEADER}}"

// ============================================================================
// Test Cases: {{MODULE_NAME}}
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
| `{{TEST_CASES}}` | Individual test case definitions | See Test Case Patterns |

### Test Case Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_DESCRIPTION}}` | Descriptive test case name | `"Calculator addition works correctly"` |
| `{{TEST_TAG}}` | Category tag for test | `"[calculator]"`, `"[unit]"`, `"[integration]"` |
| `{{SECTION_NAME}}` | Name for section/scenario | `"Adding positive numbers"` |
| `{{SETUP_CODE}}` | Setup code (Given/Arrange) | `Calculator calc;`<br>`int a = 5, b = 3;` |
| `{{CODE_UNDER_TEST}}` | Code being tested (When/Act) | `int result = calc.add(a, b);` |
| `{{ASSERTIONS}}` | Assertion code (Then/Assert) | `REQUIRE(result == 8);` |

## Catch2 Conventions

### Naming Conventions

**Test Files**:
- Pattern: `test_*.cpp` or `*_test.cpp`
- Examples: `test_calculator.cpp`, `calculator_test.cpp`
- Location: `tests/` directory

**Test Cases**:
- Pattern: Descriptive string in quotes
- Examples: `"Calculator addition"`, `"Database operations"`
- Format: Natural language description

**Tags**:
- Pattern: `[tag_name]` in square brackets
- Examples: `[calculator]`, `[unit]`, `[integration]`, `[slow]`
- Multiple tags: `[calculator][unit]`

**Sections**:
- Pattern: Descriptive string in quotes
- Examples: `"Adding positive numbers"`, `"With invalid input"`
- Format: BDD-style (Given/When/Then)

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

## Basic TEST_CASE Template

### Simple Test Case

```cpp
#include <catch2/catch_test_macros.hpp>
#include "{{HEADER_FILE}}"

TEST_CASE("{{TEST_DESCRIPTION}}", "{{TEST_TAG}}") {
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
#include <catch2/catch_test_macros.hpp>
#include "calculator.h"

TEST_CASE("Calculator addition works correctly", "[calculator]") {
    // Arrange
    Calculator calc;
    int a = 5;
    int b = 3;
    int expected = 8;

    // Act
    int result = calc.add(a, b);

    // Assert
    REQUIRE(result == expected);
    REQUIRE(result > 0);
}

TEST_CASE("Calculator subtraction works correctly", "[calculator]") {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.subtract(10, 3);

    // Assert
    REQUIRE(result == 7);
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("Calculator handles zero correctly", "[calculator][edge-case]") {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.add(5, 0);

    // Assert
    REQUIRE(result == 5);
}

TEST_CASE("Calculator handles negative numbers", "[calculator][edge-case]") {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.add(-5, -3);

    // Assert
    REQUIRE(result == -8);
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("Calculator throws on division by zero", "[calculator][error]") {
    // Arrange
    Calculator calc;

    // Act & Assert
    REQUIRE_THROWS_AS(calc.divide(10, 0), std::invalid_argument);
}
```

## SECTION Pattern (BDD-Style)

### Test Case with Multiple Sections

```cpp
TEST_CASE("{{TEST_DESCRIPTION}}", "{{TEST_TAG}}") {
    // Common setup for all sections
    {{COMMON_SETUP}}

    SECTION("{{SECTION_1_NAME}}") {
        // Arrange
        {{SECTION_1_SETUP}}

        // Act
        {{SECTION_1_CODE}}

        // Assert
        {{SECTION_1_ASSERTIONS}}
    }

    SECTION("{{SECTION_2_NAME}}") {
        // Arrange
        {{SECTION_2_SETUP}}

        // Act
        {{SECTION_2_CODE}}

        // Assert
        {{SECTION_2_ASSERTIONS}}
    }

    SECTION("{{SECTION_3_NAME}}") {
        // Arrange
        {{SECTION_3_SETUP}}

        // Act
        {{SECTION_3_CODE}}

        // Assert
        {{SECTION_3_ASSERTIONS}}
    }
}
```

**Example:**

```cpp
#include <catch2/catch_test_macros.hpp>
#include "calculator.h"

TEST_CASE("Calculator operations", "[calculator]") {
    // Common setup - runs before each SECTION
    Calculator calc;

    SECTION("Adding positive numbers") {
        // Arrange
        int a = 2;
        int b = 3;
        int expected = 5;

        // Act
        int result = calc.add(a, b);

        // Assert
        REQUIRE(result == expected);
    }

    SECTION("Adding negative numbers") {
        // Arrange
        int a = -2;
        int b = -3;
        int expected = -5;

        // Act
        int result = calc.add(a, b);

        // Assert
        REQUIRE(result == expected);
    }

    SECTION("Adding with zero") {
        // Arrange
        int a = 5;
        int b = 0;
        int expected = 5;

        // Act
        int result = calc.add(a, b);

        // Assert
        REQUIRE(result == expected);
    }
}
```

### Nested Sections (BDD Scenario)

```cpp
TEST_CASE("{{FEATURE_DESCRIPTION}}", "{{TEST_TAG}}") {
    // Given - Initial context
    {{GIVEN_SETUP}}

    SECTION("{{WHEN_CONDITION_1}}") {
        // When - Action/event
        {{WHEN_1_CODE}}

        SECTION("{{THEN_OUTCOME_1}}") {
            // Then - Expected result
            {{THEN_1_ASSERTIONS}}
        }

        SECTION("{{THEN_OUTCOME_2}}") {
            // Then - Alternative result
            {{THEN_2_ASSERTIONS}}
        }
    }

    SECTION("{{WHEN_CONDITION_2}}") {
        // When - Different action
        {{WHEN_2_CODE}}

        SECTION("{{THEN_OUTCOME_3}}") {
            // Then - Expected result
            {{THEN_3_ASSERTIONS}}
        }
    }
}
```

**Example:**

```cpp
TEST_CASE("Database user operations", "[database][bdd]") {
    // Given - A database connection
    Database db("test.db");
    db.connect();
    db.createTables();

    SECTION("When inserting a new user") {
        // When
        User user{"Alice", 30};
        int user_id = db.insertUser(user);

        SECTION("Then the user can be retrieved") {
            // Then
            auto retrieved = db.getUser(user_id);
            REQUIRE(retrieved.name == "Alice");
            REQUIRE(retrieved.age == 30);
        }

        SECTION("Then the user count increases") {
            // Then
            REQUIRE(db.getUserCount() == 1);
        }
    }

    SECTION("When deleting an existing user") {
        // Given - A user exists
        User user{"Bob", 25};
        int user_id = db.insertUser(user);

        // When
        bool deleted = db.deleteUser(user_id);

        SECTION("Then deletion succeeds") {
            // Then
            REQUIRE(deleted == true);
        }

        SECTION("Then the user cannot be found") {
            // Then
            REQUIRE_THROWS(db.getUser(user_id));
        }
    }

    // Cleanup
    db.disconnect();
}
```

## RAII Resource Management

### Automatic Cleanup with Smart Pointers

```cpp
TEST_CASE("{{TEST_DESCRIPTION}}", "{{TEST_TAG}}") {
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
TEST_CASE("File operations with automatic cleanup", "[file][raii]") {
    // Arrange - RAII ensures file is closed
    const std::string filename = "test.txt";
    {
        std::ofstream out(filename);
        out << "test content";
    } // File closed automatically

    SECTION("Reading file content") {
        // Act
        std::ifstream in(filename);
        std::string content((std::istreambuf_iterator<char>(in)),
                            std::istreambuf_iterator<char>());

        // Assert
        REQUIRE(content == "test content");
    }

    // Cleanup test file
    std::filesystem::remove(filename);
}

TEST_CASE("Database connection with RAII", "[database][raii]") {
    // Arrange - Database connection automatically managed
    auto db = std::make_unique<Database>();
    db->connect("test.db");

    SECTION("Inserting data") {
        // Act
        db->execute("INSERT INTO users VALUES (1, 'Alice')");

        // Assert
        auto result = db->query("SELECT * FROM users WHERE id = 1");
        REQUIRE(result.size() == 1);
        REQUIRE(result[0].name == "Alice");
    }

    SECTION("Querying data") {
        // Act
        auto result = db->query("SELECT * FROM users");

        // Assert
        REQUIRE(result.size() >= 0);
    }

    // db automatically disconnects when unique_ptr is destroyed
}
```

## Smart Pointer Patterns

### unique_ptr for Exclusive Ownership

```cpp
TEST_CASE("Smart pointers - unique_ptr", "[smart-pointers]") {
    SECTION("Exclusive ownership") {
        // Arrange - unique_ptr for single ownership
        auto user = std::make_unique<User>("Alice", 30);

        // Act
        auto age = user->getAge();

        // Assert
        REQUIRE(age == 30);
        REQUIRE(user.get() != nullptr);

        // user automatically deleted when scope ends
    }

    SECTION("Move semantics") {
        // Arrange
        auto user1 = std::make_unique<User>("Alice", 30);

        // Act - transfer ownership
        auto user2 = std::move(user1);

        // Assert
        REQUIRE(user1.get() == nullptr);  // user1 no longer owns the object
        REQUIRE(user2.get() != nullptr);
        REQUIRE(user2->getName() == "Alice");
    }

    SECTION("Factory pattern") {
        // Arrange & Act
        auto createUser = []() -> std::unique_ptr<User> {
            return std::make_unique<User>("Bob", 25);
        };

        auto user = createUser();

        // Assert
        REQUIRE(user->getName() == "Bob");
    }
}
```

### shared_ptr for Shared Ownership

```cpp
TEST_CASE("Smart pointers - shared_ptr", "[smart-pointers]") {
    SECTION("Multiple owners") {
        // Arrange - shared_ptr allows multiple owners
        auto user1 = std::make_shared<User>("Alice", 30);
        auto user2 = user1;  // Both share ownership

        // Act
        auto count = user1.use_count();

        // Assert
        REQUIRE(count == 2);
        REQUIRE(user1->getName() == "Alice");
        REQUIRE(user2->getName() == "Alice");
        REQUIRE(user1.get() == user2.get());  // Point to same object
    }

    SECTION("In container") {
        // Arrange
        std::vector<std::shared_ptr<User>> users;

        // Act
        users.push_back(std::make_shared<User>("Alice", 30));
        users.push_back(std::make_shared<User>("Bob", 25));
        auto first_user = users[0];  // Shared ownership

        // Assert
        REQUIRE(users.size() == 2);
        REQUIRE(first_user.use_count() == 2);  // One in vector, one in first_user
        REQUIRE(first_user->getName() == "Alice");
    }
}
```

### weak_ptr for Non-Owning References

```cpp
class Node {
public:
    std::weak_ptr<Node> parent;  // Non-owning reference
    std::vector<std::shared_ptr<Node>> children;
};

TEST_CASE("Smart pointers - weak_ptr avoids cycles", "[smart-pointers]") {
    // Arrange
    auto root = std::make_shared<Node>();
    auto child = std::make_shared<Node>();

    // Act - Set up parent-child relationship
    root->children.push_back(child);
    child->parent = root;  // weak_ptr doesn't increase ref count

    // Assert
    REQUIRE(root.use_count() == 1);  // Only root owns itself
    REQUIRE(child.use_count() == 2); // root->children and child both own

    // Verify parent is accessible
    auto parent = child->parent.lock();
    REQUIRE(parent != nullptr);
    REQUIRE(parent == root);
}
```

## Parameterized Tests with Generators

### Using GENERATE for Parameterization

```cpp
TEST_CASE("{{TEST_DESCRIPTION}} - parameterized", "{{TEST_TAG}}") {
    // Arrange
    auto [{{PARAM_NAME_1}}, {{PARAM_NAME_2}}, {{EXPECTED_NAME}}] = GENERATE(table<{{TYPE_1}}, {{TYPE_2}}, {{TYPE_3}}>({
        {{{VALUE_SET_1}}},
        {{{VALUE_SET_2}}},
        {{{VALUE_SET_3}}}
    }));

    {{ADDITIONAL_SETUP}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include "calculator.h"

TEST_CASE("Calculator addition - parameterized", "[calculator][parameterized]") {
    // Arrange
    Calculator calc;
    auto [a, b, expected] = GENERATE(table<int, int, int>({
        {2, 3, 5},
        {0, 0, 0},
        {-1, 1, 0},
        {-5, -3, -8},
        {100, 200, 300}
    }));

    // Act
    int result = calc.add(a, b);

    // Assert
    REQUIRE(result == expected);
}

TEST_CASE("String operations - parameterized", "[strings][parameterized]") {
    // Arrange
    auto [input, expected] = GENERATE(table<std::string, std::string>({
        {"hello", "HELLO"},
        {"world", "WORLD"},
        {"TeSt", "TEST"},
        {"", ""}
    }));

    // Act
    std::string result = toUpperCase(input);

    // Assert
    REQUIRE(result == expected);
}
```

### Single Value Generator

```cpp
TEST_CASE("{{TEST_DESCRIPTION}} - single param", "{{TEST_TAG}}") {
    // Arrange
    auto {{PARAM_NAME}} = GENERATE({{VALUE_1}}, {{VALUE_2}}, {{VALUE_3}});

    {{SETUP_CODE}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

```cpp
TEST_CASE("Calculator handles various inputs", "[calculator][generator]") {
    // Arrange
    Calculator calc;
    auto value = GENERATE(0, 1, -1, 100, -100);

    // Act
    int result = calc.add(value, value);

    // Assert
    REQUIRE(result == value * 2);
}

TEST_CASE("String processing handles different lengths", "[strings][generator]") {
    // Arrange
    auto str = GENERATE(
        as<std::string>{},
        "",
        "a",
        "hello",
        "this is a longer string"
    );

    // Act
    size_t length = str.length();

    // Assert
    REQUIRE(length >= 0);
    REQUIRE(countCharacters(str) == length);
}
```

## Exception Handling

### Testing Exceptions

```cpp
TEST_CASE("{{TEST_DESCRIPTION}} - exception handling", "{{TEST_TAG}}") {
    SECTION("Throws specific exception") {
        // Act & Assert
        REQUIRE_THROWS_AS({{THROWING_CODE}}, {{EXCEPTION_TYPE}});
    }

    SECTION("Throws any exception") {
        // Act & Assert
        REQUIRE_THROWS({{THROWING_CODE}});
    }

    SECTION("Does not throw") {
        // Act & Assert
        REQUIRE_NOTHROW({{SAFE_CODE}});
    }

    SECTION("Exception message check") {
        // Act & Assert
        REQUIRE_THROWS_WITH({{THROWING_CODE}}, "{{EXPECTED_MESSAGE}}");
    }
}
```

**Example:**

```cpp
TEST_CASE("Calculator exception handling", "[calculator][exceptions]") {
    Calculator calc;

    SECTION("Throws on division by zero") {
        // Act & Assert
        REQUIRE_THROWS_AS(calc.divide(10, 0), std::invalid_argument);
    }

    SECTION("Throws any exception for invalid operation") {
        // Act & Assert
        REQUIRE_THROWS(calc.performInvalidOperation());
    }

    SECTION("Does not throw for valid input") {
        // Act & Assert
        REQUIRE_NOTHROW(calc.divide(10, 2));
    }

    SECTION("Exception has correct message") {
        // Act & Assert
        REQUIRE_THROWS_WITH(
            calc.divide(10, 0),
            "Cannot divide by zero"
        );
    }
}
```

## Common Catch2 Assertions

### REQUIRE vs CHECK

```cpp
// REQUIRE - Fatal assertion (stops test on failure)
REQUIRE(condition);
REQUIRE(actual == expected);

// CHECK - Non-fatal assertion (continues on failure)
CHECK(condition);
CHECK(actual == expected);

// REQUIRE_FALSE / CHECK_FALSE
REQUIRE_FALSE(condition);
CHECK_FALSE(condition);
```

### Comparison Assertions

```cpp
// ============================================================================
// Equality and Comparison
// ============================================================================

REQUIRE(actual == expected);
REQUIRE(actual != unexpected);
REQUIRE(actual < upper_bound);
REQUIRE(actual <= upper_bound);
REQUIRE(actual > lower_bound);
REQUIRE(actual >= lower_bound);

// ============================================================================
// Floating-Point Comparison
// ============================================================================

REQUIRE(actual == Approx(expected));  // Approximate equality
REQUIRE(actual == Approx(expected).epsilon(0.01));  // Custom tolerance

// ============================================================================
// String Assertions
// ============================================================================

using Catch::Matchers::StartsWith;
using Catch::Matchers::EndsWith;
using Catch::Matchers::ContainsSubstring;

REQUIRE_THAT(str, StartsWith("prefix"));
REQUIRE_THAT(str, EndsWith("suffix"));
REQUIRE_THAT(str, ContainsSubstring("middle"));

// ============================================================================
// Container Assertions
// ============================================================================

using Catch::Matchers::Contains;
using Catch::Matchers::IsEmpty;
using Catch::Matchers::SizeIs;

REQUIRE_THAT(vec, Contains(item));
REQUIRE_THAT(vec, IsEmpty());
REQUIRE_THAT(vec, SizeIs(5));

// ============================================================================
// Exception Assertions
// ============================================================================

REQUIRE_THROWS_AS(code, std::exception);
REQUIRE_THROWS(code);
REQUIRE_NOTHROW(code);
REQUIRE_THROWS_WITH(code, "error message");
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
 * - Parameterized tests
 */

#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <memory>
#include "calculator.h"

// ============================================================================
// Basic Arithmetic Tests
// ============================================================================

TEST_CASE("Calculator basic operations", "[calculator][unit]") {
    Calculator calc;

    SECTION("Addition") {
        // Arrange
        int a = 5;
        int b = 3;
        int expected = 8;

        // Act
        int result = calc.add(a, b);

        // Assert
        REQUIRE(result == expected);
        REQUIRE(result > 0);
    }

    SECTION("Subtraction") {
        // Arrange
        int a = 10;
        int b = 3;
        int expected = 7;

        // Act
        int result = calc.subtract(a, b);

        // Assert
        REQUIRE(result == expected);
    }

    SECTION("Multiplication") {
        // Arrange
        int a = 4;
        int b = 5;
        int expected = 20;

        // Act
        int result = calc.multiply(a, b);

        // Assert
        REQUIRE(result == expected);
    }
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("Calculator edge cases", "[calculator][edge-case]") {
    Calculator calc;

    SECTION("Adding with zero") {
        int result = calc.add(5, 0);
        REQUIRE(result == 5);
    }

    SECTION("Adding negative numbers") {
        int result = calc.add(-5, -3);
        REQUIRE(result == -8);
    }

    SECTION("Multiplying by zero") {
        int result = calc.multiply(5, 0);
        REQUIRE(result == 0);
    }
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("Calculator error handling", "[calculator][error]") {
    Calculator calc;

    SECTION("Division by zero throws exception") {
        REQUIRE_THROWS_AS(calc.divide(10, 0), std::invalid_argument);
    }

    SECTION("Exception has correct message") {
        REQUIRE_THROWS_WITH(
            calc.divide(10, 0),
            "Cannot divide by zero"
        );
    }

    SECTION("Valid division does not throw") {
        REQUIRE_NOTHROW(calc.divide(10, 2));
    }
}

// ============================================================================
// Parameterized Tests
// ============================================================================

TEST_CASE("Calculator addition - parameterized", "[calculator][parameterized]") {
    Calculator calc;
    auto [a, b, expected] = GENERATE(table<int, int, int>({
        {2, 3, 5},
        {0, 0, 0},
        {-1, 1, 0},
        {-5, -3, -8},
        {100, 200, 300}
    }));

    int result = calc.add(a, b);
    REQUIRE(result == expected);
}

// ============================================================================
// RAII and Smart Pointer Tests
// ============================================================================

TEST_CASE("Calculator with smart pointers", "[calculator][raii]") {
    SECTION("Using unique_ptr") {
        // Arrange - automatic cleanup
        auto calc = std::make_unique<Calculator>();

        // Act
        int result = calc->add(5, 3);

        // Assert
        REQUIRE(result == 8);

        // calc automatically deleted
    }

    SECTION("Using shared_ptr") {
        // Arrange
        auto calc1 = std::make_shared<Calculator>();
        auto calc2 = calc1;  // Shared ownership

        // Act
        int result1 = calc1->add(2, 3);
        int result2 = calc2->add(2, 3);

        // Assert
        REQUIRE(result1 == result2);
        REQUIRE(calc1.use_count() == 2);
    }
}

// ============================================================================
// BDD-Style Scenario Tests
// ============================================================================

TEST_CASE("Calculator supports chained operations", "[calculator][bdd]") {
    // Given - A calculator instance
    Calculator calc;

    SECTION("When performing multiple additions") {
        // When
        int result = calc.add(5, 3);
        result = calc.add(result, 2);

        SECTION("Then the final result is correct") {
            // Then
            REQUIRE(result == 10);
        }
    }

    SECTION("When mixing operations") {
        // When
        int result = calc.add(10, 5);
        result = calc.subtract(result, 3);

        SECTION("Then operations are applied in order") {
            // Then
            REQUIRE(result == 12);
        }
    }
}
```

## Test Main Template

```cpp
// test_main.cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch_session.hpp>

// Alternatively, for custom main:
// int main(int argc, char* argv[]) {
//     Catch::Session session;
//
//     // Configure session if needed
//     // session.configData().showSuccessfulTests = true;
//
//     int returnCode = session.applyCommandLine(argc, argv);
//     if (returnCode != 0) return returnCode;
//
//     return session.run();
// }
```

## CMake Integration

```cmake
# CMakeLists.txt for tests
cmake_minimum_required(VERSION 3.15)
project({{PROJECT_NAME}}Tests CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Catch2
find_package(Catch2 3 REQUIRED)
include(CTest)
include(Catch)

# Add test executable
add_executable({{TEST_EXECUTABLE}}
    test_{{MODULE}}.cpp
)

# Link against Catch2 and project library
target_link_libraries({{TEST_EXECUTABLE}}
    PRIVATE
    Catch2::Catch2WithMain
    {{PROJECT_LIBRARY}}
)

# Discover tests
catch_discover_tests({{TEST_EXECUTABLE}})

# Optionally enable code coverage
if(ENABLE_COVERAGE)
    target_compile_options({{TEST_EXECUTABLE}} PRIVATE --coverage)
    target_link_options({{TEST_EXECUTABLE}} PRIVATE --coverage)
endif()
```

## Usage Guide

### Step 1: Choose the Right Pattern

- **TEST_CASE**: Basic test scenarios
- **SECTION**: Group related scenarios within a test case
- **Nested SECTION**: BDD-style Given/When/Then scenarios
- **GENERATE**: Parameterized tests with multiple inputs
- **REQUIRE vs CHECK**: Fatal vs non-fatal assertions

### Step 2: Customize Placeholders

Replace all `{{PLACEHOLDER}}` values:

1. Test case descriptions and tags
2. Section names
3. Setup/Act/Assert code blocks
4. Assertion expectations
5. Smart pointer types and names

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

# With Catch2 filters (by tag)
./test_calculator "[calculator]"

# With Catch2 filters (by name)
./test_calculator "Calculator basic operations"

# List all tests
./test_calculator --list-tests

# With XML output
./test_calculator -r xml -o test_results.xml

# Show successful tests
./test_calculator -s
```

## Best Practices

1. **Descriptive Names**: Use natural language for test case names
2. **Use Sections**: Group related scenarios within test cases
3. **BDD Style**: Use nested sections for Given/When/Then structure
4. **Smart Pointers**: Prefer `unique_ptr` and `shared_ptr` over raw pointers
5. **RAII**: Use constructors/destructors for resource management
6. **REQUIRE for Critical**: Use REQUIRE for assumptions needed to continue
7. **CHECK for Multiple**: Use CHECK to see all failures in one run
8. **Tags**: Use tags to categorize and filter tests
9. **Generators**: Use GENERATE for parameterized tests
10. **Natural Assertions**: Catch2's assertion syntax is very readable

## Comparison with Google Test

### Key Differences

| Feature | Catch2 | Google Test |
|---------|--------|-------------|
| Style | BDD-style, natural language | xUnit-style, structured |
| Sections | Built-in SECTION support | Requires fixtures or subtests |
| Assertions | Natural: `REQUIRE(x == 5)` | Macro-based: `EXPECT_EQ(x, 5)` |
| Setup | Automatic via SECTION | Explicit SetUp()/TearDown() |
| Parameterization | GENERATE (inline) | TEST_P (separate setup) |
| Integration | Header-only option | Library-based |
| Matchers | Built-in string/container | Requires additional includes |

### When to Use Catch2

- Prefer natural, readable test descriptions
- Want BDD-style Given/When/Then structure
- Need header-only solution
- Like inline parameterization with GENERATE
- Prefer minimal setup code

### When to Use Google Test

- Need Google Mock integration (gmock)
- Prefer structured xUnit-style tests
- Want parameterized tests with custom names
- Need death tests with detailed control
- Project already uses Google Test

## Related Skills

- **Framework Detection**: `skills/framework-detection/cpp-frameworks.md`
- **Test Generation**: `skills/test-generation/cpp-patterns.md`
- **Result Parsing**: `skills/result-parsing/parsers/catch2-parser.md`
- **Build Integration**: `skills/build-integration/cmake-build-system.md`
- **Google Test Template**: `skills/templates/cpp-gtest-template.md`

---

**Template Version**: 1.0.0
**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
