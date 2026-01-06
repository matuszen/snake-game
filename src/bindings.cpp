#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "Training.hpp"
#include "Types.hpp"

namespace py = pybind11;
using namespace SnakeGame;

PYBIND11_MODULE(snake_game, m) {
  m.doc() = "Snake Game Python Bindings";

  // Expose Direction enum
  py::enum_<Direction>(m, "Direction")
    .value("UP", Direction::UP)
    .value("DOWN", Direction::DOWN)
    .value("LEFT", Direction::LEFT)
    .value("RIGHT", Direction::RIGHT)
    .export_values();

  // Expose GameState enum
  py::enum_<GameState>(m, "GameState")
    .value("MENU", GameState::MENU)
    .value("PLAYING", GameState::PLAYING)
    .value("PAUSED", GameState::PAUSED)
    .value("GAME_OVER", GameState::GAME_OVER)
    .value("QUIT", GameState::QUIT)
    .export_values();

  // Expose StepResult struct
  py::class_<Game::StepResult>(m, "StepResult")
    .def_readonly("distances", &Game::StepResult::distances)
    .def_readonly("is_game_over", &Game::StepResult::isGameOver)
    .def_readonly("fruit_picked_up", &Game::StepResult::fruitPickedUp);

  // Expose Game class
  py::class_<Game>(m, "Game")
    .def(py::init<uint8_t, uint8_t>(), py::arg("board_width") = 20, py::arg("board_height") = 20)
    .def("initialize_game", &Game::initializeGame, "Initialize/reset the game and return distances vector")
    .def("step_game", &Game::stepGame, py::arg("direction"), "Step the game by one frame and return step result");
}
