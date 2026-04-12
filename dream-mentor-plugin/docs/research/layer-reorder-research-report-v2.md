# Layer Reorder Research Report v2: Semantic Tensor + Trie Architecture

**Team**: layer-reorder-research (Round 2)
**Date**: 2026-04-12
**Agents**: 4 (tensor-structure-designer, semantic-trie-designer, concurrent-agent-researcher, integration-designer)
**Status**: Complete
**Supersedes**: `layer-reorder-research-report.md` (flat manifest approach)

---

## Executive Summary

The flat `manifest.json` ordered array proposed in Round 1 is insufficient for multi-agent, semantically-aware layer reordering. This report proposes a fundamentally different architecture:

1. **N x N x N Relevance Tensor** (`tensor.json`) — a 3D matrix indexed by `[dream][category][context]` storing floating-point relevance weights [0.0, 1.0]. Replaces the flat manifest entirely.
2. **Semantic Prefix Trie** (`trie.json`) — a ~35-node taxonomy tree that provides O(k) lookup to find which dreams are relevant for a given semantic topic, avoiding full tensor scans.
3. **Per-Agent Ordering Overlay** — each concurrent agent computes its own effective ordering in memory. No shared mutable state, no disk writes for isolation.
4. **On-the-Fly Reordering** — when dream records are accessed, the system automatically adjusts effective ordering based on the semantic content of the request.

### Key Numbers

| Metric | Value |
|--------|-------|
| Tensor size (10 dreams, 50 categories, 20 contexts) | ~80KB memory, ~150KB disk |
| Trie size (35 taxonomy nodes, 10 dreams) | ~20KB memory, ~30KB disk |
| Ordering resolution time | <2ms |
| Full tensor rebuild after dream load | <30ms |
| Touchpoints requiring code changes | 5 of 9 (same as Round 1) |

---

## Architecture: How It Works

```
REQUEST ARRIVES
      |
      v
+---------------------+
| Semantic Extraction  |  <-- keyword matching, file pattern matching
| "testing.framework"  |
+---------------------+
      |
      +--------+--------+
      |                  |
      v                  v
+----------+    +--------------+
| Trie     |    | Tensor       |
| O(k)     |    | [dream]      |
| "which   |    |   [category] |
| dreams?" |    |     [context] |
+----------+    +--------------+
      |                  |
      | candidates       | weights
      +--------+---------+
               |
               v
     +-------------------+
     | Ordering Resolver  |
     | scores --> sort    |
     +-------------------+
               |
     effective_order: [D2, D1, D3]
               |
     +---------+---------+
     |                   |
     v                   v
+----------+    +------------+
| Merge    |    | Conflict   |
| Engine   |    | Resolver   |
| (first-  |    | (position- |
|  write-  |    |  based)    |
|  wins)   |    |            |
+----------+    +------------+
     |                   |
     +--------+----------+
              |
              v
     +-------------------+
     | Merged Response    |
     | with attribution   |
     +-------------------+
```

### The Three Dimensions

| Axis | What | Size | Example Values |
|------|------|------|---------------|
| **Dreams (D)** | Loaded reference repos | 2-20 | architecture-ref, testing-patterns, ui-reference |
| **Categories (K)** | Fine-grained content domains | ~24 | conventions.test_framework, patterns.naming, structure.directories |
| **Contexts (C)** | What the user/agent is doing | ~10-20 | file.test, file.component, query.testing, task.diff, _base |

A cell `tensor[d][k][c]` = "How relevant is dream `d` for category `k` when working in context `c`?"

---

## The Semantic Trie

### Structure

A static taxonomy tree (~35 nodes, max depth 3) built from the dream content domains:

```
Root
  +-- structure
  |     +-- directories
  |     +-- modules
  +-- patterns
  |     +-- architecture
  |     +-- naming
  |     +-- error_handling
  +-- conventions
  |     +-- testing
  |     |     +-- framework    <-- "what test framework?" lands here
  |     |     +-- organization
  |     |     +-- mocking
  |     +-- build
  |     +-- cicd
  +-- dependencies
        +-- framework
        +-- libraries
```

Each node stores a `DreamRelevanceMap`: per-dream scores with provenance evidence.

### Query Resolution

1. **Extract semantic path** from query keywords: "what test framework should I use?" --> `["conventions", "testing", "framework"]`
2. **Walk the trie** to the deepest matching node
3. **Weighted inheritance**: deepest node weight=1.0, parent=0.5, grandparent=0.25
4. **Combine + normalize** scores across all dreams
5. **Sort** by score descending, tiebreak by `tensor.base_order`

**Result**: testing-patterns scores ~1.0, architecture-ref ~0.55, ui-reference ~0.10 for this query.

### Why a Trie + Tensor Instead of Just One

- **Trie alone**: Can only store membership (which dreams are relevant), not nuanced per-context weights
- **Tensor alone**: Requires O(D * K) scan for every query to find relevant categories
- **Together**: Trie provides O(k) filtering to the right category, tensor provides continuous-valued ranking within that category

---

## Per-Agent Concurrent Ordering

### The Problem

Agent A (testing focus) needs testing-patterns in front. Agent B (architecture focus) needs architecture-ref in front. Both run simultaneously. A shared mutable ordering file creates race conditions.

### Solution: Per-Agent Overlay

Each agent computes its own `DreamOrdering` in memory at spawn time. No disk writes, no locks, no shared mutable state.

```
AgentContext {
  agent_id: string
  semantic_topic: string[]      // ["testing", "framework"]
  active_files: string[]        // ["src/tests/auth.test.ts"]
  explicit_pins: PinnedDream[]  // [{ dream: "testing-patterns", position: 1 }]
}
```

Resolution priority (highest to lowest):
1. **Explicit pins** from coordinator
2. **Semantic trie** routing from query content
3. **File-pattern context** rules
4. **Tensor base_order** (static fallback)

### Agent Reconciliation

When agents with different orderings produce conflicting recommendations:
1. **Scope authority**: Testing agent wins testing conflicts, architecture agent wins architecture conflicts
2. **Strength tiebreak**: Stronger recommendation wins
3. **Base ordering fallback**: User's explicit priority breaks final ties

---

## On-the-Fly Reordering via Access Hook

When a dream record is accessed, the system monitors access patterns:

```
on_dream_record_access(dream, category, agent_context):
  // Track access affinity per dream
  // If >50% of accesses are to one dream AND it's not already top-2:
  //   Auto-boost it to position 1-2 for this agent
  // Minimum 3 accesses before triggering (prevents noise)
```

This is purely in-memory, per-agent, and non-persisted. The agent's ordering refines itself as it works.

---

## Storage Layout

```
.claude/dreams/
  DREAMS.md                    # Human-readable index (unchanged)
  tensor.json                  # N*N*N relevance tensor (NEW)
  trie.json                    # Semantic prefix trie (NEW)
  .session_pin.json            # Ephemeral session pin (gitignored)
  <dream-name>/
    source.json                # Unchanged
    layer.json                 # MODIFIED: no priority, adds semantic_profile
    structure.md               # Unchanged
    patterns.md                # Unchanged
    dependencies.md            # Unchanged
    conventions.md             # Unchanged
    summary.md                 # Unchanged
```

### Updated `layer.json`

```json
{
  "active": true,
  "tags": ["architecture", "patterns"],
  "created_at": "2026-03-28T10:00:00.000Z",
  "semantic_profile": {
    "patterns.architecture": 0.95,
    "patterns.naming": 0.80,
    "conventions.testing": 0.30,
    "conventions.build": 0.70,
    "structure": 0.90,
    "dependencies.frameworks": 0.85
  }
}
```

`priority` removed. `semantic_profile` added (populated by analyzer at load time).

---

## Impact on 9 Touchpoints

| # | Touchpoint | Change | Risk |
|---|-----------|--------|------|
| 1 | Merge sort | `tensor_score(dream, cat, ctx)` replaces `a.priority` | LOW |
| 2 | Structure merge | **NONE** | NONE |
| 3 | Patterns merge | **NONE** | NONE |
| 4 | Conventions merge | **NONE** | NONE |
| 5 | Conflict resolution | Now context-dependent (same conflict can resolve differently per agent) | MEDIUM |
| 6 | Multi-layer diff | Uses tensor ordering for `task.diff` context | LOW |
| 7 | Display/list | Shows `base_order` + context boost indicators | LOW |
| 8 | DREAMS.md generation | Uses `tensor.base_order` | LOW |
| 9 | Load/forget | Updates tensor dimensions + trie nodes | MEDIUM |

---

## Migration Path

```
v1 (layer.json priority) ─┐
                           ├──> Lazy auto-detect on first read_tensor()
v2 (manifest.json)     ───┘         |
                                    v
                           Build tensor from existing
                           dream .md files + priorities
                                    |
                                    v
                           tensor.json + trie.json
                           (layer.json updated)
```

Cold start rebuilds both structures from dream content in <50ms.

---

## Phased Implementation

### Phase 1: Tensor Foundation
- `tensor.json` schema, reader/writer, lazy migration
- `trie.json` schema, construction from dream content
- Basic `get_tensor_ordering(context)` with `_base` context only
- 7 reorder operations on `tensor.base_order`
- Update 5 touchpoints
- **Equivalent behavior to flat manifest, but on tensor infrastructure**

### Phase 2: Semantic Routing
- Semantic extraction (keyword/pattern matching)
- Trie traversal with weighted inheritance
- File-based context classification
- Query-based context classification
- Context-aware conflict resolution

### Phase 3: Multi-Agent Concurrency
- `AgentContext` schema
- Per-agent ordering overlay
- Access hook for on-the-fly refinement
- Agent reconciliation protocol
- Merge caching keyed on effective ordering

### Phase 4: Self-Tuning
- Access pattern tracking (optional)
- Adaptive score boosting from usage
- Pattern-based suggestions ("You keep asking about testing. Pin testing-patterns?")

---

## Detailed Design Documents

| Document | Path |
|----------|------|
| Tensor structure design | Agent output (tensor-structure-designer) |
| Semantic trie design | Agent output (semantic-trie-designer) |
| Concurrent agent ordering | Agent output (concurrent-agent-researcher) |
| Full integration architecture | `docs/design/dynamic-layer-reordering.md` (to be updated) |
| Previous flat manifest design | `docs/design/dynamic-layer-reordering.md` (current, superseded) |
| Round 1 report | `docs/research/layer-reorder-research-report.md` |
