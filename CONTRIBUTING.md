# Contributing to skillet

Thanks for your interest in contributing! This guide will get you set up.

## Development environment

skillet uses [uv](https://docs.astral.sh/uv/) for dependency management,
[Hatchling](https://hatch.pypa.io/latest/) as the build backend, and a
`Makefile` as the single entry point for every dev workflow.

### One-time setup

```bash
# Install uv (see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and bootstrap
git clone https://github.com/stephaneglaugier91/skillet
cd skillet
make sync          # creates .venv and installs deps
make hooks         # installs the pre-commit git hooks
```

`make sync` runs `uv sync`, which creates a `.venv/` with skillet installed
in editable mode plus all dev dependencies.

## Running checks

```bash
make help          # list every target
make check         # full local CI: lint + format-check + types + tests
make test          # just the tests
make test-cov      # tests with coverage
make fmt           # format and apply auto-fixes
make lint          # ruff lint check
make typecheck     # mypy strict
make pre-commit    # run every pre-commit hook
make build-check   # build sdist+wheel and run twine check
```

CI runs the same checks (via `make pre-commit`, `make typecheck`, etc.) on
every PR, so `make check` locally matches CI almost exactly. Run it
before opening a PR.

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
