"""Shared ctypes helpers for palette-aware native diffusion filters."""

from __future__ import annotations

import ctypes
from functools import lru_cache

import numpy as np
from PIL import Image

from ._native import NATIVE_LIBRARY_BASENAME, load_native_library

_COLOR_SPACE_CODES = {
    "rgb": 0,
    "ycocg": 1,
}


@lru_cache(maxsize=None)
def load_configured_palette_library(symbol_name: str) -> ctypes.CDLL:
    lib = load_native_library(NATIVE_LIBRARY_BASENAME)
    dither = getattr(lib, symbol_name)
    dither.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
    ]
    dither.restype = ctypes.c_int
    return lib


def make_native_palette_lib(symbol_name: str):
    @lru_cache(maxsize=None)
    def _native_lib() -> ctypes.CDLL:
        return load_configured_palette_library(symbol_name)

    return _native_lib


def run_native_palette_dither(
    image: Image.Image,
    palette: np.ndarray,
    native_lib,
    symbol_name: str,
    filter_label: str,
    palette_space: str,
) -> Image.Image:
    buf = np.ascontiguousarray(np.asarray(image.convert("RGB"), dtype=np.uint8))
    palette_buf = np.ascontiguousarray(np.asarray(palette, dtype=np.uint8))
    height, width, _ = buf.shape

    status = getattr(native_lib(), symbol_name)(
        buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        width,
        height,
        palette_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        palette_buf.shape[0],
        _COLOR_SPACE_CODES[palette_space],
    )
    if status != 0:
        msg = {
            1: f"Native {filter_label} palette dithering failed: allocation error.",
            2: f"Native {filter_label} palette dithering failed: invalid image dimensions.",
            3: f"Native {filter_label} palette dithering failed: invalid palette.",
            4: f"Native {filter_label} palette dithering failed: invalid color space.",
        }.get(status, f"Native {filter_label} palette dithering failed with error code {status}.")
        raise RuntimeError(msg)

    return Image.fromarray(buf, mode="RGB")