---
description: "Test-Driven Development workflow - write failing tests first, then implement, then refactor"
argument-hint: "[requirements] [options]"
allowed-tools: Skill(test-engineering:framework-detection), Skill(test-engineering:test-generation), Skill(test-engineering:templates), Skill(test-engineering:test-location-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:build-integration), Skill(test-engineering:linting), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection), Skill(test-engineering:state-management), Skill(test-engineering:team-orchestration)
---

# /tdd Command

**Description**: Test-Driven Development workflow following Red/Green/Refactor. Write failing tests first from requirements, then implement minimal code to pass them, then refactor for quality.

**Usage**:
```
/tdd [requirements] [options]
```

**Arguments**:
- `requirements` (optional): Natural language description of what to implement. If omitted, prompts interactively.

**Options**:
- `--spec <path>`: Path to a Markdown spec file containing requirements
- `--auto`: Skip all approval gates (fully automated TDD cycle)
- `--no-refactor`: Skip the refactoring phase
- `--use-teams` (boolean, default: false): Enable team orchestration mode. When true, loads `teams/tdd-workflow.md` and invokes the team-orchestration skill for coordinator-driven execution. When false (default), uses the existing sequential tdd-orchestrator subagent.
- `--tdd-spec-model <model>`: Override model for tdd-spec-agent (opus, sonnet, haiku)
- `--execute-model <model>`: Override model for execute-agent (opus, sonnet, haiku)
- `--tdd-implement-model <model>`: Override model for tdd-implement-agent (opus, sonnet, haiku)
- `--tdd-refactor-model <model>`: Override model for tdd-refactor-agent (opus, sonnet, haiku)
- `--help, -h`: Display help information

**Examples**:
```bash
# TDD with natural language requirements
/tdd "Add a Calculator class with add, subtract, multiply, divide"

# TDD from a spec file
/tdd --spec docs/calculator-spec.md

# Fully automated TDD (no approval gates)
/tdd --auto "Add input validation to the User class"

# TDD without refactoring phase
/tdd --no-refactor "Add a Stack data structure with push, pop, peek"

# Combined flags
/tdd --auto --no-refactor "Add a fibonacci function"

# With model overrides
/tdd --tdd-spec-model=opus "Add a binary search tree"

# Team orchestration mode (coordinator-driven TDD)
/tdd --use-teams "Add a Calculator class with add, subtract, multiply, divide"

# Team mode with auto and no-refactor
/tdd --use-teams --auto --no-refactor "Add a fibonacci function"

# Interactive mode (prompts for requirements)
/tdd
```

---

## Command Behavior

This command provides a **Test-Driven Development** workflow following the Red/Green/Refactor cycle. Unlike `/test-loop` which generates tests for existing code, `/tdd` writes tests FIRST from requirements, then implements the code.

**TDD Workflow Phases**:
1. **🔴 RED** - Write failing tests from requirements + create stubs
2. **✅ Test Review (Gate #1)** - Review generated tests [skipped with `--auto`]
3. **🔴 VERIFY RED** - Confirm tests fail for the right reasons
4. **🟢 GREEN** - Write minimal implementation to pass tests
5. **🟢 VERIFY GREEN** - Confirm all tests pass
6. **✅ Implementation Review (Gate #2)** - Review implementation [skipped with `--auto`]
7. **🔵 REFACTOR** - Improve code quality [skipped with `--no-refactor`]
8. **🔵 VERIFY REFACTOR** - Confirm tests still pass (auto-reverts on failure)
9. **✅ Iteration Decision (Gate #3)** - Done or add more [skipped with `--auto`]

**Key Characteristics**:
- Follows Red/Green/Refactor TDD discipline
- Tests are written FIRST from requirements (not from existing code)
- GREEN phase is fully automated (Dante writes the implementation)
- All work goes on a new git branch
- Three approval gates (skippable with `--auto`)
- State persistence enables resumption via `/tdd-resume`
- Supports natural language requirements and spec files

---

## Approval Gates

### Gate #1: Test Review
**When**: After tests are generated (RED phase)
**Skipped with**: `--auto`
**Purpose**: Review that tests correctly capture requirements

### Gate #2: Implementation Review
**When**: After implementation passes all tests (GREEN phase)
**Skipped with**: `--auto`
**Purpose**: Review that implementation is acceptable

### Gate #3: Iteration Decision
**When**: After all phases complete
**Skipped with**: `--auto` (auto-completes)
**Purpose**: Add more requirements or finish

---

## Comparison: /tdd vs /test-loop vs /test-generate

| Feature | /tdd | /test-loop | /test-generate |
|---------|------|-----------|---------------|
| **Approach** | Tests FIRST (TDD) | Tests for existing code | Tests for existing code |
| **Input** | Requirements | Existing code | Existing code |
| **Writes Implementation** | Yes (GREEN phase) | No | No |
| **Refactoring** | Yes (optional) | No | No |
| **Approval Gates** | 3 (skippable) | 3 | None |
| **Git Branch** | Auto-creates | No | No |
| **Resumable** | Yes (/tdd-resume) | Yes (/test-resume) | No |
| **Team Mode** | Yes (--use-teams) | Yes (--use-teams) | No |

**When to use /tdd**:
- Starting new features from requirements
- You want to follow TDD discipline
- You want Dante to write both tests AND implementation
- You have a spec file or clear requirements

**When to use /test-loop**:
- You have existing code that needs tests
- You want to review test plans and generated tests
- You want control over what gets tested

**When to use /test-generate**:
- You want fast, automated test generation for existing code
- No approval gates needed

---

## State Persistence and Resumption

The `/tdd` workflow **automatically saves state** after each phase to `.claude/.tdd-state-{workflow_id}.md`. Each run gets its own state file, so you can run multiple TDD workflows concurrently (e.g., implementing two features at once).

**Resume with**: `/tdd-resume`

```bash
# Start TDD workflow
/tdd "Add a Calculator class"

# ... work through phases ...
# [interrupted]

# Resume later
/tdd-resume
```

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/tdd` command for Test-Driven Development.

## Your Task

Launch the tdd-orchestrator subagent to guide the TDD Red/Green/Refactor workflow.

### Step 1: Parse Arguments and Validate (SECURITY CRITICAL)

**Parse Arguments**:
```javascript
// Extract requirements and options from user command
const args = parseCommandArgs(userInput);
const requirements = args.requirements || null;
const specFile = args['spec'] || null;
const autoMode = args['auto'] === true;
const noRefactor = args['no-refactor'] === true;
const useTeams = args['use-teams'] === true;

// Parse model override flags
const cli_overrides = {};
if (args['tdd-spec-model']) cli_overrides['tdd-spec'] = args['tdd-spec-model'];
if (args['execute-model']) cli_overrides['execute'] = args['execute-model'];
if (args['tdd-implement-model']) cli_overrides['tdd-implement'] = args['tdd-implement-model'];
if (args['tdd-refactor-model']) cli_overrides['tdd-refactor'] = args['tdd-refactor-model'];
```

**Validate (SECURITY REQUIREMENTS)**:
- If `--spec` provided:
  - Remove null bytes from path
  - Check path length (max 4096 characters)
  - Resolve to absolute path
  - Verify path is within workspace boundaries (prevent directory traversal)
  - Check file exists (use Glob or Read)
  - If validation fails, display error and STOP

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

**Handle missing requirements**:
If no requirements and no `--spec` file provided, prompt the user:
```javascript
if (!requirements && !specFile) {
    // Use AskUserQuestion to get requirements interactively
    const response = AskUserQuestion({
        questions: [{
            question: "What would you like to implement? Describe the features, classes, and functions.",
            header: "Requirements",
            multiSelect: false,
            options: [
                {
                    label: "Enter requirements",
                    description: "Type your requirements in natural language"
                },
                {
                    label: "Provide spec file",
                    description: "Specify a path to a Markdown spec file"
                }
            ]
        }]
    });
    // Use the response to set requirements or specFile
}
```

**Display Start Message**:
```markdown
# Starting TDD Workflow (Red/Green/Refactor)

**Requirements**: {{requirements_summary}}
{{if specFile}}**Spec File**: {{specFile}}{{endif}}
**Mode**: {{autoMode ? 'Automatic (no approval gates)' : 'Interactive (with approval gates)'}}
{{if useTeams}}**Orchestration**: Team mode (teams/tdd-workflow.md){{endif}}
{{if noRefactor}}**Refactoring**: Disabled{{endif}}
{{if cli_overrides}}**Model Overrides**: {{cli_overrides}}{{endif}}

This workflow follows Test-Driven Development:
1. 🔴 RED: Write failing tests from requirements
2. 🟢 GREEN: Write minimal implementation to pass tests
3. 🔵 REFACTOR: Improve code quality (keeping tests green)

{{if !autoMode}}
Approval gates:
- 📋 Gate #1: Test Review (after RED)
- 📝 Gate #2: Implementation Review (after GREEN)
- 🔄 Gate #3: Iteration Decision (after REFACTOR)
{{endif}}

State will be saved automatically for resumption via /tdd-resume.

---
```

### Step 2: Route to Sequential or Team Orchestration Mode

Based on the `--use-teams` flag, route to the appropriate orchestration mode:

```javascript
if (useTeams) {
    // =====================================================================
    // TEAM ORCHESTRATION MODE
    // When --use-teams=true, load the tdd-workflow team definition
    // and invoke the team-orchestration skill for coordinator-driven execution.
    // =====================================================================

    // Step 2a: Verify tdd-workflow team definition exists
    const teamDefPath = 'teams/tdd-workflow.md';
    const teamDefExists = fileExists(teamDefPath);

    if (!teamDefExists) {
        // Display error and STOP - team definition not found
        displayError(`
❌ Error: Team Definition Not Found

The --use-teams flag requires the tdd-workflow team definition at:
  ${teamDefPath}

This file defines the TDD agent composition, dependency chain, and
coordinator logic for team-based TDD orchestration.

To resolve:
1. Create the team definition at teams/tdd-workflow.md
2. Or run without --use-teams to use sequential mode:
   /tdd ${requirements}

See teams/tdd-workflow.md for the team definition.
`);
        return; // STOP execution
    }

    // Step 2b: Invoke team-orchestration skill
    // Read and follow skills/team-orchestration/SKILL.md
    // This skill handles the full lifecycle: load team definition,
    // approval gates, agent spawning, lifecycle tracking, result
    // aggregation, and telemetry logging.
    execute_team({
        team_name: 'tdd-workflow',
        project_root: getWorkspaceRoot(),
        config_overrides: {
            // Pass any relevant CLI overrides to the team
            approval_gates: autoMode ? { disabled: true } : null,  // Auto mode disables gates
            telemetry_enabled: null  // Use team definition defaults
        },
        context: {
            requirements: requirements,
            spec_file: specFile,
            additional_args: {
                cli_model_overrides: cli_overrides,
                workflow_type: 'tdd',
                auto_mode: autoMode,
                no_refactor: noRefactor
            },
            depth: 1,
            parent_id: null
        }
    });

    // The team-orchestration skill handles everything from here:
    // - Loads teams/tdd-workflow.md (team definition + coordinator)
    // - Coordinator (teams/tdd-workflow-coordinator.md) manages TDD phases
    // - Spawns agents in dependency order: tdd-spec → execute → tdd-implement → execute → tdd-refactor → execute
    // - Handles phase-specific logic (failure classification, auto-revert)
    // - Presents execution plan for approval (if gates enabled)
    // - Aggregates results from all phases
    // See skills/team-orchestration/SKILL.md for the full algorithm.

} else {
    // =====================================================================
    // SEQUENTIAL MODE (default)
    // Default behavior: use existing tdd-orchestrator subagent.
    // This is the original sequential workflow, unchanged for backward
    // compatibility.
    // =====================================================================

    // Continue to Step 3 (Launch TDD Orchestrator Subagent)
}
```

### Step 3: Launch TDD Orchestrator Subagent (Sequential Mode)

Use the **Task tool** to launch the tdd-orchestrator:

```javascript
Task({
    subagent_type: "general-purpose",
    description: "Running TDD workflow",
    prompt: `You are the tdd-orchestrator subagent. Execute the TDD Red/Green/Refactor workflow.

**Requirements**: ${requirements || '(from spec file)'}
${specFile ? `**Spec File**: ${specFile}` : ''}
**Auto Mode**: ${autoMode}
**No Refactor**: ${noRefactor}
**Workflow ID**: tdd-${timestamp}
**CLI Model Overrides**: ${JSON.stringify(cli_overrides)}

Follow the complete 10-phase workflow defined in subagents/tdd-orchestrator.md:

Phase 0: Setup (project detection, framework detection, model selection)
Phase 1: RED - Write failing tests (launch tdd-spec-agent)
Phase 2: Test Review (approval gate, ${autoMode ? 'SKIP - auto mode' : 'ask user'})
Phase 3: VERIFY RED - Confirm correct failures (launch execute-agent)
Phase 4: GREEN - Write implementation (launch tdd-implement-agent)
Phase 5: VERIFY GREEN - Confirm tests pass (launch execute-agent)
Phase 6: Implementation Review (approval gate, ${autoMode ? 'SKIP - auto mode' : 'ask user'})
Phase 7: REFACTOR - Improve quality (${noRefactor ? 'SKIP - --no-refactor' : 'launch tdd-refactor-agent'})
Phase 8: VERIFY REFACTOR - Confirm still green (${noRefactor ? 'SKIP' : 'launch execute-agent'})
Phase 9: Iteration Decision (${autoMode ? 'SKIP - auto-complete' : 'ask user'})

**Important**:
- Save state to .claude/.tdd-state-{workflow_id}.md after each phase
- Use AskUserQuestion tool for all approval gates (unless auto mode)
- Create a new git branch for TDD work
- Support max 3 iterations per retry loop
- Handle errors gracefully
- Display clear progress indicators with TDD phase colors (🔴🟢🔵)

Execute the workflow now.`
})
```

### Step 4: Workflow Completion

When the orchestrator (sequential or team) completes:

```markdown
# TDD Workflow Complete

{{if workflow_successful}}
✅ TDD workflow completed successfully!

**Summary**:
- 🔴 Tests written: {{test_count}}
- 🟢 Functions implemented: {{functions_implemented}}
- 🔵 Refactoring changes: {{changes_applied}}
- Branch: {{branch_name}}

**Files created/modified**:
{{file_list}}

**Next steps**:
- Review the changes on branch `{{branch_name}}`
- Merge to your main branch when ready
- Run `/tdd-resume` if you want to add more requirements
{{else if workflow_cancelled}}
⚠️ TDD workflow was cancelled.
{{else if workflow_failed}}
❌ TDD workflow encountered errors. See state file for details.
{{endif}}

State saved to: .claude/.tdd-state-{{workflow_id}}.md
To resume: /tdd-resume
```

---

## Help Text

When user runs `/tdd --help`:

```markdown
# /tdd Command Help

**Description**: Test-Driven Development - write tests first, then implement

**Usage**: /tdd [requirements] [options]

**What it does**:
1. 🔴 RED: Writes failing tests from your requirements
2. 🟢 GREEN: Implements minimal code to pass tests
3. 🔵 REFACTOR: Improves code quality (optional)

**Arguments**:
- requirements (optional): Natural language description. Prompts if omitted.

**Options**:
- --spec <path>        Path to Markdown spec file with requirements
- --auto               Skip all approval gates (fully automated)
- --no-refactor        Skip the refactoring phase
- --use-teams          Enable team orchestration mode (coordinator-driven)
- --tdd-spec-model     Override model for test writing (opus, sonnet, haiku)
- --execute-model      Override model for test execution (opus, sonnet, haiku)
- --tdd-implement-model Override model for implementation (opus, sonnet, haiku)
- --tdd-refactor-model Override model for refactoring (opus, sonnet, haiku)
- --help, -h           Show this help message

**Examples**:
```bash
# Natural language requirements
/tdd "Add a Calculator class with add, subtract, multiply, divide"

# From spec file
/tdd --spec docs/calculator-spec.md

# Fully automated
/tdd --auto "Add input validation to User class"

# Skip refactoring
/tdd --no-refactor "Add fibonacci function"

# Team orchestration mode
/tdd --use-teams "Add a Calculator class"

# Interactive (prompts for requirements)
/tdd

# Get help
/tdd --help
```

**Comparison**:
- /tdd: Tests FIRST, then implement (TDD)
- /test-loop: Tests for EXISTING code (interactive)
- /test-generate: Tests for EXISTING code (automated)

**See also**:
- /tdd-resume - Resume interrupted TDD workflow
- /test-loop - Interactive test generation for existing code
- /test-generate - Automated test generation for existing code
```

---

## Troubleshooting

**Problem**: Command doesn't start workflow
- **Solution**: Provide requirements via text or `--spec` file. If neither, the command prompts interactively.

**Problem**: Spec file not found
- **Solution**: Check the path is correct and the file exists. Use absolute or workspace-relative paths.

**Problem**: Tests all pass in RED phase
- **Solution**: This means stubs are satisfying tests or module already has implementation. Review tests to ensure they properly assert on expected behavior.

**Problem**: Implementation doesn't pass all tests
- **Solution**: The orchestrator retries up to 3 times. If still failing, review the requirements and tests for clarity.

**Problem**: Refactoring breaks tests
- **Solution**: The orchestrator automatically reverts refactoring changes. Implementation from GREEN phase is preserved.

**Problem**: Want to resume interrupted workflow
- **Solution**: Use `/tdd-resume` to continue from where you left off.

---

## Summary

The `/tdd` command provides **Test-Driven Development** workflow:

- 🔴 **RED**: Write failing tests from requirements
- 🟢 **GREEN**: Implement minimal code to pass tests
- 🔵 **REFACTOR**: Improve quality while keeping tests green

Use `/tdd` when you want AI-assisted TDD for new features. Use `--auto` for fully automated TDD cycles, or interact through 3 approval gates for full control. Use `--use-teams` to leverage team orchestration with a coordinator-driven workflow (see `teams/tdd-workflow.md`).
