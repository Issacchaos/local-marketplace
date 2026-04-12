# Dream Manager Skill

**Description**: Core dream state lifecycle management - load, analyze, store, check, update, and diff reference codebases.

**Trigger**: Used by the `/mentor` command for all dream operations.

---

## Overview

The dream-manager skill orchestrates the full lifecycle of dream states:

1. **Load** - Resolve source (GitHub URL or local path), clone if needed
2. **Analyze** - Extract structure, patterns, dependencies, conventions via parallel agents
3. **Store** - Write structured memory files to `.claude/dreams/<name>/`
4. **Check** - Lightweight staleness detection against source HEAD
5. **Update** - Incremental re-analysis of changed files
6. **Diff** - Compare dream patterns against current project

## Sub-Skills

| Sub-Skill | File | Purpose |
|-----------|------|---------|
| Loader | `loader.md` | Source resolution, cloning, path validation |
| Analyzer | `analyzer.md` | Parallel repo analysis (structure, patterns, deps, conventions) |
| Memory Writer | `memory-writer.md` | Write/update dream memory files and index |
| Staleness Checker | `staleness-checker.md` | Detect when source repo has new commits |
| Diff Engine | `diff-engine.md` | Compare current project against dream state |

## Dream Lifecycle

### Load Flow

```
Input: source (URL or path), name, layer priority, branch
  │
  ├─ loader.md: Resolve source type, validate access
  │   ├─ GitHub: gh repo clone → temp dir
  │   └─ Local: validate path exists, is git repo
  │
  ├─ analyzer.md: Run parallel analysis agents
  │   ├─ Agent 1: Structure analysis (dirs, modules, entry points)
  │   ├─ Agent 2: Pattern analysis (architecture, naming, code style)
  │   ├─ Agent 3: Dependency analysis (package files, frameworks)
  │   └─ Agent 4: Convention analysis (testing, build, CI, docs)
  │
  ├─ memory-writer.md: Write memory files
  │   ├─ source.json (metadata)
  │   ├─ layer.json (priority config)
  │   ├─ structure.md
  │   ├─ patterns.md
  │   ├─ dependencies.md
  │   ├─ conventions.md
  │   └─ summary.md
  │
  └─ memory-writer.md: Update DREAMS.md index

Output: Dream loaded confirmation with summary
```

### Staleness Check Flow

```
Input: dream name (or all dreams)
  │
  ├─ Read source.json for each dream
  ├─ staleness-checker.md: Compare last_commit vs current HEAD
  │   ├─ Local: git -C <path> rev-parse HEAD
  │   └─ GitHub: gh api repos/<owner>/<repo>/commits/<branch>
  │
  └─ Return: { stale: bool, commits_behind: int, changed_files: [] }
```

### Update Flow

```
Input: dream name (or all stale dreams)
  │
  ├─ staleness-checker.md: Get changed files since last_commit
  │   ├─ Local: git -C <path> diff --name-only <last_commit>..HEAD
  │   └─ GitHub: gh api compare endpoint
  │
  ├─ analyzer.md: Re-analyze only affected areas
  │   ├─ Map changed files → memory categories
  │   └─ Re-run relevant analysis agents
  │
  ├─ memory-writer.md: Update affected memory files
  │
  └─ memory-writer.md: Update source.json (new commit, timestamp)
```

### Diff Flow

```
Input: dream name (or merged layer view)
  │
  ├─ Read dream memory files
  ├─ diff-engine.md: Analyze current project
  ├─ diff-engine.md: Compare dream vs current
  │   ├─ Structure differences
  │   ├─ Pattern divergences
  │   ├─ Dependency gaps
  │   └─ Convention mismatches
  │
  └─ Output: Diff report with recommendations
```

## Analysis Depth

The analyzer produces 5 memory files per dream:

### structure.md
- Top-level directory layout
- Module/package boundaries
- Entry points and main files
- Configuration file locations
- Test directory structure

### patterns.md
- Architecture style (monolith, microservices, modular, etc.)
- Design patterns in use (MVC, repository, factory, etc.)
- Naming conventions (files, functions, classes, variables)
- Code organization patterns (by feature, by layer, etc.)
- Error handling patterns
- State management approach

### dependencies.md
- Language and runtime versions
- Package manager and lock file
- Core framework(s) and version
- Key libraries with their purpose
- Dev dependencies (testing, linting, building)
- External service integrations

### conventions.md
- Testing framework and patterns (unit, integration, e2e)
- Build system and scripts
- Linting and formatting configuration
- CI/CD pipeline structure
- Documentation style
- Git workflow (branching strategy, commit conventions)
- Environment and config management

### summary.md
- What the project does (one paragraph)
- Key architectural decisions and why
- Technology stack overview
- Project maturity and activity level
- Notable strengths to emulate

## Configuration

Dreams are stored per-project in `.claude/dreams/`. No global configuration is needed.

### Environment Variables

None required. The skill uses `gh` CLI for GitHub operations (must be authenticated).

### Prerequisites

- `git` CLI available in PATH
- `gh` CLI available and authenticated (for GitHub repos)
