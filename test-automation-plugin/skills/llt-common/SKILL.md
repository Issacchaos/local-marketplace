# LLT Common: Shared Types, Validation, and Patterns

This document defines the shared response format, data structures, validation rules, and logging instructions used by all LLT skills. Each LLT skill SKILL.md references this file for these shared conventions.

---

## Response Format

All LLT skill output MUST use this JSON envelope. Output the JSON to stdout with no surrounding text.

### Schema

```json
{
  "skill": "<skill-name>",
  "version": "<semver>",
  "status": "success" | "partial_success" | "error",
  "timestamp": "<ISO-8601 UTC, e.g. 2026-02-19T15:30:00Z>",
  "data": { /* skill-specific payload */ },
  "errors": [
    {
      "severity": "error",
      "message": "<human-readable message>",
      "code": "<optional error code>",
      "context": { /* optional additional details */ }
    }
  ],
  "warnings": [
    {
      "severity": "warning",
      "message": "<human-readable message>",
      "code": "<optional warning code>",
      "context": { /* optional additional details */ }
    }
  ]
}
```

### Status Rules

- **success**: All operations completed. `errors` is empty.
- **partial_success**: Some operations completed, some failed. Both `data` and `errors` are populated.
- **error**: No operations completed. `data` is empty, `errors` has at least one entry.

### Required Fields

Every response MUST include: `skill`, `version`, `status`, `timestamp`, `data`, `errors`, `warnings`. Use empty objects/arrays (`{}`, `[]`) for absent data, never omit the keys.

### Example: Success

```json
{
  "skill": "llt-find",
  "version": "1.0.0",
  "status": "success",
  "timestamp": "2026-02-19T15:30:00Z",
  "data": {
    "test_targets": [],
    "total_tests": 42
  },
  "errors": [],
  "warnings": []
}
```

### Example: Error

```json
{
  "skill": "llt-build",
  "version": "1.0.0",
  "status": "error",
  "timestamp": "2026-02-19T15:30:05Z",
  "data": {},
  "errors": [
    {
      "severity": "error",
      "message": "Project root does not contain Engine/ or .uproject file",
      "code": "INVALID_PROJECT_ROOT",
      "context": {"path": "/tmp/not-a-project"}
    }
  ],
  "warnings": []
}
```

---

## Logging Instructions

Log all progress and diagnostic messages to **stderr** (stdout is reserved for JSON output). Use this format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [skill-name] message
```

### Log Levels

- **DEBUG**: Internal state, variable values, decision rationale. Only when verbose mode requested.
- **INFO**: Phase transitions, progress updates, completion status. Always emitted.
- **WARNING**: Non-fatal issues, degraded results, fallback paths taken.
- **ERROR**: Validation failures, missing files, unrecoverable issues.

### Required Log Points

1. **Skill start**: `[INFO] [llt-find] Starting llt-find`
2. **Phase transitions**: `[INFO] [llt-find] Phase: Scanning BuildGraph XML`
3. **Progress updates** (for operations with >10 items): `[INFO] [llt-find] Progress: 45/120 modules (37.5%)`
4. **Validation errors**: `[ERROR] [llt-find] Validation error: Project root not found at /path`
5. **Skill completion**: `[INFO] [llt-find] Completed llt-find with status 'success' in 2.45 seconds`

### When writing to stderr

Use `sys.stderr.write()` or `print(..., file=sys.stderr)` in Python scripts, or simply output diagnostic text to stderr when operating as an agent.

---

## Data Structures

These JSON structures are used in the `data` payload of LLT skill responses. Generate them directly as JSON objects.

### Evidence

Supports a test-to-source mapping relationship.

```json
{
  "type": "direct_include | naming_convention | module_dependency",
  "value": "string (e.g., '#include \"Resonance.h\"')",
  "points": "integer (direct_include=50, naming_convention=30, module_dependency=20)"
}
```

### SourceMapping

Maps a test file to the source file it tests.

```json
{
  "test_file": "string (relative path from project root)",
  "source_file": "string (relative path from project root)",
  "confidence": "very high | high | medium | low",
  "evidence": [ /* array of Evidence objects */ ]
}
```

**Confidence scoring**: Sum the `points` from all evidence items.
- **very high**: 80+ points
- **high**: 60-79 points
- **medium**: 40-59 points
- **low**: <40 points

### TestCase

A single Catch2 test case within a test file.

```json
{
  "name": "string (TEST_CASE name)",
  "tags": ["string (e.g., '[EOS]', '[suite_resonance]')"],
  "line_number": "integer",
  "sections": ["string (SECTION block names)"],
  "includes": ["string (#include directives)"]
}
```

### TestFile

A test source file containing multiple test cases.

```json
{
  "file_path": "string (relative path from project root)",
  "module_name": "string (e.g., 'OnlineServicesMcp')",
  "test_count": "integer",
  "test_cases": [ /* array of TestCase objects */ ]
}
```

### TestTarget

A test target (executable with one or more test modules).

```json
{
  "name": "string (e.g., 'OnlineServicesMcpTests')",
  "type": "explicit | implicit",
  "platforms": ["Win64", "PS5", "Linux"],
  "binary_path": "string (path to test executable)",
  "buildgraph_registered": "boolean"
}
```

**Type rules**:
- **explicit**: Registered in BuildGraph XML as a dedicated test target
- **implicit**: Discovered by convention (Tests/ directory, module naming)

### TestResult

Result from executing a single test case.

```json
{
  "test_name": "string",
  "status": "passed | failed | skipped",
  "duration": "float (seconds)",
  "failure_details": {
    "assertion_type": "REQUIRE | CHECK | REQUIRE_FALSE | ...",
    "expression": "string (expression that failed)",
    "message": "string",
    "file": "string (source file path)",
    "line": "integer"
  }
}
```

Note: `failure_details` is only present when `status` is `"failed"`.

### ModuleCoverage

Module-level test coverage from dependency analysis.

```json
{
  "module_name": "string (e.g., 'Core', 'OnlineServicesMcp')",
  "covered": "boolean",
  "test_modules": ["string (test module names that cover this module)"]
}
```

---

## Validation Rules

Before executing any LLT skill operation, validate inputs against these rules. If validation fails, emit an error response (see Response Format) and stop.

### Project Root Validation

A valid Unreal Engine project root must satisfy **at least one** of:
1. Contains a `.uproject` file (game project)
2. Contains an `Engine/` directory (UE installation root)
3. Contains at least one of: `Source/`, `Content/`, `Config/` (game project structure)

**Validation steps**:
1. Check the path exists and is a directory
2. Check for `.uproject` files: `ls *.uproject` or `Glob("*.uproject")`
3. Check for `Engine/` directory
4. Check for `Source/`, `Content/`, or `Config/` directories
5. If none match, report error: `"Project root does not contain .uproject, Engine/, Source/, Content/, or Config/ directory"`

### Platform Validation

Supported platforms (case-sensitive):
```
Win64, Mac, Linux, PS5, PS4, Xbox, XboxOne, XboxOneGDK, XSX, Switch, Android, iOS
```

If the user provides an unrecognized platform, report error and list supported platforms.

### SDK Availability

Native platforms are always available: **Win64**, **Mac**, **Linux**.

Console/mobile platforms require SDK environment variables:
| Platform | Environment Variable | Install Hint |
|----------|---------------------|--------------|
| PS5 | `SCE_ORBIS_SDK_DIR` | Launcher -> Engine -> Platform Support -> PS5 |
| PS4 | `SCE_ORBIS_SDK_DIR` | Launcher -> Engine -> Platform Support -> PS4 |
| Xbox, XboxOne, XboxOneGDK, XSX | `GameDK` or `XboxOneXDKLatest` | Microsoft Game Development Kit |
| Switch | `NINTENDO_SDK_ROOT` | Nintendo Developer Portal |
| Android | `ANDROID_HOME` or `ANDROID_SDK_ROOT` | Android Studio or sdkmanager |
| iOS | Xcode at `/Applications/Xcode.app` (macOS only) | Mac App Store |

When SDK is not found, include the install hint in the warning message.

### Path Safety

- All file paths must be **under the project root** (prevent path traversal)
- Resolve symlinks before comparison: verify `resolved_path.startswith(resolved_root)`
- Reject paths containing `..` that escape the project root

### Test Target Name Validation

Valid target names must:
- Not be empty
- Not start with a hyphen (`-`)
- Contain only: `a-z`, `A-Z`, `0-9`, `_`, `-`

### Catch2 Tag Filter Validation

Valid tag filter syntax: one or more `[tag]` or `~[tag]` groups.
- `[EOS]` - include tests tagged EOS
- `~[slow]` - exclude tests tagged slow
- `[EOS][network]` - include tests with both tags

Regex for validation: `^(~?\[[^\]]+\])+$`
