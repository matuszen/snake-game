#!/bin/bash

set -e

echo "Snake Game - Training"
echo "Please adjust all training parameters in 'py/training/config.py' before proceeding."


if [ ! -d "build" ]; then
    echo "Creating build directory..."
    mkdir -p build
fi

cd build
cmake ..
make
cd ..
source .venv/bin/activate

echo "Starting training..."
python3 py/training/training.py
