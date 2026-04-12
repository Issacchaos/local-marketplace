---
title: Redundancy Detection Skill
version: 1.0.0
category: Test Generation
purpose: Detect and prevent redundant test scenario generation by classifying test inputs into equivalence classes and identifying when proposed tests cover already-tested scenarios
target_users: write-agent
user-invocable: false
created: 2026-02-11
last_updated: 2026-02-11
---

# Redundancy Detection Skill

## Overview

This skill provides the write-agent with knowledge and heuristics to detect and prevent redundant test scenario generation. The skill defines equivalence classes for test inputs, classification rules for mapping values to classes, and a detection algorithm to identify when a proposed test covers the same scenario as an existing test.

**Key Concepts**:
- **Equivalence Class**: A category of input values that behave similarly in tests (e.g., all positive small numbers)
- **Redundant Test**: A test that exercises the same equivalence classes as an existing test for the same function
- **Edge Case**: Boundary values, error conditions, or state transitions that require separate testing even if equivalence classes match
- **Happy Path Variation**: Different values within the same equivalence class (e.g., 5 vs 100 are both positive numbers)

**Goal**: Block generation of redundant tests while allowing all unique scenarios and edge cases, providing clear explanations when blocking.

---

## Equivalence Class Definitions

### Numeric Values

#### POSITIVE_SMALL
- **Definition**: Positive integers in the small to moderate range
- **Value Range**: 1 to 100 (inclusive)
- **Language-Agnostic Description**: Any positive whole number within typical calculation range
- **Examples**:
  - Python: `1`, `5`, `42`, `100`
  - JavaScript: `1`, `10`, `99`, `100`
  - Java: `1`, `25`, `100`

#### POSITIVE_LARGE
- **Definition**: Positive integers greater than small range
- **Value Range**: Greater than 100
- **Language-Agnostic Description**: Large positive whole numbers
- **Examples**:
  - Python: `101`, `500`, `10000`, `999999`
  - JavaScript: `200`, `5000`, `1000000`
  - Java: `150`, `10000`, `Integer.MAX_VALUE / 2`

#### NEGATIVE_SMALL
- **Definition**: Negative integers in the small to moderate range
- **Value Range**: -100 to -1 (inclusive)
- **Language-Agnostic Description**: Any negative whole number within typical calculation range
- **Examples**:
  - Python: `-1`, `-5`, `-42`, `-100`
  - JavaScript: `-1`, `-10`, `-99`, `-100`
  - Java: `-1`, `-25`, `-100`

#### NEGATIVE_LARGE
- **Definition**: Negative integers greater than small range in magnitude
- **Value Range**: Less than -100
- **Language-Agnostic Description**: Large negative whole numbers
- **Examples**:
  - Python: `-101`, `-500`, `-10000`, `-999999`
  - JavaScript: `-200`, `-5000`, `-1000000`
  - Java: `-150`, `-10000`, `Integer.MIN_VALUE / 2`

#### ZERO
- **Definition**: The zero value (boundary between positive and negative)
- **Value Range**: Exactly 0
- **Language-Agnostic Description**: Zero - a critical boundary value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `0`, `0.0`
  - JavaScript: `0`, `0.0`
  - Java: `0`, `0L`, `0.0`

#### FLOAT_PRECISION
- **Definition**: Floating point numbers where precision matters
- **Value Range**: Any decimal/float value, especially those with precision issues
- **Language-Agnostic Description**: Decimal numbers that may have rounding or precision behavior
- **Edge Case**: YES - precision issues are distinct from integer arithmetic
- **Examples**:
  - Python: `0.1`, `0.2`, `3.14159`, `1.23e-10`
  - JavaScript: `0.1`, `0.2`, `Math.PI`, `1.5`
  - Java: `0.1f`, `0.2`, `Math.PI`, `1.5d`

#### BOUNDARY_MAX
- **Definition**: Maximum representable values for numeric types
- **Value Range**: Language-specific maximum constants
- **Language-Agnostic Description**: The largest possible numeric value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `sys.maxsize`, `float('inf')`
  - JavaScript: `Number.MAX_SAFE_INTEGER`, `Number.MAX_VALUE`, `Infinity`
  - Java: `Integer.MAX_VALUE`, `Long.MAX_VALUE`, `Double.MAX_VALUE`

#### BOUNDARY_MIN
- **Definition**: Minimum representable values for numeric types
- **Value Range**: Language-specific minimum constants
- **Language-Agnostic Description**: The smallest possible numeric value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `-sys.maxsize - 1`, `float('-inf')`
  - JavaScript: `Number.MIN_SAFE_INTEGER`, `Number.MIN_VALUE`, `-Infinity`
  - Java: `Integer.MIN_VALUE`, `Long.MIN_VALUE`, `Double.MIN_VALUE`

### String Values

#### EMPTY_STRING
- **Definition**: String with zero characters
- **Value Range**: Exactly "" (empty)
- **Language-Agnostic Description**: Empty string - a critical boundary value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `""`, `''`
  - JavaScript: `""`, `''`, ` `` `
  - Java: `""`

#### NON_EMPTY_STRING
- **Definition**: String with one or more characters
- **Value Range**: Any string with length >= 1
- **Language-Agnostic Description**: Any string containing characters
- **Examples**:
  - Python: `"hello"`, `"world"`, `"test123"`, `"a"`, `"very long string..."`
  - JavaScript: `"hello"`, `"world"`, `"test123"`, `"a"`
  - Java: `"hello"`, `"world"`, `"test123"`, `"a"`

### Collection Values

#### EMPTY_COLLECTION
- **Definition**: Collections (arrays, lists, sets, maps) with zero elements
- **Value Range**: Empty collections
- **Language-Agnostic Description**: Empty collection - a critical boundary value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `[]`, `()`, `{}`, `set()`
  - JavaScript: `[]`, `{}`, `new Set()`, `new Map()`
  - Java: `new ArrayList<>()`, `new int[0]`, `Collections.emptyList()`

#### NON_EMPTY_COLLECTION
- **Definition**: Collections with one or more elements
- **Value Range**: Any collection with length/size >= 1
- **Language-Agnostic Description**: Any collection containing elements
- **Examples**:
  - Python: `[1, 2, 3]`, `[4, 5, 6]`, `{"key": "value"}`
  - JavaScript: `[1, 2, 3]`, `[4, 5, 6]`, `{key: "value"}`
  - Java: `Arrays.asList(1, 2, 3)`, `new int[]{4, 5, 6}`

### Special Values

#### NULL_UNDEFINED
- **Definition**: Null, undefined, None, nil, or equivalent absence-of-value
- **Value Range**: Language-specific null/undefined/None/nil
- **Language-Agnostic Description**: Absence of value - a critical boundary value
- **Edge Case**: YES - boundary value requiring separate testing
- **Examples**:
  - Python: `None`
  - JavaScript: `null`, `undefined`
  - Java: `null`
  - Go: `nil`
  - C#: `null`
  - C++: `nullptr`, `NULL`

#### BOOLEAN
- **Definition**: Boolean true/false values
- **Value Range**: true or false
- **Language-Agnostic Description**: Boolean values (true/false)
- **Examples**:
  - Python: `True`, `False`
  - JavaScript: `true`, `false`
  - Java: `true`, `false`

### Edge Case Categories

#### ERROR_CONDITION
- **Definition**: Inputs that trigger error handling, exceptions, or error conditions
- **Value Range**: Any value that causes error behavior
- **Language-Agnostic Description**: Inputs designed to test error handling
- **Edge Case**: YES - each error condition is unique and requires separate testing
- **Examples**:
  - Division by zero: `divide(10, 0)`
  - Overflow: `add(MAX_INT, 1)`
  - Underflow: `subtract(MIN_INT, 1)`
  - Invalid format: `parse_date("invalid")`
  - Out of bounds: `array[999999]`
  - Type mismatch: `add("string", 123)` in typed languages

#### STATE_TRANSITION
- **Definition**: Tests that verify state changes or transitions
- **Value Range**: Inputs/operations that cause state changes
- **Language-Agnostic Description**: Operations that transition system state
- **Edge Case**: YES - each state transition is unique and requires separate testing
- **Examples**:
  - Lock/unlock: `lock() → unlock()`
  - Open/close: `open_file() → close_file()`
  - Start/stop: `start_service() → stop_service()`
  - Connect/disconnect: `connect() → disconnect()`
  - Initialize/teardown: `setup() → teardown()`

#### EDGE_CASE_OTHER
- **Definition**: Other edge cases not covered by specific categories
- **Value Range**: Special scenarios requiring unique testing
- **Language-Agnostic Description**: Miscellaneous edge cases
- **Edge Case**: YES - catch-all for unique scenarios
- **Examples**:
  - Unicode/special characters: `"🎉"`, `"\n\t"`, `"中文"`
  - Very large collections: `[1, 2, 3, ..., 1000000]`
  - Concurrent operations: `parallel_access()`
  - Race conditions: `read_while_writing()`
  - Resource exhaustion: `allocate_huge_memory()`

---

## Classification Rules

### General Classification Process

When analyzing a test, extract input values and classify each according to these rules. Multiple classifications may apply to a single test (e.g., a test with inputs `5` and `0` has both POSITIVE_SMALL and ZERO).

### Language-Specific Heuristics

#### Python

**Literal Value Extraction** (highest confidence):
```python
# Function call arguments
result = add(5, 10)  # Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
output = process("hello")  # Extract: "hello" (NON_EMPTY_STRING)

# Assert statements
assert divide(10, 0)  # Extract: 10 (POSITIVE_SMALL), 0 (ZERO + ERROR_CONDITION)
assert calculate([1, 2, 3]) == 6  # Extract: [1, 2, 3] (NON_EMPTY_COLLECTION)

# Variable assignments
a = 100
b = 200
result = add(a, b)  # Extract: 100 (POSITIVE_LARGE), 200 (POSITIVE_LARGE)
```

**Framework Patterns**:
- **pytest**: `def test_function_name(): assert function(args) == expected`
- **unittest**: `self.assertEqual(function(args), expected)`
- **Test naming**: `test_*` functions

**Classification**:
- Integer 1-100 → POSITIVE_SMALL
- Integer > 100 → POSITIVE_LARGE
- Integer -100 to -1 → NEGATIVE_SMALL
- Integer < -100 → NEGATIVE_LARGE
- Integer 0 → ZERO
- Float/decimal → FLOAT_PRECISION
- `""` → EMPTY_STRING
- Non-empty string → NON_EMPTY_STRING
- `[]`, `()`, `{}`, `set()` → EMPTY_COLLECTION
- Non-empty list/tuple/dict/set → NON_EMPTY_COLLECTION
- `None` → NULL_UNDEFINED
- `True`, `False` → BOOLEAN

#### JavaScript / TypeScript

**Literal Value Extraction**:
```javascript
// Jest expect patterns
expect(add(5, 10)).toBe(15);  // Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
expect(divide(10, 0)).toThrow();  // Extract: 10 (POSITIVE_SMALL), 0 (ZERO + ERROR_CONDITION)

// Function calls in describe/it blocks
it('should process string', () => {
  const result = process("hello");  // Extract: "hello" (NON_EMPTY_STRING)
});

// Variable assignments
const a = 100;
const b = 200;
const result = add(a, b);  // Extract: 100 (POSITIVE_LARGE), 200 (POSITIVE_LARGE)
```

**Framework Patterns**:
- **Jest**: `expect(...).toBe()`, `expect(...).toThrow()`, `expect(...).toEqual()`
- **Mocha/Chai**: `assert.equal()`, `expect().to.equal()`
- **Test structure**: `describe()` and `it()` blocks

**Classification**:
- Integer 1-100 → POSITIVE_SMALL
- Integer > 100 → POSITIVE_LARGE
- Integer -100 to -1 → NEGATIVE_SMALL
- Integer < -100 → NEGATIVE_LARGE
- Integer 0 → ZERO
- Float/decimal → FLOAT_PRECISION
- `""`, `''`, ` `` ` → EMPTY_STRING
- Non-empty string → NON_EMPTY_STRING
- `[]` → EMPTY_COLLECTION
- Non-empty array → NON_EMPTY_COLLECTION
- `null`, `undefined` → NULL_UNDEFINED
- `true`, `false` → BOOLEAN

#### Java

**Literal Value Extraction**:
```java
// JUnit assertEquals patterns
assertEquals(15, add(5, 10));  // Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
assertThrows(ArithmeticException.class, () -> divide(10, 0));  // Extract: 0 (ZERO + ERROR_CONDITION)

// Variable assignments
int a = 100;
int b = 200;
int result = add(a, b);  // Extract: 100 (POSITIVE_LARGE), 200 (POSITIVE_LARGE)

// Method calls
String result = process("hello");  // Extract: "hello" (NON_EMPTY_STRING)
```

**Framework Patterns**:
- **JUnit 4**: `@Test` annotations, `assertEquals()`, `assertNull()`, `assertTrue()`
- **JUnit 5**: `@Test`, `assertEquals()`, `assertThrows()`, `assertAll()`
- **Test naming**: `test*` or `*Test` methods

**Classification**:
- Integer 1-100 → POSITIVE_SMALL
- Integer > 100 → POSITIVE_LARGE
- Integer -100 to -1 → NEGATIVE_SMALL
- Integer < -100 → NEGATIVE_LARGE
- Integer 0 → ZERO
- Float/double → FLOAT_PRECISION
- `""` → EMPTY_STRING
- Non-empty string → NON_EMPTY_STRING
- Empty array/list → EMPTY_COLLECTION
- Non-empty array/list → NON_EMPTY_COLLECTION
- `null` → NULL_UNDEFINED
- `true`, `false` → BOOLEAN

#### C#

**Literal Value Extraction**:
```csharp
// NUnit/xUnit patterns
Assert.AreEqual(15, Add(5, 10));  // Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
Assert.Throws<DivideByZeroException>(() => Divide(10, 0));  // Extract: 0 (ZERO + ERROR_CONDITION)

// Variable assignments
int a = 100;
int b = 200;
int result = Add(a, b);  // Extract: 100 (POSITIVE_LARGE), 200 (POSITIVE_LARGE)
```

**Framework Patterns**:
- **NUnit**: `[Test]` attribute, `Assert.AreEqual()`, `Assert.Throws()`
- **xUnit**: `[Fact]`, `[Theory]`, `Assert.Equal()`, `Assert.Throws()`
- **MSTest**: `[TestMethod]`, `Assert.AreEqual()`

**Classification**: Same as Java (C# and Java have similar type systems)

#### Go

**Literal Value Extraction**:
```go
// testing package patterns
result := add(5, 10)  // Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
if result != 15 {
    t.Errorf("Expected 15, got %d", result)
}

// Error testing
_, err := divide(10, 0)  // Extract: 0 (ZERO + ERROR_CONDITION)
if err == nil {
    t.Error("Expected error, got nil")
}
```

**Framework Patterns**:
- **testing**: `func TestXxx(t *testing.T)`, `t.Errorf()`, `t.Fatalf()`
- **testify**: `assert.Equal()`, `assert.NoError()`

**Classification**:
- Integer 1-100 → POSITIVE_SMALL
- Integer > 100 → POSITIVE_LARGE
- Integer -100 to -1 → NEGATIVE_SMALL
- Integer < -100 → NEGATIVE_LARGE
- Integer 0 → ZERO
- Float64/float32 → FLOAT_PRECISION
- `""` → EMPTY_STRING
- Non-empty string → NON_EMPTY_STRING
- Empty slice → EMPTY_COLLECTION
- Non-empty slice → NON_EMPTY_COLLECTION
- `nil` → NULL_UNDEFINED
- `true`, `false` → BOOLEAN

#### C++

**Literal Value Extraction**:
```cpp
// Google Test patterns
EXPECT_EQ(15, add(5, 10));  // Extract: 5 (POSITIVE_SMALL), 10 (POSITIVE_SMALL)
EXPECT_THROW(divide(10, 0), std::runtime_error);  // Extract: 0 (ZERO + ERROR_CONDITION)

// Variable assignments
int a = 100;
int b = 200;
int result = add(a, b);  // Extract: 100 (POSITIVE_LARGE), 200 (POSITIVE_LARGE)
```

**Framework Patterns**:
- **Google Test**: `TEST()`, `EXPECT_EQ()`, `ASSERT_EQ()`, `EXPECT_THROW()`
- **Catch2**: `TEST_CASE()`, `REQUIRE()`, `CHECK()`
- **Boost.Test**: `BOOST_AUTO_TEST_CASE()`, `BOOST_CHECK_EQUAL()`

**Classification**:
- Integer 1-100 → POSITIVE_SMALL
- Integer > 100 → POSITIVE_LARGE
- Integer -100 to -1 → NEGATIVE_SMALL
- Integer < -100 → NEGATIVE_LARGE
- Integer 0 → ZERO
- Float/double → FLOAT_PRECISION
- `""` → EMPTY_STRING
- Non-empty string → NON_EMPTY_STRING
- Empty vector/array → EMPTY_COLLECTION
- Non-empty vector/array → NON_EMPTY_COLLECTION
- `nullptr`, `NULL` → NULL_UNDEFINED
- `true`, `false` → BOOLEAN

---

## Edge Case Criteria

### What IS an Edge Case (Always Allow)

**Boundary Values**:
- ZERO: Any test using 0 as input
- EMPTY_STRING: Any test using empty string ("")
- EMPTY_COLLECTION: Any test using empty arrays, lists, sets, maps
- NULL_UNDEFINED: Any test using null, None, nil, undefined
- BOUNDARY_MAX: Any test using MAX_INT, MAX_FLOAT, or infinity
- BOUNDARY_MIN: Any test using MIN_INT, MIN_FLOAT, or negative infinity

**Error Conditions**:
- Division by zero
- Overflow (exceeding maximum value)
- Underflow (exceeding minimum value)
- Invalid format or parse errors
- Out of bounds access
- Type mismatch errors
- Resource exhaustion

**Precision Issues**:
- FLOAT_PRECISION: Tests specifically checking floating point arithmetic (e.g., 0.1 + 0.2)
- Rounding behavior
- Decimal precision limits

**State Transitions**:
- STATE_TRANSITION: Tests verifying state changes (locked → unlocked, open → closed)
- Initialization and teardown
- Connection lifecycle
- Resource allocation and cleanup

**Other Special Scenarios**:
- EDGE_CASE_OTHER: Unicode characters, special characters, escape sequences
- Very large collections (performance/memory tests)
- Concurrent operations
- Race conditions

### What is NOT an Edge Case (May Be Redundant)

**Happy Path Variations** (different values in same equivalence class):
- Multiple positive numbers: `test_add(5, 10)` vs `test_add(100, 200)` → BOTH are POSITIVE (redundant)
- Multiple negative numbers: `test_subtract(-5, -3)` vs `test_subtract(-100, -50)` → BOTH are NEGATIVE (redundant)
- Multiple non-empty strings: `test_process("hello")` vs `test_process("world")` → BOTH are NON_EMPTY_STRING (redundant)
- Multiple non-empty collections: `test_sum([1, 2, 3])` vs `test_sum([4, 5, 6])` → BOTH are NON_EMPTY_COLLECTION (redundant)

**Key Principle**: If the only difference is the specific value (not the category), and no edge case class is present, the test is likely redundant.

**Examples of Non-Edge Cases**:
- Large positive when small positive already tested (unless testing overflow)
- Different string content when non-empty string already tested (unless testing special characters)
- Different collection contents when non-empty collection already tested (unless testing performance)
- Different boolean order when boolean already tested

---

## Detection Algorithm

### Step-by-Step Process

Follow this algorithm when generating each test to determine if it's redundant:

#### Step 1: Read Existing Tests in Target File

**Actions**:
1. Use Read tool to get target test file content
2. Identify existing test functions/methods:
   - Python: Functions matching `test_*` pattern
   - JavaScript: Functions in `it()` or `test()` blocks
   - Java: Methods with `@Test` annotation
   - C#: Methods with `[Test]`, `[Fact]`, or `[TestMethod]` attributes
   - Go: Functions matching `Test*` pattern
   - C++: `TEST()` or `TEST_CASE()` macros
3. For each existing test, extract:
   - Function under test (from test name or test body)
   - Input values (literal values from test body)
   - Equivalence classes (classify each input using Classification Rules)

**Output**: List of existing tests with their equivalence classes

#### Step 2: Analyze Proposed Test

**Actions**:
1. Extract function under test from proposed test name or test plan
2. Extract proposed input values from test description or test plan
3. Classify proposed inputs into equivalence classes using Classification Rules
4. Identify if any edge case classes are present (ZERO, EMPTY_*, NULL_UNDEFINED, ERROR_CONDITION, STATE_TRANSITION, FLOAT_PRECISION, BOUNDARY_*, EDGE_CASE_OTHER)

**Output**: Proposed test with its equivalence classes and edge case flag

#### Step 3: Compare Against Existing Tests

**Actions**:
1. Filter existing tests to same function under test (only compare tests for the same function)
2. For each existing test:
   - Normalize equivalence classes:
     - POSITIVE_SMALL and POSITIVE_LARGE → normalize to POSITIVE_SMALL
     - NEGATIVE_SMALL and NEGATIVE_LARGE → normalize to NEGATIVE_SMALL
     - Keep all other classes as-is
   - Check if proposed normalized classes match existing normalized classes
   - If match found, proceed to Step 4

**Normalization Rationale**: POSITIVE_SMALL (5) and POSITIVE_LARGE (500) are both positive numbers. The distinction helps identify them initially, but for redundancy detection they normalize to the same category.

**Output**: Match found (yes/no) with reference to matching existing test

#### Step 4: Apply Edge Case Override

**Edge Case Override Logic**:
- If proposed test has ANY of these equivalence classes:
  - ZERO
  - EMPTY_STRING
  - EMPTY_COLLECTION
  - NULL_UNDEFINED
  - BOUNDARY_MAX
  - BOUNDARY_MIN
  - FLOAT_PRECISION
  - ERROR_CONDITION
  - STATE_TRANSITION
  - EDGE_CASE_OTHER
- Then: **ALLOW the test** even if equivalence classes match existing test
- Rationale: Edge cases require separate testing regardless of overlap

**Happy Path Logic**:
- If proposed test has ONLY these equivalence classes:
  - POSITIVE_SMALL / POSITIVE_LARGE
  - NEGATIVE_SMALL / NEGATIVE_LARGE
  - NON_EMPTY_STRING
  - NON_EMPTY_COLLECTION
  - BOOLEAN
- And: Matches existing test after normalization
- Then: **BLOCK the test** as redundant

**Output**: Allow or block decision

#### Step 5: Block or Allow

**If Redundant** (match found + no edge case override):
- Skip test generation
- Add to blocked tests list
- Generate message using template (Step 6)

**If Unique or Edge Case**:
- Proceed with test generation
- No blocking message needed

#### Step 6: Generate Message (If Blocked)

**Use Message Template** (see Message Templates section):
- Populate all placeholders with test-specific details
- Include: proposed test name, function name, equivalence class explanation, existing test reference, alternative suggestions
- Ensure message is clear and actionable

**Output**: Formatted redundancy message

---

## Conservative Threshold Guidance

**Principle**: When in doubt, allow the test. False negatives (allowing redundant tests) are better than false positives (blocking valid tests).

**Apply Conservative Logic**:
- **Cannot classify input**: Allow (don't block unknown patterns)
- **Ambiguous equivalence class**: Allow (err on side of caution)
- **Parse error reading existing tests**: Allow all (don't block due to technical issues)
- **Missing SKILL.md file**: Allow all (graceful degradation)
- **Uncertain if edge case**: Allow (assume edge case)
- **Complex logic in test**: Allow (don't block if analysis is unclear)

**Target Metrics**:
- False positive rate: < 5% (blocking valid tests)
- Redundancy detection accuracy: > 95% (correctly identifying redundant tests)
- Blocking rate: 30-50% of initially proposed tests (indicates effective detection)

---

## Message Templates

### Template Structure

Use this three-part format when blocking a redundant test:

```
❌ **Test Generation Blocked: Redundant Test Scenario**

**Problem**: The proposed test '{proposed_test_name}' is redundant with existing test coverage.

**Explanation**: Both tests exercise '{function_name}' with {equivalence_class_description}. This scenario is already covered by '{existing_test_name}'.

**Suggestion**:
- Remove '{proposed_test_name}', OR
- Modify to test true edge cases: {alternative_suggestions}

Example edge cases for {function_name}:
- Zero values (0)
- Negative numbers (if not tested)
- Null/empty inputs (if applicable)
- Boundary conditions (MAX_INT, MIN_INT)
- Error conditions (overflow, underflow, division by zero)
```

### Placeholders

- `{proposed_test_name}`: Name of the proposed test being blocked
- `{function_name}`: Name of the function under test
- `{equivalence_class_description}`: Plain language explanation of equivalence classes (e.g., "positive numbers", "non-empty strings")
- `{existing_test_name}`: Name of the existing test that covers this scenario
- `{alternative_suggestions}`: Specific edge cases that could be tested instead

### Example Messages

#### Example 1: Redundant Positive Numbers (Python)

```
❌ **Test Generation Blocked: Redundant Test Scenario**

**Problem**: The proposed test 'test_add_large_numbers' is redundant with existing test coverage.

**Explanation**: Both tests exercise 'add' with positive numbers. This scenario is already covered by 'test_add_positive_numbers'.

**Suggestion**:
- Remove 'test_add_large_numbers', OR
- Modify to test true edge cases: zero values, negative numbers, overflow conditions

Example edge cases for add:
- Zero values (0 + 5)
- Negative numbers (-5 + -3)
- Null/empty inputs (if applicable)
- Boundary conditions (MAX_INT + 1)
- Error conditions (overflow)
```

#### Example 2: Redundant Strings (JavaScript)

```
❌ **Test Generation Blocked: Redundant Test Scenario**

**Problem**: The proposed test 'test_process_another_string' is redundant with existing test coverage.

**Explanation**: Both tests exercise 'process' with non-empty strings. This scenario is already covered by 'test_process_string'.

**Suggestion**:
- Remove 'test_process_another_string', OR
- Modify to test true edge cases: empty string, null/undefined, special characters

Example edge cases for process:
- Zero values (not applicable for strings)
- Negative numbers (not applicable for strings)
- Null/empty inputs ("", null, undefined)
- Boundary conditions (very long strings)
- Error conditions (invalid encoding, special characters like emojis)
```

#### Example 3: Redundant Collections (Java)

```
❌ **Test Generation Blocked: Redundant Test Scenario**

**Problem**: The proposed test 'testSumDifferentNumbers' is redundant with existing test coverage.

**Explanation**: Both tests exercise 'sum' with non-empty collections of positive numbers. This scenario is already covered by 'testSumPositiveNumbers'.

**Suggestion**:
- Remove 'testSumDifferentNumbers', OR
- Modify to test true edge cases: empty collection, null, negative numbers

Example edge cases for sum:
- Zero values (collection with zeros)
- Negative numbers ([-1, -2, -3])
- Null/empty inputs (null, empty list)
- Boundary conditions (very large collections)
- Error conditions (null elements in collection)
```

### Alternative Suggestions by Equivalence Class

Use these suggestions based on what's already tested:

**When POSITIVE is already tested**:
- Zero values (0)
- Negative numbers
- Boundary conditions (MAX_INT, MIN_INT)
- Error conditions (overflow)
- Null/empty inputs (if applicable)

**When NON_EMPTY_STRING is already tested**:
- Empty string ("")
- Null/undefined
- Special characters (emojis, escape sequences, unicode)
- Very long strings
- Invalid encoding

**When NON_EMPTY_COLLECTION is already tested**:
- Empty collection
- Null
- Very large collections (performance)
- Collections with null elements
- Concurrent modification

**When NEGATIVE is already tested**:
- Zero values (0)
- Positive numbers (if not tested)
- Boundary conditions (MIN_INT)
- Error conditions (underflow)

**When BOOLEAN is already tested**:
- Edge cases may be limited; consider error conditions or null inputs instead

---

## Usage in Write-Agent

### When to Read This Skill

**Step 1: Load Context and Plan**
- Read `skills/redundancy-detection/SKILL.md` at the start of test generation workflow
- Load equivalence class definitions, classification rules, and detection algorithm into context
- Keep skill knowledge available throughout Steps 2-7

### Where to Apply Redundancy Detection

**Step 4: Generate Individual Test Methods**
- Before generating code for each test scenario, apply redundancy detection
- Follow the Detection Algorithm (6 steps) for each proposed test
- Skip generation if redundant, proceed if unique or edge case

### How to Report Blocked Tests

**In Generation Summary**:
Add a "Redundant Tests Blocked" section showing:
- Count of blocked tests
- List of blocked test names
- Brief explanation for each (equivalence class + existing test reference)

**Example Format**:
```markdown
## Test Generation Summary

**Tests Generated**: 8
**Tests Blocked**: 3 (redundant)

### Redundant Tests Blocked
- `test_add_large_numbers`: Redundant with test_add_positive_numbers (both test positive + positive)
- `test_process_another_string`: Redundant with test_process_string (both test non-empty strings)
- `test_sum_different_numbers`: Redundant with test_sum_positive_numbers (both test non-empty collections of positives)

### Tests Generated
1. test_add_positive_numbers ✓
2. test_add_with_zero ✓ (edge case: boundary value)
3. test_add_negative_numbers ✓
4. test_divide_by_zero ✓ (edge case: error condition)
5. test_process_string ✓
6. test_process_empty_string ✓ (edge case: boundary value)
7. test_sum_positive_numbers ✓
8. test_sum_empty_collection ✓ (edge case: boundary value)
```

### Integration with Existing Workflow

**No changes to Steps 1-3** (Load Context, Understand Source, Generate Structure)

**Modified Step 4**:
```markdown
### Step 4: Generate Individual Test Methods

For each test scenario in test plan:

a. **Check redundancy** (apply redundancy-detection skill):
   - Read target test file (if exists) to identify existing tests
   - Classify proposed test inputs using equivalence class rules
   - Compare against existing tests for same function
   - Apply edge case override if proposed test is boundary/error condition
   - If redundant: Skip generation, add to blocked tests list with message
   - If unique or edge case: Proceed to generation

b. Generate test code using template and patterns

c. Apply mocking strategies if needed

d. Validate syntax and conventions
```

**Modified Generation Summary** (Step 7):
- Add "Redundant Tests Blocked" section
- Include blocked test count in metadata

---

## Cross-Language Consistency

### Equivalence Class Mapping

**Null/Undefined Mapping**:
- Python: `None` → NULL_UNDEFINED
- JavaScript: `null`, `undefined` → NULL_UNDEFINED
- Java: `null` → NULL_UNDEFINED
- Go: `nil` → NULL_UNDEFINED
- C#: `null` → NULL_UNDEFINED
- C++: `nullptr`, `NULL` → NULL_UNDEFINED

**Empty String Mapping**:
- All languages: `""` → EMPTY_STRING
- JavaScript also: `''`, ` `` ` → EMPTY_STRING

**Empty Collection Mapping**:
- Python: `[]`, `()`, `{}`, `set()` → EMPTY_COLLECTION
- JavaScript: `[]`, `{}`, `new Set()`, `new Map()` → EMPTY_COLLECTION
- Java: `new ArrayList<>()`, `new int[0]`, `Collections.emptyList()` → EMPTY_COLLECTION
- Go: `nil` slice, empty slice `[]type{}` → EMPTY_COLLECTION
- C#: `new List<T>()`, `new int[0]` → EMPTY_COLLECTION
- C++: `std::vector<T>()`, empty array `{}` → EMPTY_COLLECTION

**Boundary Max Mapping**:
- Python: `sys.maxsize`, `float('inf')` → BOUNDARY_MAX
- JavaScript: `Number.MAX_SAFE_INTEGER`, `Number.MAX_VALUE`, `Infinity` → BOUNDARY_MAX
- Java: `Integer.MAX_VALUE`, `Long.MAX_VALUE`, `Double.MAX_VALUE` → BOUNDARY_MAX
- Go: `math.MaxInt64`, `math.Inf(1)` → BOUNDARY_MAX
- C#: `int.MaxValue`, `long.MaxValue`, `double.MaxValue` → BOUNDARY_MAX
- C++: `INT_MAX`, `LONG_MAX`, `DBL_MAX` → BOUNDARY_MAX

**Boundary Min Mapping**:
- Python: `-sys.maxsize - 1`, `float('-inf')` → BOUNDARY_MIN
- JavaScript: `Number.MIN_SAFE_INTEGER`, `-Infinity` → BOUNDARY_MIN
- Java: `Integer.MIN_VALUE`, `Long.MIN_VALUE`, `Double.MIN_VALUE` → BOUNDARY_MIN
- Go: `math.MinInt64`, `math.Inf(-1)` → BOUNDARY_MIN
- C#: `int.MinValue`, `long.MinValue`, `double.MinValue` → BOUNDARY_MIN
- C++: `INT_MIN`, `LONG_MIN`, `DBL_MIN` → BOUNDARY_MIN

### Syntax Pattern Variations

**Test Function/Method Naming**:
- Python pytest: `def test_function_name():`
- Python unittest: `def test_function_name(self):`
- JavaScript Jest: `it('should do something', () => {})` or `test('description', () => {})`
- Java JUnit: `@Test public void testFunctionName()` or `@Test void functionName()`
- C# NUnit: `[Test] public void TestFunctionName()`
- C# xUnit: `[Fact] public void FunctionName()`
- Go: `func TestFunctionName(t *testing.T)`
- C++ Google Test: `TEST(TestSuiteName, TestName)`

**Assertion Patterns**:
- Python pytest: `assert function(args) == expected`
- Python unittest: `self.assertEqual(function(args), expected)`
- JavaScript Jest: `expect(function(args)).toBe(expected)`
- Java JUnit: `assertEquals(expected, function(args))`
- C# NUnit: `Assert.AreEqual(expected, function(args))`
- C# xUnit: `Assert.Equal(expected, function(args))`
- Go testing: `if got != expected { t.Errorf(...) }`
- C++ Google Test: `EXPECT_EQ(expected, function(args))`

### Framework-Specific Considerations

**Python**:
- pytest: More flexible, uses plain `assert` statements
- unittest: Class-based, uses `self.assert*` methods
- Both follow `test_*` naming convention

**JavaScript/TypeScript**:
- Jest: `expect()` with matchers (`.toBe()`, `.toEqual()`, `.toThrow()`)
- Mocha/Chai: `assert.*()` or `expect().to.*` syntax
- Both use `describe()`/`it()` blocks

**Java**:
- JUnit 4: `@Test` annotation, `assert*()` methods
- JUnit 5: `@Test`, improved assertions like `assertAll()`, `assertThrows()`
- Same equivalence class rules apply to both

**C#**:
- NUnit: `[Test]` attribute, `Assert.*()` methods
- xUnit: `[Fact]` attribute, `Assert.*()` methods
- MSTest: `[TestMethod]` attribute, `Assert.*()` methods
- Same equivalence class rules apply to all

**Go**:
- testing: `Test*` function naming, `t.Error*()` methods
- testify: Third-party library with `assert.*()` methods
- Same equivalence class rules apply

**C++**:
- Google Test: `TEST()` macro, `EXPECT_*()` and `ASSERT_*()` macros
- Catch2: `TEST_CASE()` macro, `REQUIRE()` and `CHECK()` macros
- Boost.Test: `BOOST_AUTO_TEST_CASE()`, `BOOST_CHECK_*()` macros
- Same equivalence class rules apply to all

### Conservative Handling of Language-Specific Edge Cases

**When uncertain about language-specific behavior**:
- Default to ALLOWING the test
- Example: Python's `None` vs JavaScript's `null` and `undefined` - if uncertain whether they're equivalent in a specific context, allow both tests
- Example: Java's checked vs unchecked exceptions - allow separate tests for different exception types

**Document language-specific edge cases**:
- If a language has unique edge cases (e.g., JavaScript's `NaN`, Python's `-0`), treat as EDGE_CASE_OTHER
- When in doubt, classify as edge case rather than happy path variation

---

## Examples

### Python pytest Examples

#### Example 1: Redundant Positive Numbers (Blocked)

**Existing Test**:
```python
def test_add_positive_numbers():
    result = add(2, 3)
    assert result == 5
```
- Function: `add`
- Inputs: `2` (POSITIVE_SMALL), `3` (POSITIVE_SMALL)
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL

**Proposed Test**:
```python
def test_add_large_numbers():
    result = add(100, 200)
    assert result == 300
```
- Function: `add`
- Inputs: `100` (POSITIVE_LARGE), `200` (POSITIVE_LARGE)
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL (after normalization)
- Edge case: NO
- **Decision**: BLOCK (matches existing test, no edge case)

#### Example 2: Zero Edge Case (Allowed)

**Existing Test**:
```python
def test_add_positive_numbers():
    result = add(2, 3)
    assert result == 5
```
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL

**Proposed Test**:
```python
def test_add_with_zero():
    result = add(0, 5)
    assert result == 5
```
- Function: `add`
- Inputs: `0` (ZERO), `5` (POSITIVE_SMALL)
- Edge case: YES (ZERO is boundary value)
- **Decision**: ALLOW (edge case override)

#### Example 3: Division by Zero (Allowed)

**Existing Test**:
```python
def test_divide_positive_numbers():
    result = divide(10, 2)
    assert result == 5
```
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL

**Proposed Test**:
```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```
- Function: `divide`
- Inputs: `10` (POSITIVE_SMALL), `0` (ZERO + ERROR_CONDITION)
- Edge case: YES (ERROR_CONDITION)
- **Decision**: ALLOW (error condition is unique)

#### Example 4: Negative Numbers (Allowed)

**Existing Test**:
```python
def test_add_positive_numbers():
    result = add(2, 3)
    assert result == 5
```
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL

**Proposed Test**:
```python
def test_add_negative_numbers():
    result = add(-5, -3)
    assert result == -8
```
- Function: `add`
- Inputs: `-5` (NEGATIVE_SMALL), `-3` (NEGATIVE_SMALL)
- Normalized: NEGATIVE_SMALL + NEGATIVE_SMALL
- Edge case: NO
- **Decision**: ALLOW (different equivalence class: NEGATIVE vs POSITIVE)

### JavaScript Jest Examples

#### Example 1: Redundant Non-Empty Strings (Blocked)

**Existing Test**:
```javascript
it('should process string', () => {
  const result = process("hello");
  expect(result).toBe("HELLO");
});
```
- Function: `process`
- Inputs: `"hello"` (NON_EMPTY_STRING)

**Proposed Test**:
```javascript
it('should process another string', () => {
  const result = process("world");
  expect(result).toBe("WORLD");
});
```
- Function: `process`
- Inputs: `"world"` (NON_EMPTY_STRING)
- Edge case: NO
- **Decision**: BLOCK (same equivalence class, no edge case)

#### Example 2: Empty String Edge Case (Allowed)

**Existing Test**:
```javascript
it('should process string', () => {
  const result = process("hello");
  expect(result).toBe("HELLO");
});
```
- Inputs: NON_EMPTY_STRING

**Proposed Test**:
```javascript
it('should handle empty string', () => {
  const result = process("");
  expect(result).toBe("");
});
```
- Function: `process`
- Inputs: `""` (EMPTY_STRING)
- Edge case: YES (boundary value)
- **Decision**: ALLOW (edge case override)

#### Example 3: Error Condition (Allowed)

**Existing Test**:
```javascript
it('should divide numbers', () => {
  const result = divide(10, 2);
  expect(result).toBe(5);
});
```
- Normalized: POSITIVE_SMALL + POSITIVE_SMALL

**Proposed Test**:
```javascript
it('should throw on division by zero', () => {
  expect(() => divide(10, 0)).toThrow();
});
```
- Function: `divide`
- Inputs: `10` (POSITIVE_SMALL), `0` (ZERO + ERROR_CONDITION)
- Edge case: YES (ERROR_CONDITION)
- **Decision**: ALLOW (error condition is unique)

### Java JUnit Examples

#### Example 1: Redundant Positive Collections (Blocked)

**Existing Test**:
```java
@Test
public void testSumPositiveNumbers() {
    List<Integer> numbers = Arrays.asList(1, 2, 3);
    int result = sum(numbers);
    assertEquals(6, result);
}
```
- Function: `sum`
- Inputs: `[1, 2, 3]` (NON_EMPTY_COLLECTION with POSITIVE values)

**Proposed Test**:
```java
@Test
public void testSumDifferentNumbers() {
    List<Integer> numbers = Arrays.asList(4, 5, 6);
    int result = sum(numbers);
    assertEquals(15, result);
}
```
- Function: `sum`
- Inputs: `[4, 5, 6]` (NON_EMPTY_COLLECTION with POSITIVE values)
- Edge case: NO
- **Decision**: BLOCK (same equivalence class, no edge case)

#### Example 2: Empty Collection Edge Case (Allowed)

**Existing Test**:
```java
@Test
public void testSumPositiveNumbers() {
    List<Integer> numbers = Arrays.asList(1, 2, 3);
    int result = sum(numbers);
    assertEquals(6, result);
}
```
- Inputs: NON_EMPTY_COLLECTION

**Proposed Test**:
```java
@Test
public void testSumEmptyCollection() {
    List<Integer> numbers = new ArrayList<>();
    int result = sum(numbers);
    assertEquals(0, result);
}
```
- Function: `sum`
- Inputs: `[]` (EMPTY_COLLECTION)
- Edge case: YES (boundary value)
- **Decision**: ALLOW (edge case override)

#### Example 3: Null Edge Case (Allowed)

**Existing Test**:
```java
@Test
public void testProcessString() {
    String result = process("hello");
    assertEquals("HELLO", result);
}
```
- Inputs: NON_EMPTY_STRING

**Proposed Test**:
```java
@Test
public void testProcessNull() {
    String result = process(null);
    assertNull(result);
}
```
- Function: `process`
- Inputs: `null` (NULL_UNDEFINED)
- Edge case: YES (boundary value)
- **Decision**: ALLOW (edge case override)

---

## Known Limitations

**Scope**:
- Same-file redundancy detection only (does not analyze tests across multiple files)
- No support for parametrized tests (e.g., `@pytest.mark.parametrize`)
- No detection of redundant assertions within same test method

**Classification Challenges**:
- Complex test logic may be difficult to classify accurately
- Dynamic value generation (e.g., `random.randint()`) cannot be classified
- Mocked values may not be visible in test code

**Conservative Approach**:
- When uncertain, algorithm defaults to allowing tests
- May miss some redundant tests to avoid blocking valid tests
- Target: < 5% false positive rate, which may result in < 100% redundancy detection

**Performance**:
- Large test files (> 100 tests) may slow down analysis
- Target: < 10 seconds added to write-agent workflow

---

## Validation Results

**Validation Status**: Awaiting execution of acceptance tests per TASK-005

**Placeholder for Results**:
- Redundancy detection accuracy: TBD (target > 95%)
- Edge case identification: TBD (target > 90%)
- Blocking rate: TBD (target 30-50%)
- False positive rate: TBD (target < 5%)
- Performance: TBD (target < 10 seconds per file)

**To be updated after validation testing completes.**

---

## Summary

This skill provides write-agent with comprehensive guidance to:
1. Classify test inputs into 17 equivalence classes
2. Detect redundant test scenarios by comparing equivalence classes
3. Distinguish true edge cases from happy path variations
4. Block redundant test generation with clear, actionable messages
5. Apply consistent rules across 7 programming languages

**Key Principles**:
- Edge cases always require separate testing (boundary values, errors, state transitions)
- Happy path variations (different values in same class) are redundant
- When uncertain, allow the test (conservative threshold)
- Provide clear messages without jargon

**Integration**:
- Read this skill in Step 1 of write-agent workflow
- Apply redundancy detection in Step 4 before generating each test
- Report blocked tests in generation summary

---
