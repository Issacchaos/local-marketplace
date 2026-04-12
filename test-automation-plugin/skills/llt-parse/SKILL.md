---
name: llt-parse
description: Parse Catch2 test results from XML reports and console logs
version: 1.0.0
category: LowLevelTests Results
user-invocable: true
---

# llt-parse: Test Result Parsing

**Version**: 1.0.0
**Category**: LowLevelTests Results
**Purpose**: Parse Catch2 test results from XML reports and/or console logs

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.

---

## Overview

Parses test results from LowLevelTests (LLT) execution output in multiple formats:
- **Catch2 XML reports** (JUnit-style v3, native v3, and v2 formats -- auto-detected)
- **Catch2 console logs** (text output, best-effort accuracy)
- **Mixed format** (both XML and console provided, with XML prioritized for overlapping tests)

---

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `xml` | At least one of xml/console | Path to Catch2 XML report file |
| `console` | At least one of xml/console | Path to Catch2 console log file |

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "statistics": {
    "total_tests": 42,
    "passed": 40,
    "failed": 2,
    "skipped": 0,
    "pass_rate": 95.24,
    "total_duration": 0.123456
  },
  "test_results": [
    {
      "test_name": "LruCache: Basic operations",
      "status": "passed",
      "duration": 0.002
    },
    {
      "test_name": "LruCache: Eviction policy",
      "status": "failed",
      "duration": 0.005,
      "failure_details": {
        "assertion_type": "REQUIRE",
        "expression": "cache.size() == 2",
        "message": "cache.size() == 3",
        "file": "/path/to/LruCacheTest.cpp",
        "line": 42
      }
    }
  ],
  "sources": {
    "xml": "test_results.xml",
    "console": null
  }
}
```

---

## Parsing Algorithm

### XML Parsing (Catch2 XML Reports)

The parser auto-detects the XML format from the root element tag:

#### Format 1: JUnit-style v3 (root: `<testsuites>`)

```xml
<testsuites>
  <testsuite>
    <testcase name="..." time="...">
      <failure message="..." type="...">failure text</failure>
    </testcase>
  </testsuite>
</testsuites>
```

- Find all `<testcase>` elements inside `<testsuite>` elements.
- Extract `name` attribute for test name, `time` attribute for duration (float seconds).
- If child `<failure>` element exists: status is `"failed"`.
  - `assertion_type` from failure's `type` attribute.
  - `message` from failure's `message` attribute.
  - Parse failure text body: look for `file:line` patterns and `REQUIRE(expression)` / `CHECK(expression)` patterns.
- If child `<skipped>` element exists: status is `"skipped"`.
- Otherwise: status is `"passed"`.

#### Format 2: Catch2 Native v3 (root: `<Catch2TestRun>`)

```xml
<Catch2TestRun>
  <TestCase name="..." filename="..." line="...">
    <Expression success="false" type="REQUIRE" filename="..." line="...">
      <Original>expression text</Original>
      <Expanded>expanded text</Expanded>
    </Expression>
    <OverallResult success="true|false" skips="0"/>
  </TestCase>
</Catch2TestRun>
```

- Find all `<TestCase>` elements.
- Check `<OverallResult>` for success/skip status.
- For failures, find `<Expression success="false">` elements and extract:
  - `type` attribute for assertion type
  - `filename` and `line` attributes for location
  - `<Original>` child text for expression
  - `<Expanded>` child text for expansion message
- Also check for `<FatalErrorCondition>` (crashes).
- Duration: sum `durationInSeconds` attributes from `<Expression>` elements.

#### Format 3: Catch2 v2 (root: `<Catch>` or `<Group>`)

```xml
<Catch>
  <Group>
    <TestCase name="...">
      <Expression success="false" type="REQUIRE" filename="..." line="...">
        <Original>expression</Original>
        <Expanded>expansion</Expanded>
      </Expression>
      <OverallResult durationInSeconds="0.001"/>
    </TestCase>
  </Group>
</Catch>
```

- Find all `<TestCase>` elements.
- Duration from `<OverallResult durationInSeconds="...">`.
- Failed expressions: `<Expression success="false">`.
- Extract assertion type, expression text, expansion text, filename, and line from attributes and child elements.

### Console Log Parsing (Catch2 Console Output)

Console parsing is best-effort and extracts less metadata than XML:

1. **Parse failed test cases** from the console output:
   - Look for lines of 10+ dashes (`-{10,}`) indicating test case boundaries.
   - The line immediately after dashes is the test case name.
   - Look for failure patterns: `file:line: FAILED:`
   - Extract assertion type from lines like `  REQUIRE( expression )`
   - Extract expansion from lines after `with expansion:` (indented lines).

2. **Parse summary** from end of output:
   - All passed: `All tests passed (N assertions in M test cases)`
   - Mixed: `test cases: X | Y passed | Z failed`
   - If total tests from summary exceeds parsed failures, the difference are inferred as passed (Catch2 only prints failure details).

3. **Console parsing limitations**:
   - No exact durations (set to 0.0)
   - Inferred passed tests get placeholder names (`Test #1`, `Test #2`, etc.)
   - Cannot extract SECTION details

### Result Merging (when both XML and console provided)

1. Build a lookup of XML results by test name.
2. Start with all XML results (prioritized since they have more complete metadata).
3. For each console result, add it only if its test name does NOT appear in the XML results.
4. Discard console duplicates.

### Statistics Calculation

From the final merged results list:
- `total_tests`: count of all results
- `passed`: count where `status == "passed"`
- `failed`: count where `status == "failed"`
- `skipped`: count where `status == "skipped"`
- `pass_rate`: `(passed / total_tests) * 100`, rounded to 2 decimal places
- `total_duration`: sum of all `duration` values, rounded to 6 decimal places

---

## Error Handling

| Error Code | Condition |
|------------|-----------|
| `MISSING_INPUT` | Neither `--xml` nor `--console` provided |
| `FILE_NOT_FOUND` | Input file does not exist |
| `XML_PARSE_ERROR` | XML file is malformed or unsupported format |
| `CONSOLE_PARSE_ERROR` | Console log parsing failed |

---

## Limitations

1. Console logs may lack metadata present in XML (exact durations, SECTION details)
2. Duplicate test names: only first occurrence preserved during merging
3. Severely malformed input may result in partial parsing or errors
