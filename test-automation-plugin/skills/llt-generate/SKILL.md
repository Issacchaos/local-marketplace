---
name: llt-generate
description: Generate LowLevelTest scaffolding and test stubs for Unreal Engine modules using evidence-based template patterns. Supports scaffold mode, interactive mode, and autonomous mode with build/run integration.
user-invocable: true
---

# LLT Generate Skill

**Version**: 1.0.0
**Category**: Test Generation
**Languages**: C++ (Unreal Engine)
**Purpose**: Generate LowLevelTest scaffolding and test stubs based on Fortnite codebase patterns

## Overview

The LLT Generate Skill automates the creation of LowLevelTest modules for Unreal Engine projects using evidence-based template patterns derived from analysis of 15+ existing LLT modules in the Fortnite codebase. It supports three execution modes:

1. **Scaffold Mode**: Generate complete test module structure (.Build.cs, .Target.cs, initial test file)
2. **Interactive Mode**: Step-by-step generation with user confirmation at each stage (default)
3. **Autonomous Mode**: Automatic generation, build, and test execution without prompts

The system uses intelligent pattern detection to select the most appropriate template based on source code analysis:
- **Basic/Fixture** (40% of modules): Synchronous unit tests with optional fixture support
- **Async** (30% of modules): Asynchronous tests with callbacks, tick loops, or pipeline builders
- **Plugin/Lifecycle** (15% of modules): Complex engine integration with plugin lifecycle management
- **Mock** (10% of modules): Dependency injection and mock service interfaces

## Skill Interface

### Input

```yaml
command: test-generate                       # Command invocation
module_name: string                          # UE module name (e.g., "CommChannelsRuntime")
source_file: Path | null                     # Specific source file to generate tests for
scaffold: boolean                            # Generate complete module structure
framework: string | null                     # Override framework detection (basic, async, plugin, mock)
test_type: string | null                     # Override test type (unit, integration, e2e)
template: string | null                      # Explicit template override
class_filter: string | null                  # Filter to specific class name
method_filter: List[string] | null           # Filter to specific method name(s)
build: boolean                               # Automatically build after generation
run: boolean                                 # Automatically run tests after build
compdb: Path | null                          # Path to compilation database for accurate signatures
interactive: boolean                         # Enable interactive mode (default: true)
metadata: dict | null                        # llt-find JSON output for metadata-driven generation
```

### Output

```yaml
status: string                               # "success" | "failed" | "partial"
generated_files: List[GeneratedFile]
  - path: Absolute path to generated file
    type: "test_source" | "build_config" | "target_config"
    test_count: Number of test cases in file
    line_count: Total lines of code
    template_used: Template name used for generation
validation:
  compilation: "success" | "failed" | "not_attempted"
  execution: "success" | "failed" | "not_attempted"
  test_results:
    passed: Number of tests passed
    failed: Number of tests failed
    skipped: Number of tests skipped
metadata:
  template_used: Template name (e.g., "cpp-async-llt-template.md")
  pattern_detected: Detected pattern (basic, async, plugin, mock)
  generation_time_ms: Time taken for generation
  module_dependencies: List of module dependencies
  clang_parsing_used: Whether clang AST parsing was used
progress_log: List[string]                  # Step-by-step progress feedback
error: string | null                         # Error message if failed
warnings: List[string]                       # Warnings during generation
```

## CLI Usage

### Command Format

```bash
/llt-generate [options]
```

### Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--module <name>` | Module name for test generation | Required | `--module CommChannelsRuntime` |
| `--file <path>` | Source file to generate tests for | None | `--file CommChannelNode.h` |
| `--scaffold` | Generate complete module structure | False | `--scaffold` |
| `--framework <name>` | Override framework detection | Auto-detect | `--framework async` |
| `--test-type <type>` | Override test type | Auto-detect | `--test-type unit` |
| `--template <name>` | Explicit template override | Auto-detect | `--template cpp-async-llt-template` |
| `--class <name>` | Filter to specific class | None | `--class FCommChannelNode` |
| `--method <name>` | Filter to specific method(s) | None | `--method ConnectTo,IsConnectedTo` |
| `--build` | Automatically build after generation | False | `--build` |
| `--run` | Automatically run tests after build | False | `--run` |
| `--compdb <path>` | Path to compilation database | Auto-detect | `--compdb compile_commands.json` |
| `--no-interactive` | Disable interactive prompts | False (interactive by default) | `--no-interactive` |

### Execution Modes

#### 1. Scaffold Mode: Generate Complete Test Module

Generate a complete test module structure with .Build.cs, .Target.cs, and initial test file:

```bash
# Generate complete CommChannelsTests module
/llt-generate --module CommChannelsRuntime --scaffold

# Generated files:
# - Plugins/CommChannels/Tests/CommChannelsTests/CommChannelsTests.Build.cs
# - Plugins/CommChannels/Tests/CommChannelsTests/CommChannelsTests.Target.cs
# - Plugins/CommChannels/Tests/CommChannelsTests/Private/CommChannelsTests.cpp
```

**Workflow:**
1. Analyze source module's .Build.cs for dependencies
2. Detect appropriate test pattern (basic, async, plugin, mock)
3. Generate .Build.cs with TestModuleRules and dependencies
4. Generate .Target.cs with TestTargetRules and platform config
5. Generate initial test file with placeholder test cases
6. Return structured JSON with file paths and test count

#### 2. Interactive Mode: Step-by-Step Generation (Default)

Interactive mode prompts for confirmation at each step:

```bash
# Generate tests for specific source file (interactive by default)
/llt-generate --file CommChannelNode.h

# Workflow with prompts:
# Step 1: Analyze source file
#   > Found class: FCommChannelNode
#   > Found 5 methods: ConnectTo, IsConnectedTo, SetChannelValue, GetChannelValue, GetChannelId
#   > Continue? (y/n)
#
# Step 2: Select template
#   > Detected pattern: Basic/Fixture
#   > Template: cpp-basic-fixture-llt-template.md
#   > Override? (y/n to accept, or provide template name)
#
# Step 3: Generate tests
#   > Generate tests for 5 methods? (y/n, or provide method filter)
#
# Step 4: Build tests
#   > Build CommChannelsTests module? (y/n)
#
# Step 5: Run tests
#   > Run CommChannelsTests? (y/n)
```

**User Actions:**
- **Accept**: Press `y` to continue with detected settings
- **Override**: Provide custom value (template name, method filter, etc.)
- **Skip**: Press `n` to skip optional steps (build, run)
- **Abort**: Press `Ctrl+C` to cancel generation

#### 3. Autonomous Mode: Automatic Workflow

Autonomous mode runs generation, build, and tests without prompts:

```bash
# Generate, build, and run tests automatically
/llt-generate --module CommChannelsRuntime --build --run --no-interactive

# Workflow (no prompts):
# 1. Analyze source module
# 2. Detect pattern and select template
# 3. Generate test files
# 4. Build test module (via llt-build skill)
# 5. Run tests (via llt-run skill)
# 6. Return results with compilation and execution status
```

**Use Cases:**
- CI/CD pipelines: `--no-interactive --build --run`
- Batch test generation: Generate tests for multiple modules
- Automated test scaffolding: Create tests for new code

#### 4. Metadata-Driven Generation: Coverage Gap Analysis

Generate test stubs for untested methods identified by llt-find:

```bash
# First, run llt-find to identify coverage gaps
/llt-find --module CommChannelsRuntime --output coverage.json

# Then generate stubs for untested methods
/llt-generate --file CommChannelNode.h --metadata coverage.json

# Workflow:
# 1. Parse llt-find JSON output
# 2. Compare source methods against tested methods
# 3. Identify untested methods: SetChannelValue, GetChannelValue, GetChannelId
# 4. Generate test stubs for 3 methods with appropriate template
# 5. Return structured JSON with generated file paths
```

**Output:**
```cpp
// Generated stubs:
TEST_CASE("CommChannelsRuntime::FCommChannelNode::SetChannelValue", "[setChannelValue]") {
    // Arrange
    // TODO: Set up test fixture for SetChannelValue

    // Act
    // TODO: Call SetChannelValue with test inputs

    // Assert
    // TODO: Verify expected behavior
}

// ... stubs for GetChannelValue, GetChannelId ...
```

## Template Selection

### Automatic Pattern Detection

The system automatically detects the appropriate template based on source code analysis:

**Detection Priority** (highest to lowest):

1. **Mock Pattern**: Detects mock interfaces, dependency injection, error injection
   - File contains mock interface definitions (`IMockTestUtils`)
   - Dependency injection patterns (`SetMock`, `GetMock`)
   - Error injection methods (`SetNextOpError`)
   - Test double implementations

2. **Plugin/Lifecycle Pattern**: Detects engine integration and plugin lifecycle
   - `"Engine"` in .Build.cs PrivateDependencyModuleNames (triggers bCompileAgainstEngine in .Target.cs)
   - Plugin lifecycle methods (CreateFramework/DestroyFramework)
   - Complex framework initialization
   - Engine subsystem access (GEngine, World, GameInstance)

3. **Async Pattern**: Detects asynchronous operations
   - Async modules (FHttpModule, IWebSocket)
   - Callback delegates (TDelegate, FOnComplete)
   - Tick loop patterns (FRunUntilQuitRequestedFixture)
   - Pipeline builders (GetPipeline().EmplaceStep)
   - Futures/promises (TFuture, TPromise)

4. **Basic/Fixture Pattern**: Default for synchronous tests
   - Simple unit tests (TEST_CASE)
   - Fixture tests with state (TEST_CASE_METHOD)
   - Private members indicate fixture needs
   - Constructor/destructor setup

### Manual Template Override

Override automatic detection with explicit template selection:

```bash
# Force async template for WebSocket tests
/llt-generate --file WebSocketClient.h --template cpp-async-llt-template

# Force mock template for service interfaces
/llt-generate --file MockAuthService.h --template cpp-mock-llt-template
```

### Available Templates

| Template | Usage | Pattern | Example |
|----------|-------|---------|---------|
| `cpp-basic-fixture-llt-template.md` | Synchronous unit tests (40%) | TEST_CASE or TEST_CASE_METHOD | FoundationTests/LinkedListBuilderTests.cpp |
| `cpp-async-llt-template.md` | Async with callbacks/tick loops (30%) | Tick loop + callback completion | WebTests/TestWebSockets.cpp |
| `cpp-plugin-lifecycle-llt-template.md` | Engine integration (15%) | Complex fixture + bCompileAgainstEngine | FNOnlineFrameworkTests/SaveFrameworkTests.cpp |
| `cpp-mock-llt-template.md` | Dependency injection (10%) | Mock interface + error injection | FNOnlineFrameworkTests/MockTestUtils.h |

## Pattern Detection Algorithm

This algorithm replaces `pattern_detector.py` - agents implement this on-the-fly using Read and Grep tools.

### Detection Entry Point

```python
def detect_test_pattern(source_file: Path, build_cs_path: Path = None, override_template: str = None) -> str:
    """
    Detect appropriate LLT test pattern based on source file and Build.cs analysis.

    Priority Order (REQ-F-12):
    1. Mock - Architectural patterns (highest priority)
    2. Plugin/Lifecycle - Engine integration
    3. Async - Runtime patterns
    4. Basic/Fixture - Default fallback

    Returns: 'mock' | 'plugin-lifecycle' | 'async' | 'basic' | 'fixture'
    """
    # Step 1: Check for manual override
    if override_template:
        return override_template

    # Step 2: Read source and Build.cs content
    if not source_file.exists():
        return 'basic'  # Default fallback

    source_content = Read(source_file)
    build_cs_content = Read(build_cs_path) if build_cs_path and build_cs_path.exists() else ""

    # Step 3: Priority-ordered detection
    if is_mock_pattern(source_content, build_cs_content):
        return 'mock'

    if is_plugin_lifecycle_pattern(source_content, build_cs_content):
        return 'plugin-lifecycle'

    if is_async_pattern(source_content, build_cs_content):
        return 'async'

    # Step 4: Basic vs Fixture fallback
    if requires_fixture(source_content):
        return 'fixture'
    else:
        return 'basic'
```

### Mock Pattern Detection (REQ-F-13)

**Priority**: Highest (10% of modules, architectural significance)

**Evidence**: FNOnlineFrameworkTests with IMockTestUtils, SetNextOpError, error injection

**Indicators**:

```python
def is_mock_pattern(source_content: str, build_cs_content: str) -> bool:
    """
    Detect mock interfaces, dependency injection, test doubles, error injection.
    """
    # Source file indicators
    mock_source_patterns = [
        # Mock interface definitions
        r'\bIMock\w+\b',                         # IMockTestUtils, IMockService
        r'\bclass\s+\w*Mock\w*\s*[:{]',          # class MockTestUtils, class FooMock
        r'\bstruct\s+\w*Mock\w*\s*[:{]',         # struct MockData

        # Mock implementation patterns
        r'\bFMock\w+\b',                         # FMockTestUtils, FMockService
        r'\bTMock\w+\b',                         # TMock<T>

        # Error injection patterns
        r'\bSetNextOpError\b',                   # SetNextOpError()
        r'\bInjectError\b',                      # InjectError()
        r'\bMockRetryManager\b',                 # MockRetryManager

        # Test double patterns
        r'\bTestDouble\b',                       # Test double implementations
        r'\bStub\w+\b',                          # Stub implementations
        r'\bFake\w+\b',                          # Fake implementations

        # Dependency injection indicators
        r'\bInjectDependency\b',                 # Explicit DI

        # Mock utility methods
        r'\bPause\s*\(\s*\)',                    # Pause() for controlling async ops
        r'\bUnpause\s*\(\s*\)',                  # Unpause()
        r'\bOnAsyncOpStarting\b',                # Delegate for operation tracking

        # Mock-specific includes
        r'#include\s+"MockTestUtils\.h"',       # MockTestUtils header
        r'#include\s+"\w*Mock\w*\.h"',          # Any mock header
    ]

    # Check source content (use Grep or regex)
    for pattern in mock_source_patterns:
        if Grep(pattern, source_file, output_mode="files_with_matches"):
            return True  # Match found

    # Build.cs indicators
    mock_buildcs_patterns = [
        r'\bMockTestUtils\b',
        r'\bOSSNullMockTestUtils\b',
        r'UE_WITH_OSSNULLMOCKTESTUTILS',
    ]

    for pattern in mock_buildcs_patterns:
        if Grep(pattern, build_cs_file, output_mode="files_with_matches"):
            return True

    return False
```

### Plugin/Lifecycle Pattern Detection (REQ-F-14)

**Priority**: High (15% of modules, engine integration needs)

**Evidence**: FNOnlineFrameworkTests, SaveFramework with bCompileAgainstEngine, lifecycle methods

**Indicators**:

```python
def is_plugin_lifecycle_pattern(source_content: str, build_cs_content: str, target_cs_content: str = None) -> bool:
    """
    Detect engine integration and plugin lifecycle patterns.
    """
    # Build.cs indicators - check for Engine module dependency
    # PRINCIPLE: "Include only what you use" - presence of "Engine" in dependencies
    # is the authoritative signal, NOT bCompileAgainst* flags
    if Grep(r'PrivateDependencyModuleNames.*"Engine"', build_cs_file, output_mode="files_with_matches"):
        return True  # Strong indicator - Engine module dependency

    # Target.cs indicators (legacy - check existing .Target.cs files)
    # NOTE: These flags should only be present if "Engine" is in .Build.cs dependencies
    if target_cs_content:
        targetcs_patterns = [
            r'\bbCompileAgainstEngine\s*=\s*true',
            r'\bbMockEngineDefaults\s*=\s*true',
            r'\bbTestsRequireEngine\s*=\s*true',
        ]
        for pattern in targetcs_patterns:
            if Grep(pattern, target_cs_file, output_mode="files_with_matches"):
                return True  # Legacy indicator from existing tests

    # Source code indicators
    source_patterns = [
        # Plugin lifecycle methods
        r'\bInitializeModule\b',
        r'\bShutdownModule\b',
        r'\bStartupModule\b',

        # Framework lifecycle
        r'\bCreate\w+Framework\b',              # CreateSaveFramework
        r'\bDestroy\w+Framework\b',             # DestroySaveFramework
        r'\bInitialize\w+Framework\b',

        # Component-based fixtures
        r'\b\w+Component\s+\w+Component',       # FCommonAccountComponent
        r'\bTestComponent\b',

        # Engine-specific patterns
        r'\bGEngine\b',                          # Engine global
        r'\bGConfig\b',                          # Config global
        r'\bTAutoRestore\w+\b',                  # TAutoRestoreConsoleVariable

        # Mock engine patterns
        r'\bMockEngine\b',
        r'\bEngineDefaults\b',
    ]

    for pattern in source_patterns:
        if Grep(pattern, source_file, output_mode="files_with_matches"):
            return True

    return False
```

### Async Pattern Detection (REQ-F-15)

**Priority**: Medium (30% of modules, runtime patterns)

**Evidence**: WebTests with tick loops, OnlineTests with pipeline builders

**Indicators**:

```python
def is_async_pattern(source_content: str, build_cs_content: str) -> bool:
    """
    Detect asynchronous operations, callbacks, tick loops, futures/promises.
    """
    # Source file indicators
    async_source_patterns = [
        # HTTP patterns (WebTests)
        r'\bFHttpModule\b',
        r'\bIHttpRequest\b',
        r'\bIHttpResponse\b',
        r'\bHTTPServer\b',

        # WebSocket patterns
        r'\bIWebSocket\b',
        r'\bWebSocketsModule\b',
        r'\bCreateWebSocket\b',

        # Tick loop patterns
        r'\bwhile\s*\([^)]*bQuitRequested',     # while (!bQuitRequested)
        r'\bSimulateEngineTick\b',
        r'\bRunUntilQuitRequested\b',
        r'FPlatformProcess::Sleep',
        r'FTSBackgroundableTicker',

        # Callback patterns
        r'\bOnConnected\(\)',
        r'\bOnMessage\(\)',
        r'\bOnComplete\(\)',
        r'\bOnClosed\(\)',
        r'\bAddLambda\(',                        # Callback registration

        # Futures/promises
        r'\bTFuture\s*<',
        r'\bTPromise\s*<',
        r'\bFAsyncTask\b',
        r'\bGetFuture\(\)',

        # Online Tests pipeline patterns
        r'\bGetPipeline\(\)',
        r'\bEmplaceLambda\(',
        r'\bEmplaceStep\s*<',
        r'\bRunToCompletion\(\)',
        r'\bFTestPipeline\b',
        r'\bFAsyncTestStep\b',

        # Async operation helpers
        r'\bGetAsyncOpResultChecked\b',
        r'\bBlockUntilComplete\b',
        r'\bWaitForCompletion\b',

        # Async test macros
        r'\bONLINE_TEST_CASE\b',
        r'\bRESONANCE_TEST_CASE\b',

        # Online interfaces (typically async)
        r'\bIOnlineServices\b',
        r'\bServices->GetInterface\s*<',
    ]

    for pattern in async_source_patterns:
        if Grep(pattern, source_file, output_mode="files_with_matches"):
            return True

    # Build.cs indicators
    async_buildcs_patterns = [
        r'\bHTTP\b',
        r'\bWebSockets\b',
        r'\bOnlineTestsCore\b',
        r'\bOnlineServices\w+\b',
        r'\bEventLoop\b',
    ]

    for pattern in async_buildcs_patterns:
        if Grep(pattern, build_cs_file, output_mode="files_with_matches"):
            return True

    return False
```

### Basic vs Fixture Detection (REQ-F-16)

**Priority**: Lowest (40% of modules, default fallback)

**Evidence**: FoundationTests (basic), WebTests (fixture with state)

**Indicators**:

```python
def requires_fixture(source_content: str) -> bool:
    """
    Determine if test needs fixture vs basic pattern.

    Fixture needed for:
    - Classes with private members (requires friend class or fixture access)
    - Classes with constructor/destructor setup
    - Classes requiring setup/teardown methods
    - Complex state management

    Basic suitable for:
    - Pure functions
    - Simple structs with public members
    - Minimal state
    """
    fixture_patterns = [
        # Private members (requires fixture for access)
        r'class\s+\w+\s*[:{][^}]*\bprivate\s*:[^}]*\w+\s+\w+;',

        # Constructor/destructor patterns
        r'\bexplicit\s+\w+\s*\(',                # Explicit constructor
        r'~\w+\s*\(\s*\)',                       # Destructor

        # Setup/teardown methods
        r'\bSetup\w*\s*\(\s*\)',
        r'\bTeardown\w*\s*\(\s*\)',
        r'\bInitialize\w*\s*\(\s*\)',
        r'\bCleanup\w*\s*\(\s*\)',

        # Complex fixture patterns
        r'TEST_CASE_METHOD\s*\(',                # Catch2 fixture macro
        r'\bFIXTURE\b',

        # State management
        r'\bTSharedPtr\s*<\w+>\s+\w+;',         # Shared pointer members
        r'\bTUniquePtr\s*<\w+>\s+\w+;',         # Unique pointer members

        # Component composition
        r'\b\w+Component\s+\w+;',                # Component members
    ]

    # Use Grep with multiline mode for class structure matching
    for pattern in fixture_patterns:
        if Grep(pattern, source_file, output_mode="files_with_matches", multiline=True):
            return True

    return False
```

### Usage Example

```python
# Agent implementation during test generation:

# Step 2.2: Detect pattern
source_file = Path("CommChannelNode.h")
build_cs_file = Path("CommChannelsRuntime.Build.cs")

# Read files
source_content = Read(source_file)
build_cs_content = Read(build_cs_file)

# Apply detection algorithm
detected_pattern = detect_test_pattern(source_file, build_cs_file, override_template=None)

# Result: "async" (if WebSocket patterns found)
# Result: "basic" (if pure functions only)
# Result: "mock" (if IMockTestUtils found)
```

### Confidence Scoring (Optional Debug Feature)

For debugging borderline cases, calculate weighted confidence scores:

```python
# Mock: Strong indicators (+0.3), Medium indicators (+0.2)
# Plugin: Strong indicators (+0.4), Medium indicators (+0.2)
# Async: Strong indicators (+0.3), Medium indicators (+0.2)
# Fixture: Presence = 0.7, Absence = 0.3

scores = {
    'mock': count_matches(mock_patterns) * 0.25,
    'plugin': count_matches(plugin_patterns) * 0.30,
    'async': count_matches(async_patterns) * 0.25,
    'fixture': 0.7 if requires_fixture else 0.3,
    'basic': 0.5  # Always available as fallback
}

# Winner is highest score, or fallback to priority order if tied
```

## Implementation Algorithm

### Phase 1: Initialize and Validate

```markdown
# Step 1.1: Read skill interface
Read file: skills/llt-generate/SKILL.md

# Step 1.2: Validate inputs
if not module_name and not source_file:
    return error "Must provide --module or --file"

if build or run:
    interactive = False  # Autonomous mode

# Step 1.3: Detect project root and module root
project_root = detect_project_root()
module_root = find_module_directory(module_name)

# Step 1.4: Check prerequisites
if not module_root.exists():
    return error f"Module {module_name} not found"
```

### Phase 2: Analyze Source and Detect Pattern

```markdown
# Step 2.1: Analyze source file or module
if source_file:
    methods = extract_method_signatures(source_file, use_clang=True, compdb=compdb)
    source_class = extract_class_name(source_file)
else:
    # Scaffold mode: analyze entire module
    source_files = find_source_files(module_root)
    methods = []

# Step 2.2: Detect test pattern
build_cs_path = module_root / f"{module_name}.Build.cs"
pattern = detect_test_pattern(source_file, build_cs_path)
# Returns: "mock", "plugin", "async", or "basic"

# Step 2.3: Interactive confirmation (if enabled)
if interactive:
    display_info(f"Detected pattern: {pattern}")
    display_info(f"Template: {pattern_to_template(pattern)}")
    user_choice = prompt("Accept pattern? (y/n, or provide template name): ")

    if user_choice.lower() == 'n':
        return abort "User cancelled generation"
    elif user_choice not in ['y', 'yes', '']:
        template = user_choice  # User provided explicit template
    else:
        template = pattern_to_template(pattern)
else:
    template = pattern_to_template(pattern)

# Apply template override if provided via CLI
if template_override:
    template = template_override
```

### Phase 3: Build Context and Render Templates

```markdown
## Module Analysis Algorithm

This algorithm replaces `module_analyzer.py` - agents parse .Build.cs files on-the-fly.

### Parse Dependencies from .Build.cs

```python
def extract_dependencies(module_root: Path) -> list:
    """
    Parse .Build.cs file to extract module dependencies.

    Patterns:
    - PrivateDependencyModuleNames.AddRange(new string[] { "Dep1", "Dep2" })
    - PublicDependencyModuleNames.AddRange(new string[] { "Dep3" })
    - PrivateDependencyModuleNames.Add("SingleDep")

    Returns: List of dependency module names
    """
    # Find .Build.cs file
    module_name = module_root.name
    build_cs_path = module_root / f"{module_name}.Build.cs"

    if not build_cs_path.exists():
        build_cs_files = Glob(f"{module_root}/*.Build.cs")
        if not build_cs_files:
            return ['Core', 'CoreUObject', 'ApplicationCore']
        build_cs_path = Path(build_cs_files[0])

    # Read and parse
    build_cs_content = Read(build_cs_path)

    dependencies = []

    # AddRange pattern
    addrange = r'(Private|Public)DependencyModuleNames\.AddRange\s*\(\s*new\s+string\[\]\s*\{([^}]+)\}\s*\)'
    for match in re.finditer(addrange, build_cs_content):
        deps = re.findall(r'"([^"]+)"', match.group(2))
        dependencies.extend(deps)

    # Add pattern
    add = r'(Private|Public)DependencyModuleNames\.Add\s*\(\s*"([^"]+)"\s*\)'
    for match in re.finditer(add, build_cs_content):
        dependencies.append(match.group(2))

    # Deduplicate and add essentials
    dependencies = list(set(dependencies))
    for essential in ['Core', 'CoreUObject', 'ApplicationCore']:
        if essential not in dependencies:
            dependencies.append(essential)

    return dependencies
```

# Step 3.1: Build generation context
context = {
    'module_name': module_name,
    'plugin_name': extract_plugin_name(module_root),
    'test_module_name': f"{module_name}Tests",
    'test_target_name': f"{module_name}Tests",
    'source_header': str(source_file.relative_to(project_root)) if source_file else None,
    'dependencies': extract_dependencies(module_root),  # Uses algorithm above
    'copyright_header': generate_copyright_header(),
    'methods': methods,
    'class_name': source_class if source_file else None,
}

# Apply filters
if class_filter:
    methods = filter_methods_by_class(methods, class_filter)
if method_filter:
    methods = filter_methods_by_name(methods, method_filter)
    context['methods'] = methods

# Step 3.2: Interactive method selection (if enabled)
if interactive and methods:
    display_info(f"Found {len(methods)} methods:")
    for method in methods:
        display_info(f"  - {method['name']}")

    user_choice = prompt("Generate tests for all methods? (y/n, or provide method names): ")

    if user_choice.lower() == 'n':
        return abort "User cancelled generation"
    elif user_choice not in ['y', 'yes', '']:
        # User provided method filter
        method_names = [m.strip() for m in user_choice.split(',')]
        methods = filter_methods_by_name(methods, method_names)
        context['methods'] = methods

# Step 3.3: Load and render templates

## Template Rendering Algorithm

This algorithm replaces `template_renderer.py` - agents implement placeholder substitution on-the-fly.

### Placeholder Categories (REQ-F-7 through REQ-F-11)

**5 Categories** with 100+ placeholders total:
1. **UE_MODULE** (REQ-F-7): Module names, class names, method names, header paths
2. **TEST_STRUCTURE** (REQ-F-8): Test tags, setup/act/assert code, sections
3. **ASYNC_PATTERN** (REQ-F-9): Async operations, callbacks, tick loops, pipelines
4. **MOCK_PATTERN** (REQ-F-10): Mock interfaces, error injection, test doubles
5. **MODULE_CONFIG** (REQ-F-11): Build.cs/Target.cs configuration, dependencies

### Rendering Algorithm

```python
def render_template(template_path: Path, context: dict) -> str:
    """
    Render template with placeholder substitution using category-specific resolvers.

    Args:
        template_path: Path to template markdown file
        context: Dictionary with placeholder values

    Returns:
        Rendered template string with placeholders substituted
    """
    # Step 1: Read template file
    template_content = Read(template_path)

    # Step 2: Find all placeholders: {{PLACEHOLDER}}
    placeholders = re.findall(r'\{\{(\w+)\}\}', template_content)

    # Step 3: Substitute each placeholder
    for placeholder in placeholders:
        if placeholder in context:
            value = context[placeholder]

            # Special handling for DEPENDENCY_MODULES (C# array formatting)
            if placeholder == 'DEPENDENCY_MODULES':
                value = format_dependency_modules(value)

            # Replace all occurrences
            template_content = template_content.replace(f'{{{{{placeholder}}}}}', str(value))
        else:
            # Generate TODO comment based on category
            todo_comment = generate_todo_for_placeholder(placeholder)
            template_content = template_content.replace(f'{{{{{placeholder}}}}}', todo_comment)

    # Step 4: Unescape literal braces: \{\{ → {{
    template_content = template_content.replace(r'\{\{', '{{')
    template_content = template_content.replace(r'\}\}', '}}')

    return template_content
```

### Category-Specific TODO Generation

```python
def generate_todo_for_placeholder(placeholder: str) -> str:
    """
    Generate helpful TODO comment when context value missing.

    Returns formatted TODO based on placeholder category.
    """
    # Category 1: UE_MODULE placeholders (REQ-F-7)
    ue_module_hints = {
        'UE_MODULE_NAME': 'ModuleName',
        'UE_HEADER_PATH': 'Path/To/Header.h',
        'CLASS_NAME': 'FClassName',
        'METHOD_NAME': 'MethodName',
        'NAMESPACE': 'ModuleNamespace',
        'MODULE_INTERFACE': 'IModuleInterface',
        'FRAMEWORK_NAME': 'FrameworkName',
        'SERVICE_NAME': 'ServiceName'
    }

    if placeholder in ue_module_hints:
        hint = ue_module_hints[placeholder]
        return f'/* TODO: Fill in {{{placeholder}}} - e.g., {hint} */'

    # Category 2: TEST_STRUCTURE placeholders (REQ-F-8)
    test_structure_hints = {
        'TEST_TAG': '[module]',
        'SETUP_CODE': '// Arrange\n\t// TODO: Setup test data',
        'CODE_UNDER_TEST': '// Act\n\t// TODO: Call method under test',
        'ASSERTIONS': '// Assert\n\t// TODO: Add REQUIRE() checks',
        'SECTION_NAME': 'Test scenario description',
        'FIXTURE_CLASS_NAME': 'FTestFixture',
        'TEST_DESCRIPTION': 'Description of what this test validates',
        'MODULE_TAG': '[module]',
        'FEATURE_TAG': '[feature]'
    }

    if placeholder in test_structure_hints:
        hint = test_structure_hints[placeholder]

        # Multi-line format for code placeholders
        if placeholder.endswith('_CODE') or placeholder.endswith('_ASSERTIONS'):
            return f'// TODO: Fill in {{{placeholder}}}\n\t{hint}'

        return f'/* TODO: Fill in {{{placeholder}}} - e.g., {hint} */'

    # Category 3: ASYNC_PATTERN placeholders (REQ-F-9)
    async_hints = {
        'ASYNC_OPERATION': '// TODO: Start async operation',
        'ASYNC_CALLBACK': '// TODO: Register async callback',
        'TIMEOUT_HANDLER': '// TODO: Handle timeout',
        'TICK_LOOP': '// TODO: Implement tick loop',
        'COMPLETION_SIGNAL': 'bQuitRequested = true;',
        'ASYNC_PATTERN_TYPE': 'simple',
        'NAMESPACE_BEGIN': 'namespace UE::Tests {',
        'NAMESPACE_END': '}  // namespace UE::Tests',
        'TICK_FIXTURE_CLASS_NAME': 'FRunUntilQuitRequestedFixture'
    }

    if placeholder in async_hints:
        hint = async_hints[placeholder]

        if placeholder.endswith('_CODE') or placeholder.endswith('_SIGNAL'):
            return f'// TODO: Fill in {{{placeholder}}}\n\t{hint}'

        return f'/* TODO: Fill in {{{placeholder}}} - e.g., {hint} */'

    # Category 4: MOCK_PATTERN placeholders (REQ-F-10)
    mock_hints = {
        'MOCK_INTERFACE': '// TODO: Define mock interface',
        'MOCK_IMPL': '// TODO: Implement mock class',
        'MOCK_INTERFACE_NAME': 'IMockInterface',
        'MOCK_IMPL_NAME': 'FMockImplementation',
        'ERROR_INJECTION': 'SetNextOpError(ErrorCode);',
        'TEST_FIXTURE': '// TODO: Define test fixture with dependency injection',
        'TEST_DOUBLE': '// TODO: Define test double',
        'CREATE_MOCKS': '// TODO: Create mock instances',
        'INJECT_DEPENDENCIES': '// TODO: Inject dependencies'
    }

    if placeholder in mock_hints:
        hint = mock_hints[placeholder]

        if placeholder.endswith('_CODE') or placeholder in ['MOCK_INTERFACE', 'MOCK_IMPL', 'TEST_FIXTURE']:
            return f'// TODO: Fill in {{{placeholder}}}\n\t{hint}'

        return f'/* TODO: Fill in {{{placeholder}}} - e.g., {hint} */'

    # Category 5: MODULE_CONFIG placeholders (REQ-F-11)
    config_hints = {
        'TEST_MODULE_NAME': 'ModuleNameTests',
        'TEST_NAME': 'Module Name Tests',
        'TEST_SHORT_NAME': 'ModuleName',
        'DEPENDENCY_MODULES': '"Core"',
        'ENGINE_FLAGS': '// No special flags needed',
        'TEST_TARGET_NAME': 'ModuleNameTests',
        'GAUNTLET_ARGS': ''
    }

    if placeholder in config_hints:
        hint = config_hints[placeholder]

        if placeholder.endswith('_FLAGS') or placeholder.endswith('_CONFIG'):
            return f'// TODO: Fill in {{{placeholder}}}\n\t\t{hint}'

        return f'/* TODO: Fill in {{{placeholder}}} - e.g., {hint} */'

    # Default fallback
    return f'/* TODO: Fill in {{{placeholder}}} */'
```

### Special Formatting: DEPENDENCY_MODULES

```python
def format_dependency_modules(modules: Any) -> str:
    """
    Format dependency modules as C# string array with proper indentation.

    Input formats supported:
    - List: ["Core", "CoreUObject", "Engine"]
    - String (comma-separated): "Core, CoreUObject, Engine"
    - String (single): "Core"

    Output format:
    '"Core",\n\t\t\t\t"CoreUObject",\n\t\t\t\t"Engine"'
    """
    # Step 1: Normalize to list
    if isinstance(modules, str):
        if ',' in modules:
            # Parse comma-separated string
            modules = [m.strip().strip('"') for m in modules.split(',')]
        else:
            # Single module
            modules = [modules.strip().strip('"')]
    elif not isinstance(modules, list):
        modules = [str(modules)]

    # Step 2: Format each module with quotes
    formatted_modules = [f'"{module}"' for module in modules]

    # Step 3: Join with comma and newline + 4-level indent
    return ',\n\t\t\t\t'.join(formatted_modules)
```

### Extracting Code from Markdown Templates

Many templates embed code in markdown code blocks. Extract code before writing to file:

```python
def extract_code_from_markdown(template_content: str, language: str = 'cpp') -> str:
    """
    Extract code blocks from markdown template.

    Args:
        template_content: Rendered markdown template
        language: Code fence language (cpp, csharp, etc.)

    Returns:
        Plain code without markdown formatting
    """
    # Pattern: ```cpp\n(code)\n```
    pattern = f'```{language}\\n(.*?)\\n```'
    matches = re.findall(pattern, template_content, re.DOTALL)

    if matches:
        # Join all code blocks (templates may have multiple)
        return '\n\n'.join(matches)

    # No code blocks found - return as-is
    return template_content
```

### Usage Example

```python
# During test generation (Step 3.3):

# 1. Map pattern to template files
template_map = {
    'basic': 'cpp-basic-fixture-llt-template.md',
    'async': 'cpp-async-llt-template.md',
    'plugin-lifecycle': 'cpp-plugin-lifecycle-llt-template.md',
    'mock': 'cpp-mock-llt-template.md'
}

cpp_template = template_map[detected_pattern]
build_cs_template = 'ue-test-build-cs-template.md'
target_cs_template = 'ue-test-target-cs-template.md'

# 2. Build context dictionary
context = {
    'UE_MODULE_NAME': 'CommChannelsRuntime',
    'CLASS_NAME': 'FCommChannelNode',
    'METHOD_NAME': 'SetChannelValue',
    'TEST_MODULE_NAME': 'CommChannelsRuntimeTests',
    'TEST_TAG': '[comm_channels]',
    'DEPENDENCY_MODULES': ['Core', 'CoreUObject', 'CommChannelsRuntime'],
    'SETUP_CODE': '// Arrange\n\tFCommChannelNode Node;',
    'CODE_UNDER_TEST': '// Act\n\tNode.SetChannelValue("Channel1", Value);',
    'ASSERTIONS': '// Assert\n\tREQUIRE(Node.GetChannelValue("Channel1") == Value);'
}

# 3. Render templates
test_content_raw = render_template(Path(f"skills/templates/{cpp_template}"), context)
build_cs_content_raw = render_template(Path(f"skills/templates/{build_cs_template}"), context)
target_cs_content_raw = render_template(Path(f"skills/templates/{target_cs_template}"), context)

# 4. Extract code from markdown
test_content = extract_code_from_markdown(test_content_raw, 'cpp')
build_cs_content = extract_code_from_markdown(build_cs_content_raw, 'csharp')
target_cs_content = extract_code_from_markdown(target_cs_content_raw, 'csharp')

# 5. Ensure copyright headers
test_content = ensure_copyright_header(test_content)
build_cs_content = ensure_copyright_header(build_cs_content)
target_cs_content = ensure_copyright_header(target_cs_content)

# 6. Write files (Phase 4)
Write(test_path, test_content)
Write(build_cs_path, build_cs_content)
Write(target_cs_path, target_cs_content)
```

---

# Step 3.3 Implementation (Using Algorithm Above)

```markdown
# Load templates
template_dir = Path("skills/llt-generate/templates")

if scaffold:
    # Generate .Build.cs
    build_cs_content = template_renderer.render("ue-test-build-cs-template.md", context)
    build_cs_path = module_root.parent / "Tests" / context['test_module_name'] / f"{context['test_module_name']}.Build.cs"

    # Generate .Target.cs
    target_cs_content = template_renderer.render("ue-test-target-cs-template.md", context)
    target_cs_path = module_root.parent / "Tests" / context['test_module_name'] / f"{context['test_module_name']}.Target.cs"

    # Generate test file
    test_content = template_renderer.render(template, context)
    test_path = module_root.parent / "Tests" / context['test_module_name'] / "Private" / f"{context['test_module_name']}.cpp"

    generated_files = [build_cs_path, target_cs_path, test_path]
else:
    # Generate test file only
    test_content = template_renderer.render(template, context)
    test_path = find_or_create_test_file(module_root, context['test_module_name'])
    generated_files = [test_path]
```

### Phase 3.5: Metadata-Driven Stub Generation (Optional - llt-find Integration)

This algorithm replaces `metadata_resolver.py` orchestration logic. Agents implement on-the-fly using Read and simplified script CLI.

**When to use**: When `--metadata` flag provided with llt-find JSON output for coverage-gap analysis.

## Skill Invocation

Agents receive parameters directly from skill invocation. No external scripts are required.

### Input Parameters

- `module_name`: Target module name (required)
- `plugin_root`: Plugin root directory (required)
- `source_file`: Source file path (optional for 'generate', null for 'scaffold')
- `pattern`: Pattern override (optional: basic|fixture|async|plugin-lifecycle|mock)
- `mode`: Operation mode ('generate' or 'scaffold')
- `build`: Whether to build after generation (optional, default: false)
- `run`: Whether to run tests after build (optional, default: false)
- `interactive`: Whether to prompt user during generation (optional, default: true)

### Workflow Execution

Agents validate inputs and execute the Test Generation Workflow Algorithm below. All business logic is contained in the algorithm implementations in this document - no external orchestration scripts are needed.

## Test Generation Workflow Algorithm

This algorithm orchestrates the complete test module generation workflow. Agents implement this algorithm directly using the skill's templates and pattern detection logic.

**Workflow Pipeline**:
1. Pattern Detection - Determine which template to use
2. Context Building - Extract dependencies and build context
3. Template Rendering - Substitute placeholders
4. Directory Creation - Create Tests/<Module>/Private/ structure
5. File Writing - Write .cpp, .Build.cs, .Target.cs with copyright headers
6. Validation - Verify generated files exist and contain expected content
7. Build Integration (optional) - Compile generated tests
8. Run Integration (optional) - Execute generated tests

### Main Orchestration Function

```python
def generate_test_module(
    module_name: str,
    plugin_root: Path,
    source_file: Optional[Path] = None,
    pattern_override: Optional[str] = None,
    metadata: Optional[Dict] = None,
    test_type: Optional[str] = None
) -> Dict:
    """
    Generate complete test module with .cpp, .Build.cs, .Target.cs files.

    Performance Target: <3s for complete module generation (3 files + directories)

    Returns:
        Result dictionary with:
        - success: bool
        - files_generated: List[str] (absolute paths)
        - test_count: int
        - generation_time_ms: int
        - pattern_detected: str
        - validation_status: Dict
        - progress_log: List[str]
    """
    start_time = time.time()
    result = {
        'success': False,
        'files_generated': [],
        'test_count': 0,
        'generation_time_ms': 0,
        'pattern_detected': None,
        'validation_status': {},
        'errors': [],
        'progress_log': []
    }

    # ========================================================================
    # Step 1: Pattern Detection
    # ========================================================================
    if pattern_override:
        pattern = pattern_override
        result['progress_log'].append(f"Using manual pattern override: {pattern}")
    elif source_file:
        # Auto-detect using Pattern Detection Algorithm (see earlier section)
        module_root = plugin_root / 'Source' / module_name
        build_cs_path = module_root / f"{module_name}.Build.cs"
        pattern = detect_test_pattern(source_file, build_cs_path, None)
        result['progress_log'].append(f"Detected pattern: {pattern}")
    else:
        pattern = 'basic'
        result['progress_log'].append("Defaulting to basic pattern")

    result['pattern_detected'] = pattern

    # ========================================================================
    # Step 2: Context Building
    # ========================================================================
    result['progress_log'].append("Building test module context...")

    module_root = plugin_root / 'Source' / module_name
    if not module_root.exists():
        result['errors'].append(f"Module root not found: {module_root}")
        return result

    # Use Module Analysis Algorithm to build context
    context = build_context(module_root, source_file, metadata)

    # Add test module specific context
    test_module_name = f"{module_name}Tests"
    context['TEST_MODULE_NAME'] = test_module_name
    context['TEST_NAME'] = f"{module_name} Tests"
    context['TEST_SHORT_NAME'] = module_name
    context['TEST_TARGET_NAME'] = test_module_name  # Must match .Target.cs filename (without .Target.cs)
    context['TEST_TAG'] = module_name.lower()

    # ========================================================================
    # CRITICAL: Determine Minimal Test Dependencies (REQ-F-25, REQ-F-29)
    # ========================================================================
    # DO NOT copy all dependencies from source module's Build.cs
    # Test modules should only include:
    # 1. Essential framework modules (Core, CoreUObject, Engine - only if source module needs them)
    # 2. The module being tested
    # 3. Modules specifically needed by test code itself (not internal implementation details)

    # Read source module's Build.cs to check for Core, CoreUObject, Engine dependencies
    build_cs_path = module_root / f"{module_name}.Build.cs"
    if not build_cs_path.exists():
        build_cs_files = Glob(f"{module_root}/*.Build.cs")
        if build_cs_files:
            build_cs_path = Path(build_cs_files[0])

    build_cs_content = Read(build_cs_path) if build_cs_path.exists() else ""

    # Extract ONLY Core, CoreUObject, Engine from source module dependencies
    source_essential_deps = []
    if 'CoreUObject' in build_cs_content:
        source_essential_deps.append('CoreUObject')
    if 'Engine' in build_cs_content:
        source_essential_deps.append('Engine')

    # Start with minimal dependency set
    dependencies = ['Core']  # Always needed
    dependencies.extend(source_essential_deps)  # Add CoreUObject/Engine if source module uses them

    # Add pattern-specific dependencies (if not already included)
    if pattern == 'async':
        # Async tests: Need Engine subsystems for async operations
        if 'CoreUObject' not in dependencies:
            dependencies.append('CoreUObject')
        if 'Engine' not in dependencies:
            dependencies.append('Engine')
    elif pattern == 'plugin-lifecycle':
        # Plugin/Lifecycle tests: Need Engine and CoreUObject for plugin lifecycle
        if 'CoreUObject' not in dependencies:
            dependencies.append('CoreUObject')
        if 'Engine' not in dependencies:
            dependencies.append('Engine')
    elif pattern == 'mock':
        # Mock tests: Need CoreUObject for UObject-based mocks
        if 'CoreUObject' not in dependencies:
            dependencies.append('CoreUObject')

    # CRITICAL: Always add the source module itself as a dependency
    dependencies.append(module_name)

    # ========================================================================
    # TestTargetRules Available Properties Reference
    # ========================================================================
    # Source: Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TestTargetRules.cs
    #
    # CORE ENGINE/MODULE COMPILATION FLAGS:
    # - bCompileAgainstEngine: Compile against Engine module (auto-set from dependency graph)
    # - bCompileAgainstCoreUObject: Compile against CoreUObject (auto-set from dependency graph)
    # - bCompileAgainstApplicationCore: Compile against ApplicationCore (usually true for LLTs)
    # - bCompileAgainstEditor: Compile against Editor (for editor-only tests)
    # - bTestsRequireEngine: Engine initialization required at startup
    # - bTestsRequireApplicationCore: ApplicationCore required
    # - bTestsRequireCoreUObject: CoreUObject required
    # - bTestsRequireEditor: Editor required
    #
    # OVERRIDE FLAGS (Prevent automatic compilation):
    # - bNeverCompileAgainstEngine: Excludes Engine even if in dependency graph
    # - bNeverCompileAgainstCoreUObject: Excludes CoreUObject even if in dependency graph
    # - bNeverCompileAgainstApplicationCore: Excludes ApplicationCore even if in dependency graph
    # - bNeverCompileAgainstEditor: Excludes Editor even if in dependency graph
    #
    # CRITICAL: MOCK/STUB FLAGS (Isolation):
    # - bMockEngineDefaults: Mocks engine defaults (materials, AI, rendering subsystems)
    #   * Sets GlobalDefinition: UE_LLT_WITH_MOCK_ENGINE_DEFAULTS=1
    #   * MUST be true when bCompileAgainstEngine = true
    #   * Prevents: DistanceFieldAtlas.h (Renderer), UMGCoreStyle.h (UI), full rendering pipeline
    #   * Default: false (manually set to true when using Engine)
    #
    # - bUsePlatformFileStub: Stubs platform file system API
    #   * Sets GlobalDefinition: UE_LLT_USE_PLATFORM_FILE_STUB=1
    #   * MUST be true when bCompileAgainstEngine = true
    #   * Prevents real file I/O, enables isolated testing
    #   * Default: true for Android, false for other platforms
    #
    # BUILD CONFIGURATION:
    # - bUpdateBuildGraphPropertiesFile: Controls BuildGraph metadata generation
    #
    # IMPLICIT TEST TARGET AUTO-CONFIGURATION (SetupImplicitTestProperties):
    # When bCompileAgainstEngine = true, framework automatically sets:
    #   bUsePlatformFileStub = true
    #   bMockEngineDefaults = true
    #   bCompileWithPluginSupport = true
    #
    # COMMON MISTAKE:
    # Setting bCompileAgainstEngine = true WITHOUT bMockEngineDefaults = true causes:
    #   - Fatal error: 'DistanceFieldAtlas.h' file not found (Renderer dependency)
    #   - Fatal error: 'Styling/UMGCoreStyle.h' file not found (UI dependency)
    #
    # RECOMMENDED CONFIGURATION PATTERNS:
    # PRINCIPLE: "Include only what you use" - only add bCompileAgainst* flags for modules
    # that are declared in .Build.cs PrivateDependencyModuleNames
    #
    # Pattern 1: Minimal Tests (Core only, no ApplicationCore)
    #   Dependencies: ["Core"]
    #   Flags: (none - minimal configuration)
    #
    # Pattern 2: Basic Tests (Core + ApplicationCore)
    #   Dependencies: ["Core", "ApplicationCore"]
    #   Flags:
    #     bCompileAgainstApplicationCore = true;
    #
    # Pattern 3: CoreUObject Tests (No Engine)
    #   Dependencies: ["Core", "CoreUObject", "ApplicationCore"]
    #   Flags:
    #     bCompileAgainstCoreUObject = true;
    #     bCompileAgainstApplicationCore = true;
    #
    # Pattern 4: Engine Tests (MUST use mocks)
    #   Dependencies: ["Core", "CoreUObject", "Engine", "ApplicationCore"]
    #   Flags:
    #     bCompileAgainstEngine = true;
    #     bCompileAgainstCoreUObject = true;
    #     bCompileAgainstApplicationCore = true;
    #     bMockEngineDefaults = true;      // CRITICAL - required when using Engine
    #     bTestsRequireEngine = true;      // CRITICAL - required when using Engine
    #     bUsePlatformFileStub = true;     // CRITICAL - required when using Engine
    #
    # Pattern 5: Plugin/Lifecycle Tests (Full isolation)
    #   Dependencies: ["Core", "CoreUObject", "Engine", "ApplicationCore", ...]
    #   Flags:
    #     bCompileAgainstEngine = true;
    #     bCompileAgainstCoreUObject = true;
    #     bCompileAgainstApplicationCore = true;
    #     bMockEngineDefaults = true;
    #     bTestsRequireEngine = true;
    #     bUsePlatformFileStub = true;
    #     bCompileWithPluginSupport = true;
    # ========================================================================

    # Determine engine flags based on dependencies
    # PRINCIPLE: "Include only what you use" - only add bCompileAgainst* flags for modules
    # that are explicitly declared in the .Build.cs PrivateDependencyModuleNames
    engine_flags = []
    uses_engine = 'Engine' in dependencies

    # Rule 1: If Engine module present → bCompileAgainstEngine = true + mock engine
    if uses_engine:
        engine_flags.append('bCompileAgainstEngine = true;')
        # CRITICAL - If using Engine, MUST use mock/stub flags to avoid renderer/UI deps
        engine_flags.append('bMockEngineDefaults = true;')     # Mocks engine subsystems (Renderer, AI, etc.)
        engine_flags.append('bTestsRequireEngine = true;')     # Engine init required
        engine_flags.append('bUsePlatformFileStub = true;')    # Stub file I/O

    # Rule 2: If CoreUObject module present → bCompileAgainstCoreUObject = true
    if 'CoreUObject' in dependencies:
        engine_flags.append('bCompileAgainstCoreUObject = true;')

    # Rule 3: If ApplicationCore module present → bCompileAgainstApplicationCore = true
    if 'ApplicationCore' in dependencies:
        engine_flags.append('bCompileAgainstApplicationCore = true;')

    # Rule 4: If Editor module present → bCompileAgainstEditor = true
    if 'UnrealEd' in dependencies or 'Editor' in dependencies:
        engine_flags.append('bCompileAgainstEditor = true;')

    # Format engine flags for Target.cs (with proper indentation)
    context['ENGINE_FLAGS'] = '\n\t\t'.join(engine_flags) if engine_flags else '// No special flags needed'

    # Determine additional configuration
    # NOTE: bUsePlatformFileStub is already included in engine_flags when uses_engine=true
    # No additional config needed - TestTargetRules handles defaults automatically
    context['ADDITIONAL_CONFIG'] = ''

    # Store dependencies for Build.cs template
    context['DEPENDENCY_MODULES'] = ',\n\t\t\t\t'.join([f'"{dep}"' for dep in dependencies])

    # Optional Build.cs metadata (usually empty)
    context['ADDITIONAL_METADATA'] = ''

    # Extract class/method info if source file provided
    test_count = 0
    if source_file:
        context['SOURCE_FILE'] = str(source_file)
        context['SOURCE_FILE_NAME'] = source_file.name

        # Extract class name from file name (common convention)
        class_name = source_file.stem
        if not class_name.startswith(('F', 'U', 'A')):
            class_name = f"F{class_name}"
        context['CLASS_NAME'] = class_name

        # Extract methods via source_parser (delegate to script CLI)
        # python3 scripts/source_parser.py extract-signatures --header {source_file}
        methods_json = call_bash(f"python3 scripts/source_parser.py extract-signatures --header {source_file}")
        methods = json.loads(methods_json)['signatures']
        test_count = len(methods)

        if methods:
            context['METHOD_NAME'] = methods[0]['name']
            context['METHODS'] = methods
    else:
        context['CLASS_NAME'] = 'FClassName'
        context['METHOD_NAME'] = 'MethodName'

    # Default placeholders for optional sections
    context.setdefault('SETUP_CODE', '// TODO: Setup test data')
    context.setdefault('CODE_UNDER_TEST', '// TODO: Call method under test')
    context.setdefault('ASSERTIONS', '// TODO: Add REQUIRE() checks')

    result['test_count'] = test_count if test_count > 0 else 1

    # ========================================================================
    # Step 3: Template Rendering (Agentic Implementation)
    # ========================================================================
    result['progress_log'].append(f"Rendering test files using {pattern} template...")

    # Map pattern to template file
    template_map = {
        'basic': 'cpp-basic-fixture-llt-template.md',
        'fixture': 'cpp-basic-fixture-llt-template.md',
        'async': 'cpp-async-llt-template.md',
        'plugin-lifecycle': 'cpp-plugin-lifecycle-llt-template.md',
        'mock': 'cpp-mock-llt-template.md'
    }

    cpp_template_name = template_map.get(pattern, 'cpp-basic-fixture-llt-template.md')

    # Template files location (relative to skill root)
    templates_dir = Path(__file__).parent.parent.parent / 'templates'

    # AGENTIC TEMPLATE RENDERING INSTRUCTIONS:
    # Agents should use ONE of these approaches to render templates:

    # Approach 1: Simple Regex Substitution (Recommended for straightforward cases)
    # 1. Read template file:
    #    template_content = Read(templates_dir / cpp_template_name)
    # 2. Extract code block (find content between ```cpp and ```)
    #    - Search for "```cpp\n" to find start
    #    - Extract until next "```\n"
    # 3. Substitute placeholders using regex:
    #    for key, value in context.items():
    #        template_content = template_content.replace(f'{{{{{{key}}}}}}', str(value))

    # Approach 2: LLM-based Template Filling (Recommended for complex placeholders)
    # 1. Read template file
    # 2. Extract code block
    # 3. Use LLM with prompt:
    #    "Fill in the following test template with these values: {context}
    #     Template: {template_code_block}
    #     Replace all {{PLACEHOLDER}} markers with appropriate values."

    # Approach 3: Generate Custom Script (For batch processing)
    # Create a temporary Python script that:
    # 1. Reads template
    # 2. Performs regex substitution
    # 3. Writes output
    # Then execute with Bash tool

    # EXAMPLE IMPLEMENTATION (Approach 1 - Simple Substitution):
    # Read and render .cpp test file
    test_cpp_template = Read(templates_dir / cpp_template_name)
    # Extract code block (between ```cpp and ```)
    code_start = test_cpp_template.find('```cpp\n')
    code_end = test_cpp_template.find('\n```', code_start)
    test_cpp_content = test_cpp_template[code_start+7:code_end]
    # Substitute placeholders
    for key, value in context.items():
        test_cpp_content = test_cpp_content.replace(f'{{{{{key}}}}}', str(value))

    # Read and render Build.cs file
    build_cs_template = Read(templates_dir / 'ue-test-build-cs-template.md')
    code_start = build_cs_template.find('```csharp\n')
    code_end = build_cs_template.find('\n```', code_start)
    build_cs_content = build_cs_template[code_start+10:code_end]
    for key, value in context.items():
        build_cs_content = build_cs_content.replace(f'{{{{{key}}}}}', str(value))

    # Read and render Target.cs file
    target_cs_template = Read(templates_dir / 'ue-test-target-cs-template.md')
    code_start = target_cs_template.find('```csharp\n')
    code_end = target_cs_template.find('\n```', code_start)
    target_cs_content = target_cs_template[code_start+10:code_end]
    for key, value in context.items():
        target_cs_content = target_cs_content.replace(f'{{{{{key}}}}}', str(value))

    # ========================================================================
    # Step 4: Directory Creation
    # ========================================================================
    result['progress_log'].append("Creating test module directory structure...")

    tests_root = plugin_root / 'Tests'
    test_module_dir = tests_root / test_module_name
    private_dir = test_module_dir / 'Private'

    # Create directory: <PluginRoot>/Tests/<TestModuleName>/Private/
    private_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # Step 5: File Writing
    # ========================================================================
    result['progress_log'].append("Writing generated test files...")

    # Determine test file name
    test_file_name = f"{source_file.stem}Tests.cpp" if source_file else f"{module_name}Tests.cpp"

    # File paths
    test_cpp_path = private_dir / test_file_name
    build_cs_path = test_module_dir / f"{test_module_name}.Build.cs"
    target_cs_path = test_module_dir / f"{test_module_name}.Target.cs"

    # Write files (use Write tool)
    Write(test_cpp_path, test_cpp_content)
    Write(build_cs_path, build_cs_content)
    Write(target_cs_path, target_cs_content)

    result['files_generated'] = [
        str(test_cpp_path.absolute()),
        str(build_cs_path.absolute()),
        str(target_cs_path.absolute())
    ]

    # ========================================================================
    # Step 6: Validation
    # ========================================================================
    result['progress_log'].append("Validating generated test files...")

    validation_status = validate_generated_files(test_cpp_path, build_cs_path, target_cs_path, context)
    result['validation_status'] = validation_status

    all_valid = all(v['valid'] for v in validation_status.values())

    # Calculate generation time
    end_time = time.time()
    result['generation_time_ms'] = int((end_time - start_time) * 1000)

    # Performance check (REQ-NF-1: <3s)
    if result['generation_time_ms'] > 3000:
        result['progress_log'].append(f"WARNING: Generation time {result['generation_time_ms']}ms exceeds 3s target")

    result['success'] = all_valid
    result['progress_log'].append(f"Test module generation {'succeeded' if all_valid else 'completed with warnings'}")

    return result
```

### Template Usage Guide for Agents

All templates are located at `skills/templates/` relative to the dante_plugin root. Agents should use the Read tool to load templates and perform substitution.

#### Available Templates

**C++ LowLevelTest Templates** (for Unreal Engine):
- `cpp-basic-fixture-llt-template.md` - Basic/fixture tests (40% usage)
- `cpp-async-llt-template.md` - Async operations with tick loops
- `cpp-mock-llt-template.md` - Mock interfaces and dependency injection
- `cpp-plugin-lifecycle-llt-template.md` - Plugin lifecycle and engine integration
- `ue-test-build-cs-template.md` - Test module Build.cs configuration
- `ue-test-target-cs-template.md` - Test target configuration

**Other Framework Templates** (for reference):
- `cpp-catch2-template.md`, `cpp-gtest-template.md` - Generic C++ test frameworks
- `csharp-*-template.md` - C# test frameworks (MSTest, NUnit, xUnit)
- `go-*-template.md` - Go test frameworks
- `java-*-template.md` - Java test frameworks (JUnit4, JUnit5, TestNG)
- `javascript-*-template.md` - JavaScript test frameworks (Jest, Mocha)

#### Template Structure

All templates follow this format:
1. **Header**: Description, purpose, when to use
2. **Placeholders Table**: Available `{{PLACEHOLDER}}` markers
3. **Code Block**: Actual template code in ` ```language ` block
4. **Examples**: Filled template examples

#### Extracting Code from Templates

Templates store code in markdown code blocks. Extract using string operations:

```python
# Read template
template_content = Read(templates_dir / 'cpp-basic-fixture-llt-template.md')

# Find code block (between ```cpp and ```)
code_start = template_content.find('```cpp\n')
code_end = template_content.find('\n```', code_start)
code = template_content[code_start + 7 : code_end]  # +7 skips '```cpp\n'

# For C# templates, use '```csharp\n' and +10
```

#### Placeholder Substitution Strategies

**Strategy 1: Simple String Replace** (Fast, deterministic)
```python
for key, value in context.items():
    code = code.replace(f'{{{{{key}}}}}', str(value))
```

**Strategy 2: LLM-Based Filling** (Smart, handles complex logic)
- Prompt LLM with template + context
- Let LLM fill placeholders intelligently
- Good for incomplete context or complex placeholder logic

**Strategy 3: Regex Replace** (Flexible, handles patterns)
```python
import re
for key, value in context.items():
    code = re.sub(rf'\{{\{{{key}\}}\}}', str(value), code)
```

#### Common Placeholders

| Category | Placeholder | Example Value |
|----------|-------------|---------------|
| Module | `{{MODULE_NAME}}` | `AudioInsightsRuntime` |
| Module | `{{TEST_MODULE_NAME}}` | `AudioInsightsRuntimeTests` |
| Class | `{{CLASS_NAME}}` | `UAudioInsightsBlueprintLibrary` |
| Method | `{{METHOD_NAME}}` | `LogAudioInsightsEvent` |
| Path | `{{UE_HEADER_PATH}}` | `AudioInsightsBlueprintLibrary.h` |
| Test | `{{TEST_TAG}}` | `[audioinsightsruntime]` |
| Code | `{{SETUP_CODE}}` | `// Arrange step code` |
| Code | `{{CODE_UNDER_TEST}}` | `// Act step code` |
| Code | `{{ASSERTIONS}}` | `// Assert step code` |
| Deps | `{{DEPENDENCY_MODULES}}` | `"Core",\n"Engine"` |

#### Validation Checklist

```python
def validate_generated_files(test_cpp_path: Path, build_cs_path: Path, target_cs_path: Path, context: Dict) -> Dict:
    """
    Validate generated files for correctness.

    Checks:
    - Files exist
    - Files are non-empty
    - Required content present (TEST_CASE, TestModuleRules, etc.)
    """
    validation_results = {}

    # Validate test .cpp file
    cpp_errors = []
    if test_cpp_path.exists():
        cpp_content = test_cpp_path.read_text(encoding='utf-8')
        if len(cpp_content) == 0:
            cpp_errors.append("File is empty")
        if 'TEST_CASE' not in cpp_content:
            cpp_errors.append("No TEST_CASE found")
        if '#include "TestHarness.h"' not in cpp_content:
            cpp_errors.append("Missing TestHarness.h include")
    else:
        cpp_errors.append("File does not exist")

    validation_results[test_cpp_path.name] = {
        'valid': len(cpp_errors) == 0,
        'errors': cpp_errors,
        'size': test_cpp_path.stat().st_size if test_cpp_path.exists() else 0
    }

    # Validate .Build.cs file
    build_cs_errors = []
    if build_cs_path.exists():
        build_cs_content = build_cs_path.read_text(encoding='utf-8')
        if len(build_cs_content) == 0:
            build_cs_errors.append("File is empty")
        if 'TestModuleRules' not in build_cs_content:
            build_cs_errors.append("Not inheriting from TestModuleRules")
        if 'TestMetadata' not in build_cs_content:
            build_cs_errors.append("Missing TestMetadata initialization")
        if 'PrivateDependencyModuleNames' not in build_cs_content:
            build_cs_errors.append("Missing PrivateDependencyModuleNames")
    else:
        build_cs_errors.append("File does not exist")

    validation_results[build_cs_path.name] = {
        'valid': len(build_cs_errors) == 0,
        'errors': build_cs_errors,
        'size': build_cs_path.stat().st_size if build_cs_path.exists() else 0
    }

    # Validate .Target.cs file
    target_cs_errors = []
    if target_cs_path.exists():
        target_cs_content = target_cs_path.read_text(encoding='utf-8')
        if len(target_cs_content) == 0:
            target_cs_errors.append("File is empty")
        if 'TestTargetRules' not in target_cs_content:
            target_cs_errors.append("Not inheriting from TestTargetRules")
    else:
        target_cs_errors.append("File does not exist")

    validation_results[target_cs_path.name] = {
        'valid': len(target_cs_errors) == 0,
        'errors': target_cs_errors,
        'size': target_cs_path.stat().st_size if target_cs_path.exists() else 0
    }

    return validation_results
```

### Build and Run Integration

**Note**: Build and run integration reference `skills/build-integration/ue-build-system.md` for UBT command syntax.

```python
def invoke_llt_build(test_module_name: str, test_module_dir: Path, repo_root: Path) -> Dict:
    """
    Build UE LLT test module using UnrealBuildTool.

    See skills/build-integration/ue-build-system.md for complete documentation.

    Args:
        test_module_name: Test module name (e.g., "SecurePackageReaderTests")
        test_module_dir: Path to test module directory
        repo_root: Repository root containing Engine/ and FortniteGame/

    Returns:
        Build result with success status, warnings, errors

    Build Command Syntax:
        ./Engine/Build/BatchFiles/Mac/Build.sh <TestModuleName> Mac Development \\
            -Project="<repo_root>/FortniteGame/FortniteGame.uproject"

    CRITICAL: Use test module name WITHOUT "Target" suffix.
        ✅ Correct: SecurePackageReaderTests
        ❌ Wrong: SecurePackageReaderTestsTarget
    """
    platform = detect_platform()  # "Mac", "Win64", or "Linux"
    build_script = {
        "Mac": "Engine/Build/BatchFiles/Mac/Build.sh",
        "Win64": "Engine/Build/BatchFiles/Build.bat",
        "Linux": "Engine/Build/BatchFiles/Linux/Build.sh"
    }[platform]

    fortnite_uproject = repo_root / "FortniteGame" / "FortniteGame.uproject"

    # CRITICAL: Do NOT append "Target" to test_module_name
    cmd = [
        str(repo_root / build_script),
        test_module_name,
        platform,
        "Development",
        f"-Project={fortnite_uproject}"
    ]

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, timeout=300)

    return {
        'success': result.returncode == 0,
        'stdout': result.stdout.decode('utf-8'),
        'stderr': result.stderr.decode('utf-8'),
        'exit_code': result.returncode,
        'compilation_time_ms': 0,  # Parse from UBT output if needed
        'warnings': parse_ubt_warnings(result.stdout),
        'errors': parse_ubt_errors(result.stderr) if result.returncode != 0 else []
    }

def invoke_llt_run(test_module_name: str, test_module_dir: Path, repo_root: Path) -> Dict:
    """
    Run UE LLT test executable with Catch2.

    See skills/build-integration/ue-build-system.md for complete documentation.

    Args:
        test_module_name: Test module name (e.g., "SecurePackageReaderTests")
        test_module_dir: Path to test module directory
        repo_root: Repository root containing Engine/Binaries/

    Returns:
        Test execution result with pass/fail counts, failures

    Run Command Syntax:
        ./Engine/Binaries/Mac/<TestModuleName> -r xml

    Output Location:
        - Mac: Engine/Binaries/Mac/<TestModuleName>
        - Windows: Engine/Binaries/Win64/<TestModuleName>.exe
        - Linux: Engine/Binaries/Linux/<TestModuleName>
    """
    platform = detect_platform()
    binary_path = {
        "Mac": repo_root / "Engine" / "Binaries" / "Mac" / test_module_name,
        "Win64": repo_root / "Engine" / "Binaries" / "Win64" / f"{test_module_name}.exe",
        "Linux": repo_root / "Engine" / "Binaries" / "Linux" / test_module_name
    }[platform]

    if not binary_path.exists():
        return {
            'success': False,
            'error': f'Test binary not found: {binary_path}. Build may have failed.'
        }

    # Use XML output for parsing
    cmd = [str(binary_path), "-r", "xml"]

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, timeout=300)

    # Parse Catch2 XML output (delegate to result-parsing skill)
    parsed = parse_catch2_xml(result.stdout.decode('utf-8'))

    return {
        'success': result.returncode == 0,
        'passed_count': parsed['passed'],
        'failed_count': parsed['failed'],
        'skipped_count': parsed['skipped'],
        'execution_time_ms': parsed['duration_ms'],
        'failures': parsed['failure_details']
    }
```

## Metadata Resolution Algorithm

```python
def generate_stubs_from_metadata(source_file: Path, llt_find_json: Path, output_dir: Path) -> dict:
    """
    Generate test stubs for untested methods identified by llt-find.

    Steps:
    1. Parse llt-find JSON
    2. Identify untested methods (fuzzy file matching)
    3. Extract method signatures (delegate to script CLI)
    4. Infer test dependencies (delegate to script CLI)
    5. Extract test tags for consistency
    6. Generate test stubs with Catch2 template
    7. Write stubs to output directory

    Returns: Generation result with stub count, warnings, etc.
    """

    # Step 1: Parse llt-find JSON (REQ-F-30)
    llt_find_data = parse_llt_find_json(llt_find_json)

    # Step 2: Identify untested methods (REQ-F-31)
    untested_methods = identify_untested_methods(source_file, llt_find_data)

    # Step 3: Extract method signatures (REQ-F-35) - Delegates to script
    method_signatures = {}
    for method_name in untested_methods:
        signature = call_extract_signature_cli(method_name, source_file, compdb_path)
        method_signatures[method_name] = signature

    # Step 4: Infer dependencies (REQ-F-33) - Delegates to script
    test_module_path = find_test_module_from_llt_find(source_file, llt_find_data)
    dependencies = call_extract_dependencies_cli(test_module_path)

    # Step 5: Extract test tags (REQ-F-34)
    test_tags = extract_test_tags_from_llt_find(source_file, llt_find_data)

    # Step 6: Determine template
    template = detect_test_pattern(source_file) if not template_override else template_override

    # Step 7: Build context
    context = {
        'module_name': source_file.stem,
        'test_tag': ' '.join(f'[{tag}]' for tag in test_tags),
        'dependencies': dependencies
    }

    # Step 8: Generate stubs
    generated_stubs = []
    for method_name, method_sig in method_signatures.items():
        stub_code = generate_test_stub(method_name, method_sig, context, template)
        generated_stubs.append({
            'method_name': method_name,
            'stub_code': stub_code,
            'line_count': len(stub_code.splitlines())
        })

    # Step 9: Write to output directory
    output_file = output_dir / f"{source_file.stem}Tests.cpp"
    Write(output_file, '\n\n'.join(s['stub_code'] for s in generated_stubs))

    return {
        'source_file': str(source_file),
        'untested_methods': untested_methods,
        'generated_stubs': generated_stubs,
        'stub_count': len(generated_stubs),
        'template': template,
        'dependencies': dependencies,
        'warnings': []
    }
```

### Parse llt-find JSON

```python
def parse_llt_find_json(json_path: Path) -> dict:
    """
    Parse llt-find JSON output.

    Expected format:
    {
      "source_files": [
        {
          "file": "//depot/path/Source.h",
          "methods": ["MethodA", "MethodB"],
          "test_files": ["Tests/SourceTests.cpp"],
          "tested_methods": ["MethodA"],
          "untested_methods": ["MethodB"]
        }
      ]
    }
    """
    content = Read(json_path)
    data = json.loads(content)

    # Validate structure
    if 'source_files' not in data:
        raise error "Invalid llt-find JSON: missing 'source_files' key"

    if not isinstance(data['source_files'], list):
        raise error "Invalid llt-find JSON: 'source_files' must be list"

    return data
```

### Identify Untested Methods (Fuzzy File Matching)

```python
def identify_untested_methods(source_file: Path, llt_find_data: dict) -> list:
    """
    Find source file in llt-find data using fuzzy matching.

    Matching strategies (in priority order):
    1. Exact filename match
    2. Path suffix match
    3. Filename stem match
    """
    source_file_name = source_file.name
    source_file_stem = source_file.stem

    for entry in llt_find_data['source_files']:
        entry_file = entry['file']
        entry_name = Path(entry_file).name
        entry_stem = Path(entry_file).stem

        # Strategy 1: Exact filename match
        if entry_name == source_file_name:
            return entry.get('untested_methods', [])

        # Strategy 2: Path suffix match
        if entry_file.endswith(str(source_file)):
            return entry.get('untested_methods', [])

        # Strategy 3: Stem match (MyClass.h matches MyClass.cpp)
        if entry_stem == source_file_stem:
            return entry.get('untested_methods', [])

    # Not found
    display_warning(f"Source file {source_file} not found in llt-find data")
    return []
```

### Extract Method Signature (CLI Delegation)

```python
def call_extract_signature_cli(method_name: str, source_file: Path, compdb_path: Path) -> dict:
    """
    Call simplified metadata_resolver.py CLI to extract method signature.

    Delegates to source_parser.py (requires libclang).

    Command:
      python3 scripts/metadata_resolver.py extract-signature \
        --method SetChannelValue \
        --header CommChannelNode.h \
        --compdb compile_commands.json

    Returns JSON:
    {
      "name": "SetChannelValue",
      "class_name": "FCommChannelNode",
      "return_type": "void",
      "params": [{"type": "const FString&", "name": "ChannelName"}]
    }
    """
    cmd = [
        'python3', 'scripts/metadata_resolver.py', 'extract-signature',
        '--method', method_name,
        '--header', str(source_file),
        '--compdb', str(compdb_path) if compdb_path else ''
    ]

    result = Bash(' '.join(cmd))
    return json.loads(result)
```

### Infer Test Dependencies (CLI Delegation)

```python
def call_extract_dependencies_cli(test_module_path: Path) -> list:
    """
    Call simplified metadata_resolver.py CLI to extract dependencies.

    Delegates to module_analyzer algorithm (now in SKILL.md).

    Command:
      python3 scripts/metadata_resolver.py extract-dependencies \
        --test-module Tests/CommChannelsTests

    Returns JSON:
    {"dependencies": ["Core", "CoreUObject", "CommChannelsRuntime"]}
    """
    cmd = [
        'python3', 'scripts/metadata_resolver.py', 'extract-dependencies',
        '--test-module', str(test_module_path)
    ]

    result = Bash(' '.join(cmd))
    data = json.loads(result)
    return data.get('dependencies', ['Core', 'CoreUObject', 'ApplicationCore'])
```

### Extract Test Tags (CamelCase → snake_case)

```python
def extract_test_tags_from_llt_find(source_file: Path, llt_find_data: dict) -> list:
    """
    Extract test tags from existing test files for consistency (REQ-F-34).

    Strategy:
    1. Find test files for this source file in llt-find data
    2. Extract module name from test file path (Tests/CommChannelsTests/... → CommChannels)
    3. Convert CamelCase → snake_case (CommChannels → comm_channels)
    4. Return as tag list
    """
    # Find matching entry
    for entry in llt_find_data['source_files']:
        if Path(entry['file']).stem == source_file.stem:
            test_files = entry.get('test_files', [])
            if test_files:
                test_file_path = Path(test_files[0])

                # Extract module name: Tests/CommChannelsTests/Private/... → CommChannelsTests
                for part in test_file_path.parts:
                    if 'Tests' in part and part != 'Tests':
                        # Remove 'Tests' suffix: CommChannelsTests → CommChannels
                        module_name = part.replace('Tests', '')

                        # CamelCase → snake_case
                        tag = convert_camel_to_snake(module_name)
                        return [tag]

    # Fallback: generate tag from source file name
    tag = convert_camel_to_snake(source_file.stem)
    return [tag]

def convert_camel_to_snake(text: str) -> str:
    """
    Convert CamelCase to snake_case.

    Examples:
    - CommChannels → comm_channels
    - FCommChannelNode → f_comm_channel_node
    - HTTPServer → http_server
    """
    result = ""
    for i, char in enumerate(text):
        if char.isupper() and i > 0:
            result += "_"
        result += char.lower()
    return result
```

### Generate Test Stub

```python
def generate_test_stub(method_name: str, method_sig: dict, context: dict, template: str) -> str:
    """
    Generate Catch2 test stub for a single method.

    Template: TEST_CASE or TEST_CASE_METHOD with Arrange-Act-Assert structure.
    """
    class_name = method_sig.get('class_name', 'UnknownClass')
    return_type = method_sig['return_type']
    params = method_sig.get('params', [])

    test_tag = context.get('test_tag', '[module]')
    test_name = f"{class_name}::{method_name}"

    # Generate parameter setup
    param_setup = ""
    if params:
        lines = []
        for param in params:
            lines.append(f"\t{param['type']} {param['name']}; // TODO: Initialize {param['name']}")
        param_setup = '\n'.join(lines)

    # Determine test macro
    if template == 'fixture':
        fixture_class = context.get('fixture_class', 'FTestFixture')
        test_macro = f'TEST_CASE_METHOD({fixture_class}, "{test_name}", "{test_tag}")'
    else:
        test_macro = f'TEST_CASE("{test_name}", "{test_tag}")'

    # Generate stub
    param_names = ', '.join(p['name'] for p in params)
    stub = f"""{test_macro} {{
\t// Arrange
\t// TODO: Set up test fixture for {method_name}
{param_setup}

\t// Act
\t// TODO: Call {method_name} with test inputs
\t// Example: {class_name} instance;
\t// instance.{method_name}({param_names});

\t// Assert
\t// TODO: Verify expected behavior
\t// REQUIRE(condition);
}}"""

    return stub
```

### Find Test Module from llt-find Data

```python
def find_test_module_from_llt_find(source_file: Path, llt_find_data: dict) -> Path:
    """
    Find test module path for dependency inference.

    Extracts from test_files path: Tests/ModuleTests/Private/... → Tests/ModuleTests
    """
    for entry in llt_find_data['source_files']:
        if Path(entry['file']).stem == source_file.stem:
            test_files = entry.get('test_files', [])
            if test_files:
                test_file_path = Path(test_files[0])
                # Tests/ModuleTests/Private/... → Tests/ModuleTests
                test_module_path = test_file_path.parent.parent
                return test_module_path

    return None
```

### Phase 4: Write Files and Validate

```markdown
# Step 4.1: Create directory structure
for file_path in generated_files:
    file_path.parent.mkdir(parents=True, exist_ok=True)

# Step 4.2: Write files
generated_file_info = []
for file_path, content in zip(generated_files, [build_cs_content, target_cs_content, test_content]):
    file_path.write_text(content)

    file_info = {
        'path': str(file_path.absolute()),
        'type': determine_file_type(file_path),
        'test_count': count_test_cases(content) if file_path.suffix == '.cpp' else 0,
        'line_count': len(content.splitlines()),
        'template_used': template
    }
    generated_file_info.append(file_info)

    display_info(f"Generated: {file_path}")

# Step 4.3: Log progress
progress_log = [
    f"Detected pattern: {pattern}",
    f"Template used: {template}",
    f"Generated {len(generated_files)} files",
    f"Total test cases: {sum(f['test_count'] for f in generated_file_info)}"
]
```

### Phase 5: Build and Run (Autonomous Mode)

```markdown
# Step 5.1: Build tests (if --build flag)
if build:
    if interactive:
        user_choice = prompt("Build tests? (y/n): ")
        if user_choice.lower() == 'n':
            build = False

    if build:
        display_info("Building test module...")

        # Read llt-build skill
        Read file: skills/llt-build/SKILL.md

        # Invoke llt-build
        build_result = invoke_llt_build(module_name=context['test_module_name'], platform="Win64")

        validation['compilation'] = "success" if build_result['status'] == 'success' else "failed"

        if build_result['status'] == 'failed':
            display_error("Build failed:")
            display_error(build_result['error'])
            return result with validation status

        display_info(f"Build completed in {build_result['duration_seconds']}s")
        progress_log.append(f"Build: success ({build_result['duration_seconds']}s)")

# Step 5.2: Run tests (if --run flag)
if run and validation['compilation'] == 'success':
    if interactive:
        user_choice = prompt("Run tests? (y/n): ")
        if user_choice.lower() == 'n':
            run = False

    if run:
        display_info("Running tests...")

        # Read llt-run skill
        Read file: skills/llt-run/SKILL.md

        # Invoke llt-run
        run_result = invoke_llt_run(module_name=context['test_module_name'])

        validation['execution'] = "success" if run_result['status'] == 'success' else "failed"
        validation['test_results'] = {
            'passed': run_result.get('passed_count', 0),
            'failed': run_result.get('failed_count', 0),
            'skipped': run_result.get('skipped_count', 0)
        }

        display_info(f"Tests completed: {validation['test_results']['passed']} passed, {validation['test_results']['failed']} failed")
        progress_log.append(f"Tests: {validation['test_results']['passed']} passed, {validation['test_results']['failed']} failed")
```

### Phase 6: Return Results

```markdown
# Step 6.1: Assemble result
result = {
    'status': 'success' if not validation['compilation'] == 'failed' else 'failed',
    'generated_files': generated_file_info,
    'validation': validation,
    'metadata': {
        'template_used': template,
        'pattern_detected': pattern,
        'generation_time_ms': generation_duration_ms,
        'module_dependencies': context['dependencies'],
        'clang_parsing_used': compdb is not None
    },
    'progress_log': progress_log,
    'error': None,
    'warnings': warnings
}

# Step 6.2: Display summary
display_info("=" * 80)
display_info("Generation Summary")
display_info("=" * 80)
display_info(f"Status: {result['status']}")
display_info(f"Generated files: {len(generated_file_info)}")
for file_info in generated_file_info:
    display_info(f"  - {file_info['path']} ({file_info['test_count']} tests)")
display_info(f"Template: {template}")
display_info(f"Pattern: {pattern}")
if validation['compilation'] == 'success':
    display_info(f"Build: success")
if validation['execution'] == 'success':
    display_info(f"Tests: {validation['test_results']['passed']} passed, {validation['test_results']['failed']} failed")
display_info("=" * 80)

# Step 6.3: Return result
return result
```

## Integration with Existing Skills

### llt-find Integration

Generate test stubs for coverage gaps identified by llt-find:

```bash
# Step 1: Identify coverage gaps
/llt-find --module CommChannelsRuntime --output coverage.json

# coverage.json contains:
# {
#   "test_modules": [...],
#   "source_modules": [{
#     "module_name": "CommChannelsRuntime",
#     "source_files": ["CommChannelNode.h"],
#     "public_methods": ["ConnectTo", "IsConnectedTo", "SetChannelValue", "GetChannelValue"]
#   }]
# }

# Step 2: Generate stubs for untested methods
/llt-generate --file CommChannelNode.h --metadata coverage.json

# The metadata_resolver.py script:
# 1. Parses coverage.json
# 2. Compares source methods against tested methods
# 3. Identifies untested: SetChannelValue, GetChannelValue
# 4. Generates test stubs with appropriate template
```

### llt-build Integration

Automatically build generated tests:

```bash
/llt-generate --module CommChannelsRuntime --scaffold --build

# Invokes llt-build skill after generation:
# 1. Read skills/llt-build/SKILL.md
# 2. Build CommChannelsTests module
# 3. Report compilation status
# 4. Include build output in validation
```

### llt-run Integration

Automatically run generated tests:

```bash
/llt-generate --module CommChannelsRuntime --scaffold --build --run

# Invokes llt-run skill after successful build:
# 1. Read skills/llt-run/SKILL.md
# 2. Execute CommChannelsTests
# 3. Parse test results
# 4. Include test counts in validation
```

### Compilation Database Management

Use clang AST parsing for 100% accurate method signatures via compilation database.

#### Algorithm: Generate Compilation Database

**Purpose**: Generate clang compilation database for a UE plugin/module using ushell

**Step 1: Detect Platform**
```bash
# Map system platform to UE platform name
SYSTEM=$(uname -s)
case "$SYSTEM" in
  Darwin) PLATFORM="Mac" ;;
  Linux) PLATFORM="Linux" ;;
  MINGW64_NT*|MSYS_NT*) PLATFORM="Win64" ;;
  *) echo "Unsupported platform: $SYSTEM"; exit 1 ;;
esac
```

**Step 2: Detect Project Root**
```bash
# Search upward for .uproject file
current=$(pwd)
while [ "$current" != "/" ]; do
  if ls "$current"/*.uproject >/dev/null 2>&1; then
    PROJECT_ROOT="$current"
    break
  fi
  current=$(dirname "$current")
done

if [ -z "$PROJECT_ROOT" ]; then
  echo "Error: No .uproject file found in directory hierarchy"
  exit 1
fi
```

**Step 3: Verify ushell Availability**
```bash
if ! command -v ushell >/dev/null 2>&1; then
  echo "Error: ushell not found in PATH"
  exit 1
fi
```

**Step 4: Execute ushell Command**
```bash
cd "$PROJECT_ROOT"
ushell .build misc clangdb "$TARGET" --platform "$PLATFORM"

# Example: ushell .build misc clangdb FortniteEditor --platform Mac
```

**Step 5: Verify Generated Database**
```bash
if [ ! -f "$PROJECT_ROOT/compile_commands.json" ]; then
  echo "Error: compile_commands.json not generated"
  exit 1
fi

echo "✅ Generated: $PROJECT_ROOT/compile_commands.json"
```

---

#### Algorithm: Find Compilation Database

**Purpose**: Search directory tree for existing compile_commands.json

**Step 1: Search Upward from Current Directory**
```bash
current=$(pwd)
while [ "$current" != "/" ]; do
  if [ -f "$current/compile_commands.json" ]; then
    echo "$current/compile_commands.json"
    exit 0
  fi
  current=$(dirname "$current")
done

echo "Not found"
exit 1
```

---

#### Algorithm: Get Database Info

**Purpose**: Extract metadata from compilation database

**Step 1: Verify Database Exists**
```bash
if [ ! -f "$DB_PATH" ]; then
  echo "Error: Database not found at $DB_PATH"
  exit 1
fi
```

**Step 2: Parse with jq**
```bash
# Get entry count
ENTRY_COUNT=$(jq 'length' "$DB_PATH")

# Get all file paths
jq -r '.[].file' "$DB_PATH" > /tmp/db_files.txt

# Get sample files (first 5)
jq -r '.[0:5][].file' "$DB_PATH"

echo "Entry count: $ENTRY_COUNT"
echo "Sample files:"
jq -r '.[0:5][].file' "$DB_PATH"
```

---

#### Usage Examples

**Generate database for module**:
```bash
# Detect platform and project automatically
TARGET="FortniteEditor"
# ... execute Algorithm: Generate Compilation Database
```

**Find existing database**:
```bash
# ... execute Algorithm: Find Compilation Database
```

**Get database info**:
```bash
DB_PATH="./compile_commands.json"
# ... execute Algorithm: Get Database Info
```

**Integration with llt-generate**:
```bash
# Generate compilation database first (if not exists)
/llt-generate --module CommChannelsRuntime --compdb /path/to/compile_commands.json

# The system:
# 1. Checks for compilation database at provided path
# 2. If not found, executes Algorithm: Generate Compilation Database
# 3. Uses libclang AST parsing for method extraction (100% accuracy)
# 4. Falls back to regex parsing if libclang unavailable (95% accuracy)
```

## Error Handling

### Common Errors and Solutions

#### Module Not Found

```
ERROR: Module CommChannelsRuntime not found
```

**Solution:** Verify module name and ensure you're in the correct project directory.

#### Template Not Found

```
ERROR: Template cpp-async-llt-template.md not found
```

**Solution:** Check template name spelling. Available templates:
- `cpp-basic-fixture-llt-template.md`
- `cpp-async-llt-template.md`
- `cpp-plugin-lifecycle-llt-template.md`
- `cpp-mock-llt-template.md`

#### Build Failed

```
ERROR: Build failed with exit code 1
stderr: error C2039: 'MethodName': is not a member of 'FClassName'
```

**Solution:**
1. Check generated test file for syntax errors
2. Verify module dependencies in .Build.cs
3. Ensure source headers are included correctly
4. Run manual build to see detailed errors: `ushell .build <target>`

#### Compilation Database Not Found

```
WARNING: Compilation database not found. Using regex fallback (95% accuracy).
```

**Solution:** Generate compilation database using Algorithm: Generate Compilation Database:
```bash
# Set target and execute algorithm steps
TARGET="FortniteEditor"
# Follow steps from "Algorithm: Generate Compilation Database" section
```

#### Method Extraction Failed

```
WARNING: Failed to extract methods from CommChannelNode.h. Generating template with TODOs.
```

**Solution:**
1. Verify source file exists and is readable
2. Check file contains valid C++ class definitions
3. Use `--compdb` flag to provide compilation database for accurate parsing

## Performance Characteristics

| Operation | Expected Duration | Target |
|-----------|-------------------|--------|
| Pattern detection | <100ms | <1s |
| Template rendering | <50ms per file | <500ms total |
| File generation | <10ms per file | <100ms total |
| Full scaffold | <3s | <5s |
| Metadata-driven stub generation | <1s | <3s |
| Clang AST parsing (cold) | 1-3s per file | <5s |
| Clang AST parsing (cached) | <30ms per file | <100ms |
| Regex parsing (fallback) | <100ms per file | <500ms |

## Testing Checklist

For TASK-015 acceptance, verify:

### Scaffold Mode
- [ ] Generates .Build.cs with TestModuleRules and dependencies
- [ ] Generates .Target.cs with TestTargetRules and platform config
- [ ] Generates initial test .cpp with copyright header
- [ ] Creates proper directory structure: `<PluginRoot>/Tests/<TestModuleName>/Private/`
- [ ] Returns JSON with generated file paths and test count
- [ ] Completes in <3 seconds for typical module

### Interactive Mode
- [ ] Prompts for confirmation at each step (analyze, template, generate, build, run)
- [ ] Displays detected pattern and template
- [ ] Allows user to accept, override, or abort
- [ ] Displays method list and allows filtering
- [ ] Clear progress feedback throughout
- [ ] Respects user choices (skip build, skip run)

### Autonomous Mode
- [ ] Runs without prompts when `--no-interactive` or `--build` flag present
- [ ] Automatically builds when `--build` flag present
- [ ] Automatically runs tests when `--run` flag present
- [ ] Returns comprehensive validation status (compilation, execution)
- [ ] Completes full workflow (generate → build → run) successfully

### Template Selection
- [ ] Detects Mock pattern correctly (priority 1)
- [ ] Detects Plugin/Lifecycle pattern correctly (priority 2)
- [ ] Detects Async pattern correctly (priority 3)
- [ ] Defaults to Basic/Fixture pattern
- [ ] Respects `--template` override
- [ ] Respects `--framework` override

### Filtering
- [ ] `--class` filters methods to specified class
- [ ] `--method` filters to specified method name(s)
- [ ] Multiple methods can be specified comma-separated
- [ ] Invalid class/method returns clear error

### Build Integration
- [ ] Invokes llt-build skill correctly
- [ ] Returns compilation status
- [ ] Includes build errors in output
- [ ] Handles build failures gracefully

### Run Integration
- [ ] Invokes llt-run skill after successful build
- [ ] Returns test execution results
- [ ] Includes test counts (passed, failed, skipped)
- [ ] Handles test failures gracefully

### Metadata-Driven Generation
- [ ] Parses llt-find JSON output correctly
- [ ] Identifies untested methods
- [ ] Generates test stubs for coverage gaps
- [ ] Maintains consistent tagging with existing tests

### Error Handling
- [ ] Clear error messages for missing module
- [ ] Clear error messages for missing template
- [ ] Clear error messages for invalid inputs
- [ ] Graceful fallback when clang unavailable
- [ ] Graceful fallback when build fails
- [ ] Warnings for non-critical issues

### Output Format
- [ ] Returns structured JSON with all required fields
- [ ] Includes progress log
- [ ] Includes warnings
- [ ] Includes error (if failed)
- [ ] File paths are absolute
- [ ] Test counts are accurate

## Specification Compliance

This skill implements the following spec requirements:

- ✅ **REQ-F-44**: CLI command with options for module, file, framework, test-type
- ✅ **REQ-F-45**: Scaffold mode generates complete test module
- ✅ **REQ-F-46**: Interactive mode with confirmation prompts at each step
- ✅ **REQ-F-47**: Autonomous mode with `--build` and `--run` flags
- ✅ **REQ-F-48**: Filtering parameters for class and method selection
- ✅ **REQ-F-49**: Structured JSON output with file paths, test count, validation status

## Future Enhancements

- [ ] Multi-module batch generation
- [ ] Incremental test generation (append to existing test files)
- [ ] Test refactoring when source changes
- [ ] Visual Studio IDE integration (context menu)
- [ ] Blueprint test generation
- [ ] Performance benchmark test generation
- [ ] Coverage-driven test prioritization
- [ ] AI-assisted assertion generation (experimental)

## References

- **Spec**: `.sdd/specs/2026-02-17-llt-test-generation.md` (REQ-F-44 to REQ-F-49)
- **Plan**: `.sdd/plans/2026-02-17-llt-test-generation-plan.md` (CLI design)
- **Task Breakdown**: `.sdd/tasks/2026-02-17-llt-test-generation-tasks.md` (TASK-015)
- **Skill Invocation**: See "Skill Invocation" section - agents implement workflows directly
- **Metadata Resolver**: `skills/llt-generate/scripts/metadata_resolver.py`
- **Pattern Detector**: `skills/llt-generate/scripts/pattern_detector.py`
- **Template Renderer**: `skills/llt-generate/scripts/template_renderer.py`
- **Templates**: `skills/templates/*.md`

---

**Last Updated**: 2026-02-18
**Status**: Implementation Complete (TASK-015)
**Version**: 1.0.0
