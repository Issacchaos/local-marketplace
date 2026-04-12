# JavaScript Mocha Test Template

**Purpose**: Template for generating Mocha test files with Chai assertions
**Target Language**: JavaScript
**Test Framework**: Mocha + Chai
**Version Support**: Mocha 9.x+, Chai 4.x+

## Template Structure

```javascript
/**
 * Test module for {MODULE_NAME}.
 */

const { expect } = require('chai');
{ADDITIONAL_IMPORTS}

describe('{SUITE_NAME}', () => {
  {SETUP_CODE}

  {TEST_CASES}
});
```

## Key Differences from Jest

- **No built-in assertions**: Requires Chai or other assertion library
- **No built-in mocking**: Requires Sinon or other mocking library
- **Flexible**: Can use any assertion/mocking libraries
- **Chai syntax**: `expect(value).to.equal(5)` instead of `expect(value).toBe(5)`

## Example with Chai

```javascript
const { expect } = require('chai');
const { add, subtract } = require('./calculator');

describe('Calculator', () => {
  describe('add', () => {
    it('should add two numbers', () => {
      // Arrange
      const a = 5;
      const b = 3;

      // Act
      const result = add(a, b);

      // Assert
      expect(result).to.equal(8);
    });

    it('should handle negative numbers', () => {
      // Arrange
      const a = -5;
      const b = -3;

      // Act
      const result = add(a, b);

      // Assert
      expect(result).to.equal(-8);
    });
  });

  describe('subtract', () => {
    it('should subtract two numbers', () => {
      // Arrange
      const a = 10;
      const b = 3;

      // Act
      const result = subtract(a, b);

      // Assert
      expect(result).to.equal(7);
    });
  });
});
```

## Example with Setup/Teardown

```javascript
const { expect } = require('chai');
const { Database } = require('./database');

describe('Database', () => {
  let db;

  beforeEach(() => {
    // Arrange - Setup database connection
    db = new Database();
    db.connect();
  });

  afterEach(() => {
    // Cleanup - Close database connection
    db.disconnect();
  });

  it('should insert a record', () => {
    // Arrange
    const record = { id: 1, name: 'Alice' };

    // Act
    db.insert(record);

    // Assert
    expect(db.count()).to.equal(1);
    expect(db.find(1)).to.deep.equal(record);
  });
});
```

## Example with Mocking (Sinon)

```javascript
const { expect } = require('chai');
const sinon = require('sinon');
const { UserService } = require('./user-service');
const apiClient = require('./api-client');

describe('UserService', () => {
  let sandbox;
  let userService;

  beforeEach(() => {
    // Arrange - Setup sandbox and service
    sandbox = sinon.createSandbox();
    userService = new UserService();
  });

  afterEach(() => {
    // Cleanup - Restore all stubs
    sandbox.restore();
  });

  it('should fetch and process user data', async () => {
    // Arrange
    const mockUser = { id: 1, name: 'Alice', age: 30 };
    sandbox.stub(apiClient, 'getUser').resolves(mockUser);

    // Act
    const result = await userService.processUser(1);

    // Assert
    sinon.assert.calledWith(apiClient.getUser, 1);
    expect(result.displayName).to.equal('Alice (30)');
  });
});
```

## Chai Assertions

```javascript
// Equality
expect(value).to.equal(5);             // Strict
expect(value).to.deep.equal({ a: 1}); // Deep

// Truthiness
expect(value).to.be.true;
expect(value).to.be.null;
expect(value).to.exist;

// Numbers
expect(value).to.be.above(5);
expect(value).to.be.below(10);

// Strings
expect(string).to.include('substring');
expect(string).to.match(/pattern/);

// Arrays
expect(array).to.include('item');
expect(array).to.have.lengthOf(3);

// Exceptions
expect(() => fn()).to.throw();
expect(() => fn()).to.throw('error message');
```

## Sinon Mocking

```javascript
const sinon = require('sinon');

// Stub
const stub = sinon.stub(obj, 'method');
stub.returns(42);
stub.resolves({ data: 'value' });

// Spy
const spy = sinon.spy(obj, 'method');
sinon.assert.calledOnce(spy);
sinon.assert.calledWith(spy, arg1, arg2);

// Sandbox (auto-cleanup)
const sandbox = sinon.createSandbox();
sandbox.restore();  // Restores all stubs/spies
```

## References

- Mocha: https://mochajs.org/
- Chai Assertions: https://www.chaijs.com/api/bdd/
- Sinon Mocking: https://sinonjs.org/
- JavaScript Patterns: `skills/test-generation/javascript-patterns.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
