---
name: resource-manager
description: Enforce agent/team limits (max 5 per team, max 5 concurrent teams), implement FIFO queuing, enforce depth limits (max 3 levels), and handle timeouts with warnings.
user-invocable: false
---

# Resource Manager Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Enforce resource limits, manage FIFO queues, enforce depth limits, and handle team timeouts

**Used By**: Team Orchestration SKILL, Team Coordinators

---

## Overview

The Resource Manager Skill enforces resource constraints for the team orchestration framework to prevent runaway resource consumption and ensure predictable execution. It manages agent and team limits, queues excess requests, enforces depth limits, and handles timeouts.

This skill is critical for:
- **Safety**: Preventing infinite recursion and resource exhaustion
- **Fairness**: FIFO queuing ensures requests are processed in order
- **Reliability**: Timeouts prevent indefinitely running teams
- **Scalability**: Tested up to 25 concurrent agents (5 teams × 5 agents)

### Key Principles

1. **Limits are Hard Constraints**: Cannot be exceeded, excess requests are queued
2. **FIFO Ordering**: Queue operations maintain strict first-in-first-out order
3. **Automatic Dequeue**: Completed agents trigger automatic spawning of queued agents
4. **Non-Blocking**: Resource checks never block execution, returns None when queued
5. **Layer-Based Reprioritization**: Queue order can be adjusted at the layer level (e.g., unit vs integration tests) while preserving FIFO within each layer, provided no file-write conflicts exist between layers

---

## Resource Limits (REQ-F-7, REQ-F-8, REQ-F-4, REQ-F-9)

### Agent Limit per Team
- **Limit**: Max 5 agents per team (configurable, REQ-F-7)
- **Behavior**: When limit reached, new spawn requests are queued in FIFO order
- **Override**: Team definition can specify `max_agents` (1-25)

### Team Limit (Global)
- **Limit**: Max 5 concurrent teams (configurable, REQ-F-8)
- **Behavior**: When limit reached, new team requests are queued in FIFO order
- **Override**: Global config can adjust (tested up to 25 concurrent agents total)

### Depth Limit
- **Limit**: Max 3 levels (coordinator → team agent → sub-agent, REQ-F-4)
- **Behavior**: Spawn requests at depth > 3 are rejected with error
- **Rationale**: Prevents infinite recursion, bounds resource consumption

### Timeout
- **Limit**: Default 30 minutes per team (configurable, REQ-F-9)
- **Warning**: Logs warning at 5 minutes remaining
- **Behavior**: Team execution aborted at timeout with telemetry event

---

## Skill Interface

### Input: spawn_agent()

```yaml
team_id: string                # Team this agent belongs to
agent_spec:
  agent_type: string           # Path to agent definition
  task_description: string     # Human-readable task description
  max_retries: integer         # Max retry attempts (default: 3)
parent_id: string              # ID of parent agent (coordinator)
depth: integer                 # Nesting level (1-3)
max_agents: integer            # Max parallel agents for this team (from team definition)
```

### Output: spawn_agent()

```yaml
# Success case (spawned immediately)
agent_id: string               # Unique agent identifier (for Task tool spawn)
queued: false                  # Agent was spawned, not queued

# Queued case (limit reached)
agent_id: null                 # NOT spawned yet
queued: true                   # Agent added to FIFO queue
queue_position: integer        # Position in queue (1 = next to spawn)
queue_depth: integer           # Total agents in queue

# Error case (depth limit exceeded)
agent_id: null
queued: false
error:
  reason: string               # "depth_limit_exceeded"
  message: string              # Human-readable error
  requested_depth: integer     # Depth that was requested
  max_depth: integer           # Maximum allowed depth (3)
```

### Input: on_agent_complete()

```yaml
team_id: string                # Team the completed agent belonged to
agent_id: string               # Agent that completed
```

### Output: on_agent_complete()

```yaml
dequeued_agent:
  agent_id: string | null      # Newly spawned agent ID (null if queue empty)
  agent_spec: dict | null      # Agent spec that was dequeued
  queued: false
queue_status:
  active_agents: integer       # Agents currently running for this team
  queued_agents: integer       # Agents still in queue
  max_agents: integer          # Max allowed agents
```

### Input: spawn_team()

```yaml
team_spec:
  team_id: string              # Unique team identifier
  team_name: string            # Team name
  coordinator: string          # Path to coordinator
  timeout_minutes: integer     # Execution timeout (default: 30)
```

### Output: spawn_team()

```yaml
# Success case (spawned immediately)
team_id: string                # Team identifier
queued: false                  # Team started, not queued
timeout_at: timestamp          # ISO 8601 UTC timestamp when team times out

# Queued case (limit reached)
team_id: null                  # NOT started yet
queued: true                   # Team added to FIFO queue
queue_position: integer        # Position in queue
queue_depth: integer           # Total teams in queue
```

### Input: enforce_timeout()

```yaml
team_id: string                # Team to check timeout for
active_agent_context: list     # Optional: current task context for each active agent
  - agent_id: string           # Agent ID
    current_task: string       # What the agent is currently doing (e.g., "Documenting AccountService.route.ts")
```

### Output: enforce_timeout()

```yaml
timeout_status:
  elapsed_seconds: float       # Time elapsed since team start
  timeout_seconds: float       # Configured timeout threshold
  remaining_seconds: float     # Time remaining (negative if timed out)
  timed_out: boolean           # Whether team has exceeded timeout
  warning_sent: boolean        # Whether 5-minute warning was sent
  active_tasks_at_timeout: list  # What each agent was doing when timeout occurred (only populated when timed_out=true)
    - agent_id: string
      current_task: string       # Human-readable description of interrupted work
```

### Input: reprioritize_queue()

```yaml
team_id: string                # Team whose queue to reprioritize
priority_order: list[string]   # Layer names in desired priority order (e.g., ["integration", "unit"])
                               # Agents in the queue are reordered so that agents matching
                               # earlier layers appear first, preserving FIFO within each layer
```

### Output: reprioritize_queue()

```yaml
success: boolean               # Whether reprioritization succeeded
reordered_count: integer       # Number of agents whose position changed
queue_snapshot: list[dict]     # New queue order (agent_type + layer for each)
error: string | null           # Error if failed (e.g., file conflict detected)
```

---

## Data Structures

### Resource State

```python
class ResourceManager:
    def __init__(self):
        # Agent tracking per team
        self.active_agents = {}       # {team_id: [agent_id, agent_id, ...]}
        self.agent_queue = {}         # {team_id: [agent_spec, agent_spec, ...]}
        self.agent_limits = {}        # {team_id: max_agents}

        # Team tracking (global)
        self.active_teams = []        # [team_id, team_id, ...]
        self.team_queue = []          # [team_spec, team_spec, ...]
        self.team_start_times = {}    # {team_id: timestamp}
        self.team_timeouts = {}       # {team_id: timeout_minutes}
        self.timeout_warnings = set() # {team_id, ...} (warnings sent)

        # Depth tracking
        self.depth_tracker = {}       # {agent_id: depth_level}

        # Configuration
        self.max_concurrent_teams = 5 # Global team limit
        self.max_depth = 3            # Maximum nesting depth

        # Thread safety
        import threading
        self.lock = threading.Lock()
```

---

## Implementation Algorithms

### spawn_agent() - Agent Spawn with Limit Enforcement

```python
def spawn_agent(
    team_id: str,
    agent_spec: dict,
    parent_id: str,
    depth: int,
    max_agents: int
) -> dict:
    """
    Spawn agent if limit allows, otherwise queue in FIFO order.

    Returns None as agent_id when queued (signals to coordinator
    that agent was not spawned immediately).

    Args:
        team_id: Team this agent belongs to
        agent_spec: Agent specification
        parent_id: ID of parent agent
        depth: Nesting level (1-3)
        max_agents: Max parallel agents for this team

    Returns:
        dict with agent_id (or None if queued), queued flag, queue status
    """
    with self.lock:
        # STEP 1: Enforce depth limit (REQ-F-4)
        if depth > self.max_depth:
            log_telemetry('resource', team_id, 'depth_limit_exceeded', {
                'requested_depth': depth,
                'max_depth': self.max_depth,
                'parent_id': parent_id,
                'agent_type': agent_spec['agent_type']
            })

            return {
                'agent_id': None,
                'queued': False,
                'error': {
                    'reason': 'depth_limit_exceeded',
                    'message': (
                        f"Cannot spawn agent at depth {depth}. "
                        f"Max depth is {self.max_depth}. "
                        f"Please redesign team to avoid deep nesting."
                    ),
                    'requested_depth': depth,
                    'max_depth': self.max_depth
                }
            }

        # STEP 2: Initialize team tracking if first agent
        if team_id not in self.active_agents:
            self.active_agents[team_id] = []
            self.agent_queue[team_id] = []
            self.agent_limits[team_id] = max_agents

        # STEP 3: Check agent limit (REQ-F-7)
        active_count = len(self.active_agents[team_id])

        if active_count < max_agents:
            # SPAWN IMMEDIATELY
            # Generate unique agent ID
            agent_id = generate_agent_id(
                agent_spec['agent_type'],
                team_id,
                agent_spec.get('retry_count', 0)
            )

            # Add to active list
            self.active_agents[team_id].append(agent_id)
            self.depth_tracker[agent_id] = depth

            # Store agent limit for this team
            self.agent_limits[team_id] = max_agents

            # Log to telemetry
            log_telemetry('resource', team_id, 'agent_spawned', {
                'agent_id': agent_id,
                'agent_type': agent_spec['agent_type'],
                'active_agents': active_count + 1,
                'max_agents': max_agents,
                'depth': depth,
                'parent_id': parent_id
            })

            return {
                'agent_id': agent_id,
                'queued': False
            }

        else:
            # QUEUE (FIFO) - REQ-F-10
            # Store full agent spec for later spawn
            queued_spec = {
                'agent_spec': agent_spec,
                'parent_id': parent_id,
                'depth': depth
            }

            self.agent_queue[team_id].append(queued_spec)
            queue_depth = len(self.agent_queue[team_id])

            # Log to telemetry
            log_telemetry('resource', team_id, 'agent_queued', {
                'agent_type': agent_spec['agent_type'],
                'active_agents': active_count,
                'queued_agents': queue_depth,
                'max_agents': max_agents,
                'queue_position': queue_depth
            })

            # Return None for agent_id (signals queued, not spawned)
            return {
                'agent_id': None,  # IMPORTANT: None = not spawned
                'queued': True,
                'queue_position': queue_depth,
                'queue_depth': queue_depth
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

### on_agent_complete() - Automatic Dequeue

```python
def on_agent_complete(team_id: str, agent_id: str) -> dict:
    """
    Handle agent completion and automatically spawn next queued agent.

    This implements the automatic dequeue logic (REQ-F-10).

    Args:
        team_id: Team the completed agent belonged to
        agent_id: Agent that completed

    Returns:
        dict with dequeued_agent info and queue status
    """
    with self.lock:
        # STEP 1: Remove from active list
        if team_id in self.active_agents:
            if agent_id in self.active_agents[team_id]:
                self.active_agents[team_id].remove(agent_id)

        # Remove from depth tracker
        if agent_id in self.depth_tracker:
            del self.depth_tracker[agent_id]

        # STEP 2: Check queue - spawn next agent if any (FIFO)
        if team_id in self.agent_queue and self.agent_queue[team_id]:
            # Dequeue next agent (FIFO)
            queued_spec = self.agent_queue[team_id].pop(0)  # FIFO: pop(0)

            agent_spec = queued_spec['agent_spec']
            parent_id = queued_spec['parent_id']
            depth = queued_spec['depth']

            # Generate new agent ID
            new_agent_id = generate_agent_id(
                agent_spec['agent_type'],
                team_id,
                agent_spec.get('retry_count', 0)
            )

            # Add to active list
            self.active_agents[team_id].append(new_agent_id)
            self.depth_tracker[new_agent_id] = depth

            # Log to telemetry
            log_telemetry('resource', team_id, 'agent_dequeued', {
                'agent_id': new_agent_id,
                'agent_type': agent_spec['agent_type'],
                'active_agents': len(self.active_agents[team_id]),
                'queued_agents': len(self.agent_queue[team_id]),
                'max_agents': self.agent_limits.get(team_id, 5)
            })

            return {
                'dequeued_agent': {
                    'agent_id': new_agent_id,
                    'agent_spec': agent_spec,
                    'parent_id': parent_id,
                    'depth': depth,
                    'queued': False
                },
                'queue_status': {
                    'active_agents': len(self.active_agents[team_id]),
                    'queued_agents': len(self.agent_queue[team_id]),
                    'max_agents': self.agent_limits.get(team_id, 5)
                }
            }

        else:
            # No queued agents
            return {
                'dequeued_agent': {
                    'agent_id': None,
                    'agent_spec': None,
                    'queued': False
                },
                'queue_status': {
                    'active_agents': len(self.active_agents.get(team_id, [])),
                    'queued_agents': 0,
                    'max_agents': self.agent_limits.get(team_id, 5)
                }
            }
```

---

### spawn_team() - Team Spawn with Limit Enforcement

```python
def spawn_team(team_spec: dict) -> dict:
    """
    Spawn team if limit allows, otherwise queue in FIFO order.

    Args:
        team_spec: Team specification with team_id, team_name, coordinator, timeout_minutes

    Returns:
        dict with team_id (or None if queued), queued flag, queue status
    """
    with self.lock:
        team_id = team_spec['team_id']
        team_name = team_spec.get('team_name', team_id)
        timeout_minutes = team_spec.get('timeout_minutes', 30)

        # STEP 1: Check team limit (REQ-F-8)
        if len(self.active_teams) < self.max_concurrent_teams:
            # SPAWN IMMEDIATELY
            self.active_teams.append(team_id)

            # Track start time and timeout
            import datetime
            self.team_start_times[team_id] = datetime.datetime.utcnow()
            self.team_timeouts[team_id] = timeout_minutes

            # Calculate timeout timestamp
            timeout_at = self.team_start_times[team_id] + datetime.timedelta(minutes=timeout_minutes)

            # Log to telemetry
            log_telemetry('resource', team_id, 'team_spawned', {
                'team_name': team_name,
                'active_teams': len(self.active_teams),
                'max_teams': self.max_concurrent_teams,
                'timeout_minutes': timeout_minutes,
                'timeout_at': timeout_at.isoformat()
            })

            return {
                'team_id': team_id,
                'queued': False,
                'timeout_at': timeout_at.isoformat()
            }

        else:
            # QUEUE (FIFO) - REQ-F-10
            self.team_queue.append(team_spec)
            queue_depth = len(self.team_queue)

            # Log to telemetry
            log_telemetry('resource', 'global', 'team_queued', {
                'team_id': team_id,
                'team_name': team_name,
                'active_teams': len(self.active_teams),
                'queued_teams': queue_depth,
                'max_teams': self.max_concurrent_teams,
                'queue_position': queue_depth
            })

            return {
                'team_id': None,  # NOT started yet
                'queued': True,
                'queue_position': queue_depth,
                'queue_depth': queue_depth
            }


def on_team_complete(team_id: str) -> dict:
    """
    Handle team completion and automatically spawn next queued team.

    Args:
        team_id: Team that completed

    Returns:
        dict with dequeued_team info and queue status
    """
    with self.lock:
        # STEP 1: Remove from active list
        if team_id in self.active_teams:
            self.active_teams.remove(team_id)

        # Clean up tracking data
        if team_id in self.team_start_times:
            del self.team_start_times[team_id]
        if team_id in self.team_timeouts:
            del self.team_timeouts[team_id]
        if team_id in self.timeout_warnings:
            self.timeout_warnings.remove(team_id)

        # Clean up agent tracking
        if team_id in self.active_agents:
            del self.active_agents[team_id]
        if team_id in self.agent_queue:
            del self.agent_queue[team_id]
        if team_id in self.agent_limits:
            del self.agent_limits[team_id]

        # STEP 2: Check queue - spawn next team if any (FIFO)
        if self.team_queue:
            # Dequeue next team (FIFO)
            next_team_spec = self.team_queue.pop(0)  # FIFO: pop(0)

            # Spawn team recursively
            result = self.spawn_team(next_team_spec)

            log_telemetry('resource', 'global', 'team_dequeued', {
                'team_id': result.get('team_id'),
                'team_name': next_team_spec.get('team_name'),
                'active_teams': len(self.active_teams),
                'queued_teams': len(self.team_queue),
                'max_teams': self.max_concurrent_teams
            })

            return {
                'dequeued_team': result,
                'queue_status': {
                    'active_teams': len(self.active_teams),
                    'queued_teams': len(self.team_queue),
                    'max_teams': self.max_concurrent_teams
                }
            }

        else:
            # No queued teams
            return {
                'dequeued_team': None,
                'queue_status': {
                    'active_teams': len(self.active_teams),
                    'queued_teams': 0,
                    'max_teams': self.max_concurrent_teams
                }
            }
```

---

### enforce_timeout() - Timeout Enforcement with Warnings

```python
def enforce_timeout(team_id: str, active_agent_context: list = None) -> dict:
    """
    Check if team has exceeded timeout, send warning at 5 minutes remaining.

    This should be called periodically (every 10 seconds) by the coordinator.

    Args:
        team_id: Team to check timeout for
        active_agent_context: Optional list of dicts with agent_id and current_task
            describing what each active agent is currently doing.
            Example: [{"agent_id": "write-agent-1", "current_task": "Documenting AccountService.route.ts"}]

    Returns:
        dict with timeout status (includes active_tasks_at_timeout when timed_out=True)
    """
    with self.lock:
        # Check if team is tracked
        if team_id not in self.team_start_times:
            return {
                'timeout_status': {
                    'elapsed_seconds': 0.0,
                    'timeout_seconds': 0.0,
                    'remaining_seconds': 0.0,
                    'timed_out': False,
                    'warning_sent': False,
                    'active_tasks_at_timeout': [],
                    'error': f"Team not found: {team_id}"
                }
            }

        # Calculate elapsed time
        import datetime
        start_time = self.team_start_times[team_id]
        current_time = datetime.datetime.utcnow()
        elapsed = (current_time - start_time).total_seconds()

        # Get timeout threshold
        timeout_minutes = self.team_timeouts.get(team_id, 30)
        timeout_seconds = timeout_minutes * 60
        remaining = timeout_seconds - elapsed

        # Normalize active_agent_context
        agent_context = active_agent_context or []

        # Check if warning should be sent (5 minutes = 300 seconds)
        warning_threshold = 300
        warning_sent = team_id in self.timeout_warnings

        if remaining <= warning_threshold and remaining > 0 and not warning_sent:
            # Send warning with active task context
            self.timeout_warnings.add(team_id)

            log_telemetry('resource', team_id, 'timeout_warning', {
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout_seconds,
                'remaining_seconds': remaining,
                'warning_threshold_seconds': warning_threshold,
                'active_agent_context': agent_context
            })

            warning_sent = True

        # Check if timed out
        timed_out = elapsed >= timeout_seconds

        # Build active_tasks_at_timeout (only populated when timed_out=True)
        active_tasks_at_timeout = []
        if timed_out and agent_context:
            active_tasks_at_timeout = [
                {
                    'agent_id': ctx['agent_id'],
                    'current_task': ctx['current_task']
                }
                for ctx in agent_context
            ]

            # Format human-readable summary
            task_descriptions = [
                f"{ctx['agent_id']} was {ctx['current_task'].lower()}"
                if not ctx['current_task'][0].islower()
                else f"{ctx['agent_id']} was {ctx['current_task']}"
                for ctx in agent_context
            ]
            timeout_summary = f"Team timed out. Active agents: {', '.join(task_descriptions)}"

            log_telemetry('resource', team_id, 'timeout', {
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout_seconds,
                'aborted': True,
                'active_tasks_at_timeout': active_tasks_at_timeout,
                'summary': timeout_summary
            })
        elif timed_out:
            log_telemetry('resource', team_id, 'timeout', {
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout_seconds,
                'aborted': True,
                'active_tasks_at_timeout': []
            })

        return {
            'timeout_status': {
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout_seconds,
                'remaining_seconds': remaining,
                'timed_out': timed_out,
                'warning_sent': warning_sent,
                'active_tasks_at_timeout': active_tasks_at_timeout
            }
        }
```

---

### reprioritize_queue() - Layer-Based Queue Reprioritization

```python
def reprioritize_queue(team_id: str, priority_order: list[str]) -> dict:
    """
    Reorder the agent queue by layer priority while preserving FIFO within each layer.

    Layers are derived from agent_spec['layer'] if present, otherwise inferred
    from agent_spec['task_description']. Agents in higher-priority layers
    (earlier in priority_order) are moved to the front of the queue.

    SAFETY CONSTRAINT: Reprioritization is rejected if agents in different
    layers would write to the same file, preventing file-write conflicts.
    This check uses agent_spec['target_files'] (list of file paths) when
    available. Two agents in the SAME layer may share target files (they
    run sequentially via FIFO within that layer), but agents in DIFFERENT
    layers whose execution order changes must not share target files.

    Args:
        team_id: Team whose queue to reprioritize
        priority_order: Layer names in desired priority order
                        (e.g., ["integration", "unit"])

    Returns:
        dict with success, reordered_count, queue_snapshot, error
    """
    with self.lock:
        # STEP 1: Validate team exists and has a queue
        if team_id not in self.agent_queue or not self.agent_queue[team_id]:
            return {
                'success': False,
                'reordered_count': 0,
                'queue_snapshot': [],
                'error': f"No queued agents for team: {team_id}"
            }

        queue = self.agent_queue[team_id]

        # STEP 2: Group queued agents by layer
        # Layer is derived from agent_spec['layer'] if present,
        # otherwise from agent_spec['task_description']
        layer_groups = {}  # {layer_name: [queued_spec, ...]}
        for queued_spec in queue:
            agent_spec = queued_spec['agent_spec']
            layer = agent_spec.get(
                'layer',
                _infer_layer(agent_spec.get('task_description', ''))
            )
            if layer not in layer_groups:
                layer_groups[layer] = []
            layer_groups[layer].append(queued_spec)

        # STEP 3: Check for file-write conflicts between layers
        # Collect target files per layer
        layer_files = {}  # {layer_name: set(file_paths)}
        for layer, specs in layer_groups.items():
            files = set()
            for queued_spec in specs:
                target_files = queued_spec['agent_spec'].get('target_files', [])
                files.update(target_files)
            layer_files[layer] = files

        # Check for overlapping files between any two different layers.
        # If agents in different layers write to the same file,
        # reordering could cause conflicts (one agent overwrites another's
        # output). This is the core safety constraint from PR #87.
        layer_names = list(layer_files.keys())
        for i in range(len(layer_names)):
            for j in range(i + 1, len(layer_names)):
                layer_a = layer_names[i]
                layer_b = layer_names[j]
                overlap = layer_files[layer_a] & layer_files[layer_b]
                if overlap:
                    conflict_msg = (
                        f"File-write conflict detected between layers "
                        f"'{layer_a}' and '{layer_b}': "
                        f"{sorted(overlap)}. "
                        f"Reprioritization rejected to prevent concurrent "
                        f"writes to the same file."
                    )

                    log_telemetry('resource', team_id, 'reprioritize_rejected', {
                        'reason': 'file_conflict',
                        'layer_a': layer_a,
                        'layer_b': layer_b,
                        'conflicting_files': sorted(overlap),
                        'priority_order': priority_order
                    })

                    return {
                        'success': False,
                        'reordered_count': 0,
                        'queue_snapshot': [],
                        'error': conflict_msg
                    }

        # STEP 4: Reorder queue by layer priority
        # Agents from layers listed earlier in priority_order come first.
        # Within each layer, original FIFO order is preserved (the
        # layer_groups dict maintains insertion order from the original
        # queue scan, so intra-layer FIFO is guaranteed).
        # Agents whose layer is not in priority_order are appended at
        # the end in their original FIFO order.
        old_order = list(queue)  # snapshot before reorder
        new_queue = []

        # First: add agents from layers in priority_order
        for layer in priority_order:
            if layer in layer_groups:
                new_queue.extend(layer_groups[layer])

        # Then: add agents from layers NOT in priority_order (preserve FIFO)
        for layer in layer_groups:
            if layer not in priority_order:
                new_queue.extend(layer_groups[layer])

        # STEP 5: Count how many agents changed position
        reordered_count = 0
        for idx, spec in enumerate(new_queue):
            if idx < len(old_order) and spec is not old_order[idx]:
                reordered_count += 1

        # STEP 6: Apply new queue order
        self.agent_queue[team_id] = new_queue

        # STEP 7: Build queue snapshot for response
        queue_snapshot = []
        for queued_spec in new_queue:
            agent_spec = queued_spec['agent_spec']
            layer = agent_spec.get(
                'layer',
                _infer_layer(agent_spec.get('task_description', ''))
            )
            queue_snapshot.append({
                'agent_type': agent_spec['agent_type'],
                'layer': layer
            })

        # STEP 8: Log telemetry
        log_telemetry('resource', team_id, 'queue_reprioritized', {
            'priority_order': priority_order,
            'reordered_count': reordered_count,
            'queue_size': len(new_queue),
            'layers_found': list(layer_groups.keys())
        })

        return {
            'success': True,
            'reordered_count': reordered_count,
            'queue_snapshot': queue_snapshot,
            'error': None
        }


def _infer_layer(task_description: str) -> str:
    """
    Infer layer name from task description when agent_spec['layer'] is not set.

    Simple heuristic: looks for common layer keywords in the description.

    Args:
        task_description: Human-readable task description

    Returns:
        Inferred layer name (e.g., "unit", "integration") or "default"
    """
    description_lower = task_description.lower()
    if 'integration' in description_lower:
        return 'integration'
    elif 'unit' in description_lower:
        return 'unit'
    elif 'e2e' in description_lower or 'end-to-end' in description_lower:
        return 'e2e'
    elif 'lint' in description_lower:
        return 'lint'
    else:
        return 'default'
```

---

## Integration with Agent Lifecycle Manager

The Resource Manager integrates with the Agent Lifecycle Manager for state tracking:

```markdown
# In Team Coordinator

## Phase 1: Check Resources Before Spawn

1. Read skills/team-orchestration/resource-manager.md
2. Call spawn_agent(team_id, agent_spec, parent_id, depth, max_agents)
3. Check result:
   - If agent_id is NOT None: Agent spawned successfully
     - Call agent-lifecycle-manager.spawn_agent() to track state
     - Use Task tool to actually spawn agent with agent_id
   - If agent_id is None AND queued is True: Agent queued
     - Do NOT use Task tool yet (agent not spawned)
     - Agent will be spawned automatically when slot available
   - If error exists: Depth limit exceeded
     - Abort spawning, handle error per team config

## Phase 2: Handle Agent Completion

1. When agent completes (via agent-lifecycle-manager.mark_completed())
2. Call resource-manager.on_agent_complete(team_id, agent_id)
3. Check result.dequeued_agent:
   - If dequeued_agent.agent_id is NOT None: Queued agent was spawned
     - Call agent-lifecycle-manager.spawn_agent() to track state
     - Use Task tool to spawn the dequeued agent
     - Continue monitoring
   - If dequeued_agent.agent_id is None: Queue empty
     - No action needed

## Phase 3: Monitor Timeout

Background monitoring loop (every 10 seconds):
1. Call resource-manager.enforce_timeout(team_id)
2. Check timeout_status:
   - If warning_sent: Display warning to user ("5 minutes remaining")
   - If timed_out: Abort team execution
     - Mark all active agents as failed (via agent-lifecycle-manager)
     - Clean up resources
     - Return timeout error to user
```

---

## FIFO Queue Guarantees

### Agent Queue

**Guarantee**: Agents are spawned in the exact order they were queued

**Implementation**:
```python
# Enqueue (append to end)
self.agent_queue[team_id].append(agent_spec)

# Dequeue (pop from front)
next_agent = self.agent_queue[team_id].pop(0)  # FIFO: index 0
```

**Example**:
```
Initial state: active=[A, B, C, D, E] (max 5), queue=[]

Request spawn F → queue=[F]
Request spawn G → queue=[F, G]
Request spawn H → queue=[F, G, H]

Agent C completes:
- Remove C from active: active=[A, B, D, E]
- Dequeue F (front of queue): queue=[G, H]
- Spawn F: active=[A, B, D, E, F]

Agent A completes:
- Remove A from active: active=[B, D, E, F]
- Dequeue G (front of queue): queue=[H]
- Spawn G: active=[B, D, E, F, G]

Agent B completes:
- Remove B from active: active=[D, E, F, G]
- Dequeue H (front of queue): queue=[]
- Spawn H: active=[D, E, F, G, H]
```

### Reprioritization and FIFO

**Note**: The `reprioritize_queue()` method can reorder agents **between** layers (e.g., moving all "integration" agents ahead of "unit" agents), but it **preserves FIFO order within each layer**. If agents A1, A2, A3 are all in the "unit" layer, their relative order is never changed by reprioritization. This ensures that reprioritization is a coarse-grained operation (layer-level) and does not violate the per-layer ordering guarantee. Reprioritization is rejected entirely if it would cause file-write conflicts between layers.

### Team Queue

**Guarantee**: Teams are started in the exact order they were queued

**Implementation**: Same FIFO logic as agent queue

---

## Depth Limit Enforcement

### 3-Level Hierarchy

```
Level 1: User command (/team-run testing-parallel)
         ↓
Level 2: Coordinator (testing-parallel-coordinator)
         ↓
Level 3: Specialist agents (write-agent-1, write-agent-2, ...)
         ↓
Level 4: PROHIBITED ❌ (depth_limit_exceeded error)
```

### Rejection Logic

```python
if depth > 3:
    return {
        'agent_id': None,
        'queued': False,
        'error': {
            'reason': 'depth_limit_exceeded',
            'message': 'Cannot spawn agent at depth 4. Max depth is 3.'
        }
    }
```

### Why Depth Limit Exists

- Prevents infinite recursion (coordinator spawning coordinator spawning coordinator...)
- Bounds resource consumption (each level multiplies potential agents)
- Ensures predictable execution time

---

## Timeout Handling

### Timeout Workflow

```
Team starts → Start timer (timeout = 30 minutes)
    ↓
Every 10 seconds: Check elapsed time
    ↓
At 25 minutes (5 minutes remaining):
    - Log timeout_warning event
    - Display warning to user: "Team will timeout in 5 minutes"
    - Mark warning_sent = True
    ↓
At 30 minutes (timeout reached):
    - Log timeout event with active task context
    - Include per-agent description of interrupted work
    - Abort team execution:
      - Mark all active agents as failed
      - Clean up resources
      - Return timeout error
    ↓
Team completes or times out → Clean up tracking data
```

### Configurable Timeout

```yaml
# In team definition frontmatter
timeout_minutes: 30  # Default
```

```bash
# Override via CLI
/team-run testing-parallel --timeout=60  # 60 minutes
```

---

## Thread Safety

All methods use a global lock to ensure thread-safe operations:

```python
with self.lock:
    # All state mutations within lock
    self.active_agents[team_id].append(agent_id)
    self.agent_queue[team_id].append(agent_spec)
```

**Critical Regions**:
- Agent spawn/completion tracking
- Queue operations (enqueue/dequeue)
- Team spawn/completion tracking
- Timeout tracking updates

---

## Usage Example

```markdown
# In Team Coordinator

## Spawn Multiple Agents with Queuing

# Load resource manager
resource_mgr = load_resource_manager()

# Attempt to spawn 10 agents (max_agents = 5)
agent_ids = []
for i in range(10):
    agent_spec = {
        'agent_type': 'agents/write-agent.md',
        'task_description': f'Generate tests for batch {i}',
        'retry_count': 0
    }

    result = resource_mgr.spawn_agent(
        team_id='testing-parallel',
        agent_spec=agent_spec,
        parent_id='coordinator-id',
        depth=2,
        max_agents=5
    )

    if result['queued']:
        # Agent queued, NOT spawned yet
        print(f"Agent {i} queued at position {result['queue_position']}")
    elif result['agent_id']:
        # Agent spawned successfully
        agent_ids.append(result['agent_id'])

        # Actually spawn via Task tool
        spawn_agent_via_task_tool(result['agent_id'], agent_spec)

        # Track state
        lifecycle_mgr.spawn_agent(agent_spec, 'coordinator-id', 'testing-parallel', 2)

# Expected: 5 agents spawned, 5 queued

## Handle Completion with Automatic Dequeue

# When agent completes
def on_agent_finished(agent_id):
    # Mark as completed in lifecycle manager
    lifecycle_mgr.mark_completed(agent_id, output, summary)

    # Notify resource manager (triggers dequeue)
    result = resource_mgr.on_agent_complete('testing-parallel', agent_id)

    if result['dequeued_agent']['agent_id']:
        # Queued agent was automatically spawned
        dequeued_id = result['dequeued_agent']['agent_id']
        dequeued_spec = result['dequeued_agent']['agent_spec']

        print(f"Auto-spawned queued agent: {dequeued_id}")

        # Actually spawn via Task tool
        spawn_agent_via_task_tool(dequeued_id, dequeued_spec)

        # Track state
        lifecycle_mgr.spawn_agent(
            dequeued_spec,
            result['dequeued_agent']['parent_id'],
            'testing-parallel',
            result['dequeued_agent']['depth']
        )
```

---

## Testing Checklist

For TASK-003 acceptance:

### Agent Limits (REQ-F-7)
- [ ] Enforces max 5 agents per team (or team-configured limit)
- [ ] Spawns agents immediately when under limit
- [ ] Queues agents when limit reached
- [ ] Returns agent_id when spawned, None when queued
- [ ] Stores full agent spec in queue for later spawn

### FIFO Queue (REQ-F-10)
- [ ] Enqueues agents in FIFO order (append to end)
- [ ] Dequeues agents in FIFO order (pop from front)
- [ ] Maintains queue order across multiple enqueue/dequeue operations
- [ ] Auto-spawns queued agents when active agents complete

### Team Limits (REQ-F-8)
- [ ] Enforces max 5 concurrent teams (global limit)
- [ ] Spawns teams immediately when under limit
- [ ] Queues teams when limit reached
- [ ] Auto-starts queued teams when active teams complete

### Depth Limit (REQ-F-4)
- [ ] Enforces max 3 levels (coordinator → team → agents)
- [ ] Rejects spawn requests at depth > 3
- [ ] Returns error with reason and requested depth
- [ ] Logs depth_limit_exceeded telemetry event

### Timeout (REQ-F-9)
- [ ] Tracks team start time
- [ ] Configures timeout per team (default 30 minutes)
- [ ] Logs warning at 5 minutes remaining
- [ ] Only sends warning once per team
- [ ] Detects timeout when elapsed >= timeout threshold
- [ ] Logs timeout telemetry event when timed out
- [ ] Captures active agent task context at timeout
- [ ] Includes human-readable task descriptions in timeout telemetry
- [ ] Includes active task context in 5-minute warning telemetry

### Integration
- [ ] Integrates with agent-lifecycle-manager for state tracking
- [ ] Returns None when agent queued (not spawned immediately)
- [ ] Generates unique agent_id with team_id and retry_count
- [ ] Thread-safe operations (all mutations within lock)
- [ ] Cleans up tracking data on team completion

### Queue Reprioritization
- [ ] Reprioritizes queue by layer when no file conflicts exist
- [ ] Preserves FIFO order within each layer after reprioritization
- [ ] Rejects reprioritization when agents in different layers share target files
- [ ] Returns error message identifying conflicting files and layers
- [ ] Returns queue_snapshot reflecting new order after successful reprioritization
- [ ] Handles agents with no explicit layer (infers from task_description)
- [ ] Appends agents from unlisted layers at end of queue (preserving their FIFO)
- [ ] Logs queue_reprioritized telemetry event on success
- [ ] Logs reprioritize_rejected telemetry event on file conflict
- [ ] Returns error when team has no queued agents

### Telemetry Events
- [ ] Logs agent_spawned event when agent spawned
- [ ] Logs agent_queued event when agent queued
- [ ] Logs agent_dequeued event when queued agent spawned
- [ ] Logs team_spawned event when team started
- [ ] Logs team_queued event when team queued
- [ ] Logs team_dequeued event when queued team started
- [ ] Logs timeout_warning event at 5 minutes remaining
- [ ] Logs timeout event when team times out
- [ ] Logs depth_limit_exceeded event when depth > 3

---

## Error Scenarios

### Scenario 1: Depth Limit Exceeded

```
User → /team-run testing-parallel
       ↓ (depth 1)
testing-coordinator spawns write-agent
       ↓ (depth 2)
write-agent attempts to spawn sub-coordinator
       ↓ (depth 3)
sub-coordinator attempts to spawn sub-agent
       ↓ (depth 4) ❌ REJECTED

Error returned:
{
  'agent_id': None,
  'queued': False,
  'error': {
    'reason': 'depth_limit_exceeded',
    'message': 'Cannot spawn agent at depth 4. Max depth is 3.',
    'requested_depth': 4,
    'max_depth': 3
  }
}

Telemetry:
[timestamp] | resource | testing-parallel | depth_limit_exceeded | {"requested_depth":4,"max_depth":3}
```

### Scenario 2: Timeout with Warning

```
Team starts at 14:30:00 (timeout = 30 minutes)
Active agents: write-agent-1 (documenting AccountService.route.ts),
               analyze-agent-2 (analyzing UserService.ts)

At 14:55:00 (25 minutes elapsed, 5 minutes remaining):
- enforce_timeout() called with active_agent_context:
    [{"agent_id": "write-agent-1", "current_task": "Documenting AccountService.route.ts"},
     {"agent_id": "analyze-agent-2", "current_task": "Analyzing UserService.ts"}]
- enforce_timeout() returns warning_sent = True
- Telemetry: timeout_warning event with active_agent_context
- User sees: "Team will timeout in 5 minutes"

At 15:00:00 (30 minutes elapsed):
- enforce_timeout() returns timed_out = True
- Telemetry: timeout event with active_tasks: ["write-agent-1 was documenting AccountService.route.ts", "analyze-agent-2 was analyzing UserService.ts"]
- Coordinator aborts team execution
- All active agents marked as failed
- User sees: "Team timed out. Active agents: write-agent-1 was documenting AccountService.route.ts, analyze-agent-2 was analyzing UserService.ts"
```

---

## References

- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-4, REQ-F-7, REQ-F-8, REQ-F-9, REQ-F-10)
- **Plan**: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Resource Management Strategy)
- **Related Skills**:
  - `skills/team-orchestration/agent-lifecycle-manager.md` (tracks agent state)
  - `skills/team-orchestration/team-loader.md` (loads team definitions with limits)
  - `skills/telemetry/SKILL.md` (logs resource events)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-003)
