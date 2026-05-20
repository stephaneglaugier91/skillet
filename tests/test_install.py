from __future__ import annotations

import json

from skillet.install import install, list_installed, uninstall
from skillet.paths import Host, Target, resolve_target


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


def test_install_codex_target_uses_agents_skills(fake_package, fake_project):
    fake_package("beta", skills={"beta": "# beta"})

    result = install("beta", Target.LOCAL, Host.CODEX)

    assert result.host is Host.CODEX
    assert (fake_project / ".agents" / "skills" / "beta" / "SKILL.md").is_file()
    assert not (fake_project / ".claude").exists()


def test_installed_manifests_are_separate_per_host(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha"})

    install("alpha", Target.LOCAL, Host.CLAUDE)
    install("alpha", Target.LOCAL, Host.PI)

    assert "alpha" in list_installed(Target.LOCAL, Host.CLAUDE)
    assert "alpha" in list_installed(Target.LOCAL, Host.PI)
    assert (fake_project / ".claude" / "skills" / ".skillet.json").is_file()
    assert (fake_project / ".pi" / "skills" / ".skillet.json").is_file()

    uninstall("alpha", Target.LOCAL, Host.CLAUDE)

    assert not (fake_project / ".claude" / "skills" / "alpha").exists()
    assert (fake_project / ".pi" / "skills" / "alpha" / "SKILL.md").is_file()


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


def test_resolve_target_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENCODE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    cases = [
        (Host.CLAUDE, ".claude/skills", ".claude/skills"),
        (Host.CODEX, ".agents/skills", ".agents/skills"),
        (Host.PI, ".pi/skills", ".pi/agent/skills"),
        (Host.OPENCODE, ".opencode/skills", ".config/opencode/skills"),
    ]

    for host, local_suffix, user_suffix in cases:
        local = resolve_target(Target.LOCAL, host, project_root=tmp_path)
        user = resolve_target(Target.USER, host, home=tmp_path)
        assert local.host is host
        assert user.host is host
        assert local.skills_dir == tmp_path / local_suffix
        assert user.skills_dir == tmp_path / user_suffix
        assert local.manifest_path == local.skills_dir / ".skillet.json"


def test_resolve_opencode_user_target_respects_config_env(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCODE_CONFIG_DIR", str(tmp_path / "custom-opencode"))

    resolved = resolve_target(Target.USER, Host.OPENCODE, home=tmp_path / "home")

    assert resolved.skills_dir == tmp_path / "custom-opencode" / "skills"
