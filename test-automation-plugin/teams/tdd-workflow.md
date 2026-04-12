---
# ===========================================================================
# TDD Workflow Team
# ===========================================================================
# Coordinates the Red/Green/Refactor TDD cycle using Dante's team
# orchestration framework. Agents execute in dependency order:
# tdd-spec (RED) -> execute (VERIFY RED) -> tdd-implement (GREEN) ->
# execute (VERIFY GREEN) -> tdd-refactor (REFACTOR) -> execute (VERIFY REFACTOR)
#
# Location: teams/tdd-workflow.md
# Invoked via: /tdd --use-teams "requirements"
# ===========================================================================

name: tdd-workflow

coordinator: teams/tdd-workflow-coordinator.md

# TDD is inherently sequential (RED -> GREEN -> REFACTOR), but within each
# phase there may be parallelism opportunities (e.g., multiple test files).
# Keep max_agents at 3 for the concurrent verify + next-phase overlap.
max_agents: 3

version: "1.0.0"

# TDD cycle with implementation can take time
timeout_minutes: 45

depth_limit: 3

approval_gates:
  before_execution: true    # Review execution plan before starting
  after_completion: true    # Review final results (tests + implementation)
  disabled: false

retry_config:
  max_retries: 3
  backoff_seconds: [1, 2, 4]

# Continue on non-critical failures (refactor failure is recoverable)
failure_handling: continue

token_budget: null

telemetry_enabled: true

# ---------------------------------------------------------------------------
# AGENT COMPOSITION
# TDD phases execute sequentially via dependency chain.
# Execute-agent is reused 3 times (VERIFY RED, VERIFY GREEN, VERIFY REFACTOR).
# ---------------------------------------------------------------------------

agents:
  # Phase 1: RED - Write failing tests and stubs
  - name: tdd-spec
    type: agents/tdd-spec-agent.md
    critical: true
    dependencies: []
    max_instances: 1

  # Phase 2: VERIFY RED - Run tests, expect correct failures
  - name: execute-verify-red
    type: agents/execute-agent.md
    critical: true
    dependencies: [tdd-spec]
    max_instances: 1

  # Phase 3: GREEN - Write minimal implementation
  - name: tdd-implement
    type: agents/tdd-implement-agent.md
    critical: true
    dependencies: [execute-verify-red]
    max_instances: 1

  # Phase 4: VERIFY GREEN - Run tests, expect all pass
  - name: execute-verify-green
    type: agents/execute-agent.md
    critical: true
    dependencies: [tdd-implement]
    max_instances: 1

  # Phase 5: REFACTOR - Improve code quality (non-critical, skippable)
  - name: tdd-refactor
    type: agents/tdd-refactor-agent.md
    critical: false
    dependencies: [execute-verify-green]
    max_instances: 1

  # Phase 6: VERIFY REFACTOR - Confirm tests still pass
  - name: execute-verify-refactor
    type: agents/execute-agent.md
    critical: false
    dependencies: [tdd-refactor]
    max_instances: 1

dependencies:
  # Enforce strict RED -> GREEN -> REFACTOR ordering
  - from: tdd-spec
    to: execute-verify-red
    type: sequential

  - from: execute-verify-red
    to: tdd-implement
    type: sequential

  - from: tdd-implement
    to: execute-verify-green
    type: sequential

  - from: execute-verify-green
    to: tdd-refactor
    type: sequential

  - from: tdd-refactor
    to: execute-verify-refactor
    type: sequential
---

# TDD Workflow Team Definition

This team definition orchestrates the TDD Red/Green/Refactor cycle using Dante's team orchestration framework.

## Workflow

```
tdd-spec (RED) → execute-verify-red → tdd-implement (GREEN) → execute-verify-green → tdd-refactor (REFACTOR) → execute-verify-refactor
```

## Agent Roles

| Agent | TDD Phase | Role | Critical |
|-------|-----------|------|----------|
| `tdd-spec` | RED | Write failing tests + stubs from requirements | Yes |
| `execute-verify-red` | VERIFY RED | Confirm tests fail correctly (not test bugs) | Yes |
| `tdd-implement` | GREEN | Write minimum code to pass tests | Yes |
| `execute-verify-green` | VERIFY GREEN | Confirm all TDD tests pass | Yes |
| `tdd-refactor` | REFACTOR | Improve code quality without changing behavior | No |
| `execute-verify-refactor` | VERIFY REFACTOR | Confirm tests still pass after refactoring | No |

## Failure Handling

- **Critical agents** (tdd-spec, execute-verify-red, tdd-implement, execute-verify-green): Failure aborts the workflow.
- **Non-critical agents** (tdd-refactor, execute-verify-refactor): Failure is logged but the workflow continues. If refactoring breaks tests, the coordinator auto-reverts.

## Approval Gates

- **Before execution**: Review the TDD execution plan (agents, dependencies, requirements)
- **After completion**: Review final results (tests written, implementation, refactoring changes)
- Both can be disabled with `--approval-gates=disabled` on the CLI
