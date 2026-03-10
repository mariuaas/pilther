"""Atkinson dithering via a Zig-compiled shared library."""

from __future__ import annotations

import ctypes
from typing import Final

import numpy as np
from PIL import Image

from ._native import load_native_library

_DEF_LIB_BASENAME: Final[str] = "_atkinson"
_LIB: ctypes.CDLL | None = None


def _native_lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is not None:
        return _LIB

    lib = load_native_library(_DEF_LIB_BASENAME)
    lib.atkinson_dither.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
    ]
    lib.atkinson_dither.restype = ctypes.c_int
    _LIB = lib
    return _LIB


def atkinson(image: Image.Image) -> Image.Image:
    """Apply Atkinson dithering to a PIL image and return a grayscale result."""
    gray = image.convert("L")
    buf = np.array(gray, dtype=np.uint8)
    h, w = buf.shape

    status = _native_lib().atkinson_dither(
        buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        w,
        h,
    )
    if status != 0:
        msg = {
            1: "Native Atkinson dithering failed: allocation error.",
            2: "Native Atkinson dithering failed: invalid image dimensions.",
        }.get(status, f"Native Atkinson dithering failed with error code {status}.")
        raise RuntimeError(msg)

    return Image.fromarray(buf)
