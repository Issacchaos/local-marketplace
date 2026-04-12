# C# Test Location Detection

**Language**: C#
**Frameworks**: xUnit, NUnit, MSTest
**Version**: 1.0.0

---

## Overview

C# test location conventions follow .NET project structure patterns with separate test projects. This document provides guidance for determining correct test file locations in C# solutions.

---

## Configuration Sources (Priority Order)

### 1. Solution File (.sln)

**Location**: Solution root
**Purpose**: Defines project structure and relationships

```sln
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Calculator", "src\Calculator\Calculator.csproj", "{GUID1}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Calculator.Tests", "tests\Calculator.Tests\Calculator.Tests.csproj", "{GUID2}"
EndProject
```

**Detection Strategy**:
- Find `.sln` file in project root
- Parse for test project paths (projects with `.Tests` or `.UnitTests` suffix)
- Use directory structure from solution file

---

### 2. Project File (.csproj)

**Location**: Project directory
**Purpose**: Defines project properties and dependencies

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <IsTestProject>true</IsTestProject>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.6.0" />
    <ProjectReference Include="..\..\src\Calculator\Calculator.csproj" />
  </ItemGroup>
</Project>
```

**Test Project Indicators**:
- `<IsTestProject>true</IsTestProject>` property
- Test framework packages (xUnit, NUnit, MSTest)
- Project references to source projects

---

## Default Conventions

### .NET Standard Convention (Most Common)

**Structure**:
```
MySolution/
├── src/
│   └── Calculator/
│       ├── Calculator.csproj
│       ├── Calculator.cs
│       └── Operations/
│           └── AddOperation.cs
├── tests/
│   └── Calculator.Tests/
│       ├── Calculator.Tests.csproj
│       ├── CalculatorTests.cs
│       └── Operations/
│           └── AddOperationTests.cs
└── MySolution.sln
```

**Naming Pattern**:
- Test project: `{ProjectName}.Tests` or `{ProjectName}.UnitTests`
- Test files: `{ClassName}Tests.cs`
- Mirror source structure within test project

---

### Alternative: Flat Structure

**Structure**:
```
MySolution/
├── Calculator/
│   ├── Calculator.csproj
│   └── Calculator.cs
├── Calculator.Tests/
│   ├── Calculator.Tests.csproj
│   └── CalculatorTests.cs
└── MySolution.sln
```

**When Used**:
- Small projects with few files
- Single-project solutions
- Legacy projects

---

### Alternative: Tests Within Project (Less Common)

**Structure**:
```
MySolution/
└── Calculator/
    ├── Calculator.csproj
    ├── Calculator.cs
    └── Tests/
        └── CalculatorTests.cs
```

**When Used**:
- Very small libraries
- Single-file projects
- Not recommended for production code

---

## Path Resolution Algorithm

### Input

- Source file: `C:\MySolution\src\Calculator\Operations\AddOperation.cs`
- Project root: `C:\MySolution\`
- Solution file: `C:\MySolution\MySolution.sln`

### Step 1: Identify Source Project

**From source file path**:
- File: `C:\MySolution\src\Calculator\Operations\AddOperation.cs`
- Extract project: `Calculator` (directory containing `.csproj`)
- Project path: `C:\MySolution\src\Calculator\`

---

### Step 2: Locate Test Project

**Check for test project in solution**:

**Pattern 1**: `{ProjectName}.Tests`
- Look for: `C:\MySolution\tests\Calculator.Tests\Calculator.Tests.csproj`

**Pattern 2**: `{ProjectName}.UnitTests`
- Look for: `C:\MySolution\tests\Calculator.UnitTests\Calculator.UnitTests.csproj`

**Pattern 3**: Adjacent to source
- Look for: `C:\MySolution\Calculator.Tests\Calculator.Tests.csproj`

**Priority**:
1. Check solution file for test projects
2. Search for `{ProjectName}.Tests` directory
3. Search for `{ProjectName}.UnitTests` directory
4. Fallback: Create `tests/{ProjectName}.Tests/` structure

---

### Step 3: Calculate Relative Path

**Within source project**:
- Source file: `C:\MySolution\src\Calculator\Operations\AddOperation.cs`
- Project root: `C:\MySolution\src\Calculator\`
- Relative path: `Operations\AddOperation.cs`
- Relative directory: `Operations\`

---

### Step 4: Apply Naming Convention

**Test file naming**:
- Source file: `AddOperation.cs`
- Test file: `AddOperationTests.cs`

**Pattern**: `{ClassName}Tests.cs`

---

### Step 5: Construct Test Path

**Components**:
- Test project root: `C:\MySolution\tests\Calculator.Tests\`
- Relative directory: `Operations\`
- Test filename: `AddOperationTests.cs`

**Final Test Path**: `C:\MySolution\tests\Calculator.Tests\Operations\AddOperationTests.cs`

---

## Common Project Structures

### Structure 1: src/tests Separation (Recommended)

```
MySolution/
├── src/
│   ├── Calculator/
│   │   ├── Calculator.csproj
│   │   ├── Calculator.cs
│   │   └── Operations/
│   │       ├── AddOperation.cs
│   │       └── DivideOperation.cs
│   └── Calculator.Core/
│       ├── Calculator.Core.csproj
│       └── MathEngine.cs
├── tests/
│   ├── Calculator.Tests/
│   │   ├── Calculator.Tests.csproj
│   │   ├── CalculatorTests.cs
│   │   └── Operations/
│   │       ├── AddOperationTests.cs
│   │       └── DivideOperationTests.cs
│   └── Calculator.Core.Tests/
│       ├── Calculator.Core.Tests.csproj
│       └── MathEngineTests.cs
└── MySolution.sln
```

**Path Resolution Examples**:

**Example 1**:
- Source: `src/Calculator/Calculator.cs`
- Test: `tests/Calculator.Tests/CalculatorTests.cs`

**Example 2**:
- Source: `src/Calculator/Operations/AddOperation.cs`
- Test: `tests/Calculator.Tests/Operations/AddOperationTests.cs`

**Example 3**:
- Source: `src/Calculator.Core/MathEngine.cs`
- Test: `tests/Calculator.Core.Tests/MathEngineTests.cs`

---

### Structure 2: Flat Projects (Simpler)

```
MySolution/
├── Calculator/
│   ├── Calculator.csproj
│   ├── Calculator.cs
│   └── Operations/
│       └── AddOperation.cs
├── Calculator.Tests/
│   ├── Calculator.Tests.csproj
│   ├── CalculatorTests.cs
│   └── Operations/
│       └── AddOperationTests.cs
└── MySolution.sln
```

**Path Resolution**:
- Source: `Calculator/Calculator.cs`
- Test: `Calculator.Tests/CalculatorTests.cs`

---

### Structure 3: Multiple Test Categories

```
MySolution/
├── src/
│   └── Calculator/
│       ├── Calculator.csproj
│       └── Calculator.cs
├── tests/
│   ├── unit/
│   │   └── Calculator.UnitTests/
│   │       ├── Calculator.UnitTests.csproj
│   │       └── CalculatorTests.cs
│   └── integration/
│       └── Calculator.IntegrationTests/
│           ├── Calculator.IntegrationTests.csproj
│           └── CalculatorIntegrationTests.cs
└── MySolution.sln
```

**Path Resolution** (Unit Tests):
- Source: `src/Calculator/Calculator.cs`
- Test: `tests/unit/Calculator.UnitTests/CalculatorTests.cs`

---

## Edge Cases

### Case 1: Nested Namespaces

**Source Structure**:
```
Calculator/
├── Calculator.csproj
└── Services/
    └── Advanced/
        └── ComplexCalculator.cs
```

**Test Path**:
```
Calculator.Tests/
├── Calculator.Tests.csproj
└── Services/
    └── Advanced/
        └── ComplexCalculatorTests.cs
```

**Rule**: Mirror full namespace hierarchy in test project

---

### Case 2: Multiple Source Projects

**Source**:
```
src/
├── Calculator/
│   └── Calculator.cs
├── Calculator.Core/
│   └── Engine.cs
└── Calculator.Utils/
    └── Helpers.cs
```

**Tests**:
```
tests/
├── Calculator.Tests/
│   └── CalculatorTests.cs
├── Calculator.Core.Tests/
│   └── EngineTests.cs
└── Calculator.Utils.Tests/
    └── HelpersTests.cs
```

**Rule**: Separate test project for each source project

---

### Case 3: Partial Classes

**Source**:
```
Calculator/
├── Calculator.cs
└── Calculator.Operations.cs  (partial class)
```

**Test**:
```
Calculator.Tests/
└── CalculatorTests.cs  (tests all partials)
```

**Rule**: Single test file for all partials of same class

---

## File Naming Patterns

### Test File Naming

**Pattern**: `{ClassName}Tests.cs`

**Examples**:
- `Calculator.cs` → `CalculatorTests.cs`
- `AddOperation.cs` → `AddOperationTests.cs`
- `UserService.cs` → `UserServiceTests.cs`

**Alternative Patterns** (Less Common):
- `{ClassName}Test.cs` (singular)
- `Test{ClassName}.cs` (prefix)
- `{ClassName}.Tests.cs` (with dot)

**Recommendation**: Use `{ClassName}Tests.cs` for consistency with .NET conventions

---

### Test Class Naming

**Pattern**: `{ClassName}Tests`

```csharp
// Source file: Calculator.cs
public class Calculator { }

// Test file: CalculatorTests.cs
public class CalculatorTests { }
```

---

## Validation Rules

### ✅ Valid Locations

- `tests/Calculator.Tests/CalculatorTests.cs`
- `tests/unit/Calculator.UnitTests/CalculatorTests.cs`
- `Calculator.Tests/CalculatorTests.cs` (adjacent)
- `tests/Calculator.Tests/Operations/AddOperationTests.cs` (nested)

---

### 🚫 Invalid Locations

- `.claude-tests/CalculatorTests.cs` ❌
- `.claude/CalculatorTests.cs` ❌
- `C:\Temp\CalculatorTests.cs` ❌
- `Calculator/CalculatorTests.cs` ❌ (in source project)
- Root of solution ❌

---

## Tool Integration

### Write Agent Integration

```csharp
// Pseudocode for Write Agent

function DetermineTestPath(sourceFile, projectRoot)
{
    // Step 1: Find solution file
    var solutionFile = FindSolutionFile(projectRoot);

    // Step 2: Identify source project
    var sourceProject = GetProjectFromFile(sourceFile);
    // Example: "Calculator" from "src/Calculator/Calculator.csproj"

    // Step 3: Find or create test project
    var testProject = FindTestProject(solutionFile, sourceProject);
    // Look for "Calculator.Tests" or "Calculator.UnitTests"

    if (testProject == null)
    {
        // Create default test project structure
        testProject = $"tests/{sourceProject}.Tests";
        CreateTestProject(testProject, sourceProject);
    }

    // Step 4: Calculate relative path within source project
    var sourceProjectRoot = GetProjectRoot(sourceFile);
    var relativePath = sourceFile.RelativeTo(sourceProjectRoot).DirectoryName;
    // Example: "Operations" from "src/Calculator/Operations/AddOperation.cs"

    // Step 5: Apply test naming convention
    var sourceClassName = Path.GetFileNameWithoutExtension(sourceFile);
    var testFileName = $"{sourceClassName}Tests.cs";

    // Step 6: Construct test path
    var testPath = Path.Combine(projectRoot, testProject, relativePath, testFileName);
    // Example: "C:\MySolution\tests\Calculator.Tests\Operations\AddOperationTests.cs"

    // Step 7: Validate
    if (testPath.Contains(".claude-tests") || testPath.Contains(".claude"))
    {
        throw new InvalidPathException("Test cannot be in .claude directories");
    }

    return testPath;
}
```

---

## Examples

### Example 1: Simple Project

**Input**:
- Source: `C:\MyProject\Calculator\Calculator.cs`
- Project root: `C:\MyProject\`
- Solution: `C:\MyProject\MyProject.sln`

**Output**:
- Test: `C:\MyProject\Calculator.Tests\CalculatorTests.cs`

---

### Example 2: src/tests Structure

**Input**:
- Source: `C:\MySolution\src\Calculator\Operations\AddOperation.cs`
- Project root: `C:\MySolution\`
- Solution: `C:\MySolution\MySolution.sln`

**Output**:
- Test: `C:\MySolution\tests\Calculator.Tests\Operations\AddOperationTests.cs`

---

### Example 3: Nested Namespace

**Input**:
- Source: `C:\MySolution\src\Calculator\Services\Advanced\ComplexCalculator.cs`
- Project root: `C:\MySolution\`

**Output**:
- Test: `C:\MySolution\tests\Calculator.Tests\Services\Advanced\ComplexCalculatorTests.cs`

---

## Summary

**Key Principles**:
1. C# tests always in separate test projects
2. Test project naming: `{ProjectName}.Tests` or `{ProjectName}.UnitTests`
3. Mirror source directory structure in test project
4. Test file naming: `{ClassName}Tests.cs`
5. **NEVER use `.claude-tests/` or temporary directories**
6. Create test project if it doesn't exist

**Priority Order**:
1. Solution file test project references
2. Existing `{ProjectName}.Tests` directory
3. Existing `{ProjectName}.UnitTests` directory
4. Create `tests/{ProjectName}.Tests/` structure
5. Fallback: `{ProjectName}.Tests/` adjacent to source

---

**Last Updated**: 2025-12-10
**Status**: Phase 4 - Systems Languages
**Phase**: Complete
