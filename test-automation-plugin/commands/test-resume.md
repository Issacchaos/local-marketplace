---
description: "Resume an interrupted test loop workflow from saved state"
argument-hint: ""
allowed-tools: Skill(test-engineering:state-management), Skill(test-engineering:framework-detection), Skill(test-engineering:test-generation), Skill(test-engineering:templates), Skill(test-engineering:test-location-detection), Skill(test-engineering:result-parsing), Skill(test-engineering:build-integration), Skill(test-engineering:linting), Skill(test-engineering:helper-extraction), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection)
---

# /test-resume Command

**Description**: Resume an interrupted test loop workflow from saved state

**Usage**:
```
/test-resume
```

**Arguments**: None

**Options**:
- `--help, -h`: Display help information

**Examples**:
```bash
# Resume the most recent workflow
/test-resume

# Get help
/test-resume --help
```

---

## Command Behavior

This command **resumes interrupted workflows** by loading saved state and continuing from the interruption point. It works with workflows started via `/test-loop`.

**What Gets Resumed**:
- Current workflow phase (where you left off)
- Test targets and analysis results
- Test plan (approved or pending approval)
- Generated test code (if any)
- Iteration counters
- User feedback history

**When to Use**:
- 💾 Claude Code was closed mid-workflow
- ⏸️ You needed to pause and continue later
- ❌ Workflow was interrupted by error
- 🔄 You want to continue an incomplete workflow

**State File Location**: `.claude/.test-loop-state.md`

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    RESUME WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

Step 1: Check for State File
├─→ Look for .claude/.test-loop-state.md
├─→ If not found: Display error and exit
└─→ If found: Proceed to Step 2

Step 2: Load and Parse State
├─→ Read state file content
├─→ Parse YAML frontmatter (workflow_id, current_phase, etc.)
├─→ Parse markdown body (analysis, plan, code, results)
└─→ Validate state is valid and resumable

Step 3: Display Current Status
├─→ Show workflow ID and creation time
├─→ Show current phase and progress
├─→ Show iteration counts
├─→ Show last update time
└─→ Ask user to confirm resumption

Step 4: Resume Orchestrator
├─→ Launch test-loop-orchestrator subagent
├─→ Pass loaded state as context
├─→ Orchestrator continues from current_phase
└─→ Workflow proceeds normally with approval gates
```

---

## State File Structure

The state file (`.claude/.test-loop-state.md`) contains:

### Frontmatter (YAML)
```yaml
---
workflow_id: "test-loop-20251208-143022"
current_phase: "code_approval"
iteration: 2
status: "awaiting_approval"
test_type: "unit"
target_path: "src/"
created_at: "2025-12-08T14:30:22Z"
updated_at: "2025-12-08T14:35:18Z"
language: "python"
framework: "pytest"
max_iterations: 3
---
```

### Body (Markdown)
- Workflow overview
- Progress checklist (which phases completed)
- Phase 1 results: Analysis
- Phase 2 results: Test plan
- Phase 3 results: Plan approval decision
- Phase 4 results: Generated tests
- Phase 5 results: Code approval decision
- Phase 6 results: Test execution
- Phase 7 results: Validation
- User feedback history
- Next steps

---

## Resumable Phases

The workflow can be resumed from any of these phases:

| Phase | Resumes At | What Happens Next |
|-------|-----------|-------------------|
| `plan_approval` | Waiting for test plan approval | Shows plan, asks for approval |
| `code_generation` | About to generate code | Generates test code from approved plan |
| `code_approval` | Waiting for code approval | Shows generated code, asks for approval |
| `test_execution` | About to execute tests | Runs tests (if code was approved) |
| `validation` | About to validate results | Analyzes test results |
| `iteration_decision` | Waiting for iteration decision | Shows results, asks what to do next |

**Phases that cannot be resumed**:
- `completed` - Workflow already finished
- `cancelled` - Workflow was cancelled by user
- `failed` - Workflow encountered fatal error (can be restarted from scratch)

---

## Example Resume Scenarios

### Scenario 1: Resume After Closing Claude Code

```bash
# Start workflow
/test-loop src/

# Analyze code... ✅
# Generate test plan... ✅
# Plan approval gate appears...
# [You close Claude Code to take a break]

# Later, reopen Claude Code
/test-resume

# Output:
📂 Resuming Workflow

**Workflow ID**: test-loop-20251208-143022
**Started**: 2025-12-08 14:30:22 (15 minutes ago)
**Current Phase**: Plan Approval (Phase 2/7)
**Status**: Awaiting user approval

Progress:
- ✅ Phase 1: Analysis - Complete
- ⏸️ Phase 2: Plan Approval - Awaiting approval
- ⏳ Phase 3: Code Generation - Not started
- ⏳ Phase 4: Code Approval - Not started
- ⏳ Phase 5: Execution - Not started
- ⏳ Phase 6: Validation - Not started
- ⏳ Phase 7: Iteration Decision - Not started

Resuming from Phase 2: Plan Approval

[Test plan is displayed]
Do you approve this test plan?
1. ✅ Approve
2. 🔄 Request Changes
3. ❌ Reject
```

### Scenario 2: Resume After Error During Execution

```bash
# Workflow reaches test execution...
# Error: pytest not installed
# Workflow saves state and exits

/test-resume

# Output:
📂 Resuming Workflow

**Workflow ID**: test-loop-20251208-150133
**Started**: 2025-12-08 15:01:33 (5 minutes ago)
**Current Phase**: Execution (Phase 5/7)
**Status**: Failed

Error encountered: pytest not installed

Would you like to:
1. 🔄 Retry - Try execution again (install pytest first)
2. 💾 Save and Exit - Fix issues and resume later
3. ❌ Cancel - Abandon this workflow
```

### Scenario 3: Resume After Timeout

```bash
# Analyze agent times out after 5 minutes...
# Workflow saves state

/test-resume

# Output:
📂 Resuming Workflow

**Workflow ID**: test-loop-20251208-144512
**Started**: 2025-12-08 14:45:12 (3 minutes ago)
**Current Phase**: Analysis (Phase 1/7)
**Status**: In Progress (timed out)

The Analyze agent timed out during execution.

Options:
1. 🔄 Retry with extended timeout (10 minutes)
2. 💾 Save and Exit
```

---

## Error Handling

### Error: No State File Found

**When**: No workflow to resume
```
❌ No Workflow to Resume

No saved workflow state found at: .claude/.test-loop-state.md

To start a new workflow, use:
- /test-loop [path] - Interactive workflow with approval gates
- /test-generate [path] - Fully automated workflow

To see previous workflows:
- Check .claude/.test-loop-history/ for archived states
```

### Error: Corrupted State File

**When**: State file exists but is invalid
```
❌ Invalid Workflow State

The state file at .claude/.test-loop-state.md is corrupted or invalid.

Error details: [parse error message]

Options:
1. 🔄 Start new workflow with /test-loop
2. 📂 Check archived states in .claude/.test-loop-history/
3. 🛠️ Manually inspect .claude/.test-loop-state.md
```

### Error: Workflow Already Completed

**When**: Trying to resume a finished workflow
```
✅ Workflow Already Complete

The workflow (test-loop-20251208-143022) has already finished.

Status: Completed
Finished at: 2025-12-08 14:45:30

To start a new workflow:
- /test-loop [path]

To view this workflow's state:
- Check .claude/.test-loop-history/test-loop-20251208-143022.md
```

### Error: Workflow Cancelled

**When**: Trying to resume a cancelled workflow
```
❌ Workflow Was Cancelled

The workflow (test-loop-20251208-143022) was cancelled by user.

Cancelled at: 2025-12-08 14:35:18
Phase: Plan Approval

To start a new workflow:
- /test-loop [path]
```

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/test-resume` command to resume an interrupted workflow.

## Your Task

Load the saved workflow state and resume the test-loop-orchestrator from where it left off.

### Step 1: Check for State File

**Check if state file exists**:
```javascript
// Use Read tool to check for state file
const stateFilePath = ".claude/.test-loop-state.md";

try {
  const stateContent = await Read(stateFilePath);
} catch (error) {
  // State file not found
  displayNoWorkflowError();
  return;
}
```

**If state file not found**:
```markdown
❌ No Workflow to Resume

No saved workflow state found at: .claude/.test-loop-state.md

To start a new workflow, use:
- /test-loop [path] - Interactive workflow with approval gates
- /test-generate [path] - Fully automated workflow

To see previous workflows, check: .claude/.test-loop-history/
```

**Exit if no state file**.

### Step 2: Load and Parse State (SECURITY CRITICAL)

**Read state file**:
Use Read tool to get contents of `.claude/.test-loop-state.md`.

**SECURITY - Validate State File** (See SECURITY.md):
- Verify state file path is within workspace
- Check file permissions (should be user-only)
- Validate file size (max 10MB to prevent DOS)
- Sanitize any user feedback loaded from state

**Parse frontmatter** (YAML section between `---`):
Extract these fields:
- `workflow_id`: Unique identifier
- `current_phase`: Where to resume
- `iteration`: Current iteration number
- `status`: Workflow status
- `test_type`: Type of tests (unit/integration/e2e)
- `target_path`: Target directory/file
- `created_at`: When workflow started
- `updated_at`: Last update time
- `language`: Detected language (if available)
- `framework`: Detected framework (if available)

**Parse body** (markdown content):
Extract all phase results, user feedback, and context.

**Validate state**:
```javascript
// Check if state is resumable
if (status === "completed") {
  displayWorkflowAlreadyComplete(workflow_id, updated_at);
  return;
}

if (status === "cancelled") {
  displayWorkflowCancelled(workflow_id, updated_at, current_phase);
  return;
}

// Valid resumable statuses: "in_progress", "awaiting_approval", "awaiting_decision", "failed"
```

### Step 3: Display Current Status

Show user the current workflow state:

```markdown
# Resuming Workflow

📂 **Workflow ID**: {{workflow_id}}
📅 **Started**: {{created_at}} ({{time_ago}})
📍 **Current Phase**: {{current_phase}} (Phase {{phase_number}}/7)
📊 **Status**: {{status}}
{{if language}}🐍 **Language**: {{language}}{{endif}}
{{if framework}}🧪 **Framework**: {{framework}}{{endif}}

---

## Progress

{{for phase in phases}}
{{if phase.completed}}
- ✅ Phase {{phase.number}}: {{phase.name}} - Complete
{{else if phase.current}}
- ⏸️ Phase {{phase.number}}: {{phase.name}} - **CURRENT** ({{phase.status}})
{{else}}
- ⏳ Phase {{phase.number}}: {{phase.name}} - Not started
{{endif}}
{{endfor}}

---

{{if status === "failed"}}
⚠️ **Error Encountered**: {{error_message}}
{{endif}}

Resuming from Phase {{phase_number}}: {{current_phase_name}}
```

### Step 4: Resume Orchestrator

**Launch test-loop-orchestrator with resume context**:

```javascript
Task({
  subagent_type: "general-purpose",
  description: "Resuming test loop workflow",
  prompt: `You are the test-loop-orchestrator subagent. You are RESUMING an interrupted workflow.

**IMPORTANT**: This is a RESUME operation, not a new workflow. Use the provided state to continue from where the workflow left off.

## Loaded State

**Workflow ID**: ${workflow_id}
**Current Phase**: ${current_phase}
**Iteration**: ${iteration}
**Status**: ${status}
**Target Path**: ${target_path}
**Test Type**: ${test_type}

## Previous Results

${state_body}

## Your Task

Resume the workflow from the current phase: ${current_phase}

**Phase Mapping**:
- "plan_approval" → Show test plan, ask for approval (Gate #1)
- "code_generation" → Launch write-agent with approved plan
- "code_approval" → Show generated code, ask for approval (Gate #2)
- "test_execution" → Write test files, launch execute-agent
- "validation" → Launch validate-agent, analyze results
- "iteration_decision" → Show results, ask for decision (Gate #3)

**Instructions**:
1. Use the loaded state context for all previous results
2. Do NOT re-run completed phases
3. Continue from ${current_phase} exactly
4. Maintain iteration counters from state
5. Update state file after each phase
6. Handle errors gracefully

Follow the complete workflow defined in subagents/test-loop-orchestrator.md, starting from ${current_phase}.

Execute the workflow now.`
})
```

### Step 5: Monitor Resumption

The orchestrator will:
- Load all previous context from state
- Skip completed phases
- Continue from current phase
- Maintain iteration counters
- Update state as workflow progresses

You do not need to do anything else - the orchestrator handles resumption.

---

## Help Text

When user runs `/test-resume --help`:

```markdown
# /test-resume Command Help

**Description**: Resume an interrupted test loop workflow

**Usage**: /test-resume

**What it does**:
1. 📂 Loads saved workflow state from .claude/.test-loop-state.md
2. 📊 Displays current progress and phase
3. ▶️ Resumes orchestrator from interruption point
4. ✅ Continues workflow with all context preserved

**When to use**:
- Claude Code was closed during a workflow
- You need to continue a paused workflow
- A workflow was interrupted by error
- You want to finish an incomplete workflow

**State persistence**:
- State file: .claude/.test-loop-state.md
- Archived states: .claude/.test-loop-history/

**Resumable phases**:
- Plan Approval (shows plan, asks for approval)
- Code Generation (generates tests)
- Code Approval (shows code, asks for approval)
- Test Execution (runs tests)
- Validation (analyzes results)
- Iteration Decision (asks what to do next)

**Cannot resume**:
- Completed workflows (already finished)
- Cancelled workflows (use /test-loop to start new)
- Workflows without state file

**Error handling**:
- No state file → Clear error message with guidance
- Corrupted state → Error with troubleshooting steps
- Already complete → Shows completion status
- Cancelled → Explains cancellation

**Examples**:
```bash
# Resume most recent workflow
/test-resume

# Get help
/test-resume --help
```

**See also**:
- /test-loop - Start new interactive workflow
- /test-generate - Start fully automated workflow
- /test-analyze - Analyze code only
```

---

## Integration with /test-loop

The `/test-loop` command automatically saves state after each phase, enabling seamless resumption:

```bash
# Start workflow
/test-loop src/

# Work through phases...
# Approve plan ✅
# [Claude Code crashes]

# Resume later
/test-resume

# Continues from where you left off
# Shows generated code for approval
```

**State is saved**:
- After every phase completes
- Before every approval gate
- After user provides feedback
- On error or timeout

---

## State File Location and Management

### Active State
**Location**: `.claude/.test-loop-state.md`
- Contains current/most recent workflow
- Updated in real-time as workflow progresses
- Used by `/test-resume`

### Archived States
**Location**: `.claude/.test-loop-history/test-loop-{workflow_id}.md`
- Created when workflow completes or is cancelled
- Preserves historical workflow information
- Can be manually inspected

### Example Directory Structure
```
.claude/
├── .test-loop-state.md              # Current workflow
└── .test-loop-history/
    ├── test-loop-20251208-143022.md # Completed workflow
    ├── test-loop-20251208-150133.md # Cancelled workflow
    └── test-loop-20251207-091544.md # Previous workflow
```

---

## Troubleshooting

**Problem**: /test-resume says no workflow found, but I just ran /test-loop
- **Solution**: Check if workflow completed or was cancelled. Look in `.claude/.test-loop-history/` for archived states.

**Problem**: Resume starts from wrong phase
- **Solution**: State file might be corrupted. Check `.claude/.test-loop-state.md` manually or start new workflow.

**Problem**: Resume shows old workflow from yesterday
- **Solution**: This is expected - state persists across sessions. To start new workflow, use `/test-loop`.

**Problem**: Can't resume completed workflow
- **Solution**: Completed workflows cannot be resumed. Use `/test-loop` to start a new workflow.

**Problem**: State file exists but command fails
- **Solution**: State file may be corrupted. Try starting new workflow or manually inspect/fix the YAML frontmatter.

---

## Notes

### When Resume Isn't Needed

You don't need `/test-resume` if:
- Workflow completed successfully
- You want to start a fresh workflow
- State file doesn't exist

In these cases, use `/test-loop` or `/test-generate` instead.

### State Persistence Strategy

The orchestrator uses **atomic writes** to prevent corruption:
1. Write to `.test-loop-state.tmp`
2. Rename to `.test-loop-state.md` (atomic operation)
3. If rename fails, old state is preserved

This ensures state file is never partially written or corrupted.

---

## Summary

The `/test-resume` command enables **workflow continuity** by:

- 📂 **Loading saved state** from `.claude/.test-loop-state.md`
- 📊 **Displaying progress** so you know where you left off
- ▶️ **Resuming orchestrator** from the exact interruption point
- ✅ **Preserving context** including analysis, plans, code, and user feedback

Use `/test-resume` whenever a `/test-loop` workflow is interrupted and you want to continue from where you left off.
