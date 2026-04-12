# Helper Module Generator

**Purpose**: Create or update shared helper modules from detected patterns, preserving existing helpers and handling errors gracefully.

**Version**: 1.0.0

**Requirements Addressed**: REQ-F-1, REQ-F-2, REQ-F-3, REQ-F-4, REQ-F-5, REQ-F-6, REQ-F-22, REQ-F-23, REQ-NF-1

---

## Overview

The Helper Module Generator creates or updates shared helper modules containing extracted test helper functions. It checks for existing helper modules, parses them to avoid conflicts, and generates language-appropriate code with documentation.

**Key Features**:
- Preserves existing helpers (REQ-F-22)
- Generates language-specific code (REQ-F-6, REQ-NF-1)
- Handles filesystem errors gracefully (REQ-F-23)
- Validates generated code syntax
- Creates helper modules at language-appropriate locations

---

## API Signature

```python
def generate_helper_module(
    patterns: List[PatternMetadata],
    test_directory: str,
    language: str,
    framework: str
) -> Optional[HelperModule]:
    """
    Generate or update helper module from detected patterns.

    Args:
        patterns: List of patterns to extract as helpers
        test_directory: Absolute path to test directory
        language: Programming language (python, javascript, etc.)
        framework: Test framework (pytest, jest, etc.)

    Returns:
        HelperModule object with metadata, or None on failure

    Raises:
        No exceptions - returns None and logs errors on failure
    """
```

---

## Language-Specific Helper Paths

Per TD-2, each language has specific conventions:

| Language | Helper Path | Example |
|----------|-------------|---------|
| Python | `tests/helpers.py` or `tests/helpers/__init__.py` | `/project/tests/helpers.py` |
| JavaScript | `tests/helpers/mockHelpers.js` | `/project/tests/helpers/mockHelpers.js` |
| TypeScript | `tests/helpers/mockHelpers.ts` | `/project/tests/helpers/mockHelpers.ts` |
| Java | `src/test/java/com/company/TestUtils.java` | `/project/src/test/java/TestUtils.java` |
| C# | `TestProject/TestHelpers.cs` | `/project/tests/TestHelpers.cs` |
| Go | `testing_utils_test.go` or `testhelpers/helpers.go` | `/project/testing_utils_test.go` |
| C++ | `tests/test_helpers.h` (with optional `.cpp`) | `/project/tests/test_helpers.h` |
| Rust | `tests/common/mod.rs` | `/project/tests/common/mod.rs` |

---

## Generation Algorithm

### Step 1: Determine Helper Module Path

```python
def get_helper_module_path(test_directory: str, language: str) -> str:
    """Determine where to create/update helper module."""

    if language == "python":
        return os.path.join(test_directory, "helpers.py")

    elif language == "javascript":
        helpers_dir = os.path.join(test_directory, "helpers")
        return os.path.join(helpers_dir, "mockHelpers.js")

    elif language == "typescript":
        helpers_dir = os.path.join(test_directory, "helpers")
        return os.path.join(helpers_dir, "mockHelpers.ts")

    elif language == "java":
        return os.path.join(test_directory, "TestUtils.java")

    elif language == "csharp":
        return os.path.join(test_directory, "TestHelpers.cs")

    elif language == "go":
        return os.path.join(test_directory, "../testing_utils_test.go")

    elif language == "cpp":
        return os.path.join(test_directory, "test_helpers.h")

    elif language == "rust":
        common_dir = os.path.join(test_directory, "common")
        return os.path.join(common_dir, "mod.rs")
```

### Step 2: Check if Helper Module Exists (REQ-F-22)

```python
def check_existing_helpers(helper_path: str, language: str) -> List[str]:
    """Parse existing helper module to find function/class names."""

    if not os.path.exists(helper_path):
        return []  # No existing helpers

    try:
        with open(helper_path, 'r') as f:
            content = f.read()

        existing_helpers = []

        if language == "python":
            # Parse for function definitions
            import re
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            classes = re.findall(r'^class\s+(\w+)\s*[:\(]', content, re.MULTILINE)
            existing_helpers = functions + classes

        elif language in ["javascript", "typescript"]:
            # Parse for function exports
            functions = re.findall(r'export\s+(?:function|const)\s+(\w+)', content)
            existing_helpers = functions

        elif language == "java":
            # Parse for public static methods
            methods = re.findall(r'public\s+static\s+\w+\s+(\w+)\s*\(', content)
            existing_helpers = methods

        elif language == "csharp":
            # Parse for public static methods
            methods = re.findall(r'public\s+static\s+\w+\s+(\w+)\s*\(', content)
            existing_helpers = methods

        # Similar for other languages...

        return existing_helpers

    except Exception as e:
        # Parse error - log warning, return empty (REQ-F-23)
        log_warning(f"Failed to parse existing helpers: {e}")
        return []
```

### Step 3: Filter Conflicting Patterns

```python
def filter_non_conflicting_patterns(
    patterns: List[PatternMetadata],
    existing_helpers: List[str]
) -> List[PatternMetadata]:
    """Remove patterns that conflict with existing helpers."""

    non_conflicting = []
    for pattern in patterns:
        if pattern.name not in existing_helpers:
            non_conflicting.append(pattern)
        else:
            log_info(f"Skipping {pattern.name} - already exists in helper module")

    return non_conflicting
```

### Step 4: Generate Helper Code

Use language-specific templates to generate helper functions:

#### Python Example
```python
def generate_python_helper(pattern: PatternMetadata) -> str:
    """Generate Python helper function from pattern."""

    if pattern.type == "mock_creation":
        return f"""
def {pattern.name}():
    \"\"\"Create and configure a mock API client.\"\"\"
    from unittest.mock import Mock
    mock = Mock()
    # Configure mock based on pattern
    return mock
"""

    elif pattern.type == "test_builder":
        return f"""
def {pattern.name}(**kwargs):
    \"\"\"Build a test user object with default values.\"\"\"
    defaults = {{
        "id": 1,
        "name": "Test User",
        "email": "test@example.com"
    }}
    defaults.update(kwargs)
    return User(**defaults)
"""

    elif pattern.type == "setup_teardown":
        return f"""
@pytest.fixture
def {pattern.name}():
    \"\"\"Setup and teardown database connection.\"\"\"
    db = Database()
    db.connect()
    yield db
    db.disconnect()
"""
```

#### JavaScript Example
```javascript
function generate_javascript_helper(pattern) {
    if (pattern.type === "mock_creation") {
        return `
export function ${pattern.name}() {
    const mock = jest.fn();
    mock.mockReturnValue({ status: 'ok' });
    return mock;
}
`;
    }

    // Similar for other types...
}
```

### Step 5: Create Helper Module File

```python
def create_helper_module(
    helper_path: str,
    language: str,
    new_helpers: List[str],
    existing_content: str = ""
) -> bool:
    """Write helper module to filesystem."""

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(helper_path), exist_ok=True)

        # Generate file header
        header = generate_file_header(language)

        # Combine existing + new helpers
        if existing_content:
            full_content = existing_content + "\n\n" + "\n\n".join(new_helpers)
        else:
            full_content = header + "\n\n" + "\n\n".join(new_helpers)

        # Write to file
        with open(helper_path, 'w') as f:
            f.write(full_content)

        return True

    except (OSError, PermissionError) as e:
        # Filesystem error - log and return False (REQ-F-23)
        log_error(f"Failed to write helper module: {e}")
        return False
```

### Step 6: Validate Generated Code

```python
def validate_helper_syntax(helper_path: str, language: str) -> bool:
    """Validate generated helper code compiles/parses."""

    try:
        with open(helper_path, 'r') as f:
            content = f.read()

        if language == "python":
            import ast
            ast.parse(content)

        elif language in ["javascript", "typescript"]:
            # Could use esprima or similar
            # For now, just check basic syntax patterns
            pass

        return True

    except SyntaxError:
        log_error(f"Generated helper has syntax errors")
        return False
```

---

## Complete Example

```python
from typing import List, Optional

def generate_helper_module(
    patterns: List[PatternMetadata],
    test_directory: str,
    language: str,
    framework: str
) -> Optional[HelperModule]:
    """Generate or update helper module from patterns."""

    # Step 1: Determine helper path
    helper_path = get_helper_module_path(test_directory, language)

    # Step 2: Check existing helpers
    existing_helpers = check_existing_helpers(helper_path, language)

    # Step 3: Filter conflicts (REQ-F-22)
    non_conflicting = filter_non_conflicting_patterns(patterns, existing_helpers)

    if not non_conflicting:
        # All patterns already exist
        return HelperModule(
            file_path=helper_path,
            language=language,
            framework=framework,
            existing_helpers=existing_helpers,
            generated_helpers=[],
            imports=[]
        )

    # Step 4: Generate helper code
    new_helper_code = []
    generated_names = []
    all_imports = set()

    for pattern in non_conflicting:
        helper_code = generate_helper_code(pattern, language, framework)
        new_helper_code.append(helper_code)
        generated_names.append(pattern.name)
        all_imports.update(pattern.dependencies)

    # Step 5: Create/update file
    existing_content = ""
    if os.path.exists(helper_path):
        with open(helper_path, 'r') as f:
            existing_content = f.read()

    success = create_helper_module(
        helper_path,
        language,
        new_helper_code,
        existing_content
    )

    if not success:
        # Filesystem error (REQ-F-23)
        return None

    # Step 6: Validate syntax
    if not validate_helper_syntax(helper_path, language):
        # Syntax error - rollback
        if existing_content:
            with open(helper_path, 'w') as f:
                f.write(existing_content)
        return None

    # Success!
    return HelperModule(
        file_path=helper_path,
        language=language,
        framework=framework,
        existing_helpers=existing_helpers,
        generated_helpers=generated_names,
        imports=list(all_imports)
    )
```

---

## Error Handling (REQ-F-23)

All errors are handled gracefully:

1. **Filesystem Permission Error**:
   ```python
   try:
       with open(helper_path, 'w') as f:
           f.write(content)
   except PermissionError as e:
       log_error(f"Permission denied writing helper module: {e}")
       return None  # Continue with inline helpers
   ```

2. **Disk Full**:
   ```python
   except OSError as e:
       log_error(f"Filesystem error: {e}")
       return None
   ```

3. **Parse Error on Existing Helpers**:
   ```python
   try:
       existing = check_existing_helpers(path, language)
   except Exception as e:
       log_warning(f"Could not parse existing helpers: {e}")
       existing = []  # Assume no existing helpers, proceed
   ```

4. **Syntax Error in Generated Code**:
   ```python
   if not validate_helper_syntax(helper_path, language):
       # Rollback to previous version
       restore_from_backup(helper_path)
       return None
   ```

---

## Integration with Write-Agent

```python
# In write-agent Step 5

# After pattern detection
patterns = detect_helper_patterns(test_code, language, framework)

if patterns:
    # Generate helper module
    helper_module = generate_helper_module(
        patterns, test_directory, language, framework
    )

    if helper_module:
        # Success - proceed with import injection
        log_info(f"Generated helper module: {helper_module.file_path}")
        log_info(f"New helpers: {helper_module.generated_helpers}")
    else:
        # Failed - fall back to inline helpers (REQ-F-23)
        log_warning("Helper generation failed, using inline helpers")
        helper_module = None
else:
    # No patterns detected
    helper_module = None
```

---

## Testing Requirements

Unit tests must verify:

1. **Path determination**: Correct path for each language
2. **Existing helper detection**: Parses existing files correctly
3. **Conflict avoidance**: Skips helpers that already exist (REQ-F-22)
4. **Code generation**: Generates valid code for each pattern type
5. **File creation**: Creates directories and files correctly
6. **Error handling**: Gracefully handles all error scenarios (REQ-F-23)
7. **Syntax validation**: Validates generated code
8. **Rollback**: Restores previous version on error

Test file: `tests/unit/test_helper_generator.py`
