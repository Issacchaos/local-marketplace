# TypeScript Jest/Vitest Helper Template

This template provides reusable test helper utilities for TypeScript projects using Jest or Vitest.

## Mock Creation Helpers

```typescript
/**
 * Create a mock API client with common methods configured.
 */
export function createMockApiClient(baseUrl: string = 'https://api.example.com') {
    const mock = {
        baseUrl,
        get: jest.fn().mockResolvedValue({ status: 'ok' }),
        post: jest.fn().mockResolvedValue({ id: 1 }),
        put: jest.fn().mockResolvedValue({ updated: true }),
        delete: jest.fn().mockResolvedValue({ deleted: true })
    };
    return mock;
}

/**
 * Create a mock database connection with common operations.
 */
export function createMockDatabase() {
    const mock = {
        connect: jest.fn().mockResolvedValue(true),
        disconnect: jest.fn().mockResolvedValue(true),
        query: jest.fn().mockResolvedValue([]),
        execute: jest.fn().mockResolvedValue({ affectedRows: 1 })
    };
    return mock;
}

/**
 * Create a mock logger with common logging methods.
 */
export function createMockLogger() {
    return {
        info: jest.fn(),
        warn: jest.fn(),
        error: jest.fn(),
        debug: jest.fn()
    };
}
```

## Test Data Builders

```typescript
interface User {
    id: number;
    name: string;
    email: string;
    age?: number;
    role?: string;
}

/**
 * Build a test user object with default values.
 */
export function buildTestUser(overrides: Partial<User> = {}): User {
    return {
        id: 1,
        name: 'Test User',
        email: 'test@example.com',
        age: 30,
        role: 'user',
        ...overrides
    };
}

interface Product {
    id: number;
    name: string;
    price: number;
    category?: string;
    inStock?: boolean;
}

/**
 * Build a test product object with default values.
 */
export function buildTestProduct(overrides: Partial<Product> = {}): Product {
    return {
        id: 1,
        name: 'Test Product',
        price: 99.99,
        category: 'electronics',
        inStock: true,
        ...overrides
    };
}

/**
 * Build a list of test items with sequential IDs.
 */
export function buildTestList<T extends { id: number }>(
    builder: (overrides?: Partial<T>) => T,
    count: number = 3,
    overridesFn?: (index: number) => Partial<T>
): T[] {
    return Array.from({ length: count }, (_, i) =>
        builder({ id: i + 1, ...(overridesFn?.(i) || {}) } as Partial<T>)
    );
}
```

## Setup and Teardown Utilities

```typescript
/**
 * Setup a test environment with common mocks and reset them after each test.
 */
export function setupTestEnvironment() {
    const mockApi = createMockApiClient();
    const mockDb = createMockDatabase();
    const mockLogger = createMockLogger();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    return { mockApi, mockDb, mockLogger };
}

/**
 * Setup and teardown a temporary test database.
 */
export async function withTestDatabase<T>(
    callback: (db: any) => Promise<T>
): Promise<T> {
    const db = createMockDatabase();
    await db.connect();

    try {
        return await callback(db);
    } finally {
        await db.disconnect();
    }
}

/**
 * Run a test with a timeout and automatic cleanup.
 */
export async function withTimeout<T>(
    fn: () => Promise<T>,
    timeoutMs: number = 5000
): Promise<T> {
    return Promise.race([
        fn(),
        new Promise<T>((_, reject) =>
            setTimeout(() => reject(new Error('Test timeout')), timeoutMs)
        )
    ]);
}
```

## Usage Examples

```typescript
import {
    createMockApiClient,
    buildTestUser,
    setupTestEnvironment
} from './test-helpers';

describe('UserService', () => {
    const { mockApi, mockLogger } = setupTestEnvironment();

    it('should fetch user by ID', async () => {
        const testUser = buildTestUser({ id: 123, name: 'John Doe' });
        mockApi.get.mockResolvedValue(testUser);

        const service = new UserService(mockApi, mockLogger);
        const result = await service.getUserById(123);

        expect(result).toEqual(testUser);
        expect(mockApi.get).toHaveBeenCalledWith('/users/123');
    });

    it('should create new user', async () => {
        const newUser = buildTestUser({ id: 0, name: 'Jane Doe' });
        const createdUser = { ...newUser, id: 456 };
        mockApi.post.mockResolvedValue(createdUser);

        const service = new UserService(mockApi, mockLogger);
        const result = await service.createUser(newUser);

        expect(result.id).toBe(456);
        expect(mockApi.post).toHaveBeenCalledWith('/users', newUser);
        expect(mockLogger.info).toHaveBeenCalled();
    });
});
```
