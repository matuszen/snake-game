#pragma once

#include "Types.hpp"
#include <cstdint>
#include <optional>

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
  void cleanup();
  void readInput();

  [[nodiscard]] auto getDirection() const -> std::optional<Direction>;
  [[nodiscard]] auto isPauseRequested() const -> bool;
  [[nodiscard]] auto isQuitRequested() const -> bool;

private:
  bool    initialized_;
  int32_t lastKey_;
};

}  // namespace SnakeGame
