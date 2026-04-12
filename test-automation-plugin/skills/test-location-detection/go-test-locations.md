# Go Test Location Detection

**Language**: Go
**Framework**: go test (standard library)
**Version**: 1.0.0

---

## Overview

Go test location conventions follow the `go test` tool's requirements for test discovery. Unlike many languages, Go tests reside alongside source files in the same directory and package. This document provides guidance for determining correct test file locations in Go projects.

---

## Configuration Sources (Priority Order)

### 1. go.mod File

**Location**: Module root
**Purpose**: Defines module path and Go version

```go
module github.com/username/calculator

go 1.21

require (
    github.com/stretchr/testify v1.8.4
)
```

**Detection Strategy**:
- Find `go.mod` file by walking up directory tree
- Module root is where `go.mod` is located
- All tests use same module path
- Package paths are relative to module root

---

### 2. Package Declaration

**Location**: First line of Go source file
**Purpose**: Defines package name and test package suffix

```go
// Source file: calculator.go
package calculator

// White-box test file: calculator_test.go
package calculator

// Black-box test file: calculator_test.go
package calculator_test
```

**Package Naming Rules**:
- **White-box tests**: Same package as source (can access unexported symbols)
- **Black-box tests**: Package name + `_test` suffix (only exported API)

---

## Default Conventions

### Standard Go Convention (Most Common)

**Structure**:
```
calculator/
├── go.mod
├── calculator.go
├── calculator_test.go
├── operations/
│   ├── add.go
│   ├── add_test.go
│   ├── divide.go
│   └── divide_test.go
└── internal/
    ├── helpers.go
    └── helpers_test.go
```

**Naming Pattern**:
- Test files: `*_test.go` (suffix is mandatory)
- Test functions: `func Test*(t *testing.T)`
- Benchmark functions: `func Benchmark*(b *testing.B)`
- Example functions: `func Example*()`
- Tests are in same directory as source files

---

### White-box vs Black-box Testing

**White-box Testing (Same Package)**:
```go
// calculator.go
package calculator

func add(a, b int) int { return a + b }  // unexported

// calculator_test.go
package calculator  // Same package

import "testing"

func TestAdd(t *testing.T) {
    result := add(2, 3)  // Can access unexported function
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}
```

**Black-box Testing (Package_test)**:
```go
// calculator.go
package calculator

func Add(a, b int) int { return a + b }  // exported

// calculator_test.go
package calculator_test  // Different package with _test suffix

import (
    "testing"
    "github.com/username/calculator"
)

func TestAdd(t *testing.T) {
    result := calculator.Add(2, 3)  // Only access exported API
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}
```

**When to Use Each**:
- **White-box**: Testing internal implementation, private functions, package internals
- **Black-box**: Testing public API, ensuring exported interface works correctly

---

### Table-driven Test Organization

**Standard Pattern**:
```go
// calculator_test.go
package calculator

import "testing"

func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -2, -3, -5},
        {"mixed numbers", -2, 3, 1},
        {"zeros", 0, 0, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Add(tt.a, tt.b)
            if result != tt.expected {
                t.Errorf("Add(%d, %d) = %d; want %d",
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}
```

**File Location**: Same directory as source file being tested

---

## Test File Naming

### File Naming Rules

**Pattern**: `*_test.go` (mandatory suffix)

**Examples**:
- `calculator.go` → `calculator_test.go`
- `add.go` → `add_test.go`
- `user_service.go` → `user_service_test.go`

**Multiple Test Files** (for large packages):
- `calculator.go` → `calculator_test.go` (main tests)
- `calculator_benchmark_test.go` (benchmarks)
- `calculator_integration_test.go` (integration tests)
- `calculator_example_test.go` (examples)

**Rule**: All test files must end with `_test.go`

---

## Test File Location

### Core Principle

**Tests are always in the same directory as the source code they test.**

```
package/
├── source.go        ← Source file
└── source_test.go   ← Test file (same directory)
```

**NOT separate directories like other languages**:
```
DON'T DO THIS (This is NOT Go convention):
project/
├── src/
│   └── calculator.go
└── tests/
    └── calculator_test.go  ❌ Wrong!
```

---

### Package Directory Structure

```
calculator/
├── go.mod
├── go.sum
├── README.md
├── calculator.go           ← Main source file
├── calculator_test.go      ← Main test file
├── doc.go                  ← Package documentation
├── operations/             ← Subpackage
│   ├── add.go
│   ├── add_test.go
│   ├── divide.go
│   ├── divide_test.go
│   └── multiply.go
│   └── multiply_test.go
└── internal/               ← Internal package (not importable outside module)
    ├── helpers.go
    └── helpers_test.go
```

**Key Points**:
- Each package directory contains its own test files
- Subpackages have their own test files in their directories
- No separate `test/` or `tests/` directory

---

## Black-box vs White-box Testing

### White-box Tests (Same Package)

**Purpose**: Test internal implementation details

**File Structure**:
```go
// calculator.go
package calculator

type calculator struct {
    memory int  // unexported field
}

func (c *calculator) add(a, b int) int {  // unexported method
    return a + b
}

// calculator_internal_test.go
package calculator  // Same package!

import "testing"

func TestCalculatorInternals(t *testing.T) {
    c := calculator{memory: 0}  // Can access unexported type
    result := c.add(2, 3)        // Can call unexported method
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}
```

**Characteristics**:
- Package declaration: `package packagename`
- Can access unexported (lowercase) functions, types, fields
- No import of the package being tested
- Tests implementation details

---

### Black-box Tests (Package_test)

**Purpose**: Test public API only

**File Structure**:
```go
// calculator.go
package calculator

type Calculator struct {
    Memory int  // exported field
}

func (c *Calculator) Add(a, b int) int {  // exported method
    return a + b
}

// calculator_api_test.go
package calculator_test  // Note the _test suffix!

import (
    "testing"
    "github.com/username/calculator"
)

func TestCalculatorAPI(t *testing.T) {
    c := calculator.Calculator{Memory: 0}
    result := c.Add(2, 3)
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}
```

**Characteristics**:
- Package declaration: `package packagename_test`
- Must import the package being tested
- Only access exported (uppercase) symbols
- Tests public API contract

---

### Mixing White-box and Black-box Tests

**Common Pattern**: Multiple test files in same directory

```
calculator/
├── calculator.go
├── calculator_test.go          ← White-box tests (package calculator)
└── calculator_external_test.go ← Black-box tests (package calculator_test)
```

```go
// calculator_test.go (white-box)
package calculator

func TestInternalHelpers(t *testing.T) {
    // Test unexported functions
}

// calculator_external_test.go (black-box)
package calculator_test

func TestPublicAPI(t *testing.T) {
    // Test exported API only
}
```

---

## Example Tests Placement

### Example Functions

**Purpose**: Executable examples in documentation

**Naming Convention**:
```go
func Example()        // Example for entire package
func ExampleAdd()     // Example for Add function
func ExampleAdd_second() // Second example for Add
func Example_custom() // Custom example name
```

**File Location**: Same directory as source, in `*_test.go` file

```go
// calculator_test.go or calculator_example_test.go
package calculator_test

import "fmt"

func ExampleAdd() {
    result := calculator.Add(2, 3)
    fmt.Println(result)
    // Output: 5
}

func ExampleCalculator() {
    c := calculator.New()
    result := c.Add(2, 3)
    fmt.Println(result)
    // Output: 5
}
```

**File Organization Options**:
1. In main test file: `calculator_test.go`
2. Separate file: `calculator_example_test.go` (recommended for many examples)

---

## Benchmark Tests Placement

### Benchmark Functions

**Purpose**: Performance testing

**Naming Convention**:
```go
func BenchmarkAdd(b *testing.B)
func BenchmarkCalculator_Add(b *testing.B)
```

**File Location**: Same directory as source, in `*_test.go` file

```go
// calculator_test.go or calculator_benchmark_test.go
package calculator

import "testing"

func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(2, 3)
    }
}

func BenchmarkAddParallel(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            Add(2, 3)
        }
    })
}
```

**File Organization Options**:
1. In main test file: `calculator_test.go`
2. Separate file: `calculator_benchmark_test.go` (recommended for many benchmarks)

---

## Module Structure

### Single Module Project

```
calculator/
├── go.mod              ← Module root
├── go.sum
├── calculator.go
├── calculator_test.go
├── operations/
│   ├── add.go
│   ├── add_test.go
│   ├── divide.go
│   └── divide_test.go
└── internal/
    ├── helpers.go
    └── helpers_test.go
```

**Module Path**: `github.com/username/calculator`
**Package Paths**:
- Root: `github.com/username/calculator`
- Subpackage: `github.com/username/calculator/operations`
- Internal: `github.com/username/calculator/internal`

---

### Multi-package Module

```
mathlib/
├── go.mod              ← Module root: github.com/username/mathlib
├── calculator/
│   ├── calculator.go
│   └── calculator_test.go
├── geometry/
│   ├── circle.go
│   ├── circle_test.go
│   ├── square.go
│   └── square_test.go
└── statistics/
    ├── mean.go
    └── mean_test.go
```

**Module Path**: `github.com/username/mathlib`
**Package Paths**:
- `github.com/username/mathlib/calculator`
- `github.com/username/mathlib/geometry`
- `github.com/username/mathlib/statistics`

**Test Organization**: Each package has test files in same directory

---

### Internal Packages

**Purpose**: Prevent external imports

```
calculator/
├── go.mod
├── calculator.go
├── calculator_test.go
└── internal/           ← Not importable outside this module
    ├── helpers.go
    └── helpers_test.go
```

**Import Rules**:
- Code in `calculator/` can import `calculator/internal`
- Code outside the module **cannot** import `calculator/internal`
- Test files in `internal/` directory test internal package code

---

## Detection Algorithm

### Step 1: Identify Source File

**Input**: `d:\dev\calculator\operations\add.go`

**Extract**:
- Filename: `add.go`
- Directory: `d:\dev\calculator\operations\`
- Base name: `add`

---

### Step 2: Construct Test Filename

**Pattern**: `{basename}_test.go`

**Examples**:
- `add.go` → `add_test.go`
- `calculator.go` → `calculator_test.go`
- `user_service.go` → `user_service_test.go`

**Result**: `add_test.go`

---

### Step 3: Determine Test File Path

**Rule**: Same directory as source file

**Calculation**:
- Source file: `d:\dev\calculator\operations\add.go`
- Test file: `d:\dev\calculator\operations\add_test.go`

**Simple Algorithm**:
```
testPath = sourceDirectory + basename + "_test.go"
```

---

### Step 4: Determine Package Declaration

**Read source file first line**:
```go
package operations
```

**Test package options**:

**Option 1 (White-box)**:
```go
package operations
```

**Option 2 (Black-box)**:
```go
package operations_test
```

**Default**: Use same package (white-box) unless specifically testing public API

---

### Step 5: Validate Location

**Valid Test File Checklist**:
- ✅ Filename ends with `_test.go`
- ✅ In same directory as source file
- ✅ Within Go module (has go.mod in parent path)
- ✅ Package declaration matches source or has `_test` suffix

**Invalid Locations**:
- ❌ Separate `test/` or `tests/` directory
- ❌ `.claude-tests/` directory
- ❌ Outside module root
- ❌ Wrong package name

---

## Path Resolution Algorithm

### Complete Algorithm

```go
// Pseudocode for Go test location detection

function DetermineTestPath(sourceFile string) string {
    // Step 1: Validate source file
    if !strings.HasSuffix(sourceFile, ".go") {
        return error("Not a Go source file")
    }

    if strings.HasSuffix(sourceFile, "_test.go") {
        return error("Already a test file")
    }

    // Step 2: Extract components
    dir := filepath.Dir(sourceFile)
    filename := filepath.Base(sourceFile)
    basename := strings.TrimSuffix(filename, ".go")

    // Step 3: Construct test filename
    testFilename := basename + "_test.go"

    // Step 4: Construct test path (same directory!)
    testPath := filepath.Join(dir, testFilename)

    // Step 5: Validate within module
    if !isInGoModule(testPath) {
        return error("Not in a Go module")
    }

    // Step 6: Validate not in vendor or .claude directories
    if strings.Contains(testPath, "/vendor/") ||
       strings.Contains(testPath, "\\.claude") {
        return error("Invalid test location")
    }

    return testPath
}

function determinePackageName(sourceFile string) string {
    // Read first line of source file
    packageLine := readFirstLine(sourceFile)
    // Extract: "package calculator" → "calculator"
    packageName := extractPackageName(packageLine)

    // Default: white-box testing (same package)
    return packageName

    // For black-box testing, append "_test":
    // return packageName + "_test"
}

function isInGoModule(path string) bool {
    // Walk up directory tree looking for go.mod
    current := filepath.Dir(path)
    for current != "/" && current != "." {
        if fileExists(filepath.Join(current, "go.mod")) {
            return true
        }
        current = filepath.Dir(current)
    }
    return false
}
```

---

## Common Project Structures

### Structure 1: Standard Library Style (Recommended)

```
calculator/
├── go.mod
├── calculator.go
├── calculator_test.go
├── doc.go
├── operations/
│   ├── add.go
│   ├── add_test.go
│   ├── subtract.go
│   ├── subtract_test.go
│   ├── multiply.go
│   ├── multiply_test.go
│   ├── divide.go
│   └── divide_test.go
└── internal/
    ├── parser.go
    └── parser_test.go
```

**Path Resolution Examples**:

**Example 1**:
- Source: `calculator.go`
- Test: `calculator_test.go` (same directory)

**Example 2**:
- Source: `operations/add.go`
- Test: `operations/add_test.go` (same directory)

**Example 3**:
- Source: `internal/parser.go`
- Test: `internal/parser_test.go` (same directory)

---

### Structure 2: Command with Library

```
calculator/
├── go.mod
├── main.go             ← Entry point
├── main_test.go
├── cmd/
│   └── server/
│       ├── server.go
│       └── server_test.go
└── pkg/
    ├── calculator/
    │   ├── calculator.go
    │   └── calculator_test.go
    └── parser/
        ├── parser.go
        └── parser_test.go
```

**Path Resolution**:
- Source: `pkg/calculator/calculator.go`
- Test: `pkg/calculator/calculator_test.go`

---

### Structure 3: Microservice

```
calculator-service/
├── go.mod
├── main.go
├── main_test.go
├── api/
│   ├── handlers.go
│   ├── handlers_test.go
│   ├── middleware.go
│   └── middleware_test.go
├── service/
│   ├── calculator.go
│   └── calculator_test.go
└── internal/
    ├── config/
    │   ├── config.go
    │   └── config_test.go
    └── database/
        ├── db.go
        └── db_test.go
```

**Pattern**: Every `.go` file has corresponding `_test.go` in same directory

---

## Edge Cases

### Case 1: Multiple Test Files for One Source File

**Source**:
```
calculator/
└── calculator.go
```

**Tests** (all valid in same directory):
```
calculator/
├── calculator.go
├── calculator_test.go          ← Main tests
├── calculator_benchmark_test.go ← Benchmarks
├── calculator_example_test.go   ← Examples
└── calculator_integration_test.go ← Integration tests
```

**Rule**: Multiple `*_test.go` files can exist for organization

---

### Case 2: Internal Packages

**Source**:
```
calculator/
├── go.mod
├── calculator.go
└── internal/
    ├── helpers.go
    └── parser.go
```

**Tests**:
```
calculator/
├── go.mod
├── calculator.go
├── calculator_test.go
└── internal/
    ├── helpers.go
    ├── helpers_test.go    ← Test internal package
    ├── parser.go
    └── parser_test.go     ← Test internal package
```

**Rule**: Internal packages have tests in same directory, not importable outside

---

### Case 3: Vendor Directory

**Structure**:
```
calculator/
├── go.mod
├── calculator.go
├── calculator_test.go
└── vendor/
    └── github.com/...
```

**Rule**: **Never create or modify test files in vendor directory**
- Vendor contains third-party dependencies
- Tests for vendored code stay with vendor
- Don't add tests to vendor directory

---

### Case 4: Generated Code

**Source**:
```
calculator/
├── calculator.go
├── calculator_test.go
├── calculator.pb.go        ← Generated (protobuf)
└── calculator.pb_test.go   ← Tests for generated code
```

**Rule**: Generated code can have tests, same naming convention applies

---

### Case 5: Build Tags / Conditional Compilation

**Different test files for different platforms**:
```
calculator/
├── calculator.go
├── calculator_test.go
├── calculator_linux_test.go    ← //go:build linux
├── calculator_windows_test.go  ← //go:build windows
└── calculator_darwin_test.go   ← //go:build darwin
```

**Rule**: Platform-specific tests still in same directory, use build tags

---

## File Naming Patterns

### Test File Naming

**Pattern**: `*_test.go` (mandatory)

**Examples**:
- `calculator.go` → `calculator_test.go`
- `add.go` → `add_test.go`
- `user_service.go` → `user_service_test.go`
- `http_client.go` → `http_client_test.go`

**Multiple Test Files**:
- `calculator_test.go` (main tests)
- `calculator_integration_test.go` (integration)
- `calculator_benchmark_test.go` (benchmarks)
- `calculator_example_test.go` (examples)

---

### Test Function Naming

**Test Functions**: `func Test*(t *testing.T)`
```go
func TestAdd(t *testing.T)
func TestCalculator_Add(t *testing.T)  // Method test
func TestAdd_NegativeNumbers(t *testing.T)  // Specific case
```

**Benchmark Functions**: `func Benchmark*(b *testing.B)`
```go
func BenchmarkAdd(b *testing.B)
func BenchmarkCalculator_Add(b *testing.B)
```

**Example Functions**: `func Example*()`
```go
func Example()           // Package example
func ExampleAdd()        // Function example
func ExampleCalculator() // Type example
func ExampleCalculator_Add() // Method example
```

---

## Validation Rules

### ✅ Valid Locations

- `calculator/calculator_test.go` (same directory as source)
- `operations/add_test.go` (subpackage, same directory)
- `internal/helpers_test.go` (internal package, same directory)
- `pkg/math/calculator_test.go` (nested structure, same directory)
- `calculator/calculator_benchmark_test.go` (benchmarks, same directory)

---

### 🚫 Invalid Locations

- `test/calculator_test.go` ❌ (separate test directory - not Go convention)
- `tests/calculator_test.go` ❌ (separate tests directory)
- `.claude-tests/calculator_test.go` ❌ (temp directory)
- `calculator/test/calculator_test.go` ❌ (nested test directory)
- `vendor/pkg/calculator_test.go` ❌ (in vendor)
- `calculator.go.test` ❌ (wrong suffix)
- `test_calculator.go` ❌ (prefix instead of suffix)

---

## Tool Integration

### Write Agent Integration

```go
// Pseudocode for Write Agent

function DetermineTestPath(sourceFile, projectRoot) {
    // Step 1: Validate input
    if !strings.HasSuffix(sourceFile, ".go") {
        throw new InvalidFileException("Not a Go source file")
    }

    if strings.HasSuffix(sourceFile, "_test.go") {
        throw new InvalidFileException("Source file is already a test file")
    }

    // Step 2: Extract directory and filename
    sourceDir := filepath.Dir(sourceFile)
    sourceFilename := filepath.Base(sourceFile)
    baseName := strings.TrimSuffix(sourceFilename, ".go")

    // Step 3: Construct test filename
    testFilename := baseName + "_test.go"

    // Step 4: Test file is in SAME directory (Go convention)
    testPath := filepath.Join(sourceDir, testFilename)

    // Step 5: Validate within Go module
    if !hasGoModInParentPath(testPath) {
        throw new InvalidPathException("Not in a Go module")
    }

    // Step 6: Validate not in vendor or .claude directories
    if strings.Contains(testPath, "/vendor/") ||
       strings.Contains(testPath, "/.claude") ||
       strings.Contains(testPath, "\\.claude") {
        throw new InvalidPathException("Invalid test location")
    }

    // Step 7: Return test path
    return testPath
}

function determinePackageDeclaration(sourceFile) {
    // Read source file to get package name
    content := readFile(sourceFile)
    packageLine := extractPackageLine(content)
    packageName := extractPackageName(packageLine)

    // Default to white-box testing (same package)
    return "package " + packageName

    // For black-box testing (optional):
    // return "package " + packageName + "_test"
}

function hasGoModInParentPath(path) {
    current := filepath.Dir(path)
    for current != "/" && current != "." {
        goModPath := filepath.Join(current, "go.mod")
        if fileExists(goModPath) {
            return true
        }
        current = filepath.Dir(current)
    }
    return false
}
```

---

### Integration Example

```go
// Example: Create test file for calculator.go

sourceFile := "d:/dev/calculator/operations/add.go"
projectRoot := "d:/dev/calculator"

// Determine test path
testPath := DetermineTestPath(sourceFile, projectRoot)
// Result: "d:/dev/calculator/operations/add_test.go"

// Determine package
packageDecl := determinePackageDeclaration(sourceFile)
// Result: "package operations"

// Create test file
testContent := packageDecl + "\n\n" +
    "import \"testing\"\n\n" +
    "func TestAdd(t *testing.T) {\n" +
    "    // TODO: Implement test\n" +
    "}\n"

writeFile(testPath, testContent)
```

---

## Examples

### Example 1: Root Package File

**Input**:
- Source: `d:\dev\calculator\calculator.go`
- Project root: `d:\dev\calculator\`
- Module: `github.com/username/calculator`

**Output**:
- Test: `d:\dev\calculator\calculator_test.go` (same directory)
- Package: `package calculator` or `package calculator_test`

---

### Example 2: Subpackage File

**Input**:
- Source: `d:\dev\calculator\operations\add.go`
- Project root: `d:\dev\calculator\`
- Module: `github.com/username/calculator`

**Output**:
- Test: `d:\dev\calculator\operations\add_test.go` (same directory)
- Package: `package operations` or `package operations_test`

---

### Example 3: Internal Package File

**Input**:
- Source: `d:\dev\calculator\internal\parser\parser.go`
- Project root: `d:\dev\calculator\`
- Module: `github.com/username/calculator`

**Output**:
- Test: `d:\dev\calculator\internal\parser\parser_test.go` (same directory)
- Package: `package parser` or `package parser_test`

---

### Example 4: Nested Package Structure

**Input**:
- Source: `d:\dev\mathlib\pkg\geometry\shapes\circle.go`
- Project root: `d:\dev\mathlib\`
- Module: `github.com/username/mathlib`

**Output**:
- Test: `d:\dev\mathlib\pkg\geometry\shapes\circle_test.go` (same directory)
- Package: `package shapes` or `package shapes_test`

---

## Summary

**Key Principles**:
1. Go tests are **always in the same directory** as source files
2. Test file naming: `{basename}_test.go` (mandatory `_test.go` suffix)
3. No separate test directories (unlike C#, Python, etc.)
4. Package naming: same package (white-box) or `{package}_test` (black-box)
5. Test functions: `func Test*(t *testing.T)`
6. **NEVER use separate test directories or `.claude-tests/`**
7. All tests within same Go module (go.mod)

**Test Discovery**:
- `go test` finds all `*_test.go` files in current directory
- `go test ./...` finds all test files in module recursively
- Tests must be in same directory as source to be associated correctly

**Package Conventions**:
- **White-box** (`package foo`): Access unexported symbols, test internals
- **Black-box** (`package foo_test`): Only exported API, test public contract
- Can mix both in same directory with different test files

**Priority Algorithm**:
1. Extract source file directory
2. Construct test filename: `{basename}_test.go`
3. Place test in **same directory** as source
4. Validate within Go module (has go.mod in parent)
5. Validate not in vendor or .claude directories

**Go-Specific Rules**:
- Tests are co-located with source (not separated)
- `_test.go` suffix is mandatory for `go test` to find tests
- Package `_test` suffix enables black-box testing
- Examples and benchmarks use same location pattern

---

**Last Updated**: 2025-12-11
**Status**: Phase 4 - Systems Languages
**Phase**: Complete
