#!/bin/sh
# Cross-build a wheel of the frametool extension for 64-bit Arm Linux with scikit-build-core,
# then install it into a folder and run the 27 tests with the target's interpreter under qemu.
# Needs: uv, cmake, gcc-aarch64-linux-gnu, qemu-user, and the aarch64 CPython that uv installs
#        (uv python install cpython-3.14.6-linux-aarch64-gnu).
set -eu
here=$(cd "$(dirname "$0")" && pwd)
tree=$HOME/.local/share/uv/python/cpython-3.14.6-linux-aarch64-gnu
export AARCH64_PYTHON_HOME=$tree
work=$(mktemp -d)
uv venv -q "$work/venv" --python 3.14 && uv pip install -q --python "$work/venv/bin/python" build
src=$work/src
cp -r "$here/../frametool-py" "$src" && rm -rf "$src"/build* "$src"/src/frametool/_crc16*.so

# The build runs on the host. _PYTHON_HOST_PLATFORM sets the platform tag of the wheel, CMAKE_ARGS
# tells CMake about the target.
export _PYTHON_HOST_PLATFORM=linux-aarch64
export CMAKE_ARGS="-DCMAKE_TOOLCHAIN_FILE=$src/cross/aarch64.cmake \
 -DPython_EXECUTABLE=$src/cross/py-aarch64 -DPython_INCLUDE_DIR=$tree/include/python3.14"
"$work/venv/bin/python" -m build --wheel --outdir "$work/dist" "$work/src" 2>&1 | tail -1
cd "$work/dist" && ls -1 *.whl
unzip -l ./*.whl | awk '/\.so$/ {print $4}' | sed 's/^/  /'
unzip -p ./*.whl 'frametool/_crc16*.so' > "$work/ext.so"
file -b "$work/ext.so" | sed 's/, BuildID.*//'
unzip -p ./*.whl '*.dist-info/WHEEL' | grep -E '^(Tag|Root-Is-Purelib)'

# Install the wheel for the target: the files are unpacked, nothing is built or compiled.
uv pip install -q --target "$work/site" --python-version 3.14 \
  --python-platform aarch64-manylinux_2_28 --no-build ./*.whl pytest hypothesis pyserial
export QEMU_LD_PREFIX=/usr/aarch64-linux-gnu PYTHONPATH="$work/site"
cd "$src" && qemu-aarch64 "$tree/bin/python3.14" -c \
  'import platform, frametool._crc16 as m; print(platform.machine(), m.__file__.split("/site/")[1])'
qemu-aarch64 "$tree/bin/python3.14" -m pytest -q -p no:cacheprovider tests 2>&1 | tail -1
rm -rf "$work"
