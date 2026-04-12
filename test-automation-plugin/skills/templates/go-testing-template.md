# Go Testing Template (Standard Library)

**Purpose**: Template for generating Go test files using the built-in testing package
**Target Language**: Go
**Test Framework**: testing (built-in)
**Version Support**: Go 1.13+

## Overview

This template provides copy-paste ready test patterns for Go's built-in testing package. All tests use idiomatic Go patterns including table-driven tests, subtests, error handling, and manual assertions.

## Template Structure

Each template includes:
- AAA (Arrange-Act-Assert) comments for clarity
- Placeholders in the format `{{PLACEHOLDER}}` for easy customization
- Complete, runnable test functions
- Best practices for Go testing

### Key Placeholders

- `{{PACKAGE_NAME}}` - Package being tested (e.g., `calculator`, `user`)
- `{{TEST_PACKAGE_NAME}}` - Test package name (e.g., `calculator_test`, `calculator`)
- `{{FUNCTION_NAME}}` - Function being tested (e.g., `Add`, `GetUser`)
- `{{TYPE_NAME}}` - Type/struct being tested (e.g., `Calculator`, `User`)
- `{{STRUCT_FIELD}}` - Struct field name (e.g., `Name`, `Age`)
- `{{EXPECTED_VALUE}}` - Expected result value
- `{{INPUT_VALUE}}` - Input parameter value
- `{{ERROR_TYPE}}` - Error type or variable (e.g., `ErrNotFound`)

## Basic Test Template

Simple function test with AAA pattern:

```go
package {{TEST_PACKAGE_NAME}}

import "testing"

// Test{{FUNCTION_NAME}} tests the {{FUNCTION_NAME}} function.
func Test{{FUNCTION_NAME}}(t *testing.T) {
	// Arrange
	{{INPUT_NAME}} := {{INPUT_VALUE}}
	expected := {{EXPECTED_VALUE}}

	// Act
	result := {{FUNCTION_NAME}}({{INPUT_NAME}})

	// Assert
	if result != expected {
		t.Errorf("{{FUNCTION_NAME}}(%v) = %v; want %v", {{INPUT_NAME}}, result, expected)
	}
}
```

**Example:**

```go
package calculator

import "testing"

// TestAdd tests the Add function.
func TestAdd(t *testing.T) {
	// Arrange
	a := 2
	b := 3
	expected := 5

	// Act
	result := Add(a, b)

	// Assert
	if result != expected {
		t.Errorf("Add(%d, %d) = %d; want %d", a, b, result, expected)
	}
}
```

## Table-Driven Test Template

Comprehensive table-driven pattern with multiple test cases:

```go
package {{TEST_PACKAGE_NAME}}

import "testing"

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
			if got != tt.want {
				t.Errorf("{{FUNCTION_NAME}}(%v, %v) = %v; want %v",
					tt.{{INPUT_PARAM_1}}, tt.{{INPUT_PARAM_2}}, got, tt.want)
			}
		})
	}
}
```

**Example:**

```go
package calculator

import "testing"

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
			if got != tt.want {
				t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}
```

## Subtest Template

Multiple subtests using t.Run for logical grouping:

```go
package {{TEST_PACKAGE_NAME}}

import "testing"

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
		if result != expected {
			t.Errorf("got %v; want %v", result, expected)
		}
	})

	t.Run("{{SUBTEST_2_NAME}}", func(t *testing.T) {
		// Arrange
		{{INPUT_NAME}} := {{INPUT_VALUE_2}}
		expected := {{EXPECTED_VALUE_2}}

		// Act
		result := {{INSTANCE_NAME}}.{{METHOD_NAME_2}}({{INPUT_NAME}})

		// Assert
		if result != expected {
			t.Errorf("got %v; want %v", result, expected)
		}
	})

	t.Run("{{SUBTEST_3_NAME}}", func(t *testing.T) {
		// Arrange
		{{INPUT_NAME}} := {{INPUT_VALUE_3}}
		expected := {{EXPECTED_VALUE_3}}

		// Act
		result := {{INSTANCE_NAME}}.{{METHOD_NAME_3}}({{INPUT_NAME}})

		// Assert
		if result != expected {
			t.Errorf("got %v; want %v", result, expected)
		}
	})
}
```

**Example:**

```go
package calculator

import "testing"

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
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
	})

	t.Run("Subtraction", func(t *testing.T) {
		// Arrange
		a := 5
		b := 3
		expected := 2

		// Act
		result := calc.Subtract(a, b)

		// Assert
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
	})

	t.Run("Multiplication", func(t *testing.T) {
		// Arrange
		a := 2
		b := 3
		expected := 6

		// Act
		result := calc.Multiply(a, b)

		// Assert
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
	})
}
```

## Error Handling Template

Tests with error assertions using idiomatic Go patterns:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"errors"
	"testing"
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

			// Check error expectation
			if (err != nil) != tt.wantErr {
				t.Errorf("{{FUNCTION_NAME}}(%v, %v) error = %v; wantErr %v",
					tt.{{INPUT_PARAM_1}}, tt.{{INPUT_PARAM_2}}, err, tt.wantErr)
				return
			}

			// Check value (only if no error expected)
			if !tt.wantErr && got != tt.want {
				t.Errorf("{{FUNCTION_NAME}}(%v, %v) = %v; want %v",
					tt.{{INPUT_PARAM_1}}, tt.{{INPUT_PARAM_2}}, got, tt.want)
			}
		})
	}
}

// Test{{FUNCTION_NAME}}_SpecificError tests for specific error types.
func Test{{FUNCTION_NAME}}_SpecificError(t *testing.T) {
	// Act
	_, err := {{FUNCTION_NAME}}({{INVALID_INPUT}})

	// Assert - check error occurred
	if err == nil {
		t.Error("expected error for {{ERROR_CONDITION}}")
		return
	}

	// Assert - check specific error
	if !errors.Is(err, {{ERROR_TYPE}}) {
		t.Errorf("expected {{ERROR_TYPE}}; got %v", err)
	}
}
```

**Example:**

```go
package calculator

import (
	"errors"
	"testing"
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

// TestDivide_SpecificError tests for specific error types.
func TestDivide_SpecificError(t *testing.T) {
	// Act
	_, err := Divide(10, 0)

	// Assert - check error occurred
	if err == nil {
		t.Error("expected error for division by zero")
		return
	}

	// Assert - check specific error
	if !errors.Is(err, ErrDivisionByZero) {
		t.Errorf("expected ErrDivisionByZero; got %v", err)
	}
}
```

## Interface Mocking Template

Dependency injection with manual interface mocks:

```go
package {{TEST_PACKAGE_NAME}}

import "testing"

// Mock{{INTERFACE_NAME}} is a mock implementation of {{INTERFACE_NAME}}.
type Mock{{INTERFACE_NAME}} struct {
	{{METHOD_NAME_1}}Func func({{PARAMS_1}}) ({{RETURNS_1}})
	{{METHOD_NAME_2}}Func func({{PARAMS_2}}) ({{RETURNS_2}})
}

// {{METHOD_NAME_1}} implements {{INTERFACE_NAME}}.{{METHOD_NAME_1}}.
func (m *Mock{{INTERFACE_NAME}}) {{METHOD_NAME_1}}({{PARAMS_1}}) ({{RETURNS_1}}) {
	if m.{{METHOD_NAME_1}}Func != nil {
		return m.{{METHOD_NAME_1}}Func({{PARAM_NAMES_1}})
	}
	return {{ZERO_VALUES_1}}
}

// {{METHOD_NAME_2}} implements {{INTERFACE_NAME}}.{{METHOD_NAME_2}}.
func (m *Mock{{INTERFACE_NAME}}) {{METHOD_NAME_2}}({{PARAMS_2}}) ({{RETURNS_2}}) {
	if m.{{METHOD_NAME_2}}Func != nil {
		return m.{{METHOD_NAME_2}}Func({{PARAM_NAMES_2}})
	}
	return {{ZERO_VALUES_2}}
}

// Test{{SERVICE_NAME}}_{{METHOD_NAME}} tests {{SERVICE_NAME}}.{{METHOD_NAME}} with mock dependencies.
func Test{{SERVICE_NAME}}_{{METHOD_NAME}}(t *testing.T) {
	// Arrange
	mock{{DEPENDENCY}} := &Mock{{INTERFACE_NAME}}{
		{{METHOD_NAME_1}}Func: func({{PARAMS_1}}) ({{RETURNS_1}}) {
			// Mock behavior
			{{MOCK_IMPLEMENTATION}}
		},
	}
	service := New{{SERVICE_NAME}}(mock{{DEPENDENCY}})

	// Act
	result, err := service.{{METHOD_NAME}}({{TEST_INPUT}})

	// Assert
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if result != {{EXPECTED_VALUE}} {
		t.Errorf("got %v; want %v", result, {{EXPECTED_VALUE}})
	}
}
```

**Example:**

```go
package user

import (
	"errors"
	"testing"
)

var ErrUserNotFound = errors.New("user not found")

// MockUserRepository is a mock implementation of UserRepository.
type MockUserRepository struct {
	GetUserFunc  func(id string) (*User, error)
	SaveUserFunc func(user *User) error
}

// GetUser implements UserRepository.GetUser.
func (m *MockUserRepository) GetUser(id string) (*User, error) {
	if m.GetUserFunc != nil {
		return m.GetUserFunc(id)
	}
	return nil, nil
}

// SaveUser implements UserRepository.SaveUser.
func (m *MockUserRepository) SaveUser(user *User) error {
	if m.SaveUserFunc != nil {
		return m.SaveUserFunc(user)
	}
	return nil
}

// TestUserService_GetUser tests UserService.GetUser with mock repository.
func TestUserService_GetUser(t *testing.T) {
	// Arrange
	mockRepo := &MockUserRepository{
		GetUserFunc: func(id string) (*User, error) {
			if id == "123" {
				return &User{ID: "123", Name: "Alice"}, nil
			}
			return nil, ErrUserNotFound
		},
	}
	service := NewUserService(mockRepo)

	t.Run("existing user", func(t *testing.T) {
		// Act
		user, err := service.GetUser("123")

		// Assert
		if err != nil {
			t.Errorf("unexpected error: %v", err)
		}
		if user.Name != "Alice" {
			t.Errorf("got %s; want Alice", user.Name)
		}
	})

	t.Run("non-existent user", func(t *testing.T) {
		// Act
		_, err := service.GetUser("999")

		// Assert
		if err == nil {
			t.Error("expected error for non-existent user")
		}
		if !errors.Is(err, ErrUserNotFound) {
			t.Errorf("expected ErrUserNotFound; got %v", err)
		}
	})
}
```

## Cleanup Template

Resource cleanup using defer:

```go
package {{TEST_PACKAGE_NAME}}

import (
	"os"
	"testing"
)

// Test{{FUNCTION_NAME}}_WithCleanup tests {{FUNCTION_NAME}} with resource cleanup.
func Test{{FUNCTION_NAME}}_WithCleanup(t *testing.T) {
	// Arrange - create resource
	{{RESOURCE_NAME}}, err := {{CREATE_RESOURCE}}
	if err != nil {
		t.Fatalf("failed to create {{RESOURCE_TYPE}}: %v", err)
	}
	defer {{CLEANUP_FUNC}}({{RESOURCE_NAME}})  // Cleanup runs after test

	// Act
	result := {{FUNCTION_NAME}}({{RESOURCE_NAME}})

	// Assert
	if result != {{EXPECTED_VALUE}} {
		t.Errorf("got %v; want %v", result, {{EXPECTED_VALUE}})
	}
}

// Test{{FUNCTION_NAME}}_WithStateReset tests {{FUNCTION_NAME}} with state reset.
func Test{{FUNCTION_NAME}}_WithStateReset(t *testing.T) {
	// Arrange - save original state
	originalValue := {{GET_STATE}}
	defer {{SET_STATE}}(originalValue)  // Reset state after test

	// Arrange - modify state
	{{SET_STATE}}({{NEW_VALUE}})

	// Act
	result := {{FUNCTION_NAME}}()

	// Assert
	if result != {{EXPECTED_VALUE}} {
		t.Errorf("got %v; want %v", result, {{EXPECTED_VALUE}})
	}
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
			if result != {{EXPECTED_VALUE}} {
				t.Errorf("got %v; want %v", result, {{EXPECTED_VALUE}})
			}
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
)

// TestFileOperations_WithCleanup tests file operations with resource cleanup.
func TestFileOperations_WithCleanup(t *testing.T) {
	// Arrange - create temp file
	f, err := os.CreateTemp("", "test-*.txt")
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}
	defer os.Remove(f.Name())  // Cleanup file
	defer f.Close()            // Cleanup file handle

	// Arrange - write test data
	testData := "test data"
	_, err = f.WriteString(testData)
	if err != nil {
		t.Fatalf("failed to write: %v", err)
	}

	// Act
	content, err := os.ReadFile(f.Name())
	if err != nil {
		t.Fatalf("failed to read: %v", err)
	}

	// Assert
	if string(content) != testData {
		t.Errorf("got %s; want %s", content, testData)
	}
}

// TestConfig_WithStateReset tests config modification with state reset.
func TestConfig_WithStateReset(t *testing.T) {
	// Arrange - save original config
	originalValue := GetConfigValue("timeout")
	defer SetConfigValue("timeout", originalValue)  // Reset after test

	// Arrange - modify config
	SetConfigValue("timeout", "30s")

	// Act
	result := DoSomethingWithConfig()

	// Assert
	if result == nil {
		t.Error("expected non-nil result")
	}
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
			if err != nil {
				t.Fatalf("failed to create temp file: %v", err)
			}
			defer os.Remove(tempFile.Name())  // Each subtest cleans up its own file
			defer tempFile.Close()

			// Act
			result := ProcessFile(tempFile.Name(), tt.data)

			// Assert
			if !result {
				t.Errorf("ProcessFile failed for %s", tt.name)
			}
		})
	}
}
```

## Complete Example

Full test file demonstrating all patterns:

```go
package calculator

import (
	"errors"
	"testing"
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
	if result != expected {
		t.Errorf("Add(%d, %d) = %d; want %d", a, b, result, expected)
	}
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
			if got != tt.want {
				t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.want)
			}
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
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
	})

	t.Run("Subtraction", func(t *testing.T) {
		// Arrange
		a, b := 5, 3
		expected := 2

		// Act
		result := calc.Subtract(a, b)

		// Assert
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
	})

	t.Run("Multiplication", func(t *testing.T) {
		// Arrange
		a, b := 2, 3
		expected := 6

		// Act
		result := calc.Multiply(a, b)

		// Assert
		if result != expected {
			t.Errorf("got %d; want %d", result, expected)
		}
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

// TestDivide_SpecificError tests that Divide returns the correct error type.
func TestDivide_SpecificError(t *testing.T) {
	// Arrange
	calc := NewCalculator()

	// Act
	_, err := calc.Divide(10, 0)

	// Assert - check error occurred
	if err == nil {
		t.Error("expected error for division by zero")
		return
	}

	// Assert - check specific error
	if !errors.Is(err, ErrDivisionByZero) {
		t.Errorf("expected ErrDivisionByZero; got %v", err)
	}
}

// MockLogger is a mock implementation of Logger interface.
type MockLogger struct {
	LogFunc func(msg string)
	logs    []string
}

// Log implements Logger.Log.
func (m *MockLogger) Log(msg string) {
	if m.LogFunc != nil {
		m.LogFunc(msg)
	}
	m.logs = append(m.logs, msg)
}

// GetLogs returns all logged messages.
func (m *MockLogger) GetLogs() []string {
	return m.logs
}

// TestCalculator_WithLogger tests calculator with logging dependency.
func TestCalculator_WithLogger(t *testing.T) {
	// Arrange
	mockLogger := &MockLogger{}
	calc := NewCalculatorWithLogger(mockLogger)

	// Act
	result := calc.Add(2, 3)

	// Assert - check result
	if result != 5 {
		t.Errorf("got %d; want 5", result)
	}

	// Assert - check logging
	logs := mockLogger.GetLogs()
	if len(logs) == 0 {
		t.Error("expected at least one log entry")
	}
}
```

## Usage Guide

### Step 1: Choose the Right Template

- **Basic Test**: Single function, simple assertion
- **Table-Driven**: Multiple test cases for same function
- **Subtest**: Grouped tests for related functionality
- **Error Handling**: Functions that return errors
- **Mocking**: Functions with external dependencies
- **Cleanup**: Tests requiring resource management

### Step 2: Customize Placeholders

Replace all `{{PLACEHOLDER}}` values with your specific names:

1. Package names (`{{PACKAGE_NAME}}`, `{{TEST_PACKAGE_NAME}}`)
2. Function/method names (`{{FUNCTION_NAME}}`, `{{METHOD_NAME}}`)
3. Type names (`{{TYPE_NAME}}`, `{{INTERFACE_NAME}}`)
4. Input/output values (`{{INPUT_VALUE}}`, `{{EXPECTED_VALUE}}`)
5. Parameters and types (`{{PARAMS}}`, `{{TYPE}}`)

### Step 3: Adjust Test Logic

1. Modify assertion logic based on return types
2. Add or remove test cases as needed
3. Adjust error handling based on your error types
4. Update mock implementations for your interfaces

### Step 4: Run Tests

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

1. **Use descriptive test names**: `Test{Function}_{Scenario}_{ExpectedBehavior}`
2. **Keep tests independent**: No shared state between tests
3. **Use t.Helper()** in test helper functions
4. **Prefer table-driven tests**: Easier to maintain and extend
5. **Test error paths**: Don't just test happy paths
6. **Use errors.Is()**: For error comparison with Go 1.13+
7. **Clean up resources**: Use defer for cleanup
8. **Document complex tests**: Add comments explaining why, not what

### Common Patterns

**Testing for nil:**
```go
if result == nil {
	t.Error("expected non-nil result")
}
```

**Testing slices/maps:**
```go
import "reflect"

if !reflect.DeepEqual(got, want) {
	t.Errorf("got %v; want %v", got, want)
}
```

**Testing panics:**
```go
defer func() {
	if r := recover(); r == nil {
		t.Error("expected panic")
	}
}()
```

**Skipping tests:**
```go
if testing.Short() {
	t.Skip("skipping test in short mode")
}
```

**Test helpers:**
```go
func assertEqual(t *testing.T, got, want interface{}) {
	t.Helper()  // Correct line numbers in failures
	if got != want {
		t.Errorf("got %v; want %v", got, want)
	}
}
```

## References

- Go testing package: https://pkg.go.dev/testing
- Table-driven tests: https://go.dev/wiki/TableDrivenTests
- Go patterns document: `skills/test-generation/go-patterns.md`

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
