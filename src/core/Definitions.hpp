#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string_view>
#include <utility>
#include <vector>

/**
 * @file Definitions.hpp
 * @brief Core type definitions, constants, and enumerations for the Snake Game.
 *
 * This file contains all shared data structures, enums, and constants used across
 * the game engine, including IPC structures and neural network input types.
 */

namespace SnakeGame
{

/// Default name for POSIX shared memory object.
inline constexpr std::string_view DEFAULT_SHM_NAME = "/snake_game_shm";
/// Default path for UNIX domain socket.
inline constexpr std::string_view DEFAULT_SOCKET_PATH = "/tmp/snake_game.sock";

/// Default width of the game board in tiles.
inline constexpr uint8_t DEFAULT_BOARD_WIDTH = 20;
/// Default height of the game board in tiles.
inline constexpr uint8_t DEFAULT_BOARD_HEIGHT = 20;

/// Initial length of the snake at game start.
inline constexpr uint16_t INITIAL_SNAKE_LENGTH = 3;
/// Maximum allowable length of the snake.
inline constexpr uint16_t SNAKE_MAX_LENGTH = 2048;

/// Initial delay in milliseconds between game updates.
inline constexpr uint16_t INITIAL_SPEED_DELAY_MS = 200;
/// Amount to decrease delay per speed level increase.
inline constexpr uint8_t SPEED_DECREASE_PER_LEVEL = 15;

/// Represents a 2D coordinate (x, y) on the board.
using Coordinate = std::pair<uint8_t, uint8_t>;
/// Alias for board dimensions (width, height).
using BoardDimensions = Coordinate;
/// Neural network input vector with 12 float values.
using NeuralInputs = std::array<float, 12>;

/**
 * @brief Enumeration of possible movement directions.
 */
enum class Direction : uint8_t
{
  UP,     ///< Move upward (decrease y).
  DOWN,   ///< Move downward (increase y).
  LEFT,   ///< Move left (decrease x).
  RIGHT,  ///< Move right (increase x).
};

/**
 * @brief Enumeration of game states.
 */
enum class GameState : uint8_t
{
  MENU,       ///< In main menu.
  PLAYING,    ///< Actively playing.
  PAUSED,     ///< Game paused.
  GAME_OVER,  ///< Game has ended.
  QUIT,       ///< Quit signal received.
};

/**
 * @brief Enumeration of food types available in the game.
 */
enum class FoodType : uint8_t
{
  APPLE,   ///< Apple food type.
  CHERRY,  ///< Cherry food type.
  BANANA,  ///< Banana food type.
  GRAPE,   ///< Grape food type.
  ORANGE,  ///< Orange food type.
  COUNT,   ///< Total number of food types.
};

/**
 * @brief Enumeration of inter-process communication commands.
 */
enum class IpcCommands : uint8_t
{
  NONE,               ///< No command.
  START_GAME,         ///< Start a new game.
  MOVE_UP,            ///< Command to move snake up.
  MOVE_DOWN,          ///< Command to move snake down.
  MOVE_LEFT,          ///< Command to move snake left.
  MOVE_RIGHT,         ///< Command to move snake right.
  RESTART_GAME,       ///< Restart the current game.
  QUIT_GAME,          ///< Quit the game.
  CHANGE_BOARD_SIZE,  ///< Change board dimensions.
};

/**
 * @brief Result of a single game step.
 */
struct StepResult
{
  NeuralInputs distances;      ///< Neural inputs (sensor distances).
  bool         isGameOver;     ///< True if game ended this step.
  bool         fruitPickedUp;  ///< True if snake ate food this step.
};

/// Array holding all coordinates of the snake's body.
using SnakeBody = std::array<Coordinate, SNAKE_MAX_LENGTH>;

/**
 * @brief Shared data structure representing the current game state.
 *
 * This structure is used for inter-process communication via shared memory.
 */
struct GameSharedData
{
  uint8_t      boardWidth;      ///< Width of the board.
  uint8_t      boardHeight;     ///< Height of the board.
  uint16_t     score;           ///< Current game score.
  uint8_t      speed;           ///< Current speed level.
  GameState    gameState;       ///< Current state of the game.
  Coordinate   foodPosition;    ///< Position of the food.
  FoodType     foodType;        ///< Type of the food.
  Coordinate   snakeHead;       ///< Position of the snake's head.
  uint16_t     snakeLength;     ///< Length of the snake.
  NeuralInputs neuralVector;    ///< Neural network sensor inputs.
  Direction    snakeDirection;  ///< Current direction of the snake.
  SnakeBody    snakeBody;       ///< All body segment coordinates.
};

/**
 * @brief Shared memory layout with synchronization flags.
 *
 * This structure ensures safe concurrent access to game state between processes.
 */
struct SharedMemoryData
{
  std::atomic<bool>     isWriting{false};  ///< Write lock flag.
  std::atomic<uint32_t> version{0};        ///< Version counter for readers.
  GameSharedData        gameData{};        ///< The actual game state data.
};

/// Size of the shared memory region in bytes.
inline constexpr size_t SHARED_MEMORY_SIZE = sizeof(SharedMemoryData);
/// Delay in milliseconds between shared memory write operations.
inline constexpr int64_t SHARED_MEMORY_WRITE_DELAY = 200;

/// Callback function type for handling IPC commands.
using CommandCallback = std::function<void(IpcCommands, const std::vector<uint8_t>&)>;

}  // namespace SnakeGame
