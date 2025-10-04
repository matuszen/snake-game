#pragma once

#include "Types.hpp"
#include <cstdint>
#include <deque>

namespace SnakeGame
{

constexpr uint8_t INITIAL_LENGTH = 3;

class Snake
{
public:
  Snake(Coordinate startPos, uint8_t initialLength = INITIAL_LENGTH);

  void               move(Direction dir);
  void               grow();
  [[nodiscard]] auto checkSelfCollision() const -> bool;

  [[nodiscard]] auto getBody() const -> const std::deque<Coordinate>&;
  [[nodiscard]] auto getHead() const -> Coordinate;
  [[nodiscard]] auto getDirection() const -> Direction;

private:
  std::deque<Coordinate> body_;
  Direction              currentDirection_;
  bool                   shouldGrow_;

  [[nodiscard]] static auto getNextPosition(Coordinate pos, Direction dir) -> Coordinate;
};

}  // namespace SnakeGame
