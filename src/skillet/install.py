from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from skillet.discovery import Skill, SkillSource, find_source
from skillet.paths import ResolvedTarget, Target, resolve_target

MANIFEST_VERSION = 1


@dataclass(frozen=True)
class InstallResult:
    package: str
    target: Target
    skills_dir: Path
    installed: tuple[str, ...]
    skipped: tuple[str, ...]
    replaced: tuple[str, ...]


def _load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {"version": MANIFEST_VERSION, "packages": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": MANIFEST_VERSION, "packages": {}}
    data.setdefault("version", MANIFEST_VERSION)
    data.setdefault("packages", {})
    return data


def _save_manifest(path: Path, data: dict) -> None:
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
    *,
    project_root: Path | None = None,
    home: Path | None = None,
    force: bool = False,
) -> InstallResult:
    """Install all skills declared by `package` into the requested target."""
    source = find_source(package)
    resolved = resolve_target(target, project_root=project_root, home=home)
    resolved.skills_dir.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(resolved.manifest_path)
    packages = manifest["packages"]
    existing_entry = packages.get(source.package, {})
    previously_owned = set(existing_entry.get("skills", []))

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

    packages[source.package] = {
        "version": source.distribution_version,
        "skills": sorted(set(previously_owned).union(installed)),
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_manifest(resolved.manifest_path, manifest)

    return InstallResult(
        package=source.package,
        target=target,
        skills_dir=resolved.skills_dir,
        installed=tuple(installed),
        skipped=tuple(skipped),
        replaced=tuple(replaced),
    )


def uninstall(
    package: str,
    target: Target = Target.LOCAL,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> tuple[str, ...]:
    """Uninstall all skills previously installed by `package`. Returns the names removed."""
    resolved = resolve_target(target, project_root=project_root, home=home)
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
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> dict[str, dict]:
    """Return the manifest's packages mapping for the given target."""
    resolved = resolve_target(target, project_root=project_root, home=home)
    return _load_manifest(resolved.manifest_path)["packages"]


def _match_package(packages: dict, package: str) -> tuple[str, dict] | None:
    needle = package.lower().replace("_", "-")
    for key, value in packages.items():
        if key.lower().replace("_", "-") == needle:
            return key, value
    return None


def target_summary(target: Target, *, project_root: Path | None = None, home: Path | None = None) -> ResolvedTarget:
    return resolve_target(target, project_root=project_root, home=home)
