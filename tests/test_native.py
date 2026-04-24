from __future__ import annotations

import ctypes

import pytest
from PIL import Image

from pilther._native import NATIVE_LIBRARY_BASENAME, load_native_library
from pilther.dither import Algorithm, _BINARY_FILTERS, atkinson, burkes, sierra2, sierra3, stucki

FILTER_CASES = [
    (Algorithm.ATKINSON, atkinson, NATIVE_LIBRARY_BASENAME, "atkinson_dither"),
    (Algorithm.SIERRA3, sierra3, NATIVE_LIBRARY_BASENAME, "sierra3_dither"),
    (Algorithm.SIERRA2, sierra2, NATIVE_LIBRARY_BASENAME, "sierra2_dither"),
    (Algorithm.STUCKI, stucki, NATIVE_LIBRARY_BASENAME, "stucki_dither"),
    (Algorithm.BURKES, burkes, NATIVE_LIBRARY_BASENAME, "burkes_dither"),
]


@pytest.mark.parametrize(("_algorithm", "_func", "basename", "_symbol_name"), FILTER_CASES)
def test_native_library_loads(_algorithm: Algorithm, _func, basename: str, _symbol_name: str) -> None:
    lib = load_native_library(basename)
    assert isinstance(lib, ctypes.CDLL)


@pytest.mark.parametrize(("algorithm", "_func", "_basename", "symbol_name"), FILTER_CASES)
def test_native_function_signature_is_set(algorithm: Algorithm, _func, _basename: str, symbol_name: str) -> None:
    lib = _BINARY_FILTERS[algorithm][0]()
    func = getattr(lib, symbol_name)
    assert func.argtypes is not None
    assert func.restype == ctypes.c_int


@pytest.mark.parametrize(("algorithm", "func", "_basename", "symbol_name"), FILTER_CASES)
def test_raises_on_native_error_status(
    monkeypatch: pytest.MonkeyPatch,
    algorithm: Algorithm,
    func,
    _basename: str,
    symbol_name: str,
) -> None:
    class _FakeLib:
        def __getattr__(self, name: str):
            if name != symbol_name:
                raise AttributeError(name)

            def _raise(*_args):
                return 1

            return _raise

    monkeypatch.setitem(
        _BINARY_FILTERS,
        algorithm,
        (lambda: _FakeLib(), symbol_name, _BINARY_FILTERS[algorithm][2]),
    )

    with pytest.raises(RuntimeError, match="allocation error"):
        func(Image.new("L", (1, 1), 0))
