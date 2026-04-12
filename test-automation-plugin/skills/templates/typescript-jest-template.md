# TypeScript Jest Test Template

**Purpose**: Template for generating Jest test files with TypeScript type annotations
**Target Language**: TypeScript
**Test Framework**: Jest + ts-jest
**Version Support**: Jest 27.x+, ts-jest 29.x+, TypeScript 4.0+

## Template Structure

### Basic Test File Template

```typescript
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
| `{MODULE_NAME}` | Module being tested | `Calculator`, `UserService` |
| `{TEST_COVERAGE_AREA_N}` | Coverage areas | `Type-safe operations`, `Async functionality` |
| `{ADDITIONAL_IMPORTS}` | Required imports with types | `import { User, UserRole } from './types';` |
| `{SUITE_NAME}` | Test suite name | `Calculator`, `UserService` |
| `{SETUP_CODE}` | Setup with types | `let service: UserService;` |
| `{TEST_CASES}` | Individual test cases | Generated test methods with types |

## TypeScript Conventions

### File Naming
- `*.test.ts` or `*.spec.ts` for plain TypeScript
- `*.test.tsx` or `*.spec.tsx` for React components
- Location: `__tests__/` directory or alongside source files
- Example: `calculator.test.ts`, `userService.spec.ts`

### Import Structure
```typescript
// Test framework imports
import { describe, it, expect, jest, beforeEach } from '@jest/globals';

// Type imports
import type { User, UserRole } from './types';

// Value imports
import { UserService } from './userService';
import { createMockUser } from './testUtils';
```

## Test Method Template (AAA Pattern with Types)

```typescript
it('should {ACTION} when {CONDITION}', () => {
  // Arrange
  {ARRANGE_CODE_WITH_TYPES}

  // Act
  {ACT_CODE}

  // Assert
  {ASSERT_CODE}
});
```

## Complete Examples

### Example 1: Simple Function Tests with Types

```typescript
/**
 * Test module for calculator.
 * Tests type-safe arithmetic operations.
 */

import { describe, it, expect } from '@jest/globals';
import { add, subtract, multiply, divide } from './calculator';

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

    it('should return number type', () => {
      const result = add(1, 2);
      expect(typeof result).toBe('number');
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

    it('should accept only numbers', () => {
      // TypeScript prevents: divide("10", 2)
      // This test validates runtime behavior matches types
      const result = divide(10, 2);
      expect(result).toBe(5);
    });
  });
});
```

### Example 2: Interface and Type Testing

```typescript
/**
 * Test module for UserService.
 * Tests user management with TypeScript interfaces.
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import type { User, CreateUserInput, UserRole } from './types';
import { UserService } from './userService';

describe('UserService', () => {
  let userService: UserService;

  beforeEach(() => {
    // Arrange - Create fresh instance with proper type
    userService = new UserService();
  });

  afterEach(() => {
    // Cleanup
    userService.clear();
  });

  describe('createUser', () => {
    it('should create user with all required fields', () => {
      // Arrange
      const input: CreateUserInput = {
        name: 'Alice',
        email: 'alice@example.com',
        role: 'user' as UserRole
      };

      // Act
      const user: User = userService.createUser(input);

      // Assert
      expect(user).toHaveProperty('id');
      expect(user.name).toBe('Alice');
      expect(user.email).toBe('alice@example.com');
      expect(user.role).toBe('user');
    });

    it('should enforce email format', () => {
      const input: CreateUserInput = {
        name: 'Bob',
        email: 'invalid-email',  // Type: string, but invalid format
        role: 'user'
      };

      expect(() => userService.createUser(input))
        .toThrow('Invalid email format');
    });

    it('should validate user role', () => {
      const input = {
        name: 'Charlie',
        email: 'charlie@example.com',
        role: 'superadmin'  // Invalid role
      } as CreateUserInput;

      expect(() => userService.createUser(input))
        .toThrow('Invalid role');
    });
  });

  describe('findUser', () => {
    it('should return user when found', () => {
      // Arrange
      const created = userService.createUser({
        name: 'Alice',
        email: 'alice@example.com',
        role: 'user'
      });

      // Act
      const found: User | undefined = userService.findUser(created.id);

      // Assert
      expect(found).toBeDefined();
      expect(found!.id).toBe(created.id);
    });

    it('should return undefined when not found', () => {
      const result: User | undefined = userService.findUser(999);
      expect(result).toBeUndefined();
    });
  });
});
```

### Example 3: Generic Type Testing

```typescript
/**
 * Test module for generic Stack data structure.
 */

import { describe, it, expect } from '@jest/globals';
import { Stack } from './stack';

describe('Stack', () => {
  describe('with numbers', () => {
    it('should push and pop numbers', () => {
      // Arrange
      const stack = new Stack<number>();

      // Act
      stack.push(1);
      stack.push(2);
      stack.push(3);

      // Assert
      expect(stack.pop()).toBe(3);
      expect(stack.pop()).toBe(2);
      expect(stack.pop()).toBe(1);
    });

    it('should return undefined when empty', () => {
      const stack = new Stack<number>();
      expect(stack.pop()).toBeUndefined();
    });
  });

  describe('with custom types', () => {
    interface Task {
      id: number;
      title: string;
      completed: boolean;
    }

    it('should work with Task objects', () => {
      // Arrange
      const stack = new Stack<Task>();
      const task: Task = {
        id: 1,
        title: 'Write tests',
        completed: false
      };

      // Act
      stack.push(task);
      const result = stack.pop();

      // Assert
      expect(result).toEqual(task);
      expect(result?.title).toBe('Write tests');
    });
  });
});
```

### Example 4: Async Tests with Promise Types

```typescript
/**
 * Test module for async API client.
 */

import { describe, it, expect } from '@jest/globals';
import type { User } from './types';
import { ApiClient } from './apiClient';

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    apiClient = new ApiClient('https://api.example.com');
  });

  describe('fetchUser', () => {
    it('should fetch user data', async () => {
      // Arrange
      const userId = 123;

      // Act
      const user: User = await apiClient.fetchUser(userId);

      // Assert
      expect(user).toHaveProperty('id', userId);
      expect(user).toHaveProperty('name');
      expect(user).toHaveProperty('email');
    });

    it('should handle 404 errors', async () => {
      // Arrange
      const invalidId = 999;

      // Act & Assert
      await expect(apiClient.fetchUser(invalidId))
        .rejects
        .toThrow('User not found');
    });

    it('should return proper type', async () => {
      const user = await apiClient.fetchUser(1);

      // TypeScript ensures these properties exist
      expect(typeof user.id).toBe('number');
      expect(typeof user.name).toBe('string');
      expect(typeof user.email).toBe('string');
    });
  });

  describe('updateUser', () => {
    it('should update user with partial data', async () => {
      // Arrange
      const userId = 1;
      const updates: Partial<User> = {
        name: 'Alice Updated'
      };

      // Act
      const updated: User = await apiClient.updateUser(userId, updates);

      // Assert
      expect(updated.name).toBe('Alice Updated');
      expect(updated).toHaveProperty('id');
      expect(updated).toHaveProperty('email');
    });
  });
});
```

### Example 5: Mocking with TypeScript Types

```typescript
/**
 * Test module for UserService with mocked dependencies.
 */

import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import type { User } from './types';
import { UserService } from './userService';
import type { ApiClient } from './apiClient';

describe('UserService with mocks', () => {
  let userService: UserService;
  let mockApiClient: jest.Mocked<ApiClient>;

  beforeEach(() => {
    // Arrange - Create typed mock
    mockApiClient = {
      fetchUser: jest.fn<(id: number) => Promise<User>>(),
      updateUser: jest.fn<(id: number, data: Partial<User>) => Promise<User>>(),
      deleteUser: jest.fn<(id: number) => Promise<void>>()
    } as jest.Mocked<ApiClient>;

    userService = new UserService(mockApiClient);
  });

  it('should fetch and process user data', async () => {
    // Arrange
    const mockUser: User = {
      id: 1,
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    };
    mockApiClient.fetchUser.mockResolvedValue(mockUser);

    // Act
    const result = await userService.processUser(1);

    // Assert
    expect(mockApiClient.fetchUser).toHaveBeenCalledWith(1);
    expect(result.displayName).toBe('Alice (user)');
  });

  it('should handle API errors', async () => {
    // Arrange
    mockApiClient.fetchUser.mockRejectedValue(
      new Error('Network error')
    );

    // Act & Assert
    await expect(userService.processUser(1))
      .rejects
      .toThrow('Network error');
  });

  it('should call updateUser with correct types', async () => {
    // Arrange
    const updates: Partial<User> = { name: 'Bob' };
    mockApiClient.updateUser.mockResolvedValue({
      id: 1,
      name: 'Bob',
      email: 'bob@example.com',
      role: 'user'
    });

    // Act
    await userService.updateUserName(1, 'Bob');

    // Assert
    expect(mockApiClient.updateUser).toHaveBeenCalledWith(1, updates);
  });
});
```

### Example 6: Union Types and Type Guards

```typescript
/**
 * Test module for Result type (success/error union).
 */

import { describe, it, expect } from '@jest/globals';
import type { Result, Success, Failure } from './result';
import { calculate, isSuccess, isFailure } from './calculator';

describe('Result type handling', () => {
  describe('calculate', () => {
    it('should return Success for valid operation', () => {
      // Arrange
      const dividend = 10;
      const divisor = 2;

      // Act
      const result: Result<number> = calculate(dividend, divisor, 'divide');

      // Assert - Type guard
      expect(isSuccess(result)).toBe(true);
      if (isSuccess(result)) {
        expect(result.value).toBe(5);
      }
    });

    it('should return Failure for invalid operation', () => {
      // Arrange
      const dividend = 10;
      const divisor = 0;

      // Act
      const result: Result<number> = calculate(dividend, divisor, 'divide');

      // Assert - Type guard
      expect(isFailure(result)).toBe(true);
      if (isFailure(result)) {
        expect(result.error).toContain('division by zero');
      }
    });

    it('should narrow types with type guards', () => {
      // Arrange
      const dividend = 10;
      const divisor = 2;

      // Act
      const result = calculate(dividend, divisor, 'divide');

      // Assert - TypeScript narrows type based on guard
      expect(result.success).toBe(true);
      if (result.success) {
        const value: number = result.value;  // Type: number
        expect(value).toBe(5);
      }
    });
  });
});
```

## TypeScript-Specific Best Practices

1. **Import Types Explicitly**:
   ```typescript
   import type { User } from './types';  // Type-only import
   import { UserService } from './userService';  // Value import
   ```

2. **Annotate Setup Variables**:
   ```typescript
   let service: UserService;
   let mockClient: jest.Mocked<ApiClient>;
   ```

3. **Use Type Inference for Results**:
   ```typescript
   const result = service.calculate(1, 2);  // Let TypeScript infer
   ```

4. **Explicit Types for Complex Mocks**:
   ```typescript
   const mockFn = jest.fn<(id: number) => Promise<User>>();
   ```

5. **Strict Null Checks**:
   ```typescript
   const user = service.findUser(1);
   expect(user).toBeDefined();
   // Prefer optional chaining or explicit checks over non-null assertion
   expect(user?.name).toBe('Alice');
   ```

## TypeScript Matchers

```typescript
// Type-safe property checks
expect(user).toHaveProperty('id');
expect(user).toHaveProperty('name', 'Alice');

// Deep equality with types
const expected: User = { id: 1, name: 'Alice', email: 'alice@example.com', role: 'user' };
expect(user).toEqual(expected);

// Type guards
expect(typeof result).toBe('number');
expect(result).toBeInstanceOf(Error);

// Array/Object matchers
expect(users).toHaveLength(3);
expect(users).toContain(user);
expect(user).toMatchObject({ name: 'Alice' });
```

## Configuration Notes

### jest.config.ts

```typescript
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts'
  ]
};
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["jest", "node"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Common Patterns

### Pattern: Testing with Strict Mode
```typescript
// strictNullChecks affects how you handle optional values
const user: User | undefined = service.findUser(1);

// Preferred: Check before accessing
if (user !== undefined) {
  expect(user.name).toBe('Alice');
}

// Alternative: Use optional chaining (safer than non-null assertion)
expect(user?.name).toBe('Alice');

// Avoid: Non-null assertion (use only when absolutely certain)
// expect(user!.name).toBe('Alice');  // Not recommended - can hide bugs
```

### Pattern: Testing Enums
```typescript
enum Status {
  Pending = 'PENDING',
  Active = 'ACTIVE',
  Completed = 'COMPLETED'
}

it('should set correct status', () => {
  const task = service.createTask('Test');
  expect(task.status).toBe(Status.Pending);
});
```

### Pattern: Testing with Generics
```typescript
function identity<T>(value: T): T {
  return value;
}

it('should preserve type with generics', () => {
  const num = identity(42);
  const str = identity('hello');

  expect(num).toBe(42);
  expect(str).toBe('hello');

  // TypeScript infers correct types
  expect(typeof num).toBe('number');
  expect(typeof str).toBe('string');
});
```

## References

- Jest Documentation: https://jestjs.io/docs/getting-started
- ts-jest Documentation: https://kulshekhar.github.io/ts-jest/
- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/
- Jest Matchers: https://jestjs.io/docs/expect
- Jest Mock Functions: https://jestjs.io/docs/mock-functions
- TypeScript Patterns: `skills/test-generation/typescript-patterns.md`
- JavaScript Jest Template: `skills/templates/javascript-jest-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
