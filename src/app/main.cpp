#include "Game.hpp"

#include <exception>
#include <iostream>

auto main(const int /*argc*/, const char* const /*argv*/[]) -> int
{
  try
  {
    Game{}.run();
  }
  catch (const std::exception& e)
  {
    std::cerr << "Error: " << e.what() << '\n';
    return 1;
  }
  return 0;
}
