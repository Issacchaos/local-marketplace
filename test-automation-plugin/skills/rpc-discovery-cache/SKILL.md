# Discovery Cache Service

## Purpose

The Discovery Cache allows commands that consume RPC discovery results (`/rpc-curate`, `/rpc-scenario`) to skip a full re-scan. The cache is keyed by timestamp. If a cache exists, consumers can use it directly. If no cache exists, a full scan is required.

This service is extracted from the RPC Discovery Scanner to keep cache operations out of the scanner's context during the scan-critical path.

---

## Cache File Location

```
{workspaceRoot}/.rpc/discovery/              # default (no --project)
{workspaceRoot}/.rpc/discovery/{project}/    # when --project is specified
```

The cache lives inside `.rpc/discovery/` at the workspace root. When `--project` is specified by the caller, the cache is scoped to a project-specific subdirectory. This allows multiple projects in the same workspace (e.g., FortniteGame and LyraGame) to maintain independent discovery caches without cross-contamination.

The cache consists of a **summary file** and **per-module files**:

```
.rpc/discovery/                    # flat (no project)
  summary.json
  Core.json
  Client.json
  Server.json

.rpc/discovery/FortniteGame/       # project-scoped
  summary.json
  Core.json
  Client.json
  Valkyrie.json

.rpc/discovery/LyraGame/           # separate project
  summary.json
  Core.json
```

The `.rpc/` directory is safe to add to `.p4ignore` or `.gitignore` — it contains only generated artifacts, not source.

---

## Cache File Schema

The cache uses a **split structure** to avoid polluting agent context when only one module's data is needed. Instead of one monolithic file, the cache consists of:

1. **Summary file** (`.rpc/discovery/summary.json`): Scan metadata, notes, and a module index that tells consumers which per-module files exist.
2. **Per-module files** (`.rpc/discovery/{ModuleName}.json`): The RPCs belonging to that module with their context, layer status, and completeness.

### Summary File Schema (`.rpc/discovery/summary.json`)

```json
{
  "scan_metadata": {
    "timestamp": "string (ISO 8601, when this cache was written)",
    "target_path": "string",
    "files_scanned": "int",
    "rpcs_found": "int",
    "scan_duration_ms": "int",
    "config_source": "string | null",
    "exclude_patterns": ["string"],
    "additional_paths": ["string"]
  },
  "notes": [
    "string (informational messages about the scan)"
  ],
  "modules": [
    {
      "name": "string (module name, e.g. 'Core', 'Frontend')",
      "cpp_source": "string (relative path to the C++ RPC manager .cpp file, e.g. 'FortniteGame/.../FortAutomationRpcManager_Core.cpp' — NOT the cache file path)",
      "library": "string | null (C# library file name, e.g. 'FortTest.FortRpcLibrary.cs', or null if unknown)"
    }
  ]
}
```

### Per-Module File Schema (`.rpc/discovery/{ModuleName}.json`)

```json
{
  "module": "string (module name, matches modules[].name in summary)",
  "cpp_source": "string (relative path to the C++ RPC manager .cpp file — same as modules[].cpp_source in summary)",
  "library": "string | null (C# library file name)",
  "rpcs": [
    {
      "name": "string (canonical PascalCase RPC name)",
      "context": "string (AlwaysOn|InGame|FrontEnd|Server|Unknown)",
      "cpp_file": "string (relative path to the .cpp file where this RPC's RegisterHttpCallback was found)",
      "layers": {
        "hook": "found|missing",
        "endpoint": "found|missing",
        "library": "found|missing"
      },
      "completeness": "full|substantial|partial|missing"
    }
  ]
}
```

**Field descriptions**:
- `timestamp`: The UTC ISO 8601 timestamp when `SaveDiscoveryCache` was called.
- `notes`: Free-text informational messages accumulated during the scan (e.g., missing config files, duplicate registrations skipped, stub files with no callbacks).
- `modules`: One entry per discovered RPC manager module. `cpp_source` is the relative path from the workspace root to the C++ manager `.cpp` file (this is the **source code file**, not the cache file). `library` is the C# library filename (not a full path) or `null` if no library was found for that module.
- Per-module `rpcs[]` entries carry simplified layer data — plain string values (`"found"` or `"missing"`) rather than full objects with file paths and line numbers. The `cpp_file` field is included per-RPC because a single module can span multiple .cpp files — without it, consumers cannot determine which file an RPC was registered in. Other rich fields (`parameters`, `http_path`, `category`, `characteristics`) are omitted from the cache.

---

## Operations

### SaveDiscoveryCache(report, project)

Writes the discovery report to the split cache files under `{workspaceRoot}/.rpc/discovery/` (or `.rpc/discovery/{project}/` when project-scoped).

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `report` | object | The complete discovery report returned by `ScanForRpcs`, including `scan_metadata` and `rpcs`. |
| `project` | string or null | Optional project name for scoping the cache directory. When non-null, files are written to `.rpc/discovery/{project}/`. When null, files are written to `.rpc/discovery/`. |

**Algorithm**:

**Zero tool calls in Steps 1-4.** All data comes from the `report` object passed as a parameter. Do NOT issue Grep, Bash, Read, or any other tool calls to determine module membership — the C++ file path is already present in each RPC's `layers.hook.file` field.

1. **Group RPCs by module**. For each RPC in `report.rpcs`, extract the module name from the C++ file path already present in `rpc.layers.hook.file` (e.g., filename ending `_Core.cpp` → `"Core"`, `_Client.cpp` → `"Client"`). Build a map of `moduleName → [rpcEntries]`. For C#-only RPCs (where `layers.hook.file` is absent), group under `"Unregistered"`.

2. **Build the modules array**. For each unique module:
   ```json
   {
     "name": "Core",
     "cpp_source": "FortniteGame/Source/FortniteGame/Private/Tests/FortAutomationRpcManager_Core.cpp",
     "library": ["FortTest.FortRpcLibrary.cs"]
   }
   ```
   - `name`: The module name derived from the file suffix (e.g., `_Core` → `"Core"`, `_Frontend` → `"Frontend"`).
   - `cpp_source`: Relative path to the C++ manager `.cpp` file from the workspace root. This is the **source code file**, NOT the cache file path. Extract it from the first RPC in this module's `layers.hook.file` field. Example: `"FortniteGame/Source/.../FortAutomationRpcManager_Core.cpp"`, NOT `".rpc/discovery/Core.json"`.
   - `library`: The C# library file(s) (full path, e.g., `"FortniteGame/Source/.../FortTest.FortRpcLibrary.cs"`). Any library that references RPCs in this module should appear here.

3. **Build the summary payload** (`.rpc/discovery/summary.json`):
   ```json
   {
     "scan_metadata": {
       "timestamp": "{current UTC ISO 8601}",
       "target_path": "{targetPath}",
       "files_scanned": "{count}",
       "rpcs_found": "{count}",
       "scan_duration_ms": "{duration}",
       "config_source": "{path or null}",
       "exclude_patterns": ["..."],
       "additional_paths": ["..."]
     },
     "notes": [ "...accumulated scan notes..." ],
     "modules": [ ...module entries... ]
   }
   ```
   - Copy all fields from `report.scan_metadata`, replace (or add) `timestamp` with the current UTC ISO 8601 timestamp. Do NOT include a `generated_at` field — use `timestamp` only.
   - `notes`: Collect all informational messages accumulated during the scan (missing config files, duplicate registrations, stub files, skipped RPCs, etc.). May be empty `[]`.

4. **Build per-module payloads** (`.rpc/discovery/{ModuleName}.json`). For each module, create a file containing:
   ```json
   {
     "module": "Core",
     "cpp_source": "FortniteGame/Source/FortniteGame/Private/Tests/FortAutomationRpcManager_Core.cpp",
     "library": "FortTest.FortRpcLibrary.cs",
     "rpcs": [
       {
         "name": "LoginUser",
         "context": "AlwaysOn",
         "cpp_file": "FortniteGame/Source/FortniteGame/Private/Tests/FortAutomationRpcManager_Core.cpp",
         "layers": {
           "hook": "found",
           "endpoint": "found",
           "library": "found"
         },
         "completeness": "full"
       }
     ]
   }
   ```
   - Each RPC entry carries simplified layer data — plain string values (`"found"` or `"missing"`) only. The `cpp_file` field is the one exception: it is included because a single module may span multiple .cpp files, and consumers need to know which file each RPC came from. Omit all other rich fields: `category`, `http_path`, `parameters`, `characteristics`, `core_layers_present`, `library_file`.

5. **Enumerate expected files before writing**. Before issuing any Write calls, build the complete list of files that will be written:
   ```
   cacheDir = project ? "{workspaceRoot}/.rpc/discovery/{project}/" : "{workspaceRoot}/.rpc/discovery/"
   expectedFiles = ["{cacheDir}summary.json"]
   for each module in modules:
     expectedFiles.push("{cacheDir}{module.name}.json")
   ```
   Log the expected file count: `"Writing {expectedFiles.length} cache files ({modules.length} modules + summary) to {cacheDir}"`

6. **Write ALL cache files in a single message**. Issue Write calls for summary.json AND every per-module JSON file in the same response (parallel Write tool calls). Do NOT write summary.json first and then loop through modules in separate messages — that risks dropping per-module files if the agent stops early.

   ```
   // ALL of these Write calls in ONE message:
   Write(file_path="{cacheDir}summary.json", content=JSON.stringify(summaryPayload, null, 2))
   Write(file_path="{cacheDir}{module1Name}.json", content=JSON.stringify(module1Payload, null, 2))
   Write(file_path="{cacheDir}{module2Name}.json", content=JSON.stringify(module2Payload, null, 2))
   // ... one Write per module, all in the same message
   ```

   After all Write calls return, count successful writes vs. `expectedFiles.length`. If any writes failed, log a warning per failed file but do NOT abort:
   ```
   Warning: Failed to write {failed_count}/{expectedFiles.length} cache files to {cacheDir}
   Missing files: {list of failed file names}
   Discovery results are still available for this session.
   ```

7. Return the cache directory path and write count:
   ```yaml
   cache_path: ".rpc/discovery/"
   files_written: {successful_count}
   files_expected: {expectedFiles.length}
   ```

---

### LoadDiscoveryCache(project)

Reads the summary cache file. Does NOT eagerly load per-module files — consumers load those on demand via `LoadModuleCache(moduleName, project)`.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project` | string or null | Optional project name. When non-null, reads from `.rpc/discovery/{project}/`. When null, reads from `.rpc/discovery/`. |

**Returns**:
```yaml
found: bool                         # Whether the summary cache file exists and is valid JSON
cache_path: string                  # Path checked
report: object | null               # Parsed summary content (null if not found or invalid)
```

**Algorithm**:

1. Determine the cache path:
   ```
   cacheDir = project ? ".rpc/discovery/{project}/" : ".rpc/discovery/"
   summaryPath = cacheDir + "summary.json"
   ```

   Attempt to read `{summaryPath}` using the Read tool.
   - If the file does not exist or is empty, return `{found: false, cache_path: summaryPath, report: null}`.

2. Parse the JSON content. If parsing fails (malformed JSON), treat as not found:
   - Log a warning: `Warning: Discovery cache at {summaryPath} is malformed. It will be ignored.`
   - Return the same "not found" result as step 1.

3. Return:
   ```yaml
   found: true
   cache_path: "{summaryPath}"
   report: <parsed summary object>
   ```

---

### LoadModuleCache(moduleName, project)

Reads a single per-module cache file on demand. Consumers call this when they need the RPC list for a specific module, avoiding loading all modules into context.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `moduleName` | string | The module name (e.g., `"Core"`, `"Client"`), matching a `name` in `summary.modules[]`. |
| `project` | string or null | Optional project name, matching the value used in `SaveDiscoveryCache` and `LoadDiscoveryCache`. |

**Returns**:
```yaml
found: bool                         # Whether the module cache file exists and is valid JSON
module_data: object | null          # Parsed per-module content (null if not found or invalid)
```

**Algorithm**:

1. Determine the module file path:
   ```
   cacheDir = project ? ".rpc/discovery/{project}/" : ".rpc/discovery/"
   modulePath = cacheDir + "{moduleName}.json"
   ```

   Attempt to read `{modulePath}` using the Read tool.
   - If the file does not exist or is empty, return `{found: false, module_data: null}`.

2. Parse the JSON content. If parsing fails, log a warning and return `{found: false, module_data: null}`.

3. Return `{found: true, module_data: <parsed module object>}`.

---

## Consumer Pattern: Using the Cache

Commands that consume discovery results (`/rpc-curate`, `/rpc-scenario`) follow this pattern before invoking `ScanForRpcs`. The `project` parameter must be passed through from the caller's `--project` flag (or `null` if not specified):

```
1. Call LoadDiscoveryCache(project)

2. If NOT found:
   -> Run ScanForRpcs() normally (no cache to use)

3. If found:
   -> Display: "Using cached discovery results from {report.scan_metadata.timestamp}"
   -> Display: "  RPCs: {report.scan_metadata.rpcs_found}, Files: {report.scan_metadata.files_scanned}"
   -> Use cache.report (summary) directly -- skip ScanForRpcs()
   -> Load individual module files on demand via LoadModuleCache(moduleName, project) as needed
```

**On-demand module loading**: When using cached results, consumers only call `LoadModuleCache(moduleName, project)` for the specific modules they need. For example, `/rpc-curate` filtering eligible RPCs can read the summary to get the module list and RPC counts, then load individual module files only for the modules it needs to inspect. This prevents a large monolithic cache from polluting agent context.
