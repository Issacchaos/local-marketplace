# Config Manager Sub-Skill

**Parent Skill**: [Model Selection](./SKILL.md)
**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Load, validate, and persist the `.claude/dante-config.json` configuration file for model selection

---

## Overview

The Config Manager handles all operations on the Dante configuration file located at `{project_root}/.claude/dante-config.json`. This file stores:

- Schema version
- Per-agent model overrides

The Config Manager ensures that:
1. Missing config files are handled gracefully (return defaults)
2. Malformed JSON is handled gracefully (log warning, return defaults)
3. Model names are validated against a strict whitelist (fail fast on invalid)
4. Config writes use an atomic pattern (temp file + rename) to prevent corruption
5. Environment variables can override any config file value

---

## Config File Location

```
{project_root}/.claude/dante-config.json
```

Where `{project_root}` is the detected project root directory (see `skills/project-detection/SKILL.md`).

This follows the same `.claude/` directory pattern used by state management (`skills/state-management/SKILL.md`).

---

## Config File Schema

### Full Schema

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "opus",
    "fix": "opus"
  }
}
```

### Field Definitions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `version` | string | Yes | `"1.0.0"` | Schema version for forward compatibility |
| `model_overrides` | object | No | `{}` | Per-agent model overrides |

### Field Validation Rules

#### `version`

- **Type**: string
- **Format**: Semantic version (`"major.minor.patch"`)
- **Current valid value**: `"1.0.0"`
- **On mismatch**: Log warning but continue (forward-compatible design)

#### `model_overrides`

- **Type**: object (string keys, string values)
- **Valid keys**: `"analyze"`, `"write"`, `"execute"`, `"validate"`, `"fix"`
- **Valid values**: `"opus"`, `"sonnet"`, `"haiku"`
- **On invalid key**: Log warning, skip entry
- **On invalid value**: FAIL FAST with error (REQ-F-9)

---

## Default Configuration

When no config file exists or the file is malformed, return this default:

```json
{
  "version": "1.0.0",
  "model_overrides": {}
}
```

---

## Operations

### Load Config

Load configuration from disk with graceful fallback to defaults.

**Input**: `project_root` (absolute path to project root directory)

**Output**: Validated config object (dict/map)

**Algorithm**:

```
FUNCTION load_config(project_root):

    config_path = "{project_root}/.claude/dante-config.json"

    # Step 1: Check if file exists
    IF config_path does not exist:
        Log info: "No config file found at {config_path}, using defaults"
        RETURN default_config()

    # Step 2: Read file contents
    TRY:
        content = Read file at config_path
    CATCH file read error:
        Log warning: "Cannot read config file at {config_path}: {error}"
        RETURN default_config()

    # Step 3: Parse JSON
    TRY:
        config = parse_json(content)
    CATCH JSON parse error:
        Log warning: "Malformed JSON in config file at {config_path}: {error}"
        Log warning: "Using default configuration"
        RETURN default_config()

    # Step 4: Validate schema
    validated_config = validate_config(config)

    RETURN validated_config
```

### Validate Config

Validate a parsed config object against the schema. Invalid model names cause a fail-fast error (REQ-F-9). Other invalid fields are handled gracefully.

**Input**: Parsed config object, config file path (for error messages)

**Output**: Validated config object (invalid fields corrected or removed)

**Algorithm**:

```
FUNCTION validate_config(config, config_path=""):

    VALID_MODELS = ["opus", "sonnet", "haiku"]
    VALID_AGENTS = ["analyze", "write", "execute", "validate", "fix"]

    result = default_config()

    # Validate version
    IF config has "version" AND typeof(config.version) == string:
        result.version = config.version
    ELSE:
        result.version = "1.0.0"

    # Validate model_overrides (CRITICAL - fail fast on invalid model names)
    IF config has "model_overrides" AND typeof(config.model_overrides) == object:
        result.model_overrides = {}

        FOR EACH (agent_name, model_name) IN config.model_overrides:

            # Validate agent name
            IF agent_name NOT IN VALID_AGENTS:
                Log warning: "Unknown agent '{agent_name}' in model_overrides, skipping. Valid: {VALID_AGENTS}"
                CONTINUE

            # Validate model name (REQ-F-9: FAIL FAST)
            model_lower = lowercase(model_name)
            IF model_lower NOT IN VALID_MODELS:
                FAIL with error:
                    "Invalid model '{model_name}' for agent '{agent_name}' in config file."
                    "Supported models: opus, sonnet, haiku"
                    "Config file: {config_path}"

            result.model_overrides[agent_name] = model_lower

    RETURN result
```

### Save Config

Persist configuration to disk using atomic write pattern (temp file + rename).

**Input**:
- `project_root`: Absolute path to project root directory
- `config`: Config object to save

**Output**: Success or error

**Algorithm**:

```
FUNCTION save_config(project_root, config):

    config_dir = "{project_root}/.claude"
    config_path = "{config_dir}/dante-config.json"
    tmp_path = "{config_dir}/dante-config.json.tmp"

    # Step 1: Ensure .claude directory exists
    IF config_dir does not exist:
        Create directory config_dir
        # On Windows: mkdir "{config_dir}"
        # On Unix: mkdir -p "{config_dir}"

    # Step 2: Merge with existing config (preserve fields we don't manage)
    existing_config = load_config(project_root)
    merged_config = merge(existing_config, config)

    # Step 3: Ensure version field is set
    IF merged_config does not have "version":
        merged_config.version = "1.0.0"

    # Step 4: Serialize to JSON (pretty-printed for human readability)
    json_content = json_serialize(merged_config, indent=2)

    # Step 5: Write to temporary file
    Write json_content to tmp_path

    # Step 6: Atomic rename (temp -> final)
    # On Windows: move /Y "{tmp_path}" "{config_path}"
    # On Unix: mv "{tmp_path}" "{config_path}"
    Rename tmp_path to config_path

    # Step 7: Verify write
    IF config_path does not exist:
        Log error: "Failed to save config: file not found after rename"
        RETURN error

    RETURN success
```

### Merge Config

Merge new config values into an existing config, preserving fields not present in the update.

**Algorithm**:

```
FUNCTION merge(existing, updates):

    result = copy(existing)

    FOR EACH (key, value) IN updates:
        IF key == "model_overrides" AND existing has "model_overrides":
            # Merge model_overrides individually (don't replace entire object)
            FOR EACH (agent, model) IN value:
                result.model_overrides[agent] = model
        ELSE:
            result[key] = value

    RETURN result
```

---

## Environment Variable Overrides (REQ-F-7)

Environment variables override config file values. They are checked during model resolution (in SKILL.md), not during config load.

### Per-Agent Model Override

| Environment Variable | Agent | Example |
|---------------------|-------|---------|
| `DANTE_ANALYZE_MODEL` | analyze | `DANTE_ANALYZE_MODEL=sonnet` |
| `DANTE_WRITE_MODEL` | write | `DANTE_WRITE_MODEL=opus` |
| `DANTE_EXECUTE_MODEL` | execute | `DANTE_EXECUTE_MODEL=haiku` |
| `DANTE_VALIDATE_MODEL` | validate | `DANTE_VALIDATE_MODEL=opus` |
| `DANTE_FIX_MODEL` | fix | `DANTE_FIX_MODEL=opus` |

### Resolution Pattern

When resolving a model for an agent, check environment variables AFTER CLI overrides but BEFORE config file:

```
FUNCTION resolve_env_var_model(agent_name):

    var_name = "DANTE_{agent_name_upper}_MODEL"
    value = read_env_var(var_name)

    IF value is set AND not empty:
        model = lowercase(value)
        Validate model against ["opus", "sonnet", "haiku"]
        IF invalid: FAIL FAST (REQ-F-9)
        RETURN model

    RETURN null (no env var override)
```

### Environment Variable Validation

- Values are **case-insensitive**: `OPUS`, `Opus`, `opus` are all valid
- Invalid values trigger fail-fast error (REQ-F-9), same as config file
- Empty string values are treated as "not set" (fall through to next precedence level)

---

## Error Handling

### Missing Config File

**Behavior**: Return default config. This is NOT an error.

**Log message** (informational):
```
No config file found at {project_root}/.claude/dante-config.json, using defaults.
```

**Rationale**: First-time users will not have a config file. The system must work out of the box.

### Malformed JSON

**Behavior**: Log warning, return default config.

**Log message** (warning):
```
WARNING: Malformed JSON in config file at {project_root}/.claude/dante-config.json
Parse error: {specific error message, e.g., "Unexpected token } at position 42"}
Using default configuration. To fix, correct the JSON syntax or delete the file.
```

**Rationale**: Users may accidentally corrupt the file while editing. The system should not crash.

### Invalid Model Name in Config File (REQ-F-9)

**Behavior**: FAIL FAST. Do not use defaults. Display clear error.

**Error message**:
```
ERROR: Invalid model configuration

Invalid model 'gpt4' for agent 'validate' in config file.
Config file: {project_root}/.claude/dante-config.json

Supported models: opus, sonnet, haiku

To fix:
1. Edit {project_root}/.claude/dante-config.json
2. Change the model name to one of: opus, sonnet, haiku
3. Run the command again

Example valid config:
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "opus",
    "fix": "opus"
  }
}
```

**Rationale**: Invalid model names indicate user intent that cannot be fulfilled. Silently falling back would hide the misconfiguration.

### Invalid Model Name in Environment Variable (REQ-F-9)

**Behavior**: FAIL FAST with clear error.

**Error message**:
```
ERROR: Invalid model in environment variable

DANTE_VALIDATE_MODEL='gpt4' is not a valid model.
Supported models: opus, sonnet, haiku

To fix:
  export DANTE_VALIDATE_MODEL=opus    # or sonnet, haiku
```

### Config Directory Not Writable

**Behavior**: Log warning, continue without persisting config. Model resolution still works using in-memory defaults and environment variables.

**Log message** (warning):
```
WARNING: Cannot create config directory at {project_root}/.claude/
Config changes will not be persisted across sessions.
```

### Atomic Write Failure

If the rename step fails (e.g., cross-device rename on some systems):

```
FUNCTION save_config_with_fallback(project_root, config):
    TRY:
        # Attempt atomic rename
        save_config(project_root, config)
    CATCH rename error:
        # Fallback: direct write (non-atomic but functional)
        Log warning: "Atomic rename failed, using direct write. Config may be corrupted if interrupted."
        Write json_content directly to config_path
```

---

## Validation Patterns

### Model Name Validation (REQ-F-9)

Used throughout the config manager and model resolution:

```
VALID_MODELS = ["opus", "sonnet", "haiku"]

FUNCTION validate_model_name(model, context_agent, context_source):
    model_lower = lowercase(model)

    IF model_lower NOT IN VALID_MODELS:
        FAIL with:
            "Invalid model '{model}' for agent '{context_agent}'."
            "Supported models: opus, sonnet, haiku"
            "Source: {context_source}"

    RETURN model_lower
```

### Agent Name Validation

```
VALID_AGENTS = ["analyze", "write", "execute", "validate", "fix"]

FUNCTION validate_agent_name(agent_name):
    IF agent_name NOT IN VALID_AGENTS:
        FAIL with:
            "Unknown agent '{agent_name}'."
            "Valid agents: analyze, write, execute, validate, fix"

    RETURN agent_name
```

---

## Config File Examples

### Example 1: Default (First-Time User)

No config file exists. System uses defaults:
- `model_overrides`: Empty (built-in defaults apply: validate=opus, fix=opus, others=sonnet)

### Example 2: Override Specific Agents

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

User forces validate and fix to use Sonnet (overrides built-in defaults). Other agents still use their defaults.

### Example 3: All Opus (Testing Maximum Quality)

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "analyze": "opus",
    "write": "opus",
    "execute": "opus",
    "validate": "opus",
    "fix": "opus"
  }
}
```

All agents use Opus for maximum quality.

### Example 4: Haiku for Execute (Cost Optimization)

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "execute": "haiku"
  }
}
```

Execute agent uses Haiku (fast, efficient for command construction). Other agents use built-in defaults.

---

## Implementation Checklist

When implementing the config manager, use these tools in the Claude Code agent context:

- [ ] **Load**: Use the `Read` tool to read `{project_root}/.claude/dante-config.json`
- [ ] **Parse**: Parse the file content as JSON
- [ ] **Validate**: Apply all validation rules from this document
- [ ] **Save**: Use the `Write` tool to write to `.dante-config.json.tmp`
- [ ] **Rename**: Use the `Bash` tool to atomically rename `.tmp` to `.json`
- [ ] **Create dir**: Use `Bash` tool with `mkdir` if `.claude/` directory does not exist
- [ ] **Env vars**: Use `Bash` tool to read environment variables when resolving
- [ ] **Error display**: Output clear error messages directly to user (not via file)

### Atomic Write Implementation (Cross-Platform)

```
# Step 1: Write to temp file
Use Write tool: write content to "{project_root}/.claude/dante-config.json.tmp"

# Step 2: Rename (platform-specific)
# Windows:
Use Bash tool: move /Y "{project_root}\.claude\dante-config.json.tmp" "{project_root}\.claude\dante-config.json"

# Unix/macOS:
Use Bash tool: mv "{project_root}/.claude/dante-config.json.tmp" "{project_root}/.claude/dante-config.json"
```

---

## Relationship to State Management

The config manager operates independently from state management (`skills/state-management/SKILL.md`), but shares the same `.claude/` directory:

```
{project_root}/.claude/
    dante-config.json         <-- Config Manager (this skill)
    .test-loop-state.md       <-- State Management
    .test-loop-history/       <-- State Management (archives)
```

**Key differences**:
- **Config file** (`dante-config.json`): Long-lived, persists across workflow sessions, user-editable
- **State file** (`.test-loop-state.md`): Per-workflow, archived on completion, system-managed

**No cross-dependency**: Config loading does not depend on state, and state management does not depend on config. They can be used independently.

---

## Security Considerations

### Config File Tampering

- **Risk**: User edits config with invalid or malicious values
- **Mitigation**: Strict validation on load. Model names whitelisted. No code execution from config values.

### Path Traversal

- **Risk**: Config file path constructed from user input
- **Mitigation**: Always use `{project_root}/.claude/dante-config.json`. The `project_root` is validated by project detection skill (no traversal possible).

### Environment Variable Injection

- **Risk**: Attacker sets `DANTE_VALIDATE_MODEL` to something unexpected
- **Mitigation**: Whitelist validation. Only `opus`, `sonnet`, `haiku` accepted. No arbitrary strings passed to API.

---

**Last Updated**: 2026-02-09
**Status**: Phase 1 - Foundation implementation
