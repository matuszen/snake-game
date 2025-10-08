#pragma once

#include <array>
#include <cstdint>
#include <utility>

namespace SnakeGame
{

using Coordinate = std::pair<uint8_t, uint8_t>;

constexpr uint16_t MAX_SNAKE_LENGTH = 2048;

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

enum class FoodType : uint8_t
{
  APPLE  = 0,
  CHERRY = 1,
  BANANA = 2,
  GRAPE  = 3,
  ORANGE = 4,
  COUNT  = 5
};

enum class IpcCommands : uint8_t
{
  NONE         = 0,
  START_GAME   = 1,
  MOVE_UP      = 2,
  MOVE_DOWN    = 3,
  MOVE_LEFT    = 4,
  MOVE_RIGHT   = 5,
  RESTART_GAME = 6,
  QUIT_GAME    = 7
};

struct GameSharedData
{
  uint8_t                                  boardWidth;
  uint8_t                                  boardHeight;
  uint16_t                                 score;
  uint8_t                                  speed;
  GameState                                gameState;
  Coordinate                               foodPosition;
  FoodType                                 foodType;
  Coordinate                               snakeHead;
  uint16_t                                 snakeLength;
  std::array<Coordinate, MAX_SNAKE_LENGTH> snakeBody;
};

}  // namespace SnakeGame
