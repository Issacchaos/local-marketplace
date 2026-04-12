# JavaScript Test Generation Patterns

**Version**: 1.0.0
**Language**: JavaScript
**Frameworks**: Jest, Vitest, Mocha
**Purpose**: Testing patterns and best practices for JavaScript test generation

## Overview

JavaScript test generation patterns for creating comprehensive, maintainable test suites. This skill covers Jest, Vitest, and Mocha frameworks with focus on describe/it/expect patterns, async testing, and mocking strategies specific to JavaScript.

## Supported Frameworks

### Jest
- **Description**: Delightful testing framework with built-in mocking and assertions
- **Assertions**: `expect()` with matchers (toBe, toEqual, toMatchObject, etc.)
- **Mocking**: `jest.mock()`, `jest.fn()`, `jest.spyOn()`
- **Async**: Supports promises and async/await natively

### Vitest
- **Description**: Fast Vite-native test framework, Jest-compatible API
- **Assertions**: `expect()` with Jest-compatible matchers
- **Mocking**: `vi.mock()`, `vi.fn()`, `vi.spyOn()` (similar to Jest)
- **Async**: Native async/await support, fast execution

### Mocha
- **Description**: Flexible test framework, no built-in assertions/mocking
- **Assertions**: External library required (Chai, expect.js, Node.js assert)
- **Mocking**: External library required (Sinon, proxyquire)
- **Async**: Supports callbacks, promises, and async/await

## JavaScript Testing Fundamentals

### Framework Selection Guidance

**Use Jest when**:
- Starting new project (most popular, best ecosystem)
- Need zero-configuration setup
- Want built-in mocking and coverage
- React/Vue/Angular projects

**Use Vitest when**:
- Using Vite for build tooling
- Need faster test execution
- Want Jest compatibility with better performance
- Modern ESM-first project

**Use Mocha when**:
- Need maximum flexibility
- Want to choose assertion/mocking libraries
- Legacy projects already using Mocha
- Custom test runner requirements

### File Organization

```
project/
├── src/
│   ├── calculator.js
│   ├── api/
│   │   └── client.js
│   └── utils/
│       └── format.js
└── tests/              # or __tests__/
    ├── calculator.test.js
    ├── api/
    │   └── client.test.js
    └── utils/
        └── format.test.js
```

**Naming Conventions**:
- Test files: `*.test.js` or `*.spec.js`
- Test directories: `tests/`, `__tests__/`, or `test/`
- Mirror source structure for easy navigation

### Test Structure: Describe/It Pattern

All three frameworks use describe/it (or describe/test) pattern:

```javascript
describe('Module or Class name', () => {
  describe('functionName', () => {
    it('should do something specific', () => {
      // Arrange
      const input = 5;

      // Act
      const result = functionName(input);

      // Assert
      expect(result).toBe(10);
    });

    it('should handle edge case', () => {
      // Test implementation
    });
  });
});
```

**Naming Guidelines**:
- **describe**: Name the unit being tested (function, class, module)
- **it**: Describe expected behavior in plain English
- Start with "should" for clarity: "should return sum", "should throw error"

## AAA Pattern (Arrange-Act-Assert)

### Standard AAA Pattern

```javascript
describe('add', () => {
  it('should add two positive numbers', () => {
    // Arrange - Set up test data and dependencies
    const a = 5;
    const b = 3;

    // Act - Execute the function under test
    const result = add(a, b);

    // Assert - Verify the result
    expect(result).toBe(8);
  });
});
```

### AAA with Setup

```javascript
describe('Calculator', () => {
  let calculator;

  beforeEach(() => {
    // Arrange - Create fresh instance for each test
    calculator = new Calculator();
  });

  it('should add numbers', () => {
    // Act
    const result = calculator.add(5, 3);

    // Assert
    expect(result).toBe(8);
  });

  it('should multiply numbers', () => {
    // Act
    const result = calculator.multiply(4, 3);

    // Assert
    expect(result).toBe(12);
  });
});
```

### AAA with Complex Setup

```javascript
describe('UserService', () => {
  let userService;
  let mockDatabase;

  beforeEach(() => {
    // Arrange - Set up mocks and dependencies
    mockDatabase = {
      findUser: jest.fn(),
      saveUser: jest.fn()
    };

    userService = new UserService(mockDatabase);
  });

  it('should fetch user by id', async () => {
    // Arrange
    const userId = 123;
    const mockUser = { id: 123, name: 'Alice' };
    mockDatabase.findUser.mockResolvedValue(mockUser);

    // Act
    const user = await userService.getUserById(userId);

    // Assert
    expect(user).toEqual(mockUser);
    expect(mockDatabase.findUser).toHaveBeenCalledWith(userId);
  });
});
```

## Test Scenarios

### 1. Happy Path Tests

Test the main successful use case:

```javascript
describe('divide', () => {
  it('should divide two numbers', () => {
    const result = divide(10, 2);
    expect(result).toBe(5);
  });

  it('should handle decimal results', () => {
    const result = divide(7, 2);
    expect(result).toBe(3.5);
  });
});
```

### 2. Edge Cases

Test boundary conditions and special values:

```javascript
describe('divide', () => {
  it('should handle zero dividend', () => {
    const result = divide(0, 5);
    expect(result).toBe(0);
  });

  it('should handle negative numbers', () => {
    const result = divide(-10, 2);
    expect(result).toBe(-5);
  });

  it('should handle very large numbers', () => {
    const result = divide(Number.MAX_SAFE_INTEGER, 2);
    expect(result).toBeLessThan(Number.MAX_SAFE_INTEGER);
  });
});
```

### 3. Error Cases

Test exception handling:

```javascript
describe('divide', () => {
  it('should throw error when dividing by zero', () => {
    expect(() => divide(10, 0)).toThrow('Division by zero');
  });

  it('should throw error for non-numeric inputs', () => {
    expect(() => divide('10', 2)).toThrow('Invalid input');
    expect(() => divide(10, '2')).toThrow('Invalid input');
  });
});
```

### 4. Boundary Tests

Test min/max values and limits:

```javascript
describe('clamp', () => {
  it('should clamp value below minimum', () => {
    const result = clamp(5, 10, 100);
    expect(result).toBe(10);
  });

  it('should clamp value above maximum', () => {
    const result = clamp(150, 10, 100);
    expect(result).toBe(100);
  });

  it('should not clamp value within range', () => {
    const result = clamp(50, 10, 100);
    expect(result).toBe(50);
  });
});
```

## Assertion Patterns

### Jest/Vitest Assertions

```javascript
// Equality
expect(value).toBe(5);                    // Strict equality (===)
expect(value).toEqual({ a: 1, b: 2 });    // Deep equality

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Numbers
expect(value).toBeGreaterThan(5);
expect(value).toBeGreaterThanOrEqual(5);
expect(value).toBeLessThan(10);
expect(value).toBeCloseTo(0.3, 5);        // Floating point

// Strings
expect(string).toMatch(/pattern/);
expect(string).toContain('substring');

// Arrays/Iterables
expect(array).toContain('item');
expect(array).toHaveLength(3);
expect(array).toEqual(expect.arrayContaining([1, 2]));

// Objects
expect(obj).toHaveProperty('key');
expect(obj).toHaveProperty('key', 'value');
expect(obj).toMatchObject({ a: 1 });

// Exceptions
expect(() => fn()).toThrow();
expect(() => fn()).toThrow(Error);
expect(() => fn()).toThrow('error message');

// Promises (async)
await expect(promise).resolves.toBe(value);
await expect(promise).rejects.toThrow();

// Functions
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);
```

### Mocha + Chai Assertions

```javascript
const { expect } = require('chai');

// Equality
expect(value).to.equal(5);                // Strict equality
expect(value).to.deep.equal({ a: 1 });    // Deep equality

// Truthiness
expect(value).to.be.true;
expect(value).to.be.false;
expect(value).to.be.null;
expect(value).to.be.undefined;
expect(value).to.exist;

// Numbers
expect(value).to.be.above(5);
expect(value).to.be.at.least(5);
expect(value).to.be.below(10);
expect(value).to.be.closeTo(0.3, 0.01);

// Strings
expect(string).to.match(/pattern/);
expect(string).to.include('substring');

// Arrays
expect(array).to.include('item');
expect(array).to.have.lengthOf(3);
expect(array).to.have.members([1, 2, 3]);

// Objects
expect(obj).to.have.property('key');
expect(obj).to.have.property('key', 'value');
expect(obj).to.include({ a: 1 });

// Exceptions
expect(() => fn()).to.throw();
expect(() => fn()).to.throw(Error);
expect(() => fn()).to.throw('error message');

// Promises
return expect(promise).to.eventually.equal(value);
return expect(promise).to.be.rejected;
```

## Mocking Strategies

### Jest Mocking

#### Module Mocks

```javascript
// Mock entire module
jest.mock('./api/client');

describe('UserService', () => {
  it('should fetch user data', async () => {
    const mockGetUser = jest.fn().mockResolvedValue({ id: 1, name: 'Alice' });
    require('./api/client').getUser = mockGetUser;

    const user = await userService.fetchUser(1);

    expect(mockGetUser).toHaveBeenCalledWith(1);
    expect(user.name).toBe('Alice');
  });
});
```

#### Function Mocks

```javascript
// Create mock function
const mockFn = jest.fn();

// With return value
const mockFn = jest.fn(() => 42);
const mockFn = jest.fn().mockReturnValue(42);

// With resolved promise
const mockFn = jest.fn().mockResolvedValue({ data: 'value' });

// With rejected promise
const mockFn = jest.fn().mockRejectedValue(new Error('Failed'));

// One-time values
mockFn
  .mockReturnValueOnce(1)
  .mockReturnValueOnce(2)
  .mockReturnValue(3);
```

#### Spy on Methods

```javascript
describe('Calculator', () => {
  it('should call add method', () => {
    const calculator = new Calculator();
    const addSpy = jest.spyOn(calculator, 'add');

    calculator.calculate('+', 5, 3);

    expect(addSpy).toHaveBeenCalledWith(5, 3);

    addSpy.mockRestore();  // Clean up
  });
});
```

### Vitest Mocking

Very similar to Jest, use `vi` instead of `jest`:

```javascript
import { vi } from 'vitest';

// Mock module
vi.mock('./api/client');

// Mock function
const mockFn = vi.fn();
const mockFn = vi.fn(() => 42);
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'value' });

// Spy
const spy = vi.spyOn(obj, 'method');
```

### Mocha + Sinon Mocking

```javascript
const sinon = require('sinon');

describe('UserService', () => {
  let sandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });

  afterEach(() => {
    sandbox.restore();  // Restore all mocks
  });

  it('should fetch user data', async () => {
    // Stub method
    const stub = sandbox.stub(apiClient, 'getUser');
    stub.resolves({ id: 1, name: 'Alice' });

    const user = await userService.fetchUser(1);

    sinon.assert.calledWith(stub, 1);
    expect(user.name).to.equal('Alice');
  });

  it('should track method calls', () => {
    // Spy on method
    const spy = sandbox.spy(calculator, 'add');

    calculator.calculate('+', 5, 3);

    sinon.assert.calledOnce(spy);
    sinon.assert.calledWith(spy, 5, 3);
  });
});
```

## Setup and Teardown

### beforeEach / afterEach

Run before/after each test:

```javascript
describe('Database tests', () => {
  let db;

  beforeEach(() => {
    // Runs before each it()
    db = new Database();
    db.connect();
  });

  afterEach(() => {
    // Runs after each it()
    db.disconnect();
  });

  it('should insert record', () => {
    db.insert({ id: 1, name: 'Alice' });
    expect(db.count()).toBe(1);
  });

  it('should delete record', () => {
    db.insert({ id: 1, name: 'Alice' });
    db.delete(1);
    expect(db.count()).toBe(0);
  });
});
```

### beforeAll / afterAll

Run once before/after all tests in suite:

```javascript
describe('API tests', () => {
  let server;

  beforeAll(() => {
    // Runs once before all tests
    server = startServer();
  });

  afterAll(() => {
    // Runs once after all tests
    server.close();
  });

  it('should respond to GET request', async () => {
    const response = await fetch('http://localhost:3000/api');
    expect(response.status).toBe(200);
  });
});
```

## Test Organization

### Nested Describe Blocks

```javascript
describe('Calculator', () => {
  describe('add', () => {
    it('should add positive numbers', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('should add negative numbers', () => {
      expect(add(-2, -3)).toBe(-5);
    });
  });

  describe('subtract', () => {
    it('should subtract numbers', () => {
      expect(subtract(5, 3)).toBe(2);
    });
  });
});
```

### Test Organization Best Practices

1. **Group related tests**: Use describe blocks for logical grouping
2. **One assertion per test**: Prefer focused tests
3. **Descriptive names**: Test names should explain what's being tested
4. **Arrange-Act-Assert**: Follow AAA pattern consistently
5. **Independent tests**: Each test should run independently
6. **Fast tests**: Avoid slow operations, use mocks

## Anti-Patterns to Avoid

### ❌ Multiple unrelated assertions

```javascript
// BAD
it('should work correctly', () => {
  expect(add(2, 3)).toBe(5);
  expect(subtract(5, 3)).toBe(2);  // Different function!
  expect(multiply(2, 3)).toBe(6);  // Different function!
});

// GOOD
describe('math functions', () => {
  it('should add numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  it('should subtract numbers', () => {
    expect(subtract(5, 3)).toBe(2);
  });
});
```

### ❌ Testing implementation details

```javascript
// BAD - Tests internal state
it('should call private method', () => {
  const spy = jest.spyOn(obj, '_privateMethod');
  obj.publicMethod();
  expect(spy).toHaveBeenCalled();
});

// GOOD - Tests public behavior
it('should return correct result', () => {
  const result = obj.publicMethod();
  expect(result).toBe(expectedValue);
});
```

### ❌ Shared state between tests

```javascript
// BAD
let counter = 0;

it('should increment', () => {
  counter++;
  expect(counter).toBe(1);  // Depends on test order!
});

it('should increment again', () => {
  counter++;
  expect(counter).toBe(2);  // Fragile!
});

// GOOD
describe('counter', () => {
  let counter;

  beforeEach(() => {
    counter = 0;  // Fresh state
  });

  it('should increment', () => {
    counter++;
    expect(counter).toBe(1);
  });
});
```

## Quality Checklist

Before considering tests complete:
- [ ] All happy path scenarios covered
- [ ] Edge cases tested (null, undefined, empty, max/min)
- [ ] Error cases tested (exceptions, validation errors)
- [ ] Async operations properly awaited
- [ ] Mocks cleaned up (afterEach restore)
- [ ] Test names are descriptive
- [ ] AAA pattern followed
- [ ] Tests run independently (no shared state)
- [ ] Fast execution (<50ms per test ideally)

## References

- Jest Documentation: https://jestjs.io/docs/getting-started
- Vitest Documentation: https://vitest.dev/guide/
- Mocha Documentation: https://mochajs.org/
- Chai Assertions: https://www.chaijs.com/api/bdd/
- Sinon Mocking: https://sinonjs.org/
- Python patterns (reference): `skills/test-generation/python-patterns.md`
- Unit test patterns: `skills/test-generation/unit-test-patterns.md`
- Mocking strategies: `skills/test-generation/mocking-strategies.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
