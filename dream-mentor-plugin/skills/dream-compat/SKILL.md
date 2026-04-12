# Dream Compatibility Layer Skill

**Description**: Maps dream-mentor's memory format to Claude's built-in `/dream` command format, enabling migration when the native feature becomes available.

**Trigger**: Used by `/mentor migrate` subcommand.

---

## Overview

Claude Code has a built-in `/dream` command (currently unreleased or in development). This plugin uses `/mentor` to avoid name collision. The dream-compat skill provides a bridge so that dream states created with `/mentor` can be exported to the built-in format when it becomes available.

### Design Principles

1. **Forward-compatible storage**: Dream memory files use a generic markdown+frontmatter format that can be transformed to any target schema
2. **Lossless export**: All analyzed content (structure, patterns, deps, conventions, summary) is preserved during migration
3. **Non-destructive**: Migration creates new files in the built-in format; original `.claude/dreams/` data is preserved until the user explicitly runs `/mentor forget`
4. **Adaptable**: The format mapper is isolated in this skill, so only this file needs updating when the built-in format is documented

---

## Current State

The built-in `/dream` format is not yet fully documented. This skill provides:

1. **Portable JSON export** — an intermediate format that captures all dream state data
2. **Format mapper interface** — a clear contract for transforming to the native format
3. **Migration workflow** — the end-to-end process for `/mentor migrate`

When the built-in format is known, only the **Format Mapper** section below needs updating.

---

## Portable Export Format

Until the built-in format is documented, `/mentor migrate` exports dreams as portable JSON:

### Export Location

```
.claude/dreams/_export/
  <dream-name>.json              # One file per dream
  manifest.json                  # Export manifest with metadata
```

### Dream Export Schema

```json
{
  "schema_version": "1.0.0",
  "exported_at": "2026-03-28T10:00:00.000Z",
  "exported_by": "dream-mentor-plugin@1.0.0",
  "dream": {
    "name": "architecture-ref",
    "source": {
      "type": "github",
      "url": "https://github.com/org/repo",
      "branch": "main",
      "commit": "abc123def456",
      "analyzed_at": "2026-03-28T09:00:00.000Z"
    },
    "layer": {
      "priority": 1,
      "active": true,
      "tags": ["architecture", "patterns"]
    },
    "analysis": {
      "structure": "... full content of structure.md ...",
      "patterns": "... full content of patterns.md ...",
      "dependencies": "... full content of dependencies.md ...",
      "conventions": "... full content of conventions.md ...",
      "summary": "... full content of summary.md ..."
    }
  }
}
```

### Export Manifest Schema

```json
{
  "schema_version": "1.0.0",
  "exported_at": "2026-03-28T10:00:00.000Z",
  "dream_count": 2,
  "dreams": [
    {
      "name": "architecture-ref",
      "file": "architecture-ref.json",
      "source_type": "github",
      "priority": 1
    },
    {
      "name": "testing-patterns",
      "file": "testing-patterns.json",
      "source_type": "local",
      "priority": 2
    }
  ]
}
```

---

## Format Mapper Interface

The format mapper transforms portable JSON to the built-in `/dream` format.

### Contract

```
Input:  Portable dream JSON (schema above)
Output: Files in the built-in /dream format, written to the correct location

Steps:
1. Read portable JSON
2. Map fields to built-in schema
3. Write to built-in location
4. Validate the output
```

### Current Implementation (Stub)

Until the built-in format is known, the mapper:
1. Exports portable JSON to `.claude/dreams/_export/`
2. Displays a message explaining the export is ready for manual conversion
3. Returns success with the export path

### Future Implementation

When the built-in format is documented, update this section with:
- The target file format and location
- Field mapping from portable JSON to native schema
- Any data transformations needed (e.g., markdown → structured data)
- Validation rules for the native format

---

## Migration Workflow

### `/mentor migrate` Execution

```
1. Validate dreams exist
   - Read DREAMS.md
   - If no dreams loaded: error with suggestion to /mentor load first

2. Select dreams to migrate
   - --name <name>: single dream
   - --all: all active dreams
   - Neither: prompt user with AskUserQuestion

3. For each dream:
   a. Read all memory files (structure, patterns, deps, conventions, summary)
   b. Read source.json and layer.json
   c. Assemble portable JSON
   d. Run format mapper (currently: write portable JSON)
   e. Validate output

4. Write export manifest

5. Display migration summary
   - List each dream and its migration status
   - Show export location
   - Explain next steps
```

### Post-Migration Options

After migration, the user can:
- **Keep both**: Run `/mentor` and built-in `/dream` side by side
- **Clean up**: Run `/mentor forget --all` to remove old format
- **Verify**: Use the built-in `/dream` to confirm imported states work

---

## Detecting the Built-in `/dream`

To detect whether Claude's built-in `/dream` is available (for future auto-migration prompts):

1. Check if `/dream` is registered as a built-in command (not from this plugin)
2. If detected, suggest migration: `"Claude's built-in /dream is now available. Run /mentor migrate to export your dreams."`
3. Do NOT auto-migrate — always require explicit user action

---

## Versioning

The portable export format uses `schema_version` to handle future changes:

- `1.0.0` — Current: raw markdown analysis content in JSON wrapper
- Future versions may restructure the analysis into more granular fields

The format mapper should check `schema_version` and handle older exports gracefully.
