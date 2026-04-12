---
name: result-aggregator
description: Combine outputs from parallel agents, handle partial failures, merge file lists, and generate aggregated reports with success/failure metrics.
user-invocable: false
---

# Result Aggregator Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Purpose**: Aggregate outputs from multiple parallel agents with failure handling and structured reporting

**Used By**: Team Orchestration SKILL, all team coordinators

---

## Overview

The Result Aggregator Skill combines outputs from multiple parallel agents into a single unified result. It handles partial failures gracefully (continuing with successful outputs while marking failures), merges diverse output types (file lists, metrics, warnings), preserves individual agent metadata, and generates comprehensive summary reports.

This skill is critical for:
- **Robustness**: Partial failures don't invalidate successful agent outputs
- **Observability**: Clear summary of team execution (success rates, failure reasons)
- **Completeness**: All agent outputs are preserved, not lost due to one failure
- **Extensibility**: Custom aggregation logic per team type

### Key Principle

Aggregation must be **fault-tolerant** - partial failures should result in partial success, not total failure. Always preserve successful outputs and provide clear failure attribution.

---

## Skill Interface

### Input

```yaml
agent_outputs: list              # List of agent output objects (mix of successful and failed)
team_type: string                # Team type for custom aggregation logic (e.g., "testing-parallel", "plugin-architecture")
aggregation_config: dict         # Optional custom aggregation rules per team
```

**Agent Output Structure**:
```yaml
agent_id: string                 # Unique agent identifier
agent_type: string               # Agent type (e.g., "write-agent", "analyze-agent")
status: string                   # "completed" or "failed"
output: object | null            # Agent-specific output (null if failed)
metadata:
  duration_seconds: float        # Execution time
  model_used: string             # Model name (opus, sonnet, haiku)
  spawned_at: timestamp          # ISO 8601 UTC
  completed_at: timestamp        # ISO 8601 UTC
  retry_count: integer           # Number of retries attempted
failure_reason: string | null    # Error message if failed
```

### Output

```yaml
aggregated_result:
  total_agents: integer          # Total agents in team
  successful: integer            # Successfully completed agents
  failed: integer                # Failed agents

  # Success outputs (list of all successful agent outputs)
  outputs: list                  # All successful agent outputs with metadata

  # Failure tracking
  failures: list                 # List of failed agents with reasons

  # Merged artifacts (team-specific)
  merged_files: list             # Deduplicated file list from all agents
  merged_metrics: object         # Aggregated metrics (tests_generated, coverage, etc.)
  merged_warnings: list          # All warnings from all agents

  # Execution summary
  summary:
    total_duration_seconds: float        # Total elapsed time for team
    agent_durations: dict                # {agent_id: duration} for all agents
    success_rate: float                  # successful / total_agents (0.0 to 1.0)
    failure_reasons: dict                # {reason: count} - grouped failure reasons
    models_used: dict                    # {model: count} - usage breakdown
    parallel_speedup: float | null       # Estimated speedup vs sequential (if calculable)
```

---

## Aggregation Algorithm

### Step 1: Categorize Agent Outputs

```python
def categorize_outputs(agent_outputs: list) -> dict:
    """
    Separate successful and failed agent outputs.

    Args:
        agent_outputs: List of agent output objects

    Returns:
        dict with 'successful' and 'failed' lists
    """
    successful = []
    failed = []

    for output in agent_outputs:
        if output['status'] == 'completed' and output['output'] is not None:
            successful.append(output)
        else:
            failed.append(output)

    return {
        'successful': successful,
        'failed': failed,
        'total': len(agent_outputs)
    }
```

**Example**:
```python
# Input: 5 agent outputs (3 successful, 2 failed)
agent_outputs = [
    {
        'agent_id': 'write-agent-1',
        'status': 'completed',
        'output': {'tests_generated': 5, 'files': ['test_user.py']},
        'metadata': {'duration_seconds': 28.5, 'model_used': 'sonnet'}
    },
    {
        'agent_id': 'write-agent-2',
        'status': 'failed',
        'output': None,
        'metadata': {'duration_seconds': 120.0, 'model_used': 'sonnet'},
        'failure_reason': 'Timeout after 120 seconds'
    },
    # ... more agents
]

# Output
{
    'successful': [write-agent-1, write-agent-3, write-agent-5],
    'failed': [write-agent-2, write-agent-4],
    'total': 5
}
```

---

### Step 2: Merge File Lists

```python
def merge_file_lists(successful_outputs: list) -> list:
    """
    Deduplicate and merge file lists from all successful agents.

    Args:
        successful_outputs: List of successful agent outputs

    Returns:
        Sorted list of unique file paths
    """
    all_files = set()

    for output in successful_outputs:
        agent_output = output.get('output', {})

        # Handle different file field names (files, tests_generated, documents, etc.)
        file_fields = ['files', 'tests_generated', 'documents', 'artifacts', 'generated_files']

        for field in file_fields:
            if field in agent_output:
                files = agent_output[field]

                # Handle both string and list formats
                if isinstance(files, str):
                    all_files.add(files)
                elif isinstance(files, list):
                    all_files.update(files)

    # Sort for consistent output
    return sorted(list(all_files))
```

**Example**:
```python
# Input: 3 agents with overlapping files
successful_outputs = [
    {'output': {'files': ['test_user.py', 'test_auth.py']}},
    {'output': {'files': ['test_calculator.py']}},
    {'output': {'tests_generated': ['test_user.py', 'test_validator.py']}}  # Duplicate test_user.py
]

# Output (deduplicated and sorted)
[
    'test_auth.py',
    'test_calculator.py',
    'test_user.py',       # Deduplicated
    'test_validator.py'
]
```

---

### Step 3: Aggregate Metrics

```python
def aggregate_metrics(successful_outputs: list, team_type: str) -> dict:
    """
    Aggregate numeric metrics from all successful agents.

    Args:
        successful_outputs: List of successful agent outputs
        team_type: Team type for custom aggregation rules

    Returns:
        dict with aggregated metrics
    """
    metrics = {
        'tests_generated': 0,
        'tests_passed': 0,
        'tests_failed': 0,
        'coverage_percent': None,
        'warnings_count': 0,
        'lines_of_code': 0
    }

    # Summable metrics (add across all agents)
    summable_fields = ['tests_generated', 'tests_passed', 'tests_failed', 'warnings_count', 'lines_of_code']

    # Averaged metrics (weighted by agent contribution)
    averaged_fields = ['coverage_percent']

    coverage_values = []

    for output in successful_outputs:
        agent_output = output.get('output', {})

        # Sum metrics
        for field in summable_fields:
            if field in agent_output and isinstance(agent_output[field], (int, float)):
                metrics[field] += agent_output[field]

        # Collect values for averaging
        if 'coverage_percent' in agent_output and agent_output['coverage_percent'] is not None:
            coverage_values.append(agent_output['coverage_percent'])

    # Calculate average coverage (if any agents reported it)
    if coverage_values:
        metrics['coverage_percent'] = sum(coverage_values) / len(coverage_values)

    # Team-specific metrics
    if team_type == 'testing-parallel':
        metrics['total_test_files'] = len([o for o in successful_outputs if o.get('output', {}).get('files')])
    elif team_type == 'documentation':
        metrics['total_documents'] = len([o for o in successful_outputs if o.get('output', {}).get('documents')])
    elif team_type == 'plugin-architecture':
        metrics['sdd_specs_generated'] = len([o for o in successful_outputs if 'spec' in str(o.get('output', {}))])

    # Remove zero/null metrics for clean output
    return {k: v for k, v in metrics.items() if v is not None and v != 0}
```

**Example**:
```python
# Input: 3 write-agents with different test counts
successful_outputs = [
    {'output': {'tests_generated': 5, 'coverage_percent': 85.0}},
    {'output': {'tests_generated': 3, 'coverage_percent': 90.0}},
    {'output': {'tests_generated': 7, 'coverage_percent': 80.0}}
]

# Output
{
    'tests_generated': 15,       # 5 + 3 + 7
    'coverage_percent': 85.0     # (85 + 90 + 80) / 3
}
```

---

### Step 4: Merge Warnings

```python
def merge_warnings(agent_outputs: list) -> list:
    """
    Collect all warnings from all agents (successful and failed).

    Args:
        agent_outputs: List of all agent outputs

    Returns:
        List of warning objects with agent attribution
    """
    all_warnings = []

    for output in agent_outputs:
        agent_id = output.get('agent_id', 'unknown')
        agent_output = output.get('output', {})

        # Extract warnings from various fields
        warnings_fields = ['warnings', 'warning', 'notices', 'issues']

        for field in warnings_fields:
            if field in agent_output:
                warnings = agent_output[field]

                # Handle both string and list formats
                if isinstance(warnings, str):
                    all_warnings.append({
                        'agent_id': agent_id,
                        'message': warnings
                    })
                elif isinstance(warnings, list):
                    for warning in warnings:
                        if isinstance(warning, str):
                            all_warnings.append({
                                'agent_id': agent_id,
                                'message': warning
                            })
                        elif isinstance(warning, dict):
                            warning['agent_id'] = agent_id
                            all_warnings.append(warning)

    return all_warnings
```

**Example**:
```python
# Input: Agents with various warning formats
agent_outputs = [
    {
        'agent_id': 'write-agent-1',
        'output': {'warnings': ['Missing type hints in function foo', 'Unused import: typing']}
    },
    {
        'agent_id': 'write-agent-2',
        'output': {'warnings': 'Deprecated pytest fixture usage'}
    }
]

# Output
[
    {'agent_id': 'write-agent-1', 'message': 'Missing type hints in function foo'},
    {'agent_id': 'write-agent-1', 'message': 'Unused import: typing'},
    {'agent_id': 'write-agent-2', 'message': 'Deprecated pytest fixture usage'}
]
```

---

### Step 5: Build Failure Summary

```python
def build_failure_summary(failed_outputs: list) -> dict:
    """
    Analyze failures and group by reason.

    Args:
        failed_outputs: List of failed agent outputs

    Returns:
        dict with failure analysis
    """
    failures = []
    failure_reasons = {}

    for output in failed_outputs:
        agent_id = output.get('agent_id', 'unknown')
        failure_reason = output.get('failure_reason', 'Unknown error')
        retry_count = output.get('metadata', {}).get('retry_count', 0)

        failures.append({
            'agent_id': agent_id,
            'reason': failure_reason,
            'retry_count': retry_count
        })

        # Group by reason for summary
        if failure_reason in failure_reasons:
            failure_reasons[failure_reason] += 1
        else:
            failure_reasons[failure_reason] = 1

    return {
        'failures': failures,
        'failure_reasons': failure_reasons
    }
```

**Example**:
```python
# Input: 2 failed agents
failed_outputs = [
    {
        'agent_id': 'write-agent-2',
        'failure_reason': 'Timeout after 120 seconds',
        'metadata': {'retry_count': 3}
    },
    {
        'agent_id': 'write-agent-4',
        'failure_reason': 'Timeout after 120 seconds',
        'metadata': {'retry_count': 3}
    }
]

# Output
{
    'failures': [
        {'agent_id': 'write-agent-2', 'reason': 'Timeout after 120 seconds', 'retry_count': 3},
        {'agent_id': 'write-agent-4', 'reason': 'Timeout after 120 seconds', 'retry_count': 3}
    ],
    'failure_reasons': {
        'Timeout after 120 seconds': 2
    }
}
```

---

### Step 6: Calculate Execution Metrics

```python
def calculate_execution_metrics(agent_outputs: list, team_start_time: timestamp, team_end_time: timestamp) -> dict:
    """
    Calculate timing and performance metrics.

    Args:
        agent_outputs: List of all agent outputs
        team_start_time: When team execution started
        team_end_time: When team execution completed

    Returns:
        dict with execution metrics
    """
    total_duration = (team_end_time - team_start_time).total_seconds()
    agent_durations = {}
    models_used = {}

    # Collect per-agent durations and model usage
    for output in agent_outputs:
        agent_id = output.get('agent_id', 'unknown')
        metadata = output.get('metadata', {})

        duration = metadata.get('duration_seconds', 0)
        agent_durations[agent_id] = duration

        model = metadata.get('model_used', 'unknown')
        if model in models_used:
            models_used[model] += 1
        else:
            models_used[model] = 1

    # Estimate parallel speedup
    # Speedup = (sum of agent durations) / (team wall-clock duration)
    # This assumes agents ran in parallel; if sequential, speedup = 1.0
    sum_agent_durations = sum(agent_durations.values())
    parallel_speedup = None
    if total_duration > 0:
        parallel_speedup = sum_agent_durations / total_duration

    return {
        'total_duration_seconds': total_duration,
        'agent_durations': agent_durations,
        'models_used': models_used,
        'parallel_speedup': parallel_speedup
    }
```

**Example**:
```python
# Input: 3 agents ran in parallel, total team time 30s
agent_outputs = [
    {'agent_id': 'write-agent-1', 'metadata': {'duration_seconds': 28.5, 'model_used': 'sonnet'}},
    {'agent_id': 'write-agent-2', 'metadata': {'duration_seconds': 25.0, 'model_used': 'sonnet'}},
    {'agent_id': 'write-agent-3', 'metadata': {'duration_seconds': 30.0, 'model_used': 'opus'}}
]
team_start = datetime(2026, 2, 13, 14, 30, 0)
team_end = datetime(2026, 2, 13, 14, 30, 30)  # 30 seconds elapsed

# Output
{
    'total_duration_seconds': 30.0,
    'agent_durations': {
        'write-agent-1': 28.5,
        'write-agent-2': 25.0,
        'write-agent-3': 30.0
    },
    'models_used': {
        'sonnet': 2,
        'opus': 1
    },
    'parallel_speedup': 2.78  # (28.5 + 25.0 + 30.0) / 30.0 = 2.78x speedup
}
```

---

## Complete Aggregation Workflow

```python
def aggregate_results(
    agent_outputs: list,
    team_type: str,
    team_start_time: timestamp,
    team_end_time: timestamp,
    aggregation_config: dict = None
) -> dict:
    """
    Complete workflow to aggregate results from parallel agents.

    Args:
        agent_outputs: List of agent output objects (mix of successful and failed)
        team_type: Team type for custom aggregation logic
        team_start_time: When team execution started
        team_end_time: When team execution completed
        aggregation_config: Optional custom aggregation rules

    Returns:
        Aggregated result with all metrics, outputs, and failure tracking
    """
    # Step 1: Categorize outputs
    categorized = categorize_outputs(agent_outputs)
    successful = categorized['successful']
    failed = categorized['failed']
    total = categorized['total']

    # Step 2: Merge file lists
    merged_files = merge_file_lists(successful)

    # Step 3: Aggregate metrics
    merged_metrics = aggregate_metrics(successful, team_type)

    # Step 4: Merge warnings
    merged_warnings = merge_warnings(agent_outputs)

    # Step 5: Build failure summary
    failure_summary = build_failure_summary(failed)

    # Step 6: Calculate execution metrics
    execution_metrics = calculate_execution_metrics(agent_outputs, team_start_time, team_end_time)

    # Step 7: Calculate success rate
    success_rate = len(successful) / total if total > 0 else 0.0

    # Build final aggregated result
    aggregated_result = {
        'total_agents': total,
        'successful': len(successful),
        'failed': len(failed),

        # Success outputs
        'outputs': successful,

        # Failure tracking
        'failures': failure_summary['failures'],

        # Merged artifacts
        'merged_files': merged_files,
        'merged_metrics': merged_metrics,
        'merged_warnings': merged_warnings,

        # Execution summary
        'summary': {
            'total_duration_seconds': execution_metrics['total_duration_seconds'],
            'agent_durations': execution_metrics['agent_durations'],
            'success_rate': success_rate,
            'failure_reasons': failure_summary['failure_reasons'],
            'models_used': execution_metrics['models_used'],
            'parallel_speedup': execution_metrics['parallel_speedup']
        }
    }

    # Apply custom aggregation logic if provided
    if aggregation_config:
        aggregated_result = apply_custom_aggregation(aggregated_result, aggregation_config, team_type)

    return aggregated_result
```

---

## Custom Aggregation Logic

### Extensibility Pattern

Teams can provide custom aggregation logic via `aggregation_config`:

```yaml
# In team definition frontmatter
aggregation_config:
  merge_strategy: "union"        # or "intersection", "first_wins", "last_wins"
  deduplicate_files: true        # Remove duplicate files
  include_failed_outputs: false  # Include partial outputs from failed agents
  custom_metrics:
    - name: "total_functions_analyzed"
      operation: "sum"
      field: "functions_analyzed"
    - name: "average_complexity"
      operation: "average"
      field: "cyclomatic_complexity"
```

### Implementation

```python
def apply_custom_aggregation(result: dict, config: dict, team_type: str) -> dict:
    """
    Apply custom aggregation logic per team configuration.

    Args:
        result: Base aggregated result
        config: Custom aggregation config from team definition
        team_type: Team type

    Returns:
        Modified aggregated result
    """
    # Handle merge strategy
    merge_strategy = config.get('merge_strategy', 'union')

    if merge_strategy == 'intersection':
        # Only include files present in ALL agent outputs (rare)
        result['merged_files'] = intersect_file_lists(result['outputs'])
    elif merge_strategy == 'first_wins':
        # Use only first successful agent's files
        if result['outputs']:
            result['merged_files'] = result['outputs'][0].get('output', {}).get('files', [])

    # Handle custom metrics
    if 'custom_metrics' in config:
        for metric_config in config['custom_metrics']:
            metric_name = metric_config['name']
            operation = metric_config['operation']
            field = metric_config['field']

            values = []
            for output in result['outputs']:
                agent_output = output.get('output', {})
                if field in agent_output:
                    values.append(agent_output[field])

            if values:
                if operation == 'sum':
                    result['merged_metrics'][metric_name] = sum(values)
                elif operation == 'average':
                    result['merged_metrics'][metric_name] = sum(values) / len(values)
                elif operation == 'max':
                    result['merged_metrics'][metric_name] = max(values)
                elif operation == 'min':
                    result['merged_metrics'][metric_name] = min(values)

    # Include failed outputs if requested (partial results)
    if config.get('include_failed_outputs', False):
        result['partial_outputs_from_failed'] = []
        for output in result['failures']:
            if output.get('output') is not None:
                result['partial_outputs_from_failed'].append(output)

    return result
```

---

## Team-Specific Aggregation Examples

### Testing Team (REQ-F-34)

```python
def aggregate_testing_team_results(agent_outputs: list) -> dict:
    """
    Custom aggregation for testing-parallel team.

    Merges:
    - tests_generated: Sum across all write-agents
    - test_files: Deduplicated file list
    - framework_detected: Should be same across all agents (validate consistency)
    """
    result = aggregate_results(agent_outputs, 'testing-parallel', ...)

    # Validate framework consistency (all agents should detect same framework)
    frameworks = set()
    for output in result['outputs']:
        framework = output.get('output', {}).get('framework')
        if framework:
            frameworks.add(framework)

    if len(frameworks) > 1:
        result['merged_warnings'].append({
            'agent_id': 'coordinator',
            'message': f"Inconsistent test frameworks detected: {frameworks}"
        })

    return result
```

### Plugin Architecture Team (REQ-F-33)

```python
def aggregate_plugin_architecture_results(agent_outputs: list) -> dict:
    """
    Custom aggregation for plugin-architecture team.

    Merges:
    - sdd_specs: List of generated spec files
    - implementation_files: List of generated skill/agent files
    - charon_failures_analyzed: Count of Charon test failures addressed
    """
    result = aggregate_results(agent_outputs, 'plugin-architecture', ...)

    # Extract SDD artifacts
    sdd_specs = []
    implementation_files = []

    for output in result['outputs']:
        agent_output = output.get('output', {})

        if 'sdd_spec' in agent_output:
            sdd_specs.append(agent_output['sdd_spec'])
        if 'implementation_files' in agent_output:
            implementation_files.extend(agent_output['implementation_files'])

    result['merged_artifacts'] = {
        'sdd_specs': sdd_specs,
        'implementation_files': implementation_files
    }

    return result
```

### Documentation Team (REQ-F-35)

```python
def aggregate_documentation_results(agent_outputs: list) -> dict:
    """
    Custom aggregation for documentation team.

    Merges:
    - documents: List of generated documentation files
    - examples: List of code examples
    - diagrams: List of generated diagrams/visualizations
    """
    result = aggregate_results(agent_outputs, 'documentation', ...)

    # Categorize by document type
    result['merged_artifacts'] = {
        'guides': [],
        'api_docs': [],
        'examples': [],
        'diagrams': []
    }

    for output in result['outputs']:
        agent_output = output.get('output', {})
        doc_type = agent_output.get('document_type', 'unknown')
        docs = agent_output.get('documents', [])

        if doc_type in result['merged_artifacts']:
            result['merged_artifacts'][doc_type].extend(docs)

    return result
```

### Debug/Diagnosis Team (REQ-F-36)

```python
def aggregate_debug_diagnosis_results(agent_outputs: list) -> dict:
    """
    Custom aggregation for debug-diagnosis team.

    Merges:
    - error_reports: List of analyzed errors
    - root_causes: List of identified root causes
    - fix_specs: List of generated fix specifications
    """
    result = aggregate_results(agent_outputs, 'debug-diagnosis', ...)

    # Deduplicate root causes (multiple agents may find same root cause)
    all_root_causes = []
    for output in result['outputs']:
        agent_output = output.get('output', {})
        root_causes = agent_output.get('root_causes', [])
        all_root_causes.extend(root_causes)

    # Simple deduplication by description
    unique_root_causes = []
    seen_descriptions = set()
    for cause in all_root_causes:
        description = cause.get('description', '')
        if description not in seen_descriptions:
            unique_root_causes.append(cause)
            seen_descriptions.add(description)

    result['merged_artifacts'] = {
        'unique_root_causes': unique_root_causes
    }

    return result
```

---

## Partial Failure Handling

### Scenario: 3 of 5 agents succeed

```python
# Input: 5 agents, 3 successful, 2 failed
agent_outputs = [
    {
        'agent_id': 'write-agent-1',
        'status': 'completed',
        'output': {'tests_generated': 5, 'files': ['test_user.py']},
        'metadata': {'duration_seconds': 28.5, 'model_used': 'sonnet'}
    },
    {
        'agent_id': 'write-agent-2',
        'status': 'failed',
        'output': None,
        'metadata': {'duration_seconds': 120.0, 'model_used': 'sonnet', 'retry_count': 3},
        'failure_reason': 'Timeout after 120 seconds'
    },
    {
        'agent_id': 'write-agent-3',
        'status': 'completed',
        'output': {'tests_generated': 3, 'files': ['test_calculator.py']},
        'metadata': {'duration_seconds': 25.0, 'model_used': 'sonnet'}
    },
    {
        'agent_id': 'write-agent-4',
        'status': 'failed',
        'output': None,
        'metadata': {'duration_seconds': 15.0, 'model_used': 'sonnet', 'retry_count': 2},
        'failure_reason': 'Import error: module numpy not found'
    },
    {
        'agent_id': 'write-agent-5',
        'status': 'completed',
        'output': {'tests_generated': 7, 'files': ['test_validator.py']},
        'metadata': {'duration_seconds': 30.0, 'model_used': 'opus'}
    }
]

# Output: Partial success result
{
    'total_agents': 5,
    'successful': 3,
    'failed': 2,

    'outputs': [
        # write-agent-1, write-agent-3, write-agent-5 outputs preserved
    ],

    'failures': [
        {'agent_id': 'write-agent-2', 'reason': 'Timeout after 120 seconds', 'retry_count': 3},
        {'agent_id': 'write-agent-4', 'reason': 'Import error: module numpy not found', 'retry_count': 2}
    ],

    'merged_files': [
        'test_calculator.py',
        'test_user.py',
        'test_validator.py'
    ],

    'merged_metrics': {
        'tests_generated': 15  # 5 + 3 + 7 (only successful agents)
    },

    'summary': {
        'success_rate': 0.6,  # 3/5 = 60%
        'failure_reasons': {
            'Timeout after 120 seconds': 1,
            'Import error: module numpy not found': 1
        },
        'models_used': {
            'sonnet': 4,
            'opus': 1
        }
    }
}
```

**User-Facing Message**:
```
Testing Team: Partial Success (3 of 5 agents succeeded)

Successful Agents: 3
  - write-agent-1: 5 tests generated (test_user.py)
  - write-agent-3: 3 tests generated (test_calculator.py)
  - write-agent-5: 7 tests generated (test_validator.py)

Failed Agents: 2
  - write-agent-2: Timeout after 120 seconds (3 retries)
  - write-agent-4: Import error: module numpy not found (2 retries)

Summary:
  - Total tests generated: 15
  - Success rate: 60%
  - Execution time: 120 seconds
  - Parallel speedup: 2.1x

Next Steps:
  - Review failed agents and address issues
  - Consider re-running failed batches individually
  - Check telemetry log for detailed failure information
```

---

## Preserving Agent Metadata

All successful agent outputs retain full metadata:

```yaml
outputs:
  - agent_id: write-agent-1
    agent_type: agents/write-agent.md
    status: completed
    output:
      tests_generated: 5
      files: ['test_user.py']
      framework: pytest
    metadata:
      duration_seconds: 28.5
      model_used: sonnet
      spawned_at: 2026-02-13T14:30:01.123Z
      completed_at: 2026-02-13T14:30:29.623Z
      retry_count: 0
      batch_id: 1
      assigned_targets: ['src/user_service.py', 'src/auth/login.py']
```

This allows coordinators to:
- Track which agent generated which files
- Calculate per-agent performance metrics
- Correlate outputs with specific batches or targets
- Debug failures by comparing successful vs failed agent metadata

---

## Usage in Coordinators

```markdown
# In teams/testing-parallel-coordinator.md

## Phase 4: Result Aggregation

1. Read this skill: skills/team-orchestration/result-aggregator.md
2. Collect all agent outputs (successful and failed)
3. Call aggregate_results(agent_outputs, 'testing-parallel', team_start_time, team_end_time)
4. Check aggregated_result.success_rate:
   - If 1.0 (100%): Full success, proceed to next phase
   - If 0.5-0.99 (partial): Log warning, present partial results to user
   - If 0.0 (total failure): Abort team execution
5. Pass merged_files to next phase (execute-agent)
6. Display summary to user via approval gate (if enabled)
```

**Example Coordinator Usage**:
```python
# In coordinator
agent_outputs = await_all_agents(agent_ids)  # Wait for all agents to complete

# Aggregate results
aggregated = aggregate_results(
    agent_outputs=agent_outputs,
    team_type='testing-parallel',
    team_start_time=team_start_time,
    team_end_time=current_timestamp(),
    aggregation_config=team_definition.get('aggregation_config')
)

# Handle partial failure
if aggregated['failed'] > 0:
    log_telemetry('coordination', coordinator_id, 'partial_failure', {
        'successful': aggregated['successful'],
        'failed': aggregated['failed'],
        'failure_reasons': aggregated['summary']['failure_reasons']
    })

    # Decide whether to continue or abort based on team config
    failure_handling = team_definition['failure_handling']
    if failure_handling == 'abort':
        raise Exception(f"Team execution aborted: {aggregated['failed']} agents failed")
    # else continue with partial results

# Use merged results
merged_files = aggregated['merged_files']
merged_metrics = aggregated['merged_metrics']

# Pass to next phase
execute_agent_output = spawn_execute_agent({
    'test_files': merged_files,
    'framework': merged_metrics.get('framework'),
    'total_tests': merged_metrics.get('tests_generated')
})
```

---

## Testing Checklist

For TASK-005 acceptance:

- [ ] Aggregates outputs from multiple agents (3+ agents)
- [ ] Handles partial failures (2 of 5 agents fail, continues with 3)
- [ ] Marks failed agents with failure_reason in output
- [ ] Includes successful outputs in aggregated result
- [ ] Generates summary with total_agents, successful, failed counts
- [ ] Lists failure_reasons with count per reason
- [ ] Merges file lists (deduplicates, sorts)
- [ ] Merges metrics (tests_generated, coverage_percent, etc.)
- [ ] Merges warnings from all agents with agent attribution
- [ ] Preserves individual agent metadata (duration, model, timestamps)
- [ ] Returns structured result matching output schema
- [ ] Calculates success_rate (successful / total_agents)
- [ ] Calculates parallel_speedup (sum durations / wall-clock time)
- [ ] Supports custom aggregation logic via aggregation_config
- [ ] Handles empty agent_outputs list (edge case)
- [ ] Handles all agents failed (0% success rate)
- [ ] Handles all agents succeeded (100% success rate)
- [ ] Handles mixed output formats (files vs tests_generated vs documents)
- [ ] Groups failure_reasons for summary
- [ ] Tracks models_used breakdown

---

## Example Complete Aggregation

```python
# Input: Testing team with 3 write-agents, 1 failed
agent_outputs = [
    {
        'agent_id': 'write-agent-1',
        'agent_type': 'agents/write-agent.md',
        'status': 'completed',
        'output': {
            'tests_generated': 5,
            'files': ['test_user.py'],
            'framework': 'pytest',
            'coverage_percent': 85.0,
            'warnings': ['Missing type hints in function foo']
        },
        'metadata': {
            'duration_seconds': 28.5,
            'model_used': 'sonnet',
            'spawned_at': '2026-02-13T14:30:01.123Z',
            'completed_at': '2026-02-13T14:30:29.623Z',
            'retry_count': 0
        },
        'failure_reason': None
    },
    {
        'agent_id': 'write-agent-2',
        'agent_type': 'agents/write-agent.md',
        'status': 'failed',
        'output': None,
        'metadata': {
            'duration_seconds': 120.0,
            'model_used': 'sonnet',
            'spawned_at': '2026-02-13T14:30:01.234Z',
            'completed_at': '2026-02-13T14:32:01.234Z',
            'retry_count': 3
        },
        'failure_reason': 'Timeout after 120 seconds'
    },
    {
        'agent_id': 'write-agent-3',
        'agent_type': 'agents/write-agent.md',
        'status': 'completed',
        'output': {
            'tests_generated': 7,
            'files': ['test_calculator.py', 'test_validator.py'],
            'framework': 'pytest',
            'coverage_percent': 90.0,
            'warnings': []
        },
        'metadata': {
            'duration_seconds': 30.0,
            'model_used': 'opus',
            'spawned_at': '2026-02-13T14:30:01.345Z',
            'completed_at': '2026-02-13T14:30:31.345Z',
            'retry_count': 0
        },
        'failure_reason': None
    }
]

team_start_time = datetime(2026, 2, 13, 14, 30, 0)
team_end_time = datetime(2026, 2, 13, 14, 32, 10)  # 130 seconds total

# Call aggregation
result = aggregate_results(agent_outputs, 'testing-parallel', team_start_time, team_end_time)

# Output
{
    'total_agents': 3,
    'successful': 2,
    'failed': 1,

    'outputs': [
        # write-agent-1 and write-agent-3 outputs (full metadata preserved)
    ],

    'failures': [
        {
            'agent_id': 'write-agent-2',
            'reason': 'Timeout after 120 seconds',
            'retry_count': 3
        }
    ],

    'merged_files': [
        'test_calculator.py',
        'test_user.py',
        'test_validator.py'
    ],

    'merged_metrics': {
        'tests_generated': 12,      # 5 + 7
        'coverage_percent': 87.5    # (85.0 + 90.0) / 2
    },

    'merged_warnings': [
        {
            'agent_id': 'write-agent-1',
            'message': 'Missing type hints in function foo'
        }
    ],

    'summary': {
        'total_duration_seconds': 130.0,
        'agent_durations': {
            'write-agent-1': 28.5,
            'write-agent-2': 120.0,
            'write-agent-3': 30.0
        },
        'success_rate': 0.67,       # 2/3 = 67%
        'failure_reasons': {
            'Timeout after 120 seconds': 1
        },
        'models_used': {
            'sonnet': 2,
            'opus': 1
        },
        'parallel_speedup': 1.37    # (28.5 + 120.0 + 30.0) / 130.0 = 1.37x
    }
}
```

---

## References

- Plan: `.sdd/plans/2026-02-12-agent-team-orchestration-plan.md` (Result Aggregation)
- Spec: `.sdd/specs/2026-02-12-agent-team-orchestration.md` (REQ-F-2, REQ-F-6)
- Pattern: `skills/team-orchestration/team-loader.md` (Markdown skill structure)

---

**Last Updated**: 2026-02-13
**Status**: Implementation (TASK-005)
