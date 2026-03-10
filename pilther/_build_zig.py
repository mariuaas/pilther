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


def _library_suffix() -> str:
    if os.name == "nt":
        return ".dll"
    if platform.system() == "Darwin":
        return ".dylib"
    return ".so"


def _resolve_zig_command() -> list[str]:
    zig_bin = shutil.which("zig")
    if zig_bin is not None:
        return [zig_bin]

    python_zig_bin = shutil.which("python-zig")
    if python_zig_bin is not None:
        return [python_zig_bin]

    if importlib.util.find_spec("ziglang") is not None:
        return [sys.executable, "-m", "ziglang"]

    raise RuntimeError(
        "No Zig compiler found. Install `zig` on PATH or use build-system dependency `ziglang`."
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

        zig_cmd = _resolve_zig_command()
        target_arg = _zig_target_arg()
        env = os.environ.copy()
        env.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")

        for src_file in src_files:
            out_file = package_dir / f"_{src_file.stem}{_library_suffix()}"
            if out_file.exists() and out_file.stat().st_mtime >= src_file.stat().st_mtime:
                continue

            cmd = [
                *zig_cmd,
                "build-lib",
                "-dynamic",
                "-O",
                "ReleaseFast",
                f"-femit-bin={out_file}",
                str(src_file),
            ]

            if target_arg is not None:
                cmd[2:2] = ["-target", target_arg]

            subprocess.run(cmd, check=True, cwd=project_root, env=env)


class bdist_wheel(_bdist_wheel):
    """Mark wheels as platform-specific because they bundle a native library."""

    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False
