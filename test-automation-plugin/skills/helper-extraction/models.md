# Helper Extraction Data Models

**Purpose**: Define data structures for pattern detection, helper generation, and test code modification during test helper extraction.

**Version**: 1.0.0

---

## Overview

These data models enable communication between components of the helper extraction system:
- **PatternMetadata**: Represents detected helper patterns in test code
- **HelperModule**: Represents generated or existing helper module files
- **ExtractedHelper**: Links detected patterns to generated helper functions

All models support JSON serialization for passing data between write-agent steps.

---

## PatternMetadata

Represents a detected helper pattern that is a candidate for extraction.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `type` | `str` | Pattern category: "mock_creation", "test_builder", "setup_teardown" | Required, must be one of the three types |
| `name` | `str` | Suggested helper function name (e.g., "create_mock_api") | Required, non-empty, alphanumeric + underscore |
| `code_snippet` | `str` | The actual code to extract | Required, non-empty |
| `line_count` | `int` | Number of lines in the pattern | Required, must be > 0 |
| `occurrences` | `int` | How many times this pattern appears across test files | Required, must be >= 1 |
| `complexity_score` | `int` | Complexity rating from 1-10 based on nesting, dependencies | Required, 1-10 range |
| `dependencies` | `List[str]` | Required imports for this helper (e.g., ["unittest.mock", "pytest"]) | Optional, defaults to empty list |

### Example (Python-style pseudocode)

```python
from typing import List
from dataclasses import dataclass, asdict
import json

@dataclass
class PatternMetadata:
    """Metadata about a detected helper pattern in test code."""

    type: str  # "mock_creation", "test_builder", "setup_teardown"
    name: str
    code_snippet: str
    line_count: int
    occurrences: int
    complexity_score: int
    dependencies: List[str] = None

    def __post_init__(self):
        """Validate fields after initialization."""
        if self.dependencies is None:
            self.dependencies = []

        # Validation
        valid_types = ["mock_creation", "test_builder", "setup_teardown"]
        if self.type not in valid_types:
            raise ValueError(f"Invalid type: {self.type}. Must be one of {valid_types}")

        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")

        if not self.code_snippet or not self.code_snippet.strip():
            raise ValueError("Code snippet cannot be empty")

        if self.line_count <= 0:
            raise ValueError(f"Line count must be positive, got {self.line_count}")

        if self.occurrences < 1:
            raise ValueError(f"Occurrences must be >= 1, got {self.occurrences}")

        if not (1 <= self.complexity_score <= 10):
            raise ValueError(f"Complexity score must be 1-10, got {self.complexity_score}")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'PatternMetadata':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
```

### Usage Example

```python
# Detect a mock creation pattern
pattern = PatternMetadata(
    type="mock_creation",
    name="create_mock_api_client",
    code_snippet="""
    mock_api = Mock()
    mock_api.get.return_value = {"status": "ok"}
    mock_api.post.return_value = {"id": 123}
    """,
    line_count=4,
    occurrences=3,
    complexity_score=5,
    dependencies=["unittest.mock.Mock"]
)

# Serialize for passing between components
json_data = pattern.to_json()

# Deserialize
restored_pattern = PatternMetadata.from_json(json_data)
```

---

## HelperModule

Represents a generated or existing helper module file in the project.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `file_path` | `str` | Absolute path to helper module file | Required, non-empty |
| `language` | `str` | Programming language: "python", "javascript", "typescript", "java", "csharp", "go", "cpp", "rust" | Required, must be supported language |
| `framework` | `str` | Test framework: "pytest", "jest", "junit5", "xunit", etc. | Required, non-empty |
| `existing_helpers` | `List[str]` | Function/class names already present in the file | Optional, defaults to empty list |
| `generated_helpers` | `List[str]` | Newly generated helper function names | Optional, defaults to empty list |
| `imports` | `List[str]` | Required import statements for the helper module | Optional, defaults to empty list |

### Example (Python-style pseudocode)

```python
from typing import List
from dataclasses import dataclass, asdict
import json

@dataclass
class HelperModule:
    """Represents a generated or existing helper module."""

    file_path: str
    language: str
    framework: str
    existing_helpers: List[str] = None
    generated_helpers: List[str] = None
    imports: List[str] = None

    def __post_init__(self):
        """Validate fields and set defaults."""
        if self.existing_helpers is None:
            self.existing_helpers = []
        if self.generated_helpers is None:
            self.generated_helpers = []
        if self.imports is None:
            self.imports = []

        # Validation
        if not self.file_path or not self.file_path.strip():
            raise ValueError("File path cannot be empty")

        valid_languages = ["python", "javascript", "typescript", "java",
                          "csharp", "go", "cpp", "rust"]
        if self.language not in valid_languages:
            raise ValueError(f"Invalid language: {self.language}")

        if not self.framework or not self.framework.strip():
            raise ValueError("Framework cannot be empty")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'HelperModule':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    def has_helper(self, name: str) -> bool:
        """Check if helper already exists (either existing or newly generated)."""
        return name in self.existing_helpers or name in self.generated_helpers

    def add_generated_helper(self, name: str):
        """Add a newly generated helper name."""
        if not self.has_helper(name):
            self.generated_helpers.append(name)
```

### Usage Example

```python
# Create helper module metadata
helper_module = HelperModule(
    file_path="/project/tests/helpers.py",
    language="python",
    framework="pytest",
    existing_helpers=["setup_database", "cleanup_files"],
    generated_helpers=["create_mock_api", "build_test_user"],
    imports=["from unittest.mock import Mock, patch", "import pytest"]
)

# Check if helper exists before generating
if not helper_module.has_helper("create_mock_api"):
    helper_module.add_generated_helper("create_mock_api")

# Serialize
json_data = helper_module.to_json()
```

---

## ExtractedHelper

Links a detected pattern to its generated helper function, providing all information needed for import injection.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `pattern` | `PatternMetadata` | The original detected pattern | Required |
| `function_name` | `str` | Final name of the helper function in the module | Required, non-empty |
| `import_statement` | `str` | Language-specific import statement for the test file | Required, non-empty |
| `module_path` | `str` | Path to the helper module (relative or absolute) | Required, non-empty |

### Example (Python-style pseudocode)

```python
from dataclasses import dataclass, asdict
import json

@dataclass
class ExtractedHelper:
    """Links a detected pattern to its generated helper function."""

    pattern: PatternMetadata
    function_name: str
    import_statement: str
    module_path: str

    def __post_init__(self):
        """Validate fields."""
        if not self.function_name or not self.function_name.strip():
            raise ValueError("Function name cannot be empty")

        if not self.import_statement or not self.import_statement.strip():
            raise ValueError("Import statement cannot be empty")

        if not self.module_path or not self.module_path.strip():
            raise ValueError("Module path cannot be empty")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        # Manually serialize nested PatternMetadata
        data['pattern'] = asdict(self.pattern)
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'ExtractedHelper':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        # Reconstruct nested PatternMetadata
        pattern_data = data.pop('pattern')
        pattern = PatternMetadata(**pattern_data)
        return cls(pattern=pattern, **data)
```

### Usage Example

```python
# Create extracted helper linking pattern to generated function
extracted = ExtractedHelper(
    pattern=pattern,  # PatternMetadata from earlier
    function_name="create_mock_api_client",
    import_statement="from tests.helpers import create_mock_api_client",
    module_path="tests/helpers.py"
)

# Use for import injection
print(f"Add to test file: {extracted.import_statement}")
print(f"Replace code: {extracted.pattern.code_snippet}")
print(f"With call: {extracted.function_name}()")

# Serialize for passing between agents
json_data = extracted.to_json()
```

---

## Language-Specific Import Patterns

Different languages require different import statement formats. Use these patterns when creating `ExtractedHelper` objects:

### Python
```python
# Single function
import_statement = "from tests.helpers import create_mock_api"

# Multiple functions
import_statement = "from tests.helpers import create_mock_api, build_test_user"
```

### JavaScript
```javascript
// ES6 modules
import_statement = "import { createMockRequest, buildTestUser } from './helpers/mockHelpers';"

// CommonJS
import_statement = "const { createMockRequest } = require('./helpers/mockHelpers');"
```

### TypeScript
```typescript
// With type imports
import_statement = "import { createMockRequest, MockRequest } from './helpers/mockHelpers';"
```

### Java
```java
// Static import for direct usage
import_statement = "import static com.company.TestUtils.createMockRepository;"

// Class import
import_statement = "import com.company.TestUtils;"
```

### C#
```csharp
// Using statement
import_statement = "using CompanyName.Tests;"

// Static using (C# 6+)
import_statement = "using static CompanyName.Tests.TestHelpers;"
```

### Go
```go
// Package import
import_statement = "import \"project/testhelpers\""
```

### C++
```cpp
// Header include
import_statement = "#include \"test_helpers.h\""
```

### Rust
```rust
// Module import
import_statement = "use common::test_helpers::*;"
```

---

## Serialization Examples

All models support round-trip JSON serialization:

```python
# Create models
pattern = PatternMetadata(
    type="mock_creation",
    name="create_mock_db",
    code_snippet="mock = Mock()",
    line_count=1,
    occurrences=2,
    complexity_score=3,
    dependencies=["unittest.mock"]
)

helper_module = HelperModule(
    file_path="/tests/helpers.py",
    language="python",
    framework="pytest",
    generated_helpers=["create_mock_db"]
)

extracted = ExtractedHelper(
    pattern=pattern,
    function_name="create_mock_db",
    import_statement="from tests.helpers import create_mock_db",
    module_path="tests/helpers.py"
)

# Serialize to JSON
pattern_json = pattern.to_json()
helper_json = helper_module.to_json()
extracted_json = extracted.to_json()

# Deserialize from JSON
restored_pattern = PatternMetadata.from_json(pattern_json)
restored_helper = HelperModule.from_json(helper_json)
restored_extracted = ExtractedHelper.from_json(extracted_json)

# Verify data integrity
assert pattern.name == restored_pattern.name
assert helper_module.file_path == restored_helper.file_path
assert extracted.function_name == restored_extracted.function_name
```

---

## Error Handling

All models perform validation in `__post_init__()` and raise `ValueError` with descriptive messages for invalid data:

```python
# Invalid pattern type
try:
    pattern = PatternMetadata(
        type="invalid_type",  # Not in valid_types
        name="test",
        code_snippet="code",
        line_count=1,
        occurrences=1,
        complexity_score=5
    )
except ValueError as e:
    print(f"Error: {e}")  # "Invalid type: invalid_type. Must be one of..."

# Negative line count
try:
    pattern = PatternMetadata(
        type="mock_creation",
        name="test",
        code_snippet="code",
        line_count=-5,  # Invalid
        occurrences=1,
        complexity_score=5
    )
except ValueError as e:
    print(f"Error: {e}")  # "Line count must be positive, got -5"

# Empty function name
try:
    extracted = ExtractedHelper(
        pattern=pattern,
        function_name="",  # Invalid
        import_statement="import test",
        module_path="/test.py"
    )
except ValueError as e:
    print(f"Error: {e}")  # "Function name cannot be empty"
```

---

## Integration with Write-Agent

These models are used in the write-agent Step 5 workflow:

1. **Pattern Detector** uses `PatternMetadata` to describe detected patterns
2. **Helper Generator** creates `HelperModule` objects representing generated files
3. **Import Injector** uses `ExtractedHelper` to know what imports to add and what code to replace

Example workflow:

```python
# Step 5: Add Mocking and Fixtures (with helper extraction)

# 1. Pattern Detector analyzes test code
patterns: List[PatternMetadata] = detect_helper_patterns(test_code, language, framework)

# 2. Helper Generator creates/updates helper module
if patterns:
    helper_module: HelperModule = generate_helper_module(
        patterns, test_directory, language, framework
    )

    # 3. Create ExtractedHelper objects linking patterns to functions
    extracted_helpers: List[ExtractedHelper] = []
    for pattern in patterns:
        extracted = ExtractedHelper(
            pattern=pattern,
            function_name=pattern.name,
            import_statement=generate_import(pattern.name, language, helper_module.file_path),
            module_path=helper_module.file_path
        )
        extracted_helpers.append(extracted)

    # 4. Import Injector modifies test code
    modified_test_code = inject_imports(test_code, extracted_helpers, language)
else:
    # No patterns detected, use inline helpers (existing behavior)
    modified_test_code = test_code
```

---

## Testing Requirements

Unit tests must verify:

1. **Model instantiation**: All fields populated correctly
2. **Field validation**: Invalid values raise ValueError with clear messages
3. **JSON serialization**: `to_json()` produces valid JSON
4. **JSON deserialization**: `from_json()` reconstructs object correctly
5. **Round-trip integrity**: Serialize then deserialize produces equivalent object
6. **Edge cases**: Empty strings, negative numbers, invalid enum values
7. **Helper methods**: `has_helper()`, `add_generated_helper()` work correctly

Test file location: `tests/unit/test_helper_extraction_models.py`
