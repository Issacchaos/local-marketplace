# Unreal Engine Test Module Build Configuration Template (.Build.cs)

**Purpose**: Template for generating .Build.cs files for LowLevelTest modules
**Target Language**: C# (UnrealBuildTool)
**Framework**: TestModuleRules (UE5+ LowLevelTests)
**Version**: 1.0.0

## Overview

This template generates `.Build.cs` files for Unreal Engine test modules using `TestModuleRules`. It handles:
- Static metadata initialization (TestName, TestShortName, ReportType, GauntletArgs)
- Private dependency module configuration
- TestModuleRules compilation flags based on dependencies
- Support for all 4 test patterns (Basic/Fixture, Async, Plugin/Lifecycle, Mock)

The `.Build.cs` file is the primary build configuration for test modules and must correctly set compilation flags based on the module's dependencies to ensure proper initialization of the Catch2 framework and UE subsystems.

## When to Use This Template

**Always use this template when:**
- Creating a new test module for LowLevelTests
- The test module is located in `<PluginRoot>/Tests/<TestModuleName>/`
- Using Catch2 framework with UE TestModuleRules

## Template Structure

### Complete .Build.cs Template

```csharp

using UnrealBuildTool;

public class {{TEST_MODULE_NAME}} : TestModuleRules
{
	static {{TEST_MODULE_NAME}}()
	{
		TestMetadata = new Metadata();
		TestMetadata.TestName = "{{TEST_NAME}}";
		TestMetadata.TestShortName = "{{TEST_SHORT_NAME}}";
		{{ADDITIONAL_METADATA}}
	}

	public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
	{
		PrivateDependencyModuleNames.AddRange(
			new string[] {
				{{DEPENDENCY_MODULES}}
			});
	}
}
```

## Template Placeholders

### Module Metadata Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_MODULE_NAME}}` | Test module class name | `CommChannelsTests`, `FNOnlineFrameworkTests` |
| `{{TEST_NAME}}` | Full test name for reporting | `CommChannels Tests`, `SaveFramework Tests` |
| `{{TEST_SHORT_NAME}}` | Short test name for CLI | `CommChannels`, `SaveFramework` |
| `{{ADDITIONAL_METADATA}}` | Optional metadata fields | `TestMetadata.ReportType = "xml";` |

### Dependency Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{DEPENDENCY_MODULES}}` | Private dependencies (C# array) | `"Core",`<br>`"CoreUObject",`<br>`"CommChannelsRuntime"` |

### Configuration Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{ENGINE_FLAGS}}` | TestModuleRules compilation flags | `bCompileAgainstEngine = true;` |
| `{{ADDITIONAL_CONFIG}}` | Extra configuration options | `bUsePlatformFileStub = true;` |
| `{{GAUNTLET_ARGS}}` | Gauntlet test arguments | Custom test execution args |

## CRITICAL: Dependency-Based Flag Logic

**The Catch2 framework in UE requires specific TestModuleRules flags based on module dependencies.** Missing flags cause initialization failures, linker errors, or runtime crashes.

### Decision Tree: Dependency → Required Flags

Use this decision tree to determine which flags to enable:

```
Does test module depend on:

1. Engine module?
   YES → bCompileAgainstEngine = true
   NO  → Continue

2. CoreUObject module?
   YES → bCompileAgainstCoreUObject = true
   NO  → Continue

3. Is this a Plugin/Lifecycle test?
   YES → bCompileAgainstEngine = true
         bMockEngineDefaults = true
   NO  → Continue

4. Does test use UObject-based mocks?
   YES → bCompileAgainstCoreUObject = true
   NO  → No special flags needed
```

### Flag Reference Table

| Flag | When Required | Consequence if Missing |
|------|--------------|------------------------|
| `bCompileAgainstEngine` | Depends on Engine module, Plugin lifecycle | Linker errors for Engine symbols, subsystem init failures |
| `bCompileAgainstCoreUObject` | Depends on CoreUObject, Uses UObject types | Linker errors for UObject symbols, RTTI failures |
| `bMockEngineDefaults` | Plugin/Lifecycle tests, Isolated engine testing | Real engine initialization instead of mocks, test pollution |

### Pattern-Specific Flag Requirements

#### 1. Basic/Fixture Pattern
**Dependencies**: Usually just Core
**Required Flags**: None (minimal)

```csharp
public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
{
	PrivateDependencyModuleNames.AddRange(
		new string[] {
			"Core",
			"{{MODULE_UNDER_TEST}}"
		});

	// No special flags needed for Core-only tests
}
```

**Example**: FoundationTests (LinkedListBuilder tests)

#### 2. Async Pattern
**Dependencies**: Core + optional Engine (for async subsystems)
**Required Flags**: `bCompileAgainstEngine = true` if using Engine async features

```csharp
public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
{
	PrivateDependencyModuleNames.AddRange(
		new string[] {
			"Core",
			"CoreUObject",
			"Engine",  // For async subsystems
			"HTTP",    // Example async module
			"WebSockets"
		});

	// Required when depending on Engine
	bCompileAgainstEngine = true;
	bCompileAgainstCoreUObject = true;
}
```

**Example**: WebTests (TestWebSockets.cpp)

#### 3. Plugin/Lifecycle Pattern
**Dependencies**: Core + CoreUObject + Engine (always)
**Required Flags**: `bCompileAgainstEngine = true`, `bMockEngineDefaults = true` (both always required)

```csharp
public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
{
	PrivateDependencyModuleNames.AddRange(
		new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"{{PLUGIN_MODULE}}"
		});

	// CRITICAL: Both flags required for Plugin/Lifecycle pattern
	bCompileAgainstEngine = true;
	bCompileAgainstCoreUObject = true;
	bMockEngineDefaults = true;  // Prevents real engine initialization
}
```

**Example**: FNOnlineFrameworkTests (SaveFramework tests)

**Warning**: Missing `bMockEngineDefaults = true` causes real engine initialization, leading to:
- Test pollution (global state persists)
- Initialization failures in CI environments
- Unpredictable test results

#### 4. Mock Pattern
**Dependencies**: Core + optional CoreUObject (if mocking UObjects)
**Required Flags**: `bCompileAgainstCoreUObject = true` if mocking UObject-based interfaces

```csharp
public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
{
	PrivateDependencyModuleNames.AddRange(
		new string[] {
			"Core",
			"CoreUObject",  // If mocking UObject-based interfaces
			"{{MODULE_WITH_INTERFACES}}"
		});

	// Required if mocking UObject types
	bCompileAgainstCoreUObject = true;
}
```

**Example**: FNOnlineFrameworkTests (MockTestUtils.h)

## Complete Examples

### Example 1: Basic/Fixture Test (Minimal Flags)

```csharp

using UnrealBuildTool;

public class CommChannelsTests : TestModuleRules
{
	static CommChannelsTests()
	{
		TestMetadata = new Metadata();
		TestMetadata.TestName = "CommChannels Tests";
		TestMetadata.TestShortName = "CommChannels";
	}

	public CommChannelsTests(ReadOnlyTargetRules Target) : base(Target)
	{
		PrivateDependencyModuleNames.AddRange(
			new string[] {
				"Core",
				"CommChannelsRuntime"
			});

		// No special flags - Core-only test
	}
}
```

### Example 2: Async Test (Engine Flags)

```csharp

using UnrealBuildTool;

public class WebTests : TestModuleRules
{
	static WebTests()
	{
		TestMetadata = new Metadata();
		TestMetadata.TestName = "Web Tests";
		TestMetadata.TestShortName = "Web";
	}

	public WebTests(ReadOnlyTargetRules Target) : base(Target)
	{
		PrivateDependencyModuleNames.AddRange(
			new string[] {
				"Core",
				"CoreUObject",
				"Engine",
				"HTTP",
				"WebSockets"
			});

		// Required for Engine-based async operations
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
	}
}
```

### Example 3: Plugin/Lifecycle Test (Full Flags)

```csharp

using UnrealBuildTool;

public class FNOnlineFrameworkTests : TestModuleRules
{
	static FNOnlineFrameworkTests()
	{
		TestMetadata = new Metadata();
		TestMetadata.TestName = "FNOnlineFramework Tests";
		TestMetadata.TestShortName = "FNOnlineFramework";
		TestMetadata.ReportType = "xml";
	}

	public FNOnlineFrameworkTests(ReadOnlyTargetRules Target) : base(Target)
	{
		PrivateDependencyModuleNames.AddRange(
			new string[] {
				"Core",
				"CoreUObject",
				"Engine",
				"FNOnlineFramework",
				"SaveFramework"
			});

		// CRITICAL: All three flags required for plugin testing
		bCompileAgainstEngine = true;
		bCompileAgainstCoreUObject = true;
		bMockEngineDefaults = true;  // Isolated engine testing
	}
}
```

### Example 4: Mock Test (CoreUObject Flags)

```csharp

using UnrealBuildTool;

public class OnlineServicesMockTests : TestModuleRules
{
	static OnlineServicesMockTests()
	{
		TestMetadata = new Metadata();
		TestMetadata.TestName = "Online Services Mock Tests";
		TestMetadata.TestShortName = "OnlineServicesMock";
	}

	public OnlineServicesMockTests(ReadOnlyTargetRules Target) : base(Target)
	{
		PrivateDependencyModuleNames.AddRange(
			new string[] {
				"Core",
				"CoreUObject",
				"OnlineServicesInterface"
			});

		// Required for UObject-based mock interfaces
		bCompileAgainstCoreUObject = true;
	}
}
```

## Placeholder Substitution Examples

### Basic Substitution

```csharp
// Template
public class {{TEST_MODULE_NAME}} : TestModuleRules

// Substituted
public class CommChannelsTests : TestModuleRules
```

### Metadata Substitution

```csharp
// Template
TestMetadata.TestName = "{{TEST_NAME}}";
TestMetadata.TestShortName = "{{TEST_SHORT_NAME}}";

// Substituted
TestMetadata.TestName = "CommChannels Tests";
TestMetadata.TestShortName = "CommChannels";
```

### Dependency Array Substitution

```csharp
// Template
PrivateDependencyModuleNames.AddRange(
	new string[] {
		{{DEPENDENCY_MODULES}}
	});

// Substituted (Basic)
PrivateDependencyModuleNames.AddRange(
	new string[] {
		"Core",
		"CommChannelsRuntime"
	});

// Substituted (Plugin/Lifecycle)
PrivateDependencyModuleNames.AddRange(
	new string[] {
		"Core",
		"CoreUObject",
		"Engine",
		"FNOnlineFramework"
	});
```

### Flag Substitution

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
```

## Common Mistakes and Solutions

### Mistake 1: Missing bCompileAgainstEngine for Engine Dependencies
**Symptom**: Linker errors for Engine symbols (GEngine, UWorld, etc.)
**Solution**: Add `bCompileAgainstEngine = true;` when depending on Engine module

### Mistake 2: Missing bMockEngineDefaults for Plugin Tests
**Symptom**: Real engine initialization, test pollution, CI failures
**Solution**: Always add `bMockEngineDefaults = true;` for Plugin/Lifecycle pattern

### Mistake 3: Missing bCompileAgainstCoreUObject for UObject Types
**Symptom**: Linker errors for UObject symbols, RTTI failures
**Solution**: Add `bCompileAgainstCoreUObject = true;` when using UObject types

### Mistake 4: Incorrect Dependency Array Formatting
**Symptom**: C# syntax errors, build failures
**Solution**: Use correct C# string array syntax with comma separators

```csharp
// WRONG
PrivateDependencyModuleNames.AddRange(
	new string[] {
		"Core"
		"CoreUObject"  // Missing comma
	});

// CORRECT
PrivateDependencyModuleNames.AddRange(
	new string[] {
		"Core",
		"CoreUObject"
	});
```

## Additional Configuration Options

### Optional Metadata Fields

```csharp
static {{TEST_MODULE_NAME}}()
{
	TestMetadata = new Metadata();
	TestMetadata.TestName = "{{TEST_NAME}}";
	TestMetadata.TestShortName = "{{TEST_SHORT_NAME}}";
	TestMetadata.ReportType = "xml";  // Optional: Output format
	TestMetadata.GauntletArgs = "--timeout=300";  // Optional: Gauntlet args
}
```

### Optional Build Configuration

```csharp
public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
{
	// Dependencies...

	// Flags...

	// Optional configuration
	bUsePlatformFileStub = true;  // Stub file system for isolated testing
	bWithLowLevelTestsOverride = false;  // Override default LLT behavior
}
```

## Best Practices

1. **Always determine flags based on dependencies**: Use the decision tree to select correct flags
2. **Document why flags are set**: Add comments explaining dependency-flag relationships
3. **Keep dependencies minimal**: Only add modules actually used by tests
4. **Use consistent naming**: `<ModuleName>Tests` convention
5. **Include Epic copyright**: First line of every .Build.cs file
6. **Test compilation**: Verify generated .Build.cs compiles before committing
7. **Match pattern requirements**: Each test pattern has specific flag requirements

## Validation Checklist

Before finalizing a .Build.cs file:
- [ ] TestModuleRules inheritance present
- [ ] Static metadata initialization present (TestName, TestShortName)
- [ ] PrivateDependencyModuleNames includes Core at minimum
- [ ] Dependency array uses correct C# string array syntax (commas)
- [ ] Flags match dependency requirements (use decision tree)
- [ ] Plugin/Lifecycle tests include `bMockEngineDefaults = true`
- [ ] Engine dependencies include `bCompileAgainstEngine = true`
- [ ] CoreUObject/UObject usage includes `bCompileAgainstCoreUObject = true`

## Related Templates

- **ue-test-target-cs-template.md**: Target configuration (.Target.cs)
- **cpp-basic-fixture-llt-template.md**: Basic/Fixture test code
- **cpp-async-llt-template.md**: Async test code
- **cpp-plugin-lifecycle-llt-template.md**: Plugin/Lifecycle test code
- **cpp-mock-llt-template.md**: Mock test code

---

**Template Version**: 1.0.0
**Status**: Ready for Implementation
**Maps to Spec**: REQ-F-6, REQ-F-11, REQ-F-24, REQ-F-28, REQ-F-29
