from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest
from setuptools import Distribution

from pilther._build_zig import _library_suffix, _resolve_zig_command, build_py


def _has_any_zig() -> bool:
    return (
        shutil.which("zig") is not None
        or shutil.which("python-zig") is not None
        or importlib.util.find_spec("ziglang") is not None
    )


def test_resolve_zig_command() -> None:
    if not _has_any_zig():
        pytest.skip("No Zig toolchain available")

    cmd = _resolve_zig_command()
    assert isinstance(cmd, list)
    assert len(cmd) >= 1


def test_build_produces_native_library() -> None:
    if not _has_any_zig():
        pytest.skip("No Zig toolchain available")

    cmd = build_py(Distribution())
    cmd.initialize_options()
    cmd.finalize_options()
    cmd._build_zig_shared_libs()

    project_root = Path(__file__).resolve().parent.parent
    expected = project_root / "pilther" / f"_atkinson{_library_suffix()}"
    assert expected.exists()
