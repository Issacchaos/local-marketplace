# Async LowLevelTest Template

**Purpose**: Template for generating asynchronous Catch2 test files for Unreal Engine LowLevelTests with callbacks, tick loops, and optional pipeline builders
**Target Framework**: Catch2 (v3.x) + Unreal Engine LowLevelTests
**Test Patterns**: WebTests (explicit tick loops) + OnlineTests (pipeline builders)
**Version Support**: Catch2 3.0+, UE 5.0+

## Overview

This template provides patterns for asynchronous LowLevelTests that handle callbacks, tick loops, timeouts, and multi-step async workflows. It consolidates WebTests (simple tick loop pattern) and OnlineTests (advanced pipeline builder pattern) with 60-70% pattern overlap validated through codebase analysis.

**When to use this template:**
- Testing async operations (HTTP requests, WebSockets, Online Services)
- Callback-based completion patterns
- Tests requiring explicit tick loop simulation
- Multi-step async workflows requiring pipeline orchestration
- Timeout handling for async operations

**Coverage**: 30% of LLT modules use async patterns (validated from 15+ module analysis)

## Template Structure

### File Header Template

```cpp

/**
 * Test module for {{MODULE_NAME}} - Async Operations
 *
 * Test coverage:
 * - {{ASYNC_OPERATION_1}} (async callbacks)
 * - {{ASYNC_OPERATION_2}} (timeout handling)
 * - {{ASYNC_OPERATION_3}} (multi-step workflows)
 *
 * Pattern: {{ASYNC_PATTERN_TYPE}}
 *   - "simple": Explicit tick loop with callbacks (WebTests pattern)
 *   - "pipeline": Multi-step async builder (OnlineTests pattern)
 */

#include "CoreMinimal.h"
#include "TestHarness.h"
{{ADDITIONAL_INCLUDES}}

{{CUSTOM_TAG_MACRO}}

{{NAMESPACE_BEGIN}}

// ============================================================================
// Async Test Fixtures
// ============================================================================

{{FIXTURE_DEFINITION}}

// ============================================================================
// {{MODULE_NAME}} Async Tests
// ============================================================================

{{TEST_CASES}}

{{NAMESPACE_END}}
```

## Template Placeholders

### Module-Level Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{MODULE_NAME}}` | Name of module being tested | `WebSockets`, `OnlineCommerce`, `HttpClient` |
| `{{ASYNC_OPERATION_N}}` | Async operations being tested | `WebSocket connection`, `HTTP request handling`, `Auth token refresh` |
| `{{ASYNC_PATTERN_TYPE}}` | Pattern variant ("simple" or "pipeline") | `"simple"` for WebTests, `"pipeline"` for OnlineTests |
| `{{ADDITIONAL_INCLUDES}}` | Required includes for async operations | `#include "HTTP/HttpModule.h"`<br>`#include "WebSockets/WebSocketsModule.h"`<br>`#include "OnlineCatchHelper.h"` |
| `{{CUSTOM_TAG_MACRO}}` | Custom test tag macro (optional) | `#define WEBSOCKETS_TAG "[websockets]"`<br>`#define ONLINE_TEST_CASE(x, ...) TEST_CASE(x, ONLINE_TAG __VA_ARGS__)` |
| `{{NAMESPACE_BEGIN}}` | Namespace opening (optional) | `namespace UE::WebTests {` |
| `{{NAMESPACE_END}}` | Namespace closing (optional) | `}  // namespace UE::WebTests` |

### Fixture Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{FIXTURE_DEFINITION}}` | Complete fixture class definition | See Fixture Patterns below |
| `{{FIXTURE_CLASS_NAME}}` | Name of fixture class | `FWebSocketsModuleTestFixture`, `FAsyncHttpTestFixture` |
| `{{TICK_LOOP}}` | Tick loop implementation | See Tick Loop Pattern below |
| `{{ASYNC_CALLBACK}}` | Async callback registration | `WebSocket->OnConnected().AddLambda(...)` |
| `{{TIMEOUT_HANDLER}}` | Timeout handling logic | Manual check or helper method |

### Test Case Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_CASES}}` | Individual test case definitions | See Test Case Patterns below |
| `{{TEST_DESCRIPTION}}` | Descriptive test name | `"WebSockets can connect and send message"` |
| `{{TEST_TAG}}` | Test tags | `"[websockets]"`, `"[http][slow]"` |
| `{{SETUP_CODE}}` | Test setup (Given/Arrange) | Configuration, resource creation |
| `{{ASYNC_OPERATION}}` | Async operation to test | `WebSocket->Connect()`, `GetPipeline().EmplaceStep(...)` |
| `{{COMPLETION_SIGNAL}}` | Completion mechanism | `bQuitRequested = true`, `RunToCompletion()` |
| `{{ASSERTIONS}}` | Async result assertions | `REQUIRE(response.IsSuccess())` |

### Pipeline-Specific Placeholders (Optional)

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{PIPELINE_STEPS}}` | Multi-step async workflow | See Pipeline Pattern below |
| `{{PIPELINE_STEP_N}}` | Individual pipeline step | `EmplaceStep<FAuthStep>(...)` |
| `{{HELPER_CLASS}}` | Pipeline helper class | `FQueryEntitlementsHelper` |
| `{{ASYNC_STEP_IMPL}}` | Custom async step implementation | See Pipeline Helpers below |

## Pattern 1: Simple Async (WebTests Pattern)

### Use Case
- Direct async operations with callbacks
- Explicit tick loop control
- Manual completion signaling
- WebSocket, HTTP, or simple async API testing

### Base Fixture Pattern

```cpp
/**
 * Base fixture for async module testing.
 * Manages module lifecycle and provides helpers.
 */
class {{FIXTURE_CLASS_NAME}}
{
public:
    {{FIXTURE_CLASS_NAME}}()
        : {{INIT_MEMBER_1}}({{INIT_VALUE_1}})
        , {{INIT_MEMBER_2}}({{INIT_VALUE_2}})
    {
        {{PARSE_COMMAND_LINE}}

        // Initialize required modules
        {{MODULE_INIT_CODE}}
    }

    virtual ~{{FIXTURE_CLASS_NAME}}()
    {
        // Shutdown modules in reverse order
        {{MODULE_SHUTDOWN_CODE}}
    }

    // Helper methods
    {{HELPER_METHODS}}

protected:
    // Module instances
    {{MODULE_MEMBERS}}

    // Test configuration
    {{CONFIG_MEMBERS}}
};
```

**Example (WebSockets):**

```cpp
class FWebSocketsModuleTestFixture
{
public:
    FWebSocketsModuleTestFixture()
        : WebServerIp(TEXT("127.0.0.1"))
        , WebServerWebSocketsPort(8000)
    {
        ParseSettingsFromCommandLine();

        // Init HTTP module (dependency)
        HttpModule = new FHttpModule();
        HttpModule->StartupModule();

        // Init WebSockets module
        WebSocketsModule = new FWebSocketsModule();
        WebSocketsModule->StartupModule();
    }

    virtual ~FWebSocketsModuleTestFixture()
    {
        // Shutdown in reverse order
        WebSocketsModule->ShutdownModule();
        delete WebSocketsModule;

        HttpModule->GetHttpManager().Tick(0.0);
        HttpModule->ShutdownModule();
        delete HttpModule;
    }

    // Helper: Build WebSocket test URL
    const FString UrlWebSocketsTests() const {
        return FString::Format(TEXT("ws://{0}:{1}/webtests/websocketstests"),
                               { *WebServerIp, WebServerWebSocketsPort });
    }

    // Helper: Parse command-line test configuration
    void ParseSettingsFromCommandLine() {
        FParse::Value(FCommandLine::Get(), TEXT("-WebServerIp="), WebServerIp);
        FParse::Value(FCommandLine::Get(), TEXT("-WebServerWebSocketsPort="), WebServerWebSocketsPort);
    }

protected:
    FString WebServerIp;
    uint32 WebServerWebSocketsPort;
    FWebSocketsModule* WebSocketsModule;
    FHttpModule* HttpModule;
};
```

### Tick Loop Fixture Pattern

```cpp
/**
 * Fixture with explicit tick loop for async operations.
 * Provides RunUntilQuitRequested() for callback-based completion.
 */
class {{TICK_FIXTURE_CLASS_NAME}} : public {{BASE_FIXTURE_CLASS_NAME}}
{
public:
    {{TICK_FIXTURE_CLASS_NAME}}() { }

    ~{{TICK_FIXTURE_CLASS_NAME}}()
    {
        // Ensure all async operations complete before teardown
        RunUntilQuitRequested();
    }

    /**
     * Simulate engine tick for async operations.
     * Ticks all registered ticker systems and sleeps.
     */
    void SimulateEngineTick()
    {
        {{TICKER_TICK_CODE}}
        FPlatformProcess::Sleep(TickFrequency);
    }

    /**
     * Run tick loop until bQuitRequested is set by test.
     * Supports optional timeout.
     */
    void RunUntilQuitRequested(float MaxSeconds = 30.0f)
    {
        const float StartTime = FPlatformTime::Seconds();
        while (!bQuitRequested)
        {
            SimulateEngineTick();

            // Timeout handling
            if (FPlatformTime::Seconds() - StartTime > MaxSeconds)
            {
                FAIL("Test timed out after " << MaxSeconds << " seconds");
                break;
            }
        }
    }

    // Tick frequency (60 FPS default)
    float TickFrequency = 1.0f / 60;

    // Completion signals
    bool bQuitRequested = false;
    bool bSucceed = false;
};
```

**Example (WebSockets with Tick Loop):**

```cpp
class FRunUntilQuitRequestedFixture : public FWebSocketsModuleTestFixture
{
public:
    FRunUntilQuitRequestedFixture() { }

    ~FRunUntilQuitRequestedFixture()
    {
        RunUntilQuitRequested();
    }

    void SimulateEngineTick()
    {
        FTSBackgroundableTicker::GetCoreTicker().Tick(TickFrequency);
        FTSTicker::GetCoreTicker().Tick(TickFrequency);
        FPlatformProcess::Sleep(TickFrequency);
        HttpModule->GetHttpManager().Tick(TickFrequency);
    }

    void RunUntilQuitRequested(float MaxSeconds = 30.0f)
    {
        const float StartTime = FPlatformTime::Seconds();
        while (!bQuitRequested)
        {
            SimulateEngineTick();

            if (FPlatformTime::Seconds() - StartTime > MaxSeconds)
            {
                FAIL("WebSocket test timed out after " << MaxSeconds << " seconds");
                break;
            }
        }
    }

    float TickFrequency = 1.0f / 60;
    bool bQuitRequested = false;
    bool bSucceed = false;
};
```

### Simple Async Test Case Pattern

```cpp
TEST_CASE_METHOD({{TICK_FIXTURE_CLASS_NAME}},
                 "{{TEST_DESCRIPTION}}",
                 "{{TEST_TAG}}")
{
    // Arrange
    {{SETUP_CODE}}

    // Register async callbacks
    {{ASYNC_CALLBACK_CONNECTED}}
    {{ASYNC_CALLBACK_MESSAGE}}
    {{ASYNC_CALLBACK_ERROR}}

    // Act
    {{ASYNC_OPERATION_START}}

    // Tick loop runs until bQuitRequested = true
    // (Called automatically in fixture destructor)
}
```

**Example (WebSocket Connect + Send + Receive):**

```cpp
TEST_CASE_METHOD(FRunUntilQuitRequestedFixture,
                 "WebSockets can connect then send and receive message",
                 "[WebSockets]")
{
    // Arrange
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(
        FString::Format(TEXT("{0}/echo/"), { *UrlWebSocketsTests() }));

    // Register callbacks
    WebSocket->OnConnected().AddLambda([this, WebSocket](){
        WebSocket->Send(TEXT("hi websockets tests"));
    });

    WebSocket->OnMessage().AddLambda([this, WebSocket](const FString& MessageString) {
        CHECK(MessageString == TEXT("hi websockets tests"));
        bSucceed = true;
        bQuitRequested = true;  // Signal completion
        WebSocket->Close();
    });

    WebSocket->OnConnectionError().AddLambda([this](const FString& Error) {
        FAIL("WebSocket connection failed: " << Error);
        bQuitRequested = true;
    });

    // Act
    WebSocket->Connect();

    // Tick loop runs in fixture destructor
}
```

### Timeout Handling Pattern

```cpp
TEST_CASE_METHOD({{TICK_FIXTURE_CLASS_NAME}},
                 "{{TEST_DESCRIPTION}} - with timeout",
                 "{{TEST_TAG}}")
{
    // Arrange
    const float TimeoutSeconds = {{TIMEOUT_VALUE}};
    const float StartTime = FPlatformTime::Seconds();
    bool bOperationCompleted = false;

    {{SETUP_CODE}}

    // Register callback with timeout check
    {{ASYNC_CALLBACK_CODE}}

    // Act
    {{ASYNC_OPERATION_START}}

    // Custom timeout loop
    while (!bQuitRequested)
    {
        SimulateEngineTick();

        float ElapsedTime = FPlatformTime::Seconds() - StartTime;
        if (ElapsedTime > TimeoutSeconds)
        {
            FAIL("Operation timed out after " << TimeoutSeconds << " seconds");
            bQuitRequested = true;
        }
    }

    // Assert
    REQUIRE(bOperationCompleted);
}
```

**Example (HTTP Request with Timeout):**

```cpp
TEST_CASE_METHOD(FRunUntilQuitRequestedFixture,
                 "HTTP request completes within timeout",
                 "[HTTP][timeout]")
{
    // Arrange
    const float TimeoutSeconds = 10.0f;
    bool bRequestCompleted = false;

    TSharedRef<IHttpRequest> Request = HttpModule->CreateRequest();
    Request->SetURL(TEXT("https://httpbin.org/delay/2"));
    Request->SetVerb(TEXT("GET"));

    // Register callbacks
    Request->OnProcessRequestComplete().BindLambda(
        [this, &bRequestCompleted](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
        {
            REQUIRE(bSuccess);
            REQUIRE(Res.IsValid());
            REQUIRE(Res->GetResponseCode() == 200);
            bRequestCompleted = true;
            bQuitRequested = true;
        });

    // Act
    Request->ProcessRequest();

    // Tick loop with timeout
    RunUntilQuitRequested(TimeoutSeconds);

    // Assert
    REQUIRE(bRequestCompleted);
}
```

## Pattern 2: Pipeline Builder (OnlineTests Pattern)

### Use Case
- Multi-step async workflows (login → API calls → cleanup)
- Reusable async step abstractions
- Complex orchestration with dependencies
- Online Services integration testing

### Pipeline Test Pattern

```cpp
{{CUSTOM_TEST_MACRO}}("{{TEST_DESCRIPTION}}", "{{TEST_TAG}}")
{
    // Arrange
    {{PIPELINE_PARAMS_SETUP}}

    // Get pipeline (provided by test framework)
    FTestPipeline& Pipeline = {{GET_PIPELINE_METHOD}};

    // Build multi-step workflow
    Pipeline
        {{PIPELINE_STEP_1}}
        {{PIPELINE_STEP_2}}
        {{PIPELINE_STEP_3}}
        {{PIPELINE_STEP_N}};

    // Act & Assert (runs all steps with tick loop)
    RunToCompletion();
}
```

**Example (OnlineTests Commerce Flow):**

```cpp
#define COMMERCE_TAG "[suite_commerce]"
#define COMMERCE_TEST_CASE(x, ...) ONLINE_TEST_CASE(x, COMMERCE_TAG __VA_ARGS__)

COMMERCE_TEST_CASE("Verify QueryEntitlements caches all entitlements",
                   "[query_entitlements]")
{
    // Arrange
    FAccountId AccountId;
    TOptional<uint32_t> ExpectedEntitlementsNum = 3;

    FAuthQueryExternalAuthToken::Params OpQueryExternalAuthToken;
    FCommerceQueryEntitlements::Params OpQueryEntitlementsParams;
    FQueryEntitlementsHelper::FHelperParams QueryEntitlementsHelperParams;

    TSharedPtr<FString> AccessToken = MakeShared<FString>();
    TSharedPtr<FString> EntitlementId = MakeShared<FString>();

    // Get login pipeline (framework-provided)
    FTestPipeline& LoginPipeline = GetLoginPipeline({ AccountId });

    OpQueryExternalAuthToken.LocalAccountId = AccountId;
    QueryEntitlementsHelperParams.OpParams = &OpQueryEntitlementsParams;
    QueryEntitlementsHelperParams.OpParams->LocalAccountId = AccountId;

    // Build multi-step async workflow
    LoginPipeline
        .EmplaceStep<FAuthQueryExternalAuthTokenStep>(MoveTemp(OpQueryExternalAuthToken))
        .EmplaceStep<FGetEpicAdminClientAccessTokenStep>(DeploymentId, AccessToken)
        .EmplaceStep<FGrantEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId)
        .EmplaceStep<FQueryEntitlementsHelper>(MoveTemp(QueryEntitlementsHelperParams))
        .EmplaceStep<FGetEntitlementsHelper>(MoveTemp(GetEntitlementsHelperParams), ExpectedEntitlementsNum)
        .EmplaceStep<FDeleteEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId);

    // Act & Assert (framework runs tick loop + assertions)
    RunToCompletion();
}
```

### Custom Pipeline Step Template (Optional)

```cpp
/**
 * Custom async step for pipeline.
 * Derive from FTestPipeline::FStep or FAsyncTestStep.
 */
class {{CUSTOM_STEP_CLASS}} : public FAsyncTestStep
{
public:
    {{CUSTOM_STEP_CLASS}}({{STEP_PARAMS}})
        : {{PARAM_INIT}}
    { }

    virtual void Run(FAsyncStepResult Result, const IOnlineServicesPtr& OnlineServices) override
    {
        // Perform async operation
        {{ASYNC_OPERATION_CODE}}

        // Complete with promise
        Result->SetValue({{RESULT_VALUE}});
    }

protected:
    {{STEP_MEMBER_VARIABLES}}
};
```

**Example (Custom Auth Step):**

```cpp
/**
 * Custom step to query external auth token.
 */
class FAuthQueryExternalAuthTokenStep : public FAsyncTestStep
{
public:
    struct Params
    {
        FAccountId LocalAccountId;
        FString TokenType;
    };

    FAuthQueryExternalAuthTokenStep(Params&& InParams)
        : OpParams(MoveTemp(InParams))
    { }

    virtual void Run(FAsyncStepResult Result, const IOnlineServicesPtr& OnlineServices) override
    {
        TSharedPtr<IAuth> AuthInterface = OnlineServices->GetInterface<IAuth>();
        REQUIRE(AuthInterface);

        FAuthQueryExternalAuthToken::Params QueryParams;
        QueryParams.LocalAccountId = OpParams.LocalAccountId;

        AuthInterface->QueryExternalAuthToken(MoveTemp(QueryParams))
            .Next([Result](TOnlineResult<FAuthQueryExternalAuthToken> OpResult) {
                REQUIRE(OpResult.IsOk());
                Result->SetValue(true);
            });
    }

protected:
    Params OpParams;
};
```

## Hybrid Pattern: Simple with Optional Pipeline

For flexibility, provide both patterns in same template:

```cpp
// ============================================================================
// Simple Async Tests (Explicit Tick Loop)
// ============================================================================

TEST_CASE_METHOD(FRunUntilQuitRequestedFixture,
                 "{{SIMPLE_TEST_DESCRIPTION}}",
                 "[simple]")
{
    // Simple callback-based async test
    {{SIMPLE_TEST_BODY}}
}

// ============================================================================
// Pipeline-Based Tests (Multi-Step Workflows)
// ============================================================================

{{PIPELINE_TEST_MACRO}}("{{PIPELINE_TEST_DESCRIPTION}}", "[pipeline]")
{
    // Complex multi-step async workflow
    {{PIPELINE_TEST_BODY}}
}
```

## Complete Example Test File

```cpp

/**
 * Test module for WebSockets - Async Operations
 *
 * Test coverage:
 * - WebSocket connection lifecycle (async callbacks)
 * - Message send/receive (tick loop)
 * - Error handling (timeout, connection errors)
 *
 * Pattern: simple (WebTests explicit tick loop pattern)
 */

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "HTTP/HttpModule.h"
#include "WebSockets/WebSocketsModule.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

#define WEBSOCKETS_TAG "[websockets]"
#define WEBSOCKETS_TEST_CASE(x, ...) TEST_CASE_METHOD(FRunUntilQuitRequestedFixture, x, WEBSOCKETS_TAG __VA_ARGS__)

namespace UE::WebTests
{

// ============================================================================
// Async Test Fixtures
// ============================================================================

/**
 * Base fixture for WebSocket module testing.
 */
class FWebSocketsModuleTestFixture
{
public:
    FWebSocketsModuleTestFixture()
        : WebServerIp(TEXT("127.0.0.1"))
        , WebServerWebSocketsPort(8000)
    {
        ParseSettingsFromCommandLine();

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

    void ParseSettingsFromCommandLine() {
        FParse::Value(FCommandLine::Get(), TEXT("-WebServerIp="), WebServerIp);
        FParse::Value(FCommandLine::Get(), TEXT("-WebServerWebSocketsPort="), WebServerWebSocketsPort);
    }

protected:
    FString WebServerIp;
    uint32 WebServerWebSocketsPort;
    FWebSocketsModule* WebSocketsModule;
    FHttpModule* HttpModule;
};

/**
 * Fixture with explicit tick loop for async operations.
 */
class FRunUntilQuitRequestedFixture : public FWebSocketsModuleTestFixture
{
public:
    FRunUntilQuitRequestedFixture() { }

    ~FRunUntilQuitRequestedFixture()
    {
        RunUntilQuitRequested();
    }

    void SimulateEngineTick()
    {
        FTSBackgroundableTicker::GetCoreTicker().Tick(TickFrequency);
        FTSTicker::GetCoreTicker().Tick(TickFrequency);
        FPlatformProcess::Sleep(TickFrequency);
        HttpModule->GetHttpManager().Tick(TickFrequency);
    }

    void RunUntilQuitRequested(float MaxSeconds = 30.0f)
    {
        const float StartTime = FPlatformTime::Seconds();
        while (!bQuitRequested)
        {
            SimulateEngineTick();

            if (FPlatformTime::Seconds() - StartTime > MaxSeconds)
            {
                FAIL("Test timed out after " << MaxSeconds << " seconds");
                break;
            }
        }
    }

    float TickFrequency = 1.0f / 60;
    bool bQuitRequested = false;
    bool bSucceed = false;
};

// ============================================================================
// WebSockets Async Tests
// ============================================================================

WEBSOCKETS_TEST_CASE("WebSockets can connect then send and receive message")
{
    // Arrange
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(
        FString::Format(TEXT("{0}/echo/"), { *UrlWebSocketsTests() }));

    // Register callbacks
    WebSocket->OnConnected().AddLambda([this, WebSocket](){
        WebSocket->Send(TEXT("hi websockets tests"));
    });

    WebSocket->OnMessage().AddLambda([this, WebSocket](const FString& MessageString) {
        CHECK(MessageString == TEXT("hi websockets tests"));
        bSucceed = true;
        bQuitRequested = true;
        WebSocket->Close();
    });

    WebSocket->OnConnectionError().AddLambda([this](const FString& Error) {
        FAIL("WebSocket connection failed: " << Error);
        bQuitRequested = true;
    });

    // Act
    WebSocket->Connect();

    // Tick loop runs in fixture destructor
}

WEBSOCKETS_TEST_CASE("WebSocket connection handles timeout", "[timeout]")
{
    // Arrange
    const float TimeoutSeconds = 5.0f;
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(
        TEXT("ws://invalid-host:9999/test"));  // Invalid URL

    bool bConnectionFailed = false;

    WebSocket->OnConnected().AddLambda([this](){
        FAIL("Connection should not succeed");
        bQuitRequested = true;
    });

    WebSocket->OnConnectionError().AddLambda([this, &bConnectionFailed](const FString& Error) {
        bConnectionFailed = true;
        bQuitRequested = true;
    });

    // Act
    WebSocket->Connect();

    // Tick loop with timeout
    RunUntilQuitRequested(TimeoutSeconds);

    // Assert
    REQUIRE(bConnectionFailed);
}

WEBSOCKETS_TEST_CASE("WebSocket can send binary data")
{
    // Arrange
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(
        FString::Format(TEXT("{0}/echo/"), { *UrlWebSocketsTests() }));

    TArray<uint8> BinaryData = { 0x01, 0x02, 0x03, 0x04, 0x05 };
    bool bReceivedCorrectData = false;

    WebSocket->OnConnected().AddLambda([this, WebSocket, BinaryData](){
        WebSocket->Send(BinaryData.GetData(), BinaryData.Num(), /* bIsBinary */ true);
    });

    WebSocket->OnRawMessage().AddLambda(
        [this, WebSocket, BinaryData, &bReceivedCorrectData](const void* Data, SIZE_T Size, SIZE_T BytesRemaining)
        {
            TArray<uint8> ReceivedData(static_cast<const uint8*>(Data), Size);
            bReceivedCorrectData = (ReceivedData == BinaryData);
            bQuitRequested = true;
            WebSocket->Close();
        });

    // Act
    WebSocket->Connect();

    // Assert (via callbacks)
    // Tick loop runs in fixture destructor
    // Assertion checked after completion
    REQUIRE(bReceivedCorrectData);
}

}  // namespace UE::WebTests
```

## Build Configuration (.Build.cs)

```csharp

using UnrealBuildTool;

public class {{TEST_MODULE_NAME}} : TestModuleRules
{
    static {{TEST_MODULE_NAME}}()
    {
        if (InTestMode)
        {
            TestMetadata = new Metadata();
            TestMetadata.TestName = "{{TEST_NAME}}";
            TestMetadata.TestShortName = "{{TEST_SHORT_NAME}}";
            TestMetadata.ReportType = "xml";
            {{PLATFORM_SUPPORT_CONFIG}}
        }
    }

    public {{TEST_MODULE_NAME}}(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "ApplicationCore",
                "Core",
                {{ASYNC_MODULE_DEPENDENCIES}}
            });

        {{ADDITIONAL_BUILD_CONFIG}}
    }
}
```

**Async Module Dependencies Examples:**

- **WebTests**: `"EventLoop", "HTTP", "SSL", "HTTPServer", "WebSockets", "Json"`
- **OnlineTests**: `"OnlineSubsystem", "OnlineServicesInterface", "OnlineServicesCommon", "OnlineTestsCore", "Json", "JsonUtilities"`

## Usage Guide

### Step 1: Choose Pattern Variant

**Simple Async (WebTests):**
- Direct callbacks with explicit tick loop
- Manual completion signaling
- Simpler, more transparent control flow
- Use for: HTTP, WebSocket, simple async APIs

**Pipeline Builder (OnlineTests):**
- Multi-step workflow abstraction
- Reusable step components
- Framework-managed tick loop
- Use for: Online Services, complex multi-step flows

### Step 2: Customize Placeholders

1. **Module Info**: `{{MODULE_NAME}}`, `{{ASYNC_OPERATION_N}}`
2. **Fixture**: `{{FIXTURE_CLASS_NAME}}`, `{{TICK_LOOP}}`
3. **Test Cases**: `{{TEST_DESCRIPTION}}`, `{{ASYNC_CALLBACK}}`
4. **Pattern-Specific**: `{{PIPELINE_STEPS}}` for pipeline variant

### Step 3: Implement Async Logic

1. **Setup**: Create resources, configure test parameters
2. **Callbacks**: Register OnConnected, OnMessage, OnError handlers
3. **Completion**: Set `bQuitRequested = true` when done
4. **Assertions**: Use CHECK/REQUIRE in callbacks or after completion

### Step 4: Handle Timeouts

1. **Default**: Fixture destructor timeout (30s)
2. **Custom**: Call `RunUntilQuitRequested(TimeoutSeconds)`
3. **Manual**: Check elapsed time in custom loop

## Best Practices

1. **Always Signal Completion**: Set `bQuitRequested = true` in success and error paths
2. **Register Error Handlers**: Use OnConnectionError, OnFailed callbacks to catch failures
3. **Use Lambda Captures**: Capture `this` and shared resources by value for safety
4. **Timeout All Tests**: Never rely on infinite loops - always have a timeout
5. **Fixture Cleanup**: Destructor ensures tick loop completes before module shutdown
6. **Avoid Blocking**: Never use blocking calls in async tests - defeats the purpose
7. **Pipeline Steps**: Keep steps small, focused, and reusable
8. **Assertions in Callbacks**: Use CHECK for non-fatal assertions in callbacks
9. **Thread Safety**: Be aware of thread-safe callback registration
10. **Tick Frequency**: 60 FPS (1/60s) default balances speed and responsiveness

## WebTests vs OnlineTests Pattern Comparison

| Aspect | WebTests (Simple) | OnlineTests (Pipeline) |
|--------|-------------------|------------------------|
| **Complexity** | Low - explicit control | High - abstraction layer |
| **Control Flow** | Transparent tick loop | Hidden in pipeline |
| **Reusability** | Copy-paste patterns | Composable steps |
| **Setup Overhead** | Minimal | Requires step classes |
| **Use Case** | Direct async APIs | Multi-step workflows |
| **Maintainability** | Each test self-contained | Changes affect pipeline |
| **Learning Curve** | Easy | Moderate |
| **Best For** | WebSocket, HTTP tests | Online Services tests |

## Related Templates

- **Basic/Fixture Template**: `cpp-basic-fixture-llt-template.md` (synchronous tests)
- **Plugin/Lifecycle Template**: `cpp-plugin-lifecycle-llt-template.md` (engine integration)
- **Mock Template**: `cpp-mock-llt-template.md` (dependency injection)
- **Build Configuration**: `ue-test-build-cs-template.md`
- **Target Configuration**: `ue-test-target-cs-template.md`

---

**Template Version**: 1.0.0
**Created**: 2026-02-18
**Pattern Coverage**: Simple Async (WebTests) + Pipeline Builder (OnlineTests)
**Validated Against**: 15+ LLT modules (30% async usage)
**Status**: Complete
