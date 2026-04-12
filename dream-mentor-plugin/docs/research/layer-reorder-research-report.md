# Layer Reorder Research Report

**Team**: layer-reorder-research
**Date**: 2026-04-12
**Agents**: 4 (current-system-analyst, prior-art-researcher, query-interface-designer, reorder-algorithm-designer)
**Status**: Complete

---

## Executive Summary

The dream-mentor layer system currently uses static numeric priorities in per-dream `layer.json` files. This works for basic conflict resolution but has **5 critical gaps**: no reorder command, no precedence query, no collision prevention, no reorder preview, and no context-aware ordering. Users cannot ask "what's in front of layer X" or reorder layers without forget+reload.

This report proposes a comprehensive upgrade across **4 dimensions**:

1. **Data structure**: Replace distributed `layer.json` priorities with a centralized `manifest.json` ordered array
2. **7 reorder operations**: move_to_front, move_to_back, move_before, move_after, swap, promote, demote + undo
3. **4 new intents**: precedence query, reorder, attribution, preview/what-if
4. **Context-aware ordering**: 3-tier model (base priority, context rules, session pins)

The design is informed by prior art from **7 systems** (CSS Cascade Layers, Figma/Photoshop, Kubernetes webhooks, database migrations, Docker Compose, Ansible, Git merge) and follows a **4-phase implementation plan**.

---

## 1. Current System Analysis

### How It Works Today

- **Priority model**: Numeric integers in `layer.json`, 1 = highest precedence
- **Merge algorithm**: Sort by priority ascending, iterate with first-write-wins per key
- **Conflict resolution**: Pairwise comparison, lower priority number wins
- **9 touchpoints** where priority matters across 7 files

### What's Missing

| Gap | Impact | Severity |
|-----|--------|----------|
| No reorder command | Must forget+reload to change priority | HIGH |
| No precedence query | Cannot ask "what overrides X" | HIGH |
| No collision prevention on `--layer` | Duplicate priorities create undefined behavior | MEDIUM |
| No reorder preview | Cannot see impact before committing | HIGH |
| No context-aware ordering | Priority is static regardless of what user is editing | MEDIUM |
| No undo for priority changes | Compact-after-forget is irreversible | LOW |

---

## 2. Prior Art Findings

### Best Patterns to Adopt

| Pattern | Source | Application |
|---------|--------|-------------|
| Single manifest as source of truth | CSS `@layer`, Liquibase | New `manifest.json` with ordered array |
| 4-operation reorder vocabulary | Figma/Photoshop | "bring to front", "send to back", "bring forward", "send backward" |
| "Show effective result" command | Docker Compose `config` | `attribute` intent with per-key source attribution |
| Typed merge rules | Docker Compose | Replace scalars, union lists, merge maps by key |
| Scope-based context boosting | Ansible precedence | 3-tier: base priority, context rules, session pins |
| Fallthrough semantics | CSS `revert-layer` | Layers only override what they explicitly cover |
| Checksum change detection | Flyway/Liquibase | Know when upstream layer content changed |

### Anti-Patterns to Avoid

| Anti-Pattern | Source | Why It Fails |
|-------------|--------|-------------|
| Name-based implicit ordering | Kubernetes webhooks | Fragile, non-obvious, breaks on rename |
| Too many precedence levels | Ansible (22 levels) | Even experts struggle to remember |
| Conflating two types of order | Figma Auto Layout | "Bring to front" shouldn't mean "send to bottom" |
| Immutable ordering | CSS Cascade Layers | Dream-mentor explicitly needs dynamic reorder |
| No attribution in merged output | Docker Compose | Users must trace guidance to its source |

---

## 3. Recommended Data Structure

### Centralized Manifest (replaces distributed priorities)

**New file**: `.claude/dreams/manifest.json`

```json
{
  "version": 2,
  "order": ["architecture-ref", "testing-patterns", "ui-reference"],
  "context_rules": [],
  "last_reorder": "2026-04-12T14:30:00.000Z",
  "reorder_history": []
}
```

**Updated `layer.json`** (priority field removed):

```json
{
  "active": true,
  "tags": ["architecture", "patterns"],
  "created_at": "2026-03-28T10:00:00.000Z"
}
```

### Why This Approach

- **Single source of truth**: No more reading N files to determine order
- **Array = gap-free**: No compaction needed after forget
- **Atomic reorder**: Write 1 file instead of N `layer.json` files
- **Undo support**: History ring buffer (max 20 entries) in manifest
- **Lazy migration**: Auto-migrates from v1 on first access

---

## 4. Reorder Operations

Seven operations designed as simple array manipulations:

| Operation | Natural Language | Disk Writes |
|-----------|-----------------|-------------|
| `move_to_front(dream)` | "bring X to front", "make X highest" | 2 (manifest + DREAMS.md) |
| `move_to_back(dream)` | "send X to back", "make X lowest" | 2 |
| `move_before(dream, target)` | "put X ahead of Y", "move X before Y" | 2 |
| `move_after(dream, target)` | "put X behind Y", "move X after Y" | 2 |
| `swap(dream_a, dream_b)` | "swap X and Y" | 2 |
| `promote(dream)` | "promote X", "bump X up" | 2 |
| `demote(dream)` | "demote X", "bump X down" | 2 |

Plus `undo_reorder()` which pops the history stack.

All operations are O(n) where n = dream count (typically < 10).

---

## 5. New Intents for dream-mentor Agent

### 5.1 Precedence Query

**Signals**: "order", "priority", "in front of", "ahead of", "above", "overrides", "who's on top"

**Example**: "what overrides testing-patterns?"

```markdown
## What Overrides "testing-patterns" (priority 2)

| Priority | Dream | Overrides testing-patterns on |
|----------|-------|-------------------------------|
| 1 | architecture-ref | naming_convention, error_handling |

Testing-patterns is the sole provider for: test_framework, test_organization.
```

### 5.2 Reorder

**Signals**: "move", "put", "swap", "bring to front", "send to back", "promote", "demote"

**Example**: "put testing-patterns first"

```markdown
## Layer Reorder Applied

Before: architecture-ref > testing-patterns > ui-reference
After:  testing-patterns > architecture-ref > ui-reference

2 keys changed ownership. 5 keys unaffected.
```

### 5.3 Attribution

**Signals**: "which dream controls", "where does ... come from", "who owns"

**Example**: "which dream controls my test framework?"

```markdown
## Attribution: Test Framework

Active guidance: Vitest
Provided by: testing-patterns (priority 2)
Contested: No — no other dream defines a test framework.
```

### 5.4 Preview / What-If

**Signals**: "what would change if", "preview", "dry run", "what if"

**Example**: "what would change if I put testing-patterns first?"

Shows a diff of conflict resolutions before/after the proposed change, then offers to apply.

---

## 6. Context-Aware Ordering

### Three-Tier Priority Model

| Tier | Source | Persistence | Override Strength |
|------|--------|-------------|-------------------|
| Base | `manifest.json` order | Persistent | Lowest |
| Context | `manifest.json` context_rules + active file | Computed at merge time | Medium |
| Pin | `.session_pin.json` | Session-scoped | Highest |

### Example Context Rule

```json
{
  "id": "boost-testing-in-tests",
  "type": "file_pattern",
  "condition": { "glob": "**/*.test.{ts,tsx,js,jsx}" },
  "action": { "boost": "testing-patterns", "to_position": 1 },
  "description": "When editing test files, testing-patterns takes highest priority"
}
```

---

## 7. Impact on Existing System

Of the 9 touchpoints where priority matters today:

| Touchpoint | Change Required | Risk |
|-----------|----------------|------|
| 1. Merge sort | Replace `a.priority` with `effective_order.indexOf(a.name)` | LOW |
| 2. Structure merge (first-write-wins) | **NONE** — depends on sort order from #1 | NONE |
| 3. Patterns merge (first-write-wins) | **NONE** | NONE |
| 4. Conventions merge (first-write-wins) | **NONE** | NONE |
| 5. Conflict resolution | Replace numeric comparison with position comparison | LOW |
| 6. Multi-layer diff | Use `get_effective_order()` | LOW |
| 7. Display/list operations | Read from manifest instead of layer.json | LOW |
| 8. DREAMS.md generation | Read from manifest (no sort needed) | LOW |
| 9. Load/forget priority handling | Load appends to manifest; forget removes (no compact) | MEDIUM |

**Key insight**: Touchpoints 2, 3, and 4 (the three first-write-wins merge loops) require **zero changes** because they depend entirely on iteration order from Touchpoint 1.

---

## 8. Phased Implementation Plan

### Phase 1: Foundation
- `manifest.json` schema, reader/writer, lazy migration
- 7 reorder operations + undo
- Update 5 of 9 touchpoints
- Expose through `/mentor` command and dream-mentor agent
- **Files to modify**: SKILL.md, resolver.md, memory-writer.md, dream-mentor.md, mentor.md

### Phase 2: Preview System
- `preview_reorder()` — simulate without writing
- Diff current vs. proposed merged views
- Auto-preview when conflicts would change; direct-apply when safe
- `--preview` / `--dry-run` flag

### Phase 3: Context-Aware Ordering
- Context rule schema in manifest
- `get_effective_order(context)` function
- Session pins (`.session_pin.json`)
- Rule management commands: `context add/list/remove`, `pin/unpin`

### Phase 4: Polish
- Manifest sync validation on session start
- All edge case handling (Section 6 of algorithm design)
- Batch reorder ("sort alphabetically", "reverse order")
- Conflict rule overlap warnings

---

## 9. Detailed Design Documents

| Document | Path | Contents |
|----------|------|----------|
| Algorithm & Data Structure Design | `docs/design/dynamic-layer-reordering.md` | Full pseudocode for all operations, data structures, context-aware ordering, impact analysis, edge cases, phased plan |
| Team Definition | `teams/layer-reorder-research.md` | Team structure and execution plan |
| Agent Definitions | `agents/research/*.md` | 4 research agent specifications |
