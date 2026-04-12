# Metrics Collector Sub-Skill

**Parent Skill**: [Model Selection](./SKILL.md)
**Version**: 2.0.0
**Category**: Infrastructure
**Purpose**: Non-blocking, append-only Markdown metrics logging for agent execution data, emitted to `{project_root}/.claude/dante-metrics.md`

---

## Overview

The Metrics Collector appends execution data for every agent invocation during a test-loop session to a human-readable Markdown log file. Each execution appends a Markdown table section with timestamps, agent names, models, durations, and results.

### Design Principles

1. **Non-blocking** (REQ-F-13): Metrics collection must NEVER halt the workflow. The entire emit operation is wrapped in try/except. Failures log a warning and execution continues.
2. **Append-only** (REQ-F-15): Each execution appends a new section. No read-modify-write cycle is needed. No file locking is required.
3. **Human-readable**: Output is a standard Markdown file that users can inspect directly.
4. **Cross-platform**: File path handling documented for both Unix/macOS and Windows.

---

## Metrics File Location

```
{project_root}/.claude/dante-metrics.md
```

Where `{project_root}` is the detected project root directory (see `skills/project-detection/SKILL.md`).

The metrics file lives inside `.claude/` alongside the config file (`dante-config.json`) and state files. It should be added to `.gitignore` (contains execution data, not source).

---

## Metrics Format

Each test-loop execution appends one section to the file. The section contains a heading with the execution timestamp, a Markdown table of per-agent results, and summary metadata.

### Section Format

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

### Field Definitions

| Field | Location | Description |
|-------|----------|-------------|
| Execution timestamp | `## Execution:` heading | ISO 8601 UTC timestamp when the execution completed |
| Agent | Table column 1 | Agent name: analyze, write, execute, validate, fix |
| Model | Table column 2 | Model used: opus, sonnet, haiku |
| Duration | Table column 3 | Wall-clock execution time formatted as `{seconds}s` (one decimal place) |
| Result | Table column 4 | `success` or `failure` |
| Iteration Count | Summary line | Total number of test-loop iterations in this execution |
| Total Duration | Summary line | Sum of all agent durations formatted as `{seconds}s` (one decimal place) |

### Failure Format

When an agent fails, the Result column shows `failure`. No error details are included in the table to keep it clean and scannable.

```markdown
| validate | opus | 180.0s | failure |
```

---

## Interface

### Input

```yaml
project_root: Absolute path to the project root directory
execution_data:
  timestamp: ISO 8601 UTC string (e.g., "2026-02-09T14:30:00Z")
  agents:
    - agent_name: Name of the agent (analyze, write, execute, validate, fix)
      model: Model used (opus, sonnet, haiku)
      duration_seconds: Wall-clock time in seconds (float)
      success: Boolean indicating success or failure
  iteration_count: Number of test-loop iterations
  total_duration_seconds: Sum of all agent durations in seconds (float)
```

### Output

```yaml
status: "emitted" | "skipped"
warning: Optional warning message if emission failed (non-blocking)
```

---

## Operations

### `emit_metrics(project_root, execution_data)`

The primary operation. Formats execution data as a Markdown section and appends it to the metrics file.

```
FUNCTION emit_metrics(project_root, execution_data):

    # ──────────────────────────────────────────────
    # Non-blocking wrapper (REQ-F-13)
    # The ENTIRE operation is wrapped in try/except.
    # Any failure logs a warning and returns.
    # ──────────────────────────────────────────────

    TRY:

        # Step 1: Determine metrics file path
        metrics_path = "{project_root}/.claude/dante-metrics.md"

        # Step 2: Ensure .claude directory exists
        IF "{project_root}/.claude" does not exist:
            Create directory "{project_root}/.claude"
            # Windows: mkdir "{project_root}\.claude"
            # Unix:    mkdir -p "{project_root}/.claude"

        # Step 3: Format the Markdown section
        section = format_metrics_section(execution_data)

        # Step 4: Append to metrics file
        #
        # Read existing content (if file exists), then write
        # existing content + new section. If file does not exist,
        # write just the new section.
        #
        # Implementation in Claude Code agent context:
        #   Option A: Read existing file, Write with existing + new section
        #   Option B: Use Bash tool to append directly:
        #     Unix:    echo "{section}" >> "{metrics_path}"
        #     Windows: echo {section} >> "{metrics_path}"
        #
        # Either approach works. The key constraint is APPEND behavior.
        append section to metrics_path

        RETURN { status: "emitted" }

    CATCH any_exception AS e:

        # Non-blocking: log warning, continue workflow
        Log warning: "WARNING: Failed to emit metrics: {e}"
        Log warning: "Execution will continue. Metrics may be incomplete."

        RETURN { status: "skipped", warning: str(e) }
```

### `format_metrics_section(execution_data)`

Formats execution data into a Markdown section string.

```
FUNCTION format_metrics_section(execution_data):

    # Use provided timestamp or generate current UTC
    timestamp = execution_data.timestamp OR current_utc_time_iso8601()

    # Build the section
    lines = []

    # Heading
    lines.append("## Execution: {timestamp}")
    lines.append("")

    # Table header
    lines.append("| Agent | Model | Duration | Result |")
    lines.append("|-------|-------|----------|--------|")

    # Table rows (one per agent)
    FOR EACH agent IN execution_data.agents:
        name = agent.agent_name OR "unknown"
        model = agent.model OR "unknown"
        duration = format_duration(agent.duration_seconds)
        result = "success" IF agent.success ELSE "failure"

        lines.append("| {name} | {model} | {duration} | {result} |")

    # Summary metadata
    lines.append("")
    lines.append("**Iteration Count**: {execution_data.iteration_count}")

    total_duration = format_duration(execution_data.total_duration_seconds)
    lines.append("**Total Duration**: {total_duration}")
    lines.append("")

    RETURN join(lines, newline="\n")


FUNCTION format_duration(seconds):
    # Format as "{value}s" with one decimal place
    # Clamp negative values to 0
    IF seconds < 0:
        seconds = 0
    RETURN "{seconds:.1f}s"
    # Examples: 45.2s, 0.0s, 180.0s
```

---

## Append Implementation (Cross-Platform)

Since the metrics file is append-only Markdown, the implementation is straightforward. No read-modify-write cycle is needed, and no file locking is required.

### Using Bash Tool (Preferred -- True Append)

```
# Unix/macOS:
Use Bash tool: printf '%s\n' "{section}" >> "{project_root}/.claude/dante-metrics.md"

# Windows (PowerShell):
Use Bash tool: Add-Content -Path "{project_root}\.claude\dante-metrics.md" -Value "{section}"
```

### Using Read + Write Tools (Alternative)

If Bash append is not available:

```
# Step 1: Read existing content (empty string if file does not exist)
existing = Read "{project_root}/.claude/dante-metrics.md"
    # On file-not-found: existing = ""

# Step 2: Write existing + new section
Use Write tool: write "{existing}\n{section}" to "{project_root}/.claude/dante-metrics.md"
```

### Directory Creation

Before the first write, ensure the `.claude/` directory exists:

```
# Windows:
Use Bash tool: if not exist "{project_root}\.claude" mkdir "{project_root}\.claude"

# Unix/macOS:
Use Bash tool: mkdir -p "{project_root}/.claude"
```

---

## Error Handling

All errors are handled non-blocking. The workflow must never be interrupted by metrics failures.

### Metrics Directory Does Not Exist

**Behavior**: Create the `.claude/` directory. If creation fails, log warning and skip metrics.

**Log message** (warning on failure):
```
WARNING: Cannot create metrics directory at {project_root}/.claude/: {error}
Execution continues without writing metrics.
```

### Metrics File Does Not Exist

**Behavior**: Create a new file with the first section. This is NOT an error -- it is the normal first-run case.

### Metrics File Write Failure (Disk Full, Permission Denied)

**Behavior**: Log warning, continue execution. This metrics entry is lost.

**Log message** (warning):
```
WARNING: Failed to write metrics to {project_root}/.claude/dante-metrics.md: {error}
Execution continues. This metrics entry will be lost.
```

### Invalid Execution Data

**Behavior**: Use defaults for missing fields. Never reject metrics data.

- Missing `timestamp`: Use current UTC time
- Missing `agent_name`: Record as `"unknown"`
- Missing `model`: Record as `"unknown"`
- Missing `duration_seconds`: Record as `0.0s`
- Missing `success`: Record as `failure`
- Missing `iteration_count`: Record as `0`
- Missing `total_duration_seconds`: Calculate from sum of agent durations, or `0.0s`

---

## Implementation Checklist

When implementing the Metrics Collector in a Claude Code agent context:

- [ ] **Ensure directory**: Use `Bash` tool to create `{project_root}/.claude/` if it does not exist
- [ ] **Format section**: Build the Markdown section string from execution data
- [ ] **Append to file**: Use `Bash` tool or `Read`+`Write` tools to append to `dante-metrics.md`
- [ ] **Non-blocking wrapper**: Wrap the entire operation in try/except; on failure log warning and continue
- [ ] **Generate timestamp**: Use `Bash` tool to get current UTC time in ISO 8601 format
  ```
  # Cross-platform via Python:
  python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"

  # Unix/macOS:
  date -u +"%Y-%m-%dT%H:%M:%SZ"

  # Windows (PowerShell):
  (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  ```
- [ ] **Cross-platform paths**: Use forward slashes in Unix, backslashes in Windows Bash commands
- [ ] **No file locking**: Append-only design eliminates the need for locks

---

## Testing Checklist

### Non-Blocking Behavior (REQ-F-13)

- [ ] **Write failure**: Mock file write failure (permission denied), verify `emit_metrics()` logs warning and returns `{ status: "skipped" }` -- workflow continues
- [ ] **Directory creation failure**: Mock directory creation failure, verify warning logged and workflow continues
- [ ] **Invalid execution data**: Pass null/empty execution_data, verify `emit_metrics()` does not throw
- [ ] **Agent exception flow**: Verify that when an agent throws, metrics are still emitted BEFORE the exception propagates

### Metrics Format (REQ-F-15)

- [ ] **Markdown table structure**: Verify output contains `## Execution:` heading, table header, table rows, and summary lines
- [ ] **Correct columns**: Verify table has Agent, Model, Duration, Result columns
- [ ] **Duration formatting**: Verify durations are formatted as `{value}s` with one decimal place
- [ ] **Result values**: Verify result is `success` or `failure` (not true/false)
- [ ] **Timestamp format**: Verify ISO 8601 UTC format in heading

### Append Behavior

- [ ] **First write**: When no metrics file exists, verify file is created with one section
- [ ] **Subsequent writes**: After multiple executions, verify file contains all sections in order
- [ ] **No data loss**: Verify existing content is preserved when appending new sections

### File Location (REQ-F-12)

- [ ] **Correct path**: Verify metrics file is at `{project_root}/.claude/dante-metrics.md`
- [ ] **Directory creation**: Verify `.claude/` directory is created if it does not exist

---

## Relationship to Other Sub-Skills

### Depends On

- **Config Manager** (`config-manager.md`): Indirectly, via the orchestrator which uses config to determine `project_root`

### Used By

- **Test Loop Orchestrator** (TASK-005): Calls `emit_metrics()` after each test-loop execution completes

### Does Not Depend On

- **Model Resolver** (`model-resolver.md`): Metrics Collector receives pre-resolved data (model name, duration, success). It does not call Model Resolver directly.

---

## Example: Full Metrics File

After two test-loop executions, `{project_root}/.claude/dante-metrics.md` would contain:

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

## Execution: 2026-02-09T15:45:00Z

| Agent | Model | Duration | Result |
|-------|-------|----------|--------|
| analyze | sonnet | 38.7s | success |
| write | sonnet | 55.3s | success |
| execute | sonnet | 10.1s | success |
| validate | opus | 180.0s | failure |

**Iteration Count**: 1
**Total Duration**: 284.1s
```

---

**Last Updated**: 2026-02-10
**Status**: Phase 1 - Foundation implementation (v2)
