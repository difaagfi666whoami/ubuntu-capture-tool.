"""Platform-independent PNG cropping for captured desktop frames."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from .backend import CaptureBackendError, CaptureRect


def crop_png_to_rectangle(image_data: bytes, rectangle: CaptureRect) -> bytes:
    """Crop a rectangle in image-pixel coordinates and return a PNG."""
    try:
        with Image.open(BytesIO(image_data)) as source:
            if source.format != "PNG":
                raise CaptureBackendError("The capture backend must return a PNG image.")
            bounds = (0, 0, source.width, source.height)
            requested = (
                rectangle.x,
                rectangle.y,
                rectangle.x + rectangle.width,
                rectangle.y + rectangle.height,
            )
            if rectangle.x < 0 or rectangle.y < 0 or requested[2] > source.width or requested[3] > source.height:
                raise CaptureBackendError(
                    f"The saved area {rectangle.width} × {rectangle.height} at "
                    f"({rectangle.x}, {rectangle.y}) is outside the current screen image "
                    f"({bounds[2]} × {bounds[3]}). Select an area again."
                )
            cropped = source.crop(requested)
            output = BytesIO()
            cropped.save(output, format="PNG")
            return output.getvalue()
    except (OSError, UnidentifiedImageError) as exc:
        raise CaptureBackendError(f"The screen image is not a valid PNG: {exc}") from exc
