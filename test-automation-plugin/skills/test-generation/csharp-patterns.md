# C# Test Generation Patterns

**Version**: 1.0.0
**Language**: C#
**Frameworks**: xUnit, NUnit, MSTest
**Purpose**: C#-specific patterns for generating idiomatic, type-safe tests
**Status**: Phase 4 - Systems Languages

## Overview

C# test generation patterns covering xUnit (primary), NUnit, and MSTest frameworks. This skill focuses on C#-specific features including async/await, LINQ, nullable reference types, IDisposable patterns, and mocking with Moq.

## C# Testing Fundamentals

### Framework Selection

#### xUnit (Recommended for Modern .NET)

**Characteristics**:
- Modern, extensible testing framework
- Constructor/Dispose for setup/teardown
- Parallel test execution by default
- No base classes required
- `[Fact]` for simple tests, `[Theory]` for parameterized

**When to Use**:
- New .NET projects (default choice)
- .NET Core/.NET 5+
- Projects needing parallel execution
- Teams preferring modern patterns

#### NUnit (Classic .NET Testing)

**Characteristics**:
- Mature, feature-rich framework
- `[Test]` and `[TestFixture]` attributes
- `[SetUp]` and `[TearDown]` methods
- Rich assertion library
- Similar to JUnit

**When to Use**:
- Legacy projects already using NUnit
- Teams familiar with JUnit/xUnit-style
- Projects needing NUnit-specific features

#### MSTest (Microsoft's Framework)

**Characteristics**:
- Microsoft's built-in testing framework
- `[TestMethod]` and `[TestClass]` attributes
- Native Visual Studio integration
- Enterprise-friendly

**When to Use**:
- Enterprise projects with Visual Studio
- Teams preferring Microsoft tools
- Projects requiring VS test integration

## File Organization

### Project Structure

```
Solution/
├── src/
│   └── Calculator/
│       ├── Calculator.csproj
│       ├── Calculator.cs
│       ├── Operations/
│       │   ├── AddOperation.cs
│       │   └── DivideOperation.cs
│       └── Services/
│           └── CalculatorService.cs
├── tests/
│   └── Calculator.Tests/
│       ├── Calculator.Tests.csproj
│       ├── CalculatorTests.cs
│       ├── Operations/
│       │   ├── AddOperationTests.cs
│       │   └── DivideOperationTests.cs
│       └── Services/
│           └── CalculatorServiceTests.cs
└── Calculator.sln
```

### Naming Conventions

**Test Projects**:
- Pattern: `<ProjectName>.Tests` or `<ProjectName>.UnitTests`
- Example: `Calculator.Tests`, `MyApp.Services.Tests`
- Separate project from source code

**Test Files**:
- Pattern: `<ClassName>Tests.cs`
- Match source file: `Calculator.cs` → `CalculatorTests.cs`
- Mirror source structure in test project

**Test Classes**:
- Pattern: `<ClassName>Tests` (PascalCase)
- Example: `CalculatorTests`, `UserServiceTests`

**Test Methods**:
- Pattern: `<MethodName>_<Scenario>_<Expected>` (PascalCase with underscores)
- Examples:
  - `Add_TwoPositiveNumbers_ReturnsSum`
  - `Divide_ByZero_ThrowsDivideByZeroException`
  - `GetUser_InvalidId_ReturnsNull`

## xUnit Test Patterns (Primary)

### Basic Test Structure

```csharp
using Xunit;
using Calculator;

namespace Calculator.Tests
{
    /// <summary>
    /// Test suite for Calculator class.
    /// Tests basic arithmetic operations and error handling.
    /// </summary>
    public class CalculatorTests
    {
        // ====================================================================
        // Happy Path Tests
        // ====================================================================

        [Fact]
        public void Add_TwoPositiveNumbers_ReturnsSum()
        {
            // Arrange
            var calculator = new Calculator();
            int a = 5;
            int b = 3;

            // Act
            int result = calculator.Add(a, b);

            // Assert
            Assert.Equal(8, result);
        }

        [Fact]
        public void Subtract_TwoNumbers_ReturnsDifference()
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Subtract(10, 3);

            // Assert
            Assert.Equal(7, result);
        }

        // ====================================================================
        // Edge Case Tests
        // ====================================================================

        [Fact]
        public void Add_WithZero_ReturnsOtherNumber()
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Add(5, 0);

            // Assert
            Assert.Equal(5, result);
        }

        // ====================================================================
        // Error Handling Tests
        // ====================================================================

        [Fact]
        public void Divide_ByZero_ThrowsDivideByZeroException()
        {
            // Arrange
            var calculator = new Calculator();

            // Act & Assert
            Assert.Throws<DivideByZeroException>(() => calculator.Divide(10, 0));
        }
    }
}
```

### Constructor and Dispose (Setup/Teardown)

```csharp
public class DatabaseTests : IDisposable
{
    private readonly DatabaseConnection _connection;
    private readonly ITestOutputHelper _output;

    // Constructor runs before each test
    public DatabaseTests(ITestOutputHelper output)
    {
        _output = output;
        _connection = new DatabaseConnection("TestConnectionString");
        _connection.Open();
        _output.WriteLine("Database connection opened");
    }

    [Fact]
    public void Insert_ValidRecord_ReturnsId()
    {
        // Arrange
        var record = new Record { Name = "Test", Value = 42 };

        // Act
        int id = _connection.Insert(record);

        // Assert
        Assert.True(id > 0);
        _output.WriteLine($"Inserted record with ID: {id}");
    }

    // Dispose runs after each test
    public void Dispose()
    {
        _connection?.Close();
        _output.WriteLine("Database connection closed");
    }
}
```

### Theory Tests (Parameterized)

```csharp
public class CalculatorTheoryTests
{
    [Theory]
    [InlineData(1, 2, 3)]
    [InlineData(5, 5, 10)]
    [InlineData(-1, 1, 0)]
    [InlineData(0, 0, 0)]
    public void Add_VariousInputs_ReturnsExpectedSum(int a, int b, int expected)
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        int result = calculator.Add(a, b);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [MemberData(nameof(DivisionTestData))]
    public void Divide_VariousInputs_ReturnsExpectedQuotient(int dividend, int divisor, double expected)
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        double result = calculator.Divide(dividend, divisor);

        // Assert
        Assert.Equal(expected, result, precision: 2);
    }

    public static IEnumerable<object[]> DivisionTestData =>
        new List<object[]>
        {
            new object[] { 10, 2, 5.0 },
            new object[] { 9, 3, 3.0 },
            new object[] { 7, 2, 3.5 }
        };
}
```

### Class Fixtures (Shared Setup)

```csharp
// Fixture class
public class DatabaseFixture : IDisposable
{
    public DatabaseConnection Connection { get; private set; }

    public DatabaseFixture()
    {
        Connection = new DatabaseConnection("TestConnectionString");
        Connection.Open();
        Connection.InitializeTestData();
    }

    public void Dispose()
    {
        Connection?.Close();
    }
}

// Test class using fixture
public class UserRepositoryTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;

    public UserRepositoryTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public void GetUser_ExistingId_ReturnsUser()
    {
        // Arrange
        var repository = new UserRepository(_fixture.Connection);

        // Act
        var user = repository.GetUser(1);

        // Assert
        Assert.NotNull(user);
        Assert.Equal(1, user.Id);
    }
}
```

## Async/Await Testing

### Async Test Methods

```csharp
public class ApiClientTests
{
    [Fact]
    public async Task GetUserAsync_ValidId_ReturnsUser()
    {
        // Arrange
        var client = new ApiClient("https://api.example.com");
        int userId = 1;

        // Act
        User user = await client.GetUserAsync(userId);

        // Assert
        Assert.NotNull(user);
        Assert.Equal(userId, user.Id);
    }

    [Fact]
    public async Task CreateUserAsync_ValidUser_ReturnsCreatedUser()
    {
        // Arrange
        var client = new ApiClient("https://api.example.com");
        var newUser = new User
        {
            Name = "Alice",
            Email = "alice@example.com"
        };

        // Act
        User createdUser = await client.CreateUserAsync(newUser);

        // Assert
        Assert.NotNull(createdUser);
        Assert.True(createdUser.Id > 0);
        Assert.Equal("Alice", createdUser.Name);
    }

    [Fact]
    public async Task DeleteUserAsync_NonExistentId_ThrowsNotFoundException()
    {
        // Arrange
        var client = new ApiClient("https://api.example.com");

        // Act & Assert
        await Assert.ThrowsAsync<NotFoundException>(() =>
            client.DeleteUserAsync(99999));
    }
}
```

### Testing Async Error Handling

```csharp
[Fact]
public async Task GetUserAsync_Timeout_ThrowsTimeoutException()
{
    // Arrange
    var client = new ApiClient("https://api.example.com")
    {
        Timeout = TimeSpan.FromMilliseconds(1)
    };

    // Act & Assert
    await Assert.ThrowsAsync<TimeoutException>(() =>
        client.GetUserAsync(1));
}

[Fact]
public async Task SaveAsync_CancellationRequested_ThrowsOperationCanceledException()
{
    // Arrange
    var service = new DataService();
    var cts = new CancellationTokenSource();
    cts.Cancel();

    // Act & Assert
    await Assert.ThrowsAsync<OperationCanceledException>(() =>
        service.SaveAsync(new Data(), cts.Token));
}
```

## LINQ Testing Patterns

### Testing LINQ Queries

```csharp
[Fact]
public void GetActiveUsers_FiltersCorrectly_ReturnsActiveUsersOnly()
{
    // Arrange
    var users = new List<User>
    {
        new User { Id = 1, Name = "Alice", IsActive = true },
        new User { Id = 2, Name = "Bob", IsActive = false },
        new User { Id = 3, Name = "Charlie", IsActive = true }
    };
    var service = new UserService();

    // Act
    var activeUsers = service.GetActiveUsers(users);

    // Assert
    Assert.Equal(2, activeUsers.Count());
    Assert.All(activeUsers, user => Assert.True(user.IsActive));
    Assert.Contains(activeUsers, u => u.Name == "Alice");
    Assert.Contains(activeUsers, u => u.Name == "Charlie");
}

[Fact]
public void SortByName_SortsAlphabetically_ReturnsOrderedList()
{
    // Arrange
    var users = new List<User>
    {
        new User { Name = "Charlie" },
        new User { Name = "Alice" },
        new User { Name = "Bob" }
    };
    var service = new UserService();

    // Act
    var sorted = service.SortByName(users).ToList();

    // Assert
    Assert.Equal("Alice", sorted[0].Name);
    Assert.Equal("Bob", sorted[1].Name);
    Assert.Equal("Charlie", sorted[2].Name);
}
```

## Nullable Reference Types

### Testing with Nullable Types (.NET 6+)

```csharp
#nullable enable

public class UserServiceTests
{
    [Fact]
    public void GetUser_ExistingId_ReturnsUser()
    {
        // Arrange
        var service = new UserService();

        // Act
        User? user = service.GetUser(1);  // May return null

        // Assert
        Assert.NotNull(user);
        Assert.Equal(1, user.Id);  // After Assert.NotNull, compiler knows user is not null
    }

    [Fact]
    public void GetUser_NonExistentId_ReturnsNull()
    {
        // Arrange
        var service = new UserService();

        // Act
        User? user = service.GetUser(99999);

        // Assert
        Assert.Null(user);
    }

    [Fact]
    public void CreateUser_NullName_ThrowsArgumentNullException()
    {
        // Arrange
        var service = new UserService();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            service.CreateUser(null!, "email@example.com"));  // null! suppresses warning
    }
}
```

## Resource Management with `using` Statements

### Testing IDisposable

```csharp
[Fact]
public void ProcessFile_ValidFile_ReadsContent()
{
    // Arrange
    string testFile = "test.txt";
    File.WriteAllText(testFile, "Test content");

    try
    {
        // Act
        string result;
        using (var reader = new FileProcessor(testFile))
        {
            result = reader.ReadContent();
        }  // Dispose called here

        // Assert
        Assert.Equal("Test content", result);
    }
    finally
    {
        // Cleanup
        if (File.Exists(testFile))
        {
            File.Delete(testFile);
        }
    }
}

[Fact]
public void OpenConnection_WhenDisposed_ThrowsObjectDisposedException()
{
    // Arrange
    var connection = new DatabaseConnection("TestConnectionString");
    connection.Dispose();

    // Act & Assert
    Assert.Throws<ObjectDisposedException>(() =>
        connection.ExecuteQuery("SELECT * FROM Users"));
}
```

## Mocking with Moq

### Basic Mocking

```csharp
using Moq;

public class UserServiceTests
{
    [Fact]
    public void GetUser_CallsRepository_ReturnsUser()
    {
        // Arrange
        var mockRepository = new Mock<IUserRepository>();
        mockRepository
            .Setup(repo => repo.GetById(1))
            .Returns(new User { Id = 1, Name = "Alice" });

        var service = new UserService(mockRepository.Object);

        // Act
        var user = service.GetUser(1);

        // Assert
        Assert.NotNull(user);
        Assert.Equal("Alice", user.Name);
        mockRepository.Verify(repo => repo.GetById(1), Times.Once);
    }

    [Fact]
    public void SaveUser_CallsRepository_SavesUser()
    {
        // Arrange
        var mockRepository = new Mock<IUserRepository>();
        var service = new UserService(mockRepository.Object);
        var user = new User { Id = 1, Name = "Alice" };

        // Act
        service.SaveUser(user);

        // Assert
        mockRepository.Verify(
            repo => repo.Save(It.Is<User>(u => u.Id == 1 && u.Name == "Alice")),
            Times.Once);
    }
}
```

### Async Mocking

```csharp
[Fact]
public async Task GetUserAsync_CallsRepository_ReturnsUser()
{
    // Arrange
    var mockRepository = new Mock<IUserRepository>();
    mockRepository
        .Setup(repo => repo.GetByIdAsync(1))
        .ReturnsAsync(new User { Id = 1, Name = "Alice" });

    var service = new UserService(mockRepository.Object);

    // Act
    var user = await service.GetUserAsync(1);

    // Assert
    Assert.NotNull(user);
    Assert.Equal("Alice", user.Name);
}

[Fact]
public async Task SaveUserAsync_RepositoryThrows_PropagatesException()
{
    // Arrange
    var mockRepository = new Mock<IUserRepository>();
    mockRepository
        .Setup(repo => repo.SaveAsync(It.IsAny<User>()))
        .ThrowsAsync(new DbException("Connection failed"));

    var service = new UserService(mockRepository.Object);

    // Act & Assert
    await Assert.ThrowsAsync<DbException>(() =>
        service.SaveUserAsync(new User()));
}
```

### Mock Callbacks

```csharp
[Fact]
public void SaveUser_CallsRepositoryWithCorrectData_SavesUser()
{
    // Arrange
    var mockRepository = new Mock<IUserRepository>();
    User? savedUser = null;

    mockRepository
        .Setup(repo => repo.Save(It.IsAny<User>()))
        .Callback<User>(user => savedUser = user);

    var service = new UserService(mockRepository.Object);
    var user = new User { Id = 1, Name = "Alice" };

    // Act
    service.SaveUser(user);

    // Assert
    Assert.NotNull(savedUser);
    Assert.Equal(1, savedUser.Id);
    Assert.Equal("Alice", savedUser.Name);
}
```

## Exception Testing

### xUnit Exception Assertions

```csharp
[Fact]
public void Divide_ByZero_ThrowsDivideByZeroException()
{
    // Arrange
    var calculator = new Calculator();

    // Act & Assert
    Assert.Throws<DivideByZeroException>(() => calculator.Divide(10, 0));
}

[Fact]
public void Divide_ByZero_ThrowsWithCorrectMessage()
{
    // Arrange
    var calculator = new Calculator();

    // Act & Assert
    var exception = Assert.Throws<DivideByZeroException>(() =>
        calculator.Divide(10, 0));

    Assert.Equal("Cannot divide by zero", exception.Message);
}

[Fact]
public void SaveUser_NullUser_ThrowsArgumentNullException()
{
    // Arrange
    var service = new UserService();

    // Act & Assert
    var exception = Assert.Throws<ArgumentNullException>(() =>
        service.SaveUser(null!));

    Assert.Equal("user", exception.ParamName);
}
```

## Collection Assertions

### xUnit Collection Assertions

```csharp
[Fact]
public void GetUsers_ReturnsAllUsers_CorrectCount()
{
    // Arrange
    var service = new UserService();

    // Act
    var users = service.GetUsers();

    // Assert
    Assert.NotEmpty(users);
    Assert.Equal(3, users.Count());
    Assert.Contains(users, u => u.Name == "Alice");
    Assert.DoesNotContain(users, u => u.Name == "NonExistent");
    Assert.All(users, user => Assert.NotNull(user.Name));
}

[Fact]
public void GetActiveUsers_ReturnsExpectedSubset_InCorrectOrder()
{
    // Arrange
    var service = new UserService();

    // Act
    var activeUsers = service.GetActiveUsers().ToList();

    // Assert
    Assert.Equal(2, activeUsers.Count);
    Assert.Collection(activeUsers,
        user =>
        {
            Assert.Equal("Alice", user.Name);
            Assert.True(user.IsActive);
        },
        user =>
        {
            Assert.Equal("Charlie", user.Name);
            Assert.True(user.IsActive);
        });
}
```

## Test Organization Best Practices

### Organizing Tests by Category

```csharp
public class CalculatorTests
{
    // ====================================================================
    // Constructor Tests
    // ====================================================================

    [Fact]
    public void Constructor_CreatesInstance_NotNull()
    {
        var calculator = new Calculator();
        Assert.NotNull(calculator);
    }

    // ====================================================================
    // Addition Tests
    // ====================================================================

    [Fact]
    public void Add_PositiveNumbers_ReturnsSum()
    {
        // Test implementation
    }

    [Fact]
    public void Add_NegativeNumbers_ReturnsSum()
    {
        // Test implementation
    }

    // ====================================================================
    // Subtraction Tests
    // ====================================================================

    [Fact]
    public void Subtract_PositiveNumbers_ReturnsDifference()
    {
        // Test implementation
    }

    // ====================================================================
    // Error Handling Tests
    // ====================================================================

    [Fact]
    public void Divide_ByZero_ThrowsException()
    {
        // Test implementation
    }
}
```

## Common Assertion Patterns

### xUnit Assertions

```csharp
// Equality
Assert.Equal(expected, actual);
Assert.NotEqual(expected, actual);

// Identity
Assert.Same(expected, actual);
Assert.NotSame(expected, actual);

// Null checks
Assert.Null(value);
Assert.NotNull(value);

// Boolean
Assert.True(condition);
Assert.False(condition);

// Strings
Assert.StartsWith("prefix", actual);
Assert.EndsWith("suffix", actual);
Assert.Contains("substring", actual);
Assert.Matches(@"\d{3}-\d{3}-\d{4}", phoneNumber);

// Numeric
Assert.InRange(actual, low, high);
Assert.Equal(expected, actual, precision: 2);  // For doubles

// Collections
Assert.Empty(collection);
Assert.NotEmpty(collection);
Assert.Contains(item, collection);
Assert.DoesNotContain(item, collection);
Assert.All(collection, item => Assert.NotNull(item));

// Exceptions
Assert.Throws<TException>(() => action());
Assert.ThrowsAsync<TException>(() => asyncAction());

// Type checks
Assert.IsType<TExpected>(actual);
Assert.IsAssignableFrom<TExpected>(actual);
```

## References

- xUnit Documentation: https://xunit.net/
- Moq Documentation: https://github.com/moq/moq4
- C# Language Reference: https://learn.microsoft.com/en-us/dotnet/csharp/
- .NET Testing: https://learn.microsoft.com/en-us/dotnet/core/testing/
- xUnit Patterns: `skills/templates/csharp-xunit-template.md`

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
