---
name: layer-reorder-research
description: Research team investigating how to improve dream-mentor layer reordering based on contextual queries about layer precedence
coordinator: teams/layer-reorder-research-coordinator.md
max_agents: 4
timeout_minutes: 30
approval_gates:
  before_execution: true
  after_execution: false
agents:
  - name: current-system-analyst
    type: agents/research/current-system-analyst.md
  - name: prior-art-researcher
    type: agents/research/prior-art-researcher.md
  - name: query-interface-designer
    type: agents/research/query-interface-designer.md
  - name: reorder-algorithm-designer
    type: agents/research/reorder-algorithm-designer.md
dependencies:
  - from: reorder-algorithm-designer
    depends_on: [current-system-analyst, prior-art-researcher]
  - from: query-interface-designer
    depends_on: [current-system-analyst]
---

# Layer Reorder Research Team

Research how to improve dream-mentor's layer system to support:

1. **Querying layer precedence** — "what's in front of layer X?"
2. **Context-aware reordering** — dynamically reorder layers based on what the user is working on
3. **Natural language reorder commands** — "put testing-patterns in front of architecture-ref"

## Research Questions

- How does the current priority system limit users?
- What prior art exists for layer/cascade reordering systems?
- What query interface feels natural for asking about layer order?
- What algorithms support dynamic, context-aware reordering without breaking conflict resolution?

## Execution Plan

```
Phase 1 (parallel):
  ├─ current-system-analyst: Deep dive into existing layer code
  └─ prior-art-researcher: Research cascade/layer systems in other tools

Phase 2 (parallel, after Phase 1):
  ├─ query-interface-designer: Design the "what's in front" query API
  └─ reorder-algorithm-designer: Design reorder algorithms

Phase 3:
  └─ coordinator: Aggregate all findings into report
```
