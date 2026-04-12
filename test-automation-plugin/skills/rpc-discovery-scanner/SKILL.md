# RPC Discovery Scanner

## Purpose

The RPC Discovery Scanner is a service that discovers existing RPC implementations across the codebase using a parallel discovery architecture (TD-6). Two independent scans run concurrently: C++ discovery (grep for `RegisterHttpCallback` registrations + detailed parameter/context extraction) and C# library discovery (grep for wrapper methods in `*RpcLibrary*.cs`). Results are merged by canonical RPC name into a unified inventory with completeness tracking across all three implementation layers (hook, endpoint, library).

This service is consumed by the `/rpc-discover` command (REQ-F-24), the `/rpc-curate` command (for finding complete RPCs to learn patterns from), and the `/rpc-scenario` command (for filtering existing RPCs from suggestions).

---

## Search Protocol (MANDATORY)

**All searches in this service MUST use `Bash` with `rg` (ripgrep).** Do NOT use the `Glob` tool or `Grep` tool for recursive codebase searches — they cannot apply multiple exclude patterns and will time out on Unreal Engine projects.

Every search operation receives an `excludePatterns` array from the caller — the union of built-in excludes, config `additional_excludes`, and user-provided `--exclude` flags. The caller builds this list; the scanner MUST propagate it to every agent and search operation.

---

## Operations

### ScanForRpcs

Main entry point. Runs both passes and returns a complete discovery report.

**Signature**: `ScanForRpcs(targetPath, excludePatterns, config?, findingsDir?)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `targetPath` | string | Root directory to scan. If empty, defaults to the current working directory. |
| `excludePatterns` | string[] | Glob patterns to exclude from scanning (e.g., `["ThirdParty/", "Generated/"]`). Optional. |
| `config` | object or null | Pre-loaded project config object (from the caller's Step 2). When provided, Step 1 below is skipped entirely — the scanner uses this config to build the suffix-to-context map. When `null` or omitted, the scanner loads config itself. |
| `findingsDir` | string or null | Path to the findings cache directory (e.g., `.rpc/discovery/` or `.rpc/discovery/{project}/`). Passed through to both discovery agents so they can read/write pattern findings. When `null`, agents skip the findings cache. |

**Returns**: A structured RPC Discovery Report (see Report Format section).

**Algorithm** (follow these steps exactly):

#### Step 1: Load Configuration

**If the `config` parameter was provided by the caller, skip this entire step** — use the provided config object directly and proceed to Step 1 item 2 (build the suffix-to-context lookup map).

Otherwise, load the project config file to resolve context definitions. This is a **direct file read**, NOT a search.

1. Try to load a project-specific config by reading a known path:
   - Use `Bash: ls .rpc/patterns/` to check if the directory exists and list its subdirectories
   - If a subdirectory exists (e.g., `.rpc/patterns/EOSDemo/`), read: `Read(".rpc/patterns/{projectName}/config.yaml")`
   - If `.rpc/patterns/` does not exist or has no subdirectories, skip to step 2

2. Try to load the workspace default config:
   ```
   Read(".rpc/config.yaml")
   ```
   If this Read **fails** (file not found), no config exists yet. This is not an error — proceed to step 3.

3. If neither project-specific nor default config was found: proceed with built-in defaults (AlwaysOn=_Core, InGame=_Client, FrontEnd=_Client, Server=_Server). Display an informational note:
   ```
   Note: No config found in .rpc/. Using built-in context defaults.
   Run /rpc-curate to create a project-specific configuration.
   ```

2. Build a suffix-to-context lookup map from the config's `contexts` list:
   ```
   "_Core" -> [{name: "AlwaysOn", category_enum: "EFortRpcCategory::CoreCommands"}]
   "_Client" -> [{name: "InGame", category_enum: "EFortRpcCategory::GameplayActions"},
                 {name: "FrontEnd", category_enum: "EFortRpcCategory::UICommands"}]
   "_Server" -> [{name: "Server", category_enum: "EFortRpcCategory::ServerCommands"}]
   ```

   Note: A suffix may map to multiple contexts (e.g., `_Client` maps to both InGame and FrontEnd). The C++ detailed analysis resolves the ambiguity by reading the registration function name (`RegisterInGameHttpCallbacks` vs `RegisterFrontEndHttpCallbacks`).

#### Step 2: Spawn Parallel Discovery Agents

Spawn two Task agents **simultaneously in a single message** (both tool calls in the same response — do NOT send separate messages). This achieves true parallelism: the C++ agent and C# agent run concurrently.

**IMPORTANT**: Each Task agent receives the FULL algorithm as part of its prompt. The agent algorithms were loaded earlier via `Skill(test-engineering:rpc-cpp-discovery)` and `Skill(test-engineering:rpc-csharp-discovery)`. You MUST include the complete algorithm in each Task prompt because Task-spawned agents do not inherit skills from the parent context.

**Agent 1 — C++ Discovery** (algorithm from `Skill(test-engineering:rpc-cpp-discovery)`):

Construct the Task prompt by including the full C++ Discovery Agent algorithm followed by the parameters:
```
You are the C++ Discovery Agent. Follow the algorithm below exactly.

<algorithm>
{paste the FULL content of the rpc-cpp-discovery skill here — including Search Protocol, Algorithm, Output Format, and Findings Cache sections}
</algorithm>

Execute this algorithm with the following parameters:

targetPath: {targetPath}
excludePatterns: {JSON.stringify(excludePatterns)}
configMap: {JSON.stringify(configMap)}
findingsDir: {findingsDir or "null" if not provided}
```

Use `subagent_type: "general-purpose"` for the Task tool call.

The agent runs Pass 1 (single rg call for `RegisterHttpCallback` — no separate file listing call) followed by Pass 2 (per-file parameter/context/endpoint extraction with batched parallel reads of 4 files per message, no .h header reads) and returns a JSON object:
```json
{
  "files_scanned": int,
  "cpp_rpcs": { "RpcName": { CppRpcEntry }, ... },
  "notes": ["..."]
}
```

**Agent 2 — C# Discovery** (algorithm from `Skill(test-engineering:rpc-csharp-discovery)`):

Construct the Task prompt by including the full C# Discovery Agent algorithm followed by the parameters:
```
You are the C# Discovery Agent. Follow the algorithm below exactly.

<algorithm>
{paste the FULL content of the rpc-csharp-discovery skill here — including Search Protocol, Algorithm, Output Format, and Findings Cache sections}
</algorithm>

Execute this algorithm with the following parameters:

targetPath: {targetPath}
excludePatterns: {JSON.stringify(excludePatterns)}
findingsDir: {findingsDir or "null" if not provided}
```

Use `subagent_type: "general-purpose"` for the Task tool call.

The agent searches for `*RpcLibrary*.cs` files, parses wrapper methods, and returns a JSON object:
```json
{
  "files_scanned": int,
  "rpcs": { "RpcName": [ { "file": "...", "line": int, "method_name": "...", "async": bool }, ... ], ... },
  "notes": ["..."]
}
```

#### Step 3: Collect Agent Results

Wait for both agents to complete. Parse each agent's JSON output from the last JSON-parseable block in its response.

```
cppResult    = parse JSON from cpp-discovery-agent response
csharpResult = parse JSON from csharp-discovery-agent response
```

Extract the maps:
- `cppRpcs`      = `cppResult.cpp_rpcs`   (map of rpcName → CppRpcEntry)
- `csharpRpcs`   = `csharpResult.rpcs`    (map of rpcName → callsite[])

Collect notes from both agents. These feed into the cache's `notes` array and any displayed warnings.

If an agent fails to return parseable JSON, treat its result as empty maps and add a warning note:
```
WARNING: {cpp|csharp}-discovery-agent failed to return a valid result. {layer(s)} discovery data will be missing from this report.
```
Do not abort — proceed to the merge step with whatever data was collected.

Compute `files_scanned` as `cppResult.files_scanned + csharpResult.files_scanned`.

#### Step 4: Merge & Reconcile

**Zero tool calls in this step.** All data comes from the agent results parsed in Step 3. Do NOT issue any Grep, Bash, Read, or other tool calls during the merge — it is a pure in-memory map operation.

Invoke `MergeDiscoveryResults(cppRpcs, csharpRpcs)` to combine all discovery results into a unified RPC inventory.

This step:
1. Unions all unique RPC names across both maps
2. Assembles a unified entry per RPC with layers from whichever maps have data
3. Attaches characteristics (async) from C# callsite data
4. Computes completeness per RPC

Result: A list of unified RPC entries (see Merge & Reconcile section).

#### Step 5: Build and Return Report

Assemble the final report from the merged results:

```json
{
  "scan_metadata": {
    "target_path": "{targetPath}",
    "files_scanned": "{count of unique .cpp + .cs files examined}",
    "rpcs_found": "{total RPCs discovered}",
    "timestamp": "{ISO 8601 timestamp}"
  },
  "rpcs": [ ... ]
}
```

---

## Delegated Discovery Operations

The detailed scanning algorithms are loaded via skills. This service **only** spawns agents and merges results — it does NOT implement scanning logic. Do NOT execute the agent algorithms directly; delegate via Task tool calls with the full algorithm embedded in the prompt.

| Operation | Skill | Description |
|-----------|-------|-------------|
| C++ Discovery (Pass 1 + Pass 2) | `test-engineering:rpc-cpp-discovery` | Single rg call for `RegisterHttpCallback`, then batched parallel file reads (4 per message, no .h reads) |
| C# Discovery | `test-engineering:rpc-csharp-discovery` | Library wrapper methods in `*RpcLibrary*.cs` files |

---

## Merge & Reconcile

### MergeDiscoveryResults(cppRpcs, csharpRpcs)

**Zero tool calls in this entire function.** All inputs are in-memory maps from agent results. Do NOT issue Grep, Bash, Read, or any other tool calls.

Combines independent discovery results from C++ and C# library scans into a unified RPC inventory. This is where all layers are linked by canonical RPC name.

**Algorithm**:

#### Step 1: Union All RPC Names

Collect all unique RPC names from both maps:

```
allRpcNames = union(keys(cppRpcs), keys(csharpRpcs))
```

Sort alphabetically.

#### Step 2: Assemble Unified Entries

For each RPC name in `allRpcNames`:

1. **Hook and Endpoint layers**: If `cppRpcs[name]` exists, use its hook and endpoint layer data. Otherwise, set both to `status: "missing"`.

2. **Library layer**: If `csharpRpcs[name]` exists, set `status: "found"` with all callsites. Otherwise, set `status: "missing"` with empty callsites array.

3. **Context, category, http_path, parameters**: Taken from `cppRpcs[name]` if available. For C#-only RPCs (no C++ registration), set `context: "Unknown"`, `category: null`, `http_path: null`, `parameters: []`.

#### Step 3: Determine Characteristics

For each unified entry:

**Async detection**: Set `characteristics.async = true` if any callsite in the library layer has `async: true`. If no C# library method was found at all (library status = missing), set `characteristics.async = null` (unknown, not definitively false). Downstream consumers should treat `null` as "not determined" rather than "definitely sync".

#### Step 4: Determine Completeness

Count the number of layers with status `found`:

| Found Layers | Completeness |
|---|---|
| 3 of 3 | `full` |
| 2 of 3 | `substantial` |
| 1 of 3 | `partial` |
| 0 of 3 | `missing` |

Additionally, set `core_layers_present` to `true` if both the hook (Layer 1) and endpoint (Layer 2) layers have status `found`. This flag is used by downstream consumers (e.g., `/rpc-curate`) to determine eligibility for pattern extraction independently of the library layer.

#### Merge Output (Per RPC)

```json
{
  "name": "BotAttackTarget",
  "context": "InGame",
  "category": "GameplayActions",
  "http_path": "/botattacktarget",
  "parameters": [
    {"name": "targetId", "type": "string"},
    {"name": "damage", "type": "int"},
    {"name": "weaponIds", "type": "string[]"},
    {"name": "isCritical", "type": "bool"}
  ],
  "layers": {
    "hook": {"status": "found", "file": ".../EOSDemoRpcManager_Client.cpp", "line": 26},
    "endpoint": {"status": "found", "file": ".../EOSDemoRpcManager_Client.cpp", "line": 80},
    "library": {
      "status": "found",
      "callsites": [
        {"file": ".../SampleRpcLibrary.cs", "line": 51, "method_name": "BotAttackTarget", "async": false}
      ]
    }
  },
  "characteristics": {
    "async": false
  },
  "completeness": "full",
  "core_layers_present": true
}
```

---

## Report Format

The discovery report structure is demonstrated by this example (the example is the schema — all fields and types are visible):

```json
{
  "scan_metadata": {
    "target_path": "rpc-scaffold/test_fixtures",
    "files_scanned": 2,
    "rpcs_found": 5,
    "timestamp": "2026-02-18T10:30:00Z"
  },
  "rpcs": [
    {
      "name": "BotAttackTarget",
      "context": "InGame",
      "category": "GameplayActions",
      "http_path": "/botattacktarget",
      "parameters": [
        {"name": "targetId", "type": "string"},
        {"name": "damage", "type": "int"},
        {"name": "weaponIds", "type": "string[]"},
        {"name": "isCritical", "type": "bool"}
      ],
      "layers": {
        "hook": {"status": "found", "file": ".../EOSDemoRpcManager_Client.cpp", "line": 26},
        "endpoint": {"status": "found", "file": ".../EOSDemoRpcManager_Client.cpp", "line": 80},
        "library": {
          "status": "found",
          "callsites": [
            {"file": ".../SampleRpcLibrary.cs", "line": 51, "method_name": "BotAttackTarget", "async": false}
          ]
        }
      },
      "characteristics": {
        "async": false
      },
      "completeness": "full",
      "core_layers_present": true
    }
  ]
}
```

The test fixtures contain 5 RPCs (BotAttackTarget, DebugDumpState, GetPlayerStatus, LoginUser, UIOpenMenu). See `rpc-scaffold/test_fixtures/` for full validation data.

---

## Performance Guidance

### REQ-NF-1 Target: 100 files in under 10 seconds

True parallelism is achieved by spawning the C++ Discovery Agent and C# Discovery Agent as separate Task tool calls in the same message. The orchestrating agent (this scanner service) blocks until both agents return, then merges their results.

#### Agent-Level Parallelism

- **C++ agent and C# agent run concurrently**: Both are spawned in the same Task tool message. Neither blocks the other. C++ detailed analysis (file reads) and C# grep scans execute simultaneously.
- **Independent failure**: If one agent fails or returns no results, the other still completes and contributes to the final report. The merge step handles missing data gracefully.
- **Merge is lightweight**: The merge step is a simple map union keyed by RPC name — no file I/O required.

#### C++ Agent Internal Optimizations

1. **Single rg call in Pass 1**: One call to search all `*rpc*.cpp` files for `RegisterHttpCallback`. File count is derived from the output — no separate `rg --files` call. Do NOT issue per-file calls.
2. **Group by file**: Process all RPCs from the same file together to read each file only once.
3. **Parallel file reads in batches of 4**: Issue Read calls for exactly 4 files per message (or all remaining if fewer than 4). This is the biggest performance win for the C++ agent, which previously read files sequentially (43 serial tool calls, 9+ minutes). Parallel reads can cut wall-clock time roughly in half.
4. **No per-file grep calls in Pass 2**: Extract function boundaries (Step 4) and handler locations (Step 5) from already-read file content instead of issuing separate Grep or Bash calls per file. This eliminates ~2 tool calls per file.
5. **No .h header reads**: Endpoint layer status is determined from the `.cpp` implementation only. Header declaration verification is deferred to `/rpc-curate`. This eliminates ~1 Read call per file.
6. **Excludes in the command**: Apply `--glob "!{pattern}"` arguments directly in the rg call — never post-filter.

#### C# Agent Internal Optimizations

1. **Excludes in the command**: Same as C++ agent — apply excludes directly in rg, not as a post-filter.

#### Benchmarking

When testing performance:
- Measure wall-clock time from `ScanForRpcs` invocation to report return
- The dominant cost is C++ detailed analysis (file reads); C# scans are fast grep-only operations
- Target: Both agents complete in under 10 seconds for 100 files combined; merge is near-instant
- If targets are not met, check that exclude patterns are preventing scans into Content, Intermediate, and ThirdParty directories

---

## Edge Cases

### Multiple Registration Functions in One File

A single .cpp file may contain multiple registration functions (e.g., `RegisterInGameHttpCallbacks` and `RegisterFrontEndHttpCallbacks`). Pass 2 Step 4 resolves context per-RPC using function boundaries. Example: `EOSDemoRpcManager_Client.cpp` has `BotAttackTarget`/`GetPlayerStatus` in `RegisterInGameHttpCallbacks` (-> InGame) and `UIOpenMenu` in `RegisterFrontEndHttpCallbacks` (-> FrontEnd).

### Registration Without Parameters / Malformed Registration

- **No parameters**: If no `TArray` declaration precedes `RegisterHttpCallback`, the block starts at the registration itself; parameters array is empty.
- **Malformed**: If `FName(TEXT("..."))` cannot be parsed (e.g., uses a variable), log a warning with file:line and skip the registration.

### Missing C++ Header File

If `.h` doesn't exist at the derived path, still mark endpoint as `found` if the implementation is found (implementation is the primary indicator). Add note: `"endpoint_note": "Implementation found but header declaration not located"`.

### Sync + Async C# Methods for Same RPC

Both sync (`LoginUser`) and async (`LoginUserAsync`) variants are recorded as separate callsites under the same canonical name. The merge step sets `characteristics.async = true` if any callsite has `async: true`.

### C#-Only RPCs (No C++ Registration)

The merge step creates entries with `hook: missing`, `endpoint: missing`, `context: "Unknown"`, empty parameters. These appear as `completeness: "partial"`, `core_layers_present: false` — visible in the report but not eligible for pattern extraction.

### No Config File Found

Uses built-in defaults (`_Core` -> AlwaysOn, `_Client` -> InGame/FrontEnd, `_Server` -> Server) and logs an informational message.

---

## Discovery Cache

Cache operations (`SaveDiscoveryCache`, `LoadDiscoveryCache`, `LoadModuleCache`) and the cache file schema are defined in the `test-engineering:rpc-discovery-cache` skill.

The scanner's `ScanForRpcs` operation returns a report; the **caller** (e.g., `/rpc-discover` command) is responsible for invoking cache operations. The scanner itself does not read or write cache files.

---

## Error Handling

All errors follow the standard format from REQ-NF-5.

### Target Path Not Found

```
ERROR: Target path not found
Path: {targetPath}
Issue: The specified scan target directory does not exist or is not accessible.
Remediation:
  1. Verify the path exists and is readable
  2. Use an absolute path or a path relative to the workspace root
  3. Run /rpc-discover without a path argument to scan the workspace root
```

### Glob Tool Returns No Files

This is not an error -- it is an expected condition for new projects or directories without RPC managers. Return an empty report with an informational message.

### Grep Tool Failure

If the Grep tool returns an error (not empty results, but an actual error):

```
ERROR: Search failed
Tool: Grep
Issue: {error_message_from_tool}
Remediation:
  1. Check that the target directory is accessible
  2. Verify file permissions
  3. Try scanning a smaller subdirectory to isolate the issue
```

### File Read Failure in Pass 2

If a file cannot be read during Pass 2 (permissions, locked by another process):

```
WARNING: Could not read {file_path} for detailed analysis.
Issue: {error_message}
The following RPCs from this file will have incomplete metadata:
  - {rpc_name_1}
  - {rpc_name_2}
Continuing with remaining files.
```

Do not abort the entire scan. Mark affected RPCs with partial metadata and continue.
