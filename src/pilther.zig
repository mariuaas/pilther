const atkinson = @import("atkinson.zig");
const burkes = @import("burkes.zig");
const sierra2 = @import("sierra2.zig");
const sierra3 = @import("sierra3.zig");
const stucki = @import("stucki.zig");

export fn atkinson_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return atkinson.atkinson_dither(buf, width, height);
}

export fn burkes_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return burkes.burkes_dither(buf, width, height);
}

export fn sierra2_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return sierra2.sierra2_dither(buf, width, height);
}

export fn sierra3_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return sierra3.sierra3_dither(buf, width, height);
}

export fn stucki_dither(buf: [*]u8, width: c_int, height: c_int) c_int {
    return stucki.stucki_dither(buf, width, height);
}
