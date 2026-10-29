"""Experimental screenshot adapter for GNOME Shell's session-bus API.

This backend must be tested on the declared Ubuntu GNOME Wayland target before
being described as supported.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

from .backend import CaptureBackendError, CaptureCancelled, CaptureRect

DESTINATION = "org.gnome.Shell"
OBJECT_PATH = "/org/gnome/Shell/Screenshot"
INTERFACE = "org.gnome.Shell.Screenshot"
_RECTANGLE_RESPONSE = re.compile(
    r"^\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)$"
)


class GnomeShellScreenshotBackend:
    """Use GNOME Shell to select a region and capture explicit screen pixels."""

    def __init__(
        self,
        *,
        gdbus_path: str = "gdbus",
        environment: Mapping[str, str] | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        self.gdbus_path = gdbus_path
        self.environment = dict(environment) if environment is not None else dict(os.environ)
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_current_session(cls) -> GnomeShellScreenshotBackend:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        if session_type != "wayland" or "GNOME" not in desktop:
            raise CaptureBackendError(
                "Area capture currently requires a GNOME Wayland session."
            )
        gdbus_path = shutil.which("gdbus")
        if gdbus_path is None:
            raise CaptureBackendError(
                "The gdbus command is missing. Install the Ubuntu package libglib2.0-bin."
            )
        return cls(gdbus_path=gdbus_path)

    def select_area(self) -> CaptureRect:
        result = self._call("SelectArea")
        match = _RECTANGLE_RESPONSE.fullmatch(result.strip())
        if match is None:
            raise CaptureBackendError(
                f"GNOME returned an unexpected area-selection response: {result.strip() or '(empty)'}"
            )
        x, y, width, height = (int(value) for value in match.groups())
        if width == 0 or height == 0:
            raise CaptureCancelled("Area selection was cancelled.")
        try:
            return CaptureRect(x=x, y=y, width=width, height=height)
        except ValueError as exc:
            raise CaptureBackendError("GNOME returned invalid area geometry.") from exc

    def capture(self, rectangle: CaptureRect) -> bytes:
        with tempfile.TemporaryDirectory(prefix="ubuntu-capture-tool-") as temp_dir:
            output_path = Path(temp_dir) / "capture.png"
            self._call(
                "ScreenshotArea",
                str(rectangle.x),
                str(rectangle.y),
                str(rectangle.width),
                str(rectangle.height),
                "false",
                str(output_path),
            )
            try:
                image_data = output_path.read_bytes()
            except OSError as exc:
                raise CaptureBackendError(
                    "GNOME did not create the screenshot file. Check the rectangle and desktop session."
                ) from exc
        if not image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise CaptureBackendError("GNOME returned a file that is not a PNG image.")
        return image_data

    def _call(self, method: str, *arguments: str) -> str:
        command: Sequence[str] = (
            self.gdbus_path,
            "call",
            "--session",
            "--dest",
            DESTINATION,
            "--object-path",
            OBJECT_PATH,
            "--method",
            f"{INTERFACE}.{method}",
            *arguments,
        )
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=self.environment,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CaptureBackendError("The gdbus command could not be started.") from exc
        except subprocess.TimeoutExpired as exc:
            raise CaptureBackendError(
                "GNOME Shell did not respond to the screenshot request in time."
            ) from exc
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "Unknown D-Bus error."
            raise CaptureBackendError(f"GNOME screenshot request failed: {detail}")
        return result.stdout.strip()
