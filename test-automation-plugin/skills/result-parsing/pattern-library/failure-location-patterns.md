# Failure Location Patterns

**Version**: 1.0.0
**Category**: Reusable Regex Patterns
**Purpose**: Extract failure locations (file, line, function) from test output

## Common Patterns

### File Path Extraction

**pytest**:
```python
r'^(.*?):\d+:'  # File before line number
r'(tests/.*?\.py)'  # Relative path to test file
```
Matches: `tests/test_foo.py:15: in test_function` → `tests/test_foo.py`

**Jest/Vitest**:
```python
r'at.*?\((.*?):\d+:\d+\)'  # File in stack trace
r'(tests?/.*?\.(?:test|spec)\.[jt]sx?)'  # Test file pattern
```
Matches: `at Object.<anonymous> (tests/foo.test.js:15:5)` → `tests/foo.test.js`

**JUnit**:
```python
r'at\s+\S+\((\S+\.java):(\d+)\)'  # Stack trace
r'(\w+/\w+/.*?\.java)'  # Java file path
```
Matches: `at com.example.TestClass.testMethod(TestClass.java:42)` → `TestClass.java`

**GTest**:
```python
r'(.*?\.(?:cpp|cc|cxx)):(\d+):'  # C++ file
```
Matches: `test_file.cpp:42: Failure` → `test_file.cpp`

**Go**:
```python
r'(.*?\.go):(\d+):'  # Go file
```
Matches: `test_file.go:42: Error message` → `test_file.go`

**Rust**:
```python
r'at\s+(src/.*?\.rs):(\d+):\d+'  # Rust file
r'thread.*?panicked at.*?,\s*(src/.*?\.rs):(\d+):\d+'
```
Matches: `thread 'test' panicked at 'assertion failed', src/lib.rs:42:5` → `src/lib.rs`

**RSpec**:
```python
r'#\s+\./(.*/.*?\.rb):(\d+):'  # Ruby file
```
Matches: `# ./spec/test_spec.rb:42:in 'block'` → `spec/test_spec.rb`

### Line Number Extraction

**pytest**:
```python
r':(\d+):\s+in\s+'  # Line before "in"
```
Matches: `tests/test_foo.py:15: in test_function` → 15

**Jest/Vitest**:
```python
r':(\d+):(\d+)\)'  # Line:column in stack trace
```
Matches: `at Object.<anonymous> (tests/foo.test.js:15:5)` → 15

**JUnit**:
```python
r'\.java:(\d+)\)'  # Line in Java stack trace
```
Matches: `at TestClass.testMethod(TestClass.java:42)` → 42

**GTest**:
```python
r'\.(?:cpp|cc|cxx):(\d+):'  # Line in C++ file
```
Matches: `test_file.cpp:42: Failure` → 42

**Go**:
```python
r'\.go:(\d+):'  # Line in Go file
```
Matches: `test_file.go:42: Error message` → 42

**Rust**:
```python
r'\.rs:(\d+):(\d+)'  # Line:column in Rust
```
Matches: `src/lib.rs:42:5` → 42

**RSpec**:
```python
r'\.rb:(\d+):'  # Line in Ruby file
```
Matches: `spec/test_spec.rb:42:in 'block'` → 42

### Function/Method Name Extraction

**pytest**:
```python
r'in\s+(\w+)'  # After "in"
r'::(\w+)\s+FAILED'  # Test name in path
```
Matches: `tests/test_foo.py:15: in test_function` → `test_function`

**Jest/Vitest**:
```python
r'●.*?›\s+(.*?)$'  # Test name after ›
```
Matches: `● TestSuite › test name` → `test name`

**JUnit**:
```python
r'at\s+(\S+)\(.*?\)'  # Full method path
r'\.(\w+)\(.*?\.java:\d+\)'  # Method name only
```
Matches: `at com.example.TestClass.testMethod(TestClass.java:42)` → `testMethod`

**GTest**:
```python
r'(\w+)\.(\w+)'  # TestSuite.TestName
```
Matches: `TestSuite.TestName` → `TestName`

**Go**:
```python
r'func\s+(\w+)\('  # Function name in code
r'Test\w+'  # Test function pattern
```
Matches: `func TestExample(` → `TestExample`

**Rust**:
```python
r"thread\s+'(\w+)'"  # Thread name (usually test name)
```
Matches: `thread 'test_example' panicked` → `test_example`

**RSpec**:
```python
r'#\s+\..*?:\d+:in\s+`(.*?)'"  # Method name in backtrace
```
Matches: `# ./spec/test_spec.rb:42:in 'block (2 levels)'` → `block (2 levels)`

### Error Type Extraction

**pytest**:
```python
r'E\s+(\w+Error):'  # Error type after E marker
```
Matches: `E   AssertionError: assert 1 == 2` → `AssertionError`

**Jest/Vitest**:
```python
r'(\w+Error):'  # Error type before message
```
Matches: `TypeError: Cannot read property` → `TypeError`

**JUnit**:
```python
r'(\w+(?:Exception|Error)):'  # Java exception
```
Matches: `java.lang.AssertionError: expected:` → `AssertionError`

**GTest**:
```python
r'(.*?):\s*Failure'  # Before "Failure"
```
Matches: `test_file.cpp:42: Failure` → (infer from context)

**Go**:
```python
# Go doesn't have explicit error types in output
```

**Rust**:
```python
r"panicked at '(.*?)'"  # Panic message (type implicit)
```
Matches: `thread 'test' panicked at 'assertion failed'` → (infer from message)

**RSpec**:
```python
r'(.*?Error):'  # Ruby error type
```
Matches: `ArgumentError: wrong number of arguments` → `ArgumentError`

### Combined Location Pattern

**Universal Stack Trace**:
```python
r'at\s+(.*?)\s+\((.*?):(\d+)(?::(\d+))?\)'
```
Matches: `at Object.test (tests/foo.test.js:15:5)` → (method, file, line, column)

**Universal Simple Location**:
```python
r'(.*?):(\d+):'
```
Matches: `tests/test_foo.py:15: Error` → (file, line)

## Multi-Language Patterns

### File Path (Any Language)
```python
r'([\w/]+\.(?:py|js|ts|java|go|rs|rb|cpp|c))'
```
Matches any common source file extension

### Line Number (Universal)
```python
r':(\d+):'
r':(\d+)\s+'
r'\(.*?:(\d+):'
```
Works for most frameworks

### Function Name (Universal)
```python
r'in\s+(\w+)'
r'at\s+[\w.]+\.(\w+)'
r'(\w+)\('
```
Works for many frameworks

## Usage Examples

### Extract Complete Location
```python
def extract_failure_location(stack_trace):
    # Try detailed pattern first
    match = re.search(r'(.*?):(\d+):\s+in\s+(\w+)', stack_trace)
    if match:
        return {
            'file': match.group(1),
            'line': int(match.group(2)),
            'function': match.group(3)
        }

    # Try simpler pattern
    match = re.search(r'(.*?):(\d+):', stack_trace)
    if match:
        return {
            'file': match.group(1),
            'line': int(match.group(2)),
            'function': None
        }

    return None
```

### Try Multiple Patterns
```python
def extract_file_path(output):
    patterns = [
        r'(tests/.*?\.py)',  # pytest
        r'(tests?/.*?\.(?:test|spec)\.[jt]sx?)',  # Jest/Vitest
        r'at.*?\((.*?):',  # Stack trace
        r'(.*?\.(?:py|js|java|cpp|go|rs)):\d+',  # Generic
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return ""
```

## References

- Python tracebacks: https://docs.python.org/3/library/traceback.html
- JavaScript stack traces: https://v8.dev/docs/stack-trace-api
- Java stack traces: https://docs.oracle.com/javase/8/docs/api/java/lang/Throwable.html#printStackTrace--
- GTest output: https://github.com/google/googletest/blob/main/docs/advanced.md

---

**Last Updated**: 2025-12-05
**Status**: Phase 1 patterns complete
