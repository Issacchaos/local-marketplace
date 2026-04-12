# Vitest Result Parser

**Version**: 1.0.0
**Framework**: Vitest
**Languages**: JavaScript, TypeScript
**Purpose**: Parse Vitest test execution output to extract test results, failures, and coverage

## Overview

The Vitest Result Parser processes Vitest test runner output. Vitest is highly compatible with Jest but uses different output formatting with Unicode symbols and colored output. This parser implements the BaseTestParser interface and auto-registers with the parser factory.

## Vitest Output Format

### Summary Line

```
✓ src/calculator.test.ts (2 tests) 234ms
✓ src/api.test.ts (3 tests | 1 skipped) 145ms

Test Files  2 passed (2)
     Tests  4 passed | 1 skipped (5)
  Start at  10:23:45
  Duration  1.23s
```

### Test Results

```
 ✓ src/calculator.test.ts (2)
   ✓ Calculator > adds two numbers 3ms
   ✓ Calculator > subtracts two numbers 1ms

 ✗ src/api.test.ts (2) 145ms
   ✓ API Client > fetches data successfully 45ms
   ✗ API Client > handles errors correctly 12ms
     AssertionError: expected 500 to equal 404

      ❯ src/api.test.ts:14:26
         12|   it('handles errors correctly', () => {
         13|     const error = getError();
         14|     expect(error.status).toBe(404);
            |                          ^
         15|   });
```

### Coverage Output

Similar to Jest, Vitest uses Istanbul/c8 for coverage:

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

```python
def can_parse(framework: str, output: str) -> bool:
    """Check if this parser can handle Vitest output."""

    # Check framework name
    if framework and framework.lower() in ["vitest"]:
        return True

    # Check output signatures (Vitest-specific)
    vitest_signatures = [
        r'Test Files\s+\d+',                 # "Test Files  2 passed"
        r'✓.*\.test\.(ts|js)',                # Checkmark with test file
        r'✗.*\.test\.(ts|js)',                # X mark with test file
        r'Duration\s+[\d.]+s',                # Duration line
    ]

    for pattern in vitest_signatures:
        if re.search(pattern, output, re.MULTILINE):
            return True

    return False
```

### parse(execution_result) → ParsedTestResult

```python
def parse(execution_result):
    """Parse Vitest output into structured result."""
    output = execution_result['stdout'] + execution_result['stderr']

    result = {
        'framework': 'vitest',
        'exit_code': execution_result['exit_code'],
        'duration': execution_result.get('duration', 0),
        'raw_output': output
    }

    # Extract test counts from "Tests" line
    counts = extract_test_counts(output)
    result.update(counts)

    # Extract failures
    if result['failed_count'] > 0:
        result['failures'] = extract_failures(output)

    # Extract coverage (if present)
    if '--coverage' in execution_result.get('command', ''):
        result['coverage'] = extract_coverage(output)  # Same as Jest

    return result
```

## Extraction Methods

### extract_test_counts(output: str) → dict

Vitest summary format:
```
Tests  4 passed | 1 skipped (5)
```

```python
def extract_test_counts(output):
    """Extract test counts from Vitest summary."""
    counts = {
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'total_count': 0
    }

    # Find "Tests" summary line
    pattern = r'Tests\s+(.*?)\((\d+)\)'
    match = re.search(pattern, output, re.MULTILINE)

    if not match:
        return counts

    summary = match.group(1)
    total = int(match.group(2))
    counts['total_count'] = total

    # Parse summary: "4 passed | 1 skipped" or "2 failed | 3 passed"
    parts = summary.split('|')
    for part in parts:
        part = part.strip()

        # Passed: "4 passed"
        passed_match = re.search(r'(\d+)\s+passed', part)
        if passed_match:
            counts['passed_count'] = int(passed_match.group(1))

        # Failed: "2 failed"
        failed_match = re.search(r'(\d+)\s+failed', part)
        if failed_match:
            counts['failed_count'] = int(failed_match.group(1))

        # Skipped: "1 skipped"
        skipped_match = re.search(r'(\d+)\s+skipped', part)
        if skipped_match:
            counts['skipped_count'] = int(skipped_match.group(1))

    return counts
```

### extract_failures(output: str) → list[dict]

Vitest failure format:
```
 ✗ API Client > handles errors correctly 12ms
   AssertionError: expected 500 to equal 404

    ❯ src/api.test.ts:14:26
       12|   it('handles errors correctly', () => {
       13|     const error = getError();
       14|     expect(error.status).toBe(404);
          |                          ^
       15|   });
```

```python
def extract_failures(output):
    """Extract detailed failure information from Vitest output."""
    failures = []

    # Split output into test file sections
    # Pattern: ✗ file.test.ts
    file_pattern = r'✗\s+(.+?\.test\.(ts|js|jsx|tsx))\s*\(.*?\)\s*\n(.*?)(?=✓|✗|\Z)'
    file_matches = re.finditer(file_pattern, output, re.DOTALL | re.MULTILINE)

    for file_match in file_matches:
        test_file = file_match.group(1).strip()
        file_content = file_match.group(3)

        # Find individual failures within file
        # Pattern: ✗ Test Name
        failure_pattern = r'✗\s+(.+?)\s+\d+ms\n\s+(.*?)(?=✓|✗|\Z)'
        failure_matches = re.finditer(failure_pattern, file_content, re.DOTALL)

        for failure_match in failure_matches:
            test_name = failure_match.group(1).strip()
            failure_body = failure_match.group(2)

            failure = {
                'test_name': test_name,
                'test_file': test_file,
                'line_number': None,
                'error_type': 'AssertionError',
                'error_message': None,
                'stack_trace': None
            }

            # Extract error message (first line)
            error_lines = failure_body.strip().split('\n')
            if error_lines:
                error_line = error_lines[0].strip()
                # Parse "AssertionError: expected 500 to equal 404"
                if ':' in error_line:
                    error_type, error_msg = error_line.split(':', 1)
                    failure['error_type'] = error_type.strip()
                    failure['error_message'] = error_msg.strip()
                else:
                    failure['error_message'] = error_line

            # Extract file location
            # Pattern: ❯ src/api.test.ts:14:26
            location_pattern = r'❯\s+(.+?):(\d+):\d+'
            location_match = re.search(location_pattern, failure_body)

            if location_match:
                failure['test_file'] = location_match.group(1)
                failure['line_number'] = int(location_match.group(2))

            # Extract stack trace (everything after ❯)
            stack_start = failure_body.find('❯')
            if stack_start != -1:
                failure['stack_trace'] = failure_body[stack_start:]

            failures.append(failure)

    return failures
```

## Error Handling

### No Tests Found

```
No test files found, exiting with code 1
```

```python
if 'No test files found' in output:
    return {
        'framework': 'vitest',
        'exit_code': 1,
        'passed_count': 0,
        'failed_count': 0,
        'total_count': 0,
        'error': 'No test files found',
        'recommendation': 'Verify test file patterns in vitest.config.ts'
    }
```

### Vitest Not Installed

```
sh: vitest: command not found
```

```python
if 'vitest: command not found' in output:
    return {
        'framework': 'vitest',
        'exit_code': 127,
        'error': 'Vitest not installed',
        'recommendation': 'Run: npm install --save-dev vitest'
    }
```

## Integration with Parser Factory

**Auto-Registration**: File `vitest-parser.md` → Auto-discovered

**Framework Hints**:
```python
parser_factory.framework_hints["vitest"] = ["vitest"]
```

**Note**: Jest compatibility mode (with `globals: true` in vitest.config.ts) may make output look like Jest. Parser factory will prefer Vitest if "vitest" is explicitly in the command or config.

## Example Usage

```python
execution_result = {
    'command': 'vitest run',
    'exit_code': 0,
    'stdout': '''
        ✓ src/calculator.test.ts (2 tests) 234ms

        Test Files  1 passed (1)
             Tests  2 passed (2)
          Duration  0.234s
    ''',
    'stderr': '',
    'duration': 0.234
}

parser = VitestParser()
result = parser.parse(execution_result)

assert result['passed_count'] == 2
assert result['failed_count'] == 0
assert result['framework'] == 'vitest'
```

## Key Differences from Jest

1. **Symbols**: Vitest uses ✓ and ✗ (Unicode checkmark and X) instead of PASS/FAIL text
2. **Summary Format**: `Tests 4 passed | 1 skipped (5)` vs Jest's `Tests: 4 passed, 1 skipped, 5 total`
3. **Failure Marker**: ❯ (arrow) for stack traces instead of Jest's "at"
4. **Test Grouping**: Uses `>` separator (e.g., "Calculator > adds") more prominently

## References

- Vitest CLI: https://vitest.dev/guide/cli.html
- Vitest Configuration: https://vitest.dev/config/
- Jest Parser (reference): `skills/result-parsing/parsers/jest-parser.md`
- Parser Factory: `skills/result-parsing/parser-factory-pattern.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
