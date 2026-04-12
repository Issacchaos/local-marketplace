---
name: event-types
description: Event schema definitions for telemetry logging (lifecycle, coordination, progress, test, resource, config, dependency, agent_io, approval, timing, error, cost, data_flow, environment events)
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
- `event_type`: One of: `lifecycle`, `coordination`, `progress`, `test`, `resource`, `config`, `dependency`, `agent_io`, `approval`, `timing`, `error`, `cost`, `data_flow`, `environment`
- `agent_id`: Unique agent identifier (e.g., `write-agent-1`, `testing-coordinator`)
- `status`: Event-specific status (e.g., `spawned`, `running`, `completed`, `failed`)
- `metadata_json`: JSON object with event-specific data (must be valid JSON, even if empty `{}`)

---

## Event Type 1: Lifecycle Events (REQ-F-23)

**Purpose**: Track agent lifecycle transitions (spawn -> start -> complete/fail)

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
  "team_id": "string",          // Team this agent belongs to
  "team_config_snapshot": object,  // Full team config at spawn time (max_agents, timeout, gates, retry config)
  "cli_overrides": object,        // CLI overrides that were applied (empty {} if none)
  "coordinator_path": "string"    // Path to coordinator file
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
  "files_processed": integer,   // Number of files processed (optional)
  "output_full": object,          // Complete agent output (not just summary)
  "files_created": [string],      // List of files created with sizes (e.g., "test_user.py (145 lines)")
  "files_modified": [string],     // List of files modified
  "token_usage": object,          // Inline token metrics {input_tokens, output_tokens, cache_read, cache_write}
  "model_used": "string",         // Which model was used (opus/sonnet/haiku)
  "retry_count": integer          // How many retries occurred before success
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
  "duration_seconds": float,    // Time until failure (optional)
  "full_error_trace": "string",   // Complete error trace (not truncated)
  "agent_state_at_failure": object, // Full agent state snapshot at time of failure
  "retry_history": [object]       // Array of {attempt, timestamp, error, backoff_seconds} for all retry attempts
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
  "approval_required": boolean, // Whether approval gate is enabled
  "full_plan": object,            // Complete execution plan (phases array with agent assignments)
  "dependency_graph": object,     // Adjacency list representation {agent: [dependencies]}
  "agent_composition": [object],  // Full agent specs [{name, type, critical, max_instances}]
  "resource_estimate": object     // {estimated_tokens, estimated_minutes, agent_count, max_concurrent}
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

## Event Type 4: Test Telemetry Events (REQ-F-26)

**Purpose**: Track test execution lifecycle (start, complete, results), individual test cases, fixtures, coverage, and retries

**Status Values**:
- `execution_start`: Test execution begins
- `execution_complete`: Test execution finishes
- `pass_fail_counts`: Detailed test results
- `suite_discovered`: When test suite is discovered before execution
- `test_case_start`: When individual test case begins
- `test_case_result`: When individual test case completes
- `test_fixture_setup`: When test fixture/setup runs
- `test_fixture_teardown`: When test fixture/teardown runs
- `coverage_report`: When coverage data is collected
- `test_output_captured`: When test stdout/stderr is captured
- `test_retry`: When a flaky test is retried
- `test_summary`: Final summary after all tests complete

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

### Schema: suite_discovered

**When**: Test suite is discovered before execution begins

**Metadata Fields**:
```json
{
  "framework": "string",           // Test framework (e.g., "pytest", "jest")
  "suite_name": "string",          // Name of the test suite
  "test_count": integer,           // Number of tests discovered
  "file_path": "string",           // Path to the test file
  "discovery_duration_ms": float,  // Time to discover tests in milliseconds
  "parametrized_count": integer,   // Number of parametrized test variants
  "markers": ["string"]            // List of markers/tags on the suite (e.g., ["slow", "integration"])
}
```

**Example**:
```
2026-02-12T14:30:38.000Z | test | execute-agent | suite_discovered | {"framework":"pytest","suite_name":"test_user_service","test_count":12,"file_path":"tests/test_user_service.py","discovery_duration_ms":45.2,"parametrized_count":3,"markers":["unit"]}
```

---

### Schema: test_case_start

**When**: Individual test case begins execution

**Metadata Fields**:
```json
{
  "test_name": "string",           // Fully qualified test name
  "test_file": "string",           // Path to the test file
  "test_class": "string|null",     // Test class name (null if module-level)
  "parametrize_id": "string|null", // Parametrize variant ID (null if not parametrized)
  "markers": ["string"],           // List of markers on this test (e.g., ["slow", "smoke"])
  "fixtures": ["string"]           // List of fixtures requested by this test
}
```

**Example**:
```
2026-02-12T14:30:40.100Z | test | execute-agent | test_case_start | {"test_name":"test_user_service.py::TestUserService::test_create_user","test_file":"tests/test_user_service.py","test_class":"TestUserService","parametrize_id":null,"markers":["unit"],"fixtures":["db_session","mock_email"]}
```

---

### Schema: test_case_result

**When**: Individual test case completes execution

**Metadata Fields**:
```json
{
  "test_name": "string",           // Fully qualified test name
  "test_file": "string",           // Path to the test file
  "status": "string",              // One of: "passed", "failed", "skipped", "xfailed", "error"
  "duration_seconds": float,       // Test execution time
  "failure_message": "string|null", // Failure message (null if passed)
  "failure_traceback": "string|null", // Failure traceback (null if passed)
  "stdout_capture": "string|null", // Captured stdout (null if empty)
  "stderr_capture": "string|null", // Captured stderr (null if empty)
  "assertions_checked": integer    // Number of assertions checked in this test
}
```

**Example**:
```
2026-02-12T14:30:40.500Z | test | execute-agent | test_case_result | {"test_name":"test_user_service.py::TestUserService::test_create_user","test_file":"tests/test_user_service.py","status":"passed","duration_seconds":0.045,"failure_message":null,"failure_traceback":null,"stdout_capture":null,"stderr_capture":null,"assertions_checked":3}
```

---

### Schema: test_fixture_setup

**When**: Test fixture or setup function runs before test(s)

**Metadata Fields**:
```json
{
  "fixture_name": "string",        // Name of the fixture
  "scope": "string",               // One of: "function", "class", "module", "session"
  "duration_seconds": float,       // Time to set up the fixture
  "success": boolean,              // Whether setup succeeded
  "error": "string|null"           // Error message if setup failed (null if successful)
}
```

**Example**:
```
2026-02-12T14:30:39.800Z | test | execute-agent | test_fixture_setup | {"fixture_name":"db_session","scope":"function","duration_seconds":0.12,"success":true,"error":null}
```

---

### Schema: test_fixture_teardown

**When**: Test fixture or teardown function runs after test(s)

**Metadata Fields**:
```json
{
  "fixture_name": "string",        // Name of the fixture
  "scope": "string",               // One of: "function", "class", "module", "session"
  "duration_seconds": float,       // Time to tear down the fixture
  "success": boolean,              // Whether teardown succeeded
  "error": "string|null"           // Error message if teardown failed (null if successful)
}
```

**Example**:
```
2026-02-12T14:30:40.600Z | test | execute-agent | test_fixture_teardown | {"fixture_name":"db_session","scope":"function","duration_seconds":0.03,"success":true,"error":null}
```

---

### Schema: coverage_report

**When**: Coverage data is collected after test execution

**Metadata Fields**:
```json
{
  "total_statements": integer,     // Total number of executable statements
  "covered_statements": integer,   // Number of statements executed
  "missing_statements": integer,   // Number of statements not executed
  "coverage_percent": float,       // Line coverage percentage (0.0-100.0)
  "branch_coverage_percent": "float|null", // Branch coverage percentage (null if not collected)
  "uncovered_lines": object,       // Map of file path to list of uncovered line numbers
  "files_covered": integer,        // Number of files with any coverage
  "files_total": integer           // Total number of files in coverage scope
}
```

**Example**:
```
2026-02-12T14:30:49.000Z | test | execute-agent | coverage_report | {"total_statements":450,"covered_statements":410,"missing_statements":40,"coverage_percent":91.1,"branch_coverage_percent":85.3,"uncovered_lines":{"src/user_service.py":[45,67,89],"src/auth/login.py":[112,115]},"files_covered":8,"files_total":10}
```

---

### Schema: test_output_captured

**When**: Test stdout or stderr output is captured during execution

**Metadata Fields**:
```json
{
  "test_name": "string",           // Fully qualified test name
  "stream": "string",              // One of: "stdout", "stderr"
  "content": "string",             // Captured output content
  "content_length_chars": integer  // Length of captured content in characters
}
```

**Example**:
```
2026-02-12T14:30:41.000Z | test | execute-agent | test_output_captured | {"test_name":"test_user_service.py::test_create_user","stream":"stdout","content":"Creating user: john_doe...","content_length_chars":26}
```

---

### Schema: test_retry

**When**: A flaky test is retried after failure

**Metadata Fields**:
```json
{
  "test_name": "string",           // Fully qualified test name
  "retry_count": integer,          // Current retry attempt number
  "max_retries": integer,          // Maximum retries configured
  "previous_status": "string",     // Status of the previous attempt (e.g., "failed", "error")
  "previous_error": "string"       // Error message from previous attempt
}
```

**Example**:
```
2026-02-12T14:30:42.000Z | test | execute-agent | test_retry | {"test_name":"test_user_service.py::test_concurrent_update","retry_count":1,"max_retries":3,"previous_status":"failed","previous_error":"AssertionError: expected 200, got 503"}
```

---

### Schema: test_summary

**When**: Final summary after all tests in the suite complete

**Metadata Fields**:
```json
{
  "total": integer,                // Total number of tests run
  "passed": integer,               // Number of tests passed
  "failed": integer,               // Number of tests failed
  "skipped": integer,              // Number of tests skipped
  "errors": integer,               // Number of tests with errors (setup/teardown failures)
  "xfailed": integer,              // Number of expected failures
  "xpassed": integer,              // Number of unexpected passes
  "duration_seconds": float,       // Total suite execution time
  "pass_rate": float,              // Pass rate (0.0 - 1.0)
  "slowest_tests": [object],       // Array of {"name": "string", "duration_seconds": float} for slowest tests
  "failure_categories": object     // Map of failure category to count (e.g., {"assertion": 2, "timeout": 1})
}
```

**Example**:
```
2026-02-12T14:30:49.200Z | test | execute-agent | test_summary | {"total":15,"passed":12,"failed":2,"skipped":1,"errors":0,"xfailed":0,"xpassed":0,"duration_seconds":9.2,"pass_rate":0.8,"slowest_tests":[{"name":"test_bulk_import","duration_seconds":2.3},{"name":"test_concurrent_update","duration_seconds":1.8}],"failure_categories":{"assertion":1,"timeout":1}}
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
  "model": "string",            // Model used (e.g., "opus", "sonnet", "haiku")
  "cost_estimate_usd": float,     // Estimated cost based on model pricing
  "context_window_utilization": float, // Percentage of context window used (0.0-1.0)
  "prompt_tokens_breakdown": object    // {system_tokens, user_tokens, assistant_tokens}
}
```

**Example**:
```
2026-02-12T14:30:30.000Z | resource | write-agent-1 | token_usage | {"agent_id":"write-agent-1","input_tokens":1500,"output_tokens":800,"total_tokens":2300,"cache_read_tokens":500,"cache_write_tokens":200,"model":"sonnet"}
```

---

## Event Type 6: Config Events

**Purpose**: Track configuration resolution and override decisions

**Status Values**:
- `config_loaded`: When team definition is loaded from disk
- `config_override_applied`: When CLI/env/config override changes a value
- `config_defaults_applied`: When default values fill in missing fields
- `model_resolved`: When model selection resolves for an agent

### Schema: config_loaded

**When**: Team definition is loaded from disk

**Metadata Fields**:
```json
{
  "team_name": "string",         // Name of the team definition
  "file_path": "string",         // Path to the team definition file
  "frontmatter_raw": object,     // Full parsed YAML frontmatter
  "file_size_bytes": integer,    // Size of the team definition file
  "parse_duration_ms": float     // Time to parse the file
}
```

**Example**:
```
2026-02-12T14:29:58.000Z | config | testing-coordinator | config_loaded | {"team_name":"testing-parallel","file_path":"teams/testing-parallel.md","frontmatter_raw":{"max_agents":5,"timeout":1800},"file_size_bytes":2048,"parse_duration_ms":3.2}
```

---

### Schema: config_override_applied

**When**: CLI/env/config override changes a configured value

**Metadata Fields**:
```json
{
  "field": "string",             // Field name that was overridden
  "original_value": "string",    // Original value from team definition
  "override_value": "string",    // New value after override
  "source": "string",            // Override source: "cli", "env", or "config"
  "override_key": "string"       // The key/flag used for the override
}
```

**Example**:
```
2026-02-12T14:29:58.500Z | config | testing-coordinator | config_override_applied | {"field":"max_agents","original_value":"5","override_value":"3","source":"cli","override_key":"--max-agents"}
```

---

### Schema: config_defaults_applied

**When**: Default values fill in missing fields in team configuration

**Metadata Fields**:
```json
{
  "fields_defaulted": [string],  // List of field names that received defaults
  "defaults_applied": object     // Map of field name to default value applied
}
```

**Example**:
```
2026-02-12T14:29:58.600Z | config | testing-coordinator | config_defaults_applied | {"fields_defaulted":["timeout","retry_count","gates"],"defaults_applied":{"timeout":1800,"retry_count":3,"gates":{"before_execution":true}}}
```

---

### Schema: model_resolved

**When**: Model selection resolves for a specific agent

**Metadata Fields**:
```json
{
  "agent_name": "string",        // Agent the model was resolved for
  "resolved_model": "string",    // Final resolved model name
  "resolution_source": "string", // Where the model was resolved from
  "timeout_seconds": float,      // Timeout configured for this model
  "precedence_chain": [object]   // Array of {source, value|not_set} showing resolution order
}
```

**Example**:
```
2026-02-12T14:29:59.000Z | config | testing-coordinator | model_resolved | {"agent_name":"write-agent-1","resolved_model":"sonnet","resolution_source":"team_config","timeout_seconds":120,"precedence_chain":[{"source":"cli","not_set":true},{"source":"agent_config","not_set":true},{"source":"team_config","value":"sonnet"}]}
```

---

## Event Type 7: Dependency Events

**Purpose**: Track dependency graph construction and resolution

**Status Values**:
- `graph_constructed`: When full dependency graph is built
- `phase_planned`: When an execution phase is computed
- `dependency_waiting`: When agent is blocked on unresolved dependency
- `dependency_satisfied`: When a specific dependency edge is resolved

### Schema: graph_constructed

**When**: Full dependency graph is built from team configuration

**Metadata Fields**:
```json
{
  "adjacency_list": object,      // Adjacency list representation of graph
  "topological_order": [string], // Topological sort order of agents
  "total_nodes": integer,        // Total number of nodes (agents) in graph
  "total_edges": integer,        // Total number of dependency edges
  "has_cycles": boolean          // Whether the graph contains cycles (should be false)
}
```

**Example**:
```
2026-02-12T14:30:00.000Z | dependency | testing-coordinator | graph_constructed | {"adjacency_list":{"execute-agent":["write-agent-1","write-agent-2","write-agent-3"],"write-agent-1":[],"write-agent-2":[],"write-agent-3":[]},"topological_order":["write-agent-1","write-agent-2","write-agent-3","execute-agent"],"total_nodes":4,"total_edges":3,"has_cycles":false}
```

---

### Schema: phase_planned

**When**: An execution phase is computed from the dependency graph

**Metadata Fields**:
```json
{
  "phase_number": integer,       // Phase number (1-based)
  "agents": [string],            // Agent IDs in this phase
  "parallel": boolean,           // Whether agents in this phase run in parallel
  "blocked_by": [string],        // Agent IDs that must complete before this phase
  "estimated_duration_seconds": float // Estimated time for this phase
}
```

**Example**:
```
2026-02-12T14:30:00.100Z | dependency | testing-coordinator | phase_planned | {"phase_number":1,"agents":["write-agent-1","write-agent-2","write-agent-3"],"parallel":true,"blocked_by":[],"estimated_duration_seconds":30.0}
```

---

### Schema: dependency_waiting

**When**: Agent is blocked on one or more unresolved dependencies

**Metadata Fields**:
```json
{
  "agent": "string",             // Agent ID that is waiting
  "waiting_for": [string],       // Agent IDs still being waited on
  "resolved": [string],          // Agent IDs already resolved
  "remaining": [string],         // Agent IDs still remaining
  "wait_start_timestamp": "string" // ISO 8601 timestamp when wait began
}
```

**Example**:
```
2026-02-12T14:30:25.000Z | dependency | testing-coordinator | dependency_waiting | {"agent":"execute-agent","waiting_for":["write-agent-2","write-agent-3"],"resolved":["write-agent-1"],"remaining":["write-agent-2","write-agent-3"],"wait_start_timestamp":"2026-02-12T14:30:16.300Z"}
```

---

### Schema: dependency_satisfied

**When**: A specific dependency edge is resolved (an agent another agent depends on completes)

**Metadata Fields**:
```json
{
  "agent": "string",             // Agent ID whose dependency was satisfied
  "dependency": "string",        // Agent ID that completed (the dependency)
  "resolution_duration_seconds": float, // Time from dependency start to completion
  "unblocked_agents": [string]   // Agent IDs now unblocked by this resolution
}
```

**Example**:
```
2026-02-12T14:30:30.000Z | dependency | testing-coordinator | dependency_satisfied | {"agent":"execute-agent","dependency":"write-agent-1","resolution_duration_seconds":13.7,"unblocked_agents":[]}
```

---

## Event Type 8: Agent I/O Events

**Purpose**: Capture full agent prompts, outputs, and file operations

**Status Values**:
- `prompt_constructed`: When agent prompt is built and ready to send
- `output_received`: When raw agent output is received
- `output_parsed`: When structured data is extracted from agent response
- `file_written`: When agent creates or modifies a file
- `file_read`: When agent reads a file during execution

### Schema: prompt_constructed

**When**: Agent prompt is built and ready to send to the model

**Metadata Fields**:
```json
{
  "agent_id": "string",          // Agent ID
  "prompt_text": "string",       // Full prompt text
  "prompt_length_chars": integer, // Length of prompt in characters
  "prompt_estimated_tokens": integer, // Estimated token count
  "model": "string",             // Model the prompt will be sent to
  "includes_context": boolean    // Whether context from other agents is included
}
```

**Example**:
```
2026-02-12T14:30:16.050Z | agent_io | write-agent-1 | prompt_constructed | {"agent_id":"write-agent-1","prompt_text":"Generate pytest tests for src/user_service.py...","prompt_length_chars":4500,"prompt_estimated_tokens":1125,"model":"sonnet","includes_context":false}
```

---

### Schema: output_received

**When**: Raw agent output is received from the model

**Metadata Fields**:
```json
{
  "agent_id": "string",          // Agent ID
  "output_text": "string",       // Full output text
  "output_length_chars": integer, // Length of output in characters
  "output_estimated_tokens": integer, // Estimated token count
  "duration_seconds": float      // Time from prompt send to output received
}
```

**Example**:
```
2026-02-12T14:30:29.500Z | agent_io | write-agent-1 | output_received | {"agent_id":"write-agent-1","output_text":"import pytest\nfrom user_service import UserService...","output_length_chars":3200,"output_estimated_tokens":800,"duration_seconds":13.4}
```

---

### Schema: output_parsed

**When**: Structured data is extracted from agent response

**Metadata Fields**:
```json
{
  "agent_id": "string",          // Agent ID
  "parsed_fields": [string],     // List of fields successfully parsed
  "parse_success": boolean,      // Whether parsing succeeded overall
  "parse_errors": [string],      // List of parse errors (empty if successful)
  "structured_output": object    // The parsed structured output
}
```

**Example**:
```
2026-02-12T14:30:29.600Z | agent_io | write-agent-1 | output_parsed | {"agent_id":"write-agent-1","parsed_fields":["test_file","test_count","framework"],"parse_success":true,"parse_errors":[],"structured_output":{"test_file":"test_user_service.py","test_count":5,"framework":"pytest"}}
```

---

### Schema: file_written

**When**: Agent creates or modifies a file on disk

**Metadata Fields**:
```json
{
  "agent_id": "string",          // Agent ID
  "file_path": "string",         // Path to the file
  "operation": "string",         // One of: "create", "modify", "append"
  "size_bytes": integer,         // Size of the file after write
  "line_count": integer,         // Number of lines in the file after write
  "encoding": "string"           // File encoding (e.g., "utf-8")
}
```

**Example**:
```
2026-02-12T14:30:29.700Z | agent_io | write-agent-1 | file_written | {"agent_id":"write-agent-1","file_path":"tests/test_user_service.py","operation":"create","size_bytes":4200,"line_count":145,"encoding":"utf-8"}
```

---

### Schema: file_read

**When**: Agent reads a file during execution

**Metadata Fields**:
```json
{
  "agent_id": "string",          // Agent ID
  "file_path": "string",         // Path to the file read
  "size_bytes": integer,         // Size of the file
  "line_count": integer,         // Number of lines in the file
  "read_duration_ms": float      // Time to read the file in milliseconds
}
```

**Example**:
```
2026-02-12T14:30:17.000Z | agent_io | write-agent-1 | file_read | {"agent_id":"write-agent-1","file_path":"src/user_service.py","size_bytes":3800,"line_count":120,"read_duration_ms":1.5}
```

---

## Event Type 9: Approval Events

**Purpose**: Track detailed approval gate interactions and user decisions

**Status Values**:
- `gate_entered`: When an approval gate checkpoint is reached
- `prompt_displayed`: When the full approval prompt is shown to user
- `user_response_received`: When user responds to approval gate
- `plan_regenerated`: When plan is modified after user feedback

### Schema: gate_entered

**When**: An approval gate checkpoint is reached during execution

**Metadata Fields**:
```json
{
  "gate_type": "string",         // One of: "before_execution", "after_completion"
  "iteration": integer,          // Current iteration number
  "max_iterations": integer,     // Maximum allowed iterations
  "gates_config": object,        // Full gates configuration object
  "context_summary": "string"    // Summary of current execution context
}
```

**Example**:
```
2026-02-12T14:30:01.400Z | approval | testing-coordinator | gate_entered | {"gate_type":"before_execution","iteration":1,"max_iterations":3,"gates_config":{"before_execution":true,"after_completion":false},"context_summary":"3 write-agents planned for 12 test targets"}
```

---

### Schema: prompt_displayed

**When**: The full approval prompt is shown to the user

**Metadata Fields**:
```json
{
  "gate_type": "string",         // One of: "before_execution", "after_completion"
  "prompt_text": "string",       // Full prompt text displayed to user
  "prompt_length_chars": integer, // Length of prompt in characters
  "options_presented": [string]  // List of options shown (e.g., ["approve", "reject", "modify"])
}
```

**Example**:
```
2026-02-12T14:30:01.450Z | approval | testing-coordinator | prompt_displayed | {"gate_type":"before_execution","prompt_text":"Plan: 3 parallel write-agents will generate tests for 12 files...","prompt_length_chars":250,"options_presented":["approve","reject","modify"]}
```

---

### Schema: user_response_received

**When**: User responds to an approval gate prompt

**Metadata Fields**:
```json
{
  "gate_type": "string",         // One of: "before_execution", "after_completion"
  "decision": "string",          // One of: "approve", "reject", "modify"
  "feedback_text": "string|null", // User feedback text (null if no feedback)
  "response_time_seconds": float, // Time user took to respond
  "iteration": integer           // Current iteration number
}
```

**Example**:
```
2026-02-12T14:30:15.789Z | approval | testing-coordinator | user_response_received | {"gate_type":"before_execution","decision":"approve","feedback_text":null,"response_time_seconds":14.3,"iteration":1}
```

---

### Schema: plan_regenerated

**When**: Plan is modified after user feedback requesting changes

**Metadata Fields**:
```json
{
  "iteration": integer,          // Current iteration number
  "feedback_applied": "string",  // The feedback that was applied
  "changes_made": [string],      // List of changes made to the plan
  "old_plan_summary": "string",  // Summary of the previous plan
  "new_plan_summary": "string",  // Summary of the new plan
  "agents_added": [string],      // Agent IDs added in the new plan
  "agents_removed": [string]     // Agent IDs removed in the new plan
}
```

**Example**:
```
2026-02-12T14:30:20.000Z | approval | testing-coordinator | plan_regenerated | {"iteration":2,"feedback_applied":"Reduce to 2 agents and add retry logic","changes_made":["reduced agents from 3 to 2","added retry_count: 2"],"old_plan_summary":"3 parallel write-agents","new_plan_summary":"2 parallel write-agents with retries","agents_added":[],"agents_removed":["write-agent-3"]}
```

---

## Event Type 10: Timing Events

**Purpose**: Track performance overhead and phase transitions

**Status Values**:
- `phase_transition`: When execution moves between phases
- `queue_wait_time`: How long an agent waited in FIFO queue
- `backoff_wait`: Time spent during retry backoff
- `overhead_summary`: End-of-team summary of orchestration overhead

### Schema: phase_transition

**When**: Execution moves between phases (e.g., write phase to execute phase)

**Metadata Fields**:
```json
{
  "from_phase": "string",          // Phase being exited
  "to_phase": "string",            // Phase being entered
  "transition_duration_seconds": float, // Time spent transitioning
  "idle_time_seconds": float,      // Idle time between phases
  "overhead_description": "string" // Human-readable description of overhead
}
```

**Example**:
```
2026-02-12T14:30:33.700Z | timing | testing-coordinator | phase_transition | {"from_phase":"write","to_phase":"execute","transition_duration_seconds":0.4,"idle_time_seconds":0.1,"overhead_description":"Dependency resolution and agent spawn setup"}
```

---

### Schema: queue_wait_time

**When**: An agent finishes waiting in the FIFO queue and is dequeued

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID that was queued
  "queue_entry_time": "string",    // ISO 8601 timestamp when agent entered queue
  "queue_exit_time": "string",     // ISO 8601 timestamp when agent left queue
  "wait_duration_seconds": float,  // Total time spent waiting in queue
  "queue_position_at_entry": integer, // Position in queue when entered
  "agents_ahead_at_entry": integer // Number of agents ahead in queue at entry time
}
```

**Example**:
```
2026-02-12T14:30:30.200Z | timing | testing-coordinator | queue_wait_time | {"agent_id":"write-agent-6","queue_entry_time":"2026-02-12T14:30:20.100Z","queue_exit_time":"2026-02-12T14:30:30.100Z","wait_duration_seconds":10.0,"queue_position_at_entry":1,"agents_ahead_at_entry":1}
```

---

### Schema: backoff_wait

**When**: Time is spent during retry backoff before reattempting

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID performing backoff
  "retry_attempt": integer,        // Current retry attempt number
  "backoff_seconds": float,        // Duration of the backoff wait
  "backoff_start": "string",       // ISO 8601 timestamp when backoff started
  "backoff_end": "string",         // ISO 8601 timestamp when backoff ended
  "reason": "string"               // Reason for the backoff (e.g., "rate_limit", "timeout")
}
```

**Example**:
```
2026-02-12T14:31:05.000Z | timing | write-agent-2 | backoff_wait | {"agent_id":"write-agent-2","retry_attempt":2,"backoff_seconds":5.0,"backoff_start":"2026-02-12T14:31:00.000Z","backoff_end":"2026-02-12T14:31:05.000Z","reason":"rate_limit"}
```

---

### Schema: overhead_summary

**When**: Team execution completes and overhead metrics are summarized

**Metadata Fields**:
```json
{
  "total_wall_clock_seconds": float,     // Total wall clock time for team execution
  "total_agent_work_seconds": float,     // Sum of all agent execution durations
  "total_overhead_seconds": float,       // Wall clock minus useful agent work
  "overhead_percent": float,             // Overhead as percentage of wall clock time
  "queue_wait_total_seconds": float,     // Total time all agents spent waiting in queue
  "backoff_wait_total_seconds": float,   // Total time spent in retry backoff
  "phase_transition_total_seconds": float, // Total time spent transitioning between phases
  "framework_tax_percent": float         // Overhead percentage attributable to framework
}
```

**Example**:
```
2026-02-12T14:30:49.600Z | timing | testing-coordinator | overhead_summary | {"total_wall_clock_seconds":51.5,"total_agent_work_seconds":44.6,"total_overhead_seconds":6.9,"overhead_percent":13.4,"queue_wait_total_seconds":0.0,"backoff_wait_total_seconds":0.0,"phase_transition_total_seconds":0.4,"framework_tax_percent":13.4}
```

---

## Event Type 11: Error Events

**Purpose**: Detailed error classification and debugging context

**Status Values**:
- `validation_check`: Each validation check during team loading
- `state_transition`: Agent state machine transition
- `retry_decision`: Logic behind retry/no-retry decision
- `error_classified`: Categorized error with context

### Schema: validation_check

**When**: A validation check is performed during team definition loading

**Metadata Fields**:
```json
{
  "check_name": "string",          // Name of the validation check
  "field": "string",               // Field being validated
  "result": "string",              // One of: "pass", "fail", "warn"
  "expected": "string",            // Expected value or constraint
  "actual": "string",              // Actual value found
  "suggestion": "string|null"      // Suggestion for fixing (null if passed)
}
```

**Example**:
```
2026-02-12T14:29:57.500Z | error | testing-coordinator | validation_check | {"check_name":"max_agents_range","field":"max_agents","result":"pass","expected":"1-10","actual":"5","suggestion":null}
```

---

### Schema: state_transition

**When**: An agent transitions between states in the state machine

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID transitioning
  "from_state": "string",          // Previous state
  "to_state": "string",            // New state
  "trigger": "string",             // What triggered the transition
  "before_snapshot": object,       // Agent state snapshot before transition
  "after_snapshot": object,        // Agent state snapshot after transition
  "transition_valid": boolean      // Whether this transition is valid per the state machine
}
```

**Example**:
```
2026-02-12T14:30:16.050Z | error | write-agent-1 | state_transition | {"agent_id":"write-agent-1","from_state":"spawned","to_state":"running","trigger":"task_assigned","before_snapshot":{"task":null,"retries":0},"after_snapshot":{"task":"Generate tests for src/user_service.py","retries":0},"transition_valid":true}
```

---

### Schema: retry_decision

**When**: The system decides whether to retry a failed agent

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID being evaluated
  "should_retry": boolean,         // Whether a retry will be performed
  "retry_count": integer,          // Current retry count
  "max_retries": integer,          // Maximum retries configured
  "failure_reason": "string",      // Reason for the failure
  "backoff_chosen_seconds": float, // Backoff duration chosen for retry
  "failure_handling_strategy": "string", // Strategy applied (e.g., "exponential_backoff", "immediate_retry", "abort")
  "is_critical_agent": boolean     // Whether this agent is marked as critical
}
```

**Example**:
```
2026-02-12T14:32:00.050Z | error | testing-coordinator | retry_decision | {"agent_id":"write-agent-2","should_retry":true,"retry_count":1,"max_retries":3,"failure_reason":"timeout","backoff_chosen_seconds":5.0,"failure_handling_strategy":"exponential_backoff","is_critical_agent":false}
```

---

### Schema: error_classified

**When**: An error is caught and categorized with debugging context

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID that experienced the error
  "error_category": "string",      // One of: "timeout", "rate_limit", "context_overflow", "tool_denied", "malformed_output", "network", "permission", "unknown"
  "raw_error": "string",           // Raw error message
  "classified_severity": "string", // One of: "fatal", "retriable", "ignorable"
  "suggested_action": "string",    // Suggested remediation action
  "stack_trace": "string|null"     // Stack trace if available (null otherwise)
}
```

**Example**:
```
2026-02-12T14:32:00.100Z | error | write-agent-2 | error_classified | {"agent_id":"write-agent-2","error_category":"timeout","raw_error":"Agent exceeded 120s timeout","classified_severity":"retriable","suggested_action":"Increase timeout or reduce task scope","stack_trace":null}
```

---

## Event Type 12: Cost Events

**Purpose**: Track resource consumption and cost estimates

**Status Values**:
- `memory_snapshot`: Context window usage at a point in time
- `cumulative_cost`: Running cost total for team
- `model_fallback`: When a model fails and falls back
- `utilization_snapshot`: Concurrent agent utilization over time

### Schema: memory_snapshot

**When**: Context window usage is captured at a specific point during agent execution

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID
  "snapshot_point": "string",      // One of: "spawn", "midpoint", "completion"
  "context_used_tokens": integer,  // Number of tokens currently used in context
  "context_max_tokens": integer,   // Maximum tokens available in context window
  "utilization_percent": float,    // Context utilization percentage (0.0-100.0)
  "cache_hit_rate": "float|null"   // Cache hit rate (null if not applicable)
}
```

**Example**:
```
2026-02-12T14:30:20.000Z | cost | write-agent-1 | memory_snapshot | {"agent_id":"write-agent-1","snapshot_point":"midpoint","context_used_tokens":45000,"context_max_tokens":200000,"utilization_percent":22.5,"cache_hit_rate":0.35}
```

---

### Schema: cumulative_cost

**When**: Running cost total is updated (typically after each agent completes)

**Metadata Fields**:
```json
{
  "team_id": "string",             // Team ID
  "total_input_tokens": integer,   // Cumulative input tokens across all agents
  "total_output_tokens": integer,  // Cumulative output tokens across all agents
  "total_cache_read_tokens": integer, // Cumulative cache read tokens
  "total_cache_write_tokens": integer, // Cumulative cache write tokens
  "estimated_cost_usd": float,     // Estimated total cost in USD
  "cost_by_model": object,         // Cost breakdown by model (e.g., {"sonnet": 0.024, "opus": 0.15})
  "cost_by_agent": object,         // Cost breakdown by agent (e.g., {"write-agent-1": 0.012})
  "agents_completed": integer,     // Number of agents completed so far
  "agents_remaining": integer      // Number of agents still running or queued
}
```

**Example**:
```
2026-02-12T14:30:30.100Z | cost | testing-coordinator | cumulative_cost | {"team_id":"testing-parallel","total_input_tokens":2175,"total_output_tokens":1500,"total_cache_read_tokens":380,"total_cache_write_tokens":190,"estimated_cost_usd":0.024,"cost_by_model":{"sonnet":0.024},"cost_by_agent":{"write-agent-1":0.012,"write-agent-2":0.012},"agents_completed":2,"agents_remaining":1}
```

---

### Schema: model_fallback

**When**: A model fails and the system falls back to an alternative model

**Metadata Fields**:
```json
{
  "agent_id": "string",            // Agent ID experiencing the fallback
  "original_model": "string",      // Model that was originally configured
  "fallback_model": "string",      // Model being fallen back to
  "failure_reason": "string",      // Reason the original model failed
  "attempt_count": integer,        // Number of attempts on original model before fallback
  "fallback_timeout_seconds": float // Timeout configured for the fallback model
}
```

**Example**:
```
2026-02-12T14:31:00.000Z | cost | write-agent-3 | model_fallback | {"agent_id":"write-agent-3","original_model":"opus","fallback_model":"sonnet","failure_reason":"rate_limit","attempt_count":2,"fallback_timeout_seconds":120}
```

---

### Schema: utilization_snapshot

**When**: Periodic snapshot of concurrent agent utilization

**Metadata Fields**:
```json
{
  "timestamp": "string",           // ISO 8601 timestamp of the snapshot
  "active_agents": integer,        // Number of agents currently executing
  "max_agents": integer,           // Maximum allowed concurrent agents
  "queued_agents": integer,        // Number of agents waiting in queue
  "utilization_percent": float,    // Agent slot utilization (0.0-100.0)
  "slots_available": integer,      // Number of available agent slots
  "throughput_agents_per_minute": "float|null" // Agents completed per minute (null if too early to calculate)
}
```

**Example**:
```
2026-02-12T14:30:25.000Z | cost | testing-coordinator | utilization_snapshot | {"timestamp":"2026-02-12T14:30:25.000Z","active_agents":3,"max_agents":5,"queued_agents":0,"utilization_percent":60.0,"slots_available":2,"throughput_agents_per_minute":null}
```

---

## Event Type 13: Data Flow Events

**Purpose**: Track data passing between phases and agent communication

**Status Values**:
- `data_passed`: Output from one phase becomes input to next
- `file_conflict_check`: When reprioritization checks for conflicts
- `plan_diff`: Structured diff when user modifies plan
- `agent_message`: Peer-to-peer agent communication via SendMessage

### Schema: data_passed

**When**: Output from one agent/phase is passed as input to the next

**Metadata Fields**:
```json
{
  "from_agent": "string",          // Agent ID that produced the data
  "to_agent": "string",            // Agent ID that will consume the data
  "from_phase": "string",          // Phase the data originated from
  "to_phase": "string",            // Phase the data is being passed to
  "data_type": "string",           // Type of data (e.g., "test_files", "coverage_report", "plan")
  "data_size_chars": integer,      // Size of data in characters
  "data_summary": "string",        // Human-readable summary of the data
  "fields_passed": ["string"]      // List of field names passed
}
```

**Example**:
```
2026-02-12T14:30:33.800Z | data_flow | testing-coordinator | data_passed | {"from_agent":"write-agent-1","to_agent":"execute-agent","from_phase":"write","to_phase":"execute","data_type":"test_files","data_size_chars":4200,"data_summary":"5 test functions in test_user_service.py","fields_passed":["test_file","test_count","framework"]}
```

---

### Schema: file_conflict_check

**When**: Reprioritization or parallel execution checks for file conflicts

**Metadata Fields**:
```json
{
  "team_id": "string",             // Team ID
  "layers_checked": ["string"],    // List of layer/phase names checked
  "conflicts_found": boolean,      // Whether any conflicts were detected
  "conflicting_files": ["string"], // List of file paths with conflicts
  "conflicting_layers": ["string"], // List of layers involved in conflicts
  "action_taken": "string"         // One of: "allowed", "rejected"
}
```

**Example**:
```
2026-02-12T14:30:16.250Z | data_flow | testing-coordinator | file_conflict_check | {"team_id":"testing-parallel","layers_checked":["write-agent-1","write-agent-2","write-agent-3"],"conflicts_found":false,"conflicting_files":[],"conflicting_layers":[],"action_taken":"allowed"}
```

---

### Schema: plan_diff

**When**: User modifies the execution plan during an approval gate

**Metadata Fields**:
```json
{
  "iteration": integer,            // Current iteration number
  "agents_added": ["string"],      // Agent IDs added in the modification
  "agents_removed": ["string"],    // Agent IDs removed in the modification
  "agents_reordered": boolean,     // Whether agent execution order changed
  "max_agents_changed": object,    // {"from": integer, "to": integer} if max_agents changed
  "phases_before": integer,        // Number of phases before modification
  "phases_after": integer,         // Number of phases after modification
  "user_feedback": "string"        // User feedback that prompted the change
}
```

**Example**:
```
2026-02-12T14:30:20.100Z | data_flow | testing-coordinator | plan_diff | {"iteration":2,"agents_added":[],"agents_removed":["write-agent-3"],"agents_reordered":false,"max_agents_changed":{"from":5,"to":3},"phases_before":2,"phases_after":2,"user_feedback":"Reduce to 2 agents and lower concurrency"}
```

---

### Schema: agent_message

**When**: Peer-to-peer agent communication occurs via SendMessage tool

**Metadata Fields**:
```json
{
  "from_agent": "string",          // Agent ID sending the message
  "to_agent": "string",            // Agent ID receiving the message
  "message_type": "string",        // One of: "request", "response", "notification"
  "message_summary": "string",     // Human-readable summary of the message
  "message_length_chars": integer, // Length of the message in characters
  "timestamp": "string"            // ISO 8601 timestamp of the message
}
```

**Example**:
```
2026-02-12T14:30:25.500Z | data_flow | write-agent-1 | agent_message | {"from_agent":"write-agent-1","to_agent":"write-agent-2","message_type":"notification","message_summary":"Completed tests for user_service.py, shared fixtures available","message_length_chars":85,"timestamp":"2026-02-12T14:30:25.500Z"}
```

---

## Event Type 14: Environment Events

**Purpose**: Capture execution context for log correlation and debugging

**Status Values**:
- `session_start`: When team execution session begins
- `environment_snapshot`: Full environment context
- `session_end`: When team execution session completes

### Schema: session_start

**When**: Team execution session begins

**Metadata Fields**:
```json
{
  "session_id": "string",          // Unique session identifier
  "plugin_version": "string",      // Version of the teamsters plugin
  "claude_code_version": "string|null", // Version of Claude Code (null if unavailable)
  "platform": "string",            // One of: "win32", "darwin", "linux"
  "os_version": "string",          // Operating system version
  "shell": "string",               // Shell being used (e.g., "bash", "zsh", "powershell")
  "working_directory": "string",   // Working directory path
  "git_branch": "string|null",     // Current git branch (null if not in a git repo)
  "git_commit": "string|null",     // Current git commit SHA (null if not in a git repo)
  "git_dirty": boolean,            // Whether working tree has uncommitted changes
  "node_version": "string|null",   // Node.js version (null if not available)
  "python_version": "string|null"  // Python version (null if not available)
}
```

**Example**:
```
2026-02-12T14:29:55.000Z | environment | testing-coordinator | session_start | {"session_id":"sess_abc123","plugin_version":"1.0.0","claude_code_version":"1.2.3","platform":"win32","os_version":"Windows 11 Enterprise 10.0.26100","shell":"bash","working_directory":"D:/dev/project","git_branch":"main","git_commit":"a1b2c3d","git_dirty":false,"node_version":"20.11.0","python_version":"3.12.1"}
```

---

### Schema: environment_snapshot

**When**: Full environment context is captured (typically at session start)

**Metadata Fields**:
```json
{
  "teamsters_env_vars": object,    // Relevant environment variables (e.g., {"TEAMSTERS_LOG_LEVEL": "debug"})
  "experimental_flags": object,    // Experimental flags enabled (e.g., {"parallel_v2": true})
  "config_file_path": "string|null", // Path to config file (null if not found)
  "config_file_exists": boolean,   // Whether the config file exists
  "teams_directory_exists": boolean, // Whether the teams directory exists
  "teams_available": ["string"],   // List of available team definitions
  "agents_directory_exists": boolean // Whether the agents directory exists
}
```

**Example**:
```
2026-02-12T14:29:55.100Z | environment | testing-coordinator | environment_snapshot | {"teamsters_env_vars":{"TEAMSTERS_LOG_LEVEL":"debug","TEAMSTERS_MAX_TEAMS":"3"},"experimental_flags":{},"config_file_path":"teamsters.config.json","config_file_exists":true,"teams_directory_exists":true,"teams_available":["testing-parallel","testing-sequential","code-review"],"agents_directory_exists":true}
```

---

### Schema: session_end

**When**: Team execution session completes

**Metadata Fields**:
```json
{
  "session_id": "string",          // Unique session identifier (matches session_start)
  "total_duration_seconds": float, // Total session duration
  "exit_status": "string",         // One of: "completed", "partial_success", "failed", "aborted", "timed_out"
  "teams_executed": integer,       // Number of teams executed in this session
  "total_agents_spawned": integer, // Total agents spawned across all teams
  "total_tokens_consumed": integer, // Total tokens consumed across all agents
  "total_estimated_cost_usd": float, // Total estimated cost in USD
  "telemetry_events_logged": integer, // Total number of telemetry events logged
  "log_file_size_bytes": integer   // Size of the telemetry log file in bytes
}
```

**Example**:
```
2026-02-12T14:30:49.700Z | environment | testing-coordinator | session_end | {"session_id":"sess_abc123","total_duration_seconds":54.7,"exit_status":"completed","teams_executed":1,"total_agents_spawned":4,"total_tokens_consumed":5000,"total_estimated_cost_usd":0.036,"telemetry_events_logged":42,"log_file_size_bytes":18500}
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

### Example 4: Verbose Team Execution (All Event Types)

```
2026-02-12T14:29:58.000Z | config | testing-coordinator | config_loaded | {"team_name":"testing-parallel","file_path":"teams/testing-parallel.md","frontmatter_raw":{"max_agents":5,"timeout":1800,"gates":{"before_execution":true}},"file_size_bytes":2048,"parse_duration_ms":3.2}
2026-02-12T14:29:58.500Z | config | testing-coordinator | config_override_applied | {"field":"max_agents","original_value":"5","override_value":"3","source":"cli","override_key":"--max-agents"}
2026-02-12T14:29:58.600Z | config | testing-coordinator | config_defaults_applied | {"fields_defaulted":["retry_count"],"defaults_applied":{"retry_count":3}}
2026-02-12T14:29:59.000Z | config | testing-coordinator | model_resolved | {"agent_name":"write-agent-1","resolved_model":"sonnet","resolution_source":"team_config","timeout_seconds":120,"precedence_chain":[{"source":"cli","not_set":true},{"source":"team_config","value":"sonnet"}]}
2026-02-12T14:30:00.000Z | dependency | testing-coordinator | graph_constructed | {"adjacency_list":{"execute-agent":["write-agent-1","write-agent-2"],"write-agent-1":[],"write-agent-2":[]},"topological_order":["write-agent-1","write-agent-2","execute-agent"],"total_nodes":3,"total_edges":2,"has_cycles":false}
2026-02-12T14:30:00.100Z | dependency | testing-coordinator | phase_planned | {"phase_number":1,"agents":["write-agent-1","write-agent-2"],"parallel":true,"blocked_by":[],"estimated_duration_seconds":30.0}
2026-02-12T14:30:00.200Z | dependency | testing-coordinator | phase_planned | {"phase_number":2,"agents":["execute-agent"],"parallel":false,"blocked_by":["write-agent-1","write-agent-2"],"estimated_duration_seconds":15.0}
2026-02-12T14:30:01.000Z | lifecycle | testing-coordinator | spawned | {"parent":"test-loop-orchestrator","depth":1,"team_id":"testing-parallel","team_config_snapshot":{"max_agents":3,"timeout":1800,"gates":{"before_execution":true},"retry_count":3},"cli_overrides":{"max_agents":3},"coordinator_path":"agents/testing-coordinator.md"}
2026-02-12T14:30:01.400Z | approval | testing-coordinator | gate_entered | {"gate_type":"before_execution","iteration":1,"max_iterations":3,"gates_config":{"before_execution":true,"after_completion":false},"context_summary":"2 write-agents planned for 8 test targets"}
2026-02-12T14:30:01.450Z | approval | testing-coordinator | prompt_displayed | {"gate_type":"before_execution","prompt_text":"Plan: 2 parallel write-agents will generate tests for 8 files. Approve?","prompt_length_chars":75,"options_presented":["approve","reject","modify"]}
2026-02-12T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"2 parallel write-agents","batches":2,"total_targets":8,"approval_required":true,"full_plan":{"phases":[{"phase":1,"agents":["write-agent-1","write-agent-2"]},{"phase":2,"agents":["execute-agent"]}]},"dependency_graph":{"execute-agent":["write-agent-1","write-agent-2"]},"agent_composition":[{"name":"write-agent-1","type":"agents/write-agent.md","critical":false,"max_instances":1},{"name":"write-agent-2","type":"agents/write-agent.md","critical":false,"max_instances":1},{"name":"execute-agent","type":"agents/execute-agent.md","critical":true,"max_instances":1}],"resource_estimate":{"estimated_tokens":15000,"estimated_minutes":2,"agent_count":3,"max_concurrent":2}}
2026-02-12T14:30:15.789Z | approval | testing-coordinator | user_response_received | {"gate_type":"before_execution","decision":"approve","feedback_text":null,"response_time_seconds":14.3,"iteration":1}
2026-02-12T14:30:15.789Z | coordination | testing-coordinator | plan_approved | {"user_response":"approve","batches":2,"approval_time_seconds":14.3}
2026-02-12T14:30:16.000Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2,"team_id":"testing-parallel","team_config_snapshot":{"max_agents":3},"cli_overrides":{},"coordinator_path":"agents/testing-coordinator.md"}
2026-02-12T14:30:16.050Z | agent_io | write-agent-1 | prompt_constructed | {"agent_id":"write-agent-1","prompt_text":"Generate pytest tests for src/user_service.py covering all public methods...","prompt_length_chars":4500,"prompt_estimated_tokens":1125,"model":"sonnet","includes_context":false}
2026-02-12T14:30:16.100Z | lifecycle | write-agent-2 | spawned | {"parent":"testing-coordinator","depth":2,"team_id":"testing-parallel","team_config_snapshot":{"max_agents":3},"cli_overrides":{},"coordinator_path":"agents/testing-coordinator.md"}
2026-02-12T14:30:16.300Z | coordination | testing-coordinator | parallel_execution_start | {"active_agents":2,"max_agents":3,"agent_ids":["write-agent-1","write-agent-2"]}
2026-02-12T14:30:17.000Z | agent_io | write-agent-1 | file_read | {"agent_id":"write-agent-1","file_path":"src/user_service.py","size_bytes":3800,"line_count":120,"read_duration_ms":1.5}
2026-02-12T14:30:20.000Z | progress | write-agent-1 | update | {"tests_written":2,"current_file":"test_user_service.py","percent_complete":40}
2026-02-12T14:30:25.000Z | dependency | testing-coordinator | dependency_waiting | {"agent":"execute-agent","waiting_for":["write-agent-1","write-agent-2"],"resolved":[],"remaining":["write-agent-1","write-agent-2"],"wait_start_timestamp":"2026-02-12T14:30:16.300Z"}
2026-02-12T14:30:29.500Z | agent_io | write-agent-1 | output_received | {"agent_id":"write-agent-1","output_text":"import pytest\\nfrom user_service import UserService...","output_length_chars":3200,"output_estimated_tokens":800,"duration_seconds":13.4}
2026-02-12T14:30:29.600Z | agent_io | write-agent-1 | output_parsed | {"agent_id":"write-agent-1","parsed_fields":["test_file","test_count","framework"],"parse_success":true,"parse_errors":[],"structured_output":{"test_file":"test_user_service.py","test_count":5,"framework":"pytest"}}
2026-02-12T14:30:29.700Z | agent_io | write-agent-1 | file_written | {"agent_id":"write-agent-1","file_path":"tests/test_user_service.py","operation":"create","size_bytes":4200,"line_count":145,"encoding":"utf-8"}
2026-02-12T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":13.7,"output_summary":"5 tests generated","tests_generated":5,"output_full":{"test_file":"test_user_service.py","tests":["test_create_user","test_delete_user","test_update_user","test_get_user","test_list_users"]},"files_created":["test_user_service.py (145 lines)"],"files_modified":[],"token_usage":{"input_tokens":1125,"output_tokens":800,"cache_read":200,"cache_write":100},"model_used":"sonnet","retry_count":0}
2026-02-12T14:30:30.000Z | resource | write-agent-1 | token_usage | {"agent_id":"write-agent-1","input_tokens":1125,"output_tokens":800,"total_tokens":1925,"cache_read_tokens":200,"cache_write_tokens":100,"model":"sonnet","cost_estimate_usd":0.012,"context_window_utilization":0.02,"prompt_tokens_breakdown":{"system_tokens":300,"user_tokens":725,"assistant_tokens":100}}
2026-02-12T14:30:30.000Z | dependency | testing-coordinator | dependency_satisfied | {"agent":"execute-agent","dependency":"write-agent-1","resolution_duration_seconds":13.7,"unblocked_agents":[]}
2026-02-12T14:30:33.000Z | lifecycle | write-agent-2 | completed | {"duration_seconds":16.9,"output_summary":"4 tests generated","tests_generated":4,"output_full":{"test_file":"test_auth_login.py","tests":["test_login_success","test_login_failure","test_token_refresh","test_logout"]},"files_created":["test_auth_login.py (110 lines)"],"files_modified":[],"token_usage":{"input_tokens":1050,"output_tokens":700,"cache_read":180,"cache_write":90},"model_used":"sonnet","retry_count":0}
2026-02-12T14:30:33.000Z | dependency | testing-coordinator | dependency_satisfied | {"agent":"execute-agent","dependency":"write-agent-2","resolution_duration_seconds":16.9,"unblocked_agents":["execute-agent"]}
2026-02-12T14:30:33.500Z | coordination | testing-coordinator | parallel_execution_complete | {"total_tests":9,"successful_agents":2,"failed_agents":0,"duration_seconds":17.2}
2026-02-12T14:30:33.600Z | coordination | testing-coordinator | dependencies_resolved | {"agent":"execute-agent","waited_for":["write-agent-1","write-agent-2"]}
2026-02-12T14:30:34.000Z | lifecycle | execute-agent | spawned | {"parent":"testing-coordinator","depth":2,"team_id":"testing-parallel","team_config_snapshot":{"max_agents":3},"cli_overrides":{},"coordinator_path":"agents/testing-coordinator.md"}
2026-02-12T14:30:40.000Z | test | execute-agent | execution_start | {"framework":"pytest","test_count":9,"command":"pytest tests/","target_path":"D:/dev/project/tests"}
2026-02-12T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":9,"failed":0,"skipped":0,"duration_seconds":8.5,"pass_rate":1.0}
2026-02-12T14:30:49.000Z | lifecycle | execute-agent | completed | {"duration_seconds":15.0,"output_summary":"All 9 tests passed","output_full":{"passed":9,"failed":0,"details":[]},"files_created":[],"files_modified":[],"token_usage":{"input_tokens":900,"output_tokens":400,"cache_read":150,"cache_write":50},"model_used":"sonnet","retry_count":0}
2026-02-12T14:30:49.500Z | lifecycle | testing-coordinator | completed | {"duration_seconds":51.5,"output_summary":"9 tests generated and all passing","total_tests":9,"output_full":{"agents_completed":3,"total_tests":9,"pass_rate":1.0},"files_created":["test_user_service.py (145 lines)","test_auth_login.py (110 lines)"],"files_modified":[],"token_usage":{"input_tokens":3075,"output_tokens":1900,"cache_read":530,"cache_write":240},"model_used":"sonnet","retry_count":0}
```

---

### Example 5: Verbose Test Execution with Per-Test Telemetry

```
2026-02-12T14:30:38.000Z | test | execute-agent | suite_discovered | {"framework":"pytest","suite_name":"test_user_service","test_count":5,"file_path":"tests/test_user_service.py","discovery_duration_ms":45.2,"parametrized_count":1,"markers":["unit"]}
2026-02-12T14:30:38.100Z | test | execute-agent | suite_discovered | {"framework":"pytest","suite_name":"test_auth_login","test_count":4,"file_path":"tests/test_auth_login.py","discovery_duration_ms":32.1,"parametrized_count":0,"markers":["unit","auth"]}
2026-02-12T14:30:39.800Z | test | execute-agent | test_fixture_setup | {"fixture_name":"db_session","scope":"module","duration_seconds":0.25,"success":true,"error":null}
2026-02-12T14:30:40.000Z | test | execute-agent | execution_start | {"framework":"pytest","test_count":9,"command":"pytest tests/ --cov=src --cov-branch","target_path":"D:/dev/project/tests"}
2026-02-12T14:30:40.100Z | test | execute-agent | test_case_start | {"test_name":"test_user_service.py::TestUserService::test_create_user","test_file":"tests/test_user_service.py","test_class":"TestUserService","parametrize_id":null,"markers":["unit"],"fixtures":["db_session"]}
2026-02-12T14:30:40.200Z | test | execute-agent | test_fixture_setup | {"fixture_name":"mock_email","scope":"function","duration_seconds":0.01,"success":true,"error":null}
2026-02-12T14:30:40.500Z | test | execute-agent | test_case_result | {"test_name":"test_user_service.py::TestUserService::test_create_user","test_file":"tests/test_user_service.py","status":"passed","duration_seconds":0.045,"failure_message":null,"failure_traceback":null,"stdout_capture":null,"stderr_capture":null,"assertions_checked":3}
2026-02-12T14:30:40.550Z | test | execute-agent | test_fixture_teardown | {"fixture_name":"mock_email","scope":"function","duration_seconds":0.005,"success":true,"error":null}
2026-02-12T14:30:40.600Z | test | execute-agent | test_case_start | {"test_name":"test_user_service.py::TestUserService::test_delete_user","test_file":"tests/test_user_service.py","test_class":"TestUserService","parametrize_id":null,"markers":["unit"],"fixtures":["db_session"]}
2026-02-12T14:30:40.900Z | test | execute-agent | test_case_result | {"test_name":"test_user_service.py::TestUserService::test_delete_user","test_file":"tests/test_user_service.py","status":"passed","duration_seconds":0.032,"failure_message":null,"failure_traceback":null,"stdout_capture":null,"stderr_capture":null,"assertions_checked":2}
2026-02-12T14:30:41.000Z | test | execute-agent | test_case_start | {"test_name":"test_user_service.py::TestUserService::test_concurrent_update[scenario0]","test_file":"tests/test_user_service.py","test_class":"TestUserService","parametrize_id":"scenario0","markers":["unit"],"fixtures":["db_session"]}
2026-02-12T14:30:41.800Z | test | execute-agent | test_case_result | {"test_name":"test_user_service.py::TestUserService::test_concurrent_update[scenario0]","test_file":"tests/test_user_service.py","status":"failed","duration_seconds":0.8,"failure_message":"AssertionError: expected 200, got 503","failure_traceback":"tests/test_user_service.py:45: AssertionError","stdout_capture":null,"stderr_capture":"WARNING: connection pool exhausted","assertions_checked":1}
2026-02-12T14:30:41.900Z | test | execute-agent | test_output_captured | {"test_name":"test_user_service.py::TestUserService::test_concurrent_update[scenario0]","stream":"stderr","content":"WARNING: connection pool exhausted","content_length_chars":35}
2026-02-12T14:30:42.000Z | test | execute-agent | test_retry | {"test_name":"test_user_service.py::TestUserService::test_concurrent_update[scenario0]","retry_count":1,"max_retries":2,"previous_status":"failed","previous_error":"AssertionError: expected 200, got 503"}
2026-02-12T14:30:42.900Z | test | execute-agent | test_case_result | {"test_name":"test_user_service.py::TestUserService::test_concurrent_update[scenario0]","test_file":"tests/test_user_service.py","status":"passed","duration_seconds":0.85,"failure_message":null,"failure_traceback":null,"stdout_capture":null,"stderr_capture":null,"assertions_checked":1}
2026-02-12T14:30:47.500Z | test | execute-agent | test_fixture_teardown | {"fixture_name":"db_session","scope":"module","duration_seconds":0.08,"success":true,"error":null}
2026-02-12T14:30:48.500Z | test | execute-agent | execution_complete | {"passed":8,"failed":0,"skipped":1,"duration_seconds":8.5,"pass_rate":0.89}
2026-02-12T14:30:48.600Z | test | execute-agent | coverage_report | {"total_statements":450,"covered_statements":410,"missing_statements":40,"coverage_percent":91.1,"branch_coverage_percent":85.3,"uncovered_lines":{"src/user_service.py":[45,67,89],"src/auth/login.py":[112,115]},"files_covered":8,"files_total":10}
2026-02-12T14:30:48.700Z | test | execute-agent | test_summary | {"total":9,"passed":8,"failed":0,"skipped":1,"errors":0,"xfailed":0,"xpassed":0,"duration_seconds":8.5,"pass_rate":0.89,"slowest_tests":[{"name":"test_concurrent_update[scenario0]","duration_seconds":0.85},{"name":"test_bulk_import","duration_seconds":0.6}],"failure_categories":{}}
```

---

## Common Required Fields

Every telemetry event, regardless of type, MUST include these five fields in the pipe-delimited log line. These fields form the event envelope and are required for parsing, filtering, and correlation.

### Field Specification

| Field | Type | Format | Description | Example |
|-------|------|--------|-------------|---------|
| `timestamp` | string | ISO 8601 UTC with milliseconds | When the event occurred | `2026-02-12T14:30:01.123Z` |
| `event_type` | string | One of 14 valid types | Category of event | `lifecycle` |
| `agent_id` | string | Alphanumeric with dashes | Which agent emitted the event | `write-agent-1` |
| `status` | string | Event-type-specific | What happened | `spawned` |
| `metadata` | object | Valid JSON | Event-specific payload | `{"parent":"coordinator"}` |

### Additional Required Metadata Fields

The following fields MUST be present inside the `metadata` JSON object for ALL events. Coordinators and agents MUST include these when calling `log_telemetry()`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `team_id` | string | **Required** | Team identifier (e.g., `testing-parallel`) |

**Note**: `timestamp`, `event_type`, `agent_id`, and `status` are top-level pipe-delimited fields, not metadata fields. The `team_id` is the only universally required metadata field. Individual event types define additional required and optional metadata fields in their schema sections above.

### Valid Event Types

The `event_type` field MUST be one of these 14 values:

```
lifecycle | coordination | progress | test | resource | config |
dependency | agent_io | approval | timing | error | cost |
data_flow | environment
```

Any other value MUST be rejected by `validate_event()`.

### Valid Status Values by Event Type

Each event type constrains its status values. See the individual event type sections above for the complete list. The `validate_event()` function enforces these constraints.

---

## Standard Log Line Format Specification

### Format

```
[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
```

### Parsing Rules

1. **Delimiter**: ` | ` (space, pipe, space) -- exactly 3 characters
2. **Field count**: Exactly 5 fields after splitting on the delimiter
3. **Timestamp field**: Must match `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z`
4. **Event type field**: Must be one of the 14 valid event types
5. **Agent ID field**: Non-empty string, no pipe characters, no spaces
6. **Status field**: Non-empty string, no pipe characters
7. **Metadata field**: Must be valid JSON (parseable by `json.loads()`)
8. **Line terminator**: Single newline (`\n`) -- no `\r\n`
9. **Encoding**: UTF-8
10. **Max line length**: 64KB (events exceeding this should truncate metadata)

### Parsing Implementation

```python
import json
import re

LOG_LINE_REGEX = re.compile(
    r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)'  # timestamp
    r' \| '                                                 # delimiter
    r'(\w+)'                                                # event_type
    r' \| '                                                 # delimiter
    r'([^ |]+)'                                             # agent_id
    r' \| '                                                 # delimiter
    r'([^ |]+)'                                             # status
    r' \| '                                                 # delimiter
    r'(\{.*\})$'                                            # metadata_json
)


def parse_log_line(line: str) -> dict:
    """
    Parse a single telemetry log line into its components.

    Args:
        line: Raw log line string (stripped of newline)

    Returns:
        dict with keys: timestamp, event_type, agent_id, status, metadata

    Raises:
        ValueError: If line does not match expected format
    """
    line = line.strip()

    # Skip header lines (comments and separator)
    if line.startswith('#') or line == '---' or not line:
        return None

    match = LOG_LINE_REGEX.match(line)
    if not match:
        raise ValueError(f"Line does not match telemetry format: {line[:80]}...")

    timestamp, event_type, agent_id, status, metadata_json = match.groups()

    # Parse metadata JSON
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid metadata JSON: {e}")

    return {
        'timestamp': timestamp,
        'event_type': event_type,
        'agent_id': agent_id,
        'status': status,
        'metadata': metadata
    }
```

---

## Terminal Events: TEAM_COMPLETE and TEAM_FAILED

### Problem: Incomplete Log Files

In the `sample_teams_project` testing, log files were found without terminal events. When a team execution ends (whether successfully or due to failure), the log file had no definitive "end" marker. This makes it impossible for log analyzers to determine whether:

1. The team completed successfully
2. The team failed
3. The log file was truncated due to a crash
4. The execution is still in progress

### Solution: Mandatory Terminal Events

Every team execution MUST write exactly one of these two terminal events as the **last event** in the log file. Coordinators MUST emit one of these before exiting, even in error paths.

### TEAM_COMPLETE

**When**: Team execution finishes successfully (all agents completed, all phases done)

**Event Type**: `lifecycle`
**Status**: `team_complete`
**Agent ID**: The coordinator agent ID

**Metadata Schema**:
```json
{
  "team_id": "string",                   // REQUIRED: Team identifier
  "team_name": "string",                 // REQUIRED: Human-readable team name
  "total_duration_seconds": float,       // REQUIRED: Wall clock time from session_start to now
  "total_agents_spawned": integer,       // REQUIRED: How many agents were created
  "agents_succeeded": integer,           // REQUIRED: How many agents completed successfully
  "agents_failed": integer,              // REQUIRED: How many agents failed (should be 0)
  "total_phases": integer,               // REQUIRED: Number of execution phases
  "total_tests_passed": integer,         // OPTIONAL: Total tests passed (if test team)
  "total_tests_failed": integer,         // OPTIONAL: Total tests failed (if test team)
  "total_tokens_consumed": integer,      // REQUIRED: Sum of all agent token usage
  "total_estimated_cost_usd": float,     // REQUIRED: Sum of all agent cost estimates
  "exit_code": 0,                        // REQUIRED: Always 0 for successful completion
  "files_created": ["string"],           // OPTIONAL: List of files created during execution
  "files_modified": ["string"],          // OPTIONAL: List of files modified during execution
  "telemetry_events_logged": integer,    // REQUIRED: Total event count in this log file
  "log_file_path": "string"             // REQUIRED: Absolute path to this log file
}
```

**Example**:
```
2026-02-12T14:30:49.500Z | lifecycle | testing-coordinator | team_complete | {"team_id":"testing-parallel","team_name":"testing-parallel","total_duration_seconds":51.5,"total_agents_spawned":4,"agents_succeeded":4,"agents_failed":0,"total_phases":2,"total_tests_passed":9,"total_tests_failed":0,"total_tokens_consumed":5745,"total_estimated_cost_usd":0.036,"exit_code":0,"files_created":["test_user_service.py","test_auth_login.py"],"files_modified":[],"telemetry_events_logged":93,"log_file_path":"D:/dev/project/.claude/telemetry-2026-02-12T14-30-00.log"}
```

**Validation Rules**:
- `exit_code` MUST be `0`
- `agents_failed` MUST be `0`
- `agents_succeeded` + `agents_failed` MUST equal `total_agents_spawned`
- Must be preceded by a `session_end` environment event (or emitted alongside it)

---

### TEAM_FAILED

**When**: Team execution fails (unrecoverable error, timeout, too many agent failures, user abort)

**Event Type**: `lifecycle`
**Status**: `team_failed`
**Agent ID**: The coordinator agent ID

**Metadata Schema**:
```json
{
  "team_id": "string",                   // REQUIRED: Team identifier
  "team_name": "string",                 // REQUIRED: Human-readable team name
  "total_duration_seconds": float,       // REQUIRED: Wall clock time from session_start to now
  "total_agents_spawned": integer,       // REQUIRED: How many agents were created
  "agents_succeeded": integer,           // REQUIRED: How many agents completed successfully
  "agents_failed": integer,              // REQUIRED: How many agents failed
  "failure_reason": "string",            // REQUIRED: Human-readable failure reason
  "failure_category": "string",          // REQUIRED: One of: "timeout", "agent_failure",
                                         //   "validation_error", "user_abort", "resource_limit",
                                         //   "dependency_cycle", "crash", "unknown"
  "failed_agents": [                     // REQUIRED: Details of each failed agent
    {
      "agent_id": "string",
      "error": "string",
      "retries_attempted": integer
    }
  ],
  "phase_reached": integer,              // REQUIRED: Last phase that started execution
  "total_phases_planned": integer,       // REQUIRED: Total phases in the plan
  "total_tokens_consumed": integer,      // REQUIRED: Sum of all agent token usage
  "total_estimated_cost_usd": float,     // REQUIRED: Sum of all agent cost estimates
  "exit_code": integer,                  // REQUIRED: Non-zero exit code
  "partial_results": {                   // OPTIONAL: Any partial work completed
    "files_created": ["string"],
    "tests_passed": integer,
    "tests_failed": integer
  },
  "telemetry_events_logged": integer,    // REQUIRED: Total event count in this log file
  "log_file_path": "string"             // REQUIRED: Absolute path to this log file
}
```

**Example**:
```
2026-02-12T14:32:05.000Z | lifecycle | testing-coordinator | team_failed | {"team_id":"testing-parallel","team_name":"testing-parallel","total_duration_seconds":125.0,"total_agents_spawned":4,"agents_succeeded":2,"agents_failed":2,"failure_reason":"2 agents exceeded timeout (120s)","failure_category":"timeout","failed_agents":[{"agent_id":"write-agent-2","error":"Agent exceeded 120s timeout","retries_attempted":3},{"agent_id":"write-agent-3","error":"Agent exceeded 120s timeout","retries_attempted":3}],"phase_reached":1,"total_phases_planned":2,"total_tokens_consumed":3200,"total_estimated_cost_usd":0.021,"exit_code":1,"partial_results":{"files_created":["test_user_service.py"],"tests_passed":0,"tests_failed":0},"telemetry_events_logged":67,"log_file_path":"D:/dev/project/.claude/telemetry-2026-02-12T14-30-00.log"}
```

**Validation Rules**:
- `exit_code` MUST be non-zero (1 or higher)
- `failure_reason` MUST be non-empty
- `failure_category` MUST be one of the allowed values
- `failed_agents` array MUST have at least one entry (unless `failure_category` is `user_abort` or `crash`)
- `agents_succeeded` + `agents_failed` MUST equal `total_agents_spawned`

---

### Coordinator Implementation Pattern

Coordinators MUST use a try/finally pattern to guarantee terminal event emission:

```python
def run_team(team_def, project_root):
    """
    Execute team orchestration with guaranteed terminal event.

    The terminal event (team_complete or team_failed) is written in a finally
    block to ensure it is always emitted, even on unexpected errors.
    """
    session_start_time = time.time()
    agents_spawned = 0
    agents_succeeded = 0
    agents_failed = 0
    event_count = 0
    failure_reason = None
    failure_category = None
    failed_agents = []

    try:
        # ... normal team orchestration logic ...
        # (spawn agents, coordinate phases, collect results)

        # If we reach here, team completed successfully
        duration = time.time() - session_start_time

        log_telemetry(
            event_type="lifecycle",
            agent_id=coordinator_id,
            status="team_complete",
            metadata={
                "team_id": team_def['name'],
                "team_name": team_def['name'],
                "total_duration_seconds": round(duration, 2),
                "total_agents_spawned": agents_spawned,
                "agents_succeeded": agents_succeeded,
                "agents_failed": 0,
                "total_phases": total_phases,
                "total_tokens_consumed": total_tokens,
                "total_estimated_cost_usd": total_cost,
                "exit_code": 0,
                "telemetry_events_logged": event_count + 1,
                "log_file_path": log_file_path
            },
            project_root=project_root,
            team_name=team_def['name']
        )

    except Exception as e:
        # Team failed -- emit terminal failure event
        duration = time.time() - session_start_time

        log_telemetry(
            event_type="lifecycle",
            agent_id=coordinator_id,
            status="team_failed",
            metadata={
                "team_id": team_def['name'],
                "team_name": team_def['name'],
                "total_duration_seconds": round(duration, 2),
                "total_agents_spawned": agents_spawned,
                "agents_succeeded": agents_succeeded,
                "agents_failed": agents_failed,
                "failure_reason": str(e),
                "failure_category": classify_error(e),
                "failed_agents": failed_agents,
                "phase_reached": current_phase,
                "total_phases_planned": total_phases,
                "total_tokens_consumed": total_tokens,
                "total_estimated_cost_usd": total_cost,
                "exit_code": 1,
                "telemetry_events_logged": event_count + 1,
                "log_file_path": log_file_path
            },
            project_root=project_root,
            team_name=team_def['name']
        )
        raise  # Re-raise after logging
```

### Detecting Incomplete Logs

A log file is considered **incomplete** (possible crash) if:

1. It has a `session_start` environment event but no `team_complete` or `team_failed` lifecycle event
2. The last event timestamp is more than `timeout_minutes` before the current time
3. There is no event with status `team_complete` or `team_failed` anywhere in the file

Log analysis tools SHOULD check for this condition and report it:

```python
def check_log_completeness(log_file_path: str) -> dict:
    """
    Check whether a telemetry log file has a proper terminal event.

    Returns:
        dict with keys:
            complete: bool -- True if terminal event found
            terminal_status: str or None -- "team_complete" or "team_failed"
            last_event_timestamp: str or None -- timestamp of last event
            event_count: int -- total events in file
    """
    terminal_status = None
    last_timestamp = None
    event_count = 0

    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or line == '---' or not line:
                continue

            event_count += 1
            parsed = parse_log_line(line)
            if parsed:
                last_timestamp = parsed['timestamp']
                if parsed['status'] in ('team_complete', 'team_failed'):
                    terminal_status = parsed['status']

    return {
        'complete': terminal_status is not None,
        'terminal_status': terminal_status,
        'last_event_timestamp': last_timestamp,
        'event_count': event_count
    }
```

---

## Event Validation

### validate_event() Function

The `validate_event()` function validates any telemetry event against its schema. It checks the event envelope (common fields) and the event-specific metadata.

```python
import json
import re
from datetime import datetime


# --- Constants ---

VALID_EVENT_TYPES = {
    'lifecycle', 'coordination', 'progress', 'test', 'resource', 'config',
    'dependency', 'agent_io', 'approval', 'timing', 'error', 'cost',
    'data_flow', 'environment'
}

VALID_STATUSES = {
    'lifecycle': {
        'spawned', 'start', 'completed', 'failed',
        'team_complete', 'team_failed'
    },
    'coordination': {
        'plan_proposed', 'plan_approved', 'plan_rejected',
        'task_assigned', 'dependencies_resolved',
        'parallel_execution_start', 'parallel_execution_complete'
    },
    'progress': {
        'update', 'milestone_reached'
    },
    'test': {
        'suite_discovered', 'execution_start', 'execution_complete',
        'test_case_start', 'test_case_result', 'test_fixture_setup',
        'test_fixture_teardown', 'coverage_report', 'test_output_captured',
        'test_retry', 'test_summary'
    },
    'resource': {
        'queue_status', 'timeout_warning', 'timeout', 'limit_reached',
        'token_usage', 'agent_queued', 'agent_dequeued'
    },
    'config': {
        'config_loaded', 'config_override_applied',
        'config_defaults_applied', 'model_resolved'
    },
    'dependency': {
        'graph_constructed', 'phase_planned', 'dependency_waiting',
        'dependency_satisfied'
    },
    'agent_io': {
        'prompt_constructed', 'output_received', 'output_parsed',
        'file_written', 'file_read'
    },
    'approval': {
        'gate_entered', 'prompt_displayed', 'user_response_received',
        'plan_regenerated'
    },
    'timing': {
        'phase_transition', 'queue_wait_time', 'backoff_wait',
        'overhead_summary'
    },
    'error': {
        'validation_check', 'state_transition', 'retry_decision',
        'error_classified'
    },
    'cost': {
        'memory_snapshot', 'cumulative_cost', 'model_fallback',
        'utilization_snapshot'
    },
    'data_flow': {
        'data_passed', 'file_conflict_check', 'plan_diff', 'agent_message'
    },
    'environment': {
        'session_start', 'session_end', 'environment_snapshot'
    }
}

TIMESTAMP_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')

# Required metadata fields per (event_type, status) pair.
# Fields listed here MUST be present in metadata. All other fields are optional.
REQUIRED_METADATA = {
    # Lifecycle
    ('lifecycle', 'spawned'): ['parent', 'depth'],
    ('lifecycle', 'start'): ['assigned_task'],
    ('lifecycle', 'completed'): ['duration_seconds'],
    ('lifecycle', 'failed'): ['reason', 'retries'],
    ('lifecycle', 'team_complete'): [
        'team_id', 'team_name', 'total_duration_seconds',
        'total_agents_spawned', 'agents_succeeded', 'agents_failed',
        'total_phases', 'total_tokens_consumed', 'total_estimated_cost_usd',
        'exit_code', 'telemetry_events_logged', 'log_file_path'
    ],
    ('lifecycle', 'team_failed'): [
        'team_id', 'team_name', 'total_duration_seconds',
        'total_agents_spawned', 'agents_succeeded', 'agents_failed',
        'failure_reason', 'failure_category', 'failed_agents',
        'phase_reached', 'total_phases_planned',
        'total_tokens_consumed', 'total_estimated_cost_usd',
        'exit_code', 'telemetry_events_logged', 'log_file_path'
    ],

    # Coordination
    ('coordination', 'plan_proposed'): ['plan_summary', 'approval_required'],
    ('coordination', 'plan_approved'): ['user_response'],
    ('coordination', 'plan_rejected'): ['user_response', 'rejection_reason'],
    ('coordination', 'task_assigned'): ['agent_id', 'task_description'],
    ('coordination', 'parallel_execution_start'): ['active_agents', 'max_agents'],
    ('coordination', 'parallel_execution_complete'): ['successful_agents', 'failed_agents'],

    # Progress
    ('progress', 'update'): ['percent_complete'],
    ('progress', 'milestone_reached'): ['milestone_name'],

    # Test
    ('test', 'suite_discovered'): ['framework', 'suite_name', 'test_count'],
    ('test', 'execution_start'): ['framework', 'test_count'],
    ('test', 'execution_complete'): ['passed', 'failed', 'duration_seconds'],
    ('test', 'test_case_result'): ['test_name', 'status', 'duration_seconds'],
    ('test', 'coverage_report'): ['coverage_percent'],
    ('test', 'test_retry'): ['test_name', 'retry_count', 'previous_status'],
    ('test', 'test_summary'): ['total', 'passed', 'failed', 'duration_seconds'],

    # Resource
    ('resource', 'queue_status'): ['active_agents', 'queued_agents', 'max_agents'],
    ('resource', 'timeout_warning'): ['agent_id', 'elapsed_seconds', 'timeout_seconds'],
    ('resource', 'limit_reached'): ['limit_type', 'current', 'max'],
    ('resource', 'token_usage'): [
        'agent_id', 'input_tokens', 'output_tokens', 'total_tokens', 'model'
    ],

    # Config
    ('config', 'config_loaded'): ['team_name', 'file_path'],
    ('config', 'config_override_applied'): ['field', 'original_value', 'override_value', 'source'],
    ('config', 'config_defaults_applied'): ['fields_defaulted', 'defaults_applied'],
    ('config', 'model_resolved'): ['agent_name', 'resolved_model', 'resolution_source'],

    # Dependency
    ('dependency', 'graph_constructed'): ['adjacency_list', 'topological_order', 'total_nodes', 'has_cycles'],
    ('dependency', 'phase_planned'): ['phase_number', 'agents'],
    ('dependency', 'dependency_waiting'): ['agent', 'waiting_for'],
    ('dependency', 'dependency_satisfied'): ['agent', 'dependency'],

    # Agent I/O
    ('agent_io', 'prompt_constructed'): ['agent_id', 'prompt_length_chars', 'model'],
    ('agent_io', 'output_received'): ['agent_id', 'output_length_chars'],
    ('agent_io', 'file_written'): ['agent_id', 'file_path', 'operation'],
    ('agent_io', 'file_read'): ['agent_id', 'file_path'],

    # Approval
    ('approval', 'gate_entered'): ['gate_type', 'iteration'],
    ('approval', 'user_response_received'): ['gate_type', 'decision'],
    ('approval', 'plan_regenerated'): ['gate_type', 'iteration', 'changes_summary'],

    # Timing
    ('timing', 'phase_transition'): ['from_phase', 'to_phase', 'transition_duration_seconds'],
    ('timing', 'queue_wait_time'): ['agent_id', 'wait_duration_seconds'],
    ('timing', 'backoff_wait'): ['agent_id', 'backoff_seconds', 'retry_count'],
    ('timing', 'overhead_summary'): [
        'total_wall_clock_seconds', 'total_agent_work_seconds', 'framework_tax_percent'
    ],

    # Error
    ('error', 'validation_check'): ['check_name', 'passed'],
    ('error', 'state_transition'): ['agent_id', 'from_state', 'to_state'],
    ('error', 'retry_decision'): ['agent_id', 'will_retry', 'retry_count'],
    ('error', 'error_classified'): ['error_category', 'classified_severity'],

    # Cost
    ('cost', 'memory_snapshot'): ['agent_id', 'snapshot_type'],
    ('cost', 'cumulative_cost'): ['team_id', 'estimated_cost_usd', 'agents_completed'],
    ('cost', 'model_fallback'): ['agent_id', 'from_model', 'to_model', 'reason'],
    ('cost', 'utilization_snapshot'): ['active_agents', 'max_agents'],

    # Data Flow
    ('data_flow', 'data_passed'): ['from_phase', 'to_phase', 'data_size_chars'],
    ('data_flow', 'file_conflict_check'): ['files_checked'],
    ('data_flow', 'plan_diff'): ['original_plan_hash', 'modified_plan_hash'],
    ('data_flow', 'agent_message'): ['from_agent', 'to_agent'],

    # Environment
    ('environment', 'session_start'): ['session_id', 'plugin_version', 'platform'],
    ('environment', 'session_end'): ['session_id', 'total_duration_seconds', 'exit_status'],
    ('environment', 'environment_snapshot'): ['teamsters_env_vars']
}

VALID_FAILURE_CATEGORIES = {
    'timeout', 'agent_failure', 'validation_error', 'user_abort',
    'resource_limit', 'dependency_cycle', 'crash', 'unknown'
}


# --- Validation Function ---

def validate_event(event) -> dict:
    """
    Validate a telemetry event against its schema.

    Accepts either a raw log line (string) or a pre-parsed event dict.

    Args:
        event: Either a string (raw log line) or a dict with keys:
               timestamp, event_type, agent_id, status, metadata

    Returns:
        dict:
            valid: bool -- True if event passes all checks
            errors: list[str] -- List of validation error messages (empty if valid)
            warnings: list[str] -- List of non-fatal warnings

    Usage:
        # Validate a raw log line
        result = validate_event(
            "2026-02-12T14:30:01.123Z | lifecycle | write-agent-1 | spawned | "
            '{"parent":"coordinator","depth":2,"team_id":"my-team"}'
        )
        assert result['valid']
        assert result['errors'] == []

        # Validate a pre-parsed event
        result = validate_event({
            'timestamp': '2026-02-12T14:30:01.123Z',
            'event_type': 'lifecycle',
            'agent_id': 'write-agent-1',
            'status': 'spawned',
            'metadata': {'parent': 'coordinator', 'depth': 2, 'team_id': 'my-team'}
        })
        assert result['valid']
    """
    errors = []
    warnings = []

    # --- Step 1: Parse if string ---
    if isinstance(event, str):
        try:
            parsed = parse_log_line(event)
            if parsed is None:
                return {'valid': True, 'errors': [], 'warnings': ['Header or blank line, skipped']}
        except ValueError as e:
            return {'valid': False, 'errors': [str(e)], 'warnings': []}
    elif isinstance(event, dict):
        parsed = event
    else:
        return {'valid': False, 'errors': [f"Event must be str or dict, got {type(event).__name__}"], 'warnings': []}

    # --- Step 2: Validate common envelope fields ---

    # Timestamp
    ts = parsed.get('timestamp')
    if not ts:
        errors.append("Missing required field: timestamp")
    elif not TIMESTAMP_REGEX.match(ts):
        errors.append(f"Invalid timestamp format: {ts} (expected YYYY-MM-DDTHH:MM:SS.mmmZ)")
    else:
        # Check parseable
        try:
            datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except ValueError:
            errors.append(f"Timestamp is not a valid date: {ts}")

    # Event type
    event_type = parsed.get('event_type')
    if not event_type:
        errors.append("Missing required field: event_type")
    elif event_type not in VALID_EVENT_TYPES:
        errors.append(f"Invalid event_type: '{event_type}'. Must be one of: {sorted(VALID_EVENT_TYPES)}")

    # Agent ID
    agent_id = parsed.get('agent_id')
    if not agent_id:
        errors.append("Missing required field: agent_id")
    elif ' ' in agent_id or '|' in agent_id:
        errors.append(f"Invalid agent_id: '{agent_id}'. Must not contain spaces or pipe characters")

    # Status
    status = parsed.get('status')
    if not status:
        errors.append("Missing required field: status")
    elif event_type and event_type in VALID_STATUSES:
        if status not in VALID_STATUSES[event_type]:
            errors.append(
                f"Invalid status '{status}' for event_type '{event_type}'. "
                f"Valid statuses: {sorted(VALID_STATUSES[event_type])}"
            )

    # Metadata
    metadata = parsed.get('metadata')
    if metadata is None:
        errors.append("Missing required field: metadata")
    elif not isinstance(metadata, dict):
        errors.append(f"Metadata must be a dict, got {type(metadata).__name__}")

    # --- Step 3: Validate event-specific metadata ---

    if event_type and status and isinstance(metadata, dict):
        key = (event_type, status)

        # Check required metadata fields
        required_fields = REQUIRED_METADATA.get(key, [])
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required metadata field '{field}' for {event_type}/{status}")

        # Event-specific validation rules

        # team_complete: exit_code must be 0, agents_failed must be 0
        if status == 'team_complete':
            if metadata.get('exit_code') != 0:
                errors.append("team_complete exit_code must be 0")
            if metadata.get('agents_failed', 0) != 0:
                errors.append("team_complete agents_failed must be 0")
            spawned = metadata.get('total_agents_spawned', 0)
            succeeded = metadata.get('agents_succeeded', 0)
            failed = metadata.get('agents_failed', 0)
            if spawned != succeeded + failed:
                errors.append(
                    f"agents_succeeded ({succeeded}) + agents_failed ({failed}) "
                    f"!= total_agents_spawned ({spawned})"
                )

        # team_failed: exit_code must be non-zero, failure_category must be valid
        if status == 'team_failed':
            exit_code = metadata.get('exit_code')
            if exit_code is not None and exit_code == 0:
                errors.append("team_failed exit_code must be non-zero")
            if not metadata.get('failure_reason'):
                errors.append("team_failed failure_reason must be non-empty")
            cat = metadata.get('failure_category')
            if cat and cat not in VALID_FAILURE_CATEGORIES:
                errors.append(
                    f"Invalid failure_category: '{cat}'. "
                    f"Must be one of: {sorted(VALID_FAILURE_CATEGORIES)}"
                )
            spawned = metadata.get('total_agents_spawned', 0)
            succeeded = metadata.get('agents_succeeded', 0)
            failed = metadata.get('agents_failed', 0)
            if spawned != succeeded + failed:
                errors.append(
                    f"agents_succeeded ({succeeded}) + agents_failed ({failed}) "
                    f"!= total_agents_spawned ({spawned})"
                )

        # token_usage: cache fields are recommended
        if event_type == 'resource' and status == 'token_usage':
            if 'cache_read_tokens' not in metadata:
                warnings.append("token_usage missing recommended field: cache_read_tokens")
            if 'cache_write_tokens' not in metadata:
                warnings.append("token_usage missing recommended field: cache_write_tokens")
            if 'cost_estimate_usd' not in metadata:
                warnings.append("token_usage missing recommended field: cost_estimate_usd")
            # Verify total_tokens = input_tokens + output_tokens
            inp = metadata.get('input_tokens', 0)
            out = metadata.get('output_tokens', 0)
            total = metadata.get('total_tokens', 0)
            if total != inp + out:
                errors.append(
                    f"total_tokens ({total}) != input_tokens ({inp}) + output_tokens ({out})"
                )

        # coverage_report: coverage_percent must be 0-100
        if event_type == 'test' and status == 'coverage_report':
            cov = metadata.get('coverage_percent')
            if cov is not None and (cov < 0 or cov > 100):
                errors.append(f"coverage_percent must be 0-100, got {cov}")

        # phase_transition: to_phase must be > from_phase
        if event_type == 'timing' and status == 'phase_transition':
            from_p = metadata.get('from_phase')
            to_p = metadata.get('to_phase')
            if from_p is not None and to_p is not None and to_p <= from_p:
                warnings.append(f"phase_transition to_phase ({to_p}) should be > from_phase ({from_p})")

        # graph_constructed: has_cycles should be false (cycles are fatal)
        if event_type == 'dependency' and status == 'graph_constructed':
            if metadata.get('has_cycles'):
                warnings.append("Dependency graph has cycles -- execution will likely fail")

    # --- Step 4: Return result ---

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
```

### Batch Validation

For validating an entire log file:

```python
def validate_log_file(log_file_path: str) -> dict:
    """
    Validate all events in a telemetry log file.

    Returns:
        dict:
            valid: bool -- True if all events pass validation
            total_events: int -- Number of events in file
            invalid_events: int -- Number of events that failed validation
            errors: list[dict] -- Details of each invalid event
            has_terminal_event: bool -- Whether file has team_complete/team_failed
            warnings: list[str] -- File-level warnings
    """
    results = {
        'valid': True,
        'total_events': 0,
        'invalid_events': 0,
        'errors': [],
        'has_terminal_event': False,
        'warnings': []
    }

    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith('#') or line == '---' or not line:
                continue

            results['total_events'] += 1
            validation = validate_event(line)

            if not validation['valid']:
                results['valid'] = False
                results['invalid_events'] += 1
                results['errors'].append({
                    'line_number': line_num,
                    'line': line[:200],
                    'errors': validation['errors']
                })

            # Check for terminal event
            try:
                parsed = parse_log_line(line)
                if parsed and parsed['status'] in ('team_complete', 'team_failed'):
                    results['has_terminal_event'] = True
            except ValueError:
                pass

    if not results['has_terminal_event']:
        results['warnings'].append(
            "Log file missing terminal event (team_complete or team_failed). "
            "This may indicate a crash or incomplete execution."
        )

    return results
```

---

## Testing Checklist

For TASK-006 acceptance:

- [ ] All 14 event types defined (lifecycle, coordination, progress, test, resource, config, dependency, agent_io, approval, timing, error, cost, data_flow, environment)
- [ ] Event format follows REQ-F-28 specification
- [ ] Timestamp format is ISO 8601 UTC with milliseconds
- [ ] Metadata is valid JSON (parseable by json.loads())
- [ ] Pipe-delimited format matches spec
- [ ] Lifecycle events cover all states (spawned, start, completed, failed)
- [ ] Coordination events cover plan flow (proposed, approved, rejected, assigned)
- [ ] Progress events support intermediate updates and milestones
- [ ] Test telemetry events capture full execution lifecycle (start, complete, suite_discovered, test_case_start, test_case_result, test_fixture_setup, test_fixture_teardown, coverage_report, test_output_captured, test_retry, test_summary)
- [ ] Resource events track queues, timeouts, limits, and token usage
- [ ] Token usage event includes all REQ-F-27a fields
- [ ] Config events track loading, overrides, defaults, and model resolution
- [ ] Dependency events track graph construction, phase planning, waiting, and satisfaction
- [ ] Agent I/O events capture prompt construction, output received/parsed, and file read/write
- [ ] Approval events track gate entry, prompt display, user response, and plan regeneration
- [ ] Timing events track phase transitions, queue wait times, backoff waits, and overhead summaries
- [ ] Error events track validation checks, state transitions, retry decisions, and error classification
- [ ] Cost events track memory snapshots, cumulative costs, model fallbacks, and utilization snapshots
- [ ] Data flow events track data passing, file conflict checks, plan diffs, and agent messages
- [ ] Environment events track session start/end and environment snapshots
- [ ] Enriched metadata fields present on lifecycle spawned, completed, and failed schemas
- [ ] Enriched metadata fields present on coordination plan_proposed schema
- [ ] Enriched metadata fields present on resource token_usage schema
- [ ] Event sequence examples demonstrate real-world workflows including all event types
- [ ] Example 5 demonstrates verbose per-test telemetry with fixture setup/teardown, retries, coverage, and summary
- [ ] Common required fields documented (timestamp, event_type, agent_id, status, metadata)
- [ ] Standard log line format specification with parsing rules and regex
- [ ] validate_event() function validates any event against its schema
- [ ] validate_event() checks envelope fields (timestamp, event_type, agent_id, status)
- [ ] validate_event() checks event-specific required metadata fields
- [ ] validate_event() returns structured result with valid, errors, and warnings
- [ ] TEAM_COMPLETE terminal event schema defined with all required fields
- [ ] TEAM_FAILED terminal event schema defined with all required fields
- [ ] Terminal events MUST be written at execution end (try/finally pattern documented)
- [ ] Incomplete log detection documented (check_log_completeness function)
- [ ] validate_log_file() batch validation function validates entire log files
- [ ] Failure categories enumerated for TEAM_FAILED events

---

## References

- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-23 to REQ-F-28, REQ-F-27a)
- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Telemetry Event Schema)
- Pattern: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-03-25
**Status**: Implementation (TASK-006)
