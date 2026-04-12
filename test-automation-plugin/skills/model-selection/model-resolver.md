# Model Resolver Sub-Skill

**Parent Skill**: [Model Selection](./SKILL.md)
**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Resolve the correct Claude model and timeout for any agent by applying the full configuration precedence chain: CLI override > environment variable > config file > defaults

---

## Overview

The Model Resolver is the integration point that ties together configuration sources into a single callable entry point. The parent SKILL.md (Model Resolution Algorithm) describes the high-level flow. This document provides the **detailed implementation**: consolidated function signatures, edge cases, timeout resolution, validation, implementation checklist, and structured test scenarios.

### Design Principles

1. **Single entry point**: All model resolution goes through `resolve_model()`. No caller should directly check env vars, config, or defaults.
2. **Fail fast on invalid input**: Invalid model names or agent names produce clear errors immediately (REQ-F-18). The system never silently uses a wrong model.
3. **Transparent sourcing**: Every resolution result includes the source (cli, env, config, default) so the orchestrator can display it.
4. **Deterministic**: Given the same inputs and state, resolution always produces the same output.
5. **Stateless**: The resolver reads state but does not write state. Config persistence is delegated to ConfigManager.

---

## Interface

### `resolve_model(agent_name, project_root, cli_overrides)`

The primary entry point. Resolves which Claude model to use for a given agent.

**Input**:

```yaml
agent_name: string    # One of: "analyze", "write", "execute", "validate", "fix"
project_root: string  # Absolute path to the project root directory
cli_overrides: dict   # Optional dict of {agent_name: model_name} from CLI flags. May be empty or null.
```

**Output**:

```yaml
resolved_model: string      # One of: "opus", "sonnet", "haiku"
timeout_seconds: integer    # Timeout appropriate for the resolved model
resolution_source: string   # One of: "cli", "env", "config", "default"
```

### `get_timeout_for_model(model)`

Returns the appropriate timeout in seconds for a given model.

**Input**:

```yaml
model: string  # One of: "opus", "sonnet", "haiku"
```

**Output**:

```yaml
timeout_seconds: integer  # 180 for opus, 120 for sonnet, 60 for haiku
```

### `validate_model_name(model, context_agent, context_source)`

Validates a model name against the supported list. Fails fast with a clear error if invalid (REQ-F-18).

**Input**:

```yaml
model: string           # The model name to validate
context_agent: string   # Agent name for error messages (e.g., "validate")
context_source: string  # Where the model came from for error messages (e.g., "CLI flag", "env var DANTE_VALIDATE_MODEL", "config file")
```

**Output**:

```yaml
validated_model: string  # Normalized lowercase model name ("opus", "sonnet", "haiku")
```

**On invalid input**: Fail fast with clear error message (see Error Handling section).

---

## Constants

```yaml
VALID_MODELS: ["opus", "sonnet", "haiku"]

VALID_AGENTS: ["analyze", "write", "execute", "validate", "fix"]

MODEL_TIMEOUTS:
  opus: 180      # 3 minutes (REQ-NF-1, REQ-NF-2)
  sonnet: 120    # 2 minutes
  haiku: 60      # 1 minute

# Default model assignments per agent
# These MUST match the spec requirements:
#   REQ-F-1: validate -> opus (highest priority for categorization accuracy)
#   REQ-F-2: fix -> opus (high complexity, iterative reasoning)
#   REQ-F-3: write -> sonnet (complex but template-driven)
#   REQ-F-4: analyze -> sonnet (pattern matching and heuristics)
#   REQ-F-5: execute -> sonnet (command construction and output parsing)
DEFAULT_MODELS:
  analyze: "sonnet"    # REQ-F-4: Pattern matching and heuristics
  write: "sonnet"      # REQ-F-3: Complex but template-driven
  execute: "sonnet"    # REQ-F-5: Command construction and output parsing
  validate: "opus"     # REQ-F-1: Highest priority for categorization accuracy
  fix: "opus"          # REQ-F-2: High complexity, iterative reasoning
```

---

## Core Algorithm: `resolve_model()`

This is the complete resolution algorithm implementing REQ-F-22 (configuration precedence).

```
FUNCTION resolve_model(agent_name, project_root, cli_overrides):

    # ──────────────────────────────────────────────
    # Step 0: Validate agent name
    # ──────────────────────────────────────────────
    IF agent_name NOT IN VALID_AGENTS:
        FAIL with error:
            "Unknown agent '{agent_name}'."
            "Valid agents: analyze, write, execute, validate, fix"

    # ──────────────────────────────────────────────
    # Step 1: Check CLI override (highest priority)
    # ──────────────────────────────────────────────
    # CLI overrides come from command-line flags like --validate-model=sonnet
    # These always win because the user is making an explicit request.

    IF cli_overrides is not null AND cli_overrides is not empty:
        IF cli_overrides contains agent_name AND cli_overrides[agent_name] is not empty:
            model = validate_model_name(
                cli_overrides[agent_name],
                agent_name,
                "CLI flag --{agent_name}-model"
            )
            timeout = get_timeout_for_model(model)
            RETURN {
                resolved_model: model,
                timeout_seconds: timeout,
                resolution_source: "cli"
            }

    # ──────────────────────────────────────────────
    # Step 2: Check environment variable
    # ──────────────────────────────────────────────
    # Environment variables follow the pattern DANTE_{AGENT}_MODEL
    # (e.g., DANTE_VALIDATE_MODEL=opus)

    env_var_name = "DANTE_{uppercase(agent_name)}_MODEL"
    env_value = read_environment_variable(env_var_name)

    IF env_value is set AND env_value is not empty string:
        model = validate_model_name(
            env_value,
            agent_name,
            "environment variable {env_var_name}"
        )
        timeout = get_timeout_for_model(model)
        RETURN {
            resolved_model: model,
            timeout_seconds: timeout,
            resolution_source: "env"
        }

    # ──────────────────────────────────────────────
    # Step 3: Check config file
    # ──────────────────────────────────────────────
    # Load config using ConfigManager (see config-manager.md)
    # Config model_overrides are already validated during config load.

    config = load_config(project_root)
        # Uses ConfigManager: see config-manager.md load_config()
        # Returns validated config with model_overrides dict

    IF config has "model_overrides" AND config.model_overrides is not empty:
        IF config.model_overrides contains agent_name:
            model = config.model_overrides[agent_name]
            # Already validated by ConfigManager during load
            timeout = get_timeout_for_model(model)
            RETURN {
                resolved_model: model,
                timeout_seconds: timeout,
                resolution_source: "config"
            }

    # ──────────────────────────────────────────────
    # Step 4: Apply Defaults (lowest priority)
    # ──────────────────────────────────────────────
    # No CLI, env, or config override found. Use the default model
    # for this agent as defined in DEFAULT_MODELS.

    model = DEFAULT_MODELS[agent_name]

    timeout = get_timeout_for_model(model)
    RETURN {
        resolved_model: model,
        timeout_seconds: timeout,
        resolution_source: "default"
    }
```

---

## Timeout Resolution: `get_timeout_for_model()`

Returns the appropriate timeout in seconds for a given model. These timeouts are used by the orchestrator when spawning agents via the Task tool.

```
FUNCTION get_timeout_for_model(model):

    MODEL_TIMEOUTS = {
        "opus": 180,      # 3 minutes (REQ-NF-1 for validate, REQ-NF-2 for fix)
        "sonnet": 120,    # 2 minutes
        "haiku": 60       # 1 minute
    }

    IF model NOT IN MODEL_TIMEOUTS:
        # This should not happen if validate_model_name() was called first.
        # Defensive fallback to sonnet timeout.
        Log warning: "Unknown model '{model}' in get_timeout_for_model, using sonnet timeout (120s)"
        RETURN 120

    RETURN MODEL_TIMEOUTS[model]
```

### Timeout Rationale

| Model | Timeout | Rationale |
|-------|---------|-----------|
| opus | 180s | Opus is used for complex reasoning (validate, fix). These agents may need more time for deep analysis. REQ-NF-1 specifies validate-agent should complete within 120s, but we set 180s as the hard timeout to allow for edge cases. REQ-NF-2 specifies fix-agent within 180s. |
| sonnet | 120s | Sonnet is the balanced model. Current baseline shows agents averaging 60-90s, so 120s provides comfortable headroom. |
| haiku | 60s | Haiku is the fastest model. Tasks assigned to Haiku are expected to complete quickly. |

---

## Model Validation: `validate_model_name()`

Validates a model name against the whitelist and normalizes to lowercase. This is the central validation function used across all precedence levels (REQ-F-18).

```
FUNCTION validate_model_name(model, context_agent, context_source):

    VALID_MODELS = ["opus", "sonnet", "haiku"]

    # Normalize: lowercase, strip whitespace
    model_normalized = lowercase(strip(model))

    IF model_normalized NOT IN VALID_MODELS:
        FAIL with error:
            "Invalid model '{model}' for agent '{context_agent}'."
            "Supported models: opus, sonnet, haiku"
            "Source: {context_source}"

    RETURN model_normalized
```

### Validation Behavior by Source

| Source | On Invalid Model | Rationale |
|--------|-----------------|-----------|
| CLI flag | FAIL FAST with error | User made an explicit choice that cannot be fulfilled |
| Environment variable | FAIL FAST with error | Deliberate configuration that cannot be fulfilled |
| Config file | FAIL FAST with error | Explicit configuration that may indicate copy-paste error |
| Defaults | N/A (hardcoded, always valid) | Defaults are defined in this skill and always valid |

---

## Agent Validation

```
FUNCTION validate_agent_name(agent_name):

    VALID_AGENTS = ["analyze", "write", "execute", "validate", "fix"]

    IF agent_name NOT IN VALID_AGENTS:
        FAIL with error:
            "Unknown agent '{agent_name}'."
            "Valid agents: analyze, write, execute, validate, fix"

    RETURN agent_name
```

This validation happens at the entry of `resolve_model()` before any other checks.

---

## Orchestrator Integration Pattern

The orchestrator calls the resolver for each of the 5 agents during a test-loop execution. This section shows the complete integration flow.

### Initialization (once per test-loop execution)

```
# Step 1: Detect project root
project_root = detect_project_root()
    # Uses skills/project-detection/SKILL.md

# Step 2: Load config
config = load_config(project_root)
    # Uses config-manager.md

# Step 3: Parse CLI overrides into dict
cli_overrides = parse_cli_flags()
    # e.g., {"validate": "sonnet", "fix": "sonnet"}
    # Empty dict if no flags provided
```

### Per-Agent Resolution (before each agent launch)

```
# Resolve model for this agent
result = resolve_model(agent_name, project_root, cli_overrides)

# Display model selection
Output: "  {agent_name}-agent -> {result.resolved_model} ({result.resolution_source})"

# Launch agent with resolved model
Use Task tool:
    model: result.resolved_model
    timeout: result.timeout_seconds * 1000    # Convert to milliseconds for Task tool
    prompt: <agent instructions>
```

### Complete Example: Defaults with CLI Override

```
Input:
    agents: [analyze, write, execute, validate, fix]
    cli_overrides: {"validate": "sonnet"}
    env vars: DANTE_EXECUTE_MODEL=haiku
    config: model_overrides = {}

Resolution:
    analyze  -> resolve_model("analyze", ...) -> sonnet (default)
    write    -> resolve_model("write", ...)   -> sonnet (default)
    execute  -> resolve_model("execute", ...) -> haiku  (env)
    validate -> resolve_model("validate", ..) -> sonnet (cli)
    fix      -> resolve_model("fix", ...)     -> opus   (default)

Output:
    Model Selection:
      analyze-agent  -> sonnet (default)
      write-agent    -> sonnet (default)
      execute-agent  -> haiku  (env)
      validate-agent -> sonnet (cli)
      fix-agent      -> opus   (default)
```

---

## Edge Cases

### Edge Case 1: CLI Override for One Agent, Defaults for Others

**Scenario**: User passes `--validate-model=sonnet` but no other overrides.

**Behavior**: validate uses sonnet (CLI), fix uses opus (default), others use sonnet (default).

**Rationale**: CLI overrides are per-agent. One override does not affect other agents.

### Edge Case 2: Environment Variable with Mixed Case

**Scenario**: `DANTE_VALIDATE_MODEL=Opus` (capital O).

**Behavior**: `validate_model_name()` normalizes to lowercase `"opus"`. Resolution succeeds.

**Rationale**: Case-insensitive handling prevents user frustration from capitalization errors.

### Edge Case 3: Environment Variable Set to Empty String

**Scenario**: `DANTE_VALIDATE_MODEL=""` (set but empty).

**Behavior**: Empty string treated as "not set". Falls through to config file (Step 3).

**Rationale**: Some shell environments may set but not unset variables. Empty should not be treated as a valid model.

### Edge Case 4: Config File and Environment Variable Both Set

**Scenario**: Config has `model_overrides: {"validate": "haiku"}` and `DANTE_VALIDATE_MODEL=opus`.

**Behavior**: Environment variable wins (Step 2 before Step 3). Returns `opus`.

**Rationale**: Environment variables are more transient and immediate than config files. This matches standard Unix/Windows convention.

### Edge Case 5: All Precedence Levels Set for Same Agent

**Scenario**: CLI override = sonnet, env var = opus, config = haiku, default = opus. Agent = validate.

**Behavior**: CLI override wins. Returns `sonnet` (source: "cli").

**Rationale**: CLI is the most immediate and explicit user intent.

### Edge Case 6: Config Override Changes Default

**Scenario**: Config has `model_overrides: {"validate": "haiku"}`, but default for validate is opus.

**Behavior**: Config override wins (Step 3 before Step 4). Returns `haiku` (source: "config").

**Rationale**: Config file overrides are explicit user choices that take precedence over defaults. The user has deliberately chosen to override the default assignment for this agent.

### Edge Case 7: Invalid Agent Name

**Scenario**: Caller passes `agent_name = "reviewer"` (not a valid agent).

**Behavior**: Fail fast with error: `"Unknown agent 'reviewer'. Valid agents: analyze, write, execute, validate, fix"`

**Rationale**: Invalid agent names indicate a programming error in the caller. Fail fast to surface it.

### Edge Case 8: Null or Missing cli_overrides

**Scenario**: Caller passes `cli_overrides = null` or `cli_overrides = {}`.

**Behavior**: Step 1 is skipped entirely. Resolution continues to Step 2 (env var).

**Rationale**: Not all callers have CLI context (e.g., running programmatically without a CLI).

---

## Error Handling

### Invalid Model Name (REQ-F-18)

Fail fast with a clear error that includes the source of the invalid value.

**From CLI flag**:
```
ERROR: Invalid model in CLI flag

--validate-model='gpt4' is not a valid model.
Supported models: opus, sonnet, haiku

Usage: /test-loop --validate-model=opus
```

**From environment variable**:
```
ERROR: Invalid model in environment variable

DANTE_VALIDATE_MODEL='gpt4' is not a valid model.
Supported models: opus, sonnet, haiku

To fix:
  export DANTE_VALIDATE_MODEL=opus    # or sonnet, haiku
```

**From config file**:
```
ERROR: Invalid model configuration

Invalid model 'gpt4' for agent 'validate' in config file.
Config file: {project_root}/.claude/dante-config.json

Supported models: opus, sonnet, haiku

To fix:
1. Edit {project_root}/.claude/dante-config.json
2. Change the model name to one of: opus, sonnet, haiku
3. Run the command again
```

### Invalid Agent Name

```
ERROR: Unknown agent

Unknown agent 'reviewer'.
Valid agents: analyze, write, execute, validate, fix

This is likely a programming error in the caller.
```

### Config File Issues

Config file errors (missing, malformed) are handled by the ConfigManager sub-skill (see [config-manager.md](./config-manager.md)). The Model Resolver receives a valid config object (or defaults) and does not need to handle config file I/O errors directly.

---

## Implementation Checklist

When implementing the Model Resolver in a Claude Code agent context, use these tools:

### Reading Environment Variables

```
# Windows (cmd):
if defined DANTE_VALIDATE_MODEL (echo %DANTE_VALIDATE_MODEL%) else (echo __UNSET__)

# Unix/macOS (bash/zsh):
echo "${DANTE_VALIDATE_MODEL:-__UNSET__}"
```

Use the platform detected from the environment context (`Platform:` field) to select the appropriate command.

### Step-by-Step Implementation

- [ ] **Validate agent name**: Check agent_name against VALID_AGENTS list before any resolution
- [ ] **Check CLI overrides**: If cli_overrides dict contains agent_name with non-empty value, validate and return
- [ ] **Check env var**: Use Bash tool to read `DANTE_{AGENT}_MODEL`, validate if set
- [ ] **Load config**: Follow ConfigManager load pattern (see config-manager.md), check model_overrides
- [ ] **Apply defaults**: Look up DEFAULT_MODELS for the agent
- [ ] **Compute timeout**: Call get_timeout_for_model with the resolved model
- [ ] **Return result**: Return resolved_model, timeout_seconds, and resolution_source
- [ ] **Display result**: Output the resolution to the user in CLI format
- [ ] **Error messages**: Ensure all error messages include the source (CLI, env, config) and the invalid value

### Environment Variable Reading Pattern

For each agent, the environment variable name is constructed as:

```
agent_name = "validate"
env_var_name = "DANTE_" + uppercase(agent_name) + "_MODEL"
# Result: "DANTE_VALIDATE_MODEL"
```

All five environment variable names:

| Agent | Environment Variable |
|-------|---------------------|
| analyze | `DANTE_ANALYZE_MODEL` |
| write | `DANTE_WRITE_MODEL` |
| execute | `DANTE_EXECUTE_MODEL` |
| validate | `DANTE_VALIDATE_MODEL` |
| fix | `DANTE_FIX_MODEL` |

---

## Interaction with Other Sub-Skills

### Depends On

- **[Config Manager](./config-manager.md)**: Calls `load_config(project_root)` to read model_overrides from the config file (Step 3). The Config Manager handles file I/O, JSON parsing, and schema validation.

### Used By

- **Test Loop Orchestrator** (`subagents/test-loop-orchestrator.md`): Calls `resolve_model()` for each of the 5 agents before launching them via Task tool.
- **Commands** (`commands/test-loop.md`, `commands/test-generate.md`): Parse CLI flags and pass them as `cli_overrides` to the orchestrator, which passes them to `resolve_model()`.

### Call Chain

```
Orchestrator
    |
    +--> For each agent:
            ModelResolver.resolve_model(agent_name, project_root, cli_overrides)
                |
                +--> Step 1: Check cli_overrides dict
                +--> Step 2: Read env var (Bash tool)
                +--> Step 3: ConfigManager.load_config(project_root) -> check model_overrides
                +--> Step 4: Look up DEFAULT_MODELS[agent_name]
```

---

## Testing Checklist

### Precedence Tests

These tests verify that the resolution precedence order is correct (CLI > env > config > defaults).

- [ ] **PREC-TC01**: CLI override set for agent -> returns CLI value (source: "cli")
- [ ] **PREC-TC02**: No CLI, env var set for agent -> returns env var value (source: "env")
- [ ] **PREC-TC03**: No CLI, no env var, config override set for agent -> returns config value (source: "config")
- [ ] **PREC-TC04**: No CLI, no env var, no config override -> returns default (source: "default")
- [ ] **PREC-TC05**: All four levels set for same agent -> CLI wins
- [ ] **PREC-TC06**: CLI set for one agent, default for another -> independent resolution per agent
- [ ] **PREC-TC07**: Empty CLI override value ("") for agent -> treated as not set, falls through to env var
- [ ] **PREC-TC08**: Empty env var value ("") for agent -> treated as not set, falls through to config

### Default Model Tests

These tests verify correct default model assignments when no overrides are present.

- [ ] **DEF-TC01**: validate agent, no overrides -> opus (default)
- [ ] **DEF-TC02**: fix agent, no overrides -> opus (default)
- [ ] **DEF-TC03**: analyze agent, no overrides -> sonnet (default)
- [ ] **DEF-TC04**: write agent, no overrides -> sonnet (default)
- [ ] **DEF-TC05**: execute agent, no overrides -> sonnet (default)
- [ ] **DEF-TC06**: Config override for validate=haiku -> haiku (config overrides default)

### Timeout Tests

These tests verify correct timeout values for each model.

- [ ] **TO-TC01**: `get_timeout_for_model("opus")` returns 180
- [ ] **TO-TC02**: `get_timeout_for_model("sonnet")` returns 120
- [ ] **TO-TC03**: `get_timeout_for_model("haiku")` returns 60
- [ ] **TO-TC04**: Resolved model opus -> timeout_seconds = 180 in result
- [ ] **TO-TC05**: Resolved model sonnet -> timeout_seconds = 120 in result
- [ ] **TO-TC06**: Resolved model haiku -> timeout_seconds = 60 in result

### Validation Tests (REQ-F-18)

These tests verify that invalid model and agent names produce clear errors.

- [ ] **VAL-TC01**: Invalid model name "gpt4" in CLI -> fail fast with error message including "gpt4" and supported models
- [ ] **VAL-TC02**: Invalid model name "gpt4" in env var -> fail fast with error including env var name
- [ ] **VAL-TC03**: Invalid model name "gpt4" in config -> fail fast with error including config file path
- [ ] **VAL-TC04**: Valid model with wrong case "OPUS" -> normalized to "opus", accepted
- [ ] **VAL-TC05**: Valid model with whitespace " opus " -> normalized to "opus", accepted
- [ ] **VAL-TC06**: Invalid agent name "reviewer" -> fail fast with error listing valid agents
- [ ] **VAL-TC07**: Empty string as agent name -> fail fast with error
- [ ] **VAL-TC08**: Empty string as model name in CLI -> treated as not set, falls through

### End-to-End Scenarios

These tests simulate complete resolution for all 5 agents under specific conditions.

- [ ] **E2E-TC01**: No overrides -> validate=opus, fix=opus, others=sonnet (all source: default)
- [ ] **E2E-TC02**: `--validate-model=sonnet` CLI -> validate=sonnet(cli), fix=opus(default), others=sonnet(default)
- [ ] **E2E-TC03**: `DANTE_EXECUTE_MODEL=haiku` env -> execute=haiku(env), validate=opus(default), fix=opus(default), others=sonnet(default)
- [ ] **E2E-TC04**: Config override validate=haiku -> validate=haiku(config), fix=opus(default), others=sonnet(default)
- [ ] **E2E-TC05**: All agents overridden by env vars to haiku -> all agents=haiku(env)
- [ ] **E2E-TC06**: CLI override + env var + config + default all set for validate -> CLI wins

### Error Handling Tests

- [ ] **ERR-TC01**: Invalid model in CLI -> error message mentions "CLI flag"
- [ ] **ERR-TC02**: Invalid model in env var -> error message mentions env var name
- [ ] **ERR-TC03**: Invalid model in config -> error message mentions config file path
- [ ] **ERR-TC04**: Missing config file -> falls through to defaults (no error)
- [ ] **ERR-TC05**: Malformed config JSON -> ConfigManager returns defaults, resolution continues
- [ ] **ERR-TC06**: Invalid agent name -> error before any resolution attempts

---

## Spec Requirement Coverage

| Requirement | Description | How This Sub-Skill Covers It |
|-------------|-------------|------------------------------|
| REQ-F-1 | Opus for validate-agent | DEFAULT_MODELS["validate"] = "opus" |
| REQ-F-2 | Opus for fix-agent | DEFAULT_MODELS["fix"] = "opus" |
| REQ-F-3 | Sonnet for write-agent | DEFAULT_MODELS["write"] = "sonnet" |
| REQ-F-4 | Sonnet for analyze-agent | DEFAULT_MODELS["analyze"] = "sonnet" |
| REQ-F-5 | Sonnet for execute-agent | DEFAULT_MODELS["execute"] = "sonnet" |
| REQ-F-8 | Manual model override per agent | CLI override (Step 1) and env var (Step 2) |
| REQ-F-16 | Config file support | Config file check (Step 3) via ConfigManager |
| REQ-F-17 | Environment variable override | Env var check (Step 2) with `DANTE_{AGENT}_MODEL` |
| REQ-F-18 | Model name validation | `validate_model_name()` at every precedence level |
| REQ-F-22 | Configuration precedence | `resolve_model()` implements CLI > env > config > defaults |
| REQ-NF-1 | Validate-agent timeout | `get_timeout_for_model("opus")` returns 180s |
| REQ-NF-2 | Fix-agent timeout | `get_timeout_for_model("opus")` returns 180s |
| REQ-NF-7 | CLI override flags | CLI override support in Step 1 |

---

**Last Updated**: 2026-02-09
**Status**: Phase 1 - Foundation implementation
