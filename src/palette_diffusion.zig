const std = @import("std");

const ColorSpace = enum(c_int) {
    rgb = 0,
    ycocg = 1,
};

const KernelKind = enum {
    atkinson,
    sierra2,
    sierra3,
    stucki,
    burkes,
};

const Rgb = struct {
    r: f32,
    g: f32,
    b: f32,
};

const WorkingColor = struct {
    c0: f32,
    c1: f32,
    c2: f32,
};

const PaletteData = struct {
    rgb: []Rgb,
    space: []WorkingColor,

    fn init(allocator: std.mem.Allocator, palette_buf: [*]u8, palette_colors: usize, color_space: ColorSpace) !PaletteData {
        var rgb = try allocator.alloc(Rgb, palette_colors);
        errdefer allocator.free(rgb);

        var space = try allocator.alloc(WorkingColor, palette_colors);
        errdefer allocator.free(space);

        for (0..palette_colors) |index| {
            const base = index * 3;
            const rgb_color = Rgb{
                .r = @as(f32, @floatFromInt(palette_buf[base])),
                .g = @as(f32, @floatFromInt(palette_buf[base + 1])),
                .b = @as(f32, @floatFromInt(palette_buf[base + 2])),
            };
            rgb[index] = rgb_color;
            space[index] = toWorkingColor(rgb_color, color_space);
        }

        return .{
            .rgb = rgb,
            .space = space,
        };
    }

    fn deinit(self: *PaletteData, allocator: std.mem.Allocator) void {
        allocator.free(self.rgb);
        allocator.free(self.space);
    }
};

const ColorErrorRing = struct {
    allocator: std.mem.Allocator,
    data: []Rgb,
    width: usize,
    depth: usize,

    fn init(allocator: std.mem.Allocator, width: usize, depth: usize) !ColorErrorRing {
        const data = try allocator.alloc(Rgb, width * depth);
        @memset(data, zero_rgb);

        return .{
            .allocator = allocator,
            .data = data,
            .width = width,
            .depth = depth,
        };
    }

    fn deinit(self: *ColorErrorRing) void {
        self.allocator.free(self.data);
    }

    fn prepareRow(self: *ColorErrorRing, absolute_row: usize) void {
        const recycled_row = absolute_row + self.depth - 1;
        const start = (recycled_row % self.depth) * self.width;
        @memset(self.data[start .. start + self.width], zero_rgb);
    }

    fn row(self: *ColorErrorRing, absolute_row: usize) []Rgb {
        const start = (absolute_row % self.depth) * self.width;
        return self.data[start .. start + self.width];
    }
};

const zero_rgb = Rgb{ .r = 0.0, .g = 0.0, .b = 0.0 };

pub fn atkinson_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space, .atkinson);
}

pub fn sierra2_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space, .sierra2);
}

pub fn sierra3_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space, .sierra3);
}

pub fn stucki_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space, .stucki);
}

pub fn burkes_palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space: c_int) c_int {
    return palette_dither(img_buf, width, height, palette_buf, palette_colors, color_space, .burkes);
}

fn palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space_raw: c_int, kernel: KernelKind) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }
    if (palette_colors <= 0) {
        return 3;
    }

    const color_space = std.meta.intToEnum(ColorSpace, color_space_raw) catch return 4;
    const w: usize = @intCast(width);
    const h: usize = @intCast(height);
    const palette_len: usize = @intCast(palette_colors);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var palette = PaletteData.init(allocator, palette_buf, palette_len, color_space) catch return 1;
    defer palette.deinit(allocator);

    var err_ring = ColorErrorRing.init(allocator, w, kernelDepth(kernel)) catch return 1;
    defer err_ring.deinit();

    for (0..h) |y| {
        err_ring.prepareRow(y);
        const current = err_ring.row(y);

        for (0..w) |x| {
            const idx = (y * w + x) * 3;
            const adjusted = clampRgb(Rgb{
                .r = @as(f32, @floatFromInt(img_buf[idx])) + current[x].r,
                .g = @as(f32, @floatFromInt(img_buf[idx + 1])) + current[x].g,
                .b = @as(f32, @floatFromInt(img_buf[idx + 2])) + current[x].b,
            });
            const chosen_index = nearestPaletteIndex(adjusted, palette.space, color_space);
            const chosen = palette.rgb[chosen_index];

            img_buf[idx] = floatToByte(chosen.r);
            img_buf[idx + 1] = floatToByte(chosen.g);
            img_buf[idx + 2] = floatToByte(chosen.b);

            const diff = Rgb{
                .r = adjusted.r - chosen.r,
                .g = adjusted.g - chosen.g,
                .b = adjusted.b - chosen.b,
            };

            diffuseKernel(kernel, x, y, h, diff, &err_ring);
        }
    }

    return 0;
}

fn diffuseKernel(kernel: KernelKind, x: usize, y: usize, height: usize, diff: Rgb, err_ring: *ColorErrorRing) void {
    switch (kernel) {
        .atkinson => {
            diffuseTo(err_ring.row(y), x, diff, 1, 8, 1);
            diffuseTo(err_ring.row(y), x, diff, 2, 8, 1);
            if (y + 1 < height) {
                const next = err_ring.row(y + 1);
                diffuseSigned(next, x, diff, -1, 8, 1);
                diffuseSigned(next, x, diff, 0, 8, 1);
                diffuseSigned(next, x, diff, 1, 8, 1);
            }
            if (y + 2 < height) {
                diffuseSigned(err_ring.row(y + 2), x, diff, 0, 8, 1);
            }
        },
        .sierra2 => {
            diffuseTo(err_ring.row(y), x, diff, 1, 16, 4);
            diffuseTo(err_ring.row(y), x, diff, 2, 16, 3);
            if (y + 1 < height) {
                const next = err_ring.row(y + 1);
                diffuseSigned(next, x, diff, -2, 16, 1);
                diffuseSigned(next, x, diff, -1, 16, 2);
                diffuseSigned(next, x, diff, 0, 16, 3);
                diffuseSigned(next, x, diff, 1, 16, 2);
                diffuseSigned(next, x, diff, 2, 16, 1);
            }
        },
        .sierra3 => {
            diffuseTo(err_ring.row(y), x, diff, 1, 32, 5);
            diffuseTo(err_ring.row(y), x, diff, 2, 32, 3);
            if (y + 1 < height) {
                const next = err_ring.row(y + 1);
                diffuseSigned(next, x, diff, -2, 32, 2);
                diffuseSigned(next, x, diff, -1, 32, 4);
                diffuseSigned(next, x, diff, 0, 32, 5);
                diffuseSigned(next, x, diff, 1, 32, 4);
                diffuseSigned(next, x, diff, 2, 32, 2);
            }
            if (y + 2 < height) {
                const next2 = err_ring.row(y + 2);
                diffuseSigned(next2, x, diff, -1, 32, 2);
                diffuseSigned(next2, x, diff, 0, 32, 3);
                diffuseSigned(next2, x, diff, 1, 32, 2);
            }
        },
        .stucki => {
            diffuseTo(err_ring.row(y), x, diff, 1, 42, 8);
            diffuseTo(err_ring.row(y), x, diff, 2, 42, 4);
            if (y + 1 < height) {
                const next = err_ring.row(y + 1);
                diffuseSigned(next, x, diff, -2, 42, 2);
                diffuseSigned(next, x, diff, -1, 42, 4);
                diffuseSigned(next, x, diff, 0, 42, 8);
                diffuseSigned(next, x, diff, 1, 42, 4);
                diffuseSigned(next, x, diff, 2, 42, 2);
            }
            if (y + 2 < height) {
                const next2 = err_ring.row(y + 2);
                diffuseSigned(next2, x, diff, -2, 42, 1);
                diffuseSigned(next2, x, diff, -1, 42, 2);
                diffuseSigned(next2, x, diff, 0, 42, 4);
                diffuseSigned(next2, x, diff, 1, 42, 2);
                diffuseSigned(next2, x, diff, 2, 42, 1);
            }
        },
        .burkes => {
            diffuseTo(err_ring.row(y), x, diff, 1, 32, 8);
            diffuseTo(err_ring.row(y), x, diff, 2, 32, 4);
            if (y + 1 < height) {
                const next = err_ring.row(y + 1);
                diffuseSigned(next, x, diff, -2, 32, 2);
                diffuseSigned(next, x, diff, -1, 32, 4);
                diffuseSigned(next, x, diff, 0, 32, 8);
                diffuseSigned(next, x, diff, 1, 32, 4);
                diffuseSigned(next, x, diff, 2, 32, 2);
            }
        },
    }
}

fn diffuseTo(row: []Rgb, x: usize, diff: Rgb, positive_dx: usize, divisor: comptime_float, weight: comptime_float) void {
    if (x + positive_dx >= row.len) {
        return;
    }
    addScaledError(&row[x + positive_dx], diff, weight / divisor);
}

fn diffuseSigned(row: []Rgb, x: usize, diff: Rgb, dx: isize, divisor: comptime_float, weight: comptime_float) void {
    const shifted = @as(isize, @intCast(x)) + dx;
    if (shifted < 0 or shifted >= @as(isize, @intCast(row.len))) {
        return;
    }
    addScaledError(&row[@as(usize, @intCast(shifted))], diff, weight / divisor);
}

fn addScaledError(target: *Rgb, diff: Rgb, factor: f32) void {
    target.r += diff.r * factor;
    target.g += diff.g * factor;
    target.b += diff.b * factor;
}

fn kernelDepth(kernel: KernelKind) usize {
    return switch (kernel) {
        .atkinson, .sierra3, .stucki => 3,
        .sierra2, .burkes => 2,
    };
}

fn nearestPaletteIndex(rgb: Rgb, palette_space: []const WorkingColor, color_space: ColorSpace) usize {
    const working = toWorkingColor(rgb, color_space);

    var best_index: usize = 0;
    var best_distance = distanceSquared(working, palette_space[0]);

    for (palette_space[1..], 1..) |candidate, index| {
        const distance = distanceSquared(working, candidate);
        if (distance < best_distance) {
            best_distance = distance;
            best_index = index;
        }
    }

    return best_index;
}

fn toWorkingColor(rgb: Rgb, color_space: ColorSpace) WorkingColor {
    return switch (color_space) {
        .rgb => .{ .c0 = rgb.r, .c1 = rgb.g, .c2 = rgb.b },
        .ycocg => rgbToYCoCg(rgb),
    };
}

fn rgbToYCoCg(rgb: Rgb) WorkingColor {
    const co = rgb.r - rgb.b;
    const tmp = rgb.b + (co / 2.0);
    const cg = rgb.g - tmp;
    const y = tmp + (cg / 2.0);
    return .{ .c0 = y, .c1 = co, .c2 = cg };
}

fn distanceSquared(lhs: WorkingColor, rhs: WorkingColor) f32 {
    const d0 = lhs.c0 - rhs.c0;
    const d1 = lhs.c1 - rhs.c1;
    const d2 = lhs.c2 - rhs.c2;
    return (d0 * d0) + (d1 * d1) + (d2 * d2);
}

fn clampRgb(rgb: Rgb) Rgb {
    return .{
        .r = std.math.clamp(rgb.r, 0.0, 255.0),
        .g = std.math.clamp(rgb.g, 0.0, 255.0),
        .b = std.math.clamp(rgb.b, 0.0, 255.0),
    };
}

fn floatToByte(value: f32) u8 {
    const clipped = std.math.clamp(value, 0.0, 255.0);
    return @as(u8, @intFromFloat(@round(clipped)));
}
