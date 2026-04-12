# Java JUnit 4 Test Template

**Purpose**: Template for generating JUnit 4 test files (legacy support)
**Target Language**: Java
**Test Framework**: JUnit 4
**Version Support**: JUnit 4.12+
**Build Systems**: Maven, Gradle

## Template Structure

```java
package {PACKAGE_NAME};

import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

/**
 * Test class for {CLASS_NAME}.
 */
public class {TEST_CLASS_NAME} {

    {SETUP_FIELDS}

    @Before
    public void setUp() {
        {SETUP_CODE}
    }

    @After
    public void tearDown() {
        {TEARDOWN_CODE}
    }

    {TEST_METHODS}
}
```

## Key Differences from JUnit 5

- Classes and methods must be `public`
- Use `@Before` instead of `@BeforeEach`
- Use `@After` instead of `@AfterEach`
- Import from `org.junit.*` not `org.junit.jupiter.api.*`
- No `@DisplayName` annotation
- Exception testing: `@Test(expected = Exception.class)`

## Example

```java
package com.example;

import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

/**
 * Test class for Calculator.
 */
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

    @Test
    public void testSubtractNumbers() {
        // Arrange
        int a = 10;
        int b = 3;

        // Act
        int result = calculator.subtract(a, b);

        // Assert
        assertEquals(7, result);
    }

    @Test(expected = ArithmeticException.class)
    public void testDivideByZeroThrowsException() {
        calculator.divide(10, 0);
    }

    @Test
    public void testMultiplyNumbers() {
        assertEquals(20, calculator.multiply(4, 5));
    }
}
```

## JUnit 4 Assertions

```java
assertEquals(expected, actual);
assertEquals("Message", expected, actual);
assertNotEquals(unexpected, actual);
assertTrue(condition);
assertFalse(condition);
assertNull(object);
assertNotNull(object);
assertSame(expected, actual);
assertNotSame(object1, object2);
assertArrayEquals(expectedArray, actualArray);
fail("Failure message");
```

## JUnit 4 Annotations

```java
@BeforeClass    // Runs once before all tests (static)
@Before         // Runs before each test
@Test           // Test method
@After          // Runs after each test
@AfterClass     // Runs once after all tests (static)
@Ignore("Reason")  // Skip test
@Test(timeout = 1000)  // Test must complete within 1 second
@Test(expected = Exception.class)  // Test expects exception
```

## With Mockito

```java
import org.junit.Test;
import org.junit.Before;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.junit.MockitoJUnitRunner;
import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

@RunWith(MockitoJUnitRunner.class)
public class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    public void testFindUserById() {
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

## Maven Configuration

```xml
<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>4.13.2</version>
    <scope>test</scope>
</dependency>
```

## Gradle Configuration

```groovy
dependencies {
    testImplementation 'junit:junit:4.13.2'
}
```

## Migration Note

**Consider upgrading to JUnit 5** for new projects. JUnit 4 is in maintenance mode. See `java-junit5-template.md` for modern testing features.

## References

- JUnit 4 Documentation: https://junit.org/junit4/
- Java Patterns: `skills/test-generation/java-patterns.md`
- JUnit 5 Template: `skills/templates/java-junit5-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
