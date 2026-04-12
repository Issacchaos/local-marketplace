# Async Test Patterns for JavaScript

**Version**: 1.0.0
**Language**: JavaScript
**Frameworks**: Jest, Vitest, Mocha
**Purpose**: Patterns for testing asynchronous code (Promises, async/await, callbacks)

## Overview

Asynchronous testing is critical for JavaScript applications. This skill provides comprehensive patterns for testing async operations including Promises, async/await, and callbacks across Jest, Vitest, and Mocha frameworks.

## Async Patterns Hierarchy

**Preferred → Legacy**
1. **async/await** (Modern, Recommended) - Clearest syntax, best error handling
2. **Promises with .then()/.catch()** (Common) - Explicit Promise chains
3. **Callbacks** (Legacy) - Older pattern, avoid in new code

## Pattern 1: Async/Await (Recommended)

### Basic Async/Await Test

```javascript
// Jest/Vitest
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
});

// Mocha + Chai
const { expect } = require('chai');

describe('fetchUser', () => {
  it('should fetch user data', async () => {
    const userId = 123;
    const user = await fetchUser(userId);

    expect(user).to.have.property('id', userId);
    expect(user).to.have.property('name');
  });
});
```

### Async Error Handling

```javascript
// Jest/Vitest - Using rejects matcher
describe('fetchUser', () => {
  it('should throw error for invalid user', async () => {
    const invalidId = 999;

    await expect(fetchUser(invalidId)).rejects.toThrow('User not found');
  });

  it('should handle network errors', async () => {
    await expect(fetchUser(-1)).rejects.toThrow(NetworkError);
  });
});

// Mocha + Chai - Using try/catch
describe('fetchUser', () => {
  it('should throw error for invalid user', async () => {
    const invalidId = 999;

    try {
      await fetchUser(invalidId);
      expect.fail('Should have thrown error');
    } catch (error) {
      expect(error.message).to.equal('User not found');
    }
  });
});
```

### Multiple Async Operations

```javascript
describe('UserService', () => {
  it('should fetch and process multiple users', async () => {
    // Arrange
    const userIds = [1, 2, 3];

    // Act - Sequential
    const users = [];
    for (const id of userIds) {
      users.push(await fetchUser(id));
    }

    // Assert
    expect(users).toHaveLength(3);
    expect(users[0].id).toBe(1);
  });

  it('should fetch users in parallel', async () => {
    // Arrange
    const userIds = [1, 2, 3];

    // Act - Parallel
    const userPromises = userIds.map(id => fetchUser(id));
    const users = await Promise.all(userPromises);

    // Assert
    expect(users).toHaveLength(3);
    users.forEach((user, index) => {
      expect(user.id).toBe(userIds[index]);
    });
  });
});
```

## Pattern 2: Promise Chains

### Basic Promise Test

```javascript
// Jest/Vitest - Return promise
describe('fetchUser', () => {
  it('should fetch user data', () => {
    // Must return the promise!
    return fetchUser(123).then(user => {
      expect(user).toHaveProperty('id', 123);
      expect(user).toHaveProperty('name');
    });
  });
});

// Mocha + Chai - Return promise
describe('fetchUser', () => {
  it('should fetch user data', () => {
    return fetchUser(123).then(user => {
      expect(user).to.have.property('id', 123);
      expect(user).to.have.property('name');
    });
  });
});
```

### Promise Error Handling

```javascript
// Jest/Vitest
describe('fetchUser', () => {
  it('should handle errors', () => {
    return fetchUser(999)
      .then(() => {
        throw new Error('Should not succeed');
      })
      .catch(error => {
        expect(error.message).toBe('User not found');
      });
  });
});

// Mocha + Chai - Using chai-as-promised
const chai = require('chai');
const chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);
const { expect } = chai;

describe('fetchUser', () => {
  it('should handle errors', () => {
    return expect(fetchUser(999)).to.be.rejectedWith('User not found');
  });
});
```

### Chaining Multiple Promises

```javascript
describe('User workflow', () => {
  it('should fetch, update, and verify user', () => {
    let userId;

    return createUser({ name: 'Alice' })
      .then(user => {
        userId = user.id;
        expect(user.name).toBe('Alice');
        return updateUser(userId, { age: 30 });
      })
      .then(updatedUser => {
        expect(updatedUser.age).toBe(30);
        return fetchUser(userId);
      })
      .then(fetchedUser => {
        expect(fetchedUser.id).toBe(userId);
        expect(fetchedUser.age).toBe(30);
      });
  });
});
```

## Pattern 3: Callbacks (Legacy)

### Basic Callback Test

```javascript
// Jest/Vitest - Use done callback
describe('fetchUser', () => {
  it('should fetch user data', (done) => {
    fetchUser(123, (error, user) => {
      // Arrange/Act handled by callback

      // Assert
      expect(error).toBeNull();
      expect(user).toHaveProperty('id', 123);

      done();  // CRITICAL: Must call done() or test hangs!
    });
  });
});

// Mocha + Chai - Use done callback
describe('fetchUser', () => {
  it('should fetch user data', (done) => {
    fetchUser(123, (error, user) => {
      expect(error).to.be.null;
      expect(user).to.have.property('id', 123);

      done();
    });
  });
});
```

### Callback Error Handling

```javascript
describe('fetchUser', () => {
  it('should handle errors', (done) => {
    fetchUser(999, (error, user) => {
      expect(error).toBeTruthy();
      expect(error.message).toBe('User not found');
      expect(user).toBeUndefined();

      done();
    });
  });

  it('should handle errors with try/catch', (done) => {
    fetchUser(999, (error, user) => {
      try {
        expect(error).toBeTruthy();
        expect(error.message).toBe('User not found');
        done();
      } catch (assertionError) {
        done(assertionError);  // Pass assertion errors to done()
      }
    });
  });
});
```

## Setup and Teardown Patterns

### Async beforeEach/afterEach

```javascript
describe('Database tests', () => {
  let db;

  // Setup - async/await
  beforeEach(async () => {
    db = new Database();
    await db.connect();
    await db.seed();
  });

  // Teardown - async/await
  afterEach(async () => {
    await db.clear();
    await db.disconnect();
  });

  it('should insert user', async () => {
    const user = { name: 'Alice' };

    await db.insertUser(user);

    const count = await db.countUsers();
    expect(count).toBe(1);
  });

  it('should query users', async () => {
    await db.insertUser({ name: 'Alice' });
    await db.insertUser({ name: 'Bob' });

    const users = await db.queryUsers();

    expect(users).toHaveLength(2);
  });
});
```

### Async beforeAll/afterAll

```javascript
describe('API integration tests', () => {
  let server;
  let apiClient;

  beforeAll(async () => {
    // Start server once for all tests
    server = await startTestServer();
    apiClient = new ApiClient(server.url);

    // Wait for server to be ready
    await waitForServer(server, 5000);
  });

  afterAll(async () => {
    // Clean up server
    await server.close();
  });

  it('should fetch users', async () => {
    const users = await apiClient.getUsers();
    expect(users).toBeInstanceOf(Array);
  });

  it('should create user', async () => {
    const user = await apiClient.createUser({ name: 'Alice' });
    expect(user).toHaveProperty('id');
  });
});
```

## Timeout Handling

### Setting Test Timeouts

```javascript
// Jest/Vitest - Per test timeout
describe('Long running operations', () => {
  it('should complete within 10 seconds', async () => {
    const result = await longRunningOperation();
    expect(result).toBe('completed');
  }, 10000);  // 10 second timeout

  // Suite-level timeout
  describe('Slow operations', () => {
    jest.setTimeout(30000);  // 30 seconds for all tests

    it('should process large file', async () => {
      await processLargeFile('data.csv');
    });
  });
});

// Mocha - Per test timeout
describe('Long running operations', () => {
  it('should complete within 10 seconds', async function() {
    this.timeout(10000);  // Must use function() not arrow

    const result = await longRunningOperation();
    expect(result).to.equal('completed');
  });
});
```

### Custom Wait Utilities

```javascript
// Utility function
async function waitFor(condition, timeout = 5000, interval = 100) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Timeout waiting for condition after ${timeout}ms`);
}

// Usage in tests
describe('Async state changes', () => {
  it('should update status to complete', async () => {
    // Arrange
    const task = await createTask({ name: 'Process data' });

    // Act
    await task.start();

    // Assert - Wait for status change
    await waitFor(async () => {
      const updated = await fetchTask(task.id);
      return updated.status === 'complete';
    }, 5000);

    const finalTask = await fetchTask(task.id);
    expect(finalTask.status).toBe('complete');
  });
});
```

## Mocking Async Functions

### Jest/Vitest Async Mocks

```javascript
import { vi } from 'vitest';  // or jest for Jest

describe('UserService with mocks', () => {
  it('should handle successful API call', async () => {
    // Arrange
    const mockGetUser = vi.fn().mockResolvedValue({
      id: 1,
      name: 'Alice',
      age: 30
    });

    const userService = new UserService({ getUser: mockGetUser });

    // Act
    const user = await userService.fetchUser(1);

    // Assert
    expect(mockGetUser).toHaveBeenCalledWith(1);
    expect(user.name).toBe('Alice');
  });

  it('should handle API errors', async () => {
    // Arrange
    const mockGetUser = vi.fn().mockRejectedValue(
      new Error('Network error')
    );

    const userService = new UserService({ getUser: mockGetUser });

    // Act & Assert
    await expect(userService.fetchUser(1)).rejects.toThrow('Network error');
  });

  it('should handle different responses', async () => {
    // Arrange - Multiple calls with different responses
    const mockGetUser = vi.fn()
      .mockResolvedValueOnce({ id: 1, name: 'Alice' })
      .mockResolvedValueOnce({ id: 2, name: 'Bob' })
      .mockRejectedValueOnce(new Error('Not found'));

    // Act & Assert
    const user1 = await userService.fetchUser(1);
    expect(user1.name).toBe('Alice');

    const user2 = await userService.fetchUser(2);
    expect(user2.name).toBe('Bob');

    await expect(userService.fetchUser(3)).rejects.toThrow('Not found');
  });
});
```

### Mocha + Sinon Async Mocks

```javascript
const sinon = require('sinon');
const { expect } = require('chai');

describe('UserService with Sinon', () => {
  let sandbox;
  let userService;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('should handle successful API call', async () => {
    // Arrange
    const stub = sandbox.stub(apiClient, 'getUser');
    stub.resolves({ id: 1, name: 'Alice' });

    userService = new UserService(apiClient);

    // Act
    const user = await userService.fetchUser(1);

    // Assert
    sinon.assert.calledWith(stub, 1);
    expect(user.name).to.equal('Alice');
  });

  it('should handle API errors', async () => {
    // Arrange
    const stub = sandbox.stub(apiClient, 'getUser');
    stub.rejects(new Error('Network error'));

    userService = new UserService(apiClient);

    // Act & Assert
    try {
      await userService.fetchUser(1);
      expect.fail('Should have thrown');
    } catch (error) {
      expect(error.message).to.equal('Network error');
    }
  });
});
```

## Common Async Patterns

### Pattern: Retry Logic

```javascript
describe('Retry mechanism', () => {
  it('should retry failed requests', async () => {
    // Arrange
    const mockFetch = vi.fn()
      .mockRejectedValueOnce(new Error('Timeout'))
      .mockRejectedValueOnce(new Error('Timeout'))
      .mockResolvedValueOnce({ data: 'success' });

    // Act
    const result = await retryOperation(mockFetch, { maxAttempts: 3 });

    // Assert
    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(result.data).toBe('success');
  });

  it('should fail after max retries', async () => {
    // Arrange
    const mockFetch = vi.fn()
      .mockRejectedValue(new Error('Timeout'));

    // Act & Assert
    await expect(
      retryOperation(mockFetch, { maxAttempts: 3 })
    ).rejects.toThrow('Timeout');

    expect(mockFetch).toHaveBeenCalledTimes(3);
  });
});
```

### Pattern: Parallel Execution

```javascript
describe('Parallel operations', () => {
  it('should execute operations in parallel', async () => {
    // Arrange
    const operations = [
      fetchUser(1),
      fetchUser(2),
      fetchUser(3)
    ];

    const startTime = Date.now();

    // Act
    const results = await Promise.all(operations);

    const duration = Date.now() - startTime;

    // Assert
    expect(results).toHaveLength(3);
    expect(duration).toBeLessThan(500);  // Parallel should be fast
  });

  it('should handle partial failures with allSettled', async () => {
    // Arrange
    const operations = [
      fetchUser(1),
      fetchUser(999),  // Will fail
      fetchUser(2)
    ];

    // Act
    const results = await Promise.allSettled(operations);

    // Assert
    expect(results[0].status).toBe('fulfilled');
    expect(results[0].value.id).toBe(1);

    expect(results[1].status).toBe('rejected');
    expect(results[1].reason.message).toBe('User not found');

    expect(results[2].status).toBe('fulfilled');
    expect(results[2].value.id).toBe(2);
  });
});
```

### Pattern: Race Conditions

```javascript
describe('Race conditions', () => {
  it('should return first successful result', async () => {
    // Arrange
    const slowServer = delay(1000).then(() => ({ server: 'slow' }));
    const fastServer = delay(100).then(() => ({ server: 'fast' }));

    // Act
    const result = await Promise.race([slowServer, fastServer]);

    // Assert
    expect(result.server).toBe('fast');
  });

  it('should timeout slow operations', async () => {
    // Arrange
    const slowOperation = delay(5000).then(() => 'completed');
    const timeout = delay(1000).then(() => {
      throw new Error('Timeout');
    });

    // Act & Assert
    await expect(Promise.race([slowOperation, timeout]))
      .rejects.toThrow('Timeout');
  });
});
```

## Anti-Patterns to Avoid

### ❌ Forgetting to return/await

```javascript
// BAD - Promise not awaited
it('should fetch user', () => {
  fetchUser(123).then(user => {
    expect(user.id).toBe(123);  // May not run!
  });
  // Test completes before assertion runs
});

// GOOD - Return promise
it('should fetch user', () => {
  return fetchUser(123).then(user => {
    expect(user.id).toBe(123);
  });
});

// GOOD - Use async/await
it('should fetch user', async () => {
  const user = await fetchUser(123);
  expect(user.id).toBe(123);
});
```

### ❌ Mixing patterns

```javascript
// BAD - Mixed async/await and done
it('should fetch user', async (done) => {
  const user = await fetchUser(123);
  expect(user.id).toBe(123);
  done();  // Don't mix async/await with done
});

// GOOD - Use only async/await
it('should fetch user', async () => {
  const user = await fetchUser(123);
  expect(user.id).toBe(123);
});
```

### ❌ Not handling errors properly

```javascript
// BAD - Swallowing errors
it('should handle errors', async () => {
  try {
    await fetchUser(999);
  } catch (error) {
    // Empty catch block - error not verified!
  }
});

// GOOD - Verify error
it('should handle errors', async () => {
  await expect(fetchUser(999)).rejects.toThrow('User not found');
});
```

### ❌ Forgetting done() in callbacks

```javascript
// BAD - Test will timeout
it('should fetch user', (done) => {
  fetchUser(123, (error, user) => {
    expect(user.id).toBe(123);
    // Forgot done()!
  });
});

// GOOD - Call done()
it('should fetch user', (done) => {
  fetchUser(123, (error, user) => {
    expect(user.id).toBe(123);
    done();
  });
});
```

## Best Practices Summary

1. **Prefer async/await**: Clearest syntax and best error handling
2. **Always return/await**: Promises must be handled or test completes early
3. **Use rejects matcher**: For testing async errors (Jest/Vitest)
4. **Set appropriate timeouts**: Long operations need longer timeouts
5. **Clean up resources**: Use afterEach for cleanup
6. **Mock external services**: Isolate unit under test
7. **Test error paths**: Async errors are common, test them
8. **Use Promise.all for parallel**: When operations are independent
9. **Use waitFor for polling**: When waiting for state changes
10. **Don't mix patterns**: Choose async/await OR promises OR callbacks

## Quick Reference

| Pattern | When to Use | Syntax |
|---------|-------------|--------|
| async/await | New code (recommended) | `async () => { await fn() }` |
| .then()/.catch() | Promise chains | `return promise.then(...)` |
| done callback | Legacy callback APIs | `(done) => { fn(done) }` |
| rejects | Async error testing | `await expect(...).rejects.toThrow()` |
| Promise.all | Parallel execution | `await Promise.all([...])` |
| Promise.race | Timeouts/first response | `await Promise.race([...])` |
| beforeEach(async) | Async setup | `beforeEach(async () => {...})` |

## Framework-Specific Notes

### Jest/Vitest
- Use `expect(...).resolves` and `expect(...).rejects` for Promise assertions
- Mock async functions with `mockResolvedValue()` and `mockRejectedValue()`
- Set timeout with `jest.setTimeout()` or test timeout parameter

### Mocha + Chai
- Use `chai-as-promised` plugin for Promise assertions
- Use Sinon's `resolves()` and `rejects()` for async stubs
- Set timeout with `this.timeout()` in test (must use `function()` not arrow)

## References

- MDN Async/Await: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function
- Jest Async: https://jestjs.io/docs/asynchronous
- Vitest Async: https://vitest.dev/guide/features.html#async-tests
- Mocha Async: https://mochajs.org/#asynchronous-code
- Chai as Promised: https://www.chaijs.com/plugins/chai-as-promised/
- JavaScript patterns: `skills/test-generation/javascript-patterns.md`
- Templates: `skills/templates/javascript-*-template.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
