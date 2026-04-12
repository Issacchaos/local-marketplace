# C++ Framework Detection

**Version**: 1.0.0
**Language**: C++
**Frameworks**: Google Test (gtest/gmock), Catch2
**Build Systems**: CMake, Make, Bazel
**Status**: Phase 4 - Systems Languages

## Overview

C++ framework detection skill for identifying C++ test frameworks (Google Test, Catch2) and build systems (CMake, Make, Bazel) in C++ projects. This skill provides detailed detection patterns, confidence scoring, build system integration, and compiler/standard detection.

## Critical Distinction: Build System and Compiler Required

**C++ projects require a build system and compiler to run tests.** This skill detects:
1. **Build System** (CMake, Make, Bazel) - Required for building and running tests
2. **Testing Framework** (Google Test, Catch2) - Multiple can coexist
3. **Compiler** (GCC, Clang, MSVC) - Determines compilation flags
4. **C++ Standard** (C++11/14/17/20/23) - Affects language features

## Supported Testing Frameworks

### 1. Google Test (gtest/gmock)

**Description**: Google's C++ testing and mocking framework
**Official Docs**: https://google.github.io/googletest/
**Minimum Version**: 1.10.0+
**Detection Priority**: High (industry standard)

**Key Components**:
- **gtest**: Test framework with TEST, TEST_F macros
- **gmock**: Mocking framework with EXPECT_CALL

**Key Features**:
- `TEST()` and `TEST_F()` macros
- `EXPECT_*` and `ASSERT_*` assertions
- Test fixtures with `testing::Test`
- Parameterized tests with `TEST_P()`
- Death tests with `EXPECT_DEATH()`
- Google Mock for mocking

### 2. Catch2

**Description**: Modern, header-only C++ testing framework
**Official Docs**: https://github.com/catchorg/Catch2
**Minimum Version**: 2.13.0+ or 3.0.0+
**Detection Priority**: High (popular for modern C++ projects)

**Key Features**:
- `TEST_CASE()` and `SECTION()` macros
- `REQUIRE()` and `CHECK()` assertions
- BDD-style testing (SCENARIO, GIVEN, WHEN, THEN)
- Header-only (v2) or compiled (v3)
- Natural assertion syntax

## Supported Build Systems

### 1. CMake

**Description**: Cross-platform build system generator
**Official Docs**: https://cmake.org/
**Minimum Version**: 3.15+
**Detection Priority**: High (modern standard)

**Key Files**:
- `CMakeLists.txt`
- `cmake/` directory
- `build/` directory (out-of-source builds)

**Key Features**:
- `find_package(GTest)` for Google Test
- `FetchContent` for Catch2
- `enable_testing()` and `add_test()`
- CTest integration

### 2. Make

**Description**: Traditional Unix build automation tool
**Official Docs**: https://www.gnu.org/software/make/
**Detection Priority**: Medium (legacy projects)

**Key Files**:
- `Makefile`
- `makefile`

**Key Features**:
- Targets for building and testing
- Manual compilation rules
- Test targets (e.g., `make test`)

### 3. Bazel

**Description**: Google's build and test tool
**Official Docs**: https://bazel.build/
**Minimum Version**: 4.0+
**Detection Priority**: Medium (enterprise/Google projects)

**Key Files**:
- `BUILD` or `BUILD.bazel`
- `WORKSPACE` or `WORKSPACE.bazel`

**Key Features**:
- `cc_test()` rules
- Hermetic builds
- Fast incremental builds

## Detection Strategy

### Phase 1: Build System Detection (Required)

Detect CMake, Make, or Bazel first, as this determines how to detect frameworks.

```python
def detect_cpp_build_system(project_path):
    build_system = None
    confidence = 0.0
    evidence = []

    # Check for CMake (highest priority)
    cmake_files = glob(join(project_path, "**/CMakeLists.txt"), recursive=True)
    if cmake_files:
        build_system = "cmake"
        confidence = 1.0
        evidence.append(f"CMakeLists.txt found: {len(cmake_files)} file(s)")

        # Check for build directory
        if exists(join(project_path, "build")):
            evidence.append("build/ directory found (out-of-source build)")

        # Check for CMakeCache.txt (already configured)
        if exists(join(project_path, "build/CMakeCache.txt")):
            evidence.append("CMakeCache.txt found (project configured)")

    # Check for Bazel
    elif exists(join(project_path, "WORKSPACE")) or \
         exists(join(project_path, "WORKSPACE.bazel")):
        build_system = "bazel"
        confidence = 1.0
        evidence.append("WORKSPACE file found")

        # Check for BUILD files
        build_files = glob(join(project_path, "**/BUILD*"), recursive=True)
        if build_files:
            evidence.append(f"BUILD files found: {len(build_files)} file(s)")

    # Check for Makefile (lowest priority)
    elif exists(join(project_path, "Makefile")) or \
         exists(join(project_path, "makefile")):
        build_system = "make"
        confidence = 0.8  # Lower confidence (Makefile might be legacy)
        evidence.append("Makefile found")

        # Check for test target
        try:
            makefile_content = read_file(join(project_path, "Makefile"))
            if re.search(r"^test:", makefile_content, re.MULTILINE):
                evidence.append("'test' target found in Makefile")
                confidence = 1.0
        except:
            pass

    return {
        "build_system": build_system,
        "confidence": confidence,
        "evidence": evidence
    }
```

### Phase 2: Framework Detection

Detect testing framework based on build system configuration and source code.

## CMake Detection Patterns

### CMake: Google Test Detection (Weight: 15)

**CMakeLists.txt with find_package**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Google Test
find_package(GTest REQUIRED)
# OR
find_package(googletest REQUIRED)

enable_testing()

add_executable(my_test test/my_test.cpp)
target_link_libraries(my_test GTest::GTest GTest::Main)
# OR
target_link_libraries(my_test gtest gtest_main gmock)

add_test(NAME my_test COMMAND my_test)
```

**Detection Logic**:
```python
def parse_cmake_for_gtest(cmake_path):
    score = 0
    evidence = []

    try:
        content = read_file(cmake_path)

        # find_package(GTest) or find_package(googletest)
        if re.search(r"find_package\s*\(\s*GTest", content, re.IGNORECASE):
            score += 15
            evidence.append("find_package(GTest) found in CMakeLists.txt")
        elif re.search(r"find_package\s*\(\s*googletest", content, re.IGNORECASE):
            score += 15
            evidence.append("find_package(googletest) found in CMakeLists.txt")

        # FetchContent for Google Test
        if re.search(r"FetchContent_Declare\s*\(\s*googletest", content, re.IGNORECASE):
            score += 12
            evidence.append("FetchContent for googletest found")

        # Link libraries
        if re.search(r"GTest::GTest|GTest::Main", content):
            score += 8
            evidence.append("GTest::GTest or GTest::Main linking found")
        elif re.search(r"\bgtest\b|\bgtest_main\b|\bgmock\b", content):
            score += 8
            evidence.append("gtest/gmock library linking found")

        # enable_testing() and add_test()
        if re.search(r"enable_testing\s*\(\s*\)", content):
            score += 5
            evidence.append("enable_testing() found")

        if re.search(r"add_test\s*\(", content):
            score += 3
            evidence.append("add_test() found")

        # CTest configuration
        if re.search(r"include\s*\(\s*CTest\s*\)", content):
            score += 5
            evidence.append("CTest integration found")

    except Exception as e:
        evidence.append(f"Error parsing CMakeLists.txt: {e}")

    return score, evidence
```

### CMake: Catch2 Detection (Weight: 15)

**CMakeLists.txt with Catch2**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)

# Catch2 v3 (recommended)
find_package(Catch2 3 REQUIRED)

# OR Catch2 v2 (legacy)
# FetchContent_Declare(
#   Catch2
#   GIT_REPOSITORY https://github.com/catchorg/Catch2.git
#   GIT_TAG v2.13.9
# )
# FetchContent_MakeAvailable(Catch2)

add_executable(my_test test/my_test.cpp)
target_link_libraries(my_test PRIVATE Catch2::Catch2WithMain)
# OR Catch2 v2
# target_link_libraries(my_test PRIVATE Catch2::Catch2)

enable_testing()
add_test(NAME my_test COMMAND my_test)
```

**Detection Logic**:
```python
def parse_cmake_for_catch2(cmake_path):
    score = 0
    evidence = []

    try:
        content = read_file(cmake_path)

        # find_package(Catch2)
        if re.search(r"find_package\s*\(\s*Catch2", content, re.IGNORECASE):
            score += 15
            evidence.append("find_package(Catch2) found in CMakeLists.txt")

            # Check version (v3 is modern)
            if re.search(r"find_package\s*\(\s*Catch2\s+3", content):
                evidence.append("Catch2 v3 detected")

        # FetchContent for Catch2
        if re.search(r"FetchContent_Declare\s*\(\s*Catch2", content, re.IGNORECASE):
            score += 12
            evidence.append("FetchContent for Catch2 found")

        # Link libraries
        if re.search(r"Catch2::Catch2WithMain|Catch2::Catch2", content):
            score += 8
            evidence.append("Catch2 library linking found")

    except Exception as e:
        evidence.append(f"Error parsing CMakeLists.txt: {e}")

    return score, evidence
```

### CMake: Compiler Detection

```python
def detect_cmake_compiler(project_path):
    compiler = None
    evidence = []

    # Check CMakeCache.txt if exists
    cache_file = join(project_path, "build/CMakeCache.txt")
    if exists(cache_file):
        try:
            content = read_file(cache_file)

            # CMAKE_CXX_COMPILER value
            match = re.search(r"CMAKE_CXX_COMPILER:FILEPATH=(.+)", content)
            if match:
                compiler_path = match.group(1)
                evidence.append(f"CMAKE_CXX_COMPILER: {compiler_path}")

                # Detect compiler type from path
                if "g++" in compiler_path or "gcc" in compiler_path:
                    compiler = "gcc"
                elif "clang++" in compiler_path or "clang" in compiler_path:
                    compiler = "clang"
                elif "cl.exe" in compiler_path or "msvc" in compiler_path.lower():
                    compiler = "msvc"
        except:
            pass

    # Check CMakeLists.txt for compiler hints
    cmake_files = glob(join(project_path, "**/CMakeLists.txt"), recursive=True)
    for cmake_file in cmake_files[:5]:  # Sample first 5
        try:
            content = read_file(cmake_file)

            # CMAKE_CXX_COMPILER_ID checks
            if re.search(r'CMAKE_CXX_COMPILER_ID.*"GNU"', content):
                compiler = compiler or "gcc"
                evidence.append("GNU/GCC compiler check in CMakeLists.txt")
            elif re.search(r'CMAKE_CXX_COMPILER_ID.*"Clang"', content):
                compiler = compiler or "clang"
                evidence.append("Clang compiler check in CMakeLists.txt")
            elif re.search(r'CMAKE_CXX_COMPILER_ID.*"MSVC"', content):
                compiler = compiler or "msvc"
                evidence.append("MSVC compiler check in CMakeLists.txt")
        except:
            continue

    return compiler, evidence
```

### CMake: C++ Standard Detection

```python
def detect_cpp_standard(project_path):
    standard = None
    evidence = []

    cmake_files = glob(join(project_path, "**/CMakeLists.txt"), recursive=True)

    for cmake_file in cmake_files:
        try:
            content = read_file(cmake_file)

            # CMAKE_CXX_STANDARD
            match = re.search(r"set\s*\(\s*CMAKE_CXX_STANDARD\s+(\d+)", content)
            if match:
                standard = f"C++{match.group(1)}"
                evidence.append(f"CMAKE_CXX_STANDARD {match.group(1)} in {cmake_file}")
                break

            # target_compile_features
            match = re.search(r"target_compile_features\([^)]*cxx_std_(\d+)", content)
            if match:
                standard = f"C++{match.group(1)}"
                evidence.append(f"cxx_std_{match.group(1)} in {cmake_file}")
                break

            # Compiler flags
            if re.search(r"-std=c\+\+(\d+)", content):
                match = re.search(r"-std=c\+\+(\d+)", content)
                standard = f"C++{match.group(1)}"
                evidence.append(f"-std=c++{match.group(1)} flag in {cmake_file}")
                break
        except:
            continue

    # Default if not found
    if not standard:
        standard = "C++17"  # Modern default
        evidence.append("No explicit standard found, defaulting to C++17")

    return standard, evidence
```

## Source Code Pattern Detection

### Google Test Patterns (Weight: 5)

**Google Test Test File**:
```cpp
#include <gtest/gtest.h>
// OR
#include "gtest/gtest.h"

// Simple test
TEST(CalculatorTest, Addition) {
    // Arrange
    Calculator calc;

    // Act
    int result = calc.add(2, 3);

    // Assert
    EXPECT_EQ(5, result);
}

// Test fixture
class DatabaseTest : public ::testing::Test {
protected:
    void SetUp() override {
        db = new Database();
    }

    void TearDown() override {
        delete db;
    }

    Database* db;
};

TEST_F(DatabaseTest, InsertRecord) {
    // Arrange
    Record record{1, "Alice"};

    // Act
    db->insert(record);

    // Assert
    EXPECT_EQ(1, db->count());
}

// Parameterized test
class AdditionTest : public ::testing::TestWithParam<std::tuple<int, int, int>> {};

TEST_P(AdditionTest, AddNumbers) {
    auto [a, b, expected] = GetParam();
    EXPECT_EQ(expected, add(a, b));
}

INSTANTIATE_TEST_SUITE_P(
    AdditionTests,
    AdditionTest,
    ::testing::Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(5, 5, 10)
    )
);
```

**Google Mock Example**:
```cpp
#include <gmock/gmock.h>
#include <gtest/gtest.h>

class MockDatabase : public IDatabase {
public:
    MOCK_METHOD(void, insert, (const Record&), (override));
    MOCK_METHOD(int, count, (), (const, override));
};

TEST(UserServiceTest, ProcessUser) {
    // Arrange
    MockDatabase mockDb;
    EXPECT_CALL(mockDb, insert(::testing::_))
        .Times(1);

    UserService service(&mockDb);

    // Act
    service.processUser(User{1, "Alice"});

    // Assert
    // Expectations verified automatically
}
```

**Detection Patterns**:
```python
def detect_gtest_in_source(project_path):
    score = 0
    evidence = []

    # Look for test files
    test_patterns = [
        "**/test/**/*.cpp",
        "**/test/**/*.cc",
        "**/tests/**/*.cpp",
        "**/*_test.cpp",
        "**/*_unittest.cpp",
        "**/test_*.cpp"
    ]

    test_files = []
    for pattern in test_patterns:
        test_files.extend(glob(join(project_path, pattern), recursive=True))

    # Sample up to 10 test files
    sample_files = test_files[:10]

    for test_file in sample_files:
        try:
            content = read_file(test_file)

            # Check for gtest headers
            if re.search(r'#include\s+[<"]gtest/gtest\.h[>"]', content):
                score += 5
                evidence.append(f"#include <gtest/gtest.h> in {test_file}")
                break

            # Check for gmock headers
            if re.search(r'#include\s+[<"]gmock/gmock\.h[>"]', content):
                score += 3
                evidence.append(f"#include <gmock/gmock.h> in {test_file}")

            # Check for TEST macros
            if re.search(r'\bTEST\s*\(', content):
                score += 3
                evidence.append(f"TEST() macro found in {test_file}")

            # Check for TEST_F macros
            if re.search(r'\bTEST_F\s*\(', content):
                score += 2
                evidence.append(f"TEST_F() macro found in {test_file}")

            # Check for EXPECT_ assertions
            if re.search(r'\bEXPECT_(EQ|NE|LT|GT|TRUE|FALSE)', content):
                evidence.append(f"EXPECT_* assertions found in {test_file}")

            # Check for ASSERT_ assertions
            if re.search(r'\bASSERT_(EQ|NE|LT|GT|TRUE|FALSE)', content):
                evidence.append(f"ASSERT_* assertions found in {test_file}")

        except:
            continue

    return score, evidence
```

### Catch2 Patterns (Weight: 5)

**Catch2 v3 Test File**:
```cpp
#include <catch2/catch_test_macros.hpp>
// OR Catch2 v2
// #include <catch2/catch.hpp>

TEST_CASE("Calculator addition", "[calculator]") {
    Calculator calc;

    SECTION("positive numbers") {
        REQUIRE(calc.add(2, 3) == 5);
    }

    SECTION("negative numbers") {
        REQUIRE(calc.add(-2, -3) == -5);
    }
}

// BDD-style test
SCENARIO("User authentication", "[auth]") {
    GIVEN("a valid user") {
        User user{"alice", "password123"};

        WHEN("user logs in") {
            bool result = authenticate(user);

            THEN("authentication succeeds") {
                REQUIRE(result == true);
            }
        }
    }
}

// Parameterized test (Catch2 v3)
TEST_CASE("Addition works", "[math]") {
    auto [a, b, expected] = GENERATE(table<int, int, int>({
        {1, 2, 3},
        {5, 5, 10},
        {-1, 1, 0}
    }));

    REQUIRE(add(a, b) == expected);
}
```

**Detection Patterns**:
```python
def detect_catch2_in_source(project_path):
    score = 0
    evidence = []

    # Look for test files
    test_patterns = [
        "**/test/**/*.cpp",
        "**/tests/**/*.cpp",
        "**/*_test.cpp"
    ]

    test_files = []
    for pattern in test_patterns:
        test_files.extend(glob(join(project_path, pattern), recursive=True))

    sample_files = test_files[:10]

    for test_file in sample_files:
        try:
            content = read_file(test_file)

            # Check for Catch2 headers
            if re.search(r'#include\s+[<"]catch2/catch_test_macros\.hpp[>"]', content):
                score += 5
                evidence.append(f"Catch2 v3 header in {test_file}")
                break
            elif re.search(r'#include\s+[<"]catch2/catch\.hpp[>"]', content):
                score += 5
                evidence.append(f"Catch2 v2 header in {test_file}")
                break

            # Check for TEST_CASE macro
            if re.search(r'\bTEST_CASE\s*\(', content):
                score += 3
                evidence.append(f"TEST_CASE() macro found in {test_file}")

            # Check for SECTION macro
            if re.search(r'\bSECTION\s*\(', content):
                score += 2
                evidence.append(f"SECTION() macro found in {test_file}")

            # Check for SCENARIO (BDD)
            if re.search(r'\bSCENARIO\s*\(', content):
                score += 2
                evidence.append(f"SCENARIO() (BDD) found in {test_file}")

            # Check for REQUIRE/CHECK assertions
            if re.search(r'\b(REQUIRE|CHECK)\s*\(', content):
                evidence.append(f"REQUIRE/CHECK assertions found in {test_file}")

        except:
            continue

    return score, evidence
```

## Make Detection Patterns

### Makefile Analysis

**Makefile with Test Target**:
```makefile
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra
LDFLAGS = -lgtest -lgtest_main -lpthread

TEST_SRC = test/my_test.cpp
TEST_BIN = test/my_test

all: $(TEST_BIN)

$(TEST_BIN): $(TEST_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

test: $(TEST_BIN)
	./$(TEST_BIN)

clean:
	rm -f $(TEST_BIN)

.PHONY: all test clean
```

**Detection Logic**:
```python
def parse_makefile_for_frameworks(makefile_path):
    frameworks = {
        "gtest": 0,
        "catch2": 0
    }
    evidence = []
    compiler = None
    standard = None

    try:
        content = read_file(makefile_path)

        # Google Test detection
        if re.search(r"-lgtest|-lgtest_main", content):
            frameworks["gtest"] += 10
            evidence.append("Google Test linking flags found in Makefile")

        if re.search(r"-lgmock", content):
            frameworks["gtest"] += 3
            evidence.append("Google Mock linking flags found in Makefile")

        # Catch2 detection
        if re.search(r"catch2|Catch2", content, re.IGNORECASE):
            frameworks["catch2"] += 10
            evidence.append("Catch2 references found in Makefile")

        # Compiler detection
        if re.search(r"CXX\s*=\s*g\+\+", content):
            compiler = "gcc"
            evidence.append("g++ compiler specified in Makefile")
        elif re.search(r"CXX\s*=\s*clang\+\+", content):
            compiler = "clang"
            evidence.append("clang++ compiler specified in Makefile")

        # C++ standard detection
        match = re.search(r"-std=c\+\+(\d+)", content)
        if match:
            standard = f"C++{match.group(1)}"
            evidence.append(f"C++ standard: {standard}")

        # Test target
        if re.search(r"^test:", content, re.MULTILINE):
            evidence.append("'test' target found in Makefile")

    except Exception as e:
        evidence.append(f"Error parsing Makefile: {e}")

    return frameworks, compiler, standard, evidence
```

## Bazel Detection Patterns

### BUILD File Analysis

**BUILD file with cc_test**:
```python
cc_library(
    name = "calculator",
    srcs = ["calculator.cpp"],
    hdrs = ["calculator.h"],
)

cc_test(
    name = "calculator_test",
    srcs = ["calculator_test.cpp"],
    deps = [
        ":calculator",
        "@com_google_googletest//:gtest_main",
    ],
)
```

**Detection Logic**:
```python
def parse_bazel_for_frameworks(project_path):
    frameworks = {
        "gtest": 0,
        "catch2": 0
    }
    evidence = []

    # Find BUILD files
    build_files = []
    build_files.extend(glob(join(project_path, "**/BUILD"), recursive=True))
    build_files.extend(glob(join(project_path, "**/BUILD.bazel"), recursive=True))

    for build_file in build_files[:10]:
        try:
            content = read_file(build_file)

            # cc_test rule
            if re.search(r"cc_test\s*\(", content):
                evidence.append(f"cc_test rule found in {build_file}")

            # Google Test detection
            if re.search(r"@com_google_googletest|@googletest", content):
                frameworks["gtest"] += 10
                evidence.append(f"Google Test dependency in {build_file}")

            # Catch2 detection
            if re.search(r"@catch2|@com_github_catchorg_catch2", content):
                frameworks["catch2"] += 10
                evidence.append(f"Catch2 dependency in {build_file}")

        except:
            continue

    return frameworks, evidence
```

## Complete Detection Function

```python
def detect_cpp_framework(project_path):
    # Phase 1: Detect build system (required)
    build_result = detect_cpp_build_system(project_path)

    if build_result["build_system"] is None:
        return {
            "success": False,
            "error": "No C++ build system detected (need CMakeLists.txt, Makefile, or Bazel WORKSPACE)",
            "build_system": None,
            "framework": None
        }

    build_system = build_result["build_system"]
    all_evidence = build_result["evidence"].copy()

    # Phase 2: Detect testing framework based on build system
    frameworks_score = {
        "gtest": 0,
        "catch2": 0
    }
    compiler = None
    cpp_standard = None

    if build_system == "cmake":
        # Parse all CMakeLists.txt files
        cmake_files = glob(join(project_path, "**/CMakeLists.txt"), recursive=True)

        for cmake_file in cmake_files:
            # Google Test
            score, evidence = parse_cmake_for_gtest(cmake_file)
            frameworks_score["gtest"] += score
            all_evidence.extend(evidence)

            # Catch2
            score, evidence = parse_cmake_for_catch2(cmake_file)
            frameworks_score["catch2"] += score
            all_evidence.extend(evidence)

        # Detect compiler and standard
        compiler, comp_evidence = detect_cmake_compiler(project_path)
        all_evidence.extend(comp_evidence)

        cpp_standard, std_evidence = detect_cpp_standard(project_path)
        all_evidence.extend(std_evidence)

    elif build_system == "make":
        makefile_path = join(project_path, "Makefile")
        if not exists(makefile_path):
            makefile_path = join(project_path, "makefile")

        if exists(makefile_path):
            scores, compiler, cpp_standard, evidence = parse_makefile_for_frameworks(makefile_path)
            frameworks_score["gtest"] += scores["gtest"]
            frameworks_score["catch2"] += scores["catch2"]
            all_evidence.extend(evidence)

    elif build_system == "bazel":
        scores, evidence = parse_bazel_for_frameworks(project_path)
        frameworks_score["gtest"] += scores["gtest"]
        frameworks_score["catch2"] += scores["catch2"]
        all_evidence.extend(evidence)

        # Bazel typically uses Clang or GCC
        compiler = "gcc"  # Default assumption
        all_evidence.append("Bazel detected, assuming GCC/Clang compiler")

    # Phase 3: Check source code patterns
    gtest_score, gtest_evidence = detect_gtest_in_source(project_path)
    frameworks_score["gtest"] += gtest_score
    all_evidence.extend(gtest_evidence)

    catch2_score, catch2_evidence = detect_catch2_in_source(project_path)
    frameworks_score["catch2"] += catch2_score
    all_evidence.extend(catch2_evidence)

    # Select primary framework
    result = select_primary_cpp_framework(frameworks_score)

    # Get test command
    test_cmd = get_cpp_test_command(build_system, project_path)

    return {
        "success": True,
        "build_system": build_system,
        "framework": result["framework"],
        "confidence": result["confidence"],
        "compiler": compiler or "gcc",
        "cpp_standard": cpp_standard or "C++17",
        "evidence": all_evidence,
        "test_command": test_cmd["command"],
        "test_reports_dir": test_cmd.get("test_reports_dir"),
        "build_dir": test_cmd.get("build_dir")
    }


def select_primary_cpp_framework(scores):
    total = sum(scores.values())

    if total == 0:
        # Default to Google Test (industry standard)
        return {
            "framework": "gtest",
            "confidence": 0.1,
            "reason": "Fallback default (Google Test is C++ standard)"
        }

    # Find highest scoring framework
    primary = max(scores, key=scores.get)
    confidence = min(scores[primary] / 30, 1.0)

    return {
        "framework": primary,
        "confidence": confidence,
        "reason": f"{primary} has highest score: {scores[primary]}"
    }


def get_cpp_test_command(build_system, project_path):
    if build_system == "cmake":
        return {
            "command": "cd build && ctest --output-on-failure",
            "build_command": "mkdir -p build && cd build && cmake .. && cmake --build .",
            "test_reports_dir": "build/Testing/Temporary",
            "build_dir": "build"
        }
    elif build_system == "make":
        return {
            "command": "make test",
            "build_command": "make all",
            "test_reports_dir": None,  # Varies by project
            "build_dir": "."
        }
    elif build_system == "bazel":
        return {
            "command": "bazel test //...",
            "build_command": "bazel build //...",
            "test_reports_dir": "bazel-testlogs",
            "build_dir": "bazel-bin"
        }
```

## Weighted Scoring Summary

| Detection Source | Google Test Score | Catch2 Score |
|------------------|-------------------|--------------|
| CMake find_package() | 15 | 15 |
| CMake FetchContent | 12 | 12 |
| CMake link libraries | 8 | 8 |
| CMake enable_testing() | 5 | - |
| CMake CTest | 5 | - |
| Makefile link flags | 10 | 10 |
| Bazel cc_test dep | 10 | 10 |
| Source code headers | 5 | 5 |
| TEST/TEST_F macros | 3 | - |
| TEST_CASE macro | - | 3 |
| SECTION macro | - | 2 |

**Confidence Threshold**: Score ≥ 25 = High confidence (≥0.8)

## Examples

### Example 1: CMake + Google Test

**Project Structure**:
```
my-project/
├── CMakeLists.txt
├── build/
├── src/
│   ├── calculator.cpp
│   └── calculator.h
└── test/
    └── calculator_test.cpp
```

**CMakeLists.txt**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(GTest REQUIRED)
enable_testing()

add_executable(calculator_test test/calculator_test.cpp)
target_link_libraries(calculator_test GTest::GTest GTest::Main)
add_test(NAME calculator_test COMMAND calculator_test)
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "cmake",
  "framework": "gtest",
  "confidence": 0.93,
  "compiler": "gcc",
  "cpp_standard": "C++17",
  "evidence": [
    "CMakeLists.txt found: 1 file(s)",
    "build/ directory found (out-of-source build)",
    "find_package(GTest) found in CMakeLists.txt",
    "GTest::GTest or GTest::Main linking found",
    "enable_testing() found",
    "add_test() found",
    "CMAKE_CXX_STANDARD 17 in CMakeLists.txt",
    "#include <gtest/gtest.h> in test/calculator_test.cpp",
    "TEST() macro found in test/calculator_test.cpp"
  ],
  "test_command": "cd build && ctest --output-on-failure",
  "build_command": "mkdir -p build && cd build && cmake .. && cmake --build .",
  "test_reports_dir": "build/Testing/Temporary",
  "build_dir": "build"
}
```

### Example 2: CMake + Catch2 v3

**CMakeLists.txt**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 20)

find_package(Catch2 3 REQUIRED)

add_executable(my_test test/my_test.cpp)
target_link_libraries(my_test PRIVATE Catch2::Catch2WithMain)

enable_testing()
add_test(NAME my_test COMMAND my_test)
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "cmake",
  "framework": "catch2",
  "confidence": 0.87,
  "compiler": "clang",
  "cpp_standard": "C++20",
  "evidence": [
    "CMakeLists.txt found: 1 file(s)",
    "find_package(Catch2) found in CMakeLists.txt",
    "Catch2 v3 detected",
    "Catch2 library linking found",
    "CMAKE_CXX_STANDARD 20 in CMakeLists.txt",
    "Clang compiler check in CMakeLists.txt",
    "Catch2 v3 header in test/my_test.cpp",
    "TEST_CASE() macro found in test/my_test.cpp"
  ],
  "test_command": "cd build && ctest --output-on-failure"
}
```

### Example 3: Makefile + Google Test

**Makefile**:
```makefile
CXX = g++
CXXFLAGS = -std=c++17 -Wall
LDFLAGS = -lgtest -lgtest_main -lpthread

test: calculator_test
	./calculator_test

calculator_test: test/calculator_test.cpp src/calculator.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "make",
  "framework": "gtest",
  "confidence": 0.67,
  "compiler": "gcc",
  "cpp_standard": "C++17",
  "evidence": [
    "Makefile found",
    "'test' target found in Makefile",
    "Google Test linking flags found in Makefile",
    "g++ compiler specified in Makefile",
    "C++ standard: C++17",
    "#include <gtest/gtest.h> in test/calculator_test.cpp"
  ],
  "test_command": "make test",
  "build_command": "make all"
}
```

## Edge Cases

### 1. Header-only Catch2 (v2)

**Scenario**: Catch2 v2 as single header file

**Strategy**:
- Check for `catch.hpp` file in project
- No CMake find_package needed
- Score based on header presence + TEST_CASE usage

### 2. Google Test as Submodule

**Scenario**: Google Test included as git submodule

**Strategy**:
- Check for `external/googletest/` or similar
- Check CMake `add_subdirectory(external/googletest)`
- Apply same scoring

### 3. Multi-Compiler Project

**Scenario**: CMake supports GCC and Clang

**Strategy**:
- Detect from CMakeCache.txt (actual compiler used)
- Fall back to CMAKE_CXX_COMPILER_ID checks
- Note both in evidence

### 4. No Standard Specified

**Scenario**: C++17 by default (compiler default)

**Strategy**:
- Check compiler version
- Default to C++17 for modern compilers
- Note as assumption

### 5. Conan Package Manager

**Scenario**: Google Test or Catch2 via Conan

**Strategy**:
- Check for `conanfile.txt` or `conanfile.py`
- Parse for `gtest/` or `catch2/` references
- Apply same scoring as CMake find_package

## Confidence Scoring

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 0.8 - 1.0 | High confidence | Proceed with detected framework |
| 0.5 - 0.79 | Medium confidence | Use detected framework, note in logs |
| 0.1 - 0.49 | Low confidence | Use fallback (Google Test), warn user |
| 0.0 - 0.09 | No detection | Error - need build system or framework |

## Best Practices

1. **CMake Preferred**: Modern C++ projects use CMake
2. **Out-of-source Builds**: Use `build/` directory for CMake
3. **Google Test Recommended**: Industry standard, comprehensive features
4. **Catch2 for Header-only**: Good for small projects, easy integration
5. **C++17 Minimum**: Modern standard with good compiler support
6. **Use Wrapper Scripts**: Provide `build.sh` and `test.sh` for consistency

## Test Execution Commands

| Build System | Framework | Build Command | Test Command |
|--------------|-----------|---------------|--------------|
| CMake | gtest/Catch2 | `cmake --build build` | `cd build && ctest` |
| Make | gtest/Catch2 | `make all` | `make test` |
| Bazel | gtest/Catch2 | `bazel build //...` | `bazel test //...` |

## References

- Google Test: https://google.github.io/googletest/
- Catch2: https://github.com/catchorg/Catch2
- CMake: https://cmake.org/documentation/
- CTest: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- Bazel C++ Rules: https://bazel.build/reference/be/c-cpp
- Modern CMake: https://cliutils.gitlab.io/modern-cmake/

---

**Last Updated**: 2025-12-10
**Phase**: 4 - Systems Languages
**Status**: Complete
