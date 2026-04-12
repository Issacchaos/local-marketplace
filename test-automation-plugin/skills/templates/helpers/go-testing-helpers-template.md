# Go Testing Helper Template

This template provides reusable test helper utilities for Go projects using the standard testing package and testify.

## Mock Creation Helpers

```go
package testhelpers

import (
    "github.com/stretchr/testify/mock"
)

// MockApiClient is a mock implementation of ApiClient
type MockApiClient struct {
    mock.Mock
}

func (m *MockApiClient) Get(path string) (interface{}, error) {
    args := m.Called(path)
    return args.Get(0), args.Error(1)
}

func (m *MockApiClient) Post(path string, data interface{}) (interface{}, error) {
    args := m.Called(path, data)
    return args.Get(0), args.Error(1)
}

func (m *MockApiClient) Put(path string, data interface{}) (interface{}, error) {
    args := m.Called(path, data)
    return args.Get(0), args.Error(1)
}

func (m *MockApiClient) Delete(path string) error {
    args := m.Called(path)
    return args.Error(0)
}

// CreateMockApiClient creates a mock API client with common default behaviors
func CreateMockApiClient() *MockApiClient {
    mockClient := new(MockApiClient)
    return mockClient
}

// MockDatabase is a mock implementation of Database
type MockDatabase struct {
    mock.Mock
}

func (m *MockDatabase) Connect() error {
    args := m.Called()
    return args.Error(0)
}

func (m *MockDatabase) Disconnect() error {
    args := m.Called()
    return args.Error(0)
}

func (m *MockDatabase) Query(sql string) ([]interface{}, error) {
    args := m.Called(sql)
    return args.Get(0).([]interface{}), args.Error(1)
}

func (m *MockDatabase) Execute(sql string) (int, error) {
    args := m.Called(sql)
    return args.Int(0), args.Error(1)
}

// CreateMockDatabase creates a mock database with common default behaviors
func CreateMockDatabase() *MockDatabase {
    mockDb := new(MockDatabase)
    mockDb.On("Connect").Return(nil)
    mockDb.On("Disconnect").Return(nil)
    return mockDb
}

// MockLogger is a mock implementation of Logger
type MockLogger struct {
    mock.Mock
}

func (m *MockLogger) Info(msg string) {
    m.Called(msg)
}

func (m *MockLogger) Warn(msg string) {
    m.Called(msg)
}

func (m *MockLogger) Error(msg string) {
    m.Called(msg)
}

func (m *MockLogger) Debug(msg string) {
    m.Called(msg)
}

// CreateMockLogger creates a mock logger with common default behaviors
func CreateMockLogger() *MockLogger {
    mockLogger := new(MockLogger)
    mockLogger.On("Info", mock.Anything).Return()
    mockLogger.On("Warn", mock.Anything).Return()
    mockLogger.On("Error", mock.Anything).Return()
    mockLogger.On("Debug", mock.Anything).Return()
    return mockLogger
}
```

## Test Data Builders

```go
package testhelpers

// User represents a test user entity
type User struct {
    ID    int
    Name  string
    Email string
    Age   int
    Role  string
}

// UserBuilder builds test User objects with default values
type UserBuilder struct {
    id    int
    name  string
    email string
    age   int
    role  string
}

// NewUserBuilder creates a new UserBuilder with default values
func NewUserBuilder() *UserBuilder {
    return &UserBuilder{
        id:    1,
        name:  "Test User",
        email: "test@example.com",
        age:   30,
        role:  "user",
    }
}

func (b *UserBuilder) WithID(id int) *UserBuilder {
    b.id = id
    return b
}

func (b *UserBuilder) WithName(name string) *UserBuilder {
    b.name = name
    return b
}

func (b *UserBuilder) WithEmail(email string) *UserBuilder {
    b.email = email
    return b
}

func (b *UserBuilder) WithAge(age int) *UserBuilder {
    b.age = age
    return b
}

func (b *UserBuilder) WithRole(role string) *UserBuilder {
    b.role = role
    return b
}

func (b *UserBuilder) Build() *User {
    return &User{
        ID:    b.id,
        Name:  b.name,
        Email: b.email,
        Age:   b.age,
        Role:  b.role,
    }
}

// BuildDefaultUser creates a user with all default values
func BuildDefaultUser() *User {
    return NewUserBuilder().Build()
}

// BuildUserList creates a list of test users with sequential IDs
func BuildUserList(count int) []*User {
    users := make([]*User, count)
    for i := 0; i < count; i++ {
        users[i] = NewUserBuilder().
            WithID(i + 1).
            WithName(fmt.Sprintf("User %d", i+1)).
            WithEmail(fmt.Sprintf("user%d@example.com", i+1)).
            Build()
    }
    return users
}

// Product represents a test product entity
type Product struct {
    ID       int
    Name     string
    Price    float64
    Category string
    InStock  bool
}

// ProductBuilder builds test Product objects with default values
type ProductBuilder struct {
    id       int
    name     string
    price    float64
    category string
    inStock  bool
}

// NewProductBuilder creates a new ProductBuilder with default values
func NewProductBuilder() *ProductBuilder {
    return &ProductBuilder{
        id:       1,
        name:     "Test Product",
        price:    99.99,
        category: "electronics",
        inStock:  true,
    }
}

func (b *ProductBuilder) WithID(id int) *ProductBuilder {
    b.id = id
    return b
}

func (b *ProductBuilder) WithName(name string) *ProductBuilder {
    b.name = name
    return b
}

func (b *ProductBuilder) WithPrice(price float64) *ProductBuilder {
    b.price = price
    return b
}

func (b *ProductBuilder) WithCategory(category string) *ProductBuilder {
    b.category = category
    return b
}

func (b *ProductBuilder) WithInStock(inStock bool) *ProductBuilder {
    b.inStock = inStock
    return b
}

func (b *ProductBuilder) Build() *Product {
    return &Product{
        ID:       b.id,
        Name:     b.name,
        Price:    b.price,
        Category: b.category,
        InStock:  b.inStock,
    }
}

// BuildDefaultProduct creates a product with all default values
func BuildDefaultProduct() *Product {
    return NewProductBuilder().Build()
}
```

## Setup and Teardown Utilities

```go
package testhelpers

import (
    "context"
    "testing"
    "time"
)

// TestEnvironment holds common test dependencies
type TestEnvironment struct {
    MockAPI    *MockApiClient
    MockDB     *MockDatabase
    MockLogger *MockLogger
}

// SetupTestEnvironment creates a test environment with common mocks
func SetupTestEnvironment(t *testing.T) *TestEnvironment {
    env := &TestEnvironment{
        MockAPI:    CreateMockApiClient(),
        MockDB:     CreateMockDatabase(),
        MockLogger: CreateMockLogger(),
    }

    // Cleanup function
    t.Cleanup(func() {
        env.MockAPI.AssertExpectations(t)
        env.MockDB.AssertExpectations(t)
        env.MockLogger.AssertExpectations(t)
    })

    return env
}

// WithTimeout runs a test function with a timeout
func WithTimeout(t *testing.T, timeout time.Duration, testFunc func()) {
    done := make(chan bool)
    go func() {
        testFunc()
        done <- true
    }()

    select {
    case <-done:
        // Test completed successfully
    case <-time.After(timeout):
        t.Fatal("Test timeout exceeded")
    }
}

// WithTestDatabase runs test code with a mock database connection
func WithTestDatabase(t *testing.T, testFunc func(db *MockDatabase)) {
    mockDB := CreateMockDatabase()
    err := mockDB.Connect()
    if err != nil {
        t.Fatalf("Failed to connect to test database: %v", err)
    }

    defer func() {
        err := mockDB.Disconnect()
        if err != nil {
            t.Errorf("Failed to disconnect from test database: %v", err)
        }
    }()

    testFunc(mockDB)
}

// WithContext creates a test context with timeout
func WithContext(t *testing.T, timeout time.Duration) (context.Context, context.CancelFunc) {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    t.Cleanup(cancel)
    return ctx, cancel
}
```

## Usage Examples

```go
package service_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "myapp/testhelpers"
)

func TestUserService_GetUserByID(t *testing.T) {
    // Arrange
    env := testhelpers.SetupTestEnvironment(t)
    testUser := testhelpers.NewUserBuilder().
        WithID(123).
        WithName("John Doe").
        Build()

    env.MockAPI.On("Get", "/users/123").Return(testUser, nil)

    service := NewUserService(env.MockAPI, env.MockLogger)

    // Act
    result, err := service.GetUserByID(123)

    // Assert
    assert.NoError(t, err)
    assert.Equal(t, testUser, result)
    env.MockAPI.AssertCalled(t, "Get", "/users/123")
}

func TestUserService_CreateUser(t *testing.T) {
    // Arrange
    env := testhelpers.SetupTestEnvironment(t)
    newUser := testhelpers.NewUserBuilder().
        WithID(0).
        WithName("Jane Doe").
        Build()

    createdUser := testhelpers.NewUserBuilder().
        WithID(456).
        WithName("Jane Doe").
        Build()

    env.MockAPI.On("Post", "/users", mock.Anything).Return(createdUser, nil)
    env.MockLogger.On("Info", mock.Anything).Return()

    service := NewUserService(env.MockAPI, env.MockLogger)

    // Act
    result, err := service.CreateUser(newUser)

    // Assert
    assert.NoError(t, err)
    assert.Equal(t, 456, result.ID)
    env.MockAPI.AssertCalled(t, "Post", "/users", mock.Anything)
    env.MockLogger.AssertCalled(t, "Info", mock.Anything)
}

func TestUserService_GetAllUsers(t *testing.T) {
    // Arrange
    env := testhelpers.SetupTestEnvironment(t)
    users := testhelpers.BuildUserList(3)

    env.MockAPI.On("Get", "/users").Return(users, nil)

    service := NewUserService(env.MockAPI, env.MockLogger)

    // Act
    result, err := service.GetAllUsers()

    // Assert
    assert.NoError(t, err)
    assert.Len(t, result, 3)
    env.MockAPI.AssertCalled(t, "Get", "/users")
}

func TestUserService_WithTimeout(t *testing.T) {
    // Arrange
    env := testhelpers.SetupTestEnvironment(t)
    testUser := testhelpers.BuildDefaultUser()

    env.MockAPI.On("Get", mock.Anything).Return(testUser, nil)

    service := NewUserService(env.MockAPI, env.MockLogger)

    // Act & Assert
    testhelpers.WithTimeout(t, 1*time.Second, func() {
        result, err := service.GetUserByID(1)
        assert.NoError(t, err)
        assert.NotNil(t, result)
    })
}
```
