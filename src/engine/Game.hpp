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

class Game
{
public:
  Game(BoardDimensions boardSize = {DEFAULT_BOARD_WIDTH, DEFAULT_BOARD_HEIGHT});
  ~Game() = default;

  Game(const Game& other)           = delete;
  Game(Game&& other)                = delete;
  auto operator=(const Game& other) = delete;
  auto operator=(Game&& other)      = delete;

  void run();
  auto step(Direction direction) -> StepResult;
  void reset();
  auto getScore() const -> uint16_t;
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
