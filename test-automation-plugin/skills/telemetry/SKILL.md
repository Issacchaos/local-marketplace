---
name: telemetry
description: Structured event logging for agent team orchestration with non-blocking writes to .claude/telemetry-[timestamp].log
user-invocable: false
---

# Telemetry Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Non-blocking structured event logging for agent team observability

**Used By**: Team Orchestration SKILL, team coordinators, specialist agents

---

## Overview

The Telemetry Skill provides comprehensive observability into agent team orchestration through structured event logging. It captures agent lifecycle, coordination decisions, progress metrics, test execution, and resource utilization in machine-parseable log files. Telemetry is opt-in by default and designed to be completely non-blocking - failures NEVER halt execution.

### Key Features

1. **Five Event Types** (REQ-F-23 to REQ-F-27):
   - **Lifecycle**: Agent spawn, start, completion, failure
   - **Coordination**: Plan proposals, approvals, task assignments
   - **Progress**: Intermediate updates, milestones
   - **Test**: Test execution start, completion, results
   - **Resource**: Queue status, timeouts, limits, token usage

2. **Non-Blocking Design** (REQ-NF-6):
   - All operations wrapped in try/except
   - Failures log warning but never halt execution
   - Silent no-op when disabled (opt-in)

3. **Real-Time Logging** (REQ-NF-3):
   - Events logged within 1 second of occurrence
   - No buffering or batching
   - Append-only writes for immediate visibility

4. **Opt-In Configuration** (REQ-F-22):
   - Disabled by default
   - Enabled via environment variable, config file, or team definition
   - User controls telemetry at multiple levels

---

## Entry Point Function

### log_telemetry()

**Function Signature**:
```python
def log_telemetry(event_type: str, agent_id: str, status: str, metadata: dict,
                  project_root: str, team_name: str = None) -> dict
```

**Parameters**:
- `event_type` (string): Event type - one of: `lifecycle`, `coordination`, `progress`, `test`, `resource`
- `agent_id` (string): Unique agent identifier (e.g., `write-agent-1`, `testing-coordinator`)
- `status` (string): Event-specific status (e.g., `spawned`, `completed`, `plan_approved`)
- `metadata` (dict): Event-specific metadata (see event-types.md for schemas)
- `project_root` (string): Absolute path to project root
- `team_name` (string, optional): Team name for log file initialization

**Returns**:
```python
{
  "success": boolean,           # Always True (even if write failed)
  "log_file": string | None,    # Path to log file (if write succeeded)
  "warning": string | None      # Warning message (if write failed)
}
```

**Guarantees**:
- **Never raises exceptions**: All errors caught and logged as warnings
- **Always returns success**: Even on failure, returns `success: True` to prevent halting execution
- **Non-blocking**: Returns quickly (< 10ms typical, < 1 second guaranteed per REQ-NF-3)

---

## Usage Examples

### Example 1: Lifecycle Event - Agent Spawned

```python
# Coordinator spawns write-agent
agent_id = "write-agent-1"
parent_id = "testing-coordinator"
depth = 2

# Log telemetry
log_telemetry(
    event_type="lifecycle",
    agent_id=agent_id,
    status="spawned",
    metadata={
        "parent": parent_id,
        "depth": depth,
        "agent_type": "agents/write-agent.md",
        "team_id": "testing-parallel"
    },
    project_root=project_root,
    team_name="testing-parallel"
)

# Continue execution (telemetry failure doesn't halt)
```

**Logged Event**:
```
2026-02-13T14:30:16.000Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2,"agent_type":"agents/write-agent.md","team_id":"testing-parallel"}
```

---

### Example 2: Coordination Event - Plan Proposed

```python
# Coordinator proposes execution plan
plan_summary = "3 parallel write-agents for 12 test targets"
batches = 3
total_targets = 12

# Log telemetry
log_telemetry(
    event_type="coordination",
    agent_id="testing-coordinator",
    status="plan_proposed",
    metadata={
        "plan_summary": plan_summary,
        "batches": batches,
        "total_targets": total_targets,
        "approval_required": True
    },
    project_root=project_root,
    team_name="testing-parallel"
)

# Present plan to user (telemetry logged before approval gate)
```

**Logged Event**:
```
2026-02-13T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"3 parallel write-agents for 12 test targets","batches":3,"total_targets":12,"approval_required":true}
```

---

### Example 3: Progress Event - Agent Update

```python
# Write-agent reports intermediate progress
tests_written = 2
current_file = "test_user_service.py"
percent_complete = 40

# Log telemetry
log_telemetry(
    event_type="progress",
    agent_id="write-agent-1",
    status="update",
    metadata={
        "tests_written": tests_written,
        "current_file": current_file,
        "percent_complete": percent_complete
    },
    project_root=project_root
)

# Continue writing tests (telemetry is background activity)
```

**Logged Event**:
```
2026-02-13T14:30:20.000Z | progress | write-agent-1 | update | {"tests_written":2,"current_file":"test_user_service.py","percent_complete":40}
```

---

### Example 4: Test Event - Execution Complete

```python
# Execute-agent finishes running tests
passed = 12
failed = 3
skipped = 0
duration_seconds = 8.5

# Log telemetry
log_telemetry(
    event_type="test",
    agent_id="execute-agent",
    status="execution_complete",
    metadata={
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": duration_seconds,
        "pass_rate": passed / (passed + failed)
    },
    project_root=project_root
)

# Continue with validation phase
```

**Logged Event**:
```
2026-02-13T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":12,"failed":3,"skipped":0,"duration_seconds":8.5,"pass_rate":0.8}
```

---

### Example 5: Resource Event - Queue Status

```python
# Resource manager updates queue status
active_agents = 5
queued_agents = 2
max_agents = 5

# Log telemetry
log_telemetry(
    event_type="resource",
    agent_id="testing-coordinator",
    status="queue_status",
    metadata={
        "active_agents": active_agents,
        "queued_agents": queued_agents,
        "max_agents": max_agents
    },
    project_root=project_root
)

# Continue spawning agents from queue
```

**Logged Event**:
```
2026-02-13T14:31:05.789Z | resource | testing-coordinator | queue_status | {"active_agents":5,"queued_agents":2,"max_agents":5}
```

---

### Example 6: Resource Event - Token Usage (REQ-F-27a)

```python
# Agent completes and reports token usage
agent_id = "write-agent-1"
input_tokens = 1500
output_tokens = 800
cache_read_tokens = 500
cache_write_tokens = 200

# Log telemetry
log_telemetry(
    event_type="resource",
    agent_id=agent_id,
    status="token_usage",
    metadata={
        "agent_id": agent_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "model": "sonnet"
    },
    project_root=project_root
)

# Continue with next agent
```

**Logged Event**:
```
2026-02-13T14:30:30.000Z | resource | write-agent-1 | token_usage | {"agent_id":"write-agent-1","input_tokens":1500,"output_tokens":800,"total_tokens":2300,"cache_read_tokens":500,"cache_write_tokens":200,"model":"sonnet"}
```

---

## Configuration

### Enabling Telemetry (REQ-F-22)

Telemetry is **disabled by default**. Users must opt-in using one of these methods:

**Method 1: Environment Variable**
```bash
# Enable telemetry
export DANTE_TELEMETRY=1

# Run command with telemetry
/team-run testing-parallel src/
```

**Method 2: Configuration File**
```json
// .claude/dante-config.json
{
  "telemetry_enabled": true
}
```

**Method 3: Team Definition Override**
```yaml
# teams/testing-parallel.md
---
telemetry_enabled: true
# ... other team fields
---
```

**Configuration Precedence** (highest to lowest):
1. Team definition frontmatter (`telemetry_enabled: true`)
2. Environment variable (`DANTE_TELEMETRY=1`)
3. Configuration file (`.claude/dante-config.json`)
4. Default (disabled)

---

### Log File Location (REQ-F-21)

**Path**: `{project_root}/.claude/telemetry-{timestamp}.log`

**Timestamp Format**: `YYYY-MM-DDTHH-MM-SS` (ISO 8601 with dashes for Windows compatibility)

**Example**:
```
D:/dev/dante_plugin/.claude/telemetry-2026-02-13T14-30-00.log
```

**Session-Based Logging**:
- One log file per session (cached in memory)
- All events for a session go to same file
- New session = new log file with new timestamp

---

## Implementation Details

### Sub-Skills

This skill is composed of two sub-skills:

1. **event-types.md** (REQ-F-23 to REQ-F-27, REQ-F-27a):
   - Defines schemas for all 5 event types
   - Specifies metadata fields for each status
   - Provides formatting guidelines and examples

2. **log-writer.md** (REQ-F-21, REQ-F-22, REQ-NF-3, REQ-NF-6):
   - Implements non-blocking write logic
   - Handles opt-in configuration
   - Manages log rotation (10MB threshold)
   - Ensures append-only writes without file locking

---

### Event Formatting (REQ-F-28)

**Format**:
```
[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
```

**Implementation**:
```python
def log_telemetry(event_type: str, agent_id: str, status: str, metadata: dict,
                  project_root: str, team_name: str = None) -> dict:
    """
    Log telemetry event with structured format.

    This is the main entry point for all telemetry logging.
    """
    try:
        # Check if telemetry is enabled
        if not is_telemetry_enabled():
            # Silent no-op if disabled
            return {'success': True, 'log_file': None, 'warning': None}

        # Generate timestamp (ISO 8601 UTC with milliseconds)
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')

        # Serialize metadata to JSON
        metadata_json = json.dumps(metadata, separators=(',', ':'))

        # Format event (pipe-delimited)
        event = f"{timestamp} | {event_type} | {agent_id} | {status} | {metadata_json}"

        # Write event to log file (non-blocking)
        result = write_telemetry_event(event, project_root, team_name)

        return result

    except Exception as e:
        # CRITICAL: Never raise exception from telemetry
        warning_msg = f"Telemetry logging failed (non-critical): {e}"
        log_warning(warning_msg)
        return {'success': True, 'log_file': None, 'warning': warning_msg}
```

---

### Non-Blocking Guarantee (REQ-NF-6)

**All telemetry operations are non-blocking**:

```python
# Example: Coordinator spawns agent with telemetry
try:
    # Spawn agent
    agent_id = spawn_agent_via_task_tool(agent_spec)

    # Log lifecycle event (non-blocking)
    log_telemetry(
        event_type="lifecycle",
        agent_id=agent_id,
        status="spawned",
        metadata={"parent": parent_id, "depth": depth},
        project_root=project_root
    )
    # Note: We don't check result - telemetry failure doesn't affect execution

    # Continue with coordination logic
    assign_task_to_agent(agent_id, task)

except Exception as e:
    # If spawning fails, handle that error
    # But telemetry errors are already caught and logged internally
    handle_spawn_failure(e)
```

**Key Principle**: **Telemetry is observability, not control flow**. Execution proceeds regardless of telemetry success/failure.

---

## Coordinator Integration

### When to Log Events

**Lifecycle Events**:
- `spawned`: When agent is created and registered
- `start`: When agent begins execution
- `completed`: When agent successfully finishes
- `failed`: When agent fails after retries

**Coordination Events**:
- `plan_proposed`: Before approval gate (show plan to user)
- `plan_approved`/`plan_rejected`: After user decision
- `task_assigned`: When coordinator assigns task to agent
- `dependencies_resolved`: When agent's dependencies complete

**Progress Events**:
- `update`: Periodically during long-running tasks (e.g., every 5 tests)
- `milestone_reached`: At significant milestones (e.g., all parallel agents complete)

**Test Events**:
- `execution_start`: When execute-agent starts running tests
- `execution_complete`: When all tests finish

**Resource Events**:
- `queue_status`: When agents spawn/complete (queue changes)
- `timeout_warning`: 5 minutes before timeout
- `timeout`: When timeout exceeded
- `limit_reached`: When agent/team limit hit
- `token_usage`: When agent completes (if token data available)

---

### Event Sequence Template

**Complete Workflow** (testing-parallel team):

```
1. Coordinator spawned          → lifecycle | testing-coordinator | spawned
2. Plan proposed                → coordination | testing-coordinator | plan_proposed
3. User approves                → coordination | testing-coordinator | plan_approved
4. Agent 1 spawned              → lifecycle | write-agent-1 | spawned
5. Agent 2 spawned              → lifecycle | write-agent-2 | spawned
6. Agent 3 spawned              → lifecycle | write-agent-3 | spawned
7. Parallel execution starts    → coordination | testing-coordinator | parallel_execution_start
8. Agent 1 progress update      → progress | write-agent-1 | update
9. Agent 1 completes            → lifecycle | write-agent-1 | completed
10. Agent 1 token usage         → resource | write-agent-1 | token_usage
11. Agent 2 completes           → lifecycle | write-agent-2 | completed
12. Agent 2 token usage         → resource | write-agent-2 | token_usage
13. Agent 3 completes           → lifecycle | write-agent-3 | completed
14. Agent 3 token usage         → resource | write-agent-3 | token_usage
15. Parallel execution complete → coordination | testing-coordinator | parallel_execution_complete
16. Execute agent spawned       → lifecycle | execute-agent | spawned
17. Test execution starts       → test | execute-agent | execution_start
18. Test execution complete     → test | execute-agent | execution_complete
19. Execute agent completes     → lifecycle | execute-agent | completed
20. Coordinator completes       → lifecycle | testing-coordinator | completed
```

---

## Error Handling

### Pattern 1: Silent No-Op When Disabled

```python
# If telemetry disabled, log_telemetry() returns immediately
result = log_telemetry(...)
# No warning, no error - just silent no-op
```

---

### Pattern 2: Warning on Write Failure

```python
# If telemetry write fails, warning is logged but execution continues
result = log_telemetry(...)
if result['warning']:
    # Warning was logged internally, coordinator can optionally check it
    log_debug(f"Telemetry warning: {result['warning']}")
# Execution continues regardless
```

---

### Pattern 3: Never Halt Execution

```python
# Telemetry NEVER raises exceptions
try:
    log_telemetry(...)
except Exception:
    # This will never happen - log_telemetry() catches all exceptions internally
    pass
```

---

## Testing Checklist

For TASK-006 acceptance:

**Event Schema** (event-types.md):
- [ ] Defines 5 event types: lifecycle, coordination, progress, test, resource (REQ-F-23 to REQ-F-27)
- [ ] Each event type has clear status values
- [ ] Metadata schemas defined for all statuses
- [ ] Event format matches REQ-F-28: `[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]`
- [ ] Token usage event includes all REQ-F-27a fields (input_tokens, output_tokens, total_tokens, cache_read/write)

**Log Writer** (log-writer.md):
- [ ] Writes to `.claude/telemetry-[timestamp].log` in project root (REQ-F-21)
- [ ] Opt-in via DANTE_TELEMETRY=1 environment variable (REQ-F-22)
- [ ] Opt-in via config file `.claude/dante-config.json` (REQ-F-22)
- [ ] Team definition can override telemetry setting (REQ-F-22)
- [ ] Non-blocking: try/except wrapper catches all exceptions (REQ-NF-6)
- [ ] Failures log warning but never halt execution (REQ-NF-6)
- [ ] Append-only writes (no file locking)
- [ ] Log rotation when file exceeds 10MB
- [ ] Events logged within 1 second of occurrence (REQ-NF-3)

**Entry Point** (SKILL.md):
- [ ] log_telemetry() function defined with clear signature
- [ ] Function never raises exceptions (REQ-NF-6)
- [ ] Function always returns success=True (REQ-NF-6)
- [ ] Usage examples cover all 5 event types
- [ ] Configuration options documented (REQ-F-22)
- [ ] User-invocable: false in frontmatter
- [ ] Integration patterns documented for coordinators

---

## Example Log Output

**File**: `.claude/telemetry-2026-02-13T14-30-00.log`

```
# Dante Team Orchestration Telemetry Log
# Generated: 2026-02-13T14:30:00.000Z
# Team: testing-parallel
# Telemetry Version: 1.0.0
# Format: [timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
---
2026-02-13T14:30:01.123Z | lifecycle | testing-coordinator | spawned | {"parent":"test-loop-orchestrator","depth":1,"team_id":"testing-parallel"}
2026-02-13T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"3 parallel write-agents","batches":3,"approval_required":true}
2026-02-13T14:30:15.789Z | coordination | testing-coordinator | plan_approved | {"user_response":"approve","batches":3}
2026-02-13T14:30:16.000Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:16.100Z | lifecycle | write-agent-2 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:16.200Z | lifecycle | write-agent-3 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:16.300Z | coordination | testing-coordinator | parallel_execution_start | {"active_agents":3,"max_agents":5}
2026-02-13T14:30:20.000Z | progress | write-agent-1 | update | {"tests_written":2,"percent_complete":40}
2026-02-13T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":13.7,"tests_generated":5}
2026-02-13T14:30:30.100Z | resource | write-agent-1 | token_usage | {"agent_id":"write-agent-1","input_tokens":1500,"output_tokens":800,"total_tokens":2300,"model":"sonnet"}
2026-02-13T14:30:35.000Z | lifecycle | write-agent-2 | completed | {"duration_seconds":18.9,"tests_generated":6}
2026-02-13T14:30:35.100Z | resource | write-agent-2 | token_usage | {"agent_id":"write-agent-2","input_tokens":1600,"output_tokens":900,"total_tokens":2500,"model":"sonnet"}
2026-02-13T14:30:32.000Z | lifecycle | write-agent-3 | completed | {"duration_seconds":15.8,"tests_generated":4}
2026-02-13T14:30:32.100Z | resource | write-agent-3 | token_usage | {"agent_id":"write-agent-3","input_tokens":1400,"output_tokens":700,"total_tokens":2100,"model":"sonnet"}
2026-02-13T14:30:35.500Z | coordination | testing-coordinator | parallel_execution_complete | {"total_tests":15,"successful_agents":3,"failed_agents":0}
2026-02-13T14:30:40.000Z | test | execute-agent | execution_start | {"framework":"pytest","test_count":15}
2026-02-13T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":15,"failed":0,"skipped":0,"duration_seconds":8.5}
2026-02-13T14:30:49.500Z | lifecycle | testing-coordinator | completed | {"duration_seconds":48.4}
```

---

## References

- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md`
  - REQ-F-21 to REQ-F-28 (Telemetry requirements)
  - REQ-F-27a (Token usage metrics)
  - REQ-NF-3 (< 1 second latency)
  - REQ-NF-6 (Non-blocking reliability)

- **Plan**: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md`
  - Telemetry Implementation Details
  - Event Schema definitions
  - Non-blocking design patterns

- **Sub-Skills**:
  - `skills/telemetry/event-types.md` (Event schemas)
  - `skills/telemetry/log-writer.md` (Write implementation)

- **Pattern**: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-006)
