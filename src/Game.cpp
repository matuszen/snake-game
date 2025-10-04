#include "Game.hpp"
#include "Board.hpp"
#include "Input.hpp"
#include "Snake.hpp"
#include "Types.hpp"
#include <chrono>
#include <cstdint>
#include <memory>
#include <ncurses.h>
#include <thread>

namespace SnakeGame
{

namespace
{
constexpr uint16_t PAUSE_DELAY_MS           = 100;
constexpr uint16_t INITIAL_SPEED_DELAY_MS   = 200;
constexpr uint8_t  SCORE_PER_FOOD           = 10;
constexpr uint8_t  SPEED_INCREASE_INTERVAL  = 50;
constexpr uint8_t  MAX_SPEED                = 10;
constexpr uint8_t  SPEED_DECREASE_PER_LEVEL = 15;
constexpr int32_t  ESC_KEY                  = 27;
}  // namespace

Game::Game(uint8_t boardWidth, uint8_t boardHeight)
  : snake_(nullptr), board_(std::make_unique<Board>(boardWidth, boardHeight)),
    input_(std::make_unique<Input>()), state_(GameState::MENU), score_(0), speed_(1)
{
}

void Game::run()
{
  input_->initialize();

  while (state_ != GameState::QUIT)
  {
    switch (state_)
    {
      case GameState::MENU:
        showMenu();
        break;
      case GameState::PLAYING:
        input_->readInput();
        if (input_->isQuitRequested())
        {
          state_ = GameState::QUIT;
          break;
        }
        processInput();
        update();
        render();
        std::this_thread::sleep_for(std::chrono::milliseconds(getDelayMs()));
        break;
      case GameState::PAUSED:
        input_->readInput();
        if (input_->isQuitRequested())
        {
          state_ = GameState::QUIT;
          break;
        }
        processInput();
        render();
        std::this_thread::sleep_for(std::chrono::milliseconds(PAUSE_DELAY_MS));
        break;
      case GameState::GAME_OVER:
        showGameOver();
        break;
      case GameState::QUIT:
        break;
    }
  }

  input_->cleanup();
}

void Game::initialize()
{
  const auto startPos = Coordinate{board_->getWidth() / 2, board_->getHeight() / 2};
  snake_              = std::make_unique<Snake>(startPos);
  board_->placeFood();
  score_ = 0;
  speed_ = 1;
  state_ = GameState::PLAYING;
}

void Game::processInput()
{
  if (state_ == GameState::PLAYING)
  {
    if (input_->isPauseRequested())
    {
      state_ = GameState::PAUSED;
    }
  }
  else if (state_ == GameState::PAUSED)
  {
    if (input_->isPauseRequested())
    {
      state_ = GameState::PLAYING;
    }
  }
}

void Game::update()
{
  if (state_ != GameState::PLAYING)
  {
    return;
  }

  auto newDir = input_->getDirection();

  if (newDir.has_value())
  {
    snake_->move(newDir.value());
  }
  else
  {
    snake_->move(snake_->getDirection());
  }

  handleCollision();

  if (board_->isFoodAt(snake_->getHead()))
  {
    snake_->grow();
    board_->placeFood();
    score_ += SCORE_PER_FOOD;

    if (score_ % SPEED_INCREASE_INTERVAL == 0 and speed_ < MAX_SPEED)
    {
      ++speed_;
    }
  }
}

void Game::render()
{
  clear();

  for (uint8_t col = 0; col < board_->getWidth() + 2; ++col)
  {
    mvprintw(0, col, "#");
    mvprintw(board_->getHeight() + 1, col, "#");
  }

  for (uint8_t row = 0; row < board_->getHeight() + 2; ++row)
  {
    mvprintw(row, 0, "#");
    mvprintw(row, board_->getWidth() + 1, "#");
  }

  const auto& body   = snake_->getBody();
  bool        isHead = true;
  for (const auto& segment : body)
  {
    char symbol = isHead ? '@' : 'o';
    mvprintw(segment.second + 1, segment.first + 1, "%c", symbol);
    isHead = false;
  }

  const auto food = board_->getFoodPosition();

  mvprintw(food.second + 1, food.first + 1, "*");
  mvprintw(board_->getHeight() + 3, 0, "Score: %d", score_);
  mvprintw(board_->getHeight() + 4, 0, "Speed: %d", speed_);
  mvprintw(board_->getHeight() + 5, 0, "Controls: Arrows or WASD | Pause: P | Quit: Q");

  if (state_ == GameState::PAUSED)
  {
    const auto centerY = board_->getHeight() / 2;
    const auto centerX = (board_->getWidth() / 2) - 6;
    mvprintw(centerY, centerX, "*** PAUSED ***");
  }

  refresh();
}

void Game::handleCollision()
{
  const auto head = snake_->getHead();

  if (board_->isWall(head))
  {
    state_ = GameState::GAME_OVER;
    return;
  }

  if (snake_->checkSelfCollision())
  {
    state_ = GameState::GAME_OVER;
    return;
  }
}

void Game::showMenu()
{
  clear();

  const uint8_t centerY = LINES / 2;
  const uint8_t centerX = COLS / 2;

  mvprintw(centerY - 3, centerX - 10, "===================");
  mvprintw(centerY - 2, centerX - 10, "   SNAKE GAME     ");
  mvprintw(centerY - 1, centerX - 10, "===================");
  mvprintw(centerY + 1, centerX - 12, "Press any key to start");
  mvprintw(centerY + 2, centerX - 6, "the game");
  mvprintw(centerY + 4, centerX - 6, "Quit: Q");

  refresh();

  nodelay(stdscr, FALSE);
  const auto keyPressed = getch();
  nodelay(stdscr, TRUE);

  if (keyPressed == 'q' or keyPressed == 'Q' or keyPressed == ESC_KEY)
  {
    state_ = GameState::QUIT;
    return;
  }

  initialize();
}

void Game::showGameOver()
{
  clear();

  const uint8_t centerY = LINES / 2;
  const uint8_t centerX = COLS / 2;

  mvprintw(centerY - 2, centerX - 10, "===================");
  mvprintw(centerY - 1, centerX - 10, "    GAME OVER     ");
  mvprintw(centerY, centerX - 10, "===================");
  mvprintw(centerY + 2, centerX - 10, "Your score: %d", score_);
  mvprintw(centerY + 4, centerX - 12, "Press any key to return");
  mvprintw(centerY + 5, centerX - 7, "to the menu");
  mvprintw(centerY + 6, centerX - 6, "Quit: Q");

  refresh();

  nodelay(stdscr, FALSE);
  const auto keyPressed = getch();
  nodelay(stdscr, TRUE);

  if (keyPressed == 'q' or keyPressed == 'Q' or keyPressed == ESC_KEY)
  {
    state_ = GameState::QUIT;
    return;
  }

  state_ = GameState::MENU;
}

auto Game::getDelayMs() const -> uint16_t
{
  return INITIAL_SPEED_DELAY_MS - ((speed_ - 1) * SPEED_DECREASE_PER_LEVEL);
}

}  // namespace SnakeGame
