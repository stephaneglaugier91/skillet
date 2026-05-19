from __future__ import annotations

import importlib
import importlib.metadata as md
from dataclasses import dataclass
from pathlib import Path

ENTRY_POINT_GROUP = "skillet.skills"


@dataclass(frozen=True)
class Skill:
    """A single skill (one directory containing SKILL.md)."""

    name: str
    path: Path


@dataclass(frozen=True)
class SkillSource:
    """A package that ships one or more skills via the `skillet.skills` entry point."""

    package: str
    distribution_version: str | None
    root: Path
    skills: tuple[Skill, ...]

    def __iter__(self):
        return iter(self.skills)


class SkilletError(Exception):
    pass


class PackageNotFound(SkilletError):
    pass


class NoSkillsDeclared(SkilletError):
    pass


def _entry_points_for_group(group: str) -> list[md.EntryPoint]:
    eps = md.entry_points()
    # importlib.metadata API differs slightly across versions; both forms are supported.
    select = getattr(eps, "select", None)
    if callable(select):
        return list(select(group=group))
    return list(eps.get(group, []))  # type: ignore[union-attr]


def _resolve_entry_point_dir(ep: md.EntryPoint) -> Path:
    """The entry point value is a dotted module path. We import it and use its
    on-disk directory as the root that holds skill subdirectories.
    """
    module_name = ep.value.split(":", 1)[0].strip()
    module = importlib.import_module(module_name)
    file = getattr(module, "__file__", None)
    if file is None:
        # Namespace package: try the first __path__ entry.
        paths = list(getattr(module, "__path__", []))
        if not paths:
            raise SkilletError(
                f"Cannot resolve filesystem location for entry point {ep.name!r} → {ep.value!r}"
            )
        return Path(paths[0]).resolve()
    return Path(file).resolve().parent


def _collect_skills(root: Path) -> tuple[Skill, ...]:
    """A skill is any directory under `root` that contains a SKILL.md, plus
    `root` itself if it directly contains a SKILL.md.
    """
    if not root.exists() or not root.is_dir():
        return ()

    skills: list[Skill] = []
    if (root / "SKILL.md").is_file():
        skills.append(Skill(name=root.name, path=root))
    else:
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").is_file():
                skills.append(Skill(name=child.name, path=child))
    return tuple(skills)


def discover() -> list[SkillSource]:
    """Discover all installed packages that publish skills via the `skillet.skills` entry point."""
    sources: list[SkillSource] = []
    for ep in _entry_points_for_group(ENTRY_POINT_GROUP):
        try:
            root = _resolve_entry_point_dir(ep)
        except (ModuleNotFoundError, SkilletError):
            continue
        skills = _collect_skills(root)
        if not skills:
            continue
        dist_name = ep.dist.name if ep.dist else ep.name
        dist_version = ep.dist.version if ep.dist else None
        sources.append(
            SkillSource(
                package=dist_name,
                distribution_version=dist_version,
                root=root,
                skills=skills,
            )
        )
    return sources


def find_source(package: str) -> SkillSource:
    """Find the SkillSource for a specific package name.

    Matches either the entry-point name or the distribution name (case-insensitive,
    with `-`/`_` treated as equivalent).
    """
    needle = _normalize(package)
    for ep in _entry_points_for_group(ENTRY_POINT_GROUP):
        dist_name = ep.dist.name if ep.dist else ep.name
        if _normalize(dist_name) != needle and _normalize(ep.name) != needle:
            continue
        try:
            root = _resolve_entry_point_dir(ep)
        except ModuleNotFoundError as exc:
            raise PackageNotFound(
                f"Package {package!r} declares skills but its module {exc.name!r} is not importable."
            ) from exc
        skills = _collect_skills(root)
        if not skills:
            raise NoSkillsDeclared(
                f"Package {package!r} declares a {ENTRY_POINT_GROUP} entry point but the "
                f"directory {root} contains no SKILL.md files."
            )
        return SkillSource(
            package=dist_name,
            distribution_version=ep.dist.version if ep.dist else None,
            root=root,
            skills=skills,
        )
    raise PackageNotFound(
        f"No installed package named {package!r} publishes skills via the "
        f"{ENTRY_POINT_GROUP!r} entry point."
    )


def _normalize(name: str) -> str:
    return name.lower().replace("_", "-")
