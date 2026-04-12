# JavaScript Framework Detection

**Version**: 1.0.0
**Language**: JavaScript
**Frameworks**: Jest, Vitest, Mocha
**Status**: Phase 3 - Implementation

## Overview

JavaScript framework detection skill for identifying Jest, Vitest, and Mocha testing frameworks in JavaScript projects. This skill provides detailed detection patterns, confidence scoring, and edge case handling specific to JavaScript testing.

## Supported Frameworks

### 1. Jest

**Description**: Delightful JavaScript testing framework with focus on simplicity
**Official Docs**: https://jestjs.io/
**Minimum Version**: 27.0.0+
**Detection Priority**: High (most popular, default choice)

### 2. Vitest

**Description**: Blazing fast unit test framework powered by Vite
**Official Docs**: https://vitest.dev/
**Minimum Version**: 0.30.0+
**Detection Priority**: High (modern, gaining popularity)

### 3. Mocha

**Description**: Feature-rich JavaScript test framework running on Node.js
**Official Docs**: https://mochajs.org/
**Minimum Version**: 9.0.0+
**Detection Priority**: Medium (flexible, established)

## Detection Patterns

### Jest Detection

#### 1. Configuration Files (Weight: 10)

```javascript
// Check for Jest-specific config files
jest.config.js                // Primary Jest config
jest.config.ts                // TypeScript config
jest.config.json              // JSON config
jest.config.mjs               // ES module config
package.json                  // Check for "jest" field
```

**Detection Logic**:
```javascript
// For jest.config.* - exact file match
if (exists("jest.config.js") || exists("jest.config.ts") ||
    exists("jest.config.json") || exists("jest.config.mjs")):
    score += 10
    evidence.append("jest.config.* found")

// For package.json - must contain "jest" configuration field
if (exists("package.json")):
    const pkg = JSON.parse(read("package.json"))
    if (pkg.jest):
        score += 10
        evidence.append("package.json with 'jest' configuration")
```

#### 2. Dependencies (Weight: 8)

**package.json** (devDependencies):
```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "@jest/globals": "^29.0.0",
    "ts-jest": "^29.0.0",
    "@types/jest": "^29.0.0",
    "jest-environment-jsdom": "^29.0.0"
  }
}
```

**Detection Logic**:
```javascript
// Parse package.json
if (exists("package.json")):
    const pkg = JSON.parse(read("package.json"))
    const allDeps = [
        ...Object.keys(pkg.dependencies || {}),
        ...Object.keys(pkg.devDependencies || {})
    ]

    // Check for jest
    if (allDeps.includes("jest")):
        score += 8
        evidence.append("jest in dependencies")

    // Check for Jest plugins (strong indicators)
    const jestPlugins = ["ts-jest", "@jest/globals", "jest-environment-jsdom",
                         "@types/jest", "babel-jest"]
    for (const plugin of jestPlugins):
        if (allDeps.includes(plugin)):
            score += 2
            evidence.append(`${plugin} found`)
```

#### 3. Scripts in package.json (Weight: 5)

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

**Detection Logic**:
```javascript
if (exists("package.json")):
    const pkg = JSON.parse(read("package.json"))
    const scripts = pkg.scripts || {}

    for (const [name, command] of Object.entries(scripts)):
        if (command.includes("jest")):
            score += 5
            evidence.append(`Script "${name}" uses jest`)
            break  // Only count once
```

#### 4. Import Patterns (Weight: 2)

Scan JavaScript files (*.js, *.jsx, *.mjs):

```javascript
import { describe, it, expect, test } from '@jest/globals';
const { describe, test, expect } = require('@jest/globals');

// Jest globals (when using jest environment)
describe('test suite', () => {
  test('test case', () => {
    expect(value).toBe(expected);
  });
});
```

**Detection Logic**:
```javascript
// Sample up to 50 .js/.jsx/.mjs files
const sourceFiles = glob("**/*.{js,jsx,mjs}").slice(0, 50)

for (const file of sourceFiles):
    const content = read(file)

    // Check for Jest imports
    if (content.includes("from '@jest/globals'") ||
        content.includes("require('@jest/globals')")):
        score += 2
        evidence.append(`Jest imports in ${file}`)
```

#### 5. Code Patterns (Weight: 3)

```javascript
// Jest-specific patterns
describe('suite name', () => {         // Test suite
  test('test name', () => {            // Test case (jest-specific)
    expect(result).toBe(expected);     // Jest assertions
  });

  it('test name', () => {              // Alternative test syntax
    expect(result).toEqual(expected);
  });
});

// Jest-specific matchers
expect(value).toMatchSnapshot();
expect(fn).toHaveBeenCalled();
expect(element).toBeInTheDocument();
```

**Detection Regex Patterns**:
```javascript
const patterns = [
    /describe\s*\(/,                        // Test suite
    /test\s*\(/,                            // Jest-specific test
    /it\s*\(/,                              // Standard test
    /expect\(.*\)\.to/,                     // Expect assertions
    /expect\(.*\)\.toMatchSnapshot/,        // Jest-specific matcher
    /jest\.mock\(/,                         // Jest mocking
    /jest\.fn\(/,                           // Jest mock function
]

for (const file of sourceFiles):
    const content = read(file)
    for (const pattern of patterns):
        if (pattern.test(content)):
            score += 3
            evidence.append(`Pattern '${pattern}' in ${file}`)
            break  // One match per file
```

#### 6. Test File Patterns (Weight: 1)

Jest discovers tests in files matching:
```
*.test.js
*.test.jsx
*.spec.js
*.spec.jsx
**/__tests__/*.js
**/__tests__/*.jsx
```

**Detection Logic**:
```javascript
const testFiles = [
    ...glob("**/*.test.{js,jsx}"),
    ...glob("**/*.spec.{js,jsx}"),
    ...glob("**/__tests__/**/*.{js,jsx}")
]
if (testFiles.length > 0):
    score += 1
    evidence.append(`${testFiles.length} Jest-style test files found`)
```

### Vitest Detection

#### 1. Configuration Files (Weight: 10)

```javascript
vitest.config.js              // Primary Vitest config
vitest.config.ts              // TypeScript config
vite.config.js                // Vite config with test field
vite.config.ts                // TypeScript Vite config
```

**Detection Logic**:
```javascript
if (exists("vitest.config.js") || exists("vitest.config.ts")):
    score += 10
    evidence.append("vitest.config.* found")

// Check for Vite config with test configuration
if (exists("vite.config.js") || exists("vite.config.ts")):
    const content = read("vite.config.*")
    if (content.includes("test:") || content.includes("test {")):
        score += 10
        evidence.append("vite.config.* with test configuration")
```

#### 2. Dependencies (Weight: 8)

```json
{
  "devDependencies": {
    "vitest": "^0.34.0",
    "@vitest/ui": "^0.34.0",
    "happy-dom": "^10.0.0",
    "jsdom": "^22.0.0"
  }
}
```

**Detection Logic**:
```javascript
if (exists("package.json")):
    const pkg = JSON.parse(read("package.json"))
    const allDeps = [
        ...Object.keys(pkg.dependencies || {}),
        ...Object.keys(pkg.devDependencies || {})
    ]

    if (allDeps.includes("vitest")):
        score += 8
        evidence.append("vitest in dependencies")

    // Vitest plugins
    const vitestPlugins = ["@vitest/ui", "happy-dom", "jsdom"]
    for (const plugin of vitestPlugins):
        if (allDeps.includes(plugin)):
            score += 2
            evidence.append(`${plugin} found`)
```

#### 3. Scripts in package.json (Weight: 5)

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run"
  }
}
```

#### 4. Import Patterns (Weight: 2)

```javascript
import { describe, it, expect, test, vi } from 'vitest';
```

#### 5. Code Patterns (Weight: 3)

```javascript
// Vitest-specific patterns
import { vi } from 'vitest';           // Vitest utilities

vi.mock('./module');                    // Vitest mocking
const spy = vi.spyOn(obj, 'method');   // Vitest spy
```

**Detection Regex Patterns**:
```javascript
const patterns = [
    /from ['"]vitest['"]/,              // Vitest import
    /vi\.mock\(/,                        // Vitest mocking
    /vi\.spyOn\(/,                       // Vitest spy
    /vi\.fn\(/,                          // Vitest mock function
]
```

#### 6. Test File Patterns (Weight: 1)

Vitest uses same patterns as Jest:
```
*.test.js, *.test.ts
*.spec.js, *.spec.ts
**/__tests__/**/*
```

### Mocha Detection

#### 1. Configuration Files (Weight: 10)

```javascript
.mocharc.js                   // Mocha config
.mocharc.json                 // JSON config
.mocharc.yaml                 // YAML config
mocha.opts                    // Legacy config (deprecated)
package.json                  // "mocha" field
```

**Detection Logic**:
```javascript
if (exists(".mocharc.js") || exists(".mocharc.json") ||
    exists(".mocharc.yaml") || exists("mocha.opts")):
    score += 10
    evidence.append("Mocha config file found")

if (exists("package.json")):
    const pkg = JSON.parse(read("package.json"))
    if (pkg.mocha):
        score += 10
        evidence.append("package.json with 'mocha' configuration")
```

#### 2. Dependencies (Weight: 8)

```json
{
  "devDependencies": {
    "mocha": "^10.0.0",
    "chai": "^4.3.0",
    "@types/mocha": "^10.0.0",
    "@types/chai": "^4.3.0"
  }
}
```

**Detection Logic**:
```javascript
if (allDeps.includes("mocha")):
    score += 8
    evidence.append("mocha in dependencies")

// Common Mocha companions (Mocha has no built-in assertions)
const mochaCompanions = ["chai", "expect.js", "should", "@types/mocha"]
for (const companion of mochaCompanions):
    if (allDeps.includes(companion)):
        score += 2
        evidence.append(`${companion} found (Mocha companion)`)
```

#### 3. Scripts in package.json (Weight: 5)

```json
{
  "scripts": {
    "test": "mocha",
    "test:watch": "mocha --watch"
  }
}
```

#### 4. Import Patterns (Weight: 2)

```javascript
const { describe, it } = require('mocha');
import { describe, it } from 'mocha';

// Chai assertions (common with Mocha)
const { expect } = require('chai');
import { expect } from 'chai';
```

#### 5. Code Patterns (Weight: 3)

```javascript
// Mocha-specific patterns
describe('suite', function() {          // Function syntax (this binding)
  before(function() {                   // Mocha hooks
    // setup
  });

  it('test', function() {
    // Mocha uses external assertion libraries
    expect(value).to.equal(expected);   // Chai-style
  });
});
```

**Detection Regex Patterns**:
```javascript
const patterns = [
    /describe\s*\(/,                    // Test suite
    /it\s*\(/,                          // Test case
    /before\s*\(/,                      // Mocha hook
    /after\s*\(/,                       // Mocha hook
    /beforeEach\s*\(/,                  // Mocha hook
    /afterEach\s*\(/,                   // Mocha hook
]
```

#### 6. Test File Patterns (Weight: 1)

Mocha defaults to:
```
test/*.js
test/**/*.js
```

But configurable, so check for common patterns:
```
*.test.js
*.spec.js
test/**/*.js
```

## Confidence Scoring Examples

### Example 1: Pure Jest Project

```
Project Structure:
├── jest.config.js
├── package.json  (contains "jest": "^29.0.0" in devDependencies)
├── src/
│   └── calculator.js
└── __tests__/
    ├── calculator.test.js  (contains "import { describe, test, expect } from '@jest/globals'")
    └── utils.test.js

Scoring:
- jest.config.js found: +10
- jest in package.json devDependencies: +8
- "test": "jest" script: +5
- "@jest/globals" import: +2
- describe/test patterns: +3
- 2 test files in __tests__/: +1

Total Jest score: 29
Total Vitest score: 0
Total Mocha score: 0

Confidence: jest = 29/29 = 1.0 (100%)
Result: PRIMARY=jest, SECONDARY=[], CONFIDENCE=1.0
```

### Example 2: Vitest Project

```
Project Structure:
├── vitest.config.ts
├── package.json  (contains "vitest": "^0.34.0")
├── src/
│   └── api.ts
└── tests/
    └── api.test.ts  (contains "import { describe, it, expect, vi } from 'vitest'")

Scoring:
- vitest.config.ts found: +10
- vitest in dependencies: +8
- "test": "vitest" script: +5
- "from 'vitest'" import: +2
- vi.mock pattern: +3
- 1 test file: +1

Total Vitest score: 29
Total Jest score: 0

Confidence: vitest = 29/29 = 1.0 (100%)
Result: PRIMARY=vitest, SECONDARY=[], CONFIDENCE=1.0
```

### Example 3: Mocha with Chai Project

```
Project Structure:
├── .mocharc.json
├── package.json  (contains "mocha": "^10.0.0", "chai": "^4.3.0")
├── src/
│   └── server.js
└── test/
    └── server.test.js  (contains "const { expect } = require('chai')")

Scoring:
- .mocharc.json found: +10
- mocha in dependencies: +8
- chai in dependencies: +2 (companion)
- "test": "mocha" script: +5
- describe/it patterns: +3
- 1 test file: +1

Total Mocha score: 29
Result: PRIMARY=mocha, SECONDARY=[], CONFIDENCE=1.0
```

### Example 4: Mixed Jest/Vitest Project (Migrating)

```
Project Structure:
├── jest.config.js  (legacy)
├── vitest.config.ts  (new)
├── package.json  (contains both "jest" and "vitest")
├── tests/
│   ├── legacy.test.js  (Jest-style)
│   └── new.test.ts  (Vitest-style with vi.*)

Scoring:
Jest:
- jest.config.js: +10
- jest in dependencies: +8
- describe/test patterns: +3
Total: 21

Vitest:
- vitest.config.ts: +10
- vitest in dependencies: +8
- vitest imports: +2
- vi.mock pattern: +3
Total: 23

Total: 21 + 23 = 44

Confidence:
- vitest = 23/44 = 0.52 (52%)
- jest = 21/44 = 0.48 (48%)

Result: PRIMARY=vitest, SECONDARY=[jest], CONFIDENCE=0.52
Recommendation: "Project is migrating from Jest to Vitest. Vitest selected as primary."
```

### Example 5: No Framework (Fallback)

```
Project Structure:
├── package.json  (no test dependencies)
├── src/
│   └── app.js
(no test files)

Scoring:
- No config files: 0
- No dependencies: 0
- No test files: 0

Total: 0

Result: PRIMARY=jest (fallback), SECONDARY=[], CONFIDENCE=0.1
Recommendation: "No testing framework detected. Jest recommended for new JavaScript projects."
```

## Edge Cases

### 1. package.json with Jest but no config file

**Scenario**: Developer added jest dependency but hasn't created config yet

**Detection**:
- jest in package.json: +8
- "test": "jest" script: +5
- Score: 13

**Result**: PRIMARY=jest, CONFIDENCE=0.87 (high confidence)
**Recommendation**: "Jest detected via dependencies. Consider creating jest.config.js for explicit configuration."

### 2. Vite project without test configuration

**Scenario**: Using Vite for build but no testing setup

**Detection**:
- vite.config.js exists but no test field: 0
- No vitest in dependencies: 0

**Result**: PRIMARY=jest (fallback), CONFIDENCE=0.1
**Note**: Vite alone doesn't indicate testing framework

### 3. Mocha with unconventional test directory

**Scenario**: Tests in custom directory (specs/ instead of test/)

**Detection**:
- .mocharc.json with spec: ["specs/**/*.js"]: +10
- mocha in dependencies: +8
- Mocha patterns in specs/: +3

**Result**: PRIMARY=mocha, CONFIDENCE=0.95
**Note**: Config file provides correct test location

### 4. Jest compatibility mode in Vitest

**Scenario**: Vitest configured with Jest compatibility

**Detection**:
- vitest.config.ts with globals: true: +10
- vitest in dependencies: +8
- Both jest and vitest patterns: ambiguous

**Result**: PRIMARY=vitest, SECONDARY=[jest], CONFIDENCE=0.60
**Note**: Vitest's globals option makes it Jest-compatible

## Framework Selection Logic

```javascript
function selectPrimaryFramework(jestScore, vitestScore, mochaScore) {
    const total = jestScore + vitestScore + mochaScore

    // No evidence at all
    if (total === 0) {
        return {
            primary: 'jest',           // Fallback to Jest (most popular)
            secondary: [],
            confidence: 0.1,
            recommendation: 'No testing framework detected. Jest recommended for new JavaScript projects.'
        }
    }

    // Calculate confidences
    const scores = {
        jest: jestScore / total,
        vitest: vitestScore / total,
        mocha: mochaScore / total
    }

    // Find primary (highest score)
    const primary = Object.keys(scores).reduce((a, b) =>
        scores[a] > scores[b] ? a : b
    )
    const primaryConf = scores[primary]

    // Find secondary (confidence >= 0.2)
    const secondary = Object.keys(scores)
        .filter(fw => fw !== primary && scores[fw] >= 0.2)
        .sort((a, b) => scores[b] - scores[a])

    return {
        primary,
        secondary,
        confidence: primaryConf,
        recommendation: getRecommendation(primary, primaryConf, secondary, scores)
    }
}

function getRecommendation(primary, confidence, secondary, scores) {
    if (confidence >= 0.8) {
        return `Strong detection: ${primary} is clearly the primary framework.`
    } else if (confidence >= 0.5) {
        if (secondary.length > 0) {
            return `Moderate detection: ${primary} is primary (${(confidence*100).toFixed(0)}%), but ${secondary.join(', ')} also present. Consider migrating to single framework.`
        }
        return `Moderate detection: ${primary} is likely the primary framework.`
    } else if (confidence >= 0.3) {
        return `Weak detection: ${primary} detected with low confidence. Consider specifying framework explicitly.`
    } else {
        return `Fallback to ${primary}. No clear framework detected. Recommend adding explicit configuration.`
    }
}
```

## Package Manager Detection

JavaScript projects use npm, yarn, or pnpm:

### npm (Node Package Manager)

**Indicators**:
- Files: `package-lock.json`
- Commands: `npm install`, `npm test`

### yarn

**Indicators**:
- Files: `yarn.lock`
- Commands: `yarn install`, `yarn test`

### pnpm

**Indicators**:
- Files: `pnpm-lock.yaml`
- Commands: `pnpm install`, `pnpm test`

**Detection Strategy**:
```javascript
if (exists("pnpm-lock.yaml")):
    packageManager = "pnpm"
else if (exists("yarn.lock")):
    packageManager = "yarn"
else if (exists("package-lock.json")):
    packageManager = "npm"
else:
    packageManager = "npm"  // Default
```

**Usage**: Package manager determines test execution command but doesn't affect framework detection.

## Output Format

When detection is complete, return structured data:

```yaml
language: javascript
primary_framework: jest
secondary_frameworks:
  - vitest
confidence:
  jest: 0.60
  vitest: 0.35
  mocha: 0.05
package_manager:
  type: npm
  config_file: package.json
  lock_file: package-lock.json
detection_details:
  config_files:
    - jest.config.js
  dependencies:
    - jest@^29.0.0
    - vitest@^0.34.0
  scripts:
    - test: "jest"
  import_patterns:
    - "from '@jest/globals'" in tests/app.test.js
    - "from 'vitest'" in tests/new.test.ts
  code_patterns:
    - "describe()" in tests/app.test.js
    - "vi.mock()" in tests/new.test.ts
  test_file_count: 12
  evidence_types: 5
recommendation: "Moderate detection: jest is primary (60%), but vitest also present (35%). Consider migrating to single framework."
```

## Usage in Agents

### Analyze Agent

```markdown
# Read JavaScript Framework Detection Skill
Read file: skills/framework-detection/javascript-frameworks.md

# Apply Detection Strategies
1. Check for jest.config.*, vitest.config.*, .mocharc.* files
2. Parse package.json for dependencies (jest, vitest, mocha)
3. Check package.json scripts for test commands
4. Scan up to 50 .js/.jsx/.mjs files for imports and patterns
5. Count test files matching *.test.js, *.spec.js, __tests__/**

# Calculate Scores
jestScore = sum(jest_evidence_weights)
vitestScore = sum(vitest_evidence_weights)
mochaScore = sum(mocha_evidence_weights)

# Select Framework
if (jestScore + vitestScore + mochaScore === 0):
    primary = "jest"  // Fallback
    confidence = 0.1
else:
    primary = highest_score_framework
    confidence = primary_score / total_score

# Output
Return: {
    "framework": primary,
    "confidence": confidence,
    "secondary": frameworks_with_confidence_>=_0.2,
    "package_manager": detected_package_manager
}
```

## Testing Validation

Test with these sample projects:

1. **jest-only**: jest.config.js + jest in package.json → Expect: jest, confidence ≥ 0.8
2. **vitest-only**: vitest.config.ts + vitest in package.json → Expect: vitest, confidence ≥ 0.8
3. **mocha-chai**: .mocharc.json + mocha + chai → Expect: mocha, confidence ≥ 0.7
4. **no-framework**: package.json without test deps → Expect: jest (fallback), confidence = 0.1
5. **mixed-jest-vitest**: Both frameworks present → Expect: highest score primary, both listed

## References

- Jest documentation: https://jestjs.io/docs/getting-started
- Vitest documentation: https://vitest.dev/guide/
- Mocha documentation: https://mochajs.org/#getting-started
- npm package.json: https://docs.npmjs.com/cli/v9/configuring-npm/package-json
- Phase 1 Python detection: `skills/framework-detection/python-frameworks.md`

---

**Last Updated**: 2025-12-08
**Phase**: 3 - Implementation
**Status**: Complete
