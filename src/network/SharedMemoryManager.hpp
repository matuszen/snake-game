#pragma once

#include "Definitions.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

namespace SnakeGame
{

class SharedMemoryManager
{
public:
  explicit SharedMemoryManager(std::string shmName = std::string{DEFAULT_SHM_NAME});
  ~SharedMemoryManager();

  SharedMemoryManager(const SharedMemoryManager& other)                   = delete;
  SharedMemoryManager(SharedMemoryManager&& other)                        = delete;
  auto operator=(const SharedMemoryManager& other) -> SharedMemoryManager = delete;
  auto operator=(SharedMemoryManager&& other) -> SharedMemoryManager      = delete;

  void startAsyncWriter();
  void stopAsyncWriter();
  void updateGameState(const GameSharedData& data) noexcept;
  auto isInitialized() const noexcept -> bool;

private:
  GameSharedData               writeBuffer_;
  std::mutex                   bufferMutex_;
  std::atomic<bool>            hasNewData_;
  std::unique_ptr<std::thread> writerThread_;
  std::atomic<bool>            shouldStopWriter_;
  std::string                  shmName_;

  int32_t shmFd_;
  size_t  shmSize_;
  void*   shmPtr_;
  bool    initialized_;

  auto initializeSharedMemory() -> bool;
  void cleanupSharedMemory() noexcept;
  void writerThreadFunction();
  void writeToSharedMemory(const GameSharedData& data) noexcept;
};

}  // namespace SnakeGame
