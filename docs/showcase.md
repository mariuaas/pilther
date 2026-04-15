# Showcase

This page compares `pilther` outputs on the bundled sample images in [testimgs](../testimgs).

Regenerate the gallery assets with:

```bash
uv run python scripts/generate_showcase.py
```

All generated outputs except the source image include a footer with three metrics measured against the source image: RGB MSE, RGB PSNR, and grayscale SSIM.

The showcase is split into three views for each source image:

- grayscale diffusion: the original binary-oriented filters
- color diffusion: the palette-aware variants with a shared `ega16` palette
- palette study: the same `sierra2_palette` kernel with different built-in palettes
- extracted palette quantization: 64-color median-cut palettes extracted in either RGB or YCoCg, then applied as direct quantization without diffusion

## Baboon

Baboon is useful for testing texture retention and how much noise structure each method introduces.

### Source

![Baboon source](generated/baboon/source.png)

### Grayscale Diffusion

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Baboon Atkinson](generated/baboon/grayscale_atkinson.png) | ![Baboon Sierra-2](generated/baboon/grayscale_sierra2.png) | ![Baboon Sierra-3](generated/baboon/grayscale_sierra3.png) |

| Stucki | Burkes | Blue-noise |
| --- | --- | --- |
| ![Baboon Stucki](generated/baboon/grayscale_stucki.png) | ![Baboon Burkes](generated/baboon/grayscale_burkes.png) | ![Baboon Blue-noise](generated/baboon/grayscale_bluenoise.png) |

### Color Diffusion With `ega16`

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Baboon Atkinson Palette](generated/baboon/color_atkinson_palette_ega16.png) | ![Baboon Sierra-2 Palette](generated/baboon/color_sierra2_palette_ega16.png) | ![Baboon Sierra-3 Palette](generated/baboon/color_sierra3_palette_ega16.png) |

| Stucki | Burkes |
| --- | --- |
| ![Baboon Stucki Palette](generated/baboon/color_stucki_palette_ega16.png) | ![Baboon Burkes Palette](generated/baboon/color_burkes_palette_ega16.png) |

### Palette Study With `sierra2_palette`

| gameboy4 | ega16 | ansi16 |
| --- | --- | --- |
| ![Baboon Game Boy](generated/baboon/palette_sierra2_gameboy4.png) | ![Baboon EGA](generated/baboon/palette_sierra2_ega16.png) | ![Baboon ANSI](generated/baboon/palette_sierra2_ansi16.png) |

| web216 | term256 |
| --- | --- |
| ![Baboon web216](generated/baboon/palette_sierra2_web216.png) | ![Baboon term256](generated/baboon/palette_sierra2_term256.png) |

### Extracted Palette Quantization

These examples isolate the palette extraction step by directly quantizing with a 64-color palette extracted from the image, without error diffusion.

| RGB-extracted palette | YCoCg-extracted palette |
| --- | --- |
| ![Baboon RGB palette](generated/baboon/extracted_palette_rgb.png) | ![Baboon YCoCg palette](generated/baboon/extracted_palette_ycocg.png) |

| RGB quantized | YCoCg quantized |
| --- | --- |
| ![Baboon RGB quantized](generated/baboon/extracted_quantized_rgb.png) | ![Baboon YCoCg quantized](generated/baboon/extracted_quantized_ycocg.png) |

## Pepper

Pepper is a good gradient and highlight test image. It tends to make banding and coarse diffusion patterns obvious.

### Source

![Pepper source](generated/pepper/source.png)

### Grayscale Diffusion

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Pepper Atkinson](generated/pepper/grayscale_atkinson.png) | ![Pepper Sierra-2](generated/pepper/grayscale_sierra2.png) | ![Pepper Sierra-3](generated/pepper/grayscale_sierra3.png) |

| Stucki | Burkes | Blue-noise |
| --- | --- | --- |
| ![Pepper Stucki](generated/pepper/grayscale_stucki.png) | ![Pepper Burkes](generated/pepper/grayscale_burkes.png) | ![Pepper Blue-noise](generated/pepper/grayscale_bluenoise.png) |

### Color Diffusion With `ega16`

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Pepper Atkinson Palette](generated/pepper/color_atkinson_palette_ega16.png) | ![Pepper Sierra-2 Palette](generated/pepper/color_sierra2_palette_ega16.png) | ![Pepper Sierra-3 Palette](generated/pepper/color_sierra3_palette_ega16.png) |

| Stucki | Burkes |
| --- | --- |
| ![Pepper Stucki Palette](generated/pepper/color_stucki_palette_ega16.png) | ![Pepper Burkes Palette](generated/pepper/color_burkes_palette_ega16.png) |

### Palette Study With `sierra2_palette`

| gameboy4 | ega16 | ansi16 |
| --- | --- | --- |
| ![Pepper Game Boy](generated/pepper/palette_sierra2_gameboy4.png) | ![Pepper EGA](generated/pepper/palette_sierra2_ega16.png) | ![Pepper ANSI](generated/pepper/palette_sierra2_ansi16.png) |

| web216 | term256 |
| --- | --- |
| ![Pepper web216](generated/pepper/palette_sierra2_web216.png) | ![Pepper term256](generated/pepper/palette_sierra2_term256.png) |

### Extracted Palette Quantization

These examples isolate the palette extraction step by directly quantizing with a 64-color palette extracted from the image, without error diffusion.

| RGB-extracted palette | YCoCg-extracted palette |
| --- | --- |
| ![Pepper RGB palette](generated/pepper/extracted_palette_rgb.png) | ![Pepper YCoCg palette](generated/pepper/extracted_palette_ycocg.png) |

| RGB quantized | YCoCg quantized |
| --- | --- |
| ![Pepper RGB quantized](generated/pepper/extracted_quantized_rgb.png) | ![Pepper YCoCg quantized](generated/pepper/extracted_quantized_ycocg.png) |

## Flower

Flower is useful for saturated edges and local contrast. It shows how aggressively a filter breaks up petal detail.

### Source

![Flower source](generated/flower/source.png)

### Grayscale Diffusion

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Flower Atkinson](generated/flower/grayscale_atkinson.png) | ![Flower Sierra-2](generated/flower/grayscale_sierra2.png) | ![Flower Sierra-3](generated/flower/grayscale_sierra3.png) |

| Stucki | Burkes | Blue-noise |
| --- | --- | --- |
| ![Flower Stucki](generated/flower/grayscale_stucki.png) | ![Flower Burkes](generated/flower/grayscale_burkes.png) | ![Flower Blue-noise](generated/flower/grayscale_bluenoise.png) |

### Color Diffusion With `ega16`

| Atkinson | Sierra-2 | Sierra-3 |
| --- | --- | --- |
| ![Flower Atkinson Palette](generated/flower/color_atkinson_palette_ega16.png) | ![Flower Sierra-2 Palette](generated/flower/color_sierra2_palette_ega16.png) | ![Flower Sierra-3 Palette](generated/flower/color_sierra3_palette_ega16.png) |

| Stucki | Burkes |
| --- | --- |
| ![Flower Stucki Palette](generated/flower/color_stucki_palette_ega16.png) | ![Flower Burkes Palette](generated/flower/color_burkes_palette_ega16.png) |

### Palette Study With `sierra2_palette`

| gameboy4 | ega16 | ansi16 |
| --- | --- | --- |
| ![Flower Game Boy](generated/flower/palette_sierra2_gameboy4.png) | ![Flower EGA](generated/flower/palette_sierra2_ega16.png) | ![Flower ANSI](generated/flower/palette_sierra2_ansi16.png) |

| web216 | term256 |
| --- | --- |
| ![Flower web216](generated/flower/palette_sierra2_web216.png) | ![Flower term256](generated/flower/palette_sierra2_term256.png) |

### Extracted Palette Quantization

These examples isolate the palette extraction step by directly quantizing with a 64-color palette extracted from the image, without error diffusion.

| RGB-extracted palette | YCoCg-extracted palette |
| --- | --- |
| ![Flower RGB palette](generated/flower/extracted_palette_rgb.png) | ![Flower YCoCg palette](generated/flower/extracted_palette_ycocg.png) |

| RGB quantized | YCoCg quantized |
| --- | --- |
| ![Flower RGB quantized](generated/flower/extracted_quantized_rgb.png) | ![Flower YCoCg quantized](generated/flower/extracted_quantized_ycocg.png) |