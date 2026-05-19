"""Ship Claude Code skills alongside your Python package."""

from importlib.metadata import PackageNotFoundError as _PkgNotFound
from importlib.metadata import version as _pkg_version

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

try:
    __version__ = _pkg_version("skillet")
except _PkgNotFound:  # pragma: no cover — only hit when running from a
    # source tree without an installed distribution.
    __version__ = "0.0.0+unknown"

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
