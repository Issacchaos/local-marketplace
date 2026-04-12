# llt-coverage

**Metadata**:
```yaml
applies_to:
  language: C++
  frameworks: [Catch2, LowLevelTests]
  project_indicators: ["*.Build.cs", "TestHarness.h"]
capabilities:
  - source_discovery
  - coverage_analysis
  - function_extraction
  - dependency_analysis
```

Calculate module-level test coverage for Unreal Engine LowLevelTests.

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.

## Overview

Analyzes `.Build.cs` files to build a module dependency graph and calculates test coverage based on which runtime modules have test modules depending on them. A module is "covered" if at least one test module (directly or transitively) depends on it.

Additionally supports function-level coverage analysis by extracting C++ functions from source files and matching them against test file references.

## Orchestration Flow

To analyze coverage for a UE project:

1. **Parse command-line arguments**: `--project-root`, `--output-format` (json/table/summary), optional `--module` filter
2. **Find .Build.cs files**: Recursively search `Engine/Source/Runtime` and `FortniteGame/Plugins` for `.Build.cs` files
3. **Parse each .Build.cs file**: Extract module name, dependencies, and classify as test or runtime module (see Build.cs Parsing Instructions below)
4. **Build dependency graph**: Construct forward and reverse adjacency lists, compute transitive closure (see Dependency Graph Instructions)
5. **Compute module-level coverage**: For each runtime module, find all test modules depending on it (see Coverage Computation)
6. **Optional - Function-level analysis** (if time permits):
   - For each covered module, extract C++ functions from source files (see C++ Function Extraction Instructions)
   - Extract function references from test files (see Test Function Extraction Instructions)
   - Match references to signatures and compute function-level coverage
7. **Generate output**: Format as JSON (with LLT standard envelope), table, or summary based on `--output-format`
8. **Return results**: Wrap results in the standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md) Response Format)

## Usage Examples

```bash
# Calculate coverage with JSON output (default)
python -m llt_coverage --project-root /path/to/ue5 --output-format json

# Show detailed table with all modules
python -m llt_coverage --project-root /path/to/ue5 --output-format table

# Show brief summary
python -m llt_coverage --project-root /path/to/ue5 --output-format summary

# Filter to specific module
python -m llt_coverage --project-root /path/to/ue5 --module Core --output-format table
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--project-root PATH` | Yes | Path to UE project root containing Engine/ and FortniteGame/ |
| `--output-format {json\|table\|summary}` | No | Output format (default: json) |
| `--module NAME` | No | Filter results to a specific module name |

## Output (JSON)

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "data": {
    "build_cs_files_found": 450,
    "modules_parsed": 442,
    "coverage": [
      {
        "module_name": "Core",
        "covered": true,
        "test_modules": ["CoreTests", "FoundationTests"]
      },
      {
        "module_name": "UntestedModule",
        "covered": false,
        "test_modules": []
      }
    ],
    "statistics": {
      "total_modules": 300,
      "covered_modules": 275,
      "uncovered_modules": 25,
      "coverage_percentage": 91.67,
      "uncovered_module_names": ["UntestedModule1", "UntestedModule2"]
    }
  }
}
```

## Coverage Calculation

1. **Module Discovery**: Finds all `.Build.cs` files in `Engine/Source/Runtime` and `FortniteGame/Plugins`
2. **Dependency Parsing**: Extracts `PublicDependencyModuleNames` and `PrivateDependencyModuleNames`
3. **Graph Construction**: Builds directed dependency graph
4. **Coverage Mapping**: For each runtime module, finds all test modules that depend on it (directly or transitively)
5. **Coverage Status**: A module is "covered" if at least one test module depends on it

Excluded from coverage calculations: `Catch2`, `OnlineTestsCore`, `LowLevelTestsRunner`

---

## C++ Function Extraction Instructions

When performing function-level coverage analysis, extract functions and methods from C++ source files using either Clang AST parsing (preferred) or regex-based fallback.

### Data Model

For each extracted function, capture:
- **name**: Short function name (e.g., `OpenInventory`)
- **qualified_name**: Fully qualified name including class (e.g., `FSaveFramework::OpenInventory`)
- **return_type**: Return type string (e.g., `void`, `bool`)
- **file_path**: Source file path
- **line_number**: Line number of the definition
- **is_public**: Whether the function is public (free functions are always public)
- **is_static**: Whether the function is static
- **is_const**: Whether it is a const method
- **is_constructor / is_destructor**: Whether it is a constructor or destructor
- **class_name**: Owning class name, or null for free functions

### Approach 1: Clang AST Parsing (Preferred)

Use `libclang` Python bindings (`clang.cindex`) when available:

1. Create a `clang.cindex.Index` and parse the source file as a translation unit.
2. If a `compile_commands.json` exists (search upward from module root), use it for accurate include resolution. Otherwise parse with `-x c++ -std=c++17 -I.` and `PARSE_SKIP_FUNCTION_BODIES`.
3. Traverse the AST recursively from the root cursor:
   - For `CLASS_DECL` and `STRUCT_DECL` nodes: record the class name and recurse into children with that class context.
   - For `FUNCTION_DECL`, `CXX_METHOD`, `CONSTRUCTOR`, `DESTRUCTOR` nodes: extract the function signature.
   - Skip nodes whose location file does not match the target source file (to ignore included headers).
   - Skip forward declarations (non-definitions) for non-method cursors.
4. For each function node, read: `spelling` (name), `result_type.spelling` (return type), `access_specifier` (public/private), `is_static_method()`, `is_const_method()`, and cursor kind (constructor/destructor).
5. Build `qualified_name` as `ClassName::FunctionName` when inside a class context.

### Approach 2: Regex-Based Extraction (Fallback)

When Clang is unavailable, use line-by-line regex parsing:

1. Track class/struct context using brace-depth counting:
   - Match `(?:class|struct)\s+(\w+)\s*(?::\s*public\s+\w+\s*)?{` to detect class declarations.
   - Increment/decrement brace depth on `{` and `}`. When depth returns to 0, exit class context.
2. Skip lines starting with `//` (comments) or `#` (preprocessor directives).
3. Match function definitions with the pattern:
   ```
   (\w+(?:\s*\*|\s*&)?)\s+(?:(\w+)::)?(\w+)\s*\([^)]*\)\s*(const)?\s*(?:override)?\s*{
   ```
   - Group 1: return type
   - Group 2: explicit class qualifier (e.g., from `ClassName::Method` out-of-class definitions)
   - Group 3: function name
   - Group 4: const qualifier
4. If no explicit class qualifier is found but we are inside a class context (from brace tracking), use the current class.
5. Detect constructors (function name equals class name) and destructors (name starts with `~`).
6. Free functions (not inside any class context) are assumed public. Methods inside class context need explicit `public:` tracking for accuracy (regex approach cannot reliably detect this).

### Module-Wide Extraction

To extract functions from an entire module:
1. Recursively find all `.cpp` files under the module directory.
2. Look for `compile_commands.json` by searching upward from the module root.
3. Extract functions from each file, trying Clang first, falling back to regex.
4. Aggregate all results.

### Filtering Testable Functions

After extraction, filter to testable functions:
- Exclude constructors and destructors.
- Exclude non-public methods (private methods are typically internal helpers).
- Keep trivial getters/setters (names matching `Get*`, `Is*`, `Has*`, `Can*`) for completeness, but note they may inflate counts.

---

## Test Function Extraction Instructions

Analyze test files to determine which runtime functions are being tested, then match references back to extracted function signatures.

### Extracting Function References from Test Files

For each test file (`.cpp` and `*Test*.h` files under the test module):

1. Read the file line by line, skipping comment lines (starting with `//`).
2. Apply these regex patterns to each line to find function references:
   - **Class::Method calls**: `(\w+)::(\w+)\s*\(` -- captures qualified method calls
   - **Arrow-method calls**: `->(\w+)\s*\(` -- captures pointer-to-member calls
   - **Dot-method calls**: `\.(\w+)\s*\(` -- captures object member calls
   - **Assertion-wrapped calls**: `(?:CHECK|REQUIRE|REQUIRE_FALSE|CHECK_FALSE)\s*\(\s*(\w+(?:::\w+)*)\s*\(` -- captures function calls inside Catch2 assertions
   - **Mock expectations**: `EXPECT_CALL\s*\([^,]+,\s*(\w+)\s*\)` -- captures mocked method names
3. Collect all matches into a set of function reference strings:
   - If the match contains `::`, store the full `Class::Method` form (up to the opening parenthesis).
   - Otherwise store just the method name, excluding names starting with `_`.

### Matching References to Signatures

Compare test file references against the extracted runtime function signatures:

1. **Exact match** (confidence 1.0): The reference string matches a function's `qualified_name` exactly (e.g., `FSaveFramework::OpenInventory`).
2. **Partial match** (confidence 0.7): The reference string matches a function's short `name` only. This is less reliable because multiple classes may have methods with the same name.
3. Only count matches with confidence >= 0.7 when computing coverage.

### Function-Level Coverage Computation

1. Gather all runtime function signatures from the runtime module (using C++ function extraction above).
2. Gather all function references from associated test modules (using test function extraction above).
3. Match references to signatures using exact and partial matching.
4. Partition runtime functions into **covered** (matched by at least one test reference with confidence >= 0.7) and **uncovered** sets.
5. Calculate coverage percentage: `covered_count / total_count * 100`.

### Coverage Report Generation

Produce a report containing:
- **Module name**, **total functions**, **covered count**, **uncovered count**, **coverage percentage**
- **Uncovered functions grouped by class**: Dictionary mapping each class name to its list of uncovered qualified function names. Free functions go under a `_free_functions_` key.
- **Critical gaps**: Classes with 3 or more untested public functions, listed with their untested count and function names (limit 10 per class for readability).

---

## Dependency Graph Instructions

Build and analyze a directed module dependency graph from parsed `.Build.cs` data to map runtime modules to their test modules.

### Graph Data Model

The dependency graph consists of:
- **dependencies**: Adjacency list -- `module_name -> set of modules it depends on`
- **reverse_dependencies**: Reverse adjacency list -- `module_name -> set of modules that depend on it`
- **test_modules**: Set of module names identified as test modules
- **runtime_modules**: Set of module names identified as non-test modules
- **transitive_closure_cache**: Memoization cache for transitive dependency lookups

### Building the Graph

From a list of parsed `.Build.cs` module data:

1. For each module, determine if it is a test module or runtime module. Exclude test infrastructure modules (`Catch2`, `OnlineTestsCore`, `LowLevelTestsRunner`) from both sets.
2. Initialize an empty dependency set for the module if not already present.
3. Combine `PublicDependencyModuleNames` and `PrivateDependencyModuleNames` into a single dependency set.
4. For each dependency:
   - Add a forward edge: `module -> dependency`
   - Add a reverse edge: `dependency -> module`

### Computing Transitive Dependencies

Use iterative DFS with memoization:

1. Check the transitive closure cache first. Return cached result if available.
2. Initialize a visited set and a stack with the starting module.
3. Pop from stack, skip if already visited, mark as visited, then push all direct dependencies that haven't been visited.
4. After DFS completes, remove the starting module from the visited set (a module is not its own dependency).
5. Cache and return the result.

### Finding Test Modules for a Runtime Module

For each test module in the graph:

1. Check if the runtime module appears in the test module's **direct** dependencies. If yes, classify as a direct test module.
2. Otherwise, compute the test module's transitive dependencies and check if the runtime module appears. If yes, classify as a transitive test module.
3. Return both lists sorted alphabetically.

### Computing Module-Level Coverage

For each runtime module (optionally filtered to a subset):

1. Find all test modules (direct + transitive) that depend on it.
2. Mark the module as **covered** if at least one test module depends on it.
3. Collect results into a list of coverage records: `{module_name, covered, test_modules}`.

### Coverage Statistics

From the list of coverage records, compute:
- **total_modules**: Count of all analyzed runtime modules
- **covered_modules**: Count where `covered == true`
- **uncovered_modules**: `total - covered`
- **coverage_percentage**: `covered / total * 100`, rounded to 2 decimal places
- **uncovered_module_names**: Sorted list of uncovered module names

---

## Error Handling

| Error | Behavior |
|-------|----------|
| Invalid project root | Returns error |
| No .Build.cs files found | Returns error |
| Parse failures | Continues processing; includes warnings |
| Module not found (with --module) | Returns error |
| Clang unavailable | Falls back to regex-based extraction with a warning |
| File read failures | Skips file with warning, continues processing |

## Limitations

1. Module-level coverage is based on dependency graph analysis, not actual test execution
2. Function-level coverage uses static analysis (regex/AST) and may miss complex patterns
3. No line/branch coverage metrics
4. Regex extraction cannot reliably detect access specifiers (public/private) for class methods
5. Partial function name matches (confidence 0.7) may produce false positives when multiple classes share method names

## Dependencies

- [llt-common/SKILL.md](../llt-common/SKILL.md) - Response format, data structures, validation rules, and logging instructions

---

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

### Performance Note

For large projects (1600+ .Build.cs files):
1. First `Glob("**/*.Build.cs")` to get all paths
2. For test module detection: `Grep(": TestModuleRules")` across all files
3. For dependencies: Read files in priority order (test modules first, then modules under analysis)
4. Skip reading .Build.cs files that are clearly infrastructure (Catch2.Build.cs, etc.)
