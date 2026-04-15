---
description: "Execute an agent team definition with optional CLI configuration overrides"
argument-hint: "[team-name] [options]"
allowed-tools: Skill(teamsters:team-orchestration), Skill(teamsters:telemetry)
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
- `--telemetry-console`: Enable live console telemetry output (color-coded activity feed)
- `--telemetry-format <fmt>`: Log format: `json`, `pipe`, or `text` (default: pipe)
- `--validate`: Validate team definition without executing (checks fields, refs, deps, conflicts)
- `--dry-run`: Show execution plan with dependency graph without executing
- `--history [team-name]`: Show execution history (optionally filtered by team)
- `--resume <execution-id>`: Resume an interrupted execution from last checkpoint
- `--status <execution-id>`: Inspect state of an interrupted or running execution
- `--init`: Interactive wizard to generate a new team definition
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

# Live console telemetry
/team-run testing-parallel --telemetry-console

# Execute with multiple overrides
/team-run testing-parallel --max-agents=4 --timeout=20 --approval-gates=before --telemetry

# Validate without executing
/team-run testing-parallel --validate

# Show execution plan only (dry run)
/team-run testing-parallel --dry-run

# Show execution history
/team-run --history
/team-run --history testing-parallel

# Resume interrupted execution
/team-run --resume exec-20260325T163000

# Check execution status
/team-run --status exec-20260325T163000

# Create a new team interactively
/team-run --init

# Get help
/team-run --help

# Interactive team selection (no team name — presents available teams as choices)
/team-run

# Partial name match (fuzzy-matches against available teams)
/team-run ex
/team-run testing
```

**Predictive Team Suggestions**:

When you omit the team name or provide a partial/incorrect name, the command will automatically discover available teams and present them as selectable options:
- **No team name**: Shows all available teams as an interactive selection prompt
- **Partial match**: Filters teams matching your input and presents matching options
- **No match**: Shows all teams with a "Did you mean?" prompt
- **Exact match**: Proceeds immediately with no prompt

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
if (args['telemetry-console'] !== undefined) cli_overrides['telemetry_console'] = true;
if (args['telemetry-format'] !== undefined) cli_overrides['telemetry_format'] = args['telemetry-format'];

// Standalone mode flags (these run instead of normal execution)
const standalone_mode = args['validate'] || args['dry-run'] || args['history'] !== undefined
    || args['resume'] || args['status'] || args['init'];
```

**Handle Standalone Modes** (before team name validation):

```javascript
// --init: Interactive team definition generator wizard
if (args['init']) {
  // Use AskUserQuestion to collect:
  // 1. Team name
  // 2. Number of agents and their roles
  // 3. Dependency structure (linear, parallel, diamond, custom)
  // 4. Model preferences per agent
  // 5. Approval gate preferences
  // 6. Timeout and retry settings
  // Then generate teams/<name>.md and optionally teams/<name>-coordinator.md
  // Save to teams/ directory and display confirmation
  return run_init_wizard();
}

// --history: Show execution history
if (args['history'] !== undefined) {
  // Read .claude/teamsters-history.json
  // If args['history'] is a string, filter by team name
  // Display formatted table with: team, timestamp, duration, agents, success_rate
  // Show performance trends if multiple executions exist
  return display_execution_history(args['history']);
}

// --resume: Resume interrupted execution
if (args['resume']) {
  // Read .claude/teamsters-state/<execution-id>.json
  // Validate checkpoint exists and is recoverable
  // Display what was completed and what remains
  // Ask for confirmation, then resume from last completed phase
  return resume_execution(args['resume']);
}

// --status: Inspect execution state
if (args['status']) {
  // Read .claude/teamsters-state/<execution-id>.json
  // Display: completed phases, pending agents, partial outputs, elapsed time
  return display_execution_status(args['status']);
}
```

**Resolve Team Name (Predictive Suggestions)**:

Before validating, discover available teams and resolve the team name interactively if needed.

```javascript
// Step 1: Discover available teams
// Use Glob to find all teams/*.md files
const all_team_files = Glob('teams/*.md');

// Filter out coordinator files (match *-coordinator.md pattern)
const team_files = all_team_files.filter(f => !f.match(/-coordinator\.md$/));

// Extract team names (strip path prefix and .md extension)
const available_teams = team_files.map(f => f.replace(/^teams\//, '').replace(/\.md$/, ''));

// For each team, read frontmatter to get description (for display in selection)
const team_info = {};
for (const name of available_teams) {
    const content = Read(`teams/${name}.md`);
    const frontmatter = parseFrontmatter(content);
    team_info[name] = {
        description: frontmatter.description || `Team: ${name}`,
        name: frontmatter.name || name
    };
}
```

```javascript
// Step 2: Resolve team_name based on what the user provided

if (!team_name || team_name.trim() === '') {
    // --- NO TEAM NAME PROVIDED ---
    if (available_teams.length === 0) {
        // No teams exist at all
        // Display: "No team definitions found in teams/. Run /team-run --init to create one."
        // STOP
    } else {
        // Present all available teams as selectable options via AskUserQuestion
        // Question: "Which team would you like to run?"
        // Header: "Team"
        // Options: Each team as { label: name, description: team_info[name].description }
        // Set team_name to the user's selection
        team_name = AskUserQuestion({
            question: "Which team would you like to run?",
            header: "Team",
            options: available_teams.map(name => ({
                label: name,
                description: team_info[name].description
            }))
        });
    }

} else if (!available_teams.includes(team_name)) {
    // --- TEAM NAME PROVIDED BUT NO EXACT MATCH ---

    // Find fuzzy matches: teams whose name contains the input as a substring (case-insensitive)
    const input_lower = team_name.toLowerCase();
    const matches = available_teams.filter(name => name.toLowerCase().includes(input_lower));

    if (matches.length === 1) {
        // Single fuzzy match — auto-select with confirmation message
        // Display: "No exact match for '{team_name}'. Using closest match: '{matches[0]}'"
        team_name = matches[0];

    } else if (matches.length > 1) {
        // Multiple fuzzy matches — present as selectable options
        team_name = AskUserQuestion({
            question: `Multiple teams match '${team_name}'. Which one did you mean?`,
            header: "Team",
            options: matches.map(name => ({
                label: name,
                description: team_info[name].description
            }))
        });

    } else {
        // No fuzzy matches at all — present ALL teams with "did you mean?" prompt
        if (available_teams.length === 0) {
            // Display: "No team definitions found. Run /team-run --init to create one."
            // STOP
        } else {
            team_name = AskUserQuestion({
                question: `No team matching '${team_name}' found. Did you mean one of these?`,
                header: "Team",
                options: available_teams.map(name => ({
                    label: name,
                    description: team_info[name].description
                }))
            });
        }
    }
}

// If user selected "Other" from AskUserQuestion and typed a custom value,
// treat it as a literal team name and re-validate that teams/{value}.md exists.
// If still not found, display error and STOP.
```

// At this point, team_name is resolved to a valid team name.

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

// --telemetry-format: must be one of "json", "pipe", "text"
const VALID_FORMATS = ['json', 'pipe', 'text'];
if (cli_overrides.telemetry_format !== undefined) {
    if (!VALID_FORMATS.includes(cli_overrides.telemetry_format.toLowerCase())) {
        // Display error and STOP:
        // "Error: --telemetry-format must be one of: json, pipe, text. Got: '{value}'."
    }
}
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

// Run file conflict detection (P1 improvement)
// Uses files_read/files_write from agent definitions to detect conflicts
const conflict_result = detect_file_conflicts(agents, dependencies);
if (conflict_result.conflicts.length > 0) {
  display_file_conflict_warnings(conflict_result);
}

// Build execution plan from dependency graph
// This shows user what will happen before spawning anything
const execution_plan = build_execution_plan(agents, dependencies, final_config);

// --validate: Validate and stop (don't execute)
if (args['validate']) {
  // Display validation results: errors, warnings, file conflicts, suggestions
  // Includes: required fields, coordinator exists, agent refs valid, no circular deps,
  //           file conflict detection, model name validation, timeout/limit ranges
  display_validation_report(team_def, conflict_result);
  return; // STOP - don't execute
}

// --dry-run: Show plan and stop (don't execute)
if (args['dry-run']) {
  // Generate ASCII dependency graph via plan-visualizer
  const ascii_graph = generate_ascii_graph(execution_plan);
  display_dry_run_plan(execution_plan, ascii_graph, conflict_result);
  return; // STOP - don't execute
}
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

if (outstanding_questions.length > 0) {
  const clarifications = await AskUserQuestion({
    questions: outstanding_questions.map(q => ({
      question: q.question,
      header: q.header,
      options: q.options,
      multiSelect: q.multiSelect || false
    }))
  });

  execution_plan = apply_clarifications(execution_plan, clarifications);
}
```

### Step 4: Request User Approval (If Enabled)

**Present execution plan and get approval via the `AskUserQuestion` tool.**

Do NOT write the approval prompt as plain text (e.g. `Approve / Modify / Reject?`) — that puts the burden on the user's UI to scrape options out of prose, which is fragile. Always invoke `AskUserQuestion` so the question and options travel as a structured `tool_use` block. Dashboards (e.g. llm-watcher) then show proper clickable buttons with label + description.

```javascript
if (final_config.approval_gates.before_execution && !final_config.approval_gates.disabled) {
  display_execution_plan(execution_plan);

  const { answers } = AskUserQuestion({
    questions: [{
      header: "Approval",
      question: "Approve this execution plan?",
      multiSelect: false,
      options: [
        { label: "Approve", description: "Spawn teammates and run the plan as shown" },
        { label: "Modify",  description: "Revise the plan first (up to 3 iterations)" },
        { label: "Reject",  description: "Abort without spawning any teammates" },
      ],
    }],
  });
  const approval = answers["Approve this execution plan?"];

  if (approval === "Reject") {
    return abort_execution("User rejected plan at approval gate");
  }

  if (approval === "Modify") {
    execution_plan = handle_plan_modifications(execution_plan);
  }
}
```

### Step 5: Create Team Using Built-in TeamCreate

**After clarifications and approval, spawn team using built-in orchestration**:

```javascript
TeamCreate({
  team_name: team_name,
  description: team_def.frontmatter.description || `Team: ${team_name}`,
  agent_type: coordinator_path
});
```

**How it works**:
1. **Pre-planning** (Steps 2-3): Load definition, build plan, get approval
2. **TeamCreate**: Spawns team lead agent using coordinator file
3. **Coordinator executes plan**: Reads approved plan, creates tasks, spawns teammates
4. **Task coordination**: Shared task list coordinates work and dependencies
5. **Result aggregation**: Built-in system collects and merges agent outputs

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
- --telemetry-console       Enable live console telemetry output (color-coded activity feed)
- --telemetry-format <fmt>  Log format: json, pipe, or text (default: pipe)
- --validate                Validate team definition without executing
- --dry-run                 Show execution plan with dependency graph without executing
- --history [team-name]     Show execution history (optionally filtered by team)
- --resume <execution-id>   Resume an interrupted execution from last checkpoint
- --status <execution-id>   Inspect state of a running or interrupted execution
- --init                    Interactive wizard to generate a new team definition
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

# Live console telemetry
/team-run testing-parallel --telemetry-console

# Multiple overrides
/team-run testing-parallel --max-agents=4 --timeout=20 --approval-gates=before --telemetry

# Validate without executing
/team-run testing-parallel --validate

# Dry run (show plan only)
/team-run testing-parallel --dry-run

# Execution history
/team-run --history
/team-run --history testing-parallel

# Resume / status
/team-run --resume exec-20260325T163000
/team-run --status exec-20260325T163000

# Generate a new team
/team-run --init
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

### Execution History

Team executions are tracked in `.claude/teamsters-history.json`. Each entry records:
- Team name, timestamp, duration
- Agent count, success rate
- Test results (if applicable)
- Telemetry log path

Use `--history` to view past executions and identify performance trends.

### Execution Checkpointing

During execution, phase completion state is saved to `.claude/teamsters-state/<execution-id>.json`. This enables:
- **Resume**: If execution is interrupted, resume from the last completed phase
- **Status**: Inspect what was completed and what remains
- **Recovery**: Partial outputs from completed phases are preserved

Checkpoint files are automatically cleaned up after 7 days.

### File Conflict Detection

When agent definitions include `files_read` and `files_write` fields, the framework automatically detects:
- **Read-after-write dependencies**: Agent B reads a file Agent A writes (implicit dependency)
- **Write-write conflicts**: Two parallel agents write the same file (error)

Conflicts are shown during `--validate`, `--dry-run`, and the approval gate.

### Agent Templates

Agents can reduce boilerplate by extending templates:
```yaml
extends: agents/templates/webhook-enabled.md
```

Built-in templates:
- `agents/templates/webhook-enabled.md` - Standard webhook event posting
- `agents/templates/test-runner.md` - Test execution and reporting patterns
- `agents/templates/file-safety.md` - Read-before-write and rollback safety

### Agent Parameterization

Agents support template variables for reuse across teams:
```yaml
agents:
  - name: backend
    type: agents/backend-agent.md
    params:
      framework: "native-http"
      products: "lobster-catalog"
```

Variables use `{{param_name}}` syntax in the agent body and are resolved at load time.

### Sub-Skills Reference

| Sub-Skill | File | Purpose |
|-----------|------|---------|
| Team Loader | `skills/team-orchestration/team-loader.md` | Load and validate team definitions |
| Agent Schema | `skills/team-orchestration/agent-schema.md` | Agent definition format and validation |
| Coordinator Schema | `skills/team-orchestration/coordinator-schema.md` | Coordinator interface contract |
| Approval Gate Handler | `skills/team-orchestration/approval-gate-handler.md` | User approval interactions |
| Agent Lifecycle Manager | `skills/team-orchestration/agent-lifecycle-manager.md` | Agent state machine tracking |
| Resource Manager | `skills/team-orchestration/resource-manager.md` | Limits, queuing, timeouts |
| Result Aggregator | `skills/team-orchestration/result-aggregator.md` | Output merging and failure handling |
| File Conflict Detector | `skills/team-orchestration/file-conflict-detector.md` | File dependency graph analysis |
| Plan Visualizer | `skills/team-orchestration/plan-visualizer.md` | ASCII dependency graph rendering |
| Telemetry | `skills/telemetry/SKILL.md` | Non-blocking event logging |
| Event Types | `skills/telemetry/event-types.md` | Event schema definitions |
| Log Writer | `skills/telemetry/log-writer.md` | Append-only log writer |
| Model Selection | `skills/model-selection/SKILL.md` | Model resolution |
| Config Manager | `skills/model-selection/config-manager.md` | Configuration file loading |
| Model Resolver | `skills/model-selection/model-resolver.md` | Model precedence resolution |

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

**Problem**: File conflict detected between parallel agents
- **Solution**: Either add a dependency between the conflicting agents (make them sequential) or restructure so they write to different files. Use `--validate` to check for conflicts before running.

**Problem**: Agent template variables not resolved
- **Solution**: Ensure `params` are defined in the team definition's agent entry, and the agent body uses `{{param_name}}` syntax. Check that the template file exists at the path specified in `extends`.

**Problem**: Execution interrupted, want to resume
- **Solution**: Use `/team-run --status <execution-id>` to see what was completed, then `/team-run --resume <execution-id>` to continue from the last checkpoint. Checkpoints expire after 7 days.

**Problem**: Wrong model assigned to an agent
- **Solution**: Override per-agent using CLI: `TEAMSTERS_<AGENT>_MODEL=opus`. Or set in `.claude/teamsters-config.json`. Or use `--dry-run` to see model assignments before executing.

---

## Summary

The `/team-run` command is the **user entry point** for agent team orchestration. It provides:

- **Simple invocation**: `/team-run [team-name]` loads and executes a team definition
- **CLI overrides**: Fine-tune execution with `--max-agents`, `--timeout`, `--approval-gates`, and `--telemetry`
- **Clear validation**: Invalid inputs produce specific, actionable error messages
- **Pre-flight checks**: `--validate` and `--dry-run` verify configuration before executing
- **File conflict detection**: Automatic detection of write-write conflicts between parallel agents
- **Execution visibility**: Summary shows agent counts, duration, success rate, and telemetry path
- **Real-time console**: `--telemetry-console` provides live progress output during execution
- **Execution history**: `--history` tracks and compares past executions with performance trends
- **Resilient execution**: `--resume` recovers interrupted executions from checkpoints
- **Agent reuse**: Template inheritance (`extends`) and parameterization (`params`) reduce boilerplate
- **Intelligent models**: Model recommendation engine suggests optimal models per agent role
- **Team generation**: `--init` wizard scaffolds new team definitions interactively
- **Extensibility**: Users create custom teams by adding `.md` files to `teams/`
