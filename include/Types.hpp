#pragma once

#include <cstdint>
#include <utility>

namespace SnakeGame
{

using Coordinate = std::pair<uint8_t, uint8_t>;

enum class Direction : uint8_t
{
  UP    = 0,
  DOWN  = 1,
  LEFT  = 2,
  RIGHT = 3
};

enum class GameState : uint8_t
{
  MENU      = 0,
  PLAYING   = 1,
  PAUSED    = 2,
  GAME_OVER = 3,
  QUIT      = 4
};

}  // namespace SnakeGame
