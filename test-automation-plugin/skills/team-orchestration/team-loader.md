---
name: team-loader
description: Load and validate team definitions from teams/[name].md files, including YAML frontmatter parsing, dependency validation, and circular dependency detection.
user-invocable: false
---

# Team Loader Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Load and validate team definitions from `teams/[team-name].md` files with comprehensive validation

**Used By**: Team Orchestration SKILL, /team-run command

---

## Overview

The Team Loader Skill provides secure loading and validation of team definitions stored as Markdown files with YAML frontmatter. It ensures teams are properly configured before execution by validating required fields, checking file references, detecting circular dependencies, and enforcing resource limits.

This skill is critical for:
- **Safety**: Preventing invalid or malicious team configurations from executing
- **Clarity**: Providing clear error messages when configurations are incorrect
- **Reliability**: Ensuring all referenced coordinators and agents exist before execution

### Key Principle

Team definitions must be **explicitly validated** before execution. Never assume a team definition is valid - validate all fields, references, and dependencies upfront to fail fast with actionable error messages.

---

## Skill Interface

### Input

```yaml
team_name: Name of the team to load (e.g., "testing-parallel", "plugin-architecture")
project_root: Absolute path to the project root directory (team file at {project_root}/teams/{team_name}.md)
```

### Output

```yaml
# Success case
team_definition:
  name: string                          # Team name
  version: string                       # Team definition version (default: "1.0.0")
  coordinator: string                   # Path to coordinator implementation
  max_agents: integer                   # Max parallel agents (1-25)
  timeout_minutes: integer              # Execution timeout (default: 30)
  depth_limit: integer                  # Max nesting depth (1-3, default: 3)
  approval_gates:
    before_execution: boolean           # Pause before spawning agents
    after_completion: boolean           # Pause after completion
    disabled: boolean                   # Skip all gates
  retry_config:
    max_retries: integer                # Max retries per agent (0-3)
    backoff_seconds: [int, int, int]    # Exponential backoff delays
  failure_handling: string              # "continue" or "abort"
  token_budget: integer | null          # Max tokens per team (null = unlimited)
  telemetry_enabled: boolean | null     # Override global telemetry setting
  agents: list                          # Agent composition (optional)
  dependencies: list                    # Dependency graph (optional)

validation_result:
  valid: boolean                        # Overall validity
  errors: list                          # List of validation errors (if invalid)
  warnings: list                        # List of non-critical warnings

# Error case
team_definition: null
validation_result:
  valid: false
  errors:
    - field: string                     # Which field has error
      reason: string                    # Why it's invalid
      suggestion: string                # How to fix it
  warnings: []
```

---

## Team Definition Schema

### File Location

```
{project_root}/teams/{team-name}.md
```

### YAML Frontmatter Structure

```yaml
---
# Required fields
name: string                        # Unique team identifier (must match filename)
coordinator: string                 # Path to coordinator implementation (e.g., teams/testing-parallel-coordinator.md)
max_agents: integer                 # Max parallel agents (range: 1-25)

# Optional fields with defaults
version: string                     # Team definition version (default: "1.0.0")
timeout_minutes: integer            # Execution timeout (default: 30)
depth_limit: integer                # Max nesting depth (default: 3, max: 3)

approval_gates:
  before_execution: boolean         # Pause before spawning agents (default: true)
  after_completion: boolean         # Pause after completion (default: true)
  disabled: boolean                 # Skip all gates (default: false)

retry_config:
  max_retries: integer              # Max retries per agent (default: 3, max: 3)
  backoff_seconds: [int, int, int]  # Exponential backoff delays (default: [1, 2, 4])

failure_handling: string            # "continue" or "abort" (default: "continue")
token_budget: integer               # Max tokens per team (default: null = unlimited)
telemetry_enabled: boolean          # Override global telemetry setting (default: null = inherit)

# Optional: Agent composition (used by some coordinators)
agents:
  - name: string                    # Agent identifier
    type: string                    # Agent type (path to agent definition in agents/)
    critical: boolean               # Failure aborts team? (default: false)
    dependencies: [string]          # Agent names this agent depends on
    max_instances: integer          # Max parallel instances (default: 1)

# Optional: Explicit dependency graph
dependencies:
  - from: string                    # Agent name
    to: string                      # Agent name
    type: string                    # "sequential" or "parallel"
---

# Team Description (Markdown prose)

Detailed explanation of team purpose, workflow, and coordination logic.
```

---

## Validation Rules

### Rule 1: Required Fields Present (REQ-F-15)

**Fields**:
- `name` (string)
- `coordinator` (string)
- `max_agents` (integer)

**Validation**:
```python
def validate_required_fields(frontmatter: dict) -> list:
    """Validate required fields are present and non-empty."""
    errors = []
    required = ['name', 'coordinator', 'max_agents']

    for field in required:
        if field not in frontmatter:
            errors.append({
                'field': field,
                'reason': f"Required field '{field}' is missing",
                'suggestion': f"Add '{field}' to the YAML frontmatter"
            })
        elif frontmatter[field] is None or (isinstance(frontmatter[field], str) and not frontmatter[field].strip()):
            errors.append({
                'field': field,
                'reason': f"Required field '{field}' is empty",
                'suggestion': f"Provide a value for '{field}'"
            })

    return errors
```

**Example Error**:
```
Field: coordinator
Reason: Required field 'coordinator' is missing
Suggestion: Add 'coordinator' to the YAML frontmatter

Example:
coordinator: teams/testing-parallel-coordinator.md
```

---

### Rule 2: Coordinator File Exists (REQ-F-16)

**Validation**:
```python
def validate_coordinator_exists(coordinator_path: str, project_root: str) -> dict:
    """
    Validate coordinator file exists.

    The coordinator path is resolved relative to project_root, NOT relative to
    the team definition file. This allows teams to reference coordinators
    consistently regardless of team file location.

    Args:
        coordinator_path: Path from team definition (e.g., "teams/testing-parallel-coordinator.md")
        project_root: Absolute path to project root

    Returns:
        dict with 'valid' boolean and optional 'error' dict
    """
    # Resolve path relative to project root
    full_path = os.path.join(project_root, coordinator_path)

    if not os.path.exists(full_path):
        # Try common locations if not found
        alternative_paths = [
            os.path.join(project_root, 'teams', os.path.basename(coordinator_path)),
            os.path.join(project_root, 'teams', os.path.basename(coordinator_path)),
        ]

        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                return {
                    'valid': True,
                    'warning': {
                        'field': 'coordinator',
                        'reason': f"Coordinator path '{coordinator_path}' not found, using '{alt_path}'",
                        'suggestion': f"Update frontmatter to: coordinator: {os.path.relpath(alt_path, project_root)}"
                    }
                }

        return {
            'valid': False,
            'error': {
                'field': 'coordinator',
                'reason': f"Coordinator file does not exist: {coordinator_path}",
                'suggestion': (
                    f"Coordinator file not found at: {full_path}\n\n"
                    f"How to fix:\n"
                    f"1. Create the coordinator file:\n"
                    f"   - Path: {full_path}\n"
                    f"   - See existing coordinators in teams/ directory for examples\n\n"
                    f"2. Or update the path in team definition:\n"
                    f"   coordinator: path/to/existing/coordinator.md\n\n"
                    f"Checked locations:\n"
                    f"  - {full_path}\n" +
                    "\n".join(f"  - {p}" for p in alternative_paths)
                )
            }
        }

    return {'valid': True}
```

**Example Error**:
```
Field: coordinator
Reason: Coordinator file does not exist: teams/testing-parallel-coordinator.md
Suggestion: Coordinator file not found at: /path/to/project/teams/testing-parallel-coordinator.md

How to fix:
1. Create the coordinator file:
   - Path: /path/to/project/teams/testing-parallel-coordinator.md
   - See existing coordinators in teams/ directory for examples

2. Or update the path in team definition:
   coordinator: path/to/existing/coordinator.md

Checked locations:
  - /path/to/project/teams/testing-parallel-coordinator.md
  - /path/to/project/teams/testing-parallel-coordinator.md
  - /path/to/project/teams/testing-parallel-coordinator.md
```

---

### Rule 3: Agent References Valid (REQ-F-16)

**Validation**:
```python
def validate_agent_references(agents: list, project_root: str) -> list:
    """
    Validate agent type references exist in agents/ directory.

    Args:
        agents: List of agent specs from frontmatter
        project_root: Absolute path to project root

    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []

    if not agents:
        return errors  # No agents defined, not an error

    for idx, agent in enumerate(agents):
        # Validate agent spec structure
        if 'name' not in agent:
            errors.append({
                'field': f'agents[{idx}]',
                'reason': "Agent spec missing 'name' field",
                'suggestion': "Each agent must have a 'name' field"
            })
            continue

        if 'type' not in agent:
            errors.append({
                'field': f'agents[{idx}].type',
                'reason': f"Agent '{agent['name']}' missing 'type' field",
                'suggestion': f"Add 'type' field with path to agent definition (e.g., agents/write-agent.md)"
            })
            continue

        agent_type = agent['type']
        agent_name = agent['name']

        # Resolve agent path relative to project root
        agent_path = os.path.join(project_root, agent_type)

        if not os.path.exists(agent_path):
            # Try common locations
            alternative_paths = [
                os.path.join(project_root, 'agents', os.path.basename(agent_type)),
                os.path.join(project_root, '.claude', 'agents', os.path.basename(agent_type)),
            ]

            found = False
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    found = True
                    errors.append({
                        'field': f'agents[{idx}].type',
                        'reason': f"Agent type path '{agent_type}' not found, but found at '{alt_path}'",
                        'suggestion': f"Update agent type to: {os.path.relpath(alt_path, project_root)}",
                        'warning': True  # Non-critical, alternative found
                    })
                    break

            if not found:
                errors.append({
                    'field': f'agents[{idx}].type',
                    'reason': f"Agent type file does not exist: {agent_type} (for agent '{agent_name}')",
                    'suggestion': (
                        f"Agent file not found at: {agent_path}\n\n"
                        f"How to fix:\n"
                        f"1. Create the agent file:\n"
                        f"   - Path: {agent_path}\n"
                        f"   - See existing agents in agents/ directory for examples\n\n"
                        f"2. Or update the type in team definition:\n"
                        f"   agents:\n"
                        f"     - name: {agent_name}\n"
                        f"       type: path/to/existing/agent.md\n\n"
                        f"Checked locations:\n"
                        f"  - {agent_path}\n" +
                        "\n".join(f"  - {p}" for p in alternative_paths)
                    )
                })

    return errors
```

**Example Error**:
```
Field: agents[1].type
Reason: Agent type file does not exist: agents/write-agent.md (for agent 'write-agent-1')
Suggestion: Agent file not found at: /path/to/project/agents/write-agent.md

How to fix:
1. Create the agent file:
   - Path: /path/to/project/agents/write-agent.md
   - See existing agents in agents/ directory for examples

2. Or update the type in team definition:
   agents:
     - name: write-agent-1
       type: path/to/existing/agent.md

Checked locations:
  - /path/to/project/agents/write-agent.md
  - /path/to/project/agents/write-agent.md
  - /path/to/project/.claude/agents/write-agent.md
```

---

### Rule 4: No Circular Dependencies (REQ-F-16)

**Algorithm**: Depth-First Search (DFS) cycle detection

```python
def validate_no_circular_dependencies(agents: list, dependencies: list) -> list:
    """
    Detect circular dependencies in agent dependency graph using DFS.

    Args:
        agents: List of agent specs from frontmatter
        dependencies: Explicit dependency list (optional)

    Returns:
        List of validation errors (empty if no cycles)
    """
    errors = []

    # Build dependency graph from both sources
    graph = {}  # {agent_name: [dependent_agent_names]}

    # Extract agent names
    agent_names = set()
    if agents:
        for agent in agents:
            if 'name' in agent:
                agent_names.add(agent['name'])
                graph[agent['name']] = []

    # Add dependencies from agent specs
    if agents:
        for agent in agents:
            if 'name' in agent and 'dependencies' in agent:
                agent_name = agent['name']
                for dep in agent['dependencies']:
                    if dep not in graph:
                        graph[dep] = []
                    # agent depends on dep, so dep -> agent edge
                    graph[dep].append(agent_name)

    # Add explicit dependencies
    if dependencies:
        for dep in dependencies:
            if 'from' in dep and 'to' in dep:
                from_agent = dep['from']
                to_agent = dep['to']

                if from_agent not in graph:
                    graph[from_agent] = []
                if to_agent not in graph:
                    graph[to_agent] = []

                # from -> to edge
                graph[from_agent].append(to_agent)

    # DFS cycle detection
    visited = set()
    rec_stack = set()  # Recursion stack for current path

    def has_cycle(node: str, path: list) -> tuple:
        """
        DFS to detect cycles.

        Returns:
            (has_cycle: bool, cycle_path: list)
        """
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle_found, cycle_path = has_cycle(neighbor, path[:])
                if cycle_found:
                    return True, cycle_path
            elif neighbor in rec_stack:
                # Found cycle - build cycle path
                cycle_start_idx = path.index(neighbor)
                cycle = path[cycle_start_idx:] + [neighbor]
                return True, cycle

        rec_stack.remove(node)
        return False, []

    # Check all nodes
    for node in graph:
        if node not in visited:
            cycle_found, cycle_path = has_cycle(node, [])
            if cycle_found:
                cycle_str = " -> ".join(cycle_path)
                errors.append({
                    'field': 'dependencies',
                    'reason': f"Circular dependency detected: {cycle_str}",
                    'suggestion': (
                        f"Circular dependency found in agent workflow:\n"
                        f"  {cycle_str}\n\n"
                        f"How to fix:\n"
                        f"1. Review the dependency chain above\n"
                        f"2. Remove one dependency to break the cycle\n"
                        f"3. Reorganize workflow to be acyclic (DAG)\n\n"
                        f"Example:\n"
                        f"  If A -> B -> C -> A, change to:\n"
                        f"    Option 1: A -> B -> C (remove C -> A)\n"
                        f"    Option 2: A -> B, A -> C (parallel execution)\n\n"
                        f"Dependencies must form a Directed Acyclic Graph (DAG)."
                    )
                })
                break  # Report first cycle found

    return errors
```

**Example Error**:
```
Field: dependencies
Reason: Circular dependency detected: analyze-agent -> write-agent -> validate-agent -> analyze-agent
Suggestion: Circular dependency found in agent workflow:
  analyze-agent -> write-agent -> validate-agent -> analyze-agent

How to fix:
1. Review the dependency chain above
2. Remove one dependency to break the cycle
3. Reorganize workflow to be acyclic (DAG)

Example:
  If A -> B -> C -> A, change to:
    Option 1: A -> B -> C (remove C -> A)
    Option 2: A -> B, A -> C (parallel execution)

Dependencies must form a Directed Acyclic Graph (DAG).
```

---

### Rule 5: Enforce Limits (REQ-F-16)

**Limits**:
- `depth_limit` ≤ 3
- `max_agents` ≤ 25
- `retry_config.max_retries` ≤ 3

```python
def validate_limits(frontmatter: dict) -> list:
    """Validate numeric limits are within allowed ranges."""
    errors = []

    # Validate depth_limit
    if 'depth_limit' in frontmatter:
        depth_limit = frontmatter['depth_limit']
        if not isinstance(depth_limit, int):
            errors.append({
                'field': 'depth_limit',
                'reason': f"depth_limit must be an integer, got {type(depth_limit).__name__}",
                'suggestion': "Set depth_limit to an integer between 1 and 3"
            })
        elif depth_limit < 1:
            errors.append({
                'field': 'depth_limit',
                'reason': f"depth_limit must be at least 1, got {depth_limit}",
                'suggestion': "Set depth_limit to 1, 2, or 3"
            })
        elif depth_limit > 3:
            errors.append({
                'field': 'depth_limit',
                'reason': f"depth_limit cannot exceed 3, got {depth_limit}",
                'suggestion': (
                    f"Set depth_limit to 3 or less (framework safety limit).\n\n"
                    f"Why: Depth limit prevents infinite recursion and bounds resource usage.\n"
                    f"Max hierarchy: command -> coordinator -> agents (3 levels)"
                )
            })

    # Validate max_agents
    if 'max_agents' in frontmatter:
        max_agents = frontmatter['max_agents']
        if not isinstance(max_agents, int):
            errors.append({
                'field': 'max_agents',
                'reason': f"max_agents must be an integer, got {type(max_agents).__name__}",
                'suggestion': "Set max_agents to an integer between 1 and 25"
            })
        elif max_agents < 1:
            errors.append({
                'field': 'max_agents',
                'reason': f"max_agents must be at least 1, got {max_agents}",
                'suggestion': "Set max_agents to a positive integer (recommended: 5)"
            })
        elif max_agents > 25:
            errors.append({
                'field': 'max_agents',
                'reason': f"max_agents cannot exceed 25, got {max_agents}",
                'suggestion': (
                    f"Set max_agents to 25 or less (framework scalability limit).\n\n"
                    f"Why: The framework is tested up to 25 concurrent agents (5 teams × 5 agents).\n"
                    f"Exceeding this may cause performance degradation."
                )
            })

    # Validate retry_config.max_retries
    if 'retry_config' in frontmatter and isinstance(frontmatter['retry_config'], dict):
        retry_config = frontmatter['retry_config']
        if 'max_retries' in retry_config:
            max_retries = retry_config['max_retries']
            if not isinstance(max_retries, int):
                errors.append({
                    'field': 'retry_config.max_retries',
                    'reason': f"max_retries must be an integer, got {type(max_retries).__name__}",
                    'suggestion': "Set max_retries to an integer between 0 and 3"
                })
            elif max_retries < 0:
                errors.append({
                    'field': 'retry_config.max_retries',
                    'reason': f"max_retries cannot be negative, got {max_retries}",
                    'suggestion': "Set max_retries to 0 (no retries) or higher"
                })
            elif max_retries > 3:
                errors.append({
                    'field': 'retry_config.max_retries',
                    'reason': f"max_retries cannot exceed 3, got {max_retries}",
                    'suggestion': (
                        f"Set max_retries to 3 or less (framework limit).\n\n"
                        f"Why: Excessive retries can cause long execution times.\n"
                        f"3 retries with exponential backoff is typically sufficient."
                    )
                })

    return errors
```

**Example Error**:
```
Field: max_agents
Reason: max_agents cannot exceed 25, got 50
Suggestion: Set max_agents to 25 or less (framework scalability limit).

Why: The framework is tested up to 25 concurrent agents (5 teams × 5 agents).
Exceeding this may cause performance degradation.
```

---

### Rule 6: Name Matches Filename

**Validation**:
```python
def validate_name_matches_filename(team_name: str, frontmatter_name: str) -> dict:
    """
    Validate team name in frontmatter matches filename.

    Args:
        team_name: Team name from filename (e.g., "testing-parallel" from testing-parallel.md)
        frontmatter_name: Team name from frontmatter['name']

    Returns:
        dict with optional error
    """
    if team_name != frontmatter_name:
        return {
            'valid': False,
            'error': {
                'field': 'name',
                'reason': f"Team name '{frontmatter_name}' does not match filename '{team_name}.md'",
                'suggestion': (
                    f"Team name must match filename for consistency.\n\n"
                    f"Option 1: Update frontmatter to match filename:\n"
                    f"  name: {team_name}\n\n"
                    f"Option 2: Rename file to match frontmatter:\n"
                    f"  mv teams/{team_name}.md teams/{frontmatter_name}.md"
                )
            }
        }

    return {'valid': True}
```

---

## Loading Algorithm

### Step 1: Resolve Team File Path

```python
def resolve_team_file(team_name: str, project_root: str) -> dict:
    """
    Resolve team definition file path.

    Args:
        team_name: Team name (e.g., "testing-parallel")
        project_root: Absolute path to project root

    Returns:
        dict with 'path' or 'error'
    """
    team_file = f"{team_name}.md"
    primary_path = os.path.join(project_root, 'teams', team_file)

    # Check primary location
    if os.path.exists(primary_path):
        return {'path': primary_path}

    # Try alternative locations
    alternative_paths = [
        os.path.join(project_root, '.claude', 'teams', team_file),
        os.path.join(project_root, '.claude', team_file),
    ]

    for alt_path in alternative_paths:
        if os.path.exists(alt_path):
            return {
                'path': alt_path,
                'warning': f"Team file found at non-standard location: {alt_path}"
            }

    return {
        'error': {
            'field': 'team_name',
            'reason': f"Team definition file not found: {team_file}",
            'suggestion': (
                f"Team file not found at expected location:\n"
                f"  {primary_path}\n\n"
                f"How to fix:\n"
                f"1. Create the team definition file:\n"
                f"   - Create directory: mkdir -p {os.path.dirname(primary_path)}\n"
                f"   - Create file: touch {primary_path}\n"
                f"   - Add YAML frontmatter with required fields\n\n"
                f"2. Or check for typos in team name:\n"
                f"   - Requested: {team_name}\n"
                f"   - Available teams: ls {os.path.dirname(primary_path)}\n\n"
                f"Checked locations:\n"
                f"  - {primary_path}\n" +
                "\n".join(f"  - {p}" for p in alternative_paths)
            )
        }
    }
```

---

### Step 2: Parse Markdown File

```python
def parse_team_file(file_path: str) -> dict:
    """
    Parse team definition Markdown file with YAML frontmatter.

    Args:
        file_path: Absolute path to team definition file

    Returns:
        dict with 'frontmatter' and 'body', or 'error'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        return {
            'error': {
                'field': 'file',
                'reason': f"Cannot read team file: {e}",
                'suggestion': f"Check file permissions for: {file_path}"
            }
        }

    # Check for YAML frontmatter (starts with ---)
    if not content.startswith('---'):
        return {
            'error': {
                'field': 'frontmatter',
                'reason': "Team file missing YAML frontmatter",
                'suggestion': (
                    f"Team files must start with YAML frontmatter:\n\n"
                    f"---\n"
                    f"name: team-name\n"
                    f"coordinator: teams/coordinator.md\n"
                    f"max_agents: 5\n"
                    f"---\n\n"
                    f"# Team Description\n"
                    f"...\n"
                )
            }
        }

    # Split frontmatter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {
            'error': {
                'field': 'frontmatter',
                'reason': "Invalid YAML frontmatter format",
                'suggestion': (
                    f"Frontmatter must be enclosed by '---' markers:\n\n"
                    f"---\n"
                    f"name: team-name\n"
                    f"...\n"
                    f"---\n"
                )
            }
        }

    frontmatter_str = parts[1]
    body = parts[2].strip()

    # Parse YAML
    try:
        import yaml
        frontmatter = yaml.safe_load(frontmatter_str)

        if not isinstance(frontmatter, dict):
            return {
                'error': {
                    'field': 'frontmatter',
                    'reason': "YAML frontmatter must be a dictionary",
                    'suggestion': "Use key-value pairs in frontmatter (name: value)"
                }
            }

        return {
            'frontmatter': frontmatter,
            'body': body
        }

    except yaml.YAMLError as e:
        return {
            'error': {
                'field': 'frontmatter',
                'reason': f"Invalid YAML syntax: {e}",
                'suggestion': (
                    f"Fix YAML syntax errors in frontmatter.\n\n"
                    f"Common issues:\n"
                    f"  - Incorrect indentation (use 2 spaces, not tabs)\n"
                    f"  - Missing colons after keys\n"
                    f"  - Unquoted strings with special characters\n\n"
                    f"Error details: {e}"
                )
            }
        }
```

---

### Step 3: Apply Defaults

```python
def apply_defaults(frontmatter: dict) -> dict:
    """
    Apply default values for optional fields.

    Args:
        frontmatter: Parsed YAML frontmatter

    Returns:
        Frontmatter with defaults applied
    """
    defaults = {
        'version': '1.0.0',
        'timeout_minutes': 30,
        'depth_limit': 3,
        'approval_gates': {
            'before_execution': True,
            'after_completion': True,
            'disabled': False
        },
        'retry_config': {
            'max_retries': 3,
            'backoff_seconds': [1, 2, 4]
        },
        'failure_handling': 'continue',
        'token_budget': None,
        'telemetry_enabled': None,
        'agents': [],
        'dependencies': []
    }

    # Merge defaults with provided values
    result = defaults.copy()
    result.update(frontmatter)

    # Handle nested defaults for approval_gates
    if 'approval_gates' in frontmatter:
        approval_gates = defaults['approval_gates'].copy()
        approval_gates.update(frontmatter['approval_gates'])
        result['approval_gates'] = approval_gates

    # Handle nested defaults for retry_config
    if 'retry_config' in frontmatter:
        retry_config = defaults['retry_config'].copy()
        retry_config.update(frontmatter['retry_config'])
        result['retry_config'] = retry_config

    return result
```

---

## Complete Loading Workflow

```python
def load_team_definition(team_name: str, project_root: str) -> dict:
    """
    Complete workflow to load and validate a team definition.

    Args:
        team_name: Team name to load
        project_root: Absolute path to project root

    Returns:
        dict with team_definition and validation_result
    """
    errors = []
    warnings = []

    # Step 1: Resolve team file path
    file_result = resolve_team_file(team_name, project_root)
    if 'error' in file_result:
        return {
            'team_definition': None,
            'validation_result': {
                'valid': False,
                'errors': [file_result['error']],
                'warnings': []
            }
        }

    team_file_path = file_result['path']
    if 'warning' in file_result:
        warnings.append({'field': 'file', 'message': file_result['warning']})

    # Step 2: Parse file
    parse_result = parse_team_file(team_file_path)
    if 'error' in parse_result:
        return {
            'team_definition': None,
            'validation_result': {
                'valid': False,
                'errors': [parse_result['error']],
                'warnings': warnings
            }
        }

    frontmatter = parse_result['frontmatter']

    # Step 3: Validate required fields
    errors.extend(validate_required_fields(frontmatter))

    if errors:
        # Can't continue validation without required fields
        return {
            'team_definition': None,
            'validation_result': {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        }

    # Step 4: Apply defaults
    team_def = apply_defaults(frontmatter)

    # Step 5: Validate name matches filename
    name_result = validate_name_matches_filename(team_name, team_def['name'])
    if not name_result['valid']:
        errors.append(name_result['error'])

    # Step 6: Validate coordinator exists
    coord_result = validate_coordinator_exists(team_def['coordinator'], project_root)
    if not coord_result['valid']:
        errors.append(coord_result['error'])
    elif 'warning' in coord_result:
        warnings.append(coord_result['warning'])

    # Step 7: Validate agent references
    agent_errors = validate_agent_references(team_def.get('agents', []), project_root)
    errors.extend([e for e in agent_errors if not e.get('warning', False)])
    warnings.extend([e for e in agent_errors if e.get('warning', False)])

    # Step 8: Validate no circular dependencies
    dep_errors = validate_no_circular_dependencies(
        team_def.get('agents', []),
        team_def.get('dependencies', [])
    )
    errors.extend(dep_errors)

    # Step 9: Validate limits
    limit_errors = validate_limits(team_def)
    errors.extend(limit_errors)

    # Return result
    if errors:
        return {
            'team_definition': None,
            'validation_result': {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        }

    return {
        'team_definition': team_def,
        'validation_result': {
            'valid': True,
            'errors': [],
            'warnings': warnings
        }
    }
```

---

## Error Handling

### Missing File

**Error Message**:
```
Field: team_name
Reason: Team definition file not found: testing-parallel.md
Suggestion: Team file not found at expected location:
  /path/to/project/teams/testing-parallel.md

How to fix:
1. Create the team definition file:
   - Create directory: mkdir -p /path/to/project/teams
   - Create file: touch /path/to/project/teams/testing-parallel.md
   - Add YAML frontmatter with required fields

2. Or check for typos in team name:
   - Requested: testing-parallel
   - Available teams: ls /path/to/project/teams

Checked locations:
  - /path/to/project/teams/testing-parallel.md
  - /path/to/project/.claude/teams/testing-parallel.md
  - /path/to/project/.claude/testing-parallel.md
```

### Invalid YAML

**Error Message**:
```
Field: frontmatter
Reason: Invalid YAML syntax: mapping values are not allowed here
Suggestion: Fix YAML syntax errors in frontmatter.

Common issues:
  - Incorrect indentation (use 2 spaces, not tabs)
  - Missing colons after keys
  - Unquoted strings with special characters

Error details: mapping values are not allowed here
  in "<unicode string>", line 5, column 15:
    approval_gates before_execution: true
                   ^
```

### Graceful Handling

All validation errors are collected and returned together, not failing on first error. This provides comprehensive feedback to users in a single pass.

---

## Usage in Orchestrator

```markdown
# In skills/team-orchestration/SKILL.md

## Phase 1: Load Team Definition

1. Read this skill: skills/team-orchestration/team-loader.md
2. Call load_team_definition(team_name, project_root)
3. Check validation_result.valid:
   - If False: Display errors and abort
   - If True: Proceed with team_definition
4. Display warnings (if any) to user
5. Continue with orchestration workflow
```

---

## Testing Checklist

For TASK-001 acceptance:

- [ ] Loads valid team definition successfully
- [ ] Validates required fields (name, coordinator, max_agents)
- [ ] Returns error for missing required fields
- [ ] Validates coordinator file exists
- [ ] Returns error for non-existent coordinator
- [ ] Validates agent references exist in agents/ directory
- [ ] Returns error for non-existent agent types
- [ ] Detects circular dependencies in agent workflow
- [ ] Returns error for circular dependency with cycle path
- [ ] Enforces depth_limit ≤ 3
- [ ] Returns error for depth_limit > 3
- [ ] Enforces max_agents ≤ 25
- [ ] Returns error for max_agents > 25
- [ ] Enforces max_retries ≤ 3
- [ ] Returns error for max_retries > 3
- [ ] Handles missing file gracefully
- [ ] Handles invalid YAML gracefully
- [ ] Handles malformed frontmatter gracefully
- [ ] Applies default values for optional fields
- [ ] Validates name matches filename
- [ ] Returns all errors in single pass (not fail-fast)
- [ ] Provides clear, actionable error messages

---

## Example Team Definition

```markdown
---
name: testing-parallel
version: 1.0.0
coordinator: teams/testing-parallel-coordinator.md
max_agents: 5
timeout_minutes: 30
depth_limit: 2
approval_gates:
  before_execution: true
  after_completion: false
retry_config:
  max_retries: 3
  backoff_seconds: [1, 2, 4]
failure_handling: continue
agents:
  - name: analyze-agent
    type: agents/analyze-agent.md
    critical: true
  - name: write-agent
    type: agents/write-agent.md
    critical: false
    max_instances: 5
  - name: execute-agent
    type: agents/execute-agent.md
    critical: true
dependencies:
  - from: analyze-agent
    to: write-agent
    type: sequential
  - from: write-agent
    to: execute-agent
    type: sequential
---

# Testing Team (Parallelized)

Parallelizes test generation across independent modules using multiple write-agents.

## Workflow

1. Analyze phase: Single analyze-agent identifies test targets
2. Write phase: Multiple write-agents (1-5) generate tests in parallel
3. Execute phase: Single execute-agent runs all tests

## Coordinator Logic

See teams/testing-parallel-coordinator.md for implementation details.
```

---

## References

- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Team Definition Schema)
- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-12, REQ-F-15, REQ-F-16)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-001)
