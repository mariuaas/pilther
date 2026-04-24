# pilther

[![CI](https://github.com/mariuaas/pilther/actions/workflows/ci.yml/badge.svg)](https://github.com/mariuaas/pilther/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fast Pillow dithering filters backed by Zig.

This alpha release provides these filters:

- Atkinson, Sierra-3, Sierra-2, Stucki, and Burkes diffusion kernels
- Blue-noise threshold dithering (`pilther.bluenoise`)

The canonical diffusion API is organized by kernel plus quantizer:

- Kernels: `pilther.Algorithm`
- Quantizers: `pilther.Quantizer`
- Color spaces: `pilther.ColorSpace`
- Dispatcher: `pilther.dither(...)`

Legacy convenience wrappers such as `pilther.atkinson` and `pilther.sierra2_palette` still exist, but they delegate to the canonical model.

The Python API also includes palette utilities for extraction and normalization:

- Palette extraction in grayscale, RGB, or YCoCg (`pilther.extract_palette`)
- Palette normalization for grayscale and RGB palettes (`pilther.normalize_palette`)
- Named grayscale and color palettes (`pilther.get_named_palette`, `pilther.list_named_palettes`)

Built-in palette names include grayscale ramps such as `gray4` and `gray32`, plus color presets such as `cga4`, `gameboy4`, `ega16`, `ansi16`, `web216`, and `term256`.

## Status

`pilther` is currently in alpha. The public API is small and usable, but packaging and filter coverage are still evolving.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

Zig is provided at build time via the `ziglang` build-system dependency.
For local development and tests, use the pinned `ziglang==0.15.2` package in the project environment.

## Development setup (uv)

```bash
uv sync --extra dev
```

This creates the local `.venv`, installs the test tools, and installs `ziglang==0.15.2` so builds use the same Zig version as packaging.

If you want a user-level Zig binary for local development commands:

```bash
uv tool install ziglang==0.15.2
```

## Install from source

```bash
uv pip install .
```

During build/install, setuptools runs a Zig compile step that builds the native shared library for the Zig-backed diffusion filters.

If you want an editable development install with test tools:

```bash
uv pip install -e .[dev]
```

## Usage (Python API)

```python
from PIL import Image
from pilther import Algorithm, ColorSpace, Quantizer, dither, extract_palette

img = Image.open("input.jpg")
out = dither(img, algorithm=Algorithm.ATKINSON)
palette = extract_palette(img, 8, method="median_cut", space=ColorSpace.RGB)
sierra = dither(
	img,
	algorithm=Algorithm.SIERRA2,
	quantizer=Quantizer.PALETTE,
	palette_name="ega16",
	color_space=ColorSpace.RGB,
)
out.save("output.png")
```

## Usage (CLI)

```bash
uv run pilther --algorithm stucki input.jpg output.png
```

Palette quantization can use either named palettes or extracted palettes:

```bash
uv run pilther --algorithm sierra2 --quantizer palette --palette ega16 input.jpg output.png
uv run pilther --algorithm atkinson --quantizer palette --extract-colors 8 --palette-method median_cut input.jpg output.png
```

## Visual Showcase

See [docs/showcase.md](docs/showcase.md) for grayscale and color comparisons on the bundled `baboon`, `pepper`, and `flower` sample images.

Regenerate the gallery assets with:

```bash
uv run python scripts/generate_showcase.py
```

## Native build behavior

`pilther` compiles the Zig sources in `src/` into a single platform-specific shared library during package build. The build hook prefers the pinned `ziglang==0.15.2` package from the active Python environment and falls back to a system `zig` binary only when `ziglang` is unavailable.

This means:

- source builds require Zig at build time
- built wheels bundle the compiled native library
- the package can grow to additional filters by exporting more symbols from `src/pilther.zig`

## Build an alpha distribution

```bash
uv run python -m build
```

The source distribution includes Zig sources, and wheel builds compile a platform-specific shared library.

## Testing

```bash
uv run --extra dev pytest -q
```

## License

MIT. See `LICENSE`.
