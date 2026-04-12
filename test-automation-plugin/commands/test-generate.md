---
description: "Fully automated test generation workflow with no approval gates"
argument-hint: "[options] [path]"
allowed-tools: Skill(test-engineering:framework-detection), Skill(test-engineering:test-generation), Skill(test-engineering:templates), Skill(test-engineering:test-location-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:build-integration), Skill(test-engineering:linting), Skill(test-engineering:helper-extraction), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection), Skill(test-engineering:state-management), Skill(test-engineering:team-orchestration), Skill(test-engineering:e2e), Skill(test-engineering:llt-generate), Skill(test-engineering:llt-build), Skill(test-engineering:llt-workflow), Skill(test-engineering:llt-online-tests), Skill(test-engineering:llt-web-tests), Skill(test-engineering:redundancy-detection)
---

# /test-generate Command

**Description**: Fully automated test generation workflow with no approval gates

**Usage**:
```
/test-generate [options] [path]
```

**Arguments**:
- `path` (optional): Directory or file to generate tests for. Defaults to workspace root if not specified.

**Options**:
- `--use-teams` (boolean, default: false): Enable parallel team orchestration mode. When true, loads `teams/testing-parallel.md` and invokes the team-orchestration skill for parallel agent execution. When false (default), uses the existing sequential workflow. (REQ-F-30)
- `--type <unit|integration|e2e>` (optional): Type of tests to generate. Defaults to `unit`.
- `--analyze-model <model>`: Override model for analyze-agent (opus, sonnet, haiku)
- `--write-model <model>`: Override model for write-agent (opus, sonnet, haiku)
- `--execute-model <model>`: Override model for execute-agent (opus, sonnet, haiku)
- `--validate-model <model>`: Override model for validate-agent (opus, sonnet, haiku)
- `--fix-model <model>`: Override model for fix-agent (opus, sonnet, haiku)
- `--help, -h`: Display help information

**Examples**:
```bash
# Generate unit tests for entire workspace
/test-generate

# Generate unit tests for specific directory
/test-generate src/

# Generate integration tests for specific file
/test-generate --type integration src/user_service.py

# Generate e2e tests for API module
/test-generate --type e2e src/api/

# Use sonnet for validate-agent (instead of default opus)
/test-generate --validate-model=sonnet src/

# Use haiku for write-agent to save cost on large codebases
/test-generate --write-model=haiku --type unit src/

# Enable parallel team orchestration mode
/test-generate --use-teams src/

# Combine team mode with test type and model overrides
/test-generate --use-teams --type integration --write-model=haiku src/
```

---

## Command Behavior

This command provides **fully automated test generation** with no user approval gates. It orchestrates the complete workflow:

**Workflow Phases**:
1. **Analyze** → Scan code to identify test targets
2. **Generate Plan** → Create test plan based on analysis
3. **Write** → Generate test code from plan
4. **Execute** → Run generated tests
5. **Validate** → Analyze results and categorize failures

**Key Characteristics**:
- ✅ Fully automated (no approval gates)
- ✅ Generates test plan internally (not shown to user)
- ✅ Creates test files automatically
- ✅ Executes tests immediately
- ✅ Reports final results
- ⚠️ Use `/test-loop` if you want approval gates and human-in-the-loop control

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/test-generate` command for fully automated test generation.

## Your Task

Execute the complete test generation workflow WITHOUT user approval gates. This is a fully automated process that will:
1. Analyze code
2. Generate test plan (internal)
3. Write test code
4. Execute tests
5. Validate results

### Step 1: Parse Arguments and Validate (SECURITY CRITICAL)

**Parse Arguments**:
```javascript
// Extract arguments from user command
const args = parseCommandArgs(userInput);
const path = args.path || getWorkspaceRoot();
const testType = args.type || 'unit'; // unit, integration, e2e
const useTeams = args['use-teams'] === true; // boolean flag, default: false (REQ-F-30)

// Parse model override flags
const cli_overrides = {};
if (args['analyze-model']) cli_overrides['analyze'] = args['analyze-model'];
if (args['write-model']) cli_overrides['write'] = args['write-model'];
if (args['execute-model']) cli_overrides['execute'] = args['execute-model'];
if (args['validate-model']) cli_overrides['validate'] = args['validate-model'];
if (args['fix-model']) cli_overrides['fix'] = args['fix-model'];
```

**Validate (SECURITY REQUIREMENTS)**:
- **PATH VALIDATION** (See SECURITY.md):
  - Remove null bytes from path
  - Check path length (max 4096 characters)
  - Resolve to absolute path
  - Verify path is within workspace boundaries (prevent directory traversal)
  - Check path exists (use Glob or Bash `ls`)
  - If validation fails, display error and STOP
- **Test Type Validation**:
  - Verify testType is valid (unit, integration, or e2e only)
  - Reject any other test types
- Display validation errors if needed

**Validate Model Override Flags**:
```javascript
const VALID_MODELS = ['opus', 'sonnet', 'haiku'];
for (const [agent, model] of Object.entries(cli_overrides)) {
    if (!VALID_MODELS.includes(model.toLowerCase())) {
        // Display error and stop
        // "Invalid model '{model}' for --{agent}-model. Supported: opus, sonnet, haiku"
    }
}
```

**Display Start Message**:
```markdown
## Starting Automated Test Generation

**Target**: {path}
**Test Type**: {testType}
**Mode**: ${useTeams ? 'Parallel Team Orchestration (--use-teams)' : 'Fully Automated (no approval gates)'}
${Object.keys(cli_overrides).length > 0 ? `**Model Overrides**: ${Object.entries(cli_overrides).map(([a, m]) => `${a}=${m}`).join(', ')}\n` : ''}
${useTeams ? `This will use parallel team orchestration via teams/testing-parallel.md.
Multiple agents will work simultaneously for faster test generation.` : `This will analyze, plan, generate, execute, and validate tests automatically.`}
Use `/test-loop` if you want approval gates and iterative control.

---
```

### Step 2: Detect Framework and Route Appropriately

**CRITICAL**: Before proceeding, detect if this is a Unreal Engine LLT project and delegate if needed.

**Quick Framework Detection**:
```javascript
// Perform lightweight framework detection to check for UE LLT
const isUEProject = (
    // Check for .uplugin or .uproject files
    glob(join(path, "**/*.uplugin"), {limit: 1}).length > 0 ||
    glob(join(path, "**/*.uproject"), {limit: 1}).length > 0
);

if (isUEProject) {
    // Check for TestModuleRules in .Build.cs files
    const buildCsFiles = glob(join(path, "**/Tests/**/*.Build.cs"), {limit: 5});
    for (const buildFile of buildCsFiles) {
        const content = readFile(buildFile);
        if (content.match(/:\s*TestModuleRules\s*\{/)) {
            // FOUND: This is UE LLT - delegate to /llt-generate
            displayMessage(`
🎯 Detected Unreal Engine Low Level Tests (LLT)

Delegating to specialized /llt-generate skill for UE-specific test generation...
            `);

            // Invoke the llt-generate skill directly
            return invokeLLTGenerate(path, args);
        }
    }

    // Check for TestHarness.h in test files
    const testFiles = glob(join(path, "**/Tests/**/*.cpp"), {limit: 10});
    for (const testFile of testFiles) {
        const content = readFile(testFile);
        if (content.match(/#include\s+"TestHarness\.h"/)) {
            // FOUND: This is UE LLT - delegate to /llt-generate
            displayMessage(`
🎯 Detected Unreal Engine Low Level Tests (LLT)

Delegating to specialized /llt-generate skill for UE-specific test generation...
            `);

            // Invoke the llt-generate skill directly
            return invokeLLTGenerate(path, args);
        }
    }
}

// Not UE LLT - continue with standard workflow
```

**LLT Delegation Function**:
```javascript
function invokeLLTGenerate(path, args) {
    // Invoke the llt-generate skill with the appropriate mode
    // Default to 'autonomous' mode for /test-generate compatibility

    // Build llt-generate command
    const mode = 'autonomous';  // Fully automated like /test-generate

    // Display delegation message
    displayMessage(`
📝 Using Unreal Engine LLT test generation workflow:
   - Mode: autonomous (fully automated)
   - Target: ${path}
   - Skill: llt-generate

This will:
1. Analyze UE module for testable functions
2. Generate .Build.cs, .Target.cs, and test .cpp files
3. Build the test executable with UnrealBuildTool
4. Execute tests and report results
    `);

    // Read and execute the llt-generate SKILL.md workflow
    const lltSkillContent = readFile('skills/llt-generate/SKILL.md');

    // Execute the complete LLT workflow as specified in SKILL.md
    // This includes:
    // - Phase 1: Analysis (find testable functions)
    // - Phase 2: Pattern detection
    // - Phase 3: Template rendering (.Build.cs, .Target.cs, test files)
    // - Phase 4: Build integration (UBT)
    // - Phase 5: Execution and validation

    // Follow the autonomous mode algorithm from SKILL.md
    return executeLLTWorkflow(path, mode, lltSkillContent);
}
```

### Step 2b: Route to Sequential or Team Orchestration Mode

**(Only if NOT UE LLT - otherwise already delegated in Step 2)**

Based on the `--use-teams` flag, route to the appropriate orchestration mode:

```javascript
if (useTeams) {
    // =====================================================================
    // TEAM ORCHESTRATION MODE (REQ-F-30)
    // When --use-teams=true, load the testing-parallel team definition
    // and invoke the team-orchestration skill for parallel execution.
    // =====================================================================

    // Step 2a: Verify testing-parallel team definition exists
    const teamDefPath = 'teams/testing-parallel.md';
    const teamDefExists = fileExists(teamDefPath);

    if (!teamDefExists) {
        // Display error and STOP - team definition not found
        displayError(`
❌ Error: Team Definition Not Found

The --use-teams flag requires the testing-parallel team definition at:
  ${teamDefPath}

This file defines the parallel agent composition and orchestration
strategy for team-based test generation.

To resolve:
1. Create the team definition at teams/testing-parallel.md
2. Or run without --use-teams to use sequential mode:
   /test-generate --type ${testType} ${path}

See teams/example-parallel.md for a team definition template.
See .sdd/specs/2026-02-12-agent-team-orchestration.md for the full specification.
`);
        return; // STOP execution
    }

    // Step 2b: Invoke team-orchestration skill
    // Read and follow skills/team-orchestration/SKILL.md
    // This skill handles the full lifecycle: load team definition,
    // approval gates, agent spawning, lifecycle tracking, result
    // aggregation, and telemetry logging.
    execute_team({
        team_name: 'testing-parallel',
        project_root: getWorkspaceRoot(),
        config_overrides: {
            // Disable approval gates for test-generate (fully automated)
            approval_gates: 'disabled',
            telemetry_enabled: null  // Use team definition defaults
        },
        context: {
            target_path: path,
            additional_args: {
                cli_model_overrides: cli_overrides,
                test_type: testType,
                workflow_type: 'test-generate',
                interactive_mode: false  // test-generate has no approval gates
            },
            depth: 1,
            parent_id: null
        }
    });

    // The team-orchestration skill handles everything from here:
    // - Loads teams/testing-parallel.md
    // - Skips approval gates (disabled for test-generate)
    // - Spawns parallel agents via Task tool
    // - Manages lifecycle, retries, and failure handling
    // - Aggregates results from all agents
    // - Presents final summary
    // See skills/team-orchestration/SKILL.md for the full algorithm.

    // Skip to Step 7 (Display Final Summary) after team completes.
    // The team-orchestration skill returns a TeamResult that should
    // be formatted as the final summary.

} else {
    // =====================================================================
    // SEQUENTIAL MODE (REQ-F-31, REQ-NF-5)
    // Default behavior: use existing sequential agent orchestration.
    // This is the original workflow, unchanged for backward compatibility.
    // =====================================================================

    // Continue to Step 3 (Phase 1 - Analyze Code)
}
```

### Step 3: Phase 1 - Analyze Code (Sequential Mode - Non-UE Projects)

**Display Progress**:
```
[1/5] 🔍 Analyzing code...
```

**Launch Analyze Agent**:
- Use Task tool with `subagent_type=general-purpose`
- Provide this prompt:

```
You are the Analyze Agent. Analyze the codebase at the specified path.

**Target Path**: {path}
**Test Type**: {testType}
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Read and apply the agent definition from `agents/analyze-agent.md`.
Focus on identifying test targets appropriate for {testType} tests:
- unit: Functions, methods, classes (isolated logic)
- integration: Multi-component interactions, database operations
- e2e: Full user workflows, API endpoints, UI flows

Output the complete analysis report with all required sections.
```

**Wait for Completion**:
- Extract results using agent extractors: `language`, `framework`, `test_targets`, `priority_summary`

**Display Result**:
```
✅ Analysis complete
   - Language: {language}
   - Framework: {framework}
   - Test Targets: {count} identified
   - Priorities: {critical} Critical, {high} High, {medium} Medium, {low} Low
```

**Save Analysis**:
- Create `.claude/` directory if needed
- Save analysis to `.claude/.last-analysis.md`
- Add timestamp to saved file

### Step 4: Phase 2 - Generate Test Plan (Internal)

**Display Progress**:
```
[2/5] 📋 Generating test plan...
```

**Create Test Plan Internally**:
You don't need to invoke a separate agent. Generate the plan directly based on the analysis results:

```markdown
## Test Plan

**Test Type**: {testType}
**Target**: {path}

### Test Targets

For each priority level (Critical → High → Medium → Low), list targets:

**Critical Priority**:
- {target_1}
  - Test cases: [happy path, edge cases, error handling]
  - Mocking needs: [external dependencies]
  - Fixtures needed: [setup/teardown]

**High Priority**:
- {target_2}
  - Test cases: [...]
  - Mocking needs: [...]
  - Fixtures needed: [...]

[Continue for all targets...]

### Framework Setup

- Test directory: `.claude-tests/` (or `tests/` if exists)
- Test file naming: `test_{module_name}.py`
- Fixtures: [shared fixtures needed]
- Mocking strategy: [unittest.mock, pytest-mock]

### Coverage Goals

- Target: 80%+ for Critical priority
- Target: 70%+ for High priority
- Target: 60%+ for Medium priority
```

**Display Result**:
```
✅ Test plan generated
   - Test cases planned: {count}
   - Test files to create: {file_count}
   - Estimated tests: {test_count}
```

**Save Plan**:
- Save to `.claude/.last-test-plan.md`

### Step 5: Phase 3 - Write Test Code

**Display Progress**:
```
[3/5] ✍️ Generating test code...
```

**Launch Write Agent**:
- Use Task tool with `subagent_type=general-purpose`
- Provide this prompt:

```
You are the Write Agent. Generate test code based on the analysis and plan.

**Context**:
- Analysis: Read from `.claude/.last-analysis.md`
- Test Plan: Read from `.claude/.last-test-plan.md`
- Test Type: {testType}
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Read and apply the agent definition from `agents/write-agent.md`.

**Your Mission**:
1. Load analysis and test plan
2. For each test target, generate comprehensive test code
3. Use templates from `skills/templates/python-pytest-template.md`
4. Follow patterns from `skills/test-generation/python-patterns.md`
5. Create test files in `.claude-tests/` directory
6. Validate syntax before outputting

Generate test code for ALL targets in the plan. Write actual test files using the Write tool.

Output a structured report with:
- Test files created
- Test count per file
- Any issues encountered
```

**Wait for Completion**:
- Extract results: `generated_tests`, `test_count`, `test_files`

**Display Result**:
```
✅ Test code generated
   - Test files created: {file_count}
     {list_of_files}
   - Total tests: {test_count}
```

### Step 6: Phase 4 - Execute Tests

**Display Progress**:
```
[4/5] ▶️ Executing tests...
```

**Launch Execute Agent**:
- Use Task tool with `subagent_type=general-purpose`
- Provide this prompt:

```
You are the Execute Agent. Run the generated tests.

**Test Directory**: `.claude-tests/`
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Read and apply the agent definition from `agents/execute-agent.md`.

**Your Mission**:
1. Detect test framework (pytest, unittest)
2. Locate all test files in `.claude-tests/`
3. **SECURITY - Construct test command securely**:
   - Whitelist: pytest or unittest ONLY
   - Use command array format (NOT string)
   - Never use shell=True
4. **SECURITY - Execute tests safely**:
   - Set 300 second timeout (prevent DOS)
   - Use shell=False (prevent command injection)
   - Validate paths are within workspace
   - Limit output capture to 10MB
5. Parse test results (passed, failed, skipped counts)
6. Extract failure details for any failing tests

Output a structured execution report with all test results.

**SECURITY REQUIREMENTS** (See SECURITY.md):
- Command whitelisting enforced
- No shell execution (shell=False)
- Timeouts required on all operations
- Path validation for all file operations
```

**Wait for Completion**:
- Extract results: `exit_code`, `passed_count`, `failed_count`, `skipped_count`, `duration`, `failures`

**Display Result**:
```
✅ Tests executed
   - Passed: {passed_count}
   - Failed: {failed_count}
   - Skipped: {skipped_count}
   - Duration: {duration}
```

**Save Results**:
- Save execution report to `.claude/.last-execution.md`

### Step 7: Phase 5 - Validate Results

**Display Progress**:
```
[5/5] ✅ Validating results...
```

**Launch Validate Agent**:
- Use Task tool with `subagent_type=general-purpose`
- Provide this prompt:

```
You are the Validate Agent. Analyze test execution results.

**Execution Results**: Read from `.claude/.last-execution.md`
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Read and apply the agent definition from `agents/validate-agent.md`.

**Your Mission**:
1. Assess overall test status (PASS/FAIL)
2. Categorize any failures (test bugs vs source bugs vs environment issues)
3. Perform root cause analysis for failures
4. Generate specific, actionable recommendations
5. Determine if iteration is needed

Output a structured validation report.
```

**Wait for Completion**:
- Extract results: `validation_status`, `failure_categories`, `needs_iteration`

**Display Result**:
```
✅ Validation complete
   - Status: {validation_status}
   - Test bugs: {test_bug_count}
   - Source bugs: {source_bug_count}
   - Environment issues: {environment_issue_count}
```

### Step 8: Display Final Summary

Present a comprehensive summary to the user:

```markdown
## ✅ Test Generation Complete

### Summary

**Target**: {path}
**Test Type**: {testType}
**Duration**: {total_duration}

### Results

**Analysis**:
- Language: {language}
- Framework: {framework}
- Test Targets: {target_count}

**Generated Tests**:
- Test files: {file_count}
- Total tests: {test_count}
- Location: `.claude-tests/`

**Execution**:
- ✅ Passed: {passed_count}
- ❌ Failed: {failed_count}
- ⏭️ Skipped: {skipped_count}
- ⏱️ Duration: {duration}

**Validation**:
- Overall: {validation_status}
- Test bugs: {test_bug_count} (auto-fixable)
- Source bugs: {source_bug_count} (need developer review)
- Environment issues: {environment_issue_count}

---

### Failure Analysis

{if failures exist, show categorized failures}

**Test Bugs** (Auto-fixable):
- {failure_1}: {brief_description}
  - Fix: {recommendation}

**Source Bugs** (Require Developer):
- {failure_2}: {brief_description}
  - Location: {file}:{line}
  - Recommendation: {fix_guidance}

**Environment Issues**:
- {failure_3}: {brief_description}
  - Fix: {recommendation}

---

### Recommendations

{top_3_recommendations_from_validate_agent}

---

### Saved Reports

- Analysis: `.claude/.last-analysis.md`
- Test Plan: `.claude/.last-test-plan.md`
- Execution: `.claude/.last-execution.md`
- Validation: `.claude/.last-validation.md`

---

### Next Steps

{if validation_status == "PASS"}
✅ All tests passed! Your code is well-tested.
- Review generated tests in `.claude-tests/`
- Consider moving tests to your main test directory
- Run tests in your CI/CD pipeline

{if needs_iteration == "Yes" and test_bug_count > 0}
⚠️ Some test bugs detected. Recommendations:
- Review test bugs (auto-fixable issues)
- Run `/test-loop` for iterative fixing with approval gates
- Or manually fix tests in `.claude-tests/`

{if needs_iteration == "Yes" and source_bug_count > 0}
⚠️ Source code bugs detected. Recommendations:
- Review source bugs at locations indicated above
- Fix source code issues
- Re-run `/test-generate` after fixes

{if needs_iteration == "Yes" and environment_issue_count > 0}
⚠️ Environment issues detected. Recommendations:
- Install missing dependencies
- Fix configuration issues
- Re-run `/test-generate` after fixes

### Related Commands

- `/test-analyze` - Re-analyze code for testing needs
- `/test-loop` - Interactive test generation with approval gates
- `/test-resume` - Resume interrupted test loop workflow
```

---

## Error Handling

### Team Definition Not Found (--use-teams)
```markdown
❌ Error: Team Definition Not Found

The --use-teams flag requires the testing-parallel team definition at:
  teams/testing-parallel.md

This file defines the parallel agent composition and orchestration
strategy for team-based test generation.

To resolve:
1. Create the team definition at teams/testing-parallel.md
2. Or run without --use-teams to use sequential mode:
   /test-generate [path]

See teams/example-parallel.md for a team definition template.
See .sdd/specs/2026-02-12-agent-team-orchestration.md for the full specification.
```

### Path Validation Errors
```markdown
❌ Error: Path not found

The specified path does not exist: {path}

Suggestions:
- Check the path spelling
- Use relative paths from workspace root
- Try: /test-generate (analyze entire workspace)
- Try: /test-generate src/
```

### Invalid Test Type
```markdown
❌ Error: Invalid test type

Test type must be one of: unit, integration, e2e

Example: /test-generate --type unit src/
```

### No Source Files Found
```markdown
⚠️ Warning: No source files found

No source files were found at: {path}

Suggestions:
- Verify this is the correct directory
- Check file extensions match the language
- Ensure files are not in excluded directories (venv/, node_modules/)
```

### Framework Not Detected
```markdown
⚠️ Warning: Testing framework not detected

Could not detect a testing framework for {language}.

Recommendations:
- For Python: Install pytest (`pip install pytest`)
- Create pytest.ini or add [tool.pytest] to pyproject.toml
- The plugin will default to pytest/unittest patterns
```

### Agent Execution Errors
```markdown
❌ Error: {phase} failed

An error occurred during {phase}: {error_message}

Troubleshooting:
- Check `.claude/` directory for saved reports
- Review agent output for specific errors
- Try running individual commands separately:
  - /test-analyze (for analysis phase)
  - Check logs for detailed error information
```

### Test Execution Errors
```markdown
⚠️ Test Execution Issues

Tests were generated but execution encountered issues:
- {issue_description}

Recommendations:
- Check `.claude-tests/` for generated test files
- Manually run: pytest .claude-tests/ -v
- Review execution errors in `.claude/.last-execution.md`
```

---

## Help Text

When user runs `/test-generate --help` or `/test-generate -h`:

```
/test-generate - Fully automated test generation workflow

USAGE:
  /test-generate [options] [path]

ARGUMENTS:
  path    Optional. Directory or file to generate tests for.
          Defaults to workspace root.

OPTIONS:
  --use-teams                Enable parallel team orchestration mode (default: false).
                             Loads teams/testing-parallel.md and uses the
                             team-orchestration skill for parallel agent execution.
                             Without this flag, the sequential workflow is used
                             (backward compatible). See REQ-F-30.
  --type <type>              Type of tests to generate: unit, integration, e2e
                             Default: unit
  --analyze-model <model>    Override model for analyze-agent (opus, sonnet, haiku)
  --write-model <model>      Override model for write-agent (opus, sonnet, haiku)
  --execute-model <model>    Override model for execute-agent (opus, sonnet, haiku)
  --validate-model <model>   Override model for validate-agent (opus, sonnet, haiku)
  --fix-model <model>        Override model for fix-agent (opus, sonnet, haiku)
  --no-explore               Disable browser exploration for E2E tests (default: exploration
                             is on when app is accessible). Useful for CI or offline analysis.
  --explore                  Force-enable browser exploration in CI environments (CI=true).
                             No effect locally since exploration is on by default.
  --help, -h                 Show this help message

MODEL OVERRIDES:
  By default, each agent uses its configured model (from .dante.yml, environment,
  or built-in defaults). Use --{agent}-model flags to override for a specific run.
  Precedence: CLI flag > environment variable > .dante.yml config > built-in default.

EXAMPLES:
  /test-generate                           # Generate unit tests for workspace
  /test-generate src/                      # Generate unit tests for src/
  /test-generate --type integration src/   # Generate integration tests
  /test-generate --validate-model=sonnet src/          # Override validate model
  /test-generate --write-model=haiku --type unit src/  # Use haiku for write-agent
  /test-generate --use-teams src/                      # Parallel team orchestration
  /test-generate --use-teams --type integration src/   # Team mode with test type

DESCRIPTION:
  Fully automated test generation with no approval gates. Orchestrates:
  1. Analysis: Scan code to identify test targets
  2. Planning: Generate internal test plan
  3. Writing: Create test code files
  4. Execution: Run generated tests
  5. Validation: Analyze results and categorize failures

  This command is fully automated and does not ask for approval at any stage.
  Use /test-loop if you want human-in-the-loop control with approval gates.

  With --use-teams, the command loads teams/testing-parallel.md and uses
  the team-orchestration skill to run multiple agents in parallel. This
  can significantly speed up test generation for large codebases. Without
  --use-teams, the original sequential workflow is used (backward compatible).

OUTPUT:
  - Generated test files in .claude-tests/
  - Test execution results (passed/failed/skipped)
  - Failure analysis with categorization
  - Actionable recommendations
  - Saved reports in .claude/ directory

WORKFLOW:
  Sequential (default, no approval gates):
  Analyze → Plan → Write → Execute → Validate → Report

  Parallel (--use-teams):
  Load Team → Spawn Parallel Agents → Aggregate Results → Report

COMPARISON:
  /test-generate              - Fully automated, sequential, no approval gates
  /test-generate --use-teams  - Fully automated, parallel via team orchestration
  /test-loop                  - Human-in-the-loop, approval gates, iterative control
  /test-loop --use-teams      - Human-in-the-loop, parallel, with approval gates

SAVED REPORTS:
  .claude/.last-analysis.md      - Code analysis report
  .claude/.last-test-plan.md     - Generated test plan
  .claude/.last-execution.md     - Test execution results
  .claude/.last-validation.md    - Validation and recommendations

SEE ALSO:
  /test-analyze    Analyze code for testing needs
  /test-loop       Interactive test generation with approval gates
  /test-resume     Resume interrupted test loop
```

---

## Implementation Notes

### 1. Sequential Agent Orchestration (Default Mode)

Launch agents sequentially (not in parallel), waiting for each to complete before starting the next:

```javascript
// Pseudocode for sequential orchestration (default, --use-teams=false)
const analysis = await launchAgent('analyze-agent', analysisPrompt);
const plan = generatePlan(analysis);  // Internal, no agent needed
const writeResults = await launchAgent('write-agent', writePrompt);
const execResults = await launchAgent('execute-agent', executePrompt);
const validation = await launchAgent('validate-agent', validatePrompt);
```

### 1a. Parallel Team Orchestration (--use-teams Mode)

When `--use-teams` is enabled, the team-orchestration skill handles all agent
spawning and lifecycle management. The sequential steps above are replaced by
the team orchestration workflow defined in `skills/team-orchestration/SKILL.md`:

```javascript
// Pseudocode for team orchestration (--use-teams=true)
// 1. Load team definition from teams/testing-parallel.md
// 2. Build execution plan from agent composition and dependencies
// 3. Spawn parallel agents via Task tool (respecting max_agents limit)
// 4. Monitor agent lifecycle, handle retries with exponential backoff
// 5. Aggregate results from all agents
// 6. Return unified TeamResult
const teamResult = await execute_team('testing-parallel', projectRoot, overrides, context);
```

### 2. Progress Display

Show clear progress at each phase:
- Use phase numbers: [1/5], [2/5], etc.
- Use emoji for visual clarity: 🔍 🔨 ✅ ❌
- Display phase name and status
- Show key metrics after each phase completes

### 3. State Persistence

Save state after each phase to enable debugging and analysis:
- `.claude/.last-analysis.md`: Analysis results
- `.claude/.last-test-plan.md`: Generated test plan
- `.claude/.last-execution.md`: Execution results
- `.claude/.last-validation.md`: Validation report

### 4. Test File Location

Generated tests go to `.claude-tests/` directory:
- Creates directory if it doesn't exist
- Uses same structure as source: `.claude-tests/test_{module}.py`
- User can move tests to main test directory after review

### 5. Error Recovery

If any phase fails:
- Display clear error message
- Save partial results to `.claude/` files
- Suggest fallback commands (e.g., run `/test-analyze` separately)
- Allow user to inspect saved reports for debugging

### 6. No Approval Gates

This command is fully automated:
- Does NOT use AskUserQuestion tool
- Does NOT wait for user approval
- Executes all phases automatically
- For approval gates, users should use `/test-loop` instead

### 7. Test Type Handling

Different test types require different strategies:
- **unit**: Focus on isolated functions, mock dependencies
- **integration**: Focus on component interactions, real dependencies
- **e2e**: Focus on full workflows, real systems

Pass test type to agents so they adjust their behavior accordingly.

### 8. E2E Tool Permissions (TASK-011)

When `--type e2e` is specified, the following additional tool permissions are required for E2E operations. These permissions are enabled by the `Skill(test-engineering:e2e)` entry in `allowed-tools` above.

**E2E Framework CLI Permissions**:
- Execute E2E framework CLI commands (e.g., `npx playwright`, `npx cypress`, `pip show selenium`)
- Run browser installation checks (e.g., `npx playwright install --dry-run`)
- Run browser installation commands (e.g., `npx playwright install`)
- Parse E2E framework configuration files (e.g., `playwright.config.ts`, `cypress.config.js`)

**E2E Browser Permissions**:
- Launch browser processes for E2E test execution (managed by the E2E framework)
- Launch playwright-cli for page snapshots and element inspection during analysis and fix phases
- Access localhost URLs for application-under-test verification
- Network access for browser downloads during browser installation

**E2E Knowledge Base Permissions**:
- Create `.dante/e2e-knowledge/` directory in the project root
- Read/write `known-issues.md` and `project-patterns.md` files
- Append entries to knowledge base after successful novel fixes

**E2E Timeout**:
- E2E test execution uses a 5-minute (300s) timeout instead of the standard 2-minute (120s) timeout
- This longer timeout accounts for browser startup, page navigation, and network requests

**Important**: These E2E permissions activate ONLY when `test_type=e2e`. For `test_type=unit` or `test_type=integration`, no E2E-specific tools are invoked and all existing behavior is unchanged.

---

Now execute this command with the user's arguments.
