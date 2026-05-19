---
description: Cut a release — bump version, commit, tag, push.
argument-hint: <version>
---

Cut release `$1`. Be careful: this triggers the PyPI publish workflow.

Procedure:

1. **Validate inputs.**
   - `$1` must be a semver of the form `X.Y.Z` (no leading `v`). If it isn't, stop and ask.
2. **Verify branch state.**
   - Run `git rev-parse --abbrev-ref HEAD`. We must be on `main`. If not, stop and ask.
   - Run `git status --porcelain`. The working tree must be clean. If not, stop and ask.
   - Run `git pull --ff-only origin main` to make sure we're up to date.
3. **Pre-flight checks.**
   - Run `make check`. If it fails, stop and report.
   - Run `make build-check`. If it fails, stop and report.
4. **Bump the version.**
   - Edit `pyproject.toml`: change `version = "..."` to `version = "$1"`.
   - Run `make check` once more to make sure the bump didn't break anything.
5. **Confirm with the user** before doing anything destructive. Show them:
   - The new version.
   - That you're about to commit, tag, and push.
   - That this will trigger the PyPI release workflow.
6. **On confirmation:**
   - `git add pyproject.toml`
   - `git commit -m "Release v$1"`
   - `git tag -a "v$1" -m "v$1"`
   - `git push origin main`
   - `git push origin "v$1"`
7. **Report:** the tag URL and a reminder that the release workflow now runs on GitHub.

If anything fails or is ambiguous at any step, stop and ask. Don't try to roll back partial state without checking first.
