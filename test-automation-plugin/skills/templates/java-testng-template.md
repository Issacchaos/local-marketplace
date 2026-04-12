# Java TestNG Test Template

**Purpose**: Template for generating TestNG test files
**Target Language**: Java
**Test Framework**: TestNG
**Version Support**: TestNG 6.0.0+
**Build Systems**: Maven, Gradle

## Template Structure

```java
package {PACKAGE_NAME};

import org.testng.annotations.Test;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.AfterClass;
import org.testng.annotations.DataProvider;
import static org.testng.Assert.*;

/**
 * Test class for {CLASS_NAME}.
 */
public class {TEST_CLASS_NAME} {

    {SETUP_FIELDS}

    @BeforeClass
    public void setUpClass() {
        {CLASS_SETUP_CODE}
    }

    @BeforeMethod
    public void setUp() {
        {SETUP_CODE}
    }

    @AfterMethod
    public void tearDown() {
        {TEARDOWN_CODE}
    }

    @AfterClass
    public void tearDownClass() {
        {CLASS_TEARDOWN_CODE}
    }

    {TEST_METHODS}
}
```

## Key Differences from JUnit

- Note: TestNG assertions have **(actual, expected)** order (opposite of JUnit)
- Flexible test configuration via annotations
- Built-in parallel execution support
- XML-based test suite configuration
- `@BeforeMethod` instead of `@Before` or `@BeforeEach`
- More powerful data providers

## Basic Example

```java
package com.example;

import org.testng.annotations.Test;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.AfterMethod;
import static org.testng.Assert.*;

/**
 * Test class for Calculator.
 */
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
        assertEquals(result, 8);  // Note: actual first, expected second
    }

    @Test
    public void shouldSubtractNumbers() {
        // Arrange
        int a = 10;
        int b = 3;

        // Act
        int result = calculator.subtract(a, b);

        // Assert
        assertEquals(result, 7);
    }

    @Test(expectedExceptions = ArithmeticException.class)
    public void shouldThrowExceptionWhenDividingByZero() {
        calculator.divide(10, 0);
    }

    @Test
    public void shouldMultiplyNumbers() {
        assertEquals(calculator.multiply(4, 5), 20);
    }
}
```

## TestNG Data Providers

```java
package com.example;

import org.testng.annotations.Test;
import org.testng.annotations.DataProvider;
import static org.testng.Assert.*;

public class CalculatorDataProviderTest {

    private final Calculator calculator = new Calculator();

    @DataProvider(name = "additionData")
    public Object[][] provideAdditionData() {
        return new Object[][] {
            {5, 3, 8},
            {10, 20, 30},
            {-5, 5, 0},
            {0, 0, 0}
        };
    }

    @Test(dataProvider = "additionData")
    public void shouldAddNumbers(int a, int b, int expected) {
        int result = calculator.add(a, b);
        assertEquals(result, expected);
    }

    @DataProvider(name = "positiveNumbers")
    public Object[][] providePositiveNumbers() {
        return new Object[][] {
            {1}, {2}, {5}, {10}, {100}
        };
    }

    @Test(dataProvider = "positiveNumbers")
    public void shouldIdentifyPositiveNumbers(int number) {
        assertTrue(calculator.isPositive(number));
    }
}
```

## TestNG Annotations

### Test Configuration
```java
@Test                              // Test method
@Test(priority = 1)               // Execution order
@Test(enabled = false)            // Skip test
@Test(groups = {"smoke", "regression"})  // Test grouping
@Test(dependsOnMethods = {"testA"})     // Dependencies
@Test(expectedExceptions = Exception.class)  // Expected exception
@Test(timeOut = 1000)             // Timeout in milliseconds
@Test(invocationCount = 5)        // Run test N times
@Test(dataProvider = "dataName")  // Data-driven testing
```

### Lifecycle
```java
@BeforeSuite     // Runs once before test suite
@BeforeTest      // Runs before <test> tag in XML
@BeforeClass     // Runs once before test class
@BeforeMethod    // Runs before each test method
@AfterMethod     // Runs after each test method
@AfterClass      // Runs once after test class
@AfterTest       // Runs after <test> tag in XML
@AfterSuite      // Runs once after test suite
```

## TestNG Assertions

```java
// Equality (Note: actual first, then expected)
assertEquals(actual, expected);
assertEquals(actual, expected, "Custom message");
assertNotEquals(actual, unexpected);

// Truthiness
assertTrue(condition);
assertTrue(condition, "Message");
assertFalse(condition);
assertNull(object);
assertNotNull(object);

// Objects
assertSame(actual, expected);
assertNotSame(object1, object2);

// Collections
assertEquals(actualArray, expectedArray);

// Explicit fail
fail("Failure message");
```

## Test Groups Example

```java
public class UserServiceTest {

    @Test(groups = {"smoke"})
    public void shouldCreateUser() {
        // Quick smoke test
    }

    @Test(groups = {"regression", "database"})
    public void shouldQueryUserDatabase() {
        // Full regression test
    }

    @Test(groups = {"integration"})
    public void shouldIntegrateWithExternalAPI() {
        // Integration test
    }
}
```

Run specific groups:
```bash
mvn test -Dgroups=smoke
mvn test -Dgroups="smoke,regression"
```

## TestNG XML Configuration

```xml
<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">
<suite name="Test Suite">
    <test name="Calculator Tests">
        <classes>
            <class name="com.example.CalculatorTest"/>
        </classes>
    </test>

    <test name="Smoke Tests">
        <groups>
            <run>
                <include name="smoke"/>
            </run>
        </groups>
        <packages>
            <package name="com.example.*"/>
        </packages>
    </test>
</suite>
```

## Parallel Execution

```java
@Test(threadPoolSize = 3, invocationCount = 10)
public void shouldRunInParallel() {
    // This test runs 10 times with 3 threads
}
```

Or in XML:
```xml
<suite name="Parallel Suite" parallel="methods" thread-count="5">
    <test name="Tests">
        <classes>
            <class name="com.example.CalculatorTest"/>
        </classes>
    </test>
</suite>
```

## Dependent Tests

```java
public class OrderedTest {

    @Test
    public void testA() {
        System.out.println("Test A");
    }

    @Test(dependsOnMethods = {"testA"})
    public void testB() {
        System.out.println("Test B - runs after testA");
    }

    @Test(dependsOnMethods = {"testA", "testB"})
    public void testC() {
        System.out.println("Test C - runs after testA and testB");
    }
}
```

## With Mockito

```java
import org.testng.annotations.Test;
import org.testng.annotations.BeforeMethod;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;
import static org.testng.Assert.*;
import static org.mockito.Mockito.*;

public class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeMethod
    public void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void shouldFindUserById() {
        // Arrange
        User mockUser = new User(1, "Alice");
        when(userRepository.findById(1)).thenReturn(mockUser);

        // Act
        User result = userService.getUser(1);

        // Assert
        assertEquals(result.getName(), "Alice");
        verify(userRepository).findById(1);
    }
}
```

## Maven Configuration

```xml
<dependencies>
    <dependency>
        <groupId>org.testng</groupId>
        <artifactId>testng</artifactId>
        <version>7.8.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.0.0</version>
            <configuration>
                <suiteXmlFiles>
                    <suiteXmlFile>testng.xml</suiteXmlFile>
                </suiteXmlFiles>
            </configuration>
        </plugin>
    </plugins>
</build>
```

## Gradle Configuration

```groovy
dependencies {
    testImplementation 'org.testng:testng:7.8.0'
}

test {
    useTestNG() {
        suites 'src/test/resources/testng.xml'
    }
}
```

## TestNG Advantages

1. **Flexible configuration**: XML suite files for complex scenarios
2. **Test grouping**: Organize tests by smoke, regression, integration
3. **Parallel execution**: Built-in parallel test support
4. **Test dependencies**: Control execution order
5. **Data providers**: Powerful data-driven testing
6. **Listeners**: Custom test lifecycle hooks

## Best Practices

1. **Use test groups**: Organize tests for different scenarios
2. **Leverage data providers**: Reduce test code duplication
3. **Configure via XML**: Manage test suites externally
4. **Use priorities wisely**: Control critical test execution order
5. **Parallel testing**: Speed up test execution
6. **Independent tests**: Avoid dependencies when possible

## References

- TestNG Documentation: https://testng.org/doc/documentation-main.html
- TestNG Annotations: https://testng.org/doc/documentation-main.html#annotations
- Java Patterns: `skills/test-generation/java-patterns.md`
- JUnit 5 Template: `skills/templates/java-junit5-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
