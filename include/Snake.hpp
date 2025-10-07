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
  ~Snake() = default;

  Snake(const Snake& other)                   = delete;
  Snake(Snake&& other)                        = delete;
  auto operator=(const Snake& other) -> Snake = delete;
  auto operator=(Snake&& other) -> Snake      = delete;

  void               move(Direction dir);
  void               grow();
  [[nodiscard]] auto checkSelfCollision() const -> bool;

  [[nodiscard]] auto getBody() const noexcept -> const std::deque<Coordinate>&;
  [[nodiscard]] auto getHead() const noexcept -> Coordinate;
  [[nodiscard]] auto getDirection() const noexcept -> Direction;

private:
  std::deque<Coordinate> body_;
  Direction              currentDirection_;
  bool                   shouldGrow_;

  [[nodiscard]] static constexpr auto getNextPosition(Coordinate pos, Direction dir) noexcept
    -> Coordinate;
};

}  // namespace SnakeGame
