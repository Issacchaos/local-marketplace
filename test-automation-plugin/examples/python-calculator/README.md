# Python Calculator - Example Project

**Purpose**: Demonstration project for the Automated Testing Plugin for Claude Code

This is a simple Python calculator module designed to showcase the automated testing plugin's capabilities. It contains basic arithmetic operations **without any tests**, allowing you to see the plugin generate comprehensive test suites from scratch.

## Project Structure

```
python-calculator/
├── src/
│   └── calculator.py      # Calculator module with 4 functions
├── pytest.ini             # Pytest configuration
├── requirements.txt       # Python dependencies (pytest)
└── README.md             # This file
```

## Features

The `calculator.py` module provides four basic arithmetic operations:

- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract b from a
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide a by b (with zero-division error handling)

Each function includes:
- Type hints for clarity
- Comprehensive docstrings
- Error handling (where appropriate)
- Doctests as examples

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify pytest is working**:
   ```bash
   pytest
   ```

   You should see: `collected 0 items` (no tests yet!)

## Using the Plugin

This project is perfect for testing the Automated Testing Plugin. Here are suggested workflows:

### Quick Test: Automated Generation

Generate tests automatically with no approval gates:

```bash
# Open this project in Claude Code
cd examples/python-calculator/

# Generate tests automatically
/test-generate src/calculator.py
```

Expected outcome:
- Plugin analyzes `calculator.py`
- Detects pytest as the testing framework
- Generates comprehensive tests for all 4 functions
- Executes tests and shows results
- Tests saved to `tests/` (discoverable by pytest)

### Full Test: Interactive Workflow

Use the human-in-the-loop workflow with approval gates:

```bash
# Start interactive workflow
/test-loop src/calculator.py
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
/test-analyze src/calculator.py
```

Expected output:
- Language: Python
- Framework: pytest
- Test Targets: 4 functions (add, subtract, multiply, divide)
- Priorities: All High (simple functions)
- Recommendations

## What Tests Should Be Generated

A good test suite for this calculator should include:

### For `add(a, b)`:
- Happy path: `test_add_positive_numbers`
- Edge cases: `test_add_negative_numbers`, `test_add_zero`
- Type handling: `test_add_floats`, `test_add_mixed_types`

### For `subtract(a, b)`:
- Happy path: `test_subtract_positive_numbers`
- Edge cases: `test_subtract_to_negative`, `test_subtract_zero`
- Type handling: `test_subtract_floats`

### For `multiply(a, b)`:
- Happy path: `test_multiply_positive_numbers`
- Edge cases: `test_multiply_by_zero`, `test_multiply_negative`
- Type handling: `test_multiply_floats`

### For `divide(a, b)`:
- Happy path: `test_divide_positive_numbers`
- Error handling: `test_divide_by_zero_raises_error` ⚠️ (most important!)
- Edge cases: `test_divide_negative`, `test_divide_to_float`

## Expected Test Results

After generation:
- **Total tests**: ~12-16 tests
- **Pass rate**: Should be 100% (all tests should pass)
- **Coverage**: Should achieve >90% line coverage
- **Test file**: `tests/test_calculator.py` (discoverable by pytest)

## Troubleshooting

**Problem**: `pytest: command not found`
- **Solution**: Install pytest: `pip install -r requirements.txt`

**Problem**: Plugin doesn't detect pytest
- **Solution**: Ensure `pytest.ini` exists and `requirements.txt` lists pytest

**Problem**: Tests fail after generation
- **Solution**: This is expected if there are bugs! The plugin's validation should categorize failures and suggest fixes.

## Next Steps

After using the plugin to generate tests:

1. **Review generated tests**: Check `tests/test_calculator.py`
2. **Run tests manually**: `pytest tests/test_calculator.py`
3. **Check coverage**: `pytest --cov=src tests/`
4. **Commit tests**: `git add tests/ && git commit -m "Add automated tests"`

## Integration with CI/CD

Once you have generated tests, you can integrate them into your CI/CD pipeline:

```yaml
# Example: GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=src --cov-report=xml
```

## Educational Use

This project is ideal for:
- Learning how the plugin works
- Testing plugin features
- Demonstrating test generation to teams
- Validating plugin updates
- Creating plugin tutorials

## License

This example project is provided as-is for demonstration purposes.
