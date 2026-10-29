"""Capture controls kept separate from image composition."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .backend import CaptureBackend, CaptureBackendError, CaptureCancelled
from .output import default_capture_directory, save_capture_png
from .xdg_portal import XdgPortalScreenshotBackend


class CapturePanel(QWidget):
    """Area capture through GNOME's interactive screenshot portal."""

    def __init__(
        self,
        backend: CaptureBackend | None = None,
        *,
        output_directory: str | Path | None = None,
        detect_backend: bool = True,
    ) -> None:
        super().__init__()
        self.output_directory = Path(output_directory) if output_directory else default_capture_directory()
        self.backend_message = ""
        if backend is None and detect_backend:
            try:
                backend = XdgPortalScreenshotBackend.from_current_session()
            except CaptureBackendError as exc:
                self.backend_message = str(exc)
        else:
            self.backend_message = ""
        self.backend = backend

        self.output_field = QLineEdit(str(self.output_directory))
        self.status = QLabel(self.backend_message)
        self.status.setWordWrap(True)

        self.select_button = QPushButton("Select area")
        self.select_button.clicked.connect(self.select_area)
        self.browse_button = QPushButton("Choose folder")
        self.browse_button.clicked.connect(self.choose_output_directory)
        self.select_button.setEnabled(self.backend is not None)
        self.browse_button.setEnabled(self.backend is not None)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_field, 1)
        output_row.addWidget(self.browse_button)
        form = QFormLayout()
        form.addRow("Save captures to", output_row)

        buttons = QHBoxLayout()
        buttons.addWidget(self.select_button)
        buttons.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Area capture"))
        layout.addWidget(
            QLabel(
                "Click Select area, choose Selection in GNOME's screenshot overlay, "
                "drag over the area, then confirm the screenshot."
            )
        )
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.setLayout(layout)

    def select_area(self) -> None:
        if self.backend is None:
            return
        try:
            image_data = self.backend.capture_screen()
            saved_path = save_capture_png(image_data, self.output_field.text())
            self.status.setText(f"Saved selected area to {saved_path}.")
        except CaptureCancelled:
            self.status.setText("Area selection cancelled. No screenshot was created.")
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

    def _show_error(self, error: Exception) -> None:
        self.status.setText(f"Capture failed: {error}")
        QMessageBox.critical(self, "Capture failed", str(error))
