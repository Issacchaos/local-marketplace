---
name: rpc-discover
description: "Discover and inventory existing RPC registrations across the codebase"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - Task
  - Skill(test-engineering:rpc-discovery-scanner)
  - Skill(test-engineering:rpc-discovery-cache)
  - Skill(test-engineering:rpc-cpp-discovery)
  - Skill(test-engineering:rpc-csharp-discovery)
  - Skill(test-engineering:rpc-document)
---

# /rpc-discover

Discover and inventory existing RPC registrations across the codebase. This command orchestrates the RPC Discovery Scanner service to perform a two-pass scan (fast grep-based discovery followed by on-demand detailed analysis), then formats and presents the results.

## Usage

```
/rpc-discover [target-path] [--path=additional-path] [--exclude=glob-pattern] [--no-cache] [--project=<name>]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `target-path` | No | Root directory to scan for RPC registrations. Defaults to the current workspace root if omitted. |
| `--path=<additional-path>` | No | Additional search path to include in the scan. Can be specified multiple times (e.g., `--path=Source/CustomModule --path=Source/Experimental`). Merged with the default search paths from config. |
| `--exclude=<glob-pattern>` | No | Glob pattern to exclude from scanning. Can be specified multiple times (e.g., `--exclude="ThirdParty/" --exclude="Generated/"`). Merged with the default excludes from config. |
| `--no-cache` | No | Skip writing the discovery cache files (JSON) after scanning. Results are displayed but not saved to `.rpc/discovery/`. Note: pattern findings files (`cpp-findings.md`, `csharp-findings.md`) are still written by the discovery agents regardless of this flag — they capture reusable project knowledge, not scan results. |
| `--project=<name>` | No | Project name for scoping the discovery cache. When specified, cache files are written to `.rpc/discovery/{name}/` instead of `.rpc/discovery/`. Use this when scanning multiple projects in the same workspace (e.g., `--project=FortniteGame` and `--project=LyraGame` as separate scans). If omitted, cache is written to `.rpc/discovery/` (flat, unscoped). |

### Argument Parsing Rules

1. A bare path argument (no `--` prefix) is treated as the `target-path`.
2. If no `target-path` is provided and no `--path` flags are present, scan from the workspace root.
3. If both `target-path` and `--path` are provided, scan the `target-path` first, then also scan all `--path` directories. Results are merged and deduplicated by RPC name.
4. `--exclude` patterns are applied during file discovery before any scanning occurs.
5. All paths are resolved relative to the workspace root unless they are absolute.
6. If `--project` is specified, the discovery cache is scoped to `.rpc/discovery/{project}/`. The project name must be a valid directory name (alphanumeric, hyphens, underscores). This allows multiple projects in the same workspace to maintain independent discovery caches.

## Workflow

Execute the following steps in order. This command **delegates** scanning logic to the RPC Discovery Scanner (`Skill(test-engineering:rpc-discovery-scanner)`) and uses C++ and C# discovery agents (`Skill(test-engineering:rpc-cpp-discovery)`, `Skill(test-engineering:rpc-csharp-discovery)`) for the actual scans. It does NOT implement scanning logic itself.

### Step 0: Load Required Skills

Load all required skill documents by calling these skills in a **single message** (parallel Skill tool calls):

1. `Skill(test-engineering:rpc-discovery-scanner)` — scanning orchestration and merge algorithm
2. `Skill(test-engineering:rpc-cpp-discovery)` — C++ agent algorithm (will be embedded in Task prompt)
3. `Skill(test-engineering:rpc-csharp-discovery)` — C# agent algorithm (will be embedded in Task prompt)
4. `Skill(test-engineering:rpc-discovery-cache)` — cache write/read algorithm (used in Step 3.5)

After all four skills load, their content is available in your context for the remaining steps. Skills 1 and 4 are executed directly by the orchestrator (this agent). Skills 2 and 3 are **not executed directly** — they are loaded solely so their full text can be copy-pasted into the Task prompts when spawning discovery agents in Step 3 (Task-spawned agents do not inherit parent skills).

### Step 1: Parse Arguments

Parse the user's input to extract:

- `targetPath`: The positional path argument, or workspace root if omitted.
- `additionalPaths`: Array of strings from `--path` flags (may be empty).
- `excludePatterns`: Array of glob strings from `--exclude` flags (may be empty).
- `noCache`: Boolean, true if `--no-cache` is present.
- `project`: String from `--project` flag, or `null` if omitted. Must be a valid directory name (alphanumeric, hyphens, underscores) if specified.

Validate that all specified paths exist and are accessible directories:

```
For each path in [targetPath] + additionalPaths:
  Use Bash to verify the directory exists:
    Bash: ls {resolvedPath}
  If the directory does not exist or is not accessible:
    Display error:
      ERROR: Path not found
      Path: {resolvedPath}
      Issue: The specified directory does not exist or is not accessible.
      Remediation:
        1. Verify the path exists and is readable
        2. Use an absolute path or a path relative to the workspace root
        3. Run /rpc-discover without a path argument to scan the workspace root
    Abort the command.
```

Validate that `--exclude` patterns are syntactically valid glob patterns (no error if they match nothing -- that is normal).

### Step 2: Load Configuration

Load the project configuration file to get context definitions, naming conventions, and any pre-existing search path or exclude overrides.

#### 2a: Apply Built-in Default Excludes

**Always** start with the following built-in exclude patterns. These apply on every run regardless of whether a config file exists. Unreal Engine projects contain large generated/cached directories that never have RPC source files, and scanning them causes tool timeouts.

```yaml
built_in_excludes:
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

Initialize the effective exclude list with these built-in excludes:
```
effectiveExcludes = [...built_in_excludes]
```

#### 2b: Load Config File

Load `config.yaml` using **direct Read calls only** — do NOT use Glob, Grep, or any search to find the config file. Try these known paths in order:

1. **Project-specific config**: Use `Bash: ls .rpc/patterns/` to check if the directory exists. If it does, read the first subdirectory's config:
   ```
   Read(".rpc/patterns/{projectName}/config.yaml")
   ```
   If `.rpc/patterns/` does not exist, skip to step 2.

2. **Default config from .rpc folder**: Read the workspace-level default config:
   ```
   Read(".rpc/config.yaml")
   ```
   If the Read **fails** (file not found), no config exists yet. Proceed with built-in defaults (Step 2c will display a note).

If a config is found and has a `search_config` section, merge its values:

```yaml
# Example config.yaml search_config section
search_config:
  base_paths:
    - "Source/FortniteGame"
  additional_excludes:
    - "GeneratedCode/"
    - "ExternalDependencies/"
```

#### 2c: Merge Excludes and Paths

Merge strategy (layered, additive):
1. Start with built-in defaults (always present)
2. Add `additional_excludes` from config (if config has `search_config` section)
3. Add user-provided `--exclude` flags
4. Deduplicate the combined list

```
effectiveExcludes = deduplicate(built_in_excludes + config.additional_excludes + user_excludes)
```

For paths:
- `base_paths` from config are used as default scan directories if no `target-path` is specified.
- User-provided `--path` values are added to (not replacing) config base_paths.

If no config is found at all, the built-in excludes still apply. Display an informational note:

```
Note: No project pattern config found. Using default context mappings.
Built-in directory excludes are active (ThirdParty, Intermediate, Saved, etc.).
Run /rpc-curate to create a project-specific configuration.
```

### Step 3: Invoke RPC Discovery Scanner

Delegate the actual scanning work to the RPC Discovery Scanner algorithm (loaded from `Skill(test-engineering:rpc-discovery-scanner)` in Step 0). Follow the `ScanForRpcs` algorithm from that skill.

Record the start time before invoking the scanner (use `Bash` with a date command or track via prompt context).

Compute the findings directory path for the pattern findings cache:
```
findingsDir = project ? ".rpc/discovery/{project}/" : ".rpc/discovery/"
```

Invoke the scanner's `ScanForRpcs` operation with:
- `targetPath`: The resolved target path (or workspace root)
- `excludePatterns`: The merged exclude patterns (config + user overrides)
- `config`: The config object loaded in Step 2 (pass it through so the scanner skips its own redundant config load)
- `findingsDir`: The computed findings directory path (same as the cache directory — agents will read/write `cpp-findings.md` and `csharp-findings.md` here)

The scanner algorithm tells you to spawn parallel discovery agents via Task tool. When constructing Task prompts, include the **full agent algorithm** from the skills you loaded in Step 0 (`test-engineering:rpc-cpp-discovery` for the C++ agent, `test-engineering:rpc-csharp-discovery` for the C# agent). This is required because Task-spawned agents do not inherit skills from the parent context.

Do NOT implement scanning logic here — the scanner algorithm and its agents handle all grep patterns, file discovery, and metadata extraction. RPCs found in any phase are included — C#-only RPCs (no C++ registration) and C++-only RPCs (no C# wrapper yet) are both visible.

If additional `--path` directories were specified, run the scanner against each additional path and merge results. When the same RPC name appears across paths, union their layer data (e.g., if path A has the C++ layers and path B has the C# layers, combine them into one entry). If the same layer is found in multiple paths, keep the first occurrence and log a warning.

Record the end time after scanning completes and compute the scan duration.

The scanner returns a structured report with:
- `scan_metadata`: Files scanned count, RPC count, timestamp
- `rpcs[]`: Array of RPC entries with name, context, category, http_path, parameters, layers, characteristics, and completeness

### Step 3.5: Save Discovery Cache

Unless `--no-cache` was specified, persist the scan results to `.rpc/discovery/` so that `/rpc-curate` and `/rpc-scenario` can reuse them without re-scanning.

**Execute SaveDiscoveryCache inline** — follow the `SaveDiscoveryCache` algorithm from the `test-engineering:rpc-discovery-cache` skill (loaded in Step 0) directly using Write tool calls. Do NOT spawn a Task agent or subagent for cache writes. The cache write logic is simple (group RPCs from report data, build JSON payloads, write files) and spawning an agent adds unnecessary round-trip overhead. Pass the `project` value (string or `null`) so the cache is written to the correct scoped directory.

This operation:
1. Groups RPCs by module using data already in the report (zero file I/O for grouping).
2. Writes `.rpc/discovery/summary.json` with scan metadata, notes, and module index.
3. Writes one `.rpc/discovery/{ModuleName}.json` per module with simplified RPC entries.
4. All Write calls (summary + all modules) MUST be issued in a single message — see the Discovery Cache service for details.

If `--no-cache` is set, skip this step entirely.

After the cache write (or skip), continue to Step 4. Any write failure from `SaveDiscoveryCache` is a warning only — it does not affect the display output.

The cache path and write count are included in the Step 5 metadata footer (see Step 5).

### Step 4: Format and Display Results

#### 4a: Handle Empty Results

If the scanner returns zero RPCs, display a helpful informational message and exit:

```
RPC Discovery Report
====================

No RPC registrations found.

Scanned: {files_scanned} files in {targetPath}
Duration: {duration}

This is expected for:
  - New projects that haven't added RPCs yet
  - Directories that don't contain RPC registration files (*Rpc*.cpp)

Suggestions:
  - Verify the target path contains your RPC source files
  - Check that your C++ files follow the *Rpc*.cpp naming convention (e.g., *RpcManager_Core.cpp, *RpcComponent_Overlay.cpp)
  - Try specifying a different path: /rpc-discover path/to/source
  - If using a custom file naming convention, check config.yaml settings
```

Do NOT treat zero results as an error. Exit gracefully.

#### 4b: Format Human-Readable Table (Default Output)

Sort the RPCs alphabetically by name and display in a formatted table:

```
RPC Discovery Report ({rpc_count} RPCs found in {files_scanned} files)
=====================================================================
Name              Context    Params                      Layers    Complete
--------------------------------------------------------------------------------
BotAttackTarget   InGame     targetId:str,damage:int,    @@@       Yes
                             weaponIds:str[],
                             isCritical:bool
DebugDumpState    AlwaysOn   category:str,verbose:bool   @@@       Yes
GetPlayerStatus   InGame     playerId:str                @@@       Yes
LoginUser         AlwaysOn   username:str,password:str   @@@       Yes
UIOpenMenu        FrontEnd   menuName:str,               @@@       Yes
                             forceRefresh:bool

@ = layer present, O = layer missing  |  Layers: Hook/Endpoint/Library

Scan metadata:
  Target:    {targetPath}
  Files:     {files_scanned} C++ manager files scanned
  Duration:  {duration_formatted}
  Timestamp: {ISO 8601 timestamp}
```

**Table formatting rules**:

1. **Name column**: The canonical PascalCase RPC name. Left-aligned, max 18 characters.
2. **Context column**: The registration context (AlwaysOn, InGame, FrontEnd, Server). Left-aligned, max 10 characters.
3. **Params column**: Comma-separated `name:type` pairs. Abbreviate types for display:
   - `string` -> `str`
   - `int` -> `int`
   - `float` -> `float`
   - `bool` -> `bool`
   - `string[]` -> `str[]`
   - `int[]` -> `int[]`
   - `float[]` -> `float[]`
   - `bool[]` -> `bool[]`
   - `object[]` -> `obj[]`
   - `object` -> `obj`
   If params exceed column width, wrap to the next line with appropriate indentation.
4. **Layers column**: Three characters representing the three layers in order: Hook, Endpoint, Library.
   - `@` = layer is present (found)
   - `O` = layer is missing
   - Example: `@@O` means Hook found, Endpoint found, Library missing
5. **Complete column**: `Yes` if all 3 layers found (`full`), `No` if any layer missing (`partial`).

After the table, display the scan metadata summary.

### Step 5: Display Scan Metadata

After the table (or JSON write), always display a summary footer:

```
Scan complete.
  RPCs found:    {rpc_count}
  Files scanned: {files_scanned} C++ manager files
  Duration:      {duration_seconds}s
  Complete RPCs: {full_count}/{rpc_count} (all 3 layers present)
  Partial RPCs:  {partial_count}/{rpc_count} (missing layers)
  Cache:         {cache_line}
```

Where `{cache_path}` is `.rpc/discovery/{project}/` if `--project` was specified, or `.rpc/discovery/` otherwise. `{cache_line}` is one of:
- `Saved to {cache_path} ({files_written}/{files_expected} files)` — when the cache was written successfully (full or partial)
- `Skipped (--no-cache)` — when `--no-cache` was specified
- `Write failed (see warning above)` — when `SaveDiscoveryCache` returned `files_written: 0`

If any RPCs have partial completeness, list the missing layers:

```
Incomplete RPCs:
  DebugDumpState   - missing: library
  UIOpenMenu       - missing: endpoint, library
```

### Step 5.5: Validate Cache Write Count

After displaying results, verify the cache write completed fully (unless `--no-cache` was specified, in which case skip this step entirely).

Use the `files_written` and `files_expected` values returned by `SaveDiscoveryCache` in Step 3.5:

1. If `files_written == files_expected`: Cache is complete. No further action needed.

2. If `files_written < files_expected`: Some per-module files were not written. Display the warning from SaveDiscoveryCache (which lists the missing file names). Then issue Write calls **only** for the missing files — the payloads were already built in Step 3.5, so this is a retry of the failed writes with no additional data gathering.

3. If `files_written == 0` and `files_expected > 0`: The entire cache write failed. Display a single warning and proceed — do not retry.

This validation uses data already collected during Step 3.5 and requires zero additional ls, Grep, or Read calls.

### Step 6: Offer to Persist User Overrides

If the user provided any `--path` or `--exclude` flags that are not already in the config, offer to persist them.

First, compare user-provided overrides against the existing config and built-in defaults:
- `newPaths` = user `--path` values NOT already in `config.search_config.base_paths`
- `newExcludes` = user `--exclude` values NOT already in `config.search_config.additional_excludes` AND NOT already in `built_in_excludes`

If `newPaths` or `newExcludes` is non-empty, prompt the user via AskUserQuestion:

```
You specified search overrides not yet saved in the project config:

  Additional paths:
    - Source/CustomModule
    - Source/ExperimentalRPC

  Additional excludes:
    - */Generated/*

Would you like to save these to the project config for future scans?
  [1] Yes, add to config.yaml (recommended for recurring use)
  [2] No, one-time use only
```

If the user selects [1]:

1. Read the current config file.
2. Add the new paths to `search_config.base_paths` (creating the section if it does not exist).
3. Add the new excludes to `search_config.additional_excludes` (creating the section if it does not exist).
4. Write the updated config back using the Write tool.
5. Display confirmation:

```
Config updated: {config_file_path}
  Added paths:    {newPaths}
  Added excludes: {newExcludes}
Future /rpc-discover runs will include these settings automatically.
```

If the user selects [2], proceed without saving. No further action needed.

If the user did NOT provide any `--path` or `--exclude` flags, skip this step entirely.

### Step 7: Handle No RPCs Found (already covered in Step 4a)

If no RPCs were found, the helpful message was already displayed in Step 4a. No additional action is needed. The command exits gracefully after Step 5 metadata display.

## Output Formats

### Human-Readable Table (Default)

The default output is a formatted ASCII table suitable for terminal display. The full format is shown in Step 4b above.

**Example with mixed completeness**:

```
RPC Discovery Report (5 RPCs found in 2 files)
===============================================
Name              Context    Params                      Layers    Complete
--------------------------------------------------------------------------------
BotAttackTarget   InGame     targetId:str,damage:int,    @@@       Yes
                             weaponIds:str[],
                             isCritical:bool
DebugDumpState    AlwaysOn   category:str,verbose:bool   @@O       No
GetPlayerStatus   InGame     playerId:str                @@@       Yes
LoginUser         AlwaysOn   username:str,password:str   @@@       Yes
UIOpenMenu        FrontEnd   menuName:str,               @OO       No
                             forceRefresh:bool

@ = layer present, O = layer missing  |  Layers: Hook/Endpoint/Library

Scan complete.
  RPCs found:    5
  Files scanned: 2 C++ manager files
  Duration:      3.2s
  Complete RPCs: 3/5 (all 3 layers present)
  Partial RPCs:  2/5 (missing layers)

Incomplete RPCs:
  DebugDumpState   - missing: library
  UIOpenMenu       - missing: endpoint, library
```

## Error Handling

All errors follow the standard format from REQ-NF-5: file path (if applicable), issue description, and actionable remediation steps.

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

### No RPCs Found (Informational, Not an Error)

This is a normal condition for new projects or directories without RPC manager files. Display the helpful message from Step 4a. Do NOT display an error prefix. Exit with success.

### Malformed Registration (Warn and Continue)

When the scanner encounters a `RegisterHttpCallback` call where the `FName(TEXT("..."))` pattern cannot be parsed (e.g., uses a variable instead of a string literal):

```
WARNING: Found RegisterHttpCallback at {file}:{line} but could not extract RPC name.
The FName argument may use a variable instead of a string literal.
Skipping this registration and continuing with remaining RPCs.
```

The scan continues with all other RPCs. The malformed registration is excluded from the report but noted in console output.

### File Read Failure During Scan

When a specific file cannot be read during Pass 2 detailed analysis:

```
WARNING: Could not read {file_path} for detailed analysis.
Issue: {error_message}
The following RPCs from this file will have incomplete metadata:
  - {rpc_name_1}
  - {rpc_name_2}
Continuing with remaining files.
```

Affected RPCs appear in the report with partial metadata. The scan continues.

### Config File Parse Error

If the config.yaml file exists but contains invalid YAML:

```
WARNING: Could not parse config file at {config_path}.
Issue: {parse_error_message}
Falling back to default context mappings.
Run /rpc-curate to regenerate the config file.
```

The scan continues with built-in defaults.

## Examples

### Basic Discovery (Scan Workspace Root)

```
> /rpc-discover

RPC Discovery Report (5 RPCs found in 2 files)
===============================================
Name              Context    Params                      Layers    Complete
--------------------------------------------------------------------------------
BotAttackTarget   InGame     targetId:str,damage:int,    @@@       Yes
                             weaponIds:str[],
                             isCritical:bool
DebugDumpState    AlwaysOn   category:str,verbose:bool   @@@       Yes
GetPlayerStatus   InGame     playerId:str                @@@       Yes
LoginUser         AlwaysOn   username:str,password:str   @@@       Yes
UIOpenMenu        FrontEnd   menuName:str,               @@@       Yes
                             forceRefresh:bool

@ = layer present, O = layer missing  |  Layers: Hook/Endpoint/Library

Scan complete.
  RPCs found:    5
  Files scanned: 2 C++ manager files
  Duration:      3.2s
  Complete RPCs: 5/5 (all 3 layers present)
  Partial RPCs:  0/5 (missing layers)
```

### Scan with Overrides and Persist Prompt

```
> /rpc-discover --path=Source/CustomModule --exclude="ThirdParty/"

RPC Discovery Report (3 RPCs found in 1 files)
===============================================
Name              Context    Params                    Layers    Complete
--------------------------------------------------------------------------------
CustomAction      InGame     actionId:str              @@O       No
CustomQuery       AlwaysOn   queryType:str             @@@       Yes
CustomUpdate      InGame     entityId:str,data:obj     @@@       Yes

@ = layer present, O = layer missing  |  Layers: Hook/Endpoint/Library

Scan complete.
  RPCs found:    3
  Files scanned: 1 C++ manager files
  Duration:      1.4s
  Complete RPCs: 2/3 (all 3 layers present)
  Partial RPCs:  1/3 (missing layers)

Incomplete RPCs:
  CustomAction     - missing: library

You specified search overrides not yet saved in the project config:

  Additional paths:
    - Source/CustomModule

  Additional excludes:
    - ThirdParty/

Would you like to save these to the project config for future scans?
  [1] Yes, add to config.yaml (recommended for recurring use)
  [2] No, one-time use only
```

### Empty Results

```
> /rpc-discover Source/NewModule

RPC Discovery Report
====================

No RPC registrations found.

Scanned: 0 files in Source/NewModule
Duration: 0.1s

This is expected for:
  - New projects that haven't added RPCs yet
  - Directories that don't contain RPC registration files (*Rpc*.cpp)

Suggestions:
  - Verify the target path contains your RPC source files
  - Check that your C++ files follow the *Rpc*.cpp naming convention (e.g., *RpcManager_Core.cpp, *RpcComponent_Overlay.cpp)
  - Try specifying a different path: /rpc-discover path/to/source
  - If using a custom file naming convention, check config.yaml settings
```

## Skill Dependencies

This command loads the following skills (in Step 0) and delegates scanning logic to them. It does NOT reimplement their logic.

| Component | Skill | Role |
|-----------|-------|------|
| RPC Discovery Scanner | `test-engineering:rpc-discovery-scanner` | Scanning orchestration: spawns agents, merges results. Main algorithm for `ScanForRpcs`. |
| C++ Discovery Agent | `test-engineering:rpc-cpp-discovery` | C++ scanning algorithm. Embedded in Task prompt for the C++ agent. |
| C# Discovery Agent | `test-engineering:rpc-csharp-discovery` | C# scanning algorithm. Embedded in Task prompt for the C# agent. |
| Discovery Cache | `test-engineering:rpc-discovery-cache` | Cache write/read operations (`SaveDiscoveryCache`, `LoadDiscoveryCache`, `LoadModuleCache`). Used in Steps 3.5 and 5.5. |
| Pattern Library Config | `.rpc/patterns/{project}/config.yaml` or `.rpc/config.yaml` | Provides context definitions (name-to-suffix mapping), context inference rules, and naming conventions used to resolve RPC metadata. Falls back to built-in defaults if no config file exists. |
