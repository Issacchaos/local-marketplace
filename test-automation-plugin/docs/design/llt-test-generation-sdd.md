# LowLevelTests Test Generation - Software Design Document

**Version:** 1.0
**Date:** 2026-02-17
**Author:** Claude Code
**Status:** Draft
**Complements:** llt-skills-sdd.md (test discovery, building, running)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Background & Context](#background--context)
3. [Template Architecture](#template-architecture)
4. [Test File Templates](#test-file-templates)
5. [Module Scaffolding](#module-scaffolding)
6. [Integration with /test-generate](#integration-with-test-generate)
7. [Code Examples](#code-examples)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Appendices](#appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This document specifies the design for **LowLevelTest (LLT) test code generation** capabilities in the dante plugin. It enables scaffolding of test files, module setup files (.Build.cs, .Target.cs), and integration with the existing `/test-generate` workflow.

### 1.2 Goals

- **Template-based scaffolding**: Generate Catch2 test files from templates with real Fortnite codebase patterns
- **Module setup automation**: Generate .Build.cs (TestModuleRules) and .Target.cs (TestTargetRules) files
- **Builder pattern support**: Templates for Online Tests async pipeline patterns
- **Metadata-driven generation**: Use llt-find output to identify untested code and generate test stubs
- **Framework detection**: Auto-detect test framework patterns (Catch2, ONLINE_TEST_CASE, RESONANCE_TEST_CASE)

### 1.3 Scope

**In Scope:**
- Catch2 basic test templates (TEST_CASE, SECTION, REQUIRE/CHECK)
- Catch2 fixture templates (TEST_CASE_METHOD)
- Online Tests builder pattern templates (GetPipeline, RunToCompletion)
- Module scaffolding (.Build.cs, .Target.cs generation)
- Integration with test-engineering:templates skill architecture
- Implicit test templates (no .Build.cs/.Target.cs)

**Out of Scope:**
- Automated test logic generation (AI-generated test assertions)
- Test data generation (mock objects, test fixtures)
- Legacy automation framework tests (IMPLEMENT_SIMPLE_AUTOMATION_TEST)
- Blueprint test generation

---

## 2. Background & Context

### 2.1 LowLevelTest Framework Overview

LowLevelTests are lightweight C++ unit tests built on **Catch2 v3.4.0+**. Key characteristics:

- **Fast iteration**: Minimal dependencies, no PCH, no Unity builds
- **Multiple test patterns**:
  - Standard Catch2 (TEST_CASE, SECTION)
  - Online Tests builder pattern (ONLINE_TEST_CASE, GetPipeline)
  - Custom macros (RESONANCE_TEST_CASE, etc.)
- **Module isolation**: Test Core, CoreUObject, Online subsystems independently
- **Two module types**:
  - **Explicit tests**: Self-contained executables with .Build.cs and .Target.cs
  - **Implicit tests**: Embedded in module Tests/ directories, compiled with WITH_LOW_LEVEL_TESTS=1

### 2.2 Existing Dante Template System

The dante plugin already has a comprehensive template system at `/Users/stephen.ma/dante_plugin/skills/templates/`:

```
templates/
├── cpp-catch2-template.md         # Generic Catch2 template
├── cpp-gtest-template.md          # Google Test template
├── python-pytest-template.md      # pytest template
├── java-junit5-template.md        # JUnit 5 template
└── helpers/                       # Test helper templates
```

**Key features:**
- Placeholder-based substitution: `{{MODULE_NAME}}`, `{{TEST_CASES}}`, etc.
- Pattern library: Common test patterns for each framework
- Multi-language support: C++, Python, Java, JavaScript, TypeScript, C#, Go, Rust

**Extension needed:**
- Add LLT-specific templates with Fortnite codebase patterns
- Add UE-specific placeholders: `{{UE_MODULE_NAME}}`, `{{PLUGIN_NAME}}`, etc.
- Add module scaffolding templates for .Build.cs and .Target.cs

### 2.3 Test Patterns from Fortnite Codebase

Based on exploration of the Fortnite codebase, we identified these patterns:

#### A. Standard Catch2 Tests (CommChannels example)

**File:** `/FortniteGame/Plugins/CommChannels/Tests/Private/CommChannelsTests_ChannelSubscription.cpp`

```cpp
#include "TestHarness.h"
#include "CommChannelsTypes.h"

TEST_CASE("Channel Subscriptions")
{
    FCommChannelNode NodeA;
    FCommChannelNode NodeB;
    FCommChannelNode NodeC;
    FCommChannelNode NodeD;

    // Test logic here
    REQUIRE(NodeA.IsValid());
}
```

**Pattern characteristics:**
- Simple TEST_CASE with descriptive name
- UE types (FCommChannelNode, TArray, TMap, etc.)
- REQUIRE/CHECK for assertions

#### B. Online Tests Builder Pattern (OnlineServicesMcp example)

**File:** `/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp`

```cpp
#include "OnlineCatchHelper.h"
#include "Online/Resonance.h"

#define RESONANCE_TAG "[suite_resonance]"
#define RESONANCE_TEST_CASE(x, ...) ONLINE_TEST_CASE(x, RESONANCE_TAG __VA_ARGS__)

RESONANCE_TEST_CASE("Start, Update and End conversation with minimal params", "[startupdateend]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        const Resonance::FStartConversation::Result& StartResult =
            GetAsyncOpResultChecked(Resonance->StartConversation({}),
                                   BlockUntilCompleteDefaultMaxTicks,
                                   ESleepBehavior::Sleep);
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        (void) GetAsyncOpResultChecked(Resonance->UpdateConversation({ ConversationId }),
                                      BlockUntilCompleteDefaultMaxTicks,
                                      ESleepBehavior::Sleep);

        (void) GetAsyncOpResultChecked(Resonance->EndConversation({ ConversationId }),
                                      BlockUntilCompleteDefaultMaxTicks,
                                      ESleepBehavior::Sleep);
    });

    RunToCompletion();
}
```

**Pattern characteristics:**
- Custom macro wrapping ONLINE_TEST_CASE
- Builder pipeline: `GetPipeline().EmplaceLambda()`
- Async operation handling: `GetAsyncOpResultChecked()`
- Interface access: `Services->GetInterface<T>()`
- Final execution: `RunToCompletion()`

#### C. TestModuleRules (Build.cs pattern)

**File:** `/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/OnlineServicesMcpTests.Build.cs`

```csharp
using System;
using UnrealBuildTool;

public class OnlineServicesMcpTests : TestModuleRules
{
    public virtual bool bRequireApplicationTick => false;
    public virtual bool bRequirePlatformInit { get { return false; } }

    static OnlineServicesMcpTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "OnlineServicesMcpTests";
        TestMetadata.TestShortName = "OnlineServicesMcpTests";
        TestMetadata.ReportType = "xml";
        TestMetadata.GauntletArgs = "-printreport";
        TestMetadata.StagesWithProjectFile = true;
    }

    public OnlineServicesMcpTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "OnlineTestsCore",
                "OnlineServicesMcp",          // MODULE UNDER TEST
                "ApplicationCore",
                "Core",
                "CoreUObject",
                "Engine",
                "EOSSDKFN",
                "Projects",
                "EngineSettings",
                "TestDataServiceHelpers"
            });

        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREAPPLICATIONTICK={0}",
                                           bRequireApplicationTick ? 1 : 0));
        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREPLATFORMINIT={0}",
                                           bRequirePlatformInit ? 1 : 0));
    }
}
```

**Pattern characteristics:**
- Inherits from `TestModuleRules` (not `ModuleRules`)
- Static constructor sets TestMetadata
- TestName, TestShortName, ReportType, GauntletArgs
- PrivateDependencyModuleNames includes:
  - Test framework (OnlineTestsCore, OSSTestsCore, Catch2)
  - Module under test (OnlineServicesMcp)
  - UE core modules (Core, CoreUObject, Engine)
- Optional definitions for test configuration

#### D. TestTargetRules (Target.cs pattern)

**File:** `/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/OnlineServicesMcpTests.Target.cs`

```csharp
using UnrealBuildTool;
using MyProject.Core;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class OnlineServicesMcpTestsTarget : TestTargetRules
{
    public OnlineServicesMcpTestsTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Program;
        bCompileAgainstEngine = true;
        bCompileAgainstCoreUObject = true;
        bCompileAgainstApplicationCore = true;

        bMockEngineDefaults = true;
        bUsePlatformFileStub = true;

        bWithLowLevelTestsOverride = false; // Don't pull in implicit tests

        EnablePlugins.Add("OnlineServicesMcp");

        GlobalDefinitions.Add("ONLINETESTS_USEEXTERNAUTH=1");
    }
}
```

**Pattern characteristics:**
- Inherits from `TestTargetRules` (not `TargetRules`)
- `[SupportedPlatforms(UnrealPlatformClass.All)]` attribute
- Type = TargetType.Program
- bCompileAgainstEngine, bCompileAgainstCoreUObject flags
- bMockEngineDefaults for test isolation
- EnablePlugins for plugin-based tests
- GlobalDefinitions for test configuration

### 2.4 Integration with llt-skills-sdd.md

This SDD complements the existing llt-skills-sdd.md:

| llt-skills-sdd.md | llt-test-generation-sdd.md (this) |
|------------------|----------------------------------|
| **Finding tests** (llt-find) | **Generating tests** (templates + scaffolding) |
| **Building tests** (llt-build) | **Module setup** (.Build.cs, .Target.cs generation) |
| **Running tests** (llt-run) | **Metadata-driven generation** (use llt-find output) |
| **Parsing results** (llt-parse) | **Template architecture** (integration with test-engineering:templates) |

**Workflow:**
```
1. llt-find → Discover existing tests and source files
2. llt-coverage → Identify untested modules
3. /test-generate → Use templates to scaffold new tests
4. llt-build → Compile new tests
5. llt-run → Execute and verify
```

---

## 3. Template Architecture

### 3.1 Integration with Existing test-engineering:templates Skill

The dante plugin already has templates at `/skills/templates/`. We extend this with LLT-specific templates:

```
skills/templates/
├── cpp-catch2-template.md                  # Generic Catch2 (already exists)
├── cpp-catch2-llt-template.md              # NEW: UE-specific Catch2
├── cpp-catch2-llt-fixture-template.md      # NEW: With TEST_CASE_METHOD
├── cpp-online-tests-template.md            # NEW: Online Tests builder pattern
├── cpp-llt-implicit-template.md            # NEW: Implicit test (no module setup)
└── scaffolding/
    ├── ue-test-build-cs-template.md        # NEW: .Build.cs (TestModuleRules)
    └── ue-test-target-cs-template.md       # NEW: .Target.cs (TestTargetRules)
```

### 3.2 Template File Naming Convention

| Template Type | File Name Pattern | Example |
|--------------|------------------|---------|
| **Test File** | `cpp-{framework}-llt-template.md` | `cpp-catch2-llt-template.md` |
| **Fixture Test** | `cpp-{framework}-llt-fixture-template.md` | `cpp-catch2-llt-fixture-template.md` |
| **Builder Pattern** | `cpp-online-tests-template.md` | `cpp-online-tests-template.md` |
| **Module Setup** | `ue-test-{type}-template.md` | `ue-test-build-cs-template.md` |

### 3.3 Variable Substitution System

**Existing placeholders** (from cpp-catch2-template.md):
- `{{MODULE_NAME}}` - Module being tested
- `{{TEST_DESCRIPTION}}` - Test case description
- `{{TEST_TAG}}` - Catch2 tag
- `{{SECTION_NAME}}` - Section name
- `{{SETUP_CODE}}` - Arrange phase
- `{{CODE_UNDER_TEST}}` - Act phase
- `{{ASSERTIONS}}` - Assert phase

**New LLT-specific placeholders:**

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{UE_MODULE_NAME}}` | UE module name | `OnlineServicesMcp`, `Core`, `CoreUObject` |
| `{{PLUGIN_NAME}}` | Plugin name | `OnlineServicesMcp`, `CommChannels` |
| `{{TEST_TARGET_NAME}}` | Test target name | `OnlineServicesMcpTests`, `CommChannelsTests` |
| `{{TEST_SHORT_NAME}}` | Short test name for BuildGraph | `OnlineServicesMcp`, `CommChannels` |
| `{{UE_HEADER_PATH}}` | UE header include path | `Online/Resonance.h`, `CommChannelsTypes.h` |
| `{{INTERFACE_NAME}}` | Online interface name | `IResonance`, `IAuth`, `ISessions` |
| `{{DEPENDENCY_MODULES}}` | Comma-separated module list | `"Core", "CoreUObject", "OnlineTestsCore"` |
| `{{ENABLE_PLUGINS}}` | Plugins to enable | `"OnlineServicesMcp"` |
| `{{CUSTOM_MACRO_NAME}}` | Custom test macro | `RESONANCE_TEST_CASE`, `OSS_TEST_CASE` |
| `{{CUSTOM_MACRO_TAG}}` | Custom macro tag | `RESONANCE_TAG`, `OSS_TAG` |
| `{{PIPELINE_STEPS}}` | Builder pipeline steps | See Online Tests pattern |
| `{{GAUNTLET_ARGS}}` | Gauntlet arguments | `"-printreport"`, `"-timeout=10"` |

### 3.4 Framework Detection and Selection

When generating tests, auto-detect the appropriate template based on context:

```python
def detect_test_framework(source_file_path: str, module_name: str) -> str:
    """
    Detect which test framework/pattern to use.

    Returns: "catch2-basic" | "catch2-fixture" | "online-tests" | "implicit"
    """
    # Check if it's an Online subsystem
    if "Online" in source_file_path or "OSS" in module_name:
        # Check for interface pattern
        if has_interface_pattern(source_file_path):
            return "online-tests"

    # Check if module has existing .Build.cs/.Target.cs
    module_dir = get_module_directory(source_file_path)
    if has_build_cs(module_dir) and has_target_cs(module_dir):
        # Explicit test - check for fixture needs
        if needs_fixture(source_file_path):
            return "catch2-fixture"
        return "catch2-basic"

    # Implicit test (no module setup files)
    return "implicit"

def has_interface_pattern(file_path: str) -> bool:
    """Check if file defines an online interface (IAuth, ISessions, etc.)"""
    content = read_file(file_path)
    return re.search(r'class\s+I[A-Z]\w+\s*:', content) is not None

def needs_fixture(file_path: str) -> bool:
    """Check if code needs a fixture (e.g., complex setup/teardown)"""
    content = read_file(file_path)
    # Look for patterns that suggest fixture needs
    patterns = [
        r'class\s+\w+\s*{[^}]*private:[^}]*}',  # Private members
        r'(Setup|Initialize|Construct)\w*\(',    # Setup methods
        r'(Teardown|Cleanup|Destruct)\w*\('      # Teardown methods
    ]
    return any(re.search(pattern, content) for pattern in patterns)
```

---

## 4. Test File Templates

### 4.1 Catch2 Basic Test Template

**File:** `skills/templates/cpp-catch2-llt-template.md`

**Purpose:** Generate standard Catch2 tests for UE modules (non-Online, no fixtures)

**Template:**

```cpp

#include "TestHarness.h"
#include "{{UE_HEADER_PATH}}"

/**
 * Test suite for {{UE_MODULE_NAME}}::{{CLASS_NAME}}
 *
 * Test coverage:
 * - {{COVERAGE_AREA_1}}
 * - {{COVERAGE_AREA_2}}
 * - {{COVERAGE_AREA_3}}
 */

// ============================================================================
// Basic Tests: {{CLASS_NAME}}
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{MODULE_TAG}}][{{FEATURE_TAG}}]")
{
    // Arrange
    {{SETUP_CODE}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}} - edge cases", "[{{MODULE_TAG}}][edge-case]")
{
    SECTION("{{EDGE_CASE_1_NAME}}")
    {
        // Arrange
        {{EDGE_CASE_1_SETUP}}

        // Act
        {{EDGE_CASE_1_CODE}}

        // Assert
        {{EDGE_CASE_1_ASSERTIONS}}
    }

    SECTION("{{EDGE_CASE_2_NAME}}")
    {
        // Arrange
        {{EDGE_CASE_2_SETUP}}

        // Act
        {{EDGE_CASE_2_CODE}}

        // Assert
        {{EDGE_CASE_2_ASSERTIONS}}
    }
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}} - error handling", "[{{MODULE_TAG}}][error]")
{
    SECTION("Handles invalid input")
    {
        // Arrange
        {{ERROR_SETUP}}

        // Act & Assert
        {{ERROR_ASSERTIONS}}
    }
}
```

**Real-world example** (based on CommChannelsTests):

```cpp

#include "TestHarness.h"
#include "CommChannelsTypes.h"

/**
 * Test suite for CommChannels::FCommChannelNode
 *
 * Test coverage:
 * - Channel subscription management
 * - Node-to-node communication
 * - Subscription lifecycle
 */

// ============================================================================
// Basic Tests: Channel Subscriptions
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode::Subscribe", "[CommChannels][Subscription]")
{
    // Arrange
    FCommChannelNode NodeA;
    FCommChannelNode NodeB;

    // Act
    NodeA.Subscribe(TEXT("TestChannel"));
    NodeB.Subscribe(TEXT("TestChannel"));

    // Assert
    REQUIRE(NodeA.IsSubscribed(TEXT("TestChannel")));
    REQUIRE(NodeB.IsSubscribed(TEXT("TestChannel")));
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode::Subscribe - edge cases", "[CommChannels][edge-case]")
{
    SECTION("Empty channel name")
    {
        // Arrange
        FCommChannelNode Node;

        // Act
        bool bResult = Node.Subscribe(TEXT(""));

        // Assert
        REQUIRE_FALSE(bResult);
    }

    SECTION("Duplicate subscription")
    {
        // Arrange
        FCommChannelNode Node;
        Node.Subscribe(TEXT("Channel"));

        // Act
        bool bResult = Node.Subscribe(TEXT("Channel"));

        // Assert
        REQUIRE(bResult);  // Idempotent
        REQUIRE(Node.GetSubscriptionCount(TEXT("Channel")) == 1);
    }
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode - error handling", "[CommChannels][error]")
{
    SECTION("Handles invalid channel")
    {
        // Arrange
        FCommChannelNode Node;

        // Act & Assert
        REQUIRE_THROWS_AS(Node.SendMessage(TEXT("InvalidChannel"), {}),
                         FCommChannelException);
    }
}
```

### 4.2 Catch2 Test with Fixtures (TEST_CASE_METHOD)

**File:** `skills/templates/cpp-catch2-llt-fixture-template.md`

**Purpose:** Generate tests that require setup/teardown with TEST_CASE_METHOD

**Template:**

```cpp

#include "TestHarness.h"
#include "{{UE_HEADER_PATH}}"

/**
 * Test fixture for {{UE_MODULE_NAME}}::{{CLASS_NAME}}
 */
class {{FIXTURE_CLASS_NAME}}
{
public:
    {{FIXTURE_CLASS_NAME}}()
    {
        // Setup
        {{FIXTURE_SETUP}}
    }

    ~{{FIXTURE_CLASS_NAME}}()
    {
        // Teardown
        {{FIXTURE_TEARDOWN}}
    }

protected:
    {{FIXTURE_MEMBERS}}
};

// ============================================================================
// Tests with Fixture
// ============================================================================

TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}},
                "{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}",
                "[{{MODULE_TAG}}][{{FEATURE_TAG}}]")
{
    // Arrange (fixture already set up)
    {{ADDITIONAL_SETUP}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}

    // Teardown handled by fixture destructor
}

TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}},
                "{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}} - with sections",
                "[{{MODULE_TAG}}][{{FEATURE_TAG}}]")
{
    SECTION("{{SECTION_1_NAME}}")
    {
        // Act
        {{SECTION_1_CODE}}

        // Assert
        {{SECTION_1_ASSERTIONS}}
    }

    SECTION("{{SECTION_2_NAME}}")
    {
        // Act
        {{SECTION_2_CODE}}

        // Assert
        {{SECTION_2_ASSERTIONS}}
    }
}
```

**Example:**

```cpp

#include "TestHarness.h"
#include "Online/Auth.h"

/**
 * Test fixture for Auth interface testing
 */
class FAuthTestFixture
{
public:
    FAuthTestFixture()
    {
        // Setup
        Services = CreateTestOnlineServices();
        Auth = Services->GetInterface<IAuth>();
        REQUIRE(Auth);
    }

    ~FAuthTestFixture()
    {
        // Teardown
        Auth.Reset();
        Services.Reset();
    }

protected:
    IOnlineServicesPtr Services;
    TSharedPtr<IAuth> Auth;
};

// ============================================================================
// Tests with Fixture
// ============================================================================

TEST_CASE_METHOD(FAuthTestFixture,
                "Auth::Login - valid credentials",
                "[Auth][Login]")
{
    // Arrange (fixture already set up)
    FAuthLogin::Params Params;
    Params.Credentials.Type = ELoginCredentialsType::Developer;

    // Act
    TOnlineResult<FAuthLogin> Result = Auth->Login(Params);

    // Assert
    REQUIRE(Result.IsOk());
    REQUIRE(Result.GetOkValue().AccountInfo->AccountId.IsValid());
}

TEST_CASE_METHOD(FAuthTestFixture,
                "Auth::Login - with sections",
                "[Auth][Login]")
{
    SECTION("Valid developer credentials")
    {
        // Act
        FAuthLogin::Params Params;
        Params.Credentials.Type = ELoginCredentialsType::Developer;
        TOnlineResult<FAuthLogin> Result = Auth->Login(Params);

        // Assert
        REQUIRE(Result.IsOk());
    }

    SECTION("Invalid credentials")
    {
        // Act
        FAuthLogin::Params Params;
        Params.Credentials.Type = ELoginCredentialsType::Developer;
        Params.Credentials.Id = TEXT("invalid");
        TOnlineResult<FAuthLogin> Result = Auth->Login(Params);

        // Assert
        REQUIRE_FALSE(Result.IsOk());
    }
}
```

### 4.3 Online Tests Builder Pattern Template

**File:** `skills/templates/cpp-online-tests-template.md`

**Purpose:** Generate tests using Online Tests async pipeline pattern

**Template:**

```cpp

#include "OnlineCatchHelper.h"
#include "Online/{{INTERFACE_NAME}}.h"

#define {{CUSTOM_MACRO_TAG}} "[suite_{{MODULE_SHORT_NAME}}]"
#define {{CUSTOM_MACRO_NAME}}(x, ...) ONLINE_TEST_CASE(x, {{CUSTOM_MACRO_TAG}} __VA_ARGS__)

using namespace UE::TestCommon;

// ============================================================================
// {{INTERFACE_NAME}} Tests
// ============================================================================

{{CUSTOM_MACRO_NAME}}("{{TEST_DESCRIPTION}}", "[{{TEST_TAG}}]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<{{INTERFACE_NAME}}> Interface = Services->GetInterface<{{INTERFACE_NAME}}>();
        REQUIRE(Interface);

        {{PIPELINE_STEPS}}
    });

    RunToCompletion();
}

{{CUSTOM_MACRO_NAME}}("{{TEST_DESCRIPTION_2}}", "[{{TEST_TAG_2}}]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<{{INTERFACE_NAME}}> Interface = Services->GetInterface<{{INTERFACE_NAME}}>();
        REQUIRE(Interface);

        // Step 1: {{STEP_1_DESCRIPTION}}
        {{STEP_1_PARAMS}}
        const {{STEP_1_RESULT_TYPE}}& Result1 = GetAsyncOpResultChecked(
            Interface->{{STEP_1_METHOD}}({{STEP_1_ARGS}}),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        {{STEP_1_ASSERTIONS}}

        // Step 2: {{STEP_2_DESCRIPTION}}
        {{STEP_2_PARAMS}}
        const {{STEP_2_RESULT_TYPE}}& Result2 = GetAsyncOpResultChecked(
            Interface->{{STEP_2_METHOD}}({{STEP_2_ARGS}}),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        {{STEP_2_ASSERTIONS}}
    });

    RunToCompletion();
}
```

**Real-world example** (based on ResonanceTests.cpp):

```cpp

#include "OnlineCatchHelper.h"
#include "Online/Resonance.h"

#define RESONANCE_TAG "[suite_resonance]"
#define RESONANCE_TEST_CASE(x, ...) ONLINE_TEST_CASE(x, RESONANCE_TAG __VA_ARGS__)

using namespace UE::TestCommon;

// ============================================================================
// IResonance Tests
// ============================================================================

RESONANCE_TEST_CASE("Start, Update and End conversation with minimal params", "[startupdateend]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Step 1: Start conversation
        const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
            Resonance->StartConversation({}),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        // Step 2: Update conversation
        (void) GetAsyncOpResultChecked(
            Resonance->UpdateConversation({ ConversationId }),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );

        // Step 3: End conversation
        (void) GetAsyncOpResultChecked(
            Resonance->EndConversation({ ConversationId }),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
    });

    RunToCompletion();
}

RESONANCE_TEST_CASE("Start conversation with SystemInstruction", "[start][startwithsysteminstruction]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Step 1: Prepare context item
        Resonance::FContextItem ContextItem;
        ContextItem.Emplace<Resonance::FSystemInstruction>(TEXT("Test Instruction"));

        Resonance::FStartConversation::Params StartParams;
        StartParams.ContextItems.Emplace(MoveTemp(ContextItem));

        // Step 2: Start conversation with system instruction
        const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
            Resonance->StartConversation(MoveTemp(StartParams)),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        // Step 3: Cleanup
        (void) GetAsyncOpResultChecked(
            Resonance->EndConversation({ ConversationId }),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
    });

    RunToCompletion();
}

RESONANCE_TEST_CASE("Start conversation with User Participant", "[start][startwithuserparticipant]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Step 1: Prepare participant
        Resonance::FParticipant Participant;
        Participant.Id = TEXT("TestId");
        Participant.Role = Resonance::ERole::User;

        Resonance::FContextItem ContextItem;
        ContextItem.Emplace<Resonance::FParticipant>(MoveTemp(Participant));

        Resonance::FStartConversation::Params StartParams;
        StartParams.ContextItems.Emplace(MoveTemp(ContextItem));

        // Step 2: Start conversation
        const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
            Resonance->StartConversation(MoveTemp(StartParams)),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        // Step 3: Cleanup
        (void) GetAsyncOpResultChecked(
            Resonance->EndConversation({ ConversationId }),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
    });

    RunToCompletion();
}
```

### 4.4 Implicit Test Template

**File:** `skills/templates/cpp-llt-implicit-template.md`

**Purpose:** Generate tests embedded in module Tests/ directories (no .Build.cs/.Target.cs)

**Template:**

```cpp

#include "TestHarness.h"
#include "{{UE_HEADER_PATH}}"

// ============================================================================
// Implicit Tests: {{UE_MODULE_NAME}}::{{CLASS_NAME}}
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{MODULE_TAG}}]")
{
    // Arrange
    {{SETUP_CODE}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Note:** Implicit tests are discovered and compiled by UBT when:
- `bWithLowLevelTestsOverride=true` in .Target.cs
- `WITH_LOW_LEVEL_TESTS=1` macro is set
- Tests are in `<Module>/Tests/` directory

**Example:**

```cpp

#include "TestHarness.h"
#include "Containers/LruCache.h"

// ============================================================================
// Implicit Tests: Core::TLruCache
// ============================================================================

TEST_CASE("Core::TLruCache::Add", "[Core][Containers]")
{
    // Arrange
    TLruCache<int32, FString> Cache(3);

    // Act
    Cache.Add(1, TEXT("One"));
    Cache.Add(2, TEXT("Two"));
    Cache.Add(3, TEXT("Three"));

    // Assert
    REQUIRE(Cache.Num() == 3);
    REQUIRE(Cache.Contains(1));
    REQUIRE(Cache.Contains(2));
    REQUIRE(Cache.Contains(3));
}

TEST_CASE("Core::TLruCache::Eviction", "[Core][Containers][edge-case]")
{
    // Arrange
    TLruCache<int32, FString> Cache(2);  // Capacity = 2

    // Act
    Cache.Add(1, TEXT("One"));
    Cache.Add(2, TEXT("Two"));
    Cache.Add(3, TEXT("Three"));  // Should evict key 1

    // Assert
    REQUIRE(Cache.Num() == 2);
    REQUIRE_FALSE(Cache.Contains(1));  // Evicted
    REQUIRE(Cache.Contains(2));
    REQUIRE(Cache.Contains(3));
}
```

---

## 5. Module Scaffolding

### 5.1 .Build.cs Generation (TestModuleRules)

**File:** `skills/templates/scaffolding/ue-test-build-cs-template.md`

**Purpose:** Generate .Build.cs files for explicit test targets

**Template:**

```csharp

using System;
using UnrealBuildTool;

public class {{TEST_TARGET_NAME}} : TestModuleRules
{
    public virtual bool bRequireApplicationTick => {{REQUIRE_APP_TICK}};
    public virtual bool bRequirePlatformInit { get { return {{REQUIRE_PLATFORM_INIT}}; } }

    static {{TEST_TARGET_NAME}}()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "{{TEST_NAME}}";
        TestMetadata.TestShortName = "{{TEST_SHORT_NAME}}";
        TestMetadata.ReportType = "{{REPORT_TYPE}}";
        TestMetadata.GauntletArgs = "{{GAUNTLET_ARGS}}";
        TestMetadata.StagesWithProjectFile = {{STAGES_WITH_PROJECT_FILE}};
    }

    public {{TEST_TARGET_NAME}}(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                {{DEPENDENCY_MODULES}}
            });

        {{ADDITIONAL_CONFIG}}
    }
}
```

**Real-world example** (OnlineServicesMcpTests.Build.cs):

```csharp

using System;
using UnrealBuildTool;

public class OnlineServicesMcpTests : TestModuleRules
{
    public virtual bool bRequireApplicationTick => false;
    public virtual bool bRequirePlatformInit { get { return false; } }

    static OnlineServicesMcpTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "OnlineServicesMcpTests";
        TestMetadata.TestShortName = "OnlineServicesMcp";
        TestMetadata.ReportType = "xml";
        TestMetadata.GauntletArgs = "-printreport";
        TestMetadata.StagesWithProjectFile = true;
    }

    public OnlineServicesMcpTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "OnlineTestsCore",
                "OnlineServicesMcp",
                "ApplicationCore",
                "Core",
                "CoreUObject",
                "Engine",
                "EOSSDKFN",
                "Projects",
                "EngineSettings",
                "TestDataServiceHelpers"
            });

        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREAPPLICATIONTICK={0}",
                                           bRequireApplicationTick ? 1 : 0));
        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREPLATFORMINIT={0}",
                                           bRequirePlatformInit ? 1 : 0));
    }
}
```

**Generation logic:**

```python
def generate_build_cs(module_name: str, module_under_test: str, test_type: str) -> str:
    """
    Generate .Build.cs file for test module.

    Args:
        module_name: Test module name (e.g., "OnlineServicesMcpTests")
        module_under_test: Module being tested (e.g., "OnlineServicesMcp")
        test_type: "online-tests" | "catch2-basic" | "catch2-fixture"
    """
    # Determine test framework dependencies
    if test_type == "online-tests":
        test_core = "OnlineTestsCore"
        require_app_tick = "false"
        require_platform_init = "false"
    elif test_type.startswith("oss-"):
        test_core = "OSSTestsCore"
        require_app_tick = "false"
        require_platform_init = "false"
    else:
        test_core = "Catch2"
        require_app_tick = "false"
        require_platform_init = "false"

    # Build dependency list
    dependencies = [
        f'"{test_core}"',
        f'"{module_under_test}"',
        '"ApplicationCore"',
        '"Core"',
        '"CoreUObject"'
    ]

    # Add Engine for complex tests
    if test_type in ["online-tests", "catch2-fixture"]:
        dependencies.append('"Engine"')

    # Format dependencies
    dependency_string = ",\n                ".join(dependencies)

    # Additional config for Online Tests
    additional_config = ""
    if test_type == "online-tests":
        additional_config = '''
        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREAPPLICATIONTICK={0}",
                                           bRequireApplicationTick ? 1 : 0));
        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREPLATFORMINIT={0}",
                                           bRequirePlatformInit ? 1 : 0));'''

    # Apply template substitution
    template = load_template("ue-test-build-cs-template.md")
    return template.format(
        TEST_TARGET_NAME=module_name,
        REQUIRE_APP_TICK=require_app_tick,
        REQUIRE_PLATFORM_INIT=require_platform_init,
        TEST_NAME=module_name,
        TEST_SHORT_NAME=module_name.replace("Tests", ""),
        REPORT_TYPE="xml",
        GAUNTLET_ARGS="-printreport",
        STAGES_WITH_PROJECT_FILE="true",
        DEPENDENCY_MODULES=dependency_string,
        ADDITIONAL_CONFIG=additional_config
    )
```

### 5.2 .Target.cs Generation (TestTargetRules)

**File:** `skills/templates/scaffolding/ue-test-target-cs-template.md`

**Purpose:** Generate .Target.cs files for explicit test targets

**Template:**

```csharp

using UnrealBuildTool;
using MyProject.Core;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class {{TEST_TARGET_NAME}}Target : TestTargetRules
{
    public {{TEST_TARGET_NAME}}Target(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Program;
        bCompileAgainstEngine = {{COMPILE_AGAINST_ENGINE}};
        bCompileAgainstCoreUObject = {{COMPILE_AGAINST_COREUOBJECT}};
        bCompileAgainstApplicationCore = {{COMPILE_AGAINST_APPCORE}};

        bMockEngineDefaults = {{MOCK_ENGINE_DEFAULTS}};
        bUsePlatformFileStub = {{USE_PLATFORM_FILE_STUB}};

        bWithLowLevelTestsOverride = {{WITH_LLT_OVERRIDE}};

        {{ENABLE_PLUGINS_BLOCK}}

        {{GLOBAL_DEFINITIONS_BLOCK}}
    }
}
```

**Real-world example** (OnlineServicesMcpTests.Target.cs):

```csharp

using UnrealBuildTool;
using MyProject.Core;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class OnlineServicesMcpTestsTarget : TestTargetRules
{
    public OnlineServicesMcpTestsTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Program;
        bCompileAgainstEngine = true;
        bCompileAgainstCoreUObject = true;
        bCompileAgainstApplicationCore = true;

        bMockEngineDefaults = true;
        bUsePlatformFileStub = true;

        bWithLowLevelTestsOverride = false;

        EnablePlugins.Add("OnlineServicesMcp");

        GlobalDefinitions.Add("ONLINETESTS_USEEXTERNAUTH=1");
    }
}
```

**Generation logic:**

```python
def generate_target_cs(module_name: str, plugin_name: str = None,
                      test_type: str = "catch2-basic") -> str:
    """
    Generate .Target.cs file for test target.

    Args:
        module_name: Test module name (e.g., "OnlineServicesMcpTests")
        plugin_name: Plugin to enable (e.g., "OnlineServicesMcp"), None for Engine tests
        test_type: Type of test ("online-tests" | "catch2-basic" | "catch2-fixture")
    """
    # Determine compilation flags based on test type
    if test_type == "online-tests":
        compile_against_engine = "true"
        compile_against_coreuobject = "true"
        compile_against_appcore = "true"
    elif test_type == "catch2-fixture":
        compile_against_engine = "true"
        compile_against_coreuobject = "true"
        compile_against_appcore = "true"
    else:  # catch2-basic
        compile_against_engine = "false"
        compile_against_coreuobject = "true"
        compile_against_appcore = "true"

    # Mock engine for isolation
    mock_engine_defaults = "true"
    use_platform_file_stub = "true"

    # Don't pull in implicit tests (usually)
    with_llt_override = "false"

    # Enable plugin if specified
    enable_plugins_block = ""
    if plugin_name:
        enable_plugins_block = f'EnablePlugins.Add("{plugin_name}");'

    # Global definitions for Online Tests
    global_definitions_block = ""
    if test_type == "online-tests":
        global_definitions_block = 'GlobalDefinitions.Add("ONLINETESTS_USEEXTERNAUTH=1");'

    # Apply template substitution
    template = load_template("ue-test-target-cs-template.md")
    return template.format(
        TEST_TARGET_NAME=module_name,
        COMPILE_AGAINST_ENGINE=compile_against_engine,
        COMPILE_AGAINST_COREUOBJECT=compile_against_coreuobject,
        COMPILE_AGAINST_APPCORE=compile_against_appcore,
        MOCK_ENGINE_DEFAULTS=mock_engine_defaults,
        USE_PLATFORM_FILE_STUB=use_platform_file_stub,
        WITH_LLT_OVERRIDE=with_llt_override,
        ENABLE_PLUGINS_BLOCK=enable_plugins_block,
        GLOBAL_DEFINITIONS_BLOCK=global_definitions_block
    )
```

### 5.3 Directory Structure Setup

When generating a new explicit test module, create this structure:

```
<PluginRoot>/Tests/<TestModuleName>/
├── <TestModuleName>.Build.cs
├── <TestModuleName>.Target.cs
├── Private/
│   ├── <Feature1>Tests.cpp
│   ├── <Feature2>Tests.cpp
│   └── <Feature3>Tests.cpp
└── Resources/
    └── (test data files, if needed)
```

**Example for OnlineServicesMcp:**

```
FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/
├── OnlineServicesMcpTests.Build.cs
├── OnlineServicesMcpTests.Target.cs
├── Private/
│   ├── ResonanceTests.cpp
│   ├── OnlineTDSAuth.cpp
│   └── OnlineServicesTests.cpp
└── Resources/
    └── DefaultEngine.ini
```

**Python implementation:**

```python
def create_test_module_directory(plugin_root: str, module_name: str) -> str:
    """
    Create directory structure for new test module.

    Returns: Path to test module directory
    """
    test_module_dir = os.path.join(plugin_root, "Tests", module_name)

    # Create directories
    os.makedirs(test_module_dir, exist_ok=True)
    os.makedirs(os.path.join(test_module_dir, "Private"), exist_ok=True)
    os.makedirs(os.path.join(test_module_dir, "Resources"), exist_ok=True)

    return test_module_dir

def generate_full_test_module(module_under_test: str, plugin_name: str = None):
    """
    Generate complete test module with .Build.cs, .Target.cs, and test file.
    """
    # Determine paths
    if plugin_name:
        plugin_root = find_plugin_directory(plugin_name)
    else:
        plugin_root = find_engine_module_directory(module_under_test)

    test_module_name = f"{module_under_test}Tests"

    # Create directory structure
    test_module_dir = create_test_module_directory(plugin_root, test_module_name)

    # Detect test type
    test_type = detect_test_framework(plugin_root, module_under_test)

    # Generate .Build.cs
    build_cs_content = generate_build_cs(test_module_name, module_under_test, test_type)
    write_file(os.path.join(test_module_dir, f"{test_module_name}.Build.cs"),
              build_cs_content)

    # Generate .Target.cs
    target_cs_content = generate_target_cs(test_module_name, plugin_name, test_type)
    write_file(os.path.join(test_module_dir, f"{test_module_name}.Target.cs"),
              target_cs_content)

    # Generate initial test file
    test_file_content = generate_test_file(module_under_test, test_type)
    write_file(os.path.join(test_module_dir, "Private", f"{module_under_test}Tests.cpp"),
              test_file_content)

    print(f"Generated test module at: {test_module_dir}")
    return test_module_dir
```

### 5.4 Dependency Configuration

**Key principles for module dependencies:**

1. **Always include test framework:**
   - Online Tests: `OnlineTestsCore` or `OSSTestsCore`
   - Standard Catch2: `Catch2` (or rely on Engine dependency)

2. **Include module under test:**
   - The module you're testing (e.g., `OnlineServicesMcp`)

3. **Include UE core modules:**
   - Minimum: `Core`, `CoreUObject`, `ApplicationCore`
   - For complex tests: `Engine`

4. **Include auxiliary modules:**
   - Online Tests: `EOSSDKFN`, `Projects`, `EngineSettings`
   - Test data: `TestDataServiceHelpers`

**Dependency resolution algorithm:**

```python
def resolve_test_dependencies(module_under_test: str, test_type: str) -> List[str]:
    """
    Resolve dependencies for test module based on module under test and test type.
    """
    # Start with test framework
    if test_type == "online-tests":
        dependencies = ["OnlineTestsCore"]
    elif test_type.startswith("oss-"):
        dependencies = ["OSSTestsCore"]
    else:
        dependencies = []  # Catch2 pulled in via Engine

    # Add module under test
    dependencies.append(module_under_test)

    # Add core UE modules
    dependencies.extend(["ApplicationCore", "Core", "CoreUObject"])

    # Add Engine for complex tests
    if test_type in ["online-tests", "catch2-fixture"]:
        dependencies.append("Engine")

    # Add Online-specific dependencies
    if test_type == "online-tests":
        dependencies.extend(["EOSSDKFN", "Projects", "EngineSettings"])

    # Parse module under test's .Build.cs to find transitive dependencies
    module_build_cs = find_build_cs(module_under_test)
    if module_build_cs:
        transitive_deps = parse_module_dependencies(module_build_cs)
        # Add only public dependencies (tests need them too)
        dependencies.extend(transitive_deps.get("PublicDependencyModuleNames", []))

    # Remove duplicates, preserve order
    return list(dict.fromkeys(dependencies))
```

---

## 6. Integration with /test-generate

### 6.1 Workflow: llt-find → analyze untested code → generate test stubs

**High-level workflow:**

```
User: "Generate tests for OnlineServicesMcp::IResonance"

1. llt-find:
   - Discover existing tests in OnlineServicesMcp plugin
   - Parse ResonanceTests.cpp to find existing test coverage
   - Identify tested methods

2. Analyze untested code:
   - Parse Online/Resonance.h header
   - Extract interface methods (StartConversation, UpdateConversation, EndConversation, etc.)
   - Compare with tested methods from step 1
   - Identify untested methods

3. Generate test stubs:
   - For each untested method, apply appropriate template:
     - If Online interface → use cpp-online-tests-template.md
     - If standard class → use cpp-catch2-llt-template.md
     - If complex setup needed → use cpp-catch2-llt-fixture-template.md
   - Fill in placeholders with detected metadata
   - Write to appropriate test file

4. llt-build:
   - Compile new tests

5. llt-run:
   - Execute and verify tests compile and run
```

**Implementation:**

```python
def generate_tests_for_module(module_name: str, source_file: str = None):
    """
    Generate tests for a module or specific source file.

    Args:
        module_name: Module name (e.g., "OnlineServicesMcp")
        source_file: Optional specific file to test (e.g., "Online/Resonance.h")
    """
    # Step 1: Find existing tests
    llt_find_output = run_llt_find(module_name)
    existing_tests = parse_existing_tests(llt_find_output)

    # Step 2: Analyze source code
    if source_file:
        source_files = [source_file]
    else:
        source_files = find_source_files(module_name)

    untested_methods = []
    for src_file in source_files:
        methods = extract_methods(src_file)
        for method in methods:
            if not is_method_tested(method, existing_tests):
                untested_methods.append({
                    'source_file': src_file,
                    'method': method
                })

    if not untested_methods:
        print(f"All methods in {module_name} are already tested!")
        return

    # Step 3: Generate test stubs
    print(f"Found {len(untested_methods)} untested methods")
    test_file_path = determine_test_file_path(module_name)

    for item in untested_methods:
        test_stub = generate_test_stub(
            module_name=module_name,
            source_file=item['source_file'],
            method=item['method']
        )
        append_to_test_file(test_file_path, test_stub)

    print(f"Generated test stubs in: {test_file_path}")

    # Step 4: Build tests (optional)
    if ask_user("Build tests now? (y/n)"):
        run_llt_build(module_name)

    # Step 5: Run tests (optional)
    if ask_user("Run tests now? (y/n)"):
        run_llt_run(module_name)

def generate_test_stub(module_name: str, source_file: str, method: dict) -> str:
    """
    Generate a single test stub for a method.

    Returns: Test code as string
    """
    # Detect framework
    test_type = detect_test_framework(source_file, module_name)

    # Load appropriate template
    if test_type == "online-tests":
        template = load_template("cpp-online-tests-template.md")
    elif test_type == "catch2-fixture":
        template = load_template("cpp-catch2-llt-fixture-template.md")
    else:
        template = load_template("cpp-catch2-llt-template.md")

    # Extract metadata from method
    metadata = {
        'UE_MODULE_NAME': module_name,
        'CLASS_NAME': method.class_name,
        'METHOD_NAME': method.name,
        'MODULE_TAG': module_name.lower(),
        'FEATURE_TAG': infer_feature_tag(method),
        'TEST_DESCRIPTION': generate_test_description(method),
        'SETUP_CODE': generate_setup_code(method),
        'CODE_UNDER_TEST': generate_code_under_test(method),
        'ASSERTIONS': generate_assertions(method)
    }

    # Apply template substitution
    return template.format(**metadata)

def extract_methods(source_file: str) -> List[dict]:
    """
    Extract methods from source file using regex or AST parsing.
    """
    # Parse C++ file (simplified)
    content = read_file(source_file)
    methods = []

    # Regex for method declarations
    pattern = r'(virtual\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)\s*(const\s*)?(override\s*)?;'
    for match in re.finditer(pattern, content):
        methods.append({
            'return_type': match.group(2),
            'name': match.group(3),
            'params': match.group(4),
            'is_const': bool(match.group(5)),
            'class_name': extract_class_name(content)
        })

    return methods
```

### 6.2 Command-Line Interface Design

**Proposed CLI:**

```bash
# Generate tests for entire module
dante test-generate --module OnlineServicesMcp --framework llt

# Generate tests for specific file
dante test-generate --file Online/Resonance.h --framework llt

# Generate tests with explicit test type
dante test-generate --module OnlineServicesMcp --test-type online-tests

# Generate test module scaffold (full setup)
dante test-generate --scaffold --module NewModule --plugin MyPlugin

# Generate tests and build immediately
dante test-generate --module OnlineServicesMcp --build

# Generate tests, build, and run
dante test-generate --module OnlineServicesMcp --build --run

# Interactive mode (asks for confirmation at each step)
dante test-generate --module OnlineServicesMcp --interactive
```

**Parameter details:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--module` | Module name to generate tests for | `OnlineServicesMcp` |
| `--file` | Specific source file to test | `Online/Resonance.h` |
| `--framework` | Test framework (`llt`, `catch2`, `gtest`) | `llt` |
| `--test-type` | Specific test pattern | `online-tests`, `catch2-basic`, `catch2-fixture` |
| `--scaffold` | Generate full module setup (.Build.cs, .Target.cs) | (flag) |
| `--plugin` | Plugin name (for scaffold) | `OnlineServicesMcp` |
| `--build` | Build tests after generation | (flag) |
| `--run` | Run tests after build | (flag) |
| `--interactive` | Ask for confirmation at each step | (flag) |
| `--output-dir` | Override default test output directory | `/path/to/tests` |

### 6.3 Interactive vs Autonomous Mode

**Interactive Mode** (default):

```
$ dante test-generate --module OnlineServicesMcp --interactive

Analyzing OnlineServicesMcp...
Found 5 untested methods in IResonance:
  1. CancelConversation
  2. GetConversationHistory
  3. SetParticipantRole
  4. AddContextItem
  5. RemoveContextItem

Generate tests for these methods? (y/n): y

Detected test type: online-tests
Test file: OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp

Generated test stubs:
  - ResonanceTests.cpp: "Cancel conversation with active conversation"
  - ResonanceTests.cpp: "Get conversation history after multiple updates"
  - ResonanceTests.cpp: "Set participant role to different values"
  - ResonanceTests.cpp: "Add multiple context items"
  - ResonanceTests.cpp: "Remove context item by ID"

Build tests now? (y/n): y

Building OnlineServicesMcpTests for Win64...
Build succeeded in 23.4s

Run tests now? (y/n): y

Running OnlineServicesMcpTests...
All tests passed (35/35)

Complete! Generated 5 test stubs, built, and verified.
```

**Autonomous Mode** (with `--build --run`):

```
$ dante test-generate --module OnlineServicesMcp --build --run

Analyzing OnlineServicesMcp...
Found 5 untested methods in IResonance.
Generating test stubs with online-tests pattern...
Generated 5 test stubs in ResonanceTests.cpp
Building OnlineServicesMcpTests for Win64...
Build succeeded in 23.4s
Running OnlineServicesMcpTests...
All tests passed (35/35)

Summary:
  - Generated: 5 test stubs
  - Build time: 23.4s
  - Test results: 35/35 passed

Next steps:
  - Review generated tests in: OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp
  - Fill in test assertions (marked with {{ASSERTIONS}} placeholders)
  - Add edge case tests as needed
```

### 6.4 Metadata-Driven Generation (use llt-find output from llt-skills-sdd.md)

The llt-find skill outputs detailed metadata (see Section 4.1 in llt-skills-sdd.md). Use this metadata to drive test generation:

**llt-find output (example):**

```json
{
  "test_targets": [
    {
      "name": "OnlineServicesMcpTests",
      "type": "explicit",
      "location": "/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests",
      "test_files": [
        {
          "path": "Private/ResonanceTests.cpp",
          "test_count": 12,
          "test_cases": [
            {
              "name": "Start, Update and End conversation with minimal params",
              "line": 12,
              "tags": ["suite_resonance", "startupdateend"],
              "sections": []
            },
            {
              "name": "Start conversation with SystemInstruction",
              "line": 31,
              "tags": ["suite_resonance", "start", "startwithsysteminstruction"],
              "sections": []
            }
          ],
          "includes": [
            "OnlineCatchHelper.h",
            "Online/Resonance.h"
          ]
        }
      ],
      "source_to_test_map": {
        "Online/Resonance.h": [
          {
            "test_file": "Private/ResonanceTests.cpp",
            "test_cases": [
              "Start, Update and End conversation with minimal params",
              "Start conversation with SystemInstruction"
            ],
            "coverage": "direct"
          }
        ]
      },
      "dependencies": ["OnlineTestsCore", "OnlineServicesMcp", "Core"],
      "platforms": ["Win64", "Mac", "Linux"],
      "test_count": 12,
      "tags": ["suite_resonance"]
    }
  ]
}
```

**Use this metadata to:**

1. **Identify tested methods:**
   ```python
   def get_tested_methods(llt_find_output: dict, source_file: str) -> List[str]:
       """Extract list of methods already tested."""
       tested_methods = []
       for target in llt_find_output['test_targets']:
           if source_file in target['source_to_test_map']:
               test_info = target['source_to_test_map'][source_file][0]
               # Parse test case names to extract method names
               for test_case in test_info['test_cases']:
                   method = extract_method_from_test_name(test_case)
                   tested_methods.append(method)
       return tested_methods
   ```

2. **Detect test patterns:**
   ```python
   def detect_test_pattern(llt_find_output: dict, module_name: str) -> str:
       """Detect test pattern from existing tests."""
       for target in llt_find_output['test_targets']:
           if target['name'].startswith(module_name):
               # Check includes for pattern detection
               for test_file in target['test_files']:
                   if 'OnlineCatchHelper.h' in test_file['includes']:
                       return 'online-tests'
               return 'catch2-basic'
       return 'catch2-basic'
   ```

3. **Infer dependencies:**
   ```python
   def infer_dependencies(llt_find_output: dict, module_name: str) -> List[str]:
       """Infer dependencies from existing test module."""
       for target in llt_find_output['test_targets']:
           if target['name'].startswith(module_name):
               return target['dependencies']
       # Default dependencies
       return ['Core', 'CoreUObject', 'ApplicationCore']
   ```

4. **Generate consistent tags:**
   ```python
   def generate_tags(llt_find_output: dict, module_name: str, feature: str) -> List[str]:
       """Generate tags consistent with existing tests."""
       for target in llt_find_output['test_targets']:
           if target['name'].startswith(module_name):
               # Use existing tags as base
               base_tags = target['tags']
               # Add feature-specific tag
               return base_tags + [feature.lower()]
       return [module_name.lower(), feature.lower()]
   ```

---

## 7. Code Examples

### 7.1 Complete Generated Test File (Catch2 Basic)

**Input:**
- Module: `CommChannels`
- Source file: `CommChannelsTypes.h`
- Class: `FCommChannelNode`
- Untested methods: `Subscribe`, `Unsubscribe`, `SendMessage`

**Generated output:**

```cpp

#include "TestHarness.h"
#include "CommChannelsTypes.h"

/**
 * Test suite for CommChannels::FCommChannelNode
 *
 * Test coverage:
 * - Channel subscription management
 * - Message sending
 * - Subscription lifecycle
 */

// ============================================================================
// Basic Tests: FCommChannelNode
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode::Subscribe", "[CommChannels][Subscription]")
{
    // Arrange
    FCommChannelNode Node;
    const FString ChannelName = TEXT("TestChannel");

    // Act
    bool bResult = Node.Subscribe(ChannelName);

    // Assert
    REQUIRE(bResult);
    REQUIRE(Node.IsSubscribed(ChannelName));
}

TEST_CASE("CommChannels::FCommChannelNode::Unsubscribe", "[CommChannels][Subscription]")
{
    // Arrange
    FCommChannelNode Node;
    const FString ChannelName = TEXT("TestChannel");
    Node.Subscribe(ChannelName);

    // Act
    bool bResult = Node.Unsubscribe(ChannelName);

    // Assert
    REQUIRE(bResult);
    REQUIRE_FALSE(Node.IsSubscribed(ChannelName));
}

TEST_CASE("CommChannels::FCommChannelNode::SendMessage", "[CommChannels][Messaging]")
{
    // Arrange
    FCommChannelNode NodeA;
    FCommChannelNode NodeB;
    const FString ChannelName = TEXT("TestChannel");
    NodeA.Subscribe(ChannelName);
    NodeB.Subscribe(ChannelName);

    FCommChannelMessage Message;
    Message.Content = TEXT("Test message");

    // Act
    bool bResult = NodeA.SendMessage(ChannelName, Message);

    // Assert
    REQUIRE(bResult);
    // TODO: Verify NodeB received the message
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode::Subscribe - edge cases", "[CommChannels][edge-case]")
{
    SECTION("Empty channel name")
    {
        // Arrange
        FCommChannelNode Node;

        // Act
        bool bResult = Node.Subscribe(TEXT(""));

        // Assert
        REQUIRE_FALSE(bResult);
    }

    SECTION("Duplicate subscription")
    {
        // Arrange
        FCommChannelNode Node;
        const FString ChannelName = TEXT("Channel");
        Node.Subscribe(ChannelName);

        // Act
        bool bResult = Node.Subscribe(ChannelName);

        // Assert
        REQUIRE(bResult);  // Idempotent
        REQUIRE(Node.GetSubscriptionCount(ChannelName) == 1);
    }

    SECTION("Unsubscribe from non-subscribed channel")
    {
        // Arrange
        FCommChannelNode Node;

        // Act
        bool bResult = Node.Unsubscribe(TEXT("NonExistent"));

        // Assert
        REQUIRE_FALSE(bResult);
    }
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("CommChannels::FCommChannelNode - error handling", "[CommChannels][error]")
{
    SECTION("Send to invalid channel")
    {
        // Arrange
        FCommChannelNode Node;
        FCommChannelMessage Message;

        // Act & Assert
        REQUIRE_THROWS_AS(Node.SendMessage(TEXT("InvalidChannel"), Message),
                         FCommChannelException);
    }

    SECTION("Send to unsubscribed channel")
    {
        // Arrange
        FCommChannelNode Node;
        FCommChannelMessage Message;
        const FString ChannelName = TEXT("TestChannel");

        // Act & Assert
        REQUIRE_FALSE(Node.SendMessage(ChannelName, Message));
    }
}
```

### 7.2 Complete Generated Test File (Online Tests Builder Pattern)

**Input:**
- Module: `OnlineServicesMcp`
- Source file: `Online/Resonance.h`
- Interface: `IResonance`
- Untested methods: `CancelConversation`, `GetConversationHistory`

**Generated output:**

```cpp

#include "OnlineCatchHelper.h"
#include "Online/Resonance.h"

#define RESONANCE_TAG "[suite_resonance]"
#define RESONANCE_TEST_CASE(x, ...) ONLINE_TEST_CASE(x, RESONANCE_TAG __VA_ARGS__)

using namespace UE::TestCommon;

/**
 * Test suite for IResonance
 *
 * Test coverage:
 * - Conversation cancellation
 * - Conversation history retrieval
 */

// ============================================================================
// IResonance Tests
// ============================================================================

RESONANCE_TEST_CASE("Cancel conversation with active conversation", "[cancel]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Step 1: Start a conversation
        const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
            Resonance->StartConversation({}),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        // Step 2: Cancel the conversation
        Resonance::FCancelConversation::Params CancelParams;
        CancelParams.ConversationId = ConversationId;

        const Resonance::FCancelConversation::Result& CancelResult = GetAsyncOpResultChecked(
            Resonance->CancelConversation(MoveTemp(CancelParams)),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );

        // Assert: Cancellation succeeded
        REQUIRE(CancelResult.bSuccess);

        // Step 3: Verify conversation is no longer active
        // TODO: Add verification that conversation cannot be updated after cancellation
    });

    RunToCompletion();
}

RESONANCE_TEST_CASE("Get conversation history after multiple updates", "[history]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Step 1: Start conversation
        const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
            Resonance->StartConversation({}),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
        const FString& ConversationId = StartResult.ConversationId;
        REQUIRE(!ConversationId.IsEmpty());

        // Step 2: Update conversation multiple times
        for (int32 i = 0; i < 3; ++i)
        {
            Resonance::FUpdateConversation::Params UpdateParams;
            UpdateParams.ConversationId = ConversationId;
            UpdateParams.Message = FString::Printf(TEXT("Update %d"), i);

            (void) GetAsyncOpResultChecked(
                Resonance->UpdateConversation(MoveTemp(UpdateParams)),
                BlockUntilCompleteDefaultMaxTicks,
                ESleepBehavior::Sleep
            );
        }

        // Step 3: Get conversation history
        Resonance::FGetConversationHistory::Params HistoryParams;
        HistoryParams.ConversationId = ConversationId;

        const Resonance::FGetConversationHistory::Result& HistoryResult = GetAsyncOpResultChecked(
            Resonance->GetConversationHistory(MoveTemp(HistoryParams)),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );

        // Assert: History contains all updates
        REQUIRE(HistoryResult.History.Num() >= 3);
        // TODO: Verify history content matches sent messages

        // Step 4: Cleanup
        (void) GetAsyncOpResultChecked(
            Resonance->EndConversation({ ConversationId }),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );
    });

    RunToCompletion();
}

RESONANCE_TEST_CASE("Cancel conversation - error cases", "[cancel][error]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
        REQUIRE(Resonance);

        // Attempt to cancel non-existent conversation
        Resonance::FCancelConversation::Params CancelParams;
        CancelParams.ConversationId = TEXT("invalid-id");

        TOnlineAsyncOpHandle<Resonance::FCancelConversation> Op = Resonance->CancelConversation(MoveTemp(CancelParams));

        // Wait for completion
        Op->Wait(BlockUntilCompleteDefaultMaxTicks);

        // Assert: Operation failed
        REQUIRE_FALSE(Op->GetResult().IsOk());
        // TODO: Verify error type
    });

    RunToCompletion();
}
```

### 7.3 Module Setup Example (.Build.cs + .Target.cs)

**Input:**
- New module: `MyFeatureTests`
- Module under test: `MyFeature`
- Plugin: `MyPlugin`

**Generated MyFeatureTests.Build.cs:**

```csharp

using System;
using UnrealBuildTool;

public class MyFeatureTests : TestModuleRules
{
    public virtual bool bRequireApplicationTick => false;
    public virtual bool bRequirePlatformInit { get { return false; } }

    static MyFeatureTests()
    {
        TestMetadata = new Metadata();
        TestMetadata.TestName = "MyFeatureTests";
        TestMetadata.TestShortName = "MyFeature";
        TestMetadata.ReportType = "xml";
        TestMetadata.GauntletArgs = "-printreport";
        TestMetadata.StagesWithProjectFile = true;
    }

    public MyFeatureTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "MyFeature",
                "ApplicationCore",
                "Core",
                "CoreUObject",
                "Engine"
            });
    }
}
```

**Generated MyFeatureTests.Target.cs:**

```csharp

using UnrealBuildTool;
using MyProject.Core;

[SupportedPlatforms(UnrealPlatformClass.All)]
public class MyFeatureTestsTarget : TestTargetRules
{
    public MyFeatureTestsTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Program;
        bCompileAgainstEngine = true;
        bCompileAgainstCoreUObject = true;
        bCompileAgainstApplicationCore = true;

        bMockEngineDefaults = true;
        bUsePlatformFileStub = true;

        bWithLowLevelTestsOverride = false;

        EnablePlugins.Add("MyPlugin");
    }
}
```

**Generated MyFeatureTests/Private/MyFeatureTests.cpp:**

```cpp

#include "TestHarness.h"
#include "MyFeature/MyFeatureComponent.h"

/**
 * Test suite for MyFeature
 *
 * Test coverage:
 * - TODO: List coverage areas
 */

// ============================================================================
// Basic Tests: MyFeatureComponent
// ============================================================================

TEST_CASE("MyFeature::MyFeatureComponent::Initialize", "[MyFeature][Init]")
{
    // Arrange
    FMyFeatureComponent Component;

    // Act
    bool bResult = Component.Initialize();

    // Assert
    REQUIRE(bResult);
    REQUIRE(Component.IsInitialized());
}

// TODO: Add more test cases
```

---

## 8. Implementation Roadmap

### Phase 1: Basic Catch2 Templates (Week 1-2)

**Goals:**
- Extend existing cpp-catch2-template.md with UE-specific patterns
- Create cpp-catch2-llt-template.md
- Create cpp-catch2-llt-fixture-template.md
- Create cpp-llt-implicit-template.md
- Add UE-specific placeholders

**Deliverables:**
- 3 new template files
- Updated template substitution engine
- Unit tests for template generation

**Success criteria:**
- Can generate basic Catch2 tests for UE modules
- Generated tests compile without errors
- Templates match real Fortnite codebase patterns

### Phase 2: Module Scaffolding (Week 3-4)

**Goals:**
- Create ue-test-build-cs-template.md
- Create ue-test-target-cs-template.md
- Implement directory structure creation
- Implement dependency resolution

**Deliverables:**
- 2 scaffolding templates
- Python scripts for .Build.cs/.Target.cs generation
- Directory creation utilities

**Success criteria:**
- Can scaffold complete test module with .Build.cs and .Target.cs
- Generated modules compile successfully
- Dependencies are correctly resolved

### Phase 3: Online Tests Templates (Week 5-6)

**Goals:**
- Create cpp-online-tests-template.md
- Implement builder pattern support
- Add pipeline step generation
- Support custom macros (RESONANCE_TEST_CASE, etc.)

**Deliverables:**
- 1 Online Tests template
- Builder pattern generator
- Custom macro support

**Success criteria:**
- Can generate Online Tests with GetPipeline pattern
- Generated tests follow established patterns
- AsyncOp handling is correct

### Phase 4: Metadata-Driven Generation (Week 7-8)

**Goals:**
- Integrate with llt-find output
- Implement untested method detection
- Implement test stub generation
- Add CLI interface

**Deliverables:**
- Test stub generator
- CLI for /test-generate
- Integration with llt-find

**Success criteria:**
- Can analyze llt-find output to identify untested code
- Can generate test stubs for untested methods
- CLI works in interactive and autonomous modes

### Phase 5: Refinement & Documentation (Week 9-10)

**Goals:**
- Add comprehensive examples
- Write user documentation
- Create video tutorials
- Gather user feedback

**Deliverables:**
- User guide for /test-generate
- Example projects
- Video walkthroughs

**Success criteria:**
- Users can generate tests without reading code
- Documentation covers common use cases
- Positive user feedback

---

## 9. Appendices

### Appendix A: Template Placeholder Reference

#### Generic Placeholders (inherited from test-engineering:templates)

| Placeholder | Type | Description | Example |
|------------|------|-------------|---------|
| `{{MODULE_NAME}}` | string | Module being tested | `Calculator` |
| `{{TEST_DESCRIPTION}}` | string | Test case description | `"Addition works correctly"` |
| `{{TEST_TAG}}` | string | Catch2 tag | `[calculator]` |
| `{{SECTION_NAME}}` | string | Section name | `"Adding positive numbers"` |
| `{{SETUP_CODE}}` | code | Arrange phase | `Calculator calc;` |
| `{{CODE_UNDER_TEST}}` | code | Act phase | `int result = calc.add(5, 3);` |
| `{{ASSERTIONS}}` | code | Assert phase | `REQUIRE(result == 8);` |

#### LLT-Specific Placeholders (new)

| Placeholder | Type | Description | Example |
|------------|------|-------------|---------|
| `{{UE_MODULE_NAME}}` | string | UE module name | `OnlineServicesMcp` |
| `{{PLUGIN_NAME}}` | string | Plugin name | `OnlineServicesMcp` |
| `{{TEST_TARGET_NAME}}` | string | Test target name | `OnlineServicesMcpTests` |
| `{{TEST_SHORT_NAME}}` | string | Short test name | `OnlineServicesMcp` |
| `{{UE_HEADER_PATH}}` | string | UE header path | `Online/Resonance.h` |
| `{{CLASS_NAME}}` | string | Class being tested | `FCommChannelNode` |
| `{{INTERFACE_NAME}}` | string | Interface name | `IResonance` |
| `{{METHOD_NAME}}` | string | Method being tested | `Subscribe` |
| `{{MODULE_TAG}}` | string | Module tag | `[CommChannels]` |
| `{{FEATURE_TAG}}` | string | Feature tag | `[Subscription]` |
| `{{DEPENDENCY_MODULES}}` | list | Module dependencies | `"Core", "CoreUObject"` |
| `{{ENABLE_PLUGINS}}` | list | Plugins to enable | `"OnlineServicesMcp"` |
| `{{CUSTOM_MACRO_NAME}}` | string | Custom test macro | `RESONANCE_TEST_CASE` |
| `{{CUSTOM_MACRO_TAG}}` | string | Custom macro tag | `RESONANCE_TAG` |
| `{{PIPELINE_STEPS}}` | code | Builder pipeline steps | See examples |
| `{{GAUNTLET_ARGS}}` | string | Gauntlet arguments | `"-printreport"` |
| `{{REQUIRE_APP_TICK}}` | bool | Require application tick | `false` |
| `{{REQUIRE_PLATFORM_INIT}}` | bool | Require platform init | `false` |
| `{{REPORT_TYPE}}` | string | Report type | `"xml"` |
| `{{STAGES_WITH_PROJECT_FILE}}` | bool | Stages with project file | `true` |
| `{{COMPILE_AGAINST_ENGINE}}` | bool | Compile against Engine | `true` |
| `{{COMPILE_AGAINST_COREUOBJECT}}` | bool | Compile against CoreUObject | `true` |
| `{{COMPILE_AGAINST_APPCORE}}` | bool | Compile against ApplicationCore | `true` |
| `{{MOCK_ENGINE_DEFAULTS}}` | bool | Mock engine defaults | `true` |
| `{{USE_PLATFORM_FILE_STUB}}` | bool | Use platform file stub | `true` |
| `{{WITH_LLT_OVERRIDE}}` | bool | Include implicit tests | `false` |

### Appendix B: Test Pattern Decision Tree

```
Given: Source file to test

1. Is it in an Online subsystem?
   YES → Does it define an interface (IAuth, ISessions, etc.)?
         YES → Use cpp-online-tests-template.md
         NO  → Continue to step 2
   NO  → Continue to step 2

2. Does the class have complex setup/teardown needs?
   (Private members, constructor/destructor, state management)
   YES → Use cpp-catch2-llt-fixture-template.md
   NO  → Continue to step 3

3. Does the module have .Build.cs and .Target.cs?
   YES → Use cpp-catch2-llt-template.md (explicit test)
   NO  → Use cpp-llt-implicit-template.md (implicit test)
```

### Appendix C: Common Test Patterns

#### Pattern 1: Simple Function Test

```cpp
TEST_CASE("Module::Function", "[Module][tag]")
{
    // Arrange
    FInputType Input = CreateTestInput();

    // Act
    FOutputType Output = FunctionUnderTest(Input);

    // Assert
    REQUIRE(Output.IsValid());
}
```

#### Pattern 2: Class Method Test with Sections

```cpp
TEST_CASE("Module::Class::Method", "[Module][tag]")
{
    FMyClass Instance;

    SECTION("Valid input")
    {
        bool bResult = Instance.Method(ValidInput);
        REQUIRE(bResult);
    }

    SECTION("Invalid input")
    {
        bool bResult = Instance.Method(InvalidInput);
        REQUIRE_FALSE(bResult);
    }
}
```

#### Pattern 3: Online Interface Test

```cpp
ONLINE_TEST_CASE("Interface operation", "[tag]")
{
    GetPipeline().EmplaceLambda([](const IOnlineServicesPtr& Services)
    {
        TSharedPtr<IInterface> Interface = Services->GetInterface<IInterface>();
        REQUIRE(Interface);

        const FResult& Result = GetAsyncOpResultChecked(
            Interface->Operation(Params),
            BlockUntilCompleteDefaultMaxTicks,
            ESleepBehavior::Sleep
        );

        REQUIRE(Result.IsValid());
    });

    RunToCompletion();
}
```

#### Pattern 4: Error Handling Test

```cpp
TEST_CASE("Module::Function - error handling", "[Module][error]")
{
    SECTION("Throws on invalid input")
    {
        REQUIRE_THROWS_AS(Function(InvalidInput), FExpectedException);
    }

    SECTION("Returns false on error")
    {
        bool bResult = Function(ErrorInput);
        REQUIRE_FALSE(bResult);
    }
}
```

### Appendix D: Known Limitations

1. **No AI-generated assertions**: Templates generate placeholder assertions (`{{ASSERTIONS}}`), requiring manual completion
2. **No mock object generation**: Test fixtures must be created manually
3. **Limited type inference**: Cannot automatically infer parameter types for complex templates
4. **No test data generation**: Test inputs must be created manually
5. **No automatic refactoring**: Changes to source code don't auto-update tests
6. **No coverage gap analysis**: Cannot detect untested code paths within tested methods

### Appendix E: Future Enhancements

1. **AI-assisted assertion generation**: Use LLM to suggest assertions based on method signatures and documentation
2. **Mock object scaffolding**: Generate mock implementations for interfaces
3. **Test data builders**: Generate builder pattern classes for complex test data
4. **Coverage-driven generation**: Use code coverage data to identify untested paths
5. **Test refactoring**: Auto-update tests when source code changes
6. **Integration with TDS**: Pull test data from Test Data Service
7. **Visual Studio integration**: Generate tests from context menu in VS

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Claude Code | Initial design document |

---

## References

1. **llt-skills-sdd.md** - LowLevelTests Skills Suite (test discovery, building, running)
2. **cpp-catch2-template.md** - Existing Catch2 template in dante plugin
3. **Fortnite Codebase Examples:**
   - `/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/` - Online Tests pattern
   - `/FortniteGame/Plugins/CommChannels/Tests/` - Basic Catch2 pattern
4. **Catch2 Documentation** - https://github.com/catchorg/Catch2
5. **Unreal Engine Build System** - TestModuleRules and TestTargetRules documentation
6. **Online Tests Internal Documentation.pdf** - Internal

---

**END OF DOCUMENT**
