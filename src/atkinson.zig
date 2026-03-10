const std = @import("std");

export fn atkinson_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
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
            const diff: i16 = @divTrunc(old - @as(i16, new_val), 8);

            if (x + 1 < w) err_buf[idx + 1] += diff;
            if (x + 2 < w) err_buf[idx + 2] += diff;
            if (y + 1 < h) {
                if (x > 0) err_buf[idx + w - 1] += diff;
                err_buf[idx + w] += diff;
                if (x + 1 < w) err_buf[idx + w + 1] += diff;
            }
            if (y + 2 < h) err_buf[idx + 2 * w] += diff;
        }
    }

    return 0;
}
