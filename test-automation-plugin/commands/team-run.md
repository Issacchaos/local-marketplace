---
description: "Execute an agent team definition with optional CLI configuration overrides"
argument-hint: "[team-name] [options]"
allowed-tools: Skill(test-engineering:team-orchestration), Skill(test-engineering:telemetry)
---

# /team-run Command

**Description**: Execute an agent team definition with optional CLI configuration overrides

**Usage**:
```
/team-run [team-name] [options]
```

**Arguments**:
- `team-name` (required): Name of the team to execute. Must correspond to a file at `teams/[team-name].md`.

**Options**:
- `--max-agents <n>`: Override maximum parallel agents (1-25, default: team definition value)
- `--timeout <minutes>`: Override team execution timeout in minutes (>0, default: team definition value)
- `--approval-gates <mode>`: Override approval gate mode: `before`, `after`, or `disabled` (default: team definition value)
- `--telemetry`: Enable telemetry logging for this execution (default: team definition value or off)
- `--help, -h`: Display help information

**Examples**:
```bash
# Execute a team using its default configuration
/team-run testing-parallel

# Execute with a custom agent limit
/team-run testing-parallel --max-agents=3

# Execute with a shorter timeout
/team-run documentation --timeout=10

# Execute fully autonomously (no approval gates)
/team-run example-parallel --approval-gates=disabled

# Execute with telemetry enabled
/team-run testing-parallel --telemetry

# Execute with multiple overrides
/team-run testing-parallel --max-agents=4 --timeout=20 --approval-gates=before --telemetry

# Get help
/team-run --help
```

---

## Command Behavior

This command is the primary entry point for executing agent team definitions. It parses user arguments, validates them, loads the team definition, applies CLI overrides, and **uses Claude Code's built-in TeamCreate tool** to spawn the team.

**Execution Flow**:
1. Parse command arguments and CLI flags
2. Validate all flag values against allowed ranges
3. Load team definition from `teams/[team-name].md`
4. Apply CLI flag overrides to team definition frontmatter
5. **Build execution plan** from agents and dependencies
6. **Clarify outstanding questions** via AskUserQuestion (if any ambiguities)
7. **Present plan for approval** (if approval gates enabled)
8. **Create team using TeamCreate** with coordinator agent type
9. Coordinator spawns teammates and manages shared task list
10. Display execution summary to the user
11. Return telemetry log path if telemetry was enabled

**Key Characteristics**:
- Team definitions live at the plugin root in `teams/` (NOT `.claude/teams/`)
- CLI flags take highest precedence over team definition frontmatter values
- **Uses built-in TeamCreate tool** (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- The command is a thin wrapper; orchestration handled by built-in team system
- Team lead coordinates via shared task list at `~/.claude/tasks/{team-name}/`
- Execution summary always shows agents spawned, duration, and success/failure counts
- Falls back to custom `skills/team-orchestration/SKILL.md` if built-in system unavailable

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/team-run` command to run an agent team definition.

## Your Task

Parse the user's arguments, validate inputs, and invoke the team-orchestration skill to execute the requested team.

### Step 1: Parse Arguments and Validate

**Parse Arguments**:
```javascript
// Extract team name and flags from user command
const args = parseCommandArgs(userInput);
const team_name = args.positional[0];  // e.g., "testing-parallel"

// Parse CLI override flags
const cli_overrides = {};
if (args['max-agents'] !== undefined) cli_overrides['max_agents'] = parseInt(args['max-agents'], 10);
if (args['timeout'] !== undefined) cli_overrides['timeout_minutes'] = parseInt(args['timeout'], 10);
if (args['approval-gates'] !== undefined) cli_overrides['approval_gates'] = args['approval-gates'];
if (args['telemetry'] !== undefined) cli_overrides['telemetry_enabled'] = true;
```

**Validate Team Name**:
- If `team_name` is missing or empty, display the help text and STOP:
  ```
  Error: Missing required argument [team-name].

  Usage: /team-run [team-name] [options]

  Run /team-run --help for more information.
  ```

**Validate Flag Values**:
```javascript
// --max-agents: must be integer between 1 and 25
if (cli_overrides.max_agents !== undefined) {
    if (isNaN(cli_overrides.max_agents) || cli_overrides.max_agents < 1 || cli_overrides.max_agents > 25) {
        // Display error and STOP:
        // "Error: --max-agents must be an integer between 1 and 25. Got: '{value}'."
    }
}

// --timeout: must be a positive integer (> 0)
if (cli_overrides.timeout_minutes !== undefined) {
    if (isNaN(cli_overrides.timeout_minutes) || cli_overrides.timeout_minutes <= 0) {
        // Display error and STOP:
        // "Error: --timeout must be a positive integer (minutes). Got: '{value}'."
    }
}

// --approval-gates: must be one of "before", "after", "disabled"
const VALID_GATE_MODES = ['before', 'after', 'disabled'];
if (cli_overrides.approval_gates !== undefined) {
    if (!VALID_GATE_MODES.includes(cli_overrides.approval_gates.toLowerCase())) {
        // Display error and STOP:
        // "Error: --approval-gates must be one of: before, after, disabled. Got: '{value}'."
    }
}
```

**Verify Team Definition Exists**:
Check that `teams/{team_name}.md` exists at the project root.
- Use Glob or Bash `ls` to check for the file at `teams/{team_name}.md`.
- If the file does not exist, display error and STOP:
  ```
  Error: Team definition not found: teams/{team_name}.md

  Available teams:
  {list files in teams/ directory with .md extension, showing names without extension}

  To create a new team, add a definition file at teams/{team_name}.md.
  See teams/example-parallel.md for a template.
  ```

**Display Start Message**:
```markdown
# Starting Team Execution: {team_name}

**Team Definition**: teams/{team_name}.md
${Object.keys(cli_overrides).length > 0 ? `**CLI Overrides**:\n${Object.entries(cli_overrides).map(([k, v]) => `  - ${k}: ${v}`).join('\n')}\n` : ''}
Loading team definition and preparing execution plan...

---
```

### Step 2: Load Team Definition and Build Execution Plan

**Load team definition and prepare execution plan**:

```javascript
// Read team definition to get configuration
const team_def = read_team_definition(`teams/${team_name}.md`);

// Parse YAML frontmatter to extract key fields
// Required: name, coordinator, max_agents
// Optional: agents[], dependencies[], approval_gates, timeout_minutes, etc.
const coordinator_path = team_def.frontmatter.coordinator;
const agents = team_def.frontmatter.agents || [];
const dependencies = team_def.frontmatter.dependencies || [];

// Apply CLI overrides to team definition
const final_config = apply_cli_overrides(team_def, cli_overrides);

// Build execution plan from dependency graph
// This shows user what will happen before spawning anything
const execution_plan = build_execution_plan(agents, dependencies, final_config);
```

**Execution plan structure**:
```javascript
{
  phases: [
    {
      phase_number: 1,
      agents: ['review-compilation-db', 'review-source-parser'],
      parallel: true,
      dependencies: []
    },
    {
      phase_number: 2,
      agents: ['aggregate-review-results'],
      parallel: false,
      dependencies: ['review-compilation-db', 'review-source-parser']
    }
  ],
  total_agents: 8,
  max_concurrent: 5,
  estimated_duration: "15-20 minutes"
}
```

### Step 3: Clarify Outstanding Questions

**Ask user for clarification on any ambiguities**:

```javascript
// Analyze execution plan for potential ambiguities or missing information
const outstanding_questions = analyze_plan_for_questions(execution_plan, team_def);

// Examples of questions that might need clarification:
// - "Should we run agents sequentially or in parallel for this phase?"
// - "Which test pattern should we prioritize if multiple are detected?"
// - "Should we include optional agents in this execution?"
// - "What is the target scope for this team execution?"

if (outstanding_questions.length > 0) {
  // Use AskUserQuestion tool to clarify before proceeding
  const clarifications = await AskUserQuestion({
    questions: outstanding_questions.map(q => ({
      question: q.question,
      header: q.header,
      options: q.options,
      multiSelect: q.multiSelect || false
    }))
  });

  // Apply clarifications to execution plan
  execution_plan = apply_clarifications(execution_plan, clarifications);
}
```

**Common clarification scenarios**:
- **Scope ambiguity**: "Apply to all files or subset?"
- **Priority conflicts**: "Which agent should run first if no explicit dependency?"
- **Optional agents**: "Include optional validation agents?"
- **Parameter ambiguity**: "Use default timeout or custom duration?"
- **Resource constraints**: "Max agents to run in parallel?"

### Step 4: Request User Approval (If Enabled)

**Present execution plan and get approval**:

```javascript
// Check if before_execution approval gate is enabled
if (final_config.approval_gates.before_execution && !final_config.approval_gates.disabled) {
  // Display execution plan to user (with clarifications applied)
  display_execution_plan(execution_plan);

  // Request approval
  const approval = await request_approval({
    prompt: "Approve this execution plan?",
    options: ["Approve", "Modify", "Reject"]
  });

  if (approval === "Reject") {
    return abort_execution("User rejected plan at approval gate");
  }

  if (approval === "Modify") {
    // Allow up to 3 iterations of plan modification
    // User can adjust agent composition, parallelism, etc.
    execution_plan = handle_plan_modifications(execution_plan);
  }
}
```

### Step 5: Create Team Using Built-in TeamCreate

**After clarifications and approval, spawn team using built-in orchestration**:

```javascript
// Create team using built-in TeamCreate tool
// This spawns the team lead (coordinator agent)
TeamCreate({
  team_name: team_name,
  description: team_def.frontmatter.description || `Team: ${team_name}`,
  agent_type: coordinator_path  // Coordinator file defines team lead behavior
});

// The coordinator now:
// 1. Reads team definition and execution plan
// 2. Creates tasks using TaskCreate for each agent
// 3. Spawns teammate agents respecting dependencies
// 4. Delegates work via shared task list at ~/.claude/tasks/{team_name}/
// 5. Aggregates results when all agents complete
```

**How it works**:
1. **Pre-planning** (Steps 2-3): Load definition, build plan, get approval
2. **TeamCreate**: Spawns team lead agent using coordinator file
3. **Coordinator executes plan**: Reads approved plan, creates tasks, spawns teammates
4. **Task coordination**: Shared task list coordinates work and dependencies
5. **Result aggregation**: Built-in system collects and merges agent outputs

**Configuration passed to coordinator**:
- Approved execution plan (phases, agents, dependencies)
- CLI overrides (--max-agents, --timeout, --approval-gates)
- Team definition frontmatter
- Team config at `~/.claude/teams/{team_name}/config.json`
- Shared task list at `~/.claude/tasks/{team_name}/`

**Fallback to custom orchestration**:
If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not set or team requires custom logic:
- Fall back to `skills/team-orchestration/SKILL.md` (legacy orchestration)
- This provides backward compatibility with existing team definitions

### Step 3: Display Execution Summary

When the team-orchestration skill returns its `TeamResult`, display a summary:

**On Success (status: "completed")**:
```markdown
# Team Execution Complete: {team_name}

**Status**: Completed
**Duration**: {total_duration_seconds}s
**Agents**: {total_agents} spawned, {successful} succeeded, {failed} failed
**Success Rate**: {success_rate * 100}%

## Agent Results
{for each agent output: agent_type, status, duration}

${telemetry_log_path ? `**Telemetry Log**: ${telemetry_log_path}` : ''}
```

**On Partial Success (status: "partial_success")**:
```markdown
# Team Execution Partially Succeeded: {team_name}

**Status**: Partial Success
**Duration**: {total_duration_seconds}s
**Agents**: {total_agents} spawned, {successful} succeeded, {failed} failed
**Success Rate**: {success_rate * 100}%

## Successful Agents
{list successful agents with outputs}

## Failed Agents
{list failed agents with failure reasons}

${telemetry_log_path ? `**Telemetry Log**: ${telemetry_log_path}` : ''}
```

**On Failure (status: "failed")**:
```markdown
# Team Execution Failed: {team_name}

**Status**: Failed
**Duration**: {total_duration_seconds}s
**Error**: {error message}

## Failed Agents
{list all failed agents with failure reasons}

${telemetry_log_path ? `**Telemetry Log**: ${telemetry_log_path}` : ''}
```

**On Abort (status: "aborted")**:
```markdown
# Team Execution Aborted: {team_name}

**Status**: Aborted
**Duration**: {total_duration_seconds}s
**Reason**: {error message}

${telemetry_log_path ? `**Telemetry Log**: ${telemetry_log_path}` : ''}
```

**On Timeout (status: "timed_out")**:
```markdown
# Team Execution Timed Out: {team_name}

**Status**: Timed Out
**Duration**: {total_duration_seconds}s
**Timeout Limit**: {timeout_minutes} minutes

## Agents at Timeout
{list agents with their status at timeout}

${telemetry_log_path ? `**Telemetry Log**: ${telemetry_log_path}` : ''}

Consider increasing the timeout with: /team-run {team_name} --timeout={timeout_minutes * 2}
```

---

## Help Text

When user runs `/team-run --help`:

```markdown
# /team-run Command Help

**Description**: Execute an agent team definition with optional configuration overrides

**Usage**: /team-run [team-name] [options]

**Arguments**:
- team-name (required): Name of the team to execute (matches teams/[team-name].md)

**Options**:
- --max-agents <n>          Override max parallel agents (1-25)
- --timeout <minutes>       Override team execution timeout (>0, in minutes)
- --approval-gates <mode>   Override approval gate mode: before, after, disabled
- --telemetry               Enable telemetry logging for this execution
- --help, -h                Show this help message

**How it works**:
1. Loads the team definition from teams/[team-name].md
2. Validates the definition (required fields, agent references, no circular deps)
3. Applies any CLI flag overrides to the team configuration
4. **Builds execution plan** from dependency graph (shows phases, parallelism)
5. **Clarifies outstanding questions** via AskUserQuestion (resolves ambiguities)
6. **Presents plan for approval** (if approval gates enabled)
7. **Creates team using TeamCreate** with coordinator agent type
8. **Team lead spawns teammates** and manages shared task list
9. Teammates coordinate via `~/.claude/tasks/{team-name}/` directory
10. Built-in system handles agent lifecycle, retries, and queuing
11. Aggregates results from all completed agents
12. Displays execution summary with success/failure counts

**Requirements**:
- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` to enable built-in team system
- Falls back to `skills/team-orchestration/SKILL.md` if unavailable

**Configuration Precedence** (highest to lowest):
1. CLI flags (--max-agents, --timeout, etc.)
2. Team definition frontmatter (teams/[team-name].md)
3. Framework defaults (max_agents=5, timeout=30min, gates=enabled)

**Examples**:
```bash
# Run a team with defaults
/team-run testing-parallel

# Limit to 3 parallel agents
/team-run testing-parallel --max-agents=3

# Run with a 10-minute timeout
/team-run documentation --timeout=10

# Disable approval gates for autonomous execution
/team-run example-parallel --approval-gates=disabled

# Enable telemetry
/team-run testing-parallel --telemetry

# Multiple overrides
/team-run testing-parallel --max-agents=4 --timeout=20 --approval-gates=before --telemetry
```

**Team Definition Format**:
Team definitions are Markdown files in the `teams/` directory with YAML frontmatter.
See `teams/example-parallel.md` for a fully commented template.

Required frontmatter fields:
- name: Team identifier (must match filename)
- coordinator: Path to coordinator logic file
- max_agents: Maximum parallel agents (1-25)

**See also**:
- teams/example-parallel.md - Example team definition template
- skills/team-orchestration/SKILL.md - Orchestration skill reference
- skills/team-orchestration/team-loader.md - Team definition schema
```

---

## Error Handling

### Missing Team Name
```
Error: Missing required argument [team-name].

Usage: /team-run [team-name] [options]

Run /team-run --help for more information.
```

### Team Definition Not Found
```
Error: Team definition not found: teams/my-missing-team.md

Available teams:
- example-parallel

To create a new team, add a definition file at teams/my-missing-team.md.
See teams/example-parallel.md for a template.
```

### Invalid --max-agents Value
```
Error: --max-agents must be an integer between 1 and 25. Got: '30'.
```

### Invalid --timeout Value
```
Error: --timeout must be a positive integer (minutes). Got: '-5'.
```

### Invalid --approval-gates Value
```
Error: --approval-gates must be one of: before, after, disabled. Got: 'always'.
```

### Team Definition Validation Failure
When the team-orchestration skill returns a validation error from the team-loader:
```
Error: Team definition 'my-team' failed validation:

- Missing required field: coordinator
- Agent reference not found: agents/nonexistent-agent.md

Fix the issues in teams/my-team.md and try again.
```

---

## Notes

### Team Definition Location

Team definitions live at the **plugin root** in the `teams/` directory, NOT in `.claude/teams/`. This is consistent with how agents live in `agents/` and skills live in `skills/`.

```
project-root/
  teams/
    example-parallel.md        # Example team (shipped with framework)
    testing-parallel.md        # Testing team (from child spec)
    documentation.md           # Documentation team (from child spec)
    my-custom-team.md          # User-created custom team
  commands/
    team-run.md                # This command
  skills/
    team-orchestration/
      SKILL.md                 # Orchestration entry point
```

### CLI Override Precedence

CLI flags always override the team definition frontmatter values. The configuration precedence order is:

1. **CLI Arguments** (highest): `--max-agents=3` overrides everything
2. **Team Definition Frontmatter**: `max_agents: 5` in `teams/my-team.md`
3. **Framework Defaults** (lowest): `max_agents: 5`, `timeout_minutes: 30`

### Relationship to Team Orchestration Skill

This command **prefers Claude Code's built-in team system** via TeamCreate. The command handles:
- Argument parsing and validation
- User-facing error messages for invalid inputs
- Loading team definitions
- Creating teams with TeamCreate
- Displaying the execution summary

The **built-in team system** handles:
- Team lead spawning from coordinator agent type
- Shared task list at `~/.claude/tasks/{team-name}/`
- Teammate spawning and coordination
- Agent lifecycle tracking
- Result aggregation

**Legacy support**: `skills/team-orchestration/SKILL.md` provides fallback orchestration if:
- Built-in team system is unavailable (experimental flag not set)
- Team requires custom retry logic or approval gates
- Backward compatibility with existing team definitions needed

### Creating Custom Teams

Users can create custom teams by:
1. Creating a team definition file at `teams/[team-name].md`
2. Creating a coordinator file referenced in the team definition
3. Running `/team-run [team-name]`

See `teams/example-parallel.md` for a fully commented template.

---

## Troubleshooting

**Problem**: "Team definition not found" error
- **Solution**: Verify the file exists at `teams/[team-name].md`. The name must match exactly (case-sensitive on some systems).

**Problem**: "Team definition failed validation" error
- **Solution**: Check the error details. Common issues: missing `name`, `coordinator`, or `max_agents` fields; coordinator file not found; agent definition files not found; circular dependencies.

**Problem**: Team times out before agents complete
- **Solution**: Increase the timeout: `/team-run my-team --timeout=60`. Default is 30 minutes.

**Problem**: Too many agents fail
- **Solution**: Check individual agent errors in the execution summary. Consider reducing `max_agents` to run fewer in parallel, or review agent definitions for correctness.

**Problem**: Approval gate keeps asking for approval
- **Solution**: Use `--approval-gates=disabled` to skip all gates for autonomous execution. Or use `--approval-gates=before` to only approve the plan (skip the after-completion gate).

---

## Summary

The `/team-run` command is the **user entry point** for agent team orchestration. It provides:

- **Simple invocation**: `/team-run [team-name]` loads and executes a team definition
- **CLI overrides**: Fine-tune execution with `--max-agents`, `--timeout`, `--approval-gates`, and `--telemetry`
- **Clear validation**: Invalid inputs produce specific, actionable error messages
- **Execution visibility**: Summary shows agent counts, duration, success rate, and telemetry path
- **Extensibility**: Users create custom teams by adding `.md` files to `teams/`
