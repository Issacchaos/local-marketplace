---
name: log-writer
description: Non-blocking telemetry log writer with append-only writes and automatic log rotation
user-invocable: false
---

# Telemetry Log Writer

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Non-blocking append-only log writer for telemetry events with automatic rotation

**Used By**: Telemetry SKILL

---

## Overview

The Telemetry Log Writer provides safe, non-blocking writes of telemetry events to timestamped log files in the project's `.claude/` directory. It ensures telemetry failures NEVER halt agent execution through comprehensive error handling, implements append-only writes without file locking, and automatically rotates logs when they exceed 10MB.

### Critical Design Principle (REQ-NF-6)

**Telemetry failures MUST NOT halt execution.** All operations are wrapped in try/except blocks. Any failure logs a warning but execution continues normally. This is the MOST IMPORTANT principle of the telemetry system.

---

## Skill Interface

### Input

```yaml
event: string                   # Formatted telemetry event (from event-types.md)
project_root: string            # Absolute path to project root
```

### Output

```yaml
# Success case
success: boolean                # Always true (even if write failed)
log_file: string                # Path to log file (if write succeeded)
warning: string | null          # Warning message if write failed (non-blocking)

# Note: This function NEVER raises exceptions. All errors are caught and logged.
```

---

## Log File Configuration (REQ-F-21)

### File Location

**Path Pattern**:
```
{project_root}/.claude/telemetry-{timestamp}.log
```

**Example**:
```
D:/dev/dante_plugin/.claude/telemetry-2026-02-13T14-30-00.log
```

**Timestamp Format**: `YYYY-MM-DDTHH-MM-SS` (colons replaced with dashes for Windows compatibility)

---

### File Initialization

**Header** (written when file is created):
```
# Dante Team Orchestration Telemetry Log
# Generated: 2026-02-13T14:30:00.000Z
# Team: {team_name}
# Telemetry Version: 1.0.0
# Format: [timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
---
```

**Creation Logic**:
```python
def initialize_log_file(log_file_path: str, team_name: str) -> bool:
    """
    Initialize new telemetry log file with header.

    Args:
        log_file_path: Absolute path to log file
        team_name: Name of team being logged (optional)

    Returns:
        bool: True if successful, False if failed (non-blocking)
    """
    try:
        # Ensure .claude directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Create header
        timestamp = datetime.now(timezone.utc).isoformat()
        header = f"""# Dante Team Orchestration Telemetry Log
# Generated: {timestamp}
# Team: {team_name or 'unknown'}
# Telemetry Version: 1.0.0
# Format: [timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
---
"""

        # Write header
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(header)

        return True

    except Exception as e:
        # NON-BLOCKING: Log warning but don't raise exception
        log_warning(f"Failed to initialize telemetry log file: {e}")
        return False
```

---

## Opt-In Configuration (REQ-F-22)

### Enabling Telemetry

Telemetry is **disabled by default** (opt-in only). Users must explicitly enable it via:

**Option 1: Environment Variable**
```bash
# Enable telemetry
export DANTE_TELEMETRY=1

# Disable telemetry (default)
export DANTE_TELEMETRY=0
# Or unset DANTE_TELEMETRY
```

**Option 2: Configuration File**
```json
// .claude/dante-config.json
{
  "telemetry_enabled": true
}
```

**Option 3: Team Definition Override**
```yaml
# teams/testing-parallel.md
---
telemetry_enabled: true
# ... other fields
---
```

---

### Configuration Precedence

**Priority Order** (highest to lowest):
1. Team definition frontmatter (`telemetry_enabled: true`)
2. Environment variable (`DANTE_TELEMETRY=1`)
3. Configuration file (`.claude/dante-config.json`)
4. Default (disabled)

**Detection Logic**:
```python
def is_telemetry_enabled(team_def: dict = None) -> bool:
    """
    Check if telemetry is enabled based on configuration precedence.

    Args:
        team_def: Team definition dict (optional, for team-level override)

    Returns:
        bool: True if enabled, False otherwise
    """
    # Priority 1: Team definition override
    if team_def and 'telemetry_enabled' in team_def and team_def['telemetry_enabled'] is not None:
        return bool(team_def['telemetry_enabled'])

    # Priority 2: Environment variable
    env_value = os.environ.get('DANTE_TELEMETRY', '').strip()
    if env_value:
        return env_value.lower() in ('1', 'true', 'yes', 'on')

    # Priority 3: Configuration file
    config_file = os.path.join(project_root, '.claude', 'dante-config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'telemetry_enabled' in config:
                    return bool(config['telemetry_enabled'])
        except Exception:
            pass  # If config read fails, fall through to default

    # Priority 4: Default (disabled)
    return False
```

---

## Non-Blocking Write Implementation (REQ-NF-6)

### Core Write Function

```python
def write_telemetry_event(event: str, project_root: str, team_name: str = None) -> dict:
    """
    Write telemetry event to log file (NON-BLOCKING).

    This function MUST NEVER raise exceptions. All errors are caught and logged
    as warnings, but execution continues normally.

    Args:
        event: Formatted telemetry event string
        project_root: Absolute path to project root
        team_name: Team name for log file initialization (optional)

    Returns:
        dict with success status and optional warning
    """
    try:
        # Check if telemetry is enabled
        if not is_telemetry_enabled():
            # Silent no-op if disabled (not an error)
            return {'success': True, 'log_file': None, 'warning': None}

        # Get or create log file path
        log_file = get_current_log_file(project_root)

        # Check if log file exists (if not, initialize with header)
        if not os.path.exists(log_file):
            initialize_log_file(log_file, team_name)

        # Check file size (rotate if needed)
        if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            log_file = rotate_log_file(log_file)

        # Append event to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(event + '\n')

        return {
            'success': True,
            'log_file': log_file,
            'warning': None
        }

    except Exception as e:
        # CRITICAL: Never raise exception from telemetry
        warning_msg = f"Telemetry write failed (non-critical): {e}"
        log_warning(warning_msg)

        # Return success=True so coordinator doesn't treat this as error
        return {
            'success': True,
            'log_file': None,
            'warning': warning_msg
        }
```

**Key Points**:
1. **Always returns success**: Even if write fails, returns `success: True`
2. **Never raises exceptions**: All errors caught in try/except
3. **Warns but continues**: Logs warning but doesn't halt execution
4. **Silent when disabled**: If telemetry disabled, returns immediately (no-op)

---

## Log File Management

### Current Log File Resolution

```python
def get_current_log_file(project_root: str) -> str:
    """
    Get path to current telemetry log file.

    Uses session-based log file (one log file per session). Session start time
    is cached in memory to ensure all events go to same file.

    Args:
        project_root: Absolute path to project root

    Returns:
        str: Absolute path to current log file
    """
    global _current_log_file_cache

    # Check cache (session-based)
    if '_current_log_file_cache' in globals() and _current_log_file_cache:
        return _current_log_file_cache

    # Generate new log file name with session timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
    log_file = os.path.join(project_root, '.claude', f'telemetry-{timestamp}.log')

    # Cache for this session
    _current_log_file_cache = log_file

    return log_file
```

---

### Log Rotation

**Trigger**: Log file exceeds 10MB

**Action**: Rename current log to archive, create new log file

```python
def rotate_log_file(current_log_file: str) -> str:
    """
    Rotate log file when it exceeds 10MB.

    Args:
        current_log_file: Path to current log file

    Returns:
        str: Path to new log file
    """
    try:
        # Generate archive filename with rotation timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
        base_name = os.path.basename(current_log_file).replace('.log', '')
        archived_name = f"{base_name}-archived-{timestamp}.log"
        archived_path = os.path.join(os.path.dirname(current_log_file), archived_name)

        # Rename current log to archive
        os.rename(current_log_file, archived_path)

        # Create new log file (with same base name)
        new_log_file = current_log_file

        # Update cache
        global _current_log_file_cache
        _current_log_file_cache = new_log_file

        # Log rotation event to new file
        log_warning(f"Telemetry log rotated (exceeded 10MB): {archived_name}")

        return new_log_file

    except Exception as e:
        # If rotation fails, continue with current file (non-blocking)
        log_warning(f"Log rotation failed (continuing with current file): {e}")
        return current_log_file
```

**Archive Naming Pattern**:
```
telemetry-2026-02-13T14-30-00.log                  # Original log
telemetry-2026-02-13T14-30-00-archived-2026-02-13T15-45-00.log  # Archived after rotation
telemetry-2026-02-13T14-30-00.log                  # New log (same name)
```

---

## Append-Only Write Strategy

### Why No File Locking?

**Decision**: Use append-only writes without file locking

**Rationale**:
1. **Simplicity**: No lock coordination between parallel agents
2. **Performance**: No lock contention overhead
3. **Reliability**: Filesystem append is atomic at line level on most systems
4. **Safety**: Events are self-contained (one line = one event)

**Trade-offs**:
- **Risk**: In rare cases, concurrent appends may interleave bytes within a single line
- **Mitigation**: Events are timestamped, so even if interleaved, they can be sorted
- **Reality**: This is extremely rare on modern filesystems (Linux/Windows handle append atomicity well)

---

### Append Implementation

```python
def append_event(log_file: str, event: str) -> bool:
    """
    Append event to log file (append-only, no locking).

    Args:
        log_file: Absolute path to log file
        event: Formatted event string (single line)

    Returns:
        bool: True if successful, False if failed (non-blocking)
    """
    try:
        # Open in append mode ('a')
        # Most filesystems provide atomic append for single writes under 4KB
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(event + '\n')

        return True

    except Exception as e:
        # NON-BLOCKING: Log warning but don't raise
        log_warning(f"Failed to append telemetry event: {e}")
        return False
```

**Atomicity Guarantees**:
- **Linux**: Writes < PIPE_BUF (4096 bytes) are atomic when using `O_APPEND` (which Python's 'a' mode uses)
- **Windows**: WriteFile with FILE_APPEND_DATA is atomic at line level
- **Telemetry Events**: Most events are < 1KB, well within atomic write limits

---

## Performance Requirements (REQ-NF-3)

### Event Logging Latency

**Requirement**: Events logged within 1 second of occurrence

**Implementation**:
- **No Buffering**: Events written immediately (no in-memory buffer)
- **No Batching**: Each event written individually
- **Async-Safe**: Non-blocking writes return quickly

**Measurement**:
```python
def log_telemetry_with_timing(event: str, project_root: str) -> dict:
    """
    Log telemetry event and measure write latency.

    Returns:
        dict with success status and write_time_ms
    """
    start_time = time.time()

    result = write_telemetry_event(event, project_root)

    write_time_ms = (time.time() - start_time) * 1000
    result['write_time_ms'] = write_time_ms

    # Log warning if write took > 1000ms (exceeds REQ-NF-3)
    if write_time_ms > 1000:
        log_warning(f"Telemetry write exceeded 1 second: {write_time_ms:.2f}ms")

    return result
```

**Expected Latency**: < 10ms on typical systems (well below 1 second requirement)

---

## Error Handling Patterns

### Pattern 1: Try/Except Wrapper

**All telemetry operations wrapped**:
```python
try:
    # Telemetry operation
    write_telemetry_event(...)
except Exception as e:
    # NEVER propagate exception
    log_warning(f"Telemetry failed (non-critical): {e}")
    # Execution continues normally
```

---

### Pattern 2: Silent Failure When Disabled

**No-op if telemetry disabled**:
```python
def log_telemetry(event_type, agent_id, status, metadata):
    try:
        if not is_telemetry_enabled():
            return  # Silent no-op, no warning

        # ... telemetry logic ...
    except Exception as e:
        log_warning(f"Telemetry failed: {e}")
```

---

### Pattern 3: Graceful Degradation

**Continue even if writes fail**:
```python
def write_multiple_events(events: list) -> int:
    """
    Write multiple events, continue even if some fail.

    Returns:
        int: Number of events successfully written
    """
    success_count = 0

    for event in events:
        try:
            result = write_telemetry_event(event, project_root)
            if result['success']:
                success_count += 1
        except Exception:
            # Skip failed event, continue with remaining
            continue

    return success_count
```

---

## Usage in Coordinator

```markdown
# In skills/telemetry/SKILL.md

## How to Log Events

1. Read event-types.md to understand event schemas
2. Format event according to schema
3. Call log_writer to write event (non-blocking)
4. Continue execution regardless of write result

Example:
```python
# Format lifecycle event (agent spawned)
timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
event = f"{timestamp} | lifecycle | write-agent-1 | spawned | {json.dumps({'parent':'testing-coordinator','depth':2})}"

# Write event (non-blocking)
result = write_telemetry_event(event, project_root, team_name='testing-parallel')

# Check result (optional - for debugging)
if result['warning']:
    # Telemetry write failed, but execution continues
    log_debug(f"Telemetry warning: {result['warning']}")

# Continue with coordinator logic (telemetry failure doesn't halt execution)
```
```

---

## File System Operations

### Directory Creation

```python
def ensure_telemetry_directory(project_root: str) -> bool:
    """
    Ensure .claude directory exists for telemetry logs.

    Args:
        project_root: Absolute path to project root

    Returns:
        bool: True if directory exists or was created, False if failed
    """
    try:
        telemetry_dir = os.path.join(project_root, '.claude')
        os.makedirs(telemetry_dir, exist_ok=True)
        return True
    except Exception as e:
        log_warning(f"Failed to create telemetry directory: {e}")
        return False
```

---

### File Size Check

```python
def get_log_file_size(log_file: str) -> int:
    """
    Get log file size in bytes.

    Args:
        log_file: Absolute path to log file

    Returns:
        int: File size in bytes, or 0 if file doesn't exist or error
    """
    try:
        if os.path.exists(log_file):
            return os.path.getsize(log_file)
        return 0
    except Exception:
        return 0
```

---

### File Existence Check

```python
def log_file_exists(log_file: str) -> bool:
    """
    Check if log file exists.

    Args:
        log_file: Absolute path to log file

    Returns:
        bool: True if file exists, False otherwise
    """
    try:
        return os.path.exists(log_file)
    except Exception:
        return False
```

---

## Testing Checklist

For TASK-006 acceptance:

- [ ] Writes to `.claude/telemetry-[timestamp].log` in project root (REQ-F-21)
- [ ] Opt-in via `DANTE_TELEMETRY=1` environment variable (REQ-F-22)
- [ ] Opt-in via `.claude/dante-config.json` configuration file (REQ-F-22)
- [ ] Team definition can override global telemetry setting (REQ-F-22)
- [ ] Non-blocking: try/except wrapper catches all exceptions (REQ-NF-6)
- [ ] Failures log warning but never halt execution (REQ-NF-6)
- [ ] Append-only writes (no file locking needed)
- [ ] Log rotation when file exceeds 10MB
- [ ] Rotated logs archived with timestamp suffix
- [ ] Log file initialized with header on first write
- [ ] Telemetry disabled by default (silent no-op)
- [ ] Events written within 1 second of occurrence (REQ-NF-3)
- [ ] Directory created automatically if missing
- [ ] Handles file permission errors gracefully
- [ ] Handles disk full errors gracefully
- [ ] Session-based log file (one log per session)
- [ ] Cache prevents multiple log files in same session

---

## Example Log File

**File**: `.claude/telemetry-2026-02-13T14-30-00.log`

```
# Dante Team Orchestration Telemetry Log
# Generated: 2026-02-13T14:30:00.000Z
# Team: testing-parallel
# Telemetry Version: 1.0.0
# Format: [timestamp] | [event_type] | [agent_id] | [status] | [metadata_json]
---
2026-02-13T14:30:01.123Z | lifecycle | testing-coordinator | spawned | {"parent":"test-loop-orchestrator","depth":1,"team_id":"testing-parallel"}
2026-02-13T14:30:01.456Z | coordination | testing-coordinator | plan_proposed | {"plan_summary":"3 parallel write-agents","batches":3}
2026-02-13T14:30:15.789Z | coordination | testing-coordinator | plan_approved | {"user_response":"approve","batches":3}
2026-02-13T14:30:16.000Z | lifecycle | write-agent-1 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:16.100Z | lifecycle | write-agent-2 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:16.200Z | lifecycle | write-agent-3 | spawned | {"parent":"testing-coordinator","depth":2}
2026-02-13T14:30:30.000Z | lifecycle | write-agent-1 | completed | {"duration_seconds":13.7,"tests_generated":5}
2026-02-13T14:30:32.000Z | lifecycle | write-agent-3 | completed | {"duration_seconds":15.8,"tests_generated":4}
2026-02-13T14:30:35.000Z | lifecycle | write-agent-2 | completed | {"duration_seconds":18.9,"tests_generated":6}
2026-02-13T14:30:49.500Z | lifecycle | testing-coordinator | completed | {"duration_seconds":48.4}
```

---

## References

- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-21, REQ-F-22, REQ-NF-3, REQ-NF-6)
- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Telemetry Implementation Details)
- Pattern: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-006)
