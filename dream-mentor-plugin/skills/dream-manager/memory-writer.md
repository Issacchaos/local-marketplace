# Memory Writer Sub-Skill

**Parent**: `skills/dream-manager/SKILL.md`
**Purpose**: Write and update dream memory files and the DREAMS.md index.

---

## Memory Directory Structure

```
.claude/dreams/
  DREAMS.md                        # Index of all loaded dreams
  tensor.json                      # N*N*N relevance tensor (ordering)
  trie.json                        # Semantic prefix trie (routing)
  <dream-name>/
    source.json                    # Source metadata and commit tracking
    layer.json                     # Layer config and semantic profile
    structure.md                   # Directory layout and module boundaries
    patterns.md                    # Code patterns and architecture
    dependencies.md                # Dependencies, frameworks, versions
    conventions.md                 # Testing, build, CI, documentation patterns
    summary.md                     # High-level project overview
```

---

## Writing Memory Files

### Frontmatter Format

Every `.md` memory file uses this frontmatter:

```markdown
---
dream: <dream-name>
type: <structure|patterns|dependencies|conventions|summary>
source: <url-or-path>
analyzed_at: <ISO-8601-timestamp>
commit: <7-char-short-hash>
---

[analyzed content]
```

### source.json Format

```json
{
  "type": "github|local",
  "owner": "org",
  "repo": "my-repo",
  "host": "github.com",
  "url": "https://github.com/org/my-repo",
  "path": "/absolute/path/for/local",
  "branch": "main",
  "last_commit": "full-40-char-hash",
  "last_analyzed": "2026-03-28T10:00:00.000Z"
}
```

### layer.json Format

```json
{
  "active": true,
  "tags": ["architecture", "patterns"],
  "created_at": "2026-03-28T10:00:00.000Z",
  "semantic_profile": {
    "patterns.architecture": 0.95,
    "patterns.naming": 0.80,
    "conventions.testing": 0.30,
    "structure": 0.90
  }
}
```

The `semantic_profile` maps category taxonomy paths to strength scores in `[0.0, 1.0]`, produced by `extract_semantic_profile()` from `skills/dream-layers/semantic-extractor.md`. This replaces the former flat `priority` integer; ordering is now derived from the tensor.

---

## Writing Procedure

### Initial Load

1. **Create directory**: `.claude/dreams/<name>/`
2. **Write source.json**: From loader output
3. **Write layer.json**: With initial config (active, tags, created_at)
4. **Write memory files**: From analyzer output, one file per analysis type
5. **Extract semantic profile**: Call `extract_semantic_profile()` from `skills/dream-layers/semantic-extractor.md` with the analysis results, then write the returned profile into `layer.json` under the `semantic_profile` key
6. **Update tensor**: Call `populate_tensor_for_dream()` from `skills/dream-layers/tensor.md` with the dream name and analysis results (including the semantic profile)
7. **Update trie**: Call `trie_insert_dream()` from `skills/dream-layers/trie.md` to insert the new dream into the semantic trie
8. **Write/update DREAMS.md**: Add entry for new dream

### Incremental Update

1. **Read existing memory files**: For areas being updated
2. **Merge updates**: Replace updated sections, preserve unchanged
3. **Write updated files**: Only changed memory files
4. **Update source.json**: New commit hash and timestamp
5. **Re-extract semantic profile**: Call `extract_semantic_profile()` from `skills/dream-layers/semantic-extractor.md` with the updated analysis results and write the new profile to `layer.json`
6. **Update tensor**: Call `populate_tensor_for_dream()` from `skills/dream-layers/tensor.md` with the dream name and updated analysis results
7. **Refresh trie**: Call `trie_remove_dream()` then `trie_insert_dream()` from `skills/dream-layers/trie.md` to reflect updated scores
8. **Update DREAMS.md**: Refresh status indicators

### Forget (Delete)

1. **Delete directory**: `rm -rf .claude/dreams/<name>/`
2. **Remove from tensor**: Call `remove_dream_from_tensor()` from `skills/dream-layers/tensor.md`
3. **Remove from trie**: Call `trie_remove_dream()` from `skills/dream-layers/trie.md`
4. **Update DREAMS.md**: Remove entry (ordering now comes from `tensor.base_order`)

---

## DREAMS.md Index

The index file provides a quick overview of all loaded dreams.

### Format

```markdown
# Dream States

Active dreams loaded for this project. Each dream provides patterns and conventions
that guide Claude's development assistance.

## Loaded Dreams

- [architecture-ref](architecture-ref/) — GitHub: org/repo (main@abc1234), position 1
- [testing-patterns](testing-patterns/) — Local: /path/to/repo (main@def5678), position 2
- [ui-reference](ui-reference/) — GitHub: org/ui-lib (main@ghi9012), position 3

## Layer Order (by tensor base_order)

1. **architecture-ref** — Architecture and structure patterns
2. **testing-patterns** — Testing conventions and patterns
3. **ui-reference** — UI component patterns
```

### Updating the Index

When writing DREAMS.md:
1. Read all dream directories in `.claude/dreams/`
2. Read each dream's `source.json` and `layer.json`
3. Sort by `tensor.base_order` position (read from `tensor.json`). If `tensor.json` doesn't exist yet, fall back to alphabetical ordering.
4. Generate the index with current metadata
5. Write the complete file (replace, not append)

---

## File Size Guidelines

Keep individual memory files concise and actionable:

| File | Target Size | Max Size |
|------|------------|----------|
| structure.md | 50-100 lines | 200 lines |
| patterns.md | 80-150 lines | 300 lines |
| dependencies.md | 40-80 lines | 150 lines |
| conventions.md | 80-150 lines | 300 lines |
| summary.md | 20-40 lines | 80 lines |
| DREAMS.md | 5-20 lines | 50 lines |

If analysis exceeds max size, prioritize the most distinctive and actionable observations. Generic boilerplate should be trimmed.

---

## Error Handling

| Scenario | Action |
|----------|--------|
| `.claude/dreams/` doesn't exist | Create it |
| Dream directory already exists (overwrite) | Delete and recreate |
| Write permission denied | Display error, suggest checking permissions |
| Disk space issue | Display error with file sizes |
| Corrupted source.json | Display warning, suggest `/mentor forget` + `/mentor load` |
