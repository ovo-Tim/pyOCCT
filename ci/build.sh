#!/usr/bin/env bash

declare -a CMAKE_PLATFORM_FLAGS
if [[ ${HOST} =~ .*linux.* ]]; then
  CMAKE_PLATFORM_FLAGS+=(-DCMAKE_TOOLCHAIN_FILE="${RECIPE_DIR}/cross-linux.cmake")
fi

# Fail on error
set -e

rm -Rf build
mkdir build
cd build

cmake -G "Ninja" \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DCMAKE_PREFIX_PATH="$PREFIX" \
  -DCMAKE_SYSTEM_PREFIX_PATH="$PREFIX" \
  "${CMAKE_PLATFORM_FLAGS[@]}" \
  -DCMAKE_BUILD_TYPE="Release" \
  -DPython_ROOT_DIR="$BUILD_PREFIX" \
  -DPYBIND11_PYTHON_VERSION="$PY_VER" \
  ..

ninja -j${CPU_COUNT} install

cd ..
python setup.py install --prefix="$PREFIX"
