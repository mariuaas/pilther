"""pilther: fast Pillow dithering filters backed by Zig."""

from .bluenoise import bluenoise
from .colorspace import ColorSpace
from .dither import (
	Algorithm,
	Quantizer,
	atkinson,
	atkinson_palette,
	burkes,
	burkes_palette,
	dither,
	sierra2,
	sierra2_palette,
	sierra3,
	sierra3_palette,
	stucki,
	stucki_palette,
)
from .palette import (
	Palette,
	extract_palette,
	get_named_palette,
	list_named_palettes,
	normalize_palette,
	resolve_palette,
)

__all__ = [
	"Palette",
	"Algorithm",
	"ColorSpace",
	"Quantizer",
	"atkinson",
	"atkinson_palette",
	"bluenoise",
	"burkes",
	"burkes_palette",
	"dither",
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
