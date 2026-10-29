from io import BytesIO

import pytest
from PIL import Image

from ubuntu_capture_tool.capture.backend import CaptureBackendError, CaptureRect
from ubuntu_capture_tool.capture.crop import crop_png_to_rectangle


def png_bytes(size: tuple[int, int] = (6, 5)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, (12, 34, 56)).save(output, format="PNG")
    return output.getvalue()


def test_crop_png_returns_exact_rectangle_size() -> None:
    cropped = crop_png_to_rectangle(png_bytes(), CaptureRect(2, 1, 3, 2))

    with Image.open(BytesIO(cropped)) as image:
        assert image.size == (3, 2)
        assert image.getpixel((0, 0)) == (12, 34, 56)


@pytest.mark.parametrize("rectangle", [CaptureRect(-1, 0, 2, 2), CaptureRect(5, 4, 2, 2)])
def test_crop_rejects_area_outside_screen(rectangle: CaptureRect) -> None:
    with pytest.raises(CaptureBackendError, match="outside the current screen image"):
        crop_png_to_rectangle(png_bytes(), rectangle)
