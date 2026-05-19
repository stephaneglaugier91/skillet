from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skillet import __version__
from skillet.discovery import (
    NoSkillsDeclared,
    PackageNotFound,
    SkilletError,
    discover,
    find_source,
)
from skillet.install import install, list_installed, target_summary, uninstall
from skillet.paths import Target


def _add_target_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--local",
        dest="target",
        action="store_const",
        const=Target.LOCAL,
        help="Install into ./.claude/skills (default).",
    )
    group.add_argument(
        "--user",
        dest="target",
        action="store_const",
        const=Target.USER,
        help="Install into ~/.claude/skills.",
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Target Claude Code (default). Reserved for future host selectors.",
    )
    parser.set_defaults(target=Target.LOCAL)


def build_parser(prog: str = "skillet", *, fixed_package: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Install Claude Code skills shipped by Python packages.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    install_p = sub.add_parser(
        "install",
        help="Install a package's skills.",
        description="Install all skills declared by a Python package's `skillet.skills` entry point.",
    )
    if fixed_package is None:
        install_p.add_argument("package", help="Name of the installed Python package.")
    _add_target_flags(install_p)
    install_p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite skill directories that already exist but aren't owned by skillet.",
    )

    uninstall_p = sub.add_parser("uninstall", help="Uninstall a package's skills.")
    if fixed_package is None:
        uninstall_p.add_argument("package", help="Name of the package whose skills to remove.")
    _add_target_flags(uninstall_p)

    list_p = sub.add_parser("list", help="List installed skills.")
    _add_target_flags(list_p)
    list_p.add_argument(
        "--available",
        action="store_true",
        help="List packages that declare skills (regardless of install state).",
    )

    where_p = sub.add_parser("where", help="Print the target skills directory.")
    _add_target_flags(where_p)

    parser.set_defaults(_fixed_package=fixed_package)
    return parser


def _cmd_install(args: argparse.Namespace) -> int:
    package = getattr(args, "package", None) or getattr(args, "_fixed_package", None)
    try:
        result = install(package, args.target, force=args.force)
    except (PackageNotFound, NoSkillsDeclared) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except SkilletError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Installed {result.package} into {result.skills_dir}")
    if result.installed:
        for name in result.installed:
            tag = " (replaced)" if name in result.replaced else ""
            print(f"  + {name}{tag}")
    if result.orphans_removed:
        print("Removed (no longer shipped by this version of the package):")
        for name in result.orphans_removed:
            print(f"  - {name}")
    if result.skipped:
        print("Skipped (already present, not owned by skillet; pass --force to overwrite):")
        for name in result.skipped:
            print(f"  - {name}")
    if not result.installed and not result.skipped and not result.orphans_removed:
        print("  (no skills found)")
    return 0


def _cmd_uninstall(args: argparse.Namespace) -> int:
    package = getattr(args, "package", None) or getattr(args, "_fixed_package", None)
    removed = uninstall(package, args.target)
    resolved = target_summary(args.target)
    if not removed:
        print(f"No skills owned by {package!r} were found in {resolved.skills_dir}.")
        return 0
    print(f"Removed {len(removed)} skill(s) from {resolved.skills_dir}:")
    for name in removed:
        print(f"  - {name}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    if args.available:
        sources = discover()
        if not sources:
            print("No installed Python packages publish skills via `skillet.skills`.")
            return 0
        print("Available skills (from installed packages):")
        for src in sources:
            version = f" {src.distribution_version}" if src.distribution_version else ""
            print(f"  {src.package}{version}")
            for skill in src.skills:
                print(f"    • {skill.name}  ({skill.path})")
        return 0

    resolved = target_summary(args.target)
    packages = list_installed(args.target)
    print(f"Skills installed in {resolved.skills_dir}:")
    if not packages:
        print("  (none)")
        return 0
    for pkg, info in sorted(packages.items()):
        version = f" {info.get('version')}" if info.get("version") else ""
        print(f"  {pkg}{version}")
        for name in info.get("skills", []):
            print(f"    • {name}")
    return 0


def _cmd_where(args: argparse.Namespace) -> int:
    resolved = target_summary(args.target)
    print(resolved.skills_dir)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return _dispatch(args)


def package_main(package_name: str, argv: list[str] | None = None, *, prog: str | None = None) -> int:
    """Entry point for package authors who want to expose `<mypkg> skillet ...` as their own CLI.

    Wire it up in your package's `[project.scripts]`, e.g.::

        # pyproject.toml
        [project.scripts]
        "pandas-skillet" = "pandas._skillet_entry:main"

        # pandas/_skillet_entry.py
        from skillet.cli import package_main
        def main():
            raise SystemExit(package_main("pandas"))
    """
    parser = build_parser(prog=prog or f"{package_name} skillet", fixed_package=package_name)
    args = parser.parse_args(argv)
    return _dispatch(args)


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "install":
        return _cmd_install(args)
    if args.command == "uninstall":
        return _cmd_uninstall(args)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "where":
        return _cmd_where(args)
    raise AssertionError(f"unhandled command: {args.command!r}")
