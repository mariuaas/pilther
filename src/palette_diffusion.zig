const std = @import("std");
const color = @import("color.zig");
const kernel_defs = @import("kernel.zig");

const ColorSpace = color.ColorSpace;
const DiffusionStep = kernel_defs.DiffusionStep;
const Kernel = kernel_defs.Kernel;

const GenericKernel = struct {
    divisor: f32,
    depth: usize,
    steps_buf: [*]const i16,
    step_count: usize,
};

const Rgb = color.Rgb;
const WorkingColor = color.WorkingColor;

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
            space[index] = color.toWorkingColor(rgb_color, color_space);
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

pub fn generic_palette_dither(
    img_buf: [*]u8,
    width: c_int,
    height: c_int,
    palette_buf: [*]u8,
    palette_colors: c_int,
    color_space: c_int,
    steps_buf: [*]const i16,
    step_count: c_int,
    divisor: c_int,
    depth: c_int,
) c_int {
    if (step_count <= 0 or divisor <= 0 or depth <= 0) {
        return 5;
    }

    const kernel = GenericKernel{
        .divisor = @as(f32, @floatFromInt(divisor)),
        .depth = @intCast(depth),
        .steps_buf = steps_buf,
        .step_count = @intCast(step_count),
    };
    return palette_dither_generic(img_buf, width, height, palette_buf, palette_colors, color_space, kernel);
}

fn palette_dither(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space_raw: c_int, kernel: Kernel) c_int {
    return palette_dither_builtin(img_buf, width, height, palette_buf, palette_colors, color_space_raw, kernel);
}

fn palette_dither_builtin(img_buf: [*]u8, width: c_int, height: c_int, palette_buf: [*]u8, palette_colors: c_int, color_space_raw: c_int, kernel: Kernel) c_int {
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

    var err_ring = ColorErrorRing.init(allocator, w, kernel_defs.depth(kernel)) catch return 1;
    defer err_ring.deinit();

    for (0..h) |y| {
        err_ring.prepareRow(y);
        const current = err_ring.row(y);

        for (0..w) |x| {
            const idx = (y * w + x) * 3;
            const adjusted = color.clampRgb(Rgb{
                .r = @as(f32, @floatFromInt(img_buf[idx])) + current[x].r,
                .g = @as(f32, @floatFromInt(img_buf[idx + 1])) + current[x].g,
                .b = @as(f32, @floatFromInt(img_buf[idx + 2])) + current[x].b,
            });
            const chosen_index = nearestPaletteIndex(adjusted, palette.space, color_space);
            const chosen = palette.rgb[chosen_index];

            img_buf[idx] = color.floatToByte(chosen.r);
            img_buf[idx + 1] = color.floatToByte(chosen.g);
            img_buf[idx + 2] = color.floatToByte(chosen.b);

            const diff = Rgb{
                .r = adjusted.r - chosen.r,
                .g = adjusted.g - chosen.g,
                .b = adjusted.b - chosen.b,
            };

            diffuseKernel(kernel, x, y, h, w, diff, &err_ring);
        }
    }

    return 0;
}

fn palette_dither_generic(
    img_buf: [*]u8,
    width: c_int,
    height: c_int,
    palette_buf: [*]u8,
    palette_colors: c_int,
    color_space_raw: c_int,
    kernel: GenericKernel,
) c_int {
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

    var err_ring = ColorErrorRing.init(allocator, w, kernel.depth) catch return 1;
    defer err_ring.deinit();

    for (0..h) |y| {
        err_ring.prepareRow(y);
        const current = err_ring.row(y);

        for (0..w) |x| {
            const idx = (y * w + x) * 3;
            const adjusted = color.clampRgb(Rgb{
                .r = @as(f32, @floatFromInt(img_buf[idx])) + current[x].r,
                .g = @as(f32, @floatFromInt(img_buf[idx + 1])) + current[x].g,
                .b = @as(f32, @floatFromInt(img_buf[idx + 2])) + current[x].b,
            });
            const chosen_index = nearestPaletteIndex(adjusted, palette.space, color_space);
            const chosen = palette.rgb[chosen_index];

            img_buf[idx] = color.floatToByte(chosen.r);
            img_buf[idx + 1] = color.floatToByte(chosen.g);
            img_buf[idx + 2] = color.floatToByte(chosen.b);

            const diff = Rgb{
                .r = adjusted.r - chosen.r,
                .g = adjusted.g - chosen.g,
                .b = adjusted.b - chosen.b,
            };

            diffuseGenericKernel(kernel, x, y, h, w, diff, &err_ring);
        }
    }

    return 0;
}

fn diffuseKernel(kernel: Kernel, x: usize, y: usize, height: usize, width: usize, diff: Rgb, err_ring: *ColorErrorRing) void {
    const divisor = @as(f32, @floatFromInt(kernel_defs.divisor(kernel)));
    for (kernel_defs.steps(kernel)) |step| {
        applyStep(step, x, y, width, height, diff, divisor, err_ring);
    }
}

fn diffuseGenericKernel(kernel: GenericKernel, x: usize, y: usize, height: usize, width: usize, diff: Rgb, err_ring: *ColorErrorRing) void {
    for (0..kernel.step_count) |step_index| {
        const base = step_index * 3;
        const dx = kernel.steps_buf[base];
        const dy = kernel.steps_buf[base + 1];
        const weight = kernel.steps_buf[base + 2];
        if (dy < 0 or weight <= 0) {
            continue;
        }

        applyGenericStep(dx, dy, weight, x, y, width, height, diff, kernel.divisor, err_ring);
    }
}

fn applyStep(step: DiffusionStep, x: usize, y: usize, width: usize, height: usize, diff: Rgb, divisor: f32, err_ring: *ColorErrorRing) void {
    const target_y = y + step.dy;
    if (target_y >= height) {
        return;
    }

    const shifted_x = @as(isize, @intCast(x)) + step.dx;
    if (shifted_x < 0 or shifted_x >= @as(isize, @intCast(width))) {
        return;
    }

    addScaledError(
        &err_ring.row(target_y)[@as(usize, @intCast(shifted_x))],
        diff,
        @as(f32, @floatFromInt(step.weight)) / divisor,
    );
}

fn applyGenericStep(dx: i16, dy: i16, weight: i16, x: usize, y: usize, width: usize, height: usize, diff: Rgb, divisor: f32, err_ring: *ColorErrorRing) void {
    const target_y_signed = @as(isize, @intCast(y)) + dy;
    if (target_y_signed < 0 or target_y_signed >= @as(isize, @intCast(height))) {
        return;
    }

    const shifted_x = @as(isize, @intCast(x)) + dx;
    if (shifted_x < 0 or shifted_x >= @as(isize, @intCast(width))) {
        return;
    }

    addScaledError(
        &err_ring.row(@as(usize, @intCast(target_y_signed)))[@as(usize, @intCast(shifted_x))],
        diff,
        @as(f32, @floatFromInt(weight)) / divisor,
    );
}

fn addScaledError(target: *Rgb, diff: Rgb, factor: f32) void {
    target.r += diff.r * factor;
    target.g += diff.g * factor;
    target.b += diff.b * factor;
}

fn nearestPaletteIndex(rgb: Rgb, palette_space: []const WorkingColor, color_space: ColorSpace) usize {
    const working = color.toWorkingColor(rgb, color_space);

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

fn distanceSquared(lhs: WorkingColor, rhs: WorkingColor) f32 {
    const d0 = lhs.c0 - rhs.c0;
    const d1 = lhs.c1 - rhs.c1;
    const d2 = lhs.c2 - rhs.c2;
    return (d0 * d0) + (d1 * d1) + (d2 * d2);
}
