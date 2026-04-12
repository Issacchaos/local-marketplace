# Dante Plugin Skill Inventory

**Date**: February 2026
**Total Components**: 33 (6 commands, 1 subagent, 5 agents, 20 skills, 1 external)

---

## Commands (6)

### /test-analyze
- **File**: `commands/test-analyze.md`
- **Purpose**: Standalone code analysis to identify testing needs
- **User-Invocable**: Yes (`/test-analyze [path]`)
- **Invokes**: analyze-agent, framework-detection, project-detection, model-selection
- **Invoked By**: User

### /test-loop
- **File**: `commands/test-loop.md`
- **Purpose**: Human-in-the-loop testing workflow with 3 approval gates
- **User-Invocable**: Yes (`/test-loop [options] [path]`)
- **Invokes**: test-loop-orchestrator (default) OR team-orchestration (`--use-teams`)
- **Invoked By**: User

### /test-generate
- **File**: `commands/test-generate.md`
- **Purpose**: Fully automated test generation with no approval gates
- **User-Invocable**: Yes (`/test-generate [options] [path]`)
- **Invokes**: analyze-agent, write-agent, execute-agent, validate-agent, fix-agent (sequential) OR team-orchestration (`--use-teams`)
- **Invoked By**: User

### /test-resume
- **File**: `commands/test-resume.md`
- **Purpose**: Resume interrupted test-loop workflow from saved state
- **User-Invocable**: Yes (`/test-resume`)
- **Invokes**: test-loop-orchestrator, state-management, project-detection
- **Invoked By**: User

### /team-run
- **File**: `commands/team-run.md`
- **Purpose**: Execute agent team definitions with CLI overrides
- **User-Invocable**: Yes (`/team-run [team-name] [options]`)
- **Invokes**: team-orchestration
- **Invoked By**: User

### /feedback
- **File**: `commands/feedback.md`
- **Purpose**: Submit feedback, bug reports, feature requests via GitHub CLI
- **User-Invocable**: Yes (`/feedback [options]`)
- **Invokes**: GitHub CLI (external)
- **Invoked By**: User

---

## Subagent (1)

### test-loop-orchestrator
- **File**: `subagents/test-loop-orchestrator.md`
- **Purpose**: 7-phase sequential orchestrator with approval gates and state persistence
- **Invokes**: model-selection, project-detection, test-location-detection, framework-detection, analyze-agent, write-agent, execute-agent, validate-agent, fix-agent, state-management, linting, build-integration
- **Invoked By**: /test-loop, /test-resume
- **Degree**: 14 (highest tied with team-orchestration)

---

## Agents (5)

### analyze-agent
- **File**: `agents/analyze-agent.md`
- **Purpose**: Identify testing needs, detect frameworks, assess complexity, prioritize targets
- **Default Model**: Sonnet
- **Invokes**: framework-detection
- **Invoked By**: /test-analyze, /test-loop, /test-generate, test-loop-orchestrator, team-orchestration

### write-agent
- **File**: `agents/write-agent.md`
- **Purpose**: Generate test code across 7 languages
- **Default Model**: Sonnet
- **Invokes**: test-location-detection, test-generation, templates, redundancy-detection, helper-extraction, build-integration, linting, framework-detection
- **Invoked By**: /test-loop, /test-generate, test-loop-orchestrator, team-orchestration
- **Note**: Most skill-dependent agent (~8 skill loads)

### execute-agent
- **File**: `agents/execute-agent.md`
- **Purpose**: Run test suites and parse results with smart test selection
- **Default Model**: Sonnet
- **Invokes**: result-parsing, framework-detection
- **Invoked By**: /test-loop, /test-generate, test-loop-orchestrator, team-orchestration, fix-agent (re-run)

### validate-agent
- **File**: `agents/validate-agent.md`
- **Purpose**: Root cause analysis on failures; categorize as test/source/environment bugs
- **Default Model**: Sonnet (Opus recommended)
- **Invokes**: result-parsing, state-management
- **Invoked By**: /test-loop, /test-generate, test-loop-orchestrator, team-orchestration

### fix-agent
- **File**: `agents/fix-agent.md`
- **Purpose**: Auto-fix Category 1 test bugs (5 subcategories, max 3 iterations)
- **Default Model**: Sonnet (Opus recommended)
- **Invokes**: execute-agent (re-run after fixes)
- **Invoked By**: /test-loop, test-loop-orchestrator, team-orchestration

---

## Skills -- Testing (6)

### framework-detection
- **File**: `skills/framework-detection/SKILL.md`
- **Purpose**: Detect test frameworks via weighted multi-evidence scoring (config:10, deps:8, build:10-15, imports:2-3, code:3-5)
- **In-Degree**: 6 (highest)
- **Invoked By**: analyze-agent, write-agent, execute-agent, test-loop-orchestrator, test-generation, /test-analyze

### test-generation
- **File**: `skills/test-generation/SKILL.md`
- **Purpose**: Test generation patterns, principles, anti-patterns (8 core principles including AAA)
- **Invokes**: framework-detection, result-parsing, templates
- **Invoked By**: write-agent

### redundancy-detection
- **File**: `skills/redundancy-detection/SKILL.md`
- **Purpose**: Prevent duplicate test scenarios via 17 equivalence classes (30-50% blocking rate)
- **Invoked By**: write-agent

### result-parsing
- **File**: `skills/result-parsing/SKILL.md`
- **Purpose**: Parse test framework output using factory pattern (11+ framework-specific parsers)
- **Invoked By**: execute-agent, validate-agent, test-generation

### templates
- **File**: `skills/templates/SKILL.md`
- **Purpose**: Framework-specific test code templates (16 templates across 7 languages)
- **Invoked By**: write-agent, test-generation

### helper-extraction
- **File**: `skills/helper-extraction/SKILL.md`
- **Purpose**: Extract repeated test helpers into shared modules (threshold: 2+ files OR 10+ lines)
- **Invoked By**: write-agent

---

## Skills -- Build & Integration (3)

### build-integration
- **File**: `skills/build-integration/SKILL.md`
- **Purpose**: Configure test dependencies in Maven/CMake/.NET/Go build systems
- **Invoked By**: write-agent, test-loop-orchestrator

### linting
- **File**: `skills/linting/SKILL.md`
- **Purpose**: Run linters/formatters (black, prettier, eslint, spotless, dotnet format, gofmt, clang-format) with auto-fix
- **Invoked By**: test-loop-orchestrator, write-agent

### test-location-detection
- **File**: `skills/test-location-detection/SKILL.md`
- **Purpose**: Detect correct test file locations; validate against forbidden paths
- **Invokes**: project-detection
- **Invoked By**: write-agent, test-loop-orchestrator

---

## Skills -- Orchestration (7)

### team-orchestration
- **File**: `skills/team-orchestration/SKILL.md`
- **Purpose**: Coordinator entry point for team execution (7-phase workflow)
- **Invokes**: team-loader, resource-manager, approval-gate-handler, agent-lifecycle-manager, result-aggregator, telemetry, Task tool (agents)
- **Invoked By**: /team-run, /test-loop (--use-teams), /test-generate (--use-teams)
- **Degree**: 14 (highest tied with test-loop-orchestrator)

### team-loader
- **File**: `skills/team-orchestration/team-loader.md`
- **Purpose**: Load/validate team YAML definitions with DFS cycle detection
- **Invoked By**: team-orchestration

### resource-manager
- **File**: `skills/team-orchestration/resource-manager.md`
- **Purpose**: Enforce limits (5 agents/team, 5 concurrent teams, depth<=3), FIFO queuing
- **Invokes**: agent-lifecycle-manager, telemetry
- **Invoked By**: team-orchestration

### agent-lifecycle-manager
- **File**: `skills/team-orchestration/agent-lifecycle-manager.md`
- **Purpose**: Track agent state transitions (spawned -> running -> completed/failed)
- **Invokes**: telemetry
- **Invoked By**: team-orchestration, resource-manager

### approval-gate-handler
- **File**: `skills/team-orchestration/approval-gate-handler.md`
- **Purpose**: Before/after approval gates with approve/reject/modify (max 3 iterations)
- **Invokes**: telemetry
- **Invoked By**: team-orchestration

### result-aggregator
- **File**: `skills/team-orchestration/result-aggregator.md`
- **Purpose**: Combine outputs from parallel agents, handle partial failures, deduplicate files
- **Invoked By**: team-orchestration

### telemetry
- **File**: `skills/telemetry/SKILL.md`
- **Purpose**: Non-blocking structured event logging (5 event types, opt-in via DANTE_TELEMETRY=1)
- **In-Degree**: 5
- **Invoked By**: team-orchestration, resource-manager, approval-gate-handler, agent-lifecycle-manager

---

## Skills -- Utility (4)

### project-detection
- **File**: `skills/project-detection/SKILL.md`
- **Purpose**: Find project root by walking directory tree for markers (max depth 10)
- **In-Degree**: 5
- **Invoked By**: test-loop-orchestrator, write-agent, state-management, test-location-detection, /test-resume

### state-management
- **File**: `skills/state-management/SKILL.md`
- **Purpose**: Workflow state persistence via markdown + YAML at {project_root}/.claude/.test-loop-state.md
- **Invokes**: project-detection
- **Invoked By**: test-loop-orchestrator, /test-resume, validate-agent

### model-selection
- **File**: `skills/model-selection/SKILL.md`
- **Purpose**: Resolve Claude model per agent (4-level precedence: CLI > env > config > defaults)
- **Invoked By**: test-loop-orchestrator, /test-loop, /test-generate, /test-analyze

### plugin-standards
- **File**: `skills/plugin-standards/SKILL.md`
- **Purpose**: Development standards documentation for plugin contributors
- **In-Degree**: 0 (ORPHANED -- never invoked)
- **Out-Degree**: 0
- **Note**: Should be moved to docs/ directory

---

## Graph Statistics

| Metric | Value |
|--------|-------|
| Total nodes | 33 |
| Total directed edges | 62 |
| Graph type | DAG (zero cycles) |
| Max depth | 7 |
| Leaf nodes (out-degree 0) | 14 (42%) |
| Entry points (commands) | 6 |
| Orphaned nodes | 1 (plugin-standards) |
| Union reachability | 32/33 (96.97%) |
