#include "Definitions.hpp"
#include "Game.hpp"

#include <pybind11/cast.h>
#include <pybind11/detail/common.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <memory>

namespace Py = pybind11;

using Game            = SnakeGame::Game;
using StepResult      = SnakeGame::StepResult;
using GameState       = SnakeGame::GameState;
using Direction       = SnakeGame::Direction;
using BoardDimensions = SnakeGame::BoardDimensions;

PYBIND11_MODULE(snake_lib, m)
{
  m.doc() = "Snake Game Python Bindings";

  Py::enum_<Direction>(m, "Direction")
    .value("UP", Direction::UP)
    .value("DOWN", Direction::DOWN)
    .value("LEFT", Direction::LEFT)
    .value("RIGHT", Direction::RIGHT)
    .export_values();

  Py::enum_<GameState>(m, "GameState")
    .value("MENU", GameState::MENU)
    .value("PLAYING", GameState::PLAYING)
    .value("PAUSED", GameState::PAUSED)
    .value("GAME_OVER", GameState::GAME_OVER)
    .value("QUIT", GameState::QUIT)
    .export_values();

  Py::class_<StepResult>(m, "StepResult")
    .def_readonly("distances", &StepResult::distances)
    .def_readonly("is_game_over", &StepResult::isGameOver)
    .def_readonly("fruit_picked_up", &StepResult::fruitPickedUp);

  Py::class_<Game>(m, "Game")
    .def(Py::init([](const uint8_t width, const uint8_t height) -> auto
                  { return std::make_unique<Game>(BoardDimensions{width, height}); }),
         Py::arg("width") = 20, Py::arg("height") = 20)
    .def(
      "initialize_game",
      [](Game& g) -> StepResult
      {
        g.reset();
        return {
          .distances     = g.getNeuralInputs(),
          .isGameOver    = false,
          .fruitPickedUp = false,
        };
      },
      "Initialize/reset the game and return distances vector")
    .def("step_game", &Game::step, Py::arg("direction"), "Step the game by one frame and return step result");
}
