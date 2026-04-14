# Git hooks

Project-tracked hooks. To activate them in your local clone, run once:

```sh
git config core.hooksPath .githooks
```

That points git at this directory instead of `.git/hooks/`. Git tracks these files; `.git/hooks/` does not.

## Hooks

- **pre-commit** — rejects commits whose staged diff adds unresolved git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). Catches the case where a merge resolution forgot to delete the markers.
