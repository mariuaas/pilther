"""Setuptools hooks to compile Zig native libraries during package build."""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools.command.build_py import build_py as _build_py


_NATIVE_LIB_BASENAME = "_pilther"
_NATIVE_LIB_ENTRYPOINT = "pilther.zig"


def _library_suffix() -> str:
    if os.name == "nt":
        return ".dll"
    if platform.system() == "Darwin":
        return ".dylib"
    return ".so"


def _resolve_zig_command() -> list[str]:
    if importlib.util.find_spec("ziglang") is not None:
        return [sys.executable, "-m", "ziglang"]

    zig_bin = shutil.which("zig")
    if zig_bin is not None:
        return [zig_bin]

    python_zig_bin = shutil.which("python-zig")
    if python_zig_bin is not None:
        return [python_zig_bin]

    raise RuntimeError(
        "No Zig compiler found. Install the build-system dependency `ziglang` or provide `zig` on PATH."
    )


def _zig_target_arg() -> str | None:
    if platform.system() != "Darwin":
        return None

    arch_map = {
        "arm64": "aarch64",
        "x86_64": "x86_64",
    }
    zig_arch = arch_map.get(platform.machine().lower())
    if zig_arch is None:
        return None

    deployment_target = os.environ.get("MACOSX_DEPLOYMENT_TARGET", "11.0")
    return f"{zig_arch}-macos.{deployment_target}"


class build_py(_build_py):
    """Build Python modules and compile Zig shared libraries."""

    def run(self) -> None:
        self._build_zig_shared_libs()
        super().run()

    def _build_zig_shared_libs(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        package_dir = project_root / "pilther"
        src_dir = project_root / "src"
        src_files = sorted(src_dir.glob("*.zig"))
        if not src_files:
            raise RuntimeError("No Zig source files found in src/.")

        root_source = src_dir / _NATIVE_LIB_ENTRYPOINT
        if not root_source.exists():
            raise RuntimeError(f"Missing Zig entrypoint '{_NATIVE_LIB_ENTRYPOINT}' in src/.")

        zig_cmd = _resolve_zig_command()
        target_arg = _zig_target_arg()
        env = os.environ.copy()
        env.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")

        out_file = package_dir / f"{_NATIVE_LIB_BASENAME}{_library_suffix()}"
        for legacy_file in package_dir.glob(f"_*{_library_suffix()}"):
            if legacy_file != out_file:
                legacy_file.unlink()

        latest_src_mtime = max(src_file.stat().st_mtime for src_file in src_files)
        if (
            out_file.exists()
            and out_file.stat().st_size > 0
            and out_file.stat().st_mtime >= latest_src_mtime
        ):
            return

        cmd = [
            *zig_cmd,
            "build-lib",
        ]

        if target_arg is not None:
            cmd.extend(["-target", target_arg])

        cmd.extend([
            "-dynamic",
            "-O",
            "ReleaseFast",
            f"-femit-bin={out_file}",
            str(root_source),
        ])

        subprocess.run(cmd, check=True, cwd=project_root, env=env)


class bdist_wheel(_bdist_wheel):
    """Mark wheels as platform-specific because they bundle a native library."""

    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False
