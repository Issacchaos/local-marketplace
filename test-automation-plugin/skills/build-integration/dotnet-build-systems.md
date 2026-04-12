# .NET Build System Integration

**Version**: 1.0.0
**Language**: C#
**Build Tool**: dotnet CLI
**Status**: Phase 4 - Systems Languages

## Overview

Integration skill for .NET CLI (`dotnet`) build system, covering project restoration, compilation, test execution, and report generation for xUnit, NUnit, and MSTest frameworks.

## .NET CLI Command Reference

### Project Restoration

**Command**: `dotnet restore`

```bash
# Restore dependencies for solution
dotnet restore

# Restore specific project
dotnet restore Calculator.Tests/Calculator.Tests.csproj

# Restore with specific runtime
dotnet restore --runtime win-x64
```

**Purpose**: Downloads NuGet packages defined in project files
**When to Run**: Before build, after adding packages, in CI/CD pipelines

---

### Project Build

**Command**: `dotnet build`

```bash
# Build solution
dotnet build

# Build specific project
dotnet build Calculator.Tests/Calculator.Tests.csproj

# Build with configuration
dotnet build --configuration Release

# Build without restore (faster if already restored)
dotnet build --no-restore

# Build with specific framework
dotnet build --framework net8.0
```

**Purpose**: Compiles source code into assemblies (DLLs)
**Common Options**:
- `--configuration Debug|Release`: Build configuration
- `--no-restore`: Skip automatic restore
- `--framework <TFM>`: Target framework moniker (net8.0, net6.0)
- `--output <DIR>`: Output directory for build artifacts

---

### Test Execution

**Command**: `dotnet test`

```bash
# Run all tests in solution
dotnet test

# Run tests in specific project
dotnet test Calculator.Tests/Calculator.Tests.csproj

# Run with specific configuration
dotnet test --configuration Release

# Run without building (if already built)
dotnet test --no-build --no-restore

# Run with verbosity
dotnet test --verbosity detailed
```

**Purpose**: Executes unit tests and reports results
**Common Options**:
- `--no-build`: Skip build step (faster if already built)
- `--no-restore`: Skip restore step
- `--configuration Debug|Release`: Test configuration
- `--logger <LOGGER>`: Specify logger (console, trx, html, xunit)
- `--filter <EXPRESSION>`: Filter tests (by name, category, priority)
- `--collect <COLLECTOR>`: Data collector (Code Coverage)

---

## Framework-Specific Test Execution

### xUnit Test Execution

```bash
# Basic test run
dotnet test

# With console logger (verbose)
dotnet test --logger "console;verbosity=detailed"

# With xUnit XML output
dotnet test --logger "xunit;LogFilePath=test-results.xml"

# With multiple loggers
dotnet test --logger "console;verbosity=minimal" --logger "xunit;LogFilePath=results.xml"

# Run tests in parallel (xUnit default)
dotnet test

# Run tests serially (disable parallelism)
dotnet test -- xunit.parallelizeTestCollections=false
```

**xUnit Configuration** (xunit.runner.json):
```json
{
  "$schema": "https://xunit.net/schema/current/xunit.runner.schema.json",
  "parallelizeAssembly": true,
  "parallelizeTestCollections": true,
  "maxParallelThreads": 4,
  "methodDisplay": "method"
}
```

---

### NUnit Test Execution

```bash
# Basic test run
dotnet test

# With NUnit console logger
dotnet test --logger "console;verbosity=detailed"

# With NUnit XML output
dotnet test --logger "nunit;LogFilePath=test-results.xml"

# Run by category
dotnet test --filter "TestCategory=Unit"

# Run by priority
dotnet test --filter "Priority=1"
```

**NUnit Configuration** (.runsettings):
```xml
<?xml version="1.0" encoding="utf-8"?>
<RunSettings>
  <NUnit>
    <NumberOfTestWorkers>4</NumberOfTestWorkers>
    <DefaultTimeout>60000</DefaultTimeout>
  </NUnit>
</RunSettings>
```

Apply with:
```bash
dotnet test --settings test.runsettings
```

---

### MSTest Test Execution

```bash
# Basic test run
dotnet test

# With MSTest console logger
dotnet test --logger "console;verbosity=detailed"

# With TRX output (MSTest native format)
dotnet test --logger "trx;LogFileName=test-results.trx"

# Run by test category
dotnet test --filter "TestCategory=Integration"

# Run by priority
dotnet test --filter "Priority=1"

# Run by owner
dotnet test --filter "Owner=Alice"
```

**MSTest Configuration** (.runsettings):
```xml
<?xml version="1.0" encoding="utf-8"?>
<RunSettings>
  <MSTest>
    <Parallelize>
      <Workers>4</Workers>
      <Scope>MethodLevel</Scope>
    </Parallelize>
  </MSTest>
</RunSettings>
```

---

## Test Filtering

### Filter Expressions

```bash
# Filter by fully qualified name
dotnet test --filter "FullyQualifiedName=Calculator.Tests.CalculatorTests.Add_TwoNumbers_ReturnsSum"

# Filter by test name (contains)
dotnet test --filter "Name~Add"

# Filter by category (xUnit trait, NUnit/MSTest category)
dotnet test --filter "Category=Unit"
dotnet test --filter "TestCategory=Integration"

# Filter by priority
dotnet test --filter "Priority=1"

# Combine filters with logical operators
dotnet test --filter "(TestCategory=Unit)|(TestCategory=Integration)"
dotnet test --filter "(Priority=1)&(TestCategory=Unit)"

# Exclude tests
dotnet test --filter "TestCategory!=Slow"
```

### Framework-Specific Filtering

**xUnit Traits**:
```bash
dotnet test --filter "Category=Unit"
dotnet test --filter "Type=Integration"
```

**NUnit Categories**:
```bash
dotnet test --filter "TestCategory=Unit"
dotnet test --filter "TestCategory=FastTest"
```

**MSTest Categories**:
```bash
dotnet test --filter "TestCategory=Unit"
dotnet test --filter "Priority=1"
dotnet test --filter "Owner=Alice"
```

---

## Test Logging and Reporting

### Console Logger

```bash
# Minimal verbosity (summary only)
dotnet test --logger "console;verbosity=minimal"

# Normal verbosity (default)
dotnet test --logger "console;verbosity=normal"

# Detailed verbosity (all test output)
dotnet test --logger "console;verbosity=detailed"

# Quiet mode (errors only)
dotnet test --logger "console;verbosity=quiet"
```

---

### xUnit XML Logger

```bash
# Generate xUnit XML report
dotnet test --logger "xunit;LogFilePath=test-results.xml"

# With specific output path
dotnet test --logger "xunit;LogFilePath=../TestResults/xunit-results.xml"

# Multiple test projects - use tokens
dotnet test --logger "xunit;LogFilePath=TestResults/{assembly}.xml"
```

**xUnit XML Format**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<assemblies timestamp="2025-12-10T15:30:45">
  <assembly name="Calculator.Tests" total="10" passed="9" failed="1" skipped="0"/>
</assemblies>
```

---

### TRX Logger (Visual Studio Test Results)

```bash
# Generate TRX report
dotnet test --logger "trx;LogFileName=test-results.trx"

# With specific output path
dotnet test --logger "trx;LogFileName=../TestResults/results.trx"

# Multiple test projects
dotnet test --logger "trx;LogFileName=TestResults/{assembly}-results.trx"
```

**TRX Format**: XML format used by Visual Studio, Azure DevOps, and other Microsoft tools.

---

### HTML Logger (Human-Readable Report)

Requires: `dotnet-reportgenerator-globaltool`

```bash
# Install report generator
dotnet tool install --global dotnet-reportgenerator-globaltool

# Run tests with TRX output
dotnet test --logger "trx;LogFileName=TestResults/results.trx"

# Generate HTML report
reportgenerator -reports:TestResults/*.trx -targetdir:TestResults/html -reporttypes:Html
```

---

## Code Coverage

### Coverage with Coverlet

**Install Coverlet**:
```bash
dotnet add package coverlet.msbuild
```

**Collect coverage**:
```bash
# Generate coverage data
dotnet test /p:CollectCoverage=true

# Generate coverage in specific format
dotnet test /p:CollectCoverage=true /p:CoverageReportFormat=cobertura

# Generate with threshold
dotnet test /p:CollectCoverage=true /p:Threshold=80

# Output to specific file
dotnet test /p:CollectCoverage=true /p:CoverageFile=coverage.cobertura.xml
```

**Supported Formats**:
- `json`: JSON format
- `lcov`: LCOV format (for tools like CodeCov)
- `opencover`: OpenCover XML format
- `cobertura`: Cobertura XML format

---

### Coverage with dotnet-coverage (Built-in)

```bash
# Collect coverage with built-in tool
dotnet test --collect:"Code Coverage"

# Specify output format
dotnet test --collect:"Code Coverage" --results-directory:./TestResults

# Generate report
dotnet-coverage collect "dotnet test" -f xml -o "coverage.xml"
```

---

## Build Artifacts and Output Paths

### Default Output Paths

```
Solution/
├── src/
│   └── Calculator/
│       ├── bin/
│       │   ├── Debug/
│       │   │   └── net8.0/
│       │   │       ├── Calculator.dll
│       │   │       └── Calculator.pdb
│       │   └── Release/
│       │       └── net8.0/
│       └── obj/                    # Intermediate build files
├── tests/
│   └── Calculator.Tests/
│       ├── bin/
│       │   └── Debug/
│       │       └── net8.0/
│       │           ├── Calculator.Tests.dll
│       │           └── Calculator.dll (copied)
│       └── obj/
└── TestResults/                    # Test results (if specified)
    ├── test-results.xml
    └── coverage.cobertura.xml
```

---

## MSBuild Properties

### Common Properties

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <!-- Target framework -->
    <TargetFramework>net8.0</TargetFramework>

    <!-- Multiple target frameworks -->
    <TargetFrameworks>net8.0;net6.0</TargetFrameworks>

    <!-- Output paths -->
    <OutputPath>bin\$(Configuration)\$(TargetFramework)\</OutputPath>
    <IntermediateOutputPath>obj\$(Configuration)\$(TargetFramework)\</IntermediateOutputPath>

    <!-- Nullable reference types -->
    <Nullable>enable</Nullable>

    <!-- Mark as test project -->
    <IsTestProject>true</IsTestProject>
    <IsPackable>false</IsPackable>
  </PropertyGroup>
</Project>
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: .NET Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup .NET
      uses: actions/setup-dotnet@v3
      with:
        dotnet-version: '8.0.x'

    - name: Restore dependencies
      run: dotnet restore

    - name: Build
      run: dotnet build --no-restore --configuration Release

    - name: Run tests
      run: dotnet test --no-build --configuration Release --logger "trx;LogFileName=test-results.trx" --logger "xunit;LogFileName=xunit-results.xml"

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          **/TestResults/*.trx
          **/TestResults/*.xml
```

---

### Azure DevOps Example

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  buildConfiguration: 'Release'

steps:
- task: UseDotNet@2
  inputs:
    version: '8.0.x'

- script: dotnet restore
  displayName: 'Restore dependencies'

- script: dotnet build --no-restore --configuration $(buildConfiguration)
  displayName: 'Build'

- script: dotnet test --no-build --configuration $(buildConfiguration) --logger "trx" --collect:"Code Coverage"
  displayName: 'Run tests'

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'VSTest'
    testResultsFiles: '**/*.trx'
```

---

## Common Build Workflows

### Full Build and Test

```bash
# Complete workflow
dotnet restore
dotnet build --no-restore --configuration Release
dotnet test --no-build --no-restore --configuration Release --logger "console;verbosity=normal" --logger "trx;LogFileName=TestResults/results.trx"
```

---

### Fast Development Workflow

```bash
# Quick test run (Debug config, no explicit restore/build)
dotnet test --logger "console;verbosity=minimal"
```

---

### CI/CD Workflow (Optimized)

```bash
# Restore once
dotnet restore

# Build without restore
dotnet build --no-restore --configuration Release

# Test without build or restore
dotnet test --no-build --no-restore --configuration Release \
  --logger "console;verbosity=minimal" \
  --logger "trx;LogFileName=TestResults/results.trx" \
  --collect:"Code Coverage"
```

---

## Troubleshooting

### Build Fails

```bash
# Clean build artifacts
dotnet clean

# Restore and rebuild
dotnet restore
dotnet build
```

---

### Tests Not Discovered

**Check**:
1. Test project has correct test framework package
2. Test methods have correct attributes (`[Fact]`, `[Test]`, `[TestMethod]`)
3. Test project references the code project
4. SDK is `Microsoft.NET.Sdk` (not `Microsoft.NET.Sdk.Web`)

```bash
# List tests without running
dotnet test --list-tests
```

---

### Slow Test Execution

```bash
# Run tests in parallel (xUnit default)
dotnet test

# Limit parallel threads
dotnet test -- xunit.maxParallelThreads=2

# Run specific tests only
dotnet test --filter "TestCategory=Unit"
```

---

## References

- .NET CLI Documentation: https://learn.microsoft.com/en-us/dotnet/core/tools/
- dotnet test Command: https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test
- Test Filtering: https://learn.microsoft.com/en-us/dotnet/core/testing/selective-unit-tests
- Code Coverage: https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-code-coverage
- xUnit Configuration: https://xunit.net/docs/configuration-files
- NUnit Configuration: https://docs.nunit.org/articles/nunit/technical-notes/usage/Test-Configuration-File.html

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
