# GitHub PR Management Skill

Custom Claude Code skill for managing GitHub pull request comments and review threads using GraphQL.

## Overview

This skill provides commands for:
- Posting comprehensive summary comments to PRs
- Querying review threads and their status
- Replying to specific review comments
- Resolving review threads individually or in batches

## Installation

This skill is already installed in your project at:
```
.claude/skills/gh-pr-manage/
```

## Usage

### Using the Skill in Claude Code

Invoke the skill with the `/gh-pr-manage` command:

```
/gh-pr-manage 754 query-threads
```

Available actions:
- `post-summary` - Post a comprehensive summary comment
- `query-threads` - List all review threads with IDs and status
- `reply [comment-id] [message]` - Reply to a specific comment
- `resolve [thread-id]` - Resolve a single thread
- `batch-resolve` - Resolve multiple threads

### Direct Command Execution

This skill uses **direct `gh` CLI commands** with no Python dependencies. All operations are implemented as agentic algorithms in SKILL.md that agents execute on-the-fly.

#### 1. Query Review Threads

```bash
# Query all threads and save to temp file
gh api graphql -f query='
query {
  repository(owner: "eos", name: "test-data-service") {
    pullRequest(number: 754) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 5) {
            nodes {
              id
              databaseId
              author { login }
              body
              createdAt
            }
          }
        }
      }
    }
  }
}
' > /tmp/pr-754-threads.json

# Display summary
TOTAL=$(jq '.data.repository.pullRequest.reviewThreads.nodes | length' /tmp/pr-754-threads.json)
RESOLVED=$(jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == true)] | length' /tmp/pr-754-threads.json)
echo "Total: $TOTAL, Resolved: $RESOLVED, Unresolved: $((TOTAL - RESOLVED))"

# Show unresolved threads
jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
  select(.isResolved == false) |
  "Thread ID: \(.id)\nFile: \(.path):\(.line)\nComment ID: \(.comments.nodes[0].databaseId)\nAuthor: \(.comments.nodes[0].author.login)\n"
' /tmp/pr-754-threads.json
```

Output:
```
Total: 20, Resolved: 18, Unresolved: 2

Thread ID: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4ODUwOnYy
File: src/modules/mcp/profile/mcp.profile.controller.ts:106
Comment ID: 739482
Author: mona-huang
```

#### 2. Reply to a Comment

```bash
gh api repos/eos/test-data-service/pulls/754/comments/739591/replies \
  --method POST \
  --field body="✅ Implemented with all tests passing!"
```

#### 3. Resolve a Thread

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy"}) {
    thread {
      id
      isResolved
    }
  }
}
'
```

#### 4. Batch Resolve Multiple Threads

```bash
# Loop over thread IDs
for THREAD_ID in \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy" \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTAyOnYy" \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTE2OnYy"
do
  echo "Resolving: $THREAD_ID"
  gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
      thread { id isResolved }
    }
  }
  '
done
```

#### 5. Post Summary Comment

```bash
# Option 1: From file
gh pr comment 754 --repo eos/test-data-service --body-file /tmp/pr-summary.md

# Option 2: Auto-generate summary
COMMITS=$(gh pr view 754 --repo eos/test-data-service --json commits --jq '.commits[-5:] | .[] | "- \(.messageHeadline)"')
DIFF_STATS=$(gh pr diff 754 --repo eos/test-data-service --stat | tail -1)

cat > /tmp/pr-754-auto-summary.md <<EOF
## 🎉 PR Summary

### 📝 Recent Commits
$COMMITS

### 📊 Changes Overview
\`\`\`
$DIFF_STATS
\`\`\`
EOF

gh pr comment 754 --repo eos/test-data-service --body-file /tmp/pr-754-auto-summary.md
```

### Algorithm-Based Execution

This skill uses **algorithm-based execution** - agents read SKILL.md and execute `gh` and `jq` commands directly using their Bash tool. All five algorithms are fully documented with:

- Step-by-step pseudocode
- Complete command syntax
- JSON parsing patterns
- Error handling guidance

No scripts are required. Agents execute commands on-the-fly following the documented algorithms.

## Complete Workflow Example

Here's a complete workflow for responding to all review comments on a PR:

### Step 1: Query All Threads

```bash
# Query and save to /tmp/pr-754-threads.json
gh api graphql -f query='...' > /tmp/pr-754-threads.json
```

### Step 2: Reply to Each Addressed Comment

For each comment you've addressed, post a contextual reply:

```bash
# Delete enhancement (Comment #739591)
gh api repos/eos/test-data-service/pulls/754/comments/739591/replies \
  --method POST \
  --field body="✅ Implemented! The delete endpoint now supports:
- \`?id={templateId}\` for specific template deletion
- \`?backupName={name}&templateVersion={version}\` for version-specific deletion
Added Joi validation. All 11 tests passing!"

# MMR endpoint (Comment #739881)
gh api repos/eos/test-data-service/pulls/754/comments/739881/replies \
  --method POST \
  --field body="✅ Added JSDoc documentation noting the 400 MethodRejection issue. Created ONQA-5052 to investigate."

# DeploymentId metadata (Comment #739899)
gh api repos/eos/test-data-service/pulls/754/comments/739899/replies \
  --method POST \
  --field body="✅ Added \`originalDeploymentId\` field to template metadata for traceability."
```

### Step 3: Resolve the Addressed Threads

Get the thread IDs from step 1, then resolve them:

```bash
# Batch resolve with error handling
for THREAD_ID in \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy" \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTAyOnYy" \
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTE2OnYy"
do
  gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
      thread { id isResolved }
    }
  }
  ' && echo "✅ $THREAD_ID" || echo "❌ $THREAD_ID"
done
```

### Step 4: Post Summary Comment

```bash
# Create summary file
cat > /tmp/pr-754-summary.md <<'EOF'
## 🎉 Implementation Complete - All Review Comments Addressed

### ✅ Changes Implemented

1. Delete Enhancement - Supports deletion by id, backupName, or version
2. MMR Endpoint Documentation - Added JSDoc with JIRA tracking
3. DeploymentId Metadata - Added originalDeploymentId field

### 🧪 Test Results
- takeSnapshot: 21/21 passed
- deleteMcpProfileTemplate: 11/11 passed

Ready for approval! 🚀
EOF

# Post summary
gh pr comment 754 --repo eos/test-data-service --body-file /tmp/pr-754-summary.md
```

## Templates

See `templates.md` for:
- Summary comment templates
- Reply message templates
- Output formatting templates

## Configuration

Default repository: `eos/test-data-service`

All commands support custom repositories via `--repo` flag:

```bash
# Query threads for different repo
gh api graphql --repo myorg/myrepo -f query='...'

# Reply to comment in different repo
gh api repos/myorg/myrepo/pulls/123/comments/456/replies --method POST --field body="Done!"

# Post comment to different repo
gh pr comment 123 --repo myorg/myrepo --body "message"
```

## Troubleshooting

### "Permission denied" Error

Ensure you have write access to the repository and are authenticated with `gh`:

```bash
gh auth status
```

### "Thread already resolved" Error

Query threads first to check current status before resolving.

### Invalid Thread ID Format

Thread IDs for GraphQL must start with `MDIz...` (not numeric comment IDs).
Comment IDs are numeric (like `739591`) and used for replies, not resolution.

### GraphQL UNKNOWN_CHAR Error

Use proper shell escaping in GraphQL queries:
```bash
# Correct - use single quotes and variable substitution
gh api graphql -f query='mutation { field: "'"$VAR"'" }'
```

## GraphQL vs REST API

- **Resolving threads:** Requires GraphQL (`gh api graphql`)
- **Replying to comments:** Uses REST API (`gh api repos/...`)
- **Posting new comments:** Uses CLI (`gh pr comment`)

## Related Documentation

- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills.md)

## Implementation Details

All skill operations are implemented as **algorithms in SKILL.md** that agents interpret and execute on-the-fly. No Python dependencies required. See SKILL.md for:
- Complete algorithm pseudocode
- Step-by-step execution procedures
- Example implementations with error handling
- Advanced usage patterns
