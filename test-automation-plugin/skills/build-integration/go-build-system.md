# Go Build System Integration

**Version**: 1.0.0
**Language**: Go
**Build Tool**: go CLI
**Status**: Phase 4 - Systems Languages

## Overview

Integration skill for Go toolchain (`go` command), covering module management, compilation, test execution, and report generation for Go's built-in testing framework with support for JSON output and coverage analysis.

## Go CLI Command Reference

### Module Initialization

**Command**: `go mod init`

```bash
# Initialize new module
go mod init example.com/myproject

# Initialize with module path from git remote
go mod init

# Initialize in existing directory
cd myproject && go mod init example.com/myproject
```

**Purpose**: Creates a new `go.mod` file to define module and track dependencies
**When to Run**: When starting a new Go project, converting from GOPATH

---

### Module Management

**Command**: `go mod download`

```bash
# Download all dependencies
go mod download

# Download specific module
go mod download github.com/stretchr/testify

# Download with verification
go mod download -json

# Download all dependencies (verbose)
go mod download -x
```

**Purpose**: Downloads modules to local cache without building
**When to Run**: Before build in CI/CD, to populate module cache, for offline builds

---

**Command**: `go mod tidy`

```bash
# Add missing and remove unused modules
go mod tidy

# Tidy with specific Go version
go mod tidy -go=1.21

# Tidy with verbose output
go mod tidy -v

# Tidy without verifying checksums
go mod tidy -e
```

**Purpose**: Ensures `go.mod` matches source code imports, updates `go.sum`
**When to Run**: After adding/removing imports, before committing, in CI/CD verification

---

**Command**: `go mod vendor`

```bash
# Copy dependencies to vendor/
go mod vendor

# Vendor with verbose output
go mod vendor -v

# Vendor with verification
go mod vendor -e
```

**Purpose**: Creates vendor directory with all dependencies for offline builds
**When to Run**: For reproducible builds, air-gapped environments, corporate policies

---

**Command**: `go mod verify`

```bash
# Verify dependencies haven't been modified
go mod verify

# Verify and report checksums
go mod verify -v
```

**Purpose**: Checks that dependencies in module cache match `go.sum` checksums
**When to Run**: Security audits, CI/CD verification, after downloading modules

---

### Project Build

**Command**: `go build`

```bash
# Build current package
go build

# Build specific package
go build ./cmd/myapp

# Build with output name
go build -o myapp ./cmd/myapp

# Build multiple packages
go build ./cmd/...

# Build all packages in module
go build ./...

# Build with specific flags
go build -v -x ./cmd/myapp

# Build without using module cache
go build -mod=mod ./cmd/myapp

# Build using vendor directory
go build -mod=vendor ./cmd/myapp
```

**Purpose**: Compiles Go source code into executable binaries or packages
**Common Options**:
- `-o <FILE>`: Output file name
- `-v`: Verbose output (print packages being compiled)
- `-x`: Print commands being executed
- `-a`: Force rebuild of all packages
- `-n`: Print commands without executing
- `-race`: Enable data race detection
- `-mod=readonly|vendor|mod`: Module download mode

---

### Build Flags and Optimization

**Compiler and Linker Flags**:

```bash
# Build with optimization disabled (debugging)
go build -gcflags="all=-N -l" ./cmd/myapp

# Build with linker flags (set version info)
go build -ldflags="-X main.version=1.0.0 -X main.commit=abc123" ./cmd/myapp

# Build with size optimization (strip symbols)
go build -ldflags="-s -w" ./cmd/myapp

# Build with all optimizations
go build -trimpath -ldflags="-s -w" ./cmd/myapp

# Build for production (optimized, trimmed paths)
go build -trimpath -ldflags="-s -w -X main.version=$(git describe --tags)" ./cmd/myapp
```

**Common Compiler Flags (`-gcflags`)**:
- `-N`: Disable optimizations
- `-l`: Disable inlining
- `-m`: Print optimization decisions

**Common Linker Flags (`-ldflags`)**:
- `-s`: Strip symbol table
- `-w`: Strip DWARF debug information
- `-X`: Set variable value at link time

---

### Test Execution

**Command**: `go test`

```bash
# Run all tests in current package
go test

# Run tests in specific package
go test ./calculator

# Run all tests in module
go test ./...

# Run tests recursively with verbose output
go test -v ./...

# Run specific test
go test -run TestAdd

# Run tests matching pattern
go test -run "Test.*Sum"

# Run with short mode (skip long-running tests)
go test -short ./...

# Run with timeout
go test -timeout 30s ./...

# Run without caching results
go test -count=1 ./...
```

**Purpose**: Executes test functions and reports results
**Common Options**:
- `-v`: Verbose output (print all test names and output)
- `-run <REGEXP>`: Run only tests matching pattern
- `-short`: Skip long-running tests (check `testing.Short()`)
- `-timeout <DURATION>`: Test timeout (default 10m)
- `-count <N>`: Run tests N times (use -count=1 to disable cache)
- `-parallel <N>`: Number of tests to run in parallel (default GOMAXPROCS)

---

### Test Filtering and Selection

```bash
# Run specific test function
go test -run TestCalculator_Add

# Run tests in specific file (indirect - by function pattern)
go test -run "^TestCalculator"

# Run tests by subtest
go test -run "TestCalculator/add_positive_numbers"

# Run multiple test patterns
go test -run "TestAdd|TestSubtract"

# Run benchmark tests
go test -bench=.

# Run specific benchmark
go test -bench=BenchmarkAdd

# Run benchmarks with memory stats
go test -bench=. -benchmem

# Run benchmarks multiple times
go test -bench=. -benchtime=10s

# Run benchmarks with CPU profiling
go test -bench=. -cpuprofile=cpu.prof
```

**Test Name Patterns**:
- `^TestName$`: Exact match
- `TestName`: Contains match
- `Test.*Pattern`: Regular expression
- `TestName/SubtestName`: Subtest match

---

### JSON Output for CI/CD Integration

**Command**: `go test -json`

```bash
# Run tests with JSON output
go test -json ./...

# Run tests with JSON output to file
go test -json ./... > test-results.json

# Run tests with JSON and verbose output
go test -json -v ./...

# Run with JSON output and coverage
go test -json -cover ./...

# Run with JSON output (no cache)
go test -json -count=1 ./...
```

**JSON Output Format**:
```json
{"Time":"2025-12-11T10:30:00Z","Action":"run","Package":"example.com/calculator","Test":"TestAdd"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"example.com/calculator","Test":"TestAdd","Output":"=== RUN   TestAdd\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"pass","Package":"example.com/calculator","Test":"TestAdd","Elapsed":0.001}
{"Time":"2025-12-11T10:30:00Z","Action":"pass","Package":"example.com/calculator","Elapsed":0.002}
```

**JSON Fields**:
- `Action`: `run`, `output`, `pass`, `fail`, `skip`, `pause`, `cont`
- `Package`: Import path of test package
- `Test`: Test function name
- `Output`: Test output line
- `Elapsed`: Test duration in seconds

---

### Code Coverage

**Command**: `go test -cover`

```bash
# Run tests with coverage summary
go test -cover ./...

# Run tests with coverage percentage
go test -coverprofile=coverage.out ./...

# Run tests with coverage by package
go test -coverpkg=./... -coverprofile=coverage.out ./...

# Generate HTML coverage report
go test -coverprofile=coverage.out ./... && go tool cover -html=coverage.out -o coverage.html

# View coverage in browser
go test -coverprofile=coverage.out ./... && go tool cover -html=coverage.out

# Generate coverage with specific mode
go test -covermode=count -coverprofile=coverage.out ./...

# Coverage with JSON output
go test -json -cover ./...
```

**Coverage Modes (`-covermode`)**:
- `set`: Did statement run? (default)
- `count`: How many times did statement run?
- `atomic`: Like count, but thread-safe (for parallel tests)

---

### Coverage Report Analysis

```bash
# View coverage summary
go tool cover -func=coverage.out

# View coverage by function (sorted)
go tool cover -func=coverage.out | sort -k 3 -n

# Filter coverage by package
go tool cover -func=coverage.out | grep "calculator"

# Generate coverage HTML report
go tool cover -html=coverage.out -o coverage.html

# View coverage in terminal (basic)
go tool cover -func=coverage.out | tail -n 1
```

**Coverage Output Format** (`coverage.out`):
```
mode: set
example.com/calculator/calculator.go:10.35,12.2 1 1
example.com/calculator/calculator.go:14.38,16.2 1 1
example.com/calculator/calculator.go:18.41,20.2 1 0
```

**Function Coverage Output**:
```
example.com/calculator/calculator.go:10:   Add         100.0%
example.com/calculator/calculator.go:14:   Subtract    100.0%
example.com/calculator/calculator.go:18:   Multiply    0.0%
total:                                      (statements) 66.7%
```

---

## Build Tags and Conditional Compilation

### Build Constraints

**Using `//go:build` directives** (Go 1.17+):

```go
//go:build linux
// +build linux

package mypackage
```

**Common Build Tags**:

```go
// Build only on Linux
//go:build linux

// Build only on Windows
//go:build windows

// Build only on macOS
//go:build darwin

// Build on Linux or macOS
//go:build linux || darwin

// Build with specific tag
//go:build integration

// Build without tag
//go:build !integration

// Complex conditions
//go:build (linux && amd64) || (darwin && arm64)
```

---

### Using Build Tags

```bash
# Build with custom tag
go build -tags integration ./...

# Build with multiple tags
go build -tags "integration,debug" ./...

# Test with build tags
go test -tags integration ./...

# Test with build tags and verbose output
go test -v -tags integration ./...

# Run tests excluding integration tests
go test ./... # (files with //go:build integration are excluded)
```

---

### Common Build Tag Patterns

**Integration Tests**:
```go
//go:build integration
// +build integration

package calculator_test

import "testing"

func TestIntegration_DatabaseConnection(t *testing.T) {
    // Integration test requiring external resources
}
```

Run with:
```bash
go test -tags integration ./...
```

---

**Platform-Specific Code**:

`calculator_linux.go`:
```go
//go:build linux
// +build linux

package calculator

func PlatformSpecific() string {
    return "Linux"
}
```

`calculator_windows.go`:
```go
//go:build windows
// +build windows

package calculator

func PlatformSpecific() string {
    return "Windows"
}
```

---

**Feature Flags**:
```go
//go:build debug
// +build debug

package calculator

const Debug = true
```

Build with feature:
```bash
go build -tags debug ./cmd/myapp
```

---

## Cross-Compilation

### Cross-Platform Builds

**Environment Variables**:
- `GOOS`: Target operating system (linux, windows, darwin, freebsd, etc.)
- `GOARCH`: Target architecture (amd64, arm64, 386, arm, etc.)

```bash
# Build for Linux (64-bit)
GOOS=linux GOARCH=amd64 go build -o myapp-linux-amd64 ./cmd/myapp

# Build for Windows (64-bit)
GOOS=windows GOARCH=amd64 go build -o myapp-windows-amd64.exe ./cmd/myapp

# Build for macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o myapp-darwin-amd64 ./cmd/myapp

# Build for macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o myapp-darwin-arm64 ./cmd/myapp

# Build for Raspberry Pi
GOOS=linux GOARCH=arm GOARM=7 go build -o myapp-linux-arm7 ./cmd/myapp

# Build for ARM64 Linux
GOOS=linux GOARCH=arm64 go build -o myapp-linux-arm64 ./cmd/myapp
```

---

### List Available Platforms

```bash
# List all supported OS/Architecture combinations
go tool dist list

# Filter for specific OS
go tool dist list | grep linux

# Filter for specific architecture
go tool dist list | grep arm64
```

**Common Platforms**:
```
linux/386
linux/amd64
linux/arm
linux/arm64
darwin/amd64
darwin/arm64
windows/386
windows/amd64
windows/arm64
```

---

### Cross-Compilation Script

```bash
#!/bin/bash
# build-all.sh - Build for multiple platforms

VERSION=$(git describe --tags --always --dirty)
PLATFORMS="linux/amd64 linux/arm64 darwin/amd64 darwin/arm64 windows/amd64"

for PLATFORM in $PLATFORMS; do
    GOOS=${PLATFORM%/*}
    GOARCH=${PLATFORM#*/}
    OUTPUT="dist/myapp-${GOOS}-${GOARCH}"

    if [ "$GOOS" = "windows" ]; then
        OUTPUT="${OUTPUT}.exe"
    fi

    echo "Building $OUTPUT..."
    GOOS=$GOOS GOARCH=$GOARCH go build \
        -trimpath \
        -ldflags="-s -w -X main.version=${VERSION}" \
        -o "$OUTPUT" \
        ./cmd/myapp
done

echo "Build complete!"
```

---

## Go Modules (go.mod and go.sum)

### go.mod File Structure

**Example `go.mod`**:
```go
module example.com/myproject

go 1.21

require (
    github.com/stretchr/testify v1.8.4
    golang.org/x/sync v0.5.0
)

require (
    github.com/davecgh/go-spew v1.1.1 // indirect
    github.com/pmezard/go-difflib v1.0.0 // indirect
    gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace example.com/internal => ../internal

exclude github.com/old/package v1.0.0
```

**Directives**:
- `module`: Module path (import prefix)
- `go`: Minimum Go version required
- `require`: Direct and indirect dependencies
- `replace`: Replace dependency with local or different version
- `exclude`: Exclude specific version of dependency

---

### go.sum File

**Purpose**: Cryptographic checksums for module verification

**Example `go.sum`**:
```
github.com/stretchr/testify v1.8.4 h1:CcVxjf3Q8PM0mHUKJCdn+eZZtm5yQwehR5yeSVQQcUk=
github.com/stretchr/testify v1.8.4/go.mod h1:sz/lmYIOXD/1dqDmKjjqLyZ2RngseejIcXlSw2iwfAo=
```

**Format**: `<module> <version> <hash-algorithm>:<hash>`

**Never edit manually**: Managed automatically by `go mod` commands

---

### Module Management Commands

```bash
# Show current module info
go list -m

# Show all dependencies
go list -m all

# Show dependency graph
go mod graph

# Show why package is needed
go mod why github.com/pkg/errors

# Edit go.mod (add requirement)
go mod edit -require github.com/pkg/errors@v0.9.1

# Edit go.mod (drop requirement)
go mod edit -droprequire github.com/pkg/errors

# Edit go.mod (replace dependency)
go mod edit -replace example.com/old=example.com/new@v1.0.0

# Update all dependencies to latest
go get -u ./...

# Update specific dependency
go get github.com/stretchr/testify@latest

# Update to specific version
go get github.com/stretchr/testify@v1.8.4

# Downgrade dependency
go get github.com/stretchr/testify@v1.7.0
```

---

## Common Workflows

### New Project Setup

```bash
# Create project directory
mkdir myproject && cd myproject

# Initialize module
go mod init example.com/myproject

# Create main.go
cat > main.go << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
EOF

# Run program
go run main.go

# Build executable
go build -o myapp
```

---

### Add Dependencies

```bash
# Add dependency (automatically updates go.mod)
go get github.com/stretchr/testify

# Import in code
# import "github.com/stretchr/testify/assert"

# Tidy up (remove unused, add missing)
go mod tidy

# Verify checksums
go mod verify
```

---

### Development Workflow

```bash
# Fast test run (current package)
go test

# Run all tests with coverage
go test -cover ./...

# Run tests with race detection
go test -race ./...

# Run tests and generate coverage report
go test -coverprofile=coverage.out ./... && go tool cover -html=coverage.out

# Build and run
go build -o myapp ./cmd/myapp && ./myapp

# Or use go run
go run ./cmd/myapp
```

---

### CI/CD Workflow (Complete)

```bash
# 1. Verify environment
go version

# 2. Download dependencies
go mod download

# 3. Verify dependencies
go mod verify

# 4. Check formatting
gofmt -l .

# 5. Run linter (requires golangci-lint)
golangci-lint run ./...

# 6. Run tests with coverage and JSON output
go test -v -race -coverprofile=coverage.out -covermode=atomic -json ./... > test-results.json

# 7. Generate coverage report
go tool cover -html=coverage.out -o coverage.html

# 8. Build for production
go build -trimpath -ldflags="-s -w -X main.version=$(git describe --tags)" -o myapp ./cmd/myapp

# 9. Build for multiple platforms
GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o dist/myapp-linux-amd64 ./cmd/myapp
GOOS=windows GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o dist/myapp-windows-amd64.exe ./cmd/myapp
GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o dist/myapp-darwin-arm64 ./cmd/myapp
```

---

### Release Build Workflow

```bash
# Get version from git tags
VERSION=$(git describe --tags --always --dirty)
COMMIT=$(git rev-parse --short HEAD)
BUILD_TIME=$(date -u '+%Y-%m-%d_%H:%M:%S')

# Build with version info
go build \
    -trimpath \
    -ldflags="-s -w \
        -X main.version=${VERSION} \
        -X main.commit=${COMMIT} \
        -X main.buildTime=${BUILD_TIME}" \
    -o myapp \
    ./cmd/myapp

# Verify version
./myapp --version
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Go Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Go
      uses: actions/setup-go@v5
      with:
        go-version: '1.21'

    - name: Cache Go modules
      uses: actions/cache@v3
      with:
        path: ~/go/pkg/mod
        key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
        restore-keys: |
          ${{ runner.os }}-go-

    - name: Download dependencies
      run: go mod download

    - name: Verify dependencies
      run: go mod verify

    - name: Run tests
      run: go test -v -race -coverprofile=coverage.out -covermode=atomic ./...

    - name: Generate coverage report
      run: go tool cover -html=coverage.out -o coverage.html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.out

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          coverage.out
          coverage.html

    - name: Build
      run: go build -v ./...
```

---

### GitHub Actions with JSON Output

```yaml
name: Go Tests with JSON

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Go
      uses: actions/setup-go@v5
      with:
        go-version: '1.21'

    - name: Run tests with JSON output
      run: |
        go test -json -coverprofile=coverage.out ./... | tee test-results.json

    - name: Parse test results
      if: always()
      run: |
        go install github.com/jstemmer/go-junit-report/v2@latest
        cat test-results.json | go-junit-report -set-exit-code > junit-report.xml

    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: junit-report.xml
```

---

### GitLab CI Example

```yaml
image: golang:1.21

stages:
  - test
  - build

variables:
  GOPROXY: "https://proxy.golang.org,direct"

cache:
  paths:
    - .go/pkg/mod/

test:
  stage: test
  script:
    - go mod download
    - go mod verify
    - go test -v -race -coverprofile=coverage.out -covermode=atomic ./...
    - go tool cover -html=coverage.out -o coverage.html
    - go tool cover -func=coverage.out
  coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - coverage.out
      - coverage.html

build:
  stage: build
  script:
    - go build -trimpath -ldflags="-s -w" -o myapp ./cmd/myapp
  artifacts:
    paths:
      - myapp
```

---

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    environment {
        GO_VERSION = '1.21'
        GOPROXY = 'https://proxy.golang.org,direct'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'go version'
                sh 'go mod download'
                sh 'go mod verify'
            }
        }

        stage('Test') {
            steps {
                sh 'go test -v -race -coverprofile=coverage.out -covermode=atomic ./...'
                sh 'go tool cover -html=coverage.out -o coverage.html'
                sh 'go tool cover -func=coverage.out'
            }
        }

        stage('Build') {
            steps {
                sh 'go build -trimpath -ldflags="-s -w" -o myapp ./cmd/myapp'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'coverage.out,coverage.html', allowEmptyArchive: true
            publishHTML([
                reportDir: '.',
                reportFiles: 'coverage.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

---

## Best Practices

### Module Management

1. **Always use `go mod tidy`** before committing
   ```bash
   go mod tidy
   git add go.mod go.sum
   ```

2. **Commit `go.sum`** to version control
   - Ensures reproducible builds
   - Provides security verification

3. **Use semantic versioning** for module releases
   - v1.0.0, v1.1.0, v2.0.0
   - Tag releases: `git tag v1.0.0`

4. **Pin dependencies** for reproducible builds
   ```bash
   go get github.com/pkg/errors@v0.9.1
   ```

---

### Testing

1. **Run tests with race detector** in CI/CD
   ```bash
   go test -race ./...
   ```

2. **Use `-count=1`** to disable test caching
   ```bash
   go test -count=1 ./...
   ```

3. **Set test timeouts** to prevent hanging tests
   ```bash
   go test -timeout 30s ./...
   ```

4. **Generate coverage reports** regularly
   ```bash
   go test -coverprofile=coverage.out ./...
   go tool cover -html=coverage.out
   ```

5. **Use table-driven tests** for comprehensive coverage
   ```go
   func TestAdd(t *testing.T) {
       tests := []struct {
           name string
           a, b int
           want int
       }{
           {"positive", 1, 2, 3},
           {"negative", -1, -2, -3},
           {"zero", 0, 0, 0},
       }
       for _, tt := range tests {
           t.Run(tt.name, func(t *testing.T) {
               if got := Add(tt.a, tt.b); got != tt.want {
                   t.Errorf("Add() = %v, want %v", got, tt.want)
               }
           })
       }
   }
   ```

---

### Build

1. **Use `-trimpath`** for reproducible builds
   ```bash
   go build -trimpath ./...
   ```

2. **Strip binaries** for production
   ```bash
   go build -ldflags="-s -w" ./...
   ```

3. **Embed version information** at build time
   ```bash
   go build -ldflags="-X main.version=$(git describe --tags)" ./...
   ```

4. **Use build tags** for conditional compilation
   ```go
   //go:build integration
   ```

---

### CI/CD

1. **Cache module downloads** for faster builds
   ```yaml
   # GitHub Actions
   - uses: actions/cache@v3
     with:
       path: ~/go/pkg/mod
       key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
   ```

2. **Verify modules** in CI pipeline
   ```bash
   go mod verify
   ```

3. **Use JSON output** for test result parsing
   ```bash
   go test -json ./... > test-results.json
   ```

4. **Run linters** in CI/CD
   ```bash
   golangci-lint run ./...
   ```

5. **Build for multiple platforms** in release pipeline
   ```bash
   GOOS=linux GOARCH=amd64 go build ./...
   GOOS=windows GOARCH=amd64 go build ./...
   ```

---

## Troubleshooting

### Module Issues

**Problem**: `cannot find module providing package`

```bash
# Solution: Add missing module
go get github.com/missing/package
go mod tidy
```

---

**Problem**: `checksum mismatch`

```bash
# Solution: Clear module cache and re-download
go clean -modcache
go mod download
```

---

**Problem**: `ambiguous import`

```bash
# Solution: Use replace directive in go.mod
go mod edit -replace example.com/pkg=example.com/pkg/v2@latest
```

---

### Build Issues

**Problem**: `build cache is disabled`

```bash
# Solution: Enable build cache
export GOCACHE=$(go env GOCACHE)
```

---

**Problem**: `package not found`

```bash
# Solution: Check GOPATH and module mode
go env GOPATH
go env GO111MODULE  # Should be empty or "on"
```

---

### Test Issues

**Problem**: Tests fail only in CI/CD

```bash
# Solution: Disable test caching
go test -count=1 ./...
```

---

**Problem**: Tests timeout

```bash
# Solution: Increase timeout
go test -timeout 5m ./...
```

---

**Problem**: Race detector reports data race

```bash
# Solution: Run with race detector locally
go test -race ./...
# Fix concurrent access issues
```

---

## Performance Optimization

### Build Performance

```bash
# Enable parallel compilation (default)
go build -p 4 ./...

# Use build cache
go build ./...  # subsequent builds are faster

# Skip tests in build-only scenario
go build -a ./...  # force rebuild all
```

---

### Test Performance

```bash
# Run tests in parallel (default)
go test ./...

# Limit parallel tests
go test -parallel 4 ./...

# Run short tests only
go test -short ./...

# Cache test results
go test ./...  # subsequent runs use cache
```

---

## References

- Go Command Documentation: https://pkg.go.dev/cmd/go
- Go Modules Reference: https://go.dev/ref/mod
- Go Testing Package: https://pkg.go.dev/testing
- Build Constraints: https://pkg.go.dev/cmd/go#hdr-Build_constraints
- Cross Compilation: https://go.dev/doc/install/source#environment
- Coverage Tool: https://pkg.go.dev/cmd/cover

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
