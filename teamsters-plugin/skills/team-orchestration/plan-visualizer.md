---
name: plan-visualizer
description: Generate ASCII dependency graphs and execution summaries for team execution plans, including phase visualization, critical path analysis, file dependency annotations, and dry-run mode output.
user-invocable: false
---

# Plan Visualizer Skill

**Version**: 1.0.0
**Category**: Presentation
**Purpose**: Generate human-readable ASCII visualizations of team execution plans, dependency graphs, and execution summaries

**Used By**: Team Orchestration SKILL (Phase 3 approval gate), Approval Gate Handler (plan display), `/team-run --dry-run`

---

## Overview

The Plan Visualizer Skill renders team execution plans as ASCII art dependency graphs with phase indicators, parallelism markers, estimated durations, and file dependency annotations. It produces clear, terminal-friendly output that helps users understand the execution flow before approving a plan.

This skill is critical for:
- **Clarity**: Making complex multi-agent execution plans immediately understandable
- **Decision Support**: Helping users make informed approval/rejection decisions at gates
- **Debugging**: Showing dependency relationships and critical paths for plan optimization
- **Dry-Run Mode**: Allowing plan inspection without execution via `--dry-run`

### Key Principles

1. **Terminal-Friendly**: Output must render correctly in any terminal (no Unicode box-drawing; ASCII only)
2. **Width-Aware**: Graphs should fit within 100 columns for standard terminal widths
3. **Information Dense**: Show phase numbers, parallelism, durations, and file annotations compactly
4. **Critical Path Highlighted**: Always identify and display the longest execution path
5. **Graceful Degradation**: If file dependency data is unavailable, omit annotations without error
6. **Consistent Style**: Match the formatting conventions used by approval-gate-handler.md

---

## Skill Interface

### Input

```yaml
# For generate_ascii_graph
execution_plan:
  phases: list                        # Phases from build_execution_plan()
  total_agents: integer               # Total agent count
  max_concurrent: integer             # Max parallel agents
  target_path: string | null          # Target path for the team
  estimated_time_minutes: float | null

file_graph: dict | null               # Optional file dependency graph from file-conflict-detector
team_def: dict                        # Team definition (for timeout, agent details)

# For generate_execution_summary
team_result: dict                     # Full TeamResult from orchestration
```

### Output

```yaml
# For generate_ascii_graph
ascii_graph: string                   # Multi-line ASCII art string ready for console display

# For generate_execution_summary
execution_summary: string             # Multi-line summary string ready for console display
```

---

## Core Algorithms

### Algorithm 1: Generate ASCII Graph

```python
def generate_ascii_graph(
    execution_plan: dict,
    file_graph: dict = None,
    team_def: dict = None
) -> str:
    """
    Generate an ASCII dependency graph from an execution plan.

    Renders a visual representation of the execution phases showing:
    - Phase numbers and parallel/sequential indicators
    - Agent names in brackets with connecting arrows
    - Estimated durations per agent (if available)
    - File dependency annotations (if file_graph provided)
    - Critical path highlighting

    Supports these topology patterns:
    - Linear: setup -> frontend -> tests
    - Parallel then sequential: backend + frontend -> tests
    - Diamond: test-writer -> backend + frontend -> verifier
    - Complex multi-phase with partial parallelism

    Args:
        execution_plan: Execution plan with phases from build_execution_plan()
        file_graph: Optional file dependency graph from file-conflict-detector
        team_def: Optional team definition for additional metadata

    Returns:
        Multi-line ASCII art string
    """
    phases = execution_plan.get('phases', [])

    if not phases:
        return "(empty execution plan - no agents to execute)"

    lines = []

    # Header
    total_agents = execution_plan.get('total_agents', 0)
    max_concurrent = execution_plan.get('max_concurrent', 5)
    target = execution_plan.get('target_path', 'project')

    lines.append("=" * 72)
    lines.append("EXECUTION PLAN")
    lines.append("=" * 72)
    lines.append(f"  Agents: {total_agents}  |  Max parallel: {max_concurrent}  |  Target: {target}")

    if team_def:
        timeout = team_def.get('timeout_minutes', 30)
        failure = team_def.get('failure_handling', 'continue')
        lines.append(f"  Timeout: {timeout}min  |  On failure: {failure}")

    lines.append("-" * 72)
    lines.append("")

    # Render each phase
    prev_agent_count = 0
    for phase_idx, phase in enumerate(phases):
        phase_number = phase.get('phase_number', phase_idx + 1)
        agent_names = phase.get('agent_names', [])
        is_parallel = phase.get('parallel', len(agent_names) > 1)

        phase_label = f"Phase {phase_number}"
        mode_label = "(parallel)" if is_parallel else "(sequential)"

        # Build agent boxes
        agent_boxes = []
        for agent_name in agent_names:
            duration = _get_agent_duration_estimate(agent_name, team_def)
            if duration:
                agent_boxes.append(f"[{agent_name} ~{duration}s]")
            else:
                agent_boxes.append(f"[{agent_name}]")

        # Render phase line(s)
        if is_parallel and len(agent_names) > 1:
            # Parallel agents: stack vertically with connection lines
            phase_lines = _render_parallel_phase(
                phase_label, mode_label, agent_boxes,
                has_next=(phase_idx < len(phases) - 1),
                prev_count=prev_agent_count
            )
        else:
            # Sequential (single agent): render inline
            phase_lines = _render_sequential_phase(
                phase_label, mode_label, agent_boxes,
                has_next=(phase_idx < len(phases) - 1),
                prev_count=prev_agent_count
            )

        lines.extend(phase_lines)
        prev_agent_count = len(agent_names)

    lines.append("")

    # Critical path
    critical_path = _compute_critical_path(phases, team_def)
    if critical_path:
        lines.append("-" * 72)
        lines.extend(critical_path)

    # File dependency annotations
    if file_graph:
        file_annotations = _render_file_annotations(phases, file_graph)
        if file_annotations:
            lines.append("-" * 72)
            lines.extend(file_annotations)

    lines.append("=" * 72)

    return '\n'.join(lines)
```

---

### Algorithm 2: Render Parallel Phase

```python
def _render_parallel_phase(
    phase_label: str,
    mode_label: str,
    agent_boxes: list,
    has_next: bool,
    prev_count: int
) -> list:
    """
    Render a parallel phase with vertically stacked agents and
    connection lines showing convergence to the next phase.

    Output example for 2 parallel agents:
        Phase 1 (parallel):   [backend ~45s]  ---+
                              [frontend ~65s] ---+
                                                 |
                                                 v

    Output example for 3 parallel agents:
        Phase 2 (parallel):   [unit-tests ~30s]    ---+
                              [lint-check ~10s]    ---+
                              [type-check ~15s]    ---+
                                                      |
                                                      v

    Args:
        phase_label: e.g., "Phase 1"
        mode_label: e.g., "(parallel)"
        agent_boxes: List of formatted agent strings
        has_next: Whether there is a subsequent phase
        prev_count: Number of agents in previous phase (for entry arrows)

    Returns:
        List of formatted lines
    """
    lines = []
    prefix = f"  {phase_label} {mode_label}:   "
    indent = " " * len(prefix)

    # Find the longest agent box for alignment
    max_box_len = max(len(box) for box in agent_boxes)

    for i, box in enumerate(agent_boxes):
        padded_box = box.ljust(max_box_len)
        if i == 0:
            # First agent gets the phase label
            if has_next:
                lines.append(f"{prefix}{padded_box} ---+")
            else:
                lines.append(f"{prefix}{padded_box}")
        else:
            # Subsequent agents are indented
            if has_next:
                lines.append(f"{indent}{padded_box} ---+")
            else:
                lines.append(f"{indent}{padded_box}")

    # Convergence arrow to next phase
    if has_next:
        # Calculate position for the vertical connector
        connector_pos = len(prefix) + max_box_len + 4
        connector_line = " " * connector_pos + "|"
        arrow_line = " " * connector_pos + "v"
        lines.append(connector_line)
        lines.append(arrow_line)

    lines.append("")

    return lines
```

---

### Algorithm 3: Render Sequential Phase

```python
def _render_sequential_phase(
    phase_label: str,
    mode_label: str,
    agent_boxes: list,
    has_next: bool,
    prev_count: int
) -> list:
    """
    Render a sequential (single-agent) phase with inline formatting.

    Output example:
        Phase 3 (sequential): [tests ~105s]
                                    |
                                    v

    For the first phase with no previous:
        Phase 1 (sequential): [setup ~10s]
                                   |
                                   v

    Args:
        phase_label: e.g., "Phase 3"
        mode_label: e.g., "(sequential)"
        agent_boxes: List with single agent string
        has_next: Whether there is a subsequent phase
        prev_count: Number of agents in previous phase

    Returns:
        List of formatted lines
    """
    lines = []
    prefix = f"  {phase_label} {mode_label}: "

    box = agent_boxes[0] if agent_boxes else "[unknown]"
    lines.append(f"{prefix}{box}")

    if has_next:
        # Arrow pointing down to next phase
        arrow_pos = len(prefix) + len(box) // 2
        lines.append(" " * arrow_pos + "|")
        lines.append(" " * arrow_pos + "v")

    lines.append("")

    return lines
```

---

### Algorithm 4: Compute Critical Path

```python
def _compute_critical_path(phases: list, team_def: dict = None) -> list:
    """
    Compute and format the critical path through the execution plan.

    The critical path is the longest path through the dependency graph
    by estimated duration. In a phased execution model, this is the
    sum of the longest agent in each phase (since phases are sequential
    and within-phase agents run in parallel).

    For parallel phases, the phase duration equals the slowest agent.
    For sequential phases, the phase duration equals the single agent.

    Args:
        phases: List of phase dicts from execution plan
        team_def: Optional team definition for duration estimates

    Returns:
        List of formatted lines showing critical path, or empty list
        if no duration estimates are available
    """
    lines = []
    path_segments = []
    total_estimated = 0
    has_estimates = False

    for phase in phases:
        agent_names = phase.get('agent_names', [])
        is_parallel = phase.get('parallel', len(agent_names) > 1)

        # Find the slowest agent in this phase (determines phase duration)
        max_duration = 0
        slowest_agent = None

        for agent_name in agent_names:
            duration = _get_agent_duration_estimate(agent_name, team_def)
            if duration is not None:
                has_estimates = True
                if duration > max_duration:
                    max_duration = duration
                    slowest_agent = agent_name

        if slowest_agent:
            path_segments.append({
                'agent': slowest_agent,
                'duration': max_duration,
                'parallel': is_parallel,
                'phase_agents': agent_names
            })
            total_estimated += max_duration

    if not has_estimates:
        return []

    lines.append("Critical Path:")

    # Format: agent1 (Xs) -> agent2 (Ys) -> agent3 (Zs) = ~total
    path_str_parts = []
    for segment in path_segments:
        agent = segment['agent']
        duration = segment['duration']
        if segment['parallel'] and len(segment['phase_agents']) > 1:
            # Indicate this is the bottleneck in a parallel phase
            path_str_parts.append(f"  {agent}* ({duration}s)")
        else:
            path_str_parts.append(f"  {agent} ({duration}s)")

    path_str = " -> ".join(path_str_parts)
    lines.append(f"{path_str}")
    lines.append(f"  Estimated total: ~{total_estimated}s (~{total_estimated // 60}m {total_estimated % 60}s)")

    if any(s['parallel'] for s in path_segments):
        lines.append("  (* = bottleneck in parallel phase)")

    lines.append("")

    return lines


def _get_agent_duration_estimate(agent_name: str, team_def: dict = None) -> int:
    """
    Get estimated execution duration for an agent.

    Duration estimates come from:
    1. Agent spec 'estimated_duration_seconds' field
    2. Historical telemetry data (future enhancement)
    3. Default heuristic based on agent type

    Args:
        agent_name: Name of the agent
        team_def: Team definition with agent specs

    Returns:
        Estimated duration in seconds, or None if no estimate available
    """
    if not team_def:
        return None

    agents = team_def.get('agents', [])
    for agent in agents:
        if agent.get('name') == agent_name:
            # Check for explicit estimate
            if 'estimated_duration_seconds' in agent:
                return agent['estimated_duration_seconds']

            # Default heuristic based on agent type name
            agent_type = agent.get('type', '')
            return _default_duration_heuristic(agent_type, agent_name)

    return None


def _default_duration_heuristic(agent_type: str, agent_name: str) -> int:
    """
    Provide a rough duration estimate based on agent type/name patterns.

    These are conservative defaults that help provide useful critical
    path information even without explicit estimates.

    Args:
        agent_type: Agent type path (e.g., "agents/test-agent.md")
        agent_name: Agent name (e.g., "unit-tests")

    Returns:
        Estimated duration in seconds, or None
    """
    name_lower = (agent_type + agent_name).lower()

    # Analysis/setup agents tend to be quick
    if any(kw in name_lower for kw in ['analyze', 'setup', 'lint', 'config']):
        return 15

    # Test execution agents vary by scope
    if any(kw in name_lower for kw in ['test', 'spec', 'check']):
        return 60

    # Write/generate agents (code generation)
    if any(kw in name_lower for kw in ['write', 'generate', 'create', 'build']):
        return 45

    # Verification/review agents
    if any(kw in name_lower for kw in ['verify', 'review', 'validate']):
        return 30

    # Default
    return None
```

---

### Algorithm 5: Render File Annotations

```python
def _render_file_annotations(phases: list, file_graph: dict) -> list:
    """
    Render file dependency annotations below the graph.

    Shows which agents read and write which files, grouped by phase,
    to help users understand data flow between agents.

    Output example:
        Files:
          Phase 1: backend writes src/server.ts, src/routes/*.ts
                   frontend writes public/index.html, public/styles/*.css
          Phase 2: tests reads src/**/*.ts, public/**/*

    Args:
        phases: List of phase dicts from execution plan
        file_graph: File dependency graph from file-conflict-detector

    Returns:
        List of formatted lines, or empty list if no file data
    """
    lines = []

    write_map = file_graph.get('write_map', {})
    read_map = file_graph.get('read_map', {})

    if not write_map and not read_map:
        return []

    # Build per-agent file summaries
    agent_writes = {}  # {agent_name: [file_paths]}
    agent_reads = {}   # {agent_name: [file_paths]}

    for file_path, agents in write_map.items():
        for agent in agents:
            if agent not in agent_writes:
                agent_writes[agent] = []
            agent_writes[agent].append(file_path)

    for file_path, agents in read_map.items():
        for agent in agents:
            if agent not in agent_reads:
                agent_reads[agent] = []
            agent_reads[agent].append(file_path)

    lines.append("Files:")

    for phase in phases:
        phase_number = phase.get('phase_number', 0)
        agent_names = phase.get('agent_names', [])
        phase_lines = []

        for agent_name in agent_names:
            writes = agent_writes.get(agent_name, [])
            reads = agent_reads.get(agent_name, [])

            parts = []
            if writes:
                file_list = _truncate_file_list(writes)
                parts.append(f"writes {file_list}")
            if reads:
                file_list = _truncate_file_list(reads)
                parts.append(f"reads {file_list}")

            if parts:
                phase_lines.append(f"    {agent_name} {', '.join(parts)}")

        if phase_lines:
            lines.append(f"  Phase {phase_number}:")
            lines.extend(phase_lines)

    lines.append("")

    return lines


def _truncate_file_list(files: list, max_display: int = 4) -> str:
    """
    Format a file list for display, truncating if too long.

    Args:
        files: List of file paths
        max_display: Maximum number of files to show before truncating

    Returns:
        Formatted string like "a.ts, b.ts, c.ts" or "a.ts, b.ts, +3 more"
    """
    if len(files) <= max_display:
        return ', '.join(files)
    else:
        shown = ', '.join(files[:max_display])
        remaining = len(files) - max_display
        return f"{shown}, +{remaining} more"
```

---

### Algorithm 6: Generate Execution Summary

```python
def generate_execution_summary(team_result: dict) -> str:
    """
    Generate a formatted execution summary from a completed team result.

    This is displayed after team execution completes (Phase 7) and in
    the after_completion approval gate. Shows final status, agent
    outcomes, timing metrics, and file changes.

    Args:
        team_result: Full TeamResult dict from orchestration Phase 7

    Returns:
        Multi-line formatted summary string
    """
    lines = []

    team_name = team_result.get('team_name', 'unknown')
    team_id = team_result.get('team_id', 'unknown')
    status = team_result.get('status', 'unknown')
    metrics = team_result.get('metrics', {})
    aggregated = team_result.get('aggregated_result', {})
    approval = team_result.get('approval_decisions', {})

    # Status banner
    lines.append("=" * 72)
    status_icon = _status_icon(status)
    lines.append(f"TEAM EXECUTION {status.upper()} {status_icon}")
    lines.append(f"  Team: {team_name}  |  ID: {team_id}")
    lines.append("=" * 72)
    lines.append("")

    # Agent outcomes
    total = aggregated.get('total_agents', 0)
    successful = aggregated.get('successful', 0)
    failed = aggregated.get('failed', 0)
    success_rate = metrics.get('success_rate', 0)

    lines.append("Agent Results:")
    lines.append(f"  Total: {total}  |  Passed: {successful}  |  Failed: {failed}  |  Rate: {success_rate:.0%}")
    lines.append("")

    # Per-agent details
    outputs = aggregated.get('outputs', [])
    failures = aggregated.get('failures', [])

    if outputs:
        lines.append("  Successful Agents:")
        for output in outputs:
            agent_id = output.get('agent_id', 'unknown')
            agent_type = output.get('agent_type', '')
            duration = output.get('metadata', {}).get('duration_seconds', 0)
            retry_count = output.get('metadata', {}).get('retry_count', 0)

            retry_str = f" (retries: {retry_count})" if retry_count > 0 else ""
            lines.append(f"    [OK]   {agent_id} ({duration:.1f}s){retry_str}")

    if failures:
        lines.append("")
        lines.append("  Failed Agents:")
        for failure in failures:
            agent_id = failure.get('agent_id', 'unknown')
            reason = failure.get('failure_reason', 'unknown')
            duration = failure.get('metadata', {}).get('duration_seconds', 0)
            retry_count = failure.get('metadata', {}).get('retry_count', 0)

            lines.append(f"    [FAIL] {agent_id} ({duration:.1f}s, {retry_count} retries)")
            lines.append(f"           Reason: {reason}")

    lines.append("")

    # Timing metrics
    total_duration = metrics.get('total_duration_seconds', 0)
    parallel_speedup = metrics.get('parallel_speedup')
    retry_count = metrics.get('retry_count', 0)

    lines.append("-" * 72)
    lines.append("Timing:")
    lines.append(f"  Total duration: {_format_duration(total_duration)}")

    if parallel_speedup and parallel_speedup > 1.0:
        lines.append(f"  Parallel speedup: {parallel_speedup:.1f}x vs sequential")

    agent_durations = metrics.get('agent_durations', {})
    if agent_durations:
        fastest = min(agent_durations.values()) if agent_durations else 0
        slowest = max(agent_durations.values()) if agent_durations else 0
        lines.append(f"  Fastest agent: {_format_duration(fastest)}")
        lines.append(f"  Slowest agent: {_format_duration(slowest)}")

    if retry_count > 0:
        lines.append(f"  Total retries: {retry_count}")

    lines.append("")

    # Merged files (if available)
    merged_files = aggregated.get('merged_files', [])
    if merged_files:
        lines.append("-" * 72)
        lines.append(f"Files Modified ({len(merged_files)}):")
        for file_path in merged_files[:20]:  # Cap display at 20
            lines.append(f"  {file_path}")
        if len(merged_files) > 20:
            lines.append(f"  ... and {len(merged_files) - 20} more")
        lines.append("")

    # Merged warnings (if available)
    merged_warnings = aggregated.get('merged_warnings', [])
    if merged_warnings:
        lines.append("-" * 72)
        lines.append(f"Warnings ({len(merged_warnings)}):")
        for warning in merged_warnings[:10]:  # Cap at 10
            lines.append(f"  - {warning}")
        if len(merged_warnings) > 10:
            lines.append(f"  ... and {len(merged_warnings) - 10} more")
        lines.append("")

    # Approval gate decisions
    before = approval.get('before_execution', 'N/A')
    after = approval.get('after_completion', 'N/A')
    lines.append("-" * 72)
    lines.append(f"Approval Gates:  before={before}  |  after={after}")

    # Telemetry
    telemetry_path = team_result.get('telemetry_log_path')
    if telemetry_path:
        lines.append(f"Telemetry log:   {telemetry_path}")

    # Error (if any)
    error = team_result.get('error')
    if error:
        lines.append("")
        lines.append(f"Error: {error}")

    lines.append("=" * 72)

    return '\n'.join(lines)


def _status_icon(status: str) -> str:
    """Return ASCII status indicator."""
    icons = {
        'completed': '[OK]',
        'partial_success': '[PARTIAL]',
        'failed': '[FAILED]',
        'aborted': '[ABORTED]',
        'timed_out': '[TIMEOUT]'
    }
    return icons.get(status, f'[{status.upper()}]')


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
```

---

### Algorithm 7: Generate Dry-Run Output

```python
def generate_dry_run_output(
    execution_plan: dict,
    team_def: dict,
    file_graph: dict = None,
    parallel_safety: dict = None
) -> str:
    """
    Generate comprehensive dry-run output for --dry-run mode.

    Combines the ASCII graph, file conflict analysis, critical path,
    and team configuration into a single output that shows exactly
    what would happen during execution - without actually executing.

    This is the primary output for:
        /team-run <team-name> --dry-run

    Args:
        execution_plan: Execution plan with phases
        team_def: Full team definition
        file_graph: Optional file dependency graph
        parallel_safety: Optional parallel safety result

    Returns:
        Multi-line formatted dry-run output string
    """
    lines = []

    team_name = team_def.get('name', 'unknown')
    version = team_def.get('version', '1.0.0')

    # Header
    lines.append("=" * 72)
    lines.append(f"DRY RUN: {team_name} v{version}")
    lines.append("=" * 72)
    lines.append("")
    lines.append("This is a plan preview. No agents will be spawned.")
    lines.append("")

    # Team configuration summary
    lines.append("-" * 72)
    lines.append("Team Configuration:")
    lines.append(f"  Name:             {team_name}")
    lines.append(f"  Coordinator:      {team_def.get('coordinator', 'N/A')}")
    lines.append(f"  Max agents:       {team_def.get('max_agents', 5)}")
    lines.append(f"  Timeout:          {team_def.get('timeout_minutes', 30)} minutes")
    lines.append(f"  Failure handling: {team_def.get('failure_handling', 'continue')}")
    lines.append(f"  Depth limit:      {team_def.get('depth_limit', 3)}")

    gates = team_def.get('approval_gates', {})
    before_gate = "enabled" if gates.get('before_execution', True) else "disabled"
    after_gate = "enabled" if gates.get('after_completion', True) else "disabled"
    lines.append(f"  Approval gates:   before={before_gate}, after={after_gate}")

    retry = team_def.get('retry_config', {})
    max_retries = retry.get('max_retries', 3)
    backoff = retry.get('backoff_seconds', [1, 2, 4])
    lines.append(f"  Retry config:     max={max_retries}, backoff={backoff}")
    lines.append("")

    # Agent roster
    agents = team_def.get('agents', [])
    if agents:
        lines.append("-" * 72)
        lines.append(f"Agent Roster ({len(agents)} agents):")
        lines.append("")

        for agent in agents:
            name = agent.get('name', 'unknown')
            agent_type = agent.get('type', 'unknown')
            critical = agent.get('critical', False)
            instances = agent.get('max_instances', 1)
            deps = agent.get('dependencies', [])

            critical_str = " [CRITICAL]" if critical else ""
            instance_str = f" x{instances}" if instances > 1 else ""
            dep_str = f"  deps: {', '.join(deps)}" if deps else ""

            lines.append(f"  {name}{critical_str}{instance_str}")
            lines.append(f"    type: {agent_type}{dep_str}")

            # File access (if available)
            files_read = agent.get('files_read', [])
            files_write = agent.get('files_write', [])
            if files_read:
                lines.append(f"    reads:  {_truncate_file_list(files_read)}")
            if files_write:
                lines.append(f"    writes: {_truncate_file_list(files_write)}")

        lines.append("")

    # Execution plan graph
    lines.append("-" * 72)
    graph = generate_ascii_graph(execution_plan, file_graph, team_def)
    lines.append(graph)
    lines.append("")

    # File conflict analysis (if available)
    if parallel_safety:
        if not parallel_safety.get('safe', True):
            lines.append("-" * 72)
            lines.append("FILE CONFLICT WARNINGS:")
            lines.append("")
            for conflict in parallel_safety.get('conflicts', []):
                severity = conflict.get('severity', 'warning').upper()
                lines.append(f"  [{severity}] {conflict.get('description', '')}")
            lines.append("")

            fixes = parallel_safety.get('suggested_fixes', [])
            if fixes:
                lines.append("  Suggested Fixes:")
                for idx, fix in enumerate(fixes, 1):
                    lines.append(f"    {idx}. {fix.get('description', '')}")
                lines.append("")
        else:
            lines.append("-" * 72)
            lines.append("File Conflicts: None detected")
            lines.append("")

    # Dependency graph details
    deps = team_def.get('dependencies', [])
    if deps:
        lines.append("-" * 72)
        lines.append("Explicit Dependencies:")
        for dep in deps:
            dep_type = dep.get('type', 'sequential')
            lines.append(f"  {dep['from']} -> {dep['to']} ({dep_type})")
        lines.append("")

    # Implicit dependencies from file analysis
    if file_graph:
        implicit = file_graph.get('implicit_deps', [])
        if implicit:
            lines.append("Implicit Dependencies (from file analysis):")
            for dep in implicit:
                lines.append(f"  {dep['from']} -> {dep['to']} (via {dep['file']})")
            lines.append("")

    # Footer
    lines.append("=" * 72)
    lines.append("To execute this plan, run without --dry-run:")
    lines.append(f"  /team-run {team_name}")
    lines.append("=" * 72)

    return '\n'.join(lines)
```

---

## Output Examples

### Example 1: Linear Pipeline

```
========================================================================
EXECUTION PLAN
========================================================================
  Agents: 3  |  Max parallel: 5  |  Target: src/
  Timeout: 30min  |  On failure: continue
------------------------------------------------------------------------

  Phase 1 (sequential): [setup ~10s]
                              |
                              v

  Phase 2 (sequential): [frontend ~65s]
                                |
                                v

  Phase 3 (sequential): [tests ~105s]

------------------------------------------------------------------------
Critical Path:
  setup (10s) ->   frontend (65s) ->   tests (105s)
  Estimated total: ~180s (~3m 0s)

========================================================================
```

### Example 2: Parallel Then Sequential

```
========================================================================
EXECUTION PLAN
========================================================================
  Agents: 3  |  Max parallel: 5  |  Target: src/
  Timeout: 30min  |  On failure: continue
------------------------------------------------------------------------

  Phase 1 (parallel):   [backend ~45s]  ---+
                         [frontend ~65s] ---+
                                            |
                                            v

  Phase 2 (sequential): [tests ~105s]

------------------------------------------------------------------------
Critical Path:
  frontend* (65s) ->   tests (105s)
  Estimated total: ~170s (~2m 50s)
  (* = bottleneck in parallel phase)

------------------------------------------------------------------------
Files:
  Phase 1:
    backend writes src/server.ts, src/routes/*.ts
    frontend writes public/index.html, public/styles/*.css
  Phase 2:
    tests reads src/**/*.ts, public/**/*
========================================================================
```

### Example 3: Diamond Pattern

```
========================================================================
EXECUTION PLAN
========================================================================
  Agents: 4  |  Max parallel: 5  |  Target: project
  Timeout: 30min  |  On failure: continue
------------------------------------------------------------------------

  Phase 1 (sequential): [test-writer ~30s]
                                  |
                                  v

  Phase 2 (parallel):   [backend ~45s]  ---+
                         [frontend ~65s] ---+
                                            |
                                            v

  Phase 3 (sequential): [verifier ~20s]

------------------------------------------------------------------------
Critical Path:
  test-writer (30s) ->   frontend* (65s) ->   verifier (20s)
  Estimated total: ~115s (~1m 55s)
  (* = bottleneck in parallel phase)

========================================================================
```

### Example 4: Complex Multi-Phase

```
========================================================================
EXECUTION PLAN
========================================================================
  Agents: 7  |  Max parallel: 5  |  Target: src/
  Timeout: 45min  |  On failure: abort
------------------------------------------------------------------------

  Phase 1 (sequential): [analyze ~15s]
                               |
                               v

  Phase 2 (parallel):   [backend ~45s]     ---+
                         [frontend ~65s]    ---+
                         [api-client ~40s]  ---+
                                               |
                                               v

  Phase 3 (parallel):   [unit-tests ~60s]   ---+
                         [integration ~90s]  ---+
                                                |
                                                v

  Phase 4 (sequential): [verifier ~20s]

------------------------------------------------------------------------
Critical Path:
  analyze (15s) ->   frontend* (65s) ->   integration* (90s) ->   verifier (20s)
  Estimated total: ~190s (~3m 10s)
  (* = bottleneck in parallel phase)

------------------------------------------------------------------------
Files:
  Phase 1:
    analyze reads src/**/*.ts, package.json
  Phase 2:
    backend writes src/server.ts, src/routes/*.ts
    frontend writes public/*, src/components/**/*.tsx
    api-client writes src/api/*.ts
  Phase 3:
    unit-tests reads src/**/*.ts, writes tests/unit/**/*.test.ts
    integration reads src/**/*.ts, writes tests/integration/**/*.test.ts
  Phase 4:
    verifier reads tests/**/*.test.ts, src/**/*.ts
========================================================================
```

### Example 5: Execution Summary

```
========================================================================
TEAM EXECUTION PARTIAL_SUCCESS [PARTIAL]
  Team: testing-parallel  |  ID: testing-parallel-20260325T143000
========================================================================

Agent Results:
  Total: 4  |  Passed: 3  |  Failed: 1  |  Rate: 75%

  Successful Agents:
    [OK]   analyze-agent (15.2s)
    [OK]   write-agent-1 (28.5s)
    [OK]   write-agent-3 (30.0s)

  Failed Agents:
    [FAIL] write-agent-2 (127.3s, 3 retries)
           Reason: Agent execution timed out after 120s

------------------------------------------------------------------------
Timing:
  Total duration: 3m 18s
  Parallel speedup: 1.8x vs sequential
  Fastest agent: 15.2s
  Slowest agent: 127.3s
  Total retries: 3

------------------------------------------------------------------------
Files Modified (5):
  tests/test_calculator.py
  tests/test_user.py
  tests/test_auth.py
  tests/test_api.py
  tests/conftest.py

------------------------------------------------------------------------
Approval Gates:  before=approve  |  after=approve
Telemetry log:   .claude/telemetry/testing-parallel/2026-03-25.jsonl
========================================================================
```

---

## Integration Points

### Integration with Approval Gate Handler

```python
# In approval-gate-handler.md, Phase 3 before_execution gate:

def display_execution_plan(team_config, execution_plan, file_graph=None):
    """Display the execution plan using plan-visualizer."""
    # Generate ASCII graph
    graph = generate_ascii_graph(execution_plan, file_graph, team_config)
    display_to_user(graph)

    # In dry-run mode, also show full dry-run output
    if team_config.get('_dry_run', False):
        parallel_safety = None
        if file_graph:
            parallel_safety = validate_parallel_safety(execution_plan, file_graph)
        dry_run = generate_dry_run_output(
            execution_plan, team_config, file_graph, parallel_safety
        )
        display_to_user(dry_run)
```

### Integration with Team Orchestration SKILL

```python
# In SKILL.md, Phase 3 (plan building):

# After building execution plan, generate visualization
ascii_graph = generate_ascii_graph(
    execution_plan,
    file_graph=team_def.get('_file_dependency_graph'),
    team_def=team_def
)
log_telemetry('coordination', coordinator_id, 'plan_visualized', {
    'ascii_graph': ascii_graph,
    'graph_lines': ascii_graph.count('\n') + 1
}, project_root, team_name)

# In Phase 7 (finalize), generate execution summary:
summary = generate_execution_summary(team_result)
display_to_user(summary)
```

### Integration with /team-run --dry-run

```python
# In commands/team-run.md:

if args.dry_run:
    # Load team definition
    load_result = load_team_definition(team_name, project_root)
    if not load_result['validation_result']['valid']:
        display_errors(load_result['validation_result']['errors'])
        return

    team_def = load_result['team_definition']

    # Build execution plan
    execution_plan = build_execution_plan(
        team_def.get('agents', []),
        team_def.get('dependencies', []),
        team_def, context
    )

    # File conflict analysis
    file_graph = team_def.get('_file_dependency_graph')
    parallel_safety = None
    if file_graph:
        parallel_safety = validate_parallel_safety(execution_plan, file_graph)

    # Generate and display dry-run output
    output = generate_dry_run_output(
        execution_plan, team_def, file_graph, parallel_safety
    )
    display_to_user(output)
    return  # Exit without execution
```

---

## Error Handling

### Empty Execution Plan

**Condition**: No phases in execution plan
**Behavior**: Return minimal message: `"(empty execution plan - no agents to execute)"`

### No Duration Estimates

**Condition**: No agents have `estimated_duration_seconds` and heuristic returns None
**Behavior**: Omit critical path section entirely. Graph renders without duration annotations.

### Missing File Graph

**Condition**: `file_graph` parameter is None
**Behavior**: Omit file annotations. Graph renders without file dependency information.

### Very Wide Agent Names

**Condition**: Agent names exceed 30 characters
**Behavior**: Truncate display name to 27 chars + "..." in graph. Full name shown in roster.

```python
def _truncate_name(name: str, max_len: int = 30) -> str:
    """Truncate agent name for graph display."""
    if len(name) <= max_len:
        return name
    return name[:max_len - 3] + "..."
```

### Many Parallel Agents

**Condition**: Phase has more than 8 parallel agents
**Behavior**: Show first 6 agents, then `... and N more` line.

```python
MAX_DISPLAYED_PARALLEL = 6

def _render_parallel_phase_with_limit(agent_boxes: list, ...) -> list:
    """Render parallel phase, truncating if too many agents."""
    if len(agent_boxes) <= MAX_DISPLAYED_PARALLEL:
        return _render_parallel_phase(...)

    # Show first MAX_DISPLAYED_PARALLEL agents
    visible = agent_boxes[:MAX_DISPLAYED_PARALLEL]
    hidden = len(agent_boxes) - MAX_DISPLAYED_PARALLEL
    visible.append(f"[... and {hidden} more agents]")

    return _render_parallel_phase(..., agent_boxes=visible)
```

---

## Testing Checklist

For acceptance:

### ASCII Graph Generation
- [ ] Renders empty plan with appropriate message
- [ ] Renders single-phase single-agent (simplest case)
- [ ] Renders single-phase multiple agents (parallel)
- [ ] Renders linear pipeline (3+ sequential phases)
- [ ] Renders parallel-then-sequential pattern
- [ ] Renders diamond pattern (fan-out then fan-in)
- [ ] Renders complex multi-phase with partial parallelism
- [ ] Phase numbers are correct and sequential
- [ ] Parallel/sequential labels are accurate
- [ ] Arrows connect phases correctly
- [ ] Graph fits within 100 columns
- [ ] Duration estimates shown when available
- [ ] Duration estimates omitted when unavailable
- [ ] Agent names truncated when too long
- [ ] Many parallel agents handled (>8 truncated)

### Critical Path
- [ ] Identifies correct critical path for linear pipeline
- [ ] Identifies bottleneck agent in parallel phases
- [ ] Calculates total estimated duration correctly
- [ ] Marks bottleneck agents with asterisk
- [ ] Omits critical path when no estimates available
- [ ] Handles single-phase plans (trivial path)

### File Annotations
- [ ] Renders file read/write annotations per phase
- [ ] Truncates long file lists gracefully
- [ ] Omits file section when no file data available
- [ ] Shows both reads and writes per agent

### Execution Summary
- [ ] Shows correct status banner with icon
- [ ] Lists all successful agents with durations
- [ ] Lists all failed agents with reasons and retry counts
- [ ] Shows timing metrics (total, speedup, fastest/slowest)
- [ ] Shows merged files list (truncated at 20)
- [ ] Shows warnings (truncated at 10)
- [ ] Shows approval gate decisions
- [ ] Shows telemetry log path when available
- [ ] Shows error message when team failed

### Dry-Run Output
- [ ] Shows team configuration summary
- [ ] Shows agent roster with types and dependencies
- [ ] Shows file access patterns per agent
- [ ] Includes ASCII graph
- [ ] Includes file conflict warnings when present
- [ ] Shows explicit and implicit dependencies
- [ ] Footer shows command to execute without dry-run
- [ ] No agents are spawned during dry-run

### Edge Cases
- [ ] Handles agents with no name gracefully
- [ ] Handles missing team_def gracefully
- [ ] Handles phases with empty agent lists
- [ ] Output is valid ASCII (no Unicode box-drawing)
- [ ] Output renders correctly with monospace font

---

## References

- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md`
- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-2, REQ-F-17)
- Approval Gate: `skills/team-orchestration/approval-gate-handler.md` (display integration)
- File Conflict Detector: `skills/team-orchestration/file-conflict-detector.md` (file annotations)
- Team Orchestration: `skills/team-orchestration/SKILL.md` (orchestration integration)

---

**Last Updated**: 2026-03-25
**Status**: Implementation (P1 Improvement)
