# C# xUnit/NUnit Helper Template

This template provides reusable test helper utilities for C# projects using xUnit, NUnit, or MSTest with Moq.

## Mock Creation Helpers

```csharp
using Moq;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

/// <summary>
/// Factory class for creating common test mocks.
/// </summary>
public static class MockHelpers
{
    /// <summary>
    /// Create a mock API client with common methods configured.
    /// </summary>
    public static Mock<IApiClient> CreateMockApiClient()
    {
        var mockClient = new Mock<IApiClient>();
        mockClient.Setup(x => x.BaseUrl).Returns("https://api.example.com");
        mockClient.Setup(x => x.GetAsync(It.IsAny<string>()))
            .ReturnsAsync(new Response { Status = "ok", StatusCode = 200 });
        mockClient.Setup(x => x.PostAsync(It.IsAny<string>(), It.IsAny<object>()))
            .ReturnsAsync(new Response { Status = "created", StatusCode = 201 });
        mockClient.Setup(x => x.PutAsync(It.IsAny<string>(), It.IsAny<object>()))
            .ReturnsAsync(new Response { Status = "updated", StatusCode = 200 });
        mockClient.Setup(x => x.DeleteAsync(It.IsAny<string>()))
            .ReturnsAsync(new Response { Status = "deleted", StatusCode = 204 });
        return mockClient;
    }

    /// <summary>
    /// Create a mock database connection with common operations.
    /// </summary>
    public static Mock<IDatabase> CreateMockDatabase()
    {
        var mockDb = new Mock<IDatabase>();
        mockDb.Setup(x => x.ConnectAsync()).ReturnsAsync(true);
        mockDb.Setup(x => x.DisconnectAsync()).ReturnsAsync(true);
        mockDb.Setup(x => x.QueryAsync<object>(It.IsAny<string>()))
            .ReturnsAsync(new List<object>());
        mockDb.Setup(x => x.ExecuteAsync(It.IsAny<string>())).ReturnsAsync(1);
        return mockDb;
    }

    /// <summary>
    /// Create a mock logger with common logging methods.
    /// </summary>
    public static Mock<ILogger> CreateMockLogger()
    {
        var mockLogger = new Mock<ILogger>();
        mockLogger.Setup(x => x.LogInfo(It.IsAny<string>()));
        mockLogger.Setup(x => x.LogWarning(It.IsAny<string>()));
        mockLogger.Setup(x => x.LogError(It.IsAny<string>()));
        mockLogger.Setup(x => x.LogDebug(It.IsAny<string>()));
        return mockLogger;
    }
}
```

## Test Data Builders

```csharp
/// <summary>
/// Builder for creating test User objects with default values.
/// </summary>
public class TestUserBuilder
{
    private int _id = 1;
    private string _name = "Test User";
    private string _email = "test@example.com";
    private int _age = 30;
    private string _role = "user";

    public TestUserBuilder WithId(int id)
    {
        _id = id;
        return this;
    }

    public TestUserBuilder WithName(string name)
    {
        _name = name;
        return this;
    }

    public TestUserBuilder WithEmail(string email)
    {
        _email = email;
        return this;
    }

    public TestUserBuilder WithAge(int age)
    {
        _age = age;
        return this;
    }

    public TestUserBuilder WithRole(string role)
    {
        _role = role;
        return this;
    }

    public User Build()
    {
        return new User
        {
            Id = _id,
            Name = _name,
            Email = _email,
            Age = _age,
            Role = _role
        };
    }

    public static User BuildDefault()
    {
        return new TestUserBuilder().Build();
    }

    public static List<User> BuildList(int count)
    {
        var users = new List<User>();
        for (int i = 0; i < count; i++)
        {
            users.Add(new TestUserBuilder()
                .WithId(i + 1)
                .WithName($"User {i + 1}")
                .WithEmail($"user{i + 1}@example.com")
                .Build());
        }
        return users;
    }
}

/// <summary>
/// Builder for creating test Product objects with default values.
/// </summary>
public class TestProductBuilder
{
    private int _id = 1;
    private string _name = "Test Product";
    private decimal _price = 99.99m;
    private string _category = "electronics";
    private bool _inStock = true;

    public TestProductBuilder WithId(int id)
    {
        _id = id;
        return this;
    }

    public TestProductBuilder WithName(string name)
    {
        _name = name;
        return this;
    }

    public TestProductBuilder WithPrice(decimal price)
    {
        _price = price;
        return this;
    }

    public TestProductBuilder WithCategory(string category)
    {
        _category = category;
        return this;
    }

    public TestProductBuilder WithInStock(bool inStock)
    {
        _inStock = inStock;
        return this;
    }

    public Product Build()
    {
        return new Product
        {
            Id = _id,
            Name = _name,
            Price = _price,
            Category = _category,
            InStock = _inStock
        };
    }

    public static Product BuildDefault()
    {
        return new TestProductBuilder().Build();
    }
}
```

## Setup and Teardown Utilities

```csharp
using Xunit;
using Moq;

/// <summary>
/// Base test fixture with common setup and teardown for xUnit.
/// </summary>
public class BaseTestFixture : IDisposable
{
    protected Mock<IApiClient> MockApi { get; private set; }
    protected Mock<IDatabase> MockDb { get; private set; }
    protected Mock<ILogger> MockLogger { get; private set; }

    public BaseTestFixture()
    {
        MockApi = MockHelpers.CreateMockApiClient();
        MockDb = MockHelpers.CreateMockDatabase();
        MockLogger = MockHelpers.CreateMockLogger();
    }

    public void Dispose()
    {
        // Cleanup resources if needed
        MockApi?.Reset();
        MockDb?.Reset();
        MockLogger?.Reset();
    }
}

/// <summary>
/// Utility for running async tests with timeouts.
/// </summary>
public static class TestTimeoutUtil
{
    public static async Task<T> RunWithTimeoutAsync<T>(
        Func<Task<T>> taskFunc,
        int timeoutMs = 5000)
    {
        var task = taskFunc();
        var timeoutTask = Task.Delay(timeoutMs);

        var completedTask = await Task.WhenAny(task, timeoutTask);

        if (completedTask == timeoutTask)
        {
            throw new TimeoutException($"Test timeout after {timeoutMs}ms");
        }

        return await task;
    }
}

/// <summary>
/// Utility for database test setup and cleanup.
/// </summary>
public static class DatabaseTestUtil
{
    public static async Task WithTestDatabaseAsync(
        Func<IDatabase, Task> testCode)
    {
        var mockDb = MockHelpers.CreateMockDatabase();
        await mockDb.Object.ConnectAsync();

        try
        {
            await testCode(mockDb.Object);
        }
        finally
        {
            await mockDb.Object.DisconnectAsync();
        }
    }
}
```

## Usage Examples

```csharp
using Xunit;
using Moq;
using FluentAssertions;

public class UserServiceTests : BaseTestFixture
{
    [Fact]
    public async Task GetUserById_ShouldReturnUser()
    {
        // Arrange
        var testUser = new TestUserBuilder()
            .WithId(123)
            .WithName("John Doe")
            .Build();

        MockApi.Setup(x => x.GetAsync("/users/123"))
            .ReturnsAsync(testUser);

        var service = new UserService(MockApi.Object, MockLogger.Object);

        // Act
        var result = await service.GetUserByIdAsync(123);

        // Assert
        result.Should().BeEquivalentTo(testUser);
        MockApi.Verify(x => x.GetAsync("/users/123"), Times.Once);
    }

    [Fact]
    public async Task CreateUser_ShouldReturnCreatedUser()
    {
        // Arrange
        var newUser = new TestUserBuilder()
            .WithId(0)
            .WithName("Jane Doe")
            .Build();

        var createdUser = new TestUserBuilder()
            .WithId(456)
            .WithName("Jane Doe")
            .Build();

        MockApi.Setup(x => x.PostAsync("/users", It.IsAny<User>()))
            .ReturnsAsync(createdUser);

        var service = new UserService(MockApi.Object, MockLogger.Object);

        // Act
        var result = await service.CreateUserAsync(newUser);

        // Assert
        result.Id.Should().Be(456);
        MockApi.Verify(x => x.PostAsync("/users", It.IsAny<User>()), Times.Once);
        MockLogger.Verify(x => x.LogInfo(It.IsAny<string>()), Times.AtLeastOnce);
    }

    [Fact]
    public async Task GetAllUsers_ShouldReturnMultipleUsers()
    {
        // Arrange
        var users = TestUserBuilder.BuildList(3);
        MockApi.Setup(x => x.GetAsync("/users"))
            .ReturnsAsync(users);

        var service = new UserService(MockApi.Object, MockLogger.Object);

        // Act
        var result = await service.GetAllUsersAsync();

        // Assert
        result.Should().HaveCount(3);
        MockApi.Verify(x => x.GetAsync("/users"), Times.Once);
    }

    [Fact]
    public async Task GetUserById_WithTimeout_ShouldNotExceedLimit()
    {
        // Arrange
        var testUser = TestUserBuilder.BuildDefault();
        MockApi.Setup(x => x.GetAsync(It.IsAny<string>()))
            .ReturnsAsync(testUser);

        var service = new UserService(MockApi.Object, MockLogger.Object);

        // Act & Assert
        var result = await TestTimeoutUtil.RunWithTimeoutAsync(
            () => service.GetUserByIdAsync(1),
            timeoutMs: 1000);

        result.Should().NotBeNull();
    }
}
```
