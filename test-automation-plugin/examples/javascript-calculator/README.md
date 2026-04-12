# JavaScript Calculator - Example Project

**Purpose**: Demonstration project for the Automated Testing Plugin for Claude Code

This is a simple JavaScript calculator module designed to showcase the automated testing plugin's capabilities. It contains basic arithmetic operations **without any tests**, allowing you to see the plugin generate comprehensive test suites from scratch.

## Project Structure

```
javascript-calculator/
├── src/
│   └── calculator.js          # Calculator module with 4 functions
├── package.json               # npm configuration with Jest
├── jest.config.js            # Jest configuration
└── README.md                 # This file
```

## Features

The `calculator.js` module provides four basic arithmetic operations:

- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract b from a
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide a by b (with zero-division error handling)

Each function includes:
- JSDoc documentation for clarity
- Comprehensive docstrings with examples
- Error handling (where appropriate)
- CommonJS exports for Node.js compatibility

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Verify Jest is working**:
   ```bash
   npm test
   ```

   You should see: `No tests found` (no tests yet!)

## Using the Plugin

This project is perfect for testing the Automated Testing Plugin. Here are suggested workflows:

### Quick Test: Automated Generation

Generate tests automatically with no approval gates:

```bash
# Open this project in Claude Code
cd examples/javascript-calculator/

# Generate tests automatically
/test-generate src/calculator.js
```

Expected outcome:
- Plugin analyzes `calculator.js`
- Detects Jest as the testing framework
- Generates comprehensive tests for all 4 functions
- Executes tests and shows results
- Tests saved to `.claude-tests/`

### Full Test: Interactive Workflow

Use the human-in-the-loop workflow with approval gates:

```bash
# Start interactive workflow
/test-loop src/calculator.js
```

You'll go through:
1. **Analysis** - Review identified test targets (4 functions)
2. **Plan Approval** - Review and approve test plan
3. **Code Review** - Review and approve generated test code
4. **Execution** - Tests run automatically
5. **Iteration** - Review results and decide next steps

### Analyze Only

Just see what the plugin detects without generating tests:

```bash
/test-analyze src/calculator.js
```

Expected output:
- Language: JavaScript
- Framework: Jest
- Test Targets: 4 functions (add, subtract, multiply, divide)
- Priorities: All High (simple functions)
- Recommendations

## What Tests Should Be Generated

A good test suite for this calculator should include:

### For `add(a, b)`:
- Happy path: `test('should add positive numbers')`
- Edge cases: `test('should add negative numbers')`, `test('should add zero')`
- Type handling: `test('should add floats')`, `test('should add mixed types')`

### For `subtract(a, b)`:
- Happy path: `test('should subtract positive numbers')`
- Edge cases: `test('should subtract to negative')`, `test('should subtract zero')`
- Type handling: `test('should subtract floats')`

### For `multiply(a, b)`:
- Happy path: `test('should multiply positive numbers')`
- Edge cases: `test('should multiply by zero')`, `test('should multiply negative')`
- Type handling: `test('should multiply floats')`

### For `divide(a, b)`:
- Happy path: `test('should divide positive numbers')`
- Error handling: `test('should throw error when dividing by zero')` ⚠️ (most important!)
- Edge cases: `test('should divide negative')`, `test('should divide to float')`

## Expected Test Results

After generation:
- **Total tests**: ~12-16 tests
- **Pass rate**: Should be 100% (all tests should pass)
- **Coverage**: Should achieve >90% line coverage
- **Test file**: `.claude-tests/calculator.test.js` or `__tests__/calculator.test.js`

## Troubleshooting

**Problem**: `jest: command not found`
- **Solution**: Install dependencies: `npm install`

**Problem**: Plugin doesn't detect Jest
- **Solution**: Ensure `jest.config.js` exists and `package.json` lists jest in devDependencies

**Problem**: Tests fail after generation
- **Solution**: This is expected if there are bugs! The plugin's validation should categorize failures and suggest fixes.

**Problem**: `npm test` shows "No tests found"
- **Solution**: Tests haven't been generated yet! Use `/test-generate` to create them.

## Next Steps

After using the plugin to generate tests:

1. **Review generated tests**: Check `.claude-tests/calculator.test.js`
2. **Move tests to project**: `mv .claude-tests/calculator.test.js __tests__/` or keep in src/
3. **Run tests manually**: `npm test`
4. **Check coverage**: `npm test -- --coverage`

## Integration with CI/CD

Once you have generated tests, you can integrate them into your CI/CD pipeline:

```yaml
# Example: GitHub Actions
- name: Install dependencies
  run: npm install

- name: Run tests with coverage
  run: npm test -- --coverage --coverageReporters=text-lcov > coverage.lcov
```

## JavaScript Testing Best Practices

This example demonstrates:
- **Module exports**: Using CommonJS `module.exports` for Node.js
- **JSDoc comments**: Documenting function signatures
- **Error handling**: Proper error throwing and validation
- **Pure functions**: No side effects, easy to test
- **Jest configuration**: Standard setup for Node.js projects

## Comparison with Python Calculator

This JavaScript example mirrors the Python calculator example:
- Same functionality (add, subtract, multiply, divide)
- Same error handling patterns (divide by zero)
- Same documentation approach (JSDoc vs docstrings)
- Same testing workflow (plugin generates tests)
- Same project structure (src/, config files, README)

## Educational Use

This project is ideal for:
- Learning how the plugin works with JavaScript/Jest
- Testing plugin features for JavaScript projects
- Demonstrating test generation to JavaScript teams
- Validating plugin updates for JavaScript support
- Creating plugin tutorials for JavaScript developers
- Comparing test generation across Python vs JavaScript

## Requirements

- **Node.js**: 16+ (async/await support)
- **npm**: 8+ (or yarn, pnpm)
- **Jest**: 29+ (installed via npm install)

## License

This example project is provided as-is for demonstration purposes.
