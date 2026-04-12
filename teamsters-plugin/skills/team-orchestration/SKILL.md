---
name: team-orchestration
description: Coordinator entry point for hierarchical agent team orchestration. Manages the full workflow from team definition loading through agent spawning, lifecycle tracking, retry logic, result aggregation, and approval gates.
user-invocable: false
---

# Team Orchestration Skill

**Version**: 1.0.0
**Category**: Orchestration
**Purpose**: Coordinate the complete lifecycle of a team execution using the coordinator-specialist pattern (REQ-F-1)

**Invoked By**: `/team-run` command (`commands/team-run.md`)

**Warning LEGACY/FALLBACK IMPLEMENTATION**: As of 2026-02-18, `/team-run` **prefers Claude Code's built-in TeamCreate tool** over this custom orchestration skill. This skill is maintained for:
- Fallback when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not set
- Backward compatibility with existing team definitions
- Custom retry logic or approval gates not supported by built-in system

**Built-in team system advantages**:
- Native support for shared task lists (`~/.claude/tasks/{team-name}/`)
- Automatic agent lifecycle tracking
- Peer-to-peer communication via SendMessage
- Team configuration at `~/.claude/teams/{team-name}/config.json`
- Simpler coordinator pattern (team lead + teammates)

---

## Overview

The Team Orchestration Skill is the **coordinator entry point** for all team executions. It receives a team name and configuration, then orchestrates the full workflow by invoking sub-skills in sequence:

1. **Load**: Load and validate the team definition via `team-loader.md`
2. **Approve (Before)**: Present the execution plan to the user via `approval-gate-handler.md`
3. **Spawn**: Create specialist agents via the Task tool, respecting limits from `resource-manager.md`
4. **Monitor**: Track agent lifecycle and handle retries via `agent-lifecycle-manager.md`
5. **Aggregate**: Combine results from all agents via `result-aggregator.md`
6. **Approve (After)**: Present results to the user via `approval-gate-handler.md`
7. **Log**: Record all events throughout via `skills/telemetry/SKILL.md`

This skill implements the **coordinator-specialist pattern** (REQ-F-1) where the coordinator spawns specialist agents via the Task tool and manages their lifecycle. Specialist agents execute independently and in parallel where dependencies allow.

### Key Principles

1. **Fail Fast on Invalid Input**: Validate team definitions completely before spawning any agents
2. **Respect Resource Limits**: Never exceed configured agent/team/depth limits
3. **Retry with Backoff**: Failed agents get up to 3 retries with exponential backoff [1, 2, 4] seconds
4. **Graceful Failure Handling**: Continue with remaining agents or abort based on team configuration
5. **Non-Blocking Telemetry**: Log all events but never let telemetry failures halt execution
6. **User Control via Gates**: Approval gates give users control before and after execution

---

## Sub-Skills Orchestrated

| Sub-Skill | File | Purpose |
|-----------|------|---------|
| Team Loader | `skills/team-orchestration/team-loader.md` | Load and validate team definitions from `teams/` |
| Agent Lifecycle Manager | `skills/team-orchestration/agent-lifecycle-manager.md` | Track agent state machine (spawned -> running -> completed/failed) |
| Resource Manager | `skills/team-orchestration/resource-manager.md` | Enforce limits (5 agents/team, 5 concurrent teams, depth <= 3), FIFO queuing |
| Approval Gate Handler | `skills/team-orchestration/approval-gate-handler.md` | Handle before_execution and after_completion approval gates |
| Result Aggregator | `skills/team-orchestration/result-aggregator.md` | Combine outputs from parallel agents with partial failure handling |
| Agent Schema | `skills/team-orchestration/agent-schema.md` | Agent definition format validation and template resolution |
| Coordinator Schema | `skills/team-orchestration/coordinator-schema.md` | Coordinator interface contract and auto-generation |
| File Conflict Detector | `skills/team-orchestration/file-conflict-detector.md` | File dependency graph analysis and write-write conflict detection |
| Plan Visualizer | `skills/team-orchestration/plan-visualizer.md` | ASCII dependency graph rendering and dry-run output |
| Telemetry | `skills/telemetry/SKILL.md` | Non-blocking structured event logging for observability |
| Event Types | `skills/telemetry/event-types.md` | Event type JSON schemas and validation |
| Config Manager | `skills/model-selection/config-manager.md` | Configuration file loading and model recommendations |
| Model Resolver | `skills/model-selection/model-resolver.md` | Model precedence resolution chain |

---

## Skill Interface

### Input

```yaml
team_name: string                # Name of the team to execute (e.g., "testing-parallel")
project_root: string             # Absolute path to the project root directory
config_overrides:                # Optional CLI overrides (from /team-run flags)
  max_agents: integer | null     # Override max_agents from team definition
  timeout_minutes: integer | null # Override timeout from team definition
  approval_gates: string | null  # Override approval gates ("before", "after", "disabled")
  telemetry_enabled: boolean | null # Override telemetry setting
context:                         # Execution context passed from /team-run command
  target_path: string | null     # Target path for the team (e.g., "src/")
  additional_args: dict          # Any additional arguments from the command
  depth: integer                 # Current depth level (default: 1 for top-level invocation)
  parent_id: string | null       # Parent coordinator ID (null for top-level)
```

### Output

```yaml
team_result:
  team_id: string                    # Unique team execution ID
  team_name: string                  # Team name
  status: string                     # "completed" | "partial_success" | "failed" | "aborted" | "timed_out"

  # Aggregated outputs from all agents
  aggregated_result:
    total_agents: integer            # Total agents spawned
    successful: integer              # Agents that completed successfully
    failed: integer                  # Agents that failed (after retries)
    outputs: list                    # All successful agent outputs with metadata
    failures: list                   # Failed agents with reasons
    merged_files: list               # Deduplicated file list from all agents
    merged_metrics: dict             # Aggregated numeric metrics
    merged_warnings: list            # All warnings from all agents

  # Execution metrics
  metrics:
    total_duration_seconds: float    # Wall-clock time for entire team execution
    agent_durations: dict            # {agent_id: duration_seconds} for all agents
    success_rate: float              # successful / total_agents (0.0 to 1.0)
    parallel_speedup: float | null   # Estimated speedup vs sequential
    retry_count: integer             # Total retries across all agents
    models_used: dict                # {model: count} usage breakdown

  # Approval gate decisions
  approval_decisions:
    before_execution: string         # "approve" | "reject" | "bypassed"
    after_completion: string         # "approve" | "reject" | "bypassed"

  # Telemetry
  telemetry_log_path: string | null  # Path to telemetry log file (null if disabled)

  # Error information (if failed or aborted)
  error: string | null               # Error message if team failed
```

---

## Implementation Algorithm

### Phase 0: Initialize

```python
def execute_team(team_name: str, project_root: str, config_overrides: dict, context: dict) -> dict:
    """
    Main entry point for team orchestration.

    This function implements the coordinator-specialist pattern (REQ-F-1):
    the coordinator (this function) spawns and manages specialist agents
    via the Task tool.

    Args:
        team_name: Name of the team to execute
        project_root: Absolute path to project root
        config_overrides: CLI overrides from /team-run command
        context: Execution context (target_path, depth, parent_id)

    Returns:
        TeamResult dict with outputs, metrics, and status
    """
    # Generate unique team execution ID
    team_id = generate_team_id(team_name)
    coordinator_id = f"{team_name}-coordinator-{team_id}"
    depth = context.get('depth', 1)
    parent_id = context.get('parent_id', None)
    team_start_time = current_timestamp_utc()

    # Initialize telemetry log path (set after team definition loaded)
    telemetry_log_path = None

    # Helper: Display telemetry event to console (real-time, non-blocking)
    def display_telemetry_event(event_type, agent_id, status, metadata):
        """Output formatted telemetry event to console if console telemetry enabled."""
        try:
            if is_console_telemetry_enabled(team_def):
                write_to_console(event_type, agent_id, status, metadata)
        except Exception:
            pass  # Non-blocking

    # Log session start (verbose telemetry)
    log_telemetry('environment', coordinator_id, 'session_start', {
        'session_id': f"sess-{team_id}",
        'plugin_version': '1.0.0',
        'claude_code_version': None,
        'platform': sys.platform,
        'os_version': platform.platform(),
        'shell': os.environ.get('SHELL', 'unknown'),
        'working_directory': project_root,
        'git_branch': get_git_branch(project_root),
        'git_commit': get_git_commit(project_root),
        'git_dirty': is_git_dirty(project_root),
        'node_version': None,
        'python_version': sys.version
    }, project_root, team_name)
    display_telemetry_event('environment', coordinator_id, 'session_start', {
        'session_id': f"sess-{team_id}",
        'plugin_version': '1.0.0',
        'claude_code_version': None,
        'platform': sys.platform,
        'os_version': platform.platform(),
        'shell': os.environ.get('SHELL', 'unknown'),
        'working_directory': project_root,
        'git_branch': get_git_branch(project_root),
        'git_commit': get_git_commit(project_root),
        'git_dirty': is_git_dirty(project_root),
        'node_version': None,
        'python_version': sys.version
    })

    # Log environment snapshot (verbose telemetry)
    log_telemetry('environment', coordinator_id, 'environment_snapshot', {
        'teamsters_env_vars': {k: v for k, v in os.environ.items() if k.startswith('TEAMSTERS_')},
        'experimental_flags': {
            'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS': os.environ.get('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS')
        },
        'config_file_path': f"{project_root}/.claude/teamsters-config.json",
        'config_file_exists': os.path.exists(f"{project_root}/.claude/teamsters-config.json"),
        'teams_directory_exists': os.path.exists(f"{project_root}/teams"),
        'teams_available': list_teams(project_root),
        'agents_directory_exists': os.path.exists(f"{project_root}/agents")
    }, project_root, team_name)

    # Log coordinator spawn
    log_telemetry('lifecycle', coordinator_id, 'spawned', {
        'team_name': team_name,
        'team_id': team_id,
        'parent': parent_id,
        'depth': depth,
        'target_path': context.get('target_path')
    }, project_root, team_name)
    display_telemetry_event('lifecycle', coordinator_id, 'spawned', {
        'team_name': team_name,
        'team_id': team_id,
        'parent': parent_id,
        'depth': depth,
        'target_path': context.get('target_path')
    })
```

---

### Phase 1: Load and Validate Team Definition

```python
    # =========================================================================
    # PHASE 1: Load and validate team definition
    # Invokes: skills/team-orchestration/team-loader.md
    # =========================================================================

    # Step 1.1: Load team definition from teams/{team_name}.md
    load_result = load_team_definition(team_name, project_root)
    # load_team_definition() is defined in team-loader.md
    # It resolves the file path, parses YAML frontmatter, validates required
    # fields (name, coordinator, max_agents), checks coordinator/agent file
    # existence, detects circular dependencies, and enforces limits.

    # Step 1.2: Check validation result
    if not load_result['validation_result']['valid']:
        # Team definition is invalid - abort immediately
        errors = load_result['validation_result']['errors']
        error_summary = format_validation_errors(errors)

        log_telemetry('lifecycle', coordinator_id, 'failed', {
            'reason': 'validation_failed',
            'errors': errors
        }, project_root, team_name)
        display_telemetry_event('lifecycle', coordinator_id, 'failed', {
            'reason': 'validation_failed',
            'errors': errors
        })

        return {
            'team_result': {
                'team_id': team_id,
                'team_name': team_name,
                'status': 'failed',
                'aggregated_result': None,
                'metrics': None,
                'approval_decisions': {'before_execution': None, 'after_completion': None},
                'telemetry_log_path': None,
                'error': f"Team definition validation failed:\n{error_summary}"
            }
        }

    # Log each validation check (verbose telemetry)
    for check_result in load_result['validation_result'].get('checks', []):
        log_telemetry('error', coordinator_id, 'validation_check', {
            'check_name': check_result.get('name', 'unknown'),
            'field': check_result.get('field'),
            'result': check_result.get('result', 'pass'),
            'expected': check_result.get('expected'),
            'actual': check_result.get('actual'),
            'suggestion': check_result.get('suggestion')
        }, project_root, team_name)

    team_def = load_result['team_definition']

    # Step 1.2b: Validate agent definitions against agent-schema.md
    # Ensures all referenced agents have valid frontmatter (name, description, model)
    # Resolves template inheritance (extends: field) and parameter substitution (params)
    agents = team_def.get('agents', [])
    for agent in agents:
        agent_validation = validate_agent_definition(agent, project_root)
        if not agent_validation['valid']:
            load_result['validation_result']['warnings'].extend(agent_validation['warnings'])
            if agent_validation['errors']:
                load_result['validation_result']['valid'] = False
                load_result['validation_result']['errors'].extend(agent_validation['errors'])

    # Step 1.2c: Detect file conflicts between agents
    # Uses files_read/files_write from agent definitions to find:
    # - Implicit dependencies (Agent B reads file Agent A writes)
    # - Write-write conflicts (parallel agents writing same file)
    # Invokes: skills/team-orchestration/file-conflict-detector.md
    conflict_result = detect_file_conflicts(agents, team_def.get('dependencies', []))

    if conflict_result['conflicts']:
        for conflict in conflict_result['conflicts']:
            load_result['validation_result']['errors'].append({
                'field': 'agents',
                'reason': f"File conflict: {conflict['agent_a']} and {conflict['agent_b']} both write to {conflict['file']} in parallel phase {conflict['phase']}",
                'suggestion': f"Add dependency from {conflict['agent_a']} to {conflict['agent_b']} or move to separate phases"
            })

    if conflict_result['implicit_deps']:
        for dep in conflict_result['implicit_deps']:
            load_result['validation_result']['warnings'].append(
                f"Implicit dependency detected: {dep['reader']} reads {dep['file']} written by {dep['writer']}. Consider adding explicit dependency."
            )

    # Step 1.3: Display warnings (if any)
    warnings = load_result['validation_result'].get('warnings', [])
    if warnings:
        for warning in warnings:
            display_warning(f"Team definition warning: {warning}")

    # Step 1.4: Apply CLI overrides to team definition
    team_def = apply_config_overrides(team_def, config_overrides)

    # Step 1.5: Log successful load
    log_telemetry('coordination', coordinator_id, 'team_loaded', {
        'team_name': team_def['name'],
        'max_agents': team_def['max_agents'],
        'timeout_minutes': team_def['timeout_minutes'],
        'failure_handling': team_def['failure_handling'],
        'approval_gates': team_def['approval_gates'],
        'agent_count': len(team_def.get('agents', []))
    }, project_root, team_name)

    # Log full config snapshot (verbose telemetry)
    log_telemetry('config', coordinator_id, 'config_loaded', {
        'team_name': team_def['name'],
        'file_path': f"teams/{team_name}.md",
        'frontmatter_raw': team_def,  # Full team definition
        'file_size_bytes': None,  # Set by loader
        'parse_duration_ms': None  # Set by loader
    }, project_root, team_name)
    display_telemetry_event('config', coordinator_id, 'config_loaded', {
        'team_name': team_def['name'],
        'file_path': f"teams/{team_name}.md",
        'frontmatter_raw': team_def,
        'file_size_bytes': None,
        'parse_duration_ms': None
    })
```

    # Log each override applied (verbose telemetry)
    if config_overrides:
        for field, value in config_overrides.items():
            if value is not None:
                log_telemetry('config', coordinator_id, 'config_override_applied', {
                    'field': field,
                    'original_value': str(original_team_def.get(field)),
                    'override_value': str(value),
                    'source': 'cli',
                    'override_key': f"--{field.replace('_', '-')}"
                }, project_root, team_name)
```

#### apply_config_overrides()

```python
def apply_config_overrides(team_def: dict, overrides: dict) -> dict:
    """
    Apply CLI configuration overrides to team definition.

    CLI overrides take highest precedence per the configuration
    precedence order defined in the plan:
    1. CLI Arguments (highest)
    2. Environment Variables
    3. JSON Configuration
    4. Team Definition Frontmatter
    5. Default Values (lowest)

    Args:
        team_def: Loaded team definition with defaults applied
        overrides: CLI overrides from /team-run command

    Returns:
        Team definition with overrides applied
    """
    if not overrides:
        return team_def

    if overrides.get('max_agents') is not None:
        team_def['max_agents'] = min(overrides['max_agents'], 25)  # Enforce hard limit

    if overrides.get('timeout_minutes') is not None:
        team_def['timeout_minutes'] = max(overrides['timeout_minutes'], 1)  # Min 1 minute

    if overrides.get('approval_gates') is not None:
        gate_value = overrides['approval_gates']
        if gate_value == 'disabled':
            team_def['approval_gates'] = {'before_execution': False, 'after_completion': False, 'disabled': True}
        elif gate_value == 'before':
            team_def['approval_gates'] = {'before_execution': True, 'after_completion': False, 'disabled': False}
        elif gate_value == 'after':
            team_def['approval_gates'] = {'before_execution': False, 'after_completion': True, 'disabled': False}

    if overrides.get('telemetry_enabled') is not None:
        team_def['telemetry_enabled'] = overrides['telemetry_enabled']

    return team_def
```

---

### Phase 2: Register Team with Resource Manager

```python
    # =========================================================================
    # PHASE 2: Register team with resource manager
    # Invokes: skills/team-orchestration/resource-manager.md
    # =========================================================================

    # Step 2.1: Attempt to register this team execution
    team_spec = {
        'team_id': team_id,
        'team_name': team_name,
        'coordinator': team_def['coordinator'],
        'timeout_minutes': team_def['timeout_minutes']
    }

    spawn_team_result = resource_manager.spawn_team(team_spec)
    # spawn_team() checks the global team limit (max 5 concurrent teams).
    # If under limit, registers team and starts timeout tracking.
    # If at limit, queues team in FIFO order and returns queued=True.

    if spawn_team_result['queued']:
        # Team is queued - wait for slot to open
        log_telemetry('resource', coordinator_id, 'team_queued', {
            'queue_position': spawn_team_result['queue_position'],
            'queue_depth': spawn_team_result['queue_depth']
        }, project_root, team_name)

        display_info(
            f"Team '{team_name}' queued at position {spawn_team_result['queue_position']}. "
            f"Waiting for a concurrent team slot (max {resource_manager.max_concurrent_teams})..."
        )

        # Wait for team to be dequeued (blocking wait)
        # In practice, the /team-run command handles this wait
        wait_for_team_slot(team_id)

    # Team is now active
    log_telemetry('resource', coordinator_id, 'team_active', {
        'team_id': team_id,
        'timeout_minutes': team_def['timeout_minutes']
    }, project_root, team_name)
```

---

### Phase 3: Build Execution Plan and Request Approval

```python
    # =========================================================================
    # PHASE 3: Build execution plan and request before_execution approval
    # Invokes: skills/team-orchestration/approval-gate-handler.md
    # =========================================================================

    # Step 3.1: Read coordinator logic to build execution plan
    # The coordinator file (e.g., teams/testing-parallel-coordinator.md)
    # defines the agent composition and dependency structure.
    # The orchestrator reads this and builds an execution plan.
    coordinator_path = team_def['coordinator']
    agents = team_def.get('agents', [])
    dependencies = team_def.get('dependencies', [])

    # Step 3.2: Resolve dependency graph into execution phases
    # Agents with no dependencies can run in parallel (same phase).
    # Agents with dependencies must wait for their dependencies to complete.
    execution_plan = build_execution_plan(agents, dependencies, team_def, context)

    # Log dependency graph construction (verbose telemetry)
    log_telemetry('dependency', coordinator_id, 'graph_constructed', {
        'adjacency_list': dep_graph,
        'topological_order': [name for phase in execution_plan['phases'] for name in phase['agent_names']],
        'total_nodes': execution_plan['total_agents'],
        'total_edges': sum(len(deps) for deps in dep_graph.values()),
        'has_cycles': False  # Would have been caught by validation
    }, project_root, team_name)
    display_telemetry_event('dependency', coordinator_id, 'graph_constructed', {
        'adjacency_list': dep_graph,
        'topological_order': [name for phase in execution_plan['phases'] for name in phase['agent_names']],
        'total_nodes': execution_plan['total_agents'],
        'total_edges': sum(len(deps) for deps in dep_graph.values()),
        'has_cycles': False
    })

    # Log each planned phase (verbose telemetry)
    for phase in execution_plan['phases']:
        log_telemetry('dependency', coordinator_id, 'phase_planned', {
            'phase_number': phase['phase_number'],
            'agents': phase['agent_names'],
            'parallel': phase['parallel'],
            'blocked_by': [],  # First phase has no blockers
            'estimated_duration_seconds': None
        }, project_root, team_name)

    # Step 3.3: Log plan proposal
    log_telemetry('coordination', coordinator_id, 'plan_proposed', {
        'total_agents': execution_plan['total_agents'],
        'parallel_phases': len(execution_plan['phases']),
        'max_concurrent': team_def['max_agents'],
        'estimated_time_minutes': execution_plan.get('estimated_time_minutes'),
        'approval_required': not team_def['approval_gates'].get('disabled', False)
    }, project_root, team_name)
    display_telemetry_event('coordination', coordinator_id, 'plan_proposed', {
        'total_agents': execution_plan['total_agents'],
        'parallel_phases': len(execution_plan['phases']),
        'max_concurrent': team_def['max_agents'],
        'estimated_time_minutes': execution_plan.get('estimated_time_minutes'),
        'approval_required': not team_def['approval_gates'].get('disabled', False)
    })

    # Log phase transition timing (verbose telemetry)
    phase_1_to_3_duration = elapsed_since(team_start_time)
    log_telemetry('timing', coordinator_id, 'phase_transition', {
        'from_phase': 1,
        'to_phase': 3,
        'transition_duration_seconds': phase_1_to_3_duration,
        'idle_time_seconds': 0,
        'overhead_description': 'Team loading, validation, and plan construction'
    }, project_root, team_name)
    display_telemetry_event('timing', coordinator_id, 'phase_transition', {
        'from_phase': 1,
        'to_phase': 3,
        'transition_duration_seconds': phase_1_to_3_duration,
        'idle_time_seconds': 0,
        'overhead_description': 'Team loading, validation, and plan construction'
    })

    # Step 3.4: Request before_execution approval
    iteration = 0
    approval_result = request_before_execution_approval(
        coordinator_id=coordinator_id,
        team_config=team_def,
        plan=execution_plan,
        iteration=iteration
    )
    # request_before_execution_approval() is defined in approval-gate-handler.md.
    # It checks if the before_execution gate is enabled. If disabled, returns
    # auto-approve. If enabled, presents plan to user and collects decision.

    # Log approval gate interaction (verbose telemetry)
    log_telemetry('approval', coordinator_id, 'gate_entered', {
        'gate_type': 'before_execution',
        'iteration': iteration,
        'max_iterations': 3,
        'gates_config': team_def['approval_gates'],
        'context_summary': f"{execution_plan['total_agents']} agents in {len(execution_plan['phases'])} phases"
    }, project_root, team_name)

    log_telemetry('approval', coordinator_id, 'user_response_received', {
        'gate_type': 'before_execution',
        'decision': approval_result['decision'],
        'feedback_text': approval_result.get('feedback'),
        'response_time_seconds': None,  # Measured by gate handler
        'iteration': approval_result.get('iteration', 0)
    }, project_root, team_name)
    display_telemetry_event('approval', coordinator_id, 'user_response_received', {
        'gate_type': 'before_execution',
        'decision': approval_result['decision'],
        'feedback_text': approval_result.get('feedback'),
        'response_time_seconds': None,
        'iteration': approval_result.get('iteration', 0)
    })

    # Step 3.5: Handle modification loop
    while approval_result['decision'] == 'modify':
        feedback = approval_result['feedback']
        iteration = approval_result['iteration']

        log_telemetry('coordination', coordinator_id, 'plan_modification_requested', {
            'iteration': iteration,
            'feedback': feedback
        }, project_root, team_name)

        # Regenerate plan incorporating user feedback
        execution_plan = regenerate_plan_with_feedback(execution_plan, feedback, team_def, context)

        # Log updated plan proposal
        log_telemetry('coordination', coordinator_id, 'plan_proposed', {
            'total_agents': execution_plan['total_agents'],
            'parallel_phases': len(execution_plan['phases']),
            'iteration': iteration
        }, project_root, team_name)

        # Request approval again
        approval_result = request_before_execution_approval(
            coordinator_id=coordinator_id,
            team_config=team_def,
            plan=execution_plan,
            iteration=iteration
        )

    # Step 3.6: Handle rejection
    if approval_result['decision'] == 'reject':
        log_telemetry('lifecycle', coordinator_id, 'failed', {
            'reason': 'user_rejected_plan'
        }, project_root, team_name)
        display_telemetry_event('lifecycle', coordinator_id, 'failed', {
            'reason': 'user_rejected_plan'
        })

        # Clean up team registration
        resource_manager.on_team_complete(team_id)

        return {
            'team_result': {
                'team_id': team_id,
                'team_name': team_name,
                'status': 'aborted',
                'aggregated_result': None,
                'metrics': {'total_duration_seconds': elapsed_since(team_start_time)},
                'approval_decisions': {'before_execution': 'reject', 'after_completion': None},
                'telemetry_log_path': telemetry_log_path,
                'error': 'Team execution cancelled by user at before_execution gate.'
            }
        }

    # Plan approved - continue to execution
    before_execution_decision = approval_result.get('decision', 'approve')

    log_telemetry('coordination', coordinator_id, 'plan_approved', {
        'iteration': approval_result.get('iteration', 0),
        'bypassed': approval_result.get('bypassed', False)
    }, project_root, team_name)
```

#### build_execution_plan()

```python
def build_execution_plan(agents: list, dependencies: list, team_def: dict, context: dict) -> dict:
    """
    Build an execution plan from agent composition and dependencies.

    Resolves the dependency graph into sequential phases where
    agents within each phase can execute in parallel.

    Args:
        agents: List of agent specs from team definition
        dependencies: Explicit dependency list from team definition
        team_def: Full team definition
        context: Execution context (target_path, etc.)

    Returns:
        Execution plan with phases, agent assignments, and estimates
    """
    # Build dependency graph
    dep_graph = {}  # {agent_name: [dependency_agent_names]}
    agent_map = {}  # {agent_name: agent_spec}

    for agent in agents:
        name = agent['name']
        agent_map[name] = agent
        dep_graph[name] = agent.get('dependencies', [])

    # Also incorporate explicit dependencies
    for dep in dependencies:
        from_agent = dep['from']
        to_agent = dep['to']
        if to_agent in dep_graph:
            if from_agent not in dep_graph[to_agent]:
                dep_graph[to_agent].append(from_agent)

    # Topological sort into phases (Kahn's algorithm)
    # Phase N contains agents whose dependencies are all in Phase < N
    phases = []
    remaining = set(dep_graph.keys())
    completed = set()

    while remaining:
        # Find agents with all dependencies satisfied
        ready = []
        for agent_name in remaining:
            deps = dep_graph.get(agent_name, [])
            if all(d in completed for d in deps):
                ready.append(agent_name)

        if not ready:
            # Circular dependency (should not happen - caught by team-loader)
            break

        phases.append({
            'phase_number': len(phases) + 1,
            'agents': [agent_map[name] for name in ready],
            'agent_names': ready,
            'parallel': len(ready) > 1
        })

        completed.update(ready)
        remaining -= set(ready)

    # Calculate totals
    total_agents = sum(len(phase['agents']) for phase in phases)

    return {
        'phases': phases,
        'total_agents': total_agents,
        'max_concurrent': team_def['max_agents'],
        'target_path': context.get('target_path'),
        'estimated_time_minutes': None  # Estimated by coordinator logic
    }
```

---

### Phase 4: Execute Agents (Spawn, Monitor, Retry)

```python
    # =========================================================================
    # PHASE 4: Execute agents via Task tool with lifecycle tracking
    # Invokes: resource-manager.md, agent-lifecycle-manager.md, telemetry
    # Implements: Coordinator-specialist pattern (REQ-F-1)
    #             Retry logic with exponential backoff (REQ-F-5)
    #             Failure handling: continue or abort (REQ-F-6)
    # =========================================================================

    all_agent_outputs = []   # Collect outputs from all agents
    total_retry_count = 0    # Track total retries across all agents
    aborted = False          # Flag for abort on critical failure

    # Step 4.1: Execute each phase sequentially
    # Within each phase, agents execute in parallel (up to max_agents limit)
    for phase in execution_plan['phases']:
        if aborted:
            break

        phase_number = phase['phase_number']
        phase_agents = phase['agents']

        log_telemetry('coordination', coordinator_id, 'phase_start', {
            'phase': phase_number,
            'agent_count': len(phase_agents),
            'parallel': phase['parallel'],
            'agent_names': phase['agent_names']
        }, project_root, team_name)

        # Step 4.2: Spawn all agents in this phase
        spawned_agents = {}   # {agent_id: agent_spec}
        pending_queue = []    # Agents that were queued (not spawned immediately)

        for agent_spec in phase_agents:
            # Handle agents with max_instances > 1
            instances = agent_spec.get('max_instances', 1)

            for instance_idx in range(instances):
                # Check timeout before spawning
                timeout_status = resource_manager.enforce_timeout(team_id)
                if timeout_status['timeout_status']['timed_out']:
                    aborted = True
                    break

                # Spawn agent via resource manager
                spawn_result = resource_manager.spawn_agent(
                    team_id=team_id,
                    agent_spec={
                        'agent_type': agent_spec['type'],
                        'task_description': f"{agent_spec['name']} (instance {instance_idx + 1})",
                        'max_retries': team_def['retry_config']['max_retries'],
                        'retry_count': 0
                    },
                    parent_id=coordinator_id,
                    depth=depth + 1,
                    max_agents=team_def['max_agents']
                )
                # spawn_agent() in resource-manager.md enforces:
                # - Depth limit (max 3, REQ-F-4)
                # - Agent count limit (max_agents per team, REQ-F-7)
                # - FIFO queuing when limit reached (REQ-F-10)

                if spawn_result.get('error'):
                    # Depth limit exceeded or other error
                    log_telemetry('resource', coordinator_id, 'spawn_error', {
                        'agent_type': agent_spec['type'],
                        'error': spawn_result['error']
                    }, project_root, team_name)

                    if agent_spec.get('critical', False):
                        aborted = True
                        break
                    continue

                if spawn_result['queued']:
                    # Agent queued - track for later
                    pending_queue.append({
                        'agent_spec': agent_spec,
                        'instance_idx': instance_idx,
                        'queue_position': spawn_result['queue_position']
                    })
                    continue

                agent_id = spawn_result['agent_id']

                # Register with lifecycle manager
                lifecycle_result = lifecycle_manager.spawn_agent(
                    agent_spec={
                        'agent_type': agent_spec['type'],
                        'task_description': f"{agent_spec['name']}",
                        'max_retries': team_def['retry_config']['max_retries']
                    },
                    parent_id=coordinator_id,
                    team_id=team_id,
                    depth=depth + 1,
                    retry_count=0
                )
                # spawn_agent() in agent-lifecycle-manager.md creates the
                # agent state entry with status "spawned" and logs the
                # lifecycle event to telemetry.

                spawned_agents[agent_id] = {
                    'agent_spec': agent_spec,
                    'instance_idx': instance_idx,
                    'lifecycle_id': lifecycle_result['agent_id']
                }

            if aborted:
                break

        if aborted:
            # Handle timeout or critical failure - skip to finalization
            log_telemetry('coordination', coordinator_id, 'execution_aborted', {
                'phase': phase_number,
                'reason': 'timeout_or_critical_failure'
            }, project_root, team_name)
            break

        # Step 4.3: Execute spawned agents via Task tool (parallel)
        # Each agent is spawned as a subagent using the Task tool.
        # The coordinator monitors their progress.
        active_tasks = {}  # {agent_id: task_handle}

        for agent_id, agent_info in spawned_agents.items():
            agent_spec = agent_info['agent_spec']

            # Mark agent as running in lifecycle manager
            lifecycle_manager.mark_running(
                agent_id=agent_info['lifecycle_id'],
                task_description=f"Executing {agent_spec['name']} for {context.get('target_path', 'project')}"
            )

            # Log full agent prompt (verbose telemetry)
            agent_prompt = build_agent_prompt(agent_spec, team_def, context)
            log_telemetry('agent_io', agent_id, 'prompt_constructed', {
                'agent_id': agent_id,
                'prompt_text': agent_prompt,
                'prompt_length_chars': len(agent_prompt),
                'prompt_estimated_tokens': len(agent_prompt) // 4,  # Rough estimate
                'model': team_def.get('model', 'sonnet'),
                'includes_context': bool(context.get('target_path'))
            }, project_root, team_name)
            display_telemetry_event('agent_io', agent_id, 'prompt_constructed', {
                'agent_id': agent_id,
                'prompt_text': agent_prompt,
                'prompt_length_chars': len(agent_prompt),
                'prompt_estimated_tokens': len(agent_prompt) // 4,
                'model': team_def.get('model', 'sonnet'),
                'includes_context': bool(context.get('target_path'))
            })

            # Spawn agent via Claude Code Agent tool (coordinator-specialist pattern, REQ-F-1)
            # The Agent tool creates an independent subagent that executes
            # the agent's instructions from its agent definition file.
            #
            # AGENT TOOL INTEGRATION SPECIFICATION:
            # - Use Claude Code's `Agent` tool (NOT a custom "Task" tool)
            # - Set `subagent_type` from agent definition frontmatter
            #   (defaults to "general-purpose" if not specified)
            # - Set `run_in_background: true` for parallel agents within a phase
            # - Set `run_in_background: false` for the sole agent in sequential phases
            # - Set `model` from model-selection skill resolution
            # - Prompt includes: agent definition body + phase context + dependency outputs
            #
            # For parallel agents:
            #   Agent(description=..., prompt=agent_prompt, subagent_type=...,
            #         model=resolved_model, run_in_background=True)
            #   -> Returns agent_id; completion notified automatically
            #   -> Read output file when notified
            #
            # For sequential agents:
            #   Agent(description=..., prompt=agent_prompt, subagent_type=...,
            #         model=resolved_model)
            #   -> Blocks until complete; result returned directly
            #
            # MODEL RESOLUTION:
            #   resolved = model_resolver.resolve_model(agent_spec['name'], cli_overrides)
            #   model = resolved['model']  # opus, sonnet, or haiku
            #   timeout = resolved['timeout']  # 180s, 120s, or 60s
            #
            resolved_model = resolve_model(agent_spec['name'], config_overrides)
            is_parallel = phase['parallel'] and len(phase_agents) > 1

            task_handle = Agent({
                'description': f"Running {agent_spec['name']} for team {team_name}",
                'prompt': agent_prompt,
                'subagent_type': agent_spec.get('subagent_type', 'general-purpose'),
                'model': resolved_model['model'],
                'run_in_background': is_parallel
            })

            active_tasks[agent_id] = {
                'task_handle': task_handle,
                'agent_info': agent_info,
                'start_time': current_timestamp_utc()
            }

        # Step 4.4: Monitor agents and collect results
        phase_outputs = monitor_and_collect_results(
            active_tasks=active_tasks,
            team_id=team_id,
            team_def=team_def,
            coordinator_id=coordinator_id,
            project_root=project_root,
            team_name=team_name,
            depth=depth
        )

        all_agent_outputs.extend(phase_outputs['outputs'])
        total_retry_count += phase_outputs['retry_count']

        if phase_outputs.get('aborted', False):
            aborted = True
            break

        # Step 4.5: Handle dequeued agents (spawned from queue after slots freed)
        # As agents complete, the resource manager automatically dequeues
        # waiting agents. These need to be spawned and monitored.
        # (Handled inside monitor_and_collect_results)

        # Save phase checkpoint for recovery (P1 - Execution Recovery)
        # Checkpoint state saved to .claude/teamsters-state/<team-id>.json
        # Enables --resume to continue from last completed phase
        save_execution_checkpoint(project_root, team_id, {
            'team_name': team_name,
            'completed_phase': phase_number,
            'total_phases': len(execution_plan['phases']),
            'completed_agents': [o['agent_id'] for o in all_agent_outputs if o['status'] == 'completed'],
            'failed_agents': [o['agent_id'] for o in all_agent_outputs if o['status'] == 'failed'],
            'partial_outputs': all_agent_outputs,
            'elapsed_seconds': elapsed_since(team_start_time),
            'checkpoint_time': current_timestamp_utc()
        })

        log_telemetry('coordination', coordinator_id, 'phase_complete', {
            'phase': phase_number,
            'successful': phase_outputs['successful_count'],
            'failed': phase_outputs['failed_count']
        }, project_root, team_name)

        # Log phase transition (verbose telemetry)
        log_telemetry('timing', coordinator_id, 'phase_transition', {
            'from_phase': phase_number,
            'to_phase': phase_number + 1,
            'transition_duration_seconds': phase_transition_time,
            'idle_time_seconds': idle_time,
            'overhead_description': f'Phase {phase_number} cleanup and Phase {phase_number + 1} setup'
        }, project_root, team_name)
        display_telemetry_event('timing', coordinator_id, 'phase_transition', {
            'from_phase': phase_number,
            'to_phase': phase_number + 1,
            'transition_duration_seconds': phase_transition_time,
            'idle_time_seconds': idle_time,
            'overhead_description': f'Phase {phase_number} cleanup and Phase {phase_number + 1} setup'
        })

        # Log data flow between phases (verbose telemetry)
        if phase_outputs['outputs']:
            log_telemetry('data_flow', coordinator_id, 'data_passed', {
                'from_agent': f'phase-{phase_number}-agents',
                'to_agent': f'phase-{phase_number + 1}-agents',
                'from_phase': phase_number,
                'to_phase': phase_number + 1,
                'data_type': 'agent_outputs',
                'data_size_chars': sum(len(str(o.get('output', ''))) for o in phase_outputs['outputs']),
                'data_summary': f"{len(phase_outputs['outputs'])} agent outputs",
                'fields_passed': list(set(k for o in phase_outputs['outputs'] for k in (o.get('output', {}) or {}).keys()))
            }, project_root, team_name)
            display_telemetry_event('data_flow', coordinator_id, 'data_passed', {
                'from_agent': f'phase-{phase_number}-agents',
                'to_agent': f'phase-{phase_number + 1}-agents',
                'from_phase': phase_number,
                'to_phase': phase_number + 1,
                'data_type': 'agent_outputs',
                'data_size_chars': sum(len(str(o.get('output', ''))) for o in phase_outputs['outputs']),
                'data_summary': f"{len(phase_outputs['outputs'])} agent outputs",
                'fields_passed': list(set(k for o in phase_outputs['outputs'] for k in (o.get('output', {}) or {}).keys()))
            })
```

#### monitor_and_collect_results()

```python
def monitor_and_collect_results(
    active_tasks: dict,
    team_id: str,
    team_def: dict,
    coordinator_id: str,
    project_root: str,
    team_name: str,
    depth: int
) -> dict:
    """
    Monitor active agents, handle retries on failure, and collect results.

    Implements:
    - Retry logic with exponential backoff [1, 2, 4] seconds (REQ-F-5)
    - Failure handling: "continue" or "abort" (REQ-F-6)
    - Automatic dequeue from resource manager when agents complete
    - Timeout enforcement via periodic checks

    Args:
        active_tasks: Dict of {agent_id: {task_handle, agent_info, start_time}}
        team_id: Team execution ID
        team_def: Team definition with retry_config and failure_handling
        coordinator_id: Coordinator ID for telemetry
        project_root: Project root path
        team_name: Team name for telemetry
        depth: Current nesting depth

    Returns:
        dict with outputs (list), retry_count (int), successful_count, failed_count, aborted (bool)
    """
    outputs = []
    retry_count = 0
    successful_count = 0
    failed_count = 0
    aborted = False

    retry_config = team_def.get('retry_config', {'max_retries': 3, 'backoff_seconds': [1, 2, 4]})
    failure_handling = team_def.get('failure_handling', 'continue')
    max_retries = retry_config.get('max_retries', 3)
    backoff_seconds = retry_config.get('backoff_seconds', [1, 2, 4])

    # Track agents pending completion
    pending = dict(active_tasks)

    while pending and not aborted:
        # Check timeout periodically
        timeout_status = resource_manager.enforce_timeout(team_id)
        if timeout_status['timeout_status']['timed_out']:
            # Timeout reached - mark all active agents as failed
            for agent_id, task_info in pending.items():
                lifecycle_id = task_info['agent_info']['lifecycle_id']
                lifecycle_manager.mark_failed(
                    agent_id=lifecycle_id,
                    reason='timeout',
                    last_error=f"Team timed out after {team_def['timeout_minutes']} minutes"
                )

                outputs.append({
                    'agent_id': lifecycle_id,
                    'agent_type': task_info['agent_info']['agent_spec']['type'],
                    'status': 'failed',
                    'output': None,
                    'metadata': {
                        'duration_seconds': elapsed_since(task_info['start_time']),
                        'retry_count': 0
                    },
                    'failure_reason': 'Team execution timed out'
                })
                failed_count += 1

            aborted = True
            break

        # Check each pending agent
        completed_agents = []

        for agent_id, task_info in pending.items():
            task_handle = task_info['task_handle']
            agent_info = task_info['agent_info']
            agent_spec = agent_info['agent_spec']
            lifecycle_id = agent_info['lifecycle_id']

            # Check if task completed
            if not is_task_complete(task_handle):
                continue

            # Task completed - check result
            task_result = get_task_result(task_handle)

            if task_result['success']:
                # Log full agent output (verbose telemetry)
                log_telemetry('agent_io', agent_id, 'output_received', {
                    'agent_id': agent_id,
                    'output_text': str(task_result.get('output', '')),
                    'output_length_chars': len(str(task_result.get('output', ''))),
                    'output_estimated_tokens': len(str(task_result.get('output', ''))) // 4,
                    'duration_seconds': elapsed_since(task_info['start_time'])
                }, project_root, team_name)
                display_telemetry_event('agent_io', agent_id, 'output_received', {
                    'agent_id': agent_id,
                    'output_text': str(task_result.get('output', '')),
                    'output_length_chars': len(str(task_result.get('output', ''))),
                    'output_estimated_tokens': len(str(task_result.get('output', ''))) // 4,
                    'duration_seconds': elapsed_since(task_info['start_time'])
                })

                # Agent completed successfully
                lifecycle_manager.mark_completed(
                    agent_id=lifecycle_id,
                    output=task_result['output'],
                    output_summary=task_result.get('summary', 'Completed')
                )

                outputs.append({
                    'agent_id': lifecycle_id,
                    'agent_type': agent_spec['type'],
                    'status': 'completed',
                    'output': task_result['output'],
                    'metadata': {
                        'duration_seconds': elapsed_since(task_info['start_time']),
                        'model_used': task_result.get('model', 'unknown'),
                        'spawned_at': task_info['start_time'],
                        'completed_at': current_timestamp_utc(),
                        'retry_count': agent_info.get('retry_count', 0)
                    },
                    'failure_reason': None
                })

                successful_count += 1
                completed_agents.append(agent_id)

                # Log state transition (verbose telemetry)
                log_telemetry('error', coordinator_id, 'state_transition', {
                    'agent_id': lifecycle_id,
                    'from_state': 'running',
                    'to_state': 'completed' if task_result['success'] else 'failed',
                    'trigger': 'task_complete' if task_result['success'] else task_result.get('error_type', 'unknown'),
                    'before_snapshot': {'status': 'running', 'retry_count': agent_info.get('retry_count', 0)},
                    'after_snapshot': copy.deepcopy(state),
                    'transition_valid': True
                }, project_root, team_name)

                # Log cumulative cost (verbose telemetry)
                log_telemetry('cost', coordinator_id, 'cumulative_cost', {
                    'team_id': team_id,
                    'total_input_tokens': cumulative_input_tokens,
                    'total_output_tokens': cumulative_output_tokens,
                    'total_cache_read_tokens': cumulative_cache_read,
                    'total_cache_write_tokens': cumulative_cache_write,
                    'estimated_cost_usd': estimate_cost(cumulative_input_tokens, cumulative_output_tokens),
                    'cost_by_model': cost_by_model,
                    'cost_by_agent': cost_by_agent,
                    'agents_completed': successful_count + failed_count,
                    'agents_remaining': len(pending)
                }, project_root, team_name)
                display_telemetry_event('cost', coordinator_id, 'cumulative_cost', {
                    'team_id': team_id,
                    'total_input_tokens': cumulative_input_tokens,
                    'total_output_tokens': cumulative_output_tokens,
                    'total_cache_read_tokens': cumulative_cache_read,
                    'total_cache_write_tokens': cumulative_cache_write,
                    'estimated_cost_usd': estimate_cost(cumulative_input_tokens, cumulative_output_tokens),
                    'cost_by_model': cost_by_model,
                    'cost_by_agent': cost_by_agent,
                    'agents_completed': successful_count + failed_count,
                    'agents_remaining': len(pending)
                })

                # Log memory snapshot (verbose telemetry)
                log_telemetry('cost', agent_id, 'memory_snapshot', {
                    'agent_id': agent_id,
                    'snapshot_point': 'completion',
                    'context_used_tokens': task_result.get('total_tokens', 0),
                    'context_max_tokens': 200000,
                    'utilization_percent': (task_result.get('total_tokens', 0) / 200000) * 100,
                    'cache_hit_rate': None
                }, project_root, team_name)

                # Notify resource manager (may trigger dequeue)
                dequeue_result = resource_manager.on_agent_complete(team_id, agent_id)

                # If a queued agent was dequeued, spawn it
                if dequeue_result['dequeued_agent']['agent_id']:
                    handle_dequeued_agent(
                        dequeue_result, pending, team_id, team_def,
                        coordinator_id, project_root, team_name, depth
                    )

            else:
                # Agent failed - attempt retry
                fail_result = lifecycle_manager.mark_failed(
                    agent_id=lifecycle_id,
                    reason=task_result.get('error_type', 'unknown'),
                    last_error=task_result.get('error_message', 'Agent execution failed')
                )

                current_retry = agent_info.get('retry_count', 0)

                # Log retry decision (verbose telemetry)
                log_telemetry('error', coordinator_id, 'retry_decision', {
                    'agent_id': lifecycle_id,
                    'should_retry': fail_result['should_retry'] and current_retry < max_retries,
                    'retry_count': current_retry,
                    'max_retries': max_retries,
                    'failure_reason': task_result.get('error_type', 'unknown'),
                    'backoff_chosen_seconds': backoff_seconds[min(current_retry, len(backoff_seconds) - 1)] if fail_result['should_retry'] else None,
                    'failure_handling_strategy': failure_handling,
                    'is_critical_agent': agent_spec.get('critical', False)
                }, project_root, team_name)

                # Log error classification (verbose telemetry)
                error_category = classify_error(task_result.get('error_type', 'unknown'))
                log_telemetry('error', coordinator_id, 'error_classified', {
                    'agent_id': lifecycle_id,
                    'error_category': error_category,
                    'raw_error': task_result.get('error_message', ''),
                    'classified_severity': 'retriable' if fail_result['should_retry'] else 'fatal',
                    'suggested_action': get_error_suggestion(error_category),
                    'stack_trace': task_result.get('stack_trace')
                }, project_root, team_name)
                display_telemetry_event('error', coordinator_id, 'error_classified', {
                    'agent_id': lifecycle_id,
                    'error_category': error_category,
                    'raw_error': task_result.get('error_message', ''),
                    'classified_severity': 'retriable' if fail_result['should_retry'] else 'fatal',
                    'suggested_action': get_error_suggestion(error_category),
                    'stack_trace': task_result.get('stack_trace')
                })

                # Log state transition (verbose telemetry)
                log_telemetry('error', coordinator_id, 'state_transition', {
                    'agent_id': lifecycle_id,
                    'from_state': 'running',
                    'to_state': 'completed' if task_result['success'] else 'failed',
                    'trigger': 'task_complete' if task_result['success'] else task_result.get('error_type', 'unknown'),
                    'before_snapshot': {'status': 'running', 'retry_count': agent_info.get('retry_count', 0)},
                    'after_snapshot': copy.deepcopy(state),
                    'transition_valid': True
                }, project_root, team_name)

                if fail_result['should_retry'] and current_retry < max_retries:
                    # =========================================================
                    # RETRY LOGIC (REQ-F-5)
                    # Max 3 retries with exponential backoff [1, 2, 4] seconds
                    # =========================================================
                    backoff_index = min(current_retry, len(backoff_seconds) - 1)
                    wait_seconds = backoff_seconds[backoff_index]

                    log_telemetry('lifecycle', lifecycle_id, 'retry_scheduled', {
                        'retry_count': current_retry + 1,
                        'max_retries': max_retries,
                        'backoff_seconds': wait_seconds,
                        'reason': task_result.get('error_type', 'unknown')
                    }, project_root, team_name)

                    # Log backoff wait (verbose telemetry)
                    log_telemetry('timing', coordinator_id, 'backoff_wait', {
                        'agent_id': lifecycle_id,
                        'retry_attempt': current_retry + 1,
                        'backoff_seconds': wait_seconds,
                        'backoff_start': current_timestamp_utc(),
                        'backoff_end': None,  # Set after sleep
                        'reason': task_result.get('error_type', 'unknown')
                    }, project_root, team_name)

                    # Wait for backoff delay
                    sleep(wait_seconds)

                    # Spawn retry agent
                    retry_spawn = resource_manager.spawn_agent(
                        team_id=team_id,
                        agent_spec={
                            'agent_type': agent_spec['type'],
                            'task_description': f"{agent_spec['name']} (retry {current_retry + 1})",
                            'max_retries': max_retries,
                            'retry_count': current_retry + 1
                        },
                        parent_id=coordinator_id,
                        depth=depth + 1,
                        max_agents=team_def['max_agents']
                    )

                    if retry_spawn.get('agent_id'):
                        # Register retry with lifecycle manager
                        retry_lifecycle = lifecycle_manager.spawn_agent(
                            agent_spec={
                                'agent_type': agent_spec['type'],
                                'task_description': f"{agent_spec['name']} (retry {current_retry + 1})",
                                'max_retries': max_retries
                            },
                            parent_id=coordinator_id,
                            team_id=team_id,
                            depth=depth + 1,
                            retry_count=current_retry + 1
                        )

                        # Mark as running
                        lifecycle_manager.mark_running(
                            agent_id=retry_lifecycle['agent_id'],
                            task_description=f"Retry {current_retry + 1} of {agent_spec['name']}"
                        )

                        # Spawn retry via Task tool
                        retry_task = Task({
                            'description': f"Retry {current_retry + 1} of {agent_spec['name']}",
                            'prompt': build_agent_prompt(agent_spec, team_def, context),
                        })

                        # Replace in pending
                        pending[retry_spawn['agent_id']] = {
                            'task_handle': retry_task,
                            'agent_info': {
                                'agent_spec': agent_spec,
                                'instance_idx': agent_info['instance_idx'],
                                'lifecycle_id': retry_lifecycle['agent_id'],
                                'retry_count': current_retry + 1
                            },
                            'start_time': current_timestamp_utc()
                        }

                        retry_count += 1

                    completed_agents.append(agent_id)

                else:
                    # =========================================================
                    # FAILURE HANDLING (REQ-F-6)
                    # "continue": Log error and proceed with remaining agents
                    # "abort": Stop all agents and abort team execution
                    # =========================================================
                    outputs.append({
                        'agent_id': lifecycle_id,
                        'agent_type': agent_spec['type'],
                        'status': 'failed',
                        'output': None,
                        'metadata': {
                            'duration_seconds': elapsed_since(task_info['start_time']),
                            'retry_count': current_retry
                        },
                        'failure_reason': task_result.get('error_message', 'Agent failed after max retries')
                    })

                    failed_count += 1
                    completed_agents.append(agent_id)

                    # Notify resource manager
                    dequeue_result = resource_manager.on_agent_complete(team_id, agent_id)
                    if dequeue_result['dequeued_agent']['agent_id']:
                        handle_dequeued_agent(
                            dequeue_result, pending, team_id, team_def,
                            coordinator_id, project_root, team_name, depth
                        )

                    # Check failure handling strategy
                    is_critical = agent_spec.get('critical', False)

                    if failure_handling == 'abort' or is_critical:
                        log_telemetry('coordination', coordinator_id, 'execution_aborted', {
                            'reason': 'agent_failure',
                            'failed_agent': lifecycle_id,
                            'critical': is_critical,
                            'failure_handling': failure_handling
                        }, project_root, team_name)

                        aborted = True
                        break

                    # failure_handling == 'continue': log and proceed
                    log_telemetry('coordination', coordinator_id, 'failure_continued', {
                        'failed_agent': lifecycle_id,
                        'remaining_agents': len(pending) - len(completed_agents),
                        'failure_handling': 'continue'
                    }, project_root, team_name)

        # Remove completed agents from pending
        for agent_id in completed_agents:
            if agent_id in pending:
                del pending[agent_id]

    return {
        'outputs': outputs,
        'retry_count': retry_count,
        'successful_count': successful_count,
        'failed_count': failed_count,
        'aborted': aborted
    }
```

#### handle_dequeued_agent()

```python
def handle_dequeued_agent(
    dequeue_result: dict,
    pending: dict,
    team_id: str,
    team_def: dict,
    coordinator_id: str,
    project_root: str,
    team_name: str,
    depth: int
) -> None:
    """
    Handle an agent that was dequeued from the resource manager FIFO queue.

    When an active agent completes, the resource manager automatically
    dequeues the next waiting agent. This function spawns that agent
    via the Task tool and adds it to the pending set.

    Args:
        dequeue_result: Result from resource_manager.on_agent_complete()
        pending: Dict of currently pending agents (mutated in place)
        team_id: Team execution ID
        team_def: Team definition
        coordinator_id: Coordinator ID
        project_root: Project root path
        team_name: Team name
        depth: Current nesting depth
    """
    dequeued = dequeue_result['dequeued_agent']
    new_agent_id = dequeued['agent_id']
    agent_spec_raw = dequeued['agent_spec']
    queued_spec = agent_spec_raw

                # Log queue wait time (verbose telemetry)
                log_telemetry('timing', coordinator_id, 'queue_wait_time', {
                    'agent_id': new_agent_id,
                    'queue_entry_time': queued_spec.get('queued_at'),
                    'queue_exit_time': current_timestamp_utc(),
                    'wait_duration_seconds': elapsed_since(queued_spec.get('queued_at')),
                    'queue_position_at_entry': queued_spec.get('queue_position', 0),
                    'agents_ahead_at_entry': queued_spec.get('queue_position', 0) - 1
                }, project_root, team_name)

    # Register with lifecycle manager
    lifecycle_result = lifecycle_manager.spawn_agent(
        agent_spec=agent_spec_raw,
        parent_id=dequeued.get('parent_id', coordinator_id),
        team_id=team_id,
        depth=dequeued.get('depth', depth + 1),
        retry_count=agent_spec_raw.get('retry_count', 0)
    )

    lifecycle_manager.mark_running(
        agent_id=lifecycle_result['agent_id'],
        task_description=agent_spec_raw.get('task_description', 'Dequeued agent')
    )

    # Spawn via Task tool
    task_handle = Task({
        'description': f"Running dequeued agent {agent_spec_raw.get('agent_type', 'unknown')}",
        'prompt': build_agent_prompt_from_raw(agent_spec_raw, team_def),
    })

    pending[new_agent_id] = {
        'task_handle': task_handle,
        'agent_info': {
            'agent_spec': {'type': agent_spec_raw['agent_type'], 'name': agent_spec_raw.get('task_description', 'agent')},
            'instance_idx': 0,
            'lifecycle_id': lifecycle_result['agent_id'],
            'retry_count': agent_spec_raw.get('retry_count', 0)
        },
        'start_time': current_timestamp_utc()
    }

    log_telemetry('coordination', coordinator_id, 'dequeued_agent_spawned', {
        'agent_id': new_agent_id,
        'agent_type': agent_spec_raw['agent_type'],
        'queue_status': dequeue_result['queue_status']
    }, project_root, team_name)
```

---

### Phase 5: Aggregate Results

```python
    # =========================================================================
    # PHASE 5: Aggregate results from all agents
    # Invokes: skills/team-orchestration/result-aggregator.md
    # =========================================================================

    team_end_time = current_timestamp_utc()

    # Step 5.1: Aggregate all agent outputs
    aggregated_result = aggregate_results(
        agent_outputs=all_agent_outputs,
        team_type=team_name,
        team_start_time=team_start_time,
        team_end_time=team_end_time,
        aggregation_config=team_def.get('aggregation_config')
    )
    # aggregate_results() is defined in result-aggregator.md.
    # It categorizes outputs (successful/failed), merges file lists,
    # aggregates metrics, collects warnings, builds failure summaries,
    # and calculates execution metrics including parallel speedup.

    # Step 5.2: Determine team status
    if aborted:
        if timeout_status['timeout_status'].get('timed_out', False):
            team_status = 'timed_out'
        else:
            team_status = 'aborted'
    elif aggregated_result['failed'] == 0:
        team_status = 'completed'
    elif aggregated_result['successful'] > 0:
        team_status = 'partial_success'
    else:
        team_status = 'failed'

    # Step 5.3: Log aggregation results
    log_telemetry('coordination', coordinator_id, 'results_aggregated', {
        'team_status': team_status,
        'total_agents': aggregated_result['total_agents'],
        'successful': aggregated_result['successful'],
        'failed': aggregated_result['failed'],
        'success_rate': aggregated_result['summary']['success_rate'],
        'total_duration_seconds': aggregated_result['summary']['total_duration_seconds'],
        'parallel_speedup': aggregated_result['summary'].get('parallel_speedup'),
        'total_retries': total_retry_count
    }, project_root, team_name)
```

---

### Phase 6: Request After Completion Approval

```python
    # =========================================================================
    # PHASE 6: Request after_completion approval
    # Invokes: skills/team-orchestration/approval-gate-handler.md
    # =========================================================================

    # Step 6.1: Present results to user (if gate enabled and not aborted)
    after_completion_decision = 'bypassed'

    if not aborted:
        iteration = 0
        after_result = request_after_completion_approval(
            coordinator_id=coordinator_id,
            team_config=team_def,
            results=aggregated_result,
            iteration=iteration
        )
        # request_after_completion_approval() is defined in approval-gate-handler.md.
        # It checks if the after_completion gate is enabled. If disabled, returns
        # auto-approve. If enabled, presents results to user with options:
        # Accept, Iterate (modify), or Discard (reject).

        # Log approval gate interaction (verbose telemetry)
        log_telemetry('approval', coordinator_id, 'gate_entered', {
            'gate_type': 'after_completion',
            'iteration': iteration,
            'max_iterations': 3,
            'gates_config': team_def['approval_gates'],
            'context_summary': f"{aggregated_result['total_agents']} agents, {aggregated_result['successful']} successful"
        }, project_root, team_name)

        log_telemetry('approval', coordinator_id, 'user_response_received', {
            'gate_type': 'after_completion',
            'decision': after_result['decision'],
            'feedback_text': after_result.get('feedback'),
            'response_time_seconds': None,  # Measured by gate handler
            'iteration': after_result.get('iteration', 0)
        }, project_root, team_name)
        display_telemetry_event('approval', coordinator_id, 'user_response_received', {
            'gate_type': 'after_completion',
            'decision': after_result['decision'],
            'feedback_text': after_result.get('feedback'),
            'response_time_seconds': None,
            'iteration': after_result.get('iteration', 0)
        })

        # Step 6.2: Handle iteration loop for after_completion gate
        while after_result['decision'] == 'modify' and not aborted:
            feedback = after_result['feedback']
            iteration = after_result['iteration']

            log_telemetry('coordination', coordinator_id, 'results_iteration_requested', {
                'iteration': iteration,
                'feedback': feedback
            }, project_root, team_name)

            # Re-execute agents with feedback (optional, depends on team type)
            # For most teams, this would mean re-running the execution phase
            # with adjusted parameters based on user feedback.
            display_info(f"Iteration {iteration}: Re-executing with feedback...")

            # Note: Full re-execution would repeat Phases 4-5.
            # This is a simplified representation; actual implementation
            # depends on the team coordinator's iteration capability.
            break  # Exit loop; team coordinators handle iteration specifics

        after_completion_decision = after_result.get('decision', 'approve')

        if after_result['decision'] == 'reject':
            team_status = 'aborted'

            log_telemetry('coordination', coordinator_id, 'results_rejected', {
                'iteration': after_result.get('iteration', 0)
            }, project_root, team_name)

    else:
        # Aborted - skip after_completion gate
        log_telemetry('coordination', coordinator_id, 'after_completion_skipped', {
            'reason': 'execution_aborted'
        }, project_root, team_name)
```

---

### Phase 7: Finalize and Return Results

```python
    # =========================================================================
    # PHASE 7: Finalize - clean up resources and return TeamResult
    # =========================================================================

    # Step 7.1: Get final team status from lifecycle manager
    final_team_status = lifecycle_manager.get_team_status(team_id)
    # get_team_status() returns aggregate counts:
    # total, spawned, running, completed, failed, success_rate,
    # total_duration_seconds, average_duration_seconds

    # Step 7.2: Log coordinator completion
    log_telemetry('lifecycle', coordinator_id, 'completed' if team_status == 'completed' else team_status, {
        'team_status': team_status,
        'total_duration_seconds': elapsed_since(team_start_time),
        'total_agents': aggregated_result['total_agents'],
        'successful': aggregated_result['successful'],
        'failed': aggregated_result['failed'],
        'total_retries': total_retry_count,
        'success_rate': aggregated_result['summary']['success_rate']
    }, project_root, team_name)
    display_telemetry_event('lifecycle', coordinator_id, 'completed' if team_status == 'completed' else team_status, {
        'team_status': team_status,
        'total_duration_seconds': elapsed_since(team_start_time),
        'total_agents': aggregated_result['total_agents'],
        'successful': aggregated_result['successful'],
        'failed': aggregated_result['failed'],
        'total_retries': total_retry_count,
        'success_rate': aggregated_result['summary']['success_rate']
    })

    # Step 7.3: Log resource cleanup
    log_telemetry('resource', coordinator_id, 'team_finalized', {
        'team_id': team_id,
        'final_status': team_status
    }, project_root, team_name)

    # Step 7.4: Clean up team registration with resource manager
    resource_manager.on_team_complete(team_id)
    # on_team_complete() removes team from active list, cleans up
    # tracking data, and dequeues next team if any are waiting.

    # Step 7.5: Save execution to history (P1 - Persistent Execution History)
    # Append to .claude/teamsters-history.json for --history queries
    save_execution_history(project_root, {
        'team': team_name,
        'execution_id': team_id,
        'timestamp': team_start_time,
        'duration_seconds': elapsed_since(team_start_time),
        'agents': aggregated_result['total_agents'],
        'successful': aggregated_result['successful'],
        'failed': aggregated_result['failed'],
        'success_rate': aggregated_result['summary']['success_rate'],
        'models_used': aggregated_result['summary'].get('models_used', {}),
        'telemetry_log': telemetry_log_path
    })

    # Step 7.6: Clean up execution checkpoint (P1 - Execution Recovery)
    # Remove .claude/teamsters-state/<team-id>.json since execution completed
    cleanup_execution_checkpoint(project_root, team_id)

    # Step 7.7: Log mandatory TEAM_COMPLETE event (P1 - Standardized Telemetry)
    # This MUST be written to ensure logs are never incomplete
    log_telemetry('lifecycle', coordinator_id, 'TEAM_COMPLETE', {
        'team_id': team_id,
        'team_name': team_name,
        'status': team_status,
        'duration_seconds': elapsed_since(team_start_time),
        'agents_total': aggregated_result['total_agents'],
        'agents_successful': aggregated_result['successful'],
        'agents_failed': aggregated_result['failed'],
        'success_rate': aggregated_result['summary']['success_rate']
    }, project_root, team_name)

    # Log overhead summary (verbose telemetry)
    total_agent_work = sum(d for d in aggregated_result['summary']['agent_durations'].values())
    total_wall_clock = elapsed_since(team_start_time)
    total_overhead = total_wall_clock - total_agent_work if total_wall_clock > total_agent_work else 0

    log_telemetry('timing', coordinator_id, 'overhead_summary', {
        'total_wall_clock_seconds': total_wall_clock,
        'total_agent_work_seconds': total_agent_work,
        'total_overhead_seconds': total_overhead,
        'overhead_percent': (total_overhead / total_wall_clock * 100) if total_wall_clock > 0 else 0,
        'queue_wait_total_seconds': 0,  # Accumulated during execution
        'backoff_wait_total_seconds': 0,
        'phase_transition_total_seconds': 0,
        'framework_tax_percent': (total_overhead / total_wall_clock * 100) if total_wall_clock > 0 else 0
    }, project_root, team_name)
    display_telemetry_event('timing', coordinator_id, 'overhead_summary', {
        'total_wall_clock_seconds': total_wall_clock,
        'total_agent_work_seconds': total_agent_work,
        'total_overhead_seconds': total_overhead,
        'overhead_percent': (total_overhead / total_wall_clock * 100) if total_wall_clock > 0 else 0,
        'queue_wait_total_seconds': 0,
        'backoff_wait_total_seconds': 0,
        'phase_transition_total_seconds': 0,
        'framework_tax_percent': (total_overhead / total_wall_clock * 100) if total_wall_clock > 0 else 0
    })

    # Log session end (verbose telemetry)
    log_telemetry('environment', coordinator_id, 'session_end', {
        'session_id': f"sess-{team_id}",
        'total_duration_seconds': total_wall_clock,
        'exit_status': team_status,
        'teams_executed': 1,
        'total_agents_spawned': aggregated_result['total_agents'],
        'total_tokens_consumed': sum(
            o.get('metadata', {}).get('token_usage', {}).get('total_tokens', 0)
            for o in all_agent_outputs
        ),
        'total_estimated_cost_usd': None,
        'telemetry_events_logged': None,
        'log_file_size_bytes': None
    }, project_root, team_name)
    display_telemetry_event('environment', coordinator_id, 'session_end', {
        'session_id': f"sess-{team_id}",
        'total_duration_seconds': total_wall_clock,
        'exit_status': team_status,
        'teams_executed': 1,
        'total_agents_spawned': aggregated_result['total_agents'],
        'total_tokens_consumed': sum(
            o.get('metadata', {}).get('token_usage', {}).get('total_tokens', 0)
            for o in all_agent_outputs
        ),
        'total_estimated_cost_usd': None,
        'telemetry_events_logged': None,
        'log_file_size_bytes': None
    })

    # Step 7.5: Build and return TeamResult
    team_result = {
        'team_id': team_id,
        'team_name': team_name,
        'status': team_status,

        'aggregated_result': aggregated_result,

        'metrics': {
            'total_duration_seconds': elapsed_since(team_start_time),
            'agent_durations': aggregated_result['summary']['agent_durations'],
            'success_rate': aggregated_result['summary']['success_rate'],
            'parallel_speedup': aggregated_result['summary'].get('parallel_speedup'),
            'retry_count': total_retry_count,
            'models_used': aggregated_result['summary'].get('models_used', {})
        },

        'approval_decisions': {
            'before_execution': before_execution_decision,
            'after_completion': after_completion_decision
        },

        'telemetry_log_path': telemetry_log_path,

        'error': None if team_status in ('completed', 'partial_success') else (
            f"Team execution {team_status}. "
            f"{aggregated_result['failed']} of {aggregated_result['total_agents']} agents failed."
        )
    }

    return {'team_result': team_result}
```

---

## Error Handling

### Validation Failure (Phase 1)

**Condition**: Team definition fails validation (missing fields, invalid refs, circular deps)
**Behavior**: Abort immediately with detailed error message. No agents are spawned.
**Telemetry**: `lifecycle | coordinator | failed | {"reason":"validation_failed"}`

### User Rejection (Phase 3 or Phase 6)

**Condition**: User rejects plan at before_execution or results at after_completion gate
**Behavior**: Abort gracefully. No agents spawned (if before_execution). Results discarded (if after_completion).
**Telemetry**: `coordination | coordinator | plan_rejected` or `results_rejected`

### Depth Limit Exceeded (Phase 4)

**Condition**: Agent spawn at depth > 3
**Behavior**: Resource manager rejects spawn. If agent is critical, abort team. Otherwise, skip agent.
**Telemetry**: `resource | team_id | depth_limit_exceeded | {"requested_depth":4,"max_depth":3}`

### Agent Failure with Retry (Phase 4)

**Condition**: Agent task fails during execution
**Behavior**: Check retry eligibility (retry_count < max_retries). If eligible, wait [1, 2, 4] seconds (exponential backoff), then spawn retry. If max retries exhausted, apply failure_handling strategy.
**Telemetry**: `lifecycle | agent_id | failed`, then `lifecycle | agent_id | retry_scheduled`

### Agent Failure - Continue Strategy (Phase 4)

**Condition**: Agent fails after max retries and `failure_handling == "continue"`
**Behavior**: Log failure, include in aggregated results as failed, continue with remaining agents.
**Telemetry**: `coordination | coordinator | failure_continued`

### Agent Failure - Abort Strategy (Phase 4)

**Condition**: Agent fails after max retries and (`failure_handling == "abort"` or `agent.critical == true`)
**Behavior**: Mark all pending agents as failed, abort team execution.
**Telemetry**: `coordination | coordinator | execution_aborted | {"reason":"agent_failure"}`

### Team Timeout (Phase 4)

**Condition**: Team execution exceeds configured timeout (default 30 minutes)
**Behavior**: Mark all active agents as failed. Abort team execution. Return `timed_out` status.
**Telemetry**: `resource | team_id | timeout_warning` (at 5 min remaining), then `resource | team_id | timeout`

### Team Queue Full (Phase 2)

**Condition**: Max concurrent teams reached (default 5)
**Behavior**: Queue team in FIFO order. Wait for a slot to open.
**Telemetry**: `resource | coordinator | team_queued`

### Telemetry Failure (Any Phase)

**Condition**: Telemetry write fails
**Behavior**: Log warning internally but **never halt execution**. Telemetry is non-blocking (REQ-NF-6).
**Telemetry**: Warning logged, execution continues normally.

---

## Retry Logic Detail (REQ-F-5)

### Exponential Backoff Schedule

| Attempt | Backoff Delay | Total Wait Time |
|---------|---------------|-----------------|
| 1st attempt (initial) | 0 seconds | 0 seconds |
| 2nd attempt (retry 1) | 1 second | 1 second |
| 3rd attempt (retry 2) | 2 seconds | 3 seconds |
| 4th attempt (retry 3) | 4 seconds | 7 seconds |
| 5th attempt | Not allowed | Max retries exhausted |

### Retry Flow

```
Agent spawned (attempt 0)
    |
    v
Agent fails
    |
    v
retry_count (0) < max_retries (3)? --> YES
    |
    v
Wait 1 second (backoff_seconds[0])
    |
    v
Spawn retry agent (attempt 1)
    |
    v
Agent fails again
    |
    v
retry_count (1) < max_retries (3)? --> YES
    |
    v
Wait 2 seconds (backoff_seconds[1])
    |
    v
Spawn retry agent (attempt 2)
    |
    v
Agent fails again
    |
    v
retry_count (2) < max_retries (3)? --> YES
    |
    v
Wait 4 seconds (backoff_seconds[2])
    |
    v
Spawn retry agent (attempt 3)
    |
    v
Agent fails again
    |
    v
retry_count (3) < max_retries (3)? --> NO
    |
    v
Apply failure_handling strategy:
  - "continue": Log failure, proceed with other agents
  - "abort": Stop team execution
```

---

## Failure Handling Detail (REQ-F-6)

### "continue" Strategy

When `failure_handling: continue` is set in the team definition:
- Failed agents are logged with their failure reason
- Remaining agents continue executing
- Result aggregator includes both successful and failed agents
- Team status is set to `partial_success` if at least one agent succeeded

### "abort" Strategy

When `failure_handling: abort` is set in the team definition:
- The first agent failure (after retries exhausted) triggers abort
- All pending agents are cancelled
- All active agents are marked as failed
- Team status is set to `aborted`

### Critical Agent Override

Agents with `critical: true` in the team definition always trigger abort on failure, regardless of the `failure_handling` setting. This allows teams to have critical agents (e.g., analyze-agent) that must succeed, while non-critical agents (e.g., individual write-agents) can fail without aborting.

---

## Integration Guide

### How the /team-run Command Invokes This Skill

```markdown
# In commands/team-run.md

## Execution Flow

1. Parse command arguments: team_name, --max-agents, --timeout, etc.
2. Resolve project root directory
3. Build config_overrides from CLI flags
4. Build context from target path and additional args
5. Read and follow skills/team-orchestration/SKILL.md
6. Call execute_team(team_name, project_root, config_overrides, context)
7. Display TeamResult to user:
   - Status (completed/partial_success/failed/aborted/timed_out)
   - Agent counts and success rate
   - Merged files and metrics
   - Telemetry log path (if enabled)
```

### How Team Coordinators Extend This Skill

Team coordinators (e.g., `teams/testing-parallel-coordinator.md`) provide team-specific logic:
- **Agent composition**: Which agents to spawn and in what order
- **Batching strategy**: How to divide work across parallel agents
- **Task prompts**: Agent-specific instructions and context
- **Custom aggregation**: Team-specific result merging logic

The coordinator file is referenced in the team definition's `coordinator` field and is invoked by this orchestration skill during Phase 3 (plan building) and Phase 4 (agent prompt construction).

### Telemetry Events Logged by This Skill

| Phase | Event Type | Status | Description |
|-------|-----------|--------|-------------|
| 0 | environment | session_start | Execution context captured |
| 0 | environment | environment_snapshot | Full environment state |
| 0 | lifecycle | spawned | Coordinator initialized |
| 1 | error | validation_check | Each validation check logged |
| 1 | lifecycle | failed | Validation failure (early exit) |
| 1 | coordination | team_loaded | Team definition loaded successfully |
| 1 | config | config_loaded | Full team definition captured |
| 1 | config | config_override_applied | CLI override logged |
| 2 | resource | team_queued | Team waiting for concurrent slot |
| 2 | resource | team_active | Team execution started |
| 3 | coordination | plan_proposed | Execution plan created |
| 3 | coordination | plan_approved | User approved plan |
| 3 | coordination | plan_modification_requested | User requested changes |
| 3 | dependency | graph_constructed | Full dependency graph logged |
| 3 | dependency | phase_planned | Each execution phase logged |
| 3 | timing | phase_transition | Phase 1->3 transition time |
| 3 | approval | gate_entered | Before-execution gate reached |
| 3 | approval | user_response_received | User decision logged |
| 3 | lifecycle | failed | User rejected plan (early exit) |
| 4 | coordination | phase_start | Execution phase begins |
| 4 | agent_io | prompt_constructed | Full agent prompt captured |
| 4 | agent_io | output_received | Full agent output captured |
| 4 | timing | queue_wait_time | FIFO queue wait duration |
| 4 | timing | backoff_wait | Retry backoff duration |
| 4 | error | retry_decision | Retry logic decision logged |
| 4 | error | error_classified | Error categorized |
| 4 | error | state_transition | Agent state change logged |
| 4 | cost | cumulative_cost | Running cost total |
| 4 | cost | memory_snapshot | Context window usage |
| 4 | lifecycle | retry_scheduled | Agent retry with backoff |
| 4 | coordination | execution_aborted | Critical failure or abort |
| 4 | coordination | failure_continued | Non-critical failure, continuing |
| 4 | coordination | dequeued_agent_spawned | Queued agent now active |
| 4 | coordination | phase_complete | Execution phase finished |
| 4 | timing | phase_transition | Inter-phase transition time |
| 4 | data_flow | data_passed | Output flowing between phases |
| 5 | coordination | results_aggregated | Results combined |
| 6 | coordination | results_iteration_requested | User wants changes |
| 6 | coordination | results_rejected | User discarded results |
| 6 | coordination | after_completion_skipped | Skipped (execution aborted) |
| 6 | approval | gate_entered | After-completion gate reached |
| 6 | approval | user_response_received | User decision logged |
| 7 | timing | overhead_summary | Framework overhead calculated |
| 7 | environment | session_end | Session finalized |
| 7 | lifecycle | completed | Coordinator finished |
| 7 | resource | team_finalized | Resources cleaned up |

---

## Testing Checklist

For TASK-011 acceptance:

### Phase 1: Load and Validate
- [ ] Loads team definition via team-loader.md
- [ ] Aborts with clear error on invalid team definition
- [ ] Displays validation warnings to user
- [ ] Applies CLI config overrides (max_agents, timeout, gates, telemetry)
- [ ] Logs team_loaded coordination event

### Phase 2: Resource Registration
- [ ] Registers team with resource manager
- [ ] Handles team queue when at concurrent team limit
- [ ] Logs team_queued and team_active resource events

### Phase 3: Approval Gate (Before Execution)
- [ ] Invokes approval-gate-handler for before_execution gate
- [ ] Handles Approve response (continues to Phase 4)
- [ ] Handles Reject response (aborts, returns TeamResult with status "aborted")
- [ ] Handles Modify response (regenerates plan, loops up to 3 iterations)
- [ ] Bypasses gate when disabled (logs approval_bypassed)
- [ ] Logs plan_proposed and plan_approved coordination events

### Phase 4: Agent Execution
- [ ] Spawns agents via Task tool (coordinator-specialist pattern, REQ-F-1)
- [ ] Respects max_agents limit via resource manager (REQ-F-7)
- [ ] Handles FIFO queuing when agent limit reached (REQ-F-10)
- [ ] Tracks agent state via lifecycle manager (spawned -> running -> completed/failed)
- [ ] Implements retry logic: max 3 retries with [1, 2, 4] second backoff (REQ-F-5)
- [ ] Handles failure_handling "continue": logs and proceeds (REQ-F-6)
- [ ] Handles failure_handling "abort": stops all agents (REQ-F-6)
- [ ] Handles critical agent failure: aborts regardless of failure_handling
- [ ] Handles dequeued agents (auto-spawned from queue)
- [ ] Enforces timeout via periodic checks (REQ-F-9)
- [ ] Logs all lifecycle and coordination events throughout

### Phase 5: Result Aggregation
- [ ] Invokes result-aggregator with all agent outputs
- [ ] Determines team status: completed, partial_success, failed, aborted, timed_out
- [ ] Logs results_aggregated coordination event

### Phase 6: Approval Gate (After Completion)
- [ ] Invokes approval-gate-handler for after_completion gate
- [ ] Handles Accept response (finalizes results)
- [ ] Handles Reject/Discard response (discards results, status "aborted")
- [ ] Skips gate when execution was aborted
- [ ] Logs appropriate coordination events

### Phase 7: Finalize
- [ ] Gets final team status from lifecycle manager
- [ ] Logs coordinator completion lifecycle event
- [ ] Cleans up team registration via resource_manager.on_team_complete()
- [ ] Returns complete TeamResult with all metrics

### End-to-End
- [ ] Full workflow with 2+ agents completes successfully
- [ ] Partial failure (1 of 3 agents fails) returns partial_success
- [ ] Total failure (all agents fail) returns failed
- [ ] User rejection at before_execution returns aborted
- [ ] Timeout returns timed_out
- [ ] Telemetry log captures all events when enabled
- [ ] Telemetry failures do not halt execution (REQ-NF-6)

---

## Example Execution Trace

### Scenario: Testing Team with 3 Write-Agents, 1 Failure

```
Phase 0: Initialize
  coordinator_id = "testing-parallel-coordinator-20260213T143000"
  team_id = "testing-parallel-20260213T143000"
  Telemetry: lifecycle | coordinator | spawned

Phase 1: Load Team Definition
  Load teams/testing-parallel.md
  Validation: PASSED (no errors, no warnings)
  max_agents=5, timeout=30min, failure_handling=continue
  Telemetry: coordination | coordinator | team_loaded

Phase 2: Register Team
  Active teams: 1 of 5 max
  Team registered, timeout at 15:00:00
  Telemetry: resource | coordinator | team_active

Phase 3: Before Execution Approval
  Plan: 3 parallel write-agents for 12 test targets
  Telemetry: coordination | coordinator | plan_proposed
  User: Approve
  Telemetry: coordination | coordinator | plan_approved

Phase 4: Execute Agents
  Phase 1/3 (Sequential): analyze-agent
    Spawn analyze-agent (depth 2)
    Telemetry: lifecycle | analyze-agent | spawned
    Telemetry: lifecycle | analyze-agent | start
    ... agent executes ...
    Telemetry: lifecycle | analyze-agent | completed (15.2s)

  Phase 2/3 (Parallel): write-agent-1, write-agent-2, write-agent-3
    Spawn write-agent-1, write-agent-2, write-agent-3 (depth 2)
    Telemetry: lifecycle | write-agent-1 | spawned
    Telemetry: lifecycle | write-agent-2 | spawned
    Telemetry: lifecycle | write-agent-3 | spawned

    write-agent-1: Completed (28.5s, 5 tests)
    Telemetry: lifecycle | write-agent-1 | completed

    write-agent-2: FAILED (timeout, 120s)
    Telemetry: lifecycle | write-agent-2 | failed
    Retry 1: Wait 1s, spawn retry
    Telemetry: lifecycle | write-agent-2-r1 | retry_scheduled
    write-agent-2-r1: FAILED again
    Retry 2: Wait 2s, spawn retry
    write-agent-2-r2: FAILED again
    Retry 3: Wait 4s, spawn retry
    write-agent-2-r3: FAILED (max retries exhausted)
    failure_handling=continue -> Log and proceed
    Telemetry: coordination | coordinator | failure_continued

    write-agent-3: Completed (30.0s, 7 tests)
    Telemetry: lifecycle | write-agent-3 | completed

  Phase 3/3 (Sequential): execute-agent
    Spawn execute-agent (depth 2)
    Telemetry: lifecycle | execute-agent | spawned
    ... agent runs tests ...
    Telemetry: test | execute-agent | execution_complete (12 tests, 10 passed)
    Telemetry: lifecycle | execute-agent | completed

Phase 5: Aggregate Results
  total=3 write-agents, successful=2, failed=1
  merged_files: [test_calculator.py, test_user.py]
  merged_metrics: {tests_generated: 12}
  success_rate: 0.67
  team_status: partial_success
  Telemetry: coordination | coordinator | results_aggregated

Phase 6: After Completion Approval
  Gate disabled (after_completion: false)
  Telemetry: coordination | coordinator | approval_bypassed

Phase 7: Finalize
  Duration: 198.5 seconds
  Cleanup team registration
  Telemetry: lifecycle | coordinator | completed
  Telemetry: resource | coordinator | team_finalized

  Return TeamResult:
    status: partial_success
    successful: 2, failed: 1
    success_rate: 0.67
    retry_count: 3
```

---

## References

- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md`
  - REQ-F-1 (Hierarchical orchestration via coordinator-specialist pattern)
  - REQ-F-2 (Parallel execution of independent agents)
  - REQ-F-3 (Agent lifecycle tracking)
  - REQ-F-4 (Depth limit of 3 levels)
  - REQ-F-5 (Retry logic: max 3 retries with exponential backoff)
  - REQ-F-6 (Failure handling: continue or abort)
  - REQ-F-7 (Max 5 agents per team)
  - REQ-F-8 (Max 5 concurrent teams)
  - REQ-F-9 (Team timeout enforcement)
  - REQ-F-10 (FIFO queuing for agents)
  - REQ-F-17 to REQ-F-20 (Approval gates)

- **Plan**: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md`
  - Architecture Overview (coordinator-specialist pattern)
  - Technical Decisions (retry logic, failure handling, resource management)
  - Skill Composition Patterns

- **Sub-Skills**:
  - `skills/team-orchestration/team-loader.md` (TASK-001)
  - `skills/team-orchestration/agent-lifecycle-manager.md` (TASK-002)
  - `skills/team-orchestration/resource-manager.md` (TASK-003)
  - `skills/team-orchestration/approval-gate-handler.md` (TASK-004)
  - `skills/team-orchestration/result-aggregator.md` (TASK-005)
  - `skills/telemetry/SKILL.md` (TASK-006)
  - `skills/team-orchestration/agent-schema.md` (back-prop P0)
  - `skills/team-orchestration/coordinator-schema.md` (back-prop P0)
  - `skills/team-orchestration/file-conflict-detector.md` (back-prop P1)
  - `skills/team-orchestration/plan-visualizer.md` (back-prop P1)
  - `skills/telemetry/event-types.md` (back-prop P0)
  - `skills/model-selection/config-manager.md` (back-prop P0)
  - `skills/model-selection/model-resolver.md` (back-prop P0)

- **Improvement Spec**: `.sdd/specs/back-propagation-improvements.md`
  - Back-propagation analysis from sample_teams_project
  - 6 P0 critical blockers, 12 P1 improvements, 8 P2 enhancements

---

## Helper Functions (Added by Back-Propagation Improvements)

### save_execution_checkpoint()

```python
def save_execution_checkpoint(project_root: str, team_id: str, state: dict) -> None:
    """
    Save execution checkpoint for recovery via --resume.

    Checkpoint file: {project_root}/.claude/teamsters-state/{team_id}.json

    Args:
        project_root: Project root path
        team_id: Team execution ID
        state: Checkpoint state dict containing:
            - team_name: Team name
            - completed_phase: Last completed phase number
            - total_phases: Total number of phases
            - completed_agents: List of completed agent IDs
            - failed_agents: List of failed agent IDs
            - partial_outputs: All agent outputs so far
            - elapsed_seconds: Time elapsed since start
            - checkpoint_time: ISO 8601 timestamp
    """
    try:
        state_dir = f"{project_root}/.claude/teamsters-state"
        os.makedirs(state_dir, exist_ok=True)
        state_file = f"{state_dir}/{team_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception:
        pass  # Non-blocking - checkpoint failure doesn't halt execution
```

### cleanup_execution_checkpoint()

```python
def cleanup_execution_checkpoint(project_root: str, team_id: str) -> None:
    """Remove checkpoint file after successful execution."""
    try:
        state_file = f"{project_root}/.claude/teamsters-state/{team_id}.json"
        if os.path.exists(state_file):
            os.remove(state_file)
    except Exception:
        pass  # Non-blocking
```

### save_execution_history()

```python
def save_execution_history(project_root: str, entry: dict) -> None:
    """
    Append execution record to persistent history for --history queries.

    History file: {project_root}/.claude/teamsters-history.json

    Args:
        project_root: Project root path
        entry: History entry dict containing:
            - team: Team name
            - execution_id: Unique execution ID
            - timestamp: ISO 8601 start time
            - duration_seconds: Total wall-clock time
            - agents: Total agent count
            - successful: Successful agent count
            - failed: Failed agent count
            - success_rate: 0.0 to 1.0
            - models_used: {model: count} breakdown
            - telemetry_log: Path to telemetry log file
    """
    try:
        history_file = f"{project_root}/.claude/teamsters-history.json"
        history = {'executions': []}

        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)

        history['executions'].append(entry)

        # Keep last 100 executions
        if len(history['executions']) > 100:
            history['executions'] = history['executions'][-100:]

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    except Exception:
        pass  # Non-blocking
```

### detect_file_conflicts()

```python
def detect_file_conflicts(agents: list, dependencies: list) -> dict:
    """
    Detect file conflicts between agents using files_read/files_write metadata.

    Invokes: skills/team-orchestration/file-conflict-detector.md

    Args:
        agents: List of agent specs with optional files_read/files_write
        dependencies: Explicit dependency list

    Returns:
        dict with:
            - conflicts: List of write-write conflicts in parallel phases
            - implicit_deps: List of read-after-write implicit dependencies
            - warnings: List of warning messages
    """
    # Delegate to file-conflict-detector sub-skill
    return file_conflict_detector.build_file_dependency_graph(agents, dependencies)
```

### validate_agent_definition()

```python
def validate_agent_definition(agent_spec: dict, project_root: str) -> dict:
    """
    Validate an agent definition against the agent schema.

    Invokes: skills/team-orchestration/agent-schema.md

    Args:
        agent_spec: Agent spec from team definition
        project_root: Project root for resolving file paths

    Returns:
        dict with: valid (bool), errors (list), warnings (list)
    """
    # Delegate to agent-schema sub-skill
    return agent_schema.validate(agent_spec, project_root)
```

### resolve_model()

```python
def resolve_model(agent_name: str, config_overrides: dict) -> dict:
    """
    Resolve the optimal model for an agent.

    Invokes: skills/model-selection/model-resolver.md

    Args:
        agent_name: Name of the agent
        config_overrides: CLI overrides

    Returns:
        dict with: model (str), timeout (int), source (str)
    """
    # Delegate to model-resolver sub-skill
    return model_resolver.resolve_model(agent_name, config_overrides)
```

---

**Last Updated**: 2026-03-25
**Status**: Implementation (back-propagation improvements applied)
