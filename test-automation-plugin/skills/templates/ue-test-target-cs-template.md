# Unreal Engine Test Target Configuration Template (.Target.cs)

**Purpose**: Template for generating .Target.cs files for LowLevelTest targets
**Target Language**: C# (UnrealBuildTool)
**Framework**: TestTargetRules (UE5+ LowLevelTests)
**Version**: 1.0.0

## Overview

This template generates `.Target.cs` files for Unreal Engine test targets using `TestTargetRules`. It handles:
- TestTargetRules inheritance with [SupportedPlatforms] attribute
- Platform configuration (Win64, Mac, Linux)
- Engine compilation flags matching Build.cs decisions
- Mock engine defaults for isolated testing
- Support for all 4 test patterns (Basic/Fixture, Async, Plugin/Lifecycle, Mock)

The `.Target.cs` file defines the build target and must have compilation flags that match the corresponding `.Build.cs` file to ensure consistent build behavior.

## When to Use This Template

**Always use this template when:**
- Creating a new test module for LowLevelTests
- The test module needs a corresponding build target
- Building standalone test executables

## Template Structure

### Complete .Target.cs Template

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class {{TEST_TARGET_NAME}}Target : TestTargetRules
{
	public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
	{
		{{ENGINE_FLAGS}}
	}
}
```

## Template Placeholders

### Target Metadata Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_TARGET_NAME}}` | Test target name | `CommChannelsTests`, `FNOnlineFrameworkTests` |

### Configuration Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{ENGINE_FLAGS}}` | Engine compilation flags | `bCompileAgainstEngine = true;` |
| `{{ADDITIONAL_CONFIG}}` | Optional configuration | `bUsePlatformFileStub = true;` |

## CRITICAL: Flag Consistency with Build.cs

**The .Target.cs flags MUST match the .Build.cs flags to ensure consistent build behavior.** Mismatched flags cause linker errors or initialization failures.

### Flag Matching Rules

| .Build.cs Flag | .Target.cs Flag | Must Match? |
|----------------|-----------------|-------------|
| `bCompileAgainstEngine` | `bCompileAgainstEngine` | YES |
| `bCompileAgainstCoreUObject` | `bCompileAgainstCoreUObject` | YES |
| `bMockEngineDefaults` | `bMockEngineDefaults` | YES |

**Rule**: Copy engine-related flags from `.Build.cs` to `.Target.cs` exactly.

## Pattern-Specific Target Configurations

### 1. Basic/Fixture Pattern Target
**Engine Flags**: None (minimal configuration)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class CommChannelsTestsTarget : TestTargetRules
{
	public CommChannelsTestsTarget(TargetInfo Target) : base(Target)
	{
		// No special flags needed for Core-only tests
	}
}
```

**Use Case**: Simple unit tests with Core module only
**Example**: FoundationTests (LinkedListBuilder tests)

### 2. Async Pattern Target
**Engine Flags**: `bCompileAgainstEngine = true`, `bCompileAgainstCoreUObject = true`

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class WebTestsTarget : TestTargetRules
{
	public WebTestsTarget(TargetInfo Target) : base(Target)
	{
		// Required for Engine-based async operations
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
	}
}
```

**Use Case**: Async tests with Engine subsystem dependencies
**Example**: WebTests (TestWebSockets.cpp)

### 3. Plugin/Lifecycle Pattern Target
**Engine Flags**: `bCompileAgainstEngine = true`, `bMockEngineDefaults = true`, `bTestsRequireEngine = true`

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class FNOnlineFrameworkTestsTarget : TestTargetRules
{
	public FNOnlineFrameworkTestsTarget(TargetInfo Target) : base(Target)
	{
		// CRITICAL: All flags required for plugin testing
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
		bMockEngineDefaults = true;  // Isolated engine testing
		bTestsRequireEngine = true;  // Engine initialization required

		// Optional: Stub file system for isolation
		bUsePlatformFileStub = true;
		bWithLowLevelTestsOverride = false;
	}
}
```

**Use Case**: Plugin integration tests with engine lifecycle
**Example**: FNOnlineFrameworkTests (SaveFramework tests)

**Warning**: `bMockEngineDefaults = true` is CRITICAL for Plugin/Lifecycle tests to prevent real engine initialization.

### 4. Mock Pattern Target
**Engine Flags**: `bCompileAgainstCoreUObject = true` (if mocking UObjects)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class OnlineServicesMockTestsTarget : TestTargetRules
{
	public OnlineServicesMockTestsTarget(TargetInfo Target) : base(Target)
	{
		// Required for UObject-based mock interfaces
		bCompileAgainstCoreUObject = true;
	}
}
```

**Use Case**: Dependency injection tests with mock interfaces
**Example**: FNOnlineFrameworkTests (MockTestUtils.h)

## Platform Configuration

### Supported Platforms Attribute

The `[SupportedPlatforms]` attribute controls which platforms can build this target.

```csharp
// All platforms (most common)
[SupportedPlatforms(UnrealPlatformClass.All)]

// Desktop only (Windows, Mac, Linux)
[SupportedPlatforms(UnrealPlatformClass.Desktop)]

// Specific platforms
[SupportedPlatforms("Win64", "Mac", "Linux")]
```

**Default**: Use `UnrealPlatformClass.All` for maximum compatibility.

### Platform-Specific Configuration

```csharp
public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
{
	// Common flags...

	// Platform-specific configuration
	if (Target.Platform == UnrealTargetPlatform.Win64)
	{
		// Windows-specific settings
	}
	else if (Target.Platform == UnrealTargetPlatform.Mac)
	{
		// macOS-specific settings
	}
	else if (Target.Platform == UnrealTargetPlatform.Linux)
	{
		// Linux-specific settings
	}
}
```

## Complete Examples

### Example 1: Basic/Fixture Target (Minimal)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class CommChannelsTestsTarget : TestTargetRules
{
	public CommChannelsTestsTarget(TargetInfo Target) : base(Target)
	{
		// Minimal configuration for Core-only tests
	}
}
```

### Example 2: Async Target (Engine Flags)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class WebTestsTarget : TestTargetRules
{
	public WebTestsTarget(TargetInfo Target) : base(Target)
	{
		// Matches WebTests.Build.cs flags
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
	}
}
```

### Example 3: Plugin/Lifecycle Target (Full Configuration)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class FNOnlineFrameworkTestsTarget : TestTargetRules
{
	public FNOnlineFrameworkTestsTarget(TargetInfo Target) : base(Target)
	{
		// Engine integration flags (matches FNOnlineFrameworkTests.Build.cs)
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
		bMockEngineDefaults = true;
		bTestsRequireEngine = true;

		// Isolation configuration
		bUsePlatformFileStub = true;
		bWithLowLevelTestsOverride = false;
	}
}
```

### Example 4: Mock Target (CoreUObject Flags)

```csharp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class OnlineServicesMockTestsTarget : TestTargetRules
{
	public OnlineServicesMockTestsTarget(TargetInfo Target) : base(Target)
	{
		// Matches OnlineServicesMockTests.Build.cs flags
		bCompileAgainstCoreUObject = true;
	}
}
```

## Placeholder Substitution Examples

### Target Name Substitution

```csharp
// Template
public class {{TEST_TARGET_NAME}}Target : TestTargetRules

// Substituted
public class CommChannelsTestsTarget : TestTargetRules
```

### Engine Flags Substitution

```csharp
// Template
{{ENGINE_FLAGS}}

// Substituted (Basic - empty)
// (no flags)

// Substituted (Async)
bCompileAgainstEngine = true;
bCompileAgainstCoreUObject = true;

// Substituted (Plugin/Lifecycle)
bCompileAgainstEngine = true;
bCompileAgainstCoreUObject = true;
bMockEngineDefaults = true;
bTestsRequireEngine = true;
```

### Additional Config Substitution

```csharp
// Template
{{ADDITIONAL_CONFIG}}

// Substituted (with platform stub)
bUsePlatformFileStub = true;
bWithLowLevelTestsOverride = false;
```

## Common Configuration Options

### Engine Initialization Flags

| Flag | Purpose | When to Use |
|------|---------|-------------|
| `bCompileAgainstEngine` | Link against Engine module | Tests use Engine subsystems |
| `bCompileAgainstCoreUObject` | Link against CoreUObject | Tests use UObject types |
| `bMockEngineDefaults` | Use mock engine instead of real | Plugin/Lifecycle tests (CRITICAL) |
| `bTestsRequireEngine` | Engine init required at startup | Plugin/Lifecycle tests |

### Isolation Flags

| Flag | Purpose | When to Use |
|------|---------|-------------|
| `bUsePlatformFileStub` | Stub file system API | Isolated file system testing |
| `bWithLowLevelTestsOverride` | Override default LLT behavior | Custom test framework integration |

## Flag Decision Tree (Matching .Build.cs)

Use this decision tree to determine Target.cs flags based on Build.cs:

```
Check .Build.cs flags:

1. Does .Build.cs have bCompileAgainstEngine = true?
   YES → Add to .Target.cs
   NO  → Continue

2. Does .Build.cs have bCompileAgainstCoreUObject = true?
   YES → Add to .Target.cs
   NO  → Continue

3. Does .Build.cs have bMockEngineDefaults = true?
   YES → Add to .Target.cs
        Also add bTestsRequireEngine = true
   NO  → Continue

4. Is this a Plugin/Lifecycle pattern?
   YES → Add bUsePlatformFileStub = true (optional)
         Add bWithLowLevelTestsOverride = false (optional)
   NO  → Done
```

## Common Mistakes and Solutions

### Mistake 1: Missing Flags from .Build.cs
**Symptom**: Linker errors, undefined symbols, initialization failures
**Solution**: Copy all engine flags from .Build.cs to .Target.cs

### Mistake 2: Missing bTestsRequireEngine for Plugin Tests
**Symptom**: Engine not initialized, plugin init failures
**Solution**: Add `bTestsRequireEngine = true;` when using `bMockEngineDefaults`

### Mistake 3: Incorrect SupportedPlatforms Attribute
**Symptom**: Build failures on specific platforms
**Solution**: Use `UnrealPlatformClass.All` for cross-platform tests

### Mistake 4: Mismatched Flags Between .Build.cs and .Target.cs
**Symptom**: Linker errors, inconsistent build behavior
**Solution**: Always keep flags synchronized between .Build.cs and .Target.cs

## Advanced Configuration

### Custom Build Configuration

```csharp
public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
{
	// Standard flags...

	// Custom optimization level
	OptimizationLevel = OptimizationMode.Speed;

	// Enable additional warnings
	bEnableUndefinedIdentifierWarnings = true;

	// Custom output name
	LaunchModuleName = "{{TEST_TARGET_NAME}}";
}
```

### Conditional Compilation

```csharp
public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
{
	// Standard flags...

	// Conditional configuration based on build type
	if (Target.Configuration == UnrealTargetConfiguration.Debug)
	{
		bDebugBuildsActuallyUseDebugCRT = true;
	}

	// Platform-specific flags
	if (Target.Platform == UnrealTargetPlatform.Win64)
	{
		WindowsPlatform.Compiler = WindowsCompiler.Clang;
	}
}
```

## Best Practices

1. **Always match .Build.cs flags**: Use the decision tree to ensure consistency
2. **Use UnrealPlatformClass.All by default**: Maximum platform compatibility
3. **Add comments for flag choices**: Document why flags are set
4. **Keep configuration minimal**: Only add flags actually needed
5. **Test on all target platforms**: Verify builds succeed on Win64, Mac, Linux
6. **Include Epic copyright**: First line of every .Target.cs file
7. **Use consistent naming**: `<ModuleName>TestsTarget` convention

## Validation Checklist

Before finalizing a .Target.cs file:
- [ ] TestTargetRules inheritance present
- [ ] [SupportedPlatforms] attribute present
- [ ] Engine flags match corresponding .Build.cs file
- [ ] Plugin/Lifecycle tests include `bMockEngineDefaults = true`
- [ ] Plugin/Lifecycle tests include `bTestsRequireEngine = true`
- [ ] Engine dependencies include `bCompileAgainstEngine = true`
- [ ] CoreUObject usage includes `bCompileAgainstCoreUObject = true`
- [ ] Target name ends with "Target" (e.g., `CommChannelsTestsTarget`)

## Related Templates

- **ue-test-build-cs-template.md**: Module configuration (.Build.cs)
- **cpp-basic-fixture-llt-template.md**: Basic/Fixture test code
- **cpp-async-llt-template.md**: Async test code
- **cpp-plugin-lifecycle-llt-template.md**: Plugin/Lifecycle test code
- **cpp-mock-llt-template.md**: Mock test code

---

**Template Version**: 1.0.0
**Status**: Ready for Implementation
**Maps to Spec**: REQ-F-6, REQ-F-11, REQ-F-25, REQ-F-29
