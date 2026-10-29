"""Persistence for the last area-capture rectangle."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from ubuntu_capture_tool.capture.backend import CaptureRect

APP_CONFIG_NAME = "ubuntu-capture-tool"
GEOMETRY_FILENAME = "capture-geometry.json"


def default_config_directory() -> Path:
    """Return the XDG config directory, honoring only absolute XDG overrides."""
    configured = os.environ.get("XDG_CONFIG_HOME")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_absolute():
            return candidate / APP_CONFIG_NAME
    return Path.home() / ".config" / APP_CONFIG_NAME


class GeometryStore:
    """Read and atomically write a validated capture rectangle."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_config_directory() / GEOMETRY_FILENAME

    def load(self) -> CaptureRect | None:
        """Return the saved rectangle, or None for absent/corrupt/invalid settings."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None
            return CaptureRect(
                x=data["x"],
                y=data["y"],
                width=data["width"],
                height=data["height"],
            )
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None

    def save(self, rectangle: CaptureRect) -> None:
        """Persist a rectangle with an atomic replacement of the settings file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as output:
                temp_path = Path(output.name)
                json.dump(
                    {
                        "x": rectangle.x,
                        "y": rectangle.y,
                        "width": rectangle.width,
                        "height": rectangle.height,
                    },
                    output,
                )
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
