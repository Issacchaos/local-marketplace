# Model Selection Guide

Configure which Claude model each Dante agent uses for test generation, execution, and validation.

---

## Quick Start

Out of the box, Dante assigns optimized models to each agent -- no configuration needed. If you want to customize, pick the method that fits your workflow:

**Override a single agent for one run (CLI flag):**

```bash
/test-loop src/ --validate-model=sonnet
```

**Override persistently for a project (config file):**

Create `.claude/dante-config.json` in your project root:

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

**Override via environment variable (CI or shell profile):**

```bash
export DANTE_VALIDATE_MODEL=sonnet
export DANTE_FIX_MODEL=sonnet
```

Then run `/test-loop` or `/test-generate` as usual.

---

## Default Model Assignments

Each of Dante's five agents has a default model chosen for the type of work it performs:

| Agent | Default Model | Why |
|-------|---------------|-----|
| analyze | sonnet | Pattern matching and heuristics -- Sonnet handles this efficiently |
| write | sonnet | Test generation is complex but template-driven -- Sonnet provides a good balance of quality and speed |
| execute | sonnet | Command construction and output parsing -- straightforward reasoning |
| validate | **opus** | Categorizing test results (source bug vs. test bug) requires the highest accuracy -- Opus excels at nuanced judgment |
| fix | **opus** | Iterative bug fixing requires deep, multi-step reasoning -- Opus produces the most reliable fixes |

The validate and fix agents default to Opus because errors in categorization or fix attempts can cascade through the workflow. The other three agents default to Sonnet, which provides a good balance of capability and speed for their workloads.

---

## Supported Models

| Model | Characteristics | Best For |
|-------|----------------|----------|
| **opus** | Highest capability, deeper reasoning | Complex categorization (validate), iterative fixing (fix) |
| **sonnet** | Balanced capability and speed | Most agents -- analysis, generation, execution |
| **haiku** | Fastest, most efficient | Simple tasks where speed matters more than depth |

---

## Configuration Methods

You can override the default model for any agent using three methods. They follow a strict precedence order -- the first one that provides a value wins.

### Precedence Order (Highest to Lowest)

```
1. CLI flags              --validate-model=sonnet         (wins over everything)
2. Environment variables  DANTE_VALIDATE_MODEL=opus       (wins over config + defaults)
3. Config file            .claude/dante-config.json       (wins over defaults)
4. Built-in defaults      validate=opus, fix=opus, etc.   (used when nothing else is set)
```

If you set the same agent's model at multiple levels, the highest-priority one takes effect. For example, a CLI flag always overrides an environment variable, which always overrides the config file.

---

### CLI Flags

Pass a `--<agent>-model` flag to `/test-loop` or `/test-generate` to override a specific agent's model for that run.

**Available flags:**

| Flag | Agent |
|------|-------|
| `--analyze-model <model>` | analyze |
| `--write-model <model>` | write |
| `--execute-model <model>` | execute |
| `--validate-model <model>` | validate |
| `--fix-model <model>` | fix |

**Valid values:** `opus`, `sonnet`, `haiku`

**Examples:**

```bash
# Use Sonnet for validation (instead of the default Opus)
/test-loop src/ --validate-model=sonnet

# Use Haiku for execution (fastest option)
/test-generate src/module.py --execute-model=haiku

# Override multiple agents at once
/test-loop src/ --validate-model=sonnet --fix-model=sonnet
```

CLI flags apply only to the current run. They do not persist.

---

### Environment Variables

Set environment variables to override models without editing files. This is useful for CI pipelines or shell profile configuration.

**Available variables:**

| Variable | Agent |
|----------|-------|
| `DANTE_ANALYZE_MODEL` | analyze |
| `DANTE_WRITE_MODEL` | write |
| `DANTE_EXECUTE_MODEL` | execute |
| `DANTE_VALIDATE_MODEL` | validate |
| `DANTE_FIX_MODEL` | fix |

**Valid values:** `opus`, `sonnet`, `haiku` (case-insensitive)

**Examples:**

```bash
# Set for the current shell session
export DANTE_VALIDATE_MODEL=sonnet
export DANTE_FIX_MODEL=sonnet

# Or inline with a command
DANTE_VALIDATE_MODEL=sonnet /test-loop src/
```

**Windows (PowerShell):**

```powershell
$env:DANTE_VALIDATE_MODEL = "sonnet"
$env:DANTE_FIX_MODEL = "sonnet"
```

Environment variables override the config file but are overridden by CLI flags. Empty values (e.g., `DANTE_VALIDATE_MODEL=""`) are treated as "not set" and fall through to the next precedence level.

---

### Config File

For persistent, project-level overrides, create a JSON config file at:

```
{project_root}/.claude/dante-config.json
```

**Format:**

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version. Currently `"1.0.0"`. |
| `model_overrides` | object | No | Per-agent model overrides. Only include agents you want to change. |

You only need to include agents you want to override. Agents not listed in `model_overrides` use their built-in defaults.

**Example configurations:**

Use Sonnet for all agents (optimize for speed):

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "analyze": "sonnet",
    "write": "sonnet",
    "execute": "sonnet",
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

Use Opus for all agents (optimize for quality):

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

Use Haiku for execution only (cost optimization):

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "execute": "haiku"
  }
}
```

**Error handling:**

- If the config file is missing, Dante uses the built-in defaults silently -- this is normal for first-time use.
- If the JSON is malformed (syntax error), Dante logs a warning and falls back to defaults.
- If a model name is invalid (e.g., `"gpt4"`), Dante stops with a clear error message telling you how to fix it.

---

## How Model Selection is Displayed

When you run `/test-loop` or `/test-generate`, Dante displays which model each agent will use and where the choice came from:

```
Model Selection:
  analyze-agent  -> sonnet (default)
  write-agent    -> sonnet (default)
  execute-agent  -> sonnet (default)
  validate-agent -> sonnet (cli)
  fix-agent      -> opus   (default)
```

The source label tells you which configuration level determined the model:

| Source | Meaning |
|--------|---------|
| `default` | Built-in default for this agent |
| `config` | Set in `.claude/dante-config.json` |
| `env` | Set via environment variable |
| `cli` | Set via CLI flag for this run |

---

## Retry and Fallback Behavior

If an agent call fails (timeout, rate limit, or API error), Dante applies automatic retry and fallback logic:

### Retry

Up to 3 retries with exponential backoff:

| Attempt | Wait Time |
|---------|-----------|
| 1st retry | 1 second |
| 2nd retry | 2 seconds |
| 3rd retry | 4 seconds |

### Fallback

If all 3 retries fail and the agent's model is **not** Sonnet, Dante automatically falls back to Sonnet and retries once more. You will see a warning:

```
WARNING: validate failed with opus, falling back to sonnet
```

If the agent is already using Sonnet (or if the Sonnet fallback also fails), Dante raises an error.

This fallback ensures your workflow can continue even when a higher-tier model is temporarily unavailable. Sonnet serves as the universal fallback because it is the most reliably available model.

---

## Timeouts

Each model has a configured timeout based on its expected response time:

| Model | Timeout |
|-------|---------|
| opus | 180 seconds (3 minutes) |
| sonnet | 120 seconds (2 minutes) |
| haiku | 60 seconds (1 minute) |

The timeout is automatically set based on the resolved model for each agent. If an agent exceeds its timeout, it triggers the retry/fallback logic described above.

---

## Reading the Metrics File

Dante records execution metrics in an append-only Markdown file:

```
{project_root}/.claude/dante-metrics.md
```

Each test-loop execution appends a section like this:

```markdown
## Execution: 2026-02-09T14:30:00Z

| Agent | Model | Duration | Result |
|-------|-------|----------|--------|
| analyze | sonnet | 45.2s | success |
| write | sonnet | 62.1s | success |
| execute | sonnet | 12.3s | success |
| validate | opus | 78.5s | success |
| fix | opus | 95.0s | success |

**Iteration Count**: 2
**Total Duration**: 293.1s
```

### What Each Column Means

| Column | Description |
|--------|-------------|
| **Agent** | Which agent ran (analyze, write, execute, validate, fix) |
| **Model** | Which Claude model was used for that agent |
| **Duration** | Wall-clock time the agent took to complete |
| **Result** | `success` or `failure` |

### How to Use Metrics

- **Compare model performance**: Look at Duration and Result across executions where you used different models for the same agent.
- **Identify bottlenecks**: If one agent consistently takes the longest, consider whether a different model would help.
- **Track reliability**: Check the Result column for patterns of failures with specific models.
- **Monitor over time**: Since the file is append-only, you can see how performance changes as your test suite grows.

### Disabling Metrics

If you prefer not to collect metrics, set the `DANTE_DISABLE_METRICS` environment variable:

```bash
export DANTE_DISABLE_METRICS=1
```

**Windows (PowerShell):**

```powershell
$env:DANTE_DISABLE_METRICS = "1"
```

When disabled, Dante skips writing to the metrics file entirely. This has no effect on test execution -- everything else works normally.

### Metrics and Version Control

The metrics file contains execution data specific to your local environment (timestamps, durations). It is recommended to add it to your `.gitignore`:

```
.claude/dante-metrics.md
```

---

## Common Scenarios

### Scenario 1: Speed Up a Large Test Suite

If your test-loop runs are slow and you want faster iterations, switch the validate and fix agents to Sonnet:

```bash
/test-loop src/ --validate-model=sonnet --fix-model=sonnet
```

Or persistently via config file:

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "validate": "sonnet",
    "fix": "sonnet"
  }
}
```

Trade-off: Slightly lower accuracy in test result categorization and fix quality.

### Scenario 2: Maximize Quality for a Critical Module

For important code where accuracy matters most, use Opus for all agents:

```bash
/test-loop src/critical_module.py --analyze-model=opus --write-model=opus --execute-model=opus
```

Trade-off: Longer execution times and higher resource usage.

### Scenario 3: CI Pipeline with Cost Constraints

In CI, you may want to use the most efficient models. Set environment variables in your CI configuration:

```bash
export DANTE_ANALYZE_MODEL=sonnet
export DANTE_WRITE_MODEL=sonnet
export DANTE_EXECUTE_MODEL=haiku
export DANTE_VALIDATE_MODEL=sonnet
export DANTE_FIX_MODEL=sonnet
```

Trade-off: Slightly lower categorization accuracy but significantly faster runs.

### Scenario 4: Experiment and Compare

Run the same tests twice with different models and compare the metrics:

```bash
# Run 1: Default models (validate=opus, fix=opus)
/test-loop src/

# Run 2: All Sonnet
/test-loop src/ --validate-model=sonnet --fix-model=sonnet

# Compare results in the metrics file
# Open .claude/dante-metrics.md and compare the two execution sections
```

---

## Troubleshooting

### "Invalid model" error

```
Invalid model 'gpt4' for agent 'validate'.
Supported models: opus, sonnet, haiku
```

**Cause**: You specified a model name that is not supported.
**Fix**: Use one of the three supported values: `opus`, `sonnet`, or `haiku`.

### "Unknown agent" error

```
Unknown agent 'reviewer'.
Valid agents: analyze, write, execute, validate, fix
```

**Cause**: The agent name in your configuration is not recognized.
**Fix**: Use one of the five valid agent names: `analyze`, `write`, `execute`, `validate`, `fix`.

### Fallback warning during execution

```
WARNING: validate failed with opus, falling back to sonnet
```

**Cause**: The Opus model was temporarily unavailable or timed out after 3 retries.
**What to do**: This is usually transient. The workflow continues with Sonnet. Check your metrics file to see if the fallback succeeded.

### Config file being ignored

If your `.claude/dante-config.json` overrides are not taking effect:

1. Check that the file is valid JSON (no trailing commas, proper quoting).
2. Check that model names are lowercase (`"opus"`, not `"Opus"`).
3. Check that agent names are valid (`"validate"`, not `"validate-agent"`).
4. Check whether a CLI flag or environment variable is overriding the config (they take higher precedence).

### Metrics file not being created

If `.claude/dante-metrics.md` is not appearing:

1. Check that `DANTE_DISABLE_METRICS` is not set to `1`.
2. Verify the `.claude/` directory exists in your project root.
3. Check file permissions on the `.claude/` directory.

Metrics collection is non-blocking -- if it fails, the test workflow continues normally. Check the console output for any warning messages about metrics.

---

## Reference

### All CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--analyze-model` | sonnet | Model for the analyze agent |
| `--write-model` | sonnet | Model for the write agent |
| `--execute-model` | sonnet | Model for the execute agent |
| `--validate-model` | opus | Model for the validate agent |
| `--fix-model` | opus | Model for the fix agent |

### All Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DANTE_ANALYZE_MODEL` | sonnet | Model for the analyze agent |
| `DANTE_WRITE_MODEL` | sonnet | Model for the write agent |
| `DANTE_EXECUTE_MODEL` | sonnet | Model for the execute agent |
| `DANTE_VALIDATE_MODEL` | opus | Model for the validate agent |
| `DANTE_FIX_MODEL` | opus | Model for the fix agent |
| `DANTE_DISABLE_METRICS` | (unset) | Set to `1` to disable metrics collection |

### Config File Schema

```json
{
  "version": "1.0.0",
  "model_overrides": {
    "<agent_name>": "<model>"
  }
}
```

- **Valid agent names**: `analyze`, `write`, `execute`, `validate`, `fix`
- **Valid model values**: `opus`, `sonnet`, `haiku`
- **File location**: `{project_root}/.claude/dante-config.json`

### Metrics File Format

- **Location**: `{project_root}/.claude/dante-metrics.md`
- **Format**: Append-only Markdown with one section per execution
- **Each section contains**: Timestamp heading, agent/model/duration/result table, iteration count, total duration
