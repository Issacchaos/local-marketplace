---
name: llt-find
description: Discover LowLevelTest targets in Unreal Engine projects. Parses BuildGraph XML and filesystem to enumerate test targets with metadata.
user-invocable: true
version: 1.0.0
applies_to:
  language: C++
  frameworks: [Catch2, LowLevelTests]
  project_indicators: ["*.Build.cs", "TestHarness.h", "BuildGraph.xml"]
capabilities:
  - test_discovery
  - target_enumeration
  - test_case_extraction
---

# llt-find: LowLevelTest Discovery

**Version**: 1.0.0
**Category**: LowLevelTests Discovery
**Purpose**: Discover all LLT targets using a BuildGraph-first strategy, supplemented by filesystem globbing

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.

---

## Overview

Discovers all LowLevelTest (LLT) targets in Unreal Engine projects using a BuildGraph-first strategy. Parses BuildGraph XML files to extract explicit test targets, then supplements with filesystem globbing to discover implicit test modules. For each target, extracts TEST_CASE names, tags, line numbers, and #include directives.

---

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `project_root` | Yes | Path to UE project root directory |
| `test_type` | No | `all` (default), `explicit`, or `implicit` |
| `platform` | No | Filter by platform (e.g., `Win64`, `PS5`, `Linux`) |

Supported platforms: Win64, Mac, Linux, PS5, PS4, XboxOne, Switch, Android, IOS

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "test_targets": [
    {
      "name": "OnlineServicesMcpTests",
      "type": "explicit",
      "platforms": ["Win64", "PS5"],
      "binary_path": "FortniteGame/Binaries/Win64/OnlineServicesMcpTests.exe",
      "buildgraph_registered": true
    }
  ],
  "test_files": {
    "CoreTests": [
      {
        "file_path": "Engine/Source/Runtime/Core/Tests/Containers/LruCacheTest.cpp",
        "module_name": "Core",
        "test_count": 5,
        "test_cases": [
          {
            "name": "LRU cache basic operations",
            "tags": ["Core", "Containers"],
            "line_number": 42,
            "sections": ["Insert", "Lookup", "Eviction"],
            "includes": ["Containers/LruCache.h"]
          }
        ]
      }
    ]
  },
  "statistics": {
    "total_targets": 207,
    "explicit_targets": 12,
    "implicit_targets": 195,
    "total_test_files": 330,
    "total_test_cases": 3421
  },
  "elapsed_seconds": 1.87
}
```

---

## Discovery Algorithm

### Phase 1: Explicit Test Discovery (BuildGraph XML Parsing)

Parse BuildGraph XML files to extract registered test targets:

1. **Locate BuildGraph XML files**:
   - `Engine/Build/LowLevelTests.xml`
   - `FortniteGame/Build/LowLevelTests.xml`
   - If neither exists, emit a warning and proceed to Phase 2.

2. **Parse XML** using standard XML parsing (e.g., `xml.etree.ElementTree`):
   - Handle optional XML namespaces (check if root tag starts with `{`).

3. **Extract test names** from `<Option Name="TestNames">` elements:
   - Read the `DefaultValue` attribute.
   - Split by semicolons to get individual test names.
   - If no `TestNames` option found, fall back to extracting from `<Agent>` node `Name` attributes (take first word of agent name).

4. **Extract metadata** from `<Agent>` and `<Property>` nodes:
   - For each `<Agent>`, look for `<Property Name="TestName">`, `<Property Name="Platform">`, `<Property Name="Platforms">`, and `<Property Name="BinaryPath">` child elements.
   - Build a map of `test_name -> {platforms: set, binary_paths: set}`.
   - Also check `Agent` `Type` attribute for platform info.

5. **Build TestTarget objects**:
   - All BuildGraph-discovered targets are `type: "explicit"` with `buildgraph_registered: true`.
   - Default to `Win64` platform if no platform metadata found.

6. **Deduplicate** when parsing multiple XML files (keep first occurrence).

### Phase 2: Implicit Test Discovery (Filesystem Globbing)

Search for test files not registered in BuildGraph:

1. **Glob for test files** using these patterns:
   - `Engine/Source/Runtime/*/Tests/**/*.cpp`
   - `Engine/Source/Developer/*/Tests/**/*.cpp`
   - `FortniteGame/Plugins/*/Tests/**/*.cpp`
   - `FortniteGame/Plugins/*/*/Tests/**/*.cpp`
   - `FortniteGame/Source/*/Tests/**/*.cpp`

2. **Group by module**: Extract the module name from the path (the directory immediately before `Tests/`).

3. **Create TestTarget** for each module:
   - Name: `{ModuleName}Tests`
   - Type: `implicit`
   - Platforms: `["Win64"]` (default; actual support requires `.Build.cs` parsing)
   - `buildgraph_registered: false`

### Phase 3: Merge and Deduplicate

- Explicit targets take precedence for duplicates (same name).
- Filter by platform if `platform` parameter is specified.

### Phase 4: Test File Parsing (per target)

For each implicit target, parse the C++ test files to extract metadata:

1. **Extract `#include` directives** using regex `#include\s+[<"]([^>"]+)[>"]`:
   - Filter out test framework includes: `TestHarness.h`, `OnlineCatchHelper.h`, `catch.hpp`, and anything starting with `catch2/` or `Catch2/`.

2. **Extract `TEST_CASE` declarations** using regex:
   - Pattern: `TEST_CASE\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]*)")?\s*\)` with MULTILINE | DOTALL flags
   - First capture group: test name
   - Second capture group (optional): tags string

3. **Parse tags** from the tags string:
   - Format: `[tag1][tag2]`
   - Extract using regex: `\[([^\]]+)\]`

4. **Calculate line numbers**: Count newlines before each match position, add 1.

5. **Extract `SECTION` blocks** within each test case body:
   - Pattern: `SECTION\s*\(\s*"([^"]+)"\s*\)`
   - The test body extends from the end of the `TEST_CASE` match to the start of the next `TEST_CASE` or end of file.

---

## Error Handling

| Error | Behavior |
|-------|----------|
| Invalid project root | Returns `INVALID_PATH` error |
| BuildGraph XML not found | Warning; falls back to filesystem-only discovery |
| Test file parse failure | Warning; skips file, continues discovery |

---

## Limitations

1. Only parses test files for implicit targets; explicit requires `.Target.cs`/`.Build.cs` parsing
2. Binary paths not inferred for implicit tests
3. Implicit tests default to Win64 platform; actual support requires `.Build.cs` parsing
4. Assumes test target name is `{ModuleName}Tests`
