# JavaScript Jest Test Template

**Purpose**: Template for generating Jest test files with proper structure and patterns
**Target Language**: JavaScript
**Test Framework**: Jest
**Version Support**: Jest 27.x, 28.x, 29.x

## Template Structure

### Basic Test File Template

```javascript
/**
 * Test module for {MODULE_NAME}.
 *
 * This test file covers:
 * - {TEST_COVERAGE_AREA_1}
 * - {TEST_COVERAGE_AREA_2}
 * - {TEST_COVERAGE_AREA_3}
 */

import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
{ADDITIONAL_IMPORTS}

// ============================================================================
// Test Suite: {SUITE_NAME}
// ============================================================================

describe('{SUITE_NAME}', () => {
  {SETUP_CODE}

  {TEST_CASES}
});
```

## Template Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{MODULE_NAME}` | Module being tested | `calculator`, `apiClient`, `userService` |
| `{TEST_COVERAGE_AREA_N}` | Coverage areas | `Addition operations`, `Error handling` |
| `{ADDITIONAL_IMPORTS}` | Required imports | `import { add, subtract } from './calculator.js';` |
| `{SUITE_NAME}` | Test suite name | `Calculator`, `API Client` |
| `{SETUP_CODE}` | beforeEach/afterEach | Setup and teardown code |
| `{TEST_CASES}` | Individual test cases | Generated test methods |

## Jest Conventions

### File Naming
- `*.test.js` or `*.spec.js`
- Location: `__tests__/` directory or alongside source files
- Example: `calculator.test.js`, `api-client.spec.js`

### Test Structure
- Suite: `describe('name', () => {})`
- Test: `it('should...', () => {})` or `test('...', () => {})`
- Setup: `beforeEach()`, `afterEach()`, `beforeAll()`, `afterAll()`

## Test Method Template (AAA Pattern)

```javascript
it('should {ACTION} when {CONDITION}', () => {
  // Arrange
  {ARRANGE_CODE}

  // Act
  {ACT_CODE}

  // Assert
  {ASSERT_CODE}
});
```

## Complete Examples

### Example 1: Simple Function Tests

```javascript
/**
 * Test module for calculator.
 * Tests arithmetic operations.
 */

import { describe, it, expect } from '@jest/globals';
import { add, subtract, multiply, divide } from './calculator.js';

describe('Calculator', () => {
  describe('add', () => {
    it('should add two positive numbers', () => {
      // Arrange
      const a = 5;
      const b = 3;

      // Act
      const result = add(a, b);

      // Assert
      expect(result).toBe(8);
    });

    it('should handle negative numbers', () => {
      const result = add(-5, -3);
      expect(result).toBe(-8);
    });
  });

  describe('divide', () => {
    it('should divide two numbers', () => {
      const result = divide(10, 2);
      expect(result).toBe(5);
    });

    it('should throw error when dividing by zero', () => {
      expect(() => divide(10, 0)).toThrow('Division by zero');
    });
  });
});
```

### Example 2: Tests with Setup/Teardown

```javascript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { Database } from './database.js';

describe('Database', () => {
  let db;

  beforeEach(() => {
    // Arrange - Create fresh database for each test
    db = new Database();
    db.connect();
  });

  afterEach(() => {
    // Cleanup
    db.disconnect();
  });

  it('should insert a record', () => {
    // Arrange
    const record = { id: 1, name: 'Alice' };

    // Act
    db.insert(record);

    // Assert
    expect(db.count()).toBe(1);
    expect(db.find(1)).toEqual(record);
  });

  it('should delete a record', () => {
    // Arrange
    db.insert({ id: 1, name: 'Alice' });

    // Act
    db.delete(1);

    // Assert
    expect(db.count()).toBe(0);
  });
});
```

### Example 3: Async Tests

```javascript
import { describe, it, expect } from '@jest/globals';
import { fetchUser, saveUser } from './api.js';

describe('API Client', () => {
  describe('fetchUser', () => {
    it('should fetch user data', async () => {
      // Arrange
      const userId = 123;

      // Act
      const user = await fetchUser(userId);

      // Assert
      expect(user).toHaveProperty('id', userId);
      expect(user).toHaveProperty('name');
    });

    it('should handle 404 errors', async () => {
      // Arrange
      const invalidId = 999;

      // Act & Assert
      await expect(fetchUser(invalidId)).rejects.toThrow('User not found');
    });
  });
});
```

### Example 4: Mocking

```javascript
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { UserService } from './user-service.js';
import * as apiClient from './api-client.js';

// Mock the API client module
jest.mock('./api-client.js');

describe('UserService', () => {
  let userService;

  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();

    // Arrange
    userService = new UserService();
  });

  it('should fetch and process user data', async () => {
    // Arrange
    const mockUser = { id: 1, name: 'Alice', age: 30 };
    apiClient.getUser.mockResolvedValue(mockUser);

    // Act
    const result = await userService.processUser(1);

    // Assert
    expect(apiClient.getUser).toHaveBeenCalledWith(1);
    expect(result.displayName).toBe('Alice (30)');
  });

  it('should handle API errors', async () => {
    // Arrange
    apiClient.getUser.mockRejectedValue(new Error('Network error'));

    // Act & Assert
    await expect(userService.processUser(1)).rejects.toThrow('Network error');
  });
});
```

## Best Practices

1. **One Concept Per Test**: Each test should verify one specific behavior
2. **Descriptive Names**: Use "should [action] when [condition]" format
3. **AAA Pattern**: Arrange-Act-Assert for clarity
4. **Independent Tests**: No shared state between tests
5. **Mock External Dependencies**: Isolate unit under test
6. **Clean Up**: Use afterEach to restore mocks

## Jest-Specific Features

### Matchers
```javascript
expect(value).toBe(5);                 // Strict equality
expect(value).toEqual({ a: 1 });       // Deep equality
expect(array).toContain('item');       // Array contains
expect(fn).toThrow('error');           // Exception
expect(mockFn).toHaveBeenCalled();     // Mock called
```

### Mocking
```javascript
jest.mock('./module');                 // Mock entire module
const mockFn = jest.fn();              // Create mock function
jest.spyOn(obj, 'method');            // Spy on method
```

### Async
```javascript
it('async test', async () => {
  const result = await asyncFunction();
  expect(result).toBe(expected);
});
```

## References

- Jest API: https://jestjs.io/docs/api
- Jest Matchers: https://jestjs.io/docs/expect
- Jest Mock Functions: https://jestjs.io/docs/mock-functions
- JavaScript Patterns: `skills/test-generation/javascript-patterns.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
