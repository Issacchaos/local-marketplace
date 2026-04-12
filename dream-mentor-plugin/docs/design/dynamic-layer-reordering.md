# Dynamic Layer Reordering: Algorithm and Data Structure Design

**Author**: reorder-algorithm-designer agent
**Date**: 2026-04-12
**Status**: Design proposal (research only, no implementation)
**Depends on**: Phase 1 findings from current-system-analyst and prior-art-researcher

---

## Table of Contents

1. [Recommended Data Structure](#1-recommended-data-structure)
2. [Algorithm Pseudocode for Reorder Operations](#2-algorithm-pseudocode-for-reorder-operations)
3. [Context-Aware Ordering Design](#3-context-aware-ordering-design)
4. [Impact Analysis on the 9 Touchpoints](#4-impact-analysis-on-the-9-touchpoints)
5. [Preview / What-If System](#5-preview--what-if-system)
6. [Edge Cases](#6-edge-cases)
7. [Phased Implementation Plan](#7-phased-implementation-plan)

---

## 1. Recommended Data Structure

### Decision: Hybrid — Manifest-Based Ordering with Per-Layer Metadata

The recommended approach combines a **central ordered manifest** (single source of truth for ordering) with **per-layer layer.json** (retains metadata like active/tags but drops authoritative priority). This draws on the best pattern from prior art (CSS `@layer`, Liquibase changelogs) while preserving the dream-mentor convention of per-dream directories.

#### Why Not Pure Numeric Priorities?

The current system assigns integers (1, 2, 3) in `layer.json`. This works for simple cases but creates three problems for reordering:

1. **Renumbering cascade**: Moving a layer to position 2 in a 10-layer stack requires rewriting 8 `layer.json` files atomically.
2. **No insertion gaps**: Inserting between priorities 2 and 3 requires renumbering everything from 3 onward, or switching to fractional priorities.
3. **No single source of truth**: The "order" is distributed across N files. A corrupt or missing `layer.json` makes the global order ambiguous.

#### Why Not Pure Ordered List?

A pure list in a single file would orphan the per-dream `layer.json`, which currently stores `active` and `tags`. These belong close to the dream they describe. Removing `layer.json` entirely would also break the existing load flow (`memory-writer.md` lines 76-79).

#### Recommended Schema

**New file: `.claude/dreams/manifest.json`**

```json
{
  "version": 2,
  "order": [
    "architecture-ref",
    "testing-patterns",
    "ui-reference"
  ],
  "context_rules": [],
  "last_reorder": "2026-04-12T14:30:00.000Z",
  "reorder_history": []
}
```

- `order`: Array of dream names, index 0 = highest priority. This is the **single source of truth** for ordering.
- `context_rules`: Array of context-aware priority overrides (see Section 3).
- `last_reorder`: ISO timestamp of most recent reorder operation.
- `reorder_history`: Bounded ring buffer (max 20 entries) of recent reorder operations for undo support.

**Updated per-dream `layer.json`**

```json
{
  "active": true,
  "tags": ["architecture", "patterns"],
  "created_at": "2026-03-28T10:00:00.000Z"
}
```

- `priority` field is **removed**. Priority is derived from position in `manifest.json` `order` array.
- `active` and `tags` remain — they are per-dream metadata.

**Derived priority function**:

```
function get_priority(dream_name: string): number {
  manifest = read_manifest()
  index = manifest.order.indexOf(dream_name)
  if (index === -1) throw Error("Dream not in manifest")
  return index + 1   // 1-based to match existing convention
}
```

This means every consumer that reads priority today will call `get_priority()` instead of reading `layer.json.priority`. The mapping is trivial: position 0 in the array = priority 1 (highest).

#### Reorder History Entry Schema

```json
{
  "timestamp": "2026-04-12T14:30:00.000Z",
  "operation": "move_before",
  "args": { "dream": "testing-patterns", "target": "architecture-ref" },
  "previous_order": ["architecture-ref", "testing-patterns", "ui-reference"],
  "new_order": ["testing-patterns", "architecture-ref", "ui-reference"]
}
```

#### Migration Pseudocode (v1 to v2)

```
function migrate_to_manifest():
  dreams = list_dream_directories()
  
  // Build ordered list from existing priorities
  dream_priorities = []
  for dream_name in dreams:
    layer = read_json(".claude/dreams/{dream_name}/layer.json")
    dream_priorities.push({
      name: dream_name,
      priority: layer.priority ?? Infinity,
      active: layer.active ?? true,
      tags: layer.tags ?? []
    })
  
  // Sort by existing priority (ascending = highest first)
  // Tiebreak: alphabetical by name (matches existing resolver.md edge case)
  dream_priorities.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority
    return a.name.localeCompare(b.name)
  })
  
  // Create manifest
  manifest = {
    version: 2,
    order: dream_priorities.map(d => d.name),
    context_rules: [],
    last_reorder: now_iso(),
    reorder_history: []
  }
  write_json(".claude/dreams/manifest.json", manifest)
  
  // Update each layer.json: remove priority, keep active + tags
  for dream in dream_priorities:
    layer = read_json(".claude/dreams/{dream.name}/layer.json")
    delete layer.priority
    write_json(".claude/dreams/{dream.name}/layer.json", layer)
  
  // Regenerate DREAMS.md using new ordering
  regenerate_dreams_index(manifest)
```

**Backward compatibility**: If `manifest.json` does not exist but `layer.json` files have `priority` fields, the system should auto-migrate on first access (lazy migration). This avoids a hard cutover.

---

## 2. Algorithm Pseudocode for Reorder Operations

All operations follow the same pattern:
1. Read manifest
2. Validate inputs
3. Compute new order
4. Write manifest with history entry
5. Regenerate DREAMS.md

### Common Helpers

```
function read_manifest(): Manifest {
  path = ".claude/dreams/manifest.json"
  if (!exists(path)):
    // Lazy migration from v1
    migrate_to_manifest()
  return read_json(path)
}

function write_manifest_with_history(manifest, operation, args, old_order):
  // Record history (bounded ring buffer)
  entry = {
    timestamp: now_iso(),
    operation: operation,
    args: args,
    previous_order: old_order,
    new_order: manifest.order
  }
  manifest.reorder_history.push(entry)
  if (manifest.reorder_history.length > 20):
    manifest.reorder_history.shift()  // Drop oldest
  
  manifest.last_reorder = entry.timestamp
  write_json(".claude/dreams/manifest.json", manifest)
  regenerate_dreams_index(manifest)

function active_order(manifest): string[] {
  // Returns only active dreams in manifest order
  return manifest.order.filter(name => {
    layer = read_json(".claude/dreams/{name}/layer.json")
    return layer.active === true
  })
}

function validate_dream_exists(manifest, name):
  if (name not in manifest.order):
    throw Error("Dream '{name}' not found in manifest. Loaded dreams: {manifest.order.join(', ')}")
```

### 2.1 move_to_front(dream)

Set the given dream to highest priority (position 0).

```
function move_to_front(dream: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  
  old_order = [...manifest.order]
  
  // Already at front?
  if (manifest.order[0] === dream):
    return { changed: false, message: "'{dream}' is already at highest priority." }
  
  // Remove from current position, insert at front
  manifest.order = manifest.order.filter(d => d !== dream)
  manifest.order.unshift(dream)
  
  write_manifest_with_history(manifest, "move_to_front", { dream }, old_order)
  return { changed: true, old_position: old_order.indexOf(dream) + 1, new_position: 1 }
```

**Complexity**: O(n) where n = number of dreams. Acceptable — n is typically < 10.

### 2.2 move_to_back(dream)

Set the given dream to lowest priority (last position).

```
function move_to_back(dream: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  
  old_order = [...manifest.order]
  last_index = manifest.order.length - 1
  
  if (manifest.order[last_index] === dream):
    return { changed: false, message: "'{dream}' is already at lowest priority." }
  
  manifest.order = manifest.order.filter(d => d !== dream)
  manifest.order.push(dream)
  
  write_manifest_with_history(manifest, "move_to_back", { dream }, old_order)
  return { changed: true, old_position: old_order.indexOf(dream) + 1, new_position: manifest.order.length }
```

### 2.3 move_before(dream, target)

Insert `dream` immediately before `target` in the ordering.

```
function move_before(dream: string, target: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  validate_dream_exists(manifest, target)
  
  if (dream === target):
    return { changed: false, message: "Cannot move a dream before itself." }
  
  old_order = [...manifest.order]
  
  // Remove dream from current position
  manifest.order = manifest.order.filter(d => d !== dream)
  
  // Find target's position (after removal of dream)
  target_index = manifest.order.indexOf(target)
  
  // Insert dream immediately before target
  manifest.order.splice(target_index, 0, dream)
  
  // Check if order actually changed
  if (arrays_equal(old_order, manifest.order)):
    return { changed: false, message: "'{dream}' is already before '{target}'." }
  
  write_manifest_with_history(manifest, "move_before", { dream, target }, old_order)
  return { changed: true, old_position: old_order.indexOf(dream) + 1, new_position: manifest.order.indexOf(dream) + 1 }
```

**Key subtlety**: We remove `dream` first, then find `target`'s index in the reduced array, then splice. This correctly handles the case where `dream` was originally before `target` (target's index shifts down by 1 after removal).

### 2.4 move_after(dream, target)

Insert `dream` immediately after `target` in the ordering.

```
function move_after(dream: string, target: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  validate_dream_exists(manifest, target)
  
  if (dream === target):
    return { changed: false, message: "Cannot move a dream after itself." }
  
  old_order = [...manifest.order]
  
  // Remove dream from current position
  manifest.order = manifest.order.filter(d => d !== dream)
  
  // Find target's position (after removal of dream)
  target_index = manifest.order.indexOf(target)
  
  // Insert dream immediately after target
  manifest.order.splice(target_index + 1, 0, dream)
  
  if (arrays_equal(old_order, manifest.order)):
    return { changed: false, message: "'{dream}' is already after '{target}'." }
  
  write_manifest_with_history(manifest, "move_after", { dream, target }, old_order)
  return { changed: true, old_position: old_order.indexOf(dream) + 1, new_position: manifest.order.indexOf(dream) + 1 }
```

### 2.5 swap(dream_a, dream_b)

Exchange the positions of two dreams.

```
function swap(dream_a: string, dream_b: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream_a)
  validate_dream_exists(manifest, dream_b)
  
  if (dream_a === dream_b):
    return { changed: false, message: "Cannot swap a dream with itself." }
  
  old_order = [...manifest.order]
  
  index_a = manifest.order.indexOf(dream_a)
  index_b = manifest.order.indexOf(dream_b)
  
  // Swap in place
  manifest.order[index_a] = dream_b
  manifest.order[index_b] = dream_a
  
  write_manifest_with_history(manifest, "swap", { dream_a, dream_b }, old_order)
  return {
    changed: true,
    dream_a: { old_position: index_a + 1, new_position: index_b + 1 },
    dream_b: { old_position: index_b + 1, new_position: index_a + 1 }
  }
```

### 2.6 promote(dream)

Move up one position (toward higher priority / lower index).

```
function promote(dream: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  
  index = manifest.order.indexOf(dream)
  
  if (index === 0):
    return { changed: false, message: "'{dream}' is already at highest priority." }
  
  old_order = [...manifest.order]
  
  // Swap with the dream directly above
  neighbor = manifest.order[index - 1]
  manifest.order[index - 1] = dream
  manifest.order[index] = neighbor
  
  write_manifest_with_history(manifest, "promote", { dream }, old_order)
  return { changed: true, old_position: index + 1, new_position: index, swapped_with: neighbor }
```

### 2.7 demote(dream)

Move down one position (toward lower priority / higher index).

```
function demote(dream: string):
  manifest = read_manifest()
  validate_dream_exists(manifest, dream)
  
  index = manifest.order.indexOf(dream)
  
  if (index === manifest.order.length - 1):
    return { changed: false, message: "'{dream}' is already at lowest priority." }
  
  old_order = [...manifest.order]
  
  // Swap with the dream directly below
  neighbor = manifest.order[index + 1]
  manifest.order[index + 1] = dream
  manifest.order[index] = neighbor
  
  write_manifest_with_history(manifest, "demote", { dream }, old_order)
  return { changed: true, old_position: index + 1, new_position: index + 2, swapped_with: neighbor }
```

### 2.8 undo_reorder()

Revert the most recent reorder operation.

```
function undo_reorder():
  manifest = read_manifest()
  
  if (manifest.reorder_history.length === 0):
    return { changed: false, message: "No reorder operations to undo." }
  
  last_entry = manifest.reorder_history.pop()
  manifest.order = last_entry.previous_order
  manifest.last_reorder = now_iso()
  
  write_json(".claude/dreams/manifest.json", manifest)
  regenerate_dreams_index(manifest)
  
  return {
    changed: true,
    undone_operation: last_entry.operation,
    restored_order: last_entry.previous_order
  }
```

**Note**: Undo does not itself push a history entry. Repeated undo walks back through the history stack. This is standard undo behavior.

---

## 3. Context-Aware Ordering Design

### Concept: Effective Priority

The static ordering in `manifest.json` represents the **base priority**. Context-aware rules can temporarily **boost** specific dreams when conditions match. The result is an **effective priority** — a runtime-computed ordering that may differ from the base ordering.

This is analogous to Ansible's variable precedence (inventory < group < host < play) but applied to layer ordering.

### Context Rule Schema

Rules are stored in `manifest.json` under `context_rules`:

```json
{
  "context_rules": [
    {
      "id": "boost-testing-in-tests",
      "type": "file_pattern",
      "condition": {
        "glob": "**/*.test.{ts,tsx,js,jsx}",
        "also_matches": ["**/*.spec.*", "**/tests/**", "**/__tests__/**"]
      },
      "action": {
        "boost": "testing-patterns",
        "to_position": 1
      },
      "description": "When editing test files, testing-patterns dream takes highest priority"
    },
    {
      "id": "boost-ui-in-components",
      "type": "file_pattern",
      "condition": {
        "glob": "src/components/**"
      },
      "action": {
        "boost": "ui-reference",
        "to_position": 1
      },
      "description": "When editing components, ui-reference dream takes highest priority"
    },
    {
      "id": "tag-based-testing",
      "type": "tag_match",
      "condition": {
        "tags": ["testing"],
        "when": "active_file_matches",
        "glob": "**/*.test.*"
      },
      "action": {
        "boost_tagged": true,
        "to_position": 1
      },
      "description": "When editing test files, all dreams tagged 'testing' get boosted"
    }
  ]
}
```

### Session Pin (Manual Override)

A session pin is a temporary, non-persisted override. It lives in memory only (or in a session-scoped file if needed for agent handoff).

```json
// .claude/dreams/.session_pin.json (ephemeral, gitignored)
{
  "pin": "testing-patterns",
  "to_position": 1,
  "reason": "Focusing on test coverage this session",
  "created_at": "2026-04-12T15:00:00.000Z"
}
```

### Effective Priority Function

```
function get_effective_order(context: Context | null): string[] {
  manifest = read_manifest()
  base_order = [...manifest.order]
  
  // Filter to active dreams only
  active_order = base_order.filter(name => is_active(name))
  
  // Layer 1: Apply session pin (highest override precedence)
  pin = read_session_pin()
  if (pin && pin.pin in active_order):
    active_order = move_to_position(active_order, pin.pin, pin.to_position - 1)
  
  // Layer 2: Apply context rules (if context is provided)
  if (context && context.active_file):
    applicable_rules = manifest.context_rules
      .filter(rule => rule_matches(rule, context))
      .sort((a, b) => {
        // More specific rules win over less specific
        // file_pattern > tag_match (specificity order)
        return specificity(b) - specificity(a)
      })
    
    // Apply rules in reverse specificity order so most specific ends up on top
    for (rule of applicable_rules.reverse()):
      if (rule.action.boost):
        active_order = move_to_position(active_order, rule.action.boost, rule.action.to_position - 1)
      else if (rule.action.boost_tagged):
        tagged_dreams = find_dreams_with_tags(rule.condition.tags, active_order)
        for (dream of tagged_dreams.reverse()):
          active_order = move_to_position(active_order, dream, rule.action.to_position - 1)
  
  return active_order
}

function rule_matches(rule: ContextRule, context: Context): boolean {
  switch (rule.type):
    case "file_pattern":
      globs = [rule.condition.glob, ...(rule.condition.also_matches ?? [])]
      return globs.some(g => glob_match(g, context.active_file))
    
    case "tag_match":
      if (rule.condition.when === "active_file_matches"):
        return glob_match(rule.condition.glob, context.active_file)
      return false  // Unknown condition type
    
    default:
      return false

function move_to_position(order: string[], name: string, target_index: number): string[] {
  result = order.filter(d => d !== name)
  clamped_index = Math.max(0, Math.min(target_index, result.length))
  result.splice(clamped_index, 0, name)
  return result
}
```

### Three-Tier Priority Model

Borrowing from Ansible's scope-based approach, effective priority has three tiers:

| Tier | Source | Persistence | Override Strength |
|------|--------|-------------|-------------------|
| **Base** | `manifest.json` `order` array | Persistent | Lowest |
| **Context** | `manifest.json` `context_rules` + active file | Computed at merge time | Medium |
| **Pin** | `.session_pin.json` or in-memory | Session-scoped | Highest |

The merge algorithm and resolver always use `get_effective_order(context)` instead of reading `manifest.order` directly. When no context is available (e.g., `list` command), only base + pin apply.

### Context Rule Management Commands

These would be exposed through the `/mentor` command or the dream-mentor agent:

```
/mentor context add --when "**/*.test.*" --boost testing-patterns --to 1
/mentor context add --when "src/components/**" --boost ui-reference --to 1
/mentor context list
/mentor context remove <rule-id>
/mentor pin testing-patterns           // Session pin
/mentor unpin                          // Remove session pin
```

---

## 4. Impact Analysis on the 9 Touchpoints

### Touchpoint 1: Merge Algorithm Sort (SKILL.md lines 58-60)

**Current code**:
```
dreams.sort((a, b) => a.priority - b.priority);
```

**Change required**: Replace static priority lookup with effective-order lookup.

```
// BEFORE
dreams.sort((a, b) => a.priority - b.priority);

// AFTER
effective_order = get_effective_order(current_context)
dreams.sort((a, b) => {
  return effective_order.indexOf(a.name) - effective_order.indexOf(b.name)
})
```

**Risk**: LOW. The sort comparator changes, but the algorithm (first-write-wins iteration after sort) stays identical. As long as the sort produces a total order, behavior is preserved.

### Touchpoint 2: Structure Merge First-Write-Wins (SKILL.md lines 72-78)

**Current code**:
```
for (section of dream.structure) {
  if (!merged.structure[section.key]) {
    merged.structure[section.key] = { value: section.value, source: dream.name };
  }
}
```

**Change required**: NONE. This code iterates over dreams in the order they were sorted (Touchpoint 1). Fixing the sort is sufficient. The first-write-wins logic is order-agnostic — it just trusts the iteration order.

**Risk**: NONE. No code change needed here.

### Touchpoint 3: Patterns Merge First-Write-Wins (SKILL.md lines 81-88)

**Change required**: NONE. Same reasoning as Touchpoint 2. The iteration depends on sort order, which is fixed at Touchpoint 1.

**Risk**: NONE.

### Touchpoint 4: Conventions Merge First-Write-Wins (SKILL.md lines 99-108)

**Change required**: NONE. Same reasoning as Touchpoints 2 and 3.

**Risk**: NONE.

### Touchpoint 5: Conflict Resolution (resolver.md line 38)

**Current code**:
```
resolution: a.priority < b.priority ? a.name : b.name
```

**Change required**: Replace numeric comparison with position comparison.

```
// BEFORE
resolution: a.priority < b.priority ? a.name : b.name

// AFTER
effective_order = get_effective_order(current_context)
pos_a = effective_order.indexOf(a.name)
pos_b = effective_order.indexOf(b.name)
resolution: pos_a < pos_b ? a.name : b.name
```

**Risk**: LOW. Semantics are identical — lower index = higher priority, just like lower number = higher priority before. The alphabetical tiebreaker for same-priority (resolver.md line 170-171) is no longer needed because manifest ordering is inherently total (no two dreams can occupy the same array index).

### Touchpoint 6: Multi-Layer Diff (diff-engine.md lines 125-129)

**Current code**:
```
1. Load all active dreams sorted by priority
2. Use the dream-layers resolver to produce merged view
```

**Change required**: Step 1 must use `get_effective_order()` with the diff context. When diffing, the "context" is the entire project (not a single file), so context-aware rules may or may not apply. The safest approach: use base order + session pin for diff operations, since diff is a global operation not scoped to a single file.

```
// AFTER
effective_order = get_effective_order({ active_file: null })
// This applies session pin but not file-based context rules
active_dreams = load_active_dreams_in_order(effective_order)
merged = resolver.merge(active_dreams)
```

**Risk**: LOW. The diff engine delegates to the resolver; fixing the resolver (Touchpoint 5) and sort (Touchpoint 1) propagates here automatically.

### Touchpoint 7: Display/List Operations

**Current behavior**: `list` shows dreams sorted by layer priority from `layer.json`.

**Change required**: Read ordering from `manifest.json` instead. Display both base position and effective position when context rules are active.

```
# Loaded Dreams

| Position | Name              | Source             | Status | Context Boost |
|----------|-------------------|--------------------|--------|---------------|
| 1        | architecture-ref  | github.com/org/r   | Fresh  |               |
| 2        | testing-patterns  | /local/path        | Stale  | -> 1 in tests |
| 3        | ui-reference      | github.com/org/ui  | Fresh  | -> 1 in components |
```

The "Context Boost" column shows what position the dream jumps to when a context rule fires. This helps users understand the dynamic behavior without having to mentally simulate it.

**Risk**: LOW. Display-only change.

### Touchpoint 8: DREAMS.md Index Generation (memory-writer.md lines 126-129)

**Current code**:
```
1. Read all dream directories
2. Read each dream's source.json and layer.json
3. Sort by layer priority (ascending = highest first)
4. Generate the index with current metadata
```

**Change required**: Step 2-3 change. Read ordering from `manifest.json` instead of `layer.json` priority.

```
// AFTER
1. Read manifest.json for canonical order
2. For each dream in manifest order:
   a. Read source.json for source metadata
   b. Read layer.json for active/tags metadata
3. Generate index using manifest order (no sort needed — already ordered)
4. Write DREAMS.md
```

The DREAMS.md format itself stays the same, but "priority N" in the display is replaced by "position N" (or kept as "priority N" for backward compatibility, since position in the array maps 1:1 to priority number).

**Risk**: LOW. The `regenerate_dreams_index()` function is already called by every reorder operation (see Section 2), so DREAMS.md stays in sync automatically.

### Touchpoint 9: Priority Assignment on Load and Compaction on Forget

**Current behavior**:
- **On load**: New dream gets `max_existing_priority + 1`
- **On forget**: Gaps are compacted (e.g., [1, _, 3] becomes [1, 2])

**Change required for load**: Append new dream name to end of `manifest.json` `order` array. This is equivalent to `max + 1` but simpler.

```
function on_dream_load(dream_name: string):
  manifest = read_manifest()
  if (dream_name in manifest.order):
    throw Error("Dream already exists in manifest")
  manifest.order.push(dream_name)
  write_json(".claude/dreams/manifest.json", manifest)
```

**Change required for forget**: Remove dream name from `manifest.json` `order` array. No compaction needed — array indices are inherently gap-free.

```
function on_dream_forget(dream_name: string):
  manifest = read_manifest()
  old_order = [...manifest.order]
  manifest.order = manifest.order.filter(d => d !== dream_name)
  
  // Also remove any context rules that reference this dream
  manifest.context_rules = manifest.context_rules.filter(rule =>
    rule.action.boost !== dream_name
  )
  
  write_manifest_with_history(manifest, "forget", { dream: dream_name }, old_order)
```

**Risk**: MEDIUM. The current compact-after-forget logic (SKILL.md lines 155-161) updates `layer.json` priority fields. With the manifest approach, this entire compaction step is eliminated — the array is always dense. However, we need to verify that no other code path reads `layer.json.priority` for ordering. If any legacy code does, the migration must ensure `layer.json` files no longer have a `priority` field (or if they do, it is ignored in favor of the manifest).

**Concern about compact-after-forget undoing intentional ordering**: This risk is **eliminated** by the manifest approach. Forgetting a dream just removes it from the array; all other relative positions are preserved. No compaction, no accidental reorder.

---

## 5. Preview / What-If System

### Design Philosophy

Reordering can change which dream wins every conflict. Users need to see the impact before committing. The preview system runs the full merge and conflict resolution with the proposed new order, then diffs the result against the current merge.

### Preview Algorithm

```
function preview_reorder(operation: string, args: object): PreviewResult {
  manifest = read_manifest()
  
  // Step 1: Compute current merged state
  current_order = get_effective_order(null)
  current_merged = run_merge(current_order)
  current_conflicts = detect_conflicts(current_order)
  
  // Step 2: Compute proposed order (without persisting)
  proposed_order = simulate_reorder(manifest, operation, args)
  
  // Step 3: Compute proposed merged state
  proposed_merged = run_merge(proposed_order)
  proposed_conflicts = detect_conflicts(proposed_order)
  
  // Step 4: Diff the two merged states
  changes = diff_merged_states(current_merged, proposed_merged)
  conflict_changes = diff_conflict_resolutions(current_conflicts, proposed_conflicts)
  
  return {
    current_order,
    proposed_order,
    changes,           // Keys whose source attribution changes
    conflict_changes,  // Conflicts that resolve differently
    summary: format_preview(changes, conflict_changes)
  }
}

function simulate_reorder(manifest: Manifest, operation: string, args: object): string[] {
  // Clone the manifest order and apply the operation in memory
  // without writing to disk
  simulated = [...manifest.order]
  
  switch (operation):
    case "move_to_front":
      simulated = simulated.filter(d => d !== args.dream)
      simulated.unshift(args.dream)
    case "move_before":
      simulated = simulated.filter(d => d !== args.dream)
      idx = simulated.indexOf(args.target)
      simulated.splice(idx, 0, args.dream)
    // ... etc for each operation
  
  return simulated
}
```

### Diff Output for Preview

```
function format_preview(changes, conflict_changes): string {
  output = "## Reorder Preview\n\n"
  
  if (changes.length === 0 && conflict_changes.length === 0):
    return output + "No changes to merged output. The reorder does not affect any conflict resolutions.\n"
  
  if (conflict_changes.length > 0):
    output += "### Conflict Resolutions That Would Change\n\n"
    output += "| Category | Key | Current Winner | New Winner |\n"
    output += "|----------|-----|----------------|------------|\n"
    for (change of conflict_changes):
      output += "| {change.category} | {change.key} | {change.current_winner} | {change.new_winner} |\n"
    output += "\n"
  
  if (changes.length > 0):
    output += "### Merged Values That Would Change\n\n"
    for (change of changes):
      output += "- **{change.category}.{change.key}**: "
      output += "`{change.current_value}` (from {change.current_source}) "
      output += "-> `{change.new_value}` (from {change.new_source})\n"
  
  return output
}
```

### Example Preview Output

```markdown
## Reorder Preview

Proposed: move testing-patterns before architecture-ref

### Order Change
Before: architecture-ref (1) > testing-patterns (2) > ui-reference (3)
After:  testing-patterns (1) > architecture-ref (2) > ui-reference (3)

### Conflict Resolutions That Would Change

| Category    | Key               | Current Winner     | New Winner         |
|-------------|-------------------|--------------------|--------------------|
| conventions | test_framework    | architecture-ref   | testing-patterns   |
| patterns    | naming_convention | architecture-ref   | testing-patterns   |

### Merged Values That Would Change

- **conventions.test_framework**: `jest` (from architecture-ref) -> `vitest` (from testing-patterns)
- **patterns.naming_convention**: `kebab-case` (from architecture-ref) -> `camelCase` (from testing-patterns)

**2 conflict resolutions would change.** Apply this reorder? [Yes / Cancel]
```

### Integration with Reorder Commands

Every reorder operation should offer a `--preview` flag (or `--dry-run`):

```
/mentor reorder move-before testing-patterns architecture-ref --preview
```

The dream-mentor agent should default to showing a preview for any reorder that would change conflict resolutions. Non-impactful reorders (e.g., reordering dreams that have no overlapping keys) can be applied directly with a brief confirmation.

```
function execute_reorder_with_preview(operation, args, force = false):
  preview = preview_reorder(operation, args)
  
  if (preview.conflict_changes.length === 0 || force):
    // Safe to apply directly (or user said --force)
    apply_reorder(operation, args)
    return { applied: true, preview }
  else:
    // Show preview and ask for confirmation
    display(preview.summary)
    confirm = ask_user("Apply this reorder?", ["Yes", "Cancel"])
    if (confirm === "Yes"):
      apply_reorder(operation, args)
      return { applied: true, preview }
    else:
      return { applied: false, preview }
```

---

## 6. Edge Cases

### 6.1 Single Layer

**Scenario**: Only one dream is loaded. User tries to reorder.

**Behavior**: All operations return `{ changed: false }` with an appropriate message:
- `move_to_front`: "Only one dream loaded. It is already at highest priority."
- `promote`/`demote`: Same.
- `move_before`/`move_after`: Will fail validation since the target dream won't exist (unless target = self, which is caught separately).
- `swap`: Requires two different dreams, fails validation.

No special-case code needed — the existing validations handle this naturally.

### 6.2 All Dreams at Same Position (Should Not Happen)

**Scenario**: Under the old numeric system, two dreams might have the same priority.

**Behavior**: The manifest approach eliminates this entirely. An array cannot have two elements at the same index. During migration, if two dreams have the same numeric priority, the alphabetical tiebreaker (from resolver.md) determines their relative order in the manifest array.

### 6.3 Reorder During Active Merge

**Scenario**: A merge operation is in progress (e.g., during `diff`) and a reorder happens concurrently.

**Behavior**: In the Claude Code plugin model, operations are sequential (single-threaded conversation). True concurrency is not possible. However, if a future multi-agent architecture allows parallel operations:

- **Read-then-write**: The merge reads the manifest at start. If a reorder writes a new manifest during the merge, the merge uses stale order. This is acceptable — the merge produces a consistent result based on the order at time-of-read.
- **Mitigation**: If needed, add a version counter to the manifest. The merge can check if the version changed and warn the user.

For the current single-agent architecture, this edge case does not apply.

### 6.4 Manifest Out of Sync with Dream Directories

**Scenario**: A dream directory exists but is not in the manifest, or the manifest references a dream directory that was deleted externally.

**Validation function**:

```
function validate_manifest_sync():
  manifest = read_manifest()
  dream_dirs = list_dream_directories()  // Actual directories on disk
  
  in_manifest_not_on_disk = manifest.order.filter(name => name not in dream_dirs)
  on_disk_not_in_manifest = dream_dirs.filter(name => name not in manifest.order)
  
  if (in_manifest_not_on_disk.length > 0):
    // Remove phantoms from manifest
    manifest.order = manifest.order.filter(name => name in dream_dirs)
    write_json(".claude/dreams/manifest.json", manifest)
    warn("Removed {in_manifest_not_on_disk} from manifest — directories not found.")
  
  if (on_disk_not_in_manifest.length > 0):
    // Append orphans to end of manifest
    for (name of on_disk_not_in_manifest):
      manifest.order.push(name)
    write_json(".claude/dreams/manifest.json", manifest)
    warn("Added {on_disk_not_in_manifest} to manifest — directories found but not in ordering.")
  
  return manifest
```

This should run as part of `read_manifest()` (or at session start alongside the staleness check).

### 6.5 Reorder of Inactive Dreams

**Scenario**: User reorders a dream that has `active: false` in its `layer.json`.

**Behavior**: The reorder affects the manifest order (which includes both active and inactive dreams). The inactive dream's position in the manifest determines where it would be if reactivated. This is correct — the user may want to set up the ordering before activating a dream.

The `get_effective_order()` function filters to active-only for merge operations but the manifest itself maintains all dreams.

### 6.6 Undo After Forget

**Scenario**: User forgets dream A (which removes it from manifest), then tries to undo a reorder that involved dream A.

**Behavior**: The undo would attempt to restore `previous_order` which includes the forgotten dream. Since the dream directory no longer exists, the `validate_manifest_sync()` function (edge case 6.4) will strip it out.

Better approach: when forgetting a dream, also prune all history entries that reference it, or mark them as non-undoable.

```
function on_dream_forget(dream_name):
  // ... remove from order ...
  
  // Prune history entries that would restore the forgotten dream
  manifest.reorder_history = manifest.reorder_history.filter(entry =>
    !entry.previous_order.includes(dream_name) &&
    !entry.new_order.includes(dream_name)
  )
```

### 6.7 Context Rules Referencing Non-Existent Dreams

**Scenario**: A context rule boosts dream "testing-patterns" but that dream has been forgotten.

**Behavior**: The `on_dream_forget` function already removes rules referencing the forgotten dream (see Touchpoint 9 section). Additionally, `get_effective_order` should silently skip boost operations where the target dream is not in the active order.

### 6.8 Circular or Conflicting Context Rules

**Scenario**: Rule A says "in test files, boost testing-patterns to position 1." Rule B says "in test files, boost architecture-ref to position 1." Both fire on the same file.

**Behavior**: Rules are applied in order of specificity (see Section 3). If two rules have the same specificity, they are applied in array order from `context_rules`. The last-applied rule wins because each `move_to_position` call repositions the dream, potentially displacing a dream that was just boosted.

**Recommendation**: Display a warning when adding a context rule that would conflict with an existing rule on the same glob pattern:

```
Warning: Rule "boost-testing-in-tests" already boosts a dream to position 1 
for files matching "**/*.test.*". The new rule will take precedence. Continue? [Yes / Cancel]
```

### 6.9 Empty Manifest Order

**Scenario**: All dreams have been forgotten. Manifest order is `[]`.

**Behavior**: All reorder operations will fail validation (no dreams to reorder). Merge produces empty result. `list` shows "No dreams loaded." This is consistent with the existing behavior for no-dreams-loaded (resolver.md lines 162-164).

### 6.10 Very Large Number of Dreams (>20)

**Scenario**: A user loads many reference repos.

**Behavior**: All operations are O(n) on array length, which is fine for n < 100. The manifest file stays small. The preview system may become noisy (many potential conflict changes), so it should cap output at 20 changed entries with "... and N more."

---

## 7. Phased Implementation Plan

### Phase 1: Foundation (Manifest + Core Operations)

**Goal**: Replace distributed `layer.json` priorities with centralized manifest. Implement the 7 basic reorder operations. No context-awareness yet.

**Deliverables**:

1. **`manifest.json` schema and reader/writer**
   - Create `read_manifest()` with lazy migration from v1
   - Create `write_manifest_with_history()`
   - Create `validate_manifest_sync()`

2. **Migration logic**
   - `migrate_to_manifest()` function
   - Lazy trigger: called from `read_manifest()` when `manifest.json` does not exist
   - Remove `priority` from `layer.json` after migration
   - Update `layer.json` write in memory-writer.md to omit `priority`

3. **Seven reorder operations**
   - `move_to_front`, `move_to_back`
   - `move_before`, `move_after`
   - `swap`
   - `promote`, `demote`

4. **Update the 9 touchpoints** (only the ones that need code changes)
   - Touchpoint 1: Merge sort uses `get_effective_order(null)` (no context yet)
   - Touchpoint 5: Resolver uses position comparison
   - Touchpoint 7: List reads from manifest
   - Touchpoint 8: DREAMS.md generation reads from manifest
   - Touchpoint 9: Load appends to manifest; forget removes from manifest

5. **`undo_reorder()` operation**

6. **Command surface**: Expose operations through `/mentor reorder <operation>` or natural language via dream-mentor agent.

**Estimated scope**: Modify 5 files (SKILL.md merge algorithm, resolver.md, memory-writer.md, dream-mentor.md, mentor.md command). Create 1 new file or code module for manifest management.

**Validation**: Existing merge behavior produces identical results before and after migration (verify by comparing merge output with old priorities vs. new manifest ordering for the same dream set).

### Phase 2: Preview System

**Goal**: Show users what would change before committing a reorder.

**Deliverables**:

1. **`preview_reorder()` function**
   - Simulate reorder without writing
   - Run merge with both old and new ordering
   - Diff the two merged results

2. **`simulate_reorder()` function** (pure, no side effects)

3. **Formatted preview output** (table of changed conflict resolutions and merged values)

4. **Integration**: Default to preview for reorders that change conflict resolutions. Direct-apply for non-impactful reorders.

5. **`--preview` / `--dry-run` flag** on reorder commands.

**Estimated scope**: 1 new module (preview engine). Modify reorder operations to optionally route through preview.

**Validation**: Preview output matches actual changes when reorder is applied.

### Phase 3: Context-Aware Ordering

**Goal**: Layer priority can change based on what file the user is editing.

**Deliverables**:

1. **Context rule schema** in `manifest.json`

2. **`get_effective_order(context)` function** (replaces simple manifest read)

3. **Session pin** (`.session_pin.json`)

4. **Rule management commands**: `context add`, `context list`, `context remove`, `pin`, `unpin`

5. **Update merge and resolver** to pass context through

6. **Update `list` display** to show context boost column

**Estimated scope**: Extend manifest schema. Modify `get_effective_order()`. Add rule management commands. Modify list display.

**Dependency**: Phase 1 must be complete. Phase 2 is recommended (context changes should be previewable) but not strictly required.

**Validation**: Merge output changes correctly when context rules fire. Rules that do not match produce no change.

### Phase 4: Polish and Robustness

**Goal**: Handle all edge cases, improve UX.

**Deliverables**:

1. **Manifest sync validation** on session start
2. **Graceful handling** of all edge cases from Section 6
3. **Natural language reorder** via dream-mentor agent: "put testing-patterns in front of architecture-ref" maps to `move_before(testing-patterns, architecture-ref)`
4. **Batch reorder**: "sort dreams alphabetically" or "reverse the order" as compound operations
5. **Conflict rule warnings** when adding rules that overlap

**Estimated scope**: Incremental improvements across existing code.

---

## Appendix A: Summary of Data Structure Changes

| File | Current | After Phase 1 |
|------|---------|---------------|
| `.claude/dreams/manifest.json` | Does not exist | New file. Single source of truth for ordering. |
| `.claude/dreams/<name>/layer.json` | `{ priority: N, active: bool, tags: [...] }` | `{ active: bool, tags: [...] }` — priority field removed |
| `.claude/dreams/DREAMS.md` | Generated from layer.json priorities | Generated from manifest.json order |
| `.claude/dreams/.session_pin.json` | Does not exist | Phase 3: ephemeral session pin |

## Appendix B: Summary of Algorithm Complexities

| Operation | Time Complexity | Disk Writes |
|-----------|----------------|-------------|
| move_to_front | O(n) | 1 (manifest.json) + 1 (DREAMS.md) |
| move_to_back | O(n) | 1 + 1 |
| move_before | O(n) | 1 + 1 |
| move_after | O(n) | 1 + 1 |
| swap | O(n) | 1 + 1 |
| promote | O(n) | 1 + 1 |
| demote | O(n) | 1 + 1 |
| undo_reorder | O(n) | 1 + 1 |
| preview_reorder | O(n * k) where k = total keys across all dreams | 0 (read-only) |
| get_effective_order | O(n * r) where r = number of context rules | 0 (read-only) |

All operations write at most 2 files (manifest + DREAMS.md), compared to the current system which would need to rewrite up to N `layer.json` files for a single reorder.

## Appendix C: Backward Compatibility Guarantees

1. **Lazy migration**: Systems with `layer.json` containing `priority` fields continue to work. On first access, `read_manifest()` detects the missing manifest and auto-migrates.
2. **No data loss**: Migration preserves exact ordering. Alphabetical tiebreak for same-priority dreams matches the existing resolver behavior.
3. **DREAMS.md format**: The human-readable format of DREAMS.md does not change. "priority 1" remains "priority 1" — it just comes from array position instead of `layer.json`.
4. **layer.json still exists**: Per-dream metadata (`active`, `tags`, `created_at`) remains in `layer.json`. Only `priority` is removed.
5. **Existing load/forget flows**: Load appends to manifest (equivalent to max+1). Forget removes from manifest (cleaner than compact — no renumbering side effects).
