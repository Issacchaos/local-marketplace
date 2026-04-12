# Dante: Architecture of an AI-Native Test Generation Plugin

**Version 1.0** | February 2026

**Authors**: Architecture Analysis Team

**Subject System**: Dante Plugin for Claude Code

**Repository**: `dante_plugin`

---

## Table of Contents

1. Executive Summary
2. Architecture Overview
3. Component Catalog
4. Data Flow Analysis
5. Invocation Graph
6. Cross-Cutting Concerns
7. Redundancy and Improvement Analysis
8. Conclusion

---

## 1. Executive Summary

### The Problem

Modern software development demands comprehensive test coverage, but writing high-quality tests remains one of the most labor-intensive tasks in the development lifecycle. Developers face a persistent tension: they know tests are essential for regression prevention, refactoring safety, and documentation, yet the cognitive effort required to write thorough test suites -- covering edge cases, mocking dependencies, and following framework conventions -- consistently leads to under-tested code. For teams working across multiple programming languages and testing frameworks, this burden is compounded by the need to master diverse testing idioms, directory conventions, and build system integrations.

### What Dante Is

Dante is an AI-native test generation plugin for Claude Code that automates the entire testing lifecycle: analysis, generation, execution, validation, and iterative repair. It is implemented entirely as a Claude Code plugin -- a collection of Markdown files organized into commands, agents, subagents, and skills -- with no traditional executable code. Instead, Dante uses Claude Code's extension system to define behavior declaratively: commands specify user-facing entry points, agents define specialist personas with structured output extractors, and skills encode domain knowledge that agents load on demand.

The plugin supports 7 programming languages (Python, JavaScript, TypeScript, Java, C#, Go, C++) across 18+ testing frameworks (pytest, Jest, JUnit 4/5, xUnit, Google Test, and many others), making it one of the most polyglot automated testing systems in the Claude Code ecosystem.

### Key Capabilities

- **Automated test generation** with an 80%+ auto-fix success rate for test bugs
- **Human-in-the-loop control** via three approval gates at plan review, code review, and iteration decision points
- **Smart test selection** that achieves 50-70% faster fix iterations by re-running only modified tests
- **Team orchestration** enabling parallel agent execution with configurable concurrency, FIFO queuing, and retry logic
- **Workflow persistence** allowing interrupted sessions to resume from the exact point of interruption
- **Per-agent model selection** with a four-level precedence chain (CLI > environment > config > defaults) mapping Opus, Sonnet, or Haiku to each agent role

### Architecture Philosophy

Dante's architecture is built on four principles:

1. **Coordinator-specialist pattern**: Orchestrators dispatch work to stateless specialist agents via the Task tool. Agents are single-purpose and composable.
2. **Progressive skill loading**: A three-tier system (reference, router, sub-skill) ensures that each agent loads only the 1-7 sub-skill files it needs out of 44+ total, keeping approximately 90% of skill content out of context.
3. **Declarative everything**: The entire system is defined in Markdown with YAML frontmatter. There is no compiled code, no package.json runtime, and no traditional build step.
4. **Fail-fast with graceful degradation**: Team definitions are validated exhaustively before any agent spawns; individual agent failures are retried with exponential backoff; partial successes are aggregated and reported rather than silently discarded.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total components | 33 nodes (6 commands, 1 subagent, 5 agents, 20 skills, 1 external tool) |
| Directed edges | 62 invocation relationships |
| Graph structure | Directed acyclic graph (DAG) -- zero cycles |
| Maximum invocation depth | 7 (via team orchestration path) |
| Reachability from all entry points | 32/33 nodes (96.97%) |
| Single responsibility compliance | 89% (17/19 executable skills) |
| Architecture health score | 7.5/10 (projected 9.5 after recommended fixes) |
| Supported languages | 7 |
| Supported test frameworks | 18+ |

---

## 2. Architecture Overview

### 2.1 The Four-Layer Model

Dante's architecture is organized into four distinct layers, each with a well-defined responsibility boundary. Data flows downward from user entry points through orchestration into specialist execution and finally into domain knowledge retrieval.

**Layer 1 -- Commands** (`commands/*.md`): Six user-facing entry points registered in the plugin manifest. Each command is a thin Markdown file with YAML frontmatter that declares its `description`, `argument-hint`, and `allowed-tools`. The implementation section contains a prompt template that Claude Code executes when the user types the slash command. Commands perform argument parsing, input validation (including security checks for path traversal and null byte injection), and then delegate to an orchestrator or agent. Commands never contain domain logic themselves.

**Layer 2 -- Orchestrators** (`subagents/test-loop-orchestrator.md` and `skills/team-orchestration/SKILL.md`): Two orchestration systems manage multi-phase workflows. The test-loop-orchestrator is a subagent that runs a sequential 7-phase pipeline with approval gates, while the team-orchestration skill coordinates parallel agent execution via YAML-defined team compositions. Both orchestrators interact with agents exclusively through the Task tool, treating them as black boxes that accept structured prompts and return structured Markdown output.

**Layer 3 -- Agents** (`agents/*.md`): Five specialist agents, each with a clearly defined persona, tool permissions, and structured output extractors. Agents are stateless: they receive their full context as part of the Task tool prompt, perform their work using Claude Code's built-in tools (Read, Write, Glob, Grep, Bash), and return structured Markdown reports. Output extractors, defined as regex patterns in each agent's YAML frontmatter, allow orchestrators to programmatically extract fields like `passed_count`, `framework`, or `validation_status` from agent output.

**Layer 4 -- Skills** (`skills/*/SKILL.md`): Twenty skill modules containing domain knowledge, algorithms, and patterns. Skills are not agents; they do not execute autonomously. Instead, agents load skills via the `Skill()` tool call, which triggers Claude Code's progressive loading mechanism. A skill's `SKILL.md` file serves as a lightweight router that dispatches to the appropriate sub-skill file based on the detected language and framework context.

### 2.2 Design Principles

**Declarative system definition.** Every component in Dante -- commands, agents, skills, team definitions, and even the orchestration workflow -- is defined in Markdown files with YAML frontmatter. This is not merely a documentation convention; it is the implementation. The YAML frontmatter in `agents/write-agent.md` contains the `extractors` field, which defines the regex patterns that the orchestrator uses to parse the agent's output. The frontmatter in `commands/test-loop.md` contains the `allowed-tools` field, which declares which skills the command is permitted to invoke. This declarative approach means that the entire plugin can be understood, audited, and modified without any build toolchain.

**Progressive skill loading.** Dante implements a three-tier loading architecture to manage context window consumption:

- *Tier 1 (Reference)*: Skills listed in an agent's definition are declared but not loaded into context. They serve as documentation of available capabilities.
- *Tier 2 (Router)*: When an agent calls `Skill(test-engineering:templates)`, Claude Code loads `skills/templates/SKILL.md` -- a lightweight index file of approximately 20 lines that maps language-framework pairs to specific sub-skill files.
- *Tier 3 (Sub-Skill)*: The router dispatches to exactly one sub-skill file (e.g., `python-pytest-template.md`), loading the full domain knowledge for that specific context. The other 15 template files are never loaded.

This means that a Write Agent working on a Python/pytest project loads approximately 1-7 sub-skill files out of 44+ total, keeping roughly 90% of skill content outside the agent's context window.

**Stateless agents, stateful orchestrators.** Agents are designed to be fully stateless. They receive all necessary context in their Task tool prompt and return self-contained Markdown reports. State persistence is the exclusive responsibility of orchestrators, which write checkpoint files to `{project_root}/.claude/.test-loop-state.md` after each phase. This separation ensures that agents can be retried, replaced, or run in parallel without side effects.

**Security-first input handling.** Every command performs mandatory security validation before delegating to any agent: null byte removal, path length enforcement (max 4,096 characters), absolute path resolution, workspace boundary verification, and user feedback sanitization at approval gates. The Execute Agent is further constrained: it whitelists only known test runner commands, uses array-format command construction (never string interpolation), sets mandatory timeouts (300 seconds default), and limits output capture to 10MB.

### 2.3 Integration with Claude Code's Extension System

Dante hooks into Claude Code through its plugin system, which expects a specific directory structure:

- `commands/` -- Files here are registered as slash commands. Each `.md` file becomes a `/command-name` that users can invoke from the Claude Code prompt.
- `agents/` -- Agent definitions that can be referenced by orchestrators and launched via the Task tool. The YAML frontmatter fields (`name`, `description`, `model`, `extractors`) are parsed by Claude Code's agent framework.
- `skills/` -- Knowledge modules loaded on demand via `Skill(test-engineering:skill-name)` calls. The `name` field in YAML frontmatter determines the skill's invocation identifier.
- `subagents/` -- A specialized directory for workflow orchestrators that are launched via the Task tool but operate at a higher level than individual agents.
- `teams/` -- Team definition files (Markdown with YAML frontmatter) that specify parallel agent compositions. These are consumed by the team-orchestration skill, not directly by Claude Code's plugin loader.

The plugin manifest at `.claude-plugin/plugin.json` registers commands and declares the plugin's metadata, making Dante's commands discoverable through Claude Code's command palette.

---

## 3. Component Catalog

### 3.1 Commands (6)

Commands are the user's entry points into Dante. Each is defined in `commands/{name}.md`.

**`/test-analyze`** (`commands/test-analyze.md`)
Standalone code analysis. Invokes only the Analyze Agent to scan a codebase, detect language and framework, identify testable code units, calculate complexity scores, and prioritize test targets. This is the lightest-weight entry point, touching only 5 of 33 nodes (15.2% reachability).

**`/test-generate`** (`commands/test-generate.md`)
Fully automated test generation with no approval gates. Orchestrates the complete pipeline -- analyze, plan, write, execute, validate -- without pausing for user input. Supports a `--type` flag for unit, integration, or e2e tests, and per-agent model overrides via `--{agent}-model` flags. When invoked with `--use-teams`, it routes to the team-orchestration skill with approval gates disabled. In sequential mode, it reaches 17 nodes; in team mode, 24 nodes.

**`/test-loop`** (`commands/test-loop.md`)
Human-in-the-loop testing workflow with three approval gates. Provides the same pipeline as `/test-generate` but pauses at three critical decision points: (1) test plan approval, (2) generated code review, and (3) iteration decision after execution. State is persisted after every phase, enabling resumption via `/test-resume`. This is the most comprehensive entry point, reaching 25 nodes in team mode (75.8% reachability).

**`/test-resume`** (`commands/test-resume.md`)
Resume an interrupted `/test-loop` workflow. Reads the state file at `.claude/.test-loop-state.md`, parses YAML frontmatter to determine the last completed phase, and relaunches the test-loop-orchestrator from the interruption point.

**`/team-run`** (`commands/team-run.md`)
Direct execution of team definitions. Takes a required team name argument and optional CLI overrides (`--max-agents`, `--timeout`, `--approval-gates`, `--telemetry`). Entry point for arbitrary team definitions beyond testing.

**`/feedback`** (`commands/feedback.md`)
Submit user feedback via GitHub CLI. The simplest command, reaching only 2 of 33 nodes. Exists outside the testing pipeline.

### 3.2 Subagent (1)

**test-loop-orchestrator** (`subagents/test-loop-orchestrator.md`)
The central coordinator for the sequential testing workflow. Manages a 7-phase pipeline:

1. **Analysis**: Launch analyze-agent, detect project root, resolve test locations
2. **Plan Approval**: Present test plan to user (Gate 1)
3. **Code Generation**: Launch write-agent with approved plan
4. **Code Approval**: Present generated code for review (Gate 2)
5. **Execution**: Write test files, launch execute-agent
6. **Validation**: Launch validate-agent, categorize failures
7. **Iteration Decision**: Present results, offer fix/iterate/done options (Gate 3)

The orchestrator is the most connected component in the graph (degree 14, tied with team-orchestration). It uses the `launch_agent_with_retry` pattern for every agent invocation -- 3 retries with exponential backoff [1, 2, 4] seconds and automatic fallback to Sonnet on failure.

### 3.3 Agents (5)

**analyze-agent** (`agents/analyze-agent.md`)
Role: Code analysis and test target identification. Default model: Sonnet.
Skill dependencies: framework-detection, project-detection.

**write-agent** (`agents/write-agent.md`)
Role: Test code generation across 7 languages. Default model: Sonnet.
Skill dependencies: test-location-detection, test-generation, templates, redundancy-detection, helper-extraction, build-integration, linting, framework-detection. This is the most skill-dependent agent (~8 skill loads per invocation).

**execute-agent** (`agents/execute-agent.md`)
Role: Test suite execution and result parsing. Default model: Sonnet.
Skill dependencies: result-parsing, framework-detection.
Smart test selection: On iteration > 0, receives `modified_files` and executes only changed tests (50-70% faster).

**validate-agent** (`agents/validate-agent.md`)
Role: Failure analysis and root cause determination. Default model: Sonnet (Opus recommended).
Skill dependencies: result-parsing, state-management.
Categorizes failures into: Category 1 (test bugs, auto-fixable), Category 2 (source bugs), Category 3 (environment issues).

**fix-agent** (`agents/fix-agent.md`)
Role: Automated test bug repair. Default model: Sonnet (Opus recommended).
Skill dependencies: None (reads files directly, applies targeted edits). Re-invokes execute-agent for validation.
Handles 5 subcategories: missing mock/stub, incorrect assertion, wrong test data, missing import, missing setup.

### 3.4 Skills (20)

#### Testing Skills (6)

| Skill | File | Purpose | In-Degree |
|-------|------|---------|-----------|
| framework-detection | `skills/framework-detection/SKILL.md` | Detect test frameworks via weighted multi-evidence scoring | 6 (highest) |
| test-generation | `skills/test-generation/SKILL.md` | Test generation patterns, principles, and anti-patterns (8 core principles including AAA) | 2 |
| redundancy-detection | `skills/redundancy-detection/SKILL.md` | Prevent duplicate test scenarios via 17 equivalence classes | 1 |
| result-parsing | `skills/result-parsing/SKILL.md` | Parse test framework output using factory pattern (11+ parsers) | 3 |
| templates | `skills/templates/SKILL.md` | Framework-specific test code templates (16 templates across 7 languages) | 2 |
| helper-extraction | `skills/helper-extraction/SKILL.md` | Extract repeated test helpers into shared modules | 1 |

#### Build and Integration Skills (3)

| Skill | File | Purpose | In-Degree |
|-------|------|---------|-----------|
| build-integration | `skills/build-integration/SKILL.md` | Configure test deps in Maven/CMake/.NET/Go | 3 |
| linting | `skills/linting/SKILL.md` | Run linters/formatters with auto-fix (7 languages) | 3 |
| test-location-detection | `skills/test-location-detection/SKILL.md` | Detect correct test file locations, validate against forbidden paths | 3 |

#### Orchestration Skills (7)

| Skill | File | Purpose | In-Degree |
|-------|------|---------|-----------|
| team-orchestration | `skills/team-orchestration/SKILL.md` | Coordinator entry point, 7-phase workflow | 3 |
| team-loader | `skills/team-orchestration/team-loader.md` | Load/validate team YAML definitions, DFS cycle detection | 2 |
| resource-manager | `skills/team-orchestration/resource-manager.md` | Enforce limits (5 agents/team, 5 teams, depth≤3), FIFO queuing | 1 |
| agent-lifecycle-manager | `skills/team-orchestration/agent-lifecycle-manager.md` | Track agent state machine (spawned→running→completed/failed) | 2 |
| approval-gate-handler | `skills/team-orchestration/approval-gate-handler.md` | Before/after approval gates, max 3 iterations | 1 |
| result-aggregator | `skills/team-orchestration/result-aggregator.md` | Combine parallel agent outputs, handle partial failures | 1 |
| telemetry | `skills/telemetry/SKILL.md` | Non-blocking structured event logging (5 event types) | 5 |

#### Utility Skills (4)

| Skill | File | Purpose | In-Degree |
|-------|------|---------|-----------|
| project-detection | `skills/project-detection/SKILL.md` | Find project root by directory tree walk | 5 |
| state-management | `skills/state-management/SKILL.md` | Workflow persistence via markdown + YAML, atomic writes | 3 |
| model-selection | `skills/model-selection/SKILL.md` | Resolve Claude model per agent (4-level precedence) | 4 |
| plugin-standards | `skills/plugin-standards/SKILL.md` | Development standards documentation (orphaned -- never invoked) | 0 |

---

## 4. Data Flow Analysis

### 4.1 The Test Generation Pipeline

The core data flow follows a five-stage pipeline: **Analyze -> Write -> Execute -> Validate -> Fix**.

**Stage 1: Analysis** (analyze-agent)
Input: Target path. Output: Structured analysis with `language`, `framework`, `test_targets`, `priority_summary`, `coverage_gaps`, `complexity_scores`. Saved to `.claude/.last-analysis.md`.

**Stage 2: Code Generation** (write-agent)
Input: Analysis report + approved test plan + test directory + detected framework. Process: Resolve test file locations, load framework template, apply generation patterns, check for redundancy, generate AAA-pattern tests, lint, extract helpers. Output: Test files + generation report.

**Stage 3: Execution** (execute-agent)
Input: Test file paths + iteration number + modified files list (for fix iterations). Process: Detect framework, construct runner command (whitelist-only), execute via Bash with 5-minute timeout, parse output. Output: `exit_code`, `passed_count`, `failed_count`, `failures` with per-failure details.

**Stage 4: Validation** (validate-agent)
Input: Execution report. Process: Categorize failures into Category 1 (test bugs), Category 2 (source bugs), Category 3 (environment issues). Root cause analysis with confidence levels. Output: `validation_status`, `needs_iteration`, failure counts and recommendations.

**Stage 5: Repair** (fix-agent)
Input: Category 1 failures with subcategory classifications. Process: Apply targeted fixes via Edit tool (confidence threshold 0.7). Track modified files. Output: Fix summary. Loops back to Stage 3 with `modified_files` list (max 3 iterations).

### 4.2 The Team Orchestration Pipeline

When `--use-teams` is enabled, a 7-phase parallel pipeline replaces the sequential pipeline:

1. **Initialize**: Generate team execution ID, start telemetry
2. **Load**: team-loader parses YAML, validates schema, checks file references, detects dependency cycles
3. **Approve (Before)**: approval-gate-handler presents execution plan (if enabled)
4. **Spawn**: resource-manager checks capacity, spawns agents via Task tool, queues excess (FIFO)
5. **Monitor**: agent-lifecycle-manager tracks state transitions, handles retries (3x with [1,2,4]s backoff)
6. **Aggregate**: result-aggregator combines outputs, deduplicates files, merges metrics
7. **Approve (After)**: Present aggregated results for review (if enabled)

### 4.3 State Management and Checkpoint/Resume

State file at `{project_root}/.claude/.test-loop-state.md` uses dual-format:
- **YAML frontmatter**: `workflow_id`, `current_phase`, `iteration`, `status`, `language`, `framework`
- **Markdown body**: Progress checklist, phase results, user feedback history

Checkpoints saved: after every phase, before every gate, after user feedback, on error/timeout. Atomic writes (write-to-temp, then rename) prevent corruption. Completed workflows archived to `.claude/.test-loop-history/`.

### 4.4 Model Selection Strategy

| Agent | Default Model | Rationale |
|-------|--------------|-----------|
| validate-agent | Opus | Complex reasoning for root cause analysis |
| fix-agent | Opus | Targeted code repair requires strong reasoning |
| analyze-agent | Sonnet | Pattern matching and scoring |
| write-agent | Sonnet | Template-following code generation |
| execute-agent | Sonnet | Mechanical test execution |

Precedence: CLI flag > environment variable > config file (`dante-config.json`) > defaults.
Fallback: If Opus fails 3x, falls back to Sonnet.

---

## 5. Invocation Graph

### 5.1 Graph Structure

The invocation graph contains **33 nodes** and **62 directed edges**. It is a **DAG (directed acyclic graph)** with zero true cycles. The fix-agent's re-invocation of execute-agent creates a bounded retry loop (max 3 iterations) controlled by the orchestrator, not a structural cycle.

### 5.2 Entry Point Traces

**`/test-loop` (sequential)** -- Depth 6, touches 19 components:
```
/test-loop -> test-loop-orchestrator
  -> model-selection, project-detection, framework-detection, test-location-detection
  -> [Phase 1] analyze-agent -> framework-detection
  -> [GATE 1]
  -> [Phase 3] write-agent -> 8 skills
  -> [GATE 2]
  -> [Phase 5] execute-agent -> result-parsing, framework-detection
  -> [Phase 6] validate-agent -> result-parsing, state-management
  -> [GATE 3]
  -> [Phase 7] fix-agent -> execute-agent (re-run)
  -> state-management (after every phase)
```

**`/test-loop --use-teams`** -- Depth 7 (maximum), touches 25 components:
```
/test-loop -> team-orchestration
  -> team-loader, resource-manager, approval-gate-handler,
     agent-lifecycle-manager, result-aggregator, telemetry
  -> [Task tool spawn]: all 5 agents in parallel
     -> each agent -> respective skills
```

**`/test-generate`** -- Depth 5, touches 17 components (no orchestrator layer).

**`/team-run`** -- Depth 7, touches 25 components (same as --use-teams path).

**`/test-analyze`** -- Depth 4, touches 5 components.

**`/feedback`** -- Depth 2, touches 2 components.

### 5.3 Reachability Analysis

| Entry Point | Mode | Reachable | % of Graph |
|-------------|------|-----------|------------|
| /test-loop | team | 25/33 | 75.8% |
| /team-run | - | 25/33 | 75.8% |
| /test-generate | team | 24/33 | 72.7% |
| /test-loop | sequential | 19/33 | 57.6% |
| /test-resume | - | 19/33 | 57.6% |
| /test-generate | sequential | 17/33 | 51.5% |
| /test-analyze | - | 5/33 | 15.2% |
| /feedback | - | 2/33 | 6.1% |

**Union**: 32/33 nodes reachable (96.97%). Only `plugin-standards` is unreachable (orphaned).

### 5.4 Connectivity Statistics

| Metric | Value |
|--------|-------|
| Most connected (degree) | test-loop-orchestrator (14), team-orchestration (14), write-agent (12) |
| Highest in-degree | framework-detection (6), project-detection (5), telemetry (5) |
| Leaf nodes (out-degree 0) | 14 nodes (42%) |
| Orphans (in-degree 0, not command) | 1 (plugin-standards) |
| Connected components | 2 (main + plugin-standards) |

---

## 6. Cross-Cutting Concerns

### 6.1 Model Selection

Model selection is centralized at the orchestrator level. Agents declare `model: sonnet` as a fallback, but orchestrators override this using the model-selection skill's 4-level precedence chain. Configuration is fully user-controllable via CLI flags, environment variables, config files, or defaults.

### 6.2 Telemetry and Observability

Three design properties: **non-blocking** (failures never halt execution), **opt-in** (disabled unless explicitly enabled), **real-time** (events written within 1 second to append-only logs). Five event types cover the full lifecycle: lifecycle, coordination, progress, test, resource.

### 6.3 Error Handling and Retry Logic

Layered strategy:
- **Agent-level**: 3 retries with [1,2,4]s exponential backoff + Opus→Sonnet fallback
- **Phase-level**: Save state, present options (retry/skip/exit)
- **Team-level**: "continue" or "abort" per team config, 30-minute timeout with 5-minute warning
- **Pipeline-level**: Max 3 fix iterations, max 3 gate iterations

### 6.4 Approval Gates

**Sequential mode** (3 gates): Plan approval, code review, iteration decision. Each supports approve/modify/reject with max 3 iterations.

**Parallel mode** (2 gates): Before-execution (plan review) and after-completion (result review). Configurable via team definition or CLI flags. `/test-generate` disables all gates; `/test-loop` enables them.

---

## 7. Redundancy and Improvement Analysis

### 7.1 Architecture Health Score: 7.5/10

| Category | Score | Weight |
|----------|-------|--------|
| Component Separation | 9/10 | 25% |
| Code Reuse / DRY | 5/10 | 25% |
| Naming Consistency | 7/10 | 15% |
| Single Responsibility | 9/10 | 20% |
| Dead Code Risk | 7/10 | 15% |

### 7.2 Critical Findings (P0)

**1. Duplicate orchestrators.** `test-loop-orchestrator` and `team-orchestration` are both 7-phase workflow coordinators with ~500-800 lines of duplicated logic. They differ only in sequential vs parallel execution and gate configuration.
*Recommendation*: Merge into a single orchestration engine with `mode` parameter.

**2. Near-identical commands.** `/test-loop` and `/test-generate` share ~90% implementation, differing only in approval gate configuration.
*Recommendation*: Extract shared workflow function, parameterize approval mode.

### 7.3 High-Priority Findings (P1)

**3. Framework detection ownership ambiguity.** Both the skill and analyze-agent perform detection.
*Recommendation*: Make the skill the single source of truth; agent should only invoke it.

**4. Confusing result-handling names.** `result-aggregator` (agent outputs) vs `result-parsing` (test framework output) operate at different layers but have similar names.
*Recommendation*: Rename to `agent-result-merger` and `test-output-parser`.

**5. Orphaned plugin-standards.** Zero invocations. Documentation masquerading as a skill.
*Recommendation*: Move to `docs/` directory.

### 7.4 Medium-Priority Findings (P2)

**6.** `test-generation` skill name misleading (provides patterns, doesn't generate). Rename to `test-generation-patterns`.

**7.** `team-loader` too granular (only caller is team-orchestration). Consider inlining.

**8.** Inconsistent naming: bare nouns (`linting`, `templates`, `telemetry`) vs compound (`framework-detection`, `state-management`).

### 7.5 Low-Priority Findings (P3)

**9.** Shared path utilities between project-detection and test-location-detection.
**10.** resource-manager has dual concerns (limits + queuing).
**11.** No shared process-runner utility for subprocess execution.
**12.** No unified config-resolver utility for precedence-based settings.

### 7.6 Projected Impact

| Fix Level | Health Score |
|-----------|-------------|
| Current | 7.5 |
| After P0 | 8.5 |
| After P0 + P1 | 9.0 |
| After all | 9.5 |

---

## 8. Conclusion

### Strengths

1. **Clean layering**: The four-layer model (Commands -> Orchestrators -> Agents -> Skills) provides clear separation of concerns with well-defined interfaces at each boundary.

2. **Progressive loading**: The three-tier skill loading system (reference -> router -> sub-skill) elegantly manages context window constraints, loading only 1-7 of 44+ sub-skills per agent invocation.

3. **Comprehensive language coverage**: 7 languages across 18+ frameworks with consistent abstractions -- the same 5 agents, same pipeline, same state management.

4. **Human-in-the-loop design**: A well-calibrated spectrum from fully automated (`/test-generate`) to fully supervised (`/test-loop`) to customizable (`/team-run --approval-gates`).

5. **Resilience**: Atomic state persistence, 3-level retry with exponential backoff, model fallback, and configurable failure handling make the system robust against the inherent unreliability of long-running AI workflows.

### Key Improvements Needed

The two critical findings -- duplicate orchestrators and near-identical commands -- represent the most impactful improvement opportunities. Addressing these would eliminate ~500-800 lines of duplicated logic, reduce maintenance surface by ~25%, and simplify the invocation graph from two parallel coordination paths to one configurable engine.

### Future Evolution

1. **Test type specialization**: Dedicated team definitions per test type (unit/integration/e2e) for more specialized generation strategies.
2. **Custom team compositions**: The team orchestration system can orchestrate arbitrary agent teams beyond testing -- documentation, code review, refactoring.
3. **Observability maturation**: Structured log analysis, execution time trends, and model cost estimation built on the existing telemetry event stream.

Dante demonstrates that a Claude Code plugin composed entirely of Markdown files can implement a complex, multi-agent, multi-language system. Its architecture is fundamentally sound, with a clear path from 7.5/10 to 9.5/10 through targeted deduplication and naming improvements.

---

*Generated by the Plugin Architecture Analysis Team | February 2026*
