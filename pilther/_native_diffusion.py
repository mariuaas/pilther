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


@lru_cache(maxsize=None)
def load_configured_generic_library(symbol_name: str) -> ctypes.CDLL:
    lib = load_native_library(NATIVE_LIBRARY_BASENAME)
    dither = getattr(lib, symbol_name)
    dither.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int16),
        ctypes.c_int,
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


def run_native_kernel_dither(
    image: Image.Image,
    steps: np.ndarray,
    *,
    divisor: int,
    depth: int,
    symbol_name: str = "generic_dither",
    filter_label: str = "custom kernel",
) -> Image.Image:
    buf = np.asarray(image.convert("L"), dtype=np.uint8)
    steps_buf = np.ascontiguousarray(np.asarray(steps, dtype=np.int16))
    h, w = buf.shape

    lib = load_configured_generic_library(symbol_name)
    status = getattr(lib, symbol_name)(
        buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        w,
        h,
        steps_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        steps_buf.shape[0] // 3,
        divisor,
        depth,
    )
    if status != 0:
        msg = {
            1: f"Native {filter_label} dithering failed: allocation error.",
            2: f"Native {filter_label} dithering failed: invalid image dimensions.",
            3: f"Native {filter_label} dithering failed: invalid kernel.",
        }.get(status, f"Native {filter_label} dithering failed with error code {status}.")
        raise RuntimeError(msg)

    return Image.fromarray(buf)