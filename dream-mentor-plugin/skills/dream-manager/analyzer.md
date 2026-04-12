# Analyzer Sub-Skill

**Parent**: `skills/dream-manager/SKILL.md`
**Purpose**: Extract structured knowledge from a repository by running parallel analysis agents.

---

## Analysis Strategy

The analyzer spawns up to 3 parallel Explore agents, each focused on a specific aspect of the repository. Results are combined into 5 memory files.

### Agent Allocation

```
Agent 1: Structure + Summary
  - Directory layout, module boundaries, entry points
  - High-level project overview

Agent 2: Patterns + Conventions
  - Architecture style, design patterns, naming conventions
  - Testing, build, CI/CD, documentation patterns

Agent 3: Dependencies
  - Package files, frameworks, libraries, versions
  - Dev tooling, external integrations
```

---

## Agent Prompts

### Agent 1: Structure & Summary Analyst

```
Analyze the repository at "{repo_path}" to understand its structure and purpose.

Produce two outputs:

**STRUCTURE ANALYSIS**:
1. List the top-level directory layout with a brief description of each directory's purpose
2. Identify module/package boundaries (what are the logical units?)
3. Find entry points (main files, index files, app bootstrapping)
4. Locate configuration files (package.json, tsconfig, Makefile, etc.)
5. Map the test directory structure relative to source
6. Note any monorepo or workspace structure

**SUMMARY**:
1. What does this project do? (one paragraph)
2. What are the key architectural decisions and why they were likely made?
3. What is the technology stack? (language, framework, runtime)
4. How mature/active is the project? (file count, directory depth, README quality)
5. What are notable strengths worth emulating?

Output both sections clearly labeled.
```

### Agent 2: Patterns & Conventions Analyst

```
Analyze the repository at "{repo_path}" to understand its code patterns and development conventions.

Produce two outputs:

**PATTERNS ANALYSIS**:
1. Architecture style (monolith, microservices, modular monolith, serverless, etc.)
2. Design patterns in use (MVC, repository, factory, observer, middleware, etc.)
3. Naming conventions:
   - File naming (kebab-case, camelCase, PascalCase, snake_case)
   - Function/method naming
   - Class/type naming
   - Variable naming
4. Code organization (by feature, by layer, by domain, hybrid)
5. Error handling patterns (try/catch, Result types, error codes, middleware)
6. State management approach (if applicable)
7. API design patterns (REST, GraphQL, RPC, etc.)

**CONVENTIONS ANALYSIS**:
1. Testing:
   - Framework(s) used (Jest, pytest, JUnit, etc.)
   - Test organization (colocated, separate directory, both)
   - Naming convention for test files
   - Testing patterns (unit, integration, e2e, snapshot)
   - Mocking strategy
2. Build system:
   - Build tool (webpack, vite, gradle, make, etc.)
   - Scripts defined and their purpose
   - Build outputs and artifacts
3. Linting & formatting:
   - Linter(s) configured
   - Formatter(s) configured
   - Configuration file locations
4. CI/CD:
   - Pipeline tool (GitHub Actions, Jenkins, CircleCI, etc.)
   - Pipeline stages and jobs
5. Documentation:
   - README quality and structure
   - Code documentation style (JSDoc, docstrings, etc.)
   - API documentation approach
6. Git workflow:
   - Branching strategy (if detectable from branch names)
   - Commit message conventions
7. Environment management:
   - Config file patterns (.env, config/, etc.)
   - Secret management approach

Output both sections clearly labeled.
```

### Agent 3: Dependencies Analyst

```
Analyze the repository at "{repo_path}" to catalog its dependencies and technology stack.

**DEPENDENCIES ANALYSIS**:
1. Language(s) and version(s):
   - Primary language
   - Runtime version requirements
   - Language-specific configuration
2. Package manager:
   - Which package manager (npm, yarn, pip, cargo, go mod, etc.)
   - Lock file present? (package-lock.json, yarn.lock, etc.)
3. Core framework(s):
   - Name, version, and purpose of primary framework
   - Secondary frameworks if applicable
4. Production dependencies (top 10-15 most significant):
   - Name, version, and purpose of each
   - Categorize: HTTP, database, auth, logging, validation, etc.
5. Dev dependencies (key ones):
   - Testing libraries
   - Build tools
   - Linting/formatting tools
   - Type checking tools
6. External integrations:
   - Database(s) used
   - Cloud services
   - Third-party APIs
   - Message queues, caches, etc.
7. Version constraints:
   - Minimum versions specified
   - Pinned vs range versions
   - Notable version incompatibilities

Output the analysis clearly organized.
```

---

## Incremental Analysis

For updates (not initial load), only re-analyze affected areas:

### File-to-Memory Mapping

```
Changed files in...       → Re-analyze...
─────────────────────────────────────────
src/, lib/, app/          → patterns.md, structure.md
package.json, Cargo.toml  → dependencies.md
*.test.*, __tests__/      → conventions.md (testing section)
.github/, Jenkinsfile     → conventions.md (CI section)
Makefile, webpack.config   → conventions.md (build section)
.eslintrc, prettier.config → conventions.md (linting section)
README.md, docs/          → summary.md
Any directory changes     → structure.md
```

### Incremental Agent Prompt

```
The repository at "{repo_path}" has been updated. The following files changed:

{list of changed files}

Re-analyze ONLY the affected areas. Here is the previous analysis for context:

{previous memory file content}

Update the analysis to reflect the changes. Keep unchanged sections as-is.
Output the complete updated analysis.
```

---

## Output Format

Each agent returns structured text that the memory-writer skill formats into frontmatter-annotated markdown files.

### Quality Checks

Before writing, validate that analysis:
1. Is not empty or trivially short (< 100 chars per section)
2. Contains concrete observations (not generic boilerplate)
3. References actual files/directories found in the repo
4. Does not contain hallucinated paths or dependencies

If an agent produces low-quality output, flag it in the summary:
```
Warning: {section} analysis may be incomplete. Consider running /mentor update --name {name} to re-analyze.
```
