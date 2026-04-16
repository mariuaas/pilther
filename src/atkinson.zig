const std = @import("std");
const ring = @import("diffusion_ring.zig");

pub fn atkinson_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }

    const w: usize = @intCast(width);
    const h: usize = @intCast(height);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();

    var err_buf = ring.ErrorRing.init(gpa.allocator(), w, 3) catch return 1;
    defer err_buf.deinit();

    for (0..h) |y| {
        err_buf.prepareRow(y);
        const current = err_buf.row(y);

        for (0..w) |x| {
            const idx = y * w + x;
            const old: i16 = @as(i16, buf[idx]) + current[x];
            const new_val: u8 = if (old >= 128) 255 else 0;
            buf[idx] = new_val;
            const diff: i16 = @divTrunc(old - @as(i16, new_val), 8);

            if (x + 1 < w) current[x + 1] += diff;
            if (x + 2 < w) current[x + 2] += diff;
            if (y + 1 < h) {
                const next = err_buf.row(y + 1);
                if (x > 0) next[x - 1] += diff;
                next[x] += diff;
                if (x + 1 < w) next[x + 1] += diff;
            }
            if (y + 2 < h) {
                const next2 = err_buf.row(y + 2);
                next2[x] += diff;
            }
        }
    }

    return 0;
}
