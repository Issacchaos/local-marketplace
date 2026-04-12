# Google Test (GTest) Result Parser

**Version**: 1.0.0
**Language**: C++
**Framework**: Google Test (GTest) 1.10+
**Build Systems**: CMake, Make, Bazel
**Status**: Phase 4 - Systems Languages

## Overview

Result parser for Google Test (GTest) output supporting both console output and XML report format. Google Test is the most widely used C++ testing framework, developed by Google and used extensively in large-scale C++ projects.

## Supported Output Formats

### 1. GTest Console Output

```
[==========] Running 10 tests from 3 test suites.
[----------] Global test environment set-up.
[----------] 3 tests from MathTest
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (1 ms)
[ RUN      ] MathTest.Division
test_math.cpp:42: Failure
Expected equality of these values:
  result
    Which is: 0
  5
[  FAILED  ] MathTest.Division (2 ms)
[----------] 3 tests from MathTest (3 ms total)

[----------] 2 tests from StringTest
[ RUN      ] StringTest.Concatenation
[       OK ] StringTest.Concatenation (0 ms)
[ RUN      ] StringTest.Length
[       OK ] StringTest.Length (0 ms)
[----------] 2 tests from StringTest (0 ms total)

[----------] 5 tests from ParameterizedTest
[ RUN      ] ParameterizedTest/AddTest.Sum/0
[       OK ] ParameterizedTest/AddTest.Sum/0 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/1
[       OK ] ParameterizedTest/AddTest.Sum/1 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/2
[       OK ] ParameterizedTest/AddTest.Sum/2 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/3
[  FAILED  ] ParameterizedTest/AddTest.Sum/3 (1 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/4
[       OK ] ParameterizedTest/AddTest.Sum/4 (0 ms)
[----------] 5 tests from ParameterizedTest (1 ms total)

[----------] Global test environment tear-down
[==========] 10 tests from 3 test suites ran. (5 ms total)
[  PASSED  ] 8 tests.
[  FAILED  ] 2 tests, listed below:
[  FAILED  ] MathTest.Division
[  FAILED  ] ParameterizedTest/AddTest.Sum/3

 2 FAILED TESTS
```

### 2. Minimal Console Output (CI Mode)

```
[==========] Running 10 tests from 3 test suites.
[==========] 10 tests from 3 test suites ran. (5 ms total)
[  PASSED  ] 8 tests.
[  FAILED  ] 2 tests.
```

### 3. Google Test XML Format (--gtest_output=xml:file.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="10" failures="2" disabled="0" errors="0" time="0.005" timestamp="2025-12-10T15:30:45" name="AllTests">
  <testsuite name="MathTest" tests="3" failures="1" disabled="0" errors="0" time="0.003" timestamp="2025-12-10T15:30:45">
    <testcase name="Addition" status="run" result="completed" time="0" classname="MathTest">
    </testcase>
    <testcase name="Subtraction" status="run" result="completed" time="0.001" classname="MathTest">
    </testcase>
    <testcase name="Division" status="run" result="completed" time="0.002" classname="MathTest">
      <failure message="Expected equality of these values:&#x0A;  result&#x0A;    Which is: 0&#x0A;  5" type=""><![CDATA[test_math.cpp:42
Expected equality of these values:
  result
    Which is: 0
  5]]></failure>
    </testcase>
  </testsuite>
  <testsuite name="StringTest" tests="2" failures="0" disabled="0" errors="0" time="0" timestamp="2025-12-10T15:30:45">
    <testcase name="Concatenation" status="run" result="completed" time="0" classname="StringTest">
    </testcase>
    <testcase name="Length" status="run" result="completed" time="0" classname="StringTest">
    </testcase>
  </testsuite>
  <testsuite name="ParameterizedTest/AddTest" tests="5" failures="1" disabled="0" errors="0" time="0.001" timestamp="2025-12-10T15:30:45">
    <testcase name="Sum/0" status="run" result="completed" time="0" classname="ParameterizedTest/AddTest">
    </testcase>
    <testcase name="Sum/1" status="run" result="completed" time="0" classname="ParameterizedTest/AddTest">
    </testcase>
    <testcase name="Sum/2" status="run" result="completed" time="0" classname="ParameterizedTest/AddTest">
    </testcase>
    <testcase name="Sum/3" status="run" result="completed" time="0.001" classname="ParameterizedTest/AddTest">
      <failure message="Value of: actual&#x0A;  Actual: 10&#x0A;Expected: expected&#x0A;Which is: 15" type=""><![CDATA[test_add.cpp:25
Value of: actual
  Actual: 10
Expected: expected
Which is: 15]]></failure>
    </testcase>
    <testcase name="Sum/4" status="run" result="completed" time="0" classname="ParameterizedTest/AddTest">
    </testcase>
  </testsuite>
</testsuites>
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "gtest", "googletest")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and framework.lower() in ["gtest", "googletest", "google test"]:
        return True

    # Console output signatures
    gtest_signatures = [
        r"\[={10}\]\s*Running\s+\d+\s+tests? from\s+\d+\s+test suites?",
        r"\[\s*RUN\s*\]",
        r"\[\s*(OK|PASSED)\s*\]",
        r"\[\s*FAILED\s*\]",
        r"\[----------\]\s*\d+\s+tests? from",
        r"\[={10}\]\s*\d+\s+tests? from\s+\d+\s+test suites? ran\.",
        r"\d+\s+FAILED TESTS"
    ]

    for signature in gtest_signatures:
        if re.search(signature, output):
            return True

    # XML signatures
    xml_signatures = [
        r'<testsuites\s+tests=',
        r'<testsuite\s+name=',
        r'<testcase\s+name=.*?classname='
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
    Parse Google Test console output.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "disabled": 0,
        "duration_ms": 0,
        "failures": []
    }

    # Extract summary - primary pattern
    # [==========] 10 tests from 3 test suites ran. (5 ms total)
    # [  PASSED  ] 8 tests.
    # [  FAILED  ] 2 tests.

    # Total tests
    total_pattern = r'\[={10}\]\s*(\d+)\s+tests? from\s+\d+\s+test suites? ran\.\s*\((\d+)\s*ms\s+total\)'
    total_match = re.search(total_pattern, output)

    if total_match:
        result["total"] = int(total_match.group(1))
        result["duration_ms"] = int(total_match.group(2))

    # Passed count
    passed_pattern = r'\[\s*PASSED\s*\]\s*(\d+)\s+tests?\.?'
    passed_match = re.search(passed_pattern, output)
    if passed_match:
        result["passed"] = int(passed_match.group(1))

    # Failed count
    failed_pattern = r'\[\s*FAILED\s*\]\s*(\d+)\s+tests?\.?'
    failed_match = re.search(failed_pattern, output)
    if failed_match:
        result["failed"] = int(failed_match.group(1))

    # Disabled count (may not appear if 0)
    disabled_pattern = r'YOU HAVE (\d+) DISABLED TESTS?'
    disabled_match = re.search(disabled_pattern, output)
    if disabled_match:
        result["disabled"] = int(disabled_match.group(1))

    # If total not found, try counting from list
    if result["total"] == 0:
        result["total"] = result["passed"] + result["failed"] + result["disabled"]

    # Extract individual failures
    # [  FAILED  ] MathTest.Division (2 ms)
    # OR
    # [  FAILED  ] ParameterizedTest/AddTest.Sum/3 (1 ms)

    failure_list_pattern = r'\[\s*FAILED\s*\]\s*(.+?)(?:\s+\((\d+)\s*ms\))?$'
    for match in re.finditer(failure_list_pattern, output, re.MULTILINE):
        full_name = match.group(1).strip()
        duration_ms = int(match.group(2)) if match.group(2) else 0

        # Parse test name: TestSuite.TestCase or Parameterized/TestSuite.TestCase/N
        failure_info = parse_test_name(full_name)
        failure_info["duration_ms"] = duration_ms

        # Extract failure details from console output
        failure_details = extract_failure_from_console(output, full_name)
        if failure_details:
            failure_info.update(failure_details)

        result["failures"].append(failure_info)

    return result


def parse_test_name(full_name):
    """
    Parse Google Test name format.

    Formats:
    - Simple: TestSuite.TestCase
    - Parameterized: Prefix/TestSuite.TestCase/N
    - Typed: TypedTest/0.TestCase

    Args:
        full_name: Full test name string

    Returns:
        dict: Parsed name components
    """
    info = {
        "full_name": full_name,
        "test_suite": "",
        "test_case": "",
        "prefix": None,
        "parameter_index": None,
        "is_parameterized": False
    }

    # Check for parameterized format: Prefix/TestSuite.TestCase/N
    parameterized_pattern = r'^(.+?)/(.+?)\.(.+?)/(\d+)$'
    match = re.match(parameterized_pattern, full_name)

    if match:
        info["prefix"] = match.group(1)
        info["test_suite"] = match.group(2)
        info["test_case"] = match.group(3)
        info["parameter_index"] = int(match.group(4))
        info["is_parameterized"] = True
        return info

    # Check for simple parameterized: TestSuite.TestCase/N
    simple_param_pattern = r'^(.+?)\.(.+?)/(\d+)$'
    match = re.match(simple_param_pattern, full_name)

    if match:
        info["test_suite"] = match.group(1)
        info["test_case"] = match.group(2)
        info["parameter_index"] = int(match.group(3))
        info["is_parameterized"] = True
        return info

    # Standard format: TestSuite.TestCase
    standard_pattern = r'^(.+?)\.(.+)$'
    match = re.match(standard_pattern, full_name)

    if match:
        info["test_suite"] = match.group(1)
        info["test_case"] = match.group(2)
        return info

    # Fallback: treat entire name as test case
    info["test_case"] = full_name
    return info


def extract_failure_from_console(output, test_name):
    """
    Extract failure message and location from console output.

    Args:
        output: Full console output
        test_name: Name of failed test (e.g., "MathTest.Division")

    Returns:
        dict: Failure details or None
    """
    # Find the failure section for this test
    # Pattern: [ RUN      ] TestName ... [  FAILED  ] TestName

    escaped_name = re.escape(test_name)
    failure_section_pattern = (
        r'\[\s*RUN\s*\]\s*' + escaped_name +
        r'(.+?)' +
        r'\[\s*FAILED\s*\]\s*' + escaped_name
    )

    match = re.search(failure_section_pattern, output, re.DOTALL)
    if not match:
        return None

    failure_content = match.group(1).strip()

    # Extract file location
    # Pattern: test_math.cpp:42: Failure
    location_pattern = r'^(.+?):(\d+):\s*(?:Failure|error)'
    location_match = re.search(location_pattern, failure_content, re.MULTILINE)

    file_path = None
    line_number = None
    if location_match:
        file_path = location_match.group(1).strip()
        line_number = int(location_match.group(2))

    # Extract error message (everything after location line)
    if location_match:
        message_start = location_match.end()
        error_message = failure_content[message_start:].strip()
    else:
        error_message = failure_content.strip()

    return {
        "file": file_path,
        "line": line_number,
        "message": error_message,
        "stack_trace": failure_content
    }
```

### Google Test XML Parser

```python
def parse_gtest_xml(xml_content):
    """
    Parse Google Test XML format test results.

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
        "disabled": 0,
        "errors": 0,
        "duration_seconds": 0.0,
        "failures": []
    }

    try:
        # Parse XML
        if xml_content.strip().startswith('<'):
            root = ET.fromstring(xml_content)
        else:
            tree = ET.parse(xml_content)
            root = tree.getroot()

        # Root should be <testsuites>
        if root.tag != 'testsuites':
            return {"parse_error": "Invalid GTest XML format: root element is not 'testsuites'"}

        # Extract root-level attributes
        result["total"] = int(root.get('tests', 0))
        result["failed"] = int(root.get('failures', 0))
        result["disabled"] = int(root.get('disabled', 0))
        result["errors"] = int(root.get('errors', 0))
        result["duration_seconds"] = float(root.get('time', 0.0))
        result["passed"] = result["total"] - result["failed"] - result["disabled"] - result["errors"]

        # Extract test cases from test suites
        for testsuite in root.findall('testsuite'):
            suite_name = testsuite.get('name', '')

            for testcase in testsuite.findall('testcase'):
                test_name = testcase.get('name', '')
                test_classname = testcase.get('classname', suite_name)
                test_time = float(testcase.get('time', 0.0))
                test_status = testcase.get('status', 'run')
                test_result = testcase.get('result', 'completed')

                # Check for failure
                failure_elem = testcase.find('failure')
                if failure_elem is not None:
                    failure_message = failure_elem.get('message', 'Test failed')
                    failure_type = failure_elem.get('type', '')
                    failure_text = failure_elem.text if failure_elem.text else ''

                    # Extract file location from CDATA
                    # Format: test_math.cpp:42\nFailure message
                    file_path = None
                    line_number = None

                    location_match = re.search(r'^(.+?):(\d+)', failure_text)
                    if location_match:
                        file_path = location_match.group(1).strip()
                        line_number = int(location_match.group(2))
                        # Remove location from message
                        failure_text = failure_text[location_match.end():].strip()

                    # Parse test name components
                    full_name = f"{test_classname}.{test_name}"
                    test_info = parse_test_name(full_name)

                    result["failures"].append({
                        "test_suite": test_info["test_suite"],
                        "test_case": test_info["test_case"],
                        "full_name": full_name,
                        "prefix": test_info["prefix"],
                        "parameter_index": test_info["parameter_index"],
                        "is_parameterized": test_info["is_parameterized"],
                        "file": file_path,
                        "line": line_number,
                        "message": failure_message,
                        "failure_type": failure_type if failure_type else "AssertionError",
                        "failure_text": failure_text,
                        "duration_seconds": test_time
                    })

    except Exception as e:
        result["parse_error"] = str(e)

    return result
```

### Main Parse Function

```python
def parse(framework, output, xml_files=None):
    """
    Main parsing function that dispatches to appropriate parser.

    Args:
        framework: Detected framework ("gtest", "googletest")
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
            "disabled": 0,
            "errors": 0,
            "duration_seconds": 0.0,
            "failures": []
        }

        for xml_file in xml_files:
            xml_result = parse_gtest_xml(xml_file)

            # Handle parse errors
            if "parse_error" in xml_result:
                continue

            aggregated_result["total"] += xml_result.get("total", 0)
            aggregated_result["passed"] += xml_result.get("passed", 0)
            aggregated_result["failed"] += xml_result.get("failed", 0)
            aggregated_result["disabled"] += xml_result.get("disabled", 0)
            aggregated_result["errors"] += xml_result.get("errors", 0)
            aggregated_result["duration_seconds"] += xml_result.get("duration_seconds", 0.0)
            aggregated_result["failures"].extend(xml_result.get("failures", []))

        return aggregated_result

    # Check if output contains XML
    if output.strip().startswith('<?xml') or '<testsuites' in output:
        return parse_gtest_xml(output)

    # Parse console output
    return parse_console_output(output)
```

## Regex Patterns Reference

### Console Summary Patterns

```python
# Test run summary
TEST_RUN_START = r'\[={10}\]\s*Running\s+(\d+)\s+tests? from\s+(\d+)\s+test suites?'
TEST_RUN_END = r'\[={10}\]\s*(\d+)\s+tests? from\s+(\d+)\s+test suites? ran\.\s*\((\d+)\s*ms\s+total\)'

# Test suite boundaries
SUITE_START = r'\[----------\]\s*(\d+)\s+tests? from\s+(.+)'
SUITE_END = r'\[----------\]\s*(\d+)\s+tests? from\s+(.+)\s+\((\d+)\s*ms\s+total\)'

# Individual test results
TEST_RUN = r'\[\s*RUN\s*\]\s*(.+)'
TEST_OK = r'\[\s*(?:OK|PASSED)\s*\]\s*(.+?)(?:\s+\((\d+)\s*ms\))?'
TEST_FAILED = r'\[\s*FAILED\s*\]\s*(.+?)(?:\s+\((\d+)\s*ms\))?'
```

### Summary Count Patterns

```python
# Pass/Fail summary
PASSED_COUNT = r'\[\s*PASSED\s*\]\s*(\d+)\s+tests?\.?'
FAILED_COUNT = r'\[\s*FAILED\s*\]\s*(\d+)\s+tests?\.?'
DISABLED_COUNT = r'YOU HAVE (\d+) DISABLED TESTS?'

# Failed test list
FAILED_TEST_LIST = r'\[\s*FAILED\s*\]\s*(.+?)$'
```

### Failure Detail Patterns

```python
# File location
FAILURE_LOCATION = r'^(.+?):(\d+):\s*(?:Failure|error)'

# Assertion patterns
EXPECT_EQ_FAILURE = r'Expected equality of these values:\s+(.+?)\s+Which is:\s+(.+?)\s+(.+)'
EXPECT_TRUE_FAILURE = r'Value of: (.+?)\s+Actual: (.+?)\s+Expected: true'
EXPECT_FALSE_FAILURE = r'Value of: (.+?)\s+Actual: (.+?)\s+Expected: false'
```

## Google Test-Specific Features

### Test Fixtures (TEST_F)

Tests using fixtures appear with fixture class name:

```
[ RUN      ] DatabaseTest.InsertRecord
[       OK ] DatabaseTest.InsertRecord (5 ms)
```

Parse as:
- Test suite: `DatabaseTest` (fixture class)
- Test case: `InsertRecord`

### Parameterized Tests (TEST_P)

Parameterized tests have index suffix:

```
[ RUN      ] ParameterizedTest/AddTest.Sum/0
[ RUN      ] ParameterizedTest/AddTest.Sum/1
[ RUN      ] ParameterizedTest/AddTest.Sum/2
```

Parse as:
- Prefix: `ParameterizedTest`
- Test suite: `AddTest`
- Test case: `Sum`
- Parameter index: `0`, `1`, `2`

### Typed Tests

Typed tests include type information:

```
[ RUN      ] TypedTest/0.TestCase
[ RUN      ] TypedTest/1.TestCase
```

Parse as:
- Prefix: `TypedTest`
- Parameter index: `0`, `1`
- Test case: `TestCase`

### Death Tests (EXPECT_DEATH)

Death tests verify code exits/crashes:

```
[ RUN      ] DeathTest.CrashTest
[       OK ] DeathTest.CrashTest (15 ms)
```

Death tests are slower (fork process), indicated by longer duration.

### Disabled Tests

Disabled tests show in summary:

```
YOU HAVE 3 DISABLED TESTS

[  DISABLED ] MathTest.DISABLED_Multiply
```

Parse disabled count separately from passed/failed.

## Examples

### Example 1: All Tests Pass

**Input**:
```
[==========] Running 5 tests from 2 test suites.
[----------] 3 tests from MathTest
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (0 ms)
[ RUN      ] MathTest.Multiplication
[       OK ] MathTest.Multiplication (1 ms)
[----------] 3 tests from MathTest (1 ms total)

[----------] 2 tests from StringTest
[ RUN      ] StringTest.Concatenation
[       OK ] StringTest.Concatenation (0 ms)
[ RUN      ] StringTest.Length
[       OK ] StringTest.Length (0 ms)
[----------] 2 tests from StringTest (0 ms total)

[==========] 5 tests from 2 test suites ran. (2 ms total)
[  PASSED  ] 5 tests.
```

**Output**:
```json
{
  "total": 5,
  "passed": 5,
  "failed": 0,
  "disabled": 0,
  "duration_ms": 2,
  "failures": []
}
```

### Example 2: With Failures

**Input**:
```
[==========] Running 3 tests from 1 test suite.
[----------] 3 tests from MathTest
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Division
test_math.cpp:42: Failure
Expected equality of these values:
  result
    Which is: 0
  5
[  FAILED  ] MathTest.Division (2 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (0 ms)
[----------] 3 tests from MathTest (2 ms total)

[==========] 3 tests from 1 test suite ran. (2 ms total)
[  PASSED  ] 2 tests.
[  FAILED  ] 1 test, listed below:
[  FAILED  ] MathTest.Division

 1 FAILED TEST
```

**Output**:
```json
{
  "total": 3,
  "passed": 2,
  "failed": 1,
  "disabled": 0,
  "duration_ms": 2,
  "failures": [
    {
      "test_suite": "MathTest",
      "test_case": "Division",
      "full_name": "MathTest.Division",
      "file": "test_math.cpp",
      "line": 42,
      "message": "Expected equality of these values:\n  result\n    Which is: 0\n  5",
      "duration_ms": 2,
      "is_parameterized": false
    }
  ]
}
```

### Example 3: Parameterized Tests

**Input**:
```
[==========] Running 5 tests from 1 test suite.
[----------] 5 tests from ParameterizedTest/AddTest
[ RUN      ] ParameterizedTest/AddTest.Sum/0
[       OK ] ParameterizedTest/AddTest.Sum/0 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/1
[       OK ] ParameterizedTest/AddTest.Sum/1 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/2
[  FAILED  ] ParameterizedTest/AddTest.Sum/2 (1 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/3
[       OK ] ParameterizedTest/AddTest.Sum/3 (0 ms)
[ RUN      ] ParameterizedTest/AddTest.Sum/4
[       OK ] ParameterizedTest/AddTest.Sum/4 (0 ms)
[----------] 5 tests from ParameterizedTest/AddTest (1 ms total)

[==========] 5 tests from 1 test suite ran. (1 ms total)
[  PASSED  ] 4 tests.
[  FAILED  ] 1 test, listed below:
[  FAILED  ] ParameterizedTest/AddTest.Sum/2

 1 FAILED TEST
```

**Output**:
```json
{
  "total": 5,
  "passed": 4,
  "failed": 1,
  "disabled": 0,
  "duration_ms": 1,
  "failures": [
    {
      "test_suite": "AddTest",
      "test_case": "Sum",
      "full_name": "ParameterizedTest/AddTest.Sum/2",
      "prefix": "ParameterizedTest",
      "parameter_index": 2,
      "is_parameterized": true,
      "duration_ms": 1
    }
  ]
}
```

### Example 4: XML Output

**Input XML**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="3" failures="1" disabled="0" errors="0" time="0.002" timestamp="2025-12-10T15:30:45" name="AllTests">
  <testsuite name="MathTest" tests="3" failures="1" disabled="0" errors="0" time="0.002">
    <testcase name="Addition" status="run" result="completed" time="0" classname="MathTest" />
    <testcase name="Division" status="run" result="completed" time="0.002" classname="MathTest">
      <failure message="Expected equality of these values:&#x0A;  result&#x0A;    Which is: 0&#x0A;  5" type=""><![CDATA[test_math.cpp:42
Expected equality of these values:
  result
    Which is: 0
  5]]></failure>
    </testcase>
    <testcase name="Subtraction" status="run" result="completed" time="0" classname="MathTest" />
  </testsuite>
</testsuites>
```

**Output**:
```json
{
  "total": 3,
  "passed": 2,
  "failed": 1,
  "disabled": 0,
  "errors": 0,
  "duration_seconds": 0.002,
  "failures": [
    {
      "test_suite": "MathTest",
      "test_case": "Division",
      "full_name": "MathTest.Division",
      "file": "test_math.cpp",
      "line": 42,
      "message": "Expected equality of these values:\n  result\n    Which is: 0\n  5",
      "failure_type": "AssertionError",
      "duration_seconds": 0.002,
      "is_parameterized": false
    }
  ]
}
```

## Edge Cases

### 1. No Tests Found

```
[==========] Running 0 tests from 0 test suites.
[==========] 0 tests from 0 test suites ran. (0 ms total)
[  PASSED  ] 0 tests.
```

**Result**: `total=0, passed=0, failed=0`

### 2. All Tests Disabled

```
[==========] Running 0 tests from 0 test suites.
YOU HAVE 5 DISABLED TESTS

[==========] 0 tests from 0 test suites ran. (0 ms total)
[  PASSED  ] 0 tests.
```

**Result**: `total=0, passed=0, failed=0, disabled=5`

### 3. Compilation Failure Before Tests

```
test_math.cpp:15:10: error: 'Calculator' was not declared in this scope
   15 |     auto calc = Calculator();
      |          ^~~~
compilation terminated.
```

**Result**: Parse error indicating compilation failure, no test counts

### 4. Test Timeout

If execution times out, output may be incomplete:

```
[==========] Running 10 tests from 3 test suites.
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.HangsForever
```

**Strategy**: Return partial results with warning flag

### 5. Multiple Test Executables

When running multiple test binaries:

```
Running ./test_math
[==========] 5 tests from 2 test suites ran. (2 ms total)
[  PASSED  ] 5 tests.

Running ./test_string
[==========] 3 tests from 1 test suite ran. (1 ms total)
[  PASSED  ] 3 tests.
```

**Strategy**: Parse each section separately and aggregate results

### 6. Death Tests with Expected Crashes

```
[ RUN      ] DeathTest.CrashTest
[       OK ] DeathTest.CrashTest (15 ms)
```

**Note**: Death tests are expected to crash/exit, so they show as OK when they crash as expected

### 7. Malformed XML

If XML is truncated or malformed:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="10" failures="2">
  <testsuite name="MathTest" tests="3">
```

**Strategy**: Return parse error with details

## Auto-Registration with Parser Factory

```python
# Parser metadata for factory registration
PARSER_METADATA = {
    "name": "gtest-parser",
    "frameworks": ["gtest", "googletest"],
    "languages": ["cpp", "c++"],
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

To generate Google Test XML output, use the `--gtest_output` flag:

```bash
# XML output to specific file
./my_test --gtest_output=xml:test-results.xml

# XML output to directory (creates TEST-<name>.xml)
./my_test --gtest_output=xml:test-results/

# Console + XML (redirect console separately)
./my_test --gtest_output=xml:test-results.xml 2>&1 | tee console-output.txt
```

XML output includes all test details and is more reliable than parsing console output.

## Structured Output Format

The parser returns results in the standard format defined by `base-parser-interface.md`:

```python
{
    "total": int,              # Total tests executed
    "passed": int,             # Tests that passed
    "failed": int,             # Tests that failed
    "disabled": int,           # Tests disabled
    "errors": int,             # Tests with errors (rare in GTest)
    "duration_ms": int,        # Total execution time in milliseconds
    "duration_seconds": float, # Total execution time in seconds (XML only)
    "failures": [              # List of failure details
        {
            "test_suite": str,        # Test suite/fixture name
            "test_case": str,         # Test case name
            "full_name": str,         # Complete test name
            "prefix": str | None,     # Prefix for parameterized tests
            "parameter_index": int | None,  # Parameter index if parameterized
            "is_parameterized": bool, # Whether this is a parameterized test
            "file": str | None,       # Source file path
            "line": int | None,       # Line number of failure
            "message": str,           # Failure message
            "failure_type": str,      # Type of assertion failure
            "stack_trace": str,       # Full failure output
            "duration_ms": int,       # Test execution time
            "duration_seconds": float # Test execution time (XML)
        }
    ]
}
```

## References

- Google Test Documentation: https://google.github.io/googletest/
- GTest Primer: https://google.github.io/googletest/primer.html
- Advanced GTest: https://google.github.io/googletest/advanced.html
- GTest XML Format: https://google.github.io/googletest/advanced.html#generating-an-xml-report
- CMake Testing: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- Test Execution: `agents/execute-agent.md`
- Parser Factory: `skills/result-parsing/parser-factory-pattern.md`
- Base Parser Interface: `skills/result-parsing/base-parser-interface.md`

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
