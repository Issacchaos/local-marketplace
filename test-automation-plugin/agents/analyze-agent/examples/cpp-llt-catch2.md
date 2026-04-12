---
language: cpp
framework: catch2
test_type: llt
description: Example LLT analysis output for a C++ Unreal Engine LowLevelTests project using Catch2
---

# Example LLT Analysis: C++/Catch2

This example demonstrates the expected analysis output format for an Unreal Engine LowLevelTests (LLT) project using the Catch2 framework.

---

## Analysis Summary

**Project**: WebTests (Unreal Engine LowLevelTests)
**Language**: `C++`
**Framework**: `Catch2` (Confidence: 1.0)
**Total Runtime Modules**: 4 (HTTP, WebSockets, SSL, HTTPServer)
**Total Source Files**: 89 (.cpp files in runtime modules)
**Total Testable Functions**: 450 (extracted via Clang AST)
**Existing Test Files**: 3 test files (84 test cases)
**Function Coverage**: 67% (302/450 functions tested)

---

## Test Targets

- `Engine/Source/Runtime/Online/HTTP/Private/HttpManager.cpp:245` - **FHttpManager::ProcessRequest** [Priority: Critical]
  - Type: method
  - Complexity: 8.5/10
  - Coverage: Not Covered (0 tests reference this function)
  - Reason: Core HTTP request processing, 284 LOC, state machine, no test coverage

- `Engine/Source/Runtime/Online/HTTP/Private/HttpRetrySystem.cpp:156` - **FHttpRetrySystem::ProcessRequest** [Priority: Critical]
  - Type: method
  - Complexity: 7.8/10
  - Coverage: Partial (1 test case, missing exponential backoff edge cases)
  - Reason: Retry logic with backoff, error handling, incomplete coverage

- `Engine/Source/Runtime/Online/WebSockets/Private/WebSocketsModule.cpp:89` - **FWebSocketsModule::CreateConnection** [Priority: High]
  - Type: method
  - Complexity: 6.5/10
  - Coverage: Covered (4 test cases in TestWebSockets.cpp)
  - Reason: WebSocket connection lifecycle, well tested

---

## Coverage Gaps

**Critical Gaps (3 modules <50% coverage)**:
- **FHttpManager** (Engine/HTTP): 12/45 functions tested (27%)
  - Missing: ProcessRequest, CancelRequest, FlushRequests, HandleConnectionError
- **FHttpRetrySystem** (Engine/HTTP): 5/18 functions tested (28%)
  - Missing: CalculateBackoff, ShouldRetry, ProcessRetryQueue
- **FWebSocketConnection** (Engine/WebSockets): 8/23 functions tested (35%)
  - Missing: SendBinary, ReceiveBinary, HandlePing, HandlePong

**Overall Function Coverage**: 67% (302/450)
- HTTP Module: 189 functions, 98 tested (52%)
- WebSockets Module: 87 functions, 45 tested (52%)
- SSL Module: 134 functions, 125 tested (93%)
- HTTPServer Module: 40 functions, 34 tested (85%)

---

## Recommendations

### Critical Priority: FHttpManager::ProcessRequest (0% coverage)

**Edge Cases to Test**:
1. Network timeout during request (expect timeout error, connection cleanup)
2. Server returns 500 error (expect retry logic, error callback invoked)
3. Request canceled mid-flight (expect cancellation callback, no memory leaks)
4. Invalid URL format (expect validation error, no crash)
5. Request queue full (expect queuing behavior or rejection)
6. Concurrent requests to same endpoint (expect thread safety)
7. Request body exceeds max size (expect chunked upload or rejection)

**Implementation Strategy**:
- Create FHttpManagerTestFixture with mock HTTP backend
- Use FHttpMockServer for controlled responses
- Estimated effort: 8-10 hours for comprehensive coverage

---

### Critical Priority: FHttpRetrySystem::CalculateBackoff (0% coverage)

**Edge Cases to Test**:
1. Retry count exceeds max retries (expect exponential backoff cap)
2. Backoff duration overflows int32 (expect clamping to max safe value)
3. Zero retry count (expect base delay)
4. Negative jitter values (expect non-negative result)
5. Very large retry counts (expect reasonable delay, not infinite)

**Implementation Strategy**:
- Unit test with parameterized inputs (retry count 0-10, 100, INT_MAX)
- Verify exponential growth: delay(n) ~ base * 2^n
- Test jitter randomization (within expected bounds)
- Estimated effort: 2-3 hours

---

### High Priority: FWebSocketConnection::SendBinary (0% coverage)

**Edge Cases to Test**:
1. Send empty binary data (expect success or validation)
2. Send large binary payload (>1MB) (expect chunking or streaming)
3. Send while connection closed (expect error, no crash)
4. Send during connection handshake (expect queuing or rejection)
5. Send when send buffer full (expect backpressure handling)
6. Send null pointer (expect validation error)
7. Concurrent sends from multiple threads (expect serialization or error)

**Implementation Strategy**:
- Extend FWebSocketConnectionTestFixture
- Mock underlying TCP socket for controlled scenarios
- Test binary protocol framing (opcode, masking, fragmentation)
- Estimated effort: 6-8 hours

---

### Summary

- **Total estimated effort**: 40-50 hours for Critical and High priority gaps
- **Quick wins**: FHttpRetrySystem unit tests (2-3 hours, high impact)
- **Leverage existing fixtures**: FHttpModuleTestFixture, FWebSocketsModuleTestFixture
- **Risk**: HTTP and WebSocket are core networking - bugs impact all online features
