---
description: "Human-in-the-loop testing workflow with approval gates at key decision points"
argument-hint: "[options] [path]"
allowed-tools: Skill(test-engineering:framework-detection), Skill(test-engineering:test-generation), Skill(test-engineering:templates), Skill(test-engineering:test-location-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:build-integration), Skill(test-engineering:linting), Skill(test-engineering:helper-extraction), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection), Skill(test-engineering:state-management), Skill(test-engineering:team-orchestration), Skill(test-engineering:e2e), Skill(test-engineering:llt-generate), Skill(test-engineering:llt-build), Skill(test-engineering:llt-workflow), Skill(test-engineering:llt-online-tests), Skill(test-engineering:llt-web-tests), Skill(test-engineering:redundancy-detection), Skill(test-engineering:gh-pr-manage)
---

# /test-loop Command

**Description**: Human-in-the-loop testing workflow with approval gates at key decision points

**Usage**:
```
/test-loop [options] [path]
```

**Arguments**:
- `path` (optional): Directory or file to generate tests for. Defaults to workspace root if not specified.

**Options**:
- `--use-teams` (boolean, default: false): Enable parallel team orchestration mode. When true, loads `teams/testing-parallel.md` and invokes the team-orchestration skill for parallel agent execution. When false (default), uses the existing sequential test-loop-orchestrator. (REQ-F-30)
- `--analyze-model <model>`: Override model for analyze-agent (opus, sonnet, haiku)
- `--write-model <model>`: Override model for write-agent (opus, sonnet, haiku)
- `--execute-model <model>`: Override model for execute-agent (opus, sonnet, haiku)
- `--validate-model <model>`: Override model for validate-agent (opus, sonnet, haiku)
- `--fix-model <model>`: Override model for fix-agent (opus, sonnet, haiku)
- `--help, -h`: Display help information

**Examples**:
```bash
# Start interactive test loop for entire workspace
/test-loop

# Start interactive test loop for specific directory
/test-loop src/

# Start interactive test loop for specific file
/test-loop src/user_service.py

# Use sonnet for validate-agent (instead of default opus)
/test-loop --validate-model=sonnet src/

# Use opus for all agents
/test-loop --analyze-model=opus --write-model=opus --execute-model=opus --validate-model=opus --fix-model=opus src/

# Enable parallel team orchestration mode
/test-loop --use-teams src/

# Combine team mode with model overrides
/test-loop --use-teams --write-model=haiku src/
```

---

## Command Behavior

This command provides **human-in-the-loop testing** with approval gates at critical decision points. You maintain full control over the test generation and execution process.

**Workflow Phases**:
1. **🔍 Analysis** → Scan code to identify test targets
2. **✅ Plan Approval (Gate #1)** → Review and approve test plan
3. **📝 Code Generation** → Generate test code from approved plan
4. **✅ Code Approval (Gate #2)** → Review and approve generated test code
5. **⚡ Execution** → Run approved tests
6. **🔍 Validation** → Analyze test results and categorize failures
7. **✅ Iteration Decision (Gate #3)** → Fix failures, generate more, or complete

**Key Characteristics**:
- ✅ Three approval gates for full control
- ✅ Iterative refinement with feedback (max 3 iterations per gate)
- ✅ Review test plans before code generation
- ✅ Review generated code before execution
- ✅ Decide how to handle test failures
- ✅ State persistence enables workflow resumption via `/test-resume`
- ⚡ Use `/test-generate` if you want fully automated generation without approval gates

---

## Approval Gates

### Gate #1: Test Plan Approval

**When**: After code analysis, before test code generation

**Purpose**: Review what will be tested and how

**Options**:
- **✅ Approve**: Proceed to test code generation with this plan
- **🔄 Request Changes**: Provide feedback to modify the plan
- **❌ Reject**: Cancel the workflow

**Example**:
```
📋 Test Plan Generated

Framework: pytest
Test Targets: 15

### Critical Priority
- src/user_service.py::create_user
  - Test Cases: happy path, invalid data, duplicate user
- src/calculator.py::divide
  - Test Cases: normal division, divide by zero, negative numbers

[... more targets ...]

Do you approve this test plan?
1. ✅ Approve
2. 🔄 Request Changes
3. ❌ Reject
```

### Gate #2: Test Code Approval

**When**: After test code generation, before execution

**Purpose**: Review actual test code before running it

**Options**:
- **✅ Approve**: Write tests to disk and execute them
- **🔄 Request Changes**: Provide feedback to modify the test code
- **❌ Reject**: Cancel the workflow

**Example**:
```
📝 Generated 15 tests in 3 files

### File: .claude-tests/test_user_service.py

```python
import pytest
from src.user_service import UserService

class TestUserService:
    def test_create_user_valid_data(self):
        # Arrange
        service = UserService()
        data = {"name": "John", "email": "john@example.com"}

        # Act
        result = service.create_user(data)

        # Assert
        assert result["id"] is not None
        assert result["name"] == "John"
```

[... more test code ...]

Do you approve the generated test code?
1. ✅ Approve
2. 🔄 Request Changes
3. ❌ Reject
```

### Gate #3: Iteration Decision

**When**: After test execution and validation

**Purpose**: Decide next steps based on test results

**Options** (if tests passed):
- **✅ Done**: Complete the workflow - tests are sufficient
- **🔄 Generate More**: Generate additional tests for more coverage

**Options** (if tests failed):
- **✅ Done**: Accept results as-is - I'll fix issues manually
- **🔧 Fix and Retry**: Apply recommended fixes and re-run tests
- **🔄 Generate More**: Generate additional tests
- **❌ Cancel**: Stop the workflow

**Example**:
```
📊 Test Results:
- ✅ Passed: 12
- ❌ Failed: 3
- ⏭️ Skipped: 0

🔍 Failure Analysis:
- 🐛 Test Bugs: 2 (auto-fixable)
  - test_divide_by_zero: Missing mock for logger
  - test_invalid_input: Incorrect assertion
- 🔴 Source Bugs: 1 (requires manual action)
  - divide function doesn't handle None input

Some tests failed. How would you like to proceed?
1. ✅ Done
2. 🔧 Fix and Retry
3. 🔄 Generate More
4. ❌ Cancel
```

---

## Comparison: /test-loop vs /test-generate

| Feature | /test-loop | /test-generate |
|---------|-----------|---------------|
| **Approval Gates** | ✅ 3 gates | ❌ None (fully automated) |
| **Test Plan Review** | ✅ Yes | ❌ Internal only |
| **Code Review** | ✅ Yes | ❌ Auto-generated |
| **Iteration Support** | ✅ Yes (max 3 per gate) | ❌ One-shot |
| **State Persistence** | ✅ Yes (resumable) | ⚠️ Partial |
| **User Feedback** | ✅ At every gate | ❌ None |
| **Speed** | ⚡ Slower (interactive) | ⚡⚡⚡ Fast (automated) |
| **Control** | ✅✅✅ Full control | ⚡ Quick results |

**When to use /test-loop**:
- You want to review and approve test plans before generation
- You want to inspect generated test code before execution
- You want iterative improvement with feedback
- You need control over what gets tested
- You're working on critical code that needs careful testing

**When to use /test-generate**:
- You want fast, automated test generation
- You trust AI to make good testing decisions
- You're generating tests for straightforward code
- You want to get tests quickly and refine manually later

---

## State Persistence and Resumption

The `/test-loop` workflow **automatically saves state** after each phase to `.claude/.test-loop-state.md`.

**Benefits**:
- ✅ Resume interrupted workflows with `/test-resume`
- ✅ Recover from crashes or timeouts
- ✅ Continue work across sessions
- ✅ Review workflow history in `.claude/.test-loop-history/`

**Example**:
```bash
# Start workflow
/test-loop src/

# ... work through phases ...
# [Claude Code crashes or you close it]

# Later, resume where you left off
/test-resume
```

---

## Iteration Limits

Each approval gate has a **maximum of 3 iterations** to prevent infinite loops:

- **Test Plan Iterations**: Max 3 times you can request changes to the plan
- **Test Code Iterations**: Max 3 times you can request changes to the code
- **Fix and Retry Iterations**: Max 3 times you can fix and re-run tests

When the limit is reached:
```
⚠️ Maximum Iterations Reached

You've reached the maximum of 3 iterations for this approval gate.

Options:
1. ✅ Proceed with current version
2. ❌ Cancel workflow
```

---

## Error Handling

The orchestrator handles various error scenarios:

### Agent Failures
If any agent (Analyze, Write, Execute, Validate) fails:
```
❌ Error in Phase 3/7: Code Generation

[Error details]

Options:
1. 🔄 Retry - Try this phase again
2. ⏭️ Skip - Continue to next phase (if possible)
3. 💾 Save and Exit - Save state and exit workflow
```

### Timeouts
Each agent has a 5-minute timeout:
```
⏱️ Timeout in Phase 5/7: Execution

The Execute agent exceeded the 5-minute timeout.

Options:
1. 🔄 Retry with extended timeout (10 minutes)
2. 💾 Save and Exit
```

### Missing Framework
If framework detection fails:
```
❌ Framework Detection Failed

Unable to automatically detect testing framework.

Please specify:
- Language: [Python]
- Framework: [pytest]
```

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/test-loop` command for human-in-the-loop test generation.

## Your Task

Launch the test-loop-orchestrator subagent to guide the user through the interactive testing workflow with approval gates.

### Step 1: Parse Arguments and Validate (SECURITY CRITICAL)

**Parse Arguments**:
```javascript
// Extract path from user command
const args = parseCommandArgs(userInput);
const path = args.path || getWorkspaceRoot();
const useTeams = args['use-teams'] === true; // boolean flag, default: false (REQ-F-30)

// Parse model override flags
const cli_overrides = {};
if (args['analyze-model']) cli_overrides['analyze'] = args['analyze-model'];
if (args['write-model']) cli_overrides['write'] = args['write-model'];
if (args['execute-model']) cli_overrides['execute'] = args['execute-model'];
if (args['validate-model']) cli_overrides['validate'] = args['validate-model'];
if (args['fix-model']) cli_overrides['fix'] = args['fix-model'];
```

**Validate (SECURITY REQUIREMENTS - See SECURITY.md)**:
- Remove null bytes from path
- Check path length (max 4096 characters)
- Resolve to absolute path
- Verify path is within workspace boundaries (prevent directory traversal)
- Check path exists (use Glob or Bash `ls`)
- If validation fails, display error and STOP
- **IMPORTANT**: All user feedback at approval gates must be sanitized (see SECURITY.md)

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
# Starting Human-in-the-Loop Test Generation

**Target**: {path}
**Mode**: ${useTeams ? 'Parallel Team Orchestration (--use-teams)' : 'Interactive (with approval gates)'}
${Object.keys(cli_overrides).length > 0 ? `**Model Overrides**: ${Object.entries(cli_overrides).map(([a, m]) => `${a}=${m}`).join(', ')}\n` : ''}
${useTeams ? `This workflow uses parallel team orchestration via teams/testing-parallel.md.
Multiple agents will work in parallel for faster test generation.` : `This workflow has 3 approval gates where you can review and provide feedback:
- 📋 Gate #1: Test Plan Approval
- 📝 Gate #2: Test Code Approval
- 🔄 Gate #3: Iteration Decision`}

State will be saved automatically for resumption capability.

---
```

### Step 2: Route to Sequential or Team Orchestration Mode

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
   /test-loop ${path}

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
            // Pass any relevant CLI overrides to the team
            approval_gates: null,  // Use team definition defaults
            telemetry_enabled: null  // Use team definition defaults
        },
        context: {
            target_path: path,
            additional_args: {
                cli_model_overrides: cli_overrides,
                workflow_type: 'test-loop',
                interactive_mode: true  // test-loop uses approval gates
            },
            depth: 1,
            parent_id: null
        }
    });

    // The team-orchestration skill handles everything from here:
    // - Loads teams/testing-parallel.md
    // - Presents execution plan for approval (if gates enabled)
    // - Spawns parallel agents via Task tool
    // - Manages lifecycle, retries, and failure handling
    // - Aggregates results from all agents
    // - Presents final results
    // See skills/team-orchestration/SKILL.md for the full algorithm.

} else {
    // =====================================================================
    // SEQUENTIAL MODE (REQ-F-31, REQ-NF-5)
    // Default behavior: use existing test-loop-orchestrator subagent.
    // This is the original sequential workflow, unchanged for backward
    // compatibility.
    // =====================================================================

    // Continue to Step 3 (Launch Test Loop Orchestrator Subagent)
}
```

### Step 3: Launch Test Loop Orchestrator Subagent (Sequential Mode)

Use the **Task tool** to launch the test-loop-orchestrator:

```javascript
Task({
  subagent_type: "general-purpose",
  description: "Running interactive test loop",
  prompt: `You are the test-loop-orchestrator subagent. Execute the human-in-the-loop testing workflow for the following target:

**Target Path**: ${path}
**Test Type**: unit (default)
**Workflow ID**: test-loop-${timestamp}
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Follow the complete 7-phase workflow defined in subagents/test-loop-orchestrator.md:

1. Phase 1: Analysis - Launch analyze-agent
2. Phase 2: Plan Approval - Use AskUserQuestion for approval
3. Phase 3: Code Generation - Launch write-agent
4. Phase 4: Code Approval - Use AskUserQuestion for approval
5. Phase 5: Execution - Write files and launch execute-agent
6. Phase 6: Validation - Launch validate-agent
7. Phase 7: Iteration Decision - Use AskUserQuestion for decision

**Important**:
- Save state to .claude/.test-loop-state.md after each phase
- Use AskUserQuestion tool for all approval gates
- Support max 3 iterations per gate
- Handle errors gracefully
- Display clear progress indicators

Execute the workflow now.`
})
```

### Step 3: Monitor and Display Results

The orchestrator subagent will:
- Display progress at each phase
- Present approval gates to the user
- Handle user feedback and iterations
- Save state automatically
- Archive state on completion

You do not need to do anything else - the orchestrator handles the entire workflow.

### Step 4: Workflow Completion

When the orchestrator completes (either successfully or via cancellation):

```markdown
# Test Loop Workflow Complete

The workflow has finished. Final state saved to:
- Current state: .claude/.test-loop-state.md
- Archived state: .claude/.test-loop-history/test-loop-{workflow_id}.md

{{if tests_generated}}
📁 Test files written to: .claude-tests/

{{if workflow_successful}}
✅ Workflow completed successfully!
{{else if workflow_cancelled}}
⚠️ Workflow was cancelled by user.
{{else if workflow_failed}}
❌ Workflow encountered errors. See state file for details.
{{endif}}

To resume this workflow later (if interrupted), use: /test-resume
{{endif}}
```

---

## Help Text

When user runs `/test-loop --help`:

```markdown
# /test-loop Command Help

**Description**: Human-in-the-loop testing workflow with approval gates

**Usage**: /test-loop [options] [path]

**Arguments**:
- path (optional): Directory or file to test. Default: workspace root

**Options**:
- --use-teams                Enable parallel team orchestration mode (default: false).
                             Loads teams/testing-parallel.md and uses the
                             team-orchestration skill for parallel agent execution.
                             Without this flag, the sequential test-loop-orchestrator
                             is used (backward compatible). See REQ-F-30.
- --analyze-model <model>    Override model for analyze-agent (opus, sonnet, haiku)
- --write-model <model>      Override model for write-agent (opus, sonnet, haiku)
- --execute-model <model>    Override model for execute-agent (opus, sonnet, haiku)
- --validate-model <model>   Override model for validate-agent (opus, sonnet, haiku)
- --fix-model <model>        Override model for fix-agent (opus, sonnet, haiku)
- --no-explore               Disable browser exploration for E2E tests (default: exploration
                             is on when app is accessible). Useful for CI or offline analysis.
- --explore                  Force-enable browser exploration in CI environments (CI=true).
                             No effect locally since exploration is on by default.
- --help, -h                 Show this help message

**What it does**:
1. 🔍 Analyzes code to identify test targets
2. 📋 Shows you a test plan for approval (Gate #1)
3. 📝 Generates test code for your review (Gate #2)
4. ⚡ Executes tests after your approval
5. 🔍 Validates results and categorizes failures
6. 🔄 Lets you decide: fix, iterate, or finish (Gate #3)

**Model Overrides**:
By default, each agent uses its configured model (from .dante.yml, environment, or
built-in defaults). Use --{agent}-model flags to override for a specific run.
Precedence: CLI flag > environment variable > .dante.yml config > built-in default.

**Approval Gates**:
- Gate #1: Review test plan before code generation
- Gate #2: Review test code before execution
- Gate #3: Decide how to handle results

**Features**:
- ✅ Full control with 3 approval gates
- ✅ Iterative refinement (max 3 iterations per gate)
- ✅ State persistence (resume with /test-resume)
- ✅ Error recovery and retry options
- ✅ Per-agent model overrides via CLI flags
- ✅ Optional parallel team orchestration via --use-teams

**Team Orchestration Mode (--use-teams)**:
When --use-teams is enabled, the command loads teams/testing-parallel.md and
invokes the team-orchestration skill. This spawns multiple agents in parallel
for faster test generation while preserving approval gates. Without this flag,
the command uses the original sequential test-loop-orchestrator (backward
compatible, REQ-NF-5).

**Comparison**:
- Use /test-loop for: Control, review, iteration
- Use /test-loop --use-teams for: Parallel execution with control
- Use /test-generate for: Speed, automation, trust AI

**Examples**:
```bash
# Interactive test loop for workspace
/test-loop

# Interactive test loop for directory
/test-loop src/

# Override validate-agent to use sonnet
/test-loop --validate-model=sonnet src/

# Override all agents to use opus
/test-loop --analyze-model=opus --write-model=opus --execute-model=opus --validate-model=opus --fix-model=opus src/

# Enable parallel team orchestration
/test-loop --use-teams src/

# Team mode with model overrides
/test-loop --use-teams --write-model=haiku src/

# Get help
/test-loop --help
```

**See also**:
- /test-generate - Fully automated test generation
- /test-analyze - Code analysis only
- /test-resume - Resume interrupted workflow
- /team-run - Direct team execution command
```

---

## Notes

### Integration with /test-resume

The `/test-loop` workflow saves state automatically, enabling seamless resumption:

```bash
# Start workflow
/test-loop src/

# Approve plan (Gate #1)
# Approve code (Gate #2)
# [System crashes during execution]

# Resume later
/test-resume

# Workflow continues from Phase 5 (Execution)
```

### State File Location

- **Active state**: `.claude/.test-loop-state.md`
- **Archived states**: `.claude/.test-loop-history/test-loop-{workflow_id}.md`

### Orchestrator Integration

This command is a thin wrapper that:
1. Validates arguments
2. Launches test-loop-orchestrator subagent
3. Displays completion message

All workflow logic lives in `subagents/test-loop-orchestrator.md`.

### E2E Tool Permissions (TASK-011)

When the orchestrator detects `test_type=e2e` (via framework detection or `--type e2e`), additional tool permissions are required for E2E operations. These permissions are enabled by the `Skill(test-engineering:e2e)` entry in `allowed-tools` above.

**E2E Framework CLI Permissions**:
- Execute E2E framework CLI commands (e.g., `npx playwright`, `npx cypress`, `pip show selenium`)
- Run browser installation checks (e.g., `npx playwright install --dry-run`)
- Run browser installation commands (e.g., `npx playwright install`)
- Parse E2E framework configuration files (e.g., `playwright.config.ts`, `cypress.config.js`)

**E2E Browser Permissions**:
- Launch browser processes for E2E test execution (managed by the E2E framework)
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

## Troubleshooting

**Problem**: Command doesn't start workflow
- **Solution**: Verify path exists, check for typos in path argument

**Problem**: Orchestrator times out
- **Solution**: Workflow automatically saves state, use `/test-resume` to continue

**Problem**: Can't find framework
- **Solution**: Orchestrator will prompt you to manually specify language and framework

**Problem**: Too many iterations
- **Solution**: After 3 iterations, you'll be prompted to proceed or cancel

**Problem**: Tests fail during execution
- **Solution**: Gate #3 gives you options: fix and retry, generate more, or accept as-is

**Problem**: `--use-teams` fails with "Team Definition Not Found"
- **Solution**: Ensure `teams/testing-parallel.md` exists in your project root. See `teams/example-parallel.md` for a template. Without this file, the team orchestration mode cannot be used. Remove `--use-teams` to use sequential mode instead.

---

## Summary

The `/test-loop` command provides **full human control** over test generation through three approval gates. Use it when you need:

- 📋 **Control**: Review plans before code generation
- 👀 **Visibility**: Inspect generated code before execution
- 🔄 **Iteration**: Refine tests based on feedback
- 💾 **Reliability**: Resume interrupted workflows

For fast, automated testing without approval gates, use `/test-generate` instead.
