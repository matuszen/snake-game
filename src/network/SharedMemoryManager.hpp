#pragma once

#include "Definitions.hpp"

#include <atomic>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

namespace SnakeGame
{

/**
 * @brief Manages POSIX shared memory for game state communication.
 *
 * This class creates and manages a shared memory region, providing thread-safe
 * asynchronous writes to prevent blocking the main game loop. Uses double-buffering
 * and atomic synchronization to ensure data consistency.
 */
class SharedMemoryManager
{
public:
  /**
   * @brief Constructs a SharedMemoryManager with the specified shared memory name.
   *
   * @param shmName Name of the POSIX shared memory object (default: /snake_game_shm).
   */
  explicit SharedMemoryManager(std::string shmName = std::string{DEFAULT_SHM_NAME});
  ~SharedMemoryManager();

  SharedMemoryManager(const SharedMemoryManager& other)                   = delete;
  SharedMemoryManager(SharedMemoryManager&& other)                        = delete;
  auto operator=(const SharedMemoryManager& other) -> SharedMemoryManager = delete;
  auto operator=(SharedMemoryManager&& other) -> SharedMemoryManager      = delete;

  /**
   * @brief Starts the background writer thread.
   *
   * The writer thread periodically flushes buffered game state to shared memory.
   */
  void startAsyncWriter();

  /**
   * @brief Stops the background writer thread and waits for it to finish.
   */
  void stopAsyncWriter();

  /**
   * @brief Updates the internal buffer with new game state data.
   *
   * This method is thread-safe and does not block. The data will be written
   * to shared memory asynchronously by the writer thread.
   *
   * @param data The new game state to buffer.
   */
  void updateGameState(const GameSharedData& data) noexcept;

  /**
   * @brief Checks if shared memory was successfully initialized.
   *
   * @return true If shared memory is ready for use.
   * @return false If initialization failed.
   */
  auto isInitialized() const noexcept -> bool;

private:
  GameSharedData               writeBuffer_;
  std::mutex                   bufferMutex_;
  std::atomic<bool>            hasNewData_;
  std::unique_ptr<std::thread> writerThread_;
  std::atomic<bool>            shouldStopWriter_;
  std::string                  shmName_;

  int32_t shmFd_;
  void*   shmPtr_;
  bool    initialized_;

  auto initializeSharedMemory() -> bool;
  void cleanupSharedMemory() noexcept;
  void writerThreadFunction();
  void writeToSharedMemory(const GameSharedData& data) noexcept;
};

}  // namespace SnakeGame
