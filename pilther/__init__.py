"""pilther: fast Pillow dithering filters backed by Zig."""

from .atkinson import atkinson
from .bluenoise import bluenoise
from .burkes import burkes
from .palette import (
	Palette,
	extract_palette,
	get_named_palette,
	list_named_palettes,
	normalize_palette,
	resolve_palette,
)
from .palette_diffusion import (
	atkinson_palette,
	burkes_palette,
	sierra2_palette,
	sierra3_palette,
	stucki_palette,
)
from .sierra2 import sierra2
from .sierra3 import sierra3
from .stucki import stucki

__all__ = [
	"Palette",
	"atkinson",
	"atkinson_palette",
	"bluenoise",
	"burkes",
	"burkes_palette",
	"extract_palette",
	"get_named_palette",
	"list_named_palettes",
	"normalize_palette",
	"resolve_palette",
	"sierra2",
	"sierra2_palette",
	"sierra3",
	"sierra3_palette",
	"stucki",
	"stucki_palette",
]
