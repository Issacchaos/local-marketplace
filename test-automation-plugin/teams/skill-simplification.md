---
# ===========================================================================
# Skill Simplification Team (All-in-One)
# ===========================================================================
# Reviews skill scripts, proposes simplifications, and implements approved
# changes. This is the "one stop shop" for simplifying skills by moving
# script logic into SKILL.md algorithms for agentic execution.
#
# Location: teams/skill-simplification.md
# Invoked via: /team-run skill-simplification --skill <skill-name>
# ===========================================================================

name: skill-simplification

coordinator: teams/skill-simplification-coordinator.md

# Adjust based on skill complexity (max concurrent agents)
max_agents: 10

version: "1.0.0"

# End-to-end simplification may take time
timeout_minutes: 120

depth_limit: 3

approval_gates:
  before_execution: true   # Approve review plan
  after_completion: false  # No approval after done (implementation has its own gate)
  disabled: false

retry_config:
  max_retries: 2
  backoff_seconds: [1, 2]

# Continue on non-critical failures
failure_handling: continue

token_budget: null

telemetry_enabled: true

# ---------------------------------------------------------------------------
# AGENT COMPOSITION
# Coordinator orchestrates two-phase workflow with approval gate:
#   Phase 1: Review (discover scripts, analyze, propose simplifications)
#   Phase 2: Implementation (move logic to SKILL.md, test, validate)
# ---------------------------------------------------------------------------

agents:
  # Agents are spawned dynamically by coordinator in two phases:
  #
  # PHASE 1: REVIEW
  # - Discover scripts in skills/<skill-name>/scripts/
  # - Spawn script-simplifier-agent for each script
  # - Analyze dependencies and LOC reduction potential
  # - Generate implementation plan with priorities
  # - USER APPROVAL GATE
  #
  # PHASE 2: IMPLEMENTATION
  # - Execute approved plan in phases (high→medium→low priority)
  # - Move logic to SKILL.md algorithms
  # - Update SKILL.md with new sections
  # - Run tests to verify no regressions
  # - Generate summary report

dependencies:
  # Phase 2 implementation depends on Phase 1 approval
  # Dependencies within each phase are discovered dynamically
---

# Skill Simplification Team

This team provides end-to-end skill simplification:

## Workflow

### Phase 1: Review & Analysis
1. Discover all Python scripts in `skills/<skill-name>/scripts/`
2. Analyze each script for simplification potential
3. Identify dependencies between scripts
4. Generate prioritized implementation plan
5. **→ USER APPROVAL GATE ←**

### Phase 2: Implementation
6. Execute high-priority moves (independent scripts)
7. Update SKILL.md with algorithms
8. Execute medium/low priority moves (dependent scripts)
9. Run validation tests
10. Generate summary report

## Review Criteria

### Move to SKILL.md When:
- Logic is deterministic and describable in pseudocode
- Pattern matching, decision trees, template rendering
- File generation (can use Write tool)
- Business logic that agents can execute on-the-fly

### Keep as Script When:
- Complex system integration (external tools, compilers)
- Binary parsing (libclang AST, protobuf)
- Performance-critical with caching requirements
- Requires specialized libraries unavailable to agents

## Success Criteria
- Target LOC reduction achieved (typically 40-70%)
- All existing tests pass
- No regressions in functionality
- SKILL.md algorithms are clear and executable by agents

## Usage

```bash
# Simplify a skill in current project
/team-run skill-simplification --skill <skill-name>

# Simplify a skill in a different directory
/team-run skill-simplification --skill <skill-name> --path /path/to/project

# Example: Simplify a skill in sh-scripts-and-tools
/team-run skill-simplification --skill framework-detection --path ~/sh-scripts-and-tools
```

The coordinator will:
1. Discover scripts in {base_path}/skills/<skill-name>/scripts/
2. Present review findings and implementation plan
3. Ask for your approval
4. Execute the approved plan
5. Report final results
