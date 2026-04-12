---
name: model-resolver
description: Resolve the correct Claude model, timeout, and source for any agent by applying a 4-level precedence chain (CLI > env > config > defaults) with single-level fallback, model validation, and performance tracking for telemetry integration.
user-invocable: false
---

# Model Resolver Sub-Skill

**Parent Skill**: [Model Selection](./SKILL.md)
**Version**: 3.0.0
**Category**: Infrastructure
**Purpose**: Resolve the correct Claude model and timeout for any agent by applying the full configuration precedence chain: CLI override > environment variable > config file > defaults. Includes single-level fallback, strict model validation, and performance tracking fields for telemetry integration.

**Used By**: Test Loop Orchestrator, `/test-loop` command, `/test-generate` command

---

## Overview

The Model Resolver is the single entry point for all model resolution in the Teamsters plugin. No caller should directly check environment variables, read config files, or look up default tables. Instead, all resolution goes through `resolve_model()`, which returns the resolved model, timeout, and source in a single call.

### Design Principles

1. **Single entry point**: All model resolution goes through `resolve_model()`. No caller should directly check env vars, config, or defaults.
2. **Fail fast on invalid input**: Invalid model names or agent names produce clear errors immediately (REQ-F-9). The system never silently uses a wrong model.
3. **Transparent sourcing**: Every resolution result includes the source (cli, env, config, default) so the orchestrator can display it.
4. **Deterministic**: Given the same inputs and state, resolution always produces the same output.
5. **Stateless**: The resolver reads state but does not write state. Config persistence is delegated to ConfigManager.
6. **Single-level fallback**: On failure, fall back to sonnet exactly once. No infinite recursion, no multi-level cascading.
7. **Telemetry-ready**: Every resolution result includes performance tracking fields for integration with the metrics collector.

---

## Interface

### `resolve_model(agent_name, cli_override?, env_override?)`

The primary entry point. Resolves which Claude model to use for a given agent by walking the 4-level precedence chain.

**Input**:

```yaml
agent_name: string        # One of: "analyze", "write", "execute", "validate", "fix"
cli_override: string      # Optional. Model name from CLI flag (e.g., "opus"). May be null or empty.
env_override: string      # Optional. Model name from environment variable. May be null or empty.
                          # If not provided, the resolver reads TEAMSTERS_{AGENT}_MODEL directly.
```

**Output**:

```yaml
model: string             # Resolved model: one of "opus", "sonnet", "haiku"
timeout: integer          # Timeout in seconds appropriate for the resolved model
source: string            # Resolution source: one of "cli", "env", "config", "default"
agent_name: string        # Echo of the input agent name (for logging convenience)
timestamp: string         # ISO 8601 UTC timestamp of resolution (for telemetry)
resolution_chain: array   # Ordered list of sources checked (for debugging)
fallback_used: boolean    # Whether the fallback chain was activated
original_model: string    # If fallback was used, the originally requested model. Otherwise same as model.
```

### `get_timeout_for_model(model)`

Returns the appropriate timeout in seconds for a given model, using config-defined timeouts if available.

**Input**:

```yaml
model: string  # One of: "opus", "sonnet", "haiku"
```

**Output**:

```yaml
timeout_seconds: integer  # Default: 180 for opus, 120 for sonnet, 60 for haiku
```

### `validate_model_name(model, context_agent, context_source)`

Validates a model name against the allowed set. Fails fast with a clear error if invalid (REQ-F-9).

**Input**:

```yaml
model: string           # The model name to validate
context_agent: string   # Agent name for error messages (e.g., "validate")
context_source: string  # Where the model came from for error messages (e.g., "CLI flag", "env var")
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

# Default timeout mapping (can be overridden via config file timeouts section)
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
  analyze: "sonnet"    # REQ-F-4
  write: "sonnet"      # REQ-F-3
  execute: "sonnet"    # REQ-F-5
  validate: "opus"     # REQ-F-1
  fix: "opus"          # REQ-F-2

# Fallback model when the requested model fails at runtime
FALLBACK_MODEL: "sonnet"
```

---

## 4-Level Precedence Chain

Model resolution follows a strict 4-level precedence order. The first source that provides a value wins:

```
Level 1: CLI flag              (--validate-model=opus)        Highest priority
Level 2: Environment variable  (TEAMSTERS_VALIDATE_MODEL=opus)
Level 3: Config file           (.claude/teamsters-config.json)
Level 4: Defaults              (validate=opus, fix=opus, others=sonnet)
                                                               Lowest priority
```

### Why This Order

| Level | Source | Rationale |
|-------|--------|-----------|
| 1 | CLI flag | Most immediate and explicit user intent. User is actively choosing right now. |
| 2 | Environment variable | Semi-persistent configuration. User set it for this shell session or environment. |
| 3 | Config file | Project-level persistent configuration. Shared across the team via version control. |
| 4 | Defaults | Built-in safe defaults. Always available, never missing. |

---

## Core Algorithm: `resolve_model()`

```
FUNCTION resolve_model(agent_name, cli_override=null, env_override=null):

    resolution_start_time = current_utc_time()
    resolution_chain = []

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
    resolution_chain.append("cli")

    IF cli_override is not null AND cli_override is not empty string:
        model = validate_model_name(
            cli_override,
            agent_name,
            "CLI flag --{agent_name}-model"
        )
        timeout = get_timeout_for_model(model)
        RETURN build_result(
            model=model,
            timeout=timeout,
            source="cli",
            agent_name=agent_name,
            resolution_chain=resolution_chain,
            fallback_used=false,
            original_model=model,
            timestamp=resolution_start_time
        )

    # ──────────────────────────────────────────────
    # Step 2: Check environment variable
    # ──────────────────────────────────────────────
    resolution_chain.append("env")

    # If env_override was passed explicitly, use it.
    # Otherwise, read the environment variable directly.
    IF env_override is not null:
        env_value = env_override
    ELSE:
        env_var_name = "TEAMSTERS_{uppercase(agent_name)}_MODEL"
        env_value = read_environment_variable(env_var_name)

    IF env_value is set AND env_value is not empty string:
        model = validate_model_name(
            env_value,
            agent_name,
            "environment variable TEAMSTERS_{uppercase(agent_name)}_MODEL"
        )
        timeout = get_timeout_for_model(model)
        RETURN build_result(
            model=model,
            timeout=timeout,
            source="env",
            agent_name=agent_name,
            resolution_chain=resolution_chain,
            fallback_used=false,
            original_model=model,
            timestamp=resolution_start_time
        )

    # ──────────────────────────────────────────────
    # Step 3: Check config file
    # ──────────────────────────────────────────────
    resolution_chain.append("config")

    # Load config using ConfigManager (see config-manager.md)
    # Config is cached for session duration by ConfigManager.
    config = load_config(project_root)

    # Check the "models" section first (explicit per-agent overrides)
    IF config has "models" AND config.models is not empty:
        IF config.models contains agent_name:
            model = config.models[agent_name]
            # Already validated by ConfigManager during load
            timeout = get_timeout_for_model(model)
            RETURN build_result(
                model=model,
                timeout=timeout,
                source="config",
                agent_name=agent_name,
                resolution_chain=resolution_chain,
                fallback_used=false,
                original_model=model,
                timestamp=resolution_start_time
            )

    # ──────────────────────────────────────────────
    # Step 4: Apply defaults (lowest priority)
    # ──────────────────────────────────────────────
    resolution_chain.append("default")

    # Check config "defaults" section first (user may have overridden defaults)
    IF config has "defaults" AND config.defaults contains agent_name:
        model = config.defaults[agent_name]
    ELSE:
        model = DEFAULT_MODELS[agent_name]

    timeout = get_timeout_for_model(model)
    RETURN build_result(
        model=model,
        timeout=timeout,
        source="default",
        agent_name=agent_name,
        resolution_chain=resolution_chain,
        fallback_used=false,
        original_model=model,
        timestamp=resolution_start_time
    )
```

### `build_result()` Helper

Constructs the standardized result object with performance tracking fields:

```
FUNCTION build_result(model, timeout, source, agent_name, resolution_chain, fallback_used, original_model, timestamp):
    RETURN {
        model: model,
        timeout: timeout,
        source: source,
        agent_name: agent_name,
        timestamp: format_iso8601(timestamp),
        resolution_chain: resolution_chain,
        fallback_used: fallback_used,
        original_model: original_model
    }
```

---

## Fallback Chain

When an agent call fails at runtime (timeout, rate limit, API error), the orchestrator may invoke the fallback chain. The fallback is intentionally limited to ONE level to prevent infinite recursion.

### Fallback Rules

```
REQUESTED MODEL -> sonnet -> ERROR (stop)

Specifically:
  opus   -> falls back to sonnet
  haiku  -> falls back to sonnet
  sonnet -> NO FALLBACK (error: cannot fall back further)
```

### `resolve_fallback(original_result)`

Called by the orchestrator after an agent call fails and all retries are exhausted.

```
FUNCTION resolve_fallback(original_result):

    original_model = original_result.model

    # ── Guard: sonnet cannot fall back further ──
    IF original_model == FALLBACK_MODEL:
        FAIL with error:
            "Agent '{original_result.agent_name}' failed with model '{original_model}'."
            "No fallback available. Sonnet is the final fallback model."
            "Check the agent's task for errors or increase the timeout."

    # ── Guard: prevent infinite recursion ──
    IF original_result.fallback_used == true:
        FAIL with error:
            "Agent '{original_result.agent_name}' already used fallback."
            "Fallback chain is limited to ONE level to prevent infinite recursion."
            "Original model: {original_result.original_model}"
            "Fallback model: {original_result.model}"

    # ── Fall back to sonnet ──
    fallback_model = FALLBACK_MODEL
    fallback_timeout = get_timeout_for_model(fallback_model)

    Log warning: "WARNING: {original_result.agent_name} failed with {original_model}, falling back to {fallback_model}"

    RETURN build_result(
        model=fallback_model,
        timeout=fallback_timeout,
        source=original_result.source,    # Preserve original source for tracking
        agent_name=original_result.agent_name,
        resolution_chain=original_result.resolution_chain,
        fallback_used=true,
        original_model=original_model,
        timestamp=current_utc_time()
    )
```

### Fallback Scenarios

| Original Model | Failure Type | Fallback | Result |
|----------------|-------------|----------|--------|
| opus | Timeout after 180s | sonnet | Retry with sonnet (120s timeout) |
| opus | Rate limit | sonnet | Retry with sonnet |
| opus | API error | sonnet | Retry with sonnet |
| haiku | Timeout after 60s | sonnet | Retry with sonnet (120s timeout) |
| sonnet | Any failure | NONE | Error: no fallback available |
| opus (already fell back) | Second failure | NONE | Error: fallback already used |

---

## Timeout Resolution: `get_timeout_for_model()`

Returns the timeout for a model, checking config-defined timeouts first, then using built-in defaults.

```
FUNCTION get_timeout_for_model(model):

    # Check config-defined timeouts first
    config = get_cached_config()
    IF config is not null AND config has "timeouts" AND config.timeouts contains model:
        RETURN config.timeouts[model]

    # Fall back to built-in defaults
    BUILTIN_TIMEOUTS = {
        "opus": 180,
        "sonnet": 120,
        "haiku": 60
    }

    IF model NOT IN BUILTIN_TIMEOUTS:
        # Defensive fallback. Should not happen if validate_model_name() was called.
        Log warning: "Unknown model '{model}' in get_timeout_for_model, using sonnet timeout (120s)"
        RETURN 120

    RETURN BUILTIN_TIMEOUTS[model]
```

### Timeout Rationale

| Model | Default Timeout | Rationale |
|-------|-----------------|-----------|
| opus | 180s (3 min) | Used for complex reasoning (validate, fix). These agents may need deep analysis time. REQ-NF-2 specifies fix-agent within 180s. |
| sonnet | 120s (2 min) | Balanced model. Current baseline shows agents averaging 60-90s, so 120s provides headroom. |
| haiku | 60s (1 min) | Fastest model. Tasks assigned to haiku are expected to complete quickly. |

---

## Model Validation: `validate_model_name()`

Validates a model name against the allowed set and normalizes to lowercase. This is the central validation function used across all precedence levels (REQ-F-9).

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
            ""
            "To fix: use one of the supported model names (opus, sonnet, haiku)."

    RETURN model_normalized
```

### Validation Behavior by Source

| Source | On Invalid Model | Error Includes |
|--------|-----------------|----------------|
| CLI flag | FAIL FAST | Flag name (e.g., `--validate-model`) |
| Environment variable | FAIL FAST | Env var name (e.g., `TEAMSTERS_VALIDATE_MODEL`) |
| Config file | FAIL FAST | Config file path |
| Defaults | N/A (hardcoded) | Never invalid |

---

## Performance Tracking Fields

Every resolution result includes fields designed for integration with the telemetry system (`skills/telemetry/SKILL.md`) and the metrics collector (`metrics-collector.md`).

### Tracking Fields

| Field | Type | Purpose |
|-------|------|---------|
| `timestamp` | string (ISO 8601) | When the resolution occurred. Used for metrics correlation. |
| `resolution_chain` | array of strings | Ordered list of sources checked during resolution (e.g., `["cli", "env", "config", "default"]`). Useful for debugging why a particular model was selected. |
| `fallback_used` | boolean | Whether the fallback chain was activated. Tracks reliability issues with specific models. |
| `original_model` | string | If fallback was used, records the originally resolved model. Enables tracking of fallback frequency per model. |

### Telemetry Integration

The orchestrator passes these fields to the metrics collector after each agent execution:

```
AFTER agent execution:
    metrics_data = {
        agent_name: result.agent_name,
        model: result.model,
        original_model: result.original_model,
        source: result.source,
        fallback_used: result.fallback_used,
        resolution_chain: result.resolution_chain,
        resolution_timestamp: result.timestamp,
        execution_duration: measured_duration,
        execution_success: agent_succeeded
    }
    emit_metrics(project_root, metrics_data)
```

### Performance Tracking Use Cases

1. **Fallback frequency**: Track how often agents fall back from opus/haiku to sonnet. High fallback rates indicate model availability issues.
2. **Resolution source distribution**: Track what percentage of resolutions come from CLI, env, config, or defaults. Low config usage may indicate the config feature is undiscoverable.
3. **Model-duration correlation**: Correlate model selection with execution duration to validate timeout settings.

---

## Orchestrator Integration Pattern

### Initialization (once per test-loop execution)

```
# Step 1: Detect project root
project_root = detect_project_root()

# Step 2: Parse CLI overrides into per-agent values
cli_overrides = parse_cli_flags()
    # e.g., {"validate": "sonnet", "fix": "sonnet"}
```

### Per-Agent Resolution (before each agent launch)

```
# Resolve model for this agent
result = resolve_model(
    agent_name=agent_name,
    cli_override=cli_overrides.get(agent_name, null)
)

# Display model selection
Output: "  {agent_name}-agent -> {result.model} ({result.source})"

# Launch agent with resolved model
Use Task tool:
    model: result.model
    timeout: result.timeout * 1000    # Convert seconds to milliseconds
    prompt: <agent instructions>
```

### Complete Example

```
Input:
    agents: [analyze, write, execute, validate, fix]
    cli_overrides: {"validate": "sonnet"}
    env vars: TEAMSTERS_EXECUTE_MODEL=haiku
    config: models = {}

Resolution:
    analyze  -> resolve_model("analyze")              -> sonnet (default)
    write    -> resolve_model("write")                -> sonnet (default)
    execute  -> resolve_model("execute")              -> haiku  (env)
    validate -> resolve_model("validate", cli="sonnet") -> sonnet (cli)
    fix      -> resolve_model("fix")                  -> opus   (default)

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

**Behavior**: validate uses sonnet (cli), fix uses opus (default), others use sonnet (default).

**Rationale**: CLI overrides are per-agent. One override does not affect other agents.

### Edge Case 2: Environment Variable with Mixed Case

**Scenario**: `TEAMSTERS_VALIDATE_MODEL=Opus` (capital O).

**Behavior**: `validate_model_name()` normalizes to lowercase `"opus"`. Resolution succeeds.

### Edge Case 3: Environment Variable Set to Empty String

**Scenario**: `TEAMSTERS_VALIDATE_MODEL=""` (set but empty).

**Behavior**: Empty string treated as "not set". Falls through to config file (Step 3).

### Edge Case 4: Config File and Environment Variable Both Set

**Scenario**: Config has `models: {"validate": "haiku"}` and `TEAMSTERS_VALIDATE_MODEL=opus`.

**Behavior**: Environment variable wins (Step 2 before Step 3). Returns `opus` (source: "env").

### Edge Case 5: All Precedence Levels Set for Same Agent

**Scenario**: CLI = sonnet, env = opus, config = haiku, default = opus. Agent = validate.

**Behavior**: CLI override wins. Returns `sonnet` (source: "cli").

### Edge Case 6: Fallback After Timeout

**Scenario**: validate-agent launched with opus (180s timeout). Agent times out.

**Behavior**: Orchestrator calls `resolve_fallback()`. Returns sonnet (120s timeout). `fallback_used=true`, `original_model="opus"`.

### Edge Case 7: Double Fallback Attempt (Blocked)

**Scenario**: validate-agent fails with opus, falls back to sonnet, sonnet also fails.

**Behavior**: `resolve_fallback()` detects `fallback_used=true` and refuses. Error: "Fallback chain is limited to ONE level."

### Edge Case 8: Sonnet Agent Fails (No Fallback Available)

**Scenario**: write-agent (model=sonnet) fails after all retries.

**Behavior**: `resolve_fallback()` detects model is already sonnet. Error: "No fallback available."

### Edge Case 9: env_override Parameter Passed Explicitly

**Scenario**: Caller passes `env_override="haiku"` to `resolve_model()`.

**Behavior**: The resolver uses the provided value instead of reading the environment variable. This enables testing without modifying the actual environment.

### Edge Case 10: Config Overrides Default Model Assignments

**Scenario**: Config file has `defaults: {"validate": "haiku"}` but no entry in `models`.

**Behavior**: Step 3 (config `models` section) finds no override. Step 4 checks config `defaults` section, finds `validate=haiku`. Returns haiku (source: "default").

---

## Error Handling

### Invalid Model Name (REQ-F-9)

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

TEAMSTERS_VALIDATE_MODEL='gpt4' is not a valid model.
Supported models: opus, sonnet, haiku

To fix:
  export TEAMSTERS_VALIDATE_MODEL=opus    # or sonnet, haiku
```

**From config file**:
```
ERROR: Invalid model configuration

Invalid model 'gpt4' for agent 'validate' in config file.
Config file: {project_root}/.claude/teamsters-config.json

Supported models: opus, sonnet, haiku

To fix:
1. Edit {project_root}/.claude/teamsters-config.json
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

### Fallback Exhausted

```
ERROR: Agent execution failed - no fallback available

Agent 'write' failed with model 'sonnet'.
Sonnet is the final fallback model. No further fallback is available.

Troubleshooting:
1. Check the agent's task for errors in the prompt or instructions
2. Increase the timeout in .claude/teamsters-config.json
3. Check for API rate limiting or service outages
4. Review the agent's output for actionable error messages
```

### Config File Issues

Config file errors (missing, malformed) are handled by the ConfigManager sub-skill (see [config-manager.md](./config-manager.md)). The Model Resolver receives a valid config object (or defaults) and does not handle config file I/O errors directly.

---

## Implementation Checklist

When implementing the Model Resolver in a Claude Code agent context:

### Core Resolution

- [ ] **Validate agent name**: Check agent_name against VALID_AGENTS list before any resolution
- [ ] **Check CLI override**: If cli_override is not null/empty, validate and return with source "cli"
- [ ] **Check env var**: Read `TEAMSTERS_{AGENT}_MODEL` or use env_override parameter, validate if set
- [ ] **Check config models**: Load config via ConfigManager, check `models` section
- [ ] **Apply defaults**: Check config `defaults` section, then fall back to DEFAULT_MODELS
- [ ] **Compute timeout**: Call `get_timeout_for_model()` with resolved model

### Fallback Chain

- [ ] **Single-level fallback**: Implement `resolve_fallback()` with ONE level only
- [ ] **Guard against double fallback**: Check `fallback_used` flag before allowing fallback
- [ ] **Guard against sonnet fallback**: Reject fallback when model is already sonnet
- [ ] **Preserve original model**: Set `original_model` field when fallback is used

### Performance Tracking

- [ ] **Timestamp**: Record ISO 8601 UTC timestamp at start of resolution
- [ ] **Resolution chain**: Build ordered list of sources checked
- [ ] **Fallback tracking**: Set `fallback_used` and `original_model` fields

### Validation

- [ ] **Model name validation**: Normalize to lowercase, strip whitespace, check against VALID_MODELS
- [ ] **Error messages**: Include source (CLI, env, config) and invalid value in all error messages
- [ ] **Clear fix instructions**: Every error message includes actionable steps to resolve

### Environment Variable Reading

For each agent, the environment variable name is:

```
agent_name = "validate"
env_var_name = "TEAMSTERS_" + uppercase(agent_name) + "_MODEL"
# Result: "TEAMSTERS_VALIDATE_MODEL"
```

| Agent | Environment Variable |
|-------|---------------------|
| analyze | `TEAMSTERS_ANALYZE_MODEL` |
| write | `TEAMSTERS_WRITE_MODEL` |
| execute | `TEAMSTERS_EXECUTE_MODEL` |
| validate | `TEAMSTERS_VALIDATE_MODEL` |
| fix | `TEAMSTERS_FIX_MODEL` |

---

## Testing Checklist

### Precedence Tests

- [ ] **PREC-TC01**: CLI override set -> returns CLI value (source: "cli")
- [ ] **PREC-TC02**: No CLI, env var set -> returns env var value (source: "env")
- [ ] **PREC-TC03**: No CLI, no env, config models set -> returns config value (source: "config")
- [ ] **PREC-TC04**: No CLI, no env, no config -> returns default (source: "default")
- [ ] **PREC-TC05**: All four levels set -> CLI wins
- [ ] **PREC-TC06**: CLI for one agent, default for another -> independent resolution
- [ ] **PREC-TC07**: Empty CLI override ("") -> treated as not set, falls through
- [ ] **PREC-TC08**: Empty env var ("") -> treated as not set, falls through

### Default Model Tests

- [ ] **DEF-TC01**: validate, no overrides -> opus (default)
- [ ] **DEF-TC02**: fix, no overrides -> opus (default)
- [ ] **DEF-TC03**: analyze, no overrides -> sonnet (default)
- [ ] **DEF-TC04**: write, no overrides -> sonnet (default)
- [ ] **DEF-TC05**: execute, no overrides -> sonnet (default)

### Timeout Tests

- [ ] **TO-TC01**: `get_timeout_for_model("opus")` returns 180
- [ ] **TO-TC02**: `get_timeout_for_model("sonnet")` returns 120
- [ ] **TO-TC03**: `get_timeout_for_model("haiku")` returns 60
- [ ] **TO-TC04**: Config-defined timeout overrides default
- [ ] **TO-TC05**: Unknown model falls back to 120 (sonnet timeout)

### Fallback Tests

- [ ] **FB-TC01**: opus fails -> fallback to sonnet, `fallback_used=true`
- [ ] **FB-TC02**: haiku fails -> fallback to sonnet, `fallback_used=true`
- [ ] **FB-TC03**: sonnet fails -> error "no fallback available"
- [ ] **FB-TC04**: Double fallback attempt -> error "already used fallback"
- [ ] **FB-TC05**: Fallback preserves `original_model` field
- [ ] **FB-TC06**: Fallback updates timeout to sonnet timeout

### Validation Tests (REQ-F-9)

- [ ] **VAL-TC01**: Invalid model "gpt4" in CLI -> fail fast with source info
- [ ] **VAL-TC02**: Invalid model "gpt4" in env var -> fail fast with env var name
- [ ] **VAL-TC03**: Invalid model "gpt4" in config -> fail fast with config path
- [ ] **VAL-TC04**: "OPUS" (uppercase) -> normalized to "opus", accepted
- [ ] **VAL-TC05**: " opus " (whitespace) -> normalized to "opus", accepted
- [ ] **VAL-TC06**: Invalid agent "reviewer" -> fail fast with valid agents list
- [ ] **VAL-TC07**: Empty agent name -> fail fast

### Performance Tracking Tests

- [ ] **PT-TC01**: Result contains `timestamp` field in ISO 8601 format
- [ ] **PT-TC02**: Result contains `resolution_chain` with sources checked
- [ ] **PT-TC03**: `fallback_used` is false on normal resolution
- [ ] **PT-TC04**: `fallback_used` is true after fallback
- [ ] **PT-TC05**: `original_model` matches `model` when no fallback
- [ ] **PT-TC06**: `original_model` differs from `model` after fallback

### End-to-End Scenarios

- [ ] **E2E-TC01**: No overrides -> validate=opus, fix=opus, others=sonnet
- [ ] **E2E-TC02**: CLI `--validate-model=sonnet` -> validate=sonnet(cli), others unchanged
- [ ] **E2E-TC03**: Env `TEAMSTERS_EXECUTE_MODEL=haiku` -> execute=haiku(env), others unchanged
- [ ] **E2E-TC04**: Config override validate=haiku -> validate=haiku(config)
- [ ] **E2E-TC05**: All agents overridden by env to haiku -> all haiku(env)
- [ ] **E2E-TC06**: CLI + env + config + default all set -> CLI wins

---

## Interaction with Other Sub-Skills

### Depends On

- **[Config Manager](./config-manager.md)**: Calls `load_config()` to read model overrides, default assignments, and timeout values from the config file. The Config Manager handles file I/O, JSON parsing, schema validation, and session caching.

### Used By

- **Test Loop Orchestrator** (`subagents/test-loop-orchestrator.md`): Calls `resolve_model()` for each agent and `resolve_fallback()` on failure.
- **Commands** (`commands/test-loop.md`, `commands/test-generate.md`): Parse CLI flags and pass them as cli_override parameters.
- **Metrics Collector** (`metrics-collector.md`): Receives performance tracking fields from resolution results.

### Call Chain

```
Orchestrator
    |
    +--> For each agent:
            ModelResolver.resolve_model(agent_name, cli_override, env_override)
                |
                +--> Step 1: Check cli_override parameter
                +--> Step 2: Check env_override or read TEAMSTERS_{AGENT}_MODEL
                +--> Step 3: ConfigManager.load_config() -> check models section
                +--> Step 4: Check config defaults, then DEFAULT_MODELS
                |
                +--> On failure: ModelResolver.resolve_fallback(original_result)
                        |
                        +--> Guard: not already sonnet
                        +--> Guard: not already used fallback
                        +--> Return sonnet with fallback_used=true
```

---

## Spec Requirement Coverage

| Requirement | Description | How This Sub-Skill Covers It |
|-------------|-------------|------------------------------|
| REQ-F-1 | Opus for validate-agent | DEFAULT_MODELS["validate"] = "opus" |
| REQ-F-2 | Opus for fix-agent | DEFAULT_MODELS["fix"] = "opus" |
| REQ-F-3 | Sonnet for write-agent | DEFAULT_MODELS["write"] = "sonnet" |
| REQ-F-4 | Sonnet for analyze-agent | DEFAULT_MODELS["analyze"] = "sonnet" |
| REQ-F-5 | Sonnet for execute-agent | DEFAULT_MODELS["execute"] = "sonnet" |
| REQ-F-8 | Manual model override | CLI override (Step 1) and env var (Step 2) |
| REQ-F-9 | Model name validation | `validate_model_name()` at every precedence level |
| REQ-F-10 | Configuration precedence | 4-level precedence chain: CLI > env > config > defaults |
| REQ-NF-1 | Validate-agent timeout | `get_timeout_for_model("opus")` returns 180s |
| REQ-NF-2 | Fix-agent timeout | `get_timeout_for_model("opus")` returns 180s |
| REQ-NF-3 | Fallback on failure | `resolve_fallback()` with single-level sonnet fallback |
| REQ-NF-4 | Retry with backoff | Orchestrator retries before calling fallback |

---

**Last Updated**: 2026-03-25
**Status**: Phase 2 - Extended resolver with fallback chain and telemetry (v3)
