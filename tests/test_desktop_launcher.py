from pathlib import Path

import pytest

from ubuntu_capture_tool.desktop_launcher import install_desktop_launcher, remove_desktop_launcher


def test_installs_user_desktop_entry_and_icon(tmp_path: Path) -> None:
    project = tmp_path / "Ubuntu Capture $ Tool"
    python = project / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.touch()
    icon = project / "assets" / "ubuntu-capture-tool.svg"
    icon.parent.mkdir()
    icon.write_text("<svg/>", encoding="utf-8")

    desktop_file = install_desktop_launcher(project, data_home=tmp_path / "user data")

    contents = desktop_file.read_text(encoding="utf-8")
    assert desktop_file == tmp_path / "user data/applications/ubuntu-capture-tool.desktop"
    quoted_python = str(python).replace("$", "\\$")
    assert f'Exec="{quoted_python}" -m ubuntu_capture_tool.app' in contents
    assert "Terminal=false" in contents
    assert "Icon=" in contents
    installed_icon = tmp_path / "user data/icons/hicolor/scalable/apps/ubuntu-capture-tool.svg"
    assert installed_icon.read_text(encoding="utf-8") == "<svg/>"


def test_launcher_requires_project_virtual_environment(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Create .venv"):
        install_desktop_launcher(tmp_path, data_home=tmp_path / "data")


def test_removes_installed_user_desktop_entry_and_icon(tmp_path: Path) -> None:
    project = tmp_path / "project"
    python = project / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.touch()
    icon = project / "assets" / "ubuntu-capture-tool.svg"
    icon.parent.mkdir()
    icon.write_text("<svg/>", encoding="utf-8")
    data_home = tmp_path / "data"
    desktop_file = install_desktop_launcher(project, data_home=data_home)

    removed_desktop, removed_icon = remove_desktop_launcher(data_home=data_home)

    assert removed_desktop == desktop_file
    assert not removed_desktop.exists()
    assert not removed_icon.exists()
