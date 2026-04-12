---
name: test-location-detection
description: Detect and enforce correct test file locations per project and language conventions. Use when determining where to place generated test files based on project structure, build system configuration, and language-specific conventions.
user-invocable: false
---

# Test Location Detection Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Languages**: All supported languages
**Purpose**: Detect and enforce correct test file locations per project and language conventions

---

## Overview

The Test Location Detection Skill ensures that generated tests are placed in the correct, runnable location according to project structure and language conventions. This prevents tests from being placed in temporary directories (`.claude-tests/`, `.claude/`) where they won't be discovered by test runners.

**Key Principle**: Tests MUST be placed where the project's test runner expects to find them, following established conventions.

---

## Location Detection Algorithm

### Step 1: Identify Project Root

1. **Find project root markers**:
   - Python: `pyproject.toml`, `setup.py`, `setup.cfg`, `pytest.ini`, `requirements.txt`
   - JavaScript/TypeScript: `package.json`
   - Java: `pom.xml`, `build.gradle`, `build.gradle.kts`
   - C#: `*.csproj`, `*.sln`
   - Go: `go.mod`
   - Rust: `Cargo.toml`
   - Ruby: `Gemfile`
   - C/C++: `CMakeLists.txt`, `Makefile`

2. **Use git root as fallback**:
   - If no project marker found, use `.git` directory location

3. **Validate project root**:
   - Must be an ancestor of the source file being tested
   - Must be within workspace boundaries

---

### Step 2: Read Framework Configuration

Check framework-specific configuration files for test path settings:

#### Python (pytest)
```ini
# pytest.ini
[pytest]
testpaths = tests

# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests", "integration"]
```

#### JavaScript/TypeScript (Jest)
```json
// package.json or jest.config.js
{
  "jest": {
    "testMatch": ["**/__tests__/**/*.js", "**/?(*.)+(spec|test).js"]
  }
}
```

#### Java (Maven)
```xml
<!-- pom.xml -->
<build>
  <testSourceDirectory>src/test/java</testSourceDirectory>
</build>
```

#### Java (Gradle)
```gradle
// build.gradle
sourceSets {
    test {
        java.srcDirs = ['src/test/java']
    }
}
```

#### C# (.NET)
- Test projects typically in separate directory: `ProjectName.Tests/`
- Convention: `{ProjectName}.Tests` or `{ProjectName}.UnitTests`

#### Go
- Test files alongside source: `calculator.go` → `calculator_test.go`
- File naming convention: `*_test.go`

#### Rust
- Tests in `tests/` directory for integration tests
- Unit tests within source files in `#[cfg(test)]` modules

#### Ruby (RSpec)
```ruby
# .rspec or spec/spec_helper.rb
RSpec.configure do |config|
  config.pattern = 'spec/**/*_spec.rb'
end
```

---

### Step 3: Check Existing Test Directory Structure

Scan project for existing test directories:

1. **Look for common test directories**:
   - `tests/`, `test/`, `spec/`, `__tests__/`
   - Language-specific: `src/test/java/`, `ProjectName.Tests/`

2. **Analyze existing test files**:
   - Find test files matching patterns (`test_*.py`, `*_test.go`, `*.spec.ts`)
   - Determine directory structure relative to source files
   - Identify naming conventions

3. **Infer pattern from existing tests**:
   - If tests mirror source structure, follow same pattern
   - If tests are flat (all in one directory), use flat structure
   - If tests use subdirectories, create matching subdirectories

---

### Step 4: Apply Language-Specific Conventions

If no configuration or existing tests found, use language defaults:

#### Python
**Default**: `tests/` directory at project root, mirroring source structure

```
project/
├── src/
│   └── calculator.py
└── tests/
    └── test_calculator.py
```

**Alternative**: Tests alongside source (less common)
```
project/
└── src/
    ├── calculator.py
    └── test_calculator.py
```

**Naming**: `test_*.py` or `*_test.py`

---

#### JavaScript/TypeScript
**Default**: `__tests__/` or `tests/` directory

```
project/
├── src/
│   └── calculator.ts
└── __tests__/
    └── calculator.test.ts
```

**Alternative**: Tests alongside source
```
project/
└── src/
    ├── calculator.ts
    └── calculator.test.ts
```

**Naming**: `*.test.ts`, `*.spec.ts`, or `__tests__/*.ts`

---

#### Java (Maven)
**Default**: Separate test source directory

```
project/
├── src/
│   └── main/
│       └── java/
│           └── com/example/Calculator.java
└── src/
    └── test/
        └── java/
            └── com/example/CalculatorTest.java
```

**Naming**: `*Test.java` or `Test*.java`

---

#### Java (Gradle)
**Default**: Same as Maven

```
project/
├── src/
│   ├── main/
│   │   └── java/
│   │       └── com/example/Calculator.java
│   └── test/
│       └── java/
│           └── com/example/CalculatorTest.java
```

**Naming**: `*Test.java` or `Test*.java`

---

#### C#
**Default**: Separate test project

```
solution/
├── Calculator/
│   └── Calculator.cs
└── Calculator.Tests/
    └── CalculatorTests.cs
```

**Naming**: `*Tests.cs` or `*Test.cs`

---

#### Go
**Default**: Tests alongside source with `_test` suffix

```
project/
└── calculator/
    ├── calculator.go
    └── calculator_test.go
```

**Naming**: `*_test.go`

---

#### C++
**Default**: `tests/` directory at project root

```
project/
├── src/
│   └── calculator.cpp
└── tests/
    └── test_calculator.cpp
```

**Alternative**: Tests integrated in CMake structure
```
project/
├── src/
│   └── calculator.cpp
└── test/
    └── calculator_test.cpp
```

**Naming**: `test_*.cpp`, `*_test.cpp`, or framework-specific

---

#### Rust
**Default**: `tests/` directory for integration tests

```
project/
├── src/
│   └── lib.rs
└── tests/
    └── integration_test.rs
```

**Unit tests**: Within source files in `#[cfg(test)]` modules

**Naming**: Any name for integration tests, `*_test.rs` common

---

#### Ruby
**Default**: `spec/` directory for RSpec

```
project/
├── lib/
│   └── calculator.rb
└── spec/
    └── calculator_spec.rb
```

**Naming**: `*_spec.rb`

---

### Step 5: Resolve Final Test Path

Given source file path, determine test file path:

**Algorithm**:
```
1. Get project root
2. Get test directory from config or convention
3. Get source file relative path from source root
4. Apply naming convention
5. Construct full test path

Example (Python):
  Project root: /home/user/myproject/
  Source file: /home/user/myproject/src/utils/math.py
  Test directory: tests/ (from pytest.ini)
  Relative path: utils/math.py (relative to src/)
  Test filename: test_math.py (convention)
  Final path: /home/user/myproject/tests/utils/test_math.py
```

**Path Construction Template**:
```
{project_root}/{test_directory}/{relative_directory}/{test_filename}
```

---

## Validation Rules

Before creating test file, validate:

### ✅ Valid Test Locations
- Project's configured test directory (from config file)
- Standard test directory for language (`tests/`, `spec/`, `src/test/java/`)
- Alongside source files (if language convention: Go, Rust unit tests)
- Separate test project (C#)

### 🚫 Invalid Test Locations (MUST REJECT)
- `.claude-tests/` - Temporary directory, not discoverable
- `.claude/` - Configuration directory, not for tests
- `.git/` - Version control directory
- System temp directories (`/tmp/`, `C:\Temp\`)
- User home directory
- Root directory
- Outside project boundaries

**If invalid location detected**: Stop and raise error with recommendation.

---

## Error Handling

### No Project Root Found
```
Error: Cannot determine project root
Recommendation: Ensure source file is within a recognized project structure
```

### No Test Directory Configured
```
Warning: No test directory found in configuration
Action: Use language default convention (e.g., tests/ for Python)
```

### Invalid Test Path Constructed
```
Error: Constructed test path is invalid: .claude-tests/test_foo.py
Recommendation: Review project structure and framework configuration
```

### Source File Outside Project
```
Error: Source file is outside project boundaries
Recommendation: Ensure source file is within project root
```

---

## Integration with Write Agent

The Write Agent MUST:

1. **Call this skill** before generating any test file
2. **Get validated test path** from this skill
3. **Use the returned path** for test file creation
4. **Never hardcode** test paths or use `.claude-tests/`
5. **Create parent directories** if they don't exist

**Workflow**:
```
Write Agent receives: source_file = "src/calculator.py"

1. Call Test Location Detection Skill
   Input: source_file, project_root, language, framework
   Output: test_path = "tests/test_calculator.py"

2. Validate test_path is not in forbidden locations
   If test_path contains ".claude-tests/" → ERROR

3. Create parent directories if needed
   mkdir -p tests/

4. Generate test file at test_path
   Write to: tests/test_calculator.py
```

---

## Usage Examples

### Example 1: Python pytest Project

**Input**:
- Source file: `/home/user/myproject/src/calculator.py`
- Project root: `/home/user/myproject/`
- Language: `python`
- Framework: `pytest`
- Config: `pytest.ini` with `testpaths = tests`

**Output**:
- Test path: `/home/user/myproject/tests/test_calculator.py`
- Validation: ✅ Valid (in configured test directory)

---

### Example 2: Go Project

**Input**:
- Source file: `/home/user/myproject/calculator/calculator.go`
- Project root: `/home/user/myproject/`
- Language: `go`
- Framework: `go test`

**Output**:
- Test path: `/home/user/myproject/calculator/calculator_test.go`
- Validation: ✅ Valid (Go convention: tests alongside source)

---

### Example 3: Java Maven Project

**Input**:
- Source file: `/home/user/myproject/src/main/java/com/example/Calculator.java`
- Project root: `/home/user/myproject/`
- Language: `java`
- Framework: `junit`
- Config: `pom.xml` with standard Maven structure

**Output**:
- Test path: `/home/user/myproject/src/test/java/com/example/CalculatorTest.java`
- Validation: ✅ Valid (Maven convention)

---

### Example 4: Invalid Location (Rejected)

**Input**:
- Source file: `/home/user/myproject/src/calculator.py`
- Proposed test path: `/home/user/myproject/.claude-tests/test_calculator.py`

**Output**:
- Validation: ❌ Invalid
- Error: "Test path cannot be in .claude-tests/ directory"
- Recommendation: "Use project's configured test directory: tests/"

---

## Language-Specific Details Files

For detailed conventions, see language-specific documentation:

- [Python Test Locations](./python-test-locations.md)
- [JavaScript/TypeScript Test Locations](./javascript-test-locations.md) (Phase 3)
- [Java Test Locations](./java-test-locations.md) (Phase 3)
- [C# Test Locations](./csharp-test-locations.md) (Phase 4)
- [Go Test Locations](./go-test-locations.md) (Phase 4)
- [C++ Test Locations](./cpp-test-locations.md) (Phase 4)
- [Rust Test Locations](./rust-test-locations.md) (Phase 5)
- [Ruby Test Locations](./ruby-test-locations.md) (Phase 5)

---

## Testing This Skill

Validate with sample projects:

1. **Python pytest project** with `pytest.ini`
2. **Go project** with tests alongside source
3. **Java Maven project** with standard structure
4. **Mixed project** with multiple test directories

Expected outcomes:
- Correct test paths generated for each language
- Invalid locations rejected
- Configuration respected
- Fallback conventions applied when needed

---

## Future Enhancements

- Support custom test directory patterns
- Handle monorepo structures
- Support multiple test directories
- Auto-detect test runner from installed packages
- Suggest test organization improvements

---

**Last Updated**: 2025-12-08
**Status**: Phase 1 - Python support implemented
