# skillet — developer commands
#
# All dev workflows go through this Makefile so contributors and CI share
# the same entry points. Run `make help` to list every target.

.DEFAULT_GOAL := help

UV ?= uv
PYTHON_VERSION ?= 3.12

# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "; printf "Usage: make <target>\n\nTargets:\n"} \
		/^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

.PHONY: sync
sync: ## Install / refresh dev dependencies (creates .venv).
	$(UV) sync

.PHONY: hooks
hooks: ## Install the pre-commit git hooks.
	$(UV) run pre-commit install

# ---------------------------------------------------------------------------
# Lint / format / types
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff lint check (no fixes).
	$(UV) run ruff check

.PHONY: lint-fix
lint-fix: ## Run ruff with --fix.
	$(UV) run ruff check --fix

.PHONY: fmt
fmt: ## Format code with ruff (writes changes).
	$(UV) run ruff format
	$(UV) run ruff check --fix --quiet

.PHONY: fmt-check
fmt-check: ## Check formatting without modifying.
	$(UV) run ruff format --check

.PHONY: typecheck
typecheck: ## Run mypy in strict mode.
	$(UV) run mypy

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: test
test: ## Run the test suite.
	$(UV) run pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage reports.
	$(UV) run pytest --cov --cov-report=term --cov-report=xml

# ---------------------------------------------------------------------------
# Composite checks
# ---------------------------------------------------------------------------

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks across the whole repo.
	$(UV) run pre-commit run --all-files

.PHONY: check
check: lint fmt-check typecheck test ## Run lint + format-check + types + tests.

.PHONY: ci
ci: pre-commit typecheck test-cov ## Run the exact suite CI runs locally.

# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

.PHONY: build
build: ## Build sdist and wheel into dist/.
	$(UV) build

.PHONY: build-check
build-check: build ## Build, then run twine check on the artifacts.
	$(UV) tool run twine check dist/*

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove build artifacts and tool caches.
	rm -rf build dist *.egg-info \
		.pytest_cache .mypy_cache .ruff_cache \
		.coverage coverage.xml htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: clean-all
clean-all: clean ## Also remove the uv-managed virtualenv.
	rm -rf .venv
