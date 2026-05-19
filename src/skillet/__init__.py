"""Ship Claude Code skills alongside your Python package."""

from skillet.discovery import (
    NoSkillsDeclaredError,
    PackageNotFoundError,
    Skill,
    SkilletError,
    SkillSource,
    discover,
    find_source,
)
from skillet.install import InstallResult, install, list_installed, uninstall
from skillet.paths import Target, resolve_target

__version__ = "0.1.0"

__all__ = [
    "InstallResult",
    "NoSkillsDeclaredError",
    "PackageNotFoundError",
    "Skill",
    "SkillSource",
    "SkilletError",
    "Target",
    "__version__",
    "discover",
    "find_source",
    "install",
    "list_installed",
    "resolve_target",
    "uninstall",
]
