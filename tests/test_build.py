from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from setuptools import Distribution

import pilther._build_zig as build_zig_module
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


def test_resolve_zig_command_prefers_ziglang(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_zig_module.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        build_zig_module.importlib.util,
        "find_spec",
        lambda name: object() if name == "ziglang" else None,
    )

    assert _resolve_zig_command() == [sys.executable, "-m", "ziglang"]


def test_build_invokes_ziglang_with_target_after_subcommand(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    package_dir = project_root / "pilther"
    src_dir = project_root / "src"
    package_dir.mkdir()
    src_dir.mkdir()
    src_file = src_dir / "atkinson.zig"
    src_file.write_text("pub export fn noop() void {}\n")

    monkeypatch.setattr(build_zig_module, "_resolve_zig_command", lambda: [sys.executable, "-m", "ziglang"])
    monkeypatch.setattr(build_zig_module, "_zig_target_arg", lambda: "aarch64-macos.11.0")

    recorded: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool, cwd: Path, env: dict[str, str]) -> None:
        recorded.append(cmd)

    monkeypatch.setattr(build_zig_module.subprocess, "run", fake_run)
    monkeypatch.setattr(build_zig_module.Path, "resolve", lambda self: package_dir.joinpath("_build_zig.py"))

    cmd = build_py(Distribution())
    cmd.initialize_options()
    cmd.finalize_options()
    cmd._build_zig_shared_libs()

    assert recorded == [[
        sys.executable,
        "-m",
        "ziglang",
        "build-lib",
        "-target",
        "aarch64-macos.11.0",
        "-dynamic",
        "-O",
        "ReleaseFast",
        f"-femit-bin={package_dir / ('_atkinson' + _library_suffix())}",
        str(src_file),
    ]]


def test_build_produces_native_library() -> None:
    if not _has_any_zig():
        pytest.skip("No Zig toolchain available")

    cmd = build_py(Distribution())
    cmd.initialize_options()
    cmd.finalize_options()
    cmd._build_zig_shared_libs()

    project_root = Path(__file__).resolve().parent.parent
    expected = [
        project_root / "pilther" / f"_atkinson{_library_suffix()}",
        project_root / "pilther" / f"_burkes{_library_suffix()}",
        project_root / "pilther" / f"_sierra2{_library_suffix()}",
        project_root / "pilther" / f"_sierra3{_library_suffix()}",
        project_root / "pilther" / f"_stucki{_library_suffix()}",
    ]
    assert all(path.exists() for path in expected)
