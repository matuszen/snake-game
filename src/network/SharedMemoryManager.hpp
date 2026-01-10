#pragma once

#include "Definitions.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>

namespace SnakeGame
{

inline constexpr std::string_view DEFAULT_SHM_NAME = "/snake_game_shm";

struct SharedMemoryData
{
  std::atomic<bool>     isWriting{false};
  std::atomic<uint32_t> version{0};
  GameSharedData        gameData{};
};

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
  std::string shmName_;
  int         shmFd_;
  void*       shmPtr_;
  size_t      shmSize_;
  bool        initialized_;

  GameSharedData writeBuffer_;
  std::mutex     bufferMutex_;

  std::atomic<bool> hasNewData_;

  std::unique_ptr<std::thread> writerThread_;
  std::atomic<bool>            shouldStopWriter_;

  auto initializeSharedMemory() -> bool;

  void cleanupSharedMemory() noexcept;
  void writerThreadFunction();
  void writeToSharedMemory(const GameSharedData& data) noexcept;
};

}  // namespace SnakeGame
