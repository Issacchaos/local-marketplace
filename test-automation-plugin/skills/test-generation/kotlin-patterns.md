# Kotlin Test Generation Patterns

**Version**: 1.0.0
**Language**: Kotlin
**Frameworks**: JUnit 5 (Jupiter) + MockK
**Purpose**: Testing patterns and best practices for Kotlin test generation

## Overview

Kotlin test generation patterns for JUnit 5 + MockK. This skill covers Kotlin-idiomatic syntax (no `public`, no semicolons, type inference), MockK for mocking, and coroutine testing with `runTest`.

**Scope**: JUnit 5 + MockK only. Kotest is excluded from this skill.

## File Organization

```
project/
├── src/
│   ├── main/kotlin/
│   │   └── com/example/
│   │       └── Calculator.kt
│   └── test/kotlin/
│       └── com/example/
│           └── CalculatorTest.kt
├── build.gradle.kts
```

**Naming Conventions**:
- Test files: `*Test.kt` (e.g., `CalculatorTest.kt`)
- Test location: `src/test/kotlin/{package}/` — mirrors `src/main/kotlin/{package}/`
- Package: Same as source class being tested

## JUnit 5 Patterns (Kotlin Syntax)

### Basic Test Structure

```kotlin
package com.example

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Assertions.*

@DisplayName("Calculator Tests")
class CalculatorTest {

    private lateinit var calculator: Calculator

    @BeforeEach
    fun setUp() {
        calculator = Calculator()
    }

    @AfterEach
    fun tearDown() {
        // cleanup if needed
    }

    @Test
    @DisplayName("Should add two positive numbers")
    fun shouldAddTwoPositiveNumbers() {
        // Arrange
        val a = 5
        val b = 3

        // Act
        val result = calculator.add(a, b)

        // Assert
        assertEquals(8, result)
    }

    @Test
    fun shouldThrowExceptionWhenDividingByZero() {
        // Kotlin assertThrows syntax with reified type parameter
        assertThrows<ArithmeticException> {
            calculator.divide(10, 0)
        }
    }
}
```

**Key Kotlin differences from Java**:
- No `public` modifier needed on test class or test methods
- `fun` instead of `void`
- `val`/`var` instead of typed declarations
- `lateinit var` for fields initialized in `setUp()`
- `assertThrows<ExceptionType> {}` with reified generic (no `.class`)
- No semicolons

### JUnit 5 Assertions in Kotlin

```kotlin
// Equality
assertEquals(expected, actual)
assertEquals(expected, actual, "Custom failure message")
assertNotEquals(unexpected, actual)

// Truthiness
assertTrue(condition)
assertFalse(condition)
assertNull(reference)
assertNotNull(reference)

// Exception testing — Kotlin syntax
assertThrows<IllegalArgumentException> {
    someMethod()
}

val exception = assertThrows<RuntimeException> {
    someMethod()
}
assertEquals("Expected message", exception.message)

// Multiple assertions
assertAll("Person validation",
    { assertEquals("John", person.firstName) },
    { assertEquals("Doe", person.lastName) },
    { assertEquals(30, person.age) }
)

// Timeout
assertTimeout(Duration.ofSeconds(1)) {
    // code that should complete within 1 second
}
```

### Parameterized Tests

```kotlin
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.ValueSource
import org.junit.jupiter.params.provider.CsvSource
import org.junit.jupiter.params.provider.MethodSource
import java.util.stream.Stream

class CalculatorTest {

    @ParameterizedTest
    @ValueSource(ints = [1, 2, 3, 4, 5])
    fun shouldReturnTrueForPositiveNumbers(number: Int) {
        assertTrue(calculator.isPositive(number))
    }

    @ParameterizedTest
    @CsvSource(
        "5, 3, 8",
        "10, 20, 30",
        "-5, 5, 0"
    )
    fun shouldAddNumbers(a: Int, b: Int, expected: Int) {
        assertEquals(expected, calculator.add(a, b))
    }

    companion object {
        @JvmStatic
        fun provideTestData(): Stream<org.junit.jupiter.params.provider.Arguments> = Stream.of(
            org.junit.jupiter.params.provider.Arguments.of(10, 10),
            org.junit.jupiter.params.provider.Arguments.of(20, 20)
        )
    }

    @ParameterizedTest
    @MethodSource("provideTestData")
    fun shouldHandleValues(input: Int, expected: Int) {
        assertEquals(expected, input)
    }
}
```

## MockK Patterns

### Basic MockK Setup

```kotlin
import io.mockk.MockKAnnotations
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import io.mockk.unmockkAll
import org.junit.jupiter.api.extension.ExtendWith
import io.mockk.junit5.MockKExtension

@ExtendWith(MockKExtension::class)
class UserServiceTest {

    @MockK
    private lateinit var userRepository: UserRepository

    @InjectMockKs
    private lateinit var userService: UserService

    @Test
    fun shouldFindUserById() {
        // Arrange
        val mockUser = User(id = 1, name = "Alice")
        every { userRepository.findById(1) } returns mockUser

        // Act
        val result = userService.getUser(1)

        // Assert
        assertEquals("Alice", result.name)
        verify { userRepository.findById(1) }
    }
}
```

### MockK Without Extension (Manual Setup)

```kotlin
class UserServiceTest {

    private val userRepository = mockk<UserRepository>()
    private val userService = UserService(userRepository)

    @AfterEach
    fun tearDown() {
        unmockkAll()
    }

    @Test
    fun shouldFindUserById() {
        every { userRepository.findById(1) } returns User(1, "Alice")

        val result = userService.getUser(1)

        assertEquals("Alice", result.name)
        verify { userRepository.findById(1) }
    }
}
```

### MockK Behaviors

```kotlin
// Return value
every { mockRepository.findById(1) } returns user

// Return null (for nullable return type)
every { mockRepository.findById(999) } returns null

// Throw exception
every { mockRepository.findById(-1) } throws NotFoundException("Not found")

// Return different values on successive calls
every { mockRepository.findAll() } returnsMany listOf(list1, list2)

// Argument matchers
every { mockRepository.findById(any()) } returns user
every { mockRepository.save(any()) } returns user

// Void (Unit) methods
every { mockRepository.delete(any()) } just runs

// Verify interactions
verify { mockRepository.findById(1) }
verify(exactly = 2) { mockRepository.findAll() }
verify(exactly = 0) { mockRepository.delete(any()) }

// Verify all declared verifications were called
confirmVerified(mockRepository)
```

### Suspend Function Mocking (Coroutines)

```kotlin
import io.mockk.coEvery
import io.mockk.coVerify

@Test
fun shouldFetchUserAsync() = runTest {
    // Arrange
    coEvery { userRepository.findByIdSuspend(1) } returns User(1, "Alice")

    // Act
    val result = userService.getUserAsync(1)

    // Assert
    assertEquals("Alice", result.name)
    coVerify { userRepository.findByIdSuspend(1) }
}
```

### Companion Object and Object Mocking

```kotlin
import io.mockk.mockkObject
import io.mockk.unmockkObject

@Test
fun shouldMockCompanionObject() {
    mockkObject(MyService.Companion)
    every { MyService.create() } returns mockk()

    val service = MyService.create()
    assertNotNull(service)

    unmockkObject(MyService.Companion)
}

// Singleton object mocking
@Test
fun shouldMockSingletonObject() {
    mockkObject(DatabaseConfig)
    every { DatabaseConfig.connectionString } returns "test-db"

    assertEquals("test-db", DatabaseConfig.connectionString)

    unmockkObject(DatabaseConfig)
}
```

## Coroutine Testing

```kotlin
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.TestCoroutineDispatcher
import kotlinx.coroutines.ExperimentalCoroutinesApi
import io.mockk.coEvery
import io.mockk.coVerify

@OptIn(ExperimentalCoroutinesApi::class)
class UserServiceCoroutineTest {

    private val testDispatcher = TestCoroutineDispatcher()
    private val userRepository = mockk<UserRepository>()
    private val userService = UserService(userRepository, testDispatcher)

    @AfterEach
    fun tearDown() {
        testDispatcher.cleanupTestCoroutines()
        unmockkAll()
    }

    @Test
    fun shouldFetchUsersSuspend() = runTest {
        // Arrange
        val users = listOf(User(1, "Alice"), User(2, "Bob"))
        coEvery { userRepository.findAll() } returns users

        // Act
        val result = userService.getAllUsersAsync()

        // Assert
        assertEquals(2, result.size)
        coVerify { userRepository.findAll() }
    }

    @Test
    fun shouldHandleCoroutineException() = runTest {
        coEvery { userRepository.findAll() } throws RuntimeException("DB error")

        assertThrows<RuntimeException> {
            userService.getAllUsersAsync()
        }
    }
}
```

## Kotlin-Specific Patterns

### Data Class Equality

Kotlin data classes implement structural equality automatically. No custom `equals()` needed.

```kotlin
@Test
fun shouldReturnCorrectUser() {
    val expected = User(id = 1, name = "Alice", email = "alice@example.com")

    val result = userService.getUser(1)

    // Structural equality works automatically for data classes
    assertEquals(expected, result)
}
```

### Nullable Type Assertions

```kotlin
@Test
fun shouldReturnNullWhenNotFound() {
    every { userRepository.findById(999) } returns null

    val result = userService.findUser(999)

    assertNull(result)
}

@Test
fun shouldReturnNonNullUser() {
    every { userRepository.findById(1) } returns User(1, "Alice")

    val result = userService.findUser(1)

    assertNotNull(result)
    assertEquals("Alice", result!!.name)
}
```

### Extension Function Testing

```kotlin
// Source
fun String.isPalindrome(): Boolean = this == this.reversed()

// Test
class StringExtensionsTest {

    @Test
    fun shouldDetectPalindrome() {
        assertTrue("racecar".isPalindrome())
        assertFalse("hello".isPalindrome())
    }

    @Test
    fun shouldHandleEmptyString() {
        assertTrue("".isPalindrome())
    }
}
```

### String Templates in Test Messages

```kotlin
@Test
fun shouldAddNumbers() {
    val a = 5
    val b = 3
    val expected = 8

    val result = calculator.add(a, b)

    assertEquals(expected, result, "$a + $b should equal $expected")
}
```

## Test Structure: AAA Pattern

All tests use Arrange-Act-Assert:

```kotlin
@Test
fun shouldCreateUser() {
    // Arrange
    val name = "Alice"
    val email = "alice@example.com"
    every { userRepository.save(any()) } returns User(1, name, email)

    // Act
    val result = userService.createUser(name, email)

    // Assert
    assertNotNull(result)
    assertEquals(name, result.name)
    verify { userRepository.save(any()) }
}
```

## Setup and Teardown

```kotlin
@BeforeEach
fun setUp() {
    // Runs before each test — initialize fresh state
}

@AfterEach
fun tearDown() {
    unmockkAll()  // Always clean up MockK mocks
}

@BeforeAll
companion object {
    @JvmStatic
    @BeforeAll
    fun setUpAll() {
        // Runs once before all tests
    }

    @JvmStatic
    @AfterAll
    fun tearDownAll() {
        // Runs once after all tests
    }
}
```

## Anti-Patterns to Avoid

❌ **Using Mockito instead of MockK** for Kotlin code (MockK is Kotlin-native)
❌ **Forgetting `unmockkAll()`** in teardown — causes mock state leakage between tests
❌ **Using `every {}` instead of `coEvery {}`** for suspend functions
❌ **Forgetting `@JvmStatic`** on `@BeforeAll`/`@AfterAll` companion object methods
❌ **Adding `public` modifier** to test methods or classes (not idiomatic Kotlin)
❌ **Testing pure delegation methods** — If a function body is a single forwarding call with no transformation, branching, or error handling, the test covers the mock, not the class. Skip it unless logic exists.
❌ **Symmetric pair duplication** — For paired methods (e.g. `startedSpeaking`/`stoppedSpeaking`, `screenReaderEnabled`/`Disabled`) with identical internal logic, generate one test. Add a second only when the expected output or side-effect actually differs between the two.
❌ **Same guard-clause repeated across notification/event handler subtypes** — Test a shared early-return guard (null account, missing flag, etc.) once on one representative handler. Duplicating it per-subtype adds no coverage.

## Quick Reference

| Feature | Kotlin + JUnit 5 + MockK |
|---|---|
| Test annotation | `@Test` |
| Setup | `@BeforeEach fun setUp()` |
| Teardown | `@AfterEach fun tearDown()` |
| Extension | `@ExtendWith(MockKExtension::class)` |
| Create mock | `mockk<MyClass>()` |
| Stub | `every { mock.method() } returns value` |
| Stub suspend | `coEvery { mock.method() } returns value` |
| Verify | `verify { mock.method() }` |
| Verify suspend | `coVerify { mock.method() }` |
| Exception test | `assertThrows<Type> { code }` |
| Coroutine test | `fun test() = runTest { ... }` |
| Cleanup mocks | `unmockkAll()` |

## References

- MockK Documentation: https://mockk.io/
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- kotlinx-coroutines-test: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/
- Kotlin Testing Guide: https://kotlinlang.org/docs/jvm-test-using-junit.html

---

**Last Updated**: 2026-02-23
**Phase**: 4 - Implementation
**Status**: Complete
