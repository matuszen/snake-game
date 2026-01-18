#pragma once

#include "Definitions.hpp"

#include <cstdint>
#include <deque>
#include <random>

namespace SnakeGame
{

/**
 * @brief Manages the game board including dimensions, walls, and food placement.
 *
 * This class is responsible for tracking the board's size, generating random food positions,
 * and checking for collisions with walls.
 */
class Board
{
public:
  /**
   * @brief Constructs a new Board object.
   *
   * @param dimensions Width and height of the board.
   */
  Board(BoardDimensions dimensions);
  ~Board() = default;

  Board(const Board& other)                   = delete;
  Board(Board&& other)                        = delete;
  auto operator=(const Board& other) -> Board = delete;
  auto operator=(Board&& other) -> Board      = delete;

  /**
   * @brief Places food at a random position on the board.
   */
  void placeFood();

  /**
   * @brief Places food at a random position, avoiding the snake's body.
   *
   * @param snakeBody Collection of coordinates occupied by the snake.
   */
  void placeFood(const std::deque<Coordinate>& snakeBody);

  /**
   * @brief Checks if food is at the specified position.
   *
   * @param position The coordinate to check.
   * @return true If food is present at this position.
   * @return false Otherwise.
   */
  auto isFoodAt(Coordinate position) const noexcept -> bool;

  /**
   * @brief Checks if the specified position is a wall (out of bounds).
   *
   * @param position The coordinate to check.
   * @return true If position is outside board boundaries.
   * @return false Otherwise.
   */
  auto isWall(Coordinate position) const noexcept -> bool;

  /**
   * @brief Gets the current food position.
   *
   * @return Coordinate The (x, y) position of the food.
   */
  auto getFoodPosition() const noexcept -> Coordinate;

  /**
   * @brief Gets the current food type.
   *
   * @return FoodType The enum representing the food variant.
   */
  auto getFoodType() const noexcept -> FoodType;

  /**
   * @brief Gets the board width.
   *
   * @return uint8_t The width in tiles.
   */
  auto getWidth() const noexcept -> uint8_t;

  /**
   * @brief Gets the board height.
   *
   * @return uint8_t The height in tiles.
   */
  auto getHeight() const noexcept -> uint8_t;

private:
  uint8_t    width_;
  uint8_t    height_;
  Coordinate foodPosition_;
  FoodType   foodType_;

  auto        generateRandomPosition() const -> Coordinate;
  static auto generateRandomFoodType() -> FoodType;
  static auto getGenerator() -> std::mt19937&;
};

}  // namespace SnakeGame
