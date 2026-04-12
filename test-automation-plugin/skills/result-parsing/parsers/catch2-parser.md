# Catch2 Result Parser

**Version**: 1.0.0
**Language**: C++
**Framework**: Catch2 v2.x, v3.x
**Build Systems**: CMake, Make, Bazel
**Status**: Phase 4 - Systems Languages

## Overview

Result parser for Catch2 test output supporting both console output and XML report format. Catch2 is a modern, header-only C++ testing framework with support for BDD-style testing (SCENARIO, GIVEN, WHEN, THEN) and flexible test organization through sections.

**Key Features**:
- BDD-style test support with sections
- Nested section handling (3+ levels)
- Expression expansion for assertion failures
- Supports both Catch2 v2 and v3 XML formats
- Tag-based test filtering

## Supported Output Formats

### 1. Catch2 Console Output

```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MyTests is a Catch v3.0.1 host application.
Run with -? for options

-------------------------------------------------------------------------------
Vector operations
-------------------------------------------------------------------------------
test_vector.cpp:10
...............................................................................

test_vector.cpp:15: PASSED:
  REQUIRE( vec.size() == 3 )
with expansion:
  3 == 3

===============================================================================
test cases:  2 | 1 passed | 1 failed
assertions: 10 | 8 passed | 2 failed
```

### 2. BDD-Style Console Output

```
-------------------------------------------------------------------------------
Scenario: User authentication
   Given: A user database with existing users
    When: A valid user logs in
    Then: The user is granted access
-------------------------------------------------------------------------------
test_auth.cpp:42
...............................................................................

test_auth.cpp:48: PASSED:
  REQUIRE( result.is_authenticated() )
with expansion:
  true

===============================================================================
test cases: 1 | 1 passed | 0 failed
assertions: 5 | 5 passed | 0 failed
```

### 3. Catch2 v3 XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Catch2TestRun name="MyTests" rng-seed="123456" catch2-version="3.0.1">
  <TestCase name="Vector operations" tags="[vector][math]" filename="test_vector.cpp" line="10">
    <OverallResult success="true" durationInSeconds="0.001234"/>
  </TestCase>
  <TestCase name="Division tests" tags="[math]" filename="test_math.cpp" line="25">
    <Expression success="false" type="REQUIRE" filename="test_math.cpp" line="28">
      <Original>
        result == 5
      </Original>
      <Expanded>
        0 == 5
      </Expanded>
    </Expression>
    <OverallResult success="false" durationInSeconds="0.002"/>
  </TestCase>
  <TestCase name="BDD scenario" tags="[bdd]" filename="test_bdd.cpp" line="40">
    <Section name="Given initial state" filename="test_bdd.cpp" line="42">
      <Section name="When action is performed" filename="test_bdd.cpp" line="45">
        <Section name="Then result is correct" filename="test_bdd.cpp" line="48">
          <OverallResult success="true" durationInSeconds="0.001"/>
        </Section>
      </Section>
    </Section>
    <OverallResult success="true" durationInSeconds="0.001"/>
  </TestCase>
  <OverallResults successes="2" failures="1" expectedFailures="0"/>
</Catch2TestRun>
```

### 4. Catch2 v2 XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Catch name="All tests">
  <Group name="MyTests">
    <TestCase name="Addition works" tags="[math]" filename="test_math.cpp" line="15">
      <OverallResult success="true" durationInSeconds="0.000123"/>
    </TestCase>
    <TestCase name="Division by zero fails" tags="[math]" filename="test_math.cpp" line="25">
      <Expression success="false" type="REQUIRE_THROWS" filename="test_math.cpp" line="28">
        <Original>
          divide(10, 0)
        </Original>
        <Exception filename="test_math.cpp" line="28">
          Expected exception not thrown
        </Exception>
      </Expression>
      <OverallResult success="false" durationInSeconds="0.001"/>
    </TestCase>
    <OverallResult success="false" durationInSeconds="0.001123"/>
  </Group>
</Catch>
```

## Parser Implementation

### Signature Detection

```python
def can_parse(framework, output):
    """
    Determine if this parser can handle the given output.

    Args:
        framework: Detected framework name (e.g., "catch2", "catch")
        output: Test execution output string

    Returns:
        bool: True if this parser can handle the output
    """
    # Framework match
    if framework and framework.lower() in ["catch", "catch2"]:
        return True

    # Console output signatures
    catch2_signatures = [
        r"Catch v\d+\.\d+\.\d+ host application",
        r"test cases:\s+\d+",
        r"assertions:\s+\d+",
        r"SCENARIO:",
        r"GIVEN:",
        r"WHEN:",
        r"THEN:",
        r"REQUIRE\(",
        r"CHECK\(",
        r"with expansion:"
    ]

    for signature in catch2_signatures:
        if re.search(signature, output):
            return True

    # XML signatures (v2 and v3)
    xml_signatures = [
        r'<Catch2TestRun\s+name=',      # v3 format
        r'<Catch\s+name=',               # v2 format
        r'<TestCase\s+name=.*?filename=',
        r'<Expression\s+success=',
        r'<Section\s+name='
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
    Parse Catch2 console output.

    Returns:
        dict: Parsed test results
    """
    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration_seconds": 0.0,
        "assertions_total": 0,
        "assertions_passed": 0,
        "assertions_failed": 0,
        "failures": []
    }

    # Extract summary
    # test cases:  2 | 1 passed | 1 failed
    # assertions: 10 | 8 passed | 2 failed

    # Test cases summary
    test_cases_pattern = r'test cases:\s*(\d+)\s*\|\s*(\d+)\s*passed\s*\|\s*(\d+)\s*failed'
    test_match = re.search(test_cases_pattern, output)

    if test_match:
        result["total"] = int(test_match.group(1))
        result["passed"] = int(test_match.group(2))
        result["failed"] = int(test_match.group(3))

    # Assertions summary
    assertions_pattern = r'assertions:\s*(\d+)\s*\|\s*(\d+)\s*passed\s*\|\s*(\d+)\s*failed'
    assertions_match = re.search(assertions_pattern, output)

    if assertions_match:
        result["assertions_total"] = int(assertions_match.group(1))
        result["assertions_passed"] = int(assertions_match.group(2))
        result["assertions_failed"] = int(assertions_match.group(3))

    # Extract individual failures
    # Find test case blocks with failures
    # Pattern: Test case header followed by FAILED assertion

    failure_sections = extract_failure_sections(output)

    for section in failure_sections:
        test_name = section.get("test_name", "Unknown")
        file_path = section.get("file", "")
        line_number = section.get("line", None)

        # Extract failures within this test case
        failures = extract_assertions_from_section(section.get("content", ""))

        for failure in failures:
            failure["test_name"] = test_name
            failure["test_file"] = file_path
            if not failure.get("line"):
                failure["line"] = line_number

            result["failures"].append(failure)

    return result


def extract_failure_sections(output):
    """
    Extract test case sections that contain failures.

    Args:
        output: Full console output

    Returns:
        list: List of failure sections
    """
    sections = []

    # Pattern for test case header:
    # -------------------------------------------------------------------------------
    # Test case name
    # -------------------------------------------------------------------------------
    # filename:line

    test_case_pattern = (
        r'-{79}\n'
        r'(.+?)\n'  # Test case name
        r'-{79}\n'
        r'(.+?):(\d+)\n'  # File:line
        r'(.+?)(?=\n-{79}|\nScenario:|\n={79}|$)'  # Content until next test or summary
    )

    for match in re.finditer(test_case_pattern, output, re.DOTALL):
        test_name = match.group(1).strip()
        file_path = match.group(2).strip()
        line_number = int(match.group(3))
        content = match.group(4)

        # Check if this section contains failures (FAILED markers)
        if "FAILED:" in content:
            sections.append({
                "test_name": test_name,
                "file": file_path,
                "line": line_number,
                "content": content
            })

    return sections


def extract_assertions_from_section(content):
    """
    Extract individual assertion failures from a test section.

    Args:
        content: Test case content string

    Returns:
        list: List of failure info dicts
    """
    failures = []

    # Pattern for FAILED assertion:
    # filename:line: FAILED:
    #   REQUIRE( expression )
    # with expansion:
    #   actual_value == expected_value

    failure_pattern = (
        r'(.+?):(\d+):\s*FAILED:\s*\n'  # File:line: FAILED:
        r'\s*(?:REQUIRE|CHECK)\(\s*(.+?)\s*\)\s*\n'  # Assertion macro and expression
        r'(?:with expansion:\s*\n\s*(.+?)\n)?'  # Optional expansion
    )

    for match in re.finditer(failure_pattern, content, re.DOTALL):
        file_path = match.group(1).strip()
        line_number = int(match.group(2))
        original_expression = match.group(3).strip()
        expanded_expression = match.group(4).strip() if match.group(4) else None

        message = f"REQUIRE( {original_expression} ) failed"
        if expanded_expression:
            message += f"\nwith expansion: {expanded_expression}"

        failures.append({
            "file": file_path,
            "line": line_number,
            "original_expression": original_expression,
            "expanded_expression": expanded_expression,
            "message": message,
            "assertion_type": "REQUIRE"
        })

    return failures
```

### Catch2 XML Parser

```python
def parse_catch2_xml(xml_content):
    """
    Parse Catch2 XML format test results (v2 and v3).

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
        "duration_seconds": 0.0,
        "catch2_version": None,
        "format_version": None,
        "failures": []
    }

    try:
        # Parse XML
        if xml_content.strip().startswith('<'):
            root = ET.fromstring(xml_content)
        else:
            tree = ET.parse(xml_content)
            root = tree.getroot()

        # Detect format version
        if root.tag == 'Catch2TestRun':
            result["format_version"] = "v3"
            result["catch2_version"] = root.get('catch2-version', 'Unknown')
            testsuites = [root]
        elif root.tag == 'Catch':
            result["format_version"] = "v2"
            # v2 may have Groups
            testsuites = root.findall('Group')
            if not testsuites:
                testsuites = [root]
        else:
            return {"parse_error": "Invalid Catch2 XML format: unknown root element"}

        # Extract test cases from all suites
        for testsuite in testsuites:
            for testcase in testsuite.findall('.//TestCase'):
                result["total"] += 1

                test_name = testcase.get('name', '')
                test_file = testcase.get('filename', '')
                test_line = int(testcase.get('line', 0))
                test_tags = testcase.get('tags', '')

                # Check OverallResult
                overall_result = testcase.find('OverallResult')
                if overall_result is not None:
                    success = overall_result.get('success', 'false').lower() == 'true'
                    duration = float(overall_result.get('durationInSeconds', 0.0))
                    result["duration_seconds"] += duration

                    if success:
                        result["passed"] += 1
                    else:
                        result["failed"] += 1

                        # Extract failure details
                        failures = extract_failures_from_testcase(testcase, test_name, test_file, test_line)
                        result["failures"].extend(failures)
                else:
                    # No OverallResult, assume failure
                    result["failed"] += 1

        # Extract overall results if present (v3)
        overall_results = root.find('OverallResults')
        if overall_results is not None:
            successes = int(overall_results.get('successes', 0))
            failures = int(overall_results.get('failures', 0))
            expected_failures = int(overall_results.get('expectedFailures', 0))

            # Cross-validate with counted results
            if successes + failures > 0:
                result["passed"] = successes
                result["failed"] = failures

    except Exception as e:
        result["parse_error"] = str(e)

    return result


def extract_failures_from_testcase(testcase, test_name, test_file, test_line):
    """
    Extract failure information from a TestCase element.

    Args:
        testcase: TestCase XML element
        test_name: Name of the test
        test_file: File containing the test
        test_line: Line number of the test

    Returns:
        list: List of failure info dicts
    """
    failures = []

    # Find all Expression elements (assertions)
    for expression in testcase.findall('.//Expression'):
        success = expression.get('success', 'false').lower() == 'true'

        if not success:
            expr_type = expression.get('type', 'REQUIRE')
            expr_file = expression.get('filename', test_file)
            expr_line = int(expression.get('line', test_line))

            # Extract original expression
            original_elem = expression.find('Original')
            original_expr = original_elem.text.strip() if original_elem is not None and original_elem.text else ''

            # Extract expanded expression
            expanded_elem = expression.find('Expanded')
            expanded_expr = expanded_elem.text.strip() if expanded_elem is not None and expanded_elem.text else ''

            # Check for exception element (v2 format)
            exception_elem = expression.find('Exception')
            exception_message = None
            if exception_elem is not None:
                exception_message = exception_elem.text.strip() if exception_elem.text else ''

            # Build failure message
            message = f"{expr_type}( {original_expr} ) failed"
            if expanded_expr and expanded_expr != original_expr:
                message += f"\nwith expansion: {expanded_expr}"
            if exception_message:
                message += f"\n{exception_message}"

            failures.append({
                "test_name": test_name,
                "test_file": expr_file,
                "line": expr_line,
                "assertion_type": expr_type,
                "original_expression": original_expr,
                "expanded_expression": expanded_expr,
                "exception_message": exception_message,
                "message": message
            })

    # Handle sections (BDD-style tests)
    failures.extend(extract_failures_from_sections(testcase, test_name, test_file, test_line))

    return failures


def extract_failures_from_sections(element, test_name, test_file, test_line, section_path=None):
    """
    Recursively extract failures from nested Section elements.

    Args:
        element: XML element to search
        test_name: Name of the test
        test_file: File containing the test
        test_line: Line number of the test
        section_path: List of parent section names (for BDD tests)

    Returns:
        list: List of failure info dicts
    """
    failures = []

    if section_path is None:
        section_path = []

    # Find direct Section children
    for section in element.findall('Section'):
        section_name = section.get('name', '')
        section_file = section.get('filename', test_file)
        section_line = int(section.get('line', test_line))

        current_path = section_path + [section_name]

        # Check for failures in this section
        for expression in section.findall('Expression'):
            success = expression.get('success', 'false').lower() == 'true'

            if not success:
                expr_type = expression.get('type', 'REQUIRE')
                expr_file = expression.get('filename', section_file)
                expr_line = int(expression.get('line', section_line))

                original_elem = expression.find('Original')
                original_expr = original_elem.text.strip() if original_elem is not None and original_elem.text else ''

                expanded_elem = expression.find('Expanded')
                expanded_expr = expanded_elem.text.strip() if expanded_elem is not None and expanded_elem.text else ''

                # Build message with section path for BDD tests
                section_hierarchy = " -> ".join(current_path)
                message = f"{expr_type}( {original_expr} ) failed in section: {section_hierarchy}"
                if expanded_expr and expanded_expr != original_expr:
                    message += f"\nwith expansion: {expanded_expr}"

                failures.append({
                    "test_name": test_name,
                    "test_file": expr_file,
                    "line": expr_line,
                    "assertion_type": expr_type,
                    "original_expression": original_expr,
                    "expanded_expression": expanded_expr,
                    "section_path": current_path,
                    "message": message
                })

        # Recursively process nested sections
        failures.extend(extract_failures_from_sections(section, test_name, test_file, test_line, current_path))

    return failures
```

### Main Parse Function

```python
def parse(framework, output, xml_files=None):
    """
    Main parsing function that dispatches to appropriate parser.

    Args:
        framework: Detected framework ("catch2", "catch")
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
            "duration_seconds": 0.0,
            "failures": []
        }

        for xml_file in xml_files:
            xml_result = parse_catch2_xml(xml_file)

            # Handle parse errors
            if "parse_error" in xml_result:
                continue

            aggregated_result["total"] += xml_result.get("total", 0)
            aggregated_result["passed"] += xml_result.get("passed", 0)
            aggregated_result["failed"] += xml_result.get("failed", 0)
            aggregated_result["skipped"] += xml_result.get("skipped", 0)
            aggregated_result["duration_seconds"] += xml_result.get("duration_seconds", 0.0)
            aggregated_result["failures"].extend(xml_result.get("failures", []))

        return aggregated_result

    # Check if output contains XML
    if output.strip().startswith('<?xml') or '<Catch2TestRun' in output or '<Catch' in output:
        return parse_catch2_xml(output)

    # Parse console output
    return parse_console_output(output)
```

## Regex Patterns Reference

### Console Summary Patterns

```python
# Test cases summary
TEST_CASES_SUMMARY = r'test cases:\s*(\d+)\s*\|\s*(\d+)\s*passed\s*\|\s*(\d+)\s*failed'

# Assertions summary
ASSERTIONS_SUMMARY = r'assertions:\s*(\d+)\s*\|\s*(\d+)\s*passed\s*\|\s*(\d+)\s*failed'

# Test case header
TEST_CASE_HEADER = (
    r'-{79}\n'
    r'(.+?)\n'  # Test name
    r'-{79}\n'
    r'(.+?):(\d+)'  # File:line
)
```

### Failure Patterns

```python
# FAILED assertion
FAILED_ASSERTION = (
    r'(.+?):(\d+):\s*FAILED:\s*\n'
    r'\s*(?:REQUIRE|CHECK|REQUIRE_THROWS|CHECK_THROWS)\(\s*(.+?)\s*\)\s*\n'
    r'(?:with expansion:\s*\n\s*(.+?)\n)?'
)

# REQUIRE/CHECK macros
ASSERTION_MACROS = r'(?:REQUIRE|CHECK|REQUIRE_THROWS|CHECK_THROWS|REQUIRE_FALSE|CHECK_FALSE)\('
```

### BDD Patterns

```python
# Scenario markers
SCENARIO = r'Scenario:\s*(.+)'
GIVEN = r'Given:\s*(.+)'
WHEN = r'When:\s*(.+)'
THEN = r'Then:\s*(.+)'
```

## Catch2-Specific Features

### BDD-Style Tests (SCENARIO, GIVEN, WHEN, THEN)

Catch2 supports BDD-style testing with special macros:

```cpp
SCENARIO("User authentication") {
    GIVEN("A user database with existing users") {
        UserDatabase db;
        db.add_user("alice", "password123");

        WHEN("A valid user logs in") {
            auto result = db.authenticate("alice", "password123");

            THEN("The user is granted access") {
                REQUIRE(result.is_authenticated());
                REQUIRE(result.username() == "alice");
            }
        }
    }
}
```

**XML Output**:
```xml
<TestCase name="Scenario: User authentication">
  <Section name="Given: A user database with existing users">
    <Section name="When: A valid user logs in">
      <Section name="Then: The user is granted access">
        <Expression success="true" type="REQUIRE" ...>
          <Original>result.is_authenticated()</Original>
          <Expanded>true</Expanded>
        </Expression>
      </Section>
    </Section>
  </Section>
</TestCase>
```

**Parse Strategy**:
- Test case name contains "Scenario:"
- Nested Section elements represent GIVEN/WHEN/THEN hierarchy
- Section path tracked for failure messages: "GIVEN -> WHEN -> THEN"

### Nested Sections (3+ levels)

Catch2 allows arbitrary nesting of sections:

```cpp
TEST_CASE("Database operations") {
    SECTION("Insert") {
        SECTION("Single record") {
            SECTION("Valid data") {
                // Tests here
            }
        }
    }
}
```

**Handle with recursive parsing**:
- `extract_failures_from_sections()` recursively processes Section elements
- Maintains `section_path` list to track hierarchy
- Failure messages include full section path

### Assertion Expression Expansion

Catch2 captures both original and expanded expressions:

```cpp
int a = 5, b = 10;
REQUIRE(a + b == 20);
```

**Output**:
```
Original: a + b == 20
Expanded: 15 == 20
```

**Parse Strategy**:
- Extract both `<Original>` and `<Expanded>` elements
- Show both in failure message for clarity
- Helps identify why assertion failed

### Tags

Tests can have tags for filtering:

```cpp
TEST_CASE("Addition", "[math][quick]") {
    REQUIRE(1 + 1 == 2);
}
```

**XML Output**:
```xml
<TestCase name="Addition" tags="[math][quick]" ...>
```

**Parse Strategy**:
- Extract `tags` attribute from TestCase
- Can be used for test categorization
- Stored in failure info for filtering

### Assertion Types

Catch2 provides multiple assertion macros:

- `REQUIRE(expr)`: Hard assertion (stops test on failure)
- `CHECK(expr)`: Soft assertion (continues test)
- `REQUIRE_THROWS(expr)`: Expects exception
- `REQUIRE_FALSE(expr)`: Expects false
- `REQUIRE_THAT(value, matcher)`: Custom matchers

**Parse Strategy**:
- Extract assertion type from `type` attribute in Expression element
- Include in failure message for context

## Examples

### Example 1: All Tests Pass

**Input (Console)**:
```
test cases:  5 | 5 passed | 0 failed
assertions: 25 | 25 passed | 0 failed
```

**Output**:
```json
{
  "total": 5,
  "passed": 5,
  "failed": 0,
  "skipped": 0,
  "assertions_total": 25,
  "assertions_passed": 25,
  "assertions_failed": 0,
  "failures": []
}
```

### Example 2: With Failures (XML v3)

**Input XML**:
```xml
<Catch2TestRun name="MyTests" catch2-version="3.0.1">
  <TestCase name="Division tests" filename="test_math.cpp" line="25">
    <Expression success="false" type="REQUIRE" filename="test_math.cpp" line="28">
      <Original>result == 5</Original>
      <Expanded>0 == 5</Expanded>
    </Expression>
    <OverallResult success="false" durationInSeconds="0.002"/>
  </TestCase>
  <OverallResults successes="0" failures="1" expectedFailures="0"/>
</Catch2TestRun>
```

**Output**:
```json
{
  "total": 1,
  "passed": 0,
  "failed": 1,
  "skipped": 0,
  "duration_seconds": 0.002,
  "catch2_version": "3.0.1",
  "format_version": "v3",
  "failures": [
    {
      "test_name": "Division tests",
      "test_file": "test_math.cpp",
      "line": 28,
      "assertion_type": "REQUIRE",
      "original_expression": "result == 5",
      "expanded_expression": "0 == 5",
      "message": "REQUIRE( result == 5 ) failed\nwith expansion: 0 == 5"
    }
  ]
}
```

### Example 3: BDD-Style Test with Nested Sections

**Input XML**:
```xml
<TestCase name="Scenario: User login" filename="test_auth.cpp" line="40">
  <Section name="Given: A user database" filename="test_auth.cpp" line="42">
    <Section name="When: Invalid credentials" filename="test_auth.cpp" line="48">
      <Section name="Then: Access is denied" filename="test_auth.cpp" line="52">
        <Expression success="false" type="REQUIRE" filename="test_auth.cpp" line="53">
          <Original>result.is_authenticated()</Original>
          <Expanded>true</Expanded>
        </Expression>
      </Section>
    </Section>
  </Section>
  <OverallResult success="false" durationInSeconds="0.003"/>
</TestCase>
```

**Output**:
```json
{
  "total": 1,
  "passed": 0,
  "failed": 1,
  "failures": [
    {
      "test_name": "Scenario: User login",
      "test_file": "test_auth.cpp",
      "line": 53,
      "assertion_type": "REQUIRE",
      "original_expression": "result.is_authenticated()",
      "expanded_expression": "true",
      "section_path": [
        "Given: A user database",
        "When: Invalid credentials",
        "Then: Access is denied"
      ],
      "message": "REQUIRE( result.is_authenticated() ) failed in section: Given: A user database -> When: Invalid credentials -> Then: Access is denied\nwith expansion: true"
    }
  ]
}
```

## Edge Cases

### 1. No Tests Found

```
No test cases matched filters
test cases: 0 | 0 passed | 0 failed
```

**Result**: `total=0, passed=0, failed=0`

### 2. All Tests Skipped (Hidden)

Catch2 doesn't have explicit skip functionality, but tests can be hidden:

```cpp
TEST_CASE("Hidden test", "[.]") {  // "." tag hides test
    REQUIRE(true);
}
```

**Result**: Tests not included in run unless specifically requested

### 3. Empty Sections

```xml
<TestCase name="Test with empty section">
  <Section name="Empty section">
    <OverallResult success="true" durationInSeconds="0.0"/>
  </Section>
  <OverallResult success="true" durationInSeconds="0.0"/>
</TestCase>
```

**Strategy**: Process successfully, no assertions in empty sections

### 4. Exception-Based Failures

```xml
<Expression success="false" type="REQUIRE_THROWS">
  <Original>divide(10, 0)</Original>
  <Exception filename="test.cpp" line="25">
    Expected exception not thrown
  </Exception>
</Expression>
```

**Strategy**: Extract exception message from `<Exception>` element

### 5. Multiple Test Runs (Concatenated Output)

If running multiple test executables, output may be concatenated:

```
test cases: 5 | 5 passed | 0 failed
test cases: 3 | 2 passed | 1 failed
```

**Strategy**: Use final summary line or aggregate all summary lines

### 6. Malformed XML (Incomplete Output)

If test execution times out or crashes:

```xml
<Catch2TestRun name="MyTests">
  <TestCase name="Test1">
    <Expression success="false"...
```

**Strategy**: Handle parse exception, return partial results with warning

### 7. Deep Section Nesting (5+ levels)

```xml
<Section name="Level 1">
  <Section name="Level 2">
    <Section name="Level 3">
      <Section name="Level 4">
        <Section name="Level 5">
          <Expression .../>
        </Section>
      </Section>
    </Section>
  </Section>
</Section>
```

**Strategy**: Recursive parsing handles any depth, maintain full path

## Auto-Registration with Parser Factory

```python
# Parser metadata for factory registration
PARSER_METADATA = {
    "name": "catch2-parser",
    "frameworks": ["catch2", "catch"],
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

To generate Catch2 XML output:

```bash
# XML output to specific file
./my_test -r xml -o test-results.xml

# XML output with console
./my_test -r console -r xml::out=test-results.xml

# Multiple reporters
./my_test -r console -r xml::out=results.xml -r junit::out=junit.xml
```

**Reporter Options**:
- `-r xml`: XML format (v2 or v3 depending on Catch2 version)
- `-r console`: Console output
- `-r junit`: JUnit-compatible XML
- `-r compact`: Minimal console output

## Catch2 v2 vs v3 Differences

### Root Element

**v2**: `<Catch name="...">`
```xml
<Catch name="All tests">
  <Group name="GroupName">
    <TestCase ...>
  </Group>
</Catch>
```

**v3**: `<Catch2TestRun name="...">`
```xml
<Catch2TestRun name="MyTests" rng-seed="123" catch2-version="3.0.1">
  <TestCase ...>
</Catch2TestRun>
```

### Metadata

**v2**: Minimal metadata
- No version attribute
- Groups used for organization

**v3**: Rich metadata
- `catch2-version` attribute
- `rng-seed` for randomization
- Timestamp information

### Detection Strategy

```python
if root.tag == 'Catch2TestRun':
    format_version = "v3"
elif root.tag == 'Catch':
    format_version = "v2"
```

Both formats supported transparently.

## Structured Output Format

The parser returns results in the standard format defined by `base-parser-interface.md`:

```python
{
    "total": int,                   # Total tests executed
    "passed": int,                  # Tests that passed
    "failed": int,                  # Tests that failed
    "skipped": int,                 # Tests skipped (usually 0 for Catch2)
    "duration_seconds": float,      # Total execution time
    "assertions_total": int,        # Total assertions (console only)
    "assertions_passed": int,       # Passed assertions (console only)
    "assertions_failed": int,       # Failed assertions (console only)
    "catch2_version": str,          # Catch2 version (XML v3 only)
    "format_version": str,          # "v2" or "v3" (XML only)
    "failures": [                   # List of failure details
        {
            "test_name": str,            # Test case name
            "test_file": str,            # Source file path
            "line": int,                 # Line number of failure
            "assertion_type": str,       # REQUIRE, CHECK, etc.
            "original_expression": str,  # Original assertion expression
            "expanded_expression": str,  # Expanded with values
            "exception_message": str,    # Exception details (if applicable)
            "section_path": list,        # Section hierarchy (BDD tests)
            "message": str               # Complete failure message
        }
    ]
}
```

## References

- Catch2 Documentation: https://github.com/catchorg/Catch2
- Catch2 Tutorial: https://github.com/catchorg/Catch2/blob/devel/docs/tutorial.md
- BDD-Style Tests: https://github.com/catchorg/Catch2/blob/devel/docs/test-cases-and-sections.md
- XML Reporter: https://github.com/catchorg/Catch2/blob/devel/docs/reporters.md
- CMake Integration: https://github.com/catchorg/Catch2/blob/devel/docs/cmake-integration.md
- Test Execution: `agents/execute-agent.md`
- Parser Factory: `skills/result-parsing/parser-factory-pattern.md`
- Base Parser Interface: `skills/result-parsing/base-parser-interface.md`
- Google Test Parser: `skills/result-parsing/parsers/gtest-parser.md` (similar C++ framework)

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
