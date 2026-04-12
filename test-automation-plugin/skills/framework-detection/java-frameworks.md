# Java Framework Detection

**Version**: 1.0.0
**Language**: Java
**Build Systems**: Maven, Gradle
**Frameworks**: JUnit 4, JUnit 5 (Jupiter), TestNG
**Status**: Phase 3 - Implementation

## Overview

Java framework detection skill that identifies testing frameworks and build systems for Java projects. Unlike JavaScript/TypeScript, Java requires explicit build system detection (Maven or Gradle) because tests cannot run without the build system.

## Critical Distinction: Build System Required

**Java projects MUST have a build system to run tests.** This skill detects both:
1. **Build System** (Maven or Gradle) - Required
2. **Testing Framework** (JUnit 4, JUnit 5, TestNG) - Multiple can coexist

## Supported Build Systems

### 1. Maven

**Description**: Apache Maven build automation and project management tool
**Official Docs**: https://maven.apache.org/
**Detection Files**: `pom.xml`
**Test Command**: `mvn test`
**Test Reports**: `target/surefire-reports/`

**Key Characteristics**:
- XML-based configuration (pom.xml)
- Declarative dependency management
- Standard directory structure (src/test/java)
- Maven Surefire plugin for tests

### 2. Gradle

**Description**: Build automation tool with Groovy/Kotlin DSL
**Official Docs**: https://gradle.org/
**Detection Files**: `build.gradle`, `build.gradle.kts`
**Test Command**: `./gradlew test` or `gradle test`
**Test Reports**: `build/test-results/test/`

**Key Characteristics**:
- Groovy or Kotlin DSL configuration
- Flexible and programmable
- Gradle Wrapper (gradlew) for reproducible builds
- Incremental builds

## Supported Testing Frameworks

### 1. JUnit 5 (Jupiter)

**Description**: Fifth generation of JUnit testing framework
**Official Docs**: https://junit.org/junit5/
**Minimum Version**: 5.0.0+
**Detection Priority**: High (modern standard)

**Key Dependencies**:
- `org.junit.jupiter:junit-jupiter-api`
- `org.junit.jupiter:junit-jupiter-engine`

**Imports**:
- `import org.junit.jupiter.api.Test;`
- `import org.junit.jupiter.api.Assertions.*;`

### 2. JUnit 4

**Description**: Fourth generation of JUnit (legacy)
**Official Docs**: https://junit.org/junit4/
**Minimum Version**: 4.12+
**Detection Priority**: Medium (legacy, but still common)

**Key Dependencies**:
- `junit:junit:4.x`

**Imports**:
- `import org.junit.Test;`
- `import org.junit.Assert.*;`

### 3. TestNG

**Description**: Testing framework inspired by JUnit with additional features
**Official Docs**: https://testng.org/
**Minimum Version**: 6.0.0+
**Detection Priority**: Medium (enterprise usage)

**Key Dependencies**:
- `org.testng:testng`

**Imports**:
- `import org.testng.annotations.Test;`
- `import org.testng.Assert.*;`

## Detection Strategy

### Phase 1: Build System Detection (Required)

Detect Maven or Gradle first, as this determines how to parse dependencies.

```python
def detect_build_system(project_path):
    build_system = None
    confidence = 0.0
    evidence = []

    # Check for Maven
    if exists(join(project_path, "pom.xml")):
        build_system = "maven"
        confidence = 1.0
        evidence.append("pom.xml found")

    # Check for Gradle
    gradle_files = ["build.gradle", "build.gradle.kts"]
    for gradle_file in gradle_files:
        if exists(join(project_path, gradle_file)):
            build_system = "gradle"
            confidence = 1.0
            evidence.append(f"{gradle_file} found")

            # Check for Gradle Wrapper (preferred)
            if exists(join(project_path, "gradlew")) or \
               exists(join(project_path, "gradlew.bat")):
                evidence.append("Gradle Wrapper detected")

            break

    # Check for settings.gradle (additional confirmation for Gradle)
    if build_system == "gradle":
        if exists(join(project_path, "settings.gradle")) or \
           exists(join(project_path, "settings.gradle.kts")):
            evidence.append("settings.gradle found")

    return {
        "build_system": build_system,
        "confidence": confidence,
        "evidence": evidence
    }
```

### Phase 2: Framework Detection

Once build system is known, parse dependencies to detect frameworks.

## Maven Detection Patterns

### Maven: pom.xml Structure

```xml
<project>
  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter-api</artifactId>
      <version>5.10.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
```

### Maven: Parse Dependencies (Weight: 15)

```python
def parse_maven_dependencies(pom_path):
    import xml.etree.ElementTree as ET

    frameworks = {
        "junit5": 0,
        "junit4": 0,
        "testng": 0
    }
    evidence = []

    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()

        # Handle XML namespace
        namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        dependencies = root.findall('.//maven:dependency', namespace)

        # If namespace fails, try without namespace
        if not dependencies:
            dependencies = root.findall('.//dependency')

        for dep in dependencies:
            group_id = dep.find('groupId') or dep.find('{*}groupId')
            artifact_id = dep.find('artifactId') or dep.find('{*}artifactId')

            if group_id is None or artifact_id is None:
                continue

            group = group_id.text
            artifact = artifact_id.text

            # JUnit 5 detection
            if group == "org.junit.jupiter":
                frameworks["junit5"] += 15
                evidence.append(f"Maven dependency: {group}:{artifact}")

            # JUnit 4 detection
            elif group == "junit" and artifact == "junit":
                frameworks["junit4"] += 15
                evidence.append(f"Maven dependency: junit:junit")

            # TestNG detection
            elif group == "org.testng" and artifact == "testng":
                frameworks["testng"] += 15
                evidence.append(f"Maven dependency: org.testng:testng")

    except Exception as e:
        evidence.append(f"Error parsing pom.xml: {e}")

    return frameworks, evidence
```

### Maven: Test Execution Command

```python
def get_maven_test_command(project_path):
    return {
        "command": "mvn test",
        "wrapper": None,  # Maven doesn't have standard wrapper
        "test_reports_dir": "target/surefire-reports",
        "build_dir": "target"
    }
```

## Gradle Detection Patterns

### Gradle: build.gradle (Groovy DSL)

```groovy
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.10.0'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.10.0'

    // Or JUnit 4
    testImplementation 'junit:junit:4.13.2'

    // Or TestNG
    testImplementation 'org.testng:testng:7.8.0'
}

test {
    useJUnitPlatform()  // For JUnit 5
    // useTestNG()      // For TestNG
}
```

### Gradle: build.gradle.kts (Kotlin DSL)

```kotlin
dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.10.0")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.10.0")
}

tasks.test {
    useJUnitPlatform()
}
```

### Gradle: Parse Dependencies (Weight: 15)

```python
def parse_gradle_dependencies(build_file_path):
    frameworks = {
        "junit5": 0,
        "junit4": 0,
        "testng": 0
    }
    evidence = []

    try:
        content = read_file(build_file_path)

        # JUnit 5 detection patterns
        junit5_patterns = [
            r"org\.junit\.jupiter",
            r"junit-jupiter-api",
            r"junit-jupiter-engine",
            r"useJUnitPlatform\(\)"
        ]

        for pattern in junit5_patterns:
            if re.search(pattern, content):
                frameworks["junit5"] += 10
                evidence.append(f"Gradle pattern: {pattern}")
                break  # Count once per pattern type

        # JUnit 4 detection patterns
        junit4_patterns = [
            r"junit:junit:",
            r"'junit:junit:",
            r'"junit:junit:'
        ]

        for pattern in junit4_patterns:
            if re.search(pattern, content):
                frameworks["junit4"] += 15
                evidence.append("Gradle dependency: junit:junit")
                break

        # TestNG detection patterns
        testng_patterns = [
            r"org\.testng:testng",
            r"'org.testng:testng",
            r'"org.testng:testng',
            r"useTestNG\(\)"
        ]

        for pattern in testng_patterns:
            if re.search(pattern, content):
                frameworks["testng"] += 15
                evidence.append("Gradle dependency or config: org.testng:testng")
                break

        # Check test configuration block
        if re.search(r"test\s*\{", content):
            evidence.append("Gradle test configuration block found")

    except Exception as e:
        evidence.append(f"Error parsing Gradle file: {e}")

    return frameworks, evidence
```

### Gradle: Wrapper Detection

```python
def detect_gradle_wrapper(project_path):
    has_wrapper = False
    wrapper_script = None

    # Unix/Linux/Mac wrapper
    if exists(join(project_path, "gradlew")):
        has_wrapper = True
        wrapper_script = "./gradlew"

    # Windows wrapper
    elif exists(join(project_path, "gradlew.bat")):
        has_wrapper = True
        wrapper_script = "gradlew.bat"

    return has_wrapper, wrapper_script
```

### Gradle: Test Execution Command

```python
def get_gradle_test_command(project_path):
    has_wrapper, wrapper_script = detect_gradle_wrapper(project_path)

    if has_wrapper:
        command = f"{wrapper_script} test"
        use_wrapper = True
    else:
        command = "gradle test"
        use_wrapper = False

    return {
        "command": command,
        "wrapper": wrapper_script if use_wrapper else None,
        "test_reports_dir": "build/test-results/test",
        "test_reports_xml": "build/test-results/test/*.xml",
        "build_dir": "build",
        "use_wrapper_recommended": has_wrapper
    }
```

## Source Code Pattern Detection

### Java Test File Patterns (Weight: 3)

```python
def detect_java_test_files(project_path):
    frameworks = {
        "junit5": 0,
        "junit4": 0,
        "testng": 0
    }
    evidence = []

    # Look for test files in standard locations
    test_paths = [
        "src/test/java/**/*.java",
        "src/test/**/*.java",
        "test/**/*.java"
    ]

    test_files = []
    for pattern in test_paths:
        test_files.extend(glob(join(project_path, pattern)))

    if not test_files:
        return frameworks, evidence

    # Sample up to 10 test files
    sample_files = test_files[:10]

    for test_file in sample_files:
        try:
            content = read_file(test_file)

            # JUnit 5 imports
            if re.search(r"import org\.junit\.jupiter", content):
                frameworks["junit5"] += 3
                evidence.append(f"JUnit 5 import in {test_file}")
                break  # Count once

            # JUnit 4 imports
            elif re.search(r"import org\.junit\.Test", content):
                frameworks["junit4"] += 3
                evidence.append(f"JUnit 4 import in {test_file}")
                break

            # TestNG imports
            elif re.search(r"import org\.testng", content):
                frameworks["testng"] += 3
                evidence.append(f"TestNG import in {test_file}")
                break

        except Exception:
            continue

    return frameworks, evidence
```

## Complete Detection Function

```python
def detect_java_framework(project_path):
    # Phase 1: Detect build system (required)
    build_result = detect_build_system(project_path)

    if build_result["build_system"] is None:
        return {
            "success": False,
            "error": "No Java build system detected (need pom.xml or build.gradle)",
            "build_system": None,
            "framework": None
        }

    build_system = build_result["build_system"]
    all_evidence = build_result["evidence"].copy()

    # Phase 2: Detect testing framework based on build system
    frameworks_score = {
        "junit5": 0,
        "junit4": 0,
        "testng": 0
    }

    if build_system == "maven":
        pom_path = join(project_path, "pom.xml")
        scores, evidence = parse_maven_dependencies(pom_path)
        for fw, score in scores.items():
            frameworks_score[fw] += score
        all_evidence.extend(evidence)

    elif build_system == "gradle":
        # Try both Groovy and Kotlin DSL
        build_files = [
            join(project_path, "build.gradle"),
            join(project_path, "build.gradle.kts")
        ]

        for build_file in build_files:
            if exists(build_file):
                scores, evidence = parse_gradle_dependencies(build_file)
                for fw, score in scores.items():
                    frameworks_score[fw] += score
                all_evidence.extend(evidence)
                break

    # Phase 3: Check source code patterns
    code_scores, code_evidence = detect_java_test_files(project_path)
    for fw, score in code_scores.items():
        frameworks_score[fw] += score
    all_evidence.extend(code_evidence)

    # Select primary framework
    result = select_primary_framework(frameworks_score)

    # Get test command
    if build_system == "maven":
        test_cmd = get_maven_test_command(project_path)
    else:
        test_cmd = get_gradle_test_command(project_path)

    return {
        "success": True,
        "build_system": build_system,
        "framework": result["framework"],
        "confidence": result["confidence"],
        "evidence": all_evidence,
        "test_command": test_cmd["command"],
        "test_reports_dir": test_cmd["test_reports_dir"],
        "build_dir": test_cmd["build_dir"],
        "wrapper": test_cmd.get("wrapper")
    }


def select_primary_framework(scores):
    total = sum(scores.values())

    if total == 0:
        # Default to JUnit 5 (modern standard)
        return {
            "framework": "junit5",
            "confidence": 0.1,
            "reason": "Fallback default (JUnit 5 is modern standard)"
        }

    # Find highest scoring framework
    primary = max(scores, key=scores.get)
    confidence = min(scores[primary] / 30, 1.0)

    return {
        "framework": primary,
        "confidence": confidence,
        "reason": f"{primary} has highest score: {scores[primary]}"
    }
```

## Examples

### Example 1: Maven + JUnit 5 Project

**Project Structure**:
```
my-app/
├── pom.xml
├── src/
│   ├── main/java/
│   └── test/java/
│       └── com/example/CalculatorTest.java
```

**pom.xml**:
```xml
<dependencies>
  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter-api</artifactId>
    <version>5.10.0</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "maven",
  "framework": "junit5",
  "confidence": 0.93,
  "evidence": [
    "pom.xml found",
    "Maven dependency: org.junit.jupiter:junit-jupiter-api",
    "JUnit 5 import in src/test/java/com/example/CalculatorTest.java"
  ],
  "test_command": "mvn test",
  "test_reports_dir": "target/surefire-reports",
  "build_dir": "target",
  "wrapper": null
}
```

### Example 2: Gradle + JUnit 4 Project

**Project Structure**:
```
my-app/
├── build.gradle
├── gradlew
├── gradlew.bat
├── src/
│   ├── main/java/
│   └── test/java/
│       └── com/example/CalculatorTest.java
```

**build.gradle**:
```groovy
dependencies {
    testImplementation 'junit:junit:4.13.2'
}
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "gradle",
  "framework": "junit4",
  "confidence": 1.0,
  "evidence": [
    "build.gradle found",
    "Gradle Wrapper detected",
    "Gradle dependency: junit:junit",
    "JUnit 4 import in src/test/java/com/example/CalculatorTest.java"
  ],
  "test_command": "./gradlew test",
  "test_reports_dir": "build/test-results/test",
  "build_dir": "build",
  "wrapper": "./gradlew"
}
```

### Example 3: Gradle Kotlin DSL + TestNG

**Project Structure**:
```
my-app/
├── build.gradle.kts
├── settings.gradle.kts
├── src/test/java/
```

**build.gradle.kts**:
```kotlin
dependencies {
    testImplementation("org.testng:testng:7.8.0")
}

tasks.test {
    useTestNG()
}
```

**Detection Result**:
```json
{
  "success": true,
  "build_system": "gradle",
  "framework": "testng",
  "confidence": 0.83,
  "evidence": [
    "build.gradle.kts found",
    "settings.gradle.kts found",
    "Gradle dependency or config: org.testng:testng",
    "Gradle test configuration block found",
    "TestNG import in src/test/java/com/example/UserServiceTest.java"
  ],
  "test_command": "gradle test",
  "test_reports_dir": "build/test-results/test",
  "build_dir": "build",
  "wrapper": null
}
```

## Edge Cases

### Edge Case 1: Multi-Module Maven Project

**Scenario**: Parent POM with multiple child modules

**Strategy**:
- Detect build system from root pom.xml
- Check for `<modules>` in parent POM
- Look for child module pom.xml files
- Aggregate test commands: `mvn test` (runs all modules)

### Edge Case 2: Mixed Frameworks (JUnit 4 + JUnit 5)

**Scenario**: Project transitioning from JUnit 4 to JUnit 5

**Strategy**:
- Both frameworks will have high scores
- Select framework with highest score
- Note in evidence that both detected
- Recommend primary framework (highest score)

### Edge Case 3: No Framework Detected

**Scenario**: Build system exists but no test dependencies

**Strategy**:
- Return build system information
- Low confidence (0.1)
- Default to JUnit 5 (modern standard)
- Warn user that no test framework detected

### Edge Case 4: Gradle Without Wrapper

**Scenario**: Gradle project without gradlew

**Strategy**:
- Use `gradle test` command
- Note in evidence that wrapper not found
- Recommend adding Gradle Wrapper
- Lower confidence slightly

## Confidence Scoring

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 0.8 - 1.0 | High confidence | Proceed with detected framework |
| 0.5 - 0.79 | Medium confidence | Use detected framework, note in logs |
| 0.1 - 0.49 | Low confidence | Use fallback (JUnit 5), warn user |
| 0.0 - 0.09 | No detection | Error - need build system or framework |

## Best Practices

1. **Always detect build system first** - Can't run Java tests without it
2. **Prefer Gradle Wrapper** - Reproducible builds, version consistency
3. **Check for test configuration blocks** - `useJUnitPlatform()` confirms JUnit 5
4. **Parse XML/Groovy/Kotlin carefully** - Syntax varies between DSLs
5. **Default to JUnit 5** - Modern standard, best features
6. **Support multi-module projects** - Maven and Gradle both support modules

## Test Execution Commands

| Build System | Framework | Command | Reports Location |
|--------------|-----------|---------|------------------|
| Maven | JUnit 4/5 | `mvn test` | `target/surefire-reports/` |
| Maven | TestNG | `mvn test` | `target/surefire-reports/` |
| Gradle | JUnit 4/5 | `./gradlew test` | `build/test-results/test/` |
| Gradle | TestNG | `./gradlew test` | `build/test-results/test/` |

## References

- Maven Documentation: https://maven.apache.org/guides/
- Gradle Documentation: https://docs.gradle.org/
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- JUnit 4 Documentation: https://junit.org/junit4/
- TestNG Documentation: https://testng.org/doc/documentation-main.html
- Maven Surefire Plugin: https://maven.apache.org/surefire/maven-surefire-plugin/
- Gradle Test Task: https://docs.gradle.org/current/userguide/java_testing.html

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
