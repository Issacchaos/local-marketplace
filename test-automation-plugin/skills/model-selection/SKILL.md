---
name: model-selection
description: Resolve the optimal Claude model (Opus, Sonnet, or Haiku) for each agent based on configuration precedence and runtime overrides. Use when launching agents to determine which model to use based on task complexity and user preferences.
user-invocable: false
---

# Model Selection Skill

**Version**: 2.0.0
**Category**: Infrastructure
**Purpose**: Resolve the optimal Claude model (Opus, Sonnet, or Haiku) for each agent based on configuration precedence and runtime overrides

**Used By**: Test Loop Orchestrator, `/test-loop` command, `/test-generate` command

---

## Overview

The Model Selection Skill provides centralized model resolution for all five Dante agents (analyze, write, execute, validate, fix). Instead of hardcoding a single model in each agent's frontmatter, the orchestrator uses this skill to dynamically resolve which Claude model each agent should use at runtime.

This skill is critical for:
- **Performance optimization**: Assigning higher-capability models (Opus) to complex agents (validate, fix) while using efficient models (Sonnet, Haiku) for simpler agents (execute)
- **User configurability**: Allowing per-agent model overrides via CLI flags, environment variables, or config file
- **Graceful degradation**: Falling back to Sonnet when higher-tier models fail or are unavailable

### Key Principle

Model resolution happens at the **orchestrator level**, not inside agents. Agents remain unchanged with `model: sonnet` in their frontmatter. The orchestrator resolves the actual model and passes it via the Task tool's `model` parameter.

---

## Skill Interface

### Input

```yaml
agent_name: Name of the agent to resolve model for (analyze, write, execute, validate, fix)
project_root: Absolute path to the project root directory
cli_overrides: Optional dict of per-agent model overrides from CLI flags
```

### Output

```yaml
resolved_model: The model to use for this agent (opus, sonnet, or haiku)
timeout_seconds: Timeout in seconds appropriate for the resolved model
resolution_source: Where the model was resolved from (cli, env, config, default)
```

---

## Configuration Precedence (REQ-F-10)

Model resolution follows a strict precedence order. The first source that provides a value wins:

```
1. CLI override       (--validate-model=sonnet)     Highest priority
2. Environment var    (DANTE_VALIDATE_MODEL=opus)
3. Config file        (.claude/dante-config.json model_overrides)
4. Defaults           (validate=opus, fix=opus, others=sonnet)
          |
          v
   Resolved model     Lowest priority = defaults
```

### Precedence Rules

1. **CLI override** (REQ-F-8, REQ-NF-6): User passes `--validate-model=sonnet` on command line. This always wins.
2. **Environment variable** (REQ-F-7): `DANTE_{AGENT}_MODEL` environment variable is set (e.g., `DANTE_VALIDATE_MODEL=opus`).
3. **Config file** (REQ-F-6): The `model_overrides` section in `{project_root}/.claude/dante-config.json` specifies a model for this agent.
4. **Defaults**: Return the default model for this agent (see Default Model Assignments below).

---

## Supported Models

```yaml
valid_models:
  - opus      # Highest capability, used for complex reasoning (validate, fix)
  - sonnet    # Balanced capability, used for most agents (analyze, write, execute)
  - haiku     # Fastest, lowest cost, suitable for simple tasks

model_timeouts:
  opus: 180     # 3 minutes (REQ-NF-1, REQ-NF-2)
  sonnet: 120   # 2 minutes
  haiku: 60     # 1 minute
```

Any model name not in the valid list must be rejected immediately with a clear error message (REQ-F-9):

```
Invalid model 'gpt4' for agent 'validate'. Supported models: opus, sonnet, haiku
```

---

## Default Model Assignments

| Agent    | Default Model | Rationale |
|----------|--------------|-----------|
| analyze  | sonnet       | Pattern matching and heuristics (REQ-F-4) |
| write    | sonnet       | Complex but template-driven (REQ-F-3) |
| execute  | sonnet       | Command construction and output parsing (REQ-F-5) |
| validate | opus         | Highest priority for categorization accuracy (REQ-F-1) |
| fix      | opus         | High complexity, iterative reasoning (REQ-F-2) |

---

## Valid Agents

```yaml
valid_agents:
  - analyze
  - write
  - execute
  - validate
  - fix
```

---

## Sub-Skills

### Config Manager

**File**: [config-manager.md](./config-manager.md)

Handles loading, validation, and persistence of the `.claude/dante-config.json` configuration file. Provides:

- Config file loading with graceful fallback to defaults
- Schema validation for model names against whitelist (REQ-F-9)
- Atomic write pattern for config persistence (temp file + rename)
- Environment variable override resolution (REQ-F-7)
- Malformed JSON handling (log warning, return defaults)

### Model Resolver

**File**: [model-resolver.md](./model-resolver.md)

The integration point that ties together ConfigManager with the full precedence logic. Provides:

- `resolve_model(agent_name, project_root, cli_overrides)` entry point (REQ-F-10)
- Full precedence chain: CLI override > env var > config file > defaults
- `get_timeout_for_model(model)` for timeout calculation (REQ-NF-1, REQ-NF-2)
- `validate_model_name(model, context_agent, context_source)` for fail-fast validation (REQ-F-9)
- Detailed edge cases, error messages, and structured testing checklist

### Metrics Collector

**File**: [metrics-collector.md](./metrics-collector.md)

Non-blocking metrics tracking for agent execution data. Provides:

- Append-only Markdown metrics file at `{project_root}/.claude/dante-metrics.md` (REQ-F-12, REQ-F-15)
- Non-blocking wrapper: exceptions in metrics writing log warning, never halt workflow (REQ-F-13)
- Metrics schema: timestamp, agent_name, model_used, duration, success (REQ-F-11, REQ-F-14)
- `DANTE_DISABLE_METRICS` environment variable to opt out

---

## Model Resolution Algorithm

When the orchestrator needs to determine which model to use for an agent, follow these steps:

### Step 1: Check CLI Override

```
IF cli_overrides dict contains agent_name AND value is not empty:
    model = cli_overrides[agent_name]
    Validate model against whitelist ["opus", "sonnet", "haiku"]
    IF invalid: FAIL FAST with error message (REQ-F-9)
    RETURN model (source: "cli")
```

### Step 2: Check Environment Variable

```
Read environment variable: DANTE_{AGENT_NAME_UPPER}_MODEL
Example: For agent "validate", check DANTE_VALIDATE_MODEL

IF variable is set AND not empty:
    model = lowercase(variable value)
    Validate model against whitelist
    IF invalid: FAIL FAST with error message (REQ-F-9)
    RETURN model (source: "env")
```

### Step 3: Check Config File

```
Load config from {project_root}/.claude/dante-config.json
(See config-manager.md for loading details)

IF config has "model_overrides" section:
    IF model_overrides contains agent_name:
        model = model_overrides[agent_name]
        (Already validated during config load)
        RETURN model (source: "config")
```

### Step 4: Apply Defaults

```
RETURN DEFAULT_MODELS[agent_name] (source: "default")

DEFAULT_MODELS:
  analyze  -> sonnet
  write    -> sonnet
  execute  -> sonnet
  validate -> opus
  fix      -> opus
```

---

## Environment Variable Override Pattern (REQ-F-7)

Environment variables follow the naming convention `DANTE_{AGENT}_MODEL`:

```bash
# Per-agent model overrides
DANTE_ANALYZE_MODEL=sonnet
DANTE_WRITE_MODEL=sonnet
DANTE_EXECUTE_MODEL=haiku
DANTE_VALIDATE_MODEL=opus
DANTE_FIX_MODEL=opus
```

Environment variable values are case-insensitive. The system normalizes to lowercase before validation.

---

## Usage in Orchestrator

### Initialization

At the start of a test-loop execution:

```markdown
1. Detect project root (use skills/project-detection/SKILL.md)
2. Load config (use skills/model-selection/config-manager.md)
3. Display model assignments in CLI output
```

### Before Each Agent Launch

```markdown
1. Resolve model for this agent:
   - Call model resolution algorithm with (agent_name, project_root, cli_overrides)
   - Get back: resolved_model, timeout_seconds, resolution_source

2. Display model in CLI output (REQ-NF-5):
   "Running validate-agent (opus)..."
   "Running execute-agent (sonnet)..."

3. Launch agent via Task tool with resolved model:
   - subagent_type: "general-purpose"
   - model: <resolved_model>
   - timeout: <timeout_seconds>
   - prompt: <agent instructions>
```

### Example CLI Output

```
Model Selection:
  analyze-agent  -> sonnet (default)
  write-agent    -> sonnet (default)
  execute-agent  -> sonnet (default)
  validate-agent -> opus   (default)
  fix-agent      -> opus   (default)

Running analyze-agent (sonnet)...
Running write-agent (sonnet)...
Running execute-agent (sonnet)...
Running validate-agent (opus)...
Running fix-agent (opus)...
```

---

## Retry and Fallback (REQ-NF-3, REQ-NF-4)

If an agent call fails with a model (timeout, rate limit, API error):

```markdown
1. Retry up to 3 times with exponential backoff:
   - Attempt 1: wait 1 second
   - Attempt 2: wait 2 seconds
   - Attempt 3: wait 4 seconds

2. After all retries exhausted:
   - IF current model is NOT "sonnet":
     - Fall back to "sonnet"
     - Display warning: "WARNING: {agent_name} failed with {model}, falling back to sonnet"
     - Retry once with sonnet
   - IF current model IS "sonnet":
     - Raise error (cannot fall back further)
```

---

## Error Handling

### Invalid Model Name (REQ-F-9)

If a model name is not in `["opus", "sonnet", "haiku"]`, fail fast:

```
Invalid model '{model}' for agent '{agent_name}'.
Supported models: opus, sonnet, haiku

Source: {where the invalid name came from: CLI flag, env var, config file}
```

### Invalid Agent Name

If an agent name is not in `["analyze", "write", "execute", "validate", "fix"]`:

```
Unknown agent '{agent_name}'.
Valid agents: analyze, write, execute, validate, fix
```

### Config File Missing

Not an error. Fall through to defaults. Log informational message:

```
No config file found at {project_root}/.claude/dante-config.json, using defaults.
```

### Config File Malformed

Log warning, use defaults (REQ-F-16):

```
WARNING: Malformed config file at {project_root}/.claude/dante-config.json.
Using default model assignments.
```

---

## Integration with Other Skills

### Uses

- **Project Detection** (`skills/project-detection/SKILL.md`): To find `project_root` for config file location
- **State Management** (`skills/state-management/SKILL.md`): Config stored in same `.claude/` directory as state files

### Used By

- **Test Loop Orchestrator** (`subagents/test-loop-orchestrator.md`): Resolves models before each agent launch
- **Commands** (`commands/test-loop.md`, `commands/test-generate.md`): Parse CLI override flags

### Does Not Modify

- **Agent files** (`agents/*.md`): Agent frontmatter stays at `model: sonnet`. Model override happens at Task tool level.
- **State files** (`.claude/.test-loop-state.md`): Model selection is a runtime concern, not persisted in workflow state (REQ-NF-11).

---

## Testing Checklist

For acceptance validation:

- [ ] Config file loads correctly from `{project_root}/.claude/dante-config.json`
- [ ] Missing config file falls back to defaults gracefully
- [ ] Malformed JSON in config file logs warning and returns defaults (REQ-F-16)
- [ ] Model names validated against whitelist `["opus", "sonnet", "haiku"]` (REQ-F-9)
- [ ] Invalid model name produces clear error and fails fast
- [ ] Environment variable `DANTE_{AGENT}_MODEL` overrides config file (REQ-F-7)
- [ ] CLI override takes highest precedence (REQ-F-10)
- [ ] Precedence order verified: CLI > env > config > defaults
- [ ] Default assignments: validate=opus, fix=opus, others=sonnet
- [ ] Config file saved atomically (temp file + rename)
- [ ] Timeout values correct: opus=180s, sonnet=120s, haiku=60s
- [ ] Metrics written to `.claude/dante-metrics.md` after each agent execution (REQ-F-12)
- [ ] Metrics failure does not halt execution (REQ-F-13)

---

## Spec Requirement Coverage

| Requirement | Description | Covered By |
|-------------|-------------|------------|
| REQ-F-1 | Opus for validate-agent | Default model assignments |
| REQ-F-2 | Opus for fix-agent | Default model assignments |
| REQ-F-3 | Sonnet for write-agent | Default model assignments |
| REQ-F-4 | Sonnet for analyze-agent | Default model assignments |
| REQ-F-5 | Sonnet for execute-agent | Default model assignments |
| REQ-F-6 | Config file support | config-manager.md |
| REQ-F-7 | Environment variable overrides | Environment Variable Override Pattern |
| REQ-F-8 | CLI override flags | CLI override in precedence |
| REQ-F-9 | Model name validation | Validation in resolution algorithm |
| REQ-F-10 | Configuration precedence | Configuration Precedence section |
| REQ-F-11 | Per-agent execution metrics | metrics-collector.md |
| REQ-F-12 | Metrics appended to Markdown file | metrics-collector.md |
| REQ-F-13 | Non-blocking metrics collection | metrics-collector.md |
| REQ-F-14 | Timestamp in metrics entries | metrics-collector.md |
| REQ-F-15 | Markdown table format for metrics | metrics-collector.md |
| REQ-F-16 | Malformed config handling | Error Handling section |
| REQ-NF-1 | Validate-agent timeout (120s) | Model timeouts |
| REQ-NF-2 | Fix-agent timeout (180s) | Model timeouts |
| REQ-NF-3 | Fallback on failure | Retry and Fallback section |
| REQ-NF-4 | Retry with backoff | Retry and Fallback section |
| REQ-NF-5 | Display model in CLI | Usage in Orchestrator section |
| REQ-NF-6 | CLI override flags | CLI override in precedence |
| REQ-NF-7 | Documentation | This skill document |
| REQ-NF-8 | Centralized model selection | This skill (single entry point) |
| REQ-NF-9 | Testable via integration tests | Testing Checklist section |
| REQ-NF-10 | Agent interface unchanged | Integration section |
| REQ-NF-11 | State file unchanged | Integration section |

---

## Future Enhancements

- Dynamic model routing based on task complexity (auto-detect when Opus is needed)
- Support for additional models as they become available
- Per-iteration model escalation (start with Sonnet, escalate to Opus on failures)
- Cost tracking integration with MetricsCollector

---

**Last Updated**: 2026-02-10
**Status**: Phase 1 - Foundation implementation (v2)
