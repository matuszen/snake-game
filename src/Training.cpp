#include "Training.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>

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


}  // namespace

Game::Game(uint8_t boardWidth, uint8_t boardHeight)
  : snake_(nullptr), board_(std::make_unique<Board>(boardWidth, boardHeight)), state_(GameState::MENU), score_(0),
    speed_(1), fruitPickedThisFrame_(false)
    {}

// initialize the game
auto Game::initializeGame() -> StepResult
{
  initialize();
  StepResult result;
  result.distances = getNeuralInputs();
  result.isGameOver = false;
  result.fruitPickedUp = false;
  return result;
}

// step the game by one frame
auto Game::stepGame(Direction direction) -> StepResult
{
  fruitPickedThisFrame_ = false;
  update(direction);

  StepResult result;
  result.distances = getNeuralInputs();
  result.isGameOver = (state_ == GameState::GAME_OVER);
  result.fruitPickedUp = fruitPickedThisFrame_;
  return result;
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

void Game::update(Direction direction)
{
  if (state_ != GameState::PLAYING)
  {
    return;
  }

  snake_->move(direction);
  handleCollision();

  if (board_->isFoodAt(snake_->getHead()))
  {
    fruitPickedThisFrame_ = true;
    snake_->grow();
    board_->placeFood(snake_->getBody());
    score_ += SCORE_PER_FOOD;

    if (score_ % SPEED_INCREASE_INTERVAL == 0 && speed_ < MAX_SPEED)
    {
      ++speed_;
    }
  }

  //updateSharedMemory();
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



auto Game::getNeuralInputs() const -> std::array<float, 12>
{
    // 0 - 3: distances to walls (up, down, left, right)
    // 4 - 7: distances to food (up, down, left, right)
    // 8 - 11: distances to self-collision (up, down, left, right)
    std::array<float, 12> result = {};

    const auto head = snake_->getHead();
    //const auto maxDist = static_cast<float>(std::max(board_->getWidth(), board_->getHeight()));
    const auto& snakeBody = snake_->getBody();
    const auto foodPos = board_->getFoodPosition();

    auto findDistance = [&](Direction dir, auto collisionCheck) -> float {
        Coordinate pos = head;
        int distance = 0;

        while (distance < std::max(board_->getWidth(), board_->getHeight()))
        {
            if (dir == Direction::UP) --pos.second;
            else if (dir == Direction::DOWN) ++pos.second;
            else if (dir == Direction::LEFT) --pos.first;
            else if (dir == Direction::RIGHT) ++pos.first;

            ++distance;

            if (collisionCheck(pos))
                return distance > 0 ? 1.0f / distance : 0.0f;
        }

        return 0.0f;
    };

    result[0] = findDistance(Direction::UP, [this](Coordinate pos) {
        return board_->isWall(pos);
    });
    result[1] = findDistance(Direction::DOWN, [this](Coordinate pos) {
        return board_->isWall(pos);
    });
    result[2] = findDistance(Direction::LEFT, [this](Coordinate pos) {
        return board_->isWall(pos);
    });
    result[3] = findDistance(Direction::RIGHT, [this](Coordinate pos) {
        return board_->isWall(pos);
    });

    result[4] = findDistance(Direction::UP, [foodPos](Coordinate pos) {
        return pos == foodPos;
    });
    result[5] = findDistance(Direction::DOWN, [foodPos](Coordinate pos) {
        return pos == foodPos;
    });
    result[6] = findDistance(Direction::LEFT, [foodPos](Coordinate pos) {
        return pos == foodPos;
    });
    result[7] = findDistance(Direction::RIGHT, [foodPos](Coordinate pos) {
        return pos == foodPos;
    });

    result[8] = findDistance(Direction::UP, [&snakeBody](Coordinate pos) {
        return std::find(snakeBody.begin(), snakeBody.end(), pos) != snakeBody.end();
    });
    result[9] = findDistance(Direction::DOWN, [&snakeBody](Coordinate pos) {
        return std::find(snakeBody.begin(), snakeBody.end(), pos) != snakeBody.end();
    });
    result[10] = findDistance(Direction::LEFT, [&snakeBody](Coordinate pos) {
        return std::find(snakeBody.begin(), snakeBody.end(), pos) != snakeBody.end();
    });
    result[11] = findDistance(Direction::RIGHT, [&snakeBody](Coordinate pos) {
        return std::find(snakeBody.begin(), snakeBody.end(), pos) != snakeBody.end();
    });

    return result;
}

constexpr auto Game::getDelayMs() const noexcept -> uint16_t
{
  return INITIAL_SPEED_DELAY_MS - ((speed_ - 1) * SPEED_DECREASE_PER_LEVEL);
}



}  // namespace SnakeGame
