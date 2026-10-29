"""Install a per-user desktop launcher for the project virtual environment."""

from __future__ import annotations

import os
from pathlib import Path


APP_ID = "ubuntu-capture-tool"
ICON_RELATIVE_PATH = Path("icons/hicolor/scalable/apps") / f"{APP_ID}.svg"


def default_data_home() -> Path:
    configured = os.environ.get("XDG_DATA_HOME")
    if configured and Path(configured).expanduser().is_absolute():
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share"


def _exec_argument(value: str | Path) -> str:
    """Quote one desktop-file Exec argument, including field-code markers."""
    escaped = (
        str(value)
        .replace("%", "%%")
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    return f'"{escaped}"'


def install_desktop_launcher(
    project_root: str | Path,
    *,
    data_home: str | Path | None = None,
) -> Path:
    """Install the app icon and launcher under the user's XDG data directory."""
    root = Path(project_root).expanduser().resolve()
    python = root / ".venv" / "bin" / "python"
    icon_source = root / "assets" / f"{APP_ID}.svg"
    if not python.is_file():
        raise FileNotFoundError(
            f"Project virtual-environment Python was not found at {python}. "
            "Create .venv and install the app before adding its launcher."
        )
    if not icon_source.is_file():
        raise FileNotFoundError(f"Application icon was not found at {icon_source}.")

    user_data = Path(data_home).expanduser() if data_home else default_data_home()
    applications = user_data / "applications"
    icon_path = user_data / ICON_RELATIVE_PATH
    applications.mkdir(parents=True, exist_ok=True)
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    icon_path.write_bytes(icon_source.read_bytes())

    desktop_file = applications / f"{APP_ID}.desktop"
    desktop_file.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Version=1.0",
                "Type=Application",
                "Name=Dipapipi Skrinsyun kustom",
                "Comment=Capture selected screen areas and combine images",
                f"Exec={_exec_argument(python)} -m ubuntu_capture_tool.app",
                # TryExec is a single executable path, not an Exec command line;
                # quoting it makes the quote characters part of the path and
                # causes GNOME to discard the application entry.
                f"TryExec={python}",
                f"Icon={icon_path}",
                "Terminal=false",
                "Categories=Graphics;Utility;",
                "StartupNotify=true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    desktop_file.chmod(0o755)
    return desktop_file


def remove_desktop_launcher(*, data_home: str | Path | None = None) -> tuple[Path, Path]:
    """Remove this app's user-level launcher and icon."""
    user_data = Path(data_home).expanduser() if data_home else default_data_home()
    desktop_file = user_data / "applications" / f"{APP_ID}.desktop"
    icon_path = user_data / ICON_RELATIVE_PATH
    desktop_file.unlink(missing_ok=True)
    icon_path.unlink(missing_ok=True)
    return desktop_file, icon_path
