# C# Framework Detection

**Version**: 1.0.0
**Language**: C#
**Frameworks**: xUnit, NUnit, MSTest
**Status**: Phase 4 - Systems Languages

## Overview

C# framework detection skill for identifying xUnit, NUnit, and MSTest testing frameworks in .NET projects. This skill provides detailed detection patterns, confidence scoring, and .NET-specific configuration analysis.

## Supported Frameworks

### 1. xUnit

**Description**: Modern, extensible testing framework for .NET
**Official Docs**: https://xunit.net/
**Minimum Version**: 2.4.0+
**Detection Priority**: High (most popular in modern .NET projects)

**Key Features**:
- `[Fact]` for simple tests
- `[Theory]` with `[InlineData]` for parameterized tests
- Constructor/Dispose for setup/teardown
- Parallel test execution by default

### 2. NUnit

**Description**: Classic .NET testing framework, similar to JUnit
**Official Docs**: https://nunit.org/
**Minimum Version**: 3.13.0+
**Detection Priority**: High (widely used, especially in legacy projects)

**Key Features**:
- `[Test]` for test methods
- `[TestFixture]` for test classes
- `[SetUp]` and `[TearDown]` for setup/teardown
- Rich assertion library

### 3. MSTest

**Description**: Microsoft's built-in testing framework for Visual Studio
**Official Docs**: https://docs.microsoft.com/en-us/dotnet/core/testing/unit-testing-with-mstest
**Minimum Version**: 2.2.0+
**Detection Priority**: Medium (common in enterprise/Visual Studio projects)

**Key Features**:
- `[TestMethod]` for test methods
- `[TestClass]` for test classes
- `[TestInitialize]` and `[TestCleanup]` for setup/teardown
- Native Visual Studio integration

## Detection Patterns

### xUnit Detection

#### 1. Project File Configuration (Weight: 15)

**.csproj** with xUnit PackageReference:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.6.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  </ItemGroup>
</Project>
```

**Detection Logic**:
```csharp
// Pseudocode for detection
if exists("*.csproj"):
    foreach csproj in glob("**/*.csproj"):
        content = read(csproj)

        // Check for xUnit packages
        if contains(content, '<PackageReference Include="xunit"'):
            score += 15
            evidence.append($"{csproj} contains xunit package")

        if contains(content, '<PackageReference Include="xunit.runner.visualstudio"'):
            score += 5
            evidence.append($"{csproj} contains xunit.runner.visualstudio")

        // Check for xUnit assertions package
        if contains(content, '<PackageReference Include="xunit.assert"'):
            score += 3
            evidence.append($"{csproj} contains xunit.assert")
```

#### 2. Code Patterns (Weight: 8)

**xUnit Test Class**:
```csharp
using Xunit;

public class CalculatorTests
{
    [Fact]
    public void Add_TwoNumbers_ReturnsSum()
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        var result = calculator.Add(2, 3);

        // Assert
        Assert.Equal(5, result);
    }

    [Theory]
    [InlineData(1, 2, 3)]
    [InlineData(5, 5, 10)]
    public void Add_Theory_ReturnsExpectedSum(int a, int b, int expected)
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        var result = calculator.Add(a, b);

        // Assert
        Assert.Equal(expected, result);
    }
}
```

**Detection Regex Patterns**:
```csharp
patterns = [
    @"\[Fact\]",                           // xUnit Fact attribute
    @"\[Theory\]",                         // xUnit Theory attribute
    @"\[InlineData\(",                     // xUnit InlineData attribute
    @"using Xunit;",                       // xUnit namespace
    @"Assert\.Equal\(",                    // xUnit assertion
    @"Assert\.True\(",                     // xUnit assertion
    @"Assert\.Throws<",                    // xUnit exception assertion
    @"IClassFixture<",                     // xUnit fixture interface
    @"ICollectionFixture<"                 // xUnit collection fixture
]

// Scan .cs files in test projects
foreach file in glob("**/*Test*.cs"):
    content = read(file)

    foreach pattern in patterns:
        if regex_match(pattern, content):
            score += 8
            evidence.append($"Pattern '{pattern}' found in {file}")
            break  // Count once per file
```

#### 3. Import Patterns (Weight: 5)

```csharp
using Xunit;
using Xunit.Abstractions;
```

**Detection Logic**:
```csharp
foreach file in glob("**/*.cs"):
    content = read(file)

    if contains(content, "using Xunit;"):
        score += 5
        evidence.append($"'using Xunit;' in {file}")

    if contains(content, "using Xunit.Abstractions"):
        score += 2
        evidence.append($"'using Xunit.Abstractions' in {file}")
```

### NUnit Detection

#### 1. Project File Configuration (Weight: 15)

**.csproj** with NUnit PackageReference:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="NUnit" Version="3.14.0" />
    <PackageReference Include="NUnit3TestAdapter" Version="4.5.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  </ItemGroup>
</Project>
```

**Detection Logic**:
```csharp
foreach csproj in glob("**/*.csproj"):
    content = read(csproj)

    if contains(content, '<PackageReference Include="NUnit"'):
        score += 15
        evidence.append($"{csproj} contains NUnit package")

    if contains(content, '<PackageReference Include="NUnit3TestAdapter"'):
        score += 5
        evidence.append($"{csproj} contains NUnit3TestAdapter")
```

#### 2. Code Patterns (Weight: 8)

**NUnit Test Class**:
```csharp
using NUnit.Framework;

[TestFixture]
public class CalculatorTests
{
    private Calculator _calculator;

    [SetUp]
    public void Setup()
    {
        _calculator = new Calculator();
    }

    [Test]
    public void Add_TwoNumbers_ReturnsSum()
    {
        // Arrange
        int a = 2;
        int b = 3;

        // Act
        var result = _calculator.Add(a, b);

        // Assert
        Assert.AreEqual(5, result);
    }

    [TestCase(1, 2, 3)]
    [TestCase(5, 5, 10)]
    public void Add_TestCase_ReturnsExpectedSum(int a, int b, int expected)
    {
        // Act
        var result = _calculator.Add(a, b);

        // Assert
        Assert.AreEqual(expected, result);
    }

    [TearDown]
    public void TearDown()
    {
        _calculator = null;
    }
}
```

**Detection Regex Patterns**:
```csharp
patterns = [
    @"\[Test\]",                           // NUnit Test attribute
    @"\[TestFixture\]",                    // NUnit TestFixture attribute
    @"\[TestCase\(",                       // NUnit TestCase attribute
    @"\[SetUp\]",                          // NUnit SetUp attribute
    @"\[TearDown\]",                       // NUnit TearDown attribute
    @"using NUnit\.Framework;",            // NUnit namespace
    @"Assert\.AreEqual\(",                 // NUnit assertion
    @"Assert\.IsTrue\(",                   // NUnit assertion
    @"Assert\.Throws<"                     // NUnit exception assertion
]
```

#### 3. Import Patterns (Weight: 5)

```csharp
using NUnit.Framework;
```

**Detection Logic**:
```csharp
foreach file in glob("**/*.cs"):
    content = read(file)

    if contains(content, "using NUnit.Framework;"):
        score += 5
        evidence.append($"'using NUnit.Framework;' in {file}")
```

### MSTest Detection

#### 1. Project File Configuration (Weight: 15)

**.csproj** with MSTest PackageReference:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="MSTest.TestFramework" Version="3.1.0" />
    <PackageReference Include="MSTest.TestAdapter" Version="3.1.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  </ItemGroup>
</Project>
```

**Detection Logic**:
```csharp
foreach csproj in glob("**/*.csproj"):
    content = read(csproj)

    if contains(content, '<PackageReference Include="MSTest.TestFramework"'):
        score += 15
        evidence.append($"{csproj} contains MSTest.TestFramework package")

    if contains(content, '<PackageReference Include="MSTest.TestAdapter"'):
        score += 5
        evidence.append($"{csproj} contains MSTest.TestAdapter")

    if contains(content, '<PackageReference Include="Microsoft.VisualStudio.TestTools.UnitTesting"'):
        score += 10
        evidence.append($"{csproj} contains legacy MSTest package")
```

#### 2. Code Patterns (Weight: 8)

**MSTest Test Class**:
```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;

[TestClass]
public class CalculatorTests
{
    private Calculator _calculator;

    [TestInitialize]
    public void Initialize()
    {
        _calculator = new Calculator();
    }

    [TestMethod]
    public void Add_TwoNumbers_ReturnsSum()
    {
        // Arrange
        int a = 2;
        int b = 3;

        // Act
        var result = _calculator.Add(a, b);

        // Assert
        Assert.AreEqual(5, result);
    }

    [DataTestMethod]
    [DataRow(1, 2, 3)]
    [DataRow(5, 5, 10)]
    public void Add_DataDriven_ReturnsExpectedSum(int a, int b, int expected)
    {
        // Act
        var result = _calculator.Add(a, b);

        // Assert
        Assert.AreEqual(expected, result);
    }

    [TestCleanup]
    public void Cleanup()
    {
        _calculator = null;
    }
}
```

**Detection Regex Patterns**:
```csharp
patterns = [
    @"\[TestMethod\]",                     // MSTest TestMethod attribute
    @"\[TestClass\]",                      // MSTest TestClass attribute
    @"\[DataTestMethod\]",                 // MSTest DataTestMethod attribute
    @"\[DataRow\(",                        // MSTest DataRow attribute
    @"\[TestInitialize\]",                 // MSTest TestInitialize attribute
    @"\[TestCleanup\]",                    // MSTest TestCleanup attribute
    @"using Microsoft\.VisualStudio\.TestTools\.UnitTesting;",  // MSTest namespace
    @"Assert\.AreEqual\(",                 // MSTest assertion
    @"Assert\.IsTrue\(",                   // MSTest assertion
    @"Assert\.ThrowsException<"            // MSTest exception assertion
]
```

#### 3. Import Patterns (Weight: 5)

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
```

**Detection Logic**:
```csharp
foreach file in glob("**/*.cs"):
    content = read(file)

    if contains(content, "using Microsoft.VisualStudio.TestTools.UnitTesting;"):
        score += 5
        evidence.append($"'using Microsoft.VisualStudio.TestTools.UnitTesting;' in {file}")
```

## .NET Version Detection

Detect .NET version from .csproj TargetFramework:

```xml
<PropertyGroup>
  <TargetFramework>net8.0</TargetFramework>
  <!-- OR -->
  <TargetFramework>net6.0</TargetFramework>
  <!-- OR -->
  <TargetFramework>netcoreapp3.1</TargetFramework>
  <!-- OR -->
  <TargetFramework>net48</TargetFramework>
</PropertyGroup>
```

**Detection Logic**:
```csharp
function detectDotNetVersion(csprojPath):
    content = read(csprojPath)

    // Extract TargetFramework value
    match = regex_search(@"<TargetFramework>([^<]+)</TargetFramework>", content)

    if match:
        framework = match.group(1)  // e.g., "net8.0", "net6.0"

        return {
            framework: framework,
            version: parseFrameworkVersion(framework),  // "8.0", "6.0"
            isNetCore: framework.startsWith("net") && !framework.startsWith("net4"),
            isNetFramework: framework.startsWith("net4")
        }

    return null
```

**Framework Versions**:
- `net8.0` → .NET 8.0 (LTS)
- `net7.0` → .NET 7.0
- `net6.0` → .NET 6.0 (LTS)
- `net5.0` → .NET 5.0
- `netcoreapp3.1` → .NET Core 3.1 (LTS)
- `netstandard2.1` → .NET Standard 2.1
- `net48` → .NET Framework 4.8

## NuGet Package Analysis

Parse .csproj to extract all test-related packages:

```csharp
function extractNuGetPackages(csprojPath):
    content = read(csprojPath)
    packages = []

    // Match all PackageReference elements
    matches = regex_findall(@'<PackageReference Include="([^"]+)"\s+Version="([^"]+)"', content)

    foreach match in matches:
        packageName = match[0]
        version = match[1]

        packages.append({
            name: packageName,
            version: version
        })

    return packages
```

**Relevant Packages**:
- `xunit` - xUnit core
- `xunit.runner.visualstudio` - xUnit VS runner
- `NUnit` - NUnit core
- `NUnit3TestAdapter` - NUnit VS adapter
- `MSTest.TestFramework` - MSTest framework
- `MSTest.TestAdapter` - MSTest adapter
- `Microsoft.NET.Test.Sdk` - .NET test SDK (common to all)
- `Moq` - Mocking library
- `FluentAssertions` - Fluent assertion library
- `coverlet.collector` - Code coverage

## Confidence Scoring Examples

### Example 1: Pure xUnit Project

```
Project Structure:
Calculator.Tests/
├── Calculator.Tests.csproj (contains xunit package)
├── CalculatorTests.cs (contains [Fact], using Xunit)
└── SetupTests.cs (contains [Theory])

Scoring:
xUnit:
- xunit package in .csproj: +15
- xunit.runner.visualstudio in .csproj: +5
- [Fact] pattern found: +8
- using Xunit; found: +5
Total: 33

NUnit: 0
MSTest: 0

Confidence: xUnit = 33/33 = 1.0 (100%)
Result: PRIMARY=xUnit, CONFIDENCE=1.0
```

### Example 2: Pure NUnit Project

```
Project Structure:
Calculator.Tests/
├── Calculator.Tests.csproj (contains NUnit package)
├── CalculatorTests.cs (contains [Test], [TestFixture])

Scoring:
NUnit:
- NUnit package in .csproj: +15
- NUnit3TestAdapter in .csproj: +5
- [Test] pattern found: +8
- using NUnit.Framework; found: +5
Total: 33

xUnit: 0
MSTest: 0

Confidence: NUnit = 33/33 = 1.0 (100%)
Result: PRIMARY=NUnit, CONFIDENCE=1.0
```

### Example 3: Pure MSTest Project

```
Project Structure:
Calculator.Tests/
├── Calculator.Tests.csproj (contains MSTest packages)
├── CalculatorTests.cs (contains [TestMethod], [TestClass])

Scoring:
MSTest:
- MSTest.TestFramework in .csproj: +15
- MSTest.TestAdapter in .csproj: +5
- [TestMethod] pattern found: +8
- using Microsoft.VisualStudio.TestTools.UnitTesting; found: +5
Total: 33

xUnit: 0
NUnit: 0

Confidence: MSTest = 33/33 = 1.0 (100%)
Result: PRIMARY=MSTest, CONFIDENCE=1.0
```

### Example 4: Mixed xUnit/NUnit Project (Migration)

```
Project Structure:
Calculator.Tests/
├── Calculator.Tests.csproj (contains both xunit and NUnit packages)
├── NewTests.cs (xUnit style)
└── LegacyTests.cs (NUnit style)

Scoring:
xUnit:
- xunit package: +15
- [Fact] pattern: +8
- using Xunit: +5
Total: 28

NUnit:
- NUnit package: +15
- [Test] pattern: +8
- using NUnit.Framework: +5
Total: 28

Total: 56

Confidence:
- xUnit = 28/56 = 0.5 (50%)
- NUnit = 28/56 = 0.5 (50%)

Result: PRIMARY=xUnit (tie-breaker: prefer modern), SECONDARY=[NUnit], CONFIDENCE=0.5
```

### Example 5: No Test Framework (New Project)

```
Project Structure:
Calculator/
├── Calculator.csproj
└── Calculator.cs

Scoring:
xUnit: 0
NUnit: 0
MSTest: 0

Result: PRIMARY=xUnit (fallback), CONFIDENCE=0.1
Recommendation: No test framework detected. xUnit recommended for new .NET projects.
```

## Edge Cases

### 1. .NET Framework vs .NET Core/5+

**Scenario**: Different framework targets have different package patterns

**Detection Strategy**:
- .NET Framework (net48): May use older package versions
- .NET Core/5+ (net6.0, net8.0): Use modern SDK-style .csproj

**Example**:
```xml
<!-- .NET Framework -->
<TargetFramework>net48</TargetFramework>
<PackageReference Include="xunit" Version="2.4.2" />

<!-- .NET 8 -->
<TargetFramework>net8.0</TargetFramework>
<PackageReference Include="xunit" Version="2.6.0" />
```

### 2. Solution with Multiple Test Projects

**Scenario**: .sln contains multiple .csproj test projects with different frameworks

**Strategy**:
- Detect framework per test project
- Report all detected frameworks
- Use context (which project being tested) to select appropriate framework

### 3. Legacy .csproj Format

**Scenario**: Old-style .csproj with packages.config instead of PackageReference

**Detection**:
```xml
<!-- Old-style packages.config -->
<packages>
  <package id="xunit" version="2.4.0" targetFramework="net472" />
</packages>
```

**Strategy**:
- Check for packages.config file
- Parse XML for test framework packages
- Apply same scoring logic

### 4. No .csproj (Script Projects)

**Scenario**: C# script files (.csx) without project file

**Strategy**:
- Fall back to code pattern detection only
- Lower confidence scores
- Recommend creating proper .csproj

## Framework Selection Logic

```csharp
function selectPrimaryFramework(xunitScore, nunitScore, mstestScore):
    """
    Select primary testing framework based on scores.
    Prefer xUnit in case of ties (modern standard).
    """
    total = xunitScore + nunitScore + mstestScore

    // No evidence at all
    if total == 0:
        return {
            primary: "xunit",
            secondary: [],
            confidence: 0.1,
            recommendation: "No test framework detected. xUnit recommended for new .NET projects."
        }

    // Calculate confidences
    xunitConf = xunitScore / total
    nunitConf = nunitScore / total
    mstestConf = mstestScore / total

    // Find highest score
    maxScore = max(xunitScore, nunitScore, mstestScore)

    // Primary framework
    if xunitScore == maxScore:
        primary = "xunit"
        primaryConf = xunitConf
    elif nunitScore == maxScore:
        primary = "nunit"
        primaryConf = nunitConf
    else:
        primary = "mstest"
        primaryConf = mstestConf

    // Secondary frameworks (confidence >= 0.2)
    secondary = []
    if xunitConf >= 0.2 && primary != "xunit":
        secondary.append("xunit")
    if nunitConf >= 0.2 && primary != "nunit":
        secondary.append("nunit")
    if mstestConf >= 0.2 && primary != "mstest":
        secondary.append("mstest")

    return {
        primary: primary,
        secondary: secondary,
        confidence: primaryConf,
        recommendation: generateRecommendation(primary, primaryConf, secondary)
    }
```

## Output Format

```yaml
language: csharp
primary_framework: xunit
secondary_frameworks:
  - nunit
dotnet_version: net8.0
dotnet_type: .NET 8.0
confidence:
  xunit: 0.65
  nunit: 0.35
  mstest: 0.0
detection_details:
  project_files:
    - Calculator.Tests.csproj
  packages:
    - name: xunit
      version: 2.6.0
    - name: NUnit
      version: 3.14.0
    - name: Microsoft.NET.Test.Sdk
      version: 17.8.0
  code_patterns:
    - "[Fact] in CalculatorTests.cs"
    - "[Test] in LegacyTests.cs"
  import_patterns:
    - "using Xunit; in CalculatorTests.cs"
    - "using NUnit.Framework; in LegacyTests.cs"
recommendation: "Moderate detection: xunit is primary, but nunit also present (mixed usage). Consider standardizing on xUnit for new tests."
```

## Usage in Agents

### Analyze Agent

```markdown
# Read C# Framework Detection Skill
Read: skills/framework-detection/csharp-frameworks.md

# Apply Detection
1. Find all .csproj files in project
2. Parse .csproj for PackageReference elements
3. Detect .NET version from TargetFramework
4. Scan .cs files for test attributes and imports
5. Calculate weighted scores

# Score Calculation
xunitScore = sum(xunit_evidence_weights)
nunitScore = sum(nunit_evidence_weights)
mstestScore = sum(mstest_evidence_weights)

# Framework Selection
if total == 0:
    primary = "xunit"  # Fallback
    confidence = 0.1
else:
    primary = highest_score_framework
    confidence = primary_score / total_score

# Output
Return: {
    "framework": primary,
    "dotnet_version": "net8.0",
    "confidence": confidence,
    "secondary": [frameworks_with_confidence >= 0.2]
}
```

## Testing Validation

Test with sample projects:

1. **xUnit-only**: .csproj with xunit, tests with [Fact] → Expect: xunit, confidence ≥ 0.85
2. **NUnit-only**: .csproj with NUnit, tests with [Test] → Expect: nunit, confidence ≥ 0.85
3. **MSTest-only**: .csproj with MSTest, tests with [TestMethod] → Expect: mstest, confidence ≥ 0.85
4. **Mixed xUnit/NUnit**: Both packages, mixed code → Expect: xunit primary, nunit secondary
5. **No framework**: Empty .NET project → Expect: xunit (fallback), confidence = 0.1

## References

- xUnit Documentation: https://xunit.net/
- NUnit Documentation: https://nunit.org/
- MSTest Documentation: https://docs.microsoft.com/en-us/dotnet/core/testing/unit-testing-with-mstest
- .NET Project Files: https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview
- NuGet Packages: https://www.nuget.org/

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
