#!/bin/bash

set -e

echo "Please adjust all training parameters in 'py/training/config.py' before proceeding."

if [ ! -d "build" ]; then
    ./build.sh
fi

source .venv/bin/activate
python3 py/training/training.py
