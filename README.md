# skillet

[![CI](https://github.com/stephaneglaugier91/skillet/actions/workflows/ci.yml/badge.svg)](https://github.com/stephaneglaugier91/skillet/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/stephaneglaugier91/skillet/branch/main/graph/badge.svg)](https://codecov.io/gh/stephaneglaugier91/skillet)
[![PyPI version](https://img.shields.io/pypi/v/skillet.svg)](https://pypi.org/project/skillet/)
[![Python versions](https://img.shields.io/pypi/pyversions/skillet.svg)](https://pypi.org/project/skillet/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Ship Claude Code skills alongside your Python package.

Package authors drop skill files into their package and declare them in
`pyproject.toml`. Users install them with one command — no extra downloads,
no separate registry.

## Install

```bash
pip install skillet
```

## For users

Install the skills shipped by an installed Python package into your project:

```bash
# Per-project (./.claude/skills/)
skillet install pandas --local

# User-wide (~/.claude/skills/)
skillet install pandas --user
```

Other commands:

```bash
skillet list                  # what's installed in ./.claude/skills/
skillet list --available      # what's available from installed packages
skillet uninstall pandas
skillet where                 # print the target skills directory
```

`--local` is the default. `--claude` is accepted as a (currently no-op) host
selector — it's reserved for future targets.

## For package authors

### 1. Drop your skill into your package

A skill is a directory containing a `SKILL.md` (plus any helper files). Put it
inside your package — for example:

```
src/
  pandas/
    skills/
      pandas/
        SKILL.md
```

A single entry-point can expose multiple skills: just put each one in its own
subdirectory under `skills/`. (If `skills/` itself contains a `SKILL.md`, it's
treated as a single skill.)

### 2. Declare it in `pyproject.toml`

```toml
[project.entry-points."skillet.skills"]
pandas = "pandas.skills"
```

The value is a dotted module path; skillet imports it and uses its directory
on disk.

Make sure the skill files are included in your wheel. With setuptools:

```toml
[tool.setuptools.package-data]
"pandas.skills" = ["**/*"]
```

That's it. Once your package is installed, users can run
`skillet install pandas` and it just works.

### 3. (Optional) Expose your own CLI subcommand

If you want `pandas-skillet install` to work, wire a tiny entry-point that
delegates to skillet:

```python
# src/pandas/_skillet_entry.py
from skillet.cli import package_main


def main() -> int:
    return package_main("pandas")
```

```toml
# pyproject.toml
[project.scripts]
"pandas-skillet" = "pandas._skillet_entry:main"
```

The wrapped CLI has the same commands as `skillet`, but the package name is
implicit — users run `pandas-skillet install --local` instead of
`skillet install pandas --local`.

## How discovery works

Skillet uses the standard `importlib.metadata` entry-point mechanism (the same
one `pytest`, `setuptools`, and pip plugins use). When you call
`skillet install <pkg>`, it:

1. Looks up entry points in the group `skillet.skills`.
2. Imports the referenced module and finds its directory on disk.
3. Copies each skill subdirectory into `./.claude/skills/` (or `~/.claude/skills/`).
4. Records what was installed in `.claude/skills/.skillet.json` so
   `uninstall` can clean up only what skillet put there.

No network calls. No central registry. The skill ships with the wheel.

## Layout in the install target

```
.claude/
  skills/
    .skillet.json       # manifest of what skillet installed
    pandas/             # one directory per skill
      SKILL.md
      ...
```

If a skill directory already exists and skillet didn't create it, install
skips it. Pass `--force` to overwrite.

## Library API

You can also drive skillet programmatically:

```python
from skillet import install, uninstall, list_installed, Target

install("pandas", Target.LOCAL)
list_installed(Target.LOCAL)
uninstall("pandas", Target.LOCAL)
```

## Example

See `examples/pandasx/` for a complete demo package.

## Development

skillet uses [uv](https://docs.astral.sh/uv/) and supports Python 3.12+.

```bash
git clone https://github.com/stephaneglaugier91/skillet
cd skillet
uv sync
uv run pre-commit install

uv run pytest             # tests
uv run ruff check         # lint
uv run mypy               # type-check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and
[RELEASING.md](RELEASING.md) for how releases are cut.

## License

MIT — see [LICENSE](LICENSE).
