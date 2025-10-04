# Snake Game

A classic Snake game implementation in C++20 for terminal/console.

## Description

Navigate a growing snake around the board to eat food while avoiding walls and your own tail. 
The snake grows longer with each piece of food eaten, and the game speeds up as your score increases.

## Controls

- **Arrow keys** or **WASD** - Move the snake
- **P** or **Space** - Pause/Resume
- **Q** or **ESC** - Quit game

## Rules

- Eat food (`*`) to grow your snake and increase your score
- Each food eaten adds 10 points to your score
- Avoid hitting walls (`#`) or your own body
- The game speed increases every 50 points
- Game ends when you collide with a wall or yourself

## Building

### Requirements
- C++20 compatible compiler (GCC 10+, Clang 10+)
- CMake 3.20 or newer
- ncurses library

### Install dependencies (Ubuntu/Debian)
```bash
sudo apt-get install build-essential cmake libncurses-dev
```

### Compile
```bash
mkdir build && cd build
cmake ..
make
```

### Run
```bash
./snake
```
