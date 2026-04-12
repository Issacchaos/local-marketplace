# TypeScript API Client - Example Project

**Purpose**: Demonstration project for the Automated Testing Plugin for Claude Code with TypeScript + Jest

This is a TypeScript API client designed to showcase the automated testing plugin's capabilities with TypeScript. It contains a REST API client with modern TypeScript features **without any tests**, allowing you to see the plugin generate comprehensive test suites from scratch.

## Project Structure

```
typescript-api/
├── src/
│   └── api-client.ts         # API client with TypeScript types
├── package.json              # npm configuration with Jest and ts-jest
├── tsconfig.json             # TypeScript configuration (strict mode)
├── jest.config.js            # Jest configuration for TypeScript
└── README.md                 # This file
```

## Features

The `api-client.ts` module provides a complete REST API client with TypeScript features:

### Core Classes & Functions:
- `ApiClient` - Main client class with HTTP methods (GET, POST, PUT, DELETE)
- `createApiClient()` - Factory function to create configured clients
- `isApiError()` - Type guard for error handling

### TypeScript Features Demonstrated:
- **Interfaces**: `ApiConfig`, `ApiResponse<T>`, `User`, `RequestOptions`
- **Generics**: `ApiResponse<T>`, generic HTTP methods
- **Type Guards**: `isApiError(error)`
- **Type Aliases**: `HttpMethod`, utility types
- **Custom Errors**: `ApiError` class with type safety
- **Async/Await**: All HTTP methods are async
- **Strict Type Checking**: Enabled in tsconfig.json

### Methods:
- `get<T>(endpoint, options?)` - Perform GET request with generic type
- `post<T>(endpoint, options?)` - Perform POST request
- `put<T>(endpoint, options?)` - Perform PUT request
- `delete<T>(endpoint, options?)` - Perform DELETE request
- `buildUrl(endpoint, params?)` - Private method for URL construction
- `setHeaders(headers)` - Update client headers
- `getBaseUrl()` - Get configured base URL
- `getTimeout()` - Get configured timeout

Each method includes:
- Full TypeScript type annotations (no `any` types)
- Comprehensive TSDoc documentation
- Generic type parameters for flexible responses
- Async/await patterns
- Error handling with custom `ApiError` class

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Verify TypeScript compilation**:
   ```bash
   npx tsc --noEmit
   ```
   Should show no errors (strict mode enabled)

3. **Verify Jest is working**:
   ```bash
   npm test
   ```
   You should see: `No tests found` (no tests yet!)

## Using the Plugin

This project is perfect for testing the Automated Testing Plugin with TypeScript. Here are suggested workflows:

### Quick Test: Automated Generation

Generate tests automatically with no approval gates:

```bash
# Open this project in Claude Code
cd examples/typescript-api/

# Generate tests automatically
/test-generate src/api-client.ts
```

Expected outcome:
- Plugin analyzes `api-client.ts`
- Detects TypeScript + Jest + ts-jest
- Generates comprehensive typed tests for all methods
- Executes tests with TypeScript compilation
- Tests saved to `.claude-tests/`

### Full Test: Interactive Workflow

Use the human-in-the-loop workflow with approval gates:

```bash
# Start interactive workflow
/test-loop src/api-client.ts
```

You'll go through:
1. **Analysis** - Review identified test targets (ApiClient class, utility functions)
2. **Plan Approval** - Review and approve test plan
3. **Code Review** - Review and approve generated TypeScript test code
4. **Execution** - Tests compile with tsc and run with Jest
5. **Iteration** - Review results and decide next steps

### Analyze Only

Just see what the plugin detects without generating tests:

```bash
/test-analyze src/api-client.ts
```

Expected output:
- Language: TypeScript
- Framework: Jest (with ts-jest)
- Type System: Enabled (strict mode)
- Test Targets: ApiClient class, utility functions
- Priorities: All High (core functionality)
- Recommendations

## What Tests Should Be Generated

A good test suite for this API client should include:

### For `ApiClient` class:
- **Constructor tests**:
  - `test('should initialize with required config')`
  - `test('should use default timeout when not provided')`
  - `test('should use default headers when not provided')`

### For `get<T>()` method:
- **Happy path**:
  - `test('should perform GET request successfully')`
  - `test('should return typed response')`
- **Query parameters**:
  - `test('should append query parameters to URL')`
  - `test('should handle multiple query parameters')`
- **Error handling**:
  - `test('should throw ApiError on 404')`
  - `test('should throw ApiError on 500')`

### For `post<T>()` method:
- **Happy path**:
  - `test('should perform POST request with body')`
  - `test('should return 201 status for creation')`
- **Type safety**:
  - `test('should infer correct response type from generic')`

### For `put<T>()` and `delete<T>()` methods:
- Similar patterns to GET and POST

### For `buildUrl()` private method:
- `test('should build URL without parameters')`
- `test('should build URL with query parameters')`
- `test('should encode special characters in parameters')`

### For `createApiClient()` factory:
- `test('should create client with baseUrl')`
- `test('should merge options with baseUrl')`

### For `isApiError()` type guard:
- `test('should return true for ApiError instance')`
- `test('should return false for other errors')`
- `test('should narrow type to ApiError when true')`

### For `ApiError` class:
- `test('should create error with message and status code')`
- `test('should include response data when provided')`
- `test('should be instance of Error')`

## Expected Test Results

After generation:
- **Total tests**: ~20-30 tests
- **Pass rate**: Should be 100% (all tests should pass)
- **Coverage**: Should achieve >90% line coverage
- **Type checking**: All tests should pass TypeScript strict mode
- **Test file**: `.claude-tests/api-client.test.ts` or `src/__tests__/api-client.test.ts`

## TypeScript-Specific Testing Considerations

The plugin should generate tests that:

1. **Use proper types** (avoid `any`):
   ```typescript
   const client: ApiClient = new ApiClient({ baseUrl: 'https://api.example.com' });
   const response: ApiResponse<User[]> = await client.get<User[]>('/users');
   ```

2. **Test generic type inference**:
   ```typescript
   const response = await client.get<User[]>('/users');
   expect(response.data).toHaveLength(2);
   expect(response.data[0]).toHaveProperty('id');
   ```

3. **Test type guards**:
   ```typescript
   if (isApiError(error)) {
     expect(error.statusCode).toBe(404);
   }
   ```

4. **Mock with proper types**:
   ```typescript
   const mockClient = {
     get: jest.fn() as jest.MockedFunction<typeof client.get>
   };
   ```

5. **Test async/await patterns**:
   ```typescript
   await expect(client.get('/invalid')).rejects.toThrow(ApiError);
   ```

## Troubleshooting

**Problem**: `ts-jest: command not found` or TypeScript errors
- **Solution**: Install dependencies: `npm install`

**Problem**: Plugin doesn't detect TypeScript
- **Solution**: Ensure `tsconfig.json` exists and `package.json` lists typescript + ts-jest

**Problem**: Tests fail with type errors
- **Solution**: This is expected! The plugin's validation should identify type issues and suggest fixes

**Problem**: `npm test` shows "No tests found"
- **Solution**: Tests haven't been generated yet! Use `/test-generate` to create them

**Problem**: Tests compile but fail at runtime
- **Solution**: Check for type mismatches. Use `/test-loop` to iterate with fixes

## Next Steps

After using the plugin to generate tests:

1. **Review generated tests**: Check `.claude-tests/api-client.test.ts`
2. **Verify type safety**: Ensure tests use proper TypeScript types (no `any`)
3. **Move tests to project**: `mv .claude-tests/api-client.test.ts src/__tests__/`
4. **Run tests manually**: `npm test`
5. **Check coverage**: `npm test -- --coverage`
6. **Type check tests**: `npx tsc --noEmit` (ensure tests pass strict mode)

## Integration with CI/CD

Once you have generated tests, you can integrate them into your CI/CD pipeline:

```yaml
# Example: GitHub Actions
- name: Install dependencies
  run: npm install

- name: Type check
  run: npx tsc --noEmit

- name: Run tests with coverage
  run: npm test -- --coverage --coverageReporters=text-lcov > coverage.lcov

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.lcov
```

## TypeScript Testing Best Practices

This example demonstrates:
- **Strict type checking**: All code passes `strict: true` in tsconfig.json
- **Generic types**: Flexible API responses with type safety
- **Type guards**: Runtime type checking with compile-time guarantees
- **Async/await**: Modern async patterns with Promise handling
- **Custom errors**: Type-safe error handling with custom classes
- **No external dependencies**: Pure TypeScript logic (easy to test)
- **TSDoc documentation**: Complete type and parameter documentation
- **ts-jest integration**: Seamless TypeScript testing with Jest

## Comparison with JavaScript Calculator

This TypeScript example extends beyond the JavaScript example:
- **Type safety**: Full TypeScript types and interfaces
- **Generics**: Reusable code with type parameters
- **Strict mode**: Enabled for maximum type checking
- **Complex patterns**: Classes, type guards, custom errors
- **Async/await**: Asynchronous API client patterns
- **Professional structure**: Real-world API client architecture

## Educational Use

This project is ideal for:
- Learning how the plugin works with TypeScript + Jest
- Testing plugin features for TypeScript projects
- Demonstrating test generation with TypeScript types
- Validating plugin type inference capabilities
- Creating plugin tutorials for TypeScript developers
- Showcasing async/await test generation
- Testing strict mode type annotation generation

## Requirements

- **Node.js**: 16+ (for async/await and modern features)
- **npm**: 8+ (or yarn, pnpm)
- **TypeScript**: 5.0+ (strict mode support)
- **Jest**: 29+ (with ts-jest preset)
- **ts-jest**: 29+ (TypeScript transformation)

## Technical Highlights

### TypeScript Features Used:
- ✅ Interfaces (`ApiConfig`, `ApiResponse<T>`, `User`, `RequestOptions`)
- ✅ Generics (`ApiResponse<T>`, generic methods)
- ✅ Type aliases (`HttpMethod`)
- ✅ Type guards (`isApiError`)
- ✅ Custom error classes (`ApiError`)
- ✅ Utility types (`Omit<ApiConfig, 'baseUrl'>`, `Required<ApiConfig>`)
- ✅ Async/await patterns (all HTTP methods)
- ✅ Strict null checks (enabled)
- ✅ No implicit any (enabled)

### Jest + ts-jest Configuration:
- ✅ `preset: 'ts-jest'` for TypeScript transformation
- ✅ Strict type checking in tests
- ✅ Coverage collection from `.ts` files
- ✅ Source map support for debugging
- ✅ Fast compilation with `skipLibCheck`

## License

This example project is provided as-is for demonstration purposes.
