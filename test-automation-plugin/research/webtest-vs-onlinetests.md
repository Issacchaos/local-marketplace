# Research Report: WebTests vs OnlineTests for LLT Template Examples

**Date:** 2026-02-17
**Author:** Claude Sonnet 4.5
**Purpose:** Evaluate replacing "OnlineTests" with "WebTests" as reference examples in dante plugin LLT test generation templates

---

## Executive Summary

**Recommendation: Use WebTests as the primary reference example** for basic Catch2 test patterns and fixtures. Retain OnlineTests references for domain-specific Online Services testing patterns only.

**Key Findings:**
- WebTests is significantly simpler (48 LOC Build.cs vs 84 LOC)
- WebTests uses pure Catch2 without domain-specific frameworks
- WebTests has cleaner fixture patterns suitable for general templates
- OnlineTests is complex due to Online Services infrastructure (authentication pipelines, helper systems)
- WebTests better demonstrates core LLT/Catch2 patterns developers need to learn

---

## 1. Codebase Locations

### WebTests Structure
```
/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/
├── WebTests.Build.cs          (48 lines - TestModuleRules)
├── WebTests.Target.cs         (15 lines - TestTargetRules)
├── README.md                  (23 lines - setup instructions)
└── Private/
    ├── WebLLTModule.cpp       (59 lines - module setup)
    ├── TestHttpDecode.cpp     (63 lines - 1 test case)
    ├── TestWebSockets.cpp     (236 lines - 4 test cases)
    └── TestHttp.cpp           (3357 lines - 83 test cases)
```

**Total:** ~3,715 lines across 4 test files
**Test Cases:** 88 test cases
**Avg Complexity:** 42 lines per test case

### OnlineTests Structure
```
/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/
├── OnlineTests.Build.cs       (84 lines - TestModuleRules with custom properties)
├── OnlineTests.Target.cs      (35 lines - TestTargetRules with platform config)
├── OnlineLLTModule.cpp        (82 lines - complex initialization)
└── Private/
    ├── ErrorsTest.cpp         (116 lines - 3 test cases)
    ├── OnlineTDSAuth.cpp      (445 lines - auth infrastructure)
    ├── TestErrorsAdapter.cpp  (68 lines)
    └── TestErrorsEOS.cpp      (58 lines)
    └── Tests/Commerce/        (Multiple test files)
        └── QueryEntitlementsTests.cpp (helper-based tests)
```

**Dependencies on:** OnlineTestsCore (shared test framework for all Online tests)
**Additional Complexity:**
- Test pipelines (`FTestPipeline`, `GetLoginPipeline()`)
- Helper system (`FQueryEntitlementsHelper`, `FAuthLogoutStep`)
- External auth infrastructure (TDS, EOS SDK integration)

---

## 2. Comparison Analysis

### A. Build Configuration Complexity

| Aspect | WebTests | OnlineTests |
|--------|----------|-------------|
| **Build.cs Lines** | 48 | 84 |
| **Base Class** | `TestModuleRules` | `TestModuleRules` (with custom properties) |
| **Dependencies** | 9 modules (Core, HTTP, WebSockets, etc.) | 16+ modules (OnlineSubsystem, OnlineServicesInterface, EOS SDK, etc.) |
| **Custom Properties** | None | `bRequireApplicationTick`, `bUseExternAuth`, `bRequirePlatformInit` |
| **Platform Specifics** | Standard metadata | Platform-specific definitions and includes |
| **TestMetadata Config** | Simple (TestName, platforms, report type) | Complex (tags, extra args, project file requirements) |

**Example - WebTests.Build.cs:**
```csharp
public class WebTests : TestModuleRules
{
    static WebTests()
    {
        if (InTestMode)
        {
            TestMetadata = new Metadata();
            TestMetadata.TestName = "Web";
            TestMetadata.TestShortName = "Web";
            TestMetadata.ReportType = "xml";
            TestMetadata.SupportedPlatforms.Add(UnrealTargetPlatform.Linux);
            // ... more platforms
        }
    }

    public WebTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "ApplicationCore",
                "Core",
                "EventLoop",
                "HTTP",
                "SSL",
                "HTTPServer",
                "WebSockets",
                "Json"
            });
    }
}
```

**Example - OnlineTests.Build.cs (more complex):**
```csharp
public class OnlineTests : TestModuleRules
{
    public virtual bool bRequireApplicationTick => false;
    public virtual bool bUseExternAuth => true;
    public virtual bool bRequirePlatformInit { get { return false; } }
    public virtual string PlatformFileName { get { return ""; } }

    public OnlineTests(ReadOnlyTargetRules Target) : base(Target)
    {
        bTreatAsEngineModule = false;
        CppStandard = CppStandardVersion.EngineDefault;

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "ApplicationCore",
                "Core",
                "CoreUObject",
                "Projects",
                "EngineSettings",
                "OnlineSubsystem",
                "OnlineServicesInterface",
                "OnlineServicesCommon",
                "OnlineServicesEOS",
                "OnlineServicesNull",
                "OnlineServicesOSSAdapter",
                "OnlineTestsCore",           // <- Domain-specific test framework
                "TestDataServiceHelpers",
                "EOSReservedHooks",
                "EOSSDK",
                "EOSShared",
                "SSL",
                "Json",
                "JsonUtilities"
            }
        );

        PublicDefinitions.Add(String.Format("ONLINETESTS_REQUIREAPPLICATIONTICK={0}", ...));
        // ... more custom definitions

        PrivateIncludePaths.AddRange(...);  // Platform-specific includes
    }
}
```

### B. Module Initialization Complexity

| Aspect | WebTests | OnlineTests |
|--------|----------|-------------|
| **Module Init** | Simple module loading (Sockets) | Complex platform init, config loading, service modules |
| **Global Setup** | `InitializeWebTests()` - 9 lines | `InitializeOnlineTests()` - 40+ lines with conditional compilation |
| **External Dependencies** | None | TDS auth, EOS SDK, platform-specific initialization |
| **Teardown** | Simple shutdown | Module unloading + cleanup callbacks |

**WebTests Module (Simple):**
```cpp
// WebLLTModule.cpp (59 lines total)
void InitializeWebTests()
{
    for (const FString& ModuleName : GetRequiredModules())
    {
        FModuleManager::LoadModulePtr<IModuleInterface>(*ModuleName);
    }
}

void CleanupWebTests()
{
    for (const FString& ModuleName : GetRequiredModules())
    {
        if (IModuleInterface* Module = FModuleManager::Get().GetModule(*ModuleName))
        {
            Module->ShutdownModule();
        }
    }
}

class WebTestsGlobalSetup
{
public:
    WebTestsGlobalSetup()
    {
        FTestDelegates::GetGlobalSetup().BindStatic(&InitializeWebTests);
        FTestDelegates::GetGlobalTeardown().BindStatic(&CleanupWebTests);
    }
} GWebTestsGlobalSetup;
```

**OnlineTests Module (Complex):**
```cpp
// OnlineLLTModule.cpp (82 lines total)
void InitializeOnlineTests()
{
#if ONLINETESTS_REQUIREPLATFORMINIT
    extern void PlatformInitializeTests();
    PlatformInitializeTests();
#endif
    SetProjectNameAndDirectory();
    InitAll(true, true);

#if ONLINETESTS_REQUIREAPPLICATIONTICK
    GPlatformApplication = FPlatformApplicationMisc::CreateApplication();
    check(GPlatformApplication);
    GPlatformApplicationTickHandle = FTSTicker::GetCoreTicker().AddTicker(TEXT("PlatformApplicationTick"), 0.0f,
        [](float DeltaSeconds)
        {
            GPlatformApplication->Tick(DeltaSeconds);
            return true;
        });
#endif

    FLogSuppressionInterface::Get().ProcessConfigAndCommandLine();
    OnlineTestBase::LoadServiceModules();  // <- Domain-specific service loading

    auto GlobalInitalizersPtr = GetGlobalInitalizers();
    // ... complex initialization logic

    FCoreDelegates::OnFEngineLoopInitComplete.Broadcast();
}
```

### C. Test Case Patterns

| Aspect | WebTests | OnlineTests |
|--------|----------|-------------|
| **Primary Macro** | `TEST_CASE`, `TEST_CASE_METHOD` | `ONLINE_TEST_CASE` (wraps Catch2 with online infrastructure) |
| **Fixture Pattern** | Standard Catch2 fixtures | Custom fixture base classes with pipelines |
| **Test Structure** | Direct assertions | Pipeline-based with helpers and steps |
| **Async Handling** | Manual tick loops | Builder pattern with `FTestPipeline` |
| **Setup Complexity** | Minimal (construct fixture) | Login pipelines, auth tokens, service initialization |

**WebTests Example (Simple Catch2 Fixture):**
```cpp
// TestWebSockets.cpp
class FWebSocketsModuleTestFixture
{
public:
    FWebSocketsModuleTestFixture()
        : WebServerIp(TEXT("127.0.0.1"))
        , WebServerWebSocketsPort(8000)
    {
        ParseSettingsFromCommandLine();

        // Init modules
        HttpModule = new FHttpModule();
        HttpModule->StartupModule();

        WebSocketsModule = new FWebSocketsModule();
        WebSocketsModule->StartupModule();
    }

    virtual ~FWebSocketsModuleTestFixture()
    {
        WebSocketsModule->ShutdownModule();
        delete WebSocketsModule;

        HttpModule->GetHttpManager().Tick(0.0);
        HttpModule->ShutdownModule();
        delete HttpModule;
    }

    const FString UrlWebSocketsTests() const {
        return FString::Format(TEXT("ws://{0}:{1}/webtests/websocketstests"),
                               { *WebServerIp, WebServerWebSocketsPort });
    }

    FString WebServerIp;
    uint32 WebServerWebSocketsPort;
    FWebSocketsModule* WebSocketsModule;
    FHttpModule* HttpModule;
};

TEST_CASE_METHOD(FWebSocketsModuleTestFixture,
                 "WebSockets can connect then send and receive message",
                 "[WebSockets]")
{
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(
        FString::Format(TEXT("{0}/echo/"), { *UrlWebSocketsTests() }));

    WebSocket->OnConnected().AddLambda([WebSocket](){
        WebSocket->Send(TEXT("hi websockets tests"));
    });

    WebSocket->OnMessage().AddLambda([WebSocket](const FString& MessageString) {
        CHECK(MessageString == TEXT("hi websockets tests"));
        WebSocket->Close();
    });

    WebSocket->Connect();
}
```

**OnlineTests Example (Complex Pipeline Pattern):**
```cpp
// QueryEntitlementsTests.cpp
COMMERCE_TEST_CASE("Verify that QueryEntitlements caches all entitlements",
                   COMMERCE_QUERYENTITLEMENTS_TAG)
{
    FAccountId AccountId;
    TOptional<uint32_t> ExpectedEntitlementsNum = 3;

    FAuthQueryExternalAuthToken::Params OpQueryExternalAuthToken;
    FCommerceQueryEntitlements::Params OpQueryEntitlementsParams;
    FQueryEntitlementsHelper::FHelperParams QueryEntitlementsHelperParams;
    // ... more param objects

    FTestPipeline& LoginPipeline = GetLoginPipeline({ AccountId });  // <- Framework-provided
    OpQueryExternalAuthToken.LocalAccountId = AccountId;
    QueryEntitlementsHelperParams.OpParams = &OpQueryEntitlementsParams;
    QueryEntitlementsHelperParams.OpParams->LocalAccountId = AccountId;

    TSharedPtr<FString> AccessToken = MakeShared<FString>();
    TSharedPtr<FString> EntitlementId = MakeShared<FString>();

    LoginPipeline
        .EmplaceStep<FAuthQueryExternalAuthTokenStep>(MoveTemp(OpQueryExternalAuthToken))
        .EmplaceStep<FGetEpicAdminClientAccessTokenStep>(DeploymentId, AccessToken)
        .EmplaceStep<FGrantEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId)
        .EmplaceStep<FQueryEntitlementsHelper>(MoveTemp(QueryEntitlementsHelperParams))
        .EmplaceStep<FGetEntitlementsHelper>(MoveTemp(GetEntitlementsHelperParams), ExpectedEntitlementsNum)
        .EmplaceStep<FDeleteEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId);

    RunToCompletion();  // <- Framework-provided async runner
}
```

### D. Suitability for Templates

| Criteria | WebTests | OnlineTests | Winner |
|----------|----------|-------------|---------|
| **Simplicity** | Pure Catch2, minimal boilerplate | Complex domain framework | WebTests |
| **Learnability** | Standard patterns, easy to understand | Requires learning Online Services concepts | WebTests |
| **Generalizability** | Applicable to any test domain | Specific to Online Services | WebTests |
| **Fixture Clarity** | Clear constructor/destructor pattern | Hidden in base classes and helpers | WebTests |
| **Async Pattern** | Explicit tick loops (teachable) | Abstracted pipelines (opaque) | WebTests |
| **Dependencies** | Minimal (9 modules) | Heavy (16+ modules + external services) | WebTests |
| **Maintainability** | Self-contained tests | Requires OnlineTestsCore infrastructure | WebTests |

---

## 3. Specific File Examples for Templates

### Template Type: Basic Catch2 Test

**Recommended Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestHttpDecode.cpp`

**Rationale:**
- Only 63 lines total
- Single test case demonstrating basic TEST_CASE macro
- Minimal dependencies
- Simple structure ideal for basic template

**Pattern Demonstrated:**
```cpp
#include "CoreMinimal.h"
#include <catch2/catch_test_macros.hpp>
#include "GenericPlatform/GenericPlatformHttp.h"

#define HTTP_SERVER_SUITE_TAGS "[HTTPServer]"
#define HTTP_SERVER_TEST_CASE(x, ...) TEST_CASE(x, HTTP_SERVER_SUITE_TAGS)

HTTP_SERVER_TEST_CASE("URL Decoding")
{
    // Simple assertions
    SECTION("Verify that FGenericPlatformHttp::UrlDecode() does not encounter out-of-bounds read")
    {
        FString encodedString = "test%";
        FGenericPlatformHttp::UrlDecode(encodedString);
        SUCCEED();
    }
}
```

### Template Type: Catch2 with Fixture

**Recommended Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`

**Rationale:**
- Clear fixture pattern (constructor/destructor setup/teardown)
- Standard TEST_CASE_METHOD usage
- 4 test cases demonstrating different fixture variations
- Module initialization pattern applicable to any UE module

**Pattern Demonstrated:**
```cpp
class FWebSocketsModuleTestFixture
{
public:
    FWebSocketsModuleTestFixture()
        : WebServerIp(TEXT("127.0.0.1"))
        , WebServerWebSocketsPort(8000)
    {
        // Setup
        HttpModule = new FHttpModule();
        HttpModule->StartupModule();

        WebSocketsModule = new FWebSocketsModule();
        WebSocketsModule->StartupModule();
    }

    virtual ~FWebSocketsModuleTestFixture()
    {
        // Teardown
        WebSocketsModule->ShutdownModule();
        delete WebSocketsModule;

        HttpModule->ShutdownModule();
        delete HttpModule;
    }

    // Helper methods for test cases
    const FString UrlBase() const { return TEXT("..."); }

    // Test state
    FString WebServerIp;
    FWebSocketsModule* WebSocketsModule;
    FHttpModule* HttpModule;
};

TEST_CASE_METHOD(FWebSocketsModuleTestFixture, "Test description", "[WebSockets]")
{
    // Test body has access to fixture members
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(UrlBase());
    // ...
}
```

### Template Type: Advanced Fixture (Async/Tick Loops)

**Recommended Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp` (FRunUntilQuitRequestedFixture)

**Rationale:**
- Demonstrates fixture inheritance
- Shows async test patterns with manual tick loops
- Clear control flow (not abstracted behind pipelines)

**Pattern Demonstrated:**
```cpp
class FRunUntilQuitRequestedFixture : public FWebSocketsModuleTestFixture
{
public:
    FRunUntilQuitRequestedFixture() { }

    ~FRunUntilQuitRequestedFixture()
    {
        RunUntilQuitRequested();  // Ensure cleanup
    }

    void SimulateEngineTick()
    {
        FTSBackgroundableTicker::GetCoreTicker().Tick(TickFrequency);
        FTSTicker::GetCoreTicker().Tick(TickFrequency);
        FPlatformProcess::Sleep(TickFrequency);
        HttpModule->GetHttpManager().Tick(TickFrequency);
    }

    void RunUntilQuitRequested()
    {
        while (!bQuitRequested)
        {
            SimulateEngineTick();
        }
    }

    float TickFrequency = 1.0f / 60;
    bool bQuitRequested = false;
};

TEST_CASE_METHOD(FRunUntilQuitRequestedFixture,
                 "WebSockets can connect then send and receive message",
                 "[WebSockets]")
{
    // Setup async callbacks
    WebSocket->OnConnected().AddLambda([this, WebSocket](){
        WebSocket->Send(TEXT("message"));
    });

    WebSocket->OnMessage().AddLambda([this, WebSocket](const FString& MessageString) {
        CHECK(MessageString == TEXT("message"));
        bQuitRequested = true;  // Signal completion
    });

    WebSocket->Connect();  // Async operation runs in tick loop
}
```

### Template Type: Module Setup/Initialization

**Recommended Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/WebLLTModule.cpp`

**Rationale:**
- Clean, minimal module initialization pattern
- Shows proper use of FTestDelegates for global setup/teardown
- No platform-specific or domain-specific complexity
- Directly applicable to any test module

**Pattern Demonstrated:**
```cpp
#include "TestRunner.h"
#include "TestCommon/Initialization.h"
#include <catch2/catch_test_macros.hpp>

GROUP_AFTER_GLOBAL(Catch::DefaultGroup)
{
    CleanupLocalization();
}

namespace UE::WebTests
{

TArray<FString> GetRequiredModules()
{
    static TArray<FString> Modules({
        FString(TEXT("Sockets"))
    });
    return Modules;
}

void InitializeWebTests()
{
    for (const FString& ModuleName : GetRequiredModules())
    {
        FModuleManager::LoadModulePtr<IModuleInterface>(*ModuleName);
    }
}

void CleanupWebTests()
{
    for (const FString& ModuleName : GetRequiredModules())
    {
        if (IModuleInterface* Module = FModuleManager::Get().GetModule(*ModuleName))
        {
            Module->ShutdownModule();
        }
    }
}

class WebTestsGlobalSetup
{
public:
    WebTestsGlobalSetup()
    {
        FTestDelegates::GetGlobalSetup().BindStatic(&InitializeWebTests);
        FTestDelegates::GetGlobalTeardown().BindStatic(&CleanupWebTests);
    }
} GWebTestsGlobalSetup;

}  // namespace UE::WebTests
```

---

## 4. When to Use OnlineTests

**Keep OnlineTests references for domain-specific patterns:**

1. **Online Services Test Structure**: When generating tests specifically for Online Services interfaces (Auth, Commerce, Sessions, etc.)
2. **Pipeline-Based Tests**: When demonstrating the helper/pipeline pattern used by Online ecosystem
3. **Authentication Infrastructure**: When showing how to integrate with TDS/EOS authentication
4. **Advanced Test Orchestration**: Multi-step async operations requiring helper abstraction

**Recommended OnlineTests Examples (Domain-Specific Only):**
- `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/Private/ErrorsTest.cpp` - Simple Online error tests (116 lines, 3 test cases)
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Private/Tests/Commerce/QueryOffersTests.cpp` - Pipeline pattern example

---

## 5. Recommendation: Hybrid Approach

### Primary Templates: Use WebTests

**For the following template categories, use WebTests as the reference:**

1. **Basic Catch2 Test Template** (`catch2-basic`)
   - Reference: `TestHttpDecode.cpp`
   - Pattern: Simple TEST_CASE with basic assertions
   - No fixture required

2. **Catch2 Fixture Template** (`catch2-fixture`)
   - Reference: `TestWebSockets.cpp` (FWebSocketsModuleTestFixture)
   - Pattern: TEST_CASE_METHOD with constructor/destructor setup
   - Module initialization example

3. **Async Fixture Template** (`catch2-fixture-async`)
   - Reference: `TestWebSockets.cpp` (FRunUntilQuitRequestedFixture)
   - Pattern: Fixture with tick loop for async operations
   - Demonstrates fixture inheritance

4. **Module Initialization Template** (`llt-module-init`)
   - Reference: `WebLLTModule.cpp`
   - Pattern: FTestDelegates global setup/teardown
   - Simple module loading

5. **Build.cs Template** (`test-module-build-cs`)
   - Reference: `WebTests.Build.cs`
   - Pattern: TestModuleRules with minimal configuration
   - Clear dependency list

### Domain-Specific Templates: Use OnlineTests

**Only for Online Services-specific test generation:**

6. **Online Services Test Template** (`online-services-test`)
   - Reference: OnlineTests examples
   - Pattern: ONLINE_TEST_CASE with pipelines
   - Helper system integration

---

## 6. Changes Required in Spec/Tasks/Templates

### A. Documentation Changes

**File:** `/Users/stephen.ma/dante_plugin/docs/design/llt-skills-sdd.md`

**Changes:**
1. Section 2.3 "Test Framework Variants" - Update example:
   ```markdown
   #### A. Explicit Test Targets
   - Self-contained test executables (e.g., `FoundationTests`, `WebTests`)
   ```

2. Section 2.4 "Test Execution Models" - Replace OnlineTests examples:
   ```markdown
   | Model | Command | Use Case |
   |-------|---------|----------|
   | **Direct Execution** | `.\WebTests.exe [tags] --wait --debug --log` | Local development |
   | **BuildCookRun** | `.\RunUAT.bat BuildCookRun -Project=WebTests -Stage -SkipCook` | Staging |
   ```

3. Section 4.2 "Skill 2: llt-build" - Update examples:
   ```markdown
   - `--target` (required): Test target name (e.g., `FoundationTests`, `WebTests`)
   ```

4. Section 5.3 "Skill 3: llt-run" - Update Gauntlet example:
   ```markdown
   .\RunUAT.bat RunLowLevelTests \
       -testapp=WebTests \
       -platform=Win64 \
       -tags="[HTTP]"
   ```

5. Add new section documenting WebTests as reference implementation:
   ```markdown
   ### 2.6 Reference Test Implementations

   #### WebTests (Recommended for General Patterns)
   - **Location:** `Engine/Source/Programs/WebTests/`
   - **Purpose:** Clean Catch2 examples for HTTP/WebSocket testing
   - **Use for:** Basic test templates, fixture patterns, module initialization
   - **Key Files:**
     - `TestHttpDecode.cpp` - Basic TEST_CASE pattern
     - `TestWebSockets.cpp` - Fixture patterns and async tests
     - `WebLLTModule.cpp` - Module initialization pattern
     - `WebTests.Build.cs` - Minimal TestModuleRules configuration

   #### OnlineTests (Domain-Specific)
   - **Location:** `Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/`
   - **Purpose:** Online Services-specific test patterns
   - **Use for:** Online Services plugin tests only
   - **Dependencies:** OnlineTestsCore, EOS SDK, external auth
   ```

**File:** `/Users/stephen.ma/dante_plugin/docs/design/llt-test-generation-sdd.md`

**Changes:**
1. Section 3.2 "Reference Implementation Patterns" - Add WebTests:
   ```markdown
   ### C. WebTests Pattern (Simple Catch2)

   **Location:** `Engine/Source/Programs/WebTests/`
   **Use Case:** General-purpose LLT with minimal dependencies

   **Build.cs Example:**
   ```csharp
   // WebTests.Build.cs
   public class WebTests : TestModuleRules
   {
       static WebTests()
       {
           if (InTestMode)
           {
               TestMetadata = new Metadata();
               TestMetadata.TestName = "Web";
               TestMetadata.ReportType = "xml";
               TestMetadata.SupportedPlatforms.Add(UnrealTargetPlatform.Win64);
           }
       }

       public WebTests(ReadOnlyTargetRules Target) : base(Target)
       {
           PrivateDependencyModuleNames.AddRange(
               new string[] {
                   "Core",
                   "HTTP",
                   "WebSockets",
                   "Json"
               });
       }
   }
   ```

   **Pattern characteristics:**
   - Inherits from TestModuleRules
   - Simple TestMetadata configuration
   - Minimal dependencies (no test framework infrastructure)
   - No custom properties or platform-specific logic
   ```

2. Section 3.3 "Template Variables" - Update examples:
   ```markdown
   | Variable | Description | Example Values |
   |----------|-------------|----------------|
   | `{{TEST_TARGET_NAME}}` | Test target name | `WebTests`, `CommChannelsTests` |
   | `{{DEPENDENCY_MODULES}}` | Comma-separated module list | `"Core", "HTTP", "WebSockets"` |
   ```

3. Section 5.2 "Template File Mapping" - Add WebTests references:
   ```markdown
   | Template Type | Source Reference | Output |
   |---------------|------------------|--------|
   | `catch2-basic` | `WebTests/TestHttpDecode.cpp` | `Private/Test{{MODULE}}.cpp` |
   | `catch2-fixture` | `WebTests/TestWebSockets.cpp` | `Private/Test{{MODULE}}.cpp` |
   | `llt-module-init` | `WebTests/WebLLTModule.cpp` | `Private/{{MODULE}}LLTModule.cpp` |
   | `test-module-build-cs` | `WebTests.Build.cs` | `{{MODULE}}Tests.Build.cs` |
   | `online-services-test` | `OnlineTests/QueryOffersTests.cpp` | `Private/Tests/{{TEST}}.cpp` |
   ```

4. Section 5.4 "Dependency Configuration" - Update algorithm:
   ```python
   def resolve_test_dependencies(module_under_test: str, test_type: str):
       """
       Resolve dependencies for test module based on test type.
       """
       # Start with test framework
       if test_type == "online-services-test":
           dependencies = ["OnlineTestsCore"]
       else:
           dependencies = []  # Catch2 pulled in via Engine

       # Add module under test
       dependencies.append(module_under_test)

       # Add core dependencies
       dependencies.extend(["Core", "ApplicationCore"])

       # Add domain-specific dependencies
       if test_type == "online-services-test":
           dependencies.extend([
               "OnlineServicesInterface",
               "OnlineServicesCommon",
               "CoreUObject",
               "Projects"
           ])

       return dependencies
   ```

### B. Template File Changes

**New Template Files to Create:**

1. **`templates/catch2-basic-webtest.cpp.j2`**
   - Based on `TestHttpDecode.cpp` pattern
   - Simple TEST_CASE with custom tag macro
   - Minimal includes

2. **`templates/catch2-fixture-webtest.cpp.j2`**
   - Based on `TestWebSockets.cpp` FWebSocketsModuleTestFixture
   - Constructor/destructor pattern
   - TEST_CASE_METHOD usage

3. **`templates/catch2-fixture-async-webtest.cpp.j2`**
   - Based on `TestWebSockets.cpp` FRunUntilQuitRequestedFixture
   - Tick loop pattern for async tests
   - Fixture inheritance example

4. **`templates/llt-module-webtest.cpp.j2`**
   - Based on `WebLLTModule.cpp`
   - FTestDelegates setup
   - Simple module loading pattern

5. **`templates/test-module-build-webtest.cs.j2`**
   - Based on `WebTests.Build.cs`
   - Minimal TestModuleRules pattern
   - Simple TestMetadata configuration

**Existing Template Files to Update:**

1. **`templates/test-module-build-online.cs.j2`**
   - Rename to clarify it's Online Services-specific
   - Add comment: `// Use this template only for Online Services plugin tests`

2. **`templates/online-services-test.cpp.j2`**
   - Keep as-is (already domain-specific)
   - Add comment referencing OnlineTestsCore dependency

### C. Code Changes

**File:** `scripts/llt_test_generator.py` (or equivalent)

**Changes:**
```python
# Reference implementations
REFERENCE_IMPLS = {
    'catch2-basic': {
        'file': 'Engine/Source/Programs/WebTests/Private/TestHttpDecode.cpp',
        'pattern': 'simple_test_case'
    },
    'catch2-fixture': {
        'file': 'Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp',
        'pattern': 'fixture_test_case'
    },
    'catch2-fixture-async': {
        'file': 'Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp',
        'pattern': 'async_fixture_test_case'
    },
    'llt-module-init': {
        'file': 'Engine/Source/Programs/WebTests/Private/WebLLTModule.cpp',
        'pattern': 'module_initialization'
    },
    'test-module-build-cs': {
        'file': 'Engine/Source/Programs/WebTests/WebTests.Build.cs',
        'pattern': 'test_module_rules'
    },
    'online-services-test': {
        'file': 'Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/Private/ErrorsTest.cpp',
        'pattern': 'online_test_case',
        'requires': ['OnlineTestsCore']
    }
}

def get_template_dependencies(test_type: str) -> List[str]:
    """Return required dependencies based on test type."""
    if test_type == 'online-services-test':
        return [
            'OnlineTestsCore',
            'OnlineServicesInterface',
            'OnlineServicesCommon',
            'CoreUObject'
        ]
    else:
        # WebTests-style minimal dependencies
        return ['Core', 'ApplicationCore']
```

---

## 7. Trade-offs and Risks

### Advantages of WebTests

1. **Lower Learning Curve**: Developers unfamiliar with Online Services can still understand test structure
2. **Fewer Dependencies**: Reduces build time and complexity for non-Online tests
3. **Better Generalization**: Patterns apply to any UE module, not just Online Services
4. **Clearer Examples**: No abstraction layers hiding Catch2 fundamentals
5. **Maintenance**: Self-contained tests don't break when OnlineTestsCore changes

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Developers expect Online-specific patterns** | Confusion for Online Services plugin developers | Keep OnlineTests reference for domain-specific template, document when to use each |
| **WebTests less "real-world"** | Simpler patterns may not scale to complex scenarios | Document WebTests for learning, OnlineTests for production patterns |
| **Duplication of reference examples** | Maintenance burden of tracking two reference sets | Use WebTests as primary, OnlineTests only for domain-specific needs |
| **Template fragmentation** | Too many template types confuse users | Clearly document template decision tree in SDD |

### Decision Tree for Template Selection

```
Is this an Online Services plugin test?
├─ YES → Use OnlineTests reference
│         - online-services-test template
│         - OnlineTestsCore dependency
│         - Pipeline/helper patterns
│
└─ NO → Use WebTests reference
          ├─ Need fixture?
          │  ├─ YES → catch2-fixture-webtest template
          │  │         - FWebSocketsModuleTestFixture pattern
          │  │         - Constructor/destructor setup
          │  │
          │  └─ NO → catch2-basic-webtest template
          │            - Simple TEST_CASE pattern
          │            - Minimal boilerplate
          │
          └─ Need async testing?
             └─ YES → catch2-fixture-async-webtest template
                      - FRunUntilQuitRequestedFixture pattern
                      - Tick loop for async operations
```

---

## 8. Implementation Checklist

### Phase 1: Documentation Updates
- [ ] Update llt-skills-sdd.md Section 2.3 (examples)
- [ ] Update llt-skills-sdd.md Section 2.4 (execution models)
- [ ] Update llt-skills-sdd.md Section 4.2 (build skill)
- [ ] Update llt-skills-sdd.md Section 5.3 (run skill)
- [ ] Add llt-skills-sdd.md Section 2.6 (reference implementations)
- [ ] Update llt-test-generation-sdd.md Section 3.2 (add WebTests pattern)
- [ ] Update llt-test-generation-sdd.md Section 3.3 (template variables)
- [ ] Update llt-test-generation-sdd.md Section 5.2 (template mapping)
- [ ] Update llt-test-generation-sdd.md Section 5.4 (dependency resolution)

### Phase 2: Template Creation
- [ ] Create `templates/catch2-basic-webtest.cpp.j2`
- [ ] Create `templates/catch2-fixture-webtest.cpp.j2`
- [ ] Create `templates/catch2-fixture-async-webtest.cpp.j2`
- [ ] Create `templates/llt-module-webtest.cpp.j2`
- [ ] Create `templates/test-module-build-webtest.cs.j2`
- [ ] Rename `templates/test-module-build-online.cs.j2` (add domain-specific comment)

### Phase 3: Code Updates
- [ ] Update `REFERENCE_IMPLS` dict in test generator
- [ ] Update `get_template_dependencies()` function
- [ ] Add template decision logic (select WebTests vs OnlineTests)
- [ ] Update CLI help text to document template choices
- [ ] Add validation to warn when OnlineTestsCore is used for non-Online tests

### Phase 4: Testing
- [ ] Generate test using catch2-basic-webtest template, verify it compiles
- [ ] Generate test using catch2-fixture-webtest template, verify it compiles
- [ ] Generate test using online-services-test template, verify it still works
- [ ] Compare generated code against reference implementations
- [ ] Run generated tests to ensure they execute correctly

### Phase 5: Migration
- [ ] Update existing task examples in SDDs to use WebTests
- [ ] Update CLI examples in README to default to WebTests
- [ ] Add migration guide for existing OnlineTests-based workflows
- [ ] Document when to use OnlineTests (Online Services plugins only)

---

## 9. Conclusion

**WebTests is the clear winner for general-purpose LLT test generation templates** due to:

1. **Simplicity**: 48-line Build.cs vs 84-line with custom properties
2. **Clarity**: Direct Catch2 patterns without abstraction layers
3. **Generalizability**: Applicable to any UE module, not just Online Services
4. **Maintainability**: Self-contained tests with minimal external dependencies
5. **Learnability**: Clean examples that teach core LLT/Catch2 concepts

**OnlineTests should be retained** only for domain-specific Online Services plugin test generation, where the pipeline/helper infrastructure is necessary and expected.

This hybrid approach provides:
- **Best-in-class examples** for general use (WebTests)
- **Domain expertise** for specialized needs (OnlineTests)
- **Clear guidance** on when to use each reference

**Next Steps:**
1. Implement Phase 1 (documentation updates) first to establish new reference patterns
2. Create Phase 2 (new templates) using WebTests as source
3. Phase 3-5 (code updates, testing, migration) can proceed incrementally

---

## Appendix: File Paths Reference

### WebTests Files
- Build config: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/WebTests.Build.cs`
- Target config: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/WebTests.Target.cs`
- Module init: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/WebLLTModule.cpp`
- Basic test: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestHttpDecode.cpp`
- Fixture test: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`
- Advanced test: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestHttp.cpp`

### OnlineTests Files
- Build config: `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/OnlineTests.Build.cs`
- Target config: `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/OnlineTests.Target.cs`
- Module init: `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/OnlineLLTModule.cpp`
- Simple test: `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/Private/ErrorsTest.cpp`
- Pipeline test: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Private/Tests/Commerce/QueryOffersTests.cpp`

### Design Documents
- LLT Skills SDD: `/Users/stephen.ma/dante_plugin/docs/design/llt-skills-sdd.md`
- LLT Test Generation SDD: `/Users/stephen.ma/dante_plugin/docs/design/llt-test-generation-sdd.md`
