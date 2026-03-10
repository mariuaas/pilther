from __future__ import annotations

import ctypes
import importlib

import pytest
from PIL import Image

from pilther._native import load_native_library

FILTER_CASES = [
    ("atkinson", "_atkinson", "atkinson_dither"),
    ("sierra3", "_sierra3", "sierra3_dither"),
    ("sierra2", "_sierra2", "sierra2_dither"),
    ("stucki", "_stucki", "stucki_dither"),
    ("burkes", "_burkes", "burkes_dither"),
]


@pytest.mark.parametrize(("_module_name", "basename", "_symbol_name"), FILTER_CASES)
def test_native_library_loads(_module_name: str, basename: str, _symbol_name: str) -> None:
    lib = load_native_library(basename)
    assert isinstance(lib, ctypes.CDLL)


@pytest.mark.parametrize(("module_name", "_basename", "symbol_name"), FILTER_CASES)
def test_native_function_signature_is_set(module_name: str, _basename: str, symbol_name: str) -> None:
    module = importlib.import_module(f"pilther.{module_name}")
    lib = module._native_lib()
    func = getattr(lib, symbol_name)
    assert func.argtypes is not None
    assert func.restype == ctypes.c_int


@pytest.mark.parametrize(("module_name", "_basename", "symbol_name"), FILTER_CASES)
def test_raises_on_native_error_status(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    _basename: str,
    symbol_name: str,
) -> None:
    module = importlib.import_module(f"pilther.{module_name}")

    class _FakeLib:
        def __getattr__(self, name: str):
            if name != symbol_name:
                raise AttributeError(name)

            def _raise(*_args):
                return 1

            return _raise

    monkeypatch.setattr(module, "_native_lib", lambda: _FakeLib())

    with pytest.raises(RuntimeError, match="allocation error"):
        getattr(module, module_name)(Image.new("L", (1, 1), 0))
