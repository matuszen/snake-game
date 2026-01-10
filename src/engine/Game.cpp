#include "Game.hpp"
#include "Board.hpp"
#include "CommandSocket.hpp"
#include "Definitions.hpp"
#include "SharedMemoryManager.hpp"
#include "Snake.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <memory>
#include <thread>

namespace
{

constexpr uint16_t INITIAL_SPEED_DELAY_MS   = 200;
constexpr uint8_t  SPEED_DECREASE_PER_LEVEL = 15;

}  // namespace

namespace SnakeGame
{

Game::Game(uint8_t boardWidth, uint8_t boardHeight)
  : snake_(nullptr), board_(std::make_unique<Board>(boardWidth, boardHeight)), state_(GameState::MENU), score_(0),
    speed_(1), pendingCommand_(IpcCommands::NONE)
{
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
    std::cerr << "Failed to start command socket\n";
  }
}

void Game::run()
{
  while (state_ != GameState::QUIT)
  {
    processSocketCommand();

    if (state_ == GameState::PLAYING)
    {
      gameStep();
      std::this_thread::sleep_for(std::chrono::milliseconds(getDelayMs()));
    }
    else
    {
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    updateSharedMemory();
  }
}

void Game::initialize()
{
  const auto startPos = Coordinate{board_->getWidth() / 2, board_->getHeight() / 2};
  snake_              = std::make_unique<Snake>(startPos);
  board_->placeFood();
  score_ = 0;
  speed_ = 1;
  state_ = GameState::PLAYING;
  pendingDirection_.reset();
}

void Game::gameStep() noexcept
{
  if (not snake_)
  {
    return;
  }

  if (pendingDirection_)
  {
    snake_->move(*pendingDirection_);
    pendingDirection_.reset();
  }
  else
  {
    snake_->move(snake_->getDirection());
  }

  handleCollision();

  if (state_ != GameState::PLAYING)
  {
    return;
  }

  // Check Food
  if (snake_->getHead() == board_->getFoodPosition())
  {
    snake_->grow();
    score_ += 10;

    // Speed logic can go here

    board_->placeFood();
  }
}

void Game::processSocketCommand() noexcept
{
  // Need to loop to process all pending commands or just one?
  // Original handled one per loop. Let's stick to that but maybe better to handle all?
  // But pendingCommand is atomic single value.
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

void Game::handleCollision() noexcept
{
  if (!snake_)
  {
    return;
  }

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

void Game::handleCommand(IpcCommands command) noexcept
{
  pendingCommand_.store(command, std::memory_order_release);
}

constexpr auto Game::getDelayMs() const noexcept -> uint16_t
{
  int delay = INITIAL_SPEED_DELAY_MS - ((speed_ - 1) * SPEED_DECREASE_PER_LEVEL);
  delay     = std::max(delay, 50);
  return static_cast<uint16_t>(delay);
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
    .snakeDirection = snake_ ? snake_->getDirection() : Direction::UP,
    .snakeBody      = {}
  };

  if (snake_ != nullptr)
  {
    const auto& body = snake_->getBody();

    uint16_t i = 0;
    for (const auto& segment : body)
    {
      if (i >= MAX_SNAKE_LENGTH)
      {
        break;
      }
      sharedGameInfo.snakeBody.at(i) = segment;
      ++i;
    }

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

auto Game::getNeuralInputs() const -> NeuralInputs
{
  if (!snake_)
  {
    return {};
  }

  NeuralInputs result = {};

  const auto  head      = snake_->getHead();
  const auto& snakeBody = snake_->getBody();
  const auto  foodPos   = board_->getFoodPosition();

  auto findDistance = [&](Direction dir, auto collisionCheck) -> float
  {
    Coordinate pos      = head;
    int        distance = 0;

    while (distance < std::max(board_->getWidth(), board_->getHeight()))
    {
      if (dir == Direction::UP)
      {
        --pos.second;
      }
      else if (dir == Direction::DOWN)
      {
        ++pos.second;
      }
      else if (dir == Direction::LEFT)
      {
        --pos.first;
      }
      else if (dir == Direction::RIGHT)
      {
        ++pos.first;
      }

      ++distance;

      if (collisionCheck(pos))
      {
        return distance > 0 ? 1.0F / (float)distance : 0.0F;
      }
    }

    return 0.0F;
  };

  result[0] = findDistance(Direction::UP, [this](Coordinate pos) -> bool { return board_->isWall(pos); });
  result[1] = findDistance(Direction::DOWN, [this](Coordinate pos) -> bool { return board_->isWall(pos); });
  result[2] = findDistance(Direction::LEFT, [this](Coordinate pos) -> bool { return board_->isWall(pos); });
  result[3] = findDistance(Direction::RIGHT, [this](Coordinate pos) -> bool { return board_->isWall(pos); });

  result[4] = findDistance(Direction::UP, [foodPos](Coordinate pos) -> bool { return pos == foodPos; });
  result[5] = findDistance(Direction::DOWN, [foodPos](Coordinate pos) -> bool { return pos == foodPos; });
  result[6] = findDistance(Direction::LEFT, [foodPos](Coordinate pos) -> bool { return pos == foodPos; });
  result[7] = findDistance(Direction::RIGHT, [foodPos](Coordinate pos) -> bool { return pos == foodPos; });

  result[8]  = findDistance(Direction::UP, [&snakeBody](Coordinate pos) -> bool
                            { return std::ranges::find(snakeBody, pos) != snakeBody.end(); });
  result[9]  = findDistance(Direction::DOWN, [&snakeBody](Coordinate pos) -> bool
                            { return std::ranges::find(snakeBody, pos) != snakeBody.end(); });
  result[10] = findDistance(Direction::LEFT, [&snakeBody](Coordinate pos) -> bool
                            { return std::ranges::find(snakeBody, pos) != snakeBody.end(); });
  result[11] = findDistance(Direction::RIGHT, [&snakeBody](Coordinate pos) -> bool
                            { return std::ranges::find(snakeBody, pos) != snakeBody.end(); });

  return result;
}

}  // namespace SnakeGame
