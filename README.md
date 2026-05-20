# skillet

[![CI](https://github.com/stephaneglaugier91/skillet/actions/workflows/ci.yml/badge.svg)](https://github.com/stephaneglaugier91/skillet/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/stephaneglaugier91/skillet/branch/main/graph/badge.svg)](https://codecov.io/gh/stephaneglaugier91/skillet)
[![PyPI version](https://img.shields.io/pypi/v/skillet.svg)](https://pypi.org/project/skillet/)
[![Python versions](https://img.shields.io/pypi/pyversions/skillet.svg)](https://pypi.org/project/skillet/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Ship agent skills alongside your Python package.

Package authors drop skill files into their package and declare them in
`pyproject.toml`. Users install them into Claude Code, Codex, pi, or OpenCode
with one command — no extra downloads, no separate registry.

## Install

```bash
pip install skillet
```

skillet ships its own skill via skillet — install it so your agent knows how
to help you use skillet itself:

```bash
skillet install skillet --local   # Claude Code, per-project (default)
skillet install skillet --codex   # Codex, per-project
skillet install skillet --pi      # pi, per-project
skillet install skillet --opencode
```

## For users

Install the skills shipped by an installed Python package into your project:

```bash
# Per-project Claude Code target (./.claude/skills/), the default
skillet install pandas

# User-wide Claude Code target (~/.claude/skills/)
skillet install pandas --user

# Other hosts
skillet install pandas --codex      # ./.agents/skills/
skillet install pandas --pi         # ./.pi/skills/
skillet install pandas --opencode   # ./.opencode/skills/
```

Other commands:

```bash
skillet list                  # what's installed in ./.claude/skills/
skillet list --available      # what's available from installed packages
skillet uninstall pandas
skillet where                 # print the target skills directory
```

`--local` and `--claude` are the defaults. Host selectors can be passed as
flags (`--claude`, `--codex`, `--pi`, `--opencode`) or with
`--host {claude,codex,pi,opencode}`.

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
    return package_main("pandas", prog="pandas-skillet")
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
3. Copies each skill subdirectory into the selected host's skills directory.
4. Records what was installed in that directory's `.skillet.json` so
   `uninstall` can clean up only what skillet put there.

No network calls. No central registry. The skill ships with the wheel.

## Layout in the install target

```
<host skills dir>/
  .skillet.json       # manifest of what skillet installed in this target
  pandas/             # one directory per skill
    SKILL.md
    ...
```

Target directories:

| Host | `--local` | `--user` |
| --- | --- | --- |
| Claude Code | `./.claude/skills/` | `~/.claude/skills/` |
| Codex | `./.agents/skills/` | `~/.agents/skills/` |
| pi | `./.pi/skills/` | `~/.pi/agent/skills/` |
| OpenCode | `./.opencode/skills/` | `${OPENCODE_CONFIG_DIR:-$XDG_CONFIG_HOME/opencode}/skills/` |

If a skill directory already exists and skillet didn't create it, install
skips it. Pass `--force` to overwrite.

## Library API

You can also drive skillet programmatically:

```python
from skillet import Host, Target, install, list_installed, uninstall

install("pandas", Target.LOCAL)              # Claude Code default
install("pandas", Target.LOCAL, Host.CODEX) # Codex
list_installed(Target.LOCAL, Host.CODEX)
uninstall("pandas", Target.LOCAL, Host.CODEX)
```

## Example

See `examples/pandasx/` for a complete demo package.

## Development

skillet uses [uv](https://docs.astral.sh/uv/) and supports Python 3.12+.
All dev workflows go through `make`:

```bash
git clone https://github.com/stephaneglaugier91/skillet
cd skillet
make sync       # install deps
make hooks      # install pre-commit hooks
make check      # lint + format-check + types + tests
make help       # see every target
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and
[RELEASING.md](RELEASING.md) for how releases are cut.

## License

MIT — see [LICENSE](LICENSE).
