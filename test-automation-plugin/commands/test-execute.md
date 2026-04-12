---
description: "Execute existing tests and report structured results"
argument-hint: "[options] [path]"
allowed-tools: Skill(test-engineering:framework-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:project-detection), Skill(test-engineering:e2e), Skill(test-engineering:build-integration), Skill(test-engineering:model-selection), Skill(test-engineering:llt-run), Skill(test-engineering:llt-build), Skill(test-engineering:llt-parse)
---

# /test-execute Command

**Description**: Execute existing tests and report structured results

**Usage**:
```
/test-execute [options] [path]
```

**Arguments**:
- `path` (optional): File, directory, or test pattern to execute. Defaults to workspace root if not specified.

**Options**:
- `--type <unit|integration|e2e>` (optional): Type of tests to execute. Determines timeout and execution behavior. When omitted, type is inferred from framework detection.
- `--verbose` (boolean, default: false): Include full stack traces and per-test timing in the output.
- `--validate` (boolean, default: false): Run the validate-agent on results to provide failure categorization and root cause analysis.
- `--coverage` (boolean, default: false): Enable coverage collection (appends the appropriate coverage flags for the detected framework).
- `--framework <name>` (optional): Override auto-detection when you know your framework or detection fails.
- `--validate-model <opus|sonnet|haiku>` (optional): Override the model used for the validate-agent when `--validate` is enabled.
- `--help, -h`: Display help information

**Examples**:
```bash
# Execute all tests in workspace
/test-execute

# Execute tests in specific directory
/test-execute tests/

# Execute a single test file
/test-execute tests/test_user_service.py

# Execute unit tests with verbose output
/test-execute --type unit --verbose src/

# Execute tests with coverage collection
/test-execute --coverage

# Execute and validate failures with root cause analysis
/test-execute --validate

# Execute with framework override when detection fails
/test-execute --framework jest

# Execute e2e tests (5-minute timeout, pre-flight checks)
/test-execute --type e2e

# Combine flags: coverage + verbose + validate
/test-execute --verbose --coverage --validate --type unit tests/
```

---

## Command Behavior

This command provides **lightweight, standalone test execution** for existing test suites. It does not generate, write, or modify test files.

**Workflow Phases** (without `--validate`):
1. **Detect** → Identify testing framework and construct test command
2. **Execute** → Run existing tests and capture output
3. **Results** → Parse and display structured results

**Workflow Phases** (with `--validate`):
1. **Detect** → Identify testing framework and construct test command
2. **Execute** → Run existing tests and capture output
3. **Validate** → Categorize failures and perform root cause analysis
4. **Results** → Display structured results with validation

**Key Characteristics**:
- Executes EXISTING tests — does not generate new ones
- Single-pass execution — no iteration loops or approval gates
- Structured output — pass/fail/skip counts, per-failure details, coverage
- Optional validation — use `--validate` for failure categorization
- Use `/test-generate` to create new tests
- Use `/test-loop` for iterative test generation with approval gates

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/test-execute` command for lightweight, standalone test execution.

## Your Task

Execute the existing test suite at the specified path and report structured results. This command does NOT generate, write, or modify test files — it only runs existing tests and parses the output.

### Step 1: Parse Arguments and Validate (SECURITY CRITICAL)

**Check for help flag first**:
```javascript
// Check for --help or -h before any other processing
const rawArgs = userInput.trim();
if (rawArgs.includes('--help') || rawArgs.includes('-h')) {
    // Display help text immediately and STOP
    displayHelpText();
    return;
}
```

**Help text to display**:
```
/test-execute - Execute existing tests and report structured results

USAGE:
  /test-execute [options] [path]

ARGUMENTS:
  path    Optional. File, directory, or test pattern to execute.
          Defaults to workspace root.

OPTIONS:
  --type <type>              Type of tests to execute: unit, integration, e2e
                             Determines timeout (2 min for unit/integration,
                             5 min for e2e) and execution behavior.
                             When omitted, inferred from framework detection.
  --verbose                  Include full stack traces and per-test timing in
                             the output. Default: truncate traces to 5 lines.
  --validate                 Run the validate-agent on results to provide
                             failure categorization and root cause analysis.
                             Only invoked when failures exist. (opt-in)
  --coverage                 Enable coverage collection. Appends the
                             appropriate coverage flags for the detected
                             framework (e.g., --cov for pytest, --coverage
                             for Jest). Coverage data displayed when available.
  --framework <name>         Override auto-detection. Use when detection fails
                             or you know the framework. Supported: pytest,
                             jest, junit, playwright, cypress, unittest, xunit,
                             go-test, gtest, catch2, cargo-test, rspec, unity
  --validate-model <model>   Override model for validate-agent when --validate
                             is enabled. Options: opus, sonnet, haiku.
                             Default: uses configured model from .dante.yml.
  --help, -h                 Show this help message

EXAMPLES:
  /test-execute                              # Execute all tests in workspace
  /test-execute tests/                       # Execute tests in directory
  /test-execute tests/test_user.py           # Execute single test file
  /test-execute --type unit --verbose        # Unit tests with full traces
  /test-execute --coverage                   # Execute with coverage collection
  /test-execute --validate                   # Execute and categorize failures
  /test-execute --framework jest             # Override framework detection
  /test-execute --type e2e                   # E2E tests (5-min timeout)
  /test-execute --validate --validate-model haiku  # Use haiku for validation
  /test-execute --verbose --coverage --validate tests/  # Combined flags

DESCRIPTION:
  Lightweight, single-pass test execution for existing test suites.
  Does NOT generate, write, or modify test files.

  Framework is auto-detected from project configuration files
  (pytest.ini, package.json, *.csproj, go.mod, etc.). Use --framework
  to override when detection fails or confidence is low.

  Without --validate: 3 phases (detect, execute, results).
  With --validate: 4 phases (detect, execute, validate, results).
  Validation is only invoked when failures exist (skipped on full pass).

OUTPUT:
  - Pass/fail/skip counts and duration
  - Per-failure details: test name, file, line, error message, stack trace
  - Coverage percentage and per-file breakdown (when --coverage used)
  - Failure categorization (when --validate used)
  - Saved report: .claude/.last-execution.md

TIMEOUT:
  unit/integration tests: 2 minutes (120,000ms)
  e2e tests:              5 minutes (300,000ms)

SEE ALSO:
  /test-generate    Generate new tests for your codebase
  /test-loop        Iterative test generation with approval gates
  /test-resume      Resume an interrupted test-loop workflow
```

**Parse Arguments**:
```javascript
// Extract arguments from user command
const args = parseCommandArgs(userInput);

// Positional argument: path
const targetPath = args.path || getWorkspaceRoot();

// Boolean flags
const verbose  = args['verbose']  === true || args.verbose  === true;
const validate = args['validate'] === true || args.validate === true;
const coverage = args['coverage'] === true || args.coverage === true;

// String arguments
const testType      = args['type']           || null; // null = infer from detection
const framework     = args['framework']      || null; // null = auto-detect
const validateModel = args['validate-model'] || null; // null = use configured default

// Unknown flag detection
const KNOWN_FLAGS = new Set([
    'type', 'verbose', 'validate', 'coverage',
    'framework', 'validate-model', 'help', 'h'
]);
const unknownFlags = Object.keys(args).filter(k => k !== 'path' && !KNOWN_FLAGS.has(k));
```

**Validate Unknown Flags**:
```javascript
if (unknownFlags.length > 0) {
    displayError(`
❌ Error: Unknown flag(s): ${unknownFlags.map(f => '--' + f).join(', ')}

These flags are not recognized by /test-execute.

Run /test-execute --help to see all available options.
`);
    return; // STOP
}
```

**Validate --type**:
```javascript
const VALID_TYPES = ['unit', 'integration', 'e2e'];
if (testType !== null && !VALID_TYPES.includes(testType.toLowerCase())) {
    displayError(`
❌ Error: Invalid test type

Test type must be one of: unit, integration, e2e

You provided: --type ${testType}

Example: /test-execute --type unit tests/
`);
    return; // STOP
}
const normalizedType = testType ? testType.toLowerCase() : null;
```

**Validate --validate-model**:
```javascript
const VALID_MODELS = ['opus', 'sonnet', 'haiku'];
if (validateModel !== null && !VALID_MODELS.includes(validateModel.toLowerCase())) {
    displayError(`
❌ Error: Invalid validate model

Model must be one of: opus, sonnet, haiku

You provided: --validate-model ${validateModel}

Example: /test-execute --validate --validate-model haiku
`);
    return; // STOP
}
const normalizedValidateModel = validateModel ? validateModel.toLowerCase() : null;
```

**Path Validation (SECURITY REQUIREMENTS)**:
```javascript
// Step 1: Remove null bytes (prevent null byte injection)
let resolvedPath = targetPath.replace(/\0/g, '');

// Step 2: Check path length (max 4096 characters)
if (resolvedPath.length > 4096) {
    displayError(`
❌ Error: Path too long

The specified path exceeds the maximum allowed length of 4096 characters.

Suggestions:
- Use a shorter path
- Navigate to a parent directory and use a relative path
`);
    return; // STOP
}

// Step 3: Resolve to absolute path
resolvedPath = path.resolve(getWorkspaceRoot(), resolvedPath);

// Step 4: Workspace boundary check (prevent directory traversal)
const workspaceRoot = getWorkspaceRoot();
if (!resolvedPath.startsWith(workspaceRoot)) {
    displayError(`
❌ Error: Path outside workspace

The specified path is outside the workspace boundary:
  Path:      ${resolvedPath}
  Workspace: ${workspaceRoot}

For security reasons, /test-execute cannot access paths outside the
current workspace. Use a path within: ${workspaceRoot}
`);
    return; // STOP
}

// Step 5: Check path existence
const pathExists = glob(resolvedPath, { limit: 1 }).length > 0
                || bash(`ls "${resolvedPath}" 2>/dev/null`).exitCode === 0;
if (!pathExists) {
    displayError(`
❌ Error: Path not found

The specified path does not exist: ${targetPath}

Suggestions:
- Check the path spelling
- Use relative paths from workspace root (${workspaceRoot})
- Run /test-execute to execute tests in the entire workspace
- Run /test-execute tests/ to target your test directory
`);
    return; // STOP
}
```

**Calculate Total Phase Count**:
```javascript
// Phase count is fixed at parse time based on --validate flag
// Without --validate: 3 phases (detect, execute, results)
// With --validate: 4 phases (detect, execute, validate, results)
const totalPhases = validate ? 4 : 3;
```

**Display Start Message**:
```markdown
## Starting Test Execution

**Target**: {resolvedPath}
**Test Type**: {normalizedType || 'auto-detect'}
**Mode**:
  - Coverage: {coverage ? 'enabled (--coverage)' : 'disabled'}
  - Verbose: {verbose ? 'enabled (--verbose)' : 'disabled'}
  - Validate: {validate ? 'enabled (--validate)' : 'disabled'}
{framework ? `**Framework Override**: ${framework}\n` : ''}
{normalizedValidateModel && validate ? `**Validate Model**: ${normalizedValidateModel}\n` : ''}
This will execute existing tests and report structured results.
Use /test-generate if you need to create new tests.

---
```

### Step 2: Phase 1 — Detect Test Framework

**Display Phase 1 Progress**:
```
[1/{totalPhases}] 🔍 Detecting test framework...
```

### Step 3: Invoke Execute-Agent (Phases 1 + 2)

The execute-agent handles both framework detection (Phase 1) and test execution (Phase 2) in a single Task call. Construct the prompt, set the timeout, and launch the agent.

**Calculate Timeout**:
```javascript
// REQ-F-15: 120,000ms for unit/integration; 300,000ms for E2E
const taskTimeout = (normalizedType === 'e2e') ? 300000 : 120000;
```

**Construct Execute-Agent Prompt**:
```javascript
// Build the prompt dynamically based on provided flags
let executePrompt = `
You are the Execute Agent for the /test-execute command.

## Execution Parameters

**Target Path**: ${resolvedPath}
**Iteration**: 0
**Modified Files**: []
**Test Type**: ${normalizedType || 'infer from detection'}
`;

if (framework) {
    executePrompt += `
**Framework Override**: ${framework}
IMPORTANT: The user has specified --framework ${framework}. Use this framework directly — skip auto-detection entirely. Do NOT run framework detection; proceed immediately to constructing the test command for ${framework}.
`;
} else {
    executePrompt += `
**Framework**: auto-detect (no override provided)
Run framework detection using skills/framework-detection/ to identify the testing framework. Report the detected framework name and confidence score.
`;
}

if (normalizedType === 'e2e') {
    executePrompt += `
**E2E Pre-Flight Checks Required** (REQ-F-16):
Before executing tests, perform E2E pre-flight checks:
1. Verify browser installation: check that the required browsers (Chromium, Firefox, WebKit) are installed. For Playwright: run \`npx playwright install --dry-run\` or check browser binary paths. For Cypress: verify Cypress binary is present.
2. Check application availability: if a base URL is configured (e.g., in playwright.config.ts, cypress.json), attempt a health check to confirm the app is reachable. If the app is not running, report this as a pre-flight failure with a clear message.
3. If pre-flight checks fail, report the failure with actionable suggestions and stop execution.
`;
}

if (coverage) {
    executePrompt += `
**Coverage Collection Enabled** (REQ-F-18):
Append the appropriate coverage flags for the detected framework:
- pytest: append \`--cov --cov-report=term-missing\`
- Jest/Vitest: append \`--coverage\`
- Go test: append \`-coverprofile=coverage.out\`
- cargo test: append \`-- --test-coverage\` (if tarpaulin configured)
- JUnit/Maven: append \`--coverage\` or use jacoco plugin
- Playwright: coverage is collected via istanbul if configured (no additional flag)
- Other frameworks: append the framework-appropriate coverage flag
Include coverage data in the execution report.
`;
}

executePrompt += `
## Your Mission

Read and follow the agent definition at \`agents/execute-agent.md\`.

1. ${framework ? `Use ${framework} framework (override provided — skip detection)` : 'Detect the test framework from project configuration files'}
2. Construct the appropriate test command targeting: ${resolvedPath}
3. Execute tests using the Bash tool
4. Capture stdout, stderr, and exit code
5. Parse results using framework-specific parsers from skills/result-parsing/
6. Extract: pass/fail/skip counts, duration, per-failure details (test name, file, line, error, stack trace)
7. Generate a structured execution report

## Required Output Format

Your report MUST include these labeled fields for result extraction:

Exit Code: <number>
Passed: <number>
Failed: <number>
Skipped: <number>
Duration: <number> seconds

## Execution Summary
<One-paragraph summary of the execution: framework detected, command run, overall outcome>

## Failure Details
<For each failure: test name, file path, line number, error message, stack trace>
`;
```

**Invoke Execute-Agent via Task Tool**:
```javascript
let executeAgentOutput = null;
let executeAgentError = null;
let timedOut = false;

try {
    executeAgentOutput = await Task({
        subagent_type: "test-engineering:execute-agent",
        description: `Execute tests at ${resolvedPath}`,
        prompt: executePrompt,
        timeout: taskTimeout
    });
} catch (err) {
    if (err.code === 'TIMEOUT' || err.message?.includes('timeout') || err.message?.includes('timed out')) {
        timedOut = true;
        executeAgentOutput = err.partialOutput || null; // Capture any partial output
    } else {
        executeAgentError = err;
    }
}
```

**Handle Timeout (REQ-F-30)**:
```javascript
if (timedOut) {
    const timeoutMinutes = taskTimeout / 60000;
    displayError(`
❌ Error: Test execution timed out

The test execution exceeded the configured timeout of ${taskTimeout}ms (${timeoutMinutes} minutes).

${normalizedType === 'e2e'
    ? 'E2E tests use a 5-minute timeout. If your test suite requires more time, consider:\n- Running a subset of tests with a targeted path\n- Increasing parallelism in your E2E framework configuration'
    : 'Unit/integration tests use a 2-minute timeout. If your test suite requires more time, consider:\n- Running a targeted subset: /test-execute tests/specific_module/\n- Using /test-execute --type e2e for longer-running suites'}

${executeAgentOutput ? '### Partial Results\n\nThe following partial output was captured before timeout:\n\n' + executeAgentOutput : 'No partial output was captured.'}
`);
    return; // STOP
}
```

**Handle Agent Infrastructure Failure**:
```javascript
if (executeAgentError) {
    displayError(`
❌ Error: Execute-agent failed

The execute-agent encountered an infrastructure error and could not complete execution.

Error: ${executeAgentError.message || 'Unknown error'}

Suggestions:
- Retry the command: /test-execute ${userInput.trim()}
- Check .claude/ for debugging information
- Verify the workspace is accessible and test files exist at: ${resolvedPath}
- If this error persists, check agent logs in .claude/
`);
    return; // STOP
}
```

**Extract Structured Results from Agent Output**:
```javascript
// Use execute-agent extractor patterns to parse structured fields
// Extractor patterns (from agents/execute-agent.md frontmatter):
//   exit_code:         /Exit Code:\s*(\d+)/
//   passed_count:      /Passed:\s*(\d+)/
//   failed_count:      /Failed:\s*(\d+)/
//   skipped_count:     /Skipped:\s*(\d+)/
//   duration:          /Duration:\s*([\d.]+)\s*seconds/
//   failures:          /##\s*Failure Details\s*\n([\s\S]*?)(?=\n##|$)/
//   execution_summary: /##\s*Execution Summary\s*\n([\s\S]*?)(?=\n##|$)/

const output = executeAgentOutput || '';

const exitCodeMatch      = output.match(/Exit Code:\s*(\d+)/);
const passedCountMatch   = output.match(/Passed:\s*(\d+)/);
const failedCountMatch   = output.match(/Failed:\s*(\d+)/);
const skippedCountMatch  = output.match(/Skipped:\s*(\d+)/);
const durationMatch      = output.match(/Duration:\s*([\d.]+)\s*seconds/);
const failuresMatch      = output.match(/##\s*Failure Details\s*\n([\s\S]*?)(?=\n##|$)/);
const summaryMatch       = output.match(/##\s*Execution Summary\s*\n([\s\S]*?)(?=\n##|$)/);

const exitCode        = exitCodeMatch      ? parseInt(exitCodeMatch[1], 10)      : null;
const passedCount     = passedCountMatch   ? parseInt(passedCountMatch[1], 10)   : null;
const failedCount     = failedCountMatch   ? parseInt(failedCountMatch[1], 10)   : null;
const skippedCount    = skippedCountMatch  ? parseInt(skippedCountMatch[1], 10)  : null;
const duration        = durationMatch      ? parseFloat(durationMatch[1])        : null;
const failuresText    = failuresMatch      ? failuresMatch[1].trim()             : null;
const executionSummary = summaryMatch      ? summaryMatch[1].trim()              : null;

// Extract framework detection metadata (not in formal extractors but present in agent output)
const frameworkMatch    = output.match(/Framework(?:\s+Detected)?:\s*([^\n]+)/i);
const confidenceMatch   = output.match(/Confidence(?:\s+Score)?:\s*([\d.]+)/i);
const testCommandMatch  = output.match(/Test Command(?:\s+Run)?:\s*([^\n]+)/i);

const frameworkDetected   = frameworkMatch   ? frameworkMatch[1].trim()          : (framework || 'unknown');
const frameworkConfidence = confidenceMatch  ? parseFloat(confidenceMatch[1])    : null;
const testCommand         = testCommandMatch ? testCommandMatch[1].trim()        : null;
```

**Handle Low Confidence Warning (REQ-F-12)**:
```javascript
// Only check confidence when --framework was NOT provided (auto-detection was used)
if (!framework && frameworkConfidence !== null && frameworkConfidence < 0.5) {
    // Display warning but DO NOT stop — continue with execution results
    display(`
⚠️  Warning: Low framework detection confidence (${(frameworkConfidence * 100).toFixed(0)}%)

The testing framework was detected with low confidence. Results may be incomplete or incorrect.

Detected framework: ${frameworkDetected}

Suggestions:
- Use --framework to specify the framework explicitly:
  /test-execute --framework ${frameworkDetected} ${resolvedPath !== getWorkspaceRoot() ? resolvedPath : ''}
- Supported frameworks: pytest, jest, junit, playwright, cypress, unittest,
  xunit, go-test, gtest, catch2, cargo-test, rspec, unity
`);
}
```

**Handle No Framework Detected (REQ-F-13)**:
```javascript
// No framework detected: confidence is 0 or framework is 'none'/'unknown' with no confidence
const noFrameworkDetected = !framework && (
    frameworkDetected === 'none' ||
    frameworkDetected === 'unknown' ||
    (frameworkConfidence !== null && frameworkConfidence === 0)
);

if (noFrameworkDetected) {
    displayError(`
❌ Error: No testing framework detected

Could not identify a testing framework in: ${resolvedPath}

Supported frameworks:
  - pytest          (pytest.ini, pyproject.toml, setup.cfg)
  - unittest        (Python standard library)
  - jest            (package.json jest config, jest.config.js)
  - playwright      (playwright.config.ts, playwright.config.js)
  - cypress         (cypress.config.ts, cypress.json)
  - junit           (pom.xml, *.java test files)
  - xunit           (*.csproj, *.sln with xunit reference)
  - go-test         (go.mod, *_test.go files)
  - gtest           (CMakeLists.txt with GTest)
  - catch2          (CMakeLists.txt with Catch2)
  - cargo-test      (Cargo.toml with #[test] functions)
  - rspec           (Gemfile with rspec, spec/ directory)
  - unity           (Unity project with test assemblies)

Suggestions:
- Use --framework to specify the framework manually:
  /test-execute --framework <name>
- Verify the target path contains test files: ${resolvedPath}
- Verify test framework configuration files are present
`);
    return; // STOP
}
```

### Step 4: Phase 2 Progress Display

**Display Phase 2 Progress** (displayed after execute-agent returns):
```
[2/{totalPhases}] ▶️  Executing tests...
```

### Step 4b: Optional Validation Phase (REQ-F-24 through REQ-F-27)

Conditionally invoke the validate-agent based on the `--validate` flag and whether failures exist. This section must run **before** Step 5 (coverage extraction) and **before** Step 6 (report persistence) so that `validationOutput` is available when Step 6 appends the `## Validation Results` section.

```javascript
// Declare validationOutput here so Step 6 can reference it.
// null = validation not performed (flag absent, all passed, or agent failed)
let validationOutput = null;
// Track whether validation was attempted but failed (for the failure note in the report)
let validationFailed = false;
```

**When `--validate` is NOT set**: skip this section entirely.

```javascript
// When --validate is not present, nothing to do — validationOutput stays null.
// Step 6 will omit the ## Validation Results section.
```

**When `--validate` is set AND `failedCount === 0`**: skip validation and display success message (REQ-F-27).

```javascript
if (validate && (failedCount === null || failedCount === 0)) {
    display(`✅ All tests passed — validation skipped`);
}
```

**When `--validate` is set AND `failedCount > 0`**: display progress, invoke validate-agent, handle errors (REQ-F-24).

```javascript
if (validate && failedCount !== null && failedCount > 0) {

    // Phase 3 progress display: [3/4] 🔬 Validating failures...
    display(`[3/${totalPhases}] 🔬 Validating failures...`);

    // Build validate-agent prompt.
    // Pass the full execute-agent output plus test type so the validate-agent
    // has all the context it needs (test results, failure details, coverage).
    const validatePrompt = `
You are the Validate Agent invoked by the /test-execute command.

## Context

The following test execution results were produced by the execute-agent. Analyze these results and produce a structured validation report following your output format exactly.

**Test Type**: ${normalizedType || 'unknown (infer from results)'}
**Target Path**: ${resolvedPath}

## Execute-Agent Output

${executeAgentOutput}

## Your Mission

Read and follow the agent definition at \`agents/validate-agent.md\`.

1. Categorize each failure as: test bug (with subcategory 1a-1e, or 1f-1k for E2E), source bug, or environment issue
2. Perform root cause analysis with confidence scores for each failure
3. Provide specific, actionable fix suggestions
4. Determine if iteration is needed
5. Produce both the structured JSON output and the human-readable Markdown report

Your output MUST include the following labeled sections for extraction:
- \`## Validation Summary\` (human-readable summary)
- \`Validation Status: PASS\` or \`Validation Status: FAIL\`
- \`## Failure Categories\` (with Test Bugs, Source Bugs, Environment Issues subsections)
- \`Test Bugs (Auto-fixable): N\`, \`Source Bugs (Requires Developer): N\`, \`Environment Issues: N\`
- \`Needs Iteration: Yes\` or \`Needs Iteration: No\`
- A fenced JSON block with the structured failures array
`;

    // Invoke validate-agent via Task tool (TD-5).
    // Apply --validate-model override when provided (REQ-F-8).
    let validateAgentError = null;

    try {
        const validateTaskOptions = {
            subagent_type: "test-engineering:validate-agent",
            description: `Validate ${failedCount} test failure${failedCount !== 1 ? 's' : ''} from ${resolvedPath}`,
            prompt: validatePrompt
        };

        // Apply model override when --validate-model was specified (REQ-F-8).
        // normalizedValidateModel is one of: 'opus', 'sonnet', 'haiku', or null.
        if (normalizedValidateModel) {
            validateTaskOptions.model = normalizedValidateModel;
        }

        validationOutput = await Task(validateTaskOptions);

    } catch (err) {
        // Tier 3 error: agent infrastructure failure (TD plan error strategy).
        // Do NOT stop — show execution results without validation (acceptance criterion).
        validateAgentError = err;
        validationFailed = true;
        validationOutput = null;
    }

    // When validate-agent Task fails: display note and continue to results display.
    if (validateAgentError) {
        display(`
⚠️ Validation failed — showing execution results only

The validate-agent encountered an error and could not complete failure categorization.
Error: ${validateAgentError.message || 'Unknown error'}

Execution results below are unaffected.
`);
    }
}
```

### Step 5: Extract Coverage Data

When `--coverage` was used, parse coverage output from the agent's full output:

```javascript
// Extract coverage data from execute-agent output when --coverage was enabled
let coveragePercent = null;
let coveragePerFile = null;

if (coverage) {
    // Match overall coverage percentage — common formats across frameworks
    // pytest: "TOTAL ... 85%"  |  Jest: "All files | 85 |"  |  Go: "coverage: 85.4% of statements"
    const coverageTotalMatch = output.match(
        /(?:TOTAL[^\n]*?\s+(\d+)%|All files\s*\|\s*([\d.]+)\s*\||coverage:\s*([\d.]+)%\s*of\s*statements)/i
    );
    if (coverageTotalMatch) {
        coveragePercent = parseFloat(
            coverageTotalMatch[1] ?? coverageTotalMatch[2] ?? coverageTotalMatch[3]
        );
    }

    // Extract per-file coverage block — look for the coverage table section
    const coverageTableMatch = output.match(
        /(?:(?:Name|File|Stmts|Coverage Report).*?\n[-\s|]+\n)([\s\S]*?)(?:\n[-\s]+\n|\nTOTAL|\n\n|$)/i
    );
    if (coverageTableMatch) {
        coveragePerFile = coverageTableMatch[1].trim();
    }
}
```

### Step 6: Save Full Execution Report to .claude/.last-execution.md

Before displaying the final results, persist the full execution report (REQ-F-23, TD-7):

```javascript
// Ensure .claude/ directory exists
const claudeDir = `${getWorkspaceRoot()}/.claude`;
bash(`mkdir -p "${claudeDir}"`);

// Build timestamp
const now = new Date();
const timestamp = now.toISOString(); // e.g. 2026-02-24T14:30:00.000Z

// Calculate total test count (passed + failed + skipped)
const totalCount = (passedCount ?? 0) + (failedCount ?? 0) + (skippedCount ?? 0);

// Build the full report content
const reportLines = [];

reportLines.push(`# Test Execution Report`);
reportLines.push(``);
reportLines.push(`**Generated**: ${timestamp}`);
reportLines.push(`**Target**: ${resolvedPath}`);
reportLines.push(`**Framework**: ${frameworkDetected}`);
reportLines.push(`**Test Type**: ${normalizedType || 'auto-detected'}`);
if (testCommand) {
    reportLines.push(`**Test Command**: \`${testCommand}\``);
}
reportLines.push(`**Flags**: ${[
    coverage  ? '--coverage'  : null,
    verbose   ? '--verbose'   : null,
    validate  ? '--validate'  : null,
].filter(Boolean).join(' ') || 'none'}`);
reportLines.push(``);
reportLines.push(`## Results`);
reportLines.push(``);
reportLines.push(`| Metric    | Value |`);
reportLines.push(`|-----------|-------|`);
reportLines.push(`| Total     | ${totalCount} |`);
reportLines.push(`| Passed    | ${passedCount ?? 'N/A'} |`);
reportLines.push(`| Failed    | ${failedCount ?? 'N/A'} |`);
reportLines.push(`| Skipped   | ${skippedCount ?? 'N/A'} |`);
reportLines.push(`| Duration  | ${duration != null ? duration + 's' : 'N/A'} |`);
reportLines.push(`| Exit Code | ${exitCode ?? 'N/A'} |`);
reportLines.push(``);

if (executionSummary) {
    reportLines.push(`## Execution Summary`);
    reportLines.push(``);
    reportLines.push(executionSummary);
    reportLines.push(``);
}

if (failuresText) {
    reportLines.push(`## Failure Details`);
    reportLines.push(``);
    reportLines.push(failuresText);
    reportLines.push(``);
}

if (coverage) {
    reportLines.push(`## Coverage`);
    reportLines.push(``);
    if (coveragePercent !== null) {
        reportLines.push(`**Overall Coverage**: ${coveragePercent.toFixed(1)}%`);
        reportLines.push(``);
    }
    if (coveragePerFile) {
        reportLines.push(`### Per-File Breakdown`);
        reportLines.push(``);
        reportLines.push('```');
        reportLines.push(coveragePerFile);
        reportLines.push('```');
        reportLines.push(``);
    }
    if (coveragePercent === null && !coveragePerFile) {
        reportLines.push(`_Coverage data not available for this framework._`);
        reportLines.push(``);
    }
}

reportLines.push(`## Full Agent Output`);
reportLines.push(``);
reportLines.push('```');
reportLines.push(executeAgentOutput);
reportLines.push('```');
reportLines.push(``);

// Append validation results when validate-agent was invoked and succeeded (TD-7, REQ-F-24).
// validationOutput is set in Step 4b when --validate is active and failedCount > 0.
if (validationOutput) {
    reportLines.push(`## Validation Results`);
    reportLines.push(``);
    reportLines.push(validationOutput);
    reportLines.push(``);
} else if (validationFailed) {
    // Validate-agent was invoked but failed — note this in the report.
    reportLines.push(`## Validation Results`);
    reportLines.push(``);
    reportLines.push(`_Validation failed — validate-agent encountered an error. See execution output above._`);
    reportLines.push(``);
}

const reportContent = reportLines.join('\n');

// Write the report (overwrite — consistent with existing state persistence pattern)
writeFile(`${claudeDir}/.last-execution.md`, reportContent);
```

### Step 7: Display Final Results Phase

**Display Final Phase Progress** (REQ-F-28):
```
[{totalPhases}/{totalPhases}] 📊 Results
```

**Display Structured Summary** (REQ-F-20):

```javascript
// Determine overall outcome
const hasFailures = (failedCount !== null && failedCount > 0) || (exitCode !== null && exitCode !== 0);
const summaryEmoji = hasFailures ? '⚠️' : '✅';
const totalCount   = (passedCount ?? 0) + (failedCount ?? 0) + (skippedCount ?? 0);
```

```markdown
## {summaryEmoji} Test Execution Complete

### Summary

**Target**: {resolvedPath}
**Framework**: {frameworkDetected}
{testCommand ? `**Command**: \`${testCommand}\`` : ''}

| Metric    | Value |
|-----------|-------|
| Total     | {totalCount} |
| ✅ Passed  | {passedCount ?? 'N/A'} |
| ❌ Failed  | {failedCount ?? 'N/A'} |
| ⏭️ Skipped | {skippedCount ?? 'N/A'} |
| ⏱️ Duration | {duration != null ? duration + 's' : 'N/A'} |
| Exit Code | {exitCode ?? 'N/A'} |
```

**Display Per-Failure Details** (REQ-F-21):

When `failuresText` is present and `failedCount > 0`, parse and display each failure. In default mode, truncate stack traces to 5 lines. In verbose mode, display full stack traces and per-test timing.

```javascript
if (failedCount > 0 && failuresText) {
    display(`\n### Failures\n`);

    // Split failures on common separators (numbered list, horizontal rule, or "FAILED" prefix)
    // Each failure block is expected to contain: test name, file path, line, error, stack trace
    const failureBlocks = failuresText
        .split(/\n(?=\d+\.\s|\-{3,}|FAILED\s|={3,})/)
        .map(block => block.trim())
        .filter(block => block.length > 0);

    const blocksToShow = failureBlocks.length > 0 ? failureBlocks : [failuresText];

    for (const block of blocksToShow) {
        if (!verbose) {
            // Default mode: truncate stack trace to first 5 lines (TD-6)
            const lines = block.split('\n');
            const stackStart = lines.findIndex(l =>
                /^\s+(at |File "|Traceback|  File)/.test(l) ||
                /^\s+\w.*\.(py|js|ts|java|cs|go|rb|cpp|c)\b/.test(l)
            );

            if (stackStart !== -1 && lines.length - stackStart > 5) {
                const truncated = [
                    ...lines.slice(0, stackStart + 5),
                    `    ... (use --verbose for full trace)`
                ].join('\n');
                display(truncated + '\n');
            } else {
                display(block + '\n');
            }
        } else {
            // Verbose mode: show full stack trace (REQ-F-3)
            display(block + '\n');
        }
    }
}
```

**Display Validation Results** (REQ-F-25, REQ-F-26):

When `--validate` was used and validation succeeded, display the categorization results:

```javascript
if (validate && validationOutput) {
    display(`\n### Validation Results\n`);
    display(validationOutput);
    display('\n');
}
```

**Display Coverage** (REQ-F-22):

When `--coverage` was used, display coverage results after the failure/validation section:

```javascript
if (coverage) {
    display(`\n### Coverage\n`);

    if (coveragePercent !== null) {
        display(`**Overall Coverage**: ${coveragePercent.toFixed(1)}%\n`);

        if (coveragePerFile) {
            display(`\n**Per-File Breakdown**:\n\`\`\`\n${coveragePerFile}\n\`\`\`\n`);
        }
    } else {
        display(`Coverage data not available for this framework\n`);
    }
}
```

**Display Saved Report Path** (REQ-F-23):
```
📄 Report saved to .claude/.last-execution.md
```

**Display Next Steps When Failures Exist** (acceptance criteria):

When `hasFailures` is true, display a next steps section. When `--validate` was NOT used, suggest it as an option:

```javascript
if (hasFailures) {
    display(`
---

### Next Steps

${failedCount} test${failedCount !== 1 ? 's' : ''} failed. To address these failures:

- **Automated fixing**: Run \`/test-loop\` to enter an iterative fix-and-verify cycle with approval gates
${!validate ? `- **Failure analysis**: Run \`/test-execute --validate\` to categorize failures (test bug, source bug, or environment issue) and get fix suggestions` : ''}
- **Review details**: See full report at \`.claude/.last-execution.md\`

`);
}
```

---

## Error Handling

### Unknown Flag
```markdown
❌ Error: Unknown flag(s): --{flag}

These flags are not recognized by /test-execute.

Run /test-execute --help to see all available options.
```

### Invalid Test Type
```markdown
❌ Error: Invalid test type

Test type must be one of: unit, integration, e2e

You provided: --type {value}

Example: /test-execute --type unit tests/
```

### Invalid Validate Model
```markdown
❌ Error: Invalid validate model

Model must be one of: opus, sonnet, haiku

You provided: --validate-model {value}

Example: /test-execute --validate --validate-model haiku
```

### Path Outside Workspace
```markdown
❌ Error: Path outside workspace

The specified path is outside the workspace boundary:
  Path:      {resolvedPath}
  Workspace: {workspaceRoot}

For security reasons, /test-execute cannot access paths outside the
current workspace. Use a path within: {workspaceRoot}
```

### Path Not Found
```markdown
❌ Error: Path not found

The specified path does not exist: {targetPath}

Suggestions:
- Check the path spelling
- Use relative paths from workspace root ({workspaceRoot})
- Run /test-execute to execute tests in the entire workspace
- Run /test-execute tests/ to target your test directory
```

### Path Too Long
```markdown
❌ Error: Path too long

The specified path exceeds the maximum allowed length of 4096 characters.

Suggestions:
- Use a shorter path
- Navigate to a parent directory and use a relative path
```

---

## Implementation Notes

### 1. Argument Parsing

Parse all flags inline before any agent invocation. Flag interactions:
- `--framework` overrides auto-detection (passed to execute-agent as a hint)
- `--type` determines timeout (120s unit/integration, 300s e2e) and E2E pre-flight behavior
- `--validate-model` is only relevant when `--validate` is also present; silently ignored otherwise
- `--coverage` is passed as context to the execute-agent prompt
- `--verbose` is handled at the command display level (controls stack trace truncation), not passed to agents

### 2. Progress Display

Phase numbering uses the fixed `totalPhases` value calculated from `--validate`:
- Without `--validate`: `[1/3]`, `[2/3]`, `[3/3]`
- With `--validate`: `[1/4]`, `[2/4]`, `[3/4]`, `[4/4]`

### 3. Security Model

Path validation is performed before any agent invocation:
- Null bytes removed (null byte injection prevention)
- Length checked against 4096-char maximum
- Resolved to absolute path
- Verified within workspace boundary (directory traversal prevention)
- Existence confirmed

### 4. No Approval Gates

This command is fully automated:
- Does NOT use AskUserQuestion tool
- Does NOT wait for user approval between phases
- Does NOT loop or iterate on failures
- Use `/test-loop` for iterative fixing with approval gates

### 5. Execution-Only

This command strictly executes existing tests:
- Does NOT invoke analyze-agent, write-agent, or fix-agent
- Does NOT create or modify test files
- Does NOT modify source files
- Uses execute-agent (always) and validate-agent (conditionally with --validate)

---

Now execute this command with the user's arguments.
