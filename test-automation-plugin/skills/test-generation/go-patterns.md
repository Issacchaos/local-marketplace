# Go Test Generation Patterns

**Version**: 1.0.0
**Language**: Go
**Frameworks**: testing (built-in), testify
**Status**: Phase 4 - Systems Languages

## Overview

Comprehensive patterns and best practices for generating idiomatic Go tests. This skill covers Go's built-in testing package patterns, table-driven tests, subtests, benchmarks, examples, and testify integration.

## Core Go Testing Principles

### 1. Test File Naming

```go
// Source file
calculator.go          →  package calculator

// Test file (same directory)
calculator_test.go     →  package calculator (white-box)
                      OR  package calculator_test (black-box)
```

### 2. Test Function Signature

```go
func TestFunctionName(t *testing.T) {
    // Test implementation
}
```

**Naming Convention**: `Test + FunctionName + Scenario`

Examples:
- `TestAdd`
- `TestAdd_PositiveNumbers`
- `TestDivide_ByZero_ReturnsError`

### 3. Test Organization (AAA Pattern)

```go
func TestAdd(t *testing.T) {
    // Arrange - setup
    a := 2
    b := 3
    expected := 5

    // Act - execute
    result := Add(a, b)

    // Assert - verify
    if result != expected {
        t.Errorf("Add(%d, %d) = %d; want %d", a, b, result, expected)
    }
}
```

## Table-Driven Test Patterns

### Pattern 1: Basic Table-Driven Test

```go
func TestAdd(t *testing.T) {
    // Arrange
    tests := []struct {
        name string
        a    int
        b    int
        want int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -2, -3, -5},
        {"mixed signs", -2, 3, 1},
        {"zero values", 0, 0, 0},
    }

    // Act & Assert
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

### Pattern 2: Table-Driven Test with Error Handling

```go
func TestDivide(t *testing.T) {
    // Arrange
    tests := []struct {
        name    string
        a       float64
        b       float64
        want    float64
        wantErr bool
    }{
        {"positive numbers", 10, 2, 5, false},
        {"negative divisor", 10, -2, -5, false},
        {"zero dividend", 0, 5, 0, false},
        {"zero divisor", 10, 0, 0, true},
    }

    // Act & Assert
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Divide(tt.a, tt.b)

            // Check error expectation
            if (err != nil) != tt.wantErr {
                t.Errorf("Divide(%v, %v) error = %v; wantErr %v", tt.a, tt.b, err, tt.wantErr)
                return
            }

            // Check value (only if no error expected)
            if !tt.wantErr && got != tt.want {
                t.Errorf("Divide(%v, %v) = %v; want %v", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

### Pattern 3: Table-Driven Test with Complex Inputs

```go
func TestParseUser(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *User
        wantErr bool
    }{
        {
            name:  "valid user",
            input: `{"name":"Alice","age":30}`,
            want:  &User{Name: "Alice", Age: 30},
            wantErr: false,
        },
        {
            name:  "missing field",
            input: `{"name":"Bob"}`,
            want:  &User{Name: "Bob", Age: 0},
            wantErr: false,
        },
        {
            name:    "invalid json",
            input:   `{invalid}`,
            want:    nil,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseUser(tt.input)

            if (err != nil) != tt.wantErr {
                t.Errorf("ParseUser() error = %v; wantErr %v", err, tt.wantErr)
                return
            }

            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("ParseUser() = %v; want %v", got, tt.want)
            }
        })
    }
}
```

## Subtest Patterns (t.Run)

### Pattern 1: Simple Subtests

```go
func TestCalculator(t *testing.T) {
    calc := NewCalculator()

    t.Run("Addition", func(t *testing.T) {
        result := calc.Add(2, 3)
        if result != 5 {
            t.Errorf("got %d; want 5", result)
        }
    })

    t.Run("Subtraction", func(t *testing.T) {
        result := calc.Subtract(5, 3)
        if result != 2 {
            t.Errorf("got %d; want 2", result)
        }
    })

    t.Run("Multiplication", func(t *testing.T) {
        result := calc.Multiply(2, 3)
        if result != 6 {
            t.Errorf("got %d; want 6", result)
        }
    })
}
```

### Pattern 2: Nested Subtests

```go
func TestUserAPI(t *testing.T) {
    api := NewUserAPI()

    t.Run("Create", func(t *testing.T) {
        t.Run("valid user", func(t *testing.T) {
            user := &User{Name: "Alice", Age: 30}
            err := api.Create(user)
            if err != nil {
                t.Errorf("unexpected error: %v", err)
            }
        })

        t.Run("duplicate user", func(t *testing.T) {
            user := &User{Name: "Alice", Age: 30}
            err := api.Create(user)
            if err == nil {
                t.Error("expected error for duplicate user")
            }
        })
    })

    t.Run("Get", func(t *testing.T) {
        t.Run("existing user", func(t *testing.T) {
            user, err := api.Get("Alice")
            if err != nil {
                t.Errorf("unexpected error: %v", err)
            }
            if user.Name != "Alice" {
                t.Errorf("got %s; want Alice", user.Name)
            }
        })

        t.Run("non-existent user", func(t *testing.T) {
            _, err := api.Get("Bob")
            if err == nil {
                t.Error("expected error for non-existent user")
            }
        })
    })
}
```

## defer Cleanup Patterns

### Pattern 1: Resource Cleanup

```go
func TestFileOperations(t *testing.T) {
    // Arrange - create temp file
    f, err := os.CreateTemp("", "test-*.txt")
    if err != nil {
        t.Fatalf("failed to create temp file: %v", err)
    }
    defer os.Remove(f.Name())  // Cleanup
    defer f.Close()            // Cleanup

    // Act
    _, err = f.WriteString("test data")
    if err != nil {
        t.Fatalf("failed to write: %v", err)
    }

    // Assert
    content, err := os.ReadFile(f.Name())
    if err != nil {
        t.Fatalf("failed to read: %v", err)
    }
    if string(content) != "test data" {
        t.Errorf("got %s; want 'test data'", content)
    }
}
```

### Pattern 2: State Reset

```go
func TestConfigModification(t *testing.T) {
    // Arrange - save original config
    originalValue := config.GetValue("timeout")
    defer config.SetValue("timeout", originalValue)  // Reset after test

    // Act - modify config
    config.SetValue("timeout", "30s")

    // Assert
    result := DoSomethingWithConfig()
    if result == nil {
        t.Error("expected non-nil result")
    }
}
```

### Pattern 3: Parallel Test Cleanup

```go
func TestParallelWithCleanup(t *testing.T) {
    tests := []struct {
        name string
        data string
    }{
        {"test1", "data1"},
        {"test2", "data2"},
    }

    for _, tt := range tests {
        tt := tt  // Capture range variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()  // Run subtests in parallel

            // Arrange
            tempFile := createTempFile(t, tt.data)
            defer os.Remove(tempFile)  // Each subtest cleans up its own file

            // Act & Assert
            // ... test logic ...
        })
    }
}
```

## Interface-Based Mocking

### Pattern 1: Dependency Injection with Interfaces

```go
// Interface definition
type UserRepository interface {
    GetUser(id string) (*User, error)
    SaveUser(user *User) error
}

// Mock implementation
type MockUserRepository struct {
    GetUserFunc  func(id string) (*User, error)
    SaveUserFunc func(user *User) error
}

func (m *MockUserRepository) GetUser(id string) (*User, error) {
    if m.GetUserFunc != nil {
        return m.GetUserFunc(id)
    }
    return nil, nil
}

func (m *MockUserRepository) SaveUser(user *User) error {
    if m.SaveUserFunc != nil {
        return m.SaveUserFunc(user)
    }
    return nil
}

// Test using mock
func TestUserService_GetUser(t *testing.T) {
    // Arrange
    mockRepo := &MockUserRepository{
        GetUserFunc: func(id string) (*User, error) {
            if id == "123" {
                return &User{ID: "123", Name: "Alice"}, nil
            }
            return nil, errors.New("user not found")
        },
    }
    service := NewUserService(mockRepo)

    // Act
    user, err := service.GetUser("123")

    // Assert
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
    if user.Name != "Alice" {
        t.Errorf("got %s; want Alice", user.Name)
    }
}
```

### Pattern 2: Struct-Based Mock

```go
type MockHTTPClient struct {
    DoFunc func(req *http.Request) (*http.Response, error)
}

func (m *MockHTTPClient) Do(req *http.Request) (*http.Response, error) {
    if m.DoFunc != nil {
        return m.DoFunc(req)
    }
    return nil, nil
}

func TestAPIClient(t *testing.T) {
    // Arrange
    mockClient := &MockHTTPClient{
        DoFunc: func(req *http.Request) (*http.Response, error) {
            return &http.Response{
                StatusCode: 200,
                Body:       io.NopCloser(strings.NewReader(`{"status":"ok"}`)),
            }, nil
        },
    }
    client := NewAPIClient(mockClient)

    // Act
    response, err := client.FetchData()

    // Assert
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
    if response.Status != "ok" {
        t.Errorf("got %s; want ok", response.Status)
    }
}
```

## testify Integration Patterns

### Pattern 1: assert Package (Continue on Failure)

```go
import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestCalculator_WithAssert(t *testing.T) {
    calc := NewCalculator()

    // Arrange
    a, b := 2, 3

    // Act
    result := calc.Add(a, b)

    // Assert - test continues even if assertion fails
    assert.Equal(t, 5, result, "addition should return correct sum")
    assert.NotZero(t, result, "result should not be zero")
}
```

### Pattern 2: require Package (Stop on Failure)

```go
import (
    "testing"
    "github.com/stretchr/testify/require"
)

func TestFileProcessing_WithRequire(t *testing.T) {
    // Arrange
    data, err := loadTestData()
    require.NoError(t, err, "failed to load test data")  // Stop if error

    // Act
    result := ProcessData(data)

    // Assert
    require.NotNil(t, result, "result should not be nil")
    require.Len(t, result.Items, 3, "should have 3 items")
}
```

### Pattern 3: testify with Table-Driven Tests

```go
import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestDivide_WithTestify(t *testing.T) {
    tests := []struct {
        name    string
        a       float64
        b       float64
        want    float64
        wantErr bool
    }{
        {"positive numbers", 10, 2, 5, false},
        {"zero divisor", 10, 0, 0, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Divide(tt.a, tt.b)

            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
                assert.Equal(t, tt.want, got)
            }
        })
    }
}
```

### Pattern 4: testify suite Package

```go
import (
    "testing"
    "github.com/stretchr/testify/suite"
)

type CalculatorTestSuite struct {
    suite.Suite
    calc *Calculator
}

// SetupTest runs before each test
func (s *CalculatorTestSuite) SetupTest() {
    s.calc = NewCalculator()
}

// TearDownTest runs after each test
func (s *CalculatorTestSuite) TearDownTest() {
    s.calc = nil
}

func (s *CalculatorTestSuite) TestAddition() {
    result := s.calc.Add(2, 3)
    s.Equal(5, result)
}

func (s *CalculatorTestSuite) TestSubtraction() {
    result := s.calc.Subtract(5, 3)
    s.Equal(2, result)
}

// Run the suite
func TestCalculatorTestSuite(t *testing.T) {
    suite.Run(t, new(CalculatorTestSuite))
}
```

## Benchmark Patterns

### Pattern 1: Basic Benchmark

```go
func BenchmarkAdd(b *testing.B) {
    // Arrange
    a, c := 2, 3

    // Run benchmark b.N times
    for i := 0; i < b.N; i++ {
        _ = Add(a, c)
    }
}
```

### Pattern 2: Table-Driven Benchmarks

```go
func BenchmarkFibonacci(b *testing.B) {
    benchmarks := []struct {
        name string
        n    int
    }{
        {"Fib10", 10},
        {"Fib20", 20},
        {"Fib30", 30},
    }

    for _, bm := range benchmarks {
        b.Run(bm.name, func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                Fibonacci(bm.n)
            }
        })
    }
}
```

### Pattern 3: Benchmark with Setup

```go
func BenchmarkDatabaseQuery(b *testing.B) {
    // Setup (not measured)
    db := setupTestDatabase()
    defer db.Close()

    // Reset timer to exclude setup
    b.ResetTimer()

    // Run benchmark
    for i := 0; i < b.N; i++ {
        _, _ = db.Query("SELECT * FROM users WHERE id = ?", i%1000)
    }
}
```

## Example Test Patterns

### Pattern 1: Basic Example

```go
func ExampleAdd() {
    result := Add(2, 3)
    fmt.Println(result)
    // Output: 5
}
```

### Pattern 2: Example with Unordered Output

```go
func ExampleGetUserIDs() {
    ids := GetUserIDs()
    for _, id := range ids {
        fmt.Println(id)
    }
    // Unordered output:
    // 123
    // 456
    // 789
}
```

### Pattern 3: Example for Method

```go
func ExampleCalculator_Add() {
    calc := NewCalculator()
    result := calc.Add(2, 3)
    fmt.Println(result)
    // Output: 5
}
```

## Error Handling Patterns

### Pattern 1: Error Assertion

```go
func TestDivide_ErrorHandling(t *testing.T) {
    // Act
    _, err := Divide(10, 0)

    // Assert - check error occurred
    if err == nil {
        t.Error("expected error for division by zero")
    }

    // Assert - check specific error
    if !errors.Is(err, ErrDivisionByZero) {
        t.Errorf("expected ErrDivisionByZero; got %v", err)
    }
}
```

### Pattern 2: Error with testify

```go
func TestDivide_ErrorHandling_Testify(t *testing.T) {
    _, err := Divide(10, 0)

    assert.Error(t, err)
    assert.ErrorIs(t, err, ErrDivisionByZero)
    assert.Contains(t, err.Error(), "division by zero")
}
```

### Pattern 3: Multiple Error Conditions

```go
func TestValidateUser(t *testing.T) {
    tests := []struct {
        name    string
        user    *User
        wantErr error
    }{
        {
            name:    "missing name",
            user:    &User{Name: "", Age: 25},
            wantErr: ErrMissingName,
        },
        {
            name:    "invalid age",
            user:    &User{Name: "Alice", Age: -5},
            wantErr: ErrInvalidAge,
        },
        {
            name:    "valid user",
            user:    &User{Name: "Bob", Age: 30},
            wantErr: nil,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateUser(tt.user)

            if tt.wantErr != nil {
                if !errors.Is(err, tt.wantErr) {
                    t.Errorf("expected error %v; got %v", tt.wantErr, err)
                }
            } else {
                if err != nil {
                    t.Errorf("unexpected error: %v", err)
                }
            }
        })
    }
}
```

## Test Helper Functions

### Pattern 1: Helper for Assertions

```go
func assertEqual(t *testing.T, got, want interface{}) {
    t.Helper()  // Marks this as helper (correct line numbers in failures)

    if !reflect.DeepEqual(got, want) {
        t.Errorf("got %v; want %v", got, want)
    }
}

func TestAdd_WithHelper(t *testing.T) {
    result := Add(2, 3)
    assertEqual(t, result, 5)  // Failure reports line of this call, not inside assertEqual
}
```

### Pattern 2: Helper for Setup

```go
func setupTestServer(t *testing.T) *httptest.Server {
    t.Helper()

    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"status":"ok"}`))
    })

    server := httptest.NewServer(handler)
    t.Cleanup(func() { server.Close() })  // Cleanup automatically

    return server
}

func TestAPICall(t *testing.T) {
    server := setupTestServer(t)
    // Use server in test...
}
```

## Best Practices

1. **Use Table-Driven Tests**: Reduces code duplication, easier to add new cases
2. **Use t.Run for Subtests**: Better organization, parallel execution, focused test runs
3. **Use defer for Cleanup**: Ensures cleanup even if test fails
4. **Use t.Helper() in Helpers**: Correct error line numbers
5. **Use t.Parallel() Carefully**: Only for independent tests
6. **Prefer testify/assert over require**: Unless you need to stop execution
7. **Name Tests Descriptively**: `TestFunction_Scenario_ExpectedBehavior`
8. **Keep Tests Independent**: No shared state between tests
9. **Test Error Paths**: Use errors.Is() and errors.As()
10. **Use Examples for Documentation**: Executable documentation

## Anti-Patterns to Avoid

❌ **Shared State Between Tests**
```go
var globalCounter int  // BAD: Shared between tests

func TestIncrement(t *testing.T) {
    globalCounter++  // Test order matters
}
```

✅ **Isolated Test State**
```go
func TestIncrement(t *testing.T) {
    counter := 0  // GOOD: Local state
    counter++
}
```

❌ **Testing Implementation Details**
```go
func TestSort_InternalState(t *testing.T) {
    sorter := NewSorter()
    sorter.Sort([]int{3, 1, 2})
    // BAD: Testing internal pivotIndex
    if sorter.pivotIndex != 1 {
        t.Error("wrong pivot")
    }
}
```

✅ **Testing Behavior**
```go
func TestSort_OutputOrder(t *testing.T) {
    input := []int{3, 1, 2}
    got := Sort(input)
    want := []int{1, 2, 3}
    // GOOD: Testing public behavior
    if !reflect.DeepEqual(got, want) {
        t.Errorf("got %v; want %v", got, want)
    }
}
```

## References

- Go testing package: https://pkg.go.dev/testing
- Table-driven tests: https://go.dev/wiki/TableDrivenTests
- testify library: https://github.com/stretchr/testify
- Go testing best practices: https://go.dev/doc/tutorial/add-a-test

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
