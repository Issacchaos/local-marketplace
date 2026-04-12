# Test Plan Generator

Generates a structured, risk-driven test plan from design documentation. The output follows a standardized format used by QA teams to plan testing for features, systems, and initiatives.

## Usage

```
/test-planner path/to/design-doc.pdf
/test-planner path/to/design-doc.md
/test-planner path/to/docs-folder/
```

## Arguments

- `$ARGUMENTS` - Required: path to one or more design documents.
  - Supported formats: `.md`, `.txt`, `.pdf`, `.html`
  - If a directory is provided, read all supported documents within it as combined input.
- `--code-path <path>` - Optional: path to existing source code for refactors or enhancements.
  - When provided, cross-reference the existing implementation during risk analysis to identify regression risks, untested integration points, and behavioral changes.
  - Read key source files to understand current architecture before building the risk model.

## Process

### Step 1: Load and Parse Documentation

1. Extract the document path from `$ARGUMENTS`.
2. **Validate the path (SECURITY CRITICAL)**:
   - Remove null bytes (prevent injection)
   - Check path length (max 4096 characters)
   - Resolve to absolute path
   - Verify path is within workspace boundaries (prevent directory traversal)
   - Check path exists
   - If validation fails, display error and STOP
3. Read the document(s):
   - Single file: Read using the Read tool.
   - Directory: Glob for supported file types and read each.
4. For large documents, use the Read tool's `offset` and `limit` parameters to read in chunks of 500 lines. Summarize key points from each chunk before reading the next. For very large document sets (multiple files totaling thousands of lines), prioritize reading executive summaries, architecture sections, and requirements sections first.

### Step 2: Ask the User for Context

Before generating the plan, ask the user the following questions using the AskUserQuestion tool. **Each question must be asked as its own separate AskUserQuestion prompt.** Wait for the user's answer to each question before asking the next one. Do NOT combine multiple questions into a single prompt.

**Question 1: Feature Type** — "What best describes this feature?"
- Use AskUserQuestion with options: "Seasonal game feature", "Infrastructure / system", "UX/UI flow", "Content / asset change"
- This determines the default test approach split (see Step 6).
- Wait for answer before proceeding.

**Question 2: Team Name** — "What is the team or product name that owns this feature?"
- Use AskUserQuestion with free text input.
- Used in the Overview and headers.
- Wait for answer before proceeding.

**Question 3: Target Release / Milestone** — "What is the target release or milestone? (e.g., Season 34, FN35, Phase 1 November 2024)"
- Use AskUserQuestion with free text input.
- Used in Cadence and Entry/Exit Criteria sections.
- Wait for answer before proceeding.

**Question 4: Known Constraints** — "Are there any known constraints you want called out? (e.g., dependency on another team, platform limitations, late delivery risk)"
- Use AskUserQuestion with options: "No known constraints", and an option for the user to provide their own.
- Optional. Feeds directly into Risks & Constraints.
- Wait for answer before proceeding to Step 3.

### Step 3: Build Understanding of the Design

Before generating test plan sections, build a mental model:
- **Purpose**: What problem does this feature/system solve? What are the user stories?
- **Architecture**: What are the key components, systems, or workstreams?
- **Dependencies**: What external teams, systems, or deliverables does this depend on?
- **Scope Boundaries**: What is explicitly included vs. excluded?
- **Platforms / Environments**: What platforms, devices, or configurations are relevant?
- **Phases / Milestones**: Is delivery phased? What ships when?

**If `--code-path` was provided**: Read key source files at the given path to understand the current implementation. Identify existing behavior, integration points, and areas of complexity that the design document proposes to change. This informs Step 4 with concrete regression risks and untested interaction points that would not be visible from the design document alone.

### Step 4: Identify Risks

Identify risks using the **"3 Whys" methodology**:

For each potential risk, ask "why is it a risk?" three times to drill down to the core impact.

**Example:**
> Surface observation: "This feature is coming in late."
> 1. Why is that a risk? → "Because it means we have less time to test it."
> 2. Why is THAT a risk? → "Because it means we won't catch all critical bugs/blockers before go-live."
> 3. Why is THAT a risk? → "Because escaped defects could hurt player retention and lower engagement with a major release beat."
>
> **Fully articulated risk:** "This feature is coming in late and QA won't have enough time to adequately test it, which means that we are at risk of lowered player retention due to escaped critical defects impacting their engagement with one of our major beats."

Apply this methodology to every risk. Do not write surface-level risks. Every entry in the Risks & Constraints table must contain the fully drilled-down risk statement.

**Risk sources to examine:**
- Late or unstable dependencies from other teams
- Platform or environment limitations
- Code/content changes with knock-on effects
- Iterating/unstable upstream systems that block testing
- New technology or unproven approaches
- Missing or incomplete design specs
- Cross-team coordination requirements
- Data migration or persistence compatibility
- Anything the user provided in the "Known Constraints" answer
- If `--code-path` was provided: regression risks from behavioral changes, untested integration points in existing code, and complexity hotspots identified from the source

**IMPORTANT — Mitigation column boundaries:** The third column of the Risks & Constraints table ("How the other items in this test plan will mitigate the risk") must ONLY reference:
- **Scope decisions** — which in-scope testing areas directly address this risk
- **Test approach allocation** — how the % split (Checklist/Exploratory/PerfMem/Playtest) accounts for this risk
- **Cadence choices** — which test activities and their frequency target this risk

Do NOT include entry criteria, exit criteria, or edge cases in the mitigation column. Those belong in their own dedicated sections. If a risk naturally leads to an entry criterion or edge case, that content goes in the Entry/Exit Criteria or Edge Cases table — not here.

### Step 5: Define Scope from Risks

Scope is **risk-driven**. Items are placed in-scope specifically to mitigate identified risks. Items are placed out-of-scope as deliberate trade-offs.

For each in-scope item, you should be able to trace it back to a risk it mitigates. If a testing area doesn't mitigate any identified risk, question whether it belongs in scope.

### Step 6: Determine Test Approach Split

Assign percentage allocations across four testing types. Use the feature type from Step 2 as a starting baseline, then adjust based on the specific risks and design characteristics.

**Baselines by feature type:**

| Feature Type | Checklist | Exploratory | PerfMem | Playtest |
|---|---|---|---|---|
| Seasonal game feature | 40% | 40% | 10% | 10% |
| Infrastructure / system | 40% | 30% | 10% | 20% |
| UX/UI flow | 30% | 50% | 0% | 20% |
| Content / asset change | 50% | 30% | 10% | 10% |

**Adjustment guidelines:**
- If the design mentions performance targets, install sizes, or memory budgets → increase PerfMem allocation.
- If the feature is player-facing with subjective quality concerns → increase Playtest allocation.
- If the system has many defined states and transitions → increase Checklist allocation.
- If the design is ambiguous or underspecified → increase Exploratory allocation.
- If multiple test approach areas apply, split the plan into sub-areas with individual percentage allocations per area.

### Step 7: Assemble the Test Plan

Write the complete test plan to disk as a markdown file alongside the source document:
- **File name**: `{feature-name}-test-plan.md`
- **Location**: Same directory as the source document.
- Derive `{feature-name}` from the document title or the feature name identified in Step 3, sanitized to lowercase with hyphens.

## Output Template

The generated test plan **must** follow this structure. All sections are required. Tables must use the exact column structure shown.

````markdown
# [Team/Product] - [Feature Name]

## Overview

[2-4 sentence description of the feature/system being tested. What is it, what does it change, and why does it matter? Written from the QA perspective — what are we focused on validating?]

[Reference links to design docs, JIRA epics, Slack channels, or other relevant documentation provided by the user or found in the source documents.]

## Scope

*You should be defining your test scope based on the risks you have identified for your feature. You might place some items as out of scope as a trade-off to bring other things in-scope in order to mitigate certain risks. Use testing trade-offs to inform scope.*

### In Scope

[Each entry is a high-level testing area in bold, followed by bullet points of specific items within that area.]

- **[Area of testing]**
  - [Specific item]
  - [Specific item]
- **[Area of testing]**
  - [Specific item]
  - [Specific item]

### Out of Scope

[Each entry is an exclusion with a brief rationale explaining *why* it is excluded (different team owns it, lower risk, not changing, etc.).]

- **[Excluded area]** — [Rationale for exclusion]
- **[Excluded area]** — [Rationale for exclusion]

## Risks & Constraints

*This should not be a full risk analysis (do that in reports). This should list major risks to the feature/system and the mitigation should tie into how you create this test plan — it is why you are writing the test plan.*

### [Short Risk Title]

**Risk**: [Fully articulated risk statement using the 3-whys methodology. Not a surface observation — the drilled-down core impact.]

**Likelihood**: [Low/Medium/High] | **Severity**: [Low/Medium/High]

[Additional context on what it blocks or enables.]

**Mitigation**: [Reference ONLY scope decisions, test approach allocation (%), or cadence choices that mitigate this risk. Do NOT restate entry/exit criteria or edge cases here — those have their own sections.]

---

[Repeat for each risk. Use a horizontal rule (---) between risks for visual separation.]

## Edge Cases and Integration Testing

*List out edge cases for the feature and any other features/systems the feature may interact with that will require integration testing. Keep the edge case scenarios high level and avoid writing out detailed test cases here.*

| Edge Case / Integration | Expected Behavior |
|---|---|
| [System or integration point] | [What should happen — the expected correct behavior] |
| ... | ... |

## Test Approach

*Use the baselines table from Step 6 as a starting point, then adjust based on identified risks.*

| Checklist | Exploratory | PerfMem | Playtest |
|---|---|---|---|
| [X]% | [Y]% | [Z]% | [W]% |

[1-2 sentences justifying the chosen split based on the feature type and identified risks. If the plan covers multiple distinct areas, break down the split per area.]

## Cadence

*Your cadence for each activity depends on a number of factors unique to your team/feature, such as the speed of development, stability trends, responsible dev testing/check-ins, adherence to deadlines, and overall risk. The cadence may need to be re-adjusted later if some of these factors change.*

| Test Activity | Cadence |
|---|---|
| [Activity type, e.g., Smoketests] | [Frequency and conditions, e.g., Daily on Android, iOS] |
| [Golden Path Regression] | [e.g., At Hardlock, At Pencils Down] |
| [Targeted Regression / One-offs] | [e.g., Once at Hardlock, then as-needed] |
| [Playtests] | [e.g., Minimum 1 full playtest before Pencils Down] |
| [PerfMem captures] | [e.g., One-off A/B capture comparing before/after] |
| ... | ... |

## Entry / Exit Criteria

*Any criteria not met in either column at the time it is expected should be converted into a risk during risk reporting.*

| Entry Criteria | Exit Criteria |
|---|---|
| [What must be true before testing can begin — prerequisites, dependencies resolved, builds available, systems stable] | [What must be validated/achieved before testing is considered complete — smoke tests pass, regression clean, golden path validated, etc.] |
| ... | ... |

---

*Generated by test-planner skill. Review and validate with your team before finalizing.*
````

## Analysis Guidelines

- **Risk-driven scope**: Every in-scope item should trace back to a risk it mitigates. Do not pad scope with testing areas that don't address identified risks.
- **Use the 3 Whys**: Never write a surface-level risk like "this system is new." Always drill down three levels to the actual player/business impact.
- **Be specific to the design**: Reference specific systems, components, workstreams, and phases from the source document. Generic test plans are not useful.
- **Edge cases from integration points**: Look at where systems touch each other — data handoffs, state transitions, platform boundaries, install/uninstall flows, upgrade paths. These are where edge cases live.
- **Realistic cadence**: Tie cadence to the milestones and phases described in the design documentation. Don't invent milestones that aren't in the source material.
- **Entry/Exit should be verifiable**: Each criterion should be something that can be objectively checked (a build passes, a smoke test runs, a system is available) — not subjective assessments.
- **Don't write test cases**: The test plan defines *what* to test, *why*, and *when* — not the detailed step-by-step test cases. Keep edge cases and scope items high-level.
- **Flag gaps in the design**: If the design document is missing information you need to write a complete test plan section, note it explicitly and mark those areas as higher risk.
