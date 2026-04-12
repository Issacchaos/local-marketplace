---
# ===========================================================================
# Example Parallel Team Definition
# ===========================================================================
# This is a fully commented example showing all available fields.
# Copy this file and modify it to create your own team definitions.
#
# Location: teams/example-parallel.md
# Invoked via: /team-run example-parallel
# ===========================================================================

# REQUIRED FIELDS
name: example-parallel                              # Must match filename (without .md)
coordinator: teams/example-parallel-coordinator.md  # Path to coordinator logic file
max_agents: 3                                       # Max parallel agents (1-25)

# OPTIONAL FIELDS (with defaults shown)
version: "1.0.0"                                    # Team definition version
timeout_minutes: 30                                 # Execution timeout (default: 30)
depth_limit: 2                                      # Max nesting depth (1-3, default: 3)

# Approval gates control user interaction points
approval_gates:
  before_execution: true                            # Pause before spawning agents (default: true)
  after_completion: false                           # Pause after completion (default: true)
  disabled: false                                   # Skip all gates (default: false)

# Retry configuration for failed agents
retry_config:
  max_retries: 2                                    # Max retries per agent (0-3, default: 3)
  backoff_seconds: [1, 2, 4]                        # Exponential backoff delays

# How to handle agent failures
failure_handling: continue                          # "continue" (default) or "abort"

# Optional resource limits
token_budget: null                                  # Max tokens per team (null = unlimited)
telemetry_enabled: false                            # Override global telemetry setting

# Agent composition (used by coordinator to plan execution)
agents:
  - name: task-alpha
    type: general-purpose                           # Agent type (path or built-in type)
    critical: false                                 # If true, failure aborts entire team
    dependencies: []                                # Agent names this depends on
    max_instances: 1                                # Max parallel instances

  - name: task-beta
    type: general-purpose
    critical: false
    dependencies: []
    max_instances: 1

  - name: task-gamma
    type: general-purpose
    critical: false
    dependencies: [task-alpha, task-beta]            # Waits for alpha and beta
    max_instances: 1

# Explicit dependency graph (alternative to per-agent dependencies)
dependencies:
  - from: task-alpha
    to: task-gamma
    type: sequential
  - from: task-beta
    to: task-gamma
    type: sequential
---

# Example Parallel Team

A minimal example team that demonstrates the team definition format and parallel execution capabilities.

## Purpose

This team runs two independent tasks (alpha and beta) in parallel, then runs a third task (gamma) that depends on both completing first.

## Workflow

```
Phase 1 (Parallel):  task-alpha  +  task-beta
                          |              |
                          v              v
Phase 2 (Sequential): task-gamma (waits for both)
```

## Coordinator Logic

See `teams/example-parallel-coordinator.md` for the coordinator implementation that manages this workflow.

## Usage

```bash
# Run with defaults
/team-run example-parallel

# Run with custom settings
/team-run example-parallel --max-agents=2 --timeout=10

# Run fully autonomous (no approval gates)
/team-run example-parallel --approval-gates=disabled
```
