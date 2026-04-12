---
name: agent-schema
description: Define and validate the canonical agent definition format that all agent .md files must follow, including frontmatter schema, template resolution, parameter substitution, and validation algorithm.
user-invocable: false
---

# Agent Schema Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Define the canonical agent definition format and provide validation for all agent `.md` files in the `agents/` directory

**Used By**: Team Loader (`skills/team-orchestration/team-loader.md`), Agent Lifecycle Manager (`skills/team-orchestration/agent-lifecycle-manager.md`), Team Coordinators

---

## Overview

The Agent Schema Skill defines the canonical format that all agent definition files (`agents/*.md`) must follow. It provides:

1. **Schema Definition**: Required and optional YAML frontmatter fields with types and constraints
2. **Validation Algorithm**: Comprehensive validation with clear error messages for missing or invalid fields
3. **Template Resolution**: How `extends` inheritance is resolved at load time (P1 feature)
4. **Parameter Substitution**: How `{{param_name}}` syntax is replaced with concrete values (P1 feature)
5. **Output Schema Enforcement**: How agent outputs are validated against declared schemas (P2 feature)

Agent definitions are Markdown files with YAML frontmatter. The frontmatter declares the agent's capabilities, constraints, and configuration. The Markdown body provides the agent's instructions (system prompt) that the coordinator injects when spawning the agent via the Agent tool.

### Key Principles

1. **Fail Fast**: Validate agent definitions completely before spawning any agents
2. **Explicit Declarations**: Agents must declare what they read, write, and require
3. **Backward Compatible**: New optional fields never break existing agent definitions
4. **Template Reuse**: Common agent patterns can be captured in templates via `extends` (P1)
5. **Schema Enforcement**: Agent output structure can be validated at completion (P2)

---

## Skill Interface

### Input

```yaml
agent_path: string             # Path to agent definition file (e.g., "agents/write-agent.md")
project_root: string           # Absolute path to project root
params: dict | null            # Parameter values for template substitution (optional)
```

### Output

```yaml
# Success case
agent_definition:
  name: string                 # Unique agent identifier
  description: string          # One-line description
  model: string                # Default model (opus|sonnet|haiku)
  version: string              # Agent definition version
  subagent_type: string        # Claude Code subagent type
  tools: list[string]          # Allowed tools
  files_read: list[string]     # Files this agent reads
  files_write: list[string]    # Files this agent creates/modifies
  timeout_seconds: integer     # Per-agent timeout
  critical: boolean            # If true, failure aborts team
  max_instances: integer       # Max parallel instances
  extends: string | null       # Template path (P1)
  verify_dependencies: list    # Pre-spawn checks (P1)
  output_schema: dict | null   # Expected output structure (P2)
  params: dict | null          # Template parameter definitions (P1)
  body: string                 # Markdown body (agent instructions)

validation_result:
  valid: boolean
  errors: list[dict]           # Validation errors
  warnings: list[dict]         # Non-critical warnings

# Error case
agent_definition: null
validation_result:
  valid: false
  errors: list[dict]
  warnings: list[dict]
```

---

## Agent Definition File Format

### File Location

```
{project_root}/agents/{agent-name}.md
```

### Complete YAML Frontmatter Schema

```yaml
---
# ===========================================================================
# REQUIRED FIELDS
# ===========================================================================

name: string
  # Unique identifier for this agent.
  # Convention: lowercase-kebab-case (e.g., "write-agent", "analyze-agent")
  # Must match the filename (e.g., agents/write-agent.md -> name: write-agent)
  # Constraints: non-empty string, matches /^[a-z0-9][a-z0-9-]*[a-z0-9]$/

description: string
  # One-line description of what this agent does.
  # Used in plan presentations, telemetry logs, and approval gate displays.
  # Constraints: non-empty string, max 200 characters

model: opus | sonnet | haiku
  # Default model to use when spawning this agent.
  # Can be overridden by team definition or CLI flags.
  # - opus: Highest capability, used for complex analysis and coordination
  # - sonnet: Balanced capability, used for most writing and generation tasks
  # - haiku: Fast and efficient, used for simple tasks and validation
  # Constraints: must be one of "opus", "sonnet", "haiku"

# ===========================================================================
# OPTIONAL FIELDS (with defaults)
# ===========================================================================

version: string
  # Agent definition version. Follows semantic versioning.
  # Default: "1.0.0"

subagent_type: string
  # Claude Code subagent type for the Agent tool.
  # Controls what tools and capabilities the subagent has.
  # Values: "general-purpose" (default), "Explore", "Read", "Write", "Edit"
  # Default: "general-purpose"

tools: list[string]
  # List of tools this agent is allowed to use.
  # When specified, the agent is restricted to only these tools.
  # When omitted, the agent inherits the default toolset for its subagent_type.
  # Example: ["Read", "Write", "Bash", "Grep", "Glob"]
  # Default: null (inherit from subagent_type)

files_read: list[string]
  # Files this agent expects to read during execution.
  # Used for dependency validation and conflict detection.
  # Supports glob patterns: "src/**/*.ts", "tests/*.test.js"
  # Default: [] (no declared read dependencies)

files_write: list[string]
  # Files this agent will create or modify.
  # Used for conflict detection between parallel agents.
  # Two agents writing the same file cannot run in parallel.
  # Supports glob patterns: "tests/**/*.test.ts"
  # Default: [] (no declared write targets)

timeout_seconds: integer
  # Per-agent timeout override.
  # If the agent does not complete within this time, it is marked as failed.
  # Overrides the team-level timeout for this specific agent.
  # Range: 30 to 3600 (30 seconds to 1 hour)
  # Default: null (use team timeout)

critical: boolean
  # If true, this agent's failure aborts the entire team execution,
  # regardless of the team's failure_handling setting.
  # Use for agents whose output is required by downstream agents.
  # Default: false

max_instances: integer
  # Maximum parallel instances of this agent.
  # The coordinator may spawn up to this many copies for batch processing.
  # Each instance receives a different subset of work (e.g., different file batch).
  # Range: 1 to 10
  # Default: 1

# ===========================================================================
# P1 FEATURES (Template System)
# ===========================================================================

extends: string
  # Path to a template agent definition to inherit from.
  # The current agent inherits all fields from the template,
  # then overrides with its own field values.
  # Example: extends: agents/templates/writer-template.md
  # Default: null (no template inheritance)

verify_dependencies: list[object]
  # Pre-spawn verification checks.
  # Before spawning this agent, the coordinator runs these checks
  # and aborts if any fail.
  # Each check is an object with:
  #   - type: "file_exists" | "command_succeeds" | "env_var_set"
  #   - target: string (file path, command, or env var name)
  #   - message: string (error message if check fails)
  # Default: [] (no pre-spawn checks)
  # Example:
  #   verify_dependencies:
  #     - type: file_exists
  #       target: src/index.ts
  #       message: "Source file must exist before test generation"
  #     - type: command_succeeds
  #       target: "npm test -- --version"
  #       message: "Test runner must be installed"

params: object
  # Template variable definitions for parameter substitution.
  # When an agent definition uses {{param_name}} syntax in its body,
  # these define the expected parameters and their defaults.
  # Each key is a parameter name, value is an object with:
  #   - type: "string" | "integer" | "boolean" | "list"
  #   - default: any (default value if not provided)
  #   - required: boolean (if true, must be provided at spawn time)
  #   - description: string (what this parameter controls)
  # Default: null (no template parameters)
  # Example:
  #   params:
  #     target_path:
  #       type: string
  #       required: true
  #       description: "Path to source files to analyze"
  #     coverage_threshold:
  #       type: integer
  #       default: 80
  #       description: "Minimum coverage percentage"

# ===========================================================================
# P2 FEATURES (Output Validation)
# ===========================================================================

output_schema: object
  # Expected structure of the agent's output.
  # When defined, the result aggregator validates agent output
  # against this schema and logs warnings for missing fields.
  # Uses a simplified JSON Schema subset:
  #   - type: "object" | "string" | "array"
  #   - properties: {field_name: {type, required, description}}
  #   - required: [field_names]
  # Default: null (no output validation)
  # Example:
  #   output_schema:
  #     type: object
  #     required: [files_created, test_count]
  #     properties:
  #       files_created:
  #         type: array
  #         description: "List of test file paths created"
  #       test_count:
  #         type: integer
  #         description: "Number of tests generated"
  #       coverage:
  #         type: integer
  #         description: "Estimated coverage percentage"
---

# Agent Instructions (Markdown Body)

The body of the agent file contains the agent's system prompt instructions.
These are injected into the agent's context when spawned by the coordinator.

The body may contain {{param_name}} template variables that are substituted
at spawn time using the params defined in frontmatter.
```

---

## Validation Algorithm

### Complete Validation Workflow

```python
def validate_agent_definition(agent_path: str, project_root: str, params: dict = None) -> dict:
    """
    Validate an agent definition file against the canonical schema.

    Performs validation in order:
    1. File existence and readability
    2. YAML frontmatter parsing
    3. Required fields present and non-empty
    4. Required field types and constraints
    5. Optional field types and constraints (if present)
    6. Name matches filename
    7. Template resolution (if extends is set)
    8. Parameter substitution validation (if params defined)
    9. Dependency verification checks (if verify_dependencies set)

    All errors are collected and returned together (not fail-fast).

    Args:
        agent_path: Path to agent .md file (relative to project_root)
        project_root: Absolute path to project root
        params: Parameter values for substitution (optional)

    Returns:
        dict with agent_definition and validation_result
    """
    errors = []
    warnings = []
    full_path = os.path.join(project_root, agent_path)

    # STEP 1: File existence
    if not os.path.exists(full_path):
        errors.append({
            'field': 'file',
            'reason': f"Agent definition file not found: {agent_path}",
            'suggestion': (
                f"Agent file not found at: {full_path}\n\n"
                f"How to fix:\n"
                f"1. Create the agent file at: {full_path}\n"
                f"2. Add required YAML frontmatter (name, description, model)\n"
                f"3. Add agent instructions in the Markdown body"
            )
        })
        return {
            'agent_definition': None,
            'validation_result': {'valid': False, 'errors': errors, 'warnings': warnings}
        }

    # STEP 2: Parse YAML frontmatter
    parse_result = parse_agent_file(full_path)
    if 'error' in parse_result:
        errors.append(parse_result['error'])
        return {
            'agent_definition': None,
            'validation_result': {'valid': False, 'errors': errors, 'warnings': warnings}
        }

    frontmatter = parse_result['frontmatter']
    body = parse_result['body']

    # STEP 3: Validate required fields
    required_errors = validate_required_fields(frontmatter)
    errors.extend(required_errors)

    if required_errors:
        return {
            'agent_definition': None,
            'validation_result': {'valid': False, 'errors': errors, 'warnings': warnings}
        }

    # STEP 4: Validate required field constraints
    constraint_errors = validate_field_constraints(frontmatter)
    errors.extend(constraint_errors)

    # STEP 5: Validate optional field types (if present)
    optional_errors = validate_optional_fields(frontmatter)
    errors.extend(optional_errors)

    # STEP 6: Validate name matches filename
    expected_name = os.path.splitext(os.path.basename(agent_path))[0]
    if frontmatter.get('name') != expected_name:
        # Templates may have different names; warn but do not error
        if 'template' in agent_path.lower():
            warnings.append({
                'field': 'name',
                'reason': f"Agent name '{frontmatter['name']}' differs from filename '{expected_name}'",
                'suggestion': 'Template files may use different names; this is acceptable'
            })
        else:
            errors.append({
                'field': 'name',
                'reason': f"Agent name '{frontmatter['name']}' does not match filename '{expected_name}.md'",
                'suggestion': (
                    f"Option 1: Update frontmatter to: name: {expected_name}\n"
                    f"Option 2: Rename file to: agents/{frontmatter['name']}.md"
                )
            })

    # STEP 7: Resolve template (if extends is set)
    if frontmatter.get('extends'):
        template_result = resolve_template(frontmatter, project_root)
        if template_result.get('errors'):
            errors.extend(template_result['errors'])
        else:
            frontmatter = template_result['merged_frontmatter']
            if template_result.get('warnings'):
                warnings.extend(template_result['warnings'])

    # STEP 8: Validate parameter definitions and substitution
    if frontmatter.get('params'):
        param_errors = validate_params(frontmatter['params'], params, body)
        errors.extend(param_errors)

    # STEP 9: Apply defaults
    agent_def = apply_agent_defaults(frontmatter)
    agent_def['body'] = body

    # Return result
    if errors:
        return {
            'agent_definition': None,
            'validation_result': {'valid': False, 'errors': errors, 'warnings': warnings}
        }

    return {
        'agent_definition': agent_def,
        'validation_result': {'valid': True, 'errors': [], 'warnings': warnings}
    }
```

---

### Step 3: Required Field Validation

```python
def validate_required_fields(frontmatter: dict) -> list:
    """
    Validate that all required fields are present and non-empty.

    Required fields:
        - name: string (non-empty)
        - description: string (non-empty)
        - model: string (one of opus|sonnet|haiku)

    Returns:
        List of error dicts (empty if valid)
    """
    errors = []
    required_fields = {
        'name': {
            'type': str,
            'message': "Unique identifier for this agent (e.g., 'write-agent')",
            'example': "name: write-agent"
        },
        'description': {
            'type': str,
            'message': "One-line description of what this agent does",
            'example': "description: Generate unit tests for source files"
        },
        'model': {
            'type': str,
            'message': "Default model (opus, sonnet, or haiku)",
            'example': "model: sonnet"
        }
    }

    for field, spec in required_fields.items():
        if field not in frontmatter:
            errors.append({
                'field': field,
                'reason': f"Required field '{field}' is missing from agent definition",
                'suggestion': (
                    f"Add '{field}' to the YAML frontmatter.\n\n"
                    f"Purpose: {spec['message']}\n"
                    f"Example: {spec['example']}"
                )
            })
        elif frontmatter[field] is None:
            errors.append({
                'field': field,
                'reason': f"Required field '{field}' is null",
                'suggestion': f"Provide a value for '{field}'. Example: {spec['example']}"
            })
        elif isinstance(frontmatter[field], str) and not frontmatter[field].strip():
            errors.append({
                'field': field,
                'reason': f"Required field '{field}' is empty",
                'suggestion': f"Provide a non-empty value. Example: {spec['example']}"
            })

    return errors
```

---

### Step 4: Field Constraint Validation

```python
def validate_field_constraints(frontmatter: dict) -> list:
    """
    Validate field values against their type and range constraints.

    Returns:
        List of error dicts (empty if valid)
    """
    errors = []

    # Validate name format
    name = frontmatter.get('name', '')
    if name and not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
        errors.append({
            'field': 'name',
            'reason': f"Agent name '{name}' does not match required format",
            'suggestion': (
                "Agent name must be lowercase-kebab-case:\n"
                "  - Start and end with alphanumeric character\n"
                "  - Only contain lowercase letters, digits, and hyphens\n"
                "  - Examples: 'write-agent', 'analyze-agent', 'test-runner'"
            )
        })

    # Validate description length
    description = frontmatter.get('description', '')
    if description and len(description) > 200:
        errors.append({
            'field': 'description',
            'reason': f"Description exceeds 200 characters ({len(description)} chars)",
            'suggestion': "Keep the description to one concise line (max 200 characters)"
        })

    # Validate model value
    model = frontmatter.get('model', '')
    valid_models = ['opus', 'sonnet', 'haiku']
    if model and model not in valid_models:
        errors.append({
            'field': 'model',
            'reason': f"Invalid model '{model}'. Must be one of: {', '.join(valid_models)}",
            'suggestion': (
                f"Set model to one of:\n"
                f"  - opus: Complex analysis and coordination tasks\n"
                f"  - sonnet: Balanced capability for most tasks\n"
                f"  - haiku: Fast and efficient for simple tasks"
            )
        })

    return errors
```

---

### Step 5: Optional Field Validation

```python
def validate_optional_fields(frontmatter: dict) -> list:
    """
    Validate optional fields when present.

    Returns:
        List of error dicts (empty if valid)
    """
    errors = []

    # Validate subagent_type
    if 'subagent_type' in frontmatter:
        valid_types = ['general-purpose', 'Explore', 'Read', 'Write', 'Edit']
        if frontmatter['subagent_type'] not in valid_types:
            errors.append({
                'field': 'subagent_type',
                'reason': f"Invalid subagent_type '{frontmatter['subagent_type']}'",
                'suggestion': f"Must be one of: {', '.join(valid_types)}"
            })

    # Validate tools (must be list of strings)
    if 'tools' in frontmatter:
        if not isinstance(frontmatter['tools'], list):
            errors.append({
                'field': 'tools',
                'reason': f"tools must be a list, got {type(frontmatter['tools']).__name__}",
                'suggestion': "Example: tools: [Read, Write, Bash, Grep, Glob]"
            })
        elif not all(isinstance(t, str) for t in frontmatter['tools']):
            errors.append({
                'field': 'tools',
                'reason': "All items in tools list must be strings",
                'suggestion': "Example: tools: [Read, Write, Bash, Grep, Glob]"
            })

    # Validate files_read (must be list of strings)
    if 'files_read' in frontmatter:
        if not isinstance(frontmatter['files_read'], list):
            errors.append({
                'field': 'files_read',
                'reason': f"files_read must be a list, got {type(frontmatter['files_read']).__name__}",
                'suggestion': 'Example: files_read: ["src/**/*.ts", "package.json"]'
            })

    # Validate files_write (must be list of strings)
    if 'files_write' in frontmatter:
        if not isinstance(frontmatter['files_write'], list):
            errors.append({
                'field': 'files_write',
                'reason': f"files_write must be a list, got {type(frontmatter['files_write']).__name__}",
                'suggestion': 'Example: files_write: ["tests/**/*.test.ts"]'
            })

    # Validate timeout_seconds (30-3600)
    if 'timeout_seconds' in frontmatter:
        timeout = frontmatter['timeout_seconds']
        if not isinstance(timeout, int):
            errors.append({
                'field': 'timeout_seconds',
                'reason': f"timeout_seconds must be an integer, got {type(timeout).__name__}",
                'suggestion': "Example: timeout_seconds: 300"
            })
        elif timeout < 30 or timeout > 3600:
            errors.append({
                'field': 'timeout_seconds',
                'reason': f"timeout_seconds must be between 30 and 3600, got {timeout}",
                'suggestion': "Range: 30 seconds (minimum) to 3600 seconds (1 hour maximum)"
            })

    # Validate critical (boolean)
    if 'critical' in frontmatter:
        if not isinstance(frontmatter['critical'], bool):
            errors.append({
                'field': 'critical',
                'reason': f"critical must be a boolean, got {type(frontmatter['critical']).__name__}",
                'suggestion': "Example: critical: true"
            })

    # Validate max_instances (1-10)
    if 'max_instances' in frontmatter:
        instances = frontmatter['max_instances']
        if not isinstance(instances, int):
            errors.append({
                'field': 'max_instances',
                'reason': f"max_instances must be an integer, got {type(instances).__name__}",
                'suggestion': "Example: max_instances: 3"
            })
        elif instances < 1 or instances > 10:
            errors.append({
                'field': 'max_instances',
                'reason': f"max_instances must be between 1 and 10, got {instances}",
                'suggestion': "Range: 1 (default, single instance) to 10 (max parallel copies)"
            })

    # Validate verify_dependencies (list of objects with type, target, message)
    if 'verify_dependencies' in frontmatter:
        deps = frontmatter['verify_dependencies']
        if not isinstance(deps, list):
            errors.append({
                'field': 'verify_dependencies',
                'reason': f"verify_dependencies must be a list, got {type(deps).__name__}",
                'suggestion': "Example:\nverify_dependencies:\n  - type: file_exists\n    target: src/index.ts\n    message: \"Source file required\""
            })
        else:
            valid_check_types = ['file_exists', 'command_succeeds', 'env_var_set']
            for idx, dep in enumerate(deps):
                if not isinstance(dep, dict):
                    errors.append({
                        'field': f'verify_dependencies[{idx}]',
                        'reason': f"Each dependency check must be an object, got {type(dep).__name__}",
                        'suggestion': "Example: {type: file_exists, target: src/index.ts, message: '...'}"
                    })
                    continue
                if 'type' not in dep:
                    errors.append({
                        'field': f'verify_dependencies[{idx}].type',
                        'reason': "Missing 'type' field in dependency check",
                        'suggestion': f"Must be one of: {', '.join(valid_check_types)}"
                    })
                elif dep['type'] not in valid_check_types:
                    errors.append({
                        'field': f'verify_dependencies[{idx}].type',
                        'reason': f"Invalid check type '{dep['type']}'",
                        'suggestion': f"Must be one of: {', '.join(valid_check_types)}"
                    })
                if 'target' not in dep:
                    errors.append({
                        'field': f'verify_dependencies[{idx}].target',
                        'reason': "Missing 'target' field in dependency check",
                        'suggestion': "Specify the file path, command, or env var to check"
                    })

    return errors
```

---

### Apply Defaults

```python
def apply_agent_defaults(frontmatter: dict) -> dict:
    """
    Apply default values for optional fields not present in frontmatter.

    Args:
        frontmatter: Parsed and validated YAML frontmatter

    Returns:
        Frontmatter with defaults applied
    """
    defaults = {
        'version': '1.0.0',
        'subagent_type': 'general-purpose',
        'tools': None,
        'files_read': [],
        'files_write': [],
        'timeout_seconds': None,
        'critical': False,
        'max_instances': 1,
        'extends': None,
        'verify_dependencies': [],
        'output_schema': None,
        'params': None
    }

    result = defaults.copy()
    result.update(frontmatter)
    return result
```

---

## Template Resolution (P1 Feature)

Templates allow agent definitions to inherit from a base definition using the `extends` field. This reduces duplication when multiple agents share common configuration.

### Resolution Algorithm

```python
def resolve_template(frontmatter: dict, project_root: str, depth: int = 0) -> dict:
    """
    Resolve template inheritance for an agent definition.

    Template resolution follows these rules:
    1. Load the template file specified by 'extends'
    2. If the template also has 'extends', resolve recursively (max depth: 5)
    3. Merge fields: child values override parent values
    4. Lists are replaced, not merged (child list replaces parent list)
    5. The 'name' and 'description' fields are NEVER inherited
    6. The Markdown body is inherited if the child body is empty

    Args:
        frontmatter: Child agent's frontmatter (with 'extends' field)
        project_root: Absolute path to project root
        depth: Current recursion depth (for cycle detection)

    Returns:
        dict with 'merged_frontmatter' or 'errors'
    """
    MAX_TEMPLATE_DEPTH = 5

    if depth >= MAX_TEMPLATE_DEPTH:
        return {
            'errors': [{
                'field': 'extends',
                'reason': f"Template inheritance depth exceeds {MAX_TEMPLATE_DEPTH}",
                'suggestion': (
                    "Template chains are limited to 5 levels to prevent cycles.\n"
                    "Flatten the inheritance chain or remove unnecessary templates."
                )
            }]
        }

    template_path = frontmatter['extends']
    full_template_path = os.path.join(project_root, template_path)

    # Load template file
    if not os.path.exists(full_template_path):
        return {
            'errors': [{
                'field': 'extends',
                'reason': f"Template file not found: {template_path}",
                'suggestion': (
                    f"Template file not found at: {full_template_path}\n\n"
                    f"How to fix:\n"
                    f"1. Create the template file at the specified path\n"
                    f"2. Or update 'extends' to point to an existing template"
                )
            }]
        }

    template_parse = parse_agent_file(full_template_path)
    if 'error' in template_parse:
        return {'errors': [template_parse['error']]}

    template_fm = template_parse['frontmatter']

    # Recursively resolve template's own extends
    if template_fm.get('extends'):
        recursive_result = resolve_template(template_fm, project_root, depth + 1)
        if recursive_result.get('errors'):
            return recursive_result
        template_fm = recursive_result['merged_frontmatter']

    # Merge: template provides base, child overrides
    merged = template_fm.copy()

    # Child values override template values
    for key, value in frontmatter.items():
        if key == 'extends':
            continue  # Do not propagate extends
        if value is not None:
            merged[key] = value

    # name and description are NEVER inherited
    # (they must be unique per agent)
    merged['name'] = frontmatter.get('name', template_fm.get('name'))
    merged['description'] = frontmatter.get('description', template_fm.get('description'))

    return {
        'merged_frontmatter': merged,
        'warnings': [{
            'field': 'extends',
            'reason': f"Inherited from template: {template_path}",
            'suggestion': None
        }]
    }
```

### Template Example

```yaml
# agents/templates/writer-template.md
---
name: writer-template
description: Base template for all writing agents
model: sonnet
subagent_type: general-purpose
tools: [Read, Write, Edit, Glob, Grep, Bash]
files_read: ["src/**/*"]
timeout_seconds: 600
critical: false
max_instances: 5
params:
  target_path:
    type: string
    required: true
    description: "Path to write output files"
---

# Writer Agent Template

You are a code generation agent. Follow coding standards and produce clean output.
```

```yaml
# agents/write-test-agent.md
---
name: write-test-agent
description: Generate unit tests for source files
model: sonnet
extends: agents/templates/writer-template.md
files_write: ["tests/**/*.test.ts"]
critical: false
params:
  target_path:
    type: string
    required: true
    description: "Path to source files to test"
  coverage_threshold:
    type: integer
    default: 80
    description: "Minimum coverage target"
---

# Test Writer Agent

You are a test generation agent. Generate comprehensive unit tests.
Target coverage: {{coverage_threshold}}%
Source path: {{target_path}}
```

Resolved definition for `write-test-agent.md`:
```yaml
name: write-test-agent           # From child (never inherited)
description: Generate unit tests # From child (never inherited)
model: sonnet                    # From child (overrides template)
subagent_type: general-purpose   # Inherited from template
tools: [Read, Write, Edit, ...]  # Inherited from template
files_read: ["src/**/*"]         # Inherited from template
files_write: ["tests/**/*.test.ts"]  # From child (overrides)
timeout_seconds: 600             # Inherited from template
critical: false                  # From child
max_instances: 5                 # Inherited from template
params:                          # From child (overrides template params)
  target_path: ...
  coverage_threshold: ...
```

---

## Parameter Substitution (P1 Feature)

Parameters allow agent definitions to be reusable with different configurations. The `{{param_name}}` syntax in the Markdown body is replaced with concrete values at spawn time.

### Substitution Algorithm

```python
def substitute_params(body: str, param_defs: dict, param_values: dict) -> dict:
    """
    Substitute {{param_name}} placeholders in the agent body with values.

    Algorithm:
    1. Find all {{param_name}} placeholders in body
    2. For each placeholder:
       a. Check if param is defined in param_defs
       b. Use provided value from param_values, or default from param_defs
       c. If required and not provided, return error
    3. Replace all placeholders with resolved values
    4. Warn about unreferenced params (defined but not used in body)

    Args:
        body: Agent Markdown body with {{param_name}} placeholders
        param_defs: Parameter definitions from frontmatter 'params'
        param_values: Concrete values provided at spawn time

    Returns:
        dict with 'body' (substituted) or 'errors'
    """
    errors = []
    warnings = []
    param_values = param_values or {}

    # Find all placeholders
    import re
    placeholders = set(re.findall(r'\{\{(\w+)\}\}', body))

    # Resolve each placeholder
    resolved = {}
    for param_name in placeholders:
        if param_name not in (param_defs or {}):
            errors.append({
                'field': f'params.{param_name}',
                'reason': f"Placeholder '{{{{param_name}}}}' found in body but not defined in params",
                'suggestion': (
                    f"Add '{param_name}' to the params section in frontmatter:\n"
                    f"params:\n"
                    f"  {param_name}:\n"
                    f"    type: string\n"
                    f"    required: true\n"
                    f"    description: \"...\""
                )
            })
            continue

        param_def = param_defs[param_name]

        if param_name in param_values:
            # Use provided value
            resolved[param_name] = str(param_values[param_name])
        elif 'default' in param_def:
            # Use default value
            resolved[param_name] = str(param_def['default'])
        elif param_def.get('required', False):
            # Required but not provided
            errors.append({
                'field': f'params.{param_name}',
                'reason': f"Required parameter '{param_name}' not provided",
                'suggestion': f"Provide '{param_name}' when spawning this agent"
            })
        else:
            # Optional with no default; leave placeholder
            resolved[param_name] = f"{{{{param_name}}}}"

    if errors:
        return {'errors': errors}

    # Perform substitution
    result_body = body
    for param_name, value in resolved.items():
        result_body = result_body.replace(f"{{{{{param_name}}}}}", value)

    # Check for unreferenced params
    if param_defs:
        for param_name in param_defs:
            if param_name not in placeholders:
                warnings.append({
                    'field': f'params.{param_name}',
                    'reason': f"Parameter '{param_name}' is defined but never referenced in body",
                    'suggestion': f"Add '{{{{{param_name}}}}}' to the agent body or remove from params"
                })

    return {
        'body': result_body,
        'warnings': warnings
    }
```

---

## Error Messages Summary

| Field | Error | Message |
|-------|-------|---------|
| `name` | Missing | Required field 'name' is missing from agent definition |
| `name` | Empty | Required field 'name' is empty |
| `name` | Format | Agent name must be lowercase-kebab-case |
| `name` | Mismatch | Agent name does not match filename |
| `description` | Missing | Required field 'description' is missing |
| `description` | Too long | Description exceeds 200 characters |
| `model` | Missing | Required field 'model' is missing |
| `model` | Invalid | Invalid model. Must be one of: opus, sonnet, haiku |
| `subagent_type` | Invalid | Invalid subagent_type |
| `tools` | Wrong type | tools must be a list |
| `timeout_seconds` | Out of range | timeout_seconds must be between 30 and 3600 |
| `critical` | Wrong type | critical must be a boolean |
| `max_instances` | Out of range | max_instances must be between 1 and 10 |
| `extends` | Not found | Template file not found |
| `extends` | Too deep | Template inheritance depth exceeds 5 |
| `params.X` | Undefined | Placeholder found in body but not defined in params |
| `params.X` | Required | Required parameter not provided |

---

## Testing Checklist

For acceptance:

### Required Fields
- [ ] Validates name is present, non-empty, and kebab-case
- [ ] Validates description is present, non-empty, and under 200 chars
- [ ] Validates model is present and one of opus/sonnet/haiku
- [ ] Returns error with suggestion for each missing required field

### Optional Fields
- [ ] Validates subagent_type against allowed values
- [ ] Validates tools is a list of strings
- [ ] Validates files_read and files_write are lists
- [ ] Validates timeout_seconds range (30-3600)
- [ ] Validates critical is boolean
- [ ] Validates max_instances range (1-10)
- [ ] Validates verify_dependencies structure

### Defaults
- [ ] Applies correct defaults for all optional fields
- [ ] Does not override explicitly set values

### Name Matching
- [ ] Validates name matches filename
- [ ] Warns (not errors) for template files with mismatched names

### Template Resolution (P1)
- [ ] Resolves single-level extends inheritance
- [ ] Resolves recursive extends (multi-level)
- [ ] Detects and rejects depth > 5
- [ ] Child values override parent values
- [ ] name and description are never inherited
- [ ] Returns error for missing template file

### Parameter Substitution (P1)
- [ ] Substitutes {{param_name}} with provided values
- [ ] Uses default values when param not provided
- [ ] Returns error for required params not provided
- [ ] Returns error for placeholders not defined in params
- [ ] Warns about unreferenced params

### Error Collection
- [ ] Collects all errors in single pass (not fail-fast)
- [ ] Each error includes field, reason, and suggestion
- [ ] Suggestions include examples and fix instructions

---

## Example Agent Definition

```markdown
---
name: write-agent
description: Generate unit tests for source files using analysis output
model: sonnet
version: 1.0.0
subagent_type: general-purpose
tools: [Read, Write, Edit, Glob, Grep, Bash]
files_read: ["src/**/*.ts", "src/**/*.js"]
files_write: ["tests/**/*.test.ts", "tests/**/*.test.js"]
timeout_seconds: 600
critical: false
max_instances: 5
---

# Write Agent

You are a test generation agent. Your task is to generate comprehensive
unit tests for the source files assigned to your batch.

## Instructions

1. Read the analysis output from the analyze-agent
2. For each source file in your batch:
   - Read the source file
   - Identify testable functions and classes
   - Generate unit tests with edge cases
   - Write tests to the corresponding test file
3. Return a summary of files created and test count

## Output Format

Return a structured summary:
- files_created: list of test file paths
- test_count: number of tests generated
- coverage_estimate: estimated coverage percentage
```

---

## References

- **Team Loader**: `skills/team-orchestration/team-loader.md` (validates agent references)
- **Lifecycle Manager**: `skills/team-orchestration/agent-lifecycle-manager.md` (tracks agents)
- **Coordinator Schema**: `skills/team-orchestration/coordinator-schema.md` (how coordinators use agents)
- **Spec**: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-12, REQ-F-15, REQ-F-16)

---

**Last Updated**: 2026-03-25
**Status**: Implementation
