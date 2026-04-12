# Teamsters

Agent team orchestration for Claude Code. Define parallel agent teams as Markdown files, execute them with a single command, and observe everything through structured telemetry.

## What it does

Teamsters lets you define **teams of AI agents** that work together on complex tasks. You describe the agents, their dependencies, and how they coordinate in a simple Markdown file with YAML frontmatter. Then you run `/team-run my-team` and the framework handles:

- Parsing your team definition and validating it
- Building an execution plan from the dependency graph
- Presenting the plan for your approval
- Spawning agents in parallel (respecting concurrency limits)
- Retrying failed agents with exponential backoff
- Aggregating results from all agents
- Logging everything to structured telemetry

## Installation

Clone the repo into your Claude Code plugins directory:

```bash
# From your project or a shared plugins location
git clone git@github.example.com:my-org/teamsters-plugin.git
```

Claude Code will automatically detect the `.claude-plugin/plugin.json` manifest and register the `/team-run` command.

### Requirements

- Claude Code CLI, Desktop, or IDE extension
- For built-in team system: set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Falls back to custom orchestration if the experimental flag is not set

## Quick start

### 1. Run the included example

```bash
/team-run example-parallel
```

This runs a 3-agent team (two parallel tasks + one aggregator) to demonstrate the framework.

### 2. Create your own team

Create a file at `teams/my-team.md`:

```yaml
---
name: my-team
coordinator: teams/my-team-coordinator.md
max_agents: 3
timeout_minutes: 15
---

# My Team

Describe what this team does here.
```

Create the coordinator at `teams/my-team-coordinator.md`:

```markdown
# My Team - Coordinator

## Phase 1: Research (Parallel)

### Agent: researcher-1
**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:
You are researcher-1. Search the codebase for X and report findings.

### Agent: researcher-2
**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:
You are researcher-2. Search the codebase for Y and report findings.

## Phase 2: Synthesize (Sequential)

### Agent: synthesizer
**Subagent Type**: `general-purpose`
**Model**: `opus`

**Task Prompt**:
You are the synthesizer. Combine the findings from both researchers
into a single report.
```

Run it:

```bash
/team-run my-team
```

## Command reference

### `/team-run [team-name] [options]`

| Option | Description | Default |
|--------|-------------|---------|
| `--max-agents <n>` | Max parallel agents (1-25) | Team definition value |
| `--timeout <minutes>` | Execution timeout | Team definition value |
| `--approval-gates <mode>` | `before`, `after`, or `disabled` | Team definition value |
| `--telemetry` | Enable telemetry logging | Off |
| `--help` | Show help | - |

### Examples

```bash
# Run with defaults
/team-run my-team

# Limit parallelism
/team-run my-team --max-agents=2

# Quick run, no approval prompts
/team-run my-team --approval-gates=disabled

# Full observability
/team-run my-team --telemetry

# Short timeout for fast tasks
/team-run my-team --timeout=5

# Combine options
/team-run my-team --max-agents=4 --timeout=20 --approval-gates=before --telemetry
```

## Team definition format

Team definitions are Markdown files in the `teams/` directory with YAML frontmatter.

### Required fields

```yaml
---
name: my-team                                    # Must match filename
coordinator: teams/my-team-coordinator.md        # Path to coordinator file
max_agents: 5                                    # Max parallel agents (1-25)
---
```

### All fields (with defaults)

```yaml
---
name: my-team
coordinator: teams/my-team-coordinator.md
max_agents: 5

# Optional
version: "1.0.0"
timeout_minutes: 30                              # Team execution timeout
depth_limit: 3                                   # Max nesting depth (1-3)

approval_gates:
  before_execution: true                         # Pause before spawning agents
  after_completion: true                         # Pause after all agents complete
  disabled: false                                # Skip all gates

retry_config:
  max_retries: 3                                 # Per-agent retry limit (0-3)
  backoff_seconds: [1, 2, 4]                     # Exponential backoff delays

failure_handling: continue                       # "continue" or "abort"
token_budget: null                               # Max tokens (null = unlimited)
telemetry_enabled: null                          # Override global setting

# Agent composition (optional, used by some coordinators)
agents:
  - name: analyzer
    type: agents/analyze-agent.md                # Agent definition file or built-in type
    critical: true                               # Failure aborts team if true
    dependencies: []                             # Agent names this depends on
    max_instances: 1

  - name: writer
    type: agents/write-agent.md
    critical: false
    dependencies: [analyzer]                     # Runs after analyzer completes
    max_instances: 3                             # Up to 3 parallel instances

  - name: executor
    type: agents/execute-agent.md
    critical: true
    dependencies: [writer]

# Explicit dependency graph (alternative to per-agent dependencies)
dependencies:
  - from: analyzer
    to: writer
    type: sequential
  - from: writer
    to: executor
    type: sequential
---
```

### Coordinator files

The coordinator file defines what each agent does and how phases are structured. It's referenced by the team definition's `coordinator` field.

```markdown
# My Team - Coordinator

## Phase 1: Analysis (Sequential)

### Agent: analyzer
**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:
Your instructions here. The agent runs this prompt.

## Phase 2: Writing (Parallel)

### Agent: writer-1
**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:
Instructions for writer 1.

### Agent: writer-2
**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:
Instructions for writer 2.

## Phase 3: Execution (Sequential)

### Agent: executor
**Subagent Type**: `general-purpose`
**Model**: `opus`

**Task Prompt**:
Instructions for the executor.

## Result Aggregation

Describe how to combine agent outputs into the final result.
```

## Execution lifecycle

When you run `/team-run my-team`, the framework executes 7 phases:

```
Phase 0: Initialize
  Generate team ID, start telemetry

Phase 1: Load & Validate
  Parse team definition, validate fields, check file references,
  detect circular dependencies, apply CLI overrides

Phase 2: Register Resources
  Register team, enforce concurrent team limit (max 5),
  start timeout tracking

Phase 3: Plan & Approve
  Build execution plan from dependency graph (topological sort),
  present plan to user at before_execution approval gate

Phase 4: Execute Agents
  Spawn agents via Task tool respecting max_agents limit,
  FIFO queue excess agents, retry failures with [1,2,4]s backoff,
  handle continue/abort failure strategies

Phase 5: Aggregate Results
  Merge outputs from all agents, deduplicate files,
  aggregate metrics, calculate success rate

Phase 6: After-Completion Approval
  Present results at after_completion gate (if enabled)

Phase 7: Finalize
  Clean up resources, return TeamResult with full metrics
```

## Approval gates

Approval gates are checkpoints where the framework pauses for your input.

### Before execution

Shows the execution plan and asks you to approve, modify, or reject:

```
# Testing Team: Proposed Execution Plan

## Agent Composition
- Phase 1 (Sequential): analyzer
- Phase 2 (Parallel): writer-1, writer-2, writer-3
- Phase 3 (Sequential): executor

## Proposed Parallelization
- Agents to Spawn: 3 writers simultaneously
- Estimated Time: 2 minutes

Do you approve? [Approve / Modify / Reject]
```

- **Approve**: Proceed with execution
- **Modify**: Provide feedback, plan regenerates (up to 3 iterations)
- **Reject**: Cancel, no agents spawned

### After completion

Shows aggregated results and asks you to accept, iterate, or discard.

### Disabling gates

```bash
# Skip all gates (fully autonomous)
/team-run my-team --approval-gates=disabled

# Only approve the plan, skip after-completion
/team-run my-team --approval-gates=before
```

Or in the team definition:

```yaml
approval_gates:
  disabled: true
```

## Failure handling

### Retry logic

Failed agents are retried up to 3 times with exponential backoff:

| Attempt | Backoff | Total wait |
|---------|---------|------------|
| 1st (initial) | 0s | 0s |
| 2nd (retry 1) | 1s | 1s |
| 3rd (retry 2) | 2s | 3s |
| 4th (retry 3) | 4s | 7s |

### Failure strategies

**`continue`** (default): Log the failure, proceed with remaining agents. Team status becomes `partial_success` if at least one agent succeeded.

**`abort`**: Stop all agents on first failure (after retries exhausted). Team status becomes `aborted`.

**Critical agents**: Agents with `critical: true` always trigger abort on failure, regardless of the team's `failure_handling` setting.

```yaml
failure_handling: continue  # or "abort"

agents:
  - name: analyzer
    critical: true           # Must succeed or team aborts
  - name: writer
    critical: false          # Can fail without stopping team
```

## Telemetry

Enable telemetry to capture structured logs of every orchestration decision.

### Enabling telemetry

```bash
# Via CLI flag (per-execution)
/team-run my-team --telemetry

# Via environment variable (persistent)
export TEAMSTERS_TELEMETRY=1

# Via team definition
# telemetry_enabled: true
```

### Log location

```
{project_root}/.claude/telemetry-{timestamp}.log
```

### 14 event types

| Event Type | What it captures |
|------------|-----------------|
| `lifecycle` | Agent spawn, start, complete, fail (with full output, token usage, retry history) |
| `coordination` | Plan proposals, approvals, task assignments (with full plan JSON, dependency graph) |
| `progress` | Intermediate agent updates, milestones |
| `test` | Suite discovery, per-test-case start/result, fixture setup/teardown, coverage reports, stdout/stderr capture, flaky test retries, execution summaries |
| `resource` | Queue status, timeouts, limits, token usage (with cost estimates) |
| `config` | Team definition loading, CLI overrides, default resolution, model selection |
| `dependency` | DAG construction, phase planning, dependency waiting/resolution |
| `agent_io` | Full agent prompts, full agent outputs, file read/write operations |
| `approval` | Gate entry, prompt display, user responses, plan modifications |
| `timing` | Phase transitions, queue wait times, retry backoff delays, overhead summaries (framework tax) |
| `error` | Validation checks, state machine transitions, retry decisions, error classification with severity |
| `cost` | Memory/context snapshots, cumulative cost tracking, model fallbacks, utilization curves |
| `data_flow` | Inter-phase data passing, file conflict checks, plan diffs, peer-to-peer agent messages |
| `environment` | Session start/end, platform/OS, git branch/commit, plugin version, available teams |

### Real-time monitoring

Telemetry supports 3 simultaneous delivery channels:

**Live console output** - compact, color-coded activity feed in your terminal:
```bash
/team-run my-team --telemetry-console

# Or via environment variable
export TEAMSTERS_TELEMETRY_CONSOLE=1
```

Example output:
```
[14:30:00] ENV        coordinator    session    platform=win32 branch=main
[14:30:01] CONFIG     coordinator    loaded     my-team (teams/my-team.md)
[14:30:10] LIFECYCLE  analyzer       spawned    Explore, depth=2
[14:30:25] LIFECYCLE  analyzer       completed  14.9s
[14:30:25] COST       coordinator    running    $0.008 (1/2 agents)
[14:30:45] TIMING     coordinator    overhead   44.7s wall, 34.4s work, 23% tax
[14:30:45] ENV        coordinator    session    completed, $0.019 total
```

**Live file tailing** (second terminal):
```bash
# Unix/macOS
tail -f .claude/telemetry-*.log

# Windows PowerShell
Get-Content .claude\telemetry-*.log -Wait -Tail 0

# Filter specific events
tail -f .claude/telemetry-*.log | grep "lifecycle\|error\|cost"
```

**Webhook streaming** - POST events as JSON to any HTTP endpoint:
```bash
# Stream to a local receiver
export TEAMSTERS_TELEMETRY_WEBHOOK=http://localhost:8080/events

# With auth token
export TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN=my-api-key

# Batch mode (buffer 10 events per POST)
export TEAMSTERS_TELEMETRY_WEBHOOK_BATCH=10
```

Compatible with Grafana Loki, Datadog, Elasticsearch, or any JSON POST endpoint.

**Maximum observability** - enable all channels:
```bash
export TEAMSTERS_TELEMETRY_CONSOLE=1
export TEAMSTERS_TELEMETRY_WEBHOOK=http://localhost:8080/events
/team-run my-team --telemetry
```

### Log format

```
[timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
```

### Example log output (maximum verbosity)

```
2026-03-25T14:30:00.500Z | environment | coordinator | session_start | {"session_id":"sess-my-team-20260325","platform":"win32","git_branch":"main","git_dirty":false}
2026-03-25T14:30:00.600Z | environment | coordinator | environment_snapshot | {"teamsters_env_vars":{"TEAMSTERS_TELEMETRY":"1"},"teams_available":["my-team","example-parallel"]}
2026-03-25T14:30:01.123Z | config | coordinator | config_loaded | {"team_name":"my-team","file_path":"teams/my-team.md","frontmatter_raw":{...}}
2026-03-25T14:30:01.150Z | error | coordinator | validation_check | {"check_name":"required_fields","result":"pass","field":"coordinator"}
2026-03-25T14:30:01.200Z | lifecycle | coordinator | spawned | {"team_id":"my-team","depth":1,"team_config_snapshot":{...}}
2026-03-25T14:30:01.300Z | dependency | coordinator | graph_constructed | {"adjacency_list":{"analyzer":[],"writer":["analyzer"]},"total_nodes":2,"total_edges":1}
2026-03-25T14:30:01.350Z | dependency | coordinator | phase_planned | {"phase_number":1,"agents":["analyzer"],"parallel":false}
2026-03-25T14:30:01.360Z | dependency | coordinator | phase_planned | {"phase_number":2,"agents":["writer"],"parallel":false}
2026-03-25T14:30:01.400Z | coordination | coordinator | plan_proposed | {"plan_summary":"2 agents in 2 phases","full_plan":{...}}
2026-03-25T14:30:01.410Z | approval | coordinator | gate_entered | {"gate_type":"before_execution","iteration":0}
2026-03-25T14:30:10.000Z | approval | coordinator | user_response_received | {"decision":"approve","response_time_seconds":8.6}
2026-03-25T14:30:10.050Z | timing | coordinator | phase_transition | {"from_phase":0,"to_phase":1,"transition_duration_seconds":0.05}
2026-03-25T14:30:10.100Z | agent_io | analyzer | prompt_constructed | {"prompt_length_chars":3500,"prompt_estimated_tokens":900,"model":"sonnet"}
2026-03-25T14:30:10.150Z | cost | analyzer | memory_snapshot | {"snapshot_point":"spawn","context_used_tokens":900,"utilization_percent":0.45}
2026-03-25T14:30:10.200Z | lifecycle | analyzer | spawned | {"agent_type":"Explore","depth":2}
2026-03-25T14:30:10.250Z | error | coordinator | state_transition | {"agent_id":"analyzer","from_state":"spawned","to_state":"running"}
2026-03-25T14:30:25.000Z | agent_io | analyzer | output_received | {"output_length_chars":1200,"output_estimated_tokens":300,"duration_seconds":14.8}
2026-03-25T14:30:25.100Z | lifecycle | analyzer | completed | {"duration_seconds":14.9,"model_used":"sonnet","output_full":{...},"token_usage":{"input_tokens":1500,"output_tokens":800}}
2026-03-25T14:30:25.150Z | resource | analyzer | token_usage | {"input_tokens":1500,"output_tokens":800,"total_tokens":2300,"cost_estimate_usd":0.008}
2026-03-25T14:30:25.200Z | cost | coordinator | cumulative_cost | {"estimated_cost_usd":0.008,"agents_completed":1,"agents_remaining":1}
2026-03-25T14:30:25.250Z | cost | analyzer | memory_snapshot | {"snapshot_point":"completion","context_used_tokens":2300,"utilization_percent":1.15}
2026-03-25T14:30:25.300Z | dependency | coordinator | dependency_satisfied | {"agent":"writer","dependency":"analyzer","unblocked_agents":["writer"]}
2026-03-25T14:30:25.350Z | data_flow | coordinator | data_passed | {"from_agent":"analyzer","to_agent":"writer","data_size_chars":1200,"data_summary":"1 agent output"}
2026-03-25T14:30:25.360Z | timing | coordinator | phase_transition | {"from_phase":1,"to_phase":2,"transition_duration_seconds":0.06}
2026-03-25T14:30:25.400Z | agent_io | writer | prompt_constructed | {"prompt_length_chars":4200,"prompt_estimated_tokens":1050,"model":"sonnet"}
2026-03-25T14:30:25.500Z | lifecycle | writer | spawned | {"agent_type":"general-purpose","depth":2}
2026-03-25T14:30:45.000Z | lifecycle | writer | completed | {"duration_seconds":19.5,"model_used":"sonnet","retry_count":0}
2026-03-25T14:30:45.100Z | cost | coordinator | cumulative_cost | {"estimated_cost_usd":0.019,"agents_completed":2,"agents_remaining":0}
2026-03-25T14:30:45.200Z | timing | coordinator | overhead_summary | {"total_wall_clock_seconds":44.7,"total_agent_work_seconds":34.4,"overhead_percent":23.0,"framework_tax_percent":23.0}
2026-03-25T14:30:45.300Z | lifecycle | coordinator | completed | {"duration_seconds":44.8}
2026-03-25T14:30:45.400Z | environment | coordinator | session_end | {"exit_status":"completed","total_agents_spawned":2,"total_estimated_cost_usd":0.019}
```

## Model selection

The framework supports per-agent model assignment (Opus, Sonnet, Haiku) with a configuration precedence chain.

### Precedence (highest to lowest)

1. **CLI override**: `--validate-model=sonnet`
2. **Environment variable**: `TEAMSTERS_VALIDATE_MODEL=opus`
3. **Config file**: `.claude/teamsters-config.json`
4. **Defaults**: validate/fix = opus, others = sonnet

### Model timeouts

| Model | Timeout | Use case |
|-------|---------|----------|
| Opus | 180s | Complex reasoning, validation, fixing |
| Sonnet | 120s | Balanced - analysis, writing, execution |
| Haiku | 60s | Fast, simple tasks |

### Config file

```json
// .claude/teamsters-config.json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "sonnet",
    "execute": "haiku"
  }
}
```

## Resource limits

| Resource | Limit | Configurable |
|----------|-------|-------------|
| Agents per team | 5 (default) | `max_agents` in team definition or `--max-agents` |
| Concurrent teams | 5 | Global limit |
| Nesting depth | 3 levels | `depth_limit` in team definition |
| Timeout | 30 minutes | `timeout_minutes` or `--timeout` |
| Retry attempts | 3 per agent | `retry_config.max_retries` |

When limits are reached, excess agents are queued in FIFO order and automatically spawned as slots free up.

## Configuration precedence

For all settings, the precedence order is:

```
CLI flags  >  Team definition frontmatter  >  Framework defaults
```

| Setting | CLI Flag | Frontmatter Field | Default |
|---------|----------|-------------------|---------|
| Max agents | `--max-agents=N` | `max_agents: N` | 5 |
| Timeout | `--timeout=N` | `timeout_minutes: N` | 30 |
| Approval gates | `--approval-gates=MODE` | `approval_gates:` | before+after enabled |
| Telemetry | `--telemetry` | `telemetry_enabled: true` | disabled |

## Project structure

```
teamsters-plugin/
  .claude-plugin/
    plugin.json                          # Plugin manifest
  commands/
    team-run.md                          # /team-run command definition
  skills/
    team-orchestration/
      SKILL.md                           # 7-phase coordinator lifecycle
      team-loader.md                     # Team definition loading & validation
      agent-lifecycle-manager.md         # Agent state machine (spawned->running->completed/failed)
      resource-manager.md               # Limits, FIFO queuing, timeouts
      approval-gate-handler.md          # Before/after approval gates with iteration
      result-aggregator.md              # Parallel output merging & failure handling
    telemetry/
      SKILL.md                           # Non-blocking event logging (9 event types)
      event-types.md                     # Event schemas & metadata definitions
      log-writer.md                      # Append-only log writer with rotation
    model-selection/
      SKILL.md                           # Model resolution (Opus/Sonnet/Haiku)
      config-manager.md                  # Config file loading & validation
      model-resolver.md                  # Precedence chain resolution
      metrics-collector.md               # Execution metrics logging
  teams/
    example-parallel.md                  # Example team definition (template)
    example-parallel-coordinator.md      # Example coordinator implementation
```

## Troubleshooting

**"Team definition not found"**
Check that your file is at `teams/{name}.md` and the `name` field in frontmatter matches the filename.

**"Team definition failed validation"**
Common causes: missing `name`/`coordinator`/`max_agents`, coordinator file doesn't exist, circular dependencies in agent graph.

**Team times out**
Increase the timeout: `/team-run my-team --timeout=60`. Default is 30 minutes.

**Too many agent failures**
Check individual agent errors in the execution summary. Consider reducing `max_agents` or reviewing agent prompts. Set `failure_handling: abort` if you want to stop on first failure.

**Approval gate won't stop asking**
Use `--approval-gates=disabled` for fully autonomous execution.

**Telemetry not writing**
Ensure `TEAMSTERS_TELEMETRY=1` is set, or pass `--telemetry`, or set `telemetry_enabled: true` in the team definition.
