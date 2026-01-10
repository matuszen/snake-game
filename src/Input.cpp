#include "Input.hpp"
#include "Types.hpp"

#include <notcurses/nckeys.h>
#include <notcurses/notcurses.h>

#include <optional>

namespace SnakeGame
{

Input::Input() : initialized_(false), lastKey_(0), nc_(nullptr), stdplane_(nullptr)
{
}

Input::~Input()
{
  cleanup();
}

void Input::initialize()
{
  if (not initialized_)
  {
    auto opts = notcurses_options{};
    auto ni   = ncinput{};

    opts.flags = NCOPTION_SUPPRESS_BANNERS;

    nc_ = notcurses_init(&opts, nullptr);
    if (nc_ == nullptr)
    {
      return;
    }
    stdplane_ = notcurses_stdplane(nc_);
    notcurses_get_nblock(nc_, &ni);

    initialized_ = true;
  }
}

void Input::cleanup() noexcept
{
  if (initialized_)
  {
    notcurses_stop(nc_);
    nc_          = nullptr;
    stdplane_    = nullptr;
    initialized_ = false;
  }
}

void Input::readInput() noexcept
{
  if (nc_ == nullptr)
  {
    return;
  }

  constexpr unsigned maxInputLimit = 0xFFFFFFFF;

  auto       ni  = ncinput{};
  const auto key = notcurses_get_nblock(nc_, &ni);

  if (key != maxInputLimit)
  {
    lastKey_ = key;
  }
}

void Input::resetInput() noexcept
{
  lastKey_ = 0;
}

auto Input::getDirection() const noexcept -> std::optional<Direction>
{
  switch (lastKey_)
  {
    case NCKEY_UP:
    case 'w':
    case 'W':
      return Direction::UP;
    case NCKEY_DOWN:
    case 's':
    case 'S':
      return Direction::DOWN;
    case NCKEY_LEFT:
    case 'a':
    case 'A':
      return Direction::LEFT;
    case NCKEY_RIGHT:
    case 'd':
    case 'D':
      return Direction::RIGHT;
    default:
      return std::nullopt;
  }
}

auto Input::isPauseRequested() const noexcept -> bool
{
  return lastKey_ == 'p' or lastKey_ == 'P' or lastKey_ == ' ';
}

auto Input::isQuitRequested() const noexcept -> bool
{
  return lastKey_ == 'q' or lastKey_ == 'Q';
}

auto Input::getNotcurses() noexcept -> notcurses*
{
  return nc_;
}

auto Input::getStdPlane() noexcept -> ncplane*
{
  return stdplane_;
}

}  // namespace SnakeGame
