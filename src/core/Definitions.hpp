#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <functional>
#include <string_view>
#include <utility>

namespace SnakeGame
{

inline constexpr uint8_t          DEFAULT_BOARD_WIDTH  = 40;
inline constexpr uint8_t          DEFAULT_BOARD_HEIGHT = 20;
inline constexpr std::string_view DEFAULT_SHM_NAME     = "/snake_game_shm";
inline constexpr std::string_view DEFAULT_SOCKET_PATH  = "/tmp/snake_game.sock";

inline constexpr uint16_t INITIAL_SNAKE_LENGTH   = 3;
inline constexpr uint16_t INITIAL_SPEED_DELAY_MS = 200;

inline constexpr uint16_t SNAKE_MAX_LENGTH          = 2048;
inline constexpr uint8_t  SPEED_DECREASE_PER_LEVEL  = 15;
constexpr int64_t         SHARED_MEMORY_WRITE_DELAY = 200;

using Coordinate   = std::pair<uint8_t, uint8_t>;
using NeuralInputs = std::array<float, 12>;

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

struct StepResult
{
  NeuralInputs distances;
  bool         isGameOver;
  bool         fruitPickedUp;
};

using SnakeBody = std::array<Coordinate, SNAKE_MAX_LENGTH>;

struct GameSharedData
{
  uint8_t      boardWidth;
  uint8_t      boardHeight;
  uint16_t     score;
  uint8_t      speed;
  GameState    gameState;
  Coordinate   foodPosition;
  FoodType     foodType;
  Coordinate   snakeHead;
  uint16_t     snakeLength;
  NeuralInputs neuralVector;
  Direction    snakeDirection;
  SnakeBody    snakeBody;
};

struct SharedMemoryData
{
  std::atomic<bool>     isWriting{false};
  std::atomic<uint32_t> version{0};
  GameSharedData        gameData{};
};

using CommandCallback = std::function<void(IpcCommands)>;

}  // namespace SnakeGame
