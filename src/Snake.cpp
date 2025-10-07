#include "Snake.hpp"
#include "Types.hpp"

#include <algorithm>
#include <cstdint>
#include <deque>
#include <ranges>

namespace SnakeGame
{

Snake::Snake(Coordinate startPos, uint8_t initialLength)
  : currentDirection_(Direction::RIGHT), shouldGrow_(false)
{
  for (uint8_t i = 0; i < initialLength; ++i)
  {
    body_.emplace_back(startPos.first - i, startPos.second);
  }
}

void Snake::move(Direction dir)
{
  if ((currentDirection_ == Direction::UP and dir == Direction::DOWN) or
      (currentDirection_ == Direction::DOWN and dir == Direction::UP) or
      (currentDirection_ == Direction::LEFT and dir == Direction::RIGHT) or
      (currentDirection_ == Direction::RIGHT and dir == Direction::LEFT))
  {
    dir = currentDirection_;
  }

  currentDirection_ = dir;

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

  return std::ranges::any_of(bodyWithoutHead,
                             [&head](const auto& segment) { return segment == head; });
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

constexpr auto Snake::getNextPosition(Coordinate pos, Direction dir) noexcept -> Coordinate
{
  switch (dir)
  {
    case Direction::UP:
      return {pos.first, pos.second - 1};
    case Direction::DOWN:
      return {pos.first, pos.second + 1};
    case Direction::LEFT:
      return {pos.first - 1, pos.second};
    case Direction::RIGHT:
      return {pos.first + 1, pos.second};
  }
  return pos;
}

}  // namespace SnakeGame
