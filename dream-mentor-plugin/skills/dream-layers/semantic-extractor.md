# Semantic Extractor Sub-Skill

**Parent**: `skills/dream-layers/SKILL.md`
**Purpose**: Extract semantic context from incoming requests and dream content to enable context-aware layer ordering via the relevance tensor and semantic trie.

---

## Overview

The semantic extractor bridges raw user activity (file edits, queries, task invocations) and the tensor/trie ordering system. It provides two capabilities:

1. **Context Classification** -- Map an incoming request into a structured context index that the tensor can look up.
2. **Semantic Key Extraction** -- Parse a dream's `.md` analysis files to determine what topics it covers, producing the `semantic_profile` stored in `layer.json` and used during tensor population and trie construction.

---

## Context Classification

Every request arrives with ambient signals: the active file path, the user's query text, and the operation being performed. `classify_context()` distills these into one or more **context indices** -- keys into the tensor's third dimension.

### Context Index Taxonomy

Context indices follow a `type.topic` naming convention:

| Type | Description | Example Indices |
|------|-------------|-----------------|
| `file.*` | Derived from the active file path | `file.test`, `file.component`, `file.style`, `file.config`, `file.route`, `file.model`, `file.util`, `file.hook`, `file.migration`, `file.docs` |
| `query.*` | Derived from keywords in the user's natural-language query | `query.testing`, `query.architecture`, `query.styling`, `query.deployment`, `query.dependencies`, `query.naming`, `query.errors`, `query.performance`, `query.security`, `query.state` |
| `task.*` | Derived from the operation the agent is performing | `task.diff`, `task.load`, `task.merge`, `task.list`, `task.status`, `task.update` |
| `_base` | Fallback when no specific context can be determined | `_base` |

### classify_context() Algorithm

```
function classify_context(request: Request): string[] {
  indices = []

  // --- Phase 1: File-based classification ---
  if (request.active_file):
    file_indices = classify_file(request.active_file)
    indices = indices.concat(file_indices)

  // --- Phase 2: Query-based classification ---
  if (request.query_text):
    query_indices = classify_query(request.query_text)
    indices = indices.concat(query_indices)

  // --- Phase 3: Task-based classification ---
  if (request.operation):
    task_index = classify_task(request.operation)
    if (task_index):
      indices.push(task_index)

  // --- Fallback ---
  if (indices.length === 0):
    indices.push("_base")

  // Deduplicate, preserve insertion order
  return unique(indices)
```

### File Pattern Classification

```
function classify_file(file_path: string): string[] {
  indices = []
  normalized = normalize_path(file_path)  // forward slashes, lowercase

  // Test files
  TEST_PATTERNS = [
    "**/*.test.*",
    "**/*.spec.*",
    "**/tests/**",
    "**/__tests__/**",
    "**/test/**",
    "**/*.test-utils.*",
    "**/testing/**",
    "**/*.stories.*"        // Storybook stories are test-adjacent
  ]
  if (any_glob_match(TEST_PATTERNS, normalized)):
    indices.push("file.test")

  // Component files
  COMPONENT_PATTERNS = [
    "**/components/**",
    "**/views/**",
    "**/pages/**",
    "**/screens/**",
    "**/widgets/**",
    "**/ui/**",
    "**/*.component.*",
    "**/*.vue",
    "**/*.svelte",
    "**/*.tsx"               // TSX is component-heavy by convention
  ]
  if (any_glob_match(COMPONENT_PATTERNS, normalized)):
    indices.push("file.component")

  // Style files
  STYLE_PATTERNS = [
    "**/*.css",
    "**/*.scss",
    "**/*.sass",
    "**/*.less",
    "**/*.styled.*",
    "**/styles/**",
    "**/theme/**",
    "**/*.module.css",
    "**/tailwind.config.*"
  ]
  if (any_glob_match(STYLE_PATTERNS, normalized)):
    indices.push("file.style")

  // Configuration files
  CONFIG_PATTERNS = [
    "**/.*rc",
    "**/.*rc.*",
    "**/*.config.*",
    "**/config/**",
    "**/tsconfig.*",
    "**/package.json",
    "**/Makefile",
    "**/Dockerfile",
    "**/docker-compose.*",
    "**/.github/**",
    "**/.gitlab-ci.*",
    "**/Jenkinsfile",
    "**/webpack.config.*",
    "**/vite.config.*",
    "**/rollup.config.*",
    "**/jest.config.*",
    "**/vitest.config.*",
    "**/babel.config.*",
    "**/eslint.config.*",
    "**/.eslintrc*",
    "**/.prettierrc*"
  ]
  if (any_glob_match(CONFIG_PATTERNS, normalized)):
    indices.push("file.config")

  // Route/API files
  ROUTE_PATTERNS = [
    "**/routes/**",
    "**/api/**",
    "**/endpoints/**",
    "**/controllers/**",
    "**/handlers/**",
    "**/middleware/**",
    "**/*.route.*",
    "**/*.controller.*",
    "**/app/api/**",
    "**/pages/api/**"
  ]
  if (any_glob_match(ROUTE_PATTERNS, normalized)):
    indices.push("file.route")

  // Model / data layer files
  MODEL_PATTERNS = [
    "**/models/**",
    "**/entities/**",
    "**/schemas/**",
    "**/types/**",
    "**/interfaces/**",
    "**/prisma/**",
    "**/migrations/**",
    "**/*.model.*",
    "**/*.entity.*",
    "**/*.schema.*",
    "**/*.dto.*"
  ]
  if (any_glob_match(MODEL_PATTERNS, normalized)):
    indices.push("file.model")

  // Utility / helper files
  UTIL_PATTERNS = [
    "**/utils/**",
    "**/helpers/**",
    "**/lib/**",
    "**/shared/**",
    "**/common/**",
    "**/*.util.*",
    "**/*.helper.*"
  ]
  if (any_glob_match(UTIL_PATTERNS, normalized)):
    indices.push("file.util")

  // Hook files (React / framework hooks)
  HOOK_PATTERNS = [
    "**/hooks/**",
    "**/composables/**",
    "**/use*.ts",
    "**/use*.tsx",
    "**/use*.js"
  ]
  if (any_glob_match(HOOK_PATTERNS, normalized)):
    indices.push("file.hook")

  // Migration files
  MIGRATION_PATTERNS = [
    "**/migrations/**",
    "**/migrate/**",
    "**/db/migrate/**",
    "**/*.migration.*"
  ]
  if (any_glob_match(MIGRATION_PATTERNS, normalized)):
    indices.push("file.migration")

  // Documentation files
  DOCS_PATTERNS = [
    "**/docs/**",
    "**/*.md",
    "**/README*",
    "**/CHANGELOG*",
    "**/CONTRIBUTING*",
    "**/*.mdx"
  ]
  if (any_glob_match(DOCS_PATTERNS, normalized)):
    indices.push("file.docs")

  return indices
```

**Note on overlap**: A file can match multiple patterns. For example, `src/components/__tests__/Button.test.tsx` matches `file.test`, `file.component`, and potentially `file.hook` if TSX. This is intentional -- the tensor resolves multi-context lookups by taking the maximum weight across matched contexts for each dream.

### Query Keyword Classification

```
function classify_query(query_text: string): string[] {
  indices = []
  lower = query_text.toLowerCase()
  tokens = tokenize(lower)  // split on whitespace and punctuation

  // Testing
  TESTING_KEYWORDS = [
    "test", "tests", "testing", "spec", "specs",
    "jest", "vitest", "pytest", "junit", "mocha", "cypress",
    "coverage", "mock", "mocking", "stub", "fixture",
    "assertion", "expect", "describe", "it",
    "unit test", "integration test", "e2e", "end-to-end",
    "test runner", "test framework", "tdd", "bdd"
  ]
  if (any_keyword_match(TESTING_KEYWORDS, tokens, lower)):
    indices.push("query.testing")

  // Architecture
  ARCHITECTURE_KEYWORDS = [
    "architecture", "structure", "organize", "layout",
    "monolith", "microservice", "microservices", "monorepo",
    "module", "modules", "boundary", "boundaries",
    "layer", "layers", "separation", "concern",
    "clean architecture", "hexagonal", "onion", "ddd",
    "domain", "aggregate", "bounded context",
    "feature-based", "feature-sliced"
  ]
  if (any_keyword_match(ARCHITECTURE_KEYWORDS, tokens, lower)):
    indices.push("query.architecture")

  // Styling
  STYLING_KEYWORDS = [
    "style", "styles", "styling", "css", "scss", "sass",
    "tailwind", "styled-components", "emotion", "theme",
    "design system", "design tokens", "responsive",
    "layout", "grid", "flexbox", "animation",
    "dark mode", "light mode", "color scheme"
  ]
  if (any_keyword_match(STYLING_KEYWORDS, tokens, lower)):
    indices.push("query.styling")

  // Deployment / CI/CD
  DEPLOYMENT_KEYWORDS = [
    "deploy", "deployment", "ci", "cd", "cicd", "ci/cd",
    "pipeline", "github actions", "gitlab ci", "jenkins",
    "docker", "container", "kubernetes", "k8s",
    "build", "release", "ship", "production",
    "staging", "environment", "infrastructure",
    "terraform", "ansible", "helm"
  ]
  if (any_keyword_match(DEPLOYMENT_KEYWORDS, tokens, lower)):
    indices.push("query.deployment")

  // Dependencies
  DEPENDENCY_KEYWORDS = [
    "dependency", "dependencies", "package", "packages",
    "library", "libraries", "framework", "frameworks",
    "npm", "yarn", "pnpm", "pip", "cargo", "maven",
    "install", "version", "upgrade", "migrate",
    "peer dependency", "devDependency"
  ]
  if (any_keyword_match(DEPENDENCY_KEYWORDS, tokens, lower)):
    indices.push("query.dependencies")

  // Naming conventions
  NAMING_KEYWORDS = [
    "naming", "name", "convention", "conventions",
    "camelCase", "kebab-case", "snake_case", "PascalCase",
    "prefix", "suffix", "abbreviation",
    "file naming", "variable naming", "function naming",
    "consistent naming"
  ]
  if (any_keyword_match(NAMING_KEYWORDS, tokens, lower)):
    indices.push("query.naming")

  // Error handling
  ERROR_KEYWORDS = [
    "error", "errors", "error handling", "exception",
    "exceptions", "try", "catch", "throw",
    "result type", "either", "option", "maybe",
    "fallback", "graceful", "recovery",
    "error boundary", "error page",
    "logging", "monitoring", "alerting"
  ]
  if (any_keyword_match(ERROR_KEYWORDS, tokens, lower)):
    indices.push("query.errors")

  // Performance
  PERFORMANCE_KEYWORDS = [
    "performance", "perf", "optimize", "optimization",
    "fast", "slow", "speed", "latency", "throughput",
    "cache", "caching", "memo", "memoize", "lazy",
    "bundle size", "tree shaking", "code splitting",
    "profiling", "benchmark", "render"
  ]
  if (any_keyword_match(PERFORMANCE_KEYWORDS, tokens, lower)):
    indices.push("query.performance")

  // Security
  SECURITY_KEYWORDS = [
    "security", "secure", "auth", "authentication",
    "authorization", "oauth", "jwt", "token",
    "csrf", "xss", "injection", "sanitize",
    "encrypt", "encryption", "hash", "password",
    "cors", "helmet", "rate limit", "permission",
    "role", "rbac", "acl"
  ]
  if (any_keyword_match(SECURITY_KEYWORDS, tokens, lower)):
    indices.push("query.security")

  // State management
  STATE_KEYWORDS = [
    "state", "state management", "store", "redux",
    "zustand", "mobx", "context", "signal", "signals",
    "reactive", "observable", "atom", "selector",
    "global state", "local state", "server state",
    "react query", "tanstack", "swr"
  ]
  if (any_keyword_match(STATE_KEYWORDS, tokens, lower)):
    indices.push("query.state")

  return indices
```

### Keyword Matching Helper

```
function any_keyword_match(keywords: string[], tokens: string[], full_text: string): boolean {
  for (keyword of keywords):
    if (keyword.includes(" ")):
      // Multi-word keyword: check against full text
      if (full_text.includes(keyword)):
        return true
    else:
      // Single-word keyword: check against token list
      if (keyword in tokens):
        return true
  return false

function tokenize(text: string): string[] {
  // Split on whitespace and common punctuation, lowercase
  return text.split(/[\s,.;:!?()[\]{}"'\/\-_]+/).filter(t => t.length > 0)
```

### Task Classification

```
function classify_task(operation: string): string | null {
  TASK_MAP = {
    "diff":    "task.diff",
    "compare": "task.diff",
    "load":    "task.load",
    "analyze": "task.load",
    "merge":   "task.merge",
    "list":    "task.list",
    "status":  "task.status",
    "stale":   "task.status",
    "check":   "task.status",
    "update":  "task.update",
    "refresh": "task.update",
    "sync":    "task.update"
  }

  lower = operation.toLowerCase()
  if (lower in TASK_MAP):
    return TASK_MAP[lower]

  // Partial match fallback: check if operation starts with a known key
  for (key, value of TASK_MAP):
    if (lower.startsWith(key)):
      return value

  return null
```

---

## Semantic Key Extraction

When a dream is loaded or updated, its `.md` analysis files are parsed to determine what topics the dream covers and how deeply. This produces two outputs:

1. **Semantic keys** -- topic identifiers used to populate trie nodes and tensor cells.
2. **Semantic profile** -- a `topic -> strength` map written to `layer.json`.

### extract_semantic_keys() Algorithm

```
function extract_semantic_keys(analysis_results: DreamAnalysis): SemanticKeySet {
  keys = new Set()

  // --- structure.md ---
  if (analysis_results.structure):
    keys.add("structure")
    content = analysis_results.structure

    if (mentions_directories(content)):
      keys.add("structure.directories")
    if (mentions_modules(content)):
      keys.add("structure.modules")

  // --- patterns.md ---
  if (analysis_results.patterns):
    keys.add("patterns")
    content = analysis_results.patterns

    if (mentions_architecture_style(content)):
      keys.add("patterns.architecture")
    if (mentions_naming_conventions(content)):
      keys.add("patterns.naming")
    if (mentions_error_handling(content)):
      keys.add("patterns.error_handling")
    if (mentions_state_management(content)):
      keys.add("patterns.state_management")
    if (mentions_component_patterns(content)):
      keys.add("patterns.components")

  // --- conventions.md ---
  if (analysis_results.conventions):
    keys.add("conventions")
    content = analysis_results.conventions

    if (mentions_testing(content)):
      keys.add("conventions.testing")
      // Deeper granularity
      if (mentions_test_framework(content)):
        keys.add("conventions.testing.framework")
      if (mentions_test_organization(content)):
        keys.add("conventions.testing.organization")
      if (mentions_mocking(content)):
        keys.add("conventions.testing.mocking")

    if (mentions_build_tool(content)):
      keys.add("conventions.build")
    if (mentions_cicd(content)):
      keys.add("conventions.cicd")
    if (mentions_linting(content)):
      keys.add("conventions.linting")

  // --- dependencies.md ---
  if (analysis_results.dependencies):
    keys.add("dependencies")
    content = analysis_results.dependencies

    if (mentions_frameworks(content)):
      keys.add("dependencies.framework")
    if (mentions_libraries(content)):
      keys.add("dependencies.libraries")

  // --- summary.md ---
  // Summary does not add new keys but can reinforce existing ones.
  // It is used in strength detection (see below).

  return keys
```

### Topic Detection Helpers

Each `mentions_*` function scans the markdown content for indicative headings, keywords, and patterns:

```
function mentions_directories(content: string): boolean {
  INDICATORS = [
    /^#+\s.*director/im,          // Heading containing "director(y|ies)"
    /\bsrc\//i,                    // References to src/
    /\bfolder structure\b/i,
    /\bproject layout\b/i,
    /\bmonorepo\b/i,
    /\bworkspace/i
  ]
  return any_regex_match(INDICATORS, content)

function mentions_modules(content: string): boolean {
  INDICATORS = [
    /\bmodule\b/i, /\bmodules\b/i,
    /\bboundary\b/i, /\bboundaries\b/i,
    /\bpackage\b/i, /\bpackages\b/i,
    /^#+\s.*module/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_architecture_style(content: string): boolean {
  INDICATORS = [
    /\bmicroservice/i, /\bmonolith/i,
    /\bserverless\b/i, /\bevent[- ]driven\b/i,
    /\bclean architecture\b/i, /\bhexagonal\b/i,
    /\blayered architecture\b/i, /\bonion\b/i,
    /\bMVC\b/, /\bMVVM\b/, /\bMVP\b/,
    /^#+\s.*architecture/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_naming_conventions(content: string): boolean {
  INDICATORS = [
    /\bcamelCase\b/, /\bkebab-case\b/, /\bsnake_case\b/, /\bPascalCase\b/,
    /\bnaming convention/i, /\bnaming pattern/i,
    /\bfile naming\b/i, /\bvariable naming\b/i,
    /^#+\s.*naming/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_error_handling(content: string): boolean {
  INDICATORS = [
    /\berror handling\b/i, /\bexception/i,
    /\btry[/\- ]catch\b/i, /\bResult type\b/i,
    /\bEither\b/, /\bOption\b/, /\bMaybe\b/,
    /\berror boundar/i,
    /^#+\s.*error/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_state_management(content: string): boolean {
  INDICATORS = [
    /\bstate management\b/i, /\bredux\b/i,
    /\bzustand\b/i, /\bmobx\b/i, /\bcontext api\b/i,
    /\bsignals?\b/i, /\bstore\b/i,
    /\bglobal state\b/i, /\breactive\b/i,
    /^#+\s.*state/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_component_patterns(content: string): boolean {
  INDICATORS = [
    /\bcomponent/i, /\batomic design\b/i,
    /\bcomposition\b/i, /\bcompound component/i,
    /\brender prop/i, /\bhigher.order/i,
    /\bpresentational\b/i, /\bcontainer\b/i,
    /^#+\s.*component/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_testing(content: string): boolean {
  INDICATORS = [
    /\btest/i, /\bspec\b/i,
    /\bjest\b/i, /\bvitest\b/i, /\bpytest\b/i,
    /\bcoverage\b/i, /\bmock/i,
    /^#+\s.*test/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_test_framework(content: string): boolean {
  INDICATORS = [
    /\bjest\b/i, /\bvitest\b/i, /\bpytest\b/i,
    /\bjunit\b/i, /\bmocha\b/i, /\bcypress\b/i,
    /\bplaywright\b/i, /\btesting library\b/i,
    /\btest runner\b/i, /\btest framework\b/i
  ]
  return any_regex_match(INDICATORS, content)

function mentions_test_organization(content: string): boolean {
  INDICATORS = [
    /\bcolocated\b/i, /\bco-located\b/i,
    /\bseparate.*director/i, /\b__tests__\b/,
    /\btest.*director/i, /\btest.*folder/i,
    /\btest.*location/i, /\btest.*placement/i
  ]
  return any_regex_match(INDICATORS, content)

function mentions_mocking(content: string): boolean {
  INDICATORS = [
    /\bmock/i, /\bstub\b/i, /\bspy\b/i,
    /\bfixture/i, /\bfaker\b/i, /\bfactory\b/i,
    /\btest double/i, /\bdependency injection\b/i
  ]
  return any_regex_match(INDICATORS, content)

function mentions_build_tool(content: string): boolean {
  INDICATORS = [
    /\bwebpack\b/i, /\bvite\b/i, /\besbuild\b/i,
    /\brollup\b/i, /\bturbopack\b/i, /\bparcel\b/i,
    /\bbuild tool\b/i, /\bbuild system\b/i, /\bbundler\b/i,
    /^#+\s.*build/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_cicd(content: string): boolean {
  INDICATORS = [
    /\bci[/ ]?cd\b/i, /\bgithub actions\b/i,
    /\bgitlab ci\b/i, /\bjenkins\b/i,
    /\bpipeline\b/i, /\bcontinuous integration\b/i,
    /\bcontinuous deployment\b/i, /\bcontinuous delivery\b/i,
    /^#+\s.*(ci|cd|pipeline|deploy)/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_linting(content: string): boolean {
  INDICATORS = [
    /\beslint\b/i, /\bprettier\b/i, /\blint/i,
    /\bformat/i, /\bcode style\b/i, /\bstyle guide\b/i,
    /\bbiome\b/i, /\bstylelint\b/i
  ]
  return any_regex_match(INDICATORS, content)

function mentions_frameworks(content: string): boolean {
  INDICATORS = [
    /\breact\b/i, /\bnext\.?js\b/i, /\bvue\b/i, /\bnuxt\b/i,
    /\bangular\b/i, /\bsvelte\b/i, /\bexpress\b/i,
    /\bfastapi\b/i, /\bdjango\b/i, /\bflask\b/i,
    /\bspring\b/i, /\brails\b/i, /\blaravel\b/i,
    /\bframework\b/i,
    /^#+\s.*framework/im
  ]
  return any_regex_match(INDICATORS, content)

function mentions_libraries(content: string): boolean {
  INDICATORS = [
    /\blibrar/i, /\bpackage/i,
    /\bnpm\b/i, /\byarn\b/i, /\bpnpm\b/i,
    /\bpip\b/i, /\bcargo\b/i, /\bmaven\b/i,
    /\bdependenc/i,
    /^#+\s.*(dependenc|librar|package)/im
  ]
  return any_regex_match(INDICATORS, content)

function any_regex_match(patterns: RegExp[], content: string): boolean {
  return patterns.some(p => p.test(content))
```

---

## Content Analysis Functions

### parse_coverage()

Analyze a dream's markdown file to determine the breadth (number of distinct topics) and depth (level of detail) of its coverage.

```
function parse_coverage(file_content: string): CoverageResult {
  // Extract headings to understand structure
  headings = extract_headings(file_content)
  sections = split_by_headings(file_content)

  // Breadth: count of distinct top-level sections with substantive content
  breadth = 0
  topics = []
  for (section of sections):
    if (section.content.trim().length > 50):  // Ignore near-empty sections
      breadth += 1
      topics.push(section.heading)

  // Depth: average nesting depth of headings + content density
  max_heading_depth = 0
  total_heading_depth = 0
  for (heading of headings):
    depth = heading.level  // h1=1, h2=2, h3=3, etc.
    total_heading_depth += depth
    if (depth > max_heading_depth):
      max_heading_depth = depth

  avg_heading_depth = headings.length > 0
    ? total_heading_depth / headings.length
    : 1

  // Content density: ratio of non-whitespace characters to total length
  stripped = file_content.replace(/\s+/g, "")
  density = stripped.length / Math.max(file_content.length, 1)

  // Code block count: indicator of concrete examples
  code_blocks = count_regex_matches(/```[\s\S]*?```/g, file_content)

  // List item count: indicator of enumerated guidance
  list_items = count_regex_matches(/^[\s]*[-*+]\s/gm, file_content)

  // Table count: indicator of structured comparisons
  tables = count_regex_matches(/^\|.*\|.*\|$/gm, file_content)

  return {
    breadth: breadth,
    topics: topics,
    max_heading_depth: max_heading_depth,
    avg_heading_depth: avg_heading_depth,
    content_density: density,
    code_blocks: code_blocks,
    list_items: list_items,
    tables: tables,
    word_count: file_content.split(/\s+/).filter(w => w.length > 0).length
  }
```

### detect_strength()

Score how deeply a piece of content covers a specific topic. Returns a float in `[0.0, 1.0]`.

```
function detect_strength(content: string, topic: string): float {
  // Decompose topic into path segments
  // e.g., "conventions.testing.framework" -> ["conventions", "testing", "framework"]
  segments = topic.split(".")

  // Build progressive keyword sets for each depth level
  // Deeper matches contribute more to strength
  score = 0.0
  max_possible = 0.0

  for (i = 0; i < segments.length; i++):
    segment = segments[i]
    weight = (i + 1) / segments.length  // Deeper segments weighted more

    // Check for heading-level coverage (strong signal)
    heading_regex = new RegExp("^#+\\s.*" + escape_regex(segment), "im")
    if (heading_regex.test(content)):
      score += weight * 0.4
    max_possible += weight * 0.4

    // Check for body-level mentions (moderate signal)
    mention_regex = new RegExp("\\b" + escape_regex(segment) + "\\b", "gi")
    mention_count = count_regex_matches(mention_regex, content)
    // Normalize: 1 mention = 0.1, 3+ mentions = 0.3 (capped)
    mention_score = Math.min(mention_count * 0.1, 0.3)
    score += weight * mention_score
    max_possible += weight * 0.3

    // Check for code examples related to the topic (strong signal)
    code_blocks = extract_code_blocks(content)
    topic_in_code = code_blocks.some(block =>
      new RegExp("\\b" + escape_regex(segment) + "\\b", "i").test(block)
    )
    if (topic_in_code):
      score += weight * 0.3
    max_possible += weight * 0.3

  // Normalize to [0.0, 1.0]
  if (max_possible === 0):
    return 0.0

  raw = score / max_possible

  // Apply sigmoid-like smoothing to avoid clustering at extremes
  // This maps [0, 1] -> [0, 1] with midpoint emphasis
  smoothed = raw * raw * (3 - 2 * raw)  // Hermite smoothing

  // Round to 2 decimal places
  return Math.round(smoothed * 100) / 100
```

### extract_semantic_profile()

Produce the full `semantic_profile` map for a dream's `layer.json`. This is called at dream load time (by the analyzer) and at update time (for incremental refresh).

```
function extract_semantic_profile(analysis_results: DreamAnalysis): SemanticProfile {
  // Step 1: Get the set of semantic keys this dream covers
  keys = extract_semantic_keys(analysis_results)

  // Step 2: For each key, compute strength from the relevant source file
  profile = {}

  for (key of keys):
    // Determine which .md file is the primary source for this key
    source_file = get_source_file_for_key(key)
    content = analysis_results[source_file]

    if (!content):
      continue

    strength = detect_strength(content, key)

    // Only include keys with meaningful strength
    if (strength >= 0.05):
      profile[key] = strength

  // Step 3: Cross-reference with summary.md for reinforcement
  if (analysis_results.summary):
    for (key of Object.keys(profile)):
      summary_strength = detect_strength(analysis_results.summary, key)
      if (summary_strength > 0):
        // Boost by up to 10% if the summary also mentions the topic
        boost = summary_strength * 0.10
        profile[key] = Math.min(1.0, profile[key] + boost)
        profile[key] = Math.round(profile[key] * 100) / 100

  return profile


function get_source_file_for_key(key: string): string {
  // Map top-level key prefix to the .md file that contains it
  prefix = key.split(".")[0]

  SOURCE_MAP = {
    "structure":    "structure",
    "patterns":     "patterns",
    "conventions":  "conventions",
    "dependencies": "dependencies"
  }

  return SOURCE_MAP[prefix] ?? "summary"
```

---

## Output Schemas

### SemanticProfile (written to layer.json)

```json
{
  "semantic_profile": {
    "patterns.architecture": 0.95,
    "patterns.naming": 0.80,
    "patterns.error_handling": 0.45,
    "conventions.testing": 0.30,
    "conventions.testing.framework": 0.25,
    "conventions.build": 0.70,
    "structure": 0.90,
    "structure.directories": 0.85,
    "dependencies.framework": 0.65
  }
}
```

Each value is a float in `[0.0, 1.0]` representing how deeply the dream covers that topic. Values below `0.05` are omitted.

### Context Classification Result

```json
{
  "indices": ["file.test", "query.testing"],
  "source": {
    "file": "src/components/__tests__/Button.test.tsx",
    "query": "what testing framework should I use?",
    "operation": null
  }
}
```

---

## Integration Points

| Consumer | What It Uses | How |
|----------|-------------|-----|
| Tensor builder | `extract_semantic_keys()`, `extract_semantic_profile()` | At dream load/update: populate `tensor[dream][key][_base]` cells from profile strengths |
| Trie builder | `extract_semantic_keys()` | At dream load/update: insert dream into trie nodes for each semantic key |
| Ordering resolver | `classify_context()` | At merge time: classify the request, then look up `tensor[dream][key][context]` for each classified context |
| Reorder preview | `classify_context()` | At preview time: determine context to simulate ordering under |

---

## Edge Cases

### No File Context

When `request.active_file` is null or empty, file-based classification is skipped. The query and task phases still run. If all phases produce nothing, `_base` is returned.

### Ambiguous File Paths

A file at `src/components/tests/utils/TestHelper.tsx` matches `file.component`, `file.test`, and `file.util`. All three indices are returned. The tensor's multi-context resolution (max-weight) handles the ambiguity downstream.

### Empty Dream Content

If a dream's `.md` file is empty or contains only headings with no body content, `detect_strength()` returns `0.0` for all topics. The semantic profile will be empty, and the dream will only appear in tensor lookups under the `_base` context.

### Unknown Keywords

If the user's query contains domain-specific terms not in any keyword list, query classification produces no indices. The `_base` fallback ensures the tensor still returns a valid ordering.

### New Topic Categories

The keyword lists and file patterns are static. To add a new topic:
1. Add the context index to the taxonomy table above.
2. Add a pattern set to `classify_file()` or a keyword set to `classify_query()`.
3. Add a `mentions_*` detector for `extract_semantic_keys()`.
4. The tensor and trie pick up the new key automatically on next dream load.
