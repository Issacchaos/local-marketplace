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

1. **Fourteen Event Types** (REQ-F-23 to REQ-F-27):
   - **Lifecycle**: Agent spawn, start, completion, failure
   - **Coordination**: Plan proposals, approvals, task assignments
   - **Progress**: Intermediate updates, milestones
   - **Test**: Suite discovery, per-test-case start/result, fixture setup/teardown, coverage reports, stdout/stderr capture, flaky test retries, execution summaries
   - **Resource**: Queue status, timeouts, limits, token usage
   - **Config**: Team definition loading, override resolution, model selection
   - **Agent I/O**: Full prompt/output capture, file operations
   - **Dependency**: Graph construction, phase planning, resolution tracking
   - **Approval**: Gate interactions, user responses, plan modifications
   - **Timing**: Phase transitions, queue wait times, backoff delays, overhead summaries
   - **Error**: Validation checks, state transitions, retry decisions, error classification
   - **Cost**: Memory snapshots, cumulative cost tracking, model fallbacks, utilization curves
   - **Data Flow**: Inter-phase data passing, file conflict checks, plan diffs, agent messages
   - **Environment**: Session start/end, platform info, git state, plugin version

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

5. **Real-Time Delivery Channels**:
   - **File**: Append-only log (always active when telemetry enabled)
   - **Console**: Compact, color-coded live terminal output (`TEAMSTERS_TELEMETRY_CONSOLE=1`)
   - **Webhook**: HTTP POST streaming to external systems (`TEAMSTERS_TELEMETRY_WEBHOOK=url`)

---

## Entry Point Function

### log_telemetry()

**Function Signature**:
```python
def log_telemetry(event_type: str, agent_id: str, status: str, metadata: dict,
                  project_root: str, team_name: str = None) -> dict
```

**Parameters**:
- `event_type` (string): Event type - one of: `lifecycle`, `coordination`, `progress`, `test`, `resource`, `config`, `dependency`, `agent_io`, `approval`, `timing`, `error`, `cost`, `data_flow`, `environment`
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

### Example 7: Config Event - Team Definition Loaded

```python
log_telemetry(
    event_type="config",
    agent_id="testing-coordinator",
    status="config_loaded",
    metadata={
        "team_name": "testing-parallel",
        "file_path": "teams/testing-parallel.md",
        "frontmatter_raw": {
            "name": "testing-parallel",
            "coordinator": "teams/testing-parallel-coordinator.md",
            "max_agents": 5,
            "timeout_minutes": 30,
            "approval_gates": {"before_execution": True, "after_completion": False}
        },
        "file_size_bytes": 2048,
        "parse_duration_ms": 12
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

### Example 8: Dependency Event - Graph Constructed

```python
log_telemetry(
    event_type="dependency",
    agent_id="testing-coordinator",
    status="graph_constructed",
    metadata={
        "adjacency_list": {
            "analyze-agent": [],
            "write-agent-1": ["analyze-agent"],
            "write-agent-2": ["analyze-agent"],
            "execute-agent": ["write-agent-1", "write-agent-2"]
        },
        "topological_order": ["analyze-agent", "write-agent-1", "write-agent-2", "execute-agent"],
        "total_nodes": 4,
        "total_edges": 4,
        "has_cycles": False
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

### Example 9: Agent I/O Event - Prompt Constructed

```python
log_telemetry(
    event_type="agent_io",
    agent_id="write-agent-1",
    status="prompt_constructed",
    metadata={
        "agent_id": "write-agent-1",
        "prompt_text": "You are write-agent-1 in the testing-parallel team...",
        "prompt_length_chars": 4500,
        "prompt_estimated_tokens": 1200,
        "model": "sonnet",
        "includes_context": True
    },
    project_root=project_root
)
```

---

### Example 10: Approval Event - User Response Received

```python
log_telemetry(
    event_type="approval",
    agent_id="testing-coordinator",
    status="user_response_received",
    metadata={
        "gate_type": "before_execution",
        "decision": "modify",
        "feedback_text": "Reduce to 2 parallel agents instead of 3",
        "response_time_seconds": 8.5,
        "iteration": 1
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

### Example 11: Timing Event - Phase Transition

```python
log_telemetry(
    event_type="timing",
    agent_id="testing-coordinator",
    status="phase_transition",
    metadata={
        "from_phase": 1,
        "to_phase": 2,
        "transition_duration_seconds": 0.45,
        "idle_time_seconds": 0.12,
        "overhead_description": "Dependency resolution and agent prompt construction"
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

### Example 12: Error Event - Error Classified

```python
log_telemetry(
    event_type="error",
    agent_id="write-agent-2",
    status="error_classified",
    metadata={
        "agent_id": "write-agent-2",
        "error_category": "timeout",
        "raw_error": "Agent exceeded 120s timeout while generating tests for src/complex_service.py",
        "classified_severity": "retriable",
        "suggested_action": "Retry with increased timeout or simpler prompt",
        "stack_trace": None
    },
    project_root=project_root
)
```

---

### Example 13: Cost Event - Cumulative Cost

```python
log_telemetry(
    event_type="cost",
    agent_id="testing-coordinator",
    status="cumulative_cost",
    metadata={
        "team_id": "testing-parallel",
        "total_input_tokens": 15000,
        "total_output_tokens": 8500,
        "total_cache_read_tokens": 3000,
        "total_cache_write_tokens": 1200,
        "estimated_cost_usd": 0.47,
        "cost_by_model": {"sonnet": 0.35, "opus": 0.12},
        "cost_by_agent": {"analyzer": 0.08, "writer-1": 0.15, "writer-2": 0.12, "executor": 0.12},
        "agents_completed": 4,
        "agents_remaining": 0
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

### Example 14: Test Telemetry - Individual Test Result

```python
log_telemetry(
    event_type="test",
    agent_id="execute-agent",
    status="test_case_result",
    metadata={
        "test_name": "test_user_creation_with_valid_email",
        "test_file": "tests/test_user_service.py",
        "status": "passed",
        "duration_seconds": 0.23,
        "failure_message": None,
        "failure_traceback": None,
        "stdout_capture": "",
        "stderr_capture": "",
        "assertions_checked": 3
    },
    project_root=project_root
)
```

---

### Example 15: Environment Event - Session Start

```python
log_telemetry(
    event_type="environment",
    agent_id="testing-coordinator",
    status="session_start",
    metadata={
        "session_id": "sess-20260325T143000-a7f2",
        "plugin_version": "1.0.0",
        "claude_code_version": None,
        "platform": "win32",
        "os_version": "Windows 11 Enterprise 10.0.26100",
        "shell": "bash",
        "working_directory": "D:/dev/my-project",
        "git_branch": "main",
        "git_commit": "abc1234",
        "git_dirty": False,
        "node_version": "v20.11.0",
        "python_version": "3.12.1"
    },
    project_root=project_root,
    team_name="testing-parallel"
)
```

---

## Configuration

### Enabling Telemetry (REQ-F-22)

Telemetry is **disabled by default**. Users must opt-in using one of these methods:

**Method 1: Environment Variable**
```bash
# Enable telemetry
export TEAMSTERS_TELEMETRY=1

# Run command with telemetry
/team-run testing-parallel src/
```

**Method 2: Configuration File**
```json
// .claude/teamsters-config.json
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
2. Environment variable (`TEAMSTERS_TELEMETRY=1`)
3. Configuration file (`.claude/teamsters-config.json`)
4. Default (disabled)

---

### Log File Location (REQ-F-21)

**Path**: `{project_root}/.claude/telemetry-{timestamp}.log`

**Timestamp Format**: `YYYY-MM-DDTHH-MM-SS` (ISO 8601 with dashes for Windows compatibility)

**Example**:
```
D:/dev/teamsters-plugin/.claude/telemetry-2026-02-13T14-30-00.log
```

**Session-Based Logging**:
- One log file per session (cached in memory)
- All events for a session go to same file
- New session = new log file with new timestamp

---

## Real-Time Delivery

The telemetry system supports 3 simultaneous delivery channels. All channels are non-blocking - failures in any channel never halt execution.

### Channel Overview

| Channel | Output | Enable With | Default |
|---------|--------|-------------|---------|
| File | `.claude/telemetry-{timestamp}.log` | `--telemetry` | Active when telemetry enabled |
| Console | Live terminal output | `--telemetry-console` or `TEAMSTERS_TELEMETRY_CONSOLE=1` | Disabled |
| Webhook | HTTP POST to endpoint | `TEAMSTERS_TELEMETRY_WEBHOOK=url` | Disabled |

### Console Output

Compact, color-coded event stream displayed in the terminal during execution.

**Enable**:
```bash
# CLI flag
/team-run my-team --telemetry-console

# Environment variable
export TEAMSTERS_TELEMETRY_CONSOLE=1

# Team definition
telemetry_console: true
```

**Format**: `[HH:MM:SS] EVENT_TYPE  agent_id       status     summary`

**Example**:
```
[14:30:00] ENV        coordinator    session    platform=win32 branch=main
[14:30:01] CONFIG     coordinator    loaded     my-team (teams/my-team.md)
[14:30:01] DEPEND     coordinator    graph      2 nodes, 1 edge, no cycles
[14:30:10] APPROVAL   coordinator    approved   before_execution (8.6s)
[14:30:10] LIFECYCLE  analyzer       spawned    Explore, depth=2
[14:30:25] LIFECYCLE  analyzer       completed  14.9s
[14:30:25] COST       coordinator    running    $0.008 (1/2 agents)
[14:30:45] LIFECYCLE  writer         completed  19.5s
[14:30:45] TIMING     coordinator    overhead   44.7s wall, 34.4s work, 23% tax
[14:30:45] ENV        coordinator    session    completed, $0.019 total
```

Color coding: lifecycle=green/red/yellow, timing=cyan, error=red, cost=magenta, test=blue, environment=gray.

### Webhook Streaming

Stream events as JSON to any HTTP endpoint.

**Enable**:
```bash
# Basic
export TEAMSTERS_TELEMETRY_WEBHOOK=http://localhost:8080/events

# With authentication
export TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN=my-api-key

# Batch mode (buffer 10 events per POST)
export TEAMSTERS_TELEMETRY_WEBHOOK_BATCH=10
```

**JSON payload** (single event):
```json
{
  "timestamp": "2026-03-25T14:30:25.100Z",
  "event_type": "lifecycle",
  "agent_id": "analyzer",
  "status": "completed",
  "team_name": "my-team",
  "session_id": "sess-my-team-20260325",
  "metadata": { "duration_seconds": 14.9, "model_used": "sonnet" }
}
```

**Custom headers**:
```
Content-Type: application/json
X-Teamsters-Event: lifecycle
X-Teamsters-Status: completed
X-Teamsters-Team: my-team
X-Teamsters-Session: sess-my-team-20260325
Authorization: Bearer {token}
```

**Compatible with**: Any JSON POST endpoint, Grafana Loki, Datadog, Elasticsearch, custom receivers.

### Live File Tailing

Watch the telemetry log file in a second terminal while execution runs:

```bash
# Unix/macOS
tail -f .claude/telemetry-*.log

# Windows PowerShell
Get-Content .claude\telemetry-*.log -Wait -Tail 0

# Pretty-print JSON metadata with jq
tail -f .claude/telemetry-*.log | while read line; do
  echo "$line" | sed 's/.*| //' | jq '.' 2>/dev/null || echo "$line"
done

# Filter specific event types
tail -f .claude/telemetry-*.log | grep "lifecycle\|error\|cost"

# Filter by agent
tail -f .claude/telemetry-*.log | grep "write-agent-1"
```

### Combining Channels

For maximum observability, enable all 3 channels:

```bash
export TEAMSTERS_TELEMETRY_CONSOLE=1
export TEAMSTERS_TELEMETRY_WEBHOOK=http://localhost:8080/events
/team-run my-team --telemetry
```

This gives you:
- **Console**: Live activity feed in your terminal
- **File**: Complete structured log for post-analysis
- **Webhook**: Stream to dashboards, alerting, or external storage

---

## Implementation Details

### Sub-Skills

This skill is composed of two sub-skills:

1. **event-types.md** (REQ-F-23 to REQ-F-27, REQ-F-27a):
   - Defines schemas for all 14 event types
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

**Config Events**:
- `config_loaded`: When team definition parsed from disk
- `config_override_applied`: When CLI/env/config override changes a value
- `config_defaults_applied`: When defaults fill missing fields
- `model_resolved`: When model selected for each agent

**Dependency Events**:
- `graph_constructed`: When dependency DAG built
- `phase_planned`: When execution phase computed
- `dependency_waiting`: When agent blocked on dependency
- `dependency_satisfied`: When dependency edge resolved

**Agent I/O Events**:
- `prompt_constructed`: When agent prompt built
- `output_received`: When agent returns output
- `output_parsed`: When structured data extracted
- `file_written`: When agent creates/modifies file
- `file_read`: When agent reads file

**Approval Events**:
- `gate_entered`: When approval checkpoint reached
- `prompt_displayed`: When approval prompt shown
- `user_response_received`: When user responds
- `plan_regenerated`: When plan modified from feedback

**Timing Events**:
- `phase_transition`: When execution moves between phases
- `queue_wait_time`: When queued agent is finally spawned
- `backoff_wait`: During retry backoff delays
- `overhead_summary`: At end of team execution

**Error Events**:
- `validation_check`: During team definition validation (each check)
- `state_transition`: On every agent state change
- `retry_decision`: When deciding whether to retry a failed agent
- `error_classified`: When categorizing an error

**Cost Events**:
- `memory_snapshot`: At agent spawn and completion
- `cumulative_cost`: After each agent completes
- `model_fallback`: When model fails and falls back
- `utilization_snapshot`: Periodically during execution

**Data Flow Events**:
- `data_passed`: When output flows between phases
- `file_conflict_check`: During queue reprioritization
- `plan_diff`: When user modifies plan
- `agent_message`: On peer-to-peer agent communication

**Environment Events**:
- `session_start`: At team execution start
- `environment_snapshot`: After initialization
- `session_end`: At team execution end

---

### Event Sequence Template

**Complete Workflow** (testing-parallel team):

```
1.  Session start                -> environment | testing-coordinator | session_start
2.  Environment snapshot         -> environment | testing-coordinator | environment_snapshot
3.  Config loaded                -> config | testing-coordinator | config_loaded
4.  Config defaults applied      -> config | testing-coordinator | config_defaults_applied
5.  Validation check (schema)    -> error | testing-coordinator | validation_check
6.  Validation check (agents)    -> error | testing-coordinator | validation_check
7.  Model resolved               -> config | testing-coordinator | model_resolved
8.  Coordinator spawned          -> lifecycle | testing-coordinator | spawned
9.  Coordinator state: idle      -> error | testing-coordinator | state_transition
10. Memory snapshot (spawn)      -> cost | testing-coordinator | memory_snapshot
11. Plan proposed                -> coordination | testing-coordinator | plan_proposed
12. Approval gate entered        -> approval | testing-coordinator | gate_entered
13. Approval prompt displayed    -> approval | testing-coordinator | prompt_displayed
14. User approves                -> approval | testing-coordinator | user_response_received
15. Plan approved                -> coordination | testing-coordinator | plan_approved
16. Dependency graph constructed -> dependency | testing-coordinator | graph_constructed
17. Execution phase 1 planned    -> dependency | testing-coordinator | phase_planned
18. Execution phase 2 planned    -> dependency | testing-coordinator | phase_planned
19. Phase transition (0 -> 1)    -> timing | testing-coordinator | phase_transition
20. Agent 1 spawned              -> lifecycle | write-agent-1 | spawned
21. Agent 1 state: running       -> error | write-agent-1 | state_transition
22. Agent 1 memory snapshot      -> cost | write-agent-1 | memory_snapshot
23. Agent 1 prompt constructed   -> agent_io | write-agent-1 | prompt_constructed
24. Agent 2 spawned              -> lifecycle | write-agent-2 | spawned
25. Agent 2 state: running       -> error | write-agent-2 | state_transition
26. Agent 2 memory snapshot      -> cost | write-agent-2 | memory_snapshot
27. Agent 2 prompt constructed   -> agent_io | write-agent-2 | prompt_constructed
28. Agent 3 spawned              -> lifecycle | write-agent-3 | spawned
29. Agent 3 state: running       -> error | write-agent-3 | state_transition
30. Agent 3 memory snapshot      -> cost | write-agent-3 | memory_snapshot
31. Agent 3 prompt constructed   -> agent_io | write-agent-3 | prompt_constructed
32. Queue status update          -> resource | testing-coordinator | queue_status
33. Parallel execution starts    -> coordination | testing-coordinator | parallel_execution_start
34. Utilization snapshot         -> cost | testing-coordinator | utilization_snapshot
35. Agent 1 progress update      -> progress | write-agent-1 | update
36. Agent 1 output received      -> agent_io | write-agent-1 | output_received
37. Agent 1 file written         -> agent_io | write-agent-1 | file_written
38. Agent 1 state: completed     -> error | write-agent-1 | state_transition
39. Agent 1 completes            -> lifecycle | write-agent-1 | completed
40. Agent 1 token usage          -> resource | write-agent-1 | token_usage
41. Agent 1 memory snapshot      -> cost | write-agent-1 | memory_snapshot
42. Cumulative cost update       -> cost | testing-coordinator | cumulative_cost
43. Dependency satisfied          -> dependency | testing-coordinator | dependency_satisfied
44. Data passed (agent 1 output) -> data_flow | testing-coordinator | data_passed
45. File conflict check          -> data_flow | testing-coordinator | file_conflict_check
46. Agent 2 progress update      -> progress | write-agent-2 | update
47. Agent 2 output received      -> agent_io | write-agent-2 | output_received
48. Agent 2 state: completed     -> error | write-agent-2 | state_transition
49. Agent 2 completes            -> lifecycle | write-agent-2 | completed
50. Agent 2 token usage          -> resource | write-agent-2 | token_usage
51. Agent 2 memory snapshot      -> cost | write-agent-2 | memory_snapshot
52. Cumulative cost update       -> cost | testing-coordinator | cumulative_cost
53. Agent 3 output received      -> agent_io | write-agent-3 | output_received
54. Agent 3 state: completed     -> error | write-agent-3 | state_transition
55. Agent 3 completes            -> lifecycle | write-agent-3 | completed
56. Agent 3 token usage          -> resource | write-agent-3 | token_usage
57. Agent 3 memory snapshot      -> cost | write-agent-3 | memory_snapshot
58. Cumulative cost update       -> cost | testing-coordinator | cumulative_cost
59. Parallel execution complete  -> coordination | testing-coordinator | parallel_execution_complete
60. Phase transition (1 -> 2)    -> timing | testing-coordinator | phase_transition
61. Execute agent spawned        -> lifecycle | execute-agent | spawned
62. Execute agent state: running -> error | execute-agent | state_transition
63. Execute agent memory snapshot-> cost | execute-agent | memory_snapshot
64. Execute agent prompt built   -> agent_io | execute-agent | prompt_constructed
65. Data passed (phase 1 output) -> data_flow | testing-coordinator | data_passed
66. Test execution starts        -> test | execute-agent | execution_start
67. Test case result (test 1)    -> test | execute-agent | test_case_result
68. Test case result (test 2)    -> test | execute-agent | test_case_result
69. Test case result (test 3)    -> test | execute-agent | test_case_result
70. Test case result (test 4)    -> test | execute-agent | test_case_result
71. Test case result (test 5)    -> test | execute-agent | test_case_result
72. Test progress update         -> progress | execute-agent | update
73. Test case result (test 6)    -> test | execute-agent | test_case_result
74. Test case result (test 7)    -> test | execute-agent | test_case_result
75. Test case result (test 8)    -> test | execute-agent | test_case_result
76. Test case result (test 9)    -> test | execute-agent | test_case_result
77. Test case result (test 10)   -> test | execute-agent | test_case_result
78. Test case result (test 11)   -> test | execute-agent | test_case_result
79. Test case result (test 12)   -> test | execute-agent | test_case_result
80. Test case result (test 13)   -> test | execute-agent | test_case_result
81. Test case result (test 14)   -> test | execute-agent | test_case_result
82. Test case result (test 15)   -> test | execute-agent | test_case_result
83. Test execution complete      -> test | execute-agent | execution_complete
84. Execute agent output         -> agent_io | execute-agent | output_received
85. Execute agent state: done    -> error | execute-agent | state_transition
86. Execute agent completes      -> lifecycle | execute-agent | completed
87. Execute agent token usage    -> resource | execute-agent | token_usage
88. Execute agent memory snapshot-> cost | execute-agent | memory_snapshot
89. Cumulative cost (final)      -> cost | testing-coordinator | cumulative_cost
90. Overhead summary             -> timing | testing-coordinator | overhead_summary
91. Coordinator state: completed -> error | testing-coordinator | state_transition
92. Coordinator completes        -> lifecycle | testing-coordinator | completed
93. Session end                  -> environment | testing-coordinator | session_end
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
- [ ] Defines 14 event types: lifecycle, coordination, progress, test, resource, config, dependency, agent_io, approval, timing, error, cost, data_flow, environment (REQ-F-23 to REQ-F-27)
- [ ] Each event type has clear status values
- [ ] Metadata schemas defined for all statuses
- [ ] Event format matches REQ-F-28: `[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]`
- [ ] Token usage event includes all REQ-F-27a fields (input_tokens, output_tokens, total_tokens, cache_read/write)

**Log Writer** (log-writer.md):
- [ ] Writes to `.claude/telemetry-[timestamp].log` in project root (REQ-F-21)
- [ ] Opt-in via TEAMSTERS_TELEMETRY=1 environment variable (REQ-F-22)
- [ ] Opt-in via config file `.claude/teamsters-config.json` (REQ-F-22)
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
- [ ] Usage examples cover all 14 event types
- [ ] Configuration options documented (REQ-F-22)
- [ ] User-invocable: false in frontmatter
- [ ] Integration patterns documented for coordinators

---

## Example Log Output

**File**: `.claude/telemetry-2026-02-13T14-30-00.log`

```
# Teamsters Team Orchestration Telemetry Log
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
