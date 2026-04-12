# Kotlin Framework Detection

**Version**: 1.0.0
**Language**: Kotlin
**Build Systems**: Maven, Gradle (Groovy DSL), Gradle (Kotlin DSL)
**Frameworks**: JUnit 5 (Jupiter) + MockK
**Status**: Phase 4 - Implementation

## Overview

Kotlin framework detection skill that identifies testing frameworks and build systems for Kotlin projects. Kotlin is a JVM language that shares Maven/Gradle infrastructure with Java but uses MockK for mocking and idiomatic Kotlin test syntax.

## Scope

This skill covers **JUnit 5 + MockK only**. Kotest is explicitly excluded — it requires separate verification effort. If Kotest is detected, fall back to JUnit 5 patterns and note the detection in evidence.

## Critical Distinction: Build System Required

**Kotlin projects MUST have a build system to run tests.** This skill detects both:
1. **Build System** (Maven or Gradle) - Required
2. **Testing Framework** (JUnit 5) - Default fallback
3. **Mocking Library** (MockK or Mockito) - MockK preferred for Kotlin

## Kotlin vs Java Detection

When both `.kt` and `.java` files are present, treat as a mixed Kotlin/Java project. If `.kt` files are the primary source (>50% of source files), treat as a Kotlin project and use Kotlin patterns.

Additional Kotlin signals beyond standard Java/Gradle markers:
- `build.gradle.kts` (Kotlin DSL build file)
- `settings.gradle.kts`
- Source files with `.kt` or `.kts` extension
- `kotlin` plugin in build files: `id("org.jetbrains.kotlin.jvm")`
- `io.mockk:mockk` dependency

## Supported Build Systems

### 1. Maven

**Description**: Apache Maven build automation tool
**Detection Files**: `pom.xml`
**Test Command**: `mvn test`
**Test Reports**: `target/surefire-reports/`

**Kotlin-specific pom.xml signals**:
- `kotlin-maven-plugin`
- `org.jetbrains.kotlin` groupId in dependencies

### 2. Gradle (Groovy DSL)

**Description**: Build automation tool with Groovy DSL
**Detection Files**: `build.gradle`
**Test Command**: `./gradlew test` or `gradle test`
**Test Reports**: `build/test-results/test/`

### 3. Gradle (Kotlin DSL) — Idiomatic for Kotlin

**Description**: Build automation tool with Kotlin DSL (idiomatic for Kotlin projects)
**Detection Files**: `build.gradle.kts`
**Test Command**: `./gradlew test` or `gradle test`
**Test Reports**: `build/test-results/test/`

**Additional signal**: Presence of `build.gradle.kts` is a strong Kotlin indicator.

## Supported Testing Frameworks

### JUnit 5 (Jupiter) — Default and Only Supported

**Description**: Fifth generation JUnit testing framework
**Official Docs**: https://junit.org/junit5/
**Detection Priority**: High (modern standard, default fallback)

**Key Dependencies**:
- `org.junit.jupiter:junit-jupiter-api`
- `org.junit.jupiter:junit-jupiter-engine`

**Kotlin Imports**:
- `import org.junit.jupiter.api.Test`
- `import org.junit.jupiter.api.Assertions.*`
- `import org.junit.jupiter.api.assertThrows`

## Supported Mocking Libraries

### MockK — Preferred for Kotlin

**Description**: Mocking library written in Kotlin, idiomatic for Kotlin codebases
**Official Docs**: https://mockk.io/
**Detection**: `io.mockk:mockk` in dependencies

**Key Patterns**:
- `mockk<MyClass>()`
- `every { mock.method() } returns value`
- `verify { mock.method() }`
- `coEvery` / `coVerify` for suspend functions

### Mockito — Fallback

If MockK is not found but Mockito is present (`org.mockito`), use Mockito patterns. Note in evidence that Mockito (not MockK) was detected for a Kotlin project.

## Detection Strategy

### Phase 1: Language Detection

Detect `.kt` or `.kts` files before running the standard build system check.

```python
def detect_kotlin_signals(project_path):
    signals = []
    confidence_boost = 0.0

    # Strong signals
    if glob(join(project_path, "**/*.kt"), recursive=True):
        signals.append("Kotlin source files (.kt) found")
        confidence_boost += 0.3

    if exists(join(project_path, "build.gradle.kts")):
        signals.append("build.gradle.kts (Kotlin DSL) found")
        confidence_boost += 0.2

    if exists(join(project_path, "settings.gradle.kts")):
        signals.append("settings.gradle.kts found")
        confidence_boost += 0.1

    return signals, confidence_boost
```

### Phase 2: Build System Detection

Same logic as Java build system detection. Detect Maven or Gradle.

```python
def detect_build_system(project_path):
    build_system = None
    evidence = []

    if exists(join(project_path, "pom.xml")):
        build_system = "maven"
        evidence.append("pom.xml found")

    gradle_files = ["build.gradle.kts", "build.gradle"]
    for gradle_file in gradle_files:
        if exists(join(project_path, gradle_file)):
            build_system = "gradle"
            evidence.append(f"{gradle_file} found")
            if exists(join(project_path, "gradlew")):
                evidence.append("Gradle Wrapper detected")
            break

    return {"build_system": build_system, "evidence": evidence}
```

### Phase 3: Framework and Mocking Detection

Parse dependencies to detect JUnit 5 and MockK.

## Maven Detection Patterns

### Maven: pom.xml with Kotlin

```xml
<project>
  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter-api</artifactId>
      <version>5.10.0</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>io.mockk</groupId>
      <artifactId>mockk</artifactId>
      <version>1.13.8</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.jetbrains.kotlin</groupId>
        <artifactId>kotlin-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
```

### Maven: Parse Dependencies

```python
def parse_maven_kotlin_dependencies(pom_path):
    frameworks = {"junit5": 0}
    mocking = {"mockk": 0, "mockito": 0}
    evidence = []

    try:
        content = read_file(pom_path)

        if "org.junit.jupiter" in content:
            frameworks["junit5"] += 15
            evidence.append("Maven dependency: org.junit.jupiter")

        if "io.mockk" in content:
            mocking["mockk"] += 15
            evidence.append("Maven dependency: io.mockk (MockK detected)")

        if "org.mockito" in content:
            mocking["mockito"] += 10
            evidence.append("Maven dependency: org.mockito")

        if "kotlin-maven-plugin" in content or "org.jetbrains.kotlin" in content:
            evidence.append("Kotlin Maven plugin detected")

    except Exception as e:
        evidence.append(f"Error parsing pom.xml: {e}")

    return frameworks, mocking, evidence
```

## Gradle Detection Patterns

### Gradle: build.gradle.kts (Kotlin DSL)

```kotlin
plugins {
    kotlin("jvm") version "1.9.0"
}

dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.10.0")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.10.0")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
}

tasks.test {
    useJUnitPlatform()
}
```

### Gradle: Parse Dependencies

```python
def parse_gradle_kotlin_dependencies(build_file_path):
    frameworks = {"junit5": 0}
    mocking = {"mockk": 0, "mockito": 0}
    evidence = []

    try:
        content = read_file(build_file_path)

        # JUnit 5
        if re.search(r"org\.junit\.jupiter|junit-jupiter", content):
            frameworks["junit5"] += 10
            evidence.append("Gradle: JUnit 5 dependency found")

        if re.search(r"useJUnitPlatform\(\)", content):
            frameworks["junit5"] += 5
            evidence.append("Gradle: useJUnitPlatform() found")

        # MockK
        if re.search(r"io\.mockk|mockk", content):
            mocking["mockk"] += 15
            evidence.append("Gradle: MockK dependency found")

        # Mockito (fallback)
        if re.search(r"org\.mockito|mockito", content):
            mocking["mockito"] += 10
            evidence.append("Gradle: Mockito dependency found")

        # Kotlin plugin
        if re.search(r'kotlin\("jvm"\)|kotlin-jvm|id.*kotlin', content):
            evidence.append("Kotlin Gradle plugin detected")

        # Coroutines test
        if re.search(r"kotlinx-coroutines-test", content):
            evidence.append("Coroutines test library found (coroutine testing enabled)")

    except Exception as e:
        evidence.append(f"Error parsing Gradle file: {e}")

    return frameworks, mocking, evidence
```

## Source Code Pattern Detection

Scan `.kt` test files in `src/test/kotlin/` for framework imports.

```python
def detect_kotlin_test_files(project_path):
    frameworks = {"junit5": 0}
    mocking = {"mockk": 0, "mockito": 0}
    evidence = []

    test_paths = [
        "src/test/kotlin/**/*.kt",
        "src/test/**/*.kt"
    ]

    test_files = []
    for pattern in test_paths:
        test_files.extend(glob(join(project_path, pattern), recursive=True))

    for test_file in test_files[:10]:
        try:
            content = read_file(test_file)

            if re.search(r"import org\.junit\.jupiter", content):
                frameworks["junit5"] += 3
                evidence.append(f"JUnit 5 import in {test_file}")

            if re.search(r"import io\.mockk", content):
                mocking["mockk"] += 3
                evidence.append(f"MockK import in {test_file}")

        except Exception:
            continue

    return frameworks, mocking, evidence
```

## Complete Detection Function

```python
def detect_kotlin_framework(project_path):
    # Phase 1: Kotlin language signals
    kotlin_signals, _ = detect_kotlin_signals(project_path)

    if not kotlin_signals:
        return {
            "success": False,
            "error": "No Kotlin source files detected",
            "language": None,
            "framework": None
        }

    # Phase 2: Build system
    build_result = detect_build_system(project_path)
    if build_result["build_system"] is None:
        return {
            "success": False,
            "error": "No build system detected (need pom.xml or build.gradle)",
            "language": "kotlin",
            "framework": None
        }

    build_system = build_result["build_system"]
    all_evidence = kotlin_signals + build_result["evidence"]

    # Phase 3: Framework and mocking detection
    frameworks_score = {"junit5": 0}
    mocking_score = {"mockk": 0, "mockito": 0}

    if build_system == "maven":
        fw, mk, ev = parse_maven_kotlin_dependencies(join(project_path, "pom.xml"))
    else:
        build_files = ["build.gradle.kts", "build.gradle"]
        fw, mk, ev = {}, {}, []
        for bf in build_files:
            if exists(join(project_path, bf)):
                fw, mk, ev = parse_gradle_kotlin_dependencies(join(project_path, bf))
                break

    for k, v in fw.items():
        frameworks_score[k] = frameworks_score.get(k, 0) + v
    for k, v in mk.items():
        mocking_score[k] = mocking_score.get(k, 0) + v
    all_evidence.extend(ev)

    # Source code patterns
    fw2, mk2, ev2 = detect_kotlin_test_files(project_path)
    for k, v in fw2.items():
        frameworks_score[k] = frameworks_score.get(k, 0) + v
    for k, v in mk2.items():
        mocking_score[k] = mocking_score.get(k, 0) + v
    all_evidence.extend(ev2)

    # Select framework (default: junit5)
    framework = max(frameworks_score, key=frameworks_score.get) if any(frameworks_score.values()) else "junit5"
    mocking_lib = "mockk" if mocking_score.get("mockk", 0) >= mocking_score.get("mockito", 0) else "mockito"

    # Test command
    if build_system == "maven":
        test_cmd = {"command": "mvn test", "test_reports_dir": "target/surefire-reports", "wrapper": None}
    else:
        has_wrapper = exists(join(project_path, "gradlew"))
        prefix = "./gradlew" if has_wrapper else "gradle"
        test_cmd = {
            "command": f"{prefix} test",
            "test_reports_dir": "build/test-results/test",
            "wrapper": "./gradlew" if has_wrapper else None
        }

    return {
        "success": True,
        "language": "kotlin",
        "build_system": build_system,
        "framework": framework,
        "mocking_library": mocking_lib,
        "test_sources_dir": "src/test/kotlin",
        "confidence": min(sum(frameworks_score.values()) / 20.0, 1.0) if any(frameworks_score.values()) else 0.1,
        "evidence": all_evidence,
        "test_command": test_cmd["command"],
        "test_reports_dir": test_cmd["test_reports_dir"],
        "wrapper": test_cmd.get("wrapper")
    }
```

## Examples

### Example 1: Gradle Kotlin DSL + JUnit 5 + MockK

**Project Structure**:
```
my-app/
├── build.gradle.kts
├── settings.gradle.kts
├── gradlew
├── src/
│   ├── main/kotlin/com/example/
│   │   └── Calculator.kt
│   └── test/kotlin/com/example/
│       └── CalculatorTest.kt
```

**Detection Result**:
```json
{
  "success": true,
  "language": "kotlin",
  "build_system": "gradle",
  "framework": "junit5",
  "mocking_library": "mockk",
  "test_sources_dir": "src/test/kotlin",
  "confidence": 0.95,
  "test_command": "./gradlew test",
  "test_reports_dir": "build/test-results/test",
  "wrapper": "./gradlew"
}
```

### Example 2: Maven + JUnit 5 + MockK

**Detection Result**:
```json
{
  "success": true,
  "language": "kotlin",
  "build_system": "maven",
  "framework": "junit5",
  "mocking_library": "mockk",
  "test_sources_dir": "src/test/kotlin",
  "confidence": 0.9,
  "test_command": "mvn test",
  "test_reports_dir": "target/surefire-reports",
  "wrapper": null
}
```

## Edge Cases

### No MockK Found, Mockito Present

Kotlin can use Mockito via mockito-kotlin wrapper (`com.nhaarman.mockitokotlin2` or `org.mockito.kotlin`). Use Mockito patterns but note that MockK would be more idiomatic. Evidence should include: "Using Mockito (MockK not found) - consider migrating to MockK for idiomatic Kotlin testing".

### Coroutine Testing

If `kotlinx-coroutines-test` is detected in dependencies, note it in evidence. This enables `runTest {}` patterns in generated tests.

### No Framework Detected (Build System Only)

Default to JUnit 5 (modern standard). Confidence: 0.1.

## Test Execution Commands

| Build System | Command | Reports Location |
|---|---|---|
| Maven | `mvn test` | `target/surefire-reports/` |
| Gradle (wrapper) | `./gradlew test` | `build/test-results/test/` |
| Gradle (no wrapper) | `gradle test` | `build/test-results/test/` |

Kotlin + JUnit 5 produces standard JUnit XML reports — the same `junit-parser.md` used for Java applies unchanged.

## References

- Kotlin Documentation: https://kotlinlang.org/docs/home.html
- MockK Documentation: https://mockk.io/
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- kotlinx-coroutines-test: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/

---

**Last Updated**: 2026-02-23
**Phase**: 4 - Implementation
**Status**: Complete
