# Go Framework Detection

**Version**: 1.0.0
**Language**: Go
**Frameworks**: testing (built-in), testify
**Status**: Phase 4 - Systems Languages

## Overview

Go framework detection skill for identifying Go's built-in `testing` package and the popular `testify` assertion library in Go projects. This skill provides detailed detection patterns, confidence scoring, and Go-specific configuration analysis.

## Supported Frameworks

### 1. testing (Built-in)

**Description**: Go's standard library testing package
**Official Docs**: https://pkg.go.dev/testing
**Minimum Version**: N/A (part of standard library since Go 1.0)
**Detection Priority**: Always available (default)

**Key Features**:
- `func TestXxx(t *testing.T)` test functions
- `func BenchmarkXxx(b *testing.B)` benchmark functions
- `func ExampleXxx()` example functions
- Table-driven tests pattern
- Subtests with `t.Run()`
- No external dependencies required

### 2. testify

**Description**: Popular assertion and mocking library for Go
**Official Docs**: https://github.com/stretchr/testify
**Minimum Version**: v1.7.0+
**Detection Priority**: High (when present, indicates enhanced testing)

**Key Features**:
- `assert` package for assertions
- `require` package for assertions that stop test execution
- `suite` package for test suites
- `mock` package for mocking
- Rich assertion methods (Equal, Contains, NoError, etc.)
- Compatible with standard `testing` package

## Detection Patterns

### Built-in testing Detection

Go's `testing` package is always available (part of standard library), so detection focuses on identifying test files and test patterns.

#### 1. Test File Pattern (Weight: 10)

**Pattern**: Files ending in `_test.go`

```
calculator_test.go
utils_test.go
integration_test.go
```

**Detection Logic**:
```go
// Pseudocode for detection
testFiles = glob("**/*_test.go")

if len(testFiles) > 0:
    score += 10
    evidence.append($"{len(testFiles)} test files found (*_test.go)")

    for file in testFiles:
        evidence.append($"Test file: {file}")
```

#### 2. Test Function Patterns (Weight: 8)

**Test Functions**:
```go
package calculator

import "testing"

func TestAdd(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2, 3) = %d; want 5", result)
    }
}

func TestDivide(t *testing.T) {
    tests := []struct {
        name string
        a, b float64
        want float64
    }{
        {"positive", 10, 2, 5},
        {"negative", -10, 2, -5},
        {"float", 7.5, 2.5, 3},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Divide(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("Divide(%v, %v) = %v; want %v", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

**Detection Regex Patterns**:
```go
patterns = [
    @"func\s+Test\w+\s*\(\s*t\s+\*testing\.T\s*\)",  // Test function signature
    @"func\s+Benchmark\w+\s*\(\s*b\s+\*testing\.B\s*\)",  // Benchmark function
    @"func\s+Example\w+\s*\(\s*\)",  // Example function
    @"t\.Run\(",  // Subtest
    @"t\.Error\(",  // Test error
    @"t\.Errorf\(",  // Test error with formatting
    @"t\.Fatal\(",  // Test fatal error
    @"t\.Fatalf\(",  // Test fatal error with formatting
    @"t\.Log\(",  // Test logging
]

// Scan *_test.go files
foreach file in glob("**/*_test.go"):
    content = read(file)

    foreach pattern in patterns:
        if regex_match(pattern, content):
            score += 8
            evidence.append($"Pattern '{pattern}' found in {file}")
            break  // Count once per file
```

#### 3. Import Patterns (Weight: 5)

```go
import "testing"
import (
    "testing"
)
```

**Detection Logic**:
```go
foreach file in glob("**/*_test.go"):
    content = read(file)

    if regex_match(@'import\s+"testing"', content) ||
       regex_match(@'import\s+\([^)]*"testing"[^)]*\)', content):
        score += 5
        evidence.append($"'import \"testing\"' in {file}")
        break  // Count once across all files
```

### testify Detection

#### 1. go.mod Dependency (Weight: 15)

**go.mod** with testify dependency:
```
module github.com/example/myproject

go 1.21

require (
    github.com/stretchr/testify v1.8.4
)
```

**Detection Logic**:
```go
if exists("go.mod"):
    content = read("go.mod")

    // Match testify dependency
    match = regex_search(@'github\.com/stretchr/testify\s+v([0-9.]+)', content)

    if match:
        version = match.group(1)
        score += 15
        evidence.append($"go.mod contains github.com/stretchr/testify v{version}")
```

#### 2. Import Patterns (Weight: 8)

**testify Imports**:
```go
package calculator_test

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/stretchr/testify/suite"
    "github.com/stretchr/testify/mock"
)
```

**Detection Logic**:
```go
testifyPackages = [
    "github.com/stretchr/testify/assert",
    "github.com/stretchr/testify/require",
    "github.com/stretchr/testify/suite",
    "github.com/stretchr/testify/mock",
]

foreach file in glob("**/*_test.go"):
    content = read(file)

    foreach pkg in testifyPackages:
        if contains(content, pkg):
            score += 8
            evidence.append($"Import '{pkg}' in {file}")
            break  // Count once per file
```

#### 3. Code Patterns (Weight: 5)

**testify Assertion Examples**:
```go
func TestCalculator(t *testing.T) {
    // assert package
    assert.Equal(t, 5, Add(2, 3))
    assert.NotNil(t, result)
    assert.NoError(t, err)
    assert.Contains(t, list, item)

    // require package (stops on failure)
    require.NoError(t, err)
    require.NotEmpty(t, result)

    // suite package
    suite.Run(t, new(CalculatorTestSuite))
}

// Test suite example
type CalculatorTestSuite struct {
    suite.Suite
    calc *Calculator
}

func (s *CalculatorTestSuite) SetupTest() {
    s.calc = NewCalculator()
}

func (s *CalculatorTestSuite) TestAddition() {
    s.Equal(5, s.calc.Add(2, 3))
}
```

**Detection Regex Patterns**:
```go
patterns = [
    @"assert\.\w+\(",  // assert.Equal, assert.NotNil, etc.
    @"require\.\w+\(",  // require.NoError, require.NotEmpty, etc.
    @"suite\.Run\(",  // suite.Run
    @"suite\.Suite",  // suite.Suite embedding
    @"mock\.\w+",  // mock package usage
]

foreach file in glob("**/*_test.go"):
    content = read(file)

    foreach pattern in patterns:
        if regex_match(pattern, content):
            score += 5
            evidence.append($"testify pattern '{pattern}' found in {file}")
            break  // Count once per file
```

## Go Module Structure Analysis

### go.mod Parsing

**go.mod Structure**:
```
module github.com/example/calculator

go 1.21

require (
    github.com/stretchr/testify v1.8.4
)

require (
    github.com/davecgh/go-spew v1.1.1 // indirect
    github.com/pmezard/go-difflib v1.0.0 // indirect
    gopkg.in/yaml.v3 v3.0.1 // indirect
)
```

**Parsing Logic**:
```go
function parseGoMod(goModPath):
    content = read(goModPath)

    // Extract module name
    moduleMatch = regex_search(@"module\s+([^\s]+)", content)
    moduleName = moduleMatch.group(1) if moduleMatch else null

    // Extract Go version
    goVersionMatch = regex_search(@"go\s+([0-9.]+)", content)
    goVersion = goVersionMatch.group(1) if goVersionMatch else null

    // Extract dependencies
    dependencies = []
    requireMatches = regex_findall(@"([^\s]+)\s+v([0-9.]+)", content)

    foreach match in requireMatches:
        packageName = match[0]
        version = match[1]

        dependencies.append({
            name: packageName,
            version: version,
            isTestify: packageName.contains("stretchr/testify")
        })

    return {
        moduleName: moduleName,
        goVersion: goVersion,
        dependencies: dependencies
    }
```

**Go Version Support**:
- `go 1.21` → Go 1.21 (latest stable)
- `go 1.20` → Go 1.20
- `go 1.19` → Go 1.19
- `go 1.18` → Go 1.18 (introduced generics)

## Test File Pattern Detection

### Naming Conventions

**Test Files**:
- Pattern: `*_test.go`
- Location: Same directory as source files
- Package: `package foo` or `package foo_test` (black-box testing)

**Examples**:
```
calculator/
├── calculator.go       (package calculator)
├── calculator_test.go  (package calculator or package calculator_test)
└── utils.go            (package calculator)
```

**Detection Logic**:
```go
function detectTestFiles(projectPath):
    testFiles = glob($"{projectPath}/**/*_test.go")

    testInfo = []
    foreach file in testFiles:
        content = read(file)

        // Extract package name
        packageMatch = regex_search(@"package\s+(\w+)", content)
        packageName = packageMatch.group(1) if packageMatch else "unknown"

        // Check if black-box test (package ends with _test)
        isBlackBox = packageName.endswith("_test")

        testInfo.append({
            path: file,
            package: packageName,
            isBlackBox: isBlackBox
        })

    return testInfo
```

### Black-box vs White-box Testing

**White-box Testing** (package calculator):
```go
package calculator

import "testing"

func TestAdd(t *testing.T) {
    // Can access private functions
    result := internalHelper()
    // ...
}
```

**Black-box Testing** (package calculator_test):
```go
package calculator_test

import (
    "testing"
    "github.com/example/calculator"
)

func TestAdd(t *testing.T) {
    // Only public API accessible
    result := calculator.Add(2, 3)
    // ...
}
```

## Package Naming Conventions

### Standard Patterns

1. **Same Package** (white-box):
   - Test file: `calculator_test.go`
   - Package: `package calculator`
   - Access: All functions (public and private)

2. **Separate Test Package** (black-box):
   - Test file: `calculator_test.go`
   - Package: `package calculator_test`
   - Access: Only exported (public) functions

3. **Subpackages**:
   - `package calculator/math`
   - Test: `package math` or `package math_test`

## Confidence Scoring Examples

### Example 1: Standard testing (No testify)

```
Project Structure:
calculator/
├── go.mod (no testify dependency)
├── calculator.go
└── calculator_test.go (uses testing package only)

Scoring:
Built-in testing:
- Test file found (*_test.go): +10
- Test function pattern found: +8
- import "testing" found: +5
Total: 23

testify: 0

Confidence: testing = 23/23 = 1.0 (100%)
Result: PRIMARY=testing, CONFIDENCE=1.0, testify=false
```

### Example 2: Standard testing + testify

```
Project Structure:
calculator/
├── go.mod (contains github.com/stretchr/testify v1.8.4)
├── calculator.go
└── calculator_test.go (uses testing + testify assert)

Scoring:
Built-in testing:
- Test file found: +10
- Test function pattern: +8
- import "testing": +5
Total: 23

testify:
- testify in go.mod: +15
- import "github.com/stretchr/testify/assert": +8
- assert.Equal() pattern: +5
Total: 28

Overall Total: 51

Confidence:
- testing = 23/51 = 0.45 (45%)
- testify = 28/51 = 0.55 (55%)

Result: PRIMARY=testing (always available), testify=true, CONFIDENCE=1.0
Note: testify is an enhancement to testing, not a replacement
```

### Example 3: No Tests Yet (New Project)

```
Project Structure:
calculator/
├── go.mod
└── calculator.go (no test files)

Scoring:
Built-in testing: 0
testify: 0

Result: PRIMARY=testing (fallback), testify=false, CONFIDENCE=0.1
Recommendation: No tests detected. Go's built-in testing package recommended.
```

### Example 4: Mixed Test Styles

```
Project Structure:
calculator/
├── go.mod (contains testify)
├── calculator.go
├── calculator_test.go (standard testing)
└── advanced_test.go (testify suite)

Scoring:
Built-in testing:
- 2 test files: +10
- Test patterns: +8 (per file, max counted)
- import "testing": +5
Total: 23

testify:
- testify in go.mod: +15
- testify imports: +8
- suite pattern: +5
Total: 28

Result: PRIMARY=testing, testify=true, CONFIDENCE=1.0
```

## Edge Cases

### 1. Vendor Directory

**Scenario**: Project uses vendoring (older Go projects)

```
calculator/
├── go.mod
├── calculator.go
└── vendor/
    └── github.com/stretchr/testify/
```

**Strategy**:
- Check for `vendor/github.com/stretchr/testify/` directory
- Apply same scoring as go.mod dependency
- Note vendor mode in detection output

### 2. No go.mod (Pre-modules Project)

**Scenario**: Project uses GOPATH or older Go versions

**Strategy**:
- Fall back to import pattern detection only
- Check for `vendor/` directory
- Lower confidence scores
- Recommend creating go.mod

### 3. Internal Test Packages

**Scenario**: Tests in `internal/` directory

```
calculator/
├── calculator.go
├── internal/
│   ├── helper.go
│   └── helper_test.go
```

**Strategy**:
- Scan `internal/` directories for `*_test.go`
- Apply same detection patterns
- No special scoring adjustments

### 4. Build Tags

**Scenario**: Tests with build tags

```go
//go:build integration
// +build integration

package calculator_test

import "testing"

func TestIntegration(t *testing.T) {
    // Integration test
}
```

**Strategy**:
- Detect test files regardless of build tags
- Note build tags in evidence
- No impact on framework detection

## Framework Selection Logic

```go
function selectGoFramework(testingScore, testifyScore):
    """
    Select testing framework for Go project.
    Go always uses built-in testing package as base.
    testify is an optional enhancement.
    """
    total = testingScore + testifyScore

    // No evidence at all
    if total == 0:
        return {
            primary: "testing",
            testify: false,
            confidence: 0.1,
            recommendation: "No tests detected. Go's built-in testing package recommended."
        }

    // testify present
    hasTestify = testifyScore >= 15  // Requires go.mod dependency

    // Calculate confidence
    // Note: We always use "testing" as primary since it's always required
    confidence = total > 0 ? 1.0 : 0.1

    return {
        primary: "testing",
        testify: hasTestify,
        confidence: confidence,
        goVersion: detectGoVersion(),
        recommendation: generateRecommendation(hasTestify, confidence)
    }

function detectGoVersion():
    """Extract Go version from go.mod"""
    if exists("go.mod"):
        content = read("go.mod")
        match = regex_search(@"go\s+([0-9.]+)", content)
        if match:
            return match.group(1)

    return null
```

## Output Format

```yaml
language: go
primary_framework: testing
testify_enabled: true
go_version: "1.21"
module_name: github.com/example/calculator
confidence:
  testing: 1.0
  overall: 1.0
detection_details:
  test_files:
    - calculator_test.go (package calculator)
    - utils_test.go (package calculator_test)
  go_mod_file: go.mod
  dependencies:
    - name: github.com/stretchr/testify
      version: v1.8.4
  test_patterns:
    - "func Test* in calculator_test.go"
    - "t.Run() subtest in calculator_test.go"
  import_patterns:
    - "import \"testing\" in calculator_test.go"
    - "import \"github.com/stretchr/testify/assert\" in calculator_test.go"
  package_conventions:
    - "Black-box test: calculator_test.go (package calculator_test)"
recommendation: "Strong detection: Go testing with testify enhancements. All tests use standard testing package with testify assertions."
```

## Usage in Agents

### Analyze Agent

```markdown
# Read Go Framework Detection Skill
Read: skills/framework-detection/go-frameworks.md

# Apply Detection
1. Find all *_test.go files in project
2. Check for go.mod file
3. Parse go.mod for testify dependency
4. Scan test files for testing patterns
5. Scan test files for testify imports
6. Calculate weighted scores

# Score Calculation
testingScore = sum(testing_evidence_weights)
testifyScore = sum(testify_evidence_weights)

# Framework Selection
hasTestify = testifyScore >= 15  // go.mod dependency required
confidence = (testingScore + testifyScore) > 0 ? 1.0 : 0.1

# Output
Return: {
    "framework": "testing",
    "testify": hasTestify,
    "go_version": "1.21",
    "confidence": confidence
}
```

## Testing Validation

Test with sample projects:

1. **testing-only**: No testify, standard testing → Expect: testing, testify=false, confidence 1.0
2. **testing + testify**: go.mod with testify, assert usage → Expect: testing, testify=true, confidence 1.0
3. **testify suite**: Test suites with suite.Suite → Expect: testing, testify=true, confidence 1.0
4. **No tests**: Empty project → Expect: testing (fallback), testify=false, confidence 0.1
5. **Black-box tests**: package foo_test → Expect: testing, detect black-box convention

## References

- Go testing package: https://pkg.go.dev/testing
- testify library: https://github.com/stretchr/testify
- Go Modules: https://go.dev/ref/mod
- Table-driven tests: https://go.dev/wiki/TableDrivenTests
- Go testing best practices: https://go.dev/doc/tutorial/add-a-test

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
