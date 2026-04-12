# TypeScript Framework Detection

**Version**: 1.0.0
**Language**: TypeScript
**Frameworks**: Jest + TypeScript, Vitest (native TypeScript)
**Status**: Phase 3 - Implementation

## Overview

TypeScript framework detection skill that extends JavaScript framework detection with TypeScript-specific considerations. This skill identifies TypeScript projects and determines which testing framework is configured for TypeScript compilation and execution.

## TypeScript Detection Strategy

TypeScript framework detection is a two-phase process:
1. **Phase 1**: Confirm TypeScript project (via tsconfig.json)
2. **Phase 2**: Extend JavaScript framework detection with TypeScript-specific patterns

## Supported Frameworks

### 1. Jest + TypeScript

**Description**: Jest with ts-jest transformer for TypeScript support
**Official Docs**: https://kulshekhar.github.io/ts-jest/
**Minimum Versions**: Jest 27.0.0+, ts-jest 29.0.0+, TypeScript 4.0.0+
**Detection Priority**: High (most common TypeScript testing setup)

**Key Dependencies**:
- `jest` - Test framework
- `ts-jest` - TypeScript transformer for Jest
- `@types/jest` - Jest type definitions
- `typescript` - TypeScript compiler

### 2. Vitest + TypeScript

**Description**: Vitest with native TypeScript support (no transformer needed)
**Official Docs**: https://vitest.dev/guide/
**Minimum Versions**: Vitest 0.30.0+, TypeScript 4.0.0+
**Detection Priority**: High (native TypeScript support, no extra configuration)

**Key Dependencies**:
- `vitest` - Test framework with built-in TypeScript
- `typescript` - TypeScript compiler
- No transformer needed (Vite handles TypeScript natively)

## Phase 1: TypeScript Project Detection

### Primary Indicator: tsconfig.json

The presence of `tsconfig.json` is the definitive indicator of a TypeScript project.

**Detection Logic**:
```javascript
function isTypeScriptProject(projectPath) {
    // Check for tsconfig.json (required for TypeScript)
    if (exists(join(projectPath, "tsconfig.json"))) {
        return {
            isTypeScript: true,
            confidence: 1.0,
            tsconfigPath: "tsconfig.json"
        }
    }

    // Check for alternative tsconfig files
    const altConfigs = [
        "tsconfig.test.json",
        "tsconfig.spec.json",
        "tsconfig.build.json"
    ]

    for (const config of altConfigs) {
        if (exists(join(projectPath, config))) {
            return {
                isTypeScript: true,
                confidence: 0.9,
                tsconfigPath: config
            }
        }
    }

    return {
        isTypeScript: false,
        confidence: 0.0
    }
}
```

### TypeScript Version Detection

```javascript
function detectTypeScriptVersion(packageJsonPath) {
    const pkg = JSON.parse(read(packageJsonPath))
    const allDeps = [
        ...Object.keys(pkg.dependencies || {}),
        ...Object.keys(pkg.devDependencies || {})
    ]

    if (allDeps.includes("typescript")) {
        const version = pkg.devDependencies?.typescript ||
                       pkg.dependencies?.typescript
        return {
            hasTypeScript: true,
            version: version,
            versionNumber: parseVersion(version)  // e.g., "5.3.2"
        }
    }

    return { hasTypeScript: false }
}
```

### tsconfig.json Analysis

Extract relevant TypeScript configuration for test generation:

```javascript
function analyzeTsConfig(tsconfigPath) {
    const tsconfig = JSON.parse(read(tsconfigPath))
    const compilerOptions = tsconfig.compilerOptions || {}

    return {
        strict: compilerOptions.strict || false,
        strictNullChecks: compilerOptions.strictNullChecks || false,
        esModuleInterop: compilerOptions.esModuleInterop || false,
        target: compilerOptions.target || "ES2015",
        module: compilerOptions.module || "commonjs",
        moduleResolution: compilerOptions.moduleResolution || "node",
        types: compilerOptions.types || [],
        typeRoots: compilerOptions.typeRoots || []
    }
}
```

## Phase 2: Framework Detection (TypeScript Extensions)

### Jest + TypeScript Detection

Extends JavaScript Jest detection with TypeScript-specific indicators.

#### 1. ts-jest Configuration (Weight: 10)

**jest.config.js/ts**:
```javascript
// jest.config.js with ts-jest preset
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node'
}

// Or transform configuration
module.exports = {
  transform: {
    '^.+\\.tsx?$': 'ts-jest'
  }
}
```

**Detection Logic**:
```javascript
function detectTsJestConfig() {
    let score = 0
    const evidence = []

    // Check jest.config.js/ts for ts-jest preset
    const configFiles = ["jest.config.js", "jest.config.ts", "jest.config.mjs"]

    for (const configFile of configFiles) {
        if (exists(configFile)) {
            const content = read(configFile)

            // Check for ts-jest preset
            if (content.includes("preset: 'ts-jest'") ||
                content.includes('preset: "ts-jest"')) {
                score += 10
                evidence.push(`${configFile} with ts-jest preset`)
            }

            // Check for ts-jest in transform
            if (content.includes("'ts-jest'") && content.includes("transform")) {
                score += 10
                evidence.push(`${configFile} with ts-jest transform`)
            }
        }
    }

    // Check package.json jest field
    if (exists("package.json")) {
        const pkg = JSON.parse(read("package.json"))
        if (pkg.jest) {
            if (pkg.jest.preset === "ts-jest") {
                score += 10
                evidence.push("package.json jest.preset = ts-jest")
            }
            if (pkg.jest.transform && JSON.stringify(pkg.jest.transform).includes("ts-jest")) {
                score += 10
                evidence.push("package.json jest.transform includes ts-jest")
            }
        }
    }

    return { score, evidence }
}
```

#### 2. TypeScript Jest Dependencies (Weight: 8)

**package.json**:
```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "ts-jest": "^29.1.0",
    "@types/jest": "^29.5.0",
    "typescript": "^5.0.0",
    "@jest/globals": "^29.0.0"
  }
}
```

**Detection Logic**:
```javascript
function detectTypeScriptJestDependencies() {
    let score = 0
    const evidence = []

    if (!exists("package.json")) {
        return { score: 0, evidence: [] }
    }

    const pkg = JSON.parse(read("package.json"))
    const allDeps = [
        ...Object.keys(pkg.dependencies || {}),
        ...Object.keys(pkg.devDependencies || {})
    ]

    // ts-jest is the strongest indicator
    if (allDeps.includes("ts-jest")) {
        score += 8
        evidence.push("ts-jest in dependencies")
    }

    // @types/jest provides TypeScript definitions
    if (allDeps.includes("@types/jest")) {
        score += 5
        evidence.push("@types/jest in dependencies")
    }

    // Combination of jest + typescript (weak signal)
    if (allDeps.includes("jest") && allDeps.includes("typescript")) {
        score += 2
        evidence.push("jest + typescript in dependencies")
    }

    return { score, evidence }
}
```

#### 3. TypeScript Test File Patterns (Weight: 3)

**Detection Logic**:
```javascript
function detectTypeScriptTestFiles() {
    let score = 0
    const evidence = []

    // Check for .test.ts or .spec.ts files
    const tsTestPatterns = [
        "**/*.test.ts",
        "**/*.spec.ts",
        "**/*.test.tsx",
        "**/*.spec.tsx"
    ]

    for (const pattern of tsTestPatterns) {
        const files = glob(pattern, { limit: 5 })
        if (files.length > 0) {
            score += 3
            evidence.push(`Found ${files.length} ${pattern} files`)
            break  // Only count once
        }
    }

    return { score, evidence }
}
```

### Vitest + TypeScript Detection

Vitest has native TypeScript support, so detection is simpler.

#### 1. Vitest Configuration (Weight: 10)

**vitest.config.ts**:
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node'
  }
})
```

**Detection Logic**:
```javascript
function detectVitestTypeScript() {
    let score = 0
    const evidence = []

    // vitest.config.ts is a strong indicator (TypeScript config)
    if (exists("vitest.config.ts")) {
        score += 10
        evidence.push("vitest.config.ts found")
    }

    // Check vite.config.ts for test configuration
    if (exists("vite.config.ts")) {
        const content = read("vite.config.ts")
        if (content.includes("test:") || content.includes("vitest")) {
            score += 10
            evidence.push("vite.config.ts with test configuration")
        }
    }

    return { score, evidence }
}
```

#### 2. Vitest + TypeScript Dependencies (Weight: 8)

**package.json**:
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "typescript": "^5.0.0"
  }
}
```

**Detection Logic**:
```javascript
function detectVitestTypeScriptDependencies() {
    let score = 0
    const evidence = []

    if (!exists("package.json")) {
        return { score: 0, evidence: [] }
    }

    const pkg = JSON.parse(read("package.json"))
    const allDeps = [
        ...Object.keys(pkg.dependencies || {}),
        ...Object.keys(pkg.devDependencies || {})
    ]

    // Vitest + TypeScript combo
    if (allDeps.includes("vitest") && allDeps.includes("typescript")) {
        score += 8
        evidence.push("vitest + typescript in dependencies")
    }

    // Vitest alone (still valid for TypeScript)
    if (allDeps.includes("vitest")) {
        score += 5
        evidence.push("vitest in dependencies (native TS support)")
    }

    return { score, evidence }
}
```

## Complete TypeScript Framework Detection

### Main Detection Function

```javascript
function detectTypeScriptFramework(projectPath) {
    // Phase 1: Confirm TypeScript project
    const tsProject = isTypeScriptProject(projectPath)

    if (!tsProject.isTypeScript) {
        return {
            isTypeScript: false,
            framework: null,
            message: "Not a TypeScript project (no tsconfig.json)"
        }
    }

    // Phase 2: Analyze tsconfig
    const tsConfig = analyzeTsConfig(tsProject.tsconfigPath)
    const tsVersion = detectTypeScriptVersion(join(projectPath, "package.json"))

    // Phase 3: Detect testing framework
    let jestScore = 0
    let vitestScore = 0
    const allEvidence = []

    // Jest detection
    const jestConfig = detectTsJestConfig()
    const jestDeps = detectTypeScriptJestDependencies()
    const tsTestFiles = detectTypeScriptTestFiles()

    jestScore += jestConfig.score
    jestScore += jestDeps.score
    jestScore += tsTestFiles.score
    allEvidence.push(...jestConfig.evidence, ...jestDeps.evidence, ...tsTestFiles.evidence)

    // Vitest detection
    const vitestConfig = detectVitestTypeScript()
    const vitestDeps = detectVitestTypeScriptDependencies()

    vitestScore += vitestConfig.score
    vitestScore += vitestDeps.score
    allEvidence.push(...vitestConfig.evidence, ...vitestDeps.evidence)

    // Select primary framework
    const result = selectTypeScriptFramework(jestScore, vitestScore)

    return {
        isTypeScript: true,
        framework: result.framework,
        confidence: result.confidence,
        evidence: allEvidence,
        typeScriptConfig: {
            version: tsVersion.version,
            strict: tsConfig.strict,
            target: tsConfig.target,
            module: tsConfig.module
        }
    }
}

function selectTypeScriptFramework(jestScore, vitestScore) {
    const total = jestScore + vitestScore

    if (total === 0) {
        // No framework detected, default to Jest + ts-jest
        return {
            framework: "jest",
            subtype: "ts-jest",
            confidence: 0.1,
            reason: "Fallback default (TypeScript + Jest)"
        }
    }

    if (jestScore > vitestScore) {
        return {
            framework: "jest",
            subtype: "ts-jest",
            confidence: Math.min(jestScore / 30, 1.0),
            reason: "Jest + TypeScript indicators strongest"
        }
    } else if (vitestScore > jestScore) {
        return {
            framework: "vitest",
            subtype: "native-typescript",
            confidence: Math.min(vitestScore / 30, 1.0),
            reason: "Vitest with native TypeScript support"
        }
    } else {
        // Tie - prefer Vitest (native TypeScript support)
        return {
            framework: "vitest",
            subtype: "native-typescript",
            confidence: Math.min(vitestScore / 30, 1.0),
            reason: "Tie - preferring Vitest (native TS support)"
        }
    }
}
```

## Examples

### Example 1: Jest + TypeScript Project

**Project Structure**:
```
my-app/
├── tsconfig.json
├── jest.config.ts
├── package.json
└── src/
    ├── calculator.ts
    └── calculator.test.ts
```

**package.json**:
```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "ts-jest": "^29.1.0",
    "@types/jest": "^29.5.0",
    "typescript": "^5.0.0"
  }
}
```

**jest.config.ts**:
```typescript
export default {
  preset: 'ts-jest',
  testEnvironment: 'node'
}
```

**Detection Result**:
```json
{
  "isTypeScript": true,
  "framework": "jest",
  "subtype": "ts-jest",
  "confidence": 0.93,
  "evidence": [
    "tsconfig.json found",
    "jest.config.ts with ts-jest preset",
    "ts-jest in dependencies",
    "@types/jest in dependencies",
    "Found 1 **/*.test.ts files"
  ],
  "typeScriptConfig": {
    "version": "^5.0.0",
    "strict": true,
    "target": "ES2020",
    "module": "commonjs"
  }
}
```

### Example 2: Vitest + TypeScript Project

**Project Structure**:
```
my-app/
├── tsconfig.json
├── vitest.config.ts
├── package.json
└── src/
    ├── calculator.ts
    └── calculator.test.ts
```

**package.json**:
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "typescript": "^5.0.0"
  }
}
```

**vitest.config.ts**:
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true
  }
})
```

**Detection Result**:
```json
{
  "isTypeScript": true,
  "framework": "vitest",
  "subtype": "native-typescript",
  "confidence": 0.73,
  "evidence": [
    "tsconfig.json found",
    "vitest.config.ts found",
    "vitest + typescript in dependencies",
    "Found 1 **/*.test.ts files"
  ],
  "typeScriptConfig": {
    "version": "^5.0.0",
    "strict": false,
    "target": "ESNext",
    "module": "ESNext"
  }
}
```

### Example 3: TypeScript Project with No Test Framework

**Project Structure**:
```
my-app/
├── tsconfig.json
├── package.json
└── src/
    └── calculator.ts
```

**package.json**:
```json
{
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

**Detection Result**:
```json
{
  "isTypeScript": true,
  "framework": "jest",
  "subtype": "ts-jest",
  "confidence": 0.1,
  "evidence": [
    "tsconfig.json found"
  ],
  "typeScriptConfig": {
    "version": "^5.0.0",
    "strict": true,
    "target": "ES2020",
    "module": "commonjs"
  },
  "reason": "Fallback default (TypeScript + Jest)"
}
```

## Integration with JavaScript Detection

TypeScript detection **extends** JavaScript detection:

```javascript
function detectFramework(projectPath) {
    // First, check if TypeScript
    const tsDetection = detectTypeScriptFramework(projectPath)

    if (tsDetection.isTypeScript) {
        return {
            language: "typescript",
            ...tsDetection
        }
    }

    // Fall back to JavaScript detection
    const jsDetection = detectJavaScriptFramework(projectPath)
    return {
        language: "javascript",
        ...jsDetection
    }
}
```

## Edge Cases

### Edge Case 1: Mixed JavaScript and TypeScript

**Scenario**: Project has both .js and .ts files

**Strategy**:
- If tsconfig.json exists → TypeScript project
- Check for `allowJs: true` in tsconfig.json
- Prefer TypeScript test templates for consistency

### Edge Case 2: Monorepo with Multiple tsconfig Files

**Scenario**: Multiple tsconfig.json in different packages

**Strategy**:
- Look for tsconfig.json in current working directory first
- Check for tsconfig.test.json or tsconfig.spec.json
- Document which tsconfig was used

### Edge Case 3: Jest Without ts-jest (JavaScript-only config)

**Scenario**: TypeScript project using Jest but without ts-jest

**Strategy**:
- Confidence score will be low
- Recommend installing ts-jest
- Fall back to JavaScript Jest template with warning

## Best Practices

1. **Always check tsconfig.json first** - Definitive TypeScript indicator
2. **Prefer Vitest for TypeScript** - Native support, no transformer needed
3. **For Jest, require ts-jest** - Without it, TypeScript tests won't run
4. **Check TypeScript strict mode** - Affects test code generation (null checks)
5. **Version compatibility** - Ensure TypeScript, framework, and transformer versions compatible

## Confidence Scoring

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 0.8 - 1.0 | High confidence | Proceed with detected framework |
| 0.5 - 0.79 | Medium confidence | Use detected framework, note in logs |
| 0.1 - 0.49 | Low confidence | Use fallback, warn user |
| 0.0 - 0.09 | No detection | Error - cannot proceed |

## References

- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/
- ts-jest Documentation: https://kulshekhar.github.io/ts-jest/
- Vitest TypeScript Guide: https://vitest.dev/guide/features.html#typescript
- Jest TypeScript: https://jestjs.io/docs/getting-started#using-typescript
- JavaScript Detection: `skills/framework-detection/javascript-frameworks.md`
- TypeScript Patterns: `skills/test-generation/typescript-patterns.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
