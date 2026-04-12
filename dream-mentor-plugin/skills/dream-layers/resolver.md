# Resolver Sub-Skill

**Parent**: `skills/dream-layers/SKILL.md`
**Purpose**: Detect and resolve conflicts between layered dream states.

---

## Conflict Detection

When producing a merged view, the resolver identifies overlapping guidance between dreams.

### Detection Algorithm

```
function detect_conflicts(dreams: Dream[], current_context): Conflict[] {
  // Note: conflict resolution is context-dependent — the same conflict
  // can resolve differently depending on which agent is querying and
  // what file/task they are working on.
  conflicts = [];

  // Compare each pair of dreams
  for (i = 0; i < dreams.length; i++) {
    for (j = i + 1; j < dreams.length; j++) {
      a = dreams[i];
      b = dreams[j];

      // Check each mergeable category
      for (category of ['structure', 'patterns', 'conventions']) {
        a_keys = extract_keys(a[category]);
        b_keys = extract_keys(b[category]);
        overlap = intersect(a_keys, b_keys);

        for (key of overlap) {
          if (a[category][key] !== b[category][key]) {
            // Determine resolution using tensor ordering (context-dependent)
            effective_order = get_tensor_ordering(current_context)
            pos_a = effective_order.indexOf(a.name)
            pos_b = effective_order.indexOf(b.name)

            conflicts.push({
              category: category,
              key: key,
              dream_a: { name: a.name, position: pos_a, value: a[category][key] },
              dream_b: { name: b.name, position: pos_b, value: b[category][key] },
              resolution: pos_a < pos_b ? a.name : b.name
            });
          }
        }
      }
    }
  }

  return conflicts;
}
```

### Conflict Categories

**Structure Conflicts**:
- Same-purpose directories with different names
- Entry point location differences
- Test directory placement differences

**Pattern Conflicts**:
- Architecture style (microservices vs monolith)
- Naming conventions (kebab-case vs camelCase)
- Error handling approach (Result types vs exceptions)
- State management (Redux vs Context vs signals)

**Convention Conflicts**:
- Testing framework (Jest vs Vitest vs pytest)
- Test organization (colocated vs separate)
- Build tool (webpack vs vite vs esbuild)
- Linter/formatter configuration
- CI/CD pipeline tool

**Non-Conflicting (Always Merged)**:
- Dependencies (additive union)
- External integrations (additive union)
- Documentation references (concatenated)

---

## Resolution Strategy

### Tensor-Based Resolution

The default strategy: the dream appearing earlier in the tensor's effective ordering wins. The effective ordering is context-dependent — `get_tensor_ordering(current_context)` determines it.

```
effective_order = get_tensor_ordering("_base")  // => ["architecture-ref", "testing-patterns"]

Dream A (architecture-ref, position 0): naming = "kebab-case"
Dream B (testing-patterns, position 1): naming = "camelCase"

Resolution: "kebab-case" (from architecture-ref, position 0)
```

### Resolution Report

When conflicts are resolved, produce a report:

```markdown
## Layer Conflicts Resolved

**Context**: _base (default ordering)

| Category | Key | Winner | Value | Overridden |
|----------|-----|--------|-------|------------|
| patterns | naming_convention | architecture-ref (#1) | kebab-case | testing-patterns (#2): camelCase |
| conventions | test_framework | testing-patterns (#1) | vitest | — (no conflict) |
| patterns | error_handling | architecture-ref (#1) | Result types | ui-reference (#3): try/catch |

**3 conflicts resolved** by tensor ordering. No manual intervention needed.
> Note: Resolution is context-dependent. In a different context (e.g., file.test),
> the effective ordering may differ and conflict winners may change.
```

---

## Merge Execution

### Step 1: Load All Active Dreams

```
Read tensor.json → get_tensor_ordering(current_context)
For each dream: read layer.json → filter to active: true
For each active: read all memory files
Order is already determined by the tensor — no separate sort needed
```

### Step 2: Detect Conflicts

Run conflict detection on all pairs of active dreams.

### Step 3: Resolve and Merge

```
merged = empty_dream()

for dream in sorted_active_dreams:
  for category in [structure, patterns, conventions]:
    for key, value in dream[category]:
      if key not in merged[category]:
        merged[category][key] = { value, source: dream.name }
      # else: already filled by higher-priority dream — skip

  # Dependencies: always additive
  merged.dependencies = union(merged.dependencies, dream.dependencies)

  # Summary: concatenate with attribution
  merged.summary += f"\n\n**{dream.name}**: {dream.summary.brief}"

return merged
```

### Step 4: Annotate Sources

Every entry in the merged view includes source attribution:

```markdown
- Architecture style: microservices *(from: architecture-ref, position #1)*
- Test framework: Vitest *(from: testing-patterns, position #2)*
- UI patterns: atomic design *(from: ui-reference, position #3)*
```

---

## Edge Cases

### Single Dream

When only one dream is loaded, the resolver returns it directly with no conflict detection.

### All Dreams Inactive

Return empty merged view with message:
```
No active dreams. Load a dream with /mentor load or reactivate with layer.json.
```

### Same Position (Eliminated)

The same-priority edge case is eliminated by the tensor approach — array indices in `base_order` are unique, so no two dreams can occupy the same position. If the tensor is missing or corrupted, fall back to alphabetical ordering of dream names as a safe default.

### Circular or Contradictory Guidance

If merged patterns are internally contradictory (e.g., "use microservices" + "keep everything in one module"):
- Let tensor ordering resolve it
- Note the contradiction in the resolution report
- Suggest the user review layer ordering via `reorder.md` operations

---

## Context-Dependent Resolution

With the tensor+trie ordering system, the same conflict can resolve differently depending on the context of the request. This is intentional — it means the merged guidance adapts to what the developer is actually working on.

### How It Works

1. The calling agent provides a `current_context` — either a string (e.g., `"file.test"`, `"query.architecture"`) or an object with ambient signals (`{ active_file, query, task }`).
2. `get_tensor_ordering(current_context)` returns a dream ordering that reflects the tensor weights for that context.
3. The resolver uses this ordering for both conflict detection (`detect_conflicts`) and the merge algorithm.

### Example: Same Conflict, Different Winners

```
Dreams loaded: architecture-ref, testing-patterns

Conflict: test framework preference
  architecture-ref says: Jest (weak testing coverage, score 0.3)
  testing-patterns says: Vitest (strong testing coverage, score 0.9)

Context: _base (default)
  effective_order = ["architecture-ref", "testing-patterns"]
  Winner: architecture-ref (Jest) — it comes first in base_order

Context: file.test (editing a .test.ts file)
  effective_order = ["testing-patterns", "architecture-ref"]
  Winner: testing-patterns (Vitest) — testing dream is boosted for test files

Context: query.architecture (asking about project structure)
  effective_order = ["architecture-ref", "testing-patterns"]
  Winner: architecture-ref (Jest) — architecture dream dominates for architecture queries
```

### When Context Is Unavailable

If no context is provided or the context cannot be classified, the resolver falls back to the `_base` context, which uses the `base_order` from `tensor.json`. This produces behavior equivalent to the old flat-priority system — the order the user explicitly set is respected.
