# UE LLT Test Fix Team

**Team Name**: ue-llt-fix-tests
**Purpose**: Fix failing UE Low Level Tests by analyzing failures, understanding API requirements, and correcting test code
**Orchestration**: Sequential with analysis → fix → verify workflow

---

## Team Composition

### Agent 1: Test Analyzer
- **Role**: Analyze test failures and understand root causes
- **Type**: general-purpose
- **Model**: sonnet
- **Tools**: Read, Grep, Bash
- **Mission**:
  1. Read the test execution output to identify failing tests
  2. Read the test source code to understand what's being tested
  3. Read the SecurePackageReader source to understand API requirements
  4. Analyze why the mock package data isn't working
  5. Document findings: what's failing, why, and what needs to change

### Agent 2: Test Fixer
- **Role**: Fix the test code based on analyzer findings
- **Type**: general-purpose
- **Model**: sonnet
- **Tools**: Read, Edit, Write
- **Dependencies**: test-analyzer
- **Mission**:
  1. Read the analyzer's findings
  2. Fix the FPackageFileSummary serialization in test fixtures
  3. Ensure mock package data matches SecurePackageReader expectations
  4. Update test assertions if API behavior differs from expectations
  5. Document all changes made

### Agent 3: Test Verifier
- **Role**: Build and run tests to verify fixes
- **Type**: general-purpose
- **Model**: sonnet
- **Tools**: Read, Bash
- **Dependencies**: test-fixer
- **Mission**:
  1. Rebuild the test module using UBT (see skills/build-integration/ue-build-system.md)
  2. Run the tests and capture output
  3. Verify all tests pass (12/12)
  4. If failures remain, document what still needs fixing
  5. Report final status

---

## Execution Context

**Target Path**: /Users/stephen.ma/Fornite_Main/FortniteGame/Plugins/ForEngine/ValkyrieEngine/Tests/SecurePackageReaderTests
**Test Module**: SecurePackageReaderTests
**Test Source**: SecurePackageReaderTests/Private/SecurePackageReaderTests.cpp
**Current Status**: 9 passed, 3 failed

### Known Failures
1. Line 159: `REQUIRE(bSuccess)` - Minimal valid package test failing
2. Line 222: `REQUIRE(PackageReader.IsCriticalError())` - Unversioned package test not triggering critical error
3. File size assertion: "file is too small (4 bytes, expected at least 32 bytes)"

### Key Files
- Test code: `SecurePackageReaderTests/Private/SecurePackageReaderTests.cpp`
- Module under test: `../../Source/SecurePackageReader/Private/SecurePackageReader.cpp`
- API header: `../../Source/SecurePackageReader/Public/SecurePackageReader.h`
- Build system docs: `skills/build-integration/ue-build-system.md`

### Build/Run Commands
```bash
# Build (from repo root)
cd /Users/stephen.ma/Fornite_Main
./Engine/Build/BatchFiles/Mac/Build.sh SecurePackageReaderTests Mac Development -Project="/Users/stephen.ma/Fornite_Main/FortniteGame/FortniteGame.uproject"

# Run (from repo root)
./FortniteGame/Binaries/Mac/SecurePackageReaderTests/SecurePackageReaderTests -r compact
```

---

## Success Criteria

- All 12 test cases pass
- No compilation errors
- No runtime assertions or crashes
- Tests validate SecurePackageReader security requirements correctly

---

## Orchestration Notes

- Agents run sequentially: analyzer → fixer → verifier
- Each agent produces a report for the next agent
- If verifier finds remaining failures, it reports back for manual review
- Team completes when all tests pass or max iterations reached
