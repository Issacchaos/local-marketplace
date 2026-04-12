# LLT Generate - Manual Validation Test Plan

## Overview

This document provides manual validation test cases for the llt-generate skill (TASK-015). Each test case should be run manually to verify correct behavior across all modes.

## Prerequisites

- Unreal Engine project with test modules
- dante plugin installed and configured
- llt-find, llt-build, llt-run skills available
- Compilation database generated (optional, for clang AST parsing)

## Test Environment Setup

```bash
# Navigate to test project
cd /path/to/fortnite/project

# Verify dante plugin loaded
claude --version

# Generate compilation database (optional, for accurate parsing)
# Use Algorithm: Generate Compilation Database from SKILL.md
TARGET="FortniteEditor"
# Execute steps: detect platform, detect project root, run ushell command
```

## Test Case 1: Scaffold Mode - Complete Module Generation

**Objective**: Verify scaffold mode generates complete test module structure.

**Test Steps**:
```bash
/llt-generate --module CommChannelsRuntime --scaffold
```

**Expected Output**:
```json
{
  "status": "success",
  "generated_files": [
    {
      "path": "/path/to/Plugins/CommChannels/Tests/CommChannelsTests/CommChannelsTests.Build.cs",
      "type": "build_config",
      "test_count": 0,
      "line_count": 25,
      "template_used": "ue-test-build-cs-template.md"
    },
    {
      "path": "/path/to/Plugins/CommChannels/Tests/CommChannelsTests/CommChannelsTests.Target.cs",
      "type": "target_config",
      "test_count": 0,
      "line_count": 15,
      "template_used": "ue-test-target-cs-template.md"
    },
    {
      "path": "/path/to/Plugins/CommChannels/Tests/CommChannelsTests/Private/CommChannelsTests.cpp",
      "type": "test_source",
      "test_count": 1,
      "line_count": 50,
      "template_used": "cpp-basic-fixture-llt-template.md"
    }
  ],
  "validation": {
    "compilation": "not_attempted",
    "execution": "not_attempted"
  },
  "metadata": {
    "template_used": "cpp-basic-fixture-llt-template.md",
    "pattern_detected": "basic",
    "generation_time_ms": 1250
  }
}
```

**Verification**:
- [ ] 3 files generated (.Build.cs, .Target.cs, .cpp)
- [ ] Directory structure created: `Tests/CommChannelsTests/Private/`
- [ ] .Build.cs inherits from TestModuleRules
- [ ] .Target.cs inherits from TestTargetRules
- [ ] Test file contains copyright header
- [ ] Test file compiles successfully (manual check: run llt-build)
- [ ] Generation completes in <3 seconds

**Success Criteria**: All files created with correct structure, compilation succeeds.

---

## Test Case 2: Interactive Mode - Default Behavior

**Objective**: Verify interactive mode prompts at each step.

**Test Steps**:
```bash
/llt-generate --file CommChannelNode.h
```

**Expected Prompts**:
```
Step 1: Analyze source file
  > Found class: FCommChannelNode
  > Found 5 methods: ConnectTo, IsConnectedTo, SetChannelValue, GetChannelValue, GetChannelId
  > Continue? (y/n)

[User types: y]

Step 2: Select template
  > Detected pattern: Basic/Fixture
  > Template: cpp-basic-fixture-llt-template.md
  > Override? (y/n to accept, or provide template name)

[User types: y]

Step 3: Generate tests
  > Generate tests for 5 methods? (y/n, or provide method filter)

[User types: y]

Step 4: Build tests
  > Build CommChannelsTests module? (y/n)

[User types: n]

Step 5: Run tests
  > Run CommChannelsTests? (y/n)

[User types: n]

Generation Summary
================================================================================
Status: success
Generated files: 1
  - /path/to/CommChannelsTests.cpp (5 tests)
Template: cpp-basic-fixture-llt-template.md
Pattern: basic
================================================================================
```

**Verification**:
- [ ] 5 prompts displayed in sequence
- [ ] Clear feedback at each step
- [ ] User can accept defaults with 'y'
- [ ] User can override with custom values
- [ ] User can skip optional steps (build, run) with 'n'
- [ ] Final summary displayed
- [ ] Test file generated with 5 test cases

**Success Criteria**: Interactive prompts work correctly, user has control at each step.

---

## Test Case 3: Autonomous Mode - Auto Build and Run

**Objective**: Verify autonomous mode runs without prompts and executes full workflow.

**Test Steps**:
```bash
/llt-generate --module CommChannelsRuntime --build --run --no-interactive
```

**Expected Output**:
```
Detecting pattern for CommChannelsRuntime...
Detected pattern: basic
Template: cpp-basic-fixture-llt-template.md
Generating test files...
Generated: /path/to/CommChannelsTests.cpp
Building test module...
Build completed in 45.2s
Running tests...
Tests completed: 5 passed, 0 failed

Generation Summary
================================================================================
Status: success
Generated files: 1
  - /path/to/CommChannelsTests.cpp (5 tests)
Template: cpp-basic-fixture-llt-template.md
Pattern: basic
Build: success
Tests: 5 passed, 0 failed
================================================================================
```

**Expected JSON Output**:
```json
{
  "status": "success",
  "generated_files": [...],
  "validation": {
    "compilation": "success",
    "execution": "success",
    "test_results": {
      "passed": 5,
      "failed": 0,
      "skipped": 0
    }
  },
  "progress_log": [
    "Detected pattern: basic",
    "Template used: cpp-basic-fixture-llt-template.md",
    "Generated 1 files",
    "Build: success (45.2s)",
    "Tests: 5 passed, 0 failed"
  ]
}
```

**Verification**:
- [ ] No interactive prompts displayed
- [ ] Test file generated
- [ ] Build invoked automatically
- [ ] Tests run automatically
- [ ] Validation includes compilation and execution status
- [ ] Test results accurate (5 passed, 0 failed)
- [ ] Full workflow completes successfully

**Success Criteria**: Autonomous mode runs without user interaction, reports complete results.

---

## Test Case 4: Async Template Detection

**Objective**: Verify automatic detection of async pattern.

**Test Steps**:
```bash
# Use a file with async patterns (FHttpModule, callbacks, tick loops)
/llt-generate --file WebSocketClient.h
```

**Expected Detection**:
```
Detected pattern: async
Template: cpp-async-llt-template.md
```

**Verification**:
- [ ] Pattern detected as "async"
- [ ] Template selected: `cpp-async-llt-template.md`
- [ ] Generated test includes tick loop fixture
- [ ] Generated test includes callback completion pattern
- [ ] Test compiles successfully

**Success Criteria**: Async pattern detected correctly, appropriate template used.

---

## Test Case 5: Plugin/Lifecycle Template Detection

**Objective**: Verify detection of plugin/lifecycle pattern.

**Test Steps**:
```bash
# Use a module with bCompileAgainstEngine=true
/llt-generate --module FNOnlineFramework --scaffold
```

**Expected Detection**:
```
Detected pattern: plugin
Template: cpp-plugin-lifecycle-llt-template.md
```

**Verification**:
- [ ] Pattern detected as "plugin"
- [ ] Template selected: `cpp-plugin-lifecycle-llt-template.md`
- [ ] .Build.cs includes `bCompileAgainstEngine = true`
- [ ] .Build.cs includes `bMockEngineDefaults = true`
- [ ] Generated test includes complex fixture
- [ ] Test compiles successfully

**Success Criteria**: Plugin pattern detected correctly, engine flags set.

---

## Test Case 6: Mock Template Detection

**Objective**: Verify detection of mock pattern.

**Test Steps**:
```bash
# Use a file with mock interface patterns
/llt-generate --file MockAuthService.h
```

**Expected Detection**:
```
Detected pattern: mock
Template: cpp-mock-llt-template.md
```

**Verification**:
- [ ] Pattern detected as "mock"
- [ ] Template selected: `cpp-mock-llt-template.md`
- [ ] Generated test includes mock interface definition
- [ ] Generated test includes mock implementation
- [ ] Generated test includes error injection methods
- [ ] Test compiles successfully

**Success Criteria**: Mock pattern detected correctly, DI patterns included.

---

## Test Case 7: Template Override

**Objective**: Verify manual template override works.

**Test Steps**:
```bash
# Force async template even if basic pattern detected
/llt-generate --file SimpleClass.h --template cpp-async-llt-template
```

**Expected Output**:
```
Pattern detected: basic (overridden by user)
Template: cpp-async-llt-template.md
```

**Verification**:
- [ ] Pattern detection still runs (shows "basic")
- [ ] Template override applied ("cpp-async-llt-template.md")
- [ ] Generated test uses async template
- [ ] Warning logged about override

**Success Criteria**: Template override works, detection result shown but not used.

---

## Test Case 8: Class Filtering

**Objective**: Verify class filtering works correctly.

**Test Steps**:
```bash
# Filter to specific class
/llt-generate --file MultiClassFile.h --class FChannelNode
```

**Expected Output**:
```
Found 2 classes: FChannelNode, FChannelManager
Filtering to class: FChannelNode
Found 3 methods in FChannelNode
Generating tests for 3 methods...
```

**Verification**:
- [ ] Only methods from FChannelNode included
- [ ] Methods from other classes excluded
- [ ] Test count matches filtered methods
- [ ] Generated tests reference correct class

**Success Criteria**: Only specified class methods included in generated tests.

---

## Test Case 9: Method Filtering

**Objective**: Verify method filtering works correctly.

**Test Steps**:
```bash
# Filter to specific methods
/llt-generate --file CommChannelNode.h --method ConnectTo,IsConnectedTo
```

**Expected Output**:
```
Found 5 methods: ConnectTo, IsConnectedTo, SetChannelValue, GetChannelValue, GetChannelId
Filtering to methods: ConnectTo, IsConnectedTo
Generating tests for 2 methods...
```

**Verification**:
- [ ] Only 2 test cases generated (ConnectTo, IsConnectedTo)
- [ ] Other methods excluded
- [ ] Test names match specified methods

**Success Criteria**: Only specified methods included in generated tests.

---

## Test Case 10: Metadata-Driven Generation

**Objective**: Verify llt-find integration generates stubs for coverage gaps.

**Test Steps**:
```bash
# First, run llt-find
/llt-find --module CommChannelsRuntime --output coverage.json

# Then generate stubs
/llt-generate --file CommChannelNode.h --metadata coverage.json
```

**Expected Output**:
```
Parsing llt-find metadata...
Found 5 source methods
Found 2 tested methods: ConnectTo, IsConnectedTo
Identified 3 untested methods: SetChannelValue, GetChannelValue, GetChannelId
Generating test stubs for 3 methods...
```

**Verification**:
- [ ] coverage.json parsed successfully
- [ ] Tested methods identified from metadata
- [ ] Untested methods calculated correctly
- [ ] 3 test stubs generated
- [ ] Stubs have TODO comments for manual completion

**Success Criteria**: Coverage gaps identified, stubs generated for untested methods.

---

## Test Case 11: Compilation Database Integration

**Objective**: Verify clang AST parsing with compilation database.

**Test Steps**:
```bash
# Generate compilation database first using SKILL.md algorithm
TARGET="FortniteEditor"
# Execute Algorithm: Generate Compilation Database steps

# Use it for accurate parsing
/llt-generate --file ComplexTemplate.h --compdb compile_commands.json
```

**Expected Output**:
```
Using compilation database: /path/to/compile_commands.json
Parsing with clang AST (100% accuracy)...
Extracted 10 methods with full signatures and mangled names
```

**Verification**:
- [ ] Compilation database found and loaded
- [ ] Clang AST parsing used (not regex)
- [ ] All methods extracted accurately (including templates)
- [ ] Mangled names included in metadata
- [ ] Complex C++ syntax handled correctly

**Success Criteria**: Clang parsing works, 100% accuracy achieved.

---

## Test Case 12: Regex Fallback

**Objective**: Verify regex fallback when clang unavailable.

**Test Steps**:
```bash
# Disable clang (rename libclang or use environment without it)
/llt-generate --file SimpleClass.h
```

**Expected Output**:
```
WARNING: Compilation database not found. Using regex fallback (95% accuracy).
Parsing with regex...
Extracted 5 methods with basic signatures
```

**Verification**:
- [ ] Warning displayed about fallback
- [ ] Regex parsing used
- [ ] Most methods extracted (95% accuracy)
- [ ] Generation continues successfully
- [ ] Edge cases may have TODOs

**Success Criteria**: Regex fallback works, warning shown, generation continues.

---

## Test Case 13: Build Failure Handling

**Objective**: Verify graceful handling of build failures.

**Test Steps**:
```bash
# Generate tests with intentional error (e.g., invalid include)
# Manually edit generated file to add syntax error
/llt-generate --file BrokenClass.h --build
```

**Expected Output**:
```
Generating test files...
Building test module...
Build failed with exit code 1
stderr: error C2039: 'NonExistentMethod': is not a member of 'FBrokenClass'

Generation Summary
================================================================================
Status: failed
Build: failed
Error: Build compilation failed. See stderr for details.
================================================================================
```

**Expected JSON Output**:
```json
{
  "status": "failed",
  "validation": {
    "compilation": "failed",
    "execution": "not_attempted"
  },
  "error": "Build compilation failed. See stderr for details."
}
```

**Verification**:
- [ ] Build invoked
- [ ] Build failure detected
- [ ] Error message displayed with details
- [ ] Generation marked as failed
- [ ] Tests not run (execution: "not_attempted")
- [ ] Clear error guidance provided

**Success Criteria**: Build failure handled gracefully, clear error reported.

---

## Test Case 14: Test Execution Failure Handling

**Objective**: Verify graceful handling of test execution failures.

**Test Steps**:
```bash
# Generate tests with intentional assertion failures
# Manually edit to add REQUIRE(false)
/llt-generate --file FailingTests.h --build --run
```

**Expected Output**:
```
Building test module...
Build completed in 30.5s
Running tests...
Tests completed: 2 passed, 3 failed

Generation Summary
================================================================================
Status: success (with test failures)
Build: success
Tests: 2 passed, 3 failed
================================================================================
```

**Expected JSON Output**:
```json
{
  "status": "success",
  "validation": {
    "compilation": "success",
    "execution": "success",
    "test_results": {
      "passed": 2,
      "failed": 3,
      "skipped": 0
    }
  }
}
```

**Verification**:
- [ ] Build succeeds
- [ ] Tests run
- [ ] Test failures detected
- [ ] Accurate test counts (2 passed, 3 failed)
- [ ] Status still "success" (generation succeeded)
- [ ] Test results included in validation

**Success Criteria**: Test failures detected, accurate counts reported.

---

## Test Case 15: Invalid Module Handling

**Objective**: Verify clear error for non-existent module.

**Test Steps**:
```bash
/llt-generate --module NonExistentModule --scaffold
```

**Expected Output**:
```
ERROR: Module NonExistentModule not found
Searched in:
  - Plugins/NonExistentModule/Source/NonExistentModule/
  - Source/Runtime/NonExistentModule/
  - Source/NonExistentModule/
```

**Expected JSON Output**:
```json
{
  "status": "failed",
  "error": "Module NonExistentModule not found. Searched in: [paths]"
}
```

**Verification**:
- [ ] Error message displayed
- [ ] Search paths listed
- [ ] No files generated
- [ ] Clear guidance for resolution

**Success Criteria**: Clear error message, no partial generation.

---

## Test Case 16: Invalid Template Handling

**Objective**: Verify clear error for non-existent template.

**Test Steps**:
```bash
/llt-generate --file SimpleClass.h --template invalid-template
```

**Expected Output**:
```
ERROR: Template invalid-template not found
Available templates:
  - cpp-basic-fixture-llt-template.md
  - cpp-async-llt-template.md
  - cpp-plugin-lifecycle-llt-template.md
  - cpp-mock-llt-template.md
```

**Expected JSON Output**:
```json
{
  "status": "failed",
  "error": "Template invalid-template not found. Available: [list]"
}
```

**Verification**:
- [ ] Error message displayed
- [ ] Available templates listed
- [ ] No files generated
- [ ] Clear guidance for resolution

**Success Criteria**: Clear error message, available options shown.

---

## Test Case 17: All Modes with All Templates

**Objective**: Verify each mode works with each template (comprehensive matrix test).

**Test Matrix**:

| Mode | Template | Test |
|------|----------|------|
| Scaffold | Basic/Fixture | `--module X --scaffold` |
| Scaffold | Async | `--module Y --scaffold --framework async` |
| Scaffold | Plugin | `--module Z --scaffold --framework plugin` |
| Scaffold | Mock | `--module W --scaffold --framework mock` |
| Interactive | Basic/Fixture | `--file A.h` |
| Interactive | Async | `--file B.h --template cpp-async` |
| Interactive | Plugin | `--file C.h --template cpp-plugin` |
| Interactive | Mock | `--file D.h --template cpp-mock` |
| Autonomous | Basic/Fixture | `--module X --build --run --no-interactive` |
| Autonomous | Async | `--module Y --build --run --no-interactive --framework async` |
| Autonomous | Plugin | `--module Z --build --run --no-interactive --framework plugin` |
| Autonomous | Mock | `--module W --build --run --no-interactive --framework mock` |

**Success Criteria**: All 12 combinations work correctly.

---

## Test Case 18: Performance Verification

**Objective**: Verify performance meets targets.

**Test Steps**:
```bash
# Time scaffold mode
time /llt-generate --module LargeModule --scaffold

# Time metadata-driven generation
time /llt-generate --file LargeClass.h --metadata coverage.json

# Time clang parsing
time /llt-generate --file ComplexTemplate.h --compdb compile_commands.json

# Time regex parsing
time /llt-generate --file SimpleClass.h
```

**Performance Targets**:
- [ ] Scaffold mode: <3 seconds
- [ ] Metadata-driven: <1 second
- [ ] Clang parsing (cold): <5 seconds
- [ ] Clang parsing (cached): <100ms
- [ ] Regex parsing: <500ms

**Success Criteria**: All operations meet performance targets.

---

## Summary Report

After completing all test cases, generate a summary report:

```markdown
# LLT Generate Validation Report

**Date**: 2026-02-18
**Tester**: [Your Name]
**Environment**: [Project Name, Platform, UE Version]

## Test Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-01: Scaffold Mode | PASS/FAIL | |
| TC-02: Interactive Mode | PASS/FAIL | |
| TC-03: Autonomous Mode | PASS/FAIL | |
| TC-04: Async Detection | PASS/FAIL | |
| TC-05: Plugin Detection | PASS/FAIL | |
| TC-06: Mock Detection | PASS/FAIL | |
| TC-07: Template Override | PASS/FAIL | |
| TC-08: Class Filtering | PASS/FAIL | |
| TC-09: Method Filtering | PASS/FAIL | |
| TC-10: Metadata-Driven | PASS/FAIL | |
| TC-11: Clang AST Parsing | PASS/FAIL | |
| TC-12: Regex Fallback | PASS/FAIL | |
| TC-13: Build Failure | PASS/FAIL | |
| TC-14: Test Failure | PASS/FAIL | |
| TC-15: Invalid Module | PASS/FAIL | |
| TC-16: Invalid Template | PASS/FAIL | |
| TC-17: Mode x Template Matrix | PASS/FAIL | |
| TC-18: Performance | PASS/FAIL | |

**Pass Rate**: X/18 (XX%)

## Issues Found

1. [Issue description]
2. [Issue description]

## Recommendations

1. [Recommendation]
2. [Recommendation]

## Conclusion

[Overall assessment of skill readiness for production]
```

---

## Automated Testing (Future)

The following automated tests should be implemented in the future:

```bash
# Run unit tests
pytest skills/llt-generate/tests/

# Run integration tests
pytest skills/llt-generate/tests/integration/

# Run end-to-end tests
pytest skills/llt-generate/tests/e2e/
```

Suggested test coverage:
- Unit tests: Pattern detection, template rendering, module analysis
- Integration tests: File generation, build integration, run integration
- E2E tests: Full workflows (scaffold, interactive, autonomous)

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-18
**Status**: Ready for validation
