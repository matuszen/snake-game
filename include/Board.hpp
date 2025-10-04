#pragma once

#include "Types.hpp"
#include <cstdint>

namespace SnakeGame
{

class Board
{
public:
  Board(uint8_t width, uint8_t height);

  void               placeFood();
  [[nodiscard]] auto isFoodAt(Coordinate pos) const -> bool;
  [[nodiscard]] auto isWall(Coordinate pos) const -> bool;

  [[nodiscard]] auto getFoodPosition() const -> Coordinate;
  [[nodiscard]] auto getWidth() const -> uint8_t;
  [[nodiscard]] auto getHeight() const -> uint8_t;

private:
  uint8_t    width_;
  uint8_t    height_;
  Coordinate foodPosition_;

  [[nodiscard]] auto generateRandomPosition() const -> Coordinate;
};

}  // namespace SnakeGame
