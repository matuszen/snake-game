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

namespace SnakeGame
{

constexpr uint8_t DEFAULT_BOARD_WIDTH  = 40;
constexpr uint8_t DEFAULT_BOARD_HEIGHT = 20;

class Game
{
public:
  Game(uint8_t boardWidth = DEFAULT_BOARD_WIDTH, uint8_t boardHeight = DEFAULT_BOARD_HEIGHT);
  ~Game() = default;

  Game(const Game& other)           = delete;
  Game(Game&& other)                = delete;
  auto operator=(const Game& other) = delete;
  auto operator=(Game&& other)      = delete;

  void run();

private:
  std::unique_ptr<Snake>               snake_;
  std::unique_ptr<Board>               board_;
  std::unique_ptr<SharedMemoryManager> shmManager_;
  std::unique_ptr<CommandSocket>       commandSocket_;

  GameState state_;
  uint16_t  score_;
  uint8_t   speed_;

  std::atomic<IpcCommands> pendingCommand_;
  std::mutex               commandMutex_;
  std::optional<Direction> pendingDirection_;

  void initialize();
  void processSocketCommand() noexcept;
  void handleCollision() noexcept;
  void updateSharedMemory() noexcept;

  void handleCommand(IpcCommands command) noexcept;
  void gameStep() noexcept;

  auto getNeuralInputs() const -> NeuralInputs;

  constexpr auto getDelayMs() const noexcept -> uint16_t;
};

}  // namespace SnakeGame

using Game = SnakeGame::Game;
