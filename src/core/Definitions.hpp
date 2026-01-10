#pragma once

#include <array>
#include <cstdint>
#include <utility>

namespace SnakeGame
{

using Coordinate   = std::pair<uint8_t, uint8_t>;
using NeuralInputs = std::array<float, 12>;

constexpr uint16_t MAX_SNAKE_LENGTH = 2048;

enum class Direction : uint8_t
{
  UP,
  DOWN,
  LEFT,
  RIGHT,
};

enum class GameState : uint8_t
{
  MENU,
  PLAYING,
  PAUSED,
  GAME_OVER,
  QUIT,
};

enum class FoodType : uint8_t
{
  APPLE,
  CHERRY,
  BANANA,
  GRAPE,
  ORANGE,
  COUNT,
};

enum class IpcCommands : uint8_t
{
  NONE,
  START_GAME,
  MOVE_UP,
  MOVE_DOWN,
  MOVE_LEFT,
  MOVE_RIGHT,
  RESTART_GAME,
  QUIT_GAME,
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
  NeuralInputs                             neuralVector;
  Direction                                snakeDirection;
  std::array<Coordinate, MAX_SNAKE_LENGTH> snakeBody;
};

}  // namespace SnakeGame
