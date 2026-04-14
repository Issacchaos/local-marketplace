---
description: "Check Ollama server health and list available models"
allowed-tools: Bash
---

Run these three commands in parallel using the Bash tool:

1. `open-wrapper status` -- returns server health and active model info
2. `open-wrapper models` -- lists configured and installed models
3. POST a health-check event to the SSE webhook. `/ollama-status` is single-shot (one event per invocation), so generate a fresh `SESSION_ID` inline for this one event — each `/ollama-status` invocation therefore gets a unique id, distinguishable from other concurrent `/ask-ollama` or `/ollama-chat` sessions:
   ```
   SESSION_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')
   curl -s -X POST http://localhost:9713/webhook -H "Content-Type: application/json" -d '{"event_type":"system","command":"status","status":"info","session_id":"'"$SESSION_ID"'","metadata":{"action":"health_check"}}'
   ```

After all three complete, present a summary with these sections:

- **Server Health**: whether the Ollama server is reachable and running
- **Active Model**: the currently configured/default model
- **Available Models**: a list of installed models from `open-wrapper models`

If the server is unreachable, say so clearly and suggest running `ollama serve`. If the webhook POST fails, note it but do not treat it as a blocking error.
