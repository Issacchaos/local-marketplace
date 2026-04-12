# C# xUnit Test Template

**Purpose**: Template for generating xUnit test files for C# projects
**Target Language**: C#
**Test Framework**: xUnit.net 2.x
**Version Support**: xUnit 2.4.0+, .NET 6.0+

## C# Language Features

### File-Scoped Namespaces (C# 10+)

For **.NET 6+** projects, use **file-scoped namespaces** to reduce indentation:

```csharp
namespace Calculator.Tests;  // Semicolon instead of braces

public class CalculatorTests
{
    // Tests here - one less level of indentation
}
```

**Benefits**:
- Reduces indentation by one level
- Modern C# convention (standard in .NET 6+)
- Cleaner code style

**Detection**: Check existing project files for namespace style. If the source project uses file-scoped namespaces, use them in tests too.

### Traditional Namespaces (C# 9 and earlier)

For **.NET Framework** or **older .NET Core** projects:

```csharp
namespace Calculator.Tests
{
    public class CalculatorTests
    {
        // Tests here
    }
}
```

## Template Structure

**Modern Style (Recommended for .NET 6+)**:
```csharp
using Xunit;
{ADDITIONAL_USINGS}

namespace {NAMESPACE}.Tests;

/// <summary>
/// Test suite for {CLASS_NAME}.
/// {SUITE_DESCRIPTION}
/// </summary>
public class {CLASS_NAME}Tests{FIXTURE_INTERFACE}
{
    {FIXTURE_FIELD}
    {CONSTRUCTOR}
    {DISPOSE_METHOD}

    {TEST_METHODS}
}
```

**Traditional Style**:
```csharp
using Xunit;
{ADDITIONAL_USINGS}

namespace {NAMESPACE}.Tests
{
    /// <summary>
    /// Test suite for {CLASS_NAME}.
    /// {SUITE_DESCRIPTION}
    /// </summary>
    public class {CLASS_NAME}Tests{FIXTURE_INTERFACE}
    {
        {FIXTURE_FIELD}
        {CONSTRUCTOR}
        {DISPOSE_METHOD}

        {TEST_METHODS}
    }
}
```

## Basic xUnit Test Template

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
            int a = 10;
            int b = 3;

            // Act
            int result = calculator.Subtract(a, b);

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

## With Constructor Setup (IDisposable)

```csharp
using Xunit;
using System;
using Database;

namespace Database.Tests
{
    /// <summary>
    /// Test suite for UserRepository.
    /// Tests CRUD operations with database connection management.
    /// </summary>
    public class UserRepositoryTests : IDisposable
    {
        private readonly DatabaseConnection _connection;
        private readonly UserRepository _repository;
        private readonly ITestOutputHelper _output;

        // Constructor runs before each test
        public UserRepositoryTests(ITestOutputHelper output)
        {
            _output = output;
            _connection = new DatabaseConnection("TestConnectionString");
            _connection.Open();
            _repository = new UserRepository(_connection);
            _output.WriteLine("Test setup completed");
        }

        // ====================================================================
        // Read Tests
        // ====================================================================

        [Fact]
        public void GetUser_ExistingId_ReturnsUser()
        {
            // Arrange
            int userId = 1;

            // Act
            var user = _repository.GetUser(userId);

            // Assert
            Assert.NotNull(user);
            Assert.Equal(userId, user.Id);
            _output.WriteLine($"Retrieved user: {user.Name}");
        }

        // ====================================================================
        // Create Tests
        // ====================================================================

        [Fact]
        public void CreateUser_ValidUser_ReturnsId()
        {
            // Arrange
            var user = new User
            {
                Name = "Alice",
                Email = "alice@example.com"
            };

            // Act
            int id = _repository.CreateUser(user);

            // Assert
            Assert.True(id > 0);
            _output.WriteLine($"Created user with ID: {id}");
        }

        // Dispose runs after each test
        public void Dispose()
        {
            _connection?.Close();
            _output.WriteLine("Test cleanup completed");
        }
    }
}
```

## With Class Fixture (Shared Setup)

```csharp
using Xunit;
using Database;

namespace Database.Tests
{
    // Fixture class - setup runs once for all tests
    public class DatabaseFixture : IDisposable
    {
        public DatabaseConnection Connection { get; private set; }

        public DatabaseFixture()
        {
            Connection = new DatabaseConnection("TestConnectionString");
            Connection.Open();
            Connection.SeedTestData();
        }

        public void Dispose()
        {
            Connection?.Close();
        }
    }

    /// <summary>
    /// Test suite for UserService.
    /// Uses shared database fixture for efficiency.
    /// </summary>
    public class UserServiceTests : IClassFixture<DatabaseFixture>
    {
        private readonly DatabaseFixture _fixture;
        private readonly UserService _service;

        public UserServiceTests(DatabaseFixture fixture)
        {
            _fixture = fixture;
            _service = new UserService(new UserRepository(_fixture.Connection));
        }

        [Fact]
        public void GetAllUsers_ReturnsAllUsers()
        {
            // Act
            var users = _service.GetAllUsers();

            // Assert
            Assert.NotEmpty(users);
            Assert.True(users.Count() > 0);
        }

        [Fact]
        public void GetUser_ExistingId_ReturnsUser()
        {
            // Act
            var user = _service.GetUser(1);

            // Assert
            Assert.NotNull(user);
            Assert.Equal(1, user.Id);
        }
    }
}
```

## Theory Tests (Parameterized)

```csharp
using Xunit;
using System.Collections.Generic;
using Calculator;

namespace Calculator.Tests
{
    public class CalculatorTheoryTests
    {
        // ====================================================================
        // Theory Tests with InlineData
        // ====================================================================

        [Theory]
        [InlineData(1, 2, 3)]
        [InlineData(5, 5, 10)]
        [InlineData(-1, 1, 0)]
        [InlineData(0, 0, 0)]
        [InlineData(100, 200, 300)]
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
        [InlineData(10, 2, 5)]
        [InlineData(9, 3, 3)]
        [InlineData(100, 10, 10)]
        public void Divide_VariousInputs_ReturnsExpectedQuotient(int dividend, int divisor, int expected)
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Divide(dividend, divisor);

            // Assert
            Assert.Equal(expected, result);
        }

        // ====================================================================
        // Theory Tests with MemberData
        // ====================================================================

        [Theory]
        [MemberData(nameof(MultiplicationTestData))]
        public void Multiply_VariousInputs_ReturnsExpectedProduct(int a, int b, int expected)
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Multiply(a, b);

            // Assert
            Assert.Equal(expected, result);
        }

        public static IEnumerable<object[]> MultiplicationTestData =>
            new List<object[]>
            {
                new object[] { 2, 3, 6 },
                new object[] { 5, 5, 25 },
                new object[] { -2, 3, -6 },
                new object[] { 0, 10, 0 }
            };

        // ====================================================================
        // Theory Tests with ClassData
        // ====================================================================

        [Theory]
        [ClassData(typeof(SubtractionTestData))]
        public void Subtract_VariousInputs_ReturnsExpectedDifference(int a, int b, int expected)
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Subtract(a, b);

            // Assert
            Assert.Equal(expected, result);
        }
    }

    public class SubtractionTestData : IEnumerable<object[]>
    {
        public IEnumerator<object[]> GetEnumerator()
        {
            yield return new object[] { 10, 3, 7 };
            yield return new object[] { 5, 5, 0 };
            yield return new object[] { 0, 5, -5 };
        }

        System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator() => GetEnumerator();
    }
}
```

## Async Tests

```csharp
using Xunit;
using System.Threading.Tasks;
using Api;

namespace Api.Tests
{
    /// <summary>
    /// Test suite for ApiClient.
    /// Tests asynchronous API operations.
    /// </summary>
    public class ApiClientTests
    {
        // ====================================================================
        // Async Tests
        // ====================================================================

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

        // ====================================================================
        // Async Error Tests
        // ====================================================================

        [Fact]
        public async Task GetUserAsync_NonExistentId_ThrowsNotFoundException()
        {
            // Arrange
            var client = new ApiClient("https://api.example.com");

            // Act & Assert
            await Assert.ThrowsAsync<NotFoundException>(() =>
                client.GetUserAsync(99999));
        }

        [Fact]
        public async Task DeleteUserAsync_Timeout_ThrowsTimeoutException()
        {
            // Arrange
            var client = new ApiClient("https://api.example.com")
            {
                Timeout = TimeSpan.FromMilliseconds(1)
            };

            // Act & Assert
            await Assert.ThrowsAsync<TimeoutException>(() =>
                client.DeleteUserAsync(1));
        }
    }
}
```

## Mocking with Moq

```csharp
using Xunit;
using Moq;
using Services;

namespace Services.Tests
{
    /// <summary>
    /// Test suite for UserService.
    /// Tests service layer with mocked dependencies.
    /// </summary>
    public class UserServiceTests
    {
        // ====================================================================
        // Tests with Mocked Repository
        // ====================================================================

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
            mockRepository.Verify(repo => repo.GetByIdAsync(1), Times.Once);
        }

        // ====================================================================
        // Tests with Mock Callbacks
        // ====================================================================

        [Fact]
        public void SaveUser_CallsRepositoryWithCorrectData()
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
    }
}
```

## Common xUnit Assertions

```csharp
// ====================================================================
// Equality Assertions
// ====================================================================

Assert.Equal(expected, actual);
Assert.NotEqual(expected, actual);
Assert.Same(expectedObject, actualObject);  // Reference equality
Assert.NotSame(expectedObject, actualObject);

// ====================================================================
// Null Assertions
// ====================================================================

Assert.Null(value);
Assert.NotNull(value);

// ====================================================================
// Boolean Assertions
// ====================================================================

Assert.True(condition);
Assert.False(condition);

// ====================================================================
// String Assertions
// ====================================================================

Assert.Equal("expected", actual);  // Exact match
Assert.StartsWith("prefix", actual);
Assert.EndsWith("suffix", actual);
Assert.Contains("substring", actual);
Assert.DoesNotContain("substring", actual);
Assert.Matches(@"\d{3}-\d{3}-\d{4}", phoneNumber);  // Regex

// ====================================================================
// Numeric Assertions
// ====================================================================

Assert.Equal(5, actual);
Assert.NotEqual(5, actual);
Assert.InRange(actual, low, high);
Assert.Equal(3.14159, actual, precision: 2);  // For doubles: 3.14 tolerance

// ====================================================================
// Collection Assertions
// ====================================================================

Assert.Empty(collection);
Assert.NotEmpty(collection);
Assert.Contains(item, collection);
Assert.DoesNotContain(item, collection);
Assert.All(collection, item => Assert.NotNull(item));
Assert.Collection(collection,
    item => Assert.Equal("first", item),
    item => Assert.Equal("second", item));

// ====================================================================
// Exception Assertions
// ====================================================================

Assert.Throws<ArgumentNullException>(() => method(null));
Assert.Throws<DivideByZeroException>(() => calculator.Divide(10, 0));
await Assert.ThrowsAsync<InvalidOperationException>(() => asyncMethod());

var exception = Assert.Throws<ArgumentException>(() => method(invalid));
Assert.Equal("paramName", exception.ParamName);
Assert.Contains("error message", exception.Message);

// ====================================================================
// Type Assertions
// ====================================================================

Assert.IsType<ExpectedType>(actual);
Assert.IsNotType<UnexpectedType>(actual);
Assert.IsAssignableFrom<BaseType>(actual);
```

## Test Organization Pattern

```csharp
public class {ClassName}Tests
{
    // ====================================================================
    // Constructor Tests
    // ====================================================================

    [Fact]
    public void Constructor_ValidArguments_CreatesInstance()
    {
        // Test implementation
    }

    // ====================================================================
    // Happy Path Tests
    // ====================================================================

    [Fact]
    public void Method_ValidInput_ReturnsExpectedResult()
    {
        // Test implementation
    }

    // ====================================================================
    // Edge Case Tests
    // ====================================================================

    [Fact]
    public void Method_EdgeCaseInput_HandlesCorrectly()
    {
        // Test implementation
    }

    // ====================================================================
    // Error Handling Tests
    // ====================================================================

    [Fact]
    public void Method_InvalidInput_ThrowsException()
    {
        // Test implementation
    }

    // ====================================================================
    // Integration Tests (if applicable)
    // ====================================================================

    [Fact]
    public void Method_WithDependencies_IntegratesCorrectly()
    {
        // Test implementation
    }
}
```

## Configuration

### .csproj Test Project

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
    <IsTestProject>true</IsTestProject>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.6.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.0">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="Moq" Version="4.20.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\Calculator\Calculator.csproj" />
  </ItemGroup>

</Project>
```

## References

- xUnit Documentation: https://xunit.net/
- xUnit Patterns: `skills/test-generation/csharp-patterns.md`
- Moq Documentation: https://github.com/moq/moq4
- .NET Testing: https://learn.microsoft.com/en-us/dotnet/core/testing/

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
