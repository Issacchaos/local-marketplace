# Java Build Systems Integration

**Version**: 1.0.0
**Language**: Java
**Build Systems**: Maven, Gradle
**Purpose**: Integration patterns for Maven and Gradle test execution

## Overview

Java test execution requires build system integration. This skill covers Maven and Gradle configurations, test execution commands, and result extraction patterns.

## Maven Integration

### Maven Project Structure

```
project/
├── pom.xml
├── src/
│   ├── main/java/
│   │   └── com/example/
│   │       └── Calculator.java
│   └── test/java/
│       └── com/example/
│           └── CalculatorTest.java
└── target/
    ├── classes/
    ├── test-classes/
    └── surefire-reports/
        ├── TEST-com.example.CalculatorTest.xml
        └── com.example.CalculatorTest.txt
```

### Maven Test Execution

```bash
# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=CalculatorTest

# Run specific test method
mvn test -Dtest=CalculatorTest#shouldAddNumbers

# Run with specific groups (TestNG)
mvn test -Dgroups=smoke

# Skip tests
mvn install -DskipTests

# Run tests with coverage
mvn test jacoco:report
```

### Maven pom.xml Configuration

#### JUnit 5 (Jupiter)
```xml
<project>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <junit.version>5.10.0</junit.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <version>5.5.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0</version>
                <configuration>
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/Test*.java</include>
                    </includes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

#### JUnit 4
```xml
<dependencies>
    <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.13.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

#### TestNG
```xml
<dependencies>
    <dependency>
        <groupId>org.testng</groupId>
        <artifactId>testng</artifactId>
        <version>7.8.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.0.0</version>
            <configuration>
                <suiteXmlFiles>
                    <suiteXmlFile>testng.xml</suiteXmlFile>
                </suiteXmlFiles>
            </configuration>
        </plugin>
    </plugins>
</build>
```

### Maven Test Reports

**Console Output Location**: Standard output/error
**XML Reports**: `target/surefire-reports/TEST-*.xml`
**Text Reports**: `target/surefire-reports/*.txt`

### Maven Surefire Configuration Options

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.0.0</version>
    <configuration>
        <!-- Include/exclude patterns -->
        <includes>
            <include>**/*Test.java</include>
        </includes>
        <excludes>
            <exclude>**/IntegrationTest.java</exclude>
        </excludes>

        <!-- Parallel execution -->
        <parallel>methods</parallel>
        <threadCount>4</threadCount>

        <!-- Fail fast -->
        <skipAfterFailureCount>1</skipAfterFailureCount>

        <!-- System properties -->
        <systemPropertyVariables>
            <env>test</env>
        </systemPropertyVariables>

        <!-- JVM arguments -->
        <argLine>-Xmx1024m -XX:MaxPermSize=256m</argLine>
    </configuration>
</plugin>
```

## Gradle Integration

### Gradle Project Structure

```
project/
├── build.gradle or build.gradle.kts
├── settings.gradle or settings.gradle.kts
├── gradlew (Unix/Mac)
├── gradlew.bat (Windows)
├── gradle/wrapper/
├── src/
│   ├── main/java/
│   │   └── com/example/
│   │       └── Calculator.java
│   └── test/java/
│       └── com/example/
│           └── CalculatorTest.java
└── build/
    ├── classes/
    ├── test-results/test/
    │   └── TEST-com.example.CalculatorTest.xml
    └── reports/tests/test/
        └── index.html
```

### Gradle Test Execution

```bash
# Run all tests
./gradlew test

# Run specific test class
./gradlew test --tests CalculatorTest

# Run specific test method
./gradlew test --tests CalculatorTest.shouldAddNumbers

# Run with specific category/tag
./gradlew test --tests *IntegrationTest

# Clean and test
./gradlew clean test

# Continuous testing (re-run on file changes)
./gradlew test --continuous

# Run tests with info logging
./gradlew test --info

# Force test re-run (ignore up-to-date checks)
./gradlew cleanTest test
```

### Gradle build.gradle Configuration (Groovy DSL)

#### JUnit 5 (Jupiter)
```groovy
plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'

sourceCompatibility = '17'
targetCompatibility = '17'

repositories {
    mavenCentral()
}

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.10.0'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.10.0'
    testImplementation 'org.mockito:mockito-core:5.5.0'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'
}

test {
    useJUnitPlatform()

    testLogging {
        events "passed", "skipped", "failed"
        exceptionFormat "full"
    }

    // Parallel execution
    maxParallelForks = Runtime.runtime.availableProcessors()

    // JVM arguments
    jvmArgs '-Xmx1024m'
}
```

#### JUnit 4
```groovy
dependencies {
    testImplementation 'junit:junit:4.13.2'
}

test {
    // JUnit 4 is default, no useJUnitPlatform() needed
}
```

#### TestNG
```groovy
dependencies {
    testImplementation 'org.testng:testng:7.8.0'
}

test {
    useTestNG() {
        suites 'src/test/resources/testng.xml'

        // Or configure programmatically
        useDefaultListeners = true
        outputDirectory = file("$buildDir/testng-output")
    }
}
```

### Gradle build.gradle.kts Configuration (Kotlin DSL)

```kotlin
plugins {
    java
}

group = "com.example"
version = "1.0.0"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.10.0")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.10.0")
    testImplementation("org.mockito:mockito-core:5.5.0")
}

tasks.test {
    useJUnitPlatform()

    testLogging {
        events("passed", "skipped", "failed")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }

    maxParallelForks = Runtime.getRuntime().availableProcessors()
}
```

### Gradle Test Reports

**Console Output**: Gradle console during test execution
**XML Reports**: `build/test-results/test/TEST-*.xml`
**HTML Reports**: `build/reports/tests/test/index.html`

### Gradle Test Configuration Options

```groovy
test {
    // Framework selection
    useJUnitPlatform()  // JUnit 5
    // useJUnit()       // JUnit 4
    // useTestNG()      // TestNG

    // Include/exclude patterns
    include '**/*Test.class'
    exclude '**/*IntegrationTest.class'

    // Parallel execution
    maxParallelForks = 4

    // Fail fast
    failFast = true

    // Test logging
    testLogging {
        events "passed", "skipped", "failed", "standardOut", "standardError"
        exceptionFormat "full"
        showStandardStreams = true
    }

    // System properties
    systemProperty 'env', 'test'

    // JVM arguments
    jvmArgs '-Xmx1024m', '-XX:MaxPermSize=256m'

    // Filters
    filter {
        includeTestsMatching "*Test"
        excludeTestsMatching "*IntegrationTest"
    }
}
```

## Gradle Wrapper

### Why Use Gradle Wrapper

- **Version consistency**: All developers use same Gradle version
- **No installation required**: Wrapper downloads Gradle automatically
- **CI/CD friendly**: Works in automated environments

### Generate Wrapper

```bash
gradle wrapper --gradle-version 8.5
```

### Use Wrapper

```bash
# Unix/Mac
./gradlew test

# Windows
gradlew.bat test
```

## Test Execution Patterns

### Pattern 1: Detect and Execute

```python
def execute_tests(project_path):
    # Detect build system
    if exists(join(project_path, "pom.xml")):
        return execute_maven_tests(project_path)
    elif exists(join(project_path, "build.gradle")) or \
         exists(join(project_path, "build.gradle.kts")):
        return execute_gradle_tests(project_path)
    else:
        raise Exception("No build system detected")


def execute_maven_tests(project_path):
    command = ["mvn", "test"]
    result = subprocess.run(
        command,
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "reports_dir": "target/surefire-reports"
    }


def execute_gradle_tests(project_path):
    # Prefer wrapper if available
    if exists(join(project_path, "gradlew")):
        command = ["./gradlew", "test"]
    else:
        command = ["gradle", "test"]

    result = subprocess.run(
        command,
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "reports_dir": "build/test-results/test"
    }
```

### Pattern 2: Parse Reports

```python
def collect_test_results(project_path, build_system):
    if build_system == "maven":
        reports_dir = join(project_path, "target/surefire-reports")
    else:  # gradle
        reports_dir = join(project_path, "build/test-results/test")

    xml_files = glob(join(reports_dir, "TEST-*.xml"))
    return parse_junit_xml_reports(xml_files)
```

## Common Build Commands

### Maven
```bash
mvn clean                    # Clean build artifacts
mvn compile                  # Compile source code
mvn test-compile            # Compile test code
mvn test                    # Run tests
mvn verify                  # Run integration tests
mvn install                 # Install to local repository
mvn clean install           # Clean, compile, test, install
mvn test -Dtest=TestClass   # Run specific test
```

### Gradle
```bash
./gradlew clean             # Clean build artifacts
./gradlew compileJava       # Compile source code
./gradlew compileTestJava   # Compile test code
./gradlew test              # Run tests
./gradlew build             # Compile, test, package
./gradlew clean build       # Clean and build
./gradlew test --tests TestClass  # Run specific test
```

## Troubleshooting

### Maven Issues

**Problem**: Tests not found
```xml
<!-- Solution: Check test inclusion patterns -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <includes>
            <include>**/*Test.java</include>
        </includes>
    </configuration>
</plugin>
```

**Problem**: Wrong JUnit version
```bash
# Solution: Check dependency tree
mvn dependency:tree | grep junit
```

### Gradle Issues

**Problem**: Tests not running
```groovy
// Solution: Ensure proper test framework configuration
test {
    useJUnitPlatform()  // For JUnit 5
}
```

**Problem**: Tests always up-to-date
```bash
# Solution: Force re-run
./gradlew cleanTest test
```

## Best Practices

1. **Use Gradle Wrapper**: Ensures consistent Gradle version
2. **Separate unit and integration tests**: Use different source sets
3. **Configure parallel execution**: Speed up test runs
4. **Enable test reports**: HTML reports for better visibility
5. **Set proper Java version**: Match production environment
6. **Use dependency management**: Centralize version management
7. **Configure test logging**: See test progress in real-time
8. **Handle flaky tests**: Use @RepeatedTest or retry mechanisms

## References

- Maven Surefire: https://maven.apache.org/surefire/maven-surefire-plugin/
- Maven Documentation: https://maven.apache.org/guides/
- Gradle Testing: https://docs.gradle.org/current/userguide/java_testing.html
- Gradle Build Language: https://docs.gradle.org/current/userguide/tutorial_using_tasks.html
- Java Framework Detection: `skills/framework-detection/java-frameworks.md`
- JUnit Parser: `skills/result-parsing/parsers/junit-parser.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
