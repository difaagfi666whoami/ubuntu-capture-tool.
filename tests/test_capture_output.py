from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from ubuntu_capture_tool.capture.backend import CaptureBackendError
from ubuntu_capture_tool.capture.output import save_capture_png


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), (5, 10, 15)).save(output, format="PNG")
    return output.getvalue()


def test_capture_saves_png_with_unique_name(tmp_path: Path) -> None:
    first = save_capture_png(png_bytes(), tmp_path)
    second = save_capture_png(png_bytes(), tmp_path)

    assert first.exists()
    assert second.exists()
    assert first != second
    with Image.open(first) as image:
        assert image.format == "PNG"
        assert image.size == (2, 2)


def test_capture_output_rejects_invalid_data_without_creating_file(tmp_path: Path) -> None:
    with pytest.raises(CaptureBackendError, match="not a valid PNG"):
        save_capture_png(b"not a png", tmp_path)

    assert list(tmp_path.iterdir()) == []
