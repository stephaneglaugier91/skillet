---
description: Run the full local check suite (lint + format + types + tests).
allowed-tools: Bash(make:*)
---

Run `make check` and report the result.

If it fails, identify the failing step (lint / format-check / mypy / pytest) and decide whether to fix it. For purely mechanical failures (formatting, import order, trivial lint), fix them and re-run. For substantive failures (type errors, test failures), summarize what's wrong and ask the user how to proceed.

End with a one-line status: `check: ✓` or `check: ✗ <what failed>`.
