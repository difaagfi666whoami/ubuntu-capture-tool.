import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from ubuntu_capture_tool.capture.area_selector import _ImageSelection
from ubuntu_capture_tool.capture.backend import CaptureRect


def test_preview_selection_maps_to_original_image_pixels() -> None:
    app = QApplication.instance() or QApplication([])
    selector = _ImageSelection(QPixmap(400, 200), (200, 200))
    selector._start = QPoint(10, 20)
    selector._end = QPoint(110, 70)

    assert selector.selection() == CaptureRect(20, 40, 200, 100)
    selector.close()
    app.processEvents()
