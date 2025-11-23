# Snake Game Viewer (Python + C++)

This project provides a visualization of the Snake game in Python (Pygame), which communicates with a C++ version of the game via **shared memory** and **sockets**.

## Project Structure

- `main.py` – the main Python script that runs the game visualization.
- `SnakeGameController.py` – module handling the connection to the C++ game.
- `/snake_game/build/snake` – executable file of the C++ game.
- `setup.sh` – installation script for required Python libraries.

## Requirements

- C++20 compiler (GCC 10+, Clang 10+)  
- Python 3.10+  
- Linux (Ubuntu/Debian recommended)  
- Pygame, Numpy, posix_ipc

## Installation

1. Make the setup script executable:

```bash
chmod +x setup.sh

2. Run the installation script:

setup.sh

## Running the Game

python3 main.py