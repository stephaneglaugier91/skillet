from __future__ import annotations

import json

from skillet.install import install, list_installed, uninstall
from skillet.paths import Target, resolve_target


def test_install_local_copies_skills_and_writes_manifest(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "---\nname: alpha\n---\n# alpha\n"})

    result = install("alpha", Target.LOCAL)

    skill_path = fake_project / ".claude" / "skills" / "alpha"
    assert skill_path.is_dir()
    assert (skill_path / "SKILL.md").read_text().startswith("---")
    assert result.installed == ("alpha",)
    assert result.skipped == ()

    manifest = json.loads((fake_project / ".claude" / "skills" / ".skillet.json").read_text())
    assert "alpha" in manifest["packages"]
    assert manifest["packages"]["alpha"]["skills"] == ["alpha"]
    assert manifest["packages"]["alpha"]["version"] == "1.2.3"


def test_install_user_target_uses_home(fake_package, fake_home):
    fake_package("beta", skills={"beta": "# beta"})

    install("beta", Target.USER)

    assert (fake_home / ".claude" / "skills" / "beta" / "SKILL.md").is_file()


def test_install_multiple_skills(fake_package, fake_project):
    fake_package("multi", skills={"one": "# one", "two": "# two"})

    result = install("multi", Target.LOCAL)

    assert set(result.installed) == {"one", "two"}
    assert (fake_project / ".claude" / "skills" / "one" / "SKILL.md").is_file()
    assert (fake_project / ".claude" / "skills" / "two" / "SKILL.md").is_file()


def test_install_skips_unowned_existing_dir_without_force(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha-new"})
    existing = fake_project / ".claude" / "skills" / "alpha"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("# alpha-existing")

    result = install("alpha", Target.LOCAL)

    assert result.installed == ()
    assert result.skipped == ("alpha",)
    assert (existing / "SKILL.md").read_text() == "# alpha-existing"


def test_install_with_all_skips_does_not_create_manifest_entry(fake_package, fake_project):
    """When every skill is skipped on a fresh install, we shouldn't record an
    empty manifest entry that falsely claims skillet owns the package."""
    fake_package("alpha", skills={"alpha": "# new"})
    existing = fake_project / ".claude" / "skills" / "alpha"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("# preexisting")

    install("alpha", Target.LOCAL)

    manifest_path = fake_project / ".claude" / "skills" / ".skillet.json"
    # Either no manifest at all, or no entry for this package.
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assert "alpha" not in manifest["packages"]
    assert "alpha" not in list_installed(Target.LOCAL)


def test_install_force_overwrites_unowned_dir(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha-new"})
    existing = fake_project / ".claude" / "skills" / "alpha"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("# alpha-existing")

    result = install("alpha", Target.LOCAL, force=True)

    assert result.installed == ("alpha",)
    assert result.replaced == ("alpha",)
    assert (existing / "SKILL.md").read_text() == "# alpha-new"


def test_reinstall_overwrites_previously_owned_skill(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# v1"})
    install("alpha", Target.LOCAL)
    fake_package("alpha", skills={"alpha": "# v2"})

    result = install("alpha", Target.LOCAL)

    assert result.installed == ("alpha",)
    assert result.skipped == ()
    skill_md = fake_project / ".claude" / "skills" / "alpha" / "SKILL.md"
    assert skill_md.read_text() == "# v2"


def test_reinstall_removes_orphan_skills_no_longer_shipped(fake_package, fake_project):
    """When a package previously shipped skills 'a' and 'b' but the new version
    only ships 'a', the orphan 'b' should be removed from disk and the manifest
    so a subsequent uninstall doesn't get confused."""
    fake_package("alpha", skills={"a": "# a-v1", "b": "# b-v1"})
    install("alpha", Target.LOCAL)
    fake_package("alpha", skills={"a": "# a-v2"})

    result = install("alpha", Target.LOCAL)

    skills_dir = fake_project / ".claude" / "skills"
    assert (skills_dir / "a").is_dir()
    assert not (skills_dir / "b").exists()
    assert result.installed == ("a",)
    assert result.orphans_removed == ("b",)

    manifest = json.loads((skills_dir / ".skillet.json").read_text())
    assert manifest["packages"]["alpha"]["skills"] == ["a"]


def test_uninstall_removes_skills_and_manifest_entry(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha"})
    install("alpha", Target.LOCAL)

    removed = uninstall("alpha", Target.LOCAL)

    assert removed == ("alpha",)
    assert not (fake_project / ".claude" / "skills" / "alpha").exists()

    manifest = json.loads((fake_project / ".claude" / "skills" / ".skillet.json").read_text())
    assert "alpha" not in manifest["packages"]


def test_uninstall_unknown_package_is_noop(fake_project):
    # Manifest doesn't exist yet
    resolved = resolve_target(Target.LOCAL)
    resolved.skills_dir.mkdir(parents=True, exist_ok=True)
    removed = uninstall("ghost", Target.LOCAL)
    assert removed == ()


def test_list_installed_returns_manifest_packages(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha"})
    install("alpha", Target.LOCAL)

    packages = list_installed(Target.LOCAL)

    assert "alpha" in packages
    assert packages["alpha"]["skills"] == ["alpha"]


def test_resolve_target_paths(tmp_path):
    local = resolve_target(Target.LOCAL, project_root=tmp_path)
    user = resolve_target(Target.USER, home=tmp_path)
    assert local.skills_dir == tmp_path / ".claude" / "skills"
    assert user.skills_dir == tmp_path / ".claude" / "skills"
    assert local.manifest_path == local.skills_dir / ".skillet.json"
