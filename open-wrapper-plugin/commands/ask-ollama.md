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

Set a shell variable for the model name (use the `--model` value if provided, otherwise `"default"`), and generate a per-invocation `SESSION_ID` (UUID) that correlates the start and completion events for this single `/ask-ollama` call:

```bash
MODEL_NAME="<model-or-default>"
SESSION_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')
```

Before running the query, POST a start event to the dashboard webhook (fire-and-forget):

```bash
curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{"event_type":"request","command":"ask","status":"start","model":"'"$MODEL_NAME"'","session_id":"'"$SESSION_ID"'","metadata":{"prompt":"'"${PROMPT_TRUNCATED}"'"}}' \
  > /dev/null 2>&1 &
```

Truncate the prompt to 200 characters max for the webhook metadata.

Then run the actual command as a **streamed pipeline** rather than a buffered capture. The output is written to a buffer file line-by-line, and every ~500 ms (or every 16 tokens — whichever comes first) we POST a `streaming` webhook event so the watcher renders a live tokens/s figure on the in-flight agent row. Bracket the whole pipeline with millisecond timestamps so we can still report latency:

```bash
START=$(date +%s%3N)
BUFFER=$(mktemp 2>/dev/null || echo "/tmp/ow-ask-$$.out")
: > "$BUFFER"
TOKEN_COUNT=0
LAST_FLUSH_MS=$START
FLUSH_EVERY_MS=500
FLUSH_EVERY_TOKENS=16

# Stream stdout line-by-line. Each line is written to the buffer and its
# whitespace-delimited tokens are counted. We flush a streaming webhook event
# (cumulative tokens_so_far) every FLUSH_EVERY_MS milliseconds or every
# FLUSH_EVERY_TOKENS tokens — whichever trips first — so the watcher sees
# monotonically-increasing counts without one curl per token.
open-wrapper [--model <model>] ask [-s "<system>"] "<prompt>" 2>&1 \
  | while IFS= read -r line; do
      printf '%s\n' "$line" >> "$BUFFER"
      # shellcheck disable=SC2086
      set -- $line
      TOKEN_COUNT=$((TOKEN_COUNT + $#))
      NOW=$(date +%s%3N)
      ELAPSED_SINCE_FLUSH=$((NOW - LAST_FLUSH_MS))
      TOKENS_SINCE_FLUSH=$((TOKEN_COUNT - LAST_FLUSH_TOKENS))
      if [ "$ELAPSED_SINCE_FLUSH" -ge "$FLUSH_EVERY_MS" ] || [ "$TOKENS_SINCE_FLUSH" -ge "$FLUSH_EVERY_TOKENS" ]; then
        curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper \
          -H "Content-Type: application/json" \
          -d '{"event_type":"streaming","command":"ask","status":"streaming","model":"'"$MODEL_NAME"'","session_id":"'"$SESSION_ID"'","tokens_so_far":'"$TOKEN_COUNT"',"metadata":{"tokens_so_far":'"$TOKEN_COUNT"'}}' \
          > /dev/null 2>&1 &
        LAST_FLUSH_MS=$NOW
        LAST_FLUSH_TOKENS=$TOKEN_COUNT
      fi
    done
END=$(date +%s%3N)
RESPONSE=$(cat "$BUFFER")
rm -f "$BUFFER"
echo "$RESPONSE"
```

Initialize `LAST_FLUSH_TOKENS=0` alongside `TOKEN_COUNT=0` (line above the loop). The `while` loop runs in a subshell on some older Bash versions — if you see `TOKEN_COUNT` always 0 after the loop, use `lastpipe` (`shopt -s lastpipe` on Bash 4.2+) or switch to process-substitution (`done < <(open-wrapper …)`).

Note: `date +%s%3N` yields milliseconds on GNU date (Linux, Windows git bash). On macOS, `%3N` is not supported — fall back to `START=$(($(date +%s) * 1000))` / `END=$(($(date +%s) * 1000))` for whole-second resolution. On macOS you will also want `gdate` for the in-loop `NOW=...` call.

"Tokens" here are whitespace-delimited words from stdout — an approximation of true BPE tokens, but sufficient for the watcher's tokens/s feel. If `open-wrapper` gains a `--stream-tokens` flag that emits one true token per line, swap `$#` for `1` in the counter.

After the command completes, POST a completion event (reusing the same `$SESSION_ID` so the watcher can pair start and completion) that includes the measured `duration_ms`:

```bash
RESP_LEN=${#RESPONSE}
DURATION_MS=$((END-START))
# Truncate the response body to 8000 chars and JSON-escape it (handles backslashes, quotes,
# newlines, tabs, carriage returns, and control chars) so it can be embedded safely in the webhook payload.
RESPONSE_ESCAPED=$(printf '%s' "${RESPONSE:0:8000}" | python3 -c 'import json,sys; sys.stdout.write(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null \
  || printf '%s' "${RESPONSE:0:8000}" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g' -e 's/\r/\\r/g' -e 's/\t/\\t/g')
curl -s -X POST ${OPEN_WRAPPER_WEBHOOK:-http://localhost:1420}/api/open-wrapper \
  -H "Content-Type: application/json" \
  -d '{"event_type":"completion","command":"ask","status":"completed","model":"'"$MODEL_NAME"'","session_id":"'"$SESSION_ID"'","duration_ms":'"$DURATION_MS"',"metadata":{"prompt":"'"${PROMPT_TRUNCATED}"'","response_length":'"$RESP_LEN"',"response":"'"${RESPONSE_ESCAPED}"'"}}' \
  > /dev/null 2>&1
```

The `response` field gives the watcher dashboard detail panel the model output (truncated to 8000 chars); `response_length` remains so the dashboard can still show the true total size when the body is truncated.

Combine all of the above into a single Bash tool call so the start event, the query, and the completion event run together in one script.

## Step 3: Display the Response

Show the model's response to the user. If `open-wrapper` returned an error (non-zero exit code or stderr indicating a connection failure), tell the user that the Ollama model could not be reached and suggest checking that Ollama is running (`ollama serve`).
