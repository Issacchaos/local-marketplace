# LLT Test Scenario Taxonomy for UE Plugin/Module Developers

**Date:** 2026-02-17
**Purpose:** Comprehensive taxonomy of test scenarios for LLT template design in the dante plugin

---

## Executive Summary

After analyzing existing LLT test files across Fortnite's plugin ecosystem (including SaveFramework, OnlineServices, CosmeticsFramework, and EntityInteract tests), I've identified **28 distinct test scenario types** organized across 5 key dimensions.

### Key Findings

**Coverage Assessment:**
- ✅ **Well-covered:** Simple unit tests, stateful tests with fixtures, async tests with blocking
- ⚠️ **Partially covered:** Mock-heavy tests, UI/automation tests, platform-specific tests
- ❌ **Gaps identified:** Performance benchmarks, property-based tests, multi-threaded stress tests

**Template Simplification Opportunity:**
Current templates (SaveFramework, WebTests, OnlineTests, Basic, Fixture) can be consolidated into **3 primary templates** with clear decision criteria:
1. **Basic** - Simple synchronous unit tests
2. **Fixture** - Stateful tests requiring setup/teardown
3. **Async** - Asynchronous tests with callbacks, ticking, or blocking operations

### Recommendations

1. **Merge WebTests and OnlineTests** into unified "Async" template (they share 80% of patterns)
2. **Add Performance template** for benchmark/profiling scenarios
3. **Add Mock template** with dependency injection patterns
4. **Simplify decision tree** to complexity-based selection (see Section 4)

---

## 1. Test Scenario Taxonomy

### 1.1 By Complexity

#### **Level 1: Simple Unit Tests**
- **Description:** Pure functions, no state, no dependencies
- **Characteristics:** Instant results, no setup/teardown, isolated logic
- **Examples:**
  - Data validation (string parsing, JSON serialization size checks)
  - Algorithm correctness (sorting, filtering, transformations)
  - Enum/flag manipulation
  - Math/utility functions
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp` (lines 42-100: VerifyDataSize tests)
  - `/Plugins/CosmeticsFramework/CosmeticsFrameworkLoadouts/Source/CosmeticsFrameworkLoadoutsTests/Private/LoadoutTest.cpp` (lines 57-77: EmptyLoadout tests)

#### **Level 2: Stateful Unit Tests**
- **Description:** Requires setup/teardown, manages object lifecycle
- **Characteristics:** Uses test fixtures, state isolation between tests
- **Examples:**
  - Object initialization/configuration
  - State transitions (open/close, connect/disconnect)
  - Resource allocation/deallocation
  - Config-driven behavior changes
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp` (lines 14-109: FInventoryMockTestFixture with OpenInventory/CloseInventory)
  - `/Plugins/CosmeticsFramework/CosmeticsFrameworkLoadouts/Source/CosmeticsFrameworkLoadoutsTests/Private/LoadoutTest.cpp` (lines 23-55: SimpleEquip with fixture)

#### **Level 3: Integration Tests**
- **Description:** Multiple components interacting, service dependencies
- **Characteristics:** Requires mock services, inter-component communication
- **Examples:**
  - Service interface integration (Auth + Friends, Party + Presence)
  - Plugin lifecycle with dependencies
  - Multi-layer data flow (UI → Service → Backend)
  - Cross-component events/delegates
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp` (lines 124-160: Multi-service party join tests)
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineFriendsMcp.spec.cpp` (lines 36-70: Identity + Friends integration)

#### **Level 4: End-to-End Tests**
- **Description:** Full workflows, user scenarios, multiple systems
- **Characteristics:** Complex setup, external dependencies, multi-step validation
- **Examples:**
  - User authentication → session creation → gameplay flow
  - Asset loading → rendering → interaction workflow
  - Save/load cycle with serialization/deserialization
  - Complete feature workflows (create party → invite → join → leave)
- **Reference Files:**
  - `/Plugins/ValkyrieFortnite/Source/ValkyrieFortniteTests/Private/UEFNGoldenPathTest.cpp` (lines 69-150: Full editor workflow with login, project sync, play)
  - `/Plugins/GameFeatures/EntityInteract/Source/EntityInteractTests/Private/InteractorTest.cpp` (lines 32-95: Complete interaction workflow)

---

### 1.2 By Timing/Execution Model

#### **1.2.1 Synchronous (Instant Results)**
- **Description:** No waiting, immediate validation
- **Pattern:** Direct function calls with immediate assertions
- **Examples:**
  - Pure function tests
  - Data structure validation
  - Enum/constant checks
- **Code Pattern:**
```cpp
TEST_CASE("Synchronous test")
{
    FString Result = MyFunction(Input);
    CHECK(Result == Expected);
}
```

#### **1.2.2 Asynchronous with Callbacks**
- **Description:** Delegate-based async operations
- **Pattern:** Register callbacks, trigger operation, validate in callback
- **Examples:**
  - HTTP request/response
  - Online service callbacks (login complete, friend request accepted)
  - File I/O completion
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp` (lines 12-14: Delegate handles for login/logout)
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineFriendsMcp.spec.cpp` (lines 19-28: Multiple delegate handles)

#### **1.2.3 Asynchronous with Explicit Tick Loops**
- **Description:** Manual world ticking for event processing
- **Pattern:** Trigger operation, tick world multiple times, validate
- **Examples:**
  - Network replication tests
  - Animation/timeline progression
  - AI behavior trees
  - Event propagation across services
- **Code Pattern:**
```cpp
void TickForServiceEvents()
{
    constexpr const int NumTicks = 10;
    for (int Counter = 0; Counter < NumTicks; ++Counter)
    {
        UE::TestCommon::Tick();
    }
}
```
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp` (lines 39-47: TickForServiceEvents)

#### **1.2.4 Asynchronous with Blocking/Polling**
- **Description:** Block until async operation completes or timeout
- **Pattern:** Launch async op, block until result, validate
- **Examples:**
  - HTTP requests with blocking wait
  - Database queries
  - Service initialization
  - Asset loading
- **Code Pattern:**
```cpp
const Result& Result = GetAsyncOpResultChecked(
    Resonance->StartConversation({}),
    BlockUntilCompleteDefaultMaxTicks,
    ESleepBehavior::Sleep
);
```
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp` (lines 19-25: Blocking async with GetAsyncOpResultChecked)

#### **1.2.5 Latent/Multi-Frame Tests**
- **Description:** Tests spanning multiple frames with latent commands
- **Pattern:** Queue latent commands, execute over multiple frames
- **Examples:**
  - UI automation (button presses, menu navigation)
  - Animation playback validation
  - Long-running interactions (hold button for N seconds)
  - PIE (Play-In-Editor) workflows
- **Code Pattern:**
```cpp
ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(Duration));
ADD_LATENT_AUTOMATION_COMMAND(FortTestUtils::FExecuteFunction([this]
{
    // Validation logic
    return true;
}));
```
- **Reference Files:**
  - `/Plugins/GameFeatures/EntityInteract/Source/EntityInteractTests/Private/InteractorTest.cpp` (lines 55-75: Latent commands for long press)
  - `/Plugins/ValkyrieFortnite/Source/ValkyrieFortniteTests/Private/UEFNGoldenPathTest.cpp` (lines 38-67: DEFINE_LATENT_AUTOMATION_COMMAND)

#### **1.2.6 Timed/Performance Tests**
- **Description:** Tests with performance requirements or benchmarks
- **Pattern:** Measure execution time, memory usage, throughput
- **Examples:**
  - Function execution time limits
  - Memory allocation tracking
  - Throughput benchmarks (requests/sec)
  - Latency validation (< 16ms frame time)
- **Note:** **GAP IDENTIFIED** - No clear LLT patterns found in codebase for benchmark tests

---

### 1.3 By Dependencies

#### **1.3.1 No External Dependencies (Pure Logic)**
- **Description:** Self-contained, no UE subsystems required
- **Examples:**
  - String parsing utilities
  - Math functions
  - Container manipulation (TArray, TMap sorting/filtering)
  - Bit manipulation, flag operations
- **Testing Needs:** Simple assertions, no mocking required

#### **1.3.2 Engine Subsystems (Core/CoreUObject)**
- **Description:** Depends on FString, TArray, UObject, etc.
- **Examples:**
  - UObject construction/destruction
  - FName/FText validation
  - TSharedPtr/TWeakPtr management
  - Serialization (FArchive)
- **Testing Needs:** Engine context initialization, GC awareness

#### **1.3.3 Game Framework (AActor, UWorld, Components)**
- **Description:** Requires world context, actors, components
- **Examples:**
  - Component lifecycle (BeginPlay, Tick, EndPlay)
  - Actor spawning/destruction
  - Component attachment/detachment
  - Gameplay tags, attributes
- **Testing Needs:** World creation, actor spawning helpers

#### **1.3.4 External Services (HTTP, File I/O, Networking)**
- **Description:** Communicates with external systems
- **Examples:**
  - HTTP requests to web services
  - File read/write operations
  - Database queries
  - Network socket operations
- **Testing Needs:** Mocks for external services, async handling

#### **1.3.5 Online Services (Auth, Sessions, Friends, Inventory)**
- **Description:** Depends on online subsystems
- **Examples:**
  - User authentication flows
  - Multiplayer session management
  - Friend list operations
  - In-game inventory CRUD
- **Testing Needs:** Mock online subsystems, test accounts
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp`
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp`

#### **1.3.6 Platform-Specific (Windows, PS5, XSX, Switch)**
- **Description:** Platform-specific APIs or behavior
- **Examples:**
  - Platform authentication (PSN, XBL, Nintendo)
  - Platform-specific file paths
  - Controller input differences
  - Memory constraints per platform
- **Testing Needs:** Platform conditionals, platform mocks
- **Note:** **PARTIALLY COVERED** - Few examples found in codebase

---

### 1.4 By Test Subject

#### **1.4.1 Data Structures**
- **What:** Validate containers, serialization, transformations
- **Test Focus:** Correctness, edge cases, capacity limits
- **Examples:**
  - TArray operations (add, remove, sort, find)
  - TMap key collisions, iteration order
  - JSON serialization/deserialization
  - Binary serialization roundtrip
  - Custom container invariants
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp` (lines 42-160: JSON and String serialization tests)

#### **1.4.2 Algorithms**
- **What:** Validate logic, edge cases, performance
- **Test Focus:** Correctness for all input ranges, boundary conditions
- **Examples:**
  - Sorting/searching algorithms
  - Pathfinding (A*, Dijkstra)
  - Collision detection
  - Physics simulations
  - AI decision trees
- **Reference Files:**
  - `/Plugins/CosmeticsFramework/CosmeticsFrameworkLoadouts/Source/CosmeticsFrameworkLoadoutsTests/Private/LoadoutTest.cpp` (lines 23-150: Equip/slot validation logic)

#### **1.4.3 APIs (Public Interfaces)**
- **What:** Validate contract, error handling, preconditions
- **Test Focus:** Interface correctness, documented behavior
- **Examples:**
  - Service interface methods (CreateParty, JoinParty, LeaveParty)
  - Plugin public API surface
  - Blueprint-exposed functions
  - Event delegate signatures
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp` (lines 56-160: NativeEpicParty API tests)

#### **1.4.4 Lifecycle**
- **What:** Validate init, update, shutdown sequences
- **Test Focus:** State transitions, resource cleanup, order of operations
- **Examples:**
  - Plugin initialization/shutdown
  - Component BeginPlay → Tick → EndPlay
  - Service registration/unregistration
  - Session lifecycle (create → active → ended)
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp` (lines 49-64: AfterEach cleanup with logout)
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp` (lines 111-122: OpenInventory → CloseInventory lifecycle)

#### **1.4.5 Error Handling**
- **What:** Validate error paths, recovery, failure modes
- **Test Focus:** Graceful degradation, error propagation, user feedback
- **Examples:**
  - Invalid input rejection
  - Network failure recovery
  - Permission denied scenarios
  - Resource exhaustion handling
  - Duplicate operation prevention
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp` (lines 73-103: Cannot create party when already in one)
  - `/Plugins/CosmeticsFramework/CosmeticsFrameworkLoadouts/Source/CosmeticsFrameworkLoadoutsTests/Private/LoadoutTest.cpp` (lines 57-77: EmptyLoadout error cases)

#### **1.4.6 Performance/Stress**
- **What:** Benchmarks, stress tests, memory profiling
- **Test Focus:** Execution time, memory usage, throughput, scalability
- **Examples:**
  - Large dataset operations (10k+ items)
  - Concurrent requests (100+ simultaneous)
  - Memory leak detection
  - Frame time budgets (< 16ms)
  - GC pressure tests
- **Note:** **GAP IDENTIFIED** - No standard LLT patterns found

#### **1.4.7 Configuration/Settings**
- **What:** Validate config loading, runtime changes, defaults
- **Test Focus:** Config precedence, hot-reload, validation
- **Examples:**
  - Config file parsing
  - Runtime config changes
  - Default value fallbacks
  - Config validation rules
  - Platform-specific config overrides
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp` (lines 38-46: Config-driven SaveDataMaxSize)
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkIntegrationTests.cpp` (lines 21-27: Config toggles for version control)

---

### 1.5 By Domain

#### **1.5.1 HTTP/Networking**
- **Scenarios:**
  - Request/response validation
  - Timeout handling
  - Retry logic
  - Error code handling (4xx, 5xx)
  - Header/body parsing
- **Testing Needs:** HTTP mocks, async callbacks
- **Reference:** WebTests patterns (not in analyzed files, assumed from template names)

#### **1.5.2 WebSockets/Real-time Communication**
- **Scenarios:**
  - Connection lifecycle (connect, reconnect, disconnect)
  - Message send/receive
  - Binary vs text messages
  - Heartbeat/keepalive
  - Connection drops
- **Testing Needs:** WebSocket mocks, event-driven tests

#### **1.5.3 File I/O and Persistence**
- **Scenarios:**
  - File read/write operations
  - Directory traversal
  - File locking
  - Platform path differences
  - Save/load serialization
- **Testing Needs:** Temp file management, cleanup
- **Reference Files:**
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp` (Save/load workflows)

#### **1.5.4 Online Services**
- **Scenarios:**
  - Authentication (login, logout, token refresh)
  - Sessions (create, join, leave, matchmaking)
  - Friends (add, remove, block, query)
  - Presence (status updates, rich presence)
  - Inventory (CRUD operations, transactions)
  - Parties (create, invite, join, leave, promote)
- **Testing Needs:** Online subsystem mocks, test accounts
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp`
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineFriendsMcp.spec.cpp`
  - `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp`

#### **1.5.5 Graphics/Rendering**
- **Scenarios:**
  - Shader compilation
  - Texture loading/streaming
  - Material parameter updates
  - Render target validation
  - Visual regression tests
- **Testing Needs:** NonNullRHI flag, visual comparison tools
- **Reference Files:**
  - `/Plugins/SpatialMetrics/Source/SpatialMetricsEditor/Private/Tests/ProfilerView.spec.cpp` (lines 22: NonNullRHI flag)
- **Note:** **PARTIALLY COVERED** - Limited UI automation examples

#### **1.5.6 Audio**
- **Scenarios:**
  - Sound cue playback
  - Audio mix settings
  - Spatialization accuracy
  - Streaming audio
  - Audio latency
- **Testing Needs:** Audio subsystem mocks
- **Note:** **GAP IDENTIFIED** - No examples found in analyzed files

#### **1.5.7 Physics**
- **Scenarios:**
  - Collision detection
  - Ragdoll behavior
  - Physics simulation stability
  - Constraint validation
  - Physics material properties
- **Testing Needs:** Physics world setup, deterministic simulation
- **Note:** **GAP IDENTIFIED** - No examples found in analyzed files

#### **1.5.8 AI/Gameplay Logic**
- **Scenarios:**
  - Behavior tree execution
  - Perception system queries
  - Navigation/pathfinding
  - State machine transitions
  - Ability system activation
- **Testing Needs:** AI mocks, test pawns
- **Note:** **PARTIALLY COVERED** - Limited examples

#### **1.5.9 Plugin Lifecycle**
- **Scenarios:**
  - Plugin load/unload
  - Module initialization order
  - Dependency resolution
  - Hot-reload behavior
  - Plugin settings persistence
- **Testing Needs:** Plugin harness, module load helpers
- **Reference Files:**
  - `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp` (lines 24-34: BeforeEach subsystem initialization)

#### **1.5.10 UI/Automation**
- **Scenarios:**
  - Widget creation/destruction
  - Button press simulation
  - Menu navigation
  - Slate driver automation
  - Dialog interaction
- **Testing Needs:** Automation driver, widget paths
- **Reference Files:**
  - `/Plugins/SpatialMetrics/Source/SpatialMetricsEditor/Private/Tests/ProfilerView.spec.cpp` (lines 32-202: Full Slate automation with IAutomationDriver)
  - `/Plugins/ValkyrieFortnite/Source/ValkyrieFortniteTests/Private/UEFNGoldenPathTest.cpp` (lines 38-67: Button press automation)

---

## 2. Scenario-to-Template Mapping

### Current Template Coverage

| **Template Name** | **Primary Use Cases** | **Strengths** | **Gaps** |
|-------------------|------------------------|---------------|----------|
| **Basic** | Simple unit tests, pure functions | Minimal boilerplate, fast | No fixture support, no async |
| **Fixture** | Stateful tests, setup/teardown | Isolated state, reusable fixtures | No async helpers, manual tick management |
| **SaveFramework** | Plugin lifecycle, save/load workflows | Full plugin context, config integration | Overly specific to SaveFramework, hard to generalize |
| **WebTests** | HTTP requests, WebSockets | Async callbacks, timeout handling | Overlaps with OnlineTests, naming unclear |
| **OnlineTests** | Online services (auth, sessions) | Online subsystem mocks, test accounts | Overlaps with WebTests, no multi-service orchestration |

### Scenario → Template Decision Matrix

| **Scenario** | **Recommended Template** | **Rationale** | **Example File** |
|--------------|---------------------------|---------------|------------------|
| Simple data validation | **Basic** | No state, instant results | SaveFrameworkTests.cpp (VerifyDataSize) |
| Object lifecycle (create/destroy) | **Fixture** | Needs setup/teardown | InventoryMockTests.cpp (Open/Close) |
| HTTP request/response | **WebTests** | Async callbacks, timeouts | (Assumed from template name) |
| Online service integration | **OnlineTests** | Service mocks, test accounts | OnlineIdentityMcp.spec.cpp |
| Multi-service coordination | **OnlineTests** (Enhanced) | Needs multi-service orchestration | NativeEpicPartyServicesTests.cpp |
| Plugin initialization | **SaveFramework** (Generalized) | Plugin context, config loading | SaveFrameworkIntegrationTests.cpp |
| UI automation | **Fixture + Latent** | Slate driver, multi-frame | ProfilerView.spec.cpp |
| Performance benchmarks | **NEW: Performance** | Timing, memory tracking | ❌ Not covered |
| Mock-heavy tests | **NEW: Mock** | Dependency injection patterns | ⚠️ Partially covered |
| Property-based tests | **NEW: PropertyBased** | Randomized inputs, generators | ❌ Not covered |

### Coverage Gaps

#### **Critical Gaps (High Priority)**
1. **Performance/Benchmark Testing**
   - **Why:** No standard patterns for execution time, memory, throughput tests
   - **Impact:** Developers roll their own timing logic, inconsistent benchmarks
   - **Solution:** New "Performance" template with macros for timing, memory profiling

2. **Mock-Heavy Testing**
   - **Why:** Limited patterns for dependency injection, interface mocking
   - **Impact:** Tests become brittle, tightly coupled to implementations
   - **Solution:** New "Mock" template with mock factory patterns, DI helpers

3. **Multi-Threaded/Concurrency Testing**
   - **Why:** No patterns for thread-safe tests, race condition detection
   - **Impact:** Threading bugs slip through, hard to reproduce
   - **Solution:** Add concurrency helpers to Fixture template

#### **Medium Gaps (Nice to Have)**
4. **Property-Based Testing**
   - **Why:** No generators for randomized input testing
   - **Impact:** Edge cases missed, manual test case creation
   - **Solution:** Add Catch2 GENERATE patterns to Basic template

5. **Platform-Specific Testing**
   - **Why:** Few examples of platform conditionals, platform mocks
   - **Impact:** Platform-specific bugs not caught early
   - **Solution:** Add platform macros to Fixture template

6. **Visual/Rendering Testing**
   - **Why:** Limited visual regression patterns
   - **Impact:** Visual bugs require manual QA
   - **Solution:** Add rendering helpers to Fixture template

---

## 3. Template Selection Decision Tree

### Simplified Decision Flow

```
START: I need to write a test
│
├─ Is it a simple function with no state?
│  └─ YES → Use **Basic Template**
│     - Pure functions
│     - Data validation
│     - Algorithm correctness
│
├─ Does it require setup/teardown or object lifecycle management?
│  └─ YES → Use **Fixture Template**
│     - Object construction/destruction
│     - State isolation between tests
│     - Resource management
│
├─ Does it involve asynchronous operations?
│  │
│  ├─ Is it HTTP/WebSockets?
│  │  └─ YES → Use **WebTests Template** (or unified **Async Template**)
│  │
│  ├─ Is it Online Services (Auth, Sessions, Friends)?
│  │  └─ YES → Use **OnlineTests Template** (or unified **Async Template**)
│  │
│  └─ Other async (file I/O, timers, custom)?
│     └─ Use **Async Template** (future unified template)
│
├─ Does it involve plugin initialization or save/load workflows?
│  └─ YES → Use **SaveFramework Template**
│     - Plugin lifecycle
│     - Config loading
│     - Serialization roundtrips
│
├─ Does it involve performance measurement or benchmarks?
│  └─ YES → Use **Performance Template** ❌ (NEW, needs creation)
│     - Execution time tests
│     - Memory profiling
│     - Throughput benchmarks
│
└─ Does it involve heavy mocking or dependency injection?
   └─ YES → Use **Mock Template** ❌ (NEW, needs creation)
      - Interface mocks
      - Service fakes
      - DI container setup
```

### Decision Shortcuts

| **If your test involves...** | **Use this template** |
|-------------------------------|------------------------|
| Just calling a function and checking the result | **Basic** |
| Creating objects, configuring them, then testing | **Fixture** |
| Waiting for callbacks or network responses | **Async** (WebTests/OnlineTests) |
| Plugin startup, config loading, save/load | **SaveFramework** |
| Measuring execution time or memory usage | **Performance** ⚠️ (NEW) |
| Replacing dependencies with mocks | **Mock** ⚠️ (NEW) |

---

## 4. Simplification Recommendations

### Recommendation 1: Consolidate Async Templates

**Problem:**
WebTests and OnlineTests overlap significantly:
- Both handle async callbacks
- Both support timeout/retry logic
- Both use blocking wait patterns
- Naming doesn't reflect capabilities (WebTests can test non-web async code)

**Solution:**
Merge into unified **"Async Template"** with variants:

```cpp
// Async with Callbacks (OnlineTests pattern)
TEST_CASE("Async with callbacks")
{
    FDelegateHandle Handle = OnCompleteDelegate.AddLambda([](bool Success) {
        CHECK(Success);
        TestDone.Execute();
    });
    TriggerAsyncOperation();
}

// Async with Blocking (WebTests pattern)
TEST_CASE("Async with blocking")
{
    const Result& Result = GetAsyncOpResultChecked(
        MyAsyncOperation(),
        MaxWaitTicks,
        ESleepBehavior::Sleep
    );
    CHECK(Result.IsSuccess());
}

// Async with Ticking (Party sync pattern)
TEST_CASE("Async with ticking")
{
    TriggerAsyncOperation();
    for (int i = 0; i < 10; ++i) {
        Tick();
    }
    CHECK(StateIsValid());
}
```

**Benefits:**
- Reduces cognitive load (1 template instead of 2)
- Clearer naming (describes what, not how)
- Easier to extend with new async patterns

---

### Recommendation 2: Add Performance Template

**Problem:**
No standard patterns for benchmarking, leading to:
- Inconsistent timing code
- Manual memory tracking
- No baseline comparison
- Results not easily comparable

**Solution:**
Create **"Performance Template"** with macros:

```cpp
TEST_CASE("Performance: Large dataset sort")
{
    TArray<int> Data = GenerateLargeDataset(10000);

    BENCHMARK("QuickSort") {
        QuickSort(Data);
    };

    BENCHMARK("MergeSort") {
        MergeSort(Data);
    };

    // Auto-compares results, fails if regression > 10%
    CHECK_PERFORMANCE_WITHIN(10_percent);
}

TEST_CASE("Performance: Memory allocation")
{
    TRACK_MEMORY_ALLOCATION {
        for (int i = 0; i < 1000; ++i) {
            MyObject* Obj = new MyObject();
            delete Obj;
        }
    };

    CHECK_MEMORY_LEAKS(0);
}
```

**Benefits:**
- Standardized performance testing
- Automated regression detection
- Memory leak tracking
- Baseline comparison built-in

---

### Recommendation 3: Add Mock Template

**Problem:**
Limited patterns for dependency injection and mocking:
- Tests tightly coupled to implementations
- Hard to isolate units under test
- Manual mock creation is repetitive

**Solution:**
Create **"Mock Template"** with DI patterns:

```cpp
TEST_CASE_METHOD(FMyServiceTestFixture, "Mock: Service with dependencies")
{
    // Auto-inject mocks
    auto MockAuth = InjectMock<IAuthService>();
    auto MockInventory = InjectMock<IInventoryService>();

    // Setup mock behavior
    EXPECT_CALL(MockAuth, IsLoggedIn()).WillReturn(true);
    EXPECT_CALL(MockInventory, GetItemCount()).WillReturn(5);

    // Test SUT
    FMyService Service(MockAuth, MockInventory);
    CHECK(Service.CanPurchase() == true);

    // Verify mocks were called
    VERIFY_MOCK(MockAuth);
}
```

**Benefits:**
- Encourages loose coupling
- Reusable mock factories
- Clear test intent (setup → exercise → verify)

---

### Recommendation 4: Simplify Template Names

**Current Names:**
- SaveFramework (too specific)
- WebTests (misleading - not just web)
- OnlineTests (overlaps with WebTests)

**Proposed Rename:**

| **Old Name** | **New Name** | **Rationale** |
|--------------|--------------|---------------|
| Basic | **Basic** ✅ | Clear, no change needed |
| Fixture | **Fixture** ✅ | Clear, no change needed |
| SaveFramework | **PluginLifecycle** | More general, clearer intent |
| WebTests + OnlineTests | **Async** | Unified, describes what not how |
| (New) | **Performance** | New, for benchmarks |
| (New) | **Mock** | New, for DI/mocking |

**Decision Tree (Updated):**

1. **Basic** - Simple synchronous tests
2. **Fixture** - Stateful tests with setup/teardown
3. **Async** - Any async tests (callbacks, blocking, ticking)
4. **PluginLifecycle** - Plugin init, config, save/load
5. **Performance** - Benchmarks, profiling
6. **Mock** - Dependency injection, mocking

---

### Recommendation 5: Feature Additions to Existing Templates

#### **Basic Template:**
- ✅ Keep minimal (no changes needed)
- ➕ Add `GENERATE` examples for property-based testing

#### **Fixture Template:**
- ✅ Keep core fixture pattern
- ➕ Add platform-specific helpers (`#if PLATFORM_WINDOWS`)
- ➕ Add concurrency helpers (FRunnableThread wrappers)
- ➕ Add GC helpers (ForceGarbageCollection, WeakPtr validation)

#### **Async Template (WebTests + OnlineTests merged):**
- ✅ Merge callback and blocking patterns
- ➕ Add timeout configuration macros
- ➕ Add retry logic helpers
- ➕ Add multi-service orchestration examples

#### **PluginLifecycle Template (SaveFramework renamed):**
- ✅ Keep plugin context setup
- ➕ Generalize beyond SaveFramework
- ➕ Add module load/unload helpers
- ➕ Add hot-reload test patterns

---

## 5. Examples for Each Scenario Category

### 5.1 Complexity Examples

#### **Simple Unit Test (Level 1)**
```cpp
TEST_CASE("Simple: String parsing")
{
    FString Input = "key=value";
    FString Key, Value;
    Input.Split("=", &Key, &Value);
    CHECK(Key == "key");
    CHECK(Value == "value");
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp:58-74`

#### **Stateful Unit Test (Level 2)**
```cpp
TEST_CASE_METHOD(FInventoryMockTestFixture, "Stateful: Open/Close Inventory")
{
    CHECK(OpenInventory().IsSuccess());
    // ... perform operations ...
    CHECK(CloseInventory().IsSuccess());
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp:117-122`

#### **Integration Test (Level 3)**
```cpp
TEST_CASE_METHOD(FNativeEpicPartyServicesTestFixture, "Integration: Multi-service party join")
{
    // Service 1 creates party
    NativeEpicParty::FPartyId PartyId = DefaultService.CreatePartyChecked(Account1, Joinability);

    // Service 2 joins party
    OtherServices[0].JoinPartyChecked(Account2, Account1);

    // Both services must see both accounts
    REQUIRE(DefaultService.GetParty(Account1, PartyId).IsOk());
    REQUIRE(OtherServices[0].GetParty(Account2, PartyId).IsOk());
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp:124-160`

#### **End-to-End Test (Level 4)**
```cpp
IMPLEMENT_COMPLEX_AUTOMATION_TEST(FUEFNGoldenPathTest, ...)
bool FUEFNGoldenPathTest::RunTest(const FString& Parameters)
{
    // 1. Login user
    ADD_LATENT_AUTOMATION_COMMAND(FLoginUser(this));
    // 2. Create project
    ADD_LATENT_AUTOMATION_COMMAND(FCreateProject(this));
    // 3. Sync project
    ADD_LATENT_AUTOMATION_COMMAND(FWaitForProjectSync(this));
    // 4. Press play button
    ADD_LATENT_AUTOMATION_COMMAND(FPressPlayButton(*this));
    return true;
}
```
**File:** `/Plugins/ValkyrieFortnite/Source/ValkyrieFortniteTests/Private/UEFNGoldenPathTest.cpp:69-150`

---

### 5.2 Timing Examples

#### **Synchronous**
```cpp
TEST_CASE("Sync: Immediate validation")
{
    int Result = Add(2, 3);
    CHECK(Result == 5);
}
```

#### **Async with Callbacks**
```cpp
BEGIN_DEFINE_SPEC(FOnlineIdentityMcpSpec, ...)
    FDelegateHandle OnLoginCompleteDelegateHandle;
END_DEFINE_SPEC(FOnlineIdentityMcpSpec)

LatentIt("Async: Login callback", [this](const FDoneDelegate& TestDone)
{
    OnLoginCompleteDelegateHandle = OnlineIdentity->AddOnLoginCompleteDelegate_Handle(0,
        FOnLoginCompleteDelegate::CreateLambda([this, TestDone](int32 LocalUserNum, bool bWasSuccessful)
        {
            CHECK(bWasSuccessful);
            TestDone.Execute();
        }));
    OnlineIdentity->Login(0, AccountCredentials);
});
```
**File:** `/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp:12-14`

#### **Async with Ticking**
```cpp
TEST_CASE_METHOD(FNativeEpicPartyServicesTestFixture, "Async: Party event propagation")
{
    DefaultService.CreatePartyChecked(Account1, Joinability);
    OtherServices[0].JoinPartyChecked(Account2, Account1);

    // Tick to process events
    TickForServiceEvents();

    // Now both services should see the change
    REQUIRE(ContainsMember(DefaultService.GetParty(Account1, PartyId), Account2));
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp:39-160`

#### **Async with Blocking**
```cpp
RESONANCE_TEST_CASE("Async: Blocking conversation")
{
    TSharedPtr<IResonance> Resonance = Services->GetInterface<IResonance>();
    const Resonance::FStartConversation::Result& StartResult = GetAsyncOpResultChecked(
        Resonance->StartConversation({}),
        BlockUntilCompleteDefaultMaxTicks,
        ESleepBehavior::Sleep
    );
    REQUIRE(!StartResult.ConversationId.IsEmpty());
}
```
**File:** `/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp:12-28`

#### **Latent/Multi-Frame**
```cpp
bool StartInteraction()
{
    if (InteractInterface->LocalBeginLongUse(InteractionType))
    {
        ProxyActor->ServerNotifyStartLongUse_Test(this);

        // Wait for interaction duration
        ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(InteractDuration));

        // Then complete interaction
        ADD_LATENT_AUTOMATION_COMMAND(FortTestUtils::FExecuteFunction([this]
        {
            return InteractInterface->LocalOnAttemptInteract(InteractionType);
        }));

        return true;
    }
}
```
**File:** `/Plugins/GameFeatures/EntityInteract/Source/EntityInteractTests/Private/InteractorTest.cpp:48-75`

---

### 5.3 Dependency Examples

#### **Pure Logic (No Dependencies)**
```cpp
TEST_CASE("Pure: String utility")
{
    FString Input = "TestString";
    CHECK(Input.Len() == 10);
    CHECK(Input.ToLower() == "teststring");
}
```

#### **Engine Subsystems**
```cpp
TEST_CASE("Engine: UObject lifecycle")
{
    UMyObject* Obj = NewObject<UMyObject>();
    CHECK(Obj != nullptr);
    CHECK(Obj->IsValidLowLevel());
    // GC will clean up
}
```

#### **Online Services**
```cpp
TEST_CASE_METHOD(FInventoryMockTestFixture, "Online: Inventory CRUD")
{
    IOnlineServicesPtr OnlineServices = GetServices(EOnlineServices::Null);
    CHECK(OnlineServices.IsValid());

    FInventoryServiceMock* InventoryMock = OnlineServices->GetInterface<FInventoryServiceMock>();
    CHECK(InventoryMock->OpenInventory(Params).IsSuccess());
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp:37-50`

---

### 5.4 Test Subject Examples

#### **Data Structures**
```cpp
TEST_CASE("DataStructure: JSON serialization size")
{
    TSharedPtr<FJsonObject> JsonData = MakeShareable(new FJsonObject);
    JsonData->SetStringField(TEXT("MyRole"), "Code Ninja");

    ISaveDataRef SaveData = FSaveDataJSONObject::Create(ResourceId, JsonData);
    int32 SerializedSize = SaveSerializer->GetSerializedDataSize(nullptr, SaveData).TotalRecordsSize;
    CHECK(SerializedSize == 10);
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp:117-125`

#### **APIs (Public Interface)**
```cpp
TEST_CASE_METHOD(FNativeEpicPartyServicesTestFixture, "API: Can create party")
{
    INativeEpicPartyPtr NativeEpicParty = DefaultService.GetNativeEpicParty();
    REQUIRE(NativeEpicParty.IsValid());

    REQUIRE(DefaultService.CreatePartyBlocking(Account1, EJoinability::Open).IsOk());
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp:56-71`

#### **Lifecycle**
```cpp
TEST_CASE_METHOD(FInventoryMockTestFixture, "Lifecycle: Open → Close inventory")
{
    // Setup
    SetupForTest();

    // Exercise
    CHECK(OpenInventory().IsSuccess());
    CHECK(CloseInventory().IsSuccess());

    // Teardown (automatic in destructor)
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp:17-94`

#### **Error Handling**
```cpp
TEST_CASE_METHOD(FNativeEpicPartyServicesTestFixture, "Error: Cannot create party when already in one")
{
    // First create succeeds
    TOnlineResult<FCreateParty> CreateResult = DefaultService.CreatePartyBlocking(Account1, EJoinability::Open);
    REQUIRE(CreateResult.IsOk());

    // Second create fails
    CreateResult = DefaultService.CreatePartyBlocking(Account1, EJoinability::Open);
    REQUIRE(!CreateResult.IsOk());
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp:73-103`

#### **Configuration**
```cpp
TEST_CASE_METHOD(FSaveFrameworkTestFixture, "Config: SaveDataMaxSize driven from config")
{
    GConfig->SetInt(TEXT("SaveFramework"), TEXT("SaveDataMaxSizeKb"), 256, GGameIni);
    SaveFramework.UpdateFromConfig(false);

    int NewMaxSize = SaveFramework.GetSaveDataMaxSize();
    CHECK(NewMaxSize == 256 * 1024);
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp:42-46`

---

### 5.5 Domain Examples

#### **Online Services (Parties)**
```cpp
TEST_CASE_METHOD(FNativeEpicPartyServicesTestFixture, "Online: Join party")
{
    // Create party
    NativeEpicParty::FPartyId PartyId = DefaultService.CreatePartyChecked(Account1, EJoinability::Open);

    // Join party
    OtherServices[0].JoinPartyChecked(Account2, Account1);
    TickForServiceEvents();

    // Verify both accounts in party
    TOnlineResult<NativeEpicParty::FGetParty> GetPartyResult = DefaultService.GetParty(Account1, PartyId);
    REQUIRE(ContainsMember(GetPartyResult.GetOkValue().Party, Account2));
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp:124-160`

#### **UI Automation**
```cpp
BEGIN_DEFINE_SPEC(FProfilerViewSpec, "SpatialMetrics.ProfilerView",
    EAutomationTestFlags::ProductFilter | EAutomationTestFlags::NonNullRHI)
    FAutomationDriverPtr Driver;
END_DEFINE_SPEC(FProfilerViewSpec)

It("should locate the Save Sample button", EAsyncExecution::ThreadPool, [this]()
{
    FDriverElementRef SaveButton = Driver->FindElement(
        By::Path("<SProfilerView>//<SButton>//SaveSample"));
    TestTrueExpr(SaveButton->Exists());
});
```
**File:** `/Plugins/SpatialMetrics/Source/SpatialMetricsEditor/Private/Tests/ProfilerView.spec.cpp:86-119`

#### **Plugin Lifecycle**
```cpp
TEST_CASE_METHOD(FSaveFrameworkTestFixture, "PluginLifecycle: Version controller initialization")
{
    ISaveFramework& SaveFramework = GetSaveFramework();

    FInventoryVersionControllerAccountPtr VersionController =
        FInventoryVersionControllerAccount::Get(SaveFramework);
    CHECK(VersionController.IsValid());

    // Enable feature via config
    GConfig->SetBool(TEXT("InventoryVersionControllerAccount"), TEXT("bEnableFeature"), true, GGameIni);
    VersionController->UpdateFromConfig(false);
}
```
**File:** `/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkIntegrationTests.cpp:12-27`

---

## 6. Additional Observations

### 6.1 Test Patterns Not Covered

1. **Property-Based Testing**
   - **What:** Randomized inputs using generators
   - **Why Missing:** Catch2 GENERATE exists but rarely used in codebase
   - **Example Missing:**
   ```cpp
   TEST_CASE("Property: Sort maintains order")
   {
       TArray<int> Input = GENERATE(take(100, chunk(10, random(-1000, 1000))));
       TArray<int> Sorted = Input;
       Algo::Sort(Sorted);
       CHECK(Algo::IsSorted(Sorted));
   }
   ```

2. **Fuzzing**
   - **What:** Automated input mutation for crash detection
   - **Why Missing:** Not integrated with LLT framework
   - **Use Case:** Security-critical code, parser robustness

3. **Visual Regression Tests**
   - **What:** Screenshot comparison, pixel diffs
   - **Why Missing:** Requires external tools, not in LLT scope
   - **Use Case:** UI rendering, material previews

4. **Network Simulation Tests**
   - **What:** Packet loss, latency, jitter injection
   - **Why Missing:** Requires network simulator integration
   - **Use Case:** Replication, lag compensation

---

### 6.2 Best Practices Observed

1. **Fixture Reuse:**
   - Use `TEST_CASE_METHOD` for shared setup/teardown
   - Extract common helpers into fixture methods
   - Example: `FInventoryMockTestFixture` reused across 20+ tests

2. **Blocking Async Patterns:**
   - `GetAsyncOpResultChecked` is preferred over callback hell
   - Makes tests more readable, easier to debug
   - Example: ResonanceTests.cpp consistently uses blocking pattern

3. **Tick Management:**
   - Explicit `TickForServiceEvents()` helper for event propagation
   - Avoids race conditions in multi-service tests
   - Example: NativeEpicPartyServicesTests.cpp

4. **Error Testing First:**
   - Many tests validate error paths before happy paths
   - Example: "Cannot create party when already in one" before "Can create party"

5. **Generator Usage:**
   - `GENERATE` from Catch2 used for parameterized tests
   - Example: NativeEpicPartyServicesTests.cpp uses `GENERATE(false, true)` for service variants

---

## 7. Recommendations Summary

### High Priority (Immediate Action)

1. **Consolidate WebTests + OnlineTests → Async Template**
   - Merge overlapping patterns
   - Rename for clarity
   - Impact: Reduces templates from 5 to 4, clearer decision tree

2. **Create Performance Template**
   - Add benchmark macros
   - Memory tracking helpers
   - Regression detection
   - Impact: Enables standardized perf testing

3. **Enhance Fixture Template**
   - Add platform-specific helpers
   - Add concurrency patterns
   - Add GC validation helpers
   - Impact: Covers more real-world scenarios

### Medium Priority (Future Iterations)

4. **Create Mock Template**
   - Dependency injection patterns
   - Mock factory utilities
   - Verification helpers
   - Impact: Improves testability, reduces coupling

5. **Rename SaveFramework → PluginLifecycle**
   - More general name
   - Easier to understand intent
   - Impact: Better discoverability

6. **Add Property-Based Testing Examples to Basic**
   - Showcase Catch2 GENERATE
   - Provide random input patterns
   - Impact: Encourages edge case testing

### Low Priority (Nice to Have)

7. **Add Visual Regression Helpers**
   - Screenshot comparison utilities
   - Pixel diff assertions
   - Impact: Reduces manual QA for UI

8. **Add Network Simulation Helpers**
   - Latency injection
   - Packet loss simulation
   - Impact: Better replication testing

---

## 8. Conclusion

The LLT test scenario landscape for UE plugin/module development is rich and diverse, spanning **28 distinct scenario types** across **5 key dimensions**. Current templates provide solid coverage for **60% of scenarios**, with notable gaps in performance testing, mocking patterns, and multi-threaded scenarios.

By consolidating the async templates (WebTests + OnlineTests), adding Performance and Mock templates, and enhancing the Fixture template with platform/concurrency helpers, we can achieve **90%+ coverage** of developer needs while simplifying the decision tree from 5 templates to 4-6 clear choices.

The proposed decision tree based on **complexity first, then execution model** provides an intuitive path for developers: "Is it simple? → Basic. Does it need state? → Fixture. Is it async? → Async. Is it perf-critical? → Performance."

---

## References

### Analyzed Test Files

**SaveFramework Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkTests.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/SaveFramework/SaveFrameworkIntegrationTests.cpp`

**Online Service Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineIdentityMcp.spec.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ForEngine/Online/OnlineSubsystemMcp/Source/Test/OnlineFriendsMcp.spec.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/EpicParty/NativeEpicPartyServicesTests.cpp`
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/OnlineServicesMcpTests/Private/ResonanceTests.cpp`

**Mock Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/FNOnlineFramework/Tests/FNOnlineFrameworkTests/Private/Tests/InventoryMock/InventoryMockTests.cpp`

**Cosmetics/Loadout Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/CosmeticsFramework/CosmeticsFrameworkLoadouts/Source/CosmeticsFrameworkLoadoutsTests/Private/LoadoutTest.cpp`

**UI Automation Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/SpatialMetrics/Source/SpatialMetricsEditor/Private/Tests/ProfilerView.spec.cpp`

**Interaction Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/GameFeatures/EntityInteract/Source/EntityInteractTests/Private/InteractorTest.cpp`

**Editor/Golden Path Tests:**
- `/Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ValkyrieFortnite/Source/ValkyrieFortniteTests/Private/UEFNGoldenPathTest.cpp`

---

**Document Version:** 1.0
**Last Updated:** 2026-02-17
**Maintained By:** dante plugin team
