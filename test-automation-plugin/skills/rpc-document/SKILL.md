---
name: rpc-document
description: Generates JSON documentation for a single C++ RPC hook by reading its registration and handler implementation. Use when documenting RPC endpoints from C++ source files.
argument-hint: <rpc-name> [source-file]
---

# RPC Document

## Purpose

Generates a JSON documentation object for a single named RPC by reading its registration and handler implementation from the C++ source. Consumes the discovery cache to locate the source file without scanning.

---

## Input

| Argument | Required | Description |
|----------|----------|-------------|
| `$ARGUMENTS[0]` | Yes | RPC name (PascalCase) |
| `$ARGUMENTS[1]` | No | Path to the C++ source file. When provided, the discovery cache is bypassed entirely. |

**Example invocations**:
```
# Cache-assisted lookup
test-engineering:rpc-document GetAllActorsInRadius

# Direct file (no cache needed)
test-engineering:rpc-document GetAllActorsInRadius FortniteGame/Source/FortniteGame/Private/Tests/FortAutomationRpcManager_Core.cpp
```

---

## Search Protocol

Use `Bash` with `rg` (ripgrep) for all content searches. Apply standard exclude patterns:
`--glob "!ThirdParty/" --glob "!Intermediate/" --glob "!Content/" --glob "!Saved/" --glob "!Binaries/" --glob "!Engine/" --glob "!.git/"`

---

## Algorithm

### Step 1: Locate the source file

If `$ARGUMENTS[1]` (a file path) was provided, use it directly as the C++ source file and skip the rest of this step.

Otherwise, attempt to read `.rpc/discovery/summary.json`.

If the file does not exist, stop and report:
```
ERROR: No discovery cache found at .rpc/discovery/.
Either run /rpc-discover to build the cache, or provide the source file path as a second argument:
  test-engineering:rpc-document {RPC_NAME} path/to/FortAutomationRpcManager_Foo.cpp
```

For each module in `summary.modules[]`, read `.rpc/discovery/{module.name}.json` and check if the `rpcs[]` array contains an entry whose `name` matches the requested RPC name. Stop at the first match. The matching entry's `cpp_file` field is the relative path to the C++ source file.

If no match is found in any module, report:
```
ERROR: RPC "{name}" not found in discovery cache.
Either run /rpc-discover to update the cache, or provide the source file path directly:
  test-engineering:rpc-document {RPC_NAME} path/to/FortAutomationRpcManager_Foo.cpp
```

### Step 2: Extract the HTTP registration

In the source file, find the `RegisterHttpCallback` call for this RPC. Search for the RPC name string near `RegisterHttpCallback`:

```bash
rg "RegisterHttpCallback" -A 5 {cpp_file} | grep -A 5 "{RPC_NAME}"
```

Or search directly for the name literal:
```bash
rg "TEXT\(\"{RPC_NAME}\"\)" -n {cpp_file}
```

From the `RegisterHttpCallback` call extract:
- **HTTP method**: `VERB_GET` → `"GET"`, `VERB_POST` → `"POST"`, etc.
- **HTTP path**: the `FHttpPath(...)` string argument

Also read the `FExternalRpcArgumentDesc` variable declarations immediately preceding the call — these name the request parameters and their types.

### Step 3: Extract the handler implementation

The fourth argument of `RegisterHttpCallback` is a lambda that calls the handler method (e.g., `WeakThis->HttpGetAllActorsInRadiusCommand`). Find the handler implementation in the same file:

```bash
rg "Http{RPC_NAME}Command|Http.*Command" -n {cpp_file}
```

Read ~80 lines from the handler's opening brace. From the implementation determine:

- **Request type**: `query` if parameters are read with `GetQueryParam` / `QueryParameters`, `body` if read with `GetJsonBody` / `TryGetStringField`, `none` if no parameters are read
- **Request schema**: parameter names and types; include `"default"` only when the code specifies an explicit default value
- **Response schema**: the JSON fields written by the handler (via `JsonWriter->WriteValue`, `WriteObjectStart`, `WriteArrayStart`, etc.); use `{"type": "..."}` notation

### Step 4: Output

Output exactly this JSON object (no surrounding markdown, no explanation):

```json
{
  "name": "{RPC_NAME}",
  "method": "{HTTP_METHOD}",
  "path": "{HTTP_PATH}",
  "description": "{one sentence — what the endpoint does, without repeating schema details}",
  "request": {
    "type": "{query | body | none}",
    "schema": {}
  },
  "response": {
    "schema": {}
  },
  "notes": ["{any non-obvious edge cases}"]
}
```

**Output rules**:
- `description`: one sentence; must not repeat information already present in the schema
- `schema` values: `{"type": "string|integer|number|bool"}` notation; add `"default"` only when the code specifies one explicitly
- If the response root is always an array (`WriteArrayStart()` at top level), use `[{...}]` as the schema root
- Omit `"notes"` entirely if there are no non-obvious edge cases

---

## Example

Input: `GetAllActorsInRadius`

Output:
```json
{
  "name": "GetAllActorsInRadius",
  "method": "GET",
  "path": "/core/getallactorsinradius",
  "description": "Returns all actors of a given class within a radius of the bot's pawn.",
  "request": {
    "type": "query",
    "schema": {
      "radius": { "type": "integer", "default": 10000 },
      "classname": { "type": "string", "default": "Actor" }
    }
  },
  "response": {
    "schema": [
      {
        "uniquename": { "type": "string" },
        "classname": { "type": "string" },
        "location": {
          "x": { "type": "number" },
          "y": { "type": "number" },
          "z": { "type": "number" }
        },
        "rotation": {
          "x": { "type": "number", "description": "pitch" },
          "y": { "type": "number", "description": "yaw" },
          "z": { "type": "number", "description": "roll" }
        }
      }
    ]
  },
  "notes": ["Returns an empty array if the class name is not found rather than an error response."]
}
```
