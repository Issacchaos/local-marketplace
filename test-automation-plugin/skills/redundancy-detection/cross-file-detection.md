---
title: Cross-File Redundancy Detection Skill
version: 1.0.0
category: Test Generation
target_users: write-agent
user-invocable: false
created: 2026-02-19
last_updated: 2026-02-19
---

# Cross-File Redundancy Detection Skill

## Section 1 — Overview

### Purpose

This skill extends the write-agent's redundancy detection to span the entire test suite, not just the target test file. Before generating a test, the write-agent must check whether an equivalent test scenario already exists in any other test file of the same type in the project.

### Relationship to SKILL.md

This document **extends** `skills/redundancy-detection/SKILL.md` — it does not replace it. The existing SKILL.md defines:
- 17 equivalence classes and their classification rules
- Normalization rules (POSITIVE_SMALL / POSITIVE_LARGE → POSITIVE_SMALL, etc.)
- The 6-step same-file detection algorithm
- Edge case override logic (ZERO, EMPTY_*, NULL_UNDEFINED, BOUNDARY_MAX, BOUNDARY_MIN, FLOAT_PRECISION, ERROR_CONDITION, STATE_TRANSITION, EDGE_CASE_OTHER → always allow)
- Message templates for blocked tests

All of the above are **reused unchanged** by this skill. Do not re-implement or re-define them here. Reference SKILL.md directly when applying equivalence class comparison, normalization, and edge case override during cross-file detection.

The two skills operate in sequence within Step 4 of the write-agent workflow:
1. **Step A — Same-file check** (SKILL.md): Detects redundancy within the current target test file.
2. **Step B — Cross-file check (this skill)**: Runs only if Step A passes. Detects redundancy across all other test files of the same type.

### When to Use This Skill

Read this skill alongside SKILL.md at the start of the write-agent workflow (Step 1 — Load Context). Apply the cross-file check in Step 4 for every proposed test, after the same-file check has passed.

Do **not** apply the cross-file check if:
- The same-file check already blocked the proposed test (no need to proceed).
- The proposed test carries an edge case equivalence class (ZERO, EMPTY_*, NULL_UNDEFINED, BOUNDARY_MAX, BOUNDARY_MIN, FLOAT_PRECISION, ERROR_CONDITION, STATE_TRANSITION, EDGE_CASE_OTHER) — edge case override applies cross-file just as it does same-file.
- No other test files of the same language exist in the project.

---

## Section 2 — Test Type Definitions

The cross-file check is **test-type-aware**: only tests of the same type are compared. Overlap between a unit test and an integration test for the same scenario is intentional and must not be blocked.

Three test types are defined:

### `unit`

**What it validates**: The behavior of a single function, method, or class in isolation. External dependencies (databases, network, file system, other services) are replaced with mocks, stubs, or fakes. Unit tests verify that a unit of code produces the correct output for a given input under controlled conditions.

**Scope**: One function or class at a time. Assertions target return values, raised exceptions, or state changes within the unit under test.

**Speed expectation**: Fast (milliseconds per test). No I/O, no network, no process boundaries.

**Examples of unit test subjects**: `add(a, b)`, `parse_date(str)`, `UserValidator.validate(user)`, a single repository method with a mocked database.

### `integration`

**What it validates**: The interaction between two or more components, or between the application and an external system (real database, real HTTP service, real file system, message queue). Integration tests verify that independently correct units compose correctly when wired together.

**Scope**: Multiple layers, a subsystem, or an application-to-infrastructure boundary. Assertions may target database state, HTTP responses, file contents, or observable side effects across component boundaries.

**Speed expectation**: Slower than unit (seconds to tens of seconds per test). May require setup and teardown of real infrastructure (docker containers, test databases, test servers).

**Examples of integration test subjects**: `UserRepository.save(user)` against a real test database, an API endpoint that writes to a database and reads back, a service-to-service HTTP call with a real downstream.

### `e2e`

**What it validates**: End-to-end behavior of the entire system from the user's entry point (browser, CLI, API gateway) through all layers to the final output. E2E tests simulate real user workflows and verify that the full system works together correctly.

**Scope**: The entire application stack or a complete user journey. Assertions target the visible output of the system as a whole (UI state, final API responses, final database state after a full user flow).

**Speed expectation**: Slowest (seconds to minutes per test). Requires a fully deployed or fully configured environment.

**Examples of e2e test subjects**: "A user registers, logs in, submits an order, and sees a confirmation page" verified through a headless browser or API chain; a CLI command that triggers a full pipeline and produces a final artifact.

---

## Section 3 — Classification Heuristics

To determine the type of a test file, evaluate all three signal tiers independently — do not stop after the first match. After collecting results from all tiers, apply the precedence rule defined in Section 4 (Marker > Filename > Directory) to determine the final classification. If no signal matches in any tier, default to `unit`.

The same priority chain applies to **all 7 supported languages** (Python, JavaScript, TypeScript, Java, C#, Go, C++). Language-specific patterns appear only in the signal lookup tables below; the algorithm is language-agnostic.

### 3.1 — Directory Signals

Inspect the **full file path** for the following directory name segments. Match is case-insensitive. A match on any segment classifies the file; use the first match found when scanning the path from the root toward the filename.

| Directory segment | Classified type | Notes |
|---|---|---|
| `tests/unit/` | `unit` | Universal across all languages |
| `tests/integration/` | `integration` | Universal across all languages |
| `tests/e2e/` | `e2e` | Universal across all languages |
| `tests/acceptance/` | `e2e` | `acceptance` maps to `e2e` |
| `integration_tests/` | `integration` | Common in Python projects |
| `e2e/` | `e2e` | Standalone top-level `e2e/` directory |

**Language-specific directory patterns**:

| Language | Directory segment | Classified type |
|---|---|---|
| Java | `src/test/java/.../unit/` | `unit` |
| Java | `src/test/java/.../integration/` | `integration` |
| JavaScript / TypeScript | `__tests__/unit/` | `unit` |
| JavaScript / TypeScript | `__tests__/integration/` | `integration` |
| JavaScript / TypeScript | `__tests__/e2e/` | `e2e` |

**Matching rule**: A path segment match means the segment appears as a complete directory component in the path — not as a substring of a longer name. For example, `tests/unit/` matches the path `project/tests/unit/test_calc.py` but does not match `project/tests/units_data/test_calc.py`.

**Examples**:

```
project/tests/unit/test_calculator.py          → unit   (directory: tests/unit/)
project/tests/integration/test_api.py          → integration (directory: tests/integration/)
project/tests/e2e/test_checkout.py             → e2e    (directory: tests/e2e/)
project/tests/acceptance/test_login.py         → e2e    (directory: tests/acceptance/)
project/integration_tests/test_db.py           → integration (directory: integration_tests/)
project/e2e/test_user_flow.py                  → e2e    (directory: e2e/)
src/test/java/com/example/unit/CalcTest.java   → unit   (directory: .../unit/)
project/__tests__/unit/calculator.test.ts      → unit   (directory: __tests__/unit/)
project/__tests__/integration/api.test.ts      → integration (directory: __tests__/integration/)
```

### 3.2 — Filename Signals

Strip the file extension and inspect the **base filename** for the following substrings. Match is case-insensitive. Use the first match found.

| Filename substring | Classified type |
|---|---|
| `unit` | `unit` |
| `integration` | `integration` |
| `e2e` | `e2e` |
| `acceptance` | `e2e` |

**Matching rule**: The substring must appear anywhere in the base filename (after stripping the extension). It does not need to be a whole word. `test_unit_calculator.py` → `unit`. `test_integration_api.py` → `integration`. `auth_e2e_spec.ts` → `e2e`.

**Examples**:

```
tests/test_unit_calculator.py       → unit         (filename: *unit*)
tests/test_integration_api.py       → integration  (filename: *integration*)
tests/auth_e2e_spec.ts              → e2e          (filename: *e2e*)
tests/test_acceptance_login.py      → e2e          (filename: *acceptance*)
tests/CalculatorUnitTest.java       → unit         (filename: *unit*)
tests/OrderIntegrationTest.java     → integration  (filename: *integration*)
```

### 3.3 — Framework Marker Signals

Inspect the **file content** for framework-specific type markers. Read only the first 50 lines of the file — markers appear at the top of well-structured test files. Match is case-sensitive unless noted.

When a marker is found, it takes **final precedence** over both directory and filename signals (see Section 4 — Conflict Resolution). Even if the directory says `unit/`, a marker of `@pytest.mark.integration` overrides it.

#### Python

| Marker | Classified type |
|---|---|
| `@pytest.mark.unit` | `unit` |
| `@pytest.mark.integration` | `integration` |
| `@pytest.mark.e2e` | `e2e` |

**Where to find**: Decorator on individual test functions or on the module-level `pytestmark` variable.

```python
# Module-level marker — classifies the entire file
pytestmark = pytest.mark.integration

# Function-level marker — classifies this function; if mixed markers exist, use the most common or first found
@pytest.mark.unit
def test_add_positive():
    ...

@pytest.mark.integration
def test_user_creation_db():
    ...
```

**Scanning rule**: Check the first 50 lines. If both `@pytest.mark.unit` and `@pytest.mark.integration` appear (mixed-marker file), use the marker that appears first in the file.

#### Java

| Marker | Classified type |
|---|---|
| `@Tag("unit")` | `unit` |
| `@Tag("integration")` | `integration` |
| `@Tag("e2e")` | `e2e` |
| `@Category(UnitTest.class)` | `unit` |
| `@Category(IntegrationTest.class)` | `integration` |

**Where to find**: On test class declarations or individual test methods (JUnit 5 `@Tag`, JUnit 4 `@Category`).

```java
// JUnit 5 — class-level tag classifies the entire file
@Tag("integration")
class UserRepositoryTest {
    ...
}

// JUnit 4 — class-level category
@Category(IntegrationTest.class)
public class OrderServiceTest {
    ...
}
```

#### C#

| Marker | Classified type |
|---|---|
| `[Trait("Category", "Unit")]` | `unit` |
| `[Trait("Category", "Integration")]` | `integration` |
| `[Trait("Category", "E2E")]` | `e2e` |
| `[Category("Unit")]` | `unit` |
| `[Category("Integration")]` | `integration` |
| `[Category("E2E")]` | `e2e` |

**Where to find**: On test class or method declarations. The first three rows are xUnit `[Trait]` markers; the last three rows are NUnit `[Category]` markers. Both forms are recognized and produce the same classification.

```csharp
// xUnit — class-level trait
[Trait("Category", "Integration")]
public class UserRepositoryTests
{
    ...
}

// NUnit alternative
[Category("Integration")]
public class OrderTests
{
    ...
}
```

Note: NUnit `[Category("Integration")]` is treated equivalently to `[Trait("Category", "Integration")]` — both classify the file as `integration`.

#### JavaScript / TypeScript

| Marker pattern | Classified type |
|---|---|
| `describe("unit"` (case-insensitive start of describe block name) | `unit` |
| `describe("integration"` (case-insensitive) | `integration` |
| `describe("e2e"` (case-insensitive) | `e2e` |
| `describe("acceptance"` (case-insensitive) | `e2e` |

**Where to find**: Top-level `describe()` block name. Match when the block name begins with or equals the type keyword (case-insensitive).

```typescript
// Top-level describe name starts with "integration"
describe("integration: UserRepository", () => {
  ...
});

// Also matches
describe("Integration Tests - Auth", () => {
  ...
});
```

**Limitation**: JS/TS marker signals are weaker than Python/Java because `describe` block names are free-form strings. Apply this signal only when the top-level describe block name clearly starts with a type keyword. When uncertain, do not classify from this signal — fall through to the default.

#### Go

Go does not have a standard framework mechanism for tagging tests as unit, integration, or e2e. Two supplementary marker mechanisms exist, described below in order of precedence.

**Primary marker: build tags**

The most common Go convention is to use **build tags** at the top of the file (before the `package` declaration). Scan the first 5 lines for these patterns:

| Build tag | Classified type |
|---|---|
| `//go:build unit` (or `// +build unit`) | `unit` |
| `//go:build integration` (or `// +build integration`) | `integration` |
| `//go:build e2e` (or `// +build e2e`) | `e2e` |

When a build tag is present, use it as the Go marker signal.

**Secondary marker: `t.Skip(...)` (weak signal)**

`t.Skip(...)` patterns are inconsistently used across Go projects and should be treated as a weak, supplementary signal only. Use a `t.Skip(...)` call to classify a file only when no build tag is present and no other signal (directory or filename) is available, and only when the skip message clearly names the test type (e.g., `t.Skip("only run in integration environment")`).

| Marker pattern | Classified type |
|---|---|
| `t.Skip(...)` with message containing `unit` | `unit` (weak — use only as last resort) |
| `t.Skip(...)` with message containing `integration` | `integration` (weak — use only as last resort) |
| `t.Skip(...)` with message containing `e2e` | `e2e` (weak — use only as last resort) |

Go classification in practice relies primarily on directory and filename signals; the marker signal is supplementary.

#### C++

**C++ has no standard test type markers.** None of the major C++ test frameworks (Google Test, Catch2, Boost.Test) define a built-in mechanism for marking test files as unit, integration, or e2e.

**C++ classification relies exclusively on directory and filename signals.** Do not attempt to infer test type from C++ file content. If directory and filename signals both fail to classify a C++ test file, apply the default (`unit`).

---

## Section 4 — Conflict Resolution

When two or more signals from different tiers disagree on the classification of a file, apply the following precedence rule:

**Marker > Filename > Directory**

That is:
- A framework marker always wins over a filename signal.
- A framework marker always wins over a directory signal.
- A filename signal wins over a directory signal when no marker is present.

This precedence applies uniformly across all 7 languages.

### Rationale

Framework markers are explicit, developer-authored declarations of test type. When a developer writes `@pytest.mark.integration` on a test file placed in `tests/unit/`, they have made a deliberate choice. Markers are authoritative because they require active effort to add, whereas directory placement may be a mistake, a legacy artifact, or a deliberate project-level organization that does not reflect the true test type.

Filename signals are more intentional than directory placement (a developer named the file explicitly) but less intentional than in-code markers (markers require understanding the framework). Therefore, filename overrides directory but yields to marker.

### Conflict Examples

#### Example 1 — Marker vs. Directory (AT-6)

**File**: `tests/unit/test_api.py`
**Content includes**: `@pytest.mark.integration` (within first 50 lines)

**Signals**:
- Directory signal → `unit` (`tests/unit/`)
- Marker signal → `integration` (`@pytest.mark.integration`)

**Resolution**: Marker wins. **Classified as `integration`.**

**Consequence for cross-file blocking**: The write-agent will include this file in the `integration` bucket of the cross-file index, not the `unit` bucket. Cross-file comparison of proposed unit tests will not scan this file. Cross-file comparison of proposed integration tests will scan this file.

```
tests/unit/test_api.py
  Directory signal:   unit
  Marker signal:      integration   ← wins (marker > directory)
  Final type:         integration
```

#### Example 2 — Filename vs. Directory

**File**: `tests/common/test_integration_user_flow.py`
**Content**: No framework markers within first 50 lines.

**Signals**:
- Directory signal → no match (`tests/common/` does not match any known directory pattern)
- Filename signal → `integration` (`test_integration_user_flow` contains `integration`)
- Marker signal → no match

**Resolution**: Filename wins (only signal that matched). **Classified as `integration`.**

```
tests/common/test_integration_user_flow.py
  Directory signal:   no match
  Filename signal:    integration   ← wins (only signal present)
  Marker signal:      no match
  Final type:         integration
```

#### Example 3 — Filename vs. Directory (conflict)

**File**: `tests/unit/test_integration_legacy.py`
**Content**: No markers.

**Signals**:
- Directory signal → `unit` (`tests/unit/`)
- Filename signal → `integration` (`test_integration_legacy` contains `integration`)
- Marker signal → no match

**Resolution**: Filename wins over directory. **Classified as `integration`.**

```
tests/unit/test_integration_legacy.py
  Directory signal:   unit
  Filename signal:    integration   ← wins (filename > directory)
  Marker signal:      no match
  Final type:         integration
```

### Default — No Signal Matches (AT-5)

**When no directory, filename, or marker signal matches, classify the file as `unit`.**

This is the conservative default. `unit` is the most common test type by volume. Defaulting to `unit` means that when both a proposed test and an unclassified existing file default to `unit`, the cross-file comparison proceeds — which is the safe, blocking-preferred behavior. Defaulting to `integration` or leaving the type as `unknown` would silently allow potential duplication whenever both sides lack type signals.

```
tests/test_calculator.py
  Directory signal:   no match (tests/ alone is not a type signal)
  Filename signal:    no match (filename contains neither unit, integration, e2e, nor acceptance)
  Marker signal:      no match (no @pytest.mark.* in first 50 lines)
  Final type:         unit   (default)
```

**Consequence for AT-5**: If a proposed test targets a new file that also carries no type signals, it defaults to `unit`. If an existing test file in the project also carries no type signals, it also defaults to `unit`. The cross-file check will compare them as same-type (`unit` vs `unit`), and will block if equivalence classes match. This is the intended conservative behavior — preferring to block over silently allowing duplication.

### Classification Summary Table

| Directory signal | Filename signal | Marker signal | Final type |
|---|---|---|---|
| `unit` | — | — | `unit` |
| `integration` | — | — | `integration` |
| `unit` | `integration` | — | `integration` (filename > directory) |
| `integration` | `unit` | — | `unit` (filename > directory) |
| `unit` | — | `integration` | `integration` (marker > directory) |
| `integration` | — | `unit` | `unit` (marker > directory) |
| `unit` | `integration` | `unit` | `unit` (marker > filename > directory) |
| no match | no match | no match | `unit` (default) |
| no match | `integration` | — | `integration` (filename, only signal) |
| no match | no match | `e2e` | `e2e` (marker, only signal) |
| `e2e` | — | — | `e2e` (directory signal) |
| no match | `e2e` | — | `e2e` (filename signal) |
| `unit` | `e2e` | — | `e2e` (filename > directory) |

---

## Section 5 — Discovery Algorithm

Run this algorithm **once per source file**, at the START of Step 4, before the per-test loop begins. The result is stored in working memory and reused for every proposed test generated for that source file (REQ-F-18).

### 5.1 — Step 1: Glob All Test Files

Use the Glob tool to discover all test files in the project that match the language of the source file under test. Apply the patterns for the detected language from the table below. Root the glob at `project_root` (the project root directory identified in the write-agent's loaded context).

**Do NOT traverse outside `project_root`.** Do NOT glob for other languages (REQ-F-7, REQ-NF-5).

| Language | Glob patterns |
|---|---|
| Python | `**/*test*.py`, `**/*_test.py`, `**/test_*.py` |
| JavaScript | `**/*.test.js`, `**/*.spec.js`, `**/__tests__/**/*.js` |
| TypeScript | `**/*.test.ts`, `**/*.spec.ts`, `**/__tests__/**/*.ts` |
| Java | `**/*Test.java`, `**/*Tests.java`, `**/*Spec.java` |
| C# | `**/*Test.cs`, `**/*Tests.cs`, `**/*Spec.cs` |
| Go | `**/*_test.go` |
| C++ | `**/*_test.cpp`, `**/*_test.cc`, `**/*Test.cpp`, `**/*Spec.cpp` |

If Glob returns no results (empty project, permission failure, or pattern mismatch), skip the cross-file check entirely for this source file — allow all proposed tests without cross-file comparison. Log a warning in the generation summary: `[cross-file] Warning: no test files discovered; cross-file check skipped`.

### 5.2 — Step 2: Exclude the Target Test File

Remove the current target test file (the file the write-agent is writing to) from the Glob result by exact path comparison (REQ-F-6). The same-file check (Step A in the redundancy gate) already covers that file. Including it in the cross-file index would cause double-counting and produce spurious blocks against tests in an incomplete file.

```
discovered_paths = glob_result - { target_test_file_path }
```

### 5.3 — Step 3: Classify and Index Each File

For each path in `discovered_paths`:

1. Apply the Section 3 classification heuristics to determine the file's type (`unit`, `integration`, or `e2e`).
   - Evaluate all three signal tiers (Directory, Filename, Marker) independently.
   - Apply the Section 4 precedence rule (Marker > Filename > Directory) to determine the final type.
   - If no signal matches in any tier, classify as `unit` (default — see Section 4 and TD-6).
2. Append the file path to the appropriate bucket in the index.

Store the completed index in working memory as:

```
cross_file_index = {
  "unit":        ["path/to/tests/unit/test_a.py", ...],
  "integration": ["path/to/tests/integration/test_b.py", ...],
  "e2e":         ["path/to/tests/e2e/test_c.py", ...]
}
```

Also initialize an empty content cache in working memory:

```
content_cache = {}
```

The content cache is populated lazily during the per-test cross-file comparison (Section 6, Step 3). Nothing is written to disk — both `cross_file_index` and `content_cache` exist only in working memory for the duration of the current write-agent invocation.

---

## Section 6 — Cross-File Comparison Algorithm

Run this algorithm for each proposed test, **after** the same-file check (Step A) has passed. If the same-file check already blocked the proposed test, do not run this algorithm.

### 6.1 — Step 1: Determine the Proposed Test's Type

First, check whether the write-agent received a `test_type` input parameter from the orchestrator. If the parameter is present and non-empty, use it as the proposed test's type (it is authoritative).

If `test_type` is absent or empty, fall back to classifying the **target test file path** using the Section 3 heuristics (same three-tier process: Directory → Filename → Marker → default `unit`). If path and filename signals are inconclusive, also scan the first 50 lines of the target test file for framework markers (Section 3.3), exactly as the index-build phase does for discovered files. The result is the proposed test's type for this comparison.

```
if test_type input parameter is present and non-empty:
    proposed_type = test_type
else:
    proposed_type = classify(target_test_file_path)  # Section 3 + Section 4
```

### 6.2 — Step 2: Retrieve the Same-Type File List

Look up `proposed_type` in `cross_file_index` to obtain the list of candidate files for comparison.

```
candidate_files = cross_file_index[proposed_type]  # e.g., ["tests/unit/test_a.py", ...]
```

If `candidate_files` is empty, there are no same-type files to compare against. Allow the proposed test and proceed to code generation.

### 6.3 — Step 3: Extract Scenarios from Each Candidate File

For each file path in `candidate_files`:

1. **Check the content cache**: if `content_cache[file_path]` already exists, use the cached scenario list. Do not re-read the file.
2. **If not cached**: Use the Read tool to read the file's content. Then extract all test scenarios from the content using the **Classification Rules** section in `skills/redundancy-detection/SKILL.md` — specifically, the Language-Specific Heuristics subsections that describe how to identify test functions and extract function-under-test and equivalence classes from each. Store the extracted scenario list in `content_cache[file_path]` before proceeding.
   - If the file cannot be read (permission error, binary file, parse error): treat it as containing no scenarios (`content_cache[file_path] = []`), skip it, and allow the proposed test — do not block due to a read failure. Log a warning in the generation summary: `[cross-file] Warning: could not read <file_path>; treated as empty`. See Section 7.
3. **Compare against the proposed test**: apply the equivalence class comparison from the **Detection Algorithm** section in `skills/redundancy-detection/SKILL.md` — specifically Steps 2 and 3 (Analyze Proposed Test, Compare Against Existing Tests). Filter the extracted scenarios to those targeting the same function under test before comparing equivalence classes. Apply the normalization rules from SKILL.md (POSITIVE_SMALL / POSITIVE_LARGE → POSITIVE_SMALL; NEGATIVE_SMALL / NEGATIVE_LARGE → NEGATIVE_SMALL).
4. **If a match is found**: record `{ matched_test_name, matched_file_path: file_path, matched_file_type: proposed_type }` and proceed to Step 4 (edge case override).

### 6.4 — Step 4: Apply Edge Case Override

This step is identical to Step 4 of SKILL.md's Detection Algorithm (see the **Edge Case Override Logic** block in that section). Apply it here for cross-file matches exactly as it is applied for same-file matches.

**Edge case override (REQ-F-14, AT-4)**: If the proposed test has ANY of the following equivalence classes, ALLOW the test — do not block it, even if a same-type cross-file match was found:

- ZERO
- EMPTY_STRING
- EMPTY_COLLECTION
- NULL_UNDEFINED
- BOUNDARY_MAX
- BOUNDARY_MIN
- FLOAT_PRECISION
- ERROR_CONDITION
- STATE_TRANSITION
- EDGE_CASE_OTHER

**If no edge case class is present** and a same-type cross-file match was found: BLOCK the proposed test. Generate a blocking message using the Section 8 template, then add it to the `[cross-file]` blocked tests list in the generation summary.

**If no match was found across all candidate files**: ALLOW the proposed test and proceed to code generation.

---

## Section 7 — Error Handling

All errors during cross-file detection are **non-blocking**. The conservative threshold principle from SKILL.md ("when in doubt, allow the test") applies here. When any error occurs, allow the proposed test rather than blocking it on uncertain grounds. The write-agent logs each error as a warning in the generation summary — they do not cause the overall generation to fail.

### 7.1 — Glob Failure

**Condition**: The Glob tool returns an error, or the result set is empty after excluding the target test file (either the project has no matching test files, or all discovered files were the target file itself).

**Action**: Skip the cross-file check entirely for this source file. Allow all proposed tests without cross-file comparison. Continue the write-agent workflow normally.

**Log**: Add to the generation summary: `[cross-file] Warning: no test files discovered; cross-file check skipped`.

### 7.2 — File Read Failure

**Condition**: The Read tool fails for a specific file in `candidate_files`. Failure modes include: permission error, binary file content, file deleted between Glob and Read, or content that cannot be parsed as source code.

**Action**: Treat the file as containing no test scenarios (`content_cache[file_path] = []`). Skip the file. Allow the proposed test (do not block because of an unreadable file). Continue comparing against any remaining candidate files (REQ-F-21).

**Log**: Add to the generation summary: `[cross-file] Warning: could not read <file_path>; treated as empty`.

### 7.3 — Classification Failure

**Condition**: Section 3 heuristics return no match for a discovered file — no directory, filename, or marker signal fires, and the three-tier evaluation produces no result.

**Action**: Default to `unit` (same as the Section 4 default). Classify the file as `unit` and place it in the `cross_file_index["unit"]` bucket. This is the conservative behavior: if both the proposed test and the unclassified file default to `unit`, the cross-file comparison proceeds, which is the blocking-preferred direction (TD-6).

**Log**: No warning needed for classification defaulting — this is expected behavior for projects without explicit type signals.

### 7.4 — Performance Budget Exceeded

**Condition**: The number of same-type candidate files for the proposed test's type exceeds 30 files, or cumulative Read operations during Step 3 of Section 6 appear to be exhausting the available time budget (REQ-NF-1: < 30 seconds per source file).

**Action**: Scan only the first 30 same-type candidate files. Allow all proposed tests for which no match was found in those 30 files — do not block based on unscanned files. This caps the worst-case per-source-file scan at a bounded set while preserving correctness for the most relevant files (earlier-returned Glob results tend to be the most structurally similar files).

**Log**: Add to the generation summary: `[cross-file] Warning: candidate file count exceeded threshold (>30 same-type files); cross-file check limited to first 30 files`.

---

## Section 8 — Cross-File Message Template

Use this template when blocking a proposed test due to a cross-file redundancy match. This template is distinct from SKILL.md's same-file template: it includes the path and type of the matched file so the developer knows exactly where the existing coverage lives.

### 8.1 — Template

```
[cross-file] Test Generation Blocked: Cross-File Redundant Test Scenario

Proposed test '{proposed_test_name}' is redundant with an existing test in another file of the same type.

Matched test:  '{matched_test_name}'
In file:        {matched_file_path}
File type:      {matched_file_type}

Both tests exercise the same function with the same equivalence classes. The matched file already provides this coverage.

Suggestion: {actionable_suggestion}
```

### 8.2 — Field Definitions

| Field | Description |
|---|---|
| `{proposed_test_name}` | The name of the proposed test being blocked (e.g., `test_add_large_numbers`) |
| `{matched_test_name}` | The name of the existing test in the other file that matches the proposed test's equivalence classes (e.g., `test_add_positive_numbers`) |
| `{matched_file_path}` | The relative path from `project_root` to the file containing the matched test (e.g., `tests/unit/test_calculator.py`) |
| `{matched_file_type}` | The classified type of the matched file (`unit`, `integration`, or `e2e`) — determined by the Section 3/4 classification at index-build time |
| `{actionable_suggestion}` | A concrete suggestion for what to do instead of generating the redundant test |

All five fields are required. Do not omit any field. The `{matched_file_type}` field is especially important: it makes clear to the developer why the match was treated as same-type (and therefore blocking), distinguishing this from a cross-type overlap that would have been allowed.

### 8.3 — Actionable Suggestion Guidelines

Populate `{actionable_suggestion}` with one of the following, chosen to fit the context:

- If the function has untested edge cases: `Add a test for [specific edge case, e.g., divide(10, 0)] — ERROR_CONDITION scenarios are always allowed even when a same-type match exists.`
- If the function is fully covered: `Remove '{proposed_test_name}' — the scenario is already covered by '{matched_test_name}' in {matched_file_path}.`
- If the test belongs in a different type tier: `If this test exercises real infrastructure (e.g., a real database), move it to the integration tier — cross-type overlap is intentional and will not be blocked.`

### 8.4 — Example

**Scenario**: Write-agent proposes `test_add_big_numbers` (a unit test calling `add(500, 200)`) for a new file `tests/unit/test_math_extended.py`. The cross-file index already contains `tests/unit/test_calculator.py`, which has `test_add_positive_numbers` calling `add(2, 3)`. Both normalize to POSITIVE_SMALL + POSITIVE_SMALL for the `add` function. No edge case class is present.

**Generated blocking message**:

```
[cross-file] Test Generation Blocked: Cross-File Redundant Test Scenario

Proposed test 'test_add_big_numbers' is redundant with an existing test in another file of the same type.

Matched test:  'test_add_positive_numbers'
In file:        tests/unit/test_calculator.py
File type:      unit

Both tests exercise the same function with the same equivalence classes. The matched file already provides this coverage.

Suggestion: Remove 'test_add_big_numbers' — the scenario is already covered by 'test_add_positive_numbers' in tests/unit/test_calculator.py. If you need to test overflow behavior (add(MAX_INT, 1)), that is an ERROR_CONDITION edge case and will be allowed.
```
