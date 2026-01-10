#include "Training.hpp"
#include "Types.hpp"

#include <pybind11/cast.h>
#include <pybind11/detail/common.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>

namespace Py = pybind11;

using GameState  = SnakeGame::GameState;
using NeuralGame = SnakeGame::NeuralGame;
using Direction  = SnakeGame::Direction;

PYBIND11_MODULE(snake_game, m)
{
  m.doc() = "Snake Game Python Bindings";

  // Expose Direction enum
  Py::enum_<Direction>(m, "Direction")
    .value("UP", Direction::UP)
    .value("DOWN", Direction::DOWN)
    .value("LEFT", Direction::LEFT)
    .value("RIGHT", Direction::RIGHT)
    .export_values();

  // Expose GameState enum
  Py::enum_<SnakeGame::GameState>(m, "GameState")
    .value("MENU", GameState::MENU)
    .value("PLAYING", GameState::PLAYING)
    .value("PAUSED", GameState::PAUSED)
    .value("GAME_OVER", GameState::GAME_OVER)
    .value("QUIT", GameState::QUIT)
    .export_values();

  // Expose StepResult struct
  Py::class_<NeuralGame::StepResult>(m, "StepResult")
    .def_readonly("distances", &NeuralGame::StepResult::distances)
    .def_readonly("is_game_over", &NeuralGame::StepResult::isGameOver)
    .def_readonly("fruit_picked_up", &NeuralGame::StepResult::fruitPickedUp);

  // Expose Game class
  Py::class_<NeuralGame>(m, "Game")
    .def(Py::init<uint8_t, uint8_t>(), Py::arg("board_width") = 20, Py::arg("board_height") = 20)
    .def("initialize_game", &NeuralGame::initializeGame, "Initialize/reset the game and return distances vector")
    .def("step_game", &NeuralGame::stepGame, Py::arg("direction"), "Step the game by one frame and return step result");
}
