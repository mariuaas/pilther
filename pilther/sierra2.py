"""Sierra-2 dithering via a Zig-compiled shared library."""

from __future__ import annotations

import ctypes
from typing import Final

from PIL import Image

from ._native_diffusion import apply_native_dither, load_configured_library

_DEF_LIB_BASENAME: Final[str] = "_sierra2"
_DEF_SYMBOL_NAME: Final[str] = "sierra2_dither"
_FILTER_LABEL: Final[str] = "Sierra-2"
_LIB: ctypes.CDLL | None = None


def _native_lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is not None:
        return _LIB

    _LIB = load_configured_library(_DEF_LIB_BASENAME, _DEF_SYMBOL_NAME)
    return _LIB


def sierra2(image: Image.Image) -> Image.Image:
    """Apply Sierra-2 dithering to a PIL image and return a grayscale result."""
    return apply_native_dither(image, _native_lib(), _DEF_SYMBOL_NAME, _FILTER_LABEL)