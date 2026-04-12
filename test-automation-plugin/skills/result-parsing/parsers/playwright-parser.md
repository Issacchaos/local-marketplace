# Playwright Result Parser

**Version**: 1.0.0
**Framework**: Playwright (@playwright/test)
**Languages**: JavaScript, TypeScript
**Purpose**: Parse Playwright test execution output to extract test results, failures, and coverage

## Overview

The Playwright Result Parser processes Playwright Test runner output to extract structured test results including pass/fail counts, individual test failures with browser tags and locations, error messages with call logs, retry indicators, and optional Istanbul coverage data. This parser implements the BaseTestParser interface and auto-registers with the parser factory.

## Playwright Output Format

### Summary Line

```
  8 passed (12.3s)
```

Or with failures and skips:

```
  2 failed
  1 skipped
  5 passed (15.7s)
```

### Test Results (list reporter)

```
Running 8 tests using 4 workers

  ✓  1 [chromium] > tests/home.spec.ts:5:5 > Home page > should display title (1.2s)
  ✓  2 [chromium] > tests/home.spec.ts:12:5 > Home page > should have navigation (856ms)
  ✓  3 [firefox] > tests/home.spec.ts:5:5 > Home page > should display title (2.1s)
  ✗  4 [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials (3.4s)
  -  5 [webkit] > tests/dashboard.spec.ts:15:5 > Dashboard > should load widgets
  ✓  6 [chromium] > tests/search.spec.ts:5:5 > Search > should return results (1.8s)

  1) [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials

    Error: expect(received).toHaveText(expected)

    Expected string: "Invalid credentials"
    Received string: "Login failed"

    Call log:
      - expect.toHaveText with timeout 5000ms
      - waiting for locator('.error-message')
      -   locator resolved to <div class="error-message">Login failed</div>
      -   unexpected value "Login failed"

       8 |   test('should reject invalid credentials', async ({ page }) => {
       9 |     await page.fill('#username', 'baduser');
      10 |     await page.fill('#password', 'badpass');
      11 |     await page.click('button[type="submit"]');
    > 12 |     await expect(page.locator('.error-message')).toHaveText('Invalid credentials');
         |                                                  ^
      13 |   });
      14 | });

        at tests/login.spec.ts:12:50
```

### Timeout Output

```
  1) [chromium] > tests/checkout.spec.ts:20:5 > Checkout > should complete purchase

    Test timeout of 30000ms exceeded.

    Error: locator.click: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator('button.checkout-submit')
      -   locator resolved to 0 elements

       20 |   test('should complete purchase', async ({ page }) => {
       21 |     await page.goto('/cart');
    >  22 |     await page.locator('button.checkout-submit').click();
          |                                                  ^
       23 |     await expect(page).toHaveURL('/order-confirmation');
       24 |   });

        at tests/checkout.spec.ts:22:50
```

### Retry Output

```
  ✗  4 [chromium] > tests/flaky.spec.ts:5:5 > Flaky test > sometimes fails (Retry #1) (2.1s)
  ✓  4 [chromium] > tests/flaky.spec.ts:5:5 > Flaky test > sometimes fails (Retry #2) (1.8s)
```

### Coverage Output (Istanbul via --coverage or custom reporter)

```
------------|---------|----------|---------|---------|-------------------
File        | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
------------|---------|----------|---------|---------|-------------------
All files   |   78.43 |    62.50 |   71.42 |   78.43 |
 src/app    |   85.00 |    75.00 |   80.00 |   85.00 |
  index.ts  |   90.00 |    80.00 |     100 |   90.00 | 15-18
  utils.ts  |   80.00 |    70.00 |   60.00 |   80.00 | 22-30,45
 src/pages  |   70.00 |    50.00 |   60.00 |   70.00 |
  home.ts   |   70.00 |    50.00 |   60.00 |   70.00 | 8-12,25-28
------------|---------|----------|---------|---------|-------------------
```

## Parser Interface Implementation

### can_parse(framework: str, output: str) -> bool

Determines if this parser can handle the given framework/output.

**Implementation**:
```python
def can_parse(framework: str, output: str) -> bool:
    """
    Check if this parser can handle Playwright output.

    Args:
        framework: Framework name hint (e.g., "playwright")
        output: Test execution output string

    Returns:
        True if this parser can handle the output
    """
    # Check framework name
    if framework and framework.lower() in ["playwright"]:
        return True

    # Check output signatures
    playwright_signatures = [
        r"Running \d+ tests? using \d+ workers?",  # Test run header
        r"\[chromium\]",                             # Browser tag: Chromium
        r"\[firefox\]",                              # Browser tag: Firefox
        r"\[webkit\]",                               # Browser tag: WebKit
        r"npx playwright test",                      # Command echo
    ]

    for pattern in playwright_signatures:
        if re.search(pattern, output, re.MULTILINE):
            return True

    return False
```

### parse(execution_result) -> ParsedTestResult

Parses Playwright output into structured result object.

**Input** (execution_result):
```python
{
    'command': 'npx playwright test --reporter=list',
    'exit_code': 1,              # 0 = pass, 1 = failures
    'stdout': '...',             # Playwright output
    'stderr': '...',             # Errors
    'duration': 15.7             # Seconds
}
```

**Output** (ParsedTestResult):
```python
{
    'framework': 'playwright',
    'exit_code': 1,
    'passed_count': 5,
    'failed_count': 2,
    'skipped_count': 1,
    'total_count': 8,
    'duration': 15.7,
    'failures': [
        {
            'test_name': 'Login > should reject invalid credentials',
            'test_file': 'tests/login.spec.ts',
            'line_number': 12,
            'browser': 'chromium',
            'error_type': 'AssertionError',
            'error_message': 'expect(received).toHaveText(expected)',
            'expected': '"Invalid credentials"',
            'received': '"Login failed"',
            'call_log': '...',
            'stack_trace': '...',
            'timeout': False,
            'retry_number': None
        }
    ],
    'coverage': None,
    'raw_output': '...'
}
```

**Implementation**:
```python
def parse(execution_result):
    output = execution_result['stdout'] + execution_result['stderr']

    result = {
        'framework': 'playwright',
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

    # Extract coverage (Istanbul, if present)
    result['coverage'] = extract_coverage(output)

    return result
```

## Extraction Methods

### extract_test_counts(output: str) -> dict

Extracts pass/fail/skip counts from Playwright summary.

**Pattern**:
```
  2 failed
  1 skipped
  5 passed (15.7s)
```

Or all passing:
```
  8 passed (12.3s)
```

**Implementation**:
```python
def extract_test_counts(output):
    """
    Extract test counts from Playwright summary lines.

    Playwright prints each count on a separate line:
      X failed
      Y skipped
      Z passed (duration)
    """
    counts = {
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'total_count': 0
    }

    # Extract failed count: "X failed"
    failed_match = re.search(r'(\d+)\s+failed', output)
    if failed_match:
        counts['failed_count'] = int(failed_match.group(1))

    # Extract skipped count: "X skipped"
    skipped_match = re.search(r'(\d+)\s+skipped', output)
    if skipped_match:
        counts['skipped_count'] = int(skipped_match.group(1))

    # Extract passed count: "X passed"
    passed_match = re.search(r'(\d+)\s+passed', output)
    if passed_match:
        counts['passed_count'] = int(passed_match.group(1))

    # Calculate total
    counts['total_count'] = (
        counts['passed_count'] +
        counts['failed_count'] +
        counts['skipped_count']
    )

    # Extract total duration from "X passed (Ys)" or last line with duration
    duration_match = re.search(r'passed\s+\(([\d.]+)s\)', output)
    if duration_match:
        counts['duration'] = float(duration_match.group(1))

    return counts
```

### extract_per_test_results(output: str) -> list[dict]

Extracts individual test results with browser tags and durations from the list reporter output.

**Pattern**:
```
  ✓  1 [chromium] > tests/home.spec.ts:5:5 > Home page > should display title (1.2s)
  ✗  4 [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials (3.4s)
  -  5 [webkit] > tests/dashboard.spec.ts:15:5 > Dashboard > should load widgets
```

**Implementation**:
```python
def extract_per_test_results(output):
    """
    Extract individual test results from Playwright list reporter output.

    Each line follows the pattern:
      STATUS  NUM [browser] > file:line:col > Suite > test name (duration)

    Status markers:
      ✓ = passed
      ✗ = failed
      - = skipped
    """
    results = []

    # Pattern: status marker, number, [browser], file:line:col, test path, optional duration
    pattern = (
        r'^\s*([✓✗\-])\s+\d+\s+'            # Status marker and test number
        r'\[(\w+)\]\s+>\s+'                    # Browser tag [chromium/firefox/webkit]
        r'(.+?):(\d+):\d+\s+>\s+'             # File path and line number
        r'(.+?)'                               # Test name (suite > test)
        r'(?:\s+\(Retry #(\d+)\))?'            # Optional retry indicator
        r'(?:\s+\(([\d.]+(?:ms|s))\))?'        # Optional duration
        r'\s*$'
    )

    for match in re.finditer(pattern, output, re.MULTILINE):
        status_marker = match.group(1)
        browser = match.group(2)
        test_file = match.group(3)
        line_number = int(match.group(4))
        test_name = match.group(5).strip()
        retry_number = int(match.group(6)) if match.group(6) else None
        duration_str = match.group(7)

        # Parse duration to seconds
        duration = None
        if duration_str:
            if duration_str.endswith('ms'):
                duration = float(duration_str[:-2]) / 1000
            elif duration_str.endswith('s'):
                duration = float(duration_str[:-1])

        # Map status marker to result
        if status_marker == '✓':
            status = 'passed'
        elif status_marker == '✗':
            status = 'failed'
        else:
            status = 'skipped'

        results.append({
            'test_name': test_name,
            'test_file': test_file,
            'line_number': line_number,
            'browser': browser,
            'status': status,
            'duration': duration,
            'retry_number': retry_number
        })

    return results
```

### extract_failures(output: str) -> list[dict]

Extracts individual test failure details including call logs and retry indicators.

**Pattern**:
```
  1) [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials

    Error: expect(received).toHaveText(expected)

    Expected string: "Invalid credentials"
    Received string: "Login failed"

    Call log:
      - expect.toHaveText with timeout 5000ms
      - waiting for locator('.error-message')
      -   locator resolved to <div class="error-message">Login failed</div>
      -   unexpected value "Login failed"

       8 |   test('should reject invalid credentials', async ({ page }) => {
       9 |     await page.fill('#username', 'baduser');
      10 |     await page.fill('#password', 'badpass');
      11 |     await page.click('button[type="submit"]');
    > 12 |     await expect(page.locator('.error-message')).toHaveText('Invalid credentials');
         |                                                  ^
      13 |   });
      14 | });

        at tests/login.spec.ts:12:50
```

**Implementation**:
```python
def extract_failures(output):
    """
    Extract detailed failure information from Playwright output.

    Each failure block starts with a numbered header:
      N) [browser] > file:line:col > Suite > test name

    And contains:
    - Error message
    - Expected/Received values
    - Call log (Playwright-specific action trace)
    - Code snippet with pointer
    - Stack trace with file:line
    - Timeout indicator (if applicable)
    - Retry indicator (if applicable)
    """
    failures = []

    # Split output into failure blocks
    # Pattern: numbered failure header
    failure_header_pattern = (
        r'^\s*(\d+)\)\s+'                     # Failure number
        r'\[(\w+)\]\s+>\s+'                    # Browser tag
        r'(.+?):(\d+):\d+\s+>\s+'             # File:line
        r'(.+?)\s*$'                           # Test name
    )

    # Find all failure headers and their positions
    headers = list(re.finditer(failure_header_pattern, output, re.MULTILINE))

    for i, header in enumerate(headers):
        browser = header.group(2)
        test_file = header.group(3)
        line_number = int(header.group(4))
        test_name = header.group(5).strip()

        # Extract failure body (content between this header and the next, or end)
        start = header.end()
        if i + 1 < len(headers):
            end = headers[i + 1].start()
        else:
            # End at summary line or end of output
            summary_match = re.search(r'^\s+\d+\s+(?:failed|passed|skipped)', output[start:], re.MULTILINE)
            end = start + summary_match.start() if summary_match else len(output)

        failure_body = output[start:end]

        failure = {
            'test_name': test_name,
            'test_file': test_file,
            'line_number': line_number,
            'browser': browser,
            'error_type': None,
            'error_message': None,
            'expected': None,
            'received': None,
            'call_log': None,
            'stack_trace': None,
            'timeout': False,
            'retry_number': None
        }

        # Check for timeout indicator
        timeout_match = re.search(r'Test timeout of (\d+)ms exceeded', failure_body)
        if timeout_match:
            failure['timeout'] = True
            failure['error_message'] = f'Test timeout of {timeout_match.group(1)}ms exceeded'

        # Extract error message (first "Error:" line)
        error_match = re.search(r'Error:\s*(.+)', failure_body)
        if error_match:
            failure['error_message'] = error_match.group(1).strip()

            # Classify error type from the error message
            if 'expect(' in failure['error_message']:
                failure['error_type'] = 'AssertionError'
            elif 'Timeout' in failure['error_message'] or 'timeout' in failure['error_message']:
                failure['error_type'] = 'TimeoutError'
            elif 'locator' in failure['error_message']:
                failure['error_type'] = 'LocatorError'
            else:
                failure['error_type'] = 'Error'

        # Extract Expected/Received values
        expected_match = re.search(r'Expected\s*(?:string|pattern|value)?:\s*(.+)', failure_body)
        if expected_match:
            failure['expected'] = expected_match.group(1).strip()

        received_match = re.search(r'Received\s*(?:string|pattern|value)?:\s*(.+)', failure_body)
        if received_match:
            failure['received'] = received_match.group(1).strip()

        # Extract Call log (Playwright-specific)
        call_log_match = re.search(
            r'Call log:\n((?:\s+-\s+.+\n?)+)',
            failure_body
        )
        if call_log_match:
            failure['call_log'] = call_log_match.group(1).strip()

        # Extract retry indicator
        retry_match = re.search(r'Retry #(\d+)', failure_body)
        if retry_match:
            failure['retry_number'] = int(retry_match.group(1))

        # Extract stack trace location
        # Pattern: at tests/login.spec.ts:12:50
        location_pattern = r'at\s+(.+?):(\d+):\d+'
        location_match = re.search(location_pattern, failure_body)
        if location_match:
            # Update file and line from stack trace (more precise)
            failure['test_file'] = location_match.group(1).strip()
            failure['line_number'] = int(location_match.group(2))

        # Extract full stack trace
        stack_start = failure_body.find('at ')
        if stack_start != -1:
            failure['stack_trace'] = failure_body[stack_start:].strip()

        failures.append(failure)

    return failures
```

### extract_coverage(output: str) -> dict

Extracts code coverage data if Istanbul output is present.

**Note**: Playwright does not include built-in code coverage reporting. However, projects may configure Istanbul (via `nyc` or `@playwright/test` coverage API with a custom reporter) to produce coverage output alongside Playwright test results. When Istanbul coverage is present in the output, this method parses it using the same table format as Jest's coverage output.

**Pattern** (Istanbul table, same as Jest):
```
------------|---------|----------|---------|---------|-------------------
File        | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
------------|---------|----------|---------|---------|-------------------
All files   |   78.43 |    62.50 |   71.42 |   78.43 |
 src/app    |   85.00 |    75.00 |   80.00 |   85.00 |
  index.ts  |   90.00 |    80.00 |     100 |   90.00 | 15-18
  utils.ts  |   80.00 |    70.00 |   60.00 |   80.00 | 22-30,45
------------|---------|----------|---------|---------|-------------------
```

**Implementation**:
```python
def extract_coverage(output):
    """
    Extract coverage data from Istanbul coverage table if present.

    Playwright has no built-in coverage reporter. If the project uses
    Istanbul (nyc, c8, or a custom Playwright coverage reporter),
    the coverage table will appear in the output in the same format
    as Jest's Istanbul coverage output.

    Returns:
        Coverage dict if Istanbul table is found, None otherwise.
        {
            'total_statements': 78.43,
            'total_branches': 62.50,
            'total_functions': 71.42,
            'total_lines': 78.43,
            'files': [
                {
                    'file': 'src/app/index.ts',
                    'statements': 90.0,
                    'branches': 80.0,
                    'functions': 100.0,
                    'lines': 90.0,
                    'uncovered_lines': [15, 16, 17, 18]
                },
                ...
            ],
            'coverage_tool': 'istanbul'
        }
    """
    coverage = {
        'total_statements': 0,
        'total_branches': 0,
        'total_functions': 0,
        'total_lines': 0,
        'files': [],
        'coverage_tool': 'istanbul'
    }

    # Find coverage table (Istanbul format)
    table_pattern = r'-+\|.*?\n(.*?)\n-+\|'
    table_match = re.search(table_pattern, output, re.DOTALL)

    if not table_match:
        return None  # No coverage data found

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
    Parse uncovered line ranges: '23-25,45' -> [23, 24, 25, 45]
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

### No Tests Found

**Pattern**:
```
Error: No tests found
```

Or:
```
=================
 no tests found
=================
```

**Handling**:
```python
if 'No tests found' in output or 'no tests found' in output:
    return {
        'framework': 'playwright',
        'exit_code': 1,
        'passed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'total_count': 0,
        'error': 'No tests found',
        'recommendation': 'Verify test file patterns in playwright.config.ts (testDir, testMatch)'
    }
```

### Playwright Not Installed

**Pattern**:
```
Error: Cannot find module '@playwright/test'
```

Or:
```
npx: command not found
```

**Handling**:
```python
if "Cannot find module '@playwright/test'" in output:
    return {
        'framework': 'playwright',
        'exit_code': 127,
        'error': 'Playwright not installed',
        'recommendation': 'Run: npm install --save-dev @playwright/test'
    }
```

### Browsers Not Installed

**Pattern**:
```
Error: browserType.launch: Executable doesn't exist at /path/to/chromium
╔════════════════════════════════════════════════════════════════╗
║ Looks like Playwright Test or Playwright was just installed   ║
║ or updated. Please run the following command to download      ║
║ new browsers:                                                 ║
║                                                               ║
║     npx playwright install                                    ║
║                                                               ║
╚════════════════════════════════════════════════════════════════╝
```

**Handling**:
```python
if "Executable doesn't exist" in output or 'npx playwright install' in output:
    return {
        'framework': 'playwright',
        'exit_code': 1,
        'error': 'Browsers not installed',
        'recommendation': 'Run: npx playwright install'
    }
```

### Syntax Errors in Tests

**Pattern**:
```
Error: TypeScript compilation error

tests/login.spec.ts:15:5 - error TS2304: Cannot find name 'loginHelper'.
```

**Handling**:
```python
if 'TypeScript compilation error' in output or 'SyntaxError' in output:
    # Extract syntax error details
    error_match = re.search(r'(SyntaxError|TypeError|ReferenceError|error TS\d+):\s*(.+)', output)
    if error_match:
        return {
            'framework': 'playwright',
            'exit_code': 1,
            'failed_count': 1,
            'error_type': error_match.group(1),
            'error_message': error_match.group(2),
            'recommendation': 'Fix syntax or type errors in test files'
        }
```

### Timeout

**Pattern**:
```
Test timeout of 30000ms exceeded.
```

Or action-level timeout:
```
Error: locator.click: Timeout 30000ms exceeded.
```

**Handling**:
```python
if 'Test timeout of' in output:
    timeout_match = re.search(r'Test timeout of (\d+)ms exceeded', output)
    timeout_ms = timeout_match.group(1) if timeout_match else 'unknown'

    return {
        'error': f'Test timeout ({timeout_ms} ms)',
        'recommendation': 'Increase timeout in playwright.config.ts or fix element selectors / waiting logic'
    }

if 'Timeout' in output and 'ms exceeded' in output:
    timeout_match = re.search(r'Timeout (\d+)ms exceeded', output)
    timeout_ms = timeout_match.group(1) if timeout_match else 'unknown'

    return {
        'error': f'Action timeout ({timeout_ms} ms)',
        'recommendation': 'Verify the element selector resolves and the element is actionable'
    }
```

### Web Server Startup Failure

**Pattern**:
```
Error: Timed out waiting 60000ms from config.webServer
```

**Handling**:
```python
if 'Timed out waiting' in output and 'config.webServer' in output:
    return {
        'framework': 'playwright',
        'exit_code': 1,
        'error': 'Web server failed to start',
        'recommendation': 'Check webServer config in playwright.config.ts; ensure the app starts within the configured timeout'
    }
```

## Integration with Parser Factory

### Auto-Registration

File naming convention: `playwright-parser.md` -> Auto-discovered by parser factory

**Verification**:
```python
# Parser factory will import and register this parser
assert PlaywrightParser in parser_factory.registered_parsers
assert parser_factory.get_parser(framework="playwright") == PlaywrightParser
```

### Framework Hints

```python
# Parser factory maps these to PlaywrightParser
parser_factory.framework_hints["playwright"] = ["playwright"]
```

### Output Signature Detection

```python
# If framework unknown, factory uses output patterns
if parser_factory.auto_detect_framework(command="npx playwright test", output=playwright_output) == "playwright":
    parser = parser_factory.get_parser(framework="playwright")
```

**Primary signatures**:
- `Running X tests using Y workers` -- Playwright test run header
- `[chromium]` / `[firefox]` / `[webkit]` -- Browser tags in test output

## Example Usage

### Parse Successful Test Run

```python
execution_result = {
    'command': 'npx playwright test --reporter=list',
    'exit_code': 0,
    'stdout': '''
        Running 3 tests using 2 workers

          ✓  1 [chromium] > tests/home.spec.ts:5:5 > Home page > should display title (1.2s)
          ✓  2 [chromium] > tests/home.spec.ts:12:5 > Home page > should have navigation (856ms)
          ✓  3 [chromium] > tests/search.spec.ts:5:5 > Search > should return results (1.8s)

          3 passed (4.1s)
    ''',
    'stderr': '',
    'duration': 4.1
}

parser = PlaywrightParser()
result = parser.parse(execution_result)

assert result['passed_count'] == 3
assert result['failed_count'] == 0
assert result['total_count'] == 3
assert result['exit_code'] == 0
```

### Parse Failed Test Run

```python
execution_result = {
    'command': 'npx playwright test --reporter=list',
    'exit_code': 1,
    'stdout': '''
        Running 3 tests using 2 workers

          ✓  1 [chromium] > tests/home.spec.ts:5:5 > Home page > should display title (1.2s)
          ✗  2 [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials (3.4s)
          ✓  3 [chromium] > tests/search.spec.ts:5:5 > Search > should return results (1.8s)

          1) [chromium] > tests/login.spec.ts:8:5 > Login > should reject invalid credentials

            Error: expect(received).toHaveText(expected)

            Expected string: "Invalid credentials"
            Received string: "Login failed"

            Call log:
              - expect.toHaveText with timeout 5000ms
              - waiting for locator('.error-message')

                at tests/login.spec.ts:12:50

          1 failed
          2 passed (5.2s)
    ''',
    'stderr': '',
    'duration': 5.2
}

result = parser.parse(execution_result)

assert result['failed_count'] == 1
assert result['passed_count'] == 2
assert len(result['failures']) == 1
assert result['failures'][0]['test_file'] == 'tests/login.spec.ts'
assert result['failures'][0]['line_number'] == 12
assert result['failures'][0]['browser'] == 'chromium'
assert result['failures'][0]['expected'] == '"Invalid credentials"'
assert result['failures'][0]['received'] == '"Login failed"'
assert result['failures'][0]['call_log'] is not None
```

### Parse Timeout Failure

```python
execution_result = {
    'command': 'npx playwright test --reporter=list',
    'exit_code': 1,
    'stdout': '''
        Running 1 test using 1 worker

          ✗  1 [chromium] > tests/checkout.spec.ts:20:5 > Checkout > should complete purchase (30.1s)

          1) [chromium] > tests/checkout.spec.ts:20:5 > Checkout > should complete purchase

            Test timeout of 30000ms exceeded.

            Error: locator.click: Timeout 30000ms exceeded.
            Call log:
              - waiting for locator('button.checkout-submit')
              -   locator resolved to 0 elements

                at tests/checkout.spec.ts:22:50

          1 failed (30.5s)
    ''',
    'stderr': '',
    'duration': 30.5
}

result = parser.parse(execution_result)

assert result['failed_count'] == 1
assert result['failures'][0]['timeout'] == True
assert 'timeout' in result['failures'][0]['error_message'].lower() or 'Timeout' in result['failures'][0]['error_message']
```

### Parse Retry Output

```python
execution_result = {
    'command': 'npx playwright test --reporter=list --retries=2',
    'exit_code': 0,
    'stdout': '''
        Running 2 tests using 1 worker

          ✗  1 [chromium] > tests/flaky.spec.ts:5:5 > Flaky test > sometimes fails (2.1s)
          ✓  1 [chromium] > tests/flaky.spec.ts:5:5 > Flaky test > sometimes fails (Retry #1) (1.8s)
          ✓  2 [chromium] > tests/home.spec.ts:5:5 > Home page > should display title (1.2s)

          2 passed (5.5s)
    ''',
    'stderr': '',
    'duration': 5.5
}

per_test = extract_per_test_results(execution_result['stdout'])

# First attempt failed
assert per_test[0]['status'] == 'failed'
assert per_test[0]['retry_number'] is None

# Retry #1 passed
assert per_test[1]['status'] == 'passed'
assert per_test[1]['retry_number'] == 1
```

## Testing

### Test Cases

1. **Parse successful run**: All tests pass across single browser
2. **Parse multi-browser run**: Tests pass across chromium, firefox, webkit
3. **Parse failures**: Multiple test failures with different error types
4. **Parse timeout**: Test timeout of Xms exceeded
5. **Parse retries**: Retry #1, Retry #2 indicators
6. **Parse skipped tests**: Tests marked as skipped
7. **Parse coverage**: Istanbul coverage table present in output
8. **Handle no tests**: No tests found error
9. **Handle syntax errors**: TypeScript compilation error
10. **Handle playwright not found**: @playwright/test not installed
11. **Handle browsers not found**: Browsers not installed
12. **Handle web server failure**: Web server startup timeout
13. **Parse call logs**: Playwright-specific call log extraction

### Validation

```python
def test_playwright_parser():
    parser = PlaywrightParser()

    # Test can_parse
    assert parser.can_parse("playwright", "")
    assert parser.can_parse("", "Running 5 tests using 3 workers")
    assert parser.can_parse("", "[chromium] > tests/home.spec.ts")
    assert not parser.can_parse("jest", "")
    assert not parser.can_parse("pytest", "")

    # Test parse
    result = parser.parse(sample_playwright_output)
    assert result['framework'] == 'playwright'
    assert result['passed_count'] > 0
    assert 'failures' in result or result['failed_count'] == 0

    # Test failure extraction
    failures = parser.extract_failures(sample_failure_output)
    assert len(failures) > 0
    assert failures[0]['browser'] in ['chromium', 'firefox', 'webkit']
    assert failures[0]['test_file'].endswith('.spec.ts')
```

## References

- Playwright Test CLI: https://playwright.dev/docs/test-cli
- Playwright Test Configuration: https://playwright.dev/docs/test-configuration
- Playwright Test Reporters: https://playwright.dev/docs/test-reporters
- Playwright Assertions: https://playwright.dev/docs/test-assertions
- Istanbul Coverage: https://istanbul.js.org/
- Parser Factory Pattern: `skills/result-parsing/parser-factory-pattern.md`
- Base Parser Interface: `skills/result-parsing/base-parser-interface.md`
- Jest Parser (reference): `skills/result-parsing/parsers/jest-parser.md`
- pytest Parser (reference): `skills/result-parsing/parsers/pytest-parser.md`

---

**Last Updated**: 2026-02-16
**Phase**: 2 - Detection and Parsing
**Status**: Complete
