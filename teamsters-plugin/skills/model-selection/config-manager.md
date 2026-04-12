---
name: config-manager
description: Load, validate, cache, and merge the .claude/teamsters-config.json configuration file for model selection, including the P1 model recommendation engine that suggests optimal models based on agent role keywords.
user-invocable: false
---

# Config Manager Sub-Skill

**Parent Skill**: [Model Selection](./SKILL.md)
**Version**: 3.0.0
**Category**: Infrastructure
**Purpose**: Load, validate, cache, and merge the `.claude/teamsters-config.json` configuration file for model selection. Includes the P1 model recommendation engine for keyword-based model suggestions.

**Used By**: Model Resolver (`model-resolver.md`), Test Loop Orchestrator

---

## Overview

The Config Manager handles all operations on the Teamsters configuration file located at `{project_root}/.claude/teamsters-config.json`. It provides:

1. **Config loading** with graceful fallback to defaults when the file is missing or malformed
2. **Schema validation** for model names, timeouts, and recommendation keywords against strict whitelists
3. **Merge-with-defaults algorithm** that overlays user config onto built-in defaults
4. **Session-level caching** so the config file is read from disk at most once per session
5. **Validation of unknown fields** with clear warnings for unrecognized keys
6. **P1 Model Recommendation Engine** that analyzes agent role keywords to suggest optimal models

### Design Principles

1. **Fail fast on invalid model names**: Invalid model names in the config file cause an immediate error (REQ-F-9). The system never silently uses a wrong model.
2. **Graceful on structural issues**: Missing files, malformed JSON, and unknown fields produce warnings but do not halt execution. Defaults are used instead.
3. **Cache for performance**: The config file is read once per session and cached in memory. Subsequent calls return the cached copy.
4. **Merge, do not replace**: User config is merged onto defaults. Omitted fields retain their default values.

---

## Config File Location

```
{project_root}/.claude/teamsters-config.json
```

Where `{project_root}` is the detected project root directory (see `skills/project-detection/SKILL.md`).

This follows the same `.claude/` directory pattern used by state management (`skills/state-management/SKILL.md`).

---

## Config File Schema

### Full Schema Definition

```json
{
  "models": {
    "<agent-role>": "opus|sonnet|haiku"
  },
  "timeouts": {
    "opus": 180,
    "sonnet": 120,
    "haiku": 60
  },
  "defaults": {
    "validate": "opus",
    "fix": "opus",
    "analyze": "sonnet",
    "write": "sonnet",
    "execute": "sonnet"
  },
  "recommendations": {
    "keywords_opus": ["architect", "design", "complex", "tdd", "validate", "fix"],
    "keywords_haiku": ["verify", "check", "setup", "install", "lint", "format"],
    "keywords_sonnet": []
  }
}
```

### Field Definitions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `models` | object | No | `{}` | Per-agent model overrides. Keys are agent roles, values are model names. |
| `timeouts` | object | No | See below | Per-model timeout values in seconds. |
| `timeouts.opus` | integer | No | `180` | Timeout for opus model in seconds. |
| `timeouts.sonnet` | integer | No | `120` | Timeout for sonnet model in seconds. |
| `timeouts.haiku` | integer | No | `60` | Timeout for haiku model in seconds. |
| `defaults` | object | No | See below | Default model assignment per agent when no override exists. |
| `defaults.validate` | string | No | `"opus"` | Default model for validate agent. |
| `defaults.fix` | string | No | `"opus"` | Default model for fix agent. |
| `defaults.analyze` | string | No | `"sonnet"` | Default model for analyze agent. |
| `defaults.write` | string | No | `"sonnet"` | Default model for write agent. |
| `defaults.execute` | string | No | `"sonnet"` | Default model for execute agent. |
| `recommendations` | object | No | See below | Keyword lists for model recommendation engine. |
| `recommendations.keywords_opus` | array | No | See schema | Keywords that trigger opus recommendation. |
| `recommendations.keywords_haiku` | array | No | See schema | Keywords that trigger haiku recommendation. |
| `recommendations.keywords_sonnet` | array | No | `[]` | Keywords that trigger sonnet recommendation. Empty means sonnet is the fallback. |

### Field Validation Rules

#### `models`

- **Type**: object (string keys, string values)
- **Valid keys**: Any agent role string (validated against known agents when used)
- **Valid values**: `"opus"`, `"sonnet"`, `"haiku"`
- **On invalid value**: FAIL FAST with error (REQ-F-9)
- **On unknown key**: Log warning, skip entry

#### `timeouts`

- **Type**: object (string keys, integer values)
- **Valid keys**: `"opus"`, `"sonnet"`, `"haiku"`
- **Valid values**: Positive integers (seconds)
- **On invalid value**: Log warning, use default timeout for that model
- **On unknown key**: Log warning, skip entry

#### `defaults`

- **Type**: object (string keys, string values)
- **Valid keys**: `"analyze"`, `"write"`, `"execute"`, `"validate"`, `"fix"`
- **Valid values**: `"opus"`, `"sonnet"`, `"haiku"`
- **On invalid value**: FAIL FAST with error (REQ-F-9)
- **On unknown key**: Log warning, skip entry

#### `recommendations`

- **Type**: object (string keys, array values)
- **Valid keys**: `"keywords_opus"`, `"keywords_haiku"`, `"keywords_sonnet"`
- **Valid values**: Arrays of strings (keyword strings, case-insensitive)
- **On invalid value**: Log warning, use default keyword list
- **On unknown key**: Log warning, skip entry

---

## Default Configuration

The built-in defaults used when no config file exists or when fields are omitted:

```json
{
  "models": {},
  "timeouts": {
    "opus": 180,
    "sonnet": 120,
    "haiku": 60
  },
  "defaults": {
    "validate": "opus",
    "fix": "opus",
    "analyze": "sonnet",
    "write": "sonnet",
    "execute": "sonnet"
  },
  "recommendations": {
    "keywords_opus": ["architect", "design", "complex", "tdd", "validate", "fix"],
    "keywords_haiku": ["verify", "check", "setup", "install", "lint", "format"],
    "keywords_sonnet": []
  }
}
```

---

## Operations

### Load Config

Load configuration from disk with graceful fallback to defaults. Returns a fully populated config object with all fields present (user values merged onto defaults).

**Input**: `project_root` (absolute path to project root directory)

**Output**: Validated and merged config object

**Algorithm**:

```
FUNCTION load_config(project_root):

    # Step 0: Check session cache
    IF session_cache contains config for project_root:
        RETURN session_cache[project_root]

    config_path = "{project_root}/.claude/teamsters-config.json"

    # Step 1: Check if file exists
    IF config_path does not exist:
        Log info: "No config file found at {config_path}, using defaults."
        result = default_config()
        session_cache[project_root] = result
        RETURN result

    # Step 2: Read file contents
    TRY:
        content = Read file at config_path
    CATCH file read error:
        Log warning: "Cannot read config file at {config_path}: {error}"
        result = default_config()
        session_cache[project_root] = result
        RETURN result

    # Step 3: Parse JSON
    TRY:
        parsed = parse_json(content)
    CATCH JSON parse error:
        Log warning: "WARNING: Malformed JSON in config file at {config_path}"
        Log warning: "Parse error: {specific error message}"
        Log warning: "Using default configuration. To fix, correct the JSON syntax or delete the file."
        result = default_config()
        session_cache[project_root] = result
        RETURN result

    # Step 4: Validate and merge with defaults
    result = validate_and_merge(parsed, config_path)

    # Step 5: Cache for session duration
    session_cache[project_root] = result

    RETURN result
```

### Validate and Merge

Validates a parsed config object against the schema, then merges it onto the built-in defaults. User-provided values override defaults; omitted fields retain defaults.

**Input**: Parsed config object, config file path (for error messages)

**Output**: Validated and merged config object (all fields present)

**Algorithm**:

```
FUNCTION validate_and_merge(parsed, config_path=""):

    VALID_MODELS = ["opus", "sonnet", "haiku"]
    VALID_AGENTS = ["analyze", "write", "execute", "validate", "fix"]
    VALID_TOP_LEVEL_KEYS = ["models", "timeouts", "defaults", "recommendations"]
    VALID_RECOMMENDATION_KEYS = ["keywords_opus", "keywords_haiku", "keywords_sonnet"]

    result = default_config()

    # ── Check for unknown top-level fields ──
    FOR EACH key IN parsed:
        IF key NOT IN VALID_TOP_LEVEL_KEYS:
            Log warning: "Unknown field '{key}' in config file at {config_path}, ignoring."

    # ── Validate and merge "models" ──
    IF parsed has "models" AND typeof(parsed.models) == object:
        FOR EACH (agent_role, model_name) IN parsed.models:
            model_lower = lowercase(strip(model_name))
            IF model_lower NOT IN VALID_MODELS:
                FAIL with error:
                    "Invalid model '{model_name}' for agent role '{agent_role}' in config file."
                    "Supported models: opus, sonnet, haiku"
                    "Config file: {config_path}"
            result.models[agent_role] = model_lower

    # ── Validate and merge "timeouts" ──
    IF parsed has "timeouts" AND typeof(parsed.timeouts) == object:
        FOR EACH (model_name, timeout_value) IN parsed.timeouts:
            IF model_name NOT IN VALID_MODELS:
                Log warning: "Unknown model '{model_name}' in timeouts section, ignoring."
                CONTINUE
            IF typeof(timeout_value) != integer OR timeout_value <= 0:
                Log warning: "Invalid timeout value '{timeout_value}' for model '{model_name}', using default."
                CONTINUE
            result.timeouts[model_name] = timeout_value

    # ── Validate and merge "defaults" ──
    IF parsed has "defaults" AND typeof(parsed.defaults) == object:
        FOR EACH (agent_name, model_name) IN parsed.defaults:
            IF agent_name NOT IN VALID_AGENTS:
                Log warning: "Unknown agent '{agent_name}' in defaults section, ignoring."
                CONTINUE
            model_lower = lowercase(strip(model_name))
            IF model_lower NOT IN VALID_MODELS:
                FAIL with error:
                    "Invalid default model '{model_name}' for agent '{agent_name}' in config file."
                    "Supported models: opus, sonnet, haiku"
                    "Config file: {config_path}"
            result.defaults[agent_name] = model_lower

    # ── Validate and merge "recommendations" ──
    IF parsed has "recommendations" AND typeof(parsed.recommendations) == object:
        FOR EACH (key, value) IN parsed.recommendations:
            IF key NOT IN VALID_RECOMMENDATION_KEYS:
                Log warning: "Unknown recommendation key '{key}' in config file, ignoring."
                CONTINUE
            IF typeof(value) != array:
                Log warning: "Invalid value for recommendation '{key}', expected array. Using default."
                CONTINUE
            # Validate that all entries are strings
            valid_keywords = []
            FOR EACH item IN value:
                IF typeof(item) == string:
                    valid_keywords.append(lowercase(strip(item)))
                ELSE:
                    Log warning: "Non-string keyword in '{key}', skipping entry."
            result.recommendations[key] = valid_keywords

    RETURN result
```

### Merge With Defaults Algorithm

The merge strategy follows these rules:

1. **Top-level objects**: Each top-level key (`models`, `timeouts`, `defaults`, `recommendations`) is an object. User values are overlaid onto defaults at the second level.
2. **Missing top-level keys**: If the user config omits a top-level key entirely, the default object for that key is used in full.
3. **Partial objects**: If the user provides a partial object (e.g., `"timeouts": {"opus": 200}`), the provided values override defaults while omitted keys retain defaults. In this example, `opus=200`, `sonnet=120` (default), `haiku=60` (default).
4. **Empty objects**: An empty object (e.g., `"models": {}`) is valid and means "no overrides for this section."

```
MERGE EXAMPLES:

User config:                     Merged result:
{                                {
  "timeouts": {                    "models": {},
    "opus": 200                    "timeouts": {
  }                                  "opus": 200,     <-- user override
}                                    "sonnet": 120,   <-- default
                                     "haiku": 60      <-- default
                                   },
                                   "defaults": {      <-- all defaults
                                     "validate": "opus",
                                     "fix": "opus",
                                     "analyze": "sonnet",
                                     "write": "sonnet",
                                     "execute": "sonnet"
                                   },
                                   "recommendations": { <-- all defaults
                                     "keywords_opus": [...],
                                     "keywords_haiku": [...],
                                     "keywords_sonnet": []
                                   }
                                 }
```

---

## Session Cache

The config file is read from disk once per session and cached in memory. This avoids redundant file I/O when the resolver is called multiple times (once per agent, five times per test-loop execution).

### Cache Behavior

```
SESSION_CACHE = {}   # Global, keyed by project_root

FUNCTION get_cached_config(project_root):
    IF project_root IN SESSION_CACHE:
        RETURN SESSION_CACHE[project_root]
    RETURN null

FUNCTION set_cached_config(project_root, config):
    SESSION_CACHE[project_root] = config

FUNCTION invalidate_cache(project_root=null):
    IF project_root is null:
        SESSION_CACHE = {}       # Clear all
    ELSE:
        DELETE SESSION_CACHE[project_root]
```

### Cache Invalidation

The cache is invalidated in the following scenarios:

1. **Session start**: Cache is empty at the start of each session.
2. **Config save**: After `save_config()` writes a new config to disk, the cached entry for that project_root is invalidated.
3. **Explicit invalidation**: The orchestrator can call `invalidate_cache()` to force a reload.

### Cache Rationale

- The config file is user-editable but changes between sessions, not during a session.
- Five resolver calls per test-loop iteration means five redundant file reads without caching.
- Cache is keyed by `project_root` to support multi-project scenarios (unlikely but safe).

---

## Save Config

Persist configuration to disk using atomic write pattern (temp file + rename).

**Input**:
- `project_root`: Absolute path to project root directory
- `config`: Config object to save

**Output**: Success or error

**Algorithm**:

```
FUNCTION save_config(project_root, config):

    config_dir = "{project_root}/.claude"
    config_path = "{config_dir}/teamsters-config.json"
    tmp_path = "{config_dir}/teamsters-config.json.tmp"

    # Step 1: Ensure .claude directory exists
    IF config_dir does not exist:
        Create directory config_dir

    # Step 2: Serialize to JSON (pretty-printed for human readability)
    json_content = json_serialize(config, indent=2)

    # Step 3: Write to temporary file
    Write json_content to tmp_path

    # Step 4: Atomic rename (temp -> final)
    # On Windows: move /Y "{tmp_path}" "{config_path}"
    # On Unix:    mv "{tmp_path}" "{config_path}"
    Rename tmp_path to config_path

    # Step 5: Invalidate session cache for this project
    invalidate_cache(project_root)

    # Step 6: Verify write
    IF config_path does not exist:
        Log error: "Failed to save config: file not found after rename"
        RETURN error

    RETURN success
```

---

## P1 Model Recommendation Engine

The recommendation engine analyzes agent role names and descriptions to suggest the optimal model tier. This is used as an advisory layer -- it provides suggestions that can be overridden by explicit configuration at any precedence level.

### Keyword-to-Model Mapping

| Keywords | Suggested Model | Rationale |
|----------|----------------|-----------|
| `architect`, `design`, `complex`, `tdd`, `validate`, `fix` | opus | Complex reasoning, architectural decisions, test-driven development, and validation require highest capability. |
| `verify`, `check`, `setup`, `install`, `lint`, `format` | haiku | Verification, checking, and tooling tasks are well-defined and benefit from speed over depth. |
| *(no match / general tasks)* | sonnet | Balanced capability for general-purpose tasks. Sonnet is the safe default. |

### `recommend_model(agent_name, agent_description)`

Analyzes the agent name and optional description to suggest the optimal model.

**Input**:

```yaml
agent_name: string          # The name/role of the agent (e.g., "validate", "lint-runner")
agent_description: string   # Optional description of the agent's purpose (e.g., "Validates test categorization accuracy")
```

**Output**:

```yaml
recommended_model: string   # One of: "opus", "sonnet", "haiku"
confidence: string          # One of: "high", "medium", "low"
matching_keywords: array    # Keywords that triggered the recommendation
reason: string              # Human-readable explanation of the recommendation
```

**Algorithm**:

```
FUNCTION recommend_model(agent_name, agent_description=""):

    # Load recommendation keywords from config (or use defaults)
    config = get_cached_config() OR default_config()
    keywords_opus = config.recommendations.keywords_opus
    keywords_haiku = config.recommendations.keywords_haiku
    keywords_sonnet = config.recommendations.keywords_sonnet

    # Combine agent name and description into a searchable text
    # Normalize to lowercase for case-insensitive matching
    search_text = lowercase(agent_name + " " + agent_description)

    # Tokenize: split on whitespace, hyphens, and underscores
    tokens = split(search_text, pattern=/[\s\-_]+/)

    # ── Check for opus keywords (highest priority) ──
    opus_matches = []
    FOR EACH keyword IN keywords_opus:
        IF lowercase(keyword) IN tokens OR search_text CONTAINS lowercase(keyword):
            opus_matches.append(keyword)

    IF opus_matches is not empty:
        confidence = "high" IF len(opus_matches) >= 2 ELSE "medium"
        RETURN {
            recommended_model: "opus",
            confidence: confidence,
            matching_keywords: opus_matches,
            reason: "Agent name/description contains keywords suggesting complex reasoning: {opus_matches}"
        }

    # ── Check for haiku keywords ──
    haiku_matches = []
    FOR EACH keyword IN keywords_haiku:
        IF lowercase(keyword) IN tokens OR search_text CONTAINS lowercase(keyword):
            haiku_matches.append(keyword)

    IF haiku_matches is not empty:
        confidence = "high" IF len(haiku_matches) >= 2 ELSE "medium"
        RETURN {
            recommended_model: "haiku",
            confidence: confidence,
            matching_keywords: haiku_matches,
            reason: "Agent name/description contains keywords suggesting simple/fast task: {haiku_matches}"
        }

    # ── Check for explicit sonnet keywords (if configured) ──
    sonnet_matches = []
    FOR EACH keyword IN keywords_sonnet:
        IF lowercase(keyword) IN tokens OR search_text CONTAINS lowercase(keyword):
            sonnet_matches.append(keyword)

    IF sonnet_matches is not empty:
        RETURN {
            recommended_model: "sonnet",
            confidence: "medium",
            matching_keywords: sonnet_matches,
            reason: "Agent name/description contains keywords for general-purpose tasks: {sonnet_matches}"
        }

    # ── Default: sonnet with low confidence ──
    RETURN {
        recommended_model: "sonnet",
        confidence: "low",
        matching_keywords: [],
        reason: "No specific keywords matched. Defaulting to sonnet for general-purpose tasks."
    }
```

### Recommendation Examples

| Agent Name | Description | Recommended Model | Confidence | Matching Keywords |
|------------|-------------|-------------------|------------|-------------------|
| `validate` | "Validates test results" | opus | medium | `["validate"]` |
| `fix` | "Fixes failing tests" | opus | medium | `["fix"]` |
| `architect-planner` | "Designs complex system architecture" | opus | high | `["architect", "design", "complex"]` |
| `tdd-validator` | "Validates TDD test coverage" | opus | high | `["tdd", "validate"]` |
| `lint-checker` | "Runs lint checks on code" | haiku | high | `["lint", "check"]` |
| `format-verifier` | "Verifies code formatting" | haiku | high | `["format", "verify"]` |
| `setup-installer` | "Sets up and installs dependencies" | haiku | high | `["setup", "install"]` |
| `write` | "Writes test files" | sonnet | low | `[]` |
| `analyze` | "Analyzes test patterns" | sonnet | low | `[]` |
| `execute` | "Executes test commands" | sonnet | low | `[]` |

### Recommendation Priority

When an agent name or description matches keywords for multiple models, opus keywords take priority over haiku keywords. This is because:

1. Over-provisioning (using opus for a simple task) wastes resources but produces correct results.
2. Under-provisioning (using haiku for a complex task) may produce incorrect or incomplete results.
3. The cost of a wrong model selection is asymmetric: too-powerful is wasteful, too-weak is broken.

---

## Validation Patterns

### Model Name Validation (REQ-F-9)

Used throughout the config manager:

```
VALID_MODELS = ["opus", "sonnet", "haiku"]

FUNCTION validate_model_name(model, context_agent, context_source):
    model_lower = lowercase(strip(model))

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

### Unknown Field Detection

```
FUNCTION check_unknown_fields(parsed, valid_keys, section_name, config_path):
    FOR EACH key IN parsed:
        IF key NOT IN valid_keys:
            Log warning: "Unknown field '{key}' in {section_name} section of {config_path}, ignoring."
```

---

## Error Handling

### Missing Config File

**Behavior**: Return default config. This is NOT an error.

**Log message** (informational):
```
No config file found at {project_root}/.claude/teamsters-config.json, using defaults.
```

**Rationale**: First-time users will not have a config file. The system must work out of the box.

### Malformed JSON

**Behavior**: Log warning, return default config.

**Log message** (warning):
```
WARNING: Malformed JSON in config file at {project_root}/.claude/teamsters-config.json
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
Config file: {project_root}/.claude/teamsters-config.json

Supported models: opus, sonnet, haiku

To fix:
1. Edit {project_root}/.claude/teamsters-config.json
2. Change the model name to one of: opus, sonnet, haiku
3. Run the command again

Example valid config:
{
  "models": {
    "validate": "opus",
    "fix": "opus"
  },
  "timeouts": {
    "opus": 180,
    "sonnet": 120,
    "haiku": 60
  },
  "defaults": {
    "validate": "opus",
    "fix": "opus",
    "analyze": "sonnet",
    "write": "sonnet",
    "execute": "sonnet"
  }
}
```

**Rationale**: Invalid model names indicate user intent that cannot be fulfilled. Silently falling back would hide the misconfiguration.

### Unknown Fields in Config File

**Behavior**: Log warning, ignore the unknown field. Continue processing.

**Log message** (warning):
```
WARNING: Unknown field 'model_overrides' in config file at {config_path}, ignoring.
Did you mean 'models'? See schema documentation for valid fields.
```

**Rationale**: Users migrating from an older config schema may have stale fields. Warn but do not break.

### Atomic Write Failure

If the rename step fails (e.g., cross-device rename on some systems):

```
FUNCTION save_config_with_fallback(project_root, config):
    TRY:
        save_config(project_root, config)
    CATCH rename error:
        Log warning: "Atomic rename failed, using direct write."
        Write json_content directly to config_path
```

---

## Config File Examples

### Example 1: Minimal (First-Time User)

No config file exists. System uses all built-in defaults.

### Example 2: Override Specific Agent Models

```json
{
  "models": {
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

All other fields (`timeouts`, `defaults`, `recommendations`) use built-in defaults.

### Example 3: Custom Timeouts

```json
{
  "timeouts": {
    "opus": 240,
    "sonnet": 150
  }
}
```

Opus gets 4 minutes, sonnet gets 2.5 minutes, haiku stays at default 60 seconds.

### Example 4: Custom Recommendation Keywords

```json
{
  "recommendations": {
    "keywords_opus": ["architect", "design", "complex", "tdd", "validate", "fix", "security", "audit"],
    "keywords_haiku": ["verify", "check", "setup", "install", "lint", "format", "clean", "sort"]
  }
}
```

Extends the keyword lists with project-specific terms.

### Example 5: Full Configuration

```json
{
  "models": {
    "analyze": "opus",
    "write": "opus",
    "execute": "haiku",
    "validate": "opus",
    "fix": "opus"
  },
  "timeouts": {
    "opus": 240,
    "sonnet": 150,
    "haiku": 45
  },
  "defaults": {
    "validate": "opus",
    "fix": "opus",
    "analyze": "sonnet",
    "write": "sonnet",
    "execute": "sonnet"
  },
  "recommendations": {
    "keywords_opus": ["architect", "design", "complex", "tdd", "validate", "fix"],
    "keywords_haiku": ["verify", "check", "setup", "install", "lint", "format"],
    "keywords_sonnet": ["write", "generate", "template"]
  }
}
```

---

## Environment Variable Overrides (REQ-F-7)

Environment variables override config file values. They are checked during model resolution (in `model-resolver.md`), not during config load.

| Environment Variable | Agent | Example |
|---------------------|-------|---------|
| `TEAMSTERS_ANALYZE_MODEL` | analyze | `TEAMSTERS_ANALYZE_MODEL=sonnet` |
| `TEAMSTERS_WRITE_MODEL` | write | `TEAMSTERS_WRITE_MODEL=opus` |
| `TEAMSTERS_EXECUTE_MODEL` | execute | `TEAMSTERS_EXECUTE_MODEL=haiku` |
| `TEAMSTERS_VALIDATE_MODEL` | validate | `TEAMSTERS_VALIDATE_MODEL=opus` |
| `TEAMSTERS_FIX_MODEL` | fix | `TEAMSTERS_FIX_MODEL=opus` |

Environment variable values are case-insensitive. The system normalizes to lowercase before validation.

---

## Implementation Checklist

When implementing the config manager, use these tools in the Claude Code agent context:

- [ ] **Load**: Use the `Read` tool to read `{project_root}/.claude/teamsters-config.json`
- [ ] **Parse**: Parse the file content as JSON
- [ ] **Validate**: Apply all validation rules from this document (models, timeouts, defaults, recommendations)
- [ ] **Merge**: Overlay user config onto built-in defaults using merge-with-defaults algorithm
- [ ] **Cache**: Store the merged config in session cache keyed by project_root
- [ ] **Save**: Use the `Write` tool to write to `.teamsters-config.json.tmp`
- [ ] **Rename**: Use the `Bash` tool to atomically rename `.tmp` to `.json`
- [ ] **Invalidate cache**: Clear cached config after save
- [ ] **Unknown fields**: Log warnings for any keys not in the schema
- [ ] **Recommendation engine**: Implement `recommend_model()` with keyword matching
- [ ] **Error display**: Output clear error messages directly to user (not via file)

---

## Security Considerations

### Config File Tampering

- **Risk**: User edits config with invalid or malicious values.
- **Mitigation**: Strict validation on load. Model names and agent names are whitelisted. Timeout values are validated as positive integers. No code execution from config values.

### Path Traversal

- **Risk**: Config file path constructed from user input.
- **Mitigation**: Always use `{project_root}/.claude/teamsters-config.json`. The `project_root` is validated by project detection skill.

### Keyword Injection

- **Risk**: User adds keywords to recommendations that could cause unintended model selection.
- **Mitigation**: Keywords are only used for advisory recommendations, never for mandatory model assignment. Explicit config overrides always take precedence over recommendations.

---

## Relationship to Other Sub-Skills

### Used By

- **Model Resolver** (`model-resolver.md`): Calls `load_config()` to read model overrides and timeouts
- **Test Loop Orchestrator**: Uses recommendation engine for advisory model suggestions

### Does Not Depend On

- **State Management**: Config and state are independent. They share the `.claude/` directory but have no cross-dependency.
- **Metrics Collector**: Config manager does not read or write metrics.

---

## Testing Checklist

### Config Loading

- [ ] Config file loads correctly from `{project_root}/.claude/teamsters-config.json`
- [ ] Missing config file falls back to defaults gracefully
- [ ] Malformed JSON in config file logs warning and returns defaults
- [ ] Config with all fields populated loads and validates correctly
- [ ] Config with partial fields merges correctly with defaults

### Validation

- [ ] Model names validated against whitelist `["opus", "sonnet", "haiku"]` (REQ-F-9)
- [ ] Invalid model name in `models` section produces clear error and fails fast
- [ ] Invalid model name in `defaults` section produces clear error and fails fast
- [ ] Unknown top-level fields log warning but do not fail
- [ ] Unknown agent names in `defaults` log warning and are skipped
- [ ] Negative or zero timeout values log warning and use defaults
- [ ] Non-integer timeout values log warning and use defaults

### Caching

- [ ] Second call to `load_config()` with same project_root returns cached copy
- [ ] Cache is invalidated after `save_config()` completes
- [ ] `invalidate_cache()` forces re-read from disk on next load

### Recommendation Engine

- [ ] `recommend_model("validate", "")` returns opus (keyword match on agent name)
- [ ] `recommend_model("lint-checker", "Runs lint checks")` returns haiku (keyword match)
- [ ] `recommend_model("execute", "")` returns sonnet (no keyword match, default)
- [ ] `recommend_model("tdd-validator", "TDD test validation")` returns opus with high confidence
- [ ] Custom keywords from config are used when present
- [ ] Opus keywords take priority over haiku keywords when both match

### Merge Algorithm

- [ ] User config with only `models` section preserves default timeouts, defaults, and recommendations
- [ ] User config with partial `timeouts` merges with default timeouts
- [ ] Empty config object `{}` returns all defaults

---

**Last Updated**: 2026-03-25
**Status**: Phase 2 - Extended configuration with recommendation engine (v3)
