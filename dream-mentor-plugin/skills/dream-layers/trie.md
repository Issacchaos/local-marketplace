# Trie Sub-Skill

**Parent**: `skills/dream-layers/SKILL.md`
**Purpose**: Maintain a semantic prefix trie over the category taxonomy for O(k) dream relevance lookup, avoiding full tensor scans on every query.

---

## Overview

The trie is a ~35-node tree stored at `.claude/dreams/trie.json` that mirrors the category taxonomy. Each node holds per-dream relevance scores. When a query or file context arrives, the system extracts semantic paths (e.g., `["conventions", "testing", "framework"]`), walks the trie to the deepest matching node, and returns scored dream candidates with weighted inheritance from ancestor nodes.

The trie answers: "Which dreams are relevant for this semantic topic, and how relevant is each?" The tensor (tensor.md) then refines these candidates with context-specific weights.

---

## Trie Schema

File: `.claude/dreams/trie.json`

### TrieNode Structure

```
TrieNode {
  segment: string           // This node's path segment (e.g., "testing")
  children: Map<string, TrieNode>  // Child nodes keyed by segment name
  dreams: string[]          // Dream names present at this node, sorted by tensor base_order weight
  scores: Map<string, number>      // Per-dream relevance scores at this node [0.0, 1.0]
  depth: number             // Distance from root (root = 0)
}
```

### Serialized Format

```json
{
  "version": 1,
  "root": {
    "segment": "",
    "depth": 0,
    "dreams": ["architecture-ref", "testing-patterns"],
    "scores": { "architecture-ref": 0.5, "testing-patterns": 0.5 },
    "children": {
      "structure": {
        "segment": "structure",
        "depth": 1,
        "dreams": ["architecture-ref"],
        "scores": { "architecture-ref": 0.9 },
        "children": {
          "directories": {
            "segment": "directories",
            "depth": 2,
            "dreams": ["architecture-ref"],
            "scores": { "architecture-ref": 0.85 },
            "children": {}
          },
          "modules": {
            "segment": "modules",
            "depth": 2,
            "dreams": ["architecture-ref"],
            "scores": { "architecture-ref": 0.80 },
            "children": {}
          }
        }
      }
    }
  },
  "last_modified": "2026-04-12T10:00:00.000Z"
}
```

### Size Estimates

| Dreams | Nodes | Memory | Disk |
|--------|-------|--------|------|
| 2 | 35 | ~8KB | ~15KB |
| 5 | 35 | ~12KB | ~22KB |
| 10 | 35 | ~20KB | ~30KB |
| 20 | 35 | ~35KB | ~50KB |

---

## Static Taxonomy

The trie structure is fixed at ~35 nodes with max depth 3. New dreams populate scores within these nodes but do not add new nodes.

```
Root (depth 0)
  |
  +-- structure (depth 1)
  |     +-- directories (depth 2)
  |     +-- modules (depth 2)
  |     +-- entry_points (depth 2)
  |     +-- config_files (depth 2)
  |
  +-- patterns (depth 1)
  |     +-- architecture (depth 2)
  |     |     +-- style (depth 3)          // monolith, microservices, modular
  |     |     +-- data_flow (depth 3)      // MVC, CQRS, event-driven
  |     +-- naming (depth 2)
  |     |     +-- files (depth 3)
  |     |     +-- functions (depth 3)
  |     |     +-- classes (depth 3)
  |     +-- error_handling (depth 2)
  |     +-- state_management (depth 2)
  |     +-- code_organization (depth 2)    // by feature, by layer
  |
  +-- conventions (depth 1)
  |     +-- testing (depth 2)
  |     |     +-- framework (depth 3)      // jest, vitest, pytest, junit
  |     |     +-- organization (depth 3)   // colocated, separate dir
  |     |     +-- mocking (depth 3)        // mock library, patterns
  |     +-- build (depth 2)
  |     |     +-- tool (depth 3)           // webpack, vite, gradle
  |     |     +-- scripts (depth 3)
  |     +-- cicd (depth 2)
  |     |     +-- provider (depth 3)       // github actions, jenkins
  |     |     +-- pipeline (depth 3)
  |     +-- linting (depth 2)
  |     +-- documentation (depth 2)
  |     +-- git_workflow (depth 2)
  |
  +-- dependencies (depth 1)
  |     +-- frameworks (depth 2)
  |     +-- libraries (depth 2)
  |     +-- runtime (depth 2)              // node version, python version
  |     +-- package_manager (depth 2)
  |
  +-- summary (depth 1)
```

**Total nodes**: 35 (1 root + 5 depth-1 + 17 depth-2 + 12 depth-3)

---

## Keyword-to-Path Mapping

The `SEMANTIC_MAP` maps query keywords and file patterns to trie paths. This is the primary mechanism for converting natural language into trie lookups.

```
SEMANTIC_MAP = {
  // Testing
  "test":             ["conventions", "testing"],
  "testing":          ["conventions", "testing"],
  "spec":             ["conventions", "testing"],
  "jest":             ["conventions", "testing", "framework"],
  "vitest":           ["conventions", "testing", "framework"],
  "pytest":           ["conventions", "testing", "framework"],
  "junit":            ["conventions", "testing", "framework"],
  "mocha":            ["conventions", "testing", "framework"],
  "test framework":   ["conventions", "testing", "framework"],
  "mock":             ["conventions", "testing", "mocking"],
  "stub":             ["conventions", "testing", "mocking"],
  "fixture":          ["conventions", "testing", "mocking"],
  "colocated test":   ["conventions", "testing", "organization"],
  "test directory":   ["conventions", "testing", "organization"],
  "__tests__":        ["conventions", "testing", "organization"],
  "coverage":         ["conventions", "testing"],

  // Architecture & patterns
  "architecture":     ["patterns", "architecture"],
  "microservice":     ["patterns", "architecture", "style"],
  "monolith":         ["patterns", "architecture", "style"],
  "modular":          ["patterns", "architecture", "style"],
  "mvc":              ["patterns", "architecture", "data_flow"],
  "cqrs":             ["patterns", "architecture", "data_flow"],
  "event-driven":     ["patterns", "architecture", "data_flow"],
  "design pattern":   ["patterns", "architecture"],
  "naming":           ["patterns", "naming"],
  "kebab-case":       ["patterns", "naming", "files"],
  "camelCase":        ["patterns", "naming", "functions"],
  "PascalCase":       ["patterns", "naming", "classes"],
  "error handling":   ["patterns", "error_handling"],
  "exception":        ["patterns", "error_handling"],
  "result type":      ["patterns", "error_handling"],
  "state management": ["patterns", "state_management"],
  "redux":            ["patterns", "state_management"],
  "organize":         ["patterns", "code_organization"],

  // Structure
  "structure":        ["structure"],
  "directory":        ["structure", "directories"],
  "folder":           ["structure", "directories"],
  "module":           ["structure", "modules"],
  "entry point":      ["structure", "entry_points"],
  "main file":        ["structure", "entry_points"],
  "config file":      ["structure", "config_files"],

  // Build & CI
  "build":            ["conventions", "build"],
  "webpack":          ["conventions", "build", "tool"],
  "vite":             ["conventions", "build", "tool"],
  "gradle":           ["conventions", "build", "tool"],
  "esbuild":          ["conventions", "build", "tool"],
  "rollup":           ["conventions", "build", "tool"],
  "script":           ["conventions", "build", "scripts"],
  "ci":               ["conventions", "cicd"],
  "cd":               ["conventions", "cicd"],
  "pipeline":         ["conventions", "cicd", "pipeline"],
  "github actions":   ["conventions", "cicd", "provider"],
  "jenkins":          ["conventions", "cicd", "provider"],
  "lint":             ["conventions", "linting"],
  "eslint":           ["conventions", "linting"],
  "prettier":         ["conventions", "linting"],
  "format":           ["conventions", "linting"],
  "documentation":    ["conventions", "documentation"],
  "branching":        ["conventions", "git_workflow"],
  "commit convention":["conventions", "git_workflow"],

  // Dependencies
  "dependency":       ["dependencies"],
  "dependencies":     ["dependencies"],
  "package":          ["dependencies", "package_manager"],
  "npm":              ["dependencies", "package_manager"],
  "yarn":             ["dependencies", "package_manager"],
  "pnpm":             ["dependencies", "package_manager"],
  "pip":              ["dependencies", "package_manager"],
  "framework":        ["dependencies", "frameworks"],
  "react":            ["dependencies", "frameworks"],
  "vue":              ["dependencies", "frameworks"],
  "angular":          ["dependencies", "frameworks"],
  "express":          ["dependencies", "frameworks"],
  "django":           ["dependencies", "frameworks"],
  "library":          ["dependencies", "libraries"],
  "runtime":          ["dependencies", "runtime"],
  "node version":     ["dependencies", "runtime"],
  "python version":   ["dependencies", "runtime"],

  // Summary
  "summary":          ["summary"],
  "overview":         ["summary"],
  "what does it do":  ["summary"]
}
```

**Total entries**: 68 keyword mappings across all taxonomy branches.

---

## Core Functions

### `read_trie()`

Read the trie from disk. If missing or corrupted, rebuild from dream content.

```
function read_trie():
  trie_path = ".claude/dreams/trie.json"

  if file_exists(trie_path):
    trie = json_parse(read_file(trie_path))

    if trie.version != 1:
      error("Unknown trie version: " + trie.version)

    // Validate that trie has scores for all current dreams
    current_dreams = list_active_dreams_from_dreams_md()
    trie_dreams = collect_all_dream_names(trie.root)

    if set(trie_dreams) != set(current_dreams):
      // Rebuild — dream set has changed
      return build_trie(current_dreams)

    return trie

  // No trie.json — build from scratch
  dreams = list_active_dreams_from_dreams_md()
  if dreams.length > 0:
    return build_trie(dreams)

  // No dreams loaded — return empty skeleton
  return build_empty_trie()


function collect_all_dream_names(node):
  // Recursively collect all dream names mentioned in any node
  names = set(node.dreams)
  for child in node.children.values():
    names = names.union(collect_all_dream_names(child))
  return names
```

### `build_trie(dreams)`

Construct the trie from scratch using the static taxonomy and dream content analysis.

```
function build_trie(dreams):
  // Phase 1: Build the static taxonomy skeleton
  root = build_taxonomy_skeleton()

  // Phase 2: Score each dream against every node
  for dream_name in dreams:
    score_dream(root, dream_name)

  // Phase 3: Sort dream lists at each node by tensor base_order
  tensor = read_tensor()
  sort_trie_dreams_by_base_order(root, tensor.base_order)

  // Phase 4: Persist
  trie = {
    "version": 1,
    "root": root,
    "last_modified": now_iso8601()
  }

  write_file(".claude/dreams/trie.json", json_stringify(trie, indent=2))
  return trie


function build_taxonomy_skeleton():
  // Construct the fixed ~35-node tree with empty dream lists
  root = make_node("", 0)

  // Depth 1
  structure    = add_child(root, "structure")
  patterns     = add_child(root, "patterns")
  conventions  = add_child(root, "conventions")
  dependencies = add_child(root, "dependencies")
  summary      = add_child(root, "summary")

  // Depth 2 — structure
  add_child(structure, "directories")
  add_child(structure, "modules")
  add_child(structure, "entry_points")
  add_child(structure, "config_files")

  // Depth 2 — patterns
  architecture = add_child(patterns, "architecture")
  naming       = add_child(patterns, "naming")
  add_child(patterns, "error_handling")
  add_child(patterns, "state_management")
  add_child(patterns, "code_organization")

  // Depth 3 — patterns.architecture
  add_child(architecture, "style")
  add_child(architecture, "data_flow")

  // Depth 3 — patterns.naming
  add_child(naming, "files")
  add_child(naming, "functions")
  add_child(naming, "classes")

  // Depth 2 — conventions
  testing = add_child(conventions, "testing")
  build   = add_child(conventions, "build")
  cicd    = add_child(conventions, "cicd")
  add_child(conventions, "linting")
  add_child(conventions, "documentation")
  add_child(conventions, "git_workflow")

  // Depth 3 — conventions.testing
  add_child(testing, "framework")
  add_child(testing, "organization")
  add_child(testing, "mocking")

  // Depth 3 — conventions.build
  add_child(build, "tool")
  add_child(build, "scripts")

  // Depth 3 — conventions.cicd
  add_child(cicd, "provider")
  add_child(cicd, "pipeline")

  // Depth 2 — dependencies
  add_child(dependencies, "frameworks")
  add_child(dependencies, "libraries")
  add_child(dependencies, "runtime")
  add_child(dependencies, "package_manager")

  return root


function make_node(segment, depth):
  return {
    "segment": segment,
    "children": {},
    "dreams": [],
    "scores": {},
    "depth": depth
  }


function add_child(parent, segment):
  child = make_node(segment, parent.depth + 1)
  parent.children[segment] = child
  return child
```

### `score_dream(trie_root, dream_name)`

Analyze a dream's `.md` files and assign relevance scores at each trie node.

```
function score_dream(trie_root, dream_name):
  dream_dir = ".claude/dreams/" + dream_name

  // Read all dream memory files
  content_map = {}
  for filename in ["structure.md", "patterns.md", "dependencies.md", "conventions.md", "summary.md"]:
    filepath = dream_dir + "/" + filename
    if file_exists(filepath):
      content_map[filename] = lowercase(read_file(filepath))
    else:
      content_map[filename] = ""

  // Also check layer.json for semantic_profile
  profile = {}
  layer_path = dream_dir + "/layer.json"
  if file_exists(layer_path):
    layer = json_parse(read_file(layer_path))
    profile = layer.get("semantic_profile", {})

  // Score each node in the trie
  score_node_recursive(trie_root, dream_name, content_map, profile)


function score_node_recursive(node, dream_name, content_map, profile):
  // Compute this node's score for the dream
  path = get_node_path(node)  // e.g., "conventions.testing.framework"
  score = compute_node_score(node, dream_name, content_map, profile, path)

  if score > 0.05:  // Threshold: ignore negligible relevance
    if dream_name not in node.dreams:
      node.dreams.push(dream_name)
    node.scores[dream_name] = score

  // Recurse into children
  for child in node.children.values():
    score_node_recursive(child, dream_name, content_map, profile)


function compute_node_score(node, dream_name, content_map, profile, path):
  // Priority 1: Use semantic_profile if it has an exact or parent match
  if path in profile:
    return profile[path]

  // Check parent paths in profile
  parts = path.split(".")
  while parts.length > 1:
    parts.pop()
    parent_path = parts.join(".")
    if parent_path in profile:
      depth_diff = path.split(".").length - parts.length
      return profile[parent_path] * (0.8 ** depth_diff)

  // Priority 2: Content-based heuristic scoring
  return score_from_content(node, content_map)


function score_from_content(node, content_map):
  // Map trie segments to the memory file most likely to contain relevant content
  // and keywords that indicate strong relevance
  SEGMENT_SIGNALS = {
    "structure":        { "file": "structure.md",    "keywords": ["directory", "folder", "layout", "module", "src/"] },
    "directories":      { "file": "structure.md",    "keywords": ["directory", "folder", "src/", "lib/", "app/"] },
    "modules":          { "file": "structure.md",    "keywords": ["module", "package", "workspace", "monorepo"] },
    "entry_points":     { "file": "structure.md",    "keywords": ["entry", "main", "index", "app.", "server."] },
    "config_files":     { "file": "structure.md",    "keywords": ["config", ".json", ".yaml", ".toml", ".env"] },
    "patterns":         { "file": "patterns.md",     "keywords": ["pattern", "design", "approach", "style"] },
    "architecture":     { "file": "patterns.md",     "keywords": ["architecture", "design", "structure", "layer"] },
    "style":            { "file": "patterns.md",     "keywords": ["monolith", "microservice", "modular", "serverless"] },
    "data_flow":        { "file": "patterns.md",     "keywords": ["mvc", "cqrs", "event", "pipeline", "flow"] },
    "naming":           { "file": "patterns.md",     "keywords": ["naming", "convention", "case", "prefix", "suffix"] },
    "files":            { "file": "patterns.md",     "keywords": ["file name", "kebab", "snake", "dot notation"] },
    "functions":        { "file": "patterns.md",     "keywords": ["function", "method", "camel", "verb"] },
    "classes":          { "file": "patterns.md",     "keywords": ["class", "pascal", "interface", "type"] },
    "error_handling":   { "file": "patterns.md",     "keywords": ["error", "exception", "result", "try", "catch", "throw"] },
    "state_management": { "file": "patterns.md",     "keywords": ["state", "redux", "context", "store", "signal"] },
    "code_organization":{ "file": "patterns.md",     "keywords": ["organize", "feature", "layer", "domain", "group"] },
    "conventions":      { "file": "conventions.md",  "keywords": ["convention", "standard", "rule", "practice"] },
    "testing":          { "file": "conventions.md",  "keywords": ["test", "spec", "assert", "expect", "describe"] },
    "framework":        { "file": "conventions.md",  "keywords": ["jest", "vitest", "pytest", "junit", "mocha", "cypress"] },
    "organization":     { "file": "conventions.md",  "keywords": ["colocated", "__tests__", "test/", "spec/"] },
    "mocking":          { "file": "conventions.md",  "keywords": ["mock", "stub", "fake", "spy", "fixture"] },
    "build":            { "file": "conventions.md",  "keywords": ["build", "compile", "bundle", "transpile"] },
    "tool":             { "file": "conventions.md",  "keywords": ["webpack", "vite", "esbuild", "rollup", "gradle", "make"] },
    "scripts":          { "file": "conventions.md",  "keywords": ["script", "npm run", "make", "task"] },
    "cicd":             { "file": "conventions.md",  "keywords": ["ci", "cd", "pipeline", "deploy", "workflow"] },
    "provider":         { "file": "conventions.md",  "keywords": ["github actions", "jenkins", "gitlab", "circleci"] },
    "pipeline":         { "file": "conventions.md",  "keywords": ["pipeline", "stage", "job", "step", "workflow"] },
    "linting":          { "file": "conventions.md",  "keywords": ["lint", "eslint", "prettier", "format", "style"] },
    "documentation":    { "file": "conventions.md",  "keywords": ["doc", "readme", "jsdoc", "comment", "api doc"] },
    "git_workflow":     { "file": "conventions.md",  "keywords": ["branch", "commit", "merge", "pr", "trunk"] },
    "dependencies":     { "file": "dependencies.md", "keywords": ["dependency", "package", "install", "version"] },
    "frameworks":       { "file": "dependencies.md", "keywords": ["react", "vue", "angular", "express", "django", "spring"] },
    "libraries":        { "file": "dependencies.md", "keywords": ["library", "axios", "lodash", "moment", "zod"] },
    "runtime":          { "file": "dependencies.md", "keywords": ["node", "python", "java", "go", "runtime", "version"] },
    "package_manager":  { "file": "dependencies.md", "keywords": ["npm", "yarn", "pnpm", "pip", "maven", "cargo"] },
    "summary":          { "file": "summary.md",      "keywords": ["project", "purpose", "stack", "overview"] }
  }

  segment = node.segment
  if segment == "":
    return 0.5  // Root node — all dreams have baseline relevance

  signals = SEGMENT_SIGNALS.get(segment, null)
  if signals == null:
    return 0.1  // Unknown segment — weak baseline

  content = content_map.get(signals.file, "")
  if content == "":
    return 0.0  // No content file — dream has nothing for this topic

  // Count keyword hits
  hits = 0
  for keyword in signals.keywords:
    if keyword in content:
      hits += 1

  // Score: ratio of keyword hits, with diminishing returns
  ratio = hits / signals.keywords.length
  // Apply sqrt for diminishing returns (1 hit out of 5 = 0.45, not 0.2)
  score = min(sqrt(ratio), 1.0)

  return round(score, 2)
```

### `resolve_ordering(trie, query, base_order)`

The main query resolution function. Takes a natural language query (or file context), extracts semantic paths, walks the trie with weighted inheritance, and returns a scored ordering of dreams.

```
function resolve_ordering(trie, query, base_order):
  // Step 1: Extract semantic paths from the query
  paths = extract_semantic_paths(query)

  if paths.length == 0:
    // No semantic signal — return base_order unchanged
    return base_order

  // Step 2: Accumulate scores across all matched paths
  dream_scores = {}  // dream_name -> cumulative score

  for path in paths:
    // Walk the trie with inheritance
    node_scores = traverse_with_inheritance(trie.root, path)

    // Merge into cumulative scores (take max per dream across paths)
    for dream_name, score in node_scores:
      if dream_name not in dream_scores:
        dream_scores[dream_name] = score
      else:
        dream_scores[dream_name] = max(dream_scores[dream_name], score)

  // Step 3: Include dreams that had no trie hits with a baseline score
  for dream_name in base_order:
    if dream_name not in dream_scores:
      dream_scores[dream_name] = 0.0

  // Step 4: Sort by score descending, tiebreak by base_order position
  ordered = sorted(
    dream_scores.keys(),
    key = (name) => (
      -dream_scores[name],
      base_order.index(name) if name in base_order else 999
    )
  )

  return ordered
```

### `extract_semantic_paths(query)`

Map a natural language query to one or more trie paths using keyword matching against the `SEMANTIC_MAP`.

```
function extract_semantic_paths(query):
  query_lower = lowercase(query)
  matched_paths = []
  matched_keys = set()  // Track which keywords matched to avoid sub-keyword duplication

  // Sort SEMANTIC_MAP keys by length descending so longer (more specific) phrases match first
  sorted_keys = sorted(SEMANTIC_MAP.keys(), key = (k) => -len(k))

  for keyword in sorted_keys:
    if keyword in query_lower:
      path = SEMANTIC_MAP[keyword]

      // Skip if a more specific keyword already matched to the same or deeper path
      path_str = ".".join(path)
      already_covered = false
      for matched_key in matched_keys:
        matched_path_str = ".".join(SEMANTIC_MAP[matched_key])
        if path_str.startswith(matched_path_str) or matched_path_str.startswith(path_str):
          // Keep the deeper (more specific) path
          if len(SEMANTIC_MAP[matched_key]) >= len(path):
            already_covered = true
            break

      if not already_covered:
        // Remove any less-specific path this one supersedes
        matched_paths = [p for p in matched_paths if not ".".join(p).startswith(path_str) or len(p) >= len(path)]
        matched_paths.push(path)
        matched_keys.add(keyword)

  // Deduplicate identical paths
  unique_paths = []
  seen = set()
  for path in matched_paths:
    path_str = ".".join(path)
    if path_str not in seen:
      unique_paths.push(path)
      seen.add(path_str)

  return unique_paths
```

### `traverse_with_inheritance(trie_root, path)`

Walk the trie along a semantic path and collect dream scores with 0.5 decay per level of ancestry.

```
function traverse_with_inheritance(trie_root, path):
  // Walk down the trie following the path segments
  visited_nodes = []
  current = trie_root

  // Always include root
  visited_nodes.push(current)

  for segment in path:
    if segment in current.children:
      current = current.children[segment]
      visited_nodes.push(current)
    else:
      break  // Path diverges from trie — stop here

  // The deepest reached node is the primary match
  // Score with exponential decay: deepest=1.0, parent=0.5, grandparent=0.25, etc.
  dream_scores = {}
  num_visited = visited_nodes.length

  for i in range(num_visited):
    node = visited_nodes[i]
    // Distance from deepest node: 0 for deepest, 1 for parent, etc.
    distance = (num_visited - 1) - i
    decay_factor = 0.5 ** distance  // 1.0, 0.5, 0.25, 0.125, ...

    for dream_name, node_score in node.scores.items():
      inherited_score = node_score * decay_factor

      if dream_name not in dream_scores:
        dream_scores[dream_name] = inherited_score
      else:
        // Take the max (a dream may appear at multiple levels)
        dream_scores[dream_name] = max(dream_scores[dream_name], inherited_score)

  return dream_scores
```

### `trie_insert_dream(trie, dream_name)`

Add a dream's scores to the trie. Called after dream load.

```
function trie_insert_dream(trie, dream_name):
  // Score the dream against all nodes
  score_dream(trie.root, dream_name)

  // Re-sort dream lists at all nodes by tensor base_order
  tensor = read_tensor()
  sort_trie_dreams_by_base_order(trie.root, tensor.base_order)

  trie.last_modified = now_iso8601()
  write_file(".claude/dreams/trie.json", json_stringify(trie, indent=2))


function sort_trie_dreams_by_base_order(node, base_order):
  // Sort this node's dreams list by base_order position
  node.dreams.sort(
    key = (name) => base_order.index(name) if name in base_order else 999
  )

  // Recurse
  for child in node.children.values():
    sort_trie_dreams_by_base_order(child, base_order)
```

### `trie_remove_dream(trie, dream_name)`

Remove a dream's scores from the trie and prune empty leaves.

```
function trie_remove_dream(trie, dream_name):
  remove_dream_recursive(trie.root, dream_name)
  trie.last_modified = now_iso8601()
  write_file(".claude/dreams/trie.json", json_stringify(trie, indent=2))


function remove_dream_recursive(node, dream_name):
  // Remove from this node
  if dream_name in node.dreams:
    node.dreams.remove(dream_name)
  if dream_name in node.scores:
    delete node.scores[dream_name]

  // Recurse into children
  empty_children = []
  for segment, child in node.children.items():
    remove_dream_recursive(child, dream_name)

    // Mark childless, dreamless nodes for pruning (but only depth 3+ leaves)
    if child.children.length == 0 and child.dreams.length == 0 and child.depth >= 3:
      empty_children.push(segment)

  // Prune empty leaves (only dynamic nodes at depth 3+; keep static taxonomy at depth 1-2)
  for segment in empty_children:
    // Do NOT prune — the taxonomy is static. Only clear scores.
    // Nodes remain in the trie even with no dreams so the structure is stable.
    pass
```

Note: The taxonomy is static, so nodes are never actually removed. `trie_remove_dream` clears a dream's scores and membership from nodes but leaves the tree structure intact.

---

## Example Walkthrough

**Query**: "what test framework should I use?"

**Loaded dreams**:
- `architecture-ref` — strong in structure (0.9), patterns (0.85), weak in testing (0.3)
- `testing-patterns` — strong in testing (0.95), moderate in patterns (0.5)

### Step 1: Extract Semantic Paths

```
extract_semantic_paths("what test framework should I use?")

Keyword scan (longest first):
  "test framework" matches → ["conventions", "testing", "framework"]
  "test" matches → ["conventions", "testing"]
    BUT "conventions.testing" is a prefix of already-matched "conventions.testing.framework"
    Already covered by more specific match — skip
  "framework" matches → ["dependencies", "frameworks"]
    Not covered by existing matches — add

Result: [
  ["conventions", "testing", "framework"],
  ["dependencies", "frameworks"]
]
```

### Step 2: Traverse Path 1 — `["conventions", "testing", "framework"]`

```
Walk: root → conventions → testing → framework

Visited nodes (deepest first for scoring):
  framework (depth 3): testing-patterns=0.90, architecture-ref=0.15
  testing   (depth 2): testing-patterns=0.85, architecture-ref=0.25
  conventions (depth 1): testing-patterns=0.70, architecture-ref=0.40
  root      (depth 0): testing-patterns=0.50, architecture-ref=0.50

Apply decay (0.5^distance from deepest):
  framework (distance 0, factor 1.0):
    testing-patterns: 0.90 * 1.0 = 0.90
    architecture-ref: 0.15 * 1.0 = 0.15
  testing (distance 1, factor 0.5):
    testing-patterns: 0.85 * 0.5 = 0.425
    architecture-ref: 0.25 * 0.5 = 0.125
  conventions (distance 2, factor 0.25):
    testing-patterns: 0.70 * 0.25 = 0.175
    architecture-ref: 0.40 * 0.25 = 0.10
  root (distance 3, factor 0.125):
    testing-patterns: 0.50 * 0.125 = 0.0625
    architecture-ref: 0.50 * 0.125 = 0.0625

Max per dream:
  testing-patterns: max(0.90, 0.425, 0.175, 0.0625) = 0.90
  architecture-ref: max(0.15, 0.125, 0.10, 0.0625)  = 0.15
```

### Step 3: Traverse Path 2 — `["dependencies", "frameworks"]`

```
Walk: root → dependencies → frameworks

Visited nodes:
  frameworks (depth 2): testing-patterns=0.30, architecture-ref=0.70
  dependencies (depth 1): testing-patterns=0.35, architecture-ref=0.65
  root (depth 0): testing-patterns=0.50, architecture-ref=0.50

Apply decay:
  frameworks (distance 0, factor 1.0):
    testing-patterns: 0.30
    architecture-ref: 0.70
  dependencies (distance 1, factor 0.5):
    testing-patterns: 0.175
    architecture-ref: 0.325
  root (distance 2, factor 0.25):
    testing-patterns: 0.125
    architecture-ref: 0.125

Max per dream:
  testing-patterns: max(0.30, 0.175, 0.125) = 0.30
  architecture-ref: max(0.70, 0.325, 0.125) = 0.70
```

### Step 4: Merge Across Paths (max per dream)

```
testing-patterns: max(0.90, 0.30) = 0.90
architecture-ref: max(0.15, 0.70) = 0.70
```

### Step 5: Sort

```
Descending by score, tiebreak by base_order:
  1. testing-patterns (0.90)
  2. architecture-ref (0.70)
```

**Result**: For "what test framework should I use?", `testing-patterns` is ordered first despite `architecture-ref` being first in `base_order`. The testing-specific dream dominates because the query's primary semantic signal (`conventions.testing.framework`) strongly favors it.

---

## Integration Points

| Consumer | How It Uses Trie |
|----------|-----------------|
| `get_tensor_ordering()` (tensor.md) | Can delegate to `resolve_ordering()` when a query string is available for semantic routing |
| Merge engine (SKILL.md) | Receives ordered dream list that incorporates trie-based semantic scoring |
| Load flow (dream-manager) | Calls `trie_insert_dream()` after dream analysis completes |
| Forget flow (dream-manager) | Calls `trie_remove_dream()` during cleanup |
| Tensor reorder operations (tensor.md) | After `base_order` changes, trie dream lists are re-sorted |
