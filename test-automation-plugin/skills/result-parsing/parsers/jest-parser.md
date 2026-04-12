# Jest Result Parser

**Version**: 1.0.0
**Framework**: Jest
**Languages**: JavaScript, TypeScript
**Purpose**: Parse Jest test execution output to extract test results, failures, and coverage

## Overview

The Jest Result Parser processes Jest test runner output to extract structured test results including pass/fail counts, individual test failures with locations, error messages, and code coverage data. This parser implements the BaseTestParser interface and auto-registers with the parser factory.

## Jest Output Format

### Summary Line

```
Test Suites: 2 failed, 3 passed, 5 total
Tests:       5 failed, 12 passed, 17 total
Snapshots:   1 obsolete, 1 total
Time:        5.231 s
```

### Test Results

```
 PASS  src/__tests__/calculator.test.js
  Calculator
    ✓ adds two numbers (3 ms)
    ✓ subtracts two numbers (1 ms)

 FAIL  src/__tests__/api.test.js
  API Client
    ✓ fetches data successfully (45 ms)
    ✕ handles errors correctly (12 ms)

  ● API Client › handles errors correctly

    expect(received).toBe(expected) // Object.is equality

    Expected: 404
    Received: 500

      12 |   it('handles errors correctly', () => {
      13 |     const error = getError();
    > 14 |     expect(error.status).toBe(404);
         |                          ^
      15 |   });
      16 | });

      at Object.<anonymous> (src/__tests__/api.test.js:14:26)
```

### Coverage Output (with --coverage)

```
------------|---------|----------|---------|---------|-------------------
File        | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
------------|---------|----------|---------|---------|-------------------
All files   |   85.71 |       75 |      80 |   85.71 |
 calculator |     100 |      100 |     100 |     100 |
 api        |      75 |       50 |      60 |      75 | 23-25,45
------------|---------|----------|---------|---------|-------------------
```

## Parser Interface Implementation

### can_parse(framework: str, output: str) → bool

Determines if this parser can handle the given framework/output.

**Implementation**:
```python
def can_parse(framework: str, output: str) -> bool:
    """
    Check if this parser can handle Jest output.

    Args:
        framework: Framework name hint (e.g., "jest", "vitest")
        output: Test execution output string

    Returns:
        True if this parser can handle the output
    """
    # Check framework name
    if framework and framework.lower() in ["jest"]:
        return True

    # Check output signatures
    jest_signatures = [
        r"Test Suites:",                    # Summary line
        r"Tests:\s+\d+",                    # Test count
        r"PASS\s+.*\.test\.(js|ts|jsx|tsx)", # Pass marker
        r"FAIL\s+.*\.test\.(js|ts|jsx|tsx)", # Fail marker
    ]

    for pattern in jest_signatures:
        if re.search(pattern, output, re.MULTILINE):
            return True

    return False
```

### parse(execution_result) → ParsedTestResult

Parses Jest output into structured result object.

**Input** (execution_result):
```python
{
    'command': 'npm test',
    'exit_code': 1,              # 0 = pass, 1 = failures
    'stdout': '...',             # Jest output
    'stderr': '...',             # Errors
    'duration': 5.231            # Seconds
}
```

**Output** (ParsedTestResult):
```python
{
    'framework': 'jest',
    'exit_code': 1,
    'passed_count': 12,
    'failed_count': 5,
    'skipped_count': 2,
    'total_count': 19,
    'duration': 5.231,
    'failures': [
        {
            'test_name': 'API Client › handles errors correctly',
            'test_file': 'src/__tests__/api.test.js',
            'line_number': 14,
            'error_type': 'AssertionError',
            'error_message': 'expect(received).toBe(expected)',
            'expected': '404',
            'received': '500',
            'stack_trace': '...'
        }
    ],
    'coverage': {
        'total_statements': 85.71,
        'total_branches': 75.0,
        'total_functions': 80.0,
        'total_lines': 85.71,
        'files': [...]
    },
    'raw_output': '...'
}
```

**Implementation**:
```python
def parse(execution_result):
    output = execution_result['stdout'] + execution_result['stderr']

    result = {
        'framework': 'jest',
        'exit_code': execution_result['exit_code'],
        'duration': execution_result.get('duration', 0),
        'raw_output': output
    }

    # Extract test counts
    counts = extract_test_counts(output)
    result.update(counts)

    # Extract failures
    if result['failed_count'] > 0:
        result['failures'] = extract_failures(output)

    # Extract coverage (if present)
    if '--coverage' in execution_result.get('command', ''):
        result['coverage'] = extract_coverage(output)

    return result
```

## Extraction Methods

### extract_test_counts(output: str) → dict

Extracts pass/fail/skip counts from Jest summary.

**Pattern**:
```
Tests:       5 failed, 2 skipped, 12 passed, 19 total
```

**Implementation**:
```python
def extract_test_counts(output):
    """
    Extract test counts from Jest summary line.

    Pattern: Tests: X failed, Y skipped, Z passed, T total
    """
    counts = {
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'total_count': 0
    }

    # Find "Tests:" summary line
    pattern = r'Tests:\s+(.*)'
    match = re.search(pattern, output, re.MULTILINE)

    if not match:
        return counts

    summary = match.group(1)

    # Extract individual counts
    # Failed: "5 failed"
    failed_match = re.search(r'(\d+)\s+failed', summary)
    if failed_match:
        counts['failed_count'] = int(failed_match.group(1))

    # Skipped: "2 skipped"
    skipped_match = re.search(r'(\d+)\s+skipped', summary)
    if skipped_match:
        counts['skipped_count'] = int(skipped_match.group(1))

    # Passed: "12 passed"
    passed_match = re.search(r'(\d+)\s+passed', summary)
    if passed_match:
        counts['passed_count'] = int(passed_match.group(1))

    # Total: "19 total"
    total_match = re.search(r'(\d+)\s+total', summary)
    if total_match:
        counts['total_count'] = int(total_match.group(1))

    return counts
```

### extract_failures(output: str) → list[dict]

Extracts individual test failure details.

**Pattern**:
```
  ● API Client › handles errors correctly

    expect(received).toBe(expected) // Object.is equality

    Expected: 404
    Received: 500

      12 |   it('handles errors correctly', () => {
      13 |     const error = getError();
    > 14 |     expect(error.status).toBe(404);
         |                          ^
      15 |   });

      at Object.<anonymous> (src/__tests__/api.test.js:14:26)
```

**Implementation**:
```python
def extract_failures(output):
    """
    Extract detailed failure information from Jest output.

    Each failure starts with ● and contains:
    - Test name (after ●)
    - Error message
    - Expected/Received values
    - Stack trace with file:line
    """
    failures = []

    # Split output into failure blocks
    # Pattern: ● Test Name
    failure_pattern = r'●\s+(.+?)\n\n(.*?)(?=●|\Z)'
    matches = re.finditer(failure_pattern, output, re.DOTALL | re.MULTILINE)

    for match in matches:
        test_name = match.group(1).strip()
        failure_body = match.group(2)

        failure = {
            'test_name': test_name,
            'test_file': None,
            'line_number': None,
            'error_type': 'AssertionError',
            'error_message': None,
            'expected': None,
            'received': None,
            'stack_trace': None
        }

        # Extract error message (first line of failure body)
        error_lines = failure_body.split('\n')
        if error_lines:
            failure['error_message'] = error_lines[0].strip()

        # Extract Expected/Received values
        expected_match = re.search(r'Expected:\s*(.+)', failure_body)
        if expected_match:
            failure['expected'] = expected_match.group(1).strip()

        received_match = re.search(r'Received:\s*(.+)', failure_body)
        if received_match:
            failure['received'] = received_match.group(1).strip()

        # Extract file location from stack trace
        # Pattern: at Object.<anonymous> (src/__tests__/api.test.js:14:26)
        location_pattern = r'at\s+.*?\((.+?):(\d+):\d+\)'
        location_match = re.search(location_pattern, failure_body)

        if location_match:
            failure['test_file'] = location_match.group(1)
            failure['line_number'] = int(location_match.group(2))

        # Extract full stack trace
        stack_start = failure_body.find('at ')
        if stack_start != -1:
            failure['stack_trace'] = failure_body[stack_start:]

        failures.append(failure)

    return failures
```

### extract_coverage(output: str) → dict

Extracts code coverage data from Jest coverage report.

**Pattern**:
```
------------|---------|----------|---------|---------|-------------------
File        | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
------------|---------|----------|---------|---------|-------------------
All files   |   85.71 |       75 |      80 |   85.71 |
 calculator |     100 |      100 |     100 |     100 |
 api        |      75 |       50 |      60 |      75 | 23-25,45
------------|---------|----------|---------|---------|-------------------
```

**Implementation**:
```python
def extract_coverage(output):
    """
    Extract coverage data from Jest coverage table.

    Returns:
        {
            'total_statements': 85.71,
            'total_branches': 75.0,
            'total_functions': 80.0,
            'total_lines': 85.71,
            'files': [
                {
                    'file': 'calculator',
                    'statements': 100,
                    'branches': 100,
                    'functions': 100,
                    'lines': 100,
                    'uncovered_lines': []
                },
                ...
            ]
        }
    """
    coverage = {
        'total_statements': 0,
        'total_branches': 0,
        'total_functions': 0,
        'total_lines': 0,
        'files': []
    }

    # Find coverage table
    table_pattern = r'-+\|.*?\n(.*?)\n-+\|'
    table_match = re.search(table_pattern, output, re.DOTALL)

    if not table_match:
        return coverage

    table_content = table_match.group(1)
    lines = table_content.split('\n')

    for line in lines:
        if not line.strip() or line.startswith('File'):
            continue

        # Parse table row: File | Stmts | Branch | Funcs | Lines | Uncovered
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue

        file_name = parts[0]
        stmts = parse_percentage(parts[1])
        branches = parse_percentage(parts[2])
        funcs = parse_percentage(parts[3])
        lines_cov = parse_percentage(parts[4])
        uncovered = parts[5] if len(parts) > 5 else ''

        if file_name == 'All files':
            # Total coverage
            coverage['total_statements'] = stmts
            coverage['total_branches'] = branches
            coverage['total_functions'] = funcs
            coverage['total_lines'] = lines_cov
        else:
            # Individual file
            coverage['files'].append({
                'file': file_name,
                'statements': stmts,
                'branches': branches,
                'functions': funcs,
                'lines': lines_cov,
                'uncovered_lines': parse_uncovered_lines(uncovered)
            })

    return coverage

def parse_percentage(value):
    """Convert '85.71' to 85.71 float."""
    try:
        return float(value.strip())
    except:
        return 0.0

def parse_uncovered_lines(uncovered_str):
    """
    Parse uncovered line ranges: '23-25,45' → [23, 24, 25, 45]
    """
    if not uncovered_str.strip():
        return []

    lines = []
    for part in uncovered_str.split(','):
        part = part.strip()
        if '-' in part:
            # Range: 23-25
            start, end = part.split('-')
            lines.extend(range(int(start), int(end) + 1))
        else:
            # Single line: 45
            lines.append(int(part))

    return lines
```

## Error Handling

### No Tests Collected

**Pattern**:
```
No tests found, exiting with code 1
```

**Handling**:
```python
if 'No tests found' in output:
    return {
        'framework': 'jest',
        'exit_code': 1,
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'total_count': 0,
        'error': 'No tests found',
        'recommendation': 'Verify test file patterns in jest.config.js'
    }
```

### Jest Not Installed

**Pattern**:
```
sh: jest: command not found
```
Or:
```
Cannot find module 'jest'
```

**Handling**:
```python
if 'jest: command not found' in output or "Cannot find module 'jest'" in output:
    return {
        'framework': 'jest',
        'exit_code': 127,
        'error': 'Jest not installed',
        'recommendation': 'Run: npm install --save-dev jest'
    }
```

### Syntax Errors in Tests

**Pattern**:
```
  ● Test suite failed to run

    SyntaxError: Unexpected token ')'

      at Runtime.createScriptFromCode (node_modules/jest-runtime/build/index.js:1350:14)
```

**Handling**:
```python
if 'Test suite failed to run' in output:
    # Extract syntax error details
    error_match = re.search(r'(SyntaxError|TypeError|ReferenceError):\s*(.+)', output)
    if error_match:
        return {
            'framework': 'jest',
            'exit_code': 1,
            'failed_count': 1,
            'error_type': error_match.group(1),
            'error_message': error_match.group(2),
            'recommendation': 'Fix syntax errors in test files'
        }
```

### Timeout

**Pattern**:
```
Exceeded timeout of 5000 ms for a test.
```

**Handling**:
```python
if 'Exceeded timeout' in output:
    timeout_match = re.search(r'Exceeded timeout of (\d+) ms', output)
    timeout_ms = timeout_match.group(1) if timeout_match else 'unknown'

    return {
        'error': f'Test timeout ({timeout_ms} ms)',
        'recommendation': 'Increase timeout in jest.config.js or fix hanging async operations'
    }
```

## Integration with Parser Factory

### Auto-Registration

File naming convention: `jest-parser.md` → Auto-discovered by parser factory

**Verification**:
```python
# Parser factory will import and register this parser
assert JestParser in parser_factory.registered_parsers
assert parser_factory.get_parser(framework="jest") == JestParser
```

### Framework Hints

```python
# Parser factory maps these to JestParser
parser_factory.framework_hints["jest"] = ["jest"]
```

### Output Signature Detection

```python
# If framework unknown, factory uses output patterns
if parser_factory.auto_detect_framework(command="npm test", output=jest_output) == "jest":
    parser = parser_factory.get_parser(framework="jest")
```

## Example Usage

### Parse Successful Test Run

```python
execution_result = {
    'command': 'npm test',
    'exit_code': 0,
    'stdout': '''
        PASS  src/__tests__/calculator.test.js
          ✓ adds two numbers (3 ms)
          ✓ subtracts two numbers (1 ms)

        Test Suites: 1 passed, 1 total
        Tests:       2 passed, 2 total
        Time:        1.234 s
    ''',
    'stderr': '',
    'duration': 1.234
}

parser = JestParser()
result = parser.parse(execution_result)

assert result['passed_count'] == 2
assert result['failed_count'] == 0
assert result['total_count'] == 2
assert result['exit_code'] == 0
```

### Parse Failed Test Run

```python
execution_result = {
    'command': 'npm test',
    'exit_code': 1,
    'stdout': '''
        FAIL  src/__tests__/api.test.js
          ✕ handles errors correctly (12 ms)

          ● handles errors correctly

            expect(received).toBe(expected)
            Expected: 404
            Received: 500

              at Object.<anonymous> (src/__tests__/api.test.js:14:26)

        Tests:       1 failed, 1 total
    ''',
    'stderr': '',
    'duration': 0.512
}

result = parser.parse(execution_result)

assert result['failed_count'] == 1
assert len(result['failures']) == 1
assert result['failures'][0]['test_file'] == 'src/__tests__/api.test.js'
assert result['failures'][0]['line_number'] == 14
assert result['failures'][0]['expected'] == '404'
assert result['failures'][0]['received'] == '500'
```

## Testing

### Test Cases

1. **Parse successful run**: All tests pass
2. **Parse failures**: Multiple test failures with different error types
3. **Parse coverage**: Coverage table with multiple files
4. **Parse skipped tests**: Tests marked as skipped
5. **Handle no tests**: No tests found error
6. **Handle syntax errors**: Test file has syntax error
7. **Handle timeout**: Test exceeds timeout
8. **Handle jest not found**: Jest not installed

### Validation

```python
def test_jest_parser():
    parser = JestParser()

    # Test can_parse
    assert parser.can_parse("jest", "")
    assert parser.can_parse("", "Test Suites: 1 passed")
    assert not parser.can_parse("pytest", "")

    # Test parse
    result = parser.parse(sample_jest_output)
    assert result['framework'] == 'jest'
    assert result['passed_count'] > 0
    assert 'failures' in result or result['failed_count'] == 0
```

## References

- Jest CLI Output: https://jestjs.io/docs/cli
- Jest Configuration: https://jestjs.io/docs/configuration
- Parser Factory Pattern: `skills/result-parsing/parser-factory-pattern.md`
- Base Parser Interface: `skills/result-parsing/base-parser-interface.md`
- pytest Parser (reference): `skills/result-parsing/parsers/pytest-parser.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
