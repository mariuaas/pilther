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

const atkinson_steps = [_]DiffusionStep{
    .{ .dx = 1, .dy = 0, .weight = 1 },
    .{ .dx = 2, .dy = 0, .weight = 1 },
    .{ .dx = -1, .dy = 1, .weight = 1 },
    .{ .dx = 0, .dy = 1, .weight = 1 },
    .{ .dx = 1, .dy = 1, .weight = 1 },
    .{ .dx = 0, .dy = 2, .weight = 1 },
};

const sierra2_steps = [_]DiffusionStep{
    .{ .dx = 1, .dy = 0, .weight = 4 },
    .{ .dx = 2, .dy = 0, .weight = 3 },
    .{ .dx = -2, .dy = 1, .weight = 1 },
    .{ .dx = -1, .dy = 1, .weight = 2 },
    .{ .dx = 0, .dy = 1, .weight = 3 },
    .{ .dx = 1, .dy = 1, .weight = 2 },
    .{ .dx = 2, .dy = 1, .weight = 1 },
};

const sierra3_steps = [_]DiffusionStep{
    .{ .dx = 1, .dy = 0, .weight = 5 },
    .{ .dx = 2, .dy = 0, .weight = 3 },
    .{ .dx = -2, .dy = 1, .weight = 2 },
    .{ .dx = -1, .dy = 1, .weight = 4 },
    .{ .dx = 0, .dy = 1, .weight = 5 },
    .{ .dx = 1, .dy = 1, .weight = 4 },
    .{ .dx = 2, .dy = 1, .weight = 2 },
    .{ .dx = -1, .dy = 2, .weight = 2 },
    .{ .dx = 0, .dy = 2, .weight = 3 },
    .{ .dx = 1, .dy = 2, .weight = 2 },
};

const stucki_steps = [_]DiffusionStep{
    .{ .dx = 1, .dy = 0, .weight = 8 },
    .{ .dx = 2, .dy = 0, .weight = 4 },
    .{ .dx = -2, .dy = 1, .weight = 2 },
    .{ .dx = -1, .dy = 1, .weight = 4 },
    .{ .dx = 0, .dy = 1, .weight = 8 },
    .{ .dx = 1, .dy = 1, .weight = 4 },
    .{ .dx = 2, .dy = 1, .weight = 2 },
    .{ .dx = -2, .dy = 2, .weight = 1 },
    .{ .dx = -1, .dy = 2, .weight = 2 },
    .{ .dx = 0, .dy = 2, .weight = 4 },
    .{ .dx = 1, .dy = 2, .weight = 2 },
    .{ .dx = 2, .dy = 2, .weight = 1 },
};

const burkes_steps = [_]DiffusionStep{
    .{ .dx = 1, .dy = 0, .weight = 8 },
    .{ .dx = 2, .dy = 0, .weight = 4 },
    .{ .dx = -2, .dy = 1, .weight = 2 },
    .{ .dx = -1, .dy = 1, .weight = 4 },
    .{ .dx = 0, .dy = 1, .weight = 8 },
    .{ .dx = 1, .dy = 1, .weight = 4 },
    .{ .dx = 2, .dy = 1, .weight = 2 },
};

pub fn divisor(kernel: Kernel) u8 {
    return switch (kernel) {
        .atkinson => 8,
        .sierra2 => 16,
        .sierra3, .burkes => 32,
        .stucki => 42,
    };
}

pub fn depth(kernel: Kernel) usize {
    return switch (kernel) {
        .atkinson, .sierra3, .stucki => 3,
        .sierra2, .burkes => 2,
    };
}

pub fn steps(kernel: Kernel) []const DiffusionStep {
    return switch (kernel) {
        .atkinson => atkinson_steps[0..],
        .sierra2 => sierra2_steps[0..],
        .sierra3 => sierra3_steps[0..],
        .stucki => stucki_steps[0..],
        .burkes => burkes_steps[0..],
    };
}
