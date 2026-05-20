from __future__ import annotations

from pathlib import Path

import pytest

import skillet
from skillet.cli import main, package_main


def test_version_is_resolved_from_installed_metadata():
    # If this fails, the package isn't installed (e.g., somebody added a
    # raw `python` invocation without `uv sync` first), or the metadata
    # name in pyproject.toml drifted from "skillet".
    assert skillet.__version__ != "0.0.0+unknown"
    assert skillet.__version__  # non-empty


def test_cli_install_local(fake_package, fake_project, capsys):
    fake_package("alpha", skills={"alpha": "# alpha"})

    rc = main(["install", "alpha", "--local"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Installed alpha" in out
    assert (fake_project / ".claude" / "skills" / "alpha" / "SKILL.md").is_file()


def test_cli_install_unknown_package_returns_error(fake_project, capsys):
    rc = main(["install", "nope"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "error:" in err.lower()


def test_cli_list_available(fake_package, fake_project, capsys):
    fake_package("alpha", skills={"alpha": "# alpha"})

    rc = main(["list", "--available"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out


def test_cli_list_installed(fake_package, fake_project, capsys):
    fake_package("alpha", skills={"alpha": "# alpha"})
    main(["install", "alpha"])
    capsys.readouterr()  # drain

    rc = main(["list"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out


def test_cli_uninstall(fake_package, fake_project, capsys):
    fake_package("alpha", skills={"alpha": "# alpha"})
    main(["install", "alpha"])
    capsys.readouterr()

    rc = main(["uninstall", "alpha"])

    assert rc == 0
    assert not (fake_project / ".claude" / "skills" / "alpha").exists()


def test_cli_where(fake_project, capsys):
    rc = main(["where"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    # Compare via Path so the test works on Windows (backslash separators) too.
    assert out.endswith(str(Path(".claude") / "skills"))


def test_package_main_does_not_require_package_arg(fake_package, fake_project, capsys):
    fake_package("alpha", skills={"alpha": "# alpha"})

    rc = package_main("alpha", ["install", "--local"])

    assert rc == 0
    assert (fake_project / ".claude" / "skills" / "alpha" / "SKILL.md").is_file()


def test_package_main_rejects_passing_other_package(fake_package, fake_project):
    fake_package("alpha", skills={"alpha": "# alpha"})

    with pytest.raises(SystemExit):
        # The fixed-package CLI doesn't accept a positional package argument.
        package_main("alpha", ["install", "other-pkg"])
