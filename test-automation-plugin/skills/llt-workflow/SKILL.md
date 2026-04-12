---
name: llt-workflow
description: Orchestrate end-to-end LowLevelTest workflows by chaining discovery, build, execution, and reporting steps
version: 1.0.0
category: LowLevelTests Orchestration
user-invocable: true
---

# llt-workflow: End-to-End Test Orchestration

**Version**: 1.0.0
**Category**: LowLevelTests Orchestration
**Purpose**: Chain llt-find, llt-build, llt-run, and llt-parse skills into complete test workflows

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.

---

## Overview

Provides automated test workflows for Unreal Engine's LowLevelTest framework. Orchestrates multiple skills to provide complete test automation with HTML reporting.

---

## Workflow Modes

| Mode | Pipeline | Best For |
|------|----------|----------|
| `full-suite` | Discover all -> build all -> run all -> parse -> report | Comprehensive validation, nightly CI |
| `target` | Validate target -> build -> run -> parse -> report | Focused testing, iterative development |
| `changes` | Find tests for changes -> build -> run -> parse -> report | Pre-commit validation, code review |

---

## Input Parameters

### Required (all modes)

| Parameter | Description |
|-----------|-------------|
| `workflow` | Workflow mode: `full-suite`, `target`, or `changes` |
| `project_root` | Path to UE project root directory |
| `platform` | Target platform (Win64, PS5, Mac, Linux, etc.) |

### Workflow-Specific

| Parameter | Applies To | Description |
|-----------|------------|-------------|
| `target` | `target` | Test target name (required for target mode) |
| `tags` | `target` | Catch2 tag filter (e.g., `[Core]`, `[!Slow]`) |
| `timeout` | `target` | Execution timeout in seconds (default: 600) |
| `files` | `changes` | List of changed source files (required for changes mode) |
| `include_transitive` | `changes` | Include transitive test dependencies |
| `test_type` | `full-suite` | Test type: `all` (default), `explicit`, `implicit` |

### Report Options

| Parameter | Description |
|-----------|-------------|
| `report_dir` | Directory for HTML reports (default: `./llt-reports`) |
| `report_name` | Custom report filename |
| `report_only` | Generate report from previous results (skip execution) |

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "workflow_type": "single-target",
  "status": "success",
  "total_duration_seconds": 245.67,
  "tests_discovered": 1,
  "tests_built": 1,
  "tests_executed": 42,
  "tests_passed": 40,
  "tests_failed": 2,
  "steps": [
    {
      "name": "Validate Target",
      "skill": "llt-find",
      "status": "completed",
      "duration_seconds": 1.23,
      "error": null,
      "warnings": []
    }
  ],
  "report_path": "./llt-reports/llt-workflow-single-target-20260218-120000.html",
  "errors": [],
  "warnings": []
}
```

---

## Orchestration Algorithm

### Workflow: Full Suite

1. **Discover Tests** (invoke `llt-find`):
   - Pass `project_root`, `test_type`, `platform`
   - Extract `total_targets` from statistics
   - On failure: stop workflow, return error

2. **Build All Targets** (invoke `llt-build` for each target):
   - For each discovered test target, build with the specified platform
   - Track build successes and failures

3. **Run All Tests** (invoke `llt-run` for each built target):
   - Execute each built test target
   - Collect XML output paths for parsing

4. **Parse Results** (invoke `llt-parse` for each run):
   - Parse XML reports and/or console logs
   - Aggregate results across all targets

5. **Generate HTML Report** (see Report Generation below)

### Workflow: Single Target

1. **Validate Target** (invoke `llt-find`):
   - Discover all targets and verify the specified target exists
   - On not found: stop workflow, return error

2. **Build Target** (invoke `llt-build`):
   - Build the specified target for the specified platform
   - If build returns `action: "execute_command"`, the agent must execute the command via Bash

3. **Run Tests** (invoke `llt-run`):
   - Execute the built test with optional tag filters and timeout
   - Collect XML output path

4. **Parse Results** (invoke `llt-parse`):
   - Parse execution output

5. **Generate HTML Report**

### Workflow: Change-Based

1. **Find Tests for Changes** (invoke `llt-find-for-changes`):
   - Pass `project_root` and `files` list
   - Optionally include transitive dependencies
   - Collect direct test files and transitive test modules

2. **Build Affected Tests** (invoke `llt-build` for each discovered test):
   - Build each test module identified by the change analysis

3. **Run Affected Tests** (invoke `llt-run` for each built test):
   - Execute discovered tests

4. **Parse Results** (invoke `llt-parse`):
   - Parse all results

5. **Generate HTML Report**

### Step Execution Pattern

Each workflow step follows this pattern:
1. Create a step record: `{name, skill, command, status: "pending"}`
2. Set status to `"running"`, record start time
3. Invoke the skill and capture JSON output
4. On success: set status to `"completed"`, store result
5. On failure: set status to `"failed"`, store error message
6. Record end time, calculate duration

### Result Aggregation

After all steps complete:
- `status`: `"success"` if all steps completed, `"partial_success"` if some failed, `"failed"` if critical step failed
- `tests_discovered`: count from discovery step
- `tests_built`: count from build step
- `tests_executed`, `tests_passed`, `tests_failed`: from parse step statistics
- `total_duration_seconds`: wall clock time from workflow start to end

---

## HTML Report Generation

Generate an HTML report with:

1. **Header**: Title, generation timestamp
2. **Workflow Summary**: Status badge, metric cards for discovered/built/executed/passed/failed counts, pass rate, duration
3. **Step Timeline**: Numbered steps with status badges, durations, and any warnings/errors
4. **Test Results Table**: Test name, status (color-coded), duration
5. **Failure Details**: For each failed test, show test name, file:line location, assertion expression, and expansion message
6. **Footer**: Skill version

Report filename: `llt-workflow-{workflow_type}-{YYYYMMDD-HHMMSS}.html`
Default output directory: `./llt-reports/`

The report uses self-contained CSS (no external dependencies). Use proper HTML escaping for all dynamic content.

---

## Error Handling

1. **Step Failure**: Workflow stops at failing step and returns partial results
2. **Build Failure**: Errors captured and included in report
3. **Test Failures**: Do NOT stop the workflow -- results are aggregated normally
4. **Parse Failure**: Falls back to console log parsing if XML unavailable
5. **Report Failure**: Workflow continues even if report generation fails (logged as warning)

---

## Limitations

1. Builds and runs targets sequentially (no parallel execution)
2. Some platforms require manual SDK setup
3. No incremental/cached build support
4. No distributed test execution
