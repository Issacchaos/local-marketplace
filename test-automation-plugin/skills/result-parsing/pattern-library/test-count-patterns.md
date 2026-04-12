# Test Count Patterns

**Version**: 1.0.0
**Category**: Reusable Regex Patterns
**Purpose**: Extract test counts (passed, failed, skipped, error) from test output

## Common Patterns

### Passed Count

**pytest**:
```python
r'(\d+)\s+passed'
```
Matches: `10 passed` → 10

**Jest/Vitest**:
```python
r'Tests?:\s*(\d+)\s+passed'
r'(\d+)\s+passed'
```
Matches: `Tests: 10 passed` → 10

**JUnit**:
```python
r'Tests run:\s*(\d+)'
r'(\d+)\s+tests?.*?passed'
```
Matches: `Tests run: 10` → 10

**GTest**:
```python
r'\[\s*PASSED\s*\]\s*(\d+)\s+tests?'
```
Matches: `[  PASSED  ] 10 tests` → 10

**Go**:
```python
r'ok\s+\S+\s+([\d.]+)s'  # Package passed
r'PASS:\s*(\d+)'
```

**Rust**:
```python
r'(\d+)\s+passed'
```
Matches: `10 passed; 2 failed` → 10

**RSpec**:
```python
r'(\d+)\s+examples?.*?0\s+failures?'  # All pass
r'(\d+)\s+examples?.*?(\d+)\s+failures?'  # Calculate: examples - failures
```

### Failed Count

**pytest**:
```python
r'(\d+)\s+failed'
```
Matches: `2 failed` → 2

**Jest/Vitest**:
```python
r'Tests?:\s*(\d+)\s+failed'
r'(\d+)\s+failed'
```
Matches: `Tests: 2 failed` → 2

**JUnit**:
```python
r'Failures?:\s*(\d+)'
```
Matches: `Failures: 2` → 2

**GTest**:
```python
r'\[\s*FAILED\s*\]\s*(\d+)\s+tests?'
```
Matches: `[  FAILED  ] 2 tests` → 2

**Go**:
```python
r'FAIL:\s*(\d+)'
r'FAIL\s+\S+\s+([\d.]+)s'  # Package failed
```

**Rust**:
```python
r'(\d+)\s+failed'
```
Matches: `2 failed; 10 passed` → 2

**RSpec**:
```python
r'(\d+)\s+failures?'
```
Matches: `10 examples, 2 failures` → 2

### Skipped Count

**pytest**:
```python
r'(\d+)\s+skipped'
```
Matches: `1 skipped` → 1

**Jest/Vitest**:
```python
r'Tests?:\s*(\d+)\s+skipped'
r'(\d+)\s+skipped'
```
Matches: `Tests: 1 skipped` → 1

**JUnit**:
```python
r'Skipped:\s*(\d+)'
```
Matches: `Skipped: 1` → 1

**GTest**:
```python
r'(\d+)\s+DISABLED'
```
Matches: `YOU HAVE 1 DISABLED TEST` → 1

**Go**:
```python
# Go doesn't have skipped tests
```

**Rust**:
```python
r'(\d+)\s+ignored'
```
Matches: `1 ignored; 10 passed` → 1

**RSpec**:
```python
r'(\d+)\s+pending'
```
Matches: `10 examples, 1 pending` → 1

### Error Count

**pytest**:
```python
r'(\d+)\s+error'
```
Matches: `1 error` → 1

**Jest/Vitest**:
```python
# Jest doesn't distinguish errors from failures
```

**JUnit**:
```python
r'Errors?:\s*(\d+)'
```
Matches: `Errors: 1` → 1

**GTest**:
```python
# GTest doesn't distinguish errors from failures
```

**Go**:
```python
# Go doesn't distinguish errors from failures
```

**Rust**:
```python
# Rust doesn't distinguish errors from failures
```

**RSpec**:
```python
# RSpec doesn't distinguish errors from failures
```

### Total Count

**pytest**:
```python
r'collected\s+(\d+)\s+items?'
```
Matches: `collected 10 items` → 10

**Jest/Vitest**:
```python
r'Tests?:\s*(\d+)\s+total'
```
Matches: `Tests: 10 total` → 10

**JUnit**:
```python
r'Tests run:\s*(\d+)'
```
Matches: `Tests run: 10` → 10

**GTest**:
```python
r'Running\s+(\d+)\s+tests?'
```
Matches: `Running 10 tests from 3 test suites` → 10

**Go**:
```python
r'running\s+(\d+)\s+tests?'
```
Matches: `running 10 tests` → 10

**Rust**:
```python
r'running\s+(\d+)\s+tests?'
```
Matches: `running 10 tests` → 10

**RSpec**:
```python
r'(\d+)\s+examples?'
```
Matches: `10 examples, 2 failures` → 10

## Multi-Framework Patterns

### Universal Passed Pattern
```python
r'(\d+)\s+(?:passed|ok|successful|PASSED|OK)'
```
Works for: pytest, Jest, GTest, Rust

### Universal Failed Pattern
```python
r'(\d+)\s+(?:failed|FAILED|failures?|FAIL)'
```
Works for: pytest, Jest, JUnit, GTest, RSpec, Rust

### Universal Skipped Pattern
```python
r'(\d+)\s+(?:skipped|ignored|pending|SKIPPED|DISABLED)'
```
Works for: pytest, Jest, JUnit, Rust, RSpec

## Usage Examples

### Extract All Counts
```python
def extract_test_counts(output):
    passed = extract_integer(r'(\d+)\s+passed', output, 0)
    failed = extract_integer(r'(\d+)\s+failed', output, 0)
    skipped = extract_integer(r'(\d+)\s+skipped', output, 0)
    total = passed + failed + skipped
    return total, passed, failed, skipped
```

### Try Multiple Patterns
```python
def extract_passed_count(output):
    patterns = [
        r'(\d+)\s+passed',
        r'Tests?:\s*(\d+)\s+passed',
        r'\[\s*PASSED\s*\]\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return int(match.group(1))
    return 0
```

## References

- pytest output: https://docs.pytest.org/en/stable/how-to/output.html
- Jest output: https://jestjs.io/docs/cli
- JUnit output: https://junit.org/junit5/docs/current/user-guide/
- GTest output: https://github.com/google/googletest/blob/main/docs/advanced.md

---

**Last Updated**: 2025-12-05
**Status**: Phase 1 patterns complete
