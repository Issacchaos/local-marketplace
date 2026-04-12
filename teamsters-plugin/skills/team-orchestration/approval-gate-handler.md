---
name: approval-gate-handler
description: Pause execution at configurable approval gates (before_execution, after_completion), present plans/results to users via AskUserQuestion, and handle Approve/Modify/Reject responses with up to 3 modification iterations.
user-invocable: false
---

# Approval Gate Handler Skill

**Version**: 2.0.0
**Category**: Infrastructure
**Purpose**: Manage user approval gates for team orchestration with iterative feedback, plan rendering, and result acceptance

**Used By**: Team Orchestration SKILL (`skills/team-orchestration/SKILL.md`), Team Coordinators

---

## Overview

The Approval Gate Handler Skill provides configurable approval checkpoints that pause team orchestration at two critical junctures:

1. **Before-execution gate**: After the coordinator builds an execution plan but before any agents are spawned. The user reviews parallelization strategy, agent composition, dependencies, and estimated resource usage.
2. **After-completion gate**: After all agents complete but before the workflow is finalized. The user reviews aggregated outputs, metrics, test results, and generated artifacts.

Each gate collects one of three decisions: **Approve**, **Modify** (with feedback, up to 3 iterations), or **Reject** (clean abort with no side effects).

All user interactions are performed via the **`AskUserQuestion`** tool. This ensures a consistent interactive experience within Claude Code sessions.

### Key Principles

1. **User Control**: Gates are user-facing decision points, not implementation details
2. **Clean Abort on Reject**: Rejection at any gate produces no side effects -- no agents spawned, no files written, no resources consumed
3. **Bounded Iteration**: Modification loops are capped at 3 iterations to prevent infinite feedback cycles
4. **Disableable**: Gates can be fully bypassed via `approval_gates.disabled = true` for CI/CD and batch pipelines
5. **Non-Blocking Telemetry**: All gate events are logged but telemetry failures never block the gate flow

---

## Skill Interface

### Input

```yaml
gate_type: string              # "before_execution" | "after_completion"
coordinator_id: string         # Unique identifier for the coordinator requesting approval
team_config: dict              # Team configuration dict with approval_gates settings
plan_or_results: dict          # Execution plan (before_execution) or team_result (after_completion)
iteration: integer             # Current iteration count (default: 0)
max_iterations: integer        # Maximum allowed iterations (default: 3)
```

### Output

```yaml
# Approve case
decision: "approve"
iteration: integer             # Final iteration count
bypassed: boolean              # true if gate was disabled

# Modify case
decision: "modify"
feedback: string               # User feedback text
iteration: integer             # Incremented iteration count

# Reject case
decision: "reject"
reason: string                 # "user_rejected" | "user_discarded"

# Bypass case (gate disabled)
decision: "approve"
bypassed: true
reason: string                 # "gates_disabled" | "gate_type_disabled"
```

---

## Core Functions

### Function 1: present_plan_for_approval(execution_plan)

Renders the execution plan as a structured markdown presentation for user review.

```python
def present_plan_for_approval(execution_plan: dict, team_config: dict, coordinator_id: str) -> str:
    """
    Render the execution plan as markdown for user review.

    The plan is presented as a markdown table showing phases, agents,
    dependencies, and estimated durations. This gives the user a clear
    picture of what will happen before any agents are spawned.

    Args:
        execution_plan: Execution plan from build_execution_plan()
            - phases: list of phase dicts (phase_number, agents, agent_names, parallel)
            - total_agents: int
            - max_concurrent: int
            - target_path: str or None
            - estimated_time_minutes: float or None
        team_config: Full team definition dict
        coordinator_id: Coordinator identifier

    Returns:
        Formatted markdown string for display to user
    """
    team_name = team_config['name']
    phases = execution_plan.get('phases', [])
    total_agents = execution_plan.get('total_agents', 0)
    max_concurrent = execution_plan.get('max_concurrent', 5)
    target_path = execution_plan.get('target_path', 'project root')
    estimated_time = execution_plan.get('estimated_time_minutes')
    timeout = team_config.get('timeout_minutes', 30)

    # Build header
    lines = []
    lines.append(f"# {team_name}: Proposed Execution Plan")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- **Team**: {team_name}")
    lines.append(f"- **Target**: {target_path or 'project root'}")
    lines.append(f"- **Coordinator**: {coordinator_id}")
    lines.append(f"- **Total Agents**: {total_agents}")
    lines.append(f"- **Max Concurrent**: {max_concurrent}")
    lines.append(f"- **Timeout**: {timeout} minutes")
    if estimated_time:
        lines.append(f"- **Estimated Duration**: {estimated_time} minutes")
    lines.append("")

    # Build phase table
    lines.append("## Execution Phases")
    lines.append("")
    lines.append("| Phase | Mode | Agents | Dependencies | Est. Duration |")
    lines.append("|-------|------|--------|--------------|---------------|")

    for phase in phases:
        phase_num = phase['phase_number']
        mode = "Parallel" if phase.get('parallel', False) else "Sequential"
        agent_names = ", ".join(phase.get('agent_names', []))
        agent_count = len(phase.get('agents', []))

        # Determine dependencies for this phase
        if phase_num == 1:
            deps = "None (first phase)"
        else:
            prev_phase = phases[phase_num - 2] if phase_num > 1 else None
            deps = f"Phase {phase_num - 1}" if prev_phase else "None"

        # Estimate duration (placeholder; coordinator provides actual estimates)
        est_duration = "N/A"
        for agent in phase.get('agents', []):
            if agent.get('estimated_duration_seconds'):
                est_duration = f"~{agent['estimated_duration_seconds']}s"
                break

        lines.append(
            f"| {phase_num} | {mode} ({agent_count} agent{'s' if agent_count != 1 else ''}) "
            f"| {agent_names} | {deps} | {est_duration} |"
        )

    lines.append("")

    # Build agent detail section
    lines.append("## Agent Details")
    lines.append("")

    for phase in phases:
        for agent in phase.get('agents', []):
            agent_name = agent.get('name', 'unknown')
            agent_type = agent.get('type', 'unknown')
            critical = agent.get('critical', False)
            max_instances = agent.get('max_instances', 1)
            model = agent.get('model', team_config.get('model', 'sonnet'))

            lines.append(f"**{agent_name}** (`{agent_type}`)")
            lines.append(f"- Model: {model}")
            lines.append(f"- Critical: {'Yes' if critical else 'No'}")
            if max_instances > 1:
                lines.append(f"- Instances: {max_instances}")
            lines.append("")

    # Build resource summary
    lines.append("## Resource Usage")
    lines.append(f"- **Active Agents**: up to {min(total_agents, max_concurrent)} of {max_concurrent} max")
    lines.append(f"- **Retry Budget**: {team_config.get('retry_config', {}).get('max_retries', 3)} retries per agent")
    lines.append(f"- **Failure Strategy**: {team_config.get('failure_handling', 'continue')}")
    lines.append("")

    return "\n".join(lines)
```

---

### Function 2: collect_approval_decision()

Collects the user's decision using the `AskUserQuestion` tool.

```python
def collect_approval_decision(
    gate_type: str,
    rendered_prompt: str,
    iteration: int,
    max_iterations: int
) -> dict:
    """
    Present the rendered prompt to the user and collect their decision.

    Uses the AskUserQuestion tool for all user interactions. The tool
    presents the rendered prompt followed by numbered options. The user
    responds with their choice and optional feedback.

    Args:
        gate_type: "before_execution" or "after_completion"
        rendered_prompt: Markdown string from present_plan_for_approval() or
                         present_results_for_acceptance()
        iteration: Current iteration number (0-based)
        max_iterations: Maximum allowed iterations (default: 3)

    Returns:
        dict with:
            decision: "approve" | "modify" | "reject"
            feedback: str or None (only for "modify")
            iteration: int (updated iteration count)
    """
    # Build the options section based on gate type and iteration state
    if gate_type == "before_execution":
        approve_label = "Approve"
        reject_label = "Reject"
        modify_label = "Modify"
        approve_desc = "Execute plan as proposed"
        reject_desc = "Cancel team execution (no agents will be spawned)"
        modify_desc = f"Provide feedback to adjust plan (iteration {iteration + 1} of {max_iterations})"
    else:  # after_completion
        approve_label = "Accept"
        reject_label = "Discard"
        modify_label = "Iterate"
        approve_desc = "Keep results and complete workflow"
        reject_desc = "Discard all results and cancel workflow"
        modify_desc = f"Provide feedback to regenerate (iteration {iteration + 1} of {max_iterations})"

    # Check if modification is still allowed
    can_modify = iteration < max_iterations

    # Build question for AskUserQuestion tool
    if can_modify:
        question = (
            f"{rendered_prompt}\n\n"
            f"---\n\n"
            f"## Decision Required\n\n"
            f"1. **{approve_label}** - {approve_desc}\n"
            f"2. **{modify_label}** - {modify_desc}\n"
            f"3. **{reject_label}** - {reject_desc}\n\n"
            f"Reply with your choice (1/2/3) and any feedback if choosing {modify_label}."
        )
    else:
        question = (
            f"{rendered_prompt}\n\n"
            f"---\n\n"
            f"## Decision Required\n\n"
            f"Maximum modification iterations reached ({max_iterations}).\n\n"
            f"1. **{approve_label}** - {approve_desc}\n"
            f"2. **{reject_label}** - {reject_desc}\n\n"
            f"Reply with your choice (1/2)."
        )

    # Use AskUserQuestion tool to collect response
    # The AskUserQuestion tool pauses execution and waits for user input.
    user_response = AskUserQuestion(question)

    # Parse user response
    return parse_user_response(user_response, gate_type, iteration, max_iterations)


def parse_user_response(
    response_text: str,
    gate_type: str,
    iteration: int,
    max_iterations: int
) -> dict:
    """
    Parse the user's free-form response into a structured decision.

    Accepts multiple response formats:
    - Numeric: "1", "2", "3"
    - Label: "approve", "modify", "reject", "accept", "iterate", "discard"
    - Shorthand: "y"/"yes" (approve), "n"/"no" (reject)
    - Feedback inline: "modify: reduce to 2 agents"

    Args:
        response_text: Raw user response string
        gate_type: "before_execution" or "after_completion"
        iteration: Current iteration number
        max_iterations: Maximum allowed iterations

    Returns:
        dict with decision, feedback, and iteration
    """
    text = response_text.strip().lower()

    # Detect approval
    approve_signals = ["1", "approve", "accept", "yes", "y", "ok", "lgtm", "go"]
    if any(text == signal or text.startswith(signal + " ") for signal in approve_signals):
        return {"decision": "approve", "iteration": iteration}

    # Detect rejection
    reject_signals = ["3", "reject", "discard", "cancel", "no", "n", "abort"]
    if gate_type == "after_completion":
        reject_signals = ["2", "reject", "discard", "cancel", "no", "n", "abort"]
    if any(text == signal or text.startswith(signal + " ") for signal in reject_signals):
        reason = "user_rejected" if gate_type == "before_execution" else "user_discarded"
        return {"decision": "reject", "reason": reason}

    # Detect modification
    modify_signals = ["2", "modify", "iterate", "change", "adjust", "edit"]
    if gate_type == "after_completion":
        modify_signals = ["3", "iterate", "modify", "change", "redo"]
    # If iteration limit reached, treat modify as approval prompt
    if not (iteration < max_iterations):
        # Cannot modify further; treat as ambiguous, re-prompt
        return {"decision": "approve", "iteration": iteration}

    for signal in modify_signals:
        if text == signal:
            # User chose modify but did not provide inline feedback
            # Use AskUserQuestion to collect feedback separately
            feedback = AskUserQuestion(
                f"## Modification Feedback (Iteration {iteration + 1} of {max_iterations})\n\n"
                f"Please describe what you would like changed:\n\n"
                f"**Examples**:\n"
                f"- \"Reduce agent count to 2 instead of 3\"\n"
                f"- \"Focus on high-priority targets only\"\n"
                f"- \"Increase coverage threshold to 90%\"\n"
                f"- \"Skip the analysis phase, run write agents directly\"\n"
            )
            return {
                "decision": "modify",
                "feedback": feedback.strip(),
                "iteration": iteration + 1
            }
        if text.startswith(signal + ":") or text.startswith(signal + " "):
            # User provided inline feedback: "modify: reduce to 2 agents"
            feedback = text[len(signal):].lstrip(": ")
            return {
                "decision": "modify",
                "feedback": feedback,
                "iteration": iteration + 1
            }

    # If response does not match known signals, treat the entire response
    # as modification feedback (common UX pattern: user just types feedback)
    if iteration < max_iterations and len(text) > 10:
        return {
            "decision": "modify",
            "feedback": response_text.strip(),
            "iteration": iteration + 1
        }

    # Fallback: ambiguous response, default to approve
    return {"decision": "approve", "iteration": iteration}
```

---

### Function 3: handle_plan_modification(plan, iteration)

Manages the modification loop, allowing up to 3 iterations of user feedback.

```python
def handle_plan_modification(
    execution_plan: dict,
    team_config: dict,
    coordinator_id: str,
    project_root: str,
    team_name: str,
    initial_iteration: int = 0
) -> dict:
    """
    Run the before-execution approval gate with modification loop.

    This is the top-level function called by the orchestrator for the
    before-execution gate. It handles the full lifecycle:
    1. Check if gate is disabled (bypass if so)
    2. Present plan to user
    3. Collect decision
    4. If "modify": regenerate plan with feedback, loop (up to 3 iterations)
    5. If "reject": return reject immediately
    6. If "approve": return approve

    The modification loop allows the user to iteratively refine the
    execution plan up to max_iterations times. Each iteration:
    - Presents the updated plan
    - Collects a new decision
    - If "modify" again, incorporates new feedback

    After max_iterations modifications, only Approve or Reject are offered.

    Args:
        execution_plan: Initial execution plan dict
        team_config: Full team configuration
        coordinator_id: Coordinator identifier
        project_root: Project root path (for telemetry)
        team_name: Team name (for telemetry)
        initial_iteration: Starting iteration (default: 0)

    Returns:
        dict with:
            decision: "approve" | "reject"
            iteration: final iteration count
            final_plan: the (possibly modified) execution plan
            bypassed: bool (true if gate was disabled)
    """
    max_iterations = 3
    iteration = initial_iteration
    current_plan = execution_plan

    # STEP 1: Check if gates are disabled (REQ-F-20)
    bypass_result = check_gate_bypass(team_config, "before_execution", coordinator_id)
    if bypass_result is not None:
        log_telemetry("approval", coordinator_id, "gate_bypassed", {
            "gate_type": "before_execution",
            "reason": bypass_result["reason"]
        }, project_root, team_name)
        return {
            "decision": "approve",
            "iteration": 0,
            "final_plan": current_plan,
            "bypassed": True,
            "reason": bypass_result["reason"]
        }

    # STEP 2: Enter approval loop
    while True:
        # Log gate entry
        log_telemetry("approval", coordinator_id, "gate_entered", {
            "gate_type": "before_execution",
            "iteration": iteration,
            "max_iterations": max_iterations,
            "total_agents": current_plan.get("total_agents", 0),
            "total_phases": len(current_plan.get("phases", []))
        }, project_root, team_name)

        # STEP 2a: Render plan
        rendered = present_plan_for_approval(current_plan, team_config, coordinator_id)

        # STEP 2b: Collect decision via AskUserQuestion
        result = collect_approval_decision(
            gate_type="before_execution",
            rendered_prompt=rendered,
            iteration=iteration,
            max_iterations=max_iterations
        )

        # Log user response
        log_telemetry("approval", coordinator_id, "user_response_received", {
            "gate_type": "before_execution",
            "decision": result["decision"],
            "feedback_text": result.get("feedback"),
            "iteration": result.get("iteration", iteration)
        }, project_root, team_name)

        # STEP 2c: Handle decision
        if result["decision"] == "approve":
            log_telemetry("coordination", coordinator_id, "plan_approved", {
                "gate": "before_execution",
                "iteration": iteration
            }, project_root, team_name)

            return {
                "decision": "approve",
                "iteration": result.get("iteration", iteration),
                "final_plan": current_plan,
                "bypassed": False
            }

        elif result["decision"] == "reject":
            log_telemetry("coordination", coordinator_id, "plan_rejected", {
                "gate": "before_execution",
                "iteration": iteration
            }, project_root, team_name)

            return {
                "decision": "reject",
                "iteration": result.get("iteration", iteration),
                "final_plan": current_plan,
                "bypassed": False
            }

        elif result["decision"] == "modify":
            feedback = result["feedback"]
            iteration = result["iteration"]

            log_telemetry("coordination", coordinator_id, "plan_modification_requested", {
                "gate": "before_execution",
                "iteration": iteration,
                "feedback": feedback
            }, project_root, team_name)

            # STEP 2d: Regenerate plan with feedback
            # The coordinator is responsible for interpreting feedback
            # and producing a new plan. This function delegates to the
            # coordinator's plan regeneration logic.
            current_plan = regenerate_plan_with_feedback(
                current_plan, feedback, team_config
            )

            # Loop continues with updated plan
            continue
```

---

### Function 4: present_results_for_acceptance(team_result)

Renders completed team results for user review.

```python
def present_results_for_acceptance(team_result: dict, team_config: dict, coordinator_id: str) -> str:
    """
    Render the team execution results as markdown for user review.

    Displays:
    - Agent outputs with status (completed/failed)
    - Execution metrics (duration, success rate, retries)
    - Test results (if applicable)
    - Generated artifacts (files created/modified)
    - Warnings and errors

    Args:
        team_result: Aggregated team result from result-aggregator.md
            - total_agents: int
            - successful: int
            - failed: int
            - outputs: list of agent outputs
            - failures: list of failure records
            - merged_files: list of files touched
            - merged_metrics: dict of numeric metrics
            - merged_warnings: list of warning strings
            - summary: dict with success_rate, total_duration_seconds, etc.
        team_config: Full team configuration
        coordinator_id: Coordinator identifier

    Returns:
        Formatted markdown string for display to user
    """
    team_name = team_config['name']
    total = team_result.get('total_agents', 0)
    successful = team_result.get('successful', 0)
    failed = team_result.get('failed', 0)
    summary = team_result.get('summary', {})
    outputs = team_result.get('outputs', [])
    failures = team_result.get('failures', [])
    merged_files = team_result.get('merged_files', [])
    merged_metrics = team_result.get('merged_metrics', {})
    merged_warnings = team_result.get('merged_warnings', [])

    lines = []
    lines.append(f"# {team_name}: Execution Results")
    lines.append("")

    # Overview section
    lines.append("## Overview")
    lines.append(f"- **Team**: {team_name}")
    lines.append(f"- **Coordinator**: {coordinator_id}")

    # Determine status label
    if failed == 0:
        status_label = "Completed"
    elif successful > 0:
        status_label = "Partial Success"
    else:
        status_label = "Failed"
    lines.append(f"- **Status**: {status_label}")

    duration = summary.get('total_duration_seconds', 0)
    lines.append(f"- **Duration**: {duration:.1f} seconds")
    lines.append(f"- **Success Rate**: {summary.get('success_rate', 0) * 100:.0f}% ({successful}/{total})")

    retry_count = summary.get('retry_count', 0)
    if retry_count > 0:
        lines.append(f"- **Retries**: {retry_count}")
    lines.append("")

    # Agent results table
    lines.append("## Agent Results")
    lines.append("")
    lines.append("| Agent | Type | Status | Duration | Summary |")
    lines.append("|-------|------|--------|----------|---------|")

    for output in outputs:
        agent_id = output.get('agent_id', 'unknown')
        agent_type = output.get('agent_type', 'unknown')
        status = output.get('status', 'unknown')
        meta = output.get('metadata', {})
        dur = meta.get('duration_seconds', 0)
        output_summary = str(output.get('output', {}) if isinstance(output.get('output'), dict) else output.get('output', ''))
        # Truncate summary for table display
        if len(output_summary) > 80:
            output_summary = output_summary[:77] + "..."
        status_icon = "Completed" if status == "completed" else "Failed"
        lines.append(f"| {agent_id} | {agent_type} | {status_icon} | {dur:.1f}s | {output_summary} |")

    lines.append("")

    # Failed agents detail (if any)
    if failures:
        lines.append("## Failures")
        lines.append("")
        for failure in failures:
            agent_id = failure.get('agent_id', 'unknown')
            reason = failure.get('failure_reason', 'Unknown error')
            lines.append(f"**{agent_id}**: {reason}")
            lines.append("")

    # Metrics section
    if merged_metrics:
        lines.append("## Metrics")
        lines.append("")
        for key, value in merged_metrics.items():
            # Format metric key as readable label
            label = key.replace('_', ' ').title()
            lines.append(f"- **{label}**: {value}")
        lines.append("")

    # Generated artifacts
    if merged_files:
        lines.append("## Generated Artifacts")
        lines.append("")
        for filepath in merged_files:
            lines.append(f"- `{filepath}`")
        lines.append("")

    # Warnings
    if merged_warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in merged_warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines)
```

---

## Gate Bypass Logic (REQ-F-20)

```python
def check_gate_bypass(team_config: dict, gate_type: str, coordinator_id: str) -> dict:
    """
    Check if a gate should be bypassed based on configuration.

    Bypass conditions:
    1. approval_gates.disabled == true -> bypass all gates
    2. approval_gates.{gate_type} == false -> bypass this specific gate

    Args:
        team_config: Team configuration with approval_gates
        gate_type: "before_execution" or "after_completion"
        coordinator_id: For logging

    Returns:
        None if gate should fire, or dict with bypass reason if bypassed
    """
    approval_gates = team_config.get('approval_gates', {})

    # Check global disable
    if approval_gates.get('disabled', False):
        return {
            "decision": "approve",
            "bypassed": True,
            "reason": "gates_disabled"
        }

    # Check specific gate disable
    if not approval_gates.get(gate_type, True):
        return {
            "decision": "approve",
            "bypassed": True,
            "reason": "gate_type_disabled"
        }

    # Gate should fire
    return None
```

---

## After-Completion Gate Flow

```python
def handle_results_acceptance(
    team_result: dict,
    team_config: dict,
    coordinator_id: str,
    project_root: str,
    team_name: str,
    initial_iteration: int = 0
) -> dict:
    """
    Run the after-completion approval gate with iteration loop.

    Top-level function for the after-completion gate. Handles:
    1. Check if gate is disabled (bypass if so)
    2. Present results to user
    3. Collect decision (Accept / Iterate / Discard)
    4. If "modify" (iterate): return feedback to coordinator for re-execution
    5. If "reject" (discard): return reject with no side effects
    6. If "approve" (accept): return approve to finalize

    Args:
        team_result: Aggregated results from result-aggregator.md
        team_config: Full team configuration
        coordinator_id: Coordinator identifier
        project_root: Project root path
        team_name: Team name
        initial_iteration: Starting iteration (default: 0)

    Returns:
        dict with decision, iteration, feedback (if modify), bypassed
    """
    max_iterations = 3
    iteration = initial_iteration

    # STEP 1: Check bypass
    bypass_result = check_gate_bypass(team_config, "after_completion", coordinator_id)
    if bypass_result is not None:
        log_telemetry("approval", coordinator_id, "gate_bypassed", {
            "gate_type": "after_completion",
            "reason": bypass_result["reason"]
        }, project_root, team_name)
        return {
            "decision": "approve",
            "iteration": 0,
            "bypassed": True,
            "reason": bypass_result["reason"]
        }

    # STEP 2: Enter approval loop
    while True:
        # Log gate entry
        log_telemetry("approval", coordinator_id, "gate_entered", {
            "gate_type": "after_completion",
            "iteration": iteration,
            "max_iterations": max_iterations,
            "total_agents": team_result.get("total_agents", 0),
            "successful": team_result.get("successful", 0),
            "failed": team_result.get("failed", 0)
        }, project_root, team_name)

        # Render results
        rendered = present_results_for_acceptance(team_result, team_config, coordinator_id)

        # Collect decision via AskUserQuestion
        result = collect_approval_decision(
            gate_type="after_completion",
            rendered_prompt=rendered,
            iteration=iteration,
            max_iterations=max_iterations
        )

        # Log user response
        log_telemetry("approval", coordinator_id, "user_response_received", {
            "gate_type": "after_completion",
            "decision": result["decision"],
            "feedback_text": result.get("feedback"),
            "iteration": result.get("iteration", iteration)
        }, project_root, team_name)

        # Handle decision
        if result["decision"] == "approve":
            log_telemetry("coordination", coordinator_id, "results_accepted", {
                "gate": "after_completion",
                "iteration": iteration
            }, project_root, team_name)
            return {
                "decision": "approve",
                "iteration": result.get("iteration", iteration),
                "bypassed": False
            }

        elif result["decision"] == "reject":
            log_telemetry("coordination", coordinator_id, "results_rejected", {
                "gate": "after_completion",
                "iteration": iteration
            }, project_root, team_name)
            return {
                "decision": "reject",
                "iteration": result.get("iteration", iteration),
                "bypassed": False
            }

        elif result["decision"] == "modify":
            feedback = result["feedback"]
            iteration = result["iteration"]

            log_telemetry("coordination", coordinator_id, "results_iteration_requested", {
                "gate": "after_completion",
                "iteration": iteration,
                "feedback": feedback
            }, project_root, team_name)

            # Return to coordinator for re-execution
            # Unlike the before-execution gate, the after-completion
            # gate returns the modify decision to the orchestrator
            # which decides whether to re-run agents
            return {
                "decision": "modify",
                "feedback": feedback,
                "iteration": iteration,
                "bypassed": False
            }
```

---

## Reject Behavior: Clean Abort with No Side Effects

When a user rejects at either gate, the handler guarantees no side effects:

### Before-Execution Reject

```python
# What happens on before_execution reject:
# 1. No agents have been spawned (plan was pre-execution)
# 2. Team registration is cleaned up via resource_manager.on_team_complete()
# 3. Telemetry logs the rejection event
# 4. TeamResult is returned with status "aborted"
# 5. No files are created, no tasks are spawned, no resources consumed

# The orchestrator handles cleanup:
def handle_before_execution_reject(team_id, coordinator_id, team_start_time, telemetry_log_path):
    resource_manager.on_team_complete(team_id)
    return {
        'team_result': {
            'team_id': team_id,
            'status': 'aborted',
            'aggregated_result': None,
            'metrics': {'total_duration_seconds': elapsed_since(team_start_time)},
            'approval_decisions': {'before_execution': 'reject', 'after_completion': None},
            'telemetry_log_path': telemetry_log_path,
            'error': 'Team execution cancelled by user at before_execution gate.'
        }
    }
```

### After-Completion Reject (Discard)

```python
# What happens on after_completion reject (discard):
# 1. Agents have already completed, but results are discarded
# 2. Any generated files remain on disk (user can manually clean up)
# 3. Team status is set to "aborted"
# 4. Telemetry logs the rejection event
# 5. Note: agents already consumed resources; reject only discards the results

def handle_after_completion_reject(team_id, team_result, coordinator_id, team_start_time):
    return {
        'team_result': {
            'team_id': team_id,
            'status': 'aborted',
            'aggregated_result': team_result,  # Preserved for telemetry
            'metrics': team_result.get('summary', {}),
            'approval_decisions': {'before_execution': 'approve', 'after_completion': 'reject'},
            'error': 'Results discarded by user at after_completion gate.'
        }
    }
```

---

## Telemetry Events

| Event | Status | Gate | Description |
|-------|--------|------|-------------|
| approval | gate_entered | before_execution / after_completion | Gate checkpoint reached |
| approval | gate_bypassed | before_execution / after_completion | Gate disabled, auto-approved |
| approval | user_response_received | before_execution / after_completion | User decision captured |
| coordination | plan_approved | before_execution | User approved plan |
| coordination | plan_rejected | before_execution | User rejected plan |
| coordination | plan_modification_requested | before_execution | User requested changes |
| coordination | results_accepted | after_completion | User accepted results |
| coordination | results_rejected | after_completion | User discarded results |
| coordination | results_iteration_requested | after_completion | User requested re-execution |

---

## Error Handling

### Missing approval_gates Configuration

**Condition**: Team definition has no `approval_gates` key
**Behavior**: Apply defaults (`before_execution: true`, `after_completion: true`, `disabled: false`)
**Rationale**: Gates default to enabled for safety; users must explicitly disable them

### Corrupted User Response

**Condition**: User response cannot be parsed into a known decision
**Behavior**: If response is longer than 10 characters, treat as modification feedback. Otherwise, default to approve.
**Rationale**: Long responses are likely feedback; short gibberish is likely approval intent

### Max Iterations Exceeded

**Condition**: `iteration >= max_iterations` and user chooses "Modify"
**Behavior**: Display message that max iterations reached, offer only Approve or Reject
**Message**:
```
Maximum iterations reached (3).

You have two options:
1. **Approve** the current plan as-is
2. **Reject** to cancel execution

Further modifications are not available after 3 iterations.
```

### AskUserQuestion Tool Failure

**Condition**: AskUserQuestion tool is unavailable or returns error
**Behavior**: Log error to telemetry, default to approve (fail-open for usability)
**Rationale**: Blocking on tool failure would halt all team executions

---

## Testing Checklist

For TASK-004 acceptance:

### Core Functions
- [ ] `present_plan_for_approval()` renders plan as markdown table with phases, agents, dependencies
- [ ] `collect_approval_decision()` uses AskUserQuestion for all user interactions
- [ ] `handle_plan_modification()` supports up to 3 modification iterations
- [ ] `present_results_for_acceptance()` shows agent outputs, metrics, test results, artifacts
- [ ] Returns "approve", "modify", or "reject" decisions

### Gate Behavior
- [ ] Before-execution gate displays plan and collects decision
- [ ] After-completion gate displays results and collects acceptance
- [ ] Modification loop supports up to 3 iterations
- [ ] Reject aborts cleanly with no side effects (no agents spawned at before_execution)
- [ ] Gates can be disabled via `approval_gates.disabled = true`
- [ ] Individual gates can be disabled via `approval_gates.{gate_type} = false`

### User Interaction
- [ ] All interactions use AskUserQuestion tool
- [ ] Accepts numeric responses (1/2/3)
- [ ] Accepts label responses (approve/modify/reject/accept/iterate/discard)
- [ ] Accepts inline feedback ("modify: reduce to 2 agents")
- [ ] Collects feedback separately when user chooses modify without inline text
- [ ] Handles ambiguous responses gracefully

### Telemetry
- [ ] Logs gate_entered event at each gate
- [ ] Logs gate_bypassed when gate is disabled
- [ ] Logs user_response_received with decision and feedback
- [ ] Logs plan_approved / plan_rejected / plan_modification_requested
- [ ] Logs results_accepted / results_rejected / results_iteration_requested

### Error Handling
- [ ] Applies defaults when approval_gates config is missing
- [ ] Handles corrupted user responses (defaults to approve or treats as feedback)
- [ ] Displays max iterations message when limit reached
- [ ] Handles AskUserQuestion tool failure (fail-open to approve)

---

## Example: Full Before-Execution Approval Flow

### Scenario: User Modifies Plan Once, Then Approves

```
Orchestrator -> handle_plan_modification(plan, team_config, coordinator_id, ...)

  Iteration 0:
    1. check_gate_bypass() -> None (gate enabled)
    2. present_plan_for_approval(plan) -> markdown with 5 agents in 3 phases
    3. collect_approval_decision("before_execution", markdown, 0, 3)
       -> AskUserQuestion(markdown + options)
       -> User: "modify: only run 2 agents, skip batch 3"
       -> parse_user_response() -> {decision: "modify", feedback: "only run 2 agents, skip batch 3", iteration: 1}
    4. log plan_modification_requested
    5. regenerate_plan_with_feedback(plan, feedback) -> updated_plan (2 agents, 2 phases)

  Iteration 1:
    1. present_plan_for_approval(updated_plan) -> markdown with 2 agents in 2 phases
    2. collect_approval_decision("before_execution", markdown, 1, 3)
       -> AskUserQuestion(markdown + options)
       -> User: "1" (Approve)
       -> parse_user_response() -> {decision: "approve", iteration: 1}
    3. log plan_approved

  Return: {decision: "approve", iteration: 1, final_plan: updated_plan, bypassed: false}
```

### Scenario: User Rejects Plan

```
Orchestrator -> handle_plan_modification(plan, team_config, coordinator_id, ...)

  Iteration 0:
    1. check_gate_bypass() -> None (gate enabled)
    2. present_plan_for_approval(plan) -> markdown
    3. collect_approval_decision("before_execution", markdown, 0, 3)
       -> AskUserQuestion(markdown + options)
       -> User: "reject"
       -> parse_user_response() -> {decision: "reject", reason: "user_rejected"}
    4. log plan_rejected

  Return: {decision: "reject", iteration: 0, final_plan: plan, bypassed: false}
  Orchestrator -> resource_manager.on_team_complete(team_id) -> clean abort, no agents spawned
```

### Scenario: Gates Disabled

```
Orchestrator -> handle_plan_modification(plan, team_config, coordinator_id, ...)

  team_config.approval_gates.disabled = true

  1. check_gate_bypass() -> {decision: "approve", bypassed: true, reason: "gates_disabled"}
  2. log gate_bypassed

  Return: {decision: "approve", iteration: 0, final_plan: plan, bypassed: true}
  No AskUserQuestion call made. Execution proceeds immediately.
```

---

## References

- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-17, REQ-F-18, REQ-F-19, REQ-F-20)
- **Plan**: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Approval Gates Implementation)
- **Orchestrator**: `skills/team-orchestration/SKILL.md` (Phase 3, Phase 6)
- **Result Aggregator**: `skills/team-orchestration/result-aggregator.md` (provides team_result format)

---

**Last Updated**: 2026-03-25
**Status**: Implementation (TASK-004)
