# Loader Sub-Skill

**Parent**: `skills/dream-manager/SKILL.md`
**Purpose**: Resolve dream sources (GitHub URLs or local paths), clone repos, and manage source metadata.

---

## Source Resolution

Determine the source type from user input:

### GitHub Sources

Match any of these patterns:
- `https://github.com/<owner>/<repo>`
- `https://github.com/<owner>/<repo>.git`
- `git@github.com:<owner>/<repo>.git`
- `<owner>/<repo>` (shorthand - resolve via `gh repo view`)
- GitHub Enterprise: `https://<host>/<owner>/<repo>`

**Extract**:
- `owner`: GitHub organization or user
- `repo`: Repository name
- `host`: GitHub host (default: `github.com`)

### Local Sources

Anything that doesn't match GitHub patterns is treated as a local path.

**Validation**:
1. Resolve to absolute path
2. Verify directory exists: `test -d <path>`
3. Verify it's a git repo: `git -C <path> rev-parse --git-dir`
4. Get default branch: `git -C <path> symbolic-ref --short HEAD`

---

## Clone Strategy (GitHub Sources)

For GitHub repos, clone to a temporary directory for analysis:

```bash
# Create temp directory
TEMP_DIR=$(mktemp -d)

# Clone with depth 1 for speed (we only need current state)
gh repo clone <owner>/<repo> "$TEMP_DIR" -- --depth 1 --branch <branch>

# After analysis, clean up
rm -rf "$TEMP_DIR"
```

**Branch resolution**:
1. If `--branch` specified, use it
2. Otherwise, detect default branch: `gh api repos/<owner>/<repo> --jq .default_branch`

---

## Source Metadata

After resolving the source, write `source.json`:

```json
{
  "type": "github",
  "owner": "org",
  "repo": "my-repo",
  "host": "github.com",
  "url": "https://github.com/org/my-repo",
  "branch": "main",
  "last_commit": "abc123def456",
  "last_analyzed": "2026-03-28T10:00:00.000Z",
  "clone_path": null
}
```

For local repos:

```json
{
  "type": "local",
  "path": "/absolute/path/to/repo",
  "branch": "main",
  "last_commit": "abc123def456",
  "last_analyzed": "2026-03-28T10:00:00.000Z"
}
```

---

## Name Derivation

If user doesn't provide `--name`:

1. **GitHub**: Use repo name (e.g., `https://github.com/org/awesome-app` → `awesome-app`)
2. **Local**: Use directory name (e.g., `/home/user/projects/my-app` → `my-app`)
3. **Sanitize**: Replace non-alphanumeric characters (except `-` and `_`) with `-`
4. **Deduplicate**: If name exists, append `-2`, `-3`, etc.

---

## Access Validation

Before proceeding with clone or analysis:

### GitHub
```bash
# Verify repo is accessible
gh api repos/<owner>/<repo> --jq .full_name
```

If this fails, display:
```
Error: Cannot access GitHub repository "{owner}/{repo}".
Ensure you have access and gh is authenticated (run: gh auth status).
```

### Local
```bash
# Verify path exists and is a git repo
git -C <path> rev-parse --git-dir 2>/dev/null
```

If this fails, display:
```
Error: "{path}" is not a git repository.
Ensure the path exists and contains a git repository.
```

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `gh: command not found` | gh CLI not installed | Tell user to install gh CLI |
| `gh auth` failure | Not authenticated | Tell user to run `gh auth login` |
| Repository not found | Bad URL or no access | Verify URL and permissions |
| Clone timeout | Large repo or slow network | Suggest using `--branch` to limit |
| Path not found | Invalid local path | Verify path exists |
| Not a git repo | Local path without .git | Must be a git repository |
