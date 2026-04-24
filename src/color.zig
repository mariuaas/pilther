const std = @import("std");

pub const ColorSpace = enum(c_int) {
    rgb = 0,
    ycocg = 1,
    grayscale = 2,
};

pub const Rgb = struct {
    r: f32,
    g: f32,
    b: f32,
};

pub const WorkingColor = struct {
    c0: f32,
    c1: f32,
    c2: f32,
};

pub fn toWorkingColor(rgb: Rgb, color_space: ColorSpace) WorkingColor {
    return switch (color_space) {
        .grayscale => rgbToGrayscale(rgb),
        .rgb => .{ .c0 = rgb.r, .c1 = rgb.g, .c2 = rgb.b },
        .ycocg => rgbToYCoCg(rgb),
    };
}

pub fn clampRgb(rgb: Rgb) Rgb {
    return .{
        .r = std.math.clamp(rgb.r, 0.0, 255.0),
        .g = std.math.clamp(rgb.g, 0.0, 255.0),
        .b = std.math.clamp(rgb.b, 0.0, 255.0),
    };
}

pub fn floatToByte(value: f32) u8 {
    const clipped = std.math.clamp(value, 0.0, 255.0);
    return @as(u8, @intFromFloat(@round(clipped)));
}

fn rgbToGrayscale(rgb: Rgb) WorkingColor {
    const value = (0.299 * rgb.r) + (0.587 * rgb.g) + (0.114 * rgb.b);
    return .{ .c0 = value, .c1 = value, .c2 = value };
}

fn rgbToYCoCg(rgb: Rgb) WorkingColor {
    const co = rgb.r - rgb.b;
    const tmp = rgb.b + (co / 2.0);
    const cg = rgb.g - tmp;
    const y = tmp + (cg / 2.0);
    return .{ .c0 = y, .c1 = co, .c2 = cg };
}
