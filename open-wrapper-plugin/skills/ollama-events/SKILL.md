---
name: ollama-events
description: Emit events to the open-wrapper LLM watcher dashboard via webhook
---

# Emitting Events to open-wrapper Dashboard

Events are sent to the LLM Watcher dashboard via its open-wrapper webhook endpoint:

| Endpoint | Port | Path | Use case |
|----------|------|------|----------|
| LLM Watcher | 3000 | `/api/open-wrapper` | Dashboard event ingestion |

All examples below use this endpoint.

## Event Schema

```json
{
  "id": "uuid-string",
  "timestamp": "RFC 3339 timestamp",
  "event_type": "request | streaming | completion | error | setup | status | system",
  "command": "string",
  "status": "start | running | completed | failed | info",
  "model": "optional model name",
  "metadata": {},
  "source": "ignored -- server overrides to \"webhook\""
}
```

The `id`, `timestamp`, and `source` fields are required in the JSON payload (the server deserializes the full `DashboardEvent` struct) but `source` is always overwritten to `"webhook"` by the server.

## Emitting a Single Event

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(uuidgen || cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "event_type": "request",
    "command": "ask",
    "status": "start",
    "model": "qwen2.5-coder:latest",
    "metadata": {"prompt": "hello world"},
    "source": "webhook"
  }'
```

The server responds with `{"ok": true}` on success.

## Emitting Batch Events

Wrap multiple events in a batch payload:

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "batch": true,
    "events": [
      {
        "id": "uuid-1",
        "timestamp": "2026-01-01T00:00:00.000Z",
        "event_type": "request",
        "command": "ask",
        "status": "start",
        "model": "qwen2.5-coder:latest",
        "metadata": {},
        "source": "webhook"
      },
      {
        "id": "uuid-2",
        "timestamp": "2026-01-01T00:00:01.000Z",
        "event_type": "completion",
        "command": "ask",
        "status": "completed",
        "model": "qwen2.5-coder:latest",
        "metadata": {"tokens": 128},
        "source": "webhook"
      }
    ]
  }'
```

## Standard Event Patterns

### Request Start

Emit when an LLM request begins.

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(python3 -c "import uuid; print(uuid.uuid4())")'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "event_type": "request",
    "command": "ask",
    "status": "start",
    "model": "qwen2.5-coder:latest",
    "metadata": {"prompt_length": 42},
    "source": "webhook"
  }'
```

### Request Complete

Emit when the LLM response has been fully received.

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(python3 -c "import uuid; print(uuid.uuid4())")'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "event_type": "completion",
    "command": "ask",
    "status": "completed",
    "model": "qwen2.5-coder:latest",
    "metadata": {"tokens": 256, "duration_ms": 1200},
    "source": "webhook"
  }'
```

### Error

Emit when a request fails.

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(python3 -c "import uuid; print(uuid.uuid4())")'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "event_type": "error",
    "command": "ask",
    "status": "failed",
    "model": "qwen2.5-coder:latest",
    "metadata": {"error": "connection refused", "code": 502},
    "source": "webhook"
  }'
```

### System Info

Emit informational or diagnostic messages.

```bash
curl -s -X POST http://localhost:3000/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(python3 -c "import uuid; print(uuid.uuid4())")'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "event_type": "system",
    "command": "system",
    "status": "info",
    "metadata": {"detail": "Model cache cleared"},
    "source": "webhook"
  }'
```

## Additional Event Types

Beyond the four standard patterns above, the schema supports:

- `event_type: "streaming"` with `status: "running"` -- for streaming chunk progress
- `event_type: "setup"` with `status: "info"` -- for initialization/configuration events
- `event_type: "status"` with `status: "info"` -- for health checks or status reports

## Verifying Events

Check that events are arriving via the LLM Watcher endpoints:

```bash
# Get full event history
curl -s http://localhost:3000/api/history | python3 -m json.tool

# Get aggregated stats
curl -s http://localhost:3000/api/stats | python3 -m json.tool

# Stream live events via SSE
curl -s -N http://localhost:3000/api/events
```
