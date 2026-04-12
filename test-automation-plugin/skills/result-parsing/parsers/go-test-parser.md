# Go Test JSON Parser

**Version**: 1.0.0
**Language**: Go
**Framework**: testing (built-in), testify
**Build System**: go test
**Status**: Phase 4 - Systems Languages

## Overview

Result parser for Go test output supporting `go test` console output and JSON streaming format. Go's built-in testing package provides structured JSON output for programmatic parsing.

## Supported Output Formats

### 1. go test Console Output (Default)

```
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestDivide
=== RUN   TestDivide/positive_numbers
=== RUN   TestDivide/negative_numbers
=== RUN   TestDivide/zero_divisor
    calculator_test.go:45: Divide(10, 0) should panic
--- FAIL: TestDivide (0.00s)
    --- PASS: TestDivide/positive_numbers (0.00s)
    --- PASS: TestDivide/negative_numbers (0.00s)
    --- FAIL: TestDivide/zero_divisor (0.00s)
=== RUN   TestMultiply
--- SKIP: TestMultiply (0.00s)
    calculator_test.go:60: Not implemented yet
PASS
FAIL    github.com/example/calculator   0.123s
```

### 2. Verbose Console Output (go test -v)

```
=== RUN   TestAdd
=== PAUSE TestAdd
=== RUN   TestSubtract
=== PAUSE TestSubtract
=== CONT  TestAdd
    calculator_test.go:15: Testing addition
--- PASS: TestAdd (0.00s)
=== CONT  TestSubtract
--- PASS: TestSubtract (0.00s)
PASS
ok      github.com/example/calculator   0.123s
```

### 3. JSON Streaming Output (go test -json)

**Recommended format for programmatic parsing**

```json
{"Time":"2025-12-11T10:30:00Z","Action":"run","Package":"github.com/example/calculator","Test":"TestAdd"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestAdd","Output":"=== RUN   TestAdd\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestAdd","Output":"--- PASS: TestAdd (0.00s)\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"pass","Package":"github.com/example/calculator","Test":"TestAdd","Elapsed":0.00}
{"Time":"2025-12-11T10:30:00Z","Action":"run","Package":"github.com/example/calculator","Test":"TestDivide"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestDivide","Output":"=== RUN   TestDivide\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"run","Package":"github.com/example/calculator","Test":"TestDivide/zero_divisor"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestDivide/zero_divisor","Output":"=== RUN   TestDivide/zero_divisor\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestDivide","Output":"    calculator_test.go:45: Divide(10, 0) should panic\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"fail","Package":"github.com/example/calculator","Test":"TestDivide/zero_divisor","Elapsed":0.00}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestDivide","Output":"--- FAIL: TestDivide (0.00s)\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"fail","Package":"github.com/example/calculator","Test":"TestDivide","Elapsed":0.01}
{"Time":"2025-12-11T10:30:00Z","Action":"run","Package":"github.com/example/calculator","Test":"TestMultiply"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestMultiply","Output":"=== RUN   TestMultiply\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Test":"TestMultiply","Output":"    calculator_test.go:60: Not implemented yet\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"skip","Package":"github.com/example/calculator","Test":"TestMultiply","Elapsed":0.00}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Output":"FAIL\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"fail","Package":"github.com/example/calculator","Elapsed":0.123}
```

### 4. Benchmark Output (go test -bench)

```
goos: darwin
goarch: arm64
pkg: github.com/example/calculator
BenchmarkAdd-8          1000000000               0.3145 ns/op
BenchmarkMultiply-8     1000000000               0.3201 ns/op
BenchmarkDivide-8       500000000                2.145 ns/op
PASS
ok      github.com/example/calculator   3.456s
```

### 5. Benchmark JSON Output (go test -bench -json)

```json
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Output":"goos: darwin\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Output":"goarch: arm64\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Output":"pkg: github.com/example/calculator\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"output","Package":"github.com/example/calculator","Output":"BenchmarkAdd-8          1000000000               0.3145 ns/op\n"}
{"Time":"2025-12-11T10:30:00Z","Action":"pass","Package":"github.com/example/calculator","Elapsed":3.456}
```

## JSON Format Specification

### Event Types (Action field)

| Action | Description | Fields |
|--------|-------------|--------|
| `run` | Test started | Package, Test |
| `pause` | Test paused (parallel tests) | Package, Test |
| `cont` | Test continued | Package, Test |
| `pass` | Test passed | Package, Test, Elapsed |
| `fail` | Test failed | Package, Test, Elapsed |
| `skip` | Test skipped | Package, Test, Elapsed |
| `output` | Test output line | Package, Test (optional), Output |
| `bench` | Benchmark result | Package, Test (optional), Output |

### Event Structure

```go
type TestEvent struct {
    Time    string  `json:"Time"`     // RFC3339 timestamp
    Action  string  `json:"Action"`   // Event type
    Package string  `json:"Package"`  // Package name
    Test    string  `json:"Test"`     // Test name (optional for package-level events)
    Output  string  `json:"Output"`   // Output text (for output/bench actions)
    Elapsed float64 `json:"Elapsed"`  // Duration in seconds (for pass/fail/skip)
}
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "testing", "testify")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and framework.lower() in ["testing", "testify", "go"]:
        return True

    # JSON format detection
    json_signatures = [
        r'\{"Time":"[^"]+","Action":"run","Package":"[^"]+"',
        r'\{"Time":"[^"]+","Action":"pass","Package":"[^"]+"',
        r'\{"Time":"[^"]+","Action":"fail","Package":"[^"]+"'
    ]

    for signature in json_signatures:
        if re.search(signature, output):
            return True

    # Console output signatures
    console_signatures = [
        r'^=== RUN\s+Test\w+',
        r'^--- (?:PASS|FAIL|SKIP):\s+Test\w+',
        r'^ok\s+\S+\s+[\d.]+s',
        r'^FAIL\s+\S+\s+[\d.]+s',
        r'^PASS$'
    ]

    for signature in console_signatures:
        if re.search(signature, output, re.MULTILINE):
            return True

    # Benchmark signatures
    benchmark_signatures = [
        r'Benchmark\w+-\d+\s+\d+\s+[\d.]+\s+ns/op',
        r'goos:\s+\w+',
        r'goarch:\s+\w+'
    ]

    for signature in benchmark_signatures:
        if re.search(signature, output):
            return True

    return False
```

### JSON Parser (Recommended)

```python
def parse_json_output(output):
    """
    Parse go test -json output (newline-delimited JSON).

    Args:
        output: JSON streaming output from go test -json

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration": 0.0,
        "failures": [],
        "benchmarks": []
    }

    # Track tests and their state
    tests = {}  # test_name -> {status, output, elapsed}
    package_elapsed = 0.0

    # Parse newline-delimited JSON
    lines = output.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        action = event.get("Action")
        package = event.get("Package", "")
        test = event.get("Test", "")
        output_text = event.get("Output", "")
        elapsed = event.get("Elapsed", 0.0)

        # Initialize test tracking
        if test and test not in tests:
            tests[test] = {
                "name": test,
                "package": package,
                "status": None,
                "output": [],
                "elapsed": 0.0
            }

        # Handle different actions
        if action == "run":
            # Test started
            if test:
                tests[test]["status"] = "running"

        elif action == "output":
            # Capture test output
            if test and test in tests:
                tests[test]["output"].append(output_text)

        elif action == "pass":
            # Test passed
            if test:
                tests[test]["status"] = "pass"
                tests[test]["elapsed"] = elapsed
            else:
                # Package-level pass
                package_elapsed = elapsed

        elif action == "fail":
            # Test failed
            if test:
                tests[test]["status"] = "fail"
                tests[test]["elapsed"] = elapsed
            else:
                # Package-level fail
                package_elapsed = elapsed

        elif action == "skip":
            # Test skipped
            if test:
                tests[test]["status"] = "skip"
                tests[test]["elapsed"] = elapsed

        elif action == "bench":
            # Benchmark result
            result["benchmarks"].append({
                "package": package,
                "output": output_text
            })

    # Count test results
    for test_name, test_data in tests.items():
        status = test_data["status"]

        if status == "pass":
            result["passed"] += 1
        elif status == "fail":
            result["failed"] += 1
            # Extract failure details
            result["failures"].append({
                "test": test_name,
                "package": test_data["package"],
                "output": "".join(test_data["output"]),
                "elapsed": test_data["elapsed"]
            })
        elif status == "skip":
            result["skipped"] += 1

    result["total"] = len(tests)
    result["duration"] = package_elapsed

    return result
```

### Console Output Parser

```python
def parse_console_output(output):
    """
    Parse go test console output.

    Args:
        output: Console output from go test

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration": 0.0,
        "failures": []
    }

    # Track tests
    tests = {}  # test_name -> status
    current_test = None
    current_output = []

    lines = output.split('\n')
    for line in lines:
        # === RUN   TestName
        run_match = re.match(r'^=== RUN\s+(\S+)', line)
        if run_match:
            test_name = run_match.group(1)
            current_test = test_name
            tests[test_name] = "running"
            current_output = []
            continue

        # --- PASS: TestName (0.00s)
        pass_match = re.match(r'^--- PASS:\s+(\S+)\s+\(([\d.]+)s\)', line)
        if pass_match:
            test_name = pass_match.group(1)
            elapsed = float(pass_match.group(2))
            tests[test_name] = "pass"
            continue

        # --- FAIL: TestName (0.00s)
        fail_match = re.match(r'^--- FAIL:\s+(\S+)\s+\(([\d.]+)s\)', line)
        if fail_match:
            test_name = fail_match.group(1)
            elapsed = float(fail_match.group(2))
            tests[test_name] = "fail"

            # Extract failure output
            result["failures"].append({
                "test": test_name,
                "output": "\n".join(current_output),
                "elapsed": elapsed
            })
            continue

        # --- SKIP: TestName (0.00s)
        skip_match = re.match(r'^--- SKIP:\s+(\S+)\s+\(([\d.]+)s\)', line)
        if skip_match:
            test_name = skip_match.group(1)
            tests[test_name] = "skip"
            continue

        # Capture output for current test
        if current_test and line.strip():
            current_output.append(line)

    # Count results
    for test_name, status in tests.items():
        if status == "pass":
            result["passed"] += 1
        elif status == "fail":
            result["failed"] += 1
        elif status == "skip":
            result["skipped"] += 1

    result["total"] = len(tests)

    # Extract package duration
    # ok      github.com/example/calculator   0.123s
    # FAIL    github.com/example/calculator   0.123s
    duration_match = re.search(r'^(?:ok|FAIL)\s+\S+\s+([\d.]+)s', output, re.MULTILINE)
    if duration_match:
        result["duration"] = float(duration_match.group(1))

    return result
```

### Subtest Handling

Go supports subtests with `t.Run()`, creating hierarchical test names:

```
TestDivide
TestDivide/positive_numbers
TestDivide/negative_numbers
TestDivide/zero_divisor
```

**Parsing Strategy**:

```python
def parse_subtests(tests):
    """
    Process subtest hierarchy.

    Args:
        tests: Dict of test_name -> test_data

    Returns:
        dict: Organized test hierarchy
    """
    # Separate parent tests and subtests
    parent_tests = {}
    subtests = {}

    for test_name, test_data in tests.items():
        if '/' in test_name:
            # Subtest: TestDivide/zero_divisor
            parent_name = test_name.split('/')[0]
            if parent_name not in subtests:
                subtests[parent_name] = []
            subtests[parent_name].append(test_data)
        else:
            # Parent test
            parent_tests[test_name] = test_data

    # Attach subtests to parent
    for parent_name, subtest_list in subtests.items():
        if parent_name in parent_tests:
            parent_tests[parent_name]["subtests"] = subtest_list

    return parent_tests
```

### Benchmark Result Parsing

```python
def parse_benchmark_output(output):
    """
    Parse go test -bench output.

    Args:
        output: Benchmark output

    Returns:
        list: Benchmark results
    """
    benchmarks = []

    # BenchmarkAdd-8          1000000000               0.3145 ns/op
    pattern = r'(Benchmark\w+)-(\d+)\s+(\d+)\s+([\d.]+)\s+(ns|μs|ms)/op'

    for match in re.finditer(pattern, output):
        benchmark = {
            "name": match.group(1),
            "procs": int(match.group(2)),
            "iterations": int(match.group(3)),
            "ns_per_op": float(match.group(4)),
            "unit": match.group(5)
        }
        benchmarks.append(benchmark)

    return benchmarks
```

## Output Structure

### Standard Test Results

```python
{
    "total": 4,
    "passed": 2,
    "failed": 1,
    "skipped": 1,
    "duration": 0.123,
    "failures": [
        {
            "test": "TestDivide",
            "package": "github.com/example/calculator",
            "output": "    calculator_test.go:45: Divide(10, 0) should panic\n",
            "elapsed": 0.01,
            "subtests": [
                {
                    "test": "TestDivide/zero_divisor",
                    "status": "fail",
                    "output": "...",
                    "elapsed": 0.00
                }
            ]
        }
    ]
}
```

### Benchmark Results

```python
{
    "benchmarks": [
        {
            "name": "BenchmarkAdd",
            "procs": 8,
            "iterations": 1000000000,
            "ns_per_op": 0.3145,
            "unit": "ns"
        },
        {
            "name": "BenchmarkDivide",
            "procs": 8,
            "iterations": 500000000,
            "ns_per_op": 2.145,
            "unit": "ns"
        }
    ]
}
```

## Integration with Execute Agent

### Recommended Command

```bash
go test -json ./...
```

**Why JSON format?**
- Structured, parseable output
- Includes all test events (run, pass, fail, skip)
- Captures test output
- Handles subtests correctly
- Machine-readable timestamps
- No parsing ambiguity

### Alternative Commands

```bash
# Verbose console output (human-readable)
go test -v ./...

# Run specific package
go test -json github.com/example/calculator

# Run with coverage
go test -json -cover ./...

# Run benchmarks
go test -json -bench=. ./...

# Run with timeout
go test -json -timeout=30s ./...
```

## Edge Cases

### 1. Parallel Test Output

Go can run tests in parallel, causing interleaved output:

```
=== RUN   TestA
=== PAUSE TestA
=== RUN   TestB
=== PAUSE TestB
=== CONT  TestA
=== CONT  TestB
--- PASS: TestB (0.00s)
--- PASS: TestA (0.00s)
```

**Strategy**: JSON format handles this naturally with test names in each event.

### 2. Test Panic

```
=== RUN   TestPanic
panic: runtime error: index out of range [0] with length 0

goroutine 6 [running]:
github.com/example/calculator.TestPanic(0x14000114000)
    /path/calculator_test.go:50 +0x44
--- FAIL: TestPanic (0.00s)
```

**Strategy**: Capture panic output in failure details.

### 3. Build Failures

```
# github.com/example/calculator
./calculator.go:10:2: syntax error: unexpected newline, expecting comma or }
FAIL    github.com/example/calculator [build failed]
```

**Strategy**: Detect "[build failed]" and return build error status.

### 4. No Tests

```
?       github.com/example/calculator   [no test files]
```

**Strategy**: Detect "[no test files]" and return empty results.

### 5. Cached Results

```
ok      github.com/example/calculator   (cached)
```

**Strategy**: Parse "(cached)" and note in results.

## Usage Example

```python
# Example usage in Execute Agent
output = run_command("go test -json ./...")

# Parse results
if is_json_format(output):
    results = parse_json_output(output)
else:
    results = parse_console_output(output)

# Process results
print(f"Total: {results['total']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Skipped: {results['skipped']}")
print(f"Duration: {results['duration']}s")

# Handle failures
for failure in results['failures']:
    print(f"\nFailed: {failure['test']}")
    print(f"Output: {failure['output']}")
```

## References

- Go testing package: https://pkg.go.dev/testing
- go test command: https://pkg.go.dev/cmd/go#hdr-Test_packages
- JSON test output: https://pkg.go.dev/cmd/test2json
- Table-driven tests: https://go.dev/wiki/TableDrivenTests

---

**Last Updated**: 2025-12-11
**Phase**: 4 - Systems Languages
**Status**: Complete
