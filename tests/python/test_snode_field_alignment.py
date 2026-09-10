"""Regression tests for field alignment in the gfx (SPIR-V) struct compiler.

Children of the root are laid out by ascending size. If a field is placed at an
offset that is not a multiple of its primitive size, `at_buffer` in
spirv_codegen.cpp truncates the shift-based element index and the field is read
and written one slot too low, silently aliasing the last element(s) of the field
placed before it.
"""

import taichi as ti
from tests import test_utils


@test_utils.test(require=ti.extension.data64)
def test_f64_field_does_not_alias_preceding_field():
    # Sizes: three 4-byte scalars (12 bytes), then u32[n] (4n bytes), then
    # f64[n]. With n even, the f64 field starts 4 bytes past an 8-byte boundary.
    n = 1024
    s0 = ti.field(ti.u32, shape=())
    s1 = ti.field(ti.i32, shape=())
    s2 = ti.field(ti.u32, shape=())
    ints = ti.field(ti.u32, shape=n)
    dbl = ti.field(ti.f64, shape=n)

    sentinel = 0x0BADF00D
    s0[None], s1[None], s2[None] = 1, 2, 3
    ints.fill(sentinel)

    @ti.kernel
    def write_dbl():
        for i in dbl:
            dbl[i] = 1.0

    write_dbl()

    # The low 32 bits of f64(1.0) are zero, so a misplaced dbl[0] shows up as a
    # zeroed last element of `ints`.
    assert ints[n - 1] == sentinel
    assert dbl[0] == 1.0
    assert (s0[None], s1[None], s2[None]) == (1, 2, 3)


@test_utils.test()
def test_u32_field_does_not_alias_preceding_field():
    # Same defect without needing f64: three 4-byte scalars (12 bytes), then
    # u8[n] with n = 2 (mod 4), which leaves the following u32 field at an
    # offset that is 2 (mod 4). The u32 field has to be the larger of the two
    # arrays so that the ascending-size ordering places it after the u8 field.
    n = 1026
    s0 = ti.field(ti.u32, shape=())
    s1 = ti.field(ti.i32, shape=())
    s2 = ti.field(ti.u32, shape=())
    bytes_ = ti.field(ti.u8, shape=n)
    ints = ti.field(ti.u32, shape=512)

    bytes_.fill(0xAB)

    @ti.kernel
    def write_ints():
        for i in ints:
            ints[i] = 0x0BADF00D

    write_ints()

    assert bytes_[n - 1] == 0xAB
    assert bytes_[n - 2] == 0xAB
    assert ints[0] == 0x0BADF00D
