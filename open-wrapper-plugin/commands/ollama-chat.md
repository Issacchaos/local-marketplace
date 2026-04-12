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

**Step 1 — Start session.** POST a session start event via Bash:

```
curl -s -X POST http://localhost:3000/api/open-wrapper -H "Content-Type: application/json" \
  -d '{"event_type":"system","command":"chat","status":"start","model":"<model or default>","metadata":{"action":"chat_session_start"}}'
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

4. POST a completion event (non-blocking, ignore failures):
   ```
   curl -s -X POST http://localhost:3000/api/open-wrapper -H "Content-Type: application/json" \
     -d '{"event_type":"request","command":"chat","status":"complete","metadata":{"action":"chat_turn_complete","turn":<turn_number>}}'
   ```

5. Display the assistant reply to the user.

6. Append to `conversation_history`:
   ```
   User: <user message>
   Assistant: <assistant reply>
   ```

7. Go back to sub-step 1.

**Step 3 — End session.** POST a session end event via Bash:

```
curl -s -X POST http://localhost:3000/api/open-wrapper -H "Content-Type: application/json" \
  -d '{"event_type":"system","command":"chat","status":"end","metadata":{"action":"chat_session_end"}}'
```

Print a brief message confirming the chat session has ended and how many turns were completed.
