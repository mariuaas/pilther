const std = @import("std");

fn diffuse(err_buf: []i16, idx: usize, diff: i16, weight: i16, divisor: i16) void {
    err_buf[idx] += @divTrunc(diff * weight, divisor);
}

export fn sierra3_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    if (width <= 0 or height <= 0) {
        return 2;
    }

    const w: usize = @intCast(width);
    const h: usize = @intCast(height);

    const err_buf = std.heap.page_allocator.alloc(i16, w * h) catch return 1;
    defer std.heap.page_allocator.free(err_buf);
    @memset(err_buf, 0);

    for (0..h) |y| {
        for (0..w) |x| {
            const idx = y * w + x;
            const old: i16 = @as(i16, buf[idx]) + err_buf[idx];
            const new_val: u8 = if (old >= 128) 255 else 0;
            buf[idx] = new_val;
            const diff: i16 = old - @as(i16, new_val);

            if (x + 1 < w) diffuse(err_buf, idx + 1, diff, 5, 32);
            if (x + 2 < w) diffuse(err_buf, idx + 2, diff, 3, 32);
            if (y + 1 < h) {
                const row = idx + w;
                if (x >= 2) diffuse(err_buf, row - 2, diff, 2, 32);
                if (x >= 1) diffuse(err_buf, row - 1, diff, 4, 32);
                diffuse(err_buf, row, diff, 5, 32);
                if (x + 1 < w) diffuse(err_buf, row + 1, diff, 4, 32);
                if (x + 2 < w) diffuse(err_buf, row + 2, diff, 2, 32);
            }
            if (y + 2 < h) {
                const row = idx + 2 * w;
                if (x >= 1) diffuse(err_buf, row - 1, diff, 2, 32);
                diffuse(err_buf, row, diff, 3, 32);
                if (x + 1 < w) diffuse(err_buf, row + 1, diff, 2, 32);
            }
        }
    }

    return 0;
}