---
name: gh-pr-manage
description: Query, reply to, and resolve GitHub PR review threads. Use when user asks to respond to PR comments, resolve review threads, check PR feedback, address reviewer concerns, or post PR summary comments. Supports batch operations and works with any GitHub repository. Requires --repo parameter.
argument-hint: --repo OWNER/REPO [pr-number] [--resolve-thread thread-id] [--query-threads] [--reply comment-id message]
allowed-tools: Bash(gh pr *), Bash(gh api *), Bash(jq *), Read, Write
---

# GitHub PR Management - Comments & Review Threads

Manage GitHub pull request comments and review threads using the GitHub CLI with GraphQL queries.

## When to Use This Skill

Use this skill whenever the user asks to:
- **Query review threads**: "What review comments are on PR 768?", "Show me unresolved threads", "Check PR feedback"
- **Reply to comments**: "Reply to comment 12345", "Respond to reviewer feedback", "Add a reply explaining the fix"
- **Resolve threads**: "Resolve thread XYZ", "Mark comments as resolved", "Resolve review feedback"
- **Batch operations**: "Resolve all addressed comments", "Resolve threads 1, 2, and 3", "Mark multiple threads resolved"
- **Post summaries**: "Post a PR summary", "Add implementation summary comment"
- **Address PR reviews**: "Respond to PR comments", "Address reviewer concerns", "Update PR with responses"

**Common user phrases that trigger this skill:**
- "resolve review thread(s)"
- "reply to PR comment"
- "check PR feedback"
- "respond to reviewer"
- "mark comments resolved"
- "address review comments"
- "post PR summary"

## Prerequisites

- **GitHub CLI (`gh`)**: Must be installed and authenticated
- **jq**: JSON processor for parsing API responses
- **Repository Access**: Write permissions to post comments and resolve threads
- **Network Access**: Ability to reach GitHub API endpoints

Verify setup:
```bash
gh auth status  # Check authentication
jq --version    # Verify jq is available
```

## Implementation Approach

This skill uses **direct `gh` CLI commands** with GraphQL API for all operations. Agents construct and execute commands on-the-fly following the algorithms below. No Python scripts required.

**All commands require repository configuration:**
- `--repo OWNER/REPO` - **Required parameter** specifying target repository

**Examples:**
```bash
gh api graphql --repo myorg/myrepo -f query='...'
gh pr comment 123 --repo myorg/myrepo --body "message"
```

## Available Actions

When invoked with `/gh-pr-manage [pr-number] [action]`, perform one of these actions:

### 1. Query Review Threads

Fetch all review threads with their IDs and resolved status.

**Usage:** `/gh-pr-manage 754 query-threads`

**Algorithm:**

```
Step 1: Construct GraphQL query
  - Template:
    query {
      repository(owner: "{owner}", name: "{repo}") {
        pullRequest(number: {pr}) {
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
  - Substitute: {owner}, {repo}, {pr}

Step 2: Execute query using gh CLI
  - Command: gh api graphql -f query='<query-string>'
  - Tool: Bash
  - Note: Use single quotes around query to avoid shell escaping issues

Step 3: Save results to temp file
  - Parse JSON output from gh CLI
  - Write to: /tmp/pr-{pr}-threads.json
  - Tool: Write

Step 4: Display summary
  - Parse saved JSON with jq or native parsing
  - Count total threads: .data.repository.pullRequest.reviewThreads.nodes | length
  - Count resolved: .data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == true) | length
  - Count unresolved: total - resolved
  - Format and display unresolved threads with:
    * Thread ID: .id
    * File:line: .path:.line
    * Comment ID: .comments.nodes[0].databaseId
    * Author: .comments.nodes[0].author.login
    * Body preview: .comments.nodes[0].body (first 60 chars)

Step 5: Display next steps
  - Show example commands for resolving/replying
```

**Example Implementation:**

```bash
# Step 1-2: Query threads
gh api graphql -f query='
query {
  repository(owner: "my-org", name: "test-data-service") {
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

# Step 4: Display summary
echo "Review Threads Summary"
echo "=================================================="
TOTAL=$(jq '.data.repository.pullRequest.reviewThreads.nodes | length' /tmp/pr-754-threads.json)
RESOLVED=$(jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == true)] | length' /tmp/pr-754-threads.json)
UNRESOLVED=$((TOTAL - RESOLVED))
echo "Total: $TOTAL"
echo "Resolved: $RESOLVED"
echo "Unresolved: $UNRESOLVED"

# Display unresolved threads
jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
  select(.isResolved == false) |
  "\nThread ID: \(.id)\nFile: \(.path):\(.line)\nComment ID: \(.comments.nodes[0].databaseId)\nAuthor: \(.comments.nodes[0].author.login)\nPreview: \(.comments.nodes[0].body[:60])...\n"
' /tmp/pr-754-threads.json
```

**Expected Output:**
```
Review Threads Summary
==================================================
Total: 2
Resolved: 0
Unresolved: 2

Thread ID: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy
File: src/modules/mcp/profile/mcp.profile.validation.ts:118
Comment ID: 739591
Author: mona-huang
Preview: Would be nice to add `id` as a query param...
```

---

### 2. Reply to Review Comment

Add a contextual reply to a specific review comment thread before resolving it.

**Usage:** `/gh-pr-manage 754 reply 739591 "✅ Implemented with tests"`

**Algorithm:**

```
Step 1: Validate inputs
  - PR number (numeric)
  - Comment database ID (numeric, from query_threads output)
  - Message text

Step 2: Construct REST API path
  - Path: repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies

Step 3: Execute POST request using gh CLI
  - Command: gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies --method POST --field body='{message}'
  - Tool: Bash
  - Note: Escape quotes in message if needed

Step 4: Parse response
  - Extract reply ID: .id
  - Extract reply URL: .html_url
  - Display success message with URL
```

**Example Implementation:**

```bash
# Variables
PR=754
COMMENT_ID=739591
MESSAGE="✅ Implemented! Added validation with tests."
OWNER="my-org"
REPO="test-data-service"

# Execute POST request
gh api repos/$OWNER/$REPO/pulls/$PR/comments/$COMMENT_ID/replies \
  --method POST \
  --field body="$MESSAGE" \
  > /tmp/reply-response.json

# Parse and display result
REPLY_ID=$(jq -r '.id' /tmp/reply-response.json)
REPLY_URL=$(jq -r '.html_url' /tmp/reply-response.json)

echo "✅ Successfully posted reply"
echo "Reply ID: $REPLY_ID"
echo "URL: $REPLY_URL"
```

**Expected Output:**
```
✅ Successfully posted reply
Reply ID: 739892
URL: https://github.example.com/my-org/test-data-service/pull/754#discussion_r739892
```

---

### 3. Resolve Review Thread

Resolve a review thread using its GraphQL ID.

**Usage:** `/gh-pr-manage 754 resolve MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy`

**Algorithm:**

```
Step 1: Validate inputs
  - PR number (numeric)
  - Thread GraphQL ID (starts with "MDIz...")

Step 2: Construct GraphQL mutation
  - Template:
    mutation {
      resolveReviewThread(input: {threadId: "{thread_id}"}) {
        thread {
          id
          isResolved
        }
      }
    }
  - Substitute: {thread_id}

Step 3: Execute mutation using gh CLI
  - Command: gh api graphql -f query='<mutation-string>'
  - Tool: Bash
  - Note: Use single quotes around mutation

Step 4: Verify success
  - Parse JSON response
  - Check: .data.resolveReviewThread.thread.isResolved == true
  - If true: Display success message with thread ID
  - If false or error: Display failure message with details
```

**Example Implementation:**

```bash
# Variables
PR=754
THREAD_ID="MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy"

# Execute mutation
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
    thread {
      id
      isResolved
    }
  }
}
' > /tmp/resolve-response.json

# Verify success
IS_RESOLVED=$(jq -r '.data.resolveReviewThread.thread.isResolved' /tmp/resolve-response.json)

if [ "$IS_RESOLVED" = "true" ]; then
  echo "✅ Successfully resolved thread: $THREAD_ID"
else
  echo "❌ Failed to resolve thread: $THREAD_ID"
  jq '.' /tmp/resolve-response.json
fi
```

**Expected Output:**
```
✅ Successfully resolved thread: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy
```

---

### 4. Batch Resolve Threads

Resolve multiple review threads at once by providing a list of thread IDs.

**Usage:** `/gh-pr-manage 754 batch-resolve`

**Algorithm:**

```
Input:
  - PR number
  - List of thread_ids (array or space-separated string)
  - continue_on_error flag (optional, boolean)

Step 1: Initialize counters
  - total = len(thread_ids)
  - success = 0
  - failed = 0
  - failed_threads = [] (array to track failures)

Step 2: Loop over thread_ids
  For each thread_id (with index i):
    Step 2.1: Display progress
      - Print: "[{i}/{total}] Resolving: {thread_id[:50]}... " (no newline)

    Step 2.2: Execute Algorithm 3 (Resolve Thread) for thread_id
      - Construct mutation
      - Execute gh api graphql
      - Parse response

    Step 2.3: Check result
      If successful (.data.resolveReviewThread.thread.isResolved == true):
        - Print: "✅"
        - Increment success counter
      Else:
        - Print: "❌"
        - Increment failed counter
        - Append to failed_threads: {thread_id, error, response}

    Step 2.4: Handle continue-on-error
      If failed > 0 and not continue_on_error:
        - Print: "\nStopping due to error. Use --continue-on-error to proceed."
        - Break loop

Step 3: Display summary
  - Print blank line
  - Print: "Resolution Summary"
  - Print: "=================================================="
  - Print: "Total: {total}"
  - Print: "Success: {success}"
  - Print: "Failed: {failed}"

  If failed_threads not empty:
    - Print blank line
    - Print: "Failed Threads:"
    - Print: "--------------------------------------------------"
    - For each failure:
      - Print: "\nThread: {thread_id}"
      - Print: "Error: {error}"
      - If response available: Print: "Response: {json_response}"

Step 4: Exit with appropriate code
  - If failed > 0: exit 1
  - Else: exit 0
```

**Example Implementation:**

```bash
# Variables
PR=754
THREAD_IDS=(
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy"
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTAyOnYy"
  "MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDIxMzU2OnYy"
)
CONTINUE_ON_ERROR=true

# Initialize counters
TOTAL=${#THREAD_IDS[@]}
SUCCESS=0
FAILED=0
FAILED_THREADS=()

echo "Resolving $TOTAL threads for PR #$PR"
echo

# Loop over threads
for i in "${!THREAD_IDS[@]}"; do
  THREAD_ID="${THREAD_IDS[$i]}"
  INDEX=$((i + 1))

  # Display progress
  PREVIEW="${THREAD_ID:0:50}"
  printf "[%d/%d] Resolving: %s... " "$INDEX" "$TOTAL" "$PREVIEW"

  # Execute mutation
  gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
      thread {
        id
        isResolved
      }
    }
  }
  ' > /tmp/resolve-$INDEX.json 2>&1

  # Check result
  IS_RESOLVED=$(jq -r '.data.resolveReviewThread.thread.isResolved // false' /tmp/resolve-$INDEX.json 2>/dev/null)

  if [ "$IS_RESOLVED" = "true" ]; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "❌"
    FAILED=$((FAILED + 1))
    FAILED_THREADS+=("$THREAD_ID")

    # Stop on first error if not continuing
    if [ "$CONTINUE_ON_ERROR" != "true" ]; then
      echo
      echo "Stopping due to error. Use --continue-on-error to proceed."
      break
    fi
  fi
done

# Display summary
echo
echo "Resolution Summary"
echo "=================================================="
echo "Total: $TOTAL"
echo "Success: $SUCCESS"
echo "Failed: $FAILED"

# Show failed threads
if [ ${#FAILED_THREADS[@]} -gt 0 ]; then
  echo
  echo "Failed Threads:"
  echo "--------------------------------------------------"
  for FAILED_ID in "${FAILED_THREADS[@]}"; do
    echo
    echo "Thread: $FAILED_ID"
    echo "Error: Command failed or thread already resolved"
  done
fi

# Exit with error if any failed
[ $FAILED -gt 0 ] && exit 1
exit 0
```

**Expected Output:**
```
Resolving 3 threads for PR #754

[1/3] Resolving: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy... ✅
[2/3] Resolving: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE5MTAyOnYy... ✅
[3/3] Resolving: MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDIxMzU2OnYy... ✅

Resolution Summary
==================================================
Total: 3
Success: 3
Failed: 0
```

---

### 5. Post Summary Comment

Post a comprehensive summary comment to the PR. If no content file is provided, generate one based on recent commits and changes.

**Usage:** `/gh-pr-manage 754 post-summary`

**Algorithm:**

```
Input:
  - PR number
  - Option A: file_path (path to summary markdown file)
  - Option B: message (direct text content)
  - Option C: auto (auto-generate from PR data)

Option A - Post from file:
  Step 1: Verify file exists using Read tool
  Step 2: Execute: gh pr comment {pr} --repo {owner}/{repo} --body-file {file_path}
  Step 3: Display success with comment URL

Option B - Post from text:
  Step 1: Execute: gh pr comment {pr} --repo {owner}/{repo} --body '{message}'
  Step 2: Display success with comment URL

Option C - Auto-generate summary:
  Step 1: Get diff statistics
    - Command: gh pr diff {pr} --repo {owner}/{repo} --stat
    - Parse output for files changed, insertions, deletions

  Step 2: Get recent commits
    - Command: gh pr view {pr} --repo {owner}/{repo} --json commits --jq '.commits[-5:] | .[] | "- \(.messageHeadline)"'
    - Collect last 5 commit messages

  Step 3: Format summary markdown template
    - Template:
      ## 🎉 PR Summary

      ### 📝 Recent Commits
      {commit_list}

      ### 📊 Changes Overview
      {diff_stats}

      ### 🔗 PR Link
      https://github.{domain}/{owner}/{repo}/pull/{pr}

  Step 4: Write summary to temp file
    - Path: /tmp/pr-{pr}-auto-summary.md
    - Tool: Write

  Step 5: Post using body-file
    - Command: gh pr comment {pr} --repo {owner}/{repo} --body-file /tmp/pr-{pr}-auto-summary.md

  Step 6: Display success with comment URL
```

**Example Implementation (Auto-generate):**

```bash
# Variables
PR=754
OWNER="my-org"
REPO="test-data-service"
TEMP_FILE="/tmp/pr-$PR-auto-summary.md"

# Step 1: Get diff statistics
DIFF_STATS=$(gh pr diff $PR --repo $OWNER/$REPO --stat | tail -1)

# Step 2: Get recent commits
COMMITS=$(gh pr view $PR --repo $OWNER/$REPO --json commits --jq '.commits[-5:] | .[] | "- \(.messageHeadline)"')

# Step 3-4: Format and write summary
cat > "$TEMP_FILE" <<EOF
## 🎉 PR Summary

### 📝 Recent Commits
$COMMITS

### 📊 Changes Overview
\`\`\`
$DIFF_STATS
\`\`\`

### 🔗 PR Link
https://github.example.com/$OWNER/$REPO/pull/$PR
EOF

# Step 5: Post comment
gh pr comment $PR --repo $OWNER/$REPO --body-file "$TEMP_FILE"

# Step 6: Display success
echo "✅ Successfully posted comment"
echo "Summary saved to: $TEMP_FILE"
```

**Example Implementation (From file):**

```bash
# Variables
PR=754
OWNER="my-org"
REPO="test-data-service"
FILE_PATH="/tmp/my-pr-summary.md"

# Post comment
gh pr comment $PR --repo $OWNER/$REPO --body-file "$FILE_PATH"

echo "✅ Successfully posted comment from file: $FILE_PATH"
```

**Expected Output:**
```
✅ Successfully posted comment
Comment URL: https://github.example.com/my-org/test-data-service/pull/754#issuecomment-1234567
```

---

## Implementation Patterns

### Pattern 1: Full Review Response Workflow

Complete workflow for responding to all review comments:

```bash
PR=754
OWNER="my-org"
REPO="test-data-service"

# Step 1: Query all threads to see what's unresolved
gh api graphql -f query='
query {
  repository(owner: "'"$OWNER"'", name: "'"$REPO"'") {
    pullRequest(number: '"$PR"') {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 5) {
            nodes {
              databaseId
              author { login }
              body
            }
          }
        }
      }
    }
  }
}
' > /tmp/pr-$PR-threads.json

# Step 2: For each addressed comment, post a reply
COMMENT_ID=739591
gh api repos/$OWNER/$REPO/pulls/$PR/comments/$COMMENT_ID/replies \
  --method POST \
  --field body="✅ Implemented with tests"

# Step 3: Resolve the thread
THREAD_ID="MDIzOlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDE4OTE4OnYy"
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
    thread {
      id
      isResolved
    }
  }
}
'

# Step 4: Post overall summary comment
gh pr comment $PR --repo $OWNER/$REPO --body-file /tmp/summary.md
```

---

### Pattern 2: Targeted Thread Resolution

Resolve specific threads based on implementation:

```bash
PR=754
OWNER="my-org"
REPO="test-data-service"
FILE="src/modules/mcp/profile/mcp.profile.controller.ts"

# Query threads
gh api graphql -f query='...' > /tmp/pr-$PR-threads.json

# Filter by file path and extract thread IDs
THREAD_IDS=$(jq -r ".data.repository.pullRequest.reviewThreads.nodes[] |
  select(.path == \"$FILE\" and .isResolved == false) | .id" /tmp/pr-$PR-threads.json)

# Batch resolve matching threads
for THREAD_ID in $THREAD_IDS; do
  gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "'"$THREAD_ID"'"}) {
      thread { id isResolved }
    }
  }
  '
done
```

---

### Pattern 3: Comment Database ID Mapping

Map comment database IDs to thread IDs for easier reference:

```bash
# Extract mapping from query results
jq '.data.repository.pullRequest.reviewThreads.nodes[] |
  {
    threadId: .id,
    commentId: .comments.nodes[0].databaseId,
    path: .path,
    line: .line,
    resolved: .isResolved
  }' /tmp/pr-754-threads.json
```

---

## Repository Configuration

**Repository is a required parameter.** All `gh` commands require `--repo` flag:

```bash
# Query threads for different repo
gh api graphql --repo epic/game-service -f query='...'

# Reply to comment in different repo
gh api repos/epic/game-service/pulls/123/comments/456/replies --method POST --field body="Done!"

# Resolve thread (GraphQL doesn't use --repo, specify in query)
gh api graphql -f query='
query {
  repository(owner: "epic", name: "game-service") {
    pullRequest(number: 123) { ... }
  }
}
'

# Post summary to different repo
gh pr comment 123 --repo epic/game-service --body-file summary.md
```

---

## Troubleshooting

### Common Issues and Solutions

**1. GraphQL UNKNOWN_CHAR Error**
```
gh: Expected one of SCHEMA, SCALAR, TYPE, ENUM, INPUT, UNION, INTERFACE, actual: UNKNOWN_CHAR
```
- **Cause:** Shell escaping issue with quotes in GraphQL query
- **Solution:** Use single quotes around entire query, double quotes inside. For variable substitution, close and reopen quotes: `'mutation { field: "'"$VAR"'" }'`

**2. Thread Already Resolved**
```
Error: Thread is already resolved
```
- **Cause:** Attempting to resolve a thread that's already marked as resolved
- **Solution:** Query threads first to check status before resolving

**3. Invalid Thread ID**
```
Error: Thread not found
```
- **Cause:** Thread ID format is incorrect or thread doesn't exist
- **Solution:** Thread IDs must start with "MDIz..." (GraphQL node IDs). Get IDs from query operation

**4. Permission Denied**
```
Error: You do not have permission to resolve this thread
```
- **Cause:** Missing write access to the repository
- **Solution:** Verify you have write/maintain permissions: `gh api repos/OWNER/REPO --jq .permissions`

**5. Comment Not Found**
```
Error: Comment with ID X not found
```
- **Cause:** Comment database ID is incorrect or comment was deleted
- **Solution:** Use query operation to get current comment IDs. Use comment database IDs (numeric), not GraphQL IDs

**6. Authentication Failed**
```
Error: authentication required
```
- **Cause:** GitHub CLI not authenticated or token expired
- **Solution:** Run `gh auth login` or `gh auth refresh`

**7. jq Command Not Found**
```
bash: jq: command not found
```
- **Cause:** jq not installed on system
- **Solution:** Install jq: `brew install jq` (macOS) or `apt-get install jq` (Linux)

---

## Error Handling Best Practices

When executing operations:

1. **Always query first:** Get current state before making changes
2. **Check exit codes:** `gh` commands return non-zero exit codes on failure
3. **Use continue-on-error logic:** For batch operations, decide whether to stop on first error
4. **Verify thread IDs:** Thread IDs (GraphQL) start with "MDIz...", comment IDs (database) are numeric
5. **Save query results:** Save to temp files for reference and debugging
6. **Parse JSON safely:** Use `jq` with null coalescing: `.field // "default"`

---

## Best Practices

1. **Always query threads first** - Get current state before resolving
2. **Add contextual replies** - Explain what was done before resolving
3. **Batch operations carefully** - Resolve threads individually to catch errors, or use continue-on-error
4. **Verify success** - Check `isResolved: true` in mutation response
5. **Keep summary comment comprehensive** - Include all changes, tests, and JIRA references
6. **Leave future work threads open** - Only resolve what's been implemented
7. **Use temp files for large outputs** - Save query results and summaries for debugging

---

## Notes

- Thread IDs are GraphQL node IDs (format: `MDIz...`)
- Comment IDs are database IDs (format: numeric like `739591`)
- Use thread IDs for resolving, comment IDs for replying
- Both REST API (`gh api repos/...`) and GraphQL work for different operations
- The `gh pr comment` command is simpler for posting new comments
- GraphQL is required for resolving threads (no REST API equivalent)
- All algorithms are deterministic and can be executed by agents on-the-fly

---

## Related Skills

- `/commit` - Create commits after addressing review comments
- `/review-pr` - Analyze PRs before responding to comments
- Consider creating `/jira-pr-link` to automatically link JIRA tickets mentioned in comments
