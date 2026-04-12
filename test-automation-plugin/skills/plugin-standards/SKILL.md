---
name: plugin-standards
description: Dante plugin-specific development standards. Use when contributing to the plugin, adding new skills/commands, or understanding plugin architecture. NOT for downstream users.
user-invocable: false
---

# Dante Plugin Development Standards

**Version**: 1.0.0
**Category**: Internal Development
**Purpose**: Document Dante-specific project conventions and architecture patterns

## Overview

This skill defines the Dante plugin's specific directory structure, file organization patterns, and contribution workflows. It focuses on what makes THIS plugin unique, not general coding standards.

## Dante Plugin Architecture

### Project Structure

```
dante_plugin/
├── commands/              # User-facing commands (in plugin.json)
├── skills/                # Internal utility skills (NOT in plugin.json)
├── subagents/             # Specialized workflow agents
├── docs/                  # User-facing documentation
├── tests/                 # Plugin code tests
├── test_samples/          # Sample projects for validation
├── .sdd/                  # Spec-driven development docs
└── .claude-plugin/
    └── plugin.json        # Plugin manifest
```

### Commands (`commands/`)
User-facing commands exposed to downstream plugin users:
- **Format**: Markdown files (`.md`)
- **Naming**: `{command-name}.md` (e.g., `test-generate.md`, `test-loop.md`)
- **Registration**: Must be listed in `plugin.json` `commands` array
- **Purpose**: Direct user interaction via `/command-name`
- **Current Commands**: test-analyze, test-generate, test-loop, test-resume, feedback

### Skills (`skills/`)
Internal utility modules for commands and subagents (NOT exposed to users):
- **Format**: Directory with `SKILL.md` file
- **Naming**: `skills/{skill-name}/SKILL.md`
- **Registration**: NOT in `plugin.json` - internal only
- **Purpose**: Detection logic, templates, reference documentation
- **Frontmatter Required**:
  ```yaml
  ---
  name: skill-name
  description: When to use this skill (one sentence)
  user-invocable: false
  ---
  ```
- **Current Skills**: framework-detection, project-detection, test-generation, result-parsing, state-management, linting, model-selection, redundancy-detection, helper-extraction, build-integration, test-location-detection, templates

### Subagents (`subagents/`)
Specialized agents for complex multi-step workflows:
- **Format**: Directory with agent definition
- **Purpose**: Autonomous task execution
- **Examples**: Test generation agents, analysis agents

### Test Generation Templates (`skills/templates/`)
Language and framework-specific code generation patterns:
- **Format**: Markdown files
- **Naming**: `{language}-{framework}-template.md`
- **Examples**: `python-pytest-template.md`, `javascript-jest-template.md`
- **Purpose**: Consistent test code generation across languages

## Dante-Specific File Organization

### Skill SKILL.md Template
Dante skills follow this structure:

```markdown
---
name: skill-name
description: When to use this skill (one sentence)
user-invocable: false
---

# Skill Name

**Version**: X.Y.Z
**Category**: Analysis | Generation | Execution | Internal
**Purpose**: One-line purpose statement

## Overview
High-level description

## Skill Interface (if applicable)
### Input
### Output

## Implementation Details
Core logic and algorithms

## Usage in Commands/Agents
How other components should use this skill

## Error Handling
Edge cases and fallback behavior

## Testing
Validation approach

## References
Related files, documentation

---
**Last Updated**: YYYY-MM-DD
**Status**: Active | Deprecated | Experimental
```

**Key Points:**
- Frontmatter is required for skill discovery
- `user-invocable: false` prevents skills from appearing in the user's `/` command menu (skills are internal-only; only commands should be user-invocable)
- Version and Last Updated help track changes
- Usage section shows how commands/agents reference the skill
- Status indicates lifecycle (Active | Deprecated | Experimental)

### Command File Template
Dante commands are user-facing and follow this structure:

```markdown
# /command-name

Brief description

## Overview
What this command does

## Usage
How users invoke it

## Options/Parameters
Available flags and arguments

## Workflow
Step-by-step process

## Examples
Common use cases

## Error Handling
What can go wrong and how to fix it
```

**Key Points:**
- Commands are the user interface to the plugin
- Must be registered in `plugin.json` to be callable
- Should reference relevant skills in workflow sections

## Dante Documentation Locations

### Plugin Root Documentation
- **README.md**: Quick start, features, installation overview
- **USER_GUIDE.md**: Comprehensive user guide for all commands
- **INSTALLATION.md**: Detailed installation instructions
- **MARKETPLACE_INSTALLATION.md**: Marketplace-specific install guide
- **CHANGELOG.md**: Version history and changes
- **SECURITY.md**: Security policies and reporting
- **DOCUMENTATION_UPDATES.md**: Documentation change tracking

### docs/ Directory
- User-facing guides and tutorials
- Extended documentation linked from README.md

### .sdd/ Directory
- Spec-driven development documents
- Specs, plans, tasks, and progress tracking for features
- Architecture decisions and planning

### Skills Documentation
- Each skill has a SKILL.md with detailed implementation notes
- Skills are NOT user-facing documentation

## Dante Testing Structure

### tests/ Directory
- Plugin code tests using pytest
- Tests for Python-based components if any

### test_samples/ Directory
- Sample projects for manual validation
- Used to test framework detection, test generation, etc.
- Represent real-world project structures

### Skill Validation
- Document expected outcomes in each SKILL.md
- Validate skills with sample projects from test_samples/

## Dante Version Management

### Plugin Manifest
Dante uses `.claude-plugin/plugin.json` as the single source of truth for plugin metadata:

**Key fields:**
- **name**: "dante" (plugin identifier)
- **version**: Semantic versioning (e.g., "2.1.1")
- **description**: Brief plugin description
- **author**: Test Automation
- **license**: MIT
- **commands**: Array of command file paths
- **repository**: GitHub repository URL
- **homepage**: GitHub README URL
- **keywords**: Search/discovery tags

**When to update:**
- Version changes (major.minor.patch)
- New commands added/removed
- Description or metadata changes
- Repository information updates

### Skill Versioning
- Skills version independently in their SKILL.md files
- Skills are internal, so version changes don't affect users
- Update skill version when interface or behavior changes

### CHANGELOG.md
- Update before each plugin release
- Track version history at the plugin level

### Automated Versioning (GitHub Actions)

Dante uses **automated versioning** via GitHub Actions when PRs are approved for merge to main:

**Workflow**: `.github/workflows/auto-version-on-approval.yml`
**Script**: `.github/scripts/version-analyzer.py`

**How it works:**
1. **Trigger**: When a PR targeting `main` is approved
2. **Analysis**: Claude AI analyzes:
   - Changed files
   - Commit messages
   - PR title and description
3. **Decision**: Claude determines version bump type:
   - **MAJOR**: Breaking changes, incompatible API changes
   - **MINOR**: New features, commands, significant functionality
   - **PATCH**: Bug fixes, documentation, small tweaks
4. **Update**: Automatically updates:
   - `.claude-plugin/plugin.json` version field
   - `CHANGELOG.md` with categorized changes
5. **Commit**: Commits changes to PR branch with attribution
6. **Merge**: Enables auto-merge after version bump

**Required Setup:**
- GitHub Secret: `ANTHROPIC_API_KEY` (Claude API key)
- Repository permissions: Allow GitHub Actions to commit and merge

**Semantic Versioning Philosophy:**
- Conservative approach: when uncertain, choose smaller bump
- Breaking changes are rare: only for user-impacting API changes
- New commands/features are MINOR bumps
- Internal refactoring, docs, bug fixes are PATCH bumps

**Manual Override:**
If you need to manually set a version (e.g., for special releases):
1. Update `.claude-plugin/plugin.json` version in your PR before approval
2. The automation will detect the version is already bumped and skip

**Changelog Format:**
Generated changelog entries follow this structure:
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Modifications to existing features

### Fixed
- Bug fixes

### Documentation
- Documentation updates

### Internal
- Internal changes not visible to users
```

## Dante Contribution Workflow

### Adding a New Skill
1. Create directory: `skills/{skill-name}/`
2. Create `SKILL.md` with required frontmatter (must include `user-invocable: false`)
3. Document interface, usage, error handling
4. Add references in relevant command files
5. Update this standards document if introducing new patterns
6. Do NOT add to `plugin.json` (skills are internal)

### Adding a New Command
1. Create file: `commands/{command-name}.md`
2. Follow command structure template
3. **Add to `plugin.json`** in `commands` array
4. Update README.md if user-facing
5. Document in USER_GUIDE.md
6. Test end-to-end workflow

### Adding a New Subagent
1. Create directory: `subagents/{agent-name}/`
2. Define agent interface and behavior
3. Document usage in relevant commands
4. Test with real projects

### Updating Existing Components
1. Read existing file completely first
2. Make targeted changes only
3. Update version number if significant
4. Update "Last Updated" date
5. Update references if interface changes
6. Test affected workflows

## Dante Deprecation Workflow

### Deprecating a Skill
1. Update status to "Deprecated" in SKILL.md
2. Document replacement/migration path
3. Keep for at least one minor version
4. Remove in next major version

### Deprecating a Command
1. Update command documentation with deprecation notice
2. Suggest alternative command
3. Keep functional for at least one major version
4. Remove from `plugin.json` when removing

## Dante Release Checklist

Before releasing a new version:
- [ ] Version updated in `.claude-plugin/plugin.json`
- [ ] CHANGELOG.md updated with new version
- [ ] All commands listed correctly in `.claude-plugin/plugin.json`
- [ ] README.md reflects current features
- [ ] USER_GUIDE.md updated if commands changed
- [ ] Skills documentation current
- [ ] Sample projects in test_samples/ tested
- [ ] Breaking changes documented (if any)
- [ ] Git tag created for version

## Key Dante Concepts

### Project-Private Skills
Skills in the `skills/` directory are **NOT** exposed to downstream users:
- They are internal implementation details
- Reusable by commands and subagents within Dante
- Not listed in `plugin.json` (only commands are)
- Can change without being a breaking change for users
- Must have frontmatter for proper organization
- Must include `user-invocable: false` in frontmatter to hide from the `/` command menu

**To create a project-private skill:**
1. Add to `skills/{skill-name}/` directory
2. Create `SKILL.md` with required frontmatter (including `user-invocable: false`)
3. Do NOT add to `plugin.json` commands array
4. Reference from commands or subagents via skill paths
5. Document for internal developer use only

### Commands vs Skills
- **Commands**: User-facing, in `plugin.json`, invoked with `/command-name`
- **Skills**: Internal-only, NOT in `plugin.json`, referenced by commands/subagents

## References

- Dante Repository: https://github.example.com/my-org/my-plugin.git
- README.md: Plugin overview and quick start
- USER_GUIDE.md: Comprehensive command documentation
- INSTALLATION.md: Setup instructions

---

**Last Updated**: 2026-02-12
**Status**: Active
