# gh-pr-manage Skill Installation

The `gh-pr-manage` skill provides algorithms for managing GitHub PR review threads and comments using direct `gh` CLI commands.

## Prerequisites

Before using this skill, ensure you have:

1. **GitHub CLI** (`gh`) installed and authenticated
   ```bash
   gh --version          # Check installation
   gh auth login         # Authenticate if needed
   gh auth status        # Verify authentication
   ```

2. **jq** (JSON processor) for parsing responses
   ```bash
   jq --version          # Check installation

   # Install if needed:
   # macOS: brew install jq
   # Ubuntu/Debian: apt-get install jq
   # Windows: choco install jq
   ```

3. **bash** (for command execution)

## Installation Options

### Option 1: Use as Dante Plugin Skill (Recommended)

If this skill is in the `dante_plugin` project:

```bash
# The skill is already available in skills/gh-pr-manage/
# No installation needed - agents can read SKILL.md directly
```

### Option 2: Copy to Personal Claude Skills

To make this skill available globally across all your projects:

```bash
# Copy to personal Claude directory
cp -r skills/gh-pr-manage ~/.claude/skills/

# Verify installation
ls -lh ~/.claude/skills/gh-pr-manage/
```

### Option 3: Copy to Project-Specific Skills

To make this skill available only in a specific project:

```bash
# From the dante_plugin directory
cp -r skills/gh-pr-manage /path/to/your-project/.claude/skills/

# Verify installation
ls -lh /path/to/your-project/.claude/skills/gh-pr-manage/
```

## What's Included

```
gh-pr-manage/
├── SKILL.md           # Complete algorithms for all operations
├── README.md          # Quick start guide and examples
├── INSTALL.md         # This file
└── templates.md       # Comment templates
```

## How It Works

This skill is **fully agentic** - agents execute commands directly using the algorithms documented in `SKILL.md`. There are no scripts to install or execute.

### Algorithm-Based Execution

Agents read `SKILL.md` and follow the documented algorithms:

1. **Algorithm 1: Query Review Threads** - Fetch threads with GraphQL
2. **Algorithm 2: Reply to Comment** - Post contextual replies
3. **Algorithm 3: Resolve Thread** - Mark threads as resolved
4. **Algorithm 4: Batch Resolve** - Resolve multiple threads
5. **Algorithm 5: Post Summary** - Add PR summary comments

Each algorithm includes:
- Step-by-step pseudocode
- Exact `gh` CLI commands
- `jq` parsing patterns
- Error handling guidance

Agents execute these algorithms on-the-fly using their Bash tool to run `gh` and `jq` commands directly.

## Quick Start

### Using in Claude Code

Agents can invoke this skill to manage PR review threads:

```
Help me resolve all review threads in PR #754
Post a summary comment on PR #754
Reply to comment 739591 saying the issue is fixed
```

### Direct CLI Usage (Manual)

You can also use the commands directly:

```bash
# Query threads
gh api graphql -f query='query { ... }' > /tmp/pr-754-threads.json

# Reply to comment
gh api repos/owner/repo/pulls/754/comments/739591/replies \
  --method POST --field body='✅ Implemented!'

# Resolve thread
gh api graphql -f query='mutation { resolveReviewThread(...) }'
```

See `SKILL.md` for complete command syntax.

## Verification

### Check Installation

```bash
# Verify files exist
ls -lh ~/.claude/skills/gh-pr-manage/SKILL.md

# Check prerequisites
gh --version          # Should be 2.0.0 or higher
jq --version          # Should be 1.6 or higher
gh auth status        # Should show authenticated
```

### Test Commands

```bash
# Test GraphQL query (substitute real values)
gh api graphql -f query='query { repository(owner: "eos", name: "test-data-service") { pullRequest(number: 754) { reviewThreads(first: 1) { nodes { id } } } } }'

# Test jq parsing
echo '{"data": {"test": "value"}}' | jq '.data.test'
```

## Repository Configuration

The skill defaults to `eos/test-data-service` but can work with any repository. Configure defaults in `SKILL.md` or pass `--owner` and `--repo` flags to commands.

## Documentation

- **SKILL.md** - Complete algorithms (PRIMARY REFERENCE)
- **README.md** - Quick start and common workflows
- **templates.md** - Comment templates for PR reviews

## Troubleshooting

### "gh: command not found"
Install GitHub CLI: https://cli.github.com/

### "This command requires authentication"
Run: `gh auth login`

### "jq: command not found"
Install jq:
- macOS: `brew install jq`
- Linux: `apt-get install jq` or `yum install jq`
- Windows: `choco install jq`

### "Repository not found"
Ensure you have access to the repository and are authenticated with the correct GitHub account.

## Updating

To update the skill:

```bash
# If copied to personal directory
cd ~/dante_plugin
git pull
cp -r skills/gh-pr-manage ~/.claude/skills/

# Verify update
cat ~/.claude/skills/gh-pr-manage/SKILL.md | head -20
```

## Uninstall

```bash
# Remove from personal directory
rm -rf ~/.claude/skills/gh-pr-manage

# Remove from project directory
rm -rf /path/to/project/.claude/skills/gh-pr-manage
```

---

**Version:** 3.0.0 (Fully Algorithm-Based - No Scripts)
**Last Updated:** 2026-02-19
**Compatibility:** Cross-platform (requires `gh` CLI + `jq`)
