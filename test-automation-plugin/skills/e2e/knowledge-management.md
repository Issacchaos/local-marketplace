# E2E Knowledge Management

**Version**: 1.0.0
**Parent Skill**: [E2E Testing Skill](./SKILL.md)
**Purpose**: Full specification of the `.dante/e2e-knowledge/` directory for project-specific E2E knowledge

## Overview

Dante maintains a project-specific E2E knowledge base that captures known issues and project patterns discovered during E2E test authoring and fix iterations. This knowledge is framework-agnostic in structure but framework-tagged in content, allowing some entries to be portable across frameworks (timing issues, navigation patterns) while others are framework-specific (API workarounds, selector strategies).

The knowledge base serves two purposes:
1. **Accelerate fixes** -- The fix-agent consults known issues before attempting novel fixes, applying proven resolutions first
2. **Improve classification** -- The validate-agent cross-references failures against known issues to distinguish known vs novel problems

## Directory Structure

```
{project_root}/.dante/e2e-knowledge/
  known-issues.md          # Auto-populated by fix-agent + user-maintained
  project-patterns.md      # User-maintained (free-form markdown)
```

Both files are created by the test-loop orchestrator during E2E pre-flight if they do not already exist. The orchestrator creates empty files with header comments explaining their purpose.

### Initialization

When the test-loop orchestrator detects `test_type=e2e` for the first time in a project:

1. Check if `.dante/e2e-knowledge/` directory exists
2. If not, create the directory and both files with initial content:

**Initial `known-issues.md`**:
```markdown
# E2E Known Issues

<!-- Auto-populated by Dante's fix-agent after successful novel fixes. -->
<!-- You may also add entries manually following the YAML format below. -->
<!-- Each entry is a YAML frontmatter block separated by --- delimiters. -->
```

**Initial `project-patterns.md`**:
```markdown
# E2E Project Patterns

<!-- Document your project's E2E testing patterns here. -->
<!-- This file is read by Dante's agents to understand project conventions. -->
<!-- Suggested sections: Authentication, Navigation, Components, Data Setup -->
```

## known-issues.md Format

Each known issue is a YAML frontmatter block. Multiple entries are separated by `---` delimiters. Entries are appended chronologically (newest at the bottom).

### Entry Schema

```yaml
---
id: <integer>
symptom: <string - the error message or observable failure pattern>
root_cause: <string - why this error occurs>
resolution: <string - what to do to fix it>
framework: <string - which framework discovered this ("playwright", "cypress", "selenium")>
category: <string - E2E error category ("E1", "E2", "E3", "E4", "E5", "E6")>
date_discovered: <string - ISO date "YYYY-MM-DD">
confidence: <float - 0.0 to 1.0, how reliable this resolution is>
---
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | yes | Sequential identifier, auto-incremented |
| `symptom` | string | yes | The observable error message or failure pattern. Should be specific enough to match against future failures but generic enough to catch variations. |
| `root_cause` | string | yes | Explanation of why this error occurs. Helps agents understand the underlying problem. |
| `resolution` | string | yes | The fix that resolved the issue. Should be actionable -- describe what to change in the test code. |
| `framework` | string | yes | The E2E framework that produced this error. Used for filtering when the same project uses multiple frameworks. |
| `category` | string | yes | Maps back to the E2E error taxonomy (E1-E6). Used by the validate-agent for classification. |
| `date_discovered` | string | yes | ISO 8601 date when the issue was first encountered. |
| `confidence` | float | yes | How reliable this resolution is. Range 0.0-1.0. See auto-population rules for how this is set. |

### Example Entries

```yaml
---
id: 1
symptom: "TimeoutError waiting for element"
root_cause: "Element renders after async data load"
resolution: "Wait for element visibility before interacting"
framework: "playwright"
category: "E2"
date_discovered: "2026-02-13"
confidence: 0.9
---

---
id: 2
symptom: "strict mode violation, locator resolved to 3 elements"
root_cause: "Multiple submit buttons on page, test uses generic button selector"
resolution: "Use getByRole('button', { name: 'Submit Order' }) instead of generic button selector"
framework: "playwright"
category: "E1"
date_discovered: "2026-02-14"
confidence: 0.7
---

---
id: 3
symptom: "Expected URL /dashboard but received /login"
root_cause: "Auth token expired between test setup and navigation"
resolution: "Regenerate auth state in test beforeEach or use storageState fixture"
framework: "playwright"
category: "E3"
date_discovered: "2026-02-15"
confidence: 0.9
---
```

## project-patterns.md Structure

This file is free-form markdown maintained by the user (or seeded by the analyze-agent during initial exploration). It documents project-specific conventions that help agents generate better E2E tests.

### Suggested Sections

```markdown
# E2E Project Patterns

## Authentication

<!-- How does authentication work in this app? -->
<!-- Example: OAuth2 flow, session cookies, JWT tokens -->
<!-- What test accounts exist? How to set up auth state? -->

## Navigation

<!-- How is routing structured? -->
<!-- Example: SPA with React Router, server-rendered pages -->
<!-- Key routes and their purposes -->

## Components

<!-- Naming conventions for test IDs -->
<!-- Example: data-testid="login-form-submit" follows {feature}-{component}-{action} -->
<!-- Common component patterns (modals, dropdowns, tables) -->

## Data Setup

<!-- How should test data be seeded? -->
<!-- Example: API calls in beforeEach, database fixtures, factory functions -->
<!-- Cleanup requirements -->

## Environment

<!-- Required environment variables -->
<!-- Base URL configuration -->
<!-- External service dependencies and how to mock them -->
```

Agents read this file to understand project context. The analyze-agent uses it to identify test targets and conventions. The write-agent uses it to follow established patterns. The fix-agent uses it to understand why certain patterns exist.

## Auto-Population Rules

The fix-agent automatically appends entries to `known-issues.md` after successfully resolving a **novel** issue (one not already in the knowledge base).

### When to Append

1. The fix-agent resolves a test failure
2. The validate-agent had flagged the failure as **novel** (no match in `known-issues.md`)
3. The fix is verified as successful (test passes after the fix)

### Confidence Scoring

| Scenario | Confidence | Rationale |
|----------|------------|-----------|
| Fix succeeded on first attempt | 0.9 | High confidence -- the resolution worked immediately |
| Fix succeeded after retry (2+ attempts) | 0.7 | Lower confidence -- required iteration, resolution may not generalize |
| User manually adds entry | User-specified | User determines confidence based on their knowledge |

### Entry Construction

The fix-agent constructs the entry from available context:

- `id`: Increment from the highest existing ID in the file (or start at 1)
- `symptom`: The original error message from the test failure output
- `root_cause`: The fix-agent's analysis of why the error occurred
- `resolution`: Description of what the fix-agent changed to resolve the error
- `framework`: The current E2E framework from detection output
- `category`: The E2E error category (E1-E6) from the validate-agent's classification
- `date_discovered`: Current date in ISO format
- `confidence`: 0.9 or 0.7 based on attempt count (see table above)

### Deduplication

Before appending, the fix-agent checks existing entries:
- If an entry with a matching `symptom` AND `category` already exists, do NOT append a duplicate
- If the same symptom maps to a different category, this is a distinct entry (append it)
- Symptom matching uses substring containment, not exact equality, to catch variations

## Consumption Rules

### When to Load

Agents load the knowledge base when ALL of these conditions are met:

1. `test_type=e2e` (E2E framework detected)
2. Framework detection confidence >= 0.8
3. `.dante/e2e-knowledge/` directory exists

If the directory does not exist and this is the first E2E detection, the test-loop orchestrator creates it during pre-flight (see Initialization above).

### Validate Agent Consumption

The validate-agent reads `known-issues.md` during error classification:

1. For each test failure, extract the symptom (error message)
2. Search `known-issues.md` for entries where the stored `symptom` is a substring of the current error message (or vice versa)
3. If a match is found with confidence >= 0.7:
   - Flag the failure as a **known issue**
   - Use the stored `category` as classification guidance
   - Include the stored `resolution` in the classification output for the fix-agent
4. If no match is found:
   - Flag the failure as **novel**
   - Proceed with standard classification using error patterns from the framework reference

### Fix Agent Consumption

The fix-agent reads `known-issues.md` before attempting any fix:

1. Receive the failure classification from the validate-agent
2. If the validate-agent flagged a known issue match:
   - Apply the stored `resolution` as the first fix attempt
   - Weight by `confidence` -- higher confidence resolutions are tried first if multiple matches exist
3. If no known issue match:
   - Proceed with framework-specific fix strategies from `skills/e2e/frameworks/{framework}.md`
4. After a successful fix of a novel issue:
   - Append a new entry per the auto-population rules above

### Analyze Agent Consumption

The analyze-agent reads `project-patterns.md` during E2E analysis:

1. Load project conventions (auth flows, navigation patterns, component naming)
2. Use conventions to inform test target identification
3. Pass loaded patterns to the write-agent via analysis output

## Framework Portability

Knowledge entries are tagged with a `framework` field, but some knowledge is portable across frameworks:

| Knowledge Type | Portable? | Example |
|---------------|-----------|---------|
| Timing patterns | Yes | "Element renders after async data load" applies to any framework |
| Navigation patterns | Yes | "Auth redirect on expired session" is framework-independent |
| Selector strategies | Partially | "Use data-testid for this component" is portable; the API differs |
| API workarounds | No | "Use page.route() for mocking" is Playwright-specific |
| Fix code patterns | No | Specific code changes reference framework APIs |

Agents should consider entries from other frameworks when the `root_cause` and `resolution` describe a concept (not a specific API call). The `framework` tag helps agents filter when looking for API-specific guidance.

---

**Last Updated**: 2026-02-16
**Status**: Phase 1 - Knowledge management convention defined
**Next**: Integration with test-loop orchestrator for automatic initialization
