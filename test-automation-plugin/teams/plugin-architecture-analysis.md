---
# ===========================================================================
# Plugin Architecture Analysis Team
# ===========================================================================
# Analyzes Dante's entire skill/agent/command architecture to produce:
#   1. A full traversal graph of skill invocation paths
#   2. A redundancy/overlap analysis of skills
#   3. A comprehensive white paper on how the plugin works
#
# Location: teams/plugin-architecture-analysis.md
# Invoked via: /team-run plugin-architecture-analysis
# ===========================================================================

name: plugin-architecture-analysis
coordinator: teams/plugin-architecture-analysis-coordinator.md
max_agents: 4

version: "1.0.0"
timeout_minutes: 45
depth_limit: 3

approval_gates:
  before_execution: true
  after_completion: true
  disabled: false

retry_config:
  max_retries: 2
  backoff_seconds: [2, 4, 8]

failure_handling: continue
token_budget: null
telemetry_enabled: true

agents:
  - name: skill-inventory-mapper
    type: general-purpose
    critical: true
    dependencies: []
    max_instances: 1

  - name: traversal-graph-builder
    type: general-purpose
    critical: true
    dependencies: [skill-inventory-mapper]
    max_instances: 1

  - name: redundancy-analyzer
    type: general-purpose
    critical: false
    dependencies: [skill-inventory-mapper]
    max_instances: 1

  - name: whitepaper-synthesizer
    type: general-purpose
    critical: true
    dependencies: [traversal-graph-builder, redundancy-analyzer]
    max_instances: 1

dependencies:
  - from: skill-inventory-mapper
    to: traversal-graph-builder
    type: sequential
  - from: skill-inventory-mapper
    to: redundancy-analyzer
    type: sequential
  - from: traversal-graph-builder
    to: whitepaper-synthesizer
    type: sequential
  - from: redundancy-analyzer
    to: whitepaper-synthesizer
    type: sequential
---

# Plugin Architecture Analysis Team

A research team that performs deep analysis of the Dante plugin's architecture,
producing a complete traversal graph, redundancy report, and white paper.

## Purpose

This team reads every skill, agent, command, and subagent definition in the
Dante plugin to understand the full architecture. It maps how components invoke
each other, identifies overlaps and redundancies, and synthesizes findings into
a comprehensive white paper explaining how the plugin works end-to-end.

**Use case**: Run this team when you need a complete architectural understanding
of the Dante plugin, want to identify duplicative skills, or need documentation
of the plugin's internal workings.

## Agent Composition

This team uses **4 agents** in a dependency chain:

| Agent | Role | Dependencies | Critical |
|---|---|---|---|
| `skill-inventory-mapper` | Reads ALL skills, agents, commands, subagents and catalogs their interfaces, inputs, outputs, and cross-references | None (runs first) | Yes |
| `traversal-graph-builder` | Builds directed graph of all invocation paths between components | skill-inventory-mapper | Yes |
| `redundancy-analyzer` | Identifies overlapping, duplicative, or redundant functionality across skills | skill-inventory-mapper | No |
| `whitepaper-synthesizer` | Synthesizes all findings into a structured white paper | traversal-graph-builder, redundancy-analyzer | Yes |

## Dependency Graph

```
skill-inventory-mapper ──┬──> traversal-graph-builder ──┬──> whitepaper-synthesizer
                         │                               │
                         └──> redundancy-analyzer ───────┘
```

Phase 1 (parallel: none): skill-inventory-mapper runs alone
Phase 2 (parallel: 2): traversal-graph-builder + redundancy-analyzer run in parallel
Phase 3 (parallel: none): whitepaper-synthesizer consumes all prior outputs

## Expected Outputs

1. **Skill Inventory** (from skill-inventory-mapper):
   - Complete catalog of all 15 skills, 5 agents, 6 commands, 1 subagent
   - For each: name, purpose, inputs, outputs, what it invokes, what invokes it

2. **Traversal Graph** (from traversal-graph-builder):
   - Directed acyclic graph (or cyclic, if cycles exist) of all invocation paths
   - Entry points (user commands) mapped to full execution traces
   - DOT-format graph for visualization

3. **Redundancy Report** (from redundancy-analyzer):
   - Skills with overlapping responsibilities
   - Duplicated logic across different components
   - Consolidation recommendations

4. **White Paper** (from whitepaper-synthesizer):
   - Executive summary of the plugin
   - Architecture overview with diagrams
   - Component catalog
   - Data flow analysis
   - Redundancy findings and recommendations
   - Conclusion with improvement suggestions
