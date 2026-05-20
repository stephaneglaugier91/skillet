# CLAUDE.md

Project context for Claude Code sessions on the `skillet` repo. Keep this
file short and actionable — it's loaded automatically on session start.

## What this project is

`skillet` lets Python package authors ship Claude Code skills inside their
wheels. End users run `skillet install <pkg>` to copy a package's skills
into `./.claude/skills/` (or `~/.claude/skills/`). Discovery uses the
standard `importlib.metadata` entry-point group `skillet.skills`. No
network, no separate registry.

## Source layout

```
src/skillet/        package source (cli.py, discovery.py, install.py, paths.py)
tests/              pytest suite + conftest with fake-package fixtures
examples/pandasx/   demo package showing how to declare and ship a skill
.github/workflows/  CI (ci.yml) and release (release.yml) pipelines
Makefile            single source of truth for dev commands
```

## How to do anything

Use `make`. Run `make help` to see every target. The most useful:

| Command | What it does |
| --- | --- |
| `make sync` | Install / refresh dev dependencies via uv. |
| `make fmt` | Format code with ruff. (Also runs automatically via a PostToolUse hook after you Edit/Write a `.py` file.) |
| `make check` | The full local CI: lint + format-check + mypy + pytest. **Run this before claiming a task is done.** |
| `make test` | Just the tests. |
| `make test-cov` | Tests with coverage. |
| `make pre-commit` | Run every pre-commit hook (incl. workflow schema, hygiene). |
| `make build-check` | Build sdist + wheel and run `twine check`. |
| `make ci` | The exact sequence CI runs. |

If you find yourself reaching for `uv run …` directly, check whether
there's a Make target for it first — if it's something we do often, add
one to the Makefile.

## Conventions

- **Python 3.12+ only.** Use modern syntax (PEP 604 unions, `StrEnum`,
  `match`/`case` when appropriate). Mypy is in strict mode; type
  everything in `src/`. Tests can be loose.
- **Ruff is the lint + formatter.** Don't argue with it — adjust the
  config in `pyproject.toml` if a rule is genuinely wrong, otherwise
  conform.
- **Public API lives at the package root.** Anything you add that users
  should be able to import as `from skillet import X` belongs in
  `src/skillet/__init__.py`'s `__all__`.
- **Tests are first-class.** New behavior gets a test. Use the fixtures
  in `tests/conftest.py` (`fake_package`, `fake_home`, `fake_project`)
  rather than reaching into `sys.path` directly.
- **No new runtime dependencies without discussion.** skillet is a tiny
  std-lib-only package on purpose. Dev-only deps go under
  `[dependency-groups].dev` in `pyproject.toml`.

## Before declaring a task done

1. `make check` is green.
2. If you added behavior, you also added a test.
3. If you touched public API (the names in `src/skillet/__init__.py`),
   you updated the README and CONTRIBUTING.md if relevant.
4. Commit messages are descriptive (subject under 70 chars).

## Things to ask before doing

The `.claude/settings.json` allowlist covers all the read-only and
local-only dev commands (`uv run *`, `make *`, `git status/diff/log`,
etc.). For these, just run them — no need to ask.

**Do** check with the user before:

- Pushing to a remote (`git push …`).
- Force-pushing or any destructive git op (`reset --hard`, `branch -D`,
  cleaning files).
- Committing (we only commit when the user explicitly asks).
- Bumping the version or cutting a release — the `/release` command
  exists for this; don't do it ad-hoc.
- Changing `.github/workflows/*`, `dependabot.yml`, `.pre-commit-config.yaml`,
  or `.claude/settings.json`. These shape the project's automation;
  describe the intended change first.

## Release workflow

Releases are tag-driven (see `RELEASING.md`). The `/release X.Y.Z` slash
command handles the version bump + tag + push. PyPI publishing happens
automatically via Trusted Publishing on `.github/workflows/release.yml`.

## When the harness compacts your context

Everything above is in this file, so it survives. The Makefile is the
durable interface — relearn the workflow from `make help` if needed.
