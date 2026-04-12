# Dante Plugin Redundancy Analysis Report

**Date**: February 2026
**Scope**: All 33 components (6 commands, 1 subagent, 5 agents, 20 skills, 1 external)

---

## Architecture Health Score: 7.5/10

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Component Separation | 9/10 | 25% | 2.25 |
| Code Reuse / DRY | 5/10 | 25% | 1.25 |
| Naming Consistency | 7/10 | 15% | 1.05 |
| Single Responsibility | 9/10 | 20% | 1.80 |
| Dead Code Risk | 7/10 | 15% | 1.05 |
| **Total** | | **100%** | **7.40 (rounded to 7.5)** |

---

## Executive Summary

1. **CRITICAL**: `team-orchestration` and `test-loop-orchestrator` are duplicate 7-phase orchestrators with ~500-800 lines of duplicated logic
2. **CRITICAL**: `/test-loop` and `/test-generate` have 90% overlapping implementation, differing only by approval gate configuration
3. **HIGH**: Framework detection ownership unclear between skill and analyze-agent
4. **MEDIUM**: Naming inconsistencies across skills (bare nouns vs compound descriptors)
5. **LOW**: Several potential shared utilities not yet extracted (process-runner, config-resolver)

---

## Detailed Findings

### P0 -- Critical

#### 1. Duplicate Orchestrators
- **Components**: `team-orchestration` (skill), `test-loop-orchestrator` (subagent)
- **Overlap**: Both implement 7-phase workflow coordination, agent spawning via Task tool, retry logic with identical [1,2,4]s backoff, model selection initialization, and state persistence
- **Severity**: High (fully duplicative core logic, ~500-800 lines)
- **Recommendation**: Create unified `orchestration-engine` skill with `mode` parameter (sequential/parallel)

#### 2. Near-Identical Commands
- **Components**: `/test-loop`, `/test-generate`
- **Overlap**: 90% shared implementation (argument parsing, security validation, model override handling, routing logic)
- **Severity**: High
- **Recommendation**: Extract shared workflow function, parameterize approval mode, keep both commands as thin wrappers

### P1 -- High Priority

#### 3. Framework Detection Ownership
- **Components**: `framework-detection` skill, `analyze-agent`
- **Overlap**: Both perform framework detection; unclear which is authoritative
- **Severity**: Medium
- **Recommendation**: Make skill the single source of truth; agent should only invoke it

#### 4. Result-Handling Name Confusion
- **Components**: `result-aggregator`, `result-parsing`
- **Overlap**: Similar names but completely different layers (agent outputs vs test framework output)
- **Severity**: Medium
- **Recommendation**: Rename to `agent-result-merger` and `test-output-parser`

#### 5. Orphaned Plugin Standards
- **Components**: `plugin-standards`
- **Issue**: Zero in-degree, zero out-degree. Never invoked programmatically
- **Severity**: Medium
- **Recommendation**: Move to `docs/` directory

### P2 -- Medium Priority

#### 6. Misleading test-generation Name
- **Recommendation**: Rename to `test-generation-patterns`

#### 7. Overly Granular team-loader
- **Recommendation**: Consider inlining into `team-orchestration`

#### 8. Inconsistent Naming Convention
- **Bare nouns**: `linting`, `templates`, `telemetry`
- **Compound**: `framework-detection`, `state-management`, `test-location-detection`
- **Recommendation**: Standardize on `{noun}-{action/type}` pattern

### P3 -- Low Priority

#### 9. Shared Path Utilities
- `project-detection` and `test-location-detection` share directory-walking logic

#### 10. Resource Manager Dual Concerns
- Limit enforcement + FIFO queue management could be separated

#### 11. No Shared Process Runner
- `execute-agent`, `linting`, `build-integration` all run subprocesses independently

#### 12. No Unified Config Resolver
- `model-selection`, `telemetry`, approval gate configuration all resolve settings independently

---

## Single Responsibility Compliance: 89%

17 of 19 executable skills pass SRP. Non-compliant:
- `resource-manager` (limits + queuing)
- `team-orchestration` (duplicates test-loop-orchestrator)

---

## Projected Improvement

| Fix Level | Health Score | Delta |
|-----------|-------------|-------|
| Current | 7.5 | -- |
| After P0 | 8.5 | +1.0 |
| After P0 + P1 | 9.0 | +0.5 |
| After all | 9.5 | +0.5 |
