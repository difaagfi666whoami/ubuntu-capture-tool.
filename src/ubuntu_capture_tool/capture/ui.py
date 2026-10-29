"""Capture controls kept separate from image composition."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .area_selector import ScreenAreaSelector
from .backend import CaptureBackend, CaptureBackendError, CaptureCancelled, CaptureRect
from .crop import crop_png_to_rectangle
from .output import default_capture_directory, save_capture_png
from .xdg_portal import XdgPortalScreenshotBackend
from ubuntu_capture_tool.settings.geometry_store import GeometryStore


class CapturePanel(QWidget):
    """Area-capture UI using a backend supplied by the current desktop session."""

    def __init__(
        self,
        backend: CaptureBackend | None = None,
        *,
        geometry_store: GeometryStore | None = None,
        output_directory: str | Path | None = None,
        detect_backend: bool = True,
        area_selector_factory: Callable[..., ScreenAreaSelector] = ScreenAreaSelector,
    ) -> None:
        super().__init__()
        self.area_selector_factory = area_selector_factory
        self.geometry_store = geometry_store or GeometryStore()
        self.output_directory = Path(output_directory) if output_directory else default_capture_directory()
        if backend is None and detect_backend:
            try:
                backend = XdgPortalScreenshotBackend.from_current_session()
            except CaptureBackendError as exc:
                self.backend_message = str(exc)
        else:
            self.backend_message = ""
        self.backend = backend
        if self.backend is not None:
            self.backend_message = (
                "GNOME's screenshot portal provides the full desktop image for local area selection and cropping."
            )

        self.x_field = self._integer_field(-100000, 100000)
        self.y_field = self._integer_field(-100000, 100000)
        self.width_field = self._integer_field(1, 100000)
        self.height_field = self._integer_field(1, 100000)
        self.output_field = QLineEdit(str(self.output_directory))
        self.status = QLabel(self.backend_message)
        self.status.setWordWrap(True)

        saved = self.geometry_store.load()
        if saved is not None:
            self._set_rectangle(saved)

        self.select_button = QPushButton("Select area")
        self.select_button.clicked.connect(self.select_area)
        self.capture_button = QPushButton("Capture saved area")
        self.capture_button.clicked.connect(self.capture_area)
        self.browse_button = QPushButton("Choose folder")
        self.browse_button.clicked.connect(self.choose_output_directory)
        self.capture_button.setEnabled(self.backend is not None and saved is not None)
        self.select_button.setEnabled(self.backend is not None)
        self.browse_button.setEnabled(self.backend is not None)

        geometry = QGridLayout()
        geometry.addWidget(QLabel("X"), 0, 0)
        geometry.addWidget(self.x_field, 0, 1)
        geometry.addWidget(QLabel("Y"), 0, 2)
        geometry.addWidget(self.y_field, 0, 3)
        geometry.addWidget(QLabel("Width"), 1, 0)
        geometry.addWidget(self.width_field, 1, 1)
        geometry.addWidget(QLabel("Height"), 1, 2)
        geometry.addWidget(self.height_field, 1, 3)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_field, 1)
        output_row.addWidget(self.browse_button)
        form = QFormLayout()
        form.addRow("Save captures to", output_row)

        buttons = QHBoxLayout()
        buttons.addWidget(self.select_button)
        buttons.addWidget(self.capture_button)
        buttons.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Area capture"))
        layout.addWidget(
            QLabel(
                "Select a region once, then capture the saved rectangle again without resizing it. "
                "GNOME asks permission to provide a full-screen image; the app crops it locally and saves only the selected area. "
                "You can edit coordinates and dimensions before capturing."
            )
        )
        layout.addLayout(geometry)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.setLayout(layout)

    @staticmethod
    def _integer_field(minimum: int, maximum: int) -> QSpinBox:
        field = QSpinBox()
        field.setRange(minimum, maximum)
        return field

    def _set_rectangle(self, rectangle: CaptureRect) -> None:
        self.x_field.setValue(rectangle.x)
        self.y_field.setValue(rectangle.y)
        self.width_field.setValue(rectangle.width)
        self.height_field.setValue(rectangle.height)

    def _rectangle(self) -> CaptureRect:
        return CaptureRect(
            x=self.x_field.value(),
            y=self.y_field.value(),
            width=self.width_field.value(),
            height=self.height_field.value(),
        )

    def select_area(self) -> None:
        if self.backend is None:
            return
        try:
            screen_image = self._capture_desktop_frame()
            rectangle = self.area_selector_factory(screen_image, self).selected_rectangle()
            self.geometry_store.save(rectangle)
            self._set_rectangle(rectangle)
            self.capture_button.setEnabled(True)
            self.status.setText(
                f"Selected {rectangle.width} × {rectangle.height} at ({rectangle.x}, {rectangle.y})."
            )
        except CaptureCancelled:
            self.status.setText("Area selection cancelled. No screenshot was created.")
        except (CaptureBackendError, OSError) as exc:
            self._show_error(exc)

    def capture_area(self) -> None:
        if self.backend is None:
            return
        try:
            rectangle = self._rectangle()
            screen_image = self._capture_desktop_frame()
            image_data = crop_png_to_rectangle(screen_image, rectangle)
            self.geometry_store.save(rectangle)
            saved_path = save_capture_png(image_data, self.output_field.text())
            self.status.setText(
                f"Saved {rectangle.width} × {rectangle.height} screenshot to {saved_path}."
            )
        except CaptureCancelled:
            self.status.setText("Capture cancelled. No screenshot was created.")
        except (CaptureBackendError, OSError, ValueError) as exc:
            self._show_error(exc)

    def choose_output_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose screenshot folder",
            self.output_field.text(),
        )
        if selected:
            self.output_field.setText(selected)

    def _capture_desktop_frame(self) -> bytes:
        """Hide this window so it is not included in the desktop image."""
        window = self.window()
        window.showMinimized()
        QApplication.processEvents()
        try:
            return self.backend.capture_screen()
        finally:
            window.showNormal()
            window.raise_()
            window.activateWindow()

    def _show_error(self, error: Exception) -> None:
        self.status.setText(f"Capture failed: {error}")
        QMessageBox.critical(self, "Capture failed", str(error))
