"""Desktop application entry point."""

from __future__ import annotations

from io import BytesIO
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .image_merge import Alignment, ImageMergeError, MergeOptions, Orientation, compose_images, save_png


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ubuntu Capture Tool")
        self.resize(900, 650)
        self._preview_pixmap: QPixmap | None = None

        self.files = QListWidget()
        self.files.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.files.model().rowsMoved.connect(self.refresh_preview)
        self.preview = QLabel("Add at least two images to preview the combined result.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480, 320)
        self.preview.setStyleSheet("background: #20242b; color: #d7dce2; border-radius: 8px;")

        self.orientation = QComboBox()
        self.orientation.addItem("Vertical", Orientation.VERTICAL)
        self.orientation.addItem("Horizontal", Orientation.HORIZONTAL)
        self.orientation.currentIndexChanged.connect(self.refresh_preview)

        self.alignment = QComboBox()
        for label, value in (("Start", Alignment.START), ("Center", Alignment.CENTER), ("End", Alignment.END)):
            self.alignment.addItem(label, value)
        self.alignment.setCurrentIndex(1)
        self.alignment.currentIndexChanged.connect(self.refresh_preview)

        add_button = QPushButton("Add images")
        add_button.clicked.connect(self.add_images)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self.remove_selected)
        up_button = QPushButton("Move up")
        up_button.clicked.connect(lambda: self.move_item(-1))
        down_button = QPushButton("Move down")
        down_button.clicked.connect(lambda: self.move_item(1))
        export_button = QPushButton("Export PNG")
        export_button.clicked.connect(self.export_png)

        controls = QHBoxLayout()
        controls.addWidget(add_button)
        controls.addWidget(remove_button)
        controls.addWidget(up_button)
        controls.addWidget(down_button)
        controls.addStretch(1)
        controls.addWidget(QLabel("Layout"))
        controls.addWidget(self.orientation)
        controls.addWidget(QLabel("Alignment"))
        controls.addWidget(self.alignment)

        body = QHBoxLayout()
        body.addWidget(self.files, 1)
        body.addWidget(self.preview, 2)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addLayout(body, 1)
        layout.addWidget(export_button, alignment=Qt.AlignmentFlag.AlignRight)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Images are processed locally. No screenshot backend is enabled yet.")

    def add_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp)",
        )
        for path in paths:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.files.addItem(item)
        self.refresh_preview()

    def remove_selected(self) -> None:
        for item in self.files.selectedItems():
            self.files.takeItem(self.files.row(item))
        self.refresh_preview()

    def move_item(self, direction: int) -> None:
        row = self.files.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= self.files.count():
            return
        item = self.files.takeItem(row)
        self.files.insertItem(target, item)
        self.files.setCurrentRow(target)
        self.refresh_preview()

    def _options(self) -> MergeOptions:
        return MergeOptions(
            orientation=self.orientation.currentData(),
            alignment=self.alignment.currentData(),
        )

    def _paths(self) -> list[str]:
        return [self.files.item(index).data(Qt.ItemDataRole.UserRole) for index in range(self.files.count())]

    def refresh_preview(self, *_args) -> None:
        if self.files.count() < 2:
            self._preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Add at least two images to preview the combined result.")
            return
        try:
            image = compose_images(self._paths(), self._options())
            try:
                image.thumbnail((1600, 1600))
                preview_data = BytesIO()
                image.save(preview_data, format="PNG")
                self._preview_pixmap = QPixmap()
                self._preview_pixmap.loadFromData(preview_data.getvalue(), "PNG")
            finally:
                image.close()
            self._show_preview()
        except (ImageMergeError, OSError) as exc:
            self._preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText(f"Preview unavailable: {exc}")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._show_preview()

    def _show_preview(self) -> None:
        if self._preview_pixmap is not None:
            self.preview.setPixmap(
                self._preview_pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def export_png(self) -> None:
        if self.files.count() < 2:
            QMessageBox.information(self, "Add images", "Select at least two images before exporting.")
            return
        suggested = str(Path(self._paths()[0]).with_name("combined.png"))
        destination, _ = QFileDialog.getSaveFileName(self, "Export combined image", suggested, "PNG image (*.png)")
        if not destination:
            return
        output_path = Path(destination)
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")
        source_paths = {Path(path).resolve() for path in self._paths()}
        if output_path.resolve() in source_paths:
            QMessageBox.warning(
                self,
                "Choose another output file",
                "The output path matches a selected source image. Source files are never replaced.",
            )
            return
        overwrite = False
        if output_path.exists():
            response = QMessageBox.question(
                self,
                "Replace existing file?",
                f"{output_path.name} already exists. Replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        image = None
        try:
            image = compose_images(self._paths(), self._options())
            saved_path = save_png(
                image,
                output_path,
                overwrite=overwrite,
                protected_paths=source_paths,
            )
            QMessageBox.information(self, "Export complete", f"Saved combined image to:\n{saved_path}")
        except (ImageMergeError, OSError, FileExistsError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
        finally:
            if image is not None:
                image.close()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

