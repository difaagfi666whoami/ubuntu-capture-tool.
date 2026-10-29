import json
from pathlib import Path

import pytest

from ubuntu_capture_tool.capture.backend import CaptureRect
from ubuntu_capture_tool.settings.geometry_store import (
    APP_CONFIG_NAME,
    GEOMETRY_FILENAME,
    GeometryStore,
    default_config_directory,
)


def test_geometry_round_trips_injected_path(tmp_path: Path) -> None:
    path = tmp_path / APP_CONFIG_NAME / GEOMETRY_FILENAME
    store = GeometryStore(path)
    rectangle = CaptureRect(x=-120, y=40, width=640, height=360)

    store.save(rectangle)

    assert store.load() == rectangle
    assert json.loads(path.read_text()) == {"x": -120, "y": 40, "width": 640, "height": 360}


def test_invalid_and_corrupt_geometry_recovers_as_none(tmp_path: Path) -> None:
    path = tmp_path / GEOMETRY_FILENAME
    store = GeometryStore(path)

    assert store.load() is None
    path.write_text("{broken")
    assert store.load() is None
    path.write_text(json.dumps({"x": 0, "y": 0, "width": 0, "height": 100}))
    assert store.load() is None
    path.write_text(json.dumps({"x": 0.5, "y": 0, "width": 100, "height": 100}))
    assert store.load() is None


@pytest.mark.parametrize("value", [0, -1])
def test_capture_rect_rejects_nonpositive_dimensions(value: int) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        CaptureRect(0, 0, value, 100)


def test_config_directory_uses_absolute_xdg_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_config_directory() == tmp_path / APP_CONFIG_NAME


def test_config_directory_ignores_relative_xdg_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative-config")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert default_config_directory() == tmp_path / ".config" / APP_CONFIG_NAME

