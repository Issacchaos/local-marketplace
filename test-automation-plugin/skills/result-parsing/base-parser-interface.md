# BaseTestParser Interface

**Version**: 1.0.0
**Category**: Interface Definition
**Purpose**: Define the contract that all framework-specific parsers must implement

## Overview

The BaseTestParser is an abstract interface that defines the methods all test framework parsers must implement. It provides a consistent API for parsing test output across all supported frameworks, ensuring that the Execute Agent and Validate Agent can work with any framework without needing framework-specific code.

## Interface Definition

```python
class BaseTestParser(ABC):
    """
    Abstract base class for test framework output parsers.

    Each parser is responsible for:
    1. Parsing framework-specific test output
    2. Extracting test counts (passed, failed, skipped, error)
    3. Extracting individual test failures with details
    4. Extracting coverage information (if available)
    """

    @abstractmethod
    def parse(self, execution_result: TestExecutionResult) -> TestExecutionResult:
        """Parse test output and enrich execution result."""
        pass

    @abstractmethod
    def extract_failures(self, output: str) -> List[TestFailureInfo]:
        """Extract individual test failures from output."""
        pass

    @abstractmethod
    def extract_coverage(self, output: str) -> Optional[TestCoverageInfo]:
        """Extract test coverage information from output."""
        pass

    @abstractmethod
    def can_parse(self, framework: str, output: str) -> bool:
        """Check if this parser can handle the given framework/output."""
        pass
```

## Method Details

### 1. parse(execution_result)

**Purpose**: Main parsing method that extracts test counts and metadata

**Input**:
```python
execution_result: TestExecutionResult
    .stdout: str                    # Standard output from test execution
    .stderr: str                    # Standard error from test execution
    .combined_output: str           # Merged stdout + stderr
    .exit_code: int                 # Process exit code
    .command: str                   # Test command that was executed
    .framework: str                 # Detected framework name
```

**Output**:
```python
execution_result: TestExecutionResult (enriched)
    .total_tests: int               # Total number of tests executed
    .passed_count: int              # Number of tests that passed
    .failed_count: int              # Number of tests that failed
    .skipped_count: int             # Number of tests skipped
    .error_count: int               # Number of tests with errors
    .duration_seconds: float        # Total execution time
```

**Implementation Guidelines**:
1. Access output via `execution_result.combined_output` (preferred) or `.stdout`
2. Extract test counts from summary line(s)
3. Extract duration from summary line
4. Handle edge cases:
   - No tests collected (total_tests = 0)
   - All tests pass (failed_count = 0)
   - All tests fail (passed_count = 0)
   - Timeout (partial output, no summary)
5. Set sensible defaults if parsing fails (0 for all counts)
6. Log warnings for unparseable sections
7. Return the enriched execution_result object

**Example Implementation** (pytest):
```python
def parse(self, execution_result: TestExecutionResult) -> TestExecutionResult:
    output = execution_result.combined_output

    # Extract test counts from summary
    # "===== 10 passed, 2 failed, 1 skipped in 1.23s ====="
    passed, failed, skipped, error = self._extract_test_counts(output)

    execution_result.total_tests = passed + failed + skipped + error
    execution_result.passed_count = passed
    execution_result.failed_count = failed
    execution_result.skipped_count = skipped
    execution_result.error_count = error

    # Extract duration
    duration_match = re.search(r'in ([\d.]+)s', output)
    if duration_match:
        execution_result.duration_seconds = float(duration_match.group(1))

    return execution_result
```

### 2. extract_failures(output)

**Purpose**: Extract detailed information about each failed test

**Input**:
```python
output: str                         # Raw test output (stdout + stderr)
```

**Output**:
```python
failures: List[TestFailureInfo]
    Each TestFailureInfo contains:
        .test_name: str                 # Name of the failed test
        .test_file: str                 # File containing the test
        .test_method: str               # Method/function name
        .failure_type: str              # AssertionError, TimeoutError, Exception, etc.
        .failure_message: str           # Human-readable error message
        .stack_trace: str               # Full stack trace
        .failure_line_number: int       # Line where failure occurred
        .failure_file: str              # File where failure occurred (may differ from test_file)
        .affected_code: str             # Code snippet showing failure location
```

**Implementation Guidelines**:
1. Find the failures section in output (e.g., "FAILURES", "FAILED TESTS")
2. Split into individual failure blocks
3. For each failure:
   - Extract test name from header
   - Extract file path and line number
   - Extract error type (AssertionError, Exception, etc.)
   - Extract error message (clean formatting)
   - Capture full stack trace
   - Optionally extract affected code snippet
4. Handle edge cases:
   - No failures section (return empty list)
   - Malformed failure blocks (skip and log warning)
   - Missing information (use empty strings/None for optional fields)
5. Return list of TestFailureInfo objects (may be empty)

**Example Implementation** (pytest):
```python
def extract_failures(self, output: str) -> List[TestFailureInfo]:
    failures = []

    # Find FAILURES section
    failures_match = re.search(
        r"=+ FAILURES =+(.+?)(?:=+ short test summary|$)",
        output,
        re.DOTALL,
    )

    if not failures_match:
        return failures

    failures_section = failures_match.group(1)

    # Split into individual failures
    # "___________ test_name ___________"
    failure_blocks = re.split(r"^_{30,}\s+(.+?)\s+_{30,}$", failures_section, flags=re.MULTILINE)

    # Process each failure block
    for i in range(1, len(failure_blocks), 2):
        test_name = failure_blocks[i].strip()
        failure_content = failure_blocks[i + 1] if i + 1 < len(failure_blocks) else ""

        # Extract file and location
        # "tests/test_foo.py:15: in test_function"
        location_match = re.search(r"^(.*?):(\d+):\s+in\s+(\w+)", failure_content, re.MULTILINE)
        if location_match:
            file_path = location_match.group(1)
            line_number = int(location_match.group(2))
            method_name = location_match.group(3)
        else:
            file_path = ""
            line_number = None
            method_name = None

        # Extract assertion errors
        # "E   AssertionError: assert 1 == 2"
        assertion_lines = []
        for line in failure_content.split("\n"):
            if line.strip().startswith("E   "):
                assertion_lines.append(line.strip()[4:])  # Remove "E   "

        failure_message = " ".join(assertion_lines) if assertion_lines else failure_content.strip()

        # Determine failure type
        failure_type = "AssertionError"
        if "TimeoutError" in failure_content:
            failure_type = "TimeoutError"
        elif "Exception" in failure_content:
            failure_type = "Exception"

        failures.append(TestFailureInfo(
            test_name=test_name,
            test_file=file_path,
            test_method=method_name,
            failure_message=failure_message,
            failure_type=failure_type,
            stack_trace=failure_content.strip(),
            failure_line_number=line_number,
            failure_file=file_path,
        ))

    return failures
```

### 3. extract_coverage(output)

**Purpose**: Extract test coverage information if present in output

**Input**:
```python
output: str                         # Raw test output that may contain coverage
```

**Output**:
```python
coverage: Optional[TestCoverageInfo]
    If coverage found:
        .total_coverage: float          # Overall coverage percentage (0-100)
        .line_coverage: float           # Line coverage percentage
        .branch_coverage: float         # Branch coverage percentage (optional)
        .total_lines: int               # Total lines of code
        .covered_lines: int             # Lines covered by tests
        .uncovered_lines: int           # Lines not covered
        .file_coverage: Dict[str, float] # Per-file coverage percentages
        .coverage_tool: str             # Tool used (pytest-cov, istanbul, etc.)

    If no coverage:
        None
```

**Implementation Guidelines**:
1. Look for coverage section in output (tool-specific markers)
2. Extract overall coverage percentage (TOTAL line)
3. Extract per-file coverage breakdown
4. Calculate covered/uncovered line counts
5. Handle edge cases:
   - Coverage not enabled (return None)
   - Coverage section incomplete (return None)
   - Multiple coverage formats (prioritize most detailed)
6. Return TestCoverageInfo or None

**Example Implementation** (pytest-cov):
```python
def extract_coverage(self, output: str) -> Optional[TestCoverageInfo]:
    # Look for coverage section
    # "----------- coverage: platform linux, python 3.12.1 -----------"
    coverage_match = re.search(
        r"----------- coverage:.*?-----------(.+?)(?:=+|$)",
        output,
        re.DOTALL,
    )

    if not coverage_match:
        return None

    coverage_section = coverage_match.group(1)

    # Extract TOTAL coverage
    # "TOTAL  100  25  75%"
    total_match = re.search(r"TOTAL\s+(\d+)\s+(\d+)\s+([\d.]+)%", coverage_section)
    if not total_match:
        return None

    total_stmts = int(total_match.group(1))
    total_miss = int(total_match.group(2))
    total_coverage = float(total_match.group(3))

    covered_stmts = total_stmts - total_miss

    # Extract per-file coverage
    # "src/example.py  20  5  75%"
    file_coverage = {}
    for match in re.finditer(r"^(.+?)\s+(\d+)\s+(\d+)\s+([\d.]+)%", coverage_section, re.MULTILINE):
        filename = match.group(1).strip()
        if filename != "TOTAL":
            coverage_pct = float(match.group(4))
            file_coverage[filename] = coverage_pct

    return TestCoverageInfo(
        total_coverage=total_coverage,
        line_coverage=total_coverage,
        total_lines=total_stmts,
        covered_lines=covered_stmts,
        uncovered_lines=total_miss,
        file_coverage=file_coverage,
        coverage_tool="pytest-cov",
    )
```

### 4. can_parse(framework, output)

**Purpose**: Determine if this parser can handle the given framework or output

**Input**:
```python
framework: str                      # Framework name (e.g., "pytest", "jest")
output: str                         # Sample of test output for detection
```

**Output**:
```python
can_handle: bool                    # True if this parser can parse, False otherwise
```

**Implementation Guidelines**:
1. Check framework name first (exact match or aliases)
2. If framework not provided or no match, analyze output
3. Look for framework-specific signatures (headers, markers, patterns)
4. Use multiple patterns for confidence
5. Return True only if confident this parser is correct
6. Return False if unsure (let other parsers try)

**Example Implementation** (pytest):
```python
def can_parse(self, framework: str, output: str) -> bool:
    # Check framework name
    if framework and "pytest" in framework.lower():
        return True

    # Check for pytest-specific signatures in output
    pytest_signatures = [
        r"=+ test session starts =+",      # Session header
        r"collected \d+ items?",             # Collection message
        r"\.py::\w+",                        # Test path format
        r"=+ FAILURES =+",                   # Failures section
        r"\d+ passed.*?in [\d.]+s",         # Summary line
    ]

    # If any signature matches, we can parse
    for pattern in pytest_signatures:
        if re.search(pattern, output, re.IGNORECASE):
            return True

    return False
```

## Helper Methods

The BaseTestParser provides utility methods for common parsing tasks:

### _extract_integer(pattern, text, default)

Extract integer from text using regex:

```python
count = self._extract_integer(r'(\d+) passed', output, 0)
# Extracts "10" from "10 passed, 2 failed"
```

### _extract_float(pattern, text, default)

Extract float from text using regex:

```python
coverage = self._extract_float(r'coverage: ([\d.]+)%', output, 0.0)
# Extracts "75.5" from "coverage: 75.5%"
```

### _safe_parse(execution_result)

Wrapper around parse() with error handling:

```python
result = self._safe_parse(execution_result)
# Catches exceptions and returns result with defaults
```

## Data Models

### TestExecutionResult

```python
class TestExecutionResult:
    # Input fields (provided by Execute Agent)
    command: str                    # Test command executed
    exit_code: int                  # Process exit code
    stdout: str                     # Standard output
    stderr: str                     # Standard error
    combined_output: str            # stdout + stderr
    framework: str                  # Detected framework

    # Output fields (populated by parser)
    total_tests: int                # Total tests executed
    passed_count: int               # Tests passed
    failed_count: int               # Tests failed
    skipped_count: int              # Tests skipped
    error_count: int                # Tests with errors
    duration_seconds: float         # Execution time
```

### TestFailureInfo

```python
class TestFailureInfo:
    test_name: str                  # Name of failed test
    test_file: str                  # File containing test
    test_method: str                # Method/function name
    failure_type: str               # AssertionError, Exception, etc.
    failure_message: str            # Human-readable error
    stack_trace: str                # Full stack trace
    failure_line_number: int        # Line where failure occurred
    failure_file: str               # File where failure occurred
    affected_code: str              # Code snippet (optional)
```

### TestCoverageInfo

```python
class TestCoverageInfo:
    total_coverage: float           # Overall coverage %
    line_coverage: float            # Line coverage %
    branch_coverage: float          # Branch coverage % (optional)
    total_lines: int                # Total lines of code
    covered_lines: int              # Lines covered
    uncovered_lines: int            # Lines not covered
    file_coverage: Dict[str, float] # Per-file coverage
    coverage_tool: str              # Tool used (pytest-cov, etc.)
```

## Implementation Checklist

When creating a new parser, ensure:

- [ ] Inherits from BaseTestParser
- [ ] Implements parse() method
- [ ] Implements extract_failures() method
- [ ] Implements extract_coverage() method
- [ ] Implements can_parse() method
- [ ] Handles edge cases (no tests, all pass, all fail, timeout)
- [ ] Uses helper methods (_extract_integer, _extract_float) where appropriate
- [ ] Logs warnings for unparseable sections
- [ ] Returns sensible defaults when parsing fails
- [ ] Documents framework-specific patterns
- [ ] Includes example output in documentation
- [ ] Tests with real framework output

## Testing Recommendations

### Unit Tests

Test each method independently:

```python
def test_parse_all_pass():
    parser = MyParser()
    result = TestExecutionResult(combined_output=sample_output)
    parsed = parser.parse(result)
    assert parsed.total_tests == 10
    assert parsed.passed_count == 10

def test_extract_failures():
    parser = MyParser()
    failures = parser.extract_failures(sample_output_with_failures)
    assert len(failures) == 2
    assert failures[0].test_name == "test_example"
    assert failures[0].failure_type == "AssertionError"

def test_can_parse_framework_name():
    parser = MyParser()
    assert parser.can_parse("myframework", "")
    assert not parser.can_parse("otherframework", "")

def test_can_parse_output_signature():
    parser = MyParser()
    assert parser.can_parse("", "=== MyFramework Test Runner ===")
```

### Integration Tests

Test with real framework output:

```python
def test_parse_real_output():
    # Load real pytest output from file
    with open("test_data/pytest_output.txt") as f:
        output = f.read()

    parser = PytestParser()
    result = TestExecutionResult(combined_output=output)
    parsed = parser.parse(result)

    # Verify accurate parsing
    assert parsed.total_tests > 0
    assert parsed.passed_count + parsed.failed_count == parsed.total_tests
```

### Edge Case Tests

Test challenging scenarios:

```python
def test_parse_empty_output():
    parser = MyParser()
    result = TestExecutionResult(combined_output="")
    parsed = parser.parse(result)
    assert parsed.total_tests == 0

def test_parse_malformed_output():
    parser = MyParser()
    result = TestExecutionResult(combined_output="garbage text")
    parsed = parser.parse(result)
    assert parsed.total_tests == 0  # Should not crash

def test_parse_timeout_partial_output():
    parser = MyParser()
    result = TestExecutionResult(combined_output="test 1 ... ok\ntest 2 ...")
    parsed = parser.parse(result)
    # Should handle gracefully
```

## Common Patterns

### Multi-Line Regex Matching

For finding sections:
```python
section_match = re.search(
    r"START_MARKER(.+?)END_MARKER",
    output,
    re.DOTALL  # Make . match newlines
)
```

### Line-by-Line Processing

For processing structured output:
```python
for line in output.split("\n"):
    line = line.strip()
    if line.startswith("PASS"):
        passed_count += 1
    elif line.startswith("FAIL"):
        failed_count += 1
```

### Greedy vs Non-Greedy Matching

Use non-greedy `*?` to avoid over-matching:
```python
# Greedy (BAD): Matches too much
r"START(.+)END"

# Non-greedy (GOOD): Stops at first END
r"START(.+?)END"
```

### Optional Groups

Handle variations in output format:
```python
# Matches "10 passed" OR "10 passed, 2 failed"
r"(\d+) passed(?:, (\d+) failed)?"
```

## References

- Dante's BaseTestParser: `dante/src/dante/runner/test_execution/parsers/base_parser.py`
- Python ABC (Abstract Base Class): https://docs.python.org/3/library/abc.html
- Regex documentation: https://docs.python.org/3/library/re.html

---

**Last Updated**: 2025-12-05
**Status**: Interface definition complete
**Usage**: Base class for all framework-specific parsers
