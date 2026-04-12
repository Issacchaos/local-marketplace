# C# NUnit Test Template

**Purpose**: Template for generating NUnit test files for C# projects
**Target Language**: C#
**Test Framework**: NUnit 3.x
**Version Support**: NUnit 3.13.0+, .NET 6.0+

## C# Language Features

### File-Scoped Namespaces (C# 10+)

For **.NET 6+** projects, use **file-scoped namespaces** to reduce indentation:

```csharp
namespace Calculator.Tests;  // Semicolon instead of braces

[TestFixture]
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

**Traditional Style (C# 9 and earlier)**:
```csharp
namespace Calculator.Tests
{
    [TestFixture]
    public class CalculatorTests
    {
        // Tests here - two levels of indentation
    }
}
```

---

## Template Structure

```csharp
using NUnit.Framework;
{ADDITIONAL_USINGS}

namespace {NAMESPACE}.Tests
{
    /// <summary>
    /// Test suite for {CLASS_NAME}.
    /// {SUITE_DESCRIPTION}
    /// </summary>
    [TestFixture]
    public class {CLASS_NAME}Tests
    {
        {SETUP_METHOD}
        {TEARDOWN_METHOD}

        {TEST_METHODS}
    }
}
```

## Basic NUnit Test Template

```csharp
using NUnit.Framework;
using Calculator;

namespace Calculator.Tests
{
    /// <summary>
    /// Test suite for Calculator class.
    /// Tests basic arithmetic operations and error handling.
    /// </summary>
    [TestFixture]
    public class CalculatorTests
    {
        private Calculator _calculator;

        [SetUp]
        public void Setup()
        {
            _calculator = new Calculator();
        }

        [TearDown]
        public void TearDown()
        {
            _calculator = null;
        }

        // ====================================================================
        // Happy Path Tests
        // ====================================================================

        [Test]
        public void Add_TwoPositiveNumbers_ReturnsSum()
        {
            // Arrange
            int a = 5;
            int b = 3;

            // Act
            int result = _calculator.Add(a, b);

            // Assert
            Assert.AreEqual(8, result);
        }

        [Test]
        public void Subtract_TwoNumbers_ReturnsDifference()
        {
            // Arrange
            int a = 10;
            int b = 3;

            // Act
            int result = _calculator.Subtract(a, b);

            // Assert
            Assert.AreEqual(7, result);
        }

        // ====================================================================
        // Edge Case Tests
        // ====================================================================

        [Test]
        public void Add_WithZero_ReturnsOtherNumber()
        {
            // Arrange - Setup already done in SetUp method

            // Act
            int result = _calculator.Add(5, 0);

            // Assert
            Assert.AreEqual(5, result);
        }

        // ====================================================================
        // Error Handling Tests
        // ====================================================================

        [Test]
        public void Divide_ByZero_ThrowsDivideByZeroException()
        {
            // Arrange - Calculator already initialized

            // Act & Assert
            Assert.Throws<DivideByZeroException>(() => _calculator.Divide(10, 0));
        }
    }
}
```

## With OneTimeSetUp (Class-Level Setup)

```csharp
using NUnit.Framework;
using Database;

namespace Database.Tests
{
    /// <summary>
    /// Test suite for UserRepository.
    /// Tests CRUD operations with database connection management.
    /// </summary>
    [TestFixture]
    public class UserRepositoryTests
    {
        private static DatabaseConnection _connection;
        private UserRepository _repository;

        [OneTimeSetUp]
        public void OneTimeSetup()
        {
            // Runs once before all tests in this fixture
            _connection = new DatabaseConnection("TestConnectionString");
            _connection.Open();
            _connection.SeedTestData();
            TestContext.WriteLine("Database connection opened and seeded");
        }

        [SetUp]
        public void Setup()
        {
            // Runs before each test
            _repository = new UserRepository(_connection);
        }

        [TearDown]
        public void TearDown()
        {
            // Runs after each test
            _repository = null;
        }

        [OneTimeTearDown]
        public void OneTimeTearDown()
        {
            // Runs once after all tests in this fixture
            _connection?.Close();
            TestContext.WriteLine("Database connection closed");
        }

        // ====================================================================
        // Read Tests
        // ====================================================================

        [Test]
        public void GetUser_ExistingId_ReturnsUser()
        {
            // Arrange
            int userId = 1;

            // Act
            var user = _repository.GetUser(userId);

            // Assert
            Assert.IsNotNull(user);
            Assert.AreEqual(userId, user.Id);
            TestContext.WriteLine($"Retrieved user: {user.Name}");
        }

        // ====================================================================
        // Create Tests
        // ====================================================================

        [Test]
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
            Assert.Greater(id, 0);
            TestContext.WriteLine($"Created user with ID: {id}");
        }
    }
}
```

## TestCase Tests (Parameterized)

```csharp
using NUnit.Framework;
using Calculator;

namespace Calculator.Tests
{
    [TestFixture]
    public class CalculatorTestCaseTests
    {
        private Calculator _calculator;

        [SetUp]
        public void Setup()
        {
            _calculator = new Calculator();
        }

        // ====================================================================
        // TestCase Tests with Multiple Parameters
        // ====================================================================

        [TestCase(1, 2, 3)]
        [TestCase(5, 5, 10)]
        [TestCase(-1, 1, 0)]
        [TestCase(0, 0, 0)]
        [TestCase(100, 200, 300)]
        public void Add_VariousInputs_ReturnsExpectedSum(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Add(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }

        [TestCase(10, 2, 5)]
        [TestCase(9, 3, 3)]
        [TestCase(100, 10, 10)]
        public void Divide_VariousInputs_ReturnsExpectedQuotient(int dividend, int divisor, int expected)
        {
            // Act
            int result = _calculator.Divide(dividend, divisor);

            // Assert
            Assert.AreEqual(expected, result);
        }

        // ====================================================================
        // TestCase with ExpectedResult
        // ====================================================================

        [TestCase(2, 3, ExpectedResult = 6)]
        [TestCase(5, 5, ExpectedResult = 25)]
        [TestCase(-2, 3, ExpectedResult = -6)]
        [TestCase(0, 10, ExpectedResult = 0)]
        public int Multiply_VariousInputs_ReturnsExpectedProduct(int a, int b)
        {
            // Act & Assert (return value is compared to ExpectedResult)
            return _calculator.Multiply(a, b);
        }

        // ====================================================================
        // TestCase with TestName
        // ====================================================================

        [TestCase(10, 3, 7, TestName = "Subtract 3 from 10")]
        [TestCase(5, 5, 0, TestName = "Subtract 5 from 5")]
        [TestCase(0, 5, -5, TestName = "Subtract 5 from 0")]
        public void Subtract_VariousInputs_ReturnsExpectedDifference(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Subtract(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }
    }
}
```

## TestCaseSource Tests (Advanced Parameterization)

```csharp
using NUnit.Framework;
using System.Collections;
using Calculator;

namespace Calculator.Tests
{
    [TestFixture]
    public class CalculatorTestCaseSourceTests
    {
        private Calculator _calculator;

        [SetUp]
        public void Setup()
        {
            _calculator = new Calculator();
        }

        // ====================================================================
        // TestCaseSource with Static Method
        // ====================================================================

        [TestCaseSource(nameof(AdditionTestCases))]
        public void Add_TestCaseSource_ReturnsExpectedSum(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Add(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }

        private static IEnumerable AdditionTestCases
        {
            get
            {
                yield return new TestCaseData(1, 2, 3).SetName("Add 1 and 2");
                yield return new TestCaseData(5, 5, 10).SetName("Add 5 and 5");
                yield return new TestCaseData(-1, 1, 0).SetName("Add -1 and 1");
            }
        }

        // ====================================================================
        // TestCaseSource with Separate Class
        // ====================================================================

        [TestCaseSource(typeof(DivisionTestData), nameof(DivisionTestData.TestCases))]
        public void Divide_TestCaseSource_ReturnsExpectedQuotient(int dividend, int divisor, int expected)
        {
            // Act
            int result = _calculator.Divide(dividend, divisor);

            // Assert
            Assert.AreEqual(expected, result);
        }
    }

    public class DivisionTestData
    {
        public static IEnumerable TestCases
        {
            get
            {
                yield return new TestCaseData(10, 2, 5);
                yield return new TestCaseData(9, 3, 3);
                yield return new TestCaseData(100, 10, 10);
            }
        }
    }
}
```

## Async Tests

```csharp
using NUnit.Framework;
using System.Threading.Tasks;
using Api;

namespace Api.Tests
{
    /// <summary>
    /// Test suite for ApiClient.
    /// Tests asynchronous API operations.
    /// </summary>
    [TestFixture]
    public class ApiClientTests
    {
        private ApiClient _client;

        [SetUp]
        public void Setup()
        {
            _client = new ApiClient("https://api.example.com");
        }

        // ====================================================================
        // Async Tests
        // ====================================================================

        [Test]
        public async Task GetUserAsync_ValidId_ReturnsUser()
        {
            // Arrange
            int userId = 1;

            // Act
            User user = await _client.GetUserAsync(userId);

            // Assert
            Assert.IsNotNull(user);
            Assert.AreEqual(userId, user.Id);
        }

        [Test]
        public async Task CreateUserAsync_ValidUser_ReturnsCreatedUser()
        {
            // Arrange
            var newUser = new User
            {
                Name = "Alice",
                Email = "alice@example.com"
            };

            // Act
            User createdUser = await _client.CreateUserAsync(newUser);

            // Assert
            Assert.IsNotNull(createdUser);
            Assert.Greater(createdUser.Id, 0);
            Assert.AreEqual("Alice", createdUser.Name);
        }

        // ====================================================================
        // Async Error Tests
        // ====================================================================

        [Test]
        public void GetUserAsync_NonExistentId_ThrowsNotFoundException()
        {
            // Act & Assert
            Assert.ThrowsAsync<NotFoundException>(async () =>
                await _client.GetUserAsync(99999));
        }

        [Test]
        public void DeleteUserAsync_Timeout_ThrowsTimeoutException()
        {
            // Arrange
            _client.Timeout = TimeSpan.FromMilliseconds(1);

            // Act & Assert
            Assert.ThrowsAsync<TimeoutException>(async () =>
                await _client.DeleteUserAsync(1));
        }
    }
}
```

## Mocking with Moq

```csharp
using NUnit.Framework;
using Moq;
using Services;

namespace Services.Tests
{
    /// <summary>
    /// Test suite for UserService.
    /// Tests service layer with mocked dependencies.
    /// </summary>
    [TestFixture]
    public class UserServiceTests
    {
        private Mock<IUserRepository> _mockRepository;
        private UserService _service;

        [SetUp]
        public void Setup()
        {
            _mockRepository = new Mock<IUserRepository>();
            _service = new UserService(_mockRepository.Object);
        }

        // ====================================================================
        // Tests with Mocked Repository
        // ====================================================================

        [Test]
        public void GetUser_CallsRepository_ReturnsUser()
        {
            // Arrange
            _mockRepository
                .Setup(repo => repo.GetById(1))
                .Returns(new User { Id = 1, Name = "Alice" });

            // Act
            var user = _service.GetUser(1);

            // Assert
            Assert.IsNotNull(user);
            Assert.AreEqual("Alice", user.Name);
            _mockRepository.Verify(repo => repo.GetById(1), Times.Once);
        }

        [Test]
        public void SaveUser_CallsRepository_SavesUser()
        {
            // Arrange
            var user = new User { Id = 1, Name = "Alice" };

            // Act
            _service.SaveUser(user);

            // Assert
            _mockRepository.Verify(
                repo => repo.Save(It.Is<User>(u => u.Id == 1 && u.Name == "Alice")),
                Times.Once);
        }

        [Test]
        public async Task GetUserAsync_CallsRepository_ReturnsUser()
        {
            // Arrange
            _mockRepository
                .Setup(repo => repo.GetByIdAsync(1))
                .ReturnsAsync(new User { Id = 1, Name = "Alice" });

            // Act
            var user = await _service.GetUserAsync(1);

            // Assert
            Assert.IsNotNull(user);
            Assert.AreEqual("Alice", user.Name);
            _mockRepository.Verify(repo => repo.GetByIdAsync(1), Times.Once);
        }

        // ====================================================================
        // Tests with Mock Callbacks
        // ====================================================================

        [Test]
        public void SaveUser_CallsRepositoryWithCorrectData()
        {
            // Arrange
            User? savedUser = null;

            _mockRepository
                .Setup(repo => repo.Save(It.IsAny<User>()))
                .Callback<User>(user => savedUser = user);

            var user = new User { Id = 1, Name = "Alice" };

            // Act
            _service.SaveUser(user);

            // Assert
            Assert.IsNotNull(savedUser);
            Assert.AreEqual(1, savedUser.Id);
            Assert.AreEqual("Alice", savedUser.Name);
        }
    }
}
```

## Common NUnit Assertions

```csharp
// ====================================================================
// Equality Assertions
// ====================================================================

Assert.AreEqual(expected, actual);
Assert.AreNotEqual(expected, actual);
Assert.AreSame(expectedObject, actualObject);  // Reference equality
Assert.AreNotSame(expectedObject, actualObject);

// ====================================================================
// Null Assertions
// ====================================================================

Assert.IsNull(value);
Assert.IsNotNull(value);

// ====================================================================
// Boolean Assertions
// ====================================================================

Assert.IsTrue(condition);
Assert.IsFalse(condition);

// ====================================================================
// String Assertions
// ====================================================================

Assert.AreEqual("expected", actual);
Assert.That(actual, Does.StartWith("prefix"));
Assert.That(actual, Does.EndWith("suffix"));
Assert.That(actual, Does.Contain("substring"));
Assert.That(actual, Does.Not.Contain("substring"));
Assert.That(actual, Does.Match(@"\d{3}-\d{3}-\d{4}"));  // Regex

// ====================================================================
// Numeric Assertions
// ====================================================================

Assert.AreEqual(5, actual);
Assert.AreNotEqual(5, actual);
Assert.Greater(actual, 5);
Assert.GreaterOrEqual(actual, 5);
Assert.Less(actual, 10);
Assert.LessOrEqual(actual, 10);
Assert.That(actual, Is.InRange(1, 10));
Assert.AreEqual(3.14159, actual, 0.01);  // Delta tolerance for doubles

// ====================================================================
// Collection Assertions
// ====================================================================

Assert.IsEmpty(collection);
Assert.IsNotEmpty(collection);
Assert.Contains(item, collection);
Assert.That(collection, Has.Member(item));
Assert.That(collection, Has.No.Member(item));
Assert.That(collection, Has.All.Not.Null);
Assert.That(collection, Has.Count.EqualTo(3));
Assert.That(collection, Is.Ordered);

// ====================================================================
// Exception Assertions
// ====================================================================

Assert.Throws<ArgumentNullException>(() => method(null));
Assert.Throws<DivideByZeroException>(() => calculator.Divide(10, 0));
Assert.ThrowsAsync<InvalidOperationException>(async () => await asyncMethod());

var exception = Assert.Throws<ArgumentException>(() => method(invalid));
Assert.AreEqual("paramName", exception.ParamName);
Assert.That(exception.Message, Does.Contain("error message"));

// ====================================================================
// Type Assertions
// ====================================================================

Assert.IsInstanceOf<ExpectedType>(actual);
Assert.IsNotInstanceOf<UnexpectedType>(actual);
Assert.IsAssignableFrom<BaseType>(actual);

// ====================================================================
// Constraint-Based Assertions (NUnit 3+ style)
// ====================================================================

Assert.That(actual, Is.EqualTo(expected));
Assert.That(actual, Is.Not.EqualTo(unexpected));
Assert.That(actual, Is.Null);
Assert.That(actual, Is.Not.Null);
Assert.That(actual, Is.GreaterThan(5));
Assert.That(collection, Has.Some.EqualTo(item));
```

## Test Organization Pattern

```csharp
[TestFixture]
public class {ClassName}Tests
{
    private {ClassName} _sut;  // System Under Test

    [SetUp]
    public void Setup()
    {
        _sut = new {ClassName}();
    }

    [TearDown]
    public void TearDown()
    {
        _sut = null;
    }

    // ====================================================================
    // Constructor Tests
    // ====================================================================

    [Test]
    public void Constructor_ValidArguments_CreatesInstance()
    {
        // Test implementation
    }

    // ====================================================================
    // Happy Path Tests
    // ====================================================================

    [Test]
    public void Method_ValidInput_ReturnsExpectedResult()
    {
        // Test implementation
    }

    // ====================================================================
    // Edge Case Tests
    // ====================================================================

    [Test]
    public void Method_EdgeCaseInput_HandlesCorrectly()
    {
        // Test implementation
    }

    // ====================================================================
    // Error Handling Tests
    // ====================================================================

    [Test]
    public void Method_InvalidInput_ThrowsException()
    {
        // Test implementation
    }
}
```

## Test Categories

```csharp
[TestFixture]
public class DatabaseTests
{
    [Test]
    [Category("Integration")]
    public void SaveData_ValidData_SavesSuccessfully()
    {
        // Test implementation
    }

    [Test]
    [Category("Unit")]
    [Category("FastTest")]
    public void ValidateData_ValidInput_ReturnsTrue()
    {
        // Test implementation
    }

    [Test]
    [Category("Slow")]
    [Explicit("Requires external API")]
    public void CallExternalApi_ValidRequest_ReturnsData()
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
    <PackageReference Include="NUnit" Version="3.14.0" />
    <PackageReference Include="NUnit3TestAdapter" Version="4.5.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="Moq" Version="4.20.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\Calculator\Calculator.csproj" />
  </ItemGroup>

</Project>
```

## References

- NUnit Documentation: https://docs.nunit.org/
- NUnit Patterns: `skills/test-generation/csharp-patterns.md`
- Moq Documentation: https://github.com/moq/moq4
- .NET Testing: https://learn.microsoft.com/en-us/dotnet/core/testing/

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
