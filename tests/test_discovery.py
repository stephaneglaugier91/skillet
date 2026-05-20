from __future__ import annotations

import pytest

from skillet.discovery import NoSkillsDeclaredError, PackageNotFoundError, discover, find_source


def test_skillet_self_skill_is_discoverable():
    """skillet ships its own skill via the same entry-point mechanism it
    provides to other packages. This exercises the real importlib
    metadata (no fixture monkeypatching) and catches regressions where
    the entry point is removed from pyproject.toml or the SKILL.md
    moves on disk. (It does NOT verify the SKILL.md is packaged into
    the built wheel — that check lives in the CI build job, since this
    test runs against an editable install that points at the source
    tree directly.)
    """
    src = find_source("skillet")
    assert src.package == "skillet"
    skill_names = [s.name for s in src.skills]
    assert "skillet" in skill_names
    skillet_skill = next(s for s in src.skills if s.name == "skillet")
    assert (skillet_skill.path / "SKILL.md").is_file()


def test_discover_returns_sources_with_skills(fake_package):
    fake_package("alpha", skills={"alpha": "# alpha"})

    sources = discover()

    assert len(sources) == 1
    src = sources[0]
    assert src.package == "alpha"
    assert src.distribution_version == "1.2.3"
    assert [s.name for s in src.skills] == ["alpha"]
    assert src.skills[0].path.is_dir()


def test_find_source_matches_by_package_name(fake_package):
    fake_package("my-pkg", skills={"my-pkg": "# my-pkg"})

    src = find_source("my-pkg")

    assert src.package == "my-pkg"
    assert [s.name for s in src.skills] == ["my-pkg"]


def test_find_source_normalizes_underscore_dash(fake_package):
    fake_package("my-pkg", skills={"main": "# main"})

    src = find_source("my_pkg")

    assert src.package == "my-pkg"


def test_find_source_missing_raises(fake_package):
    fake_package("alpha", skills={"alpha": "# alpha"})

    with pytest.raises(PackageNotFoundError):
        find_source("does-not-exist")


def test_skill_root_with_direct_skill_md(tmp_path, monkeypatch):
    # Build a package whose skills entry-point points to a directory that
    # itself contains SKILL.md (rather than a parent of skill subdirectories).
    import importlib.metadata as md
    import sys
    from types import SimpleNamespace

    site = tmp_path / "site2"
    site.mkdir()
    pkg = site / "betapkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    skills = pkg / "skills"
    skills.mkdir()
    (skills / "__init__.py").write_text("")
    (skills / "SKILL.md").write_text("# beta direct")
    monkeypatch.syspath_prepend(str(site))
    sys.modules.pop("betapkg", None)
    sys.modules.pop("betapkg.skills", None)

    ep = SimpleNamespace(
        name="betapkg",
        value="betapkg.skills",
        group="skillet.skills",
        dist=SimpleNamespace(name="betapkg", version="0.1"),
    )

    def fake_entry_points(*, group=None):
        return [ep] if group == "skillet.skills" else []

    monkeypatch.setattr(md, "entry_points", fake_entry_points)

    src = find_source("betapkg")
    assert [s.name for s in src.skills] == ["skills"]


def test_no_skills_declared_raises(tmp_path, monkeypatch):
    import importlib.metadata as md
    import sys
    from types import SimpleNamespace

    site = tmp_path / "site3"
    site.mkdir()
    pkg = site / "empty"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    skills = pkg / "skills"
    skills.mkdir()
    (skills / "__init__.py").write_text("")
    monkeypatch.syspath_prepend(str(site))
    sys.modules.pop("empty", None)
    sys.modules.pop("empty.skills", None)

    ep = SimpleNamespace(
        name="empty",
        value="empty.skills",
        group="skillet.skills",
        dist=SimpleNamespace(name="empty", version="0.1"),
    )

    def fake_entry_points(*, group=None):
        return [ep] if group == "skillet.skills" else []

    monkeypatch.setattr(md, "entry_points", fake_entry_points)

    with pytest.raises(NoSkillsDeclaredError):
        find_source("empty")
