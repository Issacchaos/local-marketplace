# xUnit Result Parser

**Version**: 1.0.0
**Language**: C#
**Framework**: xUnit.net 2.x
**Build System**: dotnet CLI
**Status**: Phase 4 - Systems Languages

## Overview

Result parser for xUnit test output supporting `dotnet test` console output and xUnit XML report format. xUnit is the most popular testing framework for modern .NET applications.

## Supported Output Formats

### 1. dotnet test Console Output

```
Starting test execution, please wait...
A total of 1 test files matched the specified pattern.

Passed   TestProject.CalculatorTests.Add_TwoNumbers_ReturnsSum [42 ms]
Passed   TestProject.CalculatorTests.Subtract_TwoNumbers_ReturnsDifference [12 ms]
Failed   TestProject.CalculatorTests.Divide_ByZero_ThrowsException [56 ms]
  Error Message:
   Assert.Throws() Failure
   Expected: typeof(System.DivideByZeroException)
   Actual:   (No exception was thrown)
  Stack Trace:
     at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\project\test\CalculatorTests.cs:line 42
Skipped  TestProject.CalculatorTests.Multiply_NotImplemented [0 ms]

Test Run Failed.
Total tests: 4
     Passed: 2
     Failed: 1
    Skipped: 1
 Total time: 2.3456 Seconds
```

### 2. Minimal Console Output (CI Mode)

```
Test run for C:\project\test\bin\Debug\net8.0\TestProject.dll (.NETCoreApp,Version=v8.0)
Microsoft (R) Test Execution Command Line Tool Version 17.8.0 (x64)

Total tests: 10. Passed: 8. Failed: 1. Skipped: 1.
Test Run Failed.
Test execution time: 1.2345 Seconds
```

### 3. xUnit XML Format (TestResults/*.xml or custom path)

```xml
<?xml version="1.0" encoding="utf-8"?>
<assemblies timestamp="2025-12-10T15:30:45">
  <assembly name="TestProject" test-framework="xUnit.net 2.6.0" run-date="2025-12-10" run-time="15:30:45"
            total="4" passed="2" failed="1" skipped="1" time="2.345" errors="0">
    <collection total="4" passed="2" failed="1" skipped="1" time="2.345">
      <test name="TestProject.CalculatorTests.Add_TwoNumbers_ReturnsSum"
            type="TestProject.CalculatorTests"
            method="Add_TwoNumbers_ReturnsSum"
            time="0.042"
            result="Pass"/>
      <test name="TestProject.CalculatorTests.Subtract_TwoNumbers_ReturnsDifference"
            type="TestProject.CalculatorTests"
            method="Subtract_TwoNumbers_ReturnsDifference"
            time="0.012"
            result="Pass"/>
      <test name="TestProject.CalculatorTests.Divide_ByZero_ThrowsException"
            type="TestProject.CalculatorTests"
            method="Divide_ByZero_ThrowsException"
            time="0.056"
            result="Fail">
        <failure exception-type="Xunit.Sdk.ThrowsException">
          <message><![CDATA[Assert.Throws() Failure
Expected: typeof(System.DivideByZeroException)
Actual:   (No exception was thrown)]]></message>
          <stack-trace><![CDATA[   at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\project\test\CalculatorTests.cs:line 42]]></stack-trace>
        </failure>
      </test>
      <test name="TestProject.CalculatorTests.Multiply_NotImplemented"
            type="TestProject.CalculatorTests"
            method="Multiply_NotImplemented"
            time="0.000"
            result="Skip">
        <reason><![CDATA[Not implemented yet]]></reason>
      </test>
    </collection>
  </assembly>
</assemblies>
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "xunit")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and "xunit" in framework.lower():
        return True

    # Console output signatures
    dotnet_signatures = [
        r"Starting test execution, please wait",
        r"Microsoft \(R\) Test Execution Command Line Tool",
        r"Test Run (?:Successful|Failed)\.",
        r"Total tests: \d+\.\s+Passed: \d+\.\s+Failed: \d+",
        r"Passed\s+\S+\.\S+\.\S+\s+\[\d+ ms\]",
        r"Failed\s+\S+\.\S+\.\S+\s+\[\d+ ms\]"
    ]

    for signature in dotnet_signatures:
        if re.search(signature, output):
            return True

    # xUnit XML signatures
    xml_signatures = [
        r'<assemblies\s+timestamp=',
        r'<assembly\s+.*test-framework="xUnit\.net',
        r'<test\s+.*result="(?:Pass|Fail|Skip)"'
    ]

    for signature in xml_signatures:
        if re.search(signature, output):
            return True

    return False
```

### Console Output Parser

```python
def parse_console_output(output):
    """
    Parse dotnet test console output.

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

    # Extract summary - primary pattern
    # Total tests: 4. Passed: 2. Failed: 1. Skipped: 1.
    # OR
    # Total tests: 4
    #      Passed: 2
    #      Failed: 1
    #     Skipped: 1
    summary_compact = r'Total tests:\s*(\d+)\.\s+Passed:\s*(\d+)\.\s+Failed:\s*(\d+)\.(?:\s+Skipped:\s*(\d+)\.)?'
    summary_multiline = r'Total tests:\s*(\d+)\s+Passed:\s*(\d+)\s+Failed:\s*(\d+)\s+Skipped:\s*(\d+)'

    match = re.search(summary_compact, output)
    if not match:
        match = re.search(summary_multiline, output)

    if match:
        result["total"] = int(match.group(1))
        result["passed"] = int(match.group(2))
        result["failed"] = int(match.group(3))
        result["skipped"] = int(match.group(4)) if match.group(4) else 0

    # Extract duration
    # Total time: 2.3456 Seconds
    # OR Test execution time: 1.2345 Seconds
    duration_pattern = r'(?:Total time|Test execution time):\s*([\d.]+)\s*Seconds'
    duration_match = re.search(duration_pattern, output, re.IGNORECASE)
    if duration_match:
        result["duration"] = float(duration_match.group(1))

    # Extract individual failures
    # Failed   TestProject.CalculatorTests.Divide_ByZero_ThrowsException [56 ms]
    #   Error Message:
    #    Assert.Throws() Failure
    #    Expected: typeof(System.DivideByZeroException)
    #    Actual:   (No exception was thrown)
    #   Stack Trace:
    #      at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\project\test\CalculatorTests.cs:line 42

    failure_pattern = r'Failed\s+(.+?)\s+\[(\d+) ms\]'
    for match in re.finditer(failure_pattern, output):
        full_name = match.group(1)  # TestProject.CalculatorTests.Divide_ByZero_ThrowsException
        duration_ms = int(match.group(2))

        # Parse full name: Namespace.ClassName.MethodName
        parts = full_name.rsplit('.', 2)
        if len(parts) == 3:
            namespace, class_name, method_name = parts
        elif len(parts) == 2:
            namespace = ""
            class_name, method_name = parts
        else:
            namespace = ""
            class_name = ""
            method_name = full_name

        # Extract error message and stack trace following this failure
        failure_pos = match.end()
        error_message, stack_trace = extract_failure_details(output, failure_pos)

        result["failures"].append({
            "namespace": namespace,
            "test_class": class_name,
            "test_method": method_name,
            "full_name": full_name,
            "duration_ms": duration_ms,
            "message": error_message,
            "stack_trace": stack_trace
        })

    return result


def extract_failure_details(output, start_pos, max_lines=100):
    """
    Extract error message and stack trace from console output.

    Args:
        output: Full output text
        start_pos: Position to start extraction (after "Failed ..." line)
        max_lines: Maximum number of lines to extract

    Returns:
        tuple: (error_message, stack_trace)
    """
    lines = output[start_pos:].split('\n')
    error_lines = []
    stack_lines = []
    current_section = None

    for line in lines[:max_lines]:
        stripped = line.strip()

        # Stop at next test result
        if re.match(r'^(Passed|Failed|Skipped)\s+', line):
            break

        # Detect section headers
        if stripped == 'Error Message:':
            current_section = 'error'
            continue
        elif stripped == 'Stack Trace:':
            current_section = 'stack'
            continue
        elif stripped.startswith('Expected:') or stripped.startswith('Actual:'):
            # Part of error message for xUnit assertions
            error_lines.append(stripped)
            continue

        # Collect content based on current section
        if current_section == 'error' and stripped:
            error_lines.append(stripped)
        elif current_section == 'stack' and stripped:
            stack_lines.append(stripped)

    error_message = '\n'.join(error_lines) if error_lines else "Test failed"
    stack_trace = '\n'.join(stack_lines) if stack_lines else None

    return error_message, stack_trace
```

### xUnit XML Parser

```python
def parse_xunit_xml(xml_content):
    """
    Parse xUnit XML format test results.

    Args:
        xml_content: XML content string or file path

    Returns:
        dict: Parsed test results
    """
    import xml.etree.ElementTree as ET

    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration": 0.0,
        "failures": []
    }

    try:
        # Parse XML
        if xml_content.strip().startswith('<'):
            root = ET.fromstring(xml_content)
        else:
            tree = ET.parse(xml_content)
            root = tree.getroot()

        # Handle <assemblies> wrapper or single <assembly>
        if root.tag == 'assemblies':
            assemblies = root.findall('assembly')
        else:
            assemblies = [root]

        # Aggregate results from all assemblies
        for assembly in assemblies:
            result["total"] += int(assembly.get('total', 0))
            result["passed"] += int(assembly.get('passed', 0))
            result["failed"] += int(assembly.get('failed', 0))
            result["skipped"] += int(assembly.get('skipped', 0))
            result["errors"] += int(assembly.get('errors', 0))
            result["duration"] += float(assembly.get('time', 0.0))

            # Extract test cases from collections
            for collection in assembly.findall('.//collection'):
                for test in collection.findall('test'):
                    test_name = test.get('name', '')
                    test_type = test.get('type', '')
                    test_method = test.get('method', '')
                    test_result = test.get('result', 'Unknown')
                    test_time = float(test.get('time', 0.0))

                    # Check for failure
                    if test_result == 'Fail':
                        failure_elem = test.find('failure')

                        if failure_elem is not None:
                            exception_type = failure_elem.get('exception-type', 'Unknown')

                            # Extract message (may be in CDATA)
                            message_elem = failure_elem.find('message')
                            error_message = message_elem.text if message_elem is not None and message_elem.text else 'Test failed'

                            # Extract stack trace (may be in CDATA)
                            stack_elem = failure_elem.find('stack-trace')
                            stack_trace = stack_elem.text if stack_elem is not None and stack_elem.text else None

                            # Extract location from stack trace
                            location = extract_location_from_stack(stack_trace) if stack_trace else None

                            result["failures"].append({
                                "test_class": test_type.split('.')[-1] if test_type else test_name.split('.')[-2] if '.' in test_name else '',
                                "test_method": test_method,
                                "full_name": test_name,
                                "exception_type": exception_type,
                                "message": error_message.strip(),
                                "stack_trace": stack_trace.strip() if stack_trace else None,
                                "location": location,
                                "duration_ms": int(test_time * 1000)
                            })

    except Exception as e:
        result["parse_error"] = str(e)

    return result


def extract_location_from_stack(stack_trace):
    """
    Extract file location from C# stack trace.

    Example:
        "   at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\project\test\CalculatorTests.cs:line 42"
    Returns:
        dict: {"file": "CalculatorTests.cs", "line": 42}
    """
    if not stack_trace:
        return None

    # Pattern: " in <file path>:line <number>"
    location_pattern = r' in (.+?):line (\d+)'
    match = re.search(location_pattern, stack_trace)

    if match:
        file_path = match.group(1)
        line_number = int(match.group(2))

        # Extract just filename from full path
        import os
        filename = os.path.basename(file_path)

        return {
            "file": filename,
            "file_path": file_path,
            "line": line_number
        }

    return None
```

### Main Parse Function

```python
def parse(framework, output, xml_files=None):
    """
    Main parsing function that dispatches to appropriate parser.

    Args:
        framework: Detected framework ("xunit")
        output: Console output from test execution
        xml_files: Optional list of XML report file paths

    Returns:
        dict: Standardized test results
    """
    # Prefer XML files if available (most accurate)
    if xml_files and len(xml_files) > 0:
        aggregated_result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0,
            "failures": []
        }

        for xml_file in xml_files:
            xml_result = parse_xunit_xml(xml_file)
            aggregated_result["total"] += xml_result.get("total", 0)
            aggregated_result["passed"] += xml_result.get("passed", 0)
            aggregated_result["failed"] += xml_result.get("failed", 0)
            aggregated_result["skipped"] += xml_result.get("skipped", 0)
            aggregated_result["errors"] += xml_result.get("errors", 0)
            aggregated_result["duration"] += xml_result.get("duration", 0.0)
            aggregated_result["failures"].extend(xml_result.get("failures", []))

        return aggregated_result

    # Parse console output
    return parse_console_output(output)
```

## Regex Patterns Reference

### Summary Patterns

```python
# Compact summary (single line)
SUMMARY_COMPACT = r'Total tests:\s*(\d+)\.\s+Passed:\s*(\d+)\.\s+Failed:\s*(\d+)\.(?:\s+Skipped:\s*(\d+)\.)?'

# Multi-line summary (verbose output)
SUMMARY_MULTILINE = r'Total tests:\s*(\d+)\s+Passed:\s*(\d+)\s+Failed:\s*(\d+)\s+Skipped:\s*(\d+)'

# Duration
DURATION = r'(?:Total time|Test execution time):\s*([\d.]+)\s*Seconds'
```

### Test Result Patterns

```python
# Individual test results
TEST_PASSED = r'Passed\s+(.+?)\s+\[(\d+) ms\]'
TEST_FAILED = r'Failed\s+(.+?)\s+\[(\d+) ms\]'
TEST_SKIPPED = r'Skipped\s+(.+?)\s+\[(\d+) ms\]'
```

### Failure Detail Patterns

```python
# Section headers
ERROR_MESSAGE_HEADER = r'^\s*Error Message:\s*$'
STACK_TRACE_HEADER = r'^\s*Stack Trace:\s*$'

# Stack trace line with file location
STACK_LOCATION = r'at (.+?) in (.+?):line (\d+)'
```

## xUnit-Specific Features

### Assert.Throws() Failures

xUnit has specific assertion patterns:

```
Assert.Throws() Failure
Expected: typeof(System.DivideByZeroException)
Actual:   (No exception was thrown)
```

Parse as structured data:
- Assertion type: `Assert.Throws()`
- Expected: `typeof(System.DivideByZeroException)`
- Actual: `(No exception was thrown)`

### Theory Tests with InlineData

xUnit Theory tests appear multiple times with parameter values:

```
Failed   TestProject.CalculatorTests.Add_Theory(a: 1, b: 2, expected: 4) [12 ms]
```

Extract:
- Method: `Add_Theory`
- Parameters: `{a: 1, b: 2, expected: 4}`

### Skip Reasons

Skipped tests may have reasons:

```xml
<test name="TestProject.CalculatorTests.Multiply_NotImplemented" result="Skip">
  <reason><![CDATA[Not implemented yet]]></reason>
</test>
```

## Examples

### Example 1: All Tests Pass

**Input**:
```
Starting test execution, please wait...
Passed   TestProject.CalculatorTests.Add_TwoNumbers_ReturnsSum [42 ms]
Passed   TestProject.CalculatorTests.Subtract_TwoNumbers_ReturnsDifference [12 ms]

Test Run Successful.
Total tests: 2
     Passed: 2
 Total time: 0.5432 Seconds
```

**Output**:
```json
{
  "total": 2,
  "passed": 2,
  "failed": 0,
  "skipped": 0,
  "duration": 0.5432,
  "failures": []
}
```

### Example 2: With Failures

**Input**:
```
Failed   TestProject.CalculatorTests.Divide_ByZero_ThrowsException [56 ms]
  Error Message:
   Assert.Throws() Failure
   Expected: typeof(System.DivideByZeroException)
   Actual:   (No exception was thrown)
  Stack Trace:
     at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\project\test\CalculatorTests.cs:line 42

Test Run Failed.
Total tests: 3. Passed: 2. Failed: 1.
```

**Output**:
```json
{
  "total": 3,
  "passed": 2,
  "failed": 1,
  "skipped": 0,
  "failures": [
    {
      "namespace": "TestProject",
      "test_class": "CalculatorTests",
      "test_method": "Divide_ByZero_ThrowsException",
      "full_name": "TestProject.CalculatorTests.Divide_ByZero_ThrowsException",
      "duration_ms": 56,
      "message": "Assert.Throws() Failure\nExpected: typeof(System.DivideByZeroException)\nActual:   (No exception was thrown)",
      "stack_trace": "at TestProject.CalculatorTests.Divide_ByZero_ThrowsException() in C:\\project\\test\\CalculatorTests.cs:line 42"
    }
  ]
}
```

## Edge Cases

### 1. No Tests Found

```
Starting test execution, please wait...
A total of 1 test files matched the specified pattern.

No test is available in C:\project\test\bin\Debug\net8.0\TestProject.dll
Test Run Successful.
Total tests: 0
 Total time: 0.1234 Seconds
```

**Result**: `total=0, passed=0, failed=0`

### 2. Build Failure Before Tests

```
Build FAILED.

C:\project\test\CalculatorTests.cs(42,13): error CS0103: The name 'Calculator' does not exist in the current context
    0 Warning(s)
    1 Error(s)
```

**Result**: Parse error indicating build failure, no test counts

### 3. Test Timeout

If test execution times out, output may be incomplete:

```
Passed   TestProject.CalculatorTests.Test1 [42 ms]
```

**Strategy**: Return partial results with warning flag

### 4. Multiple Test Projects

```
Test run for C:\project\TestProject1\bin\Debug\net8.0\TestProject1.dll
Total tests: 5. Passed: 5.

Test run for C:\project\TestProject2\bin\Debug\net8.0\TestProject2.dll
Total tests: 3. Passed: 2. Failed: 1.

Test Run Failed.
Total tests: 8. Passed: 7. Failed: 1.
```

**Strategy**: Use final summary line for aggregate counts

## Auto-Registration with Parser Factory

```python
# Parser metadata for factory registration
PARSER_METADATA = {
    "name": "xunit-parser",
    "frameworks": ["xunit"],
    "languages": ["csharp"],
    "priority": 10
}


def register():
    """
    Register this parser with the parser factory.
    Called automatically by parser discovery system.
    """
    from parser_factory import register_parser

    register_parser(
        name=PARSER_METADATA["name"],
        frameworks=PARSER_METADATA["frameworks"],
        languages=PARSER_METADATA["languages"],
        can_parse_fn=can_parse,
        parse_fn=parse,
        priority=PARSER_METADATA["priority"]
    )
```

## Generating XML Output

To generate xUnit XML output, use:

```bash
# Console + XML
dotnet test --logger "console;verbosity=detailed" --logger "xunit;LogFilePath=test-results.xml"

# XML only
dotnet test --logger "xunit;LogFilePath=test-results.xml"
```

The XML file will be created at the specified path and can be parsed with `parse_xunit_xml()`.

## References

- xUnit.net Documentation: https://xunit.net/
- dotnet test Command: https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test
- xUnit XML Format: https://xunit.net/docs/format-xml-v2
- Test Execution: `agents/execute-agent.md`
- Parser Factory: `skills/result-parsing/parser-factory.md`

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
