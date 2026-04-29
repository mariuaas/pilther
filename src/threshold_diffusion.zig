const std = @import("std");
const kernel_defs = @import("kernel.zig");
const ring = @import("diffusion_ring.zig");

const DiffusionStep = kernel_defs.DiffusionStep;
const Kernel = kernel_defs.Kernel;

const GenericKernel = struct {
    divisor: i16,
    depth: usize,
    steps_buf: [*]const i16,
    step_count: usize,
};

pub fn atkinson_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_dither(buf, width, height, .atkinson);
}

pub fn sierra2_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_dither(buf, width, height, .sierra2);
}

pub fn sierra3_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_dither(buf, width, height, .sierra3);
}

pub fn stucki_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_dither(buf, width, height, .stucki);
}

pub fn burkes_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return threshold_dither(buf, width, height, .burkes);
}

pub fn generic_dither(
    buf: [*]u8,
    width: c_int,
    height: c_int,
    steps_buf: [*]const i16,
    step_count: c_int,
    divisor: c_int,
    depth: c_int,
) c_int {
    if (step_count <= 0 or divisor <= 0 or depth <= 0) {
        return 3;
    }

    const kernel = GenericKernel{
        .divisor = std.math.cast(i16, divisor) orelse return 3,
        .depth = @intCast(depth),
        .steps_buf = steps_buf,
        .step_count = @intCast(step_count),
    };
    return threshold_dither_generic(buf, width, height, kernel);
}

fn threshold_dither(buf: [*]u8, width: c_int, height: c_int, kernel: Kernel) c_int {
    return threshold_dither_builtin(buf, width, height, kernel);
}

fn threshold_dither_builtin(buf: [*]u8, width: c_int, height: c_int, kernel: Kernel) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }

    const w: usize = @intCast(width);
    const h: usize = @intCast(height);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();

    var err_buf = ring.ErrorRing.init(gpa.allocator(), w, kernel_defs.depth(kernel)) catch return 1;
    defer err_buf.deinit();

    for (0..h) |y| {
        err_buf.prepareRow(y);
        const current = err_buf.row(y);

        for (0..w) |x| {
            const idx = y * w + x;
            const old: i16 = @as(i16, buf[idx]) + current[x];
            const new_val: u8 = if (old >= 128) 255 else 0;
            buf[idx] = new_val;
            const diff: i16 = old - @as(i16, new_val);

            diffuseKernel(kernel, x, y, h, w, diff, &err_buf);
        }
    }

    return 0;
}

fn threshold_dither_generic(buf: [*]u8, width: c_int, height: c_int, kernel: GenericKernel) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }

    const w: usize = @intCast(width);
    const h: usize = @intCast(height);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();

    var err_buf = ring.ErrorRing.init(gpa.allocator(), w, kernel.depth) catch return 1;
    defer err_buf.deinit();

    for (0..h) |y| {
        err_buf.prepareRow(y);
        const current = err_buf.row(y);

        for (0..w) |x| {
            const idx = y * w + x;
            const old: i16 = @as(i16, buf[idx]) + current[x];
            const new_val: u8 = if (old >= 128) 255 else 0;
            buf[idx] = new_val;
            const diff: i16 = old - @as(i16, new_val);

            diffuseGenericKernel(kernel, x, y, h, w, diff, &err_buf);
        }
    }

    return 0;
}

fn diffuseKernel(kernel: Kernel, x: usize, y: usize, height: usize, width: usize, diff: i16, err_buf: *ring.ErrorRing) void {
    const divisor: i16 = @intCast(kernel_defs.divisor(kernel));
    for (kernel_defs.steps(kernel)) |step| {
        applyStep(step, x, y, width, height, diff, divisor, err_buf);
    }
}

fn diffuseGenericKernel(kernel: GenericKernel, x: usize, y: usize, height: usize, width: usize, diff: i16, err_buf: *ring.ErrorRing) void {
    for (0..kernel.step_count) |step_index| {
        const base = step_index * 3;
        const dx = kernel.steps_buf[base];
        const dy = kernel.steps_buf[base + 1];
        const weight = kernel.steps_buf[base + 2];
        if (dy < 0 or weight <= 0) {
            continue;
        }

        applyGenericStep(dx, dy, weight, x, y, width, height, diff, kernel.divisor, err_buf);
    }
}

fn applyStep(step: DiffusionStep, x: usize, y: usize, width: usize, height: usize, diff: i16, divisor: i16, err_buf: *ring.ErrorRing) void {
    const target_y = y + step.dy;
    if (target_y >= height) {
        return;
    }

    const shifted_x = @as(isize, @intCast(x)) + step.dx;
    if (shifted_x < 0 or shifted_x >= @as(isize, @intCast(width))) {
        return;
    }

    const row = err_buf.row(target_y);
    row[@as(usize, @intCast(shifted_x))] += @divTrunc(diff * @as(i16, step.weight), divisor);
}

fn applyGenericStep(dx: i16, dy: i16, weight: i16, x: usize, y: usize, width: usize, height: usize, diff: i16, divisor: i16, err_buf: *ring.ErrorRing) void {
    const target_y_signed = @as(isize, @intCast(y)) + dy;
    if (target_y_signed < 0 or target_y_signed >= @as(isize, @intCast(height))) {
        return;
    }

    const shifted_x = @as(isize, @intCast(x)) + dx;
    if (shifted_x < 0 or shifted_x >= @as(isize, @intCast(width))) {
        return;
    }

    const row = err_buf.row(@as(usize, @intCast(target_y_signed)));
    row[@as(usize, @intCast(shifted_x))] += @divTrunc(diff * weight, divisor);
}
