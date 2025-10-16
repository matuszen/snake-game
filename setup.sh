#!/bin/bash

set -e

echo "Snake Game - Setup"

echo "Installing C++ build tools..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential \
    cmake \
    pkg-config \
    git \
    libnotcurses-dev \
    libnotcurses3 \
    notcurses-bin \
    libc6-dev > /dev/null 2>&1

gcc_version=$(gcc -dumpversion | cut -d. -f1)
if [ "$gcc_version" -lt 10 ]; then
    echo "Upgrading GCC to version 10+..."
    sudo apt-get install -y -qq gcc-10 g++-10 > /dev/null 2>&1
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 100 > /dev/null 2>&1
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 100 > /dev/null 2>&1
fi

echo "Installing Python tools..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev > /dev/null 2>&1

echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✓ Setup complete!"
echo ""
echo "Build: mkdir -p build && cd build && cmake .. && make"
echo "Run:   ./build/snake"
echo ""
echo "Python environment activated. To run AI agent:"
echo "  python py/snakeAgent.py"
