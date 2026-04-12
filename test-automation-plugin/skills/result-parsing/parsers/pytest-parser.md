# pytest Parser

**Version**: 1.0.0
**Framework**: pytest (Python)
**Category**: Framework-Specific Parser
**Status**: Phase 1 - MVP Complete

## Overview

The pytest Parser extracts test results, failure details, and coverage information from pytest test framework output. It handles pytest-specific formatting including test session information, test paths (module::class::method format), failure sections with stack traces, and pytest-cov coverage reports.

## Supported pytest Output Format

### Test Session Start
```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-7.4.3
collected 10 items
```

### Test Results
```
tests/test_foo.py::test_example PASSED                                   [ 10%]
tests/test_foo.py::test_failure FAILED                                   [ 20%]
tests/test_bar.py::test_skip SKIPPED                                     [ 30%]
```

### Failures Section
```
=================================== FAILURES ===================================
_______________________________ test_failure ___________________________________
tests/test_foo.py:15: in test_failure
    assert 1 == 2
E   AssertionError: assert 1 == 2
```

### Coverage (pytest-cov)
```
----------- coverage: platform linux, python 3.12.1 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/example.py               20      5    75%
TOTAL                        20      5    75%
```

### Summary
```
======================== short test summary info ===============================
FAILED tests/test_foo.py::test_failure - AssertionError: assert 1 == 2
======================== 1 failed, 8 passed, 1 skipped in 2.34s ===============
```

## Regex Patterns

### Test Counts

**Summary with Failures**:
```python
SUMMARY_PATTERN = r"=+\s*(\d+)\s+failed(?:,\s*(\d+)\s+passed)?(?:,\s*(\d+)\s+skipped)?(?:,\s*(\d+)\s+error)?.*?in\s+([\d.]+)s"
```
Matches: `===== 1 failed, 8 passed, 1 skipped in 2.34s =====`
Groups: (failed=1, passed=8, skipped=1, error=0, duration=2.34)

**Pass-Only Pattern**:
```python
PASS_ONLY_PATTERN = r"=+\s*(\d+)\s+passed(?:,\s*(\d+)\s+skipped)?.*?in\s+([\d.]+)s"
```
Matches: `===== 10 passed in 1.23s =====`
Groups: (passed=10, skipped=0, duration=1.23)

**Collection Pattern**:
```python
COLLECTED_PATTERN = r"collected\s+(\d+)\s+items?"
```
Matches: `collected 10 items`
Groups: (total=10)

### Failure Extraction

**Failure Start**:
```python
FAILURE_START = r"^_{30,}\s+(.+?)\s+_{30,}$"
```
Matches: `___________ test_failure ___________`
Groups: (test_name="test_failure")

**Failure Location**:
```python
FAILURE_LOCATION = r"^(.*?):(\d+):\s+in\s+(\w+)"
```
Matches: `tests/test_foo.py:15: in test_failure`
Groups: (file="tests/test_foo.py", line=15, method="test_failure")

**Assertion Error**:
```python
ASSERTION_ERROR = r"^E\s+(.+)$"
```
Matches: `E   AssertionError: assert 1 == 2`
Groups: (error_message="AssertionError: assert 1 == 2")

### Coverage Extraction

**Total Coverage**:
```python
COVERAGE_TOTAL = r"TOTAL\s+(\d+)\s+(\d+)\s+([\d.]+)%"
```
Matches: `TOTAL  20  5  75%`
Groups: (stmts=20, miss=5, coverage=75)

**Per-File Coverage**:
```python
COVERAGE_LINE = r"^(.+?)\s+(\d+)\s+(\d+)\s+([\d.]+)%"
```
Matches: `src/example.py  20  5  75%`
Groups: (file="src/example.py", stmts=20, miss=5, coverage=75)

## Implementation

### parse() Method

```python
def parse(self, execution_result: TestExecutionResult) -> TestExecutionResult:
    output = execution_result.combined_output

    # Extract test counts from summary
    passed, failed, skipped, error = self._extract_test_counts(output)

    execution_result.total_tests = passed + failed + skipped + error
    execution_result.passed_count = passed
    execution_result.failed_count = failed
    execution_result.skipped_count = skipped
    execution_result.error_count = error

    return execution_result
```

### extract_failures() Method

```python
def extract_failures(self, output: str) -> List[TestFailureInfo]:
    failures = []

    # Find FAILURES section
    failures_match = re.search(
        r"=+ FAILURES =+(.+?)(?:=+ short test summary|=+ warnings summary|$)",
        output,
        re.DOTALL,
    )

    if not failures_match:
        return failures

    failures_section = failures_match.group(1)

    # Split into individual failures
    failure_blocks = re.split(self.FAILURE_START, failures_section, flags=re.MULTILINE)

    # Process each failure block
    for i in range(1, len(failure_blocks), 2):
        test_name = failure_blocks[i].strip()
        failure_content = failure_blocks[i + 1] if i + 1 < len(failure_blocks) else ""

        failure_info = self._parse_single_failure(test_name, failure_content)
        if failure_info:
            failures.append(failure_info)

    return failures
```

### extract_coverage() Method

```python
def extract_coverage(self, output: str) -> Optional[TestCoverageInfo]:
    # Look for coverage section
    coverage_match = re.search(
        r"----------- coverage:.*?-----------(.+?)(?:=+|$)",
        output,
        re.DOTALL,
    )

    if not coverage_match:
        return None

    coverage_section = coverage_match.group(1)

    # Extract TOTAL coverage
    total_match = re.search(self.COVERAGE_TOTAL, coverage_section)
    if not total_match:
        return None

    total_stmts = int(total_match.group(1))
    total_miss = int(total_match.group(2))
    total_coverage = float(total_match.group(3))

    covered_stmts = total_stmts - total_miss

    # Extract per-file coverage
    file_coverage = {}
    for match in re.finditer(self.COVERAGE_LINE, coverage_section, re.MULTILINE):
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

### can_parse() Method

```python
def can_parse(self, framework: str, output: str) -> bool:
    # Check framework name
    if framework and "pytest" in framework.lower():
        return True

    # Check for pytest-specific signatures
    pytest_signatures = [
        r"=+ test session starts =+",
        r"collected \d+ items?",
        r"\.py::\w+",
        r"=+ FAILURES =+",
        r"\d+ passed.*?in [\d.]+s",
    ]

    for pattern in pytest_signatures:
        if re.search(pattern, output, re.IGNORECASE):
            return True

    return False
```

## Edge Cases

### No Tests Collected
```
===== test session starts =====
collected 0 items
===== no tests ran in 0.01s =====
```
**Result**: total_tests=0, passed=0, failed=0, skipped=0

### All Tests Pass
```
===== test session starts =====
collected 10 items
tests/test_foo.py::test_1 PASSED
...
===== 10 passed in 1.23s =====
```
**Result**: total_tests=10, passed=10, failed=0, failures=[]

### All Tests Fail
```
===== test session starts =====
collected 10 items
tests/test_foo.py::test_1 FAILED
...
===== FAILURES =====
...
===== 10 failed in 1.23s =====
```
**Result**: total_tests=10, passed=0, failed=10, failures=[...10 items]

### Timeout (Partial Output)
```
===== test session starts =====
collected 10 items
tests/test_foo.py::test_1 PASSED
tests/test_foo.py::test_2
```
**Result**: Extract counts from collected line, mark as partial

### Mixed Results
```
===== test session starts =====
collected 15 items
tests/test_foo.py::test_1 PASSED
tests/test_foo.py::test_2 FAILED
tests/test_foo.py::test_3 SKIPPED
...
===== 10 passed, 3 failed, 2 skipped in 2.34s =====
```
**Result**: total=15, passed=10, failed=3, skipped=2

## Sample Test Data

### All Pass
```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-7.4.3
collected 3 items

tests/test_calculator.py::test_add PASSED                                [ 33%]
tests/test_calculator.py::test_subtract PASSED                           [ 66%]
tests/test_calculator.py::test_multiply PASSED                           [100%]

============================== 3 passed in 0.02s ===============================
```

### With Failures
```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-7.4.3
collected 3 items

tests/test_calculator.py::test_add PASSED                                [ 33%]
tests/test_calculator.py::test_subtract FAILED                           [ 66%]
tests/test_calculator.py::test_multiply PASSED                           [100%]

=================================== FAILURES ===================================
_____________________________ test_subtract ____________________________________
tests/test_calculator.py:10: in test_subtract
    assert calculator.subtract(5, 3) == 3
E   AssertionError: assert 2 == 3
E    +  where 2 = <bound method Calculator.subtract of <calculator.Calculator object at 0x7f8b8c0a3d90>>(5, 3)

======================== short test summary info ===============================
FAILED tests/test_calculator.py::test_subtract - AssertionError: assert 2 == 3
======================== 1 failed, 2 passed in 0.05s ===========================
```

### With Coverage
```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-7.4.3, pluggy-1.3.0
plugins: cov-4.1.0
collected 3 items

tests/test_calculator.py::test_add PASSED                                [ 33%]
tests/test_calculator.py::test_subtract PASSED                           [ 66%]
tests/test_calculator.py::test_multiply PASSED                           [100%]

----------- coverage: platform linux, python 3.12.1 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/calculator.py            12      2    83%
TOTAL                        12      2    83%

============================== 3 passed in 0.10s ===============================
```

## References

- pytest documentation: https://docs.pytest.org/
- pytest output format: https://docs.pytest.org/en/stable/how-to/output.html
- pytest-cov: https://pytest-cov.readthedocs.io/
- Dante's PytestParser: `dante/src/dante/runner/test_execution/parsers/pytest_parser.py`

---

**Last Updated**: 2025-12-05
**Status**: Phase 1 implementation complete
**Framework**: pytest (Python)
