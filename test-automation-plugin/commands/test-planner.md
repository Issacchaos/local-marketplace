---
description: "Generates a structured test plan from design documentation. Produces risk-driven scope, edge cases, test approach splits, cadence, and entry/exit criteria."
argument-hint: "<path-to-design-doc-or-folder> [--code-path <path>]"
allowed-tools: Read, Bash, Write, Grep, Glob, WebFetch, WebSearch, AskUserQuestion, Skill(test-engineering:project-detection)
---

# /test-planner Command

**Description**: Generates a structured, risk-driven test plan from design documentation

**Usage**:
```
/test-planner <path-to-design-doc-or-folder> [--code-path <path>]
```

**Arguments**:
- `path` (required): Path to a design document or folder of documents.
- `--code-path <path>` (optional): Path to existing source code. Enriches risk analysis for refactors and enhancements by cross-referencing the current implementation.

**Examples**:
```bash
# Generate test plan from a markdown design doc
/test-planner docs/feature-design.md

# Generate test plan from a PDF spec
/test-planner specs/matchmaking-v2.pdf

# Generate test plan from a folder of design documents
/test-planner docs/season-34/

# Generate test plan with code cross-reference for a refactor
/test-planner docs/matchmaking-redesign.md --code-path src/matchmaking/
```

---

## Command Behavior

This command reads design documentation, asks contextual questions, then generates a complete test plan as `{feature-name}-test-plan.md` alongside the source document. See `skills/test-planner/SKILL.md` for the full orchestration flow, output template, and analysis guidelines.

**Output sections**: Overview, Scope, Risks & Constraints, Edge Cases, Test Approach, Cadence, Entry/Exit Criteria.

---

## Implementation Prompt

When this command is executed:

1. **Parse and Validate Arguments (SECURITY CRITICAL)**:
   - Extract the document path and optional `--code-path` from `$ARGUMENTS`
   - **SECURITY**: Validate all paths using these checks:
     - Remove null bytes (prevent injection)
     - Check path length (max 4096 characters)
     - Resolve to absolute path
     - Verify path is within workspace boundaries (prevent directory traversal)
     - Check path exists
   - If validation fails, display error and STOP

2. **Execute Skill**: Read and follow the instructions in `skills/test-planner/SKILL.md`. Pass the validated document path as `$ARGUMENTS` and the `--code-path` value if provided.

---

## Related Commands

- `/test-analyze` — Analyze code to identify testing needs and prioritize test targets. Run after `/test-planner` to map the plan against actual code.
- `/test-generate` — Auto-generate test code. Use after planning and analysis to produce tests that cover the plan's scope.
- `/test-loop` — Interactive test generation with approval gates. Alternative to `/test-generate` for hands-on control.
