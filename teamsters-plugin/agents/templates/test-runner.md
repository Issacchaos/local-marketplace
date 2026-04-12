---
name: test-runner
description: Template mixin for test workflows. Delegates to test-engineering plugin when available, falls back to Claude's built-in tools otherwise.
type: template
version: "3.0.0"
skill: test-engineering:tdd
---

# Test Runner Agent Template

This template provides test workflow capabilities for agents. It **prefers** the `test-engineering` plugin when available, and **falls back** to Claude's built-in tools (Bash, Read, Write, Glob, Grep) when it is not.

---

## Primary Path: test-engineering Plugin

Use the **Skill tool** to invoke the appropriate test-engineering command. Choose the workflow that matches your task:

### For Test-Driven Development (write tests first, then implement)

```
Skill(skill: "test-engineering:tdd")
```

This runs the full TDD cycle: RED (write failing tests) -> GREEN (implement) -> REFACTOR.

### For Generating Tests for Existing Code

```
Skill(skill: "test-engineering:test-generate")
```

This analyzes the codebase, detects frameworks, and generates tests automatically.

### For Running Existing Tests and Reporting Results

```
Skill(skill: "test-engineering:test-execute")
```

This discovers and runs the existing test suite, then parses results into structured output.

### For Interactive Test Loop (with approval gates)

```
Skill(skill: "test-engineering:test-loop")
```

This runs the full human-in-the-loop workflow with approval at key decision points.

---

## Choosing the Right Workflow

| Task | Skill to Invoke |
|------|----------------|
| Build a feature using TDD | `test-engineering:tdd` |
| Add tests to existing untested code | `test-engineering:test-generate` |
| Run tests and get structured results | `test-engineering:test-execute` |
| Interactive test development | `test-engineering:test-loop` |
| Analyze what needs testing | `test-engineering:test-analyze` |

---

## Fallback Path: Built-in Testing

When the `test-engineering` plugin is **not installed** or the Skill tool invocation **fails**, use Claude's built-in tools to perform testing directly. Follow these steps:

### Step 1: Detect the Test Framework

Use Glob and Grep to identify the project's language and test runner:

| Indicator File | Language | Test Command |
|----------------|----------|-------------|
| `package.json` with `jest` or `vitest` in devDependencies | JavaScript/TypeScript | `npm test` or `npx jest` or `npx vitest` |
| `package.json` with `mocha` in devDependencies | JavaScript/TypeScript | `npx mocha` |
| `pytest.ini`, `pyproject.toml` (has `[tool.pytest]`), or `conftest.py` | Python | `pytest` |
| `setup.py` or `tox.ini` | Python | `python -m pytest` |
| `pom.xml` | Java (Maven) | `mvn test` |
| `build.gradle` or `build.gradle.kts` | Java/Kotlin (Gradle) | `./gradlew test` |
| `go.mod` | Go | `go test ./...` |
| `*.csproj` or `*.sln` | C# (.NET) | `dotnet test` |
| `Cargo.toml` | Rust | `cargo test` |
| `CMakeLists.txt` with `enable_testing()` | C/C++ | `cmake --build . && ctest` |

**How to detect**:
1. Use `Glob(pattern: "package.json")` or `Glob(pattern: "**/pytest.ini")` to find config files
2. Use `Read` to inspect the file contents (e.g., check `devDependencies` for the test framework)
3. Use `Grep(pattern: "test", path: "package.json")` to find test scripts

### Step 2: Run Existing Tests

Execute the detected test command using Bash:

```
Bash(command: "<test-command>", timeout: 120000)
```

**Tips**:
- Add verbose flags for better output: `npm test -- --verbose`, `pytest -v`, `go test -v ./...`
- For coverage: `npm test -- --coverage`, `pytest --cov`, `go test -cover ./...`
- Set a reasonable timeout (120s default, increase for large suites)

### Step 3: Generate Tests for Untested Code

When asked to generate tests for existing source files:

1. **Read the source file** to understand its exports, functions, classes, and behavior
2. **Find existing test files** with `Glob(pattern: "**/*.test.*")` or `Glob(pattern: "**/test_*.py")` to learn the project's test patterns (imports, structure, assertion style)
3. **Write new test files** following the same patterns:
   - Match the project's file naming convention (`*.test.ts`, `*_test.go`, `test_*.py`, etc.)
   - Place tests in the project's test directory (colocated or separate `tests/` folder)
   - Import the source module and test its public API
   - Include happy path, edge cases, and error cases
4. **Run the new tests** to verify they pass (or intentionally fail for TDD red phase)

### Step 4: Parse and Report Results

After running tests, parse the Bash output and report structured results:

```
## Test Results

**Status**: PASSED | FAILED | ERROR
**Total**: N tests
**Passed**: N
**Failed**: N
**Skipped**: N
**Duration**: Xs

### Failures (if any)
- `test_name`: failure reason / assertion message
```

---

## Important Notes

- **Try the Skill tool first** -- if `test-engineering` is available, it provides superior framework detection, test placement, and structured reporting
- If the Skill tool call fails or returns an error indicating the plugin is not installed, switch to the **Fallback Path** above
- When using the fallback path, always check for existing test patterns in the project before generating new tests
- Report results in the structured format above regardless of which path was used
