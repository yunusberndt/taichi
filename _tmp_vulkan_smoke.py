import taichi as ti
print('version', ti.__version__)
ti.init(arch=ti.vulkan)
print('init ok')
x = ti.field(dtype=ti.f32, shape=8)
@ti.kernel
def fill():
    for i in x:
        x[i] = i * 1.0
fill()
print('kernel ok', x.to_numpy())