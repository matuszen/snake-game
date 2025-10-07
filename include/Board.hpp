#pragma once

#include "Types.hpp"

#include <cstdint>

namespace SnakeGame
{

class Board
{
public:
  Board(uint8_t width, uint8_t height);
  ~Board() = default;

  Board(const Board& other)                   = delete;
  Board(Board&& other)                        = delete;
  auto operator=(const Board& other) -> Board = delete;
  auto operator=(Board&& other) -> Board      = delete;

  void               placeFood();
  [[nodiscard]] auto isFoodAt(Coordinate pos) const noexcept -> bool;
  [[nodiscard]] auto isWall(Coordinate pos) const noexcept -> bool;

  [[nodiscard]] auto getFoodPosition() const noexcept -> Coordinate;
  [[nodiscard]] auto getWidth() const noexcept -> uint8_t;
  [[nodiscard]] auto getHeight() const noexcept -> uint8_t;

private:
  uint8_t    width_;
  uint8_t    height_;
  Coordinate foodPosition_;

  [[nodiscard]] auto generateRandomPosition() const -> Coordinate;
};

}  // namespace SnakeGame
