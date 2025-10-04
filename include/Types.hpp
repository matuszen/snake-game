#pragma once

#include <cstdint>
#include <utility>

namespace SnakeGame
{

using Coordinate = std::pair<uint8_t, uint8_t>;

enum class Direction : uint8_t
{
  UP,
  DOWN,
  LEFT,
  RIGHT
};

enum class GameState : uint8_t
{
  MENU,
  PLAYING,
  PAUSED,
  GAME_OVER,
  QUIT
};

}  // namespace SnakeGame
