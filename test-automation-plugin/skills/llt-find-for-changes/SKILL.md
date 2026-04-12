---
name: llt-find-for-changes
description: Identify relevant tests for modified source files in Unreal Engine LowLevelTests framework
version: 1.0.0
category: LowLevelTests Discovery
user-invocable: true
applies_to:
  language: C++
  frameworks: [Catch2, LowLevelTests]
  project_indicators: ["*.Build.cs", "TestHarness.h"]
capabilities:
  - change_based_discovery
  - module_mapping
  - dependency_analysis
---

# llt-find-for-changes: Change-Based Test Discovery

**Version**: 1.0.0
**Category**: LowLevelTests Discovery

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.
**Purpose**: Analyze modified source files and identify relevant test coverage

---

## Overview

The `llt-find-for-changes` skill analyzes modified source files and identifies relevant test coverage through:

1. **Module Discovery**: Walks directory tree upward from each modified file to find parent module (nearest `.Build.cs`)
2. **Direct Test Discovery**: Checks for test files in the same module's `Tests/` subdirectory
3. **Dependency Analysis**: Uses module dependency graph to find test modules that depend on modified modules
4. **Transitive Inclusion**: Optionally includes tests that transitively depend on modified modules

---

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `project_root` | Yes | Path to Unreal Engine project root directory |
| `files` | Yes | List of modified file paths (relative to project root or absolute) |
| `include_transitive` | No | Include transitive test modules (default: true) |

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "summary": {
    "modified_files": 1,
    "modules_affected": 1,
    "direct_test_files": 2,
    "transitive_test_modules": 3,
    "unmapped_files": 0
  },
  "file_to_module": {
    "Engine/Source/Runtime/Core/Private/Misc/LruCache.cpp": "Core"
  },
  "direct_tests": {
    "Engine/Source/Runtime/Core/Private/Misc/LruCache.cpp": [
      "Engine/Source/Runtime/Core/Tests/Misc/LruCacheTest.cpp"
    ]
  },
  "transitive_test_modules": {
    "Core": ["CoreTests", "OnlineServicesMcpTests"]
  },
  "unmapped_files": [],
  "recommendations": [
    "Run 2 direct test file(s) in modified modules",
    "Build and run 3 test module(s) that depend on modified modules"
  ]
}
```

---

## Algorithm

### Step 1: Module Discovery (for each modified file)

1. **Skip test infrastructure files** -- check if the file path contains `/Catch2/`, `/OnlineTestsCore/`, or `/LowLevelTestsRunner/`. If so, skip with a warning.
2. **Walk directory tree upward** from the file's parent directory toward the project root.
3. At each directory, **glob for `*.Build.cs`** files.
4. When found, **extract the module name** from the `.Build.cs` filename (e.g., `Core.Build.cs` -> `Core`).
5. The directory containing the `.Build.cs` is the **module root**.
6. Check for a `Tests/` subdirectory in the module root.
7. If no `.Build.cs` is found before reaching the project root, the file is **unmapped** (add to `unmapped_files` with a `MODULE_NOT_FOUND` warning).

### Step 2: Direct Test Discovery (for each module)

1. If the module has a `Tests/` subdirectory, **recursively find all `*.cpp` files** in it.
2. These are the **direct test files** for that module.

### Step 3: Dependency Graph Analysis

1. **Glob all `.Build.cs` files** in the project using these patterns:
   - `Engine/Source/**/*.Build.cs`
   - `Engine/Plugins/**/*.Build.cs`
   - `FortniteGame/Source/**/*.Build.cs`
   - `FortniteGame/Plugins/**/*.Build.cs`
2. **Parse each `.Build.cs`** to extract `PublicDependencyModuleNames` and `PrivateDependencyModuleNames` using regex patterns like:
   - `PublicDependencyModuleNames\.Add\("(\w+)"\)`
   - `PublicDependencyModuleNames\.AddRange\(new string\[\] \{([^}]+)\}\)`
   - Same patterns for `PrivateDependencyModuleNames`
3. **Build a directed dependency graph** where edges point from module A to module B if A depends on B.
4. **Identify test modules** -- modules whose names end with `Tests` or contain test-related patterns.

### Step 4: Test Module Discovery (for each modified module)

1. For each test module in the graph, check if it **directly depends** on the modified module.
2. If `include_transitive` is true, also compute **transitive dependencies** (BFS/DFS from the test module) and check if the modified module is reachable.
3. **Exclude test infrastructure modules**: `Catch2`, `OnlineTestsCore`, `LowLevelTestsRunner`.
4. Return the sorted list of test module names.

### Step 5: Build Recommendations

- If direct test files were found: "Run N direct test file(s) in modified modules"
- If transitive test modules were found: "Build and run N test module(s) that depend on modified modules"
- If neither found: "No tests found for modified files"

---

## Error Handling

| Code | Severity | Description |
|------|----------|-------------|
| `INVALID_PROJECT_ROOT` | error | Project root path does not exist |
| `MODULE_NOT_FOUND` | warning | Could not find parent module for file |
| `TEST_INFRASTRUCTURE_FILE` | warning | File is part of test infrastructure (skipped) |
| `TEST_DISCOVERY_FAILED` | error | Internal error during test discovery |

---

## Limitations

- **Module-level granularity**: Identifies test modules, not individual test cases
- **Static analysis only**: Does not consider runtime behavior or reflection-based tests
- **Requires .Build.cs**: Files without parent `.Build.cs` cannot be mapped to modules
- **UE module system**: Only works within Unreal Engine module structure
