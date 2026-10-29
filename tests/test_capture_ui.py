import os
from io import BytesIO
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication, QMessageBox

from ubuntu_capture_tool.capture.backend import CaptureBackendError, CaptureCancelled
from ubuntu_capture_tool.capture.ui import CapturePanel


def png_bytes(size: tuple[int, int] = (50, 40)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, (0, 120, 200)).save(output, format="PNG")
    return output.getvalue()


class FakeCaptureBackend:
    def __init__(
        self,
        *,
        capture_error: Exception | None = None,
        cancelled: bool = False,
    ) -> None:
        self.capture_error = capture_error
        self.cancelled = cancelled
        self.captured_frames = 0

    def capture_screen(self) -> bytes:
        if self.capture_error is not None:
            raise self.capture_error
        if self.cancelled:
            raise CaptureCancelled
        self.captured_frames += 1
        return png_bytes()


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_area_selection_saves_portal_result_directly(qt_app: QApplication, tmp_path: Path) -> None:
    backend = FakeCaptureBackend()
    panel = CapturePanel(backend, output_directory=tmp_path / "captures")

    panel.select_area()

    files = list((tmp_path / "captures").glob("capture_*.png"))
    assert backend.captured_frames == 1
    assert len(files) == 1
    with Image.open(files[0]) as image:
        assert image.size == (50, 40)
    assert "Saved selected area" in panel.status.text()
    panel.close()


def test_capture_panel_starts_when_backend_detection_is_disabled(qt_app: QApplication) -> None:
    panel = CapturePanel(detect_backend=False)

    assert not panel.select_button.isEnabled()
    assert panel.status.text() == ""
    panel.close()


def test_cancelled_area_selection_creates_no_capture_file(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = CapturePanel(
        FakeCaptureBackend(cancelled=True),
        output_directory=tmp_path / "captures",
    )

    panel.select_area()

    assert "cancelled" in panel.status.text().lower()
    assert not (tmp_path / "captures").exists()
    panel.close()


def test_backend_capture_error_creates_no_partial_output(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_directory = tmp_path / "captures"
    panel = CapturePanel(
        FakeCaptureBackend(capture_error=CaptureBackendError("portal denied permission")),
        output_directory=output_directory,
    )
    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *_args: messages.append(str(_args[2])),
    )

    panel.select_area()

    assert not output_directory.exists()
    assert messages == ["portal denied permission"]
    assert "Capture failed" in panel.status.text()
    panel.close()
