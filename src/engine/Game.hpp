#pragma once

#include "Board.hpp"
#include "CommandSocket.hpp"
#include "Definitions.hpp"
#include "SharedMemoryManager.hpp"
#include "Snake.hpp"

#include <atomic>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>

namespace SnakeGame
{

/**
 * @brief Manages the core game logic and state.
 *
 * The Game class coordinates the snake, the board, and user input/output via shared memory
 * and sockets. It handles the game loop, rule enforcement (collisions, scoring), and
 * state updates.
 */
class Game
{
public:
  /**
   * @brief Constructs a new Game object.
   *
   * @param boardSize Dimensions of the game board (default: DEFAULT_BOARD_WIDTH x DEFAULT_BOARD_HEIGHT).
   */
  Game(BoardDimensions boardSize = {DEFAULT_BOARD_WIDTH, DEFAULT_BOARD_HEIGHT});
  ~Game() = default;

  Game(const Game& other)           = delete;
  Game(Game&& other)                = delete;
  auto operator=(const Game& other) = delete;
  auto operator=(Game&& other)      = delete;

  /**
   * @brief Starts the main game loop.
   *
   * This method runs indefinitely until the game is terminated. It handles
   * timing, input processing, and game updates.
   */
  void run();

  /**
   * @brief Advances the game state by one step.
   *
   * Used primarily for step-by-step execution or AI training where the game
   * loop is controlled externally.
   *
   * @param direction The direction for the snake to move this step.
   * @return StepResult The outcome of the step (e.g., collision, fruit eaten).
   */
  auto step(Direction direction) -> StepResult;

  /**
   * @brief Resets the game to its initial state.
   *
   * Re-initializes the snake, board, and score.
   */
  void reset();

  /**
   * @brief Gets the current score.
   *
   * @return uint16_t The current score.
   */
  auto getScore() const -> uint16_t;

  /**
   * @brief Retrieves inputs formatted for the neural network.
   *
   * @return NeuralInputs A structure containing vision/sensor data for AI processing.
   */
  auto getNeuralInputs() const -> NeuralInputs;

private:
  std::unique_ptr<Snake>               snake_;
  std::unique_ptr<Board>               board_;
  std::unique_ptr<SharedMemoryManager> shmManager_;
  std::unique_ptr<CommandSocket>       commandSocket_;
  std::atomic<IpcCommands>             pendingCommand_;
  std::mutex                           commandMutex_;
  std::optional<Direction>             pendingDirection_;
  BoardDimensions                      pendingBoardSize_{0, 0};

  GameState state_;
  uint16_t  score_;
  uint8_t   speed_;
  bool      fruitPickedThisFrame_;

  void initialize();
  void update(Direction direction);
  void processSocketCommand() noexcept;
  void handleCollision() noexcept;
  void handleCommand(IpcCommands command, const std::vector<uint8_t>& payload) noexcept;
  void updateSharedMemory() noexcept;
  auto getDelayMs() const noexcept -> uint16_t;
};

}  // namespace SnakeGame

using Game = SnakeGame::Game;
