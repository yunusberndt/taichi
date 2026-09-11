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
cmd /c 'call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64 -vcvars_ver=14.34 && python build.py wheel --tag-local v174.granular16bit.align --python native --permissive'
```

## **Linux Wheel (cp312)**
Run this in a Linux environment (native Linux or WSL2 Ubuntu), from repo root. If the system toolchain is too new for this LLVM 15-era codebase, it swaps in a pinned conda Clang **and** libstdc++ — both matter, since `-Werror` is on for Clang/Linux and each new toolchain generation adds diagnostics (clang 19+ breaks imgui, gcc 15 headers break `<ciso646>` via LLVM 15's `Threading.h`). Verified on Fedora 43 / system clang 21 with conda clang 18.1 + gcc 13.4 headers.

```bash
source ~/.cache/ti-build-cache/miniforge/etc/profile.d/conda.sh
conda activate ~/.cache/ti-build-cache/miniforge/envs/3.12

EXTRA=""
V=$(clang++ -dumpversion 2>/dev/null | cut -d. -f1)
if [ "${V:-0}" -ge 16 ]; then
  VER=$(conda search -c conda-forge 'clang_linux-64' 2>/dev/null \
        | awk '$1=="clang_linux-64"{split($2,a,"."); if (a[1]+0<=18) print $2}' | sort -V | tail -1)
  # empty VER must not reach conda install: "clang_linux-64=" installs the latest (21+) and voids the pin
  # libstdcxx-devel: gcc 15 headers #warning on <ciso646>, which LLVM 15 includes -> pin <= 14
  [ -n "$VER" ] && conda install -y -c conda-forge "clang_linux-64=$VER" "clangxx_linux-64=$VER" \
                     'libstdcxx-devel_linux-64=13' \
    || echo "no clang_linux-64 <= 18 on conda-forge; try the 'clangxx' package"
  conda deactivate && conda activate ~/.cache/ti-build-cache/miniforge/envs/3.12
  echo "CC=$CC CXX=$CXX"                                          # must be non-empty
  $CXX -E -x c++ -v /dev/null 2>&1 | grep 'include/c++'           # expect 13.4.0, not 15.x
  EXTRA="-DCMAKE_C_COMPILER=$CC -DCMAKE_CXX_COMPILER=$CXX"
  # Runtime bitcode (runtime_x64.bc / runtime_cuda.bc) is compiled by CLANG_EXECUTABLE, which
  # defaults to CMAKE_CXX_COMPILER. With clang 18 that emits LLVM 18 bitcode, which the linked
  # LLVM 15 cannot read: ti.init(arch=ti.cuda/cpu) then aborts with "Unknown attribute kind".
  # Vulkan is unaffected, so this does NOT show up as a build failure - only at runtime.
  # conda-forge no longer carries clang 15, and taichi's llvm15 bundle ships no clang, so fall
  # back to upstream LLVM's own binaries (~1 GB, cached; no root required).
  # 15.0.6, not 15.0.7: upstream published no x86_64 Linux build for 15.0.7.
  BC15="$HOME/.cache/ti-build-cache/clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04"
  BCCLANG=""
  for c in "$HOME/.cache/ti-build-cache/llvm15/bin/clang" "$BC15/bin/clang" /usr/bin/clang-15; do
    [ -x "$c" ] && BCCLANG="$c" && break
  done
  if [ -z "$BCCLANG" ]; then
    # -f: without it curl "succeeds" on an HTTP error page and leaves a bogus archive behind
    (cd "$HOME/.cache/ti-build-cache" \
      && curl -fL -O https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz \
      && tar xf clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz) \
      || echo "LLVM 15 download/extract FAILED"
    [ -x "$BC15/bin/clang" ] && BCCLANG="$BC15/bin/clang"
  fi
  # -DCLANG_EXECUTABLE in TAICHI_CMAKE_ARGS does NOT work: ti_build overwrites it after parsing,
  # in .github/workflows/scripts/ti_build/compiler.py -> cmake_args["CLANG_EXECUTABLE"] = clang,
  # using the first `clang` on PATH. So shadow `clang` on PATH instead. Use a one-entry directory
  # rather than $BC15/bin, to avoid putting all of LLVM 15's binaries ahead of the conda toolchain.
  if [ -n "$BCCLANG" ]; then
    mkdir -p "$HOME/.cache/ti-build-cache/bc15bin"
    ln -sf "$BCCLANG" "$HOME/.cache/ti-build-cache/bc15bin/clang"
    export PATH="$HOME/.cache/ti-build-cache/bc15bin:$PATH"
    clang --version | head -1                                     # must report 15.x
  else echo "WARNING: no clang <= 15 for bitcode; CUDA/CPU backends will abort at ti.init()"; fi
  # X11 headers for GLFW: xorgproto supplies X11/X.h (libx11 alone only ships Xlib.h).
  # Batch install first; if a name is absent in this channel snapshot, retry one-by-one so a
  # single missing package doesn't abort the rest (names drift, e.g. xorg-xproto).
  XPKGS="xorg-xorgproto xorg-libx11 xorg-libxcursor xorg-libxi xorg-libxinerama xorg-libxrandr"
  conda install -y -c conda-forge $XPKGS \
    || for p in $XPKGS; do conda install -y -c conda-forge "$p" || echo "SKIP $p"; done
  ls "$CONDA_PREFIX"/include/X11/X.h                                # must exist before building
  # glfw3.h includes GL/gl.h unless a GLFW_INCLUDE_* macro is set. Try the packages that ship it;
  # names vary by channel snapshot, so stop as soon as the header appears.
  for p in libgl-devel mesalib libglvnd-devel; do
    [ -f "$CONDA_PREFIX/include/GL/gl.h" ] && break
    conda install -y -c conda-forge "$p" || echo "SKIP $p"
  done
  # Still no GL headers -> tell glfw3.h not to include them (taichi loads GL through external/glad).
  # This must go through -DCMAKE_CXX_FLAGS: exported CXXFLAGS does NOT reach the C++ compile line
  # here (skbuild supplies its own from Python's sysconfig). The TAICHI_CMAKE_ARGS parser truncates
  # values at the first space, so this slot holds exactly one flag - keep it free for this.
  [ -f "$CONDA_PREFIX/include/GL/gl.h" ] || EXTRA="$EXTRA -DCMAKE_CXX_FLAGS=-DGLFW_INCLUDE_NONE"
  # conda sysroot hides clock_gettime in glfw/posix_time.c (-D_GNU_SOURCE also works)
  export CFLAGS="${CFLAGS:+$CFLAGS }-D_POSIX_C_SOURCE=200809L"
  export CPPFLAGS="${CPPFLAGS:+$CPPFLAGS }-D_POSIX_C_SOURCE=200809L"
fi

rm -rf _skbuild                                                   # required if compiler/flags changed
export TAICHI_CMAKE_ARGS="-DTI_WITH_OPENGL=ON -DTI_WITH_VULKAN=ON -DTI_WITH_DX11=OFF -DTI_WITH_DX12=OFF -DTI_BUILD_TESTS=ON -DTI_WITH_C_API=ON $EXTRA"
python3 build.py wheel --tag-local v174.granular16bit.align --python 3.12 --permissive
```

Expected output pattern:

```text
dist/taichi-1.8.0+v174.granular16bit.align-cp312-cp312-manylinux_2_27_x86_64.whl
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
