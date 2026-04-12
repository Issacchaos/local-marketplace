# Unreal Engine Plugin/Lifecycle Test Template (LowLevelTests)

**Purpose**: Template for generating Plugin/Lifecycle LowLevelTest files requiring Engine integration or complex framework initialization
**Target Language**: C++ (Unreal Engine)
**Test Framework**: Catch2 v3.4.0+ (LowLevelTests)
**Pattern**: Plugin/Lifecycle (15% of LLT modules)
**Version Support**: UE5+

## Overview

This template provides Plugin/Lifecycle test patterns for Unreal Engine LowLevelTests requiring:
- Engine module compilation (`bCompileAgainstEngine = true`)
- Mock engine defaults (`bMockEngineDefaults = true`)
- Complex fixtures with component composition
- Plugin lifecycle management (CreateFramework/DestroyFramework)
- Auto-restore utilities for console variables and config

Based on analysis of FNOnlineFrameworkTests/SaveFrameworkTests.cpp pattern used extensively for plugin integration testing in Fortnite.

## When to Use This Template

**Use Plugin/Lifecycle template when:**
- Tests require Engine module (`bCompileAgainstEngine = true`)
- Plugin lifecycle management needed (initialization/shutdown)
- Complex fixtures with component composition required
- Auto-restore utilities needed (console vars, GConfig)
- Framework initialization required (SaveFramework, online frameworks)
- Heavy Engine/CoreUObject dependencies

**Do NOT use this template if:**
- Tests are purely synchronous without Engine → Use Basic/Fixture template
- Tests need async handling without Engine → Use Async template
- Tests need mocking without Engine → Use Mock template

## Template Structure

### Complete Test File Template

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"

#include "catch2/generators/catch_generators.hpp"
#include "{{UE_HEADER_PATH}}"
#include "{{FIXTURE_HEADER_PATH}}"
{{ADDITIONAL_INCLUDES}}

using namespace UE::{{NAMESPACE}};

// ============================================================================
// {{MODULE_NAME}} Tests
// ============================================================================

TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{TEST_NAME}}", "[{{MODULE_TAG}}][{{FEATURE_TAG}}]")
{
    {{MODULE_INTERFACE}}& Interface = Get{{MODULE_INTERFACE}}();

    SECTION("{{SECTION_DESCRIPTION}}") {
        // Arrange
        {{SETUP_CODE}}

        // Act
        {{CODE_UNDER_TEST}}

        // Assert
        {{ASSERTIONS}}
    }

    {{ADDITIONAL_SECTIONS}}
}

{{ADDITIONAL_TEST_CASES}}
```

### Fixture Header Template

```cpp

#pragma once

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
{{COMPONENT_INCLUDES}}

// ============================================================================
// {{FIXTURE_CLASS_NAME}} - Plugin/Lifecycle Test Fixture
// ============================================================================

/**
 * Test fixture for {{MODULE_NAME}} with Engine integration.
 *
 * Features:
 * - Component composition for test utilities
 * - Auto-restore for console variables and config
 * - Plugin lifecycle management (Create/Destroy)
 * - Mock engine defaults
 */
class {{FIXTURE_CLASS_NAME}}
{
public:
    {{FIXTURE_CLASS_NAME}}();
    ~{{FIXTURE_CLASS_NAME}}();

    // Lifecycle management
    void Create{{FRAMEWORK_NAME}}();
    void Destroy{{FRAMEWORK_NAME}}();
    void Teardown{{FIXTURE_CLASS_NAME}}();

    // Accessor for framework instance
    UE::{{NAMESPACE}}::{{MODULE_INTERFACE}}& Get{{MODULE_INTERFACE}}() const;

    {{UTILITY_METHODS}}

protected:
    // Components (dependency injection)
    {{FIXTURE_COMPONENTS}}

    // Framework instance
    TSharedPtr<UE::{{NAMESPACE}}::{{MODULE_INTERFACE}}> {{FRAMEWORK_INSTANCE_NAME}};

    // Auto-restore utilities (prevents test pollution)
    {{AUTO_RESTORE_VARIABLES}}
};
```

### Build.cs Configuration Template

```cpp

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
                "Core",
                "CoreUObject",
                "Engine",
                {{DEPENDENCY_MODULES}}
            });

        {{ADDITIONAL_CONFIG}}
    }
}
```

### Target.cs Configuration Template

```cpp

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class {{TEST_TARGET_NAME}}Target : TestTargetRules
{
    public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
    {
        // Engine integration flags
        bCompileAgainstEngine = true;
        bTestsRequireEngine = true;
        bMockEngineDefaults = true;

        // Additional configuration
        bUsePlatformFileStub = true;
        bWithLowLevelTestsOverride = false;

        {{ADDITIONAL_ENGINE_FLAGS}}
    }
}
```

## Template Placeholders

### Module-Level Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{MODULE_NAME}}` | Module being tested | `FNOnlineFramework`, `SaveFramework` |
| `{{NAMESPACE}}` | UE namespace | `FNOnlineFramework`, `Online` |
| `{{UE_HEADER_PATH}}` | Primary header path | `SaveFramework/SaveFramework.h` |
| `{{FIXTURE_HEADER_PATH}}` | Fixture header path | `Tests/SaveFramework/SaveFrameworkTestFixture.h` |
| `{{MODULE_INTERFACE}}` | Interface/Framework class | `FSaveFramework`, `ICommerce` |
| `{{FRAMEWORK_NAME}}` | Framework name for lifecycle | `SaveFramework`, `OnlineFramework` |

### Fixture Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{FIXTURE_CLASS_NAME}}` | Fixture class name | `FSaveFrameworkTestFixture` |
| `{{FIXTURE_COMPONENTS}}` | Component declarations | `FCommonAccountTestComponent CommonAccountComponent;` |
| `{{FRAMEWORK_INSTANCE_NAME}}` | Framework instance variable | `SaveFrameworkPtr` |
| `{{AUTO_RESTORE_VARIABLES}}` | Auto-restore variable declarations | `TAutoRestoreConsoleVariable<float> MockDelay;` |
| `{{UTILITY_METHODS}}` | Helper method declarations | `void CreateSaveTargetAccount();` |

### Test Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_NAME}}` | Descriptive test name | `SaveFramework validates data size` |
| `{{MODULE_TAG}}` | Module category tag | `[FNOnlineFramework]`, `[SaveFramework]` |
| `{{FEATURE_TAG}}` | Feature category tag | `[SaveFramework]`, `[Validation]` |
| `{{SECTION_DESCRIPTION}}` | Section scenario name | `VerifyDataSize with empty string` |
| `{{SETUP_CODE}}` | Test setup (Arrange) | `FString TestValue = "";` |
| `{{CODE_UNDER_TEST}}` | Code being tested (Act) | `bool Result = Framework.Validate(Data);` |
| `{{ASSERTIONS}}` | Assertion statements (Assert) | `CHECK(Result);` |

### Build Configuration Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{ENGINE_FLAGS}}` | Engine compilation flags | `bCompileAgainstEngine = true` |
| `{{MOCK_ENGINE_DEFAULTS}}` | Mock engine configuration | `bMockEngineDefaults = true` |
| `{{DEPENDENCY_MODULES}}` | Module dependencies | `"OnlineSubsystem", "Json"` |
| `{{GAUNTLET_ARGS}}` | Test metadata arguments | `TestMetadata.GauntletArgs = "-timeout=300";` |

## Plugin/Lifecycle Patterns

### Pattern 1: Component-Based Fixture

```cpp
// Fixture with component composition
class FSaveFrameworkTestFixture
{
public:
    FSaveFrameworkTestFixture()
    {
        // Setup components
        CommonAccountComponent.Setup();
        CommonConfigComponent.Setup();

        // Create framework
        CreateSaveFramework();
    }

    ~FSaveFrameworkTestFixture()
    {
        TeardownSaveFrameworkFixture();
    }

    void CreateSaveFramework()
    {
        SaveFrameworkPtr = MakeShared<UE::FNOnlineFramework::FSaveFramework>();
        SaveFrameworkPtr->Initialize();
    }

    void DestroySaveFramework()
    {
        if (SaveFrameworkPtr)
        {
            SaveFrameworkPtr->Shutdown();
            SaveFrameworkPtr.Reset();
        }
    }

    void TeardownSaveFrameworkFixture()
    {
        DestroySaveFramework();
        CommonConfigComponent.Teardown();
        CommonAccountComponent.Teardown();
    }

    UE::FNOnlineFramework::FSaveFramework& GetSaveFramework() const
    {
        check(SaveFrameworkPtr);
        return *SaveFrameworkPtr;
    }

protected:
    // Components provide utilities
    FCommonAccountTestComponent CommonAccountComponent;
    FCommonConfigTestComponent CommonConfigComponent;

    // Framework instance
    TSharedPtr<UE::FNOnlineFramework::FSaveFramework> SaveFrameworkPtr;

    // Auto-restore utilities
    TAutoRestoreConsoleVariable<float> MockDelay{TEXT("SaveFramework.MockDelay"), 0.0f};
    TAutoRestoreGConfig<FString> ConfigInstanceName{TEXT("SaveFramework"), TEXT("InstanceName"), GGameIni};
};

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework lifecycle", "[FNOnlineFramework][SaveFramework]")
{
    ISaveFramework& SaveFramework = GetSaveFramework();

    SECTION("Framework initializes successfully") {
        // Arrange
        // (Done in fixture constructor)

        // Act
        bool bIsInitialized = SaveFramework.IsInitialized();

        // Assert
        CHECK(bIsInitialized);
    }

    SECTION("Framework shuts down cleanly") {
        // Arrange
        // (Framework already initialized)

        // Act
        DestroySaveFramework();

        // Assert
        CHECK(!SaveFrameworkPtr.IsValid());
    }
}
```

### Pattern 2: Auto-Restore Utilities

```cpp
// Prevent test pollution with auto-restore
class FPluginTestFixture
{
protected:
    // Console variables automatically restored on destruction
    TAutoRestoreConsoleVariable<float> MockDelay{
        TEXT("Plugin.MockDelay"),
        0.0f
    };

    TAutoRestoreConsoleVariable<bool> EnableFeature{
        TEXT("Plugin.EnableFeature"),
        false
    };

    TAutoRestoreConsoleVariable<FString> MockFailureMode{
        TEXT("Plugin.MockFailureMode"),
        TEXT("")
    };

    // GConfig values automatically restored on destruction
    TAutoRestoreGConfig<int32> MaxRetries{
        TEXT("Plugin"),
        TEXT("MaxRetries"),
        GGameIni
    };

    TAutoRestoreGConfig<FString> ServerUrl{
        TEXT("Plugin"),
        TEXT("ServerUrl"),
        GGameIni
    };
};

TEST_CASE_METHOD(FPluginTestFixture, "Plugin respects console variables", "[Plugin][Config]")
{
    SECTION("Mock delay affects operation timing") {
        // Arrange
        MockDelay.Set(5.0f);

        // Act
        float ActualDelay = Plugin->GetMockDelay();

        // Assert
        CHECK(ActualDelay == 5.0f);

        // MockDelay automatically restored on scope exit
    }

    SECTION("Feature flag enables functionality") {
        // Arrange
        EnableFeature.Set(true);

        // Act
        bool bIsEnabled = Plugin->IsFeatureEnabled();

        // Assert
        CHECK(bIsEnabled);

        // EnableFeature automatically restored on scope exit
    }
}
```

### Pattern 3: Framework Lifecycle Management

```cpp
// Explicit lifecycle control
class FFrameworkTestFixture
{
public:
    FFrameworkTestFixture()
    {
        CreateFramework();
    }

    ~FFrameworkTestFixture()
    {
        DestroyFramework();
    }

    void CreateFramework()
    {
        FrameworkPtr = MakeShared<FMyFramework>();

        // Configure before initialization
        FrameworkPtr->SetConfigValue(TEXT("TestMode"), TEXT("true"));

        // Initialize
        FFrameworkConfig Config;
        Config.bEnableMockServices = true;
        FrameworkPtr->Initialize(Config);
    }

    void DestroyFramework()
    {
        if (FrameworkPtr)
        {
            FrameworkPtr->Shutdown();
            FrameworkPtr.Reset();
        }
    }

    FMyFramework& GetFramework() const
    {
        check(FrameworkPtr);
        return *FrameworkPtr;
    }

protected:
    TSharedPtr<FMyFramework> FrameworkPtr;
};

TEST_CASE_METHOD(FFrameworkTestFixture, "Framework lifecycle", "[Framework]")
{
    FMyFramework& Framework = GetFramework();

    SECTION("Re-initialization not allowed") {
        // Arrange
        FFrameworkConfig Config;

        // Act & Assert
        CHECK_THROWS(Framework.Initialize(Config));
    }

    SECTION("Multiple shutdowns are safe") {
        // Arrange & Act
        Framework.Shutdown();

        // Act & Assert (should not crash)
        CHECK_NOTHROW(Framework.Shutdown());
    }
}
```

### Pattern 4: Mock Engine Integration

```cpp
// Tests requiring mock engine defaults
class FEngineIntegrationTestFixture
{
public:
    FEngineIntegrationTestFixture()
    {
        // Mock engine initialized by TestTargetRules (bMockEngineDefaults = true)

        // Setup mock services
        MockOnlineSubsystem = MakeShared<FMockOnlineSubsystem>();

        // Register mock with engine
        GEngine->GetEngineSubsystem<UOnlineEngineInterface>()->RegisterSubsystem(
            TEXT("TestOSS"),
            MockOnlineSubsystem.ToSharedRef()
        );
    }

    ~FEngineIntegrationTestFixture()
    {
        // Unregister mock
        GEngine->GetEngineSubsystem<UOnlineEngineInterface>()->UnregisterSubsystem(TEXT("TestOSS"));
    }

protected:
    TSharedPtr<FMockOnlineSubsystem> MockOnlineSubsystem;
};

TEST_CASE_METHOD(FEngineIntegrationTestFixture, "Engine integration", "[Engine][Online]")
{
    SECTION("Mock subsystem registered") {
        // Arrange
        IOnlineSubsystem* OSS = IOnlineSubsystem::Get(TEXT("TestOSS"));

        // Act & Assert
        CHECK(OSS != nullptr);
        CHECK(OSS == MockOnlineSubsystem.Get());
    }
}
```

## Component Test Utilities

### Common Component Pattern

```cpp
// Reusable test component
class FCommonAccountTestComponent
{
public:
    void Setup()
    {
        // Initialize test accounts
        TestAccountId = FAccountId::FromString(TEXT("TestAccount123"));
        TestAccountData = MakeShared<FAccountData>();
    }

    void Teardown()
    {
        // Cleanup
        TestAccountData.Reset();
    }

    FAccountId GetTestAccountId() const { return TestAccountId; }
    TSharedPtr<FAccountData> GetTestAccountData() const { return TestAccountData; }

    FAccountId CreateTestAccount(const FString& Name)
    {
        // Helper to create test accounts
        FAccountId NewId = FAccountId::Generate();
        TestAccounts.Add(NewId, Name);
        return NewId;
    }

protected:
    FAccountId TestAccountId;
    TSharedPtr<FAccountData> TestAccountData;
    TMap<FAccountId, FString> TestAccounts;
};

class FCommonConfigTestComponent
{
public:
    void Setup()
    {
        // Backup original config
        OriginalConfigValues = ReadCurrentConfig();

        // Set test config
        GConfig->SetInt(TEXT("Test"), TEXT("MaxRetries"), 3, GGameIni);
        GConfig->SetString(TEXT("Test"), TEXT("ServerUrl"), TEXT("http://test.local"), GGameIni);
    }

    void Teardown()
    {
        // Restore original config
        RestoreConfig(OriginalConfigValues);
    }

protected:
    TMap<FString, FString> OriginalConfigValues;

    TMap<FString, FString> ReadCurrentConfig() { /* Implementation */ return {}; }
    void RestoreConfig(const TMap<FString, FString>& Values) { /* Implementation */ }
};
```

## Build Configuration Examples

### Build.cs with Engine Integration

```cpp
// FNOnlineFrameworkTests.Build.cs
using UnrealBuildTool;

public class FNOnlineFrameworkTests : TestModuleRules
{
    static FNOnlineFrameworkTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "FNOnlineFramework";
        TestMetadata.TestShortName = "FNOnlineFramework";
        TestMetadata.ReportType = "UnitTest";
    }

    public FNOnlineFrameworkTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "Engine",
                "FNOnlineFramework",
                "OnlineFrameworkCommon",
                "OnlineSubsystem",
                "OnlineSubsystemNull",
                "OnlineSubsystemUtils",
                "OnlineServicesNullInternal",
                "OnlineTestsCore",
                "Json",
                "LinkEntry"
            });

        // Custom defines for test environment
        PrivateDefinitions.Add("UE_INCLUDE_COMMONCONFIG_IN_LOG=1");
        PrivateDefinitions.Add("UE_WITH_OSSNULLMOCKTESTUTILS=1");
    }
}
```

### Target.cs with Mock Engine

```cpp
// FNOnlineFrameworkTests.Target.cs
using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class FNOnlineFrameworkTestsTarget : TestTargetRules
{
    public FNOnlineFrameworkTestsTarget(TargetInfo Target) : base(Target)
    {
        // Engine integration (unusual for LLT, required for plugin tests)
        bCompileAgainstEngine = true;
        bTestsRequireEngine = true;
        bMockEngineDefaults = true;

        // File system mocking
        bUsePlatformFileStub = true;

        // LLT configuration
        bWithLowLevelTestsOverride = false;
    }
}
```

## Complete Example

### Example: SaveFramework Validation Tests

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"

#include "catch2/generators/catch_generators.hpp"
#include "SaveFramework/SaveFramework.h"
#include "Tests/SaveFramework/SaveFrameworkTestFixture.h"

using namespace UE::FNOnlineFramework;

// ============================================================================
// SaveFramework Validation Tests
// ============================================================================

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework validates data size", "[FNOnlineFramework][SaveFramework]")
{
    ISaveFramework& SaveFramework = GetSaveFramework();

    // Configure max size
    GConfig->SetInt(TEXT("SaveFramework"), TEXT("SaveDataMaxSizeKb"), 128, GGameIni);
    SaveFramework.UpdateFromConfig(false);
    int SaveDataMaxSize = SaveFramework.GetSaveDataMaxSize();

    SECTION("VerifyDataSize with empty string") {
        // Arrange
        FString TestStringValue = TEXT("");
        ISaveDataRef TestSaveData = FSaveDataString::Create(TEXT("MyResourceId"), TestStringValue);

        // Act
        bool bResult = SaveFramework.VerifyDataSize(TestSaveData);

        // Assert
        CHECK(bResult);
    }

    SECTION("VerifyDataSize with valid data") {
        // Arrange
        FString TestStringValue = TEXT("ValidData");
        ISaveDataRef TestSaveData = FSaveDataString::Create(TEXT("MyResourceId"), TestStringValue);

        // Act
        bool bResult = SaveFramework.VerifyDataSize(TestSaveData);

        // Assert
        CHECK(bResult);
    }

    SECTION("VerifyDataSize with exceeded max length") {
        // Arrange
        FString TestStringValue;
        for (int Index = 0; Index < SaveDataMaxSize + 1; Index++)
        {
            TestStringValue += TEXT("a");
        }
        ISaveDataRef TestSaveData = FSaveDataString::Create(TEXT("MyResourceId"), TestStringValue);

        // Act
        bool bResult = SaveFramework.VerifyDataSize(TestSaveData);

        // Assert
        CHECK(!bResult);
    }

    SECTION("VerifyDataSize at exact max length") {
        // Arrange
        FString TestStringValue;
        for (int Index = 0; Index < SaveDataMaxSize; Index++)
        {
            TestStringValue += TEXT("a");
        }
        ISaveDataRef TestSaveData = FSaveDataString::Create(TEXT("MyResourceId"), TestStringValue);

        // Act
        bool bResult = SaveFramework.VerifyDataSize(TestSaveData);

        // Assert
        CHECK(bResult);
    }
}

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework handles config updates", "[FNOnlineFramework][SaveFramework]")
{
    ISaveFramework& SaveFramework = GetSaveFramework();

    SECTION("UpdateFromConfig applies new max size") {
        // Arrange
        int OriginalMaxSize = SaveFramework.GetSaveDataMaxSize();
        GConfig->SetInt(TEXT("SaveFramework"), TEXT("SaveDataMaxSizeKb"), 256, GGameIni);

        // Act
        SaveFramework.UpdateFromConfig(false);
        int NewMaxSize = SaveFramework.GetSaveDataMaxSize();

        // Assert
        CHECK(NewMaxSize != OriginalMaxSize);
        CHECK(NewMaxSize == 256 * 1024); // KB to bytes
    }

    SECTION("UpdateFromConfig with invalid config falls back to default") {
        // Arrange
        GConfig->SetInt(TEXT("SaveFramework"), TEXT("SaveDataMaxSizeKb"), -1, GGameIni);

        // Act
        SaveFramework.UpdateFromConfig(false);
        int MaxSize = SaveFramework.GetSaveDataMaxSize();

        // Assert
        CHECK(MaxSize > 0); // Should use default, not negative value
    }
}
```

### Example: Fixture Implementation

```cpp
// SaveFrameworkTestFixture.h
#pragma once

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

class FSaveFrameworkTestFixture
{
public:
    FSaveFrameworkTestFixture();
    ~FSaveFrameworkTestFixture();

    void TeardownSaveFrameworkFixture();
    void CreateSaveFramework();
    void DestroySaveFramework();

    UE::FNOnlineFramework::FSaveFramework& GetSaveFramework() const;

    // Utility methods
    FAccountId CreateSaveTargetAccount();

protected:
    // Components
    FCommonAccountTestComponent CommonAccountComponent;
    FCommonConfigTestComponent CommonConfigComponent;

    // Framework instance
    TSharedPtr<UE::FNOnlineFramework::FSaveFramework> SaveFrameworkPtr;

    // Auto-restore utilities
    TAutoRestoreConsoleVariable<float> MockDelay{TEXT("SaveFramework.MockDelay"), 0.0f};
    TAutoRestoreConsoleVariable<FString> MockOpenFailure{TEXT("SaveFramework.MockOpenFailure"), TEXT("")};
    TAutoRestoreGConfig<FString> ConfigInstanceName{TEXT("SaveFramework"), TEXT("InstanceName"), GGameIni};
};

// SaveFrameworkTestFixture.cpp
FSaveFrameworkTestFixture::FSaveFrameworkTestFixture()
{
    CommonAccountComponent.Setup();
    CommonConfigComponent.Setup();
    CreateSaveFramework();
}

FSaveFrameworkTestFixture::~FSaveFrameworkTestFixture()
{
    TeardownSaveFrameworkFixture();
}

void FSaveFrameworkTestFixture::CreateSaveFramework()
{
    SaveFrameworkPtr = MakeShared<UE::FNOnlineFramework::FSaveFramework>();
    SaveFrameworkPtr->Initialize();
}

void FSaveFrameworkTestFixture::DestroySaveFramework()
{
    if (SaveFrameworkPtr)
    {
        SaveFrameworkPtr->Shutdown();
        SaveFrameworkPtr.Reset();
    }
}

void FSaveFrameworkTestFixture::TeardownSaveFrameworkFixture()
{
    DestroySaveFramework();
    CommonConfigComponent.Teardown();
    CommonAccountComponent.Teardown();
}

UE::FNOnlineFramework::FSaveFramework& FSaveFrameworkTestFixture::GetSaveFramework() const
{
    check(SaveFrameworkPtr);
    return *SaveFrameworkPtr;
}

FAccountId FSaveFrameworkTestFixture::CreateSaveTargetAccount()
{
    return CommonAccountComponent.CreateTestAccount(TEXT("SaveTarget"));
}
```

## Best Practices

1. **Component Composition**: Use test components for reusable utilities
2. **Auto-Restore**: Always use TAutoRestoreConsoleVariable and TAutoRestoreGConfig
3. **Lifecycle Management**: Explicit Create/Destroy methods for clarity
4. **Check Macros**: Use `check()` for internal fixture invariants
5. **Config Updates**: Update framework from config before tests
6. **Mock Services**: Register/unregister mocks in fixture constructor/destructor
7. **Nested Sections**: Use for related test scenarios within same setup
8. **Descriptive Tags**: Use both module and feature tags for filtering
9. **Test Isolation**: Rely on auto-restore to prevent test pollution
10. **Fixture Testing**: Test fixture lifecycle separately from framework

## Template Selection Decision Tree

```
Does your test require Engine module?
├─ YES → Does it need plugin lifecycle?
│   ├─ YES → Use Plugin/Lifecycle template
│   └─ NO → Check if Basic/Fixture is sufficient
└─ NO → Use Basic/Fixture, Async, or Mock template

Does your test need complex fixtures with components?
├─ YES → Use Plugin/Lifecycle template
└─ NO → Use Basic/Fixture template

Does your test need auto-restore utilities?
├─ YES → Use Plugin/Lifecycle template
└─ NO → Use Basic/Fixture template

Does your test need mock engine defaults?
├─ YES → Plugin/Lifecycle template (bMockEngineDefaults = true)
└─ NO → Check other patterns
```

## Common Issues & Solutions

### Issue 1: Engine Not Available
**Symptom**: Link errors for Engine symbols
**Solution**: Verify `bCompileAgainstEngine = true` in Target.cs

### Issue 2: Mock Engine Fails
**Symptom**: GEngine is null
**Solution**: Verify `bMockEngineDefaults = true` in Target.cs

### Issue 3: Config Not Restored
**Symptom**: Tests affect each other
**Solution**: Use TAutoRestoreGConfig for all config changes

### Issue 4: Console Vars Not Restored
**Symptom**: Tests leave console vars modified
**Solution**: Use TAutoRestoreConsoleVariable for all cvar changes

### Issue 5: Framework Not Shutdown
**Symptom**: Resource leaks or crashes on exit
**Solution**: Call Destroy in fixture destructor

## Related Templates

- **Basic/Fixture Template**: `skills/templates/cpp-basic-fixture-llt-template.md` (simpler tests without Engine)
- **Async Template**: `skills/templates/cpp-async-llt-template.md` (async without Engine)
- **Mock Template**: `skills/templates/cpp-mock-llt-template.md` (mocking without Engine)
- **Build.cs Template**: `skills/templates/ue-test-build-cs-template.md`
- **Target.cs Template**: `skills/templates/ue-test-target-cs-template.md`

## Reference Files

Based on analysis of Fortnite LowLevelTests:
- **Primary Pattern**: `/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp`
- **Fixture Pattern**: `/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTestFixture.h`
- **Build Configuration**: `/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/FNOnlineFrameworkTests.Build.cs`
- **Target Configuration**: `/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/FNOnlineFrameworkTests.Target.cs`

---

**Template Version**: 1.0.0
**Last Updated**: 2026-02-18
**Pattern**: Plugin/Lifecycle (15% of LLT modules)
**Status**: Ready for Implementation
**Evidence Base**: 15+ LLT module analysis, SaveFramework pattern validation
