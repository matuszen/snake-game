#!/bin/bash

set -e

check_build_tools() {
    echo "Checking for C++ build tools..."
    command -v gcc >/dev/null 2>&1 || { return 1; }
    command -v g++ >/dev/null 2>&1 || { return 1; }
    command -v cmake >/dev/null 2>&1 || { return 1; }
    echo "All required tools are installed."
    return 0
}

check_python_tools() {
    echo "Checking for Python tools..."
    source .venv/bin/activate
    command -v python3 >/dev/null 2>&1 || { return 1; }
    command -v pip3 >/dev/null 2>&1 || { return 1; }
    command -v flake8 >/dev/null 2>&1 || { return 1; }
    python3 -c "import venv" >/dev/null 2>&1 || { return 1; }
    ls /usr/include/pybind11 >/dev/null 2>&1 || { return 1; }
    echo "All Python tools are installed."
    return 0
}

create_venv() {
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install --upgrade pip -q
    python3 -m pip install -r requirements.txt -q
    python3 -m pip install -e . -q
}

if ! check_build_tools; then
    echo "Installing C++ build tools..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        build-essential \
        cmake \
        pkg-config \
        git \
        libc6-dev > /dev/null 2>&1
fi

if [ ! -d ".venv" ]; then
    create_venv
fi

if ! check_python_tools; then
    echo "Installing Python tools..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        pybind11-dev \
        python3-dev \
        flake8 > /dev/null 2>&1
fi

echo "✓ Setup completed."
exit 0
