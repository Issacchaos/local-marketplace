# Test Execution Report

**Generated**: 2026-01-16 10:30:00
**Framework**: pytest

---

## Execution Summary

**Exit Code**: 1 (test failures detected)
**Total Duration**: 2.5 seconds

**Test Results**:
- Total Tests: 10
- Passed: 8
- Failed: 2
- Errors: 1

**Status**: ❌ Tests failed

---

## Failure Details

Error: TimeoutError: Test execution exceeded 300 seconds
  File: test_calculator.py, line 42
  Test: test_calculator.py::test_division_by_zero
  
FAILED test_calculator.py::test_invalid_input - AssertionError: Expected ValueError, got TypeError
  File: test_calculator.py, line 58

Exception: Database connection timeout after 30 seconds
  Context: Integration test suite initialization
  
---
