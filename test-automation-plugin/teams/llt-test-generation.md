---
# ===========================================================================
# LLT Test Generation Implementation Team
# ===========================================================================
# Coordinates parallel implementation of LowLevelTests test generation
# feature across 15 tasks organized into 3 phases
#
# Location: teams/llt-test-generation.md
# Invoked via: /team-run llt-test-generation
# Spec: .sdd/specs/2026-02-17-llt-test-generation.md
# Plan: .sdd/plans/2026-02-17-llt-test-generation-plan.md
# Tasks: .sdd/tasks/2026-02-17-llt-test-generation-tasks.md
# ===========================================================================

name: llt-test-generation

coordinator: teams/llt-test-generation-coordinator.md

# Allow up to 4 parallel agents for template creation and parallel tasks
max_agents: 4

version: "1.0.0"

# Implementation phase may take time - set generous timeout
timeout_minutes: 60

depth_limit: 3

approval_gates:
  before_execution: true
  after_completion: true
  disabled: false

retry_config:
  max_retries: 3
  backoff_seconds: [1, 2, 4]

# Continue on non-critical failures to maximize progress
failure_handling: continue

token_budget: null

telemetry_enabled: true

# ---------------------------------------------------------------------------
# AGENT COMPOSITION
# Organized by phase with parallel execution where dependencies allow
# ---------------------------------------------------------------------------

agents:
  # Phase 1: Core Templates (can run in parallel)
  - name: task-001-basic-fixture-template
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies: []
    max_instances: 1

  - name: task-002-async-template
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies: []
    max_instances: 1

  - name: task-003-plugin-lifecycle-template
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies: []
    max_instances: 1

  - name: task-004-mock-template
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies: []
    max_instances: 1

  # Phase 1: Supporting infrastructure (after templates)
  - name: task-005-module-scaffolding
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies:
      - task-001-basic-fixture-template
      - task-002-async-template
      - task-003-plugin-lifecycle-template
      - task-004-mock-template
    max_instances: 1

  - name: task-006-variable-substitution
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-005-module-scaffolding
    max_instances: 1

  # Phase 2: Framework Integration (sequential dependencies)
  - name: task-007-framework-detection
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-006-variable-substitution
    max_instances: 1

  - name: task-008-pattern-detection
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-007-framework-detection
    max_instances: 1

  # Phase 2: Generators (parallel after pattern detection)
  - name: task-009-test-file-generator
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-008-pattern-detection
    max_instances: 1

  - name: task-010-module-generator
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies:
      - task-008-pattern-detection
    max_instances: 1

  # Phase 2: Integration (after generators)
  - name: task-011-workflow-integration
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-009-test-file-generator
      - task-010-module-generator
    max_instances: 1

  # Phase 3: Metadata and CLI (parallel where appropriate)
  - name: task-012-metadata-generation
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies:
      - task-011-workflow-integration
    max_instances: 1

  - name: task-013-cli-command
    type: agents/sdd-implementation-agent.md
    critical: true
    dependencies:
      - task-011-workflow-integration
    max_instances: 1

  - name: task-014-compilation-database
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies:
      - task-011-workflow-integration
    max_instances: 1

  - name: task-015-ast-extraction
    type: agents/sdd-implementation-agent.md
    critical: false
    dependencies:
      - task-014-compilation-database
    max_instances: 1

dependencies:
  # Explicit phase boundaries for clarity
  # Phase 1 → Phase 2
  - from: task-006-variable-substitution
    to: task-007-framework-detection
    type: sequential

  # Phase 2 → Phase 3
  - from: task-011-workflow-integration
    to: task-012-metadata-generation
    type: sequential
  - from: task-011-workflow-integration
    to: task-013-cli-command
    type: sequential
  - from: task-011-workflow-integration
    to: task-014-compilation-database
    type: sequential
---

# LLT Test Generation Implementation Team

This team coordinates the implementation of the LowLevelTests test generation
feature across 15 tasks organized into 3 phases:

## Phase 1: Core Templates (Week 1)
Creates the 4 core templates (Basic/Fixture, Async, Plugin/Lifecycle, Mock)
and supporting infrastructure for variable substitution and module scaffolding.

**Parallel Execution**: Template agents run in parallel (up to 4 concurrent)

## Phase 2: Framework Integration (Week 2)
Implements framework detection, pattern matching for template selection,
and generators for test files and module scaffolding.

**Mixed Execution**: Framework detection → Pattern detection → Generators (parallel) → Integration

## Phase 3: Metadata & CLI (Week 3)
Adds metadata-driven test generation, CLI commands, and clang compilation
database integration for accurate method extraction.

**Parallel Execution**: Metadata, CLI, and compilation database agents run in parallel

## Success Criteria
- All 15 tasks completed with passing acceptance criteria
- Generated code compiles without errors (95%+ success rate)
- Tests pass for all implemented features
- Integration with existing llt-find/llt-build workflow verified
