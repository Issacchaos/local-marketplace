# Plugin Architecture Analysis - Coordinator

**Team**: plugin-architecture-analysis
**Version**: 1.0.0

---

## Coordinator Overview

This coordinator orchestrates a 4-agent research team that performs deep analysis
of the Dante plugin's architecture. The workflow is structured in 3 phases with
data flowing forward through agent dependencies.

---

## Phase 1: Skill Inventory Mapping

### Agent: skill-inventory-mapper

**Subagent Type**: `Explore`
**Model**: `sonnet`

**Task Prompt**:

```
You are the Skill Inventory Mapper for the Dante plugin architecture analysis.

Your job is to read EVERY skill, agent, command, and subagent definition in this
project and produce a comprehensive inventory catalog.

## Files to Read (ALL of these)

### Skills (15 directories, each with SKILL.md)
Read every file matching: skills/*/SKILL.md
Also read any sub-files referenced within each skill directory.

### Agents (5 agent definitions)
Read every file matching: agents/*.md

### Commands (6 command definitions)
Read every file matching: commands/*.md

### Subagents
Read every file matching: subagents/*.md

### Team Orchestration Sub-Skills
Read every file in: skills/team-orchestration/*.md

## Output Format

For EACH component, produce a structured entry:

### [Component Type]: [Name]
- **File**: [path]
- **Category**: [skill | agent | command | subagent | orchestration-sub-skill]
- **Purpose**: [1-2 sentence description]
- **User-Invocable**: [yes/no, and how]
- **Inputs**: [what it receives]
- **Outputs**: [what it produces]
- **Invokes** (outgoing edges): [list of other components this one calls/references]
- **Invoked By** (incoming edges): [list of components that call/reference this one]
- **Key Skills/Tools Used**: [Task tool, Bash, Read, specific skills, etc.]

## Important Notes
- Be EXHAUSTIVE - do not skip any component
- Pay special attention to cross-references between components (who calls whom)
- Note when skills reference other skills via `Skill()` calls or direct file reads
- Note when commands invoke skills
- Note when agents reference skills
- Note when the test-loop-orchestrator references agents and skills
- Capture the FULL dependency web, not just direct references

Produce your complete inventory as a structured report.
```

**Success Criteria**: Agent produces an entry for every component (minimum 30+ entries covering all skills, agents, commands, subagents).

---

## Phase 2a: Traversal Graph Building

### Agent: traversal-graph-builder

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Depends On**: skill-inventory-mapper output

**Task Prompt**:

```
You are the Traversal Graph Builder for the Dante plugin architecture analysis.

You have been given the complete skill inventory from Phase 1 (provided below).
Your job is to build a comprehensive directed graph of ALL invocation paths
through the Dante plugin.

## Input
{skill-inventory-mapper output}

## Your Tasks

### 1. Build the Invocation Graph
Using the inventory's "Invokes" and "Invoked By" fields, construct a directed
graph where:
- **Nodes** = every component (skill, agent, command, subagent)
- **Edges** = invocation relationships (A -> B means "A invokes/calls B")
- **Edge Labels** = type of invocation (skill call, Task tool spawn, file read, etc.)

### 2. Identify All Entry Points
List every user-facing entry point:
- Commands (/test-loop, /test-generate, /test-analyze, /test-resume, /team-run, /feedback)
- For each entry point, trace the COMPLETE execution path through all components

### 3. Trace Full Execution Paths
For each entry point, produce a complete trace like:
```
/test-loop
  -> test-loop-orchestrator (subagent)
    -> model-selection skill (resolve agent models)
    -> project-detection skill (find project root)
    -> framework-detection skill (detect test framework)
    -> analyze-agent (agent)
      -> framework-detection skill
      -> test-location-detection skill
    -> write-agent (agent)
      -> templates skill
      -> test-generation skill
      -> test-location-detection skill
      -> build-integration skill
    -> execute-agent (agent)
      -> result-parsing skill
    -> validate-agent (agent)
      -> result-parsing skill
    -> fix-agent (agent)
      -> linting skill
      -> helper-extraction skill
    -> state-management skill (save checkpoints)
```

### 4. Produce DOT Graph
Generate a DOT-format graph suitable for Graphviz visualization:
- Use different node shapes for different component types
  (box=command, diamond=subagent, ellipse=agent, rounded-box=skill)
- Use different edge colors for different invocation types
- Include a legend

### 5. Identify Cycles
Check if the graph contains any cycles (component A eventually calls back to A).
Report any cycles found.

## Output Format

Produce:
1. A table of all nodes with their type and degree (in-edges, out-edges)
2. Complete execution traces for every entry point
3. The DOT graph source code
4. Cycle analysis results
5. Statistics (total nodes, total edges, max depth, most-connected components)
```

**Success Criteria**: Complete DOT graph with all nodes and edges, plus execution traces for all 6 commands.

---

## Phase 2b: Redundancy Analysis

### Agent: redundancy-analyzer

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Depends On**: skill-inventory-mapper output
**Runs In Parallel With**: traversal-graph-builder

**Task Prompt**:

```
You are the Redundancy Analyzer for the Dante plugin architecture analysis.

You have been given the complete skill inventory from Phase 1 (provided below).
Your job is to identify overlapping, duplicative, or redundant functionality
across all components.

## Input
{skill-inventory-mapper output}

## Analysis Categories

### 1. Functional Overlap
Identify pairs or groups of skills that provide similar functionality:
- Do any two skills solve the same problem differently?
- Are there skills that could be merged without loss of functionality?
- Are there skills that partially duplicate each other's logic?

For each overlap found:
- **Components**: [list of overlapping components]
- **Overlap Description**: [what functionality overlaps]
- **Severity**: [High: fully duplicative | Medium: partial overlap | Low: minor similarity]
- **Recommendation**: [merge, deduplicate, or keep separate with justification]

### 2. Responsibility Boundaries
Analyze whether each skill has a clear, single responsibility:
- Are any skills doing too many things?
- Are responsibilities split across skills in confusing ways?
- Would the architecture benefit from different responsibility boundaries?

### 3. Naming Consistency
Check if component names accurately reflect their purpose:
- Are any names misleading?
- Do naming conventions follow a consistent pattern?
- Suggest improvements where names could be clearer

### 4. Dead or Orphaned Components
Identify components that appear to have no callers:
- Skills that are defined but never invoked
- Agent capabilities that are never used
- Commands that reference non-existent components

### 5. Architecture Efficiency
Assess the overall architecture:
- Is there unnecessary indirection (A calls B which just calls C)?
- Are there skills that are too granular (should be combined)?
- Are there skills that are too monolithic (should be split)?
- How well does the plugin follow the single-responsibility principle?

## Output Format

Produce a structured redundancy report with:
1. Executive summary (key findings in 3-5 bullets)
2. Detailed findings per category above
3. Prioritized recommendations (sorted by impact)
4. Architecture health score (1-10 with justification)
```

**Success Criteria**: Analysis covers all 5 categories with specific, actionable findings.

---

## Phase 3: White Paper Synthesis

### Agent: whitepaper-synthesizer

**Subagent Type**: `general-purpose`
**Model**: `opus`
**Depends On**: traversal-graph-builder output AND redundancy-analyzer output

**Task Prompt**:

```
You are the White Paper Synthesizer for the Dante plugin architecture analysis.

You have been given three inputs:
1. The complete skill inventory (from Phase 1)
2. The traversal graph with execution paths (from Phase 2a)
3. The redundancy analysis report (from Phase 2b)

Your job is to synthesize ALL findings into a comprehensive, well-structured
white paper that fully explains how the Dante plugin works.

## White Paper Structure

### Title
"Dante: Architecture of an AI-Native Test Generation Plugin"

### 1. Executive Summary (1 page)
- What is Dante?
- Key capabilities (automated test generation, multi-language support, agent orchestration)
- Architecture philosophy (coordinator-specialist pattern, skill-based composition)
- Key metrics (number of skills, agents, supported languages, etc.)

### 2. Architecture Overview (2-3 pages)
- High-level architecture diagram (describe in text + include DOT graph)
- The three-layer model: Commands -> Orchestrators -> Agents -> Skills
- Design principles (separation of concerns, single responsibility, composition over inheritance)
- How the plugin hooks into Claude Code's extension system

### 3. Component Catalog (3-4 pages)
- Commands: User entry points and their purposes
- Subagents: Orchestration logic (test-loop-orchestrator)
- Agents: The 5 specialist agents and their roles
- Skills: All 15 skills organized by category
  - Testing Skills (test-generation, templates, test-location-detection, framework-detection, result-parsing)
  - Build/Integration Skills (build-integration, linting, project-detection)
  - Orchestration Skills (team-orchestration/*, state-management, model-selection, telemetry)
  - Utility Skills (helper-extraction, redundancy-detection, plugin-standards)

### 4. Data Flow Analysis (2-3 pages)
- The test generation pipeline: analyze -> write -> execute -> validate -> fix
- How data flows between agents in the test loop
- The team orchestration pipeline: load -> approve -> spawn -> monitor -> aggregate -> report
- State management and checkpoint/resume flow

### 5. Invocation Graph (2 pages)
- Full traversal graph with all entry points
- The DOT graph visualization description
- Most-traversed paths (hot paths)
- Deepest execution chains

### 6. Cross-Cutting Concerns (1-2 pages)
- Model selection strategy (Opus vs Sonnet vs Haiku per agent)
- Telemetry and observability
- Error handling and retry logic
- Approval gates and user control

### 7. Redundancy & Improvement Analysis (2 pages)
- Summary of redundancy findings
- Overlapping skills analysis
- Architecture health assessment
- Prioritized recommendations for improvement

### 8. Conclusion (0.5 page)
- Summary of the plugin's architectural strengths
- Key areas for improvement
- Vision for future evolution

## Style Guidelines
- Write for a technical audience familiar with Claude Code but not with Dante internals
- Use precise technical language
- Include specific file paths and component names
- Reference the traversal graph and redundancy report findings
- Be objective - highlight both strengths and weaknesses
- Target approximately 15-20 pages total

## Output
Produce the complete white paper as a single well-formatted Markdown document.
```

**Success Criteria**: Complete white paper covering all 8 sections with specific references to findings from all prior agents.

---

## Coordinator Execution Logic

### Step 1: Spawn skill-inventory-mapper
- Use Task tool with subagent_type=Explore
- Wait for completion
- Store output as `inventory_result`

### Step 2: Spawn traversal-graph-builder and redundancy-analyzer in parallel
- Pass `inventory_result` into both agent prompts
- Use Task tool for both, launched in a single message
- Wait for both to complete
- Store outputs as `graph_result` and `redundancy_result`

### Step 3: Spawn whitepaper-synthesizer
- Pass all three results into the prompt
- Use Task tool with subagent_type=general-purpose, model=opus
- Wait for completion
- Store output as `whitepaper_result`

### Step 4: Write outputs to files
- Write inventory to `docs/architecture/skill-inventory.md`
- Write traversal graph DOT to `docs/architecture/dante-traversal-graph.dot`
- Write redundancy report to `docs/architecture/redundancy-report.md`
- Write white paper to `docs/architecture/dante-whitepaper.md`

### Step 5: Return aggregated results
- Report success/failure for each agent
- Provide file paths for all outputs
