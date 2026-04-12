# llt-build Skill

Build LowLevelTest executables using UnrealBuildTool or BuildGraph.

## Overview

The `llt-build` skill compiles test executables for the Unreal Engine LowLevelTests (LLT) framework. It supports two build methods: direct UBT invocation (`RunUBT -Mode=Test`) and BuildGraph (`RunUAT BuildGraph`). The skill validates target names, platform SDKs, and project structure, then parses build logs to return structured results including executable paths, error counts, and failure diagnostics.

Supported platforms: Win64, Mac, Linux, PS5, PS4, Xbox, Switch, Android, iOS.

## Dependencies

- **llt-common**: Response format, data structures, validation rules, and logging instructions (see [llt-common/SKILL.md](../llt-common/SKILL.md))
- **build-integration/ue-build-system.md**: Complete UBT command syntax, target naming conventions, binary locations, and troubleshooting guide

## Critical Conventions (from E2E Testing)

**IMPORTANT**: These conventions were validated through end-to-end testing of the SecurePackageReaderTests module:

1. **Target Naming**: Build target name must match the `.Target.cs` filename **WITHOUT** the `.Target.cs` extension
   - ✅ Correct: `Build.sh SecurePackageReaderTests ...`
   - ❌ Wrong: `Build.sh SecurePackageReaderTestsTarget ...`
   - The class name inside `.Target.cs` includes "Target" suffix, but the build command does NOT

2. **Binary Location**: For plugin tests, binaries are located at:
   - `<repo_root>/FortniteGame/Binaries/<Platform>/<TestName>/` (NOT `Engine/Binaries/`)
   - Example: `FortniteGame/Binaries/Mac/SecurePackageReaderTests/SecurePackageReaderTests`

3. **Build Command**: Always use `Build.sh` (not `RunUBT.sh`) with `-Project` flag:
   ```bash
   ./Engine/Build/BatchFiles/Mac/Build.sh <TestName> Mac Development -Project="<repo>/FortniteGame/FortniteGame.uproject"
   ```

4. **Project Regeneration**: After adding new tests to `Default.uprojectdirs`, run:
   ```bash
   ./GenerateProjectFiles.sh -project="<repo>/FortniteGame/FortniteGame.uproject"
   ```

See [build-integration/ue-build-system.md](../build-integration/ue-build-system.md) for complete documentation.

## Build Orchestration Instructions

Follow these steps to compile an LLT test target:

### Step 1: Validate Inputs

Before generating any build command, validate all inputs:

1. **Validate the project root**: Confirm the directory exists and contains an `Engine/` subdirectory (or is itself within an Engine tree).
2. **Validate the test target name**: Use `llt-common` validation to ensure the target name is a valid LLT test target.
3. **Validate the platform**: Use `llt-common` validation to confirm the platform string is recognized (Win64, Mac, Linux, PS5, PS4, Xbox, Switch, Android, iOS).
4. **Check SDK installation**: Use `llt-common` to verify the platform SDK is installed. If missing, retrieve the SDK install hint and report the error.

If any validation fails, return an error response using the standard LLT JSON envelope with code `COMMAND_GENERATION_FAILED`.

### Step 2: Locate Engine Root

Find the Engine root directory from the project root:

1. Check if `<project_root>/Engine/` exists. If so, `project_root` is the engine root.
2. Otherwise, walk up to 5 parent directories looking for a directory containing `Engine/`.
3. If not found, fall back to using `project_root` as the engine root.

### Step 3: Determine Build Method

Choose between direct UBT or BuildGraph based on the user's request:

- **Direct UBT** (default): Faster for local development, works for Win64/Mac/Linux. Use `RunUBT` script.
- **BuildGraph**: Required for complex builds and console platforms. Uses `RunUAT BuildGraph` with an XML script.

### Step 4: Generate Build Command

#### Direct UBT Command

Construct the command as follows:

```
<engine_root>/Engine/Build/BatchFiles/RunUBT.sh -Mode=Test -Target=<target_name> -Platform=<platform> -Configuration=<configuration>
```

- Use `RunUBT.bat` on Windows, `RunUBT.sh` on Mac/Linux.
- **Project parameter**: Add `-Project=<path_to.uproject>` if:
  - A `.uproject` file exists in the project root AND
  - The project path contains "FortniteGame", OR
  - The target is NOT found under `Engine/Source/Programs/LowLevelTests/<target_name>/`
  - Engine-only tests (those with a directory under `Engine/Source/Programs/LowLevelTests/`) do NOT need `-Project`.
- Add `-Clean` flag if a clean build is requested.
- Append any additional user-specified arguments.

#### BuildGraph Command

Construct the command as follows:

```
<engine_root>/Engine/Build/BatchFiles/RunUAT.sh BuildGraph -Script=<buildgraph_xml> -Target=<node_name> -set:BuildPlatforms=<platform>
```

- Use `RunUAT.bat` on Windows, `RunUAT.sh` on Mac/Linux.
- **BuildGraph script location**: Search in order:
  1. `<project_root>/Build/LowLevelTests.xml`
  2. `<engine_root>/Engine/Build/LowLevelTests.xml`
  3. If neither exists, report error.
- **Node name**: Default to `"Build <target_name> <platform>"` if not explicitly specified.
- Append any additional user-specified arguments.

### Step 5: Execute the Build

Run the generated command using the Bash tool. Capture the full stdout/stderr output as the build log.

### Step 6: Parse the Build Log

After execution, parse the build log output to extract structured results (see Build Log Parsing section below).

## UBT Command Construction Reference

### Script Paths

| Platform | UBT Script | UAT Script |
|----------|-----------|------------|
| Windows | `Engine/Build/BatchFiles/RunUBT.bat` | `Engine/Build/BatchFiles/RunUAT.bat` |
| Mac/Linux | `Engine/Build/BatchFiles/RunUBT.sh` | `Engine/Build/BatchFiles/RunUAT.sh` |

### Build Configurations

Valid configurations: `Debug`, `Development` (default), `Shipping`, `Test`.

### Project Parameter Logic

The `-Project=<path>` parameter is needed for game-project tests but NOT for Engine-only tests:

1. Look for a `.uproject` file in the project root (glob `*.uproject`, take the first match).
2. If no `.uproject` found, this is an Engine-only project -- no `-Project` parameter needed.
3. If found, check if the target has a directory at `<engine_root>/Engine/Source/Programs/LowLevelTests/<target_name>/`. If it does, this is an explicit Engine test -- no `-Project` needed.
4. Otherwise (especially if "FortniteGame" appears in the project root path), add `-Project=<uproject_path>`.

## Build Log Parsing

Parse the raw UBT/BuildGraph output to extract the following information:

### Executable Path

Search for a line matching: `Writing output file: <path>`
- Pattern: `Writing output file:\s+["']?([^\r\n"']+)["']?` (case-insensitive)
- Normalize path separators in the extracted path.

### Error and Warning Counts

Search from the END of the log (reversed line scan) for summary lines:
- Primary pattern: `Compilation Failed/Complete: N error(s), N warning(s)`
  - Regex: `(?:Compilation\s+)?(?:Failed|Complete)[d]?[:\.]?\s*(\d+)\s+error[s]?,\s*(\d+)\s+warning[s]?`
- Fallback pattern: `N error(s), N warning(s)`
  - Regex: `(\d+)\s+error[s]?,\s*(\d+)\s+warning[s]?`
- Default to 0 errors, 0 warnings if no summary line found.

### Build Success/Failure Determination

Apply this logic in order:

1. **Error count check**: If error count > 0, the build FAILED.
2. **Failure pattern check**: Scan all lines for these patterns (case-insensitive):
   - `Build failed`
   - `Compilation failed`
   - `ERROR: ` (with trailing space)
   - If any match found, the build FAILED.
3. **Success pattern check**: Scan all lines for these patterns (case-insensitive):
   - `Build succeeded`
   - `Compilation complete`
   - `Total build time: N.N seconds`
   - If any match found, the build SUCCEEDED.
4. **Default**: If inconclusive, treat as FAILED (safe default).

### Error Message Extraction

Collect specific error messages (up to 10, deduplicated) by scanning each line for:
- `ERROR: (.+)` -- general UBT errors
- `Fatal Error: (.+)` -- fatal errors
- `error [A-Z]\d+: (.+)` -- compiler errors (e.g., `error C2065: ...`)
- `error LNK\d+: (.+)` -- linker errors

All patterns are case-insensitive. Extract the captured group as the error message; if no capture group, use the full line. Stop after collecting 10 unique messages.

### Missing SDK Detection

Check the full log text for platform SDK errors:
- **PS5**: `PS5 SDK not (found|installed|detected)`
- **PS4**: `PS4 SDK not (found|installed|detected)`
- **Xbox**: `Xbox(One|SeriesX)? SDK not (found|installed|detected)`
- **Switch**: `Switch SDK not (found|installed|detected)`
- **Android**: `Android (SDK|NDK) not (found|installed|detected)`
- **iOS**: `iOS SDK not (found|installed|detected)`

If a missing SDK is detected, include the platform name and SDK install hint (from `llt-common`) in the error response.

### Build Time Extraction

Search for: `Total build time: N.N seconds` or `Cumulative action seconds: N.N seconds`
- Regex: `(?:Total\s+build\s+time|Cumulative\s+action\s+seconds):\s+([\d.]+)\s+seconds`
- Return the value as a float. Default to 0.0 if not found.

## Response Format

All responses use the standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)).

### Success Response (Command Generation)

The `data` field contains:

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Always `"execute_command"` |
| `command` | string | Full build command to execute |
| `build_method` | string | `"direct_ubt"` or `"buildgraph"` |
| `target` | string | Target name |
| `platform` | string | Platform name |
| `configuration` | string | Build configuration (direct UBT only) |
| `instructions` | string | Agent execution guidance |

### Success Response (Build Log Parse)

The `data` field contains:

| Field | Type | Description |
|-------|------|-------------|
| `target` | string | Target name |
| `platform` | string | Platform name |
| `build_success` | bool | Whether build succeeded |
| `executable_path` | string/null | Path to built executable |
| `build_time_seconds` | float | Build duration (0.0 if unknown) |
| `warnings` | int | Warning count |
| `errors` | int | Error count |

If warnings > 0, a warning entry is added to the envelope warnings array.

### Error Response

The envelope `errors` array contains:

```json
{
  "severity": "error",
  "message": "Build failed with 5 error(s)",
  "code": "BUILD_FAILED",
  "context": {
    "target": "OnlineServicesMcpTests",
    "platform": "Win64",
    "error_count": 5,
    "warning_count": 3,
    "error_messages": ["error C2065: 'undeclared_identifier': undeclared identifier"],
    "missing_sdk": "PS5",
    "sdk_install_hint": "Install PS5 SDK from..."
  }
}
```

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `COMMAND_GENERATION_FAILED` | Failed to generate build command | Check target name, platform SDK, project structure |
| `BUILD_FAILED` | Compilation failed with errors | Review error messages, fix source code issues |
| `INVALID_PROJECT_ROOT` | Project root directory invalid | Verify path points to UE project with Engine/ directory |
| `LOG_FILE_NOT_FOUND` | Build log file not found | Ensure build was executed and log file path is correct |

## Platform Notes

| Platform | Script | SDK Check | Executable Output |
|----------|--------|-----------|-------------------|
| Win64 | `RunUBT.bat` | Visual Studio | `Engine/Binaries/Win64/<Target>.exe` |
| Mac | `RunUBT.sh` | Xcode | `Engine/Binaries/Mac/<Target>` |
| Linux | `RunUBT.sh` | GCC/Clang | `Engine/Binaries/Linux/<Target>` |
| Consoles | BuildGraph | Platform SDK required | Platform-specific paths |
