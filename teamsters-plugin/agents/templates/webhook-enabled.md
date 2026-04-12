---
name: webhook-enabled
description: Template mixin that adds standard webhook event posting to any agent. Reduces boilerplate by providing reusable telemetry event functions.
type: template
version: "1.0.0"
---

# Webhook-Enabled Agent Template

This template adds standard webhook event posting capabilities to any agent that extends it. Instead of duplicating webhook curl commands in every agent definition, agents can inherit this template via `extends: agents/templates/webhook-enabled.md`.

---

## Webhook Event Posting

Throughout your execution, post webhook events to report progress. This enables real-time telemetry and monitoring.

### Post a Start Event

When you begin your task, post a start event:

```bash
curl -s -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"info\", \"agent\": \"{{agent_name}}\", \"action\": \"task-start\", \"detail\": \"Starting: {{task_description}}\"}" > /dev/null 2>&1 || true
```

### Post Progress Events

For significant milestones during execution:

```bash
curl -s -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"progress\", \"agent\": \"{{agent_name}}\", \"action\": \"milestone\", \"detail\": \"<description of milestone>\"}" > /dev/null 2>&1 || true
```

### Post a Completion Event

When you finish your task successfully:

```bash
curl -s -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"success\", \"agent\": \"{{agent_name}}\", \"action\": \"task-complete\", \"detail\": \"Completed: {{task_description}}\", \"files_modified\": [\"<list files>\"]}" > /dev/null 2>&1 || true
```

### Post an Error Event

If you encounter an error:

```bash
curl -s -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"error\", \"agent\": \"{{agent_name}}\", \"action\": \"task-error\", \"detail\": \"<error description>\"}" > /dev/null 2>&1 || true
```

### Important Notes

- All webhook calls use `|| true` to ensure failures don't halt execution
- Output is redirected to `/dev/null` to keep agent output clean
- Replace `<description>` placeholders with actual values at runtime
- The `{{agent_name}}` and `{{task_description}}` placeholders are resolved from agent frontmatter at load time
- If the webhook endpoint is not available, events are silently dropped (non-blocking)
