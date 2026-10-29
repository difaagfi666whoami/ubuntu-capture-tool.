import os
import subprocess
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from ubuntu_capture_tool.capture.backend import CaptureBackendError, CaptureCancelled, CaptureRect
from ubuntu_capture_tool.capture import gnome_shell
from ubuntu_capture_tool.capture.gnome_shell import GnomeShellScreenshotBackend


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (3, 2), (20, 30, 40)).save(output, format="PNG")
    return output.getvalue()


def test_area_selection_parses_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gnome_shell.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "(10, -20, 320, 240)", ""),
    )

    assert GnomeShellScreenshotBackend().select_area() == CaptureRect(10, -20, 320, 240)


def test_area_selection_cancel_is_not_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gnome_shell.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "(0, 0, 0, 0)", ""),
    )

    with pytest.raises(CaptureCancelled):
        GnomeShellScreenshotBackend().select_area()


def test_capture_returns_png_bytes_from_unique_temporary_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command, **_kwargs):
        Path(command[-1]).write_bytes(png_bytes())
        return subprocess.CompletedProcess(command, 0, "(true, 'capture.png')", "")

    monkeypatch.setattr(gnome_shell.subprocess, "run", fake_run)

    result = GnomeShellScreenshotBackend().capture(CaptureRect(1, 2, 3, 2))

    assert result.startswith(b"\x89PNG\r\n\x1a\n")


def test_dbus_failure_becomes_actionable_backend_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gnome_shell.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", "UnknownMethod"),
    )

    with pytest.raises(CaptureBackendError, match="UnknownMethod"):
        GnomeShellScreenshotBackend().select_area()


def test_backend_factory_requires_gnome_wayland_and_gdbus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    with pytest.raises(CaptureBackendError, match="GNOME Wayland"):
        GnomeShellScreenshotBackend.from_current_session()

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr(gnome_shell.shutil, "which", lambda _name: None)
    with pytest.raises(CaptureBackendError, match="libglib2.0-bin"):
        GnomeShellScreenshotBackend.from_current_session()
