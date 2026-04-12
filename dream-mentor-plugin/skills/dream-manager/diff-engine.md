# Diff Engine Sub-Skill

**Parent**: `skills/dream-manager/SKILL.md`
**Purpose**: Compare the current project against a dream state and produce actionable recommendations.

---

## Diff Procedure

### Input

- Dream name (single dream) or `null` (merged layer view)
- Current project root path

### Output

A structured diff report covering 4 areas: structure, patterns, dependencies, conventions.

---

## Comparison Areas

### 1. Structure Diff

Compare the dream's `structure.md` against the current project's directory layout.

**Analyze**:
- Directories present in dream but missing in current project
- Directories present in current project but not in dream
- File organization differences (e.g., dream uses `src/features/` but project uses `src/components/`)
- Entry point differences
- Test directory placement differences

**Agent Prompt**:
```
Compare the following dream structure analysis against the current project.

DREAM STRUCTURE:
{content of dream's structure.md}

CURRENT PROJECT:
{run Glob and ls on current project to get directory layout}

Identify:
1. Directories/patterns in the dream that the current project is missing
2. Structural differences that could be improved
3. Things the current project does that differ from the dream approach

For each difference, note whether it's:
- RECOMMENDED: Should adopt the dream's approach
- INFORMATIONAL: Different approach, neither is wrong
- SKIP: Current project's approach may be better for its context
```

### 2. Pattern Diff

Compare dream's `patterns.md` against current project's code patterns.

**Analyze**:
- Architecture style alignment
- Design pattern usage differences
- Naming convention mismatches
- Code organization divergences
- Error handling approach differences

**Agent Prompt**:
```
Compare the dream's code patterns against the current project.

DREAM PATTERNS:
{content of dream's patterns.md}

CURRENT PROJECT SAMPLE:
{read 5-10 representative source files from current project}

Identify pattern divergences. For each, categorize as:
- HIGH IMPACT: Fundamental architecture/pattern difference worth adopting
- MEDIUM IMPACT: Convention difference that would improve consistency
- LOW IMPACT: Minor stylistic difference
```

### 3. Dependency Diff

Compare dream's `dependencies.md` against current project's dependencies.

**Analyze**:
- Missing dependencies that dream uses
- Version differences for shared dependencies
- Framework alignment
- Dev tooling gaps

**Agent Prompt**:
```
Compare dependencies between dream and current project.

DREAM DEPENDENCIES:
{content of dream's dependencies.md}

CURRENT PROJECT DEPENDENCIES:
{read package.json, requirements.txt, Cargo.toml, go.mod, etc.}

Identify:
1. Dependencies in the dream that the current project should consider adding
2. Shared dependencies with version differences
3. Dependencies in the current project not in the dream (assess if they're needed)
4. Dev tool gaps (testing, linting, building)
```

### 4. Convention Diff

Compare dream's `conventions.md` against current project's development practices.

**Analyze**:
- Testing approach differences
- Build system differences
- Linting/formatting configuration gaps
- CI/CD pipeline differences
- Documentation approach differences

---

## Multi-Layer Diff

When diffing against the merged layer view (no `--name` specified):

1. Load all active dreams sorted by priority
2. Use the `dream-layers` resolver to produce merged view
3. Diff current project against the merged view
4. In the output, note which dream each recommendation comes from

---

## Output Format

```markdown
# Dream Diff: {dream_name} vs Current Project

**Dream Source**: {url_or_path}
**Dream Commit**: {short_hash}
**Current Project**: {project_name}

---

## Structure Differences

### Missing from current project (recommended)
- `src/middleware/` — Dream uses middleware pattern for request processing
- `tests/integration/` — Dream has separate integration test directory

### Different approach (informational)
- Dream uses `src/features/` grouping; project uses `src/components/` + `src/hooks/`

---

## Pattern Divergences

### High Impact
- **Error handling**: Dream uses Result type pattern; project uses try/catch.
  Consider adopting for better error flow control.

### Medium Impact
- **File naming**: Dream uses kebab-case (`user-service.ts`); project uses
  camelCase (`userService.ts`).

---

## Dependency Gaps

### Recommended additions
- `zod` (v3.22) — Dream uses for runtime validation; project has no validation library
- `vitest` — Dream uses instead of Jest; 3x faster test execution

### Version differences
- `react`: Dream uses 18.3, project uses 18.2 (minor, low risk upgrade)

---

## Convention Mismatches

### Testing
- Dream has 80%+ test coverage with colocated test files
- Project has ~30% coverage with tests in separate `__tests__/` directory

### CI/CD
- Dream has automated linting, testing, and preview deploys
- Project has testing only

---

## Recommendations (prioritized)

1. **Add integration test directory** — High impact, low effort
2. **Adopt Result type error handling** — High impact, medium effort
3. **Add zod for validation** — Medium impact, low effort
4. **Migrate to colocated test files** — Medium impact, high effort
5. **Standardize file naming** — Low impact, high effort (bulk rename)
```

---

## Performance

The diff operation spawns 1-2 agents:
- Agent 1: Structure + dependency diff (reads file lists and package files)
- Agent 2: Pattern + convention diff (reads source code samples)

Target completion: < 60 seconds for typical projects.
