#!/usr/bin/env bash
# Auto-format .py files after Claude edits them.
#
# Triggered by a PostToolUse hook in .claude/settings.json on Edit, Write,
# MultiEdit, and NotebookEdit. Reads the tool-call payload as JSON on
# stdin, pulls out the file path, and runs `ruff format` + `ruff check
# --fix --quiet` on it if it's a .py file inside this repo.
#
# Exit codes:
#   0 on success or no-op. The hook never fails the tool call.

set -u

# Read the JSON payload (and don't crash if there's nothing on stdin).
input="$(cat || true)"
[ -z "$input" ] && exit 0

# Pull the file_path out of the tool_input. Tolerate any shape we don't
# recognize; the hook is best-effort.
file_path="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tool_input = data.get("tool_input", {})
path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
print(path)
' 2>/dev/null || true)"

# Bail if no path, or path isn't a .py file, or file no longer exists.
[ -z "$file_path" ] && exit 0
case "$file_path" in
    *.py) ;;
    *) exit 0 ;;
esac
[ ! -f "$file_path" ] && exit 0

# Only act on files inside this repo.
project_dir="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$project_dir" ]; then
    project_dir="$(cd "$(dirname "$0")/../.." && pwd)"
fi
case "$file_path" in
    "$project_dir"/*) ;;
    *) exit 0 ;;
esac

# Don't auto-format files we deliberately exclude from ruff (examples/, etc.).
# We let ruff itself decide via its `extend-exclude` config: if ruff
# considers the file excluded, it'll be a no-op.

# Best-effort: format, then auto-fix lint where possible. Stay silent
# unless something goes wrong — and even then, don't fail the tool call.
if command -v uv >/dev/null 2>&1; then
    uv run --quiet ruff format "$file_path" >/dev/null 2>&1 || true
    uv run --quiet ruff check --fix --quiet "$file_path" >/dev/null 2>&1 || true
fi

exit 0
