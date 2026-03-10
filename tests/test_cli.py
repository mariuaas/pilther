from __future__ import annotations

import subprocess
import sys

import numpy as np
from PIL import Image


def test_cli_generates_output_file(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(np.array([[0, 128], [200, 40]], dtype=np.uint8), mode="L")
    img.save(inp)

    proc = subprocess.run(
        [sys.executable, "-m", "pilther.cli", str(inp), str(out)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    with Image.open(out) as saved:
        assert saved.mode == "L"
        assert saved.size == (2, 2)


def test_cli_fails_for_missing_input(tmp_path) -> None:
    out = tmp_path / "out.png"
    proc = subprocess.run(
        [sys.executable, "-m", "pilther.cli", str(tmp_path / "missing.png"), str(out)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "No such file" in proc.stderr or "cannot identify image file" in proc.stderr
