---
description: "Send a one-shot prompt to a local Ollama model via open-wrapper"
argument-hint: "<prompt> [-s system-prompt] [--model name]"
allowed-tools: Bash
---

You are executing the `/ask-ollama` command. Your job is to send a one-shot prompt to a local Ollama model using the `open-wrapper` CLI and report the response.

## Step 1: Parse Arguments

Extract from the user's input:
- **prompt** (required): The main prompt text. Everything that is not a flag or flag value.
- **-s <system-prompt>** (optional): A system prompt to prepend.
- **--model <name>** (optional): Override the default Ollama model.

If no prompt text is provided, ask the user what they want to ask and stop.

## Step 2: Build and Run the Command

Construct the `open-wrapper ask` invocation:

```
open-wrapper [--model <model>] ask [-s "<system-prompt>"] "<prompt>"
```

Set a shell variable for the model name (use the `--model` value if provided, otherwise `"default"`):

```bash
MODEL_NAME="<model-or-default>"
```

Before running the query, POST a start event to the dashboard webhook (fire-and-forget):

```bash
curl -s -X POST http://localhost:9713/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_type":"request","command":"ask","status":"start","model":"'"$MODEL_NAME"'","metadata":{"prompt":"'"${PROMPT_TRUNCATED}"'"}}' \
  > /dev/null 2>&1 &
```

Truncate the prompt to 200 characters max for the webhook metadata.

Then run the actual command and capture its output:

```bash
RESPONSE=$(open-wrapper [--model <model>] ask [-s "<system>"] "<prompt>" 2>&1)
echo "$RESPONSE"
```

After the command completes, POST a completion event:

```bash
RESP_LEN=${#RESPONSE}
# Truncate the response body to 8000 chars and JSON-escape it (handles backslashes, quotes,
# newlines, tabs, carriage returns, and control chars) so it can be embedded safely in the webhook payload.
RESPONSE_ESCAPED=$(printf '%s' "${RESPONSE:0:8000}" | python3 -c 'import json,sys; sys.stdout.write(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null \
  || printf '%s' "${RESPONSE:0:8000}" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g' -e 's/\r/\\r/g' -e 's/\t/\\t/g')
curl -s -X POST http://localhost:9713/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_type":"completion","command":"ask","status":"completed","model":"'"$MODEL_NAME"'","metadata":{"prompt":"'"${PROMPT_TRUNCATED}"'","response_length":'"$RESP_LEN"',"response":"'"${RESPONSE_ESCAPED}"'"}}' \
  > /dev/null 2>&1
```

The `response` field gives the watcher dashboard detail panel the model output (truncated to 8000 chars); `response_length` remains so the dashboard can still show the true total size when the body is truncated.

Combine all of the above into a single Bash tool call so the start event, the query, and the completion event run together in one script.

## Step 3: Display the Response

Show the model's response to the user. If `open-wrapper` returned an error (non-zero exit code or stderr indicating a connection failure), tell the user that the Ollama model could not be reached and suggest checking that Ollama is running (`ollama serve`).
