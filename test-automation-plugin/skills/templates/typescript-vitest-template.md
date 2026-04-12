# TypeScript Vitest Test Template

**Purpose**: Template for generating Vitest test files with TypeScript type annotations
**Target Language**: TypeScript
**Test Framework**: Vitest (native TypeScript support)
**Version Support**: Vitest 0.30.0+, TypeScript 4.0+

## Template Structure

```typescript
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
- Native TypeScript support (no ts-jest transformer needed)
- Otherwise Jest-compatible API with type annotations

## Example: Basic Tests

```typescript
import { describe, it, expect } from 'vitest';
import { add, subtract } from './calculator';

describe('Calculator', () => {
  it('should add two numbers', () => {
    // Arrange
    const a = 5;
    const b = 3;

    // Act
    const result = add(a, b);

    // Assert
    expect(result).toBe(8);
  });

  it('should subtract numbers', () => {
    // Arrange
    const a = 10;
    const b = 3;

    // Act
    const result = subtract(a, b);

    // Assert
    expect(result).toBe(7);
  });
});
```

## Example: With TypeScript Types

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import type { User, CreateUserInput } from './types';
import { UserService } from './userService';

describe('UserService', () => {
  let userService: UserService;

  beforeEach(() => {
    // Arrange - Setup service for each test
    userService = new UserService();
  });

  it('should create user with correct type', () => {
    // Arrange
    const input: CreateUserInput = {
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    };

    // Act
    const user: User = userService.createUser(input);

    // Assert
    expect(user).toHaveProperty('id');
    expect(user.name).toBe('Alice');
    expect(user.role).toBe('user');
  });
});
```

## Example: Async Tests with Types

```typescript
import { describe, it, expect } from 'vitest';
import type { User } from './types';
import { ApiClient } from './apiClient';

describe('ApiClient', () => {
  it('should fetch user data', async () => {
    // Arrange
    const apiClient = new ApiClient();
    const userId = 123;

    // Act
    const user: User = await apiClient.fetchUser(userId);

    // Assert
    expect(user).toHaveProperty('id', userId);
    expect(user).toHaveProperty('name');
  });

  it('should handle errors', async () => {
    // Arrange
    const apiClient = new ApiClient();
    const invalidUserId = 999;

    // Act & Assert
    await expect(apiClient.fetchUser(invalidUserId))
      .rejects
      .toThrow('User not found');
  });
});
```

## Mocking with Vitest and TypeScript

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { User } from './types';
import type { ApiClient } from './apiClient';
import { UserService } from './userService';

describe('UserService with mocks', () => {
  let userService: UserService;
  let mockApiClient: ApiClient;

  beforeEach(() => {
    // Create typed mock
    mockApiClient = {
      fetchUser: vi.fn<[number], Promise<User>>(),
      updateUser: vi.fn<[number, Partial<User>], Promise<User>>(),
      deleteUser: vi.fn<[number], Promise<void>>()
    } as ApiClient;

    userService = new UserService(mockApiClient);
  });

  it('should fetch and process user', async () => {
    // Arrange
    const mockUser: User = {
      id: 1,
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    };

    // Type-safe mock without 'as any'
    vi.mocked(mockApiClient.fetchUser).mockResolvedValue(mockUser);

    // Act
    const result = await userService.processUser(1);

    // Assert
    expect(mockApiClient.fetchUser).toHaveBeenCalledWith(1);
    expect(result.displayName).toBe('Alice (user)');
  });

  it('should handle API errors', async () => {
    // Arrange
    const error = new Error('Network error');
    // Type-safe mock without 'as any'
    vi.mocked(mockApiClient.fetchUser).mockRejectedValue(error);

    // Act & Assert
    await expect(userService.processUser(1))
      .rejects
      .toThrow('Network error');
  });
});
```

## Generic Types

```typescript
import { describe, it, expect } from 'vitest';
import { Stack } from './stack';

describe('Stack', () => {
  it('should work with numbers', () => {
    // Arrange
    const stack = new Stack<number>();

    // Act
    stack.push(1);
    stack.push(2);

    // Assert
    expect(stack.pop()).toBe(2);
    expect(stack.pop()).toBe(1);
  });

  it('should work with custom types', () => {
    // Arrange
    interface Task {
      id: number;
      title: string;
    }

    const stack = new Stack<Task>();
    const task: Task = { id: 1, title: 'Test' };

    // Act
    stack.push(task);

    // Assert
    expect(stack.pop()).toEqual(task);
  });
});
```

## Type Guards and Union Types

```typescript
import { describe, it, expect } from 'vitest';
import type { Result } from './result';
import { calculate, isSuccess } from './calculator';

describe('Result type', () => {
  it('should return success result', () => {
    // Arrange
    const dividend = 10;
    const divisor = 2;

    // Act
    const result: Result<number> = calculate(dividend, divisor, 'divide');

    // Assert - Type guard with proper assertions
    expect(isSuccess(result)).toBe(true);
    if (isSuccess(result)) {
      expect(result.value).toBe(5);
    }
  });

  it('should return error result', () => {
    // Arrange
    const dividend = 10;
    const divisor = 0;

    // Act
    const result: Result<number> = calculate(dividend, divisor, 'divide');

    // Assert - Type guard with proper assertions
    expect(isSuccess(result)).toBe(false);
    if (!isSuccess(result)) {
      expect(result.error).toContain('division by zero');
    }
  });
});
```

## Setup/Teardown with Types

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { Database } from './database';
import type { Connection } from './types';

describe('Database', () => {
  let db: Database;
  let connection: Connection;

  beforeEach(async () => {
    // Arrange - Setup database connection
    db = new Database();
    connection = await db.connect();
  });

  afterEach(async () => {
    // Cleanup - Close connection
    await connection.close();
  });

  it('should insert record', async () => {
    // Arrange
    interface Record {
      id: number;
      name: string;
    }

    const record: Record = { id: 1, name: 'Alice' };

    // Act
    await db.insert(record);

    // Assert
    const count = await db.count();
    expect(count).toBe(1);
  });
});
```

## Configuration

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['**/*.test.ts', '**/*.spec.ts']
    }
  }
});
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "lib": ["ESNext"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "types": ["vitest/globals"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Advantages of Vitest with TypeScript

1. **Native TypeScript Support**: No transformer (ts-jest) needed
2. **Faster**: Vite's fast compilation
3. **ESM First**: Modern module system
4. **HMR**: Hot module replacement for tests
5. **Jest Compatible**: Easy migration from Jest

## Type Inference

Vitest works seamlessly with TypeScript's type inference:

```typescript
describe('Type inference', () => {
  it('should infer types automatically', () => {
    // TypeScript infers types from function signatures
    const user = createUser('Alice', 'alice@example.com');

    expect(user.name).toBe('Alice');
    // TypeScript knows user.name is string
  });

  it('should infer generic types', () => {
    const numbers = [1, 2, 3, 4, 5];
    const first = numbers[0];

    expect(first).toBe(1);
    // TypeScript knows first is number
  });
});
```

## Mock Typing Patterns

```typescript
import { vi } from 'vitest';

// Simple mock function
const mockFn = vi.fn<[string], number>();
mockFn.mockReturnValue(42);

// Mock with types
interface ApiResponse {
  data: string;
  status: number;
}

const mockApi = vi.fn<[], Promise<ApiResponse>>();
mockApi.mockResolvedValue({ data: 'success', status: 200 });

// Spy with types
const obj = {
  method: (x: number): string => x.toString()
};

const spy = vi.spyOn(obj, 'method');
expect(spy).toHaveBeenCalled();
```

## Best Practices

1. **Use Type Imports**: `import type { User } from './types'`
2. **Let TypeScript Infer**: Don't over-annotate
3. **Explicit Mock Types**: Type your mocks for safety
4. **Strict Mode**: Enable `strict: true` in tsconfig
5. **Native ESM**: Use ES modules, not CommonJS
6. **Test Types**: Ensure types work as expected

## Comparison with Jest

| Feature | Jest + ts-jest | Vitest |
|---------|---------------|--------|
| TypeScript | Via transformer | Native |
| Speed | Slower | Faster |
| Module System | CommonJS default | ESM default |
| Import syntax | `@jest/globals` | `vitest` |
| Mocking | `jest.*` | `vi.*` |
| API | Jest API | Jest-compatible |

## Migration from Jest

1. Replace imports: `@jest/globals` → `vitest`
2. Replace mocking: `jest.*` → `vi.*`
3. Update config: `jest.config.*` → `vitest.config.ts`
4. Remove ts-jest (no longer needed)
5. Test everything!

## References

- Vitest Documentation: https://vitest.dev/
- Vitest TypeScript Guide: https://vitest.dev/guide/features.html#typescript
- TypeScript Patterns: `skills/test-generation/typescript-patterns.md`
- JavaScript Vitest Template: `skills/templates/javascript-vitest-template.md`
- TypeScript Jest Template: `skills/templates/typescript-jest-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
