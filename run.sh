#!/bin/bash

set -e

echo "Snake Game - Run"

if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

if [ ! -d "build" ]; then
    mkdir -p build
    cd build
    cmake ..
    make
    cd ..
fi

source .venv/bin/activate

python3 py/interface/main.py
