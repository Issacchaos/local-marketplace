# Java Test Generation Patterns

**Version**: 1.0.0
**Language**: Java
**Frameworks**: JUnit 4, JUnit 5 (Jupiter), TestNG
**Purpose**: Testing patterns and best practices for Java test generation

## Overview

Java test generation patterns for creating comprehensive, maintainable test suites. This skill covers JUnit 4, JUnit 5 (Jupiter), and TestNG frameworks with focus on assertions, mocking with Mockito, and Java-specific testing patterns.

## Supported Frameworks

### JUnit 5 (Jupiter) - Recommended

**Description**: Modern testing framework with improved architecture
**Package**: `org.junit.jupiter.api.*`
**Minimum Version**: 5.0.0+

**Key Features**:
- `@Test` annotation (no public modifier needed)
- `@BeforeEach`, `@AfterEach` lifecycle methods
- `@DisplayName` for readable test names
- Assertions in `Assertions` class
- `assertThrows()` for exception testing

### JUnit 4 - Legacy Support

**Description**: Widely used legacy testing framework
**Package**: `org.junit.*`
**Minimum Version**: 4.12+

**Key Features**:
- `@Test` annotation (requires public methods)
- `@Before`, `@After` lifecycle methods
- Assertions in `Assert` class
- `@Test(expected=Exception.class)` for exceptions

### TestNG

**Description**: Testing framework with additional features
**Package**: `org.testng.*`
**Minimum Version**: 6.0.0+

**Key Features**:
- `@Test` annotation with configuration
- `@BeforeMethod`, `@AfterMethod` lifecycle
- Flexible test configuration via XML
- Built-in parallel execution

## Java Testing Fundamentals

### File Organization

```
project/
├── src/
│   ├── main/java/
│   │   └── com/example/
│   │       └── Calculator.java
│   └── test/java/
│       └── com/example/
│           └── CalculatorTest.java
└── pom.xml or build.gradle
```

**Naming Conventions**:
- Test classes: `*Test.java` or `Test*.java`
- Test methods: `testMethodName()` or `methodName_condition_expected()`
- Package structure: Mirror main source packages

### Test Structure: AAA Pattern

All frameworks use Arrange-Act-Assert pattern:

```java
@Test
public void shouldAddTwoNumbers() {
    // Arrange
    Calculator calculator = new Calculator();
    int a = 5;
    int b = 3;

    // Act
    int result = calculator.add(a, b);

    // Assert
    assertEquals(8, result);
}
```

## JUnit 5 Patterns

### Basic Test Structure

```java
package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Calculator Tests")
class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @AfterEach
    void tearDown() {
        calculator = null;
    }

    @Test
    @DisplayName("Should add two positive numbers")
    void shouldAddTwoPositiveNumbers() {
        // Arrange
        int a = 5;
        int b = 3;

        // Act
        int result = calculator.add(a, b);

        // Assert
        assertEquals(8, result);
    }

    @Test
    void shouldThrowExceptionWhenDividingByZero() {
        assertThrows(ArithmeticException.class, () -> {
            calculator.divide(10, 0);
        });
    }
}
```

### JUnit 5 Assertions

```java
// Equality
assertEquals(expected, actual);
assertEquals(expected, actual, "Custom failure message");
assertNotEquals(unexpected, actual);

// Truthiness
assertTrue(condition);
assertFalse(condition);
assertNull(object);
assertNotNull(object);

// Object comparison
assertSame(expected, actual);  // Same reference
assertNotSame(object1, object2);

// Arrays
assertArrayEquals(expectedArray, actualArray);

// Exceptions
assertThrows(IllegalArgumentException.class, () -> {
    someMethod();
});

Exception exception = assertThrows(RuntimeException.class, () -> {
    someMethod();
});
assertEquals("Expected message", exception.getMessage());

// Timeouts
assertTimeout(Duration.ofSeconds(1), () -> {
    // Code that should complete within 1 second
});

// Multiple assertions
assertAll("Person validation",
    () -> assertEquals("John", person.getFirstName()),
    () -> assertEquals("Doe", person.getLastName()),
    () -> assertEquals(30, person.getAge())
);
```

### Parameterized Tests

```java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;
import java.util.stream.Stream;

class CalculatorTest {

    @ParameterizedTest
    @ValueSource(ints = {1, 2, 3, 4, 5})
    void shouldReturnTrueForPositiveNumbers(int number) {
        assertTrue(calculator.isPositive(number));
    }

    @ParameterizedTest
    @CsvSource({
        "5, 3, 8",
        "10, 20, 30",
        "-5, 5, 0"
    })
    void shouldAddNumbers(int a, int b, int expected) {
        assertEquals(expected, calculator.add(a, b));
    }

    @ParameterizedTest
    @MethodSource("provideTestData")
    void shouldHandleComplexScenarios(String input, int expected) {
        int result = calculator.parse(input);
        assertEquals(expected, result);
    }

    static Stream<Arguments> provideTestData() {
        return Stream.of(
            Arguments.of("10", 10),
            Arguments.of("20", 20),
            Arguments.of("30", 30)
        );
    }
}
```

## JUnit 4 Patterns

### Basic Test Structure

```java
package com.example;

import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

public class CalculatorTest {

    private Calculator calculator;

    @Before
    public void setUp() {
        calculator = new Calculator();
    }

    @After
    public void tearDown() {
        calculator = null;
    }

    @Test
    public void testAddTwoNumbers() {
        // Arrange
        int a = 5;
        int b = 3;

        // Act
        int result = calculator.add(a, b);

        // Assert
        assertEquals(8, result);
    }

    @Test(expected = ArithmeticException.class)
    public void testDivideByZeroThrowsException() {
        calculator.divide(10, 0);
    }
}
```

### JUnit 4 Assertions

```java
// Equality
assertEquals(expected, actual);
assertEquals("Failure message", expected, actual);
assertNotEquals(unexpected, actual);

// Truthiness
assertTrue(condition);
assertTrue("Failure message", condition);
assertFalse(condition);
assertNull(object);
assertNotNull(object);

// Arrays
assertArrayEquals(expectedArray, actualArray);

// Exceptions
@Test(expected = IllegalArgumentException.class)
public void shouldThrowException() {
    someMethod();
}

// Fail explicitly
fail("Should have thrown exception");
```

## TestNG Patterns

### Basic Test Structure

```java
package com.example;

import org.testng.annotations.Test;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.AfterMethod;
import static org.testng.Assert.*;

public class CalculatorTest {

    private Calculator calculator;

    @BeforeMethod
    public void setUp() {
        calculator = new Calculator();
    }

    @AfterMethod
    public void tearDown() {
        calculator = null;
    }

    @Test
    public void shouldAddTwoNumbers() {
        // Arrange
        int a = 5;
        int b = 3;

        // Act
        int result = calculator.add(a, b);

        // Assert
        assertEquals(result, 8);  // Note: TestNG order is (actual, expected)
    }

    @Test(expectedExceptions = ArithmeticException.class)
    public void shouldThrowExceptionWhenDividingByZero() {
        calculator.divide(10, 0);
    }
}
```

### TestNG Data Providers

```java
import org.testng.annotations.DataProvider;

public class CalculatorTest {

    @DataProvider(name = "additionData")
    public Object[][] provideAdditionData() {
        return new Object[][] {
            {5, 3, 8},
            {10, 20, 30},
            {-5, 5, 0}
        };
    }

    @Test(dataProvider = "additionData")
    public void shouldAddNumbers(int a, int b, int expected) {
        int result = calculator.add(a, b);
        assertEquals(result, expected);
    }
}
```

## Mocking with Mockito

### Basic Mockito Setup

```java
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

// JUnit 5
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldFindUserById() {
        // Arrange
        User mockUser = new User(1, "Alice");
        when(userRepository.findById(1)).thenReturn(mockUser);

        // Act
        User result = userService.getUser(1);

        // Assert
        assertEquals("Alice", result.getName());
        verify(userRepository).findById(1);
    }
}
```

### Mock Behaviors

```java
// Return value
when(mockRepository.findById(1)).thenReturn(user);

// Return multiple values
when(mockRepository.findAll())
    .thenReturn(list1)
    .thenReturn(list2);

// Throw exception
when(mockRepository.findById(999))
    .thenThrow(new NotFoundException());

// Void methods
doNothing().when(mockRepository).delete(any());
doThrow(new RuntimeException()).when(mockRepository).delete(any());

// Argument matchers
when(mockRepository.findById(anyInt())).thenReturn(user);
when(mockRepository.save(any(User.class))).thenReturn(user);

// Verify interactions
verify(mockRepository).findById(1);
verify(mockRepository, times(2)).findAll();
verify(mockRepository, never()).delete(any());
```

## Test Naming Conventions

### Method Naming Patterns

```java
// Pattern 1: should_expectedBehavior_when_condition
@Test
void should_returnUser_when_userExists() { }

// Pattern 2: methodName_condition_expectedResult
@Test
void findUser_userExists_returnsUser() { }

// Pattern 3: given_when_then
@Test
void given_validUserId_when_findUser_then_returnsUser() { }

// Pattern 4: Simple descriptive (with @DisplayName)
@Test
@DisplayName("Returns user when user exists")
void testFindUser() { }
```

## Setup and Teardown

### JUnit 5 Lifecycle

```java
@BeforeAll
static void initAll() {
    // Runs once before all tests
}

@BeforeEach
void init() {
    // Runs before each test
}

@AfterEach
void tearDown() {
    // Runs after each test
}

@AfterAll
static void tearDownAll() {
    // Runs once after all tests
}
```

### JUnit 4 Lifecycle

```java
@BeforeClass
public static void setUpClass() {
    // Runs once before all tests
}

@Before
public void setUp() {
    // Runs before each test
}

@After
public void tearDown() {
    // Runs after each test
}

@AfterClass
public static void tearDownClass() {
    // Runs once after all tests
}
```

## Best Practices

1. **Test one thing per test**: Focus on single behavior
2. **Use descriptive names**: Test name explains what's being tested
3. **AAA pattern**: Always use Arrange-Act-Assert
4. **Independent tests**: No shared state between tests
5. **Mock external dependencies**: Database, APIs, file system
6. **Use constants**: Avoid magic numbers/strings
7. **Clean up resources**: Use @After/@AfterEach
8. **Test edge cases**: Null, empty, boundary values
9. **Prefer JUnit 5**: Modern features, better assertions
10. **Use Mockito**: Industry standard for mocking

## Common Test Scenarios

### Testing Collections

```java
@Test
void shouldReturnAllUsers() {
    List<User> users = userService.findAll();

    assertNotNull(users);
    assertEquals(3, users.size());
    assertTrue(users.contains(expectedUser));
}
```

### Testing Exceptions

```java
// JUnit 5
@Test
void shouldThrowException() {
    Exception exception = assertThrows(
        IllegalArgumentException.class,
        () -> userService.createUser(null)
    );
    assertEquals("User cannot be null", exception.getMessage());
}

// JUnit 4
@Test(expected = IllegalArgumentException.class)
public void shouldThrowException() {
    userService.createUser(null);
}
```

### Testing Void Methods

```java
@Test
void shouldDeleteUser() {
    // Arrange
    doNothing().when(userRepository).delete(1);

    // Act
    userService.deleteUser(1);

    // Assert
    verify(userRepository).delete(1);
}
```

## Anti-Patterns to Avoid

❌ **Testing multiple things**: Keep tests focused
❌ **Hardcoding values**: Use variables and constants
❌ **Ignoring cleanup**: Always clean up resources
❌ **Testing implementation**: Test behavior, not internals
❌ **Coupling tests**: Tests should run independently

## Quick Reference

| Framework | Test Annotation | Setup | Teardown | Assert Package |
|-----------|----------------|-------|----------|----------------|
| JUnit 5 | `@Test` | `@BeforeEach` | `@AfterEach` | `org.junit.jupiter.api.Assertions` |
| JUnit 4 | `@Test` | `@Before` | `@After` | `org.junit.Assert` |
| TestNG | `@Test` | `@BeforeMethod` | `@AfterMethod` | `org.testng.Assert` |

## References

- JUnit 5: https://junit.org/junit5/docs/current/user-guide/
- JUnit 4: https://junit.org/junit4/
- TestNG: https://testng.org/doc/documentation-main.html
- Mockito: https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html
- AssertJ (fluent assertions): https://assertj.github.io/doc/

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
