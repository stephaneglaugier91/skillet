from __future__ import annotations

import importlib.metadata as md
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


class _FakeEntryPoint:
    """Mimics the parts of importlib.metadata.EntryPoint we use."""

    def __init__(self, name: str, value: str, dist_name: str, dist_version: str = "0.0.0"):
        self.name = name
        self.value = value
        self.group = "skillet.skills"
        self.dist = SimpleNamespace(name=dist_name, version=dist_version)


def _make_fake_package(tmp_path: Path, name: str, skills: dict[str, str]) -> Path:
    """Create a fake importable package on disk with a `skills/` directory.

    `skills` maps skill_name → SKILL.md contents. Returns the package directory.
    Safe to call multiple times with the same name (replaces the previous tree).
    """
    import shutil

    pkg_dir = tmp_path / name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    skills_dir = pkg_dir / "skills"
    skills_dir.mkdir()
    (skills_dir / "__init__.py").write_text("")
    for skill_name, body in skills.items():
        sd = skills_dir / skill_name
        sd.mkdir()
        (sd / "SKILL.md").write_text(body)
    return pkg_dir


@pytest.fixture
def fake_package(tmp_path, monkeypatch):
    """Build a fake on-disk package and wire it into entry-point discovery."""
    created_module_names: set[str] = set()

    def _build(name: str = "fakepkg", skills: dict[str, str] | None = None, version: str = "1.2.3"):
        if skills is None:
            skills = {name: f"---\nname: {name}\ndescription: test\n---\n# {name}\n"}
        site = tmp_path / "site"
        site.mkdir(exist_ok=True)
        _make_fake_package(site, name, skills)
        # syspath_prepend is auto-reverted at teardown; raw sys.path.insert is not.
        monkeypatch.syspath_prepend(str(site))

        ep = _FakeEntryPoint(
            name=name, value=f"{name}.skills", dist_name=name, dist_version=version
        )

        def fake_entry_points(*, group: str | None = None):
            if group == "skillet.skills":
                return [ep]
            return []

        monkeypatch.setattr(md, "entry_points", fake_entry_points)
        # Drop any cached import so a re-created package on disk is re-imported.
        sys.modules.pop(name, None)
        sys.modules.pop(f"{name}.skills", None)
        created_module_names.add(name)
        return name

    yield _build

    # Teardown: drop any modules we imported under fake names so a later test
    # that reuses the name doesn't accidentally pick up the stale module object.
    for n in created_module_names:
        sys.modules.pop(n, None)
        sys.modules.pop(f"{n}.skills", None)


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    return project
