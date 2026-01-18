#pragma once

#include "Definitions.hpp"

#include <cstdint>
#include <deque>

namespace SnakeGame
{

/**
 * @brief Represents the snake entity in the game.
 *
 * This class manages the snake's body segments, current direction, and growth state.
 * It provides methods to move the snake, grow it, and check for self-collisions.
 */
class Snake
{
public:
  /**
   * @brief Constructs a new Snake object.
   *
   * @param initialPosition The starting coordinate of the snake's head.
   * @param initialLength The initial length of the snake (default is INITIAL_SNAKE_LENGTH).
   */
  Snake(Coordinate initialPosition, uint8_t initialLength = INITIAL_SNAKE_LENGTH);
  ~Snake() = default;

  Snake(const Snake& other)                   = delete;
  Snake(Snake&& other)                        = delete;
  auto operator=(const Snake& other) -> Snake = delete;
  auto operator=(Snake&& other) -> Snake      = delete;

  /**
   * @brief Moves the snake in the specified direction.
   *
   * Updates the position of the snake's head and body segments based on the
   * given direction. If the snake is growing, the tail is not removed.
   *
   * @param movementDirection The direction in which to move the snake.
   */
  void move(Direction movementDirection);

  /**
   * @brief Signals the snake to grow on the next move.
   *
   * Sets a flag indicating that the snake should not remove its tail segment
   * during the next call to move().
   */
  void grow();

  /**
   * @brief Checks if the snake has collided with itself.
   *
   * @return true If the snake's head is at the same position as any other body segment.
   * @return false Otherwise.
   */
  auto checkSelfCollision() const -> bool;

  /**
   * @brief Gets the collection of coordinates representing the snake's body.
   *
   * @return const std::deque<Coordinate>& A reference to the deque of body coordinates.
   */
  auto getBody() const noexcept -> const std::deque<Coordinate>&;

  /**
   * @brief Gets the current position of the snake's head.
   *
   * @return Coordinate The coordinate of the head.
   */
  auto getHead() const noexcept -> Coordinate;

  /**
   * @brief Gets the current moving direction of the snake.
   *
   * @return Direction The current direction.
   */
  auto getDirection() const noexcept -> Direction;

private:
  std::deque<Coordinate> body_;
  Direction              currentDirection_;
  bool                   shouldGrow_;

  static constexpr auto getNextPosition(Coordinate headPosition, Direction headingDirection) noexcept -> Coordinate;
};

}  // namespace SnakeGame
