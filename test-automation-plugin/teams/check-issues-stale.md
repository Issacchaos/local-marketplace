---
# ===========================================================================
# GitHub Issue Staleness Audit Team
# ===========================================================================
# Audits all open GitHub issues against the current codebase to determine
# if any have been resolved. For resolved issues, adds a comment for a
# human to finalize closing.
#
# Location: teams/check-issues-stale.md
# Invoked via: /team-run check-issues-stale
# ===========================================================================

name: check-issues-stale
coordinator: teams/check-issues-stale-coordinator.md
max_agents: 4

version: "1.0.0"
timeout_minutes: 30
depth_limit: 2

approval_gates:
  before_execution: true
  after_completion: false
  disabled: false

retry_config:
  max_retries: 1
  backoff_seconds: [2, 4]

failure_handling: continue
token_budget: null
telemetry_enabled: false

agents:
  - name: issue-auditor-bugs
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: issue-auditor-enhancements-core
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: issue-auditor-enhancements-features
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: issue-auditor-meta
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

dependencies: []
---

# GitHub Issue Staleness Audit Team

Audits all open GitHub issues in the dante_plugin repository against the current
codebase to determine which issues have been resolved by recent changes. For issues
that appear resolved, a comment is added for a human to review and finalize closing.

## Purpose

Over time, issues may be resolved by commits that don't explicitly reference them.
This team systematically checks each open issue against the current state of the
codebase and flags those that appear to have been addressed.

**Use case**: Run periodically to keep the issue tracker clean and surface resolved
issues that were never formally closed.

## Agent Composition

This team uses **4 agents** running fully in parallel (no dependencies):

| Agent | Role | Issues Assigned | Critical |
|---|---|---|---|
| `issue-auditor-bugs` | Audits bug-labeled and regression issues | Bugs, broken behavior | Yes |
| `issue-auditor-enhancements-core` | Audits core workflow enhancement issues | Plugin internals, test generation, workflow | Yes |
| `issue-auditor-enhancements-features` | Audits new feature/integration issues | New capabilities, integrations | Yes |
| `issue-auditor-meta` | Audits meta, tooling, and backlog issues | Feedback, docs, tooling, backlog | Yes |

## Dependency Graph

```
issue-auditor-bugs                ──┐
issue-auditor-enhancements-core   ──┤  (all run in parallel, no dependencies)
issue-auditor-enhancements-features──┤
issue-auditor-meta                ──┘
```

Phase 1 (parallel: 4): All agents run simultaneously

## Expected Outputs

Each agent produces a structured report with:
- **RESOLVED** items: Issues that appear to be fixed, with evidence (file paths, commits, code references)
- **OPEN** items: Issues that still appear unresolved
- **UNCLEAR** items: Issues where resolution status is ambiguous

The coordinator aggregates reports and posts GitHub comments on resolved issues.
