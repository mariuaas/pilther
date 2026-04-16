const std = @import("std");

pub const ErrorRing = struct {
    allocator: std.mem.Allocator,
    data: []i16,
    width: usize,
    depth: usize,

    pub fn init(allocator: std.mem.Allocator, width: usize, depth: usize) !ErrorRing {
        const data = try allocator.alloc(i16, width * depth);
        @memset(data, 0);

        return .{
            .allocator = allocator,
            .data = data,
            .width = width,
            .depth = depth,
        };
    }

    pub fn deinit(self: *ErrorRing) void {
        self.allocator.free(self.data);
    }

    pub fn prepareRow(self: *ErrorRing, absolute_row: usize) void {
        const recycled_row = absolute_row + self.depth - 1;
        const start = (recycled_row % self.depth) * self.width;
        @memset(self.data[start .. start + self.width], 0);
    }

    pub fn row(self: *ErrorRing, absolute_row: usize) []i16 {
        const start = (absolute_row % self.depth) * self.width;
        return self.data[start .. start + self.width];
    }
};
