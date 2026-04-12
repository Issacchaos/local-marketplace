---
description: "Analyze code to identify testing needs, detect frameworks, and prioritize test targets"
argument-hint: "[optional: path to analyze]"
allowed-tools: Skill(test-engineering:framework-detection), Skill(test-engineering:project-detection), Skill(test-engineering:model-selection), Skill(test-engineering:llt-find), Skill(test-engineering:llt-find-sources), Skill(test-engineering:llt-find-for-changes), Skill(test-engineering:llt-coverage)
---

# /test-analyze Command

**Description**: Analyze code to identify testing needs, detect frameworks, and prioritize test targets

**Usage**:
```
/test-analyze [path]
```

**Arguments**:
- `path` (optional): Directory or file to analyze. Defaults to workspace root if not specified.

**Examples**:
```bash
# Analyze entire workspace
/test-analyze

# Analyze specific directory
/test-analyze src/

# Analyze specific file
/test-analyze src/calculator.py
```

---

## Command Behavior

When invoked, this command will:

1. **Validate Target Path**
   - If path provided, verify it exists
   - If no path provided, use workspace root
   - Display error if path doesn't exist

2. **Launch Analyze Agent**
   - Invoke the `analyze-agent` via Task tool with `subagent_type=general-purpose`
   - Pass the target path to the agent
   - Display progress message to user

3. **Display Analysis Results**
   - Show summary: language, framework, total testable units
   - Display test targets organized by priority (Critical, High, Medium, Low)
   - Show complexity analysis and coverage gaps
   - Present actionable recommendations

4. **Save Analysis Report**
   - Save complete analysis to `.claude/.last-analysis.md` for reference
   - This allows subsequent commands (like `/test-generate`) to reuse the analysis
   - Display path to saved report

5. **Provide Next Steps**
   - Suggest appropriate follow-up commands
   - Guide user on how to proceed based on analysis results

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/test-analyze` command to analyze code and identify testing needs.

## Your Task

1. **Parse and Validate Arguments (SECURITY CRITICAL)**:
   - Extract the `path` argument from the user's command
   - If no path provided, use the workspace root directory
   - **SECURITY**: Validate the path using these checks:
     - Remove null bytes (prevent injection)
     - Check path length (max 4096 characters)
     - Resolve to absolute path
     - Verify path is within workspace boundaries (prevent directory traversal)
     - Check path exists
   - If validation fails, display error and STOP
   - See `SECURITY.md` for complete validation requirements

2. **Launch Analyze Agent**:
   - Use the Task tool to launch an agent with `subagent_type=general-purpose`
   - Provide this prompt to the agent:

```
You are the Analyze Agent. Analyze the codebase at the specified path to identify testing needs.

**Target Path**: {path}

**Your Mission**:
Read and apply the agent definition from `agents/analyze-agent.md` in this workspace. Follow all instructions in that file to:
- Discover source files
- Detect language and testing framework
- Analyze code structure and complexity
- Assess existing test coverage
- Prioritize test targets
- Generate recommendations

**Output Format**: Follow the exact output format specified in `agents/analyze-agent.md`, including all required sections for extractors.

**Skills Available**: Reference `skills/framework-detection/` for framework detection patterns.

Begin your analysis now.
```

3. **Process Agent Results**:
   - When the agent completes, extract key information using the agent's extractors:
     - `language`: Programming language detected
     - `framework`: Testing framework detected
     - `test_targets`: List of prioritized test targets
     - `priority_summary`: Count by priority level
     - `coverage_gaps`: Files/areas with missing coverage
     - `recommendations`: Actionable recommendations

4. **Display Results to User**:
   Present a clear, formatted summary:

```markdown
## Analysis Complete ✅

**Project**: {project_name}
**Language**: {language}
**Framework**: {framework}
**Testable Units**: {total_count}

### Priority Summary
- Critical: {critical_count} targets
- High: {high_count} targets
- Medium: {medium_count} targets
- Low: {low_count} targets

### Coverage Gaps
{coverage_gaps_summary}

### Top Recommendations
{top_3_recommendations}

**Full Report**: Saved to `.claude/.last-analysis.md`

### Next Steps
- Review the full analysis report for details
- Run `/test-generate` to auto-generate tests for all targets
- Run `/test-loop` for interactive test generation with approval gates
- Focus on Critical priority targets first
```

5. **Save Analysis Report**:
   - Create `.claude/` directory if it doesn't exist
   - Save the complete agent output to `.claude/.last-analysis.md`
   - Include timestamp in the saved report
   - Use the Write tool to create the file

6. **Handle Errors**:
   - **Path doesn't exist**: Display clear error message with suggestions
   - **No source files found**: Inform user, suggest checking path or file extensions
   - **Framework not detected**: Show warning, recommend manual framework configuration
   - **Agent fails**: Display error, suggest checking logs or trying again

---

## Example Execution Flow

### User Input
```
/test-analyze src/
```

### Your Actions
1. Parse `path = "src/"`
2. Validate path exists
3. Launch analyze-agent via Task tool
4. Wait for agent completion
5. Extract results using extractors
6. Display formatted summary
7. Save full report to `.claude/.last-analysis.md`
8. Suggest next steps

### Expected Output to User
```markdown
## Analysis Complete ✅

**Project**: my-app
**Language**: python
**Framework**: pytest (Confidence: 0.85)
**Testable Units**: 15

### Priority Summary
- Critical: 3 targets
- High: 5 targets
- Medium: 4 targets
- Low: 3 targets

### Coverage Gaps
- src/user_service.py: 5 functions, 0 tests (0% coverage)
- src/calculator.py: 4 functions, 1 test (25% coverage)

### Top Recommendations
1. Start with Critical Priority: Focus on src/user_service.py
2. Set up pytest configuration: Create pytest.ini
3. Target 80% coverage for Critical and High priority functions

**Full Report**: Saved to `.claude/.last-analysis.md`

### Next Steps
- Run `/test-generate` to auto-generate tests for all uncovered functions
- Run `/test-loop` for interactive test generation with approval gates
- Focus on Critical priority targets: user_service.create_user, user_service.authenticate_user
```

---

## Help Text

When user runs `/test-analyze --help` or `/test-analyze -h`, display:

```
/test-analyze - Analyze code to identify testing needs

USAGE:
  /test-analyze [path]

ARGUMENTS:
  path    Optional. Directory or file to analyze. Defaults to workspace root.

EXAMPLES:
  /test-analyze                  # Analyze entire workspace
  /test-analyze src/             # Analyze src directory
  /test-analyze src/app.py       # Analyze specific file

DESCRIPTION:
  Scans your codebase to identify testable code units, detect testing frameworks,
  assess complexity, and prioritize test targets. Generates a comprehensive
  analysis report with actionable recommendations.

OUTPUT:
  - Language and framework detection
  - Test targets organized by priority (Critical, High, Medium, Low)
  - Complexity scores for each target
  - Existing test coverage assessment
  - Coverage gaps identification
  - Actionable recommendations

  Full analysis saved to: .claude/.last-analysis.md

NEXT STEPS:
  - Use /test-generate to auto-generate tests
  - Use /test-loop for interactive test generation
  - Review .claude/.last-analysis.md for detailed analysis

SEE ALSO:
  /test-generate    Generate tests automatically
  /test-loop        Interactive test generation workflow
```

---

## Notes for Implementation

1. **Use Task Tool Correctly**:
   - Set `subagent_type=general-purpose` (not a specialized agent type)
   - Pass the agent instructions in the prompt
   - Reference the agent file path so it can be read and applied

2. **Path Validation**:
   - Use Glob or Bash (`ls`) to verify path exists
   - Handle both absolute and relative paths
   - Convert relative paths to absolute for consistency

3. **Error Handling**:
   - Gracefully handle missing paths
   - Provide helpful error messages
   - Suggest corrections when appropriate

4. **State Management**:
   - The saved analysis (`.claude/.last-analysis.md`) is critical for subsequent commands
   - Always save the full, unmodified agent output
   - Include timestamp and path analyzed

5. **User Experience**:
   - Show progress messages ("Analyzing codebase...")
   - Display results in a scannable format (use hierarchy, bullets, emphasis)
   - Keep summary concise, save details for the full report
   - Always suggest clear next steps

---

Now execute this command with the user's arguments.
