# Releasing skillet

Releases are fully automated by `.github/workflows/release.yml`. Pushing a
tag matching `v*` will:

1. Build the sdist and wheel with `uv build`.
2. Run `twine check` on the artifacts.
3. Upload to PyPI using **trusted publishing** (no API token needed).
4. Create a GitHub Release with auto-generated notes and the artifacts attached.

## One-time PyPI setup

Before the first release, configure PyPI Trusted Publishing once:

1. Sign in to https://pypi.org and create the project (or reserve the name
   by uploading a 0.0.0 placeholder manually).
2. Go to **Manage → Publishing → Add a new pending publisher** (or, if the
   project already exists, **Settings → Publishing**).
3. Fill in:
   - **PyPI Project Name:** `skillet`
   - **Owner:** `stephaneglaugier91`
   - **Repository name:** `skillet`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Save.

In GitHub, create an Environment named `pypi`:

1. **Settings → Environments → New environment** → `pypi`.
2. Optionally require manual approval before deployments to `pypi`.

That's it. Future releases need only a tag.

## Cutting a release

The easiest path is the `/release X.Y.Z` Claude Code slash command, which
runs the procedure below with safety checks.

Manual procedure:

```bash
# 1. Make sure main is green and you're up to date.
git checkout main
git pull --ff-only

# 2. Verify everything passes locally before cutting.
make check
make build-check

# 3. Bump the version in pyproject.toml.
$EDITOR pyproject.toml          # version = "X.Y.Z"

# 4. Commit and tag.
git commit -am "Release vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

The `release.yml` workflow will run on the tag, publish to PyPI, and create
the GitHub release.

## Versioning

skillet follows [Semantic Versioning 2.0](https://semver.org/) once it
reaches 1.0. Pre-1.0 releases (0.x.y) may include breaking changes in minor
bumps; patch bumps remain backwards compatible.

## Yanking a bad release

If a release is broken, yank it from PyPI:

```bash
uv tool run twine yank skillet --version X.Y.Z --reason "broken: <reason>"
```

Yanking hides the release from new installs but keeps it available for
projects that have already pinned to it. Cut a fixed follow-up release as
soon as possible.
