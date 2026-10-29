"""Local rectangle picker over a screenshot supplied by the desktop portal."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from .backend import CaptureCancelled, CaptureRect


class _ImageSelection(QWidget):
    def __init__(self, pixmap: QPixmap, max_size: tuple[int, int], parent=None) -> None:
        super().__init__(parent)
        self.original = pixmap
        self.preview = pixmap.scaled(
            max_size[0], max_size[1], Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setFixedSize(self.preview.size())
        self._start: QPoint | None = None
        self._end: QPoint | None = None

    def selection(self) -> CaptureRect | None:
        if self._start is None or self._end is None:
            return None
        left, right = sorted((self._start.x(), self._end.x()))
        top, bottom = sorted((self._start.y(), self._end.y()))
        if right <= left or bottom <= top:
            return None
        scale_x = self.original.width() / self.preview.width()
        scale_y = self.original.height() / self.preview.height()
        x = round(left * scale_x)
        y = round(top * scale_y)
        end_x = round(right * scale_x)
        end_y = round(bottom * scale_y)
        return CaptureRect(x, y, max(1, end_x - x), max(1, end_y - y))

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.preview)
        if self._start is not None and self._end is not None:
            selection = QRect(self._start, self._end).normalized()
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawRect(selection)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = self._clamp_point(event.position().toPoint())
            self._end = self._start
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._start is not None:
            self._end = self._clamp_point(event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._start is not None:
            self._end = self._clamp_point(event.position().toPoint())
            self.update()

    def _clamp_point(self, point: QPoint) -> QPoint:
        return QPoint(
            min(max(point.x(), 0), self.width() - 1),
            min(max(point.y(), 0), self.height() - 1),
        )


class ScreenAreaSelector(QDialog):
    """Let the user select a reusable rectangle in full-screen image pixels."""

    def __init__(self, image_data: bytes, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select capture area")
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_data, "PNG"):
            raise ValueError("The screenshot portal returned an unreadable PNG image.")
        screen = self.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        max_width = max(320, int(available.width() * 0.85)) if available else 1200
        max_height = max(240, int(available.height() * 0.75)) if available else 800
        self.image_selection = _ImageSelection(pixmap, (max_width, max_height), self)
        self.hint = QLabel("Drag over the screenshot to select the area to save.")
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Use area")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.hint)
        layout.addWidget(self.image_selection)
        layout.addWidget(self.buttons)
        self.adjustSize()

    def selected_rectangle(self) -> CaptureRect:
        if self.exec() != QDialog.DialogCode.Accepted:
            raise CaptureCancelled("Area selection was cancelled.")
        rectangle = self.image_selection.selection()
        if rectangle is None:
            raise CaptureCancelled("No area was selected.")
        return rectangle
