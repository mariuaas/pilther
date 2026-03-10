# pilther

[![CI](https://github.com/mariuaas/pilther/actions/workflows/ci.yml/badge.svg)](https://github.com/mariuaas/pilther/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fast Pillow dithering filters backed by Zig.

This alpha release provides one filter:

- Atkinson error diffusion (`pilther.atkinson`)

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

During build/install, setuptools runs a Zig compile step that builds the native shared library for Atkinson dithering.

If you want an editable development install with test tools:

```bash
uv pip install -e .[dev]
```

## Usage (Python API)

```python
from PIL import Image
from pilther import atkinson

img = Image.open("input.jpg")
out = atkinson(img)
out.save("output.png")
```

## Usage (CLI)

```bash
uv run pilther input.jpg output.png
```

## Native build behavior

`pilther` compiles Zig sources in `src/` into platform-specific shared libraries during package build. The build hook prefers a system `zig` binary when available and otherwise falls back to the `ziglang` build dependency.

This means:

- source builds require Zig at build time
- built wheels bundle the compiled native library
- the package can grow to additional filters by adding more `src/*.zig` files

## Build an alpha distribution

```bash
uv run python -m build
```

The source distribution includes Zig sources, and wheel builds compile a platform-specific shared library.

## Testing

```bash
uv run --with pytest --with setuptools pytest -q
```

## License

MIT. See `LICENSE`.
