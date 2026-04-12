# Mocha Result Parser

**Version**: 1.0.0
**Framework**: Mocha
**Languages**: JavaScript, TypeScript
**Purpose**: Parse Mocha test execution output to extract test results and failures

## Overview

The Mocha Result Parser processes Mocha test runner output using the spec reporter (default). Mocha is minimalist and flexible, with no built-in assertions or mocking. This parser implements the BaseTestParser interface and auto-registers with the parser factory.

## Mocha Output Format

### Spec Reporter (Default)

```
  Calculator
    ✓ adds two numbers (3ms)
    ✓ subtracts two numbers (1ms)
    ✓ multiplies two numbers
    1) divides two numbers


  API Client
    ✓ fetches data successfully (45ms)
    2) handles errors correctly


  3 passing (150ms)
  2 failing

  1) Calculator
       divides two numbers:
     AssertionError: expected 2 to equal 3
      at Context.<anonymous> (test/calculator.test.js:15:26)
      at processImmediate (internal/timers.js:464:21)

  2) API Client
       handles errors correctly:
     Error: Expected status 404 but got 500
      at Context.<anonymous> (test/api.test.js:12:15)
```

### Summary Line

```
  5 passing (234ms)
  2 failing
  1 pending
```

## Parser Interface Implementation

### can_parse(framework: str, output: str) → bool

```python
def can_parse(framework: str, output: str) -> bool:
    """Check if this parser can handle Mocha output."""

    # Check framework name
    if framework and framework.lower() in ["mocha", "mochajs"]:
        return True

    # Check output signatures (Mocha-specific)
    mocha_signatures = [
        r'\d+\s+passing',                    # "3 passing (150ms)"
        r'\d+\s+failing',                    # "2 failing"
        r'\d+\s+pending',                    # "1 pending"
        r'\d+\)\s+\w+',                      # "1) Calculator" (failure list)
    ]

    for pattern in mocha_signatures:
        if re.search(pattern, output, re.MULTILINE):
            return True

    return False
```

### parse(execution_result) → ParsedTestResult

```python
def parse(execution_result):
    """Parse Mocha output into structured result."""
    output = execution_result['stdout'] + execution_result['stderr']

    result = {
        'framework': 'mocha',
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

    return result
```

## Extraction Methods

### extract_test_counts(output: str) → dict

Mocha summary format:
```
  5 passing (234ms)
  2 failing
  1 pending
```

```python
def extract_test_counts(output):
    """Extract test counts from Mocha summary."""
    counts = {
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,  # "pending" in Mocha
        'total_count': 0
    }

    # Passing: "5 passing (234ms)" or "5 passing"
    passed_pattern = r'(\d+)\s+passing'
    passed_match = re.search(passed_pattern, output, re.MULTILINE)
    if passed_match:
        counts['passed_count'] = int(passed_match.group(1))

    # Failing: "2 failing"
    failed_pattern = r'(\d+)\s+failing'
    failed_match = re.search(failed_pattern, output, re.MULTILINE)
    if failed_match:
        counts['failed_count'] = int(failed_match.group(1))

    # Pending (skipped): "1 pending"
    pending_pattern = r'(\d+)\s+pending'
    pending_match = re.search(pending_pattern, output, re.MULTILINE)
    if pending_match:
        counts['skipped_count'] = int(pending_match.group(1))

    # Calculate total
    counts['total_count'] = (counts['passed_count'] +
                            counts['failed_count'] +
                            counts['skipped_count'])

    return counts
```

### extract_failures(output: str) → list[dict]

Mocha failure format:
```
  1) Calculator
       divides two numbers:
     AssertionError: expected 2 to equal 3
      at Context.<anonymous> (test/calculator.test.js:15:26)
      at processImmediate (internal/timers.js:464:21)

  2) API Client
       handles errors correctly:
     Error: Expected status 404 but got 500
      at Context.<anonymous> (test/api.test.js:12:15)
```

```python
def extract_failures(output):
    """Extract detailed failure information from Mocha output."""
    failures = []

    # Split output into failure blocks
    # Pattern: 1) Suite name
    #             test name:
    #          Error message
    #           at ...
    failure_pattern = r'(\d+)\)\s+(.+?)\n\s+(.+?):\n\s+(.*?)(?=\n\s+\d+\)|\Z)'
    matches = re.finditer(failure_pattern, output, re.DOTALL | re.MULTILINE)

    for match in matches:
        failure_num = match.group(1)
        suite_name = match.group(2).strip()
        test_name = match.group(3).strip()
        failure_body = match.group(4)

        failure = {
            'test_name': f"{suite_name} > {test_name}",
            'test_file': None,
            'line_number': None,
            'error_type': 'Error',
            'error_message': None,
            'stack_trace': None
        }

        # Extract error message (first line of failure body)
        error_lines = failure_body.strip().split('\n')
        if error_lines:
            error_line = error_lines[0].strip()

            # Parse error type and message
            # "AssertionError: expected 2 to equal 3"
            # "Error: Expected status 404 but got 500"
            if ':' in error_line:
                error_type, error_msg = error_line.split(':', 1)
                failure['error_type'] = error_type.strip()
                failure['error_message'] = error_msg.strip()
            else:
                failure['error_message'] = error_line

        # Extract file location from stack trace
        # Pattern: at Context.<anonymous> (test/calculator.test.js:15:26)
        location_pattern = r'at\s+.*?\((.+?):(\d+):\d+\)'
        location_match = re.search(location_pattern, failure_body)

        if location_match:
            failure['test_file'] = location_match.group(1)
            failure['line_number'] = int(location_match.group(2))

        # Extract full stack trace (lines starting with "at")
        stack_lines = []
        for line in error_lines[1:]:  # Skip first line (error message)
            stripped = line.strip()
            if stripped.startswith('at '):
                stack_lines.append(stripped)

        if stack_lines:
            failure['stack_trace'] = '\n'.join(stack_lines)

        failures.append(failure)

    return failures
```

## Error Handling

### No Tests Found

```
  0 passing (1ms)

Error: No test files found
```

```python
if '0 passing' in output and 'No test files found' in output:
    return {
        'framework': 'mocha',
        'exit_code': 1,
        'passed_count': 0,
        'failed_count': 0,
        'total_count': 0,
        'error': 'No test files found',
        'recommendation': 'Verify test file paths in .mocharc.json or mocha command'
    }
```

### Mocha Not Installed

```
sh: mocha: command not found
```

```python
if 'mocha: command not found' in output:
    return {
        'framework': 'mocha',
        'exit_code': 127,
        'error': 'Mocha not installed',
        'recommendation': 'Run: npm install --save-dev mocha'
    }
```

### Assertion Library Missing

Mocha has no built-in assertions, so common error:

```
ReferenceError: expect is not defined
```

```python
if 'expect is not defined' in output or 'assert is not defined' in output:
    return {
        'framework': 'mocha',
        'exit_code': 1,
        'error': 'No assertion library found',
        'recommendation': 'Install assertion library: npm install --save-dev chai\n' +
                         'Or use Node.js built-in: const assert = require("assert")'
    }
```

### Test Timeout

```
  1) Calculator
       long running test:
     Error: Timeout of 2000ms exceeded
      at Timeout.<anonymous> (...)
```

```python
if 'Timeout of' in output and 'exceeded' in output:
    timeout_match = re.search(r'Timeout of (\d+)ms exceeded', output)
    timeout_ms = timeout_match.group(1) if timeout_match else 'unknown'

    return {
        'error': f'Test timeout ({timeout_ms} ms)',
        'recommendation': 'Increase timeout in .mocharc.json or use this.timeout() in test'
    }
```

## Reporter Variants

Mocha supports multiple reporters. This parser focuses on **spec** (default), but can handle others:

### spec (default)

```
  ✓ test name
  1) failing test
```

### dot

```
  ..✓.✗
```

**Detection**: Not ideal for parsing. Recommend spec reporter.

### json

```json
{
  "stats": {
    "suites": 2,
    "tests": 5,
    "passes": 3,
    "failures": 2
  },
  "failures": [...]
}
```

**Note**: If JSON output detected, parse as JSON instead of text.

```python
def parse_json_output(output):
    """Parse Mocha JSON reporter output."""
    try:
        data = json.loads(output)
        return {
            'framework': 'mocha',
            'passed_count': data['stats']['passes'],
            'failed_count': data['stats']['failures'],
            'skipped_count': data['stats']['pending'],
            'total_count': data['stats']['tests'],
            'failures': parse_json_failures(data['failures'])
        }
    except json.JSONDecodeError:
        # Fall back to text parsing
        return parse_text_output(output)
```

## Integration with Parser Factory

**Auto-Registration**: File `mocha-parser.md` → Auto-discovered

**Framework Hints**:
```python
parser_factory.framework_hints["mocha"] = ["mocha", "mochajs"]
```

## Example Usage

### Successful Run

```python
execution_result = {
    'command': 'mocha test/',
    'exit_code': 0,
    'stdout': '''
      Calculator
        ✓ adds two numbers (3ms)
        ✓ subtracts two numbers (1ms)

      2 passing (8ms)
    ''',
    'stderr': '',
    'duration': 0.008
}

parser = MochaParser()
result = parser.parse(execution_result)

assert result['passed_count'] == 2
assert result['failed_count'] == 0
assert result['framework'] == 'mocha'
```

### Failed Run

```python
execution_result = {
    'command': 'mocha test/',
    'exit_code': 1,
    'stdout': '''
      Calculator
        ✓ adds two numbers
        1) divides by zero

      1 passing (5ms)
      1 failing

      1) Calculator
           divides by zero:
         AssertionError: expected undefined to equal Infinity
          at Context.<anonymous> (test/calc.test.js:10:28)
    ''',
    'stderr': '',
    'duration': 0.005
}

result = parser.parse(execution_result)

assert result['failed_count'] == 1
assert len(result['failures']) == 1
assert 'divides by zero' in result['failures'][0]['test_name']
assert result['failures'][0]['test_file'] == 'test/calc.test.js'
assert result['failures'][0]['line_number'] == 10
```

## Key Differences from Jest/Vitest

1. **No Built-in Assertions**: Mocha requires external assertion library (Chai, expect.js, Node assert)
2. **Simple Summary**: Just "X passing, Y failing, Z pending" (no "Test Suites" concept)
3. **Numbered Failures**: Failures listed as "1)", "2)", etc., not with test file names prominently
4. **Stack Traces**: Simpler format, less Jest-specific formatting
5. **Pending vs Skipped**: Mocha uses "pending" for skipped tests
6. **No Coverage**: Mocha doesn't include coverage (use nyc/istanbul separately)

## References

- Mocha Documentation: https://mochajs.org/
- Mocha Reporters: https://mochajs.org/#reporters
- Chai Assertions: https://www.chaijs.com/ (common with Mocha)
- Jest Parser (reference): `skills/result-parsing/parsers/jest-parser.md`
- Parser Factory: `skills/result-parsing/parser-factory-pattern.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
