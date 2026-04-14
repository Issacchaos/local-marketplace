---
description: "Interactive multi-turn chat with a local Ollama model"
argument-hint: "[-s system-prompt] [--model name]"
allowed-tools: Bash, AskUserQuestion
---

Parse the arguments for optional flags:

- `-s "..."` — a system prompt to use for the conversation
- `--model <name>` — override the default Ollama model

If no system prompt is given, default to: "You are a helpful assistant."
If no model is given, omit the `--model` flag (open-wrapper uses its configured default).

**Step 1 — Start session.** Generate a `SESSION_ID` (UUID) that will be reused by every webhook POST in this chat session so the watcher can group all turns under one logical session:

```
SESSION_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')
```

Then POST a session start event via Bash:

```
curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper -H "Content-Type: application/json" \
  -d '{"event_type":"system","command":"chat","status":"start","model":"<model or default>","session_id":"'"$SESSION_ID"'","metadata":{"action":"chat_session_start"}}'
```

If the webhook POST fails, note it but continue — it is not blocking.

**Step 2 — Chat loop.** Maintain a `conversation_history` string that accumulates each exchange. Repeat the following:

1. Use **AskUserQuestion** to prompt the user for their next message. Use a prompt like: `[ollama-chat] You:`. If the user replies with `exit` or `quit` (case-insensitive), break out of the loop and go to Step 3.

2. Build the full system prompt by combining the base system prompt with the conversation history:
   ```
   <system prompt>

   Conversation so far:
   <conversation_history>
   ```
   If this is the first turn, omit the "Conversation so far" section.

3. Run the ask command via **Bash**:
   ```
   open-wrapper [--model <name>] ask -s "<full system prompt>" "<user message>"
   ```
   Capture the output as the assistant reply.

4. POST a completion event (non-blocking, ignore failures). Reuse the same `$SESSION_ID` generated in Step 1 so every turn in this session shares one id:
   ```
   curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper -H "Content-Type: application/json" \
     -d '{"event_type":"request","command":"chat","status":"complete","session_id":"'"$SESSION_ID"'","metadata":{"action":"chat_turn_complete","turn":<turn_number>}}'
   ```

5. Display the assistant reply to the user.

6. Append to `conversation_history`:
   ```
   User: <user message>
   Assistant: <assistant reply>
   ```

7. Go back to sub-step 1.

**Step 3 — End session.** POST a session end event via Bash, carrying the same `$SESSION_ID` so the end event pairs with the start and every turn in between:

```
curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper -H "Content-Type: application/json" \
  -d '{"event_type":"system","command":"chat","status":"end","session_id":"'"$SESSION_ID"'","metadata":{"action":"chat_session_end"}}'
```

Print a brief message confirming the chat session has ended and how many turns were completed.
