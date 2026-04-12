---
name: llt-run
description: Execute LowLevelTests locally or via Gauntlet for console platforms
version: 1.0.0
category: LowLevelTests Execution
user-invocable: true
---

# llt-run: LowLevelTest Execution

**Version**: 1.0.0
**Category**: LowLevelTests Execution
**Purpose**: Build and return test execution commands for local or console platforms

> **Shared Reference**: See [llt-common/SKILL.md](../llt-common/SKILL.md) for response format, data structures, validation rules, and logging instructions.

---

## Overview

Generates test execution commands using the appropriate runner based on platform:
- **Local platforms** (Win64, Mac, Linux): Direct Catch2 binary execution
- **Console platforms** (PS5, Xbox, Switch, etc.): RunLowLevelTests via RunUAT (Gauntlet)
- **Special-case LLTs** (e.g., WebTests): Always use RunLowLevelTests, even on local platforms

The skill returns a command string and metadata. The agent then executes the command via the Bash tool and uses `llt-parse` on the results.

---

## Dependencies

- **llt-common**: Response format, data structures, validation rules
- **build-integration/ue-build-system.md**: Binary locations, run command syntax, troubleshooting

## Critical Conventions (from E2E Testing)

**Binary Location Discovery**: For plugin tests, binaries are located at:

- **FortniteGame plugins**: `<repo_root>/FortniteGame/Binaries/<Platform>/<TestName>/`
  - Example: `FortniteGame/Binaries/Mac/SecurePackageReaderTests/SecurePackageReaderTests`
- **Engine tests**: `<repo_root>/Engine/Binaries/<Platform>/`

**Run Command Syntax**:
```bash
cd <repo_root>
./FortniteGame/Binaries/Mac/<TestName>/<TestName> -r compact
# or with XML output:
./<BinaryPath> -r xml -o results.xml
```

**Common Catch2 Arguments**:
- `-r compact` - Compact output format
- `-r xml` - XML output for CI integration
- `-s` - Show successful assertions
- `[tag]` - Run tests with specific tag (e.g., `[Critical]`)

See [build-integration/ue-build-system.md](../build-integration/ue-build-system.md) for complete documentation.

---

## Command-Line Parameters

LowLevelTests executables accept three categories of arguments:

### LLT-Specific Flags

| Flag | Description |
|------|-------------|
| `--log` | Enable verbose logging output |
| `--debug` | Enable debug mode with additional diagnostics |
| `--sleep=N` | Sleep N seconds before starting tests (useful for attaching debuggers) |
| `--timeout=N` | Override default timeout in seconds (per test case) |
| `--global-setup` | Run global setup/teardown even if no tests match filters |
| `--mt` | Enable multi-threaded test execution |
| `--wait` | Wait for user input before starting tests |
| `--attach-to-debugger` | Automatically attach debugger if available |
| `--buildmachine` | Enable build machine mode (affects error reporting) |

### Catch2 Arguments

All Catch2 v3.x command-line options are supported. Most common:

| Flag | Description |
|------|-------------|
| `-r <reporter>` | Output format: `compact`, `xml`, `junit`, `console` |
| `-o <file>` | Output file path (e.g., `-o results.xml`) |
| `-t <tags>` | Tag filter expression (e.g., `[Critical]~[Slow]`) |
| `-s` | Show successful assertions (default: failures only) |
| `-# <N>` | Run specific test shard N (for parallel execution) |
| `-d yes` | Show test duration timing |
| `--list-tests` | List all test cases without running |
| `--list-tags` | List all tags in test suite |

**Tag Filter Syntax**:
- `[tag]` - Include tests with tag
- `~[tag]` - Exclude tests with tag
- `[tag1],[tag2]` - OR (either tag)
- `[tag1]~[tag2]` - AND NOT (tag1 but not tag2)

### UE Arguments (via --extra-args)

Unreal Engine arguments must be passed after the `--` delimiter:

```bash
./TestExecutable -r compact -- -LogCmds="LogNet Verbose"
```

Common UE arguments:
- `-LogCmds="<category> <verbosity>"` - Control log verbosity
- `-NoLoadStartupPackages` - Skip startup package loading
- `-NoShaderCompile` - Disable shader compilation
- `-ExecCmds="<command>"` - Execute console commands

### Complete Example

```bash
# Local execution with all parameter types
./SecurePackageReaderTests \
  --log \
  --timeout=60 \
  -r xml \
  -o results.xml \
  -t "[Critical]~[Slow]" \
  -s \
  -- -LogCmds="LogCore Verbose" -NoShaderCompile

# Gauntlet execution (console platforms)
RunUAT.sh RunLowLevelTests \
  -testapp=OnlineServicesMcpTests \
  -platform=PS5 \
  -devicepool=PS5Pool \
  -reporttype=xml \
  -tags="[EOS]~[leaderboard]" \
  -extra-args="-LogCmds='LogNet Verbose'"
```

**Reference**: Full command-line documentation is available in `Engine/Source/Developer/LowLevelTestsRunner/README.md`

---

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `platform` | Yes | Target platform (Win64, Mac, Linux, PS5, Xbox, Switch, etc.) |
| `target` | One of target/executable | Test target name (for console or RunLowLevelTests execution) |
| `executable` | One of target/executable | Path to test executable binary (for local execution) |
| `project` | No | Path to `.uproject` file (required for FortniteGame console tests) |
| `tags` | No | Catch2 tag filter, e.g. `[EOS]~[leaderboard]` |
| `output_xml` | No | Path for XML report output |
| `extra_args` | No | Extra UE arguments (passed after `--` delimiter for local, `-extra-args=` for Gauntlet) |
| `timeout` | No | Execution timeout in seconds (default: 300 local, 600 console) |
| `device_pool` | No | Gauntlet device pool name (console platforms) |

---

## Output Schema

Returns standard LLT JSON envelope (see [llt-common/SKILL.md](../llt-common/SKILL.md)). The `data` field contains:

```json
{
  "execution_config": {
    "command": "/path/to/FoundationTests -t [EOS] -r xml:/tmp/results.xml",
    "xml_output": "/tmp/results.xml",
    "timeout": 300,
    "platform": "local"
  },
  "metadata": {
    "target": "FoundationTests",
    "platform": "Win64",
    "runner_type": "catch2",
    "timeout_seconds": 300,
    "xml_output": "/tmp/results.xml",
    "requires_device_pool": false,
    "action": "execute_command",
    "command": "/path/to/FoundationTests -t [EOS] -r xml:/tmp/results.xml"
  }
}
```

---

## Command Generation Algorithm

### Step 1: Determine Runner Type

Decide which runner to use based on platform and target:

1. **Console platforms always use RunLowLevelTests (Gauntlet)**:
   - PS5, PS4, Xbox, XboxOne, XboxOneGDK, XSX, Switch, Android, iOS
2. **Special-case LLTs always use RunLowLevelTests** even on local platforms:
   - Currently defined special cases:
     - `WebTests`: Requires WebTestsServer (Django); adds `--web_server_ip=127.0.0.1` extra arg
   - Detection: Check target name against known special cases, or check if executable path contains a special case directory name
3. **All other local platforms use direct Catch2 execution**:
   - Win64, Mac, Linux

### Step 2a: Build Catch2 Command (Local Direct Execution)

For regular tests on local platforms (Win64, Mac, Linux):

1. Start with the executable path (quote if contains spaces).
2. **Tag filtering**: If tags provided, combine all tag expressions and add `-t {tags}` argument.
   - Parse the tag string: Split on `~` and `[`/`]` boundaries to get individual tag expressions like `[EOS]`, `~[leaderboard]`.
   - Concatenate back: `[EOS]~[leaderboard]`
3. **XML output**: If `output_xml` provided, add `-r xml:{path}` (ensure parent directory exists).
4. **Extra args**: If provided, add `--` delimiter then the extra arguments.
5. Return: `{executable} [-t tags] [-r xml:path] [-- extra_args]`

### Step 2b: Build RunLowLevelTests Command (Gauntlet)

For console platforms or special-case LLTs:

1. Determine RunUAT script:
   - Windows host: `RunUAT.bat`
   - Mac/Linux host: `RunUAT.sh`
2. Build command parts:
   - `{RunUAT} RunLowLevelTests -testapp={target_name} -platform={platform}`
   - If `build_path` known: `-build={path}` (extract from executable parent directory)
   - If `project` provided: `-project={path}`
   - If `device_pool` provided: `-devicepool={pool_name}`
   - If `output_xml` provided: `-reporttype=xml`
   - If `tags` provided: `-tags="{tag_string}"`
   - If `extra_args` provided: `-extra-args={args}`
   - For special cases, merge special-case extra args with user-provided extra args
3. Set `requires_device_pool: true` for console platforms, `false` for local.

### Step 3: Validate Inputs

Before generating the command, validate:
- Platform is a recognized value
- For console platforms, SDK is installed
- Executable exists (if provided)
- Project file exists (if provided)
- Tag filter syntax is valid (warn if not)
- Console platforms require device pool setup (warn)

---

## Platform-Specific Behavior

| Aspect | Local (Win64/Mac/Linux) | Console (PS5/Xbox/Switch) |
|--------|------------------------|---------------------------|
| Runner | Direct Catch2 binary | RunUAT RunLowLevelTests |
| Tag flag | `-t [tags]` | `-tags="[tags]"` |
| XML flag | `-r xml:path` | `-reporttype=xml` |
| Default timeout | 300s | 600s |
| Requirements | Executable at path | SDK installed, device pool configured |

---

## Special-Case LLT Registry

| Target | Requires Server | Server | Extra Args |
|--------|----------------|--------|------------|
| `WebTests` | Yes | WebTestsServer (Django) at `Engine/Source/Programs/WebTests/WebTestsServer` | `--web_server_ip=127.0.0.1` |

To detect special cases: check if target name or executable path basename matches a known special-case name.

---

## Error Handling

| Error | Condition |
|-------|-----------|
| `VALIDATION_ERROR` | Platform SDK not installed, executable not found, or invalid platform |
| `VALUE_ERROR` | Target name required but not provided for RunLowLevelTests |
| Warning | Tag filter has invalid syntax |
| Warning | Console platform requires device pool setup |
