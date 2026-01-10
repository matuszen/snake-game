#pragma once

#include "Definitions.hpp"

#include <cstdint>
#include <deque>

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

  void placeFood();
  void placeFood(const std::deque<Coordinate>& snakeBody);
  auto isFoodAt(Coordinate pos) const noexcept -> bool;
  auto isWall(Coordinate pos) const noexcept -> bool;

  auto getFoodPosition() const noexcept -> Coordinate;
  auto getFoodType() const noexcept -> FoodType;
  auto getWidth() const noexcept -> uint8_t;
  auto getHeight() const noexcept -> uint8_t;

private:
  uint8_t    width_;
  uint8_t    height_;
  Coordinate foodPosition_;
  FoodType   foodType_;

  auto        generateRandomPosition() const -> Coordinate;
  static auto generateRandomFoodType() -> FoodType;
};

}  // namespace SnakeGame
