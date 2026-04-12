# /mentor Command

> **Deprecated**: The `/mentor` command is superseded by the `dream-mentor` agent.
> Run `claude --agent dream-mentor` for a natural-language interface to all dream operations.
> `/mentor` remains functional for backward compatibility.

**Description**: Load and manage dream states from GitHub repos or local directories to guide development

> **Note**: This command is named `/mentor` to avoid collision with Claude's built-in `/dream` command.
> When the built-in `/dream` becomes available, use `/mentor migrate` to export your dream states
> to the native format. See `skills/dream-compat/SKILL.md` for details.

**Usage**:
```
/mentor <subcommand> [options]
```

**Subcommands**:
- `load <repo-url-or-path>` - Load a repo as a dream state
- `status [--name <name>]` - Show dream status and staleness
- `update [--name <name> | --all]` - Refresh dream from source
- `diff [--name <name>]` - Compare current project vs dream
- `list` - List all loaded dreams with layer priorities
- `forget <name>` - Remove a dream state
- `reorder <operation> [args]` - Change layer ordering (move-to-front, swap, promote, etc.)
- `migrate [--name <name> | --all]` - Export dreams to Claude's built-in /dream format
- `help` - Show usage information

**Load Options**:
- `--name <name>`: Name for the dream (default: derived from repo name)
- `--layer <priority>`: Layer priority, 1 = highest (default: next available)
- `--branch <branch>`: Branch to track (default: main/master)

**Reorder Operations**:
- `move-to-front <name>`: Set dream to highest precedence
- `move-to-back <name>`: Set dream to lowest precedence
- `move-before <name> <target>`: Insert before target
- `move-after <name> <target>`: Insert after target
- `swap <name-a> <name-b>`: Exchange positions
- `promote <name>`: Move up one position
- `demote <name>`: Move down one position
- `undo`: Revert the last reorder operation
- `--preview`: Show what would change without applying

**Examples**:
```bash
# Load a GitHub repo as a dream
/mentor load https://github.com/org/awesome-project

# Load a local directory with a custom name
/mentor load /path/to/reference-repo --name architecture-reference

# Load with layer priority
/mentor load https://github.com/org/testing-patterns --name testing --layer 2

# Check dream freshness
/mentor status

# Update all dreams
/mentor update --all

# Compare current project against dream
/mentor diff --name architecture-reference

# List all dreams
/mentor list

# Remove a dream
/mentor forget old-dream

# Reorder dreams — move to front
/mentor reorder move-to-front testing-patterns

# Reorder dreams — swap two dreams
/mentor reorder swap architecture-ref testing-patterns

# Reorder dreams — promote one position
/mentor reorder promote ui-reference

# Preview a reorder without applying
/mentor reorder move-to-front testing-patterns --preview

# Undo the last reorder
/mentor reorder undo
```

---

## Command Behavior

This command manages dream states - analyzed snapshots of reference repositories that guide Claude's development assistance. Dreams persist in `.claude/dreams/` and are checked for staleness on every invocation.

**Core Concept**: A "dream" is a structured analysis of a reference codebase stored as memory files. When loaded, Claude uses these patterns, conventions, and architecture decisions to guide development in the current project.

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/mentor` command to manage dream states - reference codebases that guide development.

## Your Task

Parse the user's subcommand and arguments, then execute the appropriate dream operation.

### Step 1: Parse Arguments

```javascript
const args = parseCommandArgs(userInput);
const subcommand = args.positional[0]; // load, status, update, diff, list, forget, migrate, help

// Common options
const dream_name = args['name'] || null;
const layer_priority = args['layer'] ? parseInt(args['layer'], 10) : null;
const branch = args['branch'] || null;
const update_all = args['all'] || false;

// For load subcommand
const source = args.positional[1]; // URL or path
```

### Step 2: Validate Subcommand

```javascript
const VALID_SUBCOMMANDS = ['load', 'status', 'update', 'diff', 'list', 'forget', 'reorder', 'migrate', 'help'];

if (!subcommand || !VALID_SUBCOMMANDS.includes(subcommand)) {
  // Display help text and STOP
}
```

### Step 3: Run Staleness Check (All Subcommands Except Help)

Before executing any subcommand (except `help`), run a lightweight staleness check on all loaded dreams:

1. Read `.claude/dreams/DREAMS.md` to find all loaded dreams
2. For each dream, read its `source.json`
3. For local repos: run `git -C <path> rev-parse HEAD` and compare to `last_commit`
4. For GitHub repos: run `gh api repos/<owner>/<repo>/commits/<branch> --jq .sha` and compare
5. If any dream is stale, display a warning:
   ```
   Warning: Dream "{name}" is behind source ({n} commits). Run /mentor update --name {name} to refresh.
   ```

Use the `dream-manager` skill's `staleness-checker` sub-skill for this check.

### Step 4: Execute Subcommand

#### `load` - Load a Dream State

**Required**: `source` (URL or path)

1. **Resolve source type**:
   - If source starts with `http://`, `https://`, `git@`, or matches `owner/repo` pattern → GitHub repo
   - Otherwise → local directory path

2. **Derive dream name** (if `--name` not provided):
   - From GitHub URL: extract repo name (e.g., `https://github.com/org/my-repo` → `my-repo`)
   - From local path: use directory name

3. **Check for existing dream**:
   - Read `.claude/dreams/DREAMS.md`
   - If dream with same name exists, ask user:
     ```
     Dream "{name}" already exists. Overwrite? [Yes / Rename / Cancel]
     ```

4. **Assign layer priority**:
   - If `--layer` provided, use it
   - Otherwise, assign next available priority (max existing + 1, or 1 if first dream)

5. **Load and analyze** using `dream-manager` skill:
   - For GitHub: clone to temp dir via `gh repo clone`
   - For local: use path directly
   - Run parallel analysis agents (structure, patterns, dependencies, conventions)
   - Write memory files to `.claude/dreams/<name>/`
   - Write `source.json` with metadata
   - Write `layer.json` with priority config
   - Update `DREAMS.md` index
   - For GitHub: clean up temp clone

6. **Display summary**:
   ```markdown
   # Dream Loaded: {name}

   **Source**: {url_or_path}
   **Branch**: {branch}
   **Commit**: {short_hash}
   **Layer Priority**: {priority}

   ## What was learned:
   - **Structure**: {brief summary of project structure}
   - **Patterns**: {key patterns identified}
   - **Dependencies**: {major frameworks/libs}
   - **Conventions**: {coding conventions found}

   Dream is now active. Claude will use these patterns to guide development.
   ```

#### `status` - Show Dream Status

1. If `--name` provided, show status for that dream only
2. Otherwise, show status for all dreams
3. For each dream, display:
   ```markdown
   ## Dream: {name}
   **Source**: {url_or_path}
   **Branch**: {branch}
   **Last Analyzed**: {timestamp}
   **Status**: Fresh / Stale ({n} commits behind)
   **Layer Priority**: {priority}
   ```

#### `update` - Refresh Dream from Source

1. If `--all`, update all dreams. If `--name`, update that dream only. Otherwise, update all stale dreams.
2. For each dream to update:
   - Fetch latest from source
   - Determine changed files since `last_commit`
   - Re-analyze only changed areas (incremental update)
   - Update memory files
   - Update `source.json` with new commit hash and timestamp
3. Display what changed:
   ```markdown
   # Dream Updated: {name}

   **Previous commit**: {old_hash}
   **Current commit**: {new_hash}
   **Files changed**: {count}

   ## Updated analysis areas:
   - {list of memory files that were updated}
   ```

#### `diff` - Compare Current Project vs Dream

1. If `--name` provided, diff against that dream. Otherwise, diff against merged layer view.
2. Load dream memory files
3. Analyze current project (structure, patterns, deps, conventions)
4. Compare and output:
   ```markdown
   # Dream Diff: {name} vs Current Project

   ## Structure Differences
   {missing dirs/files, extra dirs/files}

   ## Pattern Divergences
   {conventions the dream follows that current project doesn't}

   ## Dependency Gaps
   {deps in dream not in current project}

   ## Recommendations
   {actionable items to align with dream}
   ```

#### `list` - List All Dreams

1. Read `.claude/dreams/DREAMS.md`
2. For each dream, read `source.json` and `layer.json`
3. Display sorted by layer priority:
   ```markdown
   # Loaded Dreams

   | Priority | Name | Source | Last Updated | Status |
   |----------|------|--------|-------------|--------|
   | 1 | architecture-ref | github.com/org/repo | 2h ago | Fresh |
   | 2 | testing-patterns | /local/path | 1d ago | Stale |
   ```

#### `forget` - Remove a Dream

**Required**: dream name as positional arg

1. Verify dream exists in `.claude/dreams/<name>/`
2. Confirm with user:
   ```
   Remove dream "{name}" and all its memory files? [Yes / Cancel]
   ```
3. Delete `.claude/dreams/<name>/` directory
4. Update `DREAMS.md` index
5. Re-number layer priorities if needed
6. Display confirmation

#### `migrate` - Export Dreams to Claude's Built-in /dream Format

Exports dream states to whatever format Claude's built-in `/dream` command expects. Uses the `dream-compat` compatibility layer skill.

1. If `--name` provided, migrate that dream only. If `--all`, migrate all dreams. Otherwise, prompt user.
2. For each dream to migrate:
   - Read all memory files from `.claude/dreams/<name>/`
   - Transform to the built-in `/dream` format using `dream-compat` skill
   - Write output to the location the built-in expects
   - Validate the migration succeeded
3. Display migration summary:
   ```markdown
   # Dreams Migrated

   | Dream | Status | Notes |
   |-------|--------|-------|
   | architecture-ref | Migrated | Ready for /dream |
   | testing-patterns | Migrated | Ready for /dream |

   Your dreams are now available via Claude's built-in /dream command.
   You can safely run /mentor forget to clean up the old format,
   or keep both for a transition period.
   ```

**Note**: This subcommand will be fully implemented once the built-in `/dream` format is documented. Until then, it exports a portable JSON representation that can be adapted.

#### `reorder` - Change Layer Ordering

**Required**: operation name as positional arg (e.g., `move-to-front`, `swap`, `promote`)

1. **Parse operation and arguments**:
   ```javascript
   const operation = args.positional[1]; // move-to-front, move-to-back, move-before, move-after, swap, promote, demote, undo
   const dreamName = args.positional[2]; // dream name (not needed for undo)
   const targetName = args.positional[3]; // second dream name (for move-before, move-after, swap)
   const preview = args['preview'] || args['dry-run'] || false;
   const force = args['force'] || false;
   ```

2. **Validate operation**:
   ```javascript
   const VALID_OPERATIONS = ['move-to-front', 'move-to-back', 'move-before', 'move-after', 'swap', 'promote', 'demote', 'undo'];
   if (!operation || !VALID_OPERATIONS.includes(operation)) {
     // Display reorder usage and STOP
   }
   ```

3. **Map CLI operation names to reorder functions**:
   - `move-to-front <name>` → `move_to_front(name)`
   - `move-to-back <name>` → `move_to_back(name)`
   - `move-before <name> <target>` → `move_before(name, target)`
   - `move-after <name> <target>` → `move_after(name, target)`
   - `swap <name-a> <name-b>` → `swap(name_a, name_b)`
   - `promote <name>` → `promote(name)`
   - `demote <name>` → `demote(name)`
   - `undo` → `undo_reorder()`

4. **If `--preview` flag is set**, use `preview_reorder()` from the `dream-layers` reorder sub-skill:
   - Show the order change (before/after)
   - Show any conflict resolution changes
   - Show any merged value changes
   - Ask user whether to apply

5. **If no `--preview` flag**, use `execute_reorder_with_preview()`:
   - If conflicts would change, automatically show preview and ask for confirmation
   - If no conflict impact (or `--force`), apply directly

6. **Display result**:
   ```markdown
   # Layer Order Updated

   **Operation**: {operation}
   **Before**: architecture-ref (1) > testing-patterns (2) > ui-reference (3)
   **After**:  testing-patterns (1) > architecture-ref (2) > ui-reference (3)

   {if conflicts changed}
   ## Conflict Resolutions Changed
   | Category | Key | Was Won By | Now Won By |
   |----------|-----|-----------|------------|
   | ... | ... | ... | ... |
   {end if}
   ```

7. **Undo case**: When operation is `undo`, display what was undone:
   ```markdown
   # Reorder Undone

   **Reverted**: {previous operation}
   **Restored Order**: architecture-ref (1) > testing-patterns (2) > ui-reference (3)
   ```

#### `help` - Show Usage

Display the command usage, subcommands, and examples from the top of this file.

---

## Dream Memory Storage

All dream data is stored in the current project's `.claude/dreams/` directory:

```
.claude/dreams/
  DREAMS.md                        # Index of all loaded dreams
  <dream-name>/
    source.json                    # Source metadata (type, url, path, branch, commit, timestamp)
    layer.json                     # Layer configuration (priority, active, tags)
    structure.md                   # Directory layout and module boundaries
    patterns.md                    # Code patterns, architecture, naming conventions
    dependencies.md                # Dependencies, frameworks, versions
    conventions.md                 # File organization, testing, build patterns
    summary.md                     # High-level overview
```

### DREAMS.md Format

```markdown
# Dream States

- [architecture-ref](architecture-ref/) — GitHub: org/repo, priority 1, fresh
- [testing-patterns](testing-patterns/) — Local: /path/to/repo, priority 2, stale
```

### Memory File Frontmatter

Each dream memory file uses this frontmatter format:

```markdown
---
dream: <dream-name>
type: structure|patterns|dependencies|conventions|summary
source: <url-or-path>
analyzed_at: <ISO-8601-timestamp>
commit: <short-hash>
---

[analyzed content]
```

---

## Staleness Detection

Every `/mentor` subcommand (except `help`) runs a lightweight staleness check:

1. Read each dream's `source.json`
2. Compare stored `last_commit` against current source HEAD:
   - **Local**: `git -C <path> rev-parse HEAD`
   - **GitHub**: `gh api repos/<owner>/<repo>/commits/<branch> --jq .sha`
3. If different, mark as stale and display warning
4. Staleness check should complete in <2 seconds for local, <5 seconds for GitHub

---

## Layer System

Dreams support layered composition for multi-repo guidance:

- Each dream has a numeric priority (1 = highest)
- When Claude uses dream guidance, higher-priority patterns take precedence
- Non-conflicting patterns from all layers are merged
- Use case: "architecture from repo A (priority 1), testing patterns from repo B (priority 2)"

Layer resolution is handled by the `dream-layers` skill.

---

## Error Handling

### No Source Provided for Load
```
Error: Missing required argument <repo-url-or-path>.

Usage: /mentor load <repo-url-or-path> [--name <name>] [--layer <priority>]

Examples:
  /mentor load https://github.com/org/repo
  /mentor load /path/to/local/repo --name my-dream
```

### Dream Not Found
```
Error: Dream "{name}" not found.

Loaded dreams:
{list from DREAMS.md}

Run /mentor list to see all dreams.
```

### Invalid Layer Priority
```
Error: --layer must be a positive integer. Got: '{value}'.
```

### Source Not Accessible
```
Error: Cannot access source "{source}".

For GitHub repos: ensure you have access and gh is authenticated.
For local paths: ensure the directory exists and contains a git repository.
```

### No Dreams Loaded
```
No dreams loaded yet.

Load a dream with: /mentor load <repo-url-or-path>

Examples:
  /mentor load https://github.com/org/repo
  /mentor load /path/to/local/repo --name my-dream
```

---

## Help Text

When user runs `/mentor help`:

```markdown
# /mentor Command Help

**Description**: Load repos as dream states to guide development

A "dream" is a structured analysis of a reference codebase. When loaded,
Claude uses the dream's patterns, conventions, and architecture to guide
development in your current project.

Note: Named /mentor to avoid collision with Claude's built-in /dream.
Use /mentor migrate when the built-in becomes available.

**Usage**: /mentor <subcommand> [options]

**Subcommands**:
  load <source> [opts]   Load a repo as a dream state
  status [--name <n>]    Show dream freshness and metadata
  update [--name|--all]  Refresh dream(s) from source
  diff [--name <n>]      Compare current project vs dream
  list                   List all dreams with layer priorities
  forget <name>          Remove a dream state
  reorder <op> [args]    Change layer ordering
  migrate [--name|--all] Export to Claude's built-in /dream format
  help                   Show this help message

**Load Options**:
  --name <name>          Custom name (default: repo name)
  --layer <priority>     Layer priority, 1=highest (default: auto)
  --branch <branch>      Branch to track (default: main)

**Reorder Operations**:
  move-to-front <name>   Set dream to highest precedence
  move-to-back <name>    Set dream to lowest precedence
  move-before <n> <tgt>  Insert before target
  move-after <n> <tgt>   Insert after target
  swap <a> <b>           Exchange positions
  promote <name>         Move up one position
  demote <name>          Move down one position
  undo                   Revert last reorder
  --preview              Dry run (show changes only)

**Examples**:
  /mentor load https://github.com/org/repo
  /mentor load ./reference-project --name arch --layer 1
  /mentor status
  /mentor update --all
  /mentor diff --name arch
  /mentor list
  /mentor forget old-dream
  /mentor reorder move-to-front testing
  /mentor reorder swap arch testing
  /mentor reorder promote ui-ref
  /mentor reorder undo

**How it works**:
1. /mentor load clones/references a repo and analyzes its structure,
   patterns, dependencies, and conventions
2. Analysis is stored as memory files in .claude/dreams/<name>/
3. Claude reads these memories to guide development decisions
4. Staleness is checked automatically - you're warned when dreams
   fall behind their source
5. Multiple dreams can be layered (priority 1 = highest precedence)

**Storage**: .claude/dreams/ in your current project
```

---

## Notes

### Relationship to Skills

This command delegates to three skill groups:

1. **dream-manager**: Core lifecycle (load, analyze, store, check, update, diff)
2. **dream-layers**: Layer composition, conflict resolution, tensor ordering, and reorder operations
3. **dream-compat**: Compatibility layer for migrating to Claude's built-in `/dream`

### How Dreams Guide Development

Once loaded, dream memory files are available in `.claude/dreams/`. Claude reads these files when:
- The user asks for guidance on project structure
- Making architectural decisions
- Writing new code (follows dream conventions)
- Setting up testing, CI, or build systems

The dream acts as a "mentor" - a reference implementation that Claude can learn from and apply to the current project.

### Incremental Updates

The `update` subcommand performs incremental analysis:
1. Fetches changed files since last analyzed commit
2. Re-analyzes only affected memory areas
3. For example, if only test files changed, only `conventions.md` (testing section) is updated
4. Full re-analysis can be forced with `/mentor forget` + `/mentor load`
