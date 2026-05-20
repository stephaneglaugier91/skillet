---
name: skillet
description: Use when the user is shipping Claude Code skills inside a Python package with `skillet` (declaring a `skillet.skills` entry point in `pyproject.toml`, laying out a `skills/` directory inside a package, or running `skillet install/list/uninstall/where`). Also use when debugging why a package's skill isn't being discovered.
---

# skillet

`skillet` lets a Python package ship Claude Code skills inside its wheel.
End users run `skillet install <pkg>` and the package's skills land in
`./.claude/skills/` (or `~/.claude/skills/`). Discovery is the standard
`importlib.metadata` entry-point group `skillet.skills` — no network,
no separate registry.

This skill covers both sides: shipping a skill as a package author, and
installing/managing skills as an end user.

## End-user CLI

```bash
skillet install <pkg> [--local|--user] [-f]      # install pkg's skills
skillet uninstall <pkg> [--local|--user]         # remove pkg's skills
skillet list [--local|--user] [--available]      # list installed in target; --available shows discoverable
skillet where [--local|--user]                   # print the target dir
skillet --version
```

- `--local` (default) → `./.claude/skills/`
- `--user`            → `~/.claude/skills/`
- `--force` overwrites a skill dir that exists but isn't owned by skillet
  (i.e. was put there by hand). Without it, those are skipped.

A manifest at `.claude/skills/.skillet.json` tracks which skills came
from which package, so `uninstall` removes only what skillet placed.

## Shipping a skill from your package

You need three things:

### 1. Skill files inside your package

Put each skill in its own directory containing a `SKILL.md` (plus any
helper files). Convention:

```
src/
  mypkg/
    skills/
      mypkg/            # one skill named "mypkg"
        SKILL.md
      mypkg-advanced/   # optional second skill
        SKILL.md
        scripts/
          helper.py
```

If `skills/` itself contains a `SKILL.md`, it's treated as a single skill
(named after the directory). Otherwise each immediate subdirectory with a
`SKILL.md` becomes one skill.

### 2. Entry-point declaration in `pyproject.toml`

```toml
[project.entry-points."skillet.skills"]
mypkg = "mypkg.skills"
```

The value is a dotted **module path**. skillet imports it and uses its
on-disk directory. The entry-point name (left side) is what end users pass
to `skillet install`. Case-insensitive; `-` and `_` are equivalent
(`my-pkg` matches `my_pkg`).

### 3. Make sure the skill files end up in the wheel

The trap: many build backends ship only `.py` files by default and silently
drop `SKILL.md`.

- **Hatchling** (recommended): files in a Python package directory are
  included by default. Just make sure `skills/` has an `__init__.py` (or
  is declared as a namespace package) so it's treated as part of the
  package.
- **Setuptools**: add to `pyproject.toml`:
  ```toml
  [tool.setuptools.package-data]
  "mypkg.skills" = ["**/*"]
  ```

After building, verify with:
```bash
python -m zipfile -l dist/mypkg-*.whl | grep SKILL.md
```

### Optional: branded subcommand for your users

If you want `mypkg-skillet install` to work (so users don't even need to
remember the package name), wire a tiny console_script:

```python
# src/mypkg/_skillet_entry.py
from skillet.cli import package_main


def main() -> int:
    # Pass `prog=` so `mypkg-skillet --help` prints the right program
    # name. Default would be "mypkg skillet" (with a space), which
    # doesn't match the installed console_script.
    return package_main("mypkg", prog="mypkg-skillet")
```

```toml
[project.scripts]
"mypkg-skillet" = "mypkg._skillet_entry:main"
```

`package_main` uses the same CLI as `skillet`, but the package name is
implicit — users run `mypkg-skillet install --local` instead of
`skillet install mypkg --local`.

## Library API

For programmatic use (e.g. an installer GUI, or wiring skillet into another
tool):

```python
from skillet import (
    install, uninstall, list_installed,        # actions
    discover, find_source,                      # discovery
    Target,                                     # LOCAL or USER
    InstallResult, SkillSource, Skill,          # data types
    SkilletError, PackageNotFoundError, NoSkillsDeclaredError,
)

result = install("mypkg", Target.LOCAL)
# result.installed, result.skipped, result.replaced, result.orphans_removed
```

`install()` returns an `InstallResult` whose tuples tell you exactly what
happened. `discover()` returns every `SkillSource` available on the
current `sys.path`; `find_source(name)` looks up one by name.

## Reinstall and orphan behaviour

When a user reinstalls a package whose set of shipped skills has changed,
skillet:

1. Removes skills it previously owned that the new version no longer
   ships (these are surfaced in `InstallResult.orphans_removed`).
2. Overwrites skills it previously owned that still exist in the source.
3. Skips skills it doesn't own that already exist on disk (use
   `--force` to overwrite).

The manifest reflects only what skillet currently owns on disk after the
operation — it never accumulates stale ownership claims.

## Troubleshooting

**"No installed package named X publishes skills via the 'skillet.skills' entry point"**
- The package is installed but doesn't declare the entry point.
- Or: the package was installed before the entry point was added — try
  `pip install --force-reinstall <pkg>` or `uv pip install --reinstall`.

**"Package X declares a skillet.skills entry point but the directory ... contains no SKILL.md files"**
- The entry point points at the right module, but the `SKILL.md` files
  weren't packaged into the wheel. See the "Make sure the skill files
  end up in the wheel" section above.

**Skill installed but Claude Code doesn't see it**
- Skills live in `.claude/skills/<name>/SKILL.md`. Confirm the path:
  `skillet where` + `ls .claude/skills/`.
- Each skill needs valid frontmatter (`name:` and `description:` at
  minimum). Open the `SKILL.md` and check.
- For project-scoped skills you must be inside the project directory
  when Claude Code starts.

**Skill is the wrong version after upgrading the source package**
- skillet doesn't auto-reinstall. Re-run `skillet install <pkg>` after
  upgrading the source package; previously-owned skills are overwritten.

## What this skill is NOT for

- Authoring the *content* of a SKILL.md (that's a skill-design question,
  not a skillet question).
- Anything involving downloading skills from the network (skillet has no
  network features by design — packages ship skills inside their wheel).
