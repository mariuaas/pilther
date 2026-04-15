# pilther

[![CI](https://github.com/mariuaas/pilther/actions/workflows/ci.yml/badge.svg)](https://github.com/mariuaas/pilther/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fast Pillow dithering filters backed by Zig.

This alpha release provides these filters:

- Atkinson error diffusion (`pilther.atkinson`)
- Sierra-3 error diffusion (`pilther.sierra3`)
- Sierra-2 error diffusion (`pilther.sierra2`)
- Stucki error diffusion (`pilther.stucki`)
- Burkes error diffusion (`pilther.burkes`)
- Blue-noise threshold dithering (`pilther.bluenoise`)
- Palette-aware diffusion variants (`pilther.sierra2_palette`, `pilther.atkinson_palette`, etc.)

The Python API also includes early palette utilities for extraction and normalization:

- Palette extraction in RGB or YCoCg (`pilther.extract_palette`)
- Palette normalization for grayscale and RGB palettes (`pilther.normalize_palette`)
- Named grayscale and color palettes (`pilther.get_named_palette`, `pilther.list_named_palettes`)

Built-in palette names include grayscale ramps such as `gray4` and `gray32`, plus color presets such as `cga4`, `gameboy4`, `ega16`, `ansi16`, `web216`, and `term256`.

## Status

`pilther` is currently in alpha. The public API is small and usable, but packaging and filter coverage are still evolving.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

Zig is provided at build time via the `ziglang` build-system dependency.
If you already have a system `zig`, the build hook will use it first.

## Development setup (uv)

```bash
uv sync
```

If you want a user-level Zig binary for local development commands:

```bash
uv tool install ziglang
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
from pilther import atkinson, extract_palette, sierra2_palette

img = Image.open("input.jpg")
out = atkinson(img)
palette = extract_palette(img, 8, method="median_cut", space="rgb")
sierra = sierra2_palette(img, palette_name="ega16")
out.save("output.png")
```

## Usage (CLI)

```bash
uv run pilther --filter stucki input.jpg output.png
```

Palette-aware variants can use either named palettes or extracted palettes:

```bash
uv run pilther --filter sierra2_palette --palette ega16 input.jpg output.png
uv run pilther --filter atkinson_palette --extract-colors 8 --palette-method median_cut input.jpg output.png
```

## Visual Showcase

See [docs/showcase.md](docs/showcase.md) for grayscale and color comparisons on the bundled `baboon`, `pepper`, and `flower` sample images.

Regenerate the gallery assets with:

```bash
uv run python scripts/generate_showcase.py
```

## Native build behavior

`pilther` compiles the Zig sources in `src/` into a single platform-specific shared library during package build. The build hook prefers the `ziglang` build dependency and falls back to a system `zig` binary when needed.

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
