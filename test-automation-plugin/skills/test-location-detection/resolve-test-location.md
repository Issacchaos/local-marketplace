# Test Location Resolution Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++
**Purpose**: Resolve where to write test files using standard, discoverable locations per language conventions

---

## Overview

The Test Location Resolution Skill determines the correct directory and file path for generated test files. It uses standard test locations recognized by framework test runners (pytest, jest, JUnit, etc.) instead of temporary directories.

**Key Principles**:
1. **Use standard locations** - tests/, __tests__/, src/test/java/, etc.
2. **Never use .claude-tests/** - Temporary directory not recognized by test runners
3. **Check existing structure** - Use existing test directories if present
4. **Create if needed** - Create standard test directory if none exists
5. **Validate safety** - Ensure location is within project, not plugin repo

---

## Resolution Algorithm

### Step 1: Get Project Root

**Input Required**:
- `project_root`: From Project Root Detection Skill (TASK-001)
- `language`: Detected language (python, javascript, java, etc.)
- `framework`: Detected framework (pytest, jest, junit, etc.) - optional
- `source_file`: Path to source file being tested

**Pre-condition**: Project root must already be detected and validated.

---

### Step 2: Determine Standard Test Locations by Language

```python
STANDARD_TEST_LOCATIONS = {
    # Python
    'python': {
        'primary': ['tests/', 'test/'],
        'config_files': ['pytest.ini', 'pyproject.toml', 'setup.cfg'],
        'config_keys': {
            'pytest.ini': '[pytest] testpaths',
            'pyproject.toml': '[tool.pytest.ini_options] testpaths',
            'setup.cfg': '[tool:pytest] testpaths'
        },
        'test_file_pattern': 'test_{source_name}.py',
        'alongside_source': False  # Python tests usually in separate directory
    },

    # JavaScript
    'javascript': {
        'primary': ['tests/', 'test/', '__tests__/'],
        'config_files': ['package.json', 'jest.config.js', 'jest.config.json'],
        'config_keys': {
            'package.json': 'jest.testMatch',
            'jest.config.js': 'testMatch'
        },
        'test_file_pattern': '{source_name}.test.js',
        'alongside_source': True,  # JS tests can be alongside source
        # Note: Social Overlay pattern supported - mixed locations OK
        # - Unit tests for components: alongside source (src/Button.test.js)
        # - E2E/perf tests: separate directory (tests/e2e/, tests/perf/)
        'supports_mixed_locations': True
    },

    # TypeScript
    'typescript': {
        'primary': ['tests/', 'test/', '__tests__/', 'src/__tests__/'],
        'config_files': ['package.json', 'jest.config.ts', 'vitest.config.ts'],
        'config_keys': {
            'package.json': 'jest.testMatch',
            'vitest.config.ts': 'test.include'
        },
        'test_file_pattern': '{source_name}.test.ts',
        'alongside_source': True,  # TS tests can be alongside source
        # Note: Social Overlay pattern supported - mixed locations OK
        # - Unit tests for components: alongside source (src/Button.test.ts)
        # - E2E/perf tests: separate directory (tests/e2e/, tests/perf/)
        'supports_mixed_locations': True
    },

    # Java
    'java': {
        'primary': ['src/test/java/'],
        'config_files': ['pom.xml', 'build.gradle'],
        'config_keys': {
            'pom.xml': '<testSourceDirectory>',
            'build.gradle': 'sourceSets.test.java.srcDirs'
        },
        'test_file_pattern': '{source_name}Test.java',
        'alongside_source': False,  # Separate src/test tree
        'mirror_package': True  # Must mirror src/main/java package structure
    },

    # C#
    'csharp': {
        'primary': ['Tests/', 'tests/', '{ProjectName}.Tests/', '{ProjectName}.UnitTests/', '{ProjectName}.IntegrationTests/'],
        'config_files': ['*.csproj', '*.sln'],
        'test_file_pattern': '{source_name}Tests.cs',
        'alongside_source': False,  # Usually separate test project
        'separate_project': True,  # Often in separate .csproj
        'test_project_patterns': [
            r'.*\.Tests$',           # ProjectName.Tests
            r'.*\.UnitTests$',       # ProjectName.UnitTests
            r'.*\.IntegrationTests$',# ProjectName.IntegrationTests
            r'.*\.FunctionalTests$', # ProjectName.FunctionalTests
            r'.*\.E2ETests$',        # ProjectName.E2ETests
            r'^Tests$'               # Just "Tests"
        ]
    },

    # Go
    'go': {
        'primary': [''],  # Same directory as source
        'config_files': ['go.mod'],
        'test_file_pattern': '{source_name}_test.go',
        'alongside_source': True,  # Go convention: tests alongside source
        'same_directory_required': True
    },

    # C++
    'cpp': {
        'primary': ['tests/', 'test/', 'Tests/'],
        'config_files': ['CMakeLists.txt', 'Makefile'],
        'test_file_pattern': 'test_{source_name}.cpp',
        'alongside_source': False
    }
}
```

---

### Step 3: Check for Existing Test Directory

```python
import re

def find_existing_test_directory(
    project_root: str,
    language: str
) -> str | None:
    """
    Check if project already has a test directory.

    Args:
        project_root: Absolute path to project root
        language: Language (python, javascript, etc.)

    Returns:
        Absolute path to existing test directory, or None
    """
    locations = STANDARD_TEST_LOCATIONS[language]['primary']

    # First, check exact matches from primary locations
    for location in locations:
        # Skip template placeholders (they'll be handled by regex)
        if '{' in location:
            continue
        test_dir = os.path.join(project_root, location)
        if os.path.exists(test_dir) and os.path.isdir(test_dir):
            return test_dir

    # For C#: Check for pattern-based test projects (e.g., MyProject.UnitTests)
    if language == 'csharp' and 'test_project_patterns' in STANDARD_TEST_LOCATIONS[language]:
        patterns = STANDARD_TEST_LOCATIONS[language]['test_project_patterns']

        # List all directories in project root
        try:
            for item in os.listdir(project_root):
                item_path = os.path.join(project_root, item)
                if os.path.isdir(item_path):
                    # Check if directory matches any test project pattern
                    for pattern in patterns:
                        if re.match(pattern, item):
                            return item_path
        except (OSError, PermissionError):
            pass

    return None
```

---

### Step 4: Read Framework Configuration (Optional)

```python
def read_test_config(project_root: str, language: str) -> str | None:
    """
    Read test location from framework configuration files.

    Args:
        project_root: Project root path
        language: Language

    Returns:
        Configured test path relative to project root, or None
    """
    config_info = STANDARD_TEST_LOCATIONS[language]
    config_files = config_info.get('config_files', [])
    config_keys = config_info.get('config_keys', {})

    for config_file in config_files:
        config_path = os.path.join(project_root, config_file)

        if not os.path.exists(config_path):
            continue

        # Read configuration
        if config_file == 'pytest.ini':
            test_path = read_pytest_ini(config_path, config_keys['pytest.ini'])
            if test_path:
                return test_path

        elif config_file == 'pyproject.toml':
            test_path = read_pyproject_toml(config_path, config_keys['pyproject.toml'])
            if test_path:
                return test_path

        elif config_file == 'package.json':
            test_path = read_package_json(config_path, config_keys['package.json'])
            if test_path:
                return test_path

        # Add other config readers as needed

    return None


def read_pytest_ini(config_path: str, key: str) -> str | None:
    """Read testpaths from pytest.ini"""
    # Implementation: Parse INI file, extract testpaths
    # Example: testpaths = tests
    pass


def read_pyproject_toml(config_path: str, key: str) -> str | None:
    """Read testpaths from pyproject.toml"""
    # Implementation: Parse TOML file, extract tool.pytest.ini_options.testpaths
    # Example: testpaths = ["tests", "integration"]
    pass


def read_package_json(config_path: str, key: str) -> str | None:
    """Read jest.testMatch from package.json"""
    # Implementation: Parse JSON, extract jest.testMatch
    # Example: "testMatch": ["**/__tests__/**/*.js"]
    pass
```

---

### Step 5: Resolve Test Directory

```python
def resolve_test_directory(
    project_root: str,
    language: str,
    framework: str = None
) -> dict:
    """
    Resolve where to write test files.

    Args:
        project_root: Absolute path to project root (from TASK-001)
        language: Detected language
        framework: Detected framework (optional)

    Returns:
        dict with:
        {
            'test_directory': str,          # Absolute path to test directory
            'source': str,                  # How it was determined
            'create_required': bool,        # Whether directory needs to be created
            'error': str | None
        }
    """
    # Step 1: Check for configured location
    configured_path = read_test_config(project_root, language)
    if configured_path:
        test_dir = os.path.join(project_root, configured_path)
        return {
            'test_directory': test_dir,
            'source': 'configuration',
            'create_required': not os.path.exists(test_dir),
            'error': None
        }

    # Step 2: Check for existing test directory
    existing_dir = find_existing_test_directory(project_root, language)
    if existing_dir:
        return {
            'test_directory': existing_dir,
            'source': 'existing',
            'create_required': False,
            'error': None
        }

    # Step 3: Use default standard location
    locations = STANDARD_TEST_LOCATIONS[language]['primary']
    default_location = locations[0]  # First is most common

    test_dir = os.path.join(project_root, default_location)

    return {
        'test_directory': test_dir,
        'source': 'default',
        'create_required': True,
        'error': None
    }
```

---

### Step 6: Resolve Test File Path

```python
def resolve_test_file_path(
    test_directory: str,
    source_file: str,
    language: str,
    project_root: str
) -> str:
    """
    Resolve full path to test file for a source file.

    Args:
        test_directory: Test directory from resolve_test_directory()
        source_file: Absolute path to source file being tested
        language: Language
        project_root: Project root

    Returns:
        Absolute path to test file
    """
    # Get source file name without extension
    source_name = os.path.splitext(os.path.basename(source_file))[0]

    # Get test file naming pattern
    pattern = STANDARD_TEST_LOCATIONS[language]['test_file_pattern']
    test_filename = pattern.format(source_name=source_name)

    # Handle language-specific path resolution
    if language == 'java':
        # Java: Mirror package structure from src/main/java to src/test/java
        return resolve_java_test_path(source_file, test_directory, test_filename, project_root)

    elif language == 'go':
        # Go: Same directory as source file
        source_dir = os.path.dirname(source_file)
        return os.path.join(source_dir, test_filename)

    elif language == 'csharp':
        # C#: May need to resolve test project path
        return resolve_csharp_test_path(source_file, test_directory, test_filename, project_root)

    else:
        # Python, JS, TS, C++: Test file in test directory
        # Optionally mirror source subdirectory structure
        if should_mirror_structure(language, source_file, project_root):
            relative_path = get_relative_source_path(source_file, project_root)
            test_file = os.path.join(test_directory, relative_path, test_filename)
        else:
            test_file = os.path.join(test_directory, test_filename)

        return test_file


def resolve_java_test_path(
    source_file: str,
    test_directory: str,
    test_filename: str,
    project_root: str
) -> str:
    """
    Resolve Java test path mirroring package structure.

    Example:
    Source: /project/src/main/java/com/example/Calculator.java
    Test:   /project/src/test/java/com/example/CalculatorTest.java
    """
    # Extract package path from source file
    # Assumption: Source is in src/main/java/package/path/File.java
    src_main_java = os.path.join(project_root, 'src', 'main', 'java')

    if source_file.startswith(src_main_java):
        # Get package path relative to src/main/java
        package_path = os.path.relpath(os.path.dirname(source_file), src_main_java)

        # Build test path: src/test/java/package/path/FileTest.java
        test_file = os.path.join(test_directory, package_path, test_filename)
        return test_file
    else:
        # Source not in standard location, use flat structure
        return os.path.join(test_directory, test_filename)


def resolve_csharp_test_path(
    source_file: str,
    test_directory: str,
    test_filename: str,
    project_root: str
) -> str:
    """
    Resolve C# test path.

    C# tests are typically in separate test project:
    /MyApp/MyApp.csproj
    /MyApp.Tests/MyApp.Tests.csproj
    """
    # For now, simple implementation: tests in test_directory
    return os.path.join(test_directory, test_filename)


def should_mirror_structure(language: str, source_file: str, project_root: str) -> bool:
    """Determine if test structure should mirror source structure."""
    # Python/JS/TS: Mirror if source has subdirectories
    # Example: src/utils/math.py → tests/utils/test_math.py

    source_dir = os.path.dirname(source_file)
    relative_to_project = os.path.relpath(source_dir, project_root)

    # If source is in subdirectory (not root), consider mirroring
    if relative_to_project != '.' and not relative_to_project.startswith('..'):
        # Check depth: mirror if >= 2 levels deep
        depth = len(relative_to_project.split(os.sep))
        return depth >= 2

    return False


def get_relative_source_path(source_file: str, project_root: str) -> str:
    """
    Get relative path of source file's directory from project root.

    Example:
    source_file: /project/src/utils/math.py
    project_root: /project
    Returns: src/utils
    """
    source_dir = os.path.dirname(source_file)
    return os.path.relpath(source_dir, project_root)
```

---

### Step 7: Validate Test Location

```python
def validate_test_location(
    test_path: str,
    project_root: str,
    plugin_repo_path: str = None
) -> dict:
    """
    Validate that test location is safe to write to.

    Validation Rules:
    1. Test path must be inside project root
    2. Test path must NOT be inside plugin repository
    3. Test path must NOT be in .claude/ directory
    4. Test path must NOT be in .claude-tests/ (temporary)
    5. Parent directory must be writable

    Args:
        test_path: Resolved test file path
        project_root: Project root
        plugin_repo_path: Plugin repository path

    Returns:
        dict with:
        {
            'valid': bool,
            'error': str | None,
            'suggestion': str | None
        }
    """
    test_path_abs = os.path.abspath(test_path)
    project_root_abs = os.path.abspath(project_root)

    # Rule 1: Must be inside project root
    if not test_path_abs.startswith(project_root_abs):
        return {
            'valid': False,
            'error': f"Test location {test_path_abs} is outside project root {project_root_abs}",
            'suggestion': "Internal error - test resolution should always be within project."
        }

    # Rule 2: Must NOT be in plugin repository
    if plugin_repo_path:
        plugin_repo_abs = os.path.abspath(plugin_repo_path)
        if test_path_abs.startswith(plugin_repo_abs):
            return {
                'valid': False,
                'error': (
                    f"Cannot write tests to plugin repository.\\n"
                    f"Test path: {test_path_abs}\\n"
                    f"Plugin repo: {plugin_repo_abs}\\n"
                    f"Project root: {project_root_abs}"
                ),
                'suggestion': "This should never happen - check project root detection."
            }

    # Rule 3: Must NOT be in .claude/ directory
    if '.claude' + os.sep in test_path_abs or test_path_abs.endswith('.claude'):
        return {
            'valid': False,
            'error': f"Cannot write tests to .claude/ directory: {test_path_abs}",
            'suggestion': ".claude/ is reserved for state files, not test files."
        }

    # Rule 4: Must NOT be in .claude-tests/ (old temporary location)
    if '.claude-tests' in test_path_abs:
        # Extract just the standard location part
        standard_location = test_path_abs.replace('.claude-tests', 'tests')
        return {
            'valid': False,
            'error': (
                f"Cannot write tests to temporary directory .claude-tests/\\n"
                f"Test path: {test_path_abs}"
            ),
            'suggestion': f"Tests must be in standard location: {standard_location}"
        }

    # Rule 5: Parent directory must be writable (or creatable)
    test_dir = os.path.dirname(test_path_abs)
    if os.path.exists(test_dir):
        # Directory exists - check if writable
        if not os.access(test_dir, os.W_OK):
            return {
                'valid': False,
                'error': f"Test directory is not writable: {test_dir}",
                'suggestion': "Check directory permissions."
            }
    else:
        # Directory doesn't exist - check if parent is writable (so we can create it)
        parent_dir = os.path.dirname(test_dir)
        if os.path.exists(parent_dir) and not os.access(parent_dir, os.W_OK):
            return {
                'valid': False,
                'error': f"Cannot create test directory (parent not writable): {parent_dir}",
                'suggestion': "Check directory permissions."
            }

    # All validations passed
    return {
        'valid': True,
        'error': None,
        'suggestion': None
    }
```

---

### Step 8: Create Test Directory (If Needed)

```python
def ensure_test_directory(test_directory: str) -> dict:
    """
    Create test directory if it doesn't exist.

    Args:
        test_directory: Test directory path

    Returns:
        dict with:
        {
            'success': bool,
            'created': bool,  # True if directory was created
            'error': str | None
        }
    """
    if os.path.exists(test_directory):
        # Directory already exists
        return {
            'success': True,
            'created': False,
            'error': None
        }

    try:
        # Create directory and any necessary parent directories
        os.makedirs(test_directory, exist_ok=True)

        return {
            'success': True,
            'created': True,
            'error': None
        }
    except (OSError, PermissionError) as e:
        return {
            'success': False,
            'created': False,
            'error': f"Failed to create test directory {test_directory}: {e}"
        }
```

---

## Complete Workflow Example

```python
def resolve_test_location_complete(
    target_path: str,
    language: str,
    framework: str = None,
    project_root: str = None,
    plugin_repo_path: str = None
) -> dict:
    """
    Complete workflow: Resolve test location for a source file.

    Args:
        target_path: Source file to test
        language: Detected language
        framework: Detected framework (optional)
        project_root: Project root (from TASK-001)
        plugin_repo_path: Plugin repository path

    Returns:
        dict with:
        {
            'test_file_path': str | None,    # Full path to test file
            'test_directory': str | None,    # Test directory
            'source': str,                   # How location was determined
            'create_required': bool,         # Whether directory needs creation
            'valid': bool,                   # Whether location passed validation
            'error': str | None
        }
    """
    # Step 1: Resolve test directory
    dir_result = resolve_test_directory(project_root, language, framework)

    if dir_result['error']:
        return {
            'test_file_path': None,
            'test_directory': None,
            'source': None,
            'create_required': False,
            'valid': False,
            'error': dir_result['error']
        }

    test_directory = dir_result['test_directory']

    # Step 2: Resolve test file path
    test_file_path = resolve_test_file_path(
        test_directory,
        target_path,
        language,
        project_root
    )

    # Step 3: Validate test location
    validation = validate_test_location(
        test_file_path,
        project_root,
        plugin_repo_path
    )

    if not validation['valid']:
        return {
            'test_file_path': None,
            'test_directory': None,
            'source': dir_result['source'],
            'create_required': False,
            'valid': False,
            'error': validation['error']
        }

    # Step 4: Create directory if needed
    if dir_result['create_required']:
        create_result = ensure_test_directory(test_directory)
        if not create_result['success']:
            return {
                'test_file_path': None,
                'test_directory': None,
                'source': dir_result['source'],
                'create_required': True,
                'valid': False,
                'error': create_result['error']
            }

    # Success!
    return {
        'test_file_path': test_file_path,
        'test_directory': test_directory,
        'source': dir_result['source'],
        'create_required': dir_result['create_required'],
        'valid': True,
        'error': None
    }
```

---

## Usage Examples (Cross-Language)

### Python Example

```python
# Input
target_path = "/home/user/myproject/src/calculator.py"
language = "python"
project_root = "/home/user/myproject"  # From TASK-001

# Output
{
    'test_file_path': '/home/user/myproject/tests/test_calculator.py',
    'test_directory': '/home/user/myproject/tests',
    'source': 'default',  # Created if no tests/ directory exists
    'create_required': True,
    'valid': True,
    'error': None
}
```

### JavaScript Example

```python
# Input
target_path = "/home/user/webapp/src/components/Button.js"
language = "javascript"
project_root = "/home/user/webapp"

# Output (with existing __tests__ directory)
{
    'test_file_path': '/home/user/webapp/__tests__/Button.test.js',
    'test_directory': '/home/user/webapp/__tests__',
    'source': 'existing',
    'create_required': False,
    'valid': True,
    'error': None
}
```

### Java Example

```python
# Input
target_path = "/home/user/javaapp/src/main/java/com/example/Calculator.java"
language = "java"
project_root = "/home/user/javaapp"

# Output
{
    'test_file_path': '/home/user/javaapp/src/test/java/com/example/CalculatorTest.java',
    'test_directory': '/home/user/javaapp/src/test/java',
    'source': 'default',
    'create_required': True,
    'valid': True,
    'error': None
}
```

### Go Example

```python
# Input
target_path = "/home/user/gocalc/calculator.go"
language = "go"
project_root = "/home/user/gocalc"

# Output (Go tests alongside source)
{
    'test_file_path': '/home/user/gocalc/calculator_test.go',
    'test_directory': '/home/user/gocalc',  # Same as source directory
    'source': 'default',
    'create_required': False,  # Directory already exists (source directory)
    'valid': True,
    'error': None
}
```

### C# Example

```python
# Input
target_path = "/home/user/MyApp/MyApp/Calculator.cs"
language = "csharp"
project_root = "/home/user/MyApp"

# Output
{
    'test_file_path': '/home/user/MyApp/Tests/CalculatorTests.cs',
    'test_directory': '/home/user/MyApp/Tests',
    'source': 'default',
    'create_required': True,
    'valid': True,
    'error': None
}
```

### TypeScript Example

```python
# Input
target_path = "/home/user/tsapp/src/utils/math.ts"
language = "typescript"
project_root = "/home/user/tsapp"

# Output (with configured location in package.json)
{
    'test_file_path': '/home/user/tsapp/src/__tests__/utils/math.test.ts',
    'test_directory': '/home/user/tsapp/src/__tests__',
    'source': 'configuration',  # Read from package.json
    'create_required': False,
    'valid': True,
    'error': None
}
```

### C++ Example

```python
# Input
target_path = "/home/user/cppapp/src/calculator.cpp"
language = "cpp"
project_root = "/home/user/cppapp"

# Output
{
    'test_file_path': '/home/user/cppapp/tests/test_calculator.cpp',
    'test_directory': '/home/user/cppapp/tests',
    'source': 'default',
    'create_required': True,
    'valid': True,
    'error': None
}
```

---

## Integration with Other Components

### Inputs (from other skills):
- `project_root` - From Project Root Detection Skill (TASK-001)
- `language` - From Framework Detection Skill
- `framework` - From Framework Detection Skill
- `plugin_repo_path` - From Orchestrator environment

### Outputs (to other components):
- `test_file_path` - Full path where test should be written
- `test_directory` - Directory to create if needed
- `validation_result` - Safety checks passed

### Used By:
- Write Agent (Step 3: Generate Test Structure)
- Test Loop Orchestrator (Phase 2: Planning)

---

## Testing Checklist (TASK-002 Acceptance)

- [ ] Resolves Python test location (tests/test_*.py)
- [ ] Resolves JavaScript test location (__tests__/*.test.js)
- [ ] Resolves TypeScript test location (*.test.ts)
- [ ] Resolves Java test location (src/test/java/.../Test.java)
- [ ] Resolves C# test location (Tests/*Tests.cs)
- [ ] Resolves Go test location (*_test.go alongside source)
- [ ] Resolves C++ test location (tests/test_*.cpp)
- [ ] Uses existing test directory if present
- [ ] Reads configuration files (pytest.ini, package.json, pom.xml)
- [ ] Creates test directory if needed
- [ ] Mirrors package structure for Java
- [ ] Validates test path is inside project
- [ ] Rejects .claude-tests/ paths
- [ ] Rejects .claude/ paths
- [ ] Rejects plugin repository paths
- [ ] Handles Windows paths correctly
- [ ] Handles nested source directories

---

## Mixed Test Locations (Future Enhancement)

**Pattern**: Some projects (e.g., Social Overlay) use **mixed test locations** depending on test type:
- **Unit tests**: Alongside source files (`src/Button.test.ts`)
- **Integration tests**: Separate directory (`tests/integration/`)
- **E2E tests**: Separate directory (`tests/e2e/`)
- **Performance tests**: Separate directory (`tests/perf/`)

### Current Behavior (v1.0.0)

The current implementation supports `alongside_source: True` for JS/TS, which means:
- ✅ Tests alongside source files ARE detected and preserved
- ✅ Existing patterns (like Social Overlay) work correctly
- ✅ New tests default to `primary` locations (tests/, __tests__/)

### Future Enhancement (v2.0.0)

**Goal**: Intelligently place tests based on test type.

**Detection Strategy**:
1. Analyze test name/content to determine test type:
   - `*.unit.test.ts` → alongside source
   - `*.e2e.test.ts` → tests/e2e/
   - `*.perf.test.ts` → tests/perf/
   - `*.integration.test.ts` → tests/integration/

2. Check existing project structure:
   - If `tests/e2e/` exists → place e2e tests there
   - If no e2e directory → place alongside source or in tests/

3. User configuration override:
   ```json
   // package.json
   {
     "claude-test-gen": {
       "testLocations": {
         "unit": "alongside",          // src/Button.test.ts
         "integration": "tests/integration/",
         "e2e": "tests/e2e/",
         "perf": "tests/perf/"
       }
     }
   }
   ```

**Benefits**:
- ✅ Respects existing project patterns automatically
- ✅ Follows team conventions without configuration
- ✅ Supports complex monorepo structures
- ✅ Allows per-test-type location customization

**Implementation Notes**:
- Requires test type detection in Analyze Agent
- Requires location mapping in orchestrator
- Backward compatible (defaults to current behavior)

---

## Version History

- **1.0.0** (2025-12-11): Initial version with cross-language support for 7 languages
  - JavaScript/TypeScript: Supports alongside-source pattern (Social Overlay compatible)
  - Note: Mixed locations (unit alongside, e2e in /tests) planned for v2.0.0
