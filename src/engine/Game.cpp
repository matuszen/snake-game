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
#include <mutex>
#include <ratio>
#include <thread>
#include <vector>

namespace SnakeGame
{

Game::Game(const BoardDimensions boardSize)
  : snake_(nullptr), board_(std::make_unique<Board>(boardSize)), pendingCommand_(IpcCommands::NONE),
    pendingBoardSize_({0, 0}), state_(GameState::MENU), score_(0), speed_(1), fruitPickedThisFrame_(false)
{
  shmManager_    = std::make_unique<SharedMemoryManager>();
  commandSocket_ = std::make_unique<CommandSocket>();
  if (shmManager_->isInitialized())
  {
    shmManager_->startAsyncWriter();
  }

  const auto started = commandSocket_->start([this](IpcCommands cmd, const std::vector<uint8_t>& payload) -> void
                                             { this->handleCommand(cmd, payload); });

  if (not started)
  {
    commandSocket_.reset();
    std::cerr << "Failed to start command socket\n";
  }
}

void Game::run()
{
  using Clock      = std::chrono::steady_clock;
  using DurationMs = std::chrono::duration<double, std::milli>;

  auto   lastTime        = Clock::now();
  double timeAccumulator = 0.0;

  while (state_ != GameState::QUIT)
  {
    const auto currentTime = Clock::now();
    const auto elapsed     = DurationMs(currentTime - lastTime);
    lastTime               = currentTime;

    processSocketCommand();

    if (state_ == GameState::PLAYING)
    {
      timeAccumulator        += elapsed.count();
      const auto targetDelay  = static_cast<double>(getDelayMs());

      if (timeAccumulator >= targetDelay)
      {
        auto currentDirection = snake_ ? snake_->getDirection() : Direction::UP;
        if (pendingDirection_)
        {
          currentDirection = *pendingDirection_;
          pendingDirection_.reset();
        }

        update(currentDirection);

        timeAccumulator -= targetDelay;

        if (timeAccumulator > targetDelay)
        {
          timeAccumulator = 0.0;
        }
        updateSharedMemory();
      }
    }
    else
    {
      timeAccumulator = 0.0;
      updateSharedMemory();
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
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
  fruitPickedThisFrame_ = false;
}

auto Game::step(const Direction direction) -> StepResult
{
  fruitPickedThisFrame_ = false;
  update(direction);

  return {
    .distances     = getNeuralInputs(),
    .isGameOver    = (state_ == GameState::GAME_OVER),
    .fruitPickedUp = fruitPickedThisFrame_,
  };
}

void Game::reset()
{
  initialize();
}

auto Game::getScore() const -> uint16_t
{
  return score_;
}

void Game::update(const Direction direction)
{
  if (state_ != GameState::PLAYING or not snake_)
  {
    return;
  }

  snake_->move(direction);
  handleCollision();

  if (state_ != GameState::PLAYING)
  {
    return;
  }

  if (snake_->getHead() == board_->getFoodPosition())
  {
    fruitPickedThisFrame_ = true;
    snake_->grow();
    score_ += 10;
    board_->placeFood(snake_->getBody());
  }
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

    case IpcCommands::CHANGE_BOARD_SIZE:
      if (state_ == GameState::MENU)
      {
        auto newDimensions = BoardDimensions{0, 0};
        {
          const std::lock_guard<std::mutex> lock(commandMutex_);
          newDimensions = pendingBoardSize_;
        }

        constexpr uint8_t MAX_BOARD_DIMENSION = 100;
        if (newDimensions.first >= 5 and newDimensions.second >= 5 and
            newDimensions.first <= MAX_BOARD_DIMENSION and newDimensions.second <= MAX_BOARD_DIMENSION)
        {
          board_ = std::make_unique<Board>(newDimensions);
          initialize();
        }
      }
      break;

    case IpcCommands::NONE:
      break;
  }
}

void Game::handleCollision() noexcept
{
  if (not snake_)
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

void Game::handleCommand(IpcCommands command, const std::vector<uint8_t>& payload) noexcept
{
  if (command == IpcCommands::CHANGE_BOARD_SIZE and payload.size() == 2)
  {
    const std::lock_guard<std::mutex> lock(commandMutex_);
    pendingBoardSize_ = {payload[0], payload[1]};
  }
  pendingCommand_.store(command, std::memory_order_release);
}

auto Game::getDelayMs() const noexcept -> uint16_t
{
  auto delay = INITIAL_SPEED_DELAY_MS - ((speed_ - 1) * SPEED_DECREASE_PER_LEVEL);
  delay      = std::max(delay, 10);
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
      if (i >= SNAKE_MAX_LENGTH)
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
  if (not snake_)
  {
    return {};
  }

  const auto  head      = snake_->getHead();
  const auto& snakeBody = snake_->getBody();
  const auto  foodPos   = board_->getFoodPosition();

  const auto findDistance = [&](const Direction currentDirection, const auto collisionCheck) -> float
  {
    auto    currentPosition = head;
    int32_t distance        = 0;

    while (distance < std::max(board_->getWidth(), board_->getHeight()))
    {
      if (currentDirection == Direction::UP)
      {
        --currentPosition.second;
      }
      else if (currentDirection == Direction::DOWN)
      {
        ++currentPosition.second;
      }
      else if (currentDirection == Direction::LEFT)
      {
        --currentPosition.first;
      }
      else if (currentDirection == Direction::RIGHT)
      {
        ++currentPosition.first;
      }

      ++distance;

      if (collisionCheck(currentPosition))
      {
        return distance > 0 ? 1.0F / (float)distance : 0.0F;
      }
    }

    return 0.0F;
  };

  return {
    findDistance(Direction::UP, [this](Coordinate pos) -> bool { return board_->isWall(pos); }),
    findDistance(Direction::DOWN, [this](Coordinate pos) -> bool { return board_->isWall(pos); }),
    findDistance(Direction::LEFT, [this](Coordinate pos) -> bool { return board_->isWall(pos); }),
    findDistance(Direction::RIGHT, [this](Coordinate pos) -> bool { return board_->isWall(pos); }),
    findDistance(Direction::UP, [foodPos](Coordinate pos) -> bool { return pos == foodPos; }),
    findDistance(Direction::DOWN, [foodPos](Coordinate pos) -> bool { return pos == foodPos; }),
    findDistance(Direction::LEFT, [foodPos](Coordinate pos) -> bool { return pos == foodPos; }),
    findDistance(Direction::RIGHT, [foodPos](Coordinate pos) -> bool { return pos == foodPos; }),
    findDistance(Direction::UP,
                 [&snakeBody](Coordinate pos) -> bool { return std::ranges::find(snakeBody, pos) != snakeBody.end(); }),
    findDistance(Direction::DOWN,
                 [&snakeBody](Coordinate pos) -> bool { return std::ranges::find(snakeBody, pos) != snakeBody.end(); }),
    findDistance(Direction::LEFT,
                 [&snakeBody](Coordinate pos) -> bool { return std::ranges::find(snakeBody, pos) != snakeBody.end(); }),
    findDistance(Direction::RIGHT,
                 [&snakeBody](Coordinate pos) -> bool { return std::ranges::find(snakeBody, pos) != snakeBody.end(); }),
  };
}

}  // namespace SnakeGame
