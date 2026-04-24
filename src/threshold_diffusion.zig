const std = @import("std");
const kernel_defs = @import("kernel.zig");
const ring = @import("diffusion_ring.zig");

const DiffusionStep = kernel_defs.DiffusionStep;
const Kernel = kernel_defs.Kernel;

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

fn threshold_dither(buf: [*]u8, width: c_int, height: c_int, kernel: Kernel) c_int {
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

fn diffuseKernel(kernel: Kernel, x: usize, y: usize, height: usize, width: usize, diff: i16, err_buf: *ring.ErrorRing) void {
    const divisor: i16 = @intCast(kernel_defs.divisor(kernel));
    for (kernel_defs.steps(kernel)) |step| {
        applyStep(step, x, y, width, height, diff, divisor, err_buf);
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
