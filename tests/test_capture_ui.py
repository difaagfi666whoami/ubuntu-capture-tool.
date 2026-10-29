import os
from io import BytesIO
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication, QMessageBox

from ubuntu_capture_tool.capture.backend import CaptureBackendError, CaptureCancelled, CaptureRect
from ubuntu_capture_tool.capture.ui import CapturePanel
from ubuntu_capture_tool.settings.geometry_store import GeometryStore


class FakeCaptureBackend:
    def __init__(
        self,
        rectangle: CaptureRect | None = None,
        *,
        cancel_selection: bool = False,
        capture_error: Exception | None = None,
    ) -> None:
        self.rectangle = rectangle or CaptureRect(10, 20, 4, 3)
        self.cancel_selection = cancel_selection
        self.capture_error = capture_error
        self.captured_frames = 0

    def capture_screen(self) -> bytes:
        if self.capture_error is not None:
            raise self.capture_error
        self.captured_frames += 1
        output = BytesIO()
        Image.new("RGB", (200, 200), (0, 120, 200)).save(output, format="PNG")
        return output.getvalue()


class FakeAreaSelector:
    def __init__(self, _image_data: bytes, _parent=None, *, rectangle: CaptureRect) -> None:
        self.rectangle = rectangle

    def selected_rectangle(self) -> CaptureRect:
        return self.rectangle


class CancelledAreaSelector:
    def __init__(self, _image_data: bytes, _parent=None) -> None:
        pass

    def selected_rectangle(self) -> CaptureRect:
        raise CaptureCancelled


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_select_area_then_capture_persists_geometry_and_saves_file(
    qt_app: QApplication, tmp_path: Path
) -> None:
    store = GeometryStore(tmp_path / "settings" / "capture.json")
    backend = FakeCaptureBackend(CaptureRect(30, 40, 80, 60))
    panel = CapturePanel(
        backend,
        geometry_store=store,
        output_directory=tmp_path / "captures",
        area_selector_factory=lambda data, parent: FakeAreaSelector(
            data, parent, rectangle=backend.rectangle
        ),
    )

    panel.select_area()
    assert store.load() == CaptureRect(30, 40, 80, 60)
    assert panel.capture_button.isEnabled()

    panel.width_field.setValue(50)
    panel.capture_area()

    assert backend.captured_frames == 2
    assert store.load() == CaptureRect(30, 40, 50, 60)
    files = list((tmp_path / "captures").glob("capture_*.png"))
    assert len(files) == 1
    with Image.open(files[0]) as image:
        assert image.size == (50, 60)

    panel.close()

    reopened = CapturePanel(
        backend,
        geometry_store=store,
        output_directory=tmp_path / "captures",
    )
    assert reopened.x_field.value() == 30
    assert reopened.y_field.value() == 40
    assert reopened.width_field.value() == 50
    assert reopened.height_field.value() == 60
    assert reopened.capture_button.isEnabled()
    reopened.close()


def test_cancelled_area_selection_creates_no_capture_file(
    qt_app: QApplication, tmp_path: Path
) -> None:
    store = GeometryStore(tmp_path / "settings" / "capture.json")
    panel = CapturePanel(
        FakeCaptureBackend(cancel_selection=True),
        geometry_store=store,
        output_directory=tmp_path / "captures",
        area_selector_factory=CancelledAreaSelector,
    )

    panel.select_area()

    assert "cancelled" in panel.status.text().lower()
    assert not (tmp_path / "captures").exists()
    assert store.load() is None
    panel.close()


def test_backend_capture_error_creates_no_partial_output(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_directory = tmp_path / "captures"
    store = GeometryStore(tmp_path / "settings" / "capture.json")
    store.save(CaptureRect(0, 0, 10, 10))
    panel = CapturePanel(
        FakeCaptureBackend(capture_error=CaptureBackendError("portal denied permission")),
        geometry_store=store,
        output_directory=output_directory,
    )
    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *_args: messages.append(str(_args[2])),
    )

    panel.capture_area()

    assert not output_directory.exists()
    assert messages == ["portal denied permission"]
    assert "Capture failed" in panel.status.text()
    panel.close()
