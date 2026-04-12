# Staleness Checker Sub-Skill

**Parent**: `skills/dream-manager/SKILL.md`
**Purpose**: Detect when a dream's source repository has new commits since last analysis.

---

## Staleness Check Procedure

### Input

- Dream name (or all dreams)
- Source metadata from `source.json`

### Output

```json
{
  "dream_name": "my-dream",
  "stale": true,
  "stored_commit": "abc123def456...",
  "current_commit": "789xyz012345...",
  "commits_behind": 5,
  "changed_files": ["src/main.ts", "package.json"],
  "check_duration_ms": 450
}
```

---

## Check Methods

### Local Repositories

```bash
# Get current HEAD
CURRENT=$(git -C "<path>" rev-parse HEAD)

# Compare with stored
if [ "$CURRENT" != "$STORED_COMMIT" ]; then
  # Get commit count difference
  BEHIND=$(git -C "<path>" rev-list --count "$STORED_COMMIT".."$CURRENT")

  # Get changed files
  CHANGED=$(git -C "<path>" diff --name-only "$STORED_COMMIT".."$CURRENT")
fi
```

**Performance**: ~50ms for local repos. No network calls.

### GitHub Repositories

```bash
# Get latest commit on tracked branch
CURRENT=$(gh api repos/<owner>/<repo>/commits/<branch> --jq .sha)

# Compare with stored
if [ "$CURRENT" != "$STORED_COMMIT" ]; then
  # Get comparison details
  COMPARE=$(gh api repos/<owner>/<repo>/compare/<stored>..<current> \
    --jq '{ahead_by: .ahead_by, files: [.files[].filename]}')
fi
```

**Performance**: ~1-3 seconds depending on network. Rate limited by GitHub API.

---

## Batch Checking

When checking all dreams, run checks in parallel:

```
For each dream in DREAMS.md:
  1. Read source.json
  2. Run appropriate check method (local or GitHub)
  3. Collect result

Return array of check results, sorted by staleness (stale first)
```

For GitHub repos, batch API calls when possible to minimize rate limit impact.

---

## Staleness Display

### Warning Format (shown before subcommand output)

```
Dream "my-dream" is 5 commits behind source (last checked: 2h ago).
  Changed: src/main.ts, package.json, +3 more
  Run: /mentor update --name my-dream
```

### Compact Format (for `/mentor list` table)

| Status | Display |
|--------|---------|
| Fresh (0 commits behind) | `Fresh` |
| Slightly stale (1-5 behind) | `Stale (3 behind)` |
| Very stale (6+ behind) | `Stale (12 behind)` |
| Check failed | `Unknown` |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Local path no longer exists | Display: `Warning: Source path for "{name}" no longer exists. Dream data is preserved but cannot be updated.` |
| GitHub API rate limited | Display: `Warning: GitHub API rate limit reached. Staleness check skipped for GitHub dreams.` |
| gh not authenticated | Display: `Warning: gh not authenticated. Run "gh auth login" to enable GitHub staleness checks.` |
| Network unavailable | Display: `Warning: Network unavailable. Staleness check skipped for GitHub dreams.` |
| Stored commit no longer exists (force-pushed) | Display: `Warning: Dream "{name}" commit no longer exists in source (likely force-pushed). Run /mentor update --name {name} for full re-analysis.` |

### Graceful Degradation

Staleness check failures should **never** block the subcommand. If a check fails:
1. Display a warning
2. Mark status as `Unknown`
3. Proceed with the requested operation

---

## Caching

To avoid redundant checks within a single session:

- Cache check results for 5 minutes
- If a subcommand was just run and another follows quickly, reuse cached result
- Cache is in-memory only (not persisted to disk)
- Cache key: `dream_name + source_type`

This prevents hammering the GitHub API when running multiple `/dream` commands in sequence.
