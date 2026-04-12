# Catch2 LowLevelTest Template - Basic/Fixture

**Purpose**: Unified template for synchronous Unreal Engine LowLevelTests with optional fixture support
**Target Framework**: Catch2 v3.4.0+ with UE LLT framework
**Test Pattern**: Basic unit tests (TEST_CASE) or stateful tests (TEST_CASE_METHOD)
**Usage**: 40% of Fortnite LLT modules use this pattern
**Reference**: FoundationTests/LinkedListBuilderTests.cpp

## Overview

This template provides a unified approach for creating synchronous unit tests in Unreal Engine's LowLevelTest framework. It supports both:

- **Basic Tests** (TEST_CASE): Stateless unit tests with no shared setup
- **Fixture Tests** (TEST_CASE_METHOD): Tests requiring shared state, setup, or teardown

The template follows Fortnite coding conventions including Epic copyright headers, UE naming patterns (F/I/E prefixes), and Catch2 v3 SECTION-based organization.

## When to Use This Template

**Use this template when:**
- Testing synchronous methods (no async callbacks or tick loops)
- Unit testing classes with minimal dependencies
- Testing utility functions or data structures
- State management needs are simple (local variables or simple fixture)

**Do NOT use this template when:**
- Testing async operations (use cpp-async-llt-template.md)
- Testing plugin lifecycle or engine integration (use cpp-plugin-lifecycle-llt-template.md)
- Testing with mock dependencies (use cpp-mock-llt-template.md)

## Template Placeholders

### UE Module Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{UE_MODULE_NAME}}` | Module being tested | `CommChannelsRuntime`, `FoundationTests` |
| `{{UE_HEADER_PATH}}` | Header file path relative to module | `CommChannels/CommChannelNode.h` |
| `{{CLASS_NAME}}` | UE class name (with F prefix) | `FCommChannelNode`, `FLinkedListBuilder` |
| `{{METHOD_NAME}}` | Method being tested | `ConnectTo`, `AddNode`, `IsValid` |

### Test Structure Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{TEST_TAG}}` | Test category tag | `[commchannels]`, `[foundation]`, `[unit]` |
| `{{SETUP_CODE}}` | Arrange step code | Variable declarations, object initialization |
| `{{CODE_UNDER_TEST}}` | Act step code | Method calls being tested |
| `{{ASSERTIONS}}` | Assert step code | REQUIRE() statements |
| `{{SECTION_NAME}}` | Section description | `"With valid input"`, `"Returns expected value"` |

### Fixture Placeholders (Optional)

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{FIXTURE_CLASS_NAME}}` | Fixture class name | `FCommChannelTestFixture`, `FBuilderTestFixture` |
| `{{FIXTURE_MEMBERS}}` | Private member variables | `FCommChannelNode* Node;`<br>`int TestCounter;` |
| `{{FIXTURE_SETUP}}` | Constructor initialization | `Node = new FCommChannelNode();`<br>`TestCounter = 0;` |
| `{{FIXTURE_TEARDOWN}}` | Destructor cleanup | `delete Node;`<br>`Node = nullptr;` |

## Basic Test Template (TEST_CASE)

Use this for **stateless tests** with no shared setup between test cases or sections.

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "{{UE_HEADER_PATH}}"

// ============================================================================
// {{UE_MODULE_NAME}} Tests - {{CLASS_NAME}}
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{TEST_TAG}}]")
{
	// Arrange
	{{SETUP_CODE}}

	// Act
	{{CODE_UNDER_TEST}}

	// Assert
	{{ASSERTIONS}}
}
```

### Example: Basic Test without Sections

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "CommChannels/CommChannelNode.h"

// ============================================================================
// CommChannelsRuntime Tests - FCommChannelNode
// ============================================================================

TEST_CASE("CommChannelsRuntime::FCommChannelNode::ConnectTo", "[commchannels][unit]")
{
	// Arrange
	FCommChannelNode NodeA;
	FCommChannelNode NodeB;

	// Act
	bool bConnected = NodeA.ConnectTo(&NodeB);

	// Assert
	REQUIRE(bConnected == true);
	REQUIRE(NodeA.IsConnectedTo(&NodeB) == true);
}

TEST_CASE("CommChannelsRuntime::FCommChannelNode::DisconnectFrom", "[commchannels][unit]")
{
	// Arrange
	FCommChannelNode NodeA;
	FCommChannelNode NodeB;
	NodeA.ConnectTo(&NodeB);

	// Act
	bool bDisconnected = NodeA.DisconnectFrom(&NodeB);

	// Assert
	REQUIRE(bDisconnected == true);
	REQUIRE(NodeA.IsConnectedTo(&NodeB) == false);
}
```

## Basic Test with Sections

Use SECTION blocks to test **multiple variants** of the same method with shared setup.

```cpp
TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{TEST_TAG}}]")
{
	// Common setup - runs once per SECTION
	{{COMMON_SETUP}}

	SECTION("{{SECTION_NAME_1}}")
	{
		// Arrange
		{{SETUP_CODE_1}}

		// Act
		{{CODE_UNDER_TEST_1}}

		// Assert
		{{ASSERTIONS_1}}
	}

	SECTION("{{SECTION_NAME_2}}")
	{
		// Arrange
		{{SETUP_CODE_2}}

		// Act
		{{CODE_UNDER_TEST_2}}

		// Assert
		{{ASSERTIONS_2}}
	}

	SECTION("{{SECTION_NAME_3}}")
	{
		// Arrange
		{{SETUP_CODE_3}}

		// Act
		{{CODE_UNDER_TEST_3}}

		// Assert
		{{ASSERTIONS_3}}
	}
}
```

### Example: Basic Test with Sections

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "Foundation/LinkedListBuilder.h"

// ============================================================================
// FoundationTests - FLinkedListBuilder
// ============================================================================

TEST_CASE("FoundationTests::FLinkedListBuilder::AddNode", "[foundation][linkedlist]")
{
	// Common setup - runs before each SECTION
	FLinkedListBuilder Builder;

	SECTION("Adding single node")
	{
		// Arrange
		int32 Value = 42;

		// Act
		Builder.AddNode(Value);

		// Assert
		REQUIRE(Builder.GetCount() == 1);
		REQUIRE(Builder.GetHead()->Value == Value);
	}

	SECTION("Adding multiple nodes")
	{
		// Arrange
		int32 Value1 = 10;
		int32 Value2 = 20;
		int32 Value3 = 30;

		// Act
		Builder.AddNode(Value1);
		Builder.AddNode(Value2);
		Builder.AddNode(Value3);

		// Assert
		REQUIRE(Builder.GetCount() == 3);
		REQUIRE(Builder.GetHead()->Value == Value1);
	}

	SECTION("Adding node with duplicate value")
	{
		// Arrange
		int32 Value = 100;
		Builder.AddNode(Value);

		// Act
		Builder.AddNode(Value);  // Duplicate

		// Assert
		REQUIRE(Builder.GetCount() == 2);  // Allows duplicates
	}
}
```

## Fixture Test Template (TEST_CASE_METHOD)

Use this for **stateful tests** requiring shared setup, private members, or complex initialization.

### Fixture Class Definition

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "{{UE_HEADER_PATH}}"

// ============================================================================
// Test Fixture: {{FIXTURE_CLASS_NAME}}
// ============================================================================

class {{FIXTURE_CLASS_NAME}}
{
public:
	{{FIXTURE_CLASS_NAME}}()
	{
		// Setup - runs before each test
		{{FIXTURE_SETUP}}
	}

	~{{FIXTURE_CLASS_NAME}}()
	{
		// Teardown - runs after each test
		{{FIXTURE_TEARDOWN}}
	}

	// Helper methods (optional)
	{{HELPER_METHODS}}

protected:
	// Shared test state
	{{FIXTURE_MEMBERS}}
};

// ============================================================================
// {{UE_MODULE_NAME}} Tests - {{CLASS_NAME}}
// ============================================================================

TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{TEST_TAG}}]")
{
	// Arrange
	{{SETUP_CODE}}

	// Act
	{{CODE_UNDER_TEST}}

	// Assert
	{{ASSERTIONS}}
}
```

### Example: Fixture Test with Sections

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "CommChannels/CommChannelManager.h"

// ============================================================================
// Test Fixture: FCommChannelManagerFixture
// ============================================================================

class FCommChannelManagerFixture
{
public:
	FCommChannelManagerFixture()
	{
		// Setup - runs before each test
		Manager = new FCommChannelManager();
		Manager->Initialize();
		TestChannelCount = 0;
	}

	~FCommChannelManagerFixture()
	{
		// Teardown - runs after each test
		Manager->Shutdown();
		delete Manager;
		Manager = nullptr;
	}

	// Helper method
	void CreateTestChannel(const FString& ChannelName)
	{
		Manager->CreateChannel(ChannelName);
		TestChannelCount++;
	}

protected:
	FCommChannelManager* Manager;
	int32 TestChannelCount;
};

// ============================================================================
// CommChannelsRuntime Tests - FCommChannelManager
// ============================================================================

TEST_CASE_METHOD(FCommChannelManagerFixture, "CommChannelsRuntime::FCommChannelManager::CreateChannel", "[commchannels][manager]")
{
	SECTION("Creating single channel")
	{
		// Arrange
		FString ChannelName = TEXT("TestChannel");

		// Act
		bool bCreated = Manager->CreateChannel(ChannelName);

		// Assert
		REQUIRE(bCreated == true);
		REQUIRE(Manager->GetChannelCount() == 1);
		REQUIRE(Manager->ChannelExists(ChannelName) == true);
	}

	SECTION("Creating multiple channels")
	{
		// Arrange
		// (Manager already initialized in fixture constructor)

		// Act
		CreateTestChannel(TEXT("Channel1"));
		CreateTestChannel(TEXT("Channel2"));
		CreateTestChannel(TEXT("Channel3"));

		// Assert
		REQUIRE(Manager->GetChannelCount() == 3);
		REQUIRE(TestChannelCount == 3);
	}

	SECTION("Creating channel with empty name fails")
	{
		// Arrange
		FString EmptyName = TEXT("");

		// Act
		bool bCreated = Manager->CreateChannel(EmptyName);

		// Assert
		REQUIRE(bCreated == false);
		REQUIRE(Manager->GetChannelCount() == 0);
	}
}

TEST_CASE_METHOD(FCommChannelManagerFixture, "CommChannelsRuntime::FCommChannelManager::DeleteChannel", "[commchannels][manager]")
{
	SECTION("Deleting existing channel")
	{
		// Arrange
		FString ChannelName = TEXT("TestChannel");
		Manager->CreateChannel(ChannelName);

		// Act
		bool bDeleted = Manager->DeleteChannel(ChannelName);

		// Assert
		REQUIRE(bDeleted == true);
		REQUIRE(Manager->GetChannelCount() == 0);
		REQUIRE(Manager->ChannelExists(ChannelName) == false);
	}

	SECTION("Deleting non-existent channel fails")
	{
		// Arrange
		FString NonExistentName = TEXT("DoesNotExist");

		// Act
		bool bDeleted = Manager->DeleteChannel(NonExistentName);

		// Assert
		REQUIRE(bDeleted == false);
	}
}
```

## Inline Helper Functions

For simple helper logic, use **inline lambdas** instead of fixture methods:

```cpp
TEST_CASE("FoundationTests::FLinkedListBuilder::Operations", "[foundation][linkedlist]")
{
	// Helper lambda (inline)
	auto CreateBuilderWithNodes = [](int32 Count) -> FLinkedListBuilder
	{
		FLinkedListBuilder Builder;
		for (int32 i = 0; i < Count; ++i)
		{
			Builder.AddNode(i);
		}
		return Builder;
	};

	SECTION("Builder with 5 nodes")
	{
		// Arrange
		FLinkedListBuilder Builder = CreateBuilderWithNodes(5);

		// Act
		int32 Count = Builder.GetCount();

		// Assert
		REQUIRE(Count == 5);
	}

	SECTION("Builder with empty list")
	{
		// Arrange
		FLinkedListBuilder Builder = CreateBuilderWithNodes(0);

		// Act
		bool bEmpty = Builder.IsEmpty();

		// Assert
		REQUIRE(bEmpty == true);
	}
}
```

## Edge Case Tests

```cpp
// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}} - Edge Cases", "[{{TEST_TAG}}][edge-case]")
{
	SECTION("With nullptr input")
	{
		// Arrange
		{{CLASS_NAME}}* NullPtr = nullptr;

		// Act & Assert
		{{CODE_THAT_HANDLES_NULL}}
		{{ASSERTIONS}}
	}

	SECTION("With empty container")
	{
		// Arrange
		{{CLASS_NAME}} Object;
		// Empty by default

		// Act
		{{CODE_UNDER_TEST}}

		// Assert
		{{ASSERTIONS}}
	}

	SECTION("With boundary values")
	{
		// Arrange
		{{SETUP_BOUNDARY_CONDITIONS}}

		// Act
		{{CODE_UNDER_TEST}}

		// Assert
		{{ASSERTIONS}}
	}
}
```

## Error Handling Tests

```cpp
// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}} - Error Handling", "[{{TEST_TAG}}][error]")
{
	SECTION("Returns error on invalid input")
	{
		// Arrange
		{{SETUP_INVALID_INPUT}}

		// Act
		{{RESULT_TYPE}} Result = {{CODE_UNDER_TEST}};

		// Assert
		REQUIRE(Result.IsError() == true);
		REQUIRE(Result.ErrorCode == {{EXPECTED_ERROR_CODE}});
	}

	SECTION("Returns false on failure")
	{
		// Arrange
		{{SETUP_FAILURE_CONDITION}}

		// Act
		bool bSuccess = {{CODE_UNDER_TEST}};

		// Assert
		REQUIRE(bSuccess == false);
	}
}
```

## Complete File Example

```cpp

#include "CoreMinimal.h"
#include "TestHarness.h"
#include "Foundation/LinkedListBuilder.h"

// ============================================================================
// Test Fixture: FLinkedListBuilderFixture
// ============================================================================

class FLinkedListBuilderFixture
{
public:
	FLinkedListBuilderFixture()
	{
		// Setup
		Builder = new FLinkedListBuilder();
		ExpectedCount = 0;
	}

	~FLinkedListBuilderFixture()
	{
		// Teardown
		delete Builder;
		Builder = nullptr;
	}

	void AddTestNodes(int32 Count)
	{
		for (int32 i = 0; i < Count; ++i)
		{
			Builder->AddNode(i * 10);
			ExpectedCount++;
		}
	}

protected:
	FLinkedListBuilder* Builder;
	int32 ExpectedCount;
};

// ============================================================================
// FoundationTests - FLinkedListBuilder Basic Tests
// ============================================================================

TEST_CASE("FoundationTests::FLinkedListBuilder::IsEmpty", "[foundation][linkedlist]")
{
	// Arrange
	FLinkedListBuilder Builder;

	// Act
	bool bEmpty = Builder.IsEmpty();

	// Assert
	REQUIRE(bEmpty == true);
	REQUIRE(Builder.GetCount() == 0);
}

TEST_CASE("FoundationTests::FLinkedListBuilder::AddNode", "[foundation][linkedlist]")
{
	FLinkedListBuilder Builder;

	SECTION("Adding single node")
	{
		// Arrange
		int32 Value = 42;

		// Act
		Builder.AddNode(Value);

		// Assert
		REQUIRE(Builder.GetCount() == 1);
		REQUIRE(Builder.GetHead()->Value == Value);
		REQUIRE(Builder.IsEmpty() == false);
	}

	SECTION("Adding multiple nodes maintains order")
	{
		// Arrange
		int32 Values[] = {10, 20, 30};

		// Act
		for (int32 Value : Values)
		{
			Builder.AddNode(Value);
		}

		// Assert
		REQUIRE(Builder.GetCount() == 3);
		REQUIRE(Builder.GetHead()->Value == 10);
	}
}

// ============================================================================
// FoundationTests - FLinkedListBuilder Fixture Tests
// ============================================================================

TEST_CASE_METHOD(FLinkedListBuilderFixture, "FoundationTests::FLinkedListBuilder::RemoveNode", "[foundation][linkedlist]")
{
	SECTION("Removing existing node")
	{
		// Arrange
		AddTestNodes(5);
		int32 ValueToRemove = 20;  // Second node (index 2)

		// Act
		bool bRemoved = Builder->RemoveNode(ValueToRemove);

		// Assert
		REQUIRE(bRemoved == true);
		REQUIRE(Builder->GetCount() == 4);
		REQUIRE(Builder->Contains(ValueToRemove) == false);
	}

	SECTION("Removing non-existent node")
	{
		// Arrange
		AddTestNodes(3);
		int32 NonExistentValue = 999;

		// Act
		bool bRemoved = Builder->RemoveNode(NonExistentValue);

		// Assert
		REQUIRE(bRemoved == false);
		REQUIRE(Builder->GetCount() == 3);  // Count unchanged
	}

	SECTION("Removing from empty list")
	{
		// Arrange
		// Builder is empty (no AddTestNodes call)

		// Act
		bool bRemoved = Builder->RemoveNode(42);

		// Assert
		REQUIRE(bRemoved == false);
		REQUIRE(Builder->IsEmpty() == true);
	}
}

TEST_CASE_METHOD(FLinkedListBuilderFixture, "FoundationTests::FLinkedListBuilder::Clear", "[foundation][linkedlist]")
{
	SECTION("Clearing non-empty list")
	{
		// Arrange
		AddTestNodes(10);
		REQUIRE(Builder->GetCount() == 10);  // Precondition

		// Act
		Builder->Clear();

		// Assert
		REQUIRE(Builder->IsEmpty() == true);
		REQUIRE(Builder->GetCount() == 0);
		REQUIRE(Builder->GetHead() == nullptr);
	}

	SECTION("Clearing empty list")
	{
		// Arrange
		// Builder already empty

		// Act
		Builder->Clear();

		// Assert
		REQUIRE(Builder->IsEmpty() == true);
		REQUIRE(Builder->GetCount() == 0);
	}
}

// ============================================================================
// Edge Case Tests
// ============================================================================

TEST_CASE("FoundationTests::FLinkedListBuilder::AddNode - Edge Cases", "[foundation][linkedlist][edge-case]")
{
	FLinkedListBuilder Builder;

	SECTION("Adding zero value")
	{
		// Arrange & Act
		Builder.AddNode(0);

		// Assert
		REQUIRE(Builder.GetCount() == 1);
		REQUIRE(Builder.GetHead()->Value == 0);
	}

	SECTION("Adding negative value")
	{
		// Arrange & Act
		Builder.AddNode(-100);

		// Assert
		REQUIRE(Builder.GetCount() == 1);
		REQUIRE(Builder.GetHead()->Value == -100);
	}

	SECTION("Adding INT32_MAX")
	{
		// Arrange & Act
		Builder.AddNode(INT32_MAX);

		// Assert
		REQUIRE(Builder.GetCount() == 1);
		REQUIRE(Builder.GetHead()->Value == INT32_MAX);
	}
}

// ============================================================================
// Error Handling Tests
// ============================================================================

TEST_CASE("FoundationTests::FLinkedListBuilder::GetNodeAt - Error Handling", "[foundation][linkedlist][error]")
{
	FLinkedListBuilder Builder;
	Builder.AddNode(10);
	Builder.AddNode(20);

	SECTION("Returns nullptr for out-of-bounds index")
	{
		// Act
		FLinkedListNode* Node = Builder.GetNodeAt(10);  // Index > count

		// Assert
		REQUIRE(Node == nullptr);
	}

	SECTION("Returns nullptr for negative index")
	{
		// Act
		FLinkedListNode* Node = Builder.GetNodeAt(-1);

		// Assert
		REQUIRE(Node == nullptr);
	}

	SECTION("Returns node for valid index")
	{
		// Act
		FLinkedListNode* Node = Builder.GetNodeAt(1);

		// Assert
		REQUIRE(Node != nullptr);
		REQUIRE(Node->Value == 20);
	}
}
```

## Placeholder Substitution Guide

### Basic Test (No Fixture)

```cpp
// Template
TEST_CASE("{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{TEST_TAG}}]")

// Substituted
TEST_CASE("CommChannelsRuntime::FCommChannelNode::ConnectTo", "[commchannels]")
```

### Fixture Test

```cpp
// Template
class {{FIXTURE_CLASS_NAME}}
{
protected:
	{{FIXTURE_MEMBERS}}
};

TEST_CASE_METHOD({{FIXTURE_CLASS_NAME}}, "{{UE_MODULE_NAME}}::{{CLASS_NAME}}::{{METHOD_NAME}}", "[{{TEST_TAG}}]")

// Substituted
class FCommChannelManagerFixture
{
protected:
	FCommChannelManager* Manager;
	int32 TestChannelCount;
};

TEST_CASE_METHOD(FCommChannelManagerFixture, "CommChannelsRuntime::FCommChannelManager::CreateChannel", "[commchannels]")
```

## Best Practices

1. **Choose Basic vs Fixture**:
   - Basic (TEST_CASE): No state, simple setup, independent tests
   - Fixture (TEST_CASE_METHOD): Shared state, complex setup, reusable helpers

2. **Use SECTION for Variants**:
   - Group related test scenarios within a single TEST_CASE
   - Common setup runs once per SECTION

3. **Keep Fixtures Simple**:
   - Follow FoundationTests pattern: minimal fixture, inline helpers
   - Avoid complex fixture hierarchies

4. **Arrange-Act-Assert**:
   - Always include comments to mark test phases
   - Makes test intent clear

5. **UE Naming Conventions**:
   - Use F prefix for structs/classes (FCommChannelNode)
   - Use I prefix for interfaces (IOnlineInterface)
   - Use E prefix for enums (EChannelState)

6. **Copyright Headers**:
   - Follow exact format shown in examples

7. **Test Tags**:
   - Use module name tags: `[commchannels]`, `[foundation]`
   - Add category tags: `[unit]`, `[edge-case]`, `[error]`

## Related Templates

- **cpp-async-llt-template.md**: For async tests with callbacks/tick loops
- **cpp-plugin-lifecycle-llt-template.md**: For engine integration tests
- **cpp-mock-llt-template.md**: For dependency injection tests
- **ue-test-build-cs-template.md**: For .Build.cs test module configuration
- **ue-test-target-cs-template.md**: For .Target.cs test target configuration

---

**Template Version**: 1.0.0
**Status**: Ready for Implementation
**Covers**: REQ-F-2, REQ-F-7, REQ-F-8, REQ-F-11
