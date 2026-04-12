# Example Parallel Team - Coordinator

**Team**: example-parallel
**Version**: 1.0.0

---

## Coordinator Overview

This coordinator manages a simple 2-phase workflow:
- Phase 1: Run task-alpha and task-beta in parallel
- Phase 2: Run task-gamma after both complete

---

## Phase 1: Parallel Tasks (task-alpha, task-beta)

### Agent: task-alpha

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are task-alpha in the example-parallel team.

Your job is to perform Task Alpha. This is a placeholder task for demonstration.

## Instructions

1. Report that you are running task-alpha
2. Perform any assigned work from the team definition
3. Return a structured result with:
   - status: "completed"
   - output: description of what was done
   - duration: approximate time taken
```

---

### Agent: task-beta

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are task-beta in the example-parallel team.

Your job is to perform Task Beta. This is a placeholder task for demonstration.

## Instructions

1. Report that you are running task-beta
2. Perform any assigned work from the team definition
3. Return a structured result with:
   - status: "completed"
   - output: description of what was done
   - duration: approximate time taken
```

---

## Phase 2: Sequential Task (task-gamma)

### Agent: task-gamma

**Subagent Type**: `general-purpose`
**Model**: `sonnet`

**Task Prompt**:

```
You are task-gamma in the example-parallel team.

Your job is to aggregate results from task-alpha and task-beta.

## Instructions

1. Review the outputs from task-alpha and task-beta
2. Combine their results into a unified summary
3. Return a structured result with:
   - status: "completed"
   - output: aggregated summary
   - duration: approximate time taken
```

---

## Result Aggregation

After all agents complete, produce a combined report:

```markdown
# Example Parallel Team - Results

## Phase 1 Results
- **task-alpha**: {status} ({duration}s)
- **task-beta**: {status} ({duration}s)

## Phase 2 Results
- **task-gamma**: {status} ({duration}s)

## Summary
- Total agents: 3
- Successful: {count}
- Failed: {count}
- Total duration: {duration}s
```
