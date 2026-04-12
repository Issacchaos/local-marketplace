# Kotlin JUnit 5 + MockK Test Template

**Purpose**: Template for generating JUnit 5 + MockK test files for Kotlin projects
**Target Language**: Kotlin
**Test Framework**: JUnit 5 (Jupiter)
**Mocking Library**: MockK
**Version Support**: JUnit 5.0.0+, MockK 1.9.0+
**Build Systems**: Maven, Gradle (Groovy DSL), Gradle (Kotlin DSL)

## Template Structure

### Basic Test File Template

```kotlin
package {PACKAGE_NAME}

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*
import io.mockk.unmockkAll

/**
 * Tests for {CLASS_NAME}.
 *
 * Coverage:
 * - {TEST_COVERAGE_AREA_1}
 * - {TEST_COVERAGE_AREA_2}
 * - {TEST_COVERAGE_AREA_3}
 */
@DisplayName("{DISPLAY_NAME}")
class {TEST_CLASS_NAME} {

    {SETUP_FIELDS}

    @BeforeEach
    fun setUp() {
        {SETUP_CODE}
    }

    @AfterEach
    fun tearDown() {
        unmockkAll()
    }

    {TEST_METHODS}
}
```

### Template with MockK Extension

```kotlin
package {PACKAGE_NAME}

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.extension.ExtendWith
import io.mockk.MockK
import io.mockk.InjectMockKs
import io.mockk.every
import io.mockk.verify
import io.mockk.junit5.MockKExtension

@ExtendWith(MockKExtension::class)
@DisplayName("{DISPLAY_NAME}")
class {TEST_CLASS_NAME} {

    @MockK
    private lateinit var {DEPENDENCY_FIELD}: {DEPENDENCY_TYPE}

    @InjectMockKs
    private lateinit var {CLASS_UNDER_TEST_FIELD}: {CLASS_NAME}

    {SETUP_FIELDS}

    @BeforeEach
    fun setUp() {
        {SETUP_CODE}
    }

    {TEST_METHODS}
}
```

## Template Placeholders

| Placeholder | Description | Example |
|---|---|---|
| `{PACKAGE_NAME}` | Kotlin package declaration | `com.example.calculator` |
| `{CLASS_NAME}` | Class being tested | `Calculator`, `UserService` |
| `{TEST_CLASS_NAME}` | Test class name | `CalculatorTest`, `UserServiceTest` |
| `{DISPLAY_NAME}` | Readable test suite name | `Calculator Tests` |
| `{TEST_COVERAGE_AREA_N}` | Coverage areas | `Addition operations`, `Error handling` |
| `{SETUP_FIELDS}` | Instance variable declarations | `private lateinit var calculator: Calculator` |
| `{SETUP_CODE}` | Initialization in setUp | `calculator = Calculator()` |
| `{DEPENDENCY_FIELD}` | Mocked dependency field name | `userRepository` |
| `{DEPENDENCY_TYPE}` | Mocked dependency type | `UserRepository` |
| `{CLASS_UNDER_TEST_FIELD}` | Class under test field name | `userService` |
| `{TEST_METHODS}` | Generated `@Test` functions | Individual test functions |

## Kotlin Conventions

### File Naming
- **Pattern**: `*Test.kt`
- **Location**: `src/test/kotlin/{package}/`
- **Example**: `src/test/kotlin/com/example/CalculatorTest.kt`

### Class and Method Conventions
- No `public` modifier on class or methods (default visibility is public in Kotlin)
- Use `fun` keyword (not `void`)
- Use `val`/`var` or `lateinit var` for fields
- Use `companion object` with `@JvmStatic` for `@BeforeAll`/`@AfterAll`

## Test Method Template (AAA Pattern)

```kotlin
@Test
@DisplayName("{READABLE_TEST_NAME}")
fun {TEST_FUNCTION_NAME}() {
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

```kotlin
package com.example

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*

/**
 * Tests for Calculator.
 *
 * Coverage:
 * - Basic arithmetic operations
 * - Error handling for invalid inputs
 * - Edge cases for boundary values
 */
@DisplayName("Calculator Tests")
class CalculatorTest {

    private lateinit var calculator: Calculator

    @BeforeEach
    fun setUp() {
        calculator = Calculator()
    }

    @Test
    @DisplayName("Should add two positive numbers correctly")
    fun shouldAddTwoPositiveNumbers() {
        // Arrange
        val a = 5
        val b = 3

        // Act
        val result = calculator.add(a, b)

        // Assert
        assertEquals(8, result, "5 + 3 should equal 8")
    }

    @Test
    @DisplayName("Should handle negative numbers in addition")
    fun shouldHandleNegativeNumbers() {
        val result = calculator.add(-5, -3)
        assertEquals(-8, result)
    }

    @Test
    @DisplayName("Should throw ArithmeticException when dividing by zero")
    fun shouldThrowExceptionWhenDividingByZero() {
        val exception = assertThrows<ArithmeticException> {
            calculator.divide(10, 0)
        }
        assertEquals("Division by zero", exception.message)
    }

    @Test
    fun shouldMultiplyNumbers() {
        assertEquals(20, calculator.multiply(4, 5))
    }
}
```

### Example 2: Tests with MockK

```kotlin
package com.example

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.extension.ExtendWith
import io.mockk.MockK
import io.mockk.InjectMockKs
import io.mockk.every
import io.mockk.verify
import io.mockk.unmockkAll
import io.mockk.junit5.MockKExtension

/**
 * Tests for UserService with mocked dependencies.
 */
@ExtendWith(MockKExtension::class)
@DisplayName("User Service Tests")
class UserServiceTest {

    @MockK
    private lateinit var userRepository: UserRepository

    @MockK
    private lateinit var emailService: EmailService

    @InjectMockKs
    private lateinit var userService: UserService

    private val testUser = User(id = 1, name = "Alice", email = "alice@example.com")

    @Test
    @DisplayName("Should find user by ID using repository")
    fun shouldFindUserById() {
        // Arrange
        every { userRepository.findById(1) } returns testUser

        // Act
        val found = userService.getUser(1)

        // Assert
        assertNotNull(found)
        assertEquals("Alice", found.name)
        verify { userRepository.findById(1) }
    }

    @Test
    @DisplayName("Should return null when user not found")
    fun shouldReturnNullWhenUserNotFound() {
        every { userRepository.findById(999) } returns null

        val result = userService.getUser(999)

        assertNull(result)
        verify { userRepository.findById(999) }
    }

    @Test
    @DisplayName("Should throw UserNotFoundException for missing user")
    fun shouldThrowExceptionWhenUserNotFound() {
        every { userRepository.findById(999) } throws UserNotFoundException("User not found")

        assertThrows<UserNotFoundException> {
            userService.getUser(999)
        }
    }

    @Test
    @DisplayName("Should create user and send welcome email")
    fun shouldCreateUserAndSendEmail() {
        // Arrange
        every { userRepository.save(any()) } returns testUser
        every { emailService.sendWelcomeEmail(any()) } just runs

        // Act
        val created = userService.createUser("Alice", "alice@example.com")

        // Assert
        assertNotNull(created)
        verify { userRepository.save(any()) }
        verify { emailService.sendWelcomeEmail(any()) }
    }
}
```

### Example 3: Data Class Equality and Kotlin Idioms

```kotlin
package com.example

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Assertions.*

@DisplayName("Order Service Tests")
class OrderServiceTest {

    private lateinit var orderService: OrderService

    @BeforeEach
    fun setUp() {
        orderService = OrderService()
    }

    @Test
    @DisplayName("Should create order with correct total")
    fun shouldCreateOrderWithCorrectTotal() {
        // Arrange — data class, no custom equals needed
        val expected = Order(
            id = 1,
            items = listOf(OrderItem("Widget", 10.0, 2)),
            total = 20.0
        )

        // Act
        val result = orderService.createOrder(listOf(OrderItem("Widget", 10.0, 2)))

        // Assert — structural equality via data class
        assertEquals(expected.total, result.total)
        assertEquals(expected.items.size, result.items.size)
    }

    @Test
    @DisplayName("Should return all orders as list")
    fun shouldReturnAllOrders() {
        orderService.addOrder(Order(1, emptyList(), 0.0))
        orderService.addOrder(Order(2, emptyList(), 0.0))

        val orders = orderService.findAll()

        assertAll("orders",
            { assertNotNull(orders) },
            { assertEquals(2, orders.size) }
        )
    }
}
```

### Example 4: Coroutine Testing

```kotlin
package com.example

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.unmockkAll
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.ExperimentalCoroutinesApi

@OptIn(ExperimentalCoroutinesApi::class)
@DisplayName("User Service Coroutine Tests")
class UserServiceCoroutineTest {

    private val userRepository = mockk<UserRepository>()
    private val userService = UserService(userRepository)

    @AfterEach
    fun tearDown() {
        unmockkAll()
    }

    @Test
    fun shouldFetchUsersAsync() = runTest {
        // Arrange
        val users = listOf(User(1, "Alice"), User(2, "Bob"))
        coEvery { userRepository.findAllSuspend() } returns users

        // Act
        val result = userService.getAllUsersAsync()

        // Assert
        assertEquals(2, result.size)
        coVerify { userRepository.findAllSuspend() }
    }

    @Test
    fun shouldHandleAsyncException() = runTest {
        coEvery { userRepository.findAllSuspend() } throws RuntimeException("DB error")

        assertThrows<RuntimeException> {
            userService.getAllUsersAsync()
        }
    }
}
```

## JUnit 5 Annotations Reference

```kotlin
@BeforeAll   // Runs once before all tests (must be in companion object with @JvmStatic)
@BeforeEach  // Runs before each test
@Test        // Test function
@AfterEach   // Runs after each test
@AfterAll    // Runs once after all tests (must be in companion object with @JvmStatic)
@DisplayName // Human-readable test name
@Disabled    // Skip test
```

## MockK Annotations Reference

```kotlin
@MockK                // Create a mock
@InjectMockKs         // Inject mocks into class under test
@SpyK                 // Create a spy (partial mock)
@RelaxedMockK         // Mock that returns default values without stubbing
@MockKExtension       // JUnit 5 extension for MockK
```

## Gradle Kotlin DSL Configuration

```kotlin
// build.gradle.kts
dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.10.0")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.10.0")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    testImplementation("io.mockk:mockk-junit5:1.13.8")  // MockKExtension
}

tasks.test {
    useJUnitPlatform()
}
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
    <dependency>
        <groupId>io.mockk</groupId>
        <artifactId>mockk-jvm</artifactId>
        <version>1.13.8</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.jetbrains.kotlinx</groupId>
        <artifactId>kotlinx-coroutines-test</artifactId>
        <version>1.7.3</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## References

- MockK Documentation: https://mockk.io/
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- Kotlin Patterns: `skills/test-generation/kotlin-patterns.md`

---

**Last Updated**: 2026-02-23
**Phase**: 4 - Implementation
**Status**: Complete
