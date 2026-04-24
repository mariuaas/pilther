const palette_diffusion = @import("palette_diffusion.zig");
const threshold_diffusion = @import("threshold_diffusion.zig");

export fn atkinson_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_diffusion.atkinson_dither(buf, width, height);
}

export fn burkes_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_diffusion.burkes_dither(buf, width, height);
}

export fn sierra2_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_diffusion.sierra2_dither(buf, width, height);
}

export fn sierra3_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_diffusion.sierra3_dither(buf, width, height);
}

export fn stucki_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_diffusion.stucki_dither(buf, width, height);
}

export fn atkinson_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_diffusion.atkinson_palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space);
}

export fn sierra2_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_diffusion.sierra2_palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space);
}

export fn sierra3_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_diffusion.sierra3_palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space);
}

export fn stucki_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_diffusion.stucki_palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space);
}

export fn burkes_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_diffusion.burkes_palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space);
}
