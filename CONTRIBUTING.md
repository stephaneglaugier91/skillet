# Contributing to skillet

Thanks for your interest in contributing! This guide will get you set up.

## Development environment

skillet uses [uv](https://docs.astral.sh/uv/) for dependency management and
[Hatchling](https://hatch.pypa.io/latest/) as the build backend.

### One-time setup

```bash
# Install uv (see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and sync
git clone https://github.com/stephaneglaugier91/skillet
cd skillet
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

`uv sync` creates a `.venv/` directory with the project installed in editable
mode plus all dev dependencies. Activate it with `source .venv/bin/activate`
or just prefix commands with `uv run`.

## Running checks

```bash
uv run pytest                 # tests
uv run pytest --cov           # with coverage
uv run ruff check             # lint
uv run ruff format            # format
uv run mypy                   # type-check
uv run pre-commit run --all-files   # everything pre-commit covers
```

CI runs the same set on every PR.

## Supported Python versions

skillet supports Python 3.12 and newer. CI tests against 3.12, 3.13, and 3.14
on Linux, plus 3.12 on macOS and Windows.

## Project layout

```
src/skillet/        # package source
tests/              # pytest suite
examples/pandasx/   # demo package showing how to ship skills
.github/workflows/  # CI / release pipelines
```

## Pull requests

1. Fork and create a topic branch off `main`.
2. Make your change. Add tests for any new behavior.
3. Make sure `uv run pre-commit run --all-files`, `uv run mypy`, and
   `uv run pytest` all pass.
4. Open a PR. The PR template will prompt you for the relevant details.

Keep PRs focused — one logical change per PR is easier to review and revert.

## Commit messages

There's no strict format, but please write a clear subject line (under 70
characters) describing *what* changed and *why*. Use the body for context if
the change is non-obvious.

## Reporting bugs / requesting features

Use the issue templates under
[Issues → New issue](https://github.com/stephaneglaugier91/skillet/issues/new/choose).

## Code of Conduct

By participating in this project, you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).
