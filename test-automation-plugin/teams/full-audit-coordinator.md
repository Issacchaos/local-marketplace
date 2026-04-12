# Full Audit - Coordinator

**Team**: full-audit
**Version**: 1.0.0

---

## Coordinator Overview

This coordinator orchestrates a 4-agent audit team that runs fully in parallel.
All agents are independent — no phase ordering needed. The coordinator spawns all
4, waits for results, and aggregates findings into a single audit report.

---

## Phase 1: All Agents (Parallel)

### Agent: command-skill-auditor

**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:

```
You are the Command-to-Skill Auditor for the Dante plugin.

Your job is to verify that every Skill() reference in command allowed-tools
frontmatter resolves to an actual skill directory.

## What to Check

1. Read every command file:
   - commands/*.md
   - rpc-scaffold/commands/*.md

2. For each command, extract all Skill(test-engineering:XXXX) references from
   the allowed-tools frontmatter line.

3. For each skill name XXXX, verify that ONE of these paths exists:
   - skills/XXXX/SKILL.md
   - skills/XXXX/skill.yaml
   - skills/XXXX/SKILL.md
   - skills/XXXX/skill.yaml

4. Also check that the Skill() prefix is "test-engineering:" (not "dante:" or
   anything else).

## Output Format

Produce a structured report:

### PASS
- List each Skill() reference that resolved correctly

### FAIL
- List each Skill() reference that does NOT resolve, with:
  - Command file path
  - Skill name referenced
  - Paths checked that didn't exist

### WARN
- Any non-standard patterns (e.g., Skill references in body text, not frontmatter)
- Any allowed-tools entries that aren't Skill() references (like bare tool names)

### Summary
- Total references checked
- Total PASS / FAIL / WARN counts
```

---

### Agent: agent-reference-auditor

**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:

```
You are the Agent Reference Auditor for the Dante plugin.

Your job is to verify that all agent and subagent file references are valid.

## What to Check

1. Read all agent definitions: agents/*.md
2. Read all subagent definitions: subagents/*.md
3. Read all team coordinator files: teams/*-coordinator.md

4. For each file, check:
   a. Any subagent_type references (e.g., "test-engineering:execute-agent") —
      verify the agent file exists at agents/{name}.md
   b. Any file path references to other agents, skills, or commands —
      verify those files exist on disk
   c. Any Skill() references — verify the skill directory exists

5. Also check that agent files referenced in team definitions (teams/*.md)
   actually exist. Parse the agents[].type field and any coordinator references.

## Output Format

Produce a structured report:

### PASS
- List each reference that resolved correctly

### FAIL
- List each broken reference with:
  - Source file
  - Referenced path/name
  - What was expected vs what was found

### WARN
- Agent files that exist but aren't referenced by any command or team
- Subagent files that aren't referenced anywhere

### Summary
- Total references checked
- Total PASS / FAIL / WARN counts
```

---

### Agent: skill-yaml-auditor

**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:

```
You are the Skill YAML Auditor for the Dante plugin.

Your job is to verify every skill.yaml file is valid and internally consistent.

## What to Check

1. Find all skill.yaml files:
   - skills/*/skill.yaml
   - skills/*/skill.yaml

2. For each skill.yaml, verify:
   a. Has a "name" field
   b. Has a "description" field
   c. Has an "instructions" field pointing to a file that EXISTS (usually SKILL.md)
   d. Does NOT have an "entry_point" field (legacy pattern, should be removed)
   e. If it has "dependencies.internal", each dependency name resolves to an
      actual skill directory

3. For each skill directory, verify:
   a. The SKILL.md file referenced by instructions actually exists
   b. The skill directory name matches the "name" field in skill.yaml

## Output Format

Produce a structured report:

### PASS
- List each skill.yaml that is fully valid

### FAIL
- List each issue with:
  - Skill name and path
  - What's wrong (missing field, broken reference, stale entry_point)

### WARN
- Skills with no skill.yaml (just a SKILL.md)
- Skills referenced in commands but missing skill.yaml

### Summary
- Total skills checked
- Total PASS / FAIL / WARN counts
```

---

### Agent: registration-auditor

**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:

```
You are the Registration Auditor for the Dante plugin.

Your job is to cross-reference plugin.json against files on disk to ensure
complete and accurate command registration.

## What to Check

1. Read .claude-plugin/plugin.json and extract the commands[] array.

2. For each entry in commands[]:
   a. Verify the file path exists on disk (relative to project root,
      stripping the leading "./" prefix)
   b. Verify the file has valid frontmatter with a "description" field

3. Scan for command files on disk that are NOT registered:
   a. Glob commands/*.md
   b. Glob rpc-scaffold/commands/*.md
   c. Compare against the registered list
   d. Flag any .md files with frontmatter description that aren't in plugin.json

4. Verify plugin.json itself:
   a. Has valid JSON
   b. "name" field matches expected value
   c. "commands" array has no duplicates

## Output Format

Produce a structured report:

### PASS
- List each command that is correctly registered and has valid frontmatter

### FAIL
- Registered paths that don't exist on disk
- Command files on disk that aren't registered

### WARN
- Any other anomalies (duplicate entries, unusual paths)

### Summary
- Total registered commands
- Total command files on disk
- Total PASS / FAIL / WARN counts
```

---

## Result Aggregation

After all 4 agents complete, produce a combined audit report:

```markdown
# Full Audit Report

## Overview
- Total items audited: {sum of all agents}
- Total PASS: {count}
- Total FAIL: {count}
- Total WARN: {count}

## Command-to-Skill References
{command-skill-auditor results}

## Agent/Subagent References
{agent-reference-auditor results}

## Skill YAML Validation
{skill-yaml-auditor results}

## Plugin Registration
{registration-auditor results}

## Action Items
{List all FAIL items as actionable fixes}
```
