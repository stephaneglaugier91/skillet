---
description: Run the test suite (optionally with coverage).
argument-hint: [--cov]
allowed-tools: Bash(make:*)
---

If $ARGUMENTS contains `--cov`, run `make test-cov`. Otherwise run `make test`.

Report pass/fail, the test count, and the names of any failing tests. If everything passes and coverage was requested, also print the totals line.
