"""Helpers for loading Zig-compiled native libraries."""

from __future__ import annotations

import ctypes
import os
import platform
from functools import lru_cache
from pathlib import Path


def library_suffix() -> str:
    if os.name == "nt":
        return ".dll"
    if platform.system() == "Darwin":
        return ".dylib"
    return ".so"


@lru_cache(maxsize=None)
def load_native_library(basename: str) -> ctypes.CDLL:
    lib_name = f"{basename}{library_suffix()}"
    lib_path = Path(__file__).parent / lib_name
    if not lib_path.exists():
        raise RuntimeError(
            f"Missing native library '{lib_name}'. Build/install the package first."
        )
    return ctypes.CDLL(str(lib_path))