#include "Input.hpp"
#include "Types.hpp"
#include <cstdint>
#include <ncurses.h>
#include <optional>

namespace SnakeGame
{

namespace
{
constexpr int32_t ESC_KEY = 27;
}  // namespace

Input::Input() : initialized_(false), lastKey_(ERR)
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
    initscr();
    cbreak();
    noecho();
    curs_set(0);
    keypad(stdscr, TRUE);
    nodelay(stdscr, TRUE);
    initialized_ = true;
  }
}

void Input::cleanup()
{
  if (initialized_)
  {
    endwin();
    initialized_ = false;
  }
}

void Input::readInput()
{
  lastKey_ = getch();
}

auto Input::getDirection() const -> std::optional<Direction>
{
  switch (lastKey_)
  {
    case KEY_UP:
    case 'w':
    case 'W':
      return Direction::UP;
    case KEY_DOWN:
    case 's':
    case 'S':
      return Direction::DOWN;
    case KEY_LEFT:
    case 'a':
    case 'A':
      return Direction::LEFT;
    case KEY_RIGHT:
    case 'd':
    case 'D':
      return Direction::RIGHT;
    default:
      return std::nullopt;
  }
}

auto Input::isPauseRequested() const -> bool
{
  return lastKey_ == 'p' or lastKey_ == 'P' or lastKey_ == ' ';
}

auto Input::isQuitRequested() const -> bool
{
  return lastKey_ == 'q' or lastKey_ == 'Q' or lastKey_ == ESC_KEY;
}

}  // namespace SnakeGame
