#include "Board.hpp"
#include "Types.hpp"
#include <cstdint>
#include <random>

namespace SnakeGame
{

Board::Board(uint8_t width, uint8_t height) : width_(width), height_(height), foodPosition_{0, 0}
{
  placeFood();
}

void Board::placeFood()
{
  foodPosition_ = generateRandomPosition();
}

auto Board::isFoodAt(Coordinate pos) const -> bool
{
  return pos == foodPosition_;
}

auto Board::isWall(Coordinate pos) const -> bool
{
  return pos.first >= width_ or pos.second >= height_;
}

auto Board::getFoodPosition() const -> Coordinate
{
  return foodPosition_;
}

auto Board::getWidth() const -> uint8_t
{
  return width_;
}

auto Board::getHeight() const -> uint8_t
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

}  // namespace SnakeGame
