from __future__ import annotations

import ctypes
import importlib

import pytest
from PIL import Image

from pilther._native import load_native_library

atkinson_module = importlib.import_module("pilther.atkinson")


def test_native_library_loads() -> None:
    lib = load_native_library("_atkinson")
    assert isinstance(lib, ctypes.CDLL)


def test_native_function_signature_is_set() -> None:
    lib = atkinson_module._native_lib()
    assert lib.atkinson_dither.argtypes is not None
    assert lib.atkinson_dither.restype == ctypes.c_int


def test_raises_on_native_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeLib:
        def atkinson_dither(self, *_args):
            return 1

    monkeypatch.setattr(atkinson_module, "_native_lib", lambda: _FakeLib())

    with pytest.raises(RuntimeError, match="allocation error"):
        atkinson_module.atkinson(Image.new("L", (1, 1), 0))
