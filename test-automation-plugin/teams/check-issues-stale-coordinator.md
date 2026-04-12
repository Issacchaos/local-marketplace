# Check Issues Stale - Coordinator

**Team**: check-issues-stale
**Version**: 1.0.0

---

## Coordinator Overview

This coordinator orchestrates a 4-agent audit team that checks all open GitHub
issues against the current codebase. All agents run in parallel, each investigating
a subset of issues. After all agents report back, the coordinator posts GitHub
comments on issues that appear resolved.

---

## Pre-Flight

Before spawning agents, run `gh issue list --state open --limit 100` to get the
current list of open issues. Pass the relevant issue numbers to each agent.

---

## Phase 1: All Agents (Parallel)

### Agent: issue-auditor-bugs

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are auditing open GitHub issues labeled as bugs or broken behavior in the
dante_plugin repository. For each issue below, investigate the codebase to
determine if the issue has been resolved.

## Issues to Investigate

1. **#146 - Plugin Rename caused issues**
   - Check: Was the plugin successfully renamed? Are there broken references
     from a rename? Search for old plugin name references, check plugin.json,
     commands, skill references.

2. **#102 - Test files placed in wrong location (.claude-tests vs project dir)**
   - Check: Does the test-location-detection skill now correctly place test files
     in the project directory rather than .claude-tests/? Search for
     ".claude-tests" references in skills and see if there's logic to avoid it.

3. **#99 - Team-run command needs to intelligently generate a team file rather than prompt for one**
   - Check: Does the /team-run command now handle the case where a team
     definition doesn't exist? Read commands/team-run.md and check if it has
     logic to create team files on the fly.

4. **#53 - Bug: Generates tests for impossible/unreachable scenarios**
   - Check: Is there logic in test-generation skills to filter out unreachable
     code paths or impossible scenarios? Search for "unreachable", "impossible",
     "dead code" in skill files.

## How to Investigate

For each issue:
1. Read the issue description: `gh issue view <number>`
2. Search the codebase for relevant code changes, config, or skill instructions
3. Check git log for commits that reference the issue number
4. Assess whether the described problem still exists

## Output Format

For each issue, produce:

### Issue #NNN - Title
- **Status**: RESOLVED | OPEN | UNCLEAR
- **Evidence**: What you found in the codebase (file paths, code snippets, commits)
- **Confidence**: HIGH | MEDIUM | LOW
- **Summary**: 1-2 sentence explanation

Then produce a final summary table.
```

---

### Agent: issue-auditor-enhancements-core

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are auditing open GitHub enhancement issues related to core plugin workflows
in the dante_plugin repository. For each issue below, investigate the codebase to
determine if the enhancement has been implemented.

## Issues to Investigate

1. **#148 - Programmatic workflow enforcement: prevent LLM from skipping phases in /test-generate and /test-loop**
   - Check: Is there enforcement logic in test-generate or test-loop commands/skills
     that prevents skipping workflow phases? Look for phase validation, state
     tracking, or guard conditions.

2. **#131 - Rename last-analysis.md to a more Dante-specific filename**
   - Check: Is "last-analysis.md" still used, or has it been renamed? Search for
     "last-analysis" across the codebase.

3. **#115 - Separate manually created tests from dante-generated tests**
   - Check: Is there a mechanism to distinguish manually written tests from
     generated ones? Look for markers, comments, or separate directories.

4. **#114 - Better document in projects how to run generated tests**
   - Check: Do generated test files include run instructions? Is there a README
     or comment block generated alongside tests?

5. **#112 - Auto ignore test reports and other files**
   - Check: Is there logic to auto-add test reports to .gitignore? Search for
     ".gitignore" in skills and commands.

6. **#55 - Enhancement: Check existing test coverage before generating new tests**
   - Check: Does the test generation workflow check for existing tests before
     generating? Look for coverage checks or existing test detection.

7. **#56 - Enhancement: Use beforeEach and scoped variables to reduce test duplication**
   - Check: Do test generation templates use beforeEach/setup patterns? Check
     skills/templates/ and test-generation skill instructions.

## How to Investigate

For each issue:
1. Read the issue description: `gh issue view <number>`
2. Search the codebase for relevant code changes, config, or skill instructions
3. Check git log for commits that reference the issue number
4. Assess whether the described enhancement has been implemented

## Output Format

For each issue, produce:

### Issue #NNN - Title
- **Status**: RESOLVED | OPEN | UNCLEAR
- **Evidence**: What you found in the codebase (file paths, code snippets, commits)
- **Confidence**: HIGH | MEDIUM | LOW
- **Summary**: 1-2 sentence explanation

Then produce a final summary table.
```

---

### Agent: issue-auditor-enhancements-features

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are auditing open GitHub enhancement issues related to new features and
integrations in the dante_plugin repository. For each issue below, investigate
the codebase to determine if the feature has been implemented.

## Issues to Investigate

1. **#145 - Add dedicated E2E test debugging entry point with browser exploration as first action**
   - Check: Is there an E2E debugging command or skill? Search for "e2e" and
     "browser exploration" in commands and skills.

2. **#61 - Include E2E test analysis when test-analyze is invoked**
   - Check: Does /test-analyze include E2E analysis? Read the test-analyze
     command and skill for E2E references.

3. **#59 - Currently there are no skills for Swift or Kotlin for Mobile testing**
   - Check: Are there Swift or Kotlin test templates or skills? Search for
     "swift", "kotlin", "mobile" in skills/.

4. **#51 - Integration: Localstack support for AWS service testing**
   - Check: Is there Localstack integration? Search for "localstack" in skills.

5. **#50 - Integration: TDS (Test Data Service) support for load testing**
   - Check: Is there TDS integration? Search for "TDS", "test data service",
     "load testing" in skills.

6. **#49 - Enhancement: Generate shared fixtures/mocks to reduce duplication**
   - Check: Is there a shared fixtures/mocks generation capability? Search for
     "fixture", "shared mock", "helper-extraction" in skills.

7. **#48 - Feature: Test quality analysis for existing tests**
   - Check: Is there a test quality analysis feature? Search for "quality",
     "test quality", "analysis" in skills and commands.

8. **#52 - Enhancement: Don't test private methods by default (configurable)**
   - Check: Is there configuration to skip private methods? Search for "private",
     "access modifier", "configurable" in test generation skills.

## How to Investigate

For each issue:
1. Read the issue description: `gh issue view <number>`
2. Search the codebase for relevant code changes, config, or skill instructions
3. Check git log for commits that reference the issue number
4. Assess whether the described feature has been implemented

## Output Format

For each issue, produce:

### Issue #NNN - Title
- **Status**: RESOLVED | OPEN | UNCLEAR
- **Evidence**: What you found in the codebase (file paths, code snippets, commits)
- **Confidence**: HIGH | MEDIUM | LOW
- **Summary**: 1-2 sentence explanation

Then produce a final summary table.
```

---

### Agent: issue-auditor-meta

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are auditing open GitHub issues related to meta concerns, documentation,
tooling, and backlog items in the dante_plugin repository. For each issue below,
investigate the codebase to determine if the issue has been addressed.

## Issues to Investigate

1. **#136 - Add skill-creator plugin to claude-pr-assistant GHA**
   - Check: Is there a skill-creator integration in GitHub Actions? Search for
     "skill-creator" and check .github/workflows/.

2. **#117 - Issues submitted through the feedback label**
   - Check: This is a tracking/meta issue. Check if /feedback command works and
     routes issues correctly. May be a perpetually open meta-issue.

3. **#83 - Added /dante:help which omits the getting_started.md**
   - Check: Does /help (or equivalent) include getting_started.md content? Read
     the help command and check for getting_started references.

4. **#76 - Investigate Epic Marketplace Install count**
   - Check: This is an investigation task, not a code issue. Likely still open
     unless there's documentation about marketplace metrics.

5. **#74 - Explore Agent Teams**
   - Check: Agent teams have been implemented (teams/ directory exists, /team-run
     command exists). This exploration issue may be resolved.

6. **#66 - Prompt to install `gh` via choco instead of giving md file during /feedback**
   - Check: Does the feedback command check for gh installation and offer choco
     install? Read the feedback command/skill for gh detection logic.

7. **#47 - Does /feedback lookup docs first? Enhancement: Add doc lookup**
   - Check: Does /feedback look up docs before submitting? Read the feedback
     skill for documentation lookup logic.

8. **#60 - Improve /feedback workflow: Auto-generate title from description**
   - Check: Does /feedback auto-generate issue titles? Read the feedback command
     for title generation logic.

## How to Investigate

For each issue:
1. Read the issue description: `gh issue view <number>`
2. Search the codebase for relevant code changes, config, or skill instructions
3. Check git log for commits that reference the issue number
4. Assess whether the described issue has been addressed

## Output Format

For each issue, produce:

### Issue #NNN - Title
- **Status**: RESOLVED | OPEN | UNCLEAR
- **Evidence**: What you found in the codebase (file paths, code snippets, commits)
- **Confidence**: HIGH | MEDIUM | LOW
- **Summary**: 1-2 sentence explanation

Then produce a final summary table.
```

---

## Phase 2: Result Aggregation and GitHub Comments

After all 4 agents complete, the coordinator:

### Step 1: Aggregate Results

Combine all agent reports into a single summary:

```markdown
# Issue Staleness Audit Report

## Summary
- Total issues audited: {count}
- RESOLVED (high confidence): {count}
- RESOLVED (medium/low confidence): {count}
- OPEN: {count}
- UNCLEAR: {count}

## Resolved Issues (Action Required)
| Issue | Title | Confidence | Evidence Summary |
|-------|-------|------------|-----------------|
| #NNN  | ...   | HIGH       | ...             |

## Still Open Issues
| Issue | Title | Notes |
|-------|-------|-------|
| #NNN  | ...   | ...   |

## Unclear Issues (Needs Manual Review)
| Issue | Title | Notes |
|-------|-------|-------|
| #NNN  | ...   | ...   |
```

### Step 2: Post GitHub Comments on Resolved Issues

For each issue marked RESOLVED with HIGH or MEDIUM confidence, post a comment
using `gh issue comment`:

```bash
gh issue comment <number> --body "## Automated Staleness Audit

This issue appears to have been **resolved** based on a codebase audit.

**Evidence**:
{evidence from agent report}

**Confidence**: {HIGH|MEDIUM}

---
_This comment was generated by an automated issue audit. A human should review
the evidence above and close this issue if confirmed resolved._

_Audit date: $(date +%Y-%m-%d)_"
```

**Important**: Do NOT close issues automatically. Only add the comment for human review.

For UNCLEAR issues, post a shorter comment:

```bash
gh issue comment <number> --body "## Automated Staleness Audit

This issue has an **unclear** resolution status. Some related changes were found
but it's not certain the issue is fully resolved.

**Notes**:
{notes from agent report}

---
_This comment was generated by an automated issue audit. A human should review
and determine if this issue can be closed._

_Audit date: $(date +%Y-%m-%d)_"
```

### Step 3: Display Final Report

Show the aggregated report to the user with a summary of comments posted.
