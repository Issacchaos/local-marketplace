---
name: llt-find-sources
description: Find source files tested by a test file, or find tests for a source file using evidence-based confidence scoring
version: 1.0.0
category: LowLevelTests Discovery
user-invocable: true
applies_to:
  language: C++
  frameworks: [Catch2, LowLevelTests]
  project_indicators: ["*.Build.cs", "TestHarness.h"]
capabilities:
  - source_discovery
  - test_mapping
  - dependency_mapping
---

# llt-find-sources: Source-Test Mapping Skill

**Version**: 1.0.0
**Category**: LowLevelTests Discovery

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.
**Purpose**: Map test files to source files using evidence-based confidence scoring

---

## Overview

The `llt-find-sources` skill maps test files to source files (forward lookup) or source files to test files (reverse lookup) using multiple evidence types with confidence scoring.

---

## Input Parameters

### Forward Lookup (Test -> Sources)

| Parameter | Required | Description |
|-----------|----------|-------------|
| `test_file` | Yes | Path to test file (relative to project root or absolute) |
| `project_root` | Yes | Root directory of the project |
| `module_dependencies` | No | List of module names the test depends on |
| `min_confidence` | No | Minimum confidence level: `low` (default), `medium`, `high`, `very high` |

### Reverse Lookup (Source -> Tests)

| Parameter | Required | Description |
|-----------|----------|-------------|
| `source_file` | Yes | Path to source file (relative to project root or absolute) |
| `project_root` | Yes | Root directory of the project |
| `test_root` | No | Root directory for test files (defaults to project root) |
| `min_confidence` | No | Minimum confidence level: `low` (default), `medium`, `high`, `very high` |

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "mode": "forward",
  "test_file": "Engine/Source/Runtime/Core/Tests/LruCacheTest.cpp",
  "total_count": 2,
  "mappings": [
    {
      "test_file": "Engine/Source/Runtime/Core/Tests/LruCacheTest.cpp",
      "source_file": "Engine/Source/Runtime/Core/Public/LruCache.h",
      "confidence": "very high",
      "evidence": [
        {"type": "direct_include", "value": "#include \"LruCache.h\"", "points": 50},
        {"type": "naming_convention", "value": "LruCacheTest -> LruCache.h", "points": 30}
      ]
    }
  ],
  "confidence_breakdown": {
    "very high": 1, "high": 0, "medium": 1, "low": 0
  }
}
```

---

## Mapping Algorithm

### Evidence Types and Scoring

| Evidence Type | Points | Description |
|---------------|--------|-------------|
| `direct_include` | +50 | Test file `#include`s a source header |
| `naming_convention` | +30 | Test name matches source with test suffix removed |
| `module_dependency` | +20 | Test module depends on runtime module via `.Build.cs` |

### Confidence Levels (based on total points)

- **Very high** (80+): Direct include + naming convention + module dependency
- **High** (60-79): Direct include + naming convention OR multiple strong signals
- **Medium** (40-59): Direct include OR naming convention alone
- **Low** (<40): Weak evidence only (e.g., module dependency alone)

### Forward Lookup: Test File -> Source Files

To find source files tested by a given test file, the agent should:

1. **Parse `#include` directives** from the test file:
   - Use regex `#include\s+[<"]([^>"]+)[>"]` to extract included paths
   - **Filter out test framework includes**: `TestHarness.h`, `OnlineCatchHelper.h`, `catch.hpp`, `catch2/catch.hpp`, `catch2/catch_all.hpp`, `catch2/catch_test_macros.hpp`, and anything starting with `catch2/`
   - For each remaining include, resolve the actual file path by searching:
     1. Relative to the test file directory
     2. Module `Public/` directory
     3. Module `Private/` directory
     4. Basename search in `Public/`, `Private/`, `Classes/`, `Source/` under the module root
   - Each resolved include creates a mapping with `direct_include` evidence (+50 points)

2. **Apply naming convention matching** on the test filename:
   - Strip the test suffix using these patterns (check in order, stop at first match):
     - `(.+)_tests$` -> `\1` (e.g., `foo_tests.cpp` -> `foo`)
     - `(.+)_test$` -> `\1` (e.g., `foo_test.cpp` -> `foo`)
     - `(.+)Tests$` -> `\1` (e.g., `FooTests.cpp` -> `Foo`)
     - `(.+)Test$` -> `\1` (e.g., `FooTest.cpp` -> `Foo`)
     - `^Test(.+)$` -> `\1` (e.g., `TestFoo.cpp` -> `Foo`)
   - Generate candidate source basenames: `{name}.h`, `{name}.cpp`, `{name}.inl`
   - Search for these files in the module root by:
     1. Walking up from the test file to find a directory named `Tests/`
     2. The parent of `Tests/` is the module root
     3. Searching recursively in `Public/`, `Private/`, `Classes/`, `Source/`, and the module root itself
   - Each found file creates a mapping with `naming_convention` evidence (+30 points)

3. **Add module dependency evidence** (if `module_dependencies` provided):
   - For each module name, add `module_dependency` evidence (+20 points) to ALL existing mappings
   - This boosts confidence for already-discovered mappings

4. **Calculate confidence** for each mapping by summing all evidence points and applying the confidence level thresholds above.

5. **Filter by minimum confidence** if specified.

### Reverse Lookup: Source File -> Test Files

To find test files that test a given source file, the agent should:

1. **Find all test files** by globbing `*.cpp` and `*.cxx` recursively under the test root directory.

2. **For each test file**, check:
   - **Direct include check**: Parse the test file's `#include` directives and check if any include's basename matches the source file's basename. If so, add `direct_include` evidence (+50 points).
   - **Naming convention check**: Check if the test filename matches the source stem with a test suffix:
     - `{source_stem}Tests?` (e.g., `LruCacheTest.cpp` or `LruCacheTests.cpp` for `LruCache.h`)
     - `Test{source_stem}` (e.g., `TestLruCache.cpp` for `LruCache.h`)
   - If naming matches, add `naming_convention` evidence (+30 points).

3. **Create mappings** only for test files where at least one piece of evidence was found.

---

## Error Handling

| Error | Cause | Status |
|-------|-------|--------|
| Test file not found | `test_file` path does not exist | `error` |
| Source file not found | `source_file` path does not exist | `error` |
| Invalid project root | `project_root` does not exist | `error` |
| No mappings found | No evidence found for given file | `success` with warning |

---

## Limitations

1. **No transitive include analysis**: Only direct `#include` directives are parsed
2. **No semantic analysis**: Cannot detect testing relationships from code logic
3. **Module dependencies require manual input**: `.Build.cs` parsing not integrated
4. **Path resolution heuristics**: May miss includes with complex search paths
