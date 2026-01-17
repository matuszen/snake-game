#!/bin/bash

set -e

if [ ! -d ".venv" ]; then
    ./setup.sh
fi

if [ ! -d "build" ]; then
    ./build.sh
fi

source .venv/bin/activate
python3 py/interface/main.py
