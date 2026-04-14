"""Shared helpers for ctypes-backed error-diffusion filters."""

from __future__ import annotations

import ctypes
from functools import lru_cache
from typing import Callable

import numpy as np
from PIL import Image

from ._native import NATIVE_LIBRARY_BASENAME, load_native_library


@lru_cache(maxsize=None)
def load_configured_library(lib_basename: str, symbol_name: str) -> ctypes.CDLL:
    lib = load_native_library(lib_basename)
    dither = getattr(lib, symbol_name)
    dither.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
    ]
    dither.restype = ctypes.c_int
    return lib


def apply_native_dither(
    image: Image.Image,
    lib: ctypes.CDLL,
    symbol_name: str,
    filter_label: str,
) -> Image.Image:
    gray = image.convert("L")
    buf = np.array(gray, dtype=np.uint8)
    h, w = buf.shape

    status = getattr(lib, symbol_name)(
        buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        w,
        h,
    )
    if status != 0:
        msg = {
            1: f"Native {filter_label} dithering failed: allocation error.",
            2: f"Native {filter_label} dithering failed: invalid image dimensions.",
        }.get(status, f"Native {filter_label} dithering failed with error code {status}.")
        raise RuntimeError(msg)

    return Image.fromarray(buf)


def make_native_lib(symbol_name: str) -> Callable[[], ctypes.CDLL]:
    @lru_cache(maxsize=None)
    def _native_lib() -> ctypes.CDLL:
        return load_configured_library(NATIVE_LIBRARY_BASENAME, symbol_name)

    return _native_lib


def run_native_dither(
    image: Image.Image,
    native_lib: Callable[[], ctypes.CDLL],
    symbol_name: str,
    filter_label: str,
) -> Image.Image:
    return apply_native_dither(image, native_lib(), symbol_name, filter_label)