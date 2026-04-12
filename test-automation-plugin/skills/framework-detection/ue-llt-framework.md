# Unreal Engine Low Level Tests (LLT) Framework Detection

**Framework**: Unreal Engine LowLevelTest (UE LLT)
**Base**: Catch2 v3.4.0+ with UE-specific wrappers
**Build System**: UnrealBuildTool (UBT)
**Language**: C++
**Official Docs**: https://docs.example.com/documentation/en-us/unreal-engine/low-level-tests-in-unreal-engine

---

## Overview

Unreal Engine LowLevelTest (LLT) is a testing framework that wraps Catch2 v3.4.0+ with Unreal-specific build infrastructure and integration. Unlike standalone Catch2 projects, UE LLT uses UnrealBuildTool (UBT) for compilation and provides tight integration with UE types and systems.

### Key Characteristics

- **Build System**: UnrealBuildTool (UBT) with C# build rules, NOT CMake/Make/Bazel
- **Test Module Rules**: `TestModuleRules` inheritance instead of standard `ModuleRules`
- **Test Target Rules**: `TestTargetRules` for platform-specific test configuration
- **Test Harness**: `TestHarness.h` UE wrapper around Catch2 (not direct Catch2 headers)
- **UE Integration**: Tight integration with UE types (FString, TArray, UObject, etc.)

### Critical Distinctions from Standalone Catch2

| Aspect | Standalone Catch2 | UE LLT (Catch2 Wrapper) |
|--------|-------------------|-------------------------|
| Build System | CMake/Make/Bazel | UnrealBuildTool (UBT) |
| Build Rules | Standard CMakeLists.txt | TestModuleRules (.Build.cs) |
| Target Config | CMake targets | TestTargetRules (.Target.cs) |
| Headers | `#include <catch2/catch_test_macros.hpp>` | `#include "TestHarness.h"` |
| Plugin Structure | N/A | .uplugin manifest files |
| Test Macros | TEST_CASE, SECTION, etc. | Same macros via TestHarness.h |
| UE Types | Not available | FString, TArray, UObject, etc. |

---

## Detection Patterns

### 1. Config Files (Weight: 15 - Highest Priority)

#### TestModuleRules Inheritance (.Build.cs)

**Pattern**: Test modules inherit from `TestModuleRules` (not standard `ModuleRules`)

**Example**:
```csharp
// WarpUtilsTests.Build.cs
using UnrealBuildTool;

public class WarpUtilsTests : TestModuleRules  // <-- KEY PATTERN
{
    static WarpUtilsTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "WarpUtils Tests";
        TestMetadata.TestShortName = "WarpUtils";
    }

    public WarpUtilsTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "Engine",
                "WarpUtils"
            });
    }
}
```

**Detection Regex**: `:\s*TestModuleRules\s*\{`

**Weight**: 15 points (definitive proof of UE LLT)

#### TestTargetRules Inheritance (.Target.cs)

**Pattern**: Test target files inherit from `TestTargetRules` (not standard `TargetRules`)

**Example**:
```csharp
// WarpUtilsTests.Target.cs
using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class WarpUtilsTestsTarget : TestTargetRules  // <-- KEY PATTERN
{
    public WarpUtilsTestsTarget(TargetInfo Target) : base(Target)
    {
        bCompileAgainstEngine = true;
        bCompileAgainstCoreUObject = true;
        bMockEngineDefaults = true;
        bTestsRequireEngine = true;
        bUsePlatformFileStub = true;
        bCompileAgainstApplicationCore = true;
    }
}
```

**Detection Regex**: `:\s*TestTargetRules\s*\{`

**Weight**: 15 points (definitive proof of UE LLT)

---

### 2. Import Patterns (Weight: 8 - High Confidence)

#### TestHarness.h Include

**Pattern**: `#include "TestHarness.h"` in test source files

**Example**:
```cpp
#include "CoreMinimal.h"
#include "TestHarness.h"  // <-- UE LLT-specific (NOT <catch2/...>)
#include "Blueprints/WarpUtilsBlueprintLibrary.h"

TEST_CASE("WarpUtils::UWarpUtilsBlueprintLibrary::SavePFM", "[warputils]")
{
    // Test implementation
}
```

**Detection Regex**: `#include\s+"TestHarness\.h"`

**Weight**: 8 points (unique to UE LLT)

**Anti-Pattern**: UE LLT **never** includes `<catch2/catch_test_macros.hpp>` or `<catch2/catch.hpp>`

---

### 3. Code Patterns (Weight: 5 - Medium Confidence)

#### TEST_CASE with UE Naming Conventions

**Pattern**: TEST_CASE with UE module::class::method naming convention

**Example**:
```cpp
TEST_CASE("WarpUtils::UWarpUtilsBlueprintLibrary::SavePFM", "[warputils]")
//         ^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^
//         UE Module  UE Class (U prefix)         Method
{
    // Test implementation
}

TEST_CASE("CommChannelsRuntime::FCommChannelNode::ConnectTo", "[commchannels]")
//         ^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^ ^^^^^^^^^
//         UE Module Name     UE Class (F prefix)   Method
{
    FCommChannelNode NodeA;  // <-- UE types (F prefix)
    FCommChannelNode NodeB;
    bool bConnected = NodeA.ConnectTo(&NodeB);  // <-- UE naming (b prefix)
    REQUIRE(bConnected == true);
}
```

**Detection Regex**: `TEST_CASE\s*\(\s*"[^"]*::(F|U)[A-Z]\w+::`

**Weight**: 5 points for UE naming, 2 points for generic TEST_CASE

#### UE Type Usage in Tests

**Pattern**: Usage of UE-specific types (FString, TArray, UObject, etc.)

**Common UE Types**:
- `FString` - UE string type
- `TArray` - UE dynamic array
- `TMap` - UE map container
- `TSharedPtr` - UE shared pointer
- `UObject` - UE object base class
- `FName` - UE name type
- `FText` - UE localized text

**Detection Regex**: `\b(FString|TArray|TMap|TSharedPtr|UObject|FName|FText)\b`

**Weight**: 3 points per file (supporting evidence)

---

### 4. Directory Structure (Weight: 5 - Supporting Evidence)

#### Tests/ Directory at Plugin Root

**Pattern**: `Tests/<TestModuleName>/` directory structure at plugin or module level

**Example Structure**:
```
Plugins/WarpUtils/
├── WarpUtils.uplugin              # Plugin manifest
├── Source/
│   └── WarpUtils/                 # Source module
│       ├── WarpUtils.Build.cs
│       └── Private/
│           └── WarpUtilsBlueprintLibrary.cpp
└── Tests/                         # <-- Tests at plugin root
    └── WarpUtilsTests/            # <-- Test module name
        ├── WarpUtilsTests.Build.cs      # <-- TestModuleRules
        ├── WarpUtilsTests.Target.cs     # <-- TestTargetRules
        └── Private/
            └── WarpUtilsBlueprintLibraryTests.cpp
```

**Detection Pattern**: Look for `Tests/*/` directories with `.Build.cs` files at plugin root (same level as `.uplugin`)

**Weight**: 5 points (contextual support)

#### Plugin Manifests (.uplugin)

**Pattern**: Plugin manifests with test module references

**Weight**: 5 points (contextual support)

---

### 5. Build System Anti-Patterns (Weight: 0 - Exclusion Criteria)

**CRITICAL**: UE LLT does NOT use CMake/Make/Bazel.

**Anti-Patterns that EXCLUDE UE LLT**:
- ❌ `CMakeLists.txt` with `find_package(Catch2)`
- ❌ `Makefile` with Catch2 linking flags
- ❌ Bazel `BUILD` files with Catch2 dependencies
- ❌ `#include <catch2/catch_test_macros.hpp>` headers

If any of these are found, it's **standalone Catch2**, NOT UE LLT.

---

## Confidence Scoring Algorithm

### Weighted Scoring Formula

```python
def calculate_llt_confidence(scores):
    """
    Calculate confidence score for UE LLT framework detection.

    Args:
        scores: dict with keys: build_cs, target_cs, test_harness,
                test_case, ue_types, directory, uplugin

    Returns:
        float: Confidence score 0.0-1.0
    """
    # Maximum possible score
    max_score = 15 + 15 + 8 + 5 + 5 + 5 + 5  # 58 total

    # Actual score
    actual_score = (
        scores.get("build_cs", 0) +       # Weight: 15
        scores.get("target_cs", 0) +      # Weight: 15
        scores.get("test_harness", 0) +   # Weight: 8
        scores.get("test_case", 0) +      # Weight: 5
        scores.get("ue_types", 0) +       # Weight: 5
        scores.get("directory", 0) +      # Weight: 5
        scores.get("uplugin", 0)          # Weight: 5
    )

    # Confidence = actual / max, capped at 1.0
    confidence = min(actual_score / max_score, 1.0)

    return confidence
```

### Scoring Tiers

| Confidence Range | Interpretation | Required Evidence |
|------------------|----------------|-------------------|
| **0.9 - 1.0** | **Definitive** | TestModuleRules + TestTargetRules + TestHarness.h |
| **0.7 - 0.89** | **High** | TestModuleRules + TestHarness.h (or 2 of 3 top signals) |
| **0.5 - 0.69** | **Medium** | TestModuleRules OR TestHarness.h + supporting evidence |
| **0.3 - 0.49** | **Low** | TEST_CASE + UE types + directory structure (no definitive evidence) |
| **< 0.3** | **Insufficient** | Not recommended to report as UE LLT |

### Evidence Requirements

To avoid false positives, require **at least 2 types of evidence** AND one of:
- TestModuleRules inheritance (.Build.cs), OR
- TestHarness.h include, OR
- TestTargetRules inheritance (.Target.cs)

**Minimum Reporting Threshold**: 0.5 (50%) to report UE LLT as detected.

---

## Detection Decision Tree

```
START: Detect C++ testing framework

1. Check for UnrealBuildTool build files
   ├─ Found TestModuleRules in .Build.cs?
   │  └─ YES → **UE LLT (High Confidence)** → Gather supporting evidence
   └─ NO → Continue

2. Check for Catch2 headers
   ├─ Found #include "TestHarness.h"?
   │  ├─ YES → **UE LLT (High Confidence)** → Gather supporting evidence
   │  └─ NO → Continue
   ├─ Found #include <catch2/catch_test_macros.hpp>?
   │  └─ YES → **Standalone Catch2 (Not UE LLT)** → STOP

3. Check for build system
   ├─ Found CMakeLists.txt with find_package(Catch2)?
   │  └─ YES → **Standalone Catch2 (Not UE LLT)** → STOP
   ├─ Found Makefile with Catch2 linking?
   │  └─ YES → **Standalone Catch2 (Not UE LLT)** → STOP
   └─ NO standard build system → Continue

4. Check for UE context
   ├─ Found .uplugin or .uproject files?
   │  └─ YES → **Likely UE LLT** (check for Tests/ directory)
   └─ NO → **Standalone Catch2 or other framework**

5. Check for TEST_CASE patterns
   ├─ Found TEST_CASE with UE naming (F/U prefix, :: separators)?
   │  └─ YES → **Likely UE LLT** (medium confidence)
   └─ NO → **Standalone Catch2** (if TEST_CASE found at all)

RESULT: Primary framework + confidence score
```

---

## Implementation Example

```python
def detect_ue_llt_framework(project_path):
    """
    Detect UE LLT framework in a project.

    Returns:
        {
            "framework": "ue-llt" | None,
            "confidence": float 0.0-1.0,
            "evidence": List[str],
            "build_system": "ue-ubt",
            "catch2_version": "3.4.0+",
            "ue_wrapper": True
        }
    """
    scores = {
        "build_cs": 0,
        "target_cs": 0,
        "test_harness": 0,
        "test_case": 0,
        "ue_types": 0,
        "directory": 0,
        "uplugin": 0
    }
    evidence = []

    # 1. Check for TestModuleRules (.Build.cs)
    build_cs_files = glob(join(project_path, "**/Tests/**/*.Build.cs"), recursive=True)
    for build_file in build_cs_files[:10]:
        content = read_file(build_file)
        if re.search(r":\s*TestModuleRules\s*\{", content):
            scores["build_cs"] = 15
            evidence.append(f"TestModuleRules inheritance in {build_file}")
            break

    # 2. Check for TestTargetRules (.Target.cs)
    target_cs_files = glob(join(project_path, "**/Tests/**/*.Target.cs"), recursive=True)
    for target_file in target_cs_files[:10]:
        content = read_file(target_file)
        if re.search(r":\s*TestTargetRules\s*\{", content):
            scores["target_cs"] = 15
            evidence.append(f"TestTargetRules inheritance in {target_file}")
            break

    # 3. Check for TestHarness.h imports
    test_files = glob(join(project_path, "**/Tests/**/*.cpp"), recursive=True)
    for test_file in test_files[:20]:
        content = read_file(test_file)
        if re.search(r'#include\s+"TestHarness\.h"', content):
            scores["test_harness"] = 8
            evidence.append(f'TestHarness.h include in {test_file}')
            break

    # Early exit if high confidence
    if scores["build_cs"] >= 15 or scores["test_harness"] >= 8:
        # Gather additional supporting evidence

        # TEST_CASE patterns
        for test_file in test_files[:20]:
            content = read_file(test_file)
            if re.search(r'TEST_CASE\s*\(\s*"[^"]*::(F|U)[A-Z]\w+::', content):
                scores["test_case"] = 5
                evidence.append(f"UE-style TEST_CASE in {test_file}")
                break

        # UE types
        ue_types = ["FString", "TArray", "TMap", "UObject"]
        for test_file in test_files[:20]:
            content = read_file(test_file)
            for ue_type in ue_types:
                if re.search(rf'\b{ue_type}\b', content):
                    scores["ue_types"] = 3
                    evidence.append(f"{ue_type} usage in tests")
                    break

        # Directory structure
        tests_dirs = glob(join(project_path, "**/Tests/*/*.Build.cs"), recursive=True)
        if tests_dirs:
            scores["directory"] = 5
            evidence.append("UE test directory structure found")

        # Plugin manifests
        uplugin_files = glob(join(project_path, "**/*.uplugin"), recursive=True)
        if uplugin_files:
            scores["uplugin"] = 5
            evidence.append(".uplugin manifest found")

        confidence = calculate_llt_confidence(scores)

        return {
            "framework": "ue-llt",
            "confidence": confidence,
            "evidence": evidence,
            "build_system": "ue-ubt",
            "catch2_version": "3.4.0+",
            "ue_wrapper": True
        }

    # Not UE LLT
    return None
```

---

## Testing and Validation

### Test Cases

**Positive Tests** (Should detect UE LLT with >0.9 confidence):
- `Engine/Plugins/Runtime/WarpUtils/Tests/WarpUtilsTests/`
- `Engine/Plugins/AudioInsightsRuntime/Tests/AudioInsightsRuntimeTests/`
- Fortnite: `Plugins/CommChannels/Tests/CommChannelsTests/`

**Negative Tests** (Should NOT detect as UE LLT):
- Public Catch2 projects with CMakeLists.txt
- Standalone C++ projects with `<catch2/...>` headers
- Non-UE C++ projects

**Edge Cases**:
- UE plugin without tests (should not detect)
- Mixed Catch2 and UE LLT (should detect both)
- Partial UE LLT setup (medium confidence + warning)

### Success Criteria

- **Precision**: False positive rate < 5%
- **Recall**: Detection rate > 95% for Fortnite LLT modules
- **Performance**: < 2 seconds for large UE projects
- **Minimum Confidence**: Report only when confidence >= 0.5

---

## References

- Unreal Engine LLT Docs: https://docs.example.com/documentation/en-us/unreal-engine/low-level-tests-in-unreal-engine
- Catch2 Documentation: https://github.com/catchorg/Catch2
- UnrealBuildTool: https://docs.example.com/documentation/en-us/unreal-engine/unreal-build-tool
