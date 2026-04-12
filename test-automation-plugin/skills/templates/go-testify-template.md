# Go Testify Test Template

**Purpose**: Template for generating Go test files using the testify library
**Target Language**: Go
**Test Framework**: testify (github.com/stretchr/testify)
**Version Support**: testify v1.8.0+, Go 1.13+

## Overview

This template provides copy-paste ready test patterns for Go with the testify library. Testify provides rich assertions, mocking capabilities, and test suites that reduce boilerplate compared to the standard library.

## Template Structure

Each template includes:
- AAA (Arrange-Act-Assert) comments for clarity
- Placeholders in the format `{{PLACEHOLDER}}` for easy customization
- Complete, runnable test functions
- testify-specific features (assert, require, suite, mock)

### Key Placeholders

- `{{PACKAGE_NAME}}` - Package being tested (e.g., `calculator`, `user`)
- `{{TEST_PACKAGE_NAME}}` - Test package name (e.g., `calculator_test`, `calculator`)
- `{{FUNCTION_NAME}}` - Function being tested (e.g., `Add`, `GetUser`)
- `{{TYPE_NAME}}` - Type/struct being tested (e.g., `Calculator`, `User`)
- `{{STRUCT_FIELD}}` - Struct field name (e.g., `Name`, `Age`)
- `{{EXPECTED_VALUE}}` - Expected result value
- `{{INPUT_VALUE}}` - Input parameter value
- `{{ERROR_TYPE}}` - Error type or variable (e.g., `ErrNotFound`)

## Basic Test Template (assert)

Simple function test with testify assertions (test continues on failure):

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test{{FUNCTION_NAME}} tests the {{FUNCTION_NAME}} function.
func Test{{FUNCTION_NAME}}(t *testing.T) {
	// Arrange
	{{INPUT_NAME}} := {{INPUT_VALUE}}
	expected := {{EXPECTED_VALUE}}

	// Act
	result := {{FUNCTION_NAME}}({{INPUT_NAME}})

	// Assert
	assert.Equal(t, expected, result, "{{FUNCTION_NAME}} should return correct value")
	assert.NotZero(t, result, "result should not be zero")
}
```

**Example:**

```go
package calculator

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// TestAdd tests the Add function.
func TestAdd(t *testing.T) {
	// Arrange
	a := 2
	b := 3
	expected := 5

	// Act
	result := Add(a, b)

	// Assert
	assert.Equal(t, expected, result, "Add should return correct sum")
	assert.NotZero(t, result, "result should not be zero")
}
```

## Basic Test Template (require)

Simple function test with require assertions (test stops on failure):

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/require"
)

// Test{{FUNCTION_NAME}} tests the {{FUNCTION_NAME}} function.
func Test{{FUNCTION_NAME}}(t *testing.T) {
	// Arrange
	{{INPUT_NAME}} := {{INPUT_VALUE}}
	expected := {{EXPECTED_VALUE}}

	// Act
	result := {{FUNCTION_NAME}}({{INPUT_NAME}})

	// Assert
	require.Equal(t, expected, result, "{{FUNCTION_NAME}} should return correct value")
	require.NotNil(t, result, "result should not be nil")
}
```

**Example:**

```go
package user

import (
	"testing"
	"github.com/stretchr/testify/require"
)

// TestGetUser tests the GetUser function.
func TestGetUser(t *testing.T) {
	// Arrange
	repo := NewUserRepository()
	userID := "123"

	// Act
	user, err := repo.GetUser(userID)

	// Assert
	require.NoError(t, err, "GetUser should not return error")
	require.NotNil(t, user, "user should not be nil")
	require.Equal(t, userID, user.ID, "user ID should match")
}
```

## Table-Driven Test Template

Comprehensive table-driven pattern with testify assertions:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test{{FUNCTION_NAME}} tests the {{FUNCTION_NAME}} function with various inputs.
func Test{{FUNCTION_NAME}}(t *testing.T) {
	// Arrange
	tests := []struct {
		name string
		{{INPUT_PARAM_1}} {{TYPE_1}}
		{{INPUT_PARAM_2}} {{TYPE_2}}
		want {{RETURN_TYPE}}
	}{
		{
			name: "{{TEST_CASE_1_NAME}}",
			{{INPUT_PARAM_1}}: {{VALUE_1}},
			{{INPUT_PARAM_2}}: {{VALUE_2}},
			want: {{EXPECTED_1}},
		},
		{
			name: "{{TEST_CASE_2_NAME}}",
			{{INPUT_PARAM_1}}: {{VALUE_3}},
			{{INPUT_PARAM_2}}: {{VALUE_4}},
			want: {{EXPECTED_2}},
		},
		{
			name: "{{TEST_CASE_3_NAME}}",
			{{INPUT_PARAM_1}}: {{VALUE_5}},
			{{INPUT_PARAM_2}}: {{VALUE_6}},
			want: {{EXPECTED_3}},
		},
	}

	// Act & Assert
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := {{FUNCTION_NAME}}(tt.{{INPUT_PARAM_1}}, tt.{{INPUT_PARAM_2}})
			assert.Equal(t, tt.want, got)
		})
	}
}
```

**Example:**

```go
package calculator

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// TestAdd tests the Add function with various inputs.
func TestAdd(t *testing.T) {
	// Arrange
	tests := []struct {
		name string
		a    int
		b    int
		want int
	}{
		{
			name: "positive numbers",
			a:    2,
			b:    3,
			want: 5,
		},
		{
			name: "negative numbers",
			a:    -2,
			b:    -3,
			want: -5,
		},
		{
			name: "mixed signs",
			a:    -2,
			b:    3,
			want: 1,
		},
		{
			name: "zero values",
			a:    0,
			b:    0,
			want: 0,
		},
	}

	// Act & Assert
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Add(tt.a, tt.b)
			assert.Equal(t, tt.want, got)
		})
	}
}
```

## Subtest Template

Multiple subtests using t.Run with testify assertions:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test{{TYPE_NAME}} tests the {{TYPE_NAME}} type with multiple scenarios.
func Test{{TYPE_NAME}}(t *testing.T) {
	// Arrange - shared setup
	{{INSTANCE_NAME}} := {{CONSTRUCTOR_FUNC}}()

	t.Run("{{SUBTEST_1_NAME}}", func(t *testing.T) {
		// Arrange
		{{INPUT_NAME}} := {{INPUT_VALUE_1}}
		expected := {{EXPECTED_VALUE_1}}

		// Act
		result := {{INSTANCE_NAME}}.{{METHOD_NAME_1}}({{INPUT_NAME}})

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("{{SUBTEST_2_NAME}}", func(t *testing.T) {
		// Arrange
		{{INPUT_NAME}} := {{INPUT_VALUE_2}}
		expected := {{EXPECTED_VALUE_2}}

		// Act
		result := {{INSTANCE_NAME}}.{{METHOD_NAME_2}}({{INPUT_NAME}})

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("{{SUBTEST_3_NAME}}", func(t *testing.T) {
		// Arrange
		{{INPUT_NAME}} := {{INPUT_VALUE_3}}
		expected := {{EXPECTED_VALUE_3}}

		// Act
		result := {{INSTANCE_NAME}}.{{METHOD_NAME_3}}({{INPUT_NAME}})

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})
}
```

**Example:**

```go
package calculator

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// TestCalculator tests the Calculator type with multiple scenarios.
func TestCalculator(t *testing.T) {
	// Arrange - shared setup
	calc := NewCalculator()

	t.Run("Addition", func(t *testing.T) {
		// Arrange
		a := 2
		b := 3
		expected := 5

		// Act
		result := calc.Add(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("Subtraction", func(t *testing.T) {
		// Arrange
		a := 5
		b := 3
		expected := 2

		// Act
		result := calc.Subtract(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("Multiplication", func(t *testing.T) {
		// Arrange
		a := 2
		b := 3
		expected := 6

		// Act
		result := calc.Multiply(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})
}
```

## Error Handling Template

Tests with error assertions using testify's error helpers:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test{{FUNCTION_NAME}} tests the {{FUNCTION_NAME}} function with error handling.
func Test{{FUNCTION_NAME}}(t *testing.T) {
	// Arrange
	tests := []struct {
		name    string
		{{INPUT_PARAM_1}} {{TYPE_1}}
		{{INPUT_PARAM_2}} {{TYPE_2}}
		want    {{RETURN_TYPE}}
		wantErr bool
	}{
		{
			name: "{{HAPPY_PATH_NAME}}",
			{{INPUT_PARAM_1}}: {{VALID_VALUE_1}},
			{{INPUT_PARAM_2}}: {{VALID_VALUE_2}},
			want:    {{EXPECTED_RESULT}},
			wantErr: false,
		},
		{
			name: "{{ERROR_CASE_NAME}}",
			{{INPUT_PARAM_1}}: {{INVALID_VALUE_1}},
			{{INPUT_PARAM_2}}: {{INVALID_VALUE_2}},
			want:    {{ZERO_VALUE}},
			wantErr: true,
		},
	}

	// Act & Assert
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := {{FUNCTION_NAME}}(tt.{{INPUT_PARAM_1}}, tt.{{INPUT_PARAM_2}})

			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.want, got)
			}
		})
	}
}

// Test{{FUNCTION_NAME}}_SpecificError tests for specific error types.
func Test{{FUNCTION_NAME}}_SpecificError(t *testing.T) {
	// Act
	_, err := {{FUNCTION_NAME}}({{INVALID_INPUT}})

	// Assert
	assert.Error(t, err, "should return error for {{ERROR_CONDITION}}")
	assert.ErrorIs(t, err, {{ERROR_TYPE}}, "should be specific error type")
	assert.Contains(t, err.Error(), "{{ERROR_MESSAGE_SUBSTRING}}")
}
```

**Example:**

```go
package calculator

import (
	"errors"
	"testing"
	"github.com/stretchr/testify/assert"
)

var ErrDivisionByZero = errors.New("division by zero")

// TestDivide tests the Divide function with error handling.
func TestDivide(t *testing.T) {
	// Arrange
	tests := []struct {
		name    string
		a       float64
		b       float64
		want    float64
		wantErr bool
	}{
		{
			name:    "positive numbers",
			a:       10,
			b:       2,
			want:    5,
			wantErr: false,
		},
		{
			name:    "negative divisor",
			a:       10,
			b:       -2,
			want:    -5,
			wantErr: false,
		},
		{
			name:    "zero dividend",
			a:       0,
			b:       5,
			want:    0,
			wantErr: false,
		},
		{
			name:    "zero divisor",
			a:       10,
			b:       0,
			want:    0,
			wantErr: true,
		},
	}

	// Act & Assert
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

// TestDivide_SpecificError tests for specific error types.
func TestDivide_SpecificError(t *testing.T) {
	// Act
	_, err := Divide(10, 0)

	// Assert
	assert.Error(t, err, "should return error for division by zero")
	assert.ErrorIs(t, err, ErrDivisionByZero, "should be ErrDivisionByZero")
	assert.Contains(t, err.Error(), "division by zero")
}
```

## Interface Mocking Template (testify/mock)

Dependency injection with testify's mock package:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mock{{INTERFACE_NAME}} is a mock implementation of {{INTERFACE_NAME}}.
type Mock{{INTERFACE_NAME}} struct {
	mock.Mock
}

// {{METHOD_NAME_1}} mocks {{INTERFACE_NAME}}.{{METHOD_NAME_1}}.
func (m *Mock{{INTERFACE_NAME}}) {{METHOD_NAME_1}}({{PARAMS_1}}) ({{RETURNS_1}}) {
	args := m.Called({{PARAM_NAMES_1}})
	return args.Get(0).({{RETURN_TYPE_1}}), args.Error(1)
}

// {{METHOD_NAME_2}} mocks {{INTERFACE_NAME}}.{{METHOD_NAME_2}}.
func (m *Mock{{INTERFACE_NAME}}) {{METHOD_NAME_2}}({{PARAMS_2}}) {{RETURNS_2}} {
	args := m.Called({{PARAM_NAMES_2}})
	return args.Error(0)
}

// Test{{SERVICE_NAME}}_{{METHOD_NAME}} tests {{SERVICE_NAME}}.{{METHOD_NAME}} with mock dependencies.
func Test{{SERVICE_NAME}}_{{METHOD_NAME}}(t *testing.T) {
	// Arrange
	mock{{DEPENDENCY}} := new(Mock{{INTERFACE_NAME}})
	mock{{DEPENDENCY}}.On("{{METHOD_NAME_1}}", {{EXPECTED_ARGS}}).Return({{RETURN_VALUES}})

	service := New{{SERVICE_NAME}}(mock{{DEPENDENCY}})

	// Act
	result, err := service.{{METHOD_NAME}}({{TEST_INPUT}})

	// Assert
	assert.NoError(t, err)
	assert.Equal(t, {{EXPECTED_VALUE}}, result)
	mock{{DEPENDENCY}}.AssertExpectations(t)
}
```

**Example:**

```go
package user

import (
	"errors"
	"testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

var ErrUserNotFound = errors.New("user not found")

// MockUserRepository is a mock implementation of UserRepository.
type MockUserRepository struct {
	mock.Mock
}

// GetUser mocks UserRepository.GetUser.
func (m *MockUserRepository) GetUser(id string) (*User, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*User), args.Error(1)
}

// SaveUser mocks UserRepository.SaveUser.
func (m *MockUserRepository) SaveUser(user *User) error {
	args := m.Called(user)
	return args.Error(0)
}

// TestUserService_GetUser tests UserService.GetUser with mock repository.
func TestUserService_GetUser(t *testing.T) {
	t.Run("existing user", func(t *testing.T) {
		// Arrange
		mockRepo := new(MockUserRepository)
		expectedUser := &User{ID: "123", Name: "Alice"}
		mockRepo.On("GetUser", "123").Return(expectedUser, nil)

		service := NewUserService(mockRepo)

		// Act
		user, err := service.GetUser("123")

		// Assert
		assert.NoError(t, err)
		assert.Equal(t, "Alice", user.Name)
		assert.Equal(t, "123", user.ID)
		mockRepo.AssertExpectations(t)
	})

	t.Run("non-existent user", func(t *testing.T) {
		// Arrange
		mockRepo := new(MockUserRepository)
		mockRepo.On("GetUser", "999").Return(nil, ErrUserNotFound)

		service := NewUserService(mockRepo)

		// Act
		_, err := service.GetUser("999")

		// Assert
		assert.Error(t, err)
		assert.ErrorIs(t, err, ErrUserNotFound)
		mockRepo.AssertExpectations(t)
	})
}

// TestUserService_SaveUser tests UserService.SaveUser.
func TestUserService_SaveUser(t *testing.T) {
	// Arrange
	mockRepo := new(MockUserRepository)
	user := &User{ID: "123", Name: "Alice"}
	mockRepo.On("SaveUser", user).Return(nil)

	service := NewUserService(mockRepo)

	// Act
	err := service.SaveUser(user)

	// Assert
	assert.NoError(t, err)
	mockRepo.AssertExpectations(t)
	mockRepo.AssertCalled(t, "SaveUser", user)
}
```

## Test Suite Template (testify/suite)

Test suite with setup and teardown:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"testing"
	"github.com/stretchr/testify/suite"
)

// {{TYPE_NAME}}TestSuite is a test suite for {{TYPE_NAME}}.
type {{TYPE_NAME}}TestSuite struct {
	suite.Suite
	{{FIELD_NAME}} *{{TYPE_NAME}}
	{{DEPENDENCY_FIELD}} {{DEPENDENCY_TYPE}}
}

// SetupSuite runs once before all tests in the suite.
func (s *{{TYPE_NAME}}TestSuite) SetupSuite() {
	// Suite-level setup (runs once)
	{{SUITE_SETUP}}
}

// TearDownSuite runs once after all tests in the suite.
func (s *{{TYPE_NAME}}TestSuite) TearDownSuite() {
	// Suite-level cleanup (runs once)
	{{SUITE_CLEANUP}}
}

// SetupTest runs before each test.
func (s *{{TYPE_NAME}}TestSuite) SetupTest() {
	// Test-level setup (runs before each test)
	s.{{FIELD_NAME}} = {{CONSTRUCTOR_FUNC}}()
}

// TearDownTest runs after each test.
func (s *{{TYPE_NAME}}TestSuite) TearDownTest() {
	// Test-level cleanup (runs after each test)
	s.{{FIELD_NAME}} = nil
}

// Test{{METHOD_NAME_1}} tests {{METHOD_NAME_1}}.
func (s *{{TYPE_NAME}}TestSuite) Test{{METHOD_NAME_1}}() {
	// Arrange
	{{INPUT_NAME}} := {{INPUT_VALUE}}
	expected := {{EXPECTED_VALUE}}

	// Act
	result := s.{{FIELD_NAME}}.{{METHOD_NAME_1}}({{INPUT_NAME}})

	// Assert
	s.Equal(expected, result)
	s.NotZero(result)
}

// Test{{METHOD_NAME_2}} tests {{METHOD_NAME_2}}.
func (s *{{TYPE_NAME}}TestSuite) Test{{METHOD_NAME_2}}() {
	// Arrange
	{{INPUT_NAME}} := {{INPUT_VALUE}}
	expected := {{EXPECTED_VALUE}}

	// Act
	result := s.{{FIELD_NAME}}.{{METHOD_NAME_2}}({{INPUT_NAME}})

	// Assert
	s.Equal(expected, result)
	s.NotZero(result)
}

// Test{{TYPE_NAME}}TestSuite runs the test suite.
func Test{{TYPE_NAME}}TestSuite(t *testing.T) {
	suite.Run(t, new({{TYPE_NAME}}TestSuite))
}
```

**Example:**

```go
package calculator

import (
	"testing"
	"github.com/stretchr/testify/suite"
)

// CalculatorTestSuite is a test suite for Calculator.
type CalculatorTestSuite struct {
	suite.Suite
	calc *Calculator
}

// SetupSuite runs once before all tests in the suite.
func (s *CalculatorTestSuite) SetupSuite() {
	// Suite-level setup (runs once)
	// e.g., initialize database connection
}

// TearDownSuite runs once after all tests in the suite.
func (s *CalculatorTestSuite) TearDownSuite() {
	// Suite-level cleanup (runs once)
	// e.g., close database connection
}

// SetupTest runs before each test.
func (s *CalculatorTestSuite) SetupTest() {
	// Test-level setup (runs before each test)
	s.calc = NewCalculator()
}

// TearDownTest runs after each test.
func (s *CalculatorTestSuite) TearDownTest() {
	// Test-level cleanup (runs after each test)
	s.calc = nil
}

// TestAddition tests addition functionality.
func (s *CalculatorTestSuite) TestAddition() {
	// Arrange
	a := 2
	b := 3
	expected := 5

	// Act
	result := s.calc.Add(a, b)

	// Assert
	s.Equal(expected, result)
	s.NotZero(result)
}

// TestSubtraction tests subtraction functionality.
func (s *CalculatorTestSuite) TestSubtraction() {
	// Arrange
	a := 5
	b := 3
	expected := 2

	// Act
	result := s.calc.Subtract(a, b)

	// Assert
	s.Equal(expected, result)
	s.NotZero(result)
}

// TestMultiplication tests multiplication functionality.
func (s *CalculatorTestSuite) TestMultiplication() {
	// Arrange
	a := 2
	b := 3
	expected := 6

	// Act
	result := s.calc.Multiply(a, b)

	// Assert
	s.Equal(expected, result)
	s.NotZero(result)
}

// TestCalculatorTestSuite runs the test suite.
func TestCalculatorTestSuite(t *testing.T) {
	suite.Run(t, new(CalculatorTestSuite))
}
```

## Cleanup Template

Resource cleanup using defer with testify:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"os"
	"testing"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/assert"
)

// Test{{FUNCTION_NAME}}_WithCleanup tests {{FUNCTION_NAME}} with resource cleanup.
func Test{{FUNCTION_NAME}}_WithCleanup(t *testing.T) {
	// Arrange - create resource
	{{RESOURCE_NAME}}, err := {{CREATE_RESOURCE}}
	require.NoError(t, err, "failed to create {{RESOURCE_TYPE}}")
	defer {{CLEANUP_FUNC}}({{RESOURCE_NAME}})  // Cleanup runs after test

	// Act
	result := {{FUNCTION_NAME}}({{RESOURCE_NAME}})

	// Assert
	assert.Equal(t, {{EXPECTED_VALUE}}, result)
}

// Test{{FUNCTION_NAME}}_Parallel tests {{FUNCTION_NAME}} with parallel subtests and cleanup.
func Test{{FUNCTION_NAME}}_Parallel(t *testing.T) {
	tests := []struct {
		name string
		data string
	}{
		{"test1", "data1"},
		{"test2", "data2"},
		{"test3", "data3"},
	}

	for _, tt := range tests {
		tt := tt  // Capture range variable
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()  // Run subtests in parallel

			// Arrange - create isolated resource
			resource := {{CREATE_RESOURCE}}(tt.data)
			defer {{CLEANUP_FUNC}}(resource)  // Each subtest cleans up its own resource

			// Act
			result := {{FUNCTION_NAME}}(resource)

			// Assert
			assert.Equal(t, {{EXPECTED_VALUE}}, result)
		})
	}
}
```

**Example:**

```go
package fileops

import (
	"os"
	"testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestFileOperations_WithCleanup tests file operations with resource cleanup.
func TestFileOperations_WithCleanup(t *testing.T) {
	// Arrange - create temp file
	f, err := os.CreateTemp("", "test-*.txt")
	require.NoError(t, err, "failed to create temp file")
	defer os.Remove(f.Name())  // Cleanup file
	defer f.Close()            // Cleanup file handle

	// Arrange - write test data
	testData := "test data"
	_, err = f.WriteString(testData)
	require.NoError(t, err, "failed to write")

	// Act
	content, err := os.ReadFile(f.Name())
	require.NoError(t, err, "failed to read")

	// Assert
	assert.Equal(t, testData, string(content))
}

// TestProcess_Parallel tests processing with parallel subtests and cleanup.
func TestProcess_Parallel(t *testing.T) {
	tests := []struct {
		name string
		data string
	}{
		{"test1", "data1"},
		{"test2", "data2"},
		{"test3", "data3"},
	}

	for _, tt := range tests {
		tt := tt  // Capture range variable
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()  // Run subtests in parallel

			// Arrange - create isolated temp file
			tempFile, err := os.CreateTemp("", tt.name+"-*.txt")
			require.NoError(t, err, "failed to create temp file")
			defer os.Remove(tempFile.Name())  // Each subtest cleans up its own file
			defer tempFile.Close()

			// Act
			result := ProcessFile(tempFile.Name(), tt.data)

			// Assert
			assert.True(t, result)
		})
	}
}
```

## Complete Example

Full test file demonstrating all patterns with testify:

```go
package calculator

import (
	"errors"
	"testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

var ErrDivisionByZero = errors.New("division by zero")

// TestAdd_Basic tests basic addition functionality.
func TestAdd_Basic(t *testing.T) {
	// Arrange
	calc := NewCalculator()
	a := 2
	b := 3
	expected := 5

	// Act
	result := calc.Add(a, b)

	// Assert
	assert.Equal(t, expected, result, "Add should return correct sum")
	assert.NotZero(t, result)
}

// TestAdd_TableDriven tests Add with various inputs using table-driven pattern.
func TestAdd_TableDriven(t *testing.T) {
	// Arrange
	calc := NewCalculator()
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
		{"large numbers", 1000, 2000, 3000},
	}

	// Act & Assert
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := calc.Add(tt.a, tt.b)
			assert.Equal(t, tt.want, got)
		})
	}
}

// TestCalculator_AllOperations tests all calculator operations with subtests.
func TestCalculator_AllOperations(t *testing.T) {
	// Arrange
	calc := NewCalculator()

	t.Run("Addition", func(t *testing.T) {
		// Arrange
		a, b := 2, 3
		expected := 5

		// Act
		result := calc.Add(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("Subtraction", func(t *testing.T) {
		// Arrange
		a, b := 5, 3
		expected := 2

		// Act
		result := calc.Subtract(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})

	t.Run("Multiplication", func(t *testing.T) {
		// Arrange
		a, b := 2, 3
		expected := 6

		// Act
		result := calc.Multiply(a, b)

		// Assert
		assert.Equal(t, expected, result)
		assert.NotZero(t, result)
	})
}

// TestDivide_WithErrorHandling tests Divide with error cases.
func TestDivide_WithErrorHandling(t *testing.T) {
	// Arrange
	calc := NewCalculator()
	tests := []struct {
		name    string
		a       float64
		b       float64
		want    float64
		wantErr bool
	}{
		{
			name:    "positive numbers",
			a:       10,
			b:       2,
			want:    5,
			wantErr: false,
		},
		{
			name:    "negative divisor",
			a:       10,
			b:       -2,
			want:    -5,
			wantErr: false,
		},
		{
			name:    "zero divisor",
			a:       10,
			b:       0,
			want:    0,
			wantErr: true,
		},
	}

	// Act & Assert
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := calc.Divide(tt.a, tt.b)

			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.want, got)
			}
		})
	}
}

// TestDivide_SpecificError tests that Divide returns the correct error type.
func TestDivide_SpecificError(t *testing.T) {
	// Arrange
	calc := NewCalculator()

	// Act
	_, err := calc.Divide(10, 0)

	// Assert
	assert.Error(t, err, "should return error for division by zero")
	assert.ErrorIs(t, err, ErrDivisionByZero)
	assert.Contains(t, err.Error(), "division by zero")
}

// MockLogger is a mock implementation of Logger interface using testify/mock.
type MockLogger struct {
	mock.Mock
}

// Log mocks Logger.Log.
func (m *MockLogger) Log(msg string) {
	m.Called(msg)
}

// TestCalculator_WithLogger tests calculator with logging dependency.
func TestCalculator_WithLogger(t *testing.T) {
	// Arrange
	mockLogger := new(MockLogger)
	mockLogger.On("Log", mock.Anything).Return()

	calc := NewCalculatorWithLogger(mockLogger)

	// Act
	result := calc.Add(2, 3)

	// Assert
	assert.Equal(t, 5, result)
	mockLogger.AssertExpectations(t)
	mockLogger.AssertCalled(t, "Log", mock.Anything)
}

// CalculatorTestSuite is a test suite for Calculator.
type CalculatorTestSuite struct {
	suite.Suite
	calc *Calculator
}

// SetupTest runs before each test.
func (s *CalculatorTestSuite) SetupTest() {
	s.calc = NewCalculator()
}

// TearDownTest runs after each test.
func (s *CalculatorTestSuite) TearDownTest() {
	s.calc = nil
}

// TestSuiteAddition tests addition in suite.
func (s *CalculatorTestSuite) TestSuiteAddition() {
	result := s.calc.Add(2, 3)
	s.Equal(5, result)
}

// TestSuiteSubtraction tests subtraction in suite.
func (s *CalculatorTestSuite) TestSuiteSubtraction() {
	result := s.calc.Subtract(5, 3)
	s.Equal(2, result)
}

// TestCalculatorTestSuite runs the test suite.
func TestCalculatorTestSuite(t *testing.T) {
	suite.Run(t, new(CalculatorTestSuite))
}
```

## Common Testify Assertions

```go
// ====================================================================
// Equality Assertions
// ====================================================================

assert.Equal(t, expected, actual)
assert.NotEqual(t, expected, actual)
assert.Same(t, expectedPointer, actualPointer)  // Same memory address
assert.NotSame(t, expectedPointer, actualPointer)
assert.EqualValues(t, expected, actual)  // Convert types before comparison

// ====================================================================
// Nil Assertions
// ====================================================================

assert.Nil(t, object)
assert.NotNil(t, object)

// ====================================================================
// Boolean Assertions
// ====================================================================

assert.True(t, value)
assert.False(t, value)

// ====================================================================
// String Assertions
// ====================================================================

assert.Equal(t, "expected", actual)
assert.Contains(t, "hello world", "world")
assert.NotContains(t, "hello world", "xyz")
assert.Regexp(t, `\d+`, "abc123")

// ====================================================================
// Numeric Assertions
// ====================================================================

assert.Equal(t, 5, actual)
assert.NotEqual(t, 5, actual)
assert.Greater(t, actual, 5)
assert.GreaterOrEqual(t, actual, 5)
assert.Less(t, actual, 5)
assert.LessOrEqual(t, actual, 5)
assert.InDelta(t, 3.14, actual, 0.01)  // Float comparison with delta

// ====================================================================
// Collection Assertions
// ====================================================================

assert.Empty(t, collection)
assert.NotEmpty(t, collection)
assert.Len(t, collection, 3)
assert.Contains(t, []int{1, 2, 3}, 2)
assert.NotContains(t, []int{1, 2, 3}, 5)
assert.ElementsMatch(t, []int{1, 2, 3}, []int{3, 2, 1})  // Same elements, any order
assert.Subset(t, []int{1, 2, 3, 4}, []int{2, 3})

// ====================================================================
// Error Assertions
// ====================================================================

assert.NoError(t, err)
assert.Error(t, err)
assert.ErrorIs(t, err, ErrNotFound)
assert.ErrorAs(t, err, &target)
assert.ErrorContains(t, err, "not found")
assert.EqualError(t, err, "exact error message")

// ====================================================================
// Type Assertions
// ====================================================================

assert.IsType(t, &User{}, actual)
assert.Implements(t, (*Repository)(nil), mockRepo)

// ====================================================================
// Panic Assertions
// ====================================================================

assert.Panics(t, func() { panicFunc() })
assert.NotPanics(t, func() { safeFunc() })

// ====================================================================
// require Package (Stops test on failure)
// ====================================================================

require.NoError(t, err)  // If fails, test stops immediately
require.NotNil(t, object)
require.Equal(t, expected, actual)
```

## Usage Guide

### Step 1: Install testify

```bash
go get github.com/stretchr/testify
```

### Step 2: Choose the Right Template

- **Basic Test (assert)**: Simple tests where you want all assertions to run
- **Basic Test (require)**: Tests where failure should stop immediately
- **Table-Driven**: Multiple test cases for same function
- **Subtest**: Grouped tests for related functionality
- **Error Handling**: Functions that return errors
- **Mocking (testify/mock)**: Functions with external dependencies
- **Suite (testify/suite)**: Test suites with setup/teardown
- **Cleanup**: Tests requiring resource management

### Step 3: Customize Placeholders

Replace all `{{PLACEHOLDER}}` values with your specific names:

1. Package names (`{{PACKAGE_NAME}}`, `{{TEST_PACKAGE_NAME}}`)
2. Function/method names (`{{FUNCTION_NAME}}`, `{{METHOD_NAME}}`)
3. Type names (`{{TYPE_NAME}}`, `{{INTERFACE_NAME}}`)
4. Input/output values (`{{INPUT_VALUE}}`, `{{EXPECTED_VALUE}}`)
5. Parameters and types (`{{PARAMS}}`, `{{TYPE}}`)

### Step 4: Choose assert vs require

**Use `assert`** when:
- You want all assertions in a test to run
- Failure should log but continue
- Multiple independent checks

**Use `require`** when:
- Failure should stop test immediately
- Following code depends on assertion passing
- Setup/precondition checks

### Step 5: Run Tests

```bash
# Run all tests
go test

# Run with verbose output
go test -v

# Run specific test
go test -run TestAdd

# Run with coverage
go test -cover

# Run specific subtest
go test -run TestCalculator/Addition
```

### Best Practices

1. **Use assert for most assertions**: Unless you need to stop immediately
2. **Use require for setup**: Critical preconditions that must pass
3. **Mock external dependencies**: Use testify/mock for interfaces
4. **Use suites for complex setup**: When you need setup/teardown
5. **Add descriptive messages**: `assert.Equal(t, expected, actual, "message")`
6. **Verify mock calls**: Always call `AssertExpectations(t)`
7. **Use mock.Anything**: When exact argument doesn't matter

### Common Patterns

**Testing for nil with proper type:**
```go
assert.Nil(t, object)
// OR
assert.NotNil(t, object)
```

**Mocking with specific arguments:**
```go
mockRepo.On("GetUser", "123").Return(&User{ID: "123"}, nil)
mockRepo.On("GetUser", "999").Return(nil, ErrNotFound)
```

**Mocking with any arguments:**
```go
mockLogger.On("Log", mock.Anything).Return()
```

**Mocking with argument matchers:**
```go
mockRepo.On("SaveUser", mock.MatchedBy(func(u *User) bool {
	return u.Age >= 18
})).Return(nil)
```

**Using suite with database:**
```go
func (s *MySuite) SetupSuite() {
	s.db = setupTestDB()  // Once for all tests
}

func (s *MySuite) SetupTest() {
	s.db.Truncate()  // Before each test
}
```

## References

- testify Documentation: https://github.com/stretchr/testify
- testify/assert: https://pkg.go.dev/github.com/stretchr/testify/assert
- testify/require: https://pkg.go.dev/github.com/stretchr/testify/require
- testify/mock: https://pkg.go.dev/github.com/stretchr/testify/mock
- testify/suite: https://pkg.go.dev/github.com/stretchr/testify/suite
- Go patterns document: `skills/test-generation/go-patterns.md`

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
