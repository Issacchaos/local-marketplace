---
name: file-safety
description: Template mixin that adds read-before-write, backup, and rollback safety patterns to agents that modify files.
type: template
version: "1.0.0"
---

# File Safety Agent Template

This template provides defensive file modification patterns for agents that create or edit files. Agents extending this template follow read-before-write discipline, maintain awareness of file ownership, and provide rollback guidance.

---

## File Modification Safety Rules

### Rule 1: Read Before Write

**ALWAYS read a file before modifying it.** Never write to a file blindly.

```
1. Use the Read tool to read the current file contents
2. Understand the existing structure and patterns
3. Plan your modifications
4. Use the Edit tool for targeted changes (preferred) or Write tool for full rewrites
```

This prevents:
- Overwriting another agent's recent changes
- Breaking existing functionality you weren't aware of
- Introducing formatting inconsistencies

### Rule 2: Prefer Edit Over Write

Use the **Edit** tool for targeted changes instead of the **Write** tool for full file rewrites:
- Edit only changes what needs to change, preserving everything else
- Write replaces the entire file, risking loss of other agents' work
- Only use Write for new files that don't exist yet

### Rule 3: Additive Changes

When modifying shared files (like `server.js` or `App.jsx`):
- **Add** new code sections rather than replacing existing ones
- **Append** to arrays, objects, and switch statements
- **Preserve** existing imports, exports, and module structure
- **Do not remove** code added by other agents unless explicitly instructed

### Rule 4: Verify After Write

After modifying a file, verify your changes:

```bash
# Check for syntax errors (JavaScript/TypeScript)
node -c <filename>

# Check that the server still starts (if applicable)
node server.js &
sleep 2
curl -s http://localhost:3000/api/items > /dev/null && echo "Server OK" || echo "Server BROKEN"
kill %1 2>/dev/null
```

### Rule 5: Document File Ownership

In your output, always list:
- **Files read**: Which files you examined
- **Files created**: New files you created
- **Files modified**: Existing files you changed and what you changed

This helps the coordinator track file ownership and detect conflicts.

### Rollback Guidance

If your changes break something:
1. Re-read the file to see current state
2. Identify what went wrong
3. Use Edit to revert specific changes
4. Re-run verification
5. Report the issue to the coordinator

### Important Notes

- Never delete files created by other agents
- If you need to modify a file another agent owns, check that agent completed first
- For shared configuration files, append to existing config rather than replacing
- Always use the dedicated Read/Edit/Write tools, never shell commands like cat/sed/echo
