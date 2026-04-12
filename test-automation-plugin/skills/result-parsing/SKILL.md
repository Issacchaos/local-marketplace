---
name: result-parsing
description: Parse test framework output to extract results, failures, and coverage information. Use when processing test execution output from pytest, Jest, JUnit, xUnit, Google Test, Go test, and other frameworks to extract pass/fail counts, failure details, and stack traces.
user-invocable: false
---

# Result Parsing Skill

**Version**: 1.0.0
**Category**: Analysis
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++, Rust, Ruby, C
**Purpose**: Parse test framework output to extract results, failures, and coverage information

## Overview

The Result Parsing Skill provides comprehensive test output parsing capabilities across 11+ testing frameworks. It uses a factory pattern with auto-registration to select the appropriate parser based on framework type or output analysis, ensuring accurate extraction of test counts, failure details, and coverage information.

## Skill Interface

### Input

```yaml
test_output:
  stdout: Raw standard output from test execution
  stderr: Raw standard error from test execution
  combined: Merged stdout + stderr
framework: Detected framework name (e.g., "pytest", "jest", "junit")
exit_code: Process exit code (0 = success, non-zero = failure)
```

### Output

```yaml
test_results:
  total_tests: Total number of tests executed
  passed_count: Number of tests that passed
  failed_count: Number of tests that failed
  skipped_count: Number of tests skipped
  error_count: Number of tests with errors (not assertion failures)
  duration_seconds: Total test execution time

failures: List of individual test failures
  - test_name: Name of the failed test
    test_file: File containing the test
    test_method: Method/function name
    failure_type: Type of failure (AssertionError, TimeoutError, etc.)
    failure_message: Human-readable error message
    stack_trace: Full stack trace
    failure_line_number: Line where failure occurred
    affected_code: Code snippet showing the failure location

coverage: Optional coverage information
  total_coverage: Overall coverage percentage
  line_coverage: Line coverage percentage
  branch_coverage: Branch coverage percentage (if available)
  total_lines: Total lines of code
  covered_lines: Lines covered by tests
  uncovered_lines: Lines not covered
  file_coverage: Per-file coverage breakdown
  coverage_tool: Tool used (pytest-cov, istanbul, jacoco, etc.)
```

## Architecture

### Component Hierarchy

```
Result Parsing Skill
├── BaseTestParser (abstract interface)
│   ├── parse(execution_result) → TestExecutionResult
│   ├── extract_failures(output) → List[TestFailureInfo]
│   ├── extract_coverage(output) → TestCoverageInfo
│   └── can_parse(framework, output) → bool
│
├── ParserFactory (registry and selection)
│   ├── register_parser(parser_class)
│   ├── get_parser(framework, output) → BaseTestParser
│   ├── auto_detect_framework(command, output) → str
│   └── list_registered_parsers() → List[str]
│
└── Framework-Specific Parsers (implementations)
    ├── PytestParser (Python/pytest)
    ├── UnittestParser (Python/unittest)
    ├── JestParser (JavaScript/Jest)
    ├── VitestParser (TypeScript/Vitest)
    ├── JUnitParser (Java/JUnit)
    ├── XUnitParser (C#/xUnit)
    ├── NUnitParser (C#/NUnit)
    ├── MSTestParser (C#/MSTest)
    ├── GoTestParser (Go/built-in)
    ├── GTestParser (C++/GTest)
    ├── Catch2Parser (C++/Catch2)
    ├── CargoTestParser (Rust/cargo test)
    ├── RSpecParser (Ruby/RSpec)
    ├── UnityParser (C/Unity)
    ├── PlaywrightParser (TypeScript/Playwright)
    └── GenericParser (fallback)
```

## Parser Selection Flow

```
1. Framework Provided?
   ├─ YES → Try to match framework name to registered parsers
   │         └─ Match found? Use that parser
   │         └─ No match? Continue to output analysis
   │
   └─ NO → Perform output analysis

2. Output Analysis
   └─ For each registered parser:
      └─ Call parser.can_parse(framework, output)
         └─ Returns True? Use that parser
         └─ Continue checking

3. Fallback
   └─ No parser matched?
      └─ Use GenericParser (basic pattern matching)
```

## BaseTestParser Interface

See [base-parser-interface.md](./base-parser-interface.md) for complete details.

### Core Methods

1. **parse(execution_result)**: Main parsing method
   - Input: TestExecutionResult with raw output
   - Output: Enriched TestExecutionResult with test counts
   - Extracts: total, passed, failed, skipped, error counts + duration

2. **extract_failures(output)**: Failure extraction
   - Input: Raw test output string
   - Output: List of TestFailureInfo objects
   - Extracts: test name, file, line, error type, message, stack trace

3. **extract_coverage(output)**: Coverage extraction
   - Input: Raw test output string
   - Output: TestCoverageInfo or None
   - Extracts: coverage percentages, file breakdown, tool name

4. **can_parse(framework, output)**: Detection method
   - Input: Framework name and sample output
   - Output: Boolean indicating if this parser can handle it
   - Logic: Framework name matching + output signature detection

## Parser Factory Pattern

See [parser-factory-pattern.md](./parser-factory-pattern.md) for complete details.

### Key Features

1. **Auto-Registration**: Parsers self-register when imported
2. **Framework Hints**: Aliases for framework names (e.g., "py.test" → "pytest")
3. **Output Signatures**: Regex patterns for framework detection
4. **Confidence Scoring**: Select best parser when multiple match
5. **Fallback Mechanism**: GenericParser as last resort

### Usage Example

```python
# Get the factory (singleton)
factory = get_parser_factory()

# Register a custom parser
factory.register_parser(MyCustomParser)

# Get parser by framework name
parser = factory.get_parser(framework="pytest")

# Get parser by output analysis
parser = factory.get_parser(output="===== test session starts =====")

# Auto-detect framework
framework = factory.auto_detect_framework(
    command="pytest tests/",
    output="collected 10 items"
)
```

## Framework-Specific Parsers

### Phase 1 (MVP - v0.1.0)

#### PytestParser
See [parsers/pytest-parser.md](./parsers/pytest-parser.md) for complete details.

**Patterns**:
- Summary: `===== 10 passed, 2 failed in 1.23s =====`
- Collected: `collected 10 items`
- Failure section: `===== FAILURES =====`
- Failure header: `___________ test_name ___________`
- Location: `tests/test_foo.py:15: in test_function`
- Assertion: `E   AssertionError: assert 1 == 2`
- Coverage: `TOTAL  100  25  75%`

**Edge Cases**:
- All tests pass (no FAILURES section)
- All tests fail
- No tests collected
- Timeout during execution
- Coverage not enabled

#### UnittestParser
**Patterns**:
- Summary: `Ran 10 tests in 1.230s`
- Result: `OK`, `FAILED (failures=2)`, `FAILED (errors=1, failures=2)`
- Failure marker: `FAIL: test_name (module.TestClass)`
- Error marker: `ERROR: test_name (module.TestClass)`
- Separator: `----------------------------------------------------------------------`

### Phase 3 (v0.3.0)

#### JestParser
**Patterns**:
- Summary: `Test Suites: 2 passed, 2 total`
- Test count: `Tests: 10 passed, 2 failed, 12 total`
- Pass: `PASS tests/foo.test.js`
- Fail: `FAIL tests/bar.test.js`
- Failure marker: `● TestSuite › test name`
- Error location: `at Object.<anonymous> (tests/foo.test.js:15:5)`

#### VitestParser
**Patterns**:
- Similar to Jest but with Vitest-specific markers
- Summary: `Test Files  2 passed (2)`
- Test count: `Tests  10 passed | 2 failed (12)`
- Duration: `Duration  1.23s`

#### JUnitParser
**Patterns**:
- XML or text output
- Summary: `Tests run: 10, Failures: 2, Errors: 0, Skipped: 1`
- Failure: `testFailure(com.example.TestClass) Time elapsed: 0.001 s <<< FAILURE!`
- Location: `at com.example.TestClass.testMethod(TestClass.java:42)`

### Phase 4 (v0.4.0)

#### XUnitParser (C#)
**Patterns**:
- Summary: `Total tests: 10. Passed: 8. Failed: 2. Skipped: 0.`
- Fail marker: `[FAIL] TestNamespace.TestClass.TestMethod`
- Stack trace: `at TestNamespace.TestClass.TestMethod() in TestClass.cs:line 42`

#### GoTestParser
**Patterns**:
- Run marker: `=== RUN   TestFunction`
- Pass marker: `--- PASS: TestFunction (0.01s)`
- Fail marker: `--- FAIL: TestFunction (0.02s)`
- Location: `test_file.go:42: Error message`
- Summary: `FAIL  package/name  0.123s`

#### GTestParser (C++)
**Patterns**:
- Start: `[==========] Running 10 tests from 2 test suites.`
- Run: `[ RUN      ] TestSuite.TestName`
- Pass: `[       OK ] TestSuite.TestName (1 ms)`
- Fail: `[  FAILED  ] TestSuite.TestName (2 ms)`
- Failure location: `test_file.cpp:42: Failure`
- Summary: `[  PASSED  ] 8 tests.` + `[  FAILED  ] 2 tests, listed below:`

### Phase 5 (v0.5.0)

#### CargoTestParser (Rust)
**Patterns**:
- Start: `running 10 tests`
- Pass: `test test_name ... ok`
- Fail: `test test_name ... FAILED`
- Failure marker: `---- test_name stdout ----`
- Location: `thread 'test_name' panicked at 'assertion failed', src/lib.rs:42:5`
- Summary: `test result: FAILED. 8 passed; 2 failed; 0 ignored; 0 measured`

#### RSpecParser (Ruby)
**Patterns**:
- Pass: `.` (dot)
- Fail: `F` (letter F)
- Summary: `10 examples, 2 failures`
- Failure marker: `Failure/Error:`
- Location: `# ./spec/test_spec.rb:42:in 'block (2 levels) in <top (required)>'`

### E2E Frameworks

#### PlaywrightParser
See [parsers/playwright-parser.md](./parsers/playwright-parser.md) for complete details.

**Patterns**:
- Run header: `Running X tests using Y workers`
- Browser tags: `[chromium]`, `[firefox]`, `[webkit]`
- Pass: `✓  N [browser] > file:line:col > Suite > test name (duration)`
- Fail: `✗  N [browser] > file:line:col > Suite > test name (duration)`
- Skip: `-  N [browser] > file:line:col > Suite > test name`
- Failure header: `N) [browser] > file:line:col > Suite > test name`
- Error location: `at tests/login.spec.ts:12:50`
- Summary: `X passed (Ys)`, `X failed`, `X skipped`
- Timeout: `Test timeout of Xms exceeded`
- Retry: `(Retry #N)`
- Call log: `Call log:` followed by indented action trace
- Coverage: Istanbul table (if configured; Playwright has no built-in coverage)

**Auto-Detection Signatures**:
- `Running \d+ tests? using \d+ workers?` -> PlaywrightParser
- `\[chromium\]` / `\[firefox\]` / `\[webkit\]` -> PlaywrightParser

**Edge Cases**:
- All tests pass (no failure blocks)
- All tests fail
- No tests found
- Test timeout exceeded
- Action-level timeout exceeded
- Browsers not installed
- Web server startup failure
- Retries with eventual pass
- Multi-browser runs (chromium + firefox + webkit)
- Coverage not configured (default; no built-in coverage)

## Pattern Library

The pattern library provides reusable regex patterns for common parsing tasks.

### Test Count Patterns

See [pattern-library/test-count-patterns.md](./pattern-library/test-count-patterns.md)

Common patterns for extracting test counts:
- Passed count: Various frameworks use "passed", "ok", "successful", etc.
- Failed count: "failed", "failures", "errors"
- Skipped count: "skipped", "ignored", "pending"
- Total count: "tests run", "total tests", "tests"

### Failure Location Patterns

See [pattern-library/failure-location-patterns.md](./pattern-library/failure-location-patterns.md)

Common patterns for extracting failure locations:
- File path: Extract relative or absolute paths
- Line number: Extract line numbers
- Function/method name: Extract test names
- Error type: Classify error types

## Edge Case Handling

### No Tests Collected

**Scenario**: Test discovery found no tests

**Detection**:
- pytest: `collected 0 items`
- jest: `No tests found`
- junit: `Tests run: 0`
- playwright: `No tests found` or `no tests found`

**Response**:
```yaml
total_tests: 0
passed_count: 0
failed_count: 0
skipped_count: 0
error_count: 0
```

### All Tests Pass

**Scenario**: All tests successful

**Detection**:
- No FAILURES section
- Exit code: 0
- Summary shows only passed

**Response**:
```yaml
total_tests: N
passed_count: N
failed_count: 0
skipped_count: 0
failures: []
```

### All Tests Fail

**Scenario**: Every test failed

**Detection**:
- Exit code: non-zero
- passed_count: 0
- failed_count: N

**Response**:
- Extract all failures
- Recommend checking test setup/configuration
- Suggest possible causes (imports, fixtures, environment)

### Timeout During Execution

**Scenario**: Test execution was interrupted

**Detection**:
- Partial output
- No final summary line
- Exit code: timeout signal (124, 143, etc.)

**Response**:
```yaml
total_tests: N (partial)
passed_count: N (before timeout)
failed_count: 0 or more
error_count: 1 (timeout)
failures:
  - test_name: "Test Execution"
    failure_type: "TimeoutError"
    failure_message: "Test execution timed out after X seconds"
```

### Unparseable Output

**Scenario**: Output doesn't match any known framework

**Detection**:
- No parser returns True from can_parse()
- GenericParser used as fallback

**Response**:
- Basic pattern matching for common keywords
- Extract any numbers that look like counts
- Flag as "low confidence" parsing
- Recommend explicit framework specification

## Usage in Agents

### Execute Agent

When executing tests, the Execute Agent uses this skill to parse results:

```markdown
# Read Result Parsing Skill
Read file: skills/result-parsing/SKILL.md
Read file: skills/result-parsing/base-parser-interface.md
Read file: skills/result-parsing/parser-factory-pattern.md

# For framework-specific parsing
Read file: skills/result-parsing/parsers/pytest-parser.md  # If pytest detected

# Parse Test Output
1. Get parser from factory:
   parser = factory.get_parser(framework="pytest", output=test_output)

2. Parse execution result:
   result = parser.parse(execution_result)

3. Extract failure details:
   failures = parser.extract_failures(test_output)

4. Extract coverage (if available):
   coverage = parser.extract_coverage(test_output)

# Return Structured Results
Return:
  - test_counts: {total, passed, failed, skipped, error}
  - failures: [{test_name, file, line, message, trace}, ...]
  - coverage: {total_coverage, file_coverage, ...}
```

### Validate Agent

When analyzing test results:

```markdown
# Read Failure Information
failures = execution_result.failures

# For each failure:
  - Identify failure type (assertion, exception, timeout)
  - Categorize as test bug vs source bug
  - Extract relevant code context
  - Suggest fix approaches
```

## Testing Strategy

### Unit Testing

Test individual parser methods with known output samples:

```python
# Test pytest parser
def test_pytest_parser_all_pass():
    output = """
    ===== test session starts =====
    collected 10 items
    tests/test_foo.py::test_1 PASSED
    ...
    ===== 10 passed in 1.23s =====
    """

    parser = PytestParser()
    result = parser.parse(output)

    assert result.total_tests == 10
    assert result.passed_count == 10
    assert result.failed_count == 0
    assert len(result.failures) == 0
```

### Integration Testing

Test parser factory with real framework output:

```python
def test_factory_auto_detect_pytest():
    factory = get_parser_factory()

    output = "===== test session starts ====="
    framework = factory.auto_detect_framework("pytest tests/", output)

    assert framework == "pytest"

    parser = factory.get_parser(framework=framework, output=output)
    assert isinstance(parser, PytestParser)
```

### Edge Case Testing

Test with challenging scenarios:

- Empty output
- Partial output (timeout)
- Malformed output
- Mixed framework output
- Very large output (1000+ tests)
- Unicode characters in test names

## Performance Considerations

### Optimization Strategies

1. **Lazy Parsing**: Only parse failures if requested
2. **Regex Compilation**: Pre-compile frequently used patterns
3. **Early Exit**: Stop parsing once enough information is found
4. **Chunked Processing**: For large outputs, process in chunks
5. **Caching**: Cache parsed results to avoid re-parsing

### Expected Performance

- Small output (<100 lines): < 10ms
- Medium output (100-1000 lines): < 100ms
- Large output (1000-10000 lines): < 1 second
- Very large output (10000+ lines): < 5 seconds

## Future Enhancements

- Parallel test result parsing (multiple test runs)
- Incremental parsing (streaming output)
- Visual diff for assertion failures
- Test history tracking (flaky test detection)
- Performance regression detection
- Test duration analysis and reporting
- Parameterized test result grouping
- Subtest/nested test support

## References

- Dante's ParserFactory: `dante/src/dante/runner/test_execution/parsers/parser_factory.py`
- Dante's BaseTestParser: `dante/src/dante/runner/test_execution/parsers/base_parser.py`
- Dante's PytestParser: `dante/src/dante/runner/test_execution/parsers/pytest_parser.py`
- Framework documentation: pytest, Jest, JUnit, xUnit, GTest, etc.

---

**Last Updated**: 2025-12-05
**Status**: Phase 1 - pytest parser implemented
**Next**: Add remaining framework parsers in future phases
