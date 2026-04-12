# Design: Agentic Flow Replacements for Python Utilities

**Task**: TASK-2 - Replace 5 Python scripts (1,411 total lines) with documentation-driven agentic patterns in SKILL.md files.

**Principle**: Agents (LLMs) can follow documented schemas, validation rules, and parsing instructions directly. Python scripts that exist solely to enforce structure or transform data are unnecessary when the agent is instructed in its SKILL.md.

---

## 1. llt_json_schema.py (346 lines) -> SKILL.md "Response Format" Section

### BEFORE

Python module with `create_response()`, `create_success_response()`, `create_error_response()`, `validate_response()`, plus accessor functions (`get_status()`, `get_data()`, `get_errors()`). Enforces a JSON envelope: `{skill, version, status, timestamp, data, errors, warnings}`.

### AFTER

Add a "Response Format" section to each LLT skill's SKILL.md (or a shared `skills/llt-common/SKILL.md` referenced by others).

### Concrete SKILL.md Section

```markdown
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
    "test_targets": [...],
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
```

### Agent Behavior Example

When the agent completes an LLT analysis, it reads the "Response Format" section and directly outputs:

```
Agent thinks: "I found 3 test targets. Status is success. I need to wrap this in the envelope."
Agent outputs to stdout:
{"skill":"llt-find","version":"1.0.0","status":"success","timestamp":"2026-02-19T15:30:00Z","data":{"test_targets":[...]},"errors":[],"warnings":[]}
```

### Edge Cases and Limitations

| Aspect | Python Version | Agentic Version | Impact |
|--------|---------------|-----------------|--------|
| Status validation | `ValueError` on invalid status | Agent follows documented enum | Low risk: agent reads 3 valid values |
| Timestamp format | `datetime.utcnow().isoformat() + "Z"` | Agent generates ISO-8601 string | Negligible: agents reliably produce ISO timestamps |
| Type validation | `isinstance` checks on errors/warnings | Agent follows schema definition | Low risk: schema is clear |
| Missing fields | Runtime `KeyError` | Agent follows "Required Fields" checklist | Low risk: checklist is explicit |

**Net assessment**: The Python module was a convenience wrapper around dict construction. An LLM can construct this JSON directly from a schema definition with no loss of fidelity.

---

## 2. llt_logging.py (243 lines) -> SKILL.md "Logging Instructions" Section

### BEFORE

Python logging module setup: `setup_logger()`, `create_skill_logger()`, `log_skill_start()`, `log_skill_complete()`, `log_phase()`, `log_progress()`, `log_validation_error()`. Configures handlers for stderr, file output, and log levels.

### AFTER

Add a "Logging Instructions" section to SKILL.md.

### Concrete SKILL.md Section

```markdown
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
```

### Agent Behavior Example

```
Agent writes to stderr: [2026-02-19 15:30:00] [INFO] [llt-coverage] Starting llt-coverage
Agent writes to stderr: [2026-02-19 15:30:01] [INFO] [llt-coverage] Phase: Parsing .Build.cs files
Agent writes to stderr: [2026-02-19 15:30:02] [INFO] [llt-coverage] Progress: 500/1603 modules (31.2%)
Agent writes to stderr: [2026-02-19 15:30:05] [INFO] [llt-coverage] Completed llt-coverage with status 'success' in 5.12 seconds
Agent writes to stdout: {"skill":"llt-coverage","version":"1.0.0","status":"success",...}
```

### Edge Cases and Limitations

| Aspect | Python Version | Agentic Version | Impact |
|--------|---------------|-----------------|--------|
| Log level filtering | Runtime level checks, handler-level filtering | Agent follows level descriptions | Acceptable: agent emits appropriate levels |
| File logging | `FileHandler` support | Not supported (agent uses stderr only) | Minor: file logging was rarely used |
| Null logger | `create_null_logger()` for test suppression | Not needed (agent doesn't log in test mode) | None |
| Thread safety | Python logging module handles this | Not applicable (agent is single-threaded) | None |

**Net assessment**: The logging module was Python infrastructure. Agents output diagnostic text naturally. Documenting the format ensures consistency without code.

---

## 3. llt_types.py (290 lines) -> SKILL.md "Data Structures" Section

### BEFORE

8 Python dataclasses: `Evidence`, `SourceMapping`, `TestCase`, `TestFile`, `TestTarget`, `FailureDetail`, `TestResult`, `ModuleCoverage`. Each with `to_dict()`/`from_dict()` methods and validation in `__post_init__`. Plus `calculate_confidence_score()`.

### AFTER

Add a "Data Structures" section to SKILL.md with JSON schema definitions.

### Concrete SKILL.md Section

```markdown
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
  "platforms": ["Win64", "PS5", "Linux", ...],
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
```

### Agent Behavior Example

When the agent discovers a test mapping, instead of instantiating `SourceMapping(test_file=..., source_file=..., confidence=..., evidence=[...])`, it directly constructs:

```json
{
  "test_file": "Tests/OnlineServicesMcpTests/TestAccountId.cpp",
  "source_file": "Source/OnlineServicesMcp/Private/AccountIdConverter.cpp",
  "confidence": "high",
  "evidence": [
    {"type": "direct_include", "value": "#include \"AccountIdConverter.h\"", "points": 50},
    {"type": "naming_convention", "value": "TestAccountId -> AccountIdConverter", "points": 30}
  ]
}
```

Confidence is calculated inline: 50 + 30 = 80 -> "very high" (agent corrects to "very high" based on scoring rules).

### Edge Cases and Limitations

| Aspect | Python Version | Agentic Version | Impact |
|--------|---------------|-----------------|--------|
| `__post_init__` validation | Raises `ValueError` on invalid `confidence` or `type` | Agent follows enum values from docs | Low risk: documented enums are clear |
| `to_dict()`/`from_dict()` | Serialization/deserialization boilerplate | Not needed (agent produces JSON directly) | None |
| Confidence scoring | `calculate_confidence_score()` function | Agent sums points and applies thresholds inline | Low risk: 4 thresholds, simple arithmetic |
| Type safety | Python type hints + mypy | Agent follows documented field types | Acceptable: schema definitions are explicit |

**Net assessment**: Dataclasses were type-safe containers for JSON data. Since the agent produces JSON directly, documenting the shape is sufficient. The confidence scoring algorithm (4 thresholds) is trivially followed by an LLM.

---

## 4. llt_validation.py (305 lines) -> SKILL.md "Validation Rules" Section

### BEFORE

Python functions: `validate_project_root()`, `validate_platform()`, `check_sdk_installed()`, `get_sdk_install_hint()`, `validate_file_path()`, `validate_directory_path()`, `is_path_under_root()`, `sanitize_path()`, `validate_test_target_name()`, `validate_tag_filter()`. Plus `SUPPORTED_PLATFORMS` constant.

### AFTER

Add a "Validation Rules" section to SKILL.md.

### Concrete SKILL.md Section

```markdown
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
```

### Agent Behavior Example

```
User provides: --project-root /tmp/some-path --platform PS7

Agent validates:
1. Check /tmp/some-path exists -> YES
2. Check for .uproject -> NO
3. Check for Engine/ -> NO
4. Check for Source/, Content/, Config/ -> NO
5. FAIL: emit error response with code INVALID_PROJECT_ROOT

Even if project root were valid:
6. Check platform "PS7" against supported list -> NOT FOUND
7. FAIL: emit error response "Unsupported platform: PS7. Supported: Win64, Mac, Linux, ..."
```

### Edge Cases and Limitations

| Aspect | Python Version | Agentic Version | Impact |
|--------|---------------|-----------------|--------|
| SDK env var checking | `os.environ.get()` calls | Agent uses `echo $VAR` or Bash tool | Equivalent |
| Path traversal prevention | `path.resolve()` + `startswith()` | Agent resolves and compares | Equivalent |
| Regex tag validation | `re.fullmatch()` | Agent applies documented regex | Equivalent |
| Platform list | Python constant list | Documented table | Equivalent; table is easier to update |

**Net assessment**: Validation rules are policy, not computation. Documenting the rules lets the agent apply them using its native tools (Bash, Glob, Read) without a Python intermediary.

---

## 5. build_cs_parser.py (227 lines) -> SKILL.md "Build.cs Parsing" Section

### BEFORE

Python module with regex-based parsing: `parse_build_cs_file()`, `_is_test_module()`, `_extract_dependencies()`, `_parse_array_content()`, `is_test_infrastructure_module()`, `get_all_dependencies()`. Handles `AddRange(new string[] {...})` and `new List<string> {...}` patterns.

### AFTER

Add a "Build.cs Parsing" section to the coverage skill's SKILL.md or to a shared LLT skill reference.

### Concrete SKILL.md Section

```markdown
## Build.cs Parsing Instructions

When analyzing module dependencies for coverage, read `.Build.cs` files directly and extract dependency information.

### Finding Build.cs Files

Use Glob to find all `.Build.cs` files under the project root:
```
Glob("**/*.Build.cs")
```

### Extracting Module Name

The module name is derived from the filename:
- `Core.Build.cs` -> module name: `Core`
- `OnlineServicesMcp.Build.cs` -> module name: `OnlineServicesMcp`

Strip the `.Build.cs` suffix from the filename.

### Extracting Dependencies

Look for two dependency arrays in each file:

**1. PublicDependencyModuleNames** - modules visible to dependents
**2. PrivateDependencyModuleNames** - modules used only internally

Each appears in one of these C# patterns:

**AddRange format** (most common):
```csharp
PublicDependencyModuleNames.AddRange(new string[] {
    "Core",
    "CoreUObject",
    "Engine"
});
```

**Assignment format** (less common):
```csharp
PublicDependencyModuleNames = new List<string> {
    "Core",
    "CoreUObject"
};
```

**Extraction method**: Read the file content, find the `{...}` block after each dependency type, and extract all quoted strings within it. Ignore:
- C# line comments: `// comment`
- C# block comments: `/* comment */`
- Whitespace and trailing commas

### Detecting Test Modules

A module is a **test module** if either:
1. The class inherits from `TestModuleRules` (look for `: TestModuleRules` in the file)
2. The `.Build.cs` file is located under a `Tests/` directory

### Test Infrastructure Modules (Exclude from Coverage)

These modules are test infrastructure, not production code. Exclude them from coverage analysis:
- `Catch2`
- `OnlineTestsCore`
- `LowLevelTestsRunner`

### Output Structure

For each parsed `.Build.cs` file, produce:
```json
{
  "module_name": "OnlineServicesMcp",
  "public_dependencies": ["Core", "CoreUObject", "Engine"],
  "private_dependencies": ["HTTP", "Json"],
  "is_test_module": false,
  "build_cs_path": "Source/OnlineServicesMcp/OnlineServicesMcp.Build.cs"
}
```
```

### Agent Behavior Example

```
Agent: I need to analyze module coverage. Let me find all .Build.cs files.

Glob("**/*.Build.cs") -> finds 1603 files

Agent reads first file: OnlineServicesMcp.Build.cs
- Module name: "OnlineServicesMcp" (from filename)
- Finds: PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
- Extracts quoted strings: ["Core", "CoreUObject", "Engine"]
- Finds: PrivateDependencyModuleNames.AddRange(new string[] { "HTTP", "Json" });
- Extracts: ["HTTP", "Json"]
- Checks for ": TestModuleRules" -> not found
- Checks path for "Tests/" -> not found
- is_test_module: false

Agent constructs the JSON object directly and continues to next file.
```

### Edge Cases and Limitations

| Aspect | Python Version | Agentic Version | Impact |
|--------|---------------|-----------------|--------|
| Regex robustness | Pre-compiled regex, handles edge cases | Agent reads file and extracts quoted strings | Comparable: both use pattern matching |
| Multi-line arrays | Regex with `re.DOTALL` flag | Agent reads full file, finds `{...}` blocks naturally | Agent may be more robust (understands context) |
| Comment stripping | Regex-based comment removal | Agent understands C# comments natively | Agent is arguably better here |
| Malformed files | Returns `None` on `IOError`/`UnicodeDecodeError` | Agent reports warning and skips | Equivalent |
| Performance at scale | ~1600 files parsed in seconds via Python | Agent reads files individually (slower) | Trade-off: agent is slower but correct. For 1600 files, batch with Glob + selective Read |

**Performance note**: For large projects (1600+ .Build.cs files), the agent should:
1. First `Glob("**/*.Build.cs")` to get all paths
2. For test module detection: `Grep(": TestModuleRules")` across all files
3. For dependencies: Read files in priority order (test modules first, then modules under analysis)
4. Skip reading .Build.cs files that are clearly infrastructure (Catch2.Build.cs, etc.)

This avoids reading all 1600 files while still getting accurate dependency data.

**Net assessment**: The Build.cs parser was regex-based text extraction, which is exactly what LLMs excel at. The agent can read a .Build.cs file and extract dependencies more reliably than regex (understanding context, handling edge cases). The main trade-off is speed for very large codebases, mitigated by selective reading.

---

## Summary

| Script | Lines | Replacement | Key Trade-off |
|--------|-------|-------------|---------------|
| llt_json_schema.py | 346 | Response Format schema in SKILL.md | None significant |
| llt_logging.py | 243 | Logging Instructions in SKILL.md | No file logging (rarely used) |
| llt_types.py | 290 | Data Structures JSON schemas in SKILL.md | No compile-time type checking (acceptable for JSON output) |
| llt_validation.py | 305 | Validation Rules checklist in SKILL.md | Agent uses tools instead of Python functions (equivalent) |
| build_cs_parser.py | 227 | Build.cs Parsing Instructions in SKILL.md | Slower for 1600+ files (mitigated by selective reads) |
| **Total** | **1,411** | **~200 lines of SKILL.md documentation** | **Net positive: simpler, more maintainable, no Python runtime needed** |

### Placement Recommendation

Create a shared `skills/llt-common/SKILL.md` containing:
- Response Format (from llt_json_schema.py)
- Logging Instructions (from llt_logging.py)
- Data Structures (from llt_types.py)
- Validation Rules (from llt_validation.py)

Place Build.cs Parsing Instructions in `skills/build-integration/SKILL.md` (where coverage analysis is documented).

Each LLT skill SKILL.md references the shared file: `"For response format, data structures, validation, and logging: see skills/llt-common/SKILL.md"`
