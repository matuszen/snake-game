# 🐍 Snake Game

A Snake game implementation in C++.

## Gameplay

- Snake grows with each food eaten (+10 points)
- Speed increases every 50 points (max 10 levels)
- Collision detection with walls and self
- Colorful snake - Bright green head (◉), darker green body (○)
- Variety of food - 5 different types with unique colors and symbols:
  - `●` Red Apple
  - `◆` Pink Cherry
  - `◉` Yellow Banana
  - `■` Purple Grape
  - `★` Orange Orange

## Controls

- **Arrow keys** or **WASD** - Move snake
- **P** or **Space** - Pause/Resume
- **Q** - Quit game

## Requirements

- C++20 compiler (GCC 10+, Clang 10+)
- CMake 3.20+
- [notcurses](https://github.com/dankamongmen/notcurses/) 3.0.7+

## Build & Run

```bash
mkdir build && cd build
cmake ..
make
./snake
```
