#pragma once

#include "Board.hpp"
#include "Input.hpp"
#include "Snake.hpp"
#include "Types.hpp"
#include <cstdint>
#include <memory>

namespace SnakeGame
{

constexpr uint8_t DEFAULT_DOARD_WIDTH  = 40;
constexpr uint8_t DEFAULT_DOARD_HEIGHT = 20;

class Game
{
public:
  Game(uint8_t boardWidth = DEFAULT_DOARD_WIDTH, uint8_t boardHeight = DEFAULT_DOARD_HEIGHT);

  void run();

private:
  std::unique_ptr<Snake> snake_;
  std::unique_ptr<Board> board_;
  std::unique_ptr<Input> input_;

  GameState state_;
  uint16_t  score_;
  uint8_t   speed_;

  void initialize();
  void processInput();
  void update();
  void render();
  void handleCollision();
  void showMenu();
  void showGameOver();

  [[nodiscard]] auto getDelayMs() const -> uint16_t;
};

}  // namespace SnakeGame
