---
name: agent-lifecycle-manager
description: Track agent state transitions (spawned -> running -> completed/failed) with timestamps, metadata, retry counters, and team-level status aggregation.
user-invocable: false
---

# Agent Lifecycle Manager Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Track agent state machine transitions with comprehensive metadata and provide team-level status aggregation

**Used By**: Team Orchestration SKILL, Resource Manager, Telemetry System

---

## Overview

The Agent Lifecycle Manager Skill provides stateful tracking of all agents managed by the team orchestration framework. It maintains a complete state machine for each agent (spawned -> running -> completed/failed) with timestamps, metadata, retry counters, and hierarchical relationships.

This skill is critical for:
- **Observability**: Tracking agent status for telemetry and user visibility
- **Coordination**: Managing dependencies and parallel execution
- **Reliability**: Tracking retries and failure handling
- **Metrics**: Calculating durations and aggregate team statistics

### Key Principles

1. **Immutable State Snapshots**: All state queries return copies, never internal references (prevents mutation)
2. **Thread-Safe Updates**: State transitions use atomic operations (prevents race conditions)
3. **Complete Audit Trail**: Every state transition is timestamped and logged
4. **Non-Destructive Tracking**: Failed agents remain in state for post-mortem analysis

---

## Agent State Machine

```
+-------------------------------------------------------------+
|                                                             |
|  +---------+   mark_running()   +---------+               |
|  | spawned | -----------------> | running |               |
|  +---------+                     +---------+               |
|       |                               |                     |
|       |                               |                     |
|       | mark_failed()                 | mark_completed()    |
|       +----------+                    |                     |
|                  v                    v                     |
|              +--------+           +-----------+            |
|              | failed |           | completed |            |
|              +--------+           +-----------+            |
|                  |                                          |
|                  |                                          |
|                  +---> retry (if retry_count < max) -------+
|                        spawn_agent() with retry_count++    |
|                                                             |
+-------------------------------------------------------------+

State Transitions:
- spawned -> running (agent begins execution)
- running -> completed (agent finishes successfully)
- running -> failed (agent encounters error)
- spawned -> failed (spawn failure, e.g., timeout before starting)
- failed -> spawned (retry, creates new agent_id with incremented retry_count)
```

---

## Skill Interface

### Input: spawn_agent()

```yaml
agent_spec:
  agent_type: string           # Path to agent definition (e.g., "agents/write-agent.md")
  task_description: string     # Human-readable task description
parent_id: string              # ID of parent agent (coordinator)
team_id: string                # ID of team this agent belongs to
depth: integer                 # Nesting level (1-3)
retry_count: integer           # Current retry attempt (0 for first spawn)
```

### Output: spawn_agent()

```yaml
agent_id: string               # Unique agent identifier (timestamp-ms + random hex)
agent_state: AgentState        # Initial state snapshot
```

### Input: mark_running()

```yaml
agent_id: string               # Agent to mark as running
task_description: string       # Detailed task description
```

### Output: mark_running()

```yaml
success: boolean               # Whether state transition succeeded
agent_state: AgentState        # Updated state snapshot (null if failed)
error: string | null           # Error message if transition invalid
```

### Input: mark_completed()

```yaml
agent_id: string               # Agent to mark as completed
output: object                 # Agent output (arbitrary structure)
output_summary: string         # Human-readable summary
```

### Output: mark_completed()

```yaml
success: boolean               # Whether state transition succeeded
agent_state: AgentState        # Final state snapshot with duration_seconds
error: string | null           # Error message if transition invalid
```

### Input: mark_failed()

```yaml
agent_id: string               # Agent to mark as failed
reason: string                 # Failure reason (e.g., "timeout", "exception", "validation_error")
last_error: string             # Detailed error message or stack trace
```

### Output: mark_failed()

```yaml
success: boolean               # Whether state transition succeeded
agent_state: AgentState        # Final state snapshot
should_retry: boolean          # Whether agent should be retried (retry_count < max_retries)
error: string | null           # Error message if transition invalid
```

### Input: get_team_status()

```yaml
team_id: string                # Team to get status for
```

### Output: get_team_status()

```yaml
team_status:
  team_id: string
  total_agents: integer        # Total agents spawned for this team
  spawned_count: integer       # Agents in spawned state
  running_count: integer       # Agents in running state
  completed_count: integer     # Agents in completed state
  failed_count: integer        # Agents in failed state
  success_rate: float          # completed / (completed + failed), 0.0-1.0
  total_duration_seconds: float # Sum of all completed agent durations
  average_duration_seconds: float # Average duration of completed agents
  agents: list[AgentState]     # List of agent state snapshots (for detailed view)
```

---

## Agent State Data Structure

```yaml
AgentState:
  # Identity
  agent_id: string              # Unique identifier (timestamp-ms + random hex)
  agent_type: string            # Agent definition path
  parent_id: string             # Parent coordinator ID
  team_id: string               # Team this agent belongs to
  depth: integer                # Nesting level (1-3)

  # Lifecycle Status
  status: string                # "spawned" | "running" | "completed" | "failed"

  # Timestamps (ISO 8601 UTC)
  spawned_at: timestamp         # When agent was spawned
  started_at: timestamp | null  # When agent began execution (null until mark_running)
  completed_at: timestamp | null # When agent finished (null until mark_completed/mark_failed)

  # Metrics
  duration_seconds: float | null # Total execution time (started_at -> completed_at)

  # Retry Tracking
  retry_count: integer          # Number of retries attempted (0 = first attempt)
  max_retries: integer          # Maximum allowed retries (default: 3)

  # Failure Handling
  failure_reason: string | null # High-level reason (if failed)
  last_error: string | null     # Detailed error message (if failed)

  # Output (if completed)
  output: object | null         # Agent output (arbitrary structure)
  output_summary: string | null # Human-readable summary

  # Task Context
  task_description: string      # Human-readable task description

  # Dependencies (optional, for coordinators with explicit dependencies)
  dependencies: list[string]    # Agent IDs this agent depends on
  dependents: list[string]      # Agent IDs depending on this agent
```

---

## State Management Implementation

### Spawn Agent

```python
def spawn_agent(
    agent_spec: dict,
    parent_id: str,
    team_id: str,
    depth: int,
    retry_count: int = 0
) -> dict:
    """
    Create new agent state entry in spawned status.

    Args:
        agent_spec: Agent specification (agent_type, task_description)
        parent_id: ID of parent coordinator
        team_id: ID of team this agent belongs to
        depth: Nesting level (1-3)
        retry_count: Retry attempt number (0 for first spawn)

    Returns:
        dict with agent_id and agent_state
    """
    # Generate unique agent ID
    agent_id = generate_agent_id(agent_spec['agent_type'], team_id, retry_count)

    # Create initial state
    state = {
        # Identity
        'agent_id': agent_id,
        'agent_type': agent_spec['agent_type'],
        'parent_id': parent_id,
        'team_id': team_id,
        'depth': depth,

        # Lifecycle Status
        'status': 'spawned',

        # Timestamps
        'spawned_at': current_timestamp_utc(),
        'started_at': None,
        'completed_at': None,

        # Metrics
        'duration_seconds': None,

        # Retry Tracking
        'retry_count': retry_count,
        'max_retries': agent_spec.get('max_retries', 3),

        # Failure Handling
        'failure_reason': None,
        'last_error': None,

        # Output
        'output': None,
        'output_summary': None,

        # Task Context
        'task_description': agent_spec.get('task_description', 'No description provided'),

        # Dependencies
        'dependencies': agent_spec.get('dependencies', []),
        'dependents': []
    }

    # Store state (thread-safe)
    agent_states[agent_id] = state

    # Update team index
    if team_id not in team_agent_index:
        team_agent_index[team_id] = []
    team_agent_index[team_id].append(agent_id)

    # Return snapshot (not reference)
    return {
        'agent_id': agent_id,
        'agent_state': copy.deepcopy(state)
    }


def generate_agent_id(agent_type: str, team_id: str, retry_count: int) -> str:
    """
    Generate unique agent ID with millisecond precision and random suffix.

    Format: {agent_type_name}-{team_id}-{timestamp_ms}-{random_hex}-r{retry}
    Example: write-agent-testing-parallel-20260213T143001.123-a7f2-r0

    The millisecond-precision timestamp combined with a 4-character random
    hex suffix ensures uniqueness even when multiple agents are spawned
    within the same millisecond. This is important because agent IDs may
    be used as PUIDs (persistent unique IDs) to deduplicate sessions.

    Args:
        agent_type: Path to agent definition
        team_id: Team ID
        retry_count: Retry attempt number

    Returns:
        Unique agent ID string
    """
    import os
    import secrets
    from datetime import datetime

    # Extract agent name from path
    agent_name = os.path.splitext(os.path.basename(agent_type))[0]

    # Generate timestamp with millisecond precision
    now = datetime.utcnow()
    timestamp = now.strftime('%Y%m%dT%H%M%S') + '.' + now.strftime('%f')[:3]

    # Generate 4-character random hex suffix for collision avoidance
    random_hex = secrets.token_hex(2)  # 2 bytes = 4 hex chars

    # Combine components
    agent_id = f"{agent_name}-{team_id}-{timestamp}-{random_hex}-r{retry_count}"

    return agent_id
```

---

### Mark Running

```python
def mark_running(agent_id: str, task_description: str) -> dict:
    """
    Transition agent from spawned to running status.

    Args:
        agent_id: Agent to mark as running
        task_description: Detailed task description

    Returns:
        dict with success, agent_state, error
    """
    # Validate agent exists
    if agent_id not in agent_states:
        return {
            'success': False,
            'agent_state': None,
            'error': f"Agent not found: {agent_id}"
        }

    state = agent_states[agent_id]

    # Validate state transition
    if state['status'] != 'spawned':
        return {
            'success': False,
            'agent_state': None,
            'error': f"Invalid state transition: cannot mark as running from '{state['status']}' (expected 'spawned')"
        }

    # Update state (atomic)
    state['status'] = 'running'
    state['started_at'] = current_timestamp_utc()
    state['task_description'] = task_description

    # Return snapshot
    return {
        'success': True,
        'agent_state': copy.deepcopy(state),
        'error': None
    }
```

---

### Mark Completed

```python
def mark_completed(agent_id: str, output: object, output_summary: str) -> dict:
    """
    Transition agent from running to completed status.

    Args:
        agent_id: Agent to mark as completed
        output: Agent output (arbitrary structure)
        output_summary: Human-readable summary

    Returns:
        dict with success, agent_state, error
    """
    # Validate agent exists
    if agent_id not in agent_states:
        return {
            'success': False,
            'agent_state': None,
            'error': f"Agent not found: {agent_id}"
        }

    state = agent_states[agent_id]

    # Validate state transition
    if state['status'] != 'running':
        return {
            'success': False,
            'agent_state': None,
            'error': f"Invalid state transition: cannot mark as completed from '{state['status']}' (expected 'running')"
        }

    # Calculate duration
    started_at = parse_timestamp(state['started_at'])
    completed_at = current_timestamp_utc()
    duration = (parse_timestamp(completed_at) - started_at).total_seconds()

    # Update state (atomic)
    state['status'] = 'completed'
    state['completed_at'] = completed_at
    state['duration_seconds'] = duration
    state['output'] = output
    state['output_summary'] = output_summary

    # Return snapshot
    return {
        'success': True,
        'agent_state': copy.deepcopy(state),
        'error': None
    }
```

---

### Mark Failed

```python
def mark_failed(agent_id: str, reason: str, last_error: str) -> dict:
    """
    Transition agent from running/spawned to failed status.

    Args:
        agent_id: Agent to mark as failed
        reason: High-level failure reason
        last_error: Detailed error message

    Returns:
        dict with success, agent_state, should_retry, error
    """
    # Validate agent exists
    if agent_id not in agent_states:
        return {
            'success': False,
            'agent_state': None,
            'should_retry': False,
            'error': f"Agent not found: {agent_id}"
        }

    state = agent_states[agent_id]

    # Validate state transition (can fail from spawned or running)
    if state['status'] not in ['spawned', 'running']:
        return {
            'success': False,
            'agent_state': None,
            'should_retry': False,
            'error': f"Invalid state transition: cannot mark as failed from '{state['status']}' (expected 'spawned' or 'running')"
        }

    # Calculate duration (if started)
    duration = None
    if state['started_at'] is not None:
        started_at = parse_timestamp(state['started_at'])
        completed_at = current_timestamp_utc()
        duration = (parse_timestamp(completed_at) - started_at).total_seconds()

    # Update state (atomic)
    state['status'] = 'failed'
    state['completed_at'] = current_timestamp_utc()
    state['duration_seconds'] = duration
    state['failure_reason'] = reason
    state['last_error'] = last_error

    # Determine if retry should be attempted
    should_retry = state['retry_count'] < state['max_retries']

    # Return snapshot
    return {
        'success': True,
        'agent_state': copy.deepcopy(state),
        'should_retry': should_retry,
        'error': None
    }
```

---

### Get Team Status

```python
def get_team_status(team_id: str) -> dict:
    """
    Get aggregate status for all agents in a team.

    Args:
        team_id: Team to get status for

    Returns:
        dict with team_status
    """
    # Get all agents for this team
    agent_ids = team_agent_index.get(team_id, [])

    if not agent_ids:
        return {
            'team_status': {
                'team_id': team_id,
                'total_agents': 0,
                'spawned_count': 0,
                'running_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'success_rate': 0.0,
                'total_duration_seconds': 0.0,
                'average_duration_seconds': 0.0,
                'agents': []
            }
        }

    # Collect agent states
    agents = [copy.deepcopy(agent_states[aid]) for aid in agent_ids if aid in agent_states]

    # Calculate counts
    spawned_count = len([a for a in agents if a['status'] == 'spawned'])
    running_count = len([a for a in agents if a['status'] == 'running'])
    completed_count = len([a for a in agents if a['status'] == 'completed'])
    failed_count = len([a for a in agents if a['status'] == 'failed'])

    # Calculate success rate
    terminal_count = completed_count + failed_count
    success_rate = (completed_count / terminal_count) if terminal_count > 0 else 0.0

    # Calculate durations
    completed_agents = [a for a in agents if a['status'] == 'completed' and a['duration_seconds'] is not None]
    total_duration = sum(a['duration_seconds'] for a in completed_agents)
    average_duration = (total_duration / len(completed_agents)) if completed_agents else 0.0

    return {
        'team_status': {
            'team_id': team_id,
            'total_agents': len(agents),
            'spawned_count': spawned_count,
            'running_count': running_count,
            'completed_count': completed_count,
            'failed_count': failed_count,
            'success_rate': success_rate,
            'total_duration_seconds': total_duration,
            'average_duration_seconds': average_duration,
            'agents': agents
        }
    }
```

---

## Thread Safety Considerations

### Race Condition Prevention

**Problem**: Multiple coordinators updating agent states simultaneously could cause:
- Lost updates (overwriting state changes)
- Inconsistent state transitions (invalid status sequences)
- Corrupted team indexes (agents missing from team lists)

**Solution**: Use atomic operations and locks

```python
import threading

# Global state storage
agent_states = {}              # {agent_id: AgentState}
team_agent_index = {}          # {team_id: [agent_id, ...]}
state_lock = threading.Lock()  # Protects all state mutations

def spawn_agent(...):
    """Thread-safe agent spawn."""
    with state_lock:
        # All state mutations within lock
        agent_id = generate_agent_id(...)
        state = {...}
        agent_states[agent_id] = state

        if team_id not in team_agent_index:
            team_agent_index[team_id] = []
        team_agent_index[team_id].append(agent_id)

    # Return snapshot (outside lock, safe to read)
    return {'agent_id': agent_id, 'agent_state': copy.deepcopy(state)}

def mark_running(agent_id, task_description):
    """Thread-safe state transition."""
    with state_lock:
        # Validate and update within lock
        if agent_id not in agent_states:
            return {'success': False, 'error': 'Agent not found'}

        state = agent_states[agent_id]
        if state['status'] != 'spawned':
            return {'success': False, 'error': 'Invalid state transition'}

        state['status'] = 'running'
        state['started_at'] = current_timestamp_utc()
        state['task_description'] = task_description

        # Snapshot outside lock
        return {'success': True, 'agent_state': copy.deepcopy(state)}
```

**Critical Regions**:
- All state mutations must be within `state_lock` context
- State reads can be outside lock (using snapshots)
- Never return direct references to internal state (always use `copy.deepcopy`)

---

### Copy on Read

**Why**: Prevent external code from mutating internal state

```python
# WRONG: Returns reference to internal state
def get_agent_state(agent_id):
    return agent_states[agent_id]  # Caller can mutate!

# CORRECT: Returns immutable snapshot
def get_agent_state(agent_id):
    return copy.deepcopy(agent_states[agent_id])
```

**Impact**: All skill methods return `copy.deepcopy(state)` to ensure immutability

---

## Retry Handling

### Retry Logic Flow

```
Agent fails (mark_failed called)
    v
Check: retry_count < max_retries?
    v
+-----------------------------------------------+
| YES: should_retry = True                      |
|                                               |
| 1. Coordinator receives should_retry = True   |
| 2. Coordinator waits for backoff delay:       |
|    - Attempt 1 -> wait 1 second                |
|    - Attempt 2 -> wait 2 seconds               |
|    - Attempt 3 -> wait 4 seconds               |
| 3. Coordinator calls spawn_agent with         |
|    retry_count = previous_retry_count + 1     |
| 4. New agent_id generated (e.g., -r1, -r2)    |
| 5. Original failed agent remains in state     |
|    for audit trail                            |
|                                               |
+-----------------------------------------------+
    |
    | NO: should_retry = False
    v
Coordinator handles failure per team config:
- failure_handling = "continue": log and continue
- failure_handling = "abort": abort team execution
```

### Retry Counter Tracking

```python
# First spawn (no prior failures)
result = spawn_agent(agent_spec, parent_id, team_id, depth, retry_count=0)
# agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"

# Agent fails
fail_result = mark_failed(agent_id, "timeout", "Agent exceeded 120s timeout")
# should_retry: True (0 < 3)

# Coordinator retries with incremented counter
retry_result = spawn_agent(agent_spec, parent_id, team_id, depth, retry_count=1)
# agent_id: "write-agent-testing-parallel-20260213T143010.456-b3e1-r1"

# Agent fails again
fail_result = mark_failed(retry_result['agent_id'], "timeout", "Agent exceeded 120s timeout")
# should_retry: True (1 < 3)

# Coordinator retries again
retry_result = spawn_agent(agent_spec, parent_id, team_id, depth, retry_count=2)
# agent_id: "write-agent-testing-parallel-20260213T143025.789-c9d4-r2"

# Agent fails third time
fail_result = mark_failed(retry_result['agent_id'], "timeout", "Agent exceeded 120s timeout")
# should_retry: True (2 < 3)

# Final retry
retry_result = spawn_agent(agent_spec, parent_id, team_id, depth, retry_count=3)
# agent_id: "write-agent-testing-parallel-20260213T143050.012-d5a8-r3"

# Agent fails fourth time
fail_result = mark_failed(retry_result['agent_id'], "timeout", "Agent exceeded 120s timeout")
# should_retry: False (3 >= 3, max retries exhausted)

# Coordinator applies failure_handling strategy
```

**Audit Trail**: All 4 failed attempts remain in `agent_states` for post-mortem analysis

---

## Usage in Orchestrator

```markdown
# In skills/team-orchestration/SKILL.md

## Phase 1: Initialize Lifecycle Manager

1. Read this skill: skills/team-orchestration/agent-lifecycle-manager.md
2. Initialize empty state storage (handled by skill)

## Phase 2: Spawn Agents

For each agent to spawn:
1. Call spawn_agent(agent_spec, parent_id, team_id, depth, retry_count=0)
2. Store returned agent_id for monitoring
3. Use Task tool to actually spawn agent with agent_id in context

## Phase 3: Track Agent Execution

When agent starts execution:
1. Call mark_running(agent_id, task_description)
2. Log lifecycle event to telemetry

When agent completes successfully:
1. Call mark_completed(agent_id, output, output_summary)
2. Log lifecycle event to telemetry
3. Check if dependent agents can now start

When agent fails:
1. Call mark_failed(agent_id, reason, last_error)
2. Check should_retry flag
3. If should_retry:
   - Wait for backoff delay
   - Call spawn_agent with incremented retry_count
4. If not should_retry:
   - Apply failure_handling strategy (continue or abort)
5. Log lifecycle event to telemetry

## Phase 4: Monitor Team Progress

Periodically:
1. Call get_team_status(team_id)
2. Display progress to user (X/Y agents completed)
3. Log resource event to telemetry

## Phase 5: Finalize

When all agents terminal (completed or failed):
1. Call get_team_status(team_id) for final metrics
2. Report success_rate to user
3. Return team result
```

---

## Telemetry Integration

All state transitions should log telemetry events:

```python
def spawn_agent(...):
    # ... state creation logic ...

    # Log to telemetry
    log_telemetry('lifecycle', agent_id, 'spawned', {
        'parent': parent_id,
        'team_id': team_id,
        'depth': depth,
        'retry_count': retry_count
    })

    return result

def mark_running(...):
    # ... state transition logic ...

    # Log to telemetry
    log_telemetry('lifecycle', agent_id, 'start', {
        'assigned_task': task_description
    })

    return result

def mark_completed(...):
    # ... state transition logic ...

    # Log to telemetry
    log_telemetry('lifecycle', agent_id, 'completed', {
        'duration_seconds': state['duration_seconds'],
        'output_summary': output_summary
    })

    return result

def mark_failed(...):
    # ... state transition logic ...

    # Log to telemetry
    log_telemetry('lifecycle', agent_id, 'failed', {
        'reason': reason,
        'retries': state['retry_count'],
        'should_retry': should_retry,
        'last_error': last_error[:200]  # Truncate long errors
    })

    return result
```

**Note**: Telemetry logging is non-blocking (failures don't halt execution)

---

## Testing Checklist

For TASK-002 acceptance:

- [ ] Creates agent state in spawned status
- [ ] Generates unique agent_id with team_id and retry_count
- [ ] Stores agent metadata: agent_id, agent_type, parent_id, team_id, depth
- [ ] Tracks timestamps: spawned_at, started_at, completed_at
- [ ] Transitions spawned -> running via mark_running()
- [ ] Transitions running -> completed via mark_completed()
- [ ] Transitions running -> failed via mark_failed()
- [ ] Transitions spawned -> failed via mark_failed() (spawn failure case)
- [ ] Calculates duration_seconds on completion (started_at -> completed_at)
- [ ] Returns should_retry = True when retry_count < max_retries
- [ ] Returns should_retry = False when retry_count >= max_retries
- [ ] Increments retry_count on subsequent spawn_agent calls
- [ ] Validates state transitions (rejects invalid transitions)
- [ ] Returns error for invalid state transitions
- [ ] Returns error for non-existent agent_id
- [ ] get_team_status() returns counts: spawned, running, completed, failed
- [ ] get_team_status() calculates success_rate correctly
- [ ] get_team_status() calculates total_duration_seconds correctly
- [ ] get_team_status() calculates average_duration_seconds correctly
- [ ] get_team_status() returns empty status for unknown team_id
- [ ] All methods return state snapshots (not internal references)
- [ ] State snapshots are immutable (use copy.deepcopy)
- [ ] Thread-safe updates (state_lock protects mutations)
- [ ] Multiple teams can be tracked simultaneously
- [ ] Agent states remain in storage after failure (audit trail)

---

## Example State Snapshots

### Spawned Agent

```yaml
agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"
agent_type: "agents/write-agent.md"
parent_id: "testing-coordinator-20260213T143000"
team_id: "testing-parallel"
depth: 2
status: "spawned"
spawned_at: "2026-02-13T14:30:01.123Z"
started_at: null
completed_at: null
duration_seconds: null
retry_count: 0
max_retries: 3
failure_reason: null
last_error: null
output: null
output_summary: null
task_description: "Generate tests for src/user_service.py"
dependencies: []
dependents: []
```

### Running Agent

```yaml
agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"
agent_type: "agents/write-agent.md"
parent_id: "testing-coordinator-20260213T143000"
team_id: "testing-parallel"
depth: 2
status: "running"
spawned_at: "2026-02-13T14:30:01.123Z"
started_at: "2026-02-13T14:30:01.500Z"
completed_at: null
duration_seconds: null
retry_count: 0
max_retries: 3
failure_reason: null
last_error: null
output: null
output_summary: null
task_description: "Generate tests for src/user_service.py (5 test cases)"
dependencies: []
dependents: []
```

### Completed Agent

```yaml
agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"
agent_type: "agents/write-agent.md"
parent_id: "testing-coordinator-20260213T143000"
team_id: "testing-parallel"
depth: 2
status: "completed"
spawned_at: "2026-02-13T14:30:01.123Z"
started_at: "2026-02-13T14:30:01.500Z"
completed_at: "2026-02-13T14:30:29.800Z"
duration_seconds: 28.3
retry_count: 0
max_retries: 3
failure_reason: null
last_error: null
output:
  tests_generated: 5
  files_written: ["tests/test_user_service.py"]
  framework: "pytest"
output_summary: "Generated 5 tests for user_service"
task_description: "Generate tests for src/user_service.py (5 test cases)"
dependencies: []
dependents: []
```

### Failed Agent (Will Retry)

```yaml
agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"
agent_type: "agents/write-agent.md"
parent_id: "testing-coordinator-20260213T143000"
team_id: "testing-parallel"
depth: 2
status: "failed"
spawned_at: "2026-02-13T14:30:01.123Z"
started_at: "2026-02-13T14:30:01.500Z"
completed_at: "2026-02-13T14:32:01.500Z"
duration_seconds: 120.0
retry_count: 0
max_retries: 3
failure_reason: "timeout"
last_error: "Agent exceeded 120s timeout while generating tests"
output: null
output_summary: null
task_description: "Generate tests for src/user_service.py (5 test cases)"
dependencies: []
dependents: []
```

### Team Status Example

```yaml
team_status:
  team_id: "testing-parallel"
  total_agents: 5
  spawned_count: 0
  running_count: 1
  completed_count: 3
  failed_count: 1
  success_rate: 0.75  # 3 / (3 + 1)
  total_duration_seconds: 85.6  # Sum of 3 completed agents
  average_duration_seconds: 28.53  # 85.6 / 3
  agents:
    - agent_id: "analyze-agent-testing-parallel-20260213T143000.100-e1b3-r0"
      status: "completed"
      duration_seconds: 15.2
      # ... full state ...
    - agent_id: "write-agent-testing-parallel-20260213T143001.123-a7f2-r0"
      status: "completed"
      duration_seconds: 28.3
      # ... full state ...
    - agent_id: "write-agent-testing-parallel-20260213T143002.250-f4c6-r0"
      status: "failed"
      duration_seconds: 120.0
      failure_reason: "timeout"
      # ... full state ...
    - agent_id: "write-agent-testing-parallel-20260213T143003.380-d2e9-r0"
      status: "completed"
      duration_seconds: 42.1
      # ... full state ...
    - agent_id: "execute-agent-testing-parallel-20260213T143030.500-b8a1-r0"
      status: "running"
      duration_seconds: null
      # ... full state ...
```

---

## References

- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Agent State Tracking)
- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-3, REQ-F-5)
- Related Skills:
  - `skills/team-orchestration/resource-manager.md` (uses this for state tracking)
  - `skills/telemetry/SKILL.md` (logs lifecycle events)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-002)
