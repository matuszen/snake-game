#include "SharedMemoryManager.hpp"
#include "Types.hpp"

#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <utility>

namespace
{

constexpr int64_t K_SHARED_MEMORY_WRITE_DELAY = 200;

}  // namespace

namespace SnakeGame
{

SharedMemoryManager::SharedMemoryManager(std::string shmName)
  : shmName_(std::move(shmName)), shmFd_(-1), shmPtr_(nullptr), shmSize_(sizeof(SharedMemoryData)),
    initialized_(initializeSharedMemory()), hasNewData_(false), shouldStopWriter_(false)
{
}

SharedMemoryManager::~SharedMemoryManager()
{
  stopAsyncWriter();
  cleanupSharedMemory();
}

void SharedMemoryManager::startAsyncWriter()
{
  if (not initialized_ or writerThread_ != nullptr)
  {
    return;
  }

  shouldStopWriter_ = false;
  writerThread_     = std::make_unique<std::thread>(&SharedMemoryManager::writerThreadFunction, this);
}

void SharedMemoryManager::stopAsyncWriter()
{
  if (writerThread_ == nullptr)
  {
    return;
  }

  shouldStopWriter_ = true;

  if (writerThread_->joinable())
  {
    writerThread_->join();
  }

  writerThread_.reset();
}

void SharedMemoryManager::updateGameState(const GameSharedData& data) noexcept
{
  if (not initialized_)
  {
    return;
  }

  {
    std::lock_guard<std::mutex> lock(bufferMutex_);
    writeBuffer_ = data;
  }

  hasNewData_.store(true, std::memory_order_release);
}

auto SharedMemoryManager::isInitialized() const noexcept -> bool
{
  return initialized_;
}

auto SharedMemoryManager::initializeSharedMemory() -> bool
{
  shm_unlink(shmName_.c_str());

  shmFd_ = shm_open(shmName_.c_str(), O_CREAT | O_RDWR, 0666);
  if (shmFd_ == -1)
  {
    return false;
  }

  if (ftruncate(shmFd_, static_cast<off_t>(shmSize_)) == -1)
  {
    close(shmFd_);
    shm_unlink(shmName_.c_str());
    return false;
  }

  shmPtr_ = mmap(nullptr, shmSize_, PROT_READ | PROT_WRITE, MAP_SHARED, shmFd_, 0);
  if (shmPtr_ == MAP_FAILED)
  {
    close(shmFd_);
    shm_unlink(shmName_.c_str());
    return false;
  }

  auto* shmData = static_cast<SharedMemoryData*>(shmPtr_);
  new (shmData) SharedMemoryData();

  return true;
}

void SharedMemoryManager::cleanupSharedMemory() noexcept
{
  if (shmPtr_ != nullptr and shmPtr_ != MAP_FAILED)
  {
    munmap(shmPtr_, shmSize_);
    shmPtr_ = nullptr;
  }

  if (shmFd_ != -1)
  {
    close(shmFd_);
    shmFd_ = -1;
  }

  shm_unlink(shmName_.c_str());
}

void SharedMemoryManager::writerThreadFunction()
{
  while (not shouldStopWriter_.load(std::memory_order_acquire))
  {
    if (hasNewData_.load(std::memory_order_acquire))
    {
      auto dataToWrite = GameSharedData{};
      {
        std::lock_guard<std::mutex> lock(bufferMutex_);
        dataToWrite = writeBuffer_;
      }
      hasNewData_.store(false, std::memory_order_release);
      writeToSharedMemory(dataToWrite);
    }

    std::this_thread::sleep_for(std::chrono::microseconds(K_SHARED_MEMORY_WRITE_DELAY));
  }
}

void SharedMemoryManager::writeToSharedMemory(const GameSharedData& data) noexcept
{
  if (shmPtr_ == nullptr or shmPtr_ == MAP_FAILED)
  {
    return;
  }

  auto* shmData = static_cast<SharedMemoryData*>(shmPtr_);

  bool expected = false;
  if (not shmData->isWriting.compare_exchange_strong(expected, true, std::memory_order_acquire))
  {
    return;
  }

  shmData->gameData.boardWidth     = data.boardWidth;
  shmData->gameData.boardHeight    = data.boardHeight;
  shmData->gameData.score          = data.score;
  shmData->gameData.speed          = data.speed;
  shmData->gameData.gameState      = data.gameState;
  shmData->gameData.foodPosition   = data.foodPosition;
  shmData->gameData.foodType       = data.foodType;
  shmData->gameData.snakeHead      = data.snakeHead;
  shmData->gameData.snakeLength    = data.snakeLength;
  shmData->gameData.neuralVector   = data.neuralVector;
  shmData->gameData.snakeDirection = data.snakeDirection;

  const auto copyLength = std::min(data.snakeLength, MAX_SNAKE_LENGTH);
  std::copy_n(data.snakeBody.begin(), copyLength, shmData->gameData.snakeBody.begin());

  shmData->version.fetch_add(1, std::memory_order_release);
  shmData->isWriting.store(false, std::memory_order_release);
}

}  // namespace SnakeGame
