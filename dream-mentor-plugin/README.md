# Dream Mentor

Load repos as dream states to guide development with Claude Code. Point Claude at a reference codebase and it learns the patterns, conventions, and architecture to mentor your current project.

## What it does

Dream Mentor lets you load **reference repositories** as "dream states" that Claude uses to guide development. You point it at a GitHub repo or local directory, and it analyzes the structure, patterns, dependencies, and conventions. Then Claude uses that knowledge when helping you write code, make architecture decisions, and follow best practices.

- Load any GitHub repo or local directory as a dream state
- Automatic staleness detection — knows when the source has new commits
- Multiple dreams with layer priorities — architecture from repo A, testing from repo B
- Compare your current project against the dream with `/dream-mentor:mentor diff`
- All analysis stored locally in `.claude/dreams/`

## Installation

Clone the repo into your Claude Code plugins directory:

```bash
git clone <repo-url> dream-mentor-plugin
```

Claude Code will automatically detect the `.claude-plugin/plugin.json` manifest and register the command.

> **Important**: Plugin commands must be invoked with the fully qualified name — `dream-mentor:mentor` — not just `/mentor`. For example: `/dream-mentor:mentor load https://github.com/org/repo`.

### Requirements

- Claude Code CLI, Desktop, or IDE extension
- `git` CLI available in PATH
- `gh` CLI installed and authenticated (for GitHub repos)

## Quick start

### 1. Load a dream from a GitHub repo

```bash
/dream-mentor:mentor load https://github.com/org/awesome-project
```

Claude analyzes the repo and stores the dream. Now it knows the project's architecture, patterns, and conventions.

### 2. Load a local directory

```bash
/dream-mentor:mentor load /path/to/reference-project --name my-reference
```

### 3. Check dream status

```bash
/dream-mentor:mentor status
```

Shows whether your dreams are fresh or stale (source has new commits).

### 4. Compare your project against the dream

```bash
/dream-mentor:mentor diff
```

Outputs a structured comparison: what your project is missing, pattern divergences, dependency gaps, and prioritized recommendations.

## Command reference

> **Why `/mentor`?** Claude Code has a built-in `/dream` command. This plugin uses `/mentor` to avoid the collision. When the built-in becomes available, run `/dream-mentor:mentor migrate` to export your dreams to the native format.

### `/dream-mentor:mentor <subcommand> [options]`

| Subcommand | Description |
|-----------|-------------|
| `load <source>` | Load a repo as a dream state |
| `status [--name <n>]` | Show dream status and staleness |
| `update [--name <n> \| --all]` | Refresh dream from source |
| `diff [--name <n>]` | Compare current project vs dream |
| `list` | List all dreams with layer priorities |
| `forget <name>` | Remove a dream state |
| `migrate [--name <n> \| --all]` | Export to Claude's built-in `/dream` format |
| `help` | Show help |

### Load options

| Option | Description | Default |
|--------|-------------|---------|
| `--name <name>` | Custom dream name | Derived from repo name |
| `--layer <priority>` | Layer priority (1 = highest) | Next available |
| `--branch <branch>` | Branch to track | main/master |

### Examples

```bash
# Load with all defaults
/dream-mentor:mentor load https://github.com/org/repo

# Named dream with priority
/dream-mentor:mentor load https://github.com/org/repo --name architecture --layer 1

# Load local repo
/dream-mentor:mentor load ./reference-project --name testing-ref --layer 2

# Check freshness
/dream-mentor:mentor status
/dream-mentor:mentor status --name architecture

# Update stale dreams
/dream-mentor:mentor update --all
/dream-mentor:mentor update --name architecture

# Compare against dream
/dream-mentor:mentor diff
/dream-mentor:mentor diff --name architecture

# List all dreams
/dream-mentor:mentor list

# Remove a dream
/dream-mentor:mentor forget old-dream

# Combine: architecture from one repo, testing from another
/dream-mentor:mentor load https://github.com/org/main-app --name arch --layer 1
/dream-mentor:mentor load https://github.com/org/test-patterns --name testing --layer 2
```

## How dreams work

### Loading

When you run `/dream-mentor:mentor load`, the plugin:

1. Clones the repo (GitHub) or references the directory (local)
2. Runs 3 parallel analysis agents to examine the codebase
3. Produces 5 structured memory files:
   - `structure.md` — Directory layout, modules, entry points
   - `patterns.md` — Architecture, design patterns, naming conventions
   - `dependencies.md` — Frameworks, libraries, versions
   - `conventions.md` — Testing, build, CI, linting patterns
   - `summary.md` — High-level overview and key decisions
4. Stores everything in `.claude/dreams/<name>/`
5. Cleans up any temp clone

### Staleness detection

Every command checks if your dreams are behind their source:

- **Local repos**: Compares stored commit hash vs `git rev-parse HEAD`
- **GitHub repos**: Compares stored hash vs latest commit via `gh api`
- Warnings displayed automatically when dreams are stale
- Use `/dream-mentor:mentor update` to refresh

### Layer system

Load multiple dreams with different priorities:

```bash
/dream-mentor:mentor load https://github.com/org/main-app --name arch --layer 1
/dream-mentor:mentor load https://github.com/org/test-lib --name testing --layer 2
/dream-mentor:mentor load https://github.com/org/ui-kit --name ui --layer 3
```

- Priority 1 = highest precedence
- Non-conflicting patterns merge from all layers
- Conflicting patterns: higher priority wins
- Dependencies are always additive (union of all layers)

Example: If arch (priority 1) uses kebab-case and testing (priority 2) uses camelCase, kebab-case wins.

### Dream diff

`/dream-mentor:mentor diff` compares your project against the dream and produces:

- **Structure differences**: Missing directories, different organization
- **Pattern divergences**: Architecture, naming, error handling differences
- **Dependency gaps**: Libraries the dream uses that you don't
- **Convention mismatches**: Testing, build, CI differences
- **Prioritized recommendations**: What to adopt first

## Storage

All dream data lives in your project's `.claude/dreams/` directory:

```
.claude/dreams/
  DREAMS.md                    # Index of all dreams
  my-dream/
    source.json                # Source metadata, commit tracking
    layer.json                 # Priority and layer config
    structure.md               # Directory analysis
    patterns.md                # Code patterns
    dependencies.md            # Dependency catalog
    conventions.md             # Dev conventions
    summary.md                 # Project overview
```

## Migrating to Claude's built-in /dream

When Claude's built-in `/dream` becomes available:

```bash
# Export all dreams to portable format
/dream-mentor:mentor migrate --all

# Export a specific dream
/dream-mentor:mentor migrate --name architecture
```

This writes portable JSON to `.claude/dreams/_export/` that can be imported by the built-in. The compatibility layer (`skills/dream-compat/SKILL.md`) will be updated with native format mapping once the built-in schema is documented.

After migration, you can keep both systems running side by side or clean up with `/dream-mentor:mentor forget`.

## Project structure

```
dream-mentor-plugin/
  .claude-plugin/
    plugin.json                # Plugin manifest
  commands/
    mentor.md                  # /mentor command definition
  skills/
    dream-manager/
      SKILL.md                 # Core dream lifecycle
      loader.md                # Source resolution and cloning
      analyzer.md              # Parallel repo analysis
      memory-writer.md         # Dream memory file management
      staleness-checker.md     # Freshness detection
      diff-engine.md           # Project vs dream comparison
    dream-layers/
      SKILL.md                 # Layer composition
      resolver.md              # Conflict resolution
    dream-compat/
      SKILL.md                 # Compatibility layer for built-in /dream migration
  README.md
```

## Troubleshooting

**"Cannot access source"**
For GitHub: ensure `gh auth status` shows authenticated. For local: ensure the path exists and is a git repo.

**"gh: command not found"**
Install the GitHub CLI: https://cli.github.com/

**Dreams always showing as stale**
Check that the tracked branch is correct. Use `/dream-mentor:mentor status` to see the branch being tracked.

**Slow dream loading**
Large repos take longer to analyze. The clone uses `--depth 1` for speed. For very large repos, consider loading a specific branch.

**Layer conflicts not resolving as expected**
Check priorities with `/dream-mentor:mentor list`. Priority 1 always wins. Reassign priorities by editing `.claude/dreams/<name>/layer.json`.
