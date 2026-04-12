---
language: python
framework: pytest
test_type: unit
description: Example analysis output for a Python project using pytest
---

# Example Analysis: Python/pytest

This example demonstrates the expected analysis output format for a Python project using the pytest framework.

---

## Analysis Summary

**Project**: example-calculator
**Language**: `python`
**Framework**: `pytest` (Confidence: 0.85)
**Total Source Files**: 3
**Total Testable Units**: 8
**Existing Test Files**: 1

---

## Test Targets

- `src/calculator.py:50` - **divide** [Priority: Critical]
  - Type: function
  - Complexity: 6.5/10
  - Coverage: Not Covered
  - Reason: Error handling (ZeroDivisionError), no tests yet

- `src/calculator.py:35` - **multiply** [Priority: High]
  - Type: function
  - Complexity: 4.0/10
  - Coverage: Not Covered
  - Reason: Moderate complexity, not yet tested

- `src/calculator.py:20` - **subtract** [Priority: Medium]
  - Type: function
  - Complexity: 3.0/10
  - Coverage: Partial
  - Reason: Tested but missing edge cases

- `src/calculator.py:10` - **add** [Priority: Low]
  - Type: function
  - Complexity: 2.5/10
  - Coverage: Covered
  - Reason: Simple function, well tested

---

## Priority Summary

- Critical: 1 target
- High: 1 target
- Medium: 1 target
- Low: 5 targets

Total: 8 testable units

---

## Complexity Analysis

Complexity Distribution:
- Simple (1-3): 6 units
- Moderate (4-6): 2 units
- Complex (7-8): 0 units
- Very Complex (9-10): 0 units

Average Complexity: 3.2/10

Most Complex Units:
1. src/calculator.py:50 - divide (Score: 6.5)
2. src/calculator.py:35 - multiply (Score: 4.0)
3. src/calculator.py:20 - subtract (Score: 3.0)

---

## Coverage Gaps

Partial Coverage (1 file):
- src/calculator.py: 4 functions, 1 test (25% coverage)
  - Missing tests: divide, multiply
  - Partial coverage: subtract (needs edge case tests)

---

## Recommendations

1. **Start with divide function**: Critical priority due to error handling
2. **Add edge case tests for subtract**: Test negative numbers, zero
3. **Generate tests for multiply**: Moderate complexity, straightforward
4. **Maintain existing coverage**: Keep add function tests up to date
5. **Run `/test-generate`**: Auto-generate tests for uncovered functions
