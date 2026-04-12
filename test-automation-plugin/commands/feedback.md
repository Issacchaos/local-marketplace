---
description: "Submit feedback, bug reports, and feature requests to the dante_plugin repository"
argument-hint: "[optional: feedback message]"
---

# /feedback Command

**Description**: Submit feedback, bug reports, and feature requests directly to the dante_plugin GitHub repository with automatic diagnostic information collection.

**Usage**:
```
/feedback [options]
```

**Options**:
- `--quick <description>` (optional): Quick bug report with abbreviated preview
- `--retry` (optional): Retry all queued feedback submissions
- `--list-queue` (optional): Show all queued feedback items
- `--help, -h`: Display help information

**Examples**:
```bash
# Interactive feedback submission (full workflow)
/feedback

# Quick bug report with brief description
/feedback --quick "Test execution timeout after 5 minutes"

# Retry queued feedback submissions
/feedback --retry

# List all queued feedback items
/feedback --list-queue
```

---

## Command Behavior

This command enables users to submit feedback directly to the dante_plugin GitHub repository from within Claude Code. It automatically collects diagnostic information (command history, plugin version, environment details, error logs) to help maintainers triage issues efficiently.

**Workflow Modes**:

1. **Interactive Mode** (default): Full 6-phase workflow with review gate
   - Phase 1: Feedback Type Selection
   - Phase 2: Title & Description Collection
   - Phase 3: Diagnostic Collection
   - Phase 4: Sanitization & Preview
   - Phase 5: User Approval
   - Phase 6: Submission or Queueing

2. **Quick Mode** (`--quick`): Streamlined bug report workflow
   - Auto-defaults to "Bug Report" type
   - Uses provided description as title/description
   - Shows abbreviated preview (first 5 lines per category)
   - Single approval gate
   - Target completion: < 15 seconds

3. **Retry Mode** (`--retry`): Manual retry of queued submissions
   - Retries all queued feedback items (ignores abandoned flag)
   - Displays results summary

4. **List Queue Mode** (`--list-queue`): View queued feedback
   - Displays all queued items with metadata
   - Shows queue statistics

**Key Features**:
- Automatic diagnostic collection (command history, versions, errors, project context)
- PII sanitization (removes usernames, credentials, IP addresses)
- User review gate before submission (privacy-first)
- GitHub CLI integration with clipboard fallback
- Offline queueing with automatic retry
- Privacy controls (edit/remove diagnostics before submission)

---

## Implementation Prompt

When this command is executed, use the following prompt:

---

You are executing the `/feedback` command to submit feedback to the dante_plugin GitHub repository.

## Your Task

Execute the feedback submission workflow based on the mode selected by the user (interactive, quick, retry, or list-queue).

### Step 1: Parse Arguments and Route to Mode (SECURITY CRITICAL)

**Parse Arguments**:
```javascript
// Extract arguments from user command
const args = parseCommandArgs(userInput);
const mode = determineMode(args); // "interactive", "quick", "retry", or "list-queue"
```

**Determine Mode**:
- If no arguments: mode = "interactive"
- If `--quick <description>`: mode = "quick", extract description
- If `--retry`: mode = "retry"
- If `--list-queue`: mode = "list-queue"
- If `--help` or `-h`: display help text and STOP
- If unknown argument: display error and STOP

**Validate Arguments (SECURITY REQUIREMENTS)**:
- **Quick Mode Description Validation**:
  - Remove null bytes
  - Check length (10-500 characters for quick description)
  - Reject if contains only whitespace
  - Sanitize control characters
- **Command Whitelisting**: Only accept `--quick`, `--retry`, `--list-queue`, `--help`, `-h`
- Display validation errors if needed and STOP

**Route to Mode**:
Based on mode, execute the appropriate workflow:
- Interactive → Step 2 (Interactive Workflow)
- Quick → Step 3 (Quick Mode Workflow)
- Retry → Step 4 (Retry Queue Workflow)
- List Queue → Step 5 (List Queue Workflow)

---

### Step 2: Interactive Mode Workflow

**Display Start Message**:
```markdown
## Feedback Submission

Submitting feedback to: github.example.com/my-org/my-plugin

This workflow will:
1. Collect feedback type, title, and description
2. Gather diagnostic information (command history, versions, errors)
3. Sanitize all data (remove PII, credentials, IP addresses)
4. Show you a preview for review and editing
5. Submit to GitHub or queue for later if offline

All diagnostic data will be shown for your review before submission.

---
```

#### Phase 1: Feedback Type Selection

**Use AskUserQuestion**:
```markdown
What type of feedback are you submitting?

Options:
1. Bug Report - Issues, errors, unexpected behavior
2. Feature Request - Suggestions for new capabilities
3. Question/Help - Usage questions or clarifications
4. General Feedback - Performance, UX, other comments
```

**Capture Selection**:
- Store feedback_type: "bug", "feature-request", "question", or "feedback"

**Map to GitHub Labels** (per TASK-009):

Execute hardcoded label mapping per plan TD-8:

**Step 1: Identify Feedback Type from User Selection**
- Extract the selected option from AskUserQuestion response
- Normalize to internal type identifier:
  - "Bug Report" → feedback_type = "bug"
  - "Feature Request" → feedback_type = "feature-request"
  - "Question/Help" → feedback_type = "question"
  - "General Feedback" → feedback_type = "feedback"

**Step 2: Apply Hardcoded Mapping**
Perform lookup with exact match:
```python
if feedback_type == "bug":
    labels = ["bug", "needs-triage"]
elif feedback_type == "feature-request":
    labels = ["enhancement", "needs-review"]
elif feedback_type == "question":
    labels = ["question"]
elif feedback_type == "feedback":
    labels = ["feedback"]
else:
    # Fallback (should never happen with valid input)
    labels = ["feedback"]
```

**Step 3: Format for gh CLI**
Convert label list to comma-separated string:
- Input: `["bug", "needs-triage"]`
- Output: `"bug,needs-triage"`
- Method: `",".join(labels)`

**Step 4: Store Formatted Labels**
- Store labels_string for use in Phase 6 (GitHub submission)
- Format: comma-separated, no spaces (gh CLI requirement)
- Example outputs:
  - Bug Report: `"bug,needs-triage"`
  - Feature Request: `"enhancement,needs-review"`
  - Question/Help: `"question"`
  - General Feedback: `"feedback"`

#### Phase 2: Title & Description Collection

**Collect Title**:
Use AskUserQuestion:
```markdown
Enter a brief title for your feedback (10-100 characters):
```

**Validate Title**:
- Length: 10-100 characters
- Remove null bytes
- Remove leading/trailing whitespace
- Reject if only whitespace
- If invalid, display error and re-prompt (max 3 attempts)

**Collect Description**:
Use AskUserQuestion:
```markdown
Enter a detailed description (20-5000 characters):

For bug reports, include:
- What you expected to happen
- What actually happened
- Steps to reproduce (if applicable)

For feature requests, include:
- Problem you're trying to solve
- Proposed solution or feature
```

**Validate Description**:
- Length: 20-5000 characters
- Remove null bytes
- Remove leading/trailing whitespace
- Reject if only whitespace
- If invalid, display error and re-prompt (max 3 attempts)

#### Phase 3: Diagnostic Collection

**Display Progress**:
```markdown
Collecting diagnostic information...
```

**Collect Diagnostics** (4 collectors run sequentially):

1. **Command History Collector** (per plan TD-3):

   **Algorithm**: Reconstruct command history from `.claude/` state files using file naming patterns and modification timestamps.

   **Step 1: Scan `.claude/` Directory**
   - Check if `.claude/` directory exists (use file system tools)
   - If directory doesn't exist: return `{"category": "Command History", "items": ["No command history available"], "metadata": {"count": 0}}`
   - If directory exists, list all files in `.claude/` directory

   **Step 2: Extract Command Data from Known State Files**

   For each file, apply the following filename → command mapping:

   | File Pattern | Command | Argument Extraction |
   |-------------|---------|-------------------|
   | `.last-analysis.md` | `/test-analyze` | Extract `target_path` from YAML frontmatter if present, otherwise use "." |
   | `.last-test-plan.md` | `/test-generate` | Extract `target_path` from file content or use "." |
   | `.last-execution.md` | `test execution` | No arguments (internal phase) |
   | `.last-validation.md` | `test validation` | No arguments (internal phase) |
   | `.test-loop-state.md` | `/test-loop` | Extract `target_path` from YAML frontmatter (required field) |
   | `.feedback-queue/*.json` | `/feedback` | Extract from queue entry metadata if accessible |

   **Step 3: Extract Metadata from Each File**

   For each matched file:
   a. Get file modification timestamp (mtime) using file system stat
   b. Try to parse YAML frontmatter (lines between `---` delimiters at file start):
      - Extract `created_at` timestamp if present (more accurate than mtime)
      - Extract `target_path` argument if present
      - Extract `updated_at` as fallback if `created_at` missing
   c. If YAML parsing fails or no frontmatter, use mtime as timestamp
   d. Create command entry: `{timestamp, command, args, source_file}`

   **Step 4: Sort and Limit**
   - Sort all command entries by timestamp descending (newest first)
   - Limit to first 20 entries
   - Format each entry as: `YYYY-MM-DD HH:MM:SS - {command} {args}`

   **Step 5: Return Structured Data**
   ```json
   {
     "category": "Command History (Last 20 commands)",
     "items": [
       "2025-12-08 16:25:00 - /test-loop D:\\dev\\dante_plugin",
       "2025-12-08 16:17:00 - /test-generate .",
       "2025-12-08 16:24:00 - test execution",
       ...
     ],
     "metadata": {
       "count": 4,
       "oldest": "2025-12-08 16:17:00",
       "newest": "2025-12-08 16:25:00"
     }
   }
   ```

   **Error Handling**:
   - YAML parsing errors: Log warning, use mtime and infer command from filename only
   - Missing `target_path`: Use "." as default argument
   - Malformed timestamps: Use mtime as fallback
   - File access errors: Skip file, continue with others
   - Empty result: Return "No command history available"

   **Security**:
   - All file paths MUST be validated within workspace boundaries
   - Use os.path.abspath() and os.path.commonpath() to verify `.claude/` is within workspace
   - Prevent path traversal attacks
   - Arguments extracted from files will be sanitized in Phase 4 (Sanitization Pipeline)

   **Example YAML Frontmatter Parsing**:
   ```python
   # Pseudo-code for frontmatter extraction
   def extract_frontmatter(file_path):
       with open(file_path, 'r') as f:
           content = f.read()

       # Check for YAML frontmatter (starts and ends with ---)
       if content.startswith('---\n'):
           end_index = content.find('\n---\n', 4)
           if end_index > 0:
               yaml_content = content[4:end_index]
               # Parse YAML (use simple key:value parsing or yaml library)
               frontmatter = parse_yaml(yaml_content)
               return frontmatter
       return None
   ```

   **Trade-off Acknowledgment**: This reconstruction is "best effort" and limited to commands that produce `.claude/` artifacts. Commands without state files won't be captured. This is acceptable for v1.0 per plan TD-3.

2. **Environment Collector**:

   **Algorithm**: Gather plugin version, OS platform, and detected language versions.

   **Step 1: Read Plugin Version**
   - Read `.claude-plugin/plugin.json` file from workspace
   - Parse JSON and extract "version" field
   - If file doesn't exist or parsing fails: use "Unknown" as fallback
   - Expected format: semantic version (e.g., "0.1.0")

   **Step 2: Detect OS Platform**
   - Use system environment detection:
     - Check `sys.platform` or `os.name` equivalent
     - Map to human-readable names:
       - "win32" → "Windows"
       - "darwin" → "macOS"
       - "linux" → "Linux"
       - Other → platform string as-is
   - Include OS version if easily available (e.g., "Windows 10", "macOS 13.2")

   **Step 3: Detect Language Versions** (with graceful fallback)

   For each language (Python, Node.js, Java), attempt version detection:

   a. **Python Version Detection**:
      - Subprocess: `["python", "--version"]` (2-second timeout, shell=False)
      - Alternative: `["python3", "--version"]` if first fails
      - Parse stdout/stderr for version string (format: "Python X.Y.Z")
      - Extract version number (e.g., "3.11.2")
      - If fails or times out: omit Python from results (no error)

   b. **Node.js Version Detection**:
      - Subprocess: `["node", "--version"]` (2-second timeout, shell=False)
      - Parse stdout for version string (format: "vX.Y.Z")
      - Extract version number, strip leading 'v' (e.g., "18.16.0")
      - If fails or times out: omit Node.js from results (no error)

   c. **Java Version Detection**:
      - Subprocess: `["java", "--version"]` (2-second timeout, shell=False)
      - Alternative: `["java", "-version"]` if first fails (older Java versions)
      - Parse stdout/stderr for version string (multiple formats possible)
      - Extract version number (e.g., "11.0.12", "17.0.2", "1.8.0_292")
      - If fails or times out: omit Java from results (no error)

   **Step 4: Return Structured Data**
   ```json
   {
     "category": "Environment",
     "items": [
       "Plugin Version: 0.1.0",
       "OS: Windows 10",
       "Python: 3.11.2",
       "Node.js: 18.16.0",
       "Java: 11.0.12"
     ],
     "metadata": {
       "plugin_version": "0.1.0",
       "os": "Windows 10",
       "language_versions": {
         "python": "3.11.2",
         "node": "18.16.0",
         "java": "11.0.12"
       }
     }
   }
   ```

   **Security Requirements** (per SECURITY.md):
   - **Subprocess Security**:
     - Use array form: `["python", "--version"]` (NOT string)
     - Set shell=False (prevent command injection)
     - Set 2-second timeout per language (total max 6 seconds for all 3 languages)
     - Capture stdout/stderr with size limits (prevent memory exhaustion)
   - **No User Input in Commands**: All commands are hardcoded (no user-controlled paths)
   - **Path Validation**: Plugin.json path validated within workspace boundaries

   **Error Handling**:
   - Plugin.json read errors: Log warning, use "Unknown" version
   - JSON parsing errors: Log warning, use "Unknown" version
   - Language subprocess timeout: Silently omit language (no error to user)
   - Language subprocess error (not found): Silently omit language (expected behavior)
   - OS detection error: Use "Unknown" as fallback
   - Empty language_versions: Return environment with no language data

   **Performance Target**: Complete in < 3 seconds (per REQ-NF-1 breakdown)
   - Plugin.json read: < 0.1s
   - OS detection: < 0.1s
   - Language detection: < 2.5s (3 languages × ~0.8s each with timeouts)
   - Total: ~2.7s nominal, 6.5s worst case (all timeouts)

   **Example Output (Minimal)**:
   ```json
   {
     "category": "Environment",
     "items": [
       "Plugin Version: 0.1.0",
       "OS: Linux"
     ],
     "metadata": {
       "plugin_version": "0.1.0",
       "os": "Linux",
       "language_versions": {}
     }
   }
   ```

   **Example Output (Full)**:
   ```json
   {
     "category": "Environment",
     "items": [
       "Plugin Version: 0.1.0",
       "OS: Windows 10",
       "Python: 3.11.2",
       "Node.js: 18.16.0",
       "Java: 17.0.2"
     ],
     "metadata": {
       "plugin_version": "0.1.0",
       "os": "Windows 10",
       "language_versions": {
         "python": "3.11.2",
         "node": "18.16.0",
         "java": "17.0.2"
       }
     }
   }
   ```

   **Trade-offs**:
   - Sequential language detection (not parallel) for simplicity and predictability
   - Fixed timeout (2s) may miss slow systems, but prevents workflow delays
   - Only detects default system interpreters (not virtualenv/nvm/sdkman managed versions)

3. **Error Log Collector** (per TASK-004):

   **Algorithm**: Extract recent errors from `.claude/` state files and error logs (last 10 errors or 24 hours).

   **Step 1: Scan `.claude/` Directory for Error Files**
   - Check if `.claude/` directory exists (use file system tools)
   - If directory doesn't exist: return `{"category": "Recent Errors", "items": ["No recent errors"], "metadata": {"count": 0}}`
   - If directory exists, look for these specific error-containing files:
     - `.last-execution.md` - Test execution errors and failures
     - `.last-validation.md` - Validation errors and issues
     - `.feedback-errors.log` - Feedback command errors (if exists)
   - For each file that exists, proceed to error extraction

   **Step 2: Extract Errors from Each File**

   **From `.last-execution.md`**:
   - Read file contents
   - Look for error indicators in these sections:
     - **Exit Code**: If exit code ≠ 0, extract failure information
     - **Failure Details** section: Contains test failure details
     - **Test Results**: Look for "Failed: N" where N > 0
     - **Status**: If not "All tests passed", extract error message
   - Extract patterns:
     - Lines starting with "Error:", "Exception:", "FAILED", "ERROR", "Traceback"
     - Lines in "Failure Details" or "## Failure Details" sections
     - Lines containing stack traces or exception messages
   - For each error found:
     - **Timestamp**: Use file modification time (mtime) or "Generated" field from YAML frontmatter
     - **Error Message**: Extract the error line(s)
     - **File Location**: `.claude/.last-execution.md` plus line number if available
     - **Context**: Try to extract test name or function that failed

   **From `.last-validation.md`**:
   - Read file contents
   - Look for error indicators:
     - **Validation Status**: If status = "FAIL" or contains "issues detected"
     - **Failure Categories** section: Extract test bugs, source bugs, environment issues
     - **Root Cause Analysis** section: Extract root cause descriptions
   - Extract patterns:
     - Lines in "Test Bugs", "Source Bugs", "Environment Issues" sections
     - Lines starting with "Error:", "Issue:", "Problem:"
     - Lines containing "failed", "error", "exception" (case-insensitive)
   - For each error found:
     - **Timestamp**: Use file mtime or "Generated" field
     - **Error Message**: Extract the error description
     - **File Location**: `.claude/.last-validation.md` plus section name
     - **Context**: Extract bug category (test bug, source bug, environment)

   **From `.feedback-errors.log`**:
   - If file exists, read contents (plain text log format)
   - Expected format (one error per line or multi-line):
     ```
     [2026-01-16 15:30:00] Error: GitHub CLI submission failed: network timeout
     [2026-01-16 15:25:00] Error: Failed to parse YAML frontmatter in .last-analysis.md
     ```
   - Extract patterns:
     - Lines starting with timestamp in brackets: `[YYYY-MM-DD HH:MM:SS]`
     - Followed by error level: "Error:", "Warning:", "Exception:"
     - Followed by error message
   - For each log entry:
     - **Timestamp**: Parse from log line `[YYYY-MM-DD HH:MM:SS]` format
     - **Error Message**: Text after error level indicator
     - **File Location**: `.claude/.feedback-errors.log:line_number`

   **Step 3: Parse and Structure Error Data**

   For each error extracted, create structured entry:
   ```javascript
   {
     timestamp: "2026-01-16 15:30:00",  // ISO or human-readable format
     error: "TimeoutError: Test execution exceeded 300 seconds",  // Truncated to 500 chars
     file: ".claude/.last-execution.md:42",  // File path + line number
     context: "test_calculator.py::test_division_by_zero"  // Optional: test name or category
   }
   ```

   **Step 4: Filter by Time Window**

   - Calculate time window: Current time - 24 hours
   - Filter errors where timestamp > time_window
   - If no timestamp available (parsing failed), assume error is recent (within 24h)
   - Sort errors by timestamp descending (newest first)

   **Step 5: Apply Limits**

   - Limit to MINIMUM of:
     - 10 errors (max count)
     - All errors within last 24 hours
   - Result: If 15 errors in last 24h → return 10 (limit by count)
   - Result: If 5 errors in last 24h → return 5 (within limit)
   - Result: If 20 errors in last 48h → return 10 from last 24h (limit by time then count)

   **Step 6: Truncate Long Error Messages**

   For each error message:
   - If length > 500 characters:
     - Truncate to 497 characters
     - Append "..." to indicate truncation
     - Result: "TimeoutError: Test execution exceeded 300 seconds. Details: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium..."
   - Preserve multi-line errors but count total characters across all lines
   - Keep important parts: error type, first line of message, last line if it contains file/line info

   **Step 7: Return Structured Data**

   ```json
   {
     "category": "Recent Errors (Last 10 or 24 hours)",
     "items": [
       "2026-01-16 15:30:00 - TimeoutError: Test execution exceeded 300 seconds\n  File: .claude/.last-execution.md:42\n  Context: test_calculator.py::test_division_by_zero",
       "2026-01-16 14:52:11 - ValidationError: Test failed due to source bug\n  File: .claude/.last-validation.md:source_bugs\n  Context: Division by zero not handled",
       "2026-01-16 14:25:00 - NetworkError: GitHub CLI submission timeout\n  File: .claude/.feedback-errors.log:15"
     ],
     "metadata": {
       "count": 3,
       "time_window": "24 hours",
       "oldest": "2026-01-16 14:25:00",
       "newest": "2026-01-16 15:30:00",
       "truncated_count": 0
     }
   }
   ```

   **If No Errors Found**:
   ```json
   {
     "category": "Recent Errors",
     "items": ["No recent errors"],
     "metadata": {"count": 0}
   }
   ```

   **Error Handling**:
   - **File not found**: Skip file, continue with other error sources
   - **File read errors**: Log warning, skip file
   - **Timestamp parsing errors**: Use file mtime as fallback, or assume recent (within 24h)
   - **Malformed error format**: Extract what's possible, include as "Unparsed error: [text]"
   - **Empty files**: Skip, no errors to extract
   - **Permission errors**: Log warning, skip file

   **Security**:
   - All file paths MUST be validated within workspace boundaries
   - Use os.path.abspath() and os.path.commonpath() to verify `.claude/` is within workspace
   - Prevent path traversal attacks
   - Error messages will be sanitized in Phase 4 (Sanitization Pipeline) to remove PII

   **Example Error Extraction Patterns** (Regex or string matching):

   For `.last-execution.md`:
   ```python
   # Pseudo-code patterns
   error_patterns = [
       r'Exit Code:\s*([1-9]\d*)',  # Non-zero exit code
       r'Failed:\s*(\d+)',  # Failed test count > 0
       r'Status:\s*(.*(fail|error|exception).*)',  # Status line with error
       r'^(Error|Exception|FAILED|ERROR|Traceback):.*$',  # Error line starters
   ]
   ```

   For `.last-validation.md`:
   ```python
   validation_patterns = [
       r'Status:\s*(FAIL|ERROR)',  # Failure status
       r'Failures:\s*([1-9]\d*)',  # Non-zero failures
       r'Test Bugs.*:\s*([1-9]\d*)',  # Test bugs count > 0
       r'Source Bugs.*:\s*([1-9]\d*)',  # Source bugs count > 0
   ]
   ```

   For `.feedback-errors.log`:
   ```python
   log_pattern = r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*(Error|Warning|Exception):\s*(.+)'
   ```

   **Trade-off Acknowledgment**: This collector is "best effort" - it extracts errors from known file formats. Custom error formats or new error files won't be captured until this algorithm is updated. This is acceptable for v1.0 per plan.

4. **Project Context Collector**:

   **Algorithm**: Gather anonymized project information (language, framework, test counts) without including file paths or source code.

   **Step 1: Detect Primary Language**

   Scan workspace for files by extension and count occurrences:

   a. **Python Detection**:
      - Look for files: `*.py` (excluding `__pycache__`, `venv`, `.venv`, `node_modules`, `.git`, `.claude*`, `build`, `dist`)
      - Count Python files found
      - If count > 0: language candidate = "Python"

   b. **JavaScript Detection**:
      - Look for files: `*.js`, `*.jsx` (excluding `node_modules`, `.git`, `.claude*`, `build`, `dist`)
      - Count JavaScript files found
      - If count > 0: language candidate = "JavaScript"

   c. **TypeScript Detection**:
      - Look for files: `*.ts`, `*.tsx` (excluding `node_modules`, `.git`, `.claude*`, `build`, `dist`)
      - Count TypeScript files found
      - If count > 0: language candidate = "TypeScript"

   d. **Java Detection**:
      - Look for files: `*.java` (excluding `target`, `build`, `.git`, `.claude*`)
      - Count Java files found
      - If count > 0: language candidate = "Java"

   e. **Select Primary Language**:
      - Choose language with highest file count
      - If multiple languages tied, prefer: Python > JavaScript > TypeScript > Java
      - If no files found: language = "Unknown"

   **Step 2: Infer Framework from Config Files**

   Based on detected language, check for framework-specific configuration files:

   a. **Python Framework Detection**:
      - **pytest**: Check for `pytest.ini` OR `pyproject.toml` with `[tool.pytest]` section
      - **unittest**: Check for pattern `test_*.py` files (fallback if no pytest config)
      - If pytest config found: framework = "pytest"
      - If no pytest but test files: framework = "unittest"
      - If neither: framework = "Unknown"

   b. **JavaScript/TypeScript Framework Detection**:
      - **Jest**: Check for `jest.config.js`, `jest.config.ts` OR `package.json` with `"jest"` field
      - **Mocha**: Check for `.mocharc.json`, `.mocharc.js` OR `package.json` with `"mocha"` field
      - **Vitest**: Check for `vitest.config.js`, `vitest.config.ts` OR `package.json` with `"vitest"` field
      - Priority: Jest > Mocha > Vitest (if multiple found)
      - If no config found: framework = "Unknown"

   c. **Java Framework Detection**:
      - **JUnit**: Check for `pom.xml` with `<artifactId>junit` OR `build.gradle` with `junit`
      - **TestNG**: Check for `testng.xml` OR `pom.xml` with `<artifactId>testng`
      - Priority: JUnit > TestNG (if multiple found)
      - If no config found: framework = "Unknown"

   **Step 3: Count Test Files**

   Based on detected language, count files matching test patterns:

   a. **Python Test Files**:
      - Patterns: `test_*.py`, `*_test.py`
      - Scan workspace (excluding `venv`, `.venv`, `__pycache__`, `node_modules`, `.git`, `.claude*`)
      - Count matching files

   b. **JavaScript/TypeScript Test Files**:
      - Patterns: `*.test.js`, `*.test.ts`, `*.test.jsx`, `*.test.tsx`, `*.spec.js`, `*.spec.ts`
      - Scan workspace (excluding `node_modules`, `.git`, `.claude*`, `build`, `dist`)
      - Count matching files

   c. **Java Test Files**:
      - Patterns: `*Test.java`, `*Tests.java`
      - Scan workspace (excluding `target`, `build`, `.git`, `.claude*`)
      - Count matching files

   d. **Return Count**: Total number of test files found

   **Step 4: Count Test Executions (Last 7 Days)**

   Scan `.claude/` directory for test execution records within the last 7 days:

   a. **Calculate Time Window**:
      - Current timestamp minus 7 days
      - Filter files modified within this window

   b. **Scan Execution Files**:
      - Look for `.last-execution.md` file
      - Check `.test-loop-history/` directory for execution records (if exists)
      - Get modification timestamp (mtime) for each file

   c. **Extract Execution Count**:
      - For `.last-execution.md`:
        - If mtime within 7 days: count = 1 execution
        - Try to parse "Total Tests" field from file content to get test count (not execution count)
      - For `.test-loop-history/*.md`:
        - Count files with mtime within 7 days
        - Each file represents one execution iteration

   d. **Aggregate Count**:
      - Sum all execution records found
      - If `.last-execution.md` exists and recent: count += 1
      - If `.test-loop-history/` entries exist and recent: count += number of entries

   e. **Return Count**: Total test executions in last 7 days

   **Step 5: Return Structured Data**

   ```json
   {
     "category": "Project Context",
     "items": [
       "Language: Python",
       "Framework: pytest",
       "Test Files: 15",
       "Test Executions: 23 (last 7 days)"
     ],
     "metadata": {
       "language": "Python",
       "framework": "pytest",
       "test_file_count": 15,
       "test_execution_count": 23
     }
   }
   ```

   **If Minimal Data Available**:
   ```json
   {
     "category": "Project Context",
     "items": [
       "Language: Unknown",
       "Framework: Unknown",
       "Test Files: 0",
       "Test Executions: 0"
     ],
     "metadata": {
       "language": "Unknown",
       "framework": "Unknown",
       "test_file_count": 0,
       "test_execution_count": 0
     }
   }
   ```

   **Security Requirements**:
   - **No File Paths**: Do NOT include any file paths in output (only counts)
   - **No Source Code**: Do NOT include any source code content
   - **Anonymized Data**: Only aggregate statistics (counts, language/framework names)
   - **Path Validation**: All file scanning MUST stay within workspace boundaries
   - **Exclusion Patterns**: Exclude system directories (`.git`, `node_modules`, `venv`, etc.) to avoid scanning unnecessary files

   **Error Handling**:
   - **No Files Found**: Return "Unknown" for language/framework, 0 for counts
   - **File Access Errors**: Skip inaccessible files, continue with others
   - **Parse Errors**: If config file parsing fails, fall back to pattern detection
   - **Permission Errors**: Skip files, log warning, continue
   - **Empty Workspace**: Return all "Unknown" and 0 counts

   **Performance Target**: Complete in < 5 seconds (per REQ-NF-1 breakdown)
   - Language detection: < 2s (file counting with glob patterns)
   - Framework detection: < 1s (config file checks)
   - Test file counting: < 1s (glob patterns)
   - Execution counting: < 1s (scan .claude/ directory)
   - Total: ~5s nominal

   **Privacy Guarantee**: This collector returns ONLY:
   - Language name (e.g., "Python", "JavaScript")
   - Framework name (e.g., "pytest", "jest")
   - File counts (integers only)
   - Execution counts (integers only)
   - NO file paths, NO source code, NO user-specific information

   **Example Output (Full)**:
   ```json
   {
     "category": "Project Context",
     "items": [
       "Language: Python",
       "Framework: pytest",
       "Test Files: 15",
       "Test Executions: 23 (last 7 days)"
     ],
     "metadata": {
       "language": "Python",
       "framework": "pytest",
       "test_file_count": 15,
       "test_execution_count": 23
     }
   }
   ```

   **Example Output (Mixed Languages)**:
   If multiple languages detected, report primary (highest count):
   ```json
   {
     "category": "Project Context",
     "items": [
       "Language: Python (45 files)",
       "Framework: pytest",
       "Test Files: 15",
       "Test Executions: 23 (last 7 days)"
     ],
     "metadata": {
       "language": "Python",
       "framework": "pytest",
       "test_file_count": 15,
       "test_execution_count": 23
     }
   }
   ```

   **Trade-offs**:
   - Primary language detection is heuristic-based (file count), may not reflect actual project nature
   - Framework detection relies on config files, may miss custom setups
   - Test execution count is "best effort" from `.claude/` artifacts, not guaranteed complete
   - Excludes framework-less projects (e.g., manual test runners)
   - This is acceptable for v1.0 per plan (anonymized, privacy-first approach)

**Display Collection Result**:
```markdown
Diagnostic information collected:
- Command history: {count} commands
- Environment: Plugin v{version}, {os}, {language_count} languages detected
- Recent errors: {error_count} errors
- Project context: {language} / {framework}
```

#### Phase 4: Sanitization & Preview

**Apply Sanitization Pipeline** (per plan TD-4):

Run 4-stage sequential sanitization on ALL diagnostic data. Each stage processes the output of the previous stage, ensuring comprehensive PII removal.

**STAGE 1: PathSanitizer**

**Purpose**: Strip usernames from file paths and normalize to workspace-relative paths.

**Algorithm**:

1. **Windows Path Sanitization**:
   - **Pattern**: `[A-Z]:\\Users\\[\w\.\-]+\\`
   - **Replacement**: `{WORKSPACE}/`
   - **Example Transformations**:
     - `D:\Users\john.wilson\project\src\file.py` → `{WORKSPACE}/project/src/file.py`
     - `C:\Users\jane_doe\Documents\code\test.py` → `{WORKSPACE}/Documents/code/test.py`
     - `E:\Users\admin\workspace\plugin\main.py` → `{WORKSPACE}/workspace/plugin/main.py`

2. **Linux/macOS Path Sanitization**:
   - **Pattern**: `/home/[\w\.\-]+/`
   - **Replacement**: `{WORKSPACE}/`
   - **Example Transformations**:
     - `/home/john.wilson/project/src/file.py` → `{WORKSPACE}/project/src/file.py`
     - `/home/jane_doe/workspace/test.py` → `{WORKSPACE}/workspace/test.py`
     - `/home/admin/code/plugin/main.py` → `{WORKSPACE}/code/plugin/main.py`

3. **macOS /Users Path Sanitization**:
   - **Pattern**: `/Users/[\w\.\-]+/`
   - **Replacement**: `{WORKSPACE}/`
   - **Example Transformations**:
     - `/Users/john.wilson/project/src/file.py` → `{WORKSPACE}/project/src/file.py`
     - `/Users/jane_doe/Documents/code/test.py` → `{WORKSPACE}/Documents/code/test.py`

4. **Drive Letter Normalization**:
   - **Pattern**: `[A-Z]:\\(?!Users)`
   - **Replacement**: `{DRIVE}/`
   - **Example Transformations**:
     - `D:\project\src\file.py` → `{DRIVE}/project/src/file.py`
     - `C:\code\test.py` → `{DRIVE}/code/test.py`

**Edge Cases**:
- **Nested user paths**: `D:\Users\john\Users\data\file.txt` → `{WORKSPACE}/Users/data/file.txt` (only first occurrence replaced)
- **Case sensitivity**: Pattern matches Windows paths case-insensitively (D: or d:)
- **Unicode usernames**: Pattern supports Unicode characters in usernames: `/home/josé/file.py` → `{WORKSPACE}/file.py`
- **Very long paths**: Paths > 260 characters (Windows MAX_PATH) are processed normally (no special handling needed)

**Security Note**: This sanitizer removes PII (usernames) from paths while preserving relative structure for debugging context.

---

**STAGE 2: CredentialRedactor**

**Purpose**: Redact API keys, tokens, passwords, secrets, and authentication credentials.

**Algorithm**:

**Pattern**: `(api_key|token|password|secret|auth|bearer|authorization|api-key|access_key|secret_key|private_key|session|jwt|apikey|api_token|auth_token)\s*[=:]\s*[\w\-\.\/+=]+`
  - **Note**: Pattern includes `/`, `+`, and `=` to match base64-encoded secrets (e.g., `api_key=dGVzdC9zZWNyZXQrYmFzZTY0`)

**Replacement**: `[REDACTED]`

**Case Sensitivity**: Case-insensitive matching (api_key, API_KEY, Api_Key all match)

**Example Transformations**:

1. **API Keys**:
   - `api_key=sk_live_1234567890abcdef` → `[REDACTED]`
   - `API_KEY: abcd1234efgh5678` → `[REDACTED]`
   - `apikey=xyz789` → `[REDACTED]`

2. **Tokens**:
   - `token: ghp_1234567890abcdefghij` → `[REDACTED]`
   - `auth_token=Bearer abc123` → `[REDACTED]`
   - `jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` → `[REDACTED]`

3. **Passwords**:
   - `password=MySecretP@ssw0rd` → `[REDACTED]`
   - `PASSWORD: admin123` → `[REDACTED]`
   - `secret=supersecret123` → `[REDACTED]`

4. **Bearer Tokens**:
   - `Authorization: Bearer abc123xyz` → `[REDACTED]`
   - `bearer=token123` → `[REDACTED]`

5. **AWS Keys**:
   - `AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` → `[REDACTED]`
   - `access_key: AKIAIOSFODNN7EXAMPLE` → `[REDACTED]`

6. **Base64-Encoded Secrets**:
   - `api_key=dGVzdC9zZWNyZXQrYmFzZTY0` → `[REDACTED]`
   - `token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0=` → `[REDACTED]`
   - `secret=YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=` → `[REDACTED]`

7. **Private Keys**:
   - `private_key=-----BEGIN RSA PRIVATE KEY-----` → `[REDACTED]`
   - `secret_key: sk_test_123456` → `[REDACTED]`

**Extended Pattern for Multi-line Credentials**:
- **Pattern**: `(api_key|token|password|secret)\s*[=:]\s*["']([^"']+)["']`
- **Example**: `api_key="sk_live_1234567890"` → `[REDACTED]`

**Quoted Credentials**:
- **Pattern**: `(api_key|token|password|secret)\s*[=:]\s*["'][\w\-\.]+["']`
- **Example**: `token: "ghp_abcdef123456"` → `[REDACTED]`

**Edge Cases**:
- **Configuration files**: Handles KEY=value format (dotenv, config files)
- **JSON format**: Handles "key": "value" format: `"api_key": "abc123"` → `[REDACTED]`
- **YAML format**: Handles key: value format: `api_key: abc123` → `[REDACTED]`
- **URL parameters**: `?api_key=abc123&token=xyz` → `?[REDACTED]&[REDACTED]`
- **Environment variables**: `export API_KEY=abc123` → `export [REDACTED]`
- **False positives**: Pattern may redact non-sensitive data like "password: ********" (already masked) - this is acceptable (safe to redact)

**Security Note**: This sanitizer uses aggressive pattern matching to prevent credential leakage. False positives (non-sensitive data redacted) are acceptable to ensure zero credential exposure.

---

**STAGE 3: IPAddressRemover**

**Purpose**: Redact IP addresses (IPv4 and IPv6) while preserving safe local addresses.

**Algorithm**:

**IPv4 Pattern**: `\b(\d{1,3}\.){3}\d{1,3}\b`

**IPv6 Pattern**: `\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b`

**IPv6 Compressed Pattern**: `\b([0-9a-fA-F]{1,4}:){1,7}:([0-9a-fA-F]{1,4})?` (handles :: notation)
  - **Note**: This pattern covers common IPv6 compressed forms but may not match all RFC 4291 variants (e.g., `::1`, `::`, `2001:db8::`). For production implementation, consider using a dedicated IPv6 validation library or the more comprehensive pattern: `(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))`

**Replacement**: `[IP]` for IPv4, `[IPv6]` for IPv6

**Allowlist** (do NOT redact these safe addresses):
- `127.0.0.1` (IPv4 localhost)
- `::1` (IPv6 localhost)
- `0.0.0.0` (IPv4 any/unspecified)
- `::` (IPv6 any/unspecified)
- `localhost` (hostname, not IP but commonly used)
- `255.255.255.255` (IPv4 broadcast)
- Private ranges (OPTIONAL - see note below):
  - `10.0.0.0/8` (10.x.x.x)
  - `172.16.0.0/12` (172.16.x.x - 172.31.x.x)
  - `192.168.0.0/16` (192.168.x.x)

**Example Transformations**:

1. **Public IPv4 Addresses** (redacted):
   - `Error connecting to 203.0.113.42` → `Error connecting to [IP]`
   - `Request timeout: 198.51.100.1` → `Request timeout: [IP]`
   - `DNS resolved to 8.8.8.8` → `DNS resolved to [IP]`

2. **Localhost IPv4** (preserved):
   - `Server running on 127.0.0.1:8080` → `Server running on 127.0.0.1:8080` (NOT redacted)
   - `Connected to 0.0.0.0` → `Connected to 0.0.0.0` (NOT redacted)

3. **Private IPv4 Addresses** (redacted or preserved based on policy):
   - **Policy A (Redact all non-localhost)**: `Connected to 192.168.1.1` → `Connected to [IP]`
   - **Policy B (Preserve private)**: `Connected to 192.168.1.1` → `Connected to 192.168.1.1` (NOT redacted)
   - **Recommended**: Policy A (redact all) for maximum privacy

4. **IPv6 Addresses** (redacted):
   - `Connected to 2001:0db8:85a3:0000:0000:8a2e:0370:7334` → `Connected to [IPv6]`
   - `DNS: fe80::1` → `DNS: [IPv6]`
   - `Server: 2001:db8::1` → `Server: [IPv6]`

5. **IPv6 Localhost** (preserved):
   - `Listening on ::1` → `Listening on ::1` (NOT redacted)
   - `Connected to ::1:8080` → `Connected to ::1:8080` (NOT redacted)

6. **IP Addresses in URLs** (redacted):
   - `http://203.0.113.42:8080/api` → `http://[IP]:8080/api`
   - `https://198.51.100.1/endpoint` → `https://[IP]/endpoint`

7. **IP Addresses in Error Messages** (redacted):
   - `TimeoutError: Connection to 203.0.113.42 timed out` → `TimeoutError: Connection to [IP] timed out`
   - `NetworkError: Failed to reach 198.51.100.1` → `NetworkError: Failed to reach [IP]`

**Edge Cases**:
- **Version numbers**: `Python 3.11.2` should NOT be redacted (not an IP)
  - **Detection**: The pattern `\b(\d{1,3}\.){3}\d{1,3}\b` technically matches `3.11.2` (4 segments), but IPv4 validation (lines 1018-1035) will reject it because octet 11 > 255 would fail in a valid IP context. In practice, context (preceding word "Python") prevents false matches.
  - **Validation Strategy**: Apply IPv4 octet validation (0-255 range check) AFTER pattern matching to reject version numbers
- **Port numbers**: `192.168.1.1:8080` → `[IP]:8080` (preserve port for context)
- **Invalid IPs**: `999.999.999.999` technically matches pattern but is invalid
  - **Policy**: Redact anyway (safer to over-redact than leak)
- **CIDR notation**: `192.168.1.0/24` → `[IP]/24` (preserve subnet mask)
- **IPv6 shorthand**: `::ffff:192.0.2.1` (IPv4-mapped IPv6) → `[IPv6]`

**Implementation Note**:

For IPv4, validate that each octet is 0-255 to avoid false positives:

```python
# Pseudo-code for IPv4 validation
def is_valid_ipv4(ip_string):
    octets = ip_string.split('.')
    if len(octets) != 4:
        return False
    for octet in octets:
        if not octet.isdigit():
            return False
        num = int(octet)
        if num < 0 or num > 255:
            return False
    return True

# Only redact if valid IPv4
if is_valid_ipv4(matched_ip) and matched_ip not in allowlist:
    redact(matched_ip)
```

**Recommended Policy**: Redact ALL IP addresses except localhost (127.0.0.1, ::1, 0.0.0.0, ::). Private IPs (192.168.x.x, 10.x.x.x) should also be redacted to prevent leaking internal network topology.

**Security Note**: This sanitizer prevents exposure of server IPs, client IPs, and internal network topology while preserving localhost references for debugging.

---

**STAGE 4: HostnameStripper**

**Purpose**: Remove hostnames and domain names from error messages to prevent exposure of internal infrastructure.

**Algorithm**:

**Hostname Patterns**:

1. **Fully Qualified Domain Names (FQDN)**:
   - **Pattern**: `\b[\w\-]+\.[\w\-]+\.[a-z]{2,}\b`
   - **Example Transformations**:
     - `Error connecting to server.example.com` → `Error connecting to [HOSTNAME]`
     - `Request failed: api.github.com timeout` → `Request failed: [HOSTNAME] timeout`
     - `DNS lookup failed for db.internal.corp` → `DNS lookup failed for [HOSTNAME]`

2. **Internal Hostnames** (subdomain.domain.tld):
   - **Pattern**: `\b[\w\-]+\.[\w\-]+\.[\w\-]+\.[a-z]{2,}\b`
   - **Example Transformations**:
     - `Connected to jenkins.ci.internal.corp` → `Connected to [HOSTNAME]`
     - `Error: database.prod.aws.company.com unreachable` → `Error: [HOSTNAME] unreachable`

3. **Hostname with Port**:
   - **Pattern**: `\b[\w\-]+\.[\w\-]+\.[a-z]{2,}:\d+\b`
   - **Example Transformations**:
     - `Connecting to api.example.com:443` → `Connecting to [HOSTNAME]:443`
     - `Server at db.internal.corp:5432 timeout` → `Server at [HOSTNAME]:5432 timeout`

4. **Hostname in URLs** (preserve protocol and path structure):
   - **Pattern**: `(https?://)[\w\-]+\.[\w\-]+\.[a-z]{2,}`
   - **Replacement**: `$1[HOSTNAME]`
   - **Example Transformations**:
     - `https://api.github.com/repos/user/repo` → `https://[HOSTNAME]/repos/user/repo`
     - `http://internal.corp/api/v1/data` → `http://[HOSTNAME]/api/v1/data`
     - `https://db.aws.company.com:8080/query` → `https://[HOSTNAME]:8080/query`

5. **Email Domain Stripping**:
   - **Pattern**: `[\w\.\-]+@[\w\-]+\.[\w\-]+\.[a-z]{2,}`
   - **Replacement**: `[EMAIL]@[DOMAIN]`
   - **Example Transformations**:
     - `Contact: john.doe@example.com` → `Contact: [EMAIL]@[DOMAIN]`
     - `From: admin@company.corp` → `From: [EMAIL]@[DOMAIN]`

6. **Machine Hostnames** (without TLD, e.g., dev-machine-01):
   - **Pattern**: `\b(server|host|machine|node|worker|dev|prod|staging|jenkins|db|api|web)[\-\w]*\b`
   - **Replacement**: `[MACHINE]`
   - **Example Transformations**:
     - `Error on dev-machine-01` → `Error on [MACHINE]`
     - `Connected to jenkins-worker-03` → `Connected to [MACHINE]`
     - `Database host: db-prod-master` → `Database host: [MACHINE]`

**Allowlist** (do NOT redact these safe hostnames):
- `localhost`
- `github.com` (public service, no privacy concern)
- `pypi.org` (public service)
- `npmjs.com` (public service)
- `maven.apache.org` (public service)
- `*.github.io` (public GitHub Pages)
- `*.readthedocs.io` (public documentation)

**Example Transformations**:

1. **Internal Hostnames** (redacted):
   - `Error: Connection to jenkins.ci.internal.example.com failed` → `Error: Connection to [HOSTNAME] failed`
   - `Timeout reaching db-prod-01.aws.company.net` → `Timeout reaching [HOSTNAME]`
   - `API call to api.staging.corp:8080 failed` → `API call to [HOSTNAME]:8080 failed`

2. **Public Hostnames** (preserved if in allowlist, redacted otherwise):
   - `Downloading from pypi.org` → `Downloading from pypi.org` (NOT redacted)
   - `Cloning from github.com/user/repo` → `Cloning from github.com/user/repo` (NOT redacted)
   - `Error from api.custom-service.com` → `Error from [HOSTNAME]` (redacted)

3. **Mixed Context** (partial redaction):
   - `Error: Failed to connect to db.internal.corp, tried github.com fallback` → `Error: Failed to connect to [HOSTNAME], tried github.com fallback`
   - `Timeout on jenkins-01, contact admin@company.com` → `Timeout on [MACHINE], contact [EMAIL]@[DOMAIN]`

4. **URLs with Hostnames** (preserve structure):
   - `GET https://api.internal.corp/v1/users failed` → `GET https://[HOSTNAME]/v1/users failed`
   - `POST http://db.staging.aws.com:8080/query timeout` → `POST http://[HOSTNAME]:8080/query timeout`

**Edge Cases**:
- **File extensions**: `test.py` should NOT be redacted (not a hostname)
  - **Detection**: Check for TLD presence (.com, .net, .org, .io, etc.)
  - **Example**: `test.py` does NOT match `\b[\w\-]+\.[\w\-]+\.[a-z]{2,}\b`
- **Version numbers**: `package-1.2.3` should NOT be redacted
  - **Detection**: Numeric TLD is invalid (no .3 TLD exists)
- **Floating point numbers**: `3.14.159` should NOT be redacted
  - **Detection**: Numeric segments indicate non-hostname
- **Abbreviations**: `U.S.A` should NOT be redacted
  - **Detection**: Single-letter segments indicate abbreviation, not hostname
- **Localhost variations**: `localhost.localdomain` → `localhost.localdomain` (NOT redacted)

**Implementation Note**:

For hostname detection, use a TLD validation list to avoid false positives:

```python
# Pseudo-code for hostname validation
VALID_TLDS = ['com', 'net', 'org', 'io', 'co', 'gov', 'edu', 'mil', 'int', 'corp', 'local', ...]

def is_valid_hostname(hostname_string):
    parts = hostname_string.split('.')
    if len(parts) < 2:
        return False
    tld = parts[-1].lower()
    if tld not in VALID_TLDS:
        return False
    # Check for numeric segments (likely version number)
    if all(part.isdigit() for part in parts):
        return False
    return True

# Only redact if valid hostname and not in allowlist
if is_valid_hostname(matched_hostname) and matched_hostname not in allowlist:
    redact(matched_hostname)
```

**Recommended Policy**: Redact all hostnames except public services (github.com, pypi.org, etc.) and localhost. Internal hostnames (*.corp, *.internal, *.aws) should ALWAYS be redacted to prevent infrastructure exposure.

**Security Note**: This sanitizer prevents exposure of internal infrastructure, server names, and network topology while preserving public service references and URL structure for debugging context.

---

**SANITIZATION PIPELINE EXECUTION**

**Processing Order** (CRITICAL):

The 4 stages MUST execute sequentially in this exact order:

1. **PathSanitizer** (Stage 1) → processes raw diagnostic data
2. **CredentialRedactor** (Stage 2) → processes Stage 1 output
3. **IPAddressRemover** (Stage 3) → processes Stage 2 output
4. **HostnameStripper** (Stage 4) → processes Stage 3 output

**Why Sequential?**
- Each stage may introduce new patterns that need sanitization by later stages
- Example: PathSanitizer outputs `{WORKSPACE}/` which should NOT be further processed
- Example: CredentialRedactor outputs `[REDACTED]` which should NOT match IP patterns

**Performance Target**: < 2 seconds total for all 4 stages (per REQ-NF-1)

**Algorithm for Pipeline**:

```python
# Pseudo-code for sanitization pipeline
def sanitize_diagnostics(diagnostics_data):
    # Stage 1: PathSanitizer
    data = apply_path_sanitizer(diagnostics_data)

    # Stage 2: CredentialRedactor
    data = apply_credential_redactor(data)

    # Stage 3: IPAddressRemover
    data = apply_ip_remover(data)

    # Stage 4: HostnameStripper
    data = apply_hostname_stripper(data)

    return data

# Apply to all diagnostic categories
sanitized_diagnostics = {
    "command_history": sanitize_diagnostics(raw_diagnostics["command_history"]),
    "environment": sanitize_diagnostics(raw_diagnostics["environment"]),
    "errors": sanitize_diagnostics(raw_diagnostics["errors"]),
    "project_context": sanitize_diagnostics(raw_diagnostics["project_context"])
}
```

**Example: Full Pipeline Transformation**:

**Input** (raw diagnostic data):
```
Error: Failed to connect to database at D:\Users\john.wilson\project\config.py:42
Connection string: postgresql://admin:MyP@ssw0rd@192.168.1.100:5432/db
Server: db-prod-01.internal.example.com
API key: api_key=sk_live_1234567890abcdef
Client IP: 203.0.113.42
```

**After Stage 1 (PathSanitizer)**:
```
Error: Failed to connect to database at {WORKSPACE}/project/config.py:42
Connection string: postgresql://admin:MyP@ssw0rd@192.168.1.100:5432/db
Server: db-prod-01.internal.example.com
API key: api_key=sk_live_1234567890abcdef
Client IP: 203.0.113.42
```

**After Stage 2 (CredentialRedactor)**:
```
Error: Failed to connect to database at {WORKSPACE}/project/config.py:42
Connection string: postgresql://admin:[REDACTED]@192.168.1.100:5432/db
Server: db-prod-01.internal.example.com
API key: [REDACTED]
Client IP: 203.0.113.42
```

**After Stage 3 (IPAddressRemover)**:
```
Error: Failed to connect to database at {WORKSPACE}/project/config.py:42
Connection string: postgresql://admin:[REDACTED]@[IP]:5432/db
Server: db-prod-01.internal.example.com
API key: [REDACTED]
Client IP: [IP]
```

**After Stage 4 (HostnameStripper)**:
```
Error: Failed to connect to database at {WORKSPACE}/project/config.py:42
Connection string: postgresql://admin:[REDACTED]@[IP]:5432/db
Server: [HOSTNAME]
API key: [REDACTED]
Client IP: [IP]
```

**Final Output** (fully sanitized):
```
Error: Failed to connect to database at {WORKSPACE}/project/config.py:42
Connection string: postgresql://admin:[REDACTED]@[IP]:5432/db
Server: [HOSTNAME]
API key: [REDACTED]
Client IP: [IP]
```

**Security Verification**: Zero PII remaining (no usernames, passwords, IPs, internal hostnames)

---

**Generate Preview** (per plan preview format):
```markdown
## Feedback Preview

**Type**: {feedback_type}
**Title**: {title}

### Description
{description}

---

## Diagnostic Information

### Command History (Last 20 commands)
1. {timestamp} - {command} {args}
2. {timestamp} - {command} {args}
...

### Environment
- **Plugin Version**: {plugin_version}
- **OS**: {os}
- **Python**: {python_version}
- **Node.js**: {node_version}

### Recent Errors (Last 10 or 24 hours)
1. {timestamp} - {error_message}
   File: {file_location}
...

### Project Context
- **Language**: {language}
- **Framework**: {framework}
- **Test Files**: {test_file_count}
- **Test Executions**: {test_execution_count} (last 7 days)

---

**Action**: This data will be submitted to GitHub. You can approve, edit, or cancel.
```

#### Phase 5: User Approval

**Use AskUserQuestion** (iterative approval loop, max 3 iterations):
```markdown
Review the feedback preview above. How would you like to proceed?

Options:
1. Approve - Submit this feedback to GitHub
2. Edit - Remove or modify diagnostic sections
3. Cancel - Abandon feedback submission
```

**Handle User Choice**:

- **Approve**: Proceed to Phase 6 (Submission)
- **Cancel**: Display "Feedback submission cancelled" and STOP
- **Edit**:
  1. Ask: "Which section to modify?"
     - Option 1: Remove command history
     - Option 2: Remove errors
     - Option 3: Remove project context
     - Option 4: Remove all diagnostics
     - Option 5: Custom edit (describe changes)
  2. Apply requested edits
  3. Regenerate preview
  4. Loop back to approval (max 3 iterations total)
  5. After 3 iterations, force choice: Approve or Cancel

#### Phase 6: Submission or Queueing

**Check GitHub CLI Availability** (per plan TD-5):

**GHCLIDetector Algorithm** (TASK-007):

**Purpose**: Detect `gh` CLI installation and authentication status to determine GitHub submission capability.

**Step 1: Detect gh CLI Installation**

Execute subprocess to check if `gh` CLI is installed:

```python
# Subprocess command (SECURITY: per SECURITY.md)
command = ["gh", "--version"]
shell = False  # REQUIRED: prevent command injection
timeout = 2  # seconds (fast detection, don't delay workflow)

# Execute detection
try:
    result = subprocess.run(
        command,
        shell=False,
        capture_output=True,
        timeout=2,
        text=True
    )

    # Check exit code
    if result.returncode == 0:
        # gh CLI is installed
        installed = True
        # Parse version from stdout (format: "gh version X.Y.Z")
        version_output = result.stdout.strip()
        # Extract version string: "gh version 2.40.1 (2024-01-15)" → "2.40.1"
        import re
        version_match = re.search(r'gh version ([\d\.]+)', version_output)
        version = version_match.group(1) if version_match else "unknown"
    else:
        # gh returned non-zero exit (unexpected, treat as not installed)
        installed = False
        version = None

except FileNotFoundError:
    # gh command not found (not installed or not in PATH)
    installed = False
    version = None

except subprocess.TimeoutExpired:
    # gh --version timed out (2 seconds) - unusual, treat as not installed
    installed = False
    version = None

except Exception as e:
    # Any other error (permission denied, etc.) - treat as not installed
    installed = False
    version = None
```

**Step 2: Check Authentication Status** (if installed)

If `gh` CLI is installed, check authentication:

```python
# Only check auth if gh is installed
if installed:
    # Subprocess command (SECURITY: per SECURITY.md)
    auth_command = ["gh", "auth", "status"]
    shell = False  # REQUIRED
    timeout = 2  # seconds

    try:
        auth_result = subprocess.run(
            auth_command,
            shell=False,
            capture_output=True,
            timeout=2,
            text=True
        )

        # Check exit code
        if auth_result.returncode == 0:
            # Authenticated successfully
            authenticated = True
        else:
            # Not authenticated (exit code 1 typical for "not logged in")
            authenticated = False

    except subprocess.TimeoutExpired:
        # Auth check timed out - treat as not authenticated
        authenticated = False

    except Exception as e:
        # Any other error - treat as not authenticated
        authenticated = False
else:
    # gh not installed, can't be authenticated
    authenticated = False
```

**Step 3: Return Structured Status**

```python
# Return detection result
gh_status = {
    "installed": installed,      # bool: True if gh CLI found and working
    "authenticated": authenticated,  # bool: True if gh auth status succeeded
    "version": version            # str: version number or None
}

# Example outputs:
# {"installed": True, "authenticated": True, "version": "2.40.1"}
# {"installed": True, "authenticated": False, "version": "2.40.1"}
# {"installed": False, "authenticated": False, "version": None}
```

**Security Requirements** (per SECURITY.md):

1. **Subprocess Security**:
   - Use array form: `["gh", "--version"]` (NOT string)
   - Set `shell=False` (CRITICAL: prevents command injection)
   - Set timeout: 2 seconds per subprocess call (prevents hanging)
   - Capture output safely: `capture_output=True`, `text=True`

2. **No User Input in Commands**:
   - Commands are hardcoded: `["gh", "--version"]` and `["gh", "auth", "status"]`
   - No user-controlled paths or arguments
   - No dynamic command construction

3. **Graceful Error Handling**:
   - FileNotFoundError → gh not installed (NOT an exception to user)
   - TimeoutExpired → treat as not installed/authenticated
   - Any other error → treat as not installed/authenticated
   - Never expose system internals in error messages

**Error Handling**:

- **gh not found** (FileNotFoundError): Return `{installed: False, authenticated: False, version: None}`
- **gh --version timeout**: Return `{installed: False, authenticated: False, version: None}`
- **gh --version non-zero exit**: Return `{installed: False, authenticated: False, version: None}`
- **gh auth status timeout**: Return `{installed: True, authenticated: False, version: "X.Y.Z"}`
- **gh auth status non-zero exit**: Return `{installed: True, authenticated: False, version: "X.Y.Z"}`
- **Any unexpected error**: Return `{installed: False, authenticated: False, version: None}`

**Example Scenarios**:

**Scenario 1: gh CLI Installed and Authenticated** (Happy Path)

```
Input: User has gh CLI version 2.40.1 installed and authenticated
Subprocess 1: ["gh", "--version"] → exit code 0, stdout "gh version 2.40.1 (2024-01-15)"
Subprocess 2: ["gh", "auth", "status"] → exit code 0, stdout "Logged in to github.example.com as john.wilson"
Output: {"installed": True, "authenticated": True, "version": "2.40.1"}
Next Action: Proceed to GitHub issue submission (Submission Path A)
```

**Scenario 2: gh CLI Not Installed**

```
Input: User does not have gh CLI installed
Subprocess 1: ["gh", "--version"] → FileNotFoundError (command not found)
Output: {"installed": False, "authenticated": False, "version": None}
Next Action: Fallback to clipboard copy (Submission Path B)
User Message: "GitHub CLI (gh) is not available. Install from https://cli.github.com/"
```

**Scenario 3: gh CLI Installed but Not Authenticated**

```
Input: User has gh CLI version 2.40.1 installed but not authenticated
Subprocess 1: ["gh", "--version"] → exit code 0, stdout "gh version 2.40.1 (2024-01-15)"
Subprocess 2: ["gh", "auth", "status"] → exit code 1, stderr "You are not logged into any GitHub hosts."
Output: {"installed": True, "authenticated": False, "version": "2.40.1"}
Next Action: Fallback to clipboard copy (Submission Path B)
User Message: "GitHub CLI is installed but not authenticated. Run: gh auth login"
```

**Scenario 4: gh CLI Timeout** (Unusual)

```
Input: gh CLI exists but hangs during execution
Subprocess 1: ["gh", "--version"] → TimeoutExpired after 2 seconds
Output: {"installed": False, "authenticated": False, "version": None}
Next Action: Fallback to clipboard copy (Submission Path B)
User Message: "GitHub CLI detection timed out. Please check your gh CLI installation."
```

**Scenario 5: gh CLI Permission Error**

```
Input: gh CLI exists but user lacks permission to execute it
Subprocess 1: ["gh", "--version"] → PermissionError
Output: {"installed": False, "authenticated": False, "version": None}
Next Action: Fallback to clipboard copy (Submission Path B)
User Message: "GitHub CLI is not accessible. Check file permissions."
```

**Performance**:

- **Best case** (installed + authenticated): ~0.5 seconds (2 subprocess calls)
- **Not installed**: ~0.1 seconds (1 subprocess call, immediate FileNotFoundError)
- **Installed but not authenticated**: ~0.5 seconds (2 subprocess calls)
- **Timeout**: 2 seconds (worst case for version check) + 2 seconds (auth check) = 4 seconds max

**Trade-offs**:

- **Short timeout (2s)**: Ensures fast workflow, but may miss slow systems
- **No retry logic**: Single attempt per check, fail fast to avoid delays
- **Version parsing is optional**: If version extraction fails, use "unknown" - doesn't affect submission capability

**Integration with Submission Paths**:

After detection, route to appropriate submission path:

```python
gh_status = detect_gh_cli()  # Run GHCLIDetector algorithm

if gh_status["installed"] and gh_status["authenticated"]:
    # Path A: Submit via gh CLI
    submit_via_gh_cli(feedback_data, gh_status["version"])
elif gh_status["installed"] and not gh_status["authenticated"]:
    # Path B: Clipboard fallback (not authenticated)
    display_auth_error()
    copy_to_clipboard(feedback_data)
else:
    # Path B: Clipboard fallback (not installed)
    display_install_instructions()
    copy_to_clipboard(feedback_data)
```

---

**ClipboardFallback Algorithm** (TASK-010):

**Purpose**: Copy formatted feedback issue to system clipboard when GitHub CLI is unavailable (not installed or not authenticated), enabling users to manually submit via GitHub web UI.

**Input**:
- `formatted_issue`: string (title + body with diagnostic information, already sanitized)
- `manual_url`: string (GitHub issue creation URL)

**Output**:
```python
{
    "success": bool,         # True if clipboard copy succeeded, False if fallback to manual display
    "method": str,           # "clipboard" if copied successfully, "manual" if displayed for manual copy
    "error": str | None      # Error message if clipboard failed, None if successful
}
```

**Algorithm** (4 steps per plan TD-5):

**Step 1: Detect OS Platform**

Use platform detection to determine which clipboard command to use:

<!-- IMPLEMENTATION REFERENCE: Platform Detection (not executable code) -->
> **Note**: This pseudo-code demonstrates clipboard command selection logic. Actual implementation must handle platform-specific edge cases.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
import sys

# Detect operating system
platform = sys.platform  # Returns: 'win32', 'darwin', 'linux', etc.

if platform == 'win32':
    clipboard_command = ["clip"]
elif platform == 'darwin':
    clipboard_command = ["pbcopy"]
elif platform.startswith('linux'):
    clipboard_command = ["xclip", "-selection", "clipboard"]
else:
    # Unknown platform - skip to manual fallback
    clipboard_command = None
```

**Platform-Specific Commands**:
- **Windows**: `clip` (built-in, accepts stdin)
- **macOS**: `pbcopy` (built-in, accepts stdin)
- **Linux**: `xclip -selection clipboard` (may require installation: `apt install xclip` or `yum install xclip`)

**Step 2: Attempt Clipboard Copy via Subprocess**

Execute clipboard command with formatted issue text as stdin (SECURITY: never in arguments per SECURITY.md):

<!-- SECURITY DOCUMENTATION: Clipboard Subprocess Security -->
> **Security Note**: This pseudo-code demonstrates secure subprocess patterns per SECURITY.md. User data MUST be passed via stdin, never in arguments.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
import subprocess

if clipboard_command is not None:
    try:
        # SECURITY REQUIREMENTS per SECURITY.md:
        # - Hardcoded command paths (no user input in command position)
        # - User data in stdin (NOT arguments)
        # - shell=False (prevent command injection)
        # - Timeout to prevent hanging

        result = subprocess.run(
            clipboard_command,
            input=formatted_issue,      # User data in stdin
            shell=False,                # REQUIRED: prevent command injection
            capture_output=True,
            timeout=5,                  # seconds
            text=True,                  # Decode stdin/stdout as text
            check=False                 # Don't raise exception on non-zero exit
        )

        if result.returncode == 0:
            # Clipboard copy succeeded
            clipboard_success = True
            clipboard_error = None
        else:
            # Command failed (non-zero exit)
            clipboard_success = False
            clipboard_error = f"Clipboard command failed: {result.stderr.strip()}"

    except FileNotFoundError:
        # Clipboard utility not installed
        clipboard_success = False
        clipboard_error = f"Clipboard utility not found: {clipboard_command[0]}"

    except subprocess.TimeoutExpired:
        # Command hung (rare but possible)
        clipboard_success = False
        clipboard_error = "Clipboard command timed out after 5 seconds"

    except PermissionError:
        # Clipboard utility not executable (rare)
        clipboard_success = False
        clipboard_error = f"Permission denied executing: {clipboard_command[0]}"

    except Exception as e:
        # Generic fallback for unexpected errors
        clipboard_success = False
        clipboard_error = f"Clipboard error: {str(e)}"
else:
    # Unknown platform or clipboard_command is None
    clipboard_success = False
    clipboard_error = "Clipboard not supported on this platform"
```

**Step 3: Return Structured Status**

Based on clipboard operation result:

<!-- IMPLEMENTATION REFERENCE: Return Status Structure -->
```text
EXAMPLE IMPLEMENTATION REFERENCE:
if clipboard_success:
    return {
        "success": True,
        "method": "clipboard",
        "error": None
    }
else:
    return {
        "success": False,
        "method": "manual",
        "error": clipboard_error
    }
```

**Step 4: Display User-Facing Message**

Based on return status, display appropriate message:

**Success (clipboard copy worked)**:
```markdown
✅ Formatted issue copied to clipboard!

To submit manually:
1. Visit: https://github.example.com/my-org/my-plugin/issues/new
2. Paste the clipboard content as the issue body
3. Add a title if needed
4. Click "Submit new issue"
```

**Failure (clipboard unavailable, fallback to manual)**:
```markdown
⚠️  Clipboard unavailable: {clipboard_error}

Please copy the formatted issue below and submit manually:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{formatted_issue}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To submit:
1. Copy the text above (between the lines)
2. Visit: https://github.example.com/my-org/my-plugin/issues/new
3. Paste as issue body
4. Add a title if needed
5. Click "Submit new issue"
```

<!-- EXAMPLE SCENARIOS: Clipboard Fallback Use Cases (for documentation only) -->
**Example Scenarios**:

**Scenario 1: Windows - Clipboard Success**
```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
formatted_issue = "## Bug Report\n\nTest generation failed...\n\n## Diagnostics\n..."
platform = "win32"

# Execution
clipboard_command = ["clip"]
subprocess.run(["clip"], input=formatted_issue, shell=False, timeout=5)
# Exit code: 0 (success)

# Output
{
    "success": True,
    "method": "clipboard",
    "error": None
}
```

**Scenario 2: Linux - xclip Not Installed**
```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
formatted_issue = "## Feature Request\n\nAdd Python 3.12 support...\n"
platform = "linux"

# Execution
clipboard_command = ["xclip", "-selection", "clipboard"]
subprocess.run(["xclip", "-selection", "clipboard"], ...)
# Raises: FileNotFoundError

# Output
{
    "success": False,
    "method": "manual",
    "error": "Clipboard utility not found: xclip"
}
# Display formatted_issue directly in terminal for manual copy
```

**Scenario 3: macOS - Clipboard Success**
```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
formatted_issue = "## Question\n\nHow do I configure test timeouts?\n"
platform = "darwin"

# Execution
clipboard_command = ["pbcopy"]
subprocess.run(["pbcopy"], input=formatted_issue, shell=False, timeout=5)
# Exit code: 0 (success)

# Output
{
    "success": True,
    "method": "clipboard",
    "error": None
}
```

**Scenario 4: Windows - Permission Error**
```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
formatted_issue = "## Bug Report\n\nCrash on startup...\n"
platform = "win32"

# Execution
clipboard_command = ["clip"]
subprocess.run(["clip"], ...)
# Raises: PermissionError

# Output
{
    "success": False,
    "method": "manual",
    "error": "Permission denied executing: clip"
}
```

**Scenario 5: Unknown Platform**
```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
formatted_issue = "## Bug Report\n\nError on FreeBSD...\n"
platform = "freebsd13"  # Not win32, darwin, or linux

# Execution
clipboard_command = None  # No known clipboard command

# Output
{
    "success": False,
    "method": "manual",
    "error": "Clipboard not supported on this platform"
}
```

**Integration with Workflow**:

```python
# In Phase 6: GitHub Integration
gh_status = detect_gh_cli()  # GHCLIDetector algorithm

if not (gh_status["installed"] and gh_status["authenticated"]):
    # GitHub CLI unavailable - use clipboard fallback
    clipboard_result = copy_to_clipboard(formatted_issue, manual_url)

    if clipboard_result["success"]:
        display_clipboard_success_message(manual_url)
    else:
        display_manual_fallback_message(formatted_issue, manual_url, clipboard_result["error"])
```

**Security Compliance** (per SECURITY.md):
- ✅ Hardcoded command paths (no user input in command array)
- ✅ User data in stdin (never in command arguments)
- ✅ `shell=False` (prevents command injection)
- ✅ Timeout enforcement (5 seconds)
- ✅ Graceful error handling (all exceptions caught, never crash)
- ✅ No credential handling (clipboard utilities don't require auth)

**Performance**:
- **Best case** (clipboard success): ~0.1 seconds
- **Worst case** (timeout): 5 seconds
- **Fallback** (manual display): Instant (no subprocess)

**Edge Cases Handled**:
- Unknown platform (e.g., FreeBSD, Solaris) → Manual fallback
- Clipboard utility not installed (e.g., xclip on Linux) → Manual fallback
- Permission errors → Manual fallback
- Timeout (command hangs) → Manual fallback after 5s
- Very large formatted_issue (>1MB) → Still works (stdin has no practical size limit)
- Unicode content → Handled via `text=True` parameter
- Empty formatted_issue → Works (copies empty string, unusual but valid)

---

**IssueSubmitter Algorithm** (TASK-008):

**Purpose**: Submit feedback to GitHub by creating an issue via `gh issue create` subprocess, parsing the issue URL from stdout, and returning structured result with success status, URL, or error message.

**Input**:
- `title`: string (user-provided feedback title, 10-100 characters, already validated)
- `body`: string (formatted issue body with description + diagnostics, already sanitized)
- `labels`: string (comma-separated labels from label mapping, e.g., "bug,needs-triage")

**Output**:
```python
{
    "success": bool,           # True if issue created successfully, False otherwise
    "issue_url": str | None,   # GitHub issue URL if successful, None if failed
    "error": str | None        # Error message if failed, None if successful
}
```

**Algorithm** (5 steps per plan TD-5):

**Step 1: Construct gh CLI Command**

Build the subprocess command array with hardcoded repository per plan TD-9:

<!-- IMPLEMENTATION REFERENCE: gh CLI Command Construction (not executable code) -->
> **Security Note**: This pseudo-code demonstrates secure command construction per SECURITY.md. Array form with shell=False is required.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
import subprocess

# Hardcoded repository (per spec REQ-F-4 and plan TD-9)
GITHUB_REPO = "github.example.com/my-org/my-plugin"

# Construct command array (SECURITY: per SECURITY.md)
# - Array form (NOT string)
# - shell=False (prevent command injection)
# - User data only in --title and --body arguments (gh CLI handles escaping)
command = [
    "gh", "issue", "create",
    "--repo", GITHUB_REPO,
    "--title", title,      # User-provided title (validated, 10-100 chars)
    "--body", body,        # Formatted body with diagnostics (already sanitized)
    "--label", labels      # Comma-separated labels (e.g., "bug,needs-triage")
]
```

**Security Compliance** (per SECURITY.md):
- ✅ Array form command (NOT string concatenation)
- ✅ `shell=False` (prevents command injection)
- ✅ User data only in `--title` and `--body` arguments (safe because gh CLI handles escaping)
- ✅ No user input in command position (all command tokens are hardcoded)
- ✅ Repository hardcoded (prevents arbitrary repository submission)

**Step 2: Execute Subprocess with Timeout**

Execute the command with security constraints per spec REQ-NF-2 (30-second timeout):

<!-- SECURITY DOCUMENTATION: Subprocess Execution with Timeout -->
> **Security Note**: This pseudo-code demonstrates secure subprocess execution per SECURITY.md and spec REQ-NF-2. Timeout enforcement is mandatory.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
try:
    # Execute gh issue create
    # Timeout: 30 seconds per spec REQ-NF-2 (GitHub API call latency)
    result = subprocess.run(
        command,
        shell=False,                # REQUIRED: prevent command injection
        capture_output=True,
        timeout=30,                 # REQUIRED: per spec REQ-NF-2
        text=True,                  # Decode stdout/stderr as text
        check=False                 # Don't raise exception on non-zero exit
    )

    # Store exit code and outputs for parsing
    exit_code = result.returncode
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

except subprocess.TimeoutExpired:
    # Network timeout or slow GitHub API
    return {
        "success": False,
        "issue_url": None,
        "error": "GitHub API request timed out after 30 seconds. Please retry."
    }

except FileNotFoundError:
    # gh CLI not found (should not happen - GHCLIDetector runs first)
    return {
        "success": False,
        "issue_url": None,
        "error": "GitHub CLI (gh) not found. Please install from https://cli.github.com/"
    }

except PermissionError:
    # Permission denied executing gh CLI
    return {
        "success": False,
        "issue_url": None,
        "error": "Permission denied executing gh CLI. Check file permissions."
    }

except Exception as e:
    # Generic fallback for unexpected errors
    return {
        "success": False,
        "issue_url": None,
        "error": f"Unexpected error during submission: {str(e)}"
    }
```

**Step 3: Parse Exit Code and Determine Success**

Check subprocess exit code to determine if issue creation succeeded:

<!-- IMPLEMENTATION REFERENCE: Exit Code Parsing -->
```text
EXAMPLE IMPLEMENTATION REFERENCE:
# Parse exit code per plan TD-5
if exit_code == 0:
    # Success: Issue created
    submission_succeeded = True
elif exit_code == 1:
    # Authentication error or API error (typical gh CLI error code)
    submission_succeeded = False
else:
    # Other error codes (network error, rate limit, etc.)
    submission_succeeded = False
```

**gh CLI Exit Codes** (per gh CLI documentation):
- **0**: Success, issue created
- **1**: Authentication failure, API error, invalid arguments
- **2+**: Other errors (network failure, rate limit, server error)

**Step 4: Extract Issue URL from stdout**

If submission succeeded (exit code 0), parse stdout to extract the issue URL:

<!-- IMPLEMENTATION REFERENCE: URL Extraction from stdout -->
> **Note**: This pseudo-code demonstrates URL parsing logic using regex patterns. Implementation should handle various gh CLI output formats.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
if submission_succeeded:
    # gh CLI outputs issue URL to stdout on success
    # Format: "https://github.example.com/my-org/my-plugin/issues/123"
    # May also include additional text like "✓ Created issue #123"

    import re

    # Extract URL using regex pattern
    # Pattern matches: https://github.example.com/my-org/my-plugin/issues/{number}
    url_pattern = r'https://github\.example\.com/my-org/my-plugin/issues/\d+'
    url_match = re.search(url_pattern, stdout)

    if url_match:
        issue_url = url_match.group(0)
    else:
        # URL not found in stdout (unexpected, but handle gracefully)
        # Check if stdout contains issue number pattern: "#123"
        issue_num_pattern = r'#(\d+)'
        num_match = re.search(issue_num_pattern, stdout)

        if num_match:
            issue_number = num_match.group(1)
            # Construct URL manually
            issue_url = f"https://github.example.com/my-org/my-plugin/issues/{issue_number}"
        else:
            # No URL or issue number found - fallback to repository issues page
            issue_url = "https://github.example.com/my-org/my-plugin/issues"
```

**Step 5: Return Structured Result**

Return success/failure status with issue URL or error message:

<!-- IMPLEMENTATION REFERENCE: Result Structure -->
```text
EXAMPLE IMPLEMENTATION REFERENCE:
if submission_succeeded:
    return {
        "success": True,
        "issue_url": issue_url,
        "error": None
    }
else:
    # Parse error message from stderr
    error_message = parse_gh_error(stderr, exit_code)

    return {
        "success": False,
        "issue_url": None,
        "error": error_message
    }

# Helper: Parse gh CLI error messages
def parse_gh_error(stderr, exit_code):
    """
    Parse gh CLI stderr to extract user-friendly error message.
    """
    # Common error patterns
    if "authentication" in stderr.lower() or "not logged in" in stderr.lower():
        return "GitHub authentication failed. Run: gh auth login"

    if "rate limit" in stderr.lower():
        return "GitHub API rate limit exceeded. Please try again later."

    if "connection" in stderr.lower() or "network" in stderr.lower():
        return "Network connection error. Check internet connection and retry."

    if "permission" in stderr.lower() or "forbidden" in stderr.lower():
        return "Permission denied. Check repository access rights."

    if "not found" in stderr.lower():
        return "Repository not found. Verify repository URL is correct."

    # Default: include stderr (first 200 chars to avoid overwhelming output)
    if stderr:
        return f"GitHub API error: {stderr[:200]}"
    else:
        return f"GitHub submission failed with exit code {exit_code}"
```

<!-- EXAMPLE SCENARIOS: Issue Submission Use Cases (for documentation only) -->
**Example Scenarios**:

**Scenario 1: Successful Issue Creation** (Happy Path)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Test execution timeout after 5 minutes"
body = "## Description\n\nTests fail with timeout...\n\n## Diagnostics\n..."
labels = "bug,needs-triage"

# Execution
command = ["gh", "issue", "create", "--repo", "github.example.com/my-org/my-plugin",
           "--title", title, "--body", body, "--label", labels]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 0
# Stdout: "https://github.example.com/my-org/my-plugin/issues/42\n"

# Output
{
    "success": True,
    "issue_url": "https://github.example.com/my-org/my-plugin/issues/42",
    "error": None
}
```

**Scenario 2: Authentication Failure**

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Feature request: Add Python 3.12 support"
body = "## Description\n\nPlease add support for Python 3.12...\n"
labels = "enhancement,needs-review"

# Execution
command = ["gh", "issue", "create", "--repo", ..., "--title", title, ...]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 1
# Stderr: "error: authentication failed. Run `gh auth login` to authenticate."

# Output
{
    "success": False,
    "issue_url": None,
    "error": "GitHub authentication failed. Run: gh auth login"
}
```

**Scenario 3: Network Timeout**

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Bug: Plugin crashes on startup"
body = "## Description\n\nPlugin crashes immediately...\n"
labels = "bug,needs-triage"

# Execution
command = ["gh", "issue", "create", ...]
subprocess.run(command, shell=False, timeout=30)
# Raises: subprocess.TimeoutExpired after 30 seconds

# Output
{
    "success": False,
    "issue_url": None,
    "error": "GitHub API request timed out after 30 seconds. Please retry."
}
```

**Scenario 4: Connection Refused** (Network Error)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Question: How to configure test timeouts?"
body = "## Description\n\nI need help configuring...\n"
labels = "question"

# Execution
command = ["gh", "issue", "create", ...]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 1
# Stderr: "error: failed to run `gh issue create`: connection refused"

# Output
{
    "success": False,
    "issue_url": None,
    "error": "Network connection error. Check internet connection and retry."
}
```

**Scenario 5: API Rate Limit**

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Enhancement: Add test report export"
body = "## Description\n\nAdd ability to export...\n"
labels = "enhancement,needs-review"

# Execution
command = ["gh", "issue", "create", ...]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 1
# Stderr: "error: API rate limit exceeded. Try again in 30 minutes."

# Output
{
    "success": False,
    "issue_url": None,
    "error": "GitHub API rate limit exceeded. Please try again later."
}
```

**Scenario 6: Invalid Repository** (Should Not Happen - Hardcoded)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Bug report: Invalid state"
body = "## Description\n\nSomething went wrong...\n"
labels = "bug,needs-triage"

# Execution
command = ["gh", "issue", "create", "--repo", "github.example.com/my-org/my-plugin", ...]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 1
# Stderr: "error: repository not found"

# Output
{
    "success": False,
    "issue_url": None,
    "error": "Repository not found. Verify repository URL is correct."
}
```

**Scenario 7: Issue Number Without Full URL** (gh CLI Output Variation)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
title = "Bug: Memory leak in test loop"
body = "## Description\n\nMemory usage increases...\n"
labels = "bug,needs-triage"

# Execution
command = ["gh", "issue", "create", ...]
subprocess.run(command, shell=False, timeout=30)
# Exit code: 0
# Stdout: "✓ Created issue #57\n" (no full URL, just issue number)

# Parse issue number and construct URL
issue_number = "57"  # Extracted from stdout
issue_url = f"https://github.example.com/my-org/my-plugin/issues/57"

# Output
{
    "success": True,
    "issue_url": "https://github.example.com/my-org/my-plugin/issues/57",
    "error": None
}
```

**Integration with Workflow**:

```python
# In Phase 6: Submission or Queueing
gh_status = detect_gh_cli()  # GHCLIDetector algorithm (TASK-007)

if gh_status["installed"] and gh_status["authenticated"]:
    # GitHub CLI available - submit via IssueSubmitter

    # Format issue body (combine description + diagnostics)
    formatted_body = format_issue_body(description, diagnostics)

    # Submit issue
    result = submit_issue(title, formatted_body, labels_string)

    if result["success"]:
        # Success: Display issue URL
        display_success_message(result["issue_url"])
    else:
        # Submission failed: Determine if should queue or fallback
        if is_network_error(result["error"]):
            # Network error → Queue for retry
            queue_feedback(feedback_data, result["error"])
        else:
            # Auth error or other → Fallback to clipboard
            clipboard_result = copy_to_clipboard(formatted_issue, manual_url)
            display_fallback_message(result["error"], clipboard_result)
else:
    # GitHub CLI not available → Fallback to clipboard (TASK-010)
    clipboard_result = copy_to_clipboard(formatted_issue, manual_url)
    display_clipboard_fallback_message(clipboard_result)

# Helper: Determine if error is network-related (should queue)
def is_network_error(error_message):
    """Check if error indicates network issue (timeout, connection refused)."""
    network_keywords = ["timeout", "connection", "network", "unreachable"]
    return any(keyword in error_message.lower() for keyword in network_keywords)
```

**Security Requirements** (per SECURITY.md):

1. **Subprocess Execution**:
   - ✅ Array form command (NOT string)
   - ✅ `shell=False` (CRITICAL: prevents command injection)
   - ✅ 30-second timeout (per spec REQ-NF-2)
   - ✅ User data only in `--title` and `--body` arguments (gh CLI handles escaping)
   - ✅ No user input in command position

2. **Input Validation**:
   - ✅ Title: 10-100 characters (validated before IssueSubmitter called)
   - ✅ Body: 20-5000 characters (validated before IssueSubmitter called)
   - ✅ Labels: comma-separated string from hardcoded mapping (no user input)
   - ✅ Repository: hardcoded constant (no user configuration)

3. **Error Handling**:
   - ✅ TimeoutExpired → User-friendly message, suggest retry
   - ✅ FileNotFoundError → gh CLI not installed (should not happen, GHCLIDetector runs first)
   - ✅ PermissionError → Permission denied message
   - ✅ Generic exception → Catch all, return error status
   - ✅ Never expose system internals or stack traces to user

**Performance**:

- **Best case** (success): ~2-5 seconds (GitHub API latency)
- **Worst case** (timeout): 30 seconds (enforced timeout per spec REQ-NF-2)
- **Auth failure**: ~1-2 seconds (fast gh CLI error response)
- **Network error**: Variable (depends on connection timeout detection, max 30s)

**Performance Target Compliance** (per spec REQ-NF-2):

Total workflow target: < 30 seconds from collection to submission
- Diagnostic collection: < 10 seconds (REQ-NF-1)
- Sanitization: < 2 seconds
- Preview rendering: < 1 second
- User approval: User-dependent (not counted)
- **IssueSubmitter**: < 10 seconds (typical), 30 seconds max (timeout)
- **Total**: ~24 seconds automated time (within target)

**Edge Cases Handled**:

- **gh CLI exits 0 but no URL in stdout**: Extract issue number pattern, construct URL manually
- **gh CLI exits 0 but neither URL nor issue number found**: Fallback to repository issues page URL
- **Very large body (>100KB)**: gh CLI may reject or truncate - body validation should prevent this upstream
- **Unicode in title/body**: Handled via `text=True` parameter (gh CLI supports UTF-8)
- **Labels with special characters**: gh CLI handles escaping (e.g., labels with spaces: "needs triage")
- **Empty labels string**: gh CLI accepts empty --label argument (no labels applied)
- **Network switches during execution**: Timeout mechanism (30s) ensures eventual failure/retry
- **gh CLI version differences**: URL parsing is robust (regex pattern + fallback to issue number)
- **Concurrent submissions**: Each subprocess is independent (no shared state)

**Error Recovery**:

- **Network timeout** → Queue for automatic retry (TASK-011: QueueWriter)
- **Connection refused** → Queue for automatic retry
- **Authentication failure** → Fallback to clipboard (TASK-010: ClipboardFallback)
- **Rate limit exceeded** → Display error, suggest manual retry later (no queue - likely transient)
- **Repository not found** → Critical error, log for debugging (should never happen - hardcoded repo)
- **Permission denied** → Fallback to clipboard
- **Unexpected error** → Fallback to clipboard + log error for debugging

**Logging** (for debugging):

All errors logged to `.claude/.feedback-errors.log` (not included in feedback diagnostics):

```python
import logging
import datetime

def log_submission_error(error_type, error_message, exit_code=None, stderr=None):
    """Log submission errors for debugging (not exposed to user)."""
    log_file = ".claude/.feedback-errors.log"
    timestamp = datetime.datetime.now().isoformat()

    log_entry = f"{timestamp} | {error_type} | exit_code={exit_code} | {error_message}\n"
    if stderr:
        log_entry += f"  stderr: {stderr[:500]}\n"  # First 500 chars

    # Append to log file (create if missing)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
```

**Trade-offs**:

- **30-second timeout**: Balances reliability (allows slow GitHub API) vs. user experience (long wait)
  - Alternative: 10-second timeout - Rejected (GitHub API can be slow, especially for large bodies)
  - Alternative: 60-second timeout - Rejected (violates spec REQ-NF-2 total time budget)

- **URL parsing from stdout**: Simple regex approach vs. JSON output parsing
  - Alternative: Use `gh issue create --json url` - Rejected (requires gh CLI 2.14+, older versions use plain text)
  - Current approach: Robust regex + fallback to issue number extraction

- **Error message parsing**: Heuristic keyword matching vs. structured error codes
  - Alternative: Parse gh CLI exit codes for specific errors - Rejected (gh CLI documentation doesn't guarantee stable exit codes)
  - Current approach: Keyword matching in stderr (brittle but works for common cases)

**Future Enhancements**:

- **Retry logic with exponential backoff**: For transient network errors, retry 2-3 times before queueing
- **Verbose mode**: Include full gh CLI stderr in error log for debugging
- **Issue template support**: Add `--template` flag if repository has issue templates
- **Assignee/milestone support**: Extend command to support `--assignee` and `--milestone` flags
- **Draft issues**: Add `--draft` flag for preliminary submissions (requires gh CLI 2.20+)

---

**QueueWriter Algorithm** (TASK-011):

**Purpose**: Persist failed feedback submissions to local JSON files in `.claude/.feedback-queue/` directory for automatic retry when network connectivity is restored. Ensures no data loss when GitHub submission fails due to network errors.

**Input**:
- `feedback_data`: dict (complete feedback submission data including type, title, description, diagnostics)
- `error_message`: string (optional - error that caused queueing, for logging purposes)

**Output**:
```python
{
    "success": bool,           # True if queued successfully, False if queueing failed
    "queue_id": str | None,    # Queue identifier (filename stem) if successful, None if failed
    "error": str | None        # Error message if queueing failed, None if successful
}
```

**Algorithm** (6 steps per plan TD-6):

**Step 1: Create Queue Directory**

Ensure `.claude/.feedback-queue/` directory exists with secure permissions:

```python
import os
import stat

# Queue directory path (relative to workspace root)
QUEUE_DIR = ".claude/.feedback-queue/"

# Create directory if missing
if not os.path.exists(QUEUE_DIR):
    try:
        # SECURITY: Create with user-only permissions (per SECURITY.md)
        # mode=0o700 = rwx------ (user: read, write, execute; group/others: none)
        os.makedirs(QUEUE_DIR, mode=0o700, exist_ok=True)
    except PermissionError:
        return {
            "success": False,
            "queue_id": None,
            "error": "Permission denied: Cannot create queue directory. Check filesystem permissions."
        }
    except OSError as e:
        return {
            "success": False,
            "queue_id": None,
            "error": f"Failed to create queue directory: {str(e)}"
        }
```

**Security Compliance** (per SECURITY.md and plan TD-6):
- Directory permissions: 0o700 (user-only read/write/execute)
- Path validation: Hardcoded directory path (no user input in path construction)
- Workspace boundary: Directory created within `.claude/` (plugin state directory)

**Step 2: Generate Unique Filename**

Create filename with timestamp + UUID per plan TD-6 format:

```python
import datetime
import uuid

# Generate timestamp (ISO 8601 compact format for filename)
# Format: YYYYMMDDTHHMMSS (e.g., "20260116T153045")
timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")

# Generate UUID (first 8 characters for brevity)
# Full UUID: "a3f8d9c2-1234-5678-90ab-cdef01234567"
# Short UUID: "a3f8d9c2" (sufficient for collision avoidance)
short_uuid = str(uuid.uuid4())[:8]

# Construct filename: feedback-{timestamp}-{uuid}.json
filename = f"feedback-{timestamp}-{short_uuid}.json"

# Full file path
queue_file_path = os.path.join(QUEUE_DIR, filename)

# Queue ID (filename without .json extension) - for user notification
queue_id = f"feedback-{timestamp}-{short_uuid}"
```

**Filename Convention Rationale** (per plan TD-6):
- **Timestamp first**: Enables sorting by timestamp (oldest first for retry)
- **Compact format**: YYYYMMDDTHHMMSS (no separators) for filesystem compatibility
- **UUID suffix**: Prevents collisions if multiple feedback items queued simultaneously
- **Short UUID**: 8 characters = 4.3 billion possible values (collision probability negligible)

**Step 3: Construct Queue Entry Schema**

Build QueuedFeedback structure per plan TD-6 schema:

<!-- IMPLEMENTATION REFERENCE: Queue Entry Construction (not executable code) -->
> **Note**: The following code blocks are implementation reference examples showing the expected schema structure. These are pseudo-code demonstrations for integration reference.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
# Current timestamp for metadata (ISO 8601 with separators for JSON)
# Format: YYYY-MM-DDTHH:MM:SSZ (e.g., "2026-01-16T15:30:45Z")
queued_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

# Construct queue entry
queue_entry = {
    "feedback_data": feedback_data,  # Complete feedback data (type, title, description, diagnostics)
    "submission_metadata": {
        "attempt_count": 0,          # Initialize to 0 (no retry attempts yet)
        "max_retries": 5,            # Per plan TD-6: retry up to 5 times
        "last_attempted": None,      # No attempt yet (will be updated on first retry)
        "abandoned": False,          # Not abandoned (will be set to True after 5 failures)
        "queued_at": queued_at       # Timestamp when feedback was queued
    },
    "queue_id": queue_id             # Queue identifier for user reference
}
```

**Schema Fields** (per plan TD-6):
- `feedback_data`: Original submission data (type, title, description, diagnostics)
- `attempt_count`: Number of retry attempts (0 = not yet retried)
- `max_retries`: Maximum retry attempts before marking as abandoned (5 per plan)
- `last_attempted`: Timestamp of last retry attempt (None = no attempts yet)
- `abandoned`: Boolean flag (True after max_retries exceeded, requires manual retry)
- `queued_at`: Timestamp when feedback was queued (for sorting and display)
- `queue_id`: User-facing identifier (displayed in notifications)

**Step 4: Write to Temporary File (Atomic Write Pattern)**

Use atomic write pattern to prevent corruption per plan TD-6:

<!-- IMPLEMENTATION REFERENCE: Atomic Write Pattern (not executable code) -->
> **Security Note**: This pseudo-code demonstrates secure atomic write operations. The actual implementation must follow SECURITY.md requirements for file operations.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
import json
import tempfile

try:
    # Generate temporary filename in same directory as final file
    # Pattern: .tmp-{uuid}.json (hidden file, temporary)
    temp_filename = f".tmp-{short_uuid}.json"
    temp_file_path = os.path.join(QUEUE_DIR, temp_filename)

    # Write queue entry to temporary file
    # Use UTF-8 encoding for Unicode support (per spec REQ-F-6)
    # indent=2 for human readability (users can inspect queue files)
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(queue_entry, f, indent=2, ensure_ascii=False)

        # Ensure data is written to disk (flush OS buffers)
        # This prevents data loss if system crashes between write and rename
        f.flush()
        os.fsync(f.fileno())

except PermissionError:
    return {
        "success": False,
        "queue_id": None,
        "error": "Permission denied: Cannot write to queue directory. Check filesystem permissions."
    }
except OSError as e:
    return {
        "success": False,
        "queue_id": None,
        "error": f"Failed to write queue file: {str(e)}"
    }
except Exception as e:
    # Catch JSON serialization errors or unexpected failures
    return {
        "success": False,
        "queue_id": None,
        "error": f"Unexpected error writing queue file: {str(e)}"
    }
```

**Atomic Write Pattern** (per plan TD-6):
1. Write to temporary file (`.tmp-{uuid}.json`) in same directory
2. Flush data to disk (fsync ensures persistence)
3. Rename temporary file to final name (atomic operation on most filesystems)
4. If process crashes during write, temporary file is orphaned (no corruption of final file)
5. If rename fails, final file is unmodified (preserves data integrity)

**Step 5: Set File Permissions (Security Requirement)**

Apply user-only permissions to temporary file per SECURITY.md:

<!-- SECURITY DOCUMENTATION: File Permission Requirements -->
> **Security Note**: This demonstrates file permission requirements per SECURITY.md. Actual implementation must enforce user-only access (0o600).

```text
EXAMPLE IMPLEMENTATION REFERENCE:
try:
    # SECURITY: Set file permissions to 0o600 (user read/write only)
    # This prevents other users on the system from reading feedback data
    # Permission bits: rw------- (user: read, write; group/others: none)
    os.chmod(temp_file_path, stat.S_IRUSR | stat.S_IWUSR)
    # Equivalent: os.chmod(temp_file_path, 0o600)

except PermissionError:
    # Clean up temporary file before returning error
    try:
        os.remove(temp_file_path)
    except:
        pass  # Ignore cleanup errors

    return {
        "success": False,
        "queue_id": None,
        "error": "Permission denied: Cannot set file permissions. Check filesystem settings."
    }
except OSError as e:
    # Clean up temporary file
    try:
        os.remove(temp_file_path)
    except:
        pass

    return {
        "success": False,
        "queue_id": None,
        "error": f"Failed to set file permissions: {str(e)}"
    }
```

**Security Requirements** (per SECURITY.md and spec REQ-NF-6):
- File permissions: 0o600 (user read/write only, no group/others access)
- Rationale: Feedback may contain sensitive diagnostics (command history, errors, paths)
- Platform compatibility: Works on Unix/Linux/macOS (Windows ACLs may differ, but os.chmod is safe)

**Step 6: Atomic Rename to Final Filename**

Rename temporary file to final filename (atomic operation):

<!-- IMPLEMENTATION REFERENCE: Atomic Rename Operation -->
> **Note**: This pseudo-code demonstrates atomic rename for data integrity. Implementation must handle platform-specific behaviors.

```text
EXAMPLE IMPLEMENTATION REFERENCE:
try:
    # Atomic rename (per plan TD-6)
    # On POSIX systems (Linux/macOS), rename is atomic
    # On Windows, rename is atomic if target doesn't exist
    os.rename(temp_file_path, queue_file_path)

    # Success: Queue entry persisted with atomic write + secure permissions
    return {
        "success": True,
        "queue_id": queue_id,
        "error": None
    }

except FileExistsError:
    # Target file already exists (UUID collision - extremely unlikely)
    # Clean up temporary file
    try:
        os.remove(temp_file_path)
    except:
        pass

    return {
        "success": False,
        "queue_id": None,
        "error": f"Queue file already exists: {filename}. Retry with new UUID."
    }
except PermissionError:
    # Clean up temporary file
    try:
        os.remove(temp_file_path)
    except:
        pass

    return {
        "success": False,
        "queue_id": None,
        "error": "Permission denied: Cannot rename queue file. Check filesystem permissions."
    }
except OSError as e:
    # Clean up temporary file
    try:
        os.remove(temp_file_path)
    except:
        pass

    return {
        "success": False,
        "queue_id": None,
        "error": f"Failed to finalize queue file: {str(e)}"
    }
```

**Atomic Rename Properties**:
- POSIX (Linux/macOS): Rename is guaranteed atomic (either succeeds completely or fails)
- Windows: Rename is atomic if target doesn't exist (collision unlikely due to UUID)
- If rename fails, temporary file remains (no data loss, can be manually recovered)
- If rename succeeds, queue entry is durable and ready for retry

<!-- EXAMPLE SCENARIOS: Queue Writer Use Cases (for documentation only) -->
**Example Scenarios**:

**Scenario 1: Successful Queueing** (Happy Path)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Input
feedback_data = {
    "feedback_type": "bug",
    "title": "Test execution timeout after 5 minutes",
    "description": "Tests fail with timeout...",
    "diagnostics": {
        "command_history": [...],
        "environment": {...},
        "errors": [...],
        "project_context": {...}
    },
    "sanitized": True,
    "created_at": "2026-01-16T15:30:45Z"
}
error_message = "Network connection error. Check internet connection and retry."

# Execution
# 1. Create directory: .claude/.feedback-queue/ (if missing)
os.makedirs(".claude/.feedback-queue/", mode=0o700, exist_ok=True)

# 2. Generate filename
timestamp = "20260116T153045"  # 2026-01-16 15:30:45 UTC
short_uuid = "a3f8d9c2"
filename = "feedback-20260116T153045-a3f8d9c2.json"
queue_id = "feedback-20260116T153045-a3f8d9c2"

# 3. Construct queue entry
queue_entry = {
    "feedback_data": feedback_data,
    "submission_metadata": {
        "attempt_count": 0,
        "max_retries": 5,
        "last_attempted": None,
        "abandoned": False,
        "queued_at": "2026-01-16T15:30:45Z"
    },
    "queue_id": queue_id
}

# 4. Write to temp file: .claude/.feedback-queue/.tmp-a3f8d9c2.json
with open(".claude/.feedback-queue/.tmp-a3f8d9c2.json", 'w') as f:
    json.dump(queue_entry, f, indent=2)

# 5. Set permissions: 0o600 (rw-------)
os.chmod(".claude/.feedback-queue/.tmp-a3f8d9c2.json", 0o600)

# 6. Atomic rename
os.rename(".claude/.feedback-queue/.tmp-a3f8d9c2.json",
          ".claude/.feedback-queue/feedback-20260116T153045-a3f8d9c2.json")

# Output
{
    "success": True,
    "queue_id": "feedback-20260116T153045-a3f8d9c2",
    "error": None
}
```

**Result**: Queue file created at `.claude/.feedback-queue/feedback-20260116T153045-a3f8d9c2.json`

**Scenario 2: Directory Creation** (First-Time Queueing)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Precondition: .claude/.feedback-queue/ does not exist

# Execution
# 1. Check directory existence
if not os.path.exists(".claude/.feedback-queue/"):
    # Create directory with secure permissions
    os.makedirs(".claude/.feedback-queue/", mode=0o700, exist_ok=True)

# 2-6. (Same as Scenario 1)

# Output
{
    "success": True,
    "queue_id": "feedback-20260116T153100-b4e9f0d3",
    "error": None
}
```

**Result**: Directory created, queue file persisted successfully

**Scenario 3: Permission Error** (Filesystem Restrictions)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Precondition: .claude/ directory is read-only (no write permission)

# Execution
# 1. Attempt to create directory
os.makedirs(".claude/.feedback-queue/", mode=0o700, exist_ok=True)
# Raises: PermissionError

# Output
{
    "success": False,
    "queue_id": None,
    "error": "Permission denied: Cannot create queue directory. Check filesystem permissions."
}
```

**Result**: Queueing failed, user notified of permission issue

**Scenario 4: Disk Full** (No Space Available)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Precondition: Filesystem is full (no space for new files)

# Execution
# 1-3. (Directory exists, filename generated, queue entry constructed)
# 4. Attempt to write temporary file
with open(".claude/.feedback-queue/.tmp-c5f1a2e4.json", 'w') as f:
    json.dump(queue_entry, f, indent=2)
# Raises: OSError (No space left on device)

# Output
{
    "success": False,
    "queue_id": None,
    "error": "Failed to write queue file: [Errno 28] No space left on device"
}
```

**Result**: Queueing failed, user notified of disk space issue

**Scenario 5: UUID Collision** (Extremely Unlikely)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Precondition: File "feedback-20260116T153045-a3f8d9c2.json" already exists

# Execution
# 1-5. (Directory exists, temp file written and permissions set)
# 6. Attempt atomic rename
os.rename(".claude/.feedback-queue/.tmp-a3f8d9c2.json",
          ".claude/.feedback-queue/feedback-20260116T153045-a3f8d9c2.json")
# Raises: FileExistsError (target already exists)

# Cleanup: Remove temporary file
os.remove(".claude/.feedback-queue/.tmp-a3f8d9c2.json")

# Output
{
    "success": False,
    "queue_id": None,
    "error": "Queue file already exists: feedback-20260116T153045-a3f8d9c2.json. Retry with new UUID."
}
```

**Result**: Collision detected, temporary file cleaned up, user can retry (new UUID will be generated)

**Scenario 6: Concurrent Writes** (Multiple Feedback Submissions)

```text
EXAMPLE SCENARIO (for documentation only - not executable code):
# Precondition: Two feedback submissions happen simultaneously

# Thread 1:
timestamp1 = "20260116T153045"
uuid1 = "a3f8d9c2"  # Random UUID
filename1 = "feedback-20260116T153045-a3f8d9c2.json"

# Thread 2 (same millisecond):
timestamp2 = "20260116T153045"  # Same timestamp (within 1-second granularity)
uuid2 = "d6g2b3f5"  # Different UUID (collision probability: ~1 in 4 billion)
filename2 = "feedback-20260116T153045-d6g2b3f5.json"

# Result: Both files created successfully (no collision due to different UUIDs)
```

**Result**: Atomic write pattern + UUID suffix prevents corruption from concurrent writes

<!-- SECURITY DOCUMENTATION: Example scenario showing atomic write protection -->
**Scenario 7: Process Crash During Write** (Atomic Write Protection)
> **Security Note**: This pseudo-code demonstrates how atomic writes prevent queue corruption. The actual implementation uses secure file operations with proper error handling and timeout protection.

```text
EXAMPLE SCENARIO (for documentation only - not executable code):

# Execution flow demonstration:
# 1-4. Writing to temporary file
with open(".claude/.feedback-queue/.tmp-e7h3c4g6.json", 'w') as f:
    json.dump(queue_entry, f, indent=2)
    # Process crashes here (power failure, system crash, etc.)

# Filesystem state after crash:
# - Temporary file: .tmp-e7h3c4g6.json (partial or complete, but NOT final filename)
# - Final file: Does NOT exist (rename never executed)

# Result: No corruption of queue (final file only appears after successful rename)
# Recovery: Orphaned temp files can be detected and cleaned up (.tmp-* pattern)
```

**Result**: Atomic write pattern prevents corruption (final file only appears if write succeeds)

**Integration with Workflow**:

```python
# In Phase 6: Submission or Queueing
# After IssueSubmitter returns failure due to network error

submission_result = submit_issue(title, body, labels)

if not submission_result["success"]:
    # Check if error is network-related (should queue)
    if is_network_error(submission_result["error"]):
        # Queue feedback for automatic retry
        queue_result = write_to_queue(feedback_data, submission_result["error"])

        if queue_result["success"]:
            # Display queue notification
            print(f"""
Network unavailable. Feedback queued for submission when online.

Queue ID: {queue_result["queue_id"]}

Your feedback will be automatically submitted when:
- Network connection is restored
- You run any plugin command

To manually retry: /feedback --retry
To view queue: /feedback --list-queue
            """)
        else:
            # Queueing failed (disk full, permission error, etc.)
            # Fallback to clipboard as last resort
            print(f"""
WARNING: Failed to queue feedback locally: {queue_result["error"]}

Falling back to clipboard copy...
            """)
            clipboard_result = copy_to_clipboard(formatted_issue, manual_url)
            display_clipboard_fallback_message(clipboard_result)
    else:
        # Auth error or other non-network issue → Fallback to clipboard
        clipboard_result = copy_to_clipboard(formatted_issue, manual_url)
        display_fallback_message(submission_result["error"], clipboard_result)
```

**Security Requirements** (per SECURITY.md):

1. **Directory Creation**:
   - Directory path: `.claude/.feedback-queue/` (hardcoded, no user input)
   - Permissions: 0o700 (user-only rwx, prevents access by other users)
   - Workspace boundary: Within `.claude/` directory (plugin state directory)

2. **File Creation**:
   - Filename generation: Timestamp + UUID (no user input in filename)
   - Permissions: 0o600 (user-only rw, prevents reading by other users)
   - Atomic write: Prevents corruption from concurrent writes or process crashes

3. **Path Validation**:
   - All paths constructed with `os.path.join()` (prevents path traversal)
   - No user input in path components (timestamp/UUID are sanitized by format)
   - Directory checked with `os.path.exists()` before creation

4. **Input Validation**:
   - `feedback_data`: Already validated and sanitized before QueueWriter called
   - `error_message`: Optional string (used only for logging, not in critical path)
   - No user-controlled data in filesystem operations

**Performance**:

- **Best case** (directory exists, no errors): ~10-50 ms
  - JSON serialization: ~5-10 ms (typical feedback size: 10-50 KB)
  - File write: ~5-20 ms (SSD) or ~20-50 ms (HDD)
  - chmod: ~1-5 ms
  - rename: ~1-5 ms (atomic operation, very fast)

- **Worst case** (directory creation): ~50-100 ms
  - Directory creation: +10-20 ms
  - Rest same as best case

- **Error cases** (permission denied, disk full): ~5-10 ms
  - Fast failure (no retry logic in QueueWriter)

**Performance Compliance** (per spec REQ-NF-2):
- QueueWriter execution time: < 100 ms (negligible impact on 30-second workflow budget)
- Non-blocking: Queue write happens synchronously but quickly (< 100 ms)
- Total workflow with queueing: ~24 seconds (within spec target)

**Edge Cases Handled**:

- **Directory missing**: Created with secure permissions (0o700)
- **Permission denied**: Graceful error, fallback to clipboard
- **Disk full**: Graceful error, notify user
- **UUID collision**: Detected via FileExistsError, cleanup temporary file
- **Concurrent writes**: UUID prevents filename collisions
- **Process crash during write**: Atomic write pattern prevents corruption
- **Invalid characters in filename**: Timestamp/UUID formats are filesystem-safe
- **Very large feedback data**: JSON serialization handles arbitrary size (no size limit in QueueWriter)
- **Unicode in feedback**: UTF-8 encoding supports all Unicode characters
- **Filesystem case sensitivity**: Filenames use lowercase (case-insensitive safe)
- **Long filenames**: Filename length = 34 chars ("feedback-20260116T153045-a3f8d9c2.json") << filesystem limits (255 chars)

**Error Recovery**:

- **Queueing fails** → Fallback to clipboard (last resort, ensures no data loss)
- **Directory creation fails** → Return error immediately (no partial state)
- **File write fails** → Temporary file cleaned up (no orphaned files)
- **Permission setting fails** → Temporary file cleaned up, return error
- **Rename fails** → Temporary file cleaned up, return error
- **Unexpected error** → Catch-all exception handler, return error with details

**Logging** (for debugging):

All queueing operations logged to `.claude/.feedback-errors.log`:

```python
import logging

def log_queue_operation(operation, queue_id=None, error=None):
    """Log queue operations for debugging (not exposed to user)."""
    log_file = ".claude/.feedback-errors.log"
    timestamp = datetime.datetime.now().isoformat()

    if error:
        log_entry = f"{timestamp} | QUEUE_{operation}_FAILED | queue_id={queue_id} | error={error}\n"
    else:
        log_entry = f"{timestamp} | QUEUE_{operation}_SUCCESS | queue_id={queue_id}\n"

    # Append to log file (create if missing)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except:
        pass  # Ignore logging errors (don't fail operation due to logging)
```

**Trade-offs**:

- **JSON vs. Binary format**: JSON chosen for human readability (users can inspect queue files)
  - Alternative: Pickle/MessagePack - Rejected (not human-readable, harder to debug)

- **Atomic write pattern**: Adds complexity (temp file + rename) for reliability
  - Alternative: Direct write - Rejected (risk of corruption from crashes)

- **Short UUID (8 chars)**: Balances uniqueness vs. filename length
  - Alternative: Full UUID (36 chars) - Rejected (longer filenames, 8 chars sufficient)
  - Alternative: No UUID (timestamp only) - Rejected (collisions if multiple submissions in same second)

- **File permissions (0o600)**: Maximizes security, may prevent legitimate access
  - Alternative: 0o644 (world-readable) - Rejected (violates SECURITY.md, exposes sensitive diagnostics)

**Future Enhancements**:

- **Queue size limit**: Prevent unbounded queue growth (e.g., max 100 items, oldest deleted)
- **Queue expiration**: Auto-delete queued items older than 30 days
- **Compression**: Compress large feedback data (e.g., gzip JSON for >100 KB payloads)
- **Queue statistics**: Track queue size, oldest item, success/failure rates
- **Orphaned temp file cleanup**: Periodic scan for `.tmp-*.json` files and cleanup

---

**Submission Path A: GitHub CLI Available**

If gh CLI installed AND authenticated:

1. **Format Issue Body**:
   ```markdown
   ## Description

   {user_description}

   ---

   ## Diagnostic Information

   ### Command History
   {command_history}

   ### Environment
   {environment}

   ### Recent Errors
   {errors}

   ### Project Context
   {project_context}

   ---
   *Submitted via `/feedback` command*
   ```

2. **Construct gh Command** (SECURITY: per plan TD-5):
   - Use array form: `["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body, "--label", labels_string]`
   - Repository (hardcoded per plan TD-9): `github.example.com/my-org/my-plugin`
   - Labels: Use labels_string from Phase 1 Step 4 (comma-separated format, e.g., "bug,needs-triage")
   - Set shell=False
   - Set 30-second timeout

3. **Execute Submission**:
   - Run subprocess with security requirements
   - Capture stdout to extract issue URL
   - Parse exit code:
     - 0: Success, extract URL from stdout
     - 1: Auth error → fallback to clipboard
     - Network errors → queue locally

4. **On Success**:
   ```markdown
   Feedback submitted successfully!

   Issue created: {issue_url}

   Thank you for your feedback! Maintainers will review it soon.
   ```

**Submission Path B: GitHub CLI Unavailable** (Clipboard Fallback per plan TD-5)

If gh CLI not installed OR not authenticated:

1. **Display Error**:
   ```markdown
   GitHub CLI (gh) is not available or not authenticated.

   Installation:
   - Download: https://cli.github.com/
   - Authenticate: gh auth login

   Fallback: Copying formatted issue to clipboard...
   ```

2. **Copy to Clipboard** (per plan clipboard integration):
   - Detect OS platform (Windows/macOS/Linux)
   - Use platform-specific command:
     - Windows: `["clip"]` (stdin: formatted issue)
     - macOS: `["pbcopy"]` (stdin: formatted issue)
     - Linux: `["xclip", "-selection", "clipboard"]` (stdin: formatted issue)
   - Security: shell=False, user data in stdin (NOT arguments)
   - 5-second timeout

3. **Display Manual URL**:
   ```markdown
   Formatted issue copied to clipboard!

   To submit manually:
   1. Visit: https://github.example.com/my-org/my-plugin/issues/new
   2. Paste the clipboard content as issue body
   3. Click "Submit new issue"
   ```

4. **If Clipboard Fails**:
   - Display formatted issue text directly in output
   - Provide manual URL
   - User copies text manually

**Submission Path C: Network Unavailable** (Queueing per plan TD-6)

If gh CLI submission fails with network error (timeout, connection refused):

1. **Queue Feedback Locally**:
   - Create `.claude/.feedback-queue/` directory if missing
   - Generate filename: `feedback-{timestamp}-{uuid}.json`
     - Timestamp: ISO format (YYYYMMDDTHHMMSS)
     - UUID: random unique identifier
   - Write JSON file with schema:
     ```json
     {
       "feedback_data": {
         "feedback_type": "bug",
         "title": "...",
         "description": "...",
         "diagnostics": {
           "command_history": [...],
           "environment": {...},
           "errors": [...],
           "project_context": {...}
         },
         "sanitized": true,
         "created_at": "2026-01-16T15:30:00Z"
       },
       "submission_metadata": {
         "attempt_count": 0,
         "max_retries": 5,
         "last_attempted": null,
         "abandoned": false,
         "queued_at": "2026-01-16T15:30:00Z"
       },
       "queue_id": "feedback-20260116T153000-a3f8d9c2"
     }
     ```
   - Use atomic write (temp file + rename) per plan TD-6
   - Set file permissions to user-only (0o600)

2. **Display Queue Notification**:
   ```markdown
   Network unavailable. Feedback queued for submission when online.

   Queue ID: {queue_id}

   Your feedback will be automatically submitted when:
   - Network connection is restored
   - You run any plugin command

   To manually retry: /feedback --retry
   To view queue: /feedback --list-queue
   ```

---

### Step 3: Quick Mode Workflow

**Quick Mode** (`/feedback --quick <description>`):

This is a streamlined workflow for fast bug reporting.

**Extract Description**:
- Parse description from command argument
- Validate: 10-500 characters

**Auto-Configure**:
- feedback_type = "bug" (Bug Report)
- Apply label mapping from Phase 1: labels_string = "bug,needs-triage"
- title = first 100 chars of description (or first sentence if shorter)
- description = full provided description

**Collect Diagnostics**:
- Same as Phase 3 (all 4 collectors)

**Apply Sanitization**:
- Same as Phase 4 (4-stage pipeline)

**Show Abbreviated Preview**:
```markdown
## Quick Bug Report Preview

**Title**: {title}
**Type**: Bug Report

### Description
{description}

### Diagnostics (First 5 lines per category)

**Command History**: {first_5_commands}
**Environment**: {environment_summary}
**Recent Errors**: {first_5_errors}
**Project Context**: {context_summary}

[Full diagnostics will be included in submission]

---
```

**Single Approval Gate**:
Use AskUserQuestion:
```markdown
Submit this bug report to GitHub?

Options:
1. Submit - Send to GitHub now
2. Cancel - Abandon submission
```

**On Submit**:
- Execute Phase 6 (Submission or Queueing) with same logic as interactive mode

---

### Step 4: Retry Queue Workflow

**Retry Mode** (`/feedback --retry`):

This workflow manually retries all queued feedback submissions.

**Display Start**:
```markdown
## Retrying Queued Feedback

Scanning queue directory: .claude/.feedback-queue/
```

**Scan Queue**:
1. Check if `.claude/.feedback-queue/` exists
2. List all `*.json` files
3. Load each file, parse JSON
4. Sort by queued_at timestamp (oldest first)

**If Queue Empty**:
```markdown
No queued feedback items found.

All feedback has been submitted!
```

**Retry Each Item**:
For each queued item (including abandoned items - this is manual retry mode):

**IMPORTANT**: Process ALL queued items, ignoring the abandoned flag. Manual retry overrides automatic retry restrictions.

1. **Check gh CLI availability** (same as Phase 6)
2. **Attempt submission**:
   - Extract feedback_data and format issue body
   - Execute gh CLI command (same security requirements)
   - 30-second timeout
3. **On Success**:
   - Delete queue file
   - Track success: `{queue_id, issue_url}`
4. **On Failure**:
   - Increment attempt_count
   - Update last_attempted timestamp
   - If attempt_count >= max_retries (5): set abandoned = true
   - Write updated JSON back to file
   - Track failure: `{queue_id, attempts}`

**Display Results**:
```markdown
## Retry Results

✅ Submitted: {success_count} items, ❌ Failed: {failure_count} items

{if success_count > 0}
### Successfully Submitted
{for each success}
- {queue_id}: Issue #{issue_number} ({issue_url})

{if failure_count > 0}
### Failed Submissions
{for each failure}
- {queue_id}: {attempts} attempts (max 5)

{if any abandoned}
### Abandoned Items (Max Retries Reached)
{for each abandoned}
- {queue_id}: Manual intervention may be required

{if all succeeded}
All queued feedback submitted successfully!
```

**IMPORTANT**: After displaying results, STOP execution. Do NOT continue to interactive workflow. This subcommand exits immediately after completion.

---

### Step 5: List Queue Workflow

**List Queue Mode** (`/feedback --list-queue`):

This workflow displays all queued feedback items.

**Display Header**:
```markdown
## Queued Feedback Items

Queue directory: .claude/.feedback-queue/
```

**Scan Queue**:
1. Check if `.claude/.feedback-queue/` exists
2. List all `*.json` files
3. Load each file, parse JSON
4. Sort by queued_at timestamp (newest first)

**If Queue Empty**:
```markdown
No queued feedback items.

All feedback has been submitted!
```

**Display Summary**:
```markdown
Total items: {total_count}
- Pending: {pending_count} (< 5 retry attempts)
- Abandoned: {abandoned_count} (>= 5 retry attempts)

---
```

**Display Items**:
```markdown
### Pending Items

1. **{feedback_type}**: {title}
   - Queue ID: {queue_id}
   - Queued: {queued_at}
   - Attempts: {attempt_count} / 5
   - Last Attempted: {last_attempted or 'Never'}

2. **{feedback_type}**: {title}
   ...

{if abandoned_count > 0}
### Abandoned Items (Manual Retry Required)

1. **{feedback_type}**: {title}
   - Queue ID: {queue_id}
   - Queued: {queued_at}
   - Attempts: 5 / 5 (max retries exceeded)
   - Last Attempted: {last_attempted}

---

### Next Steps

To retry all items (including abandoned):
  /feedback --retry

To submit new feedback:
  /feedback
```

**IMPORTANT**: After displaying queue items, STOP execution. Do NOT continue to interactive workflow. This subcommand exits immediately after completion.

---

### Step 6: Queue Notification Renderer (TASK-013)

**Notification Renderer Algorithm**:

This algorithm displays queue status notifications at command completion when automatic queue retry occurs. Per REQ-NF-9, notifications must be non-intrusive (single-line, no user acknowledgment required).

**When to Display**:
- ONLY display if automatic queue retry occurred during command execution
- Do NOT display on every command invocation
- Do NOT display if no queue items were processed

**Input Format** (from AutoRetry/TASK-012):
```python
{
  "submitted": [
    {"queue_id": "feedback-20260116T153000-a3f8d9c2", "issue_url": "https://github.example.com/my-org/my-plugin/issues/42"}
  ],
  "failed": [
    {"queue_id": "feedback-20260116T160000-b4e9f8d3", "attempts": 3}
  ]
}
```

**Notification Display Logic**:

1. **Check if any retry occurred**:
   ```python
   if len(submitted) == 0 and len(failed) == 0:
       return  # No notification needed
   ```

2. **Success Notification** (if any submitted successfully):
   ```markdown

   ✅ Queued feedback submitted successfully: issue #{issue_number} → {issue_url}
   ```

   **Format Details**:
   - Extract issue number from URL using regex: `issues/(\d+)`
   - Single line for issue reference
   - Second line for URL (clickable link)
   - Green checkmark emoji for visual success indicator

   **Example**:
   ```markdown

   ✅ Queued feedback submitted successfully: issue #42 → https://github.example.com/my-org/my-plugin/issues/42
   ```

   **Multiple Successes**:
   If multiple items submitted, display count:
   ```markdown

   ✅ {count} queued feedback items submitted successfully:
      - Issue #42 → https://github.example.com/my-org/my-plugin/issues/42
      - Issue #43 → https://github.example.com/my-org/my-plugin/issues/43
   ```

3. **Failure Notification** (if items still queued):
   ```markdown

   ⏸️ {count} feedback item(s) queued, will retry when online
   ```

   **Format Details**:
   - Single line, no details about attempt counts (keep non-intrusive)
   - Pause emoji for visual "waiting" indicator
   - Plural handling: "1 feedback item" vs "2 feedback items"

   **Example**:
   ```markdown

   ⏸️ 1 feedback item queued, will retry when online
   ```

4. **Mixed Results** (both successes and failures):
   Display success notification first, then failure notification:
   ```markdown

   ✅ Queued feedback submitted successfully: issue #42 → https://github.example.com/my-org/my-plugin/issues/42
   ⏸️ 1 feedback item queued, will retry when online
   ```

**Display Location**:
- Appears AFTER main command output
- Appears BEFORE returning control to user
- Separated by blank line from command output for readability

**Non-Intrusive Requirements** (REQ-NF-9):
- Maximum 2 lines per notification (1 line for reference + 1 line for URL)
- If multiple successes: maximum 5 lines total (summary + up to 4 items, then "...and N more")
- No user acknowledgment required (no "Press Enter to continue")
- No blocking dialogs or prompts
- No sound or visual alerts beyond text

**Security Considerations**:
- URLs are trusted (come from gh CLI response, not user input)
- Queue IDs are internal (generated by system, not displayed to user in notifications)
- No sensitive data in notifications (only issue numbers and URLs)

<!-- EXAMPLE OUTPUT SCENARIOS (for documentation only - not executable code) -->
**Example Scenarios**:

**Scenario 1: Single Success**
```text
EXAMPLE USER-FACING OUTPUT:
[Main command output...]

✅ Queued feedback submitted successfully: issue #42 → https://github.example.com/my-org/my-plugin/issues/42
```

**Scenario 2: Single Failure**
```text
EXAMPLE USER-FACING OUTPUT:
[Main command output...]

⏸️ 1 feedback item queued, will retry when online
```

**Scenario 3: Multiple Successes**
```text
EXAMPLE USER-FACING OUTPUT:
[Main command output...]

✅ 3 queued feedback items submitted successfully:
   - Issue #42 → https://github.example.com/my-org/my-plugin/issues/42
   - Issue #43 → https://github.example.com/my-org/my-plugin/issues/43
   - Issue #44 → https://github.example.com/my-org/my-plugin/issues/44
```

**Scenario 4: Mixed Results**
```text
EXAMPLE USER-FACING OUTPUT:
[Main command output...]

✅ 2 queued feedback items submitted successfully:
   - Issue #42 → https://github.example.com/my-org/my-plugin/issues/42
   - Issue #43 → https://github.example.com/my-org/my-plugin/issues/43
⏸️ 1 feedback item queued, will retry when online
```

**Scenario 5: No Retry Occurred**
```
[Main command output...]
```
(No notification displayed)

**Implementation Notes**:

1. **URL Parsing**:
   ```python
   issue_number = re.search(r'issues/(\d+)', issue_url).group(1)
   ```
   Fallback: If regex fails, display full URL without issue number

2. **Plural Handling**:
   ```python
   count_text = f"{count} feedback item" if count == 1 else f"{count} feedback items"
   ```

3. **Multiple Items Truncation**:
   ```python
   if len(submitted) > 4:
       # Display first 4 items
       # Add "...and {remaining} more"
   ```

4. **Integration with Other Commands**:
   When automatic retry is integrated into all plugin commands (future task), each command will:
   - Check for queued items at startup (background, non-blocking)
   - Attempt submission via AutoRetry (TASK-012)
   - Call NotificationRenderer with results before command completion
   - Display notification after command output

**Testing Checklist**:
- [ ] Single success: displays "✅ Queued feedback submitted successfully: issue #42 → [URL]"
- [ ] Single failure: displays "⏸️ 1 feedback item queued, will retry when online"
- [ ] Multiple successes: displays count and list (up to 4 items)
- [ ] Mixed results: displays both success and failure notifications
- [ ] No retry occurred: displays nothing
- [ ] Non-blocking: notification does not require user input
- [ ] Format: single line (2 lines if URL), non-intrusive per REQ-NF-9
- [ ] Issue number extraction: correctly parses from GitHub URL
- [ ] Plural handling: "1 item" vs "2 items"

---

## Error Handling

### Invalid Arguments
```markdown
Error: Invalid argument

The /feedback command accepts:
- No arguments (interactive mode)
- --quick <description> (quick bug report)
- --retry (retry queued submissions)
- --list-queue (show queue)
- --help (show help)

Example: /feedback --quick "Test execution timeout"
```

### Validation Errors (Title/Description)
```markdown
Error: Invalid title

Title must be 10-100 characters.
You provided: {length} characters

Please enter a title between 10 and 100 characters.
```

```markdown
Error: Invalid description

Description must be 20-5000 characters.
You provided: {length} characters

Please enter a description between 20 and 5000 characters.
```

### GitHub CLI Errors
```markdown
Error: GitHub CLI authentication failed

The gh CLI is installed but not authenticated.

To authenticate:
1. Run: gh auth login
2. Follow the authentication prompts
3. Retry: /feedback --retry

Alternatively, feedback has been queued and will auto-retry when gh is authenticated.
```

### Network Errors
```markdown
Network error during submission

Your feedback has been saved locally and will be automatically submitted when:
- Network connection is restored
- You run any plugin command

Queue ID: {queue_id}

To manually retry: /feedback --retry
```

### Diagnostic Collection Errors
```markdown
Warning: Partial diagnostic collection

Some diagnostic information could not be collected:
- {error_description}

Feedback will be submitted with available diagnostics.

Continue? (Yes/No)
```

### Queue Write Errors
```markdown
Error: Failed to save feedback to queue

Unable to write to .claude/.feedback-queue/

Possible causes:
- Insufficient disk space
- Permission errors
- Workspace not writable

Your feedback has NOT been saved. Please try again or submit manually.
```

---

## Help Text

When user runs `/feedback --help` or `/feedback -h`:

```
/feedback - Submit feedback to dante_plugin GitHub repository

USAGE:
  /feedback [options]

OPTIONS:
  --quick <description>    Quick bug report with brief description
  --retry                  Retry all queued feedback submissions
  --list-queue            Show all queued feedback items
  --help, -h              Show this help message

MODES:

  Interactive Mode (default):
    Full 6-phase workflow with review gate
    - Select feedback type (bug, feature, question, feedback)
    - Enter title (10-100 chars) and description (20-5000 chars)
    - Automatic diagnostic collection
    - Review and edit diagnostics before submission
    - Submit to GitHub or queue if offline

  Quick Mode (--quick):
    Streamlined bug report workflow
    - Auto-defaults to "Bug Report" type
    - Uses provided description as title/description
    - Abbreviated preview (first 5 lines per category)
    - Single approval gate
    - Target completion: < 15 seconds

  Retry Mode (--retry):
    Manual retry of queued submissions
    - Retries all queued feedback (ignores abandoned flag)
    - Displays results summary

  List Queue Mode (--list-queue):
    View queued feedback items
    - Shows all queued items with metadata
    - Displays queue statistics

EXAMPLES:
  /feedback                                    # Interactive mode
  /feedback --quick "Tests fail on Windows"    # Quick bug report
  /feedback --retry                            # Retry queue
  /feedback --list-queue                       # Show queue

DIAGNOSTIC INFORMATION:
  Automatically collected and sanitized:
  - Command history (last 20 plugin commands)
  - Plugin version and environment (OS, language versions)
  - Recent errors (last 10 or 24 hours)
  - Project context (language, framework, test counts)

PRIVACY & SECURITY:
  - All data sanitized (removes PII, credentials, IP addresses)
  - User review gate before submission
  - Edit or remove any diagnostic data
  - No source code included

GITHUB INTEGRATION:
  - Primary: GitHub CLI (gh) - preferred method
  - Fallback: Clipboard copy + manual submission URL
  - Offline: Local queue with automatic retry

REPOSITORY:
  github.example.com/my-org/my-plugin

SEE ALSO:
  GitHub CLI: https://cli.github.com/
  Plugin repository: https://github.example.com/my-org/my-plugin
```

---

## Security Requirements (CRITICAL)

**All implementations MUST follow SECURITY.md**:

1. **Input Validation**:
   - Remove null bytes from all user inputs
   - Validate title length (10-100 chars)
   - Validate description length (20-5000 chars)
   - Check argument whitelisting

2. **Subprocess Execution**:
   - Use array form (NOT string)
   - Set shell=False (prevent command injection)
   - Set timeouts (2s for detection, 30s for submission)
   - Validate all arguments
   - Never put user input in command position

3. **File Operations**:
   - Validate paths within workspace boundaries
   - Use atomic writes for queue (temp + rename)
   - Set proper file permissions (0o600 for queue)
   - Prevent path traversal

4. **PII Sanitization**:
   - Apply 4-stage sanitization pipeline to ALL diagnostics
   - Remove usernames from paths
   - Redact credentials (api_key, token, password, secret)
   - Remove IP addresses (exclude allowlist)
   - Strip hostnames

5. **Error Handling**:
   - Never expose system internals in error messages
   - Log errors to `.claude/.feedback-errors.log` (not shown to user)
   - Graceful degradation (queue if submission fails)

---

## Implementation Notes

### 1. State Persistence

Queue files enable:
- Offline submission capability
- Automatic retry on next command invocation
- Manual retry via `/feedback --retry`
- Persistent feedback even if Claude Code crashes

### 2. GitHub Repository Hardcoded

Per plan TD-9, repository is hardcoded:
- Value: `github.example.com/my-org/my-plugin`
- Prevents feedback routing to wrong repositories
- Security measure (no arbitrary repo submissions)

### 3. Label Mapping

Per plan TD-8, hardcoded mapping:
- Bug Report → bug, needs-triage
- Feature Request → enhancement, needs-review
- Question/Help → question
- General Feedback → feedback

### 4. Diagnostic Collection Performance

Target: < 10 seconds (per plan REQ-NF-1)
- Collectors run sequentially (not parallel)
- Timeouts on subprocess calls (2s for version detection)
- Caching NOT implemented in v1.0 (future optimization)

### 5. Sanitization Performance

Target: < 2 seconds (per plan TD-4)
- Regex-based pipeline (deterministic, fast)
- Sequential stages (clear separation of concerns)
- No LLM calls (latency, cost, reliability concerns)

### 6. Queue Retry Behavior

Automatic retry (per plan TD-6):
- Triggered on any plugin command start (NOT implemented in this task)
- Background submission (non-blocking)
- Max 5 retry attempts
- Exponential backoff NOT implemented (simple retry)

Note: Automatic retry integration requires modification of ALL command files to check queue at startup. Algorithm implementations for QueueReader and AutoRetry are provided below (TASK-012).

<!-- DOCUMENTATION SECTION: Implementation Reference (Not Executable Code) -->
**QueueReader Algorithm** (TASK-012):
> **Note**: The following is implementation documentation and pseudo-code examples for reference. This is NOT executable code - it describes the algorithm that should be implemented when integrating queue checking.

**Purpose**: Scan `.claude/.feedback-queue/` directory on any plugin command invocation, load queued feedback items, and return sorted list for automatic retry processing.

**Input**: None (reads from `.claude/.feedback-queue/` directory)

**Output**: <!-- Example schema - not executable code -->
```text
EXAMPLE OUTPUT SCHEMA (for documentation only):
[
    {
        "queue_id": str,              # Filename without .json extension
        "file_path": str,             # Absolute path to queue file
        "feedback_data": dict,        # User-approved feedback data
        "submission_metadata": {
            "attempt_count": int,     # Current retry attempts (0-5)
            "max_retries": int,       # Always 5
            "last_attempted": str | None,  # ISO timestamp of last attempt
            "abandoned": bool,        # True if attempt_count >= max_retries
            "queued_at": str         # ISO timestamp when first queued
        }
    },
    ...
]
# Sorted by queued_at timestamp (oldest first) for FIFO retry order
```

**Algorithm** (4 steps per plan TD-6):

**Step 1: Check Queue Directory Existence**

Verify that the queue directory exists before scanning:

```python
import os

queue_dir = os.path.join(".claude", ".feedback-queue")

# Check if directory exists
if not os.path.exists(queue_dir):
    # No queue directory means no queued items
    return []

if not os.path.isdir(queue_dir):
    # Path exists but is not a directory (corrupted state)
    # Log error and return empty list (graceful degradation)
    return []
```

**Security Compliance** (per SECURITY.md):
- ✅ Directory path constructed with `os.path.join()` (prevents path traversal)
- ✅ Queue directory is hardcoded within workspace (`.claude/.feedback-queue/`)
- ✅ No user input in path construction

**Step 2: Scan Directory for JSON Files**

List all `.json` files in queue directory using safe glob pattern:

```python
import glob

# Scan for all JSON files in queue directory
# Pattern: .claude/.feedback-queue/*.json
queue_pattern = os.path.join(queue_dir, "*.json")
queue_files = glob.glob(queue_pattern)

# If no files found, return empty list
if not queue_files:
    return []
```

**Security Compliance**:
- ✅ Uses `glob.glob()` with hardcoded pattern (no command injection)
- ✅ Pattern restricts to `.json` files only (prevents reading arbitrary files)
- ✅ No user input in glob pattern

**Step 3: Load and Parse Queue Files**

For each JSON file, load contents and parse metadata:

```python
import json

queue_entries = []

for file_path in queue_files:
    try:
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            queue_data = json.load(f)

        # Extract queue_id from filename (without .json extension)
        queue_id = os.path.basename(file_path).replace('.json', '')

        # Build queue entry structure
        queue_entry = {
            "queue_id": queue_id,
            "file_path": file_path,
            "feedback_data": queue_data.get("feedback_data", {}),
            "submission_metadata": queue_data.get("submission_metadata", {
                "attempt_count": 0,
                "max_retries": 5,
                "last_attempted": None,
                "abandoned": False,
                "queued_at": queue_data.get("submission_metadata", {}).get("queued_at", "")
            })
        }

        queue_entries.append(queue_entry)

    except json.JSONDecodeError:
        # Corrupted JSON file - skip this entry
        # Log error to .claude/.feedback-errors.log
        continue

    except FileNotFoundError:
        # File deleted between glob scan and read (race condition)
        # Skip this entry (graceful degradation)
        continue

    except PermissionError:
        # Permission denied reading file
        # Skip this entry (graceful degradation)
        continue

    except Exception as e:
        # Generic error reading file
        # Skip this entry and continue processing queue
        continue
```

**Error Handling**:
- **Corrupted JSON** → Skip file, continue processing queue (graceful degradation)
- **Missing file** → Skip (race condition between glob and read)
- **Permission error** → Skip file (log error, continue)
- **Generic errors** → Skip file, log error, continue

**Security Compliance**:
- ✅ JSON parsing with `json.load()` (safe, no code execution)
- ✅ File read with explicit encoding (`utf-8`)
- ✅ Exception handling prevents crash on malformed files

**Step 4: Sort by Timestamp (Oldest First)**

Sort queue entries by `queued_at` timestamp to ensure FIFO retry order:

```python
from datetime import datetime

def parse_timestamp(timestamp_str):
    """
    Parse ISO timestamp string to datetime object.
    Returns epoch (1970-01-01) if parsing fails.
    """
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Invalid timestamp format - use epoch as fallback
        return datetime.fromtimestamp(0)

# Sort by queued_at timestamp (oldest first)
queue_entries.sort(key=lambda entry: parse_timestamp(
    entry["submission_metadata"].get("queued_at", "")
))

return queue_entries
```

**Example Scenarios**:

**Scenario 1: Queue Has 3 Items** (Mixed States)

```python
# Queue directory contains:
# - feedback-20260116T150000-abc123.json (attempt_count: 0, queued 3 hours ago)
# - feedback-20260116T160000-def456.json (attempt_count: 2, queued 2 hours ago)
# - feedback-20260116T170000-ghi789.json (attempt_count: 5, abandoned, queued 1 hour ago)

# QueueReader output (sorted by queued_at, oldest first):
[
    {
        "queue_id": "feedback-20260116T150000-abc123",
        "file_path": ".claude/.feedback-queue/feedback-20260116T150000-abc123.json",
        "feedback_data": {...},
        "submission_metadata": {
            "attempt_count": 0,
            "max_retries": 5,
            "last_attempted": None,
            "abandoned": False,
            "queued_at": "2026-01-16T15:00:00Z"
        }
    },
    {
        "queue_id": "feedback-20260116T160000-def456",
        "file_path": ".claude/.feedback-queue/feedback-20260116T160000-def456.json",
        "feedback_data": {...},
        "submission_metadata": {
            "attempt_count": 2,
            "max_retries": 5,
            "last_attempted": "2026-01-16T17:30:00Z",
            "abandoned": False,
            "queued_at": "2026-01-16T16:00:00Z"
        }
    },
    {
        "queue_id": "feedback-20260116T170000-ghi789",
        "file_path": ".claude/.feedback-queue/feedback-20260116T170000-ghi789.json",
        "feedback_data": {...},
        "submission_metadata": {
            "attempt_count": 5,
            "max_retries": 5,
            "last_attempted": "2026-01-16T18:00:00Z",
            "abandoned": True,
            "queued_at": "2026-01-16T17:00:00Z"
        }
    }
]
```

**Scenario 2: Queue Directory Missing**

```python
# .claude/.feedback-queue/ does not exist

# QueueReader output:
[]  # Empty list (no error)
```

**Scenario 3: Queue Has Corrupted Files**

```python
# Queue directory contains:
# - feedback-20260116T150000-abc123.json (valid JSON)
# - feedback-20260116T160000-def456.json (corrupted: invalid JSON syntax)
# - feedback-20260116T170000-ghi789.json (valid JSON)

# QueueReader output (skips corrupted file):
[
    {
        "queue_id": "feedback-20260116T150000-abc123",
        ...  # Valid entry
    },
    {
        "queue_id": "feedback-20260116T170000-ghi789",
        ...  # Valid entry
    }
]
# Corrupted file def456 is skipped with error logged to .claude/.feedback-errors.log
```

**Scenario 4: Empty Queue Directory**

```python
# .claude/.feedback-queue/ exists but contains no .json files

# QueueReader output:
[]  # Empty list (no queued items)
```

**Edge Cases**:

- **Concurrent access** → File deleted between glob and read: Skip file (FileNotFoundError caught)
- **Orphaned files** → Files with invalid schema: Skip file, log error
- **Timestamp parsing failures** → Use epoch (1970-01-01) as fallback for sorting
- **Permission errors** → Skip file, continue processing queue
- **Non-JSON files in directory** → Ignored by glob pattern (`*.json`)
- **Symbolic links** → Followed by `glob.glob()` (standard behavior)
- **Large queue (100+ items)** → All loaded (no pagination in v1.0, acceptable for manual queue management)

**Performance**:
- **Best case** (empty queue): ~1ms (directory check only)
- **Typical case** (5 items): ~50ms (5 file reads + JSON parsing + sorting)
- **Worst case** (100 items): ~1s (100 file reads + JSON parsing + sorting)
- **Non-blocking**: This scan runs at command start before main execution (acceptable overhead)

**Integration with Workflow**:

QueueReader is called at the START of any plugin command invocation:

```python
# At command start (before main logic):
queue_entries = QueueReader()

if queue_entries:
    # Pass to AutoRetry for background processing
    retry_results = AutoRetry(queue_entries)
    # Results will be displayed by NotificationRenderer (TASK-013) at command end
```

---

**AutoRetry Algorithm** (TASK-012):

**Purpose**: Attempt background submission of queued feedback items via GitHub CLI, updating metadata on success/failure, and marking items as abandoned after 5 failed attempts.

**Input**:
```python
queue_entries: list[dict]  # Output from QueueReader (sorted by queued_at, oldest first)
```

**Output**:
```python
{
    "submitted": [
        {
            "queue_id": str,           # Queue ID of successfully submitted item
            "issue_url": str           # GitHub issue URL
        },
        ...
    ],
    "failed": [
        {
            "queue_id": str,           # Queue ID of failed item
            "attempts": int            # Updated attempt count (1-5)
        },
        ...
    ]
}
```

**Algorithm** (5 steps per plan TD-6):

**Step 1: Filter Eligible Entries for Retry**

Skip abandoned items (attempt_count >= max_retries) unless in manual retry mode:

```python
# For automatic retry (on command start):
# Only retry items with attempt_count < max_retries
eligible_entries = [
    entry for entry in queue_entries
    if entry["submission_metadata"]["attempt_count"] < entry["submission_metadata"]["max_retries"]
]

# For manual retry (/feedback --retry):
# Retry ALL items, including abandoned (ignores abandoned flag)
# eligible_entries = queue_entries  # All items
```

**Step 2: Attempt Submission for Each Entry**

For each eligible queue entry, attempt GitHub CLI submission:

```python
import subprocess
from datetime import datetime

submitted = []
failed = []

for entry in eligible_entries:
    queue_id = entry["queue_id"]
    file_path = entry["file_path"]
    feedback_data = entry["feedback_data"]
    metadata = entry["submission_metadata"]

    # Extract submission parameters from feedback_data
    title = feedback_data.get("title", "")
    description = feedback_data.get("description", "")
    feedback_type = feedback_data.get("feedback_type", "general")
    diagnostics = feedback_data.get("diagnostics", {})

    # Format issue body (same format as Phase 6)
    body = format_issue_body(description, diagnostics)

    # Map feedback type to labels (same as TASK-009)
    labels = map_feedback_type_to_labels(feedback_type)

    # Attempt submission via IssueSubmitter (TASK-008)
    submission_result = IssueSubmitter(title, body, labels)

    # Check submission result
    if submission_result["success"]:
        # SUCCESS: Delete queue file and track result
        try:
            os.remove(file_path)
            submitted.append({
                "queue_id": queue_id,
                "issue_url": submission_result["issue_url"]
            })
        except FileNotFoundError:
            # File already deleted (race condition) - treat as success
            submitted.append({
                "queue_id": queue_id,
                "issue_url": submission_result["issue_url"]
            })
        except PermissionError:
            # Cannot delete file - log error but still count as submitted
            # (GitHub issue created successfully, file cleanup failed)
            submitted.append({
                "queue_id": queue_id,
                "issue_url": submission_result["issue_url"]
            })
    else:
        # FAILURE: Update metadata and write back to file
        handle_submission_failure(entry, file_path, failed)
```

**Step 3: On Success - Delete Queue File**

When submission succeeds, delete the queue file atomically:

```python
def delete_queue_file(file_path):
    """
    Delete queue file after successful submission.
    Handles race conditions and permission errors gracefully.
    """
    try:
        os.remove(file_path)
        return True
    except FileNotFoundError:
        # File already deleted (race condition with another process)
        # Not an error - file cleanup succeeded
        return True
    except PermissionError:
        # Permission denied deleting file
        # Log error to .claude/.feedback-errors.log
        # File remains in queue but GitHub issue was created successfully
        return False
    except Exception as e:
        # Generic error deleting file
        # Log error but don't fail entire retry process
        return False
```

**Step 4: On Failure - Update Metadata**

When submission fails, increment attempt count and update timestamp:

```python
import json
import tempfile

def handle_submission_failure(entry, file_path, failed_list):
    """
    Update queue file metadata after failed submission.
    Increments attempt_count, updates last_attempted, sets abandoned if needed.
    """
    metadata = entry["submission_metadata"]

    # Increment attempt count
    metadata["attempt_count"] += 1

    # Update last_attempted timestamp (ISO format)
    metadata["last_attempted"] = datetime.utcnow().isoformat() + "Z"

    # Mark as abandoned if max retries reached
    if metadata["attempt_count"] >= metadata["max_retries"]:
        metadata["abandoned"] = True

    # Update entry with new metadata
    entry["submission_metadata"] = metadata

    # Write updated entry back to file (atomic write)
    try:
        # Atomic write: temp file + rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=os.path.dirname(file_path),
            suffix='.json',
            prefix='.tmp-'
        )

        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            json.dump(entry, temp_file, indent=2)

        # Atomic rename (overwrites existing file)
        os.replace(temp_path, file_path)

        # Set file permissions to user-only (0o600)
        os.chmod(file_path, 0o600)

        # Track failure for results
        failed_list.append({
            "queue_id": entry["queue_id"],
            "attempts": metadata["attempt_count"]
        })

    except Exception as e:
        # Failed to write updated metadata
        # Log error to .claude/.feedback-errors.log
        # Original file remains unchanged (retry will happen again)
        pass
```

**Security Compliance** (per SECURITY.md):
- ✅ Atomic write using `tempfile.mkstemp()` + `os.replace()` (prevents corruption)
- ✅ File permissions set to `0o600` (user-only read/write)
- ✅ No user input in file paths (all paths from QueueReader)
- ✅ JSON serialization with `json.dump()` (safe, no code injection)

**Step 5: Return Results Structure**

After processing all entries, return summary of submitted and failed items:

```python
return {
    "submitted": submitted,  # [{queue_id, issue_url}, ...]
    "failed": failed        # [{queue_id, attempts}, ...]
}
```

**Example Scenarios**:

**Scenario 1: All Items Submitted Successfully** (Happy Path)

```python
# Input: 2 queue entries (both attempt_count: 0)
queue_entries = [
    {
        "queue_id": "feedback-20260116T150000-abc123",
        "file_path": ".claude/.feedback-queue/feedback-20260116T150000-abc123.json",
        "feedback_data": {"title": "Bug report", ...},
        "submission_metadata": {"attempt_count": 0, "max_retries": 5, ...}
    },
    {
        "queue_id": "feedback-20260116T160000-def456",
        "file_path": ".claude/.feedback-queue/feedback-20260116T160000-def456.json",
        "feedback_data": {"title": "Feature request", ...},
        "submission_metadata": {"attempt_count": 0, "max_retries": 5, ...}
    }
]

# Execution:
# - Both submissions succeed via gh CLI
# - Both queue files deleted

# Output:
{
    "submitted": [
        {
            "queue_id": "feedback-20260116T150000-abc123",
            "issue_url": "https://github.example.com/my-org/my-plugin/issues/42"
        },
        {
            "queue_id": "feedback-20260116T160000-def456",
            "issue_url": "https://github.example.com/my-org/my-plugin/issues/43"
        }
    ],
    "failed": []
}
```

**Scenario 2: Partial Success** (1 Success, 1 Failure)

```python
# Input: 2 queue entries
queue_entries = [
    {
        "queue_id": "feedback-20260116T150000-abc123",
        "submission_metadata": {"attempt_count": 0, ...}
    },
    {
        "queue_id": "feedback-20260116T160000-def456",
        "submission_metadata": {"attempt_count": 3, ...}  # 3 prior attempts
    }
]

# Execution:
# - First submission succeeds → file deleted
# - Second submission fails (network error) → metadata updated (attempt_count: 3 → 4)

# Output:
{
    "submitted": [
        {
            "queue_id": "feedback-20260116T150000-abc123",
            "issue_url": "https://github.example.com/my-org/my-plugin/issues/42"
        }
    ],
    "failed": [
        {
            "queue_id": "feedback-20260116T160000-def456",
            "attempts": 4  # Updated count
        }
    ]
}

# File system state after:
# - feedback-20260116T150000-abc123.json → DELETED
# - feedback-20260116T160000-def456.json → Updated with attempt_count: 4
```

**Scenario 3: Item Reaches Abandoned State**

```python
# Input: 1 queue entry with 4 prior attempts
queue_entries = [
    {
        "queue_id": "feedback-20260116T150000-abc123",
        "submission_metadata": {
            "attempt_count": 4,
            "max_retries": 5,
            "abandoned": False
        }
    }
]

# Execution:
# - Submission fails (network error)
# - attempt_count incremented: 4 → 5
# - abandoned flag set to True (attempt_count >= max_retries)

# Output:
{
    "submitted": [],
    "failed": [
        {
            "queue_id": "feedback-20260116T150000-abc123",
            "attempts": 5
        }
    ]
}

# Updated file content:
{
    "submission_metadata": {
        "attempt_count": 5,
        "max_retries": 5,
        "last_attempted": "2026-01-16T18:00:00Z",
        "abandoned": True  # <-- Set to true
    }
}

# Note: File is NOT deleted (preserved for manual retry via /feedback --retry)
```

**Scenario 4: All Items Already Abandoned** (Automatic Retry)

```python
# Input: 2 queue entries (both abandoned)
queue_entries = [
    {
        "queue_id": "feedback-20260116T150000-abc123",
        "submission_metadata": {"attempt_count": 5, "abandoned": True}
    },
    {
        "queue_id": "feedback-20260116T160000-def456",
        "submission_metadata": {"attempt_count": 5, "abandoned": True}
    }
]

# Execution:
# - Both entries filtered out (attempt_count >= max_retries)
# - No submission attempts made

# Output:
{
    "submitted": [],
    "failed": []
}
```

**Scenario 5: Manual Retry Mode** (Ignores Abandoned Flag)

```python
# Same input as Scenario 4, but in /feedback --retry mode

# Execution:
# - Abandoned flag IGNORED (manual retry retries everything)
# - Both submissions attempted
# - If successful, files deleted; if failed, attempt_count stays at 5 (capped)

# Possible output (both succeed):
{
    "submitted": [
        {
            "queue_id": "feedback-20260116T150000-abc123",
            "issue_url": "https://github.example.com/my-org/my-plugin/issues/44"
        },
        {
            "queue_id": "feedback-20260116T160000-def456",
            "issue_url": "https://github.example.com/my-org/my-plugin/issues/45"
        }
    ],
    "failed": []
}
```

**Edge Cases**:

- **Concurrent access** → Queue file deleted by another process: FileNotFoundError caught, treat as success
- **Permission errors during deletion** → Log error, still count as submitted (GitHub issue created)
- **File write failure during metadata update** → Log error, file remains unchanged, retry will happen again
- **Corrupted file during update** → Original file preserved (atomic write failed), retry will happen again
- **Attempt count overflow** → Capped at max_retries (5), abandoned flag prevents infinite retries
- **Empty queue** → Returns `{submitted: [], failed: []}` immediately
- **Network errors** → Caught by IssueSubmitter, returned as `{success: False, error: ...}`
- **gh CLI not available** → Caught by IssueSubmitter, metadata updated, retry later

**Performance**:

- **Best case** (empty queue): ~1ms (no processing)
- **Typical case** (5 items, all succeed): ~10-25s (5 × 2-5s GitHub API latency)
- **Worst case** (5 items, all timeout): ~150s (5 × 30s timeout)
- **Non-blocking**: This algorithm runs in background (doesn't delay command execution)
  - **Implementation note**: In v1.0, "background" means sequential processing at command start. True async execution (threads/asyncio) is deferred to future optimization.

**Integration with Workflow**:

AutoRetry is called immediately after QueueReader at command start:

```python
# At command start (before main command logic):
queue_entries = QueueReader()

if queue_entries:
    retry_results = AutoRetry(queue_entries)

    # Results passed to NotificationRenderer (TASK-013) for display at command end
    # Notification examples:
    # - "✅ Queued feedback submitted successfully: issue #42 → [URL]"
    # - "⏸️ 1 feedback item queued, will retry when online"
```

**Error Recovery**:

- **Submission timeout** → Metadata updated, retry on next command invocation
- **Authentication failure** → Metadata updated, user must run `gh auth login`, retry later
- **Rate limit exceeded** → Metadata updated, retry on next command (respects GitHub API limits)
- **File corruption** → Skip entry, log error, continue processing queue
- **Disk full during metadata write** → Log error, original file preserved, retry will happen again

**Security Compliance**:

All security requirements from SECURITY.md followed:
- ✅ File operations use atomic writes (temp + rename)
- ✅ File permissions set to `0o600` (user-only)
- ✅ No user input in file paths (all from QueueReader)
- ✅ JSON serialization/deserialization with safe methods
- ✅ Subprocess execution delegated to IssueSubmitter (TASK-008) which follows SECURITY.md
- ✅ Error messages don't expose system internals
- ✅ All errors logged to `.claude/.feedback-errors.log` (not shown to user)

---

### 7. Iteration Limits

Approval editing: max 3 iterations
- Prevents infinite edit loops
- After 3 iterations: force Approve or Cancel

### 8. No Source Code Inclusion

Per spec constraint:
- Do NOT include user source code or snippets
- Even with user consent
- Only collect metadata (counts, frameworks, languages)

---

Now execute this command with the user's arguments.
