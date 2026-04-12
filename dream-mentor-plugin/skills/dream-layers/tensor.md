# Tensor Sub-Skill

**Parent**: `skills/dream-layers/SKILL.md`
**Purpose**: Manage the N x N x N relevance tensor that replaces flat numeric priorities for context-aware dream ordering.

---

## Overview

The tensor is a 3D matrix stored at `.claude/dreams/tensor.json`, indexed by `[dream][category][context]`. Each cell holds a floating-point relevance weight in the range [0.0, 1.0], answering: "How relevant is dream `d` for category `k` when working in context `c`?"

This replaces the flat `priority` integer in `layer.json` with a continuous, context-sensitive relevance model. The main entry point is `get_tensor_ordering(context)`, which returns an ordered list of dream names for any given situation.

---

## Tensor Schema

File: `.claude/dreams/tensor.json`

```json
{
  "version": 1,
  "dimensions": {
    "dreams": ["architecture-ref", "testing-patterns"],
    "categories": [
      "structure",
      "structure.directories",
      "structure.modules",
      "patterns",
      "patterns.architecture",
      "patterns.naming",
      "patterns.error_handling",
      "conventions",
      "conventions.testing",
      "conventions.testing.framework",
      "conventions.testing.organization",
      "conventions.testing.mocking",
      "conventions.build",
      "conventions.cicd",
      "dependencies",
      "dependencies.frameworks",
      "dependencies.libraries",
      "summary"
    ],
    "contexts": [
      "_base",
      "file.test",
      "file.component",
      "file.config",
      "file.ci",
      "file.build",
      "file.docs",
      "query.testing",
      "query.architecture",
      "query.dependencies",
      "task.diff",
      "task.load",
      "task.status"
    ]
  },
  "weights": [
    /* 3D array: weights[dream_idx][category_idx][context_idx]
       weights[0][2][1] = relevance of dreams[0] for categories[2] in contexts[1]
       All values in [0.0, 1.0] */
  ],
  "base_order": ["architecture-ref", "testing-patterns"],
  "history": [
    {
      "action": "reorder",
      "timestamp": "2026-04-12T10:00:00.000Z",
      "details": "move testing-patterns before architecture-ref for context query.testing"
    }
  ],
  "last_modified": "2026-04-12T10:00:00.000Z"
}
```

### Dimension Details

| Dimension | Key | Typical Size | Source |
|-----------|-----|-------------|--------|
| Dreams | `dimensions.dreams` | 2-20 | Names of loaded dreams from DREAMS.md |
| Categories | `dimensions.categories` | ~18 | Static taxonomy of content domains (see trie.md) |
| Contexts | `dimensions.contexts` | ~13 | File patterns, query types, task types |

### Size Estimates

| Dreams | Categories | Contexts | Memory | Disk |
|--------|-----------|----------|--------|------|
| 2 | 18 | 13 | ~4KB | ~8KB |
| 5 | 18 | 13 | ~10KB | ~20KB |
| 10 | 18 | 13 | ~20KB | ~40KB |
| 20 | 18 | 13 | ~40KB | ~80KB |

---

## Affinity Matrix

The static `KEY_CONTEXT_AFFINITY` mapping defines baseline relationships between categories and contexts. When a dream has strong coverage of a category, its weight is boosted in affiliated contexts.

```
KEY_CONTEXT_AFFINITY = {
  "structure":                    { "query.architecture": 0.8, "task.diff": 0.6, "_base": 0.5 },
  "structure.directories":        { "query.architecture": 0.9, "task.diff": 0.7, "file.config": 0.5 },
  "structure.modules":            { "query.architecture": 0.8, "task.diff": 0.6 },
  "patterns":                     { "query.architecture": 0.9, "_base": 0.6 },
  "patterns.architecture":        { "query.architecture": 1.0, "task.diff": 0.7, "_base": 0.6 },
  "patterns.naming":              { "query.architecture": 0.6, "file.component": 0.7, "file.test": 0.5 },
  "patterns.error_handling":      { "query.architecture": 0.7, "file.component": 0.6 },
  "conventions":                  { "_base": 0.5 },
  "conventions.testing":          { "query.testing": 0.9, "file.test": 0.9, "_base": 0.4 },
  "conventions.testing.framework":{ "query.testing": 1.0, "file.test": 0.9 },
  "conventions.testing.organization": { "query.testing": 0.8, "file.test": 0.7 },
  "conventions.testing.mocking":  { "query.testing": 0.8, "file.test": 0.8 },
  "conventions.build":            { "file.build": 0.9, "file.config": 0.7, "query.dependencies": 0.6 },
  "conventions.cicd":             { "file.ci": 1.0, "file.build": 0.5, "query.architecture": 0.4 },
  "dependencies":                 { "query.dependencies": 0.9, "file.config": 0.6, "_base": 0.4 },
  "dependencies.frameworks":      { "query.dependencies": 1.0, "query.architecture": 0.6, "file.config": 0.7 },
  "dependencies.libraries":       { "query.dependencies": 0.9, "file.config": 0.5 },
  "summary":                      { "_base": 0.7, "task.status": 0.8, "task.load": 0.6 }
}
```

### How Affinity is Applied

When populating tensor weights for a dream, the dream's `semantic_profile` scores (from `layer.json`) are combined with affinity multipliers:

```
weight[dream][category][context] =
    dream.semantic_profile[category] * KEY_CONTEXT_AFFINITY[category][context]
```

If a category-context pair has no affinity entry, the weight falls back to `dream.semantic_profile[category] * 0.1` (weak baseline).

---

## Core Functions

### `read_tensor()`

Read the tensor from disk. If missing, build from scratch. If an older format is detected (v1 layer.json priorities or v2 manifest.json), perform lazy migration.

```
function read_tensor():
  tensor_path = ".claude/dreams/tensor.json"

  if file_exists(tensor_path):
    tensor = json_parse(read_file(tensor_path))

    // Validate version
    if tensor.version != 1:
      error("Unknown tensor version: " + tensor.version)

    // Validate dimensions match current dreams
    current_dreams = list_active_dreams_from_dreams_md()
    if set(tensor.dimensions.dreams) != set(current_dreams):
      // Dreams added or removed since last write — reconcile
      tensor = reconcile_dreams(tensor, current_dreams)
      write_tensor(tensor)

    return tensor

  // No tensor.json — check for legacy formats
  if file_exists(".claude/dreams/manifest.json"):
    // v2 format (flat manifest from Round 1 design)
    return migrate_from_manifest()

  // Check for v1 format (layer.json with priority fields)
  dreams = list_dream_directories()
  if dreams.length > 0 and file_exists(dreams[0] + "/layer.json"):
    layer = json_parse(read_file(dreams[0] + "/layer.json"))
    if "priority" in layer:
      return migrate_to_tensor()

  // Completely fresh — build empty tensor
  return build_empty_tensor()


function reconcile_dreams(tensor, current_dreams):
  added = current_dreams - set(tensor.dimensions.dreams)
  removed = set(tensor.dimensions.dreams) - current_dreams

  // Remove rows for forgotten dreams
  for dream_name in removed:
    idx = tensor.dimensions.dreams.index(dream_name)
    tensor.dimensions.dreams.splice(idx, 1)
    tensor.weights.splice(idx, 1)
    tensor.base_order.remove(dream_name)

  // Add rows for new dreams
  for dream_name in added:
    tensor.dimensions.dreams.push(dream_name)
    num_categories = tensor.dimensions.categories.length
    num_contexts = tensor.dimensions.contexts.length
    // Initialize with zeros — caller must populate via populate_tensor_for_dream()
    new_row = array(num_categories, array(num_contexts, 0.0))
    tensor.weights.push(new_row)
    tensor.base_order.push(dream_name)

  tensor.last_modified = now_iso8601()
  return tensor
```

### `write_tensor(tensor)`

Serialize and persist the tensor to disk.

```
function write_tensor(tensor):
  tensor_path = ".claude/dreams/tensor.json"

  // Update timestamp
  tensor.last_modified = now_iso8601()

  // Validate structure before write
  assert tensor.dimensions.dreams.length == tensor.weights.length
  for row in tensor.weights:
    assert row.length == tensor.dimensions.categories.length
    for col in row:
      assert col.length == tensor.dimensions.contexts.length
      for val in col:
        assert 0.0 <= val <= 1.0

  // Write atomically (write to temp, rename)
  temp_path = tensor_path + ".tmp"
  write_file(temp_path, json_stringify(tensor, indent=2))
  rename(temp_path, tensor_path)
```

### `get_tensor_ordering(context)`

Main entry point. Given a context descriptor, return an ordered list of dream names sorted by relevance. This is called by the merge engine, diff engine, and conflict resolver.

```
function get_tensor_ordering(context):
  tensor = read_tensor()

  if tensor.dimensions.dreams.length == 0:
    return []

  if tensor.dimensions.dreams.length == 1:
    return [tensor.dimensions.dreams[0]]

  // Determine the context column index
  ctx_idx = resolve_context_index(tensor, context)

  // Score each dream: sum weights across all categories for this context
  scores = {}
  for d_idx in range(tensor.dimensions.dreams.length):
    dream_name = tensor.dimensions.dreams[d_idx]
    score = 0.0
    for k_idx in range(tensor.dimensions.categories.length):
      score += tensor.weights[d_idx][k_idx][ctx_idx]
    scores[dream_name] = score

  // Normalize scores to [0, 1]
  max_score = max(scores.values()) or 1.0
  for name in scores:
    scores[name] = scores[name] / max_score

  // Sort descending by score, tiebreak by base_order position
  ordered = sorted(
    tensor.dimensions.dreams,
    key = (name) => (
      -scores[name],
      tensor.base_order.index(name)
    )
  )

  return ordered


function resolve_context_index(tensor, context):
  // context can be:
  //   - a string like "_base", "file.test", "query.testing"
  //   - an object { active_file: "src/auth.test.ts", query: "...", task: "diff" }

  if type(context) == string:
    if context in tensor.dimensions.contexts:
      return tensor.dimensions.contexts.index(context)
    // Unknown context string — fall back to _base
    return tensor.dimensions.contexts.index("_base")

  // Object context — classify from signals
  if context.active_file:
    file_ctx = classify_file_context(context.active_file)
    if file_ctx in tensor.dimensions.contexts:
      return tensor.dimensions.contexts.index(file_ctx)

  if context.query:
    query_ctx = classify_query_context(context.query)
    if query_ctx in tensor.dimensions.contexts:
      return tensor.dimensions.contexts.index(query_ctx)

  if context.task:
    task_ctx = "task." + context.task
    if task_ctx in tensor.dimensions.contexts:
      return tensor.dimensions.contexts.index(task_ctx)

  // Default fallback
  return tensor.dimensions.contexts.index("_base")


function classify_file_context(filepath):
  // Map file patterns to context identifiers
  if matches(filepath, "*.test.*") or matches(filepath, "*.spec.*") or
     matches(filepath, "*/__tests__/*") or matches(filepath, "*/test/*"):
    return "file.test"

  if matches(filepath, "*.component.*") or matches(filepath, "*.tsx") or
     matches(filepath, "*.vue") or matches(filepath, "*.svelte"):
    return "file.component"

  if matches(filepath, "*.config.*") or matches(filepath, "*.json") or
     matches(filepath, "*.yaml") or matches(filepath, "*.yml") or
     matches(filepath, "*.toml") or matches(filepath, "*.env*"):
    return "file.config"

  if matches(filepath, "*.ci*") or matches(filepath, ".github/*") or
     matches(filepath, ".gitlab-ci*") or matches(filepath, "Jenkinsfile*"):
    return "file.ci"

  if matches(filepath, "Makefile*") or matches(filepath, "Dockerfile*") or
     matches(filepath, "*.gradle*") or matches(filepath, "webpack*") or
     matches(filepath, "vite.config*") or matches(filepath, "rollup*"):
    return "file.build"

  if matches(filepath, "*.md") or matches(filepath, "docs/*") or
     matches(filepath, "*.rst"):
    return "file.docs"

  return "_base"


function classify_query_context(query):
  query_lower = lowercase(query)

  testing_keywords = ["test", "testing", "spec", "jest", "vitest", "pytest",
                      "mock", "stub", "fixture", "coverage", "assertion"]
  arch_keywords = ["architecture", "structure", "design", "pattern", "module",
                   "organize", "layout", "monolith", "microservice"]
  dep_keywords = ["dependency", "dependencies", "package", "library", "framework",
                  "install", "version", "upgrade"]

  if any(kw in query_lower for kw in testing_keywords):
    return "query.testing"
  if any(kw in query_lower for kw in arch_keywords):
    return "query.architecture"
  if any(kw in query_lower for kw in dep_keywords):
    return "query.dependencies"

  return "_base"
```

### `populate_tensor_for_dream(dream_name, analysis_results)`

Fill a dream's weight row from analyzer output. Called after dream load or update. The `analysis_results` come from the analyzer sub-skill and include a `semantic_profile` mapping categories to strength scores.

```
function populate_tensor_for_dream(dream_name, analysis_results):
  tensor = read_tensor()

  // Ensure dream exists in tensor dimensions
  if dream_name not in tensor.dimensions.dreams:
    tensor.dimensions.dreams.push(dream_name)
    tensor.base_order.push(dream_name)
    num_categories = tensor.dimensions.categories.length
    num_contexts = tensor.dimensions.contexts.length
    tensor.weights.push(array(num_categories, array(num_contexts, 0.0)))

  d_idx = tensor.dimensions.dreams.index(dream_name)

  // Extract semantic_profile from analysis
  // semantic_profile: { "patterns.architecture": 0.95, "conventions.testing": 0.30, ... }
  profile = analysis_results.semantic_profile

  // Populate each cell using profile strength * affinity
  for k_idx in range(tensor.dimensions.categories.length):
    category = tensor.dimensions.categories[k_idx]

    // Get the dream's raw strength for this category
    // Walk up the category hierarchy if exact match not found
    raw_strength = lookup_profile_strength(profile, category)

    for c_idx in range(tensor.dimensions.contexts.length):
      context = tensor.dimensions.contexts[c_idx]

      // Look up affinity between this category and context
      affinity = KEY_CONTEXT_AFFINITY.get(category, {}).get(context, 0.1)

      // Compute weight: strength * affinity, clamped to [0.0, 1.0]
      weight = clamp(raw_strength * affinity, 0.0, 1.0)
      tensor.weights[d_idx][k_idx][c_idx] = weight

  // Record in history
  tensor.history.push({
    "action": "populate",
    "timestamp": now_iso8601(),
    "details": "Populated weights for dream: " + dream_name
  })

  // Cap history at 50 entries
  if tensor.history.length > 50:
    tensor.history = tensor.history.slice(-50)

  write_tensor(tensor)


function lookup_profile_strength(profile, category):
  // Exact match
  if category in profile:
    return profile[category]

  // Walk up hierarchy: "conventions.testing.framework" -> "conventions.testing" -> "conventions"
  parts = category.split(".")
  while parts.length > 1:
    parts.pop()
    parent = parts.join(".")
    if parent in profile:
      // Decay by 0.8 per level of indirection
      depth_diff = category.split(".").length - parts.length
      return profile[parent] * (0.8 ** depth_diff)

  // No match at all — return weak baseline
  return 0.1
```

### `remove_dream_from_tensor(dream_name)`

Remove a dream's dimension from the tensor. Called by the forget flow.

```
function remove_dream_from_tensor(dream_name):
  tensor = read_tensor()

  if dream_name not in tensor.dimensions.dreams:
    return  // Nothing to remove

  d_idx = tensor.dimensions.dreams.index(dream_name)

  // Remove from all structures
  tensor.dimensions.dreams.splice(d_idx, 1)
  tensor.weights.splice(d_idx, 1)
  tensor.base_order.remove(dream_name)

  // Record in history
  tensor.history.push({
    "action": "remove",
    "timestamp": now_iso8601(),
    "details": "Removed dream: " + dream_name
  })

  write_tensor(tensor)
```

### `recalculate_base_weights(tensor)`

Recalculate the `_base` context column for all dreams. Called after reorder operations or when base_order changes.

```
function recalculate_base_weights(tensor):
  base_ctx_idx = tensor.dimensions.contexts.index("_base")
  num_dreams = tensor.dimensions.dreams.length

  if num_dreams == 0:
    return tensor

  for d_idx in range(num_dreams):
    dream_name = tensor.dimensions.dreams[d_idx]

    // Base position weight: first in base_order gets highest base weight
    position = tensor.base_order.index(dream_name)
    position_weight = 1.0 - (position / num_dreams)  // Linear decay from 1.0 to near 0.0

    for k_idx in range(tensor.dimensions.categories.length):
      category = tensor.dimensions.categories[k_idx]

      // Get category-specific base affinity
      base_affinity = KEY_CONTEXT_AFFINITY.get(category, {}).get("_base", 0.3)

      // Combine position weight with base affinity
      // Position weight dominates in _base context (70/30 split)
      weight = clamp(0.7 * position_weight + 0.3 * base_affinity, 0.0, 1.0)

      tensor.weights[d_idx][k_idx][base_ctx_idx] = weight

  tensor.last_modified = now_iso8601()
  return tensor
```

### `migrate_to_tensor()`

Build the tensor from existing v1 (layer.json with priorities) or v2 (manifest.json) data. This is a one-time migration that runs lazily on first `read_tensor()`.

```
function migrate_to_tensor():
  dreams = list_dream_directories()
  dream_names = []
  dream_priorities = {}
  dream_profiles = {}

  // Phase 1: Read existing data
  for dream_dir in dreams:
    name = basename(dream_dir)
    dream_names.push(name)

    layer_path = dream_dir + "/layer.json"
    if file_exists(layer_path):
      layer = json_parse(read_file(layer_path))
      dream_priorities[name] = layer.get("priority", 999)
      dream_profiles[name] = layer.get("semantic_profile", {})

  // Phase 2: If manifest.json exists (v2), use its ordering
  manifest_path = ".claude/dreams/manifest.json"
  if file_exists(manifest_path):
    manifest = json_parse(read_file(manifest_path))
    if "order" in manifest:
      // manifest.order is the authoritative ordering
      ordered_names = manifest.order.filter(n => n in dream_names)
      // Append any dreams not in manifest
      for name in dream_names:
        if name not in ordered_names:
          ordered_names.push(name)
      dream_names = ordered_names
    // Clean up v2 file
    delete_file(manifest_path)
  else:
    // v1: sort by priority (ascending = highest priority first)
    dream_names.sort(key = (n) => dream_priorities.get(n, 999))

  // Phase 3: Build tensor
  num_categories = STATIC_CATEGORIES.length  // ~18
  num_contexts = STATIC_CONTEXTS.length      // ~13

  tensor = {
    "version": 1,
    "dimensions": {
      "dreams": dream_names,
      "categories": STATIC_CATEGORIES,
      "contexts": STATIC_CONTEXTS
    },
    "weights": [],
    "base_order": list(dream_names),
    "history": [{
      "action": "migrate",
      "timestamp": now_iso8601(),
      "details": "Migrated from " + (file_exists(manifest_path) ? "manifest.json" : "layer.json priorities")
    }],
    "last_modified": now_iso8601()
  }

  // Phase 4: Populate weights
  for d_idx, name in enumerate(dream_names):
    row = array(num_categories, array(num_contexts, 0.0))
    tensor.weights.push(row)

  // If dreams have semantic_profiles, use them
  for name in dream_names:
    if name in dream_profiles and dream_profiles[name]:
      populate_tensor_for_dream(name, { "semantic_profile": dream_profiles[name] })
    else:
      // No profile yet — use position-based defaults
      // Read dream .md files to infer a basic profile
      profile = infer_profile_from_dream_files(name)
      populate_tensor_for_dream(name, { "semantic_profile": profile })

  // Phase 5: Recalculate base weights from ordering
  tensor = recalculate_base_weights(tensor)

  // Phase 6: Update layer.json files (remove priority, add semantic_profile if missing)
  for dream_dir in dreams:
    layer_path = dream_dir + "/layer.json"
    if file_exists(layer_path):
      layer = json_parse(read_file(layer_path))
      if "priority" in layer:
        delete layer["priority"]
      if "semantic_profile" not in layer:
        name = basename(dream_dir)
        layer["semantic_profile"] = dream_profiles.get(name, {})
      write_file(layer_path, json_stringify(layer, indent=2))

  write_tensor(tensor)
  return tensor


function infer_profile_from_dream_files(dream_name):
  // Read dream memory files and estimate category strengths
  dream_dir = ".claude/dreams/" + dream_name
  profile = {}

  // Check structure.md
  if file_exists(dream_dir + "/structure.md"):
    content = read_file(dream_dir + "/structure.md")
    profile["structure"] = 0.8 if len(content) > 500 else 0.4

  // Check patterns.md
  if file_exists(dream_dir + "/patterns.md"):
    content = read_file(dream_dir + "/patterns.md")
    profile["patterns"] = 0.8 if len(content) > 500 else 0.4
    if "architecture" in lowercase(content):
      profile["patterns.architecture"] = 0.7
    if "naming" in lowercase(content):
      profile["patterns.naming"] = 0.6

  // Check conventions.md
  if file_exists(dream_dir + "/conventions.md"):
    content = read_file(dream_dir + "/conventions.md")
    profile["conventions"] = 0.7 if len(content) > 500 else 0.3
    if any(kw in lowercase(content) for kw in ["test", "jest", "vitest", "pytest"]):
      profile["conventions.testing"] = 0.7
    if any(kw in lowercase(content) for kw in ["build", "webpack", "vite", "gradle"]):
      profile["conventions.build"] = 0.6
    if any(kw in lowercase(content) for kw in ["ci", "github actions", "jenkins", "pipeline"]):
      profile["conventions.cicd"] = 0.6

  // Check dependencies.md
  if file_exists(dream_dir + "/dependencies.md"):
    content = read_file(dream_dir + "/dependencies.md")
    profile["dependencies"] = 0.7 if len(content) > 300 else 0.3
    if any(kw in lowercase(content) for kw in ["react", "vue", "angular", "express", "django"]):
      profile["dependencies.frameworks"] = 0.7

  // Summary always gets a baseline
  if file_exists(dream_dir + "/summary.md"):
    profile["summary"] = 0.5

  return profile
```

---

## Storage

### Location

```
.claude/dreams/tensor.json
```

The tensor file lives alongside `DREAMS.md` in the dreams root directory — not inside any individual dream folder.

### Caching Strategy

- **Read caching**: `read_tensor()` may cache the parsed tensor in memory within a single command execution. The cache is invalidated on any `write_tensor()` call.
- **No cross-command caching**: Each `/mentor` command invocation reads fresh from disk. The file is small enough (<100KB even at 20 dreams) that this adds negligible latency.
- **Write-through**: All mutations call `write_tensor()` immediately. No deferred writes.

### Backup and Recovery

- The `history` array provides an audit trail of mutations (capped at 50 entries).
- If `tensor.json` is corrupted or deleted, `read_tensor()` rebuilds from dream content files. This is a safe cold start — no data is lost because dream `.md` files remain authoritative.
- Atomic writes via temp file + rename prevent partial writes on crash.

---

## Reorder Operations

The following operations modify `base_order` and trigger `recalculate_base_weights()`:

| Operation | Effect on `base_order` |
|-----------|----------------------|
| `move_to_front(dream)` | Move dream to position 0 |
| `move_to_back(dream)` | Move dream to last position |
| `move_before(dream, target)` | Insert dream immediately before target |
| `move_after(dream, target)` | Insert dream immediately after target |
| `swap(dream_a, dream_b)` | Exchange positions of two dreams |
| `set_order(ordered_names)` | Replace entire base_order |
| `reverse()` | Reverse the entire base_order |

All operations validate that named dreams exist in `dimensions.dreams` before mutating. After any mutation, `recalculate_base_weights(tensor)` is called to update the `_base` context column, and `write_tensor(tensor)` persists the change.

---

## Integration Points

| Consumer | How It Uses Tensor |
|----------|-------------------|
| Merge engine (SKILL.md) | Calls `get_tensor_ordering(context)` to determine dream iteration order for first-write-wins merge |
| Conflict resolver (resolver.md) | Uses tensor ordering instead of numeric priority to determine winners |
| Trie (trie.md) | Reads `base_order` for tiebreaking after trie-based scoring |
| Diff engine (dream-manager) | Calls `get_tensor_ordering({ task: "diff" })` for diff context |
| Display/list commands | Reads `base_order` for default display ordering |
| Load flow | Calls `populate_tensor_for_dream()` after analysis |
| Forget flow | Calls `remove_dream_from_tensor()` during cleanup |
