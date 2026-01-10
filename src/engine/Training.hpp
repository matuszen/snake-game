#pragma once

#include "Board.hpp"
#include "Definitions.hpp"
#include "Game.hpp"
#include "Snake.hpp"

#include <cstdint>
#include <memory>

namespace SnakeGame
{

class NeuralGame
{
public:
  NeuralGame(uint8_t boardWidth = DEFAULT_BOARD_WIDTH, uint8_t boardHeight = DEFAULT_BOARD_HEIGHT);
  ~NeuralGame() = default;

  NeuralGame(const NeuralGame& other)     = delete;
  NeuralGame(NeuralGame&& other)          = delete;
  auto operator=(const NeuralGame& other) = delete;
  auto operator=(NeuralGame&& other)      = delete;

  struct StepResult
  {
    NeuralInputs distances;
    bool         isGameOver;
    bool         fruitPickedUp;
  };

  auto initializeGame() -> StepResult;
  auto stepGame(Direction direction) -> StepResult;

  void update(Direction direction);

private:
  std::unique_ptr<Snake> snake_;
  std::unique_ptr<Board> board_;

  GameState state_;
  uint16_t  score_;
  uint8_t   speed_;
  bool      fruitPickedThisFrame_;

  void initialize();

  void handleCollision() noexcept;

  auto           getNeuralInputs() const -> NeuralInputs;
  constexpr auto getDelayMs() const noexcept -> uint16_t;
};

}  // namespace SnakeGame

using Game = SnakeGame::Game;
