# JavaScript Vitest Test Template

**Purpose**: Template for generating Vitest test files
**Target Language**: JavaScript
**Test Framework**: Vitest
**Version Support**: Vitest 0.30.x+

## Template Structure

```javascript
/**
 * Test module for {MODULE_NAME}.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
{ADDITIONAL_IMPORTS}

describe('{SUITE_NAME}', () => {
  {SETUP_CODE}

  {TEST_CASES}
});
```

## Key Differences from Jest

- Import from `'vitest'` instead of `'@jest/globals'`
- Use `vi` instead of `jest` for mocking (`vi.mock()`, `vi.fn()`, `vi.spyOn()`)
- Otherwise Jest-compatible API

## Example

```javascript
import { describe, it, expect, vi } from 'vitest';
import { add, subtract } from './calculator.js';

describe('Calculator', () => {
  it('should add two numbers', () => {
    const result = add(5, 3);
    expect(result).toBe(8);
  });
});
```

## Mocking with Vitest

```javascript
import { vi } from 'vitest';

// Mock module
vi.mock('./api-client.js');

// Mock function
const mockFn = vi.fn();
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'value' });

// Spy
const spy = vi.spyOn(obj, 'method');
```

## References

- Vitest API: https://vitest.dev/api/
- JavaScript Patterns: `skills/test-generation/javascript-patterns.md`
- Jest Template: `skills/templates/javascript-jest-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
