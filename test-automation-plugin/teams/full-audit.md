---
# ===========================================================================
# Full Skill/Agent/Command Audit Team
# ===========================================================================
# Audits all skills, agents, commands, and subagents to verify:
#   1. All Skill() references in allowed-tools resolve to real skills
#   2. All agent/subagent references resolve to real files
#   3. All skill.yaml files are valid and internally consistent
#   4. plugin.json commands array matches what exists on disk
#
# Location: teams/full-audit.md
# Invoked via: /team-run full-audit
# ===========================================================================

name: full-audit
coordinator: teams/full-audit-coordinator.md
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
  - name: command-skill-auditor
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: agent-reference-auditor
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: skill-yaml-auditor
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: registration-auditor
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

dependencies: []
---

# Full Skill/Agent/Command Audit Team

A validation team that audits every cross-reference in the Dante plugin to ensure
all skills, agents, commands, and subagents are correctly interlinked and callable.

## Purpose

This team reads all command frontmatter, agent definitions, skill.yaml files, and
the plugin manifest to verify that every reference resolves to a real file. It
catches broken Skill() references, missing agent files, stale skill.yaml configs,
and unregistered commands.

**Use case**: Run this team after renaming the plugin, adding new commands/skills,
or refactoring agent definitions to catch broken links before shipping.

## Agent Composition

This team uses **4 agents** running fully in parallel (no dependencies):

| Agent | Role | Dependencies | Critical |
|---|---|---|---|
| `command-skill-auditor` | Validates every `Skill()` reference in command `allowed-tools` resolves to a real skill directory | None | Yes |
| `agent-reference-auditor` | Validates all agent/subagent file references and `subagent_type` values resolve correctly | None | Yes |
| `skill-yaml-auditor` | Validates every `skill.yaml` has correct `instructions` field, no stale `entry_point`, and valid internal dependencies | None | Yes |
| `registration-auditor` | Cross-references `plugin.json` commands array against files on disk in both directions | None | Yes |

## Dependency Graph

```
command-skill-auditor   ──┐
agent-reference-auditor ──┤  (all run in parallel, no dependencies)
skill-yaml-auditor      ──┤
registration-auditor    ──┘
```

Phase 1 (parallel: 4): All agents run simultaneously

## Expected Outputs

Each agent produces a structured report with:
- **PASS** items: References that resolved correctly
- **FAIL** items: Broken references with file path, line, and what's missing
- **WARN** items: Non-critical issues (e.g., unused skills, stale comments)

The coordinator aggregates all reports into a single audit summary.
