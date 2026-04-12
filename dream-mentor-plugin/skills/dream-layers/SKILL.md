# Dream Layers Skill

**Description**: Manage layered composition of multiple dream states with context-aware, tensor-based conflict resolution.

**Trigger**: Used by the `/dream` command when working with multiple dreams or producing merged guidance.

---

## Overview

The dream-layers skill enables loading multiple reference repos as layered dream states. Each dream is positioned in a relevance tensor (`tensor.json`), and when patterns conflict between dreams, the dream with higher effective relevance for the current context wins. Ordering is context-aware — a testing-focused dream can be boosted when working on test files, even if it has lower base precedence.

### Use Cases

- **Architecture from Repo A, testing from Repo B**: Load repo A first for structure/patterns, repo B second for testing conventions — tensor auto-boosts each dream for its relevant contexts
- **Framework reference + domain reference**: Base framework patterns loaded first, domain-specific patterns loaded second — context-aware ordering adapts which dominates
- **Progressive refinement**: Start with a broad reference, add specialized overlays

---

## Layer Model

### Priority System

- Priorities are derived from the `base_order` array in `tensor.json` — index 0 = highest precedence
- Each dream occupies a unique position in the ordering; there are no numeric priority fields
- When loading a new dream without `--layer`, it is appended to the end of `base_order` (lowest precedence)
- Ordering can be changed via the reorder operations defined in `reorder.md`
- Effective ordering varies by context — when working on test files, testing-focused dreams are automatically boosted
- See `tensor.md` for the full ordering algorithm (`get_tensor_ordering(context)`)

### Conflict Resolution Rules

1. **Non-conflicting patterns merge**: If dream A defines testing conventions and dream B defines deployment patterns, both apply
2. **Conflicting patterns**: Higher-precedence dream wins (earlier position in effective tensor ordering)
3. **Additive content**: Dependencies from all layers are merged (union)
4. **Structure**: Higher-precedence dream's structure is preferred when directories serve the same purpose

### What Constitutes a Conflict

| Area | Conflict Example | Resolution |
|------|-----------------|------------|
| Architecture style | Dream A: microservices, Dream B: monolith | Higher precedence wins |
| Naming conventions | Dream A: kebab-case, Dream B: camelCase | Higher precedence wins |
| Test framework | Dream A: Jest, Dream B: Vitest | Higher precedence wins |
| Test location | Dream A: colocated, Dream B: separate dir | Higher precedence wins |
| Dependencies | Dream A: axios, Dream B: fetch | Both included (additive) |
| Directory structure | Dream A: `src/features/`, Dream B: `src/modules/` | Higher precedence wins |
| Error handling | Dream A: Result types, Dream B: exceptions | Higher precedence wins |

---

## Merged View

When `/mentor diff` or `/mentor status` runs without `--name`, the layers skill produces a merged view.

### Merge Algorithm

```
function merge_layers(dreams: Dream[], current_context): MergedDream {
  // Sort by tensor ordering for the current context (index 0 = highest precedence)
  // current_context comes from the calling agent/operation (e.g., { active_file, query, task })
  effective_order = get_tensor_ordering(current_context)
  dreams.sort((a, b) => effective_order.indexOf(a.name) - effective_order.indexOf(b.name));

  merged = {
    structure: {},
    patterns: {},
    dependencies: { production: [], dev: [] },
    conventions: {},
    summary: ""
  };

  for (dream of dreams) {
    // Structure: higher priority fills first, lower priority fills gaps
    for (section of dream.structure) {
      if (!merged.structure[section.key]) {
        merged.structure[section.key] = {
          value: section.value,
          source: dream.name
        };
      }
    }

    // Patterns: same as structure - first write wins
    for (pattern of dream.patterns) {
      if (!merged.patterns[pattern.key]) {
        merged.patterns[pattern.key] = {
          value: pattern.value,
          source: dream.name
        };
      }
    }

    // Dependencies: additive merge (union)
    merged.dependencies.production = union(
      merged.dependencies.production,
      dream.dependencies.production
    );
    merged.dependencies.dev = union(
      merged.dependencies.dev,
      dream.dependencies.dev
    );

    // Conventions: same as patterns - first write wins
    for (convention of dream.conventions) {
      if (!merged.conventions[convention.key]) {
        merged.conventions[convention.key] = {
          value: convention.value,
          source: dream.name
        };
      }
    }
  }

  // Summary: concatenate with attribution
  merged.summary = dreams.map((d, idx) =>
    `**From ${d.name} (position ${idx + 1})**: ${d.summary.brief}`
  ).join('\n\n');

  return merged;
}
```

### Merged View Output

```markdown
# Merged Dream View

**Active layers** (ordered by effective relevance):
1. architecture-ref — GitHub: org/repo
2. testing-patterns — Local: /path/to/repo
3. ui-reference — GitHub: org/ui-lib

**Context**: _base (default ordering)
> Ordering is context-aware. Effective order may differ when working on test files,
> components, or other specialized contexts. See `tensor.md` for details.

## Structure (from: architecture-ref)
{merged structure with source attribution}

## Patterns
- Architecture style: microservices (from: architecture-ref)
- Naming: kebab-case (from: architecture-ref)
- Test organization: colocated (from: testing-patterns)
- Component patterns: atomic design (from: ui-reference)

## Dependencies (merged from all layers)
{union of all dependencies with source attribution}

## Conventions
- Testing framework: Vitest (from: testing-patterns)
- Build system: Vite (from: architecture-ref)
- CI/CD: GitHub Actions (from: architecture-ref)
```

---

## Layer Operations

### Reorder Operations

Layer ordering is managed through the `reorder.md` sub-skill, which provides 8 operations:
`move_to_front`, `move_to_back`, `move_before`, `move_after`, `swap`, `promote`, `demote`, and `undo_reorder`.

All operations modify `base_order` in `tensor.json` and recalculate base weights automatically. When a dream is forgotten, it is removed from `base_order` — no gap compaction is needed since ordering is array-position-based, not numeric.

See `reorder.md` for full operation details, preview support, and undo history.

### Deactivate Without Removing

Set `active: false` in `layer.json` to temporarily exclude a dream from merged views without deleting its analysis:

```json
{
  "active": false,
  "tags": ["testing"],
  "semantic_profile": {
    "conventions.testing": 0.90,
    "conventions.testing.framework": 0.85
  }
}
```

### Tags

Dreams can be tagged for filtering:

```json
{
  "active": true,
  "tags": ["architecture", "patterns", "backend"],
  "semantic_profile": {
    "patterns.architecture": 0.95,
    "patterns.naming": 0.80,
    "structure": 0.90,
    "structure.directories": 0.85
  }
}
```

Tags are informational — they help users understand what each dream contributes but don't affect merge behavior.

---

## Sub-Skills

| Sub-Skill | File | Purpose |
|-----------|------|---------|
| Resolver | `resolver.md` | Conflict detection and resolution logic |
| Tensor | `tensor.md` | N*N*N relevance tensor for context-aware ordering |
| Trie | `trie.md` | Semantic prefix trie for precedence routing |
| Semantic Extractor | `semantic-extractor.md` | Context classification and semantic profiling |
| Reorder | `reorder.md` | Layer reorder operations and preview system |
