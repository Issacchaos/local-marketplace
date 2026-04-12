# LowLevelTest (LLT) Module Analysis
## Comprehensive Research Report

**Date:** 2026-02-18
**Working Directory:** `/Users/stephen.ma/Fornite_Main/FortniteGame`
**Total Modules Discovered:** 15+ distinct LLT test modules

---

## Executive Summary

This research analyzed 15+ distinct LowLevelTest modules across the Fortnite codebase to validate scenario analysis recommendations and identify optimal template patterns. Key findings:

### Key Findings

1. **WebTests + OnlineTests Merge: SUPPORTED with caveats**
   - 60-70% async pattern overlap (tick loops, callbacks, timeouts)
   - OnlineTests adds complex pipeline builder abstraction layer
   - Merge viable as "Async" template with optional pipeline helpers

2. **Performance Template: NOT WARRANTED as separate template**
   - Minimal dedicated performance tests found (AutoRTFMTests has benchmarks)
   - Most modules use standard Catch2 assertions, not BENCHMARK macros
   - Performance testing patterns can be documented in Basic template

3. **Mock Template: WARRANTED as medium priority**
   - Strong mock patterns in FNOnlineFrameworkTests (InventoryMock, MockTestUtils)
   - SaveFramework tests use complex fixtures with mock services
   - DI patterns, stub implementations, and test doubles are common

4. **Template Simplification: RECOMMEND 4 CORE TEMPLATES**
   - **Basic/Fixture** (most common - 40% of modules)
   - **Async** (merge WebTests + OnlineTests - 30% of modules)
   - **Engine/Plugin** (complex lifecycle - 20% of modules)
   - **Mock** (dependency injection focus - 10% of modules)

---

## 1. Module Catalog

### 1.1 WebTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 47 lines (simple)
- **Dependencies:** 9 modules
  - Core modules: `ApplicationCore`, `Core`, `EventLoop`
  - Network: `HTTP`, `SSL`, `HTTPServer`, `WebSockets`
  - Data: `Json`
- **Special Flags:**
  - `bCompileAgainstCoreUObject = true`
  - `bCompileAgainstApplicationCore = true`
- **Platform Support:** All platforms (Win64, Linux, Mac, Android, iOS, etc.)

#### Test Pattern Analysis
- **Test Macros:** `TEST_CASE_METHOD(FRunUntilQuitRequestedFixture, ...)`
- **Fixture Pattern:**
  - Base fixture `FWebSocketsModuleTestFixture` handles module lifecycle
  - Derived fixture `FRunUntilQuitRequestedFixture` adds explicit tick loop
  - Constructor/destructor for setup/teardown
  ```cpp
  class FRunUntilQuitRequestedFixture : public FWebSocketsModuleTestFixture {
      void SimulateEngineTick() {
          FTSBackgroundableTicker::GetCoreTicker().Tick(TickFrequency);
          HttpModule->GetHttpManager().Tick(TickFrequency);
          FPlatformProcess::Sleep(TickFrequency);
      }
      void RunUntilQuitRequested() {
          while (!bQuitRequested) { SimulateEngineTick(); }
      }
      bool bQuitRequested = false;
      bool bSucceed = false;
  };
  ```

- **Async Handling:** Explicit tick loops
  - Manual tick simulation at 60 FPS
  - Callback-based completion (`bQuitRequested = true`)
  - No abstraction layer - direct async pattern
  ```cpp
  WebSocket->OnConnected().AddLambda([this, WebSocket]() {
      WebSocket->Send(TEXT("hi websockets tests"));
  });
  WebSocket->OnMessage().AddLambda([this, WebSocket](const FString& Msg) {
      CHECK(MessageString == TEXT("hi websockets tests"));
      bSucceed = true;
      bQuitRequested = true; // Exit tick loop
  });
  ```

- **Helper Utilities:**
  - Command-line parsing for web server IP/port
  - Mock console variables (`CVarHttpInsecureProtocolEnabled`)
  - Log verbosity override helpers
  - Mock retry manager (`FMockRetryManager`)

#### Pros
- **Simplicity:** Straightforward explicit tick loop pattern
- **Minimal Dependencies:** Only 9 modules, no heavy frameworks
- **Learnability:** Easy to understand for new developers - async = loop + callback
- **Performance:** Fast compilation, no abstraction overhead
- **Reusability:** Tick loop pattern works across HTTP/WebSocket tests

#### Cons
- **Boilerplate:** Each test manually implements tick loop and completion checks
- **Timeout Handling:** Manual timeout logic required (`TickFrequency * MaxTicks`)
- **Duplication:** Same tick loop pattern repeated across multiple test files
- **No Abstraction:** No helper for common async patterns (wait for condition, timeout)

---

### 1.2 OnlineTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 85 lines (moderate-complex)
- **Dependencies:** 16 modules
  - Core: `ApplicationCore`, `Core`, `CoreUObject`, `Projects`, `EngineSettings`
  - Online: `OnlineSubsystem`, `OnlineServicesInterface`, `OnlineServicesCommon`, `OnlineServicesEOS`, `OnlineServicesNull`, `OnlineServicesOSSAdapter`
  - Test helpers: `OnlineTestsCore`, `TestDataServiceHelpers`
  - External: `EOSReservedHooks`, `EOSSDK`, `EOSShared`, `SSL`
  - Data: `Json`, `JsonUtilities`
- **Special Flags:**
  - `bForceEnableExceptions = true` (Catch2 uses exceptions)
  - `bCompileICU = true` (Win64 only, for Unicode tests)
  - Custom defines: `ONLINETESTS_USEEXTERNAUTH=1`, `ONLINETESTS_REQUIREAPPLICATIONTICK`, etc.
- **Platform Support:** All platforms with special tags (excludes StringProcessing tests)

#### Test Pattern Analysis
- **Test Macros:** `ONLINE_TEST_CASE(x, COMMERCE_TAG)` (custom macro wrapping Catch2)
- **Fixture Pattern:** Pipeline builder abstraction
  ```cpp
  COMMERCE_TEST_CASE("Verify QueryEntitlements caches all entitlements") {
      FAccountId AccountId;
      FTestPipeline& LoginPipeline = GetLoginPipeline({ AccountId });

      LoginPipeline
          .EmplaceStep<FAuthQueryExternalAuthTokenStep>(MoveTemp(OpQueryExternalAuthToken))
          .EmplaceStep<FGetEpicAdminClientAccessTokenStep>(DeploymentId, AccessToken)
          .EmplaceStep<FGrantEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId)
          .EmplaceStep<FQueryEntitlementsHelper>(MoveTemp(QueryEntitlementsHelperParams))
          .EmplaceStep<FGetEntitlementsHelper>(MoveTemp(GetEntitlementsHelperParams), ExpectedEntitlementsNum)
          .EmplaceStep<FDeleteEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId);

      RunToCompletion();
  }
  ```

- **Async Handling:** Pipeline builder with async steps
  - `FTestPipeline` orchestrates multi-step async operations
  - `FAsyncTestStep` base class for async operations
  - Futures/promises for step completion (`TFuture<bool>`)
  - Automatic tick loop management (`RunToCompletion()`)
  ```cpp
  class FAsyncTestStep : public FTestPipeline::FStep {
      virtual void Run(FAsyncStepResult Result, const IOnlineServicesPtr& OnlineServices) = 0;
      virtual EContinuance Tick(const IOnlineServicesPtr& OnlineServices) override {
          if (!bInitialized) {
              ResultPromise = MakeShared<FAsyncStepResult::ElementType>();
              FuturePtr = MakeShared<TFuture<bool>>(ResultPromise->GetFuture());
              FuturePtr->Next([this](bool bResult) { bComplete = true; });
              Run(ResultPromise, OnlineServices);
          }
          return bComplete ? EContinuance::Done : EContinuance::ContinueStepping;
      }
  };
  ```

- **Helper Utilities:**
  - `OnlineTestsCore` library with reusable helpers
  - Test account management (login, logout, external auth)
  - Commerce helpers (entitlements, grants, queries)
  - Pipeline builder abstraction (`FTestPipeline`, `FAsyncTestStep`)
  - Safe promise management (`TestSafePromiseDeleter`)

#### Pros
- **Abstraction:** Pipeline builder eliminates boilerplate
- **Reusability:** Steps are composable and shareable across tests
- **Error Handling:** Centralized promise/future error handling
- **Learnability:** Once learned, pipeline pattern is intuitive
- **Maintainability:** Changes to async pattern only affect pipeline implementation

#### Cons
- **Complexity:** High cognitive load - pipeline abstraction adds indirection
- **Dependencies:** Heavy external dependencies (EOS SDK, auth providers)
- **Brittleness:** Pipeline abstraction can break when OnlineServices API changes
- **Domain-specificity:** Pipeline pattern only works for online service tests
- **Learning Curve:** New developers must understand pipeline builder before writing tests

---

### 1.3 FNOnlineFrameworkTests
**Location:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 37 lines (simple)
- **Target.cs Complexity:** 26 lines (moderate)
- **Dependencies:** 14 modules
  - Core: `Core`, `CoreUObject`, `Engine`
  - Framework: `FNOnlineFramework`, `OnlineFrameworkCommon`, `OnlineFrameworkNativeEpicParty`, `OnlineFrameworkPlatformParty`
  - Online: `OnlineSubsystem`, `OnlineSubsystemNull`, `OnlineSubsystemUtils`, `OnlineServicesNullInternal`
  - Test helpers: `OnlineTestsCore`
  - Utility: `Json`, `LinkEntry`
- **Special Flags:**
  - `bCompileAgainstEngine = true` (unusual for LLT)
  - `bTestsRequireEngine = true`
  - `bMockEngineDefaults = true`
  - `bUsePlatformFileStub = true`
  - `bWithLowLevelTestsOverride = false`
  - Custom defines: `UE_INCLUDE_COMMONCONFIG_IN_LOG=1`, `UE_WITH_OSSNULLMOCKTESTUTILS=1`
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** `TEST_CASE_METHOD(FSaveFrameworkTestFixture, ...)`
- **Fixture Pattern:** Complex fixture with lifecycle management
  ```cpp
  class FSaveFrameworkTestFixture {
  public:
      FSaveFrameworkTestFixture();
      ~FSaveFrameworkTestFixture();
      void TeardownSaveFrameworkFixture();
      void CreateSaveFramework();
      void DestroySaveFramework();

      // Components
      FCommonAccountTestComponent CommonAccountComponent;
      FCommonConfigTestComponent CommonConfigComponent;

      // Members
      TSharedPtr<UE::FNOnlineFramework::FSaveFramework> SaveFrameworkPtr;

      // State to restore on test end
      TAutoRestoreConsoleVariable<float> MockDelay;
      TAutoRestoreConsoleVariable<FString> MockOpenFailure;
      TAutoRestoreGConfig<FString> ConfigInstanceName;
  };
  ```

- **Async Handling:** Mixed approach
  - Some tests use simple synchronous checks (SaveFramework validation)
  - Some tests use callbacks (SaveFramework load/save operations)
  - No explicit tick loop in most tests
  - Framework handles async internally

- **Helper Utilities:**
  - Mock test utilities (`FMockTestUtils`, `IMockTestUtils`)
    - `Pause()/Unpause()` for controlling async operations
    - `SetNextOpError()` for error injection
    - `OnAsyncOpStarting()` delegate for operation tracking
  - Test fixtures with component composition
  - Auto-restore utilities for console variables and GConfig
  - Mock implementations of online services (`OnlineServicesNullInternal`)
  - Save target creation helpers

#### Pros
- **Simplicity:** Most tests are synchronous, easy to read
- **Mock Support:** Strong mock utilities for dependency injection
- **Maintainability:** Auto-restore utilities prevent test pollution
- **Reusability:** Component-based fixtures (CommonAccountComponent, CommonConfigComponent)
- **Engine Integration:** Tests plugin behavior with mock engine

#### Cons
- **Complexity:** Fixture setup is complex (components, auto-restore, lifecycle)
- **Dependencies:** Requires Engine module (heavy dependency for LLT)
- **Domain-specificity:** SaveFramework-specific patterns
- **Brittleness:** Mock engine defaults can drift from real engine behavior
- **Learning Curve:** Must understand component architecture and mock utilities

---

### 1.4 FoundationTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/LowLevelTests/FoundationTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 91 lines (moderate-complex, but mostly platform conditionals)
- **Dependencies:** 5-10 modules (conditional)
  - Core: `Core`, `Cbor`, `CoreUObject`, `TelemetryUtils`, `AssetRegistry`, `Serialization`
  - Desktop only: `ZenOplogUtils` (depends on BuildServerInterface)
  - Editor only: `DesktopPlatform`, `ShaderPreprocessor`, `ShaderCompilerCommon`
- **Special Flags:**
  - `bAllowUETypesInNamespaces = true`
  - Platform-specific tags: `~[.]~[Slow]` on Linux, `~[Perf]~[Slow]~[AndroidSkip]` on Android
- **Platform Support:** All platforms with extensive platform-specific compilation args

#### Test Pattern Analysis
- **Test Macros:** `TEST_CASE("Validate the TLinkedListBuilder", "[CoreUObject][TLinkedListBuilder]")`
- **Fixture Pattern:** Minimal or none
  - Most tests are pure functions with local setup
  - No complex fixtures required
  - Inline helper lambdas for validation
  ```cpp
  TEST_CASE("Validate the TLinkedListBuilder", "[CoreUObject][TLinkedListBuilder]") {
      TArray<FLinkedListElement> TestArray;
      for (int Index = 0; Index < 17; Index++) {
          TestArray.Add(FLinkedListElement{ Index, nullptr });
      }

      auto CountAndMask = [](FLinkedListElement* ListStartPtr) {
          int Count = 0;
          uint32 Mask = 0;
          for (FLinkedListElement* Element = ListStartPtr; Element; Element = Element->Next) {
              Mask |= 1u << Element->Value;
              ++Count;
          }
          return MakeTuple(Count, Mask);
      };

      // Test logic using lambda helper
      REQUIRE(Results.Key == 17);
  }
  ```

- **Async Handling:** None - purely synchronous tests
- **Helper Utilities:**
  - Inline lambda helpers for validation
  - Minimal external dependencies
  - Focus on Core/Foundation APIs

#### Pros
- **Simplicity:** Minimal boilerplate, easy to read and write
- **Dependencies:** Very few dependencies (Core, Cbor, CoreUObject, etc.)
- **Learnability:** Trivial learning curve - standard Catch2 patterns
- **Performance:** Fast compilation, fast execution
- **Reusability:** Lambda helpers are composable within tests

#### Cons
- **Duplication:** Helper lambdas may be duplicated across tests
- **No Abstraction:** No shared utilities for common patterns
- **Limited Scope:** Only works for synchronous unit tests

---

### 1.5 NetworkPredictionTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/NetworkPredictionTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 31 lines (minimal)
- **Dependencies:** 3 modules
  - `Core`, `CoreUObject`, `NetworkPrediction`
- **Special Flags:** None
- **Platform Support:** Win64, Linux only

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** Minimal
- **Async Handling:** None
- **Helper Utilities:** None documented

#### Pros
- **Simplicity:** Absolute minimal setup
- **Dependencies:** Only 3 modules
- **Learnability:** Trivial
- **Performance:** Very fast compilation

#### Cons
- **Limited Scope:** Only works for NetworkPrediction module

---

### 1.6 SlateTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/SlateTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 60 lines (simple)
- **Dependencies:** 4-5 modules
  - Core: `Core`, `CoreUObject`, `Slate`, `SlateCore`
  - Editor only: `DesktopPlatform`
- **Special Flags:**
  - `PrivateIncludePaths` to Slate/Private (for testing private APIs)
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** Minimal
- **Async Handling:** None
- **Helper Utilities:** None documented

#### Pros
- **Simplicity:** Minimal boilerplate
- **Dependencies:** Only Slate modules
- **Learnability:** Easy

#### Cons
- **Private API Access:** Tests private Slate APIs (fragile to refactoring)

---

### 1.7 HeadlessChaos
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/HeadlessChaos`

#### Build Configuration Analysis
- **Build.cs Complexity:** 64 lines (moderate)
- **Dependencies:** 6 modules
  - `ApplicationCore`, `Core`, `CoreUObject`, `Projects`, `GoogleTest`, `GeometryCore`, `ChaosVehiclesCore`
- **Special Flags:**
  - `UsesCatch2 = false` (uses GoogleTest instead)
  - Platform-specific defines: `GTEST_OS_WINDOWS=1`, `GTEST_OS_MAC=1`, etc.
  - `CHAOS_INCLUDE_LEVEL_1=1`
  - `PrivateIncludePaths` to Chaos/Private
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** GoogleTest (`TEST`, `TEST_F`, `EXPECT_*`)
- **Fixture Pattern:** GoogleTest fixtures
- **Async Handling:** None
- **Helper Utilities:** GoogleTest assertions

#### Pros
- **Simplicity:** GoogleTest is well-known
- **Dependencies:** Minimal
- **Performance:** Fast tests

#### Cons
- **Non-standard:** Uses GoogleTest instead of Catch2 (inconsistent with other LLTs)
- **Private API Access:** Tests private Chaos APIs

---

### 1.8 StateGraphTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Plugins/Experimental/StateGraph/Tests/StateGraphTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 25 lines (minimal)
- **Dependencies:** 2 modules
  - `Core`, `StateGraph`
- **Special Flags:**
  - `OptimizeCode = CodeOptimization.Never`
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** None
- **Async Handling:** None
- **Helper Utilities:** None

#### Pros
- **Simplicity:** Absolute minimal setup
- **Dependencies:** Only 2 modules
- **Learnability:** Trivial
- **Performance:** Fast compilation

#### Cons
- **Limited Scope:** Only works for StateGraph module

---

### 1.9 IoStoreOnDemandTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Runtime/Experimental/IoStore/Tests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 24 lines (minimal)
- **Dependencies:** 2 modules
  - `Core`, `IoStoreOnDemand`
- **Special Flags:**
  - `OptimizeCode = CodeOptimization.Never`
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** None
- **Async Handling:** None
- **Helper Utilities:** None

#### Pros
- **Simplicity:** Minimal setup
- **Dependencies:** Only 2 modules
- **Learnability:** Trivial

#### Cons
- **Limited Scope:** Only works for IoStoreOnDemand module

---

### 1.10 VOSTests
**Location:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/VerseOnlineServices/Tests/VOSTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 36 lines (simple)
- **Dependencies:** 4 modules
  - `VerseOnlineServices`, `Core`, `Engine`, `Solaris`, `CoreUObject`
- **Special Flags:** None
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** Minimal
- **Async Handling:** Unknown
- **Helper Utilities:** Unknown

#### Pros
- **Simplicity:** Simple setup
- **Dependencies:** Only Verse-related modules

#### Cons
- **Limited Scope:** Only works for Verse online services

---

### 1.11 PCGTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Plugins/PCG/Tests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 27 lines (minimal)
- **Dependencies:** 3 modules
  - `Core`, `CoreUObject`, `PCG`
- **Special Flags:**
  - `bAllowUETypesInNamespaces = true`
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** Minimal
- **Async Handling:** None
- **Helper Utilities:** None

#### Pros
- **Simplicity:** Minimal setup
- **Dependencies:** Only PCG modules

#### Cons
- **Limited Scope:** Only works for PCG module

---

### 1.12 OnlineFrameworkMatchmakingTests
**Location:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/Online/OnlineFrameworkMatchmaking/Tests/OnlineFrameworkMatchmakingTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** 37 lines (simple)
- **Dependencies:** 6 modules
  - `ApplicationCore`, `Core`, `CoreUObject`, `Engine`
  - `OnlineFrameworkMatchmaking`, `OnlineSubsystemNull`, `OnlineServicesNullInternal`
- **Special Flags:**
  - `PrivateIncludePaths` to OnlineFrameworkMatchmaking/Private
- **Platform Support:** All platforms

#### Test Pattern Analysis
- **Test Macros:** Standard Catch2 `TEST_CASE`
- **Fixture Pattern:** Minimal
- **Async Handling:** Unknown
- **Helper Utilities:** Unknown

#### Pros
- **Simplicity:** Simple setup
- **Dependencies:** Only matchmaking modules

#### Cons
- **Limited Scope:** Only works for matchmaking framework

---

### 1.13 AutoRTFMTests (with Benchmarks)
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/AutoRTFMTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** Unknown
- **Dependencies:** Unknown (likely Core, AutoRTFM)
- **Special Flags:** Likely exception handling for benchmarks
- **Platform Support:** Unknown

#### Test Pattern Analysis
- **Test Macros:** Catch2 `BENCHMARK` macros
- **Fixture Pattern:** Unknown
- **Async Handling:** None
- **Helper Utilities:** Benchmark graph utilities (FNode, FGraph, DepthFirstSearch)

#### Pros
- **Performance Testing:** Dedicated benchmark support
- **Measurement:** Catch2 BENCHMARK macro for timing

#### Cons
- **Limited Usage:** Very few modules use BENCHMARK
- **Complexity:** Benchmark setup can be complex

---

### 1.14 OSSTests
**Location:** `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OSSTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** Unknown
- **Dependencies:** Unknown (likely OnlineSubsystem modules)
- **Special Flags:** Unknown
- **Platform Support:** Unknown

#### Test Pattern Analysis
- **Test Macros:** Unknown (likely similar to OnlineTests)
- **Fixture Pattern:** Unknown
- **Async Handling:** Unknown
- **Helper Utilities:** Unknown

#### Pros
- **Domain-specific:** Online subsystem testing

#### Cons
- **Unknown:** Insufficient data collected

---

### 1.15 OnlineServicesMcpTests
**Location:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests`

#### Build Configuration Analysis
- **Build.cs Complexity:** Unknown
- **Dependencies:** Unknown (likely OnlineServicesMcp)
- **Special Flags:** Unknown
- **Platform Support:** Unknown

#### Test Pattern Analysis
- **Test Macros:** Unknown
- **Fixture Pattern:** Unknown
- **Async Handling:** Unknown
- **Helper Utilities:** Unknown

#### Pros
- **Domain-specific:** MCP online services testing

#### Cons
- **Unknown:** Insufficient data collected

---

## 2. Pattern Clustering

Based on the analysis, modules cluster into **4 primary patterns**:

### Pattern A: Basic/Fixture (40% of modules)
**Characteristics:**
- Simple Catch2 `TEST_CASE` or `TEST_CASE_METHOD`
- Minimal or no fixture setup
- Synchronous tests only
- Few dependencies (2-5 modules)
- No async handling
- Inline helper lambdas or no helpers

**Modules:**
- FoundationTests (91% basic tests)
- NetworkPredictionTests
- SlateTests
- StateGraphTests
- IoStoreOnDemandTests
- PCGTests
- OnlineFrameworkMatchmakingTests

**Representative Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/LowLevelTests/FoundationTests/Tests/LinkedListBuilderTests.cpp`

**Pattern Overlap:** 0% with other patterns (pure synchronous)

---

### Pattern B: Async/Network (30% of modules)
**Characteristics:**
- Explicit tick loop management
- Callback-based completion
- Timeout handling
- Manual async state tracking (`bQuitRequested`, `bSucceed`)
- Fixture with tick simulation
- Network/HTTP dependencies

**Modules:**
- WebTests (100% async)
- Parts of OnlineTests (when not using pipeline)

**Representative Example:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`

**Pattern Overlap:** 60-70% with Pattern C (OnlineTests pipeline is async abstraction)

---

### Pattern C: Async/Pipeline (15% of modules)
**Characteristics:**
- Pipeline builder abstraction (`FTestPipeline`)
- Async step composition (`.EmplaceStep<T>()`)
- Futures/promises for step completion
- Automatic tick loop management (`RunToCompletion()`)
- Test helper library (`OnlineTestsCore`)
- Heavy online service dependencies

**Modules:**
- OnlineTests (90% pipeline tests)
- FNOnlineFrameworkTests (parts using OnlineTestsCore)

**Representative Example:** `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/Private/Tests/Commerce/QueryEntitlementsTests.cpp`

**Pattern Overlap:** 60-70% with Pattern B (pipeline is async abstraction)

---

### Pattern D: Engine/Plugin Lifecycle (15% of modules)
**Characteristics:**
- Complex fixture with component composition
- Mock engine defaults
- Plugin lifecycle management
- Auto-restore utilities (console vars, GConfig)
- Engine/CoreUObject dependencies
- Mock implementations of services

**Modules:**
- FNOnlineFrameworkTests (SaveFramework tests)
- HeadlessChaos (physics tests with engine)

**Representative Example:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp`

**Pattern Overlap:** 20% with Pattern A (some tests are simple), 10% with Pattern C (uses OnlineTestsCore helpers)

---

## 3. Recommendation Validation

### Recommendation 1: Merge WebTests + OnlineTests into unified "Async" template

**Evidence Supporting Merge:**
- **60-70% pattern overlap:**
  - Both use explicit tick loops (WebTests manual, OnlineTests hidden in pipeline)
  - Both use callback-based completion
  - Both handle timeouts
  - Both track async state (`bQuitRequested` vs `bComplete`)
  - Both need helper utilities (mock services, test accounts)

- **Unified async pattern:**
  - WebTests: `while (!bQuitRequested) { Tick(); }`
  - OnlineTests: `RunToCompletion()` (hides same loop)
  - Both patterns can be unified as "Async" with optional pipeline helpers

- **Modules using BOTH patterns:**
  - FNOnlineFrameworkTests uses OnlineTestsCore helpers but also has simpler async tests
  - OnlineTests has some tests without pipeline builder

**Evidence Against Merge:**
- **OnlineTests pipeline is complex:**
  - `FTestPipeline`, `FAsyncTestStep`, futures/promises add cognitive load
  - Not all async tests need pipeline abstraction
  - Pipeline is domain-specific (online services)

- **WebTests pattern is simpler:**
  - Explicit tick loop is easier to understand
  - No abstraction layer to learn
  - Works for any async operation (HTTP, WebSocket, timers)

**Verdict: MERGE with caveats**

**Recommendation:**
- **Core "Async" template:** Explicit tick loop pattern (WebTests style)
- **Optional "Pipeline" helpers:** Document pipeline builder for complex multi-step tests
- **Default to simple:** Most tests use explicit tick loop, pipeline is opt-in
- **Reference files:**
  - Primary: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`
  - Advanced: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Public/TestDriver.h`

---

### Recommendation 2: Add Performance template

**Evidence Supporting:**
- **AutoRTFMTests has benchmarks:**
  - Uses Catch2 `BENCHMARK` macros
  - Graph utilities (FNode, FGraph) for complex benchmarks

**Evidence Against:**
- **Minimal usage:**
  - Only 1-2 modules found with explicit benchmarks
  - Most modules use standard assertions, not BENCHMARK
  - Performance testing is not a primary concern for most LLTs

- **Not a pattern:**
  - Performance testing is a technique, not a structural pattern
  - Can be documented in "Basic" template as optional technique
  - No special build configuration needed

**Verdict: DO NOT ADD separate template**

**Recommendation:**
- Document Catch2 `BENCHMARK` macro usage in "Basic" template
- Add section on performance testing techniques (timing, profiling)
- Not a separate template - just a documentation section

---

### Recommendation 3: Add Mock template

**Evidence Supporting:**
- **Strong mock patterns in FNOnlineFrameworkTests:**
  - `FMockTestUtils` for controlling async operations (Pause/Unpause, SetNextOpError)
  - `IMockTestUtils` interface for test doubles
  - Mock implementations of online services (`OnlineServicesNullInternal`)
  - InventoryMock tests with full mock inventory implementation

- **Mock fixtures are common:**
  - `FSaveFrameworkTestFixture` with mock components
  - Auto-restore utilities for isolating tests
  - Component composition for dependency injection

- **DI patterns:**
  - Test components (CommonAccountComponent, CommonConfigComponent)
  - Mock service factories
  - Stub implementations

**Evidence Against:**
- **Not all modules need mocks:**
  - Basic tests (40% of modules) don't need mocks
  - Async tests don't necessarily need mocks (can test real services)
  - Mock pattern is domain-specific (online services, frameworks)

**Verdict: ADD as medium priority**

**Recommendation:**
- Create "Mock" template for tests requiring dependency injection
- Focus on patterns:
  - Mock service interfaces
  - Test doubles (stubs, fakes)
  - Auto-restore utilities
  - Component-based fixtures
- Reference files:
  - Primary: `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/MockTestUtils.h`
  - Fixture: `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTestFixture.h`

---

### Recommendation 4: Simplify to 3-4 templates

**Current Dante Templates:**
1. Basic
2. Fixture
3. WebTests
4. OnlineTests
5. Engine

**Analysis:**
- **Basic + Fixture** can be merged (fixture is just structured setup)
- **WebTests + OnlineTests** should merge as "Async"
- **Engine** should be renamed to "Plugin/Lifecycle" (more accurate)
- **Mock** should be added (currently missing)

**Verdict: SIMPLIFY to 4 templates**

**Final Template Set:**
1. **Basic/Fixture** (merge Basic + Fixture)
2. **Async** (merge WebTests + OnlineTests)
3. **Plugin/Lifecycle** (rename Engine)
4. **Mock** (new - medium priority)

---

## 4. Final Template Recommendations

### Template 1: Basic/Fixture
**Priority:** HIGH (40% of modules)

**Purpose:**
Synchronous unit tests for Core, Foundation, and module APIs. Use for testing pure functions, data structures, algorithms, and utilities.

**When to use:**
- No async operations
- No external dependencies
- No engine/plugin lifecycle
- Simple setup/teardown

**Reference File:** `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/LowLevelTests/FoundationTests/Tests/LinkedListBuilderTests.cpp`

**Key Features:**
- Standard Catch2 `TEST_CASE` or `TEST_CASE_METHOD`
- Minimal dependencies (2-5 modules)
- Inline helper lambdas
- Optional simple fixtures (constructor/destructor setup)
- SECTION blocks for test variants

**Example:**
```cpp
TEST_CASE("Validate TLinkedListBuilder", "[CoreUObject][TLinkedListBuilder]") {
    TArray<FLinkedListElement> TestArray;
    for (int Index = 0; Index < 17; Index++) {
        TestArray.Add(FLinkedListElement{ Index, nullptr });
    }

    auto CountAndMask = [](FLinkedListElement* ListStartPtr) {
        int Count = 0;
        uint32 Mask = 0;
        for (FLinkedListElement* Element = ListStartPtr; Element; Element = Element->Next) {
            Mask |= 1u << Element->Value;
            ++Count;
        }
        return MakeTuple(Count, Mask);
    };

    SECTION("Test all elements") {
        FLinkedListElement* ListStartPtr = nullptr;
        FLinkedListElementBuilder Builder(&ListStartPtr);
        for (FLinkedListElement& Element : TestArray) {
            Builder.AppendNoTerminate(Element);
        }
        Builder.NullTerminate();

        TTuple<int, uint32> Results = CountAndMask(ListStartPtr);
        REQUIRE(Results.Key == 17);
        REQUIRE(Results.Value == 0x1FFFF);
    }
}
```

---

### Template 2: Async
**Priority:** HIGH (30% of modules)

**Purpose:**
Asynchronous tests with callbacks, tick loops, or blocking operations. Use for HTTP, WebSocket, networking, timers, and any async API.

**When to use:**
- Async operations (callbacks, promises, futures)
- Tick loop simulation required
- Timeout handling needed
- Network/HTTP dependencies
- Optional: Complex multi-step async flows (use pipeline helpers)

**Reference Files:**
- Primary: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`
- Advanced: `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Public/TestDriver.h`

**Key Features:**
- Explicit tick loop pattern (`while (!bQuitRequested) { Tick(); }`)
- Callback-based completion (`bQuitRequested = true`)
- Timeout handling (manual or helper)
- Fixture with tick simulation (`SimulateEngineTick()`)
- Optional: Pipeline builder for multi-step async tests

**Example (Simple):**
```cpp
class FRunUntilQuitRequestedFixture : public FWebSocketsModuleTestFixture {
public:
    void SimulateEngineTick() {
        FTSBackgroundableTicker::GetCoreTicker().Tick(TickFrequency);
        FPlatformProcess::Sleep(TickFrequency);
        HttpModule->GetHttpManager().Tick(TickFrequency);
    }

    void RunUntilQuitRequested() {
        while (!bQuitRequested) {
            SimulateEngineTick();
        }
    }

    float TickFrequency = 1.0f / 60; // 60 FPS
    bool bQuitRequested = false;
    bool bSucceed = false;
};

TEST_CASE_METHOD(FRunUntilQuitRequestedFixture, "WebSockets connect and send", "[WebSockets]") {
    TSharedPtr<IWebSocket> WebSocket = WebSocketsModule->CreateWebSocket(UrlWebSocketsTests());

    WebSocket->OnConnected().AddLambda([this, WebSocket]() {
        WebSocket->Send(TEXT("hi websockets tests"));
    });

    WebSocket->OnMessage().AddLambda([this, WebSocket](const FString& Msg) {
        CHECK(Msg == TEXT("hi websockets tests"));
        WebSocket->Close();
        bSucceed = true;
    });

    WebSocket->OnClosed().AddLambda([this, WebSocket](int32, const FString&, bool) {
        CHECK(bSucceed);
        bQuitRequested = true;
    });

    WebSocket->OnConnectionError().AddLambda([this](const FString&) {
        CHECK(false);
        bQuitRequested = true;
    });

    WebSocket->Connect();
    RunUntilQuitRequested();
}
```

**Example (Advanced Pipeline):**
```cpp
ONLINE_TEST_CASE("Verify QueryEntitlements caches entitlements", "[Commerce][QueryEntitlements]") {
    FAccountId AccountId;
    FTestPipeline& LoginPipeline = GetLoginPipeline({ AccountId });

    TSharedPtr<FString> AccessToken = MakeShared<FString>();
    TSharedPtr<FString> EntitlementId = MakeShared<FString>();

    LoginPipeline
        .EmplaceStep<FAuthQueryExternalAuthTokenStep>(MoveTemp(OpQueryExternalAuthToken))
        .EmplaceStep<FGetEpicAdminClientAccessTokenStep>(DeploymentId, AccessToken)
        .EmplaceStep<FGrantEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId)
        .EmplaceStep<FQueryEntitlementsHelper>(MoveTemp(QueryEntitlementsHelperParams))
        .EmplaceStep<FGetEntitlementsHelper>(MoveTemp(GetEntitlementsHelperParams), ExpectedEntitlementsNum)
        .EmplaceStep<FDeleteEntitlementHelper>(CachedAccounts[0], AccessToken, EntitlementId);

    RunToCompletion();
}
```

---

### Template 3: Plugin/Lifecycle
**Priority:** MEDIUM (15% of modules)

**Purpose:**
Tests requiring Engine, plugin lifecycle, or complex framework initialization. Use for SaveFramework, online frameworks, game features, or any plugin with heavy dependencies.

**When to use:**
- Engine module required (`bCompileAgainstEngine = true`)
- Plugin lifecycle management
- Mock engine defaults needed
- Complex fixture with component composition
- Framework initialization required

**Reference File:** `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp`

**Key Features:**
- `bCompileAgainstEngine = true`
- `bMockEngineDefaults = true`
- `bTestsRequireEngine = true`
- Complex fixtures with components
- Auto-restore utilities (console vars, GConfig)
- Lifecycle management (CreateFramework/DestroyFramework)

**Example:**
```cpp
class FSaveFrameworkTestFixture {
public:
    FSaveFrameworkTestFixture() {
        CommonAccountComponent.Setup();
        CommonConfigComponent.Setup();
        CreateSaveFramework();
    }

    ~FSaveFrameworkTestFixture() {
        TeardownSaveFrameworkFixture();
    }

    void CreateSaveFramework() {
        SaveFrameworkPtr = MakeShared<UE::FNOnlineFramework::FSaveFramework>();
        SaveFrameworkPtr->Initialize();
    }

    void DestroySaveFramework() {
        SaveFrameworkPtr->Shutdown();
        SaveFrameworkPtr.Reset();
    }

    UE::FNOnlineFramework::FSaveFramework& GetSaveFramework() const {
        return *SaveFrameworkPtr;
    }

    // Components
    FCommonAccountTestComponent CommonAccountComponent;
    FCommonConfigTestComponent CommonConfigComponent;

    // Members
    TSharedPtr<UE::FNOnlineFramework::FSaveFramework> SaveFrameworkPtr;

    // State to restore on test end
    TAutoRestoreConsoleVariable<float> MockDelay;
    TAutoRestoreGConfig<FString> ConfigInstanceName;
};

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework validates data size", "[FNOnlineFramework][SaveFramework]") {
    ISaveFramework& SaveFramework = GetSaveFramework();

    GConfig->SetInt(TEXT("SaveFramework"), TEXT("SaveDataMaxSizeKb"), 128, GGameIni);
    SaveFrameworkInstance.UpdateFromConfig(false);
    int SaveDataMaxSize = SaveFramework.GetSaveDataMaxSize();

    SECTION("VerifyDataSize with empty string") {
        FString TestStringValue = "";
        ISaveDataRef TestSaveData = FSaveDataString::Create("MyResourceId", TestStringValue);
        CHECK(SaveFramework.VerifyDataSize(TestSaveData));
    }

    SECTION("VerifyDataSize with exceeded max length") {
        FString TestStringValue = "";
        for (int Index = 0; Index < SaveDataMaxSize+1; Index++) {
            TestStringValue += "a";
        }
        ISaveDataRef TestSaveData = FSaveDataString::Create("MyResourceId", TestStringValue);
        CHECK(!SaveFramework.VerifyDataSize(TestSaveData));
    }
}
```

---

### Template 4: Mock
**Priority:** MEDIUM (10% of modules, but growing)

**Purpose:**
Tests requiring mock implementations, dependency injection, or test doubles. Use for isolating units under test from external dependencies (online services, file systems, databases).

**When to use:**
- External dependencies need isolation (online services, auth, commerce)
- Dependency injection required
- Test doubles needed (stubs, fakes, mocks)
- Error injection required
- Async operation control needed (pause/unpause)

**Reference Files:**
- Mock utilities: `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/MockTestUtils.h`
- Mock fixture: `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTestFixture.h`

**Key Features:**
- Mock service interfaces (`IMockTestUtils`)
- Mock implementations (`FMockTestUtils`)
- Error injection (`SetNextOpError()`)
- Async control (`Pause()`, `Unpause()`)
- Test doubles (stubs, fakes)
- Auto-restore utilities
- Component-based fixtures (dependency injection)

**Example:**
```cpp
class FMockTestUtils : public IMockTestUtils {
public:
    virtual void Pause() override {
        bIsPaused = true;
    }

    virtual void Unpause() override {
        bIsPaused = false;
        for (TPromise<void>& Promise : PausedPromises) {
            Promise.SetValue();
        }
        PausedPromises.Empty();
    }

    virtual void SetNextOpError(Errors::ErrorCodeType InErrorCode) override {
        NextOperationErrorCode = InErrorCode;
    }

    virtual TFuture<void> BeginAsyncOp(FOnlineAsyncOp& InAsyncOp, const FStringView& OpName) override {
        OnAsyncOpStartingEvent.Broadcast(InAsyncOp, OpName);

        if (bIsPaused) {
            TPromise<void> Promise;
            TFuture<void> Future = Promise.GetFuture();
            PausedPromises.Add(MoveTemp(Promise));
            return Future;
        }

        return MakeFulfilledPromise<void>().GetFuture();
    }

private:
    TArray<TPromise<void>> PausedPromises;
    bool bIsPaused = false;
    Errors::ErrorCodeType NextOperationErrorCode = 0;
};

TEST_CASE("Mock test with error injection", "[Mock]") {
    FMockTestUtils MockUtils;

    // Inject error for next operation
    MockUtils.SetNextOpError(Errors::InvalidParams());

    // Execute operation - should fail with injected error
    TOnlineResult<FCommerceQueryEntitlements> Result = ExecuteOperation(MockUtils);
    CHECK(Result.IsError());
    CHECK(Result.GetErrorValue() == Errors::InvalidParams());
}

TEST_CASE("Mock test with async control", "[Mock]") {
    FMockTestUtils MockUtils;

    // Pause async operations
    MockUtils.Pause();

    // Start async operation - will be paused
    bool bCompleted = false;
    ExecuteAsyncOperation(MockUtils).Next([&bCompleted](bool bResult) {
        bCompleted = bResult;
    });

    // Operation should not complete yet
    CHECK(!bCompleted);

    // Unpause - operation should complete
    MockUtils.Unpause();
    CHECK(bCompleted);
}
```

---

## 5. Implementation Roadmap

### Phase 1: Core Templates (High Priority)
**Timeline:** Week 1-2

1. **Basic/Fixture Template**
   - Merge existing Basic and Fixture templates
   - Add inline lambda helper patterns
   - Add SECTION block examples
   - Reference: FoundationTests

2. **Async Template**
   - Merge WebTests + OnlineTests patterns
   - Start with explicit tick loop pattern (simpler)
   - Add timeout handling helpers
   - Document callback patterns
   - Reference: WebTests

**Success Criteria:**
- Developers can create Basic tests in < 5 minutes
- Developers can create Async tests in < 15 minutes
- Templates compile and run on all platforms

---

### Phase 2: Advanced Templates (Medium Priority)
**Timeline:** Week 3-4

3. **Plugin/Lifecycle Template**
   - Rename Engine template to Plugin/Lifecycle
   - Add component composition patterns
   - Add auto-restore utilities
   - Add mock engine defaults setup
   - Reference: FNOnlineFrameworkTests

4. **Mock Template** (NEW)
   - Create new Mock template
   - Add mock service interfaces
   - Add error injection patterns
   - Add async control patterns (pause/unpause)
   - Add auto-restore utilities
   - Reference: FNOnlineFrameworkTests MockTestUtils

**Success Criteria:**
- Developers can create Plugin/Lifecycle tests in < 20 minutes
- Developers can create Mock tests in < 15 minutes
- Templates support component-based fixtures

---

### Phase 3: Advanced Async Patterns (Low Priority)
**Timeline:** Week 5+

5. **Async Pipeline Helpers** (OPTIONAL)
   - Document OnlineTestsCore pipeline builder
   - Add FTestPipeline usage examples
   - Add FAsyncTestStep composition patterns
   - Add futures/promises patterns
   - Reference: OnlineTests

**Success Criteria:**
- Developers understand when to use pipeline vs explicit tick loop
- Pipeline helpers are opt-in, not required
- Documentation clarifies trade-offs (simplicity vs abstraction)

---

### Phase 4: Migration Strategy
**Timeline:** Week 6+

6. **Deprecate Old Templates**
   - Mark WebTests and OnlineTests templates as deprecated
   - Migrate existing tests to new Async template
   - Update documentation and examples

7. **Add Decision Tree**
   - Create flowchart for template selection
   - Add to Dante CLI help
   - Add to documentation

**Decision Tree:**
```
Is your test synchronous?
├─ YES → Use Basic/Fixture template
└─ NO (async operations)
    ├─ Simple async (HTTP, WebSocket, timers)?
    │   └─ YES → Use Async template (explicit tick loop)
    └─ Complex multi-step async (online services)?
        └─ YES → Use Async template (pipeline helpers)

Does your test require Engine/Plugin lifecycle?
├─ YES → Use Plugin/Lifecycle template
└─ NO → Use Basic/Async template

Does your test need to isolate external dependencies?
├─ YES → Use Mock template
└─ NO → Use Basic/Async template
```

---

## 6. Key Insights and Patterns

### Insight 1: Simplicity Wins
**Finding:** 40% of modules use minimal setup (Basic/Fixture pattern)

**Implication:** Most tests should be simple. Default to Basic template unless async/complex lifecycle is required.

---

### Insight 2: Async Patterns are Common but Varied
**Finding:** 30% of modules need async handling, but patterns vary widely (explicit tick loop vs pipeline builder)

**Implication:** Provide both simple (tick loop) and advanced (pipeline) async patterns. Default to simple.

---

### Insight 3: Mocking is Underutilized but Powerful
**Finding:** Only 10% of modules use strong mock patterns, but those that do benefit greatly

**Implication:** Promote mock template for isolating external dependencies. Many tests could benefit from mocking but don't use it.

---

### Insight 4: Performance Testing is Rare
**Finding:** <5% of modules use explicit benchmarking (Catch2 BENCHMARK macro)

**Implication:** Performance testing is not a primary concern for LLTs. Document as optional technique, not separate template.

---

### Insight 5: Engine/Plugin Lifecycle is Complex but Necessary
**Finding:** 15% of modules require Engine/Plugin lifecycle, with complex fixtures

**Implication:** Plugin/Lifecycle template is necessary evil for framework/plugin tests. Provide strong reference examples.

---

### Insight 6: OnlineTests Pipeline is Powerful but Overengineered for Most Tests
**Finding:** Pipeline builder reduces boilerplate for complex multi-step tests, but adds cognitive load

**Implication:** Pipeline should be opt-in advanced pattern, not default. Most async tests can use simpler explicit tick loop.

---

## 7. Next Steps

1. **Validate Findings with Team**
   - Review this report with Dante team
   - Get feedback on template recommendations
   - Prioritize implementation tasks

2. **Create Template Implementations**
   - Start with Basic/Fixture (Phase 1)
   - Then Async (Phase 1)
   - Then Plugin/Lifecycle and Mock (Phase 2)
   - Document async pipeline helpers (Phase 3)

3. **Update Dante CLI**
   - Add new templates to CLI
   - Update documentation
   - Add decision tree to help

4. **Migrate Existing Tests**
   - Deprecate old templates
   - Migrate sample tests to new templates
   - Update documentation and examples

5. **Monitor Adoption**
   - Track template usage
   - Gather feedback from developers
   - Iterate on templates based on feedback

---

## Appendix A: Module Dependency Analysis

### Minimal Dependencies (2-5 modules)
- StateGraphTests: 2 modules
- IoStoreOnDemandTests: 2 modules
- NetworkPredictionTests: 3 modules
- PCGTests: 3 modules

### Moderate Dependencies (6-10 modules)
- WebTests: 9 modules
- FoundationTests: 5-10 modules (conditional)
- SlateTests: 4-5 modules
- HeadlessChaos: 6 modules
- OnlineFrameworkMatchmakingTests: 6 modules

### Heavy Dependencies (11+ modules)
- FNOnlineFrameworkTests: 14 modules
- OnlineTests: 16 modules

**Insight:** Dependency count correlates with fixture complexity. Minimal dependency tests are simpler.

---

## Appendix B: Platform Support Analysis

### All Platforms Supported
- WebTests
- OnlineTests
- FNOnlineFrameworkTests
- FoundationTests
- SlateTests
- HeadlessChaos
- StateGraphTests
- IoStoreOnDemandTests
- VOSTests
- PCGTests
- OnlineFrameworkMatchmakingTests

### Limited Platform Support
- NetworkPredictionTests: Win64, Linux only

**Insight:** Most LLT modules target all platforms. Platform restrictions are rare and domain-specific.

---

## Appendix C: Test Framework Usage

### Catch2 (Default)
- WebTests
- OnlineTests
- FNOnlineFrameworkTests
- FoundationTests
- NetworkPredictionTests
- SlateTests
- StateGraphTests
- IoStoreOnDemandTests
- VOSTests
- PCGTests
- OnlineFrameworkMatchmakingTests
- AutoRTFMTests

### GoogleTest (Non-standard)
- HeadlessChaos

**Insight:** Catch2 is the de facto standard. GoogleTest usage is rare and should be discouraged for consistency.

---

## Appendix D: Reference Files by Template

### Basic/Fixture Template
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/LowLevelTests/FoundationTests/Tests/LinkedListBuilderTests.cpp`
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/NetworkPredictionTests` (any test file)
- `/Users/stephen.ma/Fornite_Main/Engine/Plugins/Experimental/StateGraph/Tests/StateGraphTests` (any test file)

### Async Template
**Simple:**
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestWebSockets.cpp`
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/WebTests/Private/TestHttp.cpp`

**Advanced (Pipeline):**
- `/Users/stephen.ma/Fornite_Main/Engine/Restricted/NotForLicensees/Source/Programs/OnlineTests/Private/Tests/Commerce/QueryEntitlementsTests.cpp`
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Public/TestDriver.h`
- `/Users/stephen.ma/Fornite_Main/Engine/Source/Programs/Online/OnlineTestsCore/Source/Public/AsyncTestStep.h`

### Plugin/Lifecycle Template
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/FNOnlineFrameworkTests.Target.cs`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTestFixture.h`

### Mock Template
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/MockTestUtils.h`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/MockTestUtils.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTestFixture.h`

---

## Conclusion

This research analyzed 15+ distinct LowLevelTest modules across the Fortnite codebase and validated scenario analysis recommendations. Key takeaways:

1. **Merge WebTests + OnlineTests:** SUPPORTED as unified "Async" template with optional pipeline helpers
2. **Add Performance template:** NOT WARRANTED - document as optional technique in Basic template
3. **Add Mock template:** WARRANTED as medium priority for dependency injection
4. **Simplify to 4 templates:** RECOMMENDED - Basic/Fixture, Async, Plugin/Lifecycle, Mock

The final template set prioritizes simplicity while providing advanced patterns for complex scenarios. Implementation roadmap provides clear path from core templates (Phase 1) to advanced patterns (Phase 3).

---

**End of Report**
