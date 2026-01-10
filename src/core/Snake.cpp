#include "Snake.hpp"
#include "Definitions.hpp"

#include <algorithm>
#include <cstdint>
#include <deque>
#include <ranges>

namespace SnakeGame
{

Snake::Snake(const Coordinate initialPosition, const uint8_t initialLength)
  : currentDirection_(Direction::RIGHT), shouldGrow_(false)
{
  for (uint8_t i = 0; i < initialLength; ++i)
  {
    body_.emplace_back(initialPosition.first - i, initialPosition.second);
  }
}

void Snake::move(Direction movementDirection)
{
  if ((currentDirection_ == Direction::UP and movementDirection == Direction::DOWN) or
      (currentDirection_ == Direction::DOWN and movementDirection == Direction::UP) or
      (currentDirection_ == Direction::LEFT and movementDirection == Direction::RIGHT) or
      (currentDirection_ == Direction::RIGHT and movementDirection == Direction::LEFT))
  {
    movementDirection = currentDirection_;
  }

  currentDirection_ = movementDirection;

  const auto newHead = getNextPosition(body_.front(), currentDirection_);
  body_.push_front(newHead);

  if (not shouldGrow_)
  {
    body_.pop_back();
  }
  else
  {
    shouldGrow_ = false;
  }
}

void Snake::grow()
{
  shouldGrow_ = true;
}

auto Snake::checkSelfCollision() const -> bool
{
  const auto& head            = body_.front();
  const auto  bodyWithoutHead = body_ | std::views::drop(1);

  return std::ranges::any_of(bodyWithoutHead, [&head](const auto& segment) -> auto { return segment == head; });
}

auto Snake::getBody() const noexcept -> const std::deque<Coordinate>&
{
  return body_;
}

auto Snake::getHead() const noexcept -> Coordinate
{
  return body_.front();
}

auto Snake::getDirection() const noexcept -> Direction
{
  return currentDirection_;
}

constexpr auto Snake::getNextPosition(const Coordinate headPosition, const Direction headingDirection) noexcept
  -> Coordinate
{
  switch (headingDirection)
  {
    case Direction::UP:
      return {headPosition.first, headPosition.second - 1};
    case Direction::DOWN:
      return {headPosition.first, headPosition.second + 1};
    case Direction::LEFT:
      return {headPosition.first - 1, headPosition.second};
    case Direction::RIGHT:
      return {headPosition.first + 1, headPosition.second};
  }
  return headPosition;
}

}  // namespace SnakeGame
