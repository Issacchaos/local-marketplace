# C++ Test Location Detection

**Language**: C++
**Build Systems**: CMake, Make, Bazel
**Frameworks**: Google Test (gtest/gmock), Catch2
**Version**: 1.0.0

---

## Overview

C++ test location conventions follow patterns influenced by the build system and project structure. Unlike Go (co-located tests) or C# (separate test projects), C++ projects typically use a dedicated test directory structure. This document provides guidance for determining correct test file locations in C++ projects.

---

## Configuration Sources (Priority Order)

### 1. CMakeLists.txt Files

**Location**: Project root and subdirectories
**Purpose**: Defines source structure and test targets

```cmake
cmake_minimum_required(VERSION 3.15)
project(Calculator CXX)

# Source library
add_library(calculator
    src/calculator.cpp
    src/operations/add.cpp
)

# Test executable
add_executable(calculator_test
    tests/calculator_test.cpp
    tests/operations/add_test.cpp
)
```

**Detection Strategy**:
- Find `CMakeLists.txt` in project root
- Parse for `add_executable` with test targets
- Identify test directory from test source paths
- Extract test file naming patterns

---

### 2. Build Directory Structure

**Location**: Project root
**Purpose**: Indicates build system and test organization

**Common Patterns**:
```
project/
├── build/          # CMake out-of-source build
├── Makefile        # Make-based project
├── BUILD           # Bazel project
└── WORKSPACE       # Bazel workspace
```

**Detection Logic**:
- CMake: Look for `build/` directory or `CMakeLists.txt`
- Make: Look for `Makefile` or `makefile`
- Bazel: Look for `WORKSPACE` and `BUILD` files

---

### 3. Project Layout Convention

**Most Common**: Separate `tests/` or `test/` directory

```
project/
├── include/
│   └── calculator/
│       └── calculator.h
├── src/
│   ├── calculator.cpp
│   └── operations/
│       ├── add.cpp
│       └── divide.cpp
└── tests/
    ├── calculator_test.cpp
    └── operations/
        ├── add_test.cpp
        └── divide_test.cpp
```

---

## Standard Test Locations

### Pattern 1: tests/ Directory (Most Common)

**Structure**:
```
project/
├── src/
│   ├── calculator.cpp
│   └── operations/
│       └── add.cpp
└── tests/
    ├── calculator_test.cpp
    └── operations/
        └── add_test.cpp
```

**Characteristics**:
- Mirrors `src/` directory structure
- Test files named with `_test.cpp` or `_unittest.cpp` suffix
- Most widely used in modern C++ projects

---

### Pattern 2: test/ Directory (Singular)

**Structure**:
```
project/
├── src/
│   └── calculator.cpp
└── test/
    └── calculator_test.cpp
```

**Characteristics**:
- Similar to `tests/` but singular form
- Used by some projects (e.g., LLVM, Boost)
- Less common but valid

---

### Pattern 3: Per-Component Tests

**Structure**:
```
project/
├── calculator/
│   ├── src/
│   │   └── calculator.cpp
│   └── tests/
│       └── calculator_test.cpp
└── geometry/
    ├── src/
    │   └── circle.cpp
    └── tests/
        └── circle_test.cpp
```

**Characteristics**:
- Each component has its own test directory
- Common in large monorepo projects
- Used in Google-style projects

---

## File Naming Conventions

### Naming Pattern 1: *_test.cpp (Recommended)

**Pattern**: `{basename}_test.cpp`

**Examples**:
- `calculator.cpp` → `calculator_test.cpp`
- `add_operation.cpp` → `add_operation_test.cpp`
- `user_service.cpp` → `user_service_test.cpp`

**Rationale**: Aligns with Google Test conventions and Google C++ Style Guide

---

### Naming Pattern 2: *_unittest.cpp

**Pattern**: `{basename}_unittest.cpp`

**Examples**:
- `calculator.cpp` → `calculator_unittest.cpp`
- `string_utils.cpp` → `string_utils_unittest.cpp`

**Rationale**: Explicitly indicates unit tests (vs integration tests)

---

### Naming Pattern 3: test_*.cpp

**Pattern**: `test_{basename}.cpp`

**Examples**:
- `calculator.cpp` → `test_calculator.cpp`
- `operations.cpp` → `test_operations.cpp`

**Rationale**: Python-style naming, less common in C++

---

### Integration vs Unit Tests

**Separate by Directory**:
```
tests/
├── unit/
│   ├── calculator_test.cpp
│   └── operations_test.cpp
└── integration/
    └── end_to_end_test.cpp
```

**Separate by Naming**:
```
tests/
├── calculator_test.cpp          # Unit test
├── calculator_integration_test.cpp  # Integration test
└── calculator_benchmark_test.cpp    # Benchmark test
```

---

## Directory Structures

### Structure 1: Flat Source, Separate Tests (Simple)

```
calculator/
├── CMakeLists.txt
├── calculator.cpp
├── calculator.h
├── operations.cpp
└── tests/
    ├── calculator_test.cpp
    └── operations_test.cpp
```

**Path Resolution**:
- Source: `calculator.cpp`
- Test: `tests/calculator_test.cpp`

**When Used**: Small projects, single-header libraries

---

### Structure 2: Include/Src Split (Common)

```
calculator/
├── CMakeLists.txt
├── include/
│   └── calculator/
│       ├── calculator.h
│       └── operations.h
├── src/
│   ├── calculator.cpp
│   └── operations.cpp
└── tests/
    ├── calculator_test.cpp
    └── operations_test.cpp
```

**Path Resolution**:
- Source: `src/calculator.cpp`
- Header: `include/calculator/calculator.h`
- Test: `tests/calculator_test.cpp`

**When Used**: Libraries with public API, most professional projects

---

### Structure 3: Mirrored Directory Structure (Recommended)

```
calculator/
├── CMakeLists.txt
├── include/
│   └── calculator/
│       ├── calculator.h
│       └── operations/
│           ├── add.h
│           └── divide.h
├── src/
│   ├── calculator.cpp
│   └── operations/
│       ├── add.cpp
│       └── divide.cpp
└── tests/
    ├── calculator_test.cpp
    └── operations/
        ├── add_test.cpp
        └── divide_test.cpp
```

**Path Resolution**:
- Source: `src/operations/add.cpp`
- Test: `tests/operations/add_test.cpp`

**When Used**: Large projects with nested namespaces

---

### Structure 4: Header-Only Library

```
mathlib/
├── CMakeLists.txt
├── include/
│   └── mathlib/
│       ├── vector.hpp
│       ├── matrix.hpp
│       └── algorithms/
│           └── sort.hpp
└── tests/
    ├── vector_test.cpp
    ├── matrix_test.cpp
    └── algorithms/
        └── sort_test.cpp
```

**Path Resolution**:
- Header: `include/mathlib/vector.hpp`
- Test: `tests/vector_test.cpp`

**When Used**: Template libraries, header-only implementations

---

### Structure 5: Monorepo with Components

```
monorepo/
├── calculator/
│   ├── CMakeLists.txt
│   ├── src/
│   │   └── calculator.cpp
│   └── tests/
│       └── calculator_test.cpp
├── geometry/
│   ├── CMakeLists.txt
│   ├── src/
│   │   └── circle.cpp
│   └── tests/
│       └── circle_test.cpp
└── CMakeLists.txt
```

**Path Resolution**:
- Source: `calculator/src/calculator.cpp`
- Test: `calculator/tests/calculator_test.cpp`

**When Used**: Multi-project repositories, large organizations

---

## CMake Test Configuration

### Test Target Discovery

**From CMakeLists.txt**:
```cmake
# Test executable definition
add_executable(calculator_test
    tests/calculator_test.cpp
    tests/operations_test.cpp
)

# Link with source library
target_link_libraries(calculator_test PRIVATE
    calculator
    GTest::GTest
    GTest::Main
)

# Register with CTest
add_test(NAME calculator_test COMMAND calculator_test)
```

**Detection Algorithm**:
1. Find all `CMakeLists.txt` files
2. Parse for `add_executable` with "test" in name
3. Extract test file paths from source list
4. Identify test directory pattern

---

### Test Discovery Patterns

**Google Test Discovery**:
```cmake
include(GoogleTest)
gtest_discover_tests(calculator_test)
```

**Catch2 Discovery**:
```cmake
include(Catch)
catch_discover_tests(calculator_test)
```

**Manual Test Addition**:
```cmake
add_test(NAME calculator_test COMMAND calculator_test)
```

---

## Detection Algorithm

### Step 1: Identify Project Root

**Look for**:
- `CMakeLists.txt` (CMake project)
- `WORKSPACE` or `BUILD` files (Bazel)
- `Makefile` (Make project)
- `.git/` directory

**Result**: Project root directory

---

### Step 2: Detect Test Directory

**Check for existence** (priority order):
1. `tests/` directory
2. `test/` directory
3. `src/tests/` directory
4. Component-specific `*/tests/` directories

**Fallback**: If no test directory exists, create `tests/` directory

---

### Step 3: Identify Source File Structure

**Determine source directory**:
- Check for `src/` directory
- Check for `include/` directory
- Check for flat structure (sources in root)

**Extract relative path**:
- Source: `src/operations/add.cpp`
- Relative path: `operations/add.cpp`
- Relative directory: `operations/`

---

### Step 4: Apply Naming Convention

**Detect existing naming pattern**:
```python
# Sample existing test files
test_files = glob("tests/**/*_test.cpp")
unittest_files = glob("tests/**/*_unittest.cpp")
prefix_test_files = glob("tests/**/test_*.cpp")

if len(test_files) > len(unittest_files):
    pattern = "_test.cpp"
elif len(unittest_files) > 0:
    pattern = "_unittest.cpp"
else:
    pattern = "_test.cpp"  # Default
```

**Transform source filename**:
- Source: `add.cpp`
- Base name: `add`
- Test name: `add_test.cpp` (or `add_unittest.cpp`)

---

### Step 5: Construct Test Path

**Components**:
- Test directory: `tests/`
- Relative subdirectory: `operations/`
- Test filename: `add_test.cpp`

**Final Test Path**: `tests/operations/add_test.cpp`

---

## Path Resolution Algorithm

### Complete Algorithm

```python
def determine_cpp_test_path(source_file, project_root):
    """
    Determine test file path for C++ source file

    Args:
        source_file: Absolute path to source file
        project_root: Absolute path to project root

    Returns:
        Absolute path to test file
    """
    # Step 1: Validate source file
    if not source_file.endswith(('.cpp', '.cc', '.cxx')):
        raise ValueError("Not a C++ source file")

    # Step 2: Detect test directory
    test_dir = detect_test_directory(project_root)

    # Step 3: Get relative path within source structure
    source_dir = detect_source_directory(project_root)

    if source_dir and source_file.startswith(source_dir):
        # Source is in src/ or similar
        relative_path = os.path.relpath(source_file, source_dir)
    else:
        # Source is in root or other location
        relative_path = os.path.relpath(source_file, project_root)

    # Step 4: Extract directory and filename
    rel_dir = os.path.dirname(relative_path)
    source_filename = os.path.basename(source_file)

    # Step 5: Apply naming convention
    base_name = os.path.splitext(source_filename)[0]
    naming_pattern = detect_naming_pattern(test_dir)

    if naming_pattern == "_test.cpp":
        test_filename = f"{base_name}_test.cpp"
    elif naming_pattern == "_unittest.cpp":
        test_filename = f"{base_name}_unittest.cpp"
    elif naming_pattern == "test_*.cpp":
        test_filename = f"test_{base_name}.cpp"
    else:
        test_filename = f"{base_name}_test.cpp"  # Default

    # Step 6: Construct test path
    if rel_dir:
        test_path = os.path.join(project_root, test_dir, rel_dir, test_filename)
    else:
        test_path = os.path.join(project_root, test_dir, test_filename)

    # Step 7: Validate
    validate_test_path(test_path, project_root)

    return test_path


def detect_test_directory(project_root):
    """Detect test directory in project"""
    candidates = [
        "tests",
        "test",
        "src/tests",
        "unittest"
    ]

    for candidate in candidates:
        test_path = os.path.join(project_root, candidate)
        if os.path.exists(test_path) and os.path.isdir(test_path):
            return candidate

    # Fallback: create tests/ directory
    return "tests"


def detect_source_directory(project_root):
    """Detect primary source directory"""
    candidates = ["src", "source", "lib"]

    for candidate in candidates:
        src_path = os.path.join(project_root, candidate)
        if os.path.exists(src_path) and os.path.isdir(src_path):
            return os.path.join(project_root, candidate)

    return None  # Source files in root


def detect_naming_pattern(test_dir):
    """Detect existing test file naming pattern"""
    if not os.path.exists(test_dir):
        return "_test.cpp"  # Default

    # Count patterns
    test_suffix_count = len(glob.glob(f"{test_dir}/**/*_test.cpp", recursive=True))
    unittest_suffix_count = len(glob.glob(f"{test_dir}/**/*_unittest.cpp", recursive=True))
    test_prefix_count = len(glob.glob(f"{test_dir}/**/test_*.cpp", recursive=True))

    # Choose most common
    if test_suffix_count >= unittest_suffix_count and test_suffix_count >= test_prefix_count:
        return "_test.cpp"
    elif unittest_suffix_count >= test_prefix_count:
        return "_unittest.cpp"
    else:
        return "test_*.cpp"


def validate_test_path(test_path, project_root):
    """Validate test path is acceptable"""
    # Must be within project
    if not test_path.startswith(project_root):
        raise ValueError("Test path outside project root")

    # Must not be in forbidden directories
    forbidden = [".claude-tests", ".claude", "build", "cmake-build-debug"]
    for forbidden_dir in forbidden:
        if forbidden_dir in test_path:
            raise ValueError(f"Test path contains forbidden directory: {forbidden_dir}")

    # Must have correct extension
    if not test_path.endswith(('.cpp', '.cc', '.cxx')):
        raise ValueError("Test path must end with .cpp, .cc, or .cxx")
```

---

## Path Resolution Examples

### Example 1: Simple Project

**Input**:
- Source: `/home/user/project/calculator.cpp`
- Project root: `/home/user/project/`

**Detection**:
- Test directory: `tests/` (default)
- Source directory: None (flat structure)
- Relative path: `calculator.cpp`
- Naming pattern: `_test.cpp`

**Output**:
- Test: `/home/user/project/tests/calculator_test.cpp`

---

### Example 2: Include/Src Split

**Input**:
- Source: `/home/user/project/src/calculator.cpp`
- Project root: `/home/user/project/`

**Detection**:
- Test directory: `tests/` (exists)
- Source directory: `src/`
- Relative path: `calculator.cpp`
- Naming pattern: `_test.cpp`

**Output**:
- Test: `/home/user/project/tests/calculator_test.cpp`

---

### Example 3: Nested Directory Structure

**Input**:
- Source: `/home/user/project/src/operations/add.cpp`
- Project root: `/home/user/project/`

**Detection**:
- Test directory: `tests/`
- Source directory: `src/`
- Relative path: `operations/add.cpp`
- Relative directory: `operations/`
- Naming pattern: `_test.cpp`

**Output**:
- Test: `/home/user/project/tests/operations/add_test.cpp`

---

### Example 4: Header-Only Library

**Input**:
- Header: `/home/user/project/include/mathlib/vector.hpp`
- Project root: `/home/user/project/`

**Detection**:
- Test directory: `tests/`
- Source directory: `include/mathlib/`
- Relative path: `vector.hpp`
- Naming pattern: `_test.cpp`

**Output**:
- Test: `/home/user/project/tests/vector_test.cpp`

---

### Example 5: Monorepo Component

**Input**:
- Source: `/home/user/monorepo/calculator/src/calculator.cpp`
- Project root: `/home/user/monorepo/calculator/`

**Detection**:
- Test directory: `tests/`
- Source directory: `src/`
- Relative path: `calculator.cpp`
- Naming pattern: `_test.cpp`

**Output**:
- Test: `/home/user/monorepo/calculator/tests/calculator_test.cpp`

---

## Validation Rules

### Valid Test Locations

- `tests/calculator_test.cpp`
- `test/calculator_test.cpp`
- `tests/unit/calculator_test.cpp`
- `tests/integration/calculator_integration_test.cpp`
- `calculator/tests/calculator_test.cpp` (component structure)
- `src/tests/calculator_test.cpp` (less common)

---

### Invalid Test Locations

- `.claude-tests/calculator_test.cpp` (temporary directory)
- `build/calculator_test.cpp` (build directory)
- `cmake-build-debug/calculator_test.cpp` (IDE build directory)
- `/tmp/calculator_test.cpp` (outside project)
- `calculator_test.cpp` (in root, should be in tests/)

---

## Edge Cases

### Case 1: Multiple Source Extensions

**Source files**:
```
src/
├── calculator.cpp
├── operations.cc
└── utils.cxx
```

**Test files**:
```
tests/
├── calculator_test.cpp
├── operations_test.cpp  # Normalized to .cpp
└── utils_test.cpp       # Normalized to .cpp
```

**Rule**: Test files should always use `.cpp` extension (most common)

---

### Case 2: Header-Only Implementation

**Source**:
```
include/
└── mathlib/
    ├── vector.hpp
    └── matrix.hpp
```

**Tests**:
```
tests/
├── vector_test.cpp
└── matrix_test.cpp
```

**Rule**: Test `.hpp` headers with `.cpp` test files

---

### Case 3: Template Implementations

**Source**:
```
include/
└── container.hpp       # Template class
└── container.tpp       # Template implementation
```

**Tests**:
```
tests/
└── container_test.cpp  # Tests both .hpp and .tpp
```

**Rule**: Single test file for header + implementation template

---

### Case 4: Multiple Files for One Class

**Source**:
```
src/
├── database.cpp
├── database_connection.cpp
└── database_query.cpp
```

**Tests** (Option 1 - Per file):
```
tests/
├── database_test.cpp
├── database_connection_test.cpp
└── database_query_test.cpp
```

**Tests** (Option 2 - Combined):
```
tests/
└── database_test.cpp  # Tests all database files
```

**Rule**: Prefer per-file tests for modularity

---

### Case 5: Test Utilities

**Test helpers**:
```
tests/
├── helpers/
│   ├── test_utils.cpp
│   └── mock_data.cpp
├── calculator_test.cpp
└── operations_test.cpp
```

**Rule**: Test utilities go in `tests/helpers/` or `tests/utils/`

---

## Integration with Build Systems

### CMake Integration

**Create Test Target in CMakeLists.txt**:
```cmake
# When creating new test file
add_executable(calculator_test
    tests/calculator_test.cpp
    tests/operations/add_test.cpp  # New test file
)

target_link_libraries(calculator_test PRIVATE
    calculator
    GTest::GTest
    GTest::Main
)

gtest_discover_tests(calculator_test)
```

---

### Makefile Integration

**Add Test Target**:
```makefile
# Test sources
TEST_SRC = tests/calculator_test.cpp tests/operations_test.cpp
TEST_BIN = build/calculator_test

$(TEST_BIN): $(TEST_SRC) $(SRC)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

test: $(TEST_BIN)
	./$(TEST_BIN)
```

---

### Bazel Integration

**BUILD File**:
```python
cc_test(
    name = "calculator_test",
    srcs = [
        "tests/calculator_test.cpp",
        "tests/operations/add_test.cpp",
    ],
    deps = [
        ":calculator",
        "@com_google_googletest//:gtest_main",
    ],
)
```

---

## Integration with Write Agent

### Write Agent Workflow

```python
def create_cpp_test_file(source_file, project_root):
    """
    Create C++ test file for given source file

    Workflow:
    1. Determine test path using detection algorithm
    2. Read source file to extract class/function names
    3. Generate test file content (Google Test or Catch2)
    4. Write test file to determined path
    5. Update CMakeLists.txt if needed
    """
    # Step 1: Determine test path
    test_path = determine_cpp_test_path(source_file, project_root)

    # Step 2: Ensure test directory exists
    test_dir = os.path.dirname(test_path)
    os.makedirs(test_dir, exist_ok=True)

    # Step 3: Parse source file for testable entities
    classes, functions = parse_cpp_source(source_file)

    # Step 4: Detect test framework
    framework = detect_test_framework(project_root)

    # Step 5: Generate test content
    if framework == "gtest":
        content = generate_gtest_content(classes, functions, source_file)
    elif framework == "catch2":
        content = generate_catch2_content(classes, functions, source_file)

    # Step 6: Write test file
    with open(test_path, 'w') as f:
        f.write(content)

    # Step 7: Update CMakeLists.txt (if needed)
    update_cmake_test_target(test_path, project_root)

    return test_path
```

---

## File Organization Strategies

### Strategy 1: Per-Source-File Tests

**One test file per source file**:
```
src/
├── calculator.cpp
├── add.cpp
└── divide.cpp

tests/
├── calculator_test.cpp
├── add_test.cpp
└── divide_test.cpp
```

**Pros**: Clear mapping, easy to locate tests
**Cons**: Many small test files

---

### Strategy 2: Per-Class Tests

**One test file per class**:
```
src/
├── calculator.cpp         # Calculator class
├── calculator_impl.cpp    # Calculator implementation
└── calculator_utils.cpp   # Helper functions

tests/
└── calculator_test.cpp    # Tests all Calculator files
```

**Pros**: Logical grouping, fewer files
**Cons**: Large test files, harder to navigate

---

### Strategy 3: Per-Feature Tests

**Organize by feature**:
```
src/
├── arithmetic.cpp
├── trigonometry.cpp
└── statistics.cpp

tests/
├── arithmetic_test.cpp      # Add, subtract, multiply, divide
├── trigonometry_test.cpp    # Sin, cos, tan
└── statistics_test.cpp      # Mean, median, mode
```

**Pros**: Tests organized by functionality
**Cons**: May not map directly to source files

---

### Strategy 4: Separate Unit and Integration

**Different directories**:
```
tests/
├── unit/
│   ├── calculator_test.cpp
│   └── operations_test.cpp
└── integration/
    └── end_to_end_test.cpp
```

**Pros**: Clear separation of test types
**Cons**: More complex structure

---

## Summary

**Key Principles**:
1. C++ tests are typically in separate `tests/` or `test/` directory
2. Test file naming: `{basename}_test.cpp` (recommended)
3. Mirror source directory structure in test directory
4. Header-only libraries: test `.hpp` files with `.cpp` test files
5. **NEVER use `.claude-tests/` or build directories for tests**
6. Test file location depends on build system configuration

**Priority Order**:
1. Detect test directory (tests/ or test/)
2. Identify source directory (src/, include/, or root)
3. Calculate relative path within source structure
4. Apply naming convention (_test.cpp, _unittest.cpp, or test_*.cpp)
5. Mirror directory structure in test directory
6. Validate path is within project and not in forbidden directories

**Detection Algorithm**:
```
1. Find project root (CMakeLists.txt, WORKSPACE, or .git/)
2. Detect test directory (tests/ or test/)
3. Identify source directory (src/, include/, or root)
4. Extract relative path from source directory
5. Apply naming convention (detect from existing tests)
6. Construct test path: {test_dir}/{relative_dir}/{basename}_test.cpp
7. Validate path (not in build/, .claude-tests/, or outside project)
```

**Common Patterns**:
- **Flat**: `tests/{basename}_test.cpp`
- **Mirrored**: `tests/{relative_path}/{basename}_test.cpp`
- **Component**: `{component}/tests/{basename}_test.cpp`
- **Header-only**: `tests/{basename}_test.cpp` (for `.hpp` files)

**Integration**:
- Update `CMakeLists.txt` to include new test files
- Add test target with `add_executable()`
- Link with test framework and source library
- Register with CTest using `gtest_discover_tests()` or `add_test()`

---

**Last Updated**: 2026-01-06
**Status**: Phase 4 - Systems Languages (TASK-CPP-006)
**Phase**: Complete
