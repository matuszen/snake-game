#pragma once

#include "Types.hpp"

#include <cstdint>
#include <optional>

struct notcurses;
struct ncplane;

namespace SnakeGame
{

class Input
{
public:
  Input();
  ~Input();

  Input(const Input&)                   = delete;
  Input(Input&&)                        = delete;
  auto operator=(Input&&) -> Input      = delete;
  auto operator=(const Input&) -> Input = delete;

  void initialize();
  void cleanup() noexcept;
  void readInput() noexcept;
  void resetInput() noexcept;

  auto getDirection() const noexcept -> std::optional<Direction>;
  auto isPauseRequested() const noexcept -> bool;
  auto isQuitRequested() const noexcept -> bool;
  auto getNotcurses() noexcept -> notcurses*;
  auto getStdPlane() noexcept -> ncplane*;

private:
  bool       initialized_;
  uint32_t   lastKey_;
  notcurses* nc_;
  ncplane*   stdplane_;
};

}  // namespace SnakeGame
