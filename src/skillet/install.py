from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from skillet.discovery import Skill, find_source
from skillet.paths import Host, ResolvedTarget, Target, resolve_target

MANIFEST_VERSION = 1

Manifest = dict[str, Any]
PackageEntry = dict[str, Any]


@dataclass(frozen=True)
class InstallResult:
    package: str
    target: Target
    skills_dir: Path
    installed: tuple[str, ...]
    skipped: tuple[str, ...]
    replaced: tuple[str, ...]
    orphans_removed: tuple[str, ...] = ()
    host: Host = Host.CLAUDE


def _load_manifest(path: Path) -> Manifest:
    empty: Manifest = {"version": MANIFEST_VERSION, "packages": {}}
    if not path.is_file():
        return empty
    try:
        data: Manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty
    data.setdefault("version", MANIFEST_VERSION)
    data.setdefault("packages", {})
    return data


def _save_manifest(path: Path, data: Manifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_skill(source: Skill, dest: Path) -> None:
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    shutil.copytree(source.path, dest)


def install(
    package: str,
    target: Target = Target.LOCAL,
    host: Host = Host.CLAUDE,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
    force: bool = False,
) -> InstallResult:
    """Install all skills declared by `package` into the requested host target."""
    source = find_source(package)
    resolved = resolve_target(target, host, project_root=project_root, home=home)
    resolved.skills_dir.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(resolved.manifest_path)
    packages = manifest["packages"]
    had_existing_entry = source.package in packages
    previously_owned = set(packages.get(source.package, {}).get("skills", []))
    source_names = {s.name for s in source.skills}

    # Clean up skills we previously owned that this version of the source no
    # longer ships. Without this, the manifest (and the user's skills dir) would
    # accumulate stale files across upgrades.
    orphans_removed: list[str] = []
    for orphan in sorted(previously_owned - source_names):
        orphan_path = resolved.skills_dir / orphan
        if orphan_path.is_dir():
            shutil.rmtree(orphan_path)
            orphans_removed.append(orphan)
        elif orphan_path.exists():
            orphan_path.unlink()
            orphans_removed.append(orphan)

    installed: list[str] = []
    skipped: list[str] = []
    replaced: list[str] = []

    for skill in source.skills:
        dest = resolved.skills_dir / skill.name
        if dest.exists() and not force and skill.name not in previously_owned:
            skipped.append(skill.name)
            continue
        if dest.exists():
            replaced.append(skill.name)
        _copy_skill(skill, dest)
        installed.append(skill.name)

    if installed:
        packages[source.package] = {
            "version": source.distribution_version,
            "skills": sorted(installed),
            "installed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        _save_manifest(resolved.manifest_path, manifest)
    elif had_existing_entry and not source_names:
        # Source no longer ships any skills; remove the stale entry.
        del packages[source.package]
        _save_manifest(resolved.manifest_path, manifest)
    elif orphans_removed:
        # Orphans were cleaned even though nothing new was installed.
        _save_manifest(resolved.manifest_path, manifest)
    # else: nothing was placed and no prior state existed — leave manifest alone.

    return InstallResult(
        package=source.package,
        target=target,
        skills_dir=resolved.skills_dir,
        installed=tuple(installed),
        skipped=tuple(skipped),
        replaced=tuple(replaced),
        orphans_removed=tuple(orphans_removed),
        host=host,
    )


def uninstall(
    package: str,
    target: Target = Target.LOCAL,
    host: Host = Host.CLAUDE,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> tuple[str, ...]:
    """Uninstall all skills previously installed by `package`. Returns the names removed."""
    resolved = resolve_target(target, host, project_root=project_root, home=home)
    manifest = _load_manifest(resolved.manifest_path)
    packages = manifest["packages"]

    entry = _match_package(packages, package)
    if entry is None:
        return ()

    pkg_key, pkg_data = entry
    removed: list[str] = []
    for name in pkg_data.get("skills", []):
        skill_path = resolved.skills_dir / name
        if skill_path.is_dir():
            shutil.rmtree(skill_path)
            removed.append(name)
        elif skill_path.exists():
            skill_path.unlink()
            removed.append(name)

    del packages[pkg_key]
    _save_manifest(resolved.manifest_path, manifest)
    return tuple(removed)


def list_installed(
    target: Target = Target.LOCAL,
    host: Host = Host.CLAUDE,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> dict[str, PackageEntry]:
    """Return the manifest's packages mapping for the given host target."""
    resolved = resolve_target(target, host, project_root=project_root, home=home)
    packages: dict[str, PackageEntry] = _load_manifest(resolved.manifest_path)["packages"]
    return packages


def _match_package(
    packages: dict[str, PackageEntry], package: str
) -> tuple[str, PackageEntry] | None:
    needle = package.lower().replace("_", "-")
    for key, value in packages.items():
        if key.lower().replace("_", "-") == needle:
            return key, value
    return None


def target_summary(
    target: Target,
    host: Host = Host.CLAUDE,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> ResolvedTarget:
    return resolve_target(target, host, project_root=project_root, home=home)
