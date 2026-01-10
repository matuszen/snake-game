#include "Board.hpp"
#include "Definitions.hpp"

#include <algorithm>
#include <cstdint>
#include <deque>
#include <random>

namespace SnakeGame
{

Board::Board(uint8_t width, uint8_t height)
  : width_(width), height_(height), foodPosition_{0, 0}, foodType_(FoodType::APPLE)
{
  placeFood();
}

void Board::placeFood()
{
  foodPosition_ = generateRandomPosition();
  foodType_     = generateRandomFoodType();
}

void Board::placeFood(const std::deque<Coordinate>& snakeBody)
{
  foodPosition_ = generateRandomPosition();
  while (std::ranges::any_of(snakeBody, [this](const auto& segment) -> auto { return segment == foodPosition_; }))
  {
    foodPosition_ = generateRandomPosition();
  }

  foodType_ = generateRandomFoodType();
}

auto Board::isFoodAt(Coordinate pos) const noexcept -> bool
{
  return pos == foodPosition_;
}

auto Board::isWall(Coordinate pos) const noexcept -> bool
{
  return pos.first >= width_ or pos.second >= height_;
}

auto Board::getFoodPosition() const noexcept -> Coordinate
{
  return foodPosition_;
}

auto Board::getFoodType() const noexcept -> FoodType
{
  return foodType_;
}

auto Board::getWidth() const noexcept -> uint8_t
{
  return width_;
}

auto Board::getHeight() const noexcept -> uint8_t
{
  return height_;
}

auto Board::generateRandomPosition() const -> Coordinate
{
  static auto seedDevice = std::random_device{};
  static auto gen        = std::mt19937(seedDevice());

  auto distX = std::uniform_int_distribution<>(0, width_ - 1);
  auto distY = std::uniform_int_distribution<>(0, height_ - 1);

  return {distX(gen), distY(gen)};
}

auto Board::generateRandomFoodType() -> FoodType
{
  static auto seedDevice = std::random_device{};
  static auto gen        = std::mt19937(seedDevice());

  auto dist = std::uniform_int_distribution<>(0, static_cast<int>(FoodType::COUNT) - 1);

  return static_cast<FoodType>(dist(gen));
}

}  // namespace SnakeGame
