---
name: approval-gate-handler
description: Pause execution at configurable approval gates (before_execution, after_completion), present plans/results to users, and handle approval/reject/modify responses with iteration support.
user-invocable: false
---

# Approval Gate Handler Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Manage user approval gates for team orchestration with iterative feedback support

**Used By**: Team Orchestration SKILL, Team Coordinators

---

## Overview

The Approval Gate Handler Skill provides configurable approval checkpoints in team orchestration workflows. It pauses execution to present plans or results to users and handles their approval decisions (Approve, Reject, or Modify with feedback).

This skill is critical for:
- **User Control**: Ensuring users can review and approve execution plans before resource-intensive operations
- **Quality Assurance**: Allowing users to catch issues before agent spawning or after completion
- **Iterative Refinement**: Supporting feedback loops with up to 3 modification attempts per gate

### Key Principle

Approval gates are **user-facing decision points**, not implementation details. They must present clear context, actionable options, and graceful handling of all response types.

---

## Skill Interface

### Input

```yaml
gate_type: Type of approval gate (before_execution | after_completion | disabled)
coordinator_id: Unique identifier for the coordinator requesting approval
team_config: Team configuration dict with approval_gates settings
plan_or_results: Dict containing plan details (for before_execution) or results (for after_completion)
iteration_count: Current iteration count for this gate (default: 0)
max_iterations: Maximum allowed iterations (default: 3)
```

### Output

```yaml
# Success case
decision: string  # "approve", "reject", or "modify"
feedback: string | null  # User feedback text (only for "modify")
iteration: integer  # Updated iteration count

# Bypass case (gate disabled)
decision: "approve"
bypassed: true
reason: "gates_disabled" | "gate_type_disabled"

# Error case
decision: "reject"
error: string  # Error message
```

---

## Gate Types

### Gate Type 1: before_execution (REQ-F-17, REQ-F-18)

**When**: After coordinator creates execution plan, before spawning agents

**Purpose**: User reviews proposed parallelization strategy, agent composition, and estimated resource usage

**Configuration**:
```yaml
approval_gates:
  before_execution: true  # Enable before-execution gate
```

**Typical Use Cases**:
- Review parallel agent batching strategy
- Validate estimated execution time and resource usage
- Approve agent count and composition before spawning
- Ensure plan aligns with user expectations

---

### Gate Type 2: after_completion (REQ-F-17, REQ-F-18)

**When**: After all agents complete, before finalizing workflow

**Purpose**: User reviews aggregated results and decides whether to accept, iterate, or discard

**Configuration**:
```yaml
approval_gates:
  after_completion: true  # Enable after-completion gate
```

**Typical Use Cases**:
- Review generated test files and decide whether to keep them
- Validate documentation quality before finalizing
- Inspect debug analysis results before taking action
- Ensure results meet quality standards

---

### Gate Type 3: disabled (REQ-F-17, REQ-F-20)

**When**: Gates are bypassed entirely for fully autonomous execution

**Purpose**: Allow teams to run without user interaction for batch processing or CI/CD pipelines

**Configuration**:
```yaml
approval_gates:
  disabled: true  # Skip all gates (fully autonomous)
```

**Typical Use Cases**:
- CI/CD automated testing pipelines
- Batch processing multiple projects
- Internal plugin development workflows with trusted inputs
- Re-running workflows with previously approved configurations

---

## Approval Prompt Formats

### Before Execution Prompt (REQ-F-18)

Present execution plan with clear structure:

```markdown
# {Team Name}: Proposed Execution Plan

## Overview
- **Team Type**: {team_name}
- **Target**: {target_path or description}
- **Coordinator**: {coordinator_id}

## Agent Composition
The coordinator identified **{total_targets}** targets grouped into **{batch_count}** independent batches:

{for each batch:}
**Batch {batch_number}** ({target_count} targets):
- {target_1}
- {target_2}
- ...

## Proposed Parallelization
- **Agents to Spawn**: {agent_count} agents simultaneously
- **Max Agent Limit**: {max_agents}
- **Estimated Time**: {estimated_minutes} minutes (vs {sequential_minutes} minutes sequential)
- **Speedup**: ~{speedup_percentage}%

## Dependencies
{if dependencies exist:}
- Phase 1 (Sequential): {phase_1_agents}
- Phase 2 (Parallel): {phase_2_agents} (waits for Phase 1)
- Phase 3 (Sequential): {phase_3_agents} (waits for Phase 2)
{else:}
No dependencies - all agents can run in parallel

## Resource Usage
- **Active Agents**: {agent_count} of {max_agents} max
- **Estimated Tokens**: {estimated_tokens} (if available)
- **Timeout**: {timeout_minutes} minutes

---

## Approval Decision

Do you approve this execution plan?

**Options**:
1. **Approve** - Execute plan as proposed
2. **Modify** - Provide feedback to adjust plan (max {max_iterations} iterations)
3. **Reject** - Cancel team execution
```

**Example**:
```
# Testing Team: Proposed Execution Plan

## Overview
- **Team Type**: testing-parallel
- **Target**: src/
- **Coordinator**: testing-coordinator-20260213-143000

## Agent Composition
The coordinator identified **12** targets grouped into **3** independent batches:

**Batch 1** (5 targets):
- src/user_service.py (UserService class)
- src/auth/login.py (login function)
- src/auth/logout.py (logout function)
- src/validators/email.py (validate_email)
- src/validators/phone.py (validate_phone)

**Batch 2** (4 targets):
- src/calculator.py (Calculator class)
- src/validators.py (validate_input)
- src/formatters.py (format_output)
- src/converters.py (convert_units)

**Batch 3** (3 targets):
- src/api/endpoints.py (API endpoints)
- src/api/middleware.py (middleware functions)
- src/api/responses.py (response formatters)

## Proposed Parallelization
- **Agents to Spawn**: 3 write-agents simultaneously
- **Max Agent Limit**: 5
- **Estimated Time**: 2 minutes (vs 6 minutes sequential)
- **Speedup**: ~67%

## Dependencies
- Phase 1 (Sequential): analyze-agent (must complete first)
- Phase 2 (Parallel): write-agent-1, write-agent-2, write-agent-3 (waits for Phase 1)
- Phase 3 (Sequential): execute-agent, validate-agent (waits for Phase 2)

## Resource Usage
- **Active Agents**: 3 of 5 max
- **Estimated Tokens**: ~15,000
- **Timeout**: 30 minutes

---

## Approval Decision

Do you approve this execution plan?

**Options**:
1. **Approve** - Execute plan as proposed
2. **Modify** - Provide feedback to adjust plan (max 3 iterations)
3. **Reject** - Cancel team execution
```

---

### After Completion Prompt

Present results with clear summary:

```markdown
# {Team Name}: Execution Results

## Overview
- **Team Type**: {team_name}
- **Coordinator**: {coordinator_id}
- **Status**: {status}
- **Duration**: {duration_seconds} seconds

## Agent Results
{for each agent:}
**{agent_id}** ({agent_type}):
- **Status**: {status} (Completed / Failed)
- **Duration**: {duration_seconds}s
- **Output Summary**: {output_summary}
{if failed:}
  - **Error**: {error_message}

## Aggregated Results
{team-specific results, e.g.:}
- **Tests Generated**: {test_count} tests across {file_count} files
- **Pass Rate**: {pass_rate}% ({passed}/{total})
- **Coverage**: {coverage}%

## Generated Artifacts
{list of files created or modified:}
- {file_1} ({line_count} lines, {artifact_description})
- {file_2} ({line_count} lines, {artifact_description})

---

## Next Steps

How would you like to proceed?

**Options**:
1. **Accept** - Keep results and complete workflow
2. **Iterate** - Provide feedback to regenerate (max {max_iterations} iterations)
3. **Discard** - Cancel workflow and discard results
```

**Example**:
```
# Testing Team: Execution Results

## Overview
- **Team Type**: testing-parallel
- **Coordinator**: testing-coordinator-20260213-143000
- **Status**: Completed
- **Duration**: 125 seconds

## Agent Results

**write-agent-1** (agents/write-agent.md):
- **Status**: Completed
- **Duration**: 28s
- **Output Summary**: 5 tests generated for Batch 1

**write-agent-2** (agents/write-agent.md):
- **Status**: Completed
- **Duration**: 32s
- **Output Summary**: 4 tests generated for Batch 2

**write-agent-3** (agents/write-agent.md):
- **Status**: Completed
- **Duration**: 25s
- **Output Summary**: 3 tests generated for Batch 3

**execute-agent** (agents/execute-agent.md):
- **Status**: Completed
- **Duration**: 15s
- **Output Summary**: 12 tests executed, 10 passed, 2 failed

**validate-agent** (agents/validate-agent.md):
- **Status**: Completed
- **Duration**: 18s
- **Output Summary**: 2 test bugs identified, both in newly generated tests

## Aggregated Results
- **Tests Generated**: 12 tests across 3 files
- **Pass Rate**: 83% (10/12)
- **Coverage**: 78%

## Generated Artifacts
- tests/test_user_service.py (145 lines, 5 tests)
- tests/test_calculator.py (98 lines, 4 tests)
- tests/test_api_endpoints.py (67 lines, 3 tests)

---

## Next Steps

How would you like to proceed?

**Options**:
1. **Accept** - Keep results and complete workflow
2. **Iterate** - Provide feedback to regenerate (max 3 iterations)
3. **Discard** - Cancel workflow and discard results
```

---

## Decision Handling (REQ-F-19)

### Decision: Approve

**User Action**: User selects "Approve" or "Accept"

**Handler Behavior**:
1. Log approval event to telemetry: `plan_approved` or `results_accepted`
2. Return decision: `{"decision": "approve", "iteration": current_iteration}`
3. Coordinator continues execution

**Example Telemetry**:
```jsonl
{"timestamp":"2026-02-13T14:30:15.789Z","event_type":"coordination","agent_id":"testing-coordinator","status":"plan_approved","gate":"before_execution","iteration":1,"user_response":"approve"}
```

---

### Decision: Reject

**User Action**: User selects "Reject" or "Cancel" or "Discard"

**Handler Behavior**:
1. Log rejection event to telemetry: `plan_rejected` or `results_rejected`
2. Return decision: `{"decision": "reject", "reason": "user_rejected"}`
3. Coordinator aborts team execution (no agents spawned or results discarded)

**Example Telemetry**:
```jsonl
{"timestamp":"2026-02-13T14:30:15.789Z","event_type":"coordination","agent_id":"testing-coordinator","status":"plan_rejected","gate":"before_execution","iteration":1,"user_response":"reject"}
```

**User Message**:
```
Team execution cancelled by user.
No agents were spawned.
```

---

### Decision: Modify (REQ-F-19)

**User Action**: User selects "Modify" or "Request Changes" or "Iterate"

**Handler Behavior**:
1. Prompt user for feedback text
2. Log modification request to telemetry: `plan_modification_requested` or `results_iteration_requested`
3. Increment iteration count
4. Check iteration limit:
   - If `iteration < max_iterations`: Return `{"decision": "modify", "feedback": user_feedback, "iteration": iteration + 1}`
   - If `iteration >= max_iterations`: Display error, ask user to approve/reject instead
5. Coordinator regenerates plan/results with feedback

**Feedback Prompt**:
```markdown
## Modification Requested (Iteration {iteration} of {max_iterations})

Please provide feedback to adjust the {plan/results}:

**Examples**:
- "Reduce agent count to 2 instead of 3"
- "Focus on high-priority targets only"
- "Increase coverage threshold to 90%"
- "Regenerate tests with more edge cases"

**Your Feedback**:
[User enters free-form text]
```

**Example Telemetry**:
```jsonl
{"timestamp":"2026-02-13T14:30:15.789Z","event_type":"coordination","agent_id":"testing-coordinator","status":"plan_modification_requested","gate":"before_execution","iteration":1,"feedback":"Reduce to 2 batches instead of 3"}
```

**Max Iterations Handling**:
```
Maximum iterations reached ({max_iterations}).

You have two options:
1. **Approve** the current plan as-is
2. **Reject** to cancel execution

Further modifications are not available after {max_iterations} iterations.
```

---

## Bypass Logic (REQ-F-20)

### Bypass Scenario 1: All Gates Disabled

**Configuration**:
```yaml
approval_gates:
  disabled: true
```

**Handler Behavior**:
1. Log bypass event to telemetry: `approval_bypassed`
2. Return immediately: `{"decision": "approve", "bypassed": true, "reason": "gates_disabled"}`
3. No user interaction

**Example Telemetry**:
```jsonl
{"timestamp":"2026-02-13T14:30:15.789Z","event_type":"coordination","agent_id":"testing-coordinator","status":"approval_bypassed","gate":"before_execution","reason":"gates_disabled"}
```

---

### Bypass Scenario 2: Specific Gate Disabled

**Configuration**:
```yaml
approval_gates:
  before_execution: false  # This gate disabled
  after_completion: true   # Other gates may still be enabled
  disabled: false
```

**Handler Behavior**:
1. Check `approval_gates[gate_type]` value
2. If `false`: Log bypass event, return `{"decision": "approve", "bypassed": true, "reason": "gate_type_disabled"}`
3. No user interaction

**Example Telemetry**:
```jsonl
{"timestamp":"2026-02-13T14:30:15.789Z","event_type":"coordination","agent_id":"testing-coordinator","status":"approval_bypassed","gate":"before_execution","reason":"gate_type_disabled"}
```

---

## Implementation Patterns

### Pattern 1: Request Before Execution Approval

```python
def request_before_execution_approval(coordinator_id: str, team_config: dict, plan: dict, iteration: int = 0) -> dict:
    """
    Request user approval for execution plan before spawning agents.

    Args:
        coordinator_id: Unique identifier for coordinator
        team_config: Team configuration with approval_gates settings
        plan: Execution plan dict with batch_count, agent_count, estimated_time, etc.
        iteration: Current iteration count (default: 0)

    Returns:
        dict with decision, feedback (if modify), and iteration
    """
    max_iterations = 3

    # Check if gates are bypassed (REQ-F-20)
    approval_gates = team_config.get('approval_gates', {})

    if approval_gates.get('disabled', False):
        # All gates disabled - bypass
        log_telemetry("coordination", coordinator_id, "approval_bypassed", {
            "gate": "before_execution",
            "reason": "gates_disabled"
        })
        return {"decision": "approve", "bypassed": True, "reason": "gates_disabled"}

    if not approval_gates.get('before_execution', True):
        # This specific gate disabled - bypass
        log_telemetry("coordination", coordinator_id, "approval_bypassed", {
            "gate": "before_execution",
            "reason": "gate_type_disabled"
        })
        return {"decision": "approve", "bypassed": True, "reason": "gate_type_disabled"}

    # Format approval prompt
    prompt = format_before_execution_prompt(
        team_name=team_config['name'],
        coordinator_id=coordinator_id,
        plan=plan,
        max_iterations=max_iterations
    )

    # Display prompt to user
    display_approval_prompt(prompt)

    # Get user decision
    # NOTE: In practice, orchestrator will use AskUserQuestion tool
    # This is a conceptual example of the flow
    user_response = get_user_decision(options=["Approve", "Modify", "Reject"])

    if user_response == "Approve":
        # User approved - continue execution
        log_telemetry("coordination", coordinator_id, "plan_approved", {
            "gate": "before_execution",
            "iteration": iteration,
            "user_response": "approve"
        })
        return {"decision": "approve", "iteration": iteration}

    elif user_response == "Reject":
        # User rejected - abort execution
        log_telemetry("coordination", coordinator_id, "plan_rejected", {
            "gate": "before_execution",
            "iteration": iteration,
            "user_response": "reject"
        })
        return {"decision": "reject", "reason": "user_rejected"}

    elif user_response == "Modify":
        # User wants to modify plan - get feedback

        # Check iteration limit
        if iteration >= max_iterations:
            display_error(
                f"Maximum iterations reached ({max_iterations}).\n\n"
                f"You have two options:\n"
                f"1. Approve the current plan as-is\n"
                f"2. Reject to cancel execution\n\n"
                f"Further modifications are not available after {max_iterations} iterations."
            )
            # Recurse to prompt for Approve/Reject only
            return request_before_execution_approval(coordinator_id, team_config, plan, iteration)

        # Get user feedback
        feedback = get_user_feedback(
            prompt=f"Please provide feedback to adjust the plan (iteration {iteration + 1} of {max_iterations}):"
        )

        log_telemetry("coordination", coordinator_id, "plan_modification_requested", {
            "gate": "before_execution",
            "iteration": iteration,
            "feedback": feedback
        })

        return {
            "decision": "modify",
            "feedback": feedback,
            "iteration": iteration + 1
        }
```

---

### Pattern 2: Request After Completion Approval

```python
def request_after_completion_approval(coordinator_id: str, team_config: dict, results: dict, iteration: int = 0) -> dict:
    """
    Request user approval for execution results after all agents complete.

    Args:
        coordinator_id: Unique identifier for coordinator
        team_config: Team configuration with approval_gates settings
        results: Execution results dict with agent_results, aggregated_results, artifacts
        iteration: Current iteration count (default: 0)

    Returns:
        dict with decision, feedback (if iterate), and iteration
    """
    max_iterations = 3

    # Check if gates are bypassed (REQ-F-20)
    approval_gates = team_config.get('approval_gates', {})

    if approval_gates.get('disabled', False):
        log_telemetry("coordination", coordinator_id, "approval_bypassed", {
            "gate": "after_completion",
            "reason": "gates_disabled"
        })
        return {"decision": "approve", "bypassed": True, "reason": "gates_disabled"}

    if not approval_gates.get('after_completion', True):
        log_telemetry("coordination", coordinator_id, "approval_bypassed", {
            "gate": "after_completion",
            "reason": "gate_type_disabled"
        })
        return {"decision": "approve", "bypassed": True, "reason": "gate_type_disabled"}

    # Format results prompt
    prompt = format_after_completion_prompt(
        team_name=team_config['name'],
        coordinator_id=coordinator_id,
        results=results,
        max_iterations=max_iterations
    )

    # Display prompt to user
    display_results_prompt(prompt)

    # Get user decision
    user_response = get_user_decision(options=["Accept", "Iterate", "Discard"])

    if user_response == "Accept":
        # User accepted results - complete workflow
        log_telemetry("coordination", coordinator_id, "results_accepted", {
            "gate": "after_completion",
            "iteration": iteration,
            "user_response": "accept"
        })
        return {"decision": "approve", "iteration": iteration}

    elif user_response == "Discard":
        # User discarded results - abort workflow
        log_telemetry("coordination", coordinator_id, "results_rejected", {
            "gate": "after_completion",
            "iteration": iteration,
            "user_response": "discard"
        })
        return {"decision": "reject", "reason": "user_discarded"}

    elif user_response == "Iterate":
        # User wants to iterate - get feedback

        # Check iteration limit
        if iteration >= max_iterations:
            display_error(
                f"Maximum iterations reached ({max_iterations}).\n\n"
                f"You have two options:\n"
                f"1. Accept the current results\n"
                f"2. Discard to cancel workflow\n\n"
                f"Further iterations are not available after {max_iterations} attempts."
            )
            # Recurse to prompt for Accept/Discard only
            return request_after_completion_approval(coordinator_id, team_config, results, iteration)

        # Get user feedback
        feedback = get_user_feedback(
            prompt=f"Please provide feedback to regenerate (iteration {iteration + 1} of {max_iterations}):"
        )

        log_telemetry("coordination", coordinator_id, "results_iteration_requested", {
            "gate": "after_completion",
            "iteration": iteration,
            "feedback": feedback
        })

        return {
            "decision": "modify",
            "feedback": feedback,
            "iteration": iteration + 1
        }
```

---

### Pattern 3: Modify Flow with Feedback Collection

**Coordinator Usage**:
```python
# Initial approval request
iteration = 0
approval_result = request_before_execution_approval(coordinator_id, team_config, plan, iteration)

while approval_result['decision'] == 'modify':
    # User requested modification - regenerate plan with feedback
    feedback = approval_result['feedback']
    iteration = approval_result['iteration']

    display_info(f"Regenerating plan with feedback (iteration {iteration})...")

    # Regenerate plan incorporating user feedback
    plan = regenerate_plan_with_feedback(original_plan, feedback)

    # Request approval again
    approval_result = request_before_execution_approval(coordinator_id, team_config, plan, iteration)

if approval_result['decision'] == 'approve':
    # Plan approved - proceed with execution
    spawn_agents(plan)
elif approval_result['decision'] == 'reject':
    # Plan rejected - abort
    abort_team_execution()
```

---

## Telemetry Events

### Event: plan_proposed

**When**: Before prompting user for approval (before_execution gate)

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"plan_proposed","gate":"before_execution","plan_summary":"3 parallel write-agents, 12 targets","approval_required":true}
```

---

### Event: plan_approved

**When**: User approves execution plan

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"plan_approved","gate":"before_execution","iteration":1,"user_response":"approve"}
```

---

### Event: plan_rejected

**When**: User rejects execution plan

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"plan_rejected","gate":"before_execution","iteration":1,"user_response":"reject"}
```

---

### Event: plan_modification_requested

**When**: User requests plan modification with feedback

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"plan_modification_requested","gate":"before_execution","iteration":1,"feedback":"Reduce to 2 batches"}
```

---

### Event: results_accepted

**When**: User accepts results (after_completion gate)

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"results_accepted","gate":"after_completion","iteration":1,"user_response":"accept"}
```

---

### Event: results_rejected

**When**: User discards results

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"results_rejected","gate":"after_completion","iteration":1,"user_response":"discard"}
```

---

### Event: results_iteration_requested

**When**: User requests results regeneration with feedback

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"results_iteration_requested","gate":"after_completion","iteration":1,"feedback":"Add more edge cases"}
```

---

### Event: approval_bypassed

**When**: Gate is bypassed (disabled in configuration)

**Schema**:
```jsonl
{"timestamp":"ISO8601","event_type":"coordination","agent_id":"coordinator_id","status":"approval_bypassed","gate":"before_execution","reason":"gates_disabled"}
```

---

## Usage in Coordinators

```markdown
# In teams/testing-parallel-coordinator.md

## Phase 2: Plan Approval (Before Execution Gate)

1. Read `skills/team-orchestration/approval-gate-handler.md`
2. Call request_before_execution_approval() with:
   - coordinator_id: Current coordinator ID
   - team_config: Loaded team definition
   - plan: Generated execution plan from analyze-agent
   - iteration: 0 (initial request)
3. Handle decision:
   - **approve**: Proceed to Phase 3 (Parallel Writing)
   - **modify**: Regenerate plan with feedback, loop back to approval
   - **reject**: Abort team execution, log error, exit
4. Log decision to telemetry

## Phase 5: Results Review (After Completion Gate)

1. Aggregate results from all agents
2. Read `skills/team-orchestration/approval-gate-handler.md`
3. Call request_after_completion_approval() with:
   - coordinator_id: Current coordinator ID
   - team_config: Loaded team definition
   - results: Aggregated results dict
   - iteration: 0 (initial request)
4. Handle decision:
   - **approve**: Complete workflow, finalize results
   - **modify**: Provide feedback to agents, regenerate, loop back
   - **reject**: Discard results, abort workflow
5. Log decision to telemetry
```

---

## Testing Checklist

For TASK-004 acceptance:

- [ ] Supports gate types: before_execution, after_completion, disabled
- [ ] Pauses execution and presents plan to user (before_execution)
- [ ] Pauses execution and presents results to user (after_completion)
- [ ] Handles Approve response (returns "approve" decision)
- [ ] Handles Reject response (returns "reject" decision)
- [ ] Handles Modify response (collects feedback, returns "modify" decision)
- [ ] Supports modify iterations (max 3 attempts)
- [ ] Increments iteration count on each modification request
- [ ] Blocks further modifications after max_iterations reached
- [ ] Bypasses gates if approval_gates.disabled=true
- [ ] Bypasses specific gate if approval_gates.{gate_type}=false
- [ ] Returns decision: "approve", "reject", or "modify" with feedback
- [ ] Formats approval prompts with plan details (agent counts, batches, time estimates)
- [ ] Formats results prompts with aggregated results and artifacts
- [ ] Logs approval events to telemetry: plan_proposed
- [ ] Logs approval events to telemetry: plan_approved
- [ ] Logs approval events to telemetry: plan_rejected
- [ ] Logs approval events to telemetry: plan_modification_requested
- [ ] Logs approval events to telemetry: results_accepted
- [ ] Logs approval events to telemetry: results_rejected
- [ ] Logs approval events to telemetry: results_iteration_requested
- [ ] Logs approval events to telemetry: approval_bypassed
- [ ] Handles errors gracefully (corrupted config, missing fields)
- [ ] Provides clear error messages for max iteration limit

---

## Example Approval Flow

### Scenario: Testing Team with Modification

**Step 1: Initial Approval Request**

Coordinator generates plan with 5 parallel write-agents.

```python
plan = {
    "batch_count": 5,
    "agent_count": 5,
    "estimated_time_minutes": 3,
    "sequential_time_minutes": 15,
    "speedup_percentage": 80
}

result = request_before_execution_approval(
    coordinator_id="testing-coordinator-001",
    team_config=team_config,
    plan=plan,
    iteration=0
)
```

**User Response**: Modify ("Too many agents, reduce to 3")

**Result**:
```python
{
    "decision": "modify",
    "feedback": "Too many agents, reduce to 3",
    "iteration": 1
}
```

---

**Step 2: Regenerate Plan with Feedback**

Coordinator adjusts plan to 3 agents.

```python
plan = {
    "batch_count": 3,
    "agent_count": 3,
    "estimated_time_minutes": 4,
    "sequential_time_minutes": 15,
    "speedup_percentage": 73
}

result = request_before_execution_approval(
    coordinator_id="testing-coordinator-001",
    team_config=team_config,
    plan=plan,
    iteration=1
)
```

**User Response**: Approve

**Result**:
```python
{
    "decision": "approve",
    "iteration": 1
}
```

---

**Step 3: Execute Plan**

Coordinator spawns 3 write-agents and continues execution.

**Telemetry Log**:
```jsonl
{"timestamp":"2026-02-13T14:30:00.000Z","event_type":"coordination","agent_id":"testing-coordinator-001","status":"plan_proposed","gate":"before_execution","plan_summary":"5 parallel write-agents"}
{"timestamp":"2026-02-13T14:30:15.000Z","event_type":"coordination","agent_id":"testing-coordinator-001","status":"plan_modification_requested","gate":"before_execution","iteration":0,"feedback":"Too many agents, reduce to 3"}
{"timestamp":"2026-02-13T14:30:30.000Z","event_type":"coordination","agent_id":"testing-coordinator-001","status":"plan_proposed","gate":"before_execution","plan_summary":"3 parallel write-agents"}
{"timestamp":"2026-02-13T14:30:45.000Z","event_type":"coordination","agent_id":"testing-coordinator-001","status":"plan_approved","gate":"before_execution","iteration":1,"user_response":"approve"}
```

---

## References

- **Plan**: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Approval Gates Implementation, REQ-F-17 to REQ-F-20)
- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-17, REQ-F-18, REQ-F-19, REQ-F-20)
- **Pattern**: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-004)
