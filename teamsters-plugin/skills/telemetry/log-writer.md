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
D:/dev/teamsters-plugin/.claude/telemetry-2026-02-13T14-30-00.log
```

**Timestamp Format**: `YYYY-MM-DDTHH-MM-SS` (colons replaced with dashes for Windows compatibility)

---

### File Initialization

**Header** (written when file is created):
```
# Teamsters Team Orchestration Telemetry Log
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
        header = f"""# Teamsters Team Orchestration Telemetry Log
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
export TEAMSTERS_TELEMETRY=1

# Disable telemetry (default)
export TEAMSTERS_TELEMETRY=0
# Or unset TEAMSTERS_TELEMETRY
```

**Option 2: Configuration File**
```json
// .claude/teamsters-config.json
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
2. Environment variable (`TEAMSTERS_TELEMETRY=1`)
3. Configuration file (`.claude/teamsters-config.json`)
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
    env_value = os.environ.get('TEAMSTERS_TELEMETRY', '').strip()
    if env_value:
        return env_value.lower() in ('1', 'true', 'yes', 'on')

    # Priority 3: Configuration file
    config_file = os.path.join(project_root, '.claude', 'teamsters-config.json')
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

## Delivery Channels

The telemetry system supports 3 delivery channels. All channels are non-blocking - failures in any channel never halt execution.

### Channel 1: File (Default)

The existing append-only log file at `{project_root}/.claude/telemetry-{timestamp}.log`. Always active when telemetry is enabled.

### Channel 2: Console (Live Terminal Output)

Formats events as compact, human-readable lines and outputs them to the user's terminal in real-time during execution.

**Enabling Console Output**:
```bash
# Environment variable
export TEAMSTERS_TELEMETRY_CONSOLE=1

# CLI flag
/team-run my-team --telemetry-console

# Team definition
telemetry_console: true
```

**Configuration Precedence** (highest to lowest):
1. CLI flag `--telemetry-console`
2. Team definition `telemetry_console: true`
3. Environment variable `TEAMSTERS_TELEMETRY_CONSOLE=1`
4. Default: disabled

**Console Format**:
```
[HH:MM:SS] EVENT_TYPE  agent_id       status     key=value summary
```

**Example Output**:
```
[14:30:00] ENV        coordinator    session    platform=win32 branch=main
[14:30:01] CONFIG     coordinator    loaded     my-team (teams/my-team.md)
[14:30:01] DEPEND     coordinator    graph      2 nodes, 1 edge, no cycles
[14:30:01] COORD      coordinator    plan       2 agents in 2 phases
[14:30:10] APPROVAL   coordinator    approved   before_execution (8.6s)
[14:30:10] TIMING     coordinator    phase 0→1  0.05s
[14:30:10] AGENT_IO   analyzer       prompt     3500 chars → sonnet
[14:30:10] LIFECYCLE  analyzer       spawned    Explore, depth=2
[14:30:25] AGENT_IO   analyzer       output     1200 chars, 14.8s
[14:30:25] LIFECYCLE  analyzer       completed  14.9s
[14:30:25] COST       coordinator    running    $0.008 (1/2 agents)
[14:30:25] DATA       coordinator    passed     1200 chars phase 1→2
[14:30:25] TIMING     coordinator    phase 1→2  0.06s
[14:30:45] LIFECYCLE  writer         completed  19.5s
[14:30:45] COST       coordinator    running    $0.019 (2/2 agents)
[14:30:45] TIMING     coordinator    overhead   44.7s wall, 34.4s work, 23% tax
[14:30:45] LIFECYCLE  coordinator    completed  44.8s
[14:30:45] ENV        coordinator    session    completed, $0.019 total
```

**Color Coding** (when terminal supports ANSI colors):

| Event Type | Color | ANSI Code |
|------------|-------|-----------|
| lifecycle (completed) | Green | `\033[32m` |
| lifecycle (failed) | Red | `\033[31m` |
| lifecycle (spawned) | Yellow | `\033[33m` |
| timing | Cyan | `\033[36m` |
| error | Red | `\033[31m` |
| cost | Magenta | `\033[35m` |
| test (passed) | Blue | `\033[34m` |
| test (failed) | Red | `\033[31m` |
| environment | Dim gray | `\033[2m` |
| config | White | `\033[37m` |
| coordination | White | `\033[37m` |
| dependency | Cyan | `\033[36m` |
| agent_io | Yellow | `\033[33m` |
| approval | Magenta | `\033[35m` |
| data_flow | Blue | `\033[34m` |
| progress | Green | `\033[32m` |
| resource | Yellow | `\033[33m` |

**Event Type Abbreviations** (for compact display):

| Event Type | Abbreviation |
|------------|-------------|
| lifecycle | LIFECYCLE |
| coordination | COORD |
| progress | PROGRESS |
| test | TEST |
| resource | RESOURCE |
| config | CONFIG |
| dependency | DEPEND |
| agent_io | AGENT_IO |
| approval | APPROVAL |
| timing | TIMING |
| error | ERROR |
| cost | COST |
| data_flow | DATA |
| environment | ENV |

#### Console Writer Implementation

```python
def is_console_telemetry_enabled(team_def: dict = None) -> bool:
    """Check if console telemetry is enabled."""
    # Priority 1: Team definition
    if team_def and team_def.get('telemetry_console') is not None:
        return bool(team_def['telemetry_console'])

    # Priority 2: Environment variable
    env_value = os.environ.get('TEAMSTERS_TELEMETRY_CONSOLE', '').strip()
    if env_value:
        return env_value.lower() in ('1', 'true', 'yes', 'on')

    # Default: disabled
    return False


EVENT_TYPE_ABBREV = {
    'lifecycle': 'LIFECYCLE', 'coordination': 'COORD', 'progress': 'PROGRESS',
    'test': 'TEST', 'resource': 'RESOURCE', 'config': 'CONFIG',
    'dependency': 'DEPEND', 'agent_io': 'AGENT_IO', 'approval': 'APPROVAL',
    'timing': 'TIMING', 'error': 'ERROR', 'cost': 'COST',
    'data_flow': 'DATA', 'environment': 'ENV'
}

EVENT_TYPE_COLORS = {
    'lifecycle': {'completed': '\033[32m', 'failed': '\033[31m', 'spawned': '\033[33m', '_default': '\033[33m'},
    'timing': '\033[36m', 'error': '\033[31m', 'cost': '\033[35m',
    'test': {'passed': '\033[34m', 'failed': '\033[31m', '_default': '\033[34m'},
    'environment': '\033[2m', 'config': '\033[37m', 'coordination': '\033[37m',
    'dependency': '\033[36m', 'agent_io': '\033[33m', 'approval': '\033[35m',
    'data_flow': '\033[34m', 'progress': '\033[32m', 'resource': '\033[33m'
}
RESET = '\033[0m'


def format_console_event(event_type: str, agent_id: str, status: str, metadata: dict) -> str:
    """
    Format a telemetry event as a compact, human-readable console line.

    Args:
        event_type: Event type (e.g., "lifecycle")
        agent_id: Agent identifier
        status: Event status (e.g., "completed")
        metadata: Event metadata dict

    Returns:
        Formatted string for console output
    """
    from datetime import datetime, timezone

    # Timestamp (HH:MM:SS)
    now = datetime.now(timezone.utc)
    time_str = now.strftime('%H:%M:%S')

    # Event type abbreviation (padded to 10 chars)
    abbrev = EVENT_TYPE_ABBREV.get(event_type, event_type.upper())
    abbrev_padded = abbrev.ljust(10)

    # Agent ID (padded to 14 chars)
    agent_padded = agent_id[:14].ljust(14)

    # Status (padded to 10 chars)
    status_padded = status[:10].ljust(10)

    # Summary (extract key details from metadata)
    summary = format_event_summary(event_type, status, metadata)

    # Color
    color = get_color(event_type, status)

    return f"{color}[{time_str}] {abbrev_padded} {agent_padded} {status_padded} {summary}{RESET}"


def format_event_summary(event_type: str, status: str, metadata: dict) -> str:
    """Extract a compact summary from event metadata."""

    if event_type == 'lifecycle':
        if status == 'completed':
            duration = metadata.get('duration_seconds', '?')
            model = metadata.get('model_used', '')
            return f"{duration}s{', model=' + model if model else ''}"
        elif status == 'spawned':
            agent_type = metadata.get('agent_type', '')
            depth = metadata.get('depth', '')
            return f"{agent_type}, depth={depth}"
        elif status == 'failed':
            reason = metadata.get('reason', 'unknown')
            retries = metadata.get('retries', 0)
            return f"{reason} (retries={retries})"

    elif event_type == 'timing':
        if status == 'phase_transition':
            from_p = metadata.get('from_phase', '?')
            to_p = metadata.get('to_phase', '?')
            dur = metadata.get('transition_duration_seconds', '?')
            return f"phase {from_p}→{to_p}  {dur}s"
        elif status == 'overhead_summary':
            wall = metadata.get('total_wall_clock_seconds', '?')
            work = metadata.get('total_agent_work_seconds', '?')
            tax = metadata.get('framework_tax_percent', '?')
            return f"{wall}s wall, {work}s work, {tax}% tax"

    elif event_type == 'cost':
        if status == 'cumulative_cost':
            cost = metadata.get('estimated_cost_usd', '?')
            done = metadata.get('agents_completed', '?')
            remaining = metadata.get('agents_remaining', '?')
            total = done + remaining if isinstance(done, int) and isinstance(remaining, int) else '?'
            return f"${cost} ({done}/{total} agents)"

    elif event_type == 'agent_io':
        if status == 'prompt_constructed':
            chars = metadata.get('prompt_length_chars', '?')
            model = metadata.get('model', '')
            return f"{chars} chars → {model}"
        elif status == 'output_received':
            chars = metadata.get('output_length_chars', '?')
            dur = metadata.get('duration_seconds', '?')
            return f"{chars} chars, {dur}s"

    elif event_type == 'config':
        if status == 'config_loaded':
            name = metadata.get('team_name', '?')
            path = metadata.get('file_path', '')
            return f"{name} ({path})"

    elif event_type == 'dependency':
        if status == 'graph_constructed':
            nodes = metadata.get('total_nodes', '?')
            edges = metadata.get('total_edges', '?')
            cycles = metadata.get('has_cycles', False)
            return f"{nodes} nodes, {edges} edges, {'CYCLES!' if cycles else 'no cycles'}"

    elif event_type == 'approval':
        if status == 'user_response_received':
            decision = metadata.get('decision', '?')
            gate = metadata.get('gate_type', '')
            time_s = metadata.get('response_time_seconds', '')
            return f"{decision} {gate}{' (' + str(time_s) + 's)' if time_s else ''}"

    elif event_type == 'environment':
        if status == 'session_start':
            platform = metadata.get('platform', '?')
            branch = metadata.get('git_branch', '')
            return f"platform={platform}{' branch=' + branch if branch else ''}"
        elif status == 'session_end':
            exit_status = metadata.get('exit_status', '?')
            cost = metadata.get('total_estimated_cost_usd', '')
            return f"{exit_status}{', $' + str(cost) + ' total' if cost else ''}"

    elif event_type == 'test':
        if status == 'test_case_result':
            name = metadata.get('test_name', '?')
            result = metadata.get('status', '?')
            dur = metadata.get('duration_seconds', '?')
            return f"{name} {result} ({dur}s)"

    elif event_type == 'error':
        if status == 'error_classified':
            cat = metadata.get('error_category', '?')
            sev = metadata.get('classified_severity', '?')
            return f"{cat} [{sev}]"

    elif event_type == 'data_flow':
        if status == 'data_passed':
            size = metadata.get('data_size_chars', '?')
            from_p = metadata.get('from_phase', '?')
            to_p = metadata.get('to_phase', '?')
            return f"{size} chars phase {from_p}→{to_p}"

    # Fallback: show first few key=value pairs
    items = list(metadata.items())[:3]
    return ', '.join(f"{k}={v}" for k, v in items) if items else ''


def get_color(event_type: str, status: str) -> str:
    """Get ANSI color code for event type and status."""
    color_entry = EVENT_TYPE_COLORS.get(event_type, '')
    if isinstance(color_entry, dict):
        return color_entry.get(status, color_entry.get('_default', ''))
    return color_entry


def write_to_console(event_type: str, agent_id: str, status: str, metadata: dict) -> None:
    """
    Write formatted telemetry event to console (NON-BLOCKING).

    This function MUST NEVER raise exceptions.
    """
    try:
        line = format_console_event(event_type, agent_id, status, metadata)
        print(line)
    except Exception as e:
        # Non-blocking: swallow all errors
        pass
```

---

### Channel 3: Webhook (HTTP Streaming)

Streams events as JSON to a configurable HTTP endpoint in real-time.

**Enabling Webhook Streaming**:
```bash
# Set the webhook URL
export TEAMSTERS_TELEMETRY_WEBHOOK=http://localhost:8080/events

# Optional: Bearer token authentication
export TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN=my-api-key

# Optional: Batch mode (buffer N events before sending)
export TEAMSTERS_TELEMETRY_WEBHOOK_BATCH=10
```

Or in team definition:
```yaml
telemetry_webhook: "http://localhost:8080/events"
telemetry_webhook_token: "my-api-key"
telemetry_webhook_batch: 10
```

**Configuration Precedence** (highest to lowest):
1. Team definition `telemetry_webhook: "url"`
2. Environment variable `TEAMSTERS_TELEMETRY_WEBHOOK=url`
3. Default: disabled (no URL = no webhook)

**Request Format**:

Single event mode (default):
```
POST {webhook_url}
Content-Type: application/json
X-Teamsters-Event: lifecycle
X-Teamsters-Status: completed
X-Teamsters-Team: my-team
X-Teamsters-Session: sess-my-team-20260325
Authorization: Bearer {token}  (if TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN set)

{
  "timestamp": "2026-03-25T14:30:25.100Z",
  "event_type": "lifecycle",
  "agent_id": "analyzer",
  "status": "completed",
  "team_name": "my-team",
  "session_id": "sess-my-team-20260325",
  "metadata": {
    "duration_seconds": 14.9,
    "model_used": "sonnet",
    "output_summary": "Analysis complete"
  }
}
```

Batch mode (`TEAMSTERS_TELEMETRY_WEBHOOK_BATCH=N`):
```
POST {webhook_url}
Content-Type: application/json
X-Teamsters-Batch-Size: 10
X-Teamsters-Team: my-team
Authorization: Bearer {token}

{
  "batch": true,
  "events": [
    { "timestamp": "...", "event_type": "...", ... },
    { "timestamp": "...", "event_type": "...", ... }
  ],
  "batch_size": 10,
  "team_name": "my-team",
  "session_id": "sess-..."
}
```

**Compatible Endpoints**:
- Any HTTP endpoint accepting JSON POST
- Grafana Loki (`/loki/api/v1/push` with label transformation)
- Datadog Logs (`/api/v2/logs`)
- Elasticsearch (`/_bulk` with NDJSON transformation)
- Custom webhook receivers
- Local development servers (`http://localhost:PORT/events`)

#### Webhook Writer Implementation

```python
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


# Webhook event buffer for batch mode
_webhook_buffer = []
_webhook_buffer_lock = threading.Lock()


def get_webhook_url(team_def: dict = None) -> str:
    """Get webhook URL from configuration."""
    # Priority 1: Team definition
    if team_def and team_def.get('telemetry_webhook'):
        return team_def['telemetry_webhook']

    # Priority 2: Environment variable
    return os.environ.get('TEAMSTERS_TELEMETRY_WEBHOOK', '').strip() or None


def get_webhook_token(team_def: dict = None) -> str:
    """Get webhook auth token."""
    if team_def and team_def.get('telemetry_webhook_token'):
        return team_def['telemetry_webhook_token']
    return os.environ.get('TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN', '').strip() or None


def get_webhook_batch_size(team_def: dict = None) -> int:
    """Get webhook batch size (0 = no batching)."""
    if team_def and team_def.get('telemetry_webhook_batch'):
        return int(team_def['telemetry_webhook_batch'])
    env_val = os.environ.get('TEAMSTERS_TELEMETRY_WEBHOOK_BATCH', '').strip()
    return int(env_val) if env_val else 0


def write_to_webhook(
    event_type: str,
    agent_id: str,
    status: str,
    metadata: dict,
    team_name: str = None,
    session_id: str = None,
    team_def: dict = None
) -> None:
    """
    Send telemetry event to webhook endpoint (NON-BLOCKING).

    This function MUST NEVER raise exceptions.
    Fire-and-forget: does not wait for response beyond timeout.
    """
    try:
        webhook_url = get_webhook_url(team_def)
        if not webhook_url:
            return  # No webhook configured

        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')

        event_payload = {
            'timestamp': timestamp,
            'event_type': event_type,
            'agent_id': agent_id,
            'status': status,
            'team_name': team_name or 'unknown',
            'session_id': session_id or 'unknown',
            'metadata': metadata
        }

        batch_size = get_webhook_batch_size(team_def)

        if batch_size > 0:
            # Batch mode: buffer events
            with _webhook_buffer_lock:
                _webhook_buffer.append(event_payload)
                if len(_webhook_buffer) >= batch_size:
                    batch = list(_webhook_buffer)
                    _webhook_buffer.clear()
                    _send_webhook_batch(webhook_url, batch, team_name, session_id, team_def)
        else:
            # Single event mode
            _send_webhook_single(webhook_url, event_payload, team_def)

    except Exception:
        # NON-BLOCKING: swallow all errors
        pass


def flush_webhook_buffer(team_def: dict = None) -> None:
    """Flush any remaining events in the webhook buffer. Call at session end."""
    try:
        webhook_url = get_webhook_url(team_def)
        if not webhook_url:
            return

        with _webhook_buffer_lock:
            if _webhook_buffer:
                batch = list(_webhook_buffer)
                _webhook_buffer.clear()
                _send_webhook_batch(webhook_url, batch, None, None, team_def)
    except Exception:
        pass


def _send_webhook_single(webhook_url: str, payload: dict, team_def: dict = None) -> None:
    """Send single event to webhook (fire-and-forget, 5s timeout)."""
    try:
        data = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'X-Teamsters-Event': payload.get('event_type', ''),
            'X-Teamsters-Status': payload.get('status', ''),
            'X-Teamsters-Team': payload.get('team_name', ''),
            'X-Teamsters-Session': payload.get('session_id', '')
        }

        token = get_webhook_token(team_def)
        if token:
            headers['Authorization'] = f'Bearer {token}'

        req = urllib.request.Request(webhook_url, data=data, headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Fire-and-forget


def _send_webhook_batch(webhook_url: str, events: list, team_name: str, session_id: str, team_def: dict = None) -> None:
    """Send batch of events to webhook (fire-and-forget, 5s timeout)."""
    try:
        payload = {
            'batch': True,
            'events': events,
            'batch_size': len(events),
            'team_name': team_name or (events[0].get('team_name') if events else 'unknown'),
            'session_id': session_id or (events[0].get('session_id') if events else 'unknown')
        }

        data = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'X-Teamsters-Batch-Size': str(len(events)),
            'X-Teamsters-Team': payload['team_name']
        }

        token = get_webhook_token(team_def)
        if token:
            headers['Authorization'] = f'Bearer {token}'

        req = urllib.request.Request(webhook_url, data=data, headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Fire-and-forget
```

---

## Multi-Channel Dispatch

The `write_telemetry_event()` function dispatches to all enabled channels:

```python
def write_telemetry_event(event: str, project_root: str, team_name: str = None,
                          event_type: str = None, agent_id: str = None,
                          status: str = None, metadata: dict = None,
                          session_id: str = None, team_def: dict = None) -> dict:
    """
    Write telemetry event to all enabled channels (NON-BLOCKING).

    Channels:
    1. File: Always active (when telemetry enabled)
    2. Console: When TEAMSTERS_TELEMETRY_CONSOLE=1
    3. Webhook: When TEAMSTERS_TELEMETRY_WEBHOOK is set

    All channels are non-blocking. Failures in any channel do not
    affect other channels or halt execution.
    """
    try:
        if not is_telemetry_enabled(team_def):
            return {'success': True, 'log_file': None, 'warning': None}

        # Channel 1: File (existing behavior)
        file_result = _write_to_file(event, project_root, team_name)

        # Channel 2: Console (if enabled)
        if is_console_telemetry_enabled(team_def):
            write_to_console(event_type, agent_id, status, metadata)

        # Channel 3: Webhook (if configured)
        if get_webhook_url(team_def):
            write_to_webhook(event_type, agent_id, status, metadata,
                           team_name, session_id, team_def)

        return file_result

    except Exception as e:
        return {'success': True, 'log_file': None, 'warning': str(e)}
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
- [ ] Opt-in via `TEAMSTERS_TELEMETRY=1` environment variable (REQ-F-22)
- [ ] Opt-in via `.claude/teamsters-config.json` configuration file (REQ-F-22)
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

### Console Output
- [ ] Console output enabled via TEAMSTERS_TELEMETRY_CONSOLE=1
- [ ] Console output disabled by default
- [ ] Events formatted as compact human-readable lines
- [ ] Color coding applied when terminal supports ANSI
- [ ] Console write failures don't halt execution
- [ ] Event type abbreviations used (LIFECYCLE, COORD, etc.)

### Webhook Streaming
- [ ] Webhook enabled via TEAMSTERS_TELEMETRY_WEBHOOK URL
- [ ] Single event mode sends individual POST requests
- [ ] Batch mode buffers N events before sending
- [ ] Bearer token auth via TEAMSTERS_TELEMETRY_WEBHOOK_TOKEN
- [ ] Custom headers include event type, status, team, session
- [ ] 5-second timeout per request (fire-and-forget)
- [ ] Webhook failures don't halt execution
- [ ] Buffer flushed at session end

---

## Example Log File

**File**: `.claude/telemetry-2026-02-13T14-30-00.log`

```
# Teamsters Team Orchestration Telemetry Log
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
