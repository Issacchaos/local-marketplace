# File Discovery Service

## Purpose

The File Discovery Service locates target C++ and C# source files in the project workspace for RPC code insertion and discovery operations. It resolves abstract references like "the C++ manager file for AlwaysOn context" into concrete file paths by applying glob patterns, context-to-file-suffix mapping from the pattern library config, and fallback search strategies when primary patterns fail.

This service is consumed by the RPC Generator Agent (to find files for code insertion), the RPC Discovery Scanner (to enumerate files for scanning), and the `/rpc-generate` command (to present target file paths in the user confirmation step).

---

## Search Protocol (MANDATORY)

**CRITICAL**: ALL file discovery and content searches (that do not target a specific file) MUST follow this protocol. Searches that do not apply exclude patterns WILL cause tool timeouts and failures in Unreal Engine projects due to large generated/cached directories (Content, Intermediate, ThirdParty, etc.).

**Use `Bash` with `rg` (ripgrep) for ALL recursive file and content searches.** Do NOT use the `Glob` tool or `Grep` tool for recursive codebase searches, because:

- The `Glob` tool has **no exclude support** — it will scan into ThirdParty, Intermediate, Content, etc. and time out.
- The `Grep` tool only accepts a **single glob pattern** — it cannot combine an include pattern with multiple exclude patterns.

**File discovery** (finding files by name pattern):
```bash
rg --files --iglob "{include_pattern}" {exclude_args} {targetPath}
```

**Content search** (finding text within files):
```bash
rg "{regex_pattern}" --iglob "{include_pattern}" {exclude_args} -n [-A N] {targetPath}
```

Where `{exclude_args}` is built from the `excludePatterns` array:
```
exclude_args = ""
for each pattern in excludePatterns:
    exclude_args += ' --glob "!{pattern}"'
```

**Note**: Include patterns use `--iglob` (case-insensitive) to catch both `*Rpc*` and `*RPC*` file naming conventions. Exclude patterns use `--glob` (case-sensitive `!` patterns are not affected).

**When Glob and Grep tools ARE acceptable**:
- **Single-file content checks**: `Grep(pattern=..., path="specific/file.cpp")` — searching within one known file (not a recursive search)
- **Non-recursive directory listing**: `Glob(pattern="*", path="some/dir")` — listing files in one specific directory (not recursive `**`)

---

## Operations

### DiscoverManagerFiles

Finds the C++ manager `.cpp` and `.h` files for a given registration context. These are the files where RPC registrations (hook layer) and handler implementations/declarations (endpoint layer) reside.

**Signature**: `DiscoverManagerFiles(context, config)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | string | The registration context name (e.g., `AlwaysOn`, `FrontEnd`, `InGame`, `Server`) |
| `config` | object | The loaded pattern library config (from `.rpc/patterns/<project>/config.yaml` or `.rpc/config.yaml`) |

**Returns**: `{ cpp_manager: string, cpp_header: string }` -- absolute file paths.

**Algorithm** (follow these steps exactly):

#### Step 1: Resolve file suffix from config

Look up the context in `config.contexts` to get the `file_suffix`:

```
contextEntry = config.contexts.find(entry => entry.name == context)
fileSuffix = contextEntry.file_suffix
```

Context-to-suffix mapping from the default config:

| Context | file_suffix | Example file |
|---------|-------------|--------------|
| AlwaysOn | `_Core` | `*Rpc*_Core.cpp` |
| FrontEnd | `_Client` | `*Rpc*_Client.cpp` |
| InGame | `_Client` | `*Rpc*_Client.cpp` |
| Server | `_Server` | `*Rpc*_Server.cpp` |

If the context is not found in `config.contexts`, report an error:

```
ERROR: Unknown context
Issue: Context '{context}' is not defined in the pattern library config.
Remediation:
  1. Check the project's config.yaml for available contexts
  2. Available contexts: {list config.contexts[].name}
  3. Or specify the correct context via --context flag
```

#### Step 2: Search with primary pattern (rg with excludes)

Use `Bash` with `rg` to search for files matching the specific suffix pattern, applying exclude globs (see Search Protocol):

```bash
rg --files --iglob "**/*rpc*{fileSuffix}.cpp" {exclude_args} .
```

```bash
rg --files --iglob "**/*rpc*{fileSuffix}.h" {exclude_args} .
```

Example with `fileSuffix = _Core`:
```bash
rg --files --iglob "**/*rpc*_core.cpp" \
  --glob "!ThirdParty/" --glob "!Intermediate/" --glob "!Content/" \
  --glob "!Saved/" --glob "!DerivedDataCache/" --glob "!Binaries/" \
  --glob "!.git/" --glob "!node_modules/" .
  -> ["D:/project/Source/EOSDemo/Test/EOSDemoRpcComponent_Core.cpp"]
```

If exactly one `.cpp` and one `.h` file are found, return them. Proceed to Step 3 otherwise.

#### Step 3: Fallback -- broader Rpc file search

If the primary pattern returns zero results for either `.cpp` or `.h`:

```bash
rg --files --iglob "**/*rpc*.cpp" {exclude_args} .
rg --files --iglob "**/*rpc*.h" {exclude_args} .
```

This finds all Rpc-related files regardless of suffix, still applying excludes. If results are found, proceed to Step 5 (Ambiguous Match Resolution) to let the user select the correct file.

If still zero results, proceed to Step 4.

#### Step 4: Fallback -- broadest Manager search

If the broader Rpc file search also returns zero results:

```bash
rg --files --iglob "**/*manager*.cpp" {exclude_args} .
rg --files --iglob "**/*manager*.h" {exclude_args} .
```

If results are found, proceed to Step 5 (Ambiguous Match Resolution).

If still zero results, report an error:

```
ERROR: Target file not found
Issue: Cannot locate any C++ manager files in the workspace.
Remediation:
  1. Verify the project contains *Rpc*_*.cpp files
  2. Check that the workspace root is correct
  3. Specify a search path with --path flag
  4. Skip C++ layers with --skip-cpp flag
```

#### Step 5: Ambiguous match resolution

When multiple files match a pattern, present the candidates to the user via AskUserQuestion:

```
Multiple C++ manager files found for context '{context}' (suffix: '{fileSuffix}').

Please select the correct files:

.cpp files:
  [1] D:/project/Source/EOSDemo/Test/EOSDemoRpcComponent_Core.cpp
  [2] D:/project/Source/Other/OtherRpcManager_Core.cpp

.h files:
  [1] D:/project/Source/EOSDemo/Test/EOSDemoRpcComponent_Core.h
  [2] D:/project/Source/Other/OtherRpcManager_Core.h
```

After the user selects, return the chosen paths.

#### Step 6: Verify files contain expected markers

After resolving paths, verify the files contain the expected structural markers using the Read tool:

For the `.cpp` file, use Grep to check for:
```
Grep(pattern="RegisterHttpCallback|BroadcastRpcListChanged", path=cpp_manager_path)
```

For the `.h` file, use Grep to check for:
```
Grep(pattern="#if WITH_RPC_REGISTRY", path=cpp_header_path)
```

If markers are not found, warn the user but still return the file paths (the Code Insertion Engine will handle missing marker errors during insertion):

```
WARNING: File '{file}' was found but does not contain expected RPC structural markers.
This file may not be the correct target for RPC insertion.
Proceeding with this file. The Code Insertion Engine will report specific marker issues during insertion.
```

---

### DiscoverLibraryFile

Finds the C# RPC library file (`*RpcLibrary.cs`) where wrapper methods and DTOs are defined.

**Signature**: `DiscoverLibraryFile()`

**Returns**: `{ csharp_library: string }` -- absolute file path.

**Algorithm**:

#### Step 1: Search with primary pattern (rg with excludes)

```bash
rg --files --iglob "**/*rpclibrary.cs" {exclude_args} .
```

Example:
```bash
rg --files --iglob "**/*rpclibrary.cs" \
  --glob "!ThirdParty/" --glob "!Intermediate/" --glob "!Content/" \
  --glob "!Saved/" --glob "!DerivedDataCache/" --glob "!Binaries/" \
  --glob "!.git/" --glob "!node_modules/" .
  -> ["D:/project/EOSSDK/Build/Scripts/Utility/RpcFramework/EOSTest.EOSRpcLibrary.cs"]
```

If exactly one file is found, return it. If zero, proceed to Step 2. If multiple, proceed to Step 4.

#### Step 2: Fallback -- broader Rpc pattern

```bash
rg --files --iglob "**/*rpc*.cs" {exclude_args} .
```

Filter results to files that contain a class extending `RpcLibrary`. For each candidate file, use Grep on the specific file (single-file Grep is acceptable — see Search Protocol):
```
Grep(pattern="class\\s+\\w+.*:\\s*RpcLibrary", path=candidate_file)
```

If exactly one file matches the class pattern, return it. If multiple match, proceed to Step 4. If none match, proceed to Step 3.

#### Step 3: Fallback -- broadest Library search

```bash
rg --files --iglob "**/*library.cs" {exclude_args} .
```

Filter results using the same single-file Grep verification as Step 2. If results are found but none match the `RpcLibrary` base class, present them to the user via Step 4.

If still zero results:

```
ERROR: Target file not found
Issue: Cannot locate any C# RPC library files (*RpcLibrary.cs) in the workspace.
Remediation:
  1. Verify the project contains an RPC library class
  2. The file should contain a class extending RpcLibrary
  3. Check that the workspace root is correct
  4. Skip C# library layer with --skip-library flag
```

#### Step 4: Ambiguous match resolution

When multiple files match, present candidates to the user via AskUserQuestion:

```
Multiple C# library files found.

Please select the correct RPC library file:
  [1] D:/project/EOSSDK/Build/Scripts/Utility/RpcFramework/EOSTest.EOSRpcLibrary.cs
  [2] D:/project/EOSSDK/Build/Scripts/Utility/RpcFramework/EOSTest.AnotherRpcLibrary.cs
```

---

### DiscoverTestNodeFile

Finds the C# test node file (`*TestNode.cs`) where test case registrations are added.

**Signature**: `DiscoverTestNodeFile()`

**Returns**: `{ test_node: string, test_case_dir: string }` -- absolute file paths.

**Algorithm**:

#### Step 1: Search with primary pattern (rg with excludes)

```bash
rg --files --iglob "**/*testnode.cs" {exclude_args} .
```

Example:
```bash
rg --files --iglob "**/*testnode.cs" \
  --glob "!ThirdParty/" --glob "!Intermediate/" --glob "!Content/" \
  --glob "!Saved/" --glob "!DerivedDataCache/" --glob "!Binaries/" \
  --glob "!.git/" --glob "!node_modules/" .
  -> ["D:/project/EOSSDK/Build/Scripts/Tests/EOSDemo/EOSTest.EOSDemoRpcTests.cs"]
```

If exactly one file is found, return it along with its parent directory as `test_case_dir`. If zero, proceed to Step 2. If multiple, proceed to Step 4.

#### Step 2: Fallback -- rg content search for TestNode base class

If the primary pattern finds nothing, search for files containing a class that inherits from a test node base:

```bash
rg "class\s+\w+.*TestNode" --iglob "**/*.cs" {exclude_args} -l .
```

If results are found, collect the matching file paths. If exactly one, return it. If multiple, proceed to Step 4.

If still zero, proceed to Step 3.

#### Step 3: Fallback -- rg content search for SetUpTests method

```bash
rg "void\s+SetUpTests\s*\(" --iglob "**/*.cs" {exclude_args} -l .
```

This searches for any C# file that defines the `SetUpTests()` method, which is the structural marker for test registration files.

If results are found, use them as candidates. If still zero:

```
ERROR: Target file not found
Issue: Cannot locate any C# test node files (*TestNode.cs) in the workspace.
Remediation:
  1. Verify the project contains a test node class
  2. The file should contain a class with SetUpTests() method and QueueTestCase() calls
  3. Check that the workspace root is correct
  4. Skip test layer with --skip-test flag
```

#### Step 4: Ambiguous match resolution

When multiple test nodes are found, present candidates to the user via AskUserQuestion:

```
Multiple C# test node files found.

Please select the correct test node for this RPC:
  [1] D:/project/EOSSDK/Build/Scripts/Tests/EOSDemo/EOSTest.EOSDemoRpcTests.cs
  [2] D:/project/EOSSDK/Build/Scripts/Tests/EOSDemo/EOSTest.EOSDemoUITests.cs
```

After the user selects, determine the `test_case_dir` from the selected file's parent directory.

---

### DiscoverTestCaseFiles

Finds existing test case files matching the `Test*TestCase.cs` pattern. Used by the RPC Discovery Scanner to enumerate existing test cases and by conflict detection to check for naming collisions.

**Signature**: `DiscoverTestCaseFiles()`

**Returns**: `{ test_case_files: string[] }` -- array of absolute file paths.

**Algorithm**:

#### Step 1: Search with primary pattern (rg with excludes)

```bash
rg --files --iglob "**/test*testcase.cs" {exclude_args} .
```

Example:
```bash
rg --files --iglob "**/test*testcase.cs" \
  --glob "!ThirdParty/" --glob "!Intermediate/" --glob "!Content/" \
  --glob "!Saved/" --glob "!DerivedDataCache/" --glob "!Binaries/" \
  --glob "!.git/" --glob "!node_modules/" .
  -> [
       "D:/project/Tests/TestLoginUserTestCase.cs",
       "D:/project/Tests/TestGetPlayerStatusTestCase.cs",
       "D:/project/Tests/TestDebugDumpStateTestCase.cs"
     ]
```

Return all matched files. An empty result is valid (no test cases exist yet).

#### Step 2: Fallback (if needed for broader search)

If the caller needs to find test cases that do not follow the standard naming pattern:

```bash
rg --files --iglob "**/*testcase.cs" {exclude_args} .
```

This broader search catches test case files that may not have the `Test` prefix.

---

## Search Patterns Summary

The following table documents all search patterns used by this service. **All patterns are executed via `Bash: rg` with exclude arguments** (see Search Protocol). They are organized by file type with primary and fallback patterns.

### C++ Manager Files

| Priority | rg --iglob Pattern | Example Match | When Used |
|----------|-------------------|---------------|-----------|
| Primary | `**/*rpc*{fileSuffix}.cpp` | `EOSDemoRpcComponent_Core.cpp`, `FortAutomationRPCManager_Core.cpp` | Always tried first |
| Primary | `**/*rpc*{fileSuffix}.h` | `EOSDemoRpcComponent_Core.h` | Always tried first |
| Fallback 1 | `**/*rpc*.cpp` | `EOSDemoRpcComponent_Core.cpp`, `EOSDemoRpcComponent_Client.cpp` | If primary returns 0 results |
| Fallback 1 | `**/*rpc*.h` | `EOSDemoRpcComponent_Core.h`, `EOSDemoRpcComponent_Client.h` | If primary returns 0 results |
| Fallback 2 | `**/*manager*.cpp` | `SomeOtherManager.cpp` | If Fallback 1 returns 0 results |
| Fallback 2 | `**/*manager*.h` | `SomeOtherManager.h` | If Fallback 1 returns 0 results |

### C# Library File

| Priority | rg --iglob Pattern | Example Match | When Used |
|----------|-------------------|---------------|-----------|
| Primary | `**/*rpclibrary*.cs` | `EOSTest.EOSRpcLibrary.cs`, `EOSTest.EOSAsyncRpcLibrary.cs` | Always tried first |
| Fallback 1 | `**/*rpc*.cs` | `EOSTest.EOSRpcLibrary.cs`, `EOSTest.RpcHelper.cs` | If primary returns 0 results; filtered by base class |
| Fallback 2 | `**/*library.cs` | `EOSTest.EOSRpcLibrary.cs`, `SomeOtherLibrary.cs` | If Fallback 1 returns 0 results; filtered by base class |

### C# Test Node File

| Priority | rg Pattern | Example Match | When Used |
|----------|------------|---------------|-----------|
| Primary | `rg --files --iglob "**/*testnode.cs"` | `EOSTest.EOSDemoRpcTests.cs` | Always tried first |
| Fallback 1 | `rg "class\s+\w+.*TestNode" --iglob "**/*.cs"` | Files with TestNode base class | If primary returns 0 results |
| Fallback 2 | `rg "void\s+SetUpTests\s*\(" --iglob "**/*.cs"` | Files with SetUpTests method | If Fallback 1 returns 0 results |

### C# Test Case Files

| Priority | rg --iglob Pattern | Example Match | When Used |
|----------|-------------------|---------------|-----------|
| Primary | `**/test*testcase.cs` | `TestLoginUserTestCase.cs` | Standard discovery |
| Fallback | `**/*testcase.cs` | `LoginUserTestCase.cs` (non-standard prefix) | Broader search when needed |

**All patterns above use `--iglob` (case-insensitive) for include patterns and MUST include `{exclude_args}` (using `--glob "!..."`) when executed.** See the Search Protocol section for the exclude argument format.

---

## Context Mapping

The File Discovery Service uses the pattern library config to map a registration context name to the file suffix that identifies the correct C++ manager file. This mapping is defined in the `contexts` array of `config.yaml`.

### Config Structure

From `.rpc/patterns/<project>/config.yaml` (or the default at `.rpc/config.yaml`):

```yaml
contexts:
  - name: AlwaysOn
    file_suffix: _Core
    category_enum: "EFortRpcCategory::CoreCommands"
  - name: FrontEnd
    file_suffix: _Client
    category_enum: "EFortRpcCategory::UICommands"
  - name: InGame
    file_suffix: _Client
    category_enum: "EFortRpcCategory::GameplayActions"
  - name: Server
    file_suffix: _Server
    category_enum: "EFortRpcCategory::ServerCommands"
```

### Mapping Algorithm

```
Function: ResolveFileSuffix(context, config)

1. Search config.contexts for an entry where entry.name == context (case-sensitive match)

2. If found:
   - Return entry.file_suffix (e.g., "_Core")
   - Also return entry.category_enum for use by the RPC Generator Agent

3. If NOT found:
   - Report error with available context names
   - Do NOT guess or default -- the user must provide a valid context
```

### Important Notes

- **FrontEnd and InGame share `_Client` suffix**: Both contexts map to the same file suffix. This means `DiscoverManagerFiles("FrontEnd", config)` and `DiscoverManagerFiles("InGame", config)` return the same `.cpp` and `.h` files. The differentiation is in the `category_enum` (UICommands vs GameplayActions), which is used during code generation rather than file discovery.

- **Context inference vs context mapping**: Context inference (determining WHICH context an RPC belongs to from its name prefix) is handled by the `/rpc-generate` command using `config.context_inference_rules`. File Discovery only handles the SECOND step: given a known context, find the files. The inference rules from config are:

  ```yaml
  context_inference_rules:
    - priority: 1
      prefix_pattern: "Debug*"
      context: AlwaysOn
    - priority: 2
      prefix_pattern: "UI*"
      context: FrontEnd
    - priority: 3
      prefix_pattern: "Bot*"
      context: InGame
    - priority: 4
      prefix_pattern: "Get*"
      context: InGame
    - priority: 5
      prefix_pattern: "Set*"
      context: InGame
  ```

  When no rule matches, the system defaults to `AlwaysOn` with a note in the output (REQ-F-21).

---

## Fallback Logic

The fallback strategy follows a three-tier approach for each file type. The goal is to always present the user with actionable options rather than failing silently.

### Tier 1: Specific Pattern (Automatic)

Uses the exact glob pattern with the resolved file suffix. If exactly one result is found, it is used automatically with no user interaction required.

### Tier 2: Broader Pattern (User Selection)

Uses a broader glob pattern that may match multiple files. Results are presented to the user via AskUserQuestion for explicit selection. The user sees all candidates and picks the correct one.

### Tier 3: Broadest Pattern (User Selection)

Uses the broadest reasonable glob pattern. Results are presented with a note that the match is approximate:

```
No files matching '*Rpc*.cpp' were found.
A broader search found these files that may be relevant:

  [1] D:/project/Source/SomeManager.cpp
  [2] D:/project/Source/AnotherManager.cpp

Note: These files may not be RPC manager files. Select only if you are sure.
  [3] None of these -- skip C++ layers
```

### Tier 4: No Results (Error)

If even the broadest search returns nothing, report a clear error with remediation steps. Do NOT attempt to create files or guess locations.

### Fallback Flow Diagram

```
Primary Pattern (specific suffix)
  |
  |-- 1 result  --> Return (automatic)
  |-- 0 results --> Fallback 1 (broader)
  |-- 2+ results -> Ambiguous Match Resolution (AskUserQuestion)

Fallback 1 (broader pattern)
  |
  |-- 1 result  --> Return (automatic)
  |-- 0 results --> Fallback 2 (broadest)
  |-- 2+ results -> Ambiguous Match Resolution (AskUserQuestion)

Fallback 2 (broadest pattern)
  |
  |-- 1+ results -> Ambiguous Match Resolution (AskUserQuestion, with disclaimer)
  |-- 0 results  -> Error (file not found)
```

---

## Error Handling

All errors follow the standard error format defined by REQ-NF-5: file path, issue description, and actionable remediation steps.

### File Not Found

```
ERROR: Target file not found
File: (not applicable -- no file located)
Issue: Cannot locate {file_type} files in the workspace using patterns: {patterns_tried}
Remediation:
  1. Verify the project contains the expected file type
  2. Check that the workspace root is the correct project directory
  3. Specify a custom search path with --path flag
  4. Skip this layer with the appropriate --skip flag
```

### Unknown Context

```
ERROR: Unknown context
Issue: Context '{context}' is not defined in the pattern library config.
Remediation:
  1. Available contexts in config: {list context names}
  2. Check for typos in the context name
  3. Add the context to config.yaml if it is a new context type
```

### Config Not Loaded

```
ERROR: Pattern library config not loaded
Issue: Cannot read config.yaml from the pattern library.
Remediation:
  1. Run '/rpc-curate' to create a pattern library for this project
  2. Or verify '.rpc/patterns/<project>/config.yaml' exists and is valid YAML
```

### File Verification Warning

This is a warning, not a fatal error. Discovery continues, but the user is alerted:

```
WARNING: Structural marker verification failed
File: {file_path}
Issue: File was found but does not contain expected markers ({expected_markers}).
Note: Proceeding with this file. Insertion errors will be reported by the Code Insertion Engine.
```

---

## Spec Traceability

- **REQ-F-21**: Context inference (default to AlwaysOn when no rule matches). Context inference rules are consumed from config; this service maps the inferred context to file suffixes.
- **REQ-F-22**: Context-to-file mapping. The `contexts` config section maps context names to `file_suffix` values used in glob patterns and `category_enum` values used during generation.
- **REQ-NF-5**: Error messages with file/line context and actionable remediation.
- **REQ-NF-7**: Target file existence validation before generation.
- **REQ-NF-9**: No hardcoded paths. All file locations discovered via `rg` search patterns from workspace root, with mandatory exclude patterns to avoid scanning into large generated directories.
