# Python Framework Detection

**Version**: 1.0.0
**Language**: Python
**Frameworks**: pytest, unittest
**Status**: Phase 1 - MVP

## Overview

Python framework detection skill for identifying pytest and unittest testing frameworks in Python projects. This skill provides detailed detection patterns, confidence scoring, and edge case handling specific to Python testing.

## Supported Frameworks

### 1. pytest

**Description**: Modern, feature-rich testing framework for Python
**Official Docs**: https://docs.pytest.org/
**Minimum Version**: 6.0.0+
**Detection Priority**: High (preferred over unittest when both present)

### 2. unittest

**Description**: Python's built-in testing framework (standard library)
**Official Docs**: https://docs.python.org/3/library/unittest.html
**Minimum Version**: N/A (part of standard library)
**Detection Priority**: Medium (always available, use only if no pytest)

## Detection Patterns

### pytest Detection

#### 1. Configuration Files (Weight: 10)

```python
# Check for pytest-specific config files
pytest.ini                    # Primary pytest config
pyproject.toml                # Modern Python project config (check for [tool.pytest.ini_options])
setup.cfg                     # Legacy setuptools config (check for [tool:pytest])
tox.ini                       # Multi-env testing (check for [pytest] section)
```

**Detection Logic**:
```python
# For pytest.ini - exact file match
if exists("pytest.ini"):
    score += 10
    evidence.append("pytest.ini found")

# For pyproject.toml - must contain [tool.pytest.ini_options]
if exists("pyproject.toml"):
    with open("pyproject.toml") as f:
        if "[tool.pytest.ini_options]" in f.read():
            score += 10
            evidence.append("pyproject.toml with [tool.pytest.ini_options]")

# For setup.cfg - must contain [tool:pytest]
if exists("setup.cfg"):
    with open("setup.cfg") as f:
        if "[tool:pytest]" in f.read():
            score += 8
            evidence.append("setup.cfg with [tool:pytest]")
```

#### 2. Dependencies (Weight: 8)

**requirements.txt**:
```
pytest
pytest>=7.0.0
pytest[dev]
pytest-asyncio
pytest-cov
pytest-mock
pytest-xdist
```

**pyproject.toml** (poetry/pip):
```toml
[tool.poetry.dependencies]
pytest = "^7.4.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"

# OR (for pip)
[project]
dependencies = [
    "pytest>=7.0.0",
]

[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

**setup.py**:
```python
setup(
    # ...
    install_requires=['pytest'],
    tests_require=['pytest'],
    extras_require={
        'test': ['pytest', 'pytest-cov'],
    }
)
```

**Detection Logic**:
```python
dependencies = []

# Parse requirements.txt
if exists("requirements.txt"):
    for line in read_lines("requirements.txt"):
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name: pytest>=7.0.0 -> pytest
            package = line.split('==')[0].split('>=')[0].split('[')[0].strip()
            dependencies.append(package.lower())

# Parse pyproject.toml
if exists("pyproject.toml"):
    # Look for pytest in dependencies sections
    # Simple regex: r'"pytest[^"]*"' or r'pytest\s*='
    if 'pytest' in dependencies:
        score += 8
        evidence.append("pytest in dependencies")

# Check for pytest plugins (strong indicator)
pytest_plugins = ['pytest-cov', 'pytest-mock', 'pytest-asyncio', 'pytest-xdist']
for plugin in pytest_plugins:
    if plugin in dependencies:
        score += 2
        evidence.append(f"{plugin} plugin found")
```

#### 3. Import Patterns (Weight: 2)

Scan Python files (*.py) in project:

```python
import pytest
from pytest import fixture, mark
import pytest_asyncio

# Strong indicators
@pytest.fixture
@pytest.mark.parametrize
```

**Detection Logic**:
```python
# Sample up to 50 .py files
source_files = glob("**/*.py")[:50]

for file in source_files:
    content = read_file(file)

    # Check for pytest imports
    if "import pytest" in content:
        score += 2
        evidence.append(f"'import pytest' in {file}")

    if "from pytest import" in content:
        score += 2
        evidence.append(f"'from pytest import' in {file}")
```

#### 4. Code Patterns (Weight: 3)

```python
# Test function naming
def test_something():                           # pytest style (standalone)
    pass

def test_with_fixture(my_fixture):              # pytest with fixtures
    pass

# Fixtures
@pytest.fixture
def my_fixture():
    return "value"

# Parametrization
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
])
def test_increment(input, expected):
    assert input + 1 == expected

# Markers
@pytest.mark.skip
@pytest.mark.skipif(condition, reason="...")
@pytest.mark.xfail
@pytest.mark.slow

# Assertions (plain assert)
assert result == expected
assert result is not None
assert "substring" in result
```

**Detection Regex Patterns**:
```python
patterns = [
    r'def test_\w+\(',                          # Test function
    r'@pytest\.fixture',                        # Fixture decorator
    r'@pytest\.mark\.\w+',                      # Mark decorators
    r'import pytest',                           # pytest import
    r'from pytest import',                      # pytest from import
]

for file in source_files:
    content = read_file(file)
    for pattern in patterns:
        if re.search(pattern, content):
            score += 3
            evidence.append(f"Pattern '{pattern}' in {file}")
            break  # One match per file
```

#### 5. Test File Patterns (Weight: 1)

pytest discovers tests in files matching:
```
test_*.py
*_test.py
```

**Detection Logic**:
```python
test_files = glob("**/test_*.py") + glob("**/*_test.py")
if len(test_files) > 0:
    score += 1
    evidence.append(f"{len(test_files)} pytest-style test files found")
```

### unittest Detection

#### 1. Configuration Files (Weight: 10)

unittest has no specific config files (standard library), so this check is skipped.

```python
# unittest uses Python's built-in module - no config files
# Score: 0 from config files
```

#### 2. Dependencies (Weight: 8)

unittest is part of Python's standard library, so it won't appear in dependencies. However, check for unittest-related libraries:

```
mock                          # Backport of unittest.mock (Python 2)
unittest2                     # Backport for older Python versions
```

**Detection Logic**:
```python
# unittest won't be in dependencies (standard library)
# But absence of pytest + presence of test files suggests unittest
if 'pytest' not in dependencies and len(test_files) > 0:
    score += 4  # Lower confidence - might just be no framework
    evidence.append("No pytest in dependencies, but test files exist")
```

#### 3. Import Patterns (Weight: 2)

```python
import unittest
from unittest import TestCase, main
from unittest.mock import Mock, patch
```

**Detection Logic**:
```python
for file in source_files:
    content = read_file(file)

    if "import unittest" in content:
        score += 2
        evidence.append(f"'import unittest' in {file}")

    if "from unittest" in content:
        score += 2
        evidence.append(f"'from unittest import' in {file}")
```

#### 4. Code Patterns (Weight: 5)

```python
# Test class pattern
class TestMyFunction(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        self.assertEqual(result, expected)
        self.assertTrue(condition)
        self.assertIsNone(value)

# Main runner
if __name__ == '__main__':
    unittest.main()
```

**Detection Regex Patterns**:
```python
patterns = [
    r'class \w+\(unittest\.TestCase\)',         # unittest test class
    r'def test\w+\(self\)',                     # unittest test method
    r'self\.assert\w+',                         # unittest assertions
    r'unittest\.main\(\)',                      # unittest runner
    r'from unittest import TestCase',           # TestCase import
]

for file in source_files:
    content = read_file(file)
    for pattern in patterns:
        if re.search(pattern, content):
            score += 5  # Higher weight for unittest patterns
            evidence.append(f"Pattern '{pattern}' in {file}")
            break  # One match per file
```

#### 5. Test File Patterns (Weight: 1)

unittest discovers tests in:
```
test*.py
*_test.py
```

Similar to pytest, but unittest's discovery is more flexible.

## Confidence Scoring Examples

### Example 1: Pure pytest Project

```
Project Structure:
├── pytest.ini
├── requirements.txt  (contains "pytest>=7.0.0")
├── tests/
│   ├── test_api.py  (contains "import pytest" and "def test_endpoint():")
│   └── test_models.py

Scoring:
- pytest.ini found: +10
- pytest in requirements.txt: +8
- "import pytest" in test_api.py: +2
- "def test_" pattern in test_api.py: +3
- 2 pytest-style test files: +1

Total pytest score: 24
Total unittest score: 0

Confidence: pytest = 24/24 = 1.0 (100%)
Result: PRIMARY=pytest, SECONDARY=[], CONFIDENCE=1.0
```

### Example 2: Pure unittest Project

```
Project Structure:
├── requirements.txt  (no pytest)
├── tests/
│   ├── test_api.py  (contains "import unittest" and "class TestAPI(unittest.TestCase):")
│   └── test_models.py

Scoring:
- No pytest config: 0
- No pytest in dependencies: 0
- But test files exist: +4 (suggests unittest)
- "import unittest" in test_api.py: +2
- "class.*unittest.TestCase" pattern: +5

Total pytest score: 0
Total unittest score: 11

Confidence: unittest = 11/11 = 1.0 (100%)
Result: PRIMARY=unittest, SECONDARY=[], CONFIDENCE=1.0
```

### Example 3: Mixed pytest/unittest Project

```
Project Structure:
├── pytest.ini
├── requirements.txt  (contains "pytest>=7.0.0")
├── tests/
│   ├── test_new_api.py  (pytest style: "def test_endpoint():")
│   └── test_legacy.py   (unittest style: "class TestLegacy(unittest.TestCase):")

Scoring:
pytest:
- pytest.ini: +10
- pytest in requirements: +8
- "def test_" pattern: +3
Total: 21

unittest:
- "import unittest" in test_legacy.py: +2
- "class.*unittest.TestCase" pattern: +5
Total: 7

Total: 21 + 7 = 28

Confidence:
- pytest = 21/28 = 0.75 (75%)
- unittest = 7/28 = 0.25 (25%)

Result: PRIMARY=pytest, SECONDARY=[unittest], CONFIDENCE=0.75
```

### Example 4: No Framework (Fallback)

```
Project Structure:
├── requirements.txt  (no pytest)
├── src/
│   └── calculator.py
(no test files)

Scoring:
- No config files: 0
- No dependencies: 0
- No test files: 0

Total pytest score: 0
Total unittest score: 0

Result: PRIMARY=pytest (fallback), SECONDARY=[], CONFIDENCE=0.1
```

## Edge Cases

### 1. pytest.ini but no pytest dependency

**Scenario**: Developer created pytest.ini but hasn't installed pytest yet

**Detection**:
- pytest.ini found: +10
- No pytest in requirements: 0
- Score: 10

**Result**: PRIMARY=pytest, CONFIDENCE=0.8 (still high, config file is strong signal)

**Recommendation**: Suggest adding pytest to requirements.txt

### 2. pytest in requirements but unittest code style

**Scenario**: Project uses pytest to run unittest-style tests

**Detection**:
- pytest in requirements: +8
- unittest code patterns: +5
- Score: pytest=8, unittest=5

**Result**: PRIMARY=pytest, SECONDARY=[unittest], CONFIDENCE=0.62

**Note**: This is valid - pytest can run unittest-style tests

### 3. Both pytest.ini and setup.cfg with [tool:pytest]

**Scenario**: Redundant configuration

**Detection**:
- pytest.ini: +10
- setup.cfg with [tool:pytest]: +8
- Total: 18 (not 10, multiple evidence types)

**Result**: PRIMARY=pytest, CONFIDENCE=1.0

**Note**: Having multiple configs is okay, increases confidence

### 4. Test files but no clear framework

**Scenario**: Simple project with test_*.py files but no imports/assertions

**Detection**:
- test_*.py files exist: +1
- No framework imports: 0
- Score: 1

**Result**: PRIMARY=pytest (fallback), CONFIDENCE=0.1

**Recommendation**: Ask user to confirm framework choice

## Framework Selection Logic

```python
def select_primary_framework(pytest_score, unittest_score):
    """
    Select primary testing framework based on scores.
    """
    total = pytest_score + unittest_score

    # No evidence at all
    if total == 0:
        return {
            'primary': 'pytest',           # Fallback to pytest
            'secondary': [],
            'confidence': 0.1,
            'recommendation': 'No testing framework detected. pytest recommended for new projects.'
        }

    # Calculate confidences
    pytest_conf = pytest_score / total
    unittest_conf = unittest_score / total

    # Primary framework (highest score)
    if pytest_conf >= unittest_conf:
        primary = 'pytest'
        primary_conf = pytest_conf
    else:
        primary = 'unittest'
        primary_conf = unittest_conf

    # Secondary frameworks (confidence >= 0.2)
    secondary = []
    if pytest_conf >= 0.2 and primary != 'pytest':
        secondary.append('pytest')
    if unittest_conf >= 0.2 and primary != 'unittest':
        secondary.append('unittest')

    return {
        'primary': primary,
        'secondary': secondary,
        'confidence': primary_conf,
        'recommendation': _get_recommendation(primary, primary_conf, secondary)
    }

def _get_recommendation(primary, confidence, secondary):
    """Generate recommendation based on detection."""
    if confidence >= 0.8:
        return f"Strong detection: {primary} is clearly the primary framework."
    elif confidence >= 0.5:
        if secondary:
            return f"Moderate detection: {primary} is primary, but {', '.join(secondary)} also present (mixed usage)."
        else:
            return f"Moderate detection: {primary} is likely the primary framework."
    elif confidence >= 0.3:
        return f"Weak detection: {primary} detected with low confidence. Consider specifying framework explicitly."
    else:
        return f"Fallback to {primary}. No clear framework detected. Recommend adding explicit configuration."
```

## Application Framework Detection (Python)

In addition to test frameworks, detect Python application frameworks to provide better context:

### Django

**Indicators**:
- Files: `manage.py`, `settings.py`
- Dependencies: `django`
- Imports: `from django`, `import django`
- Patterns: `DJANGO_SETTINGS_MODULE`

### Flask

**Indicators**:
- Files: `app.py`
- Dependencies: `flask`
- Imports: `from flask import`
- Patterns: `Flask(__name__)`

### FastAPI

**Indicators**:
- Dependencies: `fastapi`, `uvicorn`
- Imports: `from fastapi import`
- Patterns: `FastAPI()`, `@app.get`, `@app.post`

**Usage**: Application framework helps generate relevant test fixtures and mocks.

## Output Format

When detection is complete, return structured data:

```yaml
language: python
primary_framework: pytest
secondary_frameworks:
  - unittest
application_framework: fastapi
confidence:
  pytest: 0.75
  unittest: 0.25
  fastapi: 0.90
detection_details:
  config_files:
    - pytest.ini
  dependencies:
    - pytest>=7.0.0
    - pytest-cov>=4.0.0
    - fastapi>=0.100.0
  import_patterns:
    - "import pytest" in tests/test_api.py
    - "from fastapi import" in src/main.py
  code_patterns:
    - "def test_" in tests/test_api.py
    - "@pytest.fixture" in tests/conftest.py
    - "FastAPI()" in src/main.py
  test_file_count: 15
  evidence_types: 4  # config, dependencies, imports, patterns
recommendation: "Strong detection: pytest is clearly the primary framework. FastAPI application detected - use FastAPI test client in fixtures."
```

## Usage in Agents

### Analyze Agent

```markdown
# Read Python Framework Detection Skill
Read file: skills/framework-detection/python-frameworks.md

# Apply Detection Strategies
1. Check for pytest.ini, pyproject.toml with [tool.pytest.ini_options]
2. Parse requirements.txt and pyproject.toml for pytest/unittest
3. Scan up to 50 .py files for imports (import pytest, import unittest)
4. Search for code patterns (def test_, class.*TestCase, @pytest.fixture)
5. Count test files matching test_*.py or *_test.py

# Calculate Scores
pytest_score = sum(pytest_evidence_weights)
unittest_score = sum(unittest_evidence_weights)

# Select Framework
if pytest_score + unittest_score == 0:
    primary = "pytest"  # Fallback
    confidence = 0.1
else:
    primary = highest_score_framework
    confidence = primary_score / total_score

# Output
Return: {
    "framework": primary,
    "confidence": confidence,
    "secondary": frameworks_with_confidence_>=_0.2
}
```

## Testing Validation

Test with these sample projects:

1. **pytest-only**: pytest.ini + pytest in requirements.txt → Expect: pytest, confidence ≥ 0.8
2. **unittest-only**: No pytest, unittest imports in tests → Expect: unittest, confidence ≥ 0.7
3. **mixed**: pytest config + unittest code → Expect: pytest primary, unittest secondary
4. **no-framework**: Empty project → Expect: pytest (fallback), confidence = 0.1
5. **pytest-plugins**: pytest + pytest-cov + pytest-mock → Expect: pytest, confidence ≥ 0.9

## References

- pytest documentation: https://docs.pytest.org/
- unittest documentation: https://docs.python.org/3/library/unittest.html
- Dante's FrameworkDetector: `dante/src/dante/analysis/framework_detector.py` (lines 106-117)
- Python packaging: https://packaging.python.org/

---

**Last Updated**: 2025-12-05
**Phase**: 1 - MVP
**Status**: Complete
