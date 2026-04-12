# Kotlin MockK Helper Template

This template provides reusable test helper utilities for Kotlin projects using JUnit 5 and MockK.

## MockK Setup and Teardown Utilities

```kotlin
import io.mockk.MockKAnnotations
import io.mockk.unmockkAll
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach

/**
 * Base test class with common MockK setup and teardown.
 * Extend this class for tests that use MockK annotations manually.
 *
 * Prefer using @ExtendWith(MockKExtension::class) on individual test classes
 * when possible — use this base class only for shared setup across many test classes.
 */
abstract class BaseMockKTest {

    @BeforeEach
    open fun setUp() {
        MockKAnnotations.init(this)
    }

    @AfterEach
    open fun tearDown() {
        unmockkAll()
    }
}
```

## Mock Creation Helpers

```kotlin
import io.mockk.every
import io.mockk.mockk

/**
 * Create a mock API client with common methods pre-configured.
 */
fun createMockApiClient(): ApiClient {
    return mockk<ApiClient> {
        every { getBaseUrl() } returns "https://api.example.com"
        every { get(any()) } returns Response("ok", 200)
        every { post(any(), any()) } returns Response("created", 201)
        every { put(any(), any()) } returns Response("updated", 200)
        every { delete(any()) } returns Response("deleted", 204)
    }
}

/**
 * Create a mock database connection with common operations.
 */
fun createMockDatabase(): Database {
    return mockk<Database> {
        every { connect() } returns true
        every { disconnect() } returns true
        every { query(any()) } returns emptyList()
        every { execute(any()) } returns 1
    }
}

/**
 * Create a mock logger.
 */
fun createMockLogger(): Logger {
    return mockk<Logger>(relaxed = true)  // relaxed = returns defaults without explicit stubbing
}
```

## Coroutine Test Scope Helper

```kotlin
import kotlinx.coroutines.test.TestCoroutineDispatcher
import kotlinx.coroutines.test.TestCoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import io.mockk.unmockkAll
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach

/**
 * Base test class for coroutine-based tests.
 * Provides a TestCoroutineDispatcher and handles cleanup.
 */
@OptIn(ExperimentalCoroutinesApi::class)
abstract class BaseCoroutineTest {

    protected val testDispatcher = TestCoroutineDispatcher()
    protected val testScope = TestCoroutineScope(testDispatcher)

    @BeforeEach
    open fun setUp() {
        MockKAnnotations.init(this)
    }

    @AfterEach
    open fun tearDown() {
        testScope.cleanupTestCoroutines()
        testDispatcher.cleanupTestCoroutines()
        unmockkAll()
    }
}
```

## Test Data Builders

```kotlin
/**
 * Builder for creating test User objects with sensible defaults.
 * Kotlin data class — use copy() for variations.
 */
data class TestUser(
    val id: Int = 1,
    val name: String = "Test User",
    val email: String = "test@example.com",
    val age: Int = 30,
    val role: String = "user"
)

fun buildTestUser(
    id: Int = 1,
    name: String = "Test User",
    email: String = "test@example.com",
    age: Int = 30,
    role: String = "user"
): User = User(id = id, name = name, email = email, age = age, role = role)

fun buildTestUserList(count: Int): List<User> =
    (1..count).map { i -> buildTestUser(id = i, name = "User $i") }

/**
 * Builder for creating test Product objects with sensible defaults.
 */
fun buildTestProduct(
    id: Int = 1,
    name: String = "Test Product",
    price: Double = 99.99,
    category: String = "electronics",
    inStock: Boolean = true
): Product = Product(id = id, name = name, price = price, category = category, inStock = inStock)
```

## Common Assertion Helpers for Nullable Types

```kotlin
import org.junit.jupiter.api.Assertions.*

/**
 * Assert that a nullable value is not null and return it as non-null.
 * Avoids !! operator in test assertions.
 */
fun <T : Any> assertPresentAndGet(value: T?, message: String = "Expected non-null value"): T {
    assertNotNull(value, message)
    return value!!
}

/**
 * Assert that a list is not null and has the expected size.
 */
fun <T> assertListSize(list: List<T>?, expectedSize: Int) {
    assertNotNull(list, "Expected non-null list")
    assertEquals(expectedSize, list!!.size, "Expected list size $expectedSize but was ${list.size}")
}

/**
 * Assert that a Result<T> is a success and return the value.
 */
fun <T> assertSuccess(result: Result<T>): T {
    assertTrue(result.isSuccess, "Expected Result.success but was: ${result.exceptionOrNull()}")
    return result.getOrThrow()
}

/**
 * Assert that a Result<T> is a failure with the expected exception type.
 */
inline fun <reified E : Throwable> assertFailure(result: Result<*>): E {
    assertTrue(result.isFailure, "Expected Result.failure but was success")
    val exception = result.exceptionOrNull()
    assertNotNull(exception)
    assertTrue(exception is E, "Expected ${E::class.simpleName} but was ${exception!!::class.simpleName}")
    return exception as E
}
```

## Usage Examples

```kotlin
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import io.mockk.MockK
import io.mockk.InjectMockKs
import io.mockk.every
import io.mockk.verify
import io.mockk.junit5.MockKExtension
import org.junit.jupiter.api.Assertions.*

@ExtendWith(MockKExtension::class)
class UserServiceTest {

    @MockK
    private lateinit var mockApi: ApiClient

    @MockK
    private lateinit var mockLogger: Logger

    @InjectMockKs
    private lateinit var userService: UserService

    @Test
    fun shouldGetUserById() {
        // Arrange
        val testUser = buildTestUser(id = 123, name = "John Doe")
        every { mockApi.get("/users/123") } returns testUser

        // Act
        val result = userService.getUserById(123)

        // Assert — use helper to avoid !! operator
        val user = assertPresentAndGet(result)
        assertEquals(testUser.name, user.name)
        verify { mockApi.get("/users/123") }
    }

    @Test
    fun shouldGetAllUsers() {
        // Arrange
        val testUsers = buildTestUserList(3)
        every { mockApi.get("/users") } returns testUsers

        // Act
        val result = userService.getAllUsers()

        // Assert
        assertListSize(result, 3)
        verify { mockApi.get("/users") }
    }
}
```

## Coroutine Usage Example

```kotlin
import kotlinx.coroutines.test.runTest
import io.mockk.coEvery
import io.mockk.coVerify
import kotlinx.coroutines.ExperimentalCoroutinesApi

@OptIn(ExperimentalCoroutinesApi::class)
class UserServiceAsyncTest : BaseCoroutineTest() {

    private val userRepository = mockk<UserRepository>()
    private val userService by lazy { UserService(userRepository, testDispatcher) }

    @Test
    fun shouldFetchUsersAsync() = runTest {
        val users = buildTestUserList(2)
        coEvery { userRepository.findAll() } returns users

        val result = userService.getAllUsersAsync()

        assertListSize(result, 2)
        coVerify { userRepository.findAll() }
    }
}
```
