# TestNG Result Parser

**Version**: 1.0.0
**Language**: Java
**Framework**: TestNG
**Build Systems**: Maven (Surefire), Gradle
**Status**: Phase 3 - Implementation

## Overview

Result parser for TestNG test output supporting Maven Surefire and Gradle test task formats, plus TestNG's native XML report format (testng-results.xml).

## Supported Output Formats

### 1. TestNG Console Output

```
===============================================
Test Suite Name
Total tests run: 10, Passes: 8, Failures: 1, Skips: 1
===============================================

PASSED: testAdd
PASSED: testSubtract
FAILED: testDivideByZero
java.lang.AssertionError: Expected exception not thrown
        at org.testng.Assert.fail(Assert.java:96)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
SKIPPED: testMultiply
```

### 2. Maven Surefire with TestNG

```
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running TestSuite
[INFO] Tests run: 10, Failures: 1, Errors: 0, Skipped: 1, Time elapsed: 0.456 s <<< FAILURE!
[ERROR] testDivideByZero(com.example.CalculatorTest)  Time elapsed: 0.023 s  <<< FAILURE!
java.lang.AssertionError: Expected exception not thrown
        at org.testng.Assert.fail(Assert.java:96)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
[INFO]
[INFO] Results:
[INFO]
[ERROR] Failures:
[ERROR]   CalculatorTest.testDivideByZero:42 Expected exception not thrown
[INFO]
[ERROR] Tests run: 10, Failures: 1, Errors: 0, Skipped: 1
```

### 3. Gradle with TestNG

```
> Task :test

com.example.CalculatorTest > testAdd PASSED

com.example.CalculatorTest > testDivideByZero FAILED
    java.lang.AssertionError: Expected exception not thrown
        at org.testng.Assert.fail(Assert.java:96)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)

com.example.CalculatorTest > testMultiply SKIPPED

10 tests completed, 1 failed, 1 skipped
```

### 4. TestNG XML Format (testng-results.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testng-results skipped="1" failed="1" total="10" passed="8">
  <suite name="Test Suite" duration-ms="456" started-at="2025-12-08T10:00:00Z" finished-at="2025-12-08T10:00:01Z">
    <test name="Test" duration-ms="456" started-at="2025-12-08T10:00:00Z" finished-at="2025-12-08T10:00:01Z">
      <class name="com.example.CalculatorTest">
        <test-method status="PASS" signature="testAdd()" name="testAdd" duration-ms="12" started-at="2025-12-08T10:00:00Z" finished-at="2025-12-08T10:00:00Z"/>
        <test-method status="FAIL" signature="testDivideByZero()" name="testDivideByZero" duration-ms="23" started-at="2025-12-08T10:00:00Z" finished-at="2025-12-08T10:00:00Z">
          <exception class="java.lang.AssertionError">
            <message><![CDATA[Expected exception not thrown]]></message>
            <full-stacktrace><![CDATA[java.lang.AssertionError: Expected exception not thrown
        at org.testng.Assert.fail(Assert.java:96)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)]]></full-stacktrace>
          </exception>
        </test-method>
        <test-method status="SKIP" signature="testMultiply()" name="testMultiply" duration-ms="1" started-at="2025-12-08T10:00:00Z" finished-at="2025-12-08T10:00:00Z"/>
      </class>
    </test>
  </suite>
</testng-results>
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "testng")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and framework.lower() == "testng":
        return True

    # TestNG-specific signatures
    testng_signatures = [
        r'Total tests run: \d+, Passes: \d+, Failures: \d+, Skips: \d+',
        r'PASSED:',
        r'FAILED:',
        r'SKIPPED:',
        r'org\.testng\.Assert',
        r'<testng-results',
        r'testng-results\.xml'
    ]

    for signature in testng_signatures:
        if re.search(signature, output):
            return True

    # Maven/Gradle with TestNG indicators
    if re.search(r'TestNG|testng', output, re.IGNORECASE):
        # Check for TestNG-specific patterns
        if re.search(r'org\.testng', output):
            return True

    return False
```

### TestNG Console Output Parser

```python
def parse_testng_console(output):
    """
    Parse TestNG native console output.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "failures": []
    }

    # Extract summary
    # Pattern: Total tests run: 10, Passes: 8, Failures: 1, Skips: 1
    summary_pattern = r'Total tests run: (\d+), Passes: (\d+), Failures: (\d+), Skips: (\d+)'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        result["total"] = int(summary_match.group(1))
        result["passed"] = int(summary_match.group(2))
        result["failed"] = int(summary_match.group(3))
        result["skipped"] = int(summary_match.group(4))

    # Extract individual test results
    # Pattern: FAILED: testMethodName
    failed_pattern = r'FAILED: (.+?)(?:\n|$)'
    failed_tests = re.finditer(failed_pattern, output)

    for match in failed_tests:
        test_method = match.group(1).strip()

        # Extract stack trace following failure
        failure_pos = match.end()
        stack_trace = extract_testng_stack_trace(output, failure_pos)

        # Extract failure message (first line of stack trace)
        failure_message = stack_trace.split('\n')[0] if stack_trace else "Test failed"

        result["failures"].append({
            "test_method": test_method,
            "message": failure_message,
            "stack_trace": stack_trace
        })

    return result


def extract_testng_stack_trace(output, start_pos, max_lines=50):
    """
    Extract stack trace from TestNG output.

    Args:
        output: Full output text
        start_pos: Position to start extraction
        max_lines: Maximum number of lines to extract

    Returns:
        str: Stack trace text
    """
    lines = output[start_pos:].split('\n')
    stack_lines = []

    for line in lines[:max_lines]:
        # Stop at next test result marker
        if re.match(r'(PASSED:|FAILED:|SKIPPED:)', line):
            break

        stripped = line.strip()

        # Include exception and stack trace lines
        if stripped and (
            stripped.startswith('at ') or
            'Exception' in stripped or
            'Error' in stripped or
            'Assert' in stripped or
            stripped.startswith('Caused by:')
        ):
            stack_lines.append(stripped)
        elif not stripped:
            continue  # Skip empty lines
        else:
            # Stop at non-stack-trace content
            if stack_lines:
                break

    return '\n'.join(stack_lines)
```

### TestNG XML Parser

```python
def parse_testng_xml(xml_content):
    """
    Parse TestNG XML format test results (testng-results.xml).

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
        "failures": []
    }

    try:
        # Parse XML
        if xml_content.strip().startswith('<'):
            root = ET.fromstring(xml_content)
        else:
            tree = ET.parse(xml_content)
            root = tree.getroot()

        # Root element: <testng-results>
        if root.tag == 'testng-results':
            result["total"] = int(root.get('total', 0))
            result["passed"] = int(root.get('passed', 0))
            result["failed"] = int(root.get('failed', 0))
            result["skipped"] = int(root.get('skipped', 0))

        # Extract test methods
        for suite in root.findall('.//suite'):
            for test in suite.findall('.//test'):
                for test_class in test.findall('.//class'):
                    class_name = test_class.get('name', '')

                    for test_method in test_class.findall('.//test-method'):
                        status = test_method.get('status', 'UNKNOWN')
                        method_name = test_method.get('name', '')
                        signature = test_method.get('signature', '')

                        # Only interested in failures
                        if status == 'FAIL':
                            # Extract exception information
                            exception_elem = test_method.find('.//exception')
                            if exception_elem is not None:
                                exception_class = exception_elem.get('class', 'Unknown')

                                message_elem = exception_elem.find('message')
                                failure_message = message_elem.text if message_elem is not None and message_elem.text else 'Test failed'

                                stacktrace_elem = exception_elem.find('full-stacktrace')
                                stack_trace = stacktrace_elem.text if stacktrace_elem is not None and stacktrace_elem.text else ''

                                result["failures"].append({
                                    "test_class": class_name,
                                    "test_method": method_name,
                                    "signature": signature,
                                    "exception_type": exception_class,
                                    "message": failure_message.strip(),
                                    "stack_trace": stack_trace.strip()
                                })

    except Exception as e:
        result["parse_error"] = str(e)

    return result
```

### Maven/Gradle Output with TestNG

TestNG through Maven/Gradle looks similar to JUnit, so we reuse similar parsing:

```python
def parse_maven_testng(output):
    """
    Parse Maven Surefire output when using TestNG.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "failures": []
    }

    # Summary: [INFO/ERROR] Tests run: X, Failures: Y, Errors: Z, Skipped: W
    summary_pattern = r'\[(?:INFO|ERROR)\] Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        result["total"] = int(summary_match.group(1))
        result["failed"] = int(summary_match.group(2))
        errors = int(summary_match.group(3))
        result["skipped"] = int(summary_match.group(4))
        result["passed"] = result["total"] - result["failed"] - errors - result["skipped"]

    # Extract failures
    failure_pattern = r'\[ERROR\] (.+?)\((.+?)\).*?<<< (?:FAILURE|ERROR)!'
    for match in re.finditer(failure_pattern, output):
        test_method = match.group(1).strip()
        test_class = match.group(2).strip()

        failure_pos = match.end()
        stack_trace = extract_testng_stack_trace(output, failure_pos)
        failure_message = stack_trace.split('\n')[0] if stack_trace else "Test failed"

        result["failures"].append({
            "test_class": test_class,
            "test_method": test_method,
            "message": failure_message,
            "stack_trace": stack_trace
        })

    return result


def parse_gradle_testng(output):
    """
    Parse Gradle output when using TestNG.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "failures": []
    }

    # Summary: X tests completed, Y failed, Z skipped
    summary_pattern = r'(\d+) tests completed(?:, (\d+) failed)?(?:, (\d+) skipped)?'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        result["total"] = int(summary_match.group(1))
        result["failed"] = int(summary_match.group(2)) if summary_match.group(2) else 0
        result["skipped"] = int(summary_match.group(3)) if summary_match.group(3) else 0
        result["passed"] = result["total"] - result["failed"] - result["skipped"]

    # Extract individual failures
    # Pattern: com.example.TestClass > testMethod FAILED
    test_pattern = r'(.+?) > (.+?) (PASSED|FAILED|SKIPPED)'
    for match in re.finditer(test_pattern, output):
        test_class = match.group(1).strip()
        test_method = match.group(2).strip()
        status = match.group(3)

        if status == "FAILED":
            failure_pos = match.end()
            stack_trace = extract_testng_stack_trace(output, failure_pos)
            failure_message = stack_trace.split('\n')[0] if stack_trace else "Test failed"

            result["failures"].append({
                "test_class": test_class,
                "test_method": test_method,
                "message": failure_message,
                "stack_trace": stack_trace
            })

    return result
```

### Main Parse Function

```python
def parse(framework, output, xml_files=None):
    """
    Main parsing function that dispatches to appropriate parser.

    Args:
        framework: Detected framework ("testng")
        output: Console output from test execution
        xml_files: Optional list of XML report file paths

    Returns:
        dict: Standardized test results
    """
    # Try XML files first (most accurate)
    if xml_files and len(xml_files) > 0:
        for xml_file in xml_files:
            try:
                result = parse_testng_xml(xml_file)
                if result.get("total", 0) > 0:
                    return result
            except Exception:
                continue

    # Determine output format from console
    if re.search(r'Total tests run: \d+, Passes:', output):
        # Native TestNG console output
        return parse_testng_console(output)
    elif re.search(r'\[INFO\].*T E S T S', output):
        # Maven Surefire format
        return parse_maven_testng(output)
    elif re.search(r'> Task :test', output):
        # Gradle format
        return parse_gradle_testng(output)
    else:
        # Try all parsers and return best result
        testng_result = parse_testng_console(output)
        maven_result = parse_maven_testng(output)
        gradle_result = parse_gradle_testng(output)

        # Return result with highest total
        results = [testng_result, maven_result, gradle_result]
        best_result = max(results, key=lambda r: r.get("total", 0))

        if best_result["total"] > 0:
            return best_result
        else:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "parse_error": "Unable to parse TestNG output format"
            }
```

## Auto-Registration with Parser Factory

```python
# Parser metadata for factory registration
PARSER_METADATA = {
    "name": "testng-parser",
    "frameworks": ["testng"],
    "languages": ["java"],
    "priority": 8
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

## Examples

### Example 1: TestNG Console Success

**Input**:
```
Total tests run: 15, Passes: 15, Failures: 0, Skips: 0
```

**Output**:
```json
{
  "total": 15,
  "passed": 15,
  "failed": 0,
  "skipped": 0,
  "failures": []
}
```

### Example 2: TestNG Console with Failure

**Input**:
```
Total tests run: 10, Passes: 8, Failures: 1, Skips: 1

FAILED: testDivideByZero
java.lang.AssertionError: Expected exception not thrown
        at org.testng.Assert.fail(Assert.java:96)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
```

**Output**:
```json
{
  "total": 10,
  "passed": 8,
  "failed": 1,
  "skipped": 1,
  "failures": [
    {
      "test_method": "testDivideByZero",
      "message": "java.lang.AssertionError: Expected exception not thrown",
      "stack_trace": "java.lang.AssertionError: Expected exception not thrown\n        at org.testng.Assert.fail(Assert.java:96)\n        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)"
    }
  ]
}
```

### Example 3: TestNG XML Output

**Input**: testng-results.xml with 1 failure

**Output**:
```json
{
  "total": 10,
  "passed": 8,
  "failed": 1,
  "skipped": 1,
  "failures": [
    {
      "test_class": "com.example.CalculatorTest",
      "test_method": "testDivideByZero",
      "signature": "testDivideByZero()",
      "exception_type": "java.lang.AssertionError",
      "message": "Expected exception not thrown",
      "stack_trace": "java.lang.AssertionError: Expected exception not thrown\n        at org.testng.Assert.fail(Assert.java:96)\n        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)"
    }
  ]
}
```

## Edge Cases

1. **Test groups**: TestNG supports test grouping, may appear in output
2. **Data providers**: Parameterized tests with @DataProvider
3. **Suite XML files**: Multiple testng.xml configurations
4. **Parallel execution**: Tests running in parallel threads
5. **Custom listeners**: May add extra output to console

## TestNG-Specific Features

### Test Groups

TestNG allows grouping tests:
```
[TestNG] Running test groups: smoke, regression
```

### Data Providers

Parameterized tests appear multiple times with different parameters:
```
PASSED: testAdd[0](2, 3, 5)
PASSED: testAdd[1](10, 20, 30)
```

### Suite Configuration

testng.xml defines test suites and may affect output format.

## References

- TestNG Documentation: https://testng.org/doc/documentation-main.html
- Maven Surefire with TestNG: https://maven.apache.org/surefire/maven-surefire-plugin/examples/testng.html
- Gradle with TestNG: https://docs.gradle.org/current/userguide/java_testing.html#using_testng
- Parser Factory: `skills/result-parsing/parser-factory.md`
- JUnit Parser: `skills/result-parsing/parsers/junit-parser.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
