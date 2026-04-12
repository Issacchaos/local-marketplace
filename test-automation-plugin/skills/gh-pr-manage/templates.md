# PR Comment Templates

## Summary Comment Template

```markdown
## 🎉 Implementation Complete - All Review Comments Addressed

Thank you for the thorough review! I've addressed all feedback.

### ✅ Changes Implemented

#### 1. [Feature Name] (Comment #[ID])
- **What**: Brief description
- **Implementation**: What was done
- **Files**: List of modified files
- **Tests**: Test results or new tests added

#### 2. [Another Feature]
...

### 📋 JIRA Tickets for Future Work

- **[TICKET-ID]** - Description (Comment #[ID])
- **[TICKET-ID]** - Description

### 🧪 Test Results

```
✅ [test-suite-1]: X/X passed
✅ [test-suite-2]: Y/Y passed
```

**Files Changed**: X files, Y insertions(+), Z deletions(-)

### 📦 Summary

Brief summary of what's ready for approval and any next steps.

---

**JIRA References:**
- [TICKET-1]: https://jira.example.com/browse/[TICKET-1]
- [TICKET-2]: https://jira.example.com/browse/[TICKET-2]
```

## Reply Templates

### Implementation Complete Reply

```markdown
✅ Implemented! [Brief description of what was done]

Changes:
- [Detail 1]
- [Detail 2]

[Optional: Test results, file references, or additional context]
```

### Documentation Added Reply

```markdown
✅ Added documentation in [file:line]. [Brief description of what was documented]

[Optional: Created JIRA-XXX for further investigation]
```

### Future Work Reply

```markdown
Great suggestion! After evaluating the complexity ([estimate] LOC + [considerations]), I've created [JIRA-XXX] to track this as a future enhancement.

This will allow [brief description of future feature].
```

### Investigation Needed Reply

```markdown
✅ Added [TODO/comment/documentation] noting [the issue]. Created [JIRA-XXX] to investigate and implement [the solution] in a future PR.
```

### Test Coverage Reply

```markdown
✅ Added test cases to verify this behavior:
- [Test case 1 description]
- [Test case 2 description]

All [X] tests passing!
```

## Thread Query Output Template

```
Review Threads Summary for PR #[NUMBER]
========================================

Total Threads: [X]
Resolved: [Y]
Unresolved: [Z]

Unresolved Threads:
-------------------

[Thread ID]: [File]:[Line]
  Comment ID: [ID]
  Author: [username]
  Preview: "[first 50 chars...]"

...
```

## Batch Resolution Script Template

```bash
#!/bin/bash
# Resolve multiple threads for PR

PR_NUMBER=$1
shift
THREAD_IDS=("$@")

echo "Resolving ${#THREAD_IDS[@]} threads for PR #$PR_NUMBER"

for thread_id in "${THREAD_IDS[@]}"; do
  echo "Resolving thread: $thread_id"

  result=$(gh api graphql -f query="
    mutation {
      resolveReviewThread(input: {threadId: \"$thread_id\"}) {
        thread {
          id
          isResolved
        }
      }
    }
  ")

  is_resolved=$(echo "$result" | jq -r '.data.resolveReviewThread.thread.isResolved')

  if [ "$is_resolved" = "true" ]; then
    echo "✅ Resolved: $thread_id"
  else
    echo "❌ Failed to resolve: $thread_id"
    echo "Response: $result"
  fi
done

echo ""
echo "Resolution complete!"
```
