# C# MSTest Test Template

**Purpose**: Template for generating MSTest test files for C# projects
**Target Language**: C#
**Test Framework**: MSTest (Microsoft.VisualStudio.TestTools.UnitTesting)
**Version Support**: MSTest 3.x, .NET 6.0+

## Template Structure

### Modern Style (C# 10+ with File-Scoped Namespace)

**Recommended for .NET 6+ projects**

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
{ADDITIONAL_USINGS}

namespace {NAMESPACE}.Tests;

/// <summary>
/// Test suite for {CLASS_NAME}.
/// {SUITE_DESCRIPTION}
/// </summary>
[TestClass]
public class {CLASS_NAME}Tests
{
    {TEST_INITIALIZE_METHOD}
    {TEST_CLEANUP_METHOD}

    {TEST_METHODS}
}
```

### Traditional Style (C# 9 and earlier)

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
{ADDITIONAL_USINGS}

namespace {NAMESPACE}.Tests
{
    /// <summary>
    /// Test suite for {CLASS_NAME}.
    /// {SUITE_DESCRIPTION}
    /// </summary>
    [TestClass]
    public class {CLASS_NAME}Tests
    {
        {TEST_INITIALIZE_METHOD}
        {TEST_CLEANUP_METHOD}

        {TEST_METHODS}
    }
}
```

**Note**: Use file-scoped namespaces (`;` instead of `{}`) for new test projects targeting .NET 6+. This reduces indentation and is the modern C# convention.

## Basic MSTest Test Template

**Modern Style (Recommended for .NET 6+)**

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Calculator;

namespace Calculator.Tests;

/// <summary>
/// Test suite for Calculator class.
/// Tests basic arithmetic operations and error handling.
/// </summary>
[TestClass]
public class CalculatorTests
{
    private Calculator _calculator;

    [TestInitialize]
    public void Initialize()
    {
        _calculator = new Calculator();
    }

    [TestCleanup]
    public void Cleanup()
    {
        _calculator = null;
    }

    // ====================================================================
    // Happy Path Tests
    // ====================================================================

    [TestMethod]
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

    [TestMethod]
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

    [TestMethod]
    public void Add_WithZero_ReturnsOtherNumber()
    {
        // Arrange - Setup already done in TestInitialize

        // Act
        int result = _calculator.Add(5, 0);

        // Assert
        Assert.AreEqual(5, result);
    }

    // ====================================================================
    // Error Handling Tests
    // ====================================================================

    [TestMethod]
    [ExpectedException(typeof(DivideByZeroException))]
    public void Divide_ByZero_ThrowsDivideByZeroException()
    {
        // Arrange - Calculator already initialized

        // Act - Exception expected
        _calculator.Divide(10, 0);
    }

    [TestMethod]
    public void Divide_ByZero_ThrowsDivideByZeroException_AssertThrows()
    {
        // Arrange
        // Calculator already initialized

        // Act & Assert (modern style)
        Assert.ThrowsException<DivideByZeroException>(() => _calculator.Divide(10, 0));
    }
}
```

## With ClassInitialize (Class-Level Setup)

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Database;

namespace Database.Tests;
{
    /// <summary>
    /// Test suite for UserRepository.
    /// Tests CRUD operations with database connection management.
    /// </summary>
    [TestClass]
    public class UserRepositoryTests
    {
        private static DatabaseConnection _connection;
        private UserRepository _repository;
        private TestContext _testContext;

        public TestContext TestContext
        {
            get => _testContext;
            set => _testContext = value;
        }

        [ClassInitialize]
        public static void ClassInitialize(TestContext context)
        {
            // Runs once before all tests in this class
            _connection = new DatabaseConnection("TestConnectionString");
            _connection.Open();
            _connection.SeedTestData();
            context.WriteLine("Database connection opened and seeded");
        }

        [TestInitialize]
        public void Initialize()
        {
            // Runs before each test
            _repository = new UserRepository(_connection);
        }

        [TestCleanup]
        public void Cleanup()
        {
            // Runs after each test
            _repository = null;
        }

        [ClassCleanup]
        public static void ClassCleanup()
        {
            // Runs once after all tests in this class
            _connection?.Close();
        }

        // ====================================================================
        // Read Tests
        // ====================================================================

        [TestMethod]
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

        [TestMethod]
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
            Assert.IsTrue(id > 0);
            TestContext.WriteLine($"Created user with ID: {id}");
        }
    }
}
```

## DataRow Tests (Parameterized)

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Calculator;

namespace Calculator.Tests;
{
    [TestClass]
    public class CalculatorDataRowTests
    {
        private Calculator _calculator;

        [TestInitialize]
        public void Initialize()
        {
            _calculator = new Calculator();
        }

        // ====================================================================
        // DataRow Tests with Multiple Parameters
        // ====================================================================

        [DataTestMethod]
        [DataRow(1, 2, 3)]
        [DataRow(5, 5, 10)]
        [DataRow(-1, 1, 0)]
        [DataRow(0, 0, 0)]
        [DataRow(100, 200, 300)]
        public void Add_VariousInputs_ReturnsExpectedSum(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Add(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }

        [DataTestMethod]
        [DataRow(10, 2, 5)]
        [DataRow(9, 3, 3)]
        [DataRow(100, 10, 10)]
        public void Divide_VariousInputs_ReturnsExpectedQuotient(int dividend, int divisor, int expected)
        {
            // Act
            int result = _calculator.Divide(dividend, divisor);

            // Assert
            Assert.AreEqual(expected, result);
        }

        // ====================================================================
        // DataRow with DisplayName
        // ====================================================================

        [DataTestMethod]
        [DataRow(2, 3, 6, DisplayName = "Multiply 2 by 3")]
        [DataRow(5, 5, 25, DisplayName = "Multiply 5 by 5")]
        [DataRow(-2, 3, -6, DisplayName = "Multiply -2 by 3")]
        [DataRow(0, 10, 0, DisplayName = "Multiply 0 by 10")]
        public void Multiply_VariousInputs_ReturnsExpectedProduct(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Multiply(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }
    }
}
```

## DynamicData Tests (Advanced Parameterization)

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Collections.Generic;
using Calculator;

namespace Calculator.Tests;
{
    [TestClass]
    public class CalculatorDynamicDataTests
    {
        private Calculator _calculator;

        [TestInitialize]
        public void Initialize()
        {
            _calculator = new Calculator();
        }

        // ====================================================================
        // DynamicData with Static Method
        // ====================================================================

        [DataTestMethod]
        [DynamicData(nameof(GetAdditionTestData), DynamicDataSourceType.Method)]
        public void Add_DynamicData_ReturnsExpectedSum(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Add(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }

        private static IEnumerable<object[]> GetAdditionTestData()
        {
            yield return new object[] { 1, 2, 3 };
            yield return new object[] { 5, 5, 10 };
            yield return new object[] { -1, 1, 0 };
        }

        // ====================================================================
        // DynamicData with Static Property
        // ====================================================================

        [DataTestMethod]
        [DynamicData(nameof(SubtractionTestData), DynamicDataSourceType.Property)]
        public void Subtract_DynamicData_ReturnsExpectedDifference(int a, int b, int expected)
        {
            // Act
            int result = _calculator.Subtract(a, b);

            // Assert
            Assert.AreEqual(expected, result);
        }

        public static IEnumerable<object[]> SubtractionTestData
        {
            get
            {
                yield return new object[] { 10, 3, 7 };
                yield return new object[] { 5, 5, 0 };
                yield return new object[] { 0, 5, -5 };
            }
        }
    }
}
```

## Async Tests

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Threading.Tasks;
using Api;

namespace Api.Tests;
{
    /// <summary>
    /// Test suite for ApiClient.
    /// Tests asynchronous API operations.
    /// </summary>
    [TestClass]
    public class ApiClientTests
    {
        private ApiClient _client;

        [TestInitialize]
        public void Initialize()
        {
            _client = new ApiClient("https://api.example.com");
        }

        // ====================================================================
        // Async Tests
        // ====================================================================

        [TestMethod]
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

        [TestMethod]
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
            Assert.IsTrue(createdUser.Id > 0);
            Assert.AreEqual("Alice", createdUser.Name);
        }

        // ====================================================================
        // Async Error Tests
        // ====================================================================

        [TestMethod]
        [ExpectedException(typeof(NotFoundException))]
        public async Task GetUserAsync_NonExistentId_ThrowsNotFoundException()
        {
            // Act - Exception expected
            await _client.GetUserAsync(99999);
        }

        [TestMethod]
        public async Task GetUserAsync_NonExistentId_ThrowsNotFoundException_AssertThrows()
        {
            // Act & Assert (modern style)
            await Assert.ThrowsExceptionAsync<NotFoundException>(async () =>
                await _client.GetUserAsync(99999));
        }

        [TestMethod]
        public async Task DeleteUserAsync_Timeout_ThrowsTimeoutException()
        {
            // Arrange
            _client.Timeout = TimeSpan.FromMilliseconds(1);

            // Act & Assert
            await Assert.ThrowsExceptionAsync<TimeoutException>(async () =>
                await _client.DeleteUserAsync(1));
        }
    }
}
```

## Mocking with Moq

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;
using Services;

namespace Services.Tests;
{
    /// <summary>
    /// Test suite for UserService.
    /// Tests service layer with mocked dependencies.
    /// </summary>
    [TestClass]
    public class UserServiceTests
    {
        private Mock<IUserRepository> _mockRepository;
        private UserService _service;

        [TestInitialize]
        public void Initialize()
        {
            _mockRepository = new Mock<IUserRepository>();
            _service = new UserService(_mockRepository.Object);
        }

        // ====================================================================
        // Tests with Mocked Repository
        // ====================================================================

        [TestMethod]
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

        [TestMethod]
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

        [TestMethod]
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

        [TestMethod]
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

## Common MSTest Assertions

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
StringAssert.StartsWith(actual, "prefix");
StringAssert.EndsWith(actual, "suffix");
StringAssert.Contains(actual, "substring");
StringAssert.DoesNotMatch(actual, "substring");
StringAssert.Matches(actual, new Regex(@"\d{3}-\d{3}-\d{4}"));

// ====================================================================
// Numeric Assertions
// ====================================================================

Assert.AreEqual(5, actual);
Assert.AreNotEqual(5, actual);
Assert.AreEqual(3.14159, actual, 0.01);  // Delta tolerance for doubles

// ====================================================================
// Collection Assertions
// ====================================================================

CollectionAssert.AreEqual(expectedCollection, actualCollection);
CollectionAssert.AreNotEqual(expectedCollection, actualCollection);
CollectionAssert.Contains(collection, item);
CollectionAssert.DoesNotContain(collection, item);
CollectionAssert.AllItemsAreNotNull(collection);
CollectionAssert.AllItemsAreUnique(collection);
CollectionAssert.AllItemsAreInstancesOfType(collection, typeof(ExpectedType));

// ====================================================================
// Exception Assertions
// ====================================================================

// Old style (ExpectedException attribute)
[ExpectedException(typeof(ArgumentNullException))]
public void Method_NullArg_ThrowsException()
{
    method(null);
}

// Modern style (Assert.ThrowsException)
Assert.ThrowsException<ArgumentNullException>(() => method(null));
Assert.ThrowsExceptionAsync<InvalidOperationException>(async () => await asyncMethod());

var exception = Assert.ThrowsException<ArgumentException>(() => method(invalid));
Assert.AreEqual("paramName", exception.ParamName);
StringAssert.Contains(exception.Message, "error message");

// ====================================================================
// Type Assertions
// ====================================================================

Assert.IsInstanceOfType(actual, typeof(ExpectedType));
Assert.IsNotInstanceOfType(actual, typeof(UnexpectedType));
```

## Test Organization Pattern

```csharp
[TestClass]
public class {ClassName}Tests
{
    private {ClassName} _sut;  // System Under Test

    [TestInitialize]
    public void Initialize()
    {
        _sut = new {ClassName}();
    }

    [TestCleanup]
    public void Cleanup()
    {
        _sut = null;
    }

    // ====================================================================
    // Constructor Tests
    // ====================================================================

    [TestMethod]
    public void Constructor_ValidArguments_CreatesInstance()
    {
        // Test implementation
    }

    // ====================================================================
    // Happy Path Tests
    // ====================================================================

    [TestMethod]
    public void Method_ValidInput_ReturnsExpectedResult()
    {
        // Test implementation
    }

    // ====================================================================
    // Edge Case Tests
    // ====================================================================

    [TestMethod]
    public void Method_EdgeCaseInput_HandlesCorrectly()
    {
        // Test implementation
    }

    // ====================================================================
    // Error Handling Tests
    // ====================================================================

    [TestMethod]
    [ExpectedException(typeof(InvalidOperationException))]
    public void Method_InvalidInput_ThrowsException()
    {
        // Test implementation
    }
}
```

## Test Categories and Priorities

```csharp
[TestClass]
public class DatabaseTests
{
    [TestMethod]
    [TestCategory("Integration")]
    [Priority(1)]
    public void SaveData_ValidData_SavesSuccessfully()
    {
        // Test implementation
    }

    [TestMethod]
    [TestCategory("Unit")]
    [TestCategory("FastTest")]
    [Priority(0)]
    public void ValidateData_ValidInput_ReturnsTrue()
    {
        // Test implementation
    }

    [TestMethod]
    [TestCategory("Slow")]
    [Priority(2)]
    [Ignore("Requires external API")]
    public void CallExternalApi_ValidRequest_ReturnsData()
    {
        // Test implementation
    }

    [TestMethod]
    [Owner("Alice")]
    [Description("Tests that user creation works with valid data")]
    public void CreateUser_ValidData_ReturnsUserId()
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
    <PackageReference Include="MSTest.TestFramework" Version="3.1.0" />
    <PackageReference Include="MSTest.TestAdapter" Version="3.1.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="Moq" Version="4.20.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\Calculator\Calculator.csproj" />
  </ItemGroup>

</Project>
```

## References

- MSTest Documentation: https://docs.microsoft.com/en-us/dotnet/core/testing/unit-testing-with-mstest
- MSTest Patterns: `skills/test-generation/csharp-patterns.md`
- Moq Documentation: https://github.com/moq/moq4
- .NET Testing: https://learn.microsoft.com/en-us/dotnet/core/testing/

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
