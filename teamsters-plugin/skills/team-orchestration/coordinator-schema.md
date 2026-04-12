---
name: coordinator-schema
description: Define how coordinators are invoked, how their prompts are constructed with injected context, how they spawn agents via the Agent tool, and how auto-generation mode synthesizes coordinators from team definitions.
user-invocable: false
---

# Coordinator Schema Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Define the coordinator invocation protocol, prompt construction algorithm, agent spawning mechanism, completion tracking, and auto-generation mode

**Used By**: Team Orchestration SKILL (`skills/team-orchestration/SKILL.md`), `/team-run` command

---

## Overview

A **coordinator** is the central orchestration agent for a team execution. It receives the full team context, builds an execution plan, spawns specialist agents, tracks their completion, and produces a final result. Every team has exactly one coordinator, either explicitly defined in a coordinator file or auto-generated from the team definition.

The coordinator is spawned as a **general-purpose agent** via the **Agent tool**. Its prompt is constructed by combining the coordinator file's Markdown body with an injected context block containing the team definition, execution plan, CLI overrides, and agent definitions.

### Coordinator Responsibilities

1. **Receive Context**: Accept the full team definition, execution plan, CLI overrides, and agent definitions
2. **Build Execution Plan**: Analyze targets, determine batching strategy, resolve dependencies
3. **Spawn Agents**: Create specialist agents via `TaskCreate` for each unit of work
4. **Track Completion**: Monitor agent tasks via `TaskUpdate` and handle failures
5. **Produce Output**: Return a structured result with tasks created, final summary, and warnings

### Key Principles

1. **Single Entry Point**: Each team has exactly one coordinator
2. **Context-Driven**: Coordinators receive all necessary context via prompt injection, not tool calls
3. **Task-Based Agent Management**: Agents are created via `TaskCreate` and tracked via `TaskUpdate`
4. **Structured Output**: Coordinator output follows a defined format for result aggregation
5. **Auto-Generatable**: Simple teams can use `coordinator: auto` to skip manual coordinator files

---

## Skill Interface

### Input

```yaml
team_definition: dict          # Full team definition from team-loader.md
execution_plan: dict           # Execution plan from build_execution_plan()
config_overrides: dict         # CLI overrides from /team-run command
agent_definitions: list[dict]  # Parsed agent definitions for all agents in team
project_root: string           # Absolute path to project root
context: dict                  # Execution context (target_path, depth, parent_id)
```

### Output (Required Coordinator Output Format)

```yaml
coordinator_result:
  tasks_created: list[dict]    # Tasks created for agents
    - task_id: string          # TaskCreate task ID
      agent_name: string       # Agent name from definition
      agent_type: string       # Agent type (path to definition)
      status: string           # "completed" | "failed" | "timeout"
      output: any              # Agent output (if completed)
      error: string | null     # Error message (if failed)
      duration_seconds: float  # Time taken

  final_result:
    summary: string            # Human-readable summary of execution
    files_created: list[str]   # Files created by agents
    files_modified: list[str]  # Files modified by agents
    metrics: dict              # Aggregated metrics from agents
    test_results: dict | null  # Test execution results (if applicable)

  warnings: list[string]       # Warnings generated during execution
```

---

## Coordinator File Format

### File Location

Coordinators are typically stored alongside team definitions:

```
{project_root}/teams/{team-name}-coordinator.md
```

### Structure

A coordinator file is a standard Markdown file with optional YAML frontmatter. The frontmatter is informational; the body contains the coordinator's instructions.

```yaml
---
name: string                   # Coordinator identifier (optional, informational)
description: string            # What this coordinator does (optional)
model: opus | sonnet | haiku   # Preferred model for the coordinator (optional, default: sonnet)
---

# Coordinator Title

## Coordinator instructions in Markdown

These instructions define the coordinator's behavior, including:
- How to analyze targets
- How to batch work across agents
- How to handle failures
- What output to produce
```

---

## Coordinator Prompt Construction Algorithm

When the orchestrator spawns a coordinator, it constructs a prompt by combining the coordinator file body with an injected context block. This is the core mechanism by which the coordinator receives its operating context.

### Algorithm

```python
def construct_coordinator_prompt(
    coordinator_path: str,
    team_definition: dict,
    execution_plan: dict,
    config_overrides: dict,
    agent_definitions: list,
    context: dict,
    project_root: str
) -> str:
    """
    Construct the full coordinator prompt by combining the coordinator
    file body with an injected context block.

    The prompt structure is:
    1. Coordinator file body (instructions)
    2. Injected context block (team definition, plan, agents, overrides)
    3. Output format requirements

    Args:
        coordinator_path: Path to coordinator .md file
        team_definition: Full team definition dict
        execution_plan: Execution plan with phases and agents
        config_overrides: CLI overrides
        agent_definitions: Parsed definitions for all agents
        context: Execution context (target_path, depth, parent_id)
        project_root: Absolute path to project root

    Returns:
        Complete prompt string for the coordinator agent
    """
    # STEP 1: Read coordinator file body
    full_path = os.path.join(project_root, coordinator_path)
    coordinator_body = read_coordinator_body(full_path)

    # STEP 2: Build injected context block
    context_block = build_context_injection(
        team_definition=team_definition,
        execution_plan=execution_plan,
        config_overrides=config_overrides,
        agent_definitions=agent_definitions,
        context=context,
        project_root=project_root
    )

    # STEP 3: Build output format requirements
    output_requirements = build_output_requirements()

    # STEP 4: Assemble full prompt
    prompt = (
        f"{coordinator_body}\n\n"
        f"---\n\n"
        f"{context_block}\n\n"
        f"---\n\n"
        f"{output_requirements}"
    )

    return prompt


def read_coordinator_body(file_path: str) -> str:
    """
    Read the coordinator file and extract the Markdown body.

    If the file has YAML frontmatter, the body is everything after
    the closing '---' delimiter. If no frontmatter, the entire file
    is the body.

    Args:
        file_path: Absolute path to coordinator file

    Returns:
        Markdown body string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2].strip()

    return content.strip()
```

---

### Context Injection Format

The context block is injected after the coordinator body. It provides all the information the coordinator needs to execute the team.

```python
def build_context_injection(
    team_definition: dict,
    execution_plan: dict,
    config_overrides: dict,
    agent_definitions: list,
    context: dict,
    project_root: str
) -> str:
    """
    Build the context injection block for the coordinator prompt.

    The context block is structured Markdown that the coordinator
    can parse to understand its operating environment.

    Args:
        team_definition: Full team definition
        execution_plan: Execution plan with phases
        config_overrides: CLI overrides
        agent_definitions: Agent definitions
        context: Execution context
        project_root: Project root path

    Returns:
        Formatted Markdown context block
    """
    lines = []

    # Section 1: Team Definition
    lines.append("# Injected Context: Team Execution")
    lines.append("")
    lines.append("## Team Definition")
    lines.append("")
    lines.append(f"- **Team Name**: {team_definition['name']}")
    lines.append(f"- **Max Agents**: {team_definition['max_agents']}")
    lines.append(f"- **Timeout**: {team_definition['timeout_minutes']} minutes")
    lines.append(f"- **Failure Handling**: {team_definition['failure_handling']}")
    lines.append(f"- **Retry Config**: max {team_definition['retry_config']['max_retries']} retries, "
                 f"backoff {team_definition['retry_config']['backoff_seconds']}")
    lines.append(f"- **Project Root**: {project_root}")
    lines.append(f"- **Target Path**: {context.get('target_path', 'project root')}")
    lines.append(f"- **Depth**: {context.get('depth', 1)}")
    if context.get('parent_id'):
        lines.append(f"- **Parent ID**: {context['parent_id']}")
    lines.append("")

    # Section 2: CLI Overrides (if any)
    if config_overrides:
        lines.append("## CLI Overrides")
        lines.append("")
        for key, value in config_overrides.items():
            if value is not None:
                lines.append(f"- **{key}**: {value}")
        lines.append("")

    # Section 3: Execution Plan
    lines.append("## Execution Plan")
    lines.append("")
    lines.append(f"Total agents: {execution_plan.get('total_agents', 0)}")
    lines.append(f"Max concurrent: {execution_plan.get('max_concurrent', 5)}")
    lines.append("")

    phases = execution_plan.get('phases', [])
    for phase in phases:
        phase_num = phase['phase_number']
        mode = "Parallel" if phase.get('parallel', False) else "Sequential"
        agent_names = ", ".join(phase.get('agent_names', []))
        lines.append(f"### Phase {phase_num} ({mode})")
        lines.append(f"Agents: {agent_names}")
        lines.append("")

    # Section 4: Agent Definitions
    lines.append("## Agent Definitions")
    lines.append("")

    for agent_def in agent_definitions:
        name = agent_def.get('name', 'unknown')
        description = agent_def.get('description', '')
        model = agent_def.get('model', 'sonnet')
        subagent_type = agent_def.get('subagent_type', 'general-purpose')
        tools = agent_def.get('tools', [])
        critical = agent_def.get('critical', False)
        max_instances = agent_def.get('max_instances', 1)

        lines.append(f"### Agent: {name}")
        lines.append(f"- **Description**: {description}")
        lines.append(f"- **Model**: {model}")
        lines.append(f"- **Subagent Type**: {subagent_type}")
        if tools:
            lines.append(f"- **Tools**: {', '.join(tools)}")
        lines.append(f"- **Critical**: {'Yes' if critical else 'No'}")
        if max_instances > 1:
            lines.append(f"- **Max Instances**: {max_instances}")

        # Include agent body (instructions) as context
        body = agent_def.get('body', '')
        if body:
            lines.append("")
            lines.append("**Agent Instructions**:")
            lines.append("")
            # Indent agent body to distinguish from coordinator context
            for body_line in body.split('\n')[:20]:  # Limit to first 20 lines
                lines.append(f"> {body_line}")
            if body.count('\n') > 20:
                lines.append(f"> ... ({body.count(chr(10)) - 20} more lines)")
        lines.append("")

    # Section 5: Execution Constraints
    lines.append("## Execution Constraints")
    lines.append("")
    lines.append("- Use `TaskCreate` to spawn agent tasks")
    lines.append("- Use `TaskUpdate` to track task completion")
    lines.append("- Do NOT exceed the max_agents limit")
    lines.append("- Respect the execution phase ordering (dependencies)")
    lines.append("- Handle agent failures according to the failure_handling strategy")
    lines.append("- Your output MUST include: tasks_created, final_result, warnings")
    lines.append("")

    return "\n".join(lines)
```

---

### Output Format Requirements

```python
def build_output_requirements() -> str:
    """
    Build the output format requirements section.

    This instructs the coordinator on the expected structure of its output,
    which the result aggregator will parse.

    Returns:
        Markdown string describing required output format
    """
    return """## Required Output Format

Your output MUST include the following sections:

### Tasks Created

For each agent task you create, report:
- **Task ID**: The ID returned by TaskCreate
- **Agent Name**: The agent's name from the definition
- **Agent Type**: Path to the agent definition file
- **Status**: "completed", "failed", or "timeout"
- **Output**: The agent's output (if completed)
- **Error**: Error message (if failed)
- **Duration**: Time taken in seconds

### Final Result Summary

Provide a structured summary:
- **Summary**: One-paragraph description of what was accomplished
- **Files Created**: List of new files created by agents
- **Files Modified**: List of existing files modified by agents
- **Metrics**: Key numeric metrics (e.g., tests generated, coverage percentage)
- **Test Results**: Test execution results if applicable (passed, failed, skipped)

### Warnings

List any warnings encountered during execution:
- Non-critical agent failures that were continued past
- Resource limit warnings
- Partial results or degraded quality indicators
- Missing optional dependencies
"""
```

---

## How Coordinators Spawn Agents

Coordinators spawn specialist agents using the **Agent tool** with a `subagent_type` matching the agent definition. Each agent is created as an independent task.

### Spawning Algorithm

```python
def coordinator_spawn_agent(
    agent_def: dict,
    batch_context: dict,
    team_definition: dict,
    project_root: str
) -> dict:
    """
    Spawn a specialist agent from the coordinator.

    The coordinator calls this conceptual function for each agent task.
    In practice, the coordinator uses the Agent tool directly.

    Steps:
    1. Build agent prompt from agent definition body + batch context
    2. Determine subagent_type from agent definition
    3. Create task via TaskCreate
    4. Return task handle for tracking

    Args:
        agent_def: Parsed agent definition dict
        batch_context: Context for this specific agent instance
            - batch_number: int
            - targets: list of files/modules assigned to this agent
            - dependencies_output: output from upstream agents (if any)
        team_definition: Full team definition
        project_root: Project root path

    Returns:
        dict with task_id and metadata
    """
    # STEP 1: Build agent prompt
    agent_prompt = build_agent_prompt(agent_def, batch_context, team_definition, project_root)

    # STEP 2: Determine subagent_type
    subagent_type = agent_def.get('subagent_type', 'general-purpose')

    # STEP 3: Create task via TaskCreate
    # TaskCreate is the Claude Code tool for creating agent tasks.
    # It returns a task_id that can be used to track completion.
    task_id = TaskCreate({
        'description': f"{agent_def['name']} - Batch {batch_context.get('batch_number', 1)}",
        'prompt': agent_prompt,
        'subagent_type': subagent_type
    })

    return {
        'task_id': task_id,
        'agent_name': agent_def['name'],
        'agent_type': agent_def.get('type', f"agents/{agent_def['name']}.md"),
        'batch_number': batch_context.get('batch_number', 1),
        'start_time': current_timestamp_utc()
    }


def build_agent_prompt(
    agent_def: dict,
    batch_context: dict,
    team_definition: dict,
    project_root: str
) -> str:
    """
    Build the complete prompt for a specialist agent.

    The prompt combines:
    1. Agent definition body (instructions)
    2. Batch-specific context (targets, dependencies output)
    3. Constraints (timeout, tools, output format)

    Args:
        agent_def: Parsed agent definition
        batch_context: Batch-specific context
        team_definition: Team definition
        project_root: Project root

    Returns:
        Complete agent prompt string
    """
    body = agent_def.get('body', '')

    # Build context section
    context_lines = []
    context_lines.append("# Execution Context")
    context_lines.append("")
    context_lines.append(f"- **Project Root**: {project_root}")
    context_lines.append(f"- **Team**: {team_definition['name']}")

    # Add batch targets
    targets = batch_context.get('targets', [])
    if targets:
        context_lines.append(f"- **Assigned Targets** ({len(targets)}):")
        for target in targets:
            context_lines.append(f"  - {target}")

    # Add upstream dependency output
    deps_output = batch_context.get('dependencies_output')
    if deps_output:
        context_lines.append("")
        context_lines.append("## Upstream Agent Output")
        context_lines.append("")
        context_lines.append(str(deps_output))

    context_section = "\n".join(context_lines)

    # Assemble prompt
    prompt = f"{body}\n\n---\n\n{context_section}"

    return prompt
```

---

## How Coordinators Monitor Completion

Coordinators track agent task completion using `TaskUpdate` and handle failures according to the team's failure handling strategy.

### Monitoring Algorithm

```python
def coordinator_monitor_tasks(
    active_tasks: list,
    team_definition: dict,
    coordinator_id: str,
    project_root: str,
    team_name: str
) -> dict:
    """
    Monitor active agent tasks and collect results.

    The coordinator polls TaskUpdate for each active task until all
    tasks complete or a failure triggers abort.

    Steps:
    1. For each active task, check status via TaskUpdate
    2. Collect completed task outputs
    3. Handle failures (retry or continue/abort per team config)
    4. Return aggregated results

    Args:
        active_tasks: List of task dicts from coordinator_spawn_agent()
        team_definition: Team definition with failure_handling config
        coordinator_id: Coordinator ID for telemetry
        project_root: Project root
        team_name: Team name

    Returns:
        dict with completed_tasks, failed_tasks, warnings
    """
    completed_tasks = []
    failed_tasks = []
    warnings = []

    failure_handling = team_definition.get('failure_handling', 'continue')
    retry_config = team_definition.get('retry_config', {'max_retries': 3})

    pending = list(active_tasks)

    while pending:
        newly_completed = []

        for task in pending:
            task_id = task['task_id']

            # Check task status via TaskUpdate
            status = TaskUpdate(task_id)

            if status['completed']:
                if status['success']:
                    completed_tasks.append({
                        'task_id': task_id,
                        'agent_name': task['agent_name'],
                        'agent_type': task['agent_type'],
                        'status': 'completed',
                        'output': status['output'],
                        'error': None,
                        'duration_seconds': elapsed_since(task['start_time'])
                    })
                else:
                    # Task failed
                    failed_task = {
                        'task_id': task_id,
                        'agent_name': task['agent_name'],
                        'agent_type': task['agent_type'],
                        'status': 'failed',
                        'output': None,
                        'error': status.get('error', 'Unknown error'),
                        'duration_seconds': elapsed_since(task['start_time'])
                    }

                    failed_tasks.append(failed_task)
                    warnings.append(
                        f"Agent '{task['agent_name']}' failed: {status.get('error', 'Unknown')}"
                    )

                    # Check failure handling strategy
                    if failure_handling == 'abort':
                        warnings.append("Aborting team execution due to agent failure (failure_handling: abort)")
                        # Cancel remaining tasks
                        for remaining_task in pending:
                            if remaining_task['task_id'] != task_id:
                                failed_tasks.append({
                                    'task_id': remaining_task['task_id'],
                                    'agent_name': remaining_task['agent_name'],
                                    'agent_type': remaining_task['agent_type'],
                                    'status': 'cancelled',
                                    'output': None,
                                    'error': 'Cancelled due to abort',
                                    'duration_seconds': elapsed_since(remaining_task['start_time'])
                                })
                        return {
                            'completed_tasks': completed_tasks,
                            'failed_tasks': failed_tasks,
                            'warnings': warnings,
                            'aborted': True
                        }

                newly_completed.append(task)

        # Remove completed tasks from pending
        for task in newly_completed:
            pending.remove(task)

    return {
        'completed_tasks': completed_tasks,
        'failed_tasks': failed_tasks,
        'warnings': warnings,
        'aborted': False
    }
```

---

## Auto-Generation Mode (coordinator: auto)

When a team definition specifies `coordinator: auto`, the orchestrator generates a coordinator prompt automatically from the team definition. This eliminates the need for a separate coordinator file for simple teams.

### When to Use Auto-Generation

- Teams with straightforward sequential or parallel agent workflows
- Teams where all agents are independent (no complex batching logic)
- Prototyping new teams before writing a custom coordinator
- Simple teams where the default parallelization strategy is sufficient

### When NOT to Use Auto-Generation

- Teams requiring custom batching strategies (e.g., file-based sharding)
- Teams with complex dependency resolution logic
- Teams that need custom result merging
- Teams where the coordinator performs analysis before spawning agents

### Auto-Generation Algorithm

```python
def generate_auto_coordinator(
    team_definition: dict,
    execution_plan: dict,
    agent_definitions: list,
    context: dict,
    project_root: str
) -> str:
    """
    Generate a coordinator prompt from a team definition.

    The auto-generated coordinator follows a standard workflow:
    1. Accept context (injected)
    2. For each phase in the execution plan:
       a. Spawn agents for that phase via TaskCreate
       b. Wait for all agents to complete via TaskUpdate
       c. Collect results
    3. Aggregate results and produce output

    Used when team definition specifies coordinator: auto

    Args:
        team_definition: Full team definition
        execution_plan: Execution plan with phases
        agent_definitions: Parsed agent definitions
        context: Execution context
        project_root: Project root

    Returns:
        Generated coordinator prompt string
    """
    team_name = team_definition['name']
    phases = execution_plan.get('phases', [])
    failure_handling = team_definition.get('failure_handling', 'continue')
    max_agents = team_definition.get('max_agents', 5)

    lines = []

    # Header
    lines.append(f"# Auto-Generated Coordinator for {team_name}")
    lines.append("")
    lines.append("This coordinator was auto-generated from the team definition.")
    lines.append("It executes agents in the phases defined by the dependency graph.")
    lines.append("")

    # Execution instructions
    lines.append("## Execution Instructions")
    lines.append("")
    lines.append(f"Execute the following {len(phases)} phase(s) in order.")
    lines.append(f"Maximum concurrent agents: {max_agents}")
    lines.append(f"Failure handling: {failure_handling}")
    lines.append("")

    for phase in phases:
        phase_num = phase['phase_number']
        parallel = phase.get('parallel', False)
        agent_names = phase.get('agent_names', [])
        mode = "in parallel" if parallel else "sequentially"

        lines.append(f"### Phase {phase_num}: Execute {mode}")
        lines.append("")
        lines.append(f"Spawn the following agent(s) {mode}:")
        lines.append("")

        for agent_name in agent_names:
            # Find agent definition
            agent_def = next(
                (a for a in agent_definitions if a.get('name') == agent_name),
                None
            )
            if agent_def:
                lines.append(f"- **{agent_name}** (`{agent_def.get('type', 'agents/' + agent_name + '.md')}`)")
                lines.append(f"  - Description: {agent_def.get('description', 'No description')}")
                lines.append(f"  - Model: {agent_def.get('model', 'sonnet')}")
                critical = agent_def.get('critical', False)
                if critical:
                    lines.append(f"  - CRITICAL: Failure aborts team execution")
                instances = agent_def.get('max_instances', 1)
                if instances > 1:
                    lines.append(f"  - Spawn up to {instances} parallel instances")
            else:
                lines.append(f"- **{agent_name}** (definition not found)")

        lines.append("")

        if phase_num < len(phases):
            lines.append(f"Wait for all Phase {phase_num} agents to complete before starting Phase {phase_num + 1}.")
            lines.append("")

    # Failure handling instructions
    lines.append("## Failure Handling")
    lines.append("")
    if failure_handling == 'continue':
        lines.append("If an agent fails after exhausting retries:")
        lines.append("- Log the failure with reason")
        lines.append("- Continue with remaining agents")
        lines.append("- Include the failure in the final report")
        lines.append("- EXCEPTION: If a CRITICAL agent fails, abort the entire team execution")
    elif failure_handling == 'abort':
        lines.append("If any agent fails after exhausting retries:")
        lines.append("- Abort the entire team execution")
        lines.append("- Cancel all remaining agents")
        lines.append("- Report the failure as the primary error")
    lines.append("")

    # Output instructions
    lines.append("## Output Requirements")
    lines.append("")
    lines.append("After all phases complete, produce output with:")
    lines.append("")
    lines.append("1. **Tasks Created**: List each agent task with ID, status, output, and duration")
    lines.append("2. **Final Result Summary**: Aggregate results from all agents including:")
    lines.append("   - Human-readable summary of what was accomplished")
    lines.append("   - List of files created and modified")
    lines.append("   - Key metrics from agent outputs")
    lines.append("   - Test results (if applicable)")
    lines.append("3. **Warnings**: Any non-critical issues encountered")
    lines.append("")

    return "\n".join(lines)
```

### Detection and Invocation

```python
def resolve_coordinator(team_definition: dict, project_root: str) -> dict:
    """
    Resolve the coordinator for a team, handling both file-based
    and auto-generated coordinators.

    Args:
        team_definition: Team definition with coordinator field
        project_root: Project root path

    Returns:
        dict with:
            mode: "file" | "auto"
            coordinator_path: str (for file mode) or None
            coordinator_body: str (coordinator instructions)
    """
    coordinator_value = team_definition.get('coordinator', '')

    if coordinator_value == 'auto':
        # Auto-generation mode
        return {
            'mode': 'auto',
            'coordinator_path': None,
            'coordinator_body': None  # Generated at prompt construction time
        }
    else:
        # File-based coordinator
        full_path = os.path.join(project_root, coordinator_value)
        if not os.path.exists(full_path):
            return {
                'mode': 'file',
                'coordinator_path': coordinator_value,
                'coordinator_body': None,
                'error': f"Coordinator file not found: {coordinator_value}"
            }

        body = read_coordinator_body(full_path)
        return {
            'mode': 'file',
            'coordinator_path': coordinator_value,
            'coordinator_body': body
        }
```

---

## Full Coordinator Invocation Workflow

```python
def invoke_coordinator(
    team_definition: dict,
    execution_plan: dict,
    config_overrides: dict,
    agent_definitions: list,
    context: dict,
    project_root: str
) -> dict:
    """
    Full coordinator invocation workflow.

    Steps:
    1. Resolve coordinator (file or auto-generate)
    2. Construct coordinator prompt with injected context
    3. Spawn coordinator as general-purpose agent via Agent tool
    4. Wait for coordinator to complete
    5. Parse and validate coordinator output
    6. Return structured result

    Args:
        team_definition: Full team definition
        execution_plan: Execution plan
        config_overrides: CLI overrides
        agent_definitions: Agent definitions
        context: Execution context
        project_root: Project root

    Returns:
        Coordinator result dict
    """
    coordinator_value = team_definition.get('coordinator', '')

    # STEP 1: Resolve coordinator
    if coordinator_value == 'auto':
        # Auto-generate coordinator prompt
        auto_prompt = generate_auto_coordinator(
            team_definition=team_definition,
            execution_plan=execution_plan,
            agent_definitions=agent_definitions,
            context=context,
            project_root=project_root
        )
        coordinator_body = auto_prompt
    else:
        # Read coordinator file
        resolve_result = resolve_coordinator(team_definition, project_root)
        if resolve_result.get('error'):
            return {'error': resolve_result['error']}
        coordinator_body = resolve_result['coordinator_body']

    # STEP 2: Construct full prompt with context injection
    context_block = build_context_injection(
        team_definition=team_definition,
        execution_plan=execution_plan,
        config_overrides=config_overrides,
        agent_definitions=agent_definitions,
        context=context,
        project_root=project_root
    )

    output_requirements = build_output_requirements()

    full_prompt = (
        f"{coordinator_body}\n\n"
        f"---\n\n"
        f"{context_block}\n\n"
        f"---\n\n"
        f"{output_requirements}"
    )

    # STEP 3: Spawn coordinator via Agent tool
    # The coordinator is spawned as a general-purpose agent.
    # It has full access to TaskCreate, TaskUpdate, and other tools.
    coordinator_result = Agent(
        prompt=full_prompt,
        subagent_type='general-purpose'
    )

    # STEP 4: Parse coordinator output
    parsed = parse_coordinator_output(coordinator_result)

    # STEP 5: Validate required output fields
    validation_errors = validate_coordinator_output(parsed)
    if validation_errors:
        return {
            'error': f"Coordinator output validation failed: {validation_errors}",
            'raw_output': coordinator_result,
            'parsed': parsed
        }

    return parsed


def parse_coordinator_output(raw_output: str) -> dict:
    """
    Parse the coordinator's raw output into the expected structure.

    The coordinator produces Markdown/structured text output. This
    function extracts the required sections:
    - tasks_created
    - final_result
    - warnings

    Args:
        raw_output: Raw text output from the coordinator agent

    Returns:
        Parsed coordinator result dict
    """
    # The coordinator's output is semi-structured.
    # We extract sections by heading or key patterns.
    result = {
        'tasks_created': [],
        'final_result': {
            'summary': '',
            'files_created': [],
            'files_modified': [],
            'metrics': {},
            'test_results': None
        },
        'warnings': []
    }

    # Parse tasks, results, and warnings from raw output
    # Implementation depends on the coordinator's output format
    # The result aggregator handles further normalization

    return result


def validate_coordinator_output(parsed: dict) -> list:
    """
    Validate that the coordinator output contains required fields.

    Required:
    - tasks_created (list, may be empty)
    - final_result.summary (string, non-empty)
    - warnings (list, may be empty)

    Returns:
        List of validation error strings (empty if valid)
    """
    errors = []

    if 'tasks_created' not in parsed:
        errors.append("Missing 'tasks_created' in coordinator output")

    if 'final_result' not in parsed:
        errors.append("Missing 'final_result' in coordinator output")
    elif not parsed['final_result'].get('summary'):
        errors.append("Missing 'final_result.summary' in coordinator output")

    if 'warnings' not in parsed:
        errors.append("Missing 'warnings' in coordinator output")

    return errors
```

---

## Error Handling

### Coordinator File Not Found

**Condition**: `coordinator` path in team definition points to non-existent file
**Behavior**: Validation error in team-loader.md (Phase 1). Execution never reaches coordinator invocation.
**Error Message**:
```
Coordinator file does not exist: teams/my-coordinator.md
```

### Auto-Generation with Missing Agent Definitions

**Condition**: `coordinator: auto` but agent definitions cannot be loaded
**Behavior**: Auto-generator produces a coordinator with warning notes for missing agents
**Warning**: "Agent definition not found for: {agent_name}"

### Coordinator Timeout

**Condition**: Coordinator agent exceeds team timeout
**Behavior**: Coordinator is terminated, team status set to `timed_out`
**Telemetry**: `lifecycle | coordinator | timed_out`

### Coordinator Output Validation Failure

**Condition**: Coordinator output missing required sections
**Behavior**: Return error with raw output for debugging. Result aggregator handles partial results.
**Error Message**: "Coordinator output validation failed: Missing 'tasks_created'"

### Agent Spawn Failure in Coordinator

**Condition**: TaskCreate fails for an agent (e.g., resource limit)
**Behavior**: Coordinator handles per failure_handling strategy. Logged as warning.
**Warning**: "Failed to create task for agent '{name}': {error}"

---

## Testing Checklist

For acceptance:

### Prompt Construction
- [ ] Reads coordinator file body (strips frontmatter)
- [ ] Builds context injection with all required sections
- [ ] Context includes: team definition, execution plan, CLI overrides, agent definitions
- [ ] Output requirements section is appended to prompt
- [ ] Handles coordinator files with and without frontmatter

### Context Injection
- [ ] Team definition section includes name, max_agents, timeout, failure_handling
- [ ] CLI overrides section lists all non-null overrides
- [ ] Execution plan section shows phases with agent assignments
- [ ] Agent definitions section includes name, description, model, tools, criticality
- [ ] Agent instructions (body) are included as quoted context
- [ ] Execution constraints section lists TaskCreate/TaskUpdate requirements

### Agent Spawning
- [ ] Coordinator spawns agents via TaskCreate
- [ ] Agent prompt includes agent body + batch context + upstream output
- [ ] Subagent type matches agent definition
- [ ] Returns task_id for tracking

### Completion Monitoring
- [ ] Tracks tasks via TaskUpdate
- [ ] Collects outputs from completed tasks
- [ ] Handles failed tasks per failure_handling strategy
- [ ] Abort strategy cancels remaining tasks on failure
- [ ] Continue strategy logs failure and proceeds

### Auto-Generation
- [ ] Generates coordinator for `coordinator: auto`
- [ ] Auto-coordinator includes all phases from execution plan
- [ ] Auto-coordinator includes failure handling instructions
- [ ] Auto-coordinator includes output format requirements
- [ ] Handles missing agent definitions gracefully (with warnings)

### Output Validation
- [ ] Validates tasks_created is present
- [ ] Validates final_result.summary is present and non-empty
- [ ] Validates warnings is present
- [ ] Returns errors for missing required fields
- [ ] Passes raw output for debugging on validation failure

---

## Example: Complete Coordinator File

```markdown
---
name: testing-parallel-coordinator
description: Coordinate parallel test generation across independent modules
model: sonnet
---

# Testing Parallel Coordinator

## Phase 1: Analysis

Spawn the **analyze-agent** to identify test targets in the project.

Use TaskCreate to create the analysis task:
- Read all source files in the target path
- Identify testable functions and classes
- Group targets into independent batches for parallel processing
- Return the batch assignments

Wait for the analyze-agent to complete before proceeding.

## Phase 2: Parallel Writing

For each batch identified by the analyze-agent, spawn a **write-agent** instance.

Each write-agent receives:
- Its assigned batch of test targets
- The analysis output from Phase 1
- Project coding standards

Spawn up to max_agents write-agents simultaneously.

## Phase 3: Test Execution

After all write-agents complete, spawn the **execute-agent** to:
- Run all generated tests
- Report pass/fail results
- Calculate coverage metrics

## Result Aggregation

Combine outputs from all agents:
- Merge file lists from all write-agents
- Sum test counts across batches
- Report overall pass rate and coverage
- List any failures with reasons
```

---

## References

- **Orchestrator**: `skills/team-orchestration/SKILL.md` (Phase 3, Phase 4)
- **Team Loader**: `skills/team-orchestration/team-loader.md` (validates coordinator path)
- **Agent Schema**: `skills/team-orchestration/agent-schema.md` (agent definition format)
- **Agent Lifecycle**: `skills/team-orchestration/agent-lifecycle-manager.md` (state tracking)
- **Result Aggregator**: `skills/team-orchestration/result-aggregator.md` (parses coordinator output)
- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-1, REQ-F-2)

---

**Last Updated**: 2026-03-25
**Status**: Implementation
