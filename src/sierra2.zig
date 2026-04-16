const std = @import("std");
const ring = @import("diffusion_ring.zig");

fn diffuse(row: []i16, x: usize, diff: i16, weight: i16, divisor: i16) void {
    row[x] += @divTrunc(diff * weight, divisor);
}

pub fn sierra2_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }

    const w: usize = @intCast(width);
    const h: usize = @intCast(height);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();

    var err_buf = ring.ErrorRing.init(gpa.allocator(), w, 2) catch return 1;
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

            if (x + 1 < w) diffuse(current, x + 1, diff, 4, 16);
            if (x + 2 < w) diffuse(current, x + 2, diff, 3, 16);
            if (y + 1 < h) {
                const next = err_buf.row(y + 1);
                if (x >= 2) diffuse(next, x - 2, diff, 1, 16);
                if (x >= 1) diffuse(next, x - 1, diff, 2, 16);
                diffuse(next, x, diff, 3, 16);
                if (x + 1 < w) diffuse(next, x + 1, diff, 2, 16);
                if (x + 2 < w) diffuse(next, x + 2, diff, 1, 16);
            }
        }
    }

    return 0;
}
