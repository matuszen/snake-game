#include "Game.hpp"

#include <exception>
#include <iostream>

auto main() -> int
{
  try
  {
    auto game = SnakeGame::Game{};
    game.run();
  }
  catch (const std::exception& e)
  {
    std::cerr << "Error: " << e.what() << '\n';
    return 1;
  }

  return 0;
}
