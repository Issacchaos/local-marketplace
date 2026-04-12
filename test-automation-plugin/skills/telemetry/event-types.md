---
name: event-types
description: Event schema definitions for telemetry logging (lifecycle, coordination, progress, test, resource events)
user-invocable: false
---

# Telemetry Event Types

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Define structured event schemas for team orchestration telemetry logging

**Used By**: Telemetry SKILL, log-writer skill

---

## Overview

This skill defines the complete schema for telemetry events logged during agent team orchestration. All events follow a consistent structure with event-specific metadata fields. These event definitions support real-time observability into agent lifecycle, coordination decisions, progress tracking, test execution, and resource utilization.

### Design Principles

1. **Structured Format**: All events use consistent pipe-delimited format with JSON metadata
2. **Machine-Parseable**: Events can be parsed by standard tools (jq, Python json.loads())
3. **Self-Documenting**: Field names are explicit and descriptive
4. **Extensible**: New metadata fields can be added without breaking parsers
5. **Timestamped**: All events include ISO 8601 UTC timestamps for precise ordering

### Event Format (REQ-F-28)

```
[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
```

**Fields**:
- `timestamp`: ISO 8601 UTC (e.g., `2026-02-12T14:30:01.123Z`)
- `event_type`: One of: `lifecycle`, `coordination`, `progress`, `test`, `resource`
- `agent_id`: Unique agent identifier (e.g., `write-agent-1`, `testing-coordinator`)
- `status`: Event-specific status (e.g., `spawned`, `running`, `completed`, `failed`)
- `metadata_json`: JSON object with event-specific data (must be valid JSON, even if empty `{}`)

---

## Event Type 1: Lifecycle Events (REQ-F-23)

**Purpose**: Track agent lifecycle transitions (spawn → start → complete/fail)

**Status Values**:
- `spawned`: Agent created and registered with coordinator
- `start`: Agent begins execution of assigned task
- `completed`: Agent successfully finished task
- `failed`: Agent encountered unrecoverable error

### Schema: spawned

**When**: Agent is created and registered (before execution starts)

**Metadata Fields**:
```json
{
  "parent": "string",           // Parent coordinator agent ID
  "depth": integer,             // Nesting depth (1-3)
  "agent_type": "string",       // Agent type (path to agent definition)
  "team_id": "string"           // Team this agent belongs to
}
```

**Example**:
```
2026-02-12T14:30:01.123Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2,"agent_type":"agents/write-agent.md","team_id":"testing-parallel"}
```

---

### Schema: start

**When**: Agent begins execution of assigned task

**Metadata Fields**:
```json
{
  "assigned_task": "string",    // Human-readable task description
  "parent": "string"            // Parent coordinator agent ID (optional)
}
```

**Example**:
```
2026-02-12T14:30:01.456Z | lifecycle | write-agent-1 | start | {"assigned_task":"Generate tests for src/user_service.py","parent":"testing-coordinator"}
```

---

### Schema: completed

**When**: Agent successfully finishes task

**Metadata Fields**:
```json
{
  "duration_seconds": float,    // Total execution time
  "output_summary": "string",   // Brief summary of agent output (optional)
  "tests_generated": integer,   // For write-agents: number of tests created (optional)
  "files_processed": integer    // Number of files processed (optional)
}
```

**Example**:
```
2026-02-12T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":28.5,"output_summary":"5 tests generated","tests_generated":5}
```

---

### Schema: failed

**When**: Agent encounters unrecoverable error after retries

**Metadata Fields**:
```json
{
  "reason": "string",           // Error reason (e.g., "timeout", "exception", "validation_failed")
  "retries": integer,           // Number of retry attempts made
  "last_error": "string",       // Last error message (optional)
  "duration_seconds": float     // Time until failure (optional)
}
```

**Example**:
```
2026-02-12T14:32:00.000Z | lifecycle | write-agent-2 | failed | {"reason":"timeout","retries":3,"last_error":"Agent exceeded 120s timeout","duration_seconds":121.5}
```

---

## Event Type 2: Coordination Events (REQ-F-24)

**Purpose**: Track coordinator decisions, task assignments, and team-level actions

**Status Values**:
- `plan_proposed`: Coordinator proposes execution plan (approval gate)
- `plan_approved`: User approves execution plan
- `plan_rejected`: User rejects execution plan
- `plan_modification_requested`: User requests changes to plan
- `task_assigned`: Coordinator assigns task to specialist agent
- `dependencies_resolved`: Agent's dependencies are satisfied, ready to proceed
- `parallel_execution_start`: Multiple agents begin parallel execution
- `parallel_execution_complete`: All parallel agents finished

### Schema: plan_proposed

**When**: Coordinator creates execution plan and presents to user (approval gate)

**Metadata Fields**:
```json
{
  "plan_summary": "string",     // Human-readable plan summary
  "batches": integer,           // Number of parallel batches (optional)
  "total_targets": integer,     // Total items to process (optional)
  "approval_required": boolean  // Whether approval gate is enabled
}
```

**Example**:
```
2026-02-12T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"3 parallel write-agents","batches":3,"total_targets":12,"approval_required":true}
```

---

### Schema: plan_approved

**When**: User approves coordinator's proposed plan

**Metadata Fields**:
```json
{
  "user_response": "approve",   // Fixed value
  "batches": integer,           // Number of batches in approved plan (optional)
  "approval_time_seconds": float // Time user took to approve (optional)
}
```

**Example**:
```
2026-02-12T14:30:15.789Z | coordination | testing-coordinator | plan_approved | {"user_response":"approve","batches":3,"approval_time_seconds":14.3}
```

---

### Schema: plan_rejected

**When**: User rejects coordinator's proposed plan (aborts team execution)

**Metadata Fields**:
```json
{
  "user_response": "reject",    // Fixed value
  "rejection_reason": "string"  // User's reason for rejection (optional)
}
```

**Example**:
```
2026-02-12T14:30:20.000Z | coordination | testing-coordinator | plan_rejected | {"user_response":"reject","rejection_reason":"Too many parallel agents, prefer sequential"}
```

---

### Schema: task_assigned

**When**: Coordinator assigns task to specialist agent

**Metadata Fields**:
```json
{
  "agent": "string",            // Agent ID that received task
  "target": "string",           // Target item/file to process (optional)
  "batch": integer,             // Batch number (optional)
  "targets": [string]           // List of targets for this agent (optional)
}
```

**Example**:
```
2026-02-12T14:30:16.300Z | coordination | testing-coordinator | task_assigned | {"agent":"write-agent-1","target":"src/user_service.py","batch":1,"targets":["src/user_service.py","src/auth/login.py"]}
```

---

### Schema: dependencies_resolved

**When**: Agent's dependencies are satisfied and agent is ready to proceed

**Metadata Fields**:
```json
{
  "agent": "string",            // Agent ID now ready
  "waited_for": [string]        // List of agent IDs this agent was waiting for
}
```

**Example**:
```
2026-02-12T14:30:35.500Z | coordination | testing-coordinator | dependencies_resolved | {"agent":"execute-agent","waited_for":["write-agent-1","write-agent-2","write-agent-3"]}
```

---

### Schema: parallel_execution_start

**When**: Multiple agents begin parallel execution

**Metadata Fields**:
```json
{
  "active_agents": integer,     // Number of agents starting
  "max_agents": integer,        // Maximum allowed agents
  "agent_ids": [string]         // List of agent IDs starting (optional)
}
```

**Example**:
```
2026-02-12T14:30:16.300Z | coordination | testing-coordinator | parallel_execution_start | {"active_agents":3,"max_agents":5,"agent_ids":["write-agent-1","write-agent-2","write-agent-3"]}
```

---

### Schema: parallel_execution_complete

**When**: All parallel agents finished (successful or failed)

**Metadata Fields**:
```json
{
  "total_tests": integer,       // Total items produced (optional)
  "successful_agents": integer, // Number of agents that completed
  "failed_agents": integer,     // Number of agents that failed
  "duration_seconds": float     // Total parallel execution time (optional)
}
```

**Example**:
```
2026-02-12T14:30:35.500Z | coordination | testing-coordinator | parallel_execution_complete | {"total_tests":15,"successful_agents":3,"failed_agents":0,"duration_seconds":19.2}
```

---

## Event Type 3: Progress Events (REQ-F-25)

**Purpose**: Track agent progress during long-running tasks

**Status Values**:
- `update`: Agent reports intermediate progress
- `milestone_reached`: Agent reaches significant milestone

### Schema: update

**When**: Agent reports intermediate progress (periodic updates during execution)

**Metadata Fields**:
```json
{
  "tests_written": integer,     // Number of tests written so far (optional)
  "current_file": "string",     // File currently being processed (optional)
  "percent_complete": integer,  // Estimated completion percentage 0-100 (optional)
  "files_processed": integer,   // Number of files processed (optional)
  "message": "string"           // Human-readable progress message (optional)
}
```

**Example**:
```
2026-02-12T14:30:20.000Z | progress | write-agent-1 | update | {"tests_written":2,"current_file":"test_user_service.py","percent_complete":40}
```

---

### Schema: milestone_reached

**When**: Agent reaches significant milestone (e.g., all parallel agents complete, test suite passes)

**Metadata Fields**:
```json
{
  "milestone": "string",        // Milestone name/description
  "total_tests": integer,       // Total items at milestone (optional)
  "success_count": integer,     // Number of successful items (optional)
  "failure_count": integer      // Number of failed items (optional)
}
```

**Example**:
```
2026-02-12T14:30:35.500Z | progress | testing-coordinator | milestone_reached | {"milestone":"all_write_agents_complete","total_tests":15,"success_count":15,"failure_count":0}
```

---

## Event Type 4: Test Events (REQ-F-26)

**Purpose**: Track test execution lifecycle (start, complete, results)

**Status Values**:
- `execution_start`: Test execution begins
- `execution_complete`: Test execution finishes
- `pass_fail_counts`: Detailed test results

### Schema: execution_start

**When**: Test execution begins (execute-agent starts running tests)

**Metadata Fields**:
```json
{
  "framework": "string",        // Test framework (e.g., "pytest", "jest", "junit")
  "test_count": integer,        // Number of tests to run
  "command": "string",          // Test command executed (optional)
  "target_path": "string"       // Path where tests are running (optional)
}
```

**Example**:
```
2026-02-12T14:30:40.000Z | test | execute-agent | execution_start | {"framework":"pytest","test_count":15,"command":"pytest tests/","target_path":"D:/dev/project/tests"}
```

---

### Schema: execution_complete

**When**: Test execution finishes (all tests run)

**Metadata Fields**:
```json
{
  "passed": integer,            // Number of tests passed
  "failed": integer,            // Number of tests failed
  "skipped": integer,           // Number of tests skipped
  "duration_seconds": float,    // Total test execution time
  "pass_rate": float            // Pass rate (0.0 - 1.0) (optional)
}
```

**Example**:
```
2026-02-12T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":12,"failed":3,"skipped":0,"duration_seconds":8.5,"pass_rate":0.8}
```

---

## Event Type 5: Resource Events (REQ-F-27, REQ-F-27a)

**Purpose**: Track resource utilization, limits, queues, and token usage

**Status Values**:
- `queue_status`: Current queue depth and active agents
- `timeout_warning`: Team approaching timeout limit
- `timeout`: Team exceeded timeout (aborted)
- `limit_reached`: Agent or team limit reached (queuing required)
- `agent_queued`: Agent added to queue (limit reached)
- `agent_dequeued`: Agent removed from queue and spawned
- `team_queued`: Team added to queue (concurrent team limit reached)
- `team_dequeued`: Team removed from queue and started
- `depth_limit_exceeded`: Attempted to spawn agent beyond max depth
- `token_usage`: Token usage metrics for agent (REQ-F-27a)

### Schema: queue_status

**When**: Periodic queue status update (when agents spawn/complete)

**Metadata Fields**:
```json
{
  "active_agents": integer,     // Number of currently active agents
  "queued_agents": integer,     // Number of agents in queue
  "max_agents": integer         // Maximum allowed agents
}
```

**Example**:
```
2026-02-12T14:31:05.789Z | resource | testing-coordinator | queue_status | {"active_agents":3,"queued_agents":2,"max_agents":5}
```

---

### Schema: timeout_warning

**When**: Team is approaching timeout limit (e.g., 5 minutes remaining)

**Metadata Fields**:
```json
{
  "elapsed_seconds": float,     // Time elapsed since team start
  "timeout_seconds": float,     // Configured timeout limit
  "remaining_seconds": float    // Time remaining before timeout
}
```

**Example**:
```
2026-02-12T14:54:30.000Z | resource | testing-coordinator | timeout_warning | {"elapsed_seconds":1470,"timeout_seconds":1800,"remaining_seconds":330}
```

---

### Schema: timeout

**When**: Team exceeded timeout and execution is aborted

**Metadata Fields**:
```json
{
  "elapsed_seconds": float,     // Total time elapsed
  "aborted": boolean,           // Whether execution was aborted (always true)
  "active_agents": integer      // Number of agents active at timeout (optional)
}
```

**Example**:
```
2026-02-12T15:00:00.000Z | resource | testing-coordinator | timeout | {"elapsed_seconds":1800,"aborted":true,"active_agents":2}
```

---

### Schema: limit_reached

**When**: Agent or team limit reached (new requests will be queued)

**Metadata Fields**:
```json
{
  "limit_type": "string",       // "max_agents" or "max_teams"
  "current": integer,           // Current count
  "max": integer,               // Maximum allowed
  "action": "string"            // Action taken (e.g., "queued_new_request")
}
```

**Example**:
```
2026-02-12T14:30:20.000Z | resource | testing-coordinator | limit_reached | {"limit_type":"max_agents","current":5,"max":5,"action":"queued_new_request"}
```

---

### Schema: agent_queued

**When**: Agent added to queue (max agent limit reached)

**Metadata Fields**:
```json
{
  "agent": "string",            // Agent ID queued (optional)
  "active_agents": integer,     // Number of currently active agents
  "queued_agents": integer,     // Number of agents in queue (after this one)
  "max_agents": integer         // Maximum allowed agents
}
```

**Example**:
```
2026-02-12T14:30:25.000Z | resource | testing-coordinator | agent_queued | {"agent":"write-agent-6","active_agents":5,"queued_agents":1,"max_agents":5}
```

---

### Schema: agent_dequeued

**When**: Agent removed from queue and spawned (slot became available)

**Metadata Fields**:
```json
{
  "agent": "string",            // Agent ID dequeued and spawned
  "active_agents": integer,     // Number of currently active agents (after spawn)
  "queued_agents": integer      // Number of agents remaining in queue
}
```

**Example**:
```
2026-02-12T14:30:40.000Z | resource | testing-coordinator | agent_dequeued | {"agent":"write-agent-6","active_agents":5,"queued_agents":0}
```

---

### Schema: depth_limit_exceeded

**When**: Attempted to spawn agent beyond max depth (3 levels)

**Metadata Fields**:
```json
{
  "requested_depth": integer,   // Depth that was attempted
  "max_depth": integer,         // Maximum allowed depth (3)
  "parent_id": "string"         // Parent agent ID that attempted spawn
}
```

**Example**:
```
2026-02-12T14:35:00.000Z | resource | plugin-architecture | depth_limit_exceeded | {"requested_depth":4,"max_depth":3,"parent_id":"code-generation-coordinator"}
```

---

### Schema: token_usage (REQ-F-27a)

**When**: Agent completes and reports token usage metrics

**Metadata Fields**:
```json
{
  "agent_id": "string",         // Agent ID
  "input_tokens": integer,      // Number of input tokens consumed
  "output_tokens": integer,     // Number of output tokens generated
  "total_tokens": integer,      // Total tokens (input + output)
  "cache_read_tokens": integer, // Tokens read from cache (if available)
  "cache_write_tokens": integer,// Tokens written to cache (if available)
  "model": "string"             // Model used (e.g., "opus", "sonnet", "haiku")
}
```

**Example**:
```
2026-02-12T14:30:30.000Z | resource | write-agent-1 | token_usage | {"agent_id":"write-agent-1","input_tokens":1500,"output_tokens":800,"total_tokens":2300,"cache_read_tokens":500,"cache_write_tokens":200,"model":"sonnet"}
```

---

## Event Formatting Guidelines

### Timestamp Format

**Format**: ISO 8601 UTC with milliseconds
```
YYYY-MM-DDTHH:MM:SS.sssZ
```

**Example**: `2026-02-12T14:30:01.123Z`

**Generation** (pseudocode):
```python
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
# Output: 2026-02-12T14:30:01.123Z
```

---

### Metadata JSON Format

**Rules**:
1. Must be valid JSON (can be parsed by `json.loads()`)
2. Use double quotes for strings (not single quotes)
3. No trailing commas
4. Escape special characters in strings (backslash, quotes, newlines)
5. If no metadata, use empty object: `{}`

**Valid Examples**:
```json
{"parent":"testing-coordinator","depth":2}
{"reason":"timeout","retries":3,"last_error":"Agent exceeded 120s timeout"}
{}
```

**Invalid Examples** (will break parsers):
```json
{parent:"testing-coordinator"}  // Missing quotes on key
{'parent':'testing-coordinator'} // Single quotes not valid JSON
{"reason":"timeout",} // Trailing comma
{"error":"Path: C:\temp\file.txt"} // Unescaped backslash (should be C:\\temp\\file.txt)
```

---

### Pipe-Delimited Format

**Structure**:
```
[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
```

**Rules**:
1. Use ` | ` (space-pipe-space) as delimiter for readability
2. No spaces within timestamp, event_type, agent_id, or status fields
3. Metadata JSON may contain spaces (within the JSON object)
4. Each event is a single line (no newlines within event)

**Example**:
```
2026-02-12T14:30:01.123Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2}
```

---

## Event Sequence Examples

### Example 1: Successful Parallel Test Generation

```
2026-02-12T14:30:01.123Z | lifecycle | testing-coordinator | spawned | {"parent":"test-loop-orchestrator","depth":1,"team_id":"testing-parallel"}
2026-02-12T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"3 parallel write-agents","batches":3,"approval_required":true}
2026-02-12T14:30:15.789Z | coordination | testing-coordinator | plan_approved | {"user_response":"approve","batches":3}
2026-02-12T14:30:16.000Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2,"batch":1}
2026-02-12T14:30:16.100Z | lifecycle | write-agent-2 | spawned | {"parent":"testing-coordinator","depth":2,"batch":2}
2026-02-12T14:30:16.200Z | lifecycle | write-agent-3 | spawned | {"parent":"testing-coordinator","depth":2,"batch":3}
2026-02-12T14:30:16.300Z | coordination | testing-coordinator | parallel_execution_start | {"active_agents":3,"max_agents":5}
2026-02-12T14:30:20.000Z | progress | write-agent-1 | update | {"tests_written":2,"percent_complete":40}
2026-02-12T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":13.7,"tests_generated":5}
2026-02-12T14:30:32.000Z | lifecycle | write-agent-3 | completed | {"duration_seconds":15.8,"tests_generated":4}
2026-02-12T14:30:35.000Z | lifecycle | write-agent-2 | completed | {"duration_seconds":18.9,"tests_generated":6}
2026-02-12T14:30:35.500Z | coordination | testing-coordinator | parallel_execution_complete | {"total_tests":15,"successful_agents":3,"failed_agents":0}
2026-02-12T14:30:36.000Z | lifecycle | execute-agent | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-12T14:30:40.000Z | test | execute-agent | execution_start | {"framework":"pytest","test_count":15}
2026-02-12T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":15,"failed":0,"skipped":0,"duration_seconds":8.5}
2026-02-12T14:30:49.000Z | lifecycle | execute-agent | completed | {"duration_seconds":13.0}
2026-02-12T14:30:49.500Z | lifecycle | testing-coordinator | completed | {"duration_seconds":48.4,"total_tests":15}
```

---

### Example 2: Agent Failure with Retry

```
2026-02-12T14:30:16.000Z | lifecycle | write-agent-2 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-12T14:30:16.100Z | lifecycle | write-agent-2 | start | {"assigned_task":"Generate tests for src/calculator.py"}
2026-02-12T14:32:00.000Z | lifecycle | write-agent-2 | failed | {"reason":"timeout","retries":3,"last_error":"Agent exceeded 120s timeout"}
2026-02-12T14:32:00.100Z | coordination | testing-coordinator | parallel_execution_complete | {"total_tests":10,"successful_agents":2,"failed_agents":1}
```

---

### Example 3: Resource Queueing

```
2026-02-12T14:30:20.000Z | resource | testing-coordinator | limit_reached | {"limit_type":"max_agents","current":5,"max":5}
2026-02-12T14:30:20.100Z | resource | testing-coordinator | agent_queued | {"agent":"write-agent-6","active_agents":5,"queued_agents":1}
2026-02-12T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":13.7}
2026-02-12T14:30:30.100Z | resource | testing-coordinator | agent_dequeued | {"agent":"write-agent-6","active_agents":5,"queued_agents":0}
2026-02-12T14:30:30.200Z | lifecycle | write-agent-6 | spawned | {"parent":"testing-coordinator","depth":2}
```

---

## Testing Checklist

For TASK-006 acceptance:

- [ ] All 5 event types defined (lifecycle, coordination, progress, test, resource)
- [ ] Event format follows REQ-F-28 specification
- [ ] Timestamp format is ISO 8601 UTC with milliseconds
- [ ] Metadata is valid JSON (parseable by json.loads())
- [ ] Pipe-delimited format matches spec
- [ ] Lifecycle events cover all states (spawned, start, completed, failed)
- [ ] Coordination events cover plan flow (proposed, approved, rejected, assigned)
- [ ] Progress events support intermediate updates and milestones
- [ ] Test events capture execution lifecycle (start, complete, results)
- [ ] Resource events track queues, timeouts, limits, and token usage
- [ ] Token usage event includes all REQ-F-27a fields
- [ ] Event sequence examples demonstrate real-world workflows

---

## References

- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-23 to REQ-F-28, REQ-F-27a)
- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Telemetry Event Schema)
- Pattern: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-006)
