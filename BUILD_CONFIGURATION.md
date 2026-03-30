# Taichi Build Configuration

## **Environment Setup:**
```powershell
# Set LLVM_DIR to official Taichi LLVM (CRITICAL)
$env:LLVM_DIR = "$env:LOCALAPPDATA\ti-build-cache\llvm15"

# Set CMake arguments to match official Windows release build
$env:TAICHI_CMAKE_ARGS = "-DTI_WITH_OPENGL=ON -DTI_WITH_VULKAN=ON -DTI_WITH_DX11=ON -DTI_WITH_DX12=ON -DTI_BUILD_TESTS=ON -DTI_WITH_C_API=ON"
```

## **Build Command:**
```powershell
# Use older linker version (14.34) to match official Taichi
cmd /c 'call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64 -vcvars_ver=14.34 && python build.py wheel --tag-local v174.granular16bit --python native --permissive'
```

## **Linux Wheel (cp312)**
Run this in a Linux environment (native Linux or WSL2 Ubuntu), from repo root:

```bash
export TAICHI_CMAKE_ARGS="-DTI_WITH_OPENGL=ON -DTI_WITH_VULKAN=ON -DTI_WITH_DX11=OFF -DTI_WITH_DX12=OFF -DTI_BUILD_TESTS=ON -DTI_WITH_C_API=ON"
python3 build.py wheel --tag-local v174.granular16bit --python 3.12 --permissive
```

Expected output pattern:

```text
dist/taichi-1.8.0+v174.granular16bit-cp312-cp312-manylinux_2_27_x86_64.whl
```

### Linux (Conda Clang / headless HPC)

When building with **conda-forge Clang** and the bundled **GLFW** sources, `external/glfw/src/posix_time.c` may fail with undeclared `clock_gettime`, `CLOCK_REALTIME`, or `CLOCK_MONOTONIC` (strict C99 + sysroot headers do not expose those without an explicit POSIX feature macro). Set this **before** `python build.py ...` (and after `conda activate`):

```bash
export CFLAGS="${CFLAGS:+$CFLAGS }-D_POSIX_C_SOURCE=200809L"
export CPPFLAGS="${CPPFLAGS:+$CPPFLAGS }-D_POSIX_C_SOURCE=200809L"
```

`-D_GNU_SOURCE` is a broader alternative if you already rely on it for other targets.

If you change compiler flags or conda packages, remove the stale CMake tree and rebuild:

```bash
rm -rf _skbuild
```

For GUI-related backends on a node **without** system X11/GL development packages, install the matching **xorg-** headers/libs from **conda-forge** (e.g. `xorg-libx11`, `xorg-libxcursor`, extensions as CMake reports missing includes) and keep **one** toolchain coherent—avoid mixing `CPATH`/`CMAKE_PREFIX_PATH` to conda with host `/usr/include` in the same build.

## **Required Visual Studio Components:**
- **Desktop development with C++** workload
- **MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest) - 14.34** (non-Spectre-mitigated)
- **C++ Clang Compiler for Windows**
- **C++ 2022 Redistributable MSM**
- **MS Build support for LLVM (clang-cl) toolset**

## **Critical CMake Flags (matching official release):**
- **`TI_WITH_OPENGL=ON`** - OpenGL backend
- **`TI_WITH_VULKAN=ON`** - Vulkan backend
- **`TI_WITH_DX11=ON`** - DirectX 11 backend
- **`TI_WITH_DX12=ON`** - DirectX 12 backend
- **`TI_BUILD_TESTS=ON`** - Build test suite
- **`TI_WITH_C_API=ON`** - C API support

## **Excluded Flags (not in official release):**
- **`TI_WITH_GGUI=ON`** - Adds IMM32.dll dependency (not in official)
- **`TI_WITH_LTO=ON`** - Link Time Code Generation (not in official)
- **`TI_GENERATE_PDB=ON`** - Debug symbols (not in official)

## **Build System Configuration:**
- **Visual Studio 2022 Build Tools** with MSVC 14.34.31948.0
- **Python 3.12.4** with native build
- **Official Taichi LLVM** from `%LOCALAPPDATA%\ti-build-cache\llvm15`
- **MSBuild** as the build system

## **Key Dependencies:**
- **`d3d11.dll`** - DirectX 11 runtime
- **`D3DCOMPILER_47.dll`** - DirectX shader compiler
- **`msvcp140.dll`** - MSVC C++ runtime
- **`vcruntime140.dll`** - MSVC runtime
- **`vcruntime140_1.dll`** - MSVC runtime extension
