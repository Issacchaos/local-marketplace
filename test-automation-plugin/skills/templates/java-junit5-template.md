# Java JUnit 5 Test Template

**Purpose**: Template for generating JUnit 5 test files with proper structure
**Target Language**: Java
**Test Framework**: JUnit 5 (Jupiter)
**Version Support**: JUnit 5.0.0+
**Build Systems**: Maven, Gradle

## Template Structure

### Basic Test File Template

```java
package {PACKAGE_NAME};

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Test class for {CLASS_NAME}.
 *
 * This test class covers:
 * - {TEST_COVERAGE_AREA_1}
 * - {TEST_COVERAGE_AREA_2}
 * - {TEST_COVERAGE_AREA_3}
 */
@DisplayName("{DISPLAY_NAME}")
class {TEST_CLASS_NAME} {

    {SETUP_FIELDS}

    @BeforeEach
    void setUp() {
        {SETUP_CODE}
    }

    @AfterEach
    void tearDown() {
        {TEARDOWN_CODE}
    }

    {TEST_METHODS}
}
```

## Template Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{PACKAGE_NAME}` | Java package declaration | `com.example.calculator` |
| `{CLASS_NAME}` | Class being tested | `Calculator`, `UserService` |
| `{TEST_CLASS_NAME}` | Test class name | `CalculatorTest`, `UserServiceTest` |
| `{DISPLAY_NAME}` | Readable test suite name | `Calculator Tests`, `User Service Tests` |
| `{TEST_COVERAGE_AREA_N}` | Coverage areas | `Addition operations`, `Error handling` |
| `{SETUP_FIELDS}` | Instance variables | `private Calculator calculator;` |
| `{SETUP_CODE}` | Setup initialization | `calculator = new Calculator();` |
| `{TEARDOWN_CODE}` | Cleanup code | `calculator = null;` |
| `{TEST_METHODS}` | Generated test methods | Individual @Test methods |

## JUnit 5 Conventions

### File Naming
- **Pattern**: `*Test.java` or `Test*.java`
- **Location**: `src/test/java/{package}/`
- **Example**: `src/test/java/com/example/CalculatorTest.java`

### Class Naming
- Match source class with `Test` suffix: `Calculator` → `CalculatorTest`
- Use package-private visibility (no `public` modifier needed)

### Method Naming
- Start with lowercase: `shouldAddTwoNumbers()`
- Use descriptive names with "should" prefix
- No `public` modifier needed
- Use `@DisplayName` for complex scenarios

## Test Method Template (AAA Pattern)

```java
@Test
@DisplayName("{READABLE_TEST_NAME}")
void {TEST_METHOD_NAME}() {
    // Arrange
    {ARRANGE_CODE}

    // Act
    {ACT_CODE}

    // Assert
    {ASSERT_CODE}
}
```

## Complete Examples

### Example 1: Simple Calculator Tests

```java
package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Test class for Calculator.
 *
 * This test class covers:
 * - Basic arithmetic operations
 * - Error handling for invalid inputs
 * - Edge cases for boundary values
 */
@DisplayName("Calculator Tests")
class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    @DisplayName("Should add two positive numbers correctly")
    void shouldAddTwoPositiveNumbers() {
        // Arrange
        int a = 5;
        int b = 3;

        // Act
        int result = calculator.add(a, b);

        // Assert
        assertEquals(8, result, "5 + 3 should equal 8");
    }

    @Test
    @DisplayName("Should handle negative numbers in addition")
    void shouldHandleNegativeNumbers() {
        // Arrange
        int a = -5;
        int b = -3;

        // Act
        int result = calculator.add(a, b);

        // Assert
        assertEquals(-8, result);
    }

    @Test
    @DisplayName("Should throw ArithmeticException when dividing by zero")
    void shouldThrowExceptionWhenDividingByZero() {
        // Act & Assert
        ArithmeticException exception = assertThrows(
            ArithmeticException.class,
            () -> calculator.divide(10, 0),
            "Expected divide() to throw ArithmeticException"
        );

        assertEquals("Division by zero", exception.getMessage());
    }

    @Test
    void shouldMultiplyNumbers() {
        // Arrange
        int a = 4;
        int b = 5;

        // Act
        int result = calculator.multiply(a, b);

        // Assert
        assertEquals(20, result);
    }

    @Test
    void shouldSubtractNumbers() {
        // Arrange
        int a = 10;
        int b = 3;

        // Act
        int result = calculator.subtract(a, b);

        // Assert
        assertEquals(7, result);
    }
}
```

### Example 2: Tests with Setup and Teardown

```java
package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Test class for UserService.
 */
@DisplayName("User Service Tests")
class UserServiceTest {

    private UserService userService;
    private User testUser;

    @BeforeEach
    void setUp() {
        // Arrange - Create fresh instances for each test
        userService = new UserService();
        testUser = new User(1, "Alice", "alice@example.com");
    }

    @AfterEach
    void tearDown() {
        // Cleanup
        userService.clearCache();
        userService = null;
        testUser = null;
    }

    @Test
    @DisplayName("Should create a new user successfully")
    void shouldCreateUser() {
        // Act
        User created = userService.createUser("Bob", "bob@example.com");

        // Assert
        assertNotNull(created);
        assertEquals("Bob", created.getName());
        assertEquals("bob@example.com", created.getEmail());
        assertTrue(created.getId() > 0);
    }

    @Test
    @DisplayName("Should find user by ID")
    void shouldFindUserById() {
        // Arrange
        userService.saveUser(testUser);

        // Act
        User found = userService.findById(1);

        // Assert
        assertNotNull(found);
        assertEquals(testUser.getId(), found.getId());
        assertEquals(testUser.getName(), found.getName());
    }

    @Test
    @DisplayName("Should return null when user not found")
    void shouldReturnNullWhenUserNotFound() {
        // Act
        User found = userService.findById(999);

        // Assert
        assertNull(found);
    }

    @Test
    @DisplayName("Should delete user by ID")
    void shouldDeleteUser() {
        // Arrange
        userService.saveUser(testUser);

        // Act
        boolean deleted = userService.deleteUser(1);

        // Assert
        assertTrue(deleted);
        assertNull(userService.findById(1));
    }
}
```

### Example 3: Parameterized Tests

```java
package com.example;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.Arguments;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Parameterized tests for Calculator.
 */
@DisplayName("Calculator Parameterized Tests")
class CalculatorParameterizedTest {

    private final Calculator calculator = new Calculator();

    @ParameterizedTest
    @DisplayName("Should identify positive numbers")
    @ValueSource(ints = {1, 2, 3, 4, 5, 100, 1000})
    void shouldIdentifyPositiveNumbers(int number) {
        assertTrue(calculator.isPositive(number));
    }

    @ParameterizedTest
    @DisplayName("Should add numbers correctly")
    @CsvSource({
        "5, 3, 8",
        "10, 20, 30",
        "-5, 5, 0",
        "0, 0, 0",
        "-10, -20, -30"
    })
    void shouldAddNumbers(int a, int b, int expected) {
        int result = calculator.add(a, b);
        assertEquals(expected, result);
    }

    @ParameterizedTest
    @DisplayName("Should multiply numbers correctly")
    @MethodSource("provideMultiplicationTestData")
    void shouldMultiplyNumbers(int a, int b, int expected) {
        int result = calculator.multiply(a, b);
        assertEquals(expected, result);
    }

    static Stream<Arguments> provideMultiplicationTestData() {
        return Stream.of(
            Arguments.of(2, 3, 6),
            Arguments.of(5, 5, 25),
            Arguments.of(0, 10, 0),
            Arguments.of(-2, 3, -6)
        );
    }
}
```

### Example 4: Tests with Mockito

```java
package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Test class for UserService with mocked dependencies.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("User Service Tests with Mocks")
class UserServiceMockTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = new User(1, "Alice", "alice@example.com");
    }

    @Test
    @DisplayName("Should find user by ID using repository")
    void shouldFindUserById() {
        // Arrange
        when(userRepository.findById(1)).thenReturn(testUser);

        // Act
        User found = userService.getUser(1);

        // Assert
        assertNotNull(found);
        assertEquals("Alice", found.getName());
        verify(userRepository).findById(1);
    }

    @Test
    @DisplayName("Should create user and send welcome email")
    void shouldCreateUserAndSendEmail() {
        // Arrange
        when(userRepository.save(any(User.class))).thenReturn(testUser);
        doNothing().when(emailService).sendWelcomeEmail(any(User.class));

        // Act
        User created = userService.createUser("Alice", "alice@example.com");

        // Assert
        assertNotNull(created);
        verify(userRepository).save(any(User.class));
        verify(emailService).sendWelcomeEmail(created);
    }

    @Test
    @DisplayName("Should throw exception when user not found")
    void shouldThrowExceptionWhenUserNotFound() {
        // Arrange
        when(userRepository.findById(999))
            .thenThrow(new UserNotFoundException("User not found"));

        // Act & Assert
        assertThrows(UserNotFoundException.class, () -> {
            userService.getUser(999);
        });

        verify(userRepository).findById(999);
    }
}
```

### Example 5: Testing Collections and Multiple Assertions

```java
package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Test class for UserService collection operations.
 */
@DisplayName("User Service Collection Tests")
class UserServiceCollectionTest {

    private UserService userService;

    @BeforeEach
    void setUp() {
        userService = new UserService();
        userService.saveUser(new User(1, "Alice", "alice@example.com"));
        userService.saveUser(new User(2, "Bob", "bob@example.com"));
        userService.saveUser(new User(3, "Charlie", "charlie@example.com"));
    }

    @Test
    @DisplayName("Should return all users")
    void shouldReturnAllUsers() {
        // Act
        List<User> users = userService.findAll();

        // Assert - Multiple assertions
        assertAll("users collection",
            () -> assertNotNull(users),
            () -> assertEquals(3, users.size()),
            () -> assertTrue(users.stream().anyMatch(u -> u.getName().equals("Alice"))),
            () -> assertTrue(users.stream().anyMatch(u -> u.getName().equals("Bob"))),
            () -> assertTrue(users.stream().anyMatch(u -> u.getName().equals("Charlie")))
        );
    }

    @Test
    @DisplayName("Should filter users by email domain")
    void shouldFilterUsersByEmailDomain() {
        // Act
        List<User> exampleUsers = userService.findByEmailDomain("example.com");

        // Assert
        assertFalse(exampleUsers.isEmpty());
        exampleUsers.forEach(user ->
            assertTrue(user.getEmail().endsWith("@example.com"))
        );
    }

    @Test
    @DisplayName("Should return empty list when no users match filter")
    void shouldReturnEmptyListWhenNoMatch() {
        // Act
        List<User> noMatch = userService.findByEmailDomain("nonexistent.com");

        // Assert
        assertNotNull(noMatch);
        assertTrue(noMatch.isEmpty());
    }
}
```

## JUnit 5 Annotations Reference

### Test Lifecycle
```java
@BeforeAll      // Runs once before all tests (static method)
@BeforeEach     // Runs before each test
@Test           // Test method
@AfterEach      // Runs after each test
@AfterAll       // Runs once after all tests (static method)
```

### Test Configuration
```java
@DisplayName("Readable test name")
@Disabled("Reason for disabling")
@Timeout(value = 5, unit = TimeUnit.SECONDS)
```

### Parameterized Tests
```java
@ParameterizedTest
@ValueSource(ints = {1, 2, 3})
@CsvSource({"1,2,3", "4,5,9"})
@MethodSource("provideData")
```

## Assertions Reference

```java
// Equality
assertEquals(expected, actual);
assertEquals(expected, actual, "Custom message");
assertNotEquals(unexpected, actual);

// Truthiness
assertTrue(condition);
assertFalse(condition);
assertNull(object);
assertNotNull(object);

// Exceptions
assertThrows(ExceptionType.class, () -> { /* code */ });

// Collections
assertArrayEquals(expectedArray, actualArray);

// Multiple assertions
assertAll("description",
    () -> assertEquals(expected1, actual1),
    () -> assertEquals(expected2, actual2)
);

// Timeouts
assertTimeout(Duration.ofSeconds(1), () -> { /* code */ });
```

## Maven Configuration

```xml
<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter-api</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter-engine</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>
    <!-- Optional: Mockito -->
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-core</artifactId>
        <version>5.5.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## Gradle Configuration

```groovy
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.10.0'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.10.0'

    // Optional: Mockito
    testImplementation 'org.mockito:mockito-core:5.5.0'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'
}

test {
    useJUnitPlatform()
}
```

## Best Practices

1. **One assertion per test** (when possible): Focused tests are easier to debug
2. **Use @DisplayName**: Makes test reports more readable
3. **Follow AAA pattern**: Arrange-Act-Assert for clarity
4. **Use @BeforeEach**: Initialize fresh state for each test
5. **Clean up in @AfterEach**: Release resources, reset state
6. **Use assertAll**: Group related assertions together
7. **Descriptive failure messages**: Help debug failures faster
8. **Test edge cases**: Null, empty, boundary values
9. **Use parameterized tests**: Reduce duplication for similar tests
10. **Mock external dependencies**: Isolate unit under test

## References

- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- JUnit 5 API: https://junit.org/junit5/docs/current/api/
- Mockito: https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html
- Java Patterns: `skills/test-generation/java-patterns.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
