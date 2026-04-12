# Mock LLT Template (Dependency Injection Pattern)

**Purpose**: Template for generating Mock-based Low-Level Tests with dependency injection and test doubles for Unreal Engine
**Target Language**: C++
**Test Framework**: Catch2 (v3.x) with Mock pattern
**Version Support**: Catch2 3.4.0+, C++17+, UE 5.x

## Overview

This template provides copy-paste ready test patterns for Mock-based Low-Level Tests in Unreal Engine. It supports the mock service interface pattern used in FNOnlineFramework testing, featuring dependency injection, error injection utilities, async control methods, and test doubles. Approximately 10% of LLT modules use this pattern (growing usage for plugin testing).

## Template Structure

### Mock Test File Template

```cpp

/**
 * Mock tests for {{UE_MODULE_NAME}}.
 *
 * Test coverage:
 * - {{TEST_COVERAGE_AREA_1}}
 * - {{TEST_COVERAGE_AREA_2}}
 * - {{TEST_COVERAGE_AREA_3}}
 *
 * Mock Pattern: Dependency injection with test doubles for external services.
 */

#include "CoreMinimal.h"
#include "TestHarness.h"

#include "catch2/generators/catch_generators.hpp"
#include "{{UE_HEADER_PATH}}"
{{MOCK_INCLUDES}}

using namespace UE::{{NAMESPACE}};

// ============================================================================
// Mock Interface and Implementation
// ============================================================================

{{MOCK_INTERFACE}}

{{MOCK_IMPL}}

// ============================================================================
// Test Fixture with Dependency Injection
// ============================================================================

{{TEST_FIXTURE}}

// ============================================================================
// Test Cases: {{UE_MODULE_NAME}}
// ============================================================================

{{TEST_CASES}}
```

## Template Placeholders

### Module-Level Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{UE_MODULE_NAME}}` | Module under test | `SaveFramework`, `OnlineServices`, `PartyManager` |
| `{{TEST_COVERAGE_AREA_N}}` | Areas of functionality covered | `Error injection`, `Async control`, `Service mocking` |
| `{{UE_HEADER_PATH}}` | Header file being tested | `SaveFramework/SaveFramework.h`, `Online/Party.h` |
| `{{NAMESPACE}}` | UE namespace | `Online`, `SaveFramework`, `Party` |
| `{{MOCK_INCLUDES}}` | Additional mock-specific includes | Helper headers, mock utilities |

### Mock Pattern Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{MOCK_INTERFACE}}` | Mock service interface definition | `IMockTestUtils` with virtual methods |
| `{{MOCK_IMPL}}` | Mock service implementation | `FMockTestUtils` concrete class |
| `{{ERROR_INJECTION}}` | Error injection method pattern | `SetNextOpError()`, `InjectFailure()` |
| `{{TEST_DOUBLE}}` | Test double/stub pattern | Fake service implementations |
| `{{TEST_FIXTURE}}` | Component-based fixture with DI | Fixture accepting mock instances via constructor |

### Test Structure Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_CASES}}` | Individual test case definitions | TEST_CASE_METHOD with mock fixture |
| `{{SETUP_CODE}}` | Fixture initialization code | Create mocks, inject dependencies |
| `{{CODE_UNDER_TEST}}` | Code being tested | Method calls on component under test |
| `{{ASSERTIONS}}` | Verification code | REQUIRE() checks, mock verification |

## Mock Interface Pattern

### Mock Service Interface Definition

```cpp
/**
 * Mock interface for {{SERVICE_NAME}}.
 *
 * Provides test doubles and control methods for testing {{UE_MODULE_NAME}}.
 */
class {{MOCK_INTERFACE_NAME}}
{
public:
    virtual ~{{MOCK_INTERFACE_NAME}}() = default;

    // ========================================================================
    // Service API (Test Doubles)
    // ========================================================================

    {{SERVICE_METHODS}}

    // ========================================================================
    // Test Control Methods
    // ========================================================================

    /**
     * Inject error for next operation.
     * @param ErrorCode Error to return on next call
     */
    virtual void SetNextOpError({{ERROR_TYPE}} ErrorCode) = 0;

    /**
     * Pause async operations (for testing timing).
     */
    virtual void Pause() = 0;

    /**
     * Resume async operations.
     */
    virtual void Unpause() = 0;

    /**
     * Reset mock state.
     */
    virtual void Reset() = 0;
};
```

**Example:**

```cpp
/**
 * Mock interface for Save Service testing.
 *
 * Provides test doubles and control methods for SaveFramework tests.
 */
class IMockSaveService
{
public:
    virtual ~IMockSaveService() = default;

    // ========================================================================
    // Service API (Test Doubles)
    // ========================================================================

    /**
     * Mock save operation.
     * @return Result with success/error injected by test
     */
    virtual TOnlineResult<FSaveData> SaveData(const FSaveRequest& Request) = 0;

    /**
     * Mock load operation.
     * @return Result with success/error injected by test
     */
    virtual TOnlineResult<FSaveData> LoadData(const FLoadRequest& Request) = 0;

    // ========================================================================
    // Test Control Methods
    // ========================================================================

    /**
     * Inject error for next operation.
     * @param ErrorCode Error to return on next call
     */
    virtual void SetNextOpError(EOnlineServicesError ErrorCode) = 0;

    /**
     * Pause async operations (for testing timing).
     */
    virtual void Pause() = 0;

    /**
     * Resume async operations.
     */
    virtual void Unpause() = 0;

    /**
     * Reset mock state (clear errors, unpause, reset counters).
     */
    virtual void Reset() = 0;
};
```

## Mock Implementation Pattern

### Mock Service Implementation

```cpp
/**
 * Mock implementation of {{MOCK_INTERFACE_NAME}}.
 *
 * Concrete test double with error injection and async control.
 */
class {{MOCK_IMPL_NAME}} : public {{MOCK_INTERFACE_NAME}}
{
public:
    {{MOCK_IMPL_NAME}}()
        : NextError({{ERROR_DEFAULT}})
        , bPaused(false)
        , CallCount(0)
    {}

    // ========================================================================
    // Service API Implementation (Test Doubles)
    // ========================================================================

    {{SERVICE_METHOD_IMPLEMENTATIONS}}

    // ========================================================================
    // Test Control Implementation
    // ========================================================================

    virtual void SetNextOpError({{ERROR_TYPE}} ErrorCode) override
    {
        NextError = ErrorCode;
    }

    virtual void Pause() override
    {
        bPaused = true;
    }

    virtual void Unpause() override
    {
        bPaused = false;
    }

    virtual void Reset() override
    {
        NextError = {{ERROR_DEFAULT}};
        bPaused = false;
        CallCount = 0;
        {{RESET_ADDITIONAL_STATE}}
    }

    // ========================================================================
    // Mock State (Test Inspection)
    // ========================================================================

    int32 GetCallCount() const { return CallCount; }
    bool IsPaused() const { return bPaused; }

private:
    {{ERROR_TYPE}} NextError;
    bool bPaused;
    int32 CallCount;
    {{MOCK_STATE_MEMBERS}}
};
```

**Example:**

```cpp
/**
 * Mock implementation of IMockSaveService.
 *
 * Concrete test double with error injection and async control.
 */
class FMockSaveService : public IMockSaveService
{
public:
    FMockSaveService()
        : NextError(EOnlineServicesError::Success)
        , bPaused(false)
        , SaveCallCount(0)
        , LoadCallCount(0)
    {}

    // ========================================================================
    // Service API Implementation (Test Doubles)
    // ========================================================================

    virtual TOnlineResult<FSaveData> SaveData(const FSaveRequest& Request) override
    {
        SaveCallCount++;

        // Check for paused state
        if (bPaused)
        {
            // In real test, you might block here or defer completion
            return TOnlineResult<FSaveData>(EOnlineServicesError::RequestPending);
        }

        // Check for error injection
        if (NextError != EOnlineServicesError::Success)
        {
            EOnlineServicesError Error = NextError;
            NextError = EOnlineServicesError::Success; // Consume error
            return TOnlineResult<FSaveData>(Error);
        }

        // Happy path - return mock data
        FSaveData MockData;
        MockData.DataId = Request.DataId;
        MockData.Data = Request.Data;
        return TOnlineResult<FSaveData>(MockData);
    }

    virtual TOnlineResult<FSaveData> LoadData(const FLoadRequest& Request) override
    {
        LoadCallCount++;

        // Check for paused state
        if (bPaused)
        {
            return TOnlineResult<FSaveData>(EOnlineServicesError::RequestPending);
        }

        // Check for error injection
        if (NextError != EOnlineServicesError::Success)
        {
            EOnlineServicesError Error = NextError;
            NextError = EOnlineServicesError::Success; // Consume error
            return TOnlineResult<FSaveData>(Error);
        }

        // Happy path - return mock data
        FSaveData MockData;
        MockData.DataId = Request.DataId;
        MockData.Data = TEXT("Mock saved data");
        return TOnlineResult<FSaveData>(MockData);
    }

    // ========================================================================
    // Test Control Implementation
    // ========================================================================

    virtual void SetNextOpError(EOnlineServicesError ErrorCode) override
    {
        NextError = ErrorCode;
    }

    virtual void Pause() override
    {
        bPaused = true;
    }

    virtual void Unpause() override
    {
        bPaused = false;
    }

    virtual void Reset() override
    {
        NextError = EOnlineServicesError::Success;
        bPaused = false;
        SaveCallCount = 0;
        LoadCallCount = 0;
    }

    // ========================================================================
    // Mock State (Test Inspection)
    // ========================================================================

    int32 GetSaveCallCount() const { return SaveCallCount; }
    int32 GetLoadCallCount() const { return LoadCallCount; }
    bool IsPaused() const { return bPaused; }

private:
    EOnlineServicesError NextError;
    bool bPaused;
    int32 SaveCallCount;
    int32 LoadCallCount;
};
```

## Dependency Injection Test Fixture

### Component-Based Fixture Pattern

```cpp
/**
 * Test fixture for {{UE_MODULE_NAME}} with dependency injection.
 *
 * Fixture creates mock services and injects them into the component under test.
 * This allows testing in isolation without real service dependencies.
 */
class {{FIXTURE_CLASS_NAME}}
{
public:
    {{FIXTURE_CLASS_NAME}}()
    {
        // Create mock services
        {{CREATE_MOCKS}}

        // Inject mocks into component under test
        {{INJECT_DEPENDENCIES}}

        // Perform additional setup
        {{ADDITIONAL_SETUP}}
    }

    ~{{FIXTURE_CLASS_NAME}}()
    {
        // Cleanup
        {{CLEANUP_CODE}}
    }

    // ========================================================================
    // Test Utilities
    // ========================================================================

    {{UTILITY_METHODS}}

    // ========================================================================
    // Mock Access
    // ========================================================================

    {{MOCK_ACCESSOR_METHODS}}

protected:
    // Component under test
    {{COMPONENT_UNDER_TEST_TYPE}} ComponentUnderTest;

    // Mock services
    {{MOCK_SERVICE_MEMBERS}}

    // Test state
    {{TEST_STATE_MEMBERS}}
};
```

**Example:**

```cpp
/**
 * Test fixture for SaveFramework with dependency injection.
 *
 * Fixture creates mock save service and injects it into SaveFramework.
 * This allows testing SaveFramework in isolation without real backend.
 */
class FSaveFrameworkTestFixture
{
public:
    FSaveFrameworkTestFixture()
    {
        // Create mock save service
        MockSaveService = MakeShared<FMockSaveService>();

        // Create SaveFramework with mock service injected
        SaveFramework = MakeShared<FSaveFramework>(MockSaveService);

        // Initialize framework
        SaveFramework->Initialize();
    }

    ~FSaveFrameworkTestFixture()
    {
        // Cleanup
        if (SaveFramework)
        {
            SaveFramework->Shutdown();
        }
    }

    // ========================================================================
    // Test Utilities
    // ========================================================================

    /**
     * Save data with the framework.
     */
    TOnlineResult<FSaveData> SaveData(const FString& DataId, const FString& Data)
    {
        FSaveRequest Request;
        Request.DataId = DataId;
        Request.Data = Data;
        return SaveFramework->SaveData(Request);
    }

    /**
     * Load data with the framework.
     */
    TOnlineResult<FSaveData> LoadData(const FString& DataId)
    {
        FLoadRequest Request;
        Request.DataId = DataId;
        return SaveFramework->LoadData(Request);
    }

    /**
     * Inject error for next operation.
     */
    void InjectError(EOnlineServicesError ErrorCode)
    {
        MockSaveService->SetNextOpError(ErrorCode);
    }

    /**
     * Pause async operations.
     */
    void PauseAsync()
    {
        MockSaveService->Pause();
    }

    /**
     * Resume async operations.
     */
    void ResumeAsync()
    {
        MockSaveService->Unpause();
    }

    /**
     * Reset mock state.
     */
    void ResetMock()
    {
        MockSaveService->Reset();
    }

    // ========================================================================
    // Mock Access
    // ========================================================================

    TSharedPtr<FMockSaveService> GetMockSaveService() const
    {
        return MockSaveService;
    }

    TSharedPtr<FSaveFramework> GetSaveFramework() const
    {
        return SaveFramework;
    }

protected:
    // Component under test
    TSharedPtr<FSaveFramework> SaveFramework;

    // Mock services
    TSharedPtr<FMockSaveService> MockSaveService;
};
```

## TEST_CASE_METHOD Pattern

### Basic Mock Test Case

```cpp
TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{TEST_DESCRIPTION}}", "[{{MODULE_TAG}}][{{FEATURE_TAG}}]")
{
    // Arrange
    {{SETUP_CODE}}

    // Act
    {{CODE_UNDER_TEST}}

    // Assert
    {{ASSERTIONS}}
}
```

**Example:**

```cpp
TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData succeeds with mock service", "[SaveFramework][Save]")
{
    // Arrange
    FString DataId = TEXT("TestData");
    FString Data = TEXT("Test content");

    // Act
    TOnlineResult<FSaveData> Result = SaveData(DataId, Data);

    // Assert
    REQUIRE(Result.IsOk());
    REQUIRE(Result.GetOkValue().DataId == DataId);
    REQUIRE(Result.GetOkValue().Data == Data);
    REQUIRE(GetMockSaveService()->GetSaveCallCount() == 1);
}
```

## Error Injection Pattern

### Testing Error Paths with Mock

```cpp
TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{TEST_DESCRIPTION}} - error injection", "[{{MODULE_TAG}}][{{FEATURE_TAG}}][error]")
{
    SECTION("{{ERROR_SCENARIO_1}}")
    {
        // Arrange - Inject error
        InjectError({{ERROR_CODE_1}});

        // Act
        {{CODE_UNDER_TEST}}

        // Assert - Verify error handling
        {{ERROR_ASSERTIONS}}
    }

    SECTION("{{ERROR_SCENARIO_2}}")
    {
        // Arrange - Inject different error
        InjectError({{ERROR_CODE_2}});

        // Act
        {{CODE_UNDER_TEST}}

        // Assert - Verify error handling
        {{ERROR_ASSERTIONS}}
    }

    SECTION("{{RECOVERY_SCENARIO}}")
    {
        // Arrange - Inject error, then clear
        InjectError({{ERROR_CODE}});
        {{CODE_UNDER_TEST}} // First call fails
        ResetMock(); // Clear error

        // Act - Retry after error cleared
        {{CODE_UNDER_TEST}}

        // Assert - Verify recovery
        {{RECOVERY_ASSERTIONS}}
    }
}
```

**Example:**

```cpp
TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData handles errors correctly", "[SaveFramework][Save][error]")
{
    SECTION("Network error is propagated")
    {
        // Arrange - Inject network error
        InjectError(EOnlineServicesError::NetworkError);

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert - Verify error propagation
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::NetworkError);
    }

    SECTION("Permission error is propagated")
    {
        // Arrange - Inject permission error
        InjectError(EOnlineServicesError::AccessDenied);

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert - Verify error propagation
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::AccessDenied);
    }

    SECTION("Recovery after error")
    {
        // Arrange - Inject error, then clear
        InjectError(EOnlineServicesError::NetworkError);
        TOnlineResult<FSaveData> FailResult = SaveData(TEXT("TestData"), TEXT("Content"));
        REQUIRE(FailResult.IsError());
        ResetMock(); // Clear error

        // Act - Retry after error cleared
        TOnlineResult<FSaveData> SuccessResult = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert - Verify recovery
        REQUIRE(SuccessResult.IsOk());
        REQUIRE(GetMockSaveService()->GetSaveCallCount() == 2);
    }
}
```

## Async Control Pattern

### Testing Async Timing with Mock

```cpp
TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{TEST_DESCRIPTION}} - async control", "[{{MODULE_TAG}}][{{FEATURE_TAG}}][async]")
{
    SECTION("{{ASYNC_SCENARIO_1}}")
    {
        // Arrange - Pause async operations
        PauseAsync();

        // Act - Operation should not complete
        {{CODE_UNDER_TEST}}

        // Assert - Verify pending state
        {{PENDING_ASSERTIONS}}

        // Resume and verify completion
        ResumeAsync();
        {{COMPLETION_CODE}}
        {{COMPLETION_ASSERTIONS}}
    }

    SECTION("{{ASYNC_SCENARIO_2}}")
    {
        // Arrange - Normal async flow
        {{SETUP_CODE}}

        // Act
        {{CODE_UNDER_TEST}}

        // Assert - Verify immediate completion
        {{IMMEDIATE_ASSERTIONS}}
    }
}
```

**Example:**

```cpp
TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData async control", "[SaveFramework][Save][async]")
{
    SECTION("Paused operation returns pending")
    {
        // Arrange - Pause async operations
        PauseAsync();

        // Act - Operation should not complete
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert - Verify pending state
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::RequestPending);

        // Resume and verify completion (in real test, would need to poll or use callback)
        ResumeAsync();
        TOnlineResult<FSaveData> ResumedResult = SaveData(TEXT("TestData"), TEXT("Content"));
        REQUIRE(ResumedResult.IsOk());
    }

    SECTION("Normal async flow completes immediately")
    {
        // Arrange - Ensure not paused
        ResetMock();

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert - Verify immediate completion
        REQUIRE(Result.IsOk());
    }
}
```

## Complete Mock Test Example

```cpp

/**
 * Mock tests for SaveFramework.
 *
 * Test coverage:
 * - Save/Load operations with mock service
 * - Error injection and error handling
 * - Async control and timing
 *
 * Mock Pattern: Dependency injection with test doubles for save service.
 */

#include "CoreMinimal.h"
#include "TestHarness.h"

#include "catch2/generators/catch_generators.hpp"
#include "SaveFramework/SaveFramework.h"

using namespace UE::SaveFramework;

// ============================================================================
// Mock Interface and Implementation
// ============================================================================

/**
 * Mock interface for Save Service testing.
 */
class IMockSaveService
{
public:
    virtual ~IMockSaveService() = default;

    virtual TOnlineResult<FSaveData> SaveData(const FSaveRequest& Request) = 0;
    virtual TOnlineResult<FSaveData> LoadData(const FLoadRequest& Request) = 0;

    virtual void SetNextOpError(EOnlineServicesError ErrorCode) = 0;
    virtual void Pause() = 0;
    virtual void Unpause() = 0;
    virtual void Reset() = 0;
};

/**
 * Mock implementation of IMockSaveService.
 */
class FMockSaveService : public IMockSaveService
{
public:
    FMockSaveService()
        : NextError(EOnlineServicesError::Success)
        , bPaused(false)
        , SaveCallCount(0)
        , LoadCallCount(0)
    {}

    virtual TOnlineResult<FSaveData> SaveData(const FSaveRequest& Request) override
    {
        SaveCallCount++;

        if (bPaused)
        {
            return TOnlineResult<FSaveData>(EOnlineServicesError::RequestPending);
        }

        if (NextError != EOnlineServicesError::Success)
        {
            EOnlineServicesError Error = NextError;
            NextError = EOnlineServicesError::Success;
            return TOnlineResult<FSaveData>(Error);
        }

        FSaveData MockData;
        MockData.DataId = Request.DataId;
        MockData.Data = Request.Data;
        return TOnlineResult<FSaveData>(MockData);
    }

    virtual TOnlineResult<FSaveData> LoadData(const FLoadRequest& Request) override
    {
        LoadCallCount++;

        if (bPaused)
        {
            return TOnlineResult<FSaveData>(EOnlineServicesError::RequestPending);
        }

        if (NextError != EOnlineServicesError::Success)
        {
            EOnlineServicesError Error = NextError;
            NextError = EOnlineServicesError::Success;
            return TOnlineResult<FSaveData>(Error);
        }

        FSaveData MockData;
        MockData.DataId = Request.DataId;
        MockData.Data = TEXT("Mock saved data");
        return TOnlineResult<FSaveData>(MockData);
    }

    virtual void SetNextOpError(EOnlineServicesError ErrorCode) override
    {
        NextError = ErrorCode;
    }

    virtual void Pause() override
    {
        bPaused = true;
    }

    virtual void Unpause() override
    {
        bPaused = false;
    }

    virtual void Reset() override
    {
        NextError = EOnlineServicesError::Success;
        bPaused = false;
        SaveCallCount = 0;
        LoadCallCount = 0;
    }

    int32 GetSaveCallCount() const { return SaveCallCount; }
    int32 GetLoadCallCount() const { return LoadCallCount; }

private:
    EOnlineServicesError NextError;
    bool bPaused;
    int32 SaveCallCount;
    int32 LoadCallCount;
};

// ============================================================================
// Test Fixture with Dependency Injection
// ============================================================================

/**
 * Test fixture for SaveFramework with dependency injection.
 */
class FSaveFrameworkTestFixture
{
public:
    FSaveFrameworkTestFixture()
    {
        MockSaveService = MakeShared<FMockSaveService>();
        SaveFramework = MakeShared<FSaveFramework>(MockSaveService);
        SaveFramework->Initialize();
    }

    ~FSaveFrameworkTestFixture()
    {
        if (SaveFramework)
        {
            SaveFramework->Shutdown();
        }
    }

    TOnlineResult<FSaveData> SaveData(const FString& DataId, const FString& Data)
    {
        FSaveRequest Request;
        Request.DataId = DataId;
        Request.Data = Data;
        return SaveFramework->SaveData(Request);
    }

    TOnlineResult<FSaveData> LoadData(const FString& DataId)
    {
        FLoadRequest Request;
        Request.DataId = DataId;
        return SaveFramework->LoadData(Request);
    }

    void InjectError(EOnlineServicesError ErrorCode)
    {
        MockSaveService->SetNextOpError(ErrorCode);
    }

    void PauseAsync()
    {
        MockSaveService->Pause();
    }

    void ResumeAsync()
    {
        MockSaveService->Unpause();
    }

    void ResetMock()
    {
        MockSaveService->Reset();
    }

    TSharedPtr<FMockSaveService> GetMockSaveService() const
    {
        return MockSaveService;
    }

protected:
    TSharedPtr<FSaveFramework> SaveFramework;
    TSharedPtr<FMockSaveService> MockSaveService;
};

// ============================================================================
// Test Cases: SaveFramework
// ============================================================================

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData succeeds with mock service", "[SaveFramework][Save]")
{
    // Arrange
    FString DataId = TEXT("TestData");
    FString Data = TEXT("Test content");

    // Act
    TOnlineResult<FSaveData> Result = SaveData(DataId, Data);

    // Assert
    REQUIRE(Result.IsOk());
    REQUIRE(Result.GetOkValue().DataId == DataId);
    REQUIRE(Result.GetOkValue().Data == Data);
    REQUIRE(GetMockSaveService()->GetSaveCallCount() == 1);
}

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::LoadData succeeds with mock service", "[SaveFramework][Load]")
{
    // Arrange
    FString DataId = TEXT("TestData");

    // Act
    TOnlineResult<FSaveData> Result = LoadData(DataId);

    // Assert
    REQUIRE(Result.IsOk());
    REQUIRE(Result.GetOkValue().DataId == DataId);
    REQUIRE(GetMockSaveService()->GetLoadCallCount() == 1);
}

// ============================================================================
// Error Injection Tests
// ============================================================================

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData handles errors correctly", "[SaveFramework][Save][error]")
{
    SECTION("Network error is propagated")
    {
        // Arrange
        InjectError(EOnlineServicesError::NetworkError);

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::NetworkError);
    }

    SECTION("Permission error is propagated")
    {
        // Arrange
        InjectError(EOnlineServicesError::AccessDenied);

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::AccessDenied);
    }

    SECTION("Recovery after error")
    {
        // Arrange
        InjectError(EOnlineServicesError::NetworkError);
        TOnlineResult<FSaveData> FailResult = SaveData(TEXT("TestData"), TEXT("Content"));
        REQUIRE(FailResult.IsError());
        ResetMock();

        // Act
        TOnlineResult<FSaveData> SuccessResult = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert
        REQUIRE(SuccessResult.IsOk());
        REQUIRE(GetMockSaveService()->GetSaveCallCount() == 2);
    }
}

// ============================================================================
// Async Control Tests
// ============================================================================

TEST_CASE_METHOD(FSaveFrameworkTestFixture, "SaveFramework::SaveData async control", "[SaveFramework][Save][async]")
{
    SECTION("Paused operation returns pending")
    {
        // Arrange
        PauseAsync();

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert
        REQUIRE(Result.IsError());
        REQUIRE(Result.GetErrorValue() == EOnlineServicesError::RequestPending);

        // Resume and verify completion
        ResumeAsync();
        TOnlineResult<FSaveData> ResumedResult = SaveData(TEXT("TestData"), TEXT("Content"));
        REQUIRE(ResumedResult.IsOk());
    }

    SECTION("Normal async flow completes immediately")
    {
        // Arrange
        ResetMock();

        // Act
        TOnlineResult<FSaveData> Result = SaveData(TEXT("TestData"), TEXT("Content"));

        // Assert
        REQUIRE(Result.IsOk());
    }
}
```

## UE Naming Conventions

**Interfaces**: `IMyInterface` prefix
**Classes**: `FMyClass`, `UMyObject` (UObject-derived)
**Structs**: `FMyStruct`
**Enums**: `EMyEnum`
**Mock Interfaces**: `IMockMyService`
**Mock Implementations**: `FMockMyService`

## When to Use Mock Template

Use this template when:
- Testing requires external service dependencies
- Need to test error paths without real failures
- Need to control async timing in tests
- Testing plugin integration with framework services
- Need test doubles for complex dependencies

## Related Templates

- **Basic/Fixture Template**: `cpp-basic-fixture-llt-template.md` - For simple unit tests without mocks
- **Async Template**: `cpp-async-llt-template.md` - For async tests without dependency injection
- **Plugin/Lifecycle Template**: `cpp-plugin-lifecycle-llt-template.md` - For Engine integration tests

---

**Template Version**: 1.0.0
**Last Updated**: 2026-02-18
**Phase**: LLT Test Generation
**Status**: Complete
**Maps to Spec**: REQ-F-5, REQ-F-10 (Mock pattern support, 10% of modules)
