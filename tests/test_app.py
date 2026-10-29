import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QListWidgetItem, QMessageBox

import ubuntu_capture_tool.app as app_module
from ubuntu_capture_tool.app import MainWindow
from ubuntu_capture_tool.image_merge import Alignment, Orientation


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qt_app):
    widget = MainWindow()
    yield widget
    widget.close()


def write_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> Path:
    Image.new("RGB", size, color).save(path)
    return path


def add_input(window: MainWindow, path: Path) -> None:
    item = QListWidgetItem(path.name)
    item.setData(Qt.ItemDataRole.UserRole, str(path))
    window.files.addItem(item)


def test_select_reorder_and_preview_images(window: MainWindow, tmp_path: Path) -> None:
    first = write_image(tmp_path / "first.png", (10, 20), (255, 0, 0))
    second = write_image(tmp_path / "second.png", (20, 10), (0, 0, 255))
    add_input(window, first)
    add_input(window, second)

    window.refresh_preview()
    assert window._preview_pixmap is not None
    assert window.preview.text() == ""
    assert window.files.count() == 2

    window.files.setCurrentRow(1)
    window.move_item(-1)
    assert window._paths() == [str(second), str(first)]

    window.orientation.setCurrentIndex(1)
    window.alignment.setCurrentIndex(0)
    assert window._options().orientation == Orientation.HORIZONTAL
    assert window._options().alignment == Alignment.START
    assert window._preview_pixmap is not None


def test_file_picker_adds_multiple_selected_images(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = write_image(tmp_path / "first.png", (2, 2), (255, 0, 0))
    second = write_image(tmp_path / "second.png", (2, 2), (0, 0, 255))
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getOpenFileNames",
        lambda *_: ([str(first), str(second)], "Images"),
    )

    window.add_images()

    assert window._paths() == [str(first), str(second)]
    assert window._preview_pixmap is not None


def test_invalid_image_shows_actionable_preview_error(window: MainWindow, tmp_path: Path) -> None:
    valid = write_image(tmp_path / "valid.png", (2, 2), (1, 2, 3))
    invalid = tmp_path / "invalid.png"
    invalid.write_text("not an image")
    add_input(window, valid)
    add_input(window, invalid)

    window.refresh_preview()

    assert "Could not read image" in window.preview.text()


def test_export_saves_png_and_requires_overwrite_confirmation(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a = write_image(tmp_path / "a.png", (2, 2), (255, 0, 0))
    source_b = write_image(tmp_path / "b.png", (2, 2), (0, 0, 255))
    original_a = source_a.read_bytes()
    original_b = source_b.read_bytes()
    target = tmp_path / "combined.png"
    add_input(window, source_a)
    add_input(window, source_b)

    monkeypatch.setattr(app_module.QFileDialog, "getSaveFileName", lambda *_: (str(target), "PNG"))
    confirmations: list[QMessageBox.StandardButton] = []
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_args: confirmations[-1],
    )
    monkeypatch.setattr(app_module.QMessageBox, "information", lambda *_args: None)
    errors: list[str] = []
    monkeypatch.setattr(app_module.QMessageBox, "critical", lambda *_args: errors.append(str(_args[2])))

    window.export_png()
    assert target.exists()
    with Image.open(target) as exported:
        assert exported.format == "PNG"
        assert exported.size == (2, 4)

    target.write_bytes(b"keep this existing content")
    confirmations.append(QMessageBox.StandardButton.No)
    window.export_png()
    assert target.read_bytes() == b"keep this existing content"

    confirmations[-1] = QMessageBox.StandardButton.Yes
    window.export_png()
    with Image.open(target) as exported:
        assert exported.format == "PNG"
        assert exported.size == (2, 4)
    assert source_a.read_bytes() == original_a
    assert source_b.read_bytes() == original_b
    assert not errors


def test_export_cannot_replace_selected_source(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a = write_image(tmp_path / "a.png", (1, 1), (255, 0, 0))
    source_b = write_image(tmp_path / "b.png", (1, 1), (0, 0, 255))
    original_a = source_a.read_bytes()
    add_input(window, source_a)
    add_input(window, source_b)

    monkeypatch.setattr(app_module.QFileDialog, "getSaveFileName", lambda *_: (str(source_a), "PNG"))
    warnings: list[str] = []
    monkeypatch.setattr(app_module.QMessageBox, "warning", lambda *_args: warnings.append(str(_args[2])))

    window.export_png()

    assert source_a.read_bytes() == original_a
    assert warnings and "Source files are never replaced" in warnings[0]

