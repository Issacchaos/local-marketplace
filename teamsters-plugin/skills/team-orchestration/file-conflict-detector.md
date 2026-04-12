---
name: file-conflict-detector
description: Detect file-level conflicts between agents by analyzing files_read and files_write frontmatter fields, building dependency graphs, identifying implicit dependencies and parallel write conflicts, and suggesting fixes.
user-invocable: false
---

# File Conflict Detector Skill

**Version**: 1.0.0
**Category**: Validation
**Purpose**: Detect file-level conflicts between agents to prevent data races and ensure safe parallel execution

**Used By**: Team Orchestration SKILL (Phase 1 validation), Approval Gate Handler (conflict warnings)

---

## Overview

The File Conflict Detector Skill analyzes agent definitions to identify file-level conflicts that could cause data corruption, race conditions, or implicit ordering requirements. It builds a file dependency graph from agent `files_read` and `files_write` frontmatter fields, then validates that agents scheduled for parallel execution do not have conflicting file access patterns.

This skill is critical for:
- **Safety**: Preventing two parallel agents from writing to the same file simultaneously
- **Correctness**: Detecting implicit dependencies where one agent reads a file another agent writes
- **Clarity**: Surfacing hidden ordering requirements that are not captured in explicit dependencies
- **Reliability**: Providing actionable fix suggestions before execution begins

### Key Principles

1. **Analyze Before Execute**: File conflicts must be detected during validation (Phase 1), never at runtime
2. **Implicit Dependencies Are Real Dependencies**: If Agent B reads a file Agent A writes, B depends on A
3. **Parallel Write Conflicts Are Errors**: Two agents writing the same file in the same phase is always a conflict
4. **Sequential Phases Are Safe**: Agents in different phases (sequential ordering) cannot conflict
5. **Glob Patterns Supported**: File paths may use glob patterns (e.g., `src/**/*.ts`, `public/*`)
6. **Warnings Are Not Errors**: Implicit dependencies produce warnings; only parallel write conflicts produce errors

---

## Skill Interface

### Input

```yaml
agents: list                          # Agent specs from team definition (with files_read/files_write)
dependencies: list                    # Explicit dependency graph from team definition
execution_plan: dict                  # Execution plan with phases from build_execution_plan()
```

### Output

```yaml
# Success case (no conflicts)
file_dependency_result:
  implicit_deps: list                 # Discovered implicit dependencies
  conflicts: list                     # Parallel write conflicts (errors)
  warnings: list                      # Non-critical warnings (read-after-write, overlapping globs)
  file_graph:
    write_map: dict                   # {file_path: [agent_names writing]}
    read_map: dict                    # {file_path: [agent_names reading]}
    dependency_edges: list            # [{from: agent_a, to: agent_b, file: path, type: "read-after-write"}]

parallel_safety_result:
  safe: boolean                       # True if no conflicts in any parallel phase
  conflicts: list                     # List of conflict details
  suggested_fixes: list               # Actionable fix suggestions

# Error case (conflicts detected)
file_dependency_result:
  implicit_deps: [...]
  conflicts:
    - file: string                    # Conflicting file path
      agents: [string, string]        # Agents involved
      phase: integer                  # Phase where conflict occurs
      type: string                    # "parallel-write" | "read-write-race"
      severity: string                # "error" | "warning"
      suggestion: string             # How to fix
  warnings: [...]
```

---

## Agent File Frontmatter Schema

Agent definition files (`agents/*.md`) may declare file access patterns in their YAML frontmatter:

```yaml
---
name: backend-agent
type: agents/backend-agent.md
files_read:
  - "src/config.ts"
  - "src/types/**/*.ts"
  - "package.json"
files_write:
  - "src/server.ts"
  - "src/routes/**/*.ts"
  - "src/middleware/*.ts"
---
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `files_read` | `list[string]` | Files or glob patterns the agent reads during execution |
| `files_write` | `list[string]` | Files or glob patterns the agent writes/modifies during execution |

### Glob Pattern Support

The following glob patterns are supported in `files_read` and `files_write`:

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any single path segment | `src/*.ts` matches `src/index.ts` |
| `**` | Any number of path segments | `src/**/*.ts` matches `src/a/b/c.ts` |
| `?` | Any single character | `test?.py` matches `test1.py` |
| `{a,b}` | Alternation | `src/{api,lib}/*.ts` |

---

## Core Algorithms

### Algorithm 1: Build File Dependency Graph

```python
def build_file_dependency_graph(agents: list, dependencies: list) -> dict:
    """
    Build a file-level dependency graph from agent file access declarations.

    Analyzes files_read and files_write fields from each agent's frontmatter
    to discover:
    1. Which agents write to which files (write_map)
    2. Which agents read from which files (read_map)
    3. Implicit dependencies where a reader depends on a writer
    4. Conflicts where multiple agents write to the same file

    Args:
        agents: List of agent specs from team definition, each with optional
                'files_read' and 'files_write' fields
        dependencies: Explicit dependency list from team definition

    Returns:
        dict with:
            implicit_deps: List of discovered implicit dependencies
            conflicts: List of file conflicts (parallel writes)
            warnings: List of non-critical warnings
            file_graph: dict with write_map, read_map, dependency_edges
    """
    write_map = {}   # {normalized_path: [agent_names]}
    read_map = {}    # {normalized_path: [agent_names]}
    agent_files = {} # {agent_name: {reads: set, writes: set}}

    # Step 1: Collect file access patterns from all agents
    for agent in agents:
        agent_name = agent.get('name', 'unknown')
        files_read = agent.get('files_read', [])
        files_write = agent.get('files_write', [])

        agent_files[agent_name] = {
            'reads': set(files_read),
            'writes': set(files_write)
        }

        # Build write map
        for file_path in files_write:
            normalized = normalize_path(file_path)
            if normalized not in write_map:
                write_map[normalized] = []
            write_map[normalized].append(agent_name)

        # Build read map
        for file_path in files_read:
            normalized = normalize_path(file_path)
            if normalized not in read_map:
                read_map[normalized] = []
            read_map[normalized].append(agent_name)

    # Step 2: Build explicit dependency set for lookup
    explicit_deps = set()
    for dep in (dependencies or []):
        if 'from' in dep and 'to' in dep:
            explicit_deps.add((dep['from'], dep['to']))

    # Also include agent-level dependencies
    for agent in agents:
        agent_name = agent.get('name', 'unknown')
        for dep_name in agent.get('dependencies', []):
            explicit_deps.add((dep_name, agent_name))

    # Step 3: Detect implicit dependencies (read-after-write)
    implicit_deps = []
    dependency_edges = []

    for file_path, writers in write_map.items():
        # Check if any agent reads a file that another agent writes
        readers = find_matching_readers(file_path, read_map, agent_files)

        for writer in writers:
            for reader in readers:
                if writer == reader:
                    continue  # Same agent reading its own output is fine

                # Check if this dependency is already explicit
                if (writer, reader) in explicit_deps:
                    # Already declared - just record the edge
                    dependency_edges.append({
                        'from': writer,
                        'to': reader,
                        'file': file_path,
                        'type': 'read-after-write',
                        'explicit': True
                    })
                    continue

                # Implicit dependency discovered
                implicit_dep = {
                    'from': writer,
                    'to': reader,
                    'file': file_path,
                    'type': 'read-after-write',
                    'reason': (
                        f"Agent '{reader}' reads '{file_path}' which is written by "
                        f"agent '{writer}'. This creates an implicit ordering requirement: "
                        f"'{writer}' must complete before '{reader}' starts."
                    )
                }
                implicit_deps.append(implicit_dep)

                dependency_edges.append({
                    'from': writer,
                    'to': reader,
                    'file': file_path,
                    'type': 'read-after-write',
                    'explicit': False
                })

    # Step 4: Detect write-write conflicts (multiple writers to same file)
    conflicts = []

    for file_path, writers in write_map.items():
        if len(writers) > 1:
            conflicts.append({
                'file': file_path,
                'agents': writers,
                'type': 'parallel-write',
                'severity': 'error',
                'reason': (
                    f"Multiple agents write to '{file_path}': "
                    f"{', '.join(writers)}. "
                    f"If these agents run in the same parallel phase, "
                    f"this will cause a data race."
                )
            })

    # Step 5: Check for overlapping glob patterns (warnings)
    warnings = []
    warnings.extend(detect_glob_overlaps(write_map, agent_files))

    return {
        'implicit_deps': implicit_deps,
        'conflicts': conflicts,
        'warnings': warnings,
        'file_graph': {
            'write_map': write_map,
            'read_map': read_map,
            'dependency_edges': dependency_edges
        }
    }
```

---

### Algorithm 2: Validate Parallel Safety

```python
def validate_parallel_safety(execution_plan: dict, file_graph: dict) -> dict:
    """
    Validate that agents scheduled for parallel execution within the same
    phase do not have conflicting file access patterns.

    This is the critical safety check: agents running in parallel must not
    write to the same file, and agents that read files written by other
    agents must be in a later phase.

    Args:
        execution_plan: Execution plan with phases from build_execution_plan()
        file_graph: File dependency graph from build_file_dependency_graph()

    Returns:
        dict with:
            safe: bool - True if no conflicts in any parallel phase
            conflicts: list - Detailed conflict descriptions
            suggested_fixes: list - Actionable fix suggestions
    """
    conflicts = []
    suggested_fixes = []
    write_map = file_graph['write_map']
    read_map = file_graph['read_map']
    dependency_edges = file_graph['dependency_edges']

    # Check each phase for parallel safety
    for phase in execution_plan.get('phases', []):
        phase_number = phase.get('phase_number', 0)
        phase_agents = phase.get('agent_names', [])

        if len(phase_agents) <= 1:
            continue  # Single agent phase - no conflicts possible

        # Check 1: Parallel write conflicts within this phase
        for file_path, writers in write_map.items():
            # Find writers that are in this phase
            phase_writers = [w for w in writers if w in phase_agents]

            if len(phase_writers) > 1:
                conflict = {
                    'file': file_path,
                    'agents': phase_writers,
                    'phase': phase_number,
                    'type': 'parallel-write',
                    'severity': 'error',
                    'description': (
                        f"CONFLICT in Phase {phase_number}: Agents "
                        f"{', '.join(phase_writers)} all write to '{file_path}' "
                        f"and are scheduled to run in parallel. This will cause "
                        f"a data race where the last agent to write wins, "
                        f"potentially overwriting work from other agents."
                    )
                }
                conflicts.append(conflict)

                # Generate fix suggestions
                for i, writer in enumerate(phase_writers[1:], 1):
                    suggested_fixes.append({
                        'type': 'add_dependency',
                        'description': (
                            f"Add dependency from '{phase_writers[0]}' to "
                            f"'{writer}' to serialize writes to '{file_path}'"
                        ),
                        'fix': {
                            'action': 'add_dependency',
                            'from': phase_writers[0],
                            'to': writer,
                            'reason': f"Serialize writes to {file_path}"
                        }
                    })

                suggested_fixes.append({
                    'type': 'move_to_different_phase',
                    'description': (
                        f"Move agents to different phases so they write to "
                        f"'{file_path}' sequentially instead of in parallel"
                    ),
                    'fix': {
                        'action': 'separate_phases',
                        'agents': phase_writers,
                        'file': file_path,
                        'reason': f"Avoid parallel writes to {file_path}"
                    }
                })

        # Check 2: Read-after-write conflicts within this phase
        for edge in dependency_edges:
            if not edge.get('explicit', True):
                from_agent = edge['from']
                to_agent = edge['to']

                # Both agents in the same parallel phase?
                if from_agent in phase_agents and to_agent in phase_agents:
                    conflict = {
                        'file': edge['file'],
                        'agents': [from_agent, to_agent],
                        'phase': phase_number,
                        'type': 'read-write-race',
                        'severity': 'warning',
                        'description': (
                            f"WARNING in Phase {phase_number}: Agent "
                            f"'{to_agent}' reads '{edge['file']}' which is "
                            f"written by '{from_agent}'. Both are in the same "
                            f"parallel phase, so '{to_agent}' may read stale "
                            f"data if it starts before '{from_agent}' finishes."
                        )
                    }
                    conflicts.append(conflict)

                    suggested_fixes.append({
                        'type': 'add_dependency',
                        'description': (
                            f"Add dependency from '{from_agent}' to "
                            f"'{to_agent}' so '{to_agent}' waits for "
                            f"'{from_agent}' to finish writing '{edge['file']}'"
                        ),
                        'fix': {
                            'action': 'add_dependency',
                            'from': from_agent,
                            'to': to_agent,
                            'reason': f"Ensure {to_agent} reads updated {edge['file']}"
                        }
                    })

    safe = len([c for c in conflicts if c['severity'] == 'error']) == 0

    return {
        'safe': safe,
        'conflicts': conflicts,
        'suggested_fixes': suggested_fixes
    }
```

---

### Algorithm 3: Normalize and Match Paths

```python
def normalize_path(file_path: str) -> str:
    """
    Normalize a file path for consistent comparison.

    Handles:
    - Forward/backslash normalization
    - Leading ./ removal
    - Trailing slash removal
    - Case normalization (on case-insensitive filesystems)

    Args:
        file_path: Raw file path from agent frontmatter

    Returns:
        Normalized path string
    """
    # Normalize separators to forward slashes
    normalized = file_path.replace('\\', '/')

    # Remove leading ./
    if normalized.startswith('./'):
        normalized = normalized[2:]

    # Remove trailing /
    normalized = normalized.rstrip('/')

    return normalized


def is_glob_pattern(path: str) -> bool:
    """Check if a path contains glob metacharacters."""
    return any(c in path for c in ['*', '?', '{', '['])


def paths_overlap(path_a: str, path_b: str) -> bool:
    """
    Determine if two file paths (possibly with globs) could refer to
    the same file.

    Cases:
    1. Both exact paths: direct string comparison
    2. One or both globs: check if patterns could match overlapping files
    3. Directory containment: src/a.ts is within src/**/*.ts

    Args:
        path_a: First path (may contain globs)
        path_b: Second path (may contain globs)

    Returns:
        True if paths could refer to the same file
    """
    norm_a = normalize_path(path_a)
    norm_b = normalize_path(path_b)

    # Case 1: Exact match
    if norm_a == norm_b:
        return True

    # Case 2: One is a glob, check if the other matches
    if is_glob_pattern(norm_a) and not is_glob_pattern(norm_b):
        return glob_matches(norm_a, norm_b)
    if is_glob_pattern(norm_b) and not is_glob_pattern(norm_a):
        return glob_matches(norm_b, norm_a)

    # Case 3: Both are globs - check for overlap
    if is_glob_pattern(norm_a) and is_glob_pattern(norm_b):
        return globs_could_overlap(norm_a, norm_b)

    return False


def glob_matches(pattern: str, path: str) -> bool:
    """
    Check if a glob pattern could match a specific path.

    Uses simplified glob matching:
    - ** matches any number of path segments
    - * matches any single path segment content
    - ? matches any single character

    Args:
        pattern: Glob pattern (e.g., "src/**/*.ts")
        path: Specific file path (e.g., "src/utils/helper.ts")

    Returns:
        True if pattern matches path
    """
    import fnmatch

    # Handle ** (recursive) by expanding to fnmatch-compatible form
    # fnmatch does not natively support **, so we handle it manually
    pattern_parts = pattern.split('/')
    path_parts = path.split('/')

    return _match_segments(pattern_parts, path_parts, 0, 0)


def _match_segments(pattern_parts: list, path_parts: list, pi: int, pp: int) -> bool:
    """Recursive segment matcher supporting ** glob patterns."""
    if pi == len(pattern_parts) and pp == len(path_parts):
        return True
    if pi == len(pattern_parts):
        return False

    segment = pattern_parts[pi]

    if segment == '**':
        # ** matches zero or more segments
        # Try matching zero segments (skip **)
        if _match_segments(pattern_parts, path_parts, pi + 1, pp):
            return True
        # Try matching one or more segments
        if pp < len(path_parts):
            return _match_segments(pattern_parts, path_parts, pi, pp + 1)
        return False

    if pp >= len(path_parts):
        return False

    # Use fnmatch for single-segment matching (handles * and ?)
    import fnmatch
    if fnmatch.fnmatch(path_parts[pp], segment):
        return _match_segments(pattern_parts, path_parts, pi + 1, pp + 1)

    return False


def globs_could_overlap(pattern_a: str, pattern_b: str) -> bool:
    """
    Heuristic check for whether two glob patterns could match the same file.

    This is a conservative check - it may return True even when no actual
    overlap exists. False positives are acceptable (extra warnings) but
    false negatives are not (missed conflicts).

    Args:
        pattern_a: First glob pattern
        pattern_b: Second glob pattern

    Returns:
        True if patterns could potentially overlap
    """
    # Split into directory and filename components
    dir_a = '/'.join(pattern_a.split('/')[:-1])
    dir_b = '/'.join(pattern_b.split('/')[:-1])
    file_a = pattern_a.split('/')[-1]
    file_b = pattern_b.split('/')[-1]

    # If either directory uses **, they could overlap
    if '**' in dir_a or '**' in dir_b:
        # Check if file patterns could match the same file
        return _file_patterns_compatible(file_a, file_b)

    # If directories are identical, check file patterns
    if dir_a == dir_b:
        return _file_patterns_compatible(file_a, file_b)

    # If one directory is a prefix of the other and uses wildcards
    if dir_a.startswith(dir_b) or dir_b.startswith(dir_a):
        return _file_patterns_compatible(file_a, file_b)

    return False


def _file_patterns_compatible(pat_a: str, pat_b: str) -> bool:
    """Check if two filename patterns could match the same file."""
    # If either is *, they match anything
    if pat_a == '*' or pat_b == '*':
        return True

    # If both have the same extension pattern, they could overlap
    ext_a = pat_a.split('.')[-1] if '.' in pat_a else '*'
    ext_b = pat_b.split('.')[-1] if '.' in pat_b else '*'

    if ext_a == '*' or ext_b == '*' or ext_a == ext_b:
        return True

    return False
```

---

### Algorithm 4: Find Matching Readers

```python
def find_matching_readers(write_path: str, read_map: dict, agent_files: dict) -> list:
    """
    Find all agents that read a file matching the given write path.

    Handles both exact matches and glob pattern matches. A write to
    "src/server.ts" matches a read of "src/**/*.ts".

    Args:
        write_path: File path being written (may be glob)
        read_map: Map of {read_path: [agent_names]}
        agent_files: Map of {agent_name: {reads: set, writes: set}}

    Returns:
        List of agent names that read files matching write_path
    """
    matching_readers = []

    for read_path, readers in read_map.items():
        if paths_overlap(write_path, read_path):
            matching_readers.extend(readers)

    # Deduplicate while preserving order
    seen = set()
    unique_readers = []
    for reader in matching_readers:
        if reader not in seen:
            seen.add(reader)
            unique_readers.append(reader)

    return unique_readers
```

---

### Algorithm 5: Detect Glob Overlaps

```python
def detect_glob_overlaps(write_map: dict, agent_files: dict) -> list:
    """
    Detect potentially overlapping glob patterns in write declarations
    and generate warnings.

    Glob overlap occurs when two agents use glob patterns that could
    expand to the same file, even if neither agent explicitly names
    that file. This is harder to detect than exact-path conflicts
    and warrants a warning.

    Args:
        write_map: Map of {file_path: [agent_names]}
        agent_files: Map of {agent_name: {reads: set, writes: set}}

    Returns:
        List of warning dicts
    """
    warnings = []

    # Collect all glob write patterns with their agents
    glob_writes = []
    for agent_name, files in agent_files.items():
        for write_path in files['writes']:
            if is_glob_pattern(write_path):
                glob_writes.append((agent_name, write_path))

    # Check each pair of glob writes for overlap
    for i in range(len(glob_writes)):
        agent_a, pattern_a = glob_writes[i]
        for j in range(i + 1, len(glob_writes)):
            agent_b, pattern_b = glob_writes[j]

            if agent_a == agent_b:
                continue

            if globs_could_overlap(pattern_a, pattern_b):
                warnings.append({
                    'type': 'glob_overlap',
                    'agents': [agent_a, agent_b],
                    'patterns': [pattern_a, pattern_b],
                    'severity': 'warning',
                    'message': (
                        f"Glob patterns may overlap: Agent '{agent_a}' writes "
                        f"'{pattern_a}' and agent '{agent_b}' writes "
                        f"'{pattern_b}'. These patterns could match the same "
                        f"files. If these agents run in parallel, verify they "
                        f"write to distinct files."
                    ),
                    'suggestion': (
                        f"Consider using more specific file paths instead of "
                        f"globs, or add a dependency between '{agent_a}' and "
                        f"'{agent_b}' to prevent parallel writes."
                    )
                })

    return warnings
```

---

## Display Formatting

### Format Conflict Warnings for Approval Gate

```python
def format_file_conflict_warnings(
    file_dependency_result: dict,
    parallel_safety_result: dict
) -> str:
    """
    Format file conflict detection results for display during the
    approval gate. This output is shown to the user before they
    approve or reject the execution plan.

    Produces a human-readable summary with:
    - File dependency graph overview
    - Conflict details (errors and warnings)
    - Suggested fixes with concrete actions

    Args:
        file_dependency_result: Output from build_file_dependency_graph()
        parallel_safety_result: Output from validate_parallel_safety()

    Returns:
        Formatted string for console display
    """
    lines = []

    # Header
    if not parallel_safety_result['safe']:
        lines.append("## FILE CONFLICT DETECTION: CONFLICTS FOUND")
        lines.append("")
    elif file_dependency_result['warnings']:
        lines.append("## File Conflict Detection: Warnings")
        lines.append("")
    else:
        lines.append("## File Conflict Detection: Clean")
        lines.append("")
        lines.append("No file conflicts detected between agents.")
        return '\n'.join(lines)

    # Implicit dependencies
    implicit_deps = file_dependency_result['implicit_deps']
    if implicit_deps:
        lines.append(f"### Implicit Dependencies Discovered ({len(implicit_deps)})")
        lines.append("")
        for dep in implicit_deps:
            lines.append(f"  {dep['from']} --[writes]--> {dep['file']} --[reads]--> {dep['to']}")
            lines.append(f"    Implication: {dep['to']} should run AFTER {dep['from']}")
        lines.append("")

    # Conflicts (errors)
    errors = [c for c in parallel_safety_result['conflicts'] if c['severity'] == 'error']
    if errors:
        lines.append(f"### CONFLICTS ({len(errors)} errors)")
        lines.append("")
        for conflict in errors:
            lines.append(f"  Phase {conflict['phase']}: {conflict['type'].upper()}")
            lines.append(f"    File: {conflict['file']}")
            lines.append(f"    Agents: {', '.join(conflict['agents'])}")
            lines.append(f"    {conflict['description']}")
            lines.append("")

    # Warnings
    warnings_list = [c for c in parallel_safety_result['conflicts'] if c['severity'] == 'warning']
    warnings_list.extend(file_dependency_result['warnings'])
    if warnings_list:
        lines.append(f"### Warnings ({len(warnings_list)})")
        lines.append("")
        for warning in warnings_list:
            if 'description' in warning:
                lines.append(f"  {warning['description']}")
            elif 'message' in warning:
                lines.append(f"  {warning['message']}")
            lines.append("")

    # Suggested fixes
    if parallel_safety_result['suggested_fixes']:
        lines.append("### Suggested Fixes")
        lines.append("")
        for idx, fix in enumerate(parallel_safety_result['suggested_fixes'], 1):
            lines.append(f"  {idx}. {fix['description']}")

            if fix['fix']['action'] == 'add_dependency':
                lines.append(f"     Fix: Add to team definition dependencies:")
                lines.append(f"       - from: {fix['fix']['from']}")
                lines.append(f"         to: {fix['fix']['to']}")
                lines.append(f"         type: sequential")

            elif fix['fix']['action'] == 'separate_phases':
                agents = fix['fix']['agents']
                lines.append(f"     Fix: Move agents to separate sequential phases:")
                for agent in agents:
                    lines.append(f"       - {agent}")

            lines.append("")

    return '\n'.join(lines)
```

**Example Output (Conflict Detected)**:

```
## FILE CONFLICT DETECTION: CONFLICTS FOUND

### Implicit Dependencies Discovered (1)

  backend --[writes]--> src/server.ts --[reads]--> tests
    Implication: tests should run AFTER backend

### CONFLICTS (1 errors)

  Phase 1: PARALLEL-WRITE
    File: src/shared/utils.ts
    Agents: backend, frontend
    CONFLICT in Phase 1: Agents backend, frontend all write to
    'src/shared/utils.ts' and are scheduled to run in parallel.
    This will cause a data race where the last agent to write wins,
    potentially overwriting work from other agents.

### Suggested Fixes

  1. Add dependency from 'backend' to 'frontend' to serialize writes
     to 'src/shared/utils.ts'
     Fix: Add to team definition dependencies:
       - from: backend
         to: frontend
         type: sequential

  2. Move agents to different phases so they write to
     'src/shared/utils.ts' sequentially instead of in parallel
     Fix: Move agents to separate sequential phases:
       - backend
       - frontend
```

**Example Output (Clean)**:

```
## File Conflict Detection: Clean

No file conflicts detected between agents.
```

---

## Integration with Team Loader

The File Conflict Detector is invoked during the team-loader validation phase (Step 8.5, after circular dependency detection and before limit enforcement).

### Integration Point

```python
def load_team_definition(team_name: str, project_root: str) -> dict:
    """
    Complete workflow to load and validate a team definition.
    (Extended with file conflict detection)
    """
    # ... existing steps 1-8 (required fields, coordinator, agents, cycles, limits) ...

    # Step 8.5: File conflict detection (NEW)
    agents = team_def.get('agents', [])
    dependencies = team_def.get('dependencies', [])

    # Load files_read and files_write from agent definition files
    enriched_agents = enrich_agents_with_file_declarations(agents, project_root)

    # Build file dependency graph
    file_dep_result = build_file_dependency_graph(enriched_agents, dependencies)

    # Add implicit dependencies as warnings
    for implicit_dep in file_dep_result['implicit_deps']:
        warnings.append({
            'field': 'files',
            'type': 'implicit_dependency',
            'message': implicit_dep['reason'],
            'from': implicit_dep['from'],
            'to': implicit_dep['to'],
            'file': implicit_dep['file']
        })

    # Add write-write conflicts as errors
    for conflict in file_dep_result['conflicts']:
        if conflict['severity'] == 'error':
            errors.append({
                'field': 'files_write',
                'reason': conflict['reason'],
                'suggestion': (
                    f"Agents {', '.join(conflict['agents'])} all write to "
                    f"'{conflict['file']}'. Fix by adding explicit dependencies "
                    f"to serialize access, or move agents to different phases.\n\n"
                    f"Option 1: Add dependency in team definition:\n"
                    f"  dependencies:\n"
                    f"    - from: {conflict['agents'][0]}\n"
                    f"      to: {conflict['agents'][1]}\n"
                    f"      type: sequential\n\n"
                    f"Option 2: Restructure agent file targets to avoid overlap."
                )
            })

    # Store file graph for use by plan-visualizer and approval gate
    team_def['_file_dependency_graph'] = file_dep_result

    # ... continue with remaining validation steps ...
```

### Enrich Agents with File Declarations

```python
def enrich_agents_with_file_declarations(agents: list, project_root: str) -> list:
    """
    Load files_read and files_write from agent definition files.

    Agent specs in team definitions reference agent types (e.g.,
    agents/backend-agent.md). This function reads each agent
    definition file and extracts files_read/files_write from
    its YAML frontmatter.

    Args:
        agents: List of agent specs from team definition
        project_root: Absolute path to project root

    Returns:
        List of agent specs enriched with files_read and files_write
    """
    enriched = []

    for agent in agents:
        enriched_agent = dict(agent)

        # If agent spec already has files_read/files_write, keep them
        if 'files_read' in agent or 'files_write' in agent:
            enriched.append(enriched_agent)
            continue

        # Otherwise, try to load from agent definition file
        agent_type = agent.get('type', '')
        agent_path = os.path.join(project_root, agent_type)

        if os.path.exists(agent_path):
            try:
                agent_def = parse_frontmatter(agent_path)
                if agent_def:
                    enriched_agent['files_read'] = agent_def.get('files_read', [])
                    enriched_agent['files_write'] = agent_def.get('files_write', [])
            except Exception:
                # Non-blocking: if we cannot read agent file, skip enrichment
                pass

        enriched.append(enriched_agent)

    return enriched


def parse_frontmatter(file_path: str) -> dict:
    """
    Parse YAML frontmatter from a Markdown file.

    Args:
        file_path: Absolute path to the Markdown file

    Returns:
        dict of frontmatter key-value pairs, or empty dict on failure
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return {}

        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}

        import yaml
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if isinstance(frontmatter, dict) else {}

    except Exception:
        return {}
```

---

## Integration with Approval Gate

During the before_execution approval gate (Phase 3), file conflict detection results are displayed alongside the execution plan.

```python
def request_before_execution_approval(
    coordinator_id: str,
    team_config: dict,
    plan: dict,
    iteration: int
) -> dict:
    """
    Extended approval gate with file conflict warnings.
    """
    # ... existing plan display logic ...

    # Display file conflict results (if available)
    file_graph = team_config.get('_file_dependency_graph')
    if file_graph:
        parallel_safety = validate_parallel_safety(plan, file_graph)
        conflict_display = format_file_conflict_warnings(file_graph, parallel_safety)
        display_to_user(conflict_display)

        # If conflicts exist, highlight in approval prompt
        if not parallel_safety['safe']:
            display_warning(
                "FILE CONFLICTS DETECTED: The execution plan has file "
                "conflicts that may cause data races. Review the conflicts "
                "above and consider rejecting the plan to fix them first."
            )

    # ... continue with approval collection ...
```

---

## Error Handling

### No File Declarations

**Condition**: Agents do not declare `files_read` or `files_write`
**Behavior**: Skip file conflict detection silently. No errors, no warnings. File declarations are optional.

### Unreadable Agent Definition File

**Condition**: Agent type file cannot be read during enrichment
**Behavior**: Skip enrichment for that agent. Log a debug-level message. Continue with remaining agents.

### Malformed File Paths

**Condition**: File path contains invalid characters or is empty
**Behavior**: Normalize as best as possible. If empty after normalization, skip the path.

### Extremely Large File Lists

**Condition**: Agent declares hundreds of file patterns
**Behavior**: Process all patterns but cap glob overlap detection at 100 patterns per agent to prevent O(n^2) explosion. Log a warning if cap is reached.

```python
MAX_GLOB_PATTERNS_PER_AGENT = 100

def validate_file_list_size(files: list, agent_name: str) -> tuple:
    """
    Validate file list size and truncate if necessary.

    Returns:
        (truncated_list, warning_or_none)
    """
    if len(files) <= MAX_GLOB_PATTERNS_PER_AGENT:
        return files, None

    return files[:MAX_GLOB_PATTERNS_PER_AGENT], {
        'type': 'file_list_truncated',
        'agent': agent_name,
        'severity': 'warning',
        'message': (
            f"Agent '{agent_name}' declares {len(files)} file patterns "
            f"(max {MAX_GLOB_PATTERNS_PER_AGENT} for conflict detection). "
            f"Only the first {MAX_GLOB_PATTERNS_PER_AGENT} patterns will "
            f"be checked for conflicts."
        )
    }
```

---

## Testing Checklist

For acceptance:

### Build File Dependency Graph
- [ ] Builds write_map from agent files_write declarations
- [ ] Builds read_map from agent files_read declarations
- [ ] Detects implicit read-after-write dependencies
- [ ] Detects write-write conflicts (multiple writers to same file)
- [ ] Handles agents with no file declarations (empty lists)
- [ ] Handles agents with only files_read (no writes)
- [ ] Handles agents with only files_write (no reads)
- [ ] Distinguishes explicit dependencies from implicit ones
- [ ] Normalizes paths consistently (forward slashes, no leading ./)

### Glob Pattern Matching
- [ ] Matches exact paths (src/index.ts == src/index.ts)
- [ ] Matches single wildcard (src/*.ts matches src/index.ts)
- [ ] Matches recursive wildcard (src/**/*.ts matches src/a/b/c.ts)
- [ ] Matches question mark wildcard (test?.py matches test1.py)
- [ ] Detects overlap between two glob patterns
- [ ] Does not false-negative on overlapping globs (conservative)
- [ ] Handles mixed glob and exact paths

### Validate Parallel Safety
- [ ] Returns safe=true when no parallel write conflicts exist
- [ ] Returns safe=false when parallel write conflicts exist
- [ ] Detects read-write race in same parallel phase
- [ ] Ignores conflicts between agents in different phases (sequential)
- [ ] Single-agent phases always pass (no self-conflict)
- [ ] Generates correct fix suggestions for add_dependency
- [ ] Generates correct fix suggestions for separate_phases

### Integration
- [ ] Enriches agents with files_read/files_write from agent definition files
- [ ] Falls back gracefully when agent definition files are unreadable
- [ ] Integrates with team-loader validation pipeline
- [ ] Displays conflict warnings during approval gate
- [ ] Highlights conflicts prominently when detected
- [ ] Stores file graph in team definition for downstream use

### Edge Cases
- [ ] Handles empty agent list (no agents to check)
- [ ] Handles agents with no dependencies declared
- [ ] Handles duplicate file paths in same agent
- [ ] Handles very large file lists (100+ patterns)
- [ ] Handles Windows-style backslash paths
- [ ] Handles paths with special characters

---

## Example Scenarios

### Scenario 1: Clean Parallel Execution

```yaml
agents:
  - name: backend
    type: agents/backend-agent.md
    files_write: ["src/server.ts", "src/routes/*.ts"]
  - name: frontend
    type: agents/frontend-agent.md
    files_write: ["public/index.html", "public/styles/*.css"]
  - name: tests
    type: agents/test-agent.md
    files_read: ["src/**/*.ts", "public/**/*"]
    dependencies: [backend, frontend]
```

**Result**: Safe. Backend and frontend write to disjoint files. Tests read from both but run after both complete (explicit dependencies).

### Scenario 2: Parallel Write Conflict

```yaml
agents:
  - name: backend
    type: agents/backend-agent.md
    files_write: ["src/shared/utils.ts", "src/server.ts"]
  - name: frontend
    type: agents/frontend-agent.md
    files_write: ["src/shared/utils.ts", "public/index.html"]
```

**Result**: Conflict. Both `backend` and `frontend` write to `src/shared/utils.ts`. If scheduled in the same parallel phase, this is a data race.

### Scenario 3: Implicit Dependency

```yaml
agents:
  - name: setup
    type: agents/setup-agent.md
    files_write: ["config.json", ".env.local"]
  - name: backend
    type: agents/backend-agent.md
    files_read: ["config.json"]
    files_write: ["src/server.ts"]
```

**Result**: Warning. `backend` reads `config.json` which `setup` writes. Implicit dependency: `setup` must complete before `backend` starts. If no explicit dependency is declared and both are in the same phase, this is a read-write race.

### Scenario 4: Glob Pattern Overlap

```yaml
agents:
  - name: backend
    type: agents/backend-agent.md
    files_write: ["src/**/*.ts"]
  - name: frontend
    type: agents/frontend-agent.md
    files_write: ["src/components/**/*.ts"]
```

**Result**: Warning. The glob `src/**/*.ts` overlaps with `src/components/**/*.ts`. If both agents write to files in `src/components/`, there could be a conflict.

---

## References

- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md`
- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-2, REQ-F-16)
- Team Loader: `skills/team-orchestration/team-loader.md` (integration point)
- Approval Gate: `skills/team-orchestration/approval-gate-handler.md` (display point)

---

**Last Updated**: 2026-03-25
**Status**: Implementation (P1 Improvement)
