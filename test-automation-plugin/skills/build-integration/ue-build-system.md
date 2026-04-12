# Unreal Engine Build System (UnrealBuildTool)

**Version**: 1.0.0
**Build System**: UnrealBuildTool (UBT)
**Test Framework**: UE Low Level Tests (Catch2 v3.4.0+)

## Overview

Unreal Engine uses UnrealBuildTool (UBT) for compilation. UE Low Level Tests (LLT) are standalone test executables that use TestModuleRules and TestTargetRules for build configuration.

## Key Concepts

### Target Naming Convention

**CRITICAL**: The build target name must match the `.Target.cs` filename **without the `.Target.cs` extension**.

```
File: SecurePackageReaderTests.Target.cs
Target Name: SecurePackageReaderTests (NOT SecurePackageReaderTestsTarget)
```

**Examples**:
- ✅ Correct: `Build.sh FNOnlineFrameworkTests ...`
- ❌ Wrong: `Build.sh FNOnlineFrameworkTestsTarget ...`

The class name inside `.Target.cs` includes "Target" suffix:
```csharp
// File: SecurePackageReaderTests.Target.cs
public class SecurePackageReaderTestsTarget : TestTargetRules
{
    // Build target name is "SecurePackageReaderTests" (file base name)
}
```

### Project Discovery

UBT discovers test projects through `Default.uprojectdirs` at the repository root.

**Path Structure**:
```
/path/to/Fortnite_Main/
├── Default.uprojectdirs           # Lists directories to search for projects
├── FortniteGame/
│   └── Plugins/
│       └── <PluginName>/
│           └── Tests/              # ← Add this path to Default.uprojectdirs
│               └── <TestName>Tests/
│                   ├── <TestName>Tests.uproject
│                   ├── <TestName>Tests.Target.cs
│                   ├── <TestName>Tests.Build.cs
│                   └── Private/
│                       └── <TestName>Tests.cpp
```

**Default.uprojectdirs Entry**:
```
FortniteGame/Plugins/<PluginName>/Tests/
```

**Important**: Point to the `Tests/` directory, NOT the individual test subdirectory.

- ✅ Correct: `FortniteGame/Plugins/ForEngine/ValkyrieEngine/Tests/`
- ❌ Wrong: `FortniteGame/Plugins/ForEngine/ValkyrieEngine/Tests/SecurePackageReaderTests/`

**Why**: UBT searches 1 level deep in directories listed in Default.uprojectdirs to find `.uproject` files.

### .uproject File

Required for UBT test discovery. Minimal format:

```json
{
    "FileVersion": 3,
    "EngineAssociation": "",
    "Category": "",
    "Description": "",
    "TargetPlatforms": [
        "Windows",
        "Mac",
        "Linux"
    ]
}
```

**Note**: Do NOT include a `Modules` section for LLT tests (unlike some other UE project types).

## Build Commands

### Building Tests

**Syntax**:
```bash
cd /path/to/repository_root
./Engine/Build/BatchFiles/Mac/Build.sh <TestModuleName> Mac Development -Project="<path>/FortniteGame/FortniteGame.uproject"
```

**Example**:
```bash
cd /Users/stephen.ma/Fornite_Main
./Engine/Build/BatchFiles/Mac/Build.sh SecurePackageReaderTests Mac Development -Project="/Users/stephen.ma/Fornite_Main/FortniteGame/FortniteGame.uproject"
```

**Platform-Specific Scripts**:
- Mac: `Engine/Build/BatchFiles/Mac/Build.sh`
- Windows: `Engine/Build/BatchFiles/Build.bat`
- Linux: `Engine/Build/BatchFiles/Linux/Build.sh`

**Configuration Options**:
- `Development` - Debug symbols with optimizations
- `Debug` - Full debug symbols, no optimizations
- `Shipping` - Fully optimized, no debug symbols

**Important**: Always specify the `-Project` flag pointing to `FortniteGame/FortniteGame.uproject`, not the test's `.uproject` file.

### Running Tests

**Syntax**:
```bash
cd /path/to/repository_root
./Engine/Binaries/Mac/<TestModuleName> [Catch2-args]
```

**Example**:
```bash
cd /Users/stephen.ma/Fornite_Main
./Engine/Binaries/Mac/SecurePackageReaderTests -s -r compact
```

**Common Catch2 Arguments**:
- `-s` - Show successful test assertions
- `-r compact` - Compact output format
- `-r xml` - XML output for CI integration
- `[tag]` - Run tests with specific tag (e.g., `[Critical]`)
- `-#` - Use specific test shard (for parallel execution)

**Output Location**:
- Mac: `Engine/Binaries/Mac/<TestModuleName>`
- Windows: `Engine/Binaries/Win64/<TestModuleName>.exe`
- Linux: `Engine/Binaries/Linux/<TestModuleName>`

## Project Regeneration

After adding new test modules or modifying `.Target.cs` files, regenerate project files:

```bash
cd /path/to/repository_root
./GenerateProjectFiles.sh -project="/path/to/FortniteGame/FortniteGame.uproject"
```

**When to regenerate**:
- Added new entry to `Default.uprojectdirs`
- Created new `.Target.cs` file
- Modified test module dependencies
- After major UE version updates

**Cache Clearing**:

If UBT cannot find a target after project regeneration, clear the rules cache:

```bash
rm -rf /path/to/repository_root/FortniteGame/Intermediate/Build/BuildRules/
rm -rf /path/to/repository_root/Engine/Intermediate/Build/BuildRules/
```

Then retry the build.

## Build.cs Configuration

Test modules use `TestModuleRules` (not `ModuleRules`):

```csharp
public class SecurePackageReaderTests : TestModuleRules
{
    static SecurePackageReaderTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "SecurePackageReader Tests";
        TestMetadata.TestShortName = "SecurePackageReader";
    }

    public SecurePackageReaderTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "SecurePackageReader"  // Module under test
            });
    }
}
```

**Minimal Dependencies**:
- `Core` - Always required for LLT tests
- `CoreUObject` - Required if testing UObject-derived classes
- Module under test
- Modules specifically needed by test code

## Target.cs Configuration

Test targets use `TestTargetRules` (not `TargetRules`):

```csharp
[SupportedPlatforms(UnrealPlatformClass.All)]
public class SecurePackageReaderTestsTarget : TestTargetRules
{
    public SecurePackageReaderTestsTarget(TargetInfo Target) : base(Target)
    {
        // Include only what you use - match Build.cs dependencies
        bCompileAgainstCoreUObject = true;
    }
}
```

**Engine Flags** (only add if corresponding module in Build.cs):
- `bCompileAgainstEngine = true` - If "Engine" in PrivateDependencyModuleNames
- `bCompileAgainstCoreUObject = true` - If "CoreUObject" in PrivateDependencyModuleNames
- `bCompileAgainstApplicationCore = true` - If "ApplicationCore" in PrivateDependencyModuleNames

**Additional Flags** (when using Engine):
```csharp
bMockEngineDefaults = true;       // Use mock engine initialization
bTestsRequireEngine = true;       // Tests need engine subsystems
bUsePlatformFileStub = true;      // Use file system stub
```

**Global Definitions**:
```csharp
GlobalDefinitions.Add("WITH_LOW_LEVEL_TESTS=1");
```

## Troubleshooting

### "Couldn't find target rules file"

**Symptoms**:
```
Couldn't find target rules file for target 'SecurePackageReaderTestsTarget' in rules assembly 'UE5Rules'
```

**Causes**:
1. ❌ Using wrong target name with "Target" suffix
   - Fix: Use `SecurePackageReaderTests`, not `SecurePackageReaderTestsTarget`

2. ❌ Missing Default.uprojectdirs entry
   - Fix: Add path to `Tests/` directory in Default.uprojectdirs

3. ❌ Wrong Default.uprojectdirs path (pointing to specific test subdirectory)
   - Fix: Point to `Tests/` directory, not `Tests/<TestName>/`

4. ❌ Missing `.uproject` file
   - Fix: Create minimal `.uproject` file in test directory

5. ❌ Need to regenerate project files
   - Fix: Run `./GenerateProjectFiles.sh`

6. ❌ Stale build cache
   - Fix: Clear `Intermediate/Build/BuildRules/` directories

### Compilation Errors

**Missing includes**:
```cpp
// Common includes for LLT tests
#include "TestHarness.h"                    // Catch2 TEST_CASE, REQUIRE, etc.
#include "Serialization/MemoryReader.h"     // FMemoryReader
#include "Serialization/MemoryWriter.h"     // FMemoryWriter
#include "UObject/PackageFileSummary.h"     // FPackageFileSummary
```

**API mismatches**: Check UE source for current API signatures. Generated test code may need adjustment for engine version.

## Integration with test-engineering:test-generate

### Build Phase

After generating test scaffolding, invoke build:

```python
def invoke_llt_build(test_module_name: str, repo_root: Path) -> Dict:
    """
    Build UE LLT test module using UnrealBuildTool.

    Args:
        test_module_name: Name of test module (e.g., "SecurePackageReaderTests")
        repo_root: Repository root containing Engine/ and FortniteGame/

    Returns:
        Build result with success status, warnings, errors
    """
    platform = detect_platform()  # "Mac", "Win64", or "Linux"
    build_script = {
        "Mac": "Engine/Build/BatchFiles/Mac/Build.sh",
        "Win64": "Engine/Build/BatchFiles/Build.bat",
        "Linux": "Engine/Build/BatchFiles/Linux/Build.sh"
    }[platform]

    fortnite_uproject = repo_root / "FortniteGame" / "FortniteGame.uproject"

    cmd = [
        str(repo_root / build_script),
        test_module_name,  # NOT test_module_name + "Target"
        platform,
        "Development",
        f"-Project={fortnite_uproject}"
    ]

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, timeout=300)

    return {
        'success': result.returncode == 0,
        'stdout': result.stdout.decode('utf-8'),
        'stderr': result.stderr.decode('utf-8'),
        'exit_code': result.returncode
    }
```

### Run Phase

After successful build, execute tests:

```python
def invoke_llt_run(test_module_name: str, repo_root: Path) -> Dict:
    """
    Run UE LLT test executable.

    Args:
        test_module_name: Name of test module (e.g., "SecurePackageReaderTests")
        repo_root: Repository root containing Engine/Binaries/

    Returns:
        Test execution result with pass/fail counts, failures
    """
    platform = detect_platform()
    binary_path = {
        "Mac": repo_root / "Engine" / "Binaries" / "Mac" / test_module_name,
        "Win64": repo_root / "Engine" / "Binaries" / "Win64" / f"{test_module_name}.exe",
        "Linux": repo_root / "Engine" / "Binaries" / "Linux" / test_module_name
    }[platform]

    if not binary_path.exists():
        return {
            'success': False,
            'error': f'Test binary not found: {binary_path}'
        }

    cmd = [str(binary_path), "-r", "xml"]  # XML output for parsing

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, timeout=300)

    # Parse Catch2 XML output
    parsed = parse_catch2_xml(result.stdout.decode('utf-8'))

    return {
        'success': result.returncode == 0,
        'passed_count': parsed['passed'],
        'failed_count': parsed['failed'],
        'skipped_count': parsed['skipped'],
        'failures': parsed['failure_details'],
        'execution_time_ms': parsed['duration_ms']
    }
```

## Reference Examples

### FNOnlineFramework Tests

**Location**: `FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/`

**Default.uprojectdirs entry**:
```
FortniteGame/Plugins/FNOnlineFramework/Tests/
```

**Build command**:
```bash
./Engine/Build/BatchFiles/Mac/Build.sh FNOnlineFrameworkTests Mac Development -Project="/Users/stephen.ma/Fornite_Main/FortniteGame/FortniteGame.uproject"
```

**Target.cs excerpt**:
```csharp
public class FNOnlineFrameworkTestsTarget : TestTargetRules
{
    public FNOnlineFrameworkTestsTarget(TargetInfo Target) : base(Target)
    {
        bCompileAgainstEngine = true;
        bCompileAgainstCoreUObject = false;
        bCompileAgainstApplicationCore = true;
        bTestsRequireEngine = true;
        bMockEngineDefaults = true;
        bUsePlatformFileStub = true;
    }
}
```

## Platform-Specific Notes

### Mac

- Build output: `Engine/Binaries/Mac/<TestModuleName>` (no .exe extension)
- Requires Xcode command line tools
- SDK version checked during build (e.g., "Mac SDK 26.2")

### Windows

- Build output: `Engine/Binaries/Win64/<TestModuleName>.exe`
- Requires Visual Studio toolchain
- May require GDK for console platform builds

### Linux

- Build output: `Engine/Binaries/Linux/<TestModuleName>`
- Requires clang toolchain
- Cross-compilation supported with appropriate SDK

## Additional Resources

- UE LLT Framework: `Engine/Source/Developer/LowLevelTestsRunner/`
- TestTargetRules: `Engine/Source/Programs/UnrealBuildTool/Configuration/TestTargetRules.cs`
- TestModuleRules: `Engine/Source/Programs/UnrealBuildTool/Configuration/TestModuleRules.cs`
- Catch2 Documentation: https://github.com/catchorg/Catch2/tree/v3.4.0
