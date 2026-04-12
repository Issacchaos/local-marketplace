# Automated Testing Plugin for Claude Code

**Status**: Production Ready
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++ (7 languages fully supported)

## Overview

An intelligent automated testing plugin that brings comprehensive test generation, execution, and validation capabilities directly into Claude Code. Built with a human-in-the-loop workflow, this plugin helps developers write high-quality tests faster while maintaining control over the testing process.

### Key Features

- 🔍 **Intelligent Code Analysis**: Automatically identifies what needs testing and prioritizes by complexity
- 🤖 **AI-Powered Test Generation**: Generates comprehensive tests using framework-specific templates
- ⚡ **Context-Aware Execution**: Uses your project's native build and test commands
- 🎯 **Human-in-the-Loop**: Approval gates at key decision points (test plan, code review, iteration)
- 📊 **Comprehensive Parsing**: Accurate result parsing with 11+ framework-specific parsers
- 🔄 **Workflow Resumption**: State persistence allows resuming interrupted workflows
- 🌍 **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C#, Go, C++ (7 languages)
- 🔧 **Auto-Heal Workflow**: Automatically fixes newly-written test bugs (50-70% faster iterations)
- ⚡ **Smart Test Selection**: Runs only modified tests during fix iterations (not all tests)
- 🧹 **Automated Linting**: Formats and lints generated tests with project-configured tools
- 📈 **File Coverage Tracking**: Shows which files were tested and why others were skipped

## Current Status

**Production Ready**: All core features complete across 7 programming languages

**Available Commands**:
- `/test-analyze` - Analyze code and identify testing targets
- `/test-generate` - Fully automated test generation workflow
- `/test-loop` - Human-in-the-loop interactive workflow with approval gates
- `/test-resume` - Resume interrupted workflows from saved state

## Quick Start (5 Minutes)

### Prerequisites

- **Claude Code** (latest version) - [Installation Guide](https://docs.claude.com/claude-code)
- **Language-specific requirements**:
  - **Python 3.8+**: pytest
  - **JavaScript/TypeScript**: Jest, Vitest, or Mocha
  - **Java**: JUnit 4/5 or TestNG (Maven or Gradle)
  - **C#**: xUnit, NUnit, or MSTest (.NET CLI)
  - **Go**: Built-in testing package or testify
  - **C++**: Google Test or Catch2 (CMake)

### Installation

**See [INSTALLATION.md](../INSTALLATION.md) for detailed installation instructions.**

**Quick Install**:
```bash
# 1. Navigate to Claude Code plugins directory
cd ~/.claude/plugins/  # macOS/Linux
cd %USERPROFILE%\.claude\plugins\  # Windows

# 2. Clone this repository
git clone https://github.example.com/my-org/my-plugin.git automated-testing-plugin

# 3. Restart Claude Code

# 4. Verify installation - commands should autocomplete
# Type: /test<Tab>
```

**What you should see**: `/test-analyze`, `/test-generate`, `/test-loop`, `/test-resume`

✅ If commands appear, installation successful!

**Troubleshooting**: See [INSTALLATION.md](../INSTALLATION.md) for help.

### Your First Test (Automated)

For a quick, fully automated experience:

```bash
# 1. Open a project in Claude Code
cd my-project/

# 2. Generate tests automatically (analyzes, generates, executes in one command)
/test-generate src/myfile.py  # Python
/test-generate src/myfile.ts  # TypeScript
/test-generate src/MyClass.java  # Java
```

That's it! The plugin will:
- Analyze your code structure
- Detect your testing framework
- Generate comprehensive tests in standard locations
- Execute them and show results
- Auto-fix any test bugs (with approval)
- All automatically with smart defaults

### Your First Test (Interactive)

For full control with approval gates:

```bash
# 1. Open a project in Claude Code
cd my-project/

# 2. Start interactive workflow
/test-loop src/myfile.py
```

You'll go through:
1. **Code Analysis** - Review detected targets
2. **Test Plan Approval** - Approve/modify test plan
3. **Code Review** - Approve/modify generated tests
4. **Execution** - Tests run automatically
5. **Auto-Heal** - New tests auto-fix, existing require approval
6. **Results** - Decide next steps (done, fix, or generate more)

The workflow automatically saves state, so you can `/test-resume` if interrupted!

## Supported Languages & Frameworks

### ✅ Production Ready (All Complete)

| Language | Frameworks | Build Tools | Status |
|----------|-----------|-------------|--------|
| **Python** | pytest, unittest | pip | ✅ Complete |
| **JavaScript** | Jest, Vitest, Mocha | npm, yarn, pnpm | ✅ Complete |
| **TypeScript** | Jest (ts-jest), Vitest | npm, yarn, pnpm | ✅ Complete |
| **Java** | JUnit 4/5, TestNG | Maven, Gradle | ✅ Complete |
| **C#** | xUnit, NUnit, MSTest | dotnet CLI | ✅ Complete |
| **Go** | testing, testify | go test | ✅ Complete |
| **C++** | Google Test, Catch2 | CMake, CTest | ✅ Complete |

**Each language includes**:
- Framework detection with confidence scoring
- Result parsers for framework-specific output
- Test generation patterns and templates
- Build system integration
- Test location detection (standard paths)
- Auto-heal support
- Smart test selection
- Automated linting

### 🔮 Future Languages (Planned)

| Language | Frameworks | Priority |
|----------|-----------|----------|
| **Rust** | Cargo test | Low |
| **Ruby** | RSpec | Low |
| **C** | Unity | Low |

## Commands Reference

### `/test-analyze [path]`

Analyzes code to identify testing targets and priorities.

**Arguments**:
- `path` (optional): Directory or file to analyze (default: workspace root)

**Output**:
- Detected language and framework
- List of test targets with priorities (Critical, High, Medium, Low)
- Complexity scores
- Coverage gap analysis
- Testing recommendations

**Example**:
```bash
/test-analyze src/
```

### `/test-generate [type] [path]`

Automated end-to-end test generation workflow (no approval gates).

**Arguments**:
- `type` (optional): Test type - `unit`, `integration`, `e2e` (default: `unit`)
- `path` (optional): Path to analyze (default: workspace root)

**Workflow**:
1. Analyzes code
2. Generates test plan
3. Generates test code in standard locations
4. Executes tests
5. Auto-fixes test bugs (up to 3 iterations)
6. Runs linting and formatting
7. Shows results with file coverage tracking

**Example**:
```bash
/test-generate unit src/calculator.py
```

### `/test-loop [path]`

Interactive testing workflow with human approval gates at key decision points.

**Arguments**:
- `path` (optional): Starting path for analysis (default: workspace root)

**Workflow Phases**:
1. 🔍 **Analysis** - Scan code and identify test targets
2. ✅ **Plan Approval** (Gate #1) - Review and approve test plan
3. 📝 **Code Generation** - Generate tests from approved plan (in standard locations)
4. ✅ **Code Approval** (Gate #2) - Review and approve generated code
5. ⚡ **Execution** - Run approved tests
6. 🔍 **Validation** - Analyze results and categorize failures
7. 🔧 **Auto-Heal** - Fix test bugs automatically (new tests) or with approval (existing tests)
8. 🧹 **Linting** - Format and lint tests with project tools
9. ✅ **Iteration Decision** (Gate #3) - Done, fix, or generate more

**Approval Gates**:
- **Gate #1 - Test Plan Review**: Approve/modify/reject the test plan before code generation
- **Gate #2 - Code Review**: Approve/modify/reject the generated test code before execution
- **Gate #3 - Iteration Decision**: Done, fix and retry, generate more tests, or cancel

**Features**:
- ✅ Full control with 3 approval gates
- ✅ Auto-heal for newly written tests
- ✅ Smart test selection (only runs modified tests in iterations)
- ✅ Automated linting and unused code cleanup
- ✅ File coverage tracking with skip explanations
- ✅ State persistence (resume with `/test-resume`)
- ✅ Error recovery and retry options

**When to use**:
- You want to review test plans before code generation
- You want to inspect generated code before execution
- You need iterative improvement with feedback
- You're working on critical code requiring careful testing

**Example**:
```bash
/test-loop src/api/
```

**Comparison with /test-generate**:
- `/test-loop`: Interactive, 3 approval gates, full control, auto-heal with approval
- `/test-generate`: Automated, no gates, fast, auto-heal by default

### `/test-resume`

Resumes an interrupted testing workflow from saved state.

**How it works**:
1. Loads state from `{project_root}/.claude/.test-loop-state.md`
2. Displays current progress and phase
3. Resumes test-loop-orchestrator from interruption point
4. Continues workflow with all context preserved

**When to use**:
- Claude Code was closed during a workflow
- You need to continue a paused workflow
- A workflow was interrupted by error
- You want to finish an incomplete workflow

**State persistence**:
- Active state: `{project_root}/.claude/.test-loop-state.md`
- Archived states: `{project_root}/.claude/.test-loop-history/`

**Example**:
```bash
# Start workflow
/test-loop src/

# [Close Claude Code or workflow interrupted]

# Resume later
/test-resume
```

## Architecture

### Components

```
Plugin Architecture:
├── Agents (Specialized AI assistants)
│   ├── Analyze Agent: Code analysis and target identification
│   ├── Write Agent: Test code generation with location detection
│   ├── Execute Agent: Test execution with smart test selection
│   ├── Validate Agent: Result validation and failure analysis
│   └── Fix Agent: Automatic test bug fixing (5 subcategories)
│
├── Subagents (Complex workflow orchestration)
│   └── Test Loop Orchestrator: 9-phase human-in-the-loop workflow
│
├── Skills (Reusable knowledge modules)
│   ├── Framework Detection: 7 languages, 18+ frameworks
│   ├── Test Generation: Language-specific patterns (7 languages)
│   ├── Result Parsing: 11+ framework-specific parsers
│   ├── Code Analysis: Complexity and coverage analysis
│   ├── State Management: Workflow persistence
│   ├── Test Location Detection: Standard path resolution
│   ├── Project Detection: Project root identification
│   └── Linting: Multi-language linter detection and execution
│
├── Templates (Framework-specific test templates)
│   └── 18 templates across 7 languages
│
└── Commands (User interface)
    └── /test-analyze, /test-generate, /test-loop, /test-resume
```

### Design Principles

1. **Agent-Based Architecture**: Specialized agents for distinct testing phases
2. **Human-in-the-Loop**: User maintains control with approval gates
3. **Framework Agnostic**: Support multiple frameworks via skills/parsers
4. **Context-Aware**: Uses project's existing configuration and commands
5. **Production-Ready**: Mirrors Dante's proven architecture
6. **Standard Locations**: Tests written to standard, version-controlled locations
7. **Auto-Heal Intelligence**: Distinguishes new vs existing tests for smart auto-fixing

## How It Works

### Test Generation Flow

```
1. ANALYZE
   └─→ Scan project files
   └─→ Detect language (Python, JavaScript, TypeScript, Java, C#, Go, C++)
   └─→ Detect framework (pytest, Jest, JUnit, xUnit, Go testing, GTest, etc.)
   └─→ Identify test targets (functions, classes, methods)
   └─→ Calculate complexity scores
   └─→ Prioritize targets

2. GENERATE PLAN
   └─→ Create test cases for each target
   └─→ Include edge cases and error conditions
   └─→ Specify mocking requirements

3. GENERATE CODE
   └─→ Load framework-specific template
   └─→ Generate test code with proper structure
   └─→ Include imports, fixtures, assertions
   └─→ Follow framework conventions
   └─→ Resolve standard test locations (no .claude-tests/)

4. EXECUTE
   └─→ Use project's native test command
   └─→ Capture stdout and stderr
   └─→ Parse framework-specific output
   └─→ Track which tests were generated

5. AUTO-HEAL (if test failures)
   └─→ Check if tests are newly generated
   └─→ Auto-fix new tests (confidence > 0.7)
   └─→ Request approval for fixing existing tests
   └─→ Apply fixes iteratively (max 3 iterations)
   └─→ Re-run only modified tests (smart selection)

6. LINT & CLEANUP
   └─→ Detect project-configured linters
   └─→ Run formatters (black, prettier, gofmt, clang-format)
   └─→ Run linters with auto-fix (ruff, eslint, golangci-lint)
   └─→ Clean up unused imports and variables
   └─→ Display results

7. VALIDATE & REPORT
   └─→ Analyze test results
   └─→ Show file coverage (identified vs generated)
   └─→ Explain why files were skipped
   └─→ Provide actionable recommendations
```

## Examples

### Example 1: Quick Automated Testing (Python)

```bash
# Scenario: You have a new Python file and want tests fast

# Generate tests for a single file
/test-generate src/utils/string_helpers.py

# Output:
# - Analyzes string_helpers.py
# - Detects pytest
# - Generates 8 tests for 4 functions in tests/
# - Executes tests (7 passed, 1 failed)
# - Auto-fixes the 1 failed test
# - Re-runs modified test (1 passed)
# - Runs black and ruff for formatting/linting
# - Shows file coverage: 1 identified, 1 generated, 0 skipped
```

### Example 2: Multi-Language Project

```bash
# JavaScript/TypeScript project with Jest
/test-generate src/api/users.ts

# Java project with Maven
/test-generate src/main/java/com/example/UserService.java

# Go project
/test-generate pkg/calculator/math.go

# C# project with xUnit
/test-generate src/Services/AuthenticationService.cs
```

### Example 3: Interactive Testing with Control (Java)

```bash
# Scenario: Critical authentication code needs careful testing

# Start interactive workflow
/test-loop src/main/java/com/example/auth/Authentication.java

# Step 1: Analysis completes
# Shows: 5 critical methods, 3 high priority methods

# Step 2: Review test plan (Gate #1)
# You see:
# - testLoginValidCredentials
# - testLoginInvalidPassword
# - testLoginAccountLocked
# - ... (15 test cases total)
#
# You decide: ✅ Approve

# Step 3: Code generated in src/test/java/com/example/auth/
# 15 tests created in AuthenticationTest.java

# Step 4: Review code (Gate #2)
# You notice a test is missing edge case
# You decide: 🔄 Request Changes
# Feedback: "Add test for expired tokens"

# Step 5: Code regenerated with feedback
# 16 tests now (added testLoginExpiredToken)
# You decide: ✅ Approve

# Step 6: Tests execute
# Results: 15 passed, 1 failed

# Step 7: Auto-heal activates
# New test detected: testLoginExpiredToken
# Confidence: 0.85 (high)
# Auto-fix applied without approval
# Re-run: 1 test (smart selection)
# Result: 1 passed ✅

# Step 8: Linting runs
# Maven spotless formats code
# Checkstyle verifies style compliance
# All clean ✅

# Step 9: Iteration decision (Gate #3)
# All tests passing, code formatted
# You decide: ✅ Done

# Workflow complete! Tests saved to src/test/java/
```

### Example 4: File Coverage Tracking

```bash
# Analyze entire package
/test-loop src/data/

# Output shows file coverage:
# File Coverage Summary:
# - Identified: 7 files
# - Generated tests for: 5 files
# - Skipped: 2 files
#
# Skipped Files:
# 1. src/data/database_schema.py
#    Reason: Generated code (migration file)
#    Recommendation: Test the migration logic separately
#
# 2. src/data/constants.py
#    Reason: No testable code (only constants)
#    Recommendation: No action needed
```

### Sample Projects

See `examples/` directory for complete sample projects:
- `examples/python-calculator/` - Simple Python calculator with pytest
- `examples/javascript-calculator/` - JavaScript calculator with Jest
- `examples/typescript-api/` - TypeScript API with Jest
- `examples/java-string-utils/` - Java utilities with JUnit 5

---

## Using on External Projects

Want to use this plugin on your own projects?

**See [USER_GUIDE.md](../USER_GUIDE.md) for comprehensive instructions including**:
- How to set up the plugin for your project structure (7 languages)
- Workflows for different scenarios (new features, legacy code, improving coverage)
- Best practices and tips
- Real-world examples (e-commerce, APIs, data pipelines)
- Troubleshooting common issues
- FAQ

**Quick summary for external projects**:

```bash
# 1. Navigate to your project
cd /path/to/your/project

# 2. Ensure testing framework is installed
# Python: pip install pytest
# JavaScript: npm install jest (or vitest, mocha)
# Java: Ensure Maven/Gradle with JUnit
# C#: Ensure .NET CLI with xUnit/NUnit/MSTest
# Go: Built-in (no installation needed)
# C++: Ensure CMake with Google Test or Catch2

# 3. Analyze your code
/test-analyze src/

# 4. Generate tests
/test-generate src/your_module.*  # Automated
# OR
/test-loop src/your_module.*      # Interactive with approval gates

# 5. Tests are generated in standard locations:
# - Python: tests/
# - JavaScript/TypeScript: __tests__/ or tests/
# - Java: src/test/java/
# - C#: Tests/ or {ProjectName}.Tests/
# - Go: *_test.go alongside source
# - C++: tests/
```

---

## Documentation

- **[INSTALLATION.md](../INSTALLATION.md)** - Complete installation guide with troubleshooting
- **[USER_GUIDE.md](../USER_GUIDE.md)** - Comprehensive guide for using on your own projects
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes
- **[.sdd/PHASE_COMPLETION_AUDIT.md](../.sdd/PHASE_COMPLETION_AUDIT.md)** - Complete implementation validation
- **[examples/](../examples/)** - Sample projects for all supported languages

---

## Contributing

This plugin is built using Spec-Driven Development (SDD):
- **Specification**: `.sdd/specs/` - Feature specifications
- **Technical Plans**: `.sdd/plans/` - Implementation plans
- **Task Breakdowns**: `.sdd/tasks/` - Detailed task lists
- **Progress Tracking**: `.sdd/progress/` - Implementation progress

---

## Support

- **Issues**: [GitHub Issues](https://github.example.com/my-org/my-plugin/issues)
- **Documentation**: See `.sdd/` directory for complete specifications
- **User Guide**: `USER_GUIDE.md` for comprehensive usage instructions

---

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for complete version history and detailed release notes.

---

## License

MIT License - See LICENSE file for details

---

**Built with**: Claude Code
**Inspired by**: [Dante Testing Framework](https://github.example.com/my-org/my-plugin)
**Maintained by**: My Org Team
