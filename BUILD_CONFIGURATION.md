# Taichi Build Configuration

## **Windows Wheel (PowerShell)**
Run from repo root in PowerShell.

### **Environment Setup:**
```powershell
# Set LLVM_DIR to official Taichi LLVM (CRITICAL)
$env:LLVM_DIR = "$env:LOCALAPPDATA\ti-build-cache\llvm15"

# Set CMake arguments to match official Windows release build
$env:TAICHI_CMAKE_ARGS = "-DTI_WITH_OPENGL=ON -DTI_WITH_VULKAN=ON -DTI_WITH_DX11=ON -DTI_WITH_DX12=ON -DTI_BUILD_TESTS=ON -DTI_WITH_C_API=ON"
```

### **Build Command:**
```powershell
# Use older linker version (14.34) to match official Taichi
cmd /c 'call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64 -vcvars_ver=14.34 && python build.py wheel --tag-local v174.granular16bit --python native --permissive'
```

## **Linux Wheel (cp312)**
Run this in a Linux environment (native Linux or WSL2 Ubuntu), from repo root. Swaps in a pinned conda Clang if the system one is too new (`-Werror` is on for Clang/Linux: clang 16+ breaks `core.h`, 19+ breaks imgui).

```bash
source ~/.cache/ti-build-cache/miniforge/etc/profile.d/conda.sh
conda activate ~/.cache/ti-build-cache/miniforge/envs/3.12

EXTRA=""
V=$(clang++ -dumpversion 2>/dev/null | cut -d. -f1)
if [ "${V:-0}" -ge 16 ]; then
  VER=$(conda search -c conda-forge 'clang_linux-64' 2>/dev/null \
        | awk '$1=="clang_linux-64"{split($2,a,"."); if (a[1]+0<=18) print $2}' | sort -V | tail -1)
  # empty VER must not reach conda install: "clang_linux-64=" installs the latest (21+) and voids the pin
  [ -n "$VER" ] && conda install -y -c conda-forge "clang_linux-64=$VER" "clangxx_linux-64=$VER" \
    || echo "no clang_linux-64 <= 18; try the 'clangxx' package, or drop -Werror in the fork:
             sed -i 's/ -Werror //' cmake/TaichiCXXFlags.cmake"
  conda deactivate && conda activate ~/.cache/ti-build-cache/miniforge/envs/3.12
  echo "CC=$CC CXX=$CXX"                                          # must be non-empty
  EXTRA="-DCMAKE_C_COMPILER=$CC -DCMAKE_CXX_COMPILER=$CXX"
  # clang 16-18 still warn on core.h; values can't contain spaces, so only one flag fits
  [ "$("$CXX" -dumpversion | cut -d. -f1)" -ge 16 ] && EXTRA="$EXTRA -DCMAKE_CXX_FLAGS=-Wno-deprecated-literal-operator"
  # GLFW X11 headers, if the node has no system ones (add extensions as CMake reports them)
  conda install -y -c conda-forge xorg-libx11 xorg-libxcursor xorg-libxi xorg-libxinerama xorg-libxrandr
  # conda sysroot hides clock_gettime in glfw/posix_time.c (-D_GNU_SOURCE also works)
  export CFLAGS="${CFLAGS:+$CFLAGS }-D_POSIX_C_SOURCE=200809L"
  export CPPFLAGS="${CPPFLAGS:+$CPPFLAGS }-D_POSIX_C_SOURCE=200809L"
fi

rm -rf _skbuild                                                   # required if compiler/flags changed
export TAICHI_CMAKE_ARGS="-DTI_WITH_OPENGL=ON -DTI_WITH_VULKAN=ON -DTI_WITH_DX11=OFF -DTI_WITH_DX12=OFF -DTI_BUILD_TESTS=ON -DTI_WITH_C_API=ON $EXTRA"
python3 build.py wheel --tag-local v174.granular16bit --python 3.12 --permissive
```

Expected output pattern:

```text
dist/taichi-1.8.0+v174.granular16bit-cp312-cp312-manylinux_2_27_x86_64.whl
```

### Linux (Conda Clang / headless HPC)

Keep **one** toolchain coherent: don't point `CPATH`/`CMAKE_PREFIX_PATH` at conda while also pulling host `/usr/include` into the same build.

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
