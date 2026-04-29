const std = @import("std");

pub const Kernel = enum {
    atkinson,
    sierra2,
    sierra3,
    stucki,
    burkes,
};

pub const DiffusionStep = struct {
    dx: i8,
    dy: u8,
    weight: u8,
};

const atkinson_matrix = [5][5]i16{
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 1, 1 },
    .{ 0, 1, 1, 1, 0 },
    .{ 0, 0, 1, 0, 0 },
};

const sierra2_matrix = [3][5]i16{
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 4, 3 },
    .{ 1, 2, 3, 2, 1 },
};

const sierra3_matrix = [5][5]i16{
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 5, 3 },
    .{ 2, 4, 5, 4, 2 },
    .{ 0, 2, 3, 2, 0 },
};

const stucki_matrix = [5][5]i16{
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 8, 4 },
    .{ 2, 4, 8, 4, 2 },
    .{ 1, 2, 4, 2, 1 },
};

const burkes_matrix = [3][5]i16{
    .{ 0, 0, 0, 0, 0 },
    .{ 0, 0, 0, 8, 4 },
    .{ 2, 4, 8, 4, 2 },
};

const atkinson_compiled = compileKernel(8, atkinson_matrix);
const sierra2_compiled = compileKernel(16, sierra2_matrix);
const sierra3_compiled = compileKernel(32, sierra3_matrix);
const stucki_compiled = compileKernel(42, stucki_matrix);
const burkes_compiled = compileKernel(32, burkes_matrix);

fn CompiledKernelType(comptime matrix: anytype) type {
    const Matrix = @TypeOf(matrix);
    const matrix_info = @typeInfo(Matrix);
    if (matrix_info != .array) {
        @compileError("Kernel matrix must be an array of rows.");
    }

    const row_count = matrix_info.array.len;
    if (row_count == 0 or row_count % 2 == 0) {
        @compileError("Kernel matrices must have a non-zero odd number of rows.");
    }

    const Row = matrix_info.array.child;
    const row_info = @typeInfo(Row);
    if (row_info != .array) {
        @compileError("Kernel matrix rows must be arrays.");
    }

    const column_count = row_info.array.len;
    if (column_count == 0 or column_count % 2 == 0) {
        @compileError("Kernel matrices must have a non-zero odd number of columns.");
    }

    comptime {
        for (matrix) |row| {
            if (row.len != column_count) {
                @compileError("Kernel matrix rows must all have the same width.");
            }
        }
    }

    const center_y = row_count / 2;
    const center_x = column_count / 2;

    const step_count = comptime blk: {
        var count: usize = 0;
        for (matrix, 0..) |row, y| {
            for (row, 0..) |weight, x| {
                const dy = @as(isize, @intCast(y)) - @as(isize, @intCast(center_y));
                const dx = @as(isize, @intCast(x)) - @as(isize, @intCast(center_x));
                if (weight == 0) continue;
                if (dy < 0) continue;
                if (dy == 0 and dx <= 0) continue;
                count += 1;
            }
        }
        break :blk count;
    };

    if (step_count == 0) {
        @compileError("Kernel matrix must contain at least one non-zero future weight.");
    }

    return struct {
        divisor: u8,
        depth: usize,
        steps: [step_count]DiffusionStep,
    };
}

fn compileKernel(comptime divisor_value: u8, comptime matrix: anytype) CompiledKernelType(matrix) {
    const CompiledKernel = CompiledKernelType(matrix);
    const step_count = @typeInfo(@typeInfo(CompiledKernel).@"struct".fields[2].type).array.len;
    const matrix_info = @typeInfo(@TypeOf(matrix)).array;
    const row_count = matrix_info.len;
    const column_count = @typeInfo(matrix_info.child).array.len;
    const center_y = row_count / 2;
    const center_x = column_count / 2;

    comptime {
        if (divisor_value == 0) {
            @compileError("Kernel divisor must be positive.");
        }
    }

    var compiled_steps: [step_count]DiffusionStep = undefined;
    var step_index: usize = 0;
    var max_dy: usize = 0;

    inline for (matrix, 0..) |row, y| {
        inline for (row, 0..) |weight, x| {
            if (weight == 0) continue;

            const dy = @as(isize, @intCast(y)) - @as(isize, @intCast(center_y));
            const dx = @as(isize, @intCast(x)) - @as(isize, @intCast(center_x));

            if (dy < 0) continue;
            if (dy == 0 and dx <= 0) continue;

            if (dy > std.math.maxInt(u8)) {
                @compileError("Kernel row offset exceeds supported range.");
            }
            if (dx < std.math.minInt(i8) or dx > std.math.maxInt(i8)) {
                @compileError("Kernel column offset exceeds supported range.");
            }
            if (weight < 0 or weight > std.math.maxInt(u8)) {
                @compileError("Kernel weights must fit in u8 after filtering future values.");
            }

            const step_dy: u8 = @intCast(dy);
            compiled_steps[step_index] = .{
                .dx = @intCast(dx),
                .dy = step_dy,
                .weight = @intCast(weight),
            };
            max_dy = @max(max_dy, step_dy);
            step_index += 1;
        }
    }

    return CompiledKernel{
        .divisor = divisor_value,
        .depth = max_dy + 1,
        .steps = compiled_steps,
    };
}

pub fn divisor(kernel: Kernel) u8 {
    return switch (kernel) {
        .atkinson => atkinson_compiled.divisor,
        .sierra2 => sierra2_compiled.divisor,
        .sierra3 => sierra3_compiled.divisor,
        .stucki => stucki_compiled.divisor,
        .burkes => burkes_compiled.divisor,
    };
}

pub fn depth(kernel: Kernel) usize {
    return switch (kernel) {
        .atkinson => atkinson_compiled.depth,
        .sierra2 => sierra2_compiled.depth,
        .sierra3 => sierra3_compiled.depth,
        .stucki => stucki_compiled.depth,
        .burkes => burkes_compiled.depth,
    };
}

pub fn steps(kernel: Kernel) []const DiffusionStep {
    return switch (kernel) {
        .atkinson => atkinson_compiled.steps[0..],
        .sierra2 => sierra2_compiled.steps[0..],
        .sierra3 => sierra3_compiled.steps[0..],
        .stucki => stucki_compiled.steps[0..],
        .burkes => burkes_compiled.steps[0..],
    };
}
