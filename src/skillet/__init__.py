"""Ship Claude Code skills alongside your Python package."""

from skillet.discovery import Skill, SkillSource, discover, find_source
from skillet.install import InstallResult, install, uninstall, list_installed
from skillet.paths import Target, resolve_target

__version__ = "0.1.0"

__all__ = [
    "Skill",
    "SkillSource",
    "Target",
    "InstallResult",
    "discover",
    "find_source",
    "install",
    "uninstall",
    "list_installed",
    "resolve_target",
    "__version__",
]
