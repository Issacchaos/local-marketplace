# JUnit Result Parser

**Version**: 1.0.0
**Language**: Java
**Framework**: JUnit 4, JUnit 5 (Jupiter)
**Build Systems**: Maven (Surefire), Gradle
**Status**: Phase 3 - Implementation

## Overview

Result parser for JUnit test output supporting both JUnit 4 and JUnit 5, with Maven Surefire and Gradle test task output formats. This parser handles console output and XML report files.

## Supported Output Formats

### 1. Maven Surefire Console Output

```
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running com.example.CalculatorTest
[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 1, Time elapsed: 0.123 s <<< FAILURE!
[ERROR] testDivideByZero(com.example.CalculatorTest) Time elapsed: 0.012 s  <<< FAILURE!
java.lang.AssertionError: Expected exception not thrown
        at org.junit.Assert.fail(Assert.java:89)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
[INFO]
[INFO] Results:
[INFO]
[ERROR] Failures:
[ERROR]   CalculatorTest.testDivideByZero:42 Expected exception not thrown
[INFO]
[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 1
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
```

### 2. Gradle Console Output

```
> Task :test

CalculatorTest > testAdd() PASSED

CalculatorTest > testSubtract() PASSED

CalculatorTest > testDivideByZero() FAILED
    java.lang.AssertionError: Expected exception not thrown
        at org.junit.jupiter.api.AssertionUtils.fail(AssertionUtils.java:38)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)

CalculatorTest > testMultiply() SKIPPED

5 tests completed, 1 failed, 1 skipped

> Task :test FAILED

FAILURE: Build failed with an exception.
```

### 3. JUnit XML Format (target/surefire-reports/*.xml or build/test-results/test/*.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.example.CalculatorTest" tests="5" failures="1" errors="0" skipped="1" time="0.123">
  <testcase name="testAdd" classname="com.example.CalculatorTest" time="0.012"/>
  <testcase name="testSubtract" classname="com.example.CalculatorTest" time="0.015"/>
  <testcase name="testDivideByZero" classname="com.example.CalculatorTest" time="0.012">
    <failure message="Expected exception not thrown" type="java.lang.AssertionError">
java.lang.AssertionError: Expected exception not thrown
        at org.junit.Assert.fail(Assert.java:89)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
    </failure>
  </testcase>
  <testcase name="testMultiply" classname="com.example.CalculatorTest" time="0.001">
    <skipped/>
  </testcase>
  <testcase name="testDivide" classname="com.example.CalculatorTest" time="0.018"/>
</testsuite>
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "junit4", "junit5", "junit")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and framework.startswith("junit"):
        return True

    # Maven Surefire signatures
    maven_signatures = [
        r"\[INFO\] +T E S T S",
        r"\[INFO\] Running .+Test",
        r"\[INFO\] Tests run: \d+",
        r"maven-surefire-plugin"
    ]

    for signature in maven_signatures:
        if re.search(signature, output):
            return True

    # Gradle test signatures
    gradle_signatures = [
        r"> Task :test",
        r"\d+ tests completed, \d+ failed",
        r"Test > .+ PASSED",
        r"Test > .+ FAILED"
    ]

    for signature in gradle_signatures:
        if re.search(signature, output):
            return True

    # JUnit XML signatures (if XML content provided)
    xml_signatures = [
        r'<testsuite\s+.*name="',
        r'<testcase\s+.*classname="'
    ]

    for signature in xml_signatures:
        if re.search(signature, output):
            return True

    return False
```

### Maven Surefire Output Parser

```python
def parse_maven_output(output):
    """
    Parse Maven Surefire console output.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "failures": []
    }

    # Extract summary from Results section
    # Pattern: [INFO/ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 1
    summary_pattern = r'\[(?:INFO|ERROR)\] Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        result["total"] = int(summary_match.group(1))
        result["failed"] = int(summary_match.group(2))
        result["errors"] = int(summary_match.group(3))
        result["skipped"] = int(summary_match.group(4))
        result["passed"] = result["total"] - result["failed"] - result["errors"] - result["skipped"]

    # Extract individual failures
    # Pattern: [ERROR] testMethod(com.example.TestClass) Time elapsed: X s  <<< FAILURE!
    failure_pattern = r'\[ERROR\] (.+?)\((.+?)\).*?<<< (?:FAILURE|ERROR)!'
    for match in re.finditer(failure_pattern, output):
        test_method = match.group(1).strip()
        test_class = match.group(2).strip()

        # Extract stack trace following this failure
        failure_pos = match.end()
        stack_trace = extract_java_stack_trace(output, failure_pos)

        # Extract failure message (first line of stack trace)
        failure_message = stack_trace.split('\n')[0] if stack_trace else "Test failed"

        result["failures"].append({
            "test_class": test_class,
            "test_method": test_method,
            "message": failure_message,
            "stack_trace": stack_trace
        })

    # Alternative: Extract from Failures section
    # [ERROR] Failures:
    # [ERROR]   CalculatorTest.testDivideByZero:42 Expected exception not thrown
    failures_section_pattern = r'\[ERROR\] Failures:(.+?)(?:\[INFO\]|\[ERROR\] Tests run:)'
    failures_section_match = re.search(failures_section_pattern, output, re.DOTALL)

    if failures_section_match and not result["failures"]:
        failures_text = failures_section_match.group(1)
        failure_lines = re.findall(r'\[ERROR\]\s+(.+?)\.(.+?):(\d+)\s+(.+)', failures_text)

        for test_class, test_method, line_num, message in failure_lines:
            result["failures"].append({
                "test_class": test_class,
                "test_method": test_method,
                "line_number": line_num,
                "message": message.strip(),
                "stack_trace": None
            })

    return result


def extract_java_stack_trace(output, start_pos, max_lines=50):
    """
    Extract Java stack trace starting from a position.

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
        # Stop at next [INFO] or [ERROR] marker
        if re.match(r'\[(?:INFO|ERROR)\]', line):
            break

        # Java stack trace lines start with exception type or "at "
        if line.strip() and (
            line.strip().startswith('at ') or
            'Exception' in line or
            'Error' in line or
            line.strip().startswith('Caused by:')
        ):
            stack_lines.append(line.strip())
        elif line.strip() == '':
            continue  # Skip empty lines within trace
        else:
            break  # End of stack trace

    return '\n'.join(stack_lines)
```

### Gradle Output Parser

```python
def parse_gradle_output(output):
    """
    Parse Gradle test task output.

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
    # Pattern: 5 tests completed, 1 failed, 1 skipped
    summary_pattern = r'(\d+) tests completed(?:, (\d+) failed)?(?:, (\d+) skipped)?'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        result["total"] = int(summary_match.group(1))
        result["failed"] = int(summary_match.group(2)) if summary_match.group(2) else 0
        result["skipped"] = int(summary_match.group(3)) if summary_match.group(3) else 0
        result["passed"] = result["total"] - result["failed"] - result["skipped"]

    # Extract individual test results
    # Pattern: TestClass > testMethod() FAILED
    test_pattern = r'(.+?) > (.+?)\(\) (PASSED|FAILED|SKIPPED)'
    for match in re.finditer(test_pattern, output):
        test_class = match.group(1).strip()
        test_method = match.group(2).strip()
        status = match.group(3)

        if status == "FAILED":
            # Extract stack trace following failure
            failure_pos = match.end()
            stack_trace = extract_gradle_stack_trace(output, failure_pos)

            # Extract failure message (first non-whitespace line after status)
            failure_message = stack_trace.split('\n')[0] if stack_trace else "Test failed"

            result["failures"].append({
                "test_class": test_class,
                "test_method": test_method,
                "message": failure_message,
                "stack_trace": stack_trace
            })

    return result


def extract_gradle_stack_trace(output, start_pos, max_lines=50):
    """
    Extract stack trace from Gradle output.

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
        # Stop at next test result or task marker
        if re.search(r'> (PASSED|FAILED|SKIPPED|Task)', line):
            break

        stripped = line.strip()

        # Include exception lines and stack trace lines
        if stripped and (
            stripped.startswith('at ') or
            'Exception' in stripped or
            'Error' in stripped or
            stripped.startswith('Caused by:')
        ):
            stack_lines.append(stripped)
        elif not stripped:
            continue  # Skip empty lines
        else:
            # Other lines might be part of message
            if stack_lines:  # Only if we've started collecting
                break

    return '\n'.join(stack_lines)
```

### JUnit XML Parser

```python
def parse_junit_xml(xml_content):
    """
    Parse JUnit XML format test results.

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
        "failures": []
    }

    try:
        # Parse XML
        if xml_content.strip().startswith('<'):
            root = ET.fromstring(xml_content)
        else:
            tree = ET.parse(xml_content)
            root = tree.getroot()

        # Handle both single testsuite and testsuites wrapper
        if root.tag == 'testsuites':
            testsuites = root.findall('testsuite')
        else:
            testsuites = [root]

        # Aggregate results from all test suites
        for testsuite in testsuites:
            result["total"] += int(testsuite.get('tests', 0))
            result["failed"] += int(testsuite.get('failures', 0))
            result["errors"] += int(testsuite.get('errors', 0))
            result["skipped"] += int(testsuite.get('skipped', 0))

            # Extract individual test cases
            for testcase in testsuite.findall('testcase'):
                test_class = testcase.get('classname', '')
                test_method = testcase.get('name', '')

                # Check for failure
                failure_elem = testcase.find('failure')
                error_elem = testcase.find('error')

                if failure_elem is not None or error_elem is not None:
                    elem = failure_elem if failure_elem is not None else error_elem
                    failure_type = elem.get('type', 'Unknown')
                    failure_message = elem.get('message', 'Test failed')
                    stack_trace = elem.text if elem.text else ''

                    result["failures"].append({
                        "test_class": test_class,
                        "test_method": test_method,
                        "type": failure_type,
                        "message": failure_message,
                        "stack_trace": stack_trace.strip()
                    })

        result["passed"] = result["total"] - result["failed"] - result["errors"] - result["skipped"]

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
        framework: Detected framework ("junit4", "junit5", "junit")
        output: Console output from test execution
        xml_files: Optional list of XML report file paths

    Returns:
        dict: Standardized test results
    """
    # Determine output format
    if xml_files and len(xml_files) > 0:
        # Parse XML files if available (most accurate)
        aggregated_result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failures": []
        }

        for xml_file in xml_files:
            xml_result = parse_junit_xml(xml_file)
            aggregated_result["total"] += xml_result.get("total", 0)
            aggregated_result["passed"] += xml_result.get("passed", 0)
            aggregated_result["failed"] += xml_result.get("failed", 0)
            aggregated_result["skipped"] += xml_result.get("skipped", 0)
            aggregated_result["errors"] += xml_result.get("errors", 0)
            aggregated_result["failures"].extend(xml_result.get("failures", []))

        return aggregated_result

    # Parse console output
    if re.search(r'\[INFO\].*T E S T S', output):
        # Maven Surefire format
        return parse_maven_output(output)
    elif re.search(r'> Task :test', output):
        # Gradle format
        return parse_gradle_output(output)
    else:
        # Try both and return best result
        maven_result = parse_maven_output(output)
        gradle_result = parse_gradle_output(output)

        if maven_result["total"] > 0:
            return maven_result
        elif gradle_result["total"] > 0:
            return gradle_result
        else:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "parse_error": "Unable to parse JUnit output format"
            }
```

## Auto-Registration with Parser Factory

```python
# Parser metadata for factory registration
PARSER_METADATA = {
    "name": "junit-parser",
    "frameworks": ["junit4", "junit5", "junit"],
    "languages": ["java"],
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

## Stack Trace Parsing

Java stack traces follow a specific format:

```
java.lang.AssertionError: Expected exception not thrown
        at org.junit.Assert.fail(Assert.java:89)
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)
        at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
Caused by: java.lang.NullPointerException: Cannot invoke method on null
        at com.example.Calculator.divide(Calculator.java:15)
```

Extract:
- Exception type: `java.lang.AssertionError`
- Message: `Expected exception not thrown`
- Location: `CalculatorTest.java:42`
- Caused by: Nested exception if present

## Examples

### Example 1: Maven Success Output

**Input**:
```
[INFO] Tests run: 10, Failures: 0, Errors: 0, Skipped: 0
```

**Output**:
```json
{
  "total": 10,
  "passed": 10,
  "failed": 0,
  "skipped": 0,
  "errors": 0,
  "failures": []
}
```

### Example 2: Gradle Failure Output

**Input**:
```
CalculatorTest > testDivideByZero() FAILED
    java.lang.AssertionError: Expected exception not thrown
        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)

5 tests completed, 1 failed
```

**Output**:
```json
{
  "total": 5,
  "passed": 4,
  "failed": 1,
  "skipped": 0,
  "failures": [
    {
      "test_class": "CalculatorTest",
      "test_method": "testDivideByZero",
      "message": "java.lang.AssertionError: Expected exception not thrown",
      "stack_trace": "java.lang.AssertionError: Expected exception not thrown\n        at com.example.CalculatorTest.testDivideByZero(CalculatorTest.java:42)"
    }
  ]
}
```

## Edge Cases

1. **Multi-module Maven project**: Aggregate results from multiple modules
2. **Parameterized tests**: Multiple executions of same test method
3. **Nested test classes**: Handle JUnit 5 @Nested classes
4. **Unicode in output**: Handle non-ASCII characters in test names/messages
5. **Very long stack traces**: Limit extraction to reasonable size

## References

- Maven Surefire Plugin: https://maven.apache.org/surefire/maven-surefire-plugin/
- Gradle Test Task: https://docs.gradle.org/current/dsl/org.gradle.api.tasks.testing.Test.html
- JUnit 5 Documentation: https://junit.org/junit5/docs/current/user-guide/
- JUnit 4 Documentation: https://junit.org/junit4/
- Parser Factory: `skills/result-parsing/parser-factory.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
