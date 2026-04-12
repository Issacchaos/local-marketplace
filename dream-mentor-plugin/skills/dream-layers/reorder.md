# Reorder Sub-Skill

**Parent**: `skills/dream-layers/SKILL.md`
**Purpose**: Explicit reorder operations for changing dream layer ordering within the relevance tensor, with preview support and undo history.

---

## Overview

The reorder sub-skill provides eight operations for manipulating the `base_order` array in `tensor.json`. Every operation follows the same lifecycle:

1. Read the tensor (with lazy migration if needed)
2. Validate inputs
3. Snapshot the current order for history
4. Compute the new order
5. Recalculate base weights
6. Write the tensor with a history entry
7. Regenerate `DREAMS.md`

All operations are idempotent when the requested state already holds -- they return `{ changed: false }` with an explanatory message instead of erroring.

---

## Common Helpers

### read_tensor()

```
function read_tensor(): Tensor {
  path = ".claude/dreams/tensor.json"

  if (!exists(path)):
    // Lazy migration: build tensor from existing dreams
    return migrate_to_tensor()

  tensor = read_json(path)

  // Validate sync with dream directories on disk
  tensor = validate_tensor_sync(tensor)

  return tensor
```

### validate_tensor_sync()

Ensure the tensor's `base_order` matches the dream directories that actually exist on disk.

```
function validate_tensor_sync(tensor: Tensor): Tensor {
  dream_dirs = list_dream_directories()  // Actual directories under .claude/dreams/
  changed = false

  // Remove phantoms: in tensor but not on disk
  phantoms = tensor.base_order.filter(name => name not in dream_dirs)
  if (phantoms.length > 0):
    tensor.base_order = tensor.base_order.filter(name => name in dream_dirs)
    // Also clean weight entries for removed dreams
    for (phantom of phantoms):
      delete tensor.weights[phantom]
    warn("Removed {phantoms} from tensor -- directories not found.")
    changed = true

  // Append orphans: on disk but not in tensor
  orphans = dream_dirs.filter(name => name not in tensor.base_order)
  if (orphans.length > 0):
    for (name of orphans):
      tensor.base_order.push(name)
      // Initialize weights from semantic profile if available
      tensor.weights[name] = load_initial_weights(name)
    warn("Added {orphans} to tensor -- directories found but not in ordering.")
    changed = true

  if (changed):
    write_json(".claude/dreams/tensor.json", tensor)

  return tensor
```

### write_tensor_with_history()

```
function write_tensor_with_history(tensor: Tensor, operation: string, args: object, old_order: string[]):
  // Record history (bounded ring buffer, max 20 entries)
  entry = {
    timestamp: now_iso(),
    operation: operation,
    args: args,
    previous_order: old_order,
    new_order: [...tensor.base_order]
  }
  tensor.reorder_history.push(entry)
  if (tensor.reorder_history.length > 20):
    tensor.reorder_history.shift()  // Drop oldest

  tensor.last_reorder = entry.timestamp
  write_json(".claude/dreams/tensor.json", tensor)
  regenerate_dreams_index(tensor)
```

### recalculate_base_weights()

After any reorder, update the `_base` context weights in the tensor so that position in `base_order` is reflected as a weight gradient.

```
function recalculate_base_weights(tensor: Tensor):
  n = tensor.base_order.length
  if (n === 0):
    return

  for (i = 0; i < n; i++):
    dream = tensor.base_order[i]
    // Linear decay: position 0 gets 1.0, last position gets a floor of 0.1
    // This ensures even the lowest-priority dream has nonzero base weight
    base_weight = 1.0 - (i * 0.9 / Math.max(n - 1, 1))
    base_weight = Math.round(base_weight * 100) / 100

    // Set the _base context weight for every category this dream covers
    if (!tensor.weights[dream]):
      tensor.weights[dream] = {}
    for (category of Object.keys(tensor.weights[dream])):
      if (!tensor.weights[dream][category]):
        tensor.weights[dream][category] = {}
      tensor.weights[dream][category]["_base"] = base_weight
```

### validate_dream_exists()

```
function validate_dream_exists(tensor: Tensor, name: string):
  if (name not in tensor.base_order):
    loaded = tensor.base_order.join(", ")
    throw Error("Dream '{name}' not found in tensor. Loaded dreams: {loaded}")
```

### active_order()

```
function active_order(tensor: Tensor): string[] {
  // Returns only active dreams in base_order sequence
  return tensor.base_order.filter(name => {
    layer = read_json(".claude/dreams/{name}/layer.json")
    return layer.active !== false
  })
```

---

## Reorder Operations

### 1. move_to_front(dream)

Set the given dream to highest priority (position 0 in `base_order`).

```
function move_to_front(dream: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)

  old_order = [...tensor.base_order]

  // Already at front?
  if (tensor.base_order[0] === dream):
    return { changed: false, message: "'{dream}' is already at highest priority." }

  // Edge case: single dream
  if (tensor.base_order.length === 1):
    return { changed: false, message: "Only one dream loaded. It is already at highest priority." }

  // Remove from current position, insert at front
  tensor.base_order = tensor.base_order.filter(d => d !== dream)
  tensor.base_order.unshift(dream)

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "move_to_front", { dream }, old_order)

  return {
    changed: true,
    old_position: old_order.indexOf(dream) + 1,
    new_position: 1,
    order: [...tensor.base_order]
  }
```

### 2. move_to_back(dream)

Set the given dream to lowest priority (last position in `base_order`).

```
function move_to_back(dream: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)

  old_order = [...tensor.base_order]
  last_index = tensor.base_order.length - 1

  // Already at back?
  if (tensor.base_order[last_index] === dream):
    return { changed: false, message: "'{dream}' is already at lowest priority." }

  // Edge case: single dream
  if (tensor.base_order.length === 1):
    return { changed: false, message: "Only one dream loaded. It is already at lowest priority." }

  // Remove from current position, append at end
  tensor.base_order = tensor.base_order.filter(d => d !== dream)
  tensor.base_order.push(dream)

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "move_to_back", { dream }, old_order)

  return {
    changed: true,
    old_position: old_order.indexOf(dream) + 1,
    new_position: tensor.base_order.length,
    order: [...tensor.base_order]
  }
```

### 3. move_before(dream, target)

Insert `dream` immediately before `target` in the ordering.

```
function move_before(dream: string, target: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)
  validate_dream_exists(tensor, target)

  // Self-reference check
  if (dream === target):
    return { changed: false, message: "Cannot move a dream before itself." }

  old_order = [...tensor.base_order]

  // Remove dream from current position
  tensor.base_order = tensor.base_order.filter(d => d !== dream)

  // Find target's position in the reduced array
  target_index = tensor.base_order.indexOf(target)

  // Insert dream immediately before target
  tensor.base_order.splice(target_index, 0, dream)

  // Check if order actually changed
  if (arrays_equal(old_order, tensor.base_order)):
    return { changed: false, message: "'{dream}' is already immediately before '{target}'." }

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "move_before", { dream, target }, old_order)

  return {
    changed: true,
    old_position: old_order.indexOf(dream) + 1,
    new_position: tensor.base_order.indexOf(dream) + 1,
    order: [...tensor.base_order]
  }
```

### 4. move_after(dream, target)

Insert `dream` immediately after `target` in the ordering.

```
function move_after(dream: string, target: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)
  validate_dream_exists(tensor, target)

  // Self-reference check
  if (dream === target):
    return { changed: false, message: "Cannot move a dream after itself." }

  old_order = [...tensor.base_order]

  // Remove dream from current position
  tensor.base_order = tensor.base_order.filter(d => d !== dream)

  // Find target's position in the reduced array
  target_index = tensor.base_order.indexOf(target)

  // Insert dream immediately after target
  tensor.base_order.splice(target_index + 1, 0, dream)

  // Check if order actually changed
  if (arrays_equal(old_order, tensor.base_order)):
    return { changed: false, message: "'{dream}' is already immediately after '{target}'." }

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "move_after", { dream, target }, old_order)

  return {
    changed: true,
    old_position: old_order.indexOf(dream) + 1,
    new_position: tensor.base_order.indexOf(dream) + 1,
    order: [...tensor.base_order]
  }
```

### 5. swap(dream_a, dream_b)

Exchange the positions of two dreams.

```
function swap(dream_a: string, dream_b: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream_a)
  validate_dream_exists(tensor, dream_b)

  // Self-swap check
  if (dream_a === dream_b):
    return { changed: false, message: "Cannot swap a dream with itself." }

  old_order = [...tensor.base_order]

  index_a = tensor.base_order.indexOf(dream_a)
  index_b = tensor.base_order.indexOf(dream_b)

  // Swap in place
  tensor.base_order[index_a] = dream_b
  tensor.base_order[index_b] = dream_a

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "swap", { dream_a, dream_b }, old_order)

  return {
    changed: true,
    dream_a: { old_position: index_a + 1, new_position: index_b + 1 },
    dream_b: { old_position: index_b + 1, new_position: index_a + 1 },
    order: [...tensor.base_order]
  }
```

### 6. promote(dream)

Move up one position toward higher priority (lower index).

```
function promote(dream: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)

  index = tensor.base_order.indexOf(dream)

  // Already at top?
  if (index === 0):
    return { changed: false, message: "'{dream}' is already at highest priority." }

  old_order = [...tensor.base_order]

  // Swap with the dream directly above
  neighbor = tensor.base_order[index - 1]
  tensor.base_order[index - 1] = dream
  tensor.base_order[index] = neighbor

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "promote", { dream }, old_order)

  return {
    changed: true,
    old_position: index + 1,
    new_position: index,
    swapped_with: neighbor,
    order: [...tensor.base_order]
  }
```

### 7. demote(dream)

Move down one position toward lower priority (higher index).

```
function demote(dream: string):
  tensor = read_tensor()
  validate_dream_exists(tensor, dream)

  index = tensor.base_order.indexOf(dream)

  // Already at bottom?
  if (index === tensor.base_order.length - 1):
    return { changed: false, message: "'{dream}' is already at lowest priority." }

  old_order = [...tensor.base_order]

  // Swap with the dream directly below
  neighbor = tensor.base_order[index + 1]
  tensor.base_order[index + 1] = dream
  tensor.base_order[index] = neighbor

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "demote", { dream }, old_order)

  return {
    changed: true,
    old_position: index + 1,
    new_position: index + 2,
    swapped_with: neighbor,
    order: [...tensor.base_order]
  }
```

### 8. undo_reorder()

Revert the most recent reorder operation by restoring `previous_order` from the history stack.

```
function undo_reorder():
  tensor = read_tensor()

  if (!tensor.reorder_history || tensor.reorder_history.length === 0):
    return { changed: false, message: "No reorder operations to undo." }

  last_entry = tensor.reorder_history.pop()

  // Validate that the previous order is still plausible
  // (all dreams in previous_order should still exist on disk)
  dream_dirs = list_dream_directories()
  valid_previous = last_entry.previous_order.filter(name => name in dream_dirs)
  orphans = dream_dirs.filter(name => name not in last_entry.previous_order)

  // Use the validated previous order, appending any orphans that appeared since
  tensor.base_order = valid_previous.concat(orphans)

  recalculate_base_weights(tensor)
  tensor.last_reorder = now_iso()
  write_json(".claude/dreams/tensor.json", tensor)
  regenerate_dreams_index(tensor)

  return {
    changed: true,
    undone_operation: last_entry.operation,
    restored_order: [...tensor.base_order],
    order: [...tensor.base_order]
  }
```

**Note**: Undo does not push its own history entry. Repeated undo calls walk back through the history stack. This is standard undo behavior -- there is no redo.

---

## Preview System

The preview system lets users see what would change before committing a reorder. It runs the full merge and conflict resolution pipeline with both the current and proposed ordering, then diffs the results.

### preview_reorder()

```
function preview_reorder(operation: string, args: object): PreviewResult {
  tensor = read_tensor()

  // Step 1: Compute current merged state
  current_order = active_order(tensor)
  current_merged = run_merge(current_order)
  current_conflicts = detect_conflicts(current_order)

  // Step 2: Compute proposed order without persisting
  proposed_base_order = simulate_reorder(tensor, operation, args)

  // Filter to active dreams only (same filter as active_order)
  proposed_active = proposed_base_order.filter(name => {
    layer = read_json(".claude/dreams/{name}/layer.json")
    return layer.active !== false
  })

  // Step 3: Compute proposed merged state
  proposed_merged = run_merge(proposed_active)
  proposed_conflicts = detect_conflicts(proposed_active)

  // Step 4: Diff the two merged states
  changes = diff_merged_states(current_merged, proposed_merged)
  conflict_changes = diff_conflict_resolutions(current_conflicts, proposed_conflicts)

  return {
    current_order: current_order,
    proposed_order: proposed_active,
    changes: changes,
    conflict_changes: conflict_changes,
    summary: format_preview(changes, conflict_changes, current_order, proposed_active)
  }
```

### simulate_reorder()

A pure function that returns the proposed order without writing to disk or modifying the tensor.

```
function simulate_reorder(tensor: Tensor, operation: string, args: object): string[] {
  // Clone the base_order
  simulated = [...tensor.base_order]

  switch (operation):
    case "move_to_front":
      validate_dream_exists(tensor, args.dream)
      if (simulated[0] === args.dream):
        return simulated  // No change
      simulated = simulated.filter(d => d !== args.dream)
      simulated.unshift(args.dream)

    case "move_to_back":
      validate_dream_exists(tensor, args.dream)
      if (simulated[simulated.length - 1] === args.dream):
        return simulated
      simulated = simulated.filter(d => d !== args.dream)
      simulated.push(args.dream)

    case "move_before":
      validate_dream_exists(tensor, args.dream)
      validate_dream_exists(tensor, args.target)
      if (args.dream === args.target):
        return simulated
      simulated = simulated.filter(d => d !== args.dream)
      idx = simulated.indexOf(args.target)
      simulated.splice(idx, 0, args.dream)

    case "move_after":
      validate_dream_exists(tensor, args.dream)
      validate_dream_exists(tensor, args.target)
      if (args.dream === args.target):
        return simulated
      simulated = simulated.filter(d => d !== args.dream)
      idx = simulated.indexOf(args.target)
      simulated.splice(idx + 1, 0, args.dream)

    case "swap":
      validate_dream_exists(tensor, args.dream_a)
      validate_dream_exists(tensor, args.dream_b)
      if (args.dream_a === args.dream_b):
        return simulated
      idx_a = simulated.indexOf(args.dream_a)
      idx_b = simulated.indexOf(args.dream_b)
      simulated[idx_a] = args.dream_b
      simulated[idx_b] = args.dream_a

    case "promote":
      validate_dream_exists(tensor, args.dream)
      idx = simulated.indexOf(args.dream)
      if (idx === 0):
        return simulated
      neighbor = simulated[idx - 1]
      simulated[idx - 1] = args.dream
      simulated[idx] = neighbor

    case "demote":
      validate_dream_exists(tensor, args.dream)
      idx = simulated.indexOf(args.dream)
      if (idx === simulated.length - 1):
        return simulated
      neighbor = simulated[idx + 1]
      simulated[idx + 1] = args.dream
      simulated[idx] = neighbor

    default:
      throw Error("Unknown reorder operation: '{operation}'")

  return simulated
```

### diff_merged_states()

Compare two merged results to find keys whose source attribution changed.

```
function diff_merged_states(current: MergedDream, proposed: MergedDream): MergedChange[] {
  changes = []

  for (category of ["structure", "patterns", "conventions"]):
    all_keys = union(
      Object.keys(current[category] ?? {}),
      Object.keys(proposed[category] ?? {})
    )

    for (key of all_keys):
      current_entry = current[category]?.[key]
      proposed_entry = proposed[category]?.[key]

      // Key exists in both but source changed
      if (current_entry && proposed_entry):
        if (current_entry.source !== proposed_entry.source):
          changes.push({
            category: category,
            key: key,
            current_value: current_entry.value,
            current_source: current_entry.source,
            new_value: proposed_entry.value,
            new_source: proposed_entry.source
          })

      // Key only in proposed (new dream moved into winning position)
      else if (!current_entry && proposed_entry):
        changes.push({
          category: category,
          key: key,
          current_value: null,
          current_source: null,
          new_value: proposed_entry.value,
          new_source: proposed_entry.source
        })

      // Key only in current (dream moved out of winning position -- unlikely but defensive)
      else if (current_entry && !proposed_entry):
        changes.push({
          category: category,
          key: key,
          current_value: current_entry.value,
          current_source: current_entry.source,
          new_value: null,
          new_source: null
        })

  return changes
```

### diff_conflict_resolutions()

Compare conflict resolution outcomes between current and proposed orderings.

```
function diff_conflict_resolutions(
  current_conflicts: Conflict[],
  proposed_conflicts: Conflict[]
): ConflictChange[] {
  changes = []

  // Build lookup maps: category.key -> resolution
  current_map = {}
  for (c of current_conflicts):
    current_map[c.category + "." + c.key] = c.resolution

  proposed_map = {}
  for (c of proposed_conflicts):
    proposed_map[c.category + "." + c.key] = c.resolution

  // Find conflicts where the winner changed
  all_conflict_keys = union(Object.keys(current_map), Object.keys(proposed_map))
  for (conflict_key of all_conflict_keys):
    current_winner = current_map[conflict_key]
    proposed_winner = proposed_map[conflict_key]

    if (current_winner && proposed_winner && current_winner !== proposed_winner):
      [category, key] = conflict_key.split(".", 2)
      changes.push({
        category: category,
        key: key,
        current_winner: current_winner,
        new_winner: proposed_winner
      })

  return changes
```

### format_preview()

Format the preview diff as human-readable markdown output.

```
function format_preview(
  changes: MergedChange[],
  conflict_changes: ConflictChange[],
  current_order: string[],
  proposed_order: string[]
): string {
  output = "## Reorder Preview\n\n"

  // Show order change
  output += "### Order Change\n"
  output += "Before: " + format_order_line(current_order) + "\n"
  output += "After:  " + format_order_line(proposed_order) + "\n\n"

  // No impact case
  if (changes.length === 0 && conflict_changes.length === 0):
    output += "No changes to merged output. "
    output += "The reorder does not affect any conflict resolutions.\n"
    return output

  // Conflict resolution changes
  if (conflict_changes.length > 0):
    output += "### Conflict Resolutions That Would Change\n\n"
    output += "| Category | Key | Current Winner | New Winner |\n"
    output += "|----------|-----|----------------|------------|\n"
    display_count = Math.min(conflict_changes.length, 20)
    for (i = 0; i < display_count; i++):
      c = conflict_changes[i]
      output += "| {c.category} | {c.key} | {c.current_winner} | {c.new_winner} |\n"
    if (conflict_changes.length > 20):
      output += "\n... and {conflict_changes.length - 20} more.\n"
    output += "\n"

  // Merged value changes
  if (changes.length > 0):
    output += "### Merged Values That Would Change\n\n"
    display_count = Math.min(changes.length, 20)
    for (i = 0; i < display_count; i++):
      ch = changes[i]
      if (ch.current_value && ch.new_value):
        output += "- **{ch.category}.{ch.key}**: "
        output += "`{ch.current_value}` (from {ch.current_source}) "
        output += "-> `{ch.new_value}` (from {ch.new_source})\n"
      else if (ch.new_value):
        output += "- **{ch.category}.{ch.key}**: "
        output += "(none) -> `{ch.new_value}` (from {ch.new_source})\n"
      else if (ch.current_value):
        output += "- **{ch.category}.{ch.key}**: "
        output += "`{ch.current_value}` (from {ch.current_source}) -> (none)\n"
    if (changes.length > 20):
      output += "\n... and {changes.length - 20} more.\n"

  // Summary line
  total = conflict_changes.length + changes.length
  output += "\n**{total} change(s) detected.** "
  if (conflict_changes.length > 0):
    output += "**{conflict_changes.length} conflict resolution(s) would change.** "
  output += "Apply this reorder? [Yes / Cancel]\n"

  return output


function format_order_line(order: string[]): string {
  return order.map((name, i) => "{name} ({i + 1})").join(" > ")
```

### execute_reorder_with_preview()

Integration helper that decides whether to show a preview or apply directly.

```
function execute_reorder_with_preview(operation: string, args: object, force: boolean = false):
  // Run preview first
  preview = preview_reorder(operation, args)

  if (preview.conflict_changes.length === 0 || force):
    // Safe to apply directly (no conflict impact, or user forced)
    result = apply_reorder(operation, args)
    return { applied: true, result, preview }
  else:
    // Show preview and ask for confirmation
    display(preview.summary)
    confirm = ask_user("Apply this reorder?", ["Yes", "Cancel"])
    if (confirm === "Yes"):
      result = apply_reorder(operation, args)
      return { applied: true, result, preview }
    else:
      return { applied: false, preview }


function apply_reorder(operation: string, args: object):
  switch (operation):
    case "move_to_front": return move_to_front(args.dream)
    case "move_to_back":  return move_to_back(args.dream)
    case "move_before":   return move_before(args.dream, args.target)
    case "move_after":    return move_after(args.dream, args.target)
    case "swap":          return swap(args.dream_a, args.dream_b)
    case "promote":       return promote(args.dream)
    case "demote":        return demote(args.dream)
    case "undo":          return undo_reorder()
    default:
      throw Error("Unknown reorder operation: '{operation}'")
```

---

## Integration with Tensor

Each reorder operation modifies `tensor.base_order` and calls `recalculate_base_weights()` to keep the `_base` context weights consistent with the new ordering. The relationship:

```
tensor.json
  base_order: ["architecture-ref", "testing-patterns", "ui-reference"]
  weights:
    "architecture-ref":
      "patterns.architecture":
        "_base": 1.0       // position 0 -> weight 1.0
        "file.test": 0.3   // semantic weight (unchanged by reorder)
      "conventions.testing":
        "_base": 1.0
        "file.test": 0.2
    "testing-patterns":
      "patterns.architecture":
        "_base": 0.55      // position 1 -> weight 0.55
        "file.test": 0.9
      "conventions.testing":
        "_base": 0.55
        "file.test": 0.95
    "ui-reference":
      "patterns.architecture":
        "_base": 0.10      // position 2 -> weight 0.10
        "file.test": 0.1
```

When a reorder changes `base_order`, only the `_base` weights are recalculated. Semantic weights (from the semantic extractor) and context-specific weights are untouched. The ordering resolver combines these at query time:

```
effective_weight = tensor.weights[dream][category][context]
                 ?? tensor.weights[dream][category]["_base"]
                 ?? 0.0
```

### On Dream Load

When a new dream is loaded, it is appended to `tensor.base_order` (lowest priority by default) and `recalculate_base_weights()` runs to adjust all dreams' `_base` weights.

### On Dream Forget

When a dream is forgotten, it is removed from `tensor.base_order`, its weight entries are deleted, and `recalculate_base_weights()` runs. The reorder history is pruned to remove entries referencing the forgotten dream:

```
function on_dream_forget(dream_name: string):
  tensor = read_tensor()
  old_order = [...tensor.base_order]

  tensor.base_order = tensor.base_order.filter(d => d !== dream_name)
  delete tensor.weights[dream_name]

  // Prune history entries that reference the forgotten dream
  tensor.reorder_history = tensor.reorder_history.filter(entry =>
    !entry.previous_order.includes(dream_name) &&
    !entry.new_order.includes(dream_name)
  )

  recalculate_base_weights(tensor)
  write_tensor_with_history(tensor, "forget", { dream: dream_name }, old_order)
```

---

## Edge Cases

### Single Dream

All positional operations (`move_to_front`, `move_to_back`, `promote`, `demote`) return `{ changed: false }` with a message like "Only one dream loaded." Relational operations (`move_before`, `move_after`, `swap`) fail validation because the second dream does not exist.

### Already at Requested Position

Each operation checks its precondition before mutating:
- `move_to_front` checks `base_order[0] === dream`
- `move_to_back` checks `base_order[last] === dream`
- `promote` checks `index === 0`
- `demote` checks `index === length - 1`
- `move_before` / `move_after` compare old and new order via `arrays_equal()`

All return `{ changed: false }` with an explanatory message. No history entry is created.

### Self-Swap / Self-Reference

`swap(A, A)`, `move_before(A, A)`, and `move_after(A, A)` are caught before any mutation:
```
if (dream === target): return { changed: false, message: "Cannot swap/move a dream with/before/after itself." }
```

### Undo with Empty History

`undo_reorder()` returns `{ changed: false, message: "No reorder operations to undo." }` when the history stack is empty.

### Undo After Forget

If a dream was forgotten since the last reorder, `undo_reorder()` validates the restored order against disk. Dreams that no longer exist on disk are excluded. Dreams that appeared since are appended. This prevents restoring a phantom dream reference.

### Concurrent Access

In the current single-agent Claude Code model, operations are sequential. If a future multi-agent architecture allows parallel reorder requests, the last writer wins (file-level atomicity). The history stack provides recovery. For the per-agent overlay model (see research report), each agent computes its own effective ordering in memory -- only explicit user reorders write to `tensor.json`.

### Empty Tensor / No Dreams

All operations fail validation with "Dream '{name}' not found in tensor." The preview system returns an empty diff. `undo_reorder()` returns no-op.

### Very Large Dream Count (>20)

All operations are O(n) on `base_order` length, acceptable for n < 100. The preview system caps its formatted output at 20 entries per section with a "... and N more" overflow indicator.

---

## Command Surface

These operations are exposed through the dream-mentor agent via natural language or explicit commands:

```
/mentor reorder move-front <dream>
/mentor reorder move-back <dream>
/mentor reorder before <dream> <target>
/mentor reorder after <dream> <target>
/mentor reorder swap <dream_a> <dream_b>
/mentor reorder promote <dream>
/mentor reorder demote <dream>
/mentor reorder undo

# Preview mode (any operation)
/mentor reorder <operation> [args] --preview
/mentor reorder <operation> [args] --dry-run

# Force mode (skip preview even if conflicts change)
/mentor reorder <operation> [args] --force
```

Natural language mappings in the dream-mentor agent:
- "put testing-patterns first" -> `move_to_front("testing-patterns")`
- "make architecture-ref lowest priority" -> `move_to_back("architecture-ref")`
- "move testing before architecture" -> `move_before("testing-patterns", "architecture-ref")`
- "swap testing and architecture" -> `swap("testing-patterns", "architecture-ref")`
- "bump up ui-reference" -> `promote("ui-reference")`
- "lower testing-patterns" -> `demote("testing-patterns")`
- "undo that reorder" -> `undo_reorder()`
- "what would happen if I moved testing first?" -> `preview_reorder("move_to_front", { dream: "testing-patterns" })`
