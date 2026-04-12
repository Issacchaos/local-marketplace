# TypeScript Test Generation Patterns

**Version**: 1.0.0
**Language**: TypeScript
**Frameworks**: Jest, Vitest
**Purpose**: TypeScript-specific testing patterns with type annotations

## Overview

TypeScript test generation patterns that extend JavaScript patterns with type safety, type annotations, and TypeScript-specific features. This skill covers type inference, generic types, interface testing, and mocking with TypeScript types.

## TypeScript Testing Fundamentals

### Why TypeScript in Tests?

**Benefits**:
- **Type Safety**: Catch errors at compile time, not runtime
- **IntelliSense**: Better IDE autocomplete and documentation
- **Refactoring**: Safe renames and structural changes
- **Documentation**: Types serve as inline documentation

**Trade-offs**:
- More verbose (type annotations)
- Compilation step required
- Learning curve for TypeScript syntax

### Type Annotation Strategy

**Golden Rule**: Annotate enough for clarity, let TypeScript infer the rest.

```typescript
// ✅ GOOD - Let TypeScript infer simple types
it('should add two numbers', () => {
  const result = add(2, 3);  // TypeScript infers result: number
  expect(result).toBe(5);
});

// ❌ OVER-ANNOTATED - Unnecessary noise
it('should add two numbers', () => {
  const a: number = 2;
  const b: number = 3;
  const result: number = add(a, b);
  expect(result).toBe(5);
});

// ✅ GOOD - Annotate when inference needs help
it('should handle user data', () => {
  const user: User = {  // Explicit type prevents mistakes
    id: 1,
    name: 'Alice',
    email: 'alice@example.com'
  };
  expect(validateUser(user)).toBe(true);
});
```

## Test Structure with TypeScript

### Basic Typed Test

```typescript
import { describe, it, expect } from '@jest/globals';
import { Calculator } from './calculator';

describe('Calculator', () => {
  it('should add two numbers', () => {
    // Arrange
    const calculator = new Calculator();

    // Act
    const result = calculator.add(5, 3);

    // Assert
    expect(result).toBe(8);
  });
});
```

### Testing with Interfaces

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

describe('UserService', () => {
  it('should create a valid user', () => {
    // Arrange
    const userData: Omit<User, 'id'> = {
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    };

    // Act
    const user: User = userService.createUser(userData);

    // Assert
    expect(user).toHaveProperty('id');
    expect(user.name).toBe('Alice');
    expect(user.role).toBe('user');
  });

  it('should validate user email format', () => {
    const invalidUser: User = {
      id: 1,
      name: 'Bob',
      email: 'invalid-email',  // TypeScript: string ✓, but invalid format
      role: 'user'
    };

    expect(() => userService.validateUser(invalidUser))
      .toThrow('Invalid email format');
  });
});
```

### Testing with Type Guards

```typescript
type Response<T> =
  | { success: true; data: T }
  | { success: false; error: string };

describe('API Client', () => {
  it('should return success response', async () => {
    // Act
    const response: Response<User> = await apiClient.getUser(1);

    // Assert - Type guard narrows type
    if (response.success) {
      expect(response.data.id).toBe(1);
      // TypeScript knows response.data is User here
    } else {
      fail('Expected success response');
    }
  });

  it('should return error response', async () => {
    const response: Response<User> = await apiClient.getUser(999);

    if (!response.success) {
      expect(response.error).toContain('not found');
      // TypeScript knows response.error exists here
    } else {
      fail('Expected error response');
    }
  });
});
```

## Generic Type Testing

### Testing Generic Functions

```typescript
// Source code
function first<T>(array: T[]): T | undefined {
  return array[0];
}

// Tests
describe('first', () => {
  it('should return first element of number array', () => {
    const numbers: number[] = [1, 2, 3];
    const result = first(numbers);  // TypeScript infers: number | undefined

    expect(result).toBe(1);
  });

  it('should return first element of string array', () => {
    const strings: string[] = ['a', 'b', 'c'];
    const result = first(strings);  // TypeScript infers: string | undefined

    expect(result).toBe('a');
  });

  it('should return undefined for empty array', () => {
    const empty: number[] = [];
    const result = first(empty);

    expect(result).toBeUndefined();
  });

  it('should work with custom types', () => {
    interface Product {
      id: number;
      name: string;
    }

    const products: Product[] = [
      { id: 1, name: 'Widget' },
      { id: 2, name: 'Gadget' }
    ];

    const result = first(products);  // TypeScript infers: Product | undefined

    expect(result?.name).toBe('Widget');
  });
});
```

### Testing Generic Classes

```typescript
class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }
}

describe('Stack', () => {
  it('should work with numbers', () => {
    // Arrange
    const stack = new Stack<number>();

    // Act
    stack.push(1);
    stack.push(2);
    const result = stack.pop();

    // Assert
    expect(result).toBe(2);
  });

  it('should work with custom types', () => {
    interface Task {
      id: number;
      title: string;
    }

    const stack = new Stack<Task>();
    const task: Task = { id: 1, title: 'Write tests' };

    stack.push(task);
    const result = stack.pop();

    expect(result).toEqual(task);
  });
});
```

## Mocking with TypeScript

### Jest Mock Typing

```typescript
import { jest } from '@jest/globals';

interface ApiClient {
  getUser(id: number): Promise<User>;
  updateUser(id: number, data: Partial<User>): Promise<User>;
}

describe('UserService with typed mocks', () => {
  it('should fetch user', async () => {
    // Arrange - Type-safe mock
    const mockApiClient: ApiClient = {
      getUser: jest.fn<(id: number) => Promise<User>>()
        .mockResolvedValue({
          id: 1,
          name: 'Alice',
          email: 'alice@example.com',
          role: 'user'
        }),
      updateUser: jest.fn()
    };

    const userService = new UserService(mockApiClient);

    // Act
    const user = await userService.fetchUser(1);

    // Assert
    expect(mockApiClient.getUser).toHaveBeenCalledWith(1);
    expect(user.name).toBe('Alice');
  });
});
```

### Vitest Mock Typing

```typescript
import { vi } from 'vitest';

describe('UserService with Vitest mocks', () => {
  it('should fetch user', async () => {
    // Arrange
    const mockGetUser = vi.fn<[number], Promise<User>>();
    mockGetUser.mockResolvedValue({
      id: 1,
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    });

    const mockApiClient: ApiClient = {
      getUser: mockGetUser,
      updateUser: vi.fn()
    };

    const userService = new UserService(mockApiClient);

    // Act
    const user = await userService.fetchUser(1);

    // Assert
    expect(mockGetUser).toHaveBeenCalledWith(1);
    expect(user.name).toBe('Alice');
  });
});
```

### Partial Mocking with Pick/Omit

```typescript
describe('UserService with partial mocks', () => {
  it('should only mock required methods', () => {
    // Arrange - Only mock what we need
    const mockApiClient: Pick<ApiClient, 'getUser'> = {
      getUser: jest.fn().mockResolvedValue({
        id: 1,
        name: 'Alice',
        email: 'alice@example.com',
        role: 'user'
      })
    };

    // Cast to full type when passing to service
    const userService = new UserService(mockApiClient as ApiClient);

    // Test only uses getUser, so this works
  });
});
```

## Async Function Types

### Promise Return Types

```typescript
describe('Async operations', () => {
  it('should fetch data', async () => {
    // Explicit Promise type when inference needs help
    const promise: Promise<User> = apiClient.getUser(1);
    const user = await promise;

    expect(user.id).toBe(1);
  });

  it('should handle errors', async () => {
    const promise: Promise<User> = apiClient.getUser(999);

    await expect(promise).rejects.toThrow('User not found');
  });
});
```

### Testing Callback Types

```typescript
type Callback<T> = (error: Error | null, result?: T) => void;

function fetchUser(id: number, callback: Callback<User>): void {
  // Implementation...
}

describe('Callback-based API', () => {
  it('should call callback with user', (done) => {
    // Arrange
    const callback: Callback<User> = (error, result) => {
      // Assert
      expect(error).toBeNull();
      expect(result?.id).toBe(1);
      done();
    };

    // Act
    fetchUser(1, callback);
  });
});
```

## Type Assertions in Tests

### Using Type Assertions

```typescript
describe('Type assertions', () => {
  it('should handle unknown types', () => {
    // Arrange - Data from external source
    const data: unknown = JSON.parse('{"id":1,"name":"Alice"}');

    // Assert type before using
    expect(typeof data).toBe('object');
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('name');

    // Now safe to assert type
    const user = data as User;
    expect(user.id).toBe(1);
  });

  it('should validate with type predicates', () => {
    function isUser(value: unknown): value is User {
      return (
        typeof value === 'object' &&
        value !== null &&
        'id' in value &&
        'name' in value &&
        'email' in value
      );
    }

    const data: unknown = { id: 1, name: 'Alice', email: 'alice@example.com' };

    if (isUser(data)) {
      // TypeScript knows data is User here
      expect(data.id).toBe(1);
    }
  });
});
```

## Strict Mode Considerations

### Strict Null Checks

```typescript
// With strictNullChecks enabled
describe('Strict null checks', () => {
  it('should handle potentially undefined values', () => {
    const user: User | undefined = findUser(1);

    // Must check for undefined
    expect(user).toBeDefined();

    // Now safe to access properties
    expect(user!.name).toBe('Alice');  // Non-null assertion

    // OR use optional chaining
    expect(user?.name).toBe('Alice');
  });

  it('should handle null values', () => {
    const result: string | null = processData();

    if (result === null) {
      fail('Expected non-null result');
    }

    // TypeScript narrows type to string
    expect(result.length).toBeGreaterThan(0);
  });
});
```

### Strict Function Types

```typescript
describe('Strict function types', () => {
  it('should type event handlers correctly', () => {
    type EventHandler = (event: Event) => void;

    const mockHandler: EventHandler = jest.fn();

    const button = new Button();
    button.onClick(mockHandler);

    button.click();

    expect(mockHandler).toHaveBeenCalled();
    // TypeScript ensures mockHandler receives Event type
  });
});
```

## Enum Testing

```typescript
enum Status {
  Pending = 'PENDING',
  Active = 'ACTIVE',
  Completed = 'COMPLETED'
}

describe('Status enum', () => {
  it('should handle enum values', () => {
    const task = {
      id: 1,
      title: 'Test',
      status: Status.Pending
    };

    expect(task.status).toBe(Status.Pending);
    expect(task.status).toBe('PENDING');
  });

  it('should validate enum values', () => {
    function isValidStatus(value: string): value is Status {
      return Object.values(Status).includes(value as Status);
    }

    expect(isValidStatus('PENDING')).toBe(true);
    expect(isValidStatus('INVALID')).toBe(false);
  });
});
```

## Union Type Testing

```typescript
type Result = number | Error;

describe('Union types', () => {
  it('should handle success case', () => {
    const result: Result = calculate(10, 2);

    // Type guard
    if (typeof result === 'number') {
      expect(result).toBe(5);
    } else {
      fail('Expected number result');
    }
  });

  it('should handle error case', () => {
    const result: Result = calculate(10, 0);

    if (result instanceof Error) {
      expect(result.message).toContain('division by zero');
    } else {
      fail('Expected Error result');
    }
  });
});
```

## Type Inference Patterns

### Let TypeScript Infer

```typescript
describe('Type inference', () => {
  it('should infer return types', () => {
    // No need to annotate - TypeScript infers User
    const user = createUser('Alice', 'alice@example.com');

    expect(user.name).toBe('Alice');
  });

  it('should infer array types', () => {
    // TypeScript infers number[]
    const numbers = [1, 2, 3, 4, 5];
    const sum = numbers.reduce((a, b) => a + b, 0);

    expect(sum).toBe(15);
  });

  it('should infer from function parameters', () => {
    function process<T>(items: T[]): T | undefined {
      return items[0];
    }

    // TypeScript infers process<string>
    const result = process(['a', 'b', 'c']);
    expect(result).toBe('a');
  });
});
```

## Fallback Strategy for Complex Types

When types are too complex or unknown:

```typescript
describe('Complex types fallback', () => {
  it('should use any as fallback with TODO', () => {
    // TODO: Add specific type once API contract is finalized
    const data: any = await fetchComplexData();

    expect(data).toHaveProperty('nested');
    expect(data.nested).toHaveProperty('value');
  });

  it('should use unknown for safer fallback', () => {
    const data: unknown = await fetchComplexData();

    // Must validate before using
    expect(typeof data).toBe('object');
    expect(data).not.toBeNull();

    // Then assert type
    const typed = data as ComplexType;
    expect(typed.value).toBeDefined();
  });
});
```

## Best Practices

1. **Minimal Type Annotations**: Let TypeScript infer when possible
2. **Explicit When Unclear**: Annotate when inference fails or for clarity
3. **Type Imports**: Import types alongside values
   ```typescript
   import { User, UserRole } from './types';
   ```
4. **Mock Interfaces**: Create mock implementations with proper typing
5. **Strict Mode**: Enable `strict: true` in tsconfig.json
6. **Avoid `any`**: Use `unknown` or specific types instead
7. **Type Guards**: Use type predicates for runtime validation
8. **Generic Tests**: Test generic functions with multiple types

## Common Pitfalls

### ❌ Over-annotation

```typescript
// BAD - Too much noise
const a: number = 5;
const b: number = 3;
const result: number = add(a, b);
expect(result).toBe(8);

// GOOD - Let TypeScript infer
const result = add(5, 3);
expect(result).toBe(8);
```

### ❌ Misusing `any`

```typescript
// BAD - Loses type safety
const user: any = { id: 1, name: 'Alice' };

// GOOD - Use proper type
const user: User = { id: 1, name: 'Alice', email: 'alice@example.com', role: 'user' };
```

### ❌ Ignoring Null/Undefined

```typescript
// BAD - Assumes always defined
const user = findUser(1);
expect(user.name).toBe('Alice');  // Error if undefined!

// GOOD - Check for undefined
const user = findUser(1);
expect(user).toBeDefined();
expect(user!.name).toBe('Alice');
```

## TypeScript-Specific Matchers

### Type-Safe Assertions

```typescript
describe('Type-safe assertions', () => {
  it('should use typed matchers', () => {
    const user: User = createUser();

    // Type-safe property access
    expect(user).toHaveProperty('id');
    expect(user).toHaveProperty('name', 'Alice');

    // Type-safe deep equality
    const expected: User = {
      id: 1,
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user'
    };
    expect(user).toEqual(expected);
  });
});
```

## Integration with JavaScript Patterns

TypeScript patterns **extend** JavaScript patterns with type safety:

```typescript
// All JavaScript patterns apply
// + Type annotations
// + Type inference
// + Type guards
// + Generic types
```

Refer to `skills/test-generation/javascript-patterns.md` for base patterns.

## Framework-Specific Notes

### Jest + TypeScript (ts-jest)

- Import from `@jest/globals` for types
- Use `jest.fn<Type>()` for typed mocks
- Configure `ts-jest` in jest.config.ts

### Vitest + TypeScript

- Import from `vitest` for types
- Use `vi.fn<Args, Return>()` for typed mocks
- Native TypeScript support (no transformer)

## Quick Reference

| Pattern | JavaScript | TypeScript |
|---------|-----------|-----------|
| Variable | `const x = 5` | `const x: number = 5` (when needed) |
| Function | `function add(a, b)` | `function add(a: number, b: number): number` |
| Mock | `jest.fn()` | `jest.fn<ReturnType, [ArgTypes]>()` |
| Interface | N/A | `interface User { ... }` |
| Generic | N/A | `function first<T>(arr: T[]): T` |
| Type Guard | N/A | `if (typeof x === 'number')` |
| Assert Type | N/A | `const user = data as User` |

## References

- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/
- TypeScript Deep Dive: https://basarat.gitbook.io/typescript/
- Jest TypeScript: https://jestjs.io/docs/getting-started#using-typescript
- Vitest TypeScript: https://vitest.dev/guide/features.html#typescript
- JavaScript Patterns: `skills/test-generation/javascript-patterns.md`
- Async Patterns: `skills/test-generation/async-test-patterns.md`
- TypeScript Templates: `skills/templates/typescript-*-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
