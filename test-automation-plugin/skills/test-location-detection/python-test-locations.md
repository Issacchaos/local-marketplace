# Python Test Location Detection

**Language**: Python
**Frameworks**: pytest, unittest
**Version**: 1.0.0

---

## Overview

Python test location conventions vary by framework (pytest vs unittest) and project structure. This document provides specific guidance for determining correct test file locations in Python projects.

---

## Configuration Sources (Priority Order)

### 1. pytest.ini
```ini
[pytest]
testpaths = tests integration
python_files = test_*.py *_test.py
```

**Priority**: Highest
**Location**: Project root
**Test Path**: Use `testpaths` value
**File Pattern**: Use `python_files` value (default: `test_*.py`)

---

### 2. pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["tests", "integration"]
python_files = ["test_*.py", "*_test.py"]
```

**Priority**: High
**Location**: Project root
**Test Path**: Use `testpaths` array
**File Pattern**: Use `python_files` array

---

### 3. setup.cfg
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
```

**Priority**: Medium
**Location**: Project root
**Test Path**: Use `testpaths` value
**File Pattern**: Use `python_files` value

---

### 4. tox.ini
```ini
[pytest]
testpaths = tests
```

**Priority**: Low
**Location**: Project root
**Test Path**: Use `testpaths` value

---

## Default Conventions

If no configuration found, use these defaults:

### pytest Default
- **Test directory**: `tests/` at project root
- **File naming**: `test_*.py` (prefix) or `*_test.py` (suffix)
- **Structure**: Mirror source directory structure

```
project/
├── src/
│   ├── calculator.py
│   └── utils/
│       └── math_helpers.py
└── tests/
    ├── test_calculator.py
    └── utils/
        └── test_math_helpers.py
```

---

### unittest Default
- **Test directory**: `tests/` at project root
- **File naming**: `test_*.py` (prefix only)
- **Structure**: Can be flat or mirrored

```
project/
├── calculator.py
├── utils.py
└── tests/
    ├── test_calculator.py
    └── test_utils.py
```

---

## Common Project Structures

### Structure 1: src/ Layout (Most Recommended)

```
myproject/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── calculator.py
│       └── api/
│           └── endpoints.py
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py
│   └── api/
│       └── test_endpoints.py
├── pytest.ini
└── pyproject.toml
```

**Test Path Resolution**:
- Source: `src/mypackage/calculator.py`
- Test: `tests/test_calculator.py`

**Test Path Resolution (nested)**:
- Source: `src/mypackage/api/endpoints.py`
- Test: `tests/api/test_endpoints.py`

---

### Structure 2: Flat Package Layout

```
myproject/
├── mypackage/
│   ├── __init__.py
│   ├── calculator.py
│   └── api/
│       └── endpoints.py
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py
│   └── api/
│       └── test_endpoints.py
└── pytest.ini
```

**Test Path Resolution**:
- Source: `mypackage/calculator.py`
- Test: `tests/test_calculator.py`

---

### Structure 3: Tests Alongside Source (Less Common)

```
myproject/
└── mypackage/
    ├── __init__.py
    ├── calculator.py
    ├── test_calculator.py
    └── api/
        ├── endpoints.py
        └── test_endpoints.py
```

**Test Path Resolution**:
- Source: `mypackage/calculator.py`
- Test: `mypackage/test_calculator.py` (same directory)

**Note**: This structure is less common and can pollute the package namespace. Use only if project already follows this pattern.

---

### Structure 4: Django Project

```
myproject/
├── myapp/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_views.py
├── manage.py
└── pytest.ini
```

**Test Path Resolution**:
- Source: `myapp/models.py`
- Test: `myapp/tests/test_models.py`

**Note**: Django uses app-specific test directories.

---

## Path Resolution Algorithm

### Input
- Source file: `/home/user/project/src/mypackage/calculator.py`
- Project root: `/home/user/project/`
- Framework: `pytest`

### Step 1: Read Configuration
Check for pytest.ini:
```ini
[pytest]
testpaths = tests
```

Result: Test directory = `tests/`

### Step 2: Determine Source Root
- Check for `src/` directory → Source root = `src/`
- If no `src/` → Source root = project root

Result: Source root = `src/`

### Step 3: Calculate Relative Path
- Full source path: `/home/user/project/src/mypackage/calculator.py`
- Remove source root: `mypackage/calculator.py`
- Remove filename: `mypackage/`

Result: Relative directory = `mypackage/`

### Step 4: Apply Naming Convention
- Get filename: `calculator.py`
- Remove extension: `calculator`
- Apply pattern: `test_{name}.py`

Result: Test filename = `test_calculator.py`

### Step 5: Construct Test Path
- Project root: `/home/user/project/`
- Test directory: `tests/`
- Relative directory: `mypackage/`
- Test filename: `test_calculator.py`

**Final Test Path**: `/home/user/project/tests/mypackage/test_calculator.py`

---

## Edge Cases

### Case 1: No src/ Directory

**Source**: `/home/user/project/calculator.py`

**Resolution**:
- Source root = project root
- Relative path = `` (empty, file at root)
- Test path = `/home/user/project/tests/test_calculator.py`

---

### Case 2: Multiple Source Directories

**Project Structure**:
```
project/
├── app/
│   └── calculator.py
├── lib/
│   └── utils.py
└── tests/
```

**Source**: `/home/user/project/app/calculator.py`

**Resolution**:
- Source root = project root (no src/)
- Relative path = `app/`
- Test path = `/home/user/project/tests/app/test_calculator.py`

---

### Case 3: __init__.py Files

**Source**: `/home/user/project/src/mypackage/__init__.py`

**Resolution**:
- Treat `__init__.py` as a module
- Test path = `/home/user/project/tests/mypackage/test___init__.py`
- Alternative: `tests/mypackage/test_package.py` (more readable)

---

### Case 4: Private Modules

**Source**: `/home/user/project/src/mypackage/_internal.py`

**Resolution**:
- Preserve underscore prefix in directory but not test file
- Test path = `/home/user/project/tests/mypackage/test_internal.py`
- Reason: Test files should not be considered private

---

## File Naming Patterns

### pytest Patterns

**Supported**:
- `test_*.py` - Prefix (most common)
- `*_test.py` - Suffix (also supported)

**Examples**:
- `test_calculator.py` ✅ (recommended)
- `calculator_test.py` ✅ (valid)
- `test_calculator_unit.py` ✅ (with descriptor)
- `calculator_tests.py` ❌ (tests vs test)
- `Calculator_test.py` ❌ (capital letter)

**Recommendation**: Use `test_*.py` prefix for consistency.

---

### unittest Patterns

**Supported**:
- `test_*.py` - Prefix only

**Examples**:
- `test_calculator.py` ✅
- `test_utils.py` ✅
- `calculator_test.py` ❌ (unittest doesn't discover suffix pattern by default)

---

## Special Considerations

### Integration Tests

**Separate Directory**:
```
project/
├── tests/
│   └── unit/
│       └── test_calculator.py
└── integration/
    └── test_api_integration.py
```

**Configuration**:
```ini
[pytest]
testpaths = tests integration
```

---

### Conftest Files

**Purpose**: Shared fixtures and configuration

**Location**: At test directory root or subdirectories

```
tests/
├── conftest.py          # Shared fixtures for all tests
├── test_calculator.py
└── api/
    ├── conftest.py      # Fixtures specific to api tests
    └── test_endpoints.py
```

**Not Considered Tests**: `conftest.py` files are not test files.

---

### __init__.py in Tests

**Purpose**: Make tests directory a package (optional in pytest)

**When Needed**:
- Importing from `tests/` directory
- Sharing test utilities
- Python 2 compatibility (rare)

**Modern pytest**: Not required, pytest discovers tests without `__init__.py`

```
tests/
├── __init__.py          # Optional
├── test_calculator.py
└── utils.py            # Test utilities (if __init__.py present)
```

---

## Validation Rules

### ✅ Valid Locations
- `tests/test_calculator.py`
- `tests/unit/test_calculator.py`
- `integration/test_integration.py` (if configured)
- `src/mypackage/test_calculator.py` (if existing pattern)
- `mypackage/tests/test_module.py` (Django style)

### 🚫 Invalid Locations
- `.claude-tests/test_calculator.py` ❌
- `.claude/test_calculator.py` ❌
- `/tmp/test_calculator.py` ❌
- `~/.cache/test_calculator.py` ❌
- `test_calculator.py` at project root ❌ (should be in tests/)

---

## Tool Integration

### Write Agent Integration

```python
# Pseudocode for Write Agent

def determine_test_path(source_file, project_root):
    # Step 1: Read pytest.ini or pyproject.toml
    config = read_pytest_config(project_root)
    test_directory = config.get('testpaths', ['tests'])[0]

    # Step 2: Determine source root
    if exists(join(project_root, 'src')):
        source_root = join(project_root, 'src')
    else:
        source_root = project_root

    # Step 3: Calculate relative path
    relative_path = source_file.relative_to(source_root).parent

    # Step 4: Apply naming convention
    source_filename = source_file.stem  # 'calculator' from 'calculator.py'
    test_filename = f'test_{source_filename}.py'

    # Step 5: Construct test path
    test_path = project_root / test_directory / relative_path / test_filename

    # Step 6: Validate
    assert '.claude-tests' not in str(test_path), "Invalid test location"
    assert '.claude' not in str(test_path), "Invalid test location"

    return test_path
```

---

## Examples

### Example 1: Simple Project

**Input**:
- Source: `/home/user/myproject/calculator.py`
- Project root: `/home/user/myproject/`
- Config: `pytest.ini` with `testpaths = tests`

**Output**:
- Test: `/home/user/myproject/tests/test_calculator.py`

---

### Example 2: src/ Layout

**Input**:
- Source: `/home/user/myproject/src/mypackage/calculator.py`
- Project root: `/home/user/myproject/`
- Config: `pytest.ini` with `testpaths = tests`

**Output**:
- Test: `/home/user/myproject/tests/mypackage/test_calculator.py`

---

### Example 3: Nested Module

**Input**:
- Source: `/home/user/myproject/src/mypackage/utils/math_helpers.py`
- Project root: `/home/user/myproject/`
- Config: `pytest.ini` with `testpaths = tests`

**Output**:
- Test: `/home/user/myproject/tests/mypackage/utils/test_math_helpers.py`

---

### Example 4: Django App

**Input**:
- Source: `/home/user/myproject/myapp/models.py`
- Project root: `/home/user/myproject/`
- Existing pattern: Django style (tests/ within app)

**Output**:
- Test: `/home/user/myproject/myapp/tests/test_models.py`

---

## Summary

**Key Principles**:
1. Always check configuration first (pytest.ini, pyproject.toml)
2. Default to `tests/` directory if no config
3. Mirror source directory structure in tests
4. Use `test_*.py` naming convention
5. **NEVER use `.claude-tests/` or temporary directories**
6. Create test directories if they don't exist

**Priority Order**:
1. pytest.ini `testpaths`
2. pyproject.toml `[tool.pytest.ini_options] testpaths`
3. setup.cfg `[tool:pytest] testpaths`
4. Existing test directory structure
5. Default: `tests/` at project root

---

**Last Updated**: 2025-12-08
**Status**: Phase 1 - Implemented and validated
