# Java JUnit Helper Template

This template provides reusable test helper utilities for Java projects using JUnit 4/5 and Mockito.

## Mock Creation Helpers

```java
import org.mockito.Mockito;
import static org.mockito.Mockito.*;

/**
 * Create a mock API client with common methods configured.
 */
public class MockHelpers {
    public static ApiClient createMockApiClient() {
        ApiClient mockClient = mock(ApiClient.class);
        when(mockClient.getBaseUrl()).thenReturn("https://api.example.com");
        when(mockClient.get(anyString())).thenReturn(new Response("ok", 200));
        when(mockClient.post(anyString(), any())).thenReturn(new Response("created", 201));
        when(mockClient.put(anyString(), any())).thenReturn(new Response("updated", 200));
        when(mockClient.delete(anyString())).thenReturn(new Response("deleted", 204));
        return mockClient;
    }

    /**
     * Create a mock database connection with common operations.
     */
    public static Database createMockDatabase() {
        Database mockDb = mock(Database.class);
        when(mockDb.connect()).thenReturn(true);
        when(mockDb.disconnect()).thenReturn(true);
        when(mockDb.query(anyString())).thenReturn(new ArrayList<>());
        when(mockDb.execute(anyString())).thenReturn(1);
        return mockDb;
    }

    /**
     * Create a mock logger with common logging methods.
     */
    public static Logger createMockLogger() {
        Logger mockLogger = mock(Logger.class);
        doNothing().when(mockLogger).info(anyString());
        doNothing().when(mockLogger).warn(anyString());
        doNothing().when(mockLogger).error(anyString());
        doNothing().when(mockLogger).debug(anyString());
        return mockLogger;
    }
}
```

## Test Data Builders

```java
/**
 * Builder for creating test User objects with default values.
 */
public class TestUserBuilder {
    private int id = 1;
    private String name = "Test User";
    private String email = "test@example.com";
    private int age = 30;
    private String role = "user";

    public TestUserBuilder withId(int id) {
        this.id = id;
        return this;
    }

    public TestUserBuilder withName(String name) {
        this.name = name;
        return this;
    }

    public TestUserBuilder withEmail(String email) {
        this.email = email;
        return this;
    }

    public TestUserBuilder withAge(int age) {
        this.age = age;
        return this;
    }

    public TestUserBuilder withRole(String role) {
        this.role = role;
        return this;
    }

    public User build() {
        return new User(id, name, email, age, role);
    }

    public static User buildDefault() {
        return new TestUserBuilder().build();
    }
}

/**
 * Builder for creating test Product objects with default values.
 */
public class TestProductBuilder {
    private int id = 1;
    private String name = "Test Product";
    private double price = 99.99;
    private String category = "electronics";
    private boolean inStock = true;

    public TestProductBuilder withId(int id) {
        this.id = id;
        return this;
    }

    public TestProductBuilder withName(String name) {
        this.name = name;
        return this;
    }

    public TestProductBuilder withPrice(double price) {
        this.price = price;
        return this;
    }

    public TestProductBuilder withCategory(String category) {
        this.category = category;
        return this;
    }

    public TestProductBuilder withInStock(boolean inStock) {
        this.inStock = inStock;
        return this;
    }

    public Product build() {
        return new Product(id, name, price, category, inStock);
    }

    public static Product buildDefault() {
        return new TestProductBuilder().build();
    }

    public static List<Product> buildList(int count) {
        List<Product> products = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            products.add(new TestProductBuilder()
                .withId(i + 1)
                .withName("Product " + (i + 1))
                .build());
        }
        return products;
    }
}
```

## Setup and Teardown Utilities

```java
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.mockito.MockitoAnnotations;

/**
 * Base test class with common setup and teardown.
 */
public abstract class BaseTest {
    protected ApiClient mockApi;
    protected Database mockDb;
    protected Logger mockLogger;
    private AutoCloseable closeable;

    @BeforeEach
    public void setUp() {
        closeable = MockitoAnnotations.openMocks(this);
        mockApi = MockHelpers.createMockApiClient();
        mockDb = MockHelpers.createMockDatabase();
        mockLogger = MockHelpers.createMockLogger();
    }

    @AfterEach
    public void tearDown() throws Exception {
        if (closeable != null) {
            closeable.close();
        }
        Mockito.reset(mockApi, mockDb, mockLogger);
    }
}

/**
 * Utility for running tests with timeouts.
 */
public class TestTimeoutUtil {
    public static <T> T runWithTimeout(Callable<T> callable, long timeoutMs) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<T> future = executor.submit(callable);
        try {
            return future.get(timeoutMs, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            throw new AssertionError("Test timeout after " + timeoutMs + "ms");
        } finally {
            executor.shutdown();
        }
    }
}

/**
 * Utility for database test setup and cleanup.
 */
public class DatabaseTestUtil {
    public static void withTestDatabase(Consumer<Database> testCode) {
        Database db = MockHelpers.createMockDatabase();
        db.connect();
        try {
            testCode.accept(db);
        } finally {
            db.disconnect();
        }
    }
}
```

## Usage Examples

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

public class UserServiceTest extends BaseTest {

    @Test
    public void testGetUserById() {
        // Arrange
        User testUser = new TestUserBuilder()
            .withId(123)
            .withName("John Doe")
            .build();
        when(mockApi.get("/users/123")).thenReturn(testUser);

        UserService service = new UserService(mockApi, mockLogger);

        // Act
        User result = service.getUserById(123);

        // Assert
        assertEquals(testUser, result);
        verify(mockApi).get("/users/123");
    }

    @Test
    public void testCreateUser() {
        // Arrange
        User newUser = new TestUserBuilder()
            .withId(0)
            .withName("Jane Doe")
            .build();
        User createdUser = new TestUserBuilder()
            .withId(456)
            .withName("Jane Doe")
            .build();
        when(mockApi.post(eq("/users"), any())).thenReturn(createdUser);

        UserService service = new UserService(mockApi, mockLogger);

        // Act
        User result = service.createUser(newUser);

        // Assert
        assertEquals(456, result.getId());
        verify(mockApi).post(eq("/users"), eq(newUser));
        verify(mockLogger).info(anyString());
    }

    @Test
    public void testGetMultipleUsers() {
        // Arrange
        List<User> users = List.of(
            TestUserBuilder.buildDefault(),
            new TestUserBuilder().withId(2).withName("User 2").build(),
            new TestUserBuilder().withId(3).withName("User 3").build()
        );
        when(mockApi.get("/users")).thenReturn(users);

        UserService service = new UserService(mockApi, mockLogger);

        // Act
        List<User> result = service.getAllUsers();

        // Assert
        assertEquals(3, result.size());
        verify(mockApi).get("/users");
    }
}
```
