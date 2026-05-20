from __future__ import annotations

import argparse
import sys

from skillet import __version__
from skillet.discovery import (
    NoSkillsDeclaredError,
    PackageNotFoundError,
    SkilletError,
    discover,
)
from skillet.install import install, list_installed, target_summary, uninstall
from skillet.paths import Host, Target


def _add_target_flags(parser: argparse.ArgumentParser) -> None:
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--local",
        dest="target",
        action="store_const",
        const=Target.LOCAL,
        help="Install into the current project's skills directory (default).",
    )
    target_group.add_argument(
        "--user",
        dest="target",
        action="store_const",
        const=Target.USER,
        help="Install into the current user's skills directory.",
    )

    host_group = parser.add_mutually_exclusive_group()
    host_group.add_argument(
        "--host",
        dest="host",
        type=Host,
        choices=list(Host),
        metavar="HOST",
        help="Target agent host: claude, codex, pi, or opencode.",
    )
    host_group.add_argument(
        "--claude",
        dest="host",
        action="store_const",
        const=Host.CLAUDE,
        help="Target Claude Code (default).",
    )
    host_group.add_argument(
        "--codex",
        dest="host",
        action="store_const",
        const=Host.CODEX,
        help="Target Codex via .agents/skills.",
    )
    host_group.add_argument(
        "--pi",
        dest="host",
        action="store_const",
        const=Host.PI,
        help="Target pi.",
    )
    host_group.add_argument(
        "--opencode",
        dest="host",
        action="store_const",
        const=Host.OPENCODE,
        help="Target OpenCode.",
    )
    parser.set_defaults(target=Target.LOCAL, host=Host.CLAUDE)


def build_parser(
    prog: str = "skillet", *, fixed_package: str | None = None
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Install agent skills shipped by Python packages.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    install_p = sub.add_parser(
        "install",
        help="Install a package's skills.",
        description="Install all agent skills declared by a Python package's `skillet.skills` entry point.",
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


def _resolve_package(args: argparse.Namespace) -> str:
    package = getattr(args, "package", None) or getattr(args, "_fixed_package", None)
    if not package:
        raise AssertionError("argparse should have required a package argument")
    return str(package)


def _cmd_install(args: argparse.Namespace) -> int:
    package = _resolve_package(args)
    try:
        result = install(package, args.target, args.host, force=args.force)
    except (PackageNotFoundError, NoSkillsDeclaredError) as exc:
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
    package = _resolve_package(args)
    removed = uninstall(package, args.target, args.host)
    resolved = target_summary(args.target, args.host)
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

    resolved = target_summary(args.target, args.host)
    packages = list_installed(args.target, args.host)
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
    resolved = target_summary(args.target, args.host)
    print(resolved.skills_dir)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return _dispatch(args)


def package_main(
    package_name: str, argv: list[str] | None = None, *, prog: str | None = None
) -> int:
    """Entry point for package authors who want to expose `<mypkg> skillet ...` as their own CLI.

    Wire it up in your package's `[project.scripts]`, e.g.::

        # pyproject.toml
        [project.scripts]
        "pandas-skillet" = "pandas._skillet_entry:main"

        # pandas/_skillet_entry.py
        from skillet.cli import package_main
        def main():
            # Pass `prog=` so `--help` reports the installed script
            # name; the default is "<pkg> skillet" (with a space).
            raise SystemExit(package_main("pandas", prog="pandas-skillet"))
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
