---
description: "Resume an interrupted TDD workflow from saved state"
argument-hint: ""
allowed-tools: Skill(test-engineering:state-management), Skill(test-engineering:framework-detection), Skill(test-engineering:test-generation), Skill(test-engineering:templates), Skill(test-engineering:test-location-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:build-integration), Skill(test-engineering:linting), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection)
---

# /tdd-resume Command

**Description**: Resume an interrupted TDD workflow from saved state

**Usage**:
```
/tdd-resume
```

**Arguments**: None

**Options**:
- `--help, -h`: Display help information

**Examples**:
```bash
# Resume the most recent TDD workflow
/tdd-resume

# Get help
/tdd-resume --help
```

---

## Command Behavior

This command **resumes interrupted TDD workflows** by loading saved state and continuing from the interruption point. It works with workflows started via `/tdd`.

**What Gets Resumed**:
- Current workflow phase (RED/GREEN/REFACTOR and sub-phase)
- Requirements and spec file content
- Generated test files and stub files
- Implementation files
- Iteration counters and approval history
- Git branch context
- Auto mode and no-refactor flags

**When to Use**:
- Claude Code was closed mid-TDD-workflow
- You needed to pause and continue later
- Workflow was interrupted by error
- You want to continue an incomplete TDD cycle

**State File Location**: `.claude/.tdd-state-{workflow_id}.md` (one per TDD run)

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                   TDD RESUME WORKFLOW                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Find State Files
├─→ Glob for .claude/.tdd-state-*.md
├─→ If none found: Display error and exit
├─→ If one found: Auto-select it
└─→ If multiple found: Ask user which workflow to resume

Step 2: Load and Parse State
├─→ Read selected state file content
├─→ Parse YAML frontmatter (workflow_id, current_phase, etc.)
├─→ Parse markdown body (test files, stubs, implementation, results)
└─→ Validate state is valid and resumable

Step 3: Display Current Status
├─→ Show workflow ID and creation time
├─→ Show current TDD phase and progress
├─→ Show iteration counts
├─→ Show branch name
└─→ Ask user to confirm resumption

Step 4: Resume Orchestrator
├─→ Launch tdd-orchestrator subagent
├─→ Pass loaded state as context
├─→ Orchestrator continues from current_phase
└─→ Workflow proceeds normally with approval gates
```

---

## State File Structure

The state file (`.claude/.tdd-state-{workflow_id}.md`) contains:

### Frontmatter (YAML)
```yaml
---
workflow_id: "tdd-20260225-143022"
current_phase: "green_implement"
iteration: 1
status: "in_progress"
requirements: "Add a Calculator class with add, subtract, multiply, divide"
spec_file: null
auto_mode: false
no_refactor: false
target_path: "src/"
project_root: "/home/user/myproject"
created_at: "2026-02-25T14:30:22Z"
updated_at: "2026-02-25T14:35:18Z"
language: "python"
framework: "pytest"
test_directory: "/home/user/myproject/tests"
branch_name: "tdd/calculator-20260225-143022"
test_files:
  - "tests/test_calculator.py"
stub_files:
  - "src/calculator.py"
test_count: 12
target_module: "calculator"
---
```

### Body (Markdown)
- Progress checklist (which phases completed)
- Phase 1 results: Generated tests and stubs
- Phase 3 results: VERIFY RED classification
- Phase 4 results: Implementation
- Phase 5 results: VERIFY GREEN
- Phase 7 results: Refactoring changes
- User feedback history

---

## Resumable Phases

The TDD workflow can be resumed from any of these phases:

| Phase | State Value | Resumes At |
|-------|-------------|-----------|
| RED: Write Tests | `red_write_tests` | Writing tests from requirements |
| Test Review | `test_review` | Showing tests for approval |
| VERIFY RED | `verify_red` | Running tests to verify failures |
| GREEN: Implement | `green_implement` | Writing implementation |
| VERIFY GREEN | `verify_green` | Running tests to verify pass |
| Implementation Review | `impl_review` | Showing implementation for approval |
| REFACTOR | `refactor` | Improving code quality |
| VERIFY REFACTOR | `verify_refactor` | Running tests after refactoring |
| Iteration Decision | `iteration_decision` | Showing results for decision |

**Phases that cannot be resumed**:
- `completed` - Workflow already finished
- `cancelled` - Workflow was cancelled by user

---

## Example Resume Scenarios

### Scenario 1: Resume After Closing During GREEN Phase

```bash
# Start TDD workflow
/tdd "Add a Calculator class with add, subtract, multiply, divide"

# RED phase completes ✅
# Tests approved ✅
# VERIFY RED passes ✅
# GREEN phase starts...
# [You close Claude Code]

# Later, reopen Claude Code
/tdd-resume

# Output:
📂 Resuming TDD Workflow

**Workflow ID**: tdd-20260225-143022
**Started**: 2026-02-25 14:30:22 (15 minutes ago)
**Current Phase**: GREEN - Write Implementation (Phase 4/10)
**Status**: In progress
**Branch**: tdd/calculator-20260225-143022
**Requirements**: Add a Calculator class with add, subtract, multiply, divide

Progress:
- ✅ Phase 0: Setup
- ✅ Phase 1: 🔴 RED - Write Failing Tests (12 tests)
- ✅ Phase 2: Test Review - Approved
- ✅ Phase 3: 🔴 VERIFY RED - Correct failures confirmed
- ⏸️ Phase 4: 🟢 GREEN - Write Implementation - **IN PROGRESS**
- ⏳ Phase 5: 🟢 VERIFY GREEN
- ⏳ Phase 6: Implementation Review
- ⏳ Phase 7: 🔵 REFACTOR
- ⏳ Phase 8: 🔵 VERIFY REFACTOR
- ⏳ Phase 9: Iteration Decision

Resuming from Phase 4: GREEN - Write Implementation
```

### Scenario 2: Resume After Error in VERIFY RED

```bash
# VERIFY RED encounters test execution error
# Workflow saves state and exits

/tdd-resume

# Output shows the error and offers retry options
```

---

## Error Handling

### Error: No State File Found
```
❌ No TDD Workflow to Resume

No saved TDD workflow state found matching: .claude/.tdd-state-*.md

To start a new TDD workflow, use:
- /tdd [requirements] - TDD with natural language requirements
- /tdd --spec <path> - TDD from spec file

To see previous workflows:
- Check .claude/.tdd-history/ for archived states
```

### Error: Corrupted State File
```
❌ Invalid TDD Workflow State

The selected TDD state file is corrupted or invalid.

Error details: [parse error message]

Options:
1. 🔄 Start new TDD workflow with /tdd
2. 📂 Check archived states in .claude/.tdd-history/
3. 🛠️ Manually inspect state files in .claude/.tdd-state-*.md
```

### Error: Workflow Already Completed
```
✅ TDD Workflow Already Complete

The TDD workflow (tdd-20260225-143022) has already finished.

Status: Completed
Branch: tdd/calculator-20260225-143022

To start a new TDD workflow: /tdd [requirements]
```

### Error: Workflow Cancelled
```
❌ TDD Workflow Was Cancelled

The TDD workflow (tdd-20260225-143022) was cancelled.

To start a new TDD workflow: /tdd [requirements]
```

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/tdd-resume` command to resume an interrupted TDD workflow.

## Your Task

Load the saved TDD workflow state and resume the tdd-orchestrator from where it left off.

### Step 1: Find State Files

**Search for active TDD state files**:
```javascript
// Glob for all active TDD state files (one per workflow run)
const stateFiles = await Glob(".claude/.tdd-state-*.md");

if (stateFiles.length === 0) {
    displayNoWorkflowError();
    return;
}

let selectedStateFile;
if (stateFiles.length === 1) {
    // Single workflow - auto-select
    selectedStateFile = stateFiles[0];
} else {
    // Multiple concurrent workflows - ask user which to resume
    // Parse frontmatter from each to show summary (workflow_id, requirements, phase)
    const summaries = [];
    for (const file of stateFiles) {
        const content = await Read(file);
        const frontmatter = parseYamlFrontmatter(content);
        summaries.push({
            file: file,
            workflow_id: frontmatter.workflow_id,
            requirements: frontmatter.requirements,
            current_phase: frontmatter.current_phase,
            branch_name: frontmatter.branch_name,
            updated_at: frontmatter.updated_at
        });
    }

    // Use AskUserQuestion to let user pick
    const options = summaries.map(s => ({
        label: s.workflow_id,
        description: `${s.requirements} (phase: ${s.current_phase}, branch: ${s.branch_name})`
    }));

    const choice = await AskUserQuestion({
        questions: [{
            question: "Multiple TDD workflows found. Which would you like to resume?",
            header: "Select Workflow",
            multiSelect: false,
            options: options.slice(0, 4) // AskUserQuestion supports max 4 options
        }]
    });

    selectedStateFile = summaries.find(s => s.workflow_id === choice).file;
}
```

**If no state files found**: Display error message and exit.

### Step 2: Load and Parse State (SECURITY CRITICAL)

**Read state file** using Read tool.

**SECURITY - Validate State File**:
- Verify state file path is within workspace
- Check file permissions
- Validate file size (max 10MB)
- Sanitize any user feedback loaded from state

**Parse frontmatter** (YAML section between `---`):
Extract: `workflow_id`, `current_phase`, `iteration`, `status`, `requirements`,
`spec_file`, `auto_mode`, `no_refactor`, `target_path`, `project_root`,
`language`, `framework`, `test_directory`, `branch_name`, `test_files`,
`stub_files`, `test_count`, `target_module`

**Parse body**: Extract all phase results and context.

**Validate state**:
```javascript
if (status === "completed") {
    displayWorkflowAlreadyComplete(workflow_id);
    return;
}
if (status === "cancelled") {
    displayWorkflowCancelled(workflow_id);
    return;
}
```

### Step 3: Display Current Status

```markdown
# Resuming TDD Workflow

📂 **Workflow ID**: {{workflow_id}}
📅 **Started**: {{created_at}} ({{time_ago}})
📍 **Current Phase**: {{current_phase_display}}
📊 **Status**: {{status}}
🌿 **Branch**: {{branch_name}}
📋 **Requirements**: {{requirements_summary}}
{{if language}}🔤 **Language**: {{language}}{{endif}}
{{if framework}}🧪 **Framework**: {{framework}}{{endif}}

---

## Progress

{{phase_progress_checklist}}

---

Resuming from: {{current_phase_display}}
```

### Step 4: Checkout Branch and Resume Orchestrator

```javascript
// Ensure we're on the correct TDD branch
Bash(`git checkout ${branch_name}`);

// Launch tdd-orchestrator with resume context
Task({
    subagent_type: "general-purpose",
    description: "Resuming TDD workflow",
    prompt: `You are the tdd-orchestrator subagent. You are RESUMING an interrupted TDD workflow.

**IMPORTANT**: This is a RESUME operation, not a new workflow. Use the provided state to continue from where the workflow left off.

## Loaded State

**Workflow ID**: ${workflow_id}
**Current Phase**: ${current_phase}
**Iteration**: ${iteration}
**Status**: ${status}
**Requirements**: ${requirements}
**Auto Mode**: ${auto_mode}
**No Refactor**: ${no_refactor}
**Branch**: ${branch_name}
**Test Files**: ${test_files}
**Stub Files**: ${stub_files}

## Previous Results

${state_body}

## Your Task

Resume the TDD workflow from: ${current_phase}

**Phase Mapping**:
- "red_write_tests" → Launch tdd-spec-agent
- "test_review" → Show tests, ask for approval (Gate #1)
- "verify_red" → Launch execute-agent, classify failures
- "green_implement" → Launch tdd-implement-agent
- "verify_green" → Launch execute-agent, check passes
- "impl_review" → Show implementation, ask for approval (Gate #2)
- "refactor" → Launch tdd-refactor-agent
- "verify_refactor" → Launch execute-agent, auto-revert on failure
- "iteration_decision" → Show results, ask for decision (Gate #3)

**Instructions**:
1. Use loaded state for all previous results
2. Do NOT re-run completed phases
3. Continue from ${current_phase} exactly
4. Maintain iteration counters from state
5. Update state file after each phase
6. Handle errors gracefully
7. Respect auto_mode and no_refactor flags

Follow subagents/tdd-orchestrator.md, starting from ${current_phase}.

Execute the workflow now.`
})
```

---

## Help Text

When user runs `/tdd-resume --help`:

```markdown
# /tdd-resume Command Help

**Description**: Resume an interrupted TDD workflow

**Usage**: /tdd-resume

**What it does**:
1. 📂 Finds saved TDD state files matching .claude/.tdd-state-*.md
2. 📊 Displays current TDD phase and progress
3. 🌿 Checks out the TDD branch
4. ▶️ Resumes orchestrator from interruption point
5. ✅ Continues workflow with all context preserved

**When to use**:
- Claude Code was closed during a TDD workflow
- You need to continue a paused TDD cycle
- A TDD workflow was interrupted by error
- You want to finish an incomplete TDD cycle

**State persistence**:
- State files: .claude/.tdd-state-{workflow_id}.md (one per run)
- Archived states: .claude/.tdd-history/

**Resumable phases**:
- RED: Write tests, Test review, Verify RED
- GREEN: Write implementation, Verify GREEN, Implementation review
- REFACTOR: Refactoring, Verify refactor, Iteration decision

**Cannot resume**:
- Completed workflows (already finished)
- Cancelled workflows (use /tdd to start new)
- Workflows without state file

**Examples**:
```bash
# Resume most recent TDD workflow
/tdd-resume

# Get help
/tdd-resume --help
```

**See also**:
- /tdd - Start new TDD workflow
- /test-loop - Interactive test generation for existing code
- /test-resume - Resume interrupted test-loop workflow
```

---

## Integration with /tdd

The `/tdd` command automatically saves state after each phase, enabling seamless resumption:

```bash
# Start TDD workflow
/tdd "Add a Calculator class"

# Work through RED phase... ✅
# Approve tests... ✅
# [Claude Code crashes during GREEN phase]

# Resume later
/tdd-resume

# Continues from GREEN phase
```

**State is saved**:
- After every phase completes
- Before every approval gate
- After user provides feedback
- On error or timeout

---

## Troubleshooting

**Problem**: /tdd-resume says no workflow found
- **Solution**: Check if workflow completed or was cancelled. Look in `.claude/.tdd-history/` for archived states.

**Problem**: Resume starts from wrong phase
- **Solution**: State file might be corrupted. Start new workflow with `/tdd`.

**Problem**: Branch doesn't exist
- **Solution**: The TDD branch may have been deleted. The orchestrator will attempt to recreate it.

**Problem**: Can't resume completed workflow
- **Solution**: Completed workflows cannot be resumed. Use `/tdd` to start a new workflow.

---

## Summary

The `/tdd-resume` command enables **TDD workflow continuity** by:

- 📂 **Finding saved state** from `.claude/.tdd-state-{workflow_id}.md`
- 📊 **Displaying TDD progress** (RED/GREEN/REFACTOR phases)
- 🌿 **Checking out the TDD branch**
- ▶️ **Resuming orchestrator** from the exact interruption point
- ✅ **Preserving context** including requirements, tests, implementation, and feedback

Use `/tdd-resume` whenever a `/tdd` workflow is interrupted and you want to continue from where you left off.
