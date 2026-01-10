#include "Definitions.hpp"
#include "Game.hpp"

#include <pybind11/cast.h>
#include <pybind11/detail/common.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>

namespace Py = pybind11;

using Game       = SnakeGame::Game;
using StepResult = SnakeGame::StepResult;
using GameState  = SnakeGame::GameState;
using Direction  = SnakeGame::Direction;

PYBIND11_MODULE(snake_game, m)
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
    .def(Py::init<uint8_t, uint8_t>(), Py::arg("board_width") = 20, Py::arg("board_height") = 20)
    .def(
      "initialize_game",
      [](Game& g) -> StepResult
      {
        g.reset();
        return {.distances = g.getNeuralInputs(), .isGameOver = false, .fruitPickedUp = false};
      },
      "Initialize/reset the game and return distances vector")
    .def("step_game", &Game::step, Py::arg("direction"), "Step the game by one frame and return step result");
}
