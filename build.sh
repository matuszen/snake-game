#!/bin/bash

set -e

mkdir -p build
cd build
cmake ..
make
make install
cd ..

echo "✓ Build completed."
exit 0
