#pragma once

#include "Board.hpp"
#include "Input.hpp"
#include "Snake.hpp"
#include "Types.hpp"

#include <array>
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

  struct StepResult
  {
    std::array<float, 12> distances;
    bool                  isGameOver;
    bool                  fruitPickedUp;
  };

  [[nodiscard]] auto initializeGame() -> StepResult;
  [[nodiscard]] auto stepGame(Direction direction) -> StepResult;

  void update(Direction direction);

private:
  std::unique_ptr<Snake>                    snake_;
  std::unique_ptr<Board>                    board_;
  std::unique_ptr<Input>                    input_;

  GameState state_;
  uint16_t  score_;
  uint8_t   speed_;
  bool      fruitPickedThisFrame_;

  void initialize();

  void handleCollision() noexcept;

  [[nodiscard]] auto getNeuralInputs() const -> std::array<float, 12>;
  [[nodiscard]] constexpr auto getDelayMs() const noexcept -> uint16_t;
};

}  // namespace SnakeGame

using Game = SnakeGame::Game;
