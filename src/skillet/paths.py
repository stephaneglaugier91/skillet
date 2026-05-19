from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Target(str, Enum):
    LOCAL = "local"
    USER = "user"


@dataclass(frozen=True)
class ResolvedTarget:
    target: Target
    skills_dir: Path
    manifest_path: Path


def resolve_target(target: Target, *, project_root: Path | None = None, home: Path | None = None) -> ResolvedTarget:
    """Resolve a Target enum to an absolute skills directory.

    - LOCAL → <project_root>/.claude/skills
    - USER  → <home>/.claude/skills
    """
    if target is Target.LOCAL:
        root = Path(project_root) if project_root is not None else Path.cwd()
        base = root / ".claude" / "skills"
    elif target is Target.USER:
        root = Path(home) if home is not None else Path.home()
        base = root / ".claude" / "skills"
    else:
        raise ValueError(f"Unknown target: {target!r}")

    return ResolvedTarget(
        target=target,
        skills_dir=base,
        manifest_path=base / ".skillet.json",
    )
