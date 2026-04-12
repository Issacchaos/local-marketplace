# C++ Discovery Agent

## Purpose

Performs the C++ half of RPC discovery. The goal is to find all RPCs registered within C++ managers — their names, HTTP paths, categories, parameters, and which file/line they appear in. Note that the output of some files may be large, so keep that in mind when issuing tool calls.

RPCs are registered in C++ files. Each file has a name like `FortAutomationRpcManager_Athena.cpp`. Use the pattern `*rpc*.cpp` to find them, as different projects may have different naming standards.

Each file will have one or more methods used to register RPCs. They look like `void Register<Context?>HttpCallbacks()` (for example, `RegisterHttpCallbacks()`, `RegisterBabyCorgiCallbacks()`, `RegisterAlwaysOnCallbacks()`).

Each method will contain one or more RPC registrations. They look something like the following example. While most of this will be similar between projects, the actual handler method (fourth argument) may be slightly different. It is not important for discovery, so skip looking at it.

```cpp
// Parameters are usually defined above the HttpCallback, but may not be directly above
// First argument is parameter name, second is parameter type. An optional third parameter is the description.
const FExternalRpcArgumentDesc MessageDesc(TEXT("message"), TEXT("string"), TEXT("The line to print to the log"));
RegisterHttpCallback(
  FName(TEXT("WriteToLog")), // RPC Name
  FHttpPath("/eos/writetolog"), // Http Path
  EHttpServerRequestVerbs::VERB_POST, // Http Verb
  [WeakThis](const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
  {
    if (!WeakThis.IsValid()) { return false; }
    return WeakThis->HttpWriteStringToLogCommand(Request, OnComplete); // C++ Handler
  },
  true,
  TEXT("Cheats"), // Category
  TEXT("raw"),
  { MessageDesc }); // Optional list of parameters
```

---

## Search Protocol (MANDATORY)

**CRITICAL**: ALL file discovery and content searches (that do not target a specific file) MUST follow this protocol. Searches that do not apply exclude patterns WILL cause tool timeouts and failures in Unreal Engine projects due to large generated/cached directories (Content, Intermediate, ThirdParty, etc.).

**Use `Bash` with `rg` (ripgrep) for ALL recursive file and content searches.** Do NOT use the `Glob` tool or `Grep` tool for recursive codebase searches, because:

- The `Glob` tool has **no exclude support** — it will scan into ThirdParty, Intermediate, Content, etc. and time out.
- The `Grep` tool only accepts a **single glob pattern** — it cannot combine an include pattern with multiple exclude patterns.

```yaml
exclude_args:
  - "ThirdParty/"
  - "Intermediate/"
  - "Content/"
  - "Saved/"
  - "DerivedDataCache/"
  - "Binaries/"
  - "Engine/"
  - ".git/"
  - "node_modules/"
```

**File discovery** (finding files by name pattern):
```bash
rg --files --iglob "{include_pattern}" {exclude_args} {targetPath}
```

**Content search** (finding text within files):
```bash
rg "{regex_pattern}" --iglob "{include_pattern}" {exclude_args} -n [-A N] {targetPath}
```

---

## Input

The agent receives a prompt from the orchestrator (spawned via Task tool) containing:

```
targetPath: {string}
excludePatterns: {JSON array of glob strings}
findingsDir: {string}   # e.g., ".rpc/discovery/" or ".rpc/discovery/{project}/"
```

---

## Output

In a large project, the output may be a large number of RPCs. With that in mind, if necessary, write the output to a file so that the caller may read it given there is limited context.

The output should be a JSON object with the following structure:

```json
{
  "files_scanned": 5,
  "cpp_rpcs": {
    "WriteToLog": {
      "name": "WriteToLog",
      "context": "AlwaysOn",
      "category": "Cheats",
      "http_path": "/eos/writetolog",
      "parameters": [
        {"name": "message", "type": "string"}
      ],
      "file": {"path": "path/to/RpcManager_Core.cpp", "line": 26}
    }
  },
  "notes": []
}
```

**Fields**:
- `files_scanned`: Count of unique `*rpc*.cpp` files found.
- `cpp_rpcs`: Map of RPC name to entry. Each entry includes name, context, category, http_path, parameters, and layers (hook = the registration line, endpoint = the handler function implementation).
- `notes`: Informational messages (duplicates, skipped registrations, etc.).

If no files or registrations are found, return:
```json
{"files_scanned": 0, "cpp_rpcs": {}, "notes": ["No *rpc*.cpp files found in {targetPath}"]}
```

**IMPORTANT**: The final line of the response MUST be the JSON object (or a markdown code block containing only the JSON object). The orchestrator parses the last JSON-parseable block from the response.

---

## Findings Cache

The findings cache preserves project-specific patterns discovered during scanning so that subsequent runs can benefit from prior knowledge. The cache is a markdown file at `{findingsDir}cpp-findings.md`.

### Read Findings (Before Scanning)

Before starting the search, attempt to read `{findingsDir}cpp-findings.md`.

- **If the file exists**: Read it and use the documented patterns to inform your search strategy. For example, if the findings say RPC manager files follow the pattern `FortAutomationRpcManager_*.cpp` in a specific directory, search there first. If specific registration function names are documented, use those to refine context detection. The findings are advisory — still perform the full scan, but use them to resolve ambiguities faster.
- **If the file does not exist**: Proceed normally with the default patterns (`*rpc*.cpp`, `RegisterHttpCallback`).

### Write Findings (After Scanning)

After completing discovery and assembling the output JSON, write (or overwrite) `{findingsDir}cpp-findings.md` with the patterns you discovered during this scan. Use your judgment about what is useful to record. Include any information you might be able to use to do this scan again. Good candidates include:

- **File patterns**: The actual naming convention for RPC manager files in this project (e.g., `FortAutomationRpcManager_*.cpp` vs `MyGameRpcManager_*.cpp`)
- **File locations**: Directory paths where RPC files were found
- **Registration patterns**: Registration function names and their signatures (e.g., `RegisterAlwaysOnCallbacks`, `RegisterInGameHttpCallbacks`)
- **Context mapping**: Which file suffixes map to which contexts, and which registration function names disambiguate contexts within a single file
- **Parameter patterns**: How parameters are defined (e.g., `FExternalRpcArgumentDesc` usage patterns)
- **Project-specific quirks**: Anything unusual about this project's RPC registration that deviates from the standard pattern

Keep the file concise and factual. Write what you observed, not general documentation about RPC patterns. Example structure:

```markdown
# C++ RPC Discovery Findings

## File Patterns
- RPC manager files: `FortAutomationRpcManager_*.cpp`
- Located in: `FortniteGame/Source/FortniteGame/Private/Tests/`

## Registration Functions
- RegisterAlwaysOnCallbacks → AlwaysOn context
- RegisterInGameHttpCallbacks → InGame context
- RegisterFrontEndHttpCallbacks → FrontEnd context

## Context Mapping
- `_Core.cpp` → AlwaysOn
- `_Client.cpp` → InGame, FrontEnd (disambiguated by function name)
- `_Server.cpp` → Server

## Notes
- Parameters use FExternalRpcArgumentDesc with TEXT() macros
- 5 RPCs found across 2 manager files
```

**Error handling**: If the Write fails, log a warning and continue — the findings cache is not critical to the scan results.
