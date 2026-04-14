"""Sierra-3 dithering via a Zig-compiled shared library."""

from __future__ import annotations

from PIL import Image

from ._native_diffusion import make_native_lib, run_native_dither

_native_lib = make_native_lib("sierra3_dither")


def sierra3(image: Image.Image) -> Image.Image:
    """Apply Sierra-3 dithering to a PIL image and return a grayscale result."""
    return run_native_dither(image, _native_lib, "sierra3_dither", "Sierra-3")