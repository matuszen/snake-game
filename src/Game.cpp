#include "Game.hpp"
#include "Board.hpp"
#include "CommandSocket.hpp"
#include "Input.hpp"
#include "SharedMemoryManager.hpp"
#include "Snake.hpp"
#include "Types.hpp"

#include <notcurses/notcurses.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <format>
#include <memory>
#include <string>
#include <thread>

namespace
{
constexpr uint16_t PAUSE_DELAY_MS           = 100;
constexpr uint16_t INITIAL_SPEED_DELAY_MS   = 200;
constexpr uint8_t  SPEED_DECREASE_PER_LEVEL = 15;

constexpr uint32_t APPLE_COLOR   = 0xFF0000;
constexpr uint32_t CHERRY_COLOR  = 0xFF1493;
constexpr uint32_t BANANA_COLOR  = 0xFFFF00;
constexpr uint32_t GRAPE_COLOR   = 0x9400D3;
constexpr uint32_t ORANGE_COLOR  = 0xFF8C00;
constexpr uint32_t DEFAULT_COLOR = 0xFFFFFF;

}  // namespace

namespace SnakeGame
{

Game::Game(uint8_t boardWidth, uint8_t boardHeight)
  : snake_(nullptr), board_(std::make_unique<Board>(boardWidth, boardHeight)), state_(GameState::MENU), score_(0),
    speed_(1), pendingCommand_(IpcCommands::NONE)
{
  input_         = std::make_unique<Input>();
  shmManager_    = std::make_unique<SharedMemoryManager>();
  commandSocket_ = std::make_unique<CommandSocket>();
  if (shmManager_->isInitialized())
  {
    shmManager_->startAsyncWriter();
  }

  const auto started = commandSocket_->start([this](IpcCommands cmd) { this->handleCommand(cmd); });

  if (not started)
  {
    commandSocket_.reset();
  }
}

void Game::run()
{
  input_->initialize();

  while (state_ != GameState::QUIT)
  {
    processSocketCommand();

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
  speed_ = 10;
  state_ = GameState::PLAYING;
  input_->resetInput();
}

void Game::processInput() noexcept
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

void Game::render() noexcept
{
  auto* nc       = input_->getNotcurses();
  auto* stdplane = input_->getStdPlane();
  if (nc == nullptr or stdplane == nullptr)
  {
    return;
  }

  ncplane_erase(stdplane);

  ncplane_set_fg_rgb8(stdplane, 128, 128, 128);

  for (uint8_t col = 0; col < board_->getWidth() + 2; ++col)
  {
    ncplane_putstr_yx(stdplane, 0, col, "█");
    ncplane_putstr_yx(stdplane, board_->getHeight() + 1, col, "█");
  }

  for (uint8_t row = 0; row < board_->getHeight() + 2; ++row)
  {
    ncplane_putstr_yx(stdplane, row, 0, "█");
    ncplane_putstr_yx(stdplane, row, board_->getWidth() + 1, "█");
  }

  const auto& body   = snake_->getBody();
  bool        isHead = true;
  for (const auto& segment : body)
  {
    if (isHead)
    {
      ncplane_set_fg_rgb8(stdplane, 50, 255, 50);
      ncplane_putstr_yx(stdplane, segment.second + 1, segment.first + 1, "◉");
      isHead = false;
    }
    else
    {
      ncplane_set_fg_rgb8(stdplane, 0, 200, 0);
      ncplane_putstr_yx(stdplane, segment.second + 1, segment.first + 1, "○");
    }
  }

  const auto  food       = board_->getFoodPosition();
  const auto  foodType   = board_->getFoodType();
  const auto* foodSymbol = getFoodSymbol(foodType);
  const auto  foodColor  = getFoodColor(foodType);

  ncplane_set_fg_rgb8(stdplane, (foodColor >> 16) & 0xFF, (foodColor >> 8) & 0xFF, foodColor & 0xFF);
  ncplane_putstr_yx(stdplane, food.second + 1, food.first + 1, foodSymbol);

  ncplane_set_fg_rgb8(stdplane, 255, 255, 255);

  const auto scoreText = std::format("Score: {}", score_);
  const auto speedText = std::format("Speed: {}", speed_);

  ncplane_putstr_yx(stdplane, board_->getHeight() + 3, 0, scoreText.c_str());
  ncplane_putstr_yx(stdplane, board_->getHeight() + 4, 0, speedText.c_str());
  ncplane_putstr_yx(stdplane, board_->getHeight() + 5, 0, "Controls: Arrows or WASD | Pause: P | Quit: Q");

  if (state_ == GameState::PAUSED)
  {
    const auto centerY = board_->getHeight() / 2;
    const auto centerX = (board_->getWidth() / 2) - 5;

    ncplane_set_fg_rgb8(stdplane, 255, 255, 0);
    ncplane_putstr_yx(stdplane, centerY, centerX, "|| PAUSED ||");
  }

  notcurses_render(nc);
}

void Game::handleCollision() noexcept
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
  auto* nc       = input_->getNotcurses();
  auto* stdplane = input_->getStdPlane();
  if (nc == nullptr or stdplane == nullptr)
  {
    return;
  }

  ncplane_erase(stdplane);

  unsigned rows = 0;
  unsigned cols = 0;
  ncplane_dim_yx(stdplane, &rows, &cols);

  const uint8_t centerY = rows / 2;
  const uint8_t centerX = cols / 2;

  ncplane_set_fg_rgb8(stdplane, 0, 255, 0);
  ncplane_putstr_yx(stdplane, centerY - 1, centerX - 10, "=== SNAKE GAME ===");

  ncplane_set_fg_rgb8(stdplane, 0, 255, 255);
  ncplane_putstr_yx(stdplane, centerY + 1, centerX - 12, "Press any key to start");
  ncplane_putstr_yx(stdplane, centerY + 2, centerX - 6, "the game");

  ncplane_set_fg_rgb8(stdplane, 255, 255, 0);
  ncplane_putstr_yx(stdplane, centerY + 4, centerX - 6, "Quit: Q");

  notcurses_render(nc);

  auto       ni         = ncinput{};
  const auto keyPressed = notcurses_get_nblock(nc, &ni);

  if (keyPressed == 'q' or keyPressed == 'Q')
  {
    state_ = GameState::QUIT;
    return;
  }

  if (keyPressed > 0)
  {
    initialize();
    return;
  }

  std::this_thread::sleep_for(std::chrono::milliseconds(PAUSE_DELAY_MS));
}

void Game::showGameOver()
{
  auto* nc       = input_->getNotcurses();
  auto* stdplane = input_->getStdPlane();
  if (nc == nullptr or stdplane == nullptr)
  {
    return;
  }

  ncplane_erase(stdplane);

  unsigned rows = 0;
  unsigned cols = 0;
  ncplane_dim_yx(stdplane, &rows, &cols);

  const uint8_t centerY = rows / 2;
  const uint8_t centerX = cols / 2;

  ncplane_set_fg_rgb8(stdplane, 255, 0, 0);
  ncplane_putstr_yx(stdplane, centerY - 2, centerX - 10, "=================");
  ncplane_putstr_yx(stdplane, centerY - 1, centerX - 10, "XX  GAME OVER  XX");
  ncplane_putstr_yx(stdplane, centerY, centerX - 10, "=================");

  ncplane_set_fg_rgb8(stdplane, 255, 255, 0);
  const auto scoreText = std::format("Your score: {}", score_);
  ncplane_putstr_yx(stdplane, centerY + 2, centerX - 8, scoreText.c_str());

  ncplane_set_fg_rgb8(stdplane, 255, 255, 255);
  ncplane_putstr_yx(stdplane, centerY + 4, centerX - 13, "Press any key to return");
  ncplane_putstr_yx(stdplane, centerY + 5, centerX - 8, "to the menu");

  ncplane_set_fg_rgb8(stdplane, 0, 255, 255);
  ncplane_putstr_yx(stdplane, centerY + 7, centerX - 6, "Quit: Q");

  notcurses_render(nc);

  auto       ni         = ncinput{};
  const auto keyPressed = notcurses_get_nblock(nc, &ni);

  if (keyPressed == 'q' or keyPressed == 'Q')
  {
    state_ = GameState::QUIT;
    return;
  }

  if (keyPressed > 0)
  {
    state_ = GameState::MENU;
    return;
  }

  std::this_thread::sleep_for(std::chrono::milliseconds(PAUSE_DELAY_MS));
}

constexpr auto Game::getDelayMs() const noexcept -> uint16_t
{
  return INITIAL_SPEED_DELAY_MS - ((speed_ - 1) * SPEED_DECREASE_PER_LEVEL);
}

void Game::updateSharedMemory() noexcept
{
  if (not shmManager_ or not shmManager_->isInitialized())
  {
    return;
  }

  auto sharedGameInfo = GameSharedData{
    .boardWidth     = board_->getWidth(),
    .boardHeight    = board_->getHeight(),
    .score          = score_,
    .speed          = speed_,
    .gameState      = state_,
    .foodPosition   = board_->getFoodPosition(),
    .foodType       = board_->getFoodType(),
    .snakeHead      = {0, 0},
    .snakeLength    = 0,
    .neuralVector   = getNeuralInputs(),
    .snakeDirection = snake_->getDirection(),
    .snakeBody      = {}
  };

  if (snake_ != nullptr)
  {
    const auto& body       = snake_->getBody();
    const auto  copyLength = std::min(static_cast<size_t>(MAX_SNAKE_LENGTH), body.size());

    std::copy_n(body.begin(), copyLength, sharedGameInfo.snakeBody.begin());
    sharedGameInfo.snakeHead   = snake_->getHead();
    sharedGameInfo.snakeLength = static_cast<uint16_t>(body.size());
  }
  else
  {
    sharedGameInfo.snakeHead   = {0, 0};
    sharedGameInfo.snakeLength = 0;
  }

  shmManager_->updateGameState(sharedGameInfo);
}

void Game::handleCommand(IpcCommands command) noexcept
{
  pendingCommand_.store(command, std::memory_order_release);
}

void Game::processSocketCommand() noexcept
{
  const auto command = pendingCommand_.exchange(IpcCommands::NONE, std::memory_order_acquire);

  if (command == IpcCommands::NONE)
  {
    return;
  }

  switch (command)
  {
    case IpcCommands::START_GAME:
      if (state_ == GameState::MENU or state_ == GameState::GAME_OVER)
      {
        initialize();
      }
      break;

    case IpcCommands::MOVE_UP:
      if (state_ == GameState::PLAYING)
      {
        pendingDirection_ = Direction::UP;
      }
      break;

    case IpcCommands::MOVE_DOWN:
      if (state_ == GameState::PLAYING)
      {
        pendingDirection_ = Direction::DOWN;
      }
      break;

    case IpcCommands::MOVE_LEFT:
      if (state_ == GameState::PLAYING)
      {
        pendingDirection_ = Direction::LEFT;
      }
      break;

    case IpcCommands::MOVE_RIGHT:
      if (state_ == GameState::PLAYING)
      {
        pendingDirection_ = Direction::RIGHT;
      }
      break;

    case IpcCommands::RESTART_GAME:
      if (state_ == GameState::GAME_OVER or state_ == GameState::PLAYING)
      {
        initialize();
      }
      break;

    case IpcCommands::QUIT_GAME:
      state_ = GameState::QUIT;
      break;

    case IpcCommands::NONE:
      break;
  }
}

constexpr auto Game::getFoodSymbol(FoodType type) -> const char*
{
  switch (type)
  {
    case FoodType::APPLE:
      return "●";
    case FoodType::CHERRY:
      return "◆";
    case FoodType::BANANA:
      return "◉";
    case FoodType::GRAPE:
      return "■";
    case FoodType::ORANGE:
      return "★";
    default:
      return "*";
  }
}

constexpr auto Game::getFoodColor(FoodType type) -> uint32_t
{
  switch (type)
  {
    case FoodType::APPLE:
      return APPLE_COLOR;
    case FoodType::CHERRY:
      return CHERRY_COLOR;
    case FoodType::BANANA:
      return BANANA_COLOR;
    case FoodType::GRAPE:
      return GRAPE_COLOR;
    case FoodType::ORANGE:
      return ORANGE_COLOR;
    default:
      return DEFAULT_COLOR;
  }
}

}  // namespace SnakeGame
