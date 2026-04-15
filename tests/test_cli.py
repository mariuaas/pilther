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


def test_cli_supports_filter_selection(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(np.array([[0, 128], [200, 40]], dtype=np.uint8), mode="L")
    img.save(inp)

    proc = subprocess.run(
        [sys.executable, "-m", "pilther.cli", "--filter", "stucki", str(inp), str(out)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    with Image.open(out) as saved:
        assert saved.mode == "L"
        assert saved.size == (2, 2)


def test_cli_supports_bluenoise_selection(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(np.array([[0, 128], [200, 40]], dtype=np.uint8), mode="L")
    img.save(inp)

    proc = subprocess.run(
        [sys.executable, "-m", "pilther.cli", "--filter", "bluenoise", str(inp), str(out)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    with Image.open(out) as saved:
        assert saved.mode == "1"
        assert saved.size == (2, 2)


def test_cli_supports_palette_filter_with_named_palette(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(
        np.array(
            [
                [[0, 32, 64], [128, 160, 192]],
                [[255, 240, 200], [64, 32, 0]],
            ],
            dtype=np.uint8,
        ),
        mode="RGB",
    )
    img.save(inp)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pilther.cli",
            "--filter",
            "sierra2_palette",
            "--palette",
            "ega16",
            str(inp),
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    with Image.open(out) as saved:
        assert saved.mode == "RGB"
        assert saved.size == (2, 2)


def test_cli_supports_palette_filter_with_extracted_palette(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(
        np.array(
            [
                [[0, 32, 64], [128, 160, 192]],
                [[255, 240, 200], [64, 32, 0]],
            ],
            dtype=np.uint8,
        ),
        mode="RGB",
    )
    img.save(inp)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pilther.cli",
            "--filter",
            "atkinson_palette",
            "--extract-colors",
            "4",
            "--palette-space",
            "ycocg",
            str(inp),
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    with Image.open(out) as saved:
        assert saved.mode == "RGB"
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


def test_cli_rejects_unknown_filter(tmp_path) -> None:
    out = tmp_path / "out.png"
    proc = subprocess.run(
        [sys.executable, "-m", "pilther.cli", "--filter", "unknown", str(tmp_path / "missing.png"), str(out)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr


def test_cli_rejects_palette_flags_for_binary_filters(tmp_path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"

    img = Image.fromarray(np.array([[0, 128], [200, 40]], dtype=np.uint8), mode="L")
    img.save(inp)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pilther.cli",
            "--filter",
            "sierra2",
            "--palette",
            "gray4",
            str(inp),
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "only valid for palette-aware filters" in proc.stderr
