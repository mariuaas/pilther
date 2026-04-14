"""Sierra-2 dithering via a Zig-compiled shared library."""

from __future__ import annotations

from PIL import Image

from ._native_diffusion import make_native_lib, run_native_dither

_native_lib = make_native_lib("sierra2_dither")


def sierra2(image: Image.Image) -> Image.Image:
    """Apply Sierra-2 dithering to a PIL image and return a grayscale result."""
    return run_native_dither(image, _native_lib, "sierra2_dither", "Sierra-2")