---
name: layer-reorder-implement
description: Implementation team for tensor+trie semantic layer reordering system
coordinator: teams/layer-reorder-implement-coordinator.md
max_agents: 5
timeout_minutes: 45
approval_gates:
  before_execution: false
  after_execution: false
agents:
  - name: tensor-trie-implementer
    type: agents/implement/tensor-trie-implementer.md
  - name: semantic-reorder-implementer
    type: agents/implement/semantic-reorder-implementer.md
  - name: layers-touchpoint-updater
    type: agents/implement/layers-touchpoint-updater.md
  - name: lifecycle-updater
    type: agents/implement/lifecycle-updater.md
  - name: agent-intent-implementer
    type: agents/implement/agent-intent-implementer.md
dependencies:
  - from: layers-touchpoint-updater
    depends_on: [tensor-trie-implementer, semantic-reorder-implementer]
  - from: lifecycle-updater
    depends_on: [tensor-trie-implementer]
  - from: agent-intent-implementer
    depends_on: [layers-touchpoint-updater, semantic-reorder-implementer]
---

# Layer Reorder Implementation Team

Implements the tensor+trie semantic layer reordering system from the v2 research report.

## Execution Plan

```
Phase 1 (parallel):
  ├─ tensor-trie-implementer       → NEW: tensor.md, trie.md
  └─ semantic-reorder-implementer  → NEW: semantic-extractor.md, reorder.md

Phase 2 (parallel, after Phase 1):
  ├─ layers-touchpoint-updater     → MODIFY: SKILL.md, resolver.md
  └─ lifecycle-updater             → MODIFY: memory-writer.md

Phase 3 (after Phase 2):
  └─ agent-intent-implementer      → MODIFY: dream-mentor.md, mentor.md
```

## Files Created
- `skills/dream-layers/tensor.md`
- `skills/dream-layers/trie.md`
- `skills/dream-layers/semantic-extractor.md`
- `skills/dream-layers/reorder.md`

## Files Modified
- `skills/dream-layers/SKILL.md`
- `skills/dream-layers/resolver.md`
- `skills/dream-manager/memory-writer.md`
- `agents/dream-mentor.md`
- `commands/mentor.md`
