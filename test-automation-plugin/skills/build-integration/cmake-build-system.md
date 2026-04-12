# CMake Build System Integration

**Version**: 1.0.0
**Language**: C++
**Build Tool**: CMake + CTest
**Status**: Phase 4 - Systems Languages

## Overview

Integration skill for CMake build system and CTest framework, covering project configuration, test framework integration (Google Test and Catch2), compiler setup, out-of-source builds, and test execution for C++ projects.

## CMake Basics

### Minimum CMake Version

**Recommended**: CMake 3.15 or higher

```cmake
# Minimum version for modern CMake features
cmake_minimum_required(VERSION 3.15)

# For C++20 features, recommend 3.20+
# cmake_minimum_required(VERSION 3.20)
```

**Version Rationale**:
- CMake 3.15: Improved target_link_libraries, generator expressions
- CMake 3.20: Full C++20 support, improved test discovery
- CMake 3.24+: Better FetchContent, C++23 support

---

### Project Setup

**Basic Project Declaration**:
```cmake
cmake_minimum_required(VERSION 3.15)

# Project with C++ only
project(Calculator CXX)

# Project with version
project(Calculator VERSION 1.0.0 LANGUAGES CXX)

# Project with description
project(Calculator
    VERSION 1.0.0
    DESCRIPTION "A calculator library"
    LANGUAGES CXX
)
```

**Important**: Always specify `CXX` language for C++ projects

---

### C++ Standard Configuration

**Setting C++ Standard** (Modern CMake):
```cmake
# Set C++ standard globally
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)  # Disable compiler extensions

# Available standards: 11, 14, 17, 20, 23
```

**Per-Target Standard** (Preferred for libraries):
```cmake
# Set standard for specific target
add_library(calculator src/calculator.cpp)
target_compile_features(calculator PUBLIC cxx_std_17)

# Or specify features explicitly
target_compile_features(calculator PUBLIC
    cxx_auto_type
    cxx_lambdas
    cxx_nullptr
)
```

**Standards Table**:
| Standard | Year | Key Features | CMake Min |
|----------|------|--------------|-----------|
| C++11 | 2011 | auto, lambda, nullptr | 3.1+ |
| C++14 | 2014 | Generic lambdas, binary literals | 3.1+ |
| C++17 | 2017 | Structured bindings, std::optional | 3.8+ |
| C++20 | 2020 | Concepts, ranges, coroutines | 3.12+ |
| C++23 | 2023 | std::expected, std::mdspan | 3.20+ |

---

## Finding Test Frameworks

### Google Test (GTest) Integration

**Method 1: find_package (System Installation)**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Google Test package
find_package(GTest REQUIRED)

# Include CTest module
include(CTest)
enable_testing()

# Create test executable
add_executable(my_test tests/my_test.cpp)

# Link with Google Test
target_link_libraries(my_test PRIVATE
    GTest::GTest        # Google Test library
    GTest::Main         # Google Test main() function
)

# Add test to CTest
add_test(NAME my_test COMMAND my_test)
```

**Method 2: FetchContent (Download at Configure Time)**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)

# Fetch Google Test from GitHub
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0  # Specific version tag
    # Or use release/1.14.0 for stable release
)

# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

# Make available
FetchContent_MakeAvailable(googletest)

# Enable testing
enable_testing()

# Create test executable
add_executable(my_test tests/my_test.cpp)

# Link with Google Test
target_link_libraries(my_test PRIVATE
    gtest
    gtest_main  # Provides main() function
    gmock       # Optional: Google Mock
)

# Add test
add_test(NAME my_test COMMAND my_test)
```

**Method 3: Git Submodule**:
```cmake
# Add googletest subdirectory (if included as submodule)
add_subdirectory(external/googletest)

# Create test
add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE gtest gtest_main)

enable_testing()
add_test(NAME my_test COMMAND my_test)
```

---

### Catch2 Integration

**Method 1: find_package (System Installation)**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)

# Find Catch2 (v3)
find_package(Catch2 3 REQUIRED)

# Enable testing
enable_testing()

# Create test executable
add_executable(my_test tests/my_test.cpp)

# Link with Catch2
target_link_libraries(my_test PRIVATE
    Catch2::Catch2WithMain  # Catch2 v3 with main()
)

# Discover tests automatically
include(CTest)
include(Catch)
catch_discover_tests(my_test)
```

**Method 2: FetchContent (Catch2 v3)**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)

# Fetch Catch2 v3
include(FetchContent)

FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.5.0  # Latest v3 version
)

FetchContent_MakeAvailable(Catch2)

# Enable testing
enable_testing()

# Create test executable
add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE Catch2::Catch2WithMain)

# Discover tests
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(CTest)
include(Catch)
catch_discover_tests(my_test)
```

**Method 3: Catch2 v2 (Header-Only)**:
```cmake
# Fetch Catch2 v2 (single header)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v2.13.10  # Last v2 version
)

FetchContent_MakeAvailable(Catch2)

# Create test
add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE Catch2::Catch2)

# Discover tests
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/contrib)
include(CTest)
include(Catch)
catch_discover_tests(my_test)
```

---

### Alternative Package Managers

**Conan Integration**:
```cmake
# conanfile.txt
[requires]
gtest/1.14.0

[generators]
CMakeDeps
CMakeToolchain

[options]
gtest:shared=False
```

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

# Conan-generated files
include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)

find_package(GTest REQUIRED)

add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE GTest::gtest GTest::gtest_main)

enable_testing()
add_test(NAME my_test COMMAND my_test)
```

**vcpkg Integration**:
```bash
# Install Google Test via vcpkg
vcpkg install gtest
```

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

# vcpkg toolchain is passed via -DCMAKE_TOOLCHAIN_FILE
find_package(GTest CONFIG REQUIRED)

add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE GTest::gtest GTest::gtest_main)

enable_testing()
add_test(NAME my_test COMMAND my_test)
```

---

## Test Target Configuration

### Basic Test Target Structure

```cmake
# Source library
add_library(calculator
    src/calculator.cpp
    src/operations.cpp
)

target_include_directories(calculator PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Test executable
add_executable(calculator_test
    tests/calculator_test.cpp
    tests/operations_test.cpp
)

# Link test with library and test framework
target_link_libraries(calculator_test PRIVATE
    calculator              # Library under test
    GTest::GTest           # Google Test
    GTest::Main            # Main function
)

# Add to CTest
add_test(NAME calculator_test COMMAND calculator_test)
```

---

### Multiple Test Targets

```cmake
# Unit tests
add_executable(unit_tests
    tests/calculator_test.cpp
    tests/operations_test.cpp
)
target_link_libraries(unit_tests PRIVATE calculator GTest::GTest GTest::Main)
add_test(NAME unit_tests COMMAND unit_tests)

# Integration tests
add_executable(integration_tests
    tests/integration_test.cpp
)
target_link_libraries(integration_tests PRIVATE calculator GTest::GTest GTest::Main)
add_test(NAME integration_tests COMMAND integration_tests)

# Performance tests
add_executable(perf_tests
    tests/performance_test.cpp
)
target_link_libraries(perf_tests PRIVATE calculator GTest::GTest GTest::Main)
add_test(NAME perf_tests COMMAND perf_tests)
```

---

### Test Properties and Labels

```cmake
# Add test with properties
add_test(NAME unit_tests COMMAND unit_tests)

# Set test properties
set_tests_properties(unit_tests PROPERTIES
    TIMEOUT 30                    # Max execution time (seconds)
    LABELS "unit;fast"            # Test labels for filtering
    ENVIRONMENT "TEST_DATA_DIR=${CMAKE_SOURCE_DIR}/testdata"
)

# Add test with working directory
add_test(NAME integration_tests
    COMMAND integration_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tests
)

# Run tests by label
# ctest -L unit
# ctest -LE slow  (exclude slow tests)
```

---

## CTest Integration

### Basic CTest Configuration

```cmake
# Enable testing module
include(CTest)
enable_testing()

# Or minimal setup
# enable_testing()

# Add tests
add_test(NAME my_test COMMAND my_test)

# Run with: ctest
```

---

### Google Test Discovery

**Automatic Test Discovery** (Recommended):
```cmake
# Google Test automatic discovery
include(GoogleTest)

add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE GTest::GTest GTest::Main)

# Discover all TEST() and TEST_F() macros
gtest_discover_tests(my_test
    PROPERTIES
        LABELS "unit"
        TIMEOUT 10
)

# This creates individual CTest entries for each TEST() macro
# Instead of one test per executable
```

**Manual Test Discovery**:
```cmake
# Add single test (runs all tests in executable)
add_test(NAME my_test COMMAND my_test)

# Add test with arguments
add_test(NAME my_test_subset
    COMMAND my_test --gtest_filter=CalculatorTest.*
)
```

---

### Catch2 Discovery

```cmake
include(CTest)

# Include Catch2 CMake module
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(Catch)

add_executable(my_test tests/my_test.cpp)
target_link_libraries(my_test PRIVATE Catch2::Catch2WithMain)

# Discover all TEST_CASE() macros
catch_discover_tests(my_test
    PROPERTIES
        LABELS "unit"
)
```

---

### CTest Configuration File

**CTestConfig.cmake** (Project Root):
```cmake
# CTest configuration
set(CTEST_PROJECT_NAME "Calculator")
set(CTEST_NIGHTLY_START_TIME "00:00:00 EST")

set(CTEST_DROP_METHOD "http")
set(CTEST_DROP_SITE "my.cdash.org")
set(CTEST_DROP_LOCATION "/submit.php?project=Calculator")
set(CTEST_DROP_SITE_CDASH TRUE)
```

---

## Out-of-Source Builds

### Best Practice Structure

**Directory Layout**:
```
project/
├── CMakeLists.txt          # Root CMake file
├── include/                # Public headers
│   └── calculator/
│       └── calculator.h
├── src/                    # Source files
│   ├── CMakeLists.txt
│   ├── calculator.cpp
│   └── operations.cpp
├── tests/                  # Test files
│   ├── CMakeLists.txt
│   ├── calculator_test.cpp
│   └── operations_test.cpp
├── build/                  # Build directory (gitignored)
│   ├── bin/
│   ├── lib/
│   └── Testing/
└── external/               # Third-party dependencies (optional)
    └── googletest/
```

**Why Out-of-Source?**:
- Keeps source tree clean
- Multiple build configurations (Debug/Release)
- Easy to clean (delete build/ directory)
- Parallel builds for different compilers

---

### Build Commands

**Configure and Build**:
```bash
# Create build directory
mkdir -p build
cd build

# Configure project (generate build files)
cmake ..

# Build (compile)
cmake --build .

# Run tests
ctest

# Or combined
ctest --build-and-test
```

**Multiple Build Configurations**:
```bash
# Debug build
mkdir -p build/debug
cd build/debug
cmake -DCMAKE_BUILD_TYPE=Debug ../..
cmake --build .

# Release build
mkdir -p build/release
cd build/release
cmake -DCMAKE_BUILD_TYPE=Release ../..
cmake --build .
```

---

## Compiler Flags

### Warning Flags

**GCC/Clang Warnings**:
```cmake
# Enable comprehensive warnings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(calculator PRIVATE
        -Wall              # Enable most warnings
        -Wextra            # Enable extra warnings
        -Wpedantic         # Strict ISO C++ compliance
        -Werror            # Treat warnings as errors (optional)
        -Wconversion       # Warn on implicit conversions
        -Wsign-conversion  # Warn on sign conversions
        -Wshadow           # Warn on variable shadowing
    )
endif()
```

**MSVC Warnings**:
```cmake
if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    target_compile_options(calculator PRIVATE
        /W4                # Warning level 4
        /WX                # Treat warnings as errors (optional)
        /permissive-       # Strict conformance mode
    )
endif()
```

**Cross-Platform Warnings**:
```cmake
# Apply warnings to all targets
add_library(warning_flags INTERFACE)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(warning_flags INTERFACE
        -Wall -Wextra -Wpedantic
    )
elseif(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    target_compile_options(warning_flags INTERFACE
        /W4
    )
endif()

# Link any target with warning flags
target_link_libraries(calculator PRIVATE warning_flags)
```

---

### Optimization Flags

**Debug Configuration**:
```cmake
# Debug: No optimization, debug symbols
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")

# Or per-target
target_compile_options(calculator PRIVATE
    $<$<CONFIG:Debug>:-g -O0>
)
```

**Release Configuration**:
```cmake
# Release: Full optimization
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# Or per-target
target_compile_options(calculator PRIVATE
    $<$<CONFIG:Release>:-O3 -DNDEBUG>
)
```

**RelWithDebInfo** (Release with Debug Info):
```cmake
# Optimized with debug symbols (recommended for profiling)
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g -DNDEBUG")
```

---

### Sanitizers

**AddressSanitizer (ASan)** - Detects memory errors:
```cmake
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)

if(ENABLE_ASAN)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(calculator PRIVATE
            -fsanitize=address
            -fno-omit-frame-pointer
        )
        target_link_options(calculator PRIVATE
            -fsanitize=address
        )
    endif()
endif()
```

**UndefinedBehaviorSanitizer (UBSan)**:
```cmake
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)

if(ENABLE_UBSAN)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(calculator PRIVATE
            -fsanitize=undefined
        )
        target_link_options(calculator PRIVATE
            -fsanitize=undefined
        )
    endif()
endif()
```

**ThreadSanitizer (TSan)** - Detects data races:
```cmake
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)

if(ENABLE_TSAN)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(calculator PRIVATE
            -fsanitize=thread
        )
        target_link_options(calculator PRIVATE
            -fsanitize=thread
        )
    endif()
endif()
```

**Usage**:
```bash
# Build with AddressSanitizer
cmake -DENABLE_ASAN=ON ..
cmake --build .

# Run tests with sanitizer
ctest
```

---

### Code Coverage

**GCC/Clang Coverage (gcov/llvm-cov)**:
```cmake
option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(calculator PRIVATE
            --coverage           # Enable coverage instrumentation
            -fprofile-arcs      # Generate .gcda files
            -ftest-coverage     # Generate .gcno files
        )
        target_link_options(calculator PRIVATE
            --coverage
        )
    endif()
endif()
```

**Generate Coverage Report**:
```bash
# Build with coverage
cmake -DENABLE_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .

# Run tests (generates .gcda files)
ctest

# Generate report with gcov
gcov src/calculator.cpp

# Or use lcov for HTML report
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html

# For Clang, use llvm-cov
llvm-cov gcov src/calculator.cpp
```

---

## Cross-Platform Considerations

### Platform-Specific Code

```cmake
# Detect platform
if(WIN32)
    # Windows-specific settings
    target_compile_definitions(calculator PRIVATE PLATFORM_WINDOWS)
    target_sources(calculator PRIVATE src/windows/platform.cpp)
elseif(APPLE)
    # macOS-specific settings
    target_compile_definitions(calculator PRIVATE PLATFORM_MACOS)
    target_sources(calculator PRIVATE src/macos/platform.cpp)
elseif(UNIX)
    # Linux/Unix-specific settings
    target_compile_definitions(calculator PRIVATE PLATFORM_LINUX)
    target_sources(calculator PRIVATE src/linux/platform.cpp)
endif()
```

---

### Generator Expressions

**Conditional Compilation**:
```cmake
# Different flags for different configurations
target_compile_options(calculator PRIVATE
    $<$<CONFIG:Debug>:-DDEBUG_MODE>
    $<$<CONFIG:Release>:-DRELEASE_MODE>
)

# Different flags for different compilers
target_compile_options(calculator PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wno-unused-parameter>
    $<$<CXX_COMPILER_ID:Clang>:-Wno-unused-lambda-capture>
    $<$<CXX_COMPILER_ID:MSVC>:/wd4100>
)

# Platform-specific flags
target_compile_options(calculator PRIVATE
    $<$<PLATFORM_ID:Windows>:/MP>  # MSVC parallel compilation
    $<$<PLATFORM_ID:Linux>:-pthread>
)
```

---

### Windows-Specific Configuration

```cmake
if(WIN32)
    # Set MSVC runtime library
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

    # Set Windows subsystem
    if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
        set_target_properties(calculator PROPERTIES
            WIN32_EXECUTABLE ON
        )
    endif()

    # Define Windows version
    target_compile_definitions(calculator PRIVATE
        _WIN32_WINNT=0x0A00  # Windows 10
        NOMINMAX             # Prevent min/max macros
    )
endif()
```

---

## Building and Running Tests

### CMake Build Commands

```bash
# Configure (generate build files)
cmake -S . -B build

# Configure with options
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTING=ON

# Build all targets
cmake --build build

# Build specific target
cmake --build build --target calculator_test

# Build with parallel jobs
cmake --build build --parallel 4
# Or: cmake --build build -j 4

# Clean build
cmake --build build --target clean
```

---

### CTest Commands

```bash
# Run all tests
cd build
ctest

# Run tests with output
ctest --output-on-failure

# Run tests verbosely
ctest -V
# Or: ctest --verbose

# Run specific test
ctest -R calculator_test

# Run tests matching regex
ctest -R "^unit_"

# Exclude tests
ctest -E "slow|integration"

# Run tests by label
ctest -L unit

# Run tests in parallel
ctest -j 4

# Run with timeout
ctest --timeout 30

# Run tests and show progress
ctest --progress

# Rerun only failed tests
ctest --rerun-failed
```

---

### CTest Output

**Default Output**:
```
Test project /path/to/build
    Start 1: calculator_test
1/3 Test #1: calculator_test ..................   Passed    0.02 sec
    Start 2: operations_test
2/3 Test #2: operations_test ..................   Passed    0.01 sec
    Start 3: integration_test
3/3 Test #3: integration_test .................   Passed    0.15 sec

100% tests passed, 0 tests failed out of 3
```

**With --output-on-failure**:
```
Test project /path/to/build
    Start 1: calculator_test
1/1 Test #1: calculator_test ..................***Failed    0.02 sec
Running main() from gtest_main.cc
[==========] Running 5 tests from 1 test suite.
[----------] Global test environment set-up.
[----------] 5 tests from CalculatorTest
[ RUN      ] CalculatorTest.Add
[       OK ] CalculatorTest.Add (0 ms)
[ RUN      ] CalculatorTest.Divide
tests/calculator_test.cpp:25: Failure
Value of: result
  Actual: 0
Expected: 5
[  FAILED  ] CalculatorTest.Divide (1 ms)
```

---

## Common Patterns

### Test Fixture Libraries

**Shared Test Utilities**:
```cmake
# Test helper library
add_library(test_helpers
    tests/helpers/test_utils.cpp
    tests/helpers/mock_data.cpp
)
target_link_libraries(test_helpers PUBLIC GTest::GTest)
target_include_directories(test_helpers PUBLIC tests/helpers)

# Use in test executables
add_executable(calculator_test tests/calculator_test.cpp)
target_link_libraries(calculator_test PRIVATE
    calculator
    test_helpers
    GTest::Main
)
```

---

### Custom Test Commands

**Wrapper Scripts**:
```cmake
# Add custom test that runs script
add_test(NAME run_integration_script
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/run_integration_tests.sh
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
```

**Parameterized Tests**:
```cmake
# Run same test with different arguments
foreach(dataset IN ITEMS small medium large)
    add_test(NAME performance_test_${dataset}
        COMMAND perf_test --dataset=${dataset}
    )
endforeach()
```

---

### Test Data Files

**Copy Test Data to Build**:
```cmake
# Copy test data files
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/tests/data
     DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/tests)

# Or use configure_file for templating
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/config.ini.in
    ${CMAKE_CURRENT_BINARY_DIR}/tests/config.ini
    @ONLY
)
```

**Install Test Data**:
```cmake
# Install test data with test executable
install(TARGETS calculator_test DESTINATION bin)
install(DIRECTORY tests/data DESTINATION share/calculator/tests)
```

---

### Header-Only Libraries

**Interface Library** (for header-only code):
```cmake
# Header-only library
add_library(calculator INTERFACE)
target_include_directories(calculator INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(calculator INTERFACE cxx_std_17)

# Test executable
add_executable(calculator_test tests/calculator_test.cpp)
target_link_libraries(calculator_test PRIVATE
    calculator
    GTest::Main
)
```

---

## Complete CMakeLists.txt Examples

### Example 1: Simple Project with Google Test

```cmake
cmake_minimum_required(VERSION 3.15)
project(Calculator VERSION 1.0.0 LANGUAGES CXX)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Options
option(BUILD_TESTS "Build tests" ON)
option(ENABLE_COVERAGE "Enable code coverage" OFF)

# Main library
add_library(calculator
    src/calculator.cpp
    src/operations.cpp
)

target_include_directories(calculator PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Compiler warnings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(calculator PRIVATE
        -Wall -Wextra -Wpedantic
    )
elseif(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    target_compile_options(calculator PRIVATE /W4)
endif()

# Tests
if(BUILD_TESTS)
    # Fetch Google Test
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    # Enable testing
    include(GoogleTest)
    enable_testing()

    # Test executable
    add_executable(calculator_test
        tests/calculator_test.cpp
        tests/operations_test.cpp
    )

    target_link_libraries(calculator_test PRIVATE
        calculator
        GTest::gtest
        GTest::gtest_main
    )

    # Discover tests
    gtest_discover_tests(calculator_test)

    # Coverage
    if(ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(calculator PRIVATE --coverage)
        target_link_options(calculator PRIVATE --coverage)
    endif()
endif()

# Install
install(TARGETS calculator
    EXPORT CalculatorTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
```

---

### Example 2: Multi-Directory Project

**Root CMakeLists.txt**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(AdvancedCalculator VERSION 2.0.0 LANGUAGES CXX)

# Global settings
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Options
option(BUILD_TESTS "Build tests" ON)
option(BUILD_DOCS "Build documentation" OFF)

# Subdirectories
add_subdirectory(src)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

**src/CMakeLists.txt**:
```cmake
# Core library
add_library(calculator_core
    calculator.cpp
    operations.cpp
)

target_include_directories(calculator_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
)

# Advanced features library
add_library(calculator_advanced
    advanced_ops.cpp
    scientific.cpp
)

target_link_libraries(calculator_advanced PUBLIC calculator_core)
```

**tests/CMakeLists.txt**:
```cmake
# Fetch Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

include(GoogleTest)

# Unit tests
add_executable(unit_tests
    calculator_test.cpp
    operations_test.cpp
)

target_link_libraries(unit_tests PRIVATE
    calculator_core
    GTest::gtest_main
)

gtest_discover_tests(unit_tests
    PROPERTIES LABELS "unit"
)

# Integration tests
add_executable(integration_tests
    integration_test.cpp
)

target_link_libraries(integration_tests PRIVATE
    calculator_advanced
    GTest::gtest_main
)

gtest_discover_tests(integration_tests
    PROPERTIES LABELS "integration"
)
```

---

### Example 3: Catch2 Project

```cmake
cmake_minimum_required(VERSION 3.15)
project(MathLib VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

# Library
add_library(mathlib
    src/mathlib.cpp
)

target_include_directories(mathlib PUBLIC include)

# Tests
option(BUILD_TESTS "Build tests" ON)

if(BUILD_TESTS)
    # Fetch Catch2 v3
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG v3.5.0
    )
    FetchContent_MakeAvailable(Catch2)

    # Enable testing
    enable_testing()

    # Test executable
    add_executable(mathlib_test
        tests/mathlib_test.cpp
    )

    target_link_libraries(mathlib_test PRIVATE
        mathlib
        Catch2::Catch2WithMain
    )

    # Discover tests
    list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
    include(Catch)
    catch_discover_tests(mathlib_test)
endif()
```

---

## Best Practices

1. **Use Modern CMake (3.15+)**
   - Target-based approach with `target_*` commands
   - Generator expressions for conditional configuration
   - Avoid global variables like `CMAKE_CXX_FLAGS`

2. **Always Use Out-of-Source Builds**
   - Never build in source directory
   - Use `build/` directory (add to .gitignore)
   - Supports multiple build configurations

3. **Specify C++ Standard Per-Target**
   ```cmake
   target_compile_features(mylib PUBLIC cxx_std_17)
   # Instead of: set(CMAKE_CXX_STANDARD 17)
   ```

4. **Use PRIVATE/PUBLIC/INTERFACE Keywords**
   ```cmake
   target_link_libraries(mylib
       PRIVATE internal_dep      # Only for mylib
       PUBLIC external_api       # For mylib and consumers
       INTERFACE header_only     # Only for consumers
   )
   ```

5. **Enable Warnings and Treat as Errors**
   ```cmake
   target_compile_options(mylib PRIVATE -Wall -Wextra -Werror)
   ```

6. **Use FetchContent for Dependencies**
   - Better than git submodules
   - Automatic download and build
   - Version control in CMakeLists.txt

7. **Discover Tests Automatically**
   ```cmake
   gtest_discover_tests(my_test)
   # Instead of: add_test(NAME my_test COMMAND my_test)
   ```

8. **Separate Source and Test Directories**
   ```
   project/
   ├── src/         # Source files
   ├── include/     # Public headers
   └── tests/       # Test files
   ```

9. **Use CTest Labels for Test Organization**
   ```cmake
   set_tests_properties(my_test PROPERTIES LABELS "unit;fast")
   # Run with: ctest -L unit
   ```

10. **Enable Code Coverage in CI/CD**
    ```cmake
    if(ENABLE_COVERAGE)
        target_compile_options(mylib PRIVATE --coverage)
        target_link_options(mylib PRIVATE --coverage)
    endif()
    ```

11. **Use Presets for Common Configurations** (CMake 3.19+)
    ```json
    // CMakePresets.json
    {
      "version": 3,
      "configurePresets": [
        {
          "name": "debug",
          "binaryDir": "build/debug",
          "cacheVariables": {
            "CMAKE_BUILD_TYPE": "Debug"
          }
        }
      ]
    }
    ```

12. **Set Test Timeouts**
    ```cmake
    set_tests_properties(my_test PROPERTIES TIMEOUT 30)
    ```

---

## Troubleshooting

### Problem: Google Test Not Found

```bash
# Solution 1: Install system-wide (Ubuntu/Debian)
sudo apt-get install libgtest-dev

# Solution 2: Use FetchContent (recommended)
# Add FetchContent_Declare in CMakeLists.txt

# Solution 3: Use Conan or vcpkg
conan install gtest/1.14.0
```

---

### Problem: Tests Not Discovered

```bash
# Check if enable_testing() is called
# Check if add_test() or gtest_discover_tests() is used

# List all tests
cd build
ctest -N

# Or use CMake
cmake --build build --target help | grep test
```

---

### Problem: Out-of-Source Build Issues

```bash
# Always build from build directory
rm -rf build/  # Clean old build
mkdir build
cd build
cmake ..
cmake --build .
```

---

### Problem: Compiler Not Found

```bash
# Specify compiler explicitly
cmake -DCMAKE_CXX_COMPILER=g++ ..
cmake -DCMAKE_CXX_COMPILER=clang++ ..

# On Windows with MSVC
cmake -G "Visual Studio 17 2022" ..
```

---

### Problem: C++ Standard Not Supported

```bash
# Check compiler version
g++ --version
clang++ --version

# Use older standard if needed
set(CMAKE_CXX_STANDARD 14)  # Instead of 17

# Or install newer compiler
```

---

### Problem: Tests Fail Only in CI/CD

```bash
# Run tests verbosely
ctest -V

# Check test output
ctest --output-on-failure

# Ensure dependencies are available
# Check test data files exist
# Verify environment variables
```

---

### Problem: Slow Test Discovery

```cmake
# Disable test discovery at configure time (for very large projects)
gtest_discover_tests(my_test
    DISCOVERY_MODE PRE_TEST  # Discover at test time, not configure time
)
```

---

## Related Skills

- **cpp-test-locations.md**: C++ test file location detection and conventions
- **cpp-frameworks.md**: C++ test framework detection (Google Test, Catch2)
- **cpp-templates.md**: C++ test template generation for Google Test and Catch2
- **cpp-parsers.md**: C++ source code parsing for test generation
- **conan-package-manager.md**: Conan integration for C++ dependencies
- **vcpkg-package-manager.md**: vcpkg integration for C++ dependencies

---

**Last Updated**: 2026-01-06
**Phase**: 4 - Systems Languages (TASK-CPP-006)
**Status**: Complete
