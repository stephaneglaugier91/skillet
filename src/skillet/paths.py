from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Host(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"
    PI = "pi"
    OPENCODE = "opencode"


class Target(StrEnum):
    LOCAL = "local"
    USER = "user"


@dataclass(frozen=True)
class ResolvedTarget:
    target: Target
    skills_dir: Path
    manifest_path: Path
    host: Host = Host.CLAUDE


def resolve_target(
    target: Target,
    host: Host = Host.CLAUDE,
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> ResolvedTarget:
    """Resolve a host/target pair to an absolute skills directory.

    Host-specific conventions:
    - Claude Code: local ``.claude/skills``; user ``~/.claude/skills``
    - Codex: local ``.agents/skills``; user ``~/.agents/skills``
    - pi: local ``.pi/skills``; user ``~/.pi/agent/skills``
    - OpenCode: local ``.opencode/skills``; user config dir ``skills``
    """
    if target is Target.LOCAL:
        root = Path(project_root) if project_root is not None else Path.cwd()
        base = _local_skills_dir(root, host)
    elif target is Target.USER:
        root = Path(home) if home is not None else Path.home()
        base = _user_skills_dir(root, host)
    else:
        raise ValueError(f"Unknown target: {target!r}")

    return ResolvedTarget(
        target=target,
        host=host,
        skills_dir=base,
        manifest_path=base / ".skillet.json",
    )


def _local_skills_dir(root: Path, host: Host) -> Path:
    match host:
        case Host.CLAUDE:
            return root / ".claude" / "skills"
        case Host.CODEX:
            return root / ".agents" / "skills"
        case Host.PI:
            return root / ".pi" / "skills"
        case Host.OPENCODE:
            return root / ".opencode" / "skills"
    raise ValueError(f"Unknown host: {host!r}")


def _user_skills_dir(home: Path, host: Host) -> Path:
    match host:
        case Host.CLAUDE:
            return home / ".claude" / "skills"
        case Host.CODEX:
            return home / ".agents" / "skills"
        case Host.PI:
            return home / ".pi" / "agent" / "skills"
        case Host.OPENCODE:
            return _opencode_config_dir(home) / "skills"
    raise ValueError(f"Unknown host: {host!r}")


def _opencode_config_dir(home: Path) -> Path:
    """Return OpenCode's user config directory without adding dependencies."""
    if opencode_config_dir := os.environ.get("OPENCODE_CONFIG_DIR"):
        return Path(opencode_config_dir).expanduser()
    if xdg_config_home := os.environ.get("XDG_CONFIG_HOME"):
        return Path(xdg_config_home).expanduser() / "opencode"
    return home / ".config" / "opencode"
